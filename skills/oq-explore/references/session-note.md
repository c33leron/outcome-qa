# Optional session handoff

Use an existing project QA record when it fits. Create or update `.qa/session.md` only when the user authorizes that durable project write; otherwise keep the same summary in conversation. A session note is a handoff aid, not new proof or a hidden background memory system.

## Minimal shape

```text
Scope and current requirement revision:
Target/environment and observed build (or unknown):
Observed at / session identifier:
Actors and owned synthetic entity/operation labels:
Checked: criterion → action/observation → evidence pointer → result
Findings: observed violation, reproduction exposure, current status
Gaps: blocked/not-run/unresolved criterion and deciding prerequisite
State remaining: owned fixture, restoration plan, verified cleanup or residue
Next useful check:
Supersedes / reuses: prior note or result and why still applicable
```

Keep credentials, cookies, real personal data, raw customer content and signed URLs out of the note. Use local evidence pointers with appropriate access and redacted labels; do not copy private artifacts into a public package.

## Resume with a freshness check

Compare current requirement, build/config, actor rights, fixture identity/history and observation time to the note. Identify which evidence remains applicable and label it as reused. A changed relevant condition can supersede affected conclusions; ordinary steps within the original run do not erase their own evidence.

A line marked “checked” is not sufficient by itself when its evidence is missing. Do not repeat a potentially completed write until its actual state is known. Preserve historical findings and failed attempts when appending a correction; never overwrite the record merely to make it green.

After authorized changes, read the note back and verify that unrelated project content is preserved. Conflicting or user-edited notes need reconciliation rather than blind replacement. Continue unaffected work while stating the smallest unresolved gap.
