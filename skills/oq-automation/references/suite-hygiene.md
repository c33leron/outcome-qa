# Keep the suite useful as it grows

Use the project's existing runner, conventions and risk model. Changing suite membership or CI policy is implementation work, not an automatic consequence of a read-only review.

## Fixtures, sessions and meaningful observation

Separate setup from the operation being tested. Register synthetic resources before assertions can fail, retain previous values for restoration and verify cleanup independently. Preserve the initial failure when teardown also fails; report both.

Reuse authentication only where the scenario permits it. Login/logout/expiry tests need the real transition they claim to test. Separate browser contexts can still share backend organization, role or account state. Coordinate mutable account/tenant/resource ownership across workers and processes; one runner's concurrency limit does not constrain another runner.

Prefer accessible role/name, then stable test IDs. Check that a negative locator could find the valid control in a healthy case. Wait for the relevant state, URL, response or terminal operation condition; generic network silence, sleeps and increased timeouts can hide missing synchronization. A measured timeout change can be appropriate when its contractual/trace basis is explicit.

Discover available executables, versions and browser/session capabilities before installing anything. Preserve the user's authenticated context when that is required. If installation is genuinely needed and authorized, use an isolated scratch environment, state the download/change, test the capability and clean owned resources. Missing shell/network/runtime capabilities limit execution; they do not justify invented test results.

## Select and maintain tiers

| Tier | Useful purpose | Selection principle |
| --- | --- | --- |
| Smoke | Establish that a critical journey can complete with a meaningful result | Few decisive representative paths; a health endpoint alone is not product smoke |
| Core regression | Protect important behavior from frequent changes | Stable expected rules and independent observations, including critical negative paths |
| Extended | Cover costlier compatibility, integration and uncommon combinations | Explicit supported variants and risk; report which variants actually ran |

Use tags/selection rather than duplicate copies of the same test. Admit a check when its business basis, fixture, oracle, ownership and failure action are clear. Review retirement against changed requirements and equivalent remaining coverage; preserve the old failure/proof when removing an obsolete test. Test deletion is not a legitimate way to silence an unresolved product defect.

## Quarantine is tracked risk, not green

A quarantine needs a reason, owner, issue/reference, scope, expiry/review date and an explicit coverage gap. Keep attempts and diagnostics available; ensure a critical requirement has another adequate check or is visibly unverified. Moving a test out of a blocking gate is a risk decision, not a claim that the failure disappeared. Expired quarantine must surface for review rather than renewing itself silently.

A retry that passes indicates observed intermittency. Preserve the first failure and explain retry policy separately from the fix. Diagnose synchronization, fixture ownership or product behavior before extending timeouts or changing assertions.

## CI failure and artifact policy

Fail fast where a prerequisite blocks dependent work; let independent checks finish when that provides useful evidence without conflicting state. Always preserve the initial error, relevant trace/output, fixture identity and cleanup outcome through the runner's supported finalization mechanism.

Separate install/build/authentication/collection failures from product assertions. Zero collected tests, all-skipped suites, missing reports and interrupted jobs remain incomplete even if a wrapper exited zero. Report attempted, executed, passed, failed, skipped and blocked denominators explicitly. A report upload receipt does not prove the tests completed.

Prefer a reproducible command plus necessary setup over an unexplained green screenshot. For authorized repairs, run the affected check and meaningful neighbors, then required project gates. Keep pre-existing failures separate from introduced ones.
