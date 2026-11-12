# Codex integration

For the seven QA skills, use the [standard skills install](INSTALL.md). For the full plugin, [prepare the clean marketplace from a clone](INSTALL.md#native-plugin). Choose one route per discovery scope to avoid duplicate skills.

## Install and verify discovery

From the generated `outcome-qa-marketplace` directory:

```sh
codex plugin marketplace add . --json
codex plugin add outcome-qa@outcome-qa-releases --json
codex plugin list --marketplace outcome-qa-releases --json
```

The last output should identify the installed plugin. Keep the registered bundle at that path. Start a fresh Codex CLI session or reopen the desktop project to refresh its catalog. An already-running chat can retain old instructions; a successful CLI registration does not by itself show that a desktop session has refreshed.

Use an ordinary task:

> Test this feature against the acceptance criteria. Exercise the user journey, investigate meaningful risks and verify the saved result.

For routing diagnosis, explicitly request `oq-explore` and inspect the actual skill-file read in the host trace. The agent's statement that it used a skill is not proof of discovery. Installation, discovery and successful product execution are separate checks; the release record is in [Verification](VERIFICATION.md).

## Stale paths and visible selection

Each loaded method requests one concise announcement of its name and purpose before QA actions. Exact output formats can suppress it; the real file read and subsequent checks remain the evidence.

Use the entrypoint supplied by the current host catalogue. Do not guess a publisher/cache/version, reuse a retired version path from another chat, or make cache symlinks to conceal a missing file. If it fails, rediscover the selected method once through the current catalogue or supported installed-plugin listing. If unresolved, state the loading gap. Start a new session after an update when the host still exposes old paths.

Execution workers need the exact verified entrypoint or loaded instructions in their brief. The context-only reviewers below instead receive evidence excerpts; they are not required to read files. The package cannot control the host's first implicit lookup before its instructions have been read.

## Optional native reviewer roles

The plugin and custom-agent registries are separate host mechanisms. Installing the plugin does not automatically register the TOML roles in `adapters/codex/agents/`.

The roles are:

- **`oq-evidence-reviewer`**: challenge a consequential finding, retest conclusion or coverage claim using the supplied requirements and observations.
- **`oq-test-reviewer`**: find false passes, missing assertions and fixture/state mistakes in supplied automated tests or evaluator code.

From the **inner runtime directory**, preview and then install:

```sh
python3 scripts/install_codex_agents.py --target ~/.codex/agents
python3 scripts/install_codex_agents.py --target ~/.codex/agents --apply
```

On Windows PowerShell:

```powershell
py -3 scripts/install_codex_agents.py --target "$HOME\.codex\agents"
py -3 scripts/install_codex_agents.py --target "$HOME\.codex\agents" --apply
```

A project's `.codex/agents/` is an alternative target. The Python 3.10+ installer creates new files; it refuses overwrites, partial packages and symlinks. On failure it attempts to roll back only its own unchanged files. It does not install skills, edit global configuration, select models or alter unrelated agents. Native TOML parsing is checked on Python 3.11+; Python 3.10 supports the byte-copy installer without a third-party parser.

### How reviewers work

These are **context-only reviewers**. The lead supplies relevant requirements, code and raw observations. Reviewers must not claim to have opened a file they were not given, invent a run or probe the product independently. Shell, apps, plugins, memory and permission-request features are disabled in the definitions; their instructions prohibit tool use.

This is a capability reduction, not a separate security sandbox: Codex inherits parent permissions and traditional MCP configuration. Avoid giving a reviewer unnecessary sensitive capabilities. No model or reasoning override is specified; the host's configured inheritance applies.

A reviewer is useful for a disputed conclusion or substantive test change. It is not a mandatory extra step for every check. The main agent retains responsibility for the final outcome and unresolved disagreements.

## Optional project routing

To help select the relevant method consistently in one project, preview a managed instruction block:

```sh
python3 scripts/project_routing.py --project /path/to/your-project --host codex
python3 scripts/project_routing.py --project /path/to/your-project --host codex --apply
```

Use a real project path; on Windows use `py -3` and a Windows path. The helper changes only its own marked block in `AGENTS.md`. It upgrades or removes exact unmodified legacy blocks, preserves unrelated rules and refuses conflicts rather than overwriting an edited block. Coordinate other writers before applying changes: later writes through a stale open file handle are outside its conflict checks. A successful update leaves no permanent backup of prior content; keep the file under version control if you need historical rollback.

If an older QA instruction always forces another workflow, revise that one rule deliberately. Installing Outcome QA does not silently disable existing skills or erase personal instructions.

## Remove or upgrade

Remove the plugin before its marketplace registration:

```sh
codex plugin remove outcome-qa@outcome-qa-releases --json
codex plugin marketplace remove outcome-qa-releases --json
```

For an upgrade, register the new version's extracted bundle afterward, then start a fresh host session. Keep local modifications separately instead of overwriting an installed folder.

Plugin removal does not undo the two opt-in steps above. After reviewing any local edits, remove only `oq-evidence-reviewer.toml` and `oq-test-reviewer.toml` from the target where you installed them. To remove routing, preview and apply `scripts/project_routing.py --project /path/to/your-project --host codex --remove`, adding `--apply` only after reviewing the preview. Do not delete the whole host agents directory or project instruction file.

Official references: [local plugins](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually), [custom-agent schema](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agent-file-schema), [local skill configuration](https://learn.chatgpt.com/docs/build-skills#enable-or-disable-local-codex-skills).
