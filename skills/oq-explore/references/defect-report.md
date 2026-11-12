# A defect report another person can use

Use the requested tracker style. Keep factual artifacts professional; use the user's preferred conversational voice in the accompanying explanation. Preserve one demonstrated failure per report unless a shared cause is actually established.

## Compact template

```text
Title: [surface/action] produces [observed wrong result] under [relevant condition]
Environment: target/build when known, browser/runtime, actor role, observation time
Basis: current AC/contract/baseline and its relevant revision
Preconditions: synthetic owner/entity, meaningful existing state, setup
Steps: the smallest reproducible ordered actions through the tested channel
Expected: promised effect and protected state
Actual: observed effect, including final/read-back state
Evidence: stable IDs, redacted request/response, clean screenshot/trace pointers
Reproduction: failures / comparable attempts; changed conditions listed separately
Impact / severity: demonstrated user/system consequence and scope
Priority: proposed urgency with business/dependency rationale; owner decides
Limits: untested actors/platforms, missing attribution, observed-once conditions
Cleanup: restored/removed state and independent read-back, or remaining residue
Next discriminating check: one endpoint/log/mapper/state boundary; hypothesis labeled
```

Severity describes consequence; priority describes scheduling. Neither follows automatically from an HTTP status, scary payload or tester's annoyance. A functional blocker may be low exposure but urgent for an imminent release; a serious edge case may need immediate containment even if rare. Use the project's scheme and explain the actual effect rather than inventing a universal numeric matrix.

## Worked example — illustrative, not a live finding

**Weak:** “Date edit broken. Critical. Fix ASAP.”

**Useful:**

- **Title:** Pasted delivery date is shown in the editor but the previous date is saved.
- **Environment/basis:** supplied test build, ordinary member, AC-7 requires saving the chosen date; exact runtime/build recorded by the executor.
- **Setup:** owned synthetic order `order-42`, current date `2031-05-10`, unchanged delivery address.
- **Steps:** open editor → paste `2031-05-17` into the date control → submit using the visible button → reopen the same order.
- **Expected:** displayed and persisted date are `2031-05-17`; address remains unchanged.
- **Actual/evidence:** editor showed the new date; observed submit payload and independent order read-back retained `2031-05-10`. Attach those two redacted artifacts and the reopened UI state.
- **Impact:** user can believe delivery was rescheduled when it was not. Scheduling priority depends on affected users and rollout; database failure is not established because the old value was already submitted.
- **Reproduction/limits:** record actual attempt count; typing and Safari remain untested until exercised.
- **Cleanup:** executor restores the original fixture and verifies it; a planned restoration is not completed cleanup.

Keep screenshots faithful and clean. A later non-reproduction does not delete earlier evidence; annotate the changed conditions or unresolved intermittency.
