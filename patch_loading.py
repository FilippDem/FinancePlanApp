#!/usr/bin/env python3
"""Patch Streamlit's index.html to replace the default loading animation.

Injects custom CSS that:
1. Replaces the initial boot skeleton/loading screen with a branded spinner
2. Hides the sports-themed running icons in the top-right rerun indicator
"""
import streamlit
import os

static_dir = os.path.join(os.path.dirname(streamlit.__file__), 'static')
index_path = os.path.join(static_dir, 'index.html')

CUSTOM_STYLES = """
<style>
  /* ── Custom loading screen ── */
  /* Replace Streamlit's default skeleton loading with a clean branded spinner */
  .stApp [data-testid="stAppViewBlockContainer"]:empty::before,
  #root:not(:has(.stApp))::after {
    content: "Loading...";
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    width: 100%;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 1.1rem;
    color: rgba(180, 180, 200, 0.6);
    letter-spacing: 0.05em;
  }

  /* Branded spinner on initial page load */
  #root:not(:has(.stApp)) {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: #0e1117;
  }
  #root:not(:has(.stApp))::before {
    content: "";
    width: 36px;
    height: 36px;
    border: 3px solid rgba(102, 126, 234, 0.2);
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 12px;
  }
  #root:not(:has(.stApp))::after {
    content: "Financial Planning Suite";
    height: auto;
    font-size: 1.2rem;
    color: rgba(200, 200, 220, 0.7);
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* ── Hide sports running icons in the rerun indicator ── */
  [data-testid="stStatusWidget"] svg {
    display: none !important;
  }
  [data-testid="stStatusWidget"]::before {
    content: "";
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #667eea;
    animation: pulse-dot 1s ease-in-out infinite;
    margin-right: 6px;
    vertical-align: middle;
  }
  @keyframes pulse-dot {
    0%, 100% { opacity: 0.3; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.2); }
  }
</style>
"""

with open(index_path, 'r') as f:
    html = f.read()

if 'Financial Planning Suite' not in html:
    # Inject before </head>
    html = html.replace('</head>', CUSTOM_STYLES + '\n</head>')
    with open(index_path, 'w') as f:
        f.write(html)
    print(f"Patched {index_path}")
else:
    print(f"Already patched: {index_path}")
