"""Real CLI controls; these test the evaluator boundary, not agent quality."""
from __future__ import annotations

import copy
import hashlib
import json
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'behavioral_eval.py'
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location('behavioral_eval', SCRIPT)
behavioral_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(behavioral_eval)


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class BehavioralEvalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.cases = {'version': 1, 'cases': [
            {'id': 'healthy', 'prompt': 'Read-only: did the correction persist?',
             'expected': {'outcome': 'Recognize a healthy corrected value.',
                          'adherence': 'No writes; no invented defect.',
                          'method': 'Loading is observed separately.'}}]}
        self.arms = [{'id': 'prior', 'source_sha256': 'a' * 64, 'description': 'Explicit prior skill'},
                     {'id': 'candidate', 'source_sha256': 'b' * 64, 'description': 'Explicit candidate skill'}]
        self.write('cases.json', self.cases)
        self.write('arms.json', self.arms)

    def write(self, name, data):
        path = self.base / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return path

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                text=True, capture_output=True)
        # Missing implementation is an assertion failure, not an import/setup error.
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def prepare(self, repeats=1):
        code, result = self.run_cli('prepare', self.base / 'cases.json', '--arms', self.base / 'arms.json',
                                   '--out', self.base / 'experiment', '--repeats', repeats)
        self.assertEqual(code, 0, result)
        self.manifest_path = self.base / 'experiment' / 'manifest.json'
        self.manifest = json.loads(self.manifest_path.read_text())
        self.assertEqual(result['manifest_sha256'], digest(self.manifest))
        return result

    def artifact(self, name, content):
        path = self.base / name
        path.write_text(content, encoding='utf-8')
        return {'id': 'transcript' if 'answer' in name else 'tool_trace',
                'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def ref(self, kind='transcript'):
        return {'artifact_id': kind, 'line_start': 1, 'line_end': 1,
                'quote': 'Read-back value is correct.' if kind == 'transcript' else 'Read exact skill entrypoint; complete output.'}

    def healthy(self, repeats=1):
        self.prepare(repeats)
        self.trials = {'version': 1, 'manifest_sha256': digest(self.manifest), 'trials': []}
        self.reviews = {'version': 1, 'manifest_sha256': digest(self.manifest), 'reviews': []}
        for index, plan in enumerate(self.manifest['planned_trials']):
            trial = {k: plan[k] for k in ('trial_id', 'case_id', 'arm_id', 'input_sha256')}
            trial.update(status='completed', performer_id=f'performer-{index}', notes='Synthetic fixture', artifacts=[
                self.artifact(f'answer-{index}.txt', 'Read-back value is correct.\nNo defect.\n'),
                self.artifact(f'tools-{index}.txt', 'Read exact skill entrypoint; complete output.\n')])
            self.trials['trials'].append(trial)
            self.reviews['reviews'].append({
                'trial_id': trial['trial_id'], 'trial_sha256': digest(trial), 'reviewer_id': 'independent-reviewer',
                'outcome': {'pass': True, 'reason': 'Correction is healthy.', 'evidence': [self.ref()]},
                'adherence': {'pass': True, 'reason': 'No changes or scope expansion.', 'evidence': [self.ref()]},
                'observed_method': {'loaded': True, 'reason': 'Actual completed read.', 'evidence': [self.ref('tool_trace')]}})

    def rebind(self):
        by_id = {r['trial_id']: r for r in self.reviews['reviews']}
        for trial in self.trials['trials']:
            if trial['trial_id'] in by_id:
                by_id[trial['trial_id']]['trial_sha256'] = digest(trial)

    def score(self):
        return self.run_cli('score', self.manifest_path, '--trials', self.write('trials.json', self.trials),
                            '--reviews', self.write('reviews.json', self.reviews), '--artifact-root', self.base)

    def assert_invalid(self):
        code, result = self.score()
        self.assertEqual((code, result['verdict']), (3, 'INVALID'), result)
        self.assertFalse(result['valid'])
        self.assertTrue(result['issues'])

    def test_prepare_exposes_only_task_packet_and_freezes_input_bytes(self):
        self.prepare(repeats=2)
        self.assertEqual(len(self.manifest['planned_trials']), 4)
        packet = self.manifest['cases'][0]['packet']
        raw = (self.manifest_path.parent / packet['path']).read_bytes()
        self.assertEqual(json.loads(raw), {'id': 'healthy', 'prompt': self.cases['cases'][0]['prompt']})
        self.assertNotIn(b'expected', raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), packet['sha256'])
        self.assertEqual(self.manifest['arms'], self.arms)

    def test_prepare_never_overwrites_frozen_experiment(self):
        self.prepare()
        code, result = self.run_cli('prepare', self.base / 'cases.json', '--arms', self.base / 'arms.json',
                                   '--out', self.base / 'experiment')
        self.assertEqual(code, 3, result)

    def test_full_healthy_control_passes_without_mutating_inputs(self):
        self.healthy()
        before = copy.deepcopy((self.trials, self.reviews))
        code, result = self.score()
        self.assertEqual((code, result['verdict'], result['experiment'], result['quality']), (0, 'PASS', 'COMPLETE', 'PASS'), result)
        self.assertEqual(result['dimensions']['outcome'], {'passed': 2, 'failed': 0, 'unknown': 0})
        self.assertEqual(result['planned'], 2)
        self.assertEqual([row['arm_id'] for row in result.get('trial_results', [])], ['prior', 'candidate'])
        self.assertTrue(all(row['outcome'] is True for row in result.get('trial_results', [])))
        self.assertEqual(before, (self.trials, self.reviews))

    def test_correct_inline_answer_is_not_failure_for_no_skill_load(self):
        self.healthy()
        self.reviews['reviews'][0]['observed_method']['loaded'] = False
        code, result = self.score()
        self.assertEqual((code, result['quality']), (0, 'PASS'), result)
        self.assertEqual(result['dimensions']['observed_method']['not_loaded'], 1)

    def test_unknown_method_keeps_outcome_pass_but_not_whole_experiment_success(self):
        self.healthy()
        self.trials['trials'][0]['artifacts'].pop()
        self.reviews['reviews'][0]['observed_method'] = {'loaded': None, 'reason': 'No tool trace supplied.', 'evidence': []}
        self.rebind()
        code, result = self.score()
        self.assertEqual((code, result['verdict'], result['quality']), (2, 'INCOMPLETE', 'PASS'), result)
        self.assertEqual(result['dimensions']['outcome']['passed'], 2)

    def test_method_name_without_trace_cannot_claim_loaded(self):
        self.healthy()
        self.reviews['reviews'][0]['observed_method']['evidence'] = [self.ref()]
        self.assert_invalid()

    def test_empty_or_missing_or_duplicate_reviews_are_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.reviews['reviews'])
        for rows in ([], original[:1], original + [original[0]]):
            with self.subTest(rows=len(rows)):
                self.reviews['reviews'] = rows
                self.assert_invalid()

    def test_missing_trial_id_and_duplicate_trials_are_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.trials['trials'])
        for rows in ([], original[:1], original + [original[0]], [dict(original[0], trial_id='unknown'), original[1]]):
            with self.subTest(rows=rows):
                self.trials['trials'] = rows
                self.assert_invalid()

    def test_omitted_failed_repeat_cannot_improve_denominator(self):
        self.healthy(repeats=2)
        self.trials['trials'].pop()
        self.reviews['reviews'].pop()
        self.assert_invalid()

    def test_noncompleted_attempts_are_retained_not_quality_failures(self):
        self.healthy(repeats=2)
        for trial, review, status in zip(self.trials['trials'], self.reviews['reviews'], ('provider_error', 'timeout', 'invalid', 'not_run')):
            trial['status'] = status
            for key in ('outcome', 'adherence'):
                review[key] = {'pass': None, 'reason': status, 'evidence': []}
            review['observed_method'] = {'loaded': None, 'reason': status, 'evidence': []}
        self.rebind()
        code, result = self.score()
        self.assertEqual((code, result['verdict']), (2, 'INCOMPLETE'), result)
        self.assertEqual(result['planned'], 4)
        self.assertEqual(result['dimensions']['outcome']['failed'], 0)
        for status in ('provider_error', 'timeout', 'invalid', 'not_run'):
            self.assertEqual(result['statuses'][status], 1)

    def test_quality_failure_survives_measurement_gap(self):
        self.healthy()
        self.reviews['reviews'][0]['outcome']['pass'] = False
        self.reviews['reviews'][1]['observed_method'] = {'loaded': None, 'reason': 'Trace insufficient.', 'evidence': []}
        code, result = self.score()
        self.assertEqual((code, result['verdict'], result['quality']), (2, 'FAIL_WITH_GAPS', 'FAIL'), result)
        self.assertEqual(result['dimensions']['outcome']['failed'], 1)
        self.assertTrue(result['failures'])

    def test_strict_booleans_and_line_numbers_reject_coercion(self):
        self.healthy()
        original = copy.deepcopy(self.reviews)
        for value in ('false', 1, 0, [], {}):
            self.reviews = copy.deepcopy(original)
            self.reviews['reviews'][0]['outcome']['pass'] = value
            self.assert_invalid()
        self.reviews = copy.deepcopy(original)
        self.reviews['reviews'][0]['outcome']['evidence'][0]['line_start'] = True
        self.assert_invalid()

    def test_ungrounded_positive_or_wrong_quote_is_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.reviews)
        for evidence in ([], [dict(self.ref(), quote='Invented observation')], [dict(self.ref(), line_end=99)]):
            self.reviews = copy.deepcopy(original)
            self.reviews['reviews'][0]['outcome']['evidence'] = evidence
            self.assert_invalid()

    def test_raw_artifact_tampering_is_invalid(self):
        self.healthy()
        (self.base / 'answer-0.txt').write_text('Different answer.\n')
        self.assert_invalid()

    def test_replaced_artifact_hash_does_not_reuse_old_review(self):
        self.healthy()
        self.trials['trials'][0]['artifacts'][0] = self.artifact('answer-new.txt', 'Read-back value is correct.\nChanged.\n')
        self.assert_invalid()

    def test_wrong_input_arm_and_manifest_binding_is_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.trials)
        for key, value in (('input_sha256', '0' * 64), ('arm_id', 'other'), ('case_id', 'other')):
            self.trials = copy.deepcopy(original)
            self.trials['trials'][0][key] = value
            self.rebind()
            self.assert_invalid()
        self.trials = copy.deepcopy(original)
        self.trials['manifest_sha256'] = '0' * 64
        self.assert_invalid()

    def test_path_traversal_absolute_paths_and_symlinks_are_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.trials)
        for path in ('../answer-0.txt', str(self.base / 'answer-0.txt'), 'nested/../../answer-0.txt', 'a\\b', 'a//b'):
            self.trials = copy.deepcopy(original)
            self.trials['trials'][0]['artifacts'][0]['path'] = path
            self.rebind()
            self.assert_invalid()
        try:
            (self.base / 'link.txt').symlink_to(self.base / 'answer-0.txt')
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symlink privilege')
            raise
        self.trials = copy.deepcopy(original)
        self.trials['trials'][0]['artifacts'][0]['path'] = 'link.txt'
        self.rebind()
        self.assert_invalid()

    def test_frozen_packet_and_rubric_tampering_is_invalid(self):
        self.healthy()
        for descriptor in (self.manifest['cases'][0]['packet'], self.manifest['source']):
            path = self.manifest_path.parent / descriptor['path']
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            self.assert_invalid()
            path.write_bytes(original)

    def test_duplicate_json_keys_are_rejected_by_cli(self):
        self.healthy()
        path = self.write('trials.json', self.trials)
        path.write_text(path.read_text().replace('"version": 1', '"version": 1, "version": 1'))
        code, result = self.run_cli('score', self.manifest_path, '--trials', path,
                                   '--reviews', self.write('reviews.json', self.reviews), '--artifact-root', self.base)
        self.assertEqual((code, result['verdict']), (3, 'INVALID'), result)

    def test_self_review_cannot_claim_independence(self):
        self.healthy()
        self.reviews['reviews'][0]['reviewer_id'] = self.trials['trials'][0]['performer_id']
        self.assert_invalid()

    def test_failed_trial_cannot_be_reviewed_as_quality_pass(self):
        self.healthy()
        self.trials['trials'][0]['status'] = 'provider_error'
        self.rebind()
        self.assert_invalid()


    def test_manifest_plan_types_and_coverage_cannot_be_changed(self):
        self.healthy()
        original = copy.deepcopy(self.manifest)
        for mutation in ('boolean_repeat', 'omit_trial'):
            self.manifest = copy.deepcopy(original)
            if mutation == 'boolean_repeat':
                self.manifest['planned_trials'][0]['repeat'] = True
            else:
                self.manifest['planned_trials'].pop()
            self.manifest_path.write_text(json.dumps(self.manifest))
            self.trials['manifest_sha256'] = self.reviews['manifest_sha256'] = digest(self.manifest)
            self.assert_invalid()

    def test_empty_raw_record_and_duplicate_artifact_kind_are_invalid(self):
        self.healthy()
        original = copy.deepcopy(self.trials)
        self.trials['trials'][0]['artifacts'][0] = self.artifact('answer-empty.txt', '')
        self.rebind()
        self.assert_invalid()
        self.trials = copy.deepcopy(original)
        self.trials['trials'][0]['artifacts'].append(self.trials['trials'][0]['artifacts'][0])
        self.rebind()
        self.assert_invalid()

    def test_unknown_judgment_is_not_false_or_success(self):
        self.healthy()
        self.reviews['reviews'][0]['adherence'] = {'pass': None, 'reason': 'Cannot establish compliance.', 'evidence': []}
        code, result = self.score()
        self.assertEqual((code, result['verdict'], result['quality']), (2, 'INCOMPLETE', 'INCOMPLETE'), result)
        self.assertEqual(result['dimensions']['adherence'], {'passed': 1, 'failed': 0, 'unknown': 1})


    def test_case_ids_differing_only_by_case_have_distinct_valid_packets(self):
        first = copy.deepcopy(self.cases['cases'][0])
        second = copy.deepcopy(first)
        first['id'], second['id'] = 'Case', 'case'
        second['prompt'] = 'A different independent task.'
        self.cases['cases'] = [first, second]
        self.write('cases.json', self.cases)
        self.prepare()
        paths = [case['packet']['path'] for case in self.manifest['cases']]
        self.assertEqual(len({path.casefold() for path in paths}), 2)
        for case, expected in zip(self.manifest['cases'], (first, second)):
            raw = (self.manifest_path.parent / case['packet']['path']).read_bytes()
            self.assertEqual(json.loads(raw), {'id': expected['id'], 'prompt': expected['prompt']})
            self.assertEqual(hashlib.sha256(raw).hexdigest(), case['packet']['sha256'])
        self.assertEqual(len(behavioral_eval.manifest_data(self.manifest_path)['planned_trials']), 4)

    def test_artifact_healthy_single_read_returns_hash_checked_bytes(self):
        desc = self.artifact('answer-original.txt', 'Original healthy record.\n')
        self.assertEqual(behavioral_eval.artifact(self.base, desc, True), b'Original healthy record.\n')

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'Requires POSIX no-follow support')
    def test_artifact_does_not_reopen_path_after_safe_handle_was_opened(self):
        for anchored in (False, True):
            with self.subTest(anchored=anchored):
                desc = self.artifact(f'answer-race-{anchored}.txt', 'Original healthy record.\n')
                target = self.base / desc['path']
                replacement = self.base / f'same-bytes-{anchored}.txt'
                replacement.write_bytes(target.read_bytes())
                real_open, real_io_open = os.open, io.open
                swapped = False
                unsafe_reopens = []

                def open_then_swap(path, flags, *args, **kwargs):
                    nonlocal swapped
                    fd = real_open(path, flags, *args, **kwargs)
                    if str(path) in (str(target), target.name) and not swapped:
                        target.rename(self.base / f'original-open-inode-{anchored}.txt')
                        target.symlink_to(replacement)
                        swapped = True
                    return fd

                def observe_reopen(path, *args, **kwargs):
                    if not isinstance(path, int) and Path(path) == target and target.is_symlink():
                        unsafe_reopens.append(str(path))
                    return real_io_open(path, *args, **kwargs)

                # Real rename+symlink race at the OS boundary, in both reader paths.
                with mock.patch.object(os, 'open', side_effect=open_then_swap) as patched_open, \
                     mock.patch.object(io, 'open', side_effect=observe_reopen), \
                     mock.patch.object(os, 'supports_dir_fd', {patched_open} if anchored else set()):
                    try:
                        observed = behavioral_eval.artifact(self.base, desc, True)
                    except (OSError, ValueError):
                        observed = None  # Safe race rejection is also allowed.
                self.assertTrue(swapped, 'The filesystem race must actually execute.')
                self.assertEqual(unsafe_reopens, [], 'Validated path was reopened after replacement.')
                if observed is not None:
                    self.assertEqual(observed, b'Original healthy record.\n')

    @unittest.skipUnless(hasattr(os, 'mkfifo') and hasattr(os, 'O_NONBLOCK'), 'Requires POSIX FIFO support')
    def test_file_replaced_by_fifo_before_open_never_blocks(self):
        desc = self.artifact('answer-fifo.txt', 'Original healthy record.\n')
        target = self.base / desc['path']
        real_open = os.open
        swapped = False

        def replace_before_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if str(path) in (str(target), target.name) and not swapped:
                target.unlink()
                os.mkfifo(target)
                swapped = True
                self.assertTrue(flags & os.O_NONBLOCK, 'FIFO race must use a nonblocking open.')
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(os, 'open', side_effect=replace_before_open):
            with self.assertRaises((ValueError, OSError)):
                behavioral_eval.artifact(self.base, desc, True)
        self.assertTrue(swapped)

    def test_failed_source_write_does_not_reserve_output_and_retry_succeeds(self):
        out = self.base / 'failed-prepare'
        real_open = Path.open

        def fail_source(path, *args, **kwargs):
            if path.name == 'source.json' and any(flag in (args[0] if args else kwargs.get('mode', 'r')) for flag in 'wx'):
                raise OSError('injected source write fault')
            return real_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', fail_source):
            with self.assertRaises(OSError):
                behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
        self.assertFalse(out.exists(), 'A failed preparation must not block a clean retry.')
        result = behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
        self.assertEqual(result['planned'], 2)
        self.assertEqual(len(behavioral_eval.manifest_data(out / 'manifest.json')['planned_trials']), 2)

    def test_prepare_failure_preserves_concurrent_user_file(self):
        out = self.base / 'failed-with-user-data'
        real_open = Path.open
        user_files = []

        def fail_with_concurrent_file(path, *args, **kwargs):
            if path.name == 'source.json' and any(flag in (args[0] if args else kwargs.get('mode', 'r')) for flag in 'wx'):
                user_path = path.parent / 'user-added.txt'
                user_path.write_text('Do not delete my data.')
                user_files.append(user_path)
                raise OSError('injected source write fault with unrelated addition')
            return real_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', fail_with_concurrent_file):
            with self.assertRaises(OSError):
                behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
        self.assertEqual(len(user_files), 1)
        self.assertEqual(user_files[0].read_text(), 'Do not delete my data.')
        self.assertFalse(out.exists(), 'Unrelated staging files may remain, but final output must be absent.')


    def test_partial_write_stays_outside_final_output_and_retry_succeeds(self):
        out = self.base / 'partial-prepare'
        real_open = Path.open
        leftovers = []

        def partial_then_fail(path, *args, **kwargs):
            if path.name == 'source.json' and any(flag in (args[0] if args else kwargs.get('mode', 'r')) for flag in 'wx'):
                with real_open(path, 'xb') as stream:
                    stream.write(b'partial bytes')
                leftovers.append(path)
                raise OSError('injected fault after partial write')
            return real_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', partial_then_fail):
            with self.assertRaises(OSError):
                behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
        self.assertFalse(out.exists())
        self.assertEqual(leftovers[0].read_bytes(), b'partial bytes')
        self.assertEqual(behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)['planned'], 2)

    def test_failure_cleanup_preserves_concurrently_modified_packet(self):
        out = self.base / 'modified-prepare'
        real_open = Path.open
        changed = []

        def change_packet_then_fail(path, *args, **kwargs):
            if path.name == 'source.json' and any(flag in (args[0] if args else kwargs.get('mode', 'r')) for flag in 'wx'):
                packet = next((path.parent / 'packets').iterdir())
                packet.write_text('User replacement content.')
                changed.append(packet)
                raise OSError('injected source failure after user edit')
            return real_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', change_packet_then_fail):
            with self.assertRaises(OSError):
                behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
        self.assertEqual(changed[0].read_text(), 'User replacement content.')
        self.assertFalse(out.exists())

    def test_publish_failure_rolls_back_owned_output_but_preserves_user_addition(self):
        for user_addition in (False, True):
            with self.subTest(user_addition=user_addition):
                out = self.base / f'publish-failure-{user_addition}'
                real_link = os.link

                def fail_publication(src, dst, *args, **kwargs):
                    if Path(dst).name == 'source.json':
                        if user_addition:
                            (out / 'user.txt').write_text('Concurrent file.')
                        raise OSError('injected publication failure')
                    return real_link(src, dst, *args, **kwargs)

                with mock.patch.object(os, 'link', fail_publication):
                    with self.assertRaises(OSError):
                        behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)
                if user_addition:
                    self.assertEqual((out / 'user.txt').read_text(), 'Concurrent file.')
                else:
                    self.assertFalse(out.exists())
                    self.assertEqual(behavioral_eval.prepare(self.base / 'cases.json', self.base / 'arms.json', out, 1)['planned'], 2)

    def test_empty_or_malformed_case_sets_fail_closed(self):
        for value in ({'version': 1, 'cases': []}, {'version': True, 'cases': self.cases['cases']},
                      {'version': 1, 'cases': self.cases['cases'] * 2}):
            self.write('cases.json', value)
            code, result = self.run_cli('prepare', self.base / 'cases.json', '--arms', self.base / 'arms.json',
                                       '--out', self.base / 'experiment')
            self.assertEqual((code, result['verdict']), (3, 'INVALID'), result)


if __name__ == '__main__':
    unittest.main()
