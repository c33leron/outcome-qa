"""Behavioral controls for the report validator, not model/product benchmarks."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "qa_result.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("qa_result", SCRIPT)
qa_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa_result)


class ReportTests(unittest.TestCase):
    def symlink(self, link, target, *, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symbolic-link privilege')
            raise

    def test_identifier_schema_and_runtime_parity(self):
        from strict_json import identifier, IDENTIFIER_PATTERN
        schema = json.loads((SCRIPT.parent.parent / 'schemas/run.schema.json').read_text(encoding='utf-8'))
        pattern = schema['$defs']['identifier']['pattern']
        self.assertEqual(IDENTIFIER_PATTERN, pattern)
        transition = json.loads((SCRIPT.parent.parent / 'schemas/transition.schema.json').read_text(encoding='utf-8'))
        for op in transition['properties']['rules']['items']['oneOf']:
            self.assertEqual(pattern, op['properties']['id']['pattern'])
        for value, allowed in [('', False), ('   ', False), ('x\n', False), ('x\x85', False),
             ('ok\u200bhidden', False), ('x\ue000', False), ('x\u2028', False), ('x\ud800', False),
             ('\U000e0020', False), ('Проверка-1', True), ('C1', True), ('x\u0378', True)]:
            with self.subTest(value=repr(value)):
                self.assertEqual(allowed, identifier(value))
                self.assertEqual(allowed, re.search(pattern, value) is not None)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "artifacts").mkdir()
        self.artifact = self.root / "artifacts" / "readback.json"
        self.artifact.write_text('{"item_count":1}\n', encoding="utf-8")
        self.report = {
            "version": 1,
            "run_id": "synthetic-run-1",
            "target": {"environment": "local fixture", "build": "fixture-v1", "actor": "synthetic-member"},
            "scope": {"goal": "One submission creates one item", "basis": "Fixture requirement R1", "exclusions": []},
            "checks": [{"id": "C1", "expectation": "Exactly one item is saved", "basis": "R1", "status": "PASS", "observation": "Read-back returned one item", "evidence_refs": ["E1"], "reproducibility": "single_observation"}],
            "artifacts": [{"id": "E1", "path": "artifacts/readback.json", "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest()}],
            "cleanup": {"status": "not_needed", "notes": "Read-only synthetic fixture"},
        }

    def validate(self, report=None):
        return qa_result.validate_report(self.report if report is None else report, self.root)

    def assert_verdict(self, report, verdict, code):
        self.assertEqual(report["verdict"], verdict, report)
        self.assertEqual(report["exit_code"], code, report)

    def write_report(self, data=None):
        path = self.root / "run.json"
        path.write_text(json.dumps(self.report if data is None else data), encoding="utf-8")
        return path

    def test_complete_pass_is_read_only(self):
        before = copy.deepcopy(self.report)
        self.assert_verdict(self.validate(), "PASS", 0)
        self.assertEqual(self.report, before)
        self.assertEqual(self.artifact.read_text(encoding='utf-8'), '{"item_count":1}\n')
        self.assertEqual(len(list(self.root.rglob("*"))), 2)

    def test_failure_is_preserved(self):
        self.report["checks"][0]["status"] = "FAIL"
        self.report["checks"][0]["observation"] = "Two items were saved"
        result = self.validate()
        self.assert_verdict(result, "FAIL", 1)
        self.assertEqual(result["product_failures"], ["C1"])

    def test_missing_required_checks_are_gaps_not_pass(self):
        self.report['scope']['required_check_ids'] = ['C1', 'C2']
        result = self.validate()
        self.assert_verdict(result, 'INCOMPLETE', 2)
        self.assertTrue(any('C2' in gap for gap in result['gaps']))
        self.report['checks'][0]['status'] = 'FAIL'
        self.assert_verdict(self.validate(), 'FAIL_WITH_GAPS', 2)

    def test_full_required_inventory_can_pass(self):
        self.report['scope']['required_check_ids'] = ['C1']
        self.assert_verdict(self.validate(), 'PASS', 0)

    def test_no_inventory_warns_about_bounded_coverage(self):
        result = self.validate()
        self.assertTrue(any('declared checks only' in w for w in result['warnings']))

    def test_invalid_required_inventory_rejected(self):
        for value in ([], ['C1', 'C1'], ['C1\nforged'], True, [1]):
            self.report['scope']['required_check_ids'] = value
            self.assert_verdict(self.validate(), 'INVALID', 3)

    def test_control_characters_in_identifiers_rejected(self):
        for value in ('forged\nPASS', '\x1b[2J', 'run\x07title', 'rtl\u202ePASS'):
            for kind in ('run_id', 'check_id', 'artifact_id'):
                data = copy.deepcopy(self.report)
                if kind == 'run_id': data['run_id'] = value
                elif kind == 'check_id': data['checks'][0]['id'] = value
                else: data['artifacts'][0]['id'] = value
                self.assert_verdict(self.validate(data), 'INVALID', 3)

    def test_text_cli_does_not_emit_injected_controls(self):
        self.report['run_id'] = 'x\x1b[2J\x07'
        self.report['checks'][0]['id'] = 'C1\nwarnings: forged-clean'
        p = self.write_report()
        result = subprocess.run([sys.executable, str(SCRIPT), 'check', str(p)], capture_output=True)
        self.assertEqual(3, result.returncode)
        for control in (b'\x1b', b'\x07', b'\r', b'\nwarnings: forged-clean'):
            self.assertNotIn(control, result.stdout)

    def test_failure_and_blocker_are_not_a_complete_failure_or_pass(self):
        self.report["checks"][0]["status"] = "FAIL"
        self.report["checks"].append({"id": "C2", "expectation": "Other actor cannot access item", "basis": "R2", "status": "BLOCKED", "reason": "Second fixture account unavailable", "evidence_refs": []})
        result = self.validate()
        self.assert_verdict(result, "FAIL_WITH_GAPS", 2)
        self.assertEqual(result["product_failures"], ["C1"])
        self.assertEqual(result["counts"]["BLOCKED"], 1)

    def test_incomplete_statuses_never_pass(self):
        for status in ("BLOCKED", "INCONCLUSIVE", "NOT_RUN"):
            with self.subTest(status=status):
                report = copy.deepcopy(self.report)
                report["checks"][0] = {"id": "C1", "expectation": "One item", "basis": "R1", "status": status, "reason": "Relevant condition not reached", "evidence_refs": []}
                report["artifacts"] = []
                self.assert_verdict(self.validate(report), "INCOMPLETE", 2)

    def test_empty_checks_are_invalid(self):
        self.report["checks"] = []
        self.assert_verdict(self.validate(), "INVALID", 3)

    def test_missing_evidence_cannot_pass_or_fail(self):
        for status in ("PASS", "FAIL"):
            with self.subTest(status=status):
                self.report["checks"][0]["status"] = status
                self.report["checks"][0]["evidence_refs"] = []
                self.assert_verdict(self.validate(), "INVALID", 3)

    def test_observation_and_incomplete_reason_are_required(self):
        for status, field in (("PASS", "observation"), ("FAIL", "observation"), ("BLOCKED", "reason"), ("INCONCLUSIVE", "reason"), ("NOT_RUN", "reason")):
            with self.subTest(status=status):
                report = copy.deepcopy(self.report)
                report["checks"][0]["status"] = status
                report["checks"][0].pop(field, None)
                self.assert_verdict(self.validate(report), "INVALID", 3)

    def test_cleanup_gaps_never_pass(self):
        for status in ("pending", "failed"):
            with self.subTest(status=status):
                self.report["cleanup"]["status"] = status
                self.assert_verdict(self.validate(), "INCOMPLETE", 2)

    def test_product_failure_plus_failed_cleanup_keeps_both(self):
        self.report["checks"][0]["status"] = "FAIL"
        self.report["cleanup"]["status"] = "failed"
        result = self.validate()
        self.assert_verdict(result, "FAIL_WITH_GAPS", 2)
        self.assertEqual(result["product_failures"], ["C1"])
        self.assertTrue(any("Cleanup failed" in x for x in result["gaps"]))

    def test_superseded_result_is_incomplete(self):
        self.report["superseded_by"] = "synthetic-run-2"
        self.assert_verdict(self.validate(), "INCOMPLETE", 2)

    def test_unknown_build_warns_but_does_not_invalidate_observation(self):
        self.report["target"]["build"] = None
        result = self.validate()
        self.assert_verdict(result, "PASS", 0)
        self.assertTrue(any("attribution is unverified" in x for x in result["warnings"]))

    def test_tampered_artifact_is_invalid(self):
        self.artifact.write_text('{"item_count":2}\n')
        result = self.validate()
        self.assert_verdict(result, "INVALID", 3)
        self.assertTrue(any("SHA-256 mismatch" in x for x in result["issues"]))

    def test_missing_file_and_directory_artifacts_are_invalid(self):
        for path in ("artifacts/missing.json", "artifacts"):
            with self.subTest(path=path):
                self.report["artifacts"][0]["path"] = path
                self.assert_verdict(self.validate(), "INVALID", 3)

    def test_path_traversal_and_nonportable_paths_are_rejected_before_read(self):
        for path in ("../outside.txt", "/tmp/outside.txt", "a/../../outside.txt", "./artifacts/readback.json", "artifacts//readback.json", "C:/outside.txt", "C:outside.txt", "artifacts\\readback.json", "artifacts/", "", " "):
            with self.subTest(path=path):
                self.report["artifacts"][0]["path"] = path
                result = self.validate()
                self.assert_verdict(result, "INVALID", 3)

    def test_file_symlink_inside_and_outside_are_rejected(self):
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("synthetic outside data")
        self.addCleanup(outside.unlink, missing_ok=True)
        for name, target in (("inside-link", self.artifact), ("outside-link", outside)):
            with self.subTest(name=name):
                link = self.root / name
                self.symlink(link, target)
                self.report["artifacts"][0]["path"] = name
                result = self.validate()
                self.assert_verdict(result, "INVALID", 3)
                self.assertTrue(any("symlinks" in x for x in result["issues"]))

    def test_parent_directory_symlink_is_rejected(self):
        self.symlink(self.root / "linked-dir", self.root / "artifacts", target_is_directory=True)
        self.report["artifacts"][0]["path"] = "linked-dir/readback.json"
        self.assert_verdict(self.validate(), "INVALID", 3)

    def test_fifo_artifact_is_rejected_without_opening_it(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable")
        os.mkfifo(self.root / "pipe")
        self.report["artifacts"][0]["path"] = "pipe"
        self.assert_verdict(self.validate(), "INVALID", 3)

    def test_windows_reparse_directory_is_rejected_before_open(self):
        original_lstat = Path.lstat
        target = (self.root / "artifacts").resolve()

        def reparse_lstat(path):
            if path == target:
                return SimpleNamespace(st_mode=0o040755, st_file_attributes=1024)
            return original_lstat(path)

        with mock.patch.object(qa_result.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024, create=True), mock.patch.object(Path, "lstat", reparse_lstat):
            result = self.validate()
        self.assert_verdict(result, "INVALID", 3)
        self.assertTrue(any("reparse points" in x for x in result["issues"]))

    def test_fallback_open_also_verifies_file_identity(self):
        with mock.patch.object(qa_result.os, "supports_dir_fd", set()):
            self.assert_verdict(self.validate(), "PASS", 0)

    def test_file_replacement_before_open_is_rejected(self):
        original_open = qa_result.os.open
        replacement = self.root / "replacement.json"
        replacement.write_text('{"unrelated":"synthetic"}\n')
        resolved_artifact = self.artifact.resolve()

        def swapped_open(path, *args, **kwargs):
            if Path(path) == resolved_artifact:
                replacement.replace(self.artifact)
            return original_open(path, *args, **kwargs)

        with mock.patch.object(qa_result.os, "supports_dir_fd", set()), mock.patch.object(qa_result.os, "open", swapped_open):
            result = self.validate()
        self.assert_verdict(result, "INVALID", 3)
        self.assertTrue(any("changed during inspection" in x for x in result["issues"]))

    def test_uppercase_digest_is_accepted(self):
        self.report["artifacts"][0]["sha256"] = self.report["artifacts"][0]["sha256"].upper()
        self.assert_verdict(self.validate(), "PASS", 0)

    def test_assurance_explicitly_excludes_semantic_truth(self):
        self.report["checks"][0]["observation"] = "A made-up claim that this helper cannot assess"
        result = self.validate()
        self.assert_verdict(result, "PASS", 0)
        self.assertIn("does not independently verify product behavior", result["assurance"])

    def test_duplicates_and_unknown_refs_are_invalid(self):
        cases = []
        report = copy.deepcopy(self.report)
        report["checks"].append(copy.deepcopy(report["checks"][0]))
        cases.append(report)
        report = copy.deepcopy(self.report)
        report["artifacts"].append(copy.deepcopy(report["artifacts"][0]))
        cases.append(report)
        report = copy.deepcopy(self.report)
        report["checks"][0]["evidence_refs"] = ["E1", "E1"]
        cases.append(report)
        report = copy.deepcopy(self.report)
        report["checks"][0]["evidence_refs"] = ["E-missing"]
        cases.append(report)
        for report in cases:
            with self.subTest(report=report):
                self.assert_verdict(self.validate(report), "INVALID", 3)

    def test_versions_and_boolean_are_not_coerced(self):
        for version in (True, False, "1", 1.0, 0, 2, None, [], {}):
            with self.subTest(version=version):
                self.report["version"] = version
                self.assert_verdict(self.validate(), "INVALID", 3)

    def test_nonstring_statuses_do_not_crash(self):
        for status in (True, None, 1, [], {}):
            with self.subTest(status=status):
                self.report["checks"][0]["status"] = status
                self.assert_verdict(self.validate(), "INVALID", 3)

    def test_unknown_input_verdict_is_rejected_not_trusted(self):
        self.report["verdict"] = "PASS"
        self.assert_verdict(self.validate(), "INVALID", 3)

    def test_malformed_shapes_are_invalid_not_exceptions(self):
        for key in ("target", "scope", "checks", "artifacts", "cleanup"):
            for value in (None, True, 3, "not an object"):
                with self.subTest(key=key, value=value):
                    report = copy.deepcopy(self.report)
                    report[key] = value
                    self.assert_verdict(self.validate(report), "INVALID", 3)
        for value in (None, [], True, "report"):
            self.assert_verdict(qa_result.validate_report(value, self.root), "INVALID", 3)

    def test_every_required_field_is_enforced(self):
        locations = [((), set(self.report)), (("target",), set(self.report["target"])), (("scope",), set(self.report["scope"])), (("cleanup",), set(self.report["cleanup"])), (("checks", 0), {"id", "expectation", "basis", "status", "evidence_refs"}), (("artifacts", 0), {"id", "path", "sha256"})]
        for location, fields in locations:
            for field in fields:
                with self.subTest(location=location, field=field):
                    report = copy.deepcopy(self.report)
                    target = report
                    for part in location:
                        target = target[part]
                    del target[field]
                    self.assert_verdict(self.validate(report), "INVALID", 3)

    def test_bad_text_hash_and_list_values(self):
        for key in ("expectation", "basis", "observation", "id"):
            for value in ("", "  ", True, None, []):
                with self.subTest(key=key, value=value):
                    report = copy.deepcopy(self.report)
                    report["checks"][0][key] = value
                    self.assert_verdict(self.validate(report), "INVALID", 3)
        for value in (True, "xyz", "f" * 63, "g" * 64):
            report = copy.deepcopy(self.report)
            report["artifacts"][0]["sha256"] = value
            self.assert_verdict(self.validate(report), "INVALID", 3)

    def test_failure_list_survives_invalid_evidence(self):
        self.report["checks"][0]["status"] = "FAIL"
        self.artifact.unlink()
        result = self.validate()
        self.assert_verdict(result, "INVALID", 3)
        self.assertEqual(result["product_failures"], ["C1"])

    def test_invalid_json_duplicate_keys_nonfinite_and_utf8(self):
        path = self.root / "bad.json"
        for raw in (b"{", b'{"version":1,"version":1}', b'{"version":NaN}', b'{"version":Infinity}', b"\xff"):
            with self.subTest(raw=raw):
                path.write_bytes(raw)
                self.assert_verdict(qa_result.check_file(path), "INVALID", 3)

    def test_missing_report_is_invalid(self):
        self.assert_verdict(qa_result.check_file(self.root / "missing.json"), "INVALID", 3)

    def test_cli_json_status_and_exit_codes(self):
        for status, expected_code, expected_verdict in (("PASS", 0, "PASS"), ("FAIL", 1, "FAIL"), ("BLOCKED", 2, "INCOMPLETE"), ("NOT_A_STATUS", 3, "INVALID")):
            with self.subTest(status=status):
                self.report["checks"][0]["status"] = status
                self.report["checks"][0]["reason"] = "Synthetic reason"
                path = self.write_report()
                result = subprocess.run([sys.executable, str(SCRIPT), "check", str(path), "--format", "json"], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected_code, result.stderr + result.stdout)
                output = json.loads(result.stdout)
                self.assertEqual(output["verdict"], expected_verdict)
                self.assertIn("does not independently verify", output["assurance"])
                self.assertEqual(result.stderr, "")

    def test_cli_text_is_utf8_with_ascii_console_encoding(self):
        self.report['run_id'] = 'тест-проход-1'
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'check', str(self.write_report())],
                                env={**os.environ, 'PYTHONIOENCODING': 'ascii'}, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('PASS — тест-проход-1', result.stdout.decode('utf-8'))
        self.assertEqual(b'', result.stderr)

    def test_cli_usage_error_and_help(self):
        bad = subprocess.run([sys.executable, str(SCRIPT), "check"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 3)
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)

    def test_cli_text_has_no_fake_product_certification(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.write_report())], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS", result.stdout)
        self.assertIn("local SHA-256 integrity only", result.stdout)


if __name__ == "__main__":
    unittest.main()
