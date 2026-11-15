# Find the first broken transition

Use for a delayed, failed or disputed async/media outcome. Start with the user's missing result, not the most alarming log line. This is optional investigation depth, not a new method or mandatory telemetry checklist.

## Build one attributable timeline

Bind environment, stable entity/operation ID, relevant actor/tenant and the observation window. Add deployed revision and effective configuration when available; unknown revision limits source attribution, not a directly observed contract violation. Reconstruct role, flags, capacity and ownership **at the failure time**, not merely now.

Read only records that can connect the disputed transition: request/response → accepted/queued operation → workflow/worker attempts → dependency result → saved state → user-visible result. Record time/timezone, source, correlation/attempt ID and actual event; separate event time from ingestion time and uncertain clock offsets. Similar messages or adjacent timestamps do not join different operations.

Keep original errors, retries, timeout/cancellation and terminal state distinct. A failed attempt may recover; a finished parent may hide a failed child. Observe the authoritative status/read-back for the promised result within a justified window. Report “still processing at the end of this window,” not “permanently hung.” Resolve uncertain writes before retrying and independently verify any authorized recovery or cleanup.

## Keep the boundaries separate

- **Capacity:** compare the effective limit and active/reserved slots when rejected, including lease acquisition/release and the documented queue/rejection policy. An idle dashboard later cannot prove a false rejection earlier. Do not free other work's slots to make a test pass.
- **Media:** distinguish token issued, room joined/peer connected, track received, content actually heard, recording saved, transcript produced and report persisted. Connection/packets are not audibility; a transcript does not prove both parties heard the conversation. Inspect only the next missing boundary with permitted synthetic audio or authorized artifacts.
- **Runner versus product:** count runner cases/attempts separately from unique product entities and their final outcomes. Setup failures, duplicate retries and expected rejections can all affect runner totals without matching failed product journeys. Join by IDs before reconciling counts; do not drop failed attempts or double-count retries as new users.
- **Cause:** an attributed dependency error establishes that call's failure, not a failed workflow or the cause of earlier symptoms. Find where expected and observed first diverge, then use a bounded distinguishing check. Missing traces can leave cause unknown while the user's failed outcome remains confirmed.

## Synthetic worked investigation

A render service allows one concurrent job and rejects excess work. Job `job-B` returned `at_capacity` at 10:02; at 10:08 the dashboard shows zero active jobs. Before filing a false-rejection bug, read the slot lease history and effective limit for 10:02. If `job-A` held the sole valid lease then, B's rejection followed the rule; the later idle state is irrelevant. If A's release committed at 10:01, compare the capacity decision's lease/config version and other reservations: a stale lease and another valid occupier imply different conclusions. Keep B's runner failure separate from A's eventual saved result. This is an illustrative check, not an executed finding.
