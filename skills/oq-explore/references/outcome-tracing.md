# Trace the promised outcome

Use only the stages the product's promise depends on. Do not demand database access for every visual check.

| Stage | Evidence to seek | What it does not establish |
| --- | --- | --- |
| User action | Real control activated with relevant input | Server accepted or completed it |
| Acceptance | Correct request, response and stable operation/entity ID | Durable success |
| Processing | Relevant task/attempt history, retry/cancellation and terminal reason | Complete or correct data |
| Persistence | Authorized read-back of the correct object/version | UI renders that result correctly |
| Presentation | Reload/reopen exposes the saved result to the intended actor | Other actors or devices behave the same |
| Semantics | Expected facts, relationships and constraints hold | The whole product or model is correct |

Join observations by operation, entity and attempt—not by similar text alone. Keep original and retry attempts distinct. A client timeout or a failed follow-up refresh can coexist with a successful server write. Do not replay the write until its outcome or an accepted duplicate-safe strategy is known.

Read the actual observation channel: a page displaying “503” does not establish HTTP 503, and a transient failed inner poll does not establish the final test failed. An HTML/source anomaly without an applicable requirement or observable effect is not automatically a product defect.

For async work, bound observation by the requirement or measured baseline. Queue acceptance is not completion; cancellation acceptance is not stopped work or rollback. For disputed attempts, capacity, runner/product counts or media transitions, use [incident tracing](_shared/incident-tracing.md) to reconstruct conditions at the event time and locate the next deciding check.

For a file/AI pipeline, a useful boundary sequence is: submitted file → extracted input → model output and stop metadata if available → parser/mapper → saved result → UI. A missing raw response can limit attribution without invalidating a directly observed bad saved result. Do not infer truncation solely from a parsing error.

For voice/media work, distinguish connected, track received, heard, recorded, transcribed and reported. Exercise only the boundaries relevant to the promise; a connected peer alone cannot prove a conversation.

## Minimal useful evidence packet

- Test basis and its revision or other meaningful identity.
- Environment/build identity when available, actor/ownership and relevant setup.
- Per attempt: action, expected effect, observed effect, correlation identifiers and bounded timestamps.
- Artifact pointers supporting the claim, with sensitive material withheld or redacted without changing the finding.
- What was not reached, what changed between attempts, and cleanup outcome.

Missing deployment metadata does not forbid observing black-box behavior. It limits attribution to a specific fix/build. A local source checkout or green CI cannot supply missing runtime identity.

## Preserve the evidence while investigating

Register owned fixtures and their prior values before assertions or writes that may fail. After the last dependent worker finishes, restore/delete only those fixtures and independently verify the result. Report cleanup uncertainty separately from the product finding.

Capture meaningful visual states without automation overlays or secrets, inspect the saved image, and recapture or disclose limitations instead of retouching the interface. Source anomalies and DOM nodes do not replace rendered interaction where layout matters.

Keep original failures and attempt chronology when minimizing a reproduction. A later success does not erase an observed intermittent failure. When a relevant rule, build, actor or fixture changes, identify which evidence is superseded; label applicable reused evidence as reused rather than a new run. If later observations contradict the headline, correct its scope visibly instead of silently replacing the historical record.
