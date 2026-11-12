# Task given to the testing agent

Test this local room-booking feature through the browser. You may create and reset synthetic bookings in this lab. Do not edit the app or inspect its implementation during the first black-box pass.

Contract:
- The reservation must use the calendar date currently entered by the user.
- Retrying the same submission (`request_id`) must not create another reservation.
- Reusing that identifier for different data must be rejected without changing the original reservation.
- A successful reservation remains visible after reloading the page while this server process is running. Disk persistence across a server restart is not promised.

The operator supplies the local URL. The list at `/api/bookings` is an independent read-back channel; it is not a replacement for submitting through the real UI when making a UI claim. For authorized CLI cleanup or direct API controls, first GET `/api/session` on the same loopback origin and send its token as `X-Lab-Token` with `Content-Type: application/json`; this is a local lab capability, not production authentication. The lab has no login, payment, email or actual AI. Do not invent checks or findings for those capabilities.

Return what you actually executed, findings with expected/observed effects, and unresolved gaps. Reset only this lab's synthetic data after recording relevant evidence. A patch is not requested.
