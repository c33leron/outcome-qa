#!/usr/bin/env python3
"""Check this package's authored manifest/skill subset; not host behavior or QA quality."""
import json
import re
import sys
from pathlib import Path
from strict_json import load as load_json, loads as loads_json
from sync_shared import check as check_shared

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {'oq-explore', 'oq-automation', 'oq-ai-quality', 'oq-checker-audit', 'oq-retest', 'oq-security-journeys', 'oq-test-design'}


def frontmatter(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError(f'{path.name}: missing YAML frontmatter')
    head, body = text[4:].split('\n---\n', 1)
    fields = {}
    for line in head.splitlines():
        if not line or line.startswith(' ') or line.startswith('#'):
            continue
        key, _, value = line.partition(':')
        if key in ('name', 'description'):
            if key in fields:
                raise ValueError('Duplicate frontmatter key')
            fields[key] = loads_json(value.strip())
    for key in ('name', 'description'):
        if not isinstance(fields.get(key), str) or not fields[key].strip():
            raise ValueError(f'Missing/invalid {key}: {path}')
    return fields, body


def validate(root=ROOT):
    errors = list(check_shared(root))
    def require(ok, msg):
        if not ok:
            errors.append(msg)
    try:
        manifest = load_json(root / 'plugin.json')
        require(manifest.get('$schema') == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', 'Wrong portable schema')
        require(manifest.get('name') == 'outcome-qa', 'Wrong package identity')
        require(bool(re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', manifest.get('version', ''))), 'Invalid version')
        presentation = manifest['extensions']['com.openai']['interface']
        require(0 < len(presentation['shortDescription']) <= 30, 'Subtitle exceeds 30 characters')
        require(presentation['category'] == 'Developer Tools', 'Category mismatch')
        require(isinstance(presentation['capabilities'], list), 'Capabilities must be a list')
        require(not any(k in manifest for k in ('skills', 'mcpServers', 'interface', 'apps')), 'Legacy fields in portable root')
        for overlay in ('.claude-plugin/plugin.json', '.codex-plugin/plugin.json'):
            data = load_json(root / overlay)
            for field in ('name', 'version', 'author'):
                require(data.get(field) == manifest[field], f'{overlay}: {field} drift')
        codex = load_json(root / '.codex-plugin/plugin.json')
        require(codex['interface'] == presentation, 'Codex presentation drift')
        require(codex['skills'] == './skills/', 'Wrong skill directory')
        found = {p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
        require(found == SKILLS, f'Expected seven skills, found {sorted(found)}')
        for name in sorted(found):
            entry = root / 'skills' / name / 'SKILL.md'
            fields, body = frontmatter(entry)
            require(fields['name'] == name, f'Name/directory mismatch: {name}')
            require(len(fields['description']) <= 1024, f'Oversized description: {name}')
            require(bool(body.strip()), f'Empty skill: {name}')
            meta = (entry.parent / 'agents/openai.yaml').read_text(encoding='utf-8')
            require(bool(re.search(r'^  allow_implicit_invocation: true$', meta, re.M)), f'Implicit discovery disabled: {name}')
            require('disable-model-invocation: true' not in entry.read_text(encoding='utf-8'), f'Claude implicit discovery disabled: {name}')
        for required in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt', 'README.md', 'docs/EVALUATION.md'):
            require((root / required).is_file(), f'Missing deliverable: {required}')
        for path in root.rglob('*'):
            if '.git' in path.parts or '__pycache__' in path.parts:
                continue
            require(not path.is_symlink(), f'Forbidden symlink: {path.relative_to(root)}')
            if not path.is_file() or path.suffix != '.md':
                continue
            text = path.read_text(encoding='utf-8')
            require(not re.search(r'/(?:Users|home)/[^/\s]+/', text), f'Personal absolute path: {path.relative_to(root)}')
            for dest in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in dest or dest.startswith('#'):
                    continue
                target = (path.parent / dest.split('#')[0]).resolve()
                require(target.is_relative_to(root.resolve()) and target.exists(), f'Broken/outside link: {path.relative_to(root)} -> {dest}')
    except (ValueError, KeyError, OSError, TypeError) as exc:
        errors.append(str(exc))
    return errors


if __name__ == '__main__':
    problems = validate()
    print(json.dumps({'valid': not problems, 'errors': problems,
                      'limit': 'Static package checks, not native host loading or QA effectiveness.'}, indent=2))
    raise SystemExit(bool(problems))
