# Input interpretation and browser trust

Choose the section matching an actual feature or requested security question. A search box, rich-text field and authenticated API have different contracts; testing each listed class by default adds noise rather than coverage. Start with a working control and synthetic data, then change one meaningful condition.

## Search/filter input: data versus query structure

Establish which syntax the API intentionally supports. A documented filter language or allowed operator is not an injection merely because it changes results. Identify the parameter/type, intended predicate and permitted object scope before probing.

- Use a small owned fixture whose known rows distinguish the expected result from a changed predicate. Include a valid value containing ordinary punctuation where the field permits it; a quote in a person's name must not automatically become a security rejection.
- Compare the valid scalar/type with one bounded challenge to query interpretation. For SQL, inspect parameter binding versus string construction when source is available. For NoSQL, distinguish an expected scalar from an unexpected object/operator shape at the actual parser/query boundary.
- Observe returned synthetic row IDs/counts, an authorized trace or another independent result that discriminates the expected predicate from altered query semantics. Keep authorization effects separate from ordinary search/filter behavior.
- A database error, HTTP 500, changed response length or input echo is a lead, not proof of injection. A gateway/schema rejection may prevent the probe from reaching the query; state that boundary instead of claiming the database is secure.
- Static reachable concatenation can support a static finding; a local parameterization test can establish that local path. Neither is an observed deployed exploit. Do not use database dumps, expensive delay functions, stacked destructive statements or volume probes as routine QA confirmation.

If a fix rejects the challenge, replay the legitimate punctuation/type control and verify the intended query still works. Rejecting every request is not a successful fix.

## User content: text versus active browser behavior

Follow a unique benign marker from the real input to each relevant output location: immediate display, saved/reopened record, preview or export. Classify the actual sink: text node, HTML, attribute, URL or another executable context. The encoding/sanitization requirement depends on that context and on whether controlled rich content is intentionally allowed.

- Establish that normal text, allowed markup and valid punctuation still render according to the feature contract. Do not call intentional allowed formatting a vulnerability.
- Where an active-content challenge is in scope, use a harmless local DOM/console marker with no network request, secret access or persistent side effect. Confirm actual execution/navigation behavior in the browser context under test; encoded text appearing on screen is not script execution.
- A stored marker must be traced to its saved source and subsequent rendering. Use an owned viewer/session when cross-user rendering is material; one author-only preview does not establish victim reachability.
- Preserve the real path. Executing code through DevTools, injecting a script into the page or rewriting the response to add the marker proves the harness can execute code, not that the application has XSS.
- If a browser control blocks execution, report what was observed and inspect the transformation/sink separately. One blocked marker does not prove every output context is safe, and an unsafe static sink is not identical to demonstrated runtime execution.

For client-side URL sinks, distinguish a permitted navigation from a prohibited destination or active URL interpretation; a string containing a URL alone is not a finding.

## Cross-origin browser reads and writes are separate

Use a real browser from a separately controlled origin and a synthetic test user's state. Record which credentials the browser actually sent, whether a preflight happened and whether the challenged request reached the server. A command-line request with a forged `Origin` can inspect server behavior, but it does not reproduce browser cookie, preflight or response-access rules.

**Read boundary — CORS:** establish that the response contains protected synthetic data and the test origin should not read it. Compare the legitimate origin with the selected untrusted origin under the relevant credential mode. Confirm whether script at that origin can actually read the response marker. Permissive headers, reflected origin text or a public unauthenticated response alone do not prove disclosure.

**Write boundary — CSRF:** establish a cookie-backed state-changing action and a legitimate same-origin control. Perform the bounded cross-origin action that the browser can really issue under the applicable session/cookie behavior; independently read protected state afterward. A blocked response read does not mean the write was blocked. Conversely, a request that never carried an authenticated session does not exercise the authenticated mutation boundary.

When replaying a fix, preserve both branches relevant to the finding: the unauthorized read/write must be prevented and the legitimate application action must still work. Do not turn one browser observation into an assertion about every browser or deployment.

Technique terminology was cross-checked against primary guidance; the procedure above is independently written: [OWASP WSTG reflected XSS](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/07-Input_Validation_Testing/01-Testing_for_Reflected_Cross_Site_Scripting/) and [OWASP WSTG SQL injection](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection/). These links are references, not required tool calls or a bundled scanner.
