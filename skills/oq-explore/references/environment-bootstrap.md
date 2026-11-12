# Reach the first valid check

Select a working channel rather than asking the user to design the tooling. The target is a valid observed check, not a guaranteed first bug: a healthy product is a legitimate result.

## Inspect before installing

1. Confirm the requested target, environment and required actor/session. Read project instructions and existing test commands/configuration. Reuse available fixture/reset mechanisms; keep credentials out of commands, code and reports.
2. Choose the least costly channel that preserves the claim:
   - **Existing signed-in browser:** use the host's native browser control when the task depends on that session. A new isolated browser is not the same actor or state. Confirm identity and do not export cookies to bridge the gap.
   - **Repeatable browser flow:** reuse the project's Playwright harness, installed browser CLI or available browser tool. Check tool availability and a harmless open/read before assuming it works.
   - **API/backend:** reuse the project's client or an available HTTP tool. Check that curl/Python/Node is actually present; none is universal. Observe the relevant response and state without inventing a UI requirement.
   - **Supplied evidence/source only:** perform the permitted analysis and identify the missing runtime capability. A written command is not an executed check.
3. If the required tool is absent, establish the minimal installation/dependency scope. A user's request to test does not itself authorize modifying the project's dependencies, replacing its lockfile, changing global configuration or downloading a browser. Reuse recorded installation authorization; otherwise obtain the necessary user approval and honor host permission controls.
4. With installation authorized, use an isolated scratch environment or the project's approved setup, pin/record dependency versions where practical and follow the tool's current official installation guidance. Keep the application repository unchanged unless that setup is explicitly requested. Verify the actual binary/browser startup and one harmless target observation; installation exit 0 is not operational proof.
5. Record capability, environment and first-check outcome. If installation, authentication or network access fails, mark that path blocked, retain the failure and continue independent useful checks. Ask for the smallest missing input, not for a new testing architecture.

## Setup results worth reporting

- Existing signed-in control worked: identify the tested actor without exposing its credential.
- Fresh browser worked but required session did not: public UI checks may proceed; authenticated coverage is still missing.
- API setup succeeded but UI control failed: report the UI/tooling boundary; API success does not erase it.
- Tool unavailable: explain what can still be assessed and the exact capability needed next.

When measuring onboarding, record setup start, first valid observation, environment and failures. Compare like-for-like runs; never publish an unmeasured “five minutes to a bug” promise.
