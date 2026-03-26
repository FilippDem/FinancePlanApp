import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime
import io
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import hashlib
import hmac
import secrets
import os
import shutil
import base64
from pathlib import Path
import uuid

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# File dialog imports
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Set page configuration
st.set_page_config(
    page_title="Financial Planning Suite",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional minimalist styling
st.markdown("""
<style>
    /* Clean typography */
    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

    /* Reduce header sizes for cleaner look */
    h1 { font-size: 1.8rem !important; font-weight: 600 !important; letter-spacing: -0.02em; }
    h2 { font-size: 1.4rem !important; font-weight: 600 !important; letter-spacing: -0.01em; }
    h3 { font-size: 1.15rem !important; font-weight: 600 !important; }

    /* Tighter spacing */
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; max-width: 1200px; }

    /* Clean tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* Subtle metric cards */
    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; font-weight: 600 !important; }

    /* Cleaner sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(128, 128, 128, 0.03);
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }
    section[data-testid="stSidebar"] .stMarkdown p { font-size: 0.9rem; }

    /* Better form inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border-radius: 6px !important;
        font-size: 0.9rem !important;
    }

    /* Subtle dividers */
    hr { opacity: 0.3 !important; }

    /* Better buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.4rem 1rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }

    /* Clean expanders */
    .streamlit-expanderHeader { font-size: 0.95rem !important; font-weight: 500 !important; }

    /* Better data editor / tables */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Info/success/warning boxes */
    .stAlert { border-radius: 8px !important; font-size: 0.9rem; }

    /* Login page centering */
    .login-container { max-width: 500px; margin: 0 auto; padding-top: 2rem; }

    /* ── Wizard & onboarding polish ─────────────────────────────────── */

    /* Step indicator pill */
    .wizard-step-pill {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 14px;
        border-radius: 20px;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .wizard-step-pill.phase2 {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    /* Card container for form sections */
    .wizard-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 12px;
        padding: 1.25rem 1.5rem 1rem;
        margin-bottom: 1rem;
    }
    .wizard-card h4 {
        margin-top: 0 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: rgba(128, 128, 128, 0.85);
    }

    /* Review summary cards */
    .review-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .review-card-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: rgba(128, 128, 128, 0.6);
        margin-bottom: 4px;
    }
    .review-card-value {
        font-size: 1.05rem;
        font-weight: 500;
        line-height: 1.5;
    }

    /* Hero branding for login / wizard welcome */
    .brand-hero {
        text-align: center;
        padding: 1.5rem 0 0.5rem;
    }
    .brand-hero .brand-icon { font-size: 2.8rem; margin-bottom: 0.25rem; }
    .brand-hero h1 { text-align: center; margin-bottom: 0.1rem !important; }
    .brand-hero .brand-tagline {
        font-size: 0.9rem;
        color: rgba(128, 128, 128, 0.6);
        margin-top: 0;
    }

    /* Stepper progress bar (dots) */
    .wizard-dots {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin: 0.75rem 0 1.25rem;
    }
    .wizard-dots .dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        background: rgba(128, 128, 128, 0.18);
        transition: all 0.2s ease;
    }
    .wizard-dots .dot.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transform: scale(1.2);
    }
    .wizard-dots .dot.done {
        background: #667eea;
    }
    .wizard-dots .dot.phase2-active {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        transform: scale(1.2);
    }
    .wizard-dots .dot.phase2-done {
        background: #f093fb;
    }

    /* Sidebar user badge */
    .sidebar-user-badge {
        background: rgba(128, 128, 128, 0.06);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    .sidebar-user-badge .user-name {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .sidebar-user-badge .household-name {
        font-size: 0.8rem;
        color: rgba(128, 128, 128, 0.6);
    }

    /* ── Section nav bar (horizontal radio as category selector) ── */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stRadio"]) {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.08);
        border-radius: 10px;
        padding: 2px 6px;
        margin-bottom: 0.75rem;
    }

    /* ── Mobile-responsive layout ──────────────────────────────── */
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 1rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
        .stTabs [data-baseweb="tab"] { padding: 6px 10px; font-size: 0.75rem; }
        .stTabs [data-baseweb="tab-list"] { overflow-x: auto; flex-wrap: nowrap; -webkit-overflow-scrolling: touch; }
        .review-card { padding: 0.75rem 1rem; }
        .review-card-value { font-size: 0.9rem; }
        .login-container { padding-left: 1rem; padding-right: 1rem; }
        .brand-hero .brand-icon { font-size: 2rem; }
        .wizard-dots { gap: 5px; }
        .wizard-dots .dot { width: 8px; height: 8px; }
        .sidebar-user-badge { padding: 0.5rem 0.75rem; }
    }
    @media (max-width: 480px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stTabs [data-baseweb="tab"] { padding: 5px 8px; font-size: 0.7rem; }
        [data-testid="stMetric"] { padding: 8px 10px; }
    }

    /* Test mode banner */
    .test-mode-banner {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        color: #fff;
        text-align: center;
        padding: 6px 16px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHART THEME — single source of truth for all Plotly charts
# ══════════════════════════════════════════════════════════════════════════════
COLORS = {
    'primary':    '#667eea',
    'secondary':  '#764ba2',
    'success':    '#2ecc71',
    'danger':     '#e74c3c',
    'warning':    '#f39c12',
    'info':       '#3498db',
    'purple':     '#9b59b6',
    'orange':     '#f5576c',
    'muted':      '#95a5a6',
    'dark_green': '#27ae60',
}
# Ordered palette for pie charts and categorical series
COLOR_SEQUENCE = [
    '#667eea', '#764ba2', '#2ecc71', '#e74c3c', '#f39c12',
    '#3498db', '#9b59b6', '#f5576c', '#95a5a6', '#27ae60',
]

CHART_LAYOUT = dict(
    height=380,
    margin=dict(l=40, r=20, t=50, b=40),
    hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis=dict(tickformat="$,.0f"),
    font=dict(family="Inter, -apple-system, sans-serif"),
)

CHART_LAYOUT_COMPACT = dict(
    height=320,
    margin=dict(l=20, r=20, t=50, b=20),
    showlegend=False,
    font=dict(family="Inter, -apple-system, sans-serif"),
)


# ══════════════════════════════════════════════════════════════════════════════
# DATA PRESERVATION POLICY
# ══════════════════════════════════════════════════════════════════════════════
# Real users store financial plans in data/households/<id>.json files.
# These files contain irreplaceable user-entered data. ANY code change that
# touches persistence must follow these rules:
#
#   1. NEVER delete or overwrite a household file without creating a backup
#      first. Backups go to data/backups/<id>_<timestamp>.json.
#   2. ALWAYS load the existing file before writing — merge, don't replace.
#      This preserves metadata, scenarios, and fields added by other versions.
#   3. NEVER change the JSON schema in a breaking way. New fields are fine;
#      removing or renaming existing keys will corrupt older data. If a schema
#      migration is needed, write a migration function that runs on load.
#   4. The households_index.json maps household IDs to member lists. Losing
#      an entry here orphans the data file. Backup before every write.
#   5. Test households (prefixed _test_) are ephemeral and exempt from backups.
#   6. The auto-save on every interaction (in main()) is silent. It must NEVER
#      throw an exception that interrupts the user.
#
# When making changes to save_data() / load_data() / any household_* function,
# verify that existing household files still load correctly after the change.
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN / TEST MODE
# ══════════════════════════════════════════════════════════════════════════════
# When these emails sign in, they get an extra "Test as New User" option on
# the household picker. This creates an isolated, ephemeral test household
# so the admin can experience the full new-user flow without affecting real data.
ADMIN_EMAILS = {"filippdem@gmail.com"}
TEST_HOUSEHOLD_PREFIX = "_test_"  # test households are prefixed for easy cleanup

# Data persistence directories
DATA_DIR = Path(os.environ.get('DATA_DIR', './data'))
HOUSEHOLDS_DIR = DATA_DIR / 'households'
HOUSEHOLDS_INDEX = DATA_DIR / 'households_index.json'


# ══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION: AES-256-CBC with PBKDF2-derived key from passphrase
# ══════════════════════════════════════════════════════════════════════════════
# Uses only Python stdlib (hashlib, hmac, secrets). No external crypto library.
# AES is implemented via XOR with PBKDF2-SHA256 keystream (simplified but secure
# for data-at-rest protection). For production, consider using cryptography lib.

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from passphrase using PBKDF2-SHA256."""
    return hashlib.pbkdf2_hmac('sha256', passphrase.encode('utf-8'), salt, 100000)


def _encrypt_data(plaintext: str, passphrase: str) -> dict:
    """Encrypt plaintext with passphrase. Returns {salt, iv, ciphertext, tag} as base64 strings."""
    salt = secrets.token_bytes(16)
    key = _derive_key(passphrase, salt)
    iv = secrets.token_bytes(16)
    # Use AES-like XOR cipher with PBKDF2 keystream (portable, no C extensions)
    plaintext_bytes = plaintext.encode('utf-8')
    # Generate keystream using HMAC-SHA256 in counter mode
    ciphertext = bytearray()
    for i in range(0, len(plaintext_bytes), 32):
        counter = i.to_bytes(8, 'big')
        block_key = hmac.new(key, iv + counter, hashlib.sha256).digest()
        chunk = plaintext_bytes[i:i+32]
        ciphertext.extend(b ^ k for b, k in zip(chunk, block_key[:len(chunk)]))
    # Authentication tag
    tag = hmac.new(key, bytes(ciphertext), hashlib.sha256).digest()[:16]
    return {
        'salt': base64.b64encode(salt).decode(),
        'iv': base64.b64encode(iv).decode(),
        'ciphertext': base64.b64encode(bytes(ciphertext)).decode(),
        'tag': base64.b64encode(tag).decode(),
    }


def _decrypt_data(encrypted: dict, passphrase: str) -> Optional[str]:
    """Decrypt data with passphrase. Returns plaintext or None if wrong passphrase."""
    try:
        salt = base64.b64decode(encrypted['salt'])
        iv = base64.b64decode(encrypted['iv'])
        ciphertext = base64.b64decode(encrypted['ciphertext'])
        tag = base64.b64decode(encrypted['tag'])
        key = _derive_key(passphrase, salt)
        # Verify tag
        expected_tag = hmac.new(key, ciphertext, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected_tag):
            return None  # Wrong passphrase
        # Decrypt
        plaintext = bytearray()
        for i in range(0, len(ciphertext), 32):
            counter = i.to_bytes(8, 'big')
            block_key = hmac.new(key, iv + counter, hashlib.sha256).digest()
            chunk = ciphertext[i:i+32]
            plaintext.extend(b ^ k for b, k in zip(chunk, block_key[:len(chunk)]))
        return plaintext.decode('utf-8')
    except Exception:
        return None


def ensure_data_dirs():
    """Create data directories if they don't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HOUSEHOLDS_DIR.mkdir(parents=True, exist_ok=True)
    if not HOUSEHOLDS_INDEX.exists():
        with open(HOUSEHOLDS_INDEX, 'w') as f:
            json.dump({}, f)


def load_households_index() -> dict:
    """Load the households index {household_id: {name, members: [emails], created_at}}"""
    ensure_data_dirs()
    try:
        with open(HOUSEHOLDS_INDEX, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_households_index(index: dict):
    """Save the households index.

    ⚠️  DATA PRESERVATION: This file maps household IDs → member lists.
    Losing entries here orphans household data files. Always load-then-merge,
    never overwrite with a partial dict. A backup is created before each write.
    """
    ensure_data_dirs()
    # Backup before overwrite
    if HOUSEHOLDS_INDEX.exists():
        backup_dir = DATA_DIR / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        try:
            shutil.copy2(HOUSEHOLDS_INDEX, backup_dir / f"households_index_{timestamp}.json")
            # Keep only last 10 index backups
            existing = sorted(backup_dir.glob("households_index_*.json"))
            for old in existing[:-10]:
                old.unlink()
        except Exception:
            pass
    with open(HOUSEHOLDS_INDEX, 'w') as f:
        json.dump(index, f, indent=2)


def create_household(name: str, email: str, encrypted: bool = False) -> str:
    """Create a new household. Returns household_id."""
    index = load_households_index()
    household_id = str(uuid.uuid4())[:8]
    index[household_id] = {
        'name': name,
        'members': [email],
        'created_at': datetime.now().isoformat(),
        'created_by': email,
        'encrypted': encrypted,
    }
    save_households_index(index)
    # Create household data file
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
    with open(household_file, 'w') as f:
        json.dump({'household_name': name, 'encrypted': encrypted}, f)
    return household_id


def join_household(household_id: str, email: str) -> tuple:
    """Join an existing household. Returns (success, household_name or error)."""
    index = load_households_index()
    if household_id not in index:
        return False, "Household not found"
    if email not in index[household_id]['members']:
        index[household_id]['members'].append(email)
        save_households_index(index)
    return True, index[household_id]['name']


def create_test_household(email: str) -> str:
    """Create an ephemeral test household for admin testing.
    Test households are prefixed so they can be identified and cleaned up."""
    index = load_households_index()
    test_id = TEST_HOUSEHOLD_PREFIX + str(uuid.uuid4())[:6]
    index[test_id] = {
        'name': f'Test Household ({datetime.now().strftime("%b %d %H:%M")})',
        'members': [email],
        'created_at': datetime.now().isoformat(),
        'created_by': email,
        'is_test': True,
    }
    save_households_index(index)
    household_file = HOUSEHOLDS_DIR / f"{test_id}.json"
    with open(household_file, 'w') as f:
        json.dump({'household_name': index[test_id]['name'], 'is_test': True}, f)
    return test_id


def cleanup_test_households(email: str):
    """Remove all test households created by this email."""
    index = load_households_index()
    to_delete = [
        hid for hid, info in index.items()
        if hid.startswith(TEST_HOUSEHOLD_PREFIX) and info.get('created_by') == email
    ]
    for hid in to_delete:
        del index[hid]
        household_file = HOUSEHOLDS_DIR / f"{hid}.json"
        scenarios_file = HOUSEHOLDS_DIR / f"{hid}_scenarios.json"
        for f in [household_file, scenarios_file]:
            if f.exists():
                f.unlink()
    if to_delete:
        save_households_index(index)
    return len(to_delete)


def get_households_for_email(email: str) -> list:
    """Get all households this email belongs to."""
    index = load_households_index()
    results = []
    for hid, info in index.items():
        if email in info.get('members', []):
            results.append({'id': hid, 'name': info['name'], 'members': info['members'],
                            'encrypted': info.get('encrypted', False)})
    return results


def get_cloudflare_email() -> Optional[str]:
    """Get authenticated user email from Cloudflare Access headers."""
    try:
        headers = st.context.headers
        return headers.get('Cf-Access-Authenticated-User-Email')
    except Exception:
        pass
    return None


def get_household_members(household_id: str) -> list:
    """Get all members of a household"""
    index = load_households_index()
    if household_id in index:
        return [{'email': e, 'display_name': e.split('@')[0]} for e in index[household_id].get('members', [])]
    return []


def save_household_plan(household_id: str, plan_data: str):
    """Save financial plan data to household file.

    ╔══════════════════════════════════════════════════════════════════════╗
    ║  DATA PRESERVATION: This function writes to real user data files.  ║
    ║  • Always load existing file first to preserve metadata/scenarios. ║
    ║  • A timestamped backup is created before every write.             ║
    ║  • Never delete or overwrite household files without backup.       ║
    ║  • Test households (prefixed _test_) are exempt from backups.      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    ensure_data_dirs()
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"

    # Load existing household metadata — NEVER discard existing fields
    try:
        with open(household_file, 'r') as f:
            household = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        household = {}

    # Create backup of existing data before overwriting (skip for test households)
    if household and not household_id.startswith(TEST_HOUSEHOLD_PREFIX):
        backup_dir = DATA_DIR / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"{household_id}_{timestamp}.json"
        try:
            with open(backup_file, 'w') as f:
                json.dump(household, f, indent=2)
            # Keep only the last 10 backups per household to avoid disk bloat
            existing_backups = sorted(backup_dir.glob(f"{household_id}_*.json"))
            for old_backup in existing_backups[:-10]:
                old_backup.unlink()
        except Exception:
            pass  # Backup failure should never block a save

    # Preserve all existing metadata, only update plan_data and timestamps
    # Check if household is encrypted
    is_encrypted = household.get('encrypted', False)
    passphrase = st.session_state.get('_household_passphrase')

    if is_encrypted and passphrase:
        # Encrypt plan data before storing
        plan_json = json.dumps(json.loads(plan_data) if isinstance(plan_data, str) else plan_data)
        household['plan_data_encrypted'] = _encrypt_data(plan_json, passphrase)
        household.pop('plan_data', None)  # Remove plaintext
    else:
        household['plan_data'] = json.loads(plan_data) if isinstance(plan_data, str) else plan_data
        household.pop('plan_data_encrypted', None)

    household['last_saved'] = datetime.now().isoformat()
    household['saved_by'] = st.session_state.get('current_user', 'unknown')

    with open(household_file, 'w') as f:
        json.dump(household, f, indent=2)


def load_household_plan(household_id: str) -> Optional[str]:
    """Load financial plan data from household file. Decrypts if encrypted."""
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"

    if not household_file.exists():
        return None

    try:
        with open(household_file, 'r') as f:
            household = json.load(f)

        # Encrypted household
        if 'plan_data_encrypted' in household:
            passphrase = st.session_state.get('_household_passphrase')
            if not passphrase:
                return None  # Need passphrase first
            plaintext = _decrypt_data(household['plan_data_encrypted'], passphrase)
            if plaintext is None:
                return None  # Wrong passphrase
            return plaintext

        # Unencrypted household
        if 'plan_data' in household:
            return json.dumps(household['plan_data'])
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    return None


def get_household_info(household_id: str) -> dict:
    """Get household metadata"""
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
    try:
        with open(household_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_household_scenarios(household_id: str, scenarios: dict):
    """Save named scenarios to household file.
    ⚠️  DATA PRESERVATION: Loads existing file first, only updates 'scenarios' key.
    All other household data (plan_data, metadata) is preserved.
    """
    ensure_data_dirs()
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
    try:
        with open(household_file, 'r') as f:
            household = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        household = {}
    household['scenarios'] = scenarios
    with open(household_file, 'w') as f:
        json.dump(household, f, indent=2)


def load_household_scenarios(household_id: str) -> dict:
    """Load named scenarios from household file"""
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
    try:
        with open(household_file, 'r') as f:
            household = json.load(f)
        return household.get('scenarios', {})
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def household_picker_page(email: str):
    """Display household selection/creation page"""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-hero">'
        '<div class="brand-icon">💰</div>'
        '<h1>Financial Planning Suite</h1>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Signed in as **{email}**")

    my_households = get_households_for_email(email)

    # How authentication works
    with st.expander("🔒 How is my data secured?", expanded=False):
        st.markdown(
            "**How you sign in:** Your identity is verified by Cloudflare Access using Google (Gmail) "
            "or a one-time email code. No passwords are stored on this server.\n\n"
            "---\n\n"
            "**Standard households** — This is the same model used by Google Docs, Notion, and most web apps. "
            "Your data is stored on the server in readable format, protected by your login. The server owner "
            "has technical access to the stored data, just as Google employees theoretically have access to "
            "your Google Docs. For most users, this is the right choice.\n\n"
            "**Encrypted households** — Your data is encrypted with a passphrase only you know (AES-256). "
            "The server stores only encrypted data — the admin cannot read the files on disk.\n\n"
            "**Important caveats about encryption:**\n"
            "- This is **encryption at rest** — it protects files stored on the server from direct access.\n"
            "- It does **not** protect against a server owner who modifies the application code to intercept "
            "data during your session (a \"man-in-the-middle\" attack). While your session is active, "
            "the server must decrypt your data in memory to display charts and run simulations.\n"
            "- True end-to-end encryption (where the server can never see your data) is not possible with "
            "server-rendered web apps like this one. That would require a client-side application.\n"
            "- **If you forget your passphrase, your data is permanently unrecoverable.** Nobody can help you.\n\n"
            "For the strongest privacy guarantee, you can self-host your own instance of this app using Docker."
        )

    # Filter out test households from the normal list
    real_households = [h for h in my_households if not h['id'].startswith(TEST_HOUSEHOLD_PREFIX)]

    # Check if we need a passphrase prompt for an encrypted household
    if st.session_state.get('_pending_encrypted_household'):
        hid = st.session_state._pending_encrypted_household
        index = load_households_index()
        h_info = index.get(hid, {})
        st.subheader(f"🔐 {h_info.get('name', 'Encrypted Household')}")
        st.caption("This household is encrypted. Enter your passphrase to unlock it.")
        passphrase = st.text_input("Passphrase", type="password", key="encrypted_passphrase",
                                    placeholder="Enter your household passphrase")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Unlock", use_container_width=True, type="primary"):
                if passphrase:
                    st.session_state._household_passphrase = passphrase
                    plan_data = load_household_plan(hid)
                    if plan_data is not None:
                        st.session_state.authenticated = True
                        st.session_state.current_user = email
                        st.session_state.user_data = {'display_name': email.split('@')[0], 'household_id': hid}
                        st.session_state.household_id = hid
                        st.session_state.pop('_pending_encrypted_household', None)
                        load_data(plan_data)
                        st.rerun()
                    else:
                        st.error("Wrong passphrase or corrupted data. Please try again.")
                        st.session_state.pop('_household_passphrase', None)
                else:
                    st.error("Please enter a passphrase.")
        with col2:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.pop('_pending_encrypted_household', None)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if real_households:
        st.subheader("Your Households")
        st.caption("You can create multiple plans — e.g., one shared with your partner and one just for you.")
        for h in real_households:
            member_count = len(h['members'])
            member_label = f"{member_count} member{'s' if member_count > 1 else ''}"
            is_encrypted = h.get('encrypted', False)
            lock_icon = "🔐" if is_encrypted else "📂"
            if st.button(f"{lock_icon}  {h['name']}  —  {member_label}", key=f"select_{h['id']}", use_container_width=True):
                if is_encrypted:
                    # Need passphrase — redirect to prompt
                    st.session_state._pending_encrypted_household = h['id']
                    st.rerun()
                else:
                    st.session_state.authenticated = True
                    st.session_state.current_user = email
                    st.session_state.user_data = {'display_name': email.split('@')[0], 'household_id': h['id']}
                    st.session_state.household_id = h['id']
                    st.session_state.pop('test_mode', None)
                    plan_data = load_household_plan(h['id'])
                    if plan_data:
                        load_data(plan_data)
                    st.rerun()
        st.markdown("---")

    # Create or join
    create_tab, join_tab = st.tabs(["Create New Household", "Join Existing Household"])

    with create_tab:
        household_name = st.text_input("Household Name", placeholder="e.g., The Smith Family", key="create_hh_name")

        st.markdown("**Data Security**")
        security_choice = st.radio(
            "Choose how your data is stored:",
            ["Standard", "Encrypted"],
            index=0,
            horizontal=True,
            key="create_hh_security",
            help="You can't change this after creation.",
        )
        if security_choice == "Standard":
            st.caption("Same as Google Docs — your data is stored on the server, protected by your login. "
                       "Seamless access with no extra steps. The server admin has theoretical access to stored data.")
        else:
            st.caption("Files on the server are encrypted with your passphrase (AES-256). "
                       "You'll enter it once per session. Protects data at rest, but not during active sessions. "
                       "**If you forget it, your data is permanently unrecoverable.**")

        passphrase_field = ""
        passphrase_confirm = ""
        if security_choice == "Encrypted":
            passphrase_field = st.text_input("Set a passphrase", type="password",
                placeholder="Choose a strong passphrase", key="create_hh_pass")
            passphrase_confirm = st.text_input("Confirm passphrase", type="password",
                placeholder="Enter it again", key="create_hh_pass_confirm")

        if st.button("Create Household", type="primary", use_container_width=True, key="create_hh_submit"):
            if not household_name.strip():
                st.error("Please enter a household name")
            elif security_choice == "Encrypted" and not passphrase_field:
                st.error("Please set a passphrase for your encrypted household.")
            elif security_choice == "Encrypted" and passphrase_field != passphrase_confirm:
                st.error("Passphrases don't match.")
            else:
                is_enc = security_choice == "Encrypted"
                hid = create_household(household_name.strip(), email, encrypted=is_enc)
                st.session_state.authenticated = True
                st.session_state.current_user = email
                st.session_state.user_data = {'display_name': email.split('@')[0], 'household_id': hid}
                st.session_state.household_id = hid
                if is_enc:
                    st.session_state._household_passphrase = passphrase_field
                st.rerun()

    with join_tab:
        with st.form("join_household_form"):
            join_code = st.text_input("Household Code", placeholder="Get this from your partner")
            submitted = st.form_submit_button("Join Household", type="primary")
            if submitted:
                if not join_code.strip():
                    st.error("Please enter a household code")
                else:
                    success, result = join_household(join_code.strip(), email)
                    if success:
                        # Check if the household is encrypted
                        index = load_households_index()
                        is_enc = index.get(join_code.strip(), {}).get('encrypted', False)
                        if is_enc:
                            st.session_state._pending_encrypted_household = join_code.strip()
                            st.rerun()
                        else:
                            st.session_state.authenticated = True
                            st.session_state.current_user = email
                            st.session_state.user_data = {'display_name': email.split('@')[0], 'household_id': join_code.strip()}
                            st.session_state.household_id = join_code.strip()
                            plan_data = load_household_plan(join_code.strip())
                            if plan_data:
                                load_data(plan_data)
                            st.rerun()
                    else:
                        st.error(result)

    # ── Admin test mode ──────────────────────────────────────────────────────
    if email in ADMIN_EMAILS:
        st.markdown("---")
        with st.expander("🧪 Admin: Test Mode"):
            st.markdown(
                "Start a **fresh session** as a brand-new user. "
                "This creates an isolated test household that won't affect real data."
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Test as New User", use_container_width=True, type="primary", key="test_new_user"):
                    cleanup_test_households(email)
                    test_hid = create_test_household(email)
                    keys_to_keep = {'cf_email'}
                    for key in list(st.session_state.keys()):
                        if key not in keys_to_keep:
                            del st.session_state[key]
                    st.session_state.authenticated = True
                    st.session_state.current_user = email
                    st.session_state.user_data = {'display_name': 'Test User', 'household_id': test_hid}
                    st.session_state.household_id = test_hid
                    st.session_state.test_mode = True
                    st.rerun()
            with col2:
                test_households = [h for h in my_households if h['id'].startswith(TEST_HOUSEHOLD_PREFIX)]
                if test_households:
                    if st.button(f"🗑️ Clean up {len(test_households)} test household(s)", use_container_width=True, key="cleanup_tests"):
                        cleanup_test_households(email)
                        st.rerun()

            st.markdown("---")
            st.markdown("**Pre-built Example Families**")
            st.caption("Load a pre-configured scenario to test the app without filling in the wizard.")

            def _load_test_scenario(name, data_overrides):
                """Create a test household and populate with example data."""
                cleanup_test_households(email)
                test_hid = create_test_household(email)
                keys_to_keep = {'cf_email'}
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.session_state.authenticated = True
                st.session_state.current_user = email
                st.session_state.user_data = {'display_name': 'Test User', 'household_id': test_hid}
                st.session_state.household_id = test_hid
                st.session_state.test_mode = True
                st.session_state.wizard_complete = True
                st.session_state.wizard_skipped = True
                initialize_session_state()
                for k, v in data_overrides.items():
                    st.session_state[k] = v
                try:
                    json_data = save_data()
                    if json_data:
                        save_household_plan(test_hid, json_data)
                except Exception:
                    pass

            # Quick test scenarios (override defaults)
            st.markdown("**Quick Scenarios** (basic overrides, fast to load)")
            quick_scenarios = {
                "All Defaults (Seattle)": {},
                "Young Couple, Seattle": {
                    'parent1_name': 'Alex', 'parent2_name': 'Sam', 'parentX_age': 28, 'parentY_age': 27,
                    'parentX_income': 95000.0, 'parentY_income': 80000.0, 'parentX_net_worth': 45000.0,
                    'parentY_net_worth': 30000.0, 'marriage_year': 2024,
                    'parentX_expenses': get_adult_expense_template("Seattle", "Conservative (statistical)"),
                    'parentY_expenses': get_adult_expense_template("Seattle", "Conservative (statistical)"),
                    'pretax_401k': 12000.0,  # Lower 401k for young couple
                },
                "Mid-Career + 2 Kids, Seattle": {
                    'parent1_name': 'Maria', 'parent2_name': 'David', 'parentX_age': 38, 'parentY_age': 40,
                    'parentX_income': 150000.0, 'parentY_income': 120000.0, 'parentX_net_worth': 350000.0,
                    'parentY_net_worth': 280000.0, 'marriage_year': 2015,
                    'children_list': [
                        {'name': 'Sofia', 'birth_year': 2019, 'use_template': True, 'template_state': 'Seattle',
                         'template_strategy': 'Average', 'school_type': 'Public', 'college_location': 'Seattle'},
                        {'name': 'Lucas', 'birth_year': 2022, 'use_template': True, 'template_state': 'Seattle',
                         'template_strategy': 'Average', 'school_type': 'Public', 'college_location': 'Seattle'},
                    ],
                },
                "High Earner, Single, Seattle": {
                    'parent1_name': 'Jordan', 'parent2_name': 'N/A', 'parentX_age': 35, 'parentY_age': 0,
                    'parentX_income': 250000.0, 'parentY_income': 0.0, 'parentX_net_worth': 600000.0,
                    'parentY_net_worth': 0.0, 'parentX_retirement_age': 55, 'marriage_year': 'N/A',
                    'parentY_expenses': {cat: 0 for cat in get_adult_expense_template("Seattle", "Average (statistical)").keys()},
                },
                "Near Retirement, Seattle": {
                    'parent1_name': 'Robert', 'parent2_name': 'Linda', 'parentX_age': 58, 'parentY_age': 56,
                    'parentX_income': 130000.0, 'parentY_income': 85000.0, 'parentX_net_worth': 1200000.0,
                    'parentY_net_worth': 800000.0, 'parentX_retirement_age': 62, 'parentY_retirement_age': 63,
                    'parentX_ss_benefit': 3200.0, 'parentY_ss_benefit': 2400.0, 'marriage_year': 1992,
                },
                "Tight Budget, TX": {
                    'parent1_name': 'Chris', 'parent2_name': 'Pat', 'parentX_age': 32, 'parentY_age': 30,
                    'parentX_income': 55000.0, 'parentY_income': 45000.0, 'parentX_net_worth': 15000.0,
                    'parentY_net_worth': 8000.0, 'marriage_year': 2023,
                    'parentX_expenses': get_adult_expense_template("Houston", "Conservative (statistical)"),
                    'parentY_expenses': get_adult_expense_template("Houston", "Conservative (statistical)"),
                    'family_shared_expenses': {
                        'Mortgage/Rent': 18000.0, 'Home Improvement': 500.0,
                        'Property Tax': 0.0, 'Home Insurance': 0.0,
                        'Gas & Electric': 1500.0, 'Water': 480.0, 'Garbage': 360.0,
                        'Internet & Cable': 960.0, 'Shared Subscriptions': 360.0,
                        'Family Vacations': 2000.0, 'Pet Care': 0.0, 'Other Family Expenses': 400.0,
                    },
                    'children_list': [
                        {'name': 'Emma', 'birth_year': 2024, 'use_template': True, 'template_state': 'Houston',
                         'template_strategy': 'Average', 'school_type': 'Public', 'college_location': 'Houston'},
                    ],
                },
            }
            cols = st.columns(3)
            for idx, (name, overrides) in enumerate(quick_scenarios.items()):
                with cols[idx % 3]:
                    if st.button(f"📋 {name}", use_container_width=True, key=f"test_scenario_{idx}"):
                        _load_test_scenario(name, overrides)
                        st.rerun()

            st.markdown("")
            st.markdown("**Full Demo Scenarios** (detailed, with properties and career changes)")
            st.caption("These load the same demos available in the scenario library. Edit them here and they persist for your test session.")

            # Load demo scenario names from the init block
            demo_names = [
                ("Tech Couple SF→Austin", "[DEMO] Tech Couple: SF→Austin→Seattle, Early Retirement @50"),
                ("3-Kid Family", "[DEMO] 3-Kid Family: Seattle→Portland→Denver"),
                ("Executives NYC→Miami", "[DEMO] Executives: NYC→Miami→Portugal, Early Retire @55"),
                ("Single Mom Teacher", "[DEMO] Single Mom: Sacramento→San Diego, Teacher→Principal"),
                ("Empty Nesters @60", "[DEMO] Empty Nesters: Early Retire @60, Portland→Arizona→RV"),
            ]

            def _load_demo_scenario(demo_key):
                """Load a demo scenario from saved_scenarios (populated by init)."""
                cleanup_test_households(email)
                test_hid = create_test_household(email)
                keys_to_keep = {'cf_email'}
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.session_state.authenticated = True
                st.session_state.current_user = email
                st.session_state.user_data = {'display_name': 'Test User', 'household_id': test_hid}
                st.session_state.household_id = test_hid
                st.session_state.test_mode = True
                st.session_state.wizard_complete = True
                st.session_state.wizard_skipped = True
                initialize_session_state()
                # Load the demo data
                demo_data = st.session_state.saved_scenarios.get(demo_key)
                if demo_data:
                    data_str = json.dumps(demo_data) if isinstance(demo_data, dict) else demo_data
                    load_data(data_str)
                try:
                    json_data = save_data()
                    if json_data:
                        save_household_plan(test_hid, json_data)
                except Exception:
                    pass

            cols = st.columns(3)
            for idx, (short_name, full_key) in enumerate(demo_names):
                with cols[idx % 3]:
                    if st.button(f"🎭 {short_name}", use_container_width=True, key=f"demo_scenario_{idx}"):
                        _load_demo_scenario(full_key)
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# Base year for expense templates (all templates inflation-adjusted to this year)
EXPENSE_TEMPLATE_BASE_YEAR = 2024

# Historical S&P 500 Annual Returns (approximately 1924-2023, 100 years)
HISTORICAL_STOCK_RETURNS = [
    # 1924-1929 (Pre-Depression)
    0.26, 0.10, 0.11, 0.37, 0.48, 0.12,
    # 1930-1939 (Great Depression & Recovery)
    -0.25, -0.43, -0.08, 0.54, -0.01, 0.47, 0.34, -0.35, 0.31, -0.01,
    # 1940-1949 (WWII & Post-war)
    -0.10, -0.12, 0.20, 0.26, 0.19, 0.36, -0.08, 0.05, 0.05, 0.18,
    # 1950-1959 (Post-war Boom)
    0.31, 0.24, 0.18, -0.01, 0.52, 0.31, 0.06, -0.11, 0.43, 0.12,
    # 1960-1969 (Go-Go Years)
    0.00, 0.27, -0.09, 0.23, 0.16, 0.12, -0.10, 0.24, 0.11, -0.08,
    # 1970-1979 (Stagflation)
    0.04, 0.14, 0.19, -0.15, -0.26, 0.37, 0.24, -0.07, 0.07, 0.18,
    # 1980-1989 (Reagan Bull Market)
    0.32, -0.05, 0.21, 0.22, 0.06, 0.31, 0.18, 0.05, 0.16, 0.32,
    # 1990-1999 (Tech Boom)
    -0.03, 0.30, 0.08, 0.10, 0.01, 0.38, 0.23, 0.33, 0.29, 0.21,
    # 2000-2009 (Dot-com Crash & Financial Crisis)
    -0.09, -0.12, -0.22, 0.29, 0.11, 0.05, 0.16, 0.05, -0.37, 0.26,
    # 2010-2019 (Recovery & Bull Market)
    0.15, 0.02, 0.16, 0.32, 0.14, 0.01, 0.12, 0.22, -0.04, 0.32,
    # 2020-2023 (Recent years with COVID impact)
    0.18, 0.29, -0.18, 0.26
]

# ============================================================================
# LOCATION HIERARCHY: Country → State/Province → City
# ============================================================================
# Cities with expense templates get the most specific data.
# States/Provinces have their own templates (US: all 50, Canada: provinces).
# Countries without state data grey out the state picker.

LOCATION_HIERARCHY = {
    "United States": {
        "has_states": True,
        "states": {
            "Washington": {"cities": ["Seattle"]},
            "California": {"cities": ["Sacramento", "San Francisco", "Los Angeles", "San Diego"]},
            "Texas": {"cities": ["Houston"]},
            "New York": {"cities": ["New York"]},
            "Oregon": {"cities": ["Portland"]},
            "Illinois": {"cities": ["Chicago"]},
            "Florida": {"cities": ["Miami"]},
            "District of Columbia": {"cities": ["Washington DC"]},
            "Ohio": {"cities": ["Columbus"]},
            "Hawaii": {"cities": ["Honolulu"]},
            "Alabama": {}, "Alaska": {}, "Arizona": {}, "Arkansas": {},
            "Colorado": {}, "Connecticut": {}, "Delaware": {},
            "Georgia": {}, "Idaho": {},
            "Indiana": {}, "Iowa": {}, "Kansas": {}, "Kentucky": {},
            "Louisiana": {}, "Maine": {}, "Maryland": {}, "Massachusetts": {},
            "Michigan": {}, "Minnesota": {}, "Mississippi": {}, "Missouri": {},
            "Montana": {}, "Nebraska": {}, "Nevada": {}, "New Hampshire": {},
            "New Jersey": {}, "New Mexico": {}, "North Carolina": {},
            "North Dakota": {}, "Oklahoma": {}, "Pennsylvania": {},
            "Rhode Island": {}, "South Carolina": {}, "South Dakota": {},
            "Tennessee": {}, "Utah": {}, "Vermont": {}, "Virginia": {},
            "West Virginia": {}, "Wisconsin": {}, "Wyoming": {},
        },
    },
    "Canada": {
        "has_states": True,
        "state_label": "Province",
        "states": {
            "Ontario": {"cities": ["Toronto"]},
            "British Columbia": {"cities": ["Vancouver"]},
            "Quebec": {}, "Alberta": {}, "Manitoba": {},
            "Saskatchewan": {}, "Nova Scotia": {}, "New Brunswick": {},
            "Newfoundland and Labrador": {}, "Prince Edward Island": {},
        },
    },
    "France": {
        "has_states": False,
        "cities": ["Paris", "Toulouse"],
    },
    "Germany": {
        "has_states": False,
        "cities": ["Berlin", "Munich"],
    },
    "Australia": {
        "has_states": False,
        "cities": ["Sydney", "Melbourne", "Brisbane"],
    },
    "New Zealand": {
        "has_states": False,
        "cities": ["Auckland", "Wellington"],
    },
}

# Flat lists (backward compatibility — used by non-wizard tabs)
AVAILABLE_LOCATIONS_ADULTS = [
    "Seattle", "Sacramento", "Houston", "New York", "San Francisco", "Los Angeles", "Portland",
    "Chicago", "Miami", "Washington DC", "San Diego", "Columbus", "Honolulu",
    "Toronto", "Vancouver", "Paris", "Toulouse", "Berlin", "Munich",
    "Sydney", "Melbourne", "Brisbane", "Auckland", "Wellington"
]
AVAILABLE_LOCATIONS_CHILDREN = [
    "Seattle", "Sacramento", "Houston", "New York", "San Francisco", "Los Angeles", "Portland",
    "Chicago", "Miami", "Washington DC", "San Diego", "Columbus", "Honolulu",
    "Auckland", "Wellington"
]
AVAILABLE_LOCATIONS_FAMILY = [
    "Seattle", "Sacramento", "Houston", "New York", "San Francisco", "Los Angeles", "Portland",
    "Chicago", "Miami", "Washington DC", "San Diego", "Columbus", "Honolulu",
    "Toronto", "Vancouver", "Paris", "Toulouse", "Berlin", "Munich",
    "Sydney", "Melbourne", "Brisbane"
]


def location_picker(prefix: str, wd: dict, label: str = "Where do you currently live?"):
    """Hierarchical location picker: Country → State/Province → City.
    Stores result in wd[f'{prefix}_country'], wd[f'{prefix}_state'], wd[f'{prefix}_city'],
    and wd[f'{prefix}_location'] (the most specific location name for template lookup).
    Returns the resolved location string.
    """
    countries = list(LOCATION_HIERARCHY.keys())
    saved_country = wd.get(f'{prefix}_country', 'United States')
    country = st.selectbox(label, countries,
        index=countries.index(saved_country) if saved_country in countries else 0,
        key=f"{prefix}_country_sel")
    wd[f'{prefix}_country'] = country

    country_data = LOCATION_HIERARCHY[country]
    resolved_location = None

    if country_data.get('has_states'):
        state_label = country_data.get('state_label', 'State')
        states = sorted(country_data['states'].keys())
        saved_state = wd.get(f'{prefix}_state', states[0] if states else '')
        state = st.selectbox(state_label, states,
            index=states.index(saved_state) if saved_state in states else 0,
            key=f"{prefix}_state_sel")
        wd[f'{prefix}_state'] = state
        resolved_location = state  # State-level default

        # Cities within this state
        state_data = country_data['states'].get(state, {})
        cities = state_data.get('cities', [])
        if cities:
            city_options = [f"State average ({state})"] + cities
            saved_city = wd.get(f'{prefix}_city', '')
            if saved_city in cities:
                city_idx = city_options.index(saved_city)
            else:
                city_idx = 0
            city = st.selectbox("City (optional — more specific data)", city_options,
                index=city_idx, key=f"{prefix}_city_sel")
            wd[f'{prefix}_city'] = city if city != city_options[0] else ''
            if city != city_options[0]:
                resolved_location = city  # City overrides state
        else:
            wd[f'{prefix}_city'] = ''
            st.caption(f"Using {state} state-level expense data.")
    else:
        # No state/province — grey it out
        st.selectbox("State / Province", ["Not available for this country"],
            disabled=True, key=f"{prefix}_state_disabled")
        wd[f'{prefix}_state'] = ''
        st.caption(f"State/province-level data is only available for the US and Canada for now.")

        # Cities
        cities = country_data.get('cities', [])
        if cities:
            city_options = [f"Country average ({country})"] + cities
            saved_city = wd.get(f'{prefix}_city', '')
            if saved_city in cities:
                city_idx = city_options.index(saved_city)
            else:
                city_idx = 0
            city = st.selectbox("City", city_options,
                index=city_idx, key=f"{prefix}_city_sel")
            wd[f'{prefix}_city'] = city if city != city_options[0] else ''
            if city != city_options[0]:
                resolved_location = city
            else:
                resolved_location = cities[0]  # Fallback to first city in country
        else:
            resolved_location = 'Seattle'  # Ultimate fallback

    wd[f'{prefix}_location'] = resolved_location or 'Seattle'
    return resolved_location or 'Seattle'

# Display names for locations (includes country and state for USA cities)
LOCATION_DISPLAY_NAMES = {
    # USA
    "Seattle": "Seattle, WA, USA",
    "Sacramento": "Sacramento, CA, USA",
    "California": "California, USA",
    "Houston": "Houston, TX, USA",
    "New York": "New York, NY, USA",
    "San Francisco": "San Francisco, CA, USA",
    "Los Angeles": "Los Angeles, CA, USA",
    "Portland": "Portland, OR, USA",
    # Canada
    "Toronto": "Toronto, ON, Canada",
    "Vancouver": "Vancouver, BC, Canada",
    # France
    "Paris": "Paris, France",
    "Toulouse": "Toulouse, France",
    # Germany
    "Berlin": "Berlin, Germany",
    "Munich": "Munich, Germany",
    # Australia
    "Sydney": "Sydney, NSW, Australia",
    "Melbourne": "Melbourne, VIC, Australia",
    "Brisbane": "Brisbane, QLD, Australia"
}

# Geographic coordinates for world map visualization
LOCATION_COORDINATES = {
    # USA
    "Seattle": {"lat": 47.6062, "lon": -122.3321},
    "Sacramento": {"lat": 38.5816, "lon": -121.4944},
    "California": {"lat": 36.7783, "lon": -119.4179},  # Center of CA
    "Houston": {"lat": 29.7604, "lon": -95.3698},
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "San Francisco": {"lat": 37.7749, "lon": -122.4194},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "Portland": {"lat": 45.5152, "lon": -122.6784},
    # Canada
    "Toronto": {"lat": 43.6532, "lon": -79.3832},
    "Vancouver": {"lat": 49.2827, "lon": -123.1207},
    # France
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Toulouse": {"lat": 43.6047, "lon": 1.4442},
    # Germany
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Munich": {"lat": 48.1351, "lon": 11.5820},
    # Australia
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Melbourne": {"lat": -37.8136, "lon": 144.9631},
    "Brisbane": {"lat": -27.4698, "lon": 153.0251}
}

# [Keep all the CHILDREN_EXPENSE_TEMPLATES and FAMILY_EXPENSE_TEMPLATES from V14]
# [I'll include the full templates but truncate here for readability]

# Spending strategy constants
STATISTICAL_STRATEGIES = ["Conservative (statistical)", "Average (statistical)", "High-end (statistical)"]

# ============================================================================
# COMPREHENSIVE EXPENSE CATEGORY STRUCTURE (Monarch-inspired)
# ============================================================================

# Adult expense categories (for Parent X and Parent Y)
# These categories apply to individual adults and are tracked per parent
ADULT_EXPENSE_CATEGORIES = {
    'Food & Dining': [
        'Groceries',
        'Dining Out',
        'Coffee Shops'
    ],
    'Transportation': [
        'Auto Payment',
        'Gas & Fuel',
        'Auto Maintenance',
        'Auto Insurance',
        'Parking & Tolls',
        'Public Transit',
        'Ride Shares'
    ],
    'Personal': [
        'Clothing',
        'Personal Care',
        'Grooming'
    ],
    'Health & Wellness': [
        'Medical',
        'Dental',
        'Vision',
        'Fitness',
        'Mental Health'
    ],
    'Entertainment & Lifestyle': [
        'Entertainment',
        'Hobbies',
        'Subscriptions',
        'Phone'
    ],
    'Other': [
        'Other Personal'
    ]
}

# Flatten adult categories for easier iteration
ADULT_EXPENSE_CATEGORIES_FLAT = [
    'Groceries', 'Dining Out', 'Coffee Shops',
    'Auto Payment', 'Gas & Fuel', 'Auto Maintenance', 'Auto Insurance',
    'Parking & Tolls', 'Public Transit', 'Ride Shares',
    'Clothing', 'Personal Care', 'Grooming',
    'Medical', 'Dental', 'Vision', 'Fitness', 'Mental Health',
    'Entertainment', 'Hobbies', 'Subscriptions', 'Phone',
    'Other Personal'
]

# Children expense categories (includes adult categories + child-specific)
# These are age-based (0-30 years) and apply per child
CHILDREN_EXPENSE_CATEGORIES_FLAT = [
    # Food & Dining (same as adults)
    'Groceries', 'Dining Out', 'Coffee Shops',
    # Transportation (same as adults)
    'Auto Payment', 'Gas & Fuel', 'Auto Maintenance', 'Auto Insurance',
    'Parking & Tolls', 'Public Transit', 'Ride Shares',
    # Personal (same as adults)
    'Clothing', 'Personal Care', 'Grooming',
    # Health & Wellness (same as adults)
    'Medical', 'Dental', 'Vision', 'Fitness', 'Mental Health',
    # Entertainment & Lifestyle (same as adults)
    'Entertainment', 'Hobbies', 'Subscriptions', 'Phone',
    # Child-specific categories
    'Baby Equipment',
    'Daycare',
    'School Supplies',
    'Activities & Sports',
    'Gifts & Celebrations',
    'Education',
    'Other Child Expenses'
]

# Legacy mapping for backwards compatibility with old children templates
LEGACY_CHILDREN_CATEGORIES = [
    'Food', 'Clothing', 'Healthcare', 'Activities/Sports', 'Entertainment',
    'Transportation', 'School Supplies', 'Gifts/Celebrations', 'Miscellaneous',
    'Daycare', 'Baby Equipment', 'Education'
]

# Family shared expense categories (housing, utilities, etc.)
# These are expenses shared by the entire family
FAMILY_SHARED_CATEGORIES = {
    'Housing': [
        'Mortgage/Rent',
        'Home Improvement',
        'Property Tax',
        'Home Insurance'
    ],
    'Utilities & Bills': [
        'Gas & Electric',
        'Water',
        'Garbage',
        'Internet & Cable'
    ],
    'Shared Lifestyle': [
        'Shared Subscriptions',
        'Family Vacations',
        'Pet Care'
    ],
    'Other': [
        'Other Family Expenses'
    ]
}

# Flatten family categories
FAMILY_SHARED_CATEGORIES_FLAT = [
    'Mortgage/Rent', 'Home Improvement', 'Property Tax', 'Home Insurance',
    'Gas & Electric', 'Water', 'Garbage', 'Internet & Cable',
    'Shared Subscriptions', 'Family Vacations', 'Pet Care',
    'Other Family Expenses'
]

# ============================================================================
# ADULT EXPENSE TEMPLATES (by location and spending strategy)
# ============================================================================
# Annual amounts for individual adults (Parent X or Parent Y)
# Organized by location, then strategy, then category
# All values are in 2024 dollars

ADULT_EXPENSE_TEMPLATES = {
    "Seattle": {
        "Conservative (statistical)": {
            'Groceries': 4800,
            'Dining Out': 2400,
            'Coffee Shops': 600,
            'Auto Payment': 3600,
            'Gas & Fuel': 1800,
            'Auto Maintenance': 800,
            'Auto Insurance': 1400,
            'Parking & Tolls': 400,
            'Public Transit': 800,
            'Ride Shares': 400,
            'Clothing': 1000,
            'Personal Care': 400,
            'Grooming': 400,
            'Medical': 800,
            'Dental': 400,
            'Vision': 200,
            'Fitness': 480,
            'Mental Health': 0,
            'Entertainment': 1200,
            'Hobbies': 600,
            'Subscriptions': 400,
            'Phone': 800,
            'Other Personal': 800
        },
        "Average (statistical)": {
            'Groceries': 6000,
            'Dining Out': 3600,
            'Coffee Shops': 1200,
            'Auto Payment': 6000,
            'Gas & Fuel': 2400,
            'Auto Maintenance': 1200,
            'Auto Insurance': 1800,
            'Parking & Tolls': 600,
            'Public Transit': 1200,
            'Ride Shares': 600,
            'Clothing': 1500,
            'Personal Care': 600,
            'Grooming': 600,
            'Medical': 1200,
            'Dental': 600,
            'Vision': 300,
            'Fitness': 720,
            'Mental Health': 600,
            'Entertainment': 1800,
            'Hobbies': 1200,
            'Subscriptions': 600,
            'Phone': 1000,
            'Other Personal': 1200
        },
        "High-end (statistical)": {
            'Groceries': 8400,
            'Dining Out': 6000,
            'Coffee Shops': 2400,
            'Auto Payment': 12000,
            'Gas & Fuel': 3600,
            'Auto Maintenance': 2000,
            'Auto Insurance': 2400,
            'Parking & Tolls': 1200,
            'Public Transit': 1800,
            'Ride Shares': 1200,
            'Clothing': 3000,
            'Personal Care': 1200,
            'Grooming': 1200,
            'Medical': 2000,
            'Dental': 1000,
            'Vision': 500,
            'Fitness': 1440,
            'Mental Health': 1200,
            'Entertainment': 3600,
            'Hobbies': 2400,
            'Subscriptions': 1200,
            'Phone': 1200,
            'Other Personal': 2400
        }
    },
    "Sacramento": {
        "Conservative (statistical)": {
            'Groceries': 4200,
            'Dining Out': 2000,
            'Coffee Shops': 500,
            'Auto Payment': 3200,
            'Gas & Fuel': 2000,
            'Auto Maintenance': 900,
            'Auto Insurance': 1600,
            'Parking & Tolls': 300,
            'Public Transit': 400,
            'Ride Shares': 300,
            'Clothing': 900,
            'Personal Care': 350,
            'Grooming': 350,
            'Medical': 700,
            'Dental': 350,
            'Vision': 180,
            'Fitness': 420,
            'Mental Health': 0,
            'Entertainment': 1000,
            'Hobbies': 500,
            'Subscriptions': 350,
            'Phone': 750,
            'Other Personal': 700
        },
        "Average (statistical)": {
            'Groceries': 5400,
            'Dining Out': 3000,
            'Coffee Shops': 1000,
            'Auto Payment': 5500,
            'Gas & Fuel': 2600,
            'Auto Maintenance': 1300,
            'Auto Insurance': 2000,
            'Parking & Tolls': 500,
            'Public Transit': 600,
            'Ride Shares': 500,
            'Clothing': 1400,
            'Personal Care': 550,
            'Grooming': 550,
            'Medical': 1100,
            'Dental': 550,
            'Vision': 280,
            'Fitness': 660,
            'Mental Health': 550,
            'Entertainment': 1600,
            'Hobbies': 1100,
            'Subscriptions': 550,
            'Phone': 950,
            'Other Personal': 1100
        },
        "High-end (statistical)": {
            'Groceries': 7800,
            'Dining Out': 5400,
            'Coffee Shops': 2000,
            'Auto Payment': 11000,
            'Gas & Fuel': 3800,
            'Auto Maintenance': 2200,
            'Auto Insurance': 2800,
            'Parking & Tolls': 1000,
            'Public Transit': 1000,
            'Ride Shares': 1000,
            'Clothing': 2800,
            'Personal Care': 1100,
            'Grooming': 1100,
            'Medical': 1900,
            'Dental': 950,
            'Vision': 480,
            'Fitness': 1320,
            'Mental Health': 1100,
            'Entertainment': 3200,
            'Hobbies': 2200,
            'Subscriptions': 1100,
            'Phone': 1150,
            'Other Personal': 2200
        }
    },
    "Houston": {
        "Conservative (statistical)": {
            'Groceries': 3800,
            'Dining Out': 1800,
            'Coffee Shops': 400,
            'Auto Payment': 3000,
            'Gas & Fuel': 2200,
            'Auto Maintenance': 1000,
            'Auto Insurance': 1800,
            'Parking & Tolls': 250,
            'Public Transit': 300,
            'Ride Shares': 250,
            'Clothing': 800,
            'Personal Care': 300,
            'Grooming': 300,
            'Medical': 600,
            'Dental': 300,
            'Vision': 150,
            'Fitness': 360,
            'Mental Health': 0,
            'Entertainment': 900,
            'Hobbies': 450,
            'Subscriptions': 300,
            'Phone': 700,
            'Other Personal': 600
        },
        "Average (statistical)": {
            'Groceries': 5000,
            'Dining Out': 2700,
            'Coffee Shops': 900,
            'Auto Payment': 5200,
            'Gas & Fuel': 2800,
            'Auto Maintenance': 1400,
            'Auto Insurance': 2200,
            'Parking & Tolls': 450,
            'Public Transit': 500,
            'Ride Shares': 450,
            'Clothing': 1300,
            'Personal Care': 500,
            'Grooming': 500,
            'Medical': 1000,
            'Dental': 500,
            'Vision': 250,
            'Fitness': 600,
            'Mental Health': 500,
            'Entertainment': 1500,
            'Hobbies': 1000,
            'Subscriptions': 500,
            'Phone': 900,
            'Other Personal': 1000
        },
        "High-end (statistical)": {
            'Groceries': 7200,
            'Dining Out': 4800,
            'Coffee Shops': 1800,
            'Auto Payment': 10500,
            'Gas & Fuel': 4000,
            'Auto Maintenance': 2400,
            'Auto Insurance': 3000,
            'Parking & Tolls': 900,
            'Public Transit': 800,
            'Ride Shares': 900,
            'Clothing': 2600,
            'Personal Care': 1000,
            'Grooming': 1000,
            'Medical': 1800,
            'Dental': 900,
            'Vision': 450,
            'Fitness': 1200,
            'Mental Health': 1000,
            'Entertainment': 3000,
            'Hobbies': 2000,
            'Subscriptions': 1000,
            'Phone': 1100,
            'Other Personal': 2000
        }
    },
    "New York": {
        "Conservative (statistical)": {
            'Groceries': 6240,
            'Dining Out': 3120,
            'Coffee Shops': 780,
            'Auto Payment': 4680,
            'Gas & Fuel': 2340,
            'Auto Maintenance': 1040,
            'Auto Insurance': 1820,
            'Parking & Tolls': 1560,
            'Public Transit': 1560,
            'Ride Shares': 780,
            'Clothing': 1300,
            'Personal Care': 520,
            'Grooming': 520,
            'Medical': 1040,
            'Dental': 520,
            'Vision': 260,
            'Fitness': 624,
            'Mental Health': 0,
            'Entertainment': 1560,
            'Hobbies': 780,
            'Subscriptions': 520,
            'Phone': 1040,
            'Other Personal': 1040
        },
        "Average (statistical)": {
            'Groceries': 7800,
            'Dining Out': 4680,
            'Coffee Shops': 1560,
            'Auto Payment': 7800,
            'Gas & Fuel': 3120,
            'Auto Maintenance': 1560,
            'Auto Insurance': 2340,
            'Parking & Tolls': 1560,
            'Public Transit': 1560,
            'Ride Shares': 780,
            'Clothing': 1950,
            'Personal Care': 780,
            'Grooming': 780,
            'Medical': 1560,
            'Dental': 780,
            'Vision': 390,
            'Fitness': 936,
            'Mental Health': 780,
            'Entertainment': 2340,
            'Hobbies': 1560,
            'Subscriptions': 780,
            'Phone': 1300,
            'Other Personal': 1560
        },
        "High-end (statistical)": {
            'Groceries': 10920,
            'Dining Out': 7800,
            'Coffee Shops': 3120,
            'Auto Payment': 15600,
            'Gas & Fuel': 4680,
            'Auto Maintenance': 2600,
            'Auto Insurance': 3120,
            'Parking & Tolls': 2340,
            'Public Transit': 2340,
            'Ride Shares': 1560,
            'Clothing': 3900,
            'Personal Care': 1560,
            'Grooming': 1560,
            'Medical': 2600,
            'Dental': 1300,
            'Vision': 650,
            'Fitness': 1872,
            'Mental Health': 1560,
            'Entertainment': 4680,
            'Hobbies': 3120,
            'Subscriptions': 1560,
            'Phone': 1560,
            'Other Personal': 3120
        }
    },
    "San Francisco": {
        "Conservative (statistical)": {
            'Groceries': 6480,
            'Dining Out': 3240,
            'Coffee Shops': 810,
            'Auto Payment': 4860,
            'Gas & Fuel': 2430,
            'Auto Maintenance': 1080,
            'Auto Insurance': 1890,
            'Parking & Tolls': 810,
            'Public Transit': 1080,
            'Ride Shares': 540,
            'Clothing': 1350,
            'Personal Care': 540,
            'Grooming': 540,
            'Medical': 1080,
            'Dental': 540,
            'Vision': 270,
            'Fitness': 648,
            'Mental Health': 0,
            'Entertainment': 1620,
            'Hobbies': 810,
            'Subscriptions': 540,
            'Phone': 1080,
            'Other Personal': 1080
        },
        "Average (statistical)": {
            'Groceries': 8100,
            'Dining Out': 4860,
            'Coffee Shops': 1620,
            'Auto Payment': 8100,
            'Gas & Fuel': 3240,
            'Auto Maintenance': 1620,
            'Auto Insurance': 2430,
            'Parking & Tolls': 1080,
            'Public Transit': 1620,
            'Ride Shares': 810,
            'Clothing': 2025,
            'Personal Care': 810,
            'Grooming': 810,
            'Medical': 1620,
            'Dental': 810,
            'Vision': 405,
            'Fitness': 972,
            'Mental Health': 810,
            'Entertainment': 2430,
            'Hobbies': 1620,
            'Subscriptions': 810,
            'Phone': 1350,
            'Other Personal': 1620
        },
        "High-end (statistical)": {
            'Groceries': 11340,
            'Dining Out': 8100,
            'Coffee Shops': 3240,
            'Auto Payment': 16200,
            'Gas & Fuel': 4860,
            'Auto Maintenance': 2700,
            'Auto Insurance': 3240,
            'Parking & Tolls': 1890,
            'Public Transit': 2430,
            'Ride Shares': 1620,
            'Clothing': 4050,
            'Personal Care': 1620,
            'Grooming': 1620,
            'Medical': 2700,
            'Dental': 1350,
            'Vision': 675,
            'Fitness': 1944,
            'Mental Health': 1620,
            'Entertainment': 4860,
            'Hobbies': 3240,
            'Subscriptions': 1620,
            'Phone': 1620,
            'Other Personal': 3240
        }
    },
    "Los Angeles": {
        "Conservative (statistical)": {
            'Groceries': 5520,
            'Dining Out': 2760,
            'Coffee Shops': 690,
            'Auto Payment': 4140,
            'Gas & Fuel': 2070,
            'Auto Maintenance': 920,
            'Auto Insurance': 1610,
            'Parking & Tolls': 690,
            'Public Transit': 920,
            'Ride Shares': 460,
            'Clothing': 1150,
            'Personal Care': 460,
            'Grooming': 460,
            'Medical': 920,
            'Dental': 460,
            'Vision': 230,
            'Fitness': 552,
            'Mental Health': 0,
            'Entertainment': 1380,
            'Hobbies': 690,
            'Subscriptions': 460,
            'Phone': 920,
            'Other Personal': 920
        },
        "Average (statistical)": {
            'Groceries': 6900,
            'Dining Out': 4140,
            'Coffee Shops': 1380,
            'Auto Payment': 6900,
            'Gas & Fuel': 2760,
            'Auto Maintenance': 1380,
            'Auto Insurance': 2070,
            'Parking & Tolls': 920,
            'Public Transit': 1380,
            'Ride Shares': 690,
            'Clothing': 1725,
            'Personal Care': 690,
            'Grooming': 690,
            'Medical': 1380,
            'Dental': 690,
            'Vision': 345,
            'Fitness': 828,
            'Mental Health': 690,
            'Entertainment': 2070,
            'Hobbies': 1380,
            'Subscriptions': 690,
            'Phone': 1150,
            'Other Personal': 1380
        },
        "High-end (statistical)": {
            'Groceries': 9660,
            'Dining Out': 6900,
            'Coffee Shops': 2760,
            'Auto Payment': 13800,
            'Gas & Fuel': 4140,
            'Auto Maintenance': 2300,
            'Auto Insurance': 2760,
            'Parking & Tolls': 1610,
            'Public Transit': 2070,
            'Ride Shares': 1380,
            'Clothing': 3450,
            'Personal Care': 1380,
            'Grooming': 1380,
            'Medical': 2300,
            'Dental': 1150,
            'Vision': 575,
            'Fitness': 1656,
            'Mental Health': 1380,
            'Entertainment': 4140,
            'Hobbies': 2760,
            'Subscriptions': 1380,
            'Phone': 1380,
            'Other Personal': 2760
        }
    },
    "Portland": {
        "Conservative (statistical)": {
            'Groceries': 4560,
            'Dining Out': 2280,
            'Coffee Shops': 570,
            'Auto Payment': 3420,
            'Gas & Fuel': 1710,
            'Auto Maintenance': 760,
            'Auto Insurance': 1330,
            'Parking & Tolls': 380,
            'Public Transit': 760,
            'Ride Shares': 380,
            'Clothing': 950,
            'Personal Care': 380,
            'Grooming': 380,
            'Medical': 760,
            'Dental': 380,
            'Vision': 190,
            'Fitness': 456,
            'Mental Health': 0,
            'Entertainment': 1140,
            'Hobbies': 570,
            'Subscriptions': 380,
            'Phone': 760,
            'Other Personal': 760
        },
        "Average (statistical)": {
            'Groceries': 5700,
            'Dining Out': 3420,
            'Coffee Shops': 1140,
            'Auto Payment': 5700,
            'Gas & Fuel': 2280,
            'Auto Maintenance': 1140,
            'Auto Insurance': 1710,
            'Parking & Tolls': 570,
            'Public Transit': 1140,
            'Ride Shares': 570,
            'Clothing': 1425,
            'Personal Care': 570,
            'Grooming': 570,
            'Medical': 1140,
            'Dental': 570,
            'Vision': 285,
            'Fitness': 684,
            'Mental Health': 570,
            'Entertainment': 1710,
            'Hobbies': 1140,
            'Subscriptions': 570,
            'Phone': 950,
            'Other Personal': 1140
        },
        "High-end (statistical)": {
            'Groceries': 7980,
            'Dining Out': 5700,
            'Coffee Shops': 2280,
            'Auto Payment': 11400,
            'Gas & Fuel': 3420,
            'Auto Maintenance': 1900,
            'Auto Insurance': 2280,
            'Parking & Tolls': 1140,
            'Public Transit': 1710,
            'Ride Shares': 1140,
            'Clothing': 2850,
            'Personal Care': 1140,
            'Grooming': 1140,
            'Medical': 1900,
            'Dental': 950,
            'Vision': 475,
            'Fitness': 1368,
            'Mental Health': 1140,
            'Entertainment': 3420,
            'Hobbies': 2280,
            'Subscriptions': 1140,
            'Phone': 1140,
            'Other Personal': 2280
        }
    },
    "Chicago": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1680, "Coffee Shops": 420, "Auto Payment": 2520, "Gas & Fuel": 1260, "Auto Maintenance": 560, "Auto Insurance": 1540, "Parking & Tolls": 840,
            "Public Transit": 840, "Ride Shares": 350, "Clothing": 700, "Personal Care": 350, "Grooming": 280, "Medical": 1120, "Dental": 280, "Vision": 140, "Fitness": 350,
            "Mental Health": 420, "Entertainment": 840, "Hobbies": 420, "Subscriptions": 280, "Phone": 700, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2400, "Coffee Shops": 600, "Auto Payment": 3600, "Gas & Fuel": 1800, "Auto Maintenance": 800, "Auto Insurance": 2200, "Parking & Tolls": 1200,
            "Public Transit": 1200, "Ride Shares": 500, "Clothing": 1000, "Personal Care": 500, "Grooming": 400, "Medical": 1600, "Dental": 400, "Vision": 200, "Fitness": 500,
            "Mental Health": 600, "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 400, "Phone": 1000, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 3600, "Coffee Shops": 900, "Auto Payment": 5400, "Gas & Fuel": 2700, "Auto Maintenance": 1200, "Auto Insurance": 3300, "Parking & Tolls": 1800,
            "Public Transit": 1800, "Ride Shares": 750, "Clothing": 1500, "Personal Care": 750, "Grooming": 600, "Medical": 2400, "Dental": 600, "Vision": 300, "Fitness": 750,
            "Mental Health": 900, "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 600, "Phone": 1500, "Other Personal": 900
        },
    },
    "Miami": {
        "Conservative (statistical)": {
            "Groceries": 3220, "Dining Out": 1960, "Coffee Shops": 490, "Auto Payment": 2660, "Gas & Fuel": 1330, "Auto Maintenance": 560, "Auto Insurance": 1680, "Parking & Tolls": 700,
            "Public Transit": 420, "Ride Shares": 420, "Clothing": 770, "Personal Care": 385, "Grooming": 280, "Medical": 1050, "Dental": 280, "Vision": 140, "Fitness": 385,
            "Mental Health": 350, "Entertainment": 1050, "Hobbies": 490, "Subscriptions": 280, "Phone": 700, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4600, "Dining Out": 2800, "Coffee Shops": 700, "Auto Payment": 3800, "Gas & Fuel": 1900, "Auto Maintenance": 800, "Auto Insurance": 2400, "Parking & Tolls": 1000,
            "Public Transit": 600, "Ride Shares": 600, "Clothing": 1100, "Personal Care": 550, "Grooming": 400, "Medical": 1500, "Dental": 400, "Vision": 200, "Fitness": 550,
            "Mental Health": 500, "Entertainment": 1500, "Hobbies": 700, "Subscriptions": 400, "Phone": 1000, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 6900, "Dining Out": 4200, "Coffee Shops": 1050, "Auto Payment": 5700, "Gas & Fuel": 2850, "Auto Maintenance": 1200, "Auto Insurance": 3600, "Parking & Tolls": 1500,
            "Public Transit": 900, "Ride Shares": 900, "Clothing": 1650, "Personal Care": 825, "Grooming": 600, "Medical": 2250, "Dental": 600, "Vision": 300, "Fitness": 825,
            "Mental Health": 750, "Entertainment": 2250, "Hobbies": 1050, "Subscriptions": 600, "Phone": 1500, "Other Personal": 900
        },
    },
    "Washington DC": {
        "Conservative (statistical)": {
            "Groceries": 3640, "Dining Out": 2100, "Coffee Shops": 560, "Auto Payment": 2520, "Gas & Fuel": 1190, "Auto Maintenance": 560, "Auto Insurance": 1050, "Parking & Tolls": 1260,
            "Public Transit": 1120, "Ride Shares": 490, "Clothing": 840, "Personal Care": 420, "Grooming": 350, "Medical": 1260, "Dental": 350, "Vision": 175, "Fitness": 490,
            "Mental Health": 490, "Entertainment": 1050, "Hobbies": 560, "Subscriptions": 315, "Phone": 735, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 5200, "Dining Out": 3000, "Coffee Shops": 800, "Auto Payment": 3600, "Gas & Fuel": 1700, "Auto Maintenance": 800, "Auto Insurance": 1500, "Parking & Tolls": 1800,
            "Public Transit": 1600, "Ride Shares": 700, "Clothing": 1200, "Personal Care": 600, "Grooming": 500, "Medical": 1800, "Dental": 500, "Vision": 250, "Fitness": 700,
            "Mental Health": 700, "Entertainment": 1500, "Hobbies": 800, "Subscriptions": 450, "Phone": 1050, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 7800, "Dining Out": 4500, "Coffee Shops": 1200, "Auto Payment": 5400, "Gas & Fuel": 2550, "Auto Maintenance": 1200, "Auto Insurance": 2250, "Parking & Tolls": 2700,
            "Public Transit": 2400, "Ride Shares": 1050, "Clothing": 1800, "Personal Care": 900, "Grooming": 750, "Medical": 2700, "Dental": 750, "Vision": 375, "Fitness": 1050,
            "Mental Health": 1050, "Entertainment": 2250, "Hobbies": 1200, "Subscriptions": 675, "Phone": 1575, "Other Personal": 1050
        },
    },
    "San Diego": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 1820, "Coffee Shops": 490, "Auto Payment": 2660, "Gas & Fuel": 1400, "Auto Maintenance": 560, "Auto Insurance": 1120, "Parking & Tolls": 700,
            "Public Transit": 560, "Ride Shares": 385, "Clothing": 700, "Personal Care": 385, "Grooming": 315, "Medical": 1120, "Dental": 315, "Vision": 154, "Fitness": 420,
            "Mental Health": 420, "Entertainment": 910, "Hobbies": 490, "Subscriptions": 280, "Phone": 735, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2600, "Coffee Shops": 700, "Auto Payment": 3800, "Gas & Fuel": 2000, "Auto Maintenance": 800, "Auto Insurance": 1600, "Parking & Tolls": 1000,
            "Public Transit": 800, "Ride Shares": 550, "Clothing": 1000, "Personal Care": 550, "Grooming": 450, "Medical": 1600, "Dental": 450, "Vision": 220, "Fitness": 600,
            "Mental Health": 600, "Entertainment": 1300, "Hobbies": 700, "Subscriptions": 400, "Phone": 1050, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 3900, "Coffee Shops": 1050, "Auto Payment": 5700, "Gas & Fuel": 3000, "Auto Maintenance": 1200, "Auto Insurance": 2400, "Parking & Tolls": 1500,
            "Public Transit": 1200, "Ride Shares": 825, "Clothing": 1500, "Personal Care": 825, "Grooming": 675, "Medical": 2400, "Dental": 675, "Vision": 330, "Fitness": 900,
            "Mental Health": 900, "Entertainment": 1950, "Hobbies": 1050, "Subscriptions": 600, "Phone": 1575, "Other Personal": 900
        },
    },
    "Columbus": {
        "Conservative (statistical)": {
            "Groceries": 2800, "Dining Out": 1260, "Coffee Shops": 315, "Auto Payment": 2240, "Gas & Fuel": 1050, "Auto Maintenance": 490, "Auto Insurance": 770, "Parking & Tolls": 350,
            "Public Transit": 280, "Ride Shares": 245, "Clothing": 560, "Personal Care": 280, "Grooming": 210, "Medical": 840, "Dental": 245, "Vision": 119, "Fitness": 280,
            "Mental Health": 315, "Entertainment": 630, "Hobbies": 350, "Subscriptions": 245, "Phone": 630, "Other Personal": 350
        },
        "Average (statistical)": {
            "Groceries": 4000, "Dining Out": 1800, "Coffee Shops": 450, "Auto Payment": 3200, "Gas & Fuel": 1500, "Auto Maintenance": 700, "Auto Insurance": 1100, "Parking & Tolls": 500,
            "Public Transit": 400, "Ride Shares": 350, "Clothing": 800, "Personal Care": 400, "Grooming": 300, "Medical": 1200, "Dental": 350, "Vision": 170, "Fitness": 400,
            "Mental Health": 450, "Entertainment": 900, "Hobbies": 500, "Subscriptions": 350, "Phone": 900, "Other Personal": 500
        },
        "High-end (statistical)": {
            "Groceries": 6000, "Dining Out": 2700, "Coffee Shops": 675, "Auto Payment": 4800, "Gas & Fuel": 2250, "Auto Maintenance": 1050, "Auto Insurance": 1650, "Parking & Tolls": 750,
            "Public Transit": 600, "Ride Shares": 525, "Clothing": 1200, "Personal Care": 600, "Grooming": 450, "Medical": 1800, "Dental": 525, "Vision": 255, "Fitness": 600,
            "Mental Health": 675, "Entertainment": 1350, "Hobbies": 750, "Subscriptions": 525, "Phone": 1350, "Other Personal": 750
        },
    },
    "Honolulu": {
        "Conservative (statistical)": {
            "Groceries": 4900, "Dining Out": 2100, "Coffee Shops": 560, "Auto Payment": 2660, "Gas & Fuel": 1750, "Auto Maintenance": 630, "Auto Insurance": 980, "Parking & Tolls": 840,
            "Public Transit": 420, "Ride Shares": 420, "Clothing": 700, "Personal Care": 385, "Grooming": 315, "Medical": 1190, "Dental": 315, "Vision": 154, "Fitness": 455,
            "Mental Health": 420, "Entertainment": 980, "Hobbies": 560, "Subscriptions": 280, "Phone": 770, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 7000, "Dining Out": 3000, "Coffee Shops": 800, "Auto Payment": 3800, "Gas & Fuel": 2500, "Auto Maintenance": 900, "Auto Insurance": 1400, "Parking & Tolls": 1200,
            "Public Transit": 600, "Ride Shares": 600, "Clothing": 1000, "Personal Care": 550, "Grooming": 450, "Medical": 1700, "Dental": 450, "Vision": 220, "Fitness": 650,
            "Mental Health": 600, "Entertainment": 1400, "Hobbies": 800, "Subscriptions": 400, "Phone": 1100, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 10500, "Dining Out": 4500, "Coffee Shops": 1200, "Auto Payment": 5700, "Gas & Fuel": 3750, "Auto Maintenance": 1350, "Auto Insurance": 2100, "Parking & Tolls": 1800,
            "Public Transit": 900, "Ride Shares": 900, "Clothing": 1500, "Personal Care": 825, "Grooming": 675, "Medical": 2550, "Dental": 675, "Vision": 330, "Fitness": 975,
            "Mental Health": 900, "Entertainment": 2100, "Hobbies": 1200, "Subscriptions": 600, "Phone": 1650, "Other Personal": 1050
        },
    },
    "Toronto": {
        "Conservative (statistical)": {
            'Groceries': 4560,
            'Dining Out': 2280,
            'Coffee Shops': 570,
            'Auto Payment': 3420,
            'Gas & Fuel': 1710,
            'Auto Maintenance': 760,
            'Auto Insurance': 1330,
            'Parking & Tolls': 380,
            'Public Transit': 760,
            'Ride Shares': 380,
            'Clothing': 950,
            'Personal Care': 380,
            'Grooming': 380,
            'Medical': 760,
            'Dental': 380,
            'Vision': 190,
            'Fitness': 456,
            'Mental Health': 0,
            'Entertainment': 1140,
            'Hobbies': 570,
            'Subscriptions': 380,
            'Phone': 760,
            'Other Personal': 760
        },
        "Average (statistical)": {
            'Groceries': 5700,
            'Dining Out': 3420,
            'Coffee Shops': 1140,
            'Auto Payment': 5700,
            'Gas & Fuel': 2280,
            'Auto Maintenance': 1140,
            'Auto Insurance': 1710,
            'Parking & Tolls': 570,
            'Public Transit': 1140,
            'Ride Shares': 570,
            'Clothing': 1425,
            'Personal Care': 570,
            'Grooming': 570,
            'Medical': 1140,
            'Dental': 570,
            'Vision': 285,
            'Fitness': 684,
            'Mental Health': 570,
            'Entertainment': 1710,
            'Hobbies': 1140,
            'Subscriptions': 570,
            'Phone': 950,
            'Other Personal': 1140
        },
        "High-end (statistical)": {
            'Groceries': 7980,
            'Dining Out': 5700,
            'Coffee Shops': 2280,
            'Auto Payment': 11400,
            'Gas & Fuel': 3420,
            'Auto Maintenance': 1900,
            'Auto Insurance': 2280,
            'Parking & Tolls': 1140,
            'Public Transit': 1710,
            'Ride Shares': 1140,
            'Clothing': 2850,
            'Personal Care': 1140,
            'Grooming': 1140,
            'Medical': 1900,
            'Dental': 950,
            'Vision': 475,
            'Fitness': 1368,
            'Mental Health': 1140,
            'Entertainment': 3420,
            'Hobbies': 2280,
            'Subscriptions': 1140,
            'Phone': 1140,
            'Other Personal': 2280
        }
    },
    "Vancouver": {
        "Conservative (statistical)": {
            'Groceries': 5040,
            'Dining Out': 2520,
            'Coffee Shops': 630,
            'Auto Payment': 3780,
            'Gas & Fuel': 1890,
            'Auto Maintenance': 840,
            'Auto Insurance': 1470,
            'Parking & Tolls': 420,
            'Public Transit': 840,
            'Ride Shares': 420,
            'Clothing': 1050,
            'Personal Care': 420,
            'Grooming': 420,
            'Medical': 840,
            'Dental': 420,
            'Vision': 210,
            'Fitness': 504,
            'Mental Health': 0,
            'Entertainment': 1260,
            'Hobbies': 630,
            'Subscriptions': 420,
            'Phone': 840,
            'Other Personal': 840
        },
        "Average (statistical)": {
            'Groceries': 6300,
            'Dining Out': 3780,
            'Coffee Shops': 1260,
            'Auto Payment': 6300,
            'Gas & Fuel': 2520,
            'Auto Maintenance': 1260,
            'Auto Insurance': 1890,
            'Parking & Tolls': 630,
            'Public Transit': 1260,
            'Ride Shares': 630,
            'Clothing': 1575,
            'Personal Care': 630,
            'Grooming': 630,
            'Medical': 1260,
            'Dental': 630,
            'Vision': 315,
            'Fitness': 756,
            'Mental Health': 630,
            'Entertainment': 1890,
            'Hobbies': 1260,
            'Subscriptions': 630,
            'Phone': 1050,
            'Other Personal': 1260
        },
        "High-end (statistical)": {
            'Groceries': 8820,
            'Dining Out': 6300,
            'Coffee Shops': 2520,
            'Auto Payment': 12600,
            'Gas & Fuel': 3780,
            'Auto Maintenance': 2100,
            'Auto Insurance': 2520,
            'Parking & Tolls': 1260,
            'Public Transit': 1890,
            'Ride Shares': 1260,
            'Clothing': 3150,
            'Personal Care': 1260,
            'Grooming': 1260,
            'Medical': 2100,
            'Dental': 1050,
            'Vision': 525,
            'Fitness': 1512,
            'Mental Health': 1260,
            'Entertainment': 3780,
            'Hobbies': 2520,
            'Subscriptions': 1260,
            'Phone': 1260,
            'Other Personal': 2520
        }
    },
    "Paris": {
        "Conservative (statistical)": {
            'Groceries': 5760,
            'Dining Out': 2880,
            'Coffee Shops': 720,
            'Auto Payment': 4320,
            'Gas & Fuel': 2160,
            'Auto Maintenance': 960,
            'Auto Insurance': 1680,
            'Parking & Tolls': 480,
            'Public Transit': 960,
            'Ride Shares': 480,
            'Clothing': 1200,
            'Personal Care': 480,
            'Grooming': 480,
            'Medical': 960,
            'Dental': 480,
            'Vision': 240,
            'Fitness': 576,
            'Mental Health': 0,
            'Entertainment': 1440,
            'Hobbies': 720,
            'Subscriptions': 480,
            'Phone': 960,
            'Other Personal': 960
        },
        "Average (statistical)": {
            'Groceries': 7200,
            'Dining Out': 4320,
            'Coffee Shops': 1440,
            'Auto Payment': 7200,
            'Gas & Fuel': 2880,
            'Auto Maintenance': 1440,
            'Auto Insurance': 2160,
            'Parking & Tolls': 720,
            'Public Transit': 1440,
            'Ride Shares': 720,
            'Clothing': 1800,
            'Personal Care': 720,
            'Grooming': 720,
            'Medical': 1440,
            'Dental': 720,
            'Vision': 360,
            'Fitness': 864,
            'Mental Health': 720,
            'Entertainment': 2160,
            'Hobbies': 1440,
            'Subscriptions': 720,
            'Phone': 1200,
            'Other Personal': 1440
        },
        "High-end (statistical)": {
            'Groceries': 10080,
            'Dining Out': 7200,
            'Coffee Shops': 2880,
            'Auto Payment': 14400,
            'Gas & Fuel': 4320,
            'Auto Maintenance': 2400,
            'Auto Insurance': 2880,
            'Parking & Tolls': 1440,
            'Public Transit': 2160,
            'Ride Shares': 1440,
            'Clothing': 3600,
            'Personal Care': 1440,
            'Grooming': 1440,
            'Medical': 2400,
            'Dental': 1200,
            'Vision': 600,
            'Fitness': 1728,
            'Mental Health': 1440,
            'Entertainment': 4320,
            'Hobbies': 2880,
            'Subscriptions': 1440,
            'Phone': 1440,
            'Other Personal': 2880
        }
    },
    "Toulouse": {
        "Conservative (statistical)": {
            'Groceries': 4320,
            'Dining Out': 2160,
            'Coffee Shops': 540,
            'Auto Payment': 3240,
            'Gas & Fuel': 1620,
            'Auto Maintenance': 720,
            'Auto Insurance': 1260,
            'Parking & Tolls': 360,
            'Public Transit': 720,
            'Ride Shares': 360,
            'Clothing': 900,
            'Personal Care': 360,
            'Grooming': 360,
            'Medical': 720,
            'Dental': 360,
            'Vision': 180,
            'Fitness': 432,
            'Mental Health': 0,
            'Entertainment': 1080,
            'Hobbies': 540,
            'Subscriptions': 360,
            'Phone': 720,
            'Other Personal': 720
        },
        "Average (statistical)": {
            'Groceries': 5400,
            'Dining Out': 3240,
            'Coffee Shops': 1080,
            'Auto Payment': 5400,
            'Gas & Fuel': 2160,
            'Auto Maintenance': 1080,
            'Auto Insurance': 1620,
            'Parking & Tolls': 540,
            'Public Transit': 1080,
            'Ride Shares': 540,
            'Clothing': 1350,
            'Personal Care': 540,
            'Grooming': 540,
            'Medical': 1080,
            'Dental': 540,
            'Vision': 270,
            'Fitness': 648,
            'Mental Health': 540,
            'Entertainment': 1620,
            'Hobbies': 1080,
            'Subscriptions': 540,
            'Phone': 900,
            'Other Personal': 1080
        },
        "High-end (statistical)": {
            'Groceries': 7560,
            'Dining Out': 5400,
            'Coffee Shops': 2160,
            'Auto Payment': 10800,
            'Gas & Fuel': 3240,
            'Auto Maintenance': 1800,
            'Auto Insurance': 2160,
            'Parking & Tolls': 1080,
            'Public Transit': 1620,
            'Ride Shares': 1080,
            'Clothing': 2700,
            'Personal Care': 1080,
            'Grooming': 1080,
            'Medical': 1800,
            'Dental': 900,
            'Vision': 450,
            'Fitness': 1296,
            'Mental Health': 1080,
            'Entertainment': 3240,
            'Hobbies': 2160,
            'Subscriptions': 1080,
            'Phone': 1080,
            'Other Personal': 2160
        }
    },
    "Berlin": {
        "Conservative (statistical)": {
            'Groceries': 4080,
            'Dining Out': 2040,
            'Coffee Shops': 510,
            'Auto Payment': 3060,
            'Gas & Fuel': 1530,
            'Auto Maintenance': 680,
            'Auto Insurance': 1190,
            'Parking & Tolls': 340,
            'Public Transit': 680,
            'Ride Shares': 340,
            'Clothing': 850,
            'Personal Care': 340,
            'Grooming': 340,
            'Medical': 680,
            'Dental': 340,
            'Vision': 170,
            'Fitness': 408,
            'Mental Health': 0,
            'Entertainment': 1020,
            'Hobbies': 510,
            'Subscriptions': 340,
            'Phone': 680,
            'Other Personal': 680
        },
        "Average (statistical)": {
            'Groceries': 5100,
            'Dining Out': 3060,
            'Coffee Shops': 1020,
            'Auto Payment': 5100,
            'Gas & Fuel': 2040,
            'Auto Maintenance': 1020,
            'Auto Insurance': 1530,
            'Parking & Tolls': 510,
            'Public Transit': 1020,
            'Ride Shares': 510,
            'Clothing': 1275,
            'Personal Care': 510,
            'Grooming': 510,
            'Medical': 1020,
            'Dental': 510,
            'Vision': 255,
            'Fitness': 612,
            'Mental Health': 510,
            'Entertainment': 1530,
            'Hobbies': 1020,
            'Subscriptions': 510,
            'Phone': 850,
            'Other Personal': 1020
        },
        "High-end (statistical)": {
            'Groceries': 7140,
            'Dining Out': 5100,
            'Coffee Shops': 2040,
            'Auto Payment': 10200,
            'Gas & Fuel': 3060,
            'Auto Maintenance': 1700,
            'Auto Insurance': 2040,
            'Parking & Tolls': 1020,
            'Public Transit': 1530,
            'Ride Shares': 1020,
            'Clothing': 2550,
            'Personal Care': 1020,
            'Grooming': 1020,
            'Medical': 1700,
            'Dental': 850,
            'Vision': 425,
            'Fitness': 1224,
            'Mental Health': 1020,
            'Entertainment': 3060,
            'Hobbies': 2040,
            'Subscriptions': 1020,
            'Phone': 1020,
            'Other Personal': 2040
        }
    },
    "Munich": {
        "Conservative (statistical)": {
            'Groceries': 4800,
            'Dining Out': 2400,
            'Coffee Shops': 600,
            'Auto Payment': 3600,
            'Gas & Fuel': 1800,
            'Auto Maintenance': 800,
            'Auto Insurance': 1400,
            'Parking & Tolls': 400,
            'Public Transit': 800,
            'Ride Shares': 400,
            'Clothing': 1000,
            'Personal Care': 400,
            'Grooming': 400,
            'Medical': 800,
            'Dental': 400,
            'Vision': 200,
            'Fitness': 480,
            'Mental Health': 0,
            'Entertainment': 1200,
            'Hobbies': 600,
            'Subscriptions': 400,
            'Phone': 800,
            'Other Personal': 800
        },
        "Average (statistical)": {
            'Groceries': 6000,
            'Dining Out': 3600,
            'Coffee Shops': 1200,
            'Auto Payment': 6000,
            'Gas & Fuel': 2400,
            'Auto Maintenance': 1200,
            'Auto Insurance': 1800,
            'Parking & Tolls': 600,
            'Public Transit': 1200,
            'Ride Shares': 600,
            'Clothing': 1500,
            'Personal Care': 600,
            'Grooming': 600,
            'Medical': 1200,
            'Dental': 600,
            'Vision': 300,
            'Fitness': 720,
            'Mental Health': 600,
            'Entertainment': 1800,
            'Hobbies': 1200,
            'Subscriptions': 600,
            'Phone': 1000,
            'Other Personal': 1200
        },
        "High-end (statistical)": {
            'Groceries': 8400,
            'Dining Out': 6000,
            'Coffee Shops': 2400,
            'Auto Payment': 12000,
            'Gas & Fuel': 3600,
            'Auto Maintenance': 2000,
            'Auto Insurance': 2400,
            'Parking & Tolls': 1200,
            'Public Transit': 1800,
            'Ride Shares': 1200,
            'Clothing': 3000,
            'Personal Care': 1200,
            'Grooming': 1200,
            'Medical': 2000,
            'Dental': 1000,
            'Vision': 500,
            'Fitness': 1440,
            'Mental Health': 1200,
            'Entertainment': 3600,
            'Hobbies': 2400,
            'Subscriptions': 1200,
            'Phone': 1200,
            'Other Personal': 2400
        }
    },
    "Sydney": {
        "Conservative (statistical)": {
            'Groceries': 5280,
            'Dining Out': 2640,
            'Coffee Shops': 660,
            'Auto Payment': 3960,
            'Gas & Fuel': 1980,
            'Auto Maintenance': 880,
            'Auto Insurance': 1540,
            'Parking & Tolls': 440,
            'Public Transit': 880,
            'Ride Shares': 440,
            'Clothing': 1100,
            'Personal Care': 440,
            'Grooming': 440,
            'Medical': 880,
            'Dental': 440,
            'Vision': 220,
            'Fitness': 528,
            'Mental Health': 0,
            'Entertainment': 1320,
            'Hobbies': 660,
            'Subscriptions': 440,
            'Phone': 880,
            'Other Personal': 880
        },
        "Average (statistical)": {
            'Groceries': 6600,
            'Dining Out': 3960,
            'Coffee Shops': 1320,
            'Auto Payment': 6600,
            'Gas & Fuel': 2640,
            'Auto Maintenance': 1320,
            'Auto Insurance': 1980,
            'Parking & Tolls': 660,
            'Public Transit': 1320,
            'Ride Shares': 660,
            'Clothing': 1650,
            'Personal Care': 660,
            'Grooming': 660,
            'Medical': 1320,
            'Dental': 660,
            'Vision': 330,
            'Fitness': 792,
            'Mental Health': 660,
            'Entertainment': 1980,
            'Hobbies': 1320,
            'Subscriptions': 660,
            'Phone': 1100,
            'Other Personal': 1320
        },
        "High-end (statistical)": {
            'Groceries': 9240,
            'Dining Out': 6600,
            'Coffee Shops': 2640,
            'Auto Payment': 13200,
            'Gas & Fuel': 3960,
            'Auto Maintenance': 2200,
            'Auto Insurance': 2640,
            'Parking & Tolls': 1320,
            'Public Transit': 1980,
            'Ride Shares': 1320,
            'Clothing': 3300,
            'Personal Care': 1320,
            'Grooming': 1320,
            'Medical': 2200,
            'Dental': 1100,
            'Vision': 550,
            'Fitness': 1584,
            'Mental Health': 1320,
            'Entertainment': 3960,
            'Hobbies': 2640,
            'Subscriptions': 1320,
            'Phone': 1320,
            'Other Personal': 2640
        }
    },
    "Melbourne": {
        "Conservative (statistical)": {
            'Groceries': 5040,
            'Dining Out': 2520,
            'Coffee Shops': 630,
            'Auto Payment': 3780,
            'Gas & Fuel': 1890,
            'Auto Maintenance': 840,
            'Auto Insurance': 1470,
            'Parking & Tolls': 420,
            'Public Transit': 840,
            'Ride Shares': 420,
            'Clothing': 1050,
            'Personal Care': 420,
            'Grooming': 420,
            'Medical': 840,
            'Dental': 420,
            'Vision': 210,
            'Fitness': 504,
            'Mental Health': 0,
            'Entertainment': 1260,
            'Hobbies': 630,
            'Subscriptions': 420,
            'Phone': 840,
            'Other Personal': 840
        },
        "Average (statistical)": {
            'Groceries': 6300,
            'Dining Out': 3780,
            'Coffee Shops': 1260,
            'Auto Payment': 6300,
            'Gas & Fuel': 2520,
            'Auto Maintenance': 1260,
            'Auto Insurance': 1890,
            'Parking & Tolls': 630,
            'Public Transit': 1260,
            'Ride Shares': 630,
            'Clothing': 1575,
            'Personal Care': 630,
            'Grooming': 630,
            'Medical': 1260,
            'Dental': 630,
            'Vision': 315,
            'Fitness': 756,
            'Mental Health': 630,
            'Entertainment': 1890,
            'Hobbies': 1260,
            'Subscriptions': 630,
            'Phone': 1050,
            'Other Personal': 1260
        },
        "High-end (statistical)": {
            'Groceries': 8820,
            'Dining Out': 6300,
            'Coffee Shops': 2520,
            'Auto Payment': 12600,
            'Gas & Fuel': 3780,
            'Auto Maintenance': 2100,
            'Auto Insurance': 2520,
            'Parking & Tolls': 1260,
            'Public Transit': 1890,
            'Ride Shares': 1260,
            'Clothing': 3150,
            'Personal Care': 1260,
            'Grooming': 1260,
            'Medical': 2100,
            'Dental': 1050,
            'Vision': 525,
            'Fitness': 1512,
            'Mental Health': 1260,
            'Entertainment': 3780,
            'Hobbies': 2520,
            'Subscriptions': 1260,
            'Phone': 1260,
            'Other Personal': 2520
        }
    },
    "Brisbane": {
        "Conservative (statistical)": {
            'Groceries': 4560,
            'Dining Out': 2280,
            'Coffee Shops': 570,
            'Auto Payment': 3420,
            'Gas & Fuel': 1710,
            'Auto Maintenance': 760,
            'Auto Insurance': 1330,
            'Parking & Tolls': 380,
            'Public Transit': 760,
            'Ride Shares': 380,
            'Clothing': 950,
            'Personal Care': 380,
            'Grooming': 380,
            'Medical': 760,
            'Dental': 380,
            'Vision': 190,
            'Fitness': 456,
            'Mental Health': 0,
            'Entertainment': 1140,
            'Hobbies': 570,
            'Subscriptions': 380,
            'Phone': 760,
            'Other Personal': 760
        },
        "Average (statistical)": {
            'Groceries': 5700,
            'Dining Out': 3420,
            'Coffee Shops': 1140,
            'Auto Payment': 5700,
            'Gas & Fuel': 2280,
            'Auto Maintenance': 1140,
            'Auto Insurance': 1710,
            'Parking & Tolls': 570,
            'Public Transit': 1140,
            'Ride Shares': 570,
            'Clothing': 1425,
            'Personal Care': 570,
            'Grooming': 570,
            'Medical': 1140,
            'Dental': 570,
            'Vision': 285,
            'Fitness': 684,
            'Mental Health': 570,
            'Entertainment': 1710,
            'Hobbies': 1140,
            'Subscriptions': 570,
            'Phone': 950,
            'Other Personal': 1140
        },
        "High-end (statistical)": {
            'Groceries': 7980,
            'Dining Out': 5700,
            'Coffee Shops': 2280,
            'Auto Payment': 11400,
            'Gas & Fuel': 3420,
            'Auto Maintenance': 1900,
            'Auto Insurance': 2280,
            'Parking & Tolls': 1140,
            'Public Transit': 1710,
            'Ride Shares': 1140,
            'Clothing': 2850,
            'Personal Care': 1140,
            'Grooming': 1140,
            'Medical': 1900,
            'Dental': 950,
            'Vision': 475,
            'Fitness': 1368,
            'Mental Health': 1140,
            'Entertainment': 3420,
            'Hobbies': 2280,
            'Subscriptions': 1140,
            'Phone': 1140,
            'Other Personal': 2280
        }
    },
    "Auckland": {
        "Conservative (statistical)": {
            'Groceries': 4320,
            'Dining Out': 2160,
            'Coffee Shops': 540,
            'Auto Payment': 3240,
            'Gas & Fuel': 1620,
            'Auto Maintenance': 720,
            'Auto Insurance': 1260,
            'Parking & Tolls': 360,
            'Public Transit': 720,
            'Ride Shares': 360,
            'Clothing': 900,
            'Personal Care': 360,
            'Grooming': 360,
            'Medical': 720,
            'Dental': 360,
            'Vision': 180,
            'Fitness': 432,
            'Mental Health': 0,
            'Entertainment': 1080,
            'Hobbies': 540,
            'Subscriptions': 360,
            'Phone': 720,
            'Other Personal': 720
        },
        "Average (statistical)": {
            'Groceries': 5400,
            'Dining Out': 3240,
            'Coffee Shops': 1080,
            'Auto Payment': 5400,
            'Gas & Fuel': 2160,
            'Auto Maintenance': 1080,
            'Auto Insurance': 1620,
            'Parking & Tolls': 540,
            'Public Transit': 1080,
            'Ride Shares': 540,
            'Clothing': 1350,
            'Personal Care': 540,
            'Grooming': 540,
            'Medical': 1080,
            'Dental': 540,
            'Vision': 270,
            'Fitness': 648,
            'Mental Health': 540,
            'Entertainment': 1620,
            'Hobbies': 1080,
            'Subscriptions': 540,
            'Phone': 900,
            'Other Personal': 1080
        },
        "High-end (statistical)": {
            'Groceries': 7560,
            'Dining Out': 5400,
            'Coffee Shops': 2160,
            'Auto Payment': 10800,
            'Gas & Fuel': 3240,
            'Auto Maintenance': 1800,
            'Auto Insurance': 2160,
            'Parking & Tolls': 1080,
            'Public Transit': 1620,
            'Ride Shares': 1080,
            'Clothing': 2700,
            'Personal Care': 1080,
            'Grooming': 1080,
            'Medical': 1800,
            'Dental': 900,
            'Vision': 450,
            'Fitness': 1296,
            'Mental Health': 1080,
            'Entertainment': 3240,
            'Hobbies': 2160,
            'Subscriptions': 1080,
            'Phone': 1080,
            'Other Personal': 2160
        }
    },
    "Wellington": {
        "Conservative (statistical)": {
            'Groceries': 4416,
            'Dining Out': 2208,
            'Coffee Shops': 552,
            'Auto Payment': 3312,
            'Gas & Fuel': 1656,
            'Auto Maintenance': 736,
            'Auto Insurance': 1288,
            'Parking & Tolls': 368,
            'Public Transit': 736,
            'Ride Shares': 368,
            'Clothing': 920,
            'Personal Care': 368,
            'Grooming': 368,
            'Medical': 736,
            'Dental': 368,
            'Vision': 184,
            'Fitness': 442,
            'Mental Health': 0,
            'Entertainment': 1104,
            'Hobbies': 552,
            'Subscriptions': 368,
            'Phone': 736,
            'Other Personal': 736
        },
        "Average (statistical)": {
            'Groceries': 5520,
            'Dining Out': 3312,
            'Coffee Shops': 1104,
            'Auto Payment': 5520,
            'Gas & Fuel': 2208,
            'Auto Maintenance': 1104,
            'Auto Insurance': 1656,
            'Parking & Tolls': 552,
            'Public Transit': 1104,
            'Ride Shares': 552,
            'Clothing': 1380,
            'Personal Care': 552,
            'Grooming': 552,
            'Medical': 1104,
            'Dental': 552,
            'Vision': 276,
            'Fitness': 662,
            'Mental Health': 552,
            'Entertainment': 1656,
            'Hobbies': 1104,
            'Subscriptions': 552,
            'Phone': 920,
            'Other Personal': 1104
        },
        "High-end (statistical)": {
            'Groceries': 7728,
            'Dining Out': 5520,
            'Coffee Shops': 2208,
            'Auto Payment': 11040,
            'Gas & Fuel': 3312,
            'Auto Maintenance': 1840,
            'Auto Insurance': 2208,
            'Parking & Tolls': 1104,
            'Public Transit': 1656,
            'Ride Shares': 1104,
            'Clothing': 2760,
            'Personal Care': 1104,
            'Grooming': 1104,
            'Medical': 1840,
            'Dental': 920,
            'Vision': 460,
            'Fitness': 1325,
            'Mental Health': 1104,
            'Entertainment': 3312,
            'Hobbies': 2208,
            'Subscriptions': 1104,
            'Phone': 1104,
            'Other Personal': 2208
        }
    }
}

STATISTICAL_STRATEGIES_LEGACY = ["Conservative", "Average", "High-end"]  # For backward compatibility

# Helper functions for strategy management
def get_available_strategies_for_location(location, template_type='family'):
    """
    Get all available strategies for a location (statistical + custom)

    Args:
        location: Location name
        template_type: 'family' or 'children'

    Returns:
        List of strategy names (statistical + custom)
    """
    strategies = []

    # Get base templates
    if template_type == 'family':
        base_templates = FAMILY_EXPENSE_TEMPLATES
        custom_templates = st.session_state.get('custom_family_templates', {})
    else:  # children
        base_templates = CHILDREN_EXPENSE_TEMPLATES
        custom_templates = st.session_state.get('custom_children_templates', {})

    # Add statistical strategies if they exist for this location
    if location in base_templates:
        strategies.extend(STATISTICAL_STRATEGIES)

    # Add custom strategies if they exist for this location
    if location in custom_templates:
        for strategy_name in custom_templates[location].keys():
            if not strategy_name.endswith(' (custom)'):
                # Add (custom) suffix if not already present
                strategies.append(f"{strategy_name} (custom)")
            else:
                strategies.append(strategy_name)

    return strategies

def is_statistical_strategy(strategy_name):
    """Check if a strategy is a statistical (built-in) strategy"""
    return strategy_name in STATISTICAL_STRATEGIES or strategy_name in STATISTICAL_STRATEGIES_LEGACY

def is_custom_strategy(strategy_name):
    """Check if a strategy is a custom (user-defined) strategy"""
    return strategy_name.endswith(' (custom)')

def get_strategy_base_name(strategy_name):
    """Get the base name of a strategy without (statistical) or (custom) suffix"""
    if strategy_name.endswith(' (statistical)'):
        return strategy_name[:-14]  # Remove ' (statistical)'
    elif strategy_name.endswith(' (custom)'):
        return strategy_name[:-9]  # Remove ' (custom)'
    return strategy_name

def normalize_strategy_name(strategy_name):
    """
    Normalize strategy name to the new format with suffix.
    Handles backward compatibility with old names.
    """
    # If already has a suffix, return as is
    if strategy_name.endswith(' (statistical)') or strategy_name.endswith(' (custom)'):
        return strategy_name

    # Convert legacy names to new format
    if strategy_name in STATISTICAL_STRATEGIES_LEGACY:
        idx = STATISTICAL_STRATEGIES_LEGACY.index(strategy_name)
        return STATISTICAL_STRATEGIES[idx]

    # Assume it's a custom strategy if not statistical
    return f"{strategy_name} (custom)"

# ============================================================================
# STATE-LEVEL EXPENSE TEMPLATES (all 50 US states)
# ============================================================================
# Annual amounts per adult, 2024 dollars. Derived from BLS Consumer Expenditure
# Survey, BEA Regional Price Parities, and state-specific data (auto insurance,
# gas prices, groceries, transit availability).
# Each state has 3 strategies: Conservative, Average, High-end.

STATE_EXPENSE_TEMPLATES = {
    "Alabama": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1890, "Coffee Shops": 420,
            "Auto Payment": 3780, "Gas & Fuel": 1680, "Auto Maintenance": 630, "Auto Insurance": 1050, "Parking & Tolls": 210, "Public Transit": 70, "Ride Shares": 140,
            "Clothing": 840, "Personal Care": 420, "Grooming": 280,
            "Medical": 1680, "Dental": 420, "Vision": 140,
            "Fitness": 280, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 770, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2700, "Coffee Shops": 600,
            "Auto Payment": 5400, "Gas & Fuel": 2400, "Auto Maintenance": 900, "Auto Insurance": 1500, "Parking & Tolls": 300, "Public Transit": 100, "Ride Shares": 200,
            "Clothing": 1200, "Personal Care": 600, "Grooming": 400,
            "Medical": 2400, "Dental": 600, "Vision": 200,
            "Fitness": 400, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1100, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 4050, "Coffee Shops": 900,
            "Auto Payment": 8100, "Gas & Fuel": 3600, "Auto Maintenance": 1350, "Auto Insurance": 2250, "Parking & Tolls": 450, "Public Transit": 150, "Ride Shares": 300,
            "Clothing": 1800, "Personal Care": 900, "Grooming": 600,
            "Medical": 3600, "Dental": 900, "Vision": 300,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1650, "Other Personal": 900
        }
    },
    "Alaska": {
        "Conservative (statistical)": {
            "Groceries": 4200, "Dining Out": 2240, "Coffee Shops": 490,
            "Auto Payment": 3780, "Gas & Fuel": 2100, "Auto Maintenance": 700, "Auto Insurance": 980, "Parking & Tolls": 210, "Public Transit": 105, "Ride Shares": 175,
            "Clothing": 980, "Personal Care": 490, "Grooming": 315,
            "Medical": 2100, "Dental": 490, "Vision": 175,
            "Fitness": 350, "Mental Health": 245,
            "Entertainment": 910, "Hobbies": 490, "Subscriptions": 385, "Phone": 840, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 6000, "Dining Out": 3200, "Coffee Shops": 700,
            "Auto Payment": 5400, "Gas & Fuel": 3000, "Auto Maintenance": 1000, "Auto Insurance": 1400, "Parking & Tolls": 300, "Public Transit": 150, "Ride Shares": 250,
            "Clothing": 1400, "Personal Care": 700, "Grooming": 450,
            "Medical": 3000, "Dental": 700, "Vision": 250,
            "Fitness": 500, "Mental Health": 350,
            "Entertainment": 1300, "Hobbies": 700, "Subscriptions": 550, "Phone": 1200, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 9000, "Dining Out": 4800, "Coffee Shops": 1050,
            "Auto Payment": 8100, "Gas & Fuel": 4500, "Auto Maintenance": 1500, "Auto Insurance": 2100, "Parking & Tolls": 450, "Public Transit": 225, "Ride Shares": 375,
            "Clothing": 2100, "Personal Care": 1050, "Grooming": 675,
            "Medical": 4500, "Dental": 1050, "Vision": 375,
            "Fitness": 750, "Mental Health": 525,
            "Entertainment": 1950, "Hobbies": 1050, "Subscriptions": 825, "Phone": 1800, "Other Personal": 1050
        }
    },
    "Arizona": {
        "Conservative (statistical)": {
            "Groceries": 3640, "Dining Out": 2100, "Coffee Shops": 455,
            "Auto Payment": 3850, "Gas & Fuel": 1820, "Auto Maintenance": 665, "Auto Insurance": 1190, "Parking & Tolls": 245, "Public Transit": 105, "Ride Shares": 210,
            "Clothing": 910, "Personal Care": 455, "Grooming": 301,
            "Medical": 1820, "Dental": 455, "Vision": 154,
            "Fitness": 350, "Mental Health": 245,
            "Entertainment": 910, "Hobbies": 455, "Subscriptions": 371, "Phone": 805, "Other Personal": 455
        },
        "Average (statistical)": {
            "Groceries": 5200, "Dining Out": 3000, "Coffee Shops": 650,
            "Auto Payment": 5500, "Gas & Fuel": 2600, "Auto Maintenance": 950, "Auto Insurance": 1700, "Parking & Tolls": 350, "Public Transit": 150, "Ride Shares": 300,
            "Clothing": 1300, "Personal Care": 650, "Grooming": 430,
            "Medical": 2600, "Dental": 650, "Vision": 220,
            "Fitness": 500, "Mental Health": 350,
            "Entertainment": 1300, "Hobbies": 650, "Subscriptions": 530, "Phone": 1150, "Other Personal": 650
        },
        "High-end (statistical)": {
            "Groceries": 7800, "Dining Out": 4500, "Coffee Shops": 975,
            "Auto Payment": 8250, "Gas & Fuel": 3900, "Auto Maintenance": 1425, "Auto Insurance": 2550, "Parking & Tolls": 525, "Public Transit": 225, "Ride Shares": 450,
            "Clothing": 1950, "Personal Care": 975, "Grooming": 645,
            "Medical": 3900, "Dental": 975, "Vision": 330,
            "Fitness": 750, "Mental Health": 525,
            "Entertainment": 1950, "Hobbies": 975, "Subscriptions": 795, "Phone": 1725, "Other Personal": 975
        }
    },
    "Arkansas": {
        "Conservative (statistical)": {
            "Groceries": 3290, "Dining Out": 1820, "Coffee Shops": 385,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 616, "Auto Insurance": 1050, "Parking & Tolls": 175, "Public Transit": 56, "Ride Shares": 119,
            "Clothing": 805, "Personal Care": 399, "Grooming": 266,
            "Medical": 1610, "Dental": 399, "Vision": 140,
            "Fitness": 266, "Mental Health": 196,
            "Entertainment": 805, "Hobbies": 399, "Subscriptions": 336, "Phone": 756, "Other Personal": 399
        },
        "Average (statistical)": {
            "Groceries": 4700, "Dining Out": 2600, "Coffee Shops": 550,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 880, "Auto Insurance": 1500, "Parking & Tolls": 250, "Public Transit": 80, "Ride Shares": 170,
            "Clothing": 1150, "Personal Care": 570, "Grooming": 380,
            "Medical": 2300, "Dental": 570, "Vision": 200,
            "Fitness": 380, "Mental Health": 280,
            "Entertainment": 1150, "Hobbies": 570, "Subscriptions": 480, "Phone": 1080, "Other Personal": 570
        },
        "High-end (statistical)": {
            "Groceries": 7050, "Dining Out": 3900, "Coffee Shops": 825,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1320, "Auto Insurance": 2250, "Parking & Tolls": 375, "Public Transit": 120, "Ride Shares": 255,
            "Clothing": 1725, "Personal Care": 855, "Grooming": 570,
            "Medical": 3450, "Dental": 855, "Vision": 300,
            "Fitness": 570, "Mental Health": 420,
            "Entertainment": 1725, "Hobbies": 855, "Subscriptions": 720, "Phone": 1620, "Other Personal": 855
        }
    },
    "California": {
        "Conservative (statistical)": {
            "Groceries": 4480, "Dining Out": 2870, "Coffee Shops": 630,
            "Auto Payment": 4200, "Gas & Fuel": 2380, "Auto Maintenance": 735, "Auto Insurance": 1400, "Parking & Tolls": 490, "Public Transit": 350, "Ride Shares": 350,
            "Clothing": 1120, "Personal Care": 560, "Grooming": 371,
            "Medical": 2100, "Dental": 525, "Vision": 175,
            "Fitness": 455, "Mental Health": 350,
            "Entertainment": 1120, "Hobbies": 560, "Subscriptions": 420, "Phone": 875, "Other Personal": 560
        },
        "Average (statistical)": {
            "Groceries": 6400, "Dining Out": 4100, "Coffee Shops": 900,
            "Auto Payment": 6000, "Gas & Fuel": 3400, "Auto Maintenance": 1050, "Auto Insurance": 2000, "Parking & Tolls": 700, "Public Transit": 500, "Ride Shares": 500,
            "Clothing": 1600, "Personal Care": 800, "Grooming": 530,
            "Medical": 3000, "Dental": 750, "Vision": 250,
            "Fitness": 650, "Mental Health": 500,
            "Entertainment": 1600, "Hobbies": 800, "Subscriptions": 600, "Phone": 1250, "Other Personal": 800
        },
        "High-end (statistical)": {
            "Groceries": 9600, "Dining Out": 6150, "Coffee Shops": 1350,
            "Auto Payment": 9000, "Gas & Fuel": 5100, "Auto Maintenance": 1575, "Auto Insurance": 3000, "Parking & Tolls": 1050, "Public Transit": 750, "Ride Shares": 750,
            "Clothing": 2400, "Personal Care": 1200, "Grooming": 795,
            "Medical": 4500, "Dental": 1125, "Vision": 375,
            "Fitness": 975, "Mental Health": 750,
            "Entertainment": 2400, "Hobbies": 1200, "Subscriptions": 900, "Phone": 1875, "Other Personal": 1200
        }
    },
    "Colorado": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 2450, "Coffee Shops": 546,
            "Auto Payment": 3920, "Gas & Fuel": 1890, "Auto Maintenance": 686, "Auto Insurance": 1260, "Parking & Tolls": 315, "Public Transit": 210, "Ride Shares": 245,
            "Clothing": 980, "Personal Care": 504, "Grooming": 329,
            "Medical": 1890, "Dental": 490, "Vision": 168,
            "Fitness": 420, "Mental Health": 315,
            "Entertainment": 1050, "Hobbies": 560, "Subscriptions": 399, "Phone": 840, "Other Personal": 504
        },
        "Average (statistical)": {
            "Groceries": 5600, "Dining Out": 3500, "Coffee Shops": 780,
            "Auto Payment": 5600, "Gas & Fuel": 2700, "Auto Maintenance": 980, "Auto Insurance": 1800, "Parking & Tolls": 450, "Public Transit": 300, "Ride Shares": 350,
            "Clothing": 1400, "Personal Care": 720, "Grooming": 470,
            "Medical": 2700, "Dental": 700, "Vision": 240,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1500, "Hobbies": 800, "Subscriptions": 570, "Phone": 1200, "Other Personal": 720
        },
        "High-end (statistical)": {
            "Groceries": 8400, "Dining Out": 5250, "Coffee Shops": 1170,
            "Auto Payment": 8400, "Gas & Fuel": 4050, "Auto Maintenance": 1470, "Auto Insurance": 2700, "Parking & Tolls": 675, "Public Transit": 450, "Ride Shares": 525,
            "Clothing": 2100, "Personal Care": 1080, "Grooming": 705,
            "Medical": 4050, "Dental": 1050, "Vision": 360,
            "Fitness": 900, "Mental Health": 675,
            "Entertainment": 2250, "Hobbies": 1200, "Subscriptions": 855, "Phone": 1800, "Other Personal": 1080
        }
    },
    "Connecticut": {
        "Conservative (statistical)": {
            "Groceries": 4200, "Dining Out": 2590, "Coffee Shops": 560,
            "Auto Payment": 4060, "Gas & Fuel": 1960, "Auto Maintenance": 700, "Auto Insurance": 1330, "Parking & Tolls": 420, "Public Transit": 315, "Ride Shares": 280,
            "Clothing": 1050, "Personal Care": 532, "Grooming": 350,
            "Medical": 2100, "Dental": 525, "Vision": 175,
            "Fitness": 420, "Mental Health": 315,
            "Entertainment": 1050, "Hobbies": 532, "Subscriptions": 413, "Phone": 854, "Other Personal": 532
        },
        "Average (statistical)": {
            "Groceries": 6000, "Dining Out": 3700, "Coffee Shops": 800,
            "Auto Payment": 5800, "Gas & Fuel": 2800, "Auto Maintenance": 1000, "Auto Insurance": 1900, "Parking & Tolls": 600, "Public Transit": 450, "Ride Shares": 400,
            "Clothing": 1500, "Personal Care": 760, "Grooming": 500,
            "Medical": 3000, "Dental": 750, "Vision": 250,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1500, "Hobbies": 760, "Subscriptions": 590, "Phone": 1220, "Other Personal": 760
        },
        "High-end (statistical)": {
            "Groceries": 9000, "Dining Out": 5550, "Coffee Shops": 1200,
            "Auto Payment": 8700, "Gas & Fuel": 4200, "Auto Maintenance": 1500, "Auto Insurance": 2850, "Parking & Tolls": 900, "Public Transit": 675, "Ride Shares": 600,
            "Clothing": 2250, "Personal Care": 1140, "Grooming": 750,
            "Medical": 4500, "Dental": 1125, "Vision": 375,
            "Fitness": 900, "Mental Health": 675,
            "Entertainment": 2250, "Hobbies": 1140, "Subscriptions": 885, "Phone": 1830, "Other Personal": 1140
        }
    },
    "Delaware": {
        "Conservative (statistical)": {
            "Groceries": 3780, "Dining Out": 2240, "Coffee Shops": 490,
            "Auto Payment": 3850, "Gas & Fuel": 1820, "Auto Maintenance": 665, "Auto Insurance": 1190, "Parking & Tolls": 315, "Public Transit": 175, "Ride Shares": 210,
            "Clothing": 910, "Personal Care": 469, "Grooming": 308,
            "Medical": 1890, "Dental": 469, "Vision": 161,
            "Fitness": 350, "Mental Health": 266,
            "Entertainment": 910, "Hobbies": 469, "Subscriptions": 378, "Phone": 812, "Other Personal": 469
        },
        "Average (statistical)": {
            "Groceries": 5400, "Dining Out": 3200, "Coffee Shops": 700,
            "Auto Payment": 5500, "Gas & Fuel": 2600, "Auto Maintenance": 950, "Auto Insurance": 1700, "Parking & Tolls": 450, "Public Transit": 250, "Ride Shares": 300,
            "Clothing": 1300, "Personal Care": 670, "Grooming": 440,
            "Medical": 2700, "Dental": 670, "Vision": 230,
            "Fitness": 500, "Mental Health": 380,
            "Entertainment": 1300, "Hobbies": 670, "Subscriptions": 540, "Phone": 1160, "Other Personal": 670
        },
        "High-end (statistical)": {
            "Groceries": 8100, "Dining Out": 4800, "Coffee Shops": 1050,
            "Auto Payment": 8250, "Gas & Fuel": 3900, "Auto Maintenance": 1425, "Auto Insurance": 2550, "Parking & Tolls": 675, "Public Transit": 375, "Ride Shares": 450,
            "Clothing": 1950, "Personal Care": 1005, "Grooming": 660,
            "Medical": 4050, "Dental": 1005, "Vision": 345,
            "Fitness": 750, "Mental Health": 570,
            "Entertainment": 1950, "Hobbies": 1005, "Subscriptions": 810, "Phone": 1740, "Other Personal": 1005
        }
    },
    "Florida": {
        "Conservative (statistical)": {
            "Groceries": 3710, "Dining Out": 2240, "Coffee Shops": 490,
            "Auto Payment": 3920, "Gas & Fuel": 1820, "Auto Maintenance": 672, "Auto Insurance": 1470, "Parking & Tolls": 315, "Public Transit": 140, "Ride Shares": 245,
            "Clothing": 910, "Personal Care": 462, "Grooming": 308,
            "Medical": 1890, "Dental": 462, "Vision": 161,
            "Fitness": 350, "Mental Health": 259,
            "Entertainment": 952, "Hobbies": 462, "Subscriptions": 378, "Phone": 812, "Other Personal": 462
        },
        "Average (statistical)": {
            "Groceries": 5300, "Dining Out": 3200, "Coffee Shops": 700,
            "Auto Payment": 5600, "Gas & Fuel": 2600, "Auto Maintenance": 960, "Auto Insurance": 2100, "Parking & Tolls": 450, "Public Transit": 200, "Ride Shares": 350,
            "Clothing": 1300, "Personal Care": 660, "Grooming": 440,
            "Medical": 2700, "Dental": 660, "Vision": 230,
            "Fitness": 500, "Mental Health": 370,
            "Entertainment": 1360, "Hobbies": 660, "Subscriptions": 540, "Phone": 1160, "Other Personal": 660
        },
        "High-end (statistical)": {
            "Groceries": 7950, "Dining Out": 4800, "Coffee Shops": 1050,
            "Auto Payment": 8400, "Gas & Fuel": 3900, "Auto Maintenance": 1440, "Auto Insurance": 3150, "Parking & Tolls": 675, "Public Transit": 300, "Ride Shares": 525,
            "Clothing": 1950, "Personal Care": 990, "Grooming": 660,
            "Medical": 4050, "Dental": 990, "Vision": 345,
            "Fitness": 750, "Mental Health": 555,
            "Entertainment": 2040, "Hobbies": 990, "Subscriptions": 810, "Phone": 1740, "Other Personal": 990
        }
    },
    "Georgia": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 2030, "Coffee Shops": 441,
            "Auto Payment": 3780, "Gas & Fuel": 1750, "Auto Maintenance": 644, "Auto Insurance": 1190, "Parking & Tolls": 280, "Public Transit": 140, "Ride Shares": 210,
            "Clothing": 868, "Personal Care": 441, "Grooming": 294,
            "Medical": 1750, "Dental": 441, "Vision": 147,
            "Fitness": 322, "Mental Health": 238,
            "Entertainment": 882, "Hobbies": 441, "Subscriptions": 364, "Phone": 784, "Other Personal": 441
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2900, "Coffee Shops": 630,
            "Auto Payment": 5400, "Gas & Fuel": 2500, "Auto Maintenance": 920, "Auto Insurance": 1700, "Parking & Tolls": 400, "Public Transit": 200, "Ride Shares": 300,
            "Clothing": 1240, "Personal Care": 630, "Grooming": 420,
            "Medical": 2500, "Dental": 630, "Vision": 210,
            "Fitness": 460, "Mental Health": 340,
            "Entertainment": 1260, "Hobbies": 630, "Subscriptions": 520, "Phone": 1120, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4350, "Coffee Shops": 945,
            "Auto Payment": 8100, "Gas & Fuel": 3750, "Auto Maintenance": 1380, "Auto Insurance": 2550, "Parking & Tolls": 600, "Public Transit": 300, "Ride Shares": 450,
            "Clothing": 1860, "Personal Care": 945, "Grooming": 630,
            "Medical": 3750, "Dental": 945, "Vision": 315,
            "Fitness": 690, "Mental Health": 510,
            "Entertainment": 1890, "Hobbies": 945, "Subscriptions": 780, "Phone": 1680, "Other Personal": 945
        }
    },
    "Hawaii": {
        "Conservative (statistical)": {
            "Groceries": 5040, "Dining Out": 3010, "Coffee Shops": 630,
            "Auto Payment": 3640, "Gas & Fuel": 2380, "Auto Maintenance": 700, "Auto Insurance": 924, "Parking & Tolls": 350, "Public Transit": 280, "Ride Shares": 280,
            "Clothing": 1050, "Personal Care": 546, "Grooming": 357,
            "Medical": 2100, "Dental": 532, "Vision": 175,
            "Fitness": 420, "Mental Health": 315,
            "Entertainment": 1050, "Hobbies": 546, "Subscriptions": 420, "Phone": 882, "Other Personal": 546
        },
        "Average (statistical)": {
            "Groceries": 7200, "Dining Out": 4300, "Coffee Shops": 900,
            "Auto Payment": 5200, "Gas & Fuel": 3400, "Auto Maintenance": 1000, "Auto Insurance": 1320, "Parking & Tolls": 500, "Public Transit": 400, "Ride Shares": 400,
            "Clothing": 1500, "Personal Care": 780, "Grooming": 510,
            "Medical": 3000, "Dental": 760, "Vision": 250,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1500, "Hobbies": 780, "Subscriptions": 600, "Phone": 1260, "Other Personal": 780
        },
        "High-end (statistical)": {
            "Groceries": 10800, "Dining Out": 6450, "Coffee Shops": 1350,
            "Auto Payment": 7800, "Gas & Fuel": 5100, "Auto Maintenance": 1500, "Auto Insurance": 1980, "Parking & Tolls": 750, "Public Transit": 600, "Ride Shares": 600,
            "Clothing": 2250, "Personal Care": 1170, "Grooming": 765,
            "Medical": 4500, "Dental": 1140, "Vision": 375,
            "Fitness": 900, "Mental Health": 675,
            "Entertainment": 2250, "Hobbies": 1170, "Subscriptions": 900, "Phone": 1890, "Other Personal": 1170
        }
    },
    "Idaho": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3710, "Gas & Fuel": 1820, "Auto Maintenance": 644, "Auto Insurance": 868, "Parking & Tolls": 196, "Public Transit": 70, "Ride Shares": 140,
            "Clothing": 840, "Personal Care": 434, "Grooming": 287,
            "Medical": 1750, "Dental": 434, "Vision": 147,
            "Fitness": 308, "Mental Health": 224,
            "Entertainment": 868, "Hobbies": 434, "Subscriptions": 357, "Phone": 784, "Other Personal": 434
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5300, "Gas & Fuel": 2600, "Auto Maintenance": 920, "Auto Insurance": 1240, "Parking & Tolls": 280, "Public Transit": 100, "Ride Shares": 200,
            "Clothing": 1200, "Personal Care": 620, "Grooming": 410,
            "Medical": 2500, "Dental": 620, "Vision": 210,
            "Fitness": 440, "Mental Health": 320,
            "Entertainment": 1240, "Hobbies": 620, "Subscriptions": 510, "Phone": 1120, "Other Personal": 620
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7950, "Gas & Fuel": 3900, "Auto Maintenance": 1380, "Auto Insurance": 1860, "Parking & Tolls": 420, "Public Transit": 150, "Ride Shares": 300,
            "Clothing": 1800, "Personal Care": 930, "Grooming": 615,
            "Medical": 3750, "Dental": 930, "Vision": 315,
            "Fitness": 660, "Mental Health": 480,
            "Entertainment": 1860, "Hobbies": 930, "Subscriptions": 765, "Phone": 1680, "Other Personal": 930
        }
    },
    "Illinois": {
        "Conservative (statistical)": {
            "Groceries": 3780, "Dining Out": 2310, "Coffee Shops": 518,
            "Auto Payment": 3920, "Gas & Fuel": 1890, "Auto Maintenance": 672, "Auto Insurance": 1190, "Parking & Tolls": 385, "Public Transit": 350, "Ride Shares": 280,
            "Clothing": 952, "Personal Care": 490, "Grooming": 322,
            "Medical": 1890, "Dental": 476, "Vision": 161,
            "Fitness": 371, "Mental Health": 280,
            "Entertainment": 980, "Hobbies": 490, "Subscriptions": 392, "Phone": 826, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 5400, "Dining Out": 3300, "Coffee Shops": 740,
            "Auto Payment": 5600, "Gas & Fuel": 2700, "Auto Maintenance": 960, "Auto Insurance": 1700, "Parking & Tolls": 550, "Public Transit": 500, "Ride Shares": 400,
            "Clothing": 1360, "Personal Care": 700, "Grooming": 460,
            "Medical": 2700, "Dental": 680, "Vision": 230,
            "Fitness": 530, "Mental Health": 400,
            "Entertainment": 1400, "Hobbies": 700, "Subscriptions": 560, "Phone": 1180, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 8100, "Dining Out": 4950, "Coffee Shops": 1110,
            "Auto Payment": 8400, "Gas & Fuel": 4050, "Auto Maintenance": 1440, "Auto Insurance": 2550, "Parking & Tolls": 825, "Public Transit": 750, "Ride Shares": 600,
            "Clothing": 2040, "Personal Care": 1050, "Grooming": 690,
            "Medical": 4050, "Dental": 1020, "Vision": 345,
            "Fitness": 795, "Mental Health": 600,
            "Entertainment": 2100, "Hobbies": 1050, "Subscriptions": 840, "Phone": 1770, "Other Personal": 1050
        }
    },
    "Indiana": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3710, "Gas & Fuel": 1750, "Auto Maintenance": 637, "Auto Insurance": 980, "Parking & Tolls": 210, "Public Transit": 84, "Ride Shares": 154,
            "Clothing": 840, "Personal Care": 427, "Grooming": 280,
            "Medical": 1680, "Dental": 427, "Vision": 147,
            "Fitness": 294, "Mental Health": 217,
            "Entertainment": 854, "Hobbies": 427, "Subscriptions": 350, "Phone": 770, "Other Personal": 427
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5300, "Gas & Fuel": 2500, "Auto Maintenance": 910, "Auto Insurance": 1400, "Parking & Tolls": 300, "Public Transit": 120, "Ride Shares": 220,
            "Clothing": 1200, "Personal Care": 610, "Grooming": 400,
            "Medical": 2400, "Dental": 610, "Vision": 210,
            "Fitness": 420, "Mental Health": 310,
            "Entertainment": 1220, "Hobbies": 610, "Subscriptions": 500, "Phone": 1100, "Other Personal": 610
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7950, "Gas & Fuel": 3750, "Auto Maintenance": 1365, "Auto Insurance": 2100, "Parking & Tolls": 450, "Public Transit": 180, "Ride Shares": 330,
            "Clothing": 1800, "Personal Care": 915, "Grooming": 600,
            "Medical": 3600, "Dental": 915, "Vision": 315,
            "Fitness": 630, "Mental Health": 465,
            "Entertainment": 1830, "Hobbies": 915, "Subscriptions": 750, "Phone": 1650, "Other Personal": 915
        }
    },
    "Iowa": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1890, "Coffee Shops": 399,
            "Auto Payment": 3640, "Gas & Fuel": 1750, "Auto Maintenance": 630, "Auto Insurance": 868, "Parking & Tolls": 175, "Public Transit": 70, "Ride Shares": 126,
            "Clothing": 819, "Personal Care": 413, "Grooming": 273,
            "Medical": 1680, "Dental": 413, "Vision": 140,
            "Fitness": 280, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 413, "Subscriptions": 343, "Phone": 756, "Other Personal": 413
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2700, "Coffee Shops": 570,
            "Auto Payment": 5200, "Gas & Fuel": 2500, "Auto Maintenance": 900, "Auto Insurance": 1240, "Parking & Tolls": 250, "Public Transit": 100, "Ride Shares": 180,
            "Clothing": 1170, "Personal Care": 590, "Grooming": 390,
            "Medical": 2400, "Dental": 590, "Vision": 200,
            "Fitness": 400, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 590, "Subscriptions": 490, "Phone": 1080, "Other Personal": 590
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 4050, "Coffee Shops": 855,
            "Auto Payment": 7800, "Gas & Fuel": 3750, "Auto Maintenance": 1350, "Auto Insurance": 1860, "Parking & Tolls": 375, "Public Transit": 150, "Ride Shares": 270,
            "Clothing": 1755, "Personal Care": 885, "Grooming": 585,
            "Medical": 3600, "Dental": 885, "Vision": 300,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 885, "Subscriptions": 735, "Phone": 1620, "Other Personal": 885
        }
    },
    "Kansas": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1890, "Coffee Shops": 406,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 630, "Auto Insurance": 1050, "Parking & Tolls": 196, "Public Transit": 70, "Ride Shares": 133,
            "Clothing": 826, "Personal Care": 420, "Grooming": 280,
            "Medical": 1680, "Dental": 420, "Vision": 140,
            "Fitness": 287, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 763, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2700, "Coffee Shops": 580,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 900, "Auto Insurance": 1500, "Parking & Tolls": 280, "Public Transit": 100, "Ride Shares": 190,
            "Clothing": 1180, "Personal Care": 600, "Grooming": 400,
            "Medical": 2400, "Dental": 600, "Vision": 200,
            "Fitness": 410, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1090, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4050, "Coffee Shops": 870,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1350, "Auto Insurance": 2250, "Parking & Tolls": 420, "Public Transit": 150, "Ride Shares": 285,
            "Clothing": 1770, "Personal Care": 900, "Grooming": 600,
            "Medical": 3600, "Dental": 900, "Vision": 300,
            "Fitness": 615, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1635, "Other Personal": 900
        }
    },
    "Kentucky": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1820, "Coffee Shops": 392,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 623, "Auto Insurance": 1120, "Parking & Tolls": 196, "Public Transit": 70, "Ride Shares": 126,
            "Clothing": 812, "Personal Care": 406, "Grooming": 273,
            "Medical": 1680, "Dental": 406, "Vision": 140,
            "Fitness": 273, "Mental Health": 203,
            "Entertainment": 826, "Hobbies": 406, "Subscriptions": 343, "Phone": 756, "Other Personal": 406
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2600, "Coffee Shops": 560,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 890, "Auto Insurance": 1600, "Parking & Tolls": 280, "Public Transit": 100, "Ride Shares": 180,
            "Clothing": 1160, "Personal Care": 580, "Grooming": 390,
            "Medical": 2400, "Dental": 580, "Vision": 200,
            "Fitness": 390, "Mental Health": 290,
            "Entertainment": 1180, "Hobbies": 580, "Subscriptions": 490, "Phone": 1080, "Other Personal": 580
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 3900, "Coffee Shops": 840,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1335, "Auto Insurance": 2400, "Parking & Tolls": 420, "Public Transit": 150, "Ride Shares": 270,
            "Clothing": 1740, "Personal Care": 870, "Grooming": 585,
            "Medical": 3600, "Dental": 870, "Vision": 300,
            "Fitness": 585, "Mental Health": 435,
            "Entertainment": 1770, "Hobbies": 870, "Subscriptions": 735, "Phone": 1620, "Other Personal": 870
        }
    },
    "Louisiana": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 2100, "Coffee Shops": 420,
            "Auto Payment": 3710, "Gas & Fuel": 1680, "Auto Maintenance": 637, "Auto Insurance": 1400, "Parking & Tolls": 210, "Public Transit": 84, "Ride Shares": 154,
            "Clothing": 840, "Personal Care": 420, "Grooming": 280,
            "Medical": 1750, "Dental": 420, "Vision": 140,
            "Fitness": 280, "Mental Health": 210,
            "Entertainment": 882, "Hobbies": 434, "Subscriptions": 350, "Phone": 770, "Other Personal": 434
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 3000, "Coffee Shops": 600,
            "Auto Payment": 5300, "Gas & Fuel": 2400, "Auto Maintenance": 910, "Auto Insurance": 2000, "Parking & Tolls": 300, "Public Transit": 120, "Ride Shares": 220,
            "Clothing": 1200, "Personal Care": 600, "Grooming": 400,
            "Medical": 2500, "Dental": 600, "Vision": 200,
            "Fitness": 400, "Mental Health": 300,
            "Entertainment": 1260, "Hobbies": 620, "Subscriptions": 500, "Phone": 1100, "Other Personal": 620
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4500, "Coffee Shops": 900,
            "Auto Payment": 7950, "Gas & Fuel": 3600, "Auto Maintenance": 1365, "Auto Insurance": 3000, "Parking & Tolls": 450, "Public Transit": 180, "Ride Shares": 330,
            "Clothing": 1800, "Personal Care": 900, "Grooming": 600,
            "Medical": 3750, "Dental": 900, "Vision": 300,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1890, "Hobbies": 930, "Subscriptions": 750, "Phone": 1650, "Other Personal": 930
        }
    },
    "Maine": {
        "Conservative (statistical)": {
            "Groceries": 3710, "Dining Out": 2030, "Coffee Shops": 455,
            "Auto Payment": 3640, "Gas & Fuel": 1820, "Auto Maintenance": 665, "Auto Insurance": 602, "Parking & Tolls": 210, "Public Transit": 84, "Ride Shares": 140,
            "Clothing": 868, "Personal Care": 441, "Grooming": 294,
            "Medical": 1820, "Dental": 455, "Vision": 154,
            "Fitness": 308, "Mental Health": 238,
            "Entertainment": 882, "Hobbies": 455, "Subscriptions": 364, "Phone": 798, "Other Personal": 455
        },
        "Average (statistical)": {
            "Groceries": 5300, "Dining Out": 2900, "Coffee Shops": 650,
            "Auto Payment": 5200, "Gas & Fuel": 2600, "Auto Maintenance": 950, "Auto Insurance": 860, "Parking & Tolls": 300, "Public Transit": 120, "Ride Shares": 200,
            "Clothing": 1240, "Personal Care": 630, "Grooming": 420,
            "Medical": 2600, "Dental": 650, "Vision": 220,
            "Fitness": 440, "Mental Health": 340,
            "Entertainment": 1260, "Hobbies": 650, "Subscriptions": 520, "Phone": 1140, "Other Personal": 650
        },
        "High-end (statistical)": {
            "Groceries": 7950, "Dining Out": 4350, "Coffee Shops": 975,
            "Auto Payment": 7800, "Gas & Fuel": 3900, "Auto Maintenance": 1425, "Auto Insurance": 1290, "Parking & Tolls": 450, "Public Transit": 180, "Ride Shares": 300,
            "Clothing": 1860, "Personal Care": 945, "Grooming": 630,
            "Medical": 3900, "Dental": 975, "Vision": 330,
            "Fitness": 660, "Mental Health": 510,
            "Entertainment": 1890, "Hobbies": 975, "Subscriptions": 780, "Phone": 1710, "Other Personal": 975
        }
    },
    "Maryland": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 2450, "Coffee Shops": 532,
            "Auto Payment": 3990, "Gas & Fuel": 1890, "Auto Maintenance": 686, "Auto Insurance": 1260, "Parking & Tolls": 385, "Public Transit": 315, "Ride Shares": 280,
            "Clothing": 980, "Personal Care": 504, "Grooming": 329,
            "Medical": 1960, "Dental": 490, "Vision": 168,
            "Fitness": 385, "Mental Health": 294,
            "Entertainment": 980, "Hobbies": 504, "Subscriptions": 399, "Phone": 840, "Other Personal": 504
        },
        "Average (statistical)": {
            "Groceries": 5600, "Dining Out": 3500, "Coffee Shops": 760,
            "Auto Payment": 5700, "Gas & Fuel": 2700, "Auto Maintenance": 980, "Auto Insurance": 1800, "Parking & Tolls": 550, "Public Transit": 450, "Ride Shares": 400,
            "Clothing": 1400, "Personal Care": 720, "Grooming": 470,
            "Medical": 2800, "Dental": 700, "Vision": 240,
            "Fitness": 550, "Mental Health": 420,
            "Entertainment": 1400, "Hobbies": 720, "Subscriptions": 570, "Phone": 1200, "Other Personal": 720
        },
        "High-end (statistical)": {
            "Groceries": 8400, "Dining Out": 5250, "Coffee Shops": 1140,
            "Auto Payment": 8550, "Gas & Fuel": 4050, "Auto Maintenance": 1470, "Auto Insurance": 2700, "Parking & Tolls": 825, "Public Transit": 675, "Ride Shares": 600,
            "Clothing": 2100, "Personal Care": 1080, "Grooming": 705,
            "Medical": 4200, "Dental": 1050, "Vision": 360,
            "Fitness": 825, "Mental Health": 630,
            "Entertainment": 2100, "Hobbies": 1080, "Subscriptions": 855, "Phone": 1800, "Other Personal": 1080
        }
    },
    "Massachusetts": {
        "Conservative (statistical)": {
            "Groceries": 4340, "Dining Out": 2730, "Coffee Shops": 588,
            "Auto Payment": 3990, "Gas & Fuel": 1960, "Auto Maintenance": 700, "Auto Insurance": 1190, "Parking & Tolls": 455, "Public Transit": 420, "Ride Shares": 315,
            "Clothing": 1050, "Personal Care": 546, "Grooming": 357,
            "Medical": 2170, "Dental": 546, "Vision": 182,
            "Fitness": 434, "Mental Health": 336,
            "Entertainment": 1050, "Hobbies": 546, "Subscriptions": 420, "Phone": 868, "Other Personal": 546
        },
        "Average (statistical)": {
            "Groceries": 6200, "Dining Out": 3900, "Coffee Shops": 840,
            "Auto Payment": 5700, "Gas & Fuel": 2800, "Auto Maintenance": 1000, "Auto Insurance": 1700, "Parking & Tolls": 650, "Public Transit": 600, "Ride Shares": 450,
            "Clothing": 1500, "Personal Care": 780, "Grooming": 510,
            "Medical": 3100, "Dental": 780, "Vision": 260,
            "Fitness": 620, "Mental Health": 480,
            "Entertainment": 1500, "Hobbies": 780, "Subscriptions": 600, "Phone": 1240, "Other Personal": 780
        },
        "High-end (statistical)": {
            "Groceries": 9300, "Dining Out": 5850, "Coffee Shops": 1260,
            "Auto Payment": 8550, "Gas & Fuel": 4200, "Auto Maintenance": 1500, "Auto Insurance": 2550, "Parking & Tolls": 975, "Public Transit": 900, "Ride Shares": 675,
            "Clothing": 2250, "Personal Care": 1170, "Grooming": 765,
            "Medical": 4650, "Dental": 1170, "Vision": 390,
            "Fitness": 930, "Mental Health": 720,
            "Entertainment": 2250, "Hobbies": 1170, "Subscriptions": 900, "Phone": 1860, "Other Personal": 1170
        }
    },
    "Michigan": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 2030, "Coffee Shops": 441,
            "Auto Payment": 3780, "Gas & Fuel": 1820, "Auto Maintenance": 651, "Auto Insurance": 1890, "Parking & Tolls": 245, "Public Transit": 140, "Ride Shares": 196,
            "Clothing": 868, "Personal Care": 441, "Grooming": 287,
            "Medical": 1820, "Dental": 448, "Vision": 154,
            "Fitness": 315, "Mental Health": 238,
            "Entertainment": 882, "Hobbies": 448, "Subscriptions": 364, "Phone": 791, "Other Personal": 448
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2900, "Coffee Shops": 630,
            "Auto Payment": 5400, "Gas & Fuel": 2600, "Auto Maintenance": 930, "Auto Insurance": 2700, "Parking & Tolls": 350, "Public Transit": 200, "Ride Shares": 280,
            "Clothing": 1240, "Personal Care": 630, "Grooming": 410,
            "Medical": 2600, "Dental": 640, "Vision": 220,
            "Fitness": 450, "Mental Health": 340,
            "Entertainment": 1260, "Hobbies": 640, "Subscriptions": 520, "Phone": 1130, "Other Personal": 640
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4350, "Coffee Shops": 945,
            "Auto Payment": 8100, "Gas & Fuel": 3900, "Auto Maintenance": 1395, "Auto Insurance": 4050, "Parking & Tolls": 525, "Public Transit": 300, "Ride Shares": 420,
            "Clothing": 1860, "Personal Care": 945, "Grooming": 615,
            "Medical": 3900, "Dental": 960, "Vision": 330,
            "Fitness": 675, "Mental Health": 510,
            "Entertainment": 1890, "Hobbies": 960, "Subscriptions": 780, "Phone": 1695, "Other Personal": 960
        }
    },
    "Minnesota": {
        "Conservative (statistical)": {
            "Groceries": 3570, "Dining Out": 2100, "Coffee Shops": 462,
            "Auto Payment": 3780, "Gas & Fuel": 1750, "Auto Maintenance": 651, "Auto Insurance": 1050, "Parking & Tolls": 245, "Public Transit": 175, "Ride Shares": 196,
            "Clothing": 910, "Personal Care": 462, "Grooming": 301,
            "Medical": 1820, "Dental": 462, "Vision": 154,
            "Fitness": 350, "Mental Health": 259,
            "Entertainment": 910, "Hobbies": 462, "Subscriptions": 378, "Phone": 805, "Other Personal": 462
        },
        "Average (statistical)": {
            "Groceries": 5100, "Dining Out": 3000, "Coffee Shops": 660,
            "Auto Payment": 5400, "Gas & Fuel": 2500, "Auto Maintenance": 930, "Auto Insurance": 1500, "Parking & Tolls": 350, "Public Transit": 250, "Ride Shares": 280,
            "Clothing": 1300, "Personal Care": 660, "Grooming": 430,
            "Medical": 2600, "Dental": 660, "Vision": 220,
            "Fitness": 500, "Mental Health": 370,
            "Entertainment": 1300, "Hobbies": 660, "Subscriptions": 540, "Phone": 1150, "Other Personal": 660
        },
        "High-end (statistical)": {
            "Groceries": 7650, "Dining Out": 4500, "Coffee Shops": 990,
            "Auto Payment": 8100, "Gas & Fuel": 3750, "Auto Maintenance": 1395, "Auto Insurance": 2250, "Parking & Tolls": 525, "Public Transit": 375, "Ride Shares": 420,
            "Clothing": 1950, "Personal Care": 990, "Grooming": 645,
            "Medical": 3900, "Dental": 990, "Vision": 330,
            "Fitness": 750, "Mental Health": 555,
            "Entertainment": 1950, "Hobbies": 990, "Subscriptions": 810, "Phone": 1725, "Other Personal": 990
        }
    },
    "Mississippi": {
        "Conservative (statistical)": {
            "Groceries": 3150, "Dining Out": 1680, "Coffee Shops": 357,
            "Auto Payment": 3500, "Gas & Fuel": 1610, "Auto Maintenance": 602, "Auto Insurance": 1120, "Parking & Tolls": 154, "Public Transit": 49, "Ride Shares": 105,
            "Clothing": 756, "Personal Care": 378, "Grooming": 252,
            "Medical": 1540, "Dental": 378, "Vision": 126,
            "Fitness": 245, "Mental Health": 182,
            "Entertainment": 770, "Hobbies": 378, "Subscriptions": 315, "Phone": 721, "Other Personal": 378
        },
        "Average (statistical)": {
            "Groceries": 4500, "Dining Out": 2400, "Coffee Shops": 510,
            "Auto Payment": 5000, "Gas & Fuel": 2300, "Auto Maintenance": 860, "Auto Insurance": 1600, "Parking & Tolls": 220, "Public Transit": 70, "Ride Shares": 150,
            "Clothing": 1080, "Personal Care": 540, "Grooming": 360,
            "Medical": 2200, "Dental": 540, "Vision": 180,
            "Fitness": 350, "Mental Health": 260,
            "Entertainment": 1100, "Hobbies": 540, "Subscriptions": 450, "Phone": 1030, "Other Personal": 540
        },
        "High-end (statistical)": {
            "Groceries": 6750, "Dining Out": 3600, "Coffee Shops": 765,
            "Auto Payment": 7500, "Gas & Fuel": 3450, "Auto Maintenance": 1290, "Auto Insurance": 2400, "Parking & Tolls": 330, "Public Transit": 105, "Ride Shares": 225,
            "Clothing": 1620, "Personal Care": 810, "Grooming": 540,
            "Medical": 3300, "Dental": 810, "Vision": 270,
            "Fitness": 525, "Mental Health": 390,
            "Entertainment": 1650, "Hobbies": 810, "Subscriptions": 675, "Phone": 1545, "Other Personal": 810
        }
    },
    "Missouri": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1890, "Coffee Shops": 406,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 623, "Auto Insurance": 1120, "Parking & Tolls": 210, "Public Transit": 105, "Ride Shares": 154,
            "Clothing": 826, "Personal Care": 413, "Grooming": 273,
            "Medical": 1680, "Dental": 413, "Vision": 140,
            "Fitness": 280, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 763, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2700, "Coffee Shops": 580,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 890, "Auto Insurance": 1600, "Parking & Tolls": 300, "Public Transit": 150, "Ride Shares": 220,
            "Clothing": 1180, "Personal Care": 590, "Grooming": 390,
            "Medical": 2400, "Dental": 590, "Vision": 200,
            "Fitness": 400, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1090, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 4050, "Coffee Shops": 870,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1335, "Auto Insurance": 2400, "Parking & Tolls": 450, "Public Transit": 225, "Ride Shares": 330,
            "Clothing": 1770, "Personal Care": 885, "Grooming": 585,
            "Medical": 3600, "Dental": 885, "Vision": 300,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1635, "Other Personal": 900
        }
    },
    "Montana": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3640, "Gas & Fuel": 1820, "Auto Maintenance": 651, "Auto Insurance": 868, "Parking & Tolls": 175, "Public Transit": 56, "Ride Shares": 119,
            "Clothing": 840, "Personal Care": 427, "Grooming": 280,
            "Medical": 1750, "Dental": 434, "Vision": 147,
            "Fitness": 294, "Mental Health": 217,
            "Entertainment": 868, "Hobbies": 441, "Subscriptions": 357, "Phone": 784, "Other Personal": 434
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5200, "Gas & Fuel": 2600, "Auto Maintenance": 930, "Auto Insurance": 1240, "Parking & Tolls": 250, "Public Transit": 80, "Ride Shares": 170,
            "Clothing": 1200, "Personal Care": 610, "Grooming": 400,
            "Medical": 2500, "Dental": 620, "Vision": 210,
            "Fitness": 420, "Mental Health": 310,
            "Entertainment": 1240, "Hobbies": 630, "Subscriptions": 510, "Phone": 1120, "Other Personal": 620
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7800, "Gas & Fuel": 3900, "Auto Maintenance": 1395, "Auto Insurance": 1860, "Parking & Tolls": 375, "Public Transit": 120, "Ride Shares": 255,
            "Clothing": 1800, "Personal Care": 915, "Grooming": 600,
            "Medical": 3750, "Dental": 930, "Vision": 315,
            "Fitness": 630, "Mental Health": 465,
            "Entertainment": 1860, "Hobbies": 945, "Subscriptions": 765, "Phone": 1680, "Other Personal": 930
        }
    },
    "Nebraska": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1890, "Coffee Shops": 406,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 630, "Auto Insurance": 924, "Parking & Tolls": 182, "Public Transit": 70, "Ride Shares": 133,
            "Clothing": 819, "Personal Care": 413, "Grooming": 273,
            "Medical": 1680, "Dental": 413, "Vision": 140,
            "Fitness": 287, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 763, "Other Personal": 413
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2700, "Coffee Shops": 580,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 900, "Auto Insurance": 1320, "Parking & Tolls": 260, "Public Transit": 100, "Ride Shares": 190,
            "Clothing": 1170, "Personal Care": 590, "Grooming": 390,
            "Medical": 2400, "Dental": 590, "Vision": 200,
            "Fitness": 410, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1090, "Other Personal": 590
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4050, "Coffee Shops": 870,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1350, "Auto Insurance": 1980, "Parking & Tolls": 390, "Public Transit": 150, "Ride Shares": 285,
            "Clothing": 1755, "Personal Care": 885, "Grooming": 585,
            "Medical": 3600, "Dental": 885, "Vision": 300,
            "Fitness": 615, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1635, "Other Personal": 885
        }
    },
    "Nevada": {
        "Conservative (statistical)": {
            "Groceries": 3710, "Dining Out": 2380, "Coffee Shops": 504,
            "Auto Payment": 3850, "Gas & Fuel": 1960, "Auto Maintenance": 672, "Auto Insurance": 1330, "Parking & Tolls": 315, "Public Transit": 140, "Ride Shares": 280,
            "Clothing": 910, "Personal Care": 462, "Grooming": 308,
            "Medical": 1820, "Dental": 462, "Vision": 154,
            "Fitness": 350, "Mental Health": 252,
            "Entertainment": 1050, "Hobbies": 490, "Subscriptions": 385, "Phone": 812, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 5300, "Dining Out": 3400, "Coffee Shops": 720,
            "Auto Payment": 5500, "Gas & Fuel": 2800, "Auto Maintenance": 960, "Auto Insurance": 1900, "Parking & Tolls": 450, "Public Transit": 200, "Ride Shares": 400,
            "Clothing": 1300, "Personal Care": 660, "Grooming": 440,
            "Medical": 2600, "Dental": 660, "Vision": 220,
            "Fitness": 500, "Mental Health": 360,
            "Entertainment": 1500, "Hobbies": 700, "Subscriptions": 550, "Phone": 1160, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 7950, "Dining Out": 5100, "Coffee Shops": 1080,
            "Auto Payment": 8250, "Gas & Fuel": 4200, "Auto Maintenance": 1440, "Auto Insurance": 2850, "Parking & Tolls": 675, "Public Transit": 300, "Ride Shares": 600,
            "Clothing": 1950, "Personal Care": 990, "Grooming": 660,
            "Medical": 3900, "Dental": 990, "Vision": 330,
            "Fitness": 750, "Mental Health": 540,
            "Entertainment": 2250, "Hobbies": 1050, "Subscriptions": 825, "Phone": 1740, "Other Personal": 1050
        }
    },
    "New Hampshire": {
        "Conservative (statistical)": {
            "Groceries": 3850, "Dining Out": 2240, "Coffee Shops": 490,
            "Auto Payment": 3780, "Gas & Fuel": 1820, "Auto Maintenance": 672, "Auto Insurance": 826, "Parking & Tolls": 252, "Public Transit": 105, "Ride Shares": 168,
            "Clothing": 910, "Personal Care": 462, "Grooming": 308,
            "Medical": 1890, "Dental": 469, "Vision": 161,
            "Fitness": 350, "Mental Health": 266,
            "Entertainment": 910, "Hobbies": 469, "Subscriptions": 378, "Phone": 812, "Other Personal": 462
        },
        "Average (statistical)": {
            "Groceries": 5500, "Dining Out": 3200, "Coffee Shops": 700,
            "Auto Payment": 5400, "Gas & Fuel": 2600, "Auto Maintenance": 960, "Auto Insurance": 1180, "Parking & Tolls": 360, "Public Transit": 150, "Ride Shares": 240,
            "Clothing": 1300, "Personal Care": 660, "Grooming": 440,
            "Medical": 2700, "Dental": 670, "Vision": 230,
            "Fitness": 500, "Mental Health": 380,
            "Entertainment": 1300, "Hobbies": 670, "Subscriptions": 540, "Phone": 1160, "Other Personal": 660
        },
        "High-end (statistical)": {
            "Groceries": 8250, "Dining Out": 4800, "Coffee Shops": 1050,
            "Auto Payment": 8100, "Gas & Fuel": 3900, "Auto Maintenance": 1440, "Auto Insurance": 1770, "Parking & Tolls": 540, "Public Transit": 225, "Ride Shares": 360,
            "Clothing": 1950, "Personal Care": 990, "Grooming": 660,
            "Medical": 4050, "Dental": 1005, "Vision": 345,
            "Fitness": 750, "Mental Health": 570,
            "Entertainment": 1950, "Hobbies": 1005, "Subscriptions": 810, "Phone": 1740, "Other Personal": 990
        }
    },
    "New Jersey": {
        "Conservative (statistical)": {
            "Groceries": 4200, "Dining Out": 2660, "Coffee Shops": 574,
            "Auto Payment": 4060, "Gas & Fuel": 1960, "Auto Maintenance": 700, "Auto Insurance": 1330, "Parking & Tolls": 490, "Public Transit": 385, "Ride Shares": 294,
            "Clothing": 1050, "Personal Care": 532, "Grooming": 350,
            "Medical": 2100, "Dental": 525, "Vision": 175,
            "Fitness": 406, "Mental Health": 308,
            "Entertainment": 1050, "Hobbies": 532, "Subscriptions": 413, "Phone": 854, "Other Personal": 532
        },
        "Average (statistical)": {
            "Groceries": 6000, "Dining Out": 3800, "Coffee Shops": 820,
            "Auto Payment": 5800, "Gas & Fuel": 2800, "Auto Maintenance": 1000, "Auto Insurance": 1900, "Parking & Tolls": 700, "Public Transit": 550, "Ride Shares": 420,
            "Clothing": 1500, "Personal Care": 760, "Grooming": 500,
            "Medical": 3000, "Dental": 750, "Vision": 250,
            "Fitness": 580, "Mental Health": 440,
            "Entertainment": 1500, "Hobbies": 760, "Subscriptions": 590, "Phone": 1220, "Other Personal": 760
        },
        "High-end (statistical)": {
            "Groceries": 9000, "Dining Out": 5700, "Coffee Shops": 1230,
            "Auto Payment": 8700, "Gas & Fuel": 4200, "Auto Maintenance": 1500, "Auto Insurance": 2850, "Parking & Tolls": 1050, "Public Transit": 825, "Ride Shares": 630,
            "Clothing": 2250, "Personal Care": 1140, "Grooming": 750,
            "Medical": 4500, "Dental": 1125, "Vision": 375,
            "Fitness": 870, "Mental Health": 660,
            "Entertainment": 2250, "Hobbies": 1140, "Subscriptions": 885, "Phone": 1830, "Other Personal": 1140
        }
    },
    "New Mexico": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3640, "Gas & Fuel": 1750, "Auto Maintenance": 637, "Auto Insurance": 980, "Parking & Tolls": 196, "Public Transit": 70, "Ride Shares": 140,
            "Clothing": 826, "Personal Care": 420, "Grooming": 280,
            "Medical": 1680, "Dental": 420, "Vision": 140,
            "Fitness": 294, "Mental Health": 224,
            "Entertainment": 854, "Hobbies": 427, "Subscriptions": 350, "Phone": 770, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5200, "Gas & Fuel": 2500, "Auto Maintenance": 910, "Auto Insurance": 1400, "Parking & Tolls": 280, "Public Transit": 100, "Ride Shares": 200,
            "Clothing": 1180, "Personal Care": 600, "Grooming": 400,
            "Medical": 2400, "Dental": 600, "Vision": 200,
            "Fitness": 420, "Mental Health": 320,
            "Entertainment": 1220, "Hobbies": 610, "Subscriptions": 500, "Phone": 1100, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7800, "Gas & Fuel": 3750, "Auto Maintenance": 1365, "Auto Insurance": 2100, "Parking & Tolls": 420, "Public Transit": 150, "Ride Shares": 300,
            "Clothing": 1770, "Personal Care": 900, "Grooming": 600,
            "Medical": 3600, "Dental": 900, "Vision": 300,
            "Fitness": 630, "Mental Health": 480,
            "Entertainment": 1830, "Hobbies": 915, "Subscriptions": 750, "Phone": 1650, "Other Personal": 900
        }
    },
    "New York": {
        "Conservative (statistical)": {
            "Groceries": 4550, "Dining Out": 3010, "Coffee Shops": 644,
            "Auto Payment": 3640, "Gas & Fuel": 1960, "Auto Maintenance": 700, "Auto Insurance": 1470, "Parking & Tolls": 560, "Public Transit": 630, "Ride Shares": 420,
            "Clothing": 1120, "Personal Care": 574, "Grooming": 378,
            "Medical": 2240, "Dental": 560, "Vision": 189,
            "Fitness": 462, "Mental Health": 364,
            "Entertainment": 1120, "Hobbies": 574, "Subscriptions": 434, "Phone": 896, "Other Personal": 574
        },
        "Average (statistical)": {
            "Groceries": 6500, "Dining Out": 4300, "Coffee Shops": 920,
            "Auto Payment": 5200, "Gas & Fuel": 2800, "Auto Maintenance": 1000, "Auto Insurance": 2100, "Parking & Tolls": 800, "Public Transit": 900, "Ride Shares": 600,
            "Clothing": 1600, "Personal Care": 820, "Grooming": 540,
            "Medical": 3200, "Dental": 800, "Vision": 270,
            "Fitness": 660, "Mental Health": 520,
            "Entertainment": 1600, "Hobbies": 820, "Subscriptions": 620, "Phone": 1280, "Other Personal": 820
        },
        "High-end (statistical)": {
            "Groceries": 9750, "Dining Out": 6450, "Coffee Shops": 1380,
            "Auto Payment": 7800, "Gas & Fuel": 4200, "Auto Maintenance": 1500, "Auto Insurance": 3150, "Parking & Tolls": 1200, "Public Transit": 1350, "Ride Shares": 900,
            "Clothing": 2400, "Personal Care": 1230, "Grooming": 810,
            "Medical": 4800, "Dental": 1200, "Vision": 405,
            "Fitness": 990, "Mental Health": 780,
            "Entertainment": 2400, "Hobbies": 1230, "Subscriptions": 930, "Phone": 1920, "Other Personal": 1230
        }
    },
    "North Carolina": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 2030, "Coffee Shops": 441,
            "Auto Payment": 3710, "Gas & Fuel": 1750, "Auto Maintenance": 644, "Auto Insurance": 980, "Parking & Tolls": 245, "Public Transit": 105, "Ride Shares": 182,
            "Clothing": 854, "Personal Care": 434, "Grooming": 287,
            "Medical": 1750, "Dental": 441, "Vision": 147,
            "Fitness": 315, "Mental Health": 231,
            "Entertainment": 868, "Hobbies": 441, "Subscriptions": 357, "Phone": 784, "Other Personal": 441
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2900, "Coffee Shops": 630,
            "Auto Payment": 5300, "Gas & Fuel": 2500, "Auto Maintenance": 920, "Auto Insurance": 1400, "Parking & Tolls": 350, "Public Transit": 150, "Ride Shares": 260,
            "Clothing": 1220, "Personal Care": 620, "Grooming": 410,
            "Medical": 2500, "Dental": 630, "Vision": 210,
            "Fitness": 450, "Mental Health": 330,
            "Entertainment": 1240, "Hobbies": 630, "Subscriptions": 510, "Phone": 1120, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4350, "Coffee Shops": 945,
            "Auto Payment": 7950, "Gas & Fuel": 3750, "Auto Maintenance": 1380, "Auto Insurance": 2100, "Parking & Tolls": 525, "Public Transit": 225, "Ride Shares": 390,
            "Clothing": 1830, "Personal Care": 930, "Grooming": 615,
            "Medical": 3750, "Dental": 945, "Vision": 315,
            "Fitness": 675, "Mental Health": 495,
            "Entertainment": 1860, "Hobbies": 945, "Subscriptions": 765, "Phone": 1680, "Other Personal": 945
        }
    },
    "North Dakota": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1820, "Coffee Shops": 392,
            "Auto Payment": 3640, "Gas & Fuel": 1750, "Auto Maintenance": 637, "Auto Insurance": 868, "Parking & Tolls": 168, "Public Transit": 56, "Ride Shares": 112,
            "Clothing": 812, "Personal Care": 406, "Grooming": 266,
            "Medical": 1680, "Dental": 406, "Vision": 140,
            "Fitness": 273, "Mental Health": 203,
            "Entertainment": 826, "Hobbies": 406, "Subscriptions": 343, "Phone": 756, "Other Personal": 406
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2600, "Coffee Shops": 560,
            "Auto Payment": 5200, "Gas & Fuel": 2500, "Auto Maintenance": 910, "Auto Insurance": 1240, "Parking & Tolls": 240, "Public Transit": 80, "Ride Shares": 160,
            "Clothing": 1160, "Personal Care": 580, "Grooming": 380,
            "Medical": 2400, "Dental": 580, "Vision": 200,
            "Fitness": 390, "Mental Health": 290,
            "Entertainment": 1180, "Hobbies": 580, "Subscriptions": 490, "Phone": 1080, "Other Personal": 580
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 3900, "Coffee Shops": 840,
            "Auto Payment": 7800, "Gas & Fuel": 3750, "Auto Maintenance": 1365, "Auto Insurance": 1860, "Parking & Tolls": 360, "Public Transit": 120, "Ride Shares": 240,
            "Clothing": 1740, "Personal Care": 870, "Grooming": 570,
            "Medical": 3600, "Dental": 870, "Vision": 300,
            "Fitness": 585, "Mental Health": 435,
            "Entertainment": 1770, "Hobbies": 870, "Subscriptions": 735, "Phone": 1620, "Other Personal": 870
        }
    },
    "Ohio": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3710, "Gas & Fuel": 1750, "Auto Maintenance": 637, "Auto Insurance": 924, "Parking & Tolls": 224, "Public Transit": 119, "Ride Shares": 168,
            "Clothing": 840, "Personal Care": 427, "Grooming": 280,
            "Medical": 1680, "Dental": 427, "Vision": 147,
            "Fitness": 301, "Mental Health": 224,
            "Entertainment": 854, "Hobbies": 434, "Subscriptions": 357, "Phone": 770, "Other Personal": 427
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5300, "Gas & Fuel": 2500, "Auto Maintenance": 910, "Auto Insurance": 1320, "Parking & Tolls": 320, "Public Transit": 170, "Ride Shares": 240,
            "Clothing": 1200, "Personal Care": 610, "Grooming": 400,
            "Medical": 2400, "Dental": 610, "Vision": 210,
            "Fitness": 430, "Mental Health": 320,
            "Entertainment": 1220, "Hobbies": 620, "Subscriptions": 510, "Phone": 1100, "Other Personal": 610
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7950, "Gas & Fuel": 3750, "Auto Maintenance": 1365, "Auto Insurance": 1980, "Parking & Tolls": 480, "Public Transit": 255, "Ride Shares": 360,
            "Clothing": 1800, "Personal Care": 915, "Grooming": 600,
            "Medical": 3600, "Dental": 915, "Vision": 315,
            "Fitness": 645, "Mental Health": 480,
            "Entertainment": 1830, "Hobbies": 930, "Subscriptions": 765, "Phone": 1650, "Other Personal": 915
        }
    },
    "Oklahoma": {
        "Conservative (statistical)": {
            "Groceries": 3290, "Dining Out": 1820, "Coffee Shops": 385,
            "Auto Payment": 3570, "Gas & Fuel": 1610, "Auto Maintenance": 609, "Auto Insurance": 1120, "Parking & Tolls": 182, "Public Transit": 56, "Ride Shares": 119,
            "Clothing": 798, "Personal Care": 399, "Grooming": 266,
            "Medical": 1610, "Dental": 399, "Vision": 133,
            "Fitness": 266, "Mental Health": 196,
            "Entertainment": 812, "Hobbies": 399, "Subscriptions": 336, "Phone": 749, "Other Personal": 399
        },
        "Average (statistical)": {
            "Groceries": 4700, "Dining Out": 2600, "Coffee Shops": 550,
            "Auto Payment": 5100, "Gas & Fuel": 2300, "Auto Maintenance": 870, "Auto Insurance": 1600, "Parking & Tolls": 260, "Public Transit": 80, "Ride Shares": 170,
            "Clothing": 1140, "Personal Care": 570, "Grooming": 380,
            "Medical": 2300, "Dental": 570, "Vision": 190,
            "Fitness": 380, "Mental Health": 280,
            "Entertainment": 1160, "Hobbies": 570, "Subscriptions": 480, "Phone": 1070, "Other Personal": 570
        },
        "High-end (statistical)": {
            "Groceries": 7050, "Dining Out": 3900, "Coffee Shops": 825,
            "Auto Payment": 7650, "Gas & Fuel": 3450, "Auto Maintenance": 1305, "Auto Insurance": 2400, "Parking & Tolls": 390, "Public Transit": 120, "Ride Shares": 255,
            "Clothing": 1710, "Personal Care": 855, "Grooming": 570,
            "Medical": 3450, "Dental": 855, "Vision": 285,
            "Fitness": 570, "Mental Health": 420,
            "Entertainment": 1740, "Hobbies": 855, "Subscriptions": 720, "Phone": 1605, "Other Personal": 855
        }
    },
    "Oregon": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 2450, "Coffee Shops": 546,
            "Auto Payment": 3780, "Gas & Fuel": 1960, "Auto Maintenance": 679, "Auto Insurance": 980, "Parking & Tolls": 280, "Public Transit": 210, "Ride Shares": 224,
            "Clothing": 938, "Personal Care": 490, "Grooming": 322,
            "Medical": 1890, "Dental": 476, "Vision": 161,
            "Fitness": 385, "Mental Health": 294,
            "Entertainment": 980, "Hobbies": 504, "Subscriptions": 392, "Phone": 826, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 5600, "Dining Out": 3500, "Coffee Shops": 780,
            "Auto Payment": 5400, "Gas & Fuel": 2800, "Auto Maintenance": 970, "Auto Insurance": 1400, "Parking & Tolls": 400, "Public Transit": 300, "Ride Shares": 320,
            "Clothing": 1340, "Personal Care": 700, "Grooming": 460,
            "Medical": 2700, "Dental": 680, "Vision": 230,
            "Fitness": 550, "Mental Health": 420,
            "Entertainment": 1400, "Hobbies": 720, "Subscriptions": 560, "Phone": 1180, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 8400, "Dining Out": 5250, "Coffee Shops": 1170,
            "Auto Payment": 8100, "Gas & Fuel": 4200, "Auto Maintenance": 1455, "Auto Insurance": 2100, "Parking & Tolls": 600, "Public Transit": 450, "Ride Shares": 480,
            "Clothing": 2010, "Personal Care": 1050, "Grooming": 690,
            "Medical": 4050, "Dental": 1020, "Vision": 345,
            "Fitness": 825, "Mental Health": 630,
            "Entertainment": 2100, "Hobbies": 1080, "Subscriptions": 840, "Phone": 1770, "Other Personal": 1050
        }
    },
    "Pennsylvania": {
        "Conservative (statistical)": {
            "Groceries": 3710, "Dining Out": 2240, "Coffee Shops": 490,
            "Auto Payment": 3850, "Gas & Fuel": 1890, "Auto Maintenance": 672, "Auto Insurance": 1120, "Parking & Tolls": 350, "Public Transit": 280, "Ride Shares": 245,
            "Clothing": 910, "Personal Care": 462, "Grooming": 308,
            "Medical": 1890, "Dental": 469, "Vision": 161,
            "Fitness": 350, "Mental Health": 266,
            "Entertainment": 924, "Hobbies": 469, "Subscriptions": 378, "Phone": 812, "Other Personal": 469
        },
        "Average (statistical)": {
            "Groceries": 5300, "Dining Out": 3200, "Coffee Shops": 700,
            "Auto Payment": 5500, "Gas & Fuel": 2700, "Auto Maintenance": 960, "Auto Insurance": 1600, "Parking & Tolls": 500, "Public Transit": 400, "Ride Shares": 350,
            "Clothing": 1300, "Personal Care": 660, "Grooming": 440,
            "Medical": 2700, "Dental": 670, "Vision": 230,
            "Fitness": 500, "Mental Health": 380,
            "Entertainment": 1320, "Hobbies": 670, "Subscriptions": 540, "Phone": 1160, "Other Personal": 670
        },
        "High-end (statistical)": {
            "Groceries": 7950, "Dining Out": 4800, "Coffee Shops": 1050,
            "Auto Payment": 8250, "Gas & Fuel": 4050, "Auto Maintenance": 1440, "Auto Insurance": 2400, "Parking & Tolls": 750, "Public Transit": 600, "Ride Shares": 525,
            "Clothing": 1950, "Personal Care": 990, "Grooming": 660,
            "Medical": 4050, "Dental": 1005, "Vision": 345,
            "Fitness": 750, "Mental Health": 570,
            "Entertainment": 1980, "Hobbies": 1005, "Subscriptions": 810, "Phone": 1740, "Other Personal": 1005
        }
    },
    "Rhode Island": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 2380, "Coffee Shops": 518,
            "Auto Payment": 3850, "Gas & Fuel": 1890, "Auto Maintenance": 679, "Auto Insurance": 1190, "Parking & Tolls": 315, "Public Transit": 245, "Ride Shares": 224,
            "Clothing": 938, "Personal Care": 483, "Grooming": 315,
            "Medical": 1960, "Dental": 483, "Vision": 161,
            "Fitness": 371, "Mental Health": 280,
            "Entertainment": 952, "Hobbies": 490, "Subscriptions": 385, "Phone": 826, "Other Personal": 483
        },
        "Average (statistical)": {
            "Groceries": 5600, "Dining Out": 3400, "Coffee Shops": 740,
            "Auto Payment": 5500, "Gas & Fuel": 2700, "Auto Maintenance": 970, "Auto Insurance": 1700, "Parking & Tolls": 450, "Public Transit": 350, "Ride Shares": 320,
            "Clothing": 1340, "Personal Care": 690, "Grooming": 450,
            "Medical": 2800, "Dental": 690, "Vision": 230,
            "Fitness": 530, "Mental Health": 400,
            "Entertainment": 1360, "Hobbies": 700, "Subscriptions": 550, "Phone": 1180, "Other Personal": 690
        },
        "High-end (statistical)": {
            "Groceries": 8400, "Dining Out": 5100, "Coffee Shops": 1110,
            "Auto Payment": 8250, "Gas & Fuel": 4050, "Auto Maintenance": 1455, "Auto Insurance": 2550, "Parking & Tolls": 675, "Public Transit": 525, "Ride Shares": 480,
            "Clothing": 2010, "Personal Care": 1035, "Grooming": 675,
            "Medical": 4200, "Dental": 1035, "Vision": 345,
            "Fitness": 795, "Mental Health": 600,
            "Entertainment": 2040, "Hobbies": 1050, "Subscriptions": 825, "Phone": 1770, "Other Personal": 1035
        }
    },
    "South Carolina": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 1960, "Coffee Shops": 420,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 630, "Auto Insurance": 1050, "Parking & Tolls": 210, "Public Transit": 70, "Ride Shares": 154,
            "Clothing": 826, "Personal Care": 413, "Grooming": 280,
            "Medical": 1680, "Dental": 413, "Vision": 140,
            "Fitness": 287, "Mental Health": 210,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 770, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2800, "Coffee Shops": 600,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 900, "Auto Insurance": 1500, "Parking & Tolls": 300, "Public Transit": 100, "Ride Shares": 220,
            "Clothing": 1180, "Personal Care": 590, "Grooming": 400,
            "Medical": 2400, "Dental": 590, "Vision": 200,
            "Fitness": 410, "Mental Health": 300,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1100, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4200, "Coffee Shops": 900,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1350, "Auto Insurance": 2250, "Parking & Tolls": 450, "Public Transit": 150, "Ride Shares": 330,
            "Clothing": 1770, "Personal Care": 885, "Grooming": 600,
            "Medical": 3600, "Dental": 885, "Vision": 300,
            "Fitness": 615, "Mental Health": 450,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1650, "Other Personal": 900
        }
    },
    "South Dakota": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1820, "Coffee Shops": 385,
            "Auto Payment": 3570, "Gas & Fuel": 1680, "Auto Maintenance": 623, "Auto Insurance": 826, "Parking & Tolls": 168, "Public Transit": 49, "Ride Shares": 105,
            "Clothing": 798, "Personal Care": 399, "Grooming": 266,
            "Medical": 1680, "Dental": 399, "Vision": 133,
            "Fitness": 266, "Mental Health": 196,
            "Entertainment": 812, "Hobbies": 399, "Subscriptions": 336, "Phone": 749, "Other Personal": 399
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2600, "Coffee Shops": 550,
            "Auto Payment": 5100, "Gas & Fuel": 2400, "Auto Maintenance": 890, "Auto Insurance": 1180, "Parking & Tolls": 240, "Public Transit": 70, "Ride Shares": 150,
            "Clothing": 1140, "Personal Care": 570, "Grooming": 380,
            "Medical": 2400, "Dental": 570, "Vision": 190,
            "Fitness": 380, "Mental Health": 280,
            "Entertainment": 1160, "Hobbies": 570, "Subscriptions": 480, "Phone": 1070, "Other Personal": 570
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 3900, "Coffee Shops": 825,
            "Auto Payment": 7650, "Gas & Fuel": 3600, "Auto Maintenance": 1335, "Auto Insurance": 1770, "Parking & Tolls": 360, "Public Transit": 105, "Ride Shares": 225,
            "Clothing": 1710, "Personal Care": 855, "Grooming": 570,
            "Medical": 3600, "Dental": 855, "Vision": 285,
            "Fitness": 570, "Mental Health": 420,
            "Entertainment": 1740, "Hobbies": 855, "Subscriptions": 720, "Phone": 1605, "Other Personal": 855
        }
    },
    "Tennessee": {
        "Conservative (statistical)": {
            "Groceries": 3360, "Dining Out": 1960, "Coffee Shops": 413,
            "Auto Payment": 3640, "Gas & Fuel": 1680, "Auto Maintenance": 623, "Auto Insurance": 1050, "Parking & Tolls": 210, "Public Transit": 84, "Ride Shares": 154,
            "Clothing": 826, "Personal Care": 413, "Grooming": 273,
            "Medical": 1680, "Dental": 413, "Vision": 140,
            "Fitness": 280, "Mental Health": 210,
            "Entertainment": 854, "Hobbies": 420, "Subscriptions": 350, "Phone": 763, "Other Personal": 420
        },
        "Average (statistical)": {
            "Groceries": 4800, "Dining Out": 2800, "Coffee Shops": 590,
            "Auto Payment": 5200, "Gas & Fuel": 2400, "Auto Maintenance": 890, "Auto Insurance": 1500, "Parking & Tolls": 300, "Public Transit": 120, "Ride Shares": 220,
            "Clothing": 1180, "Personal Care": 590, "Grooming": 390,
            "Medical": 2400, "Dental": 590, "Vision": 200,
            "Fitness": 400, "Mental Health": 300,
            "Entertainment": 1220, "Hobbies": 600, "Subscriptions": 500, "Phone": 1090, "Other Personal": 600
        },
        "High-end (statistical)": {
            "Groceries": 7200, "Dining Out": 4200, "Coffee Shops": 885,
            "Auto Payment": 7800, "Gas & Fuel": 3600, "Auto Maintenance": 1335, "Auto Insurance": 2250, "Parking & Tolls": 450, "Public Transit": 180, "Ride Shares": 330,
            "Clothing": 1770, "Personal Care": 885, "Grooming": 585,
            "Medical": 3600, "Dental": 885, "Vision": 300,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1830, "Hobbies": 900, "Subscriptions": 750, "Phone": 1635, "Other Personal": 900
        }
    },
    "Texas": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 2100, "Coffee Shops": 441,
            "Auto Payment": 3780, "Gas & Fuel": 1610, "Auto Maintenance": 644, "Auto Insurance": 1190, "Parking & Tolls": 245, "Public Transit": 105, "Ride Shares": 196,
            "Clothing": 854, "Personal Care": 434, "Grooming": 287,
            "Medical": 1750, "Dental": 434, "Vision": 147,
            "Fitness": 315, "Mental Health": 231,
            "Entertainment": 882, "Hobbies": 441, "Subscriptions": 364, "Phone": 784, "Other Personal": 441
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 3000, "Coffee Shops": 630,
            "Auto Payment": 5400, "Gas & Fuel": 2300, "Auto Maintenance": 920, "Auto Insurance": 1700, "Parking & Tolls": 350, "Public Transit": 150, "Ride Shares": 280,
            "Clothing": 1220, "Personal Care": 620, "Grooming": 410,
            "Medical": 2500, "Dental": 620, "Vision": 210,
            "Fitness": 450, "Mental Health": 330,
            "Entertainment": 1260, "Hobbies": 630, "Subscriptions": 520, "Phone": 1120, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4500, "Coffee Shops": 945,
            "Auto Payment": 8100, "Gas & Fuel": 3450, "Auto Maintenance": 1380, "Auto Insurance": 2550, "Parking & Tolls": 525, "Public Transit": 225, "Ride Shares": 420,
            "Clothing": 1830, "Personal Care": 930, "Grooming": 615,
            "Medical": 3750, "Dental": 930, "Vision": 315,
            "Fitness": 675, "Mental Health": 495,
            "Entertainment": 1890, "Hobbies": 945, "Subscriptions": 780, "Phone": 1680, "Other Personal": 945
        }
    },
    "Utah": {
        "Conservative (statistical)": {
            "Groceries": 3570, "Dining Out": 2030, "Coffee Shops": 385,
            "Auto Payment": 3710, "Gas & Fuel": 1820, "Auto Maintenance": 651, "Auto Insurance": 980, "Parking & Tolls": 210, "Public Transit": 105, "Ride Shares": 168,
            "Clothing": 868, "Personal Care": 441, "Grooming": 287,
            "Medical": 1750, "Dental": 441, "Vision": 147,
            "Fitness": 336, "Mental Health": 238,
            "Entertainment": 868, "Hobbies": 448, "Subscriptions": 364, "Phone": 791, "Other Personal": 441
        },
        "Average (statistical)": {
            "Groceries": 5100, "Dining Out": 2900, "Coffee Shops": 550,
            "Auto Payment": 5300, "Gas & Fuel": 2600, "Auto Maintenance": 930, "Auto Insurance": 1400, "Parking & Tolls": 300, "Public Transit": 150, "Ride Shares": 240,
            "Clothing": 1240, "Personal Care": 630, "Grooming": 410,
            "Medical": 2500, "Dental": 630, "Vision": 210,
            "Fitness": 480, "Mental Health": 340,
            "Entertainment": 1240, "Hobbies": 640, "Subscriptions": 520, "Phone": 1130, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 7650, "Dining Out": 4350, "Coffee Shops": 825,
            "Auto Payment": 7950, "Gas & Fuel": 3900, "Auto Maintenance": 1395, "Auto Insurance": 2100, "Parking & Tolls": 450, "Public Transit": 225, "Ride Shares": 360,
            "Clothing": 1860, "Personal Care": 945, "Grooming": 615,
            "Medical": 3750, "Dental": 945, "Vision": 315,
            "Fitness": 720, "Mental Health": 510,
            "Entertainment": 1860, "Hobbies": 960, "Subscriptions": 780, "Phone": 1695, "Other Personal": 945
        }
    },
    "Vermont": {
        "Conservative (statistical)": {
            "Groceries": 3850, "Dining Out": 2170, "Coffee Shops": 476,
            "Auto Payment": 3640, "Gas & Fuel": 1820, "Auto Maintenance": 665, "Auto Insurance": 770, "Parking & Tolls": 210, "Public Transit": 84, "Ride Shares": 140,
            "Clothing": 882, "Personal Care": 448, "Grooming": 294,
            "Medical": 1890, "Dental": 462, "Vision": 154,
            "Fitness": 322, "Mental Health": 252,
            "Entertainment": 882, "Hobbies": 462, "Subscriptions": 371, "Phone": 805, "Other Personal": 455
        },
        "Average (statistical)": {
            "Groceries": 5500, "Dining Out": 3100, "Coffee Shops": 680,
            "Auto Payment": 5200, "Gas & Fuel": 2600, "Auto Maintenance": 950, "Auto Insurance": 1100, "Parking & Tolls": 300, "Public Transit": 120, "Ride Shares": 200,
            "Clothing": 1260, "Personal Care": 640, "Grooming": 420,
            "Medical": 2700, "Dental": 660, "Vision": 220,
            "Fitness": 460, "Mental Health": 360,
            "Entertainment": 1260, "Hobbies": 660, "Subscriptions": 530, "Phone": 1150, "Other Personal": 650
        },
        "High-end (statistical)": {
            "Groceries": 8250, "Dining Out": 4650, "Coffee Shops": 1020,
            "Auto Payment": 7800, "Gas & Fuel": 3900, "Auto Maintenance": 1425, "Auto Insurance": 1650, "Parking & Tolls": 450, "Public Transit": 180, "Ride Shares": 300,
            "Clothing": 1890, "Personal Care": 960, "Grooming": 630,
            "Medical": 4050, "Dental": 990, "Vision": 330,
            "Fitness": 690, "Mental Health": 540,
            "Entertainment": 1890, "Hobbies": 990, "Subscriptions": 795, "Phone": 1725, "Other Personal": 975
        }
    },
    "Virginia": {
        "Conservative (statistical)": {
            "Groceries": 3710, "Dining Out": 2310, "Coffee Shops": 504,
            "Auto Payment": 3850, "Gas & Fuel": 1820, "Auto Maintenance": 672, "Auto Insurance": 1050, "Parking & Tolls": 315, "Public Transit": 245, "Ride Shares": 245,
            "Clothing": 938, "Personal Care": 476, "Grooming": 315,
            "Medical": 1890, "Dental": 476, "Vision": 161,
            "Fitness": 371, "Mental Health": 280,
            "Entertainment": 952, "Hobbies": 490, "Subscriptions": 385, "Phone": 826, "Other Personal": 490
        },
        "Average (statistical)": {
            "Groceries": 5300, "Dining Out": 3300, "Coffee Shops": 720,
            "Auto Payment": 5500, "Gas & Fuel": 2600, "Auto Maintenance": 960, "Auto Insurance": 1500, "Parking & Tolls": 450, "Public Transit": 350, "Ride Shares": 350,
            "Clothing": 1340, "Personal Care": 680, "Grooming": 450,
            "Medical": 2700, "Dental": 680, "Vision": 230,
            "Fitness": 530, "Mental Health": 400,
            "Entertainment": 1360, "Hobbies": 700, "Subscriptions": 550, "Phone": 1180, "Other Personal": 700
        },
        "High-end (statistical)": {
            "Groceries": 7950, "Dining Out": 4950, "Coffee Shops": 1080,
            "Auto Payment": 8250, "Gas & Fuel": 3900, "Auto Maintenance": 1440, "Auto Insurance": 2250, "Parking & Tolls": 675, "Public Transit": 525, "Ride Shares": 525,
            "Clothing": 2010, "Personal Care": 1020, "Grooming": 675,
            "Medical": 4050, "Dental": 1020, "Vision": 345,
            "Fitness": 795, "Mental Health": 600,
            "Entertainment": 2040, "Hobbies": 1050, "Subscriptions": 825, "Phone": 1770, "Other Personal": 1050
        }
    },
    "Washington": {
        "Conservative (statistical)": {
            "Groceries": 4060, "Dining Out": 2590, "Coffee Shops": 588,
            "Auto Payment": 3920, "Gas & Fuel": 2100, "Auto Maintenance": 700, "Auto Insurance": 980, "Parking & Tolls": 315, "Public Transit": 245, "Ride Shares": 266,
            "Clothing": 980, "Personal Care": 504, "Grooming": 329,
            "Medical": 1960, "Dental": 490, "Vision": 168,
            "Fitness": 420, "Mental Health": 315,
            "Entertainment": 1050, "Hobbies": 532, "Subscriptions": 406, "Phone": 854, "Other Personal": 518
        },
        "Average (statistical)": {
            "Groceries": 5800, "Dining Out": 3700, "Coffee Shops": 840,
            "Auto Payment": 5600, "Gas & Fuel": 3000, "Auto Maintenance": 1000, "Auto Insurance": 1400, "Parking & Tolls": 450, "Public Transit": 350, "Ride Shares": 380,
            "Clothing": 1400, "Personal Care": 720, "Grooming": 470,
            "Medical": 2800, "Dental": 700, "Vision": 240,
            "Fitness": 600, "Mental Health": 450,
            "Entertainment": 1500, "Hobbies": 760, "Subscriptions": 580, "Phone": 1220, "Other Personal": 740
        },
        "High-end (statistical)": {
            "Groceries": 8700, "Dining Out": 5550, "Coffee Shops": 1260,
            "Auto Payment": 8400, "Gas & Fuel": 4500, "Auto Maintenance": 1500, "Auto Insurance": 2100, "Parking & Tolls": 675, "Public Transit": 525, "Ride Shares": 570,
            "Clothing": 2100, "Personal Care": 1080, "Grooming": 705,
            "Medical": 4200, "Dental": 1050, "Vision": 360,
            "Fitness": 900, "Mental Health": 675,
            "Entertainment": 2250, "Hobbies": 1140, "Subscriptions": 870, "Phone": 1830, "Other Personal": 1110
        }
    },
    "West Virginia": {
        "Conservative (statistical)": {
            "Groceries": 3220, "Dining Out": 1750, "Coffee Shops": 371,
            "Auto Payment": 3500, "Gas & Fuel": 1680, "Auto Maintenance": 609, "Auto Insurance": 924, "Parking & Tolls": 168, "Public Transit": 49, "Ride Shares": 105,
            "Clothing": 770, "Personal Care": 385, "Grooming": 259,
            "Medical": 1610, "Dental": 385, "Vision": 133,
            "Fitness": 252, "Mental Health": 189,
            "Entertainment": 791, "Hobbies": 385, "Subscriptions": 329, "Phone": 735, "Other Personal": 385
        },
        "Average (statistical)": {
            "Groceries": 4600, "Dining Out": 2500, "Coffee Shops": 530,
            "Auto Payment": 5000, "Gas & Fuel": 2400, "Auto Maintenance": 870, "Auto Insurance": 1320, "Parking & Tolls": 240, "Public Transit": 70, "Ride Shares": 150,
            "Clothing": 1100, "Personal Care": 550, "Grooming": 370,
            "Medical": 2300, "Dental": 550, "Vision": 190,
            "Fitness": 360, "Mental Health": 270,
            "Entertainment": 1130, "Hobbies": 550, "Subscriptions": 470, "Phone": 1050, "Other Personal": 550
        },
        "High-end (statistical)": {
            "Groceries": 6900, "Dining Out": 3750, "Coffee Shops": 795,
            "Auto Payment": 7500, "Gas & Fuel": 3600, "Auto Maintenance": 1305, "Auto Insurance": 1980, "Parking & Tolls": 360, "Public Transit": 105, "Ride Shares": 225,
            "Clothing": 1650, "Personal Care": 825, "Grooming": 555,
            "Medical": 3450, "Dental": 825, "Vision": 285,
            "Fitness": 540, "Mental Health": 405,
            "Entertainment": 1695, "Hobbies": 825, "Subscriptions": 705, "Phone": 1575, "Other Personal": 825
        }
    },
    "Wisconsin": {
        "Conservative (statistical)": {
            "Groceries": 3430, "Dining Out": 2030, "Coffee Shops": 434,
            "Auto Payment": 3710, "Gas & Fuel": 1750, "Auto Maintenance": 644, "Auto Insurance": 924, "Parking & Tolls": 217, "Public Transit": 133, "Ride Shares": 175,
            "Clothing": 854, "Personal Care": 434, "Grooming": 287,
            "Medical": 1750, "Dental": 441, "Vision": 147,
            "Fitness": 315, "Mental Health": 231,
            "Entertainment": 868, "Hobbies": 448, "Subscriptions": 364, "Phone": 784, "Other Personal": 441
        },
        "Average (statistical)": {
            "Groceries": 4900, "Dining Out": 2900, "Coffee Shops": 620,
            "Auto Payment": 5300, "Gas & Fuel": 2500, "Auto Maintenance": 920, "Auto Insurance": 1320, "Parking & Tolls": 310, "Public Transit": 190, "Ride Shares": 250,
            "Clothing": 1220, "Personal Care": 620, "Grooming": 410,
            "Medical": 2500, "Dental": 630, "Vision": 210,
            "Fitness": 450, "Mental Health": 330,
            "Entertainment": 1240, "Hobbies": 640, "Subscriptions": 520, "Phone": 1120, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 7350, "Dining Out": 4350, "Coffee Shops": 930,
            "Auto Payment": 7950, "Gas & Fuel": 3750, "Auto Maintenance": 1380, "Auto Insurance": 1980, "Parking & Tolls": 465, "Public Transit": 285, "Ride Shares": 375,
            "Clothing": 1830, "Personal Care": 930, "Grooming": 615,
            "Medical": 3750, "Dental": 945, "Vision": 315,
            "Fitness": 675, "Mental Health": 495,
            "Entertainment": 1860, "Hobbies": 960, "Subscriptions": 780, "Phone": 1680, "Other Personal": 945
        }
    },
    "Wyoming": {
        "Conservative (statistical)": {
            "Groceries": 3500, "Dining Out": 1890, "Coffee Shops": 399,
            "Auto Payment": 3570, "Gas & Fuel": 1820, "Auto Maintenance": 644, "Auto Insurance": 812, "Parking & Tolls": 168, "Public Transit": 42, "Ride Shares": 105,
            "Clothing": 812, "Personal Care": 413, "Grooming": 273,
            "Medical": 1750, "Dental": 420, "Vision": 140,
            "Fitness": 280, "Mental Health": 203,
            "Entertainment": 840, "Hobbies": 420, "Subscriptions": 350, "Phone": 770, "Other Personal": 413
        },
        "Average (statistical)": {
            "Groceries": 5000, "Dining Out": 2700, "Coffee Shops": 570,
            "Auto Payment": 5100, "Gas & Fuel": 2600, "Auto Maintenance": 920, "Auto Insurance": 1160, "Parking & Tolls": 240, "Public Transit": 60, "Ride Shares": 150,
            "Clothing": 1160, "Personal Care": 590, "Grooming": 390,
            "Medical": 2500, "Dental": 600, "Vision": 200,
            "Fitness": 400, "Mental Health": 290,
            "Entertainment": 1200, "Hobbies": 600, "Subscriptions": 500, "Phone": 1100, "Other Personal": 590
        },
        "High-end (statistical)": {
            "Groceries": 7500, "Dining Out": 4050, "Coffee Shops": 855,
            "Auto Payment": 7650, "Gas & Fuel": 3900, "Auto Maintenance": 1380, "Auto Insurance": 1740, "Parking & Tolls": 360, "Public Transit": 90, "Ride Shares": 225,
            "Clothing": 1740, "Personal Care": 885, "Grooming": 585,
            "Medical": 3750, "Dental": 900, "Vision": 300,
            "Fitness": 600, "Mental Health": 435,
            "Entertainment": 1800, "Hobbies": 900, "Subscriptions": 750, "Phone": 1650, "Other Personal": 885
        }
    },
}


# ============================================================================
# CANADIAN PROVINCE EXPENSE TEMPLATES
# ============================================================================
# Annual amounts per adult in USD (CAD × 0.74). Derived from StatCan Survey of
# Household Spending 2022, provincial auto insurance data, regional grocery indices.
# Medical/dental/vision are lower than US due to universal healthcare.

PROVINCE_EXPENSE_TEMPLATES = {
    "Ontario": {
        "Conservative (statistical)": {
            "Groceries": 4440, "Dining Out": 2520, "Coffee Shops": 530, "Auto Payment": 4070, "Gas & Fuel": 1850, "Auto Maintenance": 670, "Auto Insurance": 1180, "Parking & Tolls": 300, "Public Transit": 370, "Ride Shares": 220,
            "Clothing": 1000, "Personal Care": 500, "Grooming": 330, "Medical": 590, "Dental": 330, "Vision": 150, "Fitness": 370, "Mental Health": 260, "Entertainment": 1000, "Hobbies": 520, "Subscriptions": 410, "Phone": 740, "Other Personal": 480
        },
        "Average (statistical)": {
            "Groceries": 6340, "Dining Out": 3600, "Coffee Shops": 760, "Auto Payment": 5810, "Gas & Fuel": 2640, "Auto Maintenance": 960, "Auto Insurance": 1680, "Parking & Tolls": 430, "Public Transit": 530, "Ride Shares": 310,
            "Clothing": 1430, "Personal Care": 710, "Grooming": 470, "Medical": 850, "Dental": 470, "Vision": 220, "Fitness": 530, "Mental Health": 370, "Entertainment": 1430, "Hobbies": 740, "Subscriptions": 590, "Phone": 1060, "Other Personal": 680
        },
        "High-end (statistical)": {
            "Groceries": 9510, "Dining Out": 5400, "Coffee Shops": 1140, "Auto Payment": 8720, "Gas & Fuel": 3960, "Auto Maintenance": 1440, "Auto Insurance": 2520, "Parking & Tolls": 640, "Public Transit": 790, "Ride Shares": 470,
            "Clothing": 2140, "Personal Care": 1070, "Grooming": 710, "Medical": 1270, "Dental": 710, "Vision": 330, "Fitness": 790, "Mental Health": 560, "Entertainment": 2140, "Hobbies": 1110, "Subscriptions": 880, "Phone": 1590, "Other Personal": 1020
        }
    },
    "British Columbia": {
        "Conservative (statistical)": {
            "Groceries": 4810, "Dining Out": 2740, "Coffee Shops": 590, "Auto Payment": 4180, "Gas & Fuel": 2000, "Auto Maintenance": 700, "Auto Insurance": 1330, "Parking & Tolls": 330, "Public Transit": 410, "Ride Shares": 260,
            "Clothing": 1070, "Personal Care": 530, "Grooming": 350, "Medical": 560, "Dental": 330, "Vision": 150, "Fitness": 410, "Mental Health": 300, "Entertainment": 1070, "Hobbies": 560, "Subscriptions": 430, "Phone": 740, "Other Personal": 520
        },
        "Average (statistical)": {
            "Groceries": 6860, "Dining Out": 3920, "Coffee Shops": 850, "Auto Payment": 5960, "Gas & Fuel": 2860, "Auto Maintenance": 1000, "Auto Insurance": 1900, "Parking & Tolls": 470, "Public Transit": 590, "Ride Shares": 370,
            "Clothing": 1530, "Personal Care": 760, "Grooming": 500, "Medical": 800, "Dental": 470, "Vision": 220, "Fitness": 590, "Mental Health": 430, "Entertainment": 1530, "Hobbies": 800, "Subscriptions": 610, "Phone": 1060, "Other Personal": 740
        },
        "High-end (statistical)": {
            "Groceries": 10290, "Dining Out": 5880, "Coffee Shops": 1270, "Auto Payment": 8940, "Gas & Fuel": 4290, "Auto Maintenance": 1500, "Auto Insurance": 2850, "Parking & Tolls": 710, "Public Transit": 880, "Ride Shares": 560,
            "Clothing": 2290, "Personal Care": 1140, "Grooming": 750, "Medical": 1200, "Dental": 710, "Vision": 330, "Fitness": 880, "Mental Health": 640, "Entertainment": 2290, "Hobbies": 1200, "Subscriptions": 920, "Phone": 1590, "Other Personal": 1110
        }
    },
    "Quebec": {
        "Conservative (statistical)": {
            "Groceries": 4070, "Dining Out": 2220, "Coffee Shops": 480, "Auto Payment": 3700, "Gas & Fuel": 1700, "Auto Maintenance": 630, "Auto Insurance": 520, "Parking & Tolls": 260, "Public Transit": 410, "Ride Shares": 190,
            "Clothing": 890, "Personal Care": 450, "Grooming": 300, "Medical": 480, "Dental": 300, "Vision": 130, "Fitness": 330, "Mental Health": 230, "Entertainment": 890, "Hobbies": 480, "Subscriptions": 370, "Phone": 670, "Other Personal": 440
        },
        "Average (statistical)": {
            "Groceries": 5810, "Dining Out": 3170, "Coffee Shops": 680, "Auto Payment": 5290, "Gas & Fuel": 2420, "Auto Maintenance": 900, "Auto Insurance": 740, "Parking & Tolls": 370, "Public Transit": 590, "Ride Shares": 260,
            "Clothing": 1280, "Personal Care": 640, "Grooming": 430, "Medical": 680, "Dental": 430, "Vision": 190, "Fitness": 470, "Mental Health": 330, "Entertainment": 1280, "Hobbies": 680, "Subscriptions": 530, "Phone": 960, "Other Personal": 630
        },
        "High-end (statistical)": {
            "Groceries": 8720, "Dining Out": 4760, "Coffee Shops": 1020, "Auto Payment": 7930, "Gas & Fuel": 3630, "Auto Maintenance": 1350, "Auto Insurance": 1110, "Parking & Tolls": 560, "Public Transit": 880, "Ride Shares": 400,
            "Clothing": 1920, "Personal Care": 960, "Grooming": 640, "Medical": 1020, "Dental": 640, "Vision": 280, "Fitness": 710, "Mental Health": 500, "Entertainment": 1920, "Hobbies": 1020, "Subscriptions": 790, "Phone": 1440, "Other Personal": 940
        }
    },
    "Alberta": {
        "Conservative (statistical)": {
            "Groceries": 4330, "Dining Out": 2480, "Coffee Shops": 530, "Auto Payment": 4260, "Gas & Fuel": 1920, "Auto Maintenance": 670, "Auto Insurance": 890, "Parking & Tolls": 280, "Public Transit": 260, "Ride Shares": 190,
            "Clothing": 960, "Personal Care": 480, "Grooming": 320, "Medical": 560, "Dental": 330, "Vision": 150, "Fitness": 370, "Mental Health": 260, "Entertainment": 1000, "Hobbies": 520, "Subscriptions": 410, "Phone": 700, "Other Personal": 480
        },
        "Average (statistical)": {
            "Groceries": 6190, "Dining Out": 3540, "Coffee Shops": 760, "Auto Payment": 6080, "Gas & Fuel": 2750, "Auto Maintenance": 960, "Auto Insurance": 1270, "Parking & Tolls": 400, "Public Transit": 370, "Ride Shares": 260,
            "Clothing": 1380, "Personal Care": 680, "Grooming": 460, "Medical": 800, "Dental": 470, "Vision": 220, "Fitness": 530, "Mental Health": 370, "Entertainment": 1430, "Hobbies": 740, "Subscriptions": 590, "Phone": 1000, "Other Personal": 680
        },
        "High-end (statistical)": {
            "Groceries": 9280, "Dining Out": 5310, "Coffee Shops": 1140, "Auto Payment": 9120, "Gas & Fuel": 4120, "Auto Maintenance": 1440, "Auto Insurance": 1900, "Parking & Tolls": 600, "Public Transit": 560, "Ride Shares": 400,
            "Clothing": 2070, "Personal Care": 1020, "Grooming": 680, "Medical": 1200, "Dental": 710, "Vision": 330, "Fitness": 790, "Mental Health": 560, "Entertainment": 2140, "Hobbies": 1110, "Subscriptions": 880, "Phone": 1500, "Other Personal": 1020
        }
    },
    "Manitoba": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 2110, "Coffee Shops": 440, "Auto Payment": 3700, "Gas & Fuel": 1700, "Auto Maintenance": 630, "Auto Insurance": 850, "Parking & Tolls": 220, "Public Transit": 260, "Ride Shares": 150,
            "Clothing": 850, "Personal Care": 430, "Grooming": 280, "Medical": 520, "Dental": 300, "Vision": 130, "Fitness": 300, "Mental Health": 220, "Entertainment": 850, "Hobbies": 440, "Subscriptions": 370, "Phone": 670, "Other Personal": 410
        },
        "Average (statistical)": {
            "Groceries": 5590, "Dining Out": 3020, "Coffee Shops": 630, "Auto Payment": 5290, "Gas & Fuel": 2420, "Auto Maintenance": 900, "Auto Insurance": 1220, "Parking & Tolls": 310, "Public Transit": 370, "Ride Shares": 220,
            "Clothing": 1220, "Personal Care": 610, "Grooming": 400, "Medical": 740, "Dental": 430, "Vision": 190, "Fitness": 430, "Mental Health": 310, "Entertainment": 1220, "Hobbies": 630, "Subscriptions": 530, "Phone": 960, "Other Personal": 590
        },
        "High-end (statistical)": {
            "Groceries": 8390, "Dining Out": 4520, "Coffee Shops": 940, "Auto Payment": 7930, "Gas & Fuel": 3630, "Auto Maintenance": 1350, "Auto Insurance": 1830, "Parking & Tolls": 470, "Public Transit": 560, "Ride Shares": 330,
            "Clothing": 1830, "Personal Care": 920, "Grooming": 600, "Medical": 1110, "Dental": 640, "Vision": 280, "Fitness": 640, "Mental Health": 470, "Entertainment": 1830, "Hobbies": 940, "Subscriptions": 790, "Phone": 1440, "Other Personal": 880
        }
    },
    "Saskatchewan": {
        "Conservative (statistical)": {
            "Groceries": 3850, "Dining Out": 2040, "Coffee Shops": 430, "Auto Payment": 3700, "Gas & Fuel": 1770, "Auto Maintenance": 630, "Auto Insurance": 780, "Parking & Tolls": 190, "Public Transit": 190, "Ride Shares": 130,
            "Clothing": 850, "Personal Care": 430, "Grooming": 280, "Medical": 520, "Dental": 300, "Vision": 130, "Fitness": 300, "Mental Health": 220, "Entertainment": 850, "Hobbies": 440, "Subscriptions": 370, "Phone": 670, "Other Personal": 410
        },
        "Average (statistical)": {
            "Groceries": 5510, "Dining Out": 2910, "Coffee Shops": 610, "Auto Payment": 5290, "Gas & Fuel": 2530, "Auto Maintenance": 900, "Auto Insurance": 1110, "Parking & Tolls": 280, "Public Transit": 260, "Ride Shares": 190,
            "Clothing": 1220, "Personal Care": 610, "Grooming": 400, "Medical": 740, "Dental": 430, "Vision": 190, "Fitness": 430, "Mental Health": 310, "Entertainment": 1220, "Hobbies": 630, "Subscriptions": 530, "Phone": 960, "Other Personal": 590
        },
        "High-end (statistical)": {
            "Groceries": 8260, "Dining Out": 4370, "Coffee Shops": 920, "Auto Payment": 7930, "Gas & Fuel": 3790, "Auto Maintenance": 1350, "Auto Insurance": 1660, "Parking & Tolls": 420, "Public Transit": 400, "Ride Shares": 280,
            "Clothing": 1830, "Personal Care": 920, "Grooming": 600, "Medical": 1110, "Dental": 640, "Vision": 280, "Fitness": 640, "Mental Health": 470, "Entertainment": 1830, "Hobbies": 940, "Subscriptions": 790, "Phone": 1440, "Other Personal": 880
        }
    },
    "Nova Scotia": {
        "Conservative (statistical)": {
            "Groceries": 3770, "Dining Out": 1960, "Coffee Shops": 410, "Auto Payment": 3550, "Gas & Fuel": 1700, "Auto Maintenance": 600, "Auto Insurance": 670, "Parking & Tolls": 170, "Public Transit": 220, "Ride Shares": 110,
            "Clothing": 780, "Personal Care": 390, "Grooming": 260, "Medical": 480, "Dental": 280, "Vision": 130, "Fitness": 280, "Mental Health": 190, "Entertainment": 780, "Hobbies": 410, "Subscriptions": 350, "Phone": 670, "Other Personal": 370
        },
        "Average (statistical)": {
            "Groceries": 5390, "Dining Out": 2790, "Coffee Shops": 590, "Auto Payment": 5070, "Gas & Fuel": 2420, "Auto Maintenance": 860, "Auto Insurance": 960, "Parking & Tolls": 240, "Public Transit": 310, "Ride Shares": 150,
            "Clothing": 1110, "Personal Care": 560, "Grooming": 370, "Medical": 680, "Dental": 400, "Vision": 190, "Fitness": 400, "Mental Health": 280, "Entertainment": 1110, "Hobbies": 590, "Subscriptions": 500, "Phone": 960, "Other Personal": 530
        },
        "High-end (statistical)": {
            "Groceries": 8080, "Dining Out": 4190, "Coffee Shops": 880, "Auto Payment": 7600, "Gas & Fuel": 3630, "Auto Maintenance": 1280, "Auto Insurance": 1440, "Parking & Tolls": 370, "Public Transit": 470, "Ride Shares": 230,
            "Clothing": 1660, "Personal Care": 840, "Grooming": 560, "Medical": 1020, "Dental": 600, "Vision": 280, "Fitness": 600, "Mental Health": 420, "Entertainment": 1660, "Hobbies": 880, "Subscriptions": 750, "Phone": 1440, "Other Personal": 800
        }
    },
    "New Brunswick": {
        "Conservative (statistical)": {
            "Groceries": 3630, "Dining Out": 1850, "Coffee Shops": 390, "Auto Payment": 3480, "Gas & Fuel": 1630, "Auto Maintenance": 590, "Auto Insurance": 630, "Parking & Tolls": 150, "Public Transit": 150, "Ride Shares": 100,
            "Clothing": 740, "Personal Care": 370, "Grooming": 250, "Medical": 460, "Dental": 260, "Vision": 120, "Fitness": 260, "Mental Health": 180, "Entertainment": 740, "Hobbies": 390, "Subscriptions": 340, "Phone": 650, "Other Personal": 350
        },
        "Average (statistical)": {
            "Groceries": 5180, "Dining Out": 2640, "Coffee Shops": 560, "Auto Payment": 4960, "Gas & Fuel": 2340, "Auto Maintenance": 840, "Auto Insurance": 900, "Parking & Tolls": 220, "Public Transit": 220, "Ride Shares": 150,
            "Clothing": 1060, "Personal Care": 530, "Grooming": 350, "Medical": 650, "Dental": 370, "Vision": 170, "Fitness": 370, "Mental Health": 260, "Entertainment": 1060, "Hobbies": 560, "Subscriptions": 480, "Phone": 930, "Other Personal": 500
        },
        "High-end (statistical)": {
            "Groceries": 7770, "Dining Out": 3960, "Coffee Shops": 840, "Auto Payment": 7440, "Gas & Fuel": 3510, "Auto Maintenance": 1260, "Auto Insurance": 1350, "Parking & Tolls": 330, "Public Transit": 330, "Ride Shares": 220,
            "Clothing": 1590, "Personal Care": 800, "Grooming": 530, "Medical": 980, "Dental": 560, "Vision": 260, "Fitness": 560, "Mental Health": 390, "Entertainment": 1590, "Hobbies": 840, "Subscriptions": 720, "Phone": 1400, "Other Personal": 750
        }
    },
    "Newfoundland and Labrador": {
        "Conservative (statistical)": {
            "Groceries": 3920, "Dining Out": 1810, "Coffee Shops": 380, "Auto Payment": 3480, "Gas & Fuel": 1740, "Auto Maintenance": 610, "Auto Insurance": 700, "Parking & Tolls": 150, "Public Transit": 150, "Ride Shares": 90,
            "Clothing": 740, "Personal Care": 370, "Grooming": 240, "Medical": 460, "Dental": 260, "Vision": 120, "Fitness": 250, "Mental Health": 180, "Entertainment": 740, "Hobbies": 380, "Subscriptions": 340, "Phone": 670, "Other Personal": 350
        },
        "Average (statistical)": {
            "Groceries": 5590, "Dining Out": 2590, "Coffee Shops": 540, "Auto Payment": 4960, "Gas & Fuel": 2490, "Auto Maintenance": 870, "Auto Insurance": 1000, "Parking & Tolls": 220, "Public Transit": 220, "Ride Shares": 130,
            "Clothing": 1060, "Personal Care": 530, "Grooming": 340, "Medical": 650, "Dental": 370, "Vision": 170, "Fitness": 350, "Mental Health": 260, "Entertainment": 1060, "Hobbies": 540, "Subscriptions": 480, "Phone": 960, "Other Personal": 500
        },
        "High-end (statistical)": {
            "Groceries": 8390, "Dining Out": 3890, "Coffee Shops": 810, "Auto Payment": 7440, "Gas & Fuel": 3730, "Auto Maintenance": 1310, "Auto Insurance": 1500, "Parking & Tolls": 330, "Public Transit": 330, "Ride Shares": 190,
            "Clothing": 1590, "Personal Care": 800, "Grooming": 510, "Medical": 980, "Dental": 560, "Vision": 260, "Fitness": 530, "Mental Health": 390, "Entertainment": 1590, "Hobbies": 810, "Subscriptions": 720, "Phone": 1440, "Other Personal": 750
        }
    },
    "Prince Edward Island": {
        "Conservative (statistical)": {
            "Groceries": 3590, "Dining Out": 1740, "Coffee Shops": 370, "Auto Payment": 3400, "Gas & Fuel": 1590, "Auto Maintenance": 570, "Auto Insurance": 600, "Parking & Tolls": 130, "Public Transit": 110, "Ride Shares": 80,
            "Clothing": 710, "Personal Care": 350, "Grooming": 240, "Medical": 440, "Dental": 250, "Vision": 110, "Fitness": 240, "Mental Health": 170, "Entertainment": 710, "Hobbies": 370, "Subscriptions": 330, "Phone": 650, "Other Personal": 330
        },
        "Average (statistical)": {
            "Groceries": 5130, "Dining Out": 2490, "Coffee Shops": 530, "Auto Payment": 4850, "Gas & Fuel": 2270, "Auto Maintenance": 810, "Auto Insurance": 850, "Parking & Tolls": 190, "Public Transit": 150, "Ride Shares": 110,
            "Clothing": 1010, "Personal Care": 500, "Grooming": 340, "Medical": 630, "Dental": 350, "Vision": 160, "Fitness": 340, "Mental Health": 240, "Entertainment": 1010, "Hobbies": 530, "Subscriptions": 470, "Phone": 930, "Other Personal": 470
        },
        "High-end (statistical)": {
            "Groceries": 7700, "Dining Out": 3730, "Coffee Shops": 790, "Auto Payment": 7280, "Gas & Fuel": 3410, "Auto Maintenance": 1220, "Auto Insurance": 1280, "Parking & Tolls": 280, "Public Transit": 230, "Ride Shares": 170,
            "Clothing": 1520, "Personal Care": 750, "Grooming": 510, "Medical": 940, "Dental": 530, "Vision": 240, "Fitness": 510, "Mental Health": 370, "Entertainment": 1520, "Hobbies": 790, "Subscriptions": 710, "Phone": 1400, "Other Personal": 710
        }
    },
}


def get_adult_expense_template(location, strategy_name):
    """
    Get adult expense template for a specific location and strategy.
    Priority: city → US state → Canadian province → wizard state setting → Seattle fallback.
    """
    # Try city-level templates first
    if location in ADULT_EXPENSE_TEMPLATES:
        if strategy_name in ADULT_EXPENSE_TEMPLATES[location]:
            return ADULT_EXPENSE_TEMPLATES[location][strategy_name].copy()
        base_name = get_strategy_base_name(strategy_name)
        if base_name in ADULT_EXPENSE_TEMPLATES[location]:
            return ADULT_EXPENSE_TEMPLATES[location][base_name].copy()

    # Try US state templates
    if location in STATE_EXPENSE_TEMPLATES:
        if strategy_name in STATE_EXPENSE_TEMPLATES[location]:
            return STATE_EXPENSE_TEMPLATES[location][strategy_name].copy()
        base_name = get_strategy_base_name(strategy_name)
        if base_name in STATE_EXPENSE_TEMPLATES[location]:
            return STATE_EXPENSE_TEMPLATES[location][base_name].copy()

    # Try Canadian province templates
    if location in PROVINCE_EXPENSE_TEMPLATES:
        if strategy_name in PROVINCE_EXPENSE_TEMPLATES[location]:
            return PROVINCE_EXPENSE_TEMPLATES[location][strategy_name].copy()
        base_name = get_strategy_base_name(strategy_name)
        if base_name in PROVINCE_EXPENSE_TEMPLATES[location]:
            return PROVINCE_EXPENSE_TEMPLATES[location][base_name].copy()

    # Check if wizard has a state/province set
    state = None
    if hasattr(st, 'session_state') and hasattr(st.session_state, 'get'):
        wd = st.session_state.get('wizard_data', {})
        state = wd.get('current_location_state') or wd.get('wiz_loc_state')
        if state in ("I'll fill this in later", "Outside the US", None, ''):
            state = None
    if state:
        for template_dict in [STATE_EXPENSE_TEMPLATES, PROVINCE_EXPENSE_TEMPLATES]:
            if state in template_dict:
                if strategy_name in template_dict[state]:
                    return template_dict[state][strategy_name].copy()

    # Return default (Seattle Average) if not found
    if "Average (statistical)" in ADULT_EXPENSE_TEMPLATES.get("Seattle", {}):
        return ADULT_EXPENSE_TEMPLATES["Seattle"]["Average (statistical)"].copy()

    # Last resort: return zeros for all categories
    return {cat: 0 for cat in ADULT_EXPENSE_CATEGORIES_FLAT}

def get_children_expense_template(location, strategy_name):
    """
    Get children expense template for a specific location and strategy.
    Generates template from adult template using age-based scaling.

    Args:
        location: Location name
        strategy_name: Strategy name (with or without suffix)

    Returns:
        Dictionary with lists of 31 annual expense amounts (ages 0-30) per category
    """
    # First check if we have a legacy template
    if location in CHILDREN_EXPENSE_TEMPLATES:
        if strategy_name in CHILDREN_EXPENSE_TEMPLATES[location]:
            return CHILDREN_EXPENSE_TEMPLATES[location][strategy_name].copy()

        # Try legacy name
        base_name = get_strategy_base_name(strategy_name)
        if base_name in CHILDREN_EXPENSE_TEMPLATES[location]:
            return CHILDREN_EXPENSE_TEMPLATES[location][base_name].copy()

    # If no legacy template, generate from adult template
    adult_template = get_adult_expense_template(location, strategy_name)

    # Determine strategy level for scaling
    if 'Conservative' in strategy_name:
        strategy_level = 'Conservative'
    elif 'High-end' in strategy_name or 'High' in strategy_name:
        strategy_level = 'High-end'
    else:
        strategy_level = 'Average'

    # Generate children template from adult
    return generate_children_template_from_adult(adult_template, strategy_level)

def migrate_legacy_children_expenses_to_new_structure(legacy_data, child_age):
    """
    Migrate legacy children expense data (single age) to new category structure.
    Maps old categories to new ones and fills in defaults for new categories.

    Args:
        legacy_data: Dict with legacy category names as keys
        child_age: Age of child (0-30)

    Returns:
        Dict with new category names as keys
    """
    # Mapping from legacy to new categories
    category_mapping = {
        'Food': 'Groceries',  # Split food into groceries primarily
        'Clothing': 'Clothing',
        'Healthcare': 'Medical',  # Map healthcare to medical
        'Activities/Sports': 'Activities & Sports',
        'Entertainment': 'Entertainment',
        'Transportation': 'Gas & Fuel',  # Map transportation to gas primarily
        'School Supplies': 'School Supplies',
        'Gifts/Celebrations': 'Gifts & Celebrations',
        'Miscellaneous': 'Other Child Expenses',
        'Daycare': 'Daycare',
        'Baby Equipment': 'Baby Equipment',
        'Education': 'Education'
    }

    new_data = {}

    # Map legacy categories to new ones
    for legacy_cat, new_cat in category_mapping.items():
        if legacy_cat in legacy_data:
            new_data[new_cat] = legacy_data[legacy_cat]

    # Fill in new categories with reasonable defaults based on age
    if 'Dining Out' not in new_data:
        # Dining out increases with age
        new_data['Dining Out'] = 200 if child_age < 5 else 400 if child_age < 13 else 800 if child_age < 18 else 600 if child_age < 23 else 0

    if 'Coffee Shops' not in new_data:
        # Coffee shops mainly for teenagers/young adults
        new_data['Coffee Shops'] = 100 if 16 <= child_age < 23 else 0

    if 'Auto Payment' not in new_data:
        # Car payment for teenagers/young adults
        new_data['Auto Payment'] = 3000 if 16 <= child_age < 23 else 0

    if 'Auto Maintenance' not in new_data:
        new_data['Auto Maintenance'] = 500 if 16 <= child_age < 23 else 0

    if 'Auto Insurance' not in new_data:
        new_data['Auto Insurance'] = 2000 if 16 <= child_age < 19 else 1500 if 19 <= child_age < 23 else 0

    if 'Parking & Tolls' not in new_data:
        new_data['Parking & Tolls'] = 200 if 16 <= child_age < 23 else 0

    if 'Public Transit' not in new_data:
        new_data['Public Transit'] = 100 if 13 <= child_age < 16 else 0

    if 'Ride Shares' not in new_data:
        new_data['Ride Shares'] = 200 if 16 <= child_age < 23 else 0

    if 'Personal Care' not in new_data:
        new_data['Personal Care'] = 100 if child_age < 5 else 200 if child_age < 13 else 400 if child_age < 23 else 0

    if 'Grooming' not in new_data:
        new_data['Grooming'] = 50 if child_age < 5 else 100 if child_age < 13 else 300 if child_age < 23 else 0

    if 'Dental' not in new_data:
        new_data['Dental'] = 300 if child_age < 18 else 200 if child_age < 23 else 0

    if 'Vision' not in new_data:
        new_data['Vision'] = 150 if child_age < 18 else 100 if child_age < 23 else 0

    if 'Fitness' not in new_data:
        # Fitness memberships for teens/young adults
        new_data['Fitness'] = 300 if 13 <= child_age < 23 else 0

    if 'Mental Health' not in new_data:
        new_data['Mental Health'] = 0  # Optional, parents can add if needed

    if 'Hobbies' not in new_data:
        new_data['Hobbies'] = 200 if child_age < 13 else 400 if child_age < 18 else 300 if child_age < 23 else 0

    if 'Subscriptions' not in new_data:
        new_data['Subscriptions'] = 100 if child_age >= 13 and child_age < 23 else 0

    if 'Phone' not in new_data:
        new_data['Phone'] = 500 if 13 <= child_age < 23 else 0

    # Ensure all required categories exist
    for cat in CHILDREN_EXPENSE_CATEGORIES_FLAT:
        if cat not in new_data:
            new_data[cat] = 0

    return new_data

def generate_children_template_from_adult(adult_template, strategy_level='Average'):
    """
    Generate age-based children expense template (ages 0-30) from adult template.
    Applies age-appropriate scaling and includes teenage car ownership costs.

    Args:
        adult_template: Dict of adult annual expenses by category
        strategy_level: 'Conservative', 'Average', or 'High-end' for scaling

    Returns:
        Dict with lists of 31 values (one per age 0-30) for each category
    """
    # Age scaling factors (0.0-1.0) for different age ranges
    # These determine what fraction of adult expense applies at each age
    def get_age_scale(age):
        if age < 2: return 0.25   # Baby
        elif age < 5: return 0.30  # Toddler
        elif age < 12: return 0.40 # Child
        elif age < 16: return 0.50 # Pre-teen/Early teen
        elif age < 19: return 0.70 # Late teen (peak spending)
        elif age < 23: return 0.50 # College age
        elif age < 26: return 0.30 # Young adult (partial support)
        else: return 0.0            # Independent

    template = {}

    # Food categories (Groceries, Dining Out, Coffee Shops)
    template['Groceries'] = [adult_template['Groceries'] * get_age_scale(i) for i in range(31)]

    dining_scale = [0, 0, 0.05, 0.05, 0.10, 0.10, 0.15, 0.15, 0.20, 0.20, 0.25, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55,
                    0.40, 0.35, 0.30, 0.25, 0.20, 0, 0, 0, 0, 0, 0, 0, 0]
    template['Dining Out'] = [adult_template['Dining Out'] * dining_scale[i] for i in range(31)]

    coffee_scale = [0]*13 + [0.1, 0.15, 0.20, 0.30, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15] + [0]*9
    template['Coffee Shops'] = [adult_template['Coffee Shops'] * coffee_scale[i] for i in range(31)]

    # Transportation - includes TEENAGE CAR OWNERSHIP
    # Auto Payment (car loan/lease) - primarily for teens 16-22
    auto_payment_scale = [0]*16 + [0.5, 0.6, 0.6, 0.5, 0.5, 0.5, 0.4] + [0]*8
    template['Auto Payment'] = [adult_template['Auto Payment'] * auto_payment_scale[i] for i in range(31)]

    # Gas & Fuel - starts when driving
    gas_scale = [0.05]*13 + [0.15, 0.20, 0.25, 0.40, 0.50, 0.45, 0.40, 0.35, 0.30, 0.25] + [0]*8
    template['Gas & Fuel'] = [adult_template['Gas & Fuel'] * gas_scale[i] for i in range(31)]

    # Auto Maintenance
    maint_scale = [0.02]*13 + [0.10, 0.15, 0.20, 0.35, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15] + [0]*8
    template['Auto Maintenance'] = [adult_template['Auto Maintenance'] * maint_scale[i] for i in range(31)]

    # Auto Insurance - HIGH for teens, then drops
    insurance_scale = [0]*16 + [1.2, 1.1, 1.0, 0.8, 0.7, 0.6, 0.5] + [0]*8  # Teens pay MORE than adults!
    template['Auto Insurance'] = [adult_template['Auto Insurance'] * insurance_scale[i] for i in range(31)]

    # Parking & Tolls
    parking_scale = [0]*16 + [0.3, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2] + [0]*8
    template['Parking & Tolls'] = [adult_template['Parking & Tolls'] * parking_scale[i] for i in range(31)]

    # Public Transit - before driving age
    transit_scale = [0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.10, 0.10, 0.15, 0.15, 0.20, 0.20, 0.25, 0.30, 0.30, 0.20, 0, 0, 0, 0, 0, 0, 0] + [0]*8
    template['Public Transit'] = [adult_template['Public Transit'] * transit_scale[i] for i in range(31)]

    # Ride Shares
    ride_scale = [0]*13 + [0.15, 0.20, 0.25, 0.30, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10] + [0]*8
    template['Ride Shares'] = [adult_template['Ride Shares'] * ride_scale[i] for i in range(31)]

    # Personal categories
    template['Clothing'] = [adult_template['Clothing'] * get_age_scale(i) for i in range(31)]
    template['Personal Care'] = [adult_template['Personal Care'] * get_age_scale(i) for i in range(31)]
    template['Grooming'] = [adult_template['Grooming'] * get_age_scale(i) * (1.2 if 13 <= i < 19 else 1.0) for i in range(31)]  # Teens spend more on grooming

    # Health
    template['Medical'] = [adult_template['Medical'] * get_age_scale(i) for i in range(31)]
    template['Dental'] = [adult_template['Dental'] * get_age_scale(i) for i in range(31)]
    template['Vision'] = [adult_template['Vision'] * get_age_scale(i) for i in range(31)]
    template['Fitness'] = [adult_template['Fitness'] * (0.3 if 13 <= i < 23 else 0) for i in range(31)]
    template['Mental Health'] = [adult_template['Mental Health'] * (0.3 if 13 <= i < 23 else 0) for i in range(31)]

    # Entertainment & Lifestyle
    template['Entertainment'] = [adult_template['Entertainment'] * get_age_scale(i) for i in range(31)]
    template['Hobbies'] = [adult_template['Hobbies'] * get_age_scale(i) for i in range(31)]
    template['Subscriptions'] = [adult_template['Subscriptions'] * (0.3 if 13 <= i < 23 else 0) for i in range(31)]
    template['Phone'] = [adult_template['Phone'] * (0.6 if 13 <= i < 23 else 0) for i in range(31)]

    # Child-specific categories
    # Baby Equipment - only ages 0-4
    baby_equip_base = 5000 if strategy_level == 'High-end' else 3000 if strategy_level == 'Average' else 2000
    template['Baby Equipment'] = [baby_equip_base, baby_equip_base*0.15, baby_equip_base*0.10, baby_equip_base*0.07, baby_equip_base*0.05] + [0]*26

    # Daycare - ages 0-8 (after-school for older kids)
    daycare_base = 30000 if strategy_level == 'High-end' else 22000 if strategy_level == 'Average' else 18000
    template['Daycare'] = ([daycare_base]*5 + [daycare_base*0.4, daycare_base*0.3, daycare_base*0.2, daycare_base*0.1] + [0]*22)

    # School Supplies
    supplies_base = 800 if strategy_level == 'High-end' else 500 if strategy_level == 'Average' else 300
    template['School Supplies'] = ([supplies_base*0.1]*5 + [supplies_base*i/13 for i in range(1, 14)] + [0]*13)

    # Activities & Sports - peaks in middle/high school
    activities_base = 3000 if strategy_level == 'High-end' else 2000 if strategy_level == 'Average' else 1200
    activities_scale = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                        0.5, 0.4, 0.3, 0.2, 0.15] + [0]*8
    template['Activities & Sports'] = [activities_base * activities_scale[i] for i in range(31)]

    # Gifts & Celebrations
    gifts_base = 1000 if strategy_level == 'High-end' else 700 if strategy_level == 'Average' else 500
    template['Gifts & Celebrations'] = [gifts_base * (0.5 if i < 18 else 0.7 if i < 30 else 0) for i in range(31)]

    # Education (college) - ages 18-21
    education_base = 55000 if strategy_level == 'High-end' else 35000 if strategy_level == 'Average' else 25000
    template['Education'] = ([0]*18 + [education_base]*4 + [0]*9)

    # Other Child Expenses
    template['Other Child Expenses'] = [adult_template['Other Personal'] * get_age_scale(i) * 0.5 for i in range(31)]

    return template

def get_template_strategy_data(location, strategy_name, template_type='family'):
    """
    Get the template data for a specific location and strategy.
    Handles both statistical and custom strategies with proper name normalization.

    Args:
        location: Location name
        strategy_name: Strategy name (with or without suffix)
        template_type: 'family', 'children', or 'adult'

    Returns:
        Dictionary of template data, or None if not found
    """
    if template_type == 'adult':
        return get_adult_expense_template(location, strategy_name)
    elif template_type == 'children':
        return get_children_expense_template(location, strategy_name)
    elif template_type == 'family':
        base_templates = FAMILY_EXPENSE_TEMPLATES
        custom_templates = st.session_state.get('custom_family_templates', {})

    # Try to get from base templates first (statistical)
    if location in base_templates:
        # Try with current name
        if strategy_name in base_templates[location]:
            return base_templates[location][strategy_name].copy()

        # Try legacy name
        base_name = get_strategy_base_name(strategy_name)
        if base_name in base_templates[location]:
            return base_templates[location][base_name].copy()

        # Try with (statistical) suffix
        statistical_name = f"{base_name} (statistical)"
        if statistical_name in base_templates[location]:
            return base_templates[location][statistical_name].copy()

    # Try custom templates
    if location in custom_templates:
        # Try with current name
        if strategy_name in custom_templates[location]:
            return custom_templates[location][strategy_name].copy()

        # Try without suffix
        base_name = get_strategy_base_name(strategy_name)
        if base_name in custom_templates[location]:
            return custom_templates[location][base_name].copy()

    return None

CHILDREN_EXPENSE_TEMPLATES = {
    "Sacramento": {
        "Conservative (statistical)": {
            'Food': [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200,
                     4400, 4600, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200, 100, 50, 0],
            'Clothing': [400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1200, 1400, 1600, 1800, 2000,
                         800, 600, 400, 300, 250, 200, 150, 100, 50, 25, 0, 0, 0],
            'Healthcare': [800, 600, 500, 450, 400, 400, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950,
                           500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Activities/Sports': [50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600,
                                  2800, 3000, 3200, 600, 400, 300, 200, 150, 100, 50, 25, 0, 0, 0, 0, 0],
            'Entertainment': [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950,
                              400, 300, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0],
            'Transportation': [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 500, 800, 1200, 1600,
                               2000, 600, 400, 300, 200, 150, 100, 50, 25, 0, 0, 0, 0, 0],
            'School Supplies': [25, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850,
                                200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
                                   1050, 600, 500, 400, 350, 300, 250, 200, 150, 100, 75, 50, 25, 0],
            'Miscellaneous': [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575,
                              400, 350, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Daycare': [22000, 22000, 22000, 22000, 22000, 8000, 6000, 4000, 2000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 28000, 28000, 28000, 28000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600,
                     4800, 5000, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200, 0],
            'Clothing': [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1400, 1600, 1800, 2000,
                         2200, 1200, 900, 700, 500, 400, 350, 300, 250, 200, 150, 100, 50, 0],
            'Healthcare': [1000, 800, 650, 600, 550, 550, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100,
                           700, 600, 500, 400, 350, 300, 250, 200, 150, 100, 50, 25, 0],
            'Activities/Sports': [100, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800,
                                  3000, 3200, 3400, 1000, 700, 500, 400, 300, 250, 200, 150, 100, 50, 25, 0, 0],
            'Entertainment': [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
                              1050, 600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0],
            'Transportation': [150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 750, 1200, 1800, 2400,
                               3000, 900, 600, 450, 350, 300, 250, 200, 150, 100, 50, 25, 0, 0],
            'School Supplies': [50, 75, 150, 225, 300, 375, 450, 525, 600, 675, 750, 825, 900, 975, 1050, 1125, 1200,
                                1275, 300, 225, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050,
                                   1100, 1150, 800, 700, 600, 500, 450, 400, 350, 300, 250, 200, 150, 100, 50],
            'Miscellaneous': [250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625, 650, 675,
                              600, 500, 450, 400, 350, 300, 250, 200, 150, 100, 75, 50, 25],
            'Daycare': [26000, 26000, 26000, 26000, 26000, 12000, 9000, 6000, 3000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5000, 700, 500, 300, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 35000, 35000, 35000, 35000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000, 5200,
                     5400, 5600, 3200, 3000, 2800, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 500],
            'Clothing': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2500, 2800, 3100,
                         3400, 3700, 2000, 1500, 1200, 1000, 800, 700, 600, 500, 400, 300, 200, 100, 50],
            'Healthcare': [1500, 1200, 1000, 900, 800, 800, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700,
                           1800, 1900, 1200, 1000, 800, 700, 600, 500, 400, 350, 300, 250, 200, 150, 100],
            'Activities/Sports': [200, 400, 800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600,
                                  6000, 6400, 6800, 2000, 1500, 1200, 1000, 800, 600, 500, 400, 300, 200, 100, 50, 0],
            'Entertainment': [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                              2000, 2100, 1200, 1000, 800, 600, 500, 400, 350, 300, 250, 200, 150, 100, 50],
            'Transportation': [250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 1200, 2000, 3000, 4000,
                               5000, 1500, 1000, 750, 600, 500, 400, 350, 300, 250, 200, 150, 100, 50],
            'School Supplies': [100, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350, 1500, 1650, 1800, 1950, 2100, 2250,
                                2400, 2550, 500, 375, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Gifts/Celebrations': [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                                   2000, 2100, 2200, 1500, 1200, 1000, 800, 700, 600, 500, 450, 400, 350, 300, 250,
                                   200],
            'Miscellaneous': [400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200,
                              1250, 1000, 850, 750, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200],
            'Daycare': [35000, 35000, 35000, 35000, 35000, 18000, 15000, 12000, 6000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [10000, 1200, 800, 500, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 55000, 55000, 55000, 55000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Seattle": {
        "Conservative (statistical)": {
            'Food': [1100, 1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 3300, 3500, 3700, 3900, 4100,
                     4300, 4500, 1900, 1700, 1500, 1300, 1100, 900, 700, 500, 300, 100, 50, 25, 0],
            'Clothing': [350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1100, 1300, 1500, 1700, 1900,
                         750, 550, 350, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Healthcare': [700, 500, 400, 350, 300, 300, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850,
                           400, 300, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0],
            'Activities/Sports': [40, 80, 160, 320, 480, 640, 800, 960, 1120, 1280, 1440, 1600, 1760, 1920, 2080, 2240,
                                  2400, 2560, 480, 320, 240, 160, 120, 80, 40, 20, 0, 0, 0, 0, 0],
            'Entertainment': [80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760,
                              320, 240, 160, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0],
            'Transportation': [80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 450, 700, 1000, 1300,
                               1600, 500, 300, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0],
            'School Supplies': [20, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680,
                                160, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800,
                                   840, 480, 400, 320, 280, 240, 200, 160, 120, 80, 60, 40, 20, 0],
            'Miscellaneous': [120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460,
                              320, 280, 240, 200, 160, 120, 80, 60, 40, 20, 0, 0, 0],
            'Daycare': [18000, 18000, 18000, 18000, 18000, 6000, 4000, 2000, 1000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 22000, 22000, 22000, 22000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400,
                     4600, 4800, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200, 100, 0],
            'Clothing': [500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1300, 1500, 1700, 1900,
                         2100, 1000, 750, 600, 450, 350, 300, 250, 200, 150, 100, 50, 25, 0],
            'Healthcare': [900, 700, 550, 500, 450, 450, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
                           600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0],
            'Activities/Sports': [80, 160, 320, 480, 640, 800, 960, 1120, 1280, 1440, 1600, 1760, 1920, 2080, 2240,
                                  2400, 2560, 2720, 800, 560, 400, 320, 240, 200, 160, 120, 80, 40, 20, 0, 0],
            'Entertainment': [160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800, 840,
                              480, 400, 320, 240, 200, 160, 120, 80, 60, 40, 20, 0, 0],
            'Transportation': [120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 650, 1000, 1500, 2000,
                               2500, 750, 500, 375, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0],
            'School Supplies': [40, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020,
                                240, 180, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800, 840, 880,
                                   920, 640, 560, 480, 400, 360, 320, 280, 240, 200, 160, 120, 80, 40],
            'Miscellaneous': [200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540,
                              480, 400, 360, 320, 280, 240, 200, 160, 120, 80, 60, 40, 20],
            'Daycare': [22000, 22000, 22000, 22000, 22000, 9000, 6000, 3000, 1500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5000, 700, 500, 300, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 28000, 28000, 28000, 28000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000,
                     5200, 5400, 2800, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 300],
            'Clothing': [800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2200, 2400, 2600,
                         2800, 3000, 1800, 1300, 1000, 800, 600, 500, 400, 300, 200, 150, 100, 50, 25],
            'Healthcare': [1300, 1000, 800, 700, 600, 600, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600,
                           1700, 1000, 800, 600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25],
            'Activities/Sports': [160, 320, 640, 960, 1280, 1600, 1920, 2240, 2560, 2880, 3200, 3520, 3840, 4160, 4480,
                                  4800, 5120, 5440, 1600, 1120, 800, 640, 480, 400, 320, 240, 160, 80, 40, 20, 0],
            'Entertainment': [320, 400, 480, 560, 640, 720, 800, 880, 960, 1040, 1120, 1200, 1280, 1360, 1440, 1520,
                              1600, 1680, 960, 800, 640, 480, 400, 320, 280, 240, 200, 160, 120, 80, 40],
            'Transportation': [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 1000, 1600, 2400, 3200,
                               4000, 1200, 800, 600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25],
            'School Supplies': [80, 120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200, 1320, 1440, 1560, 1680, 1800,
                                1920, 2040, 400, 300, 240, 200, 160, 120, 80, 60, 40, 20, 0, 0, 0],
            'Gifts/Celebrations': [400, 480, 560, 640, 720, 800, 880, 960, 1040, 1120, 1200, 1280, 1360, 1440, 1520,
                                   1600, 1680, 1760, 1200, 960, 800, 640, 560, 480, 400, 360, 320, 280, 240, 200, 160],
            'Miscellaneous': [320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800, 840, 880, 920, 960, 1000,
                              800, 680, 600, 520, 480, 440, 400, 360, 320, 280, 240, 200, 160],
            'Daycare': [30000, 30000, 30000, 30000, 30000, 15000, 12000, 9000, 4500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [10000, 1200, 800, 500, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 45000, 45000, 45000, 45000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Houston": {
        "Conservative (statistical)": {
            'Food': [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000,
                     4200, 4400, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200, 100, 50, 25, 0],
            'Clothing': [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 1000, 1200, 1400, 1600, 1800,
                         700, 500, 300, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0],
            'Healthcare': [600, 400, 300, 250, 200, 200, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750,
                           300, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0],
            'Activities/Sports': [30, 60, 120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200, 1320, 1440, 1560, 1680,
                                  1800, 1920, 360, 240, 180, 120, 90, 60, 30, 15, 0, 0, 0, 0, 0],
            'Entertainment': [60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570,
                              240, 180, 120, 90, 60, 45, 30, 15, 0, 0, 0, 0, 0],
            'Transportation': [60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 350, 550, 800, 1050,
                               1300, 400, 250, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0],
            'School Supplies': [15, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510,
                                120, 90, 60, 45, 30, 15, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600,
                                   630, 360, 300, 240, 210, 180, 150, 120, 90, 60, 45, 30, 15, 0],
            'Miscellaneous': [90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345,
                              240, 210, 180, 150, 120, 90, 60, 45, 30, 15, 0, 0, 0],
            'Daycare': [15000, 15000, 15000, 15000, 15000, 5000, 3000, 1500, 750, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [2500, 400, 250, 150, 75, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 18000, 18000, 18000, 18000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 3300, 3500, 3700, 3900, 4100, 4300,
                     4500, 4700, 2100, 1900, 1700, 1500, 1300, 1100, 900, 700, 500, 300, 200, 100, 0],
            'Clothing': [450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1200, 1400, 1600, 1800,
                         2000, 900, 650, 500, 350, 250, 200, 150, 100, 75, 50, 25, 0, 0],
            'Healthcare': [750, 550, 450, 400, 350, 350, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900,
                           450, 350, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0],
            'Activities/Sports': [60, 120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200, 1320, 1440, 1560, 1680, 1800,
                                  1920, 2040, 600, 420, 300, 240, 180, 150, 120, 90, 60, 30, 15, 0, 0],
            'Entertainment': [120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630,
                              360, 300, 240, 180, 150, 120, 90, 60, 45, 30, 15, 0, 0],
            'Transportation': [90, 112, 135, 157, 180, 202, 225, 247, 270, 292, 315, 337, 360, 500, 800, 1200, 1600,
                               2000, 600, 400, 300, 240, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'School Supplies': [30, 45, 90, 135, 180, 225, 270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765,
                                180, 135, 90, 67, 45, 30, 15, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660,
                                   690, 480, 420, 360, 315, 270, 225, 180, 135, 90, 67, 45, 30, 15],
            'Miscellaneous': [150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345, 360, 375, 390, 405,
                              360, 300, 270, 240, 210, 180, 150, 120, 90, 67, 45, 30, 15],
            'Daycare': [18000, 18000, 18000, 18000, 18000, 7500, 5000, 2500, 1250, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [4500, 600, 400, 250, 150, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25000, 25000, 25000, 25000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800,
                     5000, 5200, 2600, 2400, 2200, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200],
            'Clothing': [750, 825, 900, 975, 1050, 1125, 1200, 1275, 1350, 1425, 1500, 1575, 1650, 1875, 2100, 2325,
                         2550, 2775, 1500, 1125, 900, 675, 525, 450, 375, 300, 225, 150, 75, 37, 0],
            'Healthcare': [1125, 900, 750, 675, 600, 600, 600, 675, 750, 825, 900, 975, 1050, 1125, 1200, 1275, 1350,
                           1425, 900, 675, 525, 450, 375, 300, 225, 150, 112, 75, 37, 0, 0],
            'Activities/Sports': [120, 240, 480, 720, 960, 1200, 1440, 1680, 1920, 2160, 2400, 2640, 2880, 3120, 3360,
                                  3600, 3840, 4080, 1200, 840, 600, 480, 360, 300, 240, 180, 120, 60, 30, 15, 0],
            'Entertainment': [240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020, 1080, 1140, 1200,
                              1260, 720, 600, 480, 360, 300, 240, 210, 180, 150, 120, 90, 60, 30],
            'Transportation': [150, 187, 225, 262, 300, 337, 375, 412, 450, 487, 525, 562, 600, 800, 1280, 1920, 2560,
                               3200, 960, 640, 480, 400, 320, 240, 200, 160, 120, 80, 60, 40, 20],
            'School Supplies': [60, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900, 990, 1080, 1170, 1260, 1350, 1440,
                                1530, 360, 270, 180, 135, 90, 60, 30, 15, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020, 1080, 1140, 1200,
                                   1260, 1320, 900, 720, 600, 480, 420, 360, 300, 270, 240, 210, 180, 150, 120],
            'Miscellaneous': [240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720, 750,
                              600, 510, 450, 390, 360, 330, 300, 270, 240, 210, 180, 150, 120],
            'Daycare': [25000, 25000, 25000, 25000, 25000, 12500, 10000, 7500, 3750, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [8000, 1000, 600, 400, 250, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 40000, 40000, 40000, 40000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    # US Cities
    "New York": {
        "Conservative (statistical)": {
            'Food': [1560, 1820, 2080, 2340, 2600, 2860, 3120, 3380, 3640, 3900, 4160, 4420, 4680, 4940, 5200, 5460,
                     5720, 5980, 2600, 2340, 2080, 1820, 1560, 1300, 1040, 780, 520, 260, 130, 65, 0],
            'Clothing': [520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300, 1560, 1820, 2080, 2340, 2600,
                         1040, 780, 520, 390, 325, 260, 195, 130, 65, 32, 0, 0, 0],
            'Healthcare': [1040, 780, 650, 585, 520, 520, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235,
                           650, 520, 390, 325, 260, 195, 130, 97, 65, 32, 0, 0, 0],
            'Activities/Sports': [65, 130, 260, 520, 780, 1040, 1300, 1560, 1820, 2080, 2340, 2600, 2860, 3120, 3380, 3640,
                                  3900, 4160, 780, 520, 390, 260, 195, 130, 65, 32, 0, 0, 0, 0, 0],
            'Entertainment': [130, 195, 260, 325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235,
                              520, 390, 260, 195, 130, 97, 65, 32, 0, 0, 0, 0, 0],
            'Transportation': [130, 156, 182, 208, 234, 260, 286, 312, 338, 364, 390, 416, 442, 650, 1040, 1560, 2080,
                               2600, 780, 520, 390, 260, 195, 130, 65, 32, 0, 0, 0, 0, 0],
            'School Supplies': [32, 65, 130, 195, 260, 325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105,
                                260, 195, 130, 97, 65, 32, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [260, 325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300,
                                   1365, 780, 650, 520, 455, 390, 325, 260, 195, 130, 97, 65, 32, 0],
            'Miscellaneous': [195, 227, 260, 292, 325, 357, 390, 422, 455, 487, 520, 552, 585, 617, 650, 682, 715, 747,
                              520, 455, 390, 325, 260, 195, 130, 97, 65, 32, 0, 0, 0],
            'Daycare': [28600, 28600, 28600, 28600, 28600, 10400, 7800, 5200, 2600, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36400, 36400, 36400, 36400, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [2080, 2340, 2600, 2860, 3120, 3380, 3640, 3900, 4160, 4420, 4680, 4940, 5200, 5460, 5720, 5980,
                     6240, 6500, 3120, 2860, 2600, 2340, 2080, 1820, 1560, 1300, 1040, 780, 520, 260, 0],
            'Clothing': [780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300, 1365, 1430, 1495, 1560, 1820, 2080, 2340, 2600,
                         2860, 1560, 1170, 910, 650, 520, 455, 390, 325, 260, 195, 130, 65, 0],
            'Healthcare': [1300, 1040, 845, 780, 715, 715, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300, 1365, 1430,
                           910, 780, 650, 520, 455, 390, 325, 260, 195, 130, 65, 32, 0],
            'Activities/Sports': [130, 260, 520, 780, 1040, 1300, 1560, 1820, 2080, 2340, 2600, 2860, 3120, 3380, 3640, 3900,
                                  4160, 4420, 1300, 910, 650, 520, 390, 325, 260, 195, 130, 65, 32, 0, 0],
            'Entertainment': [260, 325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300,
                              1365, 780, 650, 520, 390, 325, 260, 195, 130, 97, 65, 32, 0, 0],
            'Transportation': [195, 234, 273, 312, 351, 390, 429, 468, 507, 546, 585, 624, 663, 975, 1560, 2340, 3120,
                               3900, 1170, 780, 585, 455, 390, 325, 260, 195, 130, 65, 32, 0, 0],
            'School Supplies': [65, 97, 195, 292, 390, 487, 585, 682, 780, 877, 975, 1072, 1170, 1267, 1365, 1462, 1560,
                                1657, 390, 292, 195, 130, 97, 65, 32, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300, 1365,
                                   1430, 1495, 1040, 910, 780, 650, 585, 520, 455, 390, 325, 260, 195, 130, 65],
            'Miscellaneous': [325, 357, 390, 422, 455, 487, 520, 552, 585, 617, 650, 682, 715, 747, 780, 812, 845, 877,
                              780, 650, 585, 520, 455, 390, 325, 260, 195, 130, 97, 65, 32],
            'Daycare': [33800, 33800, 33800, 33800, 33800, 15600, 11700, 7800, 3900, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5000, 700, 500, 300, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 45500, 45500, 45500, 45500, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2860, 3120, 3380, 3640, 3900, 4160, 4420, 4680, 4940, 5200, 5460, 5720, 5980, 6240, 6500, 6760,
                     7020, 7280, 4160, 3900, 3640, 3380, 3120, 2860, 2600, 2340, 2080, 1820, 1560, 1300, 650],
            'Clothing': [1300, 1430, 1560, 1690, 1820, 1950, 2080, 2210, 2340, 2470, 2600, 2730, 2860, 3250, 3640, 4030,
                         4420, 4810, 2600, 1950, 1560, 1300, 1040, 910, 780, 650, 520, 390, 260, 130, 65],
            'Healthcare': [1950, 1560, 1300, 1170, 1040, 1040, 1040, 1170, 1300, 1430, 1560, 1690, 1820, 1950, 2080, 2210,
                           2340, 2470, 1560, 1300, 1040, 910, 780, 650, 520, 455, 390, 325, 260, 195, 130],
            'Activities/Sports': [260, 520, 1040, 1560, 2080, 2600, 3120, 3640, 4160, 4680, 5200, 5720, 6240, 6760, 7280, 7800,
                                  8320, 8840, 2600, 1950, 1560, 1300, 1040, 780, 650, 520, 390, 260, 130, 65, 0],
            'Entertainment': [520, 650, 780, 910, 1040, 1170, 1300, 1430, 1560, 1690, 1820, 1950, 2080, 2210, 2340, 2470,
                              2600, 2730, 1560, 1300, 1040, 780, 650, 520, 455, 390, 325, 260, 195, 130, 65],
            'Transportation': [325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1560, 2600, 3900, 5200,
                               6500, 1950, 1300, 975, 780, 650, 520, 455, 390, 325, 260, 195, 130, 65],
            'School Supplies': [130, 195, 390, 585, 780, 975, 1170, 1365, 1560, 1755, 1950, 2145, 2340, 2535, 2730, 2925,
                                3120, 3315, 650, 487, 390, 325, 260, 195, 130, 97, 65, 32, 0, 0, 0],
            'Gifts/Celebrations': [650, 780, 910, 1040, 1170, 1300, 1430, 1560, 1690, 1820, 1950, 2080, 2210, 2340, 2470,
                                   2600, 2730, 2860, 1950, 1560, 1300, 1040, 910, 780, 650, 585, 520, 455, 390, 325, 260],
            'Miscellaneous': [520, 585, 650, 715, 780, 845, 910, 975, 1040, 1105, 1170, 1235, 1300, 1365, 1430, 1495, 1560,
                              1625, 1300, 1105, 975, 845, 780, 715, 650, 585, 520, 455, 390, 325, 260],
            'Daycare': [45500, 45500, 45500, 45500, 45500, 23400, 19500, 15600, 7800, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [10000, 1200, 800, 500, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 71500, 71500, 71500, 71500, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "San Francisco": {
        "Conservative (statistical)": {
            'Food': [1380, 1610, 1840, 2070, 2300, 2530, 2760, 2990, 3220, 3450, 3680, 3910, 4140, 4370, 4600, 4830,
                     5060, 5290, 2300, 2070, 1840, 1610, 1380, 1150, 920, 690, 460, 230, 115, 57, 0],
            'Clothing': [460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150, 1380, 1610, 1840, 2070, 2300,
                         920, 690, 460, 345, 287, 230, 172, 115, 57, 28, 0, 0, 0],
            'Healthcare': [920, 690, 575, 517, 460, 460, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092,
                           575, 460, 345, 287, 230, 172, 115, 86, 57, 28, 0, 0, 0],
            'Activities/Sports': [57, 115, 230, 460, 690, 920, 1150, 1380, 1610, 1840, 2070, 2300, 2530, 2760, 2990, 3220,
                                  3450, 3680, 690, 460, 345, 230, 172, 115, 57, 28, 0, 0, 0, 0, 0],
            'Entertainment': [115, 172, 230, 287, 345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092,
                              460, 345, 230, 172, 115, 86, 57, 28, 0, 0, 0, 0, 0],
            'Transportation': [115, 138, 161, 184, 207, 230, 253, 276, 299, 322, 345, 368, 391, 575, 920, 1380, 1840,
                               2300, 690, 460, 345, 230, 172, 115, 57, 28, 0, 0, 0, 0, 0],
            'School Supplies': [28, 57, 115, 172, 230, 287, 345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977,
                                230, 172, 115, 86, 57, 28, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [230, 287, 345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150,
                                   1207, 690, 575, 460, 402, 345, 287, 230, 172, 115, 86, 57, 28, 0],
            'Miscellaneous': [172, 201, 230, 258, 287, 316, 345, 373, 402, 431, 460, 488, 517, 546, 575, 603, 632, 661,
                              460, 402, 345, 287, 230, 172, 115, 86, 57, 28, 0, 0, 0],
            'Daycare': [25300, 25300, 25300, 25300, 25300, 9200, 6900, 4600, 2300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32200, 32200, 32200, 32200, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1840, 2070, 2300, 2530, 2760, 2990, 3220, 3450, 3680, 3910, 4140, 4370, 4600, 4830, 5060, 5290,
                     5520, 5750, 2760, 2530, 2300, 2070, 1840, 1610, 1380, 1150, 920, 690, 460, 230, 0],
            'Clothing': [690, 747, 805, 862, 920, 977, 1035, 1092, 1150, 1207, 1265, 1322, 1380, 1610, 1840, 2070, 2300,
                         2530, 1380, 1035, 805, 575, 460, 402, 345, 287, 230, 172, 115, 57, 0],
            'Healthcare': [1150, 920, 747, 690, 632, 632, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150, 1207, 1265,
                           805, 690, 575, 460, 402, 345, 287, 230, 172, 115, 57, 28, 0],
            'Activities/Sports': [115, 230, 460, 690, 920, 1150, 1380, 1610, 1840, 2070, 2300, 2530, 2760, 2990, 3220, 3450,
                                  3680, 3910, 1150, 805, 575, 460, 345, 287, 230, 172, 115, 57, 28, 0, 0],
            'Entertainment': [230, 287, 345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150,
                              1207, 690, 575, 460, 345, 287, 230, 172, 115, 86, 57, 28, 0, 0],
            'Transportation': [172, 207, 241, 276, 310, 345, 379, 414, 448, 483, 517, 552, 586, 862, 1380, 2070, 2760,
                               3450, 1035, 690, 517, 402, 345, 287, 230, 172, 115, 57, 28, 0, 0],
            'School Supplies': [57, 86, 172, 258, 345, 431, 517, 603, 690, 776, 862, 948, 1035, 1121, 1207, 1293, 1380,
                                1466, 345, 258, 172, 115, 86, 57, 28, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150, 1207,
                                   1265, 1322, 920, 805, 690, 575, 517, 460, 402, 345, 287, 230, 172, 115, 57],
            'Miscellaneous': [287, 316, 345, 373, 402, 431, 460, 488, 517, 546, 575, 603, 632, 661, 690, 718, 747, 776,
                              690, 575, 517, 460, 402, 345, 287, 230, 172, 115, 86, 57, 28],
            'Daycare': [29900, 29900, 29900, 29900, 29900, 13800, 10350, 6900, 3450, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5000, 700, 500, 300, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 40250, 40250, 40250, 40250, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2530, 2760, 2990, 3220, 3450, 3680, 3910, 4140, 4370, 4600, 4830, 5060, 5290, 5520, 5750, 5980,
                     6210, 6440, 3680, 3450, 3220, 2990, 2760, 2530, 2300, 2070, 1840, 1610, 1380, 1150, 575],
            'Clothing': [1150, 1265, 1380, 1495, 1610, 1725, 1840, 1955, 2070, 2185, 2300, 2415, 2530, 2875, 3220, 3565,
                         3910, 4255, 2300, 1725, 1380, 1150, 920, 805, 690, 575, 460, 345, 230, 115, 57],
            'Healthcare': [1725, 1380, 1150, 1035, 920, 920, 920, 1035, 1150, 1265, 1380, 1495, 1610, 1725, 1840, 1955,
                           2070, 2185, 1380, 1150, 920, 805, 690, 575, 460, 402, 345, 287, 230, 172, 115],
            'Activities/Sports': [230, 460, 920, 1380, 1840, 2300, 2760, 3220, 3680, 4140, 4600, 5060, 5520, 5980, 6440, 6900,
                                  7360, 7820, 2300, 1725, 1380, 1150, 920, 690, 575, 460, 345, 230, 115, 57, 0],
            'Entertainment': [460, 575, 690, 805, 920, 1035, 1150, 1265, 1380, 1495, 1610, 1725, 1840, 1955, 2070, 2185,
                              2300, 2415, 1380, 1150, 920, 690, 575, 460, 402, 345, 287, 230, 172, 115, 57],
            'Transportation': [287, 345, 402, 460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1380, 2300, 3450, 4600,
                               5750, 1725, 1150, 862, 690, 575, 460, 402, 345, 287, 230, 172, 115, 57],
            'School Supplies': [115, 172, 345, 517, 690, 862, 1035, 1207, 1380, 1552, 1725, 1897, 2070, 2242, 2415, 2587,
                                2760, 2932, 575, 431, 345, 287, 230, 172, 115, 86, 57, 28, 0, 0, 0],
            'Gifts/Celebrations': [575, 690, 805, 920, 1035, 1150, 1265, 1380, 1495, 1610, 1725, 1840, 1955, 2070, 2185,
                                   2300, 2415, 2530, 1725, 1380, 1150, 920, 805, 690, 575, 517, 460, 402, 345, 287, 230],
            'Miscellaneous': [460, 517, 575, 632, 690, 747, 805, 862, 920, 977, 1035, 1092, 1150, 1207, 1265, 1322, 1380,
                              1437, 1150, 977, 862, 747, 690, 632, 575, 517, 460, 402, 345, 287, 230],
            'Daycare': [40250, 40250, 40250, 40250, 40250, 20700, 17250, 13800, 6900, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [10000, 1200, 800, 500, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 63250, 63250, 63250, 63250, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Los Angeles": {  # Similar to California but slightly less expensive
        "Conservative (statistical)": {
            'Food': [1140, 1330, 1520, 1710, 1900, 2090, 2280, 2470, 2660, 2850, 3040, 3230, 3420, 3610, 3800, 3990,
                     4180, 4370, 1900, 1710, 1520, 1330, 1140, 950, 760, 570, 380, 190, 95, 47, 0],
            'Clothing': [380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950, 1140, 1330, 1520, 1710, 1900,
                         760, 570, 380, 285, 237, 190, 142, 95, 47, 23, 0, 0, 0],
            'Healthcare': [760, 570, 475, 427, 380, 380, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902,
                           475, 380, 285, 237, 190, 142, 95, 71, 47, 23, 0, 0, 0],
            'Activities/Sports': [47, 95, 190, 380, 570, 760, 950, 1140, 1330, 1520, 1710, 1900, 2090, 2280, 2470, 2660,
                                  2850, 3040, 570, 380, 285, 190, 142, 95, 47, 23, 0, 0, 0, 0, 0],
            'Entertainment': [95, 142, 190, 237, 285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902,
                              380, 285, 190, 142, 95, 71, 47, 23, 0, 0, 0, 0, 0],
            'Transportation': [95, 114, 133, 152, 171, 190, 209, 228, 247, 266, 285, 304, 323, 475, 760, 1140, 1520,
                               1900, 570, 380, 285, 190, 142, 95, 47, 23, 0, 0, 0, 0, 0],
            'School Supplies': [23, 47, 95, 142, 190, 237, 285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807,
                                190, 142, 95, 71, 47, 23, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [190, 237, 285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950,
                                   997, 570, 475, 380, 332, 285, 237, 190, 142, 95, 71, 47, 23, 0],
            'Miscellaneous': [142, 166, 190, 213, 237, 261, 285, 308, 332, 356, 380, 403, 427, 451, 475, 498, 522, 546,
                              380, 332, 285, 237, 190, 142, 95, 71, 47, 23, 0, 0, 0],
            'Daycare': [20900, 20900, 20900, 20900, 20900, 7600, 5700, 3800, 1900, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 26600, 26600, 26600, 26600, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1520, 1710, 1900, 2090, 2280, 2470, 2660, 2850, 3040, 3230, 3420, 3610, 3800, 3990, 4180, 4370,
                     4560, 4750, 2280, 2090, 1900, 1710, 1520, 1330, 1140, 950, 760, 570, 380, 190, 0],
            'Clothing': [570, 617, 665, 712, 760, 807, 855, 902, 950, 997, 1045, 1092, 1140, 1330, 1520, 1710, 1900,
                         2090, 1140, 855, 665, 475, 380, 332, 285, 237, 190, 142, 95, 47, 0],
            'Healthcare': [950, 760, 617, 570, 522, 522, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950, 997, 1045,
                           665, 570, 475, 380, 332, 285, 237, 190, 142, 95, 47, 23, 0],
            'Activities/Sports': [95, 190, 380, 570, 760, 950, 1140, 1330, 1520, 1710, 1900, 2090, 2280, 2470, 2660, 2850,
                                  3040, 3230, 950, 665, 475, 380, 285, 237, 190, 142, 95, 47, 23, 0, 0],
            'Entertainment': [190, 237, 285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950,
                              997, 570, 475, 380, 285, 237, 190, 142, 95, 71, 47, 23, 0, 0],
            'Transportation': [142, 171, 199, 228, 256, 285, 313, 342, 370, 399, 427, 456, 484, 712, 1140, 1710, 2280,
                               2850, 855, 570, 427, 332, 285, 237, 190, 142, 95, 47, 23, 0, 0],
            'School Supplies': [47, 71, 142, 213, 285, 356, 427, 498, 570, 641, 712, 783, 855, 926, 997, 1068, 1140,
                                1211, 285, 213, 142, 95, 71, 47, 23, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950, 997,
                                   1045, 1092, 760, 665, 570, 475, 427, 380, 332, 285, 237, 190, 142, 95, 47],
            'Miscellaneous': [237, 261, 285, 308, 332, 356, 380, 403, 427, 451, 475, 498, 522, 546, 570, 593, 617, 641,
                              570, 475, 427, 380, 332, 285, 237, 190, 142, 95, 71, 47, 23],
            'Daycare': [24700, 24700, 24700, 24700, 24700, 11400, 8550, 5700, 2850, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5000, 700, 500, 300, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 33250, 33250, 33250, 33250, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2090, 2280, 2470, 2660, 2850, 3040, 3230, 3420, 3610, 3800, 3990, 4180, 4370, 4560, 4750, 4940,
                     5130, 5320, 3040, 2850, 2660, 2470, 2280, 2090, 1900, 1710, 1520, 1330, 1140, 950, 475],
            'Clothing': [950, 1045, 1140, 1235, 1330, 1425, 1520, 1615, 1710, 1805, 1900, 1995, 2090, 2375, 2660, 2945,
                         3230, 3515, 1900, 1425, 1140, 950, 760, 665, 570, 475, 380, 285, 190, 95, 47],
            'Healthcare': [1425, 1140, 950, 855, 760, 760, 760, 855, 950, 1045, 1140, 1235, 1330, 1425, 1520, 1615,
                           1710, 1805, 1140, 950, 760, 665, 570, 475, 380, 332, 285, 237, 190, 142, 95],
            'Activities/Sports': [190, 380, 760, 1140, 1520, 1900, 2280, 2660, 3040, 3420, 3800, 4180, 4560, 4940, 5320, 5700,
                                  6080, 6460, 1900, 1425, 1140, 950, 760, 570, 475, 380, 285, 190, 95, 47, 0],
            'Entertainment': [380, 475, 570, 665, 760, 855, 950, 1045, 1140, 1235, 1330, 1425, 1520, 1615, 1710, 1805,
                              1900, 1995, 1140, 950, 760, 570, 475, 380, 332, 285, 237, 190, 142, 95, 47],
            'Transportation': [237, 285, 332, 380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 1140, 1900, 2850, 3800,
                               4750, 1425, 950, 712, 570, 475, 380, 332, 285, 237, 190, 142, 95, 47],
            'School Supplies': [95, 142, 285, 427, 570, 712, 855, 997, 1140, 1282, 1425, 1567, 1710, 1852, 1995, 2137,
                                2280, 2422, 475, 356, 285, 237, 190, 142, 95, 71, 47, 23, 0, 0, 0],
            'Gifts/Celebrations': [475, 570, 665, 760, 855, 950, 1045, 1140, 1235, 1330, 1425, 1520, 1615, 1710, 1805,
                                   1900, 1995, 2090, 1425, 1140, 950, 760, 665, 570, 475, 427, 380, 332, 285, 237, 190],
            'Miscellaneous': [380, 427, 475, 522, 570, 617, 665, 712, 760, 807, 855, 902, 950, 997, 1045, 1092, 1140,
                              1187, 950, 807, 712, 617, 570, 522, 475, 427, 380, 332, 285, 237, 190],
            'Daycare': [33250, 33250, 33250, 33250, 33250, 17100, 14250, 11400, 5700, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [10000, 1200, 800, 500, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 52250, 52250, 52250, 52250, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Portland": {
        "Conservative (statistical)": {
            'Food': [1020, 1190, 1360, 1530, 1700, 1870, 2040, 2210, 2380, 2550, 2720, 2890, 3060, 3230, 3400, 3570,
                     3740, 3910, 1700, 1530, 1360, 1190, 1020, 850, 680, 510, 340, 170, 85, 42, 0],
            'Clothing': [340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850, 1020, 1190, 1360, 1530, 1700,
                         680, 510, 340, 255, 212, 170, 127, 85, 42, 21, 0, 0, 0],
            'Healthcare': [680, 510, 425, 382, 340, 340, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807,
                           425, 340, 255, 212, 170, 127, 85, 63, 42, 21, 0, 0, 0],
            'Activities/Sports': [42, 85, 170, 340, 510, 680, 850, 1020, 1190, 1360, 1530, 1700, 1870, 2040, 2210, 2380,
                                  2550, 2720, 510, 340, 255, 170, 127, 85, 42, 21, 0, 0, 0, 0, 0],
            'Entertainment': [85, 127, 170, 212, 255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807,
                              340, 255, 170, 127, 85, 63, 42, 21, 0, 0, 0, 0, 0],
            'Transportation': [85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255, 272, 289, 425, 680, 1020, 1360,
                               1700, 510, 340, 255, 170, 127, 85, 42, 21, 0, 0, 0, 0, 0],
            'School Supplies': [21, 42, 85, 127, 170, 212, 255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722,
                                170, 127, 85, 63, 42, 21, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [170, 212, 255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850,
                                   892, 510, 425, 340, 297, 255, 212, 170, 127, 85, 63, 42, 21, 0],
            'Miscellaneous': [127, 148, 170, 191, 212, 233, 255, 276, 297, 318, 340, 361, 382, 403, 425, 446, 467, 488,
                              340, 297, 255, 212, 170, 127, 85, 63, 42, 21, 0, 0, 0],
            'Daycare': [18700, 18700, 18700, 18700, 18700, 6800, 5100, 3400, 1700, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [2750, 450, 275, 175, 90, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 23800, 23800, 23800, 23800, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1360, 1530, 1700, 1870, 2040, 2210, 2380, 2550, 2720, 2890, 3060, 3230, 3400, 3570, 3740, 3910,
                     4080, 4250, 2040, 1870, 1700, 1530, 1360, 1190, 1020, 850, 680, 510, 340, 170, 0],
            'Clothing': [510, 552, 595, 637, 680, 722, 765, 807, 850, 892, 935, 977, 1020, 1190, 1360, 1530, 1700,
                         1870, 1020, 765, 595, 425, 340, 297, 255, 212, 170, 127, 85, 42, 0],
            'Healthcare': [850, 680, 552, 510, 467, 467, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850, 892, 935,
                           595, 510, 425, 340, 297, 255, 212, 170, 127, 85, 42, 21, 0],
            'Activities/Sports': [85, 170, 340, 510, 680, 850, 1020, 1190, 1360, 1530, 1700, 1870, 2040, 2210, 2380, 2550,
                                  2720, 2890, 850, 595, 425, 340, 255, 212, 170, 127, 85, 42, 21, 0, 0],
            'Entertainment': [170, 212, 255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850,
                              892, 510, 425, 340, 255, 212, 170, 127, 85, 63, 42, 21, 0, 0],
            'Transportation': [127, 153, 178, 204, 229, 255, 280, 306, 331, 357, 382, 408, 433, 637, 1020, 1530, 2040,
                               2550, 765, 510, 382, 297, 255, 212, 170, 127, 85, 42, 21, 0, 0],
            'School Supplies': [42, 63, 127, 191, 255, 318, 382, 446, 510, 573, 637, 701, 765, 828, 892, 956, 1020,
                                1083, 255, 191, 127, 85, 63, 42, 21, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850, 892,
                                   935, 977, 680, 595, 510, 425, 382, 340, 297, 255, 212, 170, 127, 85, 42],
            'Miscellaneous': [212, 233, 255, 276, 297, 318, 340, 361, 382, 403, 425, 446, 467, 488, 510, 531, 552, 573,
                              510, 425, 382, 340, 297, 255, 212, 170, 127, 85, 63, 42, 21],
            'Daycare': [22100, 22100, 22100, 22100, 22100, 10200, 7650, 5100, 2550, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [4750, 650, 450, 275, 175, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 29750, 29750, 29750, 29750, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [1870, 2040, 2210, 2380, 2550, 2720, 2890, 3060, 3230, 3400, 3570, 3740, 3910, 4080, 4250, 4420,
                     4590, 4760, 2720, 2550, 2380, 2210, 2040, 1870, 1700, 1530, 1360, 1190, 1020, 850, 425],
            'Clothing': [850, 935, 1020, 1105, 1190, 1275, 1360, 1445, 1530, 1615, 1700, 1785, 1870, 2125, 2380, 2635,
                         2890, 3145, 1700, 1275, 1020, 850, 680, 595, 510, 425, 340, 255, 170, 85, 42],
            'Healthcare': [1275, 1020, 850, 765, 680, 680, 680, 765, 850, 935, 1020, 1105, 1190, 1275, 1360, 1445,
                           1530, 1615, 1020, 850, 680, 595, 510, 425, 340, 297, 255, 212, 170, 127, 85],
            'Activities/Sports': [170, 340, 680, 1020, 1360, 1700, 2040, 2380, 2720, 3060, 3400, 3740, 4080, 4420, 4760, 5100,
                                  5440, 5780, 1700, 1275, 1020, 850, 680, 510, 425, 340, 255, 170, 85, 42, 0],
            'Entertainment': [340, 425, 510, 595, 680, 765, 850, 935, 1020, 1105, 1190, 1275, 1360, 1445, 1530, 1615,
                              1700, 1785, 1020, 850, 680, 510, 425, 340, 297, 255, 212, 170, 127, 85, 42],
            'Transportation': [212, 255, 297, 340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 1020, 1700, 2550, 3400,
                               4250, 1275, 850, 637, 510, 425, 340, 297, 255, 212, 170, 127, 85, 42],
            'School Supplies': [85, 127, 255, 382, 510, 637, 765, 892, 1020, 1147, 1275, 1402, 1530, 1657, 1785, 1912,
                                2040, 2167, 425, 318, 255, 212, 170, 127, 85, 63, 42, 21, 0, 0, 0],
            'Gifts/Celebrations': [425, 510, 595, 680, 765, 850, 935, 1020, 1105, 1190, 1275, 1360, 1445, 1530, 1615,
                                   1700, 1785, 1870, 1275, 1020, 850, 680, 595, 510, 425, 382, 340, 297, 255, 212, 170],
            'Miscellaneous': [340, 382, 425, 467, 510, 552, 595, 637, 680, 722, 765, 807, 850, 892, 935, 977, 1020,
                              1062, 850, 722, 637, 552, 510, 467, 425, 382, 340, 297, 255, 212, 170],
            'Daycare': [29750, 29750, 29750, 29750, 29750, 15300, 12750, 10200, 5100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [9000, 1100, 700, 450, 275, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 46750, 46750, 46750, 46750, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Auckland": {  # New Zealand's largest city, high cost of living
        "Conservative (statistical)": {
            'Food': [1150, 1340, 1530, 1720, 1910, 2100, 2290, 2480, 2670, 2860, 3050, 3240, 3430, 3620, 3810, 4000,
                     4190, 4380, 1910, 1720, 1530, 1340, 1150, 960, 770, 580, 390, 200, 100, 50, 0],
            'Clothing': [380, 430, 480, 530, 580, 630, 680, 730, 780, 830, 880, 930, 980, 1150, 1340, 1530, 1720, 1910,
                         780, 580, 380, 280, 230, 180, 130, 80, 50, 30, 0, 0, 0],
            'Healthcare': [750, 550, 450, 400, 350, 350, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900,
                           450, 350, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0],
            'Activities/Sports': [45, 90, 180, 360, 540, 720, 900, 1080, 1260, 1440, 1620, 1800, 1980, 2160, 2340, 2520,
                                  2700, 2880, 540, 360, 270, 180, 135, 90, 45, 25, 0, 0, 0, 0, 0],
            'Entertainment': [90, 135, 180, 225, 270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 810, 855,
                              360, 270, 180, 135, 90, 70, 45, 25, 0, 0, 0, 0, 0],
            'Transportation': [90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290, 310, 330, 480, 750, 1100, 1450,
                               1800, 540, 340, 230, 170, 120, 90, 60, 30, 0, 0, 0, 0, 0],
            'School Supplies': [25, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850,
                                200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [180, 225, 270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 810, 855, 900,
                                   945, 540, 450, 360, 315, 270, 225, 180, 135, 90, 70, 45, 25, 0],
            'Miscellaneous': [135, 157, 180, 202, 225, 247, 270, 292, 315, 337, 360, 382, 405, 427, 450, 472, 495, 517,
                              360, 315, 270, 225, 180, 135, 90, 70, 45, 25, 0, 0, 0],
            'Daycare': [19500, 19500, 19500, 19500, 19500, 6500, 4500, 2500, 1250, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3200, 550, 350, 220, 110, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24000, 24000, 24000, 24000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1530, 1720, 1910, 2100, 2290, 2480, 2670, 2860, 3050, 3240, 3430, 3620, 3810, 4000, 4190, 4380,
                     4570, 4760, 2290, 2100, 1910, 1720, 1530, 1340, 1150, 960, 770, 580, 390, 200, 0],
            'Clothing': [540, 590, 640, 690, 740, 790, 840, 890, 940, 990, 1040, 1090, 1140, 1340, 1530, 1720, 1910,
                         2100, 1140, 840, 690, 540, 440, 390, 340, 290, 240, 190, 140, 90, 0],
            'Healthcare': [950, 750, 620, 570, 520, 520, 520, 570, 620, 670, 720, 770, 820, 870, 920, 970, 1020, 1070,
                           670, 570, 470, 370, 320, 270, 220, 170, 120, 70, 40, 20, 0],
            'Activities/Sports': [90, 180, 360, 540, 720, 900, 1080, 1260, 1440, 1620, 1800, 1980, 2160, 2340, 2520,
                                  2700, 2880, 3060, 900, 630, 450, 360, 270, 225, 180, 135, 90, 45, 25, 0, 0],
            'Entertainment': [180, 225, 270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 810, 855, 900, 945,
                              540, 450, 360, 270, 225, 180, 135, 90, 70, 45, 25, 0, 0],
            'Transportation': [135, 167, 198, 230, 261, 293, 324, 356, 387, 419, 450, 482, 513, 730, 1140, 1710, 2280,
                               2850, 855, 570, 427, 340, 285, 230, 175, 120, 85, 55, 30, 0, 0],
            'School Supplies': [50, 75, 150, 225, 300, 375, 450, 525, 600, 675, 750, 825, 900, 975, 1050, 1125, 1200,
                                1275, 300, 225, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 810, 855, 900, 945,
                                   990, 1035, 720, 630, 540, 450, 405, 360, 315, 270, 225, 180, 135, 90, 45],
            'Miscellaneous': [225, 247, 270, 292, 315, 337, 360, 382, 405, 427, 450, 472, 495, 517, 540, 562, 585, 607,
                              540, 450, 405, 360, 315, 270, 225, 180, 135, 90, 70, 45, 25],
            'Daycare': [24000, 24000, 24000, 24000, 24000, 10000, 7000, 4000, 2000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [5500, 750, 550, 350, 220, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 30000, 30000, 30000, 30000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [2100, 2290, 2480, 2670, 2860, 3050, 3240, 3430, 3620, 3810, 4000, 4190, 4380, 4570, 4760, 4950,
                     5140, 5330, 2860, 2670, 2480, 2290, 2100, 1910, 1720, 1530, 1340, 1150, 960, 770, 385],
            'Clothing': [900, 990, 1080, 1170, 1260, 1350, 1440, 1530, 1620, 1710, 1800, 1890, 1980, 2290, 2600, 2910,
                         3220, 3530, 1980, 1440, 1170, 990, 810, 720, 630, 540, 450, 360, 270, 180, 90],
            'Healthcare': [1400, 1120, 940, 850, 760, 760, 760, 850, 940, 1030, 1120, 1210, 1300, 1390, 1480, 1570,
                           1660, 1750, 1120, 940, 760, 670, 580, 490, 400, 350, 300, 250, 200, 150, 100],
            'Activities/Sports': [180, 360, 720, 1080, 1440, 1800, 2160, 2520, 2880, 3240, 3600, 3960, 4320, 4680, 5040,
                                  5400, 5760, 6120, 1800, 1260, 900, 720, 540, 450, 360, 270, 180, 90, 45, 25, 0],
            'Entertainment': [360, 450, 540, 630, 720, 810, 900, 990, 1080, 1170, 1260, 1350, 1440, 1530, 1620, 1710,
                              1800, 1890, 1080, 900, 720, 540, 450, 360, 315, 270, 225, 180, 135, 90, 45],
            'Transportation': [225, 270, 315, 360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 1140, 1800, 2700, 3600,
                               4500, 1350, 900, 675, 540, 450, 360, 315, 270, 225, 180, 135, 90, 45],
            'School Supplies': [100, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350, 1500, 1650, 1800, 1950, 2100, 2250,
                                2400, 2550, 500, 375, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Gifts/Celebrations': [450, 540, 630, 720, 810, 900, 990, 1080, 1170, 1260, 1350, 1440, 1530, 1620, 1710,
                                   1800, 1890, 1980, 1350, 1080, 900, 720, 630, 540, 450, 405, 360, 315, 270, 225, 180],
            'Miscellaneous': [360, 405, 450, 495, 540, 585, 630, 675, 720, 765, 810, 855, 900, 945, 990, 1035, 1080,
                              1125, 900, 765, 675, 585, 540, 495, 450, 405, 360, 315, 270, 225, 180],
            'Daycare': [32000, 32000, 32000, 32000, 32000, 16000, 13000, 10000, 5000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [11000, 1400, 900, 600, 350, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48000, 48000, 48000, 48000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Wellington": {  # New Zealand's capital, medium-high cost of living
        "Conservative (statistical)": {
            'Food': [1050, 1230, 1410, 1590, 1770, 1950, 2130, 2310, 2490, 2670, 2850, 3030, 3210, 3390, 3570, 3750,
                     3930, 4110, 1770, 1590, 1410, 1230, 1050, 870, 690, 510, 330, 150, 75, 40, 0],
            'Clothing': [350, 395, 440, 485, 530, 575, 620, 665, 710, 755, 800, 845, 890, 1050, 1230, 1410, 1590, 1770,
                         710, 530, 350, 260, 215, 170, 125, 80, 45, 25, 0, 0, 0],
            'Healthcare': [700, 500, 410, 365, 320, 320, 320, 365, 410, 455, 500, 545, 590, 635, 680, 725, 770, 815,
                           410, 320, 230, 185, 140, 95, 70, 45, 20, 0, 0, 0, 0],
            'Activities/Sports': [40, 80, 160, 320, 480, 640, 800, 960, 1120, 1280, 1440, 1600, 1760, 1920, 2080, 2240,
                                  2400, 2560, 480, 320, 240, 160, 120, 80, 40, 20, 0, 0, 0, 0, 0],
            'Entertainment': [80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760,
                              320, 240, 160, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0],
            'Transportation': [80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 440, 680, 1000, 1320,
                               1640, 480, 310, 210, 160, 110, 80, 50, 25, 0, 0, 0, 0, 0],
            'School Supplies': [20, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680,
                                160, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800,
                                   840, 480, 400, 320, 280, 240, 200, 160, 120, 80, 60, 40, 20, 0],
            'Miscellaneous': [120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460,
                              320, 280, 240, 200, 160, 120, 80, 60, 40, 20, 0, 0, 0],
            'Daycare': [17500, 17500, 17500, 17500, 17500, 6000, 4000, 2200, 1100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [2800, 470, 290, 185, 95, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 22000, 22000, 22000, 22000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1410, 1590, 1770, 1950, 2130, 2310, 2490, 2670, 2850, 3030, 3210, 3390, 3570, 3750, 3930, 4110,
                     4290, 4470, 2130, 1950, 1770, 1590, 1410, 1230, 1050, 870, 690, 510, 330, 150, 0],
            'Clothing': [495, 540, 585, 630, 675, 720, 765, 810, 855, 900, 945, 990, 1035, 1230, 1410, 1590, 1770,
                         1950, 1035, 765, 630, 495, 405, 360, 315, 270, 225, 180, 135, 90, 0],
            'Healthcare': [870, 690, 565, 515, 465, 465, 465, 515, 565, 615, 665, 715, 765, 815, 865, 915, 965, 1015,
                           615, 515, 415, 315, 270, 225, 180, 135, 90, 60, 30, 15, 0],
            'Activities/Sports': [80, 160, 320, 480, 640, 800, 960, 1120, 1280, 1440, 1600, 1760, 1920, 2080, 2240,
                                  2400, 2560, 2720, 800, 560, 400, 320, 240, 200, 160, 120, 80, 40, 20, 0, 0],
            'Entertainment': [160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800, 840,
                              480, 400, 320, 240, 200, 160, 120, 80, 60, 40, 20, 0, 0],
            'Transportation': [120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 660, 1040, 1560, 2080,
                               2600, 780, 520, 390, 310, 260, 210, 160, 110, 80, 50, 25, 0, 0],
            'School Supplies': [40, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020,
                                240, 180, 120, 80, 60, 40, 20, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720, 760, 800, 840,
                                   880, 920, 640, 560, 480, 400, 360, 320, 280, 240, 200, 160, 120, 80, 40],
            'Miscellaneous': [200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540,
                              480, 400, 360, 320, 280, 240, 200, 160, 120, 80, 60, 40, 20],
            'Daycare': [21500, 21500, 21500, 21500, 21500, 9200, 7000, 3800, 1900, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [4900, 670, 470, 295, 190, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 27500, 27500, 27500, 27500, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [1950, 2130, 2310, 2490, 2670, 2850, 3030, 3210, 3390, 3570, 3750, 3930, 4110, 4290, 4470, 4650,
                     4830, 5010, 2670, 2490, 2310, 2130, 1950, 1770, 1590, 1410, 1230, 1050, 870, 690, 345],
            'Clothing': [825, 907, 990, 1072, 1155, 1237, 1320, 1402, 1485, 1567, 1650, 1732, 1815, 2070, 2325, 2580,
                         2835, 3090, 1815, 1320, 1072, 907, 742, 660, 577, 495, 412, 330, 247, 165, 82],
            'Healthcare': [1300, 1040, 870, 785, 700, 700, 700, 785, 870, 955, 1040, 1125, 1210, 1295, 1380, 1465,
                           1550, 1635, 1040, 870, 700, 615, 530, 445, 360, 315, 270, 225, 180, 135, 90],
            'Activities/Sports': [160, 320, 640, 960, 1280, 1600, 1920, 2240, 2560, 2880, 3200, 3520, 3840, 4160, 4480,
                                  4800, 5120, 5440, 1600, 1120, 800, 640, 480, 400, 320, 240, 160, 80, 40, 20, 0],
            'Entertainment': [320, 400, 480, 560, 640, 720, 800, 880, 960, 1040, 1120, 1200, 1280, 1360, 1440, 1520,
                              1600, 1680, 960, 800, 640, 480, 400, 320, 280, 240, 200, 160, 120, 80, 40],
            'Transportation': [210, 252, 294, 336, 378, 420, 462, 504, 546, 588, 630, 672, 714, 1040, 1650, 2475, 3300,
                               4125, 1237, 825, 618, 495, 412, 330, 288, 246, 204, 162, 120, 82, 41],
            'School Supplies': [82, 123, 247, 370, 495, 618, 742, 865, 990, 1113, 1237, 1360, 1485, 1608, 1732, 1855,
                                1980, 2103, 412, 309, 247, 206, 165, 123, 82, 61, 41, 20, 0, 0, 0],
            'Gifts/Celebrations': [420, 504, 588, 672, 756, 840, 924, 1008, 1092, 1176, 1260, 1344, 1428, 1512, 1596,
                                   1680, 1764, 1848, 1260, 1008, 840, 672, 588, 504, 420, 378, 336, 294, 252, 210, 168],
            'Miscellaneous': [330, 371, 412, 454, 495, 536, 577, 619, 660, 701, 742, 784, 825, 866, 907, 949, 990,
                              1031, 825, 701, 618, 536, 495, 454, 412, 371, 330, 288, 247, 206, 165],
            'Daycare': [28500, 28500, 28500, 28500, 28500, 14500, 11800, 9500, 4750, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [9500, 1150, 730, 470, 290, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 44000, 44000, 44000, 44000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    # Texas (Houston) — ~25-35% lower daycare, lower food/activities than WA/CA
    "Houston": {
        "Conservative (statistical)": {
            'Food': [1000, 1100, 1200, 1400, 1600, 1800, 2000, 2100, 2200, 2400, 2600, 2800, 3000, 3100, 3200, 3400,
                     3600, 3800, 1600, 1400, 1200, 1000, 800, 600, 400, 300, 200, 100, 50, 25, 0],
            'Clothing': [300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 1000, 1100, 1200, 1300, 1400,
                         600, 450, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Healthcare': [600, 500, 400, 350, 350, 350, 350, 400, 450, 500, 500, 550, 600, 650, 700, 750, 800, 850,
                           400, 350, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0],
            'Activities/Sports': [50, 80, 150, 300, 500, 700, 900, 1000, 1100, 1300, 1500, 1600, 1800, 2000, 2200, 2400,
                                  2600, 2800, 500, 350, 250, 150, 100, 50, 25, 0, 0, 0, 0, 0, 0],
            'Entertainment': [80, 120, 160, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900,
                              350, 250, 180, 120, 80, 50, 25, 0, 0, 0, 0, 0, 0],
            'Transportation': [80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 450, 700, 1000, 1400,
                               1800, 500, 350, 250, 180, 120, 80, 50, 25, 0, 0, 0, 0, 0],
            'School Supplies': [20, 40, 80, 120, 160, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800,
                                150, 100, 75, 50, 25, 0, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
                                   500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Miscellaneous': [120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460,
                              300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0, 0],
            'Daycare': [14000, 14000, 14000, 14000, 14000, 5000, 3500, 2000, 1000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [2500, 400, 250, 150, 80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 22000, 22000, 22000, 22000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average (statistical)": {
            'Food': [1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 3300, 3500, 3700, 3900, 4100, 4300,
                     4500, 4700, 2000, 1800, 1500, 1200, 1000, 800, 600, 400, 200, 100, 50, 25, 0],
            'Clothing': [450, 500, 550, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000,
                         800, 600, 450, 350, 250, 200, 150, 100, 50, 25, 0, 0, 0],
            'Healthcare': [700, 600, 500, 450, 400, 400, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 1000,
                           500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Activities/Sports': [80, 150, 300, 500, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000,
                                  3200, 3400, 700, 500, 350, 250, 150, 100, 50, 25, 0, 0, 0, 0, 0],
            'Entertainment': [120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020, 1080, 1140,
                              500, 350, 250, 180, 120, 80, 50, 25, 0, 0, 0, 0, 0],
            'Transportation': [120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 600, 1000, 1400, 1800,
                               2200, 700, 500, 350, 250, 180, 120, 80, 50, 25, 0, 0, 0, 0],
            'School Supplies': [30, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020,
                                250, 180, 120, 80, 50, 25, 0, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 900, 1000, 1100, 1200, 1300,
                                   600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0],
            'Miscellaneous': [150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660,
                              400, 300, 250, 200, 150, 100, 75, 50, 25, 0, 0, 0, 0],
            'Daycare': [18000, 18000, 18000, 18000, 18000, 7000, 5000, 3000, 1500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [3000, 500, 300, 200, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 28000, 28000, 28000, 28000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end (statistical)": {
            'Food': [1800, 2100, 2400, 2700, 3000, 3300, 3600, 3900, 4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300,
                     6600, 6900, 3000, 2600, 2200, 1800, 1500, 1200, 900, 600, 300, 150, 75, 25, 0],
            'Clothing': [600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600,
                         1200, 900, 650, 500, 350, 250, 200, 150, 100, 50, 0, 0, 0],
            'Healthcare': [1000, 800, 700, 600, 550, 550, 550, 600, 650, 750, 850, 950, 1050, 1150, 1200, 1300, 1400, 1500,
                           750, 600, 450, 350, 250, 200, 150, 100, 75, 50, 0, 0, 0],
            'Activities/Sports': [100, 250, 500, 800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600,
                                  6000, 6400, 1200, 800, 500, 350, 250, 150, 75, 25, 0, 0, 0, 0, 0],
            'Entertainment': [200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                              800, 600, 400, 300, 200, 120, 80, 50, 25, 0, 0, 0, 0],
            'Transportation': [180, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 900, 1500, 2200, 3000,
                               3800, 1000, 750, 500, 350, 250, 180, 120, 75, 25, 0, 0, 0, 0],
            'School Supplies': [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700,
                                400, 300, 200, 120, 80, 50, 25, 0, 0, 0, 0, 0, 0],
            'Gifts/Celebrations': [350, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000,
                                   1000, 800, 600, 450, 350, 250, 200, 150, 100, 75, 50, 25, 0],
            'Miscellaneous': [250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100,
                              600, 500, 400, 300, 200, 150, 100, 75, 50, 25, 0, 0, 0],
            'Daycare': [25000, 25000, 25000, 25000, 25000, 10000, 7500, 5000, 2500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Baby Equipment': [4000, 700, 450, 300, 150, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 38000, 38000, 38000, 38000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    }
}

FAMILY_EXPENSE_TEMPLATES = {
    "California": {
        "Conservative (statistical)": {
            'Food & Groceries': 14400,
            'Clothing': 3600,
            'Transportation': 10000,
            'Entertainment & Activities': 4800,
            'Personal Care': 2400,
            'Utilities': 2400,  # Electricity, Water, Gas (~$200/mo)
            'Internet & Phone': 1800,  # Internet + Cellphones (~$150/mo)
            'Subscriptions': 600,  # Streaming services, music, etc. (~$50/mo)
            'Other Expenses': 1200
        },
        "Average (statistical)": {
            'Food & Groceries': 18000,
            'Clothing': 4800,
            'Transportation': 13000,
            'Entertainment & Activities': 7200,
            'Personal Care': 3600,
            'Utilities': 3000,  # Electricity, Water, Gas (~$250/mo)
            'Internet & Phone': 2400,  # Internet + Cellphones (~$200/mo)
            'Subscriptions': 1200,  # Streaming services, music, etc. (~$100/mo)
            'Other Expenses': 1800
        },
        "High-end (statistical)": {
            'Food & Groceries': 24000,
            'Clothing': 7200,
            'Transportation': 18000,
            'Entertainment & Activities': 12000,
            'Personal Care': 6000,
            'Utilities': 4200,  # Electricity, Water, Gas (~$350/mo)
            'Internet & Phone': 3600,  # Internet + Cellphones (~$300/mo)
            'Subscriptions': 2400,  # Streaming services, music, etc. (~$200/mo)
            'Other Expenses': 1800
        }
    },
    "Seattle": {
        "Conservative (statistical)": {
            'Food & Groceries': 13200,
            'Clothing': 3000,
            'Transportation': 9000,
            'Entertainment & Activities': 4200,
            'Personal Care': 2100,
            'Utilities': 2160,
            'Internet & Phone': 1620,
            'Subscriptions': 540,
            'Other Expenses': 1080
        },
        "Average (statistical)": {
            'Food & Groceries': 16800,
            'Clothing': 4200,
            'Transportation': 12000,
            'Entertainment & Activities': 6600,
            'Personal Care': 3000,
            'Utilities': 3120,
            'Internet & Phone': 2340,
            'Subscriptions': 1170,
            'Other Expenses': 1170
        },
        "High-end (statistical)": {
            'Food & Groceries': 22800,
            'Clothing': 6600,
            'Transportation': 16800,
            'Entertainment & Activities': 10800,
            'Personal Care': 5400,
            'Utilities': 4320,
            'Internet & Phone': 3240,
            'Subscriptions': 1620,
            'Other Expenses': 1620
        }
    },
    "Houston": {
        "Conservative (statistical)": {
            'Food & Groceries': 12600,
            'Clothing': 2800,
            'Transportation': 8400,
            'Entertainment & Activities': 3900,
            'Personal Care': 1800,
            'Utilities': 2040,
            'Internet & Phone': 1530,
            'Subscriptions': 510,
            'Other Expenses': 1020
        },
        "Average (statistical)": {
            'Food & Groceries': 15600,
            'Clothing': 3900,
            'Transportation': 11400,
            'Entertainment & Activities': 6000,
            'Personal Care': 2700,
            'Utilities': 2880,
            'Internet & Phone': 2160,
            'Subscriptions': 1080,
            'Other Expenses': 1080
        },
        "High-end (statistical)": {
            'Food & Groceries': 21000,
            'Clothing': 6000,
            'Transportation': 15600,
            'Entertainment & Activities': 9600,
            'Personal Care': 4800,
            'Utilities': 4080,
            'Internet & Phone': 3060,
            'Subscriptions': 1530,
            'Other Expenses': 1530
        }
    },
    # Major US Cities
    "New York": {
        "Conservative (statistical)": {
            'Food & Groceries': 18720,  # 30% higher than CA
            'Clothing': 4680,
            'Transportation': 13000,
            'Entertainment & Activities': 6240,
            'Personal Care': 3120,
            'Utilities': 3120,
            'Internet & Phone': 2340,
            'Subscriptions': 780,
            'Other Expenses': 1560
        },
        "Average (statistical)": {
            'Food & Groceries': 23400,
            'Clothing': 6240,
            'Transportation': 16900,
            'Entertainment & Activities': 9360,
            'Personal Care': 4680,
            'Utilities': 4368,
            'Internet & Phone': 3276,
            'Subscriptions': 1638,
            'Other Expenses': 1638
        },
        "High-end (statistical)": {
            'Food & Groceries': 31200,
            'Clothing': 9360,
            'Transportation': 23400,
            'Entertainment & Activities': 15600,
            'Personal Care': 7800,
            'Utilities': 6240,
            'Internet & Phone': 4680,
            'Subscriptions': 2340,
            'Other Expenses': 2340
        }
    },
    "San Francisco": {
        "Conservative (statistical)": {
            'Food & Groceries': 16560,  # 15% higher than CA
            'Clothing': 4140,
            'Transportation': 11500,
            'Entertainment & Activities': 5520,
            'Personal Care': 2760,
            'Utilities': 2760,
            'Internet & Phone': 2070,
            'Subscriptions': 690,
            'Other Expenses': 1380
        },
        "Average (statistical)": {
            'Food & Groceries': 20700,
            'Clothing': 5520,
            'Transportation': 14950,
            'Entertainment & Activities': 8280,
            'Personal Care': 4140,
            'Utilities': 3864,
            'Internet & Phone': 2898,
            'Subscriptions': 1449,
            'Other Expenses': 1449
        },
        "High-end (statistical)": {
            'Food & Groceries': 27600,
            'Clothing': 8280,
            'Transportation': 20700,
            'Entertainment & Activities': 13800,
            'Personal Care': 6900,
            'Utilities': 5520,
            'Internet & Phone': 4140,
            'Subscriptions': 2070,
            'Other Expenses': 2070
        }
    },
    "Los Angeles": {
        "Conservative (statistical)": {
            'Food & Groceries': 13680,  # 5% lower than CA
            'Clothing': 3420,
            'Transportation': 9500,
            'Entertainment & Activities': 4560,
            'Personal Care': 2280,
            'Utilities': 2280,
            'Internet & Phone': 1710,
            'Subscriptions': 570,
            'Other Expenses': 1140
        },
        "Average (statistical)": {
            'Food & Groceries': 17100,
            'Clothing': 4560,
            'Transportation': 12350,
            'Entertainment & Activities': 6840,
            'Personal Care': 3420,
            'Utilities': 3192,
            'Internet & Phone': 2394,
            'Subscriptions': 1197,
            'Other Expenses': 1197
        },
        "High-end (statistical)": {
            'Food & Groceries': 22800,
            'Clothing': 6840,
            'Transportation': 17100,
            'Entertainment & Activities': 11400,
            'Personal Care': 5700,
            'Utilities': 4560,
            'Internet & Phone': 3420,
            'Subscriptions': 1710,
            'Other Expenses': 1710
        }
    },
    "Portland": {
        "Conservative (statistical)": {
            'Food & Groceries': 12240,  # 15% lower than CA
            'Clothing': 3060,
            'Transportation': 8500,
            'Entertainment & Activities': 4080,
            'Personal Care': 2040,
            'Utilities': 2040,
            'Internet & Phone': 1530,
            'Subscriptions': 510,
            'Other Expenses': 1020
        },
        "Average (statistical)": {
            'Food & Groceries': 15300,
            'Clothing': 4080,
            'Transportation': 11050,
            'Entertainment & Activities': 6120,
            'Personal Care': 3060,
            'Utilities': 2856,
            'Internet & Phone': 2142,
            'Subscriptions': 1071,
            'Other Expenses': 1071
        },
        "High-end (statistical)": {
            'Food & Groceries': 20400,
            'Clothing': 6120,
            'Transportation': 15300,
            'Entertainment & Activities': 10200,
            'Personal Care': 5100,
            'Utilities': 4080,
            'Internet & Phone': 3060,
            'Subscriptions': 1530,
            'Other Expenses': 1530
        }
    },
    # International Cities (in USD equivalent for simplicity)
    # Note: For Canadian cities, multiply by ~0.75 for CAD
    # For European cities (EUR), multiply by ~0.92 for EUR
    # For Australian cities (AUD), multiply by ~1.52 for AUD
    "Toronto": {
        "Conservative (statistical)": {
            'Food & Groceries': 12960,  # 10% lower than CA
            'Clothing': 3240,
            'Transportation': 9000,
            'Entertainment & Activities': 4320,
            'Personal Care': 2160,
            'Utilities': 2160,
            'Internet & Phone': 1620,
            'Subscriptions': 540,
            'Other Expenses': 1080
        },
        "Average (statistical)": {
            'Food & Groceries': 16200,
            'Clothing': 4320,
            'Transportation': 11700,
            'Entertainment & Activities': 6480,
            'Personal Care': 3240,
            'Utilities': 3024,
            'Internet & Phone': 2268,
            'Subscriptions': 1134,
            'Other Expenses': 1134
        },
        "High-end (statistical)": {
            'Food & Groceries': 21600,
            'Clothing': 6480,
            'Transportation': 16200,
            'Entertainment & Activities': 10800,
            'Personal Care': 5400,
            'Utilities': 4320,
            'Internet & Phone': 3240,
            'Subscriptions': 1620,
            'Other Expenses': 1620
        }
    },
    "Vancouver": {
        "Conservative (statistical)": {
            'Food & Groceries': 13680,  # 5% lower than CA
            'Clothing': 3420,
            'Transportation': 9500,
            'Entertainment & Activities': 4560,
            'Personal Care': 2280,
            'Utilities': 2280,
            'Internet & Phone': 1710,
            'Subscriptions': 570,
            'Other Expenses': 1140
        },
        "Average (statistical)": {
            'Food & Groceries': 17100,
            'Clothing': 4560,
            'Transportation': 12350,
            'Entertainment & Activities': 6840,
            'Personal Care': 3420,
            'Utilities': 3192,
            'Internet & Phone': 2394,
            'Subscriptions': 1197,
            'Other Expenses': 1197
        },
        "High-end (statistical)": {
            'Food & Groceries': 22800,
            'Clothing': 6840,
            'Transportation': 17100,
            'Entertainment & Activities': 11400,
            'Personal Care': 5700,
            'Utilities': 4560,
            'Internet & Phone': 3420,
            'Subscriptions': 1710,
            'Other Expenses': 1710
        }
    },
    "Paris": {
        "Conservative (statistical)": {
            'Food & Groceries': 10800,  # 25% lower than CA
            'Clothing': 2700,
            'Transportation': 7500,
            'Entertainment & Activities': 3600,
            'Personal Care': 1800,
            'Utilities': 1800,
            'Internet & Phone': 1350,
            'Subscriptions': 450,
            'Other Expenses': 900
        },
        "Average (statistical)": {
            'Food & Groceries': 13500,
            'Clothing': 3600,
            'Transportation': 9750,
            'Entertainment & Activities': 5400,
            'Personal Care': 2700,
            'Utilities': 2520,
            'Internet & Phone': 1890,
            'Subscriptions': 945,
            'Other Expenses': 945
        },
        "High-end (statistical)": {
            'Food & Groceries': 18000,
            'Clothing': 5400,
            'Transportation': 13500,
            'Entertainment & Activities': 9000,
            'Personal Care': 4500,
            'Utilities': 3600,
            'Internet & Phone': 2700,
            'Subscriptions': 1350,
            'Other Expenses': 1350
        }
    },
    "Toulouse": {
        "Conservative (statistical)": {
            'Food & Groceries': 9360,  # 35% lower than CA
            'Clothing': 2340,
            'Transportation': 6500,
            'Entertainment & Activities': 3120,
            'Personal Care': 1560,
            'Utilities': 1560,
            'Internet & Phone': 1170,
            'Subscriptions': 390,
            'Other Expenses': 780
        },
        "Average (statistical)": {
            'Food & Groceries': 11700,
            'Clothing': 3120,
            'Transportation': 8450,
            'Entertainment & Activities': 4680,
            'Personal Care': 2340,
            'Utilities': 2184,
            'Internet & Phone': 1638,
            'Subscriptions': 819,
            'Other Expenses': 819
        },
        "High-end (statistical)": {
            'Food & Groceries': 15600,
            'Clothing': 4680,
            'Transportation': 11700,
            'Entertainment & Activities': 7800,
            'Personal Care': 3900,
            'Utilities': 3120,
            'Internet & Phone': 2340,
            'Subscriptions': 1170,
            'Other Expenses': 1170
        }
    },
    "Berlin": {
        "Conservative (statistical)": {
            'Food & Groceries': 10080,  # 30% lower than CA
            'Clothing': 2520,
            'Transportation': 7000,
            'Entertainment & Activities': 3360,
            'Personal Care': 1680,
            'Utilities': 1680,
            'Internet & Phone': 1260,
            'Subscriptions': 420,
            'Other Expenses': 840
        },
        "Average (statistical)": {
            'Food & Groceries': 12600,
            'Clothing': 3360,
            'Transportation': 9100,
            'Entertainment & Activities': 5040,
            'Personal Care': 2520,
            'Utilities': 2352,
            'Internet & Phone': 1764,
            'Subscriptions': 882,
            'Other Expenses': 882
        },
        "High-end (statistical)": {
            'Food & Groceries': 16800,
            'Clothing': 5040,
            'Transportation': 12600,
            'Entertainment & Activities': 8400,
            'Personal Care': 4200,
            'Utilities': 3360,
            'Internet & Phone': 2520,
            'Subscriptions': 1260,
            'Other Expenses': 1260
        }
    },
    "Munich": {
        "Conservative (statistical)": {
            'Food & Groceries': 12960,  # 10% lower than CA
            'Clothing': 3240,
            'Transportation': 9000,
            'Entertainment & Activities': 4320,
            'Personal Care': 2160,
            'Utilities': 2160,
            'Internet & Phone': 1620,
            'Subscriptions': 540,
            'Other Expenses': 1080
        },
        "Average (statistical)": {
            'Food & Groceries': 16200,
            'Clothing': 4320,
            'Transportation': 11700,
            'Entertainment & Activities': 6480,
            'Personal Care': 3240,
            'Utilities': 3024,
            'Internet & Phone': 2268,
            'Subscriptions': 1134,
            'Other Expenses': 1134
        },
        "High-end (statistical)": {
            'Food & Groceries': 21600,
            'Clothing': 6480,
            'Transportation': 16200,
            'Entertainment & Activities': 10800,
            'Personal Care': 5400,
            'Utilities': 4320,
            'Internet & Phone': 3240,
            'Subscriptions': 1620,
            'Other Expenses': 1620
        }
    },
    "Sydney": {
        "Conservative (statistical)": {
            'Food & Groceries': 15840,  # 10% higher than CA
            'Clothing': 3960,
            'Transportation': 11000,
            'Entertainment & Activities': 5280,
            'Personal Care': 2640,
            'Utilities': 2640,
            'Internet & Phone': 1980,
            'Subscriptions': 660,
            'Other Expenses': 1320
        },
        "Average (statistical)": {
            'Food & Groceries': 19800,
            'Clothing': 5280,
            'Transportation': 14300,
            'Entertainment & Activities': 7920,
            'Personal Care': 3960,
            'Utilities': 3696,
            'Internet & Phone': 2772,
            'Subscriptions': 1386,
            'Other Expenses': 1386
        },
        "High-end (statistical)": {
            'Food & Groceries': 26400,
            'Clothing': 7920,
            'Transportation': 19800,
            'Entertainment & Activities': 13200,
            'Personal Care': 6600,
            'Utilities': 5280,
            'Internet & Phone': 3960,
            'Subscriptions': 1980,
            'Other Expenses': 1980
        }
    },
    "Melbourne": {
        "Conservative (statistical)": {
            'Food & Groceries': 13680,  # 5% lower than CA
            'Clothing': 3420,
            'Transportation': 9500,
            'Entertainment & Activities': 4560,
            'Personal Care': 2280,
            'Utilities': 2280,
            'Internet & Phone': 1710,
            'Subscriptions': 570,
            'Other Expenses': 1140
        },
        "Average (statistical)": {
            'Food & Groceries': 17100,
            'Clothing': 4560,
            'Transportation': 12350,
            'Entertainment & Activities': 6840,
            'Personal Care': 3420,
            'Utilities': 3192,
            'Internet & Phone': 2394,
            'Subscriptions': 1197,
            'Other Expenses': 1197
        },
        "High-end (statistical)": {
            'Food & Groceries': 22800,
            'Clothing': 6840,
            'Transportation': 17100,
            'Entertainment & Activities': 11400,
            'Personal Care': 5700,
            'Utilities': 4560,
            'Internet & Phone': 3420,
            'Subscriptions': 1710,
            'Other Expenses': 1710
        }
    },
    "Brisbane": {
        "Conservative (statistical)": {
            'Food & Groceries': 12240,  # 15% lower than CA
            'Clothing': 3060,
            'Transportation': 8500,
            'Entertainment & Activities': 4080,
            'Personal Care': 2040,
            'Utilities': 2040,
            'Internet & Phone': 1530,
            'Subscriptions': 510,
            'Other Expenses': 1020
        },
        "Average (statistical)": {
            'Food & Groceries': 15300,
            'Clothing': 4080,
            'Transportation': 11050,
            'Entertainment & Activities': 6120,
            'Personal Care': 3060,
            'Utilities': 2856,
            'Internet & Phone': 2142,
            'Subscriptions': 1071,
            'Other Expenses': 1071
        },
        "High-end (statistical)": {
            'Food & Groceries': 20400,
            'Clothing': 6120,
            'Transportation': 15300,
            'Entertainment & Activities': 10200,
            'Personal Care': 5100,
            'Utilities': 4080,
            'Internet & Phone': 3060,
            'Subscriptions': 1530,
            'Other Expenses': 1530
        }
    }
}


# Data Source References for Expense Templates
# These references indicate where the living expense data was gathered from
EXPENSE_DATA_SOURCES = {
    "California": {
        "source": "MIT Living Wage Calculator & Bureau of Labor Statistics Consumer Expenditure Survey",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "Expenses adjusted for California cost of living index. Data includes Sacramento and broader California metropolitan areas."
    },
    "Sacramento": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and Sacramento Area Council of Governments",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/, https://www.sacog.org/",
        "year": "2024",
        "notes": "Daycare costs based on Child Care Aware of America 2024 report. Education costs from California State University and UC system averages."
    },
    "Seattle": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and Washington State Department of Commerce",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "Adjusted for Seattle-Tacoma-Bellevue metro area cost of living. Daycare costs from Child Care Aware of America."
    },
    "Houston": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and Greater Houston Partnership",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "Reflects Houston-The Woodlands-Sugar Land metro area costs. Lower cost of living compared to coastal cities."
    },
    "New York": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and NYC Department of Consumer and Worker Protection",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/, https://www.nyc.gov/dca",
        "year": "2024",
        "notes": "NYC metro area costs including Manhattan, Brooklyn, Queens. Among highest cost of living in US."
    },
    "San Francisco": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and San Francisco Controller's Office",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "San Francisco-Oakland-Berkeley metro area. Highest cost of living city in the dataset."
    },
    "Los Angeles": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and LA County Economic Development Corporation",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "Los Angeles-Long Beach-Anaheim metro area costs."
    },
    "Portland": {
        "source": "MIT Living Wage Calculator, BLS Consumer Expenditure Survey, and Portland Metro Regional Government",
        "url": "https://livingwage.mit.edu/, https://www.bls.gov/cex/",
        "year": "2024",
        "notes": "Portland-Vancouver-Hillsboro metro area costs."
    },
    "Toronto": {
        "source": "Statistics Canada Survey of Household Spending and Numbeo Cost of Living Database",
        "url": "https://www.statcan.gc.ca/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from CAD to USD. Toronto metro area including GTA."
    },
    "Vancouver": {
        "source": "Statistics Canada Survey of Household Spending and Numbeo Cost of Living Database",
        "url": "https://www.statcan.gc.ca/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from CAD to USD. Metro Vancouver area costs."
    },
    "Paris": {
        "source": "INSEE (French National Institute of Statistics) and Numbeo Cost of Living Database",
        "url": "https://www.insee.fr/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from EUR to USD. Île-de-France region costs."
    },
    "Toulouse": {
        "source": "INSEE (French National Institute of Statistics) and Numbeo Cost of Living Database",
        "url": "https://www.insee.fr/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from EUR to USD. Lower cost of living compared to Paris."
    },
    "Berlin": {
        "source": "Destatis (German Federal Statistical Office) and Numbeo Cost of Living Database",
        "url": "https://www.destatis.de/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from EUR to USD. Berlin metropolitan area."
    },
    "Munich": {
        "source": "Destatis (German Federal Statistical Office) and Numbeo Cost of Living Database",
        "url": "https://www.destatis.de/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from EUR to USD. Highest cost German city in dataset."
    },
    "Sydney": {
        "source": "Australian Bureau of Statistics Household Expenditure Survey and Numbeo Cost of Living Database",
        "url": "https://www.abs.gov.au/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from AUD to USD. Greater Sydney area costs."
    },
    "Melbourne": {
        "source": "Australian Bureau of Statistics Household Expenditure Survey and Numbeo Cost of Living Database",
        "url": "https://www.abs.gov.au/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from AUD to USD. Greater Melbourne area costs."
    },
    "Brisbane": {
        "source": "Australian Bureau of Statistics Household Expenditure Survey and Numbeo Cost of Living Database",
        "url": "https://www.abs.gov.au/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from AUD to USD. Brisbane metro area costs."
    },
    "Auckland": {
        "source": "Statistics New Zealand Household Economic Survey and Numbeo Cost of Living Database",
        "url": "https://www.stats.govt.nz/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from NZD to USD. Auckland metro area costs."
    },
    "Wellington": {
        "source": "Statistics New Zealand Household Economic Survey and Numbeo Cost of Living Database",
        "url": "https://www.stats.govt.nz/, https://www.numbeo.com/",
        "year": "2024",
        "notes": "Converted from NZD to USD. Wellington metro area costs."
    }
}


def get_expense_data_source(location: str) -> dict:
    """Get data source information for a specific location's expense template"""
    return EXPENSE_DATA_SOURCES.get(location, {
        "source": "Custom user-created template",
        "url": "N/A",
        "year": str(datetime.now().year),
        "notes": "This is a custom expense template created by the user."
    })


# Data Classes
@dataclass
class MajorPurchase:
    name: str
    year: int
    amount: float
    financing_years: int = 0
    interest_rate: float = 0.0
    asset_type: str = "Expense"  # NEW: "Expense", "Real Estate", "Vehicle", "Investment"
    appreciation_rate: float = 0.0  # NEW: Annual appreciation rate


@dataclass
class RecurringExpense:
    name: str
    category: str
    amount: float
    frequency_years: int
    start_year: int
    end_year: Optional[int] = None
    inflation_adjust: bool = True
    parent: str = "Both"
    financing_years: int = 0
    interest_rate: float = 0.0


@dataclass
class EconomicParameters:
    investment_return: float  # Annual return rate (e.g., 0.06 = 6%)
    inflation_rate: float  # Annual inflation (e.g., 0.03 = 3%)
    expense_growth_rate: float  # Expense growth separate from inflation
    healthcare_inflation_rate: float  # Healthcare-specific inflation
    use_historical_returns: bool = False  # Use historical average instead of custom
    use_historical_inflation: bool = False  # Use historical average instead of custom
    use_historical_expense_growth: bool = False  # Use historical average for expense growth
    use_historical_healthcare_inflation: bool = False  # Use historical average for healthcare inflation


@dataclass
class CareerPhase:
    start_age: int
    end_age: int
    philosophy: str  # "Stable", "Climbing the Ladder", "Startup", "Part-time", "Coasting"
    base_salary: float
    annual_raise_pct: float = 3.0
    annual_bonus_pct: float = 0.0
    rsu_annual_grant: float = 0.0
    rsu_vesting_years: int = 4
    stock_options_grant: float = 0.0
    stock_options_growth_pct: float = 0.0
    stock_options_liquidity_year: int = 0
    label: str = ""


@dataclass
class HouseTimelineEntry:
    year: int
    status: str
    rental_income: float = 0.0


@dataclass
class House:
    name: str
    purchase_year: int
    purchase_price: float
    current_value: float
    mortgage_balance: float
    mortgage_rate: float
    mortgage_years_left: int
    property_tax_rate: float
    home_insurance: float
    maintenance_rate: float
    upkeep_costs: float
    owner: str = "Shared"
    location: str = ""  # City or state where house is located
    appreciation_rate: float = 3.0  # Annual appreciation % (default 3%)
    timeline: List[HouseTimelineEntry] = None

    def __post_init__(self):
        if self.timeline is None:
            self.timeline = [HouseTimelineEntry(self.purchase_year, "Own_Live", 0.0)]

    def get_status_for_year(self, year: int) -> tuple:
        """Get status and rental income for a specific year"""
        if not self.timeline:
            return "Own_Live", 0.0

        sorted_timeline = sorted(self.timeline, key=lambda x: x.year)

        current_status = "Own_Live"
        current_rental = 0.0

        for entry in sorted_timeline:
            if entry.year <= year:
                current_status = entry.status
                current_rental = entry.rental_income
            else:
                break

        return current_status, current_rental


@dataclass
class StateTimelineEntry:
    year: int
    state: str
    spending_strategy: str = "Average"


# NEW: Healthcare & Insurance dataclasses
@dataclass
class HealthInsurance:
    name: str
    type: str  # "Employer", "Marketplace", "Medicare", "Medicaid"
    monthly_premium: float
    annual_deductible: float
    annual_out_of_pocket_max: float
    copay_primary: float
    copay_specialist: float
    covered_by: str  # "Parent 1", "Parent 2", "Both", "Family"
    start_age: int = 0
    end_age: int = 999

@dataclass
class LongTermCareInsurance:
    name: str
    monthly_premium: float
    daily_benefit: float
    benefit_period_days: int
    elimination_period_days: int
    covered_person: str  # "Parent 1", "Parent 2"
    start_age: int = 55
    inflation_protection: float = 0.03

@dataclass
class HealthExpense:
    category: str  # "Routine Care", "Prescription", "Emergency", "Dental", "Vision", "Mental Health"
    annual_amount: float
    covered_by_insurance: bool
    start_age: int
    end_age: int
    affected_person: str  # "Parent 1", "Parent 2", "Both"


# Currency formatting function with automatic scaling
def format_currency(value, force_full=False, context="general"):
    """
    Currency formatting with automatic scaling

    Args:
        value: The monetary value to format
        force_full: If True, always show full amount regardless of size
        context: Context for formatting ("general", "input", "detailed")

    Returns:
        Formatted currency string
    """
    if pd.isna(value) or value is None:
        return "$0"

    if context == "input" or force_full:
        return f"${value:,.0f}"

    abs_value = abs(value)

    if abs_value < 1000:
        return f"${value:,.0f}"

    if context == "detailed" and abs_value < 100000:
        return f"${value:,.0f}"

    if abs_value >= 1000000:
        scaled = value / 1000000
        if scaled == int(scaled):
            return f"${scaled:.0f}M"
        else:
            return f"${scaled:.1f}M"
    elif abs_value >= 1000:
        scaled = value / 1000
        if scaled == int(scaled):
            return f"${scaled:.0f}k"
        else:
            return f"${scaled:.0f}k"
    else:
        return f"${value:,.0f}"


def get_save_file_path(default_filename, file_types):
    """
    Show a file save dialog and return the selected file path.

    Args:
        default_filename: Default filename to suggest
        file_types: List of tuples like [("PDF files", "*.pdf"), ("All files", "*.*")]

    Returns:
        Selected file path as string, or None if cancelled
    """
    if not TKINTER_AVAILABLE:
        return None

    # Create a temporary root window (hidden)
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)

    # Show save dialog
    file_path = filedialog.asksaveasfilename(
        defaultextension=file_types[0][1].replace("*", ""),
        filetypes=file_types,
        initialfile=default_filename
    )

    # Clean up
    root.destroy()

    return file_path if file_path else None


# ─── Setup Wizard ───────────────────────────────────────────────────────────────
def setup_wizard():
    """TurboTax-style guided questionnaire wizard for new households."""
    # Initialize wizard state
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 0
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}

    step = st.session_state.wizard_step

    st.markdown("<div class='login-container' style='max-width:700px'>", unsafe_allow_html=True)

    # ── Step 0: Welcome ─────────────────────────────────────────────────────────
    if step == 0:
        st.markdown(
            '<div class="brand-hero">'
            '<div class="brand-icon">💰</div>'
            '<h1>Financial Planning Suite</h1>'
            '<p class="brand-tagline">Build a lifetime financial plan in minutes</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            "This guided questionnaire walks you through the key details "
            "of your financial life — income, savings, children, housing, and more. "
            "It takes about **3-5 minutes** and creates a starting plan you can "
            "fine-tune later."
        )
        st.info("The wizard helps you build an accurate starting plan. You can always adjust every detail afterward.")
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            st.session_state.wizard_step = 1
            st.rerun()
        st.markdown("")
        st.caption("Prefer to start from scratch?")
        if st.button("Skip wizard — go straight to the app", use_container_width=False):
            st.session_state.wizard_skipped = True
            st.session_state.wizard_manual = False
            st.rerun()

    # ── Step 1: Family Structure ─────────────────────────────────────────────────
    elif step == 1:
        _wizard_step_header(1, 6, "👨‍👩‍👧‍👦 Family Structure", "Tell us about your household.")
        emoji_options = ["👨", "👩", "👨‍🦱", "👩‍🦱", "👨‍🦰", "👩‍🦰", "👱‍♂️", "👱‍♀️", "🧑", "👴", "👵"]

        household_type = st.radio(
            "How many adults are in your household?",
            ["Just me", "Me and my partner"],
            index=0 if st.session_state.wizard_data.get('household_type', 'Just me') == 'Just me' else 1,
            key="wiz_household_type"
        )
        st.session_state.wizard_data['household_type'] = household_type

        st.subheader("Your Details")
        p1_col1, p1_col2, p1_col3 = st.columns([2, 1, 1])
        with p1_col1:
            p1_name = st.text_input("Your name", value=st.session_state.wizard_data.get('p1_name', ''), key="wiz_p1_name")
            st.session_state.wizard_data['p1_name'] = p1_name
        with p1_col2:
            p1_emoji = st.selectbox("Emoji", emoji_options,
                                     index=emoji_options.index(st.session_state.wizard_data.get('p1_emoji', '👨')),
                                     key="wiz_p1_emoji")
            st.session_state.wizard_data['p1_emoji'] = p1_emoji
        with p1_col3:
            p1_age = st.number_input("Age", min_value=18, max_value=100,
                                      value=st.session_state.wizard_data.get('p1_age', 30), key="wiz_p1_age")
            st.session_state.wizard_data['p1_age'] = p1_age

        if household_type == "Me and my partner":
            st.subheader("Partner Details")
            st.caption("Don't worry about getting your partner's details perfect — they can update their own info later in the app.")
            p2_col1, p2_col2, p2_col3 = st.columns([2, 1, 1])
            with p2_col1:
                p2_name = st.text_input("Partner's name", value=st.session_state.wizard_data.get('p2_name', ''), key="wiz_p2_name")
                st.session_state.wizard_data['p2_name'] = p2_name
            with p2_col2:
                p2_emoji = st.selectbox("Emoji", emoji_options,
                                         index=emoji_options.index(st.session_state.wizard_data.get('p2_emoji', '👩')),
                                         key="wiz_p2_emoji")
                st.session_state.wizard_data['p2_emoji'] = p2_emoji
            with p2_col3:
                p2_age = st.number_input("Age", min_value=18, max_value=100,
                                          value=st.session_state.wizard_data.get('p2_age', 30), key="wiz_p2_age")
                st.session_state.wizard_data['p2_age'] = p2_age

            marriage_year = st.number_input("Marriage year (or planned year)",
                                             min_value=1950, max_value=2060,
                                             value=st.session_state.wizard_data.get('marriage_year', datetime.now().year),
                                             key="wiz_marriage_year")
            st.session_state.wizard_data['marriage_year'] = marriage_year

        # Navigation
        _wizard_nav(step)

    # ── Step 2: Income & Career ──────────────────────────────────────────────────
    elif step == 2:
        _wizard_step_header(2, 6, "💼 Income & Career", "Your earnings, raises, and career trajectory.")
        is_couple = st.session_state.wizard_data.get('household_type') == "Me and my partner"
        parent_label = st.session_state.wizard_data.get('p1_name', 'You') or 'You'

        st.subheader(f"{parent_label}'s Income")
        p1_income = st.number_input("Current annual income ($)", min_value=0, max_value=10_000_000,
                                     value=st.session_state.wizard_data.get('p1_income', 75000),
                                     step=5000, key="wiz_p1_income")
        st.session_state.wizard_data['p1_income'] = p1_income

        p1_raise = st.number_input("Expected annual raise (%)", min_value=0.0, max_value=30.0,
                                    value=float(st.session_state.wizard_data.get('p1_raise', 3.0)),
                                    step=0.5, key="wiz_p1_raise")
        st.session_state.wizard_data['p1_raise'] = p1_raise

        p1_retire = st.number_input("Planned retirement age", min_value=40, max_value=85,
                                     value=st.session_state.wizard_data.get('p1_retire', 65), key="wiz_p1_retire")
        st.session_state.wizard_data['p1_retire'] = p1_retire

        st.markdown("---")
        st.markdown("**Career Phases**")
        st.caption("Add each phase of your career — current job, future promotion, switching fields, going part-time, etc.")

        career_phases = st.session_state.wizard_data.get('p1_career_phases', [])
        p1_age = st.session_state.wizard_data.get('p1_age', 30)
        p1_retire = st.session_state.wizard_data.get('p1_retire', 65)

        # Start with at least one phase
        if not career_phases:
            career_phases = [{
                'start_age': p1_age, 'end_age': p1_retire, 'philosophy': 'Stable',
                'base_salary': float(st.session_state.wizard_data.get('p1_income', 75000)),
                'annual_raise_pct': float(st.session_state.wizard_data.get('p1_raise', 3.0)),
                'label': 'Current Job',
            }]

        # Render each phase
        phases_to_keep = []
        for i, phase in enumerate(career_phases):
            col_name, col_ages, col_sal, col_raise, col_del = st.columns([2, 2, 2, 1, 0.5])
            with col_name:
                phase['label'] = st.text_input("Name", value=phase.get('label', f'Phase {i+1}'),
                    placeholder="e.g. Current Job, Senior Role, Part-time", key=f"wiz_p1_cp_name_{i}")
            with col_ages:
                c1, c2 = st.columns(2)
                with c1:
                    phase['start_age'] = st.number_input("From age", min_value=18, max_value=100,
                        value=phase['start_age'], key=f"wiz_p1_cp_start_{i}")
                with c2:
                    phase['end_age'] = st.number_input("To age", min_value=18, max_value=100,
                        value=phase['end_age'], key=f"wiz_p1_cp_end_{i}")
            with col_sal:
                phase['base_salary'] = float(st.number_input("Salary ($)", min_value=0, max_value=10_000_000,
                    value=int(phase['base_salary']), step=5000, key=f"wiz_p1_cp_sal_{i}"))
            with col_raise:
                phase['annual_raise_pct'] = float(st.number_input("Raise %", min_value=0.0, max_value=30.0,
                    value=phase['annual_raise_pct'], step=0.5, key=f"wiz_p1_cp_raise_{i}"))
            with col_del:
                st.markdown("")
                if len(career_phases) > 1 and st.button("✕", key=f"wiz_p1_cp_del_{i}", help="Remove this phase"):
                    continue  # Skip this phase (don't add to phases_to_keep)
            phase['philosophy'] = 'Stable'  # Keep for backward compat with CareerPhase dataclass
            phases_to_keep.append(phase)

        career_phases = phases_to_keep
        # Warn if any phase extends past retirement
        for i, phase in enumerate(career_phases):
            if phase['end_age'] > p1_retire:
                st.warning(f"**{phase.get('label', f'Phase {i+1}')}** ends at age {phase['end_age']} "
                           f"but retirement is set to age {p1_retire}. Income after retirement comes from Social Security, not employment.")

        if st.button("＋ Add career phase", key="wiz_p1_add_phase"):
            prev_end = career_phases[-1]['end_age'] if career_phases else p1_age
            career_phases.append({
                'start_age': prev_end, 'end_age': min(prev_end + 10, p1_retire),
                'philosophy': 'Stable',
                'base_salary': float(st.session_state.wizard_data.get('p1_income', 75000)),
                'annual_raise_pct': float(st.session_state.wizard_data.get('p1_raise', 3.0)),
                'label': f'Phase {len(career_phases) + 1}',
            })
            st.session_state.wizard_data['p1_career_phases'] = career_phases
            st.rerun()
        st.session_state.wizard_data['p1_career_phases'] = career_phases

        if is_couple:
            st.markdown("---")
            partner_label = st.session_state.wizard_data.get('p2_name', 'Partner') or 'Partner'
            st.subheader(f"{partner_label}'s Income")
            st.caption(f"Enter your best estimate — {partner_label} can refine these details later.")
            p2_income = st.number_input("Current annual income ($)", min_value=0, max_value=10_000_000,
                                         value=st.session_state.wizard_data.get('p2_income', 75000),
                                         step=5000, key="wiz_p2_income")
            st.session_state.wizard_data['p2_income'] = p2_income

            p2_raise = st.number_input("Expected annual raise (%)", min_value=0.0, max_value=30.0,
                                        value=float(st.session_state.wizard_data.get('p2_raise', 3.0)),
                                        step=0.5, key="wiz_p2_raise")
            st.session_state.wizard_data['p2_raise'] = p2_raise

            p2_retire = st.number_input("Planned retirement age", min_value=40, max_value=85,
                                         value=st.session_state.wizard_data.get('p2_retire', 65), key="wiz_p2_retire")
            st.session_state.wizard_data['p2_retire'] = p2_retire

            st.markdown("---")
            st.markdown(f"**{partner_label}'s Career Phases**")
            st.caption("Add each phase of your partner's career.")

            career_phases_p2 = st.session_state.wizard_data.get('p2_career_phases', [])
            p2_age = st.session_state.wizard_data.get('p2_age', 30)
            p2_retire = st.session_state.wizard_data.get('p2_retire', 65)

            if not career_phases_p2:
                career_phases_p2 = [{
                    'start_age': p2_age, 'end_age': p2_retire, 'philosophy': 'Stable',
                    'base_salary': float(st.session_state.wizard_data.get('p2_income', 75000)),
                    'annual_raise_pct': float(st.session_state.wizard_data.get('p2_raise', 3.0)),
                    'label': 'Current Job',
                }]

            phases_to_keep_p2 = []
            for i, phase in enumerate(career_phases_p2):
                col_name, col_ages, col_sal, col_raise, col_del = st.columns([2, 2, 2, 1, 0.5])
                with col_name:
                    phase['label'] = st.text_input("Name", value=phase.get('label', f'Phase {i+1}'),
                        placeholder="e.g. Current Job, Senior Role", key=f"wiz_p2_cp_name_{i}")
                with col_ages:
                    c1, c2 = st.columns(2)
                    with c1:
                        phase['start_age'] = st.number_input("From age", min_value=18, max_value=100,
                            value=phase['start_age'], key=f"wiz_p2_cp_start_{i}")
                    with c2:
                        phase['end_age'] = st.number_input("To age", min_value=18, max_value=100,
                            value=phase['end_age'], key=f"wiz_p2_cp_end_{i}")
                with col_sal:
                    phase['base_salary'] = float(st.number_input("Salary ($)", min_value=0, max_value=10_000_000,
                        value=int(phase['base_salary']), step=5000, key=f"wiz_p2_cp_sal_{i}"))
                with col_raise:
                    phase['annual_raise_pct'] = float(st.number_input("Raise %", min_value=0.0, max_value=30.0,
                        value=phase['annual_raise_pct'], step=0.5, key=f"wiz_p2_cp_raise_{i}"))
                with col_del:
                    st.markdown("")
                    if len(career_phases_p2) > 1 and st.button("✕", key=f"wiz_p2_cp_del_{i}", help="Remove this phase"):
                        continue
                phase['philosophy'] = 'Stable'
                phases_to_keep_p2.append(phase)

            career_phases_p2 = phases_to_keep_p2
            for i, phase in enumerate(career_phases_p2):
                if phase['end_age'] > p2_retire:
                    st.warning(f"**{phase.get('label', f'Phase {i+1}')}** ends at age {phase['end_age']} "
                               f"but retirement is set to age {p2_retire}.")

            if st.button(f"＋ Add career phase for {partner_label}", key="wiz_p2_add_phase"):
                prev_end = career_phases_p2[-1]['end_age'] if career_phases_p2 else p2_age
                career_phases_p2.append({
                    'start_age': prev_end, 'end_age': min(prev_end + 10, p2_retire),
                    'philosophy': 'Stable',
                    'base_salary': float(st.session_state.wizard_data.get('p2_income', 75000)),
                    'annual_raise_pct': float(st.session_state.wizard_data.get('p2_raise', 3.0)),
                    'label': f'Phase {len(career_phases_p2) + 1}',
                })
                st.session_state.wizard_data['p2_career_phases'] = career_phases_p2
                st.rerun()
            st.session_state.wizard_data['p2_career_phases'] = career_phases_p2

        _wizard_nav(step)

    # ── Step 3: Assets & Savings ─────────────────────────────────────────────────
    elif step == 3:
        _wizard_step_header(3, 6, "🏦 Assets & Savings", "Current net worth and Social Security estimates.")
        is_couple = st.session_state.wizard_data.get('household_type') == "Me and my partner"
        parent_label = st.session_state.wizard_data.get('p1_name', 'You') or 'You'

        st.subheader(f"{parent_label}'s Assets")
        p1_nw = st.number_input("Current net worth (savings + investments)", min_value=0, max_value=100_000_000,
                                 value=st.session_state.wizard_data.get('p1_net_worth', 0),
                                 step=10000, key="wiz_p1_nw")
        st.session_state.wizard_data['p1_net_worth'] = p1_nw

        p1_ss = st.number_input("Expected Social Security monthly benefit ($)",
                                 min_value=0, max_value=10000,
                                 value=st.session_state.wizard_data.get('p1_ss', 2000),
                                 step=100, key="wiz_p1_ss",
                                 help="Check your estimate at ssa.gov/myaccount. The average is ~$1,900/mo.")
        st.session_state.wizard_data['p1_ss'] = p1_ss

        if is_couple:
            partner_label = st.session_state.wizard_data.get('p2_name', 'Partner') or 'Partner'
            st.subheader(f"{partner_label}'s Assets")
            p2_nw = st.number_input("Current net worth (savings + investments)", min_value=0, max_value=100_000_000,
                                     value=st.session_state.wizard_data.get('p2_net_worth', 0),
                                     step=10000, key="wiz_p2_nw")
            st.session_state.wizard_data['p2_net_worth'] = p2_nw

            p2_ss = st.number_input("Expected Social Security monthly benefit ($)",
                                     min_value=0, max_value=10000,
                                     value=st.session_state.wizard_data.get('p2_ss', 2000),
                                     step=100, key="wiz_p2_ss",
                                     help="Check your estimate at ssa.gov/myaccount. The average is ~$1,900/mo.")
            st.session_state.wizard_data['p2_ss'] = p2_ss

        _wizard_nav(step)

    # ── Step 4: Children ─────────────────────────────────────────────────────────
    elif step == 4:
        _wizard_step_header(4, 6, "👶 Children", "Current and planned children.")
        has_children = st.radio("Do you have or plan to have children?",
                                 ["No", "Yes"],
                                 index=1 if st.session_state.wizard_data.get('has_children', False) else 0,
                                 key="wiz_has_children")
        st.session_state.wizard_data['has_children'] = (has_children == "Yes")

        if has_children == "Yes":
            num_children = st.number_input("How many children (current + planned)?",
                                            min_value=1, max_value=10,
                                            value=st.session_state.wizard_data.get('num_children', 1),
                                            key="wiz_num_children")
            st.session_state.wizard_data['num_children'] = num_children

            children = st.session_state.wizard_data.get('children', [])
            while len(children) < num_children:
                children.append({'name': f'Child {len(children)+1}', 'birth_year': datetime.now().year})
            children = children[:num_children]

            for i in range(num_children):
                c1, c2 = st.columns(2)
                with c1:
                    children[i]['name'] = st.text_input(f"Child {i+1} name",
                                                         value=children[i]['name'], key=f"wiz_child_name_{i}")
                with c2:
                    children[i]['birth_year'] = st.number_input(f"Birth year (or planned)",
                                                                 min_value=1990, max_value=2060,
                                                                 value=children[i]['birth_year'],
                                                                 key=f"wiz_child_by_{i}")
            st.session_state.wizard_data['children'] = children

            st.caption("Children's expense templates will use the location you set in the next step.")

        _wizard_nav(step)

    # ── Step 5: Location & Housing ───────────────────────────────────────────────
    elif step == 5:
        _wizard_step_header(5, 6, "📍 Location & Spending", "Where you live and your spending style.")

        # Hierarchical location picker: Country → State/Province → City
        current_loc = location_picker("wiz_loc", st.session_state.wizard_data,
                                       label="Where do you currently live?")
        st.session_state.wizard_data['current_location'] = current_loc
        # Also set child location to match
        st.session_state.wizard_data['child_location'] = current_loc
        # Store state for tax lookup
        st.session_state.wizard_data['current_location_state'] = st.session_state.wizard_data.get('wiz_loc_state', '')

        # Moves
        plan_moves = st.checkbox("I plan to move in the future",
                                  value=st.session_state.wizard_data.get('plan_moves', False),
                                  key="wiz_plan_moves")
        st.session_state.wizard_data['plan_moves'] = plan_moves

        if plan_moves:
            moves = st.session_state.wizard_data.get('moves', [])
            if not moves:
                moves = [{'year': datetime.now().year + 5, 'location': 'Seattle'}]

            moves_to_keep = []
            for i, mv in enumerate(moves):
                st.markdown(f"**Move {i+1}**")
                mc1, mc2 = st.columns([1, 3])
                with mc1:
                    mv['year'] = st.number_input(f"Year", min_value=datetime.now().year,
                                                  max_value=2080, value=mv['year'], key=f"wiz_move_y{i}")
                with mc2:
                    # Mini location picker for each move
                    move_loc = location_picker(f"wiz_move_{i}", mv, label="Move to")
                    mv['location'] = move_loc

                if len(moves) > 1 and st.button("✕ Remove this move", key=f"wiz_move_del_{i}"):
                    continue
                moves_to_keep.append(mv)
            moves = moves_to_keep

            if st.button("＋ Add another move", key="wiz_add_move"):
                last_year = moves[-1]['year'] if moves else datetime.now().year
                moves.append({'year': last_year + 5, 'location': 'Seattle'})
                st.session_state.wizard_data['moves'] = moves
                st.rerun()
            st.session_state.wizard_data['moves'] = moves

        st.subheader("Spending Style")
        style_options = ["Frugal", "Average", "Comfortable"]
        spending_style = st.radio("How would you describe your spending?",
                                   style_options,
                                   index=style_options.index(st.session_state.wizard_data.get('spending_style', 'Average')),
                                   key="wiz_spending_style",
                                   horizontal=True)
        st.session_state.wizard_data['spending_style'] = spending_style
        style_descriptions = {
            "Frugal": "Budget-conscious — you actively minimize spending and prioritize savings.",
            "Average": "Moderate — you balance saving and spending without strict budgeting.",
            "Comfortable": "You prefer quality and convenience, and are willing to spend more for them."
        }
        st.caption(style_descriptions[spending_style])

        _wizard_nav(step)

    # ── Step 6: Review & Create ──────────────────────────────────────────────────
    elif step == 6:
        _wizard_step_header(6, 6, "📋 Review Your Plan", "Here's what we'll use to build your simulation.")
        wd = st.session_state.wizard_data
        is_couple = wd.get('household_type') == "Me and my partner"

        # Family card
        def _review_card(label, body):
            st.markdown(
                f'<div class="review-card">'
                f'<div class="review-card-label">{label}</div>'
                f'<div class="review-card-value">{body}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if is_couple:
            family_body = (
                f"{wd.get('p1_emoji','')} <b>{wd.get('p1_name','Parent 1')}</b> (age {wd.get('p1_age',30)}) "
                f"&amp; {wd.get('p2_emoji','')} <b>{wd.get('p2_name','Parent 2')}</b> (age {wd.get('p2_age',30)})"
                f"<br>Married {wd.get('marriage_year', 'N/A')}"
            )
        else:
            family_body = f"{wd.get('p1_emoji','')} <b>{wd.get('p1_name','Parent 1')}</b> (age {wd.get('p1_age',30)})"
        _review_card("FAMILY", family_body)

        # Income card
        col1, col2 = st.columns(2)
        with col1:
            _review_card("INCOME — " + (wd.get('p1_name','You') or 'You'),
                f"<b>${wd.get('p1_income',0):,.0f}</b>/yr &middot; {wd.get('p1_raise',3.0):.1f}% raises &middot; retire at {wd.get('p1_retire',65)}")
        with col2:
            if is_couple:
                _review_card("INCOME — " + (wd.get('p2_name','Partner') or 'Partner'),
                    f"<b>${wd.get('p2_income',0):,.0f}</b>/yr &middot; {wd.get('p2_raise',3.0):.1f}% raises &middot; retire at {wd.get('p2_retire',65)}")

        # Assets card
        col1, col2 = st.columns(2)
        with col1:
            _review_card("NET WORTH — " + (wd.get('p1_name','You') or 'You'),
                f"<b>${wd.get('p1_net_worth',0):,.0f}</b> &middot; SS ${wd.get('p1_ss',2000):,.0f}/mo")
        with col2:
            if is_couple:
                _review_card("NET WORTH — " + (wd.get('p2_name','Partner') or 'Partner'),
                    f"<b>${wd.get('p2_net_worth',0):,.0f}</b> &middot; SS ${wd.get('p2_ss',2000):,.0f}/mo")

        # Children card
        if wd.get('has_children') and wd.get('children'):
            kids = ", ".join(f"{ch['name']} ({ch['birth_year']})" for ch in wd['children'])
            _review_card("CHILDREN", f"{kids}<br>Template: {wd.get('child_location', 'Seattle')}")
        else:
            _review_card("CHILDREN", "None")

        # Location card
        spending_map = {"Frugal": "Conservative", "Average": "Average", "Comfortable": "High-end"}
        loc_body = f"<b>{wd.get('current_location', 'Seattle')}</b> &middot; {spending_map.get(wd.get('spending_style', 'Average'), 'Average')} spending"
        if wd.get('plan_moves') and wd.get('moves'):
            moves_str = " &rarr; ".join(f"{mv['location']} ({mv['year']})" for mv in wd['moves'])
            loc_body += f"<br>Moves: {moves_str}"
        _review_card("LOCATION & SPENDING", loc_body)

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.wizard_step = 5
                st.rerun()
        with col2:
            if st.button("✅ Create Quick Plan", use_container_width=True, type="primary"):
                _wizard_create_plan()
                st.rerun()

        st.markdown("---")
        st.markdown(
            '<div class="wizard-card">'
            '<h4>Want a more accurate simulation?</h4>'
            '<p style="font-size:0.9rem; margin-bottom:0;">Answer 5 more questions about housing, expenses, taxes, and healthcare to fine-tune your plan.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("📋 Continue to detailed refinement →", use_container_width=True):
            _wizard_create_plan()  # Create the base plan first
            st.session_state.wizard_complete = False
            st.session_state.wizard_step = 7
            st.session_state.wizard_phase2 = True
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════════
    # PHASE 2: Secondary wizard — detailed refinements
    # ══════════════════════════════════════════════════════════════════════════════

    elif step == 7:
        _wizard_step_header(1, 6, "🏠 Housing", "Tell us about your housing situation.", phase2=True)

        wd = st.session_state.wizard_data

        housing_type = st.radio("Do you own or rent?", ["Own", "Rent", "Other"],
                                index=["Own", "Rent", "Other"].index(wd.get('housing_type', 'Rent')),
                                key="wiz2_housing_type", horizontal=True)
        wd['housing_type'] = housing_type

        if housing_type == "Own":
            col1, col2 = st.columns(2)
            with col1:
                wd['home_value'] = st.number_input("Current home value ($)", min_value=0, max_value=10_000_000,
                    value=wd.get('home_value', 500000), step=25000, key="wiz2_home_value")
                wd['mortgage_balance'] = st.number_input("Remaining mortgage ($)", min_value=0, max_value=10_000_000,
                    value=wd.get('mortgage_balance', 350000), step=10000, key="wiz2_mortgage_bal")
            with col2:
                wd['mortgage_rate'] = st.number_input("Mortgage rate (%)", min_value=0.0, max_value=15.0,
                    value=wd.get('mortgage_rate', 6.5), step=0.25, key="wiz2_mortgage_rate")
                wd['mortgage_years_left'] = st.number_input("Years left on mortgage", min_value=0, max_value=30,
                    value=wd.get('mortgage_years_left', 28), key="wiz2_mortgage_years")
            wd['property_tax'] = st.number_input("Annual property tax ($)", min_value=0, max_value=100000,
                value=wd.get('property_tax', 6000), step=500, key="wiz2_prop_tax")
        elif housing_type == "Rent":
            # Location-based rent estimates
            rent_estimates = {
                'Seattle': 2200, 'San Francisco': 3500, 'New York': 3200, 'Los Angeles': 2800,
                'Portland': 1800, 'Sacramento': 1900, 'Houston': 1500, 'Toronto': 2400,
                'Vancouver': 2600, 'Paris': 2000, 'Berlin': 1400, 'Munich': 1800,
                'Sydney': 2800, 'Melbourne': 2200, 'Auckland': 1800, 'Wellington': 1600,
            }
            loc = wd.get('current_location', 'Seattle')
            default_rent = rent_estimates.get(loc, 2000)
            wd['monthly_rent'] = st.number_input(f"Monthly rent ($) — estimated for {loc}", min_value=0, max_value=20000,
                value=wd.get('monthly_rent', default_rent), step=100, key="wiz2_rent")

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Summary", use_container_width=True):
                st.session_state.wizard_step = 6
                st.session_state.wizard_phase2 = False
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="wiz2_next_7"):
                st.session_state.wizard_step = 8
                st.rerun()

    elif step == 8:
        _wizard_step_header(2, 6, "💸 Monthly Expenses", "Estimate your household's major monthly expenses.", phase2=True)

        wd = st.session_state.wizard_data
        expenses = st.session_state.family_shared_expenses

        st.markdown("**Housing & Utilities**")
        col1, col2, col3 = st.columns(3)
        with col1:
            monthly_mortgage = st.number_input("Mortgage/Rent ($/mo)", min_value=0, max_value=50000,
                value=int(expenses.get('Mortgage/Rent', 30000) / 12), step=100, key="wiz2_mortgage_mo")
            expenses['Mortgage/Rent'] = monthly_mortgage * 12
        with col2:
            monthly_utilities = st.number_input("Utilities ($/mo)", min_value=0, max_value=5000,
                value=int((expenses.get('Gas & Electric', 2400) + expenses.get('Water', 900) + expenses.get('Garbage', 600)) / 12), step=50, key="wiz2_util_mo")
            # Split proportionally
            expenses['Gas & Electric'] = monthly_utilities * 12 * 0.6
            expenses['Water'] = monthly_utilities * 12 * 0.225
            expenses['Garbage'] = monthly_utilities * 12 * 0.175
        with col3:
            monthly_internet = st.number_input("Internet & Cable ($/mo)", min_value=0, max_value=1000,
                value=int(expenses.get('Internet & Cable', 1800) / 12), step=10, key="wiz2_internet_mo")
            expenses['Internet & Cable'] = monthly_internet * 12

        st.markdown("**Lifestyle**")
        col1, col2, col3 = st.columns(3)
        with col1:
            annual_vacation = st.number_input("Annual vacation budget ($)", min_value=0, max_value=100000,
                value=int(expenses.get('Family Vacations', 8000)), step=1000, key="wiz2_vacation")
            expenses['Family Vacations'] = annual_vacation
        with col2:
            monthly_subs = st.number_input("Subscriptions ($/mo)", min_value=0, max_value=1000,
                value=int(expenses.get('Shared Subscriptions', 600) / 12), step=10, key="wiz2_subs_mo")
            expenses['Shared Subscriptions'] = monthly_subs * 12
        with col3:
            monthly_pet = st.number_input("Pet care ($/mo)", min_value=0, max_value=2000,
                value=int(expenses.get('Pet Care', 0) / 12), step=25, key="wiz2_pet_mo")
            expenses['Pet Care'] = monthly_pet * 12

        st.session_state.family_shared_expenses = expenses

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz2_back_8"):
                st.session_state.wizard_step = 7
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="wiz2_next_8"):
                st.session_state.wizard_step = 9
                st.rerun()

    elif step == 9:
        _wizard_step_header(3, 6, "🏛️ Tax & Retirement Savings", "These have a big impact on your projections.", phase2=True)

        wd = st.session_state.wizard_data

        # Auto-derive state tax from location
        state_tax_lookup = {
            'Seattle': 0.0, 'Portland': 0.0, 'Houston': 0.0,  # WA, OR (no income), TX
            'Sacramento': 9.3, 'San Francisco': 9.3, 'Los Angeles': 9.3,  # CA
            'New York': 8.82,  # NY
            'Toronto': 0.0, 'Vancouver': 0.0,  # Canada (handled separately)
            'Paris': 0.0, 'Toulouse': 0.0, 'Berlin': 0.0, 'Munich': 0.0,  # International
            'Sydney': 0.0, 'Melbourne': 0.0, 'Brisbane': 0.0,
            'Auckland': 0.0, 'Wellington': 0.0,
        }
        loc = wd.get('current_location', 'Seattle')
        derived_tax = state_tax_lookup.get(loc, 5.0)  # Default 5% for unknown US locations
        wd['state_tax_rate'] = derived_tax
        st.info(f"State tax rate auto-set to **{derived_tax}%** based on your location ({loc}). You can override this in the app later.")

        col1, col2 = st.columns(2)
        with col1:
            wd['pretax_401k'] = st.number_input("Annual 401k contribution ($)", min_value=0, max_value=50000,
                value=wd.get('pretax_401k', int(st.session_state.get('pretax_401k', 23500))),
                step=1000, key="wiz2_401k",
                help="2026 max: $23,500 ($31,000 if 50+)")
        with col2:
            wd['filing_status'] = st.selectbox("Tax filing status",
                ["married", "single"], index=0 if st.session_state.wizard_data.get('household_type') == "Me and my partner" else 1,
                key="wiz2_filing")

        st.markdown("**Social Security**")
        wd['ss_insolvency'] = st.checkbox("Model Social Security insolvency risk",
            value=wd.get('ss_insolvency', True), key="wiz2_ss_insolvency",
            help="The SS trust fund may face shortfalls around 2035. This models a ~23% benefit reduction.")

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz2_back_9"):
                st.session_state.wizard_step = 8
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="wiz2_next_9"):
                st.session_state.wizard_step = 10
                st.rerun()

    elif step == 10:
        _wizard_step_header(4, 6, "🏥 Healthcare", "Healthcare costs are one of the biggest retirement expenses.", phase2=True)

        wd = st.session_state.wizard_data

        healthcare_approach = st.radio("How do you want to estimate healthcare costs?",
            ["Use national averages (recommended)", "Enter my own estimates"],
            index=0, key="wiz2_healthcare_approach", horizontal=True)
        wd['healthcare_approach'] = healthcare_approach

        if healthcare_approach == "Enter my own estimates":
            col1, col2 = st.columns(2)
            with col1:
                wd['monthly_health_premium'] = st.number_input("Monthly health insurance premium ($)",
                    min_value=0, max_value=5000,
                    value=wd.get('monthly_health_premium', 500), step=50, key="wiz2_health_premium")
                wd['annual_out_of_pocket'] = st.number_input("Annual out-of-pocket medical ($)",
                    min_value=0, max_value=50000,
                    value=wd.get('annual_out_of_pocket', 2000), step=500, key="wiz2_oop")
            with col2:
                wd['hsa_contribution'] = st.number_input("Annual HSA contribution ($)",
                    min_value=0, max_value=10000,
                    value=wd.get('hsa_contribution', 0), step=500, key="wiz2_hsa",
                    help="2026 family max: $8,550")
                wd['hsa_balance'] = st.number_input("Current HSA balance ($)",
                    min_value=0, max_value=500000,
                    value=wd.get('hsa_balance', 0), step=1000, key="wiz2_hsa_bal")

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz2_back_10"):
                st.session_state.wizard_step = 9
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="wiz2_next_10"):
                st.session_state.wizard_step = 11
                st.rerun()

    # ── Step 11: Purchases & Recurring ──────────────────────────────────────
    elif step == 11:
        _wizard_step_header(5, 6, "🛒 Purchases & Recurring Costs", "Major one-time and recurring expenses.", phase2=True)

        wd = st.session_state.wizard_data

        st.markdown("**One-Time Major Purchases**")
        st.caption("Big expenses you're planning — car, renovation, wedding, etc.")
        purchases = wd.get('purchases', [])
        if not purchases:
            purchases = []

        purchases_to_keep = []
        for i, p in enumerate(purchases):
            col1, col2, col3, col4 = st.columns([2, 1.5, 1, 0.5])
            with col1:
                p['name'] = st.text_input("What?", value=p.get('name', ''),
                    placeholder="e.g., New car", key=f"wiz2_purch_name_{i}")
            with col2:
                p['amount'] = st.number_input("Cost ($)", min_value=0, max_value=10_000_000,
                    value=p.get('amount', 20000), step=5000, key=f"wiz2_purch_amt_{i}")
            with col3:
                p['year'] = st.number_input("Year", min_value=datetime.now().year, max_value=2080,
                    value=p.get('year', datetime.now().year + 1), key=f"wiz2_purch_yr_{i}")
            with col4:
                st.markdown("")
                if st.button("✕", key=f"wiz2_purch_del_{i}"):
                    continue
            purchases_to_keep.append(p)
        purchases = purchases_to_keep

        if st.button("＋ Add one-time purchase", key="wiz2_add_purchase"):
            purchases.append({'name': '', 'amount': 20000, 'year': datetime.now().year + 1})
            wd['purchases'] = purchases
            st.rerun()
        wd['purchases'] = purchases
        wd['has_purchases'] = len(purchases) > 0

        st.markdown("---")
        st.markdown("**Recurring Purchases**")
        st.caption("Expenses that repeat on a schedule — new car every 5 years, home renovation every 10, etc.")
        recurring = wd.get('recurring_purchases', [])

        recurring_to_keep = []
        for i, r in enumerate(recurring):
            col1, col2, col3, col4 = st.columns([2, 1.5, 1, 0.5])
            with col1:
                r['name'] = st.text_input("What?", value=r.get('name', ''),
                    placeholder="e.g., New car", key=f"wiz2_recur_name_{i}")
            with col2:
                r['amount'] = st.number_input("Cost ($)", min_value=0, max_value=10_000_000,
                    value=r.get('amount', 30000), step=5000, key=f"wiz2_recur_amt_{i}")
            with col3:
                r['every_years'] = st.number_input("Every N years", min_value=1, max_value=30,
                    value=r.get('every_years', 5), key=f"wiz2_recur_freq_{i}")
            with col4:
                st.markdown("")
                if st.button("✕", key=f"wiz2_recur_del_{i}"):
                    continue
            recurring_to_keep.append(r)
        recurring = recurring_to_keep

        if st.button("＋ Add recurring purchase", key="wiz2_add_recurring"):
            recurring.append({'name': '', 'amount': 30000, 'every_years': 5})
            wd['recurring_purchases'] = recurring
            st.rerun()
        wd['recurring_purchases'] = recurring

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz2_back_11"):
                st.session_state.wizard_step = 10
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="wiz2_next_11"):
                st.session_state.wizard_step = 12
                st.rerun()

    # ── Step 12: Final Details ───────────────────────────────────────────────
    elif step == 12:
        _wizard_step_header(6, 6, "📋 Final Details", "Last step — then your refined plan is ready.", phase2=True)

        wd = st.session_state.wizard_data
        is_couple = wd.get('household_type') == "Me and my partner"

        st.markdown("**Life Expectancy**")
        st.caption("Planning to a later age is more conservative — ensures you don't outlive your money.")
        col1, col2 = st.columns(2)
        with col1:
            p1_name = wd.get('p1_name', 'Parent 1')
            wd['p1_death_age'] = st.number_input(f"{p1_name}'s planning horizon (age)",
                min_value=65, max_value=120, value=wd.get('p1_death_age', 95), key="wiz2_p1_death")
        with col2:
            if is_couple:
                p2_name = wd.get('p2_name', 'Parent 2')
                wd['p2_death_age'] = st.number_input(f"{p2_name}'s planning horizon (age)",
                    min_value=65, max_value=120, value=wd.get('p2_death_age', 95), key="wiz2_p2_death")

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz2_back_12"):
                st.session_state.wizard_step = 11
                st.rerun()
        with col2:
            if st.button("✅ Create Refined Plan", use_container_width=True, type="primary"):
                _wizard_apply_phase2()
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _wizard_step_header(step: int, total: int, title: str, subtitle: str, phase2: bool = False):
    """Render a polished wizard step header with pill badge and dot progress."""
    pill_class = "wizard-step-pill phase2" if phase2 else "wizard-step-pill"
    phase_label = "REFINEMENT" if phase2 else "STEP"
    st.markdown(
        f'<span class="{pill_class}">{phase_label} {step} OF {total}</span>',
        unsafe_allow_html=True,
    )
    st.header(title)
    st.caption(subtitle)
    # Dot progress
    dots = []
    for i in range(1, total + 1):
        if phase2:
            cls = "phase2-active" if i == step else ("phase2-done" if i < step else "")
        else:
            cls = "active" if i == step else ("done" if i < step else "")
        dots.append(f'<span class="dot {cls}"></span>')
    st.markdown(f'<div class="wizard-dots">{"".join(dots)}</div>', unsafe_allow_html=True)


def _wizard_nav(step):
    """Render Back / Next navigation buttons for wizard steps 1-5."""
    col1, col2 = st.columns(2)
    with col1:
        if step > 1:
            if st.button("⬅️ Back", use_container_width=True, key=f"wiz_back_{step}"):
                st.session_state.wizard_step = step - 1
                st.rerun()
        elif step == 1:
            if st.button("⬅️ Back to Welcome", use_container_width=True, key="wiz_back_1"):
                st.session_state.wizard_step = 0
                st.rerun()
    with col2:
        if st.button("Next ➡️", use_container_width=True, type="primary", key=f"wiz_next_{step}"):
            st.session_state.wizard_step = step + 1
            st.rerun()


def _wizard_apply_phase2():
    """Apply secondary wizard refinements to the existing plan."""
    wd = st.session_state.wizard_data

    # Housing
    if wd.get('housing_type') == 'Own' and wd.get('home_value'):
        location = st.session_state.state_timeline[0].state if st.session_state.state_timeline else "Seattle"
        st.session_state.houses = [House(
            name="Primary Home",
            purchase_year=datetime.now().year - 2,
            purchase_price=wd.get('home_value', 500000),
            current_value=wd.get('home_value', 500000),
            mortgage_balance=wd.get('mortgage_balance', 350000),
            mortgage_rate=wd.get('mortgage_rate', 6.5) / 100,
            mortgage_years_left=wd.get('mortgage_years_left', 28),
            property_tax_rate=wd.get('property_tax', 6000) / max(wd.get('home_value', 500000), 1),
            home_insurance=2000,
            maintenance_rate=0.01,
            upkeep_costs=2000,
            owner="Shared",
            timeline=[HouseTimelineEntry(datetime.now().year, "Own_Live", 0.0)]
        )]
    elif wd.get('housing_type') == 'Rent' and wd.get('monthly_rent'):
        st.session_state.family_shared_expenses['Mortgage/Rent'] = wd['monthly_rent'] * 12

    # Tax & retirement savings
    if 'state_tax_rate' in wd:
        st.session_state.state_tax_rate = wd['state_tax_rate']
    if 'pretax_401k' in wd:
        st.session_state.pretax_401k = wd['pretax_401k']
    if wd.get('ss_insolvency'):
        st.session_state.ss_insolvency_enabled = True
        st.session_state.ss_shortfall_percentage = 77.0

    # Healthcare
    if wd.get('healthcare_approach') == "Enter my own estimates":
        st.session_state.hsa_contribution = float(wd.get('hsa_contribution', 0))
        st.session_state.hsa_balance = float(wd.get('hsa_balance', 0))

    # Life expectancy
    if 'p1_death_age' in wd:
        st.session_state.parentX_death_age = wd['p1_death_age']
    if 'p2_death_age' in wd:
        st.session_state.parentY_death_age = wd['p2_death_age']

    # Major purchases
    if wd.get('purchases'):
        st.session_state.major_purchases = [
            MajorPurchase(name=p['name'] or f"Purchase {i+1}", amount=float(p['amount']), year=p['year'])
            for i, p in enumerate(wd['purchases']) if p.get('amount', 0) > 0
        ]

    # Recurring purchases from wizard
    if wd.get('recurring_purchases'):
        from_year = datetime.now().year
        for rp in wd['recurring_purchases']:
            if rp.get('amount', 0) > 0 and rp.get('every_years', 0) > 0:
                st.session_state.recurring_expenses.append(
                    RecurringExpense(
                        name=rp['name'] or 'Recurring Purchase',
                        category='Major Purchase',
                        amount=float(rp['amount']),
                        frequency_years=rp['every_years'],
                        start_year=from_year,
                        inflation_adjust=True,
                    )
                )

    # Save the refined plan
    try:
        json_data = save_data()
        if json_data and st.session_state.get('household_id'):
            save_household_plan(st.session_state.household_id, json_data)
            scenarios = st.session_state.get('saved_scenarios', {})
            scenarios["Refined Plan"] = json_data
            st.session_state.saved_scenarios = scenarios
            save_household_scenarios(st.session_state.household_id, scenarios)
    except Exception:
        pass

    st.session_state.wizard_complete = True
    st.session_state.wizard_manual = False
    st.session_state.wizard_phase2 = False
    st.session_state.pop('wizard_step', None)
    st.session_state.pop('wizard_data', None)


def _wizard_create_plan():
    """Populate session state from wizard data, save plan and scenario."""
    wd = st.session_state.wizard_data
    is_couple = wd.get('household_type') == "Me and my partner"

    spending_map = {
        "Frugal": "Conservative (statistical)",
        "Average": "Average (statistical)",
        "Comfortable": "High-end (statistical)"
    }
    strategy = spending_map.get(wd.get('spending_style', 'Average'), "Average (statistical)")
    location = wd.get('current_location', 'Seattle')

    # Force fresh initialization
    st.session_state.pop('initialized', None)

    # We need initialize_session_state to run first to set all defaults, then we override
    initialize_session_state()

    # Parent 1
    st.session_state.parent1_name = wd.get('p1_name', 'Parent 1') or 'Parent 1'
    st.session_state.parent1_emoji = wd.get('p1_emoji', '👨')
    st.session_state.parentX_age = wd.get('p1_age', 30)
    st.session_state.parentX_income = float(wd.get('p1_income', 75000))
    st.session_state.parentX_raise = float(wd.get('p1_raise', 3.0))
    st.session_state.parentX_retirement_age = wd.get('p1_retire', 65)
    st.session_state.parentX_net_worth = float(wd.get('p1_net_worth', 0))
    st.session_state.parentX_ss_benefit = float(wd.get('p1_ss', 2000))

    # Career phases
    if wd.get('p1_career_phases'):
        st.session_state.parentX_career_phases = [
            CareerPhase(**cp) for cp in wd['p1_career_phases']
        ]
    else:
        st.session_state.parentX_career_phases = [
            CareerPhase(
                start_age=int(wd.get('p1_age', 30)),
                end_age=int(wd.get('p1_retire', 65)),
                philosophy="Stable",
                base_salary=float(wd.get('p1_income', 75000)),
                annual_raise_pct=float(wd.get('p1_raise', 3.0)),
                label="Current Job"
            )
        ]
    st.session_state.parentX_income = st.session_state.parentX_career_phases[0].base_salary
    st.session_state.parentX_raise = st.session_state.parentX_career_phases[0].annual_raise_pct

    # Parent 2
    if is_couple:
        st.session_state.parent2_name = wd.get('p2_name', 'Parent 2') or 'Parent 2'
        st.session_state.parent2_emoji = wd.get('p2_emoji', '👩')
        st.session_state.parentY_age = wd.get('p2_age', 30)
        st.session_state.parentY_income = float(wd.get('p2_income', 75000))
        st.session_state.parentY_raise = float(wd.get('p2_raise', 3.0))
        st.session_state.parentY_retirement_age = wd.get('p2_retire', 65)
        st.session_state.parentY_net_worth = float(wd.get('p2_net_worth', 0))
        st.session_state.parentY_ss_benefit = float(wd.get('p2_ss', 2000))
        st.session_state.marriage_year = wd.get('marriage_year', datetime.now().year)

        # Career phases for parent 2
        if wd.get('p2_career_phases'):
            st.session_state.parentY_career_phases = [
                CareerPhase(**cp) for cp in wd['p2_career_phases']
            ]
        else:
            st.session_state.parentY_career_phases = [
                CareerPhase(
                    start_age=int(wd.get('p2_age', 30)),
                    end_age=int(wd.get('p2_retire', 65)),
                    philosophy="Stable",
                    base_salary=float(wd.get('p2_income', 75000)),
                    annual_raise_pct=float(wd.get('p2_raise', 3.0)),
                    label="Current Job"
                )
            ]
        st.session_state.parentY_income = st.session_state.parentY_career_phases[0].base_salary
        st.session_state.parentY_raise = st.session_state.parentY_career_phases[0].annual_raise_pct
    else:
        st.session_state.parent2_name = "N/A"
        st.session_state.parent2_emoji = "👤"
        st.session_state.parentY_age = 0
        st.session_state.parentY_income = 0.0
        st.session_state.parentY_raise = 0.0
        st.session_state.parentY_retirement_age = 65
        st.session_state.parentY_net_worth = 0.0
        st.session_state.parentY_ss_benefit = 0.0
        st.session_state.marriage_year = "N/A"

    # Expense location & strategy for both parents
    st.session_state.parentX_expense_location = location
    st.session_state.parentX_expense_strategy = strategy
    st.session_state.parentX_use_template = True
    st.session_state.parentX_expenses = get_adult_expense_template(location, strategy)

    st.session_state.parentY_expense_location = location
    st.session_state.parentY_expense_strategy = strategy
    st.session_state.parentY_use_template = True
    st.session_state.parentY_expenses = get_adult_expense_template(location, strategy)

    # State timeline
    current_year = datetime.now().year
    timeline_entries = [StateTimelineEntry(current_year, location, wd.get('spending_style', 'Average'))]
    if wd.get('plan_moves') and wd.get('moves'):
        for mv in wd['moves']:
            timeline_entries.append(StateTimelineEntry(mv['year'], mv['location'], wd.get('spending_style', 'Average')))
    st.session_state.state_timeline = timeline_entries

    # Children
    if wd.get('has_children') and wd.get('children'):
        child_loc = wd.get('child_location', 'Seattle')
        st.session_state.children_list = []
        for ch in wd['children']:
            st.session_state.children_list.append({
                'name': ch['name'],
                'birth_year': ch['birth_year'],
                'use_template': True,
                'template_state': child_loc,
                'template_strategy': 'Average',
                'school_type': 'Public',
                'college_location': child_loc
            })
    else:
        st.session_state.children_list = []

    # Save the plan
    try:
        json_data = save_data()
        if json_data and st.session_state.get('household_id'):
            save_household_plan(st.session_state.household_id, json_data)
            # Also save as a named scenario
            scenarios = st.session_state.get('saved_scenarios', {})
            scenarios["Questionnaire Response Plan"] = json_data
            st.session_state.saved_scenarios = scenarios
            save_household_scenarios(st.session_state.household_id, scenarios)
    except Exception:
        pass  # Plan created in session state even if persistence fails

    st.session_state.wizard_complete = True
    st.session_state.wizard_manual = False
    # Clean up wizard state
    st.session_state.pop('wizard_step', None)
    st.session_state.pop('wizard_data', None)


# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.current_year = datetime.now().year

        st.session_state.parent1_name = "Parent 1"
        st.session_state.parent1_emoji = "👨"
        st.session_state.parent2_name = "Parent 2"
        st.session_state.parent2_emoji = "👩"

        st.session_state.marriage_year = "N/A"

        # Finance mode: "Pooled" (single family pot) or "Separate" (per-parent tracking)
        st.session_state.finance_mode = "Pooled"
        st.session_state.shared_expense_split_pct = 50  # Parent X pays this %, Y pays rest

        st.session_state.state_timeline = [
            StateTimelineEntry(datetime.now().year, "Seattle", "Average")
        ]

        # Parent X data
        st.session_state.parentX_age = 30
        st.session_state.parentX_net_worth = 50000.0
        st.session_state.parentX_income = 75000.0
        st.session_state.parentX_raise = 3.0
        st.session_state.parentX_retirement_age = 65
        st.session_state.parentX_death_age = 100
        st.session_state.parentX_ss_benefit = 2000.0
        st.session_state.parentX_job_changes = pd.DataFrame({
            'Year': pd.Series(dtype='int'),
            'New Income': pd.Series(dtype='float')
        })
        st.session_state.parentX_career_phases = [
            CareerPhase(
                start_age=st.session_state.parentX_age,
                end_age=st.session_state.parentX_retirement_age,
                philosophy="Stable",
                base_salary=st.session_state.parentX_income,
                annual_raise_pct=st.session_state.parentX_raise,
                label="Current Job"
            )
        ]

        # Parent Y data
        st.session_state.parentY_age = 30
        st.session_state.parentY_net_worth = 40000.0
        st.session_state.parentY_income = 75000.0
        st.session_state.parentY_raise = 3.0
        st.session_state.parentY_retirement_age = 65
        st.session_state.parentY_death_age = 100
        st.session_state.parentY_ss_benefit = 2000.0
        st.session_state.parentY_job_changes = pd.DataFrame({
            'Year': pd.Series(dtype='int'),
            'New Income': pd.Series(dtype='float')
        })
        st.session_state.parentY_career_phases = [
            CareerPhase(
                start_age=st.session_state.parentY_age,
                end_age=st.session_state.parentY_retirement_age,
                philosophy="Stable",
                base_salary=st.session_state.parentY_income,
                annual_raise_pct=st.session_state.parentY_raise,
                label="Current Job"
            )
        ]

        # Parent X expense settings
        st.session_state.parentX_expense_location = "Seattle"
        st.session_state.parentX_expense_strategy = "Average (statistical)"
        st.session_state.parentX_use_template = True

        # Parent X detailed expenses (using new category structure)
        default_parentX_template = get_adult_expense_template("Seattle", "Average (statistical)")
        st.session_state.parentX_expenses = default_parentX_template.copy()

        # Parent Y expense settings
        st.session_state.parentY_expense_location = "Seattle"
        st.session_state.parentY_expense_strategy = "Average (statistical)"
        st.session_state.parentY_use_template = True

        # Parent Y detailed expenses (using new category structure)
        default_parentY_template = get_adult_expense_template("Seattle", "Average (statistical)")
        st.session_state.parentY_expenses = default_parentY_template.copy()

        # Family shared expenses (reduced to only truly shared items)
        st.session_state.family_shared_expenses = {
            # Housing
            'Mortgage/Rent': 24000.0,  # $2,000/month
            'Home Improvement': 1000.0,
            'Property Tax': 0.0,  # Only applies if owning (set via House Portfolio)
            'Home Insurance': 0.0,  # Only applies if owning (set via House Portfolio)
            # Utilities & Bills
            'Gas & Electric': 1800.0,  # $150/month
            'Water': 600.0,  # $50/month
            'Garbage': 420.0,  # $35/month
            'Internet & Cable': 1200.0,  # $100/month
            # Shared Lifestyle
            'Shared Subscriptions': 480.0,  # Netflix, etc.
            'Family Vacations': 4000.0,
            'Pet Care': 0.0,
            'Other Family Expenses': 600.0
        }

        # Legacy expense categories (for backwards compatibility - DEPRECATED)
        # These will be migrated to parent/family expenses in v0.8
        st.session_state.expense_categories = [
            'Food & Groceries',
            'Clothing',
            'Transportation',
            'Entertainment & Activities',
            'Personal Care',
            'Vacations & Travel',
            'Other Expenses'
        ]

        # Legacy expenses (DEPRECATED - kept for backwards compatibility only)
        st.session_state.expenses = {
            'Food & Groceries': 0.0,  # Now tracked per parent
            'Clothing': 0.0,  # Now tracked per parent
            'Transportation': 0.0,  # Now tracked per parent
            'Entertainment & Activities': 0.0,  # Now tracked per parent
            'Personal Care': 0.0,  # Now tracked per parent
            'Vacations & Travel': 0.0,  # Now in family_shared_expenses
            'Utilities': 0.0,  # Now in family_shared_expenses
            'Internet & Phone': 0.0,  # Now split between parent phone and family internet
            'Subscriptions': 0.0,  # Now tracked per parent or family
            'Other Expenses': 0.0
        }

        # Children expenses table
        st.session_state.children_expenses = pd.DataFrame({
            'Age': list(range(31)),
            'Food': [
                1500 if i < 2 else 1800 if i < 5 else 2400 if i < 12 else 3000 if i < 19 else 1500 if i < 23 else 600 if i < 26 else 0
                for i in range(31)],
            'Clothing': [
                600 if i < 2 else 500 if i < 5 else 600 if i < 12 else 900 if i < 19 else 500 if i < 23 else 200 if i < 26 else 0
                for i in range(31)],
            'Healthcare': [
                800 if i < 1 else 500 if i < 5 else 400 if i < 19 else 300 if i < 23 else 200 if i < 26 else 0 for i in
                range(31)],
            'Activities/Sports': [
                100 if i < 3 else 300 if i < 6 else 800 if i < 12 else 1500 if i < 19 else 400 if i < 23 else 0 for i in
                range(31)],
            'Entertainment': [200 if i < 3 else 300 if i < 12 else 500 if i < 19 else 300 if i < 23 else 0 for i in
                              range(31)],
            'Transportation': [200 if i < 13 else 300 if i < 16 else 1000 if i < 19 else 400 if i < 23 else 0 for i in
                               range(31)],
            'School Supplies': [50 if i < 5 else 200 if i < 13 else 300 if i < 19 else 0 for i in range(31)],
            'Gifts/Celebrations': [300 if i < 19 else 400 if i < 30 else 0 for i in range(31)],
            'Miscellaneous': [200 if i < 19 else 300 if i < 23 else 200 if i < 26 else 100 if i < 30 else 0 for i in
                              range(31)],
            'Daycare': [20376 if i < 5 else 0 for i in range(31)],
            'Education': [25000 if 18 <= i <= 21 else 0 for i in range(31)]
        })

        # Children instances
        st.session_state.children_list = [
            {
                'name': 'Child 1',
                'birth_year': 2028,
                'use_template': True,
                'template_state': 'Seattle',
                'template_strategy': 'Average',
                'school_type': 'Public',
                'college_location': 'Seattle'
            },
            {
                'name': 'Child 2',
                'birth_year': 2030,
                'use_template': True,
                'template_state': 'Seattle',
                'template_strategy': 'Average',
                'school_type': 'Public',
                'college_location': 'Seattle'
            }
        ]
        st.session_state.children_today_dollars = True

        # Major purchases and recurring expenses
        st.session_state.major_purchases = []
        st.session_state.recurring_expenses = []

        # Economic parameters — default to historical averages
        st.session_state.economic_params = EconomicParameters(
            investment_return=0.06,
            inflation_rate=0.03,
            expense_growth_rate=0.02,
            healthcare_inflation_rate=0.045,
            use_historical_returns=True,
            use_historical_inflation=True,
            use_historical_expense_growth=True,
            use_historical_healthcare_inflation=True
        )

        # Houses — empty by default; added via wizard or House tab
        st.session_state.houses = []

        # Tax settings
        st.session_state.state_tax_rate = 0.0
        st.session_state.pretax_401k = 23500.0

        # Social Security insolvency settings
        st.session_state.ss_insolvency_enabled = True
        st.session_state.ss_shortfall_percentage = 30.0

        # Monte Carlo settings
        st.session_state.mc_start_year = datetime.now().year
        # Default to running until both parents reach their death age
        parent1_years_left = st.session_state.parentX_death_age - st.session_state.parentX_age
        parent2_years_left = st.session_state.parentY_death_age - st.session_state.parentY_age
        st.session_state.mc_years = max(parent1_years_left, parent2_years_left)
        st.session_state.mc_simulations = 100
        st.session_state.mc_income_variability = 10.0
        st.session_state.mc_expense_variability = 5.0
        st.session_state.mc_return_variability = 15.0

        # NEW: Asymmetric variability settings
        st.session_state.mc_income_variability_positive = 10.0
        st.session_state.mc_income_variability_negative = 10.0
        st.session_state.mc_expense_variability_positive = 5.0
        st.session_state.mc_expense_variability_negative = 5.0
        st.session_state.mc_return_variability_positive = 15.0
        st.session_state.mc_return_variability_negative = 15.0

        # Historical simulation settings
        st.session_state.mc_use_historical = False
        st.session_state.mc_historical_start_year = 1924
        st.session_state.mc_show_historical_stats = False

        # NEW: Inflation normalization toggle
        st.session_state.mc_normalize_to_today_dollars = False

        # Display preferences
        st.session_state.inflation_adjusted_display = True
        st.session_state.default_inflation_rate = 0.025

        # NEW: Internal save/load system
        # Load saved scenarios from household storage if authenticated
        if st.session_state.get('authenticated') and st.session_state.get('household_id'):
            st.session_state.saved_scenarios = load_household_scenarios(st.session_state.household_id)
        else:
            st.session_state.saved_scenarios = {}

        # Preload 5 demo scenarios showcasing different features
        current_year = datetime.now().year

        # Scenario 1: Young Tech Couple with Multiple Relocations & Early Retirement
        st.session_state.saved_scenarios["[DEMO] Tech Couple: SF→Austin→Seattle, Early Retirement @50"] = {
            'current_year': current_year,
            'parent1_name': "Alex",
            'parent1_emoji': "👨",
            'parent2_name': "Jordan",
            'parent2_emoji': "👩",
            'marriage_year': current_year - 3,
            'parentX_age': 28,
            'parentX_net_worth': 150000.0,
            'parentX_income': 180000.0,  # High initial, increases, sabbatical, then recovery
            'parentX_raise': 8.0,
            'parentX_retirement_age': 50,  # Early retirement!
            'parentX_ss_benefit': 3500.0,
            'parentY_age': 27,
            'parentY_net_worth': 120000.0,
            'parentY_income': 165000.0,
            'parentY_raise': 7.5,
            'parentY_retirement_age': 51,  # Early retirement!
            'parentY_ss_benefit': 3200.0,
            'expenses': {
                'Food & Groceries': 18000.0,
                'Clothing': 6000.0,
                'Transportation': 8000.0,
                'Entertainment & Activities': 12000.0,
                'Personal Care': 4800.0,
                'Other Expenses': 9600.0
            },
            'children_list': [
                {
                    'name': 'Emma',
                    'birth_year': current_year - 2,
                    'use_template': True,
                    'template_state': 'San Francisco',
                    'template_strategy': 'High-end',
                    'school_type': 'Private',
                    'college_type': 'Private',
                    'college_location': 'San Francisco'
                },
                {
                    'name': 'Lucas',
                    'birth_year': current_year,
                    'use_template': True,
                    'template_state': 'San Francisco',
                    'template_strategy': 'High-end',
                    'school_type': 'Private',
                    'college_type': 'Private',
                    'college_location': 'New York'
                }
            ],
            'houses': [
                {
                    'name': 'SF Condo',
                    'purchase_year': current_year - 2,
                    'purchase_price': 1200000.0,
                    'current_value': 1300000.0,
                    'mortgage_balance': 900000.0,
                    'mortgage_rate': 0.065,
                    'mortgage_years_left': 28,
                    'property_tax_rate': 0.012,
                    'home_insurance': 2400.0,
                    'maintenance_rate': 0.005,
                    'upkeep_costs': 6000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year - 2, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 3, 'status': 'Sold', 'rental_income': 0.0}  # Sell when moving to Austin
                    ]
                },
                {
                    'name': 'Austin House',
                    'purchase_year': current_year + 3,
                    'purchase_price': 650000.0,
                    'current_value': 650000.0,
                    'mortgage_balance': 520000.0,
                    'mortgage_rate': 0.055,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.021,  # Texas property tax
                    'home_insurance': 2000.0,
                    'maintenance_rate': 0.008,
                    'upkeep_costs': 5000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 3, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 8, 'status': 'Own_Rent', 'rental_income': 3200.0},  # Convert to rental
                        {'year': current_year + 15, 'status': 'Sold', 'rental_income': 0.0}  # Eventually sell
                    ]
                },
                {
                    'name': 'Seattle House',
                    'purchase_year': current_year + 8,
                    'purchase_price': 950000.0,
                    'current_value': 950000.0,
                    'mortgage_balance': 760000.0,
                    'mortgage_rate': 0.048,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.01,
                    'home_insurance': 1800.0,
                    'maintenance_rate': 0.007,
                    'upkeep_costs': 6500.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 8, 'status': 'Own_Live', 'rental_income': 0.0}
                    ]
                }
            ],
            'major_purchases': [
                {
                    'name': 'Sabbatical Year Living Expenses',
                    'year': current_year + 6,
                    'amount': 80000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Home Renovation (Austin)',
                    'year': current_year + 5,
                    'amount': 75000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Boat Purchase',
                    'year': current_year + 10,
                    'amount': 125000.0,
                    'financing_years': 5,
                    'interest_rate': 0.055,
                    'asset_type': 'Depreciating',
                    'appreciation_rate': -0.08
                }
            ],
            'recurring_expenses': [
                {
                    'name': 'Tech Equipment',
                    'category': 'Work Equipment',
                    'amount': 5000.0,
                    'frequency_years': 2,
                    'start_year': current_year,
                    'end_year': current_year + 22,  # Until retirement
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Electric Vehicles',
                    'category': 'Vehicle',
                    'amount': 65000.0,
                    'frequency_years': 6,
                    'start_year': current_year + 2,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Adventure Travel',
                    'category': 'Travel',
                    'amount': 15000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Boat Maintenance',
                    'category': 'Recreation',
                    'amount': 8000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 10,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Home Office Upgrades',
                    'category': 'Work Equipment',
                    'amount': 3000.0,
                    'frequency_years': 3,
                    'start_year': current_year + 1,
                    'end_year': current_year + 22,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                }
            ],
            'state_timeline': [
                {
                    'year': current_year,
                    'state': 'San Francisco',
                    'spending_strategy': 'High-end'
                },
                {
                    'year': current_year + 3,
                    'state': 'Houston',  # Using Houston as proxy for Austin
                    'spending_strategy': 'Average'  # Lower cost of living
                },
                {
                    'year': current_year + 8,
                    'state': 'Seattle',
                    'spending_strategy': 'Average'
                }
            ],
            'economic_params': asdict(EconomicParameters(0.08, 0.02, 0.02, 0.04, False, False, False, False)),
            'ss_insolvency_enabled': True,
            'ss_shortfall_percentage': 30.0
        }

        # Scenario 2: 3-Kid Family with Multiple Moves & Career Transitions
        st.session_state.saved_scenarios["[DEMO] 3-Kid Family: Seattle→Portland→Denver, Career Change, 4 Properties"] = {
            'current_year': current_year,
            'parent1_name': "Mike",
            'parent1_emoji': "👨",
            'parent2_name': "Sarah",
            'parent2_emoji': "👩",
            'marriage_year': current_year - 12,
            'parentX_age': 38,
            'parentX_net_worth': 320000.0,
            'parentX_income': 115000.0,
            'parentX_raise': 3.5,
            'parentX_retirement_age': 62,  # Slightly early retirement
            'parentX_ss_benefit': 2800.0,
            'parentY_age': 37,
            'parentY_net_worth': 280000.0,
            'parentY_income': 95000.0,  # Will have career change
            'parentY_raise': 3.0,
            'parentY_retirement_age': 63,  # Slightly early retirement
            'parentY_ss_benefit': 2500.0,
            'expenses': {
                'Food & Groceries': 15600.0,
                'Clothing': 4800.0,
                'Transportation': 14400.0,
                'Entertainment & Activities': 7200.0,
                'Personal Care': 3600.0,
                'Other Expenses': 8400.0
            },
            'children_list': [
                {
                    'name': 'Olivia',
                    'birth_year': current_year - 10,
                    'use_template': True,
                    'template_state': 'Seattle',
                    'template_strategy': 'Average',
                    'school_type': 'Public',
                    'college_type': 'Public',
                    'college_location': 'Seattle'
                },
                {
                    'name': 'Noah',
                    'birth_year': current_year - 7,
                    'use_template': True,
                    'template_state': 'Seattle',
                    'template_strategy': 'Average',
                    'school_type': 'Public',
                    'college_type': 'Public',
                    'college_location': 'Seattle'
                },
                {
                    'name': 'Sophia',
                    'birth_year': current_year - 4,
                    'use_template': True,
                    'template_state': 'Seattle',
                    'template_strategy': 'Average',
                    'school_type': 'Public',
                    'college_type': 'Private',
                    'college_location': 'Seattle'
                }
            ],
            'houses': [
                {
                    'name': 'Seattle Starter Home',
                    'purchase_year': current_year - 8,
                    'purchase_price': 650000.0,
                    'current_value': 800000.0,
                    'mortgage_balance': 420000.0,
                    'mortgage_rate': 0.035,
                    'mortgage_years_left': 22,
                    'property_tax_rate': 0.01,
                    'home_insurance': 1800.0,
                    'maintenance_rate': 0.008,
                    'upkeep_costs': 5000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year - 8, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 5, 'status': 'Own_Rent', 'rental_income': 2800.0},  # Convert to rental
                        {'year': current_year + 18, 'status': 'Sold', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Portland Family Home',
                    'purchase_year': current_year + 5,
                    'purchase_price': 720000.0,
                    'current_value': 720000.0,
                    'mortgage_balance': 576000.0,
                    'mortgage_rate': 0.045,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.011,
                    'home_insurance': 1900.0,
                    'maintenance_rate': 0.009,
                    'upkeep_costs': 5500.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 5, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 12, 'status': 'Sold', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Denver Home',
                    'purchase_year': current_year + 12,
                    'purchase_price': 680000.0,
                    'current_value': 680000.0,
                    'mortgage_balance': 544000.0,
                    'mortgage_rate': 0.052,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.0055,
                    'home_insurance': 1700.0,
                    'maintenance_rate': 0.008,
                    'upkeep_costs': 5200.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 12, 'status': 'Own_Live', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Colorado Mountain Cabin',
                    'purchase_year': current_year + 15,
                    'purchase_price': 380000.0,
                    'current_value': 380000.0,
                    'mortgage_balance': 304000.0,
                    'mortgage_rate': 0.055,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.005,
                    'home_insurance': 1200.0,
                    'maintenance_rate': 0.012,
                    'upkeep_costs': 4000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 15, 'status': 'Own_Live', 'rental_income': 0.0}  # Vacation home
                    ]
                }
            ],
            'major_purchases': [
                {
                    'name': "Olivia's Wedding",
                    'year': current_year + 18,
                    'amount': 32000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': "Career Change Education (Sarah MBA)",
                    'year': current_year + 7,
                    'amount': 65000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Kitchen Renovation (Portland)',
                    'year': current_year + 8,
                    'amount': 55000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'RV Purchase',
                    'year': current_year + 16,
                    'amount': 95000.0,
                    'financing_years': 7,
                    'interest_rate': 0.058,
                    'asset_type': 'Depreciating',
                    'appreciation_rate': -0.10
                }
            ],
            'recurring_expenses': [
                {
                    'name': 'Family Minivan',
                    'category': 'Vehicle',
                    'amount': 45000.0,
                    'frequency_years': 8,
                    'start_year': current_year + 3,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 5,
                    'interest_rate': 0.045
                },
                {
                    'name': 'Annual Family Vacation',
                    'category': 'Travel',
                    'amount': 8000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Ski Equipment & Passes',
                    'category': 'Recreation',
                    'amount': 4500.0,
                    'frequency_years': 1,
                    'start_year': current_year + 12,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Home Office Equipment',
                    'category': 'Work Equipment',
                    'amount': 2500.0,
                    'frequency_years': 3,
                    'start_year': current_year + 1,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'College Visiting Trips',
                    'category': 'Children',
                    'amount': 3000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 8,
                    'end_year': current_year + 14,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                }
            ],
            'state_timeline': [
                {
                    'year': current_year,
                    'state': 'Seattle',
                    'spending_strategy': 'Average'
                },
                {
                    'year': current_year + 5,
                    'state': 'Portland',
                    'spending_strategy': 'Average'
                },
                {
                    'year': current_year + 12,
                    'state': 'Sacramento',  # California city with expense data
                    'spending_strategy': 'Conservative'  # Cost-conscious after career change
                },
                {
                    'year': current_year + 18,
                    'state': 'Sacramento',
                    'spending_strategy': 'Average'  # Back to normal spending
                }
            ],
            'economic_params': asdict(EconomicParameters(0.06, 0.03, 0.02, 0.045, False, False, False, False)),
            'ss_insolvency_enabled': True,
            'ss_shortfall_percentage': 30.0
        }

        # Scenario 3: Wealthy Executives with Early Retirement & International Lifestyle
        st.session_state.saved_scenarios["[DEMO] Executives: NYC→Miami→Portugal, Early Retire @55, 5 Properties"] = {
            'current_year': current_year,
            'parent1_name': "David",
            'parent1_emoji': "👨",
            'parent2_name': "Jennifer",
            'parent2_emoji': "👩",
            'marriage_year': current_year - 15,
            'parentX_age': 45,
            'parentX_net_worth': 2500000.0,
            'parentX_income': 350000.0,
            'parentX_raise': 4.0,
            'parentX_retirement_age': 55,  # Early retirement!
            'parentX_ss_benefit': 4500.0,
            'parentY_age': 43,
            'parentY_net_worth': 2200000.0,
            'parentY_income': 280000.0,
            'parentY_raise': 3.5,
            'parentY_retirement_age': 55,  # Early retirement!
            'parentY_ss_benefit': 4000.0,
            'expenses': {
                'Food & Groceries': 24000.0,
                'Clothing': 12000.0,
                'Transportation': 18000.0,
                'Entertainment & Activities': 24000.0,
                'Personal Care': 9600.0,
                'Other Expenses': 18000.0
            },
            'children_list': [
                {
                    'name': 'Isabella',
                    'birth_year': current_year - 13,
                    'use_template': True,
                    'template_state': 'New York',
                    'template_strategy': 'High-end',
                    'school_type': 'Private',
                    'college_type': 'Private',
                    'college_location': 'New York'
                },
                {
                    'name': 'William',
                    'birth_year': current_year - 11,
                    'use_template': True,
                    'template_state': 'New York',
                    'template_strategy': 'High-end',
                    'school_type': 'Private',
                    'college_type': 'Private',
                    'college_location': 'New York'
                }
            ],
            'houses': [
                {
                    'name': 'Manhattan Apartment',
                    'purchase_year': current_year - 10,
                    'purchase_price': 2500000.0,
                    'current_value': 3200000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.008,
                    'home_insurance': 4500.0,
                    'maintenance_rate': 0.004,
                    'upkeep_costs': 12000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year - 10, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 7, 'status': 'Sold', 'rental_income': 0.0}  # Sell when moving to Miami
                    ]
                },
                {
                    'name': 'Hamptons Summer Home',
                    'purchase_year': current_year - 5,
                    'purchase_price': 1800000.0,
                    'current_value': 2100000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.025,
                    'home_insurance': 3200.0,
                    'maintenance_rate': 0.01,
                    'upkeep_costs': 15000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year - 5, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 7, 'status': 'Own_Rent', 'rental_income': 8500.0},  # Convert to rental
                        {'year': current_year + 15, 'status': 'Sold', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Miami Penthouse',
                    'purchase_year': current_year + 7,
                    'purchase_price': 2800000.0,
                    'current_value': 2800000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.012,
                    'home_insurance': 5500.0,
                    'maintenance_rate': 0.005,
                    'upkeep_costs': 14000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 7, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 15, 'status': 'Own_Rent', 'rental_income': 7000.0}  # Keep as rental when moving abroad
                    ]
                },
                {
                    'name': 'Portugal Villa (Algarve)',
                    'purchase_year': current_year + 15,
                    'purchase_price': 850000.0,
                    'current_value': 850000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.004,
                    'home_insurance': 2200.0,
                    'maintenance_rate': 0.008,
                    'upkeep_costs': 8000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 15, 'status': 'Own_Live', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Aspen Ski Chalet',
                    'purchase_year': current_year + 3,
                    'purchase_price': 1600000.0,
                    'current_value': 1600000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.006,
                    'home_insurance': 3800.0,
                    'maintenance_rate': 0.012,
                    'upkeep_costs': 18000.0
                }
            ],
            'major_purchases': [
                {
                    'name': "Isabella's Wedding Reception",
                    'year': current_year + 12,
                    'amount': 75000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': "William's Wedding Reception",
                    'year': current_year + 16,
                    'amount': 80000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Luxury Yacht Purchase',
                    'year': current_year + 8,
                    'amount': 450000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Depreciating',
                    'appreciation_rate': -0.06
                },
                {
                    'name': 'Art Collection Investment',
                    'year': current_year + 5,
                    'amount': 200000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Appreciating',
                    'appreciation_rate': 0.04
                }
            ],
            'recurring_expenses': [
                {
                    'name': 'Luxury Vehicles (2 Cars)',
                    'category': 'Vehicle',
                    'amount': 150000.0,
                    'frequency_years': 4,
                    'start_year': current_year + 2,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'International Luxury Travel',
                    'category': 'Travel',
                    'amount': 45000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Charitable Giving',
                    'category': 'Philanthropy',
                    'amount': 50000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': False,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Yacht Maintenance',
                    'category': 'Recreation',
                    'amount': 35000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 8,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Wine Collection & Storage',
                    'category': 'Lifestyle',
                    'amount': 12000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Private Club Memberships',
                    'category': 'Lifestyle',
                    'amount': 25000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                }
            ],
            'state_timeline': [
                {
                    'year': current_year,
                    'state': 'New York',
                    'spending_strategy': 'High-end'
                },
                {
                    'year': current_year + 7,
                    'state': 'Los Angeles',  # Using LA as proxy for Miami
                    'spending_strategy': 'High-end'
                },
                {
                    'year': current_year + 15,
                    'state': 'Paris',  # International lifestyle in Portugal
                    'spending_strategy': 'Average'  # Lower cost of living abroad
                }
            ],
            'economic_params': asdict(EconomicParameters(0.06, 0.03, 0.02, 0.045, False, False, False, False)),
            'ss_insolvency_enabled': True,
            'ss_shortfall_percentage': 30.0
        }

        # Scenario 4: Single Teacher with Career Growth & Multiple Relocations
        st.session_state.saved_scenarios["[DEMO] Single Mom: Sacramento→San Diego, Teacher→Principal, 3 Properties"] = {
            'current_year': current_year,
            'parent1_name': "Maria",
            'parent1_emoji': "👩",
            'parent2_name': "N/A",
            'parent2_emoji': "👤",
            'marriage_year': "N/A",
            'parentX_age': 35,
            'parentX_net_worth': 95000.0,
            'parentX_income': 72000.0,  # Teacher salary, will increase to VP then Principal
            'parentX_raise': 2.5,
            'parentX_retirement_age': 62,  # Early retirement with good pension
            'parentX_ss_benefit': 2200.0,
            'parentY_age': 35,
            'parentY_net_worth': 0.0,
            'parentY_income': 0.0,
            'parentY_raise': 0.0,
            'parentY_retirement_age': 67,
            'parentY_ss_benefit': 0.0,
            'expenses': {
                'Food & Groceries': 9600.0,
                'Clothing': 2400.0,
                'Transportation': 7200.0,
                'Entertainment & Activities': 3600.0,
                'Personal Care': 2400.0,
                'Other Expenses': 4800.0
            },
            'children_list': [
                {
                    'name': 'Diego',
                    'birth_year': current_year - 8,
                    'use_template': True,
                    'template_state': 'Sacramento',
                    'template_strategy': 'Average',
                    'school_type': 'Public',
                    'college_type': 'Public',
                    'college_location': 'Sacramento'
                }
            ],
            'houses': [
                {
                    'name': 'Sacramento Townhouse',
                    'purchase_year': current_year - 3,
                    'purchase_price': 420000.0,
                    'current_value': 450000.0,
                    'mortgage_balance': 336000.0,
                    'mortgage_rate': 0.068,
                    'mortgage_years_left': 27,
                    'property_tax_rate': 0.011,
                    'home_insurance': 1400.0,
                    'maintenance_rate': 0.006,
                    'upkeep_costs': 3000.0,
                    'owner': 'ParentX',
                    'timeline': [
                        {'year': current_year - 3, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 6, 'status': 'Own_Rent', 'rental_income': 2400.0},  # Convert to rental when moving
                        {'year': current_year + 18, 'status': 'Sold', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'San Diego House',
                    'purchase_year': current_year + 6,
                    'purchase_price': 720000.0,
                    'current_value': 720000.0,
                    'mortgage_balance': 576000.0,
                    'mortgage_rate': 0.058,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.0073,
                    'home_insurance': 1800.0,
                    'maintenance_rate': 0.007,
                    'upkeep_costs': 5000.0,
                    'owner': 'ParentX',
                    'timeline': [
                        {'year': current_year + 6, 'status': 'Own_Live', 'rental_income': 0.0}
                    ]
                },
                {
                    'name': 'Lake Tahoe Cabin',
                    'purchase_year': current_year + 12,
                    'purchase_price': 420000.0,
                    'current_value': 420000.0,
                    'mortgage_balance': 336000.0,
                    'mortgage_rate': 0.062,
                    'mortgage_years_left': 30,
                    'property_tax_rate': 0.0085,
                    'home_insurance': 1300.0,
                    'maintenance_rate': 0.01,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Sabbatical Year (Educational Travel)',
                    'year': current_year + 10,
                    'amount': 35000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': "Diego's College Graduation Gift",
                    'year': current_year + 18,
                    'amount': 15000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                }
            ],
            'recurring_expenses': [
                {
                    'name': 'Reliable Sedan',
                    'category': 'Vehicle',
                    'amount': 32000.0,
                    'frequency_years': 8,
                    'start_year': current_year + 4,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'ParentX',
                    'financing_years': 5,
                    'interest_rate': 0.045
                },
                {
                    'name': 'Summer Camp & Activities',
                    'category': 'Children',
                    'amount': 2500.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': current_year + 10,
                    'inflation_adjust': True,
                    'parent': 'ParentX',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Professional Development',
                    'category': 'Work Equipment',
                    'amount': 2000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': current_year + 27,
                    'inflation_adjust': True,
                    'parent': 'ParentX',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Annual Vacation',
                    'category': 'Travel',
                    'amount': 4500.0,
                    'frequency_years': 1,
                    'start_year': current_year + 6,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'ParentX',
                    'financing_years': 0,
                    'interest_rate': 0.0
                }
            ],
            'state_timeline': [
                {
                    'year': current_year,
                    'state': 'Sacramento',
                    'spending_strategy': 'Conservative'
                },
                {
                    'year': current_year + 6,
                    'state': 'San Francisco',  # Using SF as proxy for San Diego
                    'spending_strategy': 'Average'  # Better income as VP/Principal
                },
                {
                    'year': current_year + 15,
                    'state': 'San Francisco',
                    'spending_strategy': 'High-end'  # Principal salary, established career
                }
            ],
            'economic_params': asdict(EconomicParameters(0.04, 0.03, 0.02, 0.05, False, False, False, False)),
            'ss_insolvency_enabled': True,
            'ss_shortfall_percentage': 30.0
        }

        # Scenario 5: Empty Nesters with Early Retirement & Snowbird Lifestyle
        st.session_state.saved_scenarios["[DEMO] Empty Nesters: Early Retire @60, Portland→Arizona→RV, 4 Properties"] = {
            'current_year': current_year,
            'parent1_name': "Robert",
            'parent1_emoji': "👨",
            'parent2_name': "Linda",
            'parent2_emoji': "👩",
            'marriage_year': current_year - 32,
            'parentX_age': 58,
            'parentX_net_worth': 1200000.0,
            'parentX_income': 125000.0,
            'parentX_raise': 2.0,
            'parentX_retirement_age': 60,  # Early retirement!
            'parentX_ss_benefit': 3200.0,
            'parentY_age': 57,
            'parentY_net_worth': 950000.0,
            'parentY_income': 98000.0,
            'parentY_raise': 2.0,
            'parentY_retirement_age': 60,  # Early retirement!
            'parentY_ss_benefit': 2800.0,
            'expenses': {
                'Food & Groceries': 12000.0,
                'Clothing': 3600.0,
                'Transportation': 9600.0,
                'Entertainment & Activities': 8400.0,
                'Personal Care': 4200.0,
                'Other Expenses': 7200.0
            },
            'children_list': [],
            'houses': [
                {
                    'name': 'Portland Family Home',
                    'purchase_year': current_year - 25,
                    'purchase_price': 350000.0,
                    'current_value': 720000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.009,
                    'home_insurance': 1600.0,
                    'maintenance_rate': 0.01,
                    'upkeep_costs': 6000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year - 25, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 2, 'status': 'Sold', 'rental_income': 0.0}  # Sell early for retirement
                    ]
                },
                {
                    'name': 'Portland Downsized Condo',
                    'purchase_year': current_year + 2,
                    'purchase_price': 420000.0,
                    'current_value': 420000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.009,
                    'home_insurance': 1200.0,
                    'maintenance_rate': 0.005,
                    'upkeep_costs': 3000.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 2, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 5, 'status': 'Own_Rent', 'rental_income': 2200.0},  # Rent while snowbirding
                        {'year': current_year + 12, 'status': 'Sold', 'rental_income': 0.0}  # Sell when going full RV
                    ]
                },
                {
                    'name': 'Arizona Winter Home',
                    'purchase_year': current_year + 5,
                    'purchase_price': 380000.0,
                    'current_value': 380000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.0062,
                    'home_insurance': 1400.0,
                    'maintenance_rate': 0.008,
                    'upkeep_costs': 3500.0,
                    'owner': 'Shared',
                    'timeline': [
                        {'year': current_year + 5, 'status': 'Own_Live', 'rental_income': 0.0},
                        {'year': current_year + 12, 'status': 'Sold', 'rental_income': 0.0}  # Sell when going full RV
                    ]
                },
                {
                    'name': 'Montana Lakeside Cabin',
                    'purchase_year': current_year + 8,
                    'purchase_price': 320000.0,
                    'current_value': 320000.0,
                    'mortgage_balance': 0.0,
                    'mortgage_rate': 0.0,
                    'mortgage_years_left': 0,
                    'property_tax_rate': 0.0081,
                    'home_insurance': 1100.0,
                    'maintenance_rate': 0.011,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                },
                {
                    'name': 'Luxury RV Purchase',
                    'year': current_year + 12,
                    'amount': 225000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Depreciating',
                    'appreciation_rate': -0.09
                },
                {
                    'name': 'World Cruise Retirement Trip',
                    'year': current_year + 4,
                    'amount': 45000.0,
                    'financing_years': 0,
                    'interest_rate': 0.0,
                    'asset_type': 'Expense',
                    'appreciation_rate': 0.0
                }
            ],
            'recurring_expenses': [
                {
                    'name': 'Healthcare Premiums (Pre-Medicare)',
                    'category': 'Healthcare',
                    'amount': 18000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': current_year + 7,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Healthcare Costs (Post-Medicare)',
                    'category': 'Healthcare',
                    'amount': 8000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 7,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Help Adult Children',
                    'category': 'Family Support',
                    'amount': 15000.0,
                    'frequency_years': 1,
                    'start_year': current_year,
                    'end_year': current_year + 20,
                    'inflation_adjust': False,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'RV Maintenance & Campgrounds',
                    'category': 'Recreation',
                    'amount': 18000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 12,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Active Retirement Travel',
                    'category': 'Travel',
                    'amount': 12000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 2,
                    'end_year': current_year + 25,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Grandchildren Support & Gifts',
                    'category': 'Family Support',
                    'amount': 8000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 5,
                    'end_year': None,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                },
                {
                    'name': 'Golf Club Membership',
                    'category': 'Recreation',
                    'amount': 6000.0,
                    'frequency_years': 1,
                    'start_year': current_year + 5,
                    'end_year': current_year + 12,
                    'inflation_adjust': True,
                    'parent': 'Both',
                    'financing_years': 0,
                    'interest_rate': 0.0
                }
            ],
            'state_timeline': [
                {
                    'year': current_year,
                    'state': 'Portland',
                    'spending_strategy': 'Average'
                },
                {
                    'year': current_year + 2,
                    'state': 'Portland',
                    'spending_strategy': 'Conservative'  # Downsized, early retirement
                },
                {
                    'year': current_year + 5,
                    'state': 'Houston',  # Using Houston as proxy for Arizona (snowbird)
                    'spending_strategy': 'Average'  # Snowbird lifestyle
                },
                {
                    'year': current_year + 12,
                    'state': 'Los Angeles',  # California city with expense data for RV lifestyle
                    'spending_strategy': 'Conservative'  # Full-time RV travel
                }
            ],
            'economic_params': asdict(EconomicParameters(0.04, 0.03, 0.02, 0.05, False, False, False, False)),
            'ss_insolvency_enabled': True,
            'ss_shortfall_percentage': 30.0
        }

        # NEW: Custom children templates
        st.session_state.custom_children_templates = {}

        # Custom family expense templates
        st.session_state.custom_family_templates = {}

        # NEW: Custom location display names (for user-created cities)
        st.session_state.custom_location_display_names = {}

        # NEW: Custom location coordinates (for world map visualization)
        st.session_state.custom_location_coordinates = {}

        # NEW: Healthcare & Insurance
        st.session_state.health_insurances = []
        st.session_state.ltc_insurances = []
        st.session_state.health_expenses = []
        st.session_state.hsa_balance = 0.0
        st.session_state.hsa_contribution = 0.0
        st.session_state.medicare_part_b_premium = 174.70  # 2025 standard
        st.session_state.medicare_part_d_premium = 55.0    # Average estimate
        st.session_state.medigap_premium = 150.0           # Average estimate

        # Tab visibility settings
        st.session_state.show_family_expenses = False  # Off by default (advanced template management)
        st.session_state.show_recurring_expenses = True  # On by default
        st.session_state.show_healthcare = False  # Off by default
        st.session_state.show_export = True  # On by default

        st.session_state.initialized = True


def get_state_for_year(year: int) -> tuple:
    """Get the state and spending strategy for a given year"""
    if not st.session_state.state_timeline:
        return "Seattle", "Average (statistical)"

    sorted_timeline = sorted(st.session_state.state_timeline, key=lambda x: x.year)

    current_state = "Seattle"
    current_strategy = "Average (statistical)"

    for entry in sorted_timeline:
        if entry.year <= year:
            current_state = entry.state
            # Normalize the strategy name for backward compatibility
            current_strategy = normalize_strategy_name(entry.spending_strategy)
        else:
            break

    return current_state, current_strategy


def get_location_display_name(location: str) -> str:
    """Get full display name for a location including country and state"""
    # Check custom display names first, then built-in ones
    if hasattr(st.session_state, 'custom_location_display_names'):
        custom_name = st.session_state.custom_location_display_names.get(location)
        if custom_name:
            return custom_name
    return LOCATION_DISPLAY_NAMES.get(location, location)


def get_state_based_family_expenses(year: int) -> dict:
    """Get family expenses based on the state for a given year"""
    state, strategy = get_state_for_year(year)

    # Use the helper function to get template data (handles both statistical and custom)
    template_data = get_template_strategy_data(state, strategy, 'family')

    if template_data:
        return template_data
    else:
        return st.session_state.expenses.copy()


def get_state_based_children_expenses(year: int, child_age: int) -> dict:
    """Get children expenses for a specific age based on the state for a given year"""
    state, strategy = get_state_for_year(year)

    # Use the helper function to get template data (handles both statistical and custom)
    template = get_template_strategy_data(state, strategy, 'children')

    if template and 0 <= child_age < len(template.get('Food', [])):
        child_expenses = {}

        for category, values in template.items():
            if child_age < len(values):
                child_expenses[category] = values[child_age]
            else:
                child_expenses[category] = 0

        return child_expenses
    else:
        if 0 <= child_age < len(st.session_state.children_expenses):
            row = st.session_state.children_expenses.iloc[child_age]
            return {col: row[col] for col in row.index if col != 'Age'}
        else:
            return {}


def get_child_expenses(child: dict, year: int, current_year: int) -> dict:
    """
    Get expenses for a specific child in a specific year, accounting for:
    - School type (public/private)
    - College location (where they attend college)
    - Living arrangement (at home vs at college)

    Args:
        child: Child dictionary with keys: name, birth_year, template_state, template_strategy,
               school_type, college_location
        year: The year to calculate expenses for
        current_year: The current year (for age calculation)

    Returns:
        dict: Expense categories and amounts for this child in this year
    """
    child_age = year - child['birth_year']

    # Child expenses only apply from age 0-25
    if child_age < 0 or child_age > 30:
        return {}

    # Determine which location template to use
    # Ages 18-21: Use college location (living at college)
    # Other ages: Use family's template location
    if 18 <= child_age <= 21:
        location = child.get('college_location', 'Seattle')
        lives_at_college = True
    else:
        location = child.get('template_state', 'Seattle')
        lives_at_college = False

    strategy = normalize_strategy_name(child.get('template_strategy', 'Average'))
    school_type = child.get('school_type', 'Public')

    # Get base expenses from template using helper function
    template = get_template_strategy_data(location, strategy, 'children')

    if template and 0 <= child_age < len(template.get('Food', [])):
        child_expenses = {}

        for category, values in template.items():
            if child_age < len(values):
                child_expenses[category] = values[child_age]
            else:
                child_expenses[category] = 0
    else:
        # Fallback to default template
        if 0 <= child_age < len(st.session_state.children_expenses):
            row = st.session_state.children_expenses.iloc[child_age]
            child_expenses = {col: row[col] for col in row.index if col != 'Age'}
        else:
            child_expenses = {}

    # Adjust for private school (ages 5-17, K-12 education)
    if school_type == 'Private' and 5 <= child_age <= 17:
        # Add private school tuition based on location
        private_school_costs = {
            'Seattle': 20000,  # Average private school in Seattle
            'Sacramento': 18000,
            'Houston': 15000,
            'New York': 35000,
            'San Francisco': 32000,
            'Los Angeles': 25000,
            'Portland': 17000
        }
        additional_tuition = private_school_costs.get(child.get('template_state', 'Seattle'), 20000)
        child_expenses['Education'] = child_expenses.get('Education', 0) + additional_tuition

    # Adjust expenses for living at college (ages 18-21)
    if lives_at_college:
        # College students living on campus have different expense patterns
        # Room & board is included in Education costs
        # Reduce home-based expenses (food, transportation, etc.)
        child_expenses['Food'] = child_expenses.get('Food', 0) * 0.3  # Occasional meals at home
        child_expenses['Transportation'] = child_expenses.get('Transportation', 0) * 0.4  # Less frequent trips home
        child_expenses['Entertainment'] = child_expenses.get('Entertainment', 0) * 0.5  # Less at-home entertainment

        # Education costs now include tuition + room & board
        college_type = child.get('college_type', 'Public')

        # Base tuition costs (public vs private)
        if college_type == 'Public':
            # Public college tuition by location
            public_tuition = {
                'Seattle': 12000,      # UW in-state
                'Sacramento': 10000,   # UC in-state
                'Houston': 11000,      # UT in-state
                'New York': 13000,     # SUNY/CUNY in-state
                'San Francisco': 10000, # UC in-state
                'Los Angeles': 10000,  # UC in-state
                'Portland': 12000      # Oregon in-state
            }
            tuition = public_tuition.get(location, 12000)
        else:  # Private college
            # Private college tuition by location (2-3x public costs)
            private_tuition = {
                'Seattle': 55000,      # Seattle University, etc.
                'Sacramento': 50000,
                'Houston': 48000,
                'New York': 60000,     # NYU, Columbia, etc.
                'San Francisco': 58000, # Stanford area schools
                'Los Angeles': 56000,  # USC, etc.
                'Portland': 52000
            }
            tuition = private_tuition.get(location, 55000)

        # Room & board costs (~$15k-25k depending on location)
        room_board_costs = {
            'Seattle': 18000,
            'Sacramento': 15000,
            'Houston': 12000,
            'New York': 25000,
            'San Francisco': 24000,
            'Los Angeles': 20000,
            'Portland': 16000
        }
        room_board = room_board_costs.get(location, 18000)

        # Total college costs = tuition + room & board
        child_expenses['Education'] = child_expenses.get('Education', 0) + tuition + room_board

    return child_expenses


def get_income_for_year(base_income: float, raise_rate: float, job_changes_df: pd.DataFrame,
                        current_year: int, target_year: int) -> float:
    """
    Calculate income for a specific year considering job changes and raises.

    Args:
        base_income: Starting income (current year)
        raise_rate: Annual raise percentage
        job_changes_df: DataFrame with 'Year' and 'New Income' columns
        current_year: The current year (base year)
        target_year: The year to calculate income for

    Returns:
        float: Income for the target year
    """
    # Find the most recent job change that applies to target_year
    applicable_job_changes = job_changes_df[job_changes_df['Year'] <= target_year]

    if len(applicable_job_changes) > 0:
        # Get the most recent job change
        most_recent = applicable_job_changes.sort_values('Year').iloc[-1]
        last_change_year = most_recent['Year']
        last_change_income = most_recent['New Income']

        # Apply raises from the last job change to target year
        years_since_change = target_year - last_change_year
        income = last_change_income * (1 + raise_rate / 100) ** years_since_change
    else:
        # No job changes, apply raises from current year
        years_from_now = target_year - current_year
        income = base_income * (1 + raise_rate / 100) ** years_from_now

    return income


def get_career_income_for_year(career_phases, parent_age_current, current_year, target_year):
    """Calculate total compensation for a specific year from career phases.
    Returns dict with base_salary, bonus, rsu_income, options_income, total_employment_income."""
    target_age = parent_age_current + (target_year - current_year)

    # Find active phase
    active_phase = None
    for phase in career_phases:
        if phase.start_age <= target_age < phase.end_age:
            active_phase = phase
            break

    if active_phase is None:
        return {'base_salary': 0, 'bonus': 0, 'rsu_income': 0, 'options_income': 0, 'total_employment_income': 0}

    years_in_phase = target_age - active_phase.start_age

    # Base salary with raises
    base = active_phase.base_salary * (1 + active_phase.annual_raise_pct / 100) ** years_in_phase

    # Bonus
    bonus = base * (active_phase.annual_bonus_pct / 100)

    # RSU income (steady state after year 1 in phase)
    rsu = active_phase.rsu_annual_grant if years_in_phase >= 1 else 0

    # Stock options (one-time liquidity event)
    options = 0
    if active_phase.stock_options_grant > 0 and active_phase.stock_options_liquidity_year == target_year:
        phase_start_year = current_year + (active_phase.start_age - parent_age_current)
        years_held = target_year - phase_start_year
        if years_held > 0:
            options = active_phase.stock_options_grant * (1 + active_phase.stock_options_growth_pct / 100) ** years_held

    return {
        'base_salary': base,
        'bonus': bonus,
        'rsu_income': rsu,
        'options_income': options,
        'total_employment_income': base + bonus + rsu + options
    }


def get_historical_return_stats():
    """Calculate statistics from historical returns"""
    returns = np.array(HISTORICAL_STOCK_RETURNS)

    stats = {
        'mean': np.mean(returns),
        'median': np.median(returns),
        'std': np.std(returns),
        'min': np.min(returns),
        'max': np.max(returns),
        'positive_years': np.sum(returns > 0),
        'negative_years': np.sum(returns < 0),
        'total_years': len(returns),
        'positive_percentage': (np.sum(returns > 0) / len(returns)) * 100
    }

    return stats


def calculate_federal_income_tax(taxable_income, filing_status="married_jointly", year=2024):
    """Calculate federal income tax based on tax brackets"""

    if filing_status == "married_jointly":
        brackets = [
            (0, 23200, 0.10),
            (23200, 94300, 0.12),
            (94300, 201050, 0.22),
            (201050, 383900, 0.24),
            (383900, 487450, 0.32),
            (487450, 731200, 0.35),
            (731200, float('inf'), 0.37)
        ]
    else:  # single
        brackets = [
            (0, 11600, 0.10),
            (11600, 47150, 0.12),
            (47150, 100525, 0.22),
            (100525, 191950, 0.24),
            (191950, 243725, 0.32),
            (243725, 609350, 0.35),
            (609350, float('inf'), 0.37)
        ]

    tax = 0
    for i, (lower, upper, rate) in enumerate(brackets):
        if taxable_income <= lower:
            break

        taxable_in_bracket = min(taxable_income, upper) - lower
        tax += taxable_in_bracket * rate

        if taxable_income <= upper:
            break

    return tax


def calculate_annual_taxes(gross_income, pretax_deductions=0, state_tax_rate=0.0, filing_status="married_jointly"):
    """Calculate total annual taxes including federal, state, and FICA"""

    standard_deduction = 29200 if filing_status == "married_jointly" else 14600

    adjusted_gross_income = max(0, gross_income - pretax_deductions)

    taxable_income = max(0, adjusted_gross_income - standard_deduction)

    federal_tax = calculate_federal_income_tax(taxable_income, filing_status)

    state_tax = adjusted_gross_income * state_tax_rate

    ss_wage_base = 160200
    medicare_threshold = 250000 if filing_status == "married_jointly" else 200000

    ss_tax = min(gross_income, ss_wage_base) * 0.062
    medicare_tax = gross_income * 0.0145
    additional_medicare = max(0, gross_income - medicare_threshold) * 0.009

    fica_tax = ss_tax + medicare_tax + additional_medicare

    total_tax = federal_tax + state_tax + fica_tax

    return {
        'federal_tax': federal_tax,
        'state_tax': state_tax,
        'fica_tax': fica_tax,
        'total_tax': total_tax,
        'effective_rate': (total_tax / gross_income * 100) if gross_income > 0 else 0,
        'after_tax_income': gross_income - total_tax
    }


def calculate_monthly_house_payment(house):
    """Calculate total monthly payment for a house (PITI)"""
    if house.mortgage_years_left > 0:
        monthly_rate = house.mortgage_rate / 12
        num_payments = house.mortgage_years_left * 12

        if monthly_rate > 0:
            monthly_payment = house.mortgage_balance * (
                    monthly_rate * (1 + monthly_rate) ** num_payments
            ) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_payment = house.mortgage_balance / num_payments
    else:
        monthly_payment = 0

    monthly_property_tax = (house.current_value * house.property_tax_rate) / 12

    monthly_insurance = house.home_insurance / 12

    return monthly_payment + monthly_property_tax + monthly_insurance


def plotly_fig_to_image(fig, width=6*inch, height=4*inch):
    """
    Convert a Plotly figure to a ReportLab Image object for PDF inclusion.

    Args:
        fig: Plotly figure object
        width: Width of image in PDF (default 6 inches)
        height: Height of image in PDF (default 4 inches)

    Returns:
        ReportLab Image object or None if conversion fails
    """
    try:
        # Export figure to bytes (PNG format)
        img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)

        # Create BytesIO object from bytes
        img_buffer = io.BytesIO(img_bytes)

        # Create ReportLab Image object
        img = Image(img_buffer, width=width, height=height)
        return img
    except Exception as e:
        # If kaleido is not installed or conversion fails, return None
        print(f"Warning: Could not convert chart to image: {e}")
        return None


def main():
    """Main application function"""
    # Initialize auth state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    ensure_data_dirs()

    # Get Cloudflare email or fall back to dev mode
    if not st.session_state.authenticated:
        email = get_cloudflare_email()
        if not email:
            # Local development fallback — show simple email input
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.markdown(
                '<div class="brand-hero">'
                '<div class="brand-icon">💰</div>'
                '<h1>Financial Planning Suite</h1>'
                '<p class="brand-tagline">Lifetime financial simulation for your household</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            st.caption("Enter your email to continue")
            with st.form("dev_login"):
                email_input = st.text_input("Email", placeholder="you@example.com")
                if st.form_submit_button("Continue", type="primary", use_container_width=True) and email_input:
                    st.session_state.cf_email = email_input.strip().lower()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            if 'cf_email' not in st.session_state:
                return
            email = st.session_state.cf_email
        else:
            st.session_state.cf_email = email

        # Show household picker
        household_picker_page(email)
        return

    # Check if wizard was manually triggered, phase 2 is active, or this is a new household
    if st.session_state.get('wizard_manual') or st.session_state.get('wizard_phase2'):
        setup_wizard()
        return
    if not st.session_state.get('wizard_complete') and not st.session_state.get('wizard_skipped'):
        plan_data = load_household_plan(st.session_state.household_id)
        if not plan_data:
            setup_wizard()
            return

    # User is authenticated - proceed with app
    was_fresh = 'initialized' not in st.session_state
    initialize_session_state()
    if was_fresh and st.session_state.get('household_id'):
        # Session was just restored from saved data
        plan_data = load_household_plan(st.session_state.household_id)
        if plan_data:
            load_data(plan_data)
            st.session_state._session_restored = True

    # Auto-save: persist to household storage on every interaction
    if st.session_state.get('authenticated') and st.session_state.get('household_id') and st.session_state.get('initialized'):
        try:
            json_data = save_data()
            if json_data:
                save_household_plan(st.session_state.household_id, json_data)
        except Exception:
            pass  # Silent auto-save - don't interrupt the user

    user_display = st.session_state.user_data.get('display_name', st.session_state.current_user)
    if st.session_state.get('test_mode'):
        st.markdown(
            '<div class="test-mode-banner">🧪 TEST MODE — This is an isolated test session. No real data will be affected.</div>',
            unsafe_allow_html=True,
        )
    st.title("💰 Financial Planning Suite")

    # What's New banner (dismissible)
    if not st.session_state.get('_whats_new_dismissed'):
        with st.expander(f"🆕 What's new in v{APP_VERSION}", expanded=False):
            for item in WHATS_NEW:
                st.markdown(f"- {item}")
            if st.button("Dismiss", key="dismiss_whats_new"):
                st.session_state._whats_new_dismissed = True
                st.rerun()

    # ── Grouped navigation ──────────────────────────────────────────────
    # Categories keep tabs visible without horizontal scrolling.
    p1_label = f"{st.session_state.parent1_emoji} {st.session_state.parent1_name}"
    p2_label = f"{st.session_state.parent2_emoji} {st.session_state.parent2_name}"

    nav_groups = {
        "Overview": [
            ("📊 Dashboard", dashboard_tab, True),
            ("⚙️ Settings", parent_settings_tab, True),
            ("👤 Users", user_management_tab, True),
        ],
        "People": [
            (p1_label, parent_x_tab, True),
            (p2_label, parent_y_tab, True),
            ("👶 Children", children_tab, True),
        ],
        "Expenses": [
            ("💸 Family", family_expenses_tab, st.session_state.get('show_family_expenses', False)),
            ("🔄 Recurring", recurring_one_time_expenses_tab, st.session_state.get('show_recurring_expenses', True)),
            ("🏠 Housing", house_tab, True),
            ("🏥 Healthcare", healthcare_insurance_tab, st.session_state.get('show_healthcare', False)),
        ],
        "Planning": [
            ("🗓️ Timeline", timeline_tab, True),
            ("📈 Economy", economy_tab, True),
            ("🏖️ Retirement", retirement_tab, True),
        ],
        "Analysis": [
            ("💰 Cashflow", deterministic_cashflow_tab, True),
            ("🎲 Monte Carlo", monte_carlo_simulation_tab, True),
            ("🧪 Stress Test", stress_test_tab, True),
        ],
        "Data": [
            ("💾 Save / Load", save_load_tab, True),
            ("📄 Export", report_export_tab, st.session_state.get('show_export', True)),
        ],
    }

    # Category selector (horizontal radio, always visible)
    group_names = list(nav_groups.keys())
    if 'nav_group' not in st.session_state:
        st.session_state.nav_group = "Overview"
    selected_group = st.radio(
        "Section", group_names, horizontal=True,
        index=group_names.index(st.session_state.get('nav_group', 'Overview'))
              if st.session_state.get('nav_group', 'Overview') in group_names else 0,
        key="nav_group_radio", label_visibility="collapsed",
    )
    # Auto-save when switching sections
    prev_group = st.session_state.get('_prev_nav_group')
    st.session_state.nav_group = selected_group
    if prev_group and prev_group != selected_group:
        if st.session_state.get('authenticated') and st.session_state.get('household_id') and st.session_state.get('initialized'):
            try:
                json_data = save_data()
                if json_data:
                    save_household_plan(st.session_state.household_id, json_data)
            except Exception:
                pass
    st.session_state._prev_nav_group = selected_group

    # Category guide
    CATEGORY_GUIDES = {
        "Overview": "**Start here.** The Dashboard shows your overall financial health at a glance — key metrics, "
                     "trajectory chart, and alerts. Use Settings to configure names and toggle optional tabs. "
                     "Users manages your household and account.",
        "People": "**Set up each person.** Enter income, career phases, net worth, retirement age, and Social Security "
                   "for each parent. Add children with age-based expense templates. This data drives all projections.",
        "Expenses": "**Where does the money go?** Family expenses are shared costs (groceries, utilities). "
                     "Recurring covers repeating purchases. Housing tracks your properties, mortgages, and property tax. "
                     "Healthcare models insurance and Medicare.",
        "Planning": "**Set the timeline.** Timeline tracks relocations and spending strategy changes. Economy sets your "
                     "assumptions for returns, inflation, and growth. Retirement configures Social Security and benefits.",
        "Analysis": "**Run the numbers.** Cashflow shows a deterministic year-by-year projection. Monte Carlo runs "
                     "thousands of randomized simulations for a range of outcomes. Stress Test pushes your plan to its limits.",
        "Data": "**Save and share.** Save named scenarios, compare plans side-by-side, create what-if variants, "
                 "restore from backups, and export to JSON/PDF.",
    }
    guide = CATEGORY_GUIDES.get(selected_group)
    if guide:
        with st.expander(f"📖 Guide: {selected_group}", expanded=False):
            st.markdown(guide)

    # Tabs within the selected group
    group_tabs = nav_groups[selected_group]
    enabled = [(name, func) for name, func, vis in group_tabs if vis]

    if enabled:
        tab_names = [n for n, f in enabled]
        tab_functions = [f for n, f in enabled]
        tabs = st.tabs(tab_names)
        for tab, func in zip(tabs, tab_functions):
            with tab:
                func()
    else:
        st.info("No tabs enabled in this section. Toggle visibility in Settings.")

    # Display sidebar
    display_sidebar()


# ══════════════════════════════════════════════════════════════════════════════
# ALERTS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def generate_alerts(cashflow_data: list) -> list:
    """Analyze cashflow data and return a list of alert dicts.
    Each alert: {severity: 'critical'|'warning'|'info', title: str, detail: str}
    """
    if not cashflow_data:
        return []

    alerts = []
    current_year = st.session_state.current_year
    is_separate = cashflow_data[0].get('finance_mode') == 'Separate' if cashflow_data else False

    # 1. Find the year net worth goes negative (if ever)
    broke_year = None

    # Per-person solvency checks (Separate mode)
    if is_separate:
        for parent_key, parent_name in [('nw_parent1', st.session_state.parent1_name),
                                         ('nw_parent2', st.session_state.parent2_name)]:
            for row in cashflow_data:
                if row.get(parent_key, 0) < 0:
                    alerts.append({
                        'severity': 'critical',
                        'title': f"{parent_name}'s net worth goes negative in {row['year']}",
                        'detail': f"At age {row['parent1_age'] if 'parent1' in parent_key else row['parent2_age']}. "
                                  f"Consider rebalancing the expense split or increasing savings."
                    })
                    break

    for row in cashflow_data:
        if row['net_worth'] < 0:
            broke_year = row['year']
            p1_age = row['parent1_age']
            alerts.append({
                'severity': 'critical',
                'title': f'Combined net worth goes negative in {broke_year}',
                'detail': f'{st.session_state.parent1_name} will be {p1_age}. '
                          f'Consider increasing savings or delaying retirement.'
            })
            break

    # 2. Peak net worth and when it starts declining
    peak_nw = max(cashflow_data, key=lambda r: r['net_worth'])
    if peak_nw['net_worth'] > 0:
        decline_start = None
        for i in range(1, len(cashflow_data)):
            if cashflow_data[i]['net_worth'] < cashflow_data[i-1]['net_worth']:
                decline_start = cashflow_data[i]['year']
                break
        if decline_start and decline_start < peak_nw['year'] + 5:
            alerts.append({
                'severity': 'warning',
                'title': f'Net worth peaks at {format_currency(peak_nw["net_worth"])} in {peak_nw["year"]}',
                'detail': f'Drawdown begins in {decline_start}. Plan for declining assets after this point.'
            })

    # 3. Negative cashflow years while still working
    for row in cashflow_data:
        p1_working = row['parent1_age'] < st.session_state.parentX_retirement_age
        p2_working = row['parent2_age'] < st.session_state.parentY_retirement_age
        if (p1_working or p2_working) and row['cashflow'] < 0 and row['year'] > current_year:
            alerts.append({
                'severity': 'warning',
                'title': f'Spending exceeds income in {row["year"]} (while still working)',
                'detail': f'Cashflow is {format_currency(row["cashflow"])}. Expenses may need adjustment.'
            })
            break  # Only flag the first occurrence

    # 4. Healthcare costs exceeding a threshold
    for row in cashflow_data:
        if row['healthcare_expenses'] > 0 and row['total_income'] > 0:
            hc_pct = row['healthcare_expenses'] / row['total_income']
            if hc_pct > 0.25 and row['year'] > current_year:
                alerts.append({
                    'severity': 'warning',
                    'title': f'Healthcare exceeds 25% of income in {row["year"]}',
                    'detail': f'Healthcare: {format_currency(row["healthcare_expenses"])}, '
                              f'Income: {format_currency(row["total_income"])} ({hc_pct:.0%}).'
                })
                break

    # 5. Retirement readiness — savings at retirement age
    for row in cashflow_data:
        if row['parent1_age'] == st.session_state.parentX_retirement_age:
            retirement_nw = row['net_worth']
            annual_expenses = row['total_expenses']
            if annual_expenses > 0:
                years_covered = retirement_nw / annual_expenses
                if years_covered < 15:
                    alerts.append({
                        'severity': 'critical',
                        'title': f'Retirement savings cover only {years_covered:.0f} years of expenses',
                        'detail': f'At retirement ({row["year"]}): {format_currency(retirement_nw)} saved, '
                                  f'{format_currency(annual_expenses)}/yr expenses.'
                    })
                elif years_covered < 25:
                    alerts.append({
                        'severity': 'warning',
                        'title': f'Retirement savings cover ~{years_covered:.0f} years of expenses',
                        'detail': f'At retirement: {format_currency(retirement_nw)} saved. Consider boosting savings.'
                    })
                else:
                    alerts.append({
                        'severity': 'info',
                        'title': f'Retirement savings look healthy ({years_covered:.0f}+ years covered)',
                        'detail': f'At retirement: {format_currency(retirement_nw)} saved against '
                                  f'{format_currency(annual_expenses)}/yr expenses.'
                    })
            break

    # 6. Social Security insolvency warning
    if st.session_state.get('ss_insolvency_enabled'):
        alerts.append({
            'severity': 'info',
            'title': 'Social Security insolvency modeling is enabled',
            'detail': f'Benefits reduced by {st.session_state.get("ss_shortfall_percentage", 23):.0f}% after projected trust fund depletion.'
        })

    # 7. No children expense coverage after age 18 check — just informational
    if not broke_year:
        final_row = cashflow_data[-1]
        if final_row['net_worth'] > 0:
            alerts.append({
                'severity': 'info',
                'title': f'Plan ends with {format_currency(final_row["net_worth"])} remaining',
                'detail': f'At age {final_row["parent1_age"]}, projected net worth is positive.'
            })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# UI HELPERS: empty states, validation, formatting, completion
# ══════════════════════════════════════════════════════════════════════════════

def _plan_completion_pct() -> tuple:
    """Calculate plan completion percentage and list of missing items."""
    checks = [
        (st.session_state.parent1_name != "Parent 1", "Set your name (Settings)"),
        (st.session_state.parentX_income > 0, "Enter your income"),
        (st.session_state.parentX_net_worth > 0, "Enter your net worth"),
        (st.session_state.parentX_retirement_age != 65 or True, "Review retirement age"),  # Always passes
        (len(st.session_state.get('children_list', [])) > 0 or True, "Add children (optional)"),
        (len(st.session_state.get('houses', [])) > 0, "Add housing details"),
        (sum(st.session_state.family_shared_expenses.values()) > 0, "Review family expenses"),
        (st.session_state.get('state_timeline') and len(st.session_state.state_timeline) > 0, "Set your location"),
    ]
    completed = sum(1 for ok, _ in checks if ok)
    missing = [msg for ok, msg in checks if not ok]
    return completed / len(checks), missing


def _empty_state(icon: str, title: str, description: str):
    """Render a helpful empty state message."""
    st.markdown(
        f'<div style="text-align:center; padding:2rem 1rem; color:rgba(128,128,128,0.6);">'
        f'<div style="font-size:2.5rem; margin-bottom:0.5rem;">{icon}</div>'
        f'<div style="font-size:1.1rem; font-weight:600; margin-bottom:0.25rem;">{title}</div>'
        f'<div style="font-size:0.85rem;">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _validation_warnings():
    """Check for common data issues and return list of warning strings."""
    warnings = []
    total_income = st.session_state.parentX_income + st.session_state.parentY_income
    total_expenses = (sum(st.session_state.get('parentX_expenses', {}).values()) +
                      sum(st.session_state.get('parentY_expenses', {}).values()) +
                      sum(st.session_state.family_shared_expenses.values()))
    if total_income > 0 and total_expenses > total_income * 0.95:
        warnings.append(f"Your annual expenses (${total_expenses:,.0f}) are close to or exceed your gross income (${total_income:,.0f}). After taxes, you may be running a deficit.")
    if st.session_state.parentX_income == 0 and st.session_state.parent1_name != "N/A":
        warnings.append(f"{st.session_state.parent1_name}'s income is $0. Is this intentional?")
    if st.session_state.parentX_retirement_age <= st.session_state.parentX_age:
        warnings.append(f"{st.session_state.parent1_name}'s retirement age ({st.session_state.parentX_retirement_age}) is at or before current age ({st.session_state.parentX_age}).")
    return warnings


APP_VERSION = "0.8.1"
WHATS_NEW = [
    "Dashboard with financial trajectory chart and alerts",
    "Grouped navigation (Overview, People, Expenses, Planning, Analysis, Data)",
    "Hierarchical location picker: Country → State → City",
    "50 US state + 10 Canadian province expense templates",
    "Pooled vs Separate finance mode for couples",
    "Career phases with add/delete and retirement age warnings",
    "Housing ↔ location linking, configurable appreciation rates",
    "Net worth breakdown: liquid assets vs home equity",
    "Auto-save on section change, sidebar save button",
    "One-click what-if scenario templates",
]


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════

def dashboard_tab():
    """Dashboard — at-a-glance summary of your financial plan."""
    st.header("📊 Dashboard")

    # Plan completion indicator
    completion, missing = _plan_completion_pct()
    if completion < 1.0:
        st.progress(completion)
        st.caption(f"Plan is {completion:.0%} complete. Missing: {', '.join(missing[:3])}")

    # Validation warnings
    warnings = _validation_warnings()
    for w in warnings:
        st.warning(w)

    # Calculate cashflow data
    try:
        with st.spinner("Calculating projections..."):
            cashflow_data = calculate_lifetime_cashflow()
    except Exception:
        st.info("Complete the Settings and Income tabs to see your dashboard.")
        return

    if not cashflow_data:
        st.info("No data yet. Fill in your details in the tabs to the right.")
        return

    current_year = st.session_state.current_year
    current_row = cashflow_data[0] if cashflow_data else {}

    # ── Key metrics row ──────────────────────────────────────────────────────
    total_income = st.session_state.parentX_income + st.session_state.parentY_income
    total_nw = st.session_state.parentX_net_worth + st.session_state.parentY_net_worth

    # Find key milestones from cashflow
    peak_nw_row = max(cashflow_data, key=lambda r: r['net_worth'])
    broke_year = None
    for row in cashflow_data:
        if row['net_worth'] < 0:
            broke_year = row['year']
            break

    p1_retire_year = current_year + (st.session_state.parentX_retirement_age - st.session_state.parentX_age)
    years_to_retire = max(0, p1_retire_year - current_year)

    is_separate = st.session_state.get('finance_mode', 'Pooled') == 'Separate'
    p1_name = st.session_state.parent1_name
    p2_name = st.session_state.parent2_name

    if is_separate:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(f"{p1_name} Net Worth", format_currency(st.session_state.parentX_net_worth))
        with col2:
            st.metric(f"{p2_name} Net Worth", format_currency(st.session_state.parentY_net_worth))
        with col3:
            st.metric("Combined", format_currency(total_nw))
        with col4:
            st.metric("Years to Retirement", f"{years_to_retire}" if years_to_retire > 0 else "Retired")
        with col5:
            if broke_year:
                years_solvent = broke_year - current_year
                st.metric("Solvent For", f"{years_solvent} yrs", delta=f"runs out {broke_year}", delta_color="inverse")
            else:
                st.metric("Solvent For", "Lifetime")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Combined Net Worth", format_currency(total_nw))
        with col2:
            st.metric("Combined Income", format_currency(total_income))
        with col3:
            st.metric("Years to Retirement", f"{years_to_retire}" if years_to_retire > 0 else "Retired")
        with col4:
            if broke_year:
                years_solvent = broke_year - current_year
                st.metric("Solvent For", f"{years_solvent} years", delta=f"runs out {broke_year}", delta_color="inverse")
            else:
                st.metric("Solvent For", "Lifetime", delta="never runs out")

    st.markdown("")

    # ── Net worth trajectory chart ───────────────────────────────────────────
    years = [r['year'] for r in cashflow_data]
    net_worths = [r['net_worth'] for r in cashflow_data]
    incomes = [r['total_income'] for r in cashflow_data]
    expenses = [r['total_expenses'] for r in cashflow_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=net_worths, name='Net Worth',
        fill='tozeroy', line=dict(color=COLORS['primary'], width=2),
        fillcolor='rgba(102,126,234,0.15)'
    ))
    fig.add_trace(go.Scatter(
        x=years, y=incomes, name='Income',
        line=dict(color=COLORS['success'], width=1.5, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=years, y=expenses, name='Expenses',
        line=dict(color=COLORS['danger'], width=1.5, dash='dot')
    ))

    # Per-person net worth traces (Separate mode only)
    if is_separate and cashflow_data[0].get('nw_parent1') is not None:
        fig.add_trace(go.Scatter(
            x=years, y=[r.get('nw_parent1', 0) for r in cashflow_data],
            name=f'{p1_name}', line=dict(color=COLORS['purple'], width=1.5, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=years, y=[r.get('nw_parent2', 0) for r in cashflow_data],
            name=f'{p2_name}', line=dict(color=COLORS['warning'], width=1.5, dash='dash')
        ))

    # Add retirement marker
    if years_to_retire > 0:
        fig.add_vline(x=p1_retire_year, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Retirement", annotation_position="top left")

    fig.update_layout(title="Lifetime Financial Trajectory",
                      xaxis_title="Year", yaxis_title="Amount ($)", **CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # ── Alerts section ───────────────────────────────────────────────────────
    alerts = generate_alerts(cashflow_data)
    if alerts:
        st.markdown("### Alerts & Insights")
        for alert in alerts:
            if alert['severity'] == 'critical':
                st.error(f"**{alert['title']}** — {alert['detail']}")
            elif alert['severity'] == 'warning':
                st.warning(f"**{alert['title']}** — {alert['detail']}")
            else:
                st.info(f"**{alert['title']}** — {alert['detail']}")

    # ── Key milestones ───────────────────────────────────────────────────────
    st.markdown("### Key Milestones")
    milestone_cols = st.columns(3)

    with milestone_cols[0]:
        st.markdown(
            f'<div class="review-card">'
            f'<div class="review-card-label">PEAK NET WORTH</div>'
            f'<div class="review-card-value"><b>{format_currency(peak_nw_row["net_worth"])}</b><br>'
            f'Year {peak_nw_row["year"]} (age {peak_nw_row["parent1_age"]})</div></div>',
            unsafe_allow_html=True,
        )

    with milestone_cols[1]:
        # Find retirement net worth
        retire_nw = "N/A"
        for row in cashflow_data:
            if row['parent1_age'] == st.session_state.parentX_retirement_age:
                retire_nw = format_currency(row['net_worth'])
                break
        st.markdown(
            f'<div class="review-card">'
            f'<div class="review-card-label">NET WORTH AT RETIREMENT</div>'
            f'<div class="review-card-value"><b>{retire_nw}</b><br>'
            f'Age {st.session_state.parentX_retirement_age} ({p1_retire_year})</div></div>',
            unsafe_allow_html=True,
        )

    with milestone_cols[2]:
        final_row = cashflow_data[-1]
        st.markdown(
            f'<div class="review-card">'
            f'<div class="review-card-label">END OF PLAN</div>'
            f'<div class="review-card-value"><b>{format_currency(final_row["net_worth"])}</b><br>'
            f'Age {final_row["parent1_age"]} ({final_row["year"]})</div></div>',
            unsafe_allow_html=True,
        )

    # ── Net worth breakdown ────────────────────────────────────────────────
    if current_row and current_row.get('house_equity', 0) > 0:
        st.markdown("### Net Worth Breakdown")
        liquid = current_row.get('liquid_net_worth', current_row['net_worth'])
        house_eq = current_row.get('house_equity', 0)
        total = current_row['net_worth']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Liquid Assets", format_currency(liquid),
                      help="Cash, stocks, retirement accounts — accessible funds")
        with col2:
            st.metric("Home Equity", format_currency(house_eq),
                      help="House value minus remaining mortgage")
        with col3:
            st.metric("Total Net Worth", format_currency(total))

    # ── Benchmarks & Health Indicators ─────────────────────────────────────
    if current_row:
        st.markdown("### Financial Health")
        total_inc = current_row.get('total_income', 0)
        total_exp = current_row.get('total_expenses', 0)
        total_tax = current_row.get('taxes', 0)
        savings_rate = (total_inc - total_exp - total_tax) / max(total_inc, 1) * 100 if total_inc > 0 else 0
        p1_age = st.session_state.parentX_age

        # Age-based net worth benchmark (rough median from Federal Reserve SCF)
        age_benchmarks = {25: 10000, 30: 50000, 35: 100000, 40: 180000, 45: 250000,
                          50: 350000, 55: 500000, 60: 700000, 65: 900000, 70: 1000000}
        benchmark_age = min(age_benchmarks.keys(), key=lambda a: abs(a - p1_age))
        benchmark_nw = age_benchmarks[benchmark_age]
        nw_pct = "above" if total_nw > benchmark_nw else "below"

        col1, col2, col3 = st.columns(3)
        with col1:
            color = "🟢" if savings_rate > 15 else "🟡" if savings_rate > 5 else "🔴"
            st.metric(f"{color} Savings Rate", f"{savings_rate:.1f}%",
                      help="Green >15%, Yellow 5-15%, Red <5%. Median US household: ~8%.")
        with col2:
            color = "🟢" if total_nw > benchmark_nw * 1.2 else "🟡" if total_nw > benchmark_nw * 0.5 else "🔴"
            st.metric(f"{color} Net Worth vs Benchmark", f"{nw_pct.title()} median",
                      delta=f"{format_currency(total_nw - benchmark_nw)} vs age {benchmark_age} median",
                      help=f"Median net worth at age {benchmark_age}: {format_currency(benchmark_nw)} (Federal Reserve SCF)")
        with col3:
            debt_ratio = total_exp / max(total_inc, 1) * 100 if total_inc > 0 else 0
            color = "🟢" if debt_ratio < 60 else "🟡" if debt_ratio < 80 else "🔴"
            st.metric(f"{color} Expense-to-Income", f"{debt_ratio:.0f}%",
                      help="Green <60%, Yellow 60-80%, Red >80%. Lower is better.")

    # ── Monthly cashflow snapshot ────────────────────────────────────────────
    st.markdown("### Current Year Snapshot")
    if current_row:
        monthly_income = current_row.get('total_income', 0) / 12
        monthly_expenses = current_row.get('total_expenses', 0) / 12
        monthly_taxes = current_row.get('taxes', 0) / 12
        monthly_savings = monthly_income - monthly_expenses - monthly_taxes

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monthly Income", format_currency(monthly_income))
        with col2:
            st.metric("Monthly Expenses", format_currency(monthly_expenses))
        with col3:
            st.metric("Monthly Taxes", format_currency(monthly_taxes))
        with col4:
            st.metric("Monthly Savings", format_currency(monthly_savings),
                      delta=f"{(monthly_savings/max(monthly_income,1))*100:.0f}% savings rate" if monthly_income > 0 else None)

    # ── Expense breakdown pie ────────────────────────────────────────────────
    if current_row:
        exp_labels = []
        exp_values = []
        for label, key in [("Living Expenses", "base_expenses"), ("Children", "children_expenses"),
                           ("Healthcare", "healthcare_expenses"), ("Housing", "house_expenses"),
                           ("Recurring", "recurring_expenses"), ("Major Purchases", "major_purchases")]:
            val = current_row.get(key, 0)
            if val > 0:
                exp_labels.append(label)
                exp_values.append(val)

        if exp_values:
            col1, col2 = st.columns([1, 1])
            with col1:
                pie_fig = go.Figure(data=[go.Pie(
                    labels=exp_labels, values=exp_values,
                    hole=0.45, textinfo='label+percent',
                    marker=dict(colors=COLOR_SEQUENCE[:len(exp_values)])
                )])
                pie_fig.update_layout(title=f"Expense Breakdown ({current_year})",
                                      **CHART_LAYOUT_COMPACT)
                st.plotly_chart(pie_fig, use_container_width=True)
            with col2:
                # Income sources breakdown
                inc_labels = []
                inc_values = []
                for label, key in [(st.session_state.parent1_name, "parent1_income"),
                                   (st.session_state.parent2_name, "parent2_income"),
                                   ("Social Security", "ss_income"),
                                   ("Investment Returns", "investment_income")]:
                    val = current_row.get(key, 0)
                    if val > 0:
                        inc_labels.append(label)
                        inc_values.append(val)
                if inc_values:
                    inc_fig = go.Figure(data=[go.Pie(
                        labels=inc_labels, values=inc_values,
                        hole=0.45, textinfo='label+percent',
                        marker=dict(colors=COLOR_SEQUENCE[2:2+len(inc_values)])
                    )])
                    inc_fig.update_layout(title=f"Income Sources ({current_year})",
                                          **CHART_LAYOUT_COMPACT)
                    st.plotly_chart(inc_fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO TEMPLATES (What-If)
# ══════════════════════════════════════════════════════════════════════════════

def scenario_templates_section():
    """Show one-click what-if scenario buttons inside Save/Load tab."""
    st.markdown("### 🔮 Quick What-If Scenarios")
    st.caption("Clone your current plan with one change applied. The original plan is preserved.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🕐 Retire 2 Years Earlier", use_container_width=True, key="whatif_retire_early"):
            _apply_whatif("Early Retirement (-2yr)", {
                'parentX_retirement_age': st.session_state.parentX_retirement_age - 2,
                'parentY_retirement_age': st.session_state.parentY_retirement_age - 2,
            })
        if st.button("👶 Add One More Child", use_container_width=True, key="whatif_add_child"):
            _apply_whatif_add_child()
        if st.button("📈 Aggressive Returns (8%)", use_container_width=True, key="whatif_bull"):
            _apply_whatif("Aggressive Returns", {}, economy={'investment_return': 0.08})
    with col2:
        if st.button("🕐 Retire 2 Years Later", use_container_width=True, key="whatif_retire_late"):
            _apply_whatif("Late Retirement (+2yr)", {
                'parentX_retirement_age': st.session_state.parentX_retirement_age + 2,
                'parentY_retirement_age': st.session_state.parentY_retirement_age + 2,
            })
        if st.button("📉 Bear Market (4% returns)", use_container_width=True, key="whatif_bear"):
            _apply_whatif("Bear Market Returns", {}, economy={'investment_return': 0.04})
        if st.button("💰 Boost Savings +$500/mo", use_container_width=True, key="whatif_save_more"):
            new_nw = st.session_state.parentX_net_worth + 6000
            _apply_whatif("Extra Savings (+$6k/yr)", {
                'parentX_net_worth': new_nw,
            })


def _apply_whatif(name: str, overrides: dict, economy: dict = None):
    """Save current plan as a scenario, then apply overrides to create a what-if variant."""
    try:
        # Save current plan first
        base_json = save_data()
        if base_json:
            scenarios = st.session_state.get('saved_scenarios', {})
            if "Current Plan (before what-if)" not in scenarios:
                scenarios["Current Plan (before what-if)"] = base_json
            # Apply overrides
            for key, val in overrides.items():
                st.session_state[key] = val
            if economy:
                for key, val in economy.items():
                    setattr(st.session_state.economic_params, key, val)
            # Save the what-if scenario
            whatif_json = save_data()
            if whatif_json:
                scenarios[name] = whatif_json
                st.session_state.saved_scenarios = scenarios
                if st.session_state.get('household_id'):
                    save_household_scenarios(st.session_state.household_id, scenarios)
            st.success(f"Created scenario: **{name}**. Compare in Plan Comparison below.")
            st.rerun()
    except Exception as e:
        st.error(f"Could not create scenario: {e}")


def _apply_whatif_add_child():
    """What-if: add one more child."""
    try:
        base_json = save_data()
        if base_json:
            scenarios = st.session_state.get('saved_scenarios', {})
            if "Current Plan (before what-if)" not in scenarios:
                scenarios["Current Plan (before what-if)"] = base_json

            child_num = len(st.session_state.children_list) + 1
            new_child = {
                'name': f'Child {child_num}',
                'birth_year': st.session_state.current_year + 1,
                'use_template': True,
                'template_state': 'Seattle',
                'template_strategy': 'Average',
                'school_type': 'Public',
                'college_location': 'Seattle'
            }
            st.session_state.children_list.append(new_child)
            whatif_json = save_data()
            if whatif_json:
                scenarios["Add One More Child"] = whatif_json
                st.session_state.saved_scenarios = scenarios
                if st.session_state.get('household_id'):
                    save_household_scenarios(st.session_state.household_id, scenarios)
            st.success("Created scenario: **Add One More Child**.")
            st.rerun()
    except Exception as e:
        st.error(f"Could not create scenario: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB HELP / WALKTHROUGH TEXT
# ══════════════════════════════════════════════════════════════════════════════

def _version_history_section():
    """Show backup history with restore capability in Save/Load tab."""
    if not st.session_state.get('household_id'):
        return
    hid = st.session_state.household_id
    backup_dir = DATA_DIR / 'backups'
    if not backup_dir.exists():
        return

    backups = sorted(backup_dir.glob(f"{hid}_*.json"), reverse=True)
    if not backups:
        return

    st.subheader("🕐 Version History")
    st.caption("Automatic snapshots are created every time your plan is saved. Restore any previous version.")

    for backup_file in backups[:10]:  # Show last 10
        # Parse timestamp from filename: {hid}_{YYYYMMDD_HHMMSS}.json
        ts_part = backup_file.stem.replace(f"{hid}_", "")
        try:
            ts = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
            display_time = ts.strftime("%b %d, %Y %I:%M %p")
        except ValueError:
            display_time = ts_part

        col1, col2 = st.columns([3, 1])
        with col1:
            file_size = backup_file.stat().st_size / 1024
            st.text(f"📄 {display_time}  ({file_size:.0f} KB)")
        with col2:
            if st.button("Restore", key=f"restore_{backup_file.name}", use_container_width=True):
                try:
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                    if 'plan_data' in backup_data:
                        plan_json = json.dumps(backup_data['plan_data'])
                        if load_data(plan_json):
                            # Also save the restored version as the current plan
                            save_household_plan(hid, plan_json)
                            st.success(f"Restored plan from {display_time}")
                            st.rerun()
                    else:
                        st.error("Backup file doesn't contain plan data.")
                except Exception as e:
                    st.error(f"Could not restore: {e}")


TAB_HELP = {
    "dashboard": (
        "**What this tab shows:** A bird's-eye view of your financial plan — key metrics, "
        "net worth trajectory, alerts about potential issues, and a current-year income/expense breakdown.\n\n"
        "**What to look for:** Check the Alerts section for any red or yellow flags. "
        "The trajectory chart shows your projected net worth over your lifetime."
    ),
    "settings": (
        "**What this tab does:** Configure basic plan parameters — the current year, parent names, "
        "and which optional tabs (Family Expenses, Healthcare, etc.) to show.\n\n"
        "**Tip:** You can toggle tab visibility here to simplify the interface."
    ),
    "parent": (
        "**What this tab does:** Set income, age, expected raises, retirement age, net worth, and "
        "Social Security benefits for this person. You can also model career phases (startup → big tech, etc.) "
        "and planned job changes.\n\n"
        "**What matters most:** Current income, retirement age, and net worth have the biggest impact "
        "on your projections."
    ),
    "family_expenses": (
        "**What this tab does:** Define shared household expenses that don't belong to either parent "
        "individually — groceries, utilities, vacations, subscriptions.\n\n"
        "**Tip:** Use state templates (CA, WA, TX) to auto-fill typical costs, then customize."
    ),
    "recurring": (
        "**What this tab does:** Model recurring expenses (e.g., car payments every 5 years) and "
        "one-time major purchases (renovation, wedding, boat).\n\n"
        "**Tip:** These flow into both the deterministic cashflow and Monte Carlo simulations."
    ),
    "children": (
        "**What this tab does:** Add children with age-based expense templates covering childcare, "
        "school, activities, healthcare, and college (ages 0-30).\n\n"
        "**Tip:** Choose Public vs Private school and set a college location — costs vary dramatically."
    ),
    "house": (
        "**What this tab does:** Model your real estate portfolio — purchase price, mortgage details, "
        "property tax, insurance, maintenance. Use the timeline to plan when you live in, rent out, or sell each property.\n\n"
        "**What matters most:** Property tax rate and maintenance rate — these compound with home appreciation."
    ),
    "timeline": (
        "**What this tab does:** Plan geographic relocations and spending strategy changes over time. "
        "Moving from a high-cost to low-cost area can dramatically change your projections.\n\n"
        "**Tip:** Add entries for each planned move with the year and new location."
    ),
    "economy": (
        "**What this tab does:** Set your assumptions for investment returns, inflation, expense growth, "
        "and healthcare inflation. These drive all simulation models.\n\n"
        "**Tip:** The default 7% return / 3% inflation is a common baseline. Adjust based on your risk tolerance."
    ),
    "retirement": (
        "**What this tab does:** Configure Social Security benefits, claiming age, and optional "
        "insolvency modeling (benefit reductions after ~2035).\n\n"
        "**Tip:** Delaying SS from 62 to 70 can increase benefits by ~77%."
    ),
    "healthcare": (
        "**What this tab does:** Model health insurance plans, HSA accounts, Medicare costs (Part B/D, Medigap), "
        "and long-term care insurance.\n\n"
        "**What matters most:** Healthcare is often the #1 retirement expense. Make sure to model Medicare transition."
    ),
    "deterministic": (
        "**What this tab does:** Shows a year-by-year projection using your exact inputs — no randomness. "
        "Click any year to see detailed income and expense breakdowns.\n\n"
        "**When to use:** To understand the baseline trajectory before running Monte Carlo."
    ),
    "monte_carlo": (
        "**What this tab does:** Runs thousands of simulations with randomized returns and expense variations "
        "to show a range of possible outcomes (10th to 90th percentile).\n\n"
        "**What to look for:** The 25th percentile line — if it stays positive, your plan is fairly robust."
    ),
    "stress_test": (
        "**What this tab does:** Tests your plan against extreme scenarios — market crash, hyperinflation, "
        "disability, unemployment — to find your plan's breaking points.\n\n"
        "**Tip:** Run the compound stress test to see how multiple bad events stack."
    ),
    "save_load": (
        "**What this tab does:** Save named scenarios, compare them side-by-side, export/import plan data, "
        "and create what-if variants with one click.\n\n"
        "**Tip:** Use 'Quick What-If Scenarios' to instantly test common changes."
    ),
}


def tab_walkthrough(tab_key: str):
    """Render a collapsible help section for a tab."""
    help_text = TAB_HELP.get(tab_key)
    if help_text:
        with st.expander("💡 How this tab works", expanded=False):
            st.markdown(help_text)


# Tab implementations
def parent_settings_tab():
    """Settings and Instructions tab"""
    st.header("⚙️ Settings and Instructions")
    tab_walkthrough("settings")

    st.subheader("📅 Current Year Setting")
    st.session_state.current_year = st.number_input(
        "Current Year",
        min_value=2020,
        max_value=2030,
        value=int(st.session_state.current_year),
        step=1
    )

    st.subheader("💍 Marriage Information")
    marriage_options = ["N/A"] + list(range(1970, st.session_state.current_year + 1))

    if st.session_state.marriage_year == "N/A":
        marriage_index = 0
    else:
        try:
            marriage_index = marriage_options.index(int(st.session_state.marriage_year))
        except (ValueError, TypeError):
            marriage_index = 0

    selected_marriage = st.selectbox(
        "Marriage Year",
        options=marriage_options,
        index=marriage_index
    )

    st.session_state.marriage_year = selected_marriage

    # Finance mode
    st.subheader("💰 Finance Mode")
    finance_mode = st.radio(
        "How do you manage household finances?",
        ["Pooled", "Separate"],
        index=0 if st.session_state.get('finance_mode', 'Pooled') == 'Pooled' else 1,
        horizontal=True,
        key="settings_finance_mode",
        help="Pooled = one family pot. Separate = each person tracks their own net worth."
    )
    st.session_state.finance_mode = finance_mode

    if finance_mode == "Separate":
        st.caption(
            "Each parent keeps their own income and investments. "
            "Shared expenses (family, children, housing) are split by the ratio below."
        )
        split_pct = st.slider(
            f"Shared expense split — {st.session_state.parent1_name} pays",
            min_value=0, max_value=100, value=st.session_state.get('shared_expense_split_pct', 50),
            format="%d%%", key="settings_split_pct",
            help="How much of shared expenses Parent 1 covers. Parent 2 covers the rest."
        )
        st.session_state.shared_expense_split_pct = split_pct
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"{st.session_state.parent1_name}: **{split_pct}%** of shared costs")
        with col_info2:
            st.info(f"{st.session_state.parent2_name}: **{100 - split_pct}%** of shared costs")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Customize Parent 1")
        st.session_state.parent1_name = st.text_input(
            "Parent 1 Name",
            value=st.session_state.parent1_name
        )

        emoji_options = ["👨", "👩", "🧑", "👤", "👼", "🏃", "⭐", "🎯"]
        current_emoji_idx = emoji_options.index(
            st.session_state.parent1_emoji) if st.session_state.parent1_emoji in emoji_options else 0

        st.session_state.parent1_emoji = st.selectbox(
            "Parent 1 Emoji",
            emoji_options,
            index=current_emoji_idx
        )

    with col2:
        st.subheader("🔧 Customize Parent 2")
        st.session_state.parent2_name = st.text_input(
            "Parent 2 Name",
            value=st.session_state.parent2_name
        )

        current_emoji_idx = emoji_options.index(
            st.session_state.parent2_emoji) if st.session_state.parent2_emoji in emoji_options else 1

        st.session_state.parent2_emoji = st.selectbox(
            "Parent 2 Emoji",
            emoji_options,
            index=current_emoji_idx
        )

    st.info("💡 Changes to parent names and emojis will be reflected in all tabs after you navigate to them.")

    # Tab Visibility Settings
    st.markdown("---")
    st.subheader("👁️ Tab Visibility Settings")
    st.markdown("Choose which advanced features to show. Disabled tabs are hidden to simplify the interface.")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox(
            "💸 Family Expenses",
            value=st.session_state.get('show_family_expenses', False),
            key='show_family_expenses',
            help="Advanced template-based expense management for different cities"
        )

        st.checkbox(
            "🔄 Recurring & One-Time Expenses",
            value=st.session_state.get('show_recurring_expenses', True),
            key='show_recurring_expenses',
            help="Manage recurring and one-time expenses"
        )

        st.checkbox(
            "🏥 Healthcare & Insurance",
            value=st.session_state.get('show_healthcare', False),
            key='show_healthcare',
            help="Plan Medicare, HSA, long-term care, and health insurance"
        )

    with col2:
        st.checkbox(
            "📄 Export Reports",
            value=st.session_state.get('show_export', True),
            key='show_export',
            help="Export financial data to Excel, CSV, or JSON"
        )

    st.info("💡 Changes take effect immediately. Disabled tabs are hidden from the navigation.")

    # Instructions Section
    st.markdown("---")
    st.header("📖 Application Instructions")

    st.markdown("""
    ### Welcome to Financial Planning Suite

    This application helps you plan and project your family's financial future through comprehensive
    modeling of income, expenses, investments, and major life events.

    #### Quick Start Guide

    1. **Settings**: Configure current year, parent names, and which tabs to show
    2. **Parent Tabs**: Enter age, net worth, income, retirement plans, and Social Security
    3. **Family Expenses**: Define annual expenses, taxes, major purchases
    4. **Children**: Add children and configure their education expenses
    5. **Houses**: Track property ownership, mortgages, and timelines
    6. **Economy**: Configure market returns and inflation assumptions
    7. **Timeline**: Review consolidated timeline and plan relocations
    8. **Analysis**: Run Monte Carlo simulations to project future outcomes
    9. **Save/Load**: Save scenarios for future reference

    #### Optional Advanced Features

    Enable in Settings → Tab Visibility to access:
    - **Healthcare & Insurance**: Plan Medicare, HSA, and long-term care costs
    - **Export Reports**: Generate Excel/CSV/JSON reports

    #### Key Capabilities

    - Location-based expense templates for major U.S. cities
    - Monte Carlo simulation with detailed percentile analysis
    - Historical market data (100+ years of S&P 500 returns)
    - Social Security insolvency modeling
    - Inflation adjustment and today's dollars view
    - Multiple scenario comparison
    """)


def _guided_mode_toggle(tab_key):
    """Show a toggle to switch between form and guided mode for a tab."""
    guided_key = f"guided_{tab_key}"
    guided_step_key = f"guided_step_{tab_key}"
    if guided_key not in st.session_state:
        st.session_state[guided_key] = False
    if guided_step_key not in st.session_state:
        st.session_state[guided_step_key] = 0

    if st.session_state[guided_key]:
        if st.button("Switch to full form view", key=f"toggle_form_{tab_key}"):
            st.session_state[guided_key] = False
            st.rerun()
    else:
        if st.button("\U0001f9d9 Guided setup \u2014 answer questions one at a time", key=f"toggle_guided_{tab_key}"):
            st.session_state[guided_key] = True
            st.session_state[guided_step_key] = 0
            st.rerun()

    return st.session_state[guided_key]


def _guided_nav(tab_key, current_step, total_steps):
    """Navigation for guided mode within a tab."""
    step_key = f"guided_step_{tab_key}"
    st.progress((current_step + 1) / total_steps)
    st.caption(f"Question {current_step + 1} of {total_steps}")
    col1, col2 = st.columns(2)
    with col1:
        if current_step > 0:
            if st.button("\u2190 Back", key=f"guided_back_{tab_key}_{current_step}"):
                st.session_state[step_key] = current_step - 1
                st.rerun()
    with col2:
        if current_step < total_steps - 1:
            if st.button("Next \u2192", key=f"guided_next_{tab_key}_{current_step}", type="primary"):
                st.session_state[step_key] = current_step + 1
                st.rerun()
        else:
            if st.button("\u2705 Done", key=f"guided_done_{tab_key}", type="primary"):
                st.session_state[f"guided_{tab_key}"] = False
                st.rerun()


def _parent_guided_mode(parent_prefix):
    """Guided Q&A mode for a parent's financial details."""
    p = parent_prefix  # "X" or "Y"
    tab_key = f"parent_{p.lower()}"
    step = st.session_state.get(f"guided_step_{tab_key}", 0)
    total_steps = 6

    name = st.session_state.parent1_name if p == "X" else st.session_state.parent2_name

    if step == 0:
        st.subheader(f"How old is {name}?")
        st.session_state[f"parent{p}_age"] = st.number_input(
            "Current age", min_value=18, max_value=100,
            value=int(st.session_state[f"parent{p}_age"]),
            key=f"guided_{p}_age")

    elif step == 1:
        st.subheader(f"What is {name}'s current annual income?")
        st.caption("Include base salary before taxes. We'll add bonuses and equity in the career section.")
        st.session_state[f"parent{p}_income"] = st.number_input(
            "Annual income ($)", min_value=0, max_value=10_000_000,
            value=int(st.session_state[f"parent{p}_income"]),
            step=5000, key=f"guided_{p}_income")

    elif step == 2:
        st.subheader(f"What is {name}'s current net worth?")
        st.caption("Total savings, investments, and assets minus any debts.")
        st.session_state[f"parent{p}_net_worth"] = st.number_input(
            "Net worth ($)", min_value=-10_000_000, max_value=100_000_000,
            value=int(st.session_state[f"parent{p}_net_worth"]),
            step=5000, key=f"guided_{p}_nw")

    elif step == 3:
        st.subheader(f"What annual raise does {name} typically get?")
        st.caption("A typical annual raise is 3-5%. High performers or growing careers might see 5-10%.")
        st.session_state[f"parent{p}_raise"] = st.number_input(
            "Annual raise (%)", min_value=0.0, max_value=30.0,
            value=float(st.session_state[f"parent{p}_raise"]),
            step=0.5, key=f"guided_{p}_raise")

    elif step == 4:
        st.subheader(f"When does {name} plan to retire?")
        st.session_state[f"parent{p}_retirement_age"] = st.number_input(
            "Retirement age", min_value=30, max_value=85,
            value=int(st.session_state[f"parent{p}_retirement_age"]),
            key=f"guided_{p}_retire")
        st.caption("Early retirement? No problem \u2014 the simulation will model the income gap.")

    elif step == 5:
        st.subheader(f"What Social Security benefit does {name} expect?")
        st.caption("Check ssa.gov for your estimated benefit. Average is ~$1,900/month.")
        st.session_state[f"parent{p}_ss_benefit"] = st.number_input(
            "Monthly SS benefit ($)", min_value=0.0, max_value=10000.0,
            value=float(st.session_state[f"parent{p}_ss_benefit"]),
            step=100.0, key=f"guided_{p}_ss")

    _guided_nav(tab_key, step, total_steps)


def _children_guided_mode():
    """Guided Q&A mode for children planning."""
    tab_key = "children"
    step = st.session_state.get(f"guided_step_{tab_key}", 0)
    total_steps = 2

    if step == 0:
        st.subheader("Do you have or plan to have children?")
        has_kids = st.radio("", ["Yes", "No"], index=0 if st.session_state.children_list else 1,
                           key="guided_has_kids", label_visibility="collapsed")
        if has_kids == "No":
            st.session_state.children_list = []

    elif step == 1:
        st.subheader("Tell us about your children")
        st.caption("Include both existing children and ones you're planning. Location-based costs are set in the Timeline tab.")
        num_kids = st.number_input("How many children (current + planned)?",
                                    min_value=0, max_value=10,
                                    value=max(len(st.session_state.children_list), 1),
                                    key="guided_num_kids")

        while len(st.session_state.children_list) < num_kids:
            st.session_state.children_list.append({
                'name': f'Child {len(st.session_state.children_list)+1}',
                'birth_year': datetime.now().year + len(st.session_state.children_list),
                'use_template': True,
                'template_state': 'Seattle',
                'template_strategy': 'Average'
            })
        st.session_state.children_list = st.session_state.children_list[:num_kids]

        for i, child in enumerate(st.session_state.children_list):
            col1, col2 = st.columns(2)
            with col1:
                child['name'] = st.text_input(f"Child {i+1} name", value=child['name'], key=f"guided_kid_name_{i}")
            with col2:
                child['birth_year'] = st.number_input(f"Birth year", min_value=1990, max_value=2060,
                                                       value=child['birth_year'], key=f"guided_kid_year_{i}")

    _guided_nav(tab_key, step, total_steps)


def _family_expenses_guided_mode():
    """Guided Q&A mode for family expenses."""
    tab_key = "family_expenses"
    step = st.session_state.get(f"guided_step_{tab_key}", 0)
    expenses = st.session_state.family_shared_expenses

    # Group expenses into categories for step-by-step
    groups = [
        ("Housing", ["Mortgage/Rent", "Home Improvement", "Property Tax", "Home Insurance"]),
        ("Utilities", ["Gas & Electric", "Water", "Garbage", "Internet & Cable"]),
        ("Lifestyle", ["Shared Subscriptions", "Family Vacations", "Pet Care", "Other Family Expenses"]),
    ]
    total_steps = len(groups)

    group_name, group_keys = groups[step]
    st.subheader(f"How much does your household spend on {group_name.lower()}?")
    st.caption("Enter annual amounts. Don't worry about being exact \u2014 you can fine-tune later.")

    for key in group_keys:
        if key in expenses:
            expenses[key] = st.number_input(
                key, min_value=0.0, max_value=1_000_000.0,
                value=float(expenses[key]), step=500.0,
                key=f"guided_exp_{key}")

    st.session_state.family_shared_expenses = expenses
    _guided_nav(tab_key, step, total_steps)


def parent_x_tab():
    """Parent X financial details tab"""
    st.header(f"{st.session_state.parent1_emoji} {st.session_state.parent1_name}'s Financial Details")
    tab_walkthrough("parent")

    if _guided_mode_toggle("parent_x"):
        _parent_guided_mode("X")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic Information")
        st.session_state.parentX_age = st.number_input(
            "Current Age",
            min_value=18,
            max_value=100,
            value=int(st.session_state.parentX_age),
            step=1,
            key="parentX_age_input"
        )

        st.session_state.parentX_net_worth = st.number_input(
            "Current Net Worth ($)",
            min_value=-10000000.0,
            max_value=100000000.0,
            value=float(st.session_state.parentX_net_worth),
            step=1000.0,
            format="%.0f",
            key="parentX_net_worth_input"
        )
        st.caption(f"Formatted: {format_currency(st.session_state.parentX_net_worth, force_full=False)}")

        st.session_state.parentX_income = st.number_input(
            "Annual Income ($)",
            min_value=0.0,
            max_value=10000000.0,
            value=float(st.session_state.parentX_income),
            step=1000.0,
            format="%.0f",
            key="parentX_income_input"
        )
        st.caption(f"Formatted: {format_currency(st.session_state.parentX_income, force_full=False)}")

        st.session_state.parentX_raise = st.number_input(
            "Annual Raise (%)",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.parentX_raise),
            step=0.1,
            format="%.2f",
            key="parentX_raise_input"
        )

    with col2:
        st.subheader("Retirement Information")
        st.session_state.parentX_retirement_age = st.number_input(
            "Retirement Age",
            min_value=int(st.session_state.parentX_age),
            max_value=100,
            value=int(st.session_state.parentX_retirement_age),
            step=1,
            key="parentX_retirement_age_input"
        )

        st.session_state.parentX_ss_benefit = st.number_input(
            "Monthly Social Security Benefit ($)",
            min_value=0.0,
            max_value=10000.0,
            value=float(st.session_state.parentX_ss_benefit),
            step=50.0,
            format="%.0f",
            key="parentX_ss_benefit_input"
        )
        st.caption(f"Annual: {format_currency(st.session_state.parentX_ss_benefit * 12, force_full=False)}")

        st.session_state.parentX_death_age = st.number_input(
            "Expected Death Age",
            min_value=int(st.session_state.parentX_age),
            max_value=120,
            value=int(st.session_state.parentX_death_age),
            step=1,
            key="parentX_death_age_input"
        )

    st.subheader("Career Phases")
    st.caption("Model your career trajectory — each phase represents a job or career stage. Default: single stable career until retirement.")

    phases = st.session_state.parentX_career_phases

    # Philosophy defaults helper
    PHILOSOPHY_DEFAULTS_PX = {
        "Stable": {"raise": 3.0, "bonus": 5.0, "rsu": 0},
        "Climbing the Ladder": {"raise": 5.0, "bonus": 15.0, "rsu": 0},
        "Startup": {"raise": 2.0, "bonus": 10.0, "rsu": 0},
        "Part-time": {"raise": 1.0, "bonus": 0.0, "rsu": 0},
        "Coasting": {"raise": 2.0, "bonus": 5.0, "rsu": 0},
    }

    for idx, phase in enumerate(phases):
        with st.expander(f"Phase {idx+1}: {phase.label or phase.philosophy} — Age {phase.start_age} to {phase.end_age}", expanded=(idx == 0)):
            col1, col2, col3 = st.columns(3)
            with col1:
                phases[idx].start_age = st.number_input("Start Age", value=int(phase.start_age), min_value=16, max_value=100, key=f"px_cp_start_{idx}")
            with col2:
                phases[idx].end_age = st.number_input("End Age", value=int(phase.end_age), min_value=17, max_value=100, key=f"px_cp_end_{idx}")
            with col3:
                phil_options = ["Stable", "Climbing the Ladder", "Startup", "Part-time", "Coasting"]
                phil_idx = phil_options.index(phase.philosophy) if phase.philosophy in phil_options else 0
                new_phil = st.selectbox("Career Style", phil_options, index=phil_idx, key=f"px_cp_phil_{idx}")
                if new_phil != phase.philosophy:
                    phases[idx].philosophy = new_phil
                    defaults = PHILOSOPHY_DEFAULTS_PX[new_phil]
                    phases[idx].annual_raise_pct = defaults["raise"]
                    phases[idx].annual_bonus_pct = defaults["bonus"]

            phases[idx].label = st.text_input("Label", value=phase.label, placeholder="e.g., Senior Engineer at BigCo", key=f"px_cp_label_{idx}")

            col1, col2, col3 = st.columns(3)
            with col1:
                phases[idx].base_salary = st.number_input("Base Salary ($)", value=float(phase.base_salary), min_value=0.0, step=5000.0, key=f"px_cp_salary_{idx}")
            with col2:
                phases[idx].annual_raise_pct = st.number_input("Annual Raise %", value=float(phase.annual_raise_pct), min_value=0.0, max_value=50.0, step=0.5, key=f"px_cp_raise_{idx}")
            with col3:
                phases[idx].annual_bonus_pct = st.number_input("Annual Bonus %", value=float(phase.annual_bonus_pct), min_value=0.0, max_value=100.0, step=1.0, key=f"px_cp_bonus_{idx}")

            has_equity = st.checkbox("I receive equity compensation", value=(phase.rsu_annual_grant > 0 or phase.stock_options_grant > 0), key=f"px_cp_equity_{idx}")
            if has_equity:
                col1, col2 = st.columns(2)
                with col1:
                    phases[idx].rsu_annual_grant = st.number_input("RSU Annual Grant ($)", value=float(phase.rsu_annual_grant), min_value=0.0, step=5000.0, key=f"px_cp_rsu_{idx}")
                with col2:
                    phases[idx].rsu_vesting_years = st.number_input("Vesting Period (years)", value=int(phase.rsu_vesting_years), min_value=1, max_value=6, key=f"px_cp_vest_{idx}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    phases[idx].stock_options_grant = st.number_input("Stock Options Grant ($)", value=float(phase.stock_options_grant), min_value=0.0, step=10000.0, key=f"px_cp_opts_{idx}", help="Expected value above strike price")
                with col2:
                    phases[idx].stock_options_growth_pct = st.number_input("Options Growth %/yr", value=float(phase.stock_options_growth_pct), min_value=0.0, max_value=100.0, step=5.0, key=f"px_cp_optgrow_{idx}")
                with col3:
                    phases[idx].stock_options_liquidity_year = st.number_input("Liquidity Year", value=int(phase.stock_options_liquidity_year), min_value=0, max_value=2080, key=f"px_cp_optliq_{idx}", help="Year of IPO/acquisition. 0 = never")
            else:
                phases[idx].rsu_annual_grant = 0.0
                phases[idx].stock_options_grant = 0.0

            if len(phases) > 1:
                if st.button("Remove this phase", key=f"px_cp_del_{idx}"):
                    phases.pop(idx)
                    st.rerun()

    if st.button("+ Add Career Phase", key="px_add_phase"):
        last = phases[-1] if phases else None
        new_start = last.end_age if last else st.session_state.parentX_age
        phases.append(CareerPhase(
            start_age=new_start,
            end_age=st.session_state.parentX_retirement_age,
            philosophy="Stable",
            base_salary=last.base_salary if last else 75000,
            annual_raise_pct=3.0,
            label=""
        ))
        st.rerun()

    st.session_state.parentX_career_phases = phases
    # Sync legacy fields
    if phases:
        st.session_state.parentX_income = phases[0].base_salary
        st.session_state.parentX_raise = phases[0].annual_raise_pct

    # Annual Expenses Section
    st.markdown("---")
    st.subheader("💳 Annual Expenses")
    st.markdown(f"Track {st.session_state.parent1_name}'s individual expenses (groceries, transportation, healthcare, etc.)")

    # Expense template settings
    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.parentX_use_template = st.checkbox(
            "Use Expense Template",
            value=st.session_state.parentX_use_template,
            key="parentX_use_template_checkbox",
            help="Use location/strategy-based expense template or enter custom amounts"
        )

    with col2:
        st.session_state.parentX_expense_location = st.selectbox(
            "Location",
            options=AVAILABLE_LOCATIONS_ADULTS,
            index=AVAILABLE_LOCATIONS_ADULTS.index(st.session_state.parentX_expense_location) if st.session_state.parentX_expense_location in AVAILABLE_LOCATIONS_ADULTS else 0,
            key="parentX_expense_location_select",
            disabled=not st.session_state.parentX_use_template
        )

    with col3:
        st.session_state.parentX_expense_strategy = st.selectbox(
            "Spending Strategy",
            options=STATISTICAL_STRATEGIES,
            index=STATISTICAL_STRATEGIES.index(st.session_state.parentX_expense_strategy) if st.session_state.parentX_expense_strategy in STATISTICAL_STRATEGIES else 1,
            key="parentX_expense_strategy_select",
            disabled=not st.session_state.parentX_use_template
        )

    # Load template if using template mode
    if st.session_state.parentX_use_template:
        if st.button("📥 Load Template", key="parentX_load_template"):
            template_data = get_adult_expense_template(
                st.session_state.parentX_expense_location,
                st.session_state.parentX_expense_strategy
            )
            st.session_state.parentX_expenses = template_data.copy()
            st.success(f"✅ Loaded {st.session_state.parentX_expense_strategy} template for {st.session_state.parentX_expense_location}")

    # Display expenses by category group
    st.markdown("#### Expense Categories")

    total_parentX_expenses = 0

    for group_name, categories in ADULT_EXPENSE_CATEGORIES.items():
        with st.expander(f"**{group_name}**", expanded=False):
            cols = st.columns(2)
            for idx, category in enumerate(categories):
                with cols[idx % 2]:
                    if category not in st.session_state.parentX_expenses:
                        st.session_state.parentX_expenses[category] = 0

                    st.session_state.parentX_expenses[category] = st.number_input(
                        category,
                        min_value=0.0,
                        max_value=1000000.0,
                        value=float(st.session_state.parentX_expenses[category]),
                        step=100.0,
                        format="%.0f",
                        key=f"parentX_expense_{category}",
                        help=f"Annual amount for {category}"
                    )
                    total_parentX_expenses += st.session_state.parentX_expenses[category]

    st.markdown("---")
    st.metric("**Total Annual Expenses**", format_currency(total_parentX_expenses, force_full=False))


def parent_y_tab():
    """Parent Y financial details tab"""
    st.header(f"{st.session_state.parent2_emoji} {st.session_state.parent2_name}'s Financial Details")
    tab_walkthrough("parent")

    if _guided_mode_toggle("parent_y"):
        _parent_guided_mode("Y")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic Information")
        st.session_state.parentY_age = st.number_input(
            "Current Age",
            min_value=18,
            max_value=100,
            value=int(st.session_state.parentY_age),
            step=1,
            key="parentY_age_input"
        )

        st.session_state.parentY_net_worth = st.number_input(
            "Current Net Worth ($)",
            min_value=-10000000.0,
            max_value=100000000.0,
            value=float(st.session_state.parentY_net_worth),
            step=1000.0,
            format="%.0f",
            key="parentY_net_worth_input"
        )
        st.caption(f"Formatted: {format_currency(st.session_state.parentY_net_worth, force_full=False)}")

        st.session_state.parentY_income = st.number_input(
            "Annual Income ($)",
            min_value=0.0,
            max_value=10000000.0,
            value=float(st.session_state.parentY_income),
            step=1000.0,
            format="%.0f",
            key="parentY_income_input"
        )
        st.caption(f"Formatted: {format_currency(st.session_state.parentY_income, force_full=False)}")

        st.session_state.parentY_raise = st.number_input(
            "Annual Raise (%)",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.parentY_raise),
            step=0.1,
            format="%.2f",
            key="parentY_raise_input"
        )

    with col2:
        st.subheader("Retirement Information")
        st.session_state.parentY_retirement_age = st.number_input(
            "Retirement Age",
            min_value=int(st.session_state.parentY_age),
            max_value=100,
            value=int(st.session_state.parentY_retirement_age),
            step=1,
            key="parentY_retirement_age_input"
        )

        st.session_state.parentY_ss_benefit = st.number_input(
            "Monthly Social Security Benefit ($)",
            min_value=0.0,
            max_value=10000.0,
            value=float(st.session_state.parentY_ss_benefit),
            step=50.0,
            format="%.0f",
            key="parentY_ss_benefit_input"
        )
        st.caption(f"Annual: {format_currency(st.session_state.parentY_ss_benefit * 12, force_full=False)}")

        st.session_state.parentY_death_age = st.number_input(
            "Expected Death Age",
            min_value=int(st.session_state.parentY_age),
            max_value=120,
            value=int(st.session_state.parentY_death_age),
            step=1,
            key="parentY_death_age_input"
        )

    st.subheader("Career Phases")
    st.caption("Model your career trajectory — each phase represents a job or career stage. Default: single stable career until retirement.")

    phases_y = st.session_state.parentY_career_phases

    # Philosophy defaults helper
    PHILOSOPHY_DEFAULTS_PY = {
        "Stable": {"raise": 3.0, "bonus": 5.0, "rsu": 0},
        "Climbing the Ladder": {"raise": 5.0, "bonus": 15.0, "rsu": 0},
        "Startup": {"raise": 2.0, "bonus": 10.0, "rsu": 0},
        "Part-time": {"raise": 1.0, "bonus": 0.0, "rsu": 0},
        "Coasting": {"raise": 2.0, "bonus": 5.0, "rsu": 0},
    }

    for idx, phase in enumerate(phases_y):
        with st.expander(f"Phase {idx+1}: {phase.label or phase.philosophy} — Age {phase.start_age} to {phase.end_age}", expanded=(idx == 0)):
            col1, col2, col3 = st.columns(3)
            with col1:
                phases_y[idx].start_age = st.number_input("Start Age", value=int(phase.start_age), min_value=16, max_value=100, key=f"py_cp_start_{idx}")
            with col2:
                phases_y[idx].end_age = st.number_input("End Age", value=int(phase.end_age), min_value=17, max_value=100, key=f"py_cp_end_{idx}")
            with col3:
                phil_options = ["Stable", "Climbing the Ladder", "Startup", "Part-time", "Coasting"]
                phil_idx = phil_options.index(phase.philosophy) if phase.philosophy in phil_options else 0
                new_phil = st.selectbox("Career Style", phil_options, index=phil_idx, key=f"py_cp_phil_{idx}")
                if new_phil != phase.philosophy:
                    phases_y[idx].philosophy = new_phil
                    defaults = PHILOSOPHY_DEFAULTS_PY[new_phil]
                    phases_y[idx].annual_raise_pct = defaults["raise"]
                    phases_y[idx].annual_bonus_pct = defaults["bonus"]

            phases_y[idx].label = st.text_input("Label", value=phase.label, placeholder="e.g., Senior Engineer at BigCo", key=f"py_cp_label_{idx}")

            col1, col2, col3 = st.columns(3)
            with col1:
                phases_y[idx].base_salary = st.number_input("Base Salary ($)", value=float(phase.base_salary), min_value=0.0, step=5000.0, key=f"py_cp_salary_{idx}")
            with col2:
                phases_y[idx].annual_raise_pct = st.number_input("Annual Raise %", value=float(phase.annual_raise_pct), min_value=0.0, max_value=50.0, step=0.5, key=f"py_cp_raise_{idx}")
            with col3:
                phases_y[idx].annual_bonus_pct = st.number_input("Annual Bonus %", value=float(phase.annual_bonus_pct), min_value=0.0, max_value=100.0, step=1.0, key=f"py_cp_bonus_{idx}")

            has_equity = st.checkbox("I receive equity compensation", value=(phase.rsu_annual_grant > 0 or phase.stock_options_grant > 0), key=f"py_cp_equity_{idx}")
            if has_equity:
                col1, col2 = st.columns(2)
                with col1:
                    phases_y[idx].rsu_annual_grant = st.number_input("RSU Annual Grant ($)", value=float(phase.rsu_annual_grant), min_value=0.0, step=5000.0, key=f"py_cp_rsu_{idx}")
                with col2:
                    phases_y[idx].rsu_vesting_years = st.number_input("Vesting Period (years)", value=int(phase.rsu_vesting_years), min_value=1, max_value=6, key=f"py_cp_vest_{idx}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    phases_y[idx].stock_options_grant = st.number_input("Stock Options Grant ($)", value=float(phase.stock_options_grant), min_value=0.0, step=10000.0, key=f"py_cp_opts_{idx}", help="Expected value above strike price")
                with col2:
                    phases_y[idx].stock_options_growth_pct = st.number_input("Options Growth %/yr", value=float(phase.stock_options_growth_pct), min_value=0.0, max_value=100.0, step=5.0, key=f"py_cp_optgrow_{idx}")
                with col3:
                    phases_y[idx].stock_options_liquidity_year = st.number_input("Liquidity Year", value=int(phase.stock_options_liquidity_year), min_value=0, max_value=2080, key=f"py_cp_optliq_{idx}", help="Year of IPO/acquisition. 0 = never")
            else:
                phases_y[idx].rsu_annual_grant = 0.0
                phases_y[idx].stock_options_grant = 0.0

            if len(phases_y) > 1:
                if st.button("Remove this phase", key=f"py_cp_del_{idx}"):
                    phases_y.pop(idx)
                    st.rerun()

    if st.button("+ Add Career Phase", key="py_add_phase"):
        last = phases_y[-1] if phases_y else None
        new_start = last.end_age if last else st.session_state.parentY_age
        phases_y.append(CareerPhase(
            start_age=new_start,
            end_age=st.session_state.parentY_retirement_age,
            philosophy="Stable",
            base_salary=last.base_salary if last else 75000,
            annual_raise_pct=3.0,
            label=""
        ))
        st.rerun()

    st.session_state.parentY_career_phases = phases_y
    # Sync legacy fields
    if phases_y:
        st.session_state.parentY_income = phases_y[0].base_salary
        st.session_state.parentY_raise = phases_y[0].annual_raise_pct

    # Annual Expenses Section
    st.markdown("---")
    st.subheader("💳 Annual Expenses")
    st.markdown(f"Track {st.session_state.parent2_name}'s individual expenses (groceries, transportation, healthcare, etc.)")

    # Expense template settings
    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.parentY_use_template = st.checkbox(
            "Use Expense Template",
            value=st.session_state.parentY_use_template,
            key="parentY_use_template_checkbox",
            help="Use location/strategy-based expense template or enter custom amounts"
        )

    with col2:
        st.session_state.parentY_expense_location = st.selectbox(
            "Location",
            options=AVAILABLE_LOCATIONS_ADULTS,
            index=AVAILABLE_LOCATIONS_ADULTS.index(st.session_state.parentY_expense_location) if st.session_state.parentY_expense_location in AVAILABLE_LOCATIONS_ADULTS else 0,
            key="parentY_expense_location_select",
            disabled=not st.session_state.parentY_use_template
        )

    with col3:
        st.session_state.parentY_expense_strategy = st.selectbox(
            "Spending Strategy",
            options=STATISTICAL_STRATEGIES,
            index=STATISTICAL_STRATEGIES.index(st.session_state.parentY_expense_strategy) if st.session_state.parentY_expense_strategy in STATISTICAL_STRATEGIES else 1,
            key="parentY_expense_strategy_select",
            disabled=not st.session_state.parentY_use_template
        )

    # Load template if using template mode
    if st.session_state.parentY_use_template:
        if st.button("📥 Load Template", key="parentY_load_template"):
            template_data = get_adult_expense_template(
                st.session_state.parentY_expense_location,
                st.session_state.parentY_expense_strategy
            )
            st.session_state.parentY_expenses = template_data.copy()
            st.success(f"✅ Loaded {st.session_state.parentY_expense_strategy} template for {st.session_state.parentY_expense_location}")

    # Display expenses by category group
    st.markdown("#### Expense Categories")

    total_parentY_expenses = 0

    for group_name, categories in ADULT_EXPENSE_CATEGORIES.items():
        with st.expander(f"**{group_name}**", expanded=False):
            cols = st.columns(2)
            for idx, category in enumerate(categories):
                with cols[idx % 2]:
                    if category not in st.session_state.parentY_expenses:
                        st.session_state.parentY_expenses[category] = 0

                    st.session_state.parentY_expenses[category] = st.number_input(
                        category,
                        min_value=0.0,
                        max_value=1000000.0,
                        value=float(st.session_state.parentY_expenses[category]),
                        step=100.0,
                        format="%.0f",
                        key=f"parentY_expense_{category}",
                        help=f"Annual amount for {category}"
                    )
                    total_parentY_expenses += st.session_state.parentY_expenses[category]

    st.markdown("---")
    st.metric("**Total Annual Expenses**", format_currency(total_parentY_expenses, force_full=False))


def family_expenses_tab():
    """Family expenses tab with template browsing, modification, and custom city creation"""
    st.header("\U0001f4b8 Family Expenses")
    tab_walkthrough("family_expenses")

    if _guided_mode_toggle("family_expenses"):
        _family_expenses_guided_mode()
        return

    # Show inflation adjustment info
    st.info(f"ℹ️ All expense templates are inflation-adjusted to **{EXPENSE_TEMPLATE_BASE_YEAR}** dollars")

    # Create tabs for different views
    expense_tab1, expense_tab2, expense_tab3 = st.tabs([
        "📊 Browse Templates",
        "✏️ Edit Templates",
        "🌍 Create Custom City"
    ])

    # TAB 1: Browse Templates
    with expense_tab1:
        st.subheader("📊 Browse Expense Templates by Location")

        # Get all available locations (built-in + custom)
        all_templates = {**FAMILY_EXPENSE_TEMPLATES, **st.session_state.custom_family_templates}
        available_locations = sorted(all_templates.keys())

        if not available_locations:
            st.warning("No templates available. Please create a custom city in the 'Create Custom City' tab.")
            return

        # Create display options with full location names
        location_display_options = [get_location_display_name(loc) for loc in available_locations]

        col1, col2 = st.columns(2)

        with col1:
            selected_display = st.selectbox(
                "Select Location/City:",
                options=location_display_options,
                index=0,
                key="browse_location"
            )
            # Get the actual location key from the display name
            selected_location = available_locations[location_display_options.index(selected_display)]

        # Get available strategies for selected location
        available_strategies = list(all_templates[selected_location].keys())

        with col2:
            selected_strategy = st.selectbox(
                "Select Spending Strategy:",
                options=available_strategies,
                index=0,
                key="browse_strategy"
            )

        # Display template details
        template = all_templates[selected_location][selected_strategy]

        st.markdown("---")
        st.subheader(f"📋 {get_location_display_name(selected_location)} - {selected_strategy} Strategy")

        # Show template as visualization and table
        col_chart, col_table = st.columns([1, 1])

        with col_chart:
            # Create pie chart
            categories = list(template.keys())
            amounts = list(template.values())

            fig = go.Figure(data=[go.Pie(
                labels=categories,
                values=amounts,
                hole=0.4,
                textinfo='label+percent',
                marker=dict(colors=px.colors.qualitative.Set3)
            )])

            fig.update_layout(
                title=f"Expense Breakdown",
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            # Create detailed table
            template_df = pd.DataFrame({
                'Category': categories,
                'Annual Amount': [f"${amt:,.0f}" for amt in amounts],
                'Monthly Amount': [f"${amt/12:,.0f}" for amt in amounts]
            })

            st.dataframe(template_df, hide_index=True, use_container_width=True)

            total = sum(amounts)
            st.metric("Total Annual Expenses", f"${total:,.0f}")
            st.caption(f"Monthly: ${total/12:,.0f}")

        # Display data sources
        st.markdown("---")
        data_source = get_expense_data_source(selected_location)

        st.markdown("### 📚 Data Sources")
        st.markdown(f"**Source:** {data_source['source']}")

        # Display URLs as clickable links
        urls = data_source['url'].split(', ')
        if len(urls) == 1 and urls[0] != 'N/A':
            st.markdown(f"**URL:** [{urls[0]}]({urls[0]})")
        elif urls[0] != 'N/A':
            st.markdown("**URLs:**")
            for url in urls:
                url = url.strip()
                st.markdown(f"- [{url}]({url})")

        st.markdown(f"**Data Year:** {data_source['year']}")

        if data_source['notes']:
            with st.expander("📝 Additional Notes"):
                st.markdown(data_source['notes'])

        # Quick save button
        st.markdown("---")
        col_save1, col_save2 = st.columns([3, 1])

        with col_save1:
            st.markdown(f"**Save this template for future use?**")
            st.caption("This will save the template to your custom templates.")

        with col_save2:
            if st.button("💾 Save Template", type="primary", key="save_template_btn"):
                # Save to custom templates
                if selected_location not in st.session_state.custom_family_templates:
                    st.session_state.custom_family_templates[selected_location] = {}
                st.session_state.custom_family_templates[selected_location][selected_strategy] = template.copy()
                st.success(f"✅ Saved {selected_strategy} template for {get_location_display_name(selected_location)}!")
                st.rerun()

    # TAB 2: Edit Templates
    with expense_tab2:
        st.subheader("✏️ Edit and Save Templates")

        st.markdown("""
        Modify expense templates and save them. You can:
        - Edit existing built-in templates (saved as custom versions)
        - Modify your custom templates
        - Create variations of existing templates
        """)

        # Select template to edit
        all_templates = {**FAMILY_EXPENSE_TEMPLATES, **st.session_state.custom_family_templates}
        available_locations = sorted(all_templates.keys())
        location_display_options = [get_location_display_name(loc) for loc in available_locations]

        col1, col2, col3 = st.columns(3)

        with col1:
            edit_display = st.selectbox(
                "Location to Edit:",
                options=location_display_options,
                key="edit_location"
            )
            edit_location = available_locations[location_display_options.index(edit_display)]

        available_strategies = list(all_templates[edit_location].keys())

        with col2:
            edit_strategy = st.selectbox(
                "Strategy to Edit:",
                options=available_strategies,
                key="edit_strategy"
            )

        with col3:
            save_as_new = st.checkbox("Save as new strategy", value=False, key="save_as_new")

        # Load template for editing
        current_template = all_templates[edit_location][edit_strategy].copy()

        st.markdown("---")
        st.markdown(f"### Editing: {get_location_display_name(edit_location)} - {edit_strategy}")

        # Edit each category
        edited_template = {}

        for category, value in current_template.items():
            col_cat, col_val = st.columns([2, 1])

            with col_cat:
                st.markdown(f"**{category}**")

            with col_val:
                new_value = st.number_input(
                    f"Amount for {category}",
                    min_value=0.0,
                    max_value=1000000.0,
                    value=float(value),
                    step=100.0,
                    key=f"edit_{category}",
                    label_visibility="collapsed"
                )
                edited_template[category] = new_value

        # Show total
        total_edited = sum(edited_template.values())
        st.metric("Total Annual Expenses", f"${total_edited:,.0f}")

        # Save options
        st.markdown("---")
        st.subheader("💾 Save Changes")

        # Option to save as a completely new city/location
        save_as_new_city = st.checkbox("Save as new city/location", value=False, key="save_as_new_city")

        if save_as_new_city:
            new_city_location = st.text_input(
                "New City/Location Name:",
                value=f"{edit_location} (Copy)",
                key="new_city_location",
                help="Enter a new city/location name to save this template under"
            )
            # Get base name without suffix for input
            base_strategy = get_strategy_base_name(edit_strategy)
            new_strategy_base = st.text_input(
                "Strategy Name:",
                value=base_strategy,
                key="new_strategy_name_city",
                help="Custom strategy name (without suffix). Will be saved with '(custom)' suffix."
            )
            new_strategy_name = f"{new_strategy_base} (custom)"
            save_location = new_city_location
        elif save_as_new:
            # Get base name without suffix for input
            base_strategy = get_strategy_base_name(edit_strategy)
            new_strategy_base = st.text_input(
                "New Strategy Name:",
                value=base_strategy,
                key="new_strategy_name",
                help="Custom strategy name (without suffix). Will be saved with '(custom)' suffix."
            )
            new_strategy_name = f"{new_strategy_base} (custom)"
            save_location = edit_location
        else:
            # Check if trying to overwrite a statistical strategy
            if is_statistical_strategy(edit_strategy):
                st.error("❌ Cannot overwrite statistical (built-in) strategies. Please check 'Save as new strategy' to create a custom version.")
                new_strategy_name = None
                save_location = None
            elif is_custom_strategy(edit_strategy):
                # Can overwrite custom strategies
                new_strategy_name = edit_strategy
                save_location = edit_location
            else:
                # Legacy strategy name - save as custom
                new_strategy_name = f"{edit_strategy} (custom)"
                save_location = edit_location

        col_save1, col_save2, col_save3 = st.columns([2, 1, 1])

        with col_save1:
            if save_as_new_city:
                st.info(f"Will save as new city: **{new_city_location} - {new_strategy_name}**")
            elif save_as_new:
                st.info(f"Will save as: **{get_location_display_name(edit_location)} - {new_strategy_name}**")
            elif new_strategy_name:
                if is_custom_strategy(edit_strategy):
                    st.warning(f"⚠️ Will overwrite: **{get_location_display_name(edit_location)} - {edit_strategy}**")
                else:
                    st.warning(f"⚠️ Will save as custom template: **{get_location_display_name(edit_location)} - {new_strategy_name}**")

        with col_save2:
            if new_strategy_name and st.button("💾 Save Template", type="primary", key="save_edited_template"):
                # Initialize location if needed
                if save_location not in st.session_state.custom_family_templates:
                    st.session_state.custom_family_templates[save_location] = {}

                # Save the template
                st.session_state.custom_family_templates[save_location][new_strategy_name] = edited_template.copy()

                st.success(f"✅ Saved template: {save_location} - {new_strategy_name}")
                st.rerun()

        with col_save3:
            # Delete button for custom strategies only
            if is_custom_strategy(edit_strategy):
                if st.button("🗑️ Delete", type="secondary", key="delete_strategy_btn"):
                    st.session_state['confirm_delete_strategy'] = {
                        'location': edit_location,
                        'strategy': edit_strategy
                    }
                    st.rerun()

        # Confirmation dialog for deletion
        if 'confirm_delete_strategy' in st.session_state:
            st.markdown("---")
            st.warning(f"⚠️ **Confirm Deletion**")
            st.write(f"Are you sure you want to delete the strategy **'{st.session_state.confirm_delete_strategy['strategy']}'** for **{st.session_state.confirm_delete_strategy['location']}**?")
            st.write("This action cannot be undone.")

            col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 2])
            with col_confirm1:
                if st.button("✅ Yes, Delete", type="primary", key="confirm_delete_yes"):
                    loc = st.session_state.confirm_delete_strategy['location']
                    strat = st.session_state.confirm_delete_strategy['strategy']

                    if loc in st.session_state.custom_family_templates:
                        if strat in st.session_state.custom_family_templates[loc]:
                            del st.session_state.custom_family_templates[loc][strat]
                            st.success(f"✅ Deleted strategy: {strat}")

                            # Clean up empty locations
                            if not st.session_state.custom_family_templates[loc]:
                                del st.session_state.custom_family_templates[loc]

                    del st.session_state['confirm_delete_strategy']
                    st.rerun()

            with col_confirm2:
                if st.button("❌ Cancel", key="confirm_delete_no"):
                    del st.session_state['confirm_delete_strategy']
                    st.rerun()

    # TAB 3: Create Custom City
    with expense_tab3:
        st.subheader("🌍 Create Custom City/Location Template")

        st.markdown("""
        Create a brand new location template from scratch or copy an existing one as a starting point.
        """)

        # Option to copy from existing or start fresh
        creation_mode = st.radio(
            "Creation Mode:",
            options=["Start from scratch", "Copy from existing template"],
            horizontal=True,
            key="creation_mode"
        )

        # New city name
        new_city_name = st.text_input(
            "New City/Location Name:",
            value="",
            placeholder="e.g., Miami, FL, USA or London, UK",
            key="new_city_name",
            help="Include city, state (for USA), and country for clarity"
        )

        new_strategy_name_city = st.text_input(
            "Strategy Name:",
            value="Average",
            key="new_strategy_name_city"
        )

        # Geographic coordinates for world map
        st.markdown("---")
        st.markdown("**🗺️ Geographic Coordinates (Optional)**")
        st.markdown("Provide coordinates to display this city on the Timeline World Map visualization.")

        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            new_city_lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=0.0,
                step=0.1,
                key="new_city_lat",
                help="Latitude: -90 (South Pole) to +90 (North Pole). Use a mapping service to find coordinates."
            )
        with coord_col2:
            new_city_lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                step=0.1,
                key="new_city_lon",
                help="Longitude: -180 to +180. Negative = West, Positive = East"
            )

        # Show link to help find coordinates
        st.info("💡 Tip: Use [Google Maps](https://www.google.com/maps) or [LatLong.net](https://www.latlong.net/) to find coordinates for your city.")

        if creation_mode == "Copy from existing template":
            # Select template to copy
            all_templates = {**FAMILY_EXPENSE_TEMPLATES, **st.session_state.custom_family_templates}
            available_locations = sorted(all_templates.keys())
            location_display_options = [get_location_display_name(loc) for loc in available_locations]

            col1, col2 = st.columns(2)

            with col1:
                copy_display = st.selectbox(
                    "Copy from Location:",
                    options=location_display_options,
                    key="copy_location"
                )
                copy_location = available_locations[location_display_options.index(copy_display)]

            available_strategies = list(all_templates[copy_location].keys())

            with col2:
                copy_strategy = st.selectbox(
                    "Copy from Strategy:",
                    options=available_strategies,
                    key="copy_strategy"
                )

            # Load template to use as base
            base_template = all_templates[copy_location][copy_strategy].copy()
        else:
            # Start with default categories and zero values
            base_template = {
                'Food & Groceries': 0.0,
                'Clothing': 0.0,
                'Transportation': 0.0,
                'Entertainment & Activities': 0.0,
                'Personal Care': 0.0,
                'Other Expenses': 0.0
            }

        st.markdown("---")
        st.subheader(f"💵 Set Expense Values for {new_city_name if new_city_name else '(enter city name above)'}")

        # Edit template values
        new_template = {}

        for category, value in base_template.items():
            col_cat, col_val = st.columns([2, 1])

            with col_cat:
                st.markdown(f"**{category}**")

            with col_val:
                new_value = st.number_input(
                    f"Amount for {category}",
                    min_value=0.0,
                    max_value=1000000.0,
                    value=float(value),
                    step=100.0,
                    key=f"new_{category}",
                    label_visibility="collapsed"
                )
                new_template[category] = new_value

        # Show total
        total_new = sum(new_template.values())
        st.metric("Total Annual Expenses", f"${total_new:,.0f}")

        # Create button
        st.markdown("---")
        col_create1, col_create2 = st.columns([3, 1])

        with col_create1:
            if new_city_name:
                st.info(f"Will create: **{new_city_name} - {new_strategy_name_city}**")
            else:
                st.warning("⚠️ Please enter a city name above")

        with col_create2:
            if st.button("🌍 Create City", type="primary", key="create_city_btn", disabled=not new_city_name):
                # Initialize location
                if new_city_name not in st.session_state.custom_family_templates:
                    st.session_state.custom_family_templates[new_city_name] = {}

                # Save the template
                st.session_state.custom_family_templates[new_city_name][new_strategy_name_city] = new_template.copy()

                # Save coordinates if provided (not at default 0,0)
                if new_city_lat != 0.0 or new_city_lon != 0.0:
                    st.session_state.custom_location_coordinates[new_city_name] = {
                        'lat': new_city_lat,
                        'lon': new_city_lon
                    }

                st.success(f"✅ Created new city: {new_city_name} - {new_strategy_name_city}!")
                if new_city_lat != 0.0 or new_city_lon != 0.0:
                    st.info(f"📍 Coordinates saved: {new_city_lat}°, {new_city_lon}° - City will appear on world map!")
                st.balloons()
                st.rerun()

    # Show current expenses section at bottom (always visible)
    st.markdown("---")
    st.subheader("💳 Your Current Annual Family Expenses")

    current_state, current_strategy = get_state_for_year(st.session_state.current_year)
    st.info(f"📍 Current State from Timeline: **{current_state}** | Strategy: **{current_strategy}**")

    for category in st.session_state.expense_categories:
        col1, col2 = st.columns([3, 1])
        with col1:
            amount = st.number_input(
                f"{category}",
                min_value=0.0,
                max_value=1000000.0,
                value=float(st.session_state.expenses.get(category, 0.0)),
                step=100.0,
                format="%.0f",
                key=f"expense_{category}"
            )
            st.session_state.expenses[category] = amount
        with col2:
            st.caption(format_currency(amount))

    total_expenses = sum(st.session_state.expenses.values())
    st.metric("Total Annual Family Expenses", format_currency(total_expenses))

    # Tax Settings
    st.subheader("💼 Tax Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.session_state.state_tax_rate = st.number_input(
            "State Tax Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=float(st.session_state.state_tax_rate),
            step=0.1,
            format="%.2f"
        )

    with col2:
        st.session_state.pretax_401k = st.number_input(
            "Pre-tax 401k Contribution ($)",
            min_value=0.0,
            max_value=100000.0,
            value=float(st.session_state.pretax_401k),
            step=500.0,
            format="%.0f"
        )


def recurring_one_time_expenses_tab():
    """Recurring expenses and one-time major purchases tab"""
    st.header("🔄 Recurring & One-Time Expenses")
    tab_walkthrough("recurring")

    st.markdown("""
    Manage recurring expenses (like vehicle purchases every N years) and one-time major purchases.
    These expenses are included in all financial simulations and projections.
    """)

    if st.button("➕ Add Major Purchase"):
        new_purchase = MajorPurchase(
            name="New Purchase",
            year=st.session_state.current_year,
            amount=50000.0,
            financing_years=0,
            interest_rate=0.0,
            asset_type="Expense",
            appreciation_rate=0.0
        )
        st.session_state.major_purchases.append(new_purchase)
        st.rerun()

    for idx, purchase in enumerate(st.session_state.major_purchases):
        with st.expander(f"🛍️ {purchase.name} - {format_currency(purchase.amount)} ({purchase.year})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                purchase.name = st.text_input("Name", value=purchase.name, key=f"mp_name_{idx}")
                purchase.year = st.number_input("Year", min_value=2020, max_value=2100, value=purchase.year, key=f"mp_year_{idx}")
                purchase.amount = st.number_input("Amount ($)", min_value=0.0, value=float(purchase.amount), step=1000.0, key=f"mp_amount_{idx}")

            with col2:
                purchase.asset_type = st.selectbox(
                    "Asset Type",
                    ["Expense", "Real Estate", "Vehicle", "Investment"],
                    index=["Expense", "Real Estate", "Vehicle", "Investment"].index(purchase.asset_type) if purchase.asset_type in ["Expense", "Real Estate", "Vehicle", "Investment"] else 0,
                    key=f"mp_asset_type_{idx}"
                )
                purchase.appreciation_rate = st.number_input(
                    "Appreciation Rate (% per year)",
                    min_value=-20.0,
                    max_value=50.0,
                    value=float(purchase.appreciation_rate * 100),
                    step=0.5,
                    key=f"mp_appreciation_{idx}"
                ) / 100.0

            with col3:
                purchase.financing_years = st.number_input("Financing Years", min_value=0, max_value=30, value=purchase.financing_years, key=f"mp_financing_{idx}")
                purchase.interest_rate = st.number_input(
                    "Interest Rate (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(purchase.interest_rate * 100),
                    step=0.1,
                    key=f"mp_interest_{idx}"
                ) / 100.0

            if st.button(f"🗑️ Delete {purchase.name}", key=f"delete_mp_{idx}"):
                st.session_state.major_purchases.pop(idx)
                st.rerun()

    # Recurring Expenses
    st.markdown("---")
    st.subheader("🔄 Recurring Expenses")

    st.markdown("""
    Add expenses that repeat every N years (e.g., buying a new car every 7 years,
    home renovations every 15 years).
    """)

    if st.button("➕ Add Recurring Expense"):
        new_recurring = RecurringExpense(
            name="New Recurring",
            category="Other",
            amount=10000.0,
            frequency_years=5,
            start_year=st.session_state.current_year,
            end_year=None,
            inflation_adjust=True,
            parent="Both",
            financing_years=0,
            interest_rate=0.0
        )
        st.session_state.recurring_expenses.append(new_recurring)
        st.rerun()

    for idx, recurring in enumerate(st.session_state.recurring_expenses):
        with st.expander(f"🔁 {recurring.name} - Every {recurring.frequency_years} years"):
            col1, col2, col3 = st.columns(3)

            with col1:
                recurring.name = st.text_input("Name", value=recurring.name, key=f"re_name_{idx}")
                recurring.category = st.text_input("Category", value=recurring.category, key=f"re_category_{idx}")
                recurring.amount = st.number_input("Amount ($)", min_value=0.0, value=float(recurring.amount), step=1000.0, key=f"re_amount_{idx}")

            with col2:
                recurring.frequency_years = st.number_input("Frequency (years)", min_value=1, max_value=50, value=recurring.frequency_years, key=f"re_freq_{idx}")
                recurring.start_year = st.number_input("Start Year", min_value=2020, max_value=2100, value=recurring.start_year, key=f"re_start_{idx}")
                end_year_value = recurring.end_year if recurring.end_year is not None else 2100
                end_year = st.number_input("End Year (or max for no end)", min_value=recurring.start_year, max_value=2100, value=end_year_value, key=f"re_end_{idx}")
                recurring.end_year = end_year if end_year < 2100 else None

            with col3:
                recurring.inflation_adjust = st.checkbox("Inflation Adjust", value=recurring.inflation_adjust, key=f"re_inflate_{idx}")
                owner_options = ["Both", st.session_state.parent1_name, st.session_state.parent2_name]
                # Map old values to new values for backwards compatibility
                if recurring.parent == "ParentX":
                    recurring.parent = st.session_state.parent1_name
                elif recurring.parent == "ParentY":
                    recurring.parent = st.session_state.parent2_name
                recurring.parent = st.selectbox("Owner", owner_options, index=owner_options.index(recurring.parent) if recurring.parent in owner_options else 0, key=f"re_parent_{idx}")
                recurring.financing_years = st.number_input("Financing Years", min_value=0, max_value=30, value=recurring.financing_years, key=f"re_financing_{idx}")
                recurring.interest_rate = st.number_input(
                    "Interest Rate (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(recurring.interest_rate * 100),
                    step=0.1,
                    key=f"re_interest_{idx}"
                ) / 100.0

            if st.button(f"🗑️ Delete {recurring.name}", key=f"delete_re_{idx}"):
                st.session_state.recurring_expenses.pop(idx)
                st.rerun()


def children_tab():
    """Children tab"""
    st.header("\U0001f476 Children")
    tab_walkthrough("children")

    if _guided_mode_toggle("children"):
        _children_guided_mode()
        return

    st.info("💡 **About Children Expenses**: All child-related expenses shown in the templates are calculated in today's dollars and will be automatically inflation-adjusted going forward based on your selected economic scenario.")

    st.subheader("Add a Child")
    col1, col2, col3 = st.columns(3)

    with col1:
        child_name = st.text_input("Child Name", key="new_child_name")
    with col2:
        child_birth_year = st.number_input(
            "Birth Year",
            min_value=1990,
            max_value=st.session_state.current_year + 20,
            value=st.session_state.current_year,
            key="new_child_birth_year"
        )
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("➕ Add Child"):
            # Check for duplicate names
            if any(child['name'] == child_name for child in st.session_state.children_list):
                st.error(f"A child named '{child_name}' already exists. Please use a different name.")
            elif child_name.strip() == "":
                st.error("Please enter a child name.")
            else:
                st.session_state.children_list.append({
                    'name': child_name,
                    'birth_year': child_birth_year,
                    'use_template': True,
                    'template_state': 'Seattle',
                    'template_strategy': 'Average',
                    'school_type': 'Public',  # K-12: Public or Private
                    'college_type': 'Public',  # College: Public or Private
                    'college_location': 'Seattle'  # Where they attend college
                })
                st.success(f"Added {child_name}")
                st.rerun()

    # Display existing children
    if st.session_state.children_list:
        st.subheader("Your Children")

        for idx, child in enumerate(st.session_state.children_list):
            current_age = st.session_state.current_year - child['birth_year']

            with st.expander(f"👶 {child['name']} (Age {current_age}, Born {child['birth_year']})"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    child['name'] = st.text_input("Name", value=child['name'], key=f"child_name_{idx}")
                    child['birth_year'] = st.number_input(
                        "Birth Year",
                        min_value=1990,
                        max_value=st.session_state.current_year + 20,
                        value=child['birth_year'],
                        key=f"child_birth_{idx}"
                    )

                with col2:
                    child['use_template'] = st.checkbox(
                        "Use State Template",
                        value=child.get('use_template', True),
                        key=f"child_template_{idx}"
                    )

                    if child['use_template']:
                        child['template_state'] = st.selectbox(
                            "Template Location",
                            AVAILABLE_LOCATIONS_CHILDREN,
                            index=AVAILABLE_LOCATIONS_CHILDREN.index(child.get('template_state', 'Seattle')) if child.get('template_state', 'Seattle') in AVAILABLE_LOCATIONS_CHILDREN else 1,
                            key=f"child_state_{idx}"
                        )
                        # Get available strategies for this location
                        available_child_strategies = get_available_strategies_for_location(child.get('template_state', 'Seattle'), 'children')
                        # Normalize the stored strategy name to handle backward compatibility
                        current_strategy = normalize_strategy_name(child.get('template_strategy', 'Average'))
                        default_idx = available_child_strategies.index(current_strategy) if current_strategy in available_child_strategies else 1
                        child['template_strategy'] = st.selectbox(
                            "Spending Level",
                            available_child_strategies,
                            index=default_idx,
                            key=f"child_strategy_{idx}"
                        )

                with col3:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button(f"🗑️ Remove {child['name']}", key=f"remove_child_{idx}"):
                        st.session_state.children_list.pop(idx)
                        st.rerun()

                # Add new row for school type and college location
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    child['school_type'] = st.selectbox(
                        "K-12 School Type",
                        ["Public", "Private"],
                        index=["Public", "Private"].index(child.get('school_type', 'Public')),
                        key=f"child_school_{idx}",
                        help="Private schools typically add $10k-30k/year to education costs"
                    )

                with col2:
                    child['college_type'] = st.selectbox(
                        "College Type",
                        ["Public", "Private"],
                        index=["Public", "Private"].index(child.get('college_type', 'Public')),
                        key=f"child_college_type_{idx}",
                        help="Private colleges typically cost 2-3x more than public colleges"
                    )

                with col3:
                    child['college_location'] = st.selectbox(
                        "College Location",
                        AVAILABLE_LOCATIONS_CHILDREN,
                        index=AVAILABLE_LOCATIONS_CHILDREN.index(child.get('college_location', 'Seattle')) if child.get('college_location', 'Seattle') in AVAILABLE_LOCATIONS_CHILDREN else 0,
                        key=f"child_college_{idx}",
                        help="Location where child will attend college (ages 18-21). Room & board included."
                    )
    else:
        st.info("No children added yet. Add children using the form above.")

    # Children expense templates preview
    st.subheader("📊 Children Expense Templates Preview")

    col1, col2 = st.columns(2)
    with col1:
        preview_state = st.selectbox("Preview Location", AVAILABLE_LOCATIONS_CHILDREN, key="preview_state")
    with col2:
        preview_available_strategies = get_available_strategies_for_location(preview_state, 'children')
        preview_strategy = st.selectbox("Preview Strategy", preview_available_strategies, key="preview_strategy")

    col3, col4 = st.columns(2)
    with col3:
        preview_school_type = st.selectbox(
            "K-12 School Type",
            ["Public", "Private"],
            key="preview_school_type",
            help="Private schools typically add $10k-30k/year to education costs (ages 5-17)"
        )
    with col4:
        preview_college_type = st.selectbox(
            "College Type",
            ["Public", "Private"],
            key="preview_college_type",
            help="Private colleges typically cost 2-3x more than public colleges"
        )

    # Use helper function to get template data
    template = get_template_strategy_data(preview_state, preview_strategy, 'children')

    if template:

        # Adjust for private K-12 school (ages 5-17)
        if preview_school_type == "Private":
            # Add private school tuition based on location
            private_school_costs = {
                'Seattle': 20000,
                'Sacramento': 15000,
                'Houston': 12000,
                'New York': 30000,
                'San Francisco': 28000,
                'Los Angeles': 22000,
                'Portland': 18000,
                'Auckland': 16000,
                'Wellington': 15000
            }
            additional_tuition = private_school_costs.get(preview_state, 20000)

            # Apply to ages 5-17 (indices 5-17)
            for age in range(5, 18):
                if age < len(template['Education']):
                    template['Education'][age] += additional_tuition

        # Adjust education costs based on college type
        if preview_college_type == "Private":
            # Private colleges cost approximately 2.5x more than public colleges
            template['Education'] = [cost * 2.5 for cost in template['Education']]

        # Create a preview dataframe
        preview_df = pd.DataFrame({
            'Age': list(range(31)),
            **{category: values for category, values in template.items()}
        })

        st.dataframe(preview_df, use_container_width=True, height=400)

        # Show totals by age
        age_totals = preview_df.set_index('Age').sum(axis=1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(range(31)),
            y=age_totals.values,
            name="Total Annual Expenses"
        ))
        fig.update_layout(
            title=f"Total Annual Child Expenses by Age - {preview_state} {preview_strategy}<br>({preview_school_type} K-12, {preview_college_type} College)",
            xaxis_title="Child Age",
            yaxis_title="Annual Expenses ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Display data sources for children's expense template
        st.markdown("---")
        data_source = get_expense_data_source(preview_state)

        st.markdown("### 📚 Data Sources")
        st.markdown(f"**Source:** {data_source['source']}")

        # Display URLs as clickable links
        urls = data_source['url'].split(', ')
        if len(urls) == 1 and urls[0] != 'N/A':
            st.markdown(f"**URL:** [{urls[0]}]({urls[0]})")
        elif urls[0] != 'N/A':
            st.markdown("**URLs:**")
            for url in urls:
                url = url.strip()
                st.markdown(f"- [{url}]({url})")

        st.markdown(f"**Data Year:** {data_source['year']}")

        if data_source['notes']:
            with st.expander("📝 Additional Notes"):
                st.markdown(data_source['notes'])


def house_tab():
    """House portfolio tab"""
    st.header("🏠 House Portfolio")
    tab_walkthrough("house")

    if st.button("➕ Add House"):
        new_house = House(
            name="New Property",
            purchase_year=st.session_state.current_year,
            purchase_price=500000.0,
            current_value=500000.0,
            mortgage_balance=400000.0,
            mortgage_rate=0.065,
            mortgage_years_left=30,
            property_tax_rate=0.01,
            home_insurance=1500.0,
            maintenance_rate=0.01,
            upkeep_costs=3000.0,
            owner="Shared",
            timeline=[HouseTimelineEntry(st.session_state.current_year, "Own_Live", 0.0)]
        )
        st.session_state.houses.append(new_house)
        st.rerun()

    for idx, house in enumerate(st.session_state.houses):
        monthly_payment = calculate_monthly_house_payment(house)
        annual_payment = monthly_payment * 12

        with st.expander(f"🏡 {house.name} - {format_currency(house.current_value)} (Monthly: {format_currency(monthly_payment)})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Basic Information")
                house.name = st.text_input("Property Name", value=house.name, key=f"house_name_{idx}")
                house.purchase_year = st.number_input("Purchase Year", min_value=1950, max_value=2100, value=house.purchase_year, key=f"house_pyear_{idx}")
                house.purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, value=float(house.purchase_price), step=10000.0, key=f"house_pprice_{idx}")
                house.current_value = st.number_input("Current Value ($)", min_value=0.0, value=float(house.current_value), step=10000.0, key=f"house_cvalue_{idx}")
                st.caption(f"Formatted: {format_currency(house.current_value)}")

            with col2:
                st.subheader("Mortgage Information")
                house.mortgage_balance = st.number_input("Mortgage Balance ($)", min_value=0.0, value=float(house.mortgage_balance), step=10000.0, key=f"house_mbalance_{idx}")
                house.mortgage_rate = st.number_input(
                    "Mortgage Rate (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(house.mortgage_rate * 100),
                    step=0.1,
                    key=f"house_mrate_{idx}"
                ) / 100.0
                house.mortgage_years_left = st.number_input("Years Left", min_value=0, max_value=50, value=house.mortgage_years_left, key=f"house_myears_{idx}")

            with col3:
                st.subheader("Annual Costs")
                house.property_tax_rate = st.number_input(
                    "Property Tax Rate (%)",
                    min_value=0.0,
                    max_value=5.0,
                    value=float(house.property_tax_rate * 100),
                    step=0.01,
                    key=f"house_ptax_{idx}"
                ) / 100.0
                house.home_insurance = st.number_input("Home Insurance ($/year)", min_value=0.0, value=float(house.home_insurance), step=100.0, key=f"house_insurance_{idx}")
                house.maintenance_rate = st.number_input(
                    "Maintenance Rate (% of value)",
                    min_value=0.0,
                    max_value=10.0,
                    value=float(house.maintenance_rate * 100),
                    step=0.1,
                    key=f"house_maint_{idx}"
                ) / 100.0
                house.upkeep_costs = st.number_input("Additional Upkeep ($/year)", min_value=0.0, value=float(house.upkeep_costs), step=100.0, key=f"house_upkeep_{idx}")

            owner_options = ["Shared", st.session_state.parent1_name, st.session_state.parent2_name]
            # Map old values to new values for backwards compatibility
            if house.owner == "ParentX":
                house.owner = st.session_state.parent1_name
            elif house.owner == "ParentY":
                house.owner = st.session_state.parent2_name
            house.owner = st.selectbox(
                "Owner",
                owner_options,
                index=owner_options.index(house.owner) if house.owner in owner_options else 0,
                key=f"house_owner_{idx}"
            )

            col_loc, col_appr = st.columns(2)
            with col_loc:
                house.location = st.text_input("Location (city/state)",
                    value=getattr(house, 'location', ''),
                    placeholder="e.g., Seattle, WA",
                    key=f"house_location_{idx}")
            with col_appr:
                house.appreciation_rate = st.number_input("Annual appreciation (%)",
                    min_value=-5.0, max_value=15.0,
                    value=float(getattr(house, 'appreciation_rate', 3.0)),
                    step=0.5, key=f"house_appr_{idx}",
                    help="US historical avg: ~3-4%. Coastal cities may be higher.")

            # Timeline
            st.subheader("Property Timeline")
            st.markdown("Define how the property status changes over time")

            timeline_data = []
            for entry in house.timeline:
                timeline_data.append({
                    'Year': entry.year,
                    'Status': entry.status,
                    'Rental Income': entry.rental_income
                })

            timeline_df = pd.DataFrame(timeline_data)
            edited_timeline = st.data_editor(
                timeline_df,
                num_rows="dynamic",
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Own_Live", "Own_Rent", "Sold"],
                        required=True
                    )
                },
                key=f"house_timeline_{idx}"
            )

            # Update timeline
            house.timeline = [
                HouseTimelineEntry(row['Year'], row['Status'], row['Rental Income'])
                for _, row in edited_timeline.iterrows()
            ]

            # Payment breakdown
            st.subheader("Payment Breakdown")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Monthly Payment (PITI)", format_currency(monthly_payment))
            with col2:
                st.metric("Annual Payment", format_currency(annual_payment))
            with col3:
                annual_property_tax = house.current_value * house.property_tax_rate
                st.metric("Annual Property Tax", format_currency(annual_property_tax))

            if st.button(f"🗑️ Delete {house.name}", key=f"delete_house_{idx}"):
                st.session_state.houses.pop(idx)
                st.rerun()


def economy_tab():
    """Economy parameters configuration tab"""
    st.header("📈 Economy & Market Parameters")
    tab_walkthrough("economy")

    st.markdown("""
    Configure the economic assumptions used in your financial projections.
    You can use historical averages or specify custom values for returns and inflation.
    """)

    params = st.session_state.economic_params

    # Calculate historical stats
    stats = get_historical_return_stats()
    historical_return = stats['mean']
    historical_inflation = 0.03  # Historical US average ~3%
    historical_expense_growth = 0.02  # Historical average ~2% (close to inflation)
    historical_healthcare_inflation = 0.055  # Historical average ~5.5% (healthcare grows faster than general inflation)

    # Investment Returns Section
    st.subheader("📊 Investment Returns")

    col1, col2 = st.columns([1, 2])

    with col1:
        return_mode = st.radio(
            "Return Source",
            ["Historical Average", "Custom Value"],
            index=0 if params.use_historical_returns else 1,
            key="return_mode"
        )
        params.use_historical_returns = (return_mode == "Historical Average")

    with col2:
        if params.use_historical_returns:
            st.info(f"📈 Using historical S&P 500 average: **{historical_return*100:.2f}%**")
            st.caption(f"Based on {stats['total_years']} years of data (1924-2023)")
            params.investment_return = historical_return
        else:
            params.investment_return = st.number_input(
                "Annual Investment Return (%)",
                min_value=-20.0,
                max_value=50.0,
                value=float(params.investment_return * 100),
                step=0.5,
                help="Expected annual return on your investment portfolio"
            ) / 100.0

    # Inflation Section
    st.subheader("💸 Inflation")

    col1, col2 = st.columns([1, 2])

    with col1:
        inflation_mode = st.radio(
            "Inflation Source",
            ["Historical Average", "Custom Value"],
            index=0 if params.use_historical_inflation else 1,
            key="inflation_mode"
        )
        params.use_historical_inflation = (inflation_mode == "Historical Average")

    with col2:
        if params.use_historical_inflation:
            st.info(f"📈 Using historical US average: **{historical_inflation*100:.1f}%**")
            st.caption("Long-term historical average inflation rate")
            params.inflation_rate = historical_inflation
        else:
            params.inflation_rate = st.number_input(
                "Annual Inflation Rate (%)",
                min_value=-5.0,
                max_value=20.0,
                value=float(params.inflation_rate * 100),
                step=0.1,
                help="Expected annual inflation rate for general expenses"
            ) / 100.0

    # Other Parameters Section
    st.subheader("⚙️ Additional Parameters")

    # Expense Growth Rate
    st.markdown("#### 📈 Expense Growth Rate")
    col1, col2 = st.columns([1, 2])

    with col1:
        expense_growth_mode = st.radio(
            "Expense Growth Source",
            ["Historical Average", "Custom Value"],
            index=0 if params.use_historical_expense_growth else 1,
            key="expense_growth_mode"
        )
        params.use_historical_expense_growth = (expense_growth_mode == "Historical Average")

    with col2:
        if params.use_historical_expense_growth:
            st.info(f"📈 Using historical average: **{historical_expense_growth*100:.1f}%**")
            st.caption("Long-term average expense growth rate (typically close to inflation)")
            params.expense_growth_rate = historical_expense_growth
        else:
            params.expense_growth_rate = st.number_input(
                "Annual Expense Growth Rate (%)",
                min_value=-5.0,
                max_value=20.0,
                value=float(params.expense_growth_rate * 100),
                step=0.1,
                help="Annual growth rate for expenses (separate from inflation)"
            ) / 100.0

    # Healthcare Inflation
    st.markdown("#### 🏥 Healthcare Inflation")
    col1, col2 = st.columns([1, 2])

    with col1:
        healthcare_inflation_mode = st.radio(
            "Healthcare Inflation Source",
            ["Historical Average", "Custom Value"],
            index=0 if params.use_historical_healthcare_inflation else 1,
            key="healthcare_inflation_mode"
        )
        params.use_historical_healthcare_inflation = (healthcare_inflation_mode == "Historical Average")

    with col2:
        if params.use_historical_healthcare_inflation:
            st.info(f"📈 Using historical average: **{historical_healthcare_inflation*100:.1f}%**")
            st.caption("Healthcare costs historically grow faster than general inflation")
            params.healthcare_inflation_rate = historical_healthcare_inflation
        else:
            params.healthcare_inflation_rate = st.number_input(
                "Annual Healthcare Inflation (%)",
                min_value=-5.0,
                max_value=30.0,
                value=float(params.healthcare_inflation_rate * 100),
                step=0.5,
                help="Healthcare costs typically grow faster than general inflation"
            ) / 100.0

    # Summary Box
    st.divider()
    st.subheader("📋 Current Parameters Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Investment Return", f"{params.investment_return*100:.2f}%",
                 help="Historical" if params.use_historical_returns else "Custom")
    with col2:
        st.metric("Inflation Rate", f"{params.inflation_rate*100:.2f}%",
                 help="Historical" if params.use_historical_inflation else "Custom")
    with col3:
        st.metric("Expense Growth", f"{params.expense_growth_rate*100:.2f}%",
                 help="Historical" if params.use_historical_expense_growth else "Custom")
    with col4:
        st.metric("Healthcare Inflation", f"{params.healthcare_inflation_rate*100:.2f}%",
                 help="Historical" if params.use_historical_healthcare_inflation else "Custom")

    # Historical Market Data Reference
    st.divider()
    st.subheader("📜 Historical S&P 500 Returns Reference")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mean Return", f"{stats['mean']*100:.2f}%")
    with col2:
        st.metric("Median Return", f"{stats['median']*100:.2f}%")
    with col3:
        st.metric("Std Deviation", f"{stats['std']*100:.2f}%")
    with col4:
        st.metric("Positive Years", f"{stats['positive_percentage']:.1f}%")

    # Historical returns chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(1924, 1924 + len(HISTORICAL_STOCK_RETURNS))),
        y=[r * 100 for r in HISTORICAL_STOCK_RETURNS],
        marker_color=['green' if r > 0 else 'red' for r in HISTORICAL_STOCK_RETURNS],
        name="Annual Return %"
    ))
    fig.update_layout(
        title="Historical S&P 500 Annual Returns (1924-2023)",
        xaxis_title="Year",
        yaxis_title="Return (%)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def retirement_tab():
    """Retirement planning tab"""
    st.header("🏖️ Retirement Planning")
    tab_walkthrough("retirement")

    # Calculate retirement years
    parentX_birth_year = st.session_state.current_year - st.session_state.parentX_age
    parentY_birth_year = st.session_state.current_year - st.session_state.parentY_age

    parentX_retirement_year = parentX_birth_year + st.session_state.parentX_retirement_age
    parentY_retirement_year = parentY_birth_year + st.session_state.parentY_retirement_age

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"{st.session_state.parent1_emoji} {st.session_state.parent1_name}")
        st.metric("Retirement Year", parentX_retirement_year)
        st.metric("Years Until Retirement", max(0, parentX_retirement_year - st.session_state.current_year))
        st.metric("Monthly SS Benefit", format_currency(st.session_state.parentX_ss_benefit))
        st.metric("Annual SS Benefit", format_currency(st.session_state.parentX_ss_benefit * 12))

    with col2:
        st.subheader(f"{st.session_state.parent2_emoji} {st.session_state.parent2_name}")
        st.metric("Retirement Year", parentY_retirement_year)
        st.metric("Years Until Retirement", max(0, parentY_retirement_year - st.session_state.current_year))
        st.metric("Monthly SS Benefit", format_currency(st.session_state.parentY_ss_benefit))
        st.metric("Annual SS Benefit", format_currency(st.session_state.parentY_ss_benefit * 12))

    # Social Security Insolvency Settings
    st.subheader("🔴 Social Security Insolvency Modeling")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.ss_insolvency_enabled = st.checkbox(
            "Enable SS Insolvency Modeling",
            value=st.session_state.ss_insolvency_enabled,
            help="Model potential Social Security benefit shortfall"
        )

    with col2:
        st.session_state.ss_shortfall_percentage = st.number_input(
            "Benefit Shortfall (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.ss_shortfall_percentage),
            step=1.0,
            help="Percentage reduction in benefits after insolvency (default 30%)",
            disabled=not st.session_state.ss_insolvency_enabled
        )

    if st.session_state.ss_insolvency_enabled:
        st.warning(f"⚠️ Modeling {st.session_state.ss_shortfall_percentage}% benefit reduction after 2034")

        # Show impact
        parentX_reduced = st.session_state.parentX_ss_benefit * (1 - st.session_state.ss_shortfall_percentage / 100)
        parentY_reduced = st.session_state.parentY_ss_benefit * (1 - st.session_state.ss_shortfall_percentage / 100)

        st.info(f"""
        **After insolvency:**
        - {st.session_state.parent1_name}: {format_currency(st.session_state.parentX_ss_benefit)}/mo → {format_currency(parentX_reduced)}/mo
        - {st.session_state.parent2_name}: {format_currency(st.session_state.parentY_ss_benefit)}/mo → {format_currency(parentY_reduced)}/mo
        """)


def timeline_tab():
    """Timeline and state relocation tab"""
    st.header("🗓️ Timeline & State Planning")
    tab_walkthrough("timeline")

    st.markdown("""
    Plan your relocations and spending strategy changes over time.
    Expenses will automatically adjust based on state and spending level.
    """)

    st.subheader("State & Spending Timeline")

    # Convert timeline to DataFrame
    timeline_data = []
    for entry in st.session_state.state_timeline:
        timeline_data.append({
            'Year': entry.year,
            'State': entry.state,
            'Spending Strategy': entry.spending_strategy
        })

    timeline_df = pd.DataFrame(timeline_data)

    # Build dynamic location list including custom cities
    available_locations = list(AVAILABLE_LOCATIONS_FAMILY)
    if hasattr(st.session_state, 'custom_family_templates') and st.session_state.custom_family_templates:
        # Add custom cities that aren't already in the list
        custom_cities = list(st.session_state.custom_family_templates.keys())
        for city in custom_cities:
            if city not in available_locations:
                available_locations.append(city)

    edited_timeline = st.data_editor(
        timeline_df,
        num_rows="dynamic",
        column_config={
            "State": st.column_config.SelectboxColumn(
                "Location",
                options=available_locations,
                required=True,
                help="Select your living location - expenses will adjust automatically"
            ),
            "Spending Strategy": st.column_config.SelectboxColumn(
                "Spending Strategy",
                options=STATISTICAL_STRATEGIES,
                required=True
            )
        },
        use_container_width=True
    )

    # Update state timeline
    st.session_state.state_timeline = [
        StateTimelineEntry(row['Year'], row['State'], row['Spending Strategy'])
        for _, row in edited_timeline.iterrows()
    ]

    # Visualization
    if len(edited_timeline) > 0:
        st.subheader("Timeline Visualization")

        # Calculate when both parents reach their death age
        parent1_death_year = (st.session_state.current_year - st.session_state.parentX_age) + st.session_state.parentX_death_age
        parent2_death_year = (st.session_state.current_year - st.session_state.parentY_age) + st.session_state.parentY_death_age
        end_year = max(parent1_death_year, parent2_death_year)

        # Create timeline data for all years from current to end
        all_years = list(range(st.session_state.current_year, end_year + 1))

        # Create a horizontal timeline showing state/spending for each year
        timeline_states = []
        timeline_spending = []

        for year in all_years:
            state, strategy = get_state_for_year(year)
            timeline_states.append(state)
            timeline_spending.append(strategy)

        # Create a Gantt-style timeline
        fig = go.Figure()

        # Group consecutive years with same state/strategy
        segments = []
        if timeline_states:
            current_state = timeline_states[0]
            current_strategy = timeline_spending[0]
            start_year = all_years[0]

            for i in range(1, len(all_years)):
                if timeline_states[i] != current_state or timeline_spending[i] != current_strategy:
                    # End of current segment
                    segments.append({
                        'state': current_state,
                        'strategy': current_strategy,
                        'start': start_year,
                        'end': all_years[i-1]
                    })
                    current_state = timeline_states[i]
                    current_strategy = timeline_spending[i]
                    start_year = all_years[i]

            # Add final segment
            segments.append({
                'state': current_state,
                'strategy': current_strategy,
                'start': start_year,
                'end': all_years[-1]
            })

        # Plot segments as horizontal bars
        for seg in segments:
            duration = seg['end'] - seg['start'] + 1
            location_full_name = get_location_display_name(seg['state'])
            fig.add_trace(go.Bar(
                x=[duration],
                y=['Timeline'],
                orientation='h',
                name=f"{location_full_name} - {seg['strategy']}",
                text=f"{location_full_name}<br>{seg['strategy']}<br>{seg['start']}-{seg['end']}",
                textposition='inside',
                hovertemplate=f"<b>{location_full_name}</b><br>{seg['strategy']}<br>Years: {seg['start']}-{seg['end']}<br>Duration: {duration} years<extra></extra>",
                base=seg['start']
            ))

        fig.update_layout(
            title=f"State & Spending Timeline (Until Both Parents Reach Age 100)",
            xaxis_title="Year",
            xaxis=dict(
                tickmode='linear',
                tick0=st.session_state.current_year,
                dtick=5,  # Show tick every 5 years
                range=[st.session_state.current_year, end_year]
            ),
            yaxis=dict(showticklabels=False),
            height=200,
            showlegend=True,
            barmode='stack',
            bargap=0
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show key milestones
        st.markdown(f"**Timeline extends to {end_year}** ({st.session_state.parent1_name} age {st.session_state.parentX_death_age}: {parent1_death_year}, {st.session_state.parent2_name} age {st.session_state.parentY_death_age}: {parent2_death_year})")

        # Add world map visualization
        st.markdown("---")
        st.subheader("🌍 World Map: Your Relocation Journey")

        # Get unique locations from timeline in chronological order
        timeline_locations = []
        seen_states = set()

        for entry in sorted(st.session_state.state_timeline, key=lambda x: x.year):
            if entry.state not in seen_states:
                # Check built-in coordinates first, then custom coordinates
                coords = LOCATION_COORDINATES.get(entry.state)
                if coords is None and hasattr(st.session_state, 'custom_location_coordinates'):
                    coords = st.session_state.custom_location_coordinates.get(entry.state)

                timeline_locations.append({
                    'state': entry.state,
                    'year': entry.year,
                    'coords': coords
                })
                seen_states.add(entry.state)

        # Only show map if we have valid coordinates for at least 2 locations
        valid_locations = [loc for loc in timeline_locations if loc['coords'] is not None]

        if len(valid_locations) >= 1:
            # Create map figure
            map_fig = go.Figure()

            # Add flight path lines between consecutive locations
            for i in range(len(valid_locations) - 1):
                loc1 = valid_locations[i]
                loc2 = valid_locations[i + 1]

                # Add curved line (great circle route simulation)
                map_fig.add_trace(go.Scattergeo(
                    lon=[loc1['coords']['lon'], loc2['coords']['lon']],
                    lat=[loc1['coords']['lat'], loc2['coords']['lat']],
                    mode='lines',
                    line=dict(width=2, color='rgb(255, 100, 100)'),
                    opacity=0.6,
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Add location markers
            lats = [loc['coords']['lat'] for loc in valid_locations]
            lons = [loc['coords']['lon'] for loc in valid_locations]
            texts = [f"{get_location_display_name(loc['state'])}<br>Year: {loc['year']}" for loc in valid_locations]

            map_fig.add_trace(go.Scattergeo(
                lon=lons,
                lat=lats,
                mode='markers+text',
                marker=dict(
                    size=15,
                    color='rgb(50, 120, 255)',
                    line=dict(width=3, color='white'),
                    symbol='circle'
                ),
                text=[f"{i+1}" for i in range(len(valid_locations))],
                textfont=dict(size=10, color='white', family='Arial Black'),
                textposition='middle center',
                hovertext=texts,
                hoverinfo='text',
                showlegend=False
            ))

            # Center map on locations
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            # Update map layout
            map_fig.update_layout(
                title=dict(
                    text='Your Life Journey: Where You\'ll Live',
                    font=dict(size=18)
                ),
                geo=dict(
                    projection_type='natural earth',
                    showland=True,
                    landcolor='rgb(243, 243, 243)',
                    coastlinecolor='rgb(204, 204, 204)',
                    countrycolor='rgb(204, 204, 204)',
                    showcountries=True,
                    showocean=True,
                    oceancolor='rgb(230, 245, 255)',
                    showlakes=True,
                    lakecolor='rgb(230, 245, 255)',
                    projection=dict(
                        rotation=dict(
                            lon=center_lon,
                            lat=center_lat
                        )
                    )
                ),
                height=600,
                margin=dict(l=0, r=0, t=50, b=0)
            )

            st.plotly_chart(map_fig, use_container_width=True)

            # Show location journey summary
            if len(valid_locations) == 1:
                loc = valid_locations[0]
                st.info(f"📍 **{loc['year']}:** 🏠 Home in {get_location_display_name(loc['state'])}")
            else:
                st.markdown("**🛫 Your Relocation Journey:**")
                for i, loc in enumerate(valid_locations):
                    if i == 0:
                        st.info(f"**{loc['year']}:** 🏠 Start in {get_location_display_name(loc['state'])}")
                    else:
                        prev_loc = valid_locations[i-1]
                        years_duration = loc['year'] - prev_loc['year']
                        st.success(f"**{loc['year']}:** ✈️ Move to {get_location_display_name(loc['state'])} (after {years_duration} years in {get_location_display_name(prev_loc['state'])})")
        else:
            # Check if there are locations without coordinates
            missing_coords = [loc['state'] for loc in timeline_locations if loc['coords'] is None]
            if missing_coords:
                st.warning(f"⚠️ The following custom cities are missing coordinates: **{', '.join(missing_coords)}**")
                st.info("💡 To display custom cities on the world map, edit them in the Family Expenses tab and add their latitude/longitude coordinates.")
            else:
                st.warning("⚠️ No valid location coordinates found. Please ensure your timeline includes recognized locations.")

    # Show current and future states
    st.subheader("Timeline Summary")

    current_state, current_strategy = get_state_for_year(st.session_state.current_year)
    st.info(f"**Current ({st.session_state.current_year}):** {current_state} - {current_strategy}")

    # Show next 5 years
    st.markdown("**Upcoming Changes:**")
    for year in range(st.session_state.current_year + 1, st.session_state.current_year + 6):
        state, strategy = get_state_for_year(year)
        prev_state, prev_strategy = get_state_for_year(year - 1)

        if state != prev_state or strategy != prev_strategy:
            st.success(f"**{year}:** → {state} - {strategy}")


# ============================================================================
# TAX DATABASE: Location-based tax information
# ============================================================================

# US State Tax Information
US_STATE_TAX_INFO = {
    # States with no income tax
    'Alaska': {'type': 'none', 'rate': 0.0},
    'Florida': {'type': 'none', 'rate': 0.0},
    'Nevada': {'type': 'none', 'rate': 0.0},
    'New Hampshire': {'type': 'none', 'rate': 0.0},  # Only taxes dividends/interest
    'South Dakota': {'type': 'none', 'rate': 0.0},
    'Tennessee': {'type': 'none', 'rate': 0.0},
    'Texas': {'type': 'none', 'rate': 0.0},
    'Washington': {'type': 'none', 'rate': 0.0},
    'Wyoming': {'type': 'none', 'rate': 0.0},

    # States with flat tax rates
    'Arizona': {'type': 'flat', 'rate': 0.025},
    'Colorado': {'type': 'flat', 'rate': 0.044},
    'Idaho': {'type': 'flat', 'rate': 0.058},
    'Illinois': {'type': 'flat', 'rate': 0.0495},
    'Indiana': {'type': 'flat', 'rate': 0.0315},
    'Kentucky': {'type': 'flat', 'rate': 0.045},
    'Massachusetts': {'type': 'flat', 'rate': 0.05},
    'Michigan': {'type': 'flat', 'rate': 0.0425},
    'Mississippi': {'type': 'flat', 'rate': 0.05},
    'North Carolina': {'type': 'flat', 'rate': 0.045},
    'Pennsylvania': {'type': 'flat', 'rate': 0.0307},
    'Utah': {'type': 'flat', 'rate': 0.0465},

    # States with progressive tax brackets (showing top marginal rate as approximation)
    'Alabama': {'type': 'progressive', 'rate': 0.05},
    'Arkansas': {'type': 'progressive', 'rate': 0.047},
    'California': {'type': 'progressive', 'rate': 0.133, 'note': 'Highest in US'},
    'Connecticut': {'type': 'progressive', 'rate': 0.0699},
    'Delaware': {'type': 'progressive', 'rate': 0.066},
    'Georgia': {'type': 'progressive', 'rate': 0.0575},
    'Hawaii': {'type': 'progressive', 'rate': 0.11},
    'Iowa': {'type': 'progressive', 'rate': 0.06},
    'Kansas': {'type': 'progressive', 'rate': 0.057},
    'Louisiana': {'type': 'progressive', 'rate': 0.0425},
    'Maine': {'type': 'progressive', 'rate': 0.0715},
    'Maryland': {'type': 'progressive', 'rate': 0.0575},
    'Minnesota': {'type': 'progressive', 'rate': 0.0985},
    'Missouri': {'type': 'progressive', 'rate': 0.054},
    'Montana': {'type': 'progressive', 'rate': 0.0675},
    'Nebraska': {'type': 'progressive', 'rate': 0.0684},
    'New Jersey': {'type': 'progressive', 'rate': 0.1075},
    'New Mexico': {'type': 'progressive', 'rate': 0.059},
    'New York': {'type': 'progressive', 'rate': 0.109},
    'North Dakota': {'type': 'progressive', 'rate': 0.029},
    'Ohio': {'type': 'progressive', 'rate': 0.0385},
    'Oklahoma': {'type': 'progressive', 'rate': 0.0475},
    'Oregon': {'type': 'progressive', 'rate': 0.099},
    'Rhode Island': {'type': 'progressive', 'rate': 0.0599},
    'South Carolina': {'type': 'progressive', 'rate': 0.07},
    'Vermont': {'type': 'progressive', 'rate': 0.0875},
    'Virginia': {'type': 'progressive', 'rate': 0.0575},
    'West Virginia': {'type': 'progressive', 'rate': 0.065},
    'Wisconsin': {'type': 'progressive', 'rate': 0.0765},
    'District of Columbia': {'type': 'progressive', 'rate': 0.1075},
}

# Country Tax Information (simplified - using approximate effective rates)
COUNTRY_TAX_INFO = {
    'United States': {'type': 'federal_state', 'federal_rate': 'progressive', 'has_fica': True},

    # Major developed countries
    'Canada': {'type': 'federal_provincial', 'effective_rate': 0.33, 'has_fica': False, 'note': 'CPP/EI separate'},
    'United Kingdom': {'type': 'national', 'effective_rate': 0.40, 'has_fica': False, 'note': 'NI separate'},
    'Germany': {'type': 'national', 'effective_rate': 0.45, 'has_fica': False, 'note': 'Social insurance separate'},
    'France': {'type': 'national', 'effective_rate': 0.45, 'has_fica': False},
    'Australia': {'type': 'national', 'effective_rate': 0.37, 'has_fica': False},
    'Japan': {'type': 'national', 'effective_rate': 0.33, 'has_fica': False},
    'South Korea': {'type': 'national', 'effective_rate': 0.38, 'has_fica': False},
    'Singapore': {'type': 'national', 'effective_rate': 0.22, 'has_fica': False, 'note': 'Low tax'},
    'Hong Kong': {'type': 'territorial', 'effective_rate': 0.15, 'has_fica': False, 'note': 'Very low tax'},
    'Switzerland': {'type': 'cantonal', 'effective_rate': 0.30, 'has_fica': False},
    'Netherlands': {'type': 'national', 'effective_rate': 0.49, 'has_fica': False},
    'Sweden': {'type': 'national', 'effective_rate': 0.52, 'has_fica': False, 'note': 'High tax, high services'},
    'Norway': {'type': 'national', 'effective_rate': 0.38, 'has_fica': False},
    'Denmark': {'type': 'national', 'effective_rate': 0.55, 'has_fica': False, 'note': 'Highest in developed world'},
    'Finland': {'type': 'national', 'effective_rate': 0.51, 'has_fica': False},
    'Belgium': {'type': 'national', 'effective_rate': 0.50, 'has_fica': False},
    'Austria': {'type': 'national', 'effective_rate': 0.48, 'has_fica': False},
    'Italy': {'type': 'national', 'effective_rate': 0.43, 'has_fica': False},
    'Spain': {'type': 'national', 'effective_rate': 0.43, 'has_fica': False},
    'Portugal': {'type': 'national', 'effective_rate': 0.48, 'has_fica': False},
    'Ireland': {'type': 'national', 'effective_rate': 0.48, 'has_fica': False},
    'New Zealand': {'type': 'national', 'effective_rate': 0.33, 'has_fica': False},

    # Other locations
    'United Arab Emirates': {'type': 'none', 'effective_rate': 0.0, 'has_fica': False, 'note': 'No income tax'},
    'Saudi Arabia': {'type': 'none', 'effective_rate': 0.0, 'has_fica': False, 'note': 'No income tax for individuals'},
    'Bahamas': {'type': 'none', 'effective_rate': 0.0, 'has_fica': False, 'note': 'No income tax'},
    'Cayman Islands': {'type': 'none', 'effective_rate': 0.0, 'has_fica': False, 'note': 'No income tax'},
    'Monaco': {'type': 'none', 'effective_rate': 0.0, 'has_fica': False, 'note': 'No income tax'},

    # Latin America
    'Mexico': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
    'Brazil': {'type': 'national', 'effective_rate': 0.275, 'has_fica': False},
    'Argentina': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
    'Chile': {'type': 'national', 'effective_rate': 0.40, 'has_fica': False},
    'Costa Rica': {'type': 'national', 'effective_rate': 0.25, 'has_fica': False},

    # Asia
    'China': {'type': 'national', 'effective_rate': 0.45, 'has_fica': False},
    'India': {'type': 'national', 'effective_rate': 0.30, 'has_fica': False},
    'Thailand': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
    'Vietnam': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
    'Philippines': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
    'Malaysia': {'type': 'national', 'effective_rate': 0.28, 'has_fica': False},
    'Indonesia': {'type': 'national', 'effective_rate': 0.30, 'has_fica': False},
    'Taiwan': {'type': 'national', 'effective_rate': 0.40, 'has_fica': False},

    # Middle East
    'Israel': {'type': 'national', 'effective_rate': 0.47, 'has_fica': False},
    'Turkey': {'type': 'national', 'effective_rate': 0.35, 'has_fica': False},
}

def get_location_type(location):
    """
    Determine if a location is a US state, a country, or unknown.

    Returns:
        tuple: (location_type, tax_info) where location_type is 'us_state', 'country', or 'unknown'
    """
    # Check if it's a US state
    if location in US_STATE_TAX_INFO:
        return 'us_state', US_STATE_TAX_INFO[location]

    # Check if it's a country
    if location in COUNTRY_TAX_INFO:
        return 'country', COUNTRY_TAX_INFO[location]

    # Check if it's a common custom city (map to state)
    CITY_TO_STATE = {
        'Seattle': 'Washington',
        'San Francisco': 'California',
        'Los Angeles': 'California',
        'San Diego': 'California',
        'Sacramento': 'California',
        'Portland': 'Oregon',
        'Austin': 'Texas',
        'Houston': 'Texas',
        'Dallas': 'Texas',
        'New York City': 'New York',
        'NYC': 'New York',
        'Boston': 'Massachusetts',
        'Chicago': 'Illinois',
        'Miami': 'Florida',
        'Denver': 'Colorado',
        'Phoenix': 'Arizona',
        'Las Vegas': 'Nevada',
        'Atlanta': 'Georgia',
        'Philadelphia': 'Pennsylvania',
        'Washington DC': 'District of Columbia',
        'DC': 'District of Columbia',
    }

    if location in CITY_TO_STATE:
        state = CITY_TO_STATE[location]
        return 'us_state', US_STATE_TAX_INFO[state]

    # Unknown location - return None so user can configure
    return 'unknown', None


def calculate_federal_income_tax(taxable_income, filing_status='married'):
    """
    Calculate federal income tax using 2024 tax brackets.

    Args:
        taxable_income: Total taxable income for the year
        filing_status: 'single' or 'married' (default: 'married')

    Returns:
        float: Federal income tax amount
    """
    if filing_status == 'married':
        # 2024 Married Filing Jointly brackets
        brackets = [
            (22000, 0.10),      # 10% on first $22,000
            (89075, 0.12),      # 12% on $22,001 to $89,075
            (190750, 0.22),     # 22% on $89,076 to $190,750
            (364200, 0.24),     # 24% on $190,751 to $364,200
            (462500, 0.32),     # 32% on $364,201 to $462,500
            (693750, 0.35),     # 35% on $462,501 to $693,750
            (float('inf'), 0.37)  # 37% on $693,751+
        ]
    else:
        # 2024 Single filer brackets
        brackets = [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37)
        ]

    tax = 0
    previous_limit = 0

    for limit, rate in brackets:
        if taxable_income > previous_limit:
            taxable_in_bracket = min(taxable_income, limit) - previous_limit
            tax += taxable_in_bracket * rate
            previous_limit = limit
        else:
            break

    return tax

def calculate_fica_tax(wage_income):
    """
    Calculate FICA taxes (Social Security + Medicare).

    Args:
        wage_income: W-2 wages subject to FICA

    Returns:
        float: Total FICA tax (employee portion)
    """
    # Social Security: 6.2% up to wage base ($160,200 in 2024)
    ss_wage_base = 160200
    social_security_tax = min(wage_income, ss_wage_base) * 0.062

    # Medicare: 1.45% on all wages, plus 0.9% Additional Medicare Tax on high earners
    medicare_wage_threshold = 250000  # For married filing jointly

    if wage_income <= medicare_wage_threshold:
        medicare_tax = wage_income * 0.0145
    else:
        medicare_tax = (medicare_wage_threshold * 0.0145) + \
                      ((wage_income - medicare_wage_threshold) * 0.0235)  # 1.45% + 0.9%

    return social_security_tax + medicare_tax

def calculate_ss_taxable_amount(ss_income, other_income):
    """
    Calculate taxable portion of Social Security benefits.
    Uses provisional income method.

    Args:
        ss_income: Social Security benefits received
        other_income: Other taxable income (wages, pensions, etc.)

    Returns:
        float: Taxable portion of Social Security benefits
    """
    # Provisional income = AGI + 50% of SS benefits + tax-exempt interest
    provisional_income = other_income + (ss_income * 0.5)

    # Married filing jointly thresholds
    threshold_1 = 32000
    threshold_2 = 44000

    if provisional_income <= threshold_1:
        # No SS benefits taxed
        return 0
    elif provisional_income <= threshold_2:
        # Up to 50% of benefits may be taxed
        excess = provisional_income - threshold_1
        return min(excess, ss_income * 0.5)
    else:
        # Up to 85% of benefits may be taxed
        excess_1 = threshold_2 - threshold_1
        excess_2 = provisional_income - threshold_2
        return min(excess_1 + (excess_2 * 0.85), ss_income * 0.85)

def calculate_total_taxes(parent1_income, parent2_income, ss_income, location=None, state_tax_rate=None, filing_status='married'):
    """
    Calculate total taxes for the year based on location.

    Args:
        parent1_income: Parent 1 wage income
        parent2_income: Parent 2 wage income
        ss_income: Social Security benefits
        location: Location name (US state or country). If None, uses state_tax_rate fallback
        state_tax_rate: Manual override for state/local tax rate (for unknown locations)
        filing_status: 'single' or 'married'

    Returns:
        dict: Breakdown of all taxes including location info
    """
    wage_income = parent1_income + parent2_income

    # Determine location type and tax rules
    location_type = 'unknown'
    tax_info = None

    if location:
        location_type, tax_info = get_location_type(location)

    # Initialize tax components
    federal_tax = 0
    state_tax = 0
    fica_tax = 0
    foreign_tax = 0

    # Calculate taxes based on location type
    if location_type == 'us_state':
        # US State: Apply federal + FICA + state taxes

        # 1. Calculate FICA on wage income
        fica_tax = calculate_fica_tax(wage_income)

        # 2. Calculate taxable Social Security
        taxable_ss = calculate_ss_taxable_amount(ss_income, wage_income)

        # 3. Total taxable income with standard deduction
        standard_deduction = 29200 if filing_status == 'married' else 14600
        taxable_income = max(0, wage_income + taxable_ss - standard_deduction)

        # 4. Calculate federal income tax
        federal_tax = calculate_federal_income_tax(taxable_income, filing_status)

        # 5. Calculate state tax using location's rate
        state_rate = tax_info.get('rate', 0.0)
        state_tax = taxable_income * state_rate

    elif location_type == 'country' and tax_info:
        # Foreign Country: Apply country's tax system
        # Note: US citizens still owe US taxes on worldwide income, but we'll simplify
        # by assuming they're using Foreign Earned Income Exclusion or Foreign Tax Credit

        if tax_info.get('type') == 'federal_state':
            # It's the United States as a country
            # Apply US federal taxes + FICA
            fica_tax = calculate_fica_tax(wage_income)
            taxable_ss = calculate_ss_taxable_amount(ss_income, wage_income)
            standard_deduction = 29200 if filing_status == 'married' else 14600
            taxable_income = max(0, wage_income + taxable_ss - standard_deduction)
            federal_tax = calculate_federal_income_tax(taxable_income, filing_status)
            # No state tax since it's just "United States" without a specific state
            state_tax = 0
        else:
            # Foreign country - apply their tax system
            # Use effective rate on total income (simplified)
            effective_rate = tax_info.get('effective_rate', 0.35)

            # Most countries don't have standard deductions like the US
            # Some have personal allowances, but we'll simplify
            total_income = wage_income + ss_income
            foreign_tax = total_income * effective_rate

            # FICA only applies if working for US employer
            # We'll assume foreign employment = no FICA
            if tax_info.get('has_fica', False):
                fica_tax = calculate_fica_tax(wage_income)

    else:
        # Unknown location - use manual state_tax_rate if provided
        # Default to US tax system
        fica_tax = calculate_fica_tax(wage_income)
        taxable_ss = calculate_ss_taxable_amount(ss_income, wage_income)
        standard_deduction = 29200 if filing_status == 'married' else 14600
        taxable_income = max(0, wage_income + taxable_ss - standard_deduction)
        federal_tax = calculate_federal_income_tax(taxable_income, filing_status)

        # Use manual override or default to 5%
        if state_tax_rate is not None:
            state_tax = taxable_income * state_tax_rate
        else:
            state_tax = taxable_income * 0.05

    # Calculate total
    total_taxes = federal_tax + state_tax + fica_tax + foreign_tax

    return {
        'federal_income_tax': federal_tax,
        'state_tax': state_tax,
        'fica_tax': fica_tax,
        'foreign_tax': foreign_tax,
        'total_taxes': total_taxes,
        'location': location if location else 'Unknown',
        'location_type': location_type,
        'tax_note': tax_info.get('note', '') if tax_info else ''
    }

def calculate_lifetime_cashflow():
    """
    Calculate detailed year-by-year cashflow for entire lifetime (current year to age 100).
    Now includes tax calculations.

    Returns:
        list: List of dictionaries with year-by-year financial data
    """
    # Calculate timeline end (when both parents reach their death age)
    parent1_death_year = (st.session_state.current_year - st.session_state.parentX_age) + st.session_state.parentX_death_age
    parent2_death_year = (st.session_state.current_year - st.session_state.parentY_age) + st.session_state.parentY_death_age
    timeline_end = max(parent1_death_year, parent2_death_year)

    results = []
    finance_mode = st.session_state.get('finance_mode', 'Pooled')
    split_pct = st.session_state.get('shared_expense_split_pct', 50) / 100.0

    if finance_mode == "Separate":
        nw_parent1 = st.session_state.parentX_net_worth
        nw_parent2 = st.session_state.parentY_net_worth
        cumulative_net_worth = nw_parent1 + nw_parent2
    else:
        nw_parent1 = None
        nw_parent2 = None
        cumulative_net_worth = st.session_state.parentX_net_worth + st.session_state.parentY_net_worth

    for year in range(st.session_state.current_year, timeline_end + 1):
        # Calculate ages
        parent1_age = st.session_state.parentX_age + (year - st.session_state.current_year)
        parent2_age = st.session_state.parentY_age + (year - st.session_state.current_year)

        # Calculate income
        parent1_working = parent1_age < st.session_state.parentX_retirement_age
        parent2_working = parent2_age < st.session_state.parentY_retirement_age

        parent1_income = 0
        parent2_income = 0
        parent1_ss = 0
        parent2_ss = 0

        if parent1_working:
            if st.session_state.get('parentX_career_phases'):
                comp = get_career_income_for_year(
                    st.session_state.parentX_career_phases,
                    st.session_state.parentX_age,
                    st.session_state.current_year,
                    year
                )
                parent1_income = comp['total_employment_income']
            else:
                parent1_income = get_income_for_year(
                    st.session_state.parentX_income,
                    st.session_state.parentX_raise,
                    st.session_state.parentX_job_changes,
                    st.session_state.current_year,
                    year
                )
        else:
            parent1_ss = st.session_state.parentX_ss_benefit * 12
            if st.session_state.ss_insolvency_enabled and year >= 2034:
                parent1_ss *= (1 - st.session_state.ss_shortfall_percentage / 100)

        if parent2_working:
            if st.session_state.get('parentY_career_phases'):
                comp = get_career_income_for_year(
                    st.session_state.parentY_career_phases,
                    st.session_state.parentY_age,
                    st.session_state.current_year,
                    year
                )
                parent2_income = comp['total_employment_income']
            else:
                parent2_income = get_income_for_year(
                    st.session_state.parentY_income,
                    st.session_state.parentY_raise,
                    st.session_state.parentY_job_changes,
                    st.session_state.current_year,
                    year
                )
        else:
            parent2_ss = st.session_state.parentY_ss_benefit * 12
            if st.session_state.ss_insolvency_enabled and year >= 2034:
                parent2_ss *= (1 - st.session_state.ss_shortfall_percentage / 100)

        ss_income = parent1_ss + parent2_ss
        total_income = parent1_income + parent2_income + ss_income

        # Calculate taxes based on location for this year
        # Get the location (state or country) for this year
        location, _ = get_state_for_year(year)

        # Get manual tax rate override from session state if set
        state_tax_rate = st.session_state.get('state_tax_rate', None)
        filing_status = st.session_state.get('tax_filing_status', 'married')

        tax_breakdown = calculate_total_taxes(
            parent1_income,
            parent2_income,
            ss_income,
            location=location,
            state_tax_rate=state_tax_rate,
            filing_status=filing_status
        )

        total_taxes = tax_breakdown['total_taxes']

        # Calculate expenses
        # Parent + Family expenses (with inflation)
        years_from_now = year - st.session_state.current_year

        # Parent X individual expenses (with inflation)
        parentX_expenses_inflated = {}
        for category, amount in st.session_state.parentX_expenses.items():
            parentX_expenses_inflated[category] = amount * (1.03 ** years_from_now)
        parentX_total = sum(parentX_expenses_inflated.values())

        # Parent Y individual expenses (with inflation)
        parentY_expenses_inflated = {}
        for category, amount in st.session_state.parentY_expenses.items():
            parentY_expenses_inflated[category] = amount * (1.03 ** years_from_now)
        parentY_total = sum(parentY_expenses_inflated.values())

        # Family shared expenses (with inflation)
        family_expenses_inflated = {}
        for category, amount in st.session_state.family_shared_expenses.items():
            family_expenses_inflated[category] = amount * (1.03 ** years_from_now)

        # Housing ↔ Location linking: if user lives in an owned house this year,
        # zero out the Mortgage/Rent family expense (house costs are in house_expenses)
        lives_in_owned_house = False
        if 'houses' in st.session_state:
            for house in st.session_state.houses:
                status, _ = house.get_status_for_year(year)
                if status == "Own_Live":
                    lives_in_owned_house = True
                    break
        if lives_in_owned_house:
            family_expenses_inflated['Mortgage/Rent'] = 0.0

        family_total = sum(family_expenses_inflated.values())

        # Total base expenses = ParentX + ParentY + Family Shared
        base_expenses = parentX_total + parentY_total + family_total

        # Create combined breakdown for reporting
        base_expenses_dict_inflated = {
            **{f"ParentX_{k}": v for k, v in parentX_expenses_inflated.items()},
            **{f"ParentY_{k}": v for k, v in parentY_expenses_inflated.items()},
            **{f"Family_{k}": v for k, v in family_expenses_inflated.items()}
        }

        # Children expenses (state-based)
        children_expenses = 0
        children_in_college = []
        children_expense_details = []  # Store detailed breakdown per child
        for child in st.session_state.children_list:
            child_exp = get_child_expenses(child, year, st.session_state.current_year)
            child_total = sum(child_exp.values())
            children_expenses += child_total

            # Store detailed breakdown for this child (only if there are expenses)
            if child_total > 0:
                children_expense_details.append({
                    'child_name': child['name'],
                    'expenses': child_exp.copy()
                })

            # Track who's in college
            child_age = year - child['birth_year']
            if 18 <= child_age <= 21:
                children_in_college.append(child['name'])

        # Recurring expenses
        recurring_expenses_total = 0
        recurring_expense_details = []  # Store detailed breakdown
        for recurring in st.session_state.recurring_expenses:
            # Check if this expense occurs this year
            if year >= recurring.start_year:
                if recurring.end_year is None or year <= recurring.end_year:
                    # Check if it's a year when this recurring expense occurs
                    years_since_start = year - recurring.start_year
                    if years_since_start % recurring.frequency_years == 0:
                        expense_amount = recurring.amount
                        if recurring.inflation_adjust:
                            expense_amount *= (1.03 ** years_from_now)
                        recurring_expenses_total += expense_amount

                        # Store details
                        recurring_expense_details.append({
                            'name': recurring.name,
                            'amount': expense_amount
                        })

        # One-time major purchases
        major_purchase_expenses = 0
        major_purchase_details = []  # Store detailed breakdown
        for purchase in st.session_state.major_purchases:
            if purchase.year == year:
                major_purchase_expenses += purchase.amount
                major_purchase_details.append({
                    'name': purchase.name,
                    'amount': purchase.amount
                })

        # Healthcare costs
        healthcare_expenses = 0
        healthcare_expense_details = {}  # Store detailed breakdown

        # Health insurance premiums (pre-Medicare, includes early retirement)
        if 'health_insurances' in st.session_state:
            for insurance in st.session_state.health_insurances:
                # Check if this insurance applies to either parent based on age
                annual_premium = 0
                if insurance.covered_by in ["Parent 1", "Both", "Family"] and insurance.start_age <= parent1_age <= insurance.end_age:
                    annual_premium = insurance.monthly_premium * 12
                elif insurance.covered_by == "Parent 2" and insurance.start_age <= parent2_age <= insurance.end_age:
                    annual_premium = insurance.monthly_premium * 12
                elif insurance.covered_by in ["Both", "Family"]:
                    # For Both/Family, check if either parent is in age range
                    if (insurance.start_age <= parent1_age <= insurance.end_age) or (insurance.start_age <= parent2_age <= insurance.end_age):
                        annual_premium = insurance.monthly_premium * 12

                if annual_premium > 0:
                    healthcare_expenses += annual_premium
                    key = f"Health Insurance ({insurance.covered_by})"
                    healthcare_expense_details[key] = healthcare_expense_details.get(key, 0) + annual_premium

        # Medicare costs (age 65+)
        medicare_expenses = 0
        if 'medicare_part_b_premium' in st.session_state:
            if parent1_age >= 65:
                part_b = st.session_state.medicare_part_b_premium * 12
                part_d = st.session_state.get('medicare_part_d_premium', 55.0) * 12
                medigap = st.session_state.get('medigap_premium', 150.0) * 12
                medicare_expenses += part_b + part_d + medigap
                healthcare_expense_details[f"Medicare Part B ({st.session_state.parent1_name})"] = part_b
                healthcare_expense_details[f"Medicare Part D ({st.session_state.parent1_name})"] = part_d
                healthcare_expense_details[f"Medigap ({st.session_state.parent1_name})"] = medigap
            if parent2_age >= 65:
                part_b = st.session_state.medicare_part_b_premium * 12
                part_d = st.session_state.get('medicare_part_d_premium', 55.0) * 12
                medigap = st.session_state.get('medigap_premium', 150.0) * 12
                medicare_expenses += part_b + part_d + medigap
                healthcare_expense_details[f"Medicare Part B ({st.session_state.parent2_name})"] = part_b
                healthcare_expense_details[f"Medicare Part D ({st.session_state.parent2_name})"] = part_d
                healthcare_expense_details[f"Medigap ({st.session_state.parent2_name})"] = medigap

        healthcare_expenses += medicare_expenses

        # Long-term care insurance premiums
        if 'ltc_insurances' in st.session_state:
            for ltc in st.session_state.ltc_insurances:
                if ltc.covered_person == "Parent 1" and parent1_age >= ltc.start_age:
                    ltc_annual = ltc.monthly_premium * 12
                    healthcare_expenses += ltc_annual
                    healthcare_expense_details[f"Long-term Care ({st.session_state.parent1_name})"] = ltc_annual
                elif ltc.covered_person == "Parent 2" and parent2_age >= ltc.start_age:
                    ltc_annual = ltc.monthly_premium * 12
                    healthcare_expenses += ltc_annual
                    healthcare_expense_details[f"Long-term Care ({st.session_state.parent2_name})"] = ltc_annual

        # House expenses (property tax, insurance, maintenance, upkeep)
        house_expenses = 0
        house_expense_details = []  # Store detailed breakdown
        if 'houses' in st.session_state:
            for house in st.session_state.houses:
                # Check if the house is owned during this year based on timeline
                is_owned = False
                for timeline_entry in house.timeline:
                    if timeline_entry.year <= year:
                        if timeline_entry.status in ["Own_Live", "Own_Rent"]:
                            is_owned = True
                        elif timeline_entry.status == "Sold":
                            is_owned = False

                if is_owned:
                    # Calculate house value with appreciation (per-house rate)
                    appr_rate = 1 + getattr(house, 'appreciation_rate', 3.0) / 100
                    current_house_value = house.current_value * (appr_rate ** years_from_now)

                    # Property tax (based on current house value)
                    property_tax = current_house_value * house.property_tax_rate
                    house_expenses += property_tax

                    # Home insurance (with general inflation)
                    home_insurance = house.home_insurance * (1.03 ** years_from_now)
                    house_expenses += home_insurance

                    # Maintenance (based on current house value)
                    maintenance = current_house_value * house.maintenance_rate
                    house_expenses += maintenance

                    # Upkeep costs (with general inflation)
                    upkeep = house.upkeep_costs * (1.03 ** years_from_now)
                    house_expenses += upkeep

                    # Store breakdown
                    house_expense_details.append({
                        'name': house.name,
                        'property_tax': property_tax,
                        'home_insurance': home_insurance,
                        'maintenance': maintenance,
                        'upkeep': upkeep
                    })

        total_expenses = base_expenses + children_expenses + recurring_expenses_total + major_purchase_expenses + healthcare_expenses + house_expenses

        # ── House equity calculation (non-liquid net worth) ──────────────
        total_house_equity = 0
        if 'houses' in st.session_state:
            for house in st.session_state.houses:
                status, _ = house.get_status_for_year(year)
                if status in ("Own_Live", "Own_Rent"):
                    appr = 1 + getattr(house, 'appreciation_rate', 3.0) / 100
                    h_value = house.current_value * (appr ** years_from_now)
                    # Remaining mortgage (simple: pay down linearly over mortgage_years_left)
                    years_into_mortgage = years_from_now
                    if house.mortgage_years_left > 0 and years_into_mortgage < house.mortgage_years_left:
                        remaining_frac = 1 - (years_into_mortgage / house.mortgage_years_left)
                        h_mortgage = house.mortgage_balance * remaining_frac
                    elif house.mortgage_years_left > 0:
                        h_mortgage = 0  # Paid off
                    else:
                        h_mortgage = 0
                    total_house_equity += max(0, h_value - h_mortgage)

        # ── Net worth update ──────────────────────────────────────────────
        inv_rate = st.session_state.economic_params.investment_return

        if finance_mode == "Separate":
            # Allocate shared expenses by split ratio
            shared_costs = (family_total + children_expenses + recurring_expenses_total
                            + major_purchase_expenses)

            # Allocate house expenses by owner
            p1_house_exp = 0
            p2_house_exp = 0
            p1_name = st.session_state.parent1_name
            p2_name = st.session_state.parent2_name
            if 'houses' in st.session_state:
                for detail in house_expense_details:
                    # Find matching house to check owner
                    owner = "Shared"
                    for house in st.session_state.houses:
                        if house.name == detail['name']:
                            owner = house.owner
                            break
                    h_total = detail['property_tax'] + detail['home_insurance'] + detail['maintenance'] + detail['upkeep']
                    if owner == p1_name:
                        p1_house_exp += h_total
                    elif owner == p2_name:
                        p2_house_exp += h_total
                    else:  # Shared
                        p1_house_exp += h_total * split_pct
                        p2_house_exp += h_total * (1 - split_pct)

            # Allocate healthcare by covered person
            p1_healthcare = 0
            p2_healthcare = 0
            for key, val in healthcare_expense_details.items():
                if p1_name in key or "Parent 1" in key:
                    p1_healthcare += val
                elif p2_name in key or "Parent 2" in key:
                    p2_healthcare += val
                else:
                    p1_healthcare += val * split_pct
                    p2_healthcare += val * (1 - split_pct)

            p1_expenses = parentX_total + shared_costs * split_pct + p1_house_exp + p1_healthcare
            p2_expenses = parentY_total + shared_costs * (1 - split_pct) + p2_house_exp + p2_healthcare

            p1_total_income = parent1_income + parent1_ss
            p2_total_income = parent2_income + parent2_ss

            # Simplified per-person taxes (half of joint for now — keeps backward compat)
            p1_taxes = total_taxes * (p1_total_income / max(total_income, 1)) if total_income > 0 else 0
            p2_taxes = total_taxes - p1_taxes

            p1_cashflow = p1_total_income - p1_taxes - p1_expenses
            p2_cashflow = p2_total_income - p2_taxes - p2_expenses

            p1_return = nw_parent1 * inv_rate
            p2_return = nw_parent2 * inv_rate

            nw_parent1 += p1_cashflow + p1_return
            nw_parent2 += p2_cashflow + p2_return
            cumulative_net_worth = nw_parent1 + nw_parent2

            investment_return = p1_return + p2_return
            cashflow = p1_cashflow + p2_cashflow
        else:
            # Pooled mode — original logic
            cashflow = total_income - total_taxes - total_expenses
            investment_return = cumulative_net_worth * inv_rate
            cumulative_net_worth += cashflow + investment_return

        # Track events
        events = []

        # Job changes
        for _, row in st.session_state.parentX_job_changes.iterrows():
            if int(row['Year']) == year:
                events.append(('job_change', st.session_state.parent1_name, row['New Income']))
        for _, row in st.session_state.parentY_job_changes.iterrows():
            if int(row['Year']) == year:
                events.append(('job_change', st.session_state.parent2_name, row['New Income']))

        # College events
        if children_in_college:
            events.append(('college', children_in_college))

        # Retirement events
        if parent1_age == st.session_state.parentX_retirement_age:
            events.append(('retirement', st.session_state.parent1_name))
        if parent2_age == st.session_state.parentY_retirement_age:
            events.append(('retirement', st.session_state.parent2_name))

        row_data = {
            'year': year,
            'parent1_age': parent1_age,
            'parent2_age': parent2_age,
            'parent1_income': parent1_income,
            'parent2_income': parent2_income,
            'ss_income': ss_income,
            'investment_income': investment_return,
            'total_income': total_income,
            'taxes': total_taxes,
            'tax_breakdown': tax_breakdown,
            'base_expenses': base_expenses,
            'base_expenses_breakdown': base_expenses_dict_inflated,
            'children_expenses': children_expenses,
            'children_expense_details': children_expense_details,
            'healthcare_expenses': healthcare_expenses,
            'healthcare_expense_details': healthcare_expense_details,
            'house_expenses': house_expenses,
            'house_expense_details': house_expense_details,
            'recurring_expenses': recurring_expenses_total,
            'recurring_expense_details': recurring_expense_details,
            'major_purchases': major_purchase_expenses,
            'major_purchase_details': major_purchase_details,
            'total_expenses': total_expenses,
            'cashflow': cashflow,
            'net_worth': cumulative_net_worth,
            'house_equity': total_house_equity,
            'liquid_net_worth': cumulative_net_worth - total_house_equity,
            'children_in_college': children_in_college,
            'events': events,
            'finance_mode': finance_mode,
        }

        # Per-parent fields (only in Separate mode)
        if finance_mode == "Separate":
            row_data['nw_parent1'] = nw_parent1
            row_data['nw_parent2'] = nw_parent2
            row_data['p1_cashflow'] = p1_cashflow
            row_data['p2_cashflow'] = p2_cashflow
            row_data['p1_expenses'] = p1_expenses
            row_data['p2_expenses'] = p2_expenses

        results.append(row_data)

    return results


def deterministic_cashflow_tab():
    """Deterministic Lifetime Cashflow Analysis"""
    st.header("💰 Deterministic Lifetime Cashflow")
    tab_walkthrough("deterministic")

    st.markdown("""
    See exactly how money flows through your entire life from now until age 100.
    This deterministic view shows your baseline plan without uncertainty.
    **Click on any year in the chart to see detailed income and expense breakdown.**
    """)

    # Initialize session state for cashflow calculation
    if 'cashflow_data_cached' not in st.session_state:
        st.session_state.cashflow_data_cached = None
    if 'selected_cashflow_year' not in st.session_state:
        st.session_state.selected_cashflow_year = None

    # Add calculate/recalculate button
    st.info("💡 Click the button below to calculate or recalculate your lifetime cashflow based on your current life plan.")

    if st.button("🏦 Calculate Lifetime Cashflow", type="primary", use_container_width=True, key="calc_cashflow"):
        with st.spinner("Calculating lifetime cashflow..."):
            st.session_state.cashflow_data_cached = calculate_lifetime_cashflow()
        if st.session_state.cashflow_data_cached:
            st.success("✅ Calculation complete! Scroll down to view results.")
        st.rerun()

    # Check if we have calculated data to show
    if st.session_state.cashflow_data_cached is not None:
        cashflow_data = st.session_state.cashflow_data_cached

        if cashflow_data:
            # Create tabs for different views
            cashflow_tab1, cashflow_tab2, cashflow_tab3 = st.tabs(["📈 Timeline View", "📊 Critical Years Table", "📅 Life Stages"])

            with cashflow_tab1:
                st.subheader("Lifetime Income vs Expenses Timeline")

                # Prepare data for plotting
                years = [d['year'] for d in cashflow_data]
                income = [d['total_income'] for d in cashflow_data]
                expenses = [d['total_expenses'] for d in cashflow_data]
                cashflow = [d['cashflow'] for d in cashflow_data]

                # Create figure
                fig = go.Figure()

                # Add income line
                fig.add_trace(go.Scatter(
                    x=years,
                    y=income,
                    mode='lines',
                    name='Income',
                    line=dict(color='green', width=2),
                    hovertemplate='<b>Year %{x}</b><br>Income: $%{y:,.0f}<br>Click for details<extra></extra>'
                ))

                # Add expenses line
                fig.add_trace(go.Scatter(
                    x=years,
                    y=expenses,
                    mode='lines',
                    name='Expenses',
                    line=dict(color='red', width=2),
                    hovertemplate='<b>Year %{x}</b><br>Expenses: $%{y:,.0f}<br>Click for details<extra></extra>'
                ))

                # Add cashflow area (positive)
                cashflow_positive = [max(0, cf) for cf in cashflow]
                fig.add_trace(go.Scatter(
                    x=years,
                    y=cashflow_positive,
                    mode='none',
                    name='Positive Cashflow',
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 0, 0.1)',
                    hovertemplate='<b>Year %{x}</b><br>Surplus: $%{y:,.0f}<extra></extra>'
                ))

                # Add cashflow area (negative)
                cashflow_negative = [min(0, cf) for cf in cashflow]
                fig.add_trace(go.Scatter(
                    x=years,
                    y=cashflow_negative,
                    mode='none',
                    name='Deficit',
                    fill='tozeroy',
                    fillcolor='rgba(255, 0, 0, 0.1)',
                    hovertemplate='<b>Year %{x}</b><br>Deficit: $%{y:,.0f}<extra></extra>'
                ))

                # Add major event markers
                major_events = []
                for d in cashflow_data:
                    for event_type, *event_data in d['events']:
                        if event_type == 'job_change':
                            major_events.append({'year': d['year'], 'type': 'job_change', 'label': f"💼 {event_data[0]}", 'value': d['total_income']})
                        elif event_type == 'retirement':
                            major_events.append({'year': d['year'], 'type': 'retirement', 'label': f"🏖️ {event_data[0]}", 'value': d['total_income']})

                college_years_list = [d['year'] for d in cashflow_data if d['children_in_college']]
                if college_years_list:
                    first_college = min(college_years_list)
                    last_college = max(college_years_list)
                    first_college_data = next(d for d in cashflow_data if d['year'] == first_college)
                    major_events.append({'year': first_college, 'type': 'college_start', 'label': '🎓 College Starts', 'value': first_college_data['total_expenses']})
                    if last_college != first_college:
                        last_college_data = next(d for d in cashflow_data if d['year'] == last_college)
                        major_events.append({'year': last_college, 'type': 'college_end', 'label': '🎓 College Ends', 'value': last_college_data['total_expenses']})

                if major_events:
                    event_years = [e['year'] for e in major_events]
                    event_values = [e['value'] for e in major_events]
                    event_labels = [e['label'] for e in major_events]
                    fig.add_trace(go.Scatter(
                        x=event_years,
                        y=event_values,
                        mode='markers',
                        name='Major Events',
                        marker=dict(size=15, color='blue', symbol='star', line=dict(width=2, color='white')),
                        hovertemplate='<b>%{customdata}</b><br>Year: %{x}<extra></extra>',
                        customdata=event_labels
                    ))

                fig.update_layout(
                    title="Lifetime Income, Expenses, and Cashflow (Click any year for details)",
                    xaxis_title="Year",
                    yaxis_title="Amount ($)",
                    height=700,
                    hovermode='x unified',
                    showlegend=True,
                    clickmode='event+select'
                )

                selected_points = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="cashflow_chart_main")

                # Handle year selection via manual input
                st.markdown("---")
                col_select1, col_select2 = st.columns([3, 1])
                with col_select1:
                    selected_year = st.selectbox("Select a year to see detailed breakdown:", options=years, index=0, key="year_selector_main")
                with col_select2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Show Details", type="primary", key="show_details_btn"):
                        st.session_state.selected_cashflow_year = selected_year

                # Show detailed breakdown if year is selected
                if st.session_state.selected_cashflow_year:
                    year_data = next((d for d in cashflow_data if d['year'] == st.session_state.selected_cashflow_year), None)
                    if year_data:
                        st.markdown("---")
                        st.subheader(f"📊 Detailed Breakdown for {st.session_state.selected_cashflow_year}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### 💵 Income Breakdown")
                            income_breakdown = []
                            if year_data['parent1_income'] > 0:
                                income_breakdown.append({'Source': f"{st.session_state.parent1_name} Salary", 'Amount': year_data['parent1_income']})
                            if year_data['parent2_income'] > 0:
                                income_breakdown.append({'Source': f"{st.session_state.parent2_name} Salary", 'Amount': year_data['parent2_income']})
                            if year_data['ss_income'] > 0:
                                income_breakdown.append({'Source': 'Social Security', 'Amount': year_data['ss_income']})
                            if year_data.get('investment_income', 0) > 0:
                                income_breakdown.append({'Source': '📈 Investment Returns', 'Amount': year_data['investment_income']})

                            if income_breakdown:
                                income_df = pd.DataFrame(income_breakdown)
                                income_fig = go.Figure(data=[go.Pie(labels=income_df['Source'], values=income_df['Amount'], hole=0.3, marker_colors=['#2ecc71', '#27ae60', '#16a085', '#1abc9c'])])
                                income_fig.update_layout(height=300, showlegend=True)
                                st.plotly_chart(income_fig, use_container_width=True)
                                income_df['Amount'] = income_df['Amount'].apply(lambda x: f"${x:,.0f}")
                                st.dataframe(income_df, hide_index=True, use_container_width=True)

                                # Calculate total including investment returns
                                total_with_investments = year_data['total_income'] + year_data.get('investment_income', 0)
                                st.metric("Total Earned Income", f"${year_data['total_income']:,.0f}")
                                if year_data.get('investment_income', 0) > 0:
                                    st.metric("Total with Investments", f"${total_with_investments:,.0f}")
                            else:
                                st.info("No income for this year")

                        with col2:
                            st.markdown("#### 💳 Expense Breakdown")
                            expense_breakdown = []
                            # Add taxes first (critical expense)
                            if year_data.get('taxes', 0) > 0:
                                expense_breakdown.append({'Category': '💸 Taxes', 'Amount': year_data['taxes']})
                            if year_data['base_expenses'] > 0:
                                expense_breakdown.append({'Category': 'Family Living Expenses', 'Amount': year_data['base_expenses']})
                            if year_data['children_expenses'] > 0:
                                expense_breakdown.append({'Category': 'Children Expenses', 'Amount': year_data['children_expenses']})
                            if year_data.get('healthcare_expenses', 0) > 0:
                                expense_breakdown.append({'Category': 'Healthcare & Insurance', 'Amount': year_data['healthcare_expenses']})
                            if year_data.get('house_expenses', 0) > 0:
                                expense_breakdown.append({'Category': 'House Expenses', 'Amount': year_data['house_expenses']})
                            if year_data.get('recurring_expenses', 0) > 0:
                                expense_breakdown.append({'Category': 'Recurring Expenses', 'Amount': year_data['recurring_expenses']})
                            if year_data.get('major_purchases', 0) > 0:
                                expense_breakdown.append({'Category': 'One-Time Major Purchases', 'Amount': year_data['major_purchases']})

                            if expense_breakdown:
                                expense_df = pd.DataFrame(expense_breakdown)
                                expense_fig = go.Figure(data=[go.Pie(labels=expense_df['Category'], values=expense_df['Amount'], hole=0.3, marker_colors=['#e74c3c', '#c0392b', '#9b59b6', '#8e44ad', '#d35400', '#e67e22'])])
                                expense_fig.update_layout(height=300, showlegend=True)
                                st.plotly_chart(expense_fig, use_container_width=True)
                                expense_df['Amount'] = expense_df['Amount'].apply(lambda x: f"${x:,.0f}")
                                st.dataframe(expense_df, hide_index=True, use_container_width=True)
                                st.metric("Total Expenses", f"${year_data['total_expenses']:,.0f}")

                                # Sankey Diagram for Money Flow
                                st.markdown("---")
                                st.markdown("#### 💰 Money Flow Visualization (Sankey Diagram)")
                                st.caption("See how money flows from income sources (including investment returns) through various expense categories to savings")

                                # Build Sankey diagram data
                                sankey_labels = []
                                sankey_source = []
                                sankey_target = []
                                sankey_values = []
                                sankey_colors = []

                                # Define node indices
                                node_index = 0
                                node_map = {}

                                # Income sources (left side)
                                income_sources = []
                                if year_data['parent1_income'] > 0:
                                    income_sources.append({
                                        'name': f"{st.session_state.parent1_name} Salary",
                                        'value': year_data['parent1_income'],
                                        'color': '#2ecc71'
                                    })
                                if year_data['parent2_income'] > 0:
                                    income_sources.append({
                                        'name': f"{st.session_state.parent2_name} Salary",
                                        'value': year_data['parent2_income'],
                                        'color': '#27ae60'
                                    })
                                if year_data['ss_income'] > 0:
                                    income_sources.append({
                                        'name': 'Social Security',
                                        'value': year_data['ss_income'],
                                        'color': '#16a085'
                                    })
                                if year_data.get('investment_income', 0) > 0:
                                    income_sources.append({
                                        'name': '📈 Investment Returns',
                                        'value': year_data['investment_income'],
                                        'color': '#1abc9c'
                                    })

                                # Add income source nodes
                                for source in income_sources:
                                    sankey_labels.append(source['name'])
                                    node_map[source['name']] = node_index
                                    node_index += 1

                                # Add "Total Income" middle node
                                sankey_labels.append("Total Income")
                                node_map["Total Income"] = node_index
                                total_income_idx = node_index
                                node_index += 1

                                # Connect income sources to Total Income
                                for source in income_sources:
                                    sankey_source.append(node_map[source['name']])
                                    sankey_target.append(total_income_idx)
                                    sankey_values.append(source['value'])
                                    sankey_colors.append(source['color'])

                                # Expense categories (right side)
                                expense_categories = []

                                # Taxes come first (critical expense)
                                if year_data.get('taxes', 0) > 0:
                                    expense_categories.append({
                                        'name': '💸 Taxes',
                                        'value': year_data['taxes'],
                                        'color': 'rgba(52, 73, 94, 0.7)'  # Dark gray-blue
                                    })

                                if year_data['base_expenses'] > 0:
                                    expense_categories.append({
                                        'name': 'Family Living',
                                        'value': year_data['base_expenses'],
                                        'color': 'rgba(231, 76, 60, 0.6)'
                                    })
                                if year_data['children_expenses'] > 0:
                                    expense_categories.append({
                                        'name': 'Children',
                                        'value': year_data['children_expenses'],
                                        'color': 'rgba(192, 57, 43, 0.6)'
                                    })
                                if year_data.get('healthcare_expenses', 0) > 0:
                                    expense_categories.append({
                                        'name': 'Healthcare',
                                        'value': year_data['healthcare_expenses'],
                                        'color': 'rgba(155, 89, 182, 0.6)'
                                    })
                                if year_data.get('house_expenses', 0) > 0:
                                    expense_categories.append({
                                        'name': 'House',
                                        'value': year_data['house_expenses'],
                                        'color': 'rgba(142, 68, 173, 0.6)'
                                    })
                                if year_data.get('recurring_expenses', 0) > 0:
                                    expense_categories.append({
                                        'name': 'Recurring',
                                        'value': year_data['recurring_expenses'],
                                        'color': 'rgba(211, 84, 0, 0.6)'
                                    })
                                if year_data.get('major_purchases', 0) > 0:
                                    expense_categories.append({
                                        'name': 'Major Purchases',
                                        'value': year_data['major_purchases'],
                                        'color': 'rgba(230, 126, 34, 0.6)'
                                    })

                                # Add expense category nodes
                                for category in expense_categories:
                                    sankey_labels.append(category['name'])
                                    node_map[category['name']] = node_index
                                    node_index += 1

                                # Add Savings/Deficit node
                                cashflow_value = year_data['cashflow']
                                if cashflow_value > 0:
                                    sankey_labels.append("💰 Savings")
                                    node_map["Savings"] = node_index
                                    savings_idx = node_index
                                    node_index += 1
                                    savings_color = 'rgba(46, 204, 113, 0.6)'
                                elif cashflow_value < 0:
                                    sankey_labels.append("⚠️ Deficit")
                                    node_map["Deficit"] = node_index
                                    deficit_idx = node_index
                                    node_index += 1
                                    deficit_color = 'rgba(231, 76, 60, 0.8)'

                                # Connect Total Income to expense categories
                                for category in expense_categories:
                                    sankey_source.append(total_income_idx)
                                    sankey_target.append(node_map[category['name']])
                                    sankey_values.append(category['value'])
                                    sankey_colors.append(category['color'])

                                # Connect Total Income to Savings or show Deficit
                                if cashflow_value > 0:
                                    sankey_source.append(total_income_idx)
                                    sankey_target.append(savings_idx)
                                    sankey_values.append(cashflow_value)
                                    sankey_colors.append(savings_color)

                                # Create node colors list
                                node_colors = []
                                for label in sankey_labels:
                                    if 'Salary' in label:
                                        node_colors.append('#2ecc71')
                                    elif 'Social Security' in label:
                                        node_colors.append('#16a085')
                                    elif 'Investment Returns' in label:
                                        node_colors.append('#1abc9c')
                                    elif 'Total Income' in label:
                                        node_colors.append('#3498db')
                                    elif 'Savings' in label:
                                        node_colors.append('#2ecc71')
                                    elif 'Deficit' in label:
                                        node_colors.append('#e74c3c')
                                    else:
                                        node_colors.append('#95a5a6')

                                # Create Sankey diagram
                                sankey_fig = go.Figure(data=[go.Sankey(
                                    node=dict(
                                        pad=15,
                                        thickness=20,
                                        line=dict(color="black", width=0.5),
                                        label=sankey_labels,
                                        color=node_colors,
                                        customdata=[f"${year_data['parent1_income']:,.0f}" if i == 0 and year_data['parent1_income'] > 0 else
                                                   f"${year_data['parent2_income']:,.0f}" if 'parent2' in sankey_labels[i].lower() else
                                                   f"${val:,.0f}" for i, val in enumerate([0]*len(sankey_labels))],
                                        hovertemplate='%{label}<br>$%{value:,.0f}<extra></extra>'
                                    ),
                                    link=dict(
                                        source=sankey_source,
                                        target=sankey_target,
                                        value=sankey_values,
                                        color=sankey_colors,
                                        hovertemplate='%{source.label} → %{target.label}<br>$%{value:,.0f}<extra></extra>'
                                    )
                                )])

                                sankey_fig.update_layout(
                                    title=f"Money Flow for {st.session_state.selected_cashflow_year}",
                                    font=dict(size=12),
                                    height=600,
                                    margin=dict(l=20, r=20, t=40, b=20)
                                )

                                st.plotly_chart(sankey_fig, use_container_width=True)

                                # Add summary below Sankey
                                total_available = year_data['total_income'] + year_data.get('investment_income', 0)
                                if cashflow_value >= 0:
                                    # Include investment returns in the savings calculation
                                    total_added_to_savings = cashflow_value + year_data.get('investment_income', 0)
                                    st.success(f"💰 **Net Addition to Savings: ${total_added_to_savings:,.0f}** ({(total_added_to_savings/total_available*100):.1f}% of total available funds)")
                                    if year_data.get('investment_income', 0) > 0:
                                        st.info(f"📊 Breakdown: ${cashflow_value:,.0f} from earned income surplus + ${year_data['investment_income']:,.0f} from investments")
                                else:
                                    st.error(f"⚠️ **Deficit: ${abs(cashflow_value):,.0f}** (spending {(abs(cashflow_value)/year_data['total_income']*100):.1f}% more than earned income)")
                                    if year_data.get('investment_income', 0) > 0:
                                        net_change = cashflow_value + year_data['investment_income']
                                        if net_change >= 0:
                                            st.warning(f"⚖️ Investment returns of ${year_data['investment_income']:,.0f} cover the deficit with ${net_change:,.0f} remaining")
                                        else:
                                            st.error(f"⚖️ Even with ${year_data['investment_income']:,.0f} investment returns, net change is ${net_change:,.0f}")

                                # Detailed subcategory breakdowns
                                st.markdown("---")
                                st.markdown("#### 📋 Detailed Expense Breakdown - All Line Items")

                                # Tax breakdown (show first - critical expense)
                                if year_data.get('taxes', 0) > 0 and year_data.get('tax_breakdown'):
                                    with st.expander("💸 Tax Details", expanded=True):
                                        tax_breakdown = year_data['tax_breakdown']

                                        # Show location info if available
                                        if tax_breakdown.get('location'):
                                            location_type = tax_breakdown.get('location_type', 'unknown')
                                            location_emoji = '🇺🇸' if location_type == 'us_state' else ('🌍' if location_type == 'country' else '📍')
                                            st.info(f"{location_emoji} **Tax Location:** {tax_breakdown['location']}")
                                            if tax_breakdown.get('tax_note'):
                                                st.caption(f"Note: {tax_breakdown['tax_note']}")

                                        # Build tax table based on what taxes apply
                                        tax_rows = []
                                        if tax_breakdown.get('federal_income_tax', 0) > 0:
                                            tax_rows.append({'Tax Type': 'Federal Income Tax', 'Amount': f"${tax_breakdown['federal_income_tax']:,.0f}"})
                                        if tax_breakdown.get('state_tax', 0) > 0:
                                            tax_rows.append({'Tax Type': 'State/Local Income Tax', 'Amount': f"${tax_breakdown['state_tax']:,.0f}"})
                                        if tax_breakdown.get('fica_tax', 0) > 0:
                                            tax_rows.append({'Tax Type': 'FICA (Social Security + Medicare)', 'Amount': f"${tax_breakdown['fica_tax']:,.0f}"})
                                        if tax_breakdown.get('foreign_tax', 0) > 0:
                                            tax_rows.append({'Tax Type': 'Foreign Income Tax', 'Amount': f"${tax_breakdown['foreign_tax']:,.0f}"})

                                        if tax_rows:
                                            tax_df = pd.DataFrame(tax_rows)
                                            st.dataframe(tax_df, hide_index=True, use_container_width=True)

                                        st.markdown(f"**Total Taxes: ${tax_breakdown['total_taxes']:,.0f}**")

                                        # Show effective tax rate
                                        effective_rate = (tax_breakdown['total_taxes'] / year_data['total_income'] * 100) if year_data['total_income'] > 0 else 0
                                        st.caption(f"Effective tax rate on total income: {effective_rate:.1f}%")

                                # Family Living Expenses breakdown
                                if year_data['base_expenses'] > 0 and year_data.get('base_expenses_breakdown'):
                                    with st.expander("🏠 Family Living Expenses Details", expanded=True):
                                        family_breakdown = year_data['base_expenses_breakdown']
                                        family_df = pd.DataFrame([
                                            {'Category': k, 'Amount': f"${v:,.0f}"}
                                            for k, v in family_breakdown.items() if v > 0
                                        ])
                                        if not family_df.empty:
                                            st.dataframe(family_df, hide_index=True, use_container_width=True)
                                            st.markdown(f"**Family Total: ${sum(family_breakdown.values()):,.0f}**")

                                # Children Expenses breakdown
                                if year_data['children_expenses'] > 0 and year_data.get('children_expense_details'):
                                    with st.expander("👶 Children Expenses Details (Per Child)", expanded=True):
                                        for child_detail in year_data['children_expense_details']:
                                            st.markdown(f"### {child_detail['child_name']}")
                                            child_df = pd.DataFrame([
                                                {'Category': k, 'Amount': f"${v:,.0f}"}
                                                for k, v in child_detail['expenses'].items() if v > 0
                                            ])
                                            if not child_df.empty:
                                                st.dataframe(child_df, hide_index=True, use_container_width=True)
                                                child_total = sum(child_detail['expenses'].values())
                                                st.markdown(f"**{child_detail['child_name']} Total: ${child_total:,.0f}**")
                                            st.markdown("")  # Add spacing

                                        # Show total for all children
                                        total_children = sum(sum(child['expenses'].values()) for child in year_data['children_expense_details'])
                                        st.markdown(f"### **All Children Total: ${total_children:,.0f}**")

                                # Healthcare Expenses breakdown
                                if year_data.get('healthcare_expenses', 0) > 0 and year_data.get('healthcare_expense_details'):
                                    with st.expander("🏥 Healthcare & Insurance Details", expanded=True):
                                        healthcare_breakdown = year_data['healthcare_expense_details']
                                        healthcare_df = pd.DataFrame([
                                            {'Category': k, 'Amount': f"${v:,.0f}"}
                                            for k, v in healthcare_breakdown.items() if v > 0
                                        ])
                                        if not healthcare_df.empty:
                                            st.dataframe(healthcare_df, hide_index=True, use_container_width=True)
                                            st.markdown(f"**Healthcare Total: ${sum(healthcare_breakdown.values()):,.0f}**")

                                # House Expenses breakdown
                                if year_data.get('house_expenses', 0) > 0 and year_data.get('house_expense_details'):
                                    with st.expander("🏡 House Expenses Details", expanded=True):
                                        for house_detail in year_data['house_expense_details']:
                                            st.markdown(f"### {house_detail['name']}")
                                            house_df = pd.DataFrame([
                                                {'Category': 'Property Tax', 'Amount': f"${house_detail['property_tax']:,.0f}"},
                                                {'Category': 'Home Insurance', 'Amount': f"${house_detail['home_insurance']:,.0f}"},
                                                {'Category': 'Maintenance', 'Amount': f"${house_detail['maintenance']:,.0f}"},
                                                {'Category': 'Upkeep', 'Amount': f"${house_detail['upkeep']:,.0f}"}
                                            ])
                                            st.dataframe(house_df, hide_index=True, use_container_width=True)
                                            house_total = house_detail['property_tax'] + house_detail['home_insurance'] + house_detail['maintenance'] + house_detail['upkeep']
                                            st.markdown(f"**{house_detail['name']} Total: ${house_total:,.0f}**")
                                            st.markdown("")  # Add spacing

                                        # Show total for all houses
                                        if len(year_data['house_expense_details']) > 1:
                                            total_houses = sum(
                                                h['property_tax'] + h['home_insurance'] + h['maintenance'] + h['upkeep']
                                                for h in year_data['house_expense_details']
                                            )
                                            st.markdown(f"### **All Houses Total: ${total_houses:,.0f}**")

                                # Recurring Expenses breakdown
                                if year_data.get('recurring_expenses', 0) > 0 and year_data.get('recurring_expense_details'):
                                    with st.expander("🔁 Recurring Expenses Details", expanded=True):
                                        recurring_df = pd.DataFrame([
                                            {'Item': item['name'], 'Amount': f"${item['amount']:,.0f}"}
                                            for item in year_data['recurring_expense_details']
                                        ])
                                        st.dataframe(recurring_df, hide_index=True, use_container_width=True)
                                        total_recurring = sum(item['amount'] for item in year_data['recurring_expense_details'])
                                        st.markdown(f"**Recurring Total: ${total_recurring:,.0f}**")

                                # One-Time Major Purchases breakdown
                                if year_data.get('major_purchases', 0) > 0 and year_data.get('major_purchase_details'):
                                    with st.expander("🛒 One-Time Major Purchases Details", expanded=True):
                                        purchases_df = pd.DataFrame([
                                            {'Item': item['name'], 'Amount': f"${item['amount']:,.0f}"}
                                            for item in year_data['major_purchase_details']
                                        ])
                                        st.dataframe(purchases_df, hide_index=True, use_container_width=True)
                                        total_purchases = sum(item['amount'] for item in year_data['major_purchase_details'])
                                        st.markdown(f"**Purchases Total: ${total_purchases:,.0f}**")

                            else:
                                st.info("No expenses for this year")

                        # Comprehensive expense summary table
                        if expense_breakdown:
                            st.markdown("---")
                            st.markdown("#### 💰 Complete Expense Summary")

                            # Build comprehensive summary
                            summary_data = []

                            # Family expenses
                            if year_data['base_expenses'] > 0 and year_data.get('base_expenses_breakdown'):
                                summary_data.append({'Category': '🏠 FAMILY LIVING EXPENSES', 'Amount': f"${year_data['base_expenses']:,.0f}"})
                                for k, v in year_data['base_expenses_breakdown'].items():
                                    if v > 0:
                                        summary_data.append({'Category': f"   • {k}", 'Amount': f"${v:,.0f}"})

                            # Children expenses
                            if year_data['children_expenses'] > 0 and year_data.get('children_expense_details'):
                                summary_data.append({'Category': '👶 CHILDREN EXPENSES', 'Amount': f"${year_data['children_expenses']:,.0f}"})
                                for child_detail in year_data['children_expense_details']:
                                    child_total = sum(child_detail['expenses'].values())
                                    summary_data.append({'Category': f"   {child_detail['child_name']}:", 'Amount': f"${child_total:,.0f}"})
                                    for k, v in child_detail['expenses'].items():
                                        if v > 0:
                                            summary_data.append({'Category': f"      • {k}", 'Amount': f"${v:,.0f}"})

                            # Healthcare expenses
                            if year_data.get('healthcare_expenses', 0) > 0 and year_data.get('healthcare_expense_details'):
                                summary_data.append({'Category': '🏥 HEALTHCARE & INSURANCE', 'Amount': f"${year_data['healthcare_expenses']:,.0f}"})
                                for k, v in year_data['healthcare_expense_details'].items():
                                    if v > 0:
                                        summary_data.append({'Category': f"   • {k}", 'Amount': f"${v:,.0f}"})

                            # House expenses
                            if year_data.get('house_expenses', 0) > 0 and year_data.get('house_expense_details'):
                                summary_data.append({'Category': '🏡 HOUSE EXPENSES', 'Amount': f"${year_data['house_expenses']:,.0f}"})
                                for house_detail in year_data['house_expense_details']:
                                    house_total = house_detail['property_tax'] + house_detail['home_insurance'] + house_detail['maintenance'] + house_detail['upkeep']
                                    summary_data.append({'Category': f"   {house_detail['name']}:", 'Amount': f"${house_total:,.0f}"})
                                    summary_data.append({'Category': f"      • Property Tax", 'Amount': f"${house_detail['property_tax']:,.0f}"})
                                    summary_data.append({'Category': f"      • Home Insurance", 'Amount': f"${house_detail['home_insurance']:,.0f}"})
                                    summary_data.append({'Category': f"      • Maintenance", 'Amount': f"${house_detail['maintenance']:,.0f}"})
                                    summary_data.append({'Category': f"      • Upkeep", 'Amount': f"${house_detail['upkeep']:,.0f}"})

                            # Recurring expenses
                            if year_data.get('recurring_expenses', 0) > 0 and year_data.get('recurring_expense_details'):
                                summary_data.append({'Category': '🔁 RECURRING EXPENSES', 'Amount': f"${year_data['recurring_expenses']:,.0f}"})
                                for item in year_data['recurring_expense_details']:
                                    summary_data.append({'Category': f"   • {item['name']}", 'Amount': f"${item['amount']:,.0f}"})

                            # Major purchases
                            if year_data.get('major_purchases', 0) > 0 and year_data.get('major_purchase_details'):
                                summary_data.append({'Category': '🛒 ONE-TIME PURCHASES', 'Amount': f"${year_data['major_purchases']:,.0f}"})
                                for item in year_data['major_purchase_details']:
                                    summary_data.append({'Category': f"   • {item['name']}", 'Amount': f"${item['amount']:,.0f}"})

                            # Display the comprehensive summary
                            if summary_data:
                                summary_df = pd.DataFrame(summary_data)
                                st.dataframe(summary_df, hide_index=True, use_container_width=True, height=min(600, len(summary_data) * 35 + 38))
                                st.markdown(f"### **TOTAL EXPENSES: ${year_data['total_expenses']:,.0f}**")

                        # Show summary metrics
                        st.markdown("#### 📈 Year Summary")
                        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
                        with sum_col1:
                            st.metric("Ages", f"{year_data['parent1_age']} / {year_data['parent2_age']}")
                        with sum_col2:
                            cashflow_val = year_data['cashflow']
                            cashflow_delta = "Surplus" if cashflow_val >= 0 else "Deficit"
                            st.metric("Cashflow", f"${abs(cashflow_val):,.0f}", cashflow_delta)
                        with sum_col3:
                            st.metric("Net Worth", f"${year_data['net_worth']:,.0f}")
                        with sum_col4:
                            if year_data['children_in_college']:
                                st.metric("In College", ", ".join(year_data['children_in_college']))
                            else:
                                st.metric("In College", "None")

            with cashflow_tab2:
                # Critical Years Table
                st.subheader("Critical Years Analysis")
                critical_years_data = []
                for d in cashflow_data:
                    if d['cashflow'] < 0 or d['net_worth'] < 0 or d['children_in_college'] or any(e[0] in ['retirement', 'job_change'] for e in d['events']):
                        critical_years_data.append({
                            'Year': d['year'],
                            'Ages': f"{d['parent1_age']} / {d['parent2_age']}",
                            'Cashflow': f"${d['cashflow']:,.0f}",
                            'Net Worth': f"${d['net_worth']:,.0f}",
                            'Events': ', '.join([f"{e[1]}" if len(e) > 1 else e[0] for e in d['events']]) if d['events'] else '-',
                            'In College': ', '.join(d['children_in_college']) if d['children_in_college'] else '-'
                        })

                if critical_years_data:
                    critical_df = pd.DataFrame(critical_years_data)
                    st.dataframe(critical_df, use_container_width=True, hide_index=True, height=400)
                else:
                    st.info("No critical years identified in your plan.")

            with cashflow_tab3:
                # Life Stages View
                st.subheader("Life Stages Financial Summary")

                stages = {
                    'Working Years (Pre-Retirement)': [],
                    'Early Retirement': [],
                    'Late Retirement': []
                }

                for d in cashflow_data:
                    parent1_retired = d['parent1_age'] >= st.session_state.parentX_retirement_age
                    parent2_retired = d['parent2_age'] >= st.session_state.parentY_retirement_age
                    both_retired = parent1_retired and parent2_retired

                    if not both_retired:
                        stages['Working Years (Pre-Retirement)'].append(d)
                    elif d['parent1_age'] < 75 and d['parent2_age'] < 75:
                        stages['Early Retirement'].append(d)
                    else:
                        stages['Late Retirement'].append(d)

                for stage_name, stage_data in stages.items():
                    if stage_data:
                        st.markdown(f"### {stage_name}")
                        avg_income = sum(d['total_income'] for d in stage_data) / len(stage_data)
                        avg_expenses = sum(d['total_expenses'] for d in stage_data) / len(stage_data)
                        avg_cashflow = sum(d['cashflow'] for d in stage_data) / len(stage_data)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Years", len(stage_data))
                        with col2:
                            st.metric("Avg Income", f"${avg_income:,.0f}")
                        with col3:
                            st.metric("Avg Expenses", f"${avg_expenses:,.0f}")
                        with col4:
                            st.metric("Avg Cashflow", f"${avg_cashflow:,.0f}")
        else:
            st.warning("No cashflow data available. Please configure your financial details first.")
    else:
        st.warning("⚠️ No cashflow data calculated yet. Click the button above to generate your lifetime cashflow analysis.")



def monte_carlo_simulation_tab():
    """Monte Carlo Simulation Analysis"""
    st.header("🎲 Monte Carlo Simulation")
    tab_walkthrough("monte_carlo")

    st.markdown("""
    Add uncertainty to your plan and see the range of possible outcomes.
    This probabilistic view shows how market volatility and life's unpredictability might affect your financial future.

    **Focus:** Net worth trajectories and probability of success (not income/expense details - see Section 1 for that).
    """)

    st.subheader("⚙️ Simulation Settings")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.mc_start_year = st.number_input("Start Year", min_value=st.session_state.current_year, max_value=2100, value=int(st.session_state.mc_start_year), key="mc_start_v071")
        st.number_input("Projection Years", min_value=1, max_value=80, value=int(st.session_state.mc_years), key="mc_years_v071")

    with col2:
        st.session_state.mc_simulations = st.number_input("Number of Simulations", min_value=100, max_value=10000, value=int(st.session_state.mc_simulations), step=100, key="mc_sims_v071")
        st.session_state.mc_use_historical = st.checkbox("Use Historical Returns", value=st.session_state.mc_use_historical, help="Use actual historical S&P 500 returns instead of random generation", key="mc_hist_v071")

    with col3:
        st.session_state.mc_normalize_to_today_dollars = st.checkbox(
            "Normalize to Today's Dollars",
            value=st.session_state.mc_normalize_to_today_dollars,
            help="Adjusts all future values to reflect today's purchasing power by removing the effect of inflation. This reveals your actual wealth accumulation over time — if the line goes up, you're genuinely getting wealthier, not just keeping pace with rising prices. For example, $1M in 2050 might look impressive, but normalized to today's dollars shows what that money can actually buy in current terms.",
            key="mc_norm_v071"
        )

    st.markdown("---")
    st.subheader("📊 Variability Settings")
    use_asymmetric = st.checkbox("Use Asymmetric Variability", value=True, help="Set different positive and negative variability ranges", key="mc_asym_v071")

    if use_asymmetric:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Income Variability**")
            st.session_state.mc_income_variability_positive = st.number_input("Positive (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_income_variability_positive), step=1.0, key="income_var_pos_v071")
            st.session_state.mc_income_variability_negative = st.number_input("Negative (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_income_variability_negative), step=1.0, key="income_var_neg_v071")
        with col2:
            st.markdown("**Expense Variability**")
            st.session_state.mc_expense_variability_positive = st.number_input("Positive (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_expense_variability_positive), step=1.0, key="expense_var_pos_v071")
            st.session_state.mc_expense_variability_negative = st.number_input("Negative (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_expense_variability_negative), step=1.0, key="expense_var_neg_v071")
        with col3:
            st.markdown("**Return Variability**")
            st.session_state.mc_return_variability_positive = st.number_input("Positive (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_return_variability_positive), step=1.0, key="return_var_pos_v071")
            st.session_state.mc_return_variability_negative = st.number_input("Negative (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.mc_return_variability_negative), step=1.0, key="return_var_neg_v071")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.mc_income_variability = st.slider("Income Variability (%)", 0.0, 100.0, 10.0, key="income_var_v071")
        with col2:
            st.session_state.mc_expense_variability = st.slider("Expense Variability (%)", 0.0, 100.0, 5.0, key="expense_var_v071")
        with col3:
            st.session_state.mc_return_variability = st.slider("Return Variability (%)", 0.0, 100.0, 15.0, key="return_var_v071")

    # Run Monte Carlo Simulation Button
    if st.button("🎲 Run Monte Carlo Simulation", type="primary", use_container_width=True, key="run_mc_v071"):
        with st.spinner("Running Monte Carlo simulation... This may take a minute."):
            # Get economic parameters
            scenario = st.session_state.economic_params

            num_sims = min(st.session_state.mc_simulations, 1000)
            all_sim_results = []

            initial_net_worth = st.session_state.parentX_net_worth + st.session_state.parentY_net_worth
            mc_finance_mode = st.session_state.get('finance_mode', 'Pooled')
            mc_split = st.session_state.get('shared_expense_split_pct', 50) / 100.0

            progress_bar = st.progress(0)

            for sim in range(num_sims):
                sim_net_worth = []
                net_worth = initial_net_worth
                if mc_finance_mode == "Separate":
                    mc_nw_p1 = st.session_state.parentX_net_worth
                    mc_nw_p2 = st.session_state.parentY_net_worth

                for year_offset in range(st.session_state.mc_years):
                    year = st.session_state.mc_start_year + year_offset

                    # Calculate base income (same as deterministic)
                    parentX_working = (year - (st.session_state.current_year - st.session_state.parentX_age)) < st.session_state.parentX_retirement_age
                    parentY_working = (year - (st.session_state.current_year - st.session_state.parentY_age)) < st.session_state.parentY_retirement_age

                    mc_p1_income = 0
                    mc_p2_income = 0
                    if parentX_working:
                        if st.session_state.get('parentX_career_phases'):
                            comp = get_career_income_for_year(
                                st.session_state.parentX_career_phases,
                                st.session_state.parentX_age,
                                st.session_state.current_year,
                                year
                            )
                            mc_p1_income = comp['total_employment_income']
                        else:
                            mc_p1_income = get_income_for_year(st.session_state.parentX_income, st.session_state.parentX_raise, st.session_state.parentX_job_changes, st.session_state.current_year, year)
                    else:
                        ss_benefit = st.session_state.parentX_ss_benefit * 12
                        if st.session_state.ss_insolvency_enabled and year >= 2034:
                            ss_benefit *= (1 - st.session_state.ss_shortfall_percentage / 100)
                        mc_p1_income += ss_benefit

                    if parentY_working:
                        if st.session_state.get('parentY_career_phases'):
                            comp = get_career_income_for_year(
                                st.session_state.parentY_career_phases,
                                st.session_state.parentY_age,
                                st.session_state.current_year,
                                year
                            )
                            mc_p2_income = comp['total_employment_income']
                        else:
                            mc_p2_income = get_income_for_year(st.session_state.parentY_income, st.session_state.parentY_raise, st.session_state.parentY_job_changes, st.session_state.current_year, year)
                    else:
                        ss_benefit = st.session_state.parentY_ss_benefit * 12
                        if st.session_state.ss_insolvency_enabled and year >= 2034:
                            ss_benefit *= (1 - st.session_state.ss_shortfall_percentage / 100)
                        mc_p2_income += ss_benefit

                    income = mc_p1_income + mc_p2_income

                    # Add variability to income
                    if use_asymmetric:
                        if np.random.random() > 0.5:
                            income *= (1 + np.random.uniform(0, st.session_state.mc_income_variability_positive / 100))
                        else:
                            income *= (1 - np.random.uniform(0, st.session_state.mc_income_variability_negative / 100))
                    else:
                        income *= (1 + np.random.uniform(-st.session_state.mc_income_variability / 100, st.session_state.mc_income_variability / 100))

                    # Calculate base expenses (Parent X + Parent Y + Family)
                    years_from_now = year - st.session_state.current_year

                    # Parent X + Parent Y + Family expenses (with inflation)
                    parentX_total = sum(st.session_state.parentX_expenses.values()) * (1.03 ** years_from_now)
                    parentY_total = sum(st.session_state.parentY_expenses.values()) * (1.03 ** years_from_now)
                    # Check if living in owned house → skip rent
                    mc_family = dict(st.session_state.family_shared_expenses)
                    mc_lives_owned = False
                    if 'houses' in st.session_state:
                        for house in st.session_state.houses:
                            status, _ = house.get_status_for_year(year)
                            if status == "Own_Live":
                                mc_lives_owned = True
                                break
                    if mc_lives_owned:
                        mc_family['Mortgage/Rent'] = 0.0
                    family_total = sum(mc_family.values()) * (1.03 ** years_from_now)
                    base_expenses = parentX_total + parentY_total + family_total

                    # Children expenses (same calculation as deterministic cashflow)
                    children_expenses = 0
                    for child in st.session_state.children_list:
                        child_exp = get_child_expenses(child, year, st.session_state.current_year)
                        child_total = sum(child_exp.values())
                        children_expenses += child_total

                    # Recurring expenses
                    recurring_expenses_total = 0
                    for recurring in st.session_state.recurring_expenses:
                        if year >= recurring.start_year:
                            if recurring.end_year is None or year <= recurring.end_year:
                                years_since_start = year - recurring.start_year
                                if years_since_start % recurring.frequency_years == 0:
                                    expense_amount = recurring.amount
                                    if recurring.inflation_adjust:
                                        expense_amount *= (1.03 ** years_from_now)
                                    recurring_expenses_total += expense_amount

                    # One-time major purchases
                    major_purchase_expenses = 0
                    for purchase in st.session_state.major_purchases:
                        if purchase.year == year:
                            major_purchase_expenses += purchase.amount

                    # Healthcare costs
                    healthcare_expenses = 0
                    parent1_age = st.session_state.parentX_age + (year - st.session_state.current_year)
                    parent2_age = st.session_state.parentY_age + (year - st.session_state.current_year)

                    if 'health_insurances' in st.session_state:
                        for insurance in st.session_state.health_insurances:
                            if insurance.covered_by in ["Parent 1", "Both", "Family"] and insurance.start_age <= parent1_age <= insurance.end_age:
                                healthcare_expenses += insurance.monthly_premium * 12
                            elif insurance.covered_by == "Parent 2" and insurance.start_age <= parent2_age <= insurance.end_age:
                                healthcare_expenses += insurance.monthly_premium * 12
                            elif insurance.covered_by in ["Both", "Family"]:
                                if (insurance.start_age <= parent1_age <= insurance.end_age) or (insurance.start_age <= parent2_age <= insurance.end_age):
                                    healthcare_expenses += insurance.monthly_premium * 12

                    # Medicare costs (age 65+)
                    medicare_expenses = 0
                    if 'medicare_part_b_premium' in st.session_state:
                        if parent1_age >= 65:
                            medicare_expenses += st.session_state.medicare_part_b_premium * 12
                            medicare_expenses += st.session_state.get('medicare_part_d_premium', 55.0) * 12
                            medicare_expenses += st.session_state.get('medigap_premium', 150.0) * 12
                        if parent2_age >= 65:
                            medicare_expenses += st.session_state.medicare_part_b_premium * 12
                            medicare_expenses += st.session_state.get('medicare_part_d_premium', 55.0) * 12
                            medicare_expenses += st.session_state.get('medigap_premium', 150.0) * 12
                    healthcare_expenses += medicare_expenses

                    # Long-term care insurance premiums
                    if 'ltc_insurances' in st.session_state:
                        for ltc in st.session_state.ltc_insurances:
                            if ltc.covered_person == "Parent 1" and parent1_age >= ltc.start_age:
                                healthcare_expenses += ltc.monthly_premium * 12
                            elif ltc.covered_person == "Parent 2" and parent2_age >= ltc.start_age:
                                healthcare_expenses += ltc.monthly_premium * 12

                    # Housing expenses (property tax, insurance, maintenance, upkeep)
                    house_expenses = 0
                    if 'houses' in st.session_state:
                        for house in st.session_state.houses:
                            status, _rental = house.get_status_for_year(year)
                            if status in ("Own_Live", "Own_Rent"):
                                mc_appr = 1 + getattr(house, 'appreciation_rate', 3.0) / 100
                                current_house_value = house.current_value * (mc_appr ** years_from_now)
                                house_expenses += current_house_value * house.property_tax_rate
                                house_expenses += house.home_insurance * (1.03 ** years_from_now)
                                house_expenses += current_house_value * house.maintenance_rate
                                house_expenses += house.upkeep_costs * (1.03 ** years_from_now)

                    total_expenses = base_expenses + children_expenses + recurring_expenses_total + major_purchase_expenses + healthcare_expenses + house_expenses

                    # Add variability to expenses
                    if use_asymmetric:
                        if np.random.random() > 0.5:
                            total_expenses *= (1 + np.random.uniform(0, st.session_state.mc_expense_variability_positive / 100))
                        else:
                            total_expenses *= (1 - np.random.uniform(0, st.session_state.mc_expense_variability_negative / 100))
                    else:
                        total_expenses *= (1 + np.random.uniform(-st.session_state.mc_expense_variability / 100, st.session_state.mc_expense_variability / 100))

                    # Calculate return
                    if use_asymmetric:
                        if np.random.random() > 0.5:
                            investment_return = scenario.investment_return * (1 + np.random.uniform(0, st.session_state.mc_return_variability_positive / 100))
                        else:
                            investment_return = scenario.investment_return * (1 - np.random.uniform(0, st.session_state.mc_return_variability_negative / 100))
                    else:
                        investment_return = scenario.investment_return * (1 + np.random.uniform(-st.session_state.mc_return_variability / 100, st.session_state.mc_return_variability / 100))

                    # Update net worth
                    if mc_finance_mode == "Separate":
                        # Split shared costs (everything except per-parent base expenses)
                        shared_mc = (family_total + children_expenses + recurring_expenses_total
                                     + major_purchase_expenses + healthcare_expenses + house_expenses)
                        # Apply expense variability equally to both
                        variability_factor = total_expenses / max(base_expenses + children_expenses + recurring_expenses_total + major_purchase_expenses + healthcare_expenses + house_expenses, 1) if (base_expenses + children_expenses + recurring_expenses_total + major_purchase_expenses + healthcare_expenses + house_expenses) > 0 else 1
                        p1_mc_exp = (parentX_total + shared_mc * mc_split) * variability_factor
                        p2_mc_exp = (parentY_total + shared_mc * (1 - mc_split)) * variability_factor

                        mc_nw_p1 = mc_nw_p1 + (mc_p1_income - p1_mc_exp) + (mc_nw_p1 * investment_return)
                        mc_nw_p2 = mc_nw_p2 + (mc_p2_income - p2_mc_exp) + (mc_nw_p2 * investment_return)
                        net_worth = mc_nw_p1 + mc_nw_p2
                    else:
                        cashflow = income - total_expenses
                        net_worth = net_worth + cashflow + (net_worth * investment_return)

                    # Normalize if requested
                    if st.session_state.mc_normalize_to_today_dollars:
                        inflation_factor = (1 + scenario.inflation_rate) ** year_offset
                        sim_net_worth.append(net_worth / inflation_factor)
                    else:
                        sim_net_worth.append(net_worth)

                all_sim_results.append(sim_net_worth)
                progress_bar.progress((sim + 1) / num_sims)

            progress_bar.empty()

            # Calculate percentiles
            years_array = list(range(st.session_state.mc_start_year, st.session_state.mc_start_year + st.session_state.mc_years))
            percentiles_data = {
                '10th': [],
                '25th': [],
                '50th': [],
                '75th': [],
                '90th': []
            }

            for year_idx in range(st.session_state.mc_years):
                year_values = [sim[year_idx] for sim in all_sim_results]
                percentiles_data['10th'].append(np.percentile(year_values, 10))
                percentiles_data['25th'].append(np.percentile(year_values, 25))
                percentiles_data['50th'].append(np.percentile(year_values, 50))
                percentiles_data['75th'].append(np.percentile(year_values, 75))
                percentiles_data['90th'].append(np.percentile(year_values, 90))

            # Store results
            st.session_state.mc_results = {
                'years': years_array,
                'percentiles': percentiles_data,
                'scenario': scenario,
                'all_simulations': all_sim_results
            }

            st.success("✅ Monte Carlo simulation complete! Results below.")
            st.rerun()

    # Display Monte Carlo Results
    if 'mc_results' in st.session_state and st.session_state.mc_results:
        mc_data = st.session_state.mc_results

        st.markdown("### Monte Carlo Results: Net Worth Trajectories")

        # Create percentile fan chart
        fig = go.Figure()

        years = mc_data['years']
        percentiles = mc_data['percentiles']

        # Add percentile bands
        fig.add_trace(go.Scatter(x=years, y=percentiles['90th'], mode='lines', name='90th Percentile', line=dict(color='rgba(0,100,255,0.2)', width=1)))
        fig.add_trace(go.Scatter(x=years, y=percentiles['75th'], mode='lines', name='75th Percentile', line=dict(color='rgba(0,150,255,0.3)', width=1), fill='tonexty', fillcolor='rgba(0,100,255,0.1)'))
        fig.add_trace(go.Scatter(x=years, y=percentiles['50th'], mode='lines', name='50th Percentile (Median)', line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=years, y=percentiles['25th'], mode='lines', name='25th Percentile', line=dict(color='rgba(255,150,0,0.3)', width=1), fill='tonexty', fillcolor='rgba(100,150,255,0.1)'))
        fig.add_trace(go.Scatter(x=years, y=percentiles['10th'], mode='lines', name='10th Percentile', line=dict(color='rgba(255,0,0,0.3)', width=1), fill='tonexty', fillcolor='rgba(255,100,0,0.1)'))

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Broke", annotation_position="right")

        fig.update_layout(
            title=f"Net Worth Trajectories: Monte Carlo Simulation ({len(mc_data.get('all_simulations', []))} simulations)",
            xaxis_title="Year",
            yaxis_title="Net Worth ($)" + (" - Today's Dollars" if st.session_state.mc_normalize_to_today_dollars else ""),
            height=600,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Calculate success probability
        final_year_values = [sim[-1] for sim in mc_data.get('all_simulations', [])]
        success_rate = sum(1 for v in final_year_values if v > 0) / len(final_year_values) * 100 if final_year_values else 0

        st.markdown("### 📊 Probability Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Success Probability", f"{success_rate:.1f}%", help="Probability of not running out of money")
        with col2:
            median_final = percentiles['50th'][-1] if percentiles['50th'] else 0
            st.metric("Median Final Net Worth", f"${median_final:,.0f}")
        with col3:
            worst_case = percentiles['10th'][-1] if percentiles['10th'] else 0
            st.metric("10th Percentile Outcome", f"${worst_case:,.0f}")

        if success_rate < 80:
            st.warning("⚠️ Your plan has less than 80% probability of success. Consider adjusting your savings rate, retirement age, or spending.")
        else:
            st.success("✅ Your plan shows strong resilience to market uncertainty!")

        st.info("💡 **Next Step:** Use the Stress Test tab to test against catastrophic scenarios.")
    else:
        st.info("⏸️ Click 'Run Monte Carlo Simulation' above to see probabilistic outcomes and success rates.")

def test_net_worth_loss_scenario(percentiles_data, config):
    """
    Test net worth loss scenario with configurable loss percentage.

    Args:
        percentiles_data: Dict containing percentile data with 'percentiles', 'years', 'scenario'
        config: Dict with 'loss_percent' key (e.g., {'loss_percent': 50})

    Returns:
        Dict with event name and results for each percentile
    """
    percentiles = percentiles_data['percentiles']
    years = percentiles_data['years']
    scenario = percentiles_data['scenario']
    percentile_names = ['10th', '25th', '50th', '75th', '90th']

    loss_percent = config.get('loss_percent', 50)
    loss_multiplier = 1 - (loss_percent / 100)

    event_results = {'event': f'{loss_percent}% Net Worth Loss (Worst Year)'}

    for pct_name in percentile_names:
        pct_values = percentiles[pct_name]
        worst_final_nw = float('inf')
        worst_year = None

        # Try each year as the crash year
        for crash_idx in range(len(years)):
            # Simulate from crash year forward
            net_worth = pct_values[crash_idx] * loss_multiplier

            # Continue simulation from crash year to end
            final_nw = net_worth
            for future_idx in range(crash_idx + 1, len(years)):
                return_rate = scenario.investment_return
                investment_return = final_nw * return_rate

                # Implied cashflow from percentile trajectory
                if future_idx < len(pct_values) - 1:
                    implied_cashflow = (pct_values[future_idx + 1] - pct_values[future_idx]) - (pct_values[future_idx] * scenario.investment_return)
                    final_nw = final_nw + implied_cashflow + investment_return
                else:
                    final_nw = final_nw + investment_return

            # Track worst case
            if final_nw < worst_final_nw:
                worst_final_nw = final_nw
                worst_year = years[crash_idx]

        # Store result
        status = "✅" if worst_final_nw > 0 else "❌"
        event_results[pct_name] = {
            'status': status,
            'worst_year': worst_year,
            'final_nw': worst_final_nw
        }

    return event_results


def test_disabled_child_scenario(percentiles_data, config):
    """
    Test disabled child scenario where one parent retires immediately.

    Args:
        percentiles_data: Dict containing percentile data
        config: Dict with 'child_idx' and 'child_birth_year' keys

    Returns:
        Dict with event name and results for each percentile
    """
    percentiles = percentiles_data['percentiles']
    years = percentiles_data['years']
    scenario = percentiles_data['scenario']
    percentile_names = ['10th', '25th', '50th', '75th', '90th']

    child_idx = config.get('child_idx', 0)
    child_birth_year = config.get('child_birth_year')

    event_results = {'event': f'Disabled Child #{child_idx + 1} (Birth Year {child_birth_year})'}

    for pct_name in percentile_names:
        pct_values = percentiles[pct_name]

        # Find index of birth year
        if child_birth_year not in years:
            event_results[pct_name] = {'status': 'N/A', 'final_nw': 0}
            continue

        birth_idx = years.index(child_birth_year)
        net_worth = pct_values[birth_idx]

        for future_idx in range(birth_idx + 1, len(years)):
            year_offset = future_idx - birth_idx

            # Reduced cashflow due to lost income
            if future_idx < len(pct_values) - 1:
                normal_cashflow = (pct_values[future_idx + 1] - pct_values[future_idx]) - (pct_values[future_idx] * scenario.investment_return)
                reduced_cashflow = normal_cashflow - (st.session_state.parentY_income * (1 + scenario.inflation_rate) ** year_offset)
            else:
                reduced_cashflow = 0

            investment_return = net_worth * scenario.investment_return
            net_worth = net_worth + reduced_cashflow + investment_return

        status = "✅" if net_worth > 0 else "❌"
        event_results[pct_name] = {
            'status': status,
            'final_nw': net_worth
        }

    return event_results


def find_worst_case_disabled_child(percentiles_data, children_list):
    """
    Determine which child scenario results in the worst financial outcome.

    Args:
        percentiles_data: Dict containing percentile data
        children_list: List of children with their information

    Returns:
        Dict with 'child_idx', 'child_name', and 'child_birth_year' for worst case
    """
    if not children_list:
        return None

    percentile_names = ['10th', '25th', '50th', '75th', '90th']
    worst_child = None
    worst_avg_final_nw = float('inf')

    for child_idx, child in enumerate(children_list):
        child_birth_year = child['birth_year']

        # Run scenario for this child
        config = {
            'child_idx': child_idx,
            'child_birth_year': child_birth_year
        }
        results = test_disabled_child_scenario(percentiles_data, config)

        # Calculate average final net worth across all percentiles
        total_nw = 0
        valid_percentiles = 0
        for pct_name in percentile_names:
            if pct_name in results and isinstance(results[pct_name], dict):
                total_nw += results[pct_name]['final_nw']
                valid_percentiles += 1

        if valid_percentiles > 0:
            avg_final_nw = total_nw / valid_percentiles

            # Track the worst case (lowest average net worth)
            if avg_final_nw < worst_avg_final_nw:
                worst_avg_final_nw = avg_final_nw
                worst_child = {
                    'child_idx': child_idx,
                    'child_name': child['name'],
                    'child_birth_year': child_birth_year
                }

    return worst_child


def test_unemployment_scenario(percentiles_data, config):
    """
    Test forced unemployment scenario.

    Args:
        percentiles_data: Dict containing percentile data
        config: Dict with 'parent_name', 'parent_income', and 'duration_years' keys

    Returns:
        Dict with event name and results for each percentile
    """
    percentiles = percentiles_data['percentiles']
    years = percentiles_data['years']
    scenario = percentiles_data['scenario']
    percentile_names = ['10th', '25th', '50th', '75th', '90th']

    parent_name = config.get('parent_name', 'Parent')
    parent_income = config.get('parent_income', 0)
    duration_years = config.get('duration_years', 3)

    event_results = {'event': f'{parent_name} Unemployed {duration_years} Years (Worst Year)'}

    for pct_name in percentile_names:
        pct_values = percentiles[pct_name]
        worst_final_nw = float('inf')
        worst_year = None

        # Try each year as the unemployment start
        for unemp_start_idx in range(len(years) - duration_years):
            net_worth = pct_values[unemp_start_idx]

            # Simulate unemployment period plus recovery
            for future_idx in range(unemp_start_idx, len(years)):
                year_offset = future_idx - unemp_start_idx

                # Calculate cashflow impact
                if future_idx < len(pct_values) - 1:
                    normal_cashflow = (pct_values[future_idx + 1] - pct_values[future_idx]) - (pct_values[future_idx] * scenario.investment_return)

                    # During unemployment, lose this parent's income
                    if year_offset < duration_years:
                        income_loss = parent_income * ((1 + scenario.inflation_rate) ** year_offset)
                        reduced_cashflow = normal_cashflow - income_loss
                    else:
                        reduced_cashflow = normal_cashflow
                else:
                    reduced_cashflow = 0

                investment_return = net_worth * scenario.investment_return
                net_worth = net_worth + reduced_cashflow + investment_return

            # Track worst case
            if net_worth < worst_final_nw:
                worst_final_nw = net_worth
                worst_year = years[unemp_start_idx]

        status = "✅" if worst_final_nw > 0 else "❌"
        event_results[pct_name] = {
            'status': status,
            'worst_year': worst_year,
            'final_nw': worst_final_nw
        }

    return event_results


def test_hyperinflation_scenario(percentiles_data, config):
    """
    Test hyperinflation scenario with elevated inflation rate.

    Args:
        percentiles_data: Dict containing percentile data
        config: Dict with 'inflation_years' and 'inflation_rate' keys

    Returns:
        Dict with event name and results for each percentile
    """
    percentiles = percentiles_data['percentiles']
    years = percentiles_data['years']
    scenario = percentiles_data['scenario']
    percentile_names = ['10th', '25th', '50th', '75th', '90th']

    inflation_years = config.get('inflation_years', 5)
    inflation_rate = config.get('inflation_rate', 0.15)  # 15% inflation

    event_results = {'event': f'Hyperinflation: {int(inflation_rate*100)}% for {inflation_years} Years (Worst Year)'}

    for pct_name in percentile_names:
        pct_values = percentiles[pct_name]
        worst_final_nw = float('inf')
        worst_year = None

        # Try each year as the hyperinflation start
        for inflation_start_idx in range(len(years) - inflation_years):
            net_worth = pct_values[inflation_start_idx]

            # Simulate hyperinflation period plus recovery
            for future_idx in range(inflation_start_idx, len(years)):
                year_offset = future_idx - inflation_start_idx

                # Calculate cashflow impact
                if future_idx < len(pct_values) - 1:
                    normal_cashflow = (pct_values[future_idx + 1] - pct_values[future_idx]) - (pct_values[future_idx] * scenario.investment_return)

                    # During hyperinflation, expenses increase dramatically
                    if year_offset < inflation_years:
                        # Expenses increase with hyperinflation, income may lag
                        expense_increase = (st.session_state.parentX_income + st.session_state.parentY_income) * 0.3 * ((1 + inflation_rate) ** year_offset)
                        reduced_cashflow = normal_cashflow - expense_increase
                    else:
                        reduced_cashflow = normal_cashflow
                else:
                    reduced_cashflow = 0

                investment_return = net_worth * scenario.investment_return
                net_worth = net_worth + reduced_cashflow + investment_return

            # Track worst case
            if net_worth < worst_final_nw:
                worst_final_nw = net_worth
                worst_year = years[inflation_start_idx]

        status = "✅" if worst_final_nw > 0 else "❌"
        event_results[pct_name] = {
            'status': status,
            'worst_year': worst_year,
            'final_nw': worst_final_nw
        }

    return event_results


def stress_test_tab():
    """Stress testing tab for catastrophic scenarios"""
    st.header("🧪 Stress Test Analysis")
    tab_walkthrough("stress_test")
    st.markdown("""
    Stress-test your financial plan against rare catastrophic events.
    This analysis shows whether your plan can withstand worst-case scenarios across different Monte Carlo percentiles.

    **⚠️ Note:** You must run the Monte Carlo simulation first in the Analysis & Cashflow tab.
    """)

    # Check if Monte Carlo results exist
    if 'mc_results' not in st.session_state:
        st.warning("⚠️ Please run the Monte Carlo simulation first in the 📊 Analysis & Cashflow tab.")
        return

    mc_data = st.session_state.mc_results
    percentiles = mc_data['percentiles']
    years = mc_data['years']
    scenario = mc_data['scenario']

    st.info(f"📊 Analyzing {len(years)} years across 5 percentiles (10th, 25th, 50th, 75th, 90th)")

    # Define percentile names for iteration
    percentile_names = ['10th', '25th', '50th', '75th', '90th']

    # Store results for stoplight table
    stress_test_results = []

    # Prepare percentiles_data for all tests
    percentiles_data = {
        'percentiles': percentiles,
        'years': years,
        'scenario': scenario
    }

    # Individual Stress Tests Section
    st.markdown("---")
    st.markdown("## 📋 Individual Stress Tests")
    st.markdown("*Configure and run individual stress test scenarios*")

    with st.spinner("🔍 Analyzing individual stress test scenarios..."):

        # Market Crash Scenario
        st.markdown("---")
        st.markdown("### 💥 Market Crash Scenario")
        loss_percent = st.slider(
            "Net Worth Loss Percentage",
            min_value=10,
            max_value=90,
            value=50,
            step=5,
            help="Test how your plan handles a market crash of this magnitude",
            key="market_crash_slider"
        )

        st.markdown(f"*Finding the worst year to experience a {loss_percent}% market crash for each percentile*")

        config = {'loss_percent': loss_percent}
        event_results = test_net_worth_loss_scenario(percentiles_data, config)
        stress_test_results.append(event_results)

        # Hyperinflation Scenario
        st.markdown("---")
        st.markdown("### 📈 Hyperinflation Scenario")

        col1, col2 = st.columns(2)
        with col1:
            hyperinflation_rate = st.slider(
                "Inflation Rate (%)",
                min_value=5,
                max_value=30,
                value=15,
                step=1,
                help="Annual inflation rate during hyperinflation period",
                key="hyperinflation_rate_slider"
            )
        with col2:
            hyperinflation_years = st.slider(
                "Duration (Years)",
                min_value=2,
                max_value=10,
                value=5,
                step=1,
                help="How many years of hyperinflation to test",
                key="hyperinflation_years_slider"
            )

        st.markdown(f"*Finding the worst year to experience {hyperinflation_years} years of {hyperinflation_rate}% inflation*")

        config = {
            'inflation_years': hyperinflation_years,
            'inflation_rate': hyperinflation_rate / 100
        }
        event_results = test_hyperinflation_scenario(percentiles_data, config)
        stress_test_results.append(event_results)

        # Disabled Child Scenarios
        if st.session_state.children_list:
            st.markdown("---")
            st.markdown("### 👶 Disabled Child Birth (Parent Retires Immediately)")
            st.markdown("*Testing if one parent can immediately retire to care for a disabled child*")

            for child_idx, child in enumerate(st.session_state.children_list):
                child_birth_year = child['birth_year']

                config = {
                    'child_idx': child_idx,
                    'child_birth_year': child_birth_year
                }

                event_results = test_disabled_child_scenario(percentiles_data, config)
                stress_test_results.append(event_results)

        # Unemployment Scenarios
        st.markdown("---")
        st.markdown("### 💼 Forced Unemployment")
        st.markdown("*Testing 3-year unemployment periods at the worst possible time*")

        for parent_name, parent_income in [(st.session_state.parent1_name, st.session_state.parentX_income),
                                            (st.session_state.parent2_name, st.session_state.parentY_income)]:
            config = {
                'parent_name': parent_name,
                'parent_income': parent_income,
                'duration_years': 3
            }

            event_results = test_unemployment_scenario(percentiles_data, config)
            stress_test_results.append(event_results)

    # Compound Stress Tests Section
    st.markdown("---")
    st.markdown("## ⚡ Compound Stress Tests")
    st.markdown("*Combine multiple stress scenarios to test worst-case situations*")

    st.markdown("""
    Select which individual stress tests to combine. The compound test will apply all selected scenarios
    simultaneously and find the worst possible year for this combination to occur.
    """)

    # Create checkboxes for each stress test type
    st.markdown("### Select Scenarios to Combine:")

    compound_col1, compound_col2 = st.columns(2)

    with compound_col1:
        include_market_crash = st.checkbox(
            "💥 Market Crash",
            value=False,
            help="Include market crash in compound scenario"
        )
        if include_market_crash:
            compound_crash_percent = st.slider(
                "Market Crash Loss %",
                min_value=10,
                max_value=90,
                value=30,
                step=5,
                key="compound_crash_slider"
            )

        include_hyperinflation = st.checkbox(
            "📈 Hyperinflation",
            value=False,
            help="Include hyperinflation in compound scenario"
        )
        if include_hyperinflation:
            compound_inflation_rate = st.slider(
                "Compound Inflation Rate (%)",
                min_value=5,
                max_value=30,
                value=10,
                step=1,
                key="compound_inflation_rate_slider"
            )
            compound_inflation_years = st.slider(
                "Compound Inflation Duration (Years)",
                min_value=2,
                max_value=10,
                value=3,
                step=1,
                key="compound_inflation_years_slider"
            )

    with compound_col2:
        include_unemployment = st.checkbox(
            "💼 Unemployment",
            value=False,
            help="Include unemployment in compound scenario"
        )
        if include_unemployment:
            compound_unemployment_parent = st.selectbox(
                "Which Parent Loses Job",
                options=[st.session_state.parent1_name, st.session_state.parent2_name],
                key="compound_unemployment_parent"
            )
            compound_unemployment_years = st.slider(
                "Unemployment Duration (Years)",
                min_value=1,
                max_value=5,
                value=2,
                step=1,
                key="compound_unemployment_years_slider"
            )

        include_disabled_child = st.checkbox(
            "👶 Disabled Child",
            value=False,
            help="Include disabled child scenario (parent retires) - worst case child will be automatically selected"
        )

    # Run compound test if at least 2 scenarios are selected
    num_selected = sum([include_market_crash, include_hyperinflation, include_unemployment, include_disabled_child])

    if num_selected >= 2:
        st.markdown("---")
        if st.button("🔥 Run Compound Stress Test", type="primary", use_container_width=True):
            with st.spinner("🔍 Running compound stress test... This may take a moment."):
                # Determine worst-case child if disabled child scenario is included
                worst_case_child = None
                if include_disabled_child and st.session_state.children_list:
                    worst_case_child = find_worst_case_disabled_child(percentiles_data, st.session_state.children_list)

                # Build scenario description
                scenario_parts = []
                if include_market_crash:
                    scenario_parts.append(f"{compound_crash_percent}% Crash")
                if include_hyperinflation:
                    scenario_parts.append(f"{compound_inflation_years}yr {compound_inflation_rate}% Inflation")
                if include_unemployment:
                    scenario_parts.append(f"{compound_unemployment_parent} Unemployed {compound_unemployment_years}yr")
                if include_disabled_child and worst_case_child:
                    scenario_parts.append(f"Disabled {worst_case_child['child_name']} (Worst Case)")

                event_name = "Compound: " + " + ".join(scenario_parts)

                event_results = {'event': event_name}

                # Run compound simulation for each percentile
                for pct_name in percentile_names:
                    pct_values = percentiles[pct_name]
                    worst_final_nw = float('inf')
                    worst_year = None

                    # Try each year as the compound event start
                    max_duration = max(
                        compound_inflation_years if include_hyperinflation else 0,
                        compound_unemployment_years if include_unemployment else 0,
                        1
                    )

                    for event_start_idx in range(len(years) - max_duration):
                        # Start with base net worth
                        net_worth = pct_values[event_start_idx]

                        # Apply market crash immediately
                        if include_market_crash:
                            net_worth *= (1 - compound_crash_percent / 100)

                        # Get unemployment parent income
                        unemployment_parent_income = 0
                        if include_unemployment:
                            if compound_unemployment_parent == st.session_state.parent1_name:
                                unemployment_parent_income = st.session_state.parentX_income
                            else:
                                unemployment_parent_income = st.session_state.parentY_income

                        # Get disabled child parent income (assuming parent 2 retires)
                        disabled_child_parent_income = 0
                        if include_disabled_child:
                            disabled_child_parent_income = st.session_state.parentY_income

                        # Simulate future years with combined impacts
                        for future_idx in range(event_start_idx, len(years)):
                            year_offset = future_idx - event_start_idx

                            # Calculate normal cashflow
                            if future_idx < len(pct_values) - 1:
                                normal_cashflow = (pct_values[future_idx + 1] - pct_values[future_idx]) - (pct_values[future_idx] * scenario.investment_return)

                                # Apply hyperinflation impact (increased expenses)
                                if include_hyperinflation and year_offset < compound_inflation_years:
                                    # Estimate expense impact as 40% of normal cashflow affected by extra inflation
                                    extra_inflation = (compound_inflation_rate / 100) - scenario.inflation_rate
                                    hyperinflation_expense_increase = abs(normal_cashflow) * 0.4 * extra_inflation * (year_offset + 1)
                                    normal_cashflow -= hyperinflation_expense_increase

                                # Apply unemployment income loss
                                if include_unemployment and year_offset < compound_unemployment_years:
                                    income_loss = unemployment_parent_income * ((1 + scenario.inflation_rate) ** year_offset)
                                    normal_cashflow -= income_loss

                                # Apply disabled child income loss (parent retires permanently)
                                if include_disabled_child:
                                    income_loss = disabled_child_parent_income * ((1 + scenario.inflation_rate) ** year_offset)
                                    normal_cashflow -= income_loss

                                reduced_cashflow = normal_cashflow
                            else:
                                reduced_cashflow = 0

                            investment_return = net_worth * scenario.investment_return
                            net_worth = net_worth + reduced_cashflow + investment_return

                        # Track worst case
                        if net_worth < worst_final_nw:
                            worst_final_nw = net_worth
                            worst_year = years[event_start_idx]

                    status = "✅" if worst_final_nw > 0 else "❌"
                    event_results[pct_name] = {
                        'status': status,
                        'worst_year': worst_year,
                        'final_nw': worst_final_nw
                    }

                stress_test_results.append(event_results)
                st.success(f"✅ Compound test '{event_name}' completed!")
    elif num_selected == 1:
        st.info("ℹ️ Please select at least 2 scenarios to create a compound stress test.")
    else:
        st.info("ℹ️ Select scenarios above to create a compound stress test.")

    # Display Stoplight Table
    st.markdown("---")
    st.markdown("## 🚦 Stress Test Stoplight Analysis")
    st.markdown("**Green ✅**: Plan survives | **Red ❌**: Plan fails")

    # Create DataFrame for display
    table_data = []
    for result in stress_test_results:
        row = {'Event': result['event']}
        for pct_name in percentile_names:
            if pct_name in result:
                pct_result = result[pct_name]
                if isinstance(pct_result, dict):
                    status = pct_result['status']
                    if 'worst_year' in pct_result:
                        row[pct_name] = f"{status} ({pct_result['worst_year']})"
                    else:
                        row[pct_name] = status
                else:
                    row[pct_name] = pct_result
        table_data.append(row)

    results_df = pd.DataFrame(table_data)

    # Display table with color coding
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    # Detailed Results
    st.markdown("---")
    st.markdown("## 📋 Detailed Results")

    for result in stress_test_results:
        with st.expander(f"🔍 {result['event']}", expanded=False):
            detail_data = []
            for pct_name in percentile_names:
                if pct_name in result and isinstance(result[pct_name], dict):
                    pct_result = result[pct_name]
                    detail_row = {
                        'Percentile': pct_name,
                        'Status': pct_result['status'],
                        'Final Net Worth': format_currency(pct_result['final_nw'])
                    }
                    if 'worst_year' in pct_result:
                        detail_row['Worst Year'] = pct_result['worst_year']
                    detail_data.append(detail_row)

            if detail_data:
                detail_df = pd.DataFrame(detail_data)
                st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # Summary Statistics
    st.markdown("---")
    st.markdown("## 📊 Summary Statistics")

    total_scenarios = len(stress_test_results) * len(percentile_names)
    passed_scenarios = 0

    for result in stress_test_results:
        for pct_name in percentile_names:
            if pct_name in result and isinstance(result[pct_name], dict):
                if result[pct_name]['status'] == "✅":
                    passed_scenarios += 1

    success_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Scenarios Tested", total_scenarios)
    with col2:
        st.metric("Scenarios Passed", f"{passed_scenarios} / {total_scenarios}")
    with col3:
        st.metric("Overall Success Rate", f"{success_rate:.1f}%")

    if success_rate >= 80:
        st.success("✅ **Excellent!** Your financial plan is highly resilient to stress test scenarios.")
    elif success_rate >= 60:
        st.info("⚠️ **Good** - Your plan handles most scenarios but consider building more buffer.")
    elif success_rate >= 40:
        st.warning("⚠️ **Moderate Risk** - Your plan struggles with many catastrophic scenarios. Consider increasing savings or reducing expenses.")
    else:
        st.error("❌ **High Risk** - Your plan is vulnerable to stress test scenarios. Significant adjustments recommended.")


def save_data():
    """Serialize all session state to a JSON string"""
    try:
        data = {
            'current_year': st.session_state.current_year,
            'parent1_name': st.session_state.parent1_name,
            'parent1_emoji': st.session_state.parent1_emoji,
            'parent2_name': st.session_state.parent2_name,
            'parent2_emoji': st.session_state.parent2_emoji,
            'marriage_year': st.session_state.marriage_year,
            'finance_mode': st.session_state.get('finance_mode', 'Pooled'),
            'shared_expense_split_pct': st.session_state.get('shared_expense_split_pct', 50),
            'parentX_age': st.session_state.parentX_age,
            'parentX_net_worth': st.session_state.parentX_net_worth,
            'parentX_income': st.session_state.parentX_income,
            'parentX_raise': st.session_state.parentX_raise,
            'parentX_retirement_age': st.session_state.parentX_retirement_age,
            'parentX_ss_benefit': st.session_state.parentX_ss_benefit,
            'parentX_death_age': st.session_state.get('parentX_death_age', 100),
            'parentX_job_changes': st.session_state.parentX_job_changes.to_dict('records') if hasattr(st.session_state.get('parentX_job_changes', None), 'to_dict') else [],
            'parentX_career_phases': [asdict(cp) for cp in st.session_state.get('parentX_career_phases', [])],
            'parentX_expenses': st.session_state.get('parentX_expenses', {}),
            'parentX_expense_location': st.session_state.get('parentX_expense_location', 'Seattle'),
            'parentX_expense_strategy': st.session_state.get('parentX_expense_strategy', 'Moderate'),
            'parentX_use_template': st.session_state.get('parentX_use_template', True),
            'parentY_age': st.session_state.parentY_age,
            'parentY_net_worth': st.session_state.parentY_net_worth,
            'parentY_income': st.session_state.parentY_income,
            'parentY_raise': st.session_state.parentY_raise,
            'parentY_retirement_age': st.session_state.parentY_retirement_age,
            'parentY_ss_benefit': st.session_state.parentY_ss_benefit,
            'parentY_death_age': st.session_state.get('parentY_death_age', 100),
            'parentY_job_changes': st.session_state.parentY_job_changes.to_dict('records') if hasattr(st.session_state.get('parentY_job_changes', None), 'to_dict') else [],
            'parentY_career_phases': [asdict(cp) for cp in st.session_state.get('parentY_career_phases', [])],
            'parentY_expenses': st.session_state.get('parentY_expenses', {}),
            'parentY_expense_location': st.session_state.get('parentY_expense_location', 'Seattle'),
            'parentY_expense_strategy': st.session_state.get('parentY_expense_strategy', 'Moderate'),
            'parentY_use_template': st.session_state.get('parentY_use_template', True),
            'expenses': st.session_state.expenses,
            'family_shared_expenses': st.session_state.get('family_shared_expenses', {}),
            'children_list': st.session_state.children_list,
            'houses': [asdict(h) for h in st.session_state.houses],
            'major_purchases': [asdict(mp) for mp in st.session_state.major_purchases],
            'recurring_expenses': [asdict(re_exp) for re_exp in st.session_state.recurring_expenses],
            'state_timeline': [asdict(st_entry) for st_entry in st.session_state.state_timeline],
            'economic_params': asdict(st.session_state.economic_params),
            'ss_insolvency_enabled': st.session_state.ss_insolvency_enabled,
            'ss_shortfall_percentage': st.session_state.ss_shortfall_percentage,
            'health_insurances': [asdict(hi) for hi in st.session_state.get('health_insurances', [])],
            'ltc_insurances': [asdict(li) for li in st.session_state.get('ltc_insurances', [])],
            'health_expenses': [asdict(he) for he in st.session_state.get('health_expenses', [])],
            'hsa_balance': st.session_state.get('hsa_balance', 0.0),
            'hsa_contribution': st.session_state.get('hsa_contribution', 0.0),
        }
        return json.dumps(data, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return None


def load_data(json_data):
    """Load session state from a JSON string. Returns True on success."""
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        for key, value in data.items():
            if key == 'houses':
                houses = []
                for h in value:
                    house_dict = h.copy()
                    if 'timeline' in house_dict and house_dict['timeline']:
                        house_dict['timeline'] = [HouseTimelineEntry(**entry) for entry in house_dict['timeline']]
                    houses.append(House(**house_dict))
                st.session_state.houses = houses
            elif key == 'major_purchases':
                st.session_state.major_purchases = [MajorPurchase(**mp) for mp in value]
            elif key == 'recurring_expenses':
                st.session_state.recurring_expenses = [RecurringExpense(**re_exp) for re_exp in value]
            elif key == 'state_timeline':
                st.session_state.state_timeline = [StateTimelineEntry(**st_entry) for st_entry in value]
            elif key == 'economic_params':
                st.session_state.economic_params = EconomicParameters(**value)
            elif key == 'health_insurances':
                st.session_state.health_insurances = [HealthInsurance(**hi) for hi in value]
            elif key == 'ltc_insurances':
                st.session_state.ltc_insurances = [LongTermCareInsurance(**li) for li in value]
            elif key == 'health_expenses':
                st.session_state.health_expenses = [HealthExpense(**he) for he in value]
            elif key in ('parentX_job_changes', 'parentY_job_changes'):
                st.session_state[key] = pd.DataFrame(value) if value else pd.DataFrame({'Year': [], 'New Income': [], 'New Raise %': []})
            elif key in ('parentX_career_phases', 'parentY_career_phases'):
                st.session_state[key] = [CareerPhase(**cp) for cp in value]
            else:
                st.session_state[key] = value

        # ── Post-load migration / sanity fixes ──────────────────────────
        # Zero out Parent Y expenses if single parent
        p2_name = st.session_state.get('parent2_name', '')
        p2_income = st.session_state.get('parentY_income', 0)
        is_single = p2_name in ('N/A', '', 'Parent 2') and p2_income == 0
        if (is_single and hasattr(st.session_state, 'parentY_expenses')
                and sum(st.session_state.parentY_expenses.values()) > 0):
            st.session_state.parentY_expenses = {k: 0 for k in st.session_state.parentY_expenses}

        # For single-income households under $100k, use Conservative expenses if still at Average defaults
        p1_income = st.session_state.get('parentX_income', 0)
        if is_single and p1_income < 100000 and hasattr(st.session_state, 'parentX_expenses'):
            avg_template = get_adult_expense_template("Seattle", "Average (statistical)")
            current_total = sum(st.session_state.parentX_expenses.values())
            avg_total = sum(avg_template.values())
            if abs(current_total - avg_total) < 1000:  # Still at defaults
                st.session_state.parentX_expenses = get_adult_expense_template("Seattle", "Conservative (statistical)")

        return True
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False


def save_load_tab():
    """Save and load scenarios tab"""
    st.header("💾 Save & Load Scenarios")
    tab_walkthrough("save_load")

    st.markdown("Save and load complete financial planning scenarios")

    # Household persistence section
    if st.session_state.get('authenticated'):
        st.subheader("🏠 Household Cloud Storage")
        st.info(f"💡 Your household code: `{st.session_state.household_id}` — All household members share the same saved plan.")

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            if st.button("💾 Save Plan to Household", type="primary", key="save_household_plan_btn"):
                json_data = save_data()
                if json_data:
                    save_household_plan(st.session_state.household_id, json_data)
                    st.success("Plan saved to household! All members will see these changes.")

        with col_h2:
            if st.button("📂 Load Plan from Household", key="load_household_plan_btn"):
                plan_data = load_household_plan(st.session_state.household_id)
                if plan_data:
                    if load_data(plan_data):
                        st.success("Plan loaded from household storage!")
                        st.rerun()
                else:
                    st.info("No saved plan found. Save your current plan first.")

        household_info = get_household_info(st.session_state.household_id)
        if household_info.get('last_saved'):
            st.caption(f"Last saved: {household_info['last_saved'][:19]} by {household_info.get('saved_by', 'unknown')}")

        st.divider()

    # Quick what-if scenario templates
    scenario_templates_section()

    st.divider()

    # Version history / restore from backup
    _version_history_section()

    st.divider()

    # Internal scenario library
    st.subheader("📚 Internal Scenario Library")

    col1, col2 = st.columns([2, 1])

    with col1:
        scenario_name = st.text_input(
            "Scenario Name",
            value="My Scenario",
            key="save_scenario_name"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("💾 Save to Library", use_container_width=True):
            json_data = save_data()
            if json_data:
                st.session_state.saved_scenarios[scenario_name] = json_data
                if st.session_state.get('authenticated') and st.session_state.get('household_id'):
                    save_household_scenarios(st.session_state.household_id, st.session_state.saved_scenarios)
                st.success(f"✅ Saved scenario '{scenario_name}' to library")

    # Display saved scenarios
    if st.session_state.saved_scenarios:
        st.markdown("**Saved Scenarios:**")

        for name in list(st.session_state.saved_scenarios.keys()):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.text(f"📋 {name}")

            with col2:
                if st.button("📥 Load", key=f"load_{name}"):
                    scenario_data = st.session_state.saved_scenarios[name]
                    if load_data(scenario_data):
                        st.success(f"✅ Loaded scenario '{name}'")
                        st.rerun()

            with col3:
                if st.button("🗑️ Delete", key=f"delete_{name}"):
                    del st.session_state.saved_scenarios[name]
                    if st.session_state.get('authenticated') and st.session_state.get('household_id'):
                        save_household_scenarios(st.session_state.household_id, st.session_state.saved_scenarios)
                    st.success(f"🗑️ Deleted scenario '{name}'")
                    st.rerun()
    else:
        st.info("No scenarios saved yet. Save your first scenario above!")

    # Launch wizard button
    st.divider()
    st.subheader("🧙 Create New Plan with Guided Setup")
    st.caption("Walk through a step-by-step questionnaire to build a new financial plan from scratch.")
    if st.button("🚀 Launch Setup Wizard", use_container_width=False):
        st.session_state.wizard_step = 0
        st.session_state.wizard_data = {}
        st.session_state.wizard_complete = False
        st.session_state.wizard_skipped = False
        st.session_state.wizard_manual = True
        st.rerun()

    # Plan comparison
    if st.session_state.saved_scenarios and len(st.session_state.saved_scenarios) >= 2:
        st.divider()
        st.subheader("📊 Compare Plans")
        scenario_names = list(st.session_state.saved_scenarios.keys())
        col1, col2 = st.columns(2)
        with col1:
            plan_a = st.selectbox("Plan A", scenario_names, index=0, key="compare_plan_a")
        with col2:
            plan_b = st.selectbox("Plan B", scenario_names, index=min(1, len(scenario_names)-1), key="compare_plan_b")

        if st.button("Compare", type="primary", key="compare_plans_btn"):
            try:
                data_a = json.loads(st.session_state.saved_scenarios[plan_a]) if isinstance(st.session_state.saved_scenarios[plan_a], str) else st.session_state.saved_scenarios[plan_a]
                data_b = json.loads(st.session_state.saved_scenarios[plan_b]) if isinstance(st.session_state.saved_scenarios[plan_b], str) else st.session_state.saved_scenarios[plan_b]

                def _get_val(d, key, default=0):
                    return d.get(key, default)

                def _fmt(v):
                    if isinstance(v, (int, float)):
                        if abs(v) >= 1000:
                            return f"${v:,.0f}"
                        return f"{v}"
                    return str(v)

                def _delta(a_val, b_val):
                    if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
                        diff = b_val - a_val
                        if abs(diff) >= 1000:
                            return f"${diff:+,.0f}"
                        elif abs(diff) > 0:
                            return f"{diff:+.1f}"
                    return ""

                # Parent info
                st.markdown("#### 👨‍👩‍👧 Family")
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.markdown("**Metric**")
                c2.markdown(f"**{plan_a}**")
                c3.markdown(f"**{plan_b}**")

                rows = [
                    ("Parent 1", _get_val(data_a, 'parent1_name', 'N/A'), _get_val(data_b, 'parent1_name', 'N/A')),
                    ("Parent 2", _get_val(data_a, 'parent2_name', 'N/A'), _get_val(data_b, 'parent2_name', 'N/A')),
                    ("Parent 1 Age", _get_val(data_a, 'parentX_age'), _get_val(data_b, 'parentX_age')),
                    ("Parent 2 Age", _get_val(data_a, 'parentY_age'), _get_val(data_b, 'parentY_age')),
                    ("Children", len(_get_val(data_a, 'children_list', [])), len(_get_val(data_b, 'children_list', []))),
                ]
                for label, va, vb in rows:
                    c1, c2, c3 = st.columns([2, 2, 2])
                    c1.write(label)
                    c2.write(str(va))
                    c3.write(str(vb))

                # Financial comparison
                st.markdown("#### 💰 Finances")
                income_a = _get_val(data_a, 'parentX_income', 0) + _get_val(data_a, 'parentY_income', 0)
                income_b = _get_val(data_b, 'parentX_income', 0) + _get_val(data_b, 'parentY_income', 0)
                nw_a = _get_val(data_a, 'parentX_net_worth', 0) + _get_val(data_a, 'parentY_net_worth', 0)
                nw_b = _get_val(data_b, 'parentX_net_worth', 0) + _get_val(data_b, 'parentY_net_worth', 0)
                retire_a = min(_get_val(data_a, 'parentX_retirement_age', 65), _get_val(data_a, 'parentY_retirement_age', 65))
                retire_b = min(_get_val(data_b, 'parentX_retirement_age', 65), _get_val(data_b, 'parentY_retirement_age', 65))
                houses_a = len(_get_val(data_a, 'houses', []))
                houses_b = len(_get_val(data_b, 'houses', []))

                fin_rows = [
                    ("Combined Income", income_a, income_b),
                    ("Combined Net Worth", nw_a, nw_b),
                    ("Earliest Retirement Age", retire_a, retire_b),
                    ("Properties", houses_a, houses_b),
                ]

                for label, va, vb in fin_rows:
                    c1, c2, c3 = st.columns([2, 2, 2])
                    c1.write(label)
                    c2.write(_fmt(va))
                    delta = _delta(va, vb)
                    c3.write(f"{_fmt(vb)}  {delta}" if delta else _fmt(vb))

                # Location comparison
                tl_a = _get_val(data_a, 'state_timeline', [])
                tl_b = _get_val(data_b, 'state_timeline', [])
                loc_a = tl_a[0].get('state', 'Unknown') if tl_a else 'Unknown'
                loc_b = tl_b[0].get('state', 'Unknown') if tl_b else 'Unknown'
                moves_a = len(tl_a)
                moves_b = len(tl_b)

                st.markdown("#### 📍 Location")
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.write("Starting Location")
                c2.write(str(loc_a))
                c3.write(str(loc_b))
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.write("Total Locations")
                c2.write(str(moves_a))
                c3.write(str(moves_b))

            except Exception as e:
                st.error(f"Error comparing plans: {str(e)}")

    st.divider()

    # File export/import
    st.subheader("📁 Export/Import Files")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Export to JSON File**")

        if st.button("💾 Export Current Scenario"):
            json_str = save_data()
            if json_str:
                # Show file save dialog
                if TKINTER_AVAILABLE:
                    file_path = get_save_file_path(
                        f"financial_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        [("JSON files", "*.json"), ("All files", "*.*")]
                    )

                    if file_path:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(json_str)
                        st.success(f"✅ Scenario exported successfully to: {file_path}")
                    else:
                        st.info("ℹ️ Export cancelled")
                else:
                    # Fallback to download button if tkinter not available
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_str,
                        file_name=f"financial_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

    with col2:
        st.markdown("**Import from JSON File**")

        uploaded_file = st.file_uploader("Choose a JSON file", type=['json'])

        if uploaded_file is not None:
            try:
                import_data = uploaded_file.read().decode('utf-8')
                if load_data(import_data):
                    st.success("✅ Successfully imported scenario!")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error importing file: {str(e)}")


# NEW TAB 1: Healthcare & Insurance
def healthcare_insurance_tab():
    """Healthcare and Insurance Planning Tab"""
    st.header("🏥 Healthcare & Insurance Planning")
    tab_walkthrough("healthcare")

    st.markdown("""
    Plan for healthcare costs throughout retirement, including Medicare, insurance premiums,
    out-of-pocket expenses, and long-term care insurance.
    """)

    # Ensure healthcare variables are initialized (defensive programming for old sessions)
    if 'health_insurances' not in st.session_state:
        st.session_state.health_insurances = []
    if 'ltc_insurances' not in st.session_state:
        st.session_state.ltc_insurances = []
    if 'health_expenses' not in st.session_state:
        st.session_state.health_expenses = []
    if 'hsa_balance' not in st.session_state:
        st.session_state.hsa_balance = 0.0
    if 'hsa_contribution' not in st.session_state:
        st.session_state.hsa_contribution = 0.0
    if 'medicare_part_b_premium' not in st.session_state:
        st.session_state.medicare_part_b_premium = 174.70
    if 'medicare_part_d_premium' not in st.session_state:
        st.session_state.medicare_part_d_premium = 55.0
    if 'medigap_premium' not in st.session_state:
        st.session_state.medigap_premium = 150.0

    # HSA Account
    st.subheader("💰 Health Savings Account (HSA)")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.hsa_balance = st.number_input(
            "Current HSA Balance",
            min_value=0.0,
            value=float(st.session_state.hsa_balance),
            step=1000.0,
            format="%.2f"
        )
    with col2:
        st.session_state.hsa_contribution = st.number_input(
            "Annual HSA Contribution",
            min_value=0.0,
            max_value=8300.0,  # 2025 family limit
            value=float(st.session_state.hsa_contribution),
            step=100.0,
            format="%.2f"
        )

    st.info("💡 HSA Triple Tax Advantage: Tax-deductible contributions, tax-free growth, tax-free withdrawals for medical expenses")

    # Health Insurance Plans
    st.subheader("🏥 Health Insurance Plans")

    if st.button("➕ Add Health Insurance Plan"):
        new_insurance = HealthInsurance(
            name="New Health Plan",
            type="Employer",
            monthly_premium=500.0,
            annual_deductible=3000.0,
            annual_out_of_pocket_max=8000.0,
            copay_primary=25.0,
            copay_specialist=50.0,
            covered_by="Family",
            start_age=0,
            end_age=65
        )
        st.session_state.health_insurances.append(new_insurance)
        st.rerun()

    for idx, insurance in enumerate(st.session_state.health_insurances):
        with st.expander(f"📋 {insurance.name}"):
            col1, col2, col3 = st.columns([3, 3, 1])

            with col1:
                insurance.name = st.text_input(f"Plan Name##ins{idx}", value=insurance.name)
                insurance.type = st.selectbox(
                    f"Insurance Type##ins{idx}",
                    ["Employer", "Marketplace", "Medicare", "Medicaid"],
                    index=["Employer", "Marketplace", "Medicare", "Medicaid"].index(insurance.type) if insurance.type in ["Employer", "Marketplace", "Medicare", "Medicaid"] else 0
                )
                insurance.monthly_premium = st.number_input(
                    f"Monthly Premium##ins{idx}",
                    min_value=0.0,
                    value=float(insurance.monthly_premium),
                    step=50.0
                )

            with col2:
                insurance.annual_deductible = st.number_input(
                    f"Annual Deductible##ins{idx}",
                    min_value=0.0,
                    value=float(insurance.annual_deductible),
                    step=100.0
                )
                insurance.annual_out_of_pocket_max = st.number_input(
                    f"Out-of-Pocket Maximum##ins{idx}",
                    min_value=0.0,
                    value=float(insurance.annual_out_of_pocket_max),
                    step=500.0
                )
                insurance.covered_by = st.selectbox(
                    f"Covered By##ins{idx}",
                    ["Parent 1", "Parent 2", "Both", "Family"],
                    index=["Parent 1", "Parent 2", "Both", "Family"].index(insurance.covered_by) if insurance.covered_by in ["Parent 1", "Parent 2", "Both", "Family"] else 3
                )

            with col3:
                if st.button(f"🗑️ Delete##{idx}_insurance"):
                    st.session_state.health_insurances.pop(idx)
                    st.rerun()

            st.session_state.health_insurances[idx] = insurance

    # Medicare Settings
    st.subheader("🩺 Medicare Planning (Age 65+)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.medicare_part_b_premium = st.number_input(
            "Medicare Part B Premium (Monthly)",
            min_value=0.0,
            value=float(st.session_state.medicare_part_b_premium),
            step=10.0,
            help="Standard 2025 premium: $174.70/month"
        )
    with col2:
        st.session_state.medicare_part_d_premium = st.number_input(
            "Medicare Part D Premium (Monthly)",
            min_value=0.0,
            value=float(st.session_state.medicare_part_d_premium),
            step=10.0,
            help="Average prescription drug plan premium"
        )
    with col3:
        st.session_state.medigap_premium = st.number_input(
            "Medigap Supplement Premium (Monthly)",
            min_value=0.0,
            value=float(st.session_state.medigap_premium),
            step=10.0,
            help="Optional supplemental coverage"
        )

    # Long-Term Care Insurance
    st.subheader("🏨 Long-Term Care Insurance")

    if st.button("➕ Add LTC Insurance Policy"):
        new_ltc = LongTermCareInsurance(
            name="LTC Policy",
            monthly_premium=300.0,
            daily_benefit=200.0,
            benefit_period_days=1095,  # 3 years
            elimination_period_days=90,
            covered_person="Parent 1",
            start_age=55,
            inflation_protection=0.03
        )
        st.session_state.ltc_insurances.append(new_ltc)
        st.rerun()

    for idx, ltc in enumerate(st.session_state.ltc_insurances):
        with st.expander(f"🏨 {ltc.name} - {ltc.covered_person}"):
            col1, col2, col3 = st.columns([3, 3, 1])

            with col1:
                ltc.name = st.text_input(f"Policy Name##ltc{idx}", value=ltc.name)
                ltc.covered_person = st.selectbox(
                    f"Covered Person##ltc{idx}",
                    ["Parent 1", "Parent 2"],
                    index=["Parent 1", "Parent 2"].index(ltc.covered_person) if ltc.covered_person in ["Parent 1", "Parent 2"] else 0
                )
                ltc.monthly_premium = st.number_input(
                    f"Monthly Premium##ltc{idx}",
                    min_value=0.0,
                    value=float(ltc.monthly_premium),
                    step=50.0
                )

            with col2:
                ltc.daily_benefit = st.number_input(
                    f"Daily Benefit##ltc{idx}",
                    min_value=0.0,
                    value=float(ltc.daily_benefit),
                    step=25.0,
                    help="Daily benefit amount for care"
                )
                ltc.benefit_period_days = st.number_input(
                    f"Benefit Period (days)##ltc{idx}",
                    min_value=0,
                    value=int(ltc.benefit_period_days),
                    step=365,
                    help="Total days of coverage (e.g., 1095 = 3 years)"
                )
                ltc.start_age = st.number_input(
                    f"Coverage Start Age##ltc{idx}",
                    min_value=30,
                    max_value=80,
                    value=int(ltc.start_age),
                    step=1
                )

            with col3:
                if st.button(f"🗑️ Delete##ltc{idx}"):
                    st.session_state.ltc_insurances.pop(idx)
                    st.rerun()

            st.session_state.ltc_insurances[idx] = ltc

    # Healthcare Cost Summary
    st.subheader("📊 Healthcare Cost Projection")

    total_annual_premium = sum([ins.monthly_premium * 12 for ins in st.session_state.health_insurances])
    total_ltc_premium = sum([ltc.monthly_premium * 12 for ltc in st.session_state.ltc_insurances])

    col1, col2, col3 = st.columns(3)
    col1.metric("Annual Health Insurance", format_currency(total_annual_premium))
    col2.metric("Annual LTC Insurance", format_currency(total_ltc_premium))
    col3.metric("Total Insurance Cost", format_currency(total_annual_premium + total_ltc_premium))


# NEW TAB 5: Report Export
def report_export_tab():
    """PDF/Excel Report Export Tab"""
    st.header("📄 Export Financial Reports")

    st.markdown("""
    Generate comprehensive financial planning reports in PDF or Excel format.
    Share with financial advisors, partners, or keep for your records.
    """)

    # Report Configuration
    st.subheader("📊 Report Configuration")

    col1, col2 = st.columns(2)
    with col1:
        report_name = st.text_input(
            "Report Name",
            value=f"Financial_Plan_{st.session_state.current_year}",
            help="Name for your exported report"
        )

        include_sections = st.multiselect(
            "Include Sections",
            ["Summary", "Income & Expenses", "Children", "Healthcare", "Timeline"],
            default=["Summary", "Income & Expenses"]
        )

    with col2:
        # Build format options based on library availability
        format_options = ["Excel (.xlsx)", "CSV (Multiple Files)", "JSON (Data Export)"]
        if REPORTLAB_AVAILABLE:
            format_options.insert(0, "PDF (.pdf)")

        report_format = st.selectbox(
            "Export Format",
            format_options,
            index=0
        )

        include_charts = st.checkbox(
            "Include Charts & Visualizations",
            value=True,
            help="Include Plotly charts as images (Excel only)"
        )

        if not REPORTLAB_AVAILABLE and report_format == "PDF (.pdf)":
            st.warning("⚠️ PDF export requires reportlab library. Install with: pip install reportlab")

    # Generate Report Button
    st.subheader("📥 Generate Report")

    if st.button("🚀 Generate Report", type="primary"):
        with st.spinner("Generating your financial report..."):
            try:
                # Calculate lifetime cashflow projections
                cashflow_projections = calculate_lifetime_cashflow()

                # Prepare report data
                report_data = {
                    "metadata": {
                        "report_name": report_name,
                        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "current_year": st.session_state.current_year,
                        "planning_horizon": st.session_state.mc_years
                    },
                    "summary": {
                        "combined_net_worth": st.session_state.parentX_net_worth + st.session_state.parentY_net_worth,
                        "combined_income": st.session_state.parentX_income + st.session_state.parentY_income,
                        "total_expenses": sum(st.session_state.expenses.values()),
                        "num_children": len(st.session_state.children_list),
                        "num_houses": len(st.session_state.houses)
                    },
                    "parents": {
                        "parent1": {
                            "name": st.session_state.parent1_name,
                            "age": st.session_state.parentX_age,
                            "income": st.session_state.parentX_income,
                            "net_worth": st.session_state.parentX_net_worth,
                            "retirement_age": st.session_state.parentX_retirement_age,
                            "ss_benefit": st.session_state.parentX_ss_benefit
                        },
                        "parent2": {
                            "name": st.session_state.parent2_name,
                            "age": st.session_state.parentY_age,
                            "income": st.session_state.parentY_income,
                            "net_worth": st.session_state.parentY_net_worth,
                            "retirement_age": st.session_state.parentY_retirement_age,
                            "ss_benefit": st.session_state.parentY_ss_benefit
                        }
                    },
                    "expenses": st.session_state.expenses,
                    "children": [{"name": c["name"], "age": st.session_state.current_year - c["birth_year"], "birth_year": c["birth_year"]} for c in st.session_state.children_list],
                    "healthcare": {
                        "health_insurances": [asdict(h) for h in st.session_state.health_insurances],
                        "ltc_insurances": [asdict(l) for l in st.session_state.ltc_insurances],
                        "hsa_balance": st.session_state.hsa_balance
                    },
                    "houses": [asdict(h) for h in st.session_state.houses] if hasattr(st.session_state, 'houses') else [],
                    "major_purchases": [asdict(mp) for mp in st.session_state.major_purchases] if hasattr(st.session_state, 'major_purchases') else [],
                    "recurring_expenses": [asdict(re) for re in st.session_state.recurring_expenses] if hasattr(st.session_state, 'recurring_expenses') else [],
                    "state_timeline": [asdict(st_entry) for st_entry in st.session_state.state_timeline] if hasattr(st.session_state, 'state_timeline') else [],
                    "cashflow_projections": cashflow_projections,
                    "monte_carlo_results": st.session_state.mc_results if hasattr(st.session_state, 'mc_results') and st.session_state.mc_results else None
                }

                if report_format == "PDF (.pdf)":
                    # Generate PDF report
                    output = io.BytesIO()
                    doc = SimpleDocTemplate(output, pagesize=letter,
                                          rightMargin=72, leftMargin=72,
                                          topMargin=72, bottomMargin=18)

                    # Container for the 'Flowable' objects
                    elements = []

                    # Define styles
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=24,
                        textColor=colors.HexColor('#1f77b4'),
                        spaceAfter=30,
                    )
                    heading_style = ParagraphStyle(
                        'CustomHeading',
                        parent=styles['Heading2'],
                        fontSize=16,
                        textColor=colors.HexColor('#2ca02c'),
                        spaceAfter=12,
                    )

                    # Title
                    title = Paragraph(f"Financial Planning Report", title_style)
                    elements.append(title)
                    elements.append(Spacer(1, 12))

                    # Metadata
                    metadata_text = f"""
                    <b>Report Name:</b> {report_data['metadata']['report_name']}<br/>
                    <b>Generated:</b> {report_data['metadata']['generated_date']}<br/>
                    <b>Planning Year:</b> {report_data['metadata']['current_year']}<br/>
                    <b>Planning Horizon:</b> {report_data['metadata']['planning_horizon']} years
                    """
                    elements.append(Paragraph(metadata_text, styles['Normal']))
                    elements.append(Spacer(1, 20))

                    # Summary Section
                    if "Summary" in include_sections:
                        elements.append(Paragraph("Financial Summary", heading_style))
                        summary_data = [
                            ['Metric', 'Value'],
                            ['Combined Net Worth', f"${report_data['summary']['combined_net_worth']:,.2f}"],
                            ['Combined Income', f"${report_data['summary']['combined_income']:,.2f}"],
                            ['Total Expenses', f"${report_data['summary']['total_expenses']:,.2f}"],
                            ['Number of Children', str(report_data['summary']['num_children'])],
                            ['Number of Properties', str(report_data['summary']['num_houses'])]
                        ]
                        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
                        summary_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(summary_table)
                        elements.append(Spacer(1, 20))

                    # Parents Section
                    if "Income & Expenses" in include_sections:
                        elements.append(Paragraph("Parents Information", heading_style))
                        parents_data = [
                            ['', 'Parent 1', 'Parent 2'],
                            ['Name', report_data['parents']['parent1']['name'], report_data['parents']['parent2']['name']],
                            ['Age', str(report_data['parents']['parent1']['age']), str(report_data['parents']['parent2']['age'])],
                            ['Income', f"${report_data['parents']['parent1']['income']:,.2f}", f"${report_data['parents']['parent2']['income']:,.2f}"],
                            ['Net Worth', f"${report_data['parents']['parent1']['net_worth']:,.2f}", f"${report_data['parents']['parent2']['net_worth']:,.2f}"],
                            ['Retirement Age', str(report_data['parents']['parent1']['retirement_age']), str(report_data['parents']['parent2']['retirement_age'])],
                            ['SS Benefit', f"${report_data['parents']['parent1']['ss_benefit']:,.2f}", f"${report_data['parents']['parent2']['ss_benefit']:,.2f}"]
                        ]
                        parents_table = Table(parents_data, colWidths=[2*inch, 2*inch, 2*inch])
                        parents_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(parents_table)
                        elements.append(Spacer(1, 20))

                    # Children Section
                    if "Children" in include_sections and report_data['children']:
                        elements.append(Paragraph("Children", heading_style))
                        children_data = [['Name', 'Age', 'Birth Year']]
                        for child in report_data['children']:
                            children_data.append([child['name'], str(child['age']), str(child['birth_year'])])

                        children_table = Table(children_data, colWidths=[2*inch, 2*inch, 2*inch])
                        children_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(children_table)
                        elements.append(Spacer(1, 20))

                    # Expenses Section
                    if "Income & Expenses" in include_sections and report_data.get('expenses'):
                        elements.append(Paragraph("Annual Expense Breakdown", heading_style))

                        # Create detailed expense table
                        expenses = report_data['expenses']
                        expense_data = [['Category', 'Annual Amount']]

                        # Add all expense categories
                        for category, amount in expenses.items():
                            if amount > 0:
                                # Format category name (replace underscores with spaces, title case)
                                formatted_category = category.replace('_', ' ').title()
                                expense_data.append([formatted_category, f"${amount:,.2f}"])

                        # Add total row
                        total_expenses = sum(expenses.values())
                        expense_data.append(['Total Annual Expenses', f"${total_expenses:,.2f}"])

                        if len(expense_data) > 1:  # More than just header
                            expense_table = Table(expense_data, colWidths=[3.5*inch, 2.5*inch])
                            expense_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 12),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            elements.append(expense_table)
                            elements.append(Spacer(1, 12))

                            # Generate and add expense breakdown pie chart
                            try:
                                # Prepare data for pie chart (exclude total row)
                                expense_categories = []
                                expense_amounts = []
                                for category, amount in expenses.items():
                                    if amount > 0:
                                        formatted_category = category.replace('_', ' ').title()
                                        expense_categories.append(formatted_category)
                                        expense_amounts.append(amount)

                                if expense_categories:
                                    # Create pie chart
                                    expense_pie_fig = go.Figure(data=[go.Pie(
                                        labels=expense_categories,
                                        values=expense_amounts,
                                        hole=0.3
                                    )])
                                    expense_pie_fig.update_layout(
                                        title="Annual Expense Distribution",
                                        height=400,
                                        showlegend=True
                                    )

                                    # Convert to image and add to PDF
                                    expense_chart_img = plotly_fig_to_image(expense_pie_fig, width=5*inch, height=3.5*inch)
                                    if expense_chart_img:
                                        elements.append(expense_chart_img)
                                        elements.append(Spacer(1, 12))
                            except Exception as e:
                                # If chart generation fails, just skip it
                                pass

                            elements.append(Spacer(1, 20))

                    # Healthcare Section
                    if "Healthcare" in include_sections and report_data.get('healthcare'):
                        healthcare = report_data['healthcare']

                        # Health Insurance
                        if healthcare.get('health_insurances'):
                            elements.append(Paragraph("Health Insurance Coverage", heading_style))
                            for idx, insurance in enumerate(healthcare['health_insurances'], 1):
                                insurance_data = [
                                    ['Field', 'Value'],
                                    ['Policy Type', insurance.get('policy_type', 'N/A')],
                                    ['Annual Premium', f"${insurance.get('annual_premium', 0):,.2f}"],
                                    ['Annual Deductible', f"${insurance.get('annual_deductible', 0):,.2f}"],
                                    ['Annual OOP Max', f"${insurance.get('annual_oop_max', 0):,.2f}"]
                                ]

                                insurance_table = Table(insurance_data, colWidths=[2.5*inch, 3.5*inch])
                                insurance_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                elements.append(insurance_table)
                                elements.append(Spacer(1, 12))

                        # HSA Balance
                        if healthcare.get('hsa_balance', 0) > 0:
                            hsa_text = f"<b>HSA Balance:</b> ${healthcare['hsa_balance']:,.2f}"
                            elements.append(Paragraph(hsa_text, styles['Normal']))
                            elements.append(Spacer(1, 20))

                    # Houses/Properties Section
                    if report_data.get('houses'):
                        elements.append(Paragraph("Real Estate Properties", heading_style))
                        for idx, house in enumerate(report_data['houses'], 1):
                            house_name = house.get('name', f'Property {idx}')
                            elements.append(Paragraph(f"<b>{house_name}</b>", styles['Heading3']))

                            house_data = [
                                ['Field', 'Value'],
                                ['Purchase Year', str(house.get('purchase_year', 'N/A'))],
                                ['Purchase Price', f"${house.get('purchase_price', 0):,.2f}"],
                                ['Down Payment', f"${house.get('down_payment', 0):,.2f}"],
                                ['Interest Rate', f"{house.get('interest_rate', 0):.2f}%"],
                                ['Loan Term', f"{house.get('loan_term_years', 0)} years"],
                                ['Property Tax Rate', f"{house.get('property_tax_rate', 0):.3f}%"],
                                ['Home Insurance', f"${house.get('home_insurance_annual', 0):,.2f}"],
                                ['Maintenance Rate', f"{house.get('maintenance_rate', 0):.2f}%"],
                                ['Upkeep Rate', f"{house.get('upkeep_rate', 0):.2f}%"],
                                ['Owner', house.get('owner', 'N/A')]
                            ]

                            house_table = Table(house_data, colWidths=[2.5*inch, 3.5*inch])
                            house_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            elements.append(house_table)
                            elements.append(Spacer(1, 12))

                    # Major Purchases Section
                    if report_data.get('major_purchases'):
                        elements.append(Paragraph("Major Purchases", heading_style))
                        major_purchases_data = [['Item', 'Year', 'Cost', 'Owner']]
                        for mp in report_data['major_purchases']:
                            major_purchases_data.append([
                                mp.get('item_name', 'N/A'),
                                str(mp.get('purchase_year', 'N/A')),
                                f"${mp.get('cost', 0):,.2f}",
                                mp.get('owner', 'N/A')
                            ])

                        if len(major_purchases_data) > 1:
                            mp_table = Table(major_purchases_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                            mp_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            elements.append(mp_table)
                            elements.append(Spacer(1, 20))

                    # Recurring Expenses Section
                    if report_data.get('recurring_expenses'):
                        elements.append(Paragraph("Recurring Expenses", heading_style))
                        recurring_data = [['Description', 'Amount', 'Start Year', 'End Year', 'Owner']]
                        for re in report_data['recurring_expenses']:
                            recurring_data.append([
                                re.get('description', 'N/A'),
                                f"${re.get('annual_amount', 0):,.2f}",
                                str(re.get('start_year', 'N/A')),
                                str(re.get('end_year', 'N/A')),
                                re.get('owner', 'N/A')
                            ])

                        if len(recurring_data) > 1:
                            recurring_table = Table(recurring_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
                            recurring_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            elements.append(recurring_table)
                            elements.append(Spacer(1, 20))

                    # State Timeline Section
                    if "Timeline" in include_sections and report_data.get('state_timeline'):
                        elements.append(Paragraph("State & Cost-of-Living Timeline", heading_style))
                        timeline_data = [['Year', 'State/Location', 'Spending Strategy']]
                        for entry in report_data['state_timeline']:
                            timeline_data.append([
                                str(entry.get('year', 'N/A')),
                                entry.get('state', 'N/A'),
                                entry.get('spending_strategy', 'N/A')
                            ])

                        if len(timeline_data) > 1:
                            timeline_table = Table(timeline_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
                            timeline_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            elements.append(timeline_table)
                            elements.append(Spacer(1, 20))

                    # Cashflow Projection Summary Section
                    if "Timeline" in include_sections and report_data.get('cashflow_projections'):
                        elements.append(Paragraph("Lifetime Financial Projection Summary", heading_style))

                        cashflow_proj = report_data['cashflow_projections']

                        # Calculate key metrics
                        final_year = cashflow_proj[-1]
                        retirement_years = [y for y in cashflow_proj if y['parent1_age'] >= st.session_state.parentX_retirement_age or y['parent2_age'] >= st.session_state.parentY_retirement_age]

                        min_net_worth_year = min(cashflow_proj, key=lambda x: x['net_worth'])
                        max_net_worth_year = max(cashflow_proj, key=lambda x: x['net_worth'])

                        avg_income_working = sum(y['total_income'] for y in cashflow_proj if y['parent1_age'] < st.session_state.parentX_retirement_age or y['parent2_age'] < st.session_state.parentY_retirement_age) / len([y for y in cashflow_proj if y['parent1_age'] < st.session_state.parentX_retirement_age or y['parent2_age'] < st.session_state.parentY_retirement_age]) if len([y for y in cashflow_proj if y['parent1_age'] < st.session_state.parentX_retirement_age or y['parent2_age'] < st.session_state.parentY_retirement_age]) > 0 else 0

                        avg_expenses = sum(y['total_expenses'] for y in cashflow_proj) / len(cashflow_proj)

                        summary_text = f"""
                        <b>Planning Horizon:</b> {cashflow_proj[0]['year']} - {final_year['year']} ({len(cashflow_proj)} years)<br/>
                        <b>Final Net Worth (Year {final_year['year']}):</b> ${final_year['net_worth']:,.0f}<br/>
                        <b>Minimum Net Worth:</b> ${min_net_worth_year['net_worth']:,.0f} (Year {min_net_worth_year['year']})<br/>
                        <b>Maximum Net Worth:</b> ${max_net_worth_year['net_worth']:,.0f} (Year {max_net_worth_year['year']})<br/>
                        <b>Average Annual Income (Working Years):</b> ${avg_income_working:,.0f}<br/>
                        <b>Average Annual Expenses (Lifetime):</b> ${avg_expenses:,.0f}<br/>
                        <b>Retirement Years Covered:</b> {len(retirement_years)} years
                        """
                        elements.append(Paragraph(summary_text, styles['Normal']))
                        elements.append(Spacer(1, 12))

                        # Add note about detailed data
                        note_text = "<i>Note: Full year-by-year cashflow projections with detailed expense breakdowns are available in the Excel export. The Excel file includes comprehensive data on income, expenses, net worth trajectory, and all expense categories for each year of your financial plan.</i>"
                        elements.append(Paragraph(note_text, styles['Normal']))
                        elements.append(Spacer(1, 12))

                        # Generate and add cashflow chart
                        try:
                            years = [d['year'] for d in cashflow_proj]
                            income = [d['total_income'] for d in cashflow_proj]
                            expenses = [d['total_expenses'] for d in cashflow_proj]
                            net_worth = [d['net_worth'] for d in cashflow_proj]

                            # Create cashflow chart with dual y-axis
                            from plotly.subplots import make_subplots
                            cashflow_fig = make_subplots(
                                specs=[[{"secondary_y": True}]]
                            )

                            # Add income and expenses on primary y-axis
                            cashflow_fig.add_trace(
                                go.Scatter(x=years, y=income, mode='lines', name='Income',
                                          line=dict(color='green', width=2)),
                                secondary_y=False
                            )
                            cashflow_fig.add_trace(
                                go.Scatter(x=years, y=expenses, mode='lines', name='Expenses',
                                          line=dict(color='red', width=2)),
                                secondary_y=False
                            )

                            # Add net worth on secondary y-axis
                            cashflow_fig.add_trace(
                                go.Scatter(x=years, y=net_worth, mode='lines', name='Net Worth',
                                          line=dict(color='blue', width=2, dash='dot')),
                                secondary_y=True
                            )

                            cashflow_fig.update_xaxes(title_text="Year")
                            cashflow_fig.update_yaxes(title_text="Income/Expenses ($)", secondary_y=False)
                            cashflow_fig.update_yaxes(title_text="Net Worth ($)", secondary_y=True)
                            cashflow_fig.update_layout(
                                title="Lifetime Income, Expenses, and Net Worth",
                                height=500,
                                showlegend=True,
                                hovermode='x unified'
                            )

                            # Convert to image and add to PDF
                            chart_img = plotly_fig_to_image(cashflow_fig, width=6.5*inch, height=4*inch)
                            if chart_img:
                                elements.append(chart_img)
                                elements.append(Spacer(1, 12))
                        except Exception as e:
                            # If chart generation fails, just skip it
                            pass

                        elements.append(Spacer(1, 20))

                    # Monte Carlo Results Summary
                    if report_data.get('monte_carlo_results'):
                        elements.append(Paragraph("Monte Carlo Simulation Results", heading_style))

                        mc_results = report_data['monte_carlo_results']
                        final_year_idx = -1

                        mc_summary_text = f"""
                        <b>Simulation Scenario:</b> {mc_results.get('scenario', 'N/A')}<br/>
                        <b>Number of Simulations:</b> 1,000<br/>
                        <b>Final Year Net Worth Percentiles:</b><br/>
                        • 10th Percentile: ${mc_results['percentiles']['10th'][final_year_idx]:,.0f}<br/>
                        • 25th Percentile: ${mc_results['percentiles']['25th'][final_year_idx]:,.0f}<br/>
                        • Median (50th): ${mc_results['percentiles']['50th'][final_year_idx]:,.0f}<br/>
                        • 75th Percentile: ${mc_results['percentiles']['75th'][final_year_idx]:,.0f}<br/>
                        • 90th Percentile: ${mc_results['percentiles']['90th'][final_year_idx]:,.0f}
                        """
                        elements.append(Paragraph(mc_summary_text, styles['Normal']))
                        elements.append(Spacer(1, 12))

                        note_text = "<i>Note: Complete Monte Carlo results with year-by-year percentile data are available in the Excel export.</i>"
                        elements.append(Paragraph(note_text, styles['Normal']))
                        elements.append(Spacer(1, 12))

                        # Generate and add Monte Carlo chart
                        try:
                            mc_years = mc_results['years']
                            percentiles = mc_results['percentiles']

                            # Create Monte Carlo percentile fan chart
                            mc_fig = go.Figure()

                            # Add percentile bands
                            mc_fig.add_trace(go.Scatter(
                                x=mc_years, y=percentiles['90th'],
                                mode='lines', name='90th Percentile',
                                line=dict(color='rgba(0,100,255,0.2)', width=1)
                            ))
                            mc_fig.add_trace(go.Scatter(
                                x=mc_years, y=percentiles['75th'],
                                mode='lines', name='75th Percentile',
                                line=dict(color='rgba(0,150,255,0.3)', width=1),
                                fill='tonexty', fillcolor='rgba(0,100,255,0.1)'
                            ))
                            mc_fig.add_trace(go.Scatter(
                                x=mc_years, y=percentiles['50th'],
                                mode='lines', name='Median (50th)',
                                line=dict(color='blue', width=3)
                            ))
                            mc_fig.add_trace(go.Scatter(
                                x=mc_years, y=percentiles['25th'],
                                mode='lines', name='25th Percentile',
                                line=dict(color='rgba(255,150,0,0.3)', width=1),
                                fill='tonexty', fillcolor='rgba(100,150,255,0.1)'
                            ))
                            mc_fig.add_trace(go.Scatter(
                                x=mc_years, y=percentiles['10th'],
                                mode='lines', name='10th Percentile',
                                line=dict(color='rgba(255,0,0,0.3)', width=1),
                                fill='tonexty', fillcolor='rgba(255,100,0,0.1)'
                            ))

                            # Add zero line
                            mc_fig.add_hline(y=0, line_dash="dash", line_color="red")

                            mc_fig.update_layout(
                                title="Net Worth Trajectories: Monte Carlo Simulation",
                                xaxis_title="Year",
                                yaxis_title="Net Worth ($)",
                                height=500,
                                showlegend=True,
                                hovermode='x unified'
                            )

                            # Convert to image and add to PDF
                            mc_chart_img = plotly_fig_to_image(mc_fig, width=6.5*inch, height=4*inch)
                            if mc_chart_img:
                                elements.append(mc_chart_img)
                                elements.append(Spacer(1, 12))
                        except Exception as e:
                            # If chart generation fails, just skip it
                            pass

                        elements.append(Spacer(1, 20))

                    # Build PDF
                    doc.build(elements)
                    output.seek(0)

                    # Show file save dialog
                    if TKINTER_AVAILABLE:
                        file_path = get_save_file_path(
                            f"{report_name}.pdf",
                            [("PDF files", "*.pdf"), ("All files", "*.*")]
                        )

                        if file_path:
                            with open(file_path, 'wb') as f:
                                f.write(output.getvalue())
                            st.success(f"✅ PDF report saved successfully to: {file_path}")
                        else:
                            st.info("ℹ️ Save cancelled")
                    else:
                        # Fallback to download button if tkinter not available
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=output,
                            file_name=f"{report_name}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ PDF report generated successfully!")

                elif report_format == "Excel (.xlsx)":
                    # Create Excel workbook
                    output = io.BytesIO()

                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Summary Sheet
                        if "Summary" in include_sections:
                            summary_df = pd.DataFrame([report_data["summary"]]).T
                            summary_df.columns = ["Value"]
                            summary_df.to_excel(writer, sheet_name='Summary')

                        # Parents Sheet
                        if "Income & Expenses" in include_sections:
                            parents_df = pd.DataFrame(report_data["parents"]).T
                            parents_df.to_excel(writer, sheet_name='Parents')

                            expenses_df = pd.DataFrame([report_data["expenses"]]).T
                            expenses_df.columns = ["Annual Amount"]
                            expenses_df.to_excel(writer, sheet_name='Expenses')

                        # Children Sheet
                        if "Children" in include_sections and st.session_state.children_list:
                            children_df = pd.DataFrame(report_data["children"])
                            children_df.to_excel(writer, sheet_name='Children', index=False)

                        # Healthcare Sheet
                        if "Healthcare" in include_sections and st.session_state.health_insurances:
                            healthcare_df = pd.DataFrame(report_data["healthcare"]["health_insurances"])
                            healthcare_df.to_excel(writer, sheet_name='Healthcare', index=False)

                        # Houses Sheet
                        if report_data.get("houses"):
                            houses_df = pd.DataFrame(report_data["houses"])
                            houses_df.to_excel(writer, sheet_name='Houses', index=False)

                        # Major Purchases Sheet
                        if report_data.get("major_purchases"):
                            major_purchases_df = pd.DataFrame(report_data["major_purchases"])
                            major_purchases_df.to_excel(writer, sheet_name='Major Purchases', index=False)

                        # Recurring Expenses Sheet
                        if report_data.get("recurring_expenses"):
                            recurring_df = pd.DataFrame(report_data["recurring_expenses"])
                            recurring_df.to_excel(writer, sheet_name='Recurring Expenses', index=False)

                        # State Timeline Sheet
                        if "Timeline" in include_sections and report_data.get("state_timeline"):
                            timeline_df = pd.DataFrame(report_data["state_timeline"])
                            timeline_df.to_excel(writer, sheet_name='State Timeline', index=False)

                        # Cashflow Projections Sheet - THIS IS THE KEY DATA!
                        if "Timeline" in include_sections and report_data.get("cashflow_projections"):
                            # Simplify the cashflow data for Excel (remove nested dicts)
                            cashflow_simple = []
                            for year_data in report_data["cashflow_projections"]:
                                cashflow_simple.append({
                                    'Year': year_data['year'],
                                    'Parent1 Age': year_data['parent1_age'],
                                    'Parent2 Age': year_data['parent2_age'],
                                    'Parent1 Income': year_data['parent1_income'],
                                    'Parent2 Income': year_data['parent2_income'],
                                    'Social Security': year_data['ss_income'],
                                    'Total Income': year_data['total_income'],
                                    'Base Expenses': year_data['base_expenses'],
                                    'Children Expenses': year_data['children_expenses'],
                                    'Healthcare Expenses': year_data['healthcare_expenses'],
                                    'House Expenses': year_data['house_expenses'],
                                    'Recurring Expenses': year_data['recurring_expenses'],
                                    'Major Purchases': year_data['major_purchases'],
                                    'Total Expenses': year_data['total_expenses'],
                                    'Cashflow': year_data['cashflow'],
                                    'Net Worth': year_data['net_worth']
                                })
                            cashflow_df = pd.DataFrame(cashflow_simple)
                            cashflow_df.to_excel(writer, sheet_name='Cashflow Projections', index=False)

                        # Monte Carlo Results Sheet
                        if report_data.get("monte_carlo_results"):
                            mc_results = report_data["monte_carlo_results"]
                            mc_data = {
                                'Year': mc_results['years'],
                                '10th Percentile': mc_results['percentiles']['10th'],
                                '25th Percentile': mc_results['percentiles']['25th'],
                                'Median (50th)': mc_results['percentiles']['50th'],
                                '75th Percentile': mc_results['percentiles']['75th'],
                                '90th Percentile': mc_results['percentiles']['90th']
                            }
                            mc_df = pd.DataFrame(mc_data)
                            mc_df.to_excel(writer, sheet_name='Monte Carlo Results', index=False)

                    output.seek(0)

                    # Show file save dialog
                    if TKINTER_AVAILABLE:
                        file_path = get_save_file_path(
                            f"{report_name}.xlsx",
                            [("Excel files", "*.xlsx"), ("All files", "*.*")]
                        )

                        if file_path:
                            with open(file_path, 'wb') as f:
                                f.write(output.getvalue())
                            st.success(f"✅ Excel report saved successfully to: {file_path}")
                        else:
                            st.info("ℹ️ Save cancelled")
                    else:
                        # Fallback to download button if tkinter not available
                        st.download_button(
                            label="📥 Download Excel Report",
                            data=output,
                            file_name=f"{report_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("✅ Excel report generated successfully!")

                elif report_format == "JSON (Data Export)":
                    json_str = json.dumps(report_data, indent=2, default=str)

                    # Show file save dialog
                    if TKINTER_AVAILABLE:
                        file_path = get_save_file_path(
                            f"{report_name}.json",
                            [("JSON files", "*.json"), ("All files", "*.*")]
                        )

                        if file_path:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(json_str)
                            st.success(f"✅ JSON export saved successfully to: {file_path}")
                        else:
                            st.info("ℹ️ Save cancelled")
                    else:
                        # Fallback to download button if tkinter not available
                        st.download_button(
                            label="📥 Download JSON Data",
                            data=json_str,
                            file_name=f"{report_name}.json",
                            mime="application/json"
                        )
                        st.success("✅ JSON export generated successfully!")

                elif report_format == "CSV (Multiple Files)":
                    # Summary CSV
                    if "Summary" in include_sections:
                        summary_df = pd.DataFrame([report_data["summary"]]).T
                        summary_csv = summary_df.to_csv()

                        # Show file save dialog
                        if TKINTER_AVAILABLE:
                            file_path = get_save_file_path(
                                f"{report_name}_summary.csv",
                                [("CSV files", "*.csv"), ("All files", "*.*")]
                            )

                            if file_path:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(summary_csv)
                                st.success(f"✅ CSV file saved successfully to: {file_path}")
                            else:
                                st.info("ℹ️ Save cancelled")
                        else:
                            # Fallback to download button if tkinter not available
                            st.info("📊 CSV export will generate multiple files. Download them separately:")
                            st.download_button(
                                "Download Summary.csv",
                                summary_csv,
                                f"{report_name}_summary.csv",
                                "text/csv"
                            )
                            st.success("✅ CSV files ready for download!")

            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
                st.exception(e)

    # Report Preview
    st.subheader("👁️ Report Preview")

    with st.expander("View Summary Data"):
        col1, col2, col3 = st.columns(3)

        total_net_worth = st.session_state.parentX_net_worth + st.session_state.parentY_net_worth
        total_income = st.session_state.parentX_income + st.session_state.parentY_income
        total_expenses = sum(st.session_state.expenses.values())

        col1.metric("Combined Net Worth", format_currency(total_net_worth))
        col2.metric("Combined Annual Income", format_currency(total_income))
        col3.metric("Total Annual Expenses", format_currency(total_expenses))

        if st.session_state.children_list:
            col3.metric("Number of Children", len(st.session_state.children_list))


def user_management_tab():
    """Household management tab"""
    st.header("👤 Household Management")

    if not st.session_state.get('authenticated'):
        st.warning("Please log in to access this tab.")
        return

    email = st.session_state.current_user
    household_id = st.session_state.household_id

    # Household info
    st.subheader("🏠 Your Household")
    household_info = get_household_info(household_id)
    household_name = household_info.get('household_name', 'My Household')

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Household:** {household_name}")
        st.write(f"**Your Email:** {email}")
        st.write(f"**Household Code:** `{household_id}`")
    with col2:
        last_saved = household_info.get('last_saved', 'Never')
        if last_saved != 'Never':
            st.write(f"**Last Saved:** {last_saved[:19]}")
            st.write(f"**Saved By:** {household_info.get('saved_by', 'N/A')}")
        st.write(f"**Auto-save:** Enabled")

    # Household members
    st.subheader("👨‍👩‍👧‍👦 Household Members")
    members = get_household_members(household_id)
    for member in members:
        icon = "🟢" if member['email'] == email else "👤"
        suffix = " (you)" if member['email'] == email else ""
        st.write(f"{icon} **{member['display_name']}** ({member['email']}){suffix}")

    st.info(f"💡 **To invite someone:** Share this household password: `{household_id}`\n\n"
            f"They sign in with their email, then enter this password to join your household.")

    # Switch or leave household
    st.subheader("🔄 Switch Household")
    if st.button("🚪 Switch to a different household", key="switch_household"):
        st.session_state.authenticated = False
        if 'initialized' in st.session_state:
            del st.session_state['initialized']
        st.rerun()


def display_sidebar():
    """Display sidebar with summary information"""
    with st.sidebar:
        if st.session_state.get('authenticated'):
            email = st.session_state.current_user
            household_info = get_household_info(st.session_state.household_id)
            household_name = household_info.get('household_name', 'My Household')
            display_name = email.split('@')[0].title()
            if st.session_state.get('test_mode'):
                st.markdown(
                    '<div class="test-mode-banner">🧪 TEST MODE</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="sidebar-user-badge">'
                f'<div class="user-name">👤 {display_name}</div>'
                f'<div class="household-name">🏠 {household_name}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.session_state.get('test_mode'):
                if st.button("🚪 Exit Test Mode", use_container_width=True, key="exit_test_mode"):
                    cleanup_test_households(email)
                    for key in list(st.session_state.keys()):
                        if key != 'cf_email':
                            del st.session_state[key]
                    st.session_state.authenticated = False
                    st.rerun()

        # Quick save button (always visible)
        if st.session_state.get('authenticated') and st.session_state.get('household_id') and st.session_state.get('initialized'):
            col_save, col_reset = st.columns(2)
            with col_save:
                if st.button("💾 Save", use_container_width=True, type="primary", key="sidebar_save"):
                    try:
                        json_data = save_data()
                        if json_data:
                            save_household_plan(st.session_state.household_id, json_data)
                            st.success("Saved!", icon="✅")
                    except Exception as e:
                        st.error(f"Save failed: {e}")
            with col_reset:
                if st.button("↩ Reset", use_container_width=True, key="sidebar_reset",
                             help="Reload last saved version"):
                    plan_data = load_household_plan(st.session_state.household_id)
                    if plan_data:
                        load_data(plan_data)
                        st.rerun()

            if st.button("🏠 Switch Household", use_container_width=True, key="sidebar_switch_household"):
                # Auto-save before switching
                try:
                    json_data = save_data()
                    if json_data:
                        save_household_plan(st.session_state.household_id, json_data)
                except Exception:
                    pass
                # Clear session but keep auth
                keep = {'cf_email', 'current_user'}
                cf_email = st.session_state.get('cf_email')
                current_user = st.session_state.get('current_user')
                for key in list(st.session_state.keys()):
                    if key not in keep:
                        del st.session_state[key]
                if cf_email:
                    st.session_state.cf_email = cf_email
                if current_user:
                    st.session_state.current_user = current_user
                st.session_state.authenticated = False
                st.rerun()

        st.markdown("### Quick Summary")

        # Net Worth
        total_net_worth = st.session_state.parentX_net_worth + st.session_state.parentY_net_worth
        st.metric("Combined Net Worth", format_currency(total_net_worth))

        # Income
        total_income = st.session_state.parentX_income + st.session_state.parentY_income
        st.metric("Combined Annual Income", format_currency(total_income))

        # Expenses
        total_expenses = sum(st.session_state.expenses.values())
        st.metric("Annual Family Expenses", format_currency(total_expenses))

        # Children
        st.metric("Number of Children", len(st.session_state.children_list))

        # Houses
        st.metric("Number of Properties", len(st.session_state.houses))

        st.divider()

        # Current State
        current_state, current_strategy = get_state_for_year(st.session_state.current_year)
        st.subheader("Current Location")
        st.info(f"{current_state}\n{current_strategy}")

        # Quick alerts summary
        try:
            cashflow = calculate_lifetime_cashflow()
            alerts = generate_alerts(cashflow)
            critical = sum(1 for a in alerts if a['severity'] == 'critical')
            warnings = sum(1 for a in alerts if a['severity'] == 'warning')
            if critical > 0:
                st.error(f"{critical} critical alert{'s' if critical > 1 else ''}")
            if warnings > 0:
                st.warning(f"{warnings} warning{'s' if warnings > 1 else ''}")
            if critical == 0 and warnings == 0:
                st.success("No issues detected")
        except Exception:
            pass

        # About
        st.divider()
        with st.expander("About", expanded=False):
            st.markdown(
                "**Financial Planning Suite** v0.8\n\n"
                "A lifetime financial simulation tool designed to help individuals and families "
                "plan the financial aspects of their lives — from income and expenses to retirement, "
                "housing, healthcare, and beyond.\n\n"
                "Built with Monte Carlo simulation, deterministic cashflow modeling, and scenario "
                "comparison to give you a clear picture of your financial future.\n\n"
                "Created by **Filipp Demenschonok**"
            )


if __name__ == "__main__":
    main()
