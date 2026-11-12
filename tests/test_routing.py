import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import score_routing as routing


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.truth = {'one': {'prompt': 'test feature', 'expected_primary': 'oq-explore'},
                      'negative': {'prompt': 'translate text', 'expected_primary': None}}
        self.pred = [{'id': 'one', 'primary': 'oq-explore'}, {'id': 'negative', 'primary': None}]

    def test_all_correct(self):
        self.assertEqual(2, routing.score(self.truth, self.pred)['matched'])

    def test_wrong_is_not_correct(self):
        self.pred[0]['primary'] = 'oq-retest'
        self.assertEqual(1, routing.score(self.truth, self.pred)['matched'])

    def test_missing_negative_case_cannot_get_credit(self):
        with self.assertRaises(ValueError):
            routing.score(self.truth, self.pred[:1])

    def test_missing_null_is_not_explicit_none(self):
        del self.pred[1]['primary']
        with self.assertRaises(ValueError):
            routing.score(self.truth, self.pred)

    def test_duplicate_and_extra_ids_invalid(self):
        for extra in ({'id': 'one', 'primary': None}, {'id': 'extra', 'primary': None}):
            with self.assertRaises(ValueError):
                routing.score(self.truth, self.pred + [extra])

    def test_invalid_types_and_labels(self):
        for value in (False, 0, [], {}, 'unknown'):
            self.pred[0]['primary'] = value
            with self.assertRaises(ValueError):
                routing.score(self.truth, self.pred)

    def test_prepared_input_does_not_leak_answer_keys(self):
        prepared = routing.prepare(self.truth)
        self.assertEqual(7, len(prepared['catalog']))
        for item in prepared['cases']:
            self.assertEqual({'id', 'prompt'}, set(item))

    def test_real_case_set_complete(self):
        self.assertEqual(44, len(routing.cases(ROOT / 'evals/routing-cases.json')))

    def test_operational_catalogs_match_declared_skills(self):
        import export_playbook
        import install_skills
        expected = {'oq-explore', 'oq-test-design', 'oq-automation', 'oq-ai-quality',
                    'oq-checker-audit', 'oq-retest', 'oq-security-journeys'}
        self.assertEqual(expected, routing.SKILLS)
        self.assertEqual(expected, export_playbook.SKILLS)
        self.assertEqual(expected, install_skills.SKILLS)

    def test_routing_fixture_covers_every_skill_and_non_qa(self):
        real = routing.cases(ROOT / 'evals/routing-cases.json')
        self.assertEqual(routing.SKILLS | {None}, {x['expected_primary'] for x in real.values()})
        self.assertEqual('oq-test-design', real['R03']['expected_primary'])
        self.assertEqual('oq-ai-quality', real['R09']['expected_primary'])

    def test_cli_duplicate_json_keys_rejected(self):
        good_case = '{"version":1,"cases":[{"id":"x","prompt":"test","expected_primary":"oq-explore"}]}'
        bad_case = '{"version":1,"cases":[{"id":"x","prompt":"test","expected_primary":"oq-retest","expected_primary":"oq-explore"}]}'
        good_pred = '[{"id":"x","primary":"oq-explore"}]'
        bad_pred = '[{"id":"x","primary":null,"primary":"oq-explore"}]'
        for case_text, pred_text in ((bad_case, good_pred), (good_case, bad_pred)):
            with tempfile.TemporaryDirectory() as t:
                c, p = Path(t) / 'cases.json', Path(t) / 'predictions.json'
                c.write_text(case_text)
                p.write_text(pred_text)
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/score_routing.py'),
                                         'score', str(c), str(p)], capture_output=True, text=True)
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn('duplicate JSON object key', result.stdout)

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'invalid.json'
            for constant in ('NaN', 'Infinity', '-Infinity'):
                p.write_text('{"unexpected":' + constant + '}')
                with self.assertRaises(ValueError):
                    routing.read_json(p)
