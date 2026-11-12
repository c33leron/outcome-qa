#!/usr/bin/env python3
"""Prepare label-free discovery prompts or score saved semantic-routing responses."""
import argparse
import json
from pathlib import Path
from validate_package import ROOT, SKILLS, frontmatter
from strict_json import load as read_json


def unique(items, label):
    if not isinstance(items, list) or not items:
        raise ValueError(f'{label}: expected a nonempty list')
    mapping = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'].strip():
            raise ValueError(f'{label}: each item needs a nonblank id')
        if item['id'] in mapping:
            raise ValueError(f'{label}: duplicate id')
        mapping[item['id']] = item
    return mapping


def cases(path):
    data = read_json(path)
    if not isinstance(data, dict) or data.get('version') != 1 or type(data.get('version')) is not int:
        raise ValueError('Expected version 1 case object')
    result = unique(data.get('cases'), 'cases')
    for item in result.values():
        if not isinstance(item.get('prompt'), str) or not item['prompt'].strip():
            raise ValueError('Case prompt must be nonblank')
        if 'expected_primary' not in item or not valid_label(item['expected_primary']):
            raise ValueError('Invalid expected skill')
    return result


def valid_label(value):
    return value is None or (isinstance(value, str) and value in SKILLS)


def score(truth, predictions):
    index = unique(predictions, 'predictions')
    if set(index) != set(truth):
        raise ValueError('Prediction IDs must exactly match all case IDs, including negative cases')
    for item in index.values():
        if 'primary' not in item or not valid_label(item['primary']):
            raise ValueError('Each prediction needs a valid primary string or explicit null')
    mismatches = [{'id': k, 'expected': c['expected_primary'], 'actual': index[k]['primary']}
                  for k, c in truth.items() if c['expected_primary'] != index[k]['primary']]
    return {'kind': 'semantic_routing_only', 'total': len(truth),
            'matched': len(truth) - len(mismatches), 'mismatches': mismatches,
            'limit': 'Correct labels do not prove host discovery or product-testing effectiveness.'}


def prepare(truth):
    catalog = [frontmatter(ROOT / 'skills' / n / 'SKILL.md')[0] for n in sorted(SKILLS)]
    return {'instructions': 'Choose one primary skill, or null when none applies. Return [{id,primary,reason}]. Do not execute the tasks.',
            'catalog': catalog,
            'cases': [{'id': k, 'prompt': c['prompt']} for k, c in truth.items()]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    pre = sub.add_parser('prepare')
    pre.add_argument('cases')
    sc = sub.add_parser('score')
    sc.add_argument('cases')
    sc.add_argument('predictions')
    a = p.parse_args()
    try:
        truth = cases(a.cases)
        if a.command == 'prepare':
            result = prepare(truth)
        else:
            result = score(truth, read_json(a.predictions))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result.get('mismatches')))
    except (OSError, ValueError, TypeError) as e:
        print(json.dumps({'error': str(e)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
