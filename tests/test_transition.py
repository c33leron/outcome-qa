import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_transition as checker


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.before={'record':{'id':'item-1','text':'old','budget':100},'items':[1]}
        self.after=copy.deepcopy(self.before);self.after['record']['text']='new'
        self.contract={'version':1,'goal':'Change only text','identity':[{'path':'/record/id','value':'item-1'}],
                       'rules':[{'id':'value','op':'equals','path':'/record/text','value':'new'},
                                {'id':'preserve','op':'only_changes','paths':['/record/text']}]}

    def check(self):return checker.check(self.before,self.after,self.contract)

    def test_healthy_update_passes_without_mutation(self):
        original=copy.deepcopy((self.before,self.after,self.contract))
        self.assertEqual('PASS',self.check()['verdict'])
        self.assertEqual(original,(self.before,self.after,self.contract))

    def test_unrequested_change_fails_even_when_requested_value_correct(self):
        self.after['record']['budget']=0
        result=self.check();self.assertEqual(['preserve'],result['violations']);self.assertEqual(1,result['exit_code'])

    def test_wrong_object_does_not_become_product_failure_or_pass(self):
        self.after['record']['id']='other'
        result=self.check();self.assertEqual('INCOMPLETE',result['verdict']);self.assertEqual([],result['rules'])

    def test_missing_rule_data_is_gap(self):
        self.contract['rules'][0]['path']='/missing'
        self.assertEqual('INCOMPLETE',self.check()['verdict'])

    def test_known_failure_survives_missing_other_data(self):
        self.after['record']['text']='wrong';self.contract['rules'][1]['paths']=['/missing']
        result=self.check();self.assertEqual('FAIL_WITH_GAPS',result['verdict']);self.assertEqual(['value'],result['violations'])

    def test_bool_is_not_number(self):
        self.contract['rules']=[{'id':'x','op':'equals','path':'/record/budget','value':True}]
        self.after['record']['budget']=1
        self.assertEqual('FAIL',self.check()['verdict'])

    def test_unchanged_and_length_delta(self):
        self.contract['rules']=[{'id':'stable','op':'unchanged','path':'/record/budget'},
                               {'id':'one','op':'length_delta','path':'/items','delta':1}]
        self.after['items'].append(2);self.assertEqual('PASS',self.check()['verdict'])
        self.after['items'].append(3);self.assertEqual(['one'],self.check()['violations'])

    def test_empty_or_malformed_contract_cannot_pass(self):
        for key,value in [('rules',[]),('identity',[]),('version',True),('version',1.0),('goal','')]:
            c=copy.deepcopy(self.contract);c[key]=value
            self.assertEqual('INVALID',checker.check(self.before,self.after,c)['verdict'])

    def test_unknown_fields_and_duplicate_ids_invalid(self):
        self.contract['rules'][0]['ignored']=True;self.assertEqual('INVALID',self.check()['verdict'])
        del self.contract['rules'][0]['ignored'];self.contract['rules'].append(self.contract['rules'][0])
        self.assertEqual('INVALID',self.check()['verdict'])

    def test_pointer_escapes_and_prefix_boundary(self):
        self.before['a/b']={'~name':1};self.after['a/b']={'~name':2}
        self.contract['rules']=[{'id':'escaped','op':'equals','path':'/a~1b/~0name','value':2}]
        self.assertEqual('PASS',self.check()['verdict'])
        self.contract['rules']=[{'id':'boundary','op':'only_changes','paths':['/record/text']}]
        self.after['record']['textExtra']='not allowed'
        self.assertEqual('FAIL',self.check()['verdict'])

    def test_adding_or_removing_field_is_change(self):
        for mutation in ('add','delete'):
            self.after=copy.deepcopy(self.before);self.after['record']['text']='new'
            if mutation=='add':self.after['unexpected']=None
            else:del self.after['record']['budget']
            self.assertEqual('FAIL',self.check()['verdict'])

    def test_no_change_allowed_for_denial_preservation_rule(self):
        self.after=copy.deepcopy(self.before)
        self.contract['rules']=[{'id':'no-write','op':'unchanged','path':'/record'}]
        self.assertEqual('PASS',self.check()['verdict'])

    def test_unknown_path_and_bad_escape_are_not_vacuous_pass(self):
        self.contract['rules']=[{'id':'x','op':'only_changes','paths':['/unknown']}]
        self.assertEqual('INCOMPLETE',self.check()['verdict'])
        self.contract['rules'][0]['paths']=['/bad~2']
        self.assertEqual('INVALID',self.check()['verdict'])

    def test_cli_strict_json_and_no_raw_state_values(self):
        script=Path(checker.__file__)
        with tempfile.TemporaryDirectory() as t:
            paths=[Path(t)/x for x in ('before.json','after.json','contract.json')]
            self.before['sensitive']='PRIVATE-CANARY';self.after['sensitive']='PRIVATE-CANARY'
            for p,d in zip(paths,[self.before,self.after,self.contract]):p.write_text(json.dumps(d))
            command=[sys.executable,str(script),'check','--before',str(paths[0]),'--after',str(paths[1]),'--contract',str(paths[2]),'--format','json']
            r=subprocess.run(command,capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stdout)
            self.assertNotIn('PRIVATE-CANARY',r.stdout)
            paths[0].write_text('{"x":1,"x":2}')
            r=subprocess.run(command,capture_output=True,text=True);self.assertEqual(3,r.returncode)
