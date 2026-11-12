# Support and useful feedback

The most useful report is a small case we can reproduce—not a full private chat export. Tell us what you expected, what happened and which Outcome QA component was actually used.

## Pick the right category

| Category | Example |
|---|---|
| Installation or discovery | The plugin installs, but the new host session does not discover `oq-explore` |
| Missed or weak check | The agent checked a toast but skipped the saved value required by the task |
| Incorrect verdict | A blocked request became PASS, or an unsupported assumption became a product bug |
| Useful new scenario | A reproducible workflow that the current methods do not handle well |

Use the repository's QA feedback issue form when available. For a vulnerability in the package itself, follow the [private reporting policy](SECURITY.md) instead of posting sensitive details.

## Include enough to reproduce

1. **Versions:** Outcome QA version, host/version, model if known, OS and relevant tool version.
2. **Install route:** marketplace plugin, standalone skills, exported playbook or optional reviewer.
3. **Task:** a short, redacted request and the requirement or baseline that defines success.
4. **Expected / actual:** the missing check, wrong conclusion or exact error—not just “it didn't work.”
5. **Loaded method:** the skill ID and observed file read or agent start, if your host exposes it. Say “unknown” when unavailable; self-reported activation is not conclusive.
6. **Minimal reproduction:** synthetic inputs, relevant initial state, actions and result. Record intermittent attempts instead of keeping only a convenient rerun.
7. **Evidence:** only the smallest sanitized excerpt or synthetic artifact needed to understand the case.

Never upload tokens, cookies, `.env` files, private chat exports, production logs, personal data, client names or private endpoints. Replace identifiers consistently so the failure remains understandable. Review screenshots for browser tabs, account details and sensitive URLs before sharing.

## Quick installation diagnosis

- Confirm that you extracted the install bundle, not the source archive.
- Run marketplace commands from the outer bundle folder, where both marketplace directories and `outcome-qa/` exist.
- For Codex, inspect `codex plugin list --marketplace outcome-qa-releases --json`.
- Start a fresh host session after installation or removal. Do not assume an old desktop chat refreshed its skill catalog.
- Avoid duplicate standalone and plugin copies in the same discovery scope.
- Helpers need Python 3.10+. Use `python3` on macOS/Linux or `py -3` on Windows.
- Check the tools required by the task. A discovered QA skill does not itself install a browser or grant API access.

See [Installation](distribution/INSTALL.md), [Codex integration](docs/CODEX.md) and [Verification](docs/VERIFICATION.md) for the concrete routes and release evidence.

## Contributing a method improvement

Prefer one demonstrated gap and a focused change over another broad persona. Show a faulty case that the proposed check detects **and** a healthy control it leaves alone. For wording/routing changes, include a request that should trigger the method and a neighboring request that should not. Keep product failures separate from setup, tool and evaluator failures.

Tests, fixtures and evaluation cases belong in the source repository; they are not shipped in the user runtime. Credit adapted material and preserve its license. No response-time commitment is implied by opening an issue.
