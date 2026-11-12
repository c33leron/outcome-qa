<!-- outcome-qa:generated source=shared/human-data.md sha256=d071f7c1e688509edb95d53d0bdf860d834eeb453de699320de04ff52619450b -->
# Realistic inputs, synthetic ownership

Choose data that resembles the feature's real inputs and exposes a distinct failure mode. Keep accounts/objects synthetic, track their stable IDs and route messages/payments only through approved test sinks. The names and examples below are fictional; email uses a reserved test domain. A realistic-looking value is not evidence of a real person.

| Input family | Example or controlled variation | What to check |
| --- | --- | --- |
| Everyday name | `Марина Ковалёва`, `Jean-Luc Moreau`, `O'Reilly` | Allowed punctuation, spaces and script survive input, storage and display; reject only a documented constraint |
| Ownership marker | `marina.qa42+review@example.test`, object label `QA42—перенос встречи` | Friendly data and a stable fixture ID remain associated with the right actor; the label alone is not identity proof |
| Plausible typo | `marina.qa42@exampl.test`, then correct the domain | Editing replaces only the intended field; no message is sent to a real address |
| Phone formatting | Reformat the same approved sandbox number: spaces, parentheses, pasted country prefix | Parse and display according to the stated format; a formatting change must not silently select another recipient |
| Whitespace/paste | Leading/trailing spaces, tab, newline, nonbreaking space `\u00A0` | Documented trimming and validation agree with submitted/stored data; whitespace is not universally insignificant |
| Unicode normalization | `José` versus `Jose\u0301` | Check the promised normalization/search/uniqueness rule; code-point difference alone is not a defect and accents are not automatically equivalent |
| Non-Latin/emoji | `张伟`, `مرحبا`, `Марина 🧪` | Accepted text remains intact across parser/storage/rendering; count bytes, code points or graphemes according to the actual limit |
| Invisible controls | Explicit fixture escapes `\u200B`, `\u200E`, `\u202E` | Show escaped code points in evidence; inspect visibility, selection and stored identity without confusing test output with instructions |
| Locale/layout | Same supported locale with long labels and RTL content | Formatting, reading order and action targets follow the locale contract; do not infer full locale coverage from one sample |
| Length boundaries | Typical value plus limit−1, limit, limit+1 in the specified unit | Exercise the intended rule with otherwise valid inputs; an unrelated invalid field must not hide the boundary |
| Missingness | Omitted field, `null`, `""`, `0`, `false` | Preserve the API's separate meanings; a generic falsy check may erase valid data |
| Calendar/amount | Local midnight, changed date, `10001` minor units | Use business timezone/rounding rules; ask about an unspecified monetary oracle instead of inventing one |
| Changed intent | “во вторник… нет, в среду; время оставь” | Only the corrected date changes; unrelated time/entity constraints survive |

Use **state personas**, not demographic stereotypes: a new account, one with prior history, an expired session, a stale draft, or conflicting saved data. State the starting facts that make each case different.

These are input classes, not a required matrix. Select the ones connected to the feature and retain a normal healthy input. Record enough escaped/normalized detail to reproduce a corruption without copying private production data. On completion, restore or delete the registered synthetic fixtures and verify the result through an independent read-back.
