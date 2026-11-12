#!/usr/bin/env python3
"""Export the reviewed runtime only. No tests, labs, source archive or upload."""
import argparse
import hashlib
import json
import stat
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote
import zipfile

from strict_json import identifier, load, terminal
from validate_package import ROOT, SKILLS, validate

OPERATIONS = {'check_transition.py', 'qa_result.py', 'strict_json.py',
              'export_playbook.py', 'install_skills.py', 'install_codex_agents.py', 'project_routing.py'}
DEV_PARTS = {'tests', 'evals', 'examples', '.github', 'distribution', 'work',
             'artifacts', '__pycache__', '.git', '.venv', 'node_modules'}
DEV_FILES = {'demo_app.py', 'boundary_lab.py', 'score_routing.py', 'package.py',
             'build_runtime.py', 'validate_package.py', 'sync_shared.py', 'demo_cases.py'}
ROOT_FILES = {'plugin.json', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'}
REQUIRED = ROOT_FILES | {'.claude-plugin/plugin.json', '.codex-plugin/plugin.json',
    'licenses/gstack-MIT.txt', 'schemas/run.schema.json', 'schemas/transition.schema.json',
    'agents/qa-evidence-reviewer.md', 'agents/qa-test-reviewer.md',
    'adapters/codex/agents/oq-evidence-reviewer.toml', 'adapters/codex/agents/oq-test-reviewer.toml',
    'commands/qa.md', 'commands/qa-retest.md', 'commands/qa-report.md',
    'adapters/claude/session_start.py', 'adapters/claude/hooks.optional.json'}
REQUIRED |= {'scripts/' + name for name in OPERATIONS}
REQUIRED |= {'skills/' + name + suffix for name in SKILLS for suffix in ('/SKILL.md', '/LICENSE.txt', '/agents/openai.yaml')}


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def _relative(value):
    if (not identifier(value) or '\\' in value or ':' in value or
            any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Expected a contained relative file path')
    return Path(value)


def _source(root, relative):
    path = root
    if _is_link(path):
        raise ValueError('Source root must not be a symlink')
    for part in _relative(relative).parts:
        path /= part
        if _is_link(path):
            raise ValueError('Source symlink forbidden: ' + relative)
    if not path.is_file():
        raise ValueError('Missing source file: ' + relative)
    return path


def _allowed(relative):
    path = _relative(relative)
    if (set(path.parts) & DEV_PARTS or path.name in DEV_FILES or
            path.name.startswith('test_') or path.name.startswith('.env') or
            path.suffix in ('.pyc', '.log', '.zip')):
        return False
    if relative in ROOT_FILES or relative in REQUIRED:
        return True
    if path.parts[0] == 'skills':
        return len(path.parts) >= 3 and path.parts[1] in SKILLS and path.suffix in ('.md', '.yaml')
    return False


def _links(payloads):
    """Check shipped local Markdown targets, never follow a URL or source fallback."""
    for relative, data in payloads.items():
        if not relative.endswith('.md'):
            continue
        for destination in re.findall(r'\]\(([^)]+)\)', data.decode('utf-8')):
            if '://' in destination or destination.startswith(('#', 'mailto:')):
                continue
            destination = unquote(destination.split('#', 1)[0])
            if not destination:
                continue
            if destination.startswith('/') or '\\' in destination or ':' in destination:
                raise ValueError('Unsafe runtime link in ' + relative)
            parts = list(Path(relative).parent.parts)
            for part in destination.split('/'):
                if part == '..':
                    if not parts:
                        raise ValueError('Runtime link escapes package: ' + relative)
                    parts.pop()
                elif part not in ('', '.'):
                    parts.append(part)
            target = '/'.join(parts)
            if target not in payloads:
                raise ValueError('Missing runtime link: ' + relative + ' -> ' + destination)


def prepare(root=None):
    root = Path(ROOT if root is None else root).absolute()
    if any(_is_link(path) for path in (root, *root.parents)):
        raise ValueError('Source ancestors must not be symlinks')
    errors = validate(root)
    if errors:
        raise ValueError('; '.join(errors))
    inventory = load(_source(root, 'package-files.json'))
    names = inventory.get('files') if isinstance(inventory, dict) else None
    if (not isinstance(inventory, dict) or type(inventory.get('format')) is not int or inventory['format'] != 1 or
            not isinstance(names, list) or not names):
        raise ValueError('Invalid source inventory')
    for name in names:
        _relative(name)
    if len(names) != len(set(names)):
        raise ValueError('Duplicate source inventory path')
    spec = load(_source(root, 'runtime-files.json'))
    if (not isinstance(spec, dict) or set(spec) != {'format', 'files'} or
            type(spec['format']) is not int or spec['format'] != 1 or
            not isinstance(spec['files'], dict) or not spec['files']):
        raise ValueError('Invalid runtime file mapping')
    mapping = spec['files']
    seen_sources = set()
    payloads = {}
    for destination, source in mapping.items():
        _relative(destination); _relative(source)
        if not _allowed(destination):
            raise ValueError('Developer-only or unsupported runtime destination: ' + destination)
        if source == 'distribution/README.md' and destination == 'README.md':
            pass
        elif source != destination or not _allowed(source):
            raise ValueError('Developer-only source or unsupported remapping: ' + source)
        if source in seen_sources:
            raise ValueError('Duplicate runtime source')
        seen_sources.add(source)
        if source not in names:
            raise ValueError('Runtime source missing from reviewed source inventory: ' + source)
        payloads[destination] = _source(root, source).read_bytes()
    missing = REQUIRED - payloads.keys()
    if missing:
        raise ValueError('Missing required runtime files: ' + ', '.join(sorted(missing)))
    _links(payloads)
    return payloads


def _identity(path):
    info = path.lstat()
    return info.st_dev, info.st_ino


def _file_ownership(path):
    info = path.lstat()
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns)


def _rollback(files, directories):
    """Never recursively remove the output: a concurrent writer may own new entries."""
    for path, ownership, data in reversed(files):
        try:
            if _parents_owned(path, directories) and not _is_link(path) and _file_ownership(path) == ownership and path.read_bytes() == data:
                if _file_ownership(path) == ownership:
                    path.unlink()
        except OSError:
            pass
    for path, identity in reversed(directories):
        try:
            if _parents_owned(path, directories) and not _is_link(path) and _identity(path) == identity:
                path.rmdir()  # Nonempty directories contain an unknown/changed file; preserve them.
        except OSError:
            pass


def _parents_owned(path, directories):
    for parent, identity in directories:
        if parent in path.parents:
            if _is_link(parent) or not parent.is_dir() or _identity(parent) != identity:
                return False
    return True


def _output(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    if path.exists() or _is_link(path):
        raise ValueError('Refusing to overwrite existing output')
    if path.is_relative_to(Path(os.path.abspath(ROOT))):
        raise ValueError('Runtime output must be outside the development source')
    for parent in path.parents:
        if _is_link(parent):
            raise ValueError('Output ancestors must not be symlinks')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_directory(output):
    payloads = prepare()
    output = _output(output)
    created_files, created_dirs = [], []
    try:
        output.mkdir()  # Exclusive, including an empty directory created concurrently.
        created_dirs.append((output, _identity(output)))
        # Entrypoints last: avoid discovery before their reference files exist.
        for name in sorted(payloads, key=lambda n: (Path(n).name == 'SKILL.md', n)):
            path = output / name
            if not _parents_owned(path, created_dirs):
                raise OSError('Output directory changed during publication')
            current = output
            for part in Path(name).parent.parts:
                current /= part
                known = dict(created_dirs).get(current)
                if known is None:
                    current.mkdir()  # Do not merge a concurrent directory.
                    created_dirs.append((current, _identity(current)))
                elif _is_link(current) or _identity(current) != known:
                    raise OSError('Output directory changed during publication')
            with path.open('xb') as stream:
                ownership = _file_ownership(path)
                created_files.append((path, ownership, payloads[name]))
                stream.write(payloads[name])
            written = _file_ownership(path)
            if written[:5] != ownership[:5]:
                raise OSError('Runtime output ownership changed during write')
            # Size and mtime stabilize after close. If writing/closing failed,
            # retain the conservative pre-write snapshot instead of claiming bytes.
            created_files[-1] = (path, written, payloads[name])
            if path.read_bytes() != payloads[name]:
                raise OSError('Runtime output read-back mismatch')
    except BaseException as exc:
        _rollback(created_files, created_dirs)
        if created_dirs and output.exists():
            raise OSError('Runtime export failed; changed or unknown output files were preserved: ' + str(output)) from exc
        raise
    return {'directory': str(output), 'files': len(payloads), 'profile': 'runtime', 'uploaded': False}


def build_archive(output):
    payloads = prepare()
    output = _output(output)
    stage = None
    try:
        # Do not expose a final-looking ZIP until writing, closing and read-back
        # all succeed. A same-filesystem hard link publishes without clobbering
        # a file that appeared while the archive was being prepared.
        with tempfile.NamedTemporaryFile(prefix='.outcome-qa-runtime-', suffix='.zip.tmp',
                                         dir=output.parent, delete=False) as stream:
            stage = Path(stream.name)
        with zipfile.ZipFile(stage, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(payloads.items()):
                archive.writestr('outcome-qa/' + name, data)
        with zipfile.ZipFile(stage) as archive:
            if archive.testzip() is not None or set(archive.namelist()) != {'outcome-qa/' + name for name in payloads}:
                raise ValueError('Runtime archive read-back failed')
            for name, data in payloads.items():
                if archive.read('outcome-qa/' + name) != data:
                    raise ValueError('Runtime archive/source mismatch')
        digest = hashlib.sha256(stage.read_bytes()).hexdigest()
        os.link(stage, output, follow_symlinks=False)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    return {'archive': str(output), 'files': len(payloads), 'profile': 'runtime',
            'sha256': digest, 'uploaded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--output-dir', type=Path)
    target.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = build_directory(args.output_dir) if args.output_dir is not None else build_archive(args.output)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print(terminal(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
