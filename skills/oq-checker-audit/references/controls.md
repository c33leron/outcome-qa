# Build controls that test the claimed property

Choose only relevant rows. A large set of easy corruptions can conceal a missing important one.

| Claimed property | Healthy control | Corrupt control | False confidence trap |
| --- | --- | --- | --- |
| Correct fact ownership | Two distinct people with their actual durations | Swap durations, leave all words present | Global substring presence still passes |
| Complete question coverage | One answer associated with each asked question | Reuse one answer for several questions | Count of recognized keywords equals answered questions |
| Literal source quote | Exact quote attached to the right source answer | Quote from another answer | Quote exists somewhere, but not where claimed |
| Semantic fidelity | Allowed paraphrase preserves negation | Remove negation while keeping topic words | High similarity hides reversed meaning |
| Structured verdict | Complete map with boolean pass fields | Missing entry or `"false"` string | Missing treated as success; string coerced to true |
| No forbidden tool effect | Reply with no prohibited write, verified state | Write succeeds before final refusal | Final refusal regex passes despite the side effect |
| Valid baseline | Accepted successful reference | Record HTTP 503, then verify HTTP 503 | Matching failures become a clean comparison |
| Nonempty coverage | Required cases collected and evaluated | Zero collected cases or all skipped | Vacuous success is reported as total coverage |
| Metric gate | Inputs around the documented boundary | Outlier/rounding input exposes wrong algorithm | Gate code and expected result share the same bug |
| Evidence completeness | Required result artifacts present | Remove one required attempt/output | Directory exists, so inspector reports success |

## Example: percentile algorithm

Only if the metric contract specifies nearest rank, p95 for twelve values consisting of eleven 100 ms samples and one 10,000 ms sample selects rank `ceil(0.95 * 12) = 12`, or 10,000 ms. Other documented percentile conventions can differ; do not call that a bug merely because a different convention was expected informally.

## Example: exact quote versus semantic claim

A report may require a literal supporting quote, but a free-text summary may allow paraphrase. Failing the quote contract is not automatically proof that the summarized fact is invented. Test and report those two properties separately.

## Record each challenge

Keep a compact record of expected verdict, actual verdict, reached checker, triggering check and execution boundary. Preserve controls and code identities. If the healthy control fails, resolve that before interpreting the corrupt control as a meaningful success.

## Trace the verdict from input to release decision

| Boundary | Question that distinguishes a reliable decision from a false result |
| --- | --- |
| Reachability | Does the intended assertion execute for required cases, including empty/missing inputs, or do early returns and conditions bypass it? |
| Independent expectation | Does expected reuse the same transformation defect as actual? Are tuning/reference labels visible to the target when they should be withheld? |
| Attribution | Are required values bound to the correct person/object/turn, or merely present somewhere? |
| Typing and completeness | Are all required keys present with exact types? Does a string boolean or absent key become success? |
| Evidence grounding | Does each quote/ID occur in the claimed source and support that particular assertion? |
| Error handling | Where do provider errors, timeouts, parse failures and missing outputs enter the verdict? Can an execution error become CLEAN or an accepted baseline? |
| Aggregation | Are attempted, reached, evaluated, failed, skipped and missing cases represented in the denominator? Which documented weighting/rounding/percentile convention is applied? |
| Currency | Does a changed case set, rubric, provider, build or parser silently reuse an incompatible reference or score? |

Preserve per-case controls and observations before computing a headline score. Healthy variations matter: permitted paraphrases and optional fields must remain acceptable when the contract allows them.

## What an experiment establishes

- A reachable static mechanism is a static finding until exercised.
- Replaying recorded outputs tests the current evaluator on those outputs, not the current product.
- Inverting an assertion demonstrates that it executes and is sensitive to that expectation; it does not prove a product bug is detectable.
- An authorized product mutation is detected only if the unchanged test reaches and fails for the intended fault. Build/setup/import failures are invalid or inconclusive attempts.
- An undetected mutation establishes that particular blind spot, not total uselessness. A detected one is not exhaustive correctness.

Run modifications only in an authorized isolated copy and verify restoration/owned-process cleanup. A green suite for the checker can still omit an important negative control.

For model judges, record rubric/model/configuration, separate tuning from holdout cases, blind candidate identities where feasible and retain every trial's disagreement/error. Judge confidence and model-family choice do not substitute for calibration against the measured rule. An error response must not be promoted as the new accepted baseline because another error happens to match it.
