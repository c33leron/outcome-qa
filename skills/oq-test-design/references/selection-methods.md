# Select checks from the rule, not a case quota

Read only the applicable sections. These methods produce a proposed test set; they do not execute it or establish product correctness.

## Technique names and their use here

| Common name | The decision it helps make |
| --- | --- |
| Equivalence partitioning | Choose inputs that represent different specified behavior |
| Boundary value analysis | Separate just-below, at and just-above behavior in the right unit |
| Decision-table testing | Cover meaningful combinations of business conditions |
| State-transition testing | Check allowed, forbidden, interrupted and repeated transitions |
| Risk-based testing | Spend effort where an incorrect outcome matters most |
| Pairwise / combinatorial selection | Reduce independent variants while retaining known risky combinations |
| Error guessing / fault models | Turn experience of failures into a testable hypothesis, not an assumed bug |

## Inputs and boundaries

Partition inputs by the product decision they should cause. A valid typical value and a different valid representation may reveal normalization behavior; ten arbitrary valid strings usually add little. Keep missing, explicit null, empty string, whitespace, zero and false separate when the contract assigns different meanings. Do not assume that a numeric string must be accepted or rejected without a type contract.

For a stated inclusive limit, select just below, exactly at and just above it using the correct unit and precision. A calendar-day boundary uses the business timezone and calendar rule, not an assumed 24-hour duration. An apparent boundary with an unrelated invalid field does not isolate the rule under test.

## Combined conditions

For eligibility, permissions or dependent validation, write the conditions and promised outcomes before choosing inputs. Enumerate the materially different decision rows; collapse rows only when the same specified decision and relevant risk remain covered. Mark impossible combinations with their actual constraint rather than generating unusable cases.

For example, when a discount requires an active promotion, an eligible basket and no prior redemption, include the allowed combination and cases that independently make each condition false. If the contract also forbids combining discounts, retain that joint-condition case: covering the individual conditions does not cover the interaction.

Pairwise selection can reduce a large set of independent dimensions such as supported browser, viewport and locale. It is not proof of complete behavior and does not replace known three-way interactions, permission boundaries, required decision rows or a critical business combination. Record what the reduction leaves out.

### A small pairwise selection procedure

List the relevant factors and allowed values, then remove impossible combinations using explicit constraints. Retain required/high-risk cases first. Mark the feasible value-pairs they cover; add a case that covers useful remaining pairs, and verify the final pair ledger. A generator can help with large sets, but its output still needs constraint and oracle review.

For two browsers, wide/narrow viewports and EN/RU locales, this small proposed set covers every pair:

| Browser | Viewport | Locale |
| --- | --- | --- |
| Chromium | Wide | EN |
| Chromium | Narrow | RU |
| Firefox | Wide | RU |
| Firefox | Narrow | EN |

It does **not** include Firefox + Narrow + RU. If that three-way combination has a known layout defect or a required business flow, add it explicitly. Pair coverage describes this selected factor model, not whole-product coverage; invalid combinations or missing factor levels can invalidate the apparent reduction.

## States and sequences

Identify the relevant states, allowed transitions, rejection behavior and irreversible effects. Design a normal transition, a meaningful forbidden or out-of-order transition, and a correction/retry/interruption path where the requirement exposes one.

Distinguish “request accepted” from “operation completed”. Define the observation that ends the check: terminal operation state, persisted entity, delivered synthetic notification or another contractual outcome. An arbitrary sleep is not an oracle. If timing or eventual-consistency tolerance is unspecified, retain the question rather than inventing a deadline for failure.

## Coverage and oracles

Maintain the link **requirement → risk → scenario → observable outcome** at the scale the task needs. Do not count planned checks as executed, hidden pages as inspected or a shared assertion as coverage of every requirement it mentions.

Prefer independent read-back for consequential writes. State which fields may change and which must not. For a meaningful negative test, preserve the valid preconditions except the challenged rule; otherwise a generic rejection may happen before the intended boundary.

When two cases appear redundant, compare their actor, starting state, decision, effect and observation before merging. A second endpoint exposing the same object can have a different authorization or projection risk; two differently worded descriptions of the same input class may be true duplicates.
