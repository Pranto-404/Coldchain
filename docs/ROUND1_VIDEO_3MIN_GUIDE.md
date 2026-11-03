# FastRoboX 1.0 — ColdChain Round 1 software simulation presentation

## Rules from organizing email (21 Oct 2026)

- Show **at least three** challenge questions, with a video **not exceeding 3 minutes**.
- Upload the recording to Google Drive or YouTube (Unlisted). Submit the **accessible link** via https://forms.gle/be3EuPwQvHPZ8WTm7.
- Deadline listed: **5 November 2026**. The email gives no exact clock time.
- Selected focus: **Q4 (Web App), Q2 (Heat-Exposure Budget), Q5 (AI Prediction & Relocation)**.
- **Software simulation only**. Never claim working real ESP32 devices or medically validated cooling performance.

## Before screen recording

1. Extract the project and launch `START_DEMO_WINDOWS.bat`. The BAT attempts to install Python and dependencies if missing.
2. Make the browser 1920×1080 if possible, zoom 90–100%, and maximize it. Hide personal notifications and other tabs.
3. Select Admin on the login screen, then click **Enter dashboard**. Let both synthetic fridges populate.
4. Practice clicking **Simulation lab** and locating the **Three-minute presentation scenes** panel.
5. To restart an example, press **Safe · 100% left** in the scene panel. The specially labeled `SIM-R1-EXPOSURE` sample is used by the staged scene. Other batches are unaffected.
6. For the Q5 transfer, **Stage forecast risk**, return to Overview, and wait until Fridge Alpha shows a warning with a safe Beta destination. After filming that screen, sign out and log in as Pharmacist to confirm the recommended stock assignment.
7. All dynamic data are simulated. The recorded values will naturally differ with time and simulation state. Read the actual on-screen values; do not hardcode a prediction number into voice-over.

## Proposed video timings (target 2:55 total)

| Time | On screen | Question |
|---|---|---|
| 00:00–00:15 | Project name, simulation notice, both fridges | Introduction |
| 00:15–01:05 | Overview, Inventory + public QR, three roles, Verify Integrity | **Q4** |
| 01:05–01:45 | Simulation lab: At Risk, Inventory; then Discard | **Q2** |
| 01:45–02:40 | Stage forecast risk, return Overview, show forecast/health/relocation; Pharmacist confirmation | **Q5** |
| 02:40–02:55 | QA summary, honest limitation, thanks | Closing |

## Sample English narration (adapt while you record)

**00:00–00:15 — Introduction**  
“Hello judges. We are presenting ColdChain, a software-simulated vaccine and medicine storage monitoring system. Our demonstration covers questions four, two, and five: the web application, heat-exposure budget, and predictive relocation.”

**00:15–01:05 — Question 4**  
“Our application provides separate Admin, Pharmacist, and Inspector roles, with server-enforced permissions. The dashboard shows two simulated refrigerators, temperature, door state, power, compressor activity, and current risk. In Inventory, each batch has a storage assignment, expiration date, and remaining heat budget. A QR code opens a public batch status check without login. On the Security page, a Verify Integrity action checks our hash-chain audit trail. Device messages are authenticated using HMAC signatures, timestamps, and anti-replay nonces.”

**01:05–01:45 — Question 2**  
“Next, let us demonstrate the sixty-minute heat-exposure budget using an explicitly synthetic historical scenario. Time above eight degrees is counted normally, while time above twelve degrees is doubled. Forty minutes at nine degrees, plus five and a half minutes at thirteen degrees, produce fifty-one weighted minutes, leaving fifteen percent of the budget: At Risk. With ten minutes above twelve degrees instead, the weighted budget reaches sixty minutes, so the batch becomes Discard. These staged examples do not pretend to be actual sensor measurements.”

**01:45–02:40 — Question 5**  
“Finally, the simulation lab prepares a rising-temperature scenario for Fridge Alpha. Our model estimates temperature thirty minutes ahead and flags possible breaches above eight degrees. We also display an indicative compressor health score from observed cooling trends. When another simulated fridge is currently suitable, the application recommends eligible batches for relocation. A Pharmacist can confirm the proposed digital inventory transfer in one action. The model was trained and tested on synthetic thermal trajectories, so field validation would still be required before clinical use.”

**02:40–02:55 — Conclusion**  
“Our prototype demonstrates interconnected monitoring, batch protection, role-based workflows, security verification, and prediction-driven decision support. All results shown here are simulations, not clinical performance claims. Thank you.”

> Narration is a sample, not a validated 2:55 audio track. Rehearse with a timer and shorten any section that runs long. Show actual controls working, not just slide animations.

## Submission checklist

- [ ] Show questions 2, 4 and 5 explicitly on screen.
- [ ] Demonstrate each relevant workflow instead of claiming unseen hardware.
- [ ] Keep simulation and synthetic training labels readable.
- [ ] Record an actual playable MP4 under three minutes, with intelligible audio.
- [ ] Avoid implying real compressor actuation or external alert delivery.
- [ ] Upload as Google Drive (view access for reviewers) or Unlisted YouTube.
- [ ] Open link in private/incognito mode without signing in.
- [ ] Submit link at https://forms.gle/be3EuPwQvHPZ8WTm7 by 5 November 2026.

## About offline simulation

The simulator generates signed samples at 5-second intervals. It can demonstrate Wi-Fi loss, RAM buffering and replay on reconnection, but **not the persistent ESP32 offline-buffer behaviour on hardware**. That distinction should remain explicit if you discuss question 3.
