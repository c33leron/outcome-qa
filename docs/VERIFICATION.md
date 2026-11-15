# Verification record

## Method verification before 0.1.1 — 2026-11-15

The following method checks used the private/local build label **0.1.3**. That label was never published on GitHub; the public successor to 0.1.0 is **0.1.1**. The same seven method bodies and references are carried into 0.1.1 without changes. These are local checks, not a claim of superiority. Tested on macOS with Python 3.14.6 and Codex CLI 0.164.0.

- Full unittest suite: 303 total, 300 passed, three Windows NTFS junction checks skipped on macOS. Shared-reference sync, package validation and all seven bundled authoring validations passed. The external authoring validator used a disposable environment for PyYAML; the runtime remains dependency-free.
- Native local installation returned 0.1.3; fresh `skills/list` returned all seven enabled methods in two working directories without package errors. All 109 runtime files in the source and installed cache matched the reviewed source mapping; all seven installed playbook exports executed successfully. Existing host configuration bytes and the prior plugin source backup were preserved.
- Explicit-path prior/candidate comparison: five fresh runs per arm on one frozen synthetic historical-capacity scenario. Both arms reached the supported bounded conclusion. Candidate runs read the new shared decision/incident references. No quality uplift was observed on that case; global host instructions remained present, so the prior was not a skill-disabled baseline.
- Additional candidate probes requested `gpt-6.1-sol` with high reasoning: role/coverage, truncated method loading, healthy correction and bounded continuation; a translation-only neighbor returned only the translation without loading QA. An extra initially pinned role probe was retained separately. The first comparison used configured `gpt-6-astra` with ultra reasoning. These are requested/configured identities; CLI output did not independently return the serving model ID.
- A fresh post-install task with no skill name/path selected the installed 0.1.3 Explore method and correctly identified an unrelated field change in a supplied synthetic trace. This establishes one natural-discovery case, not universal invocation reliability.
- Three supplied-evidence forward controls preserved healthy PASS, role-specific coverage and confident reporting of an attributed wrong-question answer. A separately frozen role case was executed by another agent and its actual answer/tool records passed the new adjudication-binding workflow. Reviews remain trusted semantic inputs, not automatic truth.
- Independent review found and verified corrections for packet filename collisions, repeated-path artifact reads and partial prepare cleanup in the development evaluator, plus an over-broad shared-loop trigger. These fixes do not add a runtime hook or mandatory review for ordinary QA.

Private raw trial records stay outside the distributed source. No live product regression, fresh Windows run, Claude runtime check, disabled-skill A/B, unseen benchmark or publication was performed for this candidate. Older live chats may retain prior instructions; use a fresh session after updating.


## Historical 0.1.0 verification

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
