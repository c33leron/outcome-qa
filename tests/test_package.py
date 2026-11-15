import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('qa_package', ROOT / 'scripts/package.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def symlink(self, link, target):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def test_validator_reads_utf8_independently_of_default_locale(self):
        read_text = Path.read_text

        def ascii_default(path, *args, **kwargs):
            if not args and 'encoding' not in kwargs:
                kwargs['encoding'] = 'ascii'
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_text', ascii_default):
            self.assertEqual([], packager.validate(ROOT))

    def copy(self, root):
        # macOS tempfile can use /var -> /private/var. These are ordinary
        # archive controls, not the separate symlink-boundary tests.
        dest = Path(root).resolve() / 'outcome-qa'
        # Start each package test from declared current source bytes. Copying
        # the author's entire checkout lets unrelated, unlisted files mask the
        # specific fault a test introduces. The production packager remains
        # strict; negative controls add their own unlisted data below.
        inventory = json.loads((ROOT / 'package-files.json').read_text(encoding='utf-8'))
        for relative in inventory['files']:
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return dest

    def test_fixture_copy_uses_current_inventory_bytes_not_unlisted_workspace_files(self):
        """Unrelated author assets must not prevent a negative test reaching its oracle."""
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve() / 'source'
            source.mkdir()
            names = ['package-files.json', 'nested/current.txt']
            (source / 'package-files.json').write_text(
                json.dumps({'format': 1, 'files': names}), encoding='utf-8')
            (source / 'nested').mkdir()
            (source / 'nested/current.txt').write_text('uncommitted current bytes', encoding='utf-8')
            (source / 'unlisted-author-asset.txt').write_text('preserve outside fixture', encoding='utf-8')
            with patch.dict(globals(), ROOT=source):
                copied = self.copy(Path(temporary) / 'destination')
            self.assertEqual('uncommitted current bytes',
                             (copied / 'nested/current.txt').read_text(encoding='utf-8'))
            self.assertFalse((copied / 'unlisted-author-asset.txt').exists())
            self.assertEqual('preserve outside fixture',
                             (source / 'unlisted-author-asset.txt').read_text(encoding='utf-8'))

    def test_archive_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            root = self.copy(t)
            output = Path(t).resolve() / 'release.zip'
            with patch.object(packager, 'ROOT', root):
                result = packager.build(output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(result['files'], len(z.namelist()))
                self.assertEqual((root / 'plugin.json').read_bytes(), z.read('outcome-qa/plugin.json'))
                self.assertIn('outcome-qa/licenses/gstack-MIT.txt', z.namelist())
                self.assertTrue(all('\\' not in name for name in z.namelist()))

    def test_windows_relative_keys_preserve_manifest_and_zip_path_contract(self):
        # A small fixture isolates archive path serialization, not package validity.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'source'
            (root / 'licenses').mkdir(parents=True)
            (root / 'licenses/notice.txt').write_bytes(b'notice\n')
            names = ['licenses/notice.txt', 'package-files.json']
            (root / 'package-files.json').write_text(json.dumps({'format': 1, 'files': names}))
            relative_to = type(root).relative_to

            def windows_relative(path, *args):
                return PureWindowsPath(relative_to(path, *args).as_posix())

            output = Path(temporary).resolve() / 'archive.zip'
            with patch.object(packager, 'ROOT', root), patch.object(packager, 'validate', return_value=[]), \
                 patch.object(type(root), 'relative_to', windows_relative):
                packager.build(output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual({'outcome-qa/' + name for name in names}, set(archive.namelist()))
                self.assertEqual(b'notice\n', archive.read('outcome-qa/licenses/notice.txt'))

    def test_unlisted_private_data_cannot_enter_archive(self):
        with tempfile.TemporaryDirectory() as t:
            root = self.copy(t)
            (root / 'evals/private-chat-export.json').write_text('{"private":"synthetic canary"}')
            output = Path(t).resolve() / 'release.zip'
            with patch.object(packager, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Unlisted'):
                packager.build(output)
            self.assertFalse(output.exists())

    def test_missing_inventory_item_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = self.copy(t)
            data = json.loads((root / 'package-files.json').read_text(encoding='utf-8'))
            data['files'].append('invented.txt')
            (root / 'package-files.json').write_text(json.dumps(data))
            with patch.object(packager, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Missing inventoried'):
                packager.build(Path(t).resolve() / 'release.zip')

    def test_no_archive_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root = self.copy(t)
            output = Path(t).resolve() / 'release.zip'
            output.write_bytes(b'keep')
            with patch.object(packager, 'ROOT', root), self.assertRaisesRegex(ValueError, 'overwrite'):
                packager.build(output)
            self.assertEqual(b'keep', output.read_bytes())

    def test_output_symlink_alias_cannot_write_into_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            alias = Path(temporary).resolve() / 'source-alias'
            self.symlink(alias, root)
            with patch.object(packager, 'ROOT', root), self.assertRaisesRegex(ValueError, 'symlink|outside'):
                packager.build(alias / 'release.zip')
            self.assertFalse((root / 'release.zip').exists())

    def test_failed_member_write_leaves_no_final_or_staging_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            output = Path(temporary).resolve() / 'release.zip'
            write = zipfile.ZipFile.write
            calls = []
            def fail_second(archive, *args, **kwargs):
                calls.append(1)
                if len(calls) == 2:
                    raise OSError('synthetic second member failure')
                return write(archive, *args, **kwargs)
            with patch.object(packager, 'ROOT', root), patch.object(zipfile.ZipFile, 'write', fail_second), \
                 self.assertRaisesRegex(OSError, 'synthetic'):
                packager.build(output)
            self.assertEqual(2, len(calls))
            self.assertFalse(output.exists())
            self.assertEqual([], list(output.parent.glob('.outcome-qa-source-*')))

    def test_failed_readback_leaves_no_final_or_staging_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            output = Path(temporary).resolve() / 'release.zip'
            with patch.object(packager, 'ROOT', root), patch.object(zipfile.ZipFile, 'testzip', return_value='bad'), \
                 self.assertRaisesRegex(ValueError, 'read-back'):
                packager.build(output)
            self.assertFalse(output.exists())
            self.assertEqual([], list(output.parent.glob('.outcome-qa-source-*')))

    def test_ambiguous_manifests_are_rejected(self):
        for relative, key in [('plugin.json', 'name'), ('plugin.json', '$schema'),
                              ('.codex-plugin/plugin.json', 'version'),
                              ('.claude-plugin/plugin.json', 'name')]:
            with tempfile.TemporaryDirectory() as t:
                root = self.copy(t)
                p = root / relative
                original = p.read_text(encoding='utf-8')
                p.write_text('{"'+key+'":"ambiguous",' + original[1:])
                with patch.object(packager, 'ROOT', root), self.assertRaisesRegex(ValueError, 'duplicate'):
                    packager.build(Path(t).resolve() / 'release.zip')

    def test_duplicate_inventory_and_nonfinite_manifest_rejected(self):
        for relative, prefix in [('package-files.json', '"files":[],') , ('plugin.json', '"unknown":1e999,')]:
            with tempfile.TemporaryDirectory() as t:
                root = self.copy(t)
                p = root / relative;p.write_text('{'+prefix+p.read_text(encoding='utf-8')[1:])
                with patch.object(packager, 'ROOT', root), self.assertRaises(ValueError):
                    packager.build(Path(t).resolve() / 'release.zip')
