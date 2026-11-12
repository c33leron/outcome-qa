#!/usr/bin/env python3
"""Init-only Codex reviewer installation; dry-run unless --apply is explicit.

Python 3.10+; no network, config edits, model overrides or third-party parser.
This copies the two reviewed adapter files, not arbitrary TOML definitions.
"""
import argparse
import json
import stat
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ('oq-evidence-reviewer', 'oq-test-reviewer')


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def _sources():
    result = {}
    source_dir = ROOT / 'adapters' / 'codex' / 'agents'
    for directory in (ROOT / 'adapters', ROOT / 'adapters/codex', source_dir):
        if _is_link(directory):
            raise ValueError('Adapter source directories must not be symlinks.')
    for name in AGENTS:
        path = source_dir / (name + '.toml')
        if _is_link(path) or not path.is_file():
            raise ValueError(f'Missing or unsafe reviewer source: {name}')
        payload = path.read_bytes()
        text = payload.decode('utf-8')
        # Minimal identity guard for our shipped files, not a general TOML parser.
        if f'name = "{name}"' not in text.splitlines():
            raise ValueError(f'Adapter identity does not match filename: {name}')
        result[name] = payload
    return result


def _fingerprint(path):
    info = path.lstat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_mode, info.st_uid, info.st_gid)


def _unchanged(path, expected, payload):
    return (not _is_link(path) and path.is_file() and _fingerprint(path) == expected
            and path.read_bytes() == payload and _fingerprint(path) == expected)


def install(target: Path, apply: bool = False) -> dict:
    target = target.expanduser().absolute()
    sources = _sources()
    if _is_link(target) or (target.exists() and not target.is_dir()):
        raise ValueError('Target must be a real directory, not a file or symlink.')
    collisions = [name for name in AGENTS
                  if (target / (name + '.toml')).exists()
                  or _is_link(target / (name + '.toml'))]
    if collisions:
        raise ValueError('Refusing to overwrite existing reviewers: ' + ', '.join(collisions))
    result = {
        'applied': False,
        'target': str(target),
        'agents': list(AGENTS),
        'warnings': [
            'These reviewers analyze context supplied by the parent; they do not open files or execute probes.',
            'Feature restrictions are not a separate sandbox; parent permissions and traditional MCP configuration may inherit.',
            'No model setting is overridden. Start a fresh host session and verify actual agent discovery.',
            'Existing agents and global configuration are not changed.',
        ],
    }
    if not apply:
        return result
    target.mkdir(parents=True, exist_ok=True)
    created = []
    retained_stages = []
    try:
        for name, payload in sources.items():
            dest = target / (name + '.toml')
            # Stage complete bytes first. Hard-link publication on the same filesystem
            # is exclusive: a race cannot replace an existing user file, and a write
            # failure cannot leave a partial .toml for Codex to discover.
            stage = None
            expected = None
            try:
                with tempfile.NamedTemporaryFile(prefix='.outcome-qa-agent-', suffix='.tmp',
                                                 dir=target, delete=False) as stream:
                    stage = Path(stream.name)
                    stream.write(payload)
                expected = _fingerprint(stage)
                # Track the owned inode before publication can succeed and then fail.
                created.append((dest, payload, expected))
                os.link(stage, dest)
                if not _unchanged(dest, expected, payload):
                    raise OSError(f'Installed reviewer read-back mismatch: {name}')
            finally:
                if stage is not None:
                    try:
                        if expected is None or _fingerprint(stage) == expected:
                            stage.unlink(missing_ok=True)
                        else:
                            retained_stages.append(stage)
                    except OSError:
                        retained_stages.append(stage)
            if retained_stages:
                raise OSError('Reviewer staging changed or could not be removed safely')
    except Exception as exc:
        remaining = list(retained_stages)
        for dest, payload, expected in reversed(created):
            # Do not remove a file somebody changed while this installation ran.
            try:
                if _unchanged(dest, expected, payload):
                    dest.unlink()
                elif dest.exists() or _is_link(dest):
                    remaining.append(dest)
            except OSError:
                remaining.append(dest)
        if remaining:
            raise OSError('Reviewer installation failed; changed or uncertain files/staging retained at: '
                          + ', '.join(str(path) for path in remaining) + '. Original error: ' + str(exc)) from exc
        raise
    result['applied'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True,
                        help='Explicit Codex agents directory; personal or project-scoped')
    parser.add_argument('--apply', action='store_true', help='Create the two new reviewer files')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.target, args.apply), ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
