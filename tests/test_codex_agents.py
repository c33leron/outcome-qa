import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import tomllib
except ModuleNotFoundError:  # Installer remains usable on Python 3.10.
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('agent_installer', ROOT / 'scripts/install_codex_agents.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class CodexAgentTests(unittest.TestCase):
    def symlink(self, link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'new-agents'
            result = installer.install(target)
            self.assertFalse(result['applied'])
            self.assertEqual(list(installer.AGENTS), result['agents'])
            self.assertFalse(target.exists())

    def test_install_has_exact_source_bytes_and_preserves_other_agent(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            other = target / 'existing-agent.toml'
            other.write_text('keep this agent')
            result = installer.install(target, True)
            self.assertTrue(result['applied'])
            for name, payload in installer._sources().items():
                self.assertEqual(payload, (target / (name + '.toml')).read_bytes())
            self.assertEqual('keep this agent', other.read_text(encoding='utf-8'))

    def test_init_only_no_overwrite_or_partial_copy(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            existing = target / 'oq-test-reviewer.toml'
            existing.write_text('user changes')
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                installer.install(target, True)
            self.assertEqual('user changes', existing.read_text(encoding='utf-8'))
            self.assertFalse((target / 'oq-evidence-reviewer.toml').exists())

    def test_target_file_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'not-directory'
            target.write_text('keep')
            with self.assertRaises(ValueError):
                installer.install(target, True)
            link = Path(t) / 'linked-directory'
            self.symlink(link, Path(t), target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(link, True)

    def test_dangling_destination_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            link = target / 'oq-test-reviewer.toml'
            self.symlink(link, target / 'missing')
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                installer.install(target, True)
            self.assertTrue(link.is_symlink())
            self.assertFalse((target / 'oq-evidence-reviewer.toml').exists())

    def test_missing_sources_rejected_before_target_creation(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            with patch.object(installer, 'ROOT', Path(t) / 'empty-source'):
                with self.assertRaisesRegex(ValueError, 'source'):
                    installer.install(target, True)
            self.assertFalse(target.exists())

    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            source_dir = root / 'adapters/codex/agents'
            source_dir.mkdir(parents=True)
            self.symlink(source_dir / 'oq-evidence-reviewer.toml',
                         ROOT / 'adapters/codex/agents/oq-evidence-reviewer.toml')
            with patch.object(installer, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    installer.install(root / 'target', True)
            self.assertFalse((root / 'target').exists())

    def test_cli_default_is_dry_run(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'new-agents'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/install_codex_agents.py'),
                                     '--target', str(target)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(json.loads(result.stdout)['applied'])
            self.assertFalse(target.exists())

    def test_mid_install_failure_rolls_back_owned_files(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            original_link = installer.os.link
            calls = 0

            def fail_second(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('synthetic publication failure')
                return original_link(source, destination)

            with patch.object(installer.os, 'link', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'synthetic publication failure'):
                    installer.install(target, True)
            self.assertEqual([], list(target.iterdir()))

    def test_rollback_preserves_chmod_only_user_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            first = target / (installer.AGENTS[0] + '.toml')
            link = installer.os.link
            calls = []
            def fail_second(source, destination):
                calls.append(1)
                if len(calls) == 2:
                    first.chmod(0o400)
                    raise OSError('synthetic second publication failure')
                return link(source, destination)
            with patch.object(installer.os, 'link', fail_second), self.assertRaises(OSError):
                installer.install(target, True)
            self.assertTrue(first.is_file())
            self.assertEqual(0, first.stat().st_mode & 0o222)
            self.assertEqual(installer._sources()[installer.AGENTS[0]], first.read_bytes())

    def test_current_link_chmod_failure_retains_staging_without_chmod_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            link = installer.os.link
            def change_then_fail(source, destination):
                link(source, destination)
                Path(destination).chmod(0o400)
                raise OSError('synthetic failure after changed publication')
            with patch.object(installer.os, 'link', change_then_fail), self.assertRaises(OSError):
                installer.install(target, True)
            first = target / (installer.AGENTS[0] + '.toml')
            self.assertTrue(first.is_file())
            self.assertEqual(0, first.stat().st_mode & 0o222)
            staging = list(target.glob('.outcome-qa-agent-*.tmp'))
            self.assertEqual(1, len(staging))
            self.assertTrue(staging[0].samefile(first))

    def test_cli_unicode_target_under_ascii_encoding_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'агенты'
            command = [sys.executable, '-B', str(ROOT / 'scripts/install_codex_agents.py'), '--target', str(target)]
            for apply in (False, True):
                result = subprocess.run(command + (['--apply'] if apply else []),
                                        env={**os.environ, 'PYTHONIOENCODING': 'ascii'}, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(str(target), data['target'])
                self.assertEqual(apply, data['applied'])
                self.assertEqual(apply, target.exists())

    @unittest.skipIf(tomllib is None, 'TOML syntax check requires Python 3.11+; byte-copy tests still run')
    def test_native_schema_and_capability_reductions(self):
        for name, payload in installer._sources().items():
            data = tomllib.loads(payload.decode('utf-8'))
            self.assertEqual(name, data['name'])
            self.assertTrue(data['description'].strip())
            self.assertTrue(data['developer_instructions'].strip())
            self.assertEqual({'name', 'description', 'developer_instructions', 'features', 'skills'}, set(data))
            self.assertEqual({'shell_tool': False, 'apps': False, 'plugins': False,
                              'memories': False, 'request_permissions_tool': False}, data['features'])
            self.assertFalse(data['skills']['include_instructions'])
            self.assertFalse(data['skills']['bundled']['enabled'])
            self.assertIn('context-only', data['developer_instructions'])
            self.assertIn('not an independent security sandbox', data['developer_instructions'])
