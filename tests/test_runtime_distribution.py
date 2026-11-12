"""The installed/runtime package excludes our own tests, labs and work products."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('runtime_builder', ROOT / 'scripts/build_runtime.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class RuntimeDistributionTests(unittest.TestCase):
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
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / 'development'
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        self.patch = patch.object(builder, 'ROOT', self.source)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.mapping = json.loads((self.source / 'runtime-files.json').read_text(encoding='utf-8'))

    def change(self, mapping):
        (self.source / 'runtime-files.json').write_text(json.dumps(mapping))

    def files(self, directory):
        return {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}

    def test_directory_has_exact_runtime_bytes_and_no_development_files(self):
        out = self.base / 'plugin'
        result = builder.build_directory(out)
        self.assertEqual(set(self.mapping['files']), self.files(out))
        self.assertEqual(len(self.mapping['files']), result['files'])
        for destination, source in self.mapping['files'].items():
            self.assertEqual((self.source / source).read_bytes(), (out / destination).read_bytes())
            self.assertFalse(set(Path(destination).parts) & builder.DEV_PARTS)
        self.assertTrue((self.source / 'tests/test_runtime_distribution.py').exists())
        self.assertTrue((self.source / 'scripts/demo_app.py').exists())
        self.assertFalse((out / 'tests').exists())
        self.assertFalse((out / 'scripts/demo_app.py').exists())

    def test_zip_has_the_same_exact_clean_profile(self):
        out = self.base / 'runtime.zip'
        result = builder.build_archive(out)
        self.assertEqual('runtime', result['profile'])
        with zipfile.ZipFile(out) as archive:
            self.assertEqual({'outcome-qa/' + p for p in self.mapping['files']}, set(archive.namelist()))
            self.assertIsNone(archive.testzip())
            for destination, source in self.mapping['files'].items():
                self.assertEqual((self.source / source).read_bytes(), archive.read('outcome-qa/' + destination))

    def test_helpers_and_attribution_work_without_development_tree(self):
        out = self.base / 'plugin'
        builder.build_directory(out)
        shutil.rmtree(self.source)
        for skill in sorted(builder.SKILLS):
            result = subprocess.run([sys.executable, '-B', str(out / 'scripts/export_playbook.py'), skill],
                                    capture_output=True, encoding='utf-8', cwd=out)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('gstack', result.stdout)
            self.assertIn('MIT', result.stdout)
        before = {'record': {'id': 'one', 'text': 'before'}}
        after = {'record': {'id': 'one', 'text': 'after'}}
        contract = {'version': 1, 'goal': 'Only change text', 'identity': [{'path': '/record/id', 'value': 'one'}],
                    'rules': [{'id': 'text', 'op': 'equals', 'path': '/record/text', 'value': 'after'}]}
        for name, value in [('before', before), ('after', after), ('contract', contract)]:
            (self.base / (name + '.json')).write_text(json.dumps(value))
        command = [sys.executable, '-B', str(out / 'scripts/check_transition.py'), 'check', '--format', 'json']
        for name in ['before', 'after', 'contract']:
            command.extend(['--' + name, str(self.base / (name + '.json'))])
        result = subprocess.run(command, capture_output=True, text=True, cwd=out)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('PASS', json.loads(result.stdout)['verdict'])

    def test_existing_directory_is_not_merged_or_replaced(self):
        out = self.base / 'plugin'
        out.mkdir()
        (out / 'keep.bin').write_bytes(b'user\x00bytes')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            builder.build_directory(out)
        self.assertEqual({'keep.bin'}, self.files(out))
        self.assertEqual(b'user\x00bytes', (out / 'keep.bin').read_bytes())

    def test_existing_archive_is_not_replaced(self):
        out = self.base / 'runtime.zip'
        out.write_bytes(b'user archive')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            builder.build_archive(out)
        self.assertEqual(b'user archive', out.read_bytes())

    def test_failed_archive_write_leaves_no_final_or_staging_zip(self):
        out = self.base / 'runtime.zip'
        write = zipfile.ZipFile.writestr
        calls = []
        def write_then_fail(archive, *args, **kwargs):
            write(archive, *args, **kwargs)
            calls.append(1)
            raise OSError('injected write failure')
        with patch.object(zipfile.ZipFile, 'writestr', write_then_fail), self.assertRaisesRegex(OSError, 'injected'):
            builder.build_archive(out)
        self.assertEqual(1, len(calls))
        self.assertFalse(out.exists())
        self.assertEqual([], list(self.base.glob('.outcome-qa-runtime-*')))

    def test_failed_archive_readback_leaves_no_final_or_staging_zip(self):
        out = self.base / 'runtime.zip'
        with patch.object(zipfile.ZipFile, 'testzip', return_value='bad-member'), self.assertRaisesRegex(ValueError, 'read-back'):
            builder.build_archive(out)
        self.assertFalse(out.exists())
        self.assertEqual([], list(self.base.glob('.outcome-qa-runtime-*')))

    def test_concurrent_final_archive_is_preserved(self):
        out = self.base / 'runtime.zip'
        link = builder.os.link
        def publish_collision(source, destination, **kwargs):
            Path(destination).write_bytes(b'CONCURRENT USER ZIP\x00\xff')
            return link(source, destination, **kwargs)
        with patch.object(builder.os, 'link', publish_collision), self.assertRaises(FileExistsError):
            builder.build_archive(out)
        self.assertEqual(b'CONCURRENT USER ZIP\x00\xff', out.read_bytes())
        self.assertEqual([], list(self.base.glob('.outcome-qa-runtime-*')))

    def test_concurrent_output_root_is_not_merged(self):
        out = self.base / 'plugin'
        original = Path.mkdir
        def create_collision(path, *args, **kwargs):
            if path == out and not out.exists():
                original(path)
                (path / 'keep').write_bytes(b'concurrent root')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'mkdir', create_collision), self.assertRaises(FileExistsError):
            builder.build_directory(out)
        self.assertEqual({'keep'}, self.files(out))
        self.assertEqual(b'concurrent root', (out / 'keep').read_bytes())

    def test_concurrent_file_is_preserved_on_failed_publication(self):
        out = self.base / 'plugin'
        original = Path.open
        collisions = []
        def create_collision(path, mode='r', *args, **kwargs):
            if mode == 'xb' and not collisions:
                with original(path, 'wb') as stream:
                    stream.write(b'concurrent file\x00\xff')
                collisions.append(path)
            return original(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', create_collision), self.assertRaisesRegex(OSError, 'preserved'):
            builder.build_directory(out)
        self.assertEqual(b'concurrent file\x00\xff', collisions[0].read_bytes())
        self.assertEqual({collisions[0].relative_to(out).as_posix()}, self.files(out))

    def test_rollback_preserves_chmod_only_user_change(self):
        output = self.base / 'plugin'
        open_file = Path.open
        created = []
        def fail_second(path, mode='r', *args, **kwargs):
            if mode == 'xb':
                if created:
                    created[0].chmod(0o400)
                    raise OSError('synthetic later publication failure')
                created.append(path)
            return open_file(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', fail_second), self.assertRaises(OSError):
            builder.build_directory(output)
        self.assertTrue(created[0].is_file())
        self.assertEqual(0, created[0].stat().st_mode & 0o222)

    def test_rollback_preserves_mtime_only_user_change(self):
        output = self.base / 'plugin'
        open_file = Path.open
        created = []
        modified = []
        def fail_second(path, mode='r', *args, **kwargs):
            if mode == 'xb':
                if created:
                    info = created[0].stat()
                    timestamp = info.st_mtime_ns + 2_000_000_000
                    os.utime(created[0], ns=(info.st_atime_ns, timestamp))
                    modified.append(created[0].stat().st_mtime_ns)
                    raise OSError('synthetic failure after user timestamp change')
                created.append(path)
            return open_file(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', fail_second), self.assertRaises(OSError):
            builder.build_directory(output)
        self.assertTrue(created[0].is_file())
        self.assertEqual(modified[0], created[0].stat().st_mtime_ns)

    def test_output_must_not_be_inside_development_source(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            builder.build_directory(self.source / 'plugin')
        self.assertFalse((self.source / 'plugin').exists())

    def test_dotdot_output_alias_cannot_enter_development_source(self):
        out = self.base / 'other' / '..' / 'development' / 'plugin'
        with self.assertRaisesRegex(ValueError, 'outside'):
            builder.build_directory(out)
        self.assertFalse((self.source / 'plugin').exists())

    def test_output_symlink_parent_is_rejected(self):
        real = self.base / 'real'
        real.mkdir()
        link = self.base / 'alias'
        self.symlink(link, real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            builder.build_directory(link / 'plugin')
        self.assertFalse((real / 'plugin').exists())

    def test_source_symlink_is_rejected(self):
        source = self.source / 'scripts/strict_json.py'
        saved = self.base / 'borrowed.py'
        source.rename(saved)
        self.symlink(source, saved)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            builder.build_archive(self.base / 'runtime.zip')

    def test_development_oracle_cannot_be_remapped_to_readme(self):
        self.mapping['files']['README.md'] = 'tests/test_transition.py'
        self.change(self.mapping)
        with self.assertRaisesRegex(ValueError, 'Developer-only'):
            builder.build_directory(self.base / 'plugin')
        self.assertFalse((self.base / 'plugin').exists())

    def test_explicit_mapping_still_cannot_ship_lab_or_tests(self):
        for name in ('scripts/demo_app.py', 'tests/test_transition.py', 'evals/booking-task.md'):
            with self.subTest(name=name):
                original = dict(self.mapping['files'])
                self.mapping['files'][name] = name
                self.change(self.mapping)
                with self.assertRaisesRegex(ValueError, 'Developer-only'):
                    builder.prepare()
                self.mapping['files'] = original

    def test_path_escape_rejected_before_publication(self):
        self.mapping['files']['../outside'] = 'LICENSE'
        self.change(self.mapping)
        with self.assertRaisesRegex(ValueError, 'contained'):
            builder.build_archive(self.base / 'runtime.zip')
        self.assertFalse((self.base / 'runtime.zip').exists())

    def test_missing_operational_dependency_rejected(self):
        del self.mapping['files']['scripts/strict_json.py']
        self.change(self.mapping)
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            builder.prepare()

    def test_missing_referenced_skill_file_rejected(self):
        del self.mapping['files']['skills/oq-explore/references/human-journeys.md']
        self.change(self.mapping)
        with self.assertRaisesRegex(ValueError, 'Missing runtime link'):
            builder.prepare()

    def test_unreviewed_source_is_not_exported(self):
        inventory = self.source / 'package-files.json'
        data = json.loads(inventory.read_text(encoding='utf-8'))
        data['files'].remove('distribution/README.md')
        inventory.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'reviewed source inventory'):
            builder.prepare()

    def test_duplicate_mapping_json_is_rejected(self):
        path = self.source / 'runtime-files.json'
        path.write_text('{"format":1,"format":1,"files":{}}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            builder.prepare()

    def test_mapping_format_boolean_is_not_integer_version(self):
        self.mapping['format'] = True
        self.change(self.mapping)
        with self.assertRaisesRegex(ValueError, 'Invalid runtime'):
            builder.prepare()


if __name__ == '__main__':
    unittest.main()
