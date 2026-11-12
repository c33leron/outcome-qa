# Find a defensible expectation

When the specification is incomplete, use several sources to discover a useful question. Record which source supports the expectation and how applicable/current it is. A heuristic identifies a candidate problem; a difference from a competitor is not automatically a violated requirement.

## FEW HICCUPPS: prompts, not commands

James Bach's oracle work, extended by Michael Bolton, is summarized by **FEW HICCUPPS**. The primary account explicitly treats these heuristics as fallible and context-dependent. These short prompts are independently written, not a reproduced checklist:

| Cue | Question to investigate |
| --- | --- |
| Familiarity | Does this resemble a previously understood failure mechanism? |
| Explainability | Can we account for the observed transition? |
| World | Are represented dates, quantities or relationships plausible? |
| History | What changed from an applicable previous behavior? |
| Image | Does this undermine a documented product promise? |
| Comparable products | What alternative behavior might expose a useful question? |
| Claims | Which actual statement promises this outcome? |
| Users' desires | What observed user need is being defeated? |
| Product | Do related parts apply the same relevant rule? |
| Purpose | Can the person accomplish the intended goal? |
| Statutes and standards | Which verified external rule actually applies here? |

Source: [Michael Bolton, FEW HICCUPPS](https://developsense.com/blog/2012/07/few-hiccupps/). Statutes/standards require actual applicability and current authority; a remembered convention is not a legal or compliance conclusion.

## Turn a suspicion into a check

1. State the discrepancy and the candidate expectation with its source.
2. Seek a counterexample: changed requirement, different role, locale, data or lifecycle stage.
3. Choose the smallest comparable observation that separates those explanations.
4. Report a requirement-backed violation when established; otherwise preserve the observation as an issue/question or risk and name the deciding evidence.

Example: another booking app preserves the chosen time after a date edit. That gives a hypothesis, not a bug in this app. Check its actual date/time rule and the user's selected slot. If the contract promises preserving that slot and read-back shows a different slot, the report now has an applicable basis. If the product deliberately requires reselection, evaluate whether that requirement is communicated rather than demanding the competitor's behavior.
