#!/usr/bin/env python3
"""Build a portable local-marketplace install bundle; never installs or uploads it."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile

from build_runtime import prepare as prepare_runtime
from strict_json import identifier, loads, terminal

ROOT = Path(__file__).resolve().parents[1]
WRAPPERS = {
    'README.md': 'distribution/INSTALL.md',
    '.agents/plugins/marketplace.json': 'distribution/codex-marketplace.json',
    '.claude-plugin/marketplace.json': 'distribution/claude-marketplace.json',
}
DEV_PARTS = {'tests', 'evals', 'examples', '.github', 'shared', 'work', 'artifacts',
             'local', '__pycache__', '.git', '.venv', 'node_modules', 'distribution'}
DEV_FILES = {'build_release.py', 'build_runtime.py', 'validate_package.py',
             'sync_shared.py', 'package.py', 'demo_app.py', 'boundary_lab.py',
             'demo_cases.py', 'score_routing.py'}
CODEX_MARKETPLACE = {
    'name': 'outcome-qa-releases',
    'interface': {'displayName': 'Outcome QA Releases'},
    'plugins': [{'name': 'outcome-qa', 'source': {'source': 'local', 'path': './outcome-qa'},
                 'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                 'category': 'Developer Tools'}],
}
CLAUDE_MARKETPLACE = {
    'name': 'outcome-qa-releases', 'description': 'Outcome QA: focused product testing methods for coding agents.',
    'owner': {'name': 'c33leron'},
    'plugins': [{'name': 'outcome-qa', 'source': './outcome-qa'}],
}


def _is_link(path):
    """Reject symlinks and NTFS reparse points/junctions, including Python 3.10."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def _relative(value):
    if not identifier(value) or '\\' in value or ':' in value:
        raise ValueError('Bundle file names must be safe POSIX relative paths')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('Bundle file names must be contained relative paths')
    if path.as_posix() != value:
        raise ValueError('Bundle file name is not normalized')
    return path


def _root(value):
    root = Path(os.path.abspath(Path(value).expanduser()))
    if any(_is_link(path) for path in (root, *root.parents)) or not root.is_dir():
        raise ValueError('Bundle source must be a real directory without symlink ancestors')
    return root


def _source(root, relative):
    path = root
    for part in _relative(relative).parts:
        path /= part
        if _is_link(path):
            raise ValueError('Symlink bundle source is forbidden: ' + relative)
    if not path.is_file():
        raise ValueError('Missing bundle source: ' + relative)
    data = path.read_bytes()
    text = data.decode('utf-8')
    if not text.strip():
        raise ValueError('Empty bundle source: ' + relative)
    if re.search(r'/(?:Users|home)/[^/\s]+/', text):
        raise ValueError('Personal absolute path in bundle wrapper: ' + relative)
    return data


def _runtime_name(name):
    path = _relative(name)
    if (set(path.parts) & DEV_PARTS or path.name in DEV_FILES or
            path.name.startswith(('.env', 'test_')) or path.suffix in ('.pyc', '.log', '.zip')):
        raise ValueError('Developer-only file cannot enter the install bundle: ' + name)
    return path


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(root=None):
    """Return the version and exact relative-file payloads, including MANIFEST.json."""
    root = _root(ROOT if root is None else root)
    runtime = prepare_runtime(root)
    if not isinstance(runtime, dict) or not runtime:
        raise ValueError('Runtime preparation returned no files')
    files = {}
    for name, data in runtime.items():
        path = _runtime_name(name)
        if not isinstance(data, bytes):
            raise ValueError('Runtime payload must contain bytes')
        files[(PurePosixPath('outcome-qa') / path).as_posix()] = data
    manifest = loads(runtime.get('plugin.json', b'').decode('utf-8'))
    version = manifest.get('version') if isinstance(manifest, dict) else None
    if (not isinstance(version, str) or
            not re.fullmatch(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?', version)):
        raise ValueError('Runtime manifest must declare a safe semantic version')
    if manifest.get('name') != 'outcome-qa':
        raise ValueError('Unexpected runtime plugin identity')
    for destination, source in WRAPPERS.items():
        files[destination] = _source(root, source)
    if loads(files['.agents/plugins/marketplace.json'].decode()) != CODEX_MARKETPLACE:
        raise ValueError('Codex marketplace must resolve the local ./outcome-qa child')
    if loads(files['.claude-plugin/marketplace.json'].decode()) != CLAUDE_MARKETPLACE:
        raise ValueError('Claude marketplace must resolve the local ./outcome-qa child and owner')
    inventory = {'format': 1, 'version': version,
                 'files': {name: _digest(data) for name, data in sorted(files.items())}}
    files['MANIFEST.json'] = (json.dumps(inventory, ensure_ascii=True, indent=2) + '\n').encode()
    return version, files


def _output(value):
    path = Path(os.path.abspath(Path(value).expanduser()))
    if path.exists() or _is_link(path):
        raise ValueError('Refusing to overwrite an existing release output')
    if path.is_relative_to(Path(os.path.abspath(ROOT))):
        raise ValueError('Release output must be outside the development source')
    if any(_is_link(parent) for parent in path.parents):
        raise ValueError('Release output ancestors must not be symlinks')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _identity(path):
    info = path.lstat()
    return info.st_dev, info.st_ino


def _mode(path):
    return stat.S_IMODE(path.lstat().st_mode)


def _metadata_from_stat(info):
    return (stat.S_IMODE(info.st_mode), info.st_mtime_ns,
            getattr(info, 'st_uid', 0), getattr(info, 'st_gid', 0))


def _metadata(path):
    return _metadata_from_stat(path.lstat())


def _parents_owned(path, directories):
    return all(not _is_link(parent) and parent.is_dir() and
               _identity(parent) == identity and _mode(parent) == mode
               for parent, identity, mode in directories if parent in path.parents)


def _unchanged_file(path, identity, metadata, expected):
    if _is_link(path):
        return False
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        return (stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity and
                _metadata_from_stat(info) == metadata and
                stream.read(len(expected) + 1) == expected)


def _rollback(files, directories):
    for path, identity, metadata, expected in reversed(files):
        try:
            if (_parents_owned(path, directories) and _unchanged_file(path, identity, metadata, expected) and
                    _identity(path) == identity and _metadata(path) == metadata):
                path.unlink()
        except OSError:
            pass
    for path, identity, mode in reversed(directories):
        try:
            if (_parents_owned(path, directories) and not _is_link(path) and
                    path.is_dir() and _identity(path) == identity and _mode(path) == mode):
                path.rmdir()
        except OSError:
            pass


def _write_staged(path, data, tracked):
    # Track exactly the successfully written prefix. An ordinary short write then
    # failure can be cleaned; changed or uncertain content is preserved instead.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o644)
    record = None
    try:
        info = os.fstat(fd)
        record = [path, (info.st_dev, info.st_ino), _metadata_from_stat(info), b'']
        tracked.append(record)
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0 or count > len(data) - offset:
                raise OSError('Release staging short write')
            offset += count
            record[-1] = data[:offset]
    finally:
        os.close(fd)
        # NTFS may finalize write timestamps on close. Record our completed-write
        # time then; retain the original owner/mode if somebody changed them.
        if record is not None:
            try:
                current = _metadata(path)
                if (not _is_link(path) and _identity(path) == record[1] and
                        current[0] == record[2][0] and current[2:] == record[2][2:]):
                    record[2] = current
            except OSError:
                pass
    if path.read_bytes() != data:
        raise OSError('Release staging read-back mismatch')


def _make_parents(root, relative, directories):
    current = root
    for part in relative.parent.parts:
        current /= part
        known = {path: (identity, mode) for path, identity, mode in directories}.get(current)
        if known is None:
            current.mkdir()  # Exclusive: no merge into a concurrent directory.
            directories.append((current, _identity(current), _mode(current)))
        elif _is_link(current) or (_identity(current), _mode(current)) != known:
            raise OSError('Release directory changed during publication')


def _verify_directory(directory, payloads):
    actual = set()
    expected_dirs = {parent.as_posix() for name in payloads for parent in _relative(name).parents
                     if parent.as_posix() != '.'}
    for path in directory.rglob('*'):
        name = path.relative_to(directory).as_posix()
        if _is_link(path):
            raise ValueError('Symlink appeared in release output')
        if path.is_file():
            actual.add(name)
            if name not in payloads or path.read_bytes() != payloads[name]:
                raise ValueError('Unexpected or changed release output: ' + name)
        elif not path.is_dir() or name not in expected_dirs:
            raise ValueError('Unexpected release output entry: ' + name)
    if actual != set(payloads):
        raise ValueError('Release directory file inventory mismatch')


def build_directory(output):
    version, payloads = prepare()
    output = _output(output)
    created_files, created_dirs = [], []
    staged_files, staged_dirs = [], []
    # All bytes are staged and verified before the public directory is claimed.
    # Cleanup is intentionally nonrecursive: TemporaryDirectory cleanup may chmod
    # a read-only staging hardlink and thereby change a user's published file.
    staging = Path(tempfile.mkdtemp(prefix='.outcome-qa-release-stage-', dir=output.parent))
    staged_dirs.append((staging, _identity(staging), _mode(staging)))
    try:
        for name, data in sorted(payloads.items()):
            relative = _relative(name)
            _make_parents(staging, relative, staged_dirs)
            _write_staged(staging.joinpath(*relative.parts), data, staged_files)
        output.mkdir()  # Exclusive, including a concurrently created empty root.
        created_dirs.append((output, _identity(output), _mode(output)))
        for name in sorted(payloads, key=lambda name: (PurePosixPath(name).name == 'SKILL.md', name)):
            relative = _relative(name)
            path = output.joinpath(*relative.parts)
            if not _parents_owned(path, created_dirs):
                raise OSError('Release directory changed during publication')
            _make_parents(output, relative, created_dirs)
            source = staging.joinpath(*relative.parts)
            identity, metadata = _identity(source), _metadata(source)
            created_files.append((path, identity, metadata, payloads[name]))
            os.link(source, path, follow_symlinks=False)
            if not _unchanged_file(path, identity, metadata, payloads[name]):
                raise OSError('Release file changed during publication')
            # Drop the private hardlink immediately, with no chmod fallback. If a
            # concurrent Windows readonly change prevents unlink, retain it.
            source.unlink()
        _verify_directory(output, payloads)
    except BaseException as exc:
        _rollback(created_files, created_dirs)
        _rollback(staged_files, staged_dirs)
        retained = [str(path) for path in (output, staging) if path.exists() or _is_link(path)]
        if retained and created_dirs:
            raise OSError('Release export incomplete; changed or uncertain paths retained at: '
                          + ', '.join(retained)) from exc
        if staging.exists() or _is_link(staging):
            raise OSError('Release staging incomplete; uncertain data retained at: ' + str(staging)) from exc
        raise
    _rollback(staged_files, staged_dirs)
    if staging.exists() or _is_link(staging):
        raise OSError('Release output created but uncertain staging retained at: ' + str(staging))
    return {'directory': str(output), 'bundle_name': 'outcome-qa-' + version,
            'version': version, 'files': len(payloads), 'profile': 'install-bundle', 'uploaded': False}


def _verify_archive(path, prefix, payloads):
    with zipfile.ZipFile(path) as archive:
        expected = {prefix + name for name in payloads}
        if archive.testzip() is not None or len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise ValueError('Release archive inventory/read-back failed')
        for name, data in payloads.items():
            if archive.read(prefix + name) != data:
                raise ValueError('Release archive content mismatch')


def build_archive(output):
    version, payloads = prepare()
    output = _output(output)
    prefix = 'outcome-qa-' + version + '/'
    stage = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.outcome-qa-release-',
                                         suffix='.zip.tmp', delete=False) as stream:
            stage = Path(stream.name)
        with zipfile.ZipFile(stage, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(payloads.items()):
                archive.writestr(prefix + _relative(name).as_posix(), data)
        _verify_archive(stage, prefix, payloads)
        digest = _digest(stage.read_bytes())
        os.link(stage, output, follow_symlinks=False)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    return {'archive': str(output), 'bundle_name': prefix[:-1], 'version': version,
            'files': len(payloads), 'profile': 'install-bundle', 'sha256': digest, 'uploaded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--output', type=Path, help='New versioned install ZIP')
    target.add_argument('--output-dir', type=Path, help='New directory to use as the install bundle root')
    args = parser.parse_args()
    try:
        result = build_archive(args.output) if args.output is not None else build_directory(args.output_dir)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError, zipfile.BadZipFile) as exc:
        print(terminal(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
