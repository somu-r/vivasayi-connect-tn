# Vivasayi Connect TN — MVP

A local demonstration prototype for agricultural stock visibility, farmer requests, officer workflow, announcement logging, and simulated IVR.

## Included
- Farmer portal: see sample stock and create a supply request
- Officer dashboard: review requests, update statuses, view demand and low-stock alerts
- Stock update page
- Announcements page: creates one demo SMS-log entry per demo farmer
- Demo SMS log (messages are NOT sent)
- Browser-simulated IVR menu using the sample stock database
- SQLite database automatically seeded with fictional data

## Requirements
- Python 3.10+
- Internet is not needed after Flask is installed

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Demo test plan
1. Home page: review fictional stock.
2. Farmer portal: create a request for Paddy seeds.
3. Officer dashboard: move the request from Pending to Under review or Approved.
4. SMS log: inspect the demo confirmation and status update.
5. Stock page: set DAP fertilizer to zero or update another item.
6. Announcements: publish a demo announcement and see log entries.
7. IVR demo: choose a product and test the spoken-response text.

## Important limitations
- All names, phone numbers, village and stock are fictional sample data.
- SMS entries are logged only; no SMS is sent.
- IVR is simulated in the browser; no telephone call is placed.
- There is no login, authorization, audit-grade inventory, or production security.
- Do not deploy this prototype publicly or enter real farmer personal data.
- Before a real pilot, add authenticated roles, HTTPS, input/security hardening, backups, privacy/retention rules, consent and opt-out handling, approved SMS/voice provider integration, monitoring, accessibility and Tamil localization, and government/department approvals.
- Stock reservation and physical dispatch are not automated. An authorized officer must verify and approve real stock movements.
- The app is a concept prototype, not an official Government of Tamil Nadu service.

## Suggested next build phase
1. Tamil/English UI and voice prompts.
2. Secure officer login and role-based access.
3. Product-specific minimum stock thresholds.
4. Real SMS provider adapter and delivery-status webhook.
5. Real IVR provider webhook and DTMF menu.
6. Exportable district reports and request escalation.
7. Pilot testing with a cooperative society after written authorization.
