#!/usr/bin/env python3
"""Check or explicitly materialize shared references into self-contained skills.

Coordinate other writers before applying updates. Conflicts observed through commit
verification are preserved; later writes through stale open handles are outside
this guarantee. A successful update leaves no permanent backup of prior content.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from strict_json import load, terminal

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {'oq-explore', 'oq-test-design', 'oq-automation', 'oq-ai-quality',
          'oq-checker-audit', 'oq-retest', 'oq-security-journeys'}
NAMES = {'voice.md', 'trust-boundary.md', 'human-data.md', 'skill-start.md'}
HEADER = re.compile(rb'<!-- outcome-qa:generated source=(shared/[a-z-]+\.md) sha256=([a-f0-9]{64}) -->\n')
WRITE_LIMIT = ('Coordinate other writers; conflicts observed through commit verification are preserved. '
               'Writes via stale open handles after that point are outside this guarantee.')


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def _root(root):
    root = Path(os.path.abspath(Path(root).expanduser()))
    for path in (root, *root.parents):
        if _is_link(path):
            raise ValueError('Symlink source ancestors are not supported')
    if not root.is_dir():
        raise ValueError('Source root must be an existing directory')
    return root


def _path(root, relative):
    current = root
    for part in Path(relative).parts:
        current /= part
        if _is_link(current):
            raise ValueError('Symlink in shared reference path: ' + relative)
    return current


def _read(path):
    """Snapshot regular bytes and identity without following a final symlink."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except FileNotFoundError:
        return None
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Expected a regular shared reference file')
        data = stream.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError('Shared reference exceeds the 1 MiB bound')
    data.decode('utf-8')
    return (info.st_dev, info.st_ino, info.st_mtime_ns, stat.S_IMODE(info.st_mode), data)


def render(source, body):
    digest = hashlib.sha256(body).hexdigest()
    return f'<!-- outcome-qa:generated source={source} sha256={digest} -->\n'.encode() + body


def _owned(snapshot, source):
    if snapshot is None:
        return
    data = snapshot[-1]
    header = HEADER.match(data)
    if (not header or header[1].decode() != source or
            hashlib.sha256(data[header.end():]).hexdigest().encode() != header[2]):
        raise ValueError('Generated reference was manually changed or has no valid ownership header')


def prepare(root=ROOT):
    root = _root(root)
    spec_path = _path(root, 'shared-references.json')
    spec = load(spec_path)
    if (not isinstance(spec, dict) or set(spec) != {'format', 'files'} or
            type(spec['format']) is not int or spec['format'] != 1 or
            not isinstance(spec['files'], dict) or not spec['files']):
        raise ValueError('Expected format 1 and a nonempty shared-reference mapping')
    mapping = spec['files']
    plan = []
    for destination, source in mapping.items():
        if not isinstance(destination, str) or not isinstance(source, str):
            raise ValueError('Shared-reference paths must be strings')
        parts = destination.split('/')
        if (len(parts) != 5 or parts[0] != 'skills' or parts[1] not in SKILLS or
                parts[2:4] != ['references', '_shared'] or parts[4] not in NAMES or
                source != 'shared/' + parts[4]):
            raise ValueError('Unsupported shared source/destination mapping')
        source_snapshot = _read(_path(root, source))
        if source_snapshot is None or not source_snapshot[-1].strip():
            raise ValueError('Missing or empty canonical shared reference: ' + source)
        path = _path(root, destination)
        snapshot = _read(path)
        _owned(snapshot, source)
        plan.append((destination, source, snapshot, render(source, source_snapshot[-1])))
    # Every existing generated file must be explicitly declared; no implicit cleanup.
    for skill in sorted(SKILLS):
        directory = _path(root, f'skills/{skill}/references/_shared')
        if directory.exists():
            if not directory.is_dir():
                raise ValueError('Generated reference parent is not a directory')
            for path in directory.iterdir():
                relative = path.relative_to(root).as_posix()
                if _is_link(path) or not path.is_file() or relative not in mapping:
                    raise ValueError('Unknown generated reference entry: ' + relative)
    return root, plan


def check(root=ROOT):
    """Return validation errors without writing anything."""
    try:
        _, plan = prepare(root)
        return ['Missing or stale shared reference: ' + destination
                for destination, _, snapshot, payload in plan
                if snapshot is None or snapshot[-1] != payload]
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        return [str(exc)]


def _mkdirs(root, relative):
    current = root
    for part in Path(relative).parent.parts:
        current /= part
        if _is_link(current):
            raise ValueError('Shared reference parent became a symlink')
        try:
            current.mkdir()
        except FileExistsError:
            if _is_link(current) or not current.is_dir():
                raise ValueError('Shared reference parent is not a real directory')


def _check_snapshot(root, relative, expected):
    path = _path(root, relative)
    if _read(path) != expected:
        raise ValueError('Shared reference changed during publication: ' + relative)
    return path


def _recover_previous(path, previous, transaction):
    """Restore no-clobber or retain both versions with a recovery path."""
    if previous.exists() or _is_link(previous):
        try:
            os.link(previous, path, follow_symlinks=False)
            left, right = previous.lstat(), path.lstat()
            if (left.st_dev, left.st_ino) != (right.st_dev, right.st_ino):
                return previous
            previous.unlink()
        except OSError:
            return previous
    try:
        transaction.rmdir()
    except OSError:
        return transaction
    return None


def _replace_existing(root, relative, path, snapshot, stage, payload):
    staged = _read(stage)
    if staged is None or staged[-1] != payload:
        raise ValueError('Staged shared content changed before publication')
    transaction = Path(tempfile.mkdtemp(dir=path.parent, prefix='.outcome-shared-txn-'))
    previous = transaction / 'previous'
    try:
        _path(root, relative)
        os.rename(path, previous)
        if _read(previous) != snapshot:
            raise ValueError('Shared reference changed at the final move; restoring it')
        _path(root, relative)
        os.link(stage, path)
        if _read(path) != staged:
            raise OSError('Published shared reference changed during read-back')
        if _read(previous) != snapshot:
            raise OSError('Previous shared reference changed during publication')
        previous.unlink()
        transaction.rmdir()
    except BaseException as exc:
        recovery = _recover_previous(path, previous, transaction)
        if recovery is not None:
            raise OSError('Shared update incomplete; destination not overwritten; recovery entry retained at: '
                          + str(recovery)) from exc
        raise


def _publish(root, relative, snapshot, payload):
    _mkdirs(root, relative)
    path = _check_snapshot(root, relative, snapshot)
    stage = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.outcome-shared-', delete=False) as stream:
            stage = Path(stream.name)
            stream.write(payload)
        os.chmod(stage, snapshot[3] if snapshot is not None else 0o644)
        _check_snapshot(root, relative, snapshot)
        if snapshot is None:
            os.link(stage, path)  # A concurrent new file is never replaced.
        else:
            _replace_existing(root, relative, path, snapshot, stage, payload)
        if path.read_bytes() != payload:
            raise OSError('Shared reference read-back mismatch')
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)


def sync(root=ROOT, write=False):
    root, plan = prepare(root)  # Validate every destination before publishing any.
    changed = [item for item in plan if item[2] is None or item[2][-1] != item[3]]
    if write:
        for destination, _, snapshot, payload in changed:
            _publish(root, destination, snapshot, payload)
    return {'written': bool(write), 'changed': [item[0] for item in changed],
            'checked': len(plan), 'valid': not check(root), 'limit': WRITE_LIMIT}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate declared unchanged-owned references')
    parser.add_argument('--check', action='store_true', help='Check only (the default)')
    args = parser.parse_args()
    if args.write and args.check:
        parser.error('--write and --check are mutually exclusive')
    try:
        result = sync(write=args.write)
        print(json.dumps(result, indent=2))
        return 0 if result['valid'] else 1
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print(json.dumps({'valid': False, 'error': terminal(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
