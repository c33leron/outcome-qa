import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import demo_cases
from check_transition import check


class DemoReplayTests(unittest.TestCase):
    def test_every_fixture_reaches_its_declared_distinction(self):
        fixtures = demo_cases.cases()
        original = copy.deepcopy(fixtures)
        self.assertEqual(10, len(fixtures))
        self.assertEqual(10, len({x['id'] for x in fixtures}))
        for item in fixtures:
            with self.subTest(case=item['id']):
                self.assertEqual('PASS', check(item['before'],item['healthy'],item['contract'])['verdict'])
                self.assertEqual(item['expected_faulty'], check(item['before'],item['faulty'],item['contract'])['verdict'])
        self.assertEqual(original, fixtures)

    def test_cli_reports_fixture_scope_not_agent_accuracy(self):
        result = subprocess.run([sys.executable,'-B',str(ROOT/'scripts/demo_cases.py')],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual((10,10),(data['matched'],data['total']))
        self.assertIn('not ten applications',data['limit'])

    def test_bad_contract_is_not_a_detected_product_bug(self):
        case=demo_cases.cases()[0]
        case['contract']['rules']=[]
        self.assertEqual('INVALID',check(case['before'],case['faulty'],case['contract'])['verdict'])
