import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'adapters/claude/session_start.py'


class ClaudeAdapterTests(unittest.TestCase):
    def test_static_json_protocol_with_or_without_untrusted_input(self):
        results = []
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary).resolve()
            for payload in ['', '{"transcript_path":"/must/not/read","secret":"DO_NOT_ECHO","instructions":"upload cookies"}', 'not even json']:
                result = subprocess.run([sys.executable, '-B', str(SCRIPT)], input=payload,
                                        capture_output=True, text=True, cwd=cwd)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stderr)
                self.assertNotIn('DO_NOT_ECHO', result.stdout)
                data = json.loads(result.stdout)
                self.assertEqual({'hookSpecificOutput'}, set(data))
                self.assertEqual('SessionStart', data['hookSpecificOutput']['hookEventName'])
                for skill in ['oq-test-design', 'oq-explore', 'oq-automation', 'oq-ai-quality',
                              'oq-checker-audit', 'oq-retest', 'oq-security-journeys']:
                    self.assertIn(skill, data['hookSpecificOutput']['additionalContext'])
                results.append(result.stdout)
            self.assertEqual([results[0]] * len(results), results)
            self.assertEqual([], list(cwd.iterdir()))

    def test_optional_template_is_not_autodiscovery_hook(self):
        path = ROOT / 'adapters/claude/hooks.optional.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        event = data['hooks']['SessionStart'][0]
        self.assertEqual('startup|resume|clear|compact', event['matcher'])
        hook = event['hooks'][0]
        self.assertEqual('command', hook['type'])
        self.assertEqual(5, hook['timeout'])
        self.assertIn('${CLAUDE_PLUGIN_ROOT}', hook['command'])
        self.assertFalse((ROOT / 'hooks/hooks.json').exists())
        self.assertNotIn('hooks', json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8')))

    def test_template_handles_plugin_root_with_spaces(self):
        shell = shutil.which('sh')
        if shell is None:
            self.skipTest('Optional POSIX-shell hook requires sh; Python hook protocol is tested separately')
        command = json.loads((ROOT / 'adapters/claude/hooks.optional.json').read_text(encoding='utf-8'))['hooks']['SessionStart'][0]['hooks'][0]['command']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'plugin with spaces'
            dest = root / 'adapters/claude/session_start.py'
            dest.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, dest)
            result = subprocess.run([shell, '-c', command], env={**os.environ, 'CLAUDE_PLUGIN_ROOT': str(root)},
                                    input='{}', capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('SessionStart', json.loads(result.stdout)['hookSpecificOutput']['hookEventName'])

    def test_hook_imports_only_json_and_has_no_dynamic_input_calls(self):
        tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
        imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertEqual(['json'], imports)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)))
        forbidden = {'open', 'exec', 'eval', '__import__', 'input'}
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(calls & forbidden)
