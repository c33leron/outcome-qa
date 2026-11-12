# Security controls inside the tested feature

Use a row only when the product exposes that surface and the task's scope permits the check. Begin with a legitimate control; preserve ordinary functionality while challenging the stated boundary.

| Actual surface | Small useful comparison | Required outcome evidence |
| --- | --- | --- |
| File upload/import/archive | Accepted type versus an agreed disallowed type/content; synthetic filename/path marker where path handling is in scope | Processing and access after upload, not only MIME/extension rejection. Imported content stays within the permitted object/tenant and storage location |
| Active rendering/export | Valid punctuation/text versus a harmless active-content marker in the actual output context | Whether rendering or export executed or exposed something outside the contract; inspect HTML/attribute/URL context rather than treating an echoed string as execution |
| URL preview/fetch | Permitted destination versus a policy-forbidden but controlled destination; if relevant, one redirect between controlled endpoints | Attribute the request to the server, input and hop. A preview reaching an allowed callback is legitimate functionality, not a violation. Establish which destination/trust rule was crossed; no internal-network scan is implied |
| Webhook/event | Valid signature, invalid/missing signature, declared timestamp boundary and one replay | Correct principal/event binding and durable effect count. A rejected response must not coexist with a completed unauthorized write |
| Cross-origin read or write | Actual browser request from an allowed origin versus the selected untrusted origin, with appropriate test credentials | Read: can the untrusted origin read protected response data? Write: did protected state change? CORS and CSRF are different controls; headers alone do not establish either result |
| Error, URL, history or download | Synthetic sensitive marker and allowed/disallowed test actor | Which data was actually disclosed through which channel; redact reusable credentials and unrelated records |
| AI document/tool boundary | Benign instruction canary in lower-trust content, with one clearly prohibited action | Real tool attempt and post-state, not a polite final refusal or self-reported success |

For uploaded archives and filenames, a suspicious name alone is not a path-traversal finding. Observe the actual destination or a harmless marker within an authorized test boundary; do not target real sensitive files. Likewise, an accepted file is not automatically executable.

For callbacks, use an operator-controlled sink approved for this task and a unique harmless correlation marker. Establish server-side attribution using appropriate server/proxy traces or controlled routing; do not mistake the tester/browser following a URL for a server request. Record redirect hops and the expected destination policy. Avoid real documents, secrets, cloud metadata or unrelated internal hosts. If only static/local testing is available, retain that scope rather than inventing a callback.

For output contexts, SQL/NoSQL input boundaries and browser cross-origin controls, consult [input and browser controls](input-and-browser-controls.md) only when that surface is relevant.

Keep identity and chronology intact. A valid setup action under the owner must not be mistaken for the challenged actor's write. After a denial or timeout, independently inspect the protected state before retrying or cleaning up. Restore owned data after preserving the evidence.

For AI boundary probes, distinguish a tool attempt, its actual effect and the final message. A refusal after an observed write does not undo the write; a canary appearing in the answer must be tied to independently known source data.


## Roles, sessions and sensitive output

Use only the transitions promised by the feature and the authorized scope. For ownership/tenant checks, verify a valid object and known permitted actor before comparing the disallowed actor. For role checks, inspect the actual server-side action rather than treating button visibility as enforcement.

For logout, stale requests, reopened tabs and history navigation, distinguish cached display from a credential that still authorizes live access. Establish the expected privacy/session policy before assigning a violation. When switching actors, bind drafts, pending requests and subsequent actions to the correct session and entity; separate tabs can share server-side organization or session state.

Inspect permitted error/download/export observations for known synthetic protected markers. Keep only the minimal redacted proof: reusable tokens, cookies and unrelated private records do not belong in reports or screenshots. A changed wording or different disclosure fragment does not invalidate a leak when its protected source and boundary are independently established. Conversely, plausible invented private text is not evidence of disclosure.

Retries or concurrent edits matter to security when they cross a money, permission, entitlement, quota or notification control. A duplicate UI row alone does not establish that impact. Coordinate bounded requests on isolated state; distinguish setup writes, tested actions, background processing and owner-side observation.
