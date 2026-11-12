---
description: "Choose and perform the appropriate Outcome QA workflow for a testing request."
argument-hint: "<testing task and relevant requirements>"
disable-model-invocation: true
---

Handle the user's QA request: $ARGUMENTS

Choose the primary installed Outcome QA skill by the requested work: design cases → oq-test-design; test actual behavior → oq-explore; write/debug tests → oq-automation; assess AI meaning → oq-ai-quality; audit a checker → oq-checker-audit; verify a claimed fix → oq-retest; check feature security → oq-security-journeys.

Read the chosen entrypoint from the current host skill catalogue or this package's `../skills/<chosen-name>/SKILL.md`, resolved relative to this command. Never invent a marketplace/cache/version path. If stale, check current discovery once; if unavailable, state the loading gap without claiming activation. After a successful read, name the method and purpose once before QA actions unless the output format forbids it. Follow its startup reference for delegation and only load applicable references.

Preserve every requested clause, adding a second method for a distinct subtask. A frontend/API label chooses relevant depth, not a mandatory new agent. Use existing tools and permitted data; select an available channel before asking the user to configure one. A missing capability is a concrete gap, not an excuse to invent execution.

For a broad product-testing request, use Explore as the lead and revisit method selection when observations introduce a distinct question. Follow [adaptive coordination](../skills/oq-explore/references/workflow-composition.md) for relevant installed outside skills, available workers, ownership, result reconciliation and stopping. This is not a requirement to route explicit specialist requests through Explore or to start a worker for every layer.

For a broad request, clarify only the consequential unknown unavailable from current project context. A narrow task needs a narrow check. Return observed results, evidence and remaining gaps in the user's requested format. This command does not install tools, expand permissions or start the whole catalog.
