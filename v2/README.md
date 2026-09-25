# Financial Planning Suite v2

A rebuild of the Streamlit app as a modern web app. It has a React front end, a
FastAPI back end, and a pure numpy engine. It reads and writes the **same
household files** as `FinancialPlanner_v0_8.py`, so both can run side by side.

```
v2/
├── engine/     finplan: plan schema + migration, templates, taxes,
│               projection + Monte Carlo (pure Python/numpy) + pytest suite
├── server/     FastAPI: auth (Cloudflare header / email), households,
│               plan merge-save with backups, scenarios, engine endpoints,
│               serves the built web app
├── web/        React + TypeScript + Vite + Tailwind + Recharts
├── tools/      extract_v08_data.py (pulls templates/demos from v0.8)
└── docs/       ENGINE_CHANGES.md (math changes vs v0.8), PARITY.md (feature checklist)
```

## Run locally (development)
```bash
# terminal 1: API (from v2/)
pip install -r requirements.txt
DATA_DIR=./app-data-v2 uvicorn server.app:app --reload --port 8502

# terminal 2: web UI with hot reload
cd web && npm install && npm run dev      # http://localhost:5173 (proxies /api to 8502)
```
Or build once and let FastAPI serve it: `cd web && npm run build`, then open http://localhost:8502.

On Windows PowerShell, set the variable first: `$env:DATA_DIR="./app-data-v2"`.

## Run on the NAS (Docker, next to the Streamlit app)
```bash
cd /Volume1/docker/financial-planner/v2
cp -r ../app-data ./app-data-v2     # optional: try it on a copy of real plans
docker-compose up -d --build        # http://NAS_IP:8502
```
The Streamlit app keeps running on 8501. When you're happy with v2, point the
volume in `docker-compose.yml` at `../app-data` (every save makes a backup in
`data/backups/`). Behind Cloudflare Access, set `ALLOW_DEV_LOGIN=0`.

## Tests
```bash
cd v2/engine && python -m pytest -q          # engine: taxes, mortgages, SS, MC, migrations
cd v2 && python -m pytest -q server/tests    # API: auth, merge-save, backups, encryption
```

## How it works
- **Live recalculation.** Every edit updates the plan in the browser. The UI calls `/api/project` (≈20 ms) and a 1,000-path Monte Carlo (≈50 ms) after short debounces, then auto-saves via `PUT /api/plan`.
- **Data safety.** The server merges incoming keys into the stored plan, so keys it doesn't know are never dropped. It writes a timestamped backup first and writes atomically. `normalize_plan()` migrates V13/V14/partial files on load without mutating the source.
- **One engine.** The deterministic projection is just the Monte Carlo engine with one path and no randomness, so the two can't drift apart.
