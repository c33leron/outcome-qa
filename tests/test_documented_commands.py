import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentedCommands(unittest.TestCase):
    def test_readme_example_really_runs(self):
        result = subprocess.run([sys.executable, 'scripts/qa_result.py', 'check',
                                 'examples/results/healthy/run.json', '--format', 'json'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn('PASS', result.stdout)
        json.loads(result.stdout)

    def test_transition_examples_have_distinguishing_outcomes(self):
        for name, code, verdict in [('healthy', 0, 'PASS'), ('corrupted', 1, 'FAIL'),
                                    ('wrong-object', 2, 'INCOMPLETE')]:
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, 'scripts/check_transition.py', 'check',
                    '--before', 'examples/transitions/before.json', '--after', f'examples/transitions/{name}.json',
                    '--contract', 'examples/transitions/contract.json', '--format', 'json'],
                    cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(code, result.returncode, result.stderr + result.stdout)
                self.assertEqual(verdict, json.loads(result.stdout)['verdict'])
