#!/usr/bin/env python3
"""Check a QA report's structure and local artifact integrity, not its truth.

Read-only, dependency-free Python 3.10+. See schemas/run.schema.json for v1.
Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE/FAIL_WITH_GAPS, 3 INVALID.
An unknown build warns about attribution; it does not erase observed behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any
from strict_json import load as load_json, identifier, terminal
from strict_json import unique_object as _unique_object, reject_constant as _reject_constant


STATUSES = {"PASS", "FAIL", "BLOCKED", "INCONCLUSIVE", "NOT_RUN"}
CLEANUP = {"not_needed", "verified", "pending", "failed"}
EXIT_CODES = {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2, "FAIL_WITH_GAPS": 2, "INVALID": 3}
ASSURANCE = (
    "Checks structure, reference consistency and local SHA-256 integrity only. "
    "It does not independently verify product behavior, expectations or authorship."
)


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, name: str, required: set[str], optional: set[str], issues: list[str]) -> bool:
    if not isinstance(value, dict):
        issues.append(f"{name}: expected an object")
        return False
    for key in sorted(required - value.keys()):
        issues.append(f"{name}.{key}: required")
    for key in sorted(value.keys() - required - optional):
        issues.append(f"{name}.{key}: unknown field")
    return True


def _text_fields(value: dict[str, Any], name: str, keys: set[str], issues: list[str]) -> None:
    for key in sorted(keys):
        if key in value and not _nonblank(value[key]):
            issues.append(f"{name}.{key}: expected a nonblank string")


def _string_list(value: Any, name: str, issues: list[str], *, unique: bool = False) -> bool:
    if not isinstance(value, list) or any(not _nonblank(x) for x in value):
        issues.append(f"{name}: expected an array of nonblank strings")
        return False
    if unique and len(set(value)) != len(value):
        issues.append(f"{name}: duplicate entries")
        return False
    return True


def _artifact_parts(path: Any) -> list[str]:
    if not _nonblank(path):
        raise ValueError("path must be a nonblank relative POSIX-style path")
    parts = path.split("/")
    if "\\" in path or ":" in path or any(p in {"", ".", ".."} for p in parts):
        raise ValueError("path must be relative, with no empty, dot, parent, drive or backslash segments")
    return parts


def _digest_artifact(base: Path, parts: list[str]) -> str:
    """Reject symlinks and non-files. POSIX traversal is anchored with dir fds.

    Elsewhere, preflight every component and compare the opened file identity
    before reading. Artifact hashes detect changes, not malicious authorship.
    """
    current = base
    info = None
    for index, part in enumerate(parts):
        current = current / part
        info = current.lstat()
        reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if stat.S_ISLNK(info.st_mode) or reparse:
            raise ValueError("symlinks and reparse points are not accepted")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ValueError("intermediate path is not a directory")
    if info is None or not stat.S_ISREG(info.st_mode):
        raise ValueError("artifact must be a regular file")

    fd = None
    directory_fd = None
    try:
        anchored = os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
        if anchored:
            directory_fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0), dir_fd=directory_fd)
        else:
            fd = os.open(current, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("artifact changed during inspection")
        digest = hashlib.sha256()
        with os.fdopen(fd, "rb") as stream:
            fd = None
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    finally:
        if fd is not None:
            os.close(fd)
        if directory_fd is not None:
            os.close(directory_fd)


def validate_report(data: Any, base_dir: Path) -> dict[str, Any]:
    """Return a conservative summary. No files are created or changed."""
    issues: list[str] = []
    warnings: list[str] = []
    gaps: list[str] = []
    failures: list[str] = []
    counts = {status: 0 for status in sorted(STATUSES)}
    run_id = data.get("run_id") if isinstance(data, dict) and _nonblank(data.get("run_id")) else None

    def finish() -> dict[str, Any]:
        if issues:
            verdict = "INVALID"
        elif failures and gaps:
            verdict = "FAIL_WITH_GAPS"
        elif failures:
            verdict = "FAIL"
        elif gaps:
            verdict = "INCOMPLETE"
        else:
            verdict = "PASS"
        return {
            "run_id": run_id,
            "verdict": verdict,
            "exit_code": EXIT_CODES[verdict],
            "counts": counts,
            "product_failures": failures,
            "gaps": gaps,
            "issues": issues,
            "warnings": warnings,
            "assurance": ASSURANCE,
        }

    if not _object(data, "report", {"version", "run_id", "target", "scope", "checks", "artifacts", "cleanup"}, {"superseded_by"}, issues):
        return finish()
    if type(data.get("version")) is not int or data["version"] != 1:
        issues.append("report.version: expected integer 1")
    _text_fields(data, "report", {"run_id", "superseded_by"}, issues)
    if not identifier(data.get("run_id")):
        issues.append("report.run_id: expected a nonblank identifier without control characters")
    if "superseded_by" in data and _nonblank(data["superseded_by"]):
        gaps.append("Report is superseded; use the replacement evidence before a current-state conclusion")

    target = data.get("target")
    if _object(target, "target", {"environment", "build", "actor"}, set(), issues):
        _text_fields(target, "target", {"environment", "actor"}, issues)
        if "build" in target:
            if target["build"] is None:
                warnings.append("Build attribution is unverified; do not claim that a particular deployed fix or version was verified")
            elif not _nonblank(target["build"]):
                issues.append("target.build: expected a nonblank string or null")
    scope = data.get("scope")
    required_ids = None
    if _object(scope, "scope", {"goal", "basis", "exclusions"}, {"required_check_ids"}, issues):
        _text_fields(scope, "scope", {"goal", "basis"}, issues)
        _string_list(scope.get("exclusions"), "scope.exclusions", issues)
        if "required_check_ids" in scope:
            value = scope["required_check_ids"]
            if _string_list(value, "scope.required_check_ids", issues, unique=True):
                if not value or any(not identifier(x) for x in value):
                    issues.append("scope.required_check_ids: expected nonempty, control-free identifiers")
                else:
                    required_ids = value
        else:
            warnings.append("No required-check inventory supplied; completeness covers declared checks only, not all requirements")

    artifacts = data.get("artifacts")
    artifact_ids: set[str] = set()
    if not isinstance(artifacts, list):
        issues.append("artifacts: expected an array")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        name = f"artifacts[{index}]"
        if not _object(artifact, name, {"id", "path", "sha256"}, set(), issues):
            continue
        _text_fields(artifact, name, {"id"}, issues)
        aid = artifact.get("id")
        if not identifier(aid):
            issues.append(f"{name}.id: invalid identifier")
        if _nonblank(aid):
            if aid in artifact_ids:
                issues.append(f"{name}.id: duplicate artifact ID")
            artifact_ids.add(aid)
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            issues.append(f"{name}.sha256: expected 64 hexadecimal characters")
            continue
        try:
            parts = _artifact_parts(artifact.get("path"))
            observed = _digest_artifact(Path(base_dir).resolve(strict=True), parts)
            if observed != digest.lower():
                issues.append(f"{name}: SHA-256 mismatch")
        except (OSError, ValueError, RuntimeError) as error:
            # Avoid leaking OS exception paths or file contents in shareable output.
            message = str(error) if isinstance(error, ValueError) else type(error).__name__
            issues.append(f"{name}: artifact unavailable or unsafe ({message})")

    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        issues.append("checks: expected a nonempty array; zero checks cannot establish PASS")
        checks = []
    check_ids: set[str] = set()
    for index, check in enumerate(checks):
        name = f"checks[{index}]"
        if not _object(check, name, {"id", "expectation", "basis", "status", "evidence_refs"}, {"observation", "reason", "reproducibility"}, issues):
            continue
        _text_fields(check, name, {"id", "expectation", "basis", "observation", "reason"}, issues)
        cid = check.get("id")
        if not identifier(cid):
            issues.append(f"{name}.id: invalid identifier")
        label = cid if _nonblank(cid) else name
        if _nonblank(cid):
            if cid in check_ids:
                issues.append(f"{name}.id: duplicate check ID")
            check_ids.add(cid)
        status_value = check.get("status")
        if not isinstance(status_value, str) or status_value not in STATUSES:
            issues.append(f"{name}.status: invalid status")
        else:
            counts[status_value] += 1
            if status_value == "FAIL":
                failures.append(label)
            if status_value in {"BLOCKED", "INCONCLUSIVE", "NOT_RUN"}:
                gaps.append(f"{label}: {status_value}")
                if not _nonblank(check.get("reason")):
                    issues.append(f"{name}.reason: required for an incomplete check")
            elif not _nonblank(check.get("observation")):
                issues.append(f"{name}.observation: required for PASS/FAIL")
        refs = check.get("evidence_refs")
        if _string_list(refs, f"{name}.evidence_refs", issues, unique=True):
            if status_value in ("PASS", "FAIL") and not refs:
                issues.append(f"{name}.evidence_refs: PASS/FAIL requires evidence")
            for ref in refs:
                if ref not in artifact_ids:
                    issues.append(f"{name}.evidence_refs: unknown artifact ID {ref!r}")
        if "reproducibility" in check:
            value = check["reproducibility"]
            if not isinstance(value, str) or value not in {"single_observation", "replayed", "not_applicable"}:
                issues.append(f"{name}.reproducibility: invalid value")

    if required_ids is not None:
        for cid in required_ids:
            if cid not in check_ids:
                gaps.append(f"Required check {cid}: missing from report")

    cleanup = data.get("cleanup")
    if _object(cleanup, "cleanup", {"status", "notes"}, set(), issues):
        _text_fields(cleanup, "cleanup", {"notes"}, issues)
        status_value = cleanup.get("status")
        if not isinstance(status_value, str) or status_value not in CLEANUP:
            issues.append("cleanup.status: invalid status")
        elif status_value in {"pending", "failed"}:
            gaps.append(f"Cleanup {status_value}; no complete-run PASS")
    return finish()


def check_file(path: Path) -> dict[str, Any]:
    try:
        data = load_json(path)
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        result = validate_report(None, path.parent)
        result["issues"] = [f"Report could not be read as strict UTF-8 JSON ({type(error).__name__})"]
        return result
    return validate_report(data, path.parent)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(3, f"{self.prog}: error: {message}\n")


def main(argv: list[str] | None = None) -> int:
    # Keep human-readable results portable across Windows console/code-page settings.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    parser = _Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    check = commands.add_parser("check", help="Read-only validation of a v1 report and its referenced artifacts")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)
    result = check_file(args.path)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"{result['verdict']} — {terminal(result['run_id'] or 'unreadable run')}")
        print("Checks: " + ", ".join(f"{key}={value}" for key, value in result["counts"].items()))
        for category in ("product_failures", "gaps", "issues", "warnings"):
            for item in result[category]:
                print(f"{category}: {terminal(item)}")
        print(result["assurance"])
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
