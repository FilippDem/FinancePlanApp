"""Financial Planner as a desktop window (pywebview + the Edge WebView2 engine built into Windows).

Two ways to connect, saved in settings.json next to this folder:
  local  "This computer": runs the planner server inside this process; closing the window stops it.
  nas    "Our NAS": shows a planner that is already running elsewhere (NAS on the LAN or the Cloudflare
         address), so the whole household edits one plan. Nothing runs locally.

Started without a console by the desktop shortcut (pythonw). Everything is logged to logs/desktop.log;
the local server's own log is logs/server.log.

    pythonw launcher/desktop.py            normal start
    pythonw launcher/desktop.py --choose   open the connection settings first
    python  launcher/desktop.py --smoke    open, check the app renders, close (used for testing)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'app'
LOGS = ROOT / 'logs'
DATA = ROOT / 'data'
SETTINGS = ROOT / 'settings.json'
WEBDATA = ROOT / 'webview-data'          # cookies / sign-in for the window (kept between runs)
ICON = ROOT / 'launcher' / 'planner.ico'
DESKTOP_PID = ROOT / '.desktop.pid'
SERVER_PID = ROOT / '.server.pid'
TITLE = 'Financial Planner'
DEFAULT_PORT = int(os.environ.get('FP_PORT', '8502'))
ON_WINDOWS = os.name == 'nt'
NO_WINDOW = 0x08000000 if ON_WINDOWS else 0
SMOKE_FLAG = ROOT / '.smoke'             # testing: a file named .smoke makes the next start a self-check run
SMOKE = '--smoke' in sys.argv or SMOKE_FLAG.exists()
CHOOSE_FIRST = '--choose' in sys.argv
if SMOKE_FLAG.exists():
    try:
        SMOKE_FLAG.unlink()
    except OSError:
        pass

LOGS.mkdir(parents=True, exist_ok=True)
_logf = LOGS / 'desktop.log'
if _logf.exists() and _logf.stat().st_size > 1_000_000:
    _logf.replace(LOGS / 'desktop.old.log')
logging.basicConfig(filename=str(_logf), level=logging.INFO, encoding='utf-8',
                    format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('desktop')
if sys.stdout is None or sys.stderr is None or not SMOKE:   # pythonw has no console: keep stray prints in the log
    _stray = open(_logf, 'a', buffering=1, encoding='utf-8')
    sys.stdout = sys.stderr = _stray


# ── settings ────────────────────────────────────────────────────────────────────────────────
def load_settings() -> dict:
    s = {'mode': 'local', 'nas_url': '', 'width': 1440, 'height': 920, 'maximized': False}
    try:
        s.update(json.loads(SETTINGS.read_text(encoding='utf-8')))
    except FileNotFoundError:
        pass
    except Exception:
        log.exception('settings.json unreadable; using defaults')
    if s.get('mode') not in ('local', 'nas'):
        s['mode'] = 'local'
    return s


def save_settings(s: dict) -> None:
    tmp = SETTINGS.with_suffix('.tmp')
    tmp.write_text(json.dumps(s, indent=2), encoding='utf-8')
    os.replace(tmp, SETTINGS)


def normalize_url(u: str) -> str:
    u = (u or '').strip()
    if not u:
        return ''
    if '://' not in u:
        u = 'http://' + u
    return u.rstrip('/')


# ── network helpers (no proxies: the planner is on this PC or the LAN) ─────────────────────────
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def port_open(port: int, host: str = '127.0.0.1') -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.6):
            return True
    except OSError:
        return False


def planner_healthy(base: str, timeout: float = 2.0) -> bool:
    try:
        with _opener.open(base + '/api/health', timeout=timeout) as r:
            return r.status == 200 and b'"ok"' in r.read(200)
    except Exception:
        return False


def reachable(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """Is there a v2 planner at this address? A Cloudflare Access sign-in in front of it also counts
    (the window shows the sign-in); an old v0.8 app or some other site does not."""
    try:
        with _opener.open(url + '/api/health', timeout=timeout) as r:
            final, body = r.geturl(), r.read(400)
            if r.status == 200 and b'"ok"' in body:
                return True, 'Financial Planner found.'
            if 'cloudflareaccess.com' in final or 'cdn-cgi/access' in final:
                return True, 'Found it behind Cloudflare; the window will ask you to sign in.'
            return False, ("That address answers, but it isn't Financial Planner v2. If the NAS still runs the old app "
                           "(port 8501), v2 needs to be set up there first (it uses port 8502).")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and ('cloudflare' in str(e.headers.get('Server', '')).lower() or 'cf-ray' in {k.lower() for k in e.headers.keys()}):
            return True, 'Found it behind Cloudflare; the window will ask you to sign in.'
        return False, f"That address answers with an error (HTTP {e.code}); it doesn't look like Financial Planner v2."
    except Exception as e:
        reason = getattr(e, 'reason', e)
        return False, f"Couldn't reach {url}: {reason}"


def listening_pid(port: int) -> int | None:
    if not ON_WINDOWS:
        return None
    try:
        out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True,
                             creationflags=NO_WINDOW, timeout=10).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[1].endswith(f':{port}') and parts[3].upper() == 'LISTENING':
                return int(parts[4])
    except Exception:
        log.exception('netstat failed')
    return None


def process_name(pid: int) -> str:
    try:
        out = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'], capture_output=True,
                             text=True, creationflags=NO_WINDOW, timeout=10).stdout.strip()
        return out.split(',')[0].strip('"').lower() if out.startswith('"') else ''
    except Exception:
        return ''


def kill(pid: int) -> None:
    subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True, creationflags=NO_WINDOW, timeout=15)


# ── packages: install anything new in the requirement files (after an update) ──────────────────
def _req_files() -> list[tuple[Path, Path]]:
    venv = Path(sys.prefix)
    return [(APP / 'requirements.txt', venv / '.requirements.sha256'),
            (ROOT / 'launcher' / 'requirements-desktop.txt', venv / '.desktop-requirements.sha256')]


def packages_current() -> bool:
    for req, stamp in _req_files():
        if req.exists() and (not stamp.exists() or stamp.read_text().strip().upper() != _sha(req)):
            return False
    return True


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def install_packages() -> None:
    py = Path(sys.prefix) / ('Scripts/python.exe' if ON_WINDOWS else 'bin/python')
    for req, stamp in _req_files():
        if req.exists() and (not stamp.exists() or stamp.read_text().strip().upper() != _sha(req)):
            log.info('installing %s', req.name)
            cmd = [str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '-q', '-r', str(req)]
            wheels = ROOT / 'launcher' / 'wheels'
            if wheels.is_dir():
                cmd += ['--find-links', str(wheels)]
            r = subprocess.run(cmd, capture_output=True, text=True, creationflags=NO_WINDOW)
            if r.returncode != 0:
                raise RuntimeError(f'Installing packages failed:\n{(r.stderr or r.stdout)[-1500:]}')
            stamp.write_text(_sha(req))


# ── the local planner server, inside this process ─────────────────────────────────────────────
class LocalServer:
    def __init__(self):
        self.server = None
        self.thread = None
        self.port = None
        self.owned = False

    @property
    def url(self) -> str:
        return f'http://127.0.0.1:{self.port}'

    def ensure(self, status) -> str:
        if self.thread and self.thread.is_alive() and planner_healthy(self.url):
            return self.url
        port = DEFAULT_PORT
        if port_open(port):
            if planner_healthy(f'http://127.0.0.1:{port}'):
                # a planner started by the browser launcher: replace it so closing this window stops everything
                pid = listening_pid(port)
                name = process_name(pid) if pid else ''
                if pid and pid != os.getpid() and name.startswith('python'):
                    status('Taking over the planner that was running in the background…')
                    log.info('stopping background planner pid %s (%s)', pid, name)
                    kill(pid)
                    for _ in range(40):
                        if not port_open(port):
                            break
                        time.sleep(0.25)
                if port_open(port):
                    log.info('reusing the planner already on port %s', port)
                    self.port, self.owned = port, False
                    return self.url
            else:
                for p in range(port + 1, port + 30):     # something else owns 8502: pick a free port
                    if not port_open(p):
                        port = p
                        break
        status('Starting the planner…')
        self.port = port
        self._start(port)
        deadline = time.time() + 90
        while time.time() < deadline:
            if planner_healthy(self.url, 1.0):
                log.info('local server ready on %s', self.url)
                return self.url
            if not self.thread.is_alive():
                break
            time.sleep(0.3)
        raise RuntimeError('The planner server did not start. Details are in logs\\server.log.')

    def _start(self, port: int) -> None:
        os.environ.setdefault('DATA_DIR', str(DATA))
        os.environ.setdefault('ALLOW_DEV_LOGIN', '1')
        DATA.mkdir(parents=True, exist_ok=True)
        if str(APP) not in sys.path:
            sys.path.insert(0, str(APP))
        os.chdir(APP)
        import uvicorn
        from uvicorn.config import LOGGING_CONFIG
        lc = json.loads(json.dumps(LOGGING_CONFIG))
        for h in lc['handlers'].values():
            h.pop('stream', None)
            h['class'] = 'logging.FileHandler'
            h['filename'] = str(LOGS / 'server.log')
            h['encoding'] = 'utf-8'
        for f in lc['formatters'].values():
            f['use_colors'] = False
        config = uvicorn.Config('server.app:app', host='127.0.0.1', port=port, log_config=lc, log_level='info')
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self._run, name='planner-server', daemon=True)
        self.thread.start()
        self.owned = True
        SERVER_PID.write_text(str(os.getpid()))

    def _run(self):
        try:
            self.server.run()
        except Exception:
            log.exception('server crashed')

    def stop(self) -> None:
        if self.owned and self.server is not None:
            log.info('stopping local server')
            self.server.should_exit = True
            if self.thread:
                self.thread.join(8)
            try:
                if SERVER_PID.exists() and SERVER_PID.read_text().strip() == str(os.getpid()):
                    SERVER_PID.unlink()
            except Exception:
                pass
        self.server, self.thread, self.owned = None, None, False


# ── the window's own pages (splash, problem, connection), served on 127.0.0.1 behind a random token ──
STYLE = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#111827;--ink2:#4b5563;--muted:#6b7280;--line:#e5e7eb;--accent:#2563eb;--bad:#dc2626;--good:#16a34a}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a21;--ink:#f3f4f6;--ink2:#cbd5e1;--muted:#94a3b8;--line:#2a2f3a;--accent:#3b82f6;--bad:#f87171;--good:#4ade80}}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:14px/1.45 "Segoe UI Variable","Segoe UI",system-ui,sans-serif}
.wrap{min-height:100%;display:flex;align-items:center;justify-content:center;padding:24px}
.box{text-align:center;max-width:540px;width:100%}.logo{width:64px;height:64px;margin:0 auto 18px;display:block}
h1{font-size:22px;font-weight:600;margin:0 0 6px}p{margin:6px 0;color:var(--ink2)}
.status{color:var(--muted);min-height:20px;margin-top:14px}
.spin{width:22px;height:22px;border:2.5px solid var(--line);border-top-color:var(--accent);border-radius:50%;margin:18px auto 0;animation:s .9s linear infinite}
@keyframes s{to{transform:rotate(360deg)}}
button{font:inherit;height:36px;padding:0 14px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button:disabled{opacity:.6;cursor:default}
.row{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:18px}
pre{white-space:pre-wrap;text-align:left;font:12px/1.4 Consolas,monospace;color:var(--muted);background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;max-height:160px;overflow:auto}
.card{text-align:left;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 24px}
label.opt{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px;cursor:pointer}
label.opt.on{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
label.opt input[type=radio]{margin-top:4px;accent-color:var(--accent)}.t{font-weight:600}.d{color:var(--muted);font-size:12.5px}
input[type=text]{width:100%;height:36px;border-radius:9px;border:1px solid var(--line);background:var(--bg);color:var(--ink);padding:0 10px;font:inherit;margin-top:8px}
.msg{font-size:12.5px;min-height:18px;margin-top:6px}.ok{color:var(--good)}.no{color:var(--bad)}
.foot{display:flex;gap:8px;justify-content:space-between;align-items:center;margin-top:18px;flex-wrap:wrap}
a{color:var(--accent);cursor:pointer;font-size:12.5px}
"""
LOGO = ('<svg class="logo" viewBox="0 0 64 64"><rect x="2" y="2" width="60" height="60" rx="14" fill="#2563eb"/>'
        '<polyline points="13,46 24,35 32,40 50,21" fill="none" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>'
        '<polygon points="53,15 53,28 42,18" fill="#fff"/></svg>')
HEAD = f'<!doctype html><html><head><meta charset="utf-8"><title>{TITLE}</title><style>{STYLE}</style></head><body>'
# every page talks to the page server with fetch(); the token is part of the page's own path
JS_POST = "const post=(p,b)=>fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json());"


def esc(t: str) -> str:
    return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def page_splash() -> str:
    return HEAD + f"""<div class="wrap"><div class="box">{LOGO}<h1>Financial Planner</h1><div class="spin"></div>
<div class="status" id="st">Opening…</div></div></div>
<script>{JS_POST}
async function poll(){{try{{const s=await fetch('status').then(r=>r.json());document.getElementById('st').textContent=s.text||'';
}}catch(e){{}}setTimeout(poll,300)}}poll();</script></body></html>"""


def page_problem(msg: str, detail: str, mode: str) -> str:
    local_btn = '' if mode == 'local' else '<button onclick="go(\'use-local\')">Use this computer instead</button>'
    return HEAD + f"""<div class="wrap"><div class="box">{LOGO}<h1>Can't open the planner</h1><p>{esc(msg)}</p>
{f'<pre>{esc(detail)}</pre>' if detail else ''}
<div class="row"><button class="primary" onclick="go('reconnect')">Try again</button>{local_btn}
<button onclick="location.href='connection'">Connection settings</button>
<button onclick="go('open-logs')">Open the log folder</button></div></div></div>
<script>{JS_POST} function go(a){{post(a)}}</script></body></html>"""


def page_connection(s: dict, back: str) -> str:
    local_on, nas_on = ('on', '') if s['mode'] == 'local' else ('', 'on')
    return HEAD + f"""<div class="wrap"><div class="box" style="max-width:600px">{LOGO}
<div class="card"><h1 style="font-size:19px">Connection</h1><p style="margin:0;color:var(--muted)">Where should this window get your plan from?</p>
<label class="opt {local_on}"><input type="radio" name="m" value="local" {'checked' if local_on else ''}><div><div class="t">This computer</div>
<div class="d">The planner runs inside this window. Plans are saved in Documents\\FinancialPlanner\\data, and closing the window stops it.</div></div></label>
<label class="opt {nas_on}"><input type="radio" name="m" value="nas" {'checked' if nas_on else ''}><div style="flex:1"><div class="t">Our NAS (shared household plan)</div>
<div class="d">Use the planner running on the NAS, so the whole household edits one plan. Type the address you'd use in a browser,
for example http://tm223_nas:8502 at home, or your Cloudflare address from anywhere.</div>
<input type="text" id="url" value="{esc(s.get('nas_url', ''))}" placeholder="http://tm223_nas:8502" spellcheck="false">
<div class="msg" id="msg"></div></div></label>
<div class="foot"><a onclick="post('open-browser')">Open the planner in my browser</a>
<div style="display:flex;gap:8px"><button onclick="test()">Test</button>{f'<button onclick="location.href={json.dumps(back)}">Cancel</button>' if back else ''}
<button class="primary" id="save" onclick="save()">Save</button></div></div></div></div></div>
<script>{JS_POST}
const $=id=>document.getElementById(id);
const mode=()=>document.querySelector('input[name=m]:checked').value;
function mark(){{document.querySelectorAll('label.opt').forEach(l=>l.classList.toggle('on',l.querySelector('input').checked))}}
document.querySelectorAll('input[name=m]').forEach(i=>i.addEventListener('change',mark));
$('url').addEventListener('focus',()=>{{document.querySelector('input[value=nas]').checked=true;mark()}});
function show(r){{$('msg').textContent=r.message;$('msg').className='msg '+(r.ok?'ok':'no')}}
async function test(){{$('msg').textContent='Checking…';$('msg').className='msg';show(await post('test',{{url:$('url').value}}))}}
async function save(){{$('save').disabled=true;if(mode()==='nas'){{$('msg').textContent='Checking…';$('msg').className='msg'}}
const r=await post('save',{{mode:mode(),url:$('url').value}});$('save').disabled=false;if(!r.ok)show(r)}}
</script></body></html>"""


class PageServer:
    """Serves the window's own pages and their few actions. Only this computer can reach it, and every
    path starts with a random token, so other programs and web pages can't drive it."""

    def __init__(self, app: 'DesktopApp'):
        import http.server
        import secrets
        self.app = app
        self.token = secrets.token_urlsafe(16)
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _route(self):
                parts = self.path.split('?', 1)[0].strip('/').split('/')
                if len(parts) != 2 or parts[0] != outer.token:
                    self.send_error(404)
                    return None
                return parts[1]

            def _send(self, body: str, ctype='text/html; charset=utf-8'):
                b = body.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                r = self._route()
                if r is None:
                    return
                a = outer.app
                if r == 'splash':
                    self._send(page_splash())
                elif r == 'status':
                    self._send(json.dumps({'text': a.status_text}), 'application/json')
                elif r == 'problem':
                    self._send(page_problem(a.problem[0], a.problem[1], a.settings['mode']))
                elif r == 'connection':
                    self._send(page_connection(a.settings, a.current_url and a.current_url + '/'))
                else:
                    self.send_error(404)

            def do_POST(self):
                r = self._route()
                if r is None:
                    return
                try:
                    n = int(self.headers.get('Content-Length') or 0)
                    body = json.loads(self.rfile.read(n) or b'{}') if n else {}
                except Exception:
                    body = {}
                try:
                    out = outer.app.action(r, body)
                except Exception as e:
                    log.exception('action %s failed', r)
                    out = {'ok': False, 'message': str(e)}
                self._send(json.dumps(out or {'ok': True}), 'application/json')

        self.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.httpd.daemon_threads = True
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}/{self.token}/'
        threading.Thread(target=self.httpd.serve_forever, name='page-server', daemon=True).start()

    def url(self, page: str) -> str:
        return self.base + page

    def stop(self):
        try:
            self.httpd.shutdown()
        except Exception:
            pass


# ── the app ────────────────────────────────────────────────────────────────────────────────────
class Api:
    """window.pywebview.api inside the planner (the sidebar's Connection item uses it).
    Attributes start with _ so pywebview doesn't expose them."""

    def __init__(self, app: 'DesktopApp'):
        self._app = app

    def get_state(self):
        a = self._app
        return {'mode': a.settings['mode'], 'nas_url': a.settings.get('nas_url', ''), 'url': a.current_url, 'desktop': True}

    def choose_connection(self):
        self._app.show_connection()

    def open_in_browser(self):
        self._app.action('open-browser', {})


class DesktopApp:
    def __init__(self):
        import webview
        self.webview = webview
        self.settings = load_settings()
        self.server = LocalServer()
        self.pages = PageServer(self)
        self.api = Api(self)
        self.window = None
        self.current_url = ''           # the planner's address once it's showing
        self.status_text = 'Opening…'
        self.problem = ('', '')
        self._boot_lock = threading.Lock()
        self._maximized = bool(self.settings.get('maximized'))

    # window ------------------------------------------------------------------------------------
    def size(self) -> tuple[int, int]:
        w, h = int(self.settings.get('width') or 1440), int(self.settings.get('height') or 920)
        try:
            sc = self.webview.screens[0]
            w, h = min(w, int(sc.width * 0.95)), min(h, int(sc.height * 0.9))
        except Exception:
            pass
        return max(w, 1000), max(h, 680)

    def run(self) -> None:
        wv = self.webview
        wv.settings['ALLOW_DOWNLOADS'] = True                 # reports, CSV and JSON exports
        wv.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True  # source links open in the normal browser
        w, h = self.size()
        first = self.pages.url('connection') if CHOOSE_FIRST else self.pages.url('splash')
        self.window = wv.create_window(TITLE, url=first, js_api=self.api, width=w, height=h, min_size=(1000, 660),
                                       maximized=self._maximized, background_color='#F6F7F9', text_select=True,
                                       zoomable=True)
        self.window.events.closing += self._on_closing
        self.window.events.maximized += lambda *a: setattr(self, '_maximized', True)
        self.window.events.restored += lambda *a: setattr(self, '_maximized', False)
        WEBDATA.mkdir(exist_ok=True)
        log.info('starting window (mode=%s)', self.settings['mode'])
        wv.start(None if CHOOSE_FIRST else self.boot, private_mode=False, storage_path=str(WEBDATA),
                 icon=str(ICON) if ICON.exists() else None)
        log.info('window closed')
        self.server.stop()
        self.pages.stop()

    def _on_closing(self, *a):
        try:
            if not self._maximized and self.window.width and self.window.height:
                self.settings['width'], self.settings['height'] = int(self.window.width), int(self.window.height)
            self.settings['maximized'] = self._maximized
            save_settings(self.settings)
        except Exception:
            log.exception('saving the window size failed')

    def navigate(self, url: str) -> None:
        try:
            self.window.load_url(url)
        except Exception:
            log.exception('navigating to %s failed', url)

    def status(self, text: str) -> None:
        log.info('status: %s', text)
        self.status_text = text            # the splash page polls this

    # connecting --------------------------------------------------------------------------------
    def boot(self) -> None:
        if not self._boot_lock.acquire(blocking=False):
            return
        try:
            self.current_url = ''
            if not packages_current():
                self.status('Updating the app’s packages (one time)…')
                install_packages()
            if self.settings['mode'] == 'nas':
                url = normalize_url(self.settings.get('nas_url', ''))
                if not url:
                    raise UserError('No NAS address is set yet.', '')
                self.status('Connecting to the NAS…')
                ok, msg = reachable(url, 8)
                if not ok:
                    raise UserError('The NAS planner is not answering. Is the NAS on, and is the address right?', msg)
                self.server.stop()                # nothing to run locally in NAS mode
            else:
                url = self.server.ensure(self.status)
            self.current_url = url
            self.status('Loading your plan…')
            log.info('loading %s', url)
            self.navigate(url + '/')
            if SMOKE:
                threading.Thread(target=self._smoke, daemon=True).start()
        except UserError as e:
            self._show_problem(str(e), e.detail)
        except Exception as e:
            log.exception('boot failed')
            self._show_problem('Something went wrong while starting.', f'{type(e).__name__}: {e}')
        finally:
            self._boot_lock.release()

    def _show_problem(self, msg: str, detail: str) -> None:
        self.current_url = ''
        self.problem = (msg, detail)
        log.error('problem: %s | %s', msg, detail)
        self.navigate(self.pages.url('problem'))
        if SMOKE:
            log.error('SMOKE FAIL: %s', msg)
            time.sleep(2)
            self.window.destroy()

    def reconnect(self) -> None:
        self.current_url, self.status_text = '', 'Opening…'
        self.navigate(self.pages.url('splash'))
        threading.Thread(target=self.boot, daemon=True).start()

    def show_connection(self) -> None:
        self.navigate(self.pages.url('connection'))

    # actions from our pages ----------------------------------------------------------------------
    def action(self, name: str, body: dict) -> dict:
        if name == 'reconnect':
            self.reconnect()
        elif name == 'use-local':
            self.settings['mode'] = 'local'
            save_settings(self.settings)
            self.reconnect()
        elif name == 'open-logs':
            if ON_WINDOWS:
                os.startfile(str(LOGS))
        elif name == 'open-browser':
            url = self.current_url or (self.settings.get('nas_url') if self.settings['mode'] == 'nas' else '')
            if url:
                webbrowser.open(url.replace('://127.0.0.1', '://localhost'))
            else:
                return {'ok': False, 'message': 'The planner is not running yet.'}
        elif name == 'test':
            u = normalize_url(body.get('url', ''))
            if not u:
                return {'ok': False, 'message': 'Type the NAS address first.'}
            ok, msg = reachable(u)
            return {'ok': ok, 'message': msg}
        elif name == 'save':
            mode = 'nas' if body.get('mode') == 'nas' else 'local'
            u = normalize_url(body.get('url', ''))
            if mode == 'nas':
                if not u:
                    return {'ok': False, 'message': 'Type the NAS address first.'}
                ok, msg = reachable(u)
                if not ok:
                    return {'ok': False, 'message': msg}
            self.settings.update({'mode': mode, 'nas_url': u or self.settings.get('nas_url', '')})
            save_settings(self.settings)
            log.info('connection saved: %s %s', mode, self.settings.get('nas_url'))
            self.reconnect()
        else:
            return {'ok': False, 'message': f'unknown action {name}'}
        return {'ok': True}

    # test mode ----------------------------------------------------------------------------------
    def _smoke(self) -> None:
        ok = False
        for _ in range(60):
            time.sleep(0.5)
            try:
                r = self.window.evaluate_js('JSON.stringify({title: document.title, href: location.href, '
                                            'text: (document.getElementById("root")||document.body).innerText.length, '
                                            'api: !!(window.pywebview && window.pywebview.api)})')
                info = json.loads(r) if isinstance(r, str) else r
                if info and info.get('text', 0) > 20 and str(info.get('href', '')).startswith(self.current_url):
                    log.info('SMOKE OK %s', info)
                    ok = True
                    break
            except Exception as e:
                log.info('smoke poll: %s', e)
        if not ok:
            log.error('SMOKE FAIL: the planner page did not render')
        time.sleep(1)
        self.window.destroy()


class UserError(Exception):
    def __init__(self, msg: str, detail: str = ''):
        super().__init__(msg)
        self.detail = detail


# ── single instance ───────────────────────────────────────────────────────────────────────────
def already_running() -> bool:
    """True if another window is open (and bring it to the front)."""
    if not ON_WINDOWS:
        return False
    import ctypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    u32 = ctypes.WinDLL('user32', use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    u32.FindWindowW.restype = ctypes.c_void_p
    u32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    u32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
    global _mutex
    _mutex = k32.CreateMutexW(None, False, 'Local\\GonzikFinancialPlannerDesktop')
    if ctypes.get_last_error() != 183:     # ERROR_ALREADY_EXISTS
        return False
    for _ in range(10):                    # the other copy may still be opening its window
        hwnd = u32.FindWindowW(None, TITLE)
        if hwnd:
            u32.ShowWindow(hwnd, 9)        # SW_RESTORE
            u32.SetForegroundWindow(hwnd)
            return True
        time.sleep(0.5)
    log.warning('another copy holds the lock but has no window; starting anyway')
    return False


def message_box(text: str) -> None:
    if ON_WINDOWS:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, TITLE, 0x40)
    else:
        print(text)


def main() -> None:
    log.info('---- start %s (python %s) ----', ' '.join(sys.argv[1:]) or '', sys.version.split()[0])
    if not SMOKE and already_running():
        log.info('already open; brought it to the front')
        return
    DESKTOP_PID.write_text(str(os.getpid()))
    try:
        try:
            import webview  # noqa: F401
        except ImportError:
            log.exception('pywebview missing')
            message_box('Financial Planner needs to finish setting up.\n\nDouble-click "Start Financial Planner" '
                        'in Documents\\FinancialPlanner once (it installs what is missing).')
            return
        DesktopApp().run()
    except Exception:
        log.exception('desktop app crashed')
        message_box('Financial Planner could not open its window.\n\nDetails are in logs\\desktop.log. '
                    '"Open in Browser" in Documents\\FinancialPlanner still works.')
    finally:
        try:
            if DESKTOP_PID.exists() and DESKTOP_PID.read_text().strip() == str(os.getpid()):
                DESKTOP_PID.unlink()
        except Exception:
            pass
        log.info('---- exit ----')
        logging.shutdown()


if __name__ == '__main__':
    main()
    # leave nothing behind: a lingering invisible process would hold the single-instance lock
    os._exit(0)
