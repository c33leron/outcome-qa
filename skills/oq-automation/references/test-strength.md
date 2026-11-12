# Review whether the test can detect the defect

Use this for ordinary test implementation and code review. Start with the test's product claim and inspect the mechanisms needed to assess it. An explicit audit of whether an oracle, judge, metric or release gate can be trusted belongs to `oq-checker-audit`; this reference is not a separate competing evaluator-audit workflow.

## Common blind spots

- Assertion checks a locator object, nonempty text or HTTP status instead of the promised outcome.
- UI success is optimistic; no observation establishes the server write or later rendering.
- Expected and actual values use the same faulty parser or helper.
- Wrong subject/object passes because all expected words occur somewhere.
- Conditional test paths or swallowed exceptions remove the only meaningful assertion.
- Empty collections, missing rows or skipped steps produce a vacuous “all passed”.
- Mock replaces the component or boundary the test claims to exercise.
- Negative assertion never demonstrates that the selector/control can succeed.
- State leaks from a previous test; cleanup is not independently verified.

## Levels of evidence

1. **Static reasoning:** identify a specific code path that can conceal a defect. State it as a static finding unless executed.
2. **Assertion sensitivity:** change an expectation in a disposable copy and observe failure. This shows the assertion executes; it does not prove detection of a product defect.
3. **Product fault sensitivity:** introduce a narrowly defined fault in an isolated app/fixture, keep the test expectation unchanged, and observe a failure at the intended assertion. Verify the healthy control still passes.

Do not count compilation errors, server startup errors, missing dependencies or unrelated timeouts as a detected product mutant. If a mutant cannot reach the targeted assertion, classify the attempt as invalid or inconclusive, not “caught”. Preserve the injected fault identity and relevant output.

Run such experiments only where local modification/fault injection is authorized, never in a shared live environment. Prefer an isolated copy rather than promising to undo mutations in someone else's working tree. Check restoration and owned processes even on failure.

An undetected mutation establishes a blind spot for that mutation, not that the test is useless. A detected mutation establishes sensitivity to that fault, not exhaustive correctness. Choose faults tied to real risks rather than maximizing a mutation-score headline.
