"""Household storage — byte-compatible with FinancialPlanner_v0_8.py.

Same directory layout (DATA_DIR/households/<id>.json, households_index.json,
backups/), same keys, same encryption scheme. Follows the Data Preservation
Policy in CLAUDE.md: load-then-merge, timestamped backup before every write
(test households exempt), never drop unknown keys, atomic writes.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', 'filippdem@gmail.com').split(',') if e.strip()}
TEST_PREFIX = "_test_"


def data_dir() -> Path:
    return Path(os.environ.get('DATA_DIR', './data'))


def hh_dir() -> Path:
    return data_dir() / 'households'


def index_path() -> Path:
    return data_dir() / 'households_index.json'


def ensure_dirs():
    hh_dir().mkdir(parents=True, exist_ok=True)
    if not index_path().exists():
        _atomic_write(index_path(), {})


def _atomic_write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.tmp_', suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read(path: Path) -> dict:
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _backup(path: Path, stem: str, keep: int = 10) -> None:
    if not path.exists():
        return
    bdir = data_dir() / 'backups'
    bdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        shutil.copy2(path, bdir / f"{stem}_{ts}.json")
        olds = sorted(bdir.glob(f"{stem}_2*.json"))
        for o in olds[:-keep]:
            o.unlink()
        # v2: one snapshot per day (kept 120 days) so version history spans months,
        # not just the last 10 autosaves
        if stem != 'households_index':
            ddir = bdir / 'daily'
            ddir.mkdir(exist_ok=True)
            daily = ddir / f"{stem}_{datetime.now():%Y%m%d}.json"
            if not daily.exists():
                shutil.copy2(path, daily)
                for o in sorted(ddir.glob(f"{stem}_2*.json"))[:-120]:
                    o.unlink()
    except Exception:
        pass


# ── encryption (identical to v0.8) ─────────────────────────────────────────
def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', passphrase.encode('utf-8'), salt, 100000)


def encrypt(plaintext: str, passphrase: str) -> dict:
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(16)
    key = _derive_key(passphrase, salt)
    pb = plaintext.encode('utf-8')
    ct = bytearray()
    for i in range(0, len(pb), 32):
        bk = hmac.new(key, iv + i.to_bytes(8, 'big'), hashlib.sha256).digest()
        chunk = pb[i:i + 32]
        ct.extend(b ^ k for b, k in zip(chunk, bk[:len(chunk)]))
    tag = hmac.new(key, bytes(ct), hashlib.sha256).digest()[:16]
    b64 = lambda b: base64.b64encode(b).decode()
    return {'salt': b64(salt), 'iv': b64(iv), 'ciphertext': b64(bytes(ct)), 'tag': b64(tag)}


def decrypt(enc: dict, passphrase: str) -> Optional[str]:
    try:
        d = lambda k: base64.b64decode(enc[k])
        salt, iv, ct, tag = d('salt'), d('iv'), d('ciphertext'), d('tag')
        key = _derive_key(passphrase, salt)
        if not hmac.compare_digest(tag, hmac.new(key, ct, hashlib.sha256).digest()[:16]):
            return None
        pt = bytearray()
        for i in range(0, len(ct), 32):
            bk = hmac.new(key, iv + i.to_bytes(8, 'big'), hashlib.sha256).digest()
            chunk = ct[i:i + 32]
            pt.extend(b ^ k for b, k in zip(chunk, bk[:len(chunk)]))
        return pt.decode('utf-8')
    except Exception:
        return None


# ── index ───────────────────────────────────────────────────────────────
def load_index() -> dict:
    ensure_dirs()
    return _read(index_path())


def save_index(index: dict) -> None:
    ensure_dirs()
    _backup(index_path(), 'households_index')
    _atomic_write(index_path(), index)


def households_for(email: str) -> list:
    out = []
    for hid, info in load_index().items():
        if email in info.get('members', []):
            out.append({'id': hid, 'name': info.get('name', hid), 'members': info.get('members', []),
                        'encrypted': info.get('encrypted', False), 'is_test': hid.startswith(TEST_PREFIX)})
    return out


def create_household(name: str, email: str, passphrase: Optional[str] = None) -> str:
    index = load_index()
    hid = str(uuid.uuid4())[:8]
    while hid in index:
        hid = str(uuid.uuid4())[:8]
    enc = bool(passphrase)
    index[hid] = {'name': name, 'members': [email], 'created_at': datetime.now().isoformat(),
                  'created_by': email, 'encrypted': enc}
    save_index(index)
    _atomic_write(hh_dir() / f"{hid}.json", {'household_name': name, 'encrypted': enc})
    return hid


def create_test_household(email: str) -> str:
    index = load_index()
    hid = TEST_PREFIX + str(uuid.uuid4())[:6]
    name = f'Test Household ({datetime.now().strftime("%b %d %H:%M")})'
    index[hid] = {'name': name, 'members': [email], 'created_at': datetime.now().isoformat(),
                  'created_by': email, 'is_test': True}
    save_index(index)
    _atomic_write(hh_dir() / f"{hid}.json", {'household_name': name, 'is_test': True})
    return hid


def join_household(hid: str, email: str):
    index = load_index()
    if hid not in index:
        return False, "Household not found"
    if email not in index[hid].setdefault('members', []):
        index[hid]['members'].append(email)
        save_index(index)
    return True, index[hid]['name']


def rename_household(hid: str, name: str) -> None:
    index = load_index()
    if hid not in index:
        return
    index[hid]['name'] = name
    save_index(index)                      # backs up the index first
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    if not hid.startswith(TEST_PREFIX):
        _backup(path, hid)
    hh['household_name'] = name
    _atomic_write(path, hh)


def remove_member(hid: str, email: str) -> bool:
    index = load_index()
    mem = index.get(hid, {}).get('members', [])
    if email not in mem or len(mem) <= 1:
        return False
    index[hid]['members'] = [m for m in mem if m != email]
    save_index(index)
    return True


def cleanup_test_households(email: str) -> int:
    """Remove this admin's _test_ households (exempt from the backup rule, see CLAUDE.md)."""
    index = load_index()
    gone = [h for h, i in index.items() if h.startswith(TEST_PREFIX) and email in i.get('members', [])]
    for h in gone:
        index.pop(h, None)
        f = hh_dir() / f"{h}.json"
        if f.exists():
            f.unlink()
    if gone:
        save_index(index)
    return len(gone)


def is_member(hid: str, email: str) -> bool:
    return email in load_index().get(hid, {}).get('members', [])


def household_info(hid: str) -> dict:
    return _read(hh_dir() / f"{hid}.json")


def members(hid: str) -> list:
    return load_index().get(hid, {}).get('members', [])


# ── plan ────────────────────────────────────────────────────────────────
class LockedError(Exception):
    pass


def load_plan(hid: str, passphrase: Optional[str] = None) -> Optional[dict]:
    hh = household_info(hid)
    if 'plan_data_encrypted' in hh:
        if not passphrase:
            raise LockedError()
        pt = decrypt(hh['plan_data_encrypted'], passphrase)
        if pt is None:
            raise LockedError()
        return json.loads(pt)
    pd = hh.get('plan_data')
    if isinstance(pd, str):
        try:
            pd = json.loads(pd)
        except json.JSONDecodeError:
            pd = None
    return pd


def check_passphrase(hid: str, passphrase: str) -> bool:
    hh = household_info(hid)
    if 'plan_data_encrypted' not in hh:
        return True
    return decrypt(hh['plan_data_encrypted'], passphrase) is not None


def save_plan(hid: str, plan: dict, user: str, passphrase: Optional[str] = None) -> str:
    """Merge `plan` into the stored plan (keys not sent are preserved)."""
    ensure_dirs()
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    try:
        existing = load_plan(hid, passphrase) or {}
    except LockedError:
        raise
    merged = {**existing, **plan}
    if hh and not hid.startswith(TEST_PREFIX):
        _backup(path, hid)
    if hh.get('encrypted') and passphrase:
        hh['plan_data_encrypted'] = encrypt(json.dumps(merged), passphrase)
        hh.pop('plan_data', None)
    else:
        hh['plan_data'] = merged
        hh.pop('plan_data_encrypted', None)
    now = datetime.now().isoformat()
    hh['last_saved'] = now
    hh['saved_by'] = user
    _atomic_write(path, hh)
    return now


def load_scenarios(hid: str) -> dict:
    return household_info(hid).get('scenarios', {}) or {}


def save_scenarios(hid: str, scenarios: dict) -> None:
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    if hh and not hid.startswith(TEST_PREFIX):
        _backup(path, hid)
    hh['scenarios'] = scenarios
    _atomic_write(path, hh)


def load_actuals(hid: str, passphrase: Optional[str] = None) -> dict:
    hh = household_info(hid)
    if 'actuals_encrypted' in hh:
        if passphrase:
            pt = decrypt(hh['actuals_encrypted'], passphrase)
            if pt:
                return json.loads(pt)
        return {}
    return hh.get('actuals', {}) or {}


def save_actuals(hid: str, actuals: dict, passphrase: Optional[str] = None) -> None:
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    if hh and not hid.startswith(TEST_PREFIX):
        _backup(path, hid)
    if hh.get('encrypted') and passphrase:
        hh['actuals_encrypted'] = encrypt(json.dumps(actuals), passphrase)
        hh.pop('actuals', None)
    else:
        hh['actuals'] = actuals
        hh.pop('actuals_encrypted', None)
    _atomic_write(path, hh)


# ── generic household-level keys (check-ins etc.) ──────────────────────────
def load_hh_key(hid: str, key: str, default, passphrase: Optional[str] = None):
    hh = household_info(hid)
    if f'{key}_encrypted' in hh:
        if passphrase:
            pt = decrypt(hh[f'{key}_encrypted'], passphrase)
            if pt:
                return json.loads(pt)
        return default
    v = hh.get(key)
    return default if v is None else v


def save_hh_key(hid: str, key: str, value, passphrase: Optional[str] = None, encrypt_if_needed: bool = True) -> None:
    ensure_dirs()
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    if hh and not hid.startswith(TEST_PREFIX):
        _backup(path, hid)
    if encrypt_if_needed and hh.get('encrypted') and passphrase:
        hh[f'{key}_encrypted'] = encrypt(json.dumps(value), passphrase)
        hh.pop(key, None)
    else:
        hh[key] = value
        hh.pop(f'{key}_encrypted', None)
    _atomic_write(path, hh)


# ── version history ──────────────────────────────────────────────────────
def list_versions(hid: str) -> list:
    bdir = data_dir() / 'backups'
    out = []
    for kind, folder in (('recent', bdir), ('daily', bdir / 'daily')):
        if not folder.exists():
            continue
        for f in folder.glob(f"{hid}_2*.json"):
            hh = _read(f)
            pd = hh.get('plan_data') if isinstance(hh.get('plan_data'), dict) else None
            if pd is None and 'plan_data_encrypted' not in hh:
                continue   # snapshot taken before any plan was saved
            summary = None
            if pd:
                summary = {'names': [pd.get('parent1_name'), pd.get('parent2_name')],
                           'savings': (pd.get('parentX_net_worth') or 0) + (pd.get('parentY_net_worth') or 0),
                           'homes': len(pd.get('houses') or []), 'kids': len(pd.get('children_list') or []),
                           'retire': [pd.get('parentX_retirement_age'), pd.get('parentY_retirement_age')]}
            out.append({'id': f"{kind}/{f.name}", 'kind': kind, 'file_time': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        'last_saved': hh.get('last_saved'), 'saved_by': hh.get('saved_by'),
                        'encrypted': 'plan_data_encrypted' in hh, 'summary': summary})
    out.sort(key=lambda v: v['last_saved'] or v['file_time'], reverse=True)
    return out


def _version_path(hid: str, vid: str) -> Path:
    kind, name = vid.split('/', 1)
    if '/' in name or '..' in name or not name.startswith(f"{hid}_") or kind not in ('recent', 'daily'):
        raise ValueError('bad version id')
    bdir = data_dir() / 'backups'
    return (bdir if kind == 'recent' else bdir / 'daily') / name


def load_version_plan(hid: str, vid: str, passphrase: Optional[str] = None) -> Optional[dict]:
    hh = _read(_version_path(hid, vid))
    if 'plan_data_encrypted' in hh:
        pt = decrypt(hh['plan_data_encrypted'], passphrase) if passphrase else None
        return json.loads(pt) if pt else None
    return hh.get('plan_data')


def restore_version(hid: str, vid: str, user: str, passphrase: Optional[str] = None) -> str:
    """Restore only plan_data from a snapshot (check-ins, scenarios and actuals are kept)."""
    plan = load_version_plan(hid, vid, passphrase)
    if plan is None:
        raise ValueError('snapshot has no readable plan')
    try:
        current = load_plan(hid, passphrase) or {}
    except LockedError:
        current = {}
    plan = {**current, **plan}   # merge: keys added since the snapshot are kept
    path = hh_dir() / f"{hid}.json"
    hh = _read(path)
    _backup(path, hid)
    if hh.get('encrypted') and passphrase:
        hh['plan_data_encrypted'] = encrypt(json.dumps(plan), passphrase)
        hh.pop('plan_data', None)
    else:
        hh['plan_data'] = plan
    hh['last_saved'] = datetime.now().isoformat()
    hh['saved_by'] = f"{user} (restored {vid.split('/', 1)[1]})"
    _atomic_write(path, hh)
    return hh['last_saved']
