# Give a release recommendation with visible limits

Use only when asked about release readiness, broad acceptance or a go/no-go recommendation. A recommendation is not permission to deploy, merge, change a tracker or waive an acceptance criterion.

## Build the decision from evidence

- Identify the release/build, selected scope, support variants and agreed release criteria. Check changed requirements and superseded evidence.
- Include a healthy smoke through the critical user journey and its promised final effect. A login or health endpoint alone is not a substitute for checkout, delivered message, completed report or whichever outcome matters.
- Reconcile each critical criterion with executed evidence, a known defect, a blocked check, an explicit omission or an unresolved expectation. Check pagination/truncated requirements before calling the map complete.
- Surface material requirement questions before closing the affected item. Report which check passed and which decision remains open. An unanswered acceptance question prevents a ready recommendation for the affected scope.
- Keep reproduced blockers and meaningful regressions visible even when neighboring tests passed. State mitigations/workarounds only where observed or clearly proposed.
- Check restoration of test data and any uncertainty after writes. Distinguish remaining test residue from product defects.

Give one scoped recommendation: **ready for the tested scope**, **not ready because of named blockers**, or **insufficient evidence pending named checks**. A product owner may explicitly accept a known risk; report that decision separately from QA completion. Missing evidence does not become green because the release is urgent.

## Useful metrics without invented denominators

- **Coverage:** map selected obligations to evidence; show unavailable requirements and omitted support variants. A case count alone cannot express total product coverage.
- **Flake rate:** define the run population, comparable conditions and classification rule before counting inconsistent outcomes. Preserve first attempts and retries; retry success is not a fix.
- **Escaped defects:** define release/time window and which later-confirmed defects belong to it. Without reliable detection/reporting populations, report counts and examples instead of a misleading percentage.

## Example

“Not ready for the requested checkout release: duplicate submission creates a second order in the tested build. Normal payment and receipt delivery passed. Mobile Safari is untested because the required device is unavailable. Retry suppression is a proposed mitigation, not a verified fix.”

This example is wording, not a recorded execution. Link actual requirements and observations when using the format.
