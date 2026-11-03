# ColdChain V9 — Vercel Website + Render Backend

> This is a deployment preparation kit, **not a live deployment**. It is a competition simulation, not a medical system. Do not use real patients, vaccines, or secret devices. Publishing demo credentials makes the demo alterable by visitors. Prefer private access and reset the demo after testing.

## Why two services?
The original V8 includes an always-running Python simulator, local SQLite, and MQTT bridge. Vercel supports Python/FastAPI as Functions, but its read-only ephemeral function filesystem and lifecycle are not suitable for this architecture as-is.

- **Render:** Python FastAPI web service and simulator.
- **Vercel:** frontend static HTML/CSS/JavaScript + rewrites for `/api/*`, `/check/*`, `/health`.
- **GitHub:** private source repository and automatic redeploy for both services.

## STEP 1 — GitHub

Create a new private GitHub repository, for example `coldchain-hackathon`. Upload/extract all project files at the repository root. Ensure `.env`, `ONSITE_PRIVATE_CREDENTIALS.txt`, generated secrets and database are NOT committed. `.gitignore` excludes them; verify anyway. Do not upload the ZIP as a single file; upload its **contents**.

## STEP 2 — Render backend FIRST

- Render dashboard → New → Web Service → connect GitHub repository.
- Root Directory: repository root (leave blank).
- Language: `Python 3`.
- Build command: `pip install -r requirements.txt`.
- Start command: `uvicorn coldchain.app:app --host 0.0.0.0 --port $PORT`.
- Environment variables:
  - `DEMO_MODE=1`
  - `MQTT_ENABLED=0`
  - `JWT_SECRET=` generate a RANDOM secret of at least 32 characters directly in Render; do NOT put it into GitHub.
  - `PYTHON_VERSION=3.12.11` (or rely on `.python-version`, 3.12).
- Deploy and visit `https://your-project.onrender.com/health` — it should return `{"ok":true,...}`.
- Render Free services can spin down after 15 minutes and local SQLite data is lost on restart/deploy. For demo reliability use paid always-on with a persistent disk and set `DB_PATH=/var/data/coldchain.db`, mount `/var/data`. SQLite is not intended for multi-instance cloud scaling.
- Don't set `DEMO_MODE=0` without generating **private** login passwords and device secrets.

## STEP 3 — Vercel frontend

1. Run `CONFIGURE_VERCEL_FRONTEND_WINDOWS.bat` from the project root. Enter actual Render backend URL. This writes `vercel-frontend/vercel.json`. Alternatively edit it in a text editor.
2. Git commit and push the change.
3. Vercel → Add New → Project → import **the same GitHub repository**.
4. Root Directory: **`vercel-frontend`**.
5. Framework: `Other`; Build Command: leave empty; Output Directory: `public`.
6. Deploy. Open the `https://...vercel.app` URL. Frontend should load. `/health` on this domain should be proxied to Render.
7. In Render environment, set `PUBLIC_BASE_URL` to your **exact Vercel URL**, such as `https://coldchain-demo.vercel.app`. Deploy/restart backend. This ensures generated QR codes open on the Vercel domain.
8. Test Admin/Pharmacist/Inspector login and API requests. For a demo-only sandbox, use the original README demo accounts. These are public demo passwords, NOT safe production credentials.

## STEP 4 — acceptance checks

- Vercel `/` shows login (not 404).
- Vercel `/health` returns JSON from Render.
- Admin login works; fridge cards refresh every 5 seconds while Render is awake.
- Q2 exposure scenarios, inventory & QR public check, Q5 forecast and relocation work; verify both user permissions.
- Refresh the dashboard, reopen in a separate browser; test website on phone too.
- Remember SQLite on Render Free loses data on sleep/restart/deploy.

## Important hackathon note

The local MQTT broker, ESP32, and hardware launcher do **not** automatically work through this Vercel deployment. Physical ESP32s should use the local V8 hardware stack or a separately secured, always-on MQTT broker/backend accessible from the event network. Do not expose the local unauthenticated demo broker or secret keys on the internet.

## Official references

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/routing/rewrites
- https://vercel.com/docs/builds/configure-a-build
- https://render.com/docs/deploy-fastapi
- https://render.com/docs/free
