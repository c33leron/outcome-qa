# AI behaviors across the product boundary

Select behavior from the feature's promise, with a healthy control and synthetic source/session whose expected result is independently known. This is not a mandatory benchmark. Use the shared [decision loop](_shared/decision-loop.md) when a new observation needs another check or method; preserve the original semantic question.

## Streaming and cancellation

Follow one generation/operation ID through request acceptance, visible partial output, completion/cancellation, tool work and saved state. Distinguish a streaming transport event from the user's finished result.

| Situation | Controlled variation | Observe |
| --- | --- | --- |
| Partial rendering | Use a known multi-part response and interrupt at an observable boundary | Text remains associated with the correct message; incomplete output is represented as incomplete according to the product rule |
| Chunk order and retry | Delay or replay a chunk in an authorized controlled fixture | No duplicated/lost content or stale generation replacing the current one; preserve chunk IDs/order where exposed |
| Stop button | Stop after partial output but before contractual completion | Button response, upstream cancellation/terminal reason if observable, retained text and saved status agree with the promised cancellation semantics |
| Late completion | Start a new intent after stopping the old generation; observe a delayed old response | The old completion does not overwrite the newer conversation/entity contrary to the ordering rule |
| Tool work around cancellation | Cancel near an approved synthetic tool action | Establish whether the action was pending, already committed or prevented; inspect post-state before retrying or claiming rollback |
| Broken transport | Interrupt the stream while the worker may continue | Separately observe client presentation, worker terminal state and persisted result; a disconnected UI does not establish backend cancellation |

Preserve raw output and returned stop/error metadata; if absent, leave the finish reason unknown. Controlled fixtures establish modeled behavior, not production frequency. A final refusal cannot undo an earlier write. For async/media localization use [incident tracing](_shared/incident-tracing.md): runner completions, connected calls, transcripts and persisted reports are different outcomes.

## RAG and source grounding

Use a small approved corpus with stable document/chunk IDs and a known answer location. Test an answerable question, an absent fact and a deliberately conflicting source pair whose authority/date rule is specified.

- Inspect retrieved chunks and their relevant versions when the system exposes them. A plausible answer is not proof that the expected source was retrieved; absence of retrieval traces limits cause attribution.
- Tie each claim or literal quote to its actual chunk and entity. A citation can exist yet support a different person, date or exception.
- Preserve exceptions, source uncertainty and known authority rules. If two sources conflict without a resolution policy, require qualified uncertainty or clarification rather than silently preferring the newest-looking filename.
- After a document correction, inspect the promised indexing/visibility boundary and the answer's evidence. Respect the documented freshness window; a prematurely queried index is not automatically a failed update.
- Separate retrieval failure, unsupported generation, parser/mapper corruption and wrong saved/UI output. A mock retrieval replay cannot certify the live vector store.

Tenant/data-isolation probes are a separate scoped security obligation. Use owned corpora and canaries; keep private documents and expected labels out of public artifacts and model inputs unless genuinely required by the authorized test.

## Timing and cost as observable requirements

Establish the actual budget and definition: request-to-first-visible-content, terminal completion, token usage, provider spend or application charge. Record units, retry count, caching and the measured boundary. Report provider-supplied usage as supplied telemetry, not independently audited billing.

Compare equivalent cases/configurations, keep errors in a separate count and state sample size. A fast first token does not prove fast completion or useful output. Unknown budgets remain observations/questions; a single sample cannot establish a general percentile or cost advantage.

## Synthetic worked path

A user says “stop, keep the draft.” The UI stops rendering, but a permitted tool has already created one synthetic draft. Correct evidence distinguishes the stopped display from that committed effect, reads its ID/state, and follows the agreed retain/remove policy. Blindly resending would risk a second draft. This is an illustrative expected investigation, not a recorded product run.
