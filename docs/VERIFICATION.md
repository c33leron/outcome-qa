# Outcome QA 0.1.0 verification

| Check | Observed result |
|---|---|
| Source and shared references | Package validation and all 24 shared-reference checks passed |
| Helper, lab and packaging tests | 264 passed, 3 skipped on macOS; the skipped cases require Windows NTFS junctions |
| Skills CLI 1.8.1 | Found all seven skills from the local source tree. Default and copy installs passed for eight agent targets: Codex, Claude Code, Cursor, OpenCode, GitHub Copilot, Gemini CLI, Antigravity and Hermes Agent. Installed files matched the source, including supporting references and licenses. No tests or labs were copied. |
| Full plugin marketplace | Built a 99-file local marketplace without a ZIP, including 95 runtime files. Verified SHA-256 for each declared file; no tests, CI, labs or contributor tools. |
| Codex CLI 0.164.0 | Clean-profile add, install, repeat install, discovery of all seven skills and removal |
| Claude Code 2.1.322 | Strict manifest validation, clean-profile install, repeat install, discovery of seven skills, three command entry points and two reviewers, and removal; no hooks enabled |
| Clone fallback helpers | Preview, install all seven skill folders, reject an existing target without modifying it, and export a self-contained Markdown playbook |

Checks ran on macOS arm64 with Python 3.14.6 and Node.js 22.23.2. Skills CLI checks verified installer discovery, routing and file contents, not agent inference on eight products. Native lifecycle tests used isolated profiles, no copied authentication and no model calls. The GitHub workflow covers macOS, Linux and Windows; native Linux/Windows host execution is not reported here.

[The recorded booking demo](DEMO.md) is a separate synthetic browser run with independent read-back. It illustrates the method, not comparative defect-detection performance. See [Evaluation](EVALUATION.md) for how to run and interpret comparisons.
