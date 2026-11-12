# How we test the tester

Outcome QA does not claim to outperform other QA bundles without a matched comparison. Syntax tests, helper tests and a working lab are different from successful host discovery, useful agent behavior, and comparative effectiveness.

## Four evidence levels

1. **Package**: manifests parse, skill scopes are distinct, implicit invocation is enabled, referenced files and notices are included, archive round-trip is intact.
2. **Helpers/lab**: real tests of integrity, incomplete outcomes, collisions, faulty/fixed app states and cleanup. These do not evaluate the model.
3. **Agent behavior**: fresh model session receives a realistic task and minimum raw artifacts, without the expected answer; inspect tool actions and resulting evidence. A static model-only reasoning probe is labeled as such, not a live browser test.
4. **Comparison**: repeat baseline/current/new/competitor arms on matched tasks and isolated state. Record model, host, instructions, tool versions, permissions, data/build, limits and all attempts. Do not attribute a tool/runtime difference to skill prose.

## Routing

[routing-cases.json](../evals/routing-cases.json) contains positive, negative and neighboring-intent requests. Give the tested model only names/descriptions and prompts, not the answer fields. Determine primary skill (or none); inspect whether it actually loads the skill when evaluating native discovery. A model returning the correct label is a semantic-routing smoke, not proof of host integration.

Mixed requests may need a second skill. The fixture's primary scope must not suppress other user requirements. Disagreement is reviewed for ambiguity before editing a description. Do not turn all skills into broad catchalls just to raise recall.

The dependency-free runner prepares label-free input and scores saved predictions (it does not call a model):

```sh
python3 scripts/score_routing.py prepare evals/routing-cases.json
python3 scripts/score_routing.py score evals/routing-cases.json /path/to/predictions.json
```

Predictions must include every neutral case ID exactly once with `primary` as a skill name or explicit JSON null. Missing negative cases do not earn credit. Exit 0 means all routing labels matched, 1 means mismatches, 2 means invalid/incomplete input. None of these exits measures product quality.

## Behavioral fixtures

The local booking app has buggy/fixed modes. Both expose the same user task and normal shape; the grader independently checks saved state. Do not disclose fault location during the first black-box pass. The runtime tests verify the fixtures, not the agent's discovery ability. Published source fixtures are development cases, **not an unseen benchmark**.

Offline reasoning tasks also cover partial AI completion, changed requirements, artifact-only anomalies, invalid graders, empty evidence and uncertainty after a write. Record when the agent only interpreted supplied evidence and did not execute product actions.

The second development lab, `scripts/boundary_lab.py`, is specified in [boundary-task](../evals/boundary-task.md). Its denied-write/owner-readback contrast tests whether the tester follows the side effect rather than trusting the HTTP status. For a blind trial provide the task and running URL, not the lab source or expected variant. [State contracts](STATE-CONTRACTS.md) add executable checks for protected fields and object identity; fixture tests do not prove an agent will collect correct snapshots.

## Adaptive lead controls

[lead-routing-cases.json](../evals/lead-routing-cases.json) records open development expectations for mid-task method selection, installed external skills, actual worker capability, shared-state isolation, context-only review and stopping. Keep its `expected` fields away from the tested agent. These cases are not an executed-coverage claim.

Freeze the task, evidence, catalogue and allowed capabilities before comparing a prior package with a candidate. Use fresh processes and preserve every attempt. Inspect the actual body reads and their order relative to new observations; separate a method mentioned in prose from a method loaded, and a batch read from evidence-triggered selection. Count only actual native dispatch/return events as worker execution. Check the lead's final evidence reconciliation rather than a promise to delegate.

Include a small healthy frontend/API control and a missing-role/tool fallback. Zero workers can be correct; a catalogue entry alone does not justify loading a skill. Grade correct product conclusions separately from routing observations so an equally good inline analysis is not falsely labelled a product failure. A named skill still does not prove that its applicable checks were followed. Explicit-catalogue offline probes do not establish native implicit discovery or live browser/API execution.

## Fair comparison before public claims

- Same substantive task, model, tools, permissions and initial state; baseline gets a competent request, not a straw man.
- Arms: base agent; incumbent QA skill; Outcome QA; a selected relevant competitor. Run host-specific adaptations separately rather than silently giving one arm extra tools.
- Develop on visible fixtures, then freeze new held-out variants not used to write the skills. Keep their oracle away from the agent; source tests should not reveal fault labels in the accessible workspace.
- Use repeated fresh sessions. A three-trial pilot reveals some instability; it does not establish statistical superiority or generalization.
- Include healthy controls. Always answering BLOCKED is not good QA. Missing a required step is a coverage gap, not permission to infer the final outcome.
- Grade defect detection and false positives, unsupported PASS/FIXED, justified coverage, evidence reproducibility, data preservation and cleanup. Report time/cost secondarily.
- Wrongly attributing a response to another person/question, skipping a negative branch, or accepting a failed provider output as a baseline must be testable failures, not style scores.
- If mutation is used, the unchanged test must fail on the intended product behavior. Syntax/import/setup failures are invalid mutants, not caught defects.
- Host/model/rubric changes require fresh applicable results. Keep failed attempts; no cherry-picking the best run or rewriting the baseline to match the candidate.

Initial acceptance: no unsupported PASS/FIXED on the declared trap set, healthy controls accepted, critical requirements executed or explicitly untested, no regression versus the incumbent in verified detection/false positives. These are bounded acceptance criteria, not a universal guarantee.

## Private research and public data

The author reviewed historical QA requests from multiple projects. Only generalized mechanisms belong here. Private chat IDs, internal URLs, credentials, names and raw transcripts must stay outside the release. The package has no telemetry or automatic corpus upload.

## Pressure controls before and after a method change

Freeze task inputs, expected obligations and healthy/negative controls before editing the method. Run a documented baseline (prefer a genuinely skill-disabled host or a pinned prior release), preserve its raw responses/attempts, then apply the candidate under comparable conditions. Verify actual skill reads from traces; a parent saying it used a skill is not sufficient.

Pressure examples: deadline-driven demand for PASS despite a failed terminal job; zero collected tests; invalid 404 fix fixture; 500 promoted to injection; discarded first intermittent failure; realistic design-only utterances; a tiny task inflated into a full audit. Inspect both dishonest certainty and useless refusal/over-cautious non-execution.

A baseline that already passes leaves no observed improvement on those cases; it does not forbid a readability, portability or UX fix. One trial is a smoke, not reliability or causal improvement. Repeated matched trials and frozen held-out cases are needed for a quality claim. Preserve failed setup/provider runs as invalid experiments, not model failures or clean passes.

Record model/host/config and limits. A second model family or smaller model is an additional experiment, not assumed compatibility. Never fill its row without an actual supported run. If the requested model/provider is unavailable, retain an explicit untested row rather than silently substituting another model.

## Trace review and style checks

Inspect actual reads, tool attempts, error recovery and result construction. Repeated reads may indicate over-prescription, but also truncation, a tool failure or changed state; establish the cause before cutting necessary constraints. Count entrypoint words as a maintenance budget, not a quality score. Worked examples are illustrative until a real run produces evidence.
