# Security policy

Outcome QA contains agent instructions, local helpers and host adapters. Security reports are welcome for defects in those components—for example unsafe file handling, unintended overwrites, command execution, disclosure of private data or broken trust-boundary handling.

## Report privately

Use the repository's **private vulnerability reporting** feature when it is enabled. If that option is unavailable, open an issue containing only a request for a private reporting channel and a broad component name. Do **not** include exploit details, credentials, private endpoints, client data or raw evidence in that public issue.

This project does not publish an email address or promise a response-time SLA. Include the following in the private report once a channel is established:

- Package version and affected component.
- Host, OS and relevant tool versions.
- Expected behavior and observed behavior.
- A minimal reproduction using synthetic files, accounts and data.
- Impact, required preconditions and any proposed fix.

Keep real secrets out of the reproduction. If a secret has already been exposed, rotate or revoke it through its owner rather than relying on deletion of a message.

## Scope and safe reproduction

Report defects in Outcome QA itself separately from defects found in a product you are testing. Use local fixtures or systems you are authorized to test; stop after the minimum evidence needed. Do not upload third-party private reports or production data to demonstrate a package issue.

Skills guide an agent; they are not a security sandbox. The host supplies permissions, tools and model access. Local helper validation checks explicit input and filesystem boundaries; it does not authenticate the truth of an observation or make sensitive evidence safe to publish.

## Supported releases

Security fixes target the latest published release. Older versions may need an upgrade; no long-term-support branch is promised. The initial release line is `0.1.x`.

For ordinary installation problems, missed checks and incorrect QA conclusions, use [Support](SUPPORT.md).
