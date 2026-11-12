# Reuse an evaluation harness without overstating its result

Use the current supported harness interfaces; inspect the project's installed version and adapter before inventing configuration keys. This skill does not require Promptfoo, pytest or any particular provider.

## Keep four kinds of result separate

| Run | What it can demonstrate | What it cannot demonstrate alone |
| --- | --- | --- |
| Synthetic checker controls | The evaluator detects the selected deliberate corruptions | Live model quality |
| Recorded-output replay | The current evaluator's verdict on those recorded outputs | Current deployed behavior |
| Direct provider/service call | Behavior of that service with those inputs | Application authorization, mapping or persistence omitted by the adapter |
| Product journey | Observed full-path behavior in the tested environment | Universal model quality or behavior in another deployment |

## Comparison record

Record only what is needed to reproduce the comparison: case/input identities, expectation version, baseline/candidate identities, checker/rubric identity, relevant settings, tools and observed boundary. Mark unknown identity explicitly; do not fill it from an unrelated source checkout.

Retain per-case outcomes before aggregates. Separate product quality from execution health: a model refusal can be an expected pass or a quality failure depending on the task, while a provider outage is an execution problem. Missing output does not establish absence of a forbidden behavior that may have occurred earlier.

Run baseline and candidate on a fixed comparable case set. If a dataset or rubric changes, recompute both or present the change separately. Keep latency/cost comparisons clear about cached vs live execution, model calls, retries and excluded errors.

Baseline promotion is an explicit operation after validation, not a side effect of a failed test. An error response must not become the accepted reference simply because a later error matches it.

## Data destinations

Before a live run, inspect where target requests, generated probes, grading calls and report uploads go. A “do not share report” option does not prevent external model calls. Keep credentials outside fixtures and archives; use approved synthetic data and existing secure runtime configuration.

During a bounded live run, stop on an unexpected authorization/tenant mismatch, rate limiting or degradation according to the agreed rules. Do not retry a possibly state-changing request blindly.

## Preserve the meaning through transformations

Retain the original response when parsing/extraction fails. Apply normalization only when the contract permits it and preserve both forms; stripping unexpected wrappers can otherwise conceal a structured-output failure. Bind extracted facts and quotes to source ranges/IDs and to the saved entity, not merely to text found somewhere in the response.

Separate actual runtime identity from a model name in configuration or a source checkout. Record what is known and which comparison remains valid when the deployment is unknown.

## Judge selection and calibration

Use deterministic checks for exact obligations and a calibrated human/semantic assessment for meaning. Require the judge's verdict map to be complete and correctly typed, with evidence actually present in the designated source. Missing fields, invalid citations, parse failures and provider errors are execution/assessment failures rather than implicit passes.

Keep calibration/tuning cases apart from the evaluation holdout. Blind candidate identity where feasible, preserve repeated-trial disagreement, and spot-check consequential judgments—including passes—against source material. A system's self-assessment is not independent evidence. Checker auditing owns investigation of evaluator defects; avoid rewriting the rubric until a preferred candidate wins.

The final account should distinguish direct observations, judge assessments, unresolved disagreement, execution errors and unexecuted cases. Preserve cleanup outcome alongside valid findings.
