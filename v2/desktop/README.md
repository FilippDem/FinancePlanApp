# Desktop window (Windows)

v2 can run as its own desktop window instead of a browser tab. The app is the same React + FastAPI app,
wrapped by [pywebview](https://pywebview.flowrl.com/) on the Edge WebView2 engine that ships with
Windows 11.

```
v2/desktop/
├── launcher/
│   ├── desktop.py               the window: splash, local server inside the process, This computer / NAS, problem page
│   ├── start.ps1                first-run setup (Python, .venv, packages, shortcuts), then opens the window; -Browser = old way
│   ├── run_server.py / stop.ps1 browser mode: background server and how to stop it
│   ├── backup.ps1               zips data\ to OneDrive (or another folder), keeps 30, checks each zip restores
│   ├── requirements-desktop.txt pywebview (+ pythonnet on Windows)
│   ├── planner.ico
│   └── wheels/                  proxy_tools wheel (pywebview dependency that is only published as source)
├── root/                        the .bat files and README.txt that sit at the top of the installed folder
└── make_package.py              builds the installable folder (and zip) from this repo
```

## How it works
- **Two connection modes**, chosen from the sidebar item just above "Dark mode". It only appears inside the
  window: `Shell.tsx` → `DesktopConnection` uses `window.pywebview.api`.
  - **This computer** (default): `desktop.py` starts the FastAPI app with uvicorn in a thread of the same process,
    on 127.0.0.1:8502, or the next free port. Closing the window stops it. If a browser-mode server
    (`run_server.py`) is already on 8502, it is replaced.
  - **Our NAS**: the window opens a planner running elsewhere, such as `http://tm223_nas:8502` on the LAN or the
    Cloudflare address. Nothing runs locally. The address is checked before saving, and if the NAS is down at
    start-up a problem page offers "Try again / Use this computer instead / Connection settings".
- **The window's own pages** (splash, problem, connection) come from a tiny HTTP server on 127.0.0.1 with a random
  token in every path. They are not injected HTML, which some web engines handle badly after navigation. Their
  buttons `fetch()` actions from that server.
- **Settings**: `settings.json` holds the mode, NAS address, window size and maximized state. Sign-in cookies stay
  in `webview-data/` (`private_mode=False`).
- **Downloads** (reports, CSV/JSON exports) open a Save dialog (`ALLOW_DOWNLOADS`). Links with `target=_blank` open in
  the normal browser.
- **One window at a time**: a second launch brings the open window to the front.
- **Logs**: `logs/desktop.log` (the window) and `logs/server.log` (uvicorn).
- **Packages**: `start.ps1` and `desktop.py` both keep a SHA-256 stamp of each requirements file in `.venv`, so an
  update that changes requirements installs them on the next start.
- **Testing without a screen**: a file named `.smoke` in the installed folder makes the next start open, check that
  the planner rendered (`SMOKE OK` / `SMOKE FAIL` in `logs/desktop.log`) and close. `python launcher/desktop.py --smoke`
  does the same.

## Build and install
```
python v2/desktop/make_package.py --build-web --zip
```
Unzip anywhere (the installed copy lives in `C:\Users\filip\Documents\FinancialPlanner`) and double-click
**Start Financial Planner**. After that, use the **Financial Planner** shortcut on the desktop or in the Start menu.

To update an installed copy, replace `app/`, `launcher/` and the `.bat` files. Keep `data/`, `settings.json`,
`webview-data/`, `.venv/` and `logs/`. A daily backup task (below) points at `launcherackup.ps1`, so it keeps working.

## Backups off this computer
The planner's own `data/backups/` protects against bad edits, not against losing the disk. `launcher/backup.ps1`
zips the whole `data/` folder to a folder that syncs somewhere else.

- **Where**: `-Target <folder>`, else `"backup_dir"` in `settings.json` (environment variables like `%OneDrive%` work;
  `desktop.py` keeps keys it doesn't know), else `%OneDrive%\FinancialPlanner-backups`. With none of them it logs
  `FAIL: no backup folder` and exits 1.
- **What**: `FinancialPlanner-data-<yyyyMMdd-HHmmss>-<fingerprint>.zip` holding `data/...` (forward-slash names, opens
  anywhere). `data/` is copied to a temp folder first and the copy is zipped, so a save during the backup can't produce a
  half-old, half-new zip. `data/.session_secret` is left out (the server makes a new one; you sign in again).
  Nothing in `data/` is changed.
- **Idempotent**: the fingerprint is a SHA-256 over every file's path and hash. If the newest zip has the same one, no new
  zip is made (`unchanged since ...`). `-Force` makes one anyway.
- **Restore test on every backup**: the new zip is unzipped to a temp folder; `households_index.json` and each
  `households/*.json` must parse as JSON objects, every household in the index must have its file, and every file must
  match the copy byte for byte. Only then is it moved into the target. A failing zip is never saved.
- **Keeps the newest 30** (`-Keep N`). Only `FinancialPlanner-data-*.zip` files in the target folder are ever removed.
- **Log**: `logs/backup.log`.

Run it now: double-click **Back Up Plans Now** in the installed folder, or
```
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\filip\Documents\FinancialPlanner\launcher\backup.ps1"
```
Check the newest backup (or `-Zip <file>`) without making a new one:
```
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\filip\Documents\FinancialPlanner\launcher\backup.ps1" -Check
```
**Daily backup** (run once; adds a Task Scheduler task "Financial Planner backup" for your user at 12:30, no admin needed;
if the PC is asleep then it runs at the next chance; `-At 21:00` picks another time):
```
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\filip\Documents\FinancialPlanner\launcher\backup.ps1" -Register
```
Remove it with `-Unregister`. The task runs only while you're signed in (it needs your OneDrive).

**Restoring**: close the planner, rename `data` to `data-before-restore` (don't delete it), unzip the backup into the
installed folder so it makes a new `data\`, and start the planner. Sign in again.

## Claude connection (MCP)
`app/server/mcp_server.py` lets Claude Desktop or Claude Code read your plans, run the analysis and scenario matrix, and
edit the plan. Nothing extra needs installing: it speaks MCP over stdio with the planner's own Python.

- **Tools:**
  - `list_households`, `get_plan`, `run_analysis` (success, headroom, safe spending), `run_scenarios`
  - `propose_changes` (a JSON merge patch; returns every changed field and the before/after results, writes nothing)
  - `apply_changes` (saves a confirmed proposal with a backup; refused if the plan was saved since)
  - `save_scenario`
- **Data:** uses `data/` next to `app/`. Reload the planner window after Claude applies a change.

Claude Code:
```
claude mcp add financial-planner -- "C:\Users\filip\Documents\FinancialPlanner\.venv\Scripts\python.exe" "C:\Users\filip\Documents\FinancialPlanner\app\server\mcp_server.py"
```
Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{"mcpServers": {"financial-planner": {"command": "C:\\Users\\filip\\Documents\\FinancialPlanner\\.venv\\Scripts\\python.exe",
  "args": ["C:\\Users\\filip\\Documents\\FinancialPlanner\\app\\server\\mcp_server.py"]}}}
```

## Known limits
- Windows only for the window itself. On other systems pywebview would need GTK or Qt; the browser mode works anywhere.
- NAS mode needs v2 deployed on the NAS (`v2/docker-compose.yml`, port 8502). Until then the NAS serves v0.8 on
  8501. The connection check refuses anything that isn't a v2 planner, apart from a Cloudflare Access sign-in in
  front of one, so the window can't be pointed at the old app by mistake.
