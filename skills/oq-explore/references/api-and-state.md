# API and integration outcome lenses

Use these when the API or asynchronous integration is the tested surface. A browser is optional unless the claim concerns an actual UI journey. Select lenses from the contract, not every row for every endpoint.

| Contract or risk | Discriminating check | Observe beyond the status |
| --- | --- | --- |
| Atomic batch | One invalid element among valid ones | If all-or-nothing is promised, no element is committed after rejection; if partial success is allowed, reconcile each item outcome |
| Retry/idempotency | Same logical operation repeated; same key with conflicting payload | Allowed effect count and original object state; a repeated success response may still duplicate work |
| Version conflict | Two permitted stale views update the same disposable object | The documented reject/merge/last-write policy; not merely whichever response arrived last |
| Pagination | Traverse pages with stable identifiers and declared ordering | Missing/duplicate records, cursor behavior and completeness; consider concurrent writes only when that consistency model is in scope |
| Callback/webhook | Valid event, invalid authentication, a bounded replay or older event when permitted | Correct event binding, one allowed state transition, and no stale overwrite or repeated effect |
| Async acceptance | Operation accepted, then success/error/cancel/retry | Terminal reason and saved result for that operation; 202 and a queue ID do not prove completion |
| Negative write | Invalid data or a disallowed test actor | Protected post-state unchanged even if the API returned the expected 4xx |
| Partial update | Omit a field, explicitly send null, then use the contract's distinct empty value on equivalent fixtures | Preserve, clear, replace or reject according to the specific update format; unchanged neighbors stay intact. Do not assume every PATCH uses JSON Merge Patch semantics |
| Write/read projection | Change a value, then read the same stable entity through the relevant detail/list/export or permitted other client | Ownership and meaning survive serialization and normalization; a correct write response need not prove every read projection is current |
| Cache or eventual read model | Compare the relevant read before and after a known completed operation, using the documented consistency window or completion signal | Distinguish an allowed stale projection from a lost update. Capture cache/client behavior rather than silently bypassing the failing user path |

Capture a healthy control and the relevant pre-state before the challenge. Use stable operation/entity identifiers to correlate the response, background attempt and read-back. A lower-level setup may make the check efficient, but do not label it a full user journey if it bypasses a material boundary.

Validate types and documented null/empty/absent meanings, then inspect relationships and preserved fields. A structurally valid response can carry the wrong owner or stale value. Do not weaken the expectation to match an implementation detail discovered during diagnosis.

For normalized values, compare the meaning and representation the contract actually promises: identifier type, units/precision, timestamp offset and permitted canonical form. Do not compare only displayed strings, coerce a large integer through an imprecise number representation, or invent a rounding tolerance to hide a mismatch.

For multiple read models, bind observations to the same actor, tenant, stable object ID and operation/version where available. State which boundary was observed: browser cache, API response, materialized projection or source record. A cache-bypassed read can help localize a stale display but does not erase it. If the acceptable delay or consistency rule is unknown, report the observed divergence and the missing contract; do not invent either immediate consistency or an unlimited wait for success.

Authorization rules in the selected API contract require appropriate actor controls even in a request called “functional QA”. Use permitted accounts and synthetic objects; an invalid object rejected for every role is not an authorization test. Keep setup, challenged operation and owner-side read-back distinct.

For concurrency or replay, establish the expected conflict/duplicate policy first and use bounded, coordinated requests on isolated data. Random parallel traffic does not make a meaningful race test. Restore owned state and report residual effects after preserving evidence.
