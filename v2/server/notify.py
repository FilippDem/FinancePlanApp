"""Email reminders for due check-ins.

Configure with environment variables (docker-compose.yml):
  SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM (defaults to SMTP_USER),
  SMTP_TLS (starttls|ssl|none, default starttls), APP_URL (link in the email),
  REMINDER_CHECK_MINUTES (default 60).
Gmail: use an App Password (Google Account → Security → App passwords), SMTP_HOST=smtp.gmail.com.

Rules: a household gets an email when a check-in is due and email reminders are on
(checkin_settings.email_reminders). At most one reminder per due date, plus one
follow-up 7 days later if still not done.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
import threading
import time
from datetime import date, datetime, timedelta
from email.message import EmailMessage

from server import storage as S
from server import checkins as CK

log = logging.getLogger('finplan.notify')


def configured() -> bool:
    return bool(os.environ.get('SMTP_HOST'))


def send(to: list[str], subject: str, text: str, html: str | None = None) -> None:
    host = os.environ['SMTP_HOST']
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ.get('SMTP_USER')
    pw = os.environ.get('SMTP_PASSWORD')
    sender = os.environ.get('SMTP_FROM') or user or 'planner@localhost'
    mode = os.environ.get('SMTP_TLS', 'starttls').lower()
    msg = EmailMessage()
    msg['Subject'], msg['From'], msg['To'] = subject, sender, ', '.join(to)
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype='html')
    if mode == 'ssl':
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20) as s:
            if user:
                s.login(user, pw or '')
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            if mode == 'starttls':
                s.starttls(context=ssl.create_default_context())
            if user:
                s.login(user, pw or '')
            s.send_message(msg)


def reminder_email(household: str, period: str, url: str, follow_up: bool = False) -> tuple[str, str, str]:
    subject = f"{'Reminder: ' if follow_up else ''}Your {period.replace('-', ' ')} financial check-in is due"
    link = f"{url.rstrip('/')}/checkin"
    text = (f"Hi {household},\n\nIt's time for your {period.replace('-', ' ')} check-in. It takes about 5 minutes: update your "
            f"balances, see if you're on track, and roll your plan forward.\n\nStart here: {link}\n\n"
            f"Short on time? Do a 30-second quick update: {link}?mode=quick\n\n— Financial Planning Suite\n"
            f"(Turn these emails off on the Check-ins page.)")
    html = (f"<div style='font-family:-apple-system,Segoe UI,sans-serif;max-width:520px'>"
            f"<h2 style='margin:0 0 8px'>Your {period.replace('-', ' ')} check-in is due</h2>"
            f"<p>About 5 minutes: update your balances, see if you're on track, and roll your plan forward.</p>"
            f"<p><a href='{link}' style='display:inline-block;background:#2a78d6;color:#fff;padding:10px 18px;border-radius:8px;"
            f"text-decoration:none;font-weight:600'>Start check-in</a> &nbsp; <a href='{link}?mode=quick'>Quick update</a></p>"
            f"<p style='color:#888;font-size:12px'>Turn these emails off on the Check-ins page.</p></div>")
    return subject, text, html


def run_once(today: date | None = None, sender=send) -> list[str]:
    """Check every household and send due reminders. Returns household ids emailed."""
    today = today or date.today()
    url = os.environ.get('APP_URL', 'http://localhost:8502')
    sent = []
    for hid, info in S.load_index().items():
        if hid.startswith(S.TEST_PREFIX):
            continue
        settings = CK.normalize_settings(S.load_hh_key(hid, 'checkin_settings', None))
        if not settings.get('email_reminders') or not CK.is_due(settings, today):
            continue
        due = settings['next_due']
        last_due = settings.get('last_emailed_due')
        last_at = date.fromisoformat(settings['last_emailed_at']) if settings.get('last_emailed_at') else None
        follow = False
        if last_due == due:
            if settings.get('followup_sent') or not last_at or (today - last_at).days < 7:
                continue
            follow = True
        members = [m for m in info.get('members', []) if '@' in m]
        if not members:
            continue
        period = CK.period_label(date.fromisoformat(due) - timedelta(days=1), settings['cadence'])
        subj, text, html = reminder_email(info.get('name', 'there'), CK.period_label(date.fromisoformat(due), settings['cadence']), url, follow)
        try:
            sender(members, subj, text, html)
        except Exception as e:  # never crash the scheduler
            log.warning('reminder to %s failed: %s', hid, e)
            continue
        settings.update(last_emailed_due=due, last_emailed_at=today.isoformat(), followup_sent=follow)
        S.save_hh_key(hid, 'checkin_settings', settings, encrypt_if_needed=False)
        sent.append(hid)
    return sent


_started = False


def start_scheduler():
    global _started
    if _started or not configured() or os.environ.get('DISABLE_REMINDERS') == '1':
        return
    _started = True
    minutes = int(os.environ.get('REMINDER_CHECK_MINUTES', '60'))

    def loop():
        while True:
            try:
                sent = run_once()
                if sent:
                    log.info('sent check-in reminders to %s', sent)
            except Exception as e:
                log.warning('reminder loop error: %s', e)
            time.sleep(minutes * 60)
    threading.Thread(target=loop, daemon=True, name='checkin-reminders').start()
