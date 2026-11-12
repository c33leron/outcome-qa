# Fault models: choose a useful next question

After a healthy path, pick a plausible mechanism that could defeat this product promise. A model is a source of candidates, not a guarantee of bugs. Keep the next probe bounded and preserve the healthy control.

| Surface | Candidate failure | Small distinguishing check / observation |
| --- | --- | --- |
| Frontend | Old request overwrites newer intent | Reverse controlled response order; correlate input/request/entity and final visible/submitted state |
| Frontend | Optimistic success never persists | Observe a genuine failed write; reopen the same object and check scoped rollback |
| Frontend | Paste/blur/composition misses submitted state | Compare authentic input paths; inspect transmitted value, not just the label |
| Frontend | Overlay/focus/layout changes the target | Continue the real interaction at the affected viewport; identify the activated entity |
| Backend | Rejected batch commits a subset | Include one invalid item among valid owned data; read all affected records against the atomicity contract |
| Backend | Retry duplicates an irreversible effect | Repeat one logical operation under the specified key/history; compare durable effect count |
| Backend | Patch erases neighbors or read models disagree | Exercise omitted/null/empty distinctions; compare relevant projections within the promised consistency window |
| Backend | Delete leaves an invalid dependent object | Delete a disposable parent only when authorized; inspect the documented retain/cascade/reject policy and dependent read paths |
| Backend | Pagination/update race loses or duplicates data | Traverse stable IDs under the permitted consistency model; compare bounded concurrent writes only when in scope |
| AI | Negation, attribution or correction changes meaning | Compare input facts with raw, mapped and saved output; preserve unrelated facts |
| AI | “Complete” hides truncation or a late tool effect | Follow stop/cancel metadata and final state; a refusal after a write cannot undo it |
| Access | UI hides control or 403 follows a completed mutation | Use the valid permitted actor control and protected-state read-back after the challenged action |

For methods rather than another checklist, open only the relevant detail: [frontend state](frontend-state.md), [API/state](api-and-state.md), [outcome tracing](outcome-tracing.md), or [human journeys](human-journeys.md). Choose another question when the observed mechanism contradicts the first hypothesis. Record actual behavior even when the candidate is disproved.
