"""Check-in scheduling helpers (see docs/CHECKINS.md)."""
from __future__ import annotations

import secrets
from datetime import date, timedelta

CADENCE_MONTHS = {'quarterly': 3, 'semiannual': 6, 'annual': 12}


def period_label(d: date, cadence: str) -> str:
    if cadence == 'annual':
        return f"{d.year}"
    if cadence == 'semiannual':
        return f"{d.year}-H{1 if d.month <= 6 else 2}"
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def next_period_start(d: date, cadence: str) -> date:
    """First day of the period after the one containing d."""
    m = CADENCE_MONTHS.get(cadence, 3)
    start_month = ((d.month - 1) // m) * m + 1
    month = start_month + m
    year = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1)


def default_settings(today: date | None = None) -> dict:
    today = today or date.today()
    return {'cadence': 'quarterly', 'next_due': next_period_start(today, 'quarterly').isoformat(), 'snoozed_until': None}


def normalize_settings(s: dict | None, today: date | None = None) -> dict:
    base = default_settings(today)
    s = {**base, **(s or {})}
    if s['cadence'] not in (*CADENCE_MONTHS, 'off'):
        s['cadence'] = 'quarterly'
    return s


def is_due(s: dict, today: date | None = None) -> bool:
    today = today or date.today()
    if s.get('cadence') == 'off' or not s.get('next_due'):
        return False
    if s.get('snoozed_until') and date.fromisoformat(s['snoozed_until']) > today:
        return False
    return date.fromisoformat(s['next_due']) <= today


def after_checkin(s: dict, d: date, kind: str) -> dict:
    """Advance the schedule. Manual check-ins count if within 3 weeks of the due date."""
    s = dict(s)
    if s.get('cadence') == 'off':
        return s
    due = date.fromisoformat(s['next_due']) if s.get('next_due') else d
    if d >= due - timedelta(days=21):          # on time, late, or up to 3 weeks early
        s['next_due'] = next_period_start(max(d, due), s['cadence']).isoformat()
        s['snoozed_until'] = None
    elif kind == 'baseline':                   # onboarding: next period, but not within a month
        nxt = next_period_start(d, s['cadence'])
        if (nxt - d).days < 30:
            nxt = next_period_start(nxt, s['cadence'])
        s['next_due'] = nxt.isoformat()
    return s


def new_id() -> str:
    return 'c_' + secrets.token_hex(4)


def ics(settings: dict, app_url: str, household_name: str) -> str:
    """Repeating calendar reminder for the check-in cadence."""
    m = CADENCE_MONTHS.get(settings.get('cadence'), 3)
    due = date.fromisoformat(settings['next_due'])
    uid = f"finplan-checkin-{secrets.token_hex(6)}@financial-planner"
    stamp = date.today().strftime('%Y%m%d') + 'T000000Z'
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Financial Planning Suite//Check-ins//EN", "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{due.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(due + timedelta(days=1)).strftime('%Y%m%d')}",
        f"RRULE:FREQ=MONTHLY;INTERVAL={m}",
        f"SUMMARY:Financial check-in ({household_name})",
        f"DESCRIPTION:5-minute check-in: update balances and see if you're on track. {app_url}/checkins",
        f"URL:{app_url}/checkins",
        "BEGIN:VALARM", "TRIGGER:PT9H", "ACTION:DISPLAY", "DESCRIPTION:Financial check-in due", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR", ""])
