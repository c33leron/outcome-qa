# Keep the whole requested scope visible

Use this for a batch of tasks, a large feature or multiple requirement sources. A narrow check can keep the same reasoning in conversation.

## Establish what “all” refers to

- Identify the selected tasks and material acceptance criteria by stable IDs or unambiguous labels. Read the next page/cursor when the source is paginated; check whether a tool truncated the document or only returned a search excerpt.
- Distinguish the complete selected set from the subset currently available. If twelve tasks are requested but only five have been retrieved, five completed checks cannot establish acceptance of twelve. Continue useful work without disguising the retrieval gap.
- Resolve duplicate, superseded and changed requirements before counting them. Owner acceptance with disclosed gaps, board status and a completed QA check are different facts.
- Keep requirements from different roles, environments or versions separate when the difference affects behavior. Do not merge similar titles into one entity.

## Connect rules to observations

For each material rule, record the relevant check and its current outcome: executed with evidence, partial, blocked, not run or unresolved expectation. Several checks may cover one rule; one check may support several rules only when its observation actually establishes each. Case count alone is not coverage.

For stateful work, keep a short outcome contract:

> Actor / entity → intended action → what may change → what must remain → allowed effect count → independent observation.

Example: replacing one item may change its ID, description and total price, but must preserve the selected neighboring items and the user's budget rule. A success toast is not evidence for all these properties.

Do not manufacture a percentage when the denominator is unknown. If scope changes, preserve the original selection and identify the newly included/excluded requirements; do not silently shrink the denominator until the report is green.

## Optional full-plugin result helper

When the full Outcome QA plugin and Python are available, the read-only [result helper](../../../scripts/qa_result.py) checks a saved report against its [schema](../../../schemas/run.schema.json), local artifact hashes and declared completeness. Resolve `../../scripts/qa_result.py` from the skill directory that contains this `SKILL.md`, not from the user's project working directory. Use its resolved absolute path:

```sh
python3 <resolved-helper-path> check <authorized-run-report.json> --format json
```

For a known set of required checks, `scope.required_check_ids` can declare their IDs. A missing required check remains a gap instead of disappearing from the total. This is only a declaration: the helper cannot discover omitted requirements, certify the chosen checks or establish the truth of their observations. Without an explicit inventory, the result covers only the reported checks.

Check that the helper and schema actually exist before using them. A standalone skill installation or a pasted playbook may not include either; continue with a clear conversational coverage record rather than claiming helper verification or installing a new framework automatically. Missing Python blocks the helper, not independent QA work.

## Optional state-transition checker

For a stateful claim with authorized before/after JSON object snapshots, the full plugin's [transition checker](../../../scripts/check_transition.py) can compare explicit constraints. It executes no product actions:

```sh
python3 <plugin-root>/scripts/check_transition.py check --before before.json --after after.json --contract contract.json --format json
```

A minimal contract binds the entity in both snapshots and names the intended change and protected state:

```json
{
  "version": 1,
  "goal": "Change one record's text without changing its budget",
  "identity": [{"path": "/record/id", "value": "note-1"}],
  "rules": [
    {"id": "only-requested", "op": "only_changes", "paths": ["/record/text"]},
    {"id": "new-value", "op": "equals", "path": "/record/text", "value": "desired"},
    {"id": "budget-stable", "op": "unchanged", "path": "/record/budget"}
  ]
}
```

`only_changes` compares the supplied snapshots except the listed subtrees; use equivalently complete projections. An `equals` rule checks the after-value, `unchanged` compares both, and `length_delta` with a `path` and integer `delta` checks a collection's count change. These rules do not establish semantic correctness or exactly-once behavior beyond the observed data.

A missing/mismatched identity or unavailable rule data is incomplete evidence, not a wrong-object PASS/FAIL; known mismatches remain visible alongside gaps. Any PASS is limited to these snapshots and selected constraints, not their authenticity, live persistence or data omitted from them. Without the helper, make the same bounded before/after comparison directly; do not claim a machine check.
