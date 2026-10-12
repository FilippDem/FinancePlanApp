FINANCIAL PLANNER (v2)
======================

TO OPEN IT: use the "Financial Planner" shortcut on your desktop or in the Start menu.
It opens in its own window. Closing the window shuts the planner down; nothing keeps
running in the background.

FIRST TIME (or after an update): double-click "Start Financial Planner" in this folder.
It needs internet and takes a few minutes the first time:
  - installs Python 3.12 if you don't have it (through winget),
  - sets up the app's packages in a private folder (.venv),
  - copies your existing plans from C:\Users\<you>\financial-planner\data
    if it finds them (a copy; the originals are not touched),
  - adds the "Financial Planner" shortcuts, then opens the window.
If Windows asks whether to run the file, choose Run (or "More info" > "Run anyway").

SIGNING IN: type your email. You stay signed in.

THIS COMPUTER OR THE NAS: the item just above "Dark mode" at the bottom of the sidebar
shows where the window gets your plan from. Click it to switch:
  - This computer: plans are stored in the "data" folder here.
  - Our NAS: type the NAS planner's address (for example http://tm223_nas:8502 at home,
    or your Cloudflare address). Everyone using that address shares one plan.
    (v2 has to be running on the NAS first; for now the NAS still runs the old app.)
If the window can't reach the planner, it shows what went wrong with buttons to try
again, switch back to this computer, or change the address.

IN A BROWSER INSTEAD: double-click "Open in Browser". It runs in the background until you
double-click "Stop Financial Planner" (or restart the PC).

YOUR DATA lives in the "data" folder here. Every save makes a backup in data\backups.
To move to a newer build later, replace only the "app" and "launcher" folders;
keep "data", "settings.json" and "webview-data" (your sign-in).

WHAT'S IN THIS BUILD
  GitHub branch v2-react (e3fb591) plus 5 commits that aren't pushed yet:
  scenario matrix; tax planning (Roth conversions, capital gains, IRMAA, ACA), goals,
  safe spending, guardrails, historical backtest, pensions, loans, 529 plans; the pages
  for those; the drag-and-drop plan editor on the Life timeline; and the desktop window
  (launcher in v2/desktop, "This computer / Shared plan (NAS)" item in the sidebar).
  Tests: 67 engine + 24 API passing.

EXTRAS
  extras\"Push the updates to GitHub" adds those commits to your checkout in
  C:\Users\<you>\financial-planner and pushes v2-react, so GitHub is up to date.

TROUBLESHOOTING
  logs\desktop.log (the window) and logs\server.log (the planner) say what happened.
  "Start Financial Planner" repairs the setup if something is missing.
  If the window ever won't open, "Open in Browser" still works.
