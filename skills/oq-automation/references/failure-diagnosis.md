# Classify a failing automated check

These are investigation outcomes, not labels to assign from an exception string alone.

| Possibility | Discriminating observation | Useful next probe |
| --- | --- | --- |
| Product defect | The specified user effect is wrong under valid conditions | Repeat the critical action with equivalent data and independently inspect the result |
| Test defect | The product meets the rule but the test observes or expects something else | Examine locator/assertion, actual state and the latest expected rule |
| Fixture or environment failure | The test never reaches the claimed check | Validate just the missing setup, role, connection or dependency |
| Intermittent behavior | Comparable attempts disagree | Preserve attempts, correlate state/timing and test one plausible cause |
| Insufficient evidence | Available output cannot distinguish these causes | Name the missing observation and the cheapest permitted check that could obtain it |

A timeout may mean a blocked control, missing event, dead connection, wrong locator, slower operation or an operation that completed after the client stopped waiting. It is not automatically a product hang or a test issue.

Start with the first causal failure in a cascade. If authentication fails, ten dependent assertions are not ten separate product defects. Conversely, a setup warning must not erase an independently observed data corruption later in the run. Inspect the final runner result: a failed observation inside a successful bounded poll is not a separate failed test.

Compare failing and working attempts by build/config, account/role, fixture, sequence and observation channel. Preserve an allowed alternate-path control as a control: an API success cannot certify a broken browser path.

After a retry, count side effects and cleanup owned data. Do not make another mutating attempt merely because the runner offers “retry”. If the operation outcome is unknown, establish it first or use a permitted duplicate-safe recovery mechanism.
