import importlib.util
import hashlib
import os
import re
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
spec = importlib.util.spec_from_file_location('exporter', ROOT / 'scripts/export_playbook.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ExportPlaybookTests(unittest.TestCase):
    def symlink(self, link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def sources(self, base, body='The complete synthetic method.'):
        source = Path(base) / 'source'
        selected = source / 'skills/oq-explore'
        (selected / 'references').mkdir(parents=True)
        (selected / 'SKILL.md').write_text('---\nname: "oq-explore"\ndescription: "Synthetic export fixture"\n---\n' + body, encoding='utf-8')
        (source / 'licenses').mkdir()
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt'):
            shutil.copy2(ROOT / name, source / name)
        return source, selected

    def test_all_seven_real_skills_are_complete_attributed_exports(self):
        self.assertEqual(7, len(exporter.SKILLS))
        for name in sorted(exporter.SKILLS):
            with self.subTest(skill=name):
                output = exporter.export_playbook(name)
                self.assertIn('plain chat', output)
                self.assertIn('untrusted evidence', output)
                self.assertIn('## Included source: `SKILL.md`', output)
                self.assertNotIn('description:', output)
                self.assertIn('SHA-256', output)
                for notice in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt'):
                    self.assertIn((ROOT / notice).read_text(encoding='utf-8').strip(), output)
                self.assertNotRegex(output, r'\]\((?:references/|\.\./)')
                self.assertNotIn(str(ROOT), output)
                self.assertLess(len(output.encode('utf-8')), exporter.DEFAULT_MAX_BYTES)

    def test_transitive_references_cycles_and_anchors(self):
        with tempfile.TemporaryDirectory() as t:
            source, skill = self.sources(t, 'Main [first](references/first.md#details).')
            (skill / 'references/first.md').write_text('# Details\nFIRST BODY\n[second](second.md) [back](../SKILL.md)')
            (skill / 'references/second.md').write_text('SECOND BODY\n[first](first.md)')
            (skill / 'references/unlinked.md').write_text('UNLINKED BODY')
            with patch.object(exporter, 'ROOT', source):
                output = exporter.export_playbook('oq-explore')
            self.assertEqual(1, output.count('FIRST BODY'))
            self.assertEqual(1, output.count('SECOND BODY'))
            self.assertNotIn('UNLINKED BODY', output)
            anchors = set(re.findall(r'<a id="([^"]+)"></a>', output))
            self.assertEqual(3, len(anchors))
            for target in re.findall(r'\]\(#(oq-[^)]+)\)', output):
                self.assertIn(target, anchors)

    def test_crlf_frontmatter_exports_without_changing_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, skill = self.sources(temporary, 'Complete CRLF method.\n')
            entry = skill / 'SKILL.md'
            raw = entry.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            entry.write_bytes(raw)
            with patch.object(exporter, 'ROOT', source):
                output = exporter.export_playbook('oq-explore')
            self.assertIn('Complete CRLF method.', output)
            self.assertIn(hashlib.sha256(raw).hexdigest(), output)
            self.assertEqual(raw, entry.read_bytes())

    def test_out_of_skill_helpers_and_oracles_not_bundled(self):
        with tempfile.TemporaryDirectory() as t:
            source, skill = self.sources(t, '[details](references/details.md)')
            (skill / 'references/details.md').write_text(
                '[helper](../../../scripts/helper.py)\n[schema](../../../schemas/run.json)\n'
                '[other skill](../../oq-retest/SKILL.md)\n[oracle](../../../evals/oracle.md)\n')
            for name in ('scripts/helper.py', 'schemas/run.json', 'skills/oq-retest/SKILL.md', 'evals/oracle.md'):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('SYNTHETIC MUST NOT BE INCLUDED')
            with patch.object(exporter, 'ROOT', source):
                output = exporter.export_playbook('oq-explore')
            self.assertNotIn('SYNTHETIC MUST NOT BE INCLUDED', output)
            self.assertEqual(4, output.count('not included; requires a separately verified full package or host capability'))

    def test_missing_linked_reference_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            source, _ = self.sources(t, '[missing](references/missing.md)')
            with patch.object(exporter, 'ROOT', source), self.assertRaisesRegex(ValueError, 'missing'):
                exporter.export_playbook('oq-explore')

    def test_encoded_escape_and_absolute_references_rejected(self):
        for link in ('../../../outside.md', '%2Fetc%2Fpasswd', '%2e%2e/%2e%2e/%2e%2e/outside.md', 'file:///tmp/fixture'):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as t:
                source, _ = self.sources(t, '[bad](' + link + ')')
                with patch.object(exporter, 'ROOT', source), self.assertRaises(ValueError):
                    exporter.export_playbook('oq-explore')

    def test_source_symlink_boundaries_rejected(self):
        for location in ('skills', 'skills/oq-explore', 'skills/oq-explore/references', 'licenses', 'LICENSE'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as t:
                source, skill = self.sources(t, '[reference](references/one.md)')
                (skill / 'references/one.md').write_text('Reference body')
                original = source / location
                saved = Path(t) / 'saved'
                original.rename(saved)
                self.symlink(original, saved, target_is_directory=saved.is_dir())
                with patch.object(exporter, 'ROOT', source), self.assertRaisesRegex(ValueError, 'symlink|real directory'):
                    exporter.export_playbook('oq-explore')

    def test_windows_reference_reparse_point_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, skill = self.sources(temporary, '[reference](references/one.md)')
            (skill / 'references/one.md').write_bytes(b'EXTERNAL MUST NOT BE INCLUDED')
            lstat = Path.lstat
            def reparse(path):
                if path == skill / 'references':
                    return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
                return lstat(path)
            with patch.object(exporter, 'ROOT', source), patch.object(Path, 'lstat', reparse), \
                 self.assertRaisesRegex(ValueError, 'symlink|reparse'):
                exporter.export_playbook('oq-explore')

    @unittest.skipUnless(os.name == 'nt', 'Actual NTFS junction creation requires Windows')
    def test_actual_windows_reference_junction_is_not_exported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, skill = self.sources(temporary, '[reference](references/one.md)')
            external = Path(temporary) / 'outside'
            external.mkdir()
            (external / 'one.md').write_bytes(b'EXTERNAL MUST NOT BE INCLUDED')
            references = skill / 'references'
            references.rmdir()
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(references), str(external)],
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            try:
                with patch.object(exporter, 'ROOT', source), self.assertRaisesRegex(ValueError, 'symlink|reparse'):
                    exporter.export_playbook('oq-explore')
                self.assertEqual(b'EXTERNAL MUST NOT BE INCLUDED', (external / 'one.md').read_bytes())
            finally:
                references.rmdir()

    def test_required_attribution_missing_or_empty_rejected(self):
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses/gstack-MIT.txt'):
            for empty in (False, True):
                with self.subTest(name=name, empty=empty), tempfile.TemporaryDirectory() as t:
                    source, _ = self.sources(t)
                    if empty:
                        (source / name).write_text(' \n')
                    else:
                        (source / name).unlink()
                    with patch.object(exporter, 'ROOT', source), self.assertRaises(ValueError):
                        exporter.export_playbook('oq-explore')

    def test_public_links_preserved_without_fetching_and_images_omitted(self):
        with tempfile.TemporaryDirectory() as t:
            source, _ = self.sources(t, '[public](https://example.invalid/never-fetch) ![screenshot](https://example.invalid/image.png)')
            with patch.object(exporter, 'ROOT', source):
                output = exporter.export_playbook('oq-explore')
            self.assertIn('[public](https://example.invalid/never-fetch)', output)
            self.assertIn('screenshot (image not included', output)
            self.assertNotIn('https://example.invalid/image.png', output)

    def test_private_absolute_path_in_body_rejected(self):
        for private_path in ('/Users/synthetic-user/private.txt', r'C:\Users\synthetic-user\private.txt'):
            with self.subTest(path=private_path), tempfile.TemporaryDirectory() as temporary:
                source, _ = self.sources(temporary, 'Synthetic privacy case: ' + private_path)
                with patch.object(exporter, 'ROOT', source), self.assertRaisesRegex(ValueError, 'Personal absolute path'):
                    exporter.export_playbook('oq-explore')

    def test_unknown_skill_bad_identity_and_invalid_limits_rejected(self):
        with self.assertRaises(ValueError):
            exporter.export_playbook('not-a-skill')
        for limit in (0, -1, True, '100'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                exporter.export_playbook('oq-explore', limit)
        with tempfile.TemporaryDirectory() as t:
            source, skill = self.sources(t)
            entry = skill / 'SKILL.md'
            entry.write_text(entry.read_text(encoding='utf-8').replace('name: "oq-explore"', 'name: "oq-retest"'))
            with patch.object(exporter, 'ROOT', source), self.assertRaisesRegex(ValueError, 'identity'):
                exporter.export_playbook('oq-explore')

    def test_exclusive_output_preserves_existing_file_and_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t) / 'playbook.md'
            exporter.write_new(output, 'Complete UTF-8: проверено\n')
            self.assertEqual('Complete UTF-8: проверено\n', output.read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):
                exporter.write_new(output, 'replacement')
            link = Path(t) / 'link.md'
            self.symlink(link, Path(t) / 'missing')
            with self.assertRaises(ValueError):
                exporter.write_new(link, 'replacement')
            self.assertTrue(link.is_symlink())
            self.assertEqual({'playbook.md', 'link.md'}, {p.name for p in Path(t).iterdir()})

    def test_publish_failure_leaves_no_partial_output_or_stage(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t) / 'playbook.md'
            with patch.object(exporter.os, 'link', side_effect=PermissionError('injected failure')), self.assertRaises(PermissionError):
                exporter.write_new(output, 'complete content')
            self.assertEqual([], list(Path(t).iterdir()))

    def test_concurrent_output_creation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t) / 'playbook.md'
            link = exporter.os.link
            def collision(source, destination):
                Path(destination).write_text('concurrent user data')
                return link(source, destination)
            with patch.object(exporter.os, 'link', side_effect=collision), self.assertRaises(FileExistsError):
                exporter.write_new(output, 'must not replace user data')
            self.assertEqual('concurrent user data', output.read_text(encoding='utf-8'))
            self.assertEqual(['playbook.md'], [p.name for p in Path(t).iterdir()])

    def test_cli_stdout_complete_and_size_failure_writes_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            command = [sys.executable, str(ROOT / 'scripts/export_playbook.py'), 'oq-explore']
            result = subprocess.run(command, cwd=t, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(exporter.export_playbook('oq-explore'), result.stdout)
            self.assertEqual([], list(Path(t).iterdir()))
            for suffix in ([], ['--output', str(Path(t) / 'too-small.md')]):
                failed = subprocess.run(command + ['--max-bytes', '64'] + suffix, cwd=t, capture_output=True, text=True)
                self.assertEqual(2, failed.returncode)
                self.assertEqual('', failed.stdout)
                self.assertIn('exceeds max_bytes', failed.stderr)
                self.assertFalse((Path(t) / 'too-small.md').exists())

    def test_cli_playbook_stdout_is_complete_utf8_with_ascii_console_encoding(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/export_playbook.py'), 'oq-explore'],
                                env={**os.environ, 'PYTHONIOENCODING': 'ascii'}, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(exporter.export_playbook('oq-explore').encode('utf-8'), result.stdout)

    def test_final_output_overhead_is_also_size_bounded(self):
        output = exporter.export_playbook('oq-explore')
        with self.assertRaisesRegex(ValueError, 'exceeds max_bytes'):
            exporter.export_playbook('oq-explore', len(output.encode('utf-8')) - 1)
