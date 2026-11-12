# Frontend state and interaction lenses

Use the relevant lens when browser state, event order or rendering affects the user promise. This is not a requirement to throttle every request, test every browser or run every row for a simple form.

| Observed mechanism or risk | Discriminating interaction | Check the actual outcome |
| --- | --- | --- |
| Async search, filters or dependent fields | Make an earlier request complete after a later one using an authorized controlled delay, or preserve an observed occurrence | The visible result, selected stable ID and next submitted action belong to the latest valid intent; an old response must not restore a discarded choice |
| Optimistic update | Change one disposable entity, then observe a genuine rejected/failed request and recovery | The pending display resolves according to the contract; rollback must not revert another entity, a later successful edit or unrelated fields |
| Composition and validation ordering | Use a supported real IME/composition path, then blur or submit at the relevant boundary | Committed text, visible validation and transmitted value agree. Keyboard events, bulk `fill` and actual composition are different execution paths |
| Focus after modal/list change | Open and close the relevant dialog, or change a list while focus is inside it; continue by keyboard | Focus remains usable and the next action targets the intended entity, not merely the same row position or a hidden control |
| Loading, empty, error and retry states | Reach the specific state with a valid fixture, then use the offered recovery action | Actions are reachable only when valid, retry refers to the right operation, and feedback does not conceal stale or duplicated results |
| Responsive layout, zoom or long content | Exercise the required viewport/zoom/content variant through real controls | Critical content and controls remain discoverable and operable; overlays, sticky regions or shifted layout must not redirect the action |
| Navigation and stale UI state | Return through history, reopen a deep link or restore a draft after the relevant entity changed | Displayed identity and submitted identity agree; stale local state must not silently overwrite newer values contrary to the conflict policy |

Correlate input, request identity, response order and rendered/submitted state before assigning a cause. The presence of a pending request is not proof of a race, and a console warning is not automatically the user's failure. Preserve a successful control on the same runtime and fixture.

If fault injection or request stubbing is used, describe it as a controlled frontend/integration probe. It can establish behavior under that modeled failure; it does not show that the deployed backend naturally produces the injected error or timing. Do not patch application state, dispatch artificial success events or force a covered/disabled control and then claim the real user path works.

When browser tooling cannot produce an authentic input path such as IME composition, mark that path untested or use a suitable permitted runtime. A synthetic event test may support a component finding, but is not proof of real OS/browser input behavior. Likewise, viewport emulation does not prove a mobile keyboard, touch gesture, Safari or physical-device result.

Inspect the rendered state as well as DOM/accessibility data where layout or focus matters. Keep screenshots clean and preserve their actual state. A screenshot can support visual evidence; it does not alone prove keyboard behavior, the subsequent target or persistence.

## Visual acceptance and supported runtimes

For an explicit design comparison, establish the current approved mockup/baseline, page state and data, viewport/zoom and relevant fonts/runtime. Compare equivalent states; a loading screen against a populated design or an obsolete mockup is not automatically a product defect. Preserve a meaningful mismatch before deciding whether it is intended by a newer design change.

Choose browser/device/viewport variants from the support contract and actual risk, not a mandatory exhaustive matrix. Record which combinations really ran; one Chromium session cannot establish Safari, Firefox or physical-device coverage. Unavailable variants remain coverage gaps rather than inferred passes.

Separate visual deviation, functional inaccessibility and an accessibility finding. A control may look correct but be unreachable by keyboard; an intentional layout difference may remain usable. Keyboard/focus checks or a green accessibility scanner alone do not establish full accessibility conformance.

Do not replace a screenshot baseline merely to make the comparison green. Keep the original reference and observation, verify the reason for the change, and update the accepted baseline only when that change is authorized.
