"""Structural authoring budgets; these are not model-quality assertions."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_package import SKILLS, frontmatter
from sync_shared import check


class PromptContracts(unittest.TestCase):
    def test_entrypoint_budget_examples_and_discovery(self):
        for name in sorted(SKILLS):
            with self.subTest(skill=name):
                path=ROOT/'skills'/name/'SKILL.md'
                header,body=frontmatter(path)
                self.assertLessEqual(len(body.split()),450)
                self.assertGreater(len(body.split()),150)
                self.assertLessEqual(len(header['description']),400)
                self.assertIn('example',body.lower())
                self.assertIn('references/_shared/trust-boundary.md',body)
                self.assertIn('references/_shared/voice.md',body)

    def test_canonical_materialization_is_current(self):
        self.assertEqual([],check(ROOT))

    def test_startup_reference_is_reachable_in_every_standalone_skill_and_runtime(self):
        """Delivery contract only: model compliance needs separate native traces."""
        shared=json.loads((ROOT/'shared-references.json').read_text())['files']
        runtime=json.loads((ROOT/'runtime-files.json').read_text())['files']
        for name in sorted(SKILLS):
            with self.subTest(skill=name):
                relative=f'skills/{name}/references/_shared/skill-start.md'
                entry=(ROOT/'skills'/name/'SKILL.md').read_text(encoding='utf-8')
                self.assertIn('references/_shared/skill-start.md',entry)
                self.assertEqual('shared/skill-start.md',shared.get(relative))
                self.assertEqual(relative,runtime.get(relative))
                self.assertTrue((ROOT/relative).is_file())

    def test_commands_explicit_and_hook_opt_in(self):
        for name in ('qa','qa-retest','qa-report'):
            text=(ROOT/'commands'/(name+'.md')).read_text(encoding='utf-8')
            self.assertIn('disable-model-invocation: true',text)
            self.assertIn('$ARGUMENTS',text)
        self.assertFalse((ROOT/'hooks/hooks.json').exists())
        self.assertNotIn('hooks',json.loads((ROOT/'.claude-plugin/plugin.json').read_text(encoding='utf-8')))

    def test_adaptive_and_incident_depth_ship_with_each_standalone_method(self):
        """Reference closure, not evidence that a model follows the guidance."""
        shared = json.loads((ROOT / 'shared-references.json').read_text(encoding='utf-8'))['files']
        runtime = json.loads((ROOT / 'runtime-files.json').read_text(encoding='utf-8'))['files']
        for skill in sorted(SKILLS):
            for name in ('decision-loop.md', 'incident-tracing.md'):
                with self.subTest(skill=skill, reference=name):
                    relative = f'skills/{skill}/references/_shared/{name}'
                    self.assertEqual(f'shared/{name}', shared.get(relative))
                    self.assertEqual(relative, runtime.get(relative))
                    self.assertTrue((ROOT / relative).is_file())
        startup = (ROOT / 'shared/skill-start.md').read_text(encoding='utf-8')
        self.assertIn('(decision-loop.md)', startup)
        decision = (ROOT / 'shared/decision-loop.md').read_text(encoding='utf-8')
        self.assertIn('(incident-tracing.md)', decision)

    def test_runtime_omits_canon_sync_tests_and_labs(self):
        mapping=json.loads((ROOT/'runtime-files.json').read_text(encoding='utf-8'))['files']
        for path in mapping:
            self.assertFalse(path.startswith(('shared/','tests/','evals/')))
            self.assertNotIn(path,('scripts/sync_shared.py','scripts/demo_cases.py'))
