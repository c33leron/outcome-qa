# Human journey lenses

Choose a lens because it challenges a product promise. These are candidate actions, not requirements that every product must implement.

| Lens | Useful variation | What distinguishes a real result |
| --- | --- | --- |
| Input method | Type, paste, autofill, edit an existing value, press Enter | Visible value, validation and transmitted value agree |
| Isolated constraint | Violate one documented rule while the others remain valid | The intended rule—not an unrelated invalid field—causes rejection |
| Meaningful boundary | Just below, at, just above a limit; dependent field combination | Expected behavior follows the actual rule, including null/empty/absent distinctions |
| Business time | Just before/at/after a business-day boundary, expiry or calendar transition | Use the product's timezone and calendar rule; a calendar day is not automatically a 24-hour duration |
| Numeric meaning | Relevant precision, rounding, units and quantity boundaries | Compare using the declared monetary/measurement rule, not an invented float tolerance or assumed display rounding |
| Uncertain feedback | Timeout or delayed acknowledgement, then inspect before retry | Determine whether zero, one or multiple durable effects occurred |
| Changed intent | Replace only one selected item; cancel a dependent choice | Requested value changes; unrelated user constraints survive |
| History | Back/Forward, deep link, reopen, stale tab, old draft | Displayed entity and the entity used by the next action are the same |
| Interrupted gesture | Cancel file picker, abandon drag, blur while editing | No unintended commit; recovery follows the promised draft policy |
| Interrupted operation | Leave during processing, reconnect, resume | Partial completion and recovery are observable; retries do not silently duplicate effects |
| Existing data | Edit a populated record, import into a nonempty collection | Old facts and ownership are preserved unless the contract says otherwise |
| Multiple actors | Two authorized test actors or two stale views | Conflict policy is respected without cross-account contamination |
| Accessibility | Keyboard reachability, focus recovery, error announcement | A usable route exists for the required interaction; tree presence alone is insufficient |
| Visual interaction | Overlay, responsive layout, loading shift, long content | A person can identify and activate the correct control |
| Native/mobile | Keyboard open, app background/return, supported rotation | Verify on the required runtime; label emulation separately |

Choose a persona by relevant **state and context**: a new user with no records, a returning user with a saved draft, a user with stale permissions, conflicting saved values, or an interrupted previous operation. Those states change the next meaningful action. Age, gender or an invented personality alone does not specify a failure mechanism.

“After an unclear response, a user retries the same order” is a concrete sequence; random clicking is not. Use [realistic human data](_shared/human-data.md) to make inputs believable while retaining safe synthetic ownership and independent read-back.

## An executable charter, not a long plan

Use a compact form when the work warrants it:

> A user with [relevant existing state] wants [outcome]. After [plausible sequence or interruption], [source of expected behavior] requires [effect and preserved invariants]. Observe through [UI and authorized independent result].

For example, a reservation editor may promise to retain a selected slot after a date correction. Compare typed and pasted corrections; submit through the real control; reopen the saved reservation. If the request already contains the old date, investigate the input/state boundary before speculating about the database.

For a broad feature, record must-check risks, optional extensions and omissions. For a small question, use this reasoning without producing a ceremonial document. If a requested check is impossible, identify the missing capability and continue independent permitted checks.

## HTSM-inspired blind-spot scan

For a broad feature, James Bach's [Heuristic Test Strategy Model](https://www.satisfice.com/download/heuristic-test-strategy-model) suggests looking beyond the easy visible path. The following questions are an original compact application, not a reproduction of the model:

- **Project context:** which access, environments, time or dependencies constrain useful testing?
- **Product:** which structure, data, interface, platform, operation or time-dependent state can affect the goal?
- **Quality:** which consequences matter here—correctness, recoverability, usability, accessibility, isolation or responsiveness?
- **Technique:** which concrete variation or observation would expose a failure in that combination?

Select a few consequential combinations; an exhaustive cross-product is neither required nor implied. A discovered blind spot becomes a planned check or an explicit gap, not retroactive coverage.

For a timeboxed session, retain a three-line debrief: **charter/timebox and actual elapsed time**; **what design, execution and bug investigation actually occurred**; **findings, gaps and next discriminating check**. Record measured effort only when it was measured. The timebox is a stopping aid, not a requirement to invent bugs before it ends.
