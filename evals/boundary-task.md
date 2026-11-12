# Task given to the testing agent

Test this local synthetic record feature through its real UI and narrow API controls. Alice owns `note-1`. Bob must not read or change Alice's record. A rejected request must leave the owner-visible state unchanged. Alice must still be able to read and update the record normally.

The operator supplies the loopback URL. Use only the two synthetic actor labels `alice` and `bob`; there are no passwords, real people, tenants or production authentication. For an authorized direct write/reset, GET `/api/session` and send its token as `X-Lab-Token` with JSON. Reads identify the synthetic actor through `X-Actor`.

Do not treat a hidden button or status code alone as proof. Compare the disallowed actor's response with an owner-side read-back of the same record, while keeping setup and challenged action distinct. Stop after the minimal synthetic proof; do not invent other records, enumerate IDs, inspect implementation or patch the lab. Restore the record through `/api/reset` and independently confirm Alice sees the initial canary.

Return executed coverage, expected and observed effects, whether the legitimate owner path survived, cleanup, and unresolved gaps.
