#!/usr/bin/env python3
"""Preview or explicitly manage a small Outcome QA block in one project file.

Coordinate other writers before applying updates. Conflicts observed through commit
verification are preserved; later writes through stale open handles are outside
this guarantee. A successful update leaves no permanent backup of prior content.
"""
import argparse
import difflib
import json
import os
from pathlib import Path
import stat
import tempfile

START = '<!-- outcome-qa:start -->'
END = '<!-- outcome-qa:end -->'
WRITE_LIMIT = ('Coordinate other writers; conflicts observed through commit verification are preserved. '
               'Writes via stale open handles after that point are outside this guarantee.')
LEGACY_0_1_0_LINES = (
    'Use the installed Outcome QA method matching the requested work:',
    '- oq-test-design: planned cases and coverage from requirements; no implied execution.',
    '- oq-explore: actual product journeys, frontend/API behavior and regression exploration.',
    '- oq-automation: write, review or diagnose automated test code and CI failures.',
    '- oq-ai-quality: AI meaning, conversation behavior and saved/tool outcomes.',
    '- oq-checker-audit: reliability of assertions, judges, metrics and evaluation gates.',
    '- oq-retest: replay a claimed fix under equivalent relevant conditions.',
    '- oq-security-journeys: scoped feature security and access/data/action controls.',
    'Load only relevant methods; preserve task scope and host permissions. Missing tools are not executed checks.',
)
LINES = LEGACY_0_1_0_LINES + (
    'Read the exact entrypoint from the current host skill catalogue; never guess a marketplace, cache path or version. '
    'If stale, rediscover the selected method once; if unavailable, state the gap rather than claim it was loaded.',
    'After loading, name the selected method and purpose once before QA actions, unless the requested output format forbids it. '
    'Give execution workers the verified path or loaded instructions; give context-only reviewers excerpts, not file-reading duties.',
)


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def block(newline='\n'):
    return (newline.join((START, *LINES, END)) + newline + newline).encode('utf-8')


def _is_filesystem_root(path):
    # Covers POSIX /, Windows drive roots and UNC share roots alike.
    return path.is_absolute() and path.parent == path


def _project(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    forbidden = {Path('/'), Path.home(), Path.home() / '.codex',
                 Path.home() / '.claude', Path.home() / '.agents'}
    if _is_filesystem_root(path) or path in forbidden:
        raise ValueError('Choose an explicit project directory, not a global configuration directory')
    for ancestor in (path, *path.parents):
        if _is_link(ancestor):
            raise ValueError('Project ancestors must not be symlinks')
    if not path.is_dir():
        raise ValueError('Project must be an existing directory')
    return path


def _read(path):
    if _is_link(path):
        raise ValueError('Instruction file must not be a symlink')
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except FileNotFoundError:
        return None
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Instruction path must be a regular file')
        data = stream.read(4 * 1024 * 1024 + 1)
        if len(data) > 4 * 1024 * 1024:
            raise ValueError('Instruction file exceeds the 4 MiB edit bound')
    data.decode('utf-8')
    return (info.st_dev, info.st_ino, info.st_mtime_ns, stat.S_IMODE(info.st_mode), data)


def _newline(data):
    index = data.find(b'\n')
    return '\r\n' if index > 0 and data[index-1:index] == b'\r' else '\n'


def transform(data, remove=False):
    data.decode('utf-8')
    start, end = START.encode(), END.encode()
    counts = data.count(start), data.count(end)
    if counts == (0, 0):
        if remove:
            return data
        bom = b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b''
        return bom + block(_newline(data)) + data[len(bom):]
    if counts != (1, 1):
        raise ValueError('Duplicate, nested or unbalanced Outcome QA markers')
    begin, finish = data.index(start), data.index(end)
    if begin > finish or (begin and data[begin-1:begin] != b'\n' and data[:begin] != b'\xef\xbb\xbf'):
        raise ValueError('Managed markers must delimit an unchanged complete block')
    after_start = data[begin+len(start):]
    newline = '\r\n' if after_start.startswith(b'\r\n') else '\n'
    current = block(newline)
    legacy = (newline.join((START, *LEGACY_0_1_0_LINES, END)) + newline + newline).encode('utf-8')
    expected = next((candidate for candidate in (current, legacy)
                     if data[begin:begin+len(candidate)] == candidate), None)
    if expected is None:
        raise ValueError('Managed routing block was edited; preserve and reconcile it manually')
    if remove:
        return data[:begin] + data[begin+len(expected):]
    return data[:begin] + current + data[begin+len(expected):]


def _assert_preimage(project, path, snapshot):
    _project(project)
    if _read(path) != snapshot:
        raise ValueError('Instruction file changed while preparing the edit')


def _recover_previous(path, previous, transaction):
    """Restore without replacing a new arrival; retain recovery material on conflict."""
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


def _replace_existing(project, path, snapshot, stage, payload):
    """Move then validate the actual preimage; never rename over destination."""
    staged = _read(stage)
    if staged is None or staged[-1] != payload:
        raise ValueError('Staged routing content changed before publication')
    transaction = Path(tempfile.mkdtemp(dir=project, prefix='.outcome-routing-txn-'))
    previous = transaction / 'previous'
    try:
        _project(project)
        os.rename(path, previous)
        if _read(previous) != snapshot:
            raise ValueError('Instruction file changed at the final move; restoring it')
        _project(project)
        os.link(stage, path)  # A final publication race cannot clobber user bytes.
        if _read(path) != staged:
            raise OSError('Published routing content changed during read-back')
        if _read(previous) != snapshot:
            raise OSError('Previous instruction file changed during publication')
        previous.unlink()
        transaction.rmdir()
    except BaseException as exc:
        recovery = _recover_previous(path, previous, transaction)
        if recovery is not None:
            raise OSError('Routing update incomplete; destination not overwritten; recovery entry retained at: '
                          + str(recovery)) from exc
        raise


def _write(project, path, snapshot, payload):
    _assert_preimage(project, path, snapshot)
    stage = None
    try:
        with tempfile.NamedTemporaryFile(dir=project, prefix='.outcome-routing-', delete=False) as stream:
            stage = Path(stream.name)
            stream.write(payload)
        os.chmod(stage, snapshot[3] if snapshot is not None else 0o600)
        _assert_preimage(project, path, snapshot)
        if snapshot is None:
            os.link(stage, path)
        else:
            _replace_existing(project, path, snapshot, stage, payload)
        if path.read_bytes() != payload:
            raise OSError('Project routing read-back mismatch')
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)


def configure(project, host, apply=False, remove=False):
    if host not in ('codex', 'claude'):
        raise ValueError('Host must be codex or claude')
    project = _project(project)
    path = project / ('AGENTS.md' if host == 'codex' else 'CLAUDE.md')
    snapshot = _read(path)
    before = snapshot[-1] if snapshot is not None else b''
    after = transform(before, remove)
    changed = before != after
    # Zero context exposes only the managed change, not neighboring user secrets.
    # Keep a UTF-8 BOM out of line matching: it moves with the new first line,
    # but is unchanged metadata, not a reason to echo the user's original line.
    diff = ''.join(difflib.unified_diff(before.decode('utf-8-sig').splitlines(keepends=True),
        after.decode('utf-8-sig').splitlines(keepends=True), fromfile=path.name, tofile=path.name, n=0))
    if apply and changed:
        _write(project, path, snapshot, after)
    return {'file': str(path), 'host': host, 'applied': bool(apply and changed),
            'changed': changed, 'removed': bool(remove), 'diff': diff,
            'limit': 'Project routing only; no skills, tools, permissions or global files are installed. '
                     + WRITE_LIMIT}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--host', required=True, choices=('codex', 'claude'))
    parser.add_argument('--apply', action='store_true', help='Write the previewed managed-block change')
    parser.add_argument('--remove', action='store_true', help='Remove only the unchanged managed block')
    args = parser.parse_args()
    try:
        print(json.dumps(configure(args.project, args.host, args.apply, args.remove), ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
