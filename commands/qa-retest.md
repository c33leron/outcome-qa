---
description: "Verify a claimed fix against its original failure and current product rule."
argument-hint: "<original bug, claimed fix and environment>"
disable-model-invocation: true
---

Handle the requested fix verification: $ARGUMENTS

Use the installed [retest workflow](../skills/oq-retest/SKILL.md). Recover the original setup, failed transition, expected result and relevant build/actor/entity from available evidence. Establish an equivalent valid fixture and replay the critical action; check normal functionality and risk-relevant neighbors. Keep changed requirements, invalid fixtures and unexecuted paths distinct from a closed bug.

Return a scoped retest verdict and evidence. If the request only supplies material for review, assess that material without claiming a fresh runtime replay. Product repairs or publication are separate requested actions.
