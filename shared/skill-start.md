# Start from a verified method, not a guessed path

## Select and load

Use the exact entrypoint supplied by the current host skill catalogue, or a verified link relative to an already loaded package file. Resolve references relative to the file actually read, not the working directory. A catalogue listing, a chosen path and an observed read are different facts; none establishes adherence by itself.

If a path is missing or stale, check the current catalogue or supported installed-plugin listing once for that method, then read its verified entrypoint. An old chat, remembered version, search hit or first/lexically latest cache directory does not identify the active installation. Do not repair discovery by installing, changing configuration or creating symlinks. If discovery remains ambiguous, state the load limitation and continue useful permitted work without claiming method use.

When auditing an explicitly selected source or historical version, read that target and label it accordingly; do not silently substitute the active installation. If a read is truncated, retrieve the omitted required sections by bounded ranges before applying them; a search excerpt is not the whole entrypoint. Read only relevant references, not the entire catalogue.

The host controls initial discovery; these instructions cannot repair a lookup before being read. After an update, a new session may be needed to refresh its catalogue.

## Make selection visible, briefly

After reading the method, before its QA actions, name it and its purpose once in the user's language: "Использую oq-retest: повторю исходный баг и проверю соседний регресс." Do not repeat the banner for references or continuations. Name another method when starting a distinct subtask that needs it.

Preserve exact output contracts: use permitted commentary or an existing field, otherwise omit the banner rather than add keys. Announcing a method is not evidence of following it.

## Review the expected behavior

Before designing or running a check that depends on a product requirement, read the relevant clause in the current ticket or specification. Inspect direct requirements and dependency links for the surface you are checking, even outside the initial ticket list. Follow any further source that defines the expected result. If a relevant source is unavailable, state what it leaves open. Use documented precedence or an approved clarification to resolve conflicting sources. What the product does today, including snapshots and existing tests, is evidence of behavior. It cannot settle an open product decision.

Walk the requested actor to the intended result. Ask where that person finds or receives it, when it is final, which state must survive, and what happens on a plausible interruption or retry. Pick the gaps that could change the assertion, coverage or readiness. For acceptance of a new user-facing result, treat its primary destination as a material question when users could plausibly look in different places and the sources do not settle it. Seeing the result in one place confirms its presence there. Ask which path the intended audience is supposed to use before giving full acceptance.

Surface a material gap as soon as it can affect a check. Look for the answer in available sources first. If it remains open, ask one concrete question per decision. Name the source or conflict, the specific behavior that needs a decision, and what the answer changes. If the question has not been sent, include the question itself in the handoff so the owner can answer or the user can forward it. For example, ask “Should reviewers open the finished report from Activity, Results, or both?” When the user requests sending it and the recipient and channel are authorized and available, send the question there and report what the channel confirmed. A sent question stays open until an answer resolves it. Continue independent checks, record observations for the affected behavior, and leave its verdict open. For a smoke with no formal spec, use any explicit expected outcomes from the request and report the rest as observations. Skip questions when the basis already answers them.

## Advance the question

When an observation changes the question, leaves a disputed conclusion, or requires a change of actor/channel/scope, use the shared [decision loop](decision-loop.md) from **any** method. A straightforward check with sufficient read-back can close directly. For async/media incident localization, select [incident tracing](incident-tracing.md).

## Delegate without losing discovery or boundaries

Execution workers receive scope, evidence needs and the method's exact verified entrypoint, or relevant loaded instructions when files are inaccessible—not a bare skill name that invites a guessed path. A child's stale path follows the same bounded recovery.

Context-only reviewers receive actual excerpts/evidence, not file-reading or product-execution duties; their boundary is not a load failure. The lead owns the user-facing announcement.
