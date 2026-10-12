"""Build the Windows "Financial Planner" folder (desktop window + browser fallback) from this repo.

    python v2/desktop/make_package.py                 # -> v2/desktop/package/FinancialPlanner
    python v2/desktop/make_package.py --zip           # also FinancialPlanner-v2.zip
    python v2/desktop/make_package.py --build-web     # run `npm run build` in v2/web first

Layout of the result (what launcher/start.ps1 and launcher/desktop.py expect):
    FinancialPlanner/
      Start Financial Planner.bat   Open in Browser.bat   Stop Financial Planner.bat   Back Up Plans Now.bat   README.txt
      app/        engine/ server/ requirements.txt web/dist/      (the v2 app, tests left out)
      launcher/   desktop.py start.ps1 stop.ps1 backup.ps1 run_server.py requirements-desktop.txt planner.ico wheels/
To update an installed copy, replace its app/ and launcher/ folders (and the .bat files); keep data/,
settings.json, webview-data/ (sign-in), .venv/ and logs/. The next start installs any new packages.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # v2/desktop
V2 = HERE.parent
SKIP = shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache', 'tests')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE / 'package'))
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--build-web', action='store_true')
    a = ap.parse_args()

    dist = V2 / 'web' / 'dist'
    if a.build_web or not dist.exists():
        npm = 'npm.cmd' if sys.platform == 'win32' else 'npm'
        subprocess.run([npm, 'run', 'build'], cwd=V2 / 'web', check=True)

    out = Path(a.out)
    pkg = out / 'FinancialPlanner'
    if pkg.exists():
        shutil.rmtree(pkg)
    (pkg / 'app' / 'web').mkdir(parents=True)
    shutil.copytree(V2 / 'engine', pkg / 'app' / 'engine', ignore=SKIP)
    shutil.copytree(V2 / 'server', pkg / 'app' / 'server', ignore=SKIP)
    shutil.copy2(V2 / 'requirements.txt', pkg / 'app' / 'requirements.txt')
    shutil.copytree(dist, pkg / 'app' / 'web' / 'dist')
    shutil.copytree(HERE / 'launcher', pkg / 'launcher', ignore=SKIP)
    for f in (HERE / 'root').iterdir():
        dst = pkg / f.name
        if f.suffix.lower() in ('.bat', '.txt'):   # Windows line endings for the files people open
            dst.write_bytes(f.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        else:
            shutil.copy2(f, dst)
    print(f'built {pkg}')
    if a.zip:
        z = shutil.make_archive(str(out / 'FinancialPlanner-v2'), 'zip', root_dir=out, base_dir='FinancialPlanner')
        print(f'zipped {z}')


if __name__ == '__main__':
    main()
