# Run records: consistency, not certification

These are **synthetic format examples**, not results from a browser, model or
production application. The helper verifies local evidence integrity and report
consistency. It cannot establish whether the expectation is correct, the observation
is true, or the file was written by an independent observer.

From the **source checkout root**, with Python 3.10 or later (use `py -3` on Windows):

```sh
python3 scripts/qa_result.py check examples/results/healthy/run.json
python3 scripts/qa_result.py check examples/results/failing/run.json --format json
python3 scripts/qa_result.py check examples/results/incomplete/run.json --format json
```

Expected exit codes are **0**, **1**, and **2**, respectively. Do not wrap all
three in an unconditional `set -e` example and mistake the intentional FAIL for
a broken helper. These example records are source fixtures and are excluded from the
install bundle; runtime users supply their own report paths. No network, model, shell command, report mutation, or artifact
write is performed by `check`.

## Input version 1

The complete machine-readable shape is in `schemas/run.schema.json` in both the source and runtime. The Python validator additionally checks cross-references and files.

- `version`: the JSON integer `1` (not a string, boolean or `1.0`).
- `run_id`: a nonblank identifier for this record.
- `target`: `environment`, `actor`, and `build`. Use a nonsecret actor/role label;
  a build may be `null` when unknown. Unknown build attribution produces a warning,
  not a false claim that the observed behavior was not tested. Do not use it to
  claim that a particular deployed fix has been verified.
- `scope`: `goal`, the requirement/baseline `basis`, and an `exclusions` array.
  An exclusion describes the agreed scope; it does not turn an untested included
  requirement into PASS. Optional `required_check_ids` records the agreed check IDs;
  a required check absent from the record is a coverage gap, not an implicit PASS.
- `checks`: one or more check objects. Every check has unique `id`, `expectation`,
  `basis`, `status`, and `evidence_refs`.
  - `PASS` and `FAIL` require a nonblank `observation` and one or more artifact IDs.
  - `BLOCKED`, `INCONCLUSIVE`, and `NOT_RUN` require a nonblank `reason`.
  - Optional `reproducibility` is `single_observation`, `replayed`, or
    `not_applicable`. It records the author's assertion; it does not prove replay.
- `artifacts`: unique `id`, report-relative `path`, and `sha256`. Paths use `/`,
  stay inside the report directory, and cannot contain drive prefixes, backslashes,
  empty segments, `.` or `..`. Symlinks, Windows reparse points (including
  junctions), non-regular files, missing files and hash mismatches are rejected. Hashes detect a changed artifact, not fabricated evidence.
- `cleanup`: `status` and nonblank `notes`. Status is `not_needed`, `verified`,
  `pending`, or `failed`. An unresolved cleanup prevents a complete-run PASS.
- Optional `superseded_by`: replacement run ID/reference. This record remains
  historical and incomplete for a current-state conclusion. The helper does not
  follow or fetch the replacement.

There is **no input `verdict`**. Unknown properties and duplicate JSON keys are
rejected rather than silently ignoring a misleading headline. Enum values and
types are not coerced. Use `NOT_RUN` with a reason to record an unavailable check;
an empty `checks` array is invalid.

## Derived outcome and exit status

Applied in this order:

| Outcome | Condition | Exit |
|---|---|---:|
| `INVALID` | Invalid structure, missing/unsafe evidence, broken reference or hash mismatch | 3 |
| `FAIL_WITH_GAPS` | At least one declared product FAIL plus incomplete checks, cleanup, or supersession | 2 |
| `FAIL` | At least one declared product FAIL; no incomplete checks or lifecycle gaps | 1 |
| `INCOMPLETE` | No product FAIL, but an included check/lifecycle is incomplete or the report is superseded | 2 |
| `PASS` | Every included check declares PASS, the artifact checks succeed, and lifecycle is complete | 0 |

`product_failures` preserves the IDs of declared FAIL checks even when the overall
record is invalid or incomplete. It is **not an independent confirmation** of those
failures. `counts`, `gaps`, `issues`, `warnings`, and `assurance` remain visible in
JSON output. CLI syntax errors also exit 3; `--help` exits 0.

Keep the artifact directory stable while checking it. Files are streamed for
hashing, not loaded wholesale. Read sensitive evidence only in an appropriate
private workspace; this helper is not a redactor or a secret scanner.

## What this intentionally does not do

It does not run tests, decide which tests are sufficient, authenticate an actor,
prove deployment provenance, enforce network scope, judge screenshots, compare
AI meaning, publish a result, or replace a product test oracle. A trustworthy
looking JSON record can still contain an incorrect expectation. Review the
underlying claim and its evidence before a release decision.
