"""Linked accounts: balances from Fidelity (and other brokerages) without typing.

Two ways in, both optional and usable together:

* **SnapTrade** (automatic, read-only). The household pastes its free SnapTrade *Personal*
  client ID and consumer key once, opens the Connection Portal to sign in at Fidelity, and
  the server pulls balances once a day (and on "Sync now"). Commercial keys also work when
  a user ID / user secret is given.
* **CSV import** (manual). Fidelity's Positions page → Download, or any CSV with an account
  column and a value column.

Stored in the household file (additive keys, encrypted like everything else in encrypted
households):
    integrations.snaptrade = {client_id, consumer_key, user_id?, user_secret?, added_by, added_at}
    linked_accounts = {accounts: {key: {...}}, covers_all, last_sync, last_error, connections}
Secrets are never returned to the browser.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime, timezone

API = 'https://api.snaptrade.com/api/v1'
KINDS = ('liquid', 'retirement', 'roth', 'hsa', 'ignore')


# ─────────────────────────────── SnapTrade ───────────────────────────────

def sign(path_and_query: str, consumer_key: str, body=None) -> str:
    """SnapTrade request signature (HMAC-SHA256 over canonical JSON of content, path, query; base64)."""
    subpath, query = path_and_query.split('?', 1)
    obj = {'content': None if body is None or body == {} else body, 'path': '/api/v1%s' % subpath, 'query': query}
    content = json.dumps(obj, separators=(',', ':'), sort_keys=True)
    return b64encode(hmac.new(consumer_key.encode(), content.encode(), hashlib.sha256).digest()).decode()


class SnapTradeError(Exception):
    def __init__(self, msg: str, status: int | None = None):
        super().__init__(msg)
        self.status = status


def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None, timeout: float = 30):
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class SnapTrade:
    """Minimal signed client. `transport(method, url, headers, body) -> (status, bytes)` is injectable for tests."""

    def __init__(self, cfg: dict, transport=None):
        self.client_id = (cfg.get('client_id') or '').strip()
        self.consumer_key = (cfg.get('consumer_key') or '').strip()
        self.user_id = (cfg.get('user_id') or '').strip() or None          # commercial keys only
        self.user_secret = (cfg.get('user_secret') or '').strip() or None
        self.transport = transport or _urllib_transport
        if not self.client_id or not self.consumer_key:
            raise SnapTradeError('SnapTrade client ID and consumer key are required')

    def _req(self, method: str, subpath: str, query: dict | None = None, body=None):
        q = {'clientId': self.client_id, 'timestamp': str(int(time.time()))}
        if self.user_id and self.user_secret:
            q.update(userId=self.user_id, userSecret=self.user_secret)
        q.update(query or {})
        qs = urllib.parse.urlencode(q)
        pq = f'{subpath}?{qs}'
        headers = {'Signature': sign(pq, self.consumer_key, body), 'Accept': 'application/json'}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        status, raw = self.transport(method, f'{API}{pq}', headers, data)
        try:
            payload = json.loads(raw.decode() or 'null')
        except (ValueError, AttributeError):
            payload = None
        if status >= 400:
            detail = (payload or {}).get('detail') if isinstance(payload, dict) else None
            raise SnapTradeError(f'SnapTrade {status}: {detail or (raw[:200].decode(errors="ignore") if raw else "error")}', status)
        return payload

    def portal_url(self, broker: str | None = None, reconnect: str | None = None, redirect: str | None = None) -> str:
        body = {'connectionType': 'read', 'immediateRedirect': bool(redirect)}
        if broker:
            body['broker'] = broker
        if reconnect:
            body['reconnect'] = reconnect
        if redirect:
            body['customRedirect'] = redirect
        r = self._req('POST', '/snapTrade/login', body=body)
        url = (r or {}).get('redirectURI') if isinstance(r, dict) else None
        if not url:
            raise SnapTradeError('SnapTrade did not return a connection link')
        return url

    def connections(self) -> list:
        return self._req('GET', '/authorizations') or []

    def accounts(self) -> list:
        return self._req('GET', '/accounts') or []

    def refresh(self, authorization_id: str):
        return self._req('POST', f'/authorizations/{authorization_id}/refresh')


# ─────────────────────────────── accounts ────────────────────────────────

def guess_kind(*texts) -> str:
    t = ' '.join(str(x or '') for x in texts).upper()
    if 'HSA' in t or 'HEALTH SAVINGS' in t:
        return 'hsa'
    if 'ROTH' in t:
        return 'roth'
    if re.search(r'\b(IRA|ROTH|401\s?\(?K\)?|403\s?\(?B\)?|457|SEP|SIMPLE|RETIREMENT|ROLLOVER|TSP|PENSION|BROKERAGELINK|KEOGH)\b', t):
        return 'retirement'
    return 'liquid'


def _mask(number: str) -> str:
    n = re.sub(r'\s', '', str(number or ''))
    return ('…' + n[-4:]) if len(n) >= 4 else n


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def empty_state() -> dict:
    # covers_all: None = not asked yet (treated as 'no': check-ins show linked totals as a hint only)
    return {'accounts': {}, 'covers_all': None, 'last_sync': None, 'last_error': None, 'connections': []}


def upsert(state: dict, key: str, fields: dict) -> dict:
    """Insert or update an account, keeping the user's choices (owner, kind, separate, include)."""
    st = state.setdefault('accounts', {})
    cur = st.get(key)
    if cur is None:
        cur = {'key': key, 'owner': 'p1', 'kind': guess_kind(fields.get('name'), fields.get('raw_type')),
               'separate': False, 'include': True}
    cur.update({k: v for k, v in fields.items() if v is not None})
    st[key] = cur
    return cur


def apply_snaptrade(state: dict, accounts: list, connections: list) -> dict:
    conn = {c.get('id'): c for c in connections or []}
    state['connections'] = [{'id': c.get('id'), 'institution': ((c.get('brokerage') or {}).get('name') or ''),
                             'disabled': bool(c.get('disabled')), 'disabled_date': c.get('disabled_date')} for c in connections or []]
    seen = set()
    for a in accounts or []:
        key = f"snaptrade:{a.get('id')}"
        seen.add(key)
        bal = ((a.get('balance') or {}).get('total') or {})
        c = conn.get(a.get('brokerage_authorization')) or {}
        sync = ((a.get('sync_status') or {}).get('holdings') or {})
        upsert(state, key, {
            'source': 'snaptrade', 'institution': a.get('institution_name') or ((c.get('brokerage') or {}).get('name')),
            'name': a.get('name') or a.get('raw_type') or 'Account', 'number': _mask(a.get('number')),
            'raw_type': a.get('raw_type'), 'balance': float(bal.get('amount') or 0.0), 'currency': bal.get('currency') or 'USD',
            'as_of': sync.get('last_successful_sync') or _now(), 'connection_id': a.get('brokerage_authorization'),
            'disabled': bool(c.get('disabled')), 'status': a.get('status')})
    # accounts that disappeared from SnapTrade are kept but flagged
    for k, v in state.get('accounts', {}).items():
        if v.get('source') == 'snaptrade' and k not in seen:
            v['missing'] = True
        elif k in seen:
            v.pop('missing', None)
    state['last_sync'] = _now()
    state['last_error'] = None
    return state


# ─────────────────────────────── CSV import ──────────────────────────────

def _money(s) -> float | None:
    if s is None:
        return None
    t = str(s).strip().replace('$', '').replace(',', '').replace('"', '')
    if t in ('', '--', 'n/a', 'N/A'):
        return None
    neg = t.startswith('(') and t.endswith(')')
    t = t.strip('()').replace('+', '')
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


VALUE_COLS = ('current value', 'market value', 'value', 'balance', 'total value', 'ending balance', 'amount')
ACCOUNT_COLS = ('account number', 'account', 'account name', 'account #', 'acct')


def parse_csv(text: str, institution_hint: str = '') -> list[dict]:
    """Fidelity positions export (one or many accounts per file) or any CSV with account + value columns.
    Returns [{number, name, balance, positions}] summed per account."""
    text = text.lstrip('﻿')
    lines = text.splitlines()
    # find the header row (Fidelity puts disclaimers after the table; some exports have preamble rows)
    start = None
    for i, ln in enumerate(lines[:40]):
        low = ln.lower()
        if any(c in low for c in VALUE_COLS) and ('account' in low or 'symbol' in low or 'description' in low):
            start = i
            break
    if start is None:
        raise ValueError("Couldn't find a header row with an account and a value column")
    reader = csv.DictReader(io.StringIO('\n'.join(lines[start:])))
    heads = {h.lower().strip(): h for h in (reader.fieldnames or []) if h}
    vcol = next((heads[c] for c in VALUE_COLS if c in heads), None)
    ncol = next((heads[c] for c in ('account number', 'account #', 'acct', 'account') if c in heads), None)
    namecol = next((heads[c] for c in ('account name', 'account', 'description') if c in heads and heads[c] != ncol), None)
    if not vcol:
        raise ValueError('No value column (e.g. "Current Value") in this file')
    out: dict[str, dict] = {}
    for row in reader:
        if not row or all(not (v or '').strip() for v in row.values() if isinstance(v, str)):
            continue
        val = _money(row.get(vcol))
        num = (row.get(ncol) or '').strip() if ncol else ''
        name = (row.get(namecol) or '').strip() if namecol else ''
        if val is None or (not num and not name):
            continue   # footer / disclaimer rows
        k = num or name
        a = out.setdefault(k, {'number': num, 'name': name or num, 'balance': 0.0, 'positions': 0})
        a['balance'] += val
        a['positions'] += 1
    if not out:
        raise ValueError('No account balances found in this file')
    return [{**a, 'balance': round(a['balance'], 2)} for a in out.values()]


def apply_csv(state: dict, parsed: list[dict], institution: str, filename: str = '') -> list[dict]:
    done = []
    for a in parsed:
        ident = re.sub(r'\W', '', (a['number'] or a['name']).lower())
        inst = re.sub(r'\W', '', institution.lower()) or 'file'
        key = f'csv:{inst}:{ident}'
        done.append(upsert(state, key, {'source': 'csv', 'institution': institution, 'name': a['name'], 'number': _mask(a['number']),
                                        'raw_type': None, 'balance': a['balance'], 'currency': 'USD', 'as_of': _now(),
                                        'file': filename, 'positions': a['positions']}))
    return done


# ─────────────────────────────── balances ────────────────────────────────

def totals(state: dict, single: bool = False) -> dict:
    """Per-person balances in the check-in shape: {p1: {liquid, pretax, separate_liquid, separate_pretax}, p2, hsa}.
    Joint accounts are split evenly; HSA counts toward retirement accounts (the plan treats it as pre-tax)."""
    out = {w: {'liquid': 0.0, 'pretax': 0.0, 'roth': 0.0, 'separate_liquid': 0.0, 'separate_pretax': 0.0, 'any_separate': False} for w in ('p1', 'p2')}
    oldest = None
    n = 0
    for a in (state.get('accounts') or {}).values():
        if not a.get('include', True) or a.get('kind') == 'ignore' or a.get('missing'):
            continue
        n += 1
        bucket = 'liquid' if a.get('kind') == 'liquid' else 'roth' if a.get('kind') == 'roth' else 'pretax'
        owners = ['p1'] if single else (['p1', 'p2'] if a.get('owner') == 'joint' else [a.get('owner') if a.get('owner') in ('p1', 'p2') else 'p1'])
        share = float(a.get('balance') or 0) / len(owners)
        for w in owners:
            out[w][bucket] += share
            if a.get('separate') and a.get('owner') != 'joint':
                out[w]['separate_' + ('liquid' if bucket == 'liquid' else 'pretax')] += share
                out[w]['any_separate'] = True
        ts = a.get('as_of')
        if ts and (oldest is None or ts < oldest):
            oldest = ts
    return {**out, 'accounts': n, 'as_of': oldest}


def public(state: dict) -> dict:
    """State for the browser (no secrets live here, but keep it tidy)."""
    s = empty_state()
    s.update({k: v for k, v in (state or {}).items() if k in s})
    s['accounts'] = sorted((state or {}).get('accounts', {}).values(), key=lambda a: (a.get('institution') or '', a.get('name') or ''))
    return s
