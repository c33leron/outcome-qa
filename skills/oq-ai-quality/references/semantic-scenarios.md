# Semantic scenarios with observable invariants

These generic examples illustrate test design, not universal expected answers. Bind the invariant to the actual product contract before execution.

| Situation | Controlled variation | Expected invariant to establish |
| --- | --- | --- |
| Fact correction | “The appointment is Tuesday—actually Wednesday.” | The corrected day replaces the old day for that appointment, not for other appointments |
| Partial update | Replace the oven, keep the refrigerator and spending limit | Unchanged item IDs/constraints survive the update |
| Negation | “I have not used this library.” | Absence of experience is not rewritten as experience |
| Multiple people | Two people share an employer but have different roles | Each role stays attached to its actual person |
| Multiple questions | A clarification belongs to a later question | Stored answer/range does not duplicate it into an earlier question |
| Unknown information | A document omits the shipping date | Omission or qualified uncertainty, not an invented exact date |
| Source grounding | A source contains an exception to a general rule | The exception remains applicable to the relevant case |
| Equivalent wording | Rephrase an acceptable answer without changing meaning | Quality verdict stays acceptable unless literal wording is required |
| Changed intent | Switch from purchase to comparison before confirmation | No purchase side effect; the new intent governs subsequent behavior |
| Repeated request | A delayed result arrives after a retry | Effects follow the promised idempotency/order policy |
| Interrupted session | Resume after reconnect with an existing draft | Correct actor/session and relevant facts survive; no old reply overwrites newer state |

## Make defects observable

For each case distinguish:

- Input fact and its owner/reference.
- Permitted semantic alternatives.
- Specific contradiction, unsupported claim or state change that would fail.
- Observation boundary: answer text, parsed field, executed action or saved object.
- Healthy control and the smallest meaningful corrupt counterpart.

An answer can be stylistically poor without violating a functional requirement. Separate usability/style concerns from supported factual or business failures. For open-ended answers, do not invent a single canonical phrasing.

Where a relationship should stay stable, a metamorphic pair can help: reordering unrelated source paragraphs should not swap people; correcting one field should not erase another. The expected stability itself needs justification—some ranking or temporal changes legitimately affect multiple outputs.

## Talk to it like a person

Use these synthetic utterances with a known context and a normal-language control. Their purpose is a semantic variation, not demographic roleplay or a requirement that every product accept every style. Choose relevant rows; preserve the application's actual supported languages and actions.

| Human input | Meaning to test | What must stay true |
| --- | --- | --- |
| “я не работал с Kafka. вообще” | Informal emphatic negation | Lack of experience stays attached to this person; topic-word presence does not become experience |
| “на вт… нет, на ср. время то же” | Mid-message correction | Only the intended appointment day changes; preserve time and other appointments; resolve the calendar date if necessary |
| “перенеси второй. тот, что после обеда” | Fragmented reference | Resolve a unique known appointment or ask; ambiguous wording must not select a random object |
| “отчёт ок, salary не меняй” | RU/EN field restriction | Accept the permitted report change while preserving the existing salary |
| “ну так что??” | Impatient follow-up during work | Report current operation state; repeating the question must not silently create another operation |
| “давай другой. стоп, ничего не покупай” | Changed intent followed by cancellation | Apply the contract's ordering/confirmation rule; distinguish prevention from an already committed purchase |
| “зп 150… не, 180 тыс” | Correction plus abbreviated units | Use the corrected amount for the intended field; resolve missing currency when required |
| “а Марина это говорила или Илья?” | Attribution challenge | Check the named speaker/source; do not merge facts from similarly situated people |
| “без сахра, пожалуйста” | Typo in a constraint | Where supported and unambiguous, preserve the intended exclusion; clarify genuine ambiguity |
| “среда” | A word without context | Ask what action/entity/date is meant when context cannot resolve it; do not invent a booking |
| “покороче, но все исключения оставь” | Summarization with preservation constraint | Shortening retains material exceptions and their applicable entities |
| “скинь ещё раз” | Repeat delivery versus repeat business action | Re-present an existing result when that is the intent; clarify before repeating an irreversible action |
| “I didn't say cancel, только дату поменять” | Code-switching and denial of an action | Preserve the object and change only the agreed date; do not cancel it |
| “не всё — только первый пункт” | Narrowed scope in a follow-up | Apply the correction to the intended first item and retain unrelated items/constraints |

Capture raw utterances, resolved references and resulting saved fields when execution is in scope. A polite paraphrase can be correct; a polished answer with changed facts is not. Designed dialogue rows remain unexecuted until the relevant product path actually runs.
