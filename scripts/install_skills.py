#!/usr/bin/env python3
"""Explicit, init-only skill installation. Dry-run unless --apply is given."""
import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {'oq-explore', 'oq-automation', 'oq-ai-quality', 'oq-checker-audit', 'oq-retest', 'oq-security-journeys', 'oq-test-design'}


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def _regular(path: Path, label: str) -> None:
    if _is_link(path) or not path.is_file():
        raise ValueError(f'Missing or unsafe {label}: {path.name}')


def _safe_tree(path: Path) -> None:
    if _is_link(path) or not path.is_dir():
        raise ValueError(f'Missing or unsafe source directory: {path.name}')
    for item in path.rglob('*'):
        info = item.lstat()
        if (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400
                or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
            raise ValueError(f'Source contains a symlink or non-regular entry: {item.name}')


def _sources():
    directory = ROOT / 'skills'
    _safe_tree(directory)
    entries = sorted(directory.glob('*/SKILL.md'))
    if {p.name for p in directory.iterdir() if p.is_dir()} != SKILLS or {p.parent.name for p in entries} != SKILLS:
        raise ValueError('Expected the exact complete seven-skill package.')
    for entry in entries:
        _regular(entry, 'skill entrypoint')
        text = entry.read_text(encoding='utf-8')
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:
            raise ValueError(f'Missing skill frontmatter: {entry.parent.name}')
        header = text[4:].split('\n---\n', 1)[0]
        values = [line.partition(':')[2].strip() for line in header.splitlines() if line.startswith('name:')]
        if len(values) != 1 or json.loads(values[0]) != entry.parent.name:
            raise ValueError(f'Skill identity does not match directory: {entry.parent.name}')
    _safe_tree(ROOT / 'licenses')
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt'):
        path = ROOT / name
        _regular(path, 'required provenance file')
        if not path.read_bytes().strip():
            raise ValueError(f'Empty required provenance file: {name}')
    return entries


def _identity(path: Path):
    info = path.lstat()
    return info.st_dev, info.st_ino


def _metadata(path: Path):
    info = path.lstat()
    # Rename changes ctime and reading may change atime; neither means a user edit.
    return info.st_size, info.st_mtime_ns, info.st_mode, info.st_uid, info.st_gid


def _digest(path: Path, identity=None):
    result = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (identity is not None and (info.st_dev, info.st_ino) != identity):
            raise OSError('File changed identity during rollback')
        for chunk in iter(lambda: stream.read(65536), b''):
            result.update(chunk)
    return result.hexdigest()


def _snapshot(directory: Path):
    return {str(p.relative_to(directory)): (_identity(p), _digest(p) if p.is_file() else None,
                                          _metadata(p) if p.is_file() else None)
            for p in directory.rglob('*')}


def _owned_parent(path: Path, root: Path, root_identity, expected):
    """Do not traverse replaced directories or symlinks during rollback."""
    try:
        if _is_link(root) or not root.is_dir() or _identity(root) != root_identity:
            return False
        for parent in reversed(path.relative_to(root).parents):
            if str(parent) == '.':
                continue
            candidate = root / parent
            item = expected.get(str(parent))
            if not item or item[1] is not None or _is_link(candidate) or not candidate.is_dir() or _identity(candidate) != item[0]:
                return False
        return True
    except OSError:
        return False


def _rollback(created):
    """Remove only unchanged staged entries; retain user additions/edits."""
    remaining = []
    for root, root_identity, expected in reversed(created):
        for rel, (identity, digest, metadata) in sorted(expected.items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
            path = root / rel
            try:
                if not _owned_parent(path, root, root_identity, expected) or _is_link(path) or not path.exists():
                    continue
                if _identity(path) != identity:
                    continue
                if digest is not None and path.is_file() and _metadata(path) == metadata and _digest(path, identity) == digest:
                    # A repeated identity check avoids deleting a replaced file after hashing.
                    if _identity(path) == identity and _metadata(path) == metadata:
                        path.unlink()
                elif digest is None and path.is_dir():
                    path.rmdir()  # Unknown additions make this fail rather than get removed.
            except OSError:
                pass
        try:
            if not _is_link(root) and root.is_dir() and _identity(root) == root_identity:
                root.rmdir()
        except OSError:
            pass
        if root.exists() or _is_link(root):
            remaining.append(str(root))
    return remaining


def _publish(source: Path, destination: Path, root: Path, expected: dict):
    """Publish without merging directories or replacing a concurrent file."""
    if source.is_dir():
        destination.mkdir()  # Exclusive claim; never merge into a new arrival.
        expected[str(destination.relative_to(root))] = (_identity(destination), None, None)
        for child in sorted(source.iterdir()):
            _publish(child, destination / child.name, root, expected)
    else:
        # Staging lives on the same filesystem. Unlike rename/move, link is
        # atomic and fails if any entry already occupies destination.
        os.link(source, destination, follow_symlinks=False)
        source.unlink()


def install(target: Path, apply: bool = False) -> dict:
    target = target.expanduser().absolute()
    sources = _sources()  # The same complete preflight runs for preview and apply.
    if _is_link(target) or (target.exists() and not target.is_dir()):
        raise ValueError('Target must be a real directory, not a file or symlink.')
    collisions = [p.parent.name for p in sources if (target / p.parent.name).exists()
                  or _is_link(target / p.parent.name)]
    if collisions:
        raise ValueError('Refusing to overwrite existing skills: ' + ', '.join(collisions))
    result = {'applied': False, 'target': str(target),
              'skills': [p.parent.name for p in sources],
              'warnings': ['Do not enable another overlapping QA bundle in the same evaluation.',
                           'Existing qa-exploratory is not disabled or changed.',
                           'Host discovery requires a new session; this script does not prove activation.']}
    if not apply:
        return result
    target.mkdir(parents=True, exist_ok=True)
    created = []
    staging = Path(tempfile.mkdtemp(prefix='.outcome-qa-stage-', dir=target))
    retain_staging = False
    try:
        for src in sources:
            dest = staging / src.parent.name
            shutil.copytree(src.parent, dest)
            for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
                shutil.copy2(ROOT / name, dest / name)
            shutil.copytree(ROOT / 'licenses', dest / 'licenses')
        # Stage complete contents before publishing anything, including notices.
        snapshots = {src.parent.name: _snapshot(staging / src.parent.name) for src in sources}
        try:
            for src in sources:
                dest = target / src.parent.name
                # mkdir is the exclusive ownership claim; never merge into an existing dir.
                dest.mkdir()
                created.append((dest, _identity(dest), snapshots[src.parent.name]))
                # Publish SKILL.md last so a host cannot discover a half-populated skill.
                for p in sorted((staging / src.parent.name).iterdir(), key=lambda p: (p.name == 'SKILL.md', p.name)):
                    _publish(p, dest / p.name, dest, snapshots[src.parent.name])
        except Exception as exc:
            remaining = _rollback(created)
            if remaining:
                # Stage files can still share an inode with a changed destination.
                # Windows TemporaryDirectory cleanup may chmod read-only files;
                # that would silently change the user's published hardlink too.
                retain_staging = True
                raise OSError('Installation failed; rollback preserved changed, unknown or uncertain files at: '
                              + ', '.join(remaining) + '. Staging retained without modifying shared inodes: '
                              + str(staging) + '. Original error: ' + str(exc)) from exc
            raise
    finally:
        if not retain_staging:
            shutil.rmtree(staging)
    result['applied'] = True
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', required=True, type=Path,
                   help='Explicit host skills directory; e.g. a project .agents/skills')
    p.add_argument('--apply', action='store_true', help='Actually create new skill directories')
    args = p.parse_args()
    try:
        print(json.dumps(install(args.target, args.apply), ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
