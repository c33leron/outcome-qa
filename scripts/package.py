#!/usr/bin/env python3
"""Build a private/source ZIP from an explicit allowlist; never uploads anything."""
import argparse
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path
from validate_package import ROOT, validate
from strict_json import load as load_json, terminal, identifier

IGNORED_PARTS = {'__pycache__', '.git', '.venv', 'node_modules'}


def _is_link(path):
    """Reject symlinks and Windows reparse points, including NTFS junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def build(output):
    errors = validate(ROOT)
    if errors:
        raise ValueError('; '.join(errors))
    output = Path(os.path.abspath(Path(output).expanduser()))
    if output.exists() or _is_link(output):
        raise ValueError('Refusing to overwrite an archive; choose a new output path.')
    if output.is_relative_to(Path(os.path.abspath(ROOT))):
        raise ValueError('Write the archive outside the package directory.')
    if any(_is_link(parent) for parent in output.parents):
        raise ValueError('Output ancestors must not be symlinks or reparse points.')
    inventory = load_json(ROOT / 'package-files.json')
    names = inventory.get('files')
    if inventory.get('format') != 1 or not isinstance(names, list) or not names:
        raise ValueError('Invalid release inventory')
    if any(not identifier(n) or '\\' in n or ':' in n or
           any(p in ('', '.', '..') for p in n.split('/')) for n in names):
        raise ValueError('Release inventory paths must be contained relative files')
    if len(set(names)) != len(names):
        raise ValueError('Duplicate release inventory path')
    expected = set(names)
    members = []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == 'artifacts' or any(p in IGNORED_PARTS for p in rel.parts):
            continue
        if path.name == '.DS_Store':
            continue
        if _is_link(path):
            raise ValueError(f'Symlink forbidden: {rel}')
        if path.is_file():
            if rel.as_posix() not in expected:
                raise ValueError(f'Unlisted file; review before explicitly changing package-files.json: {rel}')
            if path.name.startswith('.env') or path.suffix in ('.pyc', '.zip', '.log'):
                raise ValueError(f'Unexpected artifact: {rel}')
            members.append(path)
    actual = {p.relative_to(ROOT).as_posix() for p in members}
    if actual != expected:
        raise ValueError('Missing inventoried files: ' + ', '.join(sorted(expected - actual)))
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.outcome-qa-source-', suffix='.zip.tmp',
                                         dir=output.parent, delete=False) as stream:
            stage = Path(stream.name)
        with zipfile.ZipFile(stage, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for path in members:
                z.write(path, 'outcome-qa/' + path.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(stage) as z:
            expected_names = {'outcome-qa/' + name for name in expected}
            if z.testzip() is not None or len(z.namelist()) != len(members) or set(z.namelist()) != expected_names:
                raise ValueError('Archive read-back failed')
            for path in members:
                if z.read('outcome-qa/' + path.relative_to(ROOT).as_posix()) != path.read_bytes():
                    raise ValueError('Archive/source content mismatch')
        digest = hashlib.sha256(stage.read_bytes()).hexdigest()
        os.link(stage, output, follow_symlinks=False)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    return {'archive': str(output), 'files': len(members), 'sha256': digest,
            'uploaded': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(build(args.output), indent=2))
    except (OSError, ValueError) as exc:
        p.exit(2, terminal(exc) + '\n')
