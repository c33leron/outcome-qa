# Install Outcome QA

| I want… | Use… |
|---|---|
| The QA skills in my coding agent | [Skills CLI](#skills-cli) |
| The QA skills without Node.js | [Git clone](#git-clone-without-nodejs) |
| The full Codex or Claude Code plugin | [Native plugin](#native-plugin) |
| A playbook for an assistant that cannot load skills | [Markdown playbook](#markdown-playbook) |

Choose one installation route per agent and project to avoid duplicate skills.

## Skills CLI

With Node.js 22.20+ and Git installed, open a terminal in the **project you want to test**:

```sh
npx skills add c33leron/outcome-qa
```

Select the skills and agents you want. The [Skills CLI](https://github.com/vercel-labs/skills) handles discovery and placement. Its [supported agent list](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) includes Codex, Claude Code, Cursor, OpenCode, GitHub Copilot, Gemini CLI, Antigravity, and Hermes Agent. Use `-g` for user-wide installation, or `--copy` if your setup does not support symlinks.

To target specific agents or install only one skill:

```sh
npx skills add c33leron/outcome-qa -a cursor -a github-copilot
npx skills add c33leron/outcome-qa --skill oq-explore -a gemini-cli
```

Run `npx skills list` in the project to check what was installed. Use `npx skills remove` and select the Outcome QA skills to remove them. Add `-g` to list or remove a global install.

## Git clone without Node.js

```sh
git clone https://github.com/c33leron/outcome-qa.git
cd outcome-qa
```

Copy the complete `skills/oq-*` folders into your agent's documented skills directory. Do not copy just `SKILL.md`: the folders include supporting references and licenses.

Or use the Python 3.10+ installer. Replace the example path with the actual skills directory. Without `--apply`, it previews changes; with it, it copies the skills and refuses to overwrite existing folders.

```sh
python3 scripts/install_skills.py --target "/path/to/my-project/.agents/skills" --apply
```

Windows PowerShell:

```powershell
py -3 scripts/install_skills.py --target "C:\Projects\my-project\.agents\skills" --apply
```

The standalone routes install the QA methods, not plugin commands, custom reviewer registration, or hooks. The host still supplies tools, permissions, and the model.

## Native plugin

Use this route for the packaged runtime and host integrations. From the Git checkout, build a clean marketplace folder beside the repository. Keep the generated folder where you register it. The builder excludes test and development files.

macOS / Linux:

```sh
python3 scripts/build_release.py --output-dir ../outcome-qa-marketplace
cd ../outcome-qa-marketplace
```

Windows PowerShell:

```powershell
py -3 scripts/build_release.py --output-dir ..\outcome-qa-marketplace
Set-Location ..\outcome-qa-marketplace
```

**Codex**

```sh
codex plugin marketplace add . --json
codex plugin add outcome-qa@outcome-qa-releases --json
```

See [Codex integration](CODEX.md) for discovery and the separately enabled reviewer roles.

**Claude Code**

```sh
claude plugin marketplace add ./
claude plugin install outcome-qa@outcome-qa-releases
```

Claude Code exposes `/outcome-qa:qa`, `/outcome-qa:qa-retest`, and `/outcome-qa:qa-report`. For a single session without marketplace registration, launch `claude --plugin-dir ./outcome-qa` from the generated marketplace folder.

Check the native install with `codex plugin list --marketplace outcome-qa-releases --json` or `claude plugin list --json`.

To remove a native install, run the commands for your host and restart it:

```sh
# Codex
codex plugin remove outcome-qa@outcome-qa-releases --json
codex plugin marketplace remove outcome-qa-releases --json

# Claude Code
claude plugin uninstall outcome-qa@outcome-qa-releases
claude plugin marketplace remove outcome-qa-releases
```

## Markdown playbook

From the Git checkout, export a self-contained playbook for a single method:

```sh
python3 scripts/export_playbook.py oq-explore --output outcome-qa-explore.md
```

Use `py -3` instead of `python3` on Windows. Attach or paste the Markdown into your assistant. It provides the QA method, not tool access.

## First task

Start a fresh agent session in your project and give it a test objective, the requirements, and the environment it may use. For example:

> Test the profile editor on staging. Start with a normal edit, then try correcting the input, submitting twice, and reloading. Verify what persisted and what should stay unchanged.

If the host does not select a skill automatically, ask it to use `oq-explore` explicitly. See [verification](VERIFICATION.md) for tested installation paths and [support](../SUPPORT.md) for troubleshooting.
