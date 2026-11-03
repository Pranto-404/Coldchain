# ColdChain V12 — accounts, dark/light themes, hands-on hardware

**Live:** https://coldchain-monitor-30qu.onrender.com

## Create an account
- Front page has **Sign in / Create account** tabs plus three dedicated demo buttons (Admin, Pharmacist, Inspector).
- Sign-up: username or email, password with a strength meter, confirmation, and an access choice.
- Security: every new account starts as a **read-only Inspector**. Choosing Pharmacist only files a request;
  an Admin approves it with one click on the Users page (a badge in the sidebar counts pending requests).
  Nobody can register as Admin. Usernames are unique regardless of case; sign-ups are limited to 5 per
  network per hour. Set `ALLOW_REGISTRATION=0` to switch sign-up off.

## Dark and light mode
- Sun/moon switch on the front page and in the top bar (or press **T**). Follows the device setting until
  the user picks one; the choice is remembered. Every colour — charts, dials and the hardware drawing —
  has a value for each theme.

## Front page
- One coherent theme (no more half-dark / half-light), slowly drifting aurora background, rising frost
  particles, animated headline, a looping thermostat preview card, count-up figures, and a server
  status chip that says "waking up" while Render's free instance starts.

## Inside the app
- Sliding highlight follows the active page in the navigation; button ripples; loading skeletons;
  toasts with a countdown bar; smooth theme cross-fade; hover lift on cards.

## Hardware: manual operation
- **Manual control** panel: Door, Mains power, Wi-Fi, Compressor (weak/healthy) and Heat load switches,
  a **probe-temperature slider** (0–15 °C) and *Ice pack −2 °C* / *Warm hand +2 °C* buttons.
- Keys on the Hardware page: **D** door · **P** mains · **W** Wi-Fi · **C** compressor · **H** heat.
- The compressor in the drawing is clickable too. Every action is audit-logged and shown in the serial monitor.

## Cross-device
- Touch targets ≥ 42 px on touch screens, stacked layouts below 1180 px, two-row navigation on phones,
  the hardware drawing scrolls sideways on small screens, toasts span the width on phones.

## Tests
`pytest`: 41 passed (adds sign-up/approval, sign-up rate limit and probe-control tests).
