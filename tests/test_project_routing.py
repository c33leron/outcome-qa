import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('project_routing', ROOT / 'scripts/project_routing.py')
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

# Literal released 0.1.0 fixture: do not derive this from current routing.block().
LEGACY_0_1_0 = '''<!-- outcome-qa:start -->
Use the installed Outcome QA method matching the requested work:
- oq-test-design: planned cases and coverage from requirements; no implied execution.
- oq-explore: actual product journeys, frontend/API behavior and regression exploration.
- oq-automation: write, review or diagnose automated test code and CI failures.
- oq-ai-quality: AI meaning, conversation behavior and saved/tool outcomes.
- oq-checker-audit: reliability of assertions, judges, metrics and evaluation gates.
- oq-retest: replay a claimed fix under equivalent relevant conditions.
- oq-security-journeys: scoped feature security and access/data/action controls.
Load only relevant methods; preserve task scope and host permissions. Missing tools are not executed checks.
<!-- outcome-qa:end -->

'''.encode('utf-8')


class ProjectRoutingTests(unittest.TestCase):
    def symlink(self, link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name).resolve()

    def test_preview_does_not_write_or_expose_unrelated_content(self):
        path = self.project / 'AGENTS.md'
        path.write_text('PRIVATE CANARY: retain this\n')
        before = path.read_bytes()
        result = routing.configure(self.project, 'codex')
        self.assertTrue(result['changed'])
        self.assertFalse(result['applied'])
        self.assertIn('Coordinate other writers', result['limit'])
        self.assertIn('stale open handles after that point are outside this guarantee', result['limit'])
        self.assertNotIn('PRIVATE CANARY', result['diff'])
        self.assertIn('oq-test-design', result['diff'])
        self.assertEqual(before, path.read_bytes())

    def test_apply_is_idempotent_remove_restores_exact_no_final_newline(self):
        path = self.project / 'AGENTS.md'
        original = 'Existing rules\nРусский текст without final newline'.encode()
        path.write_bytes(original)
        path.chmod(0o640)
        expected_mode = path.stat().st_mode & 0o777
        result = routing.configure(self.project, 'codex', apply=True)
        self.assertTrue(result['applied'])
        self.assertTrue(path.read_bytes().endswith(original))
        self.assertEqual(expected_mode, path.stat().st_mode & 0o777)
        self.assertFalse(routing.configure(self.project, 'codex', apply=True)['changed'])
        routing.configure(self.project, 'codex', apply=True, remove=True)
        self.assertEqual(original, path.read_bytes())

    def test_released_block_preview_and_upgrade_preserve_surrounding_bytes(self):
        for newline in (b'\n', b'\r\n'):
            for bom in (b'', b'\xef\xbb\xbf'):
                with self.subTest(newline=newline, bom=bom):
                    path = self.project / 'AGENTS.md'
                    prefix = bom + b'Existing instruction' + newline
                    suffix = 'Private unrelated instructions без final newline'.encode('utf-8')
                    legacy = LEGACY_0_1_0.replace(b'\n', newline)
                    before = prefix + legacy + suffix
                    path.write_bytes(before)
                    preview = routing.configure(self.project, 'codex')
                    self.assertTrue(preview['changed'])
                    self.assertFalse(preview['applied'])
                    self.assertEqual(before, path.read_bytes())
                    self.assertNotIn('Private unrelated', preview['diff'])
                    applied = routing.configure(self.project, 'codex', apply=True)
                    self.assertTrue(applied['applied'])
                    self.assertEqual(prefix + routing.block(newline.decode()) + suffix, path.read_bytes())
                    self.assertFalse(routing.configure(self.project, 'codex', apply=True)['changed'])
                    routing.configure(self.project, 'codex', apply=True, remove=True)
                    self.assertEqual(prefix + suffix, path.read_bytes())

    def test_released_block_can_be_removed_without_upgrading(self):
        for newline in (b'\n', b'\r\n'):
            path = self.project / 'CLAUDE.md'
            before = b'\xef\xbb\xbf' + LEGACY_0_1_0.replace(b'\n', newline) + b'Keep me'
            path.write_bytes(before)
            routing.configure(self.project, 'claude', apply=True, remove=True)
            self.assertEqual(b'\xef\xbb\xbfKeep me', path.read_bytes())

    def test_modified_released_block_is_not_migrated_or_removed(self):
        path = self.project / 'AGENTS.md'
        for edited in (LEGACY_0_1_0.replace(b'oq-retest:', b'custom-retest:'),
                       LEGACY_0_1_0.replace(b'Load only relevant', b'Custom policy: Load only relevant')):
            path.write_bytes(edited)
            for remove in (False, True):
                with self.subTest(remove=remove, edited=edited[:40]):
                    with self.assertRaisesRegex(ValueError, 'edited'):
                        routing.configure(self.project, 'codex', apply=True, remove=remove)
                    self.assertEqual(edited, path.read_bytes())

    def test_crlf_and_bom_preserved_roundtrip(self):
        path = self.project / 'CLAUDE.md'
        original = b'\xef\xbb\xbfFirst\r\nSecond\r\n'
        path.write_bytes(original)
        routing.configure(self.project, 'claude', apply=True)
        data = path.read_bytes()
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(data.replace(b'\r\n', b''), data.replace(b'\r\n', b'').replace(b'\n', b''))
        routing.configure(self.project, 'claude', apply=True, remove=True)
        self.assertEqual(original, path.read_bytes())

    def test_bom_preview_does_not_echo_unchanged_private_first_line(self):
        path = self.project / 'AGENTS.md'
        original = b'\xef\xbb\xbfPRIVATE FIRST LINE\r\nOther private material'
        path.write_bytes(original)
        preview = routing.configure(self.project, 'codex')
        self.assertNotIn('PRIVATE FIRST LINE', preview['diff'])
        self.assertNotIn('Other private material', preview['diff'])
        self.assertEqual(original, path.read_bytes())

    def test_user_prefix_and_suffix_survive_removal(self):
        path = self.project / 'AGENTS.md'
        original = b'Original no final newline'
        path.write_bytes(original)
        routing.configure(self.project, 'codex', apply=True)
        path.write_bytes(b'New intro\n' + path.read_bytes() + b'\nLater user addition')
        routing.configure(self.project, 'codex', apply=True, remove=True)
        self.assertEqual(b'New intro\n' + original + b'\nLater user addition', path.read_bytes())

    def test_new_file_and_remove_do_not_delete_instruction_file(self):
        path = self.project / 'AGENTS.md'
        routing.configure(self.project, 'codex', apply=True)
        self.assertTrue(path.is_file())
        routing.configure(self.project, 'codex', apply=True, remove=True)
        self.assertEqual(b'', path.read_bytes())
        self.assertFalse(routing.configure(self.project, 'codex', apply=True, remove=True)['changed'])

    def test_remove_missing_file_does_not_create_it(self):
        self.assertFalse(routing.configure(self.project, 'claude', apply=True, remove=True)['changed'])
        self.assertFalse((self.project / 'CLAUDE.md').exists())

    def test_modified_managed_block_is_preserved(self):
        path = self.project / 'AGENTS.md'
        routing.configure(self.project, 'codex', apply=True)
        path.write_bytes(path.read_bytes().replace(b'oq-retest:', b'custom-retest:'))
        before = path.read_bytes()
        for remove in [False, True]:
            with self.assertRaisesRegex(ValueError, 'edited'):
                routing.configure(self.project, 'codex', apply=True, remove=remove)
            self.assertEqual(before, path.read_bytes())

    def test_duplicate_nested_unbalanced_and_inline_markers_rejected(self):
        samples = [routing.block() * 2, routing.START.encode(), routing.END.encode(),
                   routing.START.encode() + routing.block(),
                   b'inline ' + routing.block(),
                   routing.END.encode() + b'\n' + routing.START.encode()]
        path = self.project / 'AGENTS.md'
        for payload in samples:
            with self.subTest(payload=payload):
                path.write_bytes(payload)
                with self.assertRaises(ValueError):
                    routing.configure(self.project, 'codex', apply=True)
                self.assertEqual(payload, path.read_bytes())

    def test_explicit_host_only_changes_its_own_file(self):
        (self.project / 'AGENTS.md').write_text('codex remains')
        routing.configure(self.project, 'claude', apply=True)
        self.assertEqual('codex remains', (self.project / 'AGENTS.md').read_text(encoding='utf-8'))
        self.assertIn(routing.START, (self.project / 'CLAUDE.md').read_text(encoding='utf-8'))

    def test_project_and_instruction_symlinks_rejected(self):
        link = self.project / 'project-link'
        real = self.project / 'real'
        real.mkdir()
        self.symlink(link, real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            routing.configure(link, 'codex', apply=True)
        self.symlink(real / 'AGENTS.md', self.project / 'missing')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            routing.configure(real, 'codex', apply=True)

    def test_global_or_absent_project_and_invalid_host_rejected(self):
        for project in [Path('/'), Path.home(), Path.home() / '.codex', self.project / 'missing']:
            with self.subTest(project=project), self.assertRaises(ValueError):
                routing.configure(project, 'codex', apply=True)
        with self.assertRaises(ValueError):
            routing.configure(self.project, '../outside', apply=True)

    def test_filesystem_roots_include_windows_drives_and_unc_shares(self):
        for root in (PurePosixPath('/'), PureWindowsPath('C:/'),
                     PureWindowsPath('D:/'), PureWindowsPath('//server/share/')):
            with self.subTest(root=root):
                self.assertTrue(routing._is_filesystem_root(root))
                self.assertFalse(routing._is_filesystem_root(root / 'project'))
        self.assertFalse(routing._is_filesystem_root(PureWindowsPath('C:')))

    def test_invalid_utf8_and_nonregular_instruction_rejected(self):
        path = self.project / 'AGENTS.md'
        path.write_bytes(b'\xff\xfe')
        with self.assertRaises(UnicodeError):
            routing.configure(self.project, 'codex', apply=True)
        path.unlink()
        path.mkdir()
        with self.assertRaises((ValueError, OSError)):
            routing.configure(self.project, 'codex', apply=True)

    def test_concurrent_change_before_replace_is_preserved(self):
        path = self.project / 'AGENTS.md'
        path.write_text('before')
        check = routing._assert_preimage
        calls = []
        def edit(project, target, snapshot):
            calls.append(1)
            if len(calls) == 2:
                target.write_text('CONCURRENT EDIT')
            return check(project, target, snapshot)
        with patch.object(routing, '_assert_preimage', edit), self.assertRaisesRegex(ValueError, 'changed'):
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual('CONCURRENT EDIT', path.read_text(encoding='utf-8'))
        self.assertEqual([], list(self.project.glob('.outcome-routing-*')))

    def test_new_file_collision_is_preserved(self):
        path = self.project / 'AGENTS.md'
        link = routing.os.link
        def race(source, target):
            Path(target).write_text('CONCURRENT FILE')
            return link(source, target)
        with patch.object(routing.os, 'link', race), self.assertRaises(FileExistsError):
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual('CONCURRENT FILE', path.read_text(encoding='utf-8'))
        self.assertEqual([], list(self.project.glob('.outcome-routing-*')))

    def test_cli_requires_project_and_defaults_to_preview(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/project_routing.py'),
                                 '--project', str(self.project), '--host', 'codex'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(json.loads(result.stdout)['applied'])
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_same_bytes_replaced_during_edit_are_still_a_conflict(self):
        path = self.project / 'AGENTS.md'
        path.write_bytes(b'same bytes')
        snapshot = routing._read(path)
        replacement = self.project / 'replacement'
        replacement.write_bytes(b'same bytes')
        os.replace(replacement, path)
        with self.assertRaisesRegex(ValueError, 'changed'):
            routing._assert_preimage(self.project, path, snapshot)

    def test_final_move_race_restores_the_actual_concurrent_edit(self):
        path = self.project / 'AGENTS.md'
        path.write_bytes(b'old rules')
        rename = routing.os.rename
        def edit_at_move(source, destination):
            if Path(source) == path:
                path.write_bytes(b'FINAL CONCURRENT EDIT\x00')
            return rename(source, destination)
        with patch.object(routing.os, 'rename', edit_at_move), self.assertRaisesRegex(ValueError, 'final move'):
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual(b'FINAL CONCURRENT EDIT\x00', path.read_bytes())
        self.assertEqual([], list(self.project.glob('.outcome-routing-*')))

    def test_final_publish_race_preserves_new_file_and_quarantined_original(self):
        path = self.project / 'AGENTS.md'
        original = b'original instructions'
        path.write_bytes(original)
        link = routing.os.link
        injected = []
        def collide(source, destination, **kwargs):
            if Path(source).name != 'previous' and not injected:
                injected.append(True)
                Path(destination).write_bytes(b'FINAL USER FILE\x00')
            return link(source, destination, **kwargs)
        with patch.object(routing.os, 'link', collide), self.assertRaisesRegex(OSError, 'recovery entry retained') as error:
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual(b'FINAL USER FILE\x00', path.read_bytes())
        recovery = list(self.project.glob('.outcome-routing-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(original, recovery[0].read_bytes())
        self.assertIn(str(recovery[0]), str(error.exception))

    def test_publish_failure_restores_original_without_leftover_backup(self):
        path = self.project / 'AGENTS.md'
        original = b'private original\r\nno last newline'
        path.write_bytes(original)
        path.chmod(0o640)
        expected_mode = path.stat().st_mode & 0o777
        link = routing.os.link
        def fail_publish(source, destination, **kwargs):
            if Path(source).name != 'previous':
                raise PermissionError('injected final publication failure')
            return link(source, destination, **kwargs)
        with patch.object(routing.os, 'link', fail_publish), self.assertRaisesRegex(PermissionError, 'injected'):
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual(original, path.read_bytes())
        self.assertEqual(expected_mode, path.stat().st_mode & 0o777)
        self.assertEqual([], list(self.project.glob('.outcome-routing-*')))

    def test_mismatched_preimage_and_occupied_destination_are_both_preserved(self):
        path = self.project / 'AGENTS.md'
        path.write_bytes(b'initial')
        rename = routing.os.rename
        def replace_both(source, destination):
            if Path(source) == path:
                path.write_bytes(b'changed just before move')
                result = rename(source, destination)
                path.write_bytes(b'new arrival after move')
                return result
            return rename(source, destination)
        with patch.object(routing.os, 'rename', replace_both), self.assertRaisesRegex(OSError, 'recovery entry retained'):
            routing.configure(self.project, 'codex', apply=True)
        self.assertEqual(b'new arrival after move', path.read_bytes())
        recovery = list(self.project.glob('.outcome-routing-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(b'changed just before move', recovery[0].read_bytes())

    def test_old_open_handle_write_before_commit_check_is_retained(self):
        path = self.project / 'AGENTS.md'
        path.write_bytes(b'original')
        link = routing.os.link
        with path.open('r+b') as old_handle:
            def edit_old_inode(source, destination, **kwargs):
                result = link(source, destination, **kwargs)
                if Path(source).name != 'previous':
                    old_handle.seek(0)
                    old_handle.write(b'user edit through old handle')
                    old_handle.truncate()
                    old_handle.flush()
                return result
            with patch.object(routing.os, 'link', edit_old_inode), self.assertRaises(OSError) as error:
                routing.configure(self.project, 'codex', apply=True)
        if getattr(error.exception, 'winerror', None) == 32:
            # Windows can forbid moving an open file: refusal must be non-destructive.
            self.assertEqual(b'original', path.read_bytes())
            self.assertEqual([], list(self.project.glob('.outcome-routing-*')))
            return
        self.assertIn('recovery entry retained', str(error.exception))
        self.assertIn(routing.START.encode(), path.read_bytes())
        recovery = list(self.project.glob('.outcome-routing-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(b'user edit through old handle', recovery[0].read_bytes())
