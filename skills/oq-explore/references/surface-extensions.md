# Small surface checks, selected by the task

These lenses extend ordinary acceptance; they are not a claim of exhaustive accessibility, localization or performance certification.

## Accessibility: a usable route, not just a scanner score

Use POUR as a reminder: **Perceivable, Operable, Understandable, Robust**. Select the relevant interaction: meaningful labels/error messages, keyboard reachability and focus order, visible focus, recovery after dialogs, and appropriate announcement of state changes. For a requested screen-reader smoke, run the actual supported assistive technology and record its output/behavior; inspecting ARIA markup alone is not that run.

Use the project's declared accessibility target and applicable current guidance when assessing conformance. A healthy automated scan is useful evidence for its rules, not proof of complete accessibility. A missing required runtime remains an explicit gap.

## Locale and text

Choose supported locale combinations from the contract. Compare display and submitted values for date/timezone, decimal/grouping separators, currency units and translated validation. Use realistic names/text and the [human data pack](_shared/human-data.md) to select Unicode, copy/paste, long-content and RTL/bidi cases. Check mixed-direction labels and identifiers in their actual context rather than treating every direction marker as a bug.

A normalized value may be correct if the contract requires it; record the rule before rejecting NFC/NFD changes, transliteration or formatting. Select stateful cases such as changing locale with a populated draft when relevant.

## Performance as a product promise

Establish the actual response/interaction budget or an agreed baseline and observation window. Record environment, payload/data size, cold/warm state, sample count and relevant timing boundaries. Separate accepted, first visible response and completed useful outcome.

A short isolated probe can expose a slow interaction or recovery failure. It does not establish load capacity, a stable percentile or production performance. Load, stress, sustained concurrency and fault injection need a separately scoped plan; routine QA does not expand into a denial-of-service exercise.

For an observed delay, ask whether the UI communicates progress, cancellation/retry is safe, and the operation eventually leaves the correct state. Latency alone does not explain its root cause.
