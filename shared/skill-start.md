# Start from a verified method, not a guessed path

## Select and load

Use the exact entrypoint supplied by the current host skill catalogue, or a verified link relative to an already loaded package file. Never reconstruct a publisher, cache directory or version from memory, an old chat, or a familiar marketplace name. Resolve references relative to the entrypoint actually read, not the working directory.

If a path is missing or stale, check the current host catalogue or supported installed-plugin listing once for the selected method. Read the newly verified entrypoint before proceeding. A directory name, a search hit, or a lexically "latest" version alone does not establish the active installation. If discovery is unavailable or ambiguous, state that the method could not be loaded; continue only the permitted work with that limitation. Do not claim the skill was used, repeatedly guess paths, install anything, create cache symlinks or change configuration to hide the failure.

The host controls initial implicit discovery. These instructions cannot repair an old session's first lookup before it has read them. After an update, a new session may be necessary to refresh the host catalogue.

## Make selection visible, briefly

After successfully reading the chosen method, and before its QA actions, tell the user once which method you are using and why, in their language: "Использую oq-retest: повторю исходный баг и проверю соседний регресс." Keep it one short sentence, not a ceremony or a claim of test success. Do not repeat it for each reply, reference or same-workflow continuation. Name an additional method only when starting a distinct subtask that needs it.

Preserve strict output contracts. For JSON-only or another exact format, use an allowed commentary channel or existing schema field only if permitted; otherwise omit the announcement rather than add keys or break the format. A banner is not evidence of use: the method must actually have been read and its applicable checks followed.

## Delegate without losing discovery or boundaries

An execution worker gets the selected method name and its exact verified entrypoint, or the relevant loaded instructions when files are inaccessible, alongside the task scope and evidence requirements. Do not send only a bare skill name and expect the child to invent an installation path. A stale path discovered by a child follows the same bounded recovery above.

Context-only evidence/test reviewers instead receive the actual relevant excerpts and evidence. Do not require them to read skill files, execute tools or inspect product state. Their lack of tool access is an intentional boundary, not an installation failure. The lead owns the user-facing announcement; internal workers need not generate duplicate banners.
