#!/usr/bin/env python3
"""Check a bounded before/after state contract; never executes product actions."""
import argparse
import json
from pathlib import Path
from strict_json import load, identifier, terminal

ASSURANCE = ('Checks only supplied JSON snapshots, identity guards and declared constraints. '
             'Does not verify snapshot origin, completeness, product execution or AI meaning.')


def tokens(path):
    if not isinstance(path, str) or not path.startswith('/'):
        raise ValueError('Expected a nonempty RFC6901 JSON pointer')
    import re
    if re.search(r'~(?![01])', path):
        raise ValueError('Invalid JSON pointer escape')
    return [part.replace('~1', '/').replace('~0', '~') for part in path[1:].split('/')]


class MissingData(Exception):
    pass


def at(data, path):
    value = data
    for key in tokens(path):
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isascii() and key.isdecimal() and (key == '0' or not key.startswith('0')):
            index = int(key)
            if index >= len(value): raise MissingData()
            value = value[index]
        else:
            raise MissingData()
    return value


def equal(a, b):
    # JSON numbers share a value domain; booleans must never equal numbers.
    if type(a) in (int, float) and type(b) in (int, float):
        return a == b
    if type(a) is not type(b): return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def differences(a, b, path=''):
    if equal(a, b): return []
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            sub = path + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in a or key not in b: result.append(sub)
            else: result.extend(differences(a[key], b[key], sub))
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        result = []
        for i, (x, y) in enumerate(zip(a, b)):
            result.extend(differences(x, y, path + '/' + str(i)))
        return result
    return [path]


def shape(obj, required):
    if not isinstance(obj, dict) or set(obj) != set(required):
        raise ValueError('Unexpected or missing contract fields')


def validate_contract(c):
    shape(c, ('version', 'goal', 'identity', 'rules'))
    if type(c['version']) is not int or c['version'] != 1:
        raise ValueError('Expected contract version integer 1')
    if not isinstance(c['goal'], str) or not c['goal'].strip():
        raise ValueError('Expected nonblank goal')
    if not isinstance(c['identity'], list) or not c['identity']:
        raise ValueError('At least one explicit identity guard is required')
    paths = set()
    for guard in c['identity']:
        shape(guard, ('path', 'value'));tokens(guard['path'])
        if guard['path'] in paths: raise ValueError('Duplicate identity guard')
        paths.add(guard['path'])
    if not isinstance(c['rules'], list) or not c['rules']:
        raise ValueError('An empty rule set cannot establish PASS')
    ids = set()
    for rule in c['rules']:
        if not isinstance(rule, dict) or not identifier(rule.get('id')):
            raise ValueError('Expected control-free unique rule ID')
        if rule['id'] in ids: raise ValueError('Duplicate rule ID')
        ids.add(rule['id'])
        op = rule.get('op')
        fields = {'equals': ('id','op','path','value'), 'unchanged': ('id','op','path'),
                  'length_delta': ('id','op','path','delta'), 'only_changes': ('id','op','paths')}
        if not isinstance(op, str) or op not in fields: raise ValueError('Unknown transition operation')
        shape(rule, fields[op])
        if op == 'only_changes':
            ps = rule['paths']
            if not isinstance(ps, list) or not ps: raise ValueError('Expected explicit permitted paths')
            for p in ps: tokens(p)
            if len(set(ps)) != len(ps): raise ValueError('Duplicate permitted path')
        else:
            tokens(rule['path'])
        if op == 'length_delta' and type(rule['delta']) is not int:
            raise ValueError('Array length delta must be an integer, not boolean')


def check(before, after, contract):
    rows, gaps, violations, issues = [], [], [], []
    def finish():
        verdict = ('INVALID' if issues else 'FAIL_WITH_GAPS' if violations and gaps else
                   'FAIL' if violations else 'INCOMPLETE' if gaps else 'PASS')
        return {'verdict': verdict, 'exit_code': {'PASS':0,'FAIL':1,'FAIL_WITH_GAPS':2,'INCOMPLETE':2,'INVALID':3}[verdict],
                'rules': rows, 'violations': violations, 'gaps': gaps, 'issues': issues, 'assurance': ASSURANCE}
    try:
        validate_contract(contract)
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise ValueError('Snapshots must be JSON objects with equivalent projections')
    except (ValueError, TypeError, RecursionError) as exc:
        issues.append(str(exc));return finish()
    for guard in contract['identity']:
        for label, snapshot in [('before', before), ('after', after)]:
            try: matches = equal(at(snapshot, guard['path']), guard['value'])
            except MissingData: matches = False
            if not matches: gaps.append(label + ': identity not established at ' + guard['path'])
    if gaps: return finish()  # Do not score product changes on the wrong object.
    for rule in contract['rules']:
        rid, op = rule['id'], rule['op']
        try:
            if op == 'equals':
                passed = equal(at(after, rule['path']), rule['value'])
            elif op == 'unchanged':
                passed = equal(at(before, rule['path']), at(after, rule['path']))
            elif op == 'length_delta':
                old, new = at(before, rule['path']), at(after, rule['path'])
                if not isinstance(old, list) or not isinstance(new, list): raise MissingData()
                passed = len(new) - len(old) == rule['delta']
            else:
                # Require allowed paths to exist in at least one snapshot; typos are gaps.
                for path in rule['paths']:
                    try: at(before, path)
                    except MissingData: at(after, path)
                passed = all(any(p == allowed or p.startswith(allowed + '/') for allowed in rule['paths'])
                             for p in differences(before, after))
            rows.append({'id': rid, 'status': 'PASS' if passed else 'FAIL'})
            if not passed: violations.append(rid)
        except MissingData:
            rows.append({'id': rid, 'status': 'INCOMPLETE'})
            gaps.append(rid + ': required data missing or incompatible; verify snapshot projection/path')
    return finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('check')
    for name in ('before', 'after', 'contract'): p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--format', choices=('json','text'), default='text')
    args = parser.parse_args()
    try:
        result = check(load(args.before), load(args.after), load(args.contract))
    except (OSError, ValueError, TypeError, RecursionError, UnicodeError):
        result = {'verdict':'INVALID','exit_code':3,'rules':[],'violations':[],'gaps':[],
                  'issues':['Could not read strict JSON inputs or evaluate nesting safely'], 'assurance':ASSURANCE}
    if args.format == 'json': print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(result['verdict'])
        for category in ('rules','violations','gaps','issues'):
            for item in result[category]: print(category + ': ' + terminal(item))
        print(ASSURANCE)
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
