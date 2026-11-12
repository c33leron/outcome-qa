# Outcome QA

## Give your coding agent a senior QA playbook.

**Seven practical QA methods for coding agents:** human journeys, frontend and API behavior, test design, automation, AI quality, fix verification and feature security.

Start with what should happen and what can go wrong. Test the way people really use the product, follow unexpected behavior across layers, and back every finding with evidence someone else can reproduce.

## Start with a real task

> Test this feature against the acceptance criteria. Exercise the normal flow, meaningful mistakes and recovery. Verify the saved outcome and report observed coverage, findings and gaps.

Skill descriptions help a compatible host choose the method from your task. Explicit selection remains useful when diagnosing routing. Start a fresh session after installation.

| Need | Skill |
|---|---|
| Test cases and coverage from requirements | `oq-test-design` |
| Frontend, API, integration or regression testing | `oq-explore` |
| Automated tests, fixtures, flaky failures and CI | `oq-automation` |
| AI meaning, corrections, facts and downstream effects | `oq-ai-quality` |
| False-pass assertions, judges, metrics or gates | `oq-checker-audit` |
| Original-bug confirmation after a fix | `oq-retest` |
| Feature access, input, rendering, files, origins and AI actions | `oq-security-journeys` |

## Install the complete bundle

The outer install bundle contains this `outcome-qa/` directory and marketplace descriptors. Run marketplace commands from the **outer bundle root**, not this inner directory.

Codex:

```sh
codex plugin marketplace add . --json
codex plugin add outcome-qa@outcome-qa-releases --json
codex plugin list --marketplace outcome-qa-releases --json
```

Claude Code, in an interactive session at the outer bundle root:

```text
/plugin marketplace add ./
/plugin install outcome-qa@outcome-qa-releases
```

For a session-only Claude Code load, run `claude --plugin-dir ./outcome-qa` from that same outer root. The outer `README.md` has extraction, standalone installation, upgrade and removal instructions. Keep a registered local bundle at its installation path.

## A lead that adapts during testing

For a broad “test this task” request, Explore leads the investigation and reassesses after meaningful observations. It can load another Outcome QA method or a suitable installed outside skill, use an available tool, delegate an independent branch, and reconcile the returned evidence. Frontend/backend labels alone do not start extra agents. Direct specialist requests still enter their own method.

This is host-driven coordination, not a background orchestrator or new permission grant. The host must actually expose the skill, tool or worker capability. The lead preserves task scope, isolates mutable state, joins workers before cleanup and reports concrete gaps. It does not install tools automatically or promise every available method will run.

## What is in the kit

- Seven focused skills with their own references and worked examples.
- Two optional reviewer definitions: evidence review and automated-test review. The lead supplies the relevant material; context-only reviewers do not independently execute the product.
- Explicit Claude commands: `/outcome-qa:qa`, `/outcome-qa:qa-retest`, `/outcome-qa:qa-report`.
- Local helpers for JSON state contracts, result-record consistency, standalone installation, project routing and complete playbook export.
- Schemas, attribution and license notices.

Your host supplies models and tools. Nothing starts a background service or automatically installs a browser. Hooks and native Codex reviewer installation are opt-in. The optional Claude SessionStart hook template requires a POSIX shell and `python3`; it is not needed for the main plugin. Installing a skill does not start a separate agent.

## Optional helpers

Run these from **this inner runtime directory** with Python 3.10+. On Windows, replace `python3` with `py -3`.

```sh
python3 scripts/export_playbook.py oq-explore --output outcome-qa-explore.md
python3 scripts/check_transition.py --help
python3 scripts/qa_result.py --help
```

The exporter writes a new complete playbook with its linked references and attribution. The state checker evaluates supplied before/after snapshots against explicit rules. The result checker checks record consistency and referenced artifact hashes. Neither helper runs your product or certifies that an observation is true.

Tests, labs, example run records and contributor tooling live in the source repository, not in this runtime. Supply your own private snapshot/report paths to the helpers; do not expect the source examples here.

## License and provenance

MIT. Maintained by c33leron with AI assistance. Preserve `LICENSE`, `THIRD_PARTY_NOTICES.md` and `licenses/gstack-MIT.txt` when redistributing. The human-journey method descends from an attributed gstack adaptation; this is an independent project, not an official OpenAI or Anthropic product.
