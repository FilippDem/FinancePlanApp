# 💰 Financial Planning Suite

A comprehensive lifetime financial planning repository with two applications:

## Applications

### 1. FinancialPlanner v0.7 - Desktop/Standalone Application

**Latest features:**
- **Custom Spending Templates**: Create and save custom expense templates per location
- **Location-Based Taxation**: Automatic tax calculations for 50+ US states and 40+ countries
- **Tax-Smart Planning**: Federal, state, FICA, and foreign tax calculations that adjust as you move
- **Sankey Flow Diagrams**: Visual money flow from income → taxes → expenses → savings
- **Investment Tracking**: Uses your configured expected return rate
- **Multi-Generational Planning**: Track finances across generations with Monte Carlo simulations

**Quick Start:**
```bash
# Mac/Linux
chmod +x setup.sh && ./setup.sh
chmod +x run.sh && ./run.sh

# Windows
setup.bat
run.bat
```

Or manually:
```bash
pip install streamlit pandas numpy plotly
streamlit run FinancialPlanner_v0_7.py
```

**Key Features:**
- Custom spending strategy templates with save/delete functionality
- Location-based tax calculations (adapts as you move between states/countries)
- Comprehensive tax tracking (Federal, State, FICA, Foreign)
- Split tabs: Deterministic Cashflow & Monte Carlo Simulation
- Sankey diagrams for money flow visualization
- Investment returns using user-configured rates
- 50+ US states with accurate tax rates (TX=0%, CA=13.3%, etc.)
- 40+ countries with effective tax rates worldwide
- Support for zero-tax locations (UAE, Monaco, Cayman Islands, etc.)

**Supported Tax Locations:**
- **US States**: All 50 states with accurate rates
- **Countries**: Canada, UK, Germany, France, Australia, Japan, Singapore, Hong Kong, Switzerland, Sweden, Norway, Denmark, and 25+ more

### 2. FinancialApp V14 - Multi-User Web Application with Docker

**Architecture:**
- Multi-user authentication with household profiles
- Docker deployment for NAS hosting
- Couples share financial plans via household codes
- Persistent storage (survives restarts)

**Quick Start:**
```bash
# Local deployment
docker-compose -f docker-compose-local.yml build
docker-compose -f docker-compose-local.yml up -d
# Open http://localhost:8501

# HTTPS deployment with Nginx Proxy Manager
docker-compose build
docker-compose up -d
```

**Features:**
- Two-parent financial modeling with income, raises, job changes
- Monte Carlo simulation (Traditional + Historical S&P 500 data)
- House portfolio with Own/Rent/Sell timelines
- Children expenses (age 0-30, 11 categories, state templates)
- Multi-user authentication with PBKDF2-SHA256 hashing
- Household profiles (shared financial plans)
- 12 tabs: Settings, Parent1, Parent2, Family, Children, Houses, Economy, Retirement, Timeline, Analysis, Save/Load, Users

## Common Features (Both Apps)

- **Monte Carlo Simulations**: 1,000+ iterations using historical volatility
- **Social Security**: Insolvency modeling with 30% reduction after 2034
- **Historical Data**: 100 years (1924-2024) of S&P 500 returns
- **Save/Load**: Store and compare different scenarios
- **Real Estate**: Multiple properties with appreciation tracking
- **State Templates**: Location-based cost-of-living adjustments

## File Structure

```
FinancePlanApp/
├── FinancialPlanner_v0_7.py             # Standalone app with custom templates & taxes
├── FinancialApp_V14.py                  # Multi-user Docker app
├── FinancialPlanner_v0_8.py             # Alternative version
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker build instructions
├── docker-compose.yml                   # HTTPS deployment
├── docker-compose-local.yml             # Local deployment
├── CLAUDE.md                            # Development guide
├── SETUP_GUIDE.md                       # NAS deployment guide
├── HTTPS_SETUP_GUIDE.md                 # SSL/HTTPS setup
├── dist_executable/                     # Executable build scripts
└── test_*.py                            # Test suites
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Development guide for Claude Code
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - NAS deployment instructions
- **[HTTPS_SETUP_GUIDE.md](HTTPS_SETUP_GUIDE.md)** - HTTPS/SSL setup
- **[dist_executable/README.md](dist_executable/README.md)** - Building executables

## Version History

### FinancialPlanner v0.7 (Latest)
- Custom spending strategy templates with create/delete
- Location-based tax calculations for 50+ US states and 40+ countries
- Tax calculations adapt as users move between locations
- Investment returns use user-configured rate
- Filipp's default net worth: $4.9M
- Split Analysis tab into Deterministic Cashflow and Monte Carlo Simulation
- Sankey diagrams for money flow visualization
- Comprehensive tax tracking (Federal, State, FICA, Foreign)

### FinancialApp V14
- Multi-user authentication with household profiles
- Docker deployment for NAS self-hosting
- Persistent file storage
- PBKDF2-SHA256 password hashing
- Users tab with profile management
- Sidebar quick save/logout buttons

## Technical Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly
- **Deployment**: Docker, Nginx Proxy Manager
- **Storage**: JSON files (V14), Session state (v0.7)
- **Authentication**: PBKDF2-SHA256 (V14)

## Troubleshooting

### Port already in use
- Streamlit auto-tries ports 8501, 8502, 8503...
- Or specify: `streamlit run <app>.py --server.port 8080`

### Dependencies won't install
- Upgrade pip: `pip install --upgrade pip`
- Check Python version: 3.8+ required

### Docker containers won't start
- Check logs: `docker-compose logs -f`
- Verify port availability: `docker ps`

## License

Personal use only.

---

**Built with ❤️ using Streamlit and Python**
