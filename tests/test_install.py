import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install_skills.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def symlink(self, link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def copy_sources(self, base):
        source = Path(base) / 'source'
        source.mkdir()
        for name in ('skills', 'licenses'):
            shutil.copytree(ROOT / name, source / name)
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
            shutil.copy2(ROOT / name, source / name)
        return source

    def test_every_standalone_skill_carries_both_mit_notices(self):
        expected = ((ROOT / 'LICENSE').read_bytes().rstrip() + b'\n\n'
                    + (ROOT / 'licenses/gstack-MIT.txt').read_bytes().rstrip() + b'\n')
        for name in sorted(installer.SKILLS):
            with self.subTest(skill=name):
                self.assertEqual(expected, (ROOT / 'skills' / name / 'LICENSE.txt').read_bytes())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'new'
            result = installer.install(target)
            self.assertFalse(result['applied'])
            self.assertFalse(target.exists())

    def test_cli_unicode_target_is_safe_with_ascii_output_encoding(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'skills with spaces - тест'
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/install_skills.py'), '--target', str(target)],
                env={**os.environ, 'PYTHONIOENCODING': 'ascii'}, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(str(target), json.loads(result.stdout)['target'])
            self.assertFalse(target.exists())

    def test_install_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            result = installer.install(target, True)
            self.assertEqual(7, len(result['skills']))
            for name in result['skills']:
                self.assertTrue((target / name / 'SKILL.md').is_file())
                self.assertTrue((target / name / 'licenses/gstack-MIT.txt').is_file())
                originals = {str(p.relative_to(ROOT / 'skills' / name)): p
                             for p in (ROOT / 'skills' / name).rglob('*') if p.is_file()}
                originals.update({notice: ROOT / notice for notice in ('LICENSE', 'THIRD_PARTY_NOTICES.md')})
                originals.update({str(p.relative_to(ROOT)): p for p in (ROOT / 'licenses').rglob('*') if p.is_file()})
                installed = {str(p.relative_to(target / name)): p for p in (target / name).rglob('*') if p.is_file()}
                self.assertEqual(set(originals), set(installed))
                for relative, original in originals.items():
                    self.assertEqual(original.read_bytes(), installed[relative].read_bytes())
            user_file = target / result['skills'][0] / 'user-note.txt'
            user_file.write_text('keep me')
            with self.assertRaises(ValueError):
                installer.install(target, True)
            self.assertEqual('keep me', user_file.read_text(encoding='utf-8'))

    def test_reject_target_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'link'
            self.symlink(target, Path(t), target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(target, True)

    def test_windows_reparse_attribute_is_rejected_before_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'target'
            lstat = Path.lstat
            def reparse(path):
                if path == target:
                    return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
                return lstat(path)
            with patch.object(Path, 'lstat', reparse), self.assertRaisesRegex(ValueError, 'real directory'):
                installer.install(target, True)
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == 'nt', 'Actual NTFS junction creation requires Windows')
    def test_actual_windows_junction_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            real = Path(temporary) / 'real'
            real.mkdir()
            junction = Path(temporary) / 'junction'
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(real)],
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            try:
                with self.assertRaisesRegex(ValueError, 'real directory'):
                    installer.install(junction, True)
                self.assertEqual([], list(real.iterdir()))
            finally:
                junction.rmdir()

    def test_collision_does_not_partially_install(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t)
            (target / 'oq-retest').mkdir()
            with self.assertRaises(ValueError):
                installer.install(target, True)
            self.assertEqual(['oq-retest'], [p.name for p in target.iterdir()])

    def test_missing_provenance_rejected_in_preview_and_apply(self):
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt'):
            for apply in (False, True):
                with self.subTest(name=name, apply=apply), tempfile.TemporaryDirectory() as t:
                    source = self.copy_sources(t)
                    (source / name).unlink()
                    target = Path(t) / 'target'
                    with patch.object(installer, 'ROOT', source), self.assertRaises(ValueError):
                        installer.install(target, apply)
                    self.assertFalse(target.exists())

    def test_empty_upstream_notice_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            source = self.copy_sources(t)
            (source / 'licenses/gstack-MIT.txt').write_text(' \n')
            target = Path(t) / 'target'
            with patch.object(installer, 'ROOT', source), self.assertRaises(ValueError):
                installer.install(target, True)
            self.assertFalse(target.exists())

    def test_wrong_skills_are_not_the_complete_package(self):
        with tempfile.TemporaryDirectory() as t:
            source = self.copy_sources(t)
            shutil.rmtree(source / 'skills/oq-retest')
            (source / 'skills/oq-imposter').mkdir()
            (source / 'skills/oq-imposter/SKILL.md').write_text('---\nname: "oq-imposter"\ndescription: "Fake"\n---\nFake')
            with patch.object(installer, 'ROOT', source), self.assertRaises(ValueError):
                installer.install(Path(t) / 'target')

    def test_unexpected_skill_directory_without_entrypoint_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            source = self.copy_sources(t)
            (source / 'skills/extra-incomplete-skill').mkdir()
            with patch.object(installer, 'ROOT', source), self.assertRaises(ValueError):
                installer.install(Path(t) / 'target')

    def test_provenance_file_and_directory_symlinks_rejected(self):
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses', 'licenses/gstack-MIT.txt'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as t:
                source = self.copy_sources(t)
                original = source / name
                saved = Path(t) / 'saved'
                original.rename(saved)
                self.symlink(original, saved, target_is_directory=saved.is_dir())
                target = Path(t) / 'target'
                with patch.object(installer, 'ROOT', source), self.assertRaises(ValueError):
                    installer.install(target, True)
                self.assertFalse(target.exists())

    def test_mid_publication_failure_cleans_unchanged_owned_entries(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            def fail_after_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                raise PermissionError('injected write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_link), self.assertRaises(PermissionError):
                installer.install(target, True)
            self.assertEqual([], list(target.iterdir()))

    def test_rollback_preserves_concurrent_user_addition(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            notes = []
            def fail_after_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                note = Path(dst).parent / 'user-note.txt'
                note.write_text('new user data')
                notes.append(note)
                raise PermissionError('injected write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_link), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertEqual('new user data', notes[0].read_text(encoding='utf-8'))
            self.assertEqual(['user-note.txt'], [p.name for p in notes[0].parent.iterdir()])

    def test_failure_after_nested_publication_cleans_owned_tree(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            injected = []
            def fail_after_nested_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                if Path(dst).parent.name == 'licenses':
                    injected.append(Path(dst))
                    raise PermissionError('injected nested write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_nested_link), self.assertRaises(PermissionError):
                installer.install(target, True)
            self.assertEqual(1, len(injected))
            self.assertEqual([], list(target.iterdir()))

    def test_rollback_preserves_modified_published_file(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            changed = []
            def fail_after_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                Path(dst).write_text('user modified published file')
                changed.append(Path(dst))
                raise PermissionError('injected write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_link), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertEqual('user modified published file', changed[0].read_text(encoding='utf-8'))

    def test_rollback_preserves_equal_bytes_with_new_identity(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            changed = []
            def fail_after_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                dest = Path(dst)
                data = dest.read_bytes()
                dest.rename(dest.with_name('user-kept-original'))
                dest.write_bytes(data)
                changed.append(dest)
                raise PermissionError('injected write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_link), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertTrue(changed[0].is_file())
            self.assertTrue(changed[0].with_name('user-kept-original').is_file())

    def test_rollback_preserves_file_permissions_changed_by_user(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            changed = []
            def fail_after_link(src, dst, **kwargs):
                link(src, dst, **kwargs)
                Path(dst).chmod(0o400)
                changed.append((Path(dst), Path(dst).stat().st_mode & 0o777))
                raise PermissionError('injected write failure')
            with patch.object(installer.os, 'link', side_effect=fail_after_link), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            path, actual_readonly_mode = changed[0]
            self.assertTrue(path.is_file())
            self.assertEqual(0, actual_readonly_mode & 0o222)
            self.assertEqual(actual_readonly_mode, path.stat().st_mode & 0o777)
            staging = list(target.glob('.outcome-qa-stage-*'))
            self.assertEqual(1, len(staging))
            staged_path = staging[0] / path.relative_to(target)
            self.assertTrue(staged_path.samefile(path))
            self.assertEqual(actual_readonly_mode, staged_path.stat().st_mode & 0o777)

    def test_rollback_preserves_unknown_nested_file(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            publish = installer._publish
            notes = []
            def fail_after_directory_publish(src, dst, root, expected):
                publish(src, dst, root, expected)
                if Path(dst).is_dir():
                    note = Path(dst) / 'user-note.txt'
                    note.write_text('nested user data')
                    notes.append(note)
                    raise PermissionError('injected write failure')
            with patch.object(installer, '_publish', side_effect=fail_after_directory_publish), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertEqual('nested user data', notes[0].read_text(encoding='utf-8'))
            self.assertEqual(['user-note.txt'], [p.name for p in notes[0].parent.iterdir()])

    def test_file_created_before_publish_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            link = installer.os.link
            collisions = []
            data = b'CONCURRENTUSERDATA\x00\xff'
            def collision_before_link(src, dst, **kwargs):
                Path(dst).write_bytes(data)
                collisions.append(Path(dst))
                return link(src, dst, **kwargs)
            with patch.object(installer.os, 'link', side_effect=collision_before_link), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertEqual(data, collisions[0].read_bytes())
            self.assertEqual([collisions[0].name], [p.name for p in collisions[0].parent.iterdir()])
            self.assertFalse((collisions[0].parent / 'SKILL.md').exists())

    def test_directory_created_before_publish_is_never_merged(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'target'
            publish = installer._publish
            collisions = []
            data = b'CONCURRENT TREE CONTENT\x00\xff'
            def collision_before_directory(src, dst, root, expected):
                if Path(src).is_dir() and not collisions:
                    Path(dst).mkdir()
                    (Path(dst) / 'user' / 'empty').mkdir(parents=True)
                    (Path(dst) / 'user' / 'original.bin').write_bytes(data)
                    collisions.append(Path(dst))
                return publish(src, dst, root, expected)
            with patch.object(installer, '_publish', side_effect=collision_before_directory), self.assertRaisesRegex(OSError, 'rollback preserved'):
                installer.install(target, True)
            self.assertEqual(data, (collisions[0] / 'user/original.bin').read_bytes())
            self.assertEqual({'user', 'user/empty', 'user/original.bin'},
                             {p.relative_to(collisions[0]).as_posix() for p in collisions[0].rglob('*')})
            self.assertEqual([collisions[0].name], [p.name for p in collisions[0].parent.iterdir()])
            self.assertFalse((collisions[0].parent / 'SKILL.md').exists())

    def test_entrypoint_is_published_last(self):
        with tempfile.TemporaryDirectory() as t:
            calls = {}
            publish = installer._publish
            def record(src, dst, root, expected):
                if Path(dst).parent == root:
                    calls.setdefault(root.name, []).append(Path(dst).name)
                return publish(src, dst, root, expected)
            with patch.object(installer, '_publish', side_effect=record):
                installer.install(Path(t) / 'target', True)
            self.assertEqual(7, len(calls))
            for names in calls.values():
                self.assertEqual('SKILL.md', names[-1])
