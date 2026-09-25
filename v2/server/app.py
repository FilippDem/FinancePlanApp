"""FastAPI back end for Financial Planning Suite v2.

Run locally:   uvicorn server.app:app --reload --port 8502   (from v2/)
Identity:      Cloudflare Access header (Cf-Access-Authenticated-User-Email)
               when present, otherwise a simple email login (dev / LAN).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))

from finplan.engine import project, monte_carlo, historical_stats  # noqa: E402
from finplan.plan import normalize_plan  # noqa: E402
from finplan import reference as R  # noqa: E402
from server import storage as S  # noqa: E402

app = FastAPI(title="Financial Planning Suite v2")
COOKIE = 'fp_session'
ALLOW_DEV_LOGIN = os.environ.get('ALLOW_DEV_LOGIN', '1') == '1'
_passphrases: dict[tuple, str] = {}


def _secret() -> bytes:
    env = os.environ.get('SESSION_SECRET')
    if env:
        return env.encode()
    S.ensure_dirs()
    f = S.data_dir() / '.session_secret'
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip().encode()


def _sign(data: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    sig = hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def _unsign(token: str | None) -> dict:
    if not token or '.' not in token:
        return {}
    raw, sig = token.rsplit('.', 1)
    if not hmac.compare_digest(sig, hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()):
        return {}
    try:
        return json.loads(base64.urlsafe_b64decode(raw.encode()))
    except Exception:
        return {}


def _session(request: Request) -> dict:
    sess = _unsign(request.cookies.get(COOKIE))
    cf = request.headers.get('Cf-Access-Authenticated-User-Email')
    if cf:
        cf = cf.strip().lower()
        if sess.get('email') != cf:
            sess = {'email': cf}
        sess['cloudflare'] = True
    return sess


def _set(resp: Response, sess: dict):
    resp.set_cookie(COOKIE, _sign({k: v for k, v in sess.items() if k in ('email', 'hid')}),
                    httponly=True, samesite='lax', max_age=60 * 60 * 24 * 30)


def _require(request: Request, household: bool = True) -> dict:
    sess = _session(request)
    if not sess.get('email'):
        raise HTTPException(401, 'Not signed in')
    if household:
        hid = sess.get('hid')
        if not hid or not S.is_member(hid, sess['email']):
            raise HTTPException(409, 'No household selected')
    return sess


def _pp(sess: dict) -> Optional[str]:
    return _passphrases.get((sess.get('email'), sess.get('hid')))


# ── auth & households ───────────────────────────────────────────────────
class LoginIn(BaseModel):
    email: str


@app.get('/api/me')
def me(request: Request):
    sess = _session(request)
    email = sess.get('email')
    if not email:
        return {'email': None, 'dev_login': ALLOW_DEV_LOGIN}
    hid = sess.get('hid') if sess.get('hid') and S.is_member(sess['hid'], email) else None
    info = S.load_index().get(hid, {}) if hid else {}
    locked = False
    if hid and info.get('encrypted'):
        locked = not bool(_pp(sess)) and 'plan_data_encrypted' in S.household_info(hid)
    return {'email': email, 'is_admin': email in S.ADMIN_EMAILS, 'cloudflare': bool(sess.get('cloudflare')),
            'households': S.households_for(email),
            'household': ({'id': hid, 'name': info.get('name', hid), 'members': info.get('members', []),
                           'encrypted': info.get('encrypted', False), 'locked': locked,
                           'is_test': hid.startswith(S.TEST_PREFIX)} if hid else None)}


@app.post('/api/login')
def login(body: LoginIn, request: Request, response: Response):
    if request.headers.get('Cf-Access-Authenticated-User-Email'):
        raise HTTPException(400, 'Signed in via Cloudflare')
    if not ALLOW_DEV_LOGIN:
        raise HTTPException(403, 'Email login disabled')
    email = body.email.strip().lower()
    if '@' not in email:
        raise HTTPException(400, 'Enter a valid email')
    _set(response, {'email': email})
    return {'ok': True}


@app.post('/api/logout')
def logout(response: Response):
    response.delete_cookie(COOKIE)
    return {'ok': True}


class HouseholdIn(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    passphrase: Optional[str] = None


@app.post('/api/households')
def create_household(body: HouseholdIn, request: Request, response: Response):
    sess = _require(request, household=False)
    hid = S.create_household((body.name or 'My Household').strip(), sess['email'], body.passphrase or None)
    if body.passphrase:
        _passphrases[(sess['email'], hid)] = body.passphrase
    sess['hid'] = hid
    _set(response, sess)
    return {'id': hid}


@app.post('/api/households/test')
def create_test(request: Request, response: Response):
    sess = _require(request, household=False)
    if sess['email'] not in S.ADMIN_EMAILS:
        raise HTTPException(403, 'Admins only')
    hid = S.create_test_household(sess['email'])
    sess['hid'] = hid
    _set(response, sess)
    return {'id': hid}


@app.post('/api/households/join')
def join(body: HouseholdIn, request: Request, response: Response):
    sess = _require(request, household=False)
    ok, msg = S.join_household((body.id or '').strip(), sess['email'])
    if not ok:
        raise HTTPException(404, msg)
    sess['hid'] = body.id.strip()
    _set(response, sess)
    return {'id': sess['hid'], 'name': msg}


@app.post('/api/households/select')
def select(body: HouseholdIn, request: Request, response: Response):
    sess = _require(request, household=False)
    hid = (body.id or '').strip()
    if not S.is_member(hid, sess['email']):
        raise HTTPException(403, 'Not a member of that household')
    if body.passphrase:
        if not S.check_passphrase(hid, body.passphrase):
            raise HTTPException(403, 'Wrong passphrase')
        _passphrases[(sess['email'], hid)] = body.passphrase
    sess['hid'] = hid
    _set(response, sess)
    return {'id': hid}


# ── plan ────────────────────────────────────────────────────────────────
@app.get('/api/plan')
def get_plan(request: Request):
    sess = _require(request)
    try:
        raw = S.load_plan(sess['hid'], _pp(sess))
    except S.LockedError:
        raise HTTPException(423, 'Household is encrypted; unlock with passphrase')
    info = S.household_info(sess['hid'])
    return {'plan': normalize_plan(raw or {}), 'is_new': not raw,
            'last_saved': info.get('last_saved'), 'saved_by': info.get('saved_by')}


class PlanIn(BaseModel):
    plan: dict[str, Any]


@app.put('/api/plan')
def put_plan(body: PlanIn, request: Request):
    sess = _require(request)
    plan = {k: v for k, v in body.plan.items()}
    try:
        ts = S.save_plan(sess['hid'], plan, sess['email'], _pp(sess))
    except S.LockedError:
        raise HTTPException(423, 'Household is locked')
    return {'last_saved': ts}


# ── scenarios ───────────────────────────────────────────────────────────
@app.get('/api/scenarios')
def get_scenarios(request: Request):
    sess = _require(request)
    sc = S.load_scenarios(sess['hid'])
    out = {}
    for k, v in sc.items():
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                continue
        out[k] = v
    return {'scenarios': out}


class ScenarioIn(BaseModel):
    name: str
    plan: Optional[dict[str, Any]] = None
    new_name: Optional[str] = None


@app.post('/api/scenarios')
def save_scenario(body: ScenarioIn, request: Request):
    sess = _require(request)
    sc = S.load_scenarios(sess['hid'])
    sc[body.name.strip()] = body.plan or {}
    S.save_scenarios(sess['hid'], sc)
    return {'ok': True}


@app.post('/api/scenarios/rename')
def rename_scenario(body: ScenarioIn, request: Request):
    sess = _require(request)
    sc = S.load_scenarios(sess['hid'])
    if body.name in sc and body.new_name:
        sc[body.new_name.strip()] = sc.pop(body.name)
        S.save_scenarios(sess['hid'], sc)
    return {'ok': True}


@app.delete('/api/scenarios/{name}')
def delete_scenario(name: str, request: Request):
    sess = _require(request)
    sc = S.load_scenarios(sess['hid'])
    sc.pop(name, None)
    S.save_scenarios(sess['hid'], sc)
    return {'ok': True}


@app.get('/api/actuals')
def get_actuals(request: Request):
    sess = _require(request)
    return {'actuals': S.load_actuals(sess['hid'], _pp(sess))}


@app.put('/api/actuals')
def put_actuals(body: dict, request: Request):
    sess = _require(request)
    S.save_actuals(sess['hid'], body.get('actuals', {}), _pp(sess))
    return {'ok': True}


# ── engine ──────────────────────────────────────────────────────────────
class ProjectIn(BaseModel):
    plan: dict[str, Any]
    n: Optional[int] = None
    seed: Optional[int] = 42
    normalized: Optional[bool] = None


@app.post('/api/project')
def api_project(body: ProjectIn):
    r = project(body.plan)
    r.pop('plan', None)
    return r


@app.post('/api/montecarlo')
def api_mc(body: ProjectIn):
    return monte_carlo(body.plan, body.n, body.seed, body.normalized)


@app.post('/api/normalize')
def api_normalize(body: PlanIn):
    return {'plan': normalize_plan(body.plan)}


@app.get('/api/demos')
def demos():
    return {'demos': {k: normalize_plan(v) for k, v in R.demo_plans().items()}}


@app.get('/api/reference')
def reference():
    r = R.ref()
    return {
        'locations': R.all_locations(),
        'location_display_names': r['LOCATION_DISPLAY_NAMES'],
        'location_hierarchy': r['LOCATION_HIERARCHY'],
        'strategies': R.STATISTICAL_STRATEGIES,
        'adult_categories': r['ADULT_EXPENSE_CATEGORIES'],
        'family_categories': r['FAMILY_SHARED_CATEGORIES'],
        'children_categories': r['CHILDREN_EXPENSE_CATEGORIES_FLAT'],
        'us_state_tax': r['US_STATE_TAX_INFO'], 'country_tax': r['COUNTRY_TAX_INFO'],
        'data_sources': r['EXPENSE_DATA_SOURCES'],
        'template_base_year': 2024,
        'historical': historical_stats(),
    }


class TemplateIn(BaseModel):
    location: str
    strategy: str
    current_year: int = 2026
    inflation: float = 0.03


@app.post('/api/templates/adult')
def tmpl_adult(body: TemplateIn):
    scale = (1 + body.inflation) ** max(0, body.current_year - 2024)
    return {k: round(v * scale) for k, v in R.adult_template(body.location, body.strategy).items()}


@app.post('/api/templates/family')
def tmpl_family(body: TemplateIn):
    scale = (1 + body.inflation) ** max(0, body.current_year - 2024)
    t = R.family_template(body.location, body.strategy)
    return {k: round(v * scale) for k, v in (t or {}).items()}


@app.post('/api/templates/children')
def tmpl_children(body: TemplateIn):
    scale = (1 + body.inflation) ** max(0, body.current_year - 2024)
    t = R.children_template(body.location, body.strategy)
    return {k: [round(x * scale) for x in v] for k, v in t.items()}


@app.get('/api/health')
def health():
    return {'ok': True}


# ── static SPA ──────────────────────────────────────────────────────────
DIST = ROOT / 'web' / 'dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')

    @app.get('/{full_path:path}')
    def spa(full_path: str):
        f = DIST / full_path
        if full_path and f.is_file():
            return FileResponse(f)
        return FileResponse(DIST / 'index.html')
