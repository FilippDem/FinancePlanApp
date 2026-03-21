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
import secrets
import os
from pathlib import Path
import uuid

# Set page configuration
st.set_page_config(
    page_title="Financial Planning Application",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# DATA PERSISTENCE & AUTHENTICATION SYSTEM
# =====================================================

DATA_DIR = Path(os.environ.get('DATA_DIR', './data'))
USERS_FILE = DATA_DIR / 'users.json'
HOUSEHOLDS_DIR = DATA_DIR / 'households'


def ensure_data_dirs():
    """Create data directories if they don't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HOUSEHOLDS_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)


def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password with a salt"""
    if salt is None:
        salt = secrets.token_hex(32)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex(), salt


def load_users() -> dict:
    """Load users database from disk"""
    ensure_data_dirs()
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users: dict):
    """Save users database to disk"""
    ensure_data_dirs()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def create_user(username: str, password: str, display_name: str, household_name: str = None, household_id: str = None) -> tuple:
    """Create a new user. Returns (success, message)"""
    users = load_users()

    if username.lower() in {u.lower() for u in users}:
        return False, "Username already exists"

    if len(password) < 4:
        return False, "Password must be at least 4 characters"

    password_hash, salt = hash_password(password)

    # Create or join household
    if household_id:
        # Join existing household
        household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
        if not household_file.exists():
            return False, "Household code not found"
    else:
        # Create new household
        household_id = str(uuid.uuid4())[:8]
        household_file = HOUSEHOLDS_DIR / f"{household_id}.json"
        ensure_data_dirs()
        with open(household_file, 'w') as f:
            json.dump({'household_name': household_name or f"{display_name}'s Household", 'created_by': username, 'created_at': datetime.now().isoformat()}, f)

    users[username] = {
        'password_hash': password_hash,
        'salt': salt,
        'display_name': display_name,
        'household_id': household_id,
        'created_at': datetime.now().isoformat()
    }

    save_users(users)
    return True, f"Account created! Your household code is: **{household_id}**"


def authenticate_user(username: str, password: str) -> tuple:
    """Authenticate a user. Returns (success, user_data or error_message)"""
    users = load_users()

    if username not in users:
        return False, "Invalid username or password"

    user = users[username]
    password_hash, _ = hash_password(password, user['salt'])

    if password_hash != user['password_hash']:
        return False, "Invalid username or password"

    return True, user


def get_household_members(household_id: str) -> list:
    """Get all members of a household"""
    users = load_users()
    members = []
    for username, user_data in users.items():
        if user_data.get('household_id') == household_id:
            members.append({'username': username, 'display_name': user_data['display_name']})
    return members


def save_household_plan(household_id: str, plan_data: str):
    """Save financial plan data to household file"""
    ensure_data_dirs()
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"

    # Load existing household metadata
    try:
        with open(household_file, 'r') as f:
            household = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        household = {}

    # Preserve metadata, update plan
    household['plan_data'] = json.loads(plan_data) if isinstance(plan_data, str) else plan_data
    household['last_saved'] = datetime.now().isoformat()
    household['saved_by'] = st.session_state.get('current_user', 'unknown')

    with open(household_file, 'w') as f:
        json.dump(household, f, indent=2)


def load_household_plan(household_id: str) -> Optional[str]:
    """Load financial plan data from household file"""
    household_file = HOUSEHOLDS_DIR / f"{household_id}.json"

    if not household_file.exists():
        return None

    try:
        with open(household_file, 'r') as f:
            household = json.load(f)
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


def login_page():
    """Display login/registration page"""
    st.title("💰 Financial Planning Suite")
    st.markdown("### Welcome! Please log in or create an account.")

    users = load_users()
    has_users = len(users) > 0

    if has_users:
        login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])
    else:
        st.info("👋 **First time setup!** Create your admin account to get started.")
        register_tab = st.container()
        login_tab = None

    # Login form
    if login_tab is not None:
        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary")

                if submitted and username and password:
                    success, result = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.user_data = result
                        st.session_state.household_id = result['household_id']

                        # Load household plan if exists
                        plan_data = load_household_plan(result['household_id'])
                        if plan_data:
                            load_data(plan_data)

                        st.rerun()
                    else:
                        st.error(result)

    # Registration form
    with register_tab:
        with st.form("register_form"):
            st.subheader("Create Account")
            new_username = st.text_input("Choose Username", key="reg_username")
            new_display_name = st.text_input("Display Name", key="reg_display")
            new_password = st.text_input("Choose Password (min 4 characters)", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

            st.markdown("---")
            st.subheader("Household Setup")
            household_choice = st.radio(
                "Household Option",
                ["Create new household", "Join existing household"],
                key="reg_household_choice"
            )

            household_name = ""
            join_code = ""
            if household_choice == "Create new household":
                household_name = st.text_input("Household Name (e.g., 'The Smith Family')", key="reg_household_name")
            else:
                join_code = st.text_input("Enter Household Code (from your partner)", key="reg_join_code")

            submitted = st.form_submit_button("Create Account", type="primary")

            if submitted:
                if not new_username or not new_password or not new_display_name:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success, message = create_user(
                        new_username,
                        new_password,
                        new_display_name,
                        household_name=household_name if household_choice == "Create new household" else None,
                        household_id=join_code if household_choice == "Join existing household" else None
                    )
                    if success:
                        st.success(message)
                        st.info("You can now log in with your credentials!")
                    else:
                        st.error(message)

# Historical S&P 500 Annual Returns (approximately 1924-2023, 100 years)
# These are approximate total returns including dividends
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

# Children expense templates by state and spending strategy
CHILDREN_EXPENSE_TEMPLATES = {
    "California": {
        "Conservative": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 28000, 28000, 28000, 28000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 35000, 35000, 35000, 35000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 55000, 55000, 55000, 55000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    },
    "Washington": {
        "Conservative": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 22000, 22000, 22000, 22000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "Average": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 28000, 28000, 28000, 28000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        },
        "High-end": {
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
            'Education': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 45000, 45000, 45000, 45000, 0, 0, 0, 0,
                          0, 0, 0, 0, 0]
        }
    }
}

# Family expense templates by state and spending strategy
FAMILY_EXPENSE_TEMPLATES = {
    "California": {
        "Conservative": {
            'Food & Groceries': 14400,
            'Clothing': 3600,
            'Transportation': 10000,
            'Entertainment & Activities': 4800,
            'Personal Care': 2400,
            'Parent Retirement Help': 12000,
            'Other Expenses': 6000
        },
        "Average": {
            'Food & Groceries': 18000,
            'Clothing': 4800,
            'Transportation': 13000,
            'Entertainment & Activities': 7200,
            'Personal Care': 3600,
            'Parent Retirement Help': 18000,
            'Other Expenses': 8400
        },
        "High-end": {
            'Food & Groceries': 24000,
            'Clothing': 7200,
            'Transportation': 18000,
            'Entertainment & Activities': 12000,
            'Personal Care': 6000,
            'Parent Retirement Help': 30000,
            'Other Expenses': 12000
        }
    },
    "Washington": {
        "Conservative": {
            'Food & Groceries': 13200,
            'Clothing': 3000,
            'Transportation': 9000,
            'Entertainment & Activities': 4200,
            'Personal Care': 2100,
            'Parent Retirement Help': 10000,
            'Other Expenses': 5400
        },
        "Average": {
            'Food & Groceries': 16800,
            'Clothing': 4200,
            'Transportation': 12000,
            'Entertainment & Activities': 6600,
            'Personal Care': 3000,
            'Parent Retirement Help': 16000,
            'Other Expenses': 7800
        },
        "High-end": {
            'Food & Groceries': 22800,
            'Clothing': 6600,
            'Transportation': 16800,
            'Entertainment & Activities': 10800,
            'Personal Care': 5400,
            'Parent Retirement Help': 28000,
            'Other Expenses': 10800
        }
    },
    "Texas": {
        "Conservative": {
            'Food & Groceries': 12600,
            'Clothing': 2800,
            'Transportation': 8400,
            'Entertainment & Activities': 3900,
            'Personal Care': 1800,
            'Parent Retirement Help': 9000,
            'Other Expenses': 5100
        },
        "Average": {
            'Food & Groceries': 15600,
            'Clothing': 3900,
            'Transportation': 11400,
            'Entertainment & Activities': 6000,
            'Personal Care': 2700,
            'Parent Retirement Help': 15000,
            'Other Expenses': 7200
        },
        "High-end": {
            'Food & Groceries': 21000,
            'Clothing': 6000,
            'Transportation': 15600,
            'Entertainment & Activities': 9600,
            'Personal Care': 4800,
            'Parent Retirement Help': 25000,
            'Other Expenses': 10200
        }
    }
}


# Data Classes
@dataclass
class MajorPurchase:
    name: str
    year: int
    amount: float
    financing_years: int = 0
    interest_rate: float = 0.0


@dataclass
class RecurringExpense:
    name: str
    category: str  # "Vehicle", "Home", "Travel", "Technology", "Other"
    amount: float
    frequency_years: int  # How often it recurs (e.g., 10 for every decade)
    start_year: int
    end_year: Optional[int] = None  # When to stop recurring (None = forever)
    inflation_adjust: bool = True
    parent: str = "Both"  # "Parent1", "Parent2", "Both"
    financing_years: int = 0
    interest_rate: float = 0.0


@dataclass
class EconomicScenario:
    name: str
    investment_return: float
    inflation_rate: float
    expense_growth_rate: float
    healthcare_inflation_rate: float


@dataclass
class HouseTimelineEntry:
    year: int
    status: str  # "Own_Live", "Own_Rent", "Sell"
    rental_income: float = 0.0  # Monthly rental income if renting


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
    upkeep_costs: float  # Annual upkeep/repair costs
    owner: str = "Shared"  # "Parent1", "Parent2", "Shared"
    timeline: List[HouseTimelineEntry] = None  # Timeline of house status changes

    def __post_init__(self):
        if self.timeline is None:
            # Default timeline: own and live in from purchase year
            self.timeline = [HouseTimelineEntry(self.purchase_year, "Own_Live", 0.0)]

    def get_status_for_year(self, year: int) -> tuple:
        """Get status and rental income for a specific year"""
        if not self.timeline:
            return "Own_Live", 0.0

        # Sort timeline by year
        sorted_timeline = sorted(self.timeline, key=lambda x: x.year)

        # Find the most recent entry before or at the given year
        current_status = "Own_Live"
        current_rental = 0.0

        for entry in sorted_timeline:
            if entry.year <= year:
                current_status = entry.status
                current_rental = entry.rental_income
            else:
                break

        return current_status, current_rental


# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        # Current year setting
        st.session_state.current_year = 2025

        # Parent naming and emojis - CHANGED defaults
        st.session_state.parent1_name = "Filipp"
        st.session_state.parent1_emoji = "👨"
        st.session_state.parent2_name = "Erin"
        st.session_state.parent2_emoji = "👩"

        # Marriage year setting
        st.session_state.marriage_year = "N/A"

        # Parent X data
        st.session_state.parentX_age = 35
        st.session_state.parentX_net_worth = 85000.0
        st.session_state.parentX_income = 95000.0
        st.session_state.parentX_raise = 3.5
        st.session_state.parentX_retirement_age = 65
        st.session_state.parentX_ss_benefit = 2500.0
        st.session_state.parentX_job_changes = pd.DataFrame({
            'Year': [2027, 2032],
            'New Income': [105000, 120000]
        })

        # Parent Y data
        st.session_state.parentY_age = 33
        st.session_state.parentY_net_worth = 75000.0
        st.session_state.parentY_income = 85000.0
        st.session_state.parentY_raise = 3.2
        st.session_state.parentY_retirement_age = 65
        st.session_state.parentY_ss_benefit = 2200.0
        st.session_state.parentY_job_changes = pd.DataFrame({
            'Year': [2028, 2033],
            'New Income': [92000, 105000]
        })

        # NEW: Dynamic expense categories with Parent Retirement Help
        st.session_state.expense_categories = [
            'Food & Groceries',
            'Clothing',
            'Transportation',
            'Entertainment & Activities',
            'Personal Care',
            'Parent Retirement Help',
            'Other Expenses'
        ]

        # Expense categories - UPDATED with new category
        st.session_state.expenses = {
            'Food & Groceries': 16800.0,
            'Clothing': 4200.0,
            'Transportation': 12000.0,
            'Entertainment & Activities': 6000.0,
            'Personal Care': 3600.0,
            'Parent Retirement Help': 20000.0,  # NEW category
            'Other Expenses': 7200.0
        }

        # Children expenses table (Age 0-30 with expense categories)
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
            'Daycare': [20376 if i < 5 else 0 for i in range(31)],  # $1,698/month for ages 0-4
            'Education': [25000 if 18 <= i <= 21 else 0 for i in range(31)]  # College costs
        })

        # Children instances (list of children with birth years)
        st.session_state.children_list = []
        st.session_state.children_today_dollars = True  # Toggle for today dollars vs inflation adjusted

        # Major purchases and recurring expenses
        st.session_state.major_purchases = []
        st.session_state.recurring_expenses = [
            RecurringExpense(
                name="Parent X Vehicle",
                category="Vehicle",
                amount=35000.0,
                frequency_years=10,
                start_year=2025,
                end_year=None,
                inflation_adjust=True,
                parent="ParentX",
                financing_years=5,
                interest_rate=0.045
            ),
            RecurringExpense(
                name="Parent Y Vehicle",
                category="Vehicle",
                amount=32000.0,
                frequency_years=10,
                start_year=2027,
                end_year=None,
                inflation_adjust=True,
                parent="ParentY",
                financing_years=5,
                interest_rate=0.045
            )
        ]

        # Economic scenarios
        st.session_state.economic_scenarios = {
            'Conservative': EconomicScenario('Conservative', 0.04, 0.03, 0.02, 0.05),
            'Moderate': EconomicScenario('Moderate', 0.06, 0.025, 0.02, 0.045),
            'Aggressive': EconomicScenario('Aggressive', 0.08, 0.02, 0.02, 0.04)
        }

        # Active economic scenario
        st.session_state.active_scenario = 'Moderate'

        # Houses (updated to list of House objects with timeline)
        st.session_state.houses = [
            House(
                name="Primary Home",
                purchase_year=2020,
                purchase_price=600000.0,
                current_value=650000.0,
                mortgage_balance=500000.0,
                mortgage_rate=0.067,
                mortgage_years_left=28,
                property_tax_rate=0.0092,
                home_insurance=1800.0,
                maintenance_rate=0.015,
                upkeep_costs=3000.0,
                owner="Shared",  # NEW field
                timeline=[HouseTimelineEntry(2020, "Own_Live", 0.0)]
            )
        ]

        # Tax settings
        st.session_state.state_tax_rate = 0.0  # State income tax rate
        st.session_state.pretax_401k = 0.0  # Pre-tax 401k contributions

        # Social Security insolvency settings (NEW)
        st.session_state.ss_insolvency_enabled = True
        st.session_state.ss_shortfall_percentage = 30.0  # 30% shortfall

        # Monte Carlo settings (Enhanced with historical option)
        st.session_state.mc_start_year = 2025
        st.session_state.mc_years = 30
        st.session_state.mc_simulations = 1000
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

        # NEW: Historical simulation settings
        st.session_state.mc_use_historical = False  # Toggle for historical vs traditional
        st.session_state.mc_historical_start_year = 1924  # Starting year for historical data
        st.session_state.mc_show_historical_stats = False  # Show historical statistics

        # NEW: Inflation normalization toggle
        st.session_state.mc_normalize_to_today_dollars = False

        # Display preferences
        st.session_state.inflation_adjusted_display = True
        st.session_state.default_inflation_rate = 0.025

        # NEW: Internal save/load system
        st.session_state.saved_scenarios = {}  # Dictionary to store named scenarios

        st.session_state.initialized = True


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

    # 2024 tax brackets for married filing jointly
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

    # Standard deduction for 2024
    standard_deduction = 29200 if filing_status == "married_jointly" else 14600

    # Calculate adjusted gross income
    adjusted_gross_income = max(0, gross_income - pretax_deductions)

    # Calculate taxable income
    taxable_income = max(0, adjusted_gross_income - standard_deduction)

    # Federal income tax
    federal_tax = calculate_federal_income_tax(taxable_income, filing_status)

    # State income tax (on AGI)
    state_tax = adjusted_gross_income * state_tax_rate

    # FICA taxes (on gross income, up to limits)
    # Social Security: 6.2% up to $160,200 (2024)
    # Medicare: 1.45% on all income + 0.9% additional on income over $250,000 (married)
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


def format_currency(value, show_thousands=False):
    """Format number as currency without cents, optionally show in thousands"""
    if show_thousands and abs(value) >= 10000:
        return f"${value / 1000:.0f}k"
    else:
        return f"${value:,.0f}"


def timeline_tab():
    """Simplified Timeline tab that shows data from other tabs"""
    st.header("🗓️ Financial Timeline Overview")

    st.info(
        "📅 **Timeline View**: This tab shows a consolidated timeline based on data from other tabs. Modify data in individual tabs to see changes here.")

    # Timeline controls
    col1, col2 = st.columns(2)

    with col1:
        start_year = st.number_input("Timeline Start Year", min_value=2020, max_value=2040,
                                     value=int(st.session_state.current_year), key="timeline_start")

    with col2:
        end_year = st.number_input("Timeline End Year", min_value=start_year + 1, max_value=2080,
                                   value=int(start_year + 30),
                                   key="timeline_end")

    # Create timeline visualization
    timeline_data = []
    years = list(range(start_year, end_year + 1))

    # Parent career timelines
    for year in years:
        parentX_age = st.session_state.parentX_age + (year - st.session_state.current_year)
        parentY_age = st.session_state.parentY_age + (year - st.session_state.current_year)

        # Parent X career
        if parentX_age >= 18 and parentX_age < st.session_state.parentX_retirement_age:
            # Calculate income with raises and job changes
            base_income = st.session_state.parentX_income
            years_elapsed = year - st.session_state.current_year
            current_income = base_income * ((1 + st.session_state.parentX_raise / 100) ** years_elapsed)

            # Apply job changes
            for _, job_change in st.session_state.parentX_job_changes.iterrows():
                if year >= job_change['Year']:
                    years_since_change = year - job_change['Year']
                    current_income = job_change['New Income'] * (
                            (1 + st.session_state.parentX_raise / 100) ** years_since_change)

            timeline_data.append({
                'Year': year,
                'Category': f'{st.session_state.parent1_name} Career',
                'Event': f'Age {parentX_age}: {format_currency(current_income)}/year',
                'Type': 'Income',
                'Amount': current_income
            })
        elif parentX_age >= st.session_state.parentX_retirement_age:
            timeline_data.append({
                'Year': year,
                'Category': f'{st.session_state.parent1_name} Career',
                'Event': f'Age {parentX_age}: Retired + Social Security',
                'Type': 'Retirement',
                'Amount': st.session_state.parentX_ss_benefit * 12
            })

        # Parent Y career
        if parentY_age >= 18 and parentY_age < st.session_state.parentY_retirement_age:
            # Calculate income with raises and job changes
            base_income = st.session_state.parentY_income
            years_elapsed = year - st.session_state.current_year
            current_income = base_income * ((1 + st.session_state.parentY_raise / 100) ** years_elapsed)

            # Apply job changes
            for _, job_change in st.session_state.parentY_job_changes.iterrows():
                if year >= job_change['Year']:
                    years_since_change = year - job_change['Year']
                    current_income = job_change['New Income'] * (
                            (1 + st.session_state.parentY_raise / 100) ** years_since_change)

            timeline_data.append({
                'Year': year,
                'Category': f'{st.session_state.parent2_name} Career',
                'Event': f'Age {parentY_age}: {format_currency(current_income)}/year',
                'Type': 'Income',
                'Amount': current_income
            })
        elif parentY_age >= st.session_state.parentY_retirement_age:
            timeline_data.append({
                'Year': year,
                'Category': f'{st.session_state.parent2_name} Career',
                'Event': f'Age {parentY_age}: Retired + Social Security',
                'Type': 'Retirement',
                'Amount': st.session_state.parentY_ss_benefit * 12
            })

    # Children timeline
    for child in st.session_state.children_list:
        for year in years:
            child_age = year - child['birth_year']
            if child_age == 0:
                timeline_data.append({
                    'Year': year,
                    'Category': 'Children',
                    'Event': f"{child['name']} born",
                    'Type': 'Birth',
                    'Amount': 0
                })
            elif child_age == 18:
                timeline_data.append({
                    'Year': year,
                    'Category': 'Children',
                    'Event': f"{child['name']} turns 18 (college age)",
                    'Type': 'Education',
                    'Amount': 0
                })
            elif child_age == 22:
                timeline_data.append({
                    'Year': year,
                    'Category': 'Children',
                    'Event': f"{child['name']} graduates college",
                    'Type': 'Education',
                    'Amount': 0
                })

    # House timeline
    for house in st.session_state.houses:
        for year in years:
            status, rental_income = house.get_status_for_year(year)

            # Check for status changes
            if year > start_year:
                prev_status, _ = house.get_status_for_year(year - 1)
                if status != prev_status:
                    if status == "Own_Live":
                        event_text = f"{house.name}: Move back in"
                    elif status == "Own_Rent":
                        event_text = f"{house.name}: Start renting out ({format_currency(rental_income)}/mo)"
                    elif status == "Sell":
                        event_text = f"{house.name}: Sell property"

                    timeline_data.append({
                        'Year': year,
                        'Category': 'Real Estate',
                        'Event': event_text,
                        'Type': 'Property',
                        'Amount': rental_income * 12 if status == "Own_Rent" else 0
                    })

    # Major purchases timeline
    for purchase in st.session_state.major_purchases:
        if start_year <= purchase.year <= end_year:
            timeline_data.append({
                'Year': purchase.year,
                'Category': 'Major Purchases',
                'Event': f"{purchase.name}: {format_currency(purchase.amount)}",
                'Type': 'Purchase',
                'Amount': purchase.amount
            })

    # Recurring expenses timeline
    for expense in st.session_state.recurring_expenses:
        for year in years:
            if (year >= expense.start_year and
                    (expense.end_year is None or year <= expense.end_year) and
                    (year - expense.start_year) % expense.frequency_years == 0):
                timeline_data.append({
                    'Year': year,
                    'Category': 'Recurring Expenses',
                    'Event': f"{expense.name}: {format_currency(expense.amount)}",
                    'Type': 'Expense',
                    'Amount': expense.amount
                })

    if timeline_data:
        # Convert to DataFrame for display
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values(['Year', 'Category'])

        # Create interactive timeline chart
        fig = go.Figure()

        categories = timeline_df['Category'].unique()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

        for i, category in enumerate(categories):
            cat_data = timeline_df[timeline_df['Category'] == category]

            fig.add_trace(go.Scatter(
                x=cat_data['Year'],
                y=[i] * len(cat_data),
                mode='markers+text',
                name=category,
                text=cat_data['Event'],
                textposition='top center',
                marker=dict(
                    size=10,
                    color=colors[i % len(colors)],
                    symbol='circle'
                ),
                hovertemplate='<b>%{text}</b><br>Year: %{x}<extra></extra>'
            ))

        fig.update_layout(
            title=f'Financial Timeline Overview ({start_year}-{end_year})',
            xaxis_title='Year',
            yaxis_title='Categories',
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(categories))),
                ticktext=categories
            ),
            height=600,
            showlegend=True,
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        st.subheader("📋 Timeline Events Summary")

        # Format the display dataframe
        display_df = timeline_df[['Year', 'Category', 'Event']].copy()
        display_df = display_df.sort_values(['Year', 'Category'])

        st.dataframe(display_df, use_container_width=True, height=400)

        # Key insights
        st.subheader("🔍 Key Timeline Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            retirement_years = timeline_df[timeline_df['Type'] == 'Retirement']['Year'].tolist()
            if retirement_years:
                first_retirement = min(retirement_years)
                st.metric("First Parent Retires", first_retirement)
            else:
                st.metric("First Parent Retires", "After timeline")

        with col2:
            birth_years = timeline_df[timeline_df['Type'] == 'Birth']['Year'].tolist()
            if birth_years:
                st.metric("Children Born", len(birth_years))
                if len(birth_years) > 1:
                    st.write(f"Years: {', '.join(map(str, birth_years))}")
            else:
                st.metric("Children Born", 0)

        with col3:
            major_purchases = timeline_df[timeline_df['Type'] == 'Purchase']
            if not major_purchases.empty:
                total_purchases = major_purchases['Amount'].sum()
                st.metric("Total Major Purchases", format_currency(total_purchases, show_thousands=True))
            else:
                st.metric("Total Major Purchases", "$0")

    else:
        st.info("No timeline events found for the selected period. Add data in other tabs to populate the timeline.")


def parent_settings_tab():
    """Enhanced Parent Settings tab with instructions"""
    st.header("⚙️ Settings and Instructions")

    # Current year setting
    st.subheader("📅 Current Year Setting")
    st.session_state.current_year = st.number_input(
        "Current Year",
        min_value=2020,
        max_value=2030,
        value=int(st.session_state.current_year),
        step=1,
        help="Set the current year to track parent ages accurately"
    )

    # Marriage year setting
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
        "Marriage Year (when assets became family assets)",
        options=marriage_options,
        index=marriage_index,
        help="Select the year when individual assets became family assets, or N/A if not applicable"
    )

    st.session_state.marriage_year = selected_marriage

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Customize Parent 1")
        st.session_state.parent1_name = st.text_input(
            "Parent 1 Name",
            value=st.session_state.parent1_name,
            key="parent1_name_input"
        )

        emoji_options = ["👨", "👩", "🧑", "👤", "👼", "🏃", "⭐", "🎯"]
        current_emoji_idx = emoji_options.index(
            st.session_state.parent1_emoji) if st.session_state.parent1_emoji in emoji_options else 0

        st.session_state.parent1_emoji = st.selectbox(
            "Parent 1 Emoji",
            emoji_options,
            index=current_emoji_idx,
            key="parent1_emoji_select"
        )

    with col2:
        st.subheader("🔧 Customize Parent 2")
        st.session_state.parent2_name = st.text_input(
            "Parent 2 Name",
            value=st.session_state.parent2_name,
            key="parent2_name_input"
        )

        current_emoji_idx = emoji_options.index(
            st.session_state.parent2_emoji) if st.session_state.parent2_emoji in emoji_options else 1

        st.session_state.parent2_emoji = st.selectbox(
            "Parent 2 Emoji",
            emoji_options,
            index=current_emoji_idx,
            key="parent2_emoji_select"
        )

    st.info("💡 Changes to parent names and emojis will be reflected in all tabs after you navigate to them.")

    # NEW: Instructions Section
    st.header("📖 Application Instructions")

    st.markdown("""
    ### How to Use This Financial Planning Application

    This comprehensive financial planning tool helps you model your family's financial future across multiple dimensions. 
    Here's how to use each tab effectively:

    #### 📊 Tab-by-Tab Guide:

    **⚙️ Settings and Instructions (This Tab)**
    - Set the current year for accurate age tracking
    - Customize parent names and emojis used throughout the app
    - Define marriage year for asset tracking purposes
    - Review these instructions anytime

    **👨/👩 Parent Tabs**
    - Enter each parent's current age, net worth, and income
    - Set expected annual raises and retirement ages
    - Add job changes with new income levels and timing
    - Configure Social Security benefit estimates

    **💸 Family Expenses**
    - Define annual family expense categories (fully customizable)
    - Use expense templates by state and spending level
    - Configure tax settings including state taxes and 401(k) contributions
    - Add one-time major purchases and recurring expenses

    **👶 Children**
    - Add children with birth years
    - Customize expense templates by age (0-30) and category
    - Use state-specific templates or create custom expense schedules
    - Prevent duplicate child names for better tracking

    **🏠 House Portfolio**
    - Track multiple properties with ownership attribution
    - Define timelines for living in, renting out, or selling properties
    - Monitor mortgage payments, property taxes, and maintenance costs
    - Assign ownership to individual parents or family

    **📈 Economy**
    - Choose from Conservative, Moderate, or Aggressive economic scenarios
    - Adjust investment returns, inflation rates, and expense growth
    - View historical stock market performance statistics
    - Select active scenario used throughout calculations

    **🖼️ Retirement**
    - Review combined retirement timeline and Social Security benefits
    - Configure Social Security insolvency adjustments
    - Compare early vs. delayed retirement benefit options
    - Analyze retirement income replacement ratios

    **🗓️ Timeline**
    - View consolidated timeline of all financial events
    - See career changes, children milestones, and house transitions
    - Identify key planning periods and potential conflicts
    - Export timeline data for external use

    **📊 Analysis**
    - Run comprehensive Monte Carlo simulations
    - Choose between traditional statistical modeling or historical performance
    - View detailed yearly expense breakdowns
    - Analyze net worth projections with confidence intervals
    - Option to normalize results to today's purchasing power

    **💾 Save/Load**
    - Save multiple named scenarios within the application
    - Export scenarios to external files for backup
    - Load previously saved scenarios for comparison
    - Maintain multiple "what-if" analyses

    #### 💡 Best Practices:

    1. **Start with Basic Info**: Enter parent ages, incomes, and current year first
    2. **Build Gradually**: Add one category at a time (expenses, children, houses)
    3. **Use Templates**: Leverage state-specific templates as starting points
    4. **Save Frequently**: Create named scenarios to preserve different assumptions
    5. **Review Timeline**: Use the timeline tab to spot potential issues
    6. **Run Analysis**: Generate Monte Carlo simulations to test robustness
    7. **Compare Scenarios**: Save multiple versions to compare strategies

    #### 🎯 Key Features:

    - **Dynamic Categories**: Add/remove expense categories as needed
    - **Ownership Tracking**: Separate parent vs. family assets
    - **Template System**: Pre-built expense templates by location and lifestyle
    - **Historical Simulation**: Use 100 years of market data for projections
    - **Inflation Adjustment**: View results in today's dollars or future values
    - **Comprehensive Modeling**: Includes taxes, Social Security, and detailed expenses
    - **Multiple Scenarios**: Save and compare different planning assumptions

    #### 🔧 Advanced Features:

    - **Asymmetric Variability**: Set different positive/negative variance ranges
    - **Social Security Insolvency**: Model potential benefit reductions
    - **House Timeline Management**: Complex property ownership and rental scenarios
    - **Detailed Breakdown**: See exactly how simulations calculate net worth
    - **Custom Economic Scenarios**: Create your own market assumptions
    """)


def parent_x_tab():
    """Parent X tab implementation"""
    st.header(f"{st.session_state.parent1_emoji} {st.session_state.parent1_name} Financial Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic Information")

        st.session_state.parentX_age = st.number_input(
            f"Current Age (in {st.session_state.current_year})",
            min_value=18,
            max_value=80,
            value=int(st.session_state.parentX_age),
            step=1,
            key="pX_age",
            help=f"Current age of {st.session_state.parent1_name} in {st.session_state.current_year}"
        )

        st.session_state.parentX_net_worth = st.number_input(
            "Starting Net Worth ($)",
            min_value=0.0,
            value=float(st.session_state.parentX_net_worth),
            step=1000.0,
            format="%.0f",
            key="pX_net_worth",
            help="Current total net worth (assets minus debts)"
        )

        st.session_state.parentX_income = st.number_input(
            "Current Yearly Income ($)",
            min_value=0.0,
            value=float(st.session_state.parentX_income),
            step=1000.0,
            format="%.0f",
            key="pX_income",
            help="Current annual gross income"
        )

        st.session_state.parentX_raise = st.number_input(
            "Annual Raise (%)",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.parentX_raise),
            step=0.1,
            format="%.1f",
            key="pX_raise",
            help="Expected annual salary increase percentage"
        )

    with col2:
        st.subheader("Retirement & Social Security")

        st.session_state.parentX_retirement_age = st.number_input(
            "Planned Retirement Age",
            min_value=50,
            max_value=80,
            value=int(st.session_state.parentX_retirement_age),
            step=1,
            key="pX_retirement_age",
            help=f"Age when {st.session_state.parent1_name} plans to retire"
        )

        st.session_state.parentX_ss_benefit = st.number_input(
            "Estimated Monthly Social Security ($)",
            min_value=0.0,
            value=float(st.session_state.parentX_ss_benefit),
            step=50.0,
            format="%.0f",
            key="pX_ss_benefit",
            help="Estimated monthly Social Security benefit at full retirement age"
        )

        # Calculate years to retirement
        years_to_retirement = max(0, st.session_state.parentX_retirement_age - st.session_state.parentX_age)
        annual_ss_benefit = st.session_state.parentX_ss_benefit * 12

        st.metric("Years to Retirement", years_to_retirement)
        st.metric("Annual Social Security", format_currency(annual_ss_benefit))

    # Marriage info display
    if st.session_state.marriage_year != "N/A":
        st.info(f"💍 **Marriage Year**: {st.session_state.marriage_year} - Assets became family assets this year")

    # Job Changes Schedule
    st.subheader("📈 Job Changes Schedule")
    st.session_state.parentX_job_changes = st.data_editor(
        st.session_state.parentX_job_changes,
        column_config={
            "Year": st.column_config.NumberColumn(
                "Year",
                help="Year when job change occurs",
                min_value=2025,
                max_value=2100,
                step=1,
                format="%d"
            ),
            "New Income": st.column_config.NumberColumn(
                "New Income ($)",
                help="New annual income after job change",
                min_value=0,
                step=1000,
                format="$%.0f"
            )
        },
        num_rows="dynamic",
        key="pX_job_changes"
    )


def parent_y_tab():
    """Parent Y tab implementation"""
    st.header(f"{st.session_state.parent2_emoji} {st.session_state.parent2_name} Financial Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic Information")

        st.session_state.parentY_age = st.number_input(
            f"Current Age (in {st.session_state.current_year})",
            min_value=18,
            max_value=80,
            value=int(st.session_state.parentY_age),
            step=1,
            key="pY_age",
            help=f"Current age of {st.session_state.parent2_name} in {st.session_state.current_year}"
        )

        st.session_state.parentY_net_worth = st.number_input(
            "Starting Net Worth ($)",
            min_value=0.0,
            value=float(st.session_state.parentY_net_worth),
            step=1000.0,
            format="%.0f",
            key="pY_net_worth",
            help="Current total net worth (assets minus debts)"
        )

        st.session_state.parentY_income = st.number_input(
            "Current Yearly Income ($)",
            min_value=0.0,
            value=float(st.session_state.parentY_income),
            step=1000.0,
            format="%.0f",
            key="pY_income",
            help="Current annual gross income"
        )

        st.session_state.parentY_raise = st.number_input(
            "Annual Raise (%)",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.parentY_raise),
            step=0.1,
            format="%.1f",
            key="pY_raise",
            help="Expected annual salary increase percentage"
        )

    with col2:
        st.subheader("Retirement & Social Security")

        st.session_state.parentY_retirement_age = st.number_input(
            "Planned Retirement Age",
            min_value=50,
            max_value=80,
            value=int(st.session_state.parentY_retirement_age),
            step=1,
            key="pY_retirement_age",
            help=f"Age when {st.session_state.parent2_name} plans to retire"
        )

        st.session_state.parentY_ss_benefit = st.number_input(
            "Estimated Monthly Social Security ($)",
            min_value=0.0,
            value=float(st.session_state.parentY_ss_benefit),
            step=50.0,
            format="%.0f",
            key="pY_ss_benefit",
            help="Estimated monthly Social Security benefit at full retirement age"
        )

        # Calculate years to retirement
        years_to_retirement = max(0, st.session_state.parentY_retirement_age - st.session_state.parentY_age)
        annual_ss_benefit = st.session_state.parentY_ss_benefit * 12

        st.metric("Years to Retirement", years_to_retirement)
        st.metric("Annual Social Security", format_currency(annual_ss_benefit))

    # Marriage info display
    if st.session_state.marriage_year != "N/A":
        st.info(f"💍 **Marriage Year**: {st.session_state.marriage_year} - Assets became family assets this year")

    # Job Changes Schedule
    st.subheader("📈 Job Changes Schedule")
    st.session_state.parentY_job_changes = st.data_editor(
        st.session_state.parentY_job_changes,
        column_config={
            "Year": st.column_config.NumberColumn(
                "Year",
                help="Year when job change occurs",
                min_value=2025,
                max_value=2100,
                step=1,
                format="%d"
            ),
            "New Income": st.column_config.NumberColumn(
                "New Income ($)",
                help="New annual income after job change",
                min_value=0,
                step=1000,
                format="$%.0f"
            )
        },
        num_rows="dynamic",
        key="pY_job_changes"
    )


def load_family_expense_template(state, strategy):
    """Load a family expense template"""
    if state in FAMILY_EXPENSE_TEMPLATES and strategy in FAMILY_EXPENSE_TEMPLATES[state]:
        template = FAMILY_EXPENSE_TEMPLATES[state][strategy]

        # Update expenses with template values
        for category, amount in template.items():
            if category in st.session_state.expenses:
                st.session_state.expenses[category] = amount

        return True
    return False


def family_expenses_tab():
    """Enhanced Family expenses tab with templates"""
    st.header("💸 Family Expenses & Major Purchases")

    # NEW: Family Expense Templates Section
    st.subheader("📋 Family Expense Templates")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_state = st.selectbox(
            "Select State",
            ["Custom"] + list(FAMILY_EXPENSE_TEMPLATES.keys()),
            key="family_expense_state_select"
        )

    with col2:
        if selected_state != "Custom":
            selected_strategy = st.selectbox(
                "Spending Strategy",
                list(FAMILY_EXPENSE_TEMPLATES[selected_state].keys()),
                key="family_expense_strategy_select"
            )
        else:
            selected_strategy = None
            st.write("**Custom Template**")

    with col3:
        if selected_state != "Custom" and selected_strategy:
            if st.button("🔥 Load Template", key="load_family_expense_template"):
                if load_family_expense_template(selected_state, selected_strategy):
                    st.success(f"Loaded {selected_state} {selected_strategy} template!")
                    st.rerun()
                else:
                    st.error("Failed to load template")

    with col4:
        # Template description
        if selected_state != "Custom" and selected_strategy:
            template_desc = {
                "Conservative": "Lower-cost approach with essential expenses",
                "Average": "Moderate spending based on regional averages",
                "High-end": "Premium spending with higher quality options"
            }
            st.info(f"**{selected_strategy}**: {template_desc.get(selected_strategy, '')}")

    # Dynamic Expense Categories Management
    st.subheader("🏷️ Manage Expense Categories")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Add New Expense Category**")
        new_category = st.text_input("New Category Name", key="new_expense_category")
        if st.button("➕ Add Category", key="add_expense_category"):
            if new_category and new_category not in st.session_state.expense_categories:
                st.session_state.expense_categories.append(new_category)
                st.session_state.expenses[new_category] = 0.0
                st.success(f"Added category: {new_category}")
                st.rerun()
            elif new_category in st.session_state.expense_categories:
                st.error("Category already exists!")

    with col2:
        st.write("**Remove Expense Category**")
        if len(st.session_state.expense_categories) > 1:
            category_to_remove = st.selectbox(
                "Select category to remove",
                ["Select..."] + st.session_state.expense_categories,
                key="remove_expense_category"
            )
            if st.button("🗑️ Remove Category", key="remove_expense_category_btn"):
                if category_to_remove != "Select...":
                    st.session_state.expense_categories.remove(category_to_remove)
                    st.session_state.expenses.pop(category_to_remove, None)
                    st.success(f"Removed category: {category_to_remove}")
                    st.rerun()

    # Family Expenses Section
    st.subheader("💰 Annual Family Expense Categories")

    # Create dynamic columns based on number of categories
    num_categories = len(st.session_state.expense_categories)
    cols_per_row = 3
    rows_needed = (num_categories + cols_per_row - 1) // cols_per_row

    for row in range(rows_needed):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            category_idx = row * cols_per_row + col_idx
            if category_idx < num_categories:
                category = st.session_state.expense_categories[category_idx]
                with cols[col_idx]:
                    st.session_state.expenses[category] = st.number_input(
                        f"{category} ($)",
                        min_value=0.0,
                        value=float(st.session_state.expenses.get(category, 0.0)),
                        step=100.0,
                        format="%.0f",
                        key=f"exp_{category.replace(' ', '_').replace('&', 'and').lower()}"
                    )

    # Tax Settings Section
    st.subheader("💼 Tax Settings")

    tax_col1, tax_col2 = st.columns(2)

    with tax_col1:
        st.session_state.state_tax_rate = st.number_input(
            "State Income Tax Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=float(st.session_state.state_tax_rate * 100),
            step=0.1,
            format="%.1f",
            key="state_tax_rate_input",
            help="Enter your state's income tax rate"
        ) / 100

        st.session_state.pretax_401k = st.number_input(
            "Annual Pre-tax 401(k) Contributions ($)",
            min_value=0.0,
            value=float(st.session_state.pretax_401k),
            step=500.0,
            format="%.0f",
            key="pretax_401k_input",
            help="Combined pre-tax retirement contributions for both parents"
        )

    with tax_col2:
        # Calculate current taxes
        gross_income = st.session_state.parentX_income + st.session_state.parentY_income
        if gross_income > 0:
            tax_info = calculate_annual_taxes(
                gross_income,
                st.session_state.pretax_401k,
                st.session_state.state_tax_rate
            )

            st.metric("Estimated Annual Taxes", format_currency(tax_info['total_tax']))
            st.metric("Effective Tax Rate", f"{tax_info['effective_rate']:.1f}%")
            st.metric("After-Tax Income", format_currency(tax_info['after_tax_income']))

    # Family Expenses Summary with house payment and taxes
    total_expenses = sum(st.session_state.expenses.values())

    # Calculate total monthly house payment for all houses (current year)
    current_year = st.session_state.current_year
    total_monthly_house_payment = 0

    for house in st.session_state.houses:
        status, rental_income = house.get_status_for_year(current_year)
        if status in ["Own_Live", "Own_Rent"]:
            # Mortgage payment
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

            # Property tax (monthly)
            monthly_property_tax = (house.current_value * house.property_tax_rate) / 12

            # Insurance (monthly)
            monthly_insurance = house.home_insurance / 12

            # Total monthly payment for this house
            house_monthly_payment = monthly_payment + monthly_property_tax + monthly_insurance
            total_monthly_house_payment += house_monthly_payment

    annual_house_payment = total_monthly_house_payment * 12
    gross_income = st.session_state.parentX_income + st.session_state.parentY_income

    # Calculate taxes
    tax_info = calculate_annual_taxes(
        gross_income,
        st.session_state.pretax_401k,
        st.session_state.state_tax_rate
    )

    after_tax_income = tax_info['after_tax_income']
    net_income = after_tax_income - total_expenses - annual_house_payment

    st.subheader("📊 Family Financial Summary")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Gross Annual Income", format_currency(gross_income))
    with col2:
        st.metric("Annual Taxes", format_currency(tax_info['total_tax']))
    with col3:
        st.metric("After-Tax Income", format_currency(after_tax_income))
    with col4:
        st.metric("Family Expenses", format_currency(total_expenses))
    with col5:
        st.metric("Monthly House Payment", format_currency(total_monthly_house_payment))
        st.caption("(All houses - PITI)")
    with col6:
        st.metric("Final Net Income", format_currency(net_income))

    # Display parent breakdown
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{st.session_state.parent1_name} Income", format_currency(st.session_state.parentX_income))
        st.metric(f"{st.session_state.parent1_name} Net Worth", format_currency(st.session_state.parentX_net_worth))
    with col2:
        st.metric(f"{st.session_state.parent2_name} Income", format_currency(st.session_state.parentY_income))
        st.metric(f"{st.session_state.parent2_name} Net Worth", format_currency(st.session_state.parentY_net_worth))

    # Major Expenses Section (as subheading)
    st.header("💳 Major Expenses & Purchases")

    # Create sub-tabs for major expenses
    recurring_tab, one_time_tab = st.tabs(["Recurring Expenses", "One-Time Purchases"])

    with recurring_tab:
        st.subheader("🔄 Recurring Major Expenses")

        # Add new recurring expense
        with st.expander("➕ Add New Recurring Expense", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                expense_name = st.text_input("Expense Name", key="recurring_name")
                category = st.selectbox("Category", ["Vehicle", "Home", "Travel", "Technology", "Other"],
                                        key="recurring_category")
                amount = st.number_input("Amount ($)", min_value=0.0, value=25000.0, step=1000.0, format="%.0f",
                                         key="recurring_amount")
                frequency_years = st.number_input("Frequency (years)", min_value=1, max_value=50, value=10,
                                                  key="recurring_frequency")

            with col2:
                start_year = st.number_input("Start Year", min_value=2025, max_value=2080, value=2025,
                                             key="recurring_start_year")
                inflation_adjust = st.checkbox("Adjust for Inflation", value=True, key="recurring_inflation")
                parent = st.selectbox("For Which Parent",
                                      ["Both", st.session_state.parent1_name, st.session_state.parent2_name],
                                      key="recurring_parent")

            if st.button("Add Recurring Expense", key="add_recurring_expense"):
                if expense_name:
                    expense = RecurringExpense(
                        name=expense_name,
                        category=category,
                        amount=amount,
                        frequency_years=frequency_years,
                        start_year=start_year,
                        end_year=None,
                        inflation_adjust=inflation_adjust,
                        parent=parent,
                        financing_years=0,
                        interest_rate=0.0
                    )

                    st.session_state.recurring_expenses.append(expense)
                    st.success(f"Added recurring expense: {expense_name}")
                    st.rerun()

        # Display existing recurring expenses
        if st.session_state.recurring_expenses:
            st.subheader("📋 Current Recurring Expenses")

            # Create editable dataframe
            expense_data = []
            for i, expense in enumerate(st.session_state.recurring_expenses):
                expense_data.append({
                    "Index": i,
                    "Name": expense.name,
                    "Category": expense.category,
                    "Amount": expense.amount,
                    "Frequency": expense.frequency_years,
                    "Start Year": expense.start_year,
                    "Parent": expense.parent,
                    "Inflation Adj.": expense.inflation_adjust
                })

            expense_df = pd.DataFrame(expense_data)

            # Edit existing expenses
            edited_expense_df = st.data_editor(
                expense_df,
                column_config={
                    "Index": st.column_config.NumberColumn("Index", disabled=True, width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=["Vehicle", "Home", "Travel", "Technology", "Other"],
                        width="small"
                    ),
                    "Amount": st.column_config.NumberColumn(
                        "Amount ($)",
                        min_value=0,
                        step=1000,
                        format="$%.0f"
                    ),
                    "Frequency": st.column_config.NumberColumn(
                        "Frequency (years)",
                        min_value=1,
                        max_value=50,
                        step=1,
                        width="small"
                    ),
                    "Start Year": st.column_config.NumberColumn(
                        "Start Year",
                        min_value=2025,
                        max_value=2080,
                        step=1,
                        width="small"
                    ),
                    "Parent": st.column_config.SelectboxColumn(
                        "Parent",
                        options=["Both", st.session_state.parent1_name, st.session_state.parent2_name],
                        width="small"
                    ),
                    "Inflation Adj.": st.column_config.CheckboxColumn("Inflation Adj.", width="small")
                },
                use_container_width=True,
                num_rows="dynamic",
                key="edit_recurring_expenses"
            )

            # Update session state with edited values
            if len(edited_expense_df) != len(st.session_state.recurring_expenses):
                # Handle deletions
                remaining_indices = set(edited_expense_df['Index'].tolist())
                original_indices = set(range(len(st.session_state.recurring_expenses)))
                deleted_indices = original_indices - remaining_indices

                # Remove deleted expenses (in reverse order to maintain indices)
                for idx in sorted(deleted_indices, reverse=True):
                    if 0 <= idx < len(st.session_state.recurring_expenses):
                        st.session_state.recurring_expenses.pop(idx)

                st.success(f"Removed {len(deleted_indices)} recurring expense(s)")
                st.rerun()
            else:
                # Update existing expenses
                for _, row in edited_expense_df.iterrows():
                    idx = row['Index']
                    if 0 <= idx < len(st.session_state.recurring_expenses):
                        expense = st.session_state.recurring_expenses[idx]
                        expense.name = row['Name']
                        expense.category = row['Category']
                        expense.amount = row['Amount']
                        expense.frequency_years = row['Frequency']
                        expense.start_year = row['Start Year']
                        expense.parent = row['Parent']
                        expense.inflation_adjust = row['Inflation Adj.']

            # Delete all button
            if st.button("🗑️ Delete All Recurring Expenses", key="delete_all_recurring"):
                st.session_state.recurring_expenses = []
                st.success("Deleted all recurring expenses")
                st.rerun()

    with one_time_tab:
        st.subheader("🛏️ One-Time Major Purchases")

        # Add new one-time purchase
        with st.expander("➕ Add New Purchase", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                purchase_name = st.text_input("Purchase Name", key="purchase_name")
                purchase_year = st.number_input("Year", min_value=2025, max_value=2080, value=2025, key="purchase_year")
                purchase_amount = st.number_input("Amount ($)", min_value=0.0, value=10000.0, step=500.0, format="%.0f",
                                                  key="purchase_amount")

            with col2:
                purchase_financing_years = st.number_input("Financing Years (0 for cash)", min_value=0, max_value=30,
                                                           value=0, key="purchase_financing")
                if purchase_financing_years > 0:
                    purchase_interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=20.0,
                                                             value=5.0, step=0.1, key="purchase_interest") / 100
                else:
                    purchase_interest_rate = 0.0

            if st.button("Add Purchase", key="add_purchase"):
                if purchase_name:
                    purchase = MajorPurchase(
                        name=purchase_name,
                        year=purchase_year,
                        amount=purchase_amount,
                        financing_years=purchase_financing_years,
                        interest_rate=purchase_interest_rate
                    )

                    st.session_state.major_purchases.append(purchase)
                    st.success(f"Added purchase: {purchase_name}")
                    st.rerun()

        # Display existing purchases
        if st.session_state.major_purchases:
            st.subheader("📋 Planned One-Time Purchases")

            purchase_data = []
            for purchase in st.session_state.major_purchases:
                purchase_data.append({
                    "Name": purchase.name,
                    "Year": purchase.year,
                    "Amount": format_currency(purchase.amount),
                    "Financing": f"{purchase.financing_years} years" if purchase.financing_years > 0 else "Cash"
                })

            st.dataframe(pd.DataFrame(purchase_data), use_container_width=True)


def load_children_expense_template(state, strategy):
    """Load a children expense template"""
    if state in CHILDREN_EXPENSE_TEMPLATES and strategy in CHILDREN_EXPENSE_TEMPLATES[state]:
        template = CHILDREN_EXPENSE_TEMPLATES[state][strategy]

        # Convert template to DataFrame format
        df_data = {'Age': list(range(31))}
        for category, values in template.items():
            df_data[category] = values

        st.session_state.children_expenses = pd.DataFrame(df_data)
        return True
    return False


def export_children_expenses_csv():
    """Export children expenses to CSV"""
    csv_buffer = io.StringIO()
    st.session_state.children_expenses.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    return csv_data


def import_children_expenses_csv(uploaded_file):
    """Import children expenses from CSV"""
    try:
        df = pd.read_csv(uploaded_file)

        # Validate required columns
        required_columns = ['Age', 'Food', 'Clothing', 'Healthcare', 'Activities/Sports',
                            'Entertainment', 'Transportation', 'School Supplies',
                            'Gifts/Celebrations', 'Miscellaneous', 'Daycare', 'Education']

        if not all(col in df.columns for col in required_columns):
            st.error("CSV file must contain all required columns: " + ", ".join(required_columns))
            return False

        # Ensure Age column contains 0-30
        if not (df['Age'].min() == 0 and df['Age'].max() == 30 and len(df) == 31):
            st.error("CSV must contain exactly 31 rows with ages 0-30")
            return False

        # Update session state
        st.session_state.children_expenses = df
        return True

    except Exception as e:
        st.error(f"Error importing CSV: {str(e)}")
        return False


def children_tab():
    """Enhanced Children expenses table tab with duplicate name prevention"""
    st.header("👶 Children Expenses & Planning")

    # Children instances management
    st.subheader("👨‍👩‍👧‍👦 Your Children")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Add a Child**")
        child_name = st.text_input("Child Name", key="new_child_name")
        child_birth_year = st.number_input(
            "Birth Year",
            min_value=1990,
            max_value=2040,
            value=2020,
            step=1,
            key="new_child_birth_year",
            help="Year the child was/will be born"
        )

        if st.button("Add Child", key="add_new_child"):
            if child_name:
                # Check for duplicate names
                existing_names = [child['name'].lower() for child in st.session_state.children_list]
                if child_name.lower() in existing_names:
                    st.error(f"A child named '{child_name}' already exists. Please use a different name.")
                else:
                    new_child = {
                        'name': child_name,
                        'birth_year': child_birth_year
                    }
                    st.session_state.children_list.append(new_child)
                    st.success(f"Added {child_name} (born {child_birth_year})")
                    st.rerun()
            else:
                st.error("Please enter a child name")

    with col2:
        if st.session_state.children_list:
            st.write("**Current Children**")
            current_year = st.session_state.current_year

            for i, child in enumerate(st.session_state.children_list):
                current_age = current_year - child['birth_year']
                age_text = f"Age {current_age}" if current_age >= 0 else f"Born in {abs(current_age)} years"
                st.write(f"• {child['name']} ({child['birth_year']}) - {age_text}")

            # Remove child option
            if len(st.session_state.children_list) > 0:
                child_to_remove = st.selectbox(
                    "Remove child:",
                    ["Select..."] + [f"{c['name']} ({c['birth_year']})" for c in st.session_state.children_list],
                    key="remove_child_select"
                )

                if st.button("Remove Selected Child", key="remove_child_btn") and child_to_remove != "Select...":
                    child_name = child_to_remove.split(" (")[0]
                    st.session_state.children_list = [c for c in st.session_state.children_list if
                                                      c['name'] != child_name]
                    st.success(f"Removed {child_name}")
                    st.rerun()
        else:
            st.info("No children added yet. Add a child above to start planning.")

    # Template selection section
    st.subheader("📋 Expense Templates")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_state = st.selectbox(
            "Select State",
            ["Custom"] + list(CHILDREN_EXPENSE_TEMPLATES.keys()),
            key="children_state_select"
        )

    with col2:
        if selected_state != "Custom":
            selected_strategy = st.selectbox(
                "Spending Strategy",
                list(CHILDREN_EXPENSE_TEMPLATES[selected_state].keys()),
                key="children_strategy_select"
            )
        else:
            selected_strategy = None
            st.write("**Custom Template**")

    with col3:
        if selected_state != "Custom" and selected_strategy:
            if st.button("🔥 Load Template", key="load_children_template"):
                if load_children_expense_template(selected_state, selected_strategy):
                    st.success(f"Loaded {selected_state} {selected_strategy} template!")
                    st.rerun()
                else:
                    st.error("Failed to load template")

    with col4:
        # Template description
        if selected_state != "Custom" and selected_strategy:
            template_desc = {
                "Conservative": "Lower-cost approach with essential expenses",
                "Average": "Moderate spending based on regional averages",
                "High-end": "Premium spending with higher quality options"
            }
            st.info(f"**{selected_strategy}**: {template_desc.get(selected_strategy, '')}")

    # Expense table management with CSV import/export
    st.subheader("💰 Children Expense Template")

    # CSV Import/Export section
    col1, col2, col3 = st.columns(3)

    with col1:
        # Today dollars toggle
        st.session_state.children_today_dollars = st.toggle(
            "Today's Dollars View",
            value=st.session_state.children_today_dollars,
            help="Toggle between today's purchasing power and inflation-adjusted future values"
        )

    with col2:
        # Export CSV
        csv_data = export_children_expenses_csv()
        st.download_button(
            label="📤 Export to CSV",
            data=csv_data,
            file_name=f"children_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Download current children expenses as CSV file"
        )

    with col3:
        # Import CSV
        uploaded_file = st.file_uploader(
            "📥 Import CSV",
            type=['csv'],
            help="Upload a CSV file to replace current children expenses"
        )

        if uploaded_file is not None:
            if st.button("Import CSV Data", key="import_csv_btn"):
                if import_children_expenses_csv(uploaded_file):
                    st.success("✅ CSV data imported successfully!")
                    st.rerun()

    # Display info about current view
    if st.session_state.children_today_dollars:
        st.info(
            "💡 **Today's Dollars**: Enter expenses in current purchasing power. The app will apply inflation automatically in calculations.")
    else:
        st.info(
            "📈 **Future Dollars**: Values shown include inflation adjustments. Enter what you expect to actually pay in future years.")

    # Get active inflation rate for calculations
    active_scenario = st.session_state.economic_scenarios[st.session_state.active_scenario]
    inflation_rate = active_scenario.inflation_rate

    # Prepare display dataframe
    display_df = st.session_state.children_expenses.copy()

    if not st.session_state.children_today_dollars:
        # Apply inflation to display values
        base_year = st.session_state.current_year
        for index, row in display_df.iterrows():
            age = row['Age']
            # Assume expenses are for when child reaches that age
            future_year = base_year + age
            inflation_multiplier = (1 + inflation_rate) ** age

            for col in display_df.columns:
                if col != 'Age':
                    display_df.at[index, col] = row[col] * inflation_multiplier

    st.write("**Annual expenses for children by age (0-30 years)**")
    st.write("Edit the values below to customize expenses for each age and category.")

    # Display and edit the children expenses table
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Age": st.column_config.NumberColumn(
                "Age",
                help="Child's age",
                disabled=True,
                width="small"
            ),
            "Food": st.column_config.NumberColumn(
                "Food ($)",
                help="Annual food expenses",
                min_value=0,
                step=100,
                format="$%.0f"
            ),
            "Clothing": st.column_config.NumberColumn(
                "Clothing ($)",
                help="Annual clothing expenses",
                min_value=0,
                step=50,
                format="$%.0f"
            ),
            "Healthcare": st.column_config.NumberColumn(
                "Healthcare ($)",
                help="Annual healthcare expenses",
                min_value=0,
                step=50,
                format="$%.0f"
            ),
            "Activities/Sports": st.column_config.NumberColumn(
                "Activities/Sports ($)",
                help="Annual activities and sports expenses",
                min_value=0,
                step=100,
                format="$%.0f"
            ),
            "Entertainment": st.column_config.NumberColumn(
                "Entertainment ($)",
                help="Annual entertainment expenses",
                min_value=0,
                step=50,
                format="$%.0f"
            ),
            "Transportation": st.column_config.NumberColumn(
                "Transportation ($)",
                help="Annual transportation expenses",
                min_value=0,
                step=100,
                format="$%.0f"
            ),
            "School Supplies": st.column_config.NumberColumn(
                "School Supplies ($)",
                help="Annual school supplies expenses",
                min_value=0,
                step=25,
                format="$%.0f"
            ),
            "Gifts/Celebrations": st.column_config.NumberColumn(
                "Gifts/Celebrations ($)",
                help="Annual gifts and celebrations expenses",
                min_value=0,
                step=25,
                format="$%.0f"
            ),
            "Miscellaneous": st.column_config.NumberColumn(
                "Miscellaneous ($)",
                help="Annual miscellaneous expenses",
                min_value=0,
                step=25,
                format="$%.0f"
            ),
            "Daycare": st.column_config.NumberColumn(
                "Daycare ($)",
                help="Annual daycare expenses",
                min_value=0,
                step=1000,
                format="$%.0f"
            ),
            "Education": st.column_config.NumberColumn(
                "Education ($)",
                help="Annual education expenses (college, etc.)",
                min_value=0,
                step=1000,
                format="$%.0f"
            )
        },
        use_container_width=True,
        height=600,
        key="children_expenses_editor"
    )

    # Convert back to today's dollars if needed and update session state
    if not st.session_state.children_today_dollars:
        # Convert back to today's dollars for storage
        base_year = st.session_state.current_year
        for index, row in edited_df.iterrows():
            age = row['Age']
            inflation_multiplier = (1 + inflation_rate) ** age

            for col in edited_df.columns:
                if col != 'Age':
                    st.session_state.children_expenses.at[index, col] = row[col] / inflation_multiplier
    else:
        st.session_state.children_expenses = edited_df

    # Calculate and display summary statistics
    st.subheader("📊 Children Expenses Summary")

    if st.session_state.children_list:
        # Calculate current year expenses for all children
        current_year = st.session_state.current_year
        total_current_expenses = 0

        for child in st.session_state.children_list:
            child_age = current_year - child['birth_year']
            if 0 <= child_age < len(st.session_state.children_expenses):
                row = st.session_state.children_expenses.iloc[child_age]
                child_annual_cost = sum(row[col] for col in row.index if col != 'Age')
                total_current_expenses += child_annual_cost

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Year Children Expenses", format_currency(total_current_expenses, show_thousands=True))
        with col2:
            st.metric("Number of Children", len(st.session_state.children_list))
        with col3:
            if len(st.session_state.children_list) > 0:
                avg_per_child = total_current_expenses / len(st.session_state.children_list)
                st.metric("Average per Child (Current Year)", format_currency(avg_per_child))

    # Calculate totals for different age ranges
    age_ranges = [
        ("Infants (0-2)", range(0, 3)),
        ("Toddlers (3-5)", range(3, 6)),
        ("Children (6-12)", range(6, 13)),
        ("Teenagers (13-17)", range(13, 18)),
        ("College Age (18-21)", range(18, 22)),
        ("Young Adults (22-30)", range(22, 31))
    ]

    summary_data = []
    for range_name, age_range in age_ranges:
        total_cost = 0
        for age in age_range:
            if age < len(st.session_state.children_expenses):
                row = st.session_state.children_expenses.iloc[age]
                total_cost += sum(row[col] for col in row.index if col != 'Age')

        avg_annual = total_cost / len(age_range) if len(age_range) > 0 else 0
        summary_data.append({
            "Age Range": range_name,
            "Total Cost": format_currency(total_cost),
            "Avg Annual": format_currency(avg_annual)
        })

    st.write("**Cost by Age Range (per child, in today's dollars):**")
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    # Total lifetime cost
    total_lifetime_cost = 0
    for _, row in st.session_state.children_expenses.iterrows():
        total_lifetime_cost += sum(row[col] for col in row.index if col != 'Age')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lifetime Cost per Child (Today's $)", format_currency(total_lifetime_cost, show_thousands=True))
    with col2:
        st.metric("Average Annual Cost per Child", format_currency(total_lifetime_cost / 31))
    with col3:
        peak_year_cost = 0
        peak_age = 0
        for _, row in st.session_state.children_expenses.iterrows():
            year_cost = sum(row[col] for col in row.index if col != 'Age')
            if year_cost > peak_year_cost:
                peak_year_cost = year_cost
                peak_age = row['Age']
        st.metric(f"Peak Year Cost (Age {peak_age})", format_currency(peak_year_cost))


def calculate_monthly_house_payment(house):
    """Calculate total monthly payment for a house (PITI)"""
    # Mortgage payment
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

    # Property tax (monthly)
    monthly_property_tax = (house.current_value * house.property_tax_rate) / 12

    # Insurance (monthly)
    monthly_insurance = house.home_insurance / 12

    # Total monthly payment
    return monthly_payment + monthly_property_tax + monthly_insurance


def house_tab():
    """Enhanced House and Real Estate tab with ownership tracking"""
    st.header("🏠 House Portfolio & Real Estate Planning")

    # Current Houses Section
    st.subheader("🏡 Your House Portfolio")

    if st.session_state.houses:
        # Display summary of all houses
        current_year = st.session_state.current_year
        total_equity = 0
        total_monthly_payment = 0
        total_rental_income = 0

        # Calculate net worth by owner
        parent1_real_estate = 0
        parent2_real_estate = 0
        family_real_estate = 0

        for house in st.session_state.houses:
            equity = house.current_value - house.mortgage_balance
            total_equity += equity

            # Assign equity by owner
            if house.owner == "Parent1":
                parent1_real_estate += equity
            elif house.owner == "Parent2":
                parent2_real_estate += equity
            else:  # Shared
                family_real_estate += equity

            status, rental_income = house.get_status_for_year(current_year)

            if status in ["Own_Live", "Own_Rent"]:
                monthly_payment = calculate_monthly_house_payment(house)
                total_monthly_payment += monthly_payment

            if status == "Own_Rent":
                total_rental_income += rental_income

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Houses", len(st.session_state.houses))
        with col2:
            st.metric("Total Equity", format_currency(total_equity, show_thousands=True))
        with col3:
            st.metric("Total Monthly Payments", format_currency(total_monthly_payment))
        with col4:
            st.metric("Monthly Rental Income", format_currency(total_rental_income))

        # Show equity breakdown by owner
        if parent1_real_estate > 0 or parent2_real_estate > 0 or family_real_estate > 0:
            st.write("**Real Estate Equity by Owner:**")
            equity_col1, equity_col2, equity_col3 = st.columns(3)
            with equity_col1:
                st.metric(f"{st.session_state.parent1_name} Real Estate",
                          format_currency(parent1_real_estate, show_thousands=True))
            with equity_col2:
                st.metric(f"{st.session_state.parent2_name} Real Estate",
                          format_currency(parent2_real_estate, show_thousands=True))
            with equity_col3:
                st.metric("Family Real Estate", format_currency(family_real_estate, show_thousands=True))

        # Display each house
        for i, house in enumerate(st.session_state.houses):
            current_status, current_rental = house.get_status_for_year(current_year)
            status_text = {
                "Own_Live": "Own & Live In",
                "Own_Rent": "Own & Rent Out",
                "Sell": "Sold"
            }.get(current_status, current_status)

            owner_text = {
                "Parent1": st.session_state.parent1_name,
                "Parent2": st.session_state.parent2_name,
                "Shared": "Family/Shared"
            }.get(house.owner, house.owner)

            with st.expander(f"🏠 {house.name} ({status_text}) - {owner_text}", expanded=i == 0):
                house_col1, house_col2 = st.columns(2)

                with house_col1:
                    st.write("**Basic Information**")
                    house.name = st.text_input("House Name", value=house.name, key=f"house_name_{i}")
                    house.purchase_year = st.number_input("Purchase Year", value=int(house.purchase_year),
                                                          key=f"house_year_{i}")
                    house.purchase_price = st.number_input("Purchase Price ($)", value=float(house.purchase_price),
                                                           format="%.0f",
                                                           key=f"house_purchase_{i}")
                    house.current_value = st.number_input("Current Value ($)", value=float(house.current_value),
                                                          format="%.0f",
                                                          key=f"house_value_{i}")

                    # Owner selection
                    owner_options = ["Shared", "Parent1", "Parent2"]
                    owner_labels = ["Family/Shared", st.session_state.parent1_name, st.session_state.parent2_name]
                    current_owner_idx = owner_options.index(house.owner) if house.owner in owner_options else 0

                    selected_owner = st.selectbox(
                        "House Owner",
                        options=owner_options,
                        format_func=lambda x: owner_labels[owner_options.index(x)],
                        index=current_owner_idx,
                        key=f"house_owner_{i}",
                        help="Who owns this property for net worth tracking"
                    )
                    house.owner = selected_owner

                    st.write("**Mortgage Information**")
                    house.mortgage_balance = st.number_input("Mortgage Balance ($)",
                                                             value=float(house.mortgage_balance), format="%.0f",
                                                             key=f"house_balance_{i}")
                    house.mortgage_rate = st.number_input("Mortgage Rate (%)", value=float(house.mortgage_rate * 100),
                                                          key=f"house_rate_{i}") / 100
                    house.mortgage_years_left = st.number_input("Years Left", value=int(house.mortgage_years_left),
                                                                key=f"house_years_{i}")

                with house_col2:
                    st.write("**Property Expenses**")
                    house.property_tax_rate = st.number_input("Property Tax Rate (%)",
                                                              value=float(house.property_tax_rate * 100),
                                                              key=f"house_tax_{i}") / 100
                    house.home_insurance = st.number_input("Annual Insurance ($)", value=float(house.home_insurance),
                                                           format="%.0f",
                                                           key=f"house_insurance_{i}")
                    house.upkeep_costs = st.number_input("Annual Upkeep/Repairs ($)", value=float(house.upkeep_costs),
                                                         format="%.0f",
                                                         key=f"house_upkeep_{i}")

                # Timeline Management
                st.write("**🗓️ House Timeline**")
                st.write("Define when you own/live in/rent out this property:")

                # Display current timeline
                timeline_data = []
                for j, entry in enumerate(house.timeline):
                    status_display = {
                        "Own_Live": "Own & Live In",
                        "Own_Rent": "Own & Rent Out",
                        "Sell": "Sell"
                    }.get(entry.status, entry.status)

                    timeline_data.append({
                        "Index": j,
                        "Year": entry.year,
                        "Status": entry.status,
                        "Monthly Rent": entry.rental_income if entry.status == "Own_Rent" else 0
                    })

                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)

                    edited_timeline = st.data_editor(
                        timeline_df,
                        column_config={
                            "Index": st.column_config.NumberColumn("Index", disabled=True, width="small"),
                            "Year": st.column_config.NumberColumn("Year", min_value=2020, max_value=2080),
                            "Status": st.column_config.SelectboxColumn(
                                "Status",
                                options=["Own_Live", "Own_Rent", "Sell"]
                            ),
                            "Monthly Rent": st.column_config.NumberColumn(
                                "Monthly Rent ($)",
                                min_value=0,
                                step=100,
                                format="$%.0f"
                            )
                        },
                        num_rows="dynamic",
                        key=f"house_timeline_{i}"
                    )

                    # Update timeline
                    new_timeline = []
                    for _, row in edited_timeline.iterrows():
                        new_timeline.append(HouseTimelineEntry(
                            year=int(row['Year']),
                            status=row['Status'],
                            rental_income=float(row['Monthly Rent']) if row['Status'] == "Own_Rent" else 0.0
                        ))

                    house.timeline = sorted(new_timeline, key=lambda x: x.year)
                else:
                    # Add first timeline entry
                    if st.button(f"Add Timeline Entry for {house.name}", key=f"add_timeline_{i}"):
                        house.timeline = [HouseTimelineEntry(house.purchase_year, "Own_Live", 0.0)]
                        st.rerun()

                # Quick add timeline entry
                with st.expander("➕ Add Timeline Entry", expanded=False):
                    timeline_col1, timeline_col2 = st.columns(2)

                    with timeline_col1:
                        new_year = st.number_input("Year", min_value=2020, max_value=2080, value=current_year + 1,
                                                   key=f"new_timeline_year_{i}")
                        new_status = st.selectbox("Status", ["Own_Live", "Own_Rent", "Sell"],
                                                  key=f"new_timeline_status_{i}")

                    with timeline_col2:
                        new_rental = 0.0
                        if new_status == "Own_Rent":
                            new_rental = st.number_input("Monthly Rental Income ($)", min_value=0.0, value=2000.0,
                                                         format="%.0f",
                                                         key=f"new_timeline_rent_{i}")

                    if st.button(f"Add Entry", key=f"add_timeline_entry_{i}"):
                        house.timeline.append(HouseTimelineEntry(new_year, new_status, new_rental))
                        house.timeline = sorted(house.timeline, key=lambda x: x.year)
                        st.success(f"Added timeline entry for {new_year}")
                        st.rerun()

                # Calculate and display house metrics
                equity = house.current_value - house.mortgage_balance
                monthly_payment = calculate_monthly_house_payment(house)
                annual_property_tax = house.current_value * house.property_tax_rate

                st.write("**House Financial Summary**")
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric("Current Equity", format_currency(equity, show_thousands=True))
                with metric_col2:
                    st.metric("Monthly Payment (PITI)", format_currency(monthly_payment))
                with metric_col3:
                    st.metric("Annual Property Tax", format_currency(annual_property_tax))
                with metric_col4:
                    st.metric("Annual Upkeep", format_currency(house.upkeep_costs))

                # Show current and future status
                st.write("**Status Overview:**")
                for year in range(current_year, min(current_year + 10, 2035)):
                    status, rental = house.get_status_for_year(year)
                    status_display = {
                        "Own_Live": "Own & Live In",
                        "Own_Rent": f"Rent Out ({format_currency(rental)}/mo)",
                        "Sell": "Sell"
                    }.get(status, status)
                    st.write(f"• {year}: {status_display}")

                # Delete house button
                if len(st.session_state.houses) > 1:
                    if st.button(f"🗑️ Delete {house.name}", key=f"delete_house_{i}"):
                        st.session_state.houses.pop(i)
                        st.success(f"Deleted {house.name}")
                        st.rerun()

    # Add new house section
    st.subheader("➕ Add New House")

    with st.expander("Add New Property", expanded=False):
        new_col1, new_col2 = st.columns(2)

        with new_col1:
            new_name = st.text_input("House Name", value="New Property", key="new_house_name")
            new_purchase_year = st.number_input("Purchase Year", value=2025, step=1, key="new_house_year")
            new_purchase_price = st.number_input("Purchase Price ($)", value=400000.0, format="%.0f",
                                                 key="new_house_purchase")
            new_current_value = st.number_input("Current Value ($)", value=400000.0, format="%.0f",
                                                key="new_house_value")
            new_mortgage_balance = st.number_input("Mortgage Balance ($)", value=320000.0, format="%.0f",
                                                   key="new_house_balance")
            new_mortgage_rate = st.number_input("Mortgage Rate (%)", value=6.5, step=0.1, key="new_house_rate") / 100

        with new_col2:
            new_mortgage_years = st.number_input("Mortgage Years Left", value=30, step=1, key="new_house_years")
            new_property_tax = st.number_input("Property Tax Rate (%)", value=1.0, step=0.1, key="new_house_tax") / 100
            new_insurance = st.number_input("Annual Insurance ($)", value=1200.0, format="%.0f",
                                            key="new_house_insurance")
            new_upkeep = st.number_input("Annual Upkeep/Repairs ($)", value=2000.0, format="%.0f",
                                         key="new_house_upkeep")
            initial_status = st.selectbox("Initial Status", ["Own_Live", "Own_Rent", "Sell"], key="new_house_status")

            # Owner selection for new house
            new_owner_options = ["Shared", "Parent1", "Parent2"]
            new_owner_labels = ["Family/Shared", st.session_state.parent1_name, st.session_state.parent2_name]
            new_owner = st.selectbox(
                "House Owner",
                options=new_owner_options,
                format_func=lambda x: new_owner_labels[new_owner_options.index(x)],
                key="new_house_owner"
            )

            initial_rental = 0.0
            if initial_status == "Own_Rent":
                initial_rental = st.number_input("Monthly Rental Income ($)", value=2000.0, format="%.0f",
                                                 key="new_house_rent")

        if st.button("Add New House", type="primary", key="add_new_house"):
            new_house = House(
                name=new_name,
                purchase_year=new_purchase_year,
                purchase_price=new_purchase_price,
                current_value=new_current_value,
                mortgage_balance=new_mortgage_balance,
                mortgage_rate=new_mortgage_rate,
                mortgage_years_left=new_mortgage_years,
                property_tax_rate=new_property_tax,
                home_insurance=new_insurance,
                maintenance_rate=0.015,
                upkeep_costs=new_upkeep,
                owner=new_owner,
                timeline=[HouseTimelineEntry(new_purchase_year, initial_status, initial_rental)]
            )

            st.session_state.houses.append(new_house)
            st.success(f"Added new house: {new_name}")
            st.rerun()


def economy_tab():
    """Economic Assumptions and Scenarios tab with active scenario selection"""
    st.header("📈 Economic Assumptions & Scenarios")

    # Active scenario selection
    st.subheader("🎯 Active Economic Scenario")

    col1, col2 = st.columns([1, 2])

    with col1:
        new_active_scenario = st.selectbox(
            "Select Active Scenario",
            list(st.session_state.economic_scenarios.keys()),
            index=list(st.session_state.economic_scenarios.keys()).index(st.session_state.active_scenario),
            key="active_scenario_selector",
            help="This scenario will be used for all calculations throughout the app"
        )

        if new_active_scenario != st.session_state.active_scenario:
            st.session_state.active_scenario = new_active_scenario
            st.success(f"✅ Active scenario changed to: {new_active_scenario}")
            st.rerun()

    with col2:
        # Display active scenario details
        active = st.session_state.economic_scenarios[st.session_state.active_scenario]
        st.info(f"**{st.session_state.active_scenario} Scenario (ACTIVE)**\n"
                f"• Investment Return: {active.investment_return * 100:.1f}%\n"
                f"• Inflation Rate: {active.inflation_rate * 100:.1f}%\n"
                f"• Expense Growth: {active.expense_growth_rate * 100:.1f}%\n"
                f"• Healthcare Inflation: {active.healthcare_inflation_rate * 100:.1f}%")

    # Economic Scenarios Section
    st.subheader("📊 All Economic Scenarios")

    # Display current scenarios
    scenario_data = []
    for name, scenario in st.session_state.economic_scenarios.items():
        is_active = "✅ ACTIVE" if name == st.session_state.active_scenario else ""
        scenario_data.append({
            "Scenario": f"{name} {is_active}",
            "Investment Return": f"{scenario.investment_return * 100:.1f}%",
            "Inflation Rate": f"{scenario.inflation_rate * 100:.1f}%",
            "Expense Growth": f"{scenario.expense_growth_rate * 100:.1f}%",
            "Healthcare Inflation": f"{scenario.healthcare_inflation_rate * 100:.1f}%"
        })

    st.dataframe(pd.DataFrame(scenario_data), use_container_width=True)

    # Edit scenarios
    st.subheader("✏️ Edit Economic Scenarios")

    selected_scenario = st.selectbox(
        "Select Scenario to Edit",
        list(st.session_state.economic_scenarios.keys()),
        key="selected_scenario"
    )

    if selected_scenario:
        scenario = st.session_state.economic_scenarios[selected_scenario]

        col1, col2 = st.columns(2)

        with col1:
            new_investment_return = st.number_input(
                "Investment Return Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=float(scenario.investment_return * 100),
                step=0.1,
                format="%.1f",
                key=f"investment_return_{selected_scenario}"
            ) / 100

            new_inflation_rate = st.number_input(
                "General Inflation Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=float(scenario.inflation_rate * 100),
                step=0.1,
                format="%.1f",
                key=f"inflation_rate_{selected_scenario}",
                help="This rate affects all inflation calculations in the app when this scenario is active"
            ) / 100

        with col2:
            new_expense_growth = st.number_input(
                "Expense Growth Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=float(scenario.expense_growth_rate * 100),
                step=0.1,
                format="%.1f",
                key=f"expense_growth_{selected_scenario}"
            ) / 100

            new_healthcare_inflation = st.number_input(
                "Healthcare Inflation Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=float(scenario.healthcare_inflation_rate * 100),
                step=0.1,
                format="%.1f",
                key=f"healthcare_inflation_{selected_scenario}"
            ) / 100

        if st.button(f"Update {selected_scenario} Scenario", key=f"update_{selected_scenario}"):
            st.session_state.economic_scenarios[selected_scenario] = EconomicScenario(
                name=selected_scenario,
                investment_return=new_investment_return,
                inflation_rate=new_inflation_rate,
                expense_growth_rate=new_expense_growth,
                healthcare_inflation_rate=new_healthcare_inflation
            )
            st.success(f"Updated {selected_scenario} scenario!")
            st.rerun()

    # Usage note
    st.info("💡 **Note**: The active scenario's inflation rate is used throughout the app for:\n"
            "• Children expenses inflation adjustments\n"
            "• Recurring expenses inflation\n"
            "• House value appreciation\n"
            "• Monte Carlo simulations\n"
            "• All future value calculations")

    # Historical Stock Market Performance Section
    st.subheader("📊 Historical Stock Market Performance")

    # Show historical statistics
    if st.session_state.mc_show_historical_stats or st.button("📈 Show Historical Statistics", key="show_hist_stats"):
        st.session_state.mc_show_historical_stats = True

        stats = get_historical_return_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Annual Return", f"{stats['mean'] * 100:.1f}%")
            st.metric("Median Annual Return", f"{stats['median'] * 100:.1f}%")
        with col2:
            st.metric("Standard Deviation", f"{stats['std'] * 100:.1f}%")
            st.metric("Years of Data", stats['total_years'])
        with col3:
            st.metric("Best Year", f"{stats['max'] * 100:.1f}%")
            st.metric("Worst Year", f"{stats['min'] * 100:.1f}%")
        with col4:
            st.metric("Positive Years", f"{stats['positive_years']}")
            st.metric("Positive %", f"{stats['positive_percentage']:.1f}%")

        # Historical returns chart
        historical_df = pd.DataFrame({
            'Year': range(st.session_state.mc_historical_start_year,
                          st.session_state.mc_historical_start_year + len(HISTORICAL_STOCK_RETURNS)),
            'Return': [r * 100 for r in HISTORICAL_STOCK_RETURNS]
        })

        fig_hist = go.Figure()

        # Color positive and negative returns differently
        positive_mask = historical_df['Return'] >= 0

        fig_hist.add_trace(go.Bar(
            x=historical_df[positive_mask]['Year'],
            y=historical_df[positive_mask]['Return'],
            name='Positive Returns',
            marker_color='green',
            opacity=0.7
        ))

        fig_hist.add_trace(go.Bar(
            x=historical_df[~positive_mask]['Year'],
            y=historical_df[~positive_mask]['Return'],
            name='Negative Returns',
            marker_color='red',
            opacity=0.7
        ))

        fig_hist.add_hline(y=stats['mean'] * 100, line_dash="dash", line_color="blue",
                           annotation_text=f"Average: {stats['mean'] * 100:.1f}%")

        fig_hist.update_layout(
            title='Historical US Stock Market Annual Returns (S&P 500 Total Return)',
            xaxis_title='Year',
            yaxis_title='Annual Return (%)',
            height=400,
            barmode='overlay'
        )

        st.plotly_chart(fig_hist, use_container_width=True)

        st.info(
            f"💡 **Historical Data**: Based on approximately {stats['total_years']} years of S&P 500 total return data. "
            f"When using historical simulation mode, each Monte Carlo run randomly samples from these actual returns.")


def retirement_tab():
    """Enhanced Retirement and Social Security tab with insolvency option"""
    st.header("🖼️ Retirement & Social Security")

    # NEW: Social Security Insolvency Settings
    st.subheader("⚠️ Social Security Insolvency Planning")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.ss_insolvency_enabled = st.checkbox(
            "Enable Social Security Insolvency Adjustment",
            value=st.session_state.ss_insolvency_enabled,
            help="Account for potential Social Security benefit reductions due to trust fund insolvency"
        )

    with col2:
        if st.session_state.ss_insolvency_enabled:
            st.session_state.ss_shortfall_percentage = st.number_input(
                "Benefit Shortfall Percentage (%)",
                min_value=0.0,
                max_value=50.0,
                value=float(st.session_state.ss_shortfall_percentage),
                step=1.0,
                format="%.1f",
                help="Percentage reduction in Social Security benefits (e.g., 30% means only 70% of benefits paid)"
            )

            effective_percentage = 100 - st.session_state.ss_shortfall_percentage
            st.info(
                f"💡 With {st.session_state.ss_shortfall_percentage}% shortfall, you'll receive {effective_percentage}% of stated benefits")

    # Combined retirement summary
    st.subheader("👫 Combined Retirement Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**{st.session_state.parent1_name} Retirement**")
        years_to_retirement_x = max(0, st.session_state.parentX_retirement_age - st.session_state.parentX_age)

        # Apply insolvency adjustment if enabled
        base_annual_ss_x = st.session_state.parentX_ss_benefit * 12
        if st.session_state.ss_insolvency_enabled:
            adjusted_annual_ss_x = base_annual_ss_x * (1 - st.session_state.ss_shortfall_percentage / 100)
        else:
            adjusted_annual_ss_x = base_annual_ss_x

        st.metric("Years to Retirement", years_to_retirement_x)
        st.metric("Annual Social Security (Base)", format_currency(base_annual_ss_x))
        if st.session_state.ss_insolvency_enabled:
            st.metric("Annual Social Security (Adjusted)", format_currency(adjusted_annual_ss_x))

        # Early and delayed retirement options
        early_benefit_x = adjusted_annual_ss_x * 0.75  # ~25% reduction
        delayed_benefit_x = adjusted_annual_ss_x * 1.32  # ~32% increase

        st.write("**Benefit Options (Adjusted):**")
        st.write(f"• At 62 (early): {format_currency(early_benefit_x)}")
        st.write(f"• At {st.session_state.parentX_retirement_age} (planned): {format_currency(adjusted_annual_ss_x)}")
        st.write(f"• At 70 (delayed): {format_currency(delayed_benefit_x)}")

    with col2:
        st.write(f"**{st.session_state.parent2_name} Retirement**")
        years_to_retirement_y = max(0, st.session_state.parentY_retirement_age - st.session_state.parentY_age)

        # Apply insolvency adjustment if enabled
        base_annual_ss_y = st.session_state.parentY_ss_benefit * 12
        if st.session_state.ss_insolvency_enabled:
            adjusted_annual_ss_y = base_annual_ss_y * (1 - st.session_state.ss_shortfall_percentage / 100)
        else:
            adjusted_annual_ss_y = base_annual_ss_y

        st.metric("Years to Retirement", years_to_retirement_y)
        st.metric("Annual Social Security (Base)", format_currency(base_annual_ss_y))
        if st.session_state.ss_insolvency_enabled:
            st.metric("Annual Social Security (Adjusted)", format_currency(adjusted_annual_ss_y))

        # Early and delayed retirement options
        early_benefit_y = adjusted_annual_ss_y * 0.75
        delayed_benefit_y = adjusted_annual_ss_y * 1.32

        st.write("**Benefit Options (Adjusted):**")
        st.write(f"• At 62 (early): {format_currency(early_benefit_y)}")
        st.write(f"• At {st.session_state.parentY_retirement_age} (planned): {format_currency(adjusted_annual_ss_y)}")
        st.write(f"• At 70 (delayed): {format_currency(delayed_benefit_y)}")

    # Combined analysis
    st.subheader("💰 Combined Social Security Analysis")

    combined_annual_ss = adjusted_annual_ss_x + adjusted_annual_ss_y
    combined_early = early_benefit_x + early_benefit_y
    combined_delayed = delayed_benefit_x + delayed_benefit_y

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Combined Early (62)", format_currency(combined_early))
    with col2:
        st.metric("Combined Planned", format_currency(combined_annual_ss))
    with col3:
        st.metric("Combined Delayed (70)", format_currency(combined_delayed))

    # Retirement income replacement calculation
    st.subheader("📊 Retirement Income Analysis")

    current_combined_income = st.session_state.parentX_income + st.session_state.parentY_income
    ss_replacement_ratio = (combined_annual_ss / current_combined_income) * 100 if current_combined_income > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Current Combined Income", format_currency(current_combined_income, show_thousands=True))
        st.metric("Social Security Replacement", f"{ss_replacement_ratio:.1f}%")

    with col2:
        # Estimate additional retirement income needed (assuming 80% replacement goal)
        target_retirement_income = current_combined_income * 0.8
        additional_income_needed = max(0, target_retirement_income - combined_annual_ss)

        st.metric("Target Retirement Income (80%)", format_currency(target_retirement_income, show_thousands=True))
        st.metric("Additional Income Needed", format_currency(additional_income_needed, show_thousands=True))

    # Strategy tips with insolvency context
    strategy_tips = "💡 **Social Security Strategy Tips:**\n"
    strategy_tips += "• Delaying until age 70 increases benefits by ~8% per year after full retirement age\n"
    strategy_tips += "• Consider having the lower earner claim early while the higher earner delays\n"
    strategy_tips += "• Social Security is typically 40-60% of retirement income - plan for additional sources\n"
    strategy_tips += "• Benefits are adjusted for inflation (COLA) each year\n"

    if st.session_state.ss_insolvency_enabled:
        strategy_tips += f"• **Insolvency Planning**: Current projections assume {st.session_state.ss_shortfall_percentage}% benefit reduction\n"
        strategy_tips += "• Consider this uncertainty when planning retirement savings and withdrawal strategies"

    st.info(strategy_tips)


def run_comprehensive_simulation():
    """Enhanced Monte Carlo simulation with historical returns option, taxes, house ownership tracking, and detailed breakdown by parent"""
    try:
        # Get parameters
        start_year = st.session_state.mc_start_year
        years = st.session_state.mc_years
        simulations = st.session_state.mc_simulations
        use_historical = st.session_state.mc_use_historical
        normalize_to_today = st.session_state.mc_normalize_to_today_dollars

        # Get active economic scenario
        scenario = st.session_state.economic_scenarios[st.session_state.active_scenario]

        # Initial values with house equity tracking by owner
        initial_parent1_net_worth = st.session_state.parentX_net_worth
        initial_parent2_net_worth = st.session_state.parentY_net_worth
        initial_family_net_worth = 0.0

        initial_income = st.session_state.parentX_income + st.session_state.parentY_income
        initial_family_expenses = sum(st.session_state.expenses.values())

        # Add house equity by owner
        current_year = st.session_state.current_year
        for house in st.session_state.houses:
            status, _ = house.get_status_for_year(current_year)
            if status in ["Own_Live", "Own_Rent"]:
                house_equity = max(0, house.current_value - house.mortgage_balance)
                if house.owner == "Parent1":
                    initial_parent1_net_worth += house_equity
                elif house.owner == "Parent2":
                    initial_parent2_net_worth += house_equity
                else:  # Shared
                    initial_family_net_worth += house_equity

        initial_total_net_worth = initial_parent1_net_worth + initial_parent2_net_worth + initial_family_net_worth

        # Create arrays to store results and detailed breakdown data
        total_results = np.zeros((simulations, years + 1))
        parent1_results = np.zeros((simulations, years + 1))
        parent2_results = np.zeros((simulations, years + 1))
        family_results = np.zeros((simulations, years + 1))

        total_results[:, 0] = initial_total_net_worth
        parent1_results[:, 0] = initial_parent1_net_worth
        parent2_results[:, 0] = initial_parent2_net_worth
        family_results[:, 0] = initial_family_net_worth

        # Store detailed data for all simulations to calculate medians
        all_simulation_data = []
        for year_idx in range(years):
            all_simulation_data.append({
                'gross_income': [],
                'taxes': [],
                'after_tax_income': [],
                'rental_income': [],
                'total_income': [],
                'family_expenses': [],
                'children_expenses': [],
                'house_expenses': [],
                'major_purchases': [],
                'recurring_expenses': [],
                'total_expenses': [],
                'net_income': [],
                'investment_return': [],
                'net_worth': [],
                'parent1_net_worth': [],
                'parent2_net_worth': [],
                'family_net_worth': []
            })

        # Prepare historical returns if using historical mode
        if use_historical:
            historical_returns = np.array(HISTORICAL_STOCK_RETURNS)

        # Run simulations
        for sim in range(simulations):
            total_net_worth = initial_total_net_worth
            parent1_net_worth = initial_parent1_net_worth
            parent2_net_worth = initial_parent2_net_worth
            family_net_worth = initial_family_net_worth

            for year in range(1, years + 1):
                current_sim_year = start_year + year - 1

                # Calculate parent ages for this year
                parentX_age_in_year = st.session_state.parentX_age + year - 1
                parentY_age_in_year = st.session_state.parentY_age + year - 1

                # === INCOME CALCULATIONS ===
                # Base income with raises
                parentX_raise_rate = st.session_state.parentX_raise / 100
                parentY_raise_rate = st.session_state.parentY_raise / 100

                parentX_income = st.session_state.parentX_income * ((1 + parentX_raise_rate) ** (year - 1))
                parentY_income = st.session_state.parentY_income * ((1 + parentY_raise_rate) ** (year - 1))

                # Apply job changes
                for _, job_change in st.session_state.parentX_job_changes.iterrows():
                    if current_sim_year >= job_change['Year']:
                        parentX_income = job_change['New Income'] * (
                                (1 + parentX_raise_rate) ** max(0, current_sim_year - job_change['Year']))

                for _, job_change in st.session_state.parentY_job_changes.iterrows():
                    if current_sim_year >= job_change['Year']:
                        parentY_income = job_change['New Income'] * (
                                (1 + parentY_raise_rate) ** max(0, current_sim_year - job_change['Year']))

                # Social Security benefits and retirement with insolvency adjustment
                ss_income = 0
                if parentX_age_in_year >= st.session_state.parentX_retirement_age:
                    base_ss_x = st.session_state.parentX_ss_benefit * 12
                    if st.session_state.ss_insolvency_enabled:
                        ss_income += base_ss_x * (1 - st.session_state.ss_shortfall_percentage / 100)
                    else:
                        ss_income += base_ss_x
                    parentX_income = 0  # Retired

                if parentY_age_in_year >= st.session_state.parentY_retirement_age:
                    base_ss_y = st.session_state.parentY_ss_benefit * 12
                    if st.session_state.ss_insolvency_enabled:
                        ss_income += base_ss_y * (1 - st.session_state.ss_shortfall_percentage / 100)
                    else:
                        ss_income += base_ss_y
                    parentY_income = 0  # Retired

                gross_income = parentX_income + parentY_income + ss_income

                # Apply asymmetric income variability to EMPLOYMENT income only (not SS)
                employment_income = parentX_income + parentY_income
                if use_historical:
                    # For historical mode, use symmetric variability for income
                    income_var = st.session_state.mc_income_variability / 100
                    income_multiplier = 1 + np.random.normal(0, income_var)
                else:
                    # Use asymmetric variability for traditional mode
                    if np.random.random() < 0.5:  # Negative direction
                        income_var = st.session_state.mc_income_variability_negative / 100
                        income_multiplier = 1 - abs(np.random.normal(0, income_var))
                    else:  # Positive direction
                        income_var = st.session_state.mc_income_variability_positive / 100
                        income_multiplier = 1 + abs(np.random.normal(0, income_var))

                # Variability only affects employment income, SS is fixed
                gross_income = employment_income * income_multiplier + ss_income

                # === TAX CALCULATIONS ===
                # Calculate taxes with inflation-adjusted 401k contributions
                pretax_401k_inflated = st.session_state.pretax_401k * ((1 + scenario.inflation_rate) ** (year - 1))

                tax_info = calculate_annual_taxes(
                    gross_income,
                    pretax_401k_inflated,
                    st.session_state.state_tax_rate
                )

                after_tax_income = tax_info['after_tax_income']
                annual_taxes = tax_info['total_tax']

                # === EXPENSE CALCULATIONS ===
                # Family expenses with growth and asymmetric variability
                base_family_expenses = initial_family_expenses * (
                        (1 + scenario.expense_growth_rate) ** (year - 1))

                if use_historical:
                    expense_var = st.session_state.mc_expense_variability / 100
                    expense_multiplier = 1 + np.random.normal(0, expense_var)
                else:
                    # Use asymmetric variability for traditional mode
                    if np.random.random() < 0.5:  # Negative direction (lower expenses)
                        expense_var = st.session_state.mc_expense_variability_negative / 100
                        expense_multiplier = 1 - abs(np.random.normal(0, expense_var))
                    else:  # Positive direction (higher expenses)
                        expense_var = st.session_state.mc_expense_variability_positive / 100
                        expense_multiplier = 1 + abs(np.random.normal(0, expense_var))

                annual_family_expenses = base_family_expenses * expense_multiplier

                # Children expenses
                annual_children_expenses = 0
                for child in st.session_state.children_list:
                    child_age_in_year = current_sim_year - child['birth_year']
                    if 0 <= child_age_in_year < len(st.session_state.children_expenses):
                        child_row = st.session_state.children_expenses.iloc[child_age_in_year]
                        for col in child_row.index:
                            if col != 'Age':
                                # Use healthcare inflation for Healthcare column
                                if col == 'Healthcare':
                                    inflated_expense = child_row[col] * ((1 + scenario.healthcare_inflation_rate) ** (year - 1))
                                else:
                                    inflated_expense = child_row[col] * ((1 + scenario.inflation_rate) ** (year - 1))
                                annual_children_expenses += inflated_expense

                # House-related expenses and rental income
                annual_house_expenses = 0
                annual_rental_income = 0

                for house in st.session_state.houses:
                    status, rental_income = house.get_status_for_year(current_sim_year)

                    if status in ["Own_Live", "Own_Rent"]:
                        # Mortgage payments
                        mortgage_years_elapsed = current_sim_year - house.purchase_year
                        remaining_mortgage_years = max(0, house.mortgage_years_left - mortgage_years_elapsed)

                        if remaining_mortgage_years > 0:
                            monthly_rate = house.mortgage_rate / 12
                            num_payments = remaining_mortgage_years * 12

                            if monthly_rate > 0:
                                # Calculate remaining balance (simplified)
                                original_payment = house.mortgage_balance * (
                                        monthly_rate * (1 + monthly_rate) ** (house.mortgage_years_left * 12)
                                ) / ((1 + monthly_rate) ** (house.mortgage_years_left * 12) - 1)
                                annual_house_expenses += original_payment * 12
                            else:
                                annual_house_expenses += house.mortgage_balance / remaining_mortgage_years

                        # Property tax, insurance, maintenance, and upkeep (with inflation)
                        current_home_value = house.current_value * ((1 + scenario.inflation_rate) ** (year - 1))
                        annual_property_tax = current_home_value * house.property_tax_rate
                        annual_insurance = house.home_insurance * ((1 + scenario.inflation_rate) ** (year - 1))
                        annual_maintenance = current_home_value * house.maintenance_rate  # Percentage-based maintenance
                        annual_upkeep = house.upkeep_costs * ((1 + scenario.inflation_rate) ** (year - 1))  # Flat upkeep

                        annual_house_expenses += annual_property_tax + annual_insurance + annual_maintenance + annual_upkeep

                    if status == "Own_Rent":
                        # Rental income (with inflation)
                        monthly_rent = rental_income * ((1 + scenario.inflation_rate) ** (year - 1))
                        annual_rental_income += monthly_rent * 12

                    elif status == "Sell":
                        # One-time gain from house sale (only in the year of sale)
                        # Check if this is the first year with "Sell" status
                        prev_year_status, _ = house.get_status_for_year(
                            current_sim_year - 1) if current_sim_year > start_year else ("Own_Live", 0)

                        if prev_year_status != "Sell":  # First year of sale
                            sale_value = house.current_value * ((1 + scenario.inflation_rate) ** (year - 1))
                            # Simplified: assume mortgage is paid off at sale
                            remaining_mortgage = house.mortgage_balance * max(0, (
                                    1 - (current_sim_year - house.purchase_year) / house.mortgage_years_left))
                            sale_proceeds = max(0, sale_value - remaining_mortgage)

                            # Add sale proceeds to appropriate owner's net worth
                            if house.owner == "Parent1":
                                parent1_net_worth += sale_proceeds
                            elif house.owner == "Parent2":
                                parent2_net_worth += sale_proceeds
                            else:  # Shared
                                family_net_worth += sale_proceeds

                # Major one-time purchases
                annual_major_purchases = 0
                for purchase in st.session_state.major_purchases:
                    if purchase.year == current_sim_year:
                        if purchase.financing_years == 0:
                            annual_major_purchases += purchase.amount
                        else:
                            # Calculate annual payment for financed purchases
                            monthly_rate = purchase.interest_rate / 12
                            num_payments = purchase.financing_years * 12

                            if monthly_rate > 0:
                                monthly_payment = purchase.amount * (
                                        monthly_rate * (1 + monthly_rate) ** num_payments
                                ) / ((1 + monthly_rate) ** num_payments - 1)
                            else:
                                monthly_payment = purchase.amount / num_payments

                            annual_major_purchases += monthly_payment * 12

                    # Ongoing financing payments
                    elif (purchase.financing_years > 0 and
                          current_sim_year > purchase.year and
                          current_sim_year <= purchase.year + purchase.financing_years):

                        monthly_rate = purchase.interest_rate / 12
                        num_payments = purchase.financing_years * 12

                        if monthly_rate > 0:
                            monthly_payment = purchase.amount * (
                                    monthly_rate * (1 + monthly_rate) ** num_payments
                            ) / ((1 + monthly_rate) ** num_payments - 1)
                        else:
                            monthly_payment = purchase.amount / num_payments

                        annual_major_purchases += monthly_payment * 12

                # Recurring expenses
                annual_recurring_expenses = 0
                for expense in st.session_state.recurring_expenses:
                    if (current_sim_year >= expense.start_year and
                            (expense.end_year is None or current_sim_year <= expense.end_year) and
                            (current_sim_year - expense.start_year) % expense.frequency_years == 0):

                        if expense.inflation_adjust:
                            inflation_years = current_sim_year - expense.start_year
                            cost = expense.amount * ((1 + scenario.inflation_rate) ** inflation_years)
                        else:
                            cost = expense.amount

                        annual_recurring_expenses += cost

                # Total income and expenses
                total_annual_income = after_tax_income + annual_rental_income
                total_annual_expenses = (annual_family_expenses + annual_children_expenses +
                                         annual_house_expenses + annual_major_purchases +
                                         annual_recurring_expenses)

                # Calculate net income
                net_annual_income = total_annual_income - total_annual_expenses

                # === INVESTMENT RETURN CALCULATION ===
                if use_historical:
                    # Use historical returns - randomly sample from historical data
                    historical_return = np.random.choice(historical_returns)

                    # Apply returns proportionally to each owner's net worth
                    parent1_investment_return = parent1_net_worth * historical_return
                    parent2_investment_return = parent2_net_worth * historical_return
                    family_investment_return = family_net_worth * historical_return
                    total_investment_return = parent1_investment_return + parent2_investment_return + family_investment_return
                else:
                    # Use traditional method with asymmetric variability
                    if np.random.random() < 0.5:  # Negative direction
                        return_var = st.session_state.mc_return_variability_negative / 100
                        return_multiplier = 1 - abs(np.random.normal(0, return_var))
                    else:  # Positive direction
                        return_var = st.session_state.mc_return_variability_positive / 100
                        return_multiplier = 1 + abs(np.random.normal(0, return_var))

                    # Apply returns proportionally to each owner's net worth
                    parent1_investment_return = parent1_net_worth * scenario.investment_return * return_multiplier
                    parent2_investment_return = parent2_net_worth * scenario.investment_return * return_multiplier
                    family_investment_return = family_net_worth * scenario.investment_return * return_multiplier
                    total_investment_return = parent1_investment_return + parent2_investment_return + family_investment_return

                # Update net worth by owner (simplified allocation of net income to family)
                family_net_worth = family_net_worth + net_annual_income + family_investment_return
                parent1_net_worth = parent1_net_worth + parent1_investment_return
                parent2_net_worth = parent2_net_worth + parent2_investment_return

                total_net_worth = parent1_net_worth + parent2_net_worth + family_net_worth

                # Apply floor to prevent unlimited debt
                total_net_worth = max(total_net_worth, -2000000)
                parent1_net_worth = max(parent1_net_worth, -500000)
                parent2_net_worth = max(parent2_net_worth, -500000)
                family_net_worth = max(family_net_worth, -1000000)

                # Store results (normalize to today's dollars if requested)
                if normalize_to_today:
                    inflation_factor = (1 + scenario.inflation_rate) ** (year - 1)
                    total_results[sim, year] = total_net_worth / inflation_factor
                    parent1_results[sim, year] = parent1_net_worth / inflation_factor
                    parent2_results[sim, year] = parent2_net_worth / inflation_factor
                    family_results[sim, year] = family_net_worth / inflation_factor
                else:
                    total_results[sim, year] = total_net_worth
                    parent1_results[sim, year] = parent1_net_worth
                    parent2_results[sim, year] = parent2_net_worth
                    family_results[sim, year] = family_net_worth

                # Store data for all simulations to calculate medians later
                year_idx = year - 1  # Convert to 0-based index
                all_simulation_data[year_idx]['gross_income'].append(gross_income)
                all_simulation_data[year_idx]['taxes'].append(annual_taxes)
                all_simulation_data[year_idx]['after_tax_income'].append(after_tax_income)
                all_simulation_data[year_idx]['rental_income'].append(annual_rental_income)
                all_simulation_data[year_idx]['total_income'].append(total_annual_income)
                all_simulation_data[year_idx]['family_expenses'].append(annual_family_expenses)
                all_simulation_data[year_idx]['children_expenses'].append(annual_children_expenses)
                all_simulation_data[year_idx]['house_expenses'].append(annual_house_expenses)
                all_simulation_data[year_idx]['major_purchases'].append(annual_major_purchases)
                all_simulation_data[year_idx]['recurring_expenses'].append(annual_recurring_expenses)
                all_simulation_data[year_idx]['total_expenses'].append(total_annual_expenses)
                all_simulation_data[year_idx]['net_income'].append(net_annual_income)
                all_simulation_data[year_idx]['investment_return'].append(total_investment_return)
                all_simulation_data[year_idx]['net_worth'].append(total_net_worth)
                all_simulation_data[year_idx]['parent1_net_worth'].append(parent1_net_worth)
                all_simulation_data[year_idx]['parent2_net_worth'].append(parent2_net_worth)
                all_simulation_data[year_idx]['family_net_worth'].append(family_net_worth)

        # Calculate median values for yearly breakdown
        yearly_breakdown = []
        for year_idx in range(years):
            current_sim_year = start_year + year_idx
            year_data = all_simulation_data[year_idx]

            # Apply inflation normalization to breakdown if requested
            if normalize_to_today:
                inflation_factor = (1 + scenario.inflation_rate) ** year_idx
            else:
                inflation_factor = 1.0

            yearly_breakdown.append({
                'Year': current_sim_year,
                'Gross Income': np.median(year_data['gross_income']) / inflation_factor,
                'Taxes': np.median(year_data['taxes']) / inflation_factor,
                'After-Tax Income': np.median(year_data['after_tax_income']) / inflation_factor,
                'Rental Income': np.median(year_data['rental_income']) / inflation_factor,
                'Total Income': np.median(year_data['total_income']) / inflation_factor,
                'Family Expenses': np.median(year_data['family_expenses']) / inflation_factor,
                'Children Expenses': np.median(year_data['children_expenses']) / inflation_factor,
                'House Expenses': np.median(year_data['house_expenses']) / inflation_factor,
                'Major Purchases': np.median(year_data['major_purchases']) / inflation_factor,
                'Recurring Expenses': np.median(year_data['recurring_expenses']) / inflation_factor,
                'Total Expenses': np.median(year_data['total_expenses']) / inflation_factor,
                'Net Income': np.median(year_data['net_income']) / inflation_factor,
                'Investment Return': np.median(year_data['investment_return']) / inflation_factor,
                'Net Worth': np.median(year_data['net_worth']) / inflation_factor,
                'Parent1 Net Worth': np.median(year_data['parent1_net_worth']) / inflation_factor,
                'Parent2 Net Worth': np.median(year_data['parent2_net_worth']) / inflation_factor,
                'Family Net Worth': np.median(year_data['family_net_worth']) / inflation_factor
            })

        return (total_results, parent1_results, parent2_results, family_results,
                list(range(start_year, start_year + years + 1)), yearly_breakdown)

    except Exception as e:
        st.error(f"Error running comprehensive simulation: {str(e)}")
        return None, None, None, None, None, None


def combined_simulation_tab():
    """Enhanced Combined Monte Carlo and Yearly Analysis Tab with all new features"""
    st.header("📊 Comprehensive Financial Analysis")

    st.info(
        "💡 **Complete Financial Simulation**: This analysis includes ALL cash flows - parent incomes, family expenses, children expenses, house portfolio (including rentals), major purchases, recurring expenses, Social Security benefits, and retirement timing.")

    # Enhanced settings with all new options
    with st.expander("🔧 Simulation Settings", expanded=False):
        # Simulation Type Selection
        st.subheader("📈 Simulation Type")

        simulation_type_col1, simulation_type_col2 = st.columns(2)

        with simulation_type_col1:
            st.session_state.mc_use_historical = st.radio(
                "Investment Return Method",
                options=[False, True],
                format_func=lambda
                    x: "Traditional (Scenario-based with Variability)" if not x else "Historical (Random Historical Performance)",
                index=1 if st.session_state.mc_use_historical else 0,
                key="mc_simulation_type",
                help="Choose between traditional Monte Carlo with statistical distributions or historical performance sampling"
            )

        with simulation_type_col2:
            if st.session_state.mc_use_historical:
                st.info(
                    "🏛️ **Historical Mode**: Each simulation randomly samples investment returns from the last 100 years of US stock market data (S&P 500 total returns)")

                # Historical statistics summary
                stats = get_historical_return_stats()
                st.write(f"**Historical Data Summary:**")
                st.write(f"• {stats['total_years']} years of data")
                st.write(f"• Average: {stats['mean'] * 100:.1f}%")
                st.write(f"• Std Dev: {stats['std'] * 100:.1f}%")
                st.write(f"• Range: {stats['min'] * 100:.1f}% to {stats['max'] * 100:.1f}%")
            else:
                st.info(
                    "📊 **Traditional Mode**: Uses your active economic scenario's investment return rate with configurable statistical variability")

        # NEW: Inflation normalization toggle
        st.subheader("💵 Display Options")
        st.session_state.mc_normalize_to_today_dollars = st.checkbox(
            "Normalize simulation to today's dollars",
            value=st.session_state.mc_normalize_to_today_dollars,
            help="Show all net worth values in today's purchasing power by adjusting for inflation"
        )

        if st.session_state.mc_normalize_to_today_dollars:
            st.info(
                "💡 **Today's Dollars**: All results will be adjusted for inflation to show purchasing power in today's dollars")
        else:
            st.info("📈 **Future Dollars**: Results will be shown in nominal future dollar amounts")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Simulation Parameters**")
            st.session_state.mc_start_year = st.number_input(
                "Starting Year", min_value=2025, max_value=2030,
                value=int(st.session_state.mc_start_year), step=1, key="mc_start_year_input"
            )
            st.session_state.mc_years = st.number_input(
                "Years to Simulate", min_value=1, max_value=100,
                value=int(st.session_state.mc_years), step=1, key="mc_years_input"
            )
            st.session_state.mc_simulations = st.number_input(
                "Number of Simulations", min_value=1, max_value=10000,
                value=int(st.session_state.mc_simulations), step=1, key="mc_simulations_input"
            )

        with col2:
            if not st.session_state.mc_use_historical:
                st.write("**Asymmetric Variability Settings**")
                st.info("💡 Set different variability ranges for positive and negative directions")

                # Income variability
                income_col1, income_col2 = st.columns(2)
                with income_col1:
                    st.session_state.mc_income_variability_positive = st.number_input(
                        "Income Var. (+%)", min_value=0.0, max_value=50.0,
                        value=float(st.session_state.mc_income_variability_positive), step=0.5, format="%.1f",
                        key="mc_income_var_pos_input"
                    )
                with income_col2:
                    st.session_state.mc_income_variability_negative = st.number_input(
                        "Income Var. (-%)", min_value=0.0, max_value=50.0,
                        value=float(st.session_state.mc_income_variability_negative), step=0.5, format="%.1f",
                        key="mc_income_var_neg_input"
                    )

                # Expense variability
                expense_col1, expense_col2 = st.columns(2)
                with expense_col1:
                    st.session_state.mc_expense_variability_positive = st.number_input(
                        "Expense Var. (+%)", min_value=0.0, max_value=50.0,
                        value=float(st.session_state.mc_expense_variability_positive), step=0.5, format="%.1f",
                        key="mc_expense_var_pos_input"
                    )
                with expense_col2:
                    st.session_state.mc_expense_variability_negative = st.number_input(
                        "Expense Var. (-%)", min_value=0.0, max_value=50.0,
                        value=float(st.session_state.mc_expense_variability_negative), step=0.5, format="%.1f",
                        key="mc_expense_var_neg_input"
                    )

                # Return variability
                return_col1, return_col2 = st.columns(2)
                with return_col1:
                    st.session_state.mc_return_variability_positive = st.number_input(
                        "Return Var. (+%)", min_value=0.0, max_value=100.0,
                        value=float(st.session_state.mc_return_variability_positive), step=1.0, format="%.1f",
                        key="mc_return_var_pos_input"
                    )
                with return_col2:
                    st.session_state.mc_return_variability_negative = st.number_input(
                        "Return Var. (-%)", min_value=0.0, max_value=100.0,
                        value=float(st.session_state.mc_return_variability_negative), step=1.0, format="%.1f",
                        key="mc_return_var_neg_input"
                    )
            else:
                st.write("**Symmetric Variability Settings**")
                st.info("💡 Historical mode uses symmetric variability")

                st.session_state.mc_income_variability = st.number_input(
                    "Income Variability (±%)", min_value=0.0, max_value=50.0,
                    value=float(st.session_state.mc_income_variability), step=0.5, format="%.1f",
                    key="mc_income_var_input"
                )
                st.session_state.mc_expense_variability = st.number_input(
                    "Expense Variability (±%)", min_value=0.0, max_value=50.0,
                    value=float(st.session_state.mc_expense_variability), step=0.5, format="%.1f",
                    key="mc_expense_var_input"
                )

    # Show active scenario
    if st.session_state.mc_use_historical:
        st.info(f"🎯 **Using Active Scenario for Inflation**: {st.session_state.active_scenario} - "
                f"Inflation: {st.session_state.economic_scenarios[st.session_state.active_scenario].inflation_rate * 100:.1f}% "
                f"(Investment returns use historical data)")
    else:
        st.info(f"🎯 **Using Active Scenario**: {st.session_state.active_scenario} - "
                f"Investment Return: {st.session_state.economic_scenarios[st.session_state.active_scenario].investment_return * 100:.1f}%, "
                f"Inflation: {st.session_state.economic_scenarios[st.session_state.active_scenario].inflation_rate * 100:.1f}%")

    # Run simulation button
    button_text = "🚀 Run Historical Performance Analysis" if st.session_state.mc_use_historical else "🚀 Run Traditional Monte Carlo Analysis"

    if st.button(button_text, type="primary"):
        simulation_description = "historical performance sampling" if st.session_state.mc_use_historical else "traditional Monte Carlo"
        dollar_description = "today's dollars" if st.session_state.mc_normalize_to_today_dollars else "future dollars"

        with st.spinner(
                f"Running comprehensive analysis using {simulation_description} in {dollar_description}... This includes detailed yearly expense breakdown."):
            results = run_comprehensive_simulation()

            if results[0] is not None:
                (total_results, parent1_results, parent2_results, family_results, years, yearly_breakdown) = results

                st.session_state.mc_total_results = total_results
                st.session_state.mc_parent1_results = parent1_results
                st.session_state.mc_parent2_results = parent2_results
                st.session_state.mc_family_results = family_results
                st.session_state.mc_years_list = years
                st.session_state.yearly_breakdown = yearly_breakdown
                st.session_state.mc_last_simulation_type = "Historical" if st.session_state.mc_use_historical else "Traditional"
                st.session_state.mc_last_normalization = st.session_state.mc_normalize_to_today_dollars

                success_message = f"✅ Analysis completed using {'historical performance data' if st.session_state.mc_use_historical else 'traditional Monte Carlo'}! "
                success_message += f"Generated {st.session_state.mc_simulations:,} scenarios over {st.session_state.mc_years} years "
                success_message += f"in {'today\'s dollars' if st.session_state.mc_normalize_to_today_dollars else 'future dollars'}."
                st.success(success_message)

    # Display results if available
    if ('mc_total_results' in st.session_state and 'yearly_breakdown' in st.session_state and
            'mc_parent1_results' in st.session_state and 'mc_parent2_results' in st.session_state and
            'mc_family_results' in st.session_state):

        # Show what type of simulation was last run
        last_sim_type = st.session_state.get('mc_last_simulation_type', 'Unknown')
        last_normalization = st.session_state.get('mc_last_normalization', False)
        dollar_type = "Today's Dollars" if last_normalization else "Future Dollars"
        st.info(f"📊 **Results from {last_sim_type} Simulation** ({dollar_type})")

        # Create tabs for different views
        mc_tab, detailed_tab, yearly_tab, breakdown_tab = st.tabs(
            ["📈 Monte Carlo Results", "🔍 Detailed Breakdown", "📅 Yearly Expense Analysis", "📋 Data Export"])

        with mc_tab:
            st.subheader("📊 Monte Carlo Simulation Results")

            total_results = st.session_state.mc_total_results
            years = st.session_state.mc_years_list

            # Calculate percentiles
            percentiles = {
                '95th': np.percentile(total_results, 95, axis=0),
                '75th': np.percentile(total_results, 75, axis=0),
                'Median': np.percentile(total_results, 50, axis=0),
                '25th': np.percentile(total_results, 25, axis=0),
                '5th': np.percentile(total_results, 5, axis=0)
            }

            # Create plot
            fig = go.Figure()

            # Add percentile lines
            colors = {
                '95th': '#2E8B57',
                '75th': '#4682B4',
                'Median': '#FF6347',
                '25th': '#4682B4',
                '5th': '#8B0000'
            }

            for label, values in percentiles.items():
                fig.add_trace(go.Scatter(
                    x=years, y=values, mode='lines', name=f'{label} Percentile',
                    line=dict(color=colors[label], width=4 if label == 'Median' else 2)
                ))

            # Add retirement markers
            parentX_retirement_year = st.session_state.mc_start_year + (
                    st.session_state.parentX_retirement_age - st.session_state.parentX_age)
            parentY_retirement_year = st.session_state.mc_start_year + (
                    st.session_state.parentY_retirement_age - st.session_state.parentY_age)

            if parentX_retirement_year <= max(years):
                fig.add_vline(x=parentX_retirement_year, line_dash="dash", line_color="purple",
                              annotation_text=f"{st.session_state.parent1_name} Retirement", annotation_position="top")

            if parentY_retirement_year <= max(years):
                fig.add_vline(x=parentY_retirement_year, line_dash="dash", line_color="orange",
                              annotation_text=f"{st.session_state.parent2_name} Retirement", annotation_position="top")

            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.7)

            # Update title to reflect simulation type and dollar type
            title_suffix = "Historical Performance" if last_sim_type == "Historical" else "Traditional Monte Carlo"
            fig.update_layout(
                title=f'Net Worth Projection - {st.session_state.mc_years} Years ({st.session_state.mc_simulations:,} Simulations - {title_suffix} - {dollar_type})',
                xaxis_title='Year', yaxis_title=f'Net Worth ({dollar_type})', height=600,
                hovermode='x unified', yaxis=dict(tickformat='$,.0f')
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary statistics
            final_year_results = total_results[:, -1]
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Median Final Net Worth", format_currency(np.median(final_year_results), show_thousands=True))
            with col2:
                st.metric("25th Percentile",
                          format_currency(np.percentile(final_year_results, 25), show_thousands=True))
            with col3:
                st.metric("75th Percentile",
                          format_currency(np.percentile(final_year_results, 75), show_thousands=True))
            with col4:
                probability_positive = np.mean(final_year_results > 0) * 100
                st.metric("Probability of Positive Net Worth", f"{probability_positive:.1f}%")

            # Additional statistics
            st.subheader("📈 Additional Analysis")
            col1, col2, col3 = st.columns(3)

            with col1:
                worst_case = np.min(final_year_results)
                best_case = np.max(final_year_results)
                st.metric("Worst Case Scenario", format_currency(worst_case, show_thousands=True))
                st.metric("Best Case Scenario", format_currency(best_case, show_thousands=True))

            with col2:
                # Calculate some risk metrics
                negative_outcomes = np.sum(final_year_results < 0)
                st.metric("Scenarios with Negative Net Worth",
                          f"{negative_outcomes}/{st.session_state.mc_simulations}")

                millionaire_outcomes = np.sum(final_year_results >= 1000000)
                st.metric("Scenarios Reaching $1M+", f"{millionaire_outcomes}/{st.session_state.mc_simulations}")

            with col3:
                # Show range statistics
                range_width = best_case - worst_case
                st.metric("Range (Best - Worst)", format_currency(range_width, show_thousands=True))

                std_dev = np.std(final_year_results)
                st.metric("Standard Deviation", format_currency(std_dev, show_thousands=True))

        with detailed_tab:
            st.subheader("🔍 Detailed Monte Carlo Breakdown by Owner")

            parent1_results = st.session_state.mc_parent1_results
            parent2_results = st.session_state.mc_parent2_results
            family_results = st.session_state.mc_family_results
            years = st.session_state.mc_years_list

            # Create breakdown chart
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    f'{st.session_state.parent1_name} Net Worth',
                    f'{st.session_state.parent2_name} Net Worth',
                    'Family/Shared Net Worth',
                    'Combined Total Net Worth'
                ),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )

            # Parent 1 Net Worth
            parent1_median = np.percentile(parent1_results, 50, axis=0)
            parent1_75th = np.percentile(parent1_results, 75, axis=0)
            parent1_25th = np.percentile(parent1_results, 25, axis=0)

            fig.add_trace(
                go.Scatter(x=years, y=parent1_median, mode='lines', name=f'{st.session_state.parent1_name} Median',
                           line=dict(color='blue', width=3)), row=1, col=1)
            fig.add_trace(
                go.Scatter(x=years, y=parent1_75th, mode='lines', name=f'{st.session_state.parent1_name} 75th',
                           line=dict(color='lightblue', width=1)), row=1, col=1)
            fig.add_trace(
                go.Scatter(x=years, y=parent1_25th, mode='lines', name=f'{st.session_state.parent1_name} 25th',
                           line=dict(color='lightblue', width=1)), row=1, col=1)

            # Parent 2 Net Worth
            parent2_median = np.percentile(parent2_results, 50, axis=0)
            parent2_75th = np.percentile(parent2_results, 75, axis=0)
            parent2_25th = np.percentile(parent2_results, 25, axis=0)

            fig.add_trace(
                go.Scatter(x=years, y=parent2_median, mode='lines', name=f'{st.session_state.parent2_name} Median',
                           line=dict(color='green', width=3)), row=1, col=2)
            fig.add_trace(
                go.Scatter(x=years, y=parent2_75th, mode='lines', name=f'{st.session_state.parent2_name} 75th',
                           line=dict(color='lightgreen', width=1)), row=1, col=2)
            fig.add_trace(
                go.Scatter(x=years, y=parent2_25th, mode='lines', name=f'{st.session_state.parent2_name} 25th',
                           line=dict(color='lightgreen', width=1)), row=1, col=2)

            # Family Net Worth
            family_median = np.percentile(family_results, 50, axis=0)
            family_75th = np.percentile(family_results, 75, axis=0)
            family_25th = np.percentile(family_results, 25, axis=0)

            fig.add_trace(go.Scatter(x=years, y=family_median, mode='lines', name='Family Median',
                                     line=dict(color='purple', width=3)), row=2, col=1)
            fig.add_trace(go.Scatter(x=years, y=family_75th, mode='lines', name='Family 75th',
                                     line=dict(color='plum', width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=years, y=family_25th, mode='lines', name='Family 25th',
                                     line=dict(color='plum', width=1)), row=2, col=1)

            # Total Net Worth
            total_median = np.percentile(total_results, 50, axis=0)
            total_75th = np.percentile(total_results, 75, axis=0)
            total_25th = np.percentile(total_results, 25, axis=0)

            fig.add_trace(go.Scatter(x=years, y=total_median, mode='lines', name='Total Median',
                                     line=dict(color='red', width=3)), row=2, col=2)
            fig.add_trace(go.Scatter(x=years, y=total_75th, mode='lines', name='Total 75th',
                                     line=dict(color='pink', width=1)), row=2, col=2)
            fig.add_trace(go.Scatter(x=years, y=total_25th, mode='lines', name='Total 25th',
                                     line=dict(color='pink', width=1)), row=2, col=2)

            fig.update_layout(
                title=f'Net Worth Breakdown by Owner ({dollar_type})',
                height=800,
                showlegend=False
            )

            # Add zero lines to all subplots
            for row in [1, 2]:
                for col in [1, 2]:
                    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=row, col=col)

            st.plotly_chart(fig, use_container_width=True)

            # Summary table for final year by owner
            st.subheader("📊 Final Year Net Worth Summary by Owner")

            final_parent1 = parent1_results[:, -1]
            final_parent2 = parent2_results[:, -1]
            final_family = family_results[:, -1]

            summary_data = {
                "Owner": [st.session_state.parent1_name, st.session_state.parent2_name, "Family/Shared", "Total"],
                "Median": [
                    format_currency(np.median(final_parent1), show_thousands=True),
                    format_currency(np.median(final_parent2), show_thousands=True),
                    format_currency(np.median(final_family), show_thousands=True),
                    format_currency(np.median(final_year_results), show_thousands=True)
                ],
                "25th Percentile": [
                    format_currency(np.percentile(final_parent1, 25), show_thousands=True),
                    format_currency(np.percentile(final_parent2, 25), show_thousands=True),
                    format_currency(np.percentile(final_family, 25), show_thousands=True),
                    format_currency(np.percentile(final_year_results, 25), show_thousands=True)
                ],
                "75th Percentile": [
                    format_currency(np.percentile(final_parent1, 75), show_thousands=True),
                    format_currency(np.percentile(final_parent2, 75), show_thousands=True),
                    format_currency(np.percentile(final_family, 75), show_thousands=True),
                    format_currency(np.percentile(final_year_results, 75), show_thousands=True)
                ]
            }

            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

        with yearly_tab:
            st.subheader("📅 Annual Expense Breakdown (Median Values)")

            yearly_data = st.session_state.yearly_breakdown
            df = pd.DataFrame(yearly_data)

            value_description = "today's purchasing power" if last_normalization else "nominal future values"
            st.info(
                f"💡 **These values represent the 50th percentile (median) across all simulation runs in {value_description}.**")

            # Create stacked bar chart
            fig = go.Figure()

            fig.add_trace(
                go.Bar(x=df['Year'], y=df['Family Expenses'], name='Family Expenses', marker_color='lightblue'))
            fig.add_trace(
                go.Bar(x=df['Year'], y=df['Children Expenses'], name='Children Expenses', marker_color='lightgreen'))
            fig.add_trace(go.Bar(x=df['Year'], y=df['House Expenses'], name='House Expenses', marker_color='orange'))
            fig.add_trace(go.Bar(x=df['Year'], y=df['Major Purchases'], name='Major Purchases', marker_color='red'))
            fig.add_trace(
                go.Bar(x=df['Year'], y=df['Recurring Expenses'], name='Recurring Expenses', marker_color='purple'))

            fig.update_layout(
                barmode='stack',
                title=f'Annual Expenses Breakdown - Median Values ({st.session_state.mc_start_year}-{st.session_state.mc_start_year + st.session_state.mc_years - 1}) - {dollar_type}',
                xaxis_title='Year', yaxis_title=f'Annual Expenses ({dollar_type})', height=600,
                yaxis=dict(tickformat='$,.0f')
            )

            st.plotly_chart(fig, use_container_width=True)

            # Income vs Expenses chart
            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(x=df['Year'], y=df['Total Income'], mode='lines+markers',
                                      name='Total Income', line=dict(color='green', width=3)))
            fig2.add_trace(go.Scatter(x=df['Year'], y=df['Total Expenses'], mode='lines+markers',
                                      name='Total Expenses', line=dict(color='red', width=3)))
            fig2.add_trace(go.Scatter(x=df['Year'], y=df['After-Tax Income'], mode='lines+markers',
                                      name='After-Tax Income', line=dict(color='blue', width=2)))

            if 'Taxes' in df.columns:
                fig2.add_trace(go.Scatter(x=df['Year'], y=df['Taxes'], mode='lines+markers',
                                          name='Annual Taxes', line=dict(color='orange', width=2)))

            fig2.update_layout(
                title=f'Income vs Expenses Over Time (Median Values - {dollar_type})',
                xaxis_title='Year', yaxis_title=f'Amount ({dollar_type})', height=500,
                yaxis=dict(tickformat='$,.0f')
            )

            st.plotly_chart(fig2, use_container_width=True)

            # Key insights
            st.subheader("🔍 Key Expense Insights")
            col1, col2, col3 = st.columns(3)

            with col1:
                peak_year = df.loc[df['Total Expenses'].idxmax()]
                st.metric("Peak Expense Year", f"{int(peak_year['Year'])}")
                st.metric("Peak Year Amount", format_currency(peak_year['Total Expenses'], show_thousands=True))

            with col2:
                avg_expenses = df['Total Expenses'].mean()
                st.metric("Average Annual Expenses", format_currency(avg_expenses, show_thousands=True))
                total_over_period = df['Total Expenses'].sum()
                st.metric(f"Total Over {st.session_state.mc_years} Years",
                          format_currency(total_over_period, show_thousands=True))

            with col3:
                # Major purchase years
                major_purchase_years = df[df['Major Purchases'] > 0]['Year'].tolist()
                if major_purchase_years:
                    st.write("**Major Purchase Years:**")
                    for year in major_purchase_years[:5]:
                        amount = df[df['Year'] == year]['Major Purchases'].iloc[0]
                        st.write(f"• {int(year)}: {format_currency(amount, show_thousands=True)}")

        with breakdown_tab:
            st.subheader("📋 Detailed Financial Breakdown by Year (Median Values)")

            value_description = "today's purchasing power" if last_normalization else "nominal future values"
            st.info(
                f"💡 **These values represent the 50th percentile (median) across all simulation runs in {value_description}.**")

            # Format the detailed breakdown for display
            display_df = pd.DataFrame(st.session_state.yearly_breakdown)

            # Format currency columns
            currency_columns = ['Gross Income', 'Taxes', 'After-Tax Income', 'Rental Income', 'Total Income',
                                'Family Expenses', 'Children Expenses', 'House Expenses',
                                'Major Purchases', 'Recurring Expenses', 'Total Expenses', 'Net Income',
                                'Investment Return', 'Net Worth', 'Parent1 Net Worth', 'Parent2 Net Worth',
                                'Family Net Worth']

            for col in currency_columns:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x, show_thousands=True))

            st.dataframe(display_df, use_container_width=True, height=600)

            # Export breakdown
            csv_breakdown = display_df.to_csv(index=False)
            filename_suffix = "historical_median" if last_sim_type == "Historical" else "traditional_median"
            dollar_suffix = "today_dollars" if last_normalization else "future_dollars"
            st.download_button(
                label="📤 Export Detailed Breakdown to CSV",
                data=csv_breakdown,
                file_name=f"financial_breakdown_{filename_suffix}_{dollar_suffix}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


def save_data():
    """Save all session state data to JSON"""
    try:
        # Prepare data for saving
        data_to_save = {
            'app_version': '3.0',  # Updated version tracking
            'current_year': st.session_state.current_year,
            'marriage_year': st.session_state.marriage_year,
            'parent_settings': {
                'parent1_name': st.session_state.parent1_name,
                'parent1_emoji': st.session_state.parent1_emoji,
                'parent2_name': st.session_state.parent2_name,
                'parent2_emoji': st.session_state.parent2_emoji
            },
            'parentX': {
                'age': st.session_state.parentX_age,
                'net_worth': st.session_state.parentX_net_worth,
                'income': st.session_state.parentX_income,
                'raise': st.session_state.parentX_raise,
                'retirement_age': st.session_state.parentX_retirement_age,
                'ss_benefit': st.session_state.parentX_ss_benefit,
                'job_changes': st.session_state.parentX_job_changes.to_dict('records')
            },
            'parentY': {
                'age': st.session_state.parentY_age,
                'net_worth': st.session_state.parentY_net_worth,
                'income': st.session_state.parentY_income,
                'raise': st.session_state.parentY_raise,
                'retirement_age': st.session_state.parentY_retirement_age,
                'ss_benefit': st.session_state.parentY_ss_benefit,
                'job_changes': st.session_state.parentY_job_changes.to_dict('records')
            },
            'expense_categories': st.session_state.expense_categories,
            'expenses': st.session_state.expenses,
            'children_expenses': st.session_state.children_expenses.to_dict('records'),
            'children_list': st.session_state.children_list,
            'children_today_dollars': st.session_state.children_today_dollars,
            'active_scenario': st.session_state.active_scenario,
            'major_purchases': [asdict(purchase) for purchase in st.session_state.major_purchases],
            'recurring_expenses': [asdict(expense) for expense in st.session_state.recurring_expenses],
            'economic_scenarios': {name: asdict(scenario) for name, scenario in
                                   st.session_state.economic_scenarios.items()},
            'houses': [asdict(house) for house in st.session_state.houses],
            'tax_settings': {
                'state_tax_rate': st.session_state.state_tax_rate,
                'pretax_401k': st.session_state.pretax_401k
            },
            'social_security': {
                'insolvency_enabled': st.session_state.ss_insolvency_enabled,
                'shortfall_percentage': st.session_state.ss_shortfall_percentage
            },
            'monte_carlo': {
                'start_year': st.session_state.mc_start_year,
                'years': st.session_state.mc_years,
                'simulations': st.session_state.mc_simulations,
                'income_variability': st.session_state.mc_income_variability,
                'expense_variability': st.session_state.mc_expense_variability,
                'return_variability': st.session_state.mc_return_variability,
                'income_variability_positive': st.session_state.mc_income_variability_positive,
                'income_variability_negative': st.session_state.mc_income_variability_negative,
                'expense_variability_positive': st.session_state.mc_expense_variability_positive,
                'expense_variability_negative': st.session_state.mc_expense_variability_negative,
                'return_variability_positive': st.session_state.mc_return_variability_positive,
                'return_variability_negative': st.session_state.mc_return_variability_negative,
                'use_historical': st.session_state.mc_use_historical,
                'historical_start_year': st.session_state.mc_historical_start_year,
                'show_historical_stats': st.session_state.mc_show_historical_stats,
                'normalize_to_today_dollars': st.session_state.mc_normalize_to_today_dollars
            },
            'saved_date': datetime.now().isoformat()
        }

        # Convert to JSON
        json_data = json.dumps(data_to_save, indent=2)
        return json_data

    except Exception as e:
        st.error(f"Error preparing data for save: {str(e)}")
        return None


def load_data(json_data):
    """Load data from JSON into session state"""
    try:
        data = json.loads(json_data)

        # Load version-specific settings
        if 'current_year' in data:
            st.session_state.current_year = data['current_year']

        if 'marriage_year' in data:
            st.session_state.marriage_year = data['marriage_year']

        # Load parent settings
        if 'parent_settings' in data:
            settings = data['parent_settings']
            st.session_state.parent1_name = settings.get('parent1_name', 'Filipp')
            st.session_state.parent1_emoji = settings.get('parent1_emoji', '👨')
            st.session_state.parent2_name = settings.get('parent2_name', 'Erin')
            st.session_state.parent2_emoji = settings.get('parent2_emoji', '👩')

        # Load expense categories
        if 'expense_categories' in data:
            st.session_state.expense_categories = data['expense_categories']

        # Load parent data
        if 'parentX' in data:
            parentX = data['parentX']
            st.session_state.parentX_age = parentX['age']
            st.session_state.parentX_net_worth = parentX['net_worth']
            st.session_state.parentX_income = parentX['income']
            st.session_state.parentX_raise = parentX['raise']
            st.session_state.parentX_retirement_age = parentX.get('retirement_age', 65)
            st.session_state.parentX_ss_benefit = parentX.get('ss_benefit', 2500.0)
            st.session_state.parentX_job_changes = pd.DataFrame(parentX['job_changes'])

        if 'parentY' in data:
            parentY = data['parentY']
            st.session_state.parentY_age = parentY['age']
            st.session_state.parentY_net_worth = parentY['net_worth']
            st.session_state.parentY_income = parentY['income']
            st.session_state.parentY_raise = parentY['raise']
            st.session_state.parentY_retirement_age = parentY.get('retirement_age', 65)
            st.session_state.parentY_ss_benefit = parentY.get('ss_benefit', 2200.0)
            st.session_state.parentY_job_changes = pd.DataFrame(parentY['job_changes'])

        # Load other data
        if 'expenses' in data:
            st.session_state.expenses = data['expenses']

        if 'children_expenses' in data:
            st.session_state.children_expenses = pd.DataFrame(data['children_expenses'])

        if 'children_list' in data:
            st.session_state.children_list = data['children_list']

        if 'children_today_dollars' in data:
            st.session_state.children_today_dollars = data['children_today_dollars']

        if 'active_scenario' in data:
            st.session_state.active_scenario = data['active_scenario']

        if 'major_purchases' in data:
            st.session_state.major_purchases = []
            for purchase_data in data['major_purchases']:
                purchase = MajorPurchase(**purchase_data)
                st.session_state.major_purchases.append(purchase)

        if 'recurring_expenses' in data:
            st.session_state.recurring_expenses = []
            for expense_data in data['recurring_expenses']:
                expense = RecurringExpense(**expense_data)
                st.session_state.recurring_expenses.append(expense)

        if 'economic_scenarios' in data:
            st.session_state.economic_scenarios = {}
            for name, scenario_data in data['economic_scenarios'].items():
                scenario = EconomicScenario(**scenario_data)
                st.session_state.economic_scenarios[name] = scenario

        if 'houses' in data:
            st.session_state.houses = []
            for house_data in data['houses']:
                # Handle timeline conversion for backward compatibility
                if 'timeline' in house_data:
                    timeline = []
                    for entry_data in house_data['timeline']:
                        timeline.append(HouseTimelineEntry(**entry_data))
                    house_data['timeline'] = timeline
                else:
                    # Convert old format to new timeline format
                    status = house_data.get('status', 'Own_Live')
                    rental_income = house_data.get('rental_income', 0.0)
                    purchase_year = house_data.get('purchase_year', 2020)

                    # Convert old status to new format
                    if status == "Own":
                        new_status = "Own_Live"
                    elif status == "Rent":
                        new_status = "Own_Rent"
                    else:
                        new_status = status

                    house_data['timeline'] = [HouseTimelineEntry(purchase_year, new_status, rental_income)]

                    # Remove old fields
                    house_data.pop('status', None)
                    house_data.pop('rental_income', None)
                    house_data.pop('sell_year', None)

                # Ensure owner field exists (backward compatibility)
                if 'owner' not in house_data:
                    house_data['owner'] = "Shared"

                house = House(**house_data)
                st.session_state.houses.append(house)

        # Load tax settings
        if 'tax_settings' in data:
            tax_settings = data['tax_settings']
            st.session_state.state_tax_rate = tax_settings.get('state_tax_rate', 0.0)
            st.session_state.pretax_401k = tax_settings.get('pretax_401k', 0.0)

        # Load Social Security settings
        if 'social_security' in data:
            ss_settings = data['social_security']
            st.session_state.ss_insolvency_enabled = ss_settings.get('insolvency_enabled', True)
            st.session_state.ss_shortfall_percentage = ss_settings.get('shortfall_percentage', 30.0)

        # Load Monte Carlo settings (including new asymmetric and normalization settings)
        if 'monte_carlo' in data:
            mc = data['monte_carlo']
            st.session_state.mc_start_year = mc.get('start_year', 2025)
            st.session_state.mc_years = mc.get('years', 30)
            st.session_state.mc_simulations = mc.get('simulations', 1000)
            st.session_state.mc_income_variability = mc.get('income_variability', 10.0)
            st.session_state.mc_expense_variability = mc.get('expense_variability', 5.0)
            st.session_state.mc_return_variability = mc.get('return_variability', 15.0)
            st.session_state.mc_income_variability_positive = mc.get('income_variability_positive', 10.0)
            st.session_state.mc_income_variability_negative = mc.get('income_variability_negative', 10.0)
            st.session_state.mc_expense_variability_positive = mc.get('expense_variability_positive', 5.0)
            st.session_state.mc_expense_variability_negative = mc.get('expense_variability_negative', 5.0)
            st.session_state.mc_return_variability_positive = mc.get('return_variability_positive', 15.0)
            st.session_state.mc_return_variability_negative = mc.get('return_variability_negative', 15.0)
            st.session_state.mc_use_historical = mc.get('use_historical', False)
            st.session_state.mc_historical_start_year = mc.get('historical_start_year', 1924)
            st.session_state.mc_show_historical_stats = mc.get('show_historical_stats', False)
            st.session_state.mc_normalize_to_today_dollars = mc.get('normalize_to_today_dollars', False)

        return True

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False


def save_load_tab():
    """Enhanced Save/Load tab with internal scenario management and household persistence"""
    st.header("💾 Save & Load Data")

    # Household persistence section
    if st.session_state.get('authenticated'):
        st.subheader("🏠 Household Cloud Storage")
        st.info(f"💡 Your household code: `{st.session_state.household_id}` — All household members share the same saved plan.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Plan to Household", type="primary", key="save_household_plan"):
                json_data = save_data()
                if json_data:
                    save_household_plan(st.session_state.household_id, json_data)
                    st.success("Plan saved to household! All members will see these changes.")

        with col2:
            if st.button("📂 Load Plan from Household", key="load_household_plan"):
                plan_data = load_household_plan(st.session_state.household_id)
                if plan_data:
                    if load_data(plan_data):
                        st.success("Plan loaded from household storage!")
                        st.rerun()
                else:
                    st.info("No saved plan found. Save your current plan first.")

        # Show last save info
        household_info = get_household_info(st.session_state.household_id)
        if household_info.get('last_saved'):
            st.caption(f"Last saved: {household_info['last_saved'][:19]} by {household_info.get('saved_by', 'unknown')}")

        st.markdown("---")

    # Internal scenario management
    st.subheader("📚 Internal Scenario Management")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Save Current Scenario**")
        scenario_name = st.text_input("Scenario Name", key="save_scenario_name",
                                      placeholder="e.g., 'Base Case', 'Optimistic', 'Conservative'")

        if st.button("💾 Save Scenario Internally", key="save_internal_scenario"):
            if scenario_name and scenario_name.strip():
                scenario_data = save_data()
                if scenario_data:
                    st.session_state.saved_scenarios[scenario_name.strip()] = scenario_data
                    st.success(f"Saved scenario: {scenario_name}")
                    st.rerun()
            else:
                st.error("Please enter a scenario name")

    with col2:
        st.write("**Load Saved Scenario**")
        if st.session_state.saved_scenarios:
            scenario_to_load = st.selectbox(
                "Select Scenario to Load",
                ["Select..."] + list(st.session_state.saved_scenarios.keys()),
                key="load_scenario_select"
            )

            col2_1, col2_2 = st.columns(2)
            with col2_1:
                if st.button("📂 Load Scenario", key="load_internal_scenario"):
                    if scenario_to_load != "Select...":
                        scenario_data = st.session_state.saved_scenarios[scenario_to_load]
                        if load_data(scenario_data):
                            st.success(f"Loaded scenario: {scenario_to_load}")
                            st.rerun()
                        else:
                            st.error("Failed to load scenario")

            with col2_2:
                if st.button("🗑️ Delete Scenario", key="delete_internal_scenario"):
                    if scenario_to_load != "Select...":
                        del st.session_state.saved_scenarios[scenario_to_load]
                        st.success(f"Deleted scenario: {scenario_to_load}")
                        st.rerun()
        else:
            st.info("No scenarios saved yet. Save your current configuration above.")

    # Show saved scenarios
    if st.session_state.saved_scenarios:
        st.write("**Saved Scenarios:**")
        for i, (name, _) in enumerate(st.session_state.saved_scenarios.items(), 1):
            st.write(f"{i}. {name}")

    st.markdown("---")

    # External file management
    st.subheader("📁 External File Management")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Export to File**")

        if st.button("Generate Export File", type="primary"):
            json_data = save_data()
            if json_data:
                st.success("Data prepared for download!")

                # Create download button
                st.download_button(
                    label="📥 Download Financial Plan",
                    data=json_data,
                    file_name=f"financial_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    with col2:
        st.write("**Import from File**")

        uploaded_file = st.file_uploader("Choose a JSON file to load", type=['json'])

        if uploaded_file is not None:
            try:
                json_data = uploaded_file.read().decode('utf-8')

                if st.button("📄 Load from File", type="secondary"):
                    if load_data(json_data):
                        st.success("Data loaded successfully from file!")
                        st.rerun()
                    else:
                        st.error("Failed to load data from file.")

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    # Quick actions
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Reset to Default", key="reset_to_default"):
            # Clear all session state and reinitialize (preserve auth + saved scenarios)
            auth_keys = {'authenticated', 'current_user', 'user_data', 'household_id'}
            for key in list(st.session_state.keys()):
                if key != 'saved_scenarios' and key not in auth_keys:
                    del st.session_state[key]
            initialize_session_state()
            st.success("Reset to default configuration!")
            st.rerun()

    with col2:
        if len(st.session_state.saved_scenarios) > 1:
            if st.button("📊 Compare Scenarios", key="compare_scenarios"):
                st.info(
                    "💡 Comparison feature: Run Monte Carlo analysis on different scenarios and compare results in separate browser tabs.")

    with col3:
        if st.session_state.saved_scenarios:
            if st.button("🗑️ Clear All Scenarios", key="clear_all_scenarios"):
                st.session_state.saved_scenarios = {}
                st.success("Cleared all saved scenarios!")
                st.rerun()


def user_management_tab():
    """User profile and household management tab"""
    st.header("👤 User & Household Management")

    if not st.session_state.get('authenticated'):
        st.warning("Please log in to access this tab.")
        return

    current_user = st.session_state.current_user
    user_data = st.session_state.user_data
    household_id = st.session_state.household_id

    # Current user info
    st.subheader("👤 Your Profile")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Username:** {current_user}")
        st.write(f"**Display Name:** {user_data['display_name']}")
        st.write(f"**Household Code:** `{household_id}`")

    with col2:
        # Household info
        household_info = get_household_info(household_id)
        household_name = household_info.get('household_name', 'My Household')
        st.write(f"**Household:** {household_name}")

        last_saved = household_info.get('last_saved', 'Never')
        saved_by = household_info.get('saved_by', 'N/A')
        if last_saved != 'Never':
            st.write(f"**Last Saved:** {last_saved[:19]}")
            st.write(f"**Saved By:** {saved_by}")

    # Household members
    st.subheader("👨‍👩‍👧‍👦 Household Members")
    members = get_household_members(household_id)

    if members:
        for member in members:
            icon = "🟢" if member['username'] == current_user else "👤"
            suffix = " (you)" if member['username'] == current_user else ""
            st.write(f"{icon} **{member['display_name']}** (@{member['username']}){suffix}")
    else:
        st.info("No other members found.")

    st.info(f"💡 **Share this household code with your partner:** `{household_id}`\n\n"
            f"They can use it when registering to join your household and share the same financial plan.")

    # Save/Load household plan
    st.subheader("💾 Household Plan")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Plan to Household", type="primary", key="save_to_household_user_tab"):
            json_data = save_data()
            if json_data:
                save_household_plan(household_id, json_data)
                st.success("Plan saved! All household members will see these changes when they log in.")

    with col2:
        if st.button("📂 Reload Plan from Household", key="reload_household_user_tab"):
            plan_data = load_household_plan(household_id)
            if plan_data:
                if load_data(plan_data):
                    st.success("Plan reloaded from household storage!")
                    st.rerun()
            else:
                st.info("No saved plan found for this household yet.")

    # Change password
    st.subheader("🔒 Change Password")
    with st.form("change_password_form"):
        current_pw = st.text_input("Current Password", type="password", key="current_pw")
        new_pw = st.text_input("New Password (min 4 characters)", type="password", key="new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_new_pw")
        submitted = st.form_submit_button("Update Password")

        if submitted:
            if not current_pw or not new_pw:
                st.error("Please fill in all fields")
            elif new_pw != confirm_pw:
                st.error("New passwords don't match")
            elif len(new_pw) < 4:
                st.error("Password must be at least 4 characters")
            else:
                success, _ = authenticate_user(current_user, current_pw)
                if success:
                    users = load_users()
                    password_hash, salt = hash_password(new_pw)
                    users[current_user]['password_hash'] = password_hash
                    users[current_user]['salt'] = salt
                    save_users(users)
                    st.success("Password updated!")
                else:
                    st.error("Current password is incorrect")

    # Logout
    st.subheader("🚪 Session")
    if st.button("🚪 Logout", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Main application function with enhanced sidebar and authentication"""

    # Initialize auth state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Check if any users exist - if not, allow setup
    ensure_data_dirs()

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        login_page()
        return

    # User is authenticated - proceed with app
    initialize_session_state()

    # Define current year for use throughout the function
    current_year = st.session_state.current_year

    # App title and description
    user_display = st.session_state.user_data.get('display_name', st.session_state.current_user)
    household_info = get_household_info(st.session_state.household_id)
    household_name = household_info.get('household_name', 'My Household')

    st.title("💰 Enhanced Financial Planning Suite V14")
    st.markdown(
        f"**{household_name}** — Logged in as **{user_display}** · "
        f"Comprehensive financial planning with user profiles, dynamic expense categories, house ownership tracking, asymmetric variability, and advanced analytics")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
        "⚙️ Settings",
        f"{st.session_state.parent1_emoji} {st.session_state.parent1_name}",
        f"{st.session_state.parent2_emoji} {st.session_state.parent2_name}",
        "💸 Family Expenses",
        "👶 Children",
        "🏠 House Portfolio",
        "📈 Economy",
        "🖼️ Retirement",
        "🗓️ Timeline",
        "📊 Analysis",
        "💾 Save/Load",
        "👤 Users"
    ])

    with tab1:
        parent_settings_tab()

    with tab2:
        parent_x_tab()

    with tab3:
        parent_y_tab()

    with tab4:
        family_expenses_tab()

    with tab5:
        children_tab()

    with tab6:
        house_tab()

    with tab7:
        economy_tab()

    with tab8:
        retirement_tab()

    with tab9:
        timeline_tab()

    with tab10:
        combined_simulation_tab()

    with tab11:
        save_load_tab()

    with tab12:
        user_management_tab()

    # Enhanced sidebar with real-time house ownership updates
    with st.sidebar:
        st.header("📊 Financial Dashboard")

        # User info and quick save
        if st.session_state.get('authenticated'):
            user_display = st.session_state.user_data.get('display_name', st.session_state.current_user)
            st.write(f"👤 **{user_display}**")
            col_save, col_logout = st.columns(2)
            with col_save:
                if st.button("💾 Save", key="sidebar_save", help="Save plan to household"):
                    json_data = save_data()
                    if json_data:
                        save_household_plan(st.session_state.household_id, json_data)
                        st.success("Saved!")
            with col_logout:
                if st.button("🚪 Logout", key="sidebar_logout"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            st.markdown("---")

        # Basic metrics
        total_income = st.session_state.parentX_income + st.session_state.parentY_income
        total_expenses = sum(st.session_state.expenses.values())

        # Calculate total monthly house payment for all houses
        total_monthly_house_payment = 0
        total_rental_income = 0

        # Calculate net worth by category and owner (FIXED to update in real-time)
        parent1_portfolio = st.session_state.parentX_net_worth
        parent2_portfolio = st.session_state.parentY_net_worth
        family_portfolio = 0.0

        parent1_real_estate = 0.0
        parent2_real_estate = 0.0
        family_real_estate = 0.0

        for house in st.session_state.houses:
            status, rental_income = house.get_status_for_year(current_year)

            if status in ["Own_Live", "Own_Rent"]:
                monthly_payment = calculate_monthly_house_payment(house)
                total_monthly_house_payment += monthly_payment

                # Add house equity by owner (REAL-TIME UPDATE)
                house_equity = max(0, house.current_value - house.mortgage_balance)
                if house.owner == "Parent1":
                    parent1_real_estate += house_equity
                elif house.owner == "Parent2":
                    parent2_real_estate += house_equity
                else:  # Shared
                    family_real_estate += house_equity

            if status == "Own_Rent":
                total_rental_income += rental_income

        annual_house_payment = total_monthly_house_payment * 12
        annual_rental_income = total_rental_income * 12

        # Calculate taxes
        gross_income = total_income + annual_rental_income
        tax_info = calculate_annual_taxes(
            gross_income,
            st.session_state.pretax_401k,
            st.session_state.state_tax_rate
        )

        after_tax_income = tax_info['after_tax_income']
        net_income = after_tax_income - total_expenses - annual_house_payment

        st.metric("Gross Annual Income", format_currency(gross_income, show_thousands=True))
        if annual_rental_income > 0:
            st.metric("Rental Income", format_currency(annual_rental_income))
        st.metric("Annual Taxes", format_currency(tax_info['total_tax'], show_thousands=True))
        st.metric("After-Tax Income", format_currency(after_tax_income, show_thousands=True))
        st.metric("Family Expenses", format_currency(total_expenses, show_thousands=True))
        st.metric("House Payments", format_currency(annual_house_payment, show_thousands=True))
        st.metric("Net Income", format_currency(net_income, show_thousands=True))

        st.markdown("---")

        # Enhanced Net Worth Breakdown (REAL-TIME UPDATES)
        st.write("**💰 Net Worth Breakdown**")

        total_parent1 = parent1_portfolio + parent1_real_estate
        total_parent2 = parent2_portfolio + parent2_real_estate
        total_family = family_portfolio + family_real_estate
        total_net_worth = total_parent1 + total_parent2 + total_family

        # Individual parent net worth
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"{st.session_state.parent1_name} Total", format_currency(total_parent1, show_thousands=True))
            if parent1_portfolio > 0:
                st.caption(f"Portfolio: {format_currency(parent1_portfolio, show_thousands=True)}")
            if parent1_real_estate > 0:
                st.caption(f"Real Estate: {format_currency(parent1_real_estate, show_thousands=True)}")

        with col2:
            st.metric(f"{st.session_state.parent2_name} Total", format_currency(total_parent2, show_thousands=True))
            if parent2_portfolio > 0:
                st.caption(f"Portfolio: {format_currency(parent2_portfolio, show_thousands=True)}")
            if parent2_real_estate > 0:
                st.caption(f"Real Estate: {format_currency(parent2_real_estate, show_thousands=True)}")

        # Family/shared net worth
        if total_family > 0:
            st.metric("Family/Shared Total", format_currency(total_family, show_thousands=True))
            if family_portfolio > 0:
                st.caption(f"Portfolio: {format_currency(family_portfolio, show_thousands=True)}")
            if family_real_estate > 0:
                st.caption(f"Real Estate: {format_currency(family_real_estate, show_thousands=True)}")

        # Total combined
        st.metric("**Total Net Worth**", format_currency(total_net_worth, show_thousands=True))

        st.markdown("---")

        # Parent summary with custom names
        st.write("**👨‍👩‍👧‍👦 Family Summary**")
        st.write(
            f"• {st.session_state.parent1_name}: Age {st.session_state.parentX_age}, retires at {st.session_state.parentX_retirement_age}")
        st.write(
            f"• {st.session_state.parent2_name}: Age {st.session_state.parentY_age}, retires at {st.session_state.parentY_retirement_age}")

        # Marriage info
        if st.session_state.marriage_year != "N/A":
            st.write(f"• Married: {st.session_state.marriage_year}")

        # Combined Social Security with insolvency adjustment
        base_combined_ss_annual = (st.session_state.parentX_ss_benefit + st.session_state.parentY_ss_benefit) * 12
        if st.session_state.ss_insolvency_enabled:
            adjusted_combined_ss_annual = base_combined_ss_annual * (1 - st.session_state.ss_shortfall_percentage / 100)
            st.write(f"• Base SS: {format_currency(base_combined_ss_annual)}/year")
            st.write(f"• Adjusted SS: {format_currency(adjusted_combined_ss_annual)}/year")
        else:
            st.write(f"• Combined SS: {format_currency(base_combined_ss_annual)}/year")

        st.markdown("---")

        # Planning summary
        st.write("**📋 Planning Summary**")

        # House status breakdown with current year
        own_live_count = 0
        own_rent_count = 0
        sell_count = 0

        for house in st.session_state.houses:
            status, _ = house.get_status_for_year(current_year)
            if status == "Own_Live":
                own_live_count += 1
            elif status == "Own_Rent":
                own_rent_count += 1
            elif status == "Sell":
                sell_count += 1

        st.write(f"• Houses: {len(st.session_state.houses)} total")
        if own_live_count > 0:
            st.write(f"  - Living in: {own_live_count}")
        if own_rent_count > 0:
            st.write(f"  - Renting out: {own_rent_count}")
        if sell_count > 0:
            st.write(f"  - Sold: {sell_count}")

        st.write(f"• Major purchases: {len(st.session_state.major_purchases)}")
        st.write(f"• Recurring expenses: {len(st.session_state.recurring_expenses)}")
        st.write(f"• Expense categories: {len(st.session_state.expense_categories)}")

        # Children expenses summary
        if st.session_state.children_list:
            total_current_children_expenses = 0

            for child in st.session_state.children_list:
                child_age = current_year - child['birth_year']
                if 0 <= child_age < len(st.session_state.children_expenses):
                    child_row = st.session_state.children_expenses.iloc[child_age]
                    child_annual_cost = sum(child_row[col] for col in child_row.index if col != 'Age')
                    total_current_children_expenses += child_annual_cost

            st.write(
                f"• Children: {len(st.session_state.children_list)} (current cost: {format_currency(total_current_children_expenses, show_thousands=True)})")
        else:
            st.write("• Children: 0")

        # Active economic scenario and simulation mode
        st.write(f"• Active scenario: {st.session_state.active_scenario}")
        scenario = st.session_state.economic_scenarios[st.session_state.active_scenario]
        st.write(f"• Inflation rate: {scenario.inflation_rate * 100:.1f}%")

        # Show simulation mode and dollar normalization
        simulation_mode = "Historical Performance" if st.session_state.mc_use_historical else "Traditional Monte Carlo"
        st.write(f"• Simulation mode: {simulation_mode}")
        if st.session_state.mc_normalize_to_today_dollars:
            st.write("• Display: Today's dollars")
        else:
            st.write("• Display: Future dollars")

        # Social Security insolvency status
        if st.session_state.ss_insolvency_enabled:
            st.write(f"• SS Insolvency: {st.session_state.ss_shortfall_percentage}% reduction")

        # Internal scenarios count
        scenario_count = len(st.session_state.saved_scenarios)
        st.write(f"• Saved scenarios: {scenario_count}")

        st.markdown("---")

        # Enhanced quick tips
        st.write("**💡 Quick Tips**")
        st.write("• Use family expense templates by state")
        st.write("• Prevent duplicate child names")
        st.write("• Track house ownership for net worth")
        st.write("• Set SS insolvency expectations")
        st.write("• Use asymmetric variability in traditional mode")
        st.write("• Normalize results to today's dollars")
        st.write("• Save multiple scenarios internally")

        # Tax summary if configured
        if st.session_state.state_tax_rate > 0 or st.session_state.pretax_401k > 0:
            st.markdown("---")
            st.write("**💼 Tax Configuration**")
            if st.session_state.state_tax_rate > 0:
                st.write(f"• State tax: {st.session_state.state_tax_rate * 100:.1f}%")
            if st.session_state.pretax_401k > 0:
                st.write(f"• 401(k): {format_currency(st.session_state.pretax_401k, show_thousands=True)}/year")


if __name__ == "__main__":
    main()