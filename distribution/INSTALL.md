# Outcome QA 0.1.1

**Give your coding agent a senior QA playbook.** Unzip the bundle, install for your host, and describe a real QA task. You do not need Python for the Codex or Claude Code plugin.

## 1. Extract the install bundle

Download `outcome-qa-0.1.1.zip`, not GitHub's automatic **Source code** archive. Extract it to a folder you will keep. Open a terminal in the extracted `outcome-qa-0.1.1` folder (not the inner `outcome-qa` folder). Use your archive manager or the commands below.

**macOS / Linux**

```sh
unzip outcome-qa-0.1.1.zip
cd outcome-qa-0.1.1
```

**Windows PowerShell**

```powershell
Expand-Archive -LiteralPath .\outcome-qa-0.1.1.zip -DestinationPath .
Set-Location .\outcome-qa-0.1.1
```

The current directory must contain `.agents/`, `.claude-plugin/` and the inner `outcome-qa/` runtime directory. All plugin commands below start here.

## 2. Install for your host

### Codex

With the Codex CLI installed, run these two commands from the outer bundle folder:

```sh
codex plugin marketplace add . --json
codex plugin add outcome-qa@outcome-qa-releases --json
```

Start a new Codex session, or reopen the desktop project to refresh its catalog. To verify the install, run `codex plugin list --marketplace outcome-qa-releases --json` and look for the installed, enabled `outcome-qa` entry.

### Claude Code

With Claude Code installed, run these two commands from the same outer folder:

```sh
claude plugin marketplace add ./
claude plugin install outcome-qa@outcome-qa-releases
```

In an interactive session, `/plugin marketplace add ./` registers the same catalog; `/plugin install outcome-qa@outcome-qa-releases` opens its plugin panel, where you confirm installation.

Start a new Claude Code session. To verify the install, run `claude plugin list --json` and look for the enabled `outcome-qa` entry. For a session-only load without marketplace registration:

```sh
claude --plugin-dir ./outcome-qa
```

This integrates with **Claude Code**; it is not an installer for every Claude chat application. Explicit entry points include `/outcome-qa:qa`, `/outcome-qa:qa-retest` and `/outcome-qa:qa-report`.

### Other skill-aware agents

For another agent that supports `SKILL.md`, find its documented skills directory. Copy each complete `oq-*` folder from `outcome-qa/skills/` into that directory, including the references. Restart the host. Do not copy only the entrypoint.

Prefer a checked copy? From the outer bundle folder, use the optional installer with your host's actual skills path. The first command previews; the second applies.

```sh
cd outcome-qa
python3 scripts/install_skills.py --target /path/to/your-project/.agents/skills
python3 scripts/install_skills.py --target /path/to/your-project/.agents/skills --apply
```

On Windows, use a Windows target path and `py -3`:

```powershell
Set-Location .\outcome-qa
py -3 scripts/install_skills.py --target "C:\Projects\my-app\.agents\skills"
py -3 scripts/install_skills.py --target "C:\Projects\my-app\.agents\skills" --apply
```

Python 3.10+ is required for these helpers, not for reading the skills. The installer creates new directories and refuses overwrites. It does not install a host or configure model access. Do not install standalone copies and the plugin into the same host's discovery scope.

For assistants without skill discovery, export one self-contained Markdown playbook from the inner runtime directory:

```sh
python3 scripts/export_playbook.py oq-explore --output outcome-qa-explore.md
```

Use `py -3` on Windows. Attach or load that file using your assistant's supported workflow. A playbook provides method, not browser access or a background agent.

## 3. Give it the work

Open your application project in the host and provide the feature, requirements, environment and allowed actions:

> Test the profile editor. Check normal saving, correction, repeated submission and reload. Verify that the edited field persists and unrelated fields remain unchanged.

Other useful requests:

- “Design test cases for this API contract, with meaningful boundaries and expected results.”
- “Verify this bug fix using the original reproduction and a healthy control.”
- “Review these tests for assertions that could pass while the feature is broken.”
- “Test whether the AI applies a corrected fact in its final saved report.”
- “Check this feature's access boundaries using the supplied synthetic accounts.”

A compatible host can select relevant skills from their descriptions, or you can name the skill explicitly. Skills do not automatically spawn an agent swarm. The lead can combine methods, and supported hosts can use optional reviewers when an independent check is useful.

## Check that the method loaded

After reading a method, the agent should briefly name it and its purpose before QA actions. Strict JSON or other exact output contracts take priority; a banner alone does not prove use. When diagnosing a miss, inspect the actual `SKILL.md` read in the host trace.

Use the entrypoint from the **current host catalogue**, not a path copied from an old session. Publisher names, cache layouts and versions vary by installation. After an update, refresh the host session; do not create old-version cache symlinks or rename marketplace directories to make a guessed path work. If the catalogue is unavailable or ambiguous, the agent must disclose that it could not load the method rather than claim activation.

## Optional project routing and reviewers

For a persistent project-specific routing hint, run from the inner runtime directory:

```sh
python3 scripts/project_routing.py --project /path/to/your-project --host codex
python3 scripts/project_routing.py --project /path/to/your-project --host codex --apply
```

Use `--host claude` for Claude Code, and `py -3` plus a Windows project path on Windows. Preview first. The helper manages its own marked block in `AGENTS.md` or `CLAUDE.md`; it is not a reason to replace existing project instructions. Coordinate concurrent edits before applying changes. The current helper upgrades or removes exact unmodified legacy routing blocks; manually edited blocks remain conflicts and require deliberate reconciliation.

Native Codex reviewer roles are a separate opt-in:

```sh
python3 scripts/install_codex_agents.py --target ~/.codex/agents
python3 scripts/install_codex_agents.py --target ~/.codex/agents --apply
```

PowerShell equivalent target: `"$HOME\.codex\agents"`, using `py -3`. A project's `.codex/agents/` is also supported. These two context-only roles review supplied evidence or test code; they do not independently run the product. No model, global config or permission setting is changed.

The optional Claude SessionStart hook template in `adapters/claude/` is not enabled automatically. It requires a **POSIX shell and `python3`**; native Windows PowerShell users can use the main plugin without this hook. Review a hook before adding it to host configuration.

## Upgrade and remove

Before an upgrade, retain any local edits and extract the new version into its own permanent folder. Remove the old plugin and marketplace registration before adding the new bundle at its new path; do not overwrite an installed directory in place.

**Codex**, from any directory:

```sh
codex plugin remove outcome-qa@outcome-qa-releases --json
codex plugin marketplace remove outcome-qa-releases --json
```

**Claude Code**, from a terminal:

```sh
claude plugin uninstall outcome-qa@outcome-qa-releases
claude plugin marketplace remove outcome-qa-releases
```

Restart the host after removal. Remove registrations in both hosts if both use the bundle, then archive or delete the bundle when no longer needed.

Separately installed reviewers and standalone skills are not removed by plugin uninstall. Review local changes first, then remove only the files/directories installed for Outcome QA: the two reviewer TOMLs (`oq-evidence-reviewer.toml`, `oq-test-reviewer.toml`) or the seven `oq-*` skill directories named in the inner runtime `README.md`. Do not remove the host's whole agents or skills directory.

Remove a project routing block with a preview, then explicit apply:

```sh
python3 scripts/project_routing.py --project /path/to/your-project --host codex --remove
python3 scripts/project_routing.py --project /path/to/your-project --host codex --remove --apply
```

Use the same host choice and platform-specific Python command as installation. The helper refuses to remove an edited managed block blindly.

## Requirements and help

The package uses text-based plugin/skill formats; helpers use Python 3.10+ and the standard library. Your selected host supplies the model, authentication, permissions and testing tools. Browser testing needs a working browser tool; API testing needs appropriate network access. Existing project tooling is reused before new setup is considered.

For troubleshooting, report the package version, host and version, OS, install route and exact redacted error. For test-quality feedback, include the requirement, minimal synthetic reproduction, observed behavior and the skill actually loaded. Do not send tokens, private chat exports or client data. Source documentation contains `SUPPORT.md`, `SECURITY.md` and `docs/VERIFICATION.md` with release check details.

MIT. Preserve the inner runtime's `LICENSE`, `THIRD_PARTY_NOTICES.md` and bundled upstream license when redistributing.

Host command reference: [Claude Code marketplace workflow](https://code.claude.com/docs/en/plugin-marketplaces).
