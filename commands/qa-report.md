---
description: "Turn existing QA evidence into a concise report without inventing execution."
argument-hint: "<evidence, observations and desired report format>"
disable-model-invocation: true
---

Prepare the requested QA report from: $ARGUMENTS

Use the relevant project format, or the [defect report guide](../skills/oq-explore/references/defect-report.md). Bind each material claim to the actual requirement, actor/entity, environment/build and observation. Describe reproduction, expected versus actual outcome, evidence, impact and unresolved coverage. Keep severity separate from business priority.

Existing observations may establish a narrow finding without establishing a complete run. Preserve failures, inconclusive attempts and cleanup uncertainty. Label missing evidence rather than fabricating it; drafting a report is not a request to execute new product actions, edit a tracker or publish externally.
