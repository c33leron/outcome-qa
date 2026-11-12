# Result v1: consistency, not an oracle

Run `python3 scripts/qa_result.py check PATH --format json` from the package root. It is a read-only local validator; no commands embedded in a report are executed and no URLs are fetched.

The canonical shape is [run.schema.json](../schemas/run.schema.json). A report identifies environment, actor, nullable build, goal, test basis, exclusions, checks, artifacts and cleanup. Artifact paths are relative to the report directory; SHA-256 binds each reference to the saved bytes. It is not a digital signature or an independent witness.

For a declared batch/all-AC run, `scope.required_check_ids` may list the nonempty unique expected check IDs. A required ID missing from `checks` makes the result INCOMPLETE (or FAIL_WITH_GAPS), not PASS. Without this inventory the helper warns that completeness covers only checks actually declared. It cannot invent omitted requirements, detect a dishonest inventory or establish pagination completeness from prose. IDs reject control/format characters; input JSON rejects duplicate keys and nonfinite numbers.

Every PASS/FAIL check needs a concrete expectation, basis, observation and evidence reference. Other statuses carry the reason the check is unfinished. Null build means attribution is unverified, not that every directly observed behavior is unknowable. A superseded report cannot supply a current PASS.

| Computed outcome | Exit | Meaning |
|---|---:|---|
| PASS | 0 | Complete, internally consistent declared passes; **not independently proven correctness** |
| FAIL | 1 | Valid report records a product failure with no declared gaps |
| FAIL_WITH_GAPS | 2 | Product failure remains visible, but coverage/cleanup/report currency is incomplete |
| INCOMPLETE | 2 | Blocked, not run, inconclusive, cleanup pending/failed or superseded |
| INVALID | 3 | Bad schema, types, references, missing/tampered artifacts or unsafe path |

Do not map every nonzero exit to a product bug. Do not map exit 0 to approval of the product. Read the check-level record, especially known failures alongside gaps.

The helper cannot detect a fabricated screenshot, dishonest observation, wrong test oracle, stale external environment or unrecorded action. Have a reviewer compare important claims to raw evidence, and use known-good/bad controls for evaluators. Keep raw secrets and personal data out of the report; artifact hashing does not redact them.
