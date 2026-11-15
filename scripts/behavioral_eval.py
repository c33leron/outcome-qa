#!/usr/bin/env python3
"""Prepare frozen task-only packets; validate independent behavioral adjudications.

Development-only, offline, Python 3.10+. No model calls or semantic scoring.
External reviewer judgments and declared identities are trusted inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import string
import stat
import tempfile

from qa_result import _artifact_parts
from strict_json import load, loads, identifier

STATUSES = ('completed', 'provider_error', 'timeout', 'invalid', 'not_run')
EXIT = {'PASS': 0, 'FAIL': 1, 'INCOMPLETE': 2, 'FAIL_WITH_GAPS': 2, 'INVALID': 3}
ASSURANCE = ('External reviewer judgments are trusted inputs, not automatic semantic truth. '
             'Hashes bind declared inputs, arms and raw artifacts, not authorship, actual loading, '
             'or completeness of unregistered executions. This is a bounded development experiment, '
             'not a hidden benchmark or a claim of agent superiority.')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def obj(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys.split()), f'{name}: wrong fields')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def slug(value):
    return (isinstance(value, str) and 0 < len(value) <= 100 and value not in ('.', '..')
            and all(c in string.ascii_letters + string.digits + '-_.' for c in value))


def digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in string.hexdigits for c in value)


def rows(value, key, name):
    require(isinstance(value, list) and value, f'{name}: nonempty list required')
    result = {}
    for row in value:
        require(isinstance(row, dict) and identifier(row.get(key)), f'{name}: missing or invalid {key}')
        require(row[key] not in result, f'{name}: duplicate {key}')
        result[row[key]] = row
    return result


def version(data, keys, name):
    obj(data, 'version ' + keys, name)
    require(type(data['version']) is int and data['version'] == 1, f'{name}: expected version 1')


def source_cases(data):
    version(data, 'cases', 'source')
    index = rows(data['cases'], 'id', 'cases')
    for case in index.values():
        obj(case, 'id prompt expected', 'case')
        require(slug(case['id']) and text(case['prompt']), 'case: safe id and nonblank prompt required')
        obj(case['expected'], 'outcome adherence method', 'expected')
        require(all(text(v) for v in case['expected'].values()), 'expected: nonblank rubric fields required')
    return index


def check_arms(arms):
    index = rows(arms, 'id', 'arms')
    for arm in index.values():
        obj(arm, 'id source_sha256 description', 'arm')
        require(slug(arm['id']) and digest(arm['source_sha256']) and text(arm['description']), 'arm: invalid identity')
    return index


def planned(cases, arms, repeats):
    require(type(repeats) is int and 1 <= repeats <= 100, 'repeats: integer from 1 to 100 required')
    result = []
    for case in cases:
        for arm in arms:
            for repeat in range(1, repeats + 1):
                result.append({'trial_id': f't{len(result) + 1:06d}', 'case_id': case['id'],
                               'arm_id': arm['id'], 'repeat': repeat,
                               'input_sha256': case['packet']['sha256']})
    return result


def prepare(cases_path, arms_path, out, repeats):
    source = load(cases_path)
    cases = source_cases(source)
    arms = load(arms_path)
    check_arms(arms)
    packets = []
    payloads = {}
    for index, case in enumerate(cases.values(), 1):
        path = f"packets/p{index:06d}.json"
        raw = canonical({'id': case['id'], 'prompt': case['prompt']})
        payloads[path] = raw
        packets.append({'id': case['id'], 'packet': {'path': path, 'sha256': sha(raw)}})
    raw_source = canonical(source)
    manifest = {'version': 1, 'source': {'path': 'source.json', 'sha256': sha(raw_source)},
                'arms': arms, 'cases': packets, 'repeats': repeats,
                'planned_trials': planned(packets, arms, repeats)}
    payloads['source.json'] = raw_source
    payloads['manifest.json'] = canonical(manifest)
    out = Path(out)
    publish(out, payloads)
    return {'manifest_sha256': sha(canonical(manifest)), 'planned': len(manifest['planned_trials']),
            'packet_directory': str(out / 'packets'),
            'note': 'Give performers only their packet, never source.json, manifest or reviewer rubric.'}


def file_identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def discard_unchanged(files, directories):
    """No recursive deletion: retain unknown, replaced or modified entries."""
    for path, original, expected in reversed(files):
        try:
            if file_identity(path.lstat()) != file_identity(original):
                continue
            if sha(read_regular(path.parent, [path.name])) == expected:
                # Recheck identity after the read; changed user content stays put.
                if file_identity(path.lstat()) == file_identity(original):
                    path.unlink()
        except (OSError, ValueError):
            pass
    for path, original in reversed(directories):
        try:
            current = path.lstat()
            if (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino):
                path.rmdir()  # A concurrent/unrecognized addition prevents removal.
        except OSError:
            pass


def publish(out, payloads):
    """Stage complete bytes before reserving output; publish with no overwrite."""
    if out.exists() or out.is_symlink():
        raise FileExistsError('output already exists')
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{out.name}.prepare-', dir=out.parent))
    staged_files, staged_dirs, published_files, published_dirs = [], [(stage, stage.lstat())], [], []
    try:
        (stage / 'packets').mkdir()
        staged_dirs.append((stage / 'packets', (stage / 'packets').lstat()))
        for relative, raw in payloads.items():
            path = stage / relative
            with path.open('xb') as stream:
                require(stream.write(raw) == len(raw), 'preparation: incomplete write')
                stream.flush()
                staged_files.append((path, os.fstat(stream.fileno()), sha(raw)))
        out.mkdir()  # Exclusive: a concurrent destination is never replaced.
        published_dirs.append((out, out.lstat()))
        (out / 'packets').mkdir()
        published_dirs.append((out / 'packets', (out / 'packets').lstat()))
        for relative, raw in payloads.items():
            destination = out / relative
            os.link(stage / relative, destination, follow_symlinks=False)
            published_files.append((destination, destination.lstat(), sha(raw)))
    except BaseException:
        discard_unchanged(published_files, published_dirs)
        raise
    finally:
        # A failed partial write or concurrent file may leave staging residue,
        # never a blocked final output from a staging-write failure.
        discard_unchanged(staged_files, staged_dirs)


def read_regular(base, parts):
    """Return bytes from the same no-follow regular-file handle we validate."""
    def inspect():
        current = base
        info = None
        for index, part in enumerate(parts):
            current = current / part
            info = current.lstat()
            reparse = getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
            require(not stat.S_ISLNK(info.st_mode) and not reparse, 'artifact: symlinks/reparse points forbidden')
            require(stat.S_ISDIR(info.st_mode) if index < len(parts) - 1 else stat.S_ISREG(info.st_mode),
                    'artifact: expected directories and a regular file')
        return info

    original = inspect()
    fd = directory_fd = None
    try:
        anchored = os.open in os.supports_dir_fd and hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY')
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        if anchored:
            directory_fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            fd = os.open(parts[-1], flags, dir_fd=directory_fd)
        else:
            fd = os.open(base.joinpath(*parts), flags)
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino) == (original.st_dev, original.st_ino),
                'artifact: file changed during open')
        if not anchored:
            current = inspect()
            require((current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino),
                    'artifact: path changed during open')
        with os.fdopen(fd, 'rb') as stream:
            fd = None
            return stream.read()
    finally:
        if fd is not None:
            os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def artifact(base, descriptor, with_id=False):
    obj(descriptor, 'id path sha256' if with_id else 'path sha256', 'artifact')
    require(digest(descriptor['sha256']), 'artifact: invalid SHA-256')
    raw = read_regular(base, _artifact_parts(descriptor['path']))
    require(sha(raw) == descriptor['sha256'].lower(), 'artifact: SHA-256 mismatch')
    return raw


def manifest_data(path):
    data = load(path)
    version(data, 'source arms cases repeats planned_trials', 'manifest')
    check_arms(data['arms'])
    base = Path(path).parent.resolve(strict=True)
    source = source_cases(loads(artifact(base, data['source']).decode('utf-8')))
    cases = rows(data['cases'], 'id', 'manifest cases')
    require(set(cases) == set(source), 'manifest cases must match frozen source')
    for case in cases.values():
        obj(case, 'id packet', 'manifest case')
        raw = artifact(base, case['packet'])
        require(raw == canonical({'id': case['id'], 'prompt': source[case['id']]['prompt']}),
                'packet: not the frozen task-only input')
    require(canonical(data['planned_trials']) == canonical(planned(data['cases'], data['arms'], data['repeats'])),
            'manifest: exact planned case/arm/repeat coverage required')
    return data


def evidence(refs, artifacts):
    require(isinstance(refs, list), 'evidence: list required')
    kinds = set()
    for ref in refs:
        obj(ref, 'artifact_id line_start line_end quote', 'evidence')
        aid, start, end = ref['artifact_id'], ref['line_start'], ref['line_end']
        require(isinstance(aid, str) and aid in artifacts, 'evidence: unknown artifact')
        lines = artifacts[aid].splitlines()
        require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
                'evidence: invalid one-based inclusive line range')
        require(text(ref['quote']) and ref['quote'] == '\n'.join(lines[start - 1:end]),
                'evidence: quote does not match raw artifact lines')
        kinds.add(aid)
    return kinds


def evaluate(manifest_path, trials_path, reviews_path, artifact_root):
    result = {'valid': False, 'verdict': 'INVALID', 'experiment': 'INVALID', 'quality': 'INVALID',
              'planned': 0, 'statuses': {status: 0 for status in STATUSES},
              'dimensions': {'outcome': {'passed': 0, 'failed': 0, 'unknown': 0},
                             'adherence': {'passed': 0, 'failed': 0, 'unknown': 0},
                             'observed_method': {'loaded': 0, 'not_loaded': 0, 'unknown': 0}},
              'trial_results': [], 'failures': [], 'gaps': [], 'issues': [], 'assurance': ASSURANCE}
    try:
        manifest = manifest_data(manifest_path)
        manifest_sha = sha(canonical(manifest))
        expected = rows(manifest['planned_trials'], 'trial_id', 'planned trials')
        result['planned'] = len(expected)
        records, decisions = load(trials_path), load(reviews_path)
        for data, key in ((records, 'trials'), (decisions, 'reviews')):
            version(data, f'manifest_sha256 {key}', key)
            require(data['manifest_sha256'] == manifest_sha, f'{key}: manifest binding mismatch')
        trials, reviews = rows(records['trials'], 'trial_id', 'trials'), rows(decisions['reviews'], 'trial_id', 'reviews')
        require(set(trials) == set(expected) == set(reviews), 'Exact planned trial and review coverage required')
        base = Path(artifact_root).resolve(strict=True)
        for tid, plan in expected.items():
            try:
                trial, review = trials[tid], reviews[tid]
                obj(trial, 'trial_id case_id arm_id input_sha256 status performer_id notes artifacts', 'trial')
                require(all(trial[k] == plan[k] for k in ('trial_id', 'case_id', 'arm_id', 'input_sha256')),
                        'trial: input/arm/case binding mismatch')
                require(trial['status'] in STATUSES and identifier(trial['performer_id']) and text(trial['notes']),
                        'trial: invalid status/performer/notes')
                result['statuses'][trial['status']] += 1
                require(isinstance(trial['artifacts'], list), 'trial artifacts: list required')
                artifacts = {}
                for desc in trial['artifacts']:
                    require(isinstance(desc, dict) and desc.get('id') in ('transcript', 'tool_trace'), 'artifact: unknown kind')
                    require(desc['id'] not in artifacts, 'artifact: duplicate kind')
                    artifacts[desc['id']] = artifact(base, desc, True).decode('utf-8')
                    require(text(artifacts[desc['id']]), 'artifact: empty raw record')
                require(trial['status'] == 'not_run' or 'transcript' in artifacts,
                        'trial: raw transcript or error record required for every attempted run')
                obj(review, 'trial_id trial_sha256 reviewer_id outcome adherence observed_method', 'review')
                require(review['trial_sha256'] == sha(canonical(trial)), 'review: trial/artifact binding mismatch')
                require(identifier(review['reviewer_id']) and review['reviewer_id'] != trial['performer_id'],
                        'review: independent reviewer identity required')
                completed = trial['status'] == 'completed'
                if not completed:
                    result['gaps'].append(f"{tid}: {trial['status']} (retained attempt)")
                observed = {'trial_id': tid, 'case_id': plan['case_id'], 'arm_id': plan['arm_id'],
                            'status': trial['status']}
                for dimension, field in (('outcome', 'pass'), ('adherence', 'pass'), ('observed_method', 'loaded')):
                    judgment = review[dimension]
                    obj(judgment, field + ' reason evidence', dimension)
                    value = judgment[field]
                    require(value is None or type(value) is bool, f'{dimension}: boolean or null required')
                    require(text(judgment['reason']), f'{dimension}: reason required')
                    kinds = evidence(judgment['evidence'], artifacts)
                    if dimension != 'observed_method':
                        require(completed or value is None, 'Noncompleted attempt cannot receive quality pass/fail')
                        require(value is None or 'transcript' in kinds, f'{dimension}: transcript evidence required')
                        bucket = 'unknown' if value is None else ('passed' if value else 'failed')
                        if value is False:
                            result['failures'].append(f'{tid}: {dimension}')
                    else:
                        require(value is None or 'tool_trace' in kinds,
                                'observed_method: raw tool trace required, naming a method is not a read')
                        bucket = 'unknown' if value is None else ('loaded' if value else 'not_loaded')
                    observed[dimension] = value
                    result['dimensions'][dimension][bucket] += 1
                    if value is None:
                        result['gaps'].append(f'{tid}: {dimension} unmeasured')
                result['trial_results'].append(observed)
            except (ValueError, OSError, TypeError, KeyError) as error:
                result['issues'].append(f'{tid}: {safe_error(error)}')
        if not result['issues']:
            result['valid'] = True
            failed = bool(result['failures'])
            quality_gap = any(result['dimensions'][dim]['unknown'] for dim in ('outcome', 'adherence'))
            result['quality'] = verdict(failed, quality_gap)
            result['experiment'] = 'INCOMPLETE' if result['gaps'] else 'COMPLETE'
            result['verdict'] = verdict(failed, bool(result['gaps']))
    except (ValueError, OSError, TypeError, KeyError) as error:
        result['issues'].append(safe_error(error))
    return result


def safe_error(error):
    # Do not leak absolute paths or raw artifacts into shareable error output.
    return str(error) if isinstance(error, ValueError) and not isinstance(error, UnicodeError) else type(error).__name__


def verdict(failed, gaps):
    return ('FAIL_WITH_GAPS' if failed else 'INCOMPLETE') if gaps else ('FAIL' if failed else 'PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pre = sub.add_parser('prepare')
    pre.add_argument('cases')
    pre.add_argument('--arms', required=True, help='JSON array of id/source_sha256/description')
    pre.add_argument('--out', required=True)
    pre.add_argument('--repeats', type=int, default=1)
    score = sub.add_parser('score')
    score.add_argument('manifest')
    score.add_argument('--trials', required=True)
    score.add_argument('--reviews', required=True)
    score.add_argument('--artifact-root', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.cases, args.arms, args.out, args.repeats)
        else:
            result = evaluate(args.manifest, args.trials, args.reviews, args.artifact_root)
    except (ValueError, OSError, TypeError, KeyError) as error:
        result = {'valid': False, 'verdict': 'INVALID', 'issues': [safe_error(error)], 'assurance': ASSURANCE}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return EXIT.get(result.get('verdict'), 0)


if __name__ == '__main__':
    raise SystemExit(main())
