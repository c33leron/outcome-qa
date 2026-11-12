# Verify the change—and what must stay unchanged

A useful QA check asks two questions: **did the intended result happen, and did anything else change?** Outcome QA's local state-contract helper makes those before/after rules executable.

A text correction should not change its author or budget. A rejected write should leave the owner's object intact. Repeating a confirmation should not duplicate the effect. A successful response alone answers none of those questions.

## Try a synthetic example

From the **source checkout root**, with Python 3.10+:

```sh
python3 scripts/check_transition.py check --before examples/transitions/before.json --after examples/transitions/healthy.json --contract examples/transitions/contract.json --format json
```

Use `py -3` instead of `python3` on Windows. The healthy snapshot yields `PASS`, exit 0. Replace `healthy.json` with `corrupted.json`: the requested text is correct, but the budget also changed, so the result is `FAIL`, exit 1. `wrong-object.json` refers to a different entity and yields `INCOMPLETE`, exit 2—not a product bug or a pass.

These examples are source fixtures. They are intentionally excluded from the install bundle; when working from the runtime, supply your own snapshot and contract paths.

## Apply it to a real check

1. Derive the action, expected change, protected fields and stable entity identity from the requirement. Include owner/tenant identity when a bare object ID is ambiguous.
2. Capture the initial state through a trustworthy read-back. Perform the user action through the channel you are testing; the helper executes no UI or API action.
3. Independently read the saved state at the same level and with the same completeness. Wait for the defined async completion condition. A premature snapshot is not evidence that a save was lost.
4. Compare the snapshots with the contract. Use `unchanged` for a protected value; combine `equals` with `only_changes` when one intended field may change. Permission to change is not a requirement to change.
5. Retain the underlying evidence in an appropriate private workspace. The helper reports rule IDs and outcomes, not state values; input snapshots can still contain sensitive data.

## Contract operations

The machine-readable contract is [transition.schema.json](../schemas/transition.schema.json).

| Operation | Check |
|---|---|
| `equals` | The post-action value matches the expectation |
| `unchanged` | A value is identical before and after |
| `length_delta` | An array length changes by the specified integer |
| `only_changes` | No change in the supplied state falls outside the allowed JSON pointers or their subtrees |

Identity guards establish that both snapshots represent the intended entity. JSON pointers follow RFC 6901 (`~0` means `~`, `~1` means `/`); the root pointer is unsupported. Adding or removing a key counts as a change. An array-length change counts as changing the array, not as business-ID matching between its elements.

Booleans are distinct from numbers. Numeric comparison is exact in the JSON/Python representation, without tolerance. Use agreed precision or minor units for money and an explicit business timezone for dates.

## Outcomes

| Outcome | Meaning | Exit |
|---|---|---:|
| `PASS` | The supplied snapshots satisfy all specified checks | 0 |
| `FAIL` | A specified rule is violated with sufficient input | 1 |
| `INCOMPLETE` | Required input is missing or entity identity does not match | 2 |
| `FAIL_WITH_GAPS` | A known rule violation exists alongside missing input | 2 |
| `INVALID` | Malformed contract/input, unknown operation, duplicate JSON keys or non-finite numbers | 3 |

A missing field can mean that the product removed it **or** the collector omitted it. `only_changes` can identify removal in comparable, complete projections; a missing path alone does not establish that product bug. Fields omitted from both snapshots are invisible to the comparison.

The helper verifies supplied state constraints, not evidence provenance, snapshot completeness, execution of a UI action, natural-language AI meaning or the correctness of the requirement. Pair it with the real journey and independent read-back; do not replace those with a well-formed JSON file.

See [Evaluation](EVALUATION.md) for healthy/faulty controls and [Third-party notices](../THIRD_PARTY_NOTICES.md) for provenance.
