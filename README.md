# 💰 Financial Planning Suite V14

A comprehensive lifetime financial planning application built with Streamlit. Features Monte Carlo simulations, multi-user household profiles, and Docker deployment for self-hosting on a NAS.

## Features

- **Two-parent financial modeling** with income, raises, job changes, retirement, Social Security
- **Monte Carlo simulation** — Traditional (asymmetric variability) + Historical (100yr S&P 500 data)
- **House portfolio** — Multiple properties with Own/Rent/Sell timelines
- **Children expenses** — Age 0-30 with 11 categories and state-based templates
- **Multi-user auth** — Couples share a household code to collaborate on the same plan
- **Docker deployment** — Self-hosted on a NAS with optional HTTPS via Nginx Proxy Manager

## Quick Start (Local)

```bash
pip install streamlit pandas numpy plotly
streamlit run FinancialApp_V14.py
```

## Docker Deployment

```bash
docker-compose -f docker-compose-local.yml build
docker-compose -f docker-compose-local.yml up -d
# Open http://localhost:8501
```

## Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) — General NAS deployment
- [HTTPS_SETUP_GUIDE.md](HTTPS_SETUP_GUIDE.md) — HTTPS/SSL with Let's Encrypt
- [CLAUDE.md](CLAUDE.md) — Development guide for Claude Code
