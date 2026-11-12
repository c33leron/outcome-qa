# Provenance — what is ours, what we adapted

Outcome QA is maintained by **c33leron**, developed with AI assistance. It is not an official OpenAI, Anthropic, Microsoft or upstream project. No competitor endorsement or comparative superiority is claimed.

## Adapted material: gstack → personal qa-exploratory → Outcome QA

The human-journey method in `skills/oq-explore/` and shared practices re-expressed in the other skills descend from a personal `qa-exploratory` adaptation of **Garry Tan's gstack**, MIT:

- Upstream snapshot: [`e9dfcf64f0f3532803fe0334efae8cd54a22fdda`](https://github.com/garrytan/gstack/tree/e9dfcf64f0f3532803fe0334efae8cd54a22fdda).
- Original areas: `qa-only/SKILL.md`, `qa/sections/exploratory.md`, `qa/sections/qa-patterns.md`, and `qa/references/issue-taxonomy.md`.
- Local adaptation entrypoint SHA-256 used as input: `7ff6b9b158954115a2d04fd5a3eaac1cf47d9f9a31e16bbd122b54ba0262b8ef`.
- Preserved ideas: report-only exploration, bounded charters, observation/hypothesis/probe, realistic state sequences, equivalent reproduction and evidence-bounded claims.
- Changes here: seven discriminating skill scopes, portable per-skill references, RU/EN task discovery, separate AI-output and checker auditing, changed-contract retests, explicit tool/product failure distinction, optional reviewers, synthetic lab and new helper implementations.
- The gstack runtime, browser engine, updater, hooks and recorder are **not bundled**. The personal recorder is also not copied.

The original copyright and MIT permission notice are retained in `licenses/gstack-MIT.txt`. Each skill also carries the full MIT notices in its own `LICENSE.txt`, so installers that copy only the skill folder preserve attribution. Keep the applicable notices with redistributed copies.

## Conceptual references — independently written implementation

These were inspected during design. No source code or substantial text from these projects is bundled. Their own licenses still govern their original files; this table does not relicense them.

| Source / pinned revision | Mechanism studied | Outcome QA decision |
|---|---|---|
| [voidmatcha/e2e-skills — a770334](https://github.com/voidmatcha/e2e-skills/tree/a7703345e1248006aab61cc168d1ae138d6f0278), Apache-2.0 | Test-strength audits; app faults versus assertion mutation | Keep the distinction in checker auditing; never count build/setup failure as detection |
| [petrkindlmann/qa-skills — 6243425](https://github.com/petrkindlmann/qa-skills/tree/62434253c2592f27b494609c27f224939c86346d), MIT | Context routing; incomplete command results; skills-on/off experiments | Use focused task scopes; no mandatory meta-agent; record limits instead of manufacturing PASS |
| [0xSteph/pentest-ai-agents — e5d7aa0](https://github.com/0xSteph/pentest-ai-agents/tree/e5d7aa02c4c0c29a90e4789034b45e0cb7488e89), MIT | Original-proof retest and neighboring behavior | Adapt the idea to quality verification; no offensive runtime bundled |
| [obra/superpowers — 22f0b46](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7), MIT | Discriminating diagnosis and verification before completion | State changes determine evidence freshness, not message boundaries |
| [testland/qa — 12772c9](https://github.com/testland/qa/tree/12772c93d3ffd7c8b79f683b01b539afdc2e9b47), MIT | Confirmation testing; eval calibration and sham control | Separate retest from release regression and supplied fixtures from unseen evidence |
| [jaktestowac/awesome-agents-for-quality — c4efc46](https://github.com/jaktestowac/awesome-agents-for-quality/tree/c4efc46815a7c860ab3616f1eed953c87f2f4f0c), MIT | Trigger-collision cases and portable authoring | Include positive, negative and neighboring-intent routing cases |
| [Promptfoo official eval skill](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md), inspected 2026-11-09, MIT | Calibrated graders; application boundary versus direct model call | Reuse existing eval tooling when available; no provider, API key or model dependency bundled |

Claude-BugHunter (MIT code / CC BY 4.0 content), Claude-Red and other catalogs were compared but their files are **not incorporated**. Rewording substantial copied content would not erase attribution or license obligations.

## Original components and methodology

The package manifests, local marketplace bundle, state-contract and result-consistency helpers, strict JSON utilities, playbook exporter, explicit installers, packaging checks, project-routing helper, optional hook adapter, synthetic labs, automated tests, routing cases and evaluation protocol were written for Outcome QA. No additional third-party runtime is bundled by those components.

The six initial skill procedures retain the gstack-derived lineage above rather than being relabeled as wholly original. The seventh procedure, `oq-test-design`, and the frontend-state, workflow-composition and feature-security additions were independently authored. Worked examples and shared-reference materialization were also implemented for this package. Comparison with other catalogs informed architectural decisions; catalog size was not treated as a measure of quality.

Test scenarios generalize recurring QA mechanisms using synthetic data. Private research indexes and raw project conversations are not distributed as test fixtures.

### Additional conceptual guidance

- [OWASP WSTG v4.2 reflected XSS](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/07-Input_Validation_Testing/01-Testing_for_Reflected_Cross_Site_Scripting/) and [SQL injection](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection/) informed the input/rendering distinctions. No OWASP text or payload catalog is redistributed.
- [Michael Bolton, FEW HICCUPPS](https://developsense.com/blog/2012/07/few-hiccupps/) and [James Bach, Heuristic Test Strategy Model](https://www.satisfice.com/download/heuristic-test-strategy-model) informed short, originally worded test-selection aids. Those aids do not reproduce the complete source models or imply endorsement. Oracle heuristics suggest questions; product requirements still define the expected result.
- [Superpowers writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md) informed baseline and pressure-control evaluation. [Anthropic webapp-testing](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) was inspected for helper/tool discovery. Their implementations and substantial prompt bodies are not incorporated.

Claude command/hook and Codex plugin/agent adapters follow their host formats. Their compatibility evidence is recorded separately from this attribution notice. No forced hooks, automatic updater, universal wait strategy or guarantee of skill activation is inherited from conceptual references.
