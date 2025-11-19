# FinancePlanApp - Multi-Generational Financial Planning Tool

A comprehensive web-based financial planning application that helps families plan their financial future across multiple generations with Monte Carlo simulations, portfolio tracking, and cost-of-living adjustments for 14 global locations.

## Features

- **Multi-Parent Planning**: Track finances for two parents with different retirement ages and Social Security benefits
- **Children Management**: Add unlimited children with age-based expense templates
- **Real Estate Tracking**: Monitor home values with custom appreciation rates over time
- **Portfolio Allocation**: Manage asset allocation across 7 asset classes with automatic validation
- **Economic Scenarios**: Model different market conditions using 100 years of historical S&P 500 data
- **Retirement Planning**: Include Social Security with insolvency modeling (30% reduction after 2034)
- **Timeline View**: Visualize your entire financial journey with state-based cost adjustments
- **Monte Carlo Simulations**: Run 1,000 simulations to understand outcome probabilities
- **Save/Load Scenarios**: Store and compare different planning scenarios
- **Global Cost-of-Living**: Support for 14 locations across 5 countries

### Key Features in v0.7 🎉
- **🏥 Healthcare & Insurance Planning**: Model Medicare, HSA accounts, long-term care insurance, and health insurance costs
- **💳 Comprehensive Debt Management**: Track student loans, credit cards, auto loans with payoff strategies (Avalanche/Snowball)
- **🎓 Education Funding**: 529 plan tracking, college cost projections, scholarship/grant management, and funding gap analysis
- **💼 Tax Optimization**: Roth conversions, QCD strategies, withdrawal sequencing, and tax-loss harvesting
- **📄 Report Export**: Generate professional Excel, CSV, or JSON reports of your complete financial plan

### Supported Locations

**United States**: California, Washington, Texas, New York, San Francisco, Los Angeles, Portland

**Canada**: Toronto, Vancouver

**France**: Paris, Toulouse

**Germany**: Berlin, Munich

**Australia**: Sydney, Melbourne, Brisbane

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Internet connection (for first-time setup)

### Installation & Running

#### **Mac/Linux Users**

1. **First-time setup** (only needed once):
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   Or simply double-click `setup.sh`

2. **Launch the application**:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   Or simply double-click `run.sh`

#### **Windows Users**

1. **First-time setup** (only needed once):
   - Double-click `setup.bat`
   - Or run from command prompt: `setup.bat`

2. **Launch the application**:
   - Double-click `run.bat`
   - Or run from command prompt: `run.bat`

The application will automatically open in your default web browser at `http://localhost:8501`

### Manual Installation (Alternative)

If you prefer to install manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run FinancialPlanner_v0_7.py
```

## How to Use

### 1. Parent Settings
- Navigate to the **Parent X** and **Parent Y** tabs
- Enter current ages, retirement ages, and life expectancies
- Set current retirement savings and contribution rates
- Configure Social Security benefits

### 2. Family Expenses
- Go to **Family Expenses** tab
- Select your location from 14 global options
- Choose spending strategy (Conservative, Average, High-end)
- Customize expense categories as needed

### 3. Add Children
- Visit the **👶 Children** tab
- Add each child with name and birth year
- Choose location-based expense templates
- Templates automatically adjust costs by age (0-30 years)

### 4. Real Estate
- Go to **🏠 House** tab
- Add your home with purchase details
- Set custom appreciation rates
- Track value over time in your portfolio

### 5. Portfolio Allocation
- Configure your investment mix in **💼 Portfolio Allocation**
- Seven asset classes: US Stocks, International Stocks, Bonds, REITs, Commodities, Cash, Crypto
- Must total 100% - automatic validation provided

### 6. Economy Settings
- Choose economic scenario in **📊 Economy** tab
- Options: Historical Average, Optimistic, Pessimistic, Recession, Boom, Custom
- View 100 years of historical S&P 500 data for context

### 7. Retirement Details
- Fine-tune retirement in **🏖️ Retirement** tab
- Social Security insolvency modeling included
- View detailed income/expense breakdowns by year

### 8. Timeline View
- See your entire plan in **📅 Timeline** tab
- Add multiple life stages with different locations
- Expenses automatically adjust based on location

### 9. Run Simulations
- Go to **🎲 Combined Simulation** tab
- Run Monte Carlo simulations (1,000 iterations)
- View probability distributions and statistics
- Analyze best-case, worst-case, and median scenarios
- See detailed year-by-year breakdown

### 10. Save Your Work
- Use **💾 Save/Load** tab to preserve scenarios
- Internal library stores all your plans
- Easy comparison between different scenarios

## Technical Details

### Dependencies

- **Streamlit** (≥1.28.0): Web application framework
- **Pandas** (≥2.0.0): Data manipulation and analysis
- **NumPy** (≥1.24.0): Numerical computing
- **Plotly** (≥5.17.0): Interactive visualizations
- **openpyxl** (≥3.1.0): Excel file export

### Data Models

The application uses Python dataclasses for structured data:
- `ParentData`: Parent information and retirement details
- `ChildData`: Child information and expense tracking
- `HouseData`: Real estate properties and appreciation
- `TimelineEvent`: Life stages with location-based costs

### Financial Calculations

- **Monte Carlo**: 1,000 simulations using historical volatility
- **Social Security**: Includes 30% reduction after 2034 insolvency date
- **Inflation**: All values can be viewed in real or nominal dollars
- **Asset Growth**: Separate modeling for stocks, bonds, and alternative assets
- **Expense Scaling**: Location-based cost-of-living adjustments

### Historical Data

Uses 100 years (1928-2024) of S&P 500 returns for realistic market modeling:
- Average annual return: ~11.87%
- Historical volatility: ~19.5%
- Accounts for both bull and bear markets

## File Structure

```
FinancePlanApp/
├── FinancialPlanner_v0_7.py             # Main application
├── requirements.txt                     # Python dependencies
├── setup.sh                             # Mac/Linux setup script
├── setup.bat                            # Windows setup script
├── run.sh                               # Mac/Linux launcher
├── run.bat                              # Windows launcher
├── README.md                            # This file
├── test_*.py                            # Test suites
└── .gitignore                           # Git ignore rules
```

## Troubleshooting

### Application won't start
- Ensure you ran the setup script first (`setup.sh` or `setup.bat`)
- Verify Python 3.8+ is installed: `python3 --version` or `python --version`
- Check that virtual environment was created (look for `venv/` folder)

### Port already in use
- If port 8501 is occupied, Streamlit will automatically try 8502, 8503, etc.
- Or specify a different port: `streamlit run FinancialPlanner_v0_7.py --server.port 8080`

### Dependencies won't install
- Ensure you have internet connection
- Try upgrading pip: `pip install --upgrade pip`
- Check Python version compatibility

### Browser doesn't open automatically
- Manually navigate to `http://localhost:8501`
- Check firewall settings if connection fails

## Version History

### v0.7 (Current)
- 🏥 Healthcare & Insurance Planning (Medicare, HSA, LTC)
- 💳 Comprehensive Debt Management (Student loans, credit cards, payoff strategies)
- 🎓 Education Funding (529 plans, college cost projections)
- 💼 Tax Optimization (Roth conversions, QCD, withdrawal sequencing)
- 📄 Report Export (Excel, CSV, JSON)
- 📅 Dynamic year detection (automatically detects current year)
- 💰 Inflation-adjusted children expenses with clear documentation
- 17 functional tabs with comprehensive feature set
- Enhanced safety checks and error handling
- Comprehensive test suite included
- Support for importing past scenarios with automatic year adjustment

### Earlier Versions
- Pre-v0.7: Legacy versioning system (V2-V16)
- Migrated from PyQt6 desktop to web-based Streamlit interface

## Contributing

This is a personal financial planning tool. Feel free to fork and customize for your own needs.

## License

Personal use only.

## Support

For issues or questions, please refer to the application's built-in help tooltips or check the code documentation.

---

**Built with ❤️ using Streamlit and Python**
