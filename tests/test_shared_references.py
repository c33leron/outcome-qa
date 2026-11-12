import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('shared_sync', ROOT / 'scripts/sync_shared.py')
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)


class SharedReferenceTests(unittest.TestCase):
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
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'shared').mkdir()
        self.source = self.root / 'shared/voice.md'
        self.source.write_text('# Voice\nClear synthetic prose.\n', encoding='utf-8')
        self.destination = 'skills/oq-explore/references/_shared/voice.md'
        self.second = 'skills/oq-test-design/references/_shared/voice.md'
        self.mapping = {'format': 1, 'files': {self.destination: 'shared/voice.md', self.second: 'shared/voice.md'}}
        self.write_mapping()

    def write_mapping(self):
        (self.root / 'shared-references.json').write_text(json.dumps(self.mapping))

    def test_default_check_does_not_write_and_reports_missing(self):
        result = shared.sync(self.root)
        self.assertFalse(result['valid'])
        self.assertFalse(result['written'])
        self.assertIn('Coordinate other writers', result['limit'])
        self.assertIn('stale open handles after that point are outside this guarantee', result['limit'])
        self.assertEqual(2, len(shared.check(self.root)))
        self.assertFalse((self.root / 'skills').exists())

    def test_write_has_exact_generated_header_body_and_idempotence(self):
        result = shared.sync(self.root, write=True)
        self.assertTrue(result['valid'])
        for destination in self.mapping['files']:
            self.assertEqual(shared.render('shared/voice.md', self.source.read_bytes()),
                             (self.root / destination).read_bytes())
        self.assertEqual([], shared.check(self.root))
        self.assertEqual([], shared.sync(self.root, write=True)['changed'])

    def test_manifest_keys_use_posix_separators_even_for_windows_relative_paths(self):
        shared.sync(self.root, write=True)
        relative_to = type(self.root).relative_to

        def windows_relative(path, *args):
            return PureWindowsPath(relative_to(path, *args).as_posix())

        with patch.object(type(self.root), 'relative_to', windows_relative):
            self.assertEqual([], shared.check(self.root))

    def test_canonical_edit_is_stale_then_regenerated(self):
        shared.sync(self.root, write=True)
        (self.root / self.destination).chmod(0o640)
        expected_mode = (self.root / self.destination).stat().st_mode & 0o777
        self.source.write_text('# Voice\nUpdated logical rule.\n')
        self.assertEqual(2, len(shared.check(self.root)))
        result = shared.sync(self.root, write=True)
        self.assertTrue(result['valid'])
        self.assertEqual(expected_mode, (self.root / self.destination).stat().st_mode & 0o777)
        self.assertIn(b'Updated logical rule.', (self.root / self.destination).read_bytes())

    def test_manual_body_or_header_edit_is_preserved(self):
        for payload in [b'personal notes', b'<!-- outcome-qa:generated source=shared/voice.md sha256=' + b'0'*64 + b' -->\nchanged']:
            with self.subTest(payload=payload):
                shared.sync(self.root, write=True)
                path = self.root / self.destination
                path.write_bytes(payload)
                self.source.write_text('new canon')
                other = (self.root / self.second).read_bytes()
                with self.assertRaisesRegex(ValueError, 'manually changed'):
                    shared.sync(self.root, write=True)
                self.assertEqual(payload, path.read_bytes())
                self.assertEqual(other, (self.root / self.second).read_bytes())
                path.write_bytes(shared.render('shared/voice.md', self.source.read_bytes()))

    def test_all_preflight_happens_before_any_write(self):
        path = self.root / self.second
        path.parent.mkdir(parents=True)
        path.write_text('keep user material')
        with self.assertRaises(ValueError):
            shared.sync(self.root, write=True)
        self.assertFalse((self.root / self.destination).exists())
        self.assertEqual('keep user material', path.read_text(encoding='utf-8'))

    def test_unknown_generated_entry_is_not_removed(self):
        directory = (self.root / self.destination).parent
        directory.mkdir(parents=True)
        unknown = directory / 'user-notes.md'
        unknown.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'Unknown generated'):
            shared.sync(self.root, write=True)
        self.assertEqual('keep', unknown.read_text(encoding='utf-8'))
        self.assertFalse((self.root / self.destination).exists())

    def test_invalid_mapping_rejected(self):
        for destination, source in [('../outside.md', 'shared/voice.md'),
             ('skills/oq-explore/references/_shared/../../escape.md', 'shared/voice.md'),
             ('skills/not-ours/references/_shared/voice.md', 'shared/voice.md'),
             (self.destination, '../voice.md'), (self.destination, 'shared/trust-boundary.md')]:
            with self.subTest(destination=destination, source=source):
                self.mapping['files'] = {destination: source}
                self.write_mapping()
                with self.assertRaises(ValueError):
                    shared.sync(self.root, write=True)
        self.assertFalse((self.root / 'skills').exists())

    def test_duplicate_mapping_keys_and_bool_format_rejected(self):
        spec = self.root / 'shared-references.json'
        spec.write_text('{"format":1,"files":{},"files":{}}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            shared.sync(self.root, write=True)
        self.mapping['format'] = True
        self.write_mapping()
        with self.assertRaises(ValueError):
            shared.sync(self.root, write=True)

    def test_missing_or_empty_canon_rejected(self):
        self.source.write_bytes(b' \n')
        with self.assertRaisesRegex(ValueError, 'empty'):
            shared.sync(self.root, write=True)
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            shared.sync(self.root, write=True)
        self.assertFalse((self.root / 'skills').exists())

    def test_source_and_destination_symlinks_rejected(self):
        original = self.source.read_bytes()
        saved = self.root / 'original.md'
        saved.write_bytes(original)
        self.source.unlink()
        self.symlink(self.source, saved)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            shared.sync(self.root, write=True)
        self.source.unlink()
        self.source.write_bytes(original)
        directory = self.root / 'skills/oq-explore'
        directory.parent.mkdir()
        self.symlink(directory, self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            shared.sync(self.root, write=True)

    def test_new_destination_race_does_not_overwrite(self):
        link = shared.os.link
        def collision(source, destination):
            Path(destination).write_bytes(b'CONCURRENT USER DATA\x00')
            return link(source, destination)
        with patch.object(shared.os, 'link', collision), self.assertRaises(FileExistsError):
            shared.sync(self.root, write=True)
        self.assertEqual(b'CONCURRENT USER DATA\x00', (self.root / self.destination).read_bytes())
        self.assertEqual([], list(self.root.rglob('.outcome-shared-*')))

    def test_existing_destination_change_before_publication_is_preserved(self):
        shared.sync(self.root, write=True)
        self.source.write_text('new canon')
        check = shared._check_snapshot
        calls = []
        def edited(root, relative, snapshot):
            calls.append(relative)
            if len(calls) == 2:
                (root / relative).write_text('concurrent notes')
            return check(root, relative, snapshot)
        with patch.object(shared, '_check_snapshot', edited), self.assertRaisesRegex(ValueError, 'changed during'):
            shared.sync(self.root, write=True)
        self.assertEqual('concurrent notes', (self.root / self.destination).read_text(encoding='utf-8'))
        self.assertEqual([], list(self.root.rglob('.outcome-shared-*')))

    def test_generated_parent_file_and_nonregular_canon_rejected(self):
        parent = self.root / 'skills/oq-explore/references/_shared'
        parent.parent.mkdir(parents=True)
        parent.write_text('keep')
        with self.assertRaises((ValueError, OSError)):
            shared.sync(self.root, write=True)
        self.assertEqual('keep', parent.read_text(encoding='utf-8'))

    def test_final_move_race_restores_concurrent_user_bytes(self):
        shared.sync(self.root, write=True)
        path = self.root / self.destination
        self.source.write_text('new canon')
        rename = shared.os.rename
        def race(source, destination):
            if Path(source) == path:
                path.write_bytes(b'FINAL CONCURRENT SHARED EDIT\x00')
            return rename(source, destination)
        with patch.object(shared.os, 'rename', race), self.assertRaisesRegex(ValueError, 'final move'):
            shared.sync(self.root, write=True)
        self.assertEqual(b'FINAL CONCURRENT SHARED EDIT\x00', path.read_bytes())
        self.assertEqual([], list(self.root.rglob('.outcome-shared-*')))

    def test_final_publish_race_preserves_current_and_original(self):
        shared.sync(self.root, write=True)
        path = self.root / self.destination
        original = path.read_bytes()
        self.source.write_text('new canon')
        link = shared.os.link
        injected = []
        def race(source, destination, **kwargs):
            if Path(source).name != 'previous' and not injected:
                injected.append(True)
                Path(destination).write_bytes(b'FINAL USER SHARED FILE')
            return link(source, destination, **kwargs)
        with patch.object(shared.os, 'link', race), self.assertRaisesRegex(OSError, 'recovery entry retained') as error:
            shared.sync(self.root, write=True)
        self.assertEqual(b'FINAL USER SHARED FILE', path.read_bytes())
        recovery = list(path.parent.glob('.outcome-shared-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(original, recovery[0].read_bytes())
        self.assertIn(str(recovery[0]), str(error.exception))

    def test_publish_failure_restores_shared_original_without_leftovers(self):
        shared.sync(self.root, write=True)
        path = self.root / self.destination
        original = path.read_bytes()
        path.chmod(0o640)
        expected_mode = path.stat().st_mode & 0o777
        self.source.write_text('new canon')
        link = shared.os.link
        def fail(source, destination, **kwargs):
            if Path(source).name != 'previous':
                raise PermissionError('injected shared publication failure')
            return link(source, destination, **kwargs)
        with patch.object(shared.os, 'link', fail), self.assertRaisesRegex(PermissionError, 'injected'):
            shared.sync(self.root, write=True)
        self.assertEqual(original, path.read_bytes())
        self.assertEqual(expected_mode, path.stat().st_mode & 0o777)
        self.assertEqual([], list(self.root.rglob('.outcome-shared-*')))

    def test_mismatched_shared_preimage_and_new_arrival_are_both_retained(self):
        shared.sync(self.root, write=True)
        path = self.root / self.destination
        self.source.write_text('new canon')
        rename = shared.os.rename
        def race(source, destination):
            if Path(source) == path:
                path.write_bytes(b'changed before quarantine')
                result = rename(source, destination)
                path.write_bytes(b'new arrival')
                return result
            return rename(source, destination)
        with patch.object(shared.os, 'rename', race), self.assertRaisesRegex(OSError, 'recovery entry retained'):
            shared.sync(self.root, write=True)
        self.assertEqual(b'new arrival', path.read_bytes())
        recovery = list(path.parent.glob('.outcome-shared-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(b'changed before quarantine', recovery[0].read_bytes())

    def test_shared_old_open_handle_write_before_commit_check_is_retained(self):
        shared.sync(self.root, write=True)
        path = self.root / self.destination
        original = path.read_bytes()
        self.source.write_text('new canon')
        link = shared.os.link
        with path.open('r+b') as old_handle:
            def edit_previous(source, destination, **kwargs):
                result = link(source, destination, **kwargs)
                if Path(source).name != 'previous':
                    old_handle.seek(0)
                    old_handle.write(b'concurrent old-handle edit')
                    old_handle.truncate()
                    old_handle.flush()
                return result
            with patch.object(shared.os, 'link', edit_previous), self.assertRaises(OSError) as error:
                shared.sync(self.root, write=True)
        if getattr(error.exception, 'winerror', None) == 32:
            self.assertEqual(original, path.read_bytes())
            self.assertEqual([], list(self.root.rglob('.outcome-shared-*')))
            return
        self.assertIn('recovery entry retained', str(error.exception))
        self.assertEqual(shared.render('shared/voice.md', self.source.read_bytes()), path.read_bytes())
        recovery = list(path.parent.glob('.outcome-shared-txn-*/previous'))
        self.assertEqual(1, len(recovery))
        self.assertEqual(b'concurrent old-handle edit', recovery[0].read_bytes())
