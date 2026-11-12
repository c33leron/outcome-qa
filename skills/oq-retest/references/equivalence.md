# Equivalent retests

Compare conditions for causal relevance, not superficial equality.

| Dimension | Preserve when relevant | Legitimate difference | Invalid shortcut |
| --- | --- | --- | --- |
| Product rule | Current agreed expectation and its scope | Explicitly revised requirement | Treat implementation behavior as its own new specification |
| Build/config | Know what environment was observed | New deployed fix, intended migration/flag | Assume source branch tip equals runtime |
| Actor | Role, ownership and tenant boundary | Fresh owned test identity with equivalent rights | Use admin because restricted user cannot reach it |
| Data | Defect-producing shape, dependencies and existing state | Fresh disposable IDs | Remove the nullable/old/conflicting data that caused the issue |
| Sequence | Critical action, prior history and timing dependency | Safe setup shortcut outside the disputed path | Replace UI submit with an API call |
| Observation | Original symptom and relevant persistent effect | Better independent instrumentation | Accept a toast instead of reading the saved record |
| Authentication | Valid session at the required stage | Refresh expired credential | Count 401/404 as proof the defect is blocked |
| Platform | Relevant browser/device/runtime | Additional control platform | Close a native-device issue from desktop emulation only |

## Source containment is useful, not magic

When the environment supplies an actual build SHA and the relevant repository is available, ancestry checks can support source containment. Handle “ancestor”, “not ancestor” and “command errored” separately; unknown/shallow history is not proof of absence. Squash/rebase can replace the original fix SHA.

Containment does not prove the deployed binary, migration or feature flag matches the source, and absence of metadata does not prohibit observing behavior. Keep source attribution and runtime confirmation distinct.

## Example verdicts

- The same corrected-date action now sends and saves the intended date; reopen agrees. Confirm this path fixed. A separate browser not exercised remains a gap, not a failed fix.
- The replay gets 401 before the target handler because the session expired. Not comparable; refresh the permitted fixture and repeat if authorized.
- Duplicate submission no longer creates two records because all submissions fail. The duplicate symptom is absent, but legitimate functionality is broken; do not close the feature as successful.
- A business rule changed from blocking a stage to allowing the stage and scheduling follow-up. Test the new end-to-end rule and label the requirement change rather than reporting the removed block as a regression.

## Evidence and remaining scope

Recover primary artifacts when available rather than relying only on a summary. If an exact reproduction is missing, reconstruct the smallest justified scenario and identify that difference. Preserve every current attempt; for intermittent behavior, state exposure and condition changes instead of certifying a fix from one non-reproduction.

Confirmation and regression answer different questions. Report the original defect separately from a newly observed neighbor failure, an untested platform and a blocked subpart. Relevant reused evidence stays labeled; out-of-band changes to requirements/configuration/fixtures can supersede it. Ordinary test steps do not invalidate the observations they produced.

Verify restoration of owned state and report residual data explicitly. A closure comment can recommend a tracker status only as strongly as the observed retest permits; historical evidence, tracker updates, repairs or broader environment changes remain separately authorized work.
