# CLAUDE.md — Financial Planning Suite

## Project Overview

This is a Streamlit-based lifetime financial planning application (V14) with:
- Multi-user authentication with household profiles (couples share financial plans)
- Monte Carlo simulation engine (historical S&P 500 + traditional modes)
- 12 tabs: Settings, Parent1, Parent2, Family Expenses, Children, House Portfolio, Economy, Retirement, Timeline, Analysis, Save/Load, Users
- Docker deployment targeting a TerraMaster F4-223 NAS

## Architecture

- **App**: Single-file Streamlit app (`FinancialApp_V14.py`, ~4,800 lines)
- **Auth**: PBKDF2-SHA256 password hashing, JSON file storage
- **Data**: Each household gets an isolated JSON file in `data/households/`
- **Deploy**: Docker + Nginx Proxy Manager for HTTPS

## v2 (React + FastAPI rewrite) — branch `v2-react`, folder `v2/`

- The Streamlit app (`FinancialPlanner_v0_8.py`) is frozen at tag `v0.8-streamlit` / branch `legacy/streamlit-v0.8` and still deploys from `main`.
- v2 shares the same data directory format — the Data Preservation Policy above applies unchanged (server merges keys, backs up before each write).
- Engine: `v2/engine/finplan` (pure numpy). Math changes vs v0.8 are listed in `v2/docs/ENGINE_CHANGES.md`; feature status in `v2/docs/PARITY.md` — keep it updated and never drop a ✅ item.
- Tests: `cd v2/engine && python -m pytest -q` and `cd v2 && python -m pytest -q server/tests` must pass; `cd v2/web && npx tsc -b` must be clean.
- Reference data (templates, tax tables, demos) is extracted from v0.8 by `v2/tools/extract_v08_data.py` — don't hand-edit the JSON.
- Demo re-tuning lives in `v2/engine/finplan/data/demo_overrides.json` (applied by `reference.demo_plans()`); edit that, not `demo_plans.json`.
- Roadmap and known gaps: `v2/docs/ROADMAP.md`. Email reminders run in-process: keep uvicorn at 1 worker.

## NAS Deployment Details

- **NAS Model**: TerraMaster F4-223 (Intel Celeron N4505, 32GB RAM)
- **NAS IP**: 192.168.68.102
- **SSH**: Port 9222, user `Gonzik`
- **SSH Command**: `ssh -p 9222 Gonzik@192.168.68.102`
- **App path on NAS**: `/Volume1/docker/financial-planner/`
- **File transfer**: Copy files via SMB to `\\192.168.68.102\Gonzik\Transfer\` then SSH `cp ~/Transfer/* /Volume1/docker/financial-planner/`
- **Docker**: Already installed on the NAS

## How to Deploy Updates

### Step 1: Copy changed files to NAS
The NAS SMB share is accessible at `\\192.168.68.102\Gonzik\Transfer\`.
Files placed there appear at `~/Transfer/` on the NAS via SSH.

From this repo directory, copy the app file:
```bash
# On Windows (if SMB drive mapped):
copy FinancialApp_V14.py Z:\Transfer\
# Or from WSL/Linux:
cp FinancialApp_V14.py /mnt/z/Transfer/
```

### Step 2: SSH and deploy
```bash
ssh -p 9222 Gonzik@192.168.68.102
cp ~/Transfer/FinancialApp_V14.py /Volume1/docker/financial-planner/
cd /Volume1/docker/financial-planner
docker-compose -f docker-compose-local.yml build --no-cache
docker-compose -f docker-compose-local.yml up -d
```

### Step 3: Verify
Open `http://192.168.68.102:8501` in a browser.

## Data Preservation Policy (CRITICAL)

Real users store financial plans in `data/households/<id>.json`. These files contain irreplaceable user-entered data. **ANY code change that touches persistence must follow these rules:**

1. **NEVER delete or overwrite** a household file without creating a backup first. Backups go to `data/backups/<id>_<timestamp>.json`.
2. **ALWAYS load the existing file before writing** — merge, don't replace. This preserves metadata, scenarios, and fields added by other versions.
3. **NEVER change the JSON schema in a breaking way.** New fields are fine; removing or renaming existing keys will corrupt older data. If a schema migration is needed, write a migration function that runs on load.
4. **The `households_index.json`** maps household IDs → member lists. Losing an entry here orphans the data file. Backup before every write.
5. **Test households** (prefixed `_test_`) are ephemeral and exempt from backups.
6. **Auto-save** on every interaction (in `main()`) is silent — it must NEVER throw an exception that interrupts the user.
7. When changing `save_data()` / `load_data()` / any `household_*` function, **verify that existing household files still load correctly** after the change.

## Critical Rules for Code Changes

### NEVER regress features. V14 has ALL of these — verify they survive any edit:

**11 Original Tabs (from V13):**
1. Settings (parent names, emojis, marriage year, current year)
2. Parent X (income, age, raises, job changes, net worth, retirement, SS)
3. Parent Y (same structure)
4. Family Expenses (dynamic categories, state templates CA/WA/TX, recurring expenses, one-time purchases, tax settings)
5. Children (per-child age 0-30 expenses, 11 categories, state templates, CSV import/export, duplicate name prevention)
6. House Portfolio (multiple houses, timeline Own_Live/Own_Rent/Sell, mortgage, property tax, insurance, maintenance, upkeep, ownership)
7. Economy (3 scenarios: Conservative/Moderate/Aggressive, investment return, inflation, expense growth, healthcare inflation)
8. Retirement (SS with insolvency modeling, early/delayed benefits, income replacement)
9. Timeline (consolidated visual timeline of all events)
10. Analysis (Monte Carlo: traditional asymmetric + historical S&P 500 modes, today's dollar normalization, Plotly charts, percentile bands, yearly breakdown)
11. Save/Load (JSON export/import, internal scenario save/compare, household persistence)

**V14 Additions:**
12. Users tab (profile management, household members, invite code, password change, logout)
13. Login/Registration page with PBKDF2-SHA256 hashing
14. Household profiles (shared financial plans via household code)
15. Persistent file storage (survives Docker restarts)
16. Sidebar quick save/logout buttons

**V14 Bug Fixes (DO NOT REVERT):**
- SS income variability: `employment_income * income_multiplier + ss_income` (line ~2975) — SS is NOT varied
- maintenance_rate: `annual_maintenance = current_home_value * house.maintenance_rate` is used in simulation
- healthcare_inflation_rate: Children's Healthcare column uses `scenario.healthcare_inflation_rate` not general inflation

## Key Data Structures

- `HISTORICAL_STOCK_RETURNS` — 100 years of S&P 500 annual returns (list of 100 floats)
- `CHILDREN_EXPENSE_TEMPLATES` — State/strategy expense arrays, all length 31 (ages 0-30)
- `FAMILY_EXPENSE_TEMPLATES` — State/strategy annual family expenses
- `House` dataclass with `HouseTimelineEntry` list
- `RecurringExpense` and `MajorPurchase` dataclasses
- `EconomicScenario` dataclass (investment_return, inflation_rate, expense_growth_rate, healthcare_inflation_rate)

## Testing

Run the verification suite to confirm no regressions:
```bash
python v14_verify.py
```
All 75 tests must pass. The original 77-test stress test is in `stress_test.py`.

## File Structure

```
├── FinancialApp_V14.py          # Main application (THE app)
├── Dockerfile                    # Docker build instructions
├── docker-compose.yml            # HTTPS deployment (app + Nginx Proxy Manager)
├── docker-compose-local.yml      # Local-only deployment (no HTTPS)
├── requirements.txt              # Python dependencies
├── streamlit_config.toml         # Streamlit server config
├── Launcher.py                   # Desktop launcher (PyInstaller)
├── SETUP_GUIDE.md                # General deployment guide
├── HTTPS_SETUP_GUIDE.md          # HTTPS/SSL setup guide
├── stress_test.py                # 77-test calculation stress test
├── v14_verify.py                 # 75-test V14 verification suite
├── CLAUDE.md                     # This file
└── deploy.sh                     # One-command NAS deployment script
```
