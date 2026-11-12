import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('release_builder', ROOT / 'scripts/build_release.py')
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / 'development'
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        self.root_patch = patch.object(release, 'ROOT', self.source)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def assert_clean_staging(self):
        self.assertEqual([], list(self.base.glob('.outcome-qa-release-*')))

    def test_versioned_archive_examples_match_bundle_version(self):
        version, _ = release.prepare()
        for name in ('distribution/INSTALL.md', 'docs/PUBLISHING.md'):
            with self.subTest(document=name):
                text = (self.source / name).read_text(encoding='utf-8')
                versions = re.findall(r'outcome-qa-(?:source-)?(\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)', text)
                # Strip a ZIP suffix consumed by the optional prerelease segment.
                self.assertTrue(versions, 'Expected a versioned bundle example')
                self.assertEqual({version}, {value.removesuffix('.zip') for value in versions})

    def test_prepare_has_exact_wrapper_locations_and_runtime_bytes(self):
        version, payloads = release.prepare()
        runtime = release.prepare_runtime(self.source)
        self.assertEqual(set(payloads), {'outcome-qa/' + name for name in runtime} |
                         {'README.md', '.agents/plugins/marketplace.json',
                          '.claude-plugin/marketplace.json', 'MANIFEST.json'})
        for name, data in runtime.items():
            self.assertEqual(data, payloads['outcome-qa/' + name])
            self.assertFalse(set(Path(name).parts) & release.DEV_PARTS)
        self.assertEqual((self.source / 'distribution/INSTALL.md').read_bytes(), payloads['README.md'])
        codex = json.loads(payloads['.agents/plugins/marketplace.json'])
        claude = json.loads(payloads['.claude-plugin/marketplace.json'])
        self.assertEqual('outcome-qa-releases', codex['name'])
        self.assertEqual({'source': 'local', 'path': './outcome-qa'}, codex['plugins'][0]['source'])
        self.assertEqual('./outcome-qa', claude['plugins'][0]['source'])
        self.assertEqual({'name': 'c33leron'}, claude['owner'])
        self.assertEqual(version, json.loads(payloads['outcome-qa/plugin.json'])['version'])

    def test_manifest_hashes_every_payload_except_itself_without_host_paths(self):
        version, payloads = release.prepare()
        manifest = json.loads(payloads['MANIFEST.json'])
        self.assertEqual({'format', 'version', 'files'}, set(manifest))
        self.assertEqual(1, manifest['format'])
        self.assertEqual(version, manifest['version'])
        self.assertEqual(set(payloads) - {'MANIFEST.json'}, set(manifest['files']))
        for name, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256(payloads[name]).hexdigest(), expected)
            self.assertNotIn('\\', name)
            self.assertFalse(name.startswith('/'))
        self.assertNotIn(str(self.base).encode(), payloads['MANIFEST.json'])
        self.assertNotIn(b'/Users/', payloads['MANIFEST.json'])

    def test_directory_and_zip_are_the_same_verified_bundle(self):
        version, payloads = release.prepare()
        directory = self.base / ('outcome-qa-' + version)
        archive_path = self.base / 'release.zip'
        direct = release.build_directory(directory)
        zipped = release.build_archive(archive_path)
        self.assertEqual(len(payloads), direct['files'])
        self.assertEqual(len(payloads), zipped['files'])
        prefix = 'outcome-qa-' + version + '/'
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual({prefix + name for name in payloads}, set(archive.namelist()))
            for name, data in payloads.items():
                self.assertEqual(data, directory.joinpath(*name.split('/')).read_bytes())
                self.assertEqual(data, archive.read(prefix + name))
            manifest = json.loads(archive.read(prefix + 'MANIFEST.json'))
            for name, expected in manifest['files'].items():
                self.assertEqual(expected, hashlib.sha256(archive.read(prefix + name)).hexdigest())
        self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), zipped['sha256'])
        self.assert_clean_staging()

    def test_existing_zip_and_directory_are_not_overwritten(self):
        archive = self.base / 'release.zip'
        archive.write_bytes(b'USER ZIP')
        directory = self.base / 'bundle'
        directory.mkdir()
        (directory / 'notes').write_bytes(b'USER NOTES')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            release.build_archive(archive)
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            release.build_directory(directory)
        self.assertEqual(b'USER ZIP', archive.read_bytes())
        self.assertEqual(b'USER NOTES', (directory / 'notes').read_bytes())

    def test_output_inside_source_and_normalized_alias_rejected(self):
        for output in [self.source / 'release.zip', self.source / 'missing/../bundle']:
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'outside'):
                release.build_archive(output)
        self.assertFalse((self.source / 'release.zip').exists())
        self.assertFalse((self.source / 'missing').exists())

    def test_output_symlink_ancestors_are_rejected(self):
        actual = self.base / 'actual'
        actual.mkdir()
        alias = self.base / 'alias'
        alias.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            release.build_archive(alias / 'release.zip')
        self.assertEqual([], list(actual.iterdir()))

    def test_missing_or_empty_install_readme_is_rejected_before_output(self):
        path = self.source / 'distribution/INSTALL.md'
        path.unlink()
        with self.assertRaises(ValueError):
            release.build_archive(self.base / 'missing.zip')
        path.write_text(' \n')
        with self.assertRaisesRegex(ValueError, 'Empty'):
            release.build_archive(self.base / 'empty.zip')
        self.assertFalse((self.base / 'missing.zip').exists())
        self.assertFalse((self.base / 'empty.zip').exists())

    def test_wrapper_symlink_is_rejected_without_reading_external_bytes(self):
        path = self.source / 'distribution/codex-marketplace.json'
        external = self.base / 'external.json'
        external.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(external)
        with self.assertRaises(ValueError):
            release.build_archive(self.base / 'release.zip')
        self.assertFalse((self.base / 'release.zip').exists())

    def test_remote_or_traversing_marketplace_sources_are_rejected(self):
        codex = self.source / 'distribution/codex-marketplace.json'
        claude = self.source / 'distribution/claude-marketplace.json'
        original = codex.read_bytes()
        for source in ['../outside', '/absolute', 'https://example.test/plugin']:
            data = json.loads(original)
            data['plugins'][0]['source']['path'] = source
            codex.write_text(json.dumps(data))
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'Codex marketplace'):
                release.prepare()
        codex.write_bytes(original)
        data = json.loads(claude.read_bytes())
        data['plugins'][0]['source'] = '../outside'
        claude.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Claude marketplace'):
            release.prepare()

    def test_duplicate_descriptor_keys_and_unexpected_credentials_are_rejected(self):
        path = self.source / 'distribution/codex-marketplace.json'
        original = path.read_text()
        path.write_text('{"name":"ambiguous",' + original[1:])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            release.prepare()
        data = json.loads(original)
        data['credentials'] = 'synthetic-do-not-ship'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Codex marketplace'):
            release.prepare()

    def test_development_or_unsafe_runtime_names_are_rejected(self):
        runtime = release.prepare_runtime(self.source)
        for name in ['../outside', '/absolute', 'C:\\secret', 'tests/test_extra.py',
                     'evals/answer.json', '.github/workflows/check.yml', 'shared/voice.md',
                     'scripts/build_release.py', 'outcome//bad.md']:
            with self.subTest(name=name), patch.object(release, 'prepare_runtime', return_value={**runtime, name: b'no'}):
                with self.assertRaises(ValueError):
                    release.build_archive(self.base / 'release.zip')
        self.assertFalse((self.base / 'release.zip').exists())

    def test_unsafe_version_cannot_control_zip_paths(self):
        runtime = release.prepare_runtime(self.source)
        for version in ['../../escape', '1/2/3', '1.0.0\n', True, None]:
            payloads = {**runtime, 'plugin.json': json.dumps({'name': 'outcome-qa', 'version': version}).encode()}
            with self.subTest(version=version), patch.object(release, 'prepare_runtime', return_value=payloads):
                with self.assertRaisesRegex(ValueError, 'semantic version'):
                    release.prepare()

    def test_directory_stage_write_failure_never_exposes_final_root(self):
        output = self.base / 'bundle'
        write = release.os.write
        calls = []
        def fail(fd, data):
            if not calls:
                calls.append(True)
                return write(fd, data[:max(1, len(data)//2)])
            raise OSError('injected write failure')
        with patch.object(release.os, 'write', fail), self.assertRaisesRegex(OSError, 'injected'):
            release.build_directory(output)
        self.assertFalse(output.exists())
        self.assert_clean_staging()

    def test_archive_write_failure_leaves_neither_final_nor_stage(self):
        output = self.base / 'release.zip'
        write = zipfile.ZipFile.writestr
        def fail(archive, *args, **kwargs):
            write(archive, *args, **kwargs)
            raise OSError('injected ZIP write failure')
        with patch.object(zipfile.ZipFile, 'writestr', fail), self.assertRaisesRegex(OSError, 'injected'):
            release.build_archive(output)
        self.assertFalse(output.exists())
        self.assert_clean_staging()

    def test_archive_readback_failure_never_publishes(self):
        output = self.base / 'release.zip'
        with patch.object(zipfile.ZipFile, 'read', return_value=b'corrupted'), self.assertRaisesRegex(ValueError, 'content mismatch'):
            release.build_archive(output)
        self.assertFalse(output.exists())
        self.assert_clean_staging()

    def test_final_zip_collision_preserves_user_bytes(self):
        output = self.base / 'release.zip'
        link = release.os.link
        def race(source, target, **kwargs):
            Path(target).write_bytes(b'CONCURRENT USER ZIP\x00')
            return link(source, target, **kwargs)
        with patch.object(release.os, 'link', race), self.assertRaises(FileExistsError):
            release.build_archive(output)
        self.assertEqual(b'CONCURRENT USER ZIP\x00', output.read_bytes())
        self.assert_clean_staging()

    def test_concurrent_directory_root_is_not_merged(self):
        output = self.base / 'bundle'
        mkdir = Path.mkdir
        def race(path, *args, **kwargs):
            if path == output and not path.exists():
                mkdir(path)
                (path / 'user-note').write_bytes(b'USER DATA')
            return mkdir(path, *args, **kwargs)
        with patch.object(Path, 'mkdir', race), self.assertRaises(FileExistsError):
            release.build_directory(output)
        self.assertEqual({'user-note'}, {p.name for p in output.iterdir()})
        self.assertEqual(b'USER DATA', (output / 'user-note').read_bytes())
        self.assert_clean_staging()

    def test_concurrent_output_file_is_preserved_and_owned_files_rolled_back(self):
        output = self.base / 'bundle'
        link = release.os.link
        arrived = []
        def race(source, target, **kwargs):
            if not arrived:
                Path(target).write_bytes(b'CONCURRENT USER FILE')
                arrived.append(Path(target))
            return link(source, target, **kwargs)
        with patch.object(release.os, 'link', race), self.assertRaisesRegex(OSError, 'incomplete'):
            release.build_directory(output)
        self.assertEqual(b'CONCURRENT USER FILE', arrived[0].read_bytes())
        self.assertEqual({arrived[0]}, {p for p in output.rglob('*') if p.is_file()})
        self.assert_clean_staging()

    def test_failure_after_successful_link_cleans_unchanged_owned_output(self):
        output = self.base / 'bundle'
        link = release.os.link
        def fail_after(source, target, **kwargs):
            link(source, target, **kwargs)
            raise OSError('injected post-link failure')
        with patch.object(release.os, 'link', fail_after), self.assertRaisesRegex(OSError, 'post-link'):
            release.build_directory(output)
        self.assertFalse(output.exists())
        self.assert_clean_staging()

    def test_user_edit_to_published_file_is_retained_on_failure(self):
        output = self.base / 'bundle'
        link = release.os.link
        edited = []
        def edit_after(source, target, **kwargs):
            link(source, target, **kwargs)
            Path(target).write_bytes(b'USER EDIT AFTER LINK')
            edited.append(Path(target))
        with patch.object(release.os, 'link', edit_after), self.assertRaisesRegex(OSError, 'incomplete'):
            release.build_directory(output)
        self.assertEqual(b'USER EDIT AFTER LINK', edited[0].read_bytes())
        staging = list(self.base.glob('.outcome-qa-release-stage-*'))
        self.assertEqual(1, len(staging))
        linked = staging[0] / edited[0].relative_to(output)
        self.assertEqual(b'USER EDIT AFTER LINK', linked.read_bytes())
        self.assertEqual(linked.stat().st_ino, edited[0].stat().st_ino)

    def test_unknown_file_added_to_bundle_is_not_silently_shipped_or_deleted(self):
        output = self.base / 'bundle'
        verify = release._verify_directory
        def add_unknown(directory, payloads):
            (directory / 'user-notes.txt').write_text('KEEP')
            return verify(directory, payloads)
        with patch.object(release, '_verify_directory', add_unknown), self.assertRaisesRegex(OSError, 'incomplete'):
            release.build_directory(output)
        self.assertEqual('KEEP', (output / 'user-notes.txt').read_text())
        self.assertEqual({'user-notes.txt'}, {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()})
        self.assert_clean_staging()

    def test_reparse_attribute_is_detected_without_symlink_file_type(self):
        path = Mock()
        path.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_file_attributes=0x400)
        self.assertTrue(release._is_link(path))
        path.lstat.return_value.st_file_attributes = 0
        self.assertFalse(release._is_link(path))
        path.lstat.return_value.st_mode = stat.S_IFLNK | 0o777
        self.assertTrue(release._is_link(path))

    def test_reparse_guards_cover_source_and_output_ancestors(self):
        is_link = release._is_link
        marked = self.source / 'distribution'
        with patch.object(release, '_is_link', side_effect=lambda path: path == marked or is_link(path)):
            with self.assertRaisesRegex(ValueError, 'Symlink bundle source'):
                release.prepare()
        output_parent = self.base / 'output'
        output_parent.mkdir()
        with patch.object(release, '_is_link', side_effect=lambda path: path == output_parent or is_link(path)):
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                release.build_archive(output_parent / 'release.zip')
        self.assertEqual([], list(output_parent.iterdir()))

    @unittest.skipUnless(os.name == 'nt', 'Actual NTFS junction check requires Windows')
    def test_actual_windows_junction_is_rejected(self):
        actual = self.base / 'real-target'
        actual.mkdir()
        junction = self.base / 'junction'
        result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(junction), str(actual)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.addCleanup(lambda: os.rmdir(junction) if junction.exists() else None)
        self.assertTrue(release._is_link(junction))
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            release.build_archive(junction / 'release.zip')
        self.assertFalse((actual / 'release.zip').exists())

    def test_permission_only_edit_survives_later_publication_failure(self):
        output = self.base / 'bundle'
        link = release.os.link
        protected = []
        modified_modes = []
        def fail_after_user_chmod(source, target, **kwargs):
            if protected:
                protected[0].chmod(0o400)
                modified_modes.append(stat.S_IMODE(protected[0].stat().st_mode))
                raise PermissionError('injected next-link failure')
            result = link(source, target, **kwargs)
            if Path(target) == output / 'README.md':
                protected.append(Path(target))
            return result
        try:
            with patch.object(release.os, 'link', fail_after_user_chmod), self.assertRaisesRegex(OSError, 'incomplete'):
                release.build_directory(output)
            self.assertEqual([output / 'README.md'], protected)
            self.assertEqual((self.source / 'distribution/INSTALL.md').read_bytes(), protected[0].read_bytes())
            self.assertEqual(modified_modes[0], stat.S_IMODE(protected[0].stat().st_mode))
            self.assertEqual(0, protected[0].stat().st_mode & 0o222)
            self.assert_clean_staging()
        finally:
            for path in protected:
                if path.exists():
                    path.chmod(0o600)  # Disposable fixture cleanup, not the builder.

    def test_readonly_shared_stage_is_retained_without_chmod_cleanup(self):
        output = self.base / 'bundle'
        link, chmod = release.os.link, release.os.chmod
        edited = []
        def read_only_after_link(source, target, **kwargs):
            result = link(source, target, **kwargs)
            chmod(target, 0o400)
            edited.append((Path(source), Path(target), stat.S_IMODE(Path(target).stat().st_mode)))
            return result
        try:
            with patch.object(release.os, 'link', read_only_after_link), patch.object(
                    release.os, 'chmod', side_effect=AssertionError('Builder must never chmod shared user inode')):
                with self.assertRaisesRegex(OSError, 'uncertain paths retained') as error:
                    release.build_directory(output)
            source, target, mode = edited[0]
            self.assertTrue(source.exists())
            self.assertTrue(target.exists())
            self.assertEqual(mode, stat.S_IMODE(source.stat().st_mode))
            self.assertEqual(mode, stat.S_IMODE(target.stat().st_mode))
            self.assertEqual(source.stat().st_ino, target.stat().st_ino)
            self.assertIn(str(output), str(error.exception))
            staging = list(self.base.glob('.outcome-qa-release-stage-*'))
            self.assertEqual(1, len(staging))
            self.assertIn(str(staging[0]), str(error.exception))
        finally:
            for source, target, _ in edited:
                if target.exists():
                    chmod(target, 0o600)  # Restore this test's owned fixture after assertions.

    def test_same_bytes_timestamp_edit_survives_later_failure(self):
        output = self.base / 'bundle'
        link = release.os.link
        protected, times = [], []
        def fail_after_touch(source, target, **kwargs):
            if protected:
                before = protected[0].stat()
                changed = before.st_mtime_ns + 1_000_000_000
                os.utime(protected[0], ns=(before.st_atime_ns, changed))
                times.append(protected[0].stat().st_mtime_ns)
                raise PermissionError('injected failure after metadata-only edit')
            result = link(source, target, **kwargs)
            if Path(target) == output / 'README.md':
                protected.append(Path(target))
            return result
        with patch.object(release.os, 'link', fail_after_touch), self.assertRaisesRegex(OSError, 'incomplete'):
            release.build_directory(output)
        self.assertEqual((self.source / 'distribution/INSTALL.md').read_bytes(), protected[0].read_bytes())
        self.assertEqual(times[0], protected[0].stat().st_mtime_ns)
        self.assert_clean_staging()

    def test_file_ownership_guard_includes_mtime_uid_and_gid(self):
        path = self.base / 'metadata.txt'
        payload = b'unchanged content'
        path.write_bytes(payload)
        info = path.stat()
        identity = release._identity(path)
        metadata = release._metadata(path)
        self.assertEqual((stat.S_IMODE(info.st_mode), info.st_mtime_ns,
                          getattr(info, 'st_uid', 0), getattr(info, 'st_gid', 0)), metadata)
        self.assertTrue(release._unchanged_file(path, identity, metadata, payload))
        for index in (1, 2, 3):
            different = list(metadata)
            different[index] += 1
            with self.subTest(index=index):
                self.assertFalse(release._unchanged_file(path, identity, tuple(different), payload))
