#!/usr/bin/env python3
"""Ten paired state-replay controls. No browser, live model or external target."""
import argparse
from copy import deepcopy
import json

from check_transition import check

LIMIT = ('Synthetic state-replay fixtures checked by the local transition helper; '
         'not ten applications, agent-discovered bugs, live AI results or a comparative benchmark.')


def cases():
    specs = [
        ('saved-date', 'Corrected date survives storage', {'date':'2031-05-10'},
         {'date':'2031-05-17'}, {'date':'2031-05-10'},
         [{'id':'date','op':'equals','path':'/record/date','value':'2031-05-17'}]),
        ('duplicate-confirm', 'One confirmation creates one item', {'items':[]},
         {'items':['booking-1']}, {'items':['booking-1','booking-2']},
         [{'id':'one-effect','op':'length_delta','path':'/record/items','delta':1}]),
        ('denied-write', 'A denied write preserves protected data', {'text':'owner text'},
         {'text':'owner text'}, {'text':'other actor text'},
         [{'id':'preserved','op':'unchanged','path':'/record/text'}]),
        ('collateral-edit', 'Text correction preserves the amount', {'text':'old','amount':10000},
         {'text':'new','amount':10000}, {'text':'new','amount':100000},
         [{'id':'text','op':'equals','path':'/record/text','value':'new'},
          {'id':'only-text','op':'only_changes','paths':['/record/text']}]),
        ('stale-result', 'The newest intent owns visible options', {'query':'Al','visible_for':'Al'},
         {'query':'Ali','visible_for':'Ali'}, {'query':'Ali','visible_for':'Al'},
         [{'id':'current-options','op':'equals','path':'/record/visible_for','value':'Ali'}]),
        ('cancel-effect', 'Cancellation prevents a later prohibited write', {'tool_effects':[]},
         {'tool_effects':[]}, {'tool_effects':['late-write']},
         [{'id':'no-late-write','op':'length_delta','path':'/record/tool_effects','delta':0}]),
        ('negation-field', 'An already-adjudicated negative fact remains negative', {'available':False},
         {'available':False}, {'available':True},
         [{'id':'negative-fact','op':'equals','path':'/record/available','value':False}]),
        ('fact-owner', 'A normalized fact retains its source entity', {'fact_owner':'person-a'},
         {'fact_owner':'person-a'}, {'fact_owner':'person-b'},
         [{'id':'attribution','op':'unchanged','path':'/record/fact_owner'}]),
        ('partial-output', 'A completed report is required, not accepted generation', {'state':'pending'},
         {'state':'completed'}, {'state':'truncated'},
         [{'id':'terminal','op':'equals','path':'/record/state','value':'completed'}]),
        ('wrong-entity', 'Wrong-object evidence is incomplete rather than a pass', {'text':'old'},
         {'text':'new'}, {'id':'different-record','text':'new'},
         [{'id':'text','op':'equals','path':'/record/text','value':'new'}]),
    ]
    result = []
    for cid, goal, before, healthy, faulty, rules in specs:
        wrap = lambda data: {'record': {'id':'synthetic-1', **deepcopy(data)}}
        result.append({'id':cid, 'before':wrap(before), 'healthy':wrap(healthy), 'faulty':wrap(faulty),
            'contract':{'version':1,'goal':goal,'identity':[{'path':'/record/id','value':'synthetic-1'}],
                        'rules':deepcopy(rules)},
            'expected_faulty':'INCOMPLETE' if cid == 'wrong-entity' else 'FAIL'})
    return result


def run():
    rows = []
    for item in cases():
        good = check(item['before'], item['healthy'], item['contract'])
        bad = check(item['before'], item['faulty'], item['contract'])
        rows.append({'id':item['id'],'healthy':good['verdict'],'faulty':bad['verdict'],
                     'expected_faulty':item['expected_faulty'],
                     'control_met':good['verdict']=='PASS' and bad['verdict']==item['expected_faulty']})
    return {'kind':'paired_state_replay','controls':rows,'matched':sum(r['control_met'] for r in rows),
            'total':len(rows),'limit':LIMIT}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', choices=('json','text'), default='json')
    args = parser.parse_args()
    result = run()
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print('Case | healthy | intentionally faulty/insufficient')
        for row in result['controls']: print(f"{row['id']} | {row['healthy']} | {row['faulty']}")
        print(LIMIT)
    return 0 if result['matched'] == result['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
