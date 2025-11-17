def setup_tax_burden_tab(self) -> QWidget:
    """Set up the tax burden visualization tab."""
    try:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scenario selection
        scenario_group = QGroupBox("Tax Projection Settings")
        scenario_layout = QFormLayout()

        self.tax_scenario_combo = QComboBox()
        self.tax_scenario_combo.addItems(list(self.planner.scenario_params.scenarios.keys()))

        scenario_layout.addRow("Scenario:", self.tax_scenario_combo)

        run_projection_button = QPushButton("Run Tax Projection")
        run_projection_button.clicked.connect(self.run_tax_projection)
        scenario_layout.addRow(run_projection_button)

        scenario_group.setLayout(scenario_layout)
        layout.addWidget(scenario_group)

        # Canvas for matplotlib figure
        self.tax_figure = Figure(figsize=(10, 6))
        self.tax_canvas = FigureCanvasQTAgg(self.tax_figure)
        layout.addWidget(self.tax_canvas)

        logger.debug("Tax burden tab setup complete")
        return tab
    except Exception as e:
        logger.error(f"Error in setup_tax_burden_tab: {e}")
        logger.error(traceback.format_exc())
        # Create a minimal fallback tab
        error_tab = QWidget()
        error_layout = QVBoxLayout(error_tab)
        error_label = QLabel(f"Error setting up Tax Burden tab: {str(e)}")
        error_layout.addWidget(error_label)
        return error_tab


def run_tax_projection(self):
    """Run tax projection and display results."""
    try:
        logger.debug("Starting tax projection")
        # Show wait cursor
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        scenario_name = self.tax_scenario_combo.currentText()
        results = self.planner.calculate_projection(scenario_name)

        # Clear the figure
        self.tax_figure.clear()

        # Create subplot
        ax = self.tax_figure.add_subplot(111)

        # Extract data
        years = [r['year'] for r in results]

        # Extract and calculate tax data
        tax_data = []
        income_data = []
        tax_rate_data = []

        for result in results:
            year_tax = 0
            year_gross_income = 0

            for person_name, income_info in result['income_details'].items():
                year_tax += income_info['tax']
                year_gross_income += income_info['gross']

            tax_data.append(year_tax)
            income_data.append(year_gross_income)

            # Calculate effective tax rate (if income > 0)
            if year_gross_income > 0:
                tax_rate_data.append((year_tax / year_gross_income) * 100)  # as percentage
            else:
                tax_rate_data.append(0)

        # Plot taxes as bars
        bar_width = 0.35
        bar1 = ax.bar(years, tax_data, bar_width, label='Total Tax')

        # Add a second y-axis for tax rate percentage
        ax2 = ax.twinx()
        line = ax2.plot(years, tax_rate_data, 'r-', label='Effective Tax Rate (%)')

        # Set up labels and formatting
        ax.set_xlabel('Year')
        ax.set_ylabel('Tax Amount ($)')
        ax2.set_ylabel('Effective Tax Rate (%)')

        # Format y-axis with dollar sign and commas
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'${x:,.0f}')
        )

        # Combine legends
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left')

        ax.set_title('Tax Burden Projection')
        ax.grid(True, alpha=0.3)

        self.tax_figure.tight_layout()
        self.tax_canvas.draw()

        # Restore normal cursor
        QApplication.restoreOverrideCursor()
        logger.debug("Tax projection completed and displayed")
    except Exception as e:
        QApplication.restoreOverrideCursor()
        logger.error(f"Error in tax projection: {e}")
        logger.error(traceback.format_exc())
        QMessageBox.warning(self, "Error", f"Failed to run tax projection: {str(e)}")


def update_partner(self, partner_id: str):
    """Update partner information in the planner."""
    try:
        name_attr = f"partner_{partner_id.lower()}_name_input"
        birth_attr = f"partner_{partner_id.lower()}_birth_year_input"
        income_attr = f"partner_{partner_id.lower()}_base_income_input"
        growth_attr = f"partner_{partner_id.lower()}_income_growth_input"
        retirement_attr = f"partner_{partner_id.lower()}_retirement_age_input"
        death_attr = f"partner_{partner_id.lower()}_death_age_input"
        filing_attr = f"partner_{partner_id.lower()}_filing_status_input"
        tax_attr = f"partner_{partner_id.lower()}_state_tax_input"
        net_worth_attr = f"partner_{partner_id.lower()}_net_worth_input"
        ss_age_attr = f"partner_{partner_id.lower()}_ss_age_input"
        ss_benefit_attr = f"partner_{partner_id.lower()}_ss_benefit_input"

        name = getattr(self, name_attr).text()
        birth_year = getattr(self, birth_attr).value()
        base_income = getattr(self, income_attr).value()
        income_growth = getattr(self, growth_attr).value()
        retirement_age = getattr(self, retirement_attr).value()
        death_age = getattr(self, death_attr).value()
        filing_status = getattr(self, filing_attr).currentText()
        state_tax = getattr(self, tax_attr).value()
        ss_age = getattr(self, ss_age_attr).value()
        ss_benefit = getattr(self, ss_benefit_attr).value()

        if not name:
            QMessageBox.warning(self, "Warning", f"Partner {partner_id} name is required")
            return

        # Create or update the person
        partner_person = None

        # Check if this partner already exists in persons
        for person in self.planner.persons:
            if person.name.startswith(f"Partner {partner_id}:"):
                partner_person = person
                break

        if partner_person:
            # Update existing person
            partner_person.name = f"Partner {partner_id}: {name}"
            partner_person.birth_year = birth_year
            partner_person.base_income = base_income
            partner_person.income_growth_rate = income_growth
            partner_person.retirement_age = retirement_age
            partner_person.death_age = death_age
            partner_person.filing_status = filing_status
            partner_person.state_tax_rate = state_tax
            partner_person.ss_benefit_age = ss_age
            partner_person.estimated_ss_benefit = ss_benefit
        else:
            # Create new person for this partner
            partner_person = Person(
                name=f"Partner {partner_id}: {name}",
                birth_year=birth_year,
                base_income=base_income,
                income_growth_rate=income_growth,
                retirement_age=retirement_age,
                death_age=death_age,
                filing_status=filing_status,
                state_tax_rate=state_tax,
                ss_benefit_age=ss_age,
                estimated_ss_benefit=ss_benefit
            )
            self.planner.persons.append(partner_person)

        # Update the net worth (combining both partners' net worth)
        partner_x_net_worth = 0
        partner_y_net_worth = 0

        if hasattr(self, "partner_x_net_worth_input"):
            partner_x_net_worth = self.partner_x_net_worth_input.value()

        if hasattr(self, "partner_y_net_worth_input"):
            partner_y_net_worth = self.partner_y_net_worth_input.value()

        self.planner.current_net_worth = partner_x_net_worth + partner_y_net_worth

        # Show success message
        QMessageBox.information(
            self,
            "Success",
            f"Partner {partner_id} information updated"
        )

        logger.debug(f"Updated Partner {partner_id}: {name}")

        # Refresh the tables
        self.refresh_partner_data(partner_id)

    except Exception as e:
        logger.error(f"Error updating partner {partner_id}: {e}")
        QMessageBox.warning(self, "Error", f"Failed to update partner: {str(e)}")


def add_partner_income_change(self, partner_id: str):
    """Add an income change for a partner."""
    try:
        year_attr = f"partner_{partner_id.lower()}_income_change_year_input"
        amount_attr = f"partner_{partner_id.lower()}_income_change_amount_input"

        year = getattr(self, year_attr).value()
        amount = getattr(self, amount_attr).value()

        # Find the partner person
        partner_person = None
        for person in self.planner.persons:
            if person.name.startswith(f"Partner {partner_id}:"):
                partner_person = person
                break

        if not partner_person:
            QMessageBox.warning(self, "Warning", f"Please update Partner {partner_id} first")
            return

        # Add the income change
        partner_person.income_changes[year] = amount

        # Update UI
        QMessageBox.information(
            self,
            "Success",
            f"Income change added for Partner {partner_id}: {format_currency(amount)} starting in {year}"
        )
        getattr(self, amount_attr).setValue(0)

        # Refresh the income changes table
        self.refresh_partner_income_changes(partner_id)

        logger.debug(f"Added income change for Partner {partner_id}, year: {year}, amount: ${amount}")
    except Exception as e:
        logger.error(f"Error adding income change for Partner {partner_id}: {e}")
        QMessageBox.warning(self, "Error", f"Failed to add income change: {str(e)}")


def delete_partner_income_change(self, partner_id: str, year: int):
    """Remove an income change for a partner."""
    try:
        # Find the partner person
        partner_person = None
        for person in self.planner.persons:
            if person.name.startswith(f"Partner {partner_id}:"):
                partner_person = person
                break

        if not partner_person or year not in partner_person.income_changes:
            return

        # Remove the income change
        del partner_person.income_changes[year]

        # Refresh the table
        self.refresh_partner_income_changes(partner_id)

        logger.debug(f"Deleted income change for Partner {partner_id}, year: {year}")
    except Exception as e:
        logger.error(f"Error deleting income change for Partner {partner_id}: {e}")


def refresh_partner_data(self, partner_id: str):
    """Refresh the partner UI with data from the planner."""
    try:
        # Make sure all the required attributes exist
        name_attr = f"partner_{partner_id.lower()}_name_input"
        birth_attr = f"partner_{partner_id.lower()}_birth_year_input"
        income_attr = f"partner_{partner_id.lower()}_base_income_input"
        growth_attr = f"partner_{partner_id.lower()}_income_growth_input"
        retirement_attr = f"partner_{partner_id.lower()}_retirement_age_input"
        death_attr = f"partner_{partner_id.lower()}_death_age_input"
        filing_attr = f"partner_{partner_id.lower()}_filing_status_input"
        tax_attr = f"partner_{partner_id.lower()}_state_tax_input"
        ss_age_attr = f"partner_{partner_id.lower()}_ss_age_input"
        ss_benefit_attr = f"partner_{partner_id.lower()}_ss_benefit_input"

        # Check if all attributes exist before continuing
        required_attrs = [name_attr, birth_attr, income_attr, growth_attr,
                          retirement_attr, death_attr, filing_attr, tax_attr,
                          ss_age_attr, ss_benefit_attr]

        if not all(hasattr(self, attr) for attr in required_attrs):
            logger.warning(f"Some partner {partner_id} UI elements are not yet initialized")
            return

        # Find the partner person
        partner_person = None
        for person in self.planner.persons:
            if person.name.startswith(f"Partner {partner_id}:"):
                partner_person = person
                break

        if partner_person:
            # Parse the name (after "Partner X: ")
            name = partner_person.name.split(": ", 1)[1] if ": " in partner_person.name else ""

            # Update the UI fields
            getattr(self, name_attr).setText(name)
            getattr(self, birth_attr).setValue(partner_person.birth_year)
            getattr(self, income_attr).setValue(partner_person.base_income)
            getattr(self, growth_attr).setValue(partner_person.income_growth_rate)
            getattr(self, retirement_attr).setValue(partner_person.retirement_age)
            getattr(self, death_attr).setValue(partner_person.death_age)
            getattr(self, ss_age_attr).setValue(partner_person.ss_benefit_age)
            getattr(self, ss_benefit_attr).setValue(partner_person.estimated_ss_benefit)

            # Set combo box index by text
            index = getattr(self, filing_attr).findText(partner_person.filing_status)
            if index >= 0:
                getattr(self, filing_attr).setCurrentIndex(index)

            getattr(self, tax_attr).setValue(partner_person.state_tax_rate)

            # Refresh income changes table
            self.refresh_partner_income_changes(partner_id)
    except Exception as e:
        logger.error(f"Error refreshing Partner {partner_id} data: {e}")


def refresh_partner_income_changes(self, partner_id: str):
    """Refresh the income changes table for a partner."""
    try:
        table_attr = f"partner_{partner_id.lower()}_income_changes_table"

        # Make sure the table exists
        if not hasattr(self, table_attr):
            logger.warning(f"Partner {partner_id} income changes table not initialized")
            return

        # Clear the table
        getattr(self, table_attr).setRowCount(0)

        # Find the partner person
        partner_person = None
        for person in self.planner.persons:
            if person.name.startswith(f"Partner {partner_id}:"):
                partner_person = person
                break

        if not partner_person:
            return

        # Populate the table with income changes
        for year, amount in sorted(partner_person.income_changes.items()):
            row = getattr(self, table_attr).rowCount()
            getattr(self, table_attr).insertRow(row)

            getattr(self, table_attr).setItem(row, 0, QTableWidgetItem(str(year)))
            getattr(self, table_attr).setItem(row, 1, QTableWidgetItem(format_currency(amount)))

            # Add delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, y=year: self.delete_partner_income_change(partner_id, y))
            getattr(self, table_attr).setCellWidget(row, 2, delete_btn)

    except Exception as e:
        logger.error(f"Error refreshing income changes for Partner {partner_id}: {e}")


import sys
import traceback
import logging
import gc  # For garbage collection
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import date
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.ticker
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QFormLayout, QSpinBox, QDoubleSpinBox, QScrollArea,
    QFileDialog, QDateEdit, QDialog, QCheckBox, QListWidget
)
from PyQt6.QtCore import Qt, QDate
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("financial_planner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinancialPlanner")


# Utility function for formatting dollar amounts
def format_currency(amount: float, show_cents: bool = False) -> str:
    """
    Format dollar amounts without cents and with thousands notation for large values.

    Args:
        amount: The dollar amount to format
        show_cents: If True, show cents (for rates/percentages only)

    Returns:
        Formatted string like "$1.2M", "$450K", or "$1,234"
    """
    if abs(amount) >= 1_000_000:
        # Format in millions
        return f"${amount / 1_000_000:.1f}M"
    elif abs(amount) >= 100_000:
        # Format in thousands for values >= 100K
        return f"${amount / 1_000:.0f}K"
    else:
        # Format with commas, no cents for values < 100K
        if show_cents:
            return f"${amount:,.2f}"
        else:
            return f"${amount:,.0f}"


@dataclass
class TaxBracket:
    min_income: float
    max_income: Optional[float]
    rate: float


@dataclass
class Person:
    name: str
    birth_year: int
    base_income: float
    income_growth_rate: float
    retirement_age: int
    filing_status: str = 'single'
    state_tax_rate: float = 0.0
    income_changes: Dict[int, float] = None
    death_age: int = 100  # Maximum age set to 100
    ss_benefit_age: int = 67  # Age when Social Security benefits start
    estimated_ss_benefit: float = 0.0  # Annual estimated Social Security benefit

    def __post_init__(self):
        if self.income_changes is None:
            self.income_changes = {}

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class ChildTemplate:
    name: str
    yearly_expenses: Dict[int, Dict[str, float]]  # Age -> {Category -> Expense} mapping
    education_fund_target: float = 0.0
    education_start_age: int = 18
    education_duration: int = 4
    daycare_start_age: int = 0  # Default to start at birth
    daycare_end_age: int = 5  # Default to end at kindergarten age
    daycare_monthly_cost: float = 0.0
    daycare_cost_location: str = "Custom"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def get_default_expenses():
        """Get default expense values for Washington state"""
        # Create dictionary with default values for all ages 0-25
        default_expenses = {}

        # Default expense categories for each age
        categories = [
            "Food",
            "Clothing",
            "Healthcare",
            "Activities/Sports",
            "Entertainment",
            "Transportation",
            "School Supplies",
            "Gifts/Celebrations",
            "Miscellaneous",
            "Daycare/Childcare",
            "Education"
        ]

        # Initialize with zeros for all ages and categories
        for age in range(26):  # 0-25 years
            default_expenses[age] = {category: 0.0 for category in categories}

        # Food - increases with age
        for age in range(26):
            if age < 2:
                default_expenses[age]["Food"] = 1500  # Higher for infants (formula, baby food)
            elif age < 5:
                default_expenses[age]["Food"] = 1800  # Toddlers
            elif age < 12:
                default_expenses[age]["Food"] = 2400  # Children
            elif age < 19:
                default_expenses[age]["Food"] = 3000  # Teenagers
            else:
                default_expenses[age]["Food"] = 3500  # Young adults

        # Clothing - increases with age and spikes during growth years
        for age in range(26):
            if age < 2:
                default_expenses[age]["Clothing"] = 600  # Infants need many sizes
            elif age < 5:
                default_expenses[age]["Clothing"] = 500  # Toddlers
            elif age < 12:
                default_expenses[age]["Clothing"] = 600  # Children
            elif age < 19:
                default_expenses[age]["Clothing"] = 900  # Teenagers (brand conscious)
            else:
                default_expenses[age]["Clothing"] = 1000  # Young adults

        # Healthcare - includes co-pays, medications, etc.
        for age in range(26):
            if age < 1:
                default_expenses[age]["Healthcare"] = 800  # More doctor visits for infants
            elif age < 5:
                default_expenses[age]["Healthcare"] = 500  # Toddlers
            elif age < 19:
                default_expenses[age]["Healthcare"] = 400  # Children
            else:
                default_expenses[age]["Healthcare"] = 800  # Young adults (may need own insurance)

        # Activities/Sports - increases with age
        for age in range(26):
            if age < 3:
                default_expenses[age]["Activities/Sports"] = 100  # Minimal for babies
            elif age < 6:
                default_expenses[age]["Activities/Sports"] = 300  # Preschool activities
            elif age < 12:
                default_expenses[age]["Activities/Sports"] = 800  # Elementary school sports/activities
            elif age < 19:
                default_expenses[age]["Activities/Sports"] = 1500  # Teen sports can be expensive
            else:
                default_expenses[age]["Activities/Sports"] = 800  # Young adults (less parent-funded)

        # Entertainment - increases slightly with age
        for age in range(26):
            if age < 3:
                default_expenses[age]["Entertainment"] = 200
            elif age < 12:
                default_expenses[age]["Entertainment"] = 300
            elif age < 19:
                default_expenses[age]["Entertainment"] = 500
            else:
                default_expenses[age]["Entertainment"] = 400  # Young adults (less parent-funded)

        # Transportation - increases significantly for teens
        for age in range(26):
            if age < 13:
                default_expenses[age]["Transportation"] = 200
            elif age < 16:
                default_expenses[age]["Transportation"] = 300
            elif age < 21:
                default_expenses[age]["Transportation"] = 1000  # Driving age - insurance, gas, etc.
            else:
                default_expenses[age]["Transportation"] = 500  # Young adults (less parent-funded)

        # School Supplies - varies by school age
        for age in range(26):
            if age < 5:
                default_expenses[age]["School Supplies"] = 50
            elif age < 13:
                default_expenses[age]["School Supplies"] = 200
            elif age < 19:
                default_expenses[age]["School Supplies"] = 300
            else:
                default_expenses[age]["School Supplies"] = 400  # College supplies

        # Gifts/Celebrations - birthdays, holidays, etc.
        for age in range(26):
            if age < 19:
                default_expenses[age]["Gifts/Celebrations"] = 300
            else:
                default_expenses[age]["Gifts/Celebrations"] = 200  # Less parent-funded

        # Miscellaneous - catch-all for other expenses
        for age in range(26):
            if age < 19:
                default_expenses[age]["Miscellaneous"] = 200
            else:
                default_expenses[age]["Miscellaneous"] = 300  # Young adults have more varied expenses

        # Daycare/Childcare - new category
        for age in range(26):
            if age < 1:
                default_expenses[age]["Daycare/Childcare"] = 20376  # Infant daycare ($1,698/mo)
            elif age < 3:
                default_expenses[age]["Daycare/Childcare"] = 15720  # Toddler daycare ($1,310/mo)
            elif age < 5:
                default_expenses[age]["Daycare/Childcare"] = 15720  # Preschool ($1,310/mo)
            else:
                default_expenses[age]["Daycare/Childcare"] = 0  # No daycare after kindergarten

        # Education - new category
        for age in range(26):
            if age >= 18 and age < 22:
                default_expenses[age]["Education"] = 75000  # College tuition/room/board
            else:
                default_expenses[age]["Education"] = 0

        return default_expenses


@dataclass
class Child:
    name: str
    birth_year: int
    template: ChildTemplate

    def to_dict(self):
        return {
            'name': self.name,
            'birth_year': self.birth_year,
            'template': self.template.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        template_data = data.pop('template')
        return cls(
            **data,
            template=ChildTemplate.from_dict(template_data)
        )


@dataclass
class FamilyExpenseTemplate:
    name: str
    state: str  # State for location-based defaults
    spending_category: str  # Frugal, Moderate, Luxury
    annual_expenses: Dict[str, float]  # Category -> Annual Amount

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @staticmethod
    def get_default_templates():
        """Get default family expense templates by state and spending category."""
        templates = {}

        # Define expense categories
        categories = [
            "Groceries",
            "Utilities",
            "Home Maintenance",
            "Insurance",
            "Transportation",
            "Entertainment",
            "Dining Out",
            "Travel/Vacation",
            "Personal Care",
            "Miscellaneous"
        ]

        # Define spending levels
        spending_levels = {
            "Frugal": 0.7,      # 70% of moderate
            "Moderate": 1.0,    # 100% baseline
            "Luxury": 1.5       # 150% of moderate
        }

        # State-specific cost of living multipliers (relative to national average)
        state_multipliers = {
            "California": 1.3,
            "New York": 1.25,
            "Washington": 1.15,
            "Texas": 0.95,
            "Florida": 1.0,
            "National Average": 1.0
        }

        # Base moderate expenses (national average)
        base_moderate = {
            "Groceries": 12000,
            "Utilities": 4800,
            "Home Maintenance": 6000,
            "Insurance": 8000,
            "Transportation": 10000,
            "Entertainment": 4000,
            "Dining Out": 6000,
            "Travel/Vacation": 5000,
            "Personal Care": 3000,
            "Miscellaneous": 5000
        }

        # Generate templates for each state and spending level
        for state, state_mult in state_multipliers.items():
            for level, level_mult in spending_levels.items():
                template_name = f"{state} - {level}"
                annual_expenses = {}

                for category, base_amount in base_moderate.items():
                    annual_expenses[category] = base_amount * state_mult * level_mult

                templates[template_name] = FamilyExpenseTemplate(
                    name=template_name,
                    state=state,
                    spending_category=level,
                    annual_expenses=annual_expenses
                )

        return templates


@dataclass
class MajorPurchase:
    name: str
    year: int
    amount: float
    financing_years: int = 0
    interest_rate: float = 0.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ScenarioParameters:
    def __init__(self):
        logger.debug("Initializing scenario parameters")
        self.scenarios = {
            'Conservative': {
                'investment_return': 0.04,
                'inflation_rate': 0.03,
                'expense_growth_rate': 0.02,
                'healthcare_inflation_rate': 0.05  # Healthcare costs rise faster
            },
            'Moderate': {
                'investment_return': 0.06,
                'inflation_rate': 0.025,
                'expense_growth_rate': 0.02,
                'healthcare_inflation_rate': 0.045
            },
            'Aggressive': {
                'investment_return': 0.08,
                'inflation_rate': 0.02,
                'expense_growth_rate': 0.02,
                'healthcare_inflation_rate': 0.04
            }
        }

        # Social Security insolvency settings
        self.ss_insolvency_enabled = True  # Enable by default
        self.ss_insolvency_year = 2034  # Projected insolvency year
        self.ss_shortfall_rate = 0.30  # 30% shortfall (70% of benefits will be paid)


class TaxSystem:
    def __init__(self):
        # Federal tax brackets for 2024 (simplified)
        self.federal_brackets = {
            'single': [
                TaxBracket(0, 11600, 0.10),
                TaxBracket(11600, 47150, 0.12),
                TaxBracket(47150, 100525, 0.22),
                TaxBracket(100525, 191950, 0.24),
                TaxBracket(191950, 243725, 0.32),
                TaxBracket(243725, 609350, 0.35),
                TaxBracket(609350, None, 0.37)
            ],
            'married': [
                TaxBracket(0, 23200, 0.10),
                TaxBracket(23200, 94300, 0.12),
                TaxBracket(94300, 201050, 0.22),
                TaxBracket(201050, 383900, 0.24),
                TaxBracket(383900, 487450, 0.32),
                TaxBracket(487450, 731200, 0.35),
                TaxBracket(731200, None, 0.37)
            ],
            'head_of_household': [
                TaxBracket(0, 16550, 0.10),
                TaxBracket(16550, 63100, 0.12),
                TaxBracket(63100, 100500, 0.22),
                TaxBracket(100500, 191950, 0.24),
                TaxBracket(191950, 243700, 0.32),
                TaxBracket(243700, 609350, 0.35),
                TaxBracket(609350, None, 0.37)
            ]
        }

        # Standard deductions for 2024
        self.standard_deductions = {
            'single': 14600,
            'married': 29200,
            'head_of_household': 21900
        }

    def _get_standard_deduction(self, year, filing_status):
        """Get standard deduction for a given year and filing status."""
        # In a real system, this would account for inflation adjustments over time
        # For now, just return the 2024 values
        return self.standard_deductions.get(filing_status, 14600)

    def calculate_federal_tax(self, income: float, filing_status: str) -> float:
        """Calculate federal income tax for a given income and filing status."""
        if filing_status not in self.federal_brackets:
            # Default to single if filing status not recognized
            filing_status = 'single'

        standard_deduction = self.standard_deductions[filing_status]
        taxable_income = max(0, income - standard_deduction)

        tax = 0
        for bracket in self.federal_brackets[filing_status]:
            if taxable_income > bracket.min_income:
                if bracket.max_income is None:
                    # This is the highest bracket
                    tax += (taxable_income - bracket.min_income) * bracket.rate
                else:
                    # Calculate tax for this bracket
                    bracket_income = min(taxable_income, bracket.max_income) - bracket.min_income
                    tax += bracket_income * bracket.rate

        return tax

    def calculate_state_tax(self, income: float, state_tax_rate: float) -> float:
        """Calculate state income tax for a given income and flat state tax rate."""
        return income * state_tax_rate

    def calculate_total_tax(self, income: float, filing_status: str, state_tax_rate: float) -> float:
        """Calculate total income tax (federal + state)."""
        federal_tax = self.calculate_federal_tax(income, filing_status)
        state_tax = self.calculate_state_tax(income, state_tax_rate)
        return federal_tax + state_tax


class ScenarioManager:
    def __init__(self):
        self.scenarios = {}

    def add_scenario(self, name, planner):
        """Save a scenario with a given name."""
        self.scenarios[name] = planner.to_dict()

    def get_scenario(self, name):
        """Get a saved scenario by name."""
        if name in self.scenarios:
            return FinancialPlanner.from_dict(self.scenarios[name])
        return None

    def compare_scenarios(self, scenario_names):
        """Compare multiple saved scenarios."""
        try:
            if not all(name in self.scenarios for name in scenario_names):
                missing = [name for name in scenario_names if name not in self.scenarios]
                raise ValueError(f"Scenarios not found: {missing}")

            comparison = {}
            for name in scenario_names:
                planner = FinancialPlanner.from_dict(self.scenarios[name])
                # Run projection with moderate parameters
                results = planner.calculate_projection('Moderate')
                comparison[name] = {
                    'ending_net_worth': results[-1]['net_worth'],
                    'min_net_worth': min(r['net_worth'] for r in results),
                    'max_annual_expense': max(r['total_expenses'] for r in results),
                    'retirement_income': sum(r['total_income'] for r in results if r['year'] >=
                                             min(p.birth_year + p.retirement_age for p in planner.persons))
                }

            return comparison
        except Exception as e:
            logger.error(f"Error comparing scenarios: {e}")
            logger.error(traceback.format_exc())
            return {}

    def list_scenarios(self):
        """Get a list of all saved scenario names."""
        return list(self.scenarios.keys())


class FinancialPlanner:
    def __init__(self,
                 persons: List[Person],
                 children: List[Child],
                 current_year: int,
                 current_net_worth: float,
                 yearly_expenses: float,
                 major_purchases: List[MajorPurchase] = None,
                 child_templates: List[ChildTemplate] = None,
                 family_expense_templates: List[FamilyExpenseTemplate] = None):
        logger.debug("Initializing FinancialPlanner")
        self.persons = persons
        self.children = children or []
        self.current_year = current_year
        self.current_net_worth = current_net_worth
        self.yearly_expenses = yearly_expenses
        self.scenario_params = ScenarioParameters()
        self.tax_system = TaxSystem()
        self.household_expenses = {}
        self.major_purchases = major_purchases or []
        self.child_templates = child_templates or []
        self.family_expense_templates = family_expense_templates or []
        self.healthcare_expenses = yearly_expenses * 0.12  # Estimate healthcare as 12% of total expenses
        logger.debug(f"Created planner with {len(persons)} persons, {len(children)} children")

    def to_dict(self):
        try:
            return {
                'persons': [p.to_dict() for p in self.persons],
                'children': [c.to_dict() for c in self.children],
                'current_year': self.current_year,
                'current_net_worth': self.current_net_worth,
                'yearly_expenses': self.yearly_expenses,
                'household_expenses': self.household_expenses,
                'major_purchases': [p.to_dict() for p in self.major_purchases],
                'child_templates': [t.to_dict() for t in self.child_templates],
                'family_expense_templates': [t.to_dict() for t in self.family_expense_templates],
                'healthcare_expenses': self.healthcare_expenses
            }
        except Exception as e:
            logger.error(f"Error in to_dict: {e}")
            raise

    @classmethod
    def from_dict(cls, data):
        try:
            persons = [Person.from_dict(p) for p in data['persons']]
            children = [Child.from_dict(c) for c in data['children']]
            major_purchases = [MajorPurchase.from_dict(p) for p in data['major_purchases']]
            child_templates = [ChildTemplate.from_dict(t) for t in data['child_templates']]
            family_expense_templates = [FamilyExpenseTemplate.from_dict(t) for t in data.get('family_expense_templates', [])]

            planner = cls(
                persons=persons,
                children=children,
                current_year=data['current_year'],
                current_net_worth=data['current_net_worth'],
                yearly_expenses=data['yearly_expenses'],
                major_purchases=major_purchases,
                child_templates=child_templates,
                family_expense_templates=family_expense_templates
            )
            planner.household_expenses = data.get('household_expenses', {})
            planner.healthcare_expenses = data.get('healthcare_expenses', planner.yearly_expenses * 0.12)
            return planner
        except Exception as e:
            logger.error(f"Error in from_dict: {e}")
            raise

    def save_scenario(self, filename: str):
        """Save current scenario to a JSON file."""
        try:
            logger.debug(f"Saving scenario to {filename}")
            data = self.to_dict()
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Save completed successfully")
        except Exception as e:
            logger.error(f"Error saving scenario: {e}")
            raise

    @classmethod
    def load_scenario(cls, filename: str):
        """Load scenario from a JSON file."""
        try:
            logger.debug(f"Loading scenario from {filename}")
            with open(filename, 'r') as f:
                data = json.load(f)
            planner = cls.from_dict(data)
            logger.debug("Load completed successfully")
            return planner
        except Exception as e:
            logger.error(f"Error loading scenario: {e}")
            raise

    def _calculate_ss_benefit(self, person: Person, year: int) -> float:
        """Calculate Social Security benefit for a person in a given year."""
        # Check if person is eligible for SS (has reached SS benefit age)
        person_age = year - person.birth_year
        if person_age < person.ss_benefit_age:
            return 0

        # Check if person is alive
        if person_age > person.death_age:
            return 0

        # Calculate base benefit
        benefit = person.estimated_ss_benefit

        # Apply insolvency shortfall if enabled and year is after insolvency year
        if self.scenario_params.ss_insolvency_enabled and year >= self.scenario_params.ss_insolvency_year:
            benefit = benefit * (1 - self.scenario_params.ss_shortfall_rate)

        return benefit

    def _calculate_gross_income(self, person: Person, year: int, inflation_rate: float) -> float:
        """Calculate gross income before taxes with step changes."""
        # Check if person is alive in this year
        if year > person.birth_year + person.death_age:
            return 0

        # Check if person is retired in this year
        if year >= person.birth_year + person.retirement_age:
            # If retired, only include Social Security benefits
            return self._calculate_ss_benefit(person, year)

        # Find the most recent income change before or at the current year
        most_recent_change = None
        change_year = None
        for y in sorted(person.income_changes.keys()):
            if y <= year:
                most_recent_change = person.income_changes[y]
                change_year = y

        if most_recent_change is not None:
            # Calculate growth from the most recent change
            years_since_change = year - change_year
            base_income = most_recent_change * (1 + person.income_growth_rate) ** years_since_change
        else:
            # Use original base income with growth
            years_working = year - self.current_year
            base_income = person.base_income * (1 + person.income_growth_rate) ** years_working

        # Apply inflation adjustment
        return base_income * (1 + inflation_rate) ** (year - self.current_year)

    def _calculate_tax(self, person: Person, income: float) -> float:
        """Calculate total tax for a person."""
        return self.tax_system.calculate_total_tax(
            income,
            person.filing_status,
            person.state_tax_rate
        )

    def _calculate_total_income(self, year: int, inflation_rate: float) -> Tuple[float, Dict[str, float]]:
        """Calculate total household income after taxes for a given year."""
        total_income = 0
        income_details = {}

        for person in self.persons:
            gross_income = self._calculate_gross_income(person, year, inflation_rate)
            tax = self._calculate_tax(person, gross_income)
            net_income = gross_income - tax

            total_income += net_income
            income_details[person.name] = {
                'gross': gross_income,
                'tax': tax,
                'net': net_income
            }

        return total_income, income_details

    def _calculate_child_expenses(self, year, inflation_rate):
        """Calculate child-related expenses for a given year."""
        total_child_expenses = 0

        for child in self.children:
            # Check child's age in this year
            age = year - child.birth_year

            # General expenses for children (all categories including daycare and education)
            if 0 <= age < 26:  # Include ages 0-25
                # Get expenses for this age from template
                if age in child.template.yearly_expenses:
                    # Get all expense categories
                    for category, amount in child.template.yearly_expenses[age].items():
                        # Apply inflation to the expense
                        years_elapsed = year - self.current_year
                        inflated_expense = amount * (1 + inflation_rate) ** years_elapsed
                        total_child_expenses += inflated_expense

        return total_child_expenses

    def _calculate_major_purchase_expenses(self, year: int) -> float:
        """Calculate expenses from major purchases for a given year."""
        total_expense = 0
        for purchase in self.major_purchases:
            if purchase.year == year:
                if purchase.financing_years == 0:
                    # Cash purchase
                    total_expense += purchase.amount
                else:
                    # Calculate monthly payment using loan amortization formula
                    r = purchase.interest_rate / 12  # Monthly interest rate
                    n = purchase.financing_years * 12  # Number of payments
                    if r > 0:
                        monthly_payment = (purchase.amount * r * (1 + r) ** n) / ((1 + r) ** n - 1)
                    else:
                        # Handle 0% interest case
                        monthly_payment = purchase.amount / n
                    total_expense += monthly_payment * 12
            elif (purchase.financing_years > 0 and
                  year > purchase.year and
                  year < purchase.year + purchase.financing_years):
                # Ongoing financing payments
                r = purchase.interest_rate / 12
                n = purchase.financing_years * 12
                if r > 0:
                    monthly_payment = (purchase.amount * r * (1 + r) ** n) / ((1 + r) ** n - 1)
                else:
                    # Handle 0% interest case
                    monthly_payment = purchase.amount / n
                total_expense += monthly_payment * 12

        return total_expense

    def _calculate_total_expenses(self, year: int, expense_growth_rate: float, inflation_rate: float,
                                  healthcare_inflation_rate: float) -> float:
        """Calculate total expenses including children and major purchases."""
        # Base household expenses with general inflation
        years_elapsed = year - self.current_year
        base_expenses = (self.yearly_expenses - self.healthcare_expenses) * (1 + expense_growth_rate) ** years_elapsed

        # Healthcare expenses with healthcare-specific inflation
        healthcare = self.healthcare_expenses * (1 + healthcare_inflation_rate) ** years_elapsed

        # Add child expenses
        child_expenses = self._calculate_child_expenses(year, inflation_rate)

        # Add major purchase expenses
        major_purchase_expenses = self._calculate_major_purchase_expenses(year)

        return base_expenses + healthcare + child_expenses + major_purchase_expenses

    def calculate_projection(self, scenario_name: str):
        """Calculate financial projection until all persons reach their death age."""
        try:
            logger.debug(f"Starting projection calculation for scenario: {scenario_name}")
            params = self.scenario_params.scenarios[scenario_name]

            # Determine end year (when all persons reach their death age)
            max_ages = [person.birth_year + person.death_age for person in self.persons]
            end_year = max(max_ages)
            logger.debug(f"Projection end year: {end_year}")

            # Run the projection
            results = []
            net_worth = self.current_net_worth

            for year in range(self.current_year, end_year + 1):
                # Calculate income
                total_income, income_details = self._calculate_total_income(
                    year,
                    params['inflation_rate']
                )

                # Calculate expenses
                total_expenses = self._calculate_total_expenses(
                    year,
                    params['expense_growth_rate'],
                    params['inflation_rate'],
                    params['healthcare_inflation_rate']
                )

                # Calculate investment returns
                investment_return = net_worth * params['investment_return']

                # Update net worth
                net_change = total_income - total_expenses + investment_return
                net_worth += net_change

                # Store results
                results.append({
                    'year': year,
                    'total_income': total_income,
                    'total_expenses': total_expenses,
                    'investment_return': investment_return,
                    'net_change': net_change,
                    'net_worth': net_worth,
                    'income_details': income_details
                })

            logger.debug(f"Projection completed with {len(results)} years of data")
            return results
        except Exception as e:
            logger.error(f"Error in calculate_projection: {e}")
            logger.error(traceback.format_exc())
            raise

    def calculate_projection_with_returns(self, scenario_name: str, annual_returns: List[float]):
        """Calculate projection with a specific sequence of investment returns."""
        try:
            logger.debug(f"Starting projection with custom returns for scenario: {scenario_name}")
            params = self.scenario_params.scenarios[scenario_name]

            # Determine end year (when all persons reach their death age)
            max_ages = [person.birth_year + person.death_age for person in self.persons]
            end_year = max(max_ages)

            # Make sure we have enough returns
            if len(annual_returns) < end_year - self.current_year + 1:
                raise ValueError("Not enough annual returns provided")

            # Run the projection
            results = []
            net_worth = self.current_net_worth

            for i, year in enumerate(range(self.current_year, end_year + 1)):
                # Calculate income
                total_income, income_details = self._calculate_total_income(
                    year,
                    params['inflation_rate']
                )

                # Calculate expenses
                total_expenses = self._calculate_total_expenses(
                    year,
                    params['expense_growth_rate'],
                    params['inflation_rate'],
                    params['healthcare_inflation_rate']
                )

                # Use the provided investment return for this year
                investment_return = net_worth * annual_returns[i]

                # Update net worth
                net_change = total_income - total_expenses + investment_return
                net_worth += net_change

                # Store results
                results.append({
                    'year': year,
                    'total_income': total_income,
                    'total_expenses': total_expenses,
                    'investment_return': investment_return,
                    'net_change': net_change,
                    'net_worth': net_worth
                })

            return results
        except Exception as e:
            logger.error(f"Error in calculate_projection_with_returns: {e}")
            logger.error(traceback.format_exc())
            raise

    def run_monte_carlo_simulation(self, scenario_name, num_simulations=1000):
        """Run a Monte Carlo simulation with varying market returns."""
        try:
            logger.debug(f"Starting Monte Carlo simulation for {scenario_name}")

            # Limit simulations to prevent crashes
            num_simulations = min(500, num_simulations)
            logger.debug(f"Using {num_simulations} simulations to prevent memory issues")

            params = self.scenario_params.scenarios[scenario_name]
            base_return = params['investment_return']

            success_count = 0
            results = []

            # Force garbage collection before starting
            gc.collect()

            # Determine how many years to simulate first
            max_ages = [person.birth_year + person.death_age for person in self.persons]
            end_year = max(max_ages)
            num_years = end_year - self.current_year + 1
            logger.debug(f"Monte Carlo simulation period: {num_years} years")

            for i in range(num_simulations):
                if i > 0 and i % 100 == 0:
                    logger.debug(f"Completed {i} Monte Carlo simulations")
                    # Force garbage collection periodically
                    gc.collect()

                # Vary the investment return for each simulation
                # Using normal distribution around the base return
                annual_returns = []

                for j in range(num_years):
                    # Standard deviation can be adjusted based on asset allocation
                    std_dev = base_return * 0.5  # Simplified volatility model
                    annual_return = np.random.normal(base_return, std_dev)
                    annual_returns.append(annual_return)

                # Run simulation with this return series
                simulation_result = self.calculate_projection_with_returns(scenario_name, annual_returns)
                results.append(simulation_result)

                # Check if this simulation was successful (never ran out of money)
                if all(r['net_worth'] > 0 for r in simulation_result):
                    success_count += 1

            success_rate = success_count / num_simulations * 100
            logger.debug(f"Monte Carlo completed with success rate: {success_rate:.1f}%")

            # Force garbage collection before returning results
            gc.collect()

            return {
                'success_rate': success_rate,
                'results': results
            }
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            logger.error(traceback.format_exc())
            # Return a minimal valid result structure to prevent crashes
            return {
                'success_rate': 0,
                'results': []
            }

    def optimize_retirement_withdrawals(self, person, year, amount_needed):
        """Determine tax-optimal withdrawal strategy from different account types."""
        # Simplified implementation - a full implementation would be more complex
        taxable_amount = 0
        tax_deferred_amount = 0
        tax_free_amount = 0

        # Start with RMDs from tax-deferred accounts if required
        rmd_amount = 0  # In a real implementation, calculate RMDs
        amount_needed -= rmd_amount
        tax_deferred_amount += rmd_amount

        if amount_needed <= 0:
            return {
                'taxable': 0,
                'tax_deferred': tax_deferred_amount,
                'tax_free': 0
            }

        # First use taxable accounts to fill standard deduction
        standard_deduction = self.tax_system._get_standard_deduction(year, person.filing_status)
        taxable_to_deduction = min(standard_deduction, amount_needed)
        taxable_amount += taxable_to_deduction
        amount_needed -= taxable_to_deduction

        # Next use Roth (tax-free) for amounts that would be taxed at higher rates
        tax_free_amount = amount_needed * 0.5  # Simplified - would need more complex logic
        amount_needed -= tax_free_amount

        # Remainder from tax-deferred accounts
        tax_deferred_amount += amount_needed

        return {
            'taxable': taxable_amount,
            'tax_deferred': tax_deferred_amount,
            'tax_free': tax_free_amount
        }


class FinancialPlannerGUI(QMainWindow):
    def __init__(self, planner: FinancialPlanner):
        try:
            logger.debug("Initializing GUI")
            super().__init__()
            self.planner = planner
            self.scenario_manager = ScenarioManager()
            self.init_ui()
            logger.debug("GUI initialization complete")
        except Exception as e:
            logger.critical(f"Error initializing GUI: {e}")
            logger.critical(traceback.format_exc())
            QMessageBox.critical(None, "Initialization Error",
                                 f"Failed to initialize application: {str(e)}")
            raise

    def init_ui(self):
        """Initialize the main user interface."""
        try:
            self.setWindowTitle('Financial Planner')
            self.setGeometry(100, 100, 1200, 800)

            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Add scenario management buttons
            scenario_layout = QHBoxLayout()
            save_button = QPushButton("Save Scenario")
            load_button = QPushButton("Load Scenario")
            compare_button = QPushButton("Compare Scenarios")
            save_button.clicked.connect(self.save_scenario)
            load_button.clicked.connect(self.load_scenario)
            compare_button.clicked.connect(self.compare_scenarios)

            scenario_layout.addWidget(save_button)
            scenario_layout.addWidget(load_button)
            scenario_layout.addWidget(compare_button)
            layout.addLayout(scenario_layout)

            # Create tab widget
            self.tabs = QTabWidget()
            layout.addWidget(self.tabs)

            # Setup all tabs
            self._setup_all_tabs()
        except Exception as e:
            logger.error(f"Error in init_ui: {e}")
            logger.error(traceback.format_exc())
            raise

    def _setup_all_tabs(self):
        """Create and set up all tabs in the interface."""
        try:
            # Basic info tab
            basic_info_tab = self.setup_basic_info_tab()
            self.tabs.addTab(basic_info_tab, "Settings and Instructions")

            # Partner X tab
            partner_x_tab = self.setup_partner_tab("X")
            self.tabs.addTab(partner_x_tab, "Partner X")

            # Partner Y tab
            partner_y_tab = self.setup_partner_tab("Y")
            self.tabs.addTab(partner_y_tab, "Partner Y")

            # Dependents Template Tab
            dependents_template_tab = self.setup_dependents_template_tab()
            self.tabs.addTab(dependents_template_tab, "Dependents Templates")

            # Dependents Planning Tab
            dependents_planning_tab = self.setup_dependents_planning_tab()
            self.tabs.addTab(dependents_planning_tab, "Dependents Planning")

            # Major Purchases Tab
            major_purchases_tab = self.setup_major_purchases_tab()
            self.tabs.addTab(major_purchases_tab, "Major Purchases")

            # Check if tax burden tab method exists
            if hasattr(self, 'setup_tax_burden_tab'):
                # Tax Burden Tab
                tax_burden_tab = self.setup_tax_burden_tab()
                self.tabs.addTab(tax_burden_tab, "Tax Burden")
            else:
                logger.warning("Tax burden tab method not found")

            # Results Tab
            results_tab = self.setup_results_tab()
            self.tabs.addTab(results_tab, "Results")

            # Monte Carlo Tab
            monte_carlo_tab = self.setup_monte_carlo_tab()
            self.tabs.addTab(monte_carlo_tab, "Monte Carlo")

            # After all tabs are set up and all methods are defined,
            # now we can initialize partner data if available
            for partner_id in ["X", "Y"]:
                # Find any existing partner data
                for person in self.planner.persons:
                    if person.name.startswith(f"Partner {partner_id}:"):
                        # Now that all methods are defined, we can safely call refresh_partner_data
                        self.refresh_partner_data(partner_id)
                        break

            logger.debug("All tabs created successfully")
        except Exception as e:
            logger.error(f"Error setting up tabs: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_basic_info_tab(self) -> QWidget:
        """Set up the basic information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        basic_group = QGroupBox("Household Information")
        basic_layout = QFormLayout()

        self.current_year_input = QSpinBox()
        self.current_year_input.setRange(2000, 2100)
        self.current_year_input.setValue(self.planner.current_year)

        self.yearly_expenses_input = QDoubleSpinBox()
        self.yearly_expenses_input.setRange(0, 1000000)
        self.yearly_expenses_input.setPrefix("$")
        self.yearly_expenses_input.setValue(self.planner.yearly_expenses)

        self.healthcare_expenses_input = QDoubleSpinBox()
        self.healthcare_expenses_input.setRange(0, 1000000)
        self.healthcare_expenses_input.setPrefix("$")
        self.healthcare_expenses_input.setValue(self.planner.healthcare_expenses)

        basic_layout.addRow("Current Year:", self.current_year_input)
        basic_layout.addRow("Yearly Expenses:", self.yearly_expenses_input)
        basic_layout.addRow("Healthcare Expenses:", self.healthcare_expenses_input)

        update_button = QPushButton("Update Basic Info")
        update_button.clicked.connect(self.update_basic_info)

        basic_layout.addRow(update_button)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Add scenario parameters display
        scenario_group = QGroupBox("Scenario Parameters")
        scenario_layout = QVBoxLayout()

        # Create a table to display scenario parameters
        self.scenario_params_table = QTableWidget()
        self.scenario_params_table.setColumnCount(5)
        self.scenario_params_table.setHorizontalHeaderLabels([
            "Scenario", "Investment Return", "Inflation", "Expense Growth", "Healthcare Inflation"
        ])

        # Populate the table
        self.refresh_scenario_params_table()

        scenario_layout.addWidget(self.scenario_params_table)
        scenario_group.setLayout(scenario_layout)
        layout.addWidget(scenario_group)

        # Add Social Security insolvency settings
        ss_group = QGroupBox("Social Security Insolvency Settings")
        ss_layout = QFormLayout()

        self.ss_insolvency_enabled = QCheckBox()
        self.ss_insolvency_enabled.setChecked(self.planner.scenario_params.ss_insolvency_enabled)

        self.ss_insolvency_year_input = QSpinBox()
        self.ss_insolvency_year_input.setRange(2024, 2100)
        self.ss_insolvency_year_input.setValue(self.planner.scenario_params.ss_insolvency_year)

        self.ss_shortfall_rate_input = QDoubleSpinBox()
        self.ss_shortfall_rate_input.setRange(0, 1.0)
        self.ss_shortfall_rate_input.setSingleStep(0.05)
        self.ss_shortfall_rate_input.setDecimals(2)
        self.ss_shortfall_rate_input.setValue(self.planner.scenario_params.ss_shortfall_rate)
        self.ss_shortfall_rate_input.setSuffix("%")

        ss_layout.addRow("Enable SS Insolvency:", self.ss_insolvency_enabled)
        ss_layout.addRow("Insolvency Year:", self.ss_insolvency_year_input)
        ss_layout.addRow("Benefit Shortfall Rate:", self.ss_shortfall_rate_input)

        update_ss_button = QPushButton("Update SS Settings")
        update_ss_button.clicked.connect(self.update_ss_settings)
        ss_layout.addRow(update_ss_button)

        ss_group.setLayout(ss_layout)
        layout.addWidget(ss_group)

        # Add instructions section
        instructions_group = QGroupBox("Instructions and Tab Guide")
        instructions_layout = QVBoxLayout()

        instructions_text = """
        <h3>How to Use the Financial Planner</h3>

        <p><b>Settings and Instructions:</b> Configure household information, scenario parameters, and Social Security settings.
        Social Security insolvency option allows you to model the projected 30% shortfall in benefits starting in 2034.</p>

        <p><b>Partner X / Partner Y:</b> Enter detailed information for each partner including income, retirement age, death age,
        and Social Security benefits. You can also add income changes that occur at specific years.</p>

        <p><b>Dependents Templates:</b> Create expense templates for children by state and spending category. These templates
        can be reused for multiple children and include age-specific expenses, daycare costs, and education funding.</p>

        <p><b>Dependents Planning:</b> Add children to your plan and assign them to templates. View projected costs and
        education funding needs.</p>

        <p><b>Major Purchases:</b> Track large expenses like homes, cars, or other significant purchases. Include financing
        details such as loan term and interest rate.</p>

        <p><b>Tax Burden:</b> View projected tax burden over time based on income, filing status, and state tax rates.</p>

        <p><b>Results:</b> Run projections to see how your net worth evolves over time under different scenarios
        (Conservative, Moderate, Aggressive). View detailed breakdowns of income, expenses, and net worth trajectories.</p>

        <p><b>Monte Carlo:</b> Run probabilistic simulations that account for market volatility to estimate the likelihood
        of financial success under various conditions.</p>

        <p><i>Tip: Start by entering partner information, then add children and major purchases. Run projections to see
        how different scenarios affect your financial future.</i></p>
        """

        from PyQt6.QtWidgets import QTextBrowser
        instructions_browser = QTextBrowser()
        instructions_browser.setHtml(instructions_text)
        instructions_browser.setMaximumHeight(400)

        instructions_layout.addWidget(instructions_browser)
        instructions_group.setLayout(instructions_layout)
        layout.addWidget(instructions_group)

        # Add Scenario Library section
        library_group = QGroupBox("Scenario Library")
        library_layout = QVBoxLayout()

        # Saved scenarios list
        scenarios_list_layout = QHBoxLayout()

        self.saved_scenarios_list = QListWidget()
        self.saved_scenarios_list.setMaximumHeight(150)
        scenarios_list_layout.addWidget(self.saved_scenarios_list)

        # Buttons for scenario management
        library_buttons_layout = QVBoxLayout()

        self.load_selected_scenario_btn = QPushButton("Load Selected")
        self.load_selected_scenario_btn.clicked.connect(self.load_selected_scenario)
        library_buttons_layout.addWidget(self.load_selected_scenario_btn)

        self.delete_selected_scenario_btn = QPushButton("Delete Selected")
        self.delete_selected_scenario_btn.clicked.connect(self.delete_selected_scenario)
        library_buttons_layout.addWidget(self.delete_selected_scenario_btn)

        library_buttons_layout.addStretch()
        scenarios_list_layout.addLayout(library_buttons_layout)

        library_layout.addLayout(scenarios_list_layout)

        # Save current scenario with name
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Scenario Name:"))

        self.scenario_name_input = QLineEdit()
        self.scenario_name_input.setPlaceholderText("Enter scenario name...")
        save_layout.addWidget(self.scenario_name_input)

        self.save_named_scenario_btn = QPushButton("Save as Named Scenario")
        self.save_named_scenario_btn.clicked.connect(self.save_named_scenario)
        save_layout.addWidget(self.save_named_scenario_btn)

        library_layout.addLayout(save_layout)

        # Add file-based save/load buttons
        file_layout = QHBoxLayout()

        export_file_btn = QPushButton("Export to File...")
        export_file_btn.clicked.connect(self.save_scenario)
        file_layout.addWidget(export_file_btn)

        import_file_btn = QPushButton("Import from File...")
        import_file_btn.clicked.connect(self.load_scenario)
        file_layout.addWidget(import_file_btn)

        library_layout.addLayout(file_layout)

        library_group.setLayout(library_layout)
        layout.addWidget(library_group)

        # Refresh the scenarios list
        self.refresh_scenarios_library()

        return tab

    def refresh_scenario_params_table(self):
        """Refresh the scenario parameters table."""
        self.scenario_params_table.setRowCount(0)

        for scenario_name, params in self.planner.scenario_params.scenarios.items():
            row = self.scenario_params_table.rowCount()
            self.scenario_params_table.insertRow(row)

            self.scenario_params_table.setItem(row, 0, QTableWidgetItem(scenario_name))
            self.scenario_params_table.setItem(row, 1, QTableWidgetItem(f"{params['investment_return'] * 100:.1f}%"))
            self.scenario_params_table.setItem(row, 2, QTableWidgetItem(f"{params['inflation_rate'] * 100:.1f}%"))
            self.scenario_params_table.setItem(row, 3, QTableWidgetItem(f"{params['expense_growth_rate'] * 100:.1f}%"))
            self.scenario_params_table.setItem(row, 4,
                                               QTableWidgetItem(f"{params['healthcare_inflation_rate'] * 100:.1f}%"))

    def setup_partner_tab(self, partner_id: str) -> QWidget:
        """Set up the partner tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Define partner-specific attribute names to store widgets
        name_attr = f"partner_{partner_id.lower()}_name_input"
        birth_attr = f"partner_{partner_id.lower()}_birth_year_input"
        income_attr = f"partner_{partner_id.lower()}_base_income_input"
        growth_attr = f"partner_{partner_id.lower()}_income_growth_input"
        retirement_attr = f"partner_{partner_id.lower()}_retirement_age_input"
        death_attr = f"partner_{partner_id.lower()}_death_age_input"
        filing_attr = f"partner_{partner_id.lower()}_filing_status_input"
        tax_attr = f"partner_{partner_id.lower()}_state_tax_input"
        net_worth_attr = f"partner_{partner_id.lower()}_net_worth_input"
        ss_age_attr = f"partner_{partner_id.lower()}_ss_age_input"
        ss_benefit_attr = f"partner_{partner_id.lower()}_ss_benefit_input"

        # Partner info fields
        partner_group = QGroupBox(f"Partner {partner_id} Information")
        partner_layout = QFormLayout()

        # Create widgets and store them as attributes
        setattr(self, name_attr, QLineEdit())
        setattr(self, birth_attr, QSpinBox())
        getattr(self, birth_attr).setRange(1900, 2100)

        setattr(self, income_attr, QDoubleSpinBox())
        getattr(self, income_attr).setRange(0, 10000000)
        getattr(self, income_attr).setPrefix("$")

        setattr(self, growth_attr, QDoubleSpinBox())
        getattr(self, growth_attr).setRange(0, 0.5)
        getattr(self, growth_attr).setSingleStep(0.005)
        getattr(self, growth_attr).setDecimals(3)
        getattr(self, growth_attr).setValue(0.03)

        setattr(self, retirement_attr, QSpinBox())
        getattr(self, retirement_attr).setRange(20, 100)
        getattr(self, retirement_attr).setValue(65)

        setattr(self, death_attr, QSpinBox())
        getattr(self, death_attr).setRange(50, 120)
        getattr(self, death_attr).setValue(100)

        setattr(self, ss_age_attr, QSpinBox())
        getattr(self, ss_age_attr).setRange(62, 70)
        getattr(self, ss_age_attr).setValue(67)

        setattr(self, ss_benefit_attr, QDoubleSpinBox())
        getattr(self, ss_benefit_attr).setRange(0, 100000)
        getattr(self, ss_benefit_attr).setPrefix("$")
        getattr(self, ss_benefit_attr).setValue(0)

        setattr(self, filing_attr, QComboBox())
        getattr(self, filing_attr).addItems(['single', 'married', 'head_of_household'])

        setattr(self, tax_attr, QDoubleSpinBox())
        getattr(self, tax_attr).setRange(0, 0.2)
        getattr(self, tax_attr).setSingleStep(0.005)
        getattr(self, tax_attr).setDecimals(3)

        # Net worth input (moved from basic info)
        setattr(self, net_worth_attr, QDoubleSpinBox())
        getattr(self, net_worth_attr).setRange(-10000000, 100000000)
        getattr(self, net_worth_attr).setPrefix("$")

        # Set value based on planner's current net worth (equally divided between partners)
        if partner_id == "X":
            getattr(self, net_worth_attr).setValue(self.planner.current_net_worth * 0.5)
        else:
            getattr(self, net_worth_attr).setValue(self.planner.current_net_worth * 0.5)

        # Add all widgets to the form layout
        partner_layout.addRow("Name:", getattr(self, name_attr))
        partner_layout.addRow("Birth Year:", getattr(self, birth_attr))
        partner_layout.addRow("Base Income:", getattr(self, income_attr))
        partner_layout.addRow("Income Growth Rate:", getattr(self, growth_attr))
        partner_layout.addRow("Retirement Age:", getattr(self, retirement_attr))
        partner_layout.addRow("Death Age:", getattr(self, death_attr))
        partner_layout.addRow("Social Security Age:", getattr(self, ss_age_attr))
        partner_layout.addRow("Annual SS Benefit:", getattr(self, ss_benefit_attr))
        partner_layout.addRow("Filing Status:", getattr(self, filing_attr))
        partner_layout.addRow("State Tax Rate:", getattr(self, tax_attr))
        partner_layout.addRow("Net Worth:", getattr(self, net_worth_attr))

        # Add buttons to update or reset partner info
        update_button = QPushButton(f"Update Partner {partner_id}")
        update_button.clicked.connect(lambda: self.update_partner(partner_id))
        partner_layout.addRow(update_button)

        partner_group.setLayout(partner_layout)
        layout.addWidget(partner_group)

        # Income changes section
        income_change_group = QGroupBox("Income Changes")
        income_change_layout = QFormLayout()

        income_change_year_attr = f"partner_{partner_id.lower()}_income_change_year_input"
        income_change_amount_attr = f"partner_{partner_id.lower()}_income_change_amount_input"

        setattr(self, income_change_year_attr, QSpinBox())
        getattr(self, income_change_year_attr).setRange(2000, 2100)

        setattr(self, income_change_amount_attr, QDoubleSpinBox())
        getattr(self, income_change_amount_attr).setRange(0, 10000000)
        getattr(self, income_change_amount_attr).setPrefix("$")

        income_change_layout.addRow("Year:", getattr(self, income_change_year_attr))
        income_change_layout.addRow("New Income:", getattr(self, income_change_amount_attr))

        add_income_change_button = QPushButton("Add Income Change")
        add_income_change_button.clicked.connect(lambda: self.add_partner_income_change(partner_id))

        income_change_layout.addRow(add_income_change_button)
        income_change_group.setLayout(income_change_layout)
        layout.addWidget(income_change_group)

        # Income changes table
        table_attr = f"partner_{partner_id.lower()}_income_changes_table"
        setattr(self, table_attr, QTableWidget())
        getattr(self, table_attr).setColumnCount(3)
        getattr(self, table_attr).setHorizontalHeaderLabels([
            "Year", "New Income", "Action"
        ])
        layout.addWidget(getattr(self, table_attr))

        # Don't call refresh_partner_data here - it's causing initialization issues
        # We'll update the UI after all methods are defined

        return tab

    def setup_dependents_template_tab(self) -> QWidget:
        """Set up the child template management tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Top section with template name
        top_group = QGroupBox("Template Settings")
        top_layout = QFormLayout()
        self.template_name_input = QLineEdit()
        top_layout.addRow("Template Name:", self.template_name_input)
        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)

        # Annual expenses table by age and category
        expense_group = QGroupBox("Annual Expenses by Age and Category (including Daycare and Education)")
        expense_layout = QVBoxLayout()

        # Controls above the table
        controls_layout = QHBoxLayout()

        self.age_filter_combo = QComboBox()
        age_options = ["All Ages"] + [f"Age {i}" for i in range(26)]  # 0-25
        self.age_filter_combo.addItems(age_options)
        self.age_filter_combo.currentIndexChanged.connect(self.filter_expense_table)

        self.expense_category_filter = QComboBox()
        self.expense_category_filter.addItems(["All Categories", "Food", "Clothing", "Healthcare",
                                               "Activities/Sports", "Entertainment", "Transportation",
                                               "School Supplies", "Gifts/Celebrations", "Miscellaneous",
                                               "Daycare/Childcare", "Education"])
        self.expense_category_filter.currentIndexChanged.connect(self.filter_expense_table)

        load_default_button = QPushButton("Load WA Default Values")
        load_default_button.clicked.connect(self.load_default_expenses)

        controls_layout.addWidget(QLabel("Filter by Age:"))
        controls_layout.addWidget(self.age_filter_combo)
        controls_layout.addWidget(QLabel("Filter by Category:"))
        controls_layout.addWidget(self.expense_category_filter)
        controls_layout.addWidget(load_default_button)

        expense_layout.addLayout(controls_layout)

        # Create the expense table
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(13)  # Age + 11 expense categories + Total
        headers = ["Age", "Food", "Clothing", "Healthcare", "Activities/Sports",
                   "Entertainment", "Transportation", "School Supplies",
                   "Gifts/Celebrations", "Miscellaneous", "Daycare/Childcare",
                   "Education", "Total"]
        self.expense_table.setHorizontalHeaderLabels(headers)
        self.expense_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.expense_table.itemChanged.connect(self.update_expense_total)

        # Create total labels before initializing the table
        # These need to be created before calling init_expense_table since it calls
        # update_expense_total which in turn calls update_cost_summary which uses these labels
        self.total_child_cost_label = QLabel("$0")
        self.annual_avg_cost_label = QLabel("$0")

        # Initialize the table with rows for ages 0-25
        self.init_expense_table()

        expense_layout.addWidget(self.expense_table)
        expense_group.setLayout(expense_layout)

        # Add to main layout
        main_layout.addWidget(expense_group)

        # Total cost summary
        summary_group = QGroupBox("Cost Summary")
        summary_layout = QFormLayout()

        summary_layout.addRow("Total Cost (Age 0-25):", self.total_child_cost_label)
        summary_layout.addRow("Average Annual Cost:", self.annual_avg_cost_label)

        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)

        # Save template button
        save_template_button = QPushButton("Save Template")
        save_template_button.clicked.connect(self.save_template)
        main_layout.addWidget(save_template_button)

        # Templates table
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(4)  # Removed separate education and daycare columns
        self.templates_table.setHorizontalHeaderLabels(
            ["Name", "Total Cost", "Annual Average", "Action"])
        main_layout.addWidget(self.templates_table)

        self.refresh_templates_table()

        return tab

    def init_expense_table(self):
        """Initialize the expense table with rows for ages 0-25."""
        self.expense_table.setRowCount(26)  # Ages 0-25
        for row in range(26):
            # Set age cell
            age_item = QTableWidgetItem(str(row))
            age_item.setFlags(age_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make age non-editable
            self.expense_table.setItem(row, 0, age_item)

            # Initialize expense cells with $0
            for col in range(1, 12):  # 11 expense categories
                expense_item = QTableWidgetItem("$0")
                self.expense_table.setItem(row, col, expense_item)

            # Initialize total column
            total_item = QTableWidgetItem("$0")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make total non-editable
            self.expense_table.setItem(row, 12, total_item)

    def update_expense_total(self, item):
        """Update the total column when an expense is changed."""
        try:
            if item.column() == 0 or item.column() == 12:
                return  # Skip if age or total column

            row = item.row()

            # Convert cell text to value
            try:
                # Clean the text and convert to float
                text = item.text().replace("$", "").replace(",", "")
                value = float(text)

                # Update the cell with formatted value
                item.setText(format_currency(value))
            except ValueError:
                # If conversion fails, reset to $0
                item.setText("$0")
                value = 0

            # Calculate row total
            row_total = 0
            for col in range(1, 12):  # 11 expense categories
                cell_item = self.expense_table.item(row, col)
                if cell_item:
                    try:
                        cell_text = cell_item.text().replace("$", "").replace(",", "")
                        row_total += float(cell_text)
                    except (ValueError, AttributeError):
                        pass

            # Update total cell
            total_item = self.expense_table.item(row, 12)
            if total_item:
                total_item.setText(format_currency(row_total))

            # Update summary
            self.update_cost_summary()
        except Exception as e:
            logger.error(f"Error in update_expense_total: {e}")

    def update_cost_summary(self):
        """Update the total and average cost labels."""
        try:
            # Guard against the method being called before labels are initialized
            if not hasattr(self, 'total_child_cost_label') or not hasattr(self, 'annual_avg_cost_label'):
                return

            total_cost = 0
            for row in range(26):  # Ages 0-25
                total_item = self.expense_table.item(row, 12)
                if total_item:
                    try:
                        text = total_item.text().replace("$", "").replace(",", "")
                        total_cost += float(text)
                    except ValueError:
                        pass

            self.total_child_cost_label.setText(format_currency(total_cost))
            self.annual_avg_cost_label.setText(format_currency(total_cost / 26))
        except Exception as e:
            logger.error(f"Error in update_cost_summary: {e}")

    def filter_expense_table(self):
        """Filter the expense table by age and/or category."""
        try:
            age_filter = self.age_filter_combo.currentText()
            category_filter = self.expense_category_filter.currentText()

            # Show all rows and columns initially
            for row in range(26):
                self.expense_table.setRowHidden(row, False)

            for col in range(13):
                self.expense_table.setColumnHidden(col, False)

            # Apply age filter
            if age_filter != "All Ages":
                age = int(age_filter.replace("Age ", ""))
                for row in range(26):
                    if row != age:
                        self.expense_table.setRowHidden(row, True)

            # Apply category filter
            if category_filter != "All Categories":
                # Find column index for the selected category
                for col in range(1, 12):  # Skip age and total columns
                    header_item = self.expense_table.horizontalHeaderItem(col)
                    if header_item and header_item.text() != category_filter:
                        self.expense_table.setColumnHidden(col, True)
        except Exception as e:
            logger.error(f"Error in filter_expense_table: {e}")

    def load_default_expenses(self):
        """Load default Washington state expense values."""
        try:
            # Get default expenses
            default_expenses = ChildTemplate.get_default_expenses()

            # Update the table
            for age, categories in default_expenses.items():
                row = age  # Row index equals age

                for col in range(1, 12):  # 11 expense categories
                    col_header = self.expense_table.horizontalHeaderItem(col).text()
                    if col_header in categories:
                        value = categories[col_header]
                        item = QTableWidgetItem(format_currency(value))
                        self.expense_table.setItem(row, col, item)

                # Update row total
                row_total = sum(categories.values())
                total_item = self.expense_table.item(row, 12)
                if total_item:
                    total_item.setText(format_currency(row_total))

            # Update summary
            self.update_cost_summary()

            logger.debug("Loaded default expenses")
        except Exception as e:
            logger.error(f"Error loading default expenses: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load default expenses: {str(e)}")

    def save_template(self):
        """Save the current child template."""
        try:
            name = self.template_name_input.text()
            if not name:
                QMessageBox.warning(self, "Warning", "Template name is required")
                return

            # Collect expenses from table
            yearly_expenses = {}
            for row in range(26):  # Ages 0-25
                age = int(self.expense_table.item(row, 0).text())
                yearly_expenses[age] = {}

                # Get values for each expense category
                for col in range(1, 12):  # 11 expense categories
                    category = self.expense_table.horizontalHeaderItem(col).text()
                    item = self.expense_table.item(row, col)
                    if item:
                        try:
                            value_text = item.text().replace("$", "").replace(",", "")
                            value = float(value_text)
                            yearly_expenses[age][category] = value
                        except ValueError:
                            yearly_expenses[age][category] = 0.0
                    else:
                        yearly_expenses[age][category] = 0.0

            # Create template and add to planner
            template = ChildTemplate(
                name=name,
                yearly_expenses=yearly_expenses
            )

            # Add to planner and update UI
            self.planner.child_templates.append(template)
            self.refresh_templates_table()
            self.update_template_dropdown()

            # Show success message
            QMessageBox.information(
                self,
                "Template Saved",
                f"Template '{name}' has been saved successfully."
            )

            # Clear inputs
            self.template_name_input.clear()

            logger.debug(f"Saved template: {name}")
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save template: {str(e)}")

    def refresh_templates_table(self):
        """Refresh the templates table with current data."""
        try:
            if not hasattr(self, 'templates_table'):
                return

            self.templates_table.setRowCount(0)
            for template in self.planner.child_templates:
                row = self.templates_table.rowCount()
                self.templates_table.insertRow(row)

                # Calculate total cost and average annual cost
                total_cost = 0
                for age, categories in template.yearly_expenses.items():
                    total_cost += sum(categories.values())
                avg_annual_cost = total_cost / 26 if len(template.yearly_expenses) > 0 else 0

                self.templates_table.setItem(row, 0, QTableWidgetItem(template.name))
                self.templates_table.setItem(row, 1, QTableWidgetItem(format_currency(total_cost)))
                self.templates_table.setItem(row, 2, QTableWidgetItem(format_currency(avg_annual_cost)))

                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, t=template: self.delete_template(t))
                self.templates_table.setCellWidget(row, 3, delete_btn)
        except Exception as e:
            logger.error(f"Error in refresh_templates_table: {e}")

    def delete_template(self, template):
        """Remove a template from the planner."""
        try:
            # Check if any children are using this template
            using_children = []
            for child in self.planner.children:
                if child.template.name == template.name:
                    using_children.append(child.name)

            if using_children:
                QMessageBox.warning(
                    self,
                    "Cannot Delete",
                    f"Cannot delete template '{template.name}' because it is used by: {', '.join(using_children)}"
                )
                return

            self.planner.child_templates.remove(template)
            self.refresh_templates_table()
            self.update_template_dropdown()
        except Exception as e:
            logger.error(f"Error in delete_template: {e}")

    def update_template_dropdown(self):
        """Update the template dropdown in the children planning tab."""
        try:
            if not hasattr(self, 'child_template_combo'):
                return

            current_text = self.child_template_combo.currentText()

            self.child_template_combo.clear()
            for template in self.planner.child_templates:
                self.child_template_combo.addItem(template.name)

            # Try to restore previous selection
            index = self.child_template_combo.findText(current_text)
            if index >= 0:
                self.child_template_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error in update_template_dropdown: {e}")

    def setup_dependents_planning_tab(self) -> QWidget:
        """Set up the children planning tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add new child section
        add_child_group = QGroupBox("Add New Child")
        add_child_layout = QFormLayout()

        self.child_name_input = QLineEdit()

        self.child_template_combo = QComboBox()
        self.update_template_dropdown()

        self.child_birth_year_input = QSpinBox()
        self.child_birth_year_input.setRange(2000, 2100)
        self.child_birth_year_input.setValue(self.planner.current_year)

        add_child_layout.addRow("Name:", self.child_name_input)
        add_child_layout.addRow("Template:", self.child_template_combo)
        add_child_layout.addRow("Birth Year:", self.child_birth_year_input)

        add_child_button = QPushButton("Add Child")
        add_child_button.clicked.connect(self.add_child)
        add_child_layout.addRow(add_child_button)

        add_child_group.setLayout(add_child_layout)
        layout.addWidget(add_child_group)

        # Children list
        self.children_table = QTableWidget()
        self.children_table.setColumnCount(4)
        self.children_table.setHorizontalHeaderLabels(["Name", "Birth Year", "Template", "Action"])
        layout.addWidget(self.children_table)

        self.refresh_children_table()

        return tab

    def setup_major_purchases_tab(self) -> QWidget:
        """Set up the major purchases tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add new purchase section
        add_purchase_group = QGroupBox("Add Major Purchase")
        add_purchase_layout = QFormLayout()

        self.purchase_name_input = QLineEdit()

        self.purchase_year_input = QSpinBox()
        self.purchase_year_input.setRange(self.planner.current_year, 2100)
        self.purchase_year_input.setValue(self.planner.current_year)

        self.purchase_amount_input = QDoubleSpinBox()
        self.purchase_amount_input.setRange(0, 10000000)
        self.purchase_amount_input.setPrefix("$")

        self.financing_years_input = QSpinBox()
        self.financing_years_input.setRange(0, 30)

        self.interest_rate_input = QDoubleSpinBox()
        self.interest_rate_input.setRange(0, 20)
        self.interest_rate_input.setSuffix("%")
        self.interest_rate_input.setDecimals(2)

        add_purchase_layout.addRow("Name:", self.purchase_name_input)
        add_purchase_layout.addRow("Year:", self.purchase_year_input)
        add_purchase_layout.addRow("Amount:", self.purchase_amount_input)
        add_purchase_layout.addRow("Financing Years (0 for cash):", self.financing_years_input)
        add_purchase_layout.addRow("Interest Rate:", self.interest_rate_input)

        add_purchase_button = QPushButton("Add Purchase")
        add_purchase_button.clicked.connect(self.add_purchase)
        add_purchase_layout.addRow(add_purchase_button)

        add_purchase_group.setLayout(add_purchase_layout)
        layout.addWidget(add_purchase_group)

        # Purchases table
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(6)
        self.purchases_table.setHorizontalHeaderLabels([
            "Name", "Year", "Amount", "Financing Years", "Interest Rate", "Action"
        ])
        layout.addWidget(self.purchases_table)

        self.refresh_purchases_table()

        return tab

    def setup_results_tab(self) -> QWidget:
        """Set up the results visualization tab."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Scenario selection
            scenario_group = QGroupBox("Projection Settings")
            scenario_layout = QFormLayout()

            self.scenario_combo = QComboBox()
            self.scenario_combo.addItems(list(self.planner.scenario_params.scenarios.keys()))

            scenario_layout.addRow("Scenario:", self.scenario_combo)

            # Chart display options
            display_group = QGroupBox("Chart Display Options")
            display_layout = QFormLayout()

            # Net worth scale settings
            self.auto_scale_checkbox = QCheckBox("Auto-scale")
            self.auto_scale_checkbox.setChecked(True)
            self.auto_scale_checkbox.stateChanged.connect(self.toggle_net_worth_scale_inputs)

            self.min_net_worth_input = QDoubleSpinBox()
            self.min_net_worth_input.setRange(-10000000, 10000000)
            self.min_net_worth_input.setPrefix("$")
            self.min_net_worth_input.setSingleStep(10000)
            self.min_net_worth_input.setValue(0)
            self.min_net_worth_input.setEnabled(False)

            self.max_net_worth_input = QDoubleSpinBox()
            self.max_net_worth_input.setRange(0, 100000000)
            self.max_net_worth_input.setPrefix("$")
            self.max_net_worth_input.setSingleStep(100000)
            self.max_net_worth_input.setValue(1000000)
            self.max_net_worth_input.setEnabled(False)

            # Inflation normalization toggle
            self.normalize_inflation_checkbox = QCheckBox("Normalize to today's dollars")
            self.normalize_inflation_checkbox.setChecked(False)

            # Variability settings
            self.enable_variability_checkbox = QCheckBox("Enable Variability Bands")
            self.enable_variability_checkbox.setChecked(False)
            self.enable_variability_checkbox.stateChanged.connect(self.toggle_variability_inputs)

            self.upside_variability_input = QDoubleSpinBox()
            self.upside_variability_input.setRange(0, 100)
            self.upside_variability_input.setSingleStep(1)
            self.upside_variability_input.setValue(10)
            self.upside_variability_input.setSuffix("%")
            self.upside_variability_input.setEnabled(False)

            self.downside_variability_input = QDoubleSpinBox()
            self.downside_variability_input.setRange(0, 100)
            self.downside_variability_input.setSingleStep(1)
            self.downside_variability_input.setValue(10)
            self.downside_variability_input.setSuffix("%")
            self.downside_variability_input.setEnabled(False)

            display_layout.addRow("Auto-scale Y-axis:", self.auto_scale_checkbox)
            display_layout.addRow("Minimum Net Worth:", self.min_net_worth_input)
            display_layout.addRow("Maximum Net Worth:", self.max_net_worth_input)
            display_layout.addRow("Inflation Adjustment:", self.normalize_inflation_checkbox)
            display_layout.addRow("", QLabel(""))  # Spacer
            display_layout.addRow(self.enable_variability_checkbox)
            display_layout.addRow("Upside Variability:", self.upside_variability_input)
            display_layout.addRow("Downside Variability:", self.downside_variability_input)

            display_group.setLayout(display_layout)

            run_projection_button = QPushButton("Run Projection")
            run_projection_button.clicked.connect(self.run_projection)
            scenario_layout.addRow(run_projection_button)

            scenario_group.setLayout(scenario_layout)
            layout.addWidget(scenario_group)
            layout.addWidget(display_group)

            # Canvas for matplotlib figure
            self.figure = Figure(figsize=(10, 6))
            self.canvas = FigureCanvasQTAgg(self.figure)
            layout.addWidget(self.canvas)

            logger.debug("Results tab setup complete")
            return tab
        except Exception as e:
            logger.error(f"Error in setup_results_tab: {e}")
            logger.error(traceback.format_exc())
            # Create a minimal fallback tab
            error_tab = QWidget()
            error_layout = QVBoxLayout(error_tab)
            error_label = QLabel(f"Error setting up Results tab: {str(e)}")
            error_layout.addWidget(error_label)
            return error_tab

    def toggle_net_worth_scale_inputs(self, state):
        """Enable or disable net worth scale inputs based on auto-scale checkbox."""
        enabled = not bool(state)
        self.min_net_worth_input.setEnabled(enabled)
        self.max_net_worth_input.setEnabled(enabled)

    def toggle_variability_inputs(self, state):
        """Enable or disable variability inputs based on checkbox."""
        enabled = bool(state)
        self.upside_variability_input.setEnabled(enabled)
        self.downside_variability_input.setEnabled(enabled)

    def setup_monte_carlo_tab(self) -> QWidget:
        """Set up the Monte Carlo simulation tab."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Simulation settings
            mc_group = QGroupBox("Monte Carlo Settings")
            mc_layout = QFormLayout()

            self.mc_scenario_combo = QComboBox()
            self.mc_scenario_combo.addItems(list(self.planner.scenario_params.scenarios.keys()))

            self.num_simulations_input = QSpinBox()
            self.num_simulations_input.setRange(100, 10000)
            self.num_simulations_input.setSingleStep(100)
            self.num_simulations_input.setValue(500)  # Default to safer value

            # Inflation normalization toggle
            self.mc_normalize_inflation_checkbox = QCheckBox("Normalize to today's dollars")
            self.mc_normalize_inflation_checkbox.setChecked(False)

            mc_layout.addRow("Base Scenario:", self.mc_scenario_combo)
            mc_layout.addRow("Number of Simulations:", self.num_simulations_input)
            mc_layout.addRow("Inflation Adjustment:", self.mc_normalize_inflation_checkbox)

            # Add warning label
            warning_label = QLabel(
                "Note: Monte Carlo simulations are memory-intensive. If you experience crashes, try reducing the number of simulations.")
            warning_label.setStyleSheet("color: red;")

            run_mc_button = QPushButton("Run Monte Carlo Simulation")
            run_mc_button.clicked.connect(self.run_monte_carlo)
            mc_layout.addRow(run_mc_button)

            mc_group.setLayout(mc_layout)
            layout.addWidget(mc_group)
            layout.addWidget(warning_label)

            # Canvas for Monte Carlo visualization
            self.mc_figure = Figure(figsize=(10, 6))
            self.mc_canvas = FigureCanvasQTAgg(self.mc_figure)
            layout.addWidget(self.mc_canvas)

            logger.debug("Monte Carlo tab setup complete")
            return tab
        except Exception as e:
            logger.error(f"Error in setup_monte_carlo_tab: {e}")
            logger.error(traceback.format_exc())
            # Create a minimal fallback tab
            error_tab = QWidget()
            error_layout = QVBoxLayout(error_tab)
            error_label = QLabel(f"Error setting up Monte Carlo tab: {str(e)}")
            error_layout.addWidget(error_label)
            return error_tab

    def add_child(self):
        """Add a new child to the planner."""
        try:
            name = self.child_name_input.text()
            birth_year = self.child_birth_year_input.value()
            template_name = self.child_template_combo.currentText()

            if not name:
                QMessageBox.warning(self, "Warning", "Child name is required")
                return

            if not template_name:
                QMessageBox.warning(self, "Warning", "Please create a child template first")
                return

            # Find the selected template
            template = next((t for t in self.planner.child_templates if t.name == template_name), None)
            if not template:
                QMessageBox.warning(self, "Warning", "Selected template not found")
                return

            # Check for duplicate child names
            if any(c.name == name for c in self.planner.children):
                QMessageBox.warning(self, "Warning", f"A child named '{name}' already exists. Please use a different name.")
                return

            # Create and add the child
            child = Child(name=name, birth_year=birth_year, template=template)
            self.planner.children.append(child)

            # Update the UI
            self.refresh_children_table()
            self.child_name_input.clear()

            logger.debug(f"Added child: {name}")
        except Exception as e:
            logger.error(f"Error adding child: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add child: {str(e)}")

    def refresh_children_table(self):
        """Refresh the children table with current data."""
        try:
            if not hasattr(self, 'children_table'):
                return

            self.children_table.setRowCount(0)
            for child in self.planner.children:
                row = self.children_table.rowCount()
                self.children_table.insertRow(row)

                self.children_table.setItem(row, 0, QTableWidgetItem(child.name))
                self.children_table.setItem(row, 1, QTableWidgetItem(str(child.birth_year)))
                self.children_table.setItem(row, 2, QTableWidgetItem(child.template.name))

                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, c=child: self.delete_child(c))
                self.children_table.setCellWidget(row, 3, delete_btn)
        except Exception as e:
            logger.error(f"Error refreshing children table: {e}")

    def delete_child(self, child):
        """Remove a child from the planner."""
        try:
            self.planner.children.remove(child)
            self.refresh_children_table()
            logger.debug(f"Deleted child: {child.name}")
        except Exception as e:
            logger.error(f"Error deleting child: {e}")

    def add_purchase(self):
        """Add a new major purchase."""
        try:
            name = self.purchase_name_input.text()
            year = self.purchase_year_input.value()
            amount = self.purchase_amount_input.value()
            financing_years = self.financing_years_input.value()
            interest_rate = self.interest_rate_input.value() / 100  # Convert from percentage

            if not name:
                QMessageBox.warning(self, "Warning", "Purchase name is required")
                return

            # Create and add the purchase
            purchase = MajorPurchase(
                name=name,
                year=year,
                amount=amount,
                financing_years=financing_years,
                interest_rate=interest_rate
            )

            self.planner.major_purchases.append(purchase)

            # Update UI
            self.refresh_purchases_table()
            self.clear_purchase_inputs()

            logger.debug(f"Added purchase: {name}, ${amount}")
        except Exception as e:
            logger.error(f"Error adding purchase: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add purchase: {str(e)}")

    def clear_purchase_inputs(self):
        """Clear major purchase input fields."""
        self.purchase_name_input.clear()
        self.purchase_amount_input.setValue(0)
        self.financing_years_input.setValue(0)
        self.interest_rate_input.setValue(0)

    def refresh_purchases_table(self):
        """Refresh the purchases table with current data."""
        try:
            if not hasattr(self, 'purchases_table'):
                return

            self.purchases_table.setRowCount(0)
            for purchase in self.planner.major_purchases:
                row = self.purchases_table.rowCount()
                self.purchases_table.insertRow(row)

                self.purchases_table.setItem(row, 0, QTableWidgetItem(purchase.name))
                self.purchases_table.setItem(row, 1, QTableWidgetItem(str(purchase.year)))
                self.purchases_table.setItem(row, 2, QTableWidgetItem(format_currency(purchase.amount)))
                self.purchases_table.setItem(row, 3, QTableWidgetItem(str(purchase.financing_years)))
                self.purchases_table.setItem(row, 4, QTableWidgetItem(f"{purchase.interest_rate * 100:.2f}%"))

                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, p=purchase: self.delete_purchase(p))
                self.purchases_table.setCellWidget(row, 5, delete_btn)
        except Exception as e:
            logger.error(f"Error refreshing purchases table: {e}")

    def delete_purchase(self, purchase):
        """Remove a purchase from the planner."""
        try:
            self.planner.major_purchases.remove(purchase)
            self.refresh_purchases_table()
            logger.debug(f"Deleted purchase: {purchase.name}")
        except Exception as e:
            logger.error(f"Error deleting purchase: {e}")

    def add_person(self):
        """Add a new person to the planner."""
        try:
            name = self.person_name_input.text()
            birth_year = self.birth_year_input.value()
            base_income = self.base_income_input.value()
            income_growth = self.income_growth_input.value()
            retirement_age = self.retirement_age_input.value()
            death_age = self.death_age_input.value()
            filing_status = self.filing_status_input.currentText()
            state_tax = self.state_tax_input.value()

            if not name:
                QMessageBox.warning(self, "Warning", "Person name is required")
                return

            # Create and add the person
            person = Person(
                name=name,
                birth_year=birth_year,
                base_income=base_income,
                income_growth_rate=income_growth,
                retirement_age=retirement_age,
                death_age=death_age,
                filing_status=filing_status,
                state_tax_rate=state_tax
            )

            self.planner.persons.append(person)

            # Update UI
            self.refresh_persons_table()
            self.update_person_dropdown()
            self.person_name_input.clear()
            self.base_income_input.setValue(0)

            logger.debug(f"Added person: {name}")
        except Exception as e:
            logger.error(f"Error adding person: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add person: {str(e)}")

    def update_person_dropdown(self):
        """Update the person dropdown for income changes."""
        try:
            current_text = self.income_change_person_combo.currentText()

            self.income_change_person_combo.clear()
            for person in self.planner.persons:
                self.income_change_person_combo.addItem(person.name)

            # Try to restore previous selection
            index = self.income_change_person_combo.findText(current_text)
            if index >= 0:
                self.income_change_person_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error updating person dropdown: {e}")

    def add_income_change(self):
        """Add an income change for a person."""
        try:
            person_name = self.income_change_person_combo.currentText()
            year = self.income_change_year_input.value()
            amount = self.income_change_amount_input.value()

            if not person_name:
                QMessageBox.warning(self, "Warning", "Please add a person first")
                return

            # Find the person
            person = next((p for p in self.planner.persons if p.name == person_name), None)
            if not person:
                QMessageBox.warning(self, "Warning", "Selected person not found")
                return

            # Add the income change
            person.income_changes[year] = amount

            # Update UI
            QMessageBox.information(
                self,
                "Success",
                f"Income change added: {person_name} will earn {format_currency(amount)} starting in {year}"
            )
            self.income_change_amount_input.setValue(0)

            logger.debug(f"Added income change for {person_name}, year: {year}, amount: ${amount}")
        except Exception as e:
            logger.error(f"Error adding income change: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add income change: {str(e)}")

    def refresh_persons_table(self):
        """Refresh the persons table with current data."""
        try:
            self.persons_table.setRowCount(0)
            for person in self.planner.persons:
                row = self.persons_table.rowCount()
                self.persons_table.insertRow(row)

                self.persons_table.setItem(row, 0, QTableWidgetItem(person.name))
                self.persons_table.setItem(row, 1, QTableWidgetItem(str(person.birth_year)))
                self.persons_table.setItem(row, 2, QTableWidgetItem(format_currency(person.base_income)))
                self.persons_table.setItem(row, 3, QTableWidgetItem(f"{person.income_growth_rate * 100:.1f}%"))
                self.persons_table.setItem(row, 4, QTableWidgetItem(str(person.retirement_age)))
                self.persons_table.setItem(row, 5, QTableWidgetItem(str(person.death_age)))
                self.persons_table.setItem(row, 6, QTableWidgetItem(person.filing_status))
                self.persons_table.setItem(row, 7, QTableWidgetItem(f"{person.state_tax_rate * 100:.1f}%"))

                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, p=person: self.delete_person(p))
                self.persons_table.setCellWidget(row, 8, delete_btn)
        except Exception as e:
            logger.error(f"Error refreshing persons table: {e}")

    def delete_person(self, person):
        """Remove a person from the planner."""
        try:
            self.planner.persons.remove(person)
            self.refresh_persons_table()
            self.update_person_dropdown()
            logger.debug(f"Deleted person: {person.name}")
        except Exception as e:
            logger.error(f"Error deleting person: {e}")

    def update_basic_info(self):
        """Update basic household information."""
        try:
            self.planner.current_year = self.current_year_input.value()
            self.planner.yearly_expenses = self.yearly_expenses_input.value()
            self.planner.healthcare_expenses = self.healthcare_expenses_input.value()

            # Net worth is now handled in the partner tabs

            QMessageBox.information(self, "Success", "Basic information updated")
            logger.debug("Updated basic information")
        except Exception as e:
            logger.error(f"Error updating basic info: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update basic information: {str(e)}")

    def update_ss_settings(self):
        """Update Social Security insolvency settings."""
        try:
            self.planner.scenario_params.ss_insolvency_enabled = self.ss_insolvency_enabled.isChecked()
            self.planner.scenario_params.ss_insolvency_year = self.ss_insolvency_year_input.value()
            self.planner.scenario_params.ss_shortfall_rate = self.ss_shortfall_rate_input.value()

            QMessageBox.information(self, "Success", "Social Security settings updated")
            logger.debug(f"Updated SS settings: enabled={self.planner.scenario_params.ss_insolvency_enabled}, "
                        f"year={self.planner.scenario_params.ss_insolvency_year}, "
                        f"shortfall={self.planner.scenario_params.ss_shortfall_rate}")
        except Exception as e:
            logger.error(f"Error updating SS settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update Social Security settings: {str(e)}")

    def get_scenarios_directory(self):
        """Get or create the scenarios directory."""
        import os
        scenarios_dir = Path.home() / ".financial_planner" / "scenarios"
        scenarios_dir.mkdir(parents=True, exist_ok=True)
        return scenarios_dir

    def refresh_scenarios_library(self):
        """Refresh the list of saved scenarios."""
        try:
            self.saved_scenarios_list.clear()
            scenarios_dir = self.get_scenarios_directory()

            # List all .json files in the scenarios directory
            for scenario_file in scenarios_dir.glob("*.json"):
                scenario_name = scenario_file.stem  # Filename without extension
                self.saved_scenarios_list.addItem(scenario_name)

            logger.debug(f"Refreshed scenarios library with {self.saved_scenarios_list.count()} scenarios")
        except Exception as e:
            logger.error(f"Error refreshing scenarios library: {e}")

    def save_named_scenario(self):
        """Save the current scenario with a user-provided name."""
        try:
            scenario_name = self.scenario_name_input.text().strip()

            if not scenario_name:
                QMessageBox.warning(self, "Warning", "Please enter a scenario name")
                return

            # Validate scenario name (no special characters)
            import re
            if not re.match(r'^[\w\s-]+$', scenario_name):
                QMessageBox.warning(self, "Warning",
                                  "Scenario name can only contain letters, numbers, spaces, hyphens, and underscores")
                return

            scenarios_dir = self.get_scenarios_directory()
            filename = scenarios_dir / f"{scenario_name}.json"

            # Check if scenario already exists
            if filename.exists():
                reply = QMessageBox.question(
                    self,
                    "Overwrite Scenario",
                    f"Scenario '{scenario_name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # Save the scenario
            self.planner.save_scenario(str(filename))

            QMessageBox.information(self, "Success", f"Scenario '{scenario_name}' saved successfully")
            logger.debug(f"Saved named scenario: {scenario_name}")

            # Clear the input and refresh the list
            self.scenario_name_input.clear()
            self.refresh_scenarios_library()

        except Exception as e:
            logger.error(f"Error saving named scenario: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save scenario: {str(e)}")

    def load_selected_scenario(self):
        """Load the selected scenario from the library."""
        try:
            selected_items = self.saved_scenarios_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a scenario to load")
                return

            scenario_name = selected_items[0].text()
            scenarios_dir = self.get_scenarios_directory()
            filename = scenarios_dir / f"{scenario_name}.json"

            if not filename.exists():
                QMessageBox.warning(self, "Error", f"Scenario file not found: {scenario_name}")
                return

            # Load the scenario
            loaded_planner = FinancialPlanner.load_scenario(str(filename))

            if loaded_planner:
                self.planner = loaded_planner

                # Refresh all UI elements
                self.current_year_input.setValue(self.planner.current_year)
                self.yearly_expenses_input.setValue(self.planner.yearly_expenses)
                self.healthcare_expenses_input.setValue(self.planner.healthcare_expenses)

                # Refresh partner data
                self.refresh_partner_data("X")
                self.refresh_partner_data("Y")

                QMessageBox.information(self, "Success", f"Scenario '{scenario_name}' loaded successfully")
                logger.debug(f"Loaded scenario from library: {scenario_name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load scenario")

        except Exception as e:
            logger.error(f"Error loading selected scenario: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load scenario: {str(e)}")

    def delete_selected_scenario(self):
        """Delete the selected scenario from the library."""
        try:
            selected_items = self.saved_scenarios_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a scenario to delete")
                return

            scenario_name = selected_items[0].text()

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Delete Scenario",
                f"Are you sure you want to delete scenario '{scenario_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            scenarios_dir = self.get_scenarios_directory()
            filename = scenarios_dir / f"{scenario_name}.json"

            if filename.exists():
                filename.unlink()  # Delete the file
                QMessageBox.information(self, "Success", f"Scenario '{scenario_name}' deleted")
                logger.debug(f"Deleted scenario: {scenario_name}")
                self.refresh_scenarios_library()
            else:
                QMessageBox.warning(self, "Error", f"Scenario file not found: {scenario_name}")

        except Exception as e:
            logger.error(f"Error deleting scenario: {e}")
            QMessageBox.warning(self, "Error", f"Failed to delete scenario: {str(e)}")

    def run_projection(self):
        """Run financial projection and display results."""
        try:
            logger.debug("Starting financial projection")
            # Show wait cursor
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            scenario_name = self.scenario_combo.currentText()
            results = self.planner.calculate_projection(scenario_name)

            # Clear the figure
            self.figure.clear()

            # Create subplots
            ax1 = self.figure.add_subplot(211)  # Net worth
            ax2 = self.figure.add_subplot(212)  # Income and expenses

            # Extract data
            years = [r['year'] for r in results]
            net_worth = [r['net_worth'] for r in results]
            income = [r['total_income'] for r in results]
            expenses = [r['total_expenses'] for r in results]

            # Apply inflation normalization if checkbox is checked
            if self.normalize_inflation_checkbox.isChecked():
                scenario_params = self.planner.scenario_params.scenarios[scenario_name]
                inflation_rate = scenario_params['inflation_rate']
                current_year = self.planner.current_year

                # Convert to real dollars (purchasing power in today's dollars)
                net_worth = [nw / ((1 + inflation_rate) ** (year - current_year))
                            for year, nw in zip(years, net_worth)]
                income = [inc / ((1 + inflation_rate) ** (year - current_year))
                         for year, inc in zip(years, income)]
                expenses = [exp / ((1 + inflation_rate) ** (year - current_year))
                           for year, exp in zip(years, expenses)]

                dollar_label = "Real Dollars (Today's Purchasing Power)"
            else:
                dollar_label = "Nominal Dollars"

            # Calculate and plot variability bands if enabled
            if self.enable_variability_checkbox.isChecked():
                upside_pct = self.upside_variability_input.value() / 100.0
                downside_pct = self.downside_variability_input.value() / 100.0

                # Calculate best case (upside variability)
                best_case_net_worth = []
                # Calculate worst case (downside variability)
                worst_case_net_worth = []

                for i, year in enumerate(years):
                    base_value = results[i]['net_worth']
                    # Apply asymmetric variability
                    best_case = base_value * (1 + upside_pct)
                    worst_case = base_value * (1 - downside_pct)

                    # Apply inflation normalization if enabled
                    if self.normalize_inflation_checkbox.isChecked():
                        year_offset = year - current_year
                        inflation_factor = ((1 + inflation_rate) ** year_offset)
                        best_case = best_case / inflation_factor
                        worst_case = worst_case / inflation_factor

                    best_case_net_worth.append(best_case)
                    worst_case_net_worth.append(worst_case)

                # Plot variability bands as shaded regions
                ax1.fill_between(years, worst_case_net_worth, best_case_net_worth,
                                alpha=0.2, color='blue', label='Variability Range')
                ax1.plot(years, best_case_net_worth, 'b--', linewidth=1, alpha=0.5, label='Best Case')
                ax1.plot(years, worst_case_net_worth, 'b--', linewidth=1, alpha=0.5, label='Worst Case')

            # Plot net worth with custom scale if specified
            ax1.plot(years, net_worth, 'b-', linewidth=2, label='Expected')
            ax1.set_title('Net Worth Projection')
            ax1.set_ylabel(f'Net Worth ({dollar_label})')
            ax1.legend(loc='best')
            ax1.grid(True)

            # Apply custom scale if auto-scale is not checked
            if not self.auto_scale_checkbox.isChecked():
                min_value = self.min_net_worth_input.value()
                max_value = self.max_net_worth_input.value()
                ax1.set_ylim(min_value, max_value)

                # Add note about custom scale
                ax1.text(0.02, 0.98, 'Custom scale', transform=ax1.transAxes,
                         verticalalignment='top', fontsize=8, color='gray')
            else:
                # Add padding to auto scale
                min_val = min(net_worth)
                max_val = max(net_worth)
                padding = (max_val - min_val) * 0.1  # 10% padding
                ax1.set_ylim(min_val - padding, max_val + padding)

                # Update the scale inputs with the auto values (but don't trigger their events)
                self.min_net_worth_input.blockSignals(True)
                self.max_net_worth_input.blockSignals(True)
                self.min_net_worth_input.setValue(min_val - padding)
                self.max_net_worth_input.setValue(max_val + padding)
                self.min_net_worth_input.blockSignals(False)
                self.max_net_worth_input.blockSignals(False)

            # Format y-axis with dollar sign and commas
            ax1.get_yaxis().set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, p: f'${x:,.0f}')
            )

            # Plot income and expenses
            ax2.plot(years, income, 'g-', label='Income')
            ax2.plot(years, expenses, 'r-', label='Expenses')
            ax2.set_title('Income and Expenses Projection')
            ax2.set_xlabel('Year')
            ax2.set_ylabel(f'Amount ({dollar_label})')
            ax2.legend()
            ax2.grid(True)

            # Format y-axis with dollar sign and commas
            ax2.get_yaxis().set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, p: f'${x:,.0f}')
            )

            self.figure.tight_layout()
            self.canvas.draw()

            # Force garbage collection to free memory
            gc.collect()

            # Restore normal cursor
            QApplication.restoreOverrideCursor()
            logger.debug("Projection completed and displayed")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"Error in financial projection: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Error", f"Failed to run projection: {str(e)}")

    def run_monte_carlo(self):
        """Run Monte Carlo simulation and display results."""
        progress_msg = None
        try:
            logger.debug("Starting Monte Carlo simulation")
            # Show wait cursor
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            scenario_name = self.mc_scenario_combo.currentText()
            num_simulations = self.num_simulations_input.value()

            # Memory usage warning
            if num_simulations > 500:
                res = QMessageBox.warning(
                    self,
                    "High Memory Usage Warning",
                    f"Running {num_simulations} simulations may cause the application to crash due to memory limitations. "
                    f"It is recommended to use 500 or fewer simulations.\n\n"
                    f"Would you like to continue with {num_simulations} simulations or reduce to 500?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if res == QMessageBox.StandardButton.No:
                    num_simulations = 500
                    self.num_simulations_input.setValue(500)
                    logger.info(f"Reduced Monte Carlo simulations to 500")

            # Create a non-modal progress dialog with a cancel button
            progress_msg = QDialog(self)
            progress_msg.setWindowTitle("Running Simulation")
            dialog_layout = QVBoxLayout(progress_msg)
            dialog_layout.addWidget(QLabel(f"Running {num_simulations} simulations. This may take a while..."))

            # Add a cancel button
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(progress_msg.reject)
            dialog_layout.addWidget(cancel_btn)

            # Show the dialog without blocking
            progress_msg.setWindowModality(Qt.WindowModality.NonModal)
            progress_msg.show()
            QApplication.processEvents()  # Process UI events to show dialog

            simulation_results = self.planner.run_monte_carlo_simulation(
                scenario_name,
                num_simulations
            )

            # Clear the figure
            self.mc_figure.clear()

            # Create subplot
            ax = self.mc_figure.add_subplot(111)

            # Check if inflation normalization is enabled
            normalize_inflation = self.mc_normalize_inflation_checkbox.isChecked()
            if normalize_inflation:
                scenario_params = self.planner.scenario_params.scenarios[scenario_name]
                inflation_rate = scenario_params['inflation_rate']
                current_year = self.planner.current_year
                dollar_label = "Real Dollars (Today's Purchasing Power)"
            else:
                dollar_label = "Nominal Dollars"

            # Plot all simulation paths with low opacity
            max_year = 0
            min_net_worth = 0
            max_net_worth = 0

            for result in simulation_results['results']:
                years = [r['year'] for r in result]
                net_worth = [r['net_worth'] for r in result]

                # Apply inflation normalization if enabled
                if normalize_inflation:
                    net_worth = [nw / ((1 + inflation_rate) ** (year - current_year))
                                for year, nw in zip(years, net_worth)]

                max_year = max(max_year, years[-1])
                min_net_worth = min(min_net_worth, min(net_worth))
                max_net_worth = max(max_net_worth, max(net_worth))

                ax.plot(years, net_worth, 'b-', alpha=0.05)

            # Plot success rate
            success_rate = simulation_results['success_rate']
            ax.set_title(f'Monte Carlo Simulation: {success_rate:.1f}% Success Rate')
            ax.set_xlabel('Year')
            ax.set_ylabel(f'Net Worth ({dollar_label})')
            ax.grid(True)

            # Add reference lines
            ax.axhline(y=0, color='r', linestyle='-', alpha=0.5)

            # Format y-axis with dollar sign and commas
            ax.get_yaxis().set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, p: f'${x:,.0f}')
            )

            self.mc_figure.tight_layout()
            self.mc_canvas.draw()

            # Force garbage collection to free memory
            gc.collect()

            logger.debug("Monte Carlo simulation completed and displayed")
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Error", f"Failed to run Monte Carlo simulation: {str(e)}")
        finally:
            # Always make sure to close the progress dialog and restore cursor
            if progress_msg is not None:
                progress_msg.close()
                progress_msg.deleteLater()  # Ensure proper cleanup
            QApplication.restoreOverrideCursor()
            # Final UI refresh
            QApplication.processEvents()

    def save_scenario(self):
        """Save the current scenario to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Scenario",
                "",
                "JSON Files (*.json)"
            )
            if filename:
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'

                # Update planner from UI fields
                self.update_planner_from_ui()

                # Save the scenario
                self.planner.save_scenario(filename)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Scenario saved to {filename}"
                )
                logger.debug(f"Scenario saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving scenario: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Error", f"Failed to save scenario: {str(e)}")

    def load_scenario(self):
        """Load a scenario from a file."""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Load Scenario",
                "",
                "JSON Files (*.json)"
            )
            if filename:
                # Load the scenario
                loaded_planner = FinancialPlanner.load_scenario(filename)

                # Replace current planner with loaded one
                self.planner = loaded_planner

                # Update UI
                self.update_ui_from_planner()

                QMessageBox.information(
                    self,
                    "Success",
                    f"Scenario loaded from {filename}"
                )
                logger.debug(f"Scenario loaded from {filename}")
        except Exception as e:
            logger.error(f"Error loading scenario: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Error", f"Failed to load scenario: {str(e)}")

    def update_planner_from_ui(self):
        """Update planner object with all current UI values."""
        try:
            # Update basic info
            self.planner.current_year = self.current_year_input.value()
            self.planner.current_net_worth = self.net_worth_input.value()
            self.planner.yearly_expenses = self.yearly_expenses_input.value()
            self.planner.healthcare_expenses = self.healthcare_expenses_input.value()

            logger.debug("Updated planner from UI")
        except Exception as e:
            logger.error(f"Error updating planner from UI: {e}")
            raise

    def update_ui_from_planner(self):
        """Update all UI elements to reflect current planner state."""
        try:
            # Update basic info fields
            self.current_year_input.setValue(self.planner.current_year)
            self.yearly_expenses_input.setValue(self.planner.yearly_expenses)
            self.healthcare_expenses_input.setValue(self.planner.healthcare_expenses)

            # Distribute initial net worth between partners
            # Wait until partner tabs are fully initialized
            QApplication.processEvents()

            # Update partner tabs
            if hasattr(self, "partner_x_net_worth_input") and hasattr(self, "partner_y_net_worth_input"):
                # Divide net worth equally if loading a file that doesn't have per-partner net worth
                self.partner_x_net_worth_input.setValue(self.planner.current_net_worth * 0.5)
                self.partner_y_net_worth_input.setValue(self.planner.current_net_worth * 0.5)

            # Refresh partner data - make sure this happens after all UI elements are created
            QApplication.processEvents()
            self.refresh_partner_data("X")
            self.refresh_partner_data("Y")

            # Refresh all other tables
            self.refresh_children_table()
            self.refresh_templates_table()
            self.refresh_purchases_table()

            # Update dropdown menus
            self.update_template_dropdown()

            logger.debug("Updated UI from planner")
        except Exception as e:
            logger.error(f"Error updating UI from planner: {e}")
            logger.error(traceback.format_exc())

    def compare_scenarios(self):
        """Open dialog to compare multiple scenarios."""
        try:
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Compare Scenarios")
            dialog.setMinimumWidth(600)

            layout = QVBoxLayout(dialog)

            # Create scenario selection list
            label = QLabel("Select scenarios to compare:")
            layout.addWidget(label)

            scenario_list = QListWidget()
            scenario_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            layout.addWidget(scenario_list)

            # Get saved scenarios from manager
            saved_scenarios = self.scenario_manager.list_scenarios()
            for scenario in saved_scenarios:
                scenario_list.addItem(scenario)

            # Add current scenario option
            current_item = QListWidgetItem("Current (Unsaved)")
            current_item.setData(Qt.ItemDataRole.UserRole, "current")
            scenario_list.addItem(current_item)

            # Buttons
            buttons_layout = QHBoxLayout()
            compare_button = QPushButton("Compare")
            cancel_button = QPushButton("Cancel")
            buttons_layout.addWidget(compare_button)
            buttons_layout.addWidget(cancel_button)
            layout.addLayout(buttons_layout)

            # Connect buttons
            cancel_button.clicked.connect(dialog.reject)
            compare_button.clicked.connect(dialog.accept)

            # Show dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_items = scenario_list.selectedItems()
                selected_scenarios = []

                for item in selected_items:
                    # Check if it's the current scenario
                    if item.data(Qt.ItemDataRole.UserRole) == "current":
                        # Save current to temporary scenario
                        self.update_planner_from_ui()
                        self.scenario_manager.add_scenario("__current__", self.planner)
                        selected_scenarios.append("__current__")
                    else:
                        selected_scenarios.append(item.text())

                if len(selected_scenarios) < 2:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Please select at least 2 scenarios to compare"
                    )
                    # Remove temporary scenario if it exists
                    if "__current__" in self.scenario_manager.scenarios:
                        del self.scenario_manager.scenarios["__current__"]
                    return

                # Compare the scenarios
                comparison = self.scenario_manager.compare_scenarios(selected_scenarios)

                # Remove temporary scenario if it exists
                if "__current__" in self.scenario_manager.scenarios:
                    del self.scenario_manager.scenarios["__current__"]

                # Show results in a new dialog
                self.show_comparison_results(comparison)

        except Exception as e:
            logger.error(f"Error in scenario comparison: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "Error", f"Failed to compare scenarios: {str(e)}")

    def show_comparison_results(self, comparison):
        """Show scenario comparison results."""
        try:
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Scenario Comparison Results")
            dialog.setMinimumSize(800, 600)

            layout = QVBoxLayout(dialog)

            # Create table
            results_table = QTableWidget()
            results_table.setColumnCount(5)
            results_table.setHorizontalHeaderLabels([
                "Scenario", "Ending Net Worth", "Minimum Net Worth",
                "Maximum Annual Expense", "Total Retirement Income"
            ])

            # Populate table
            for row, (scenario, data) in enumerate(comparison.items()):
                # Replace "__current__" with "Current (Unsaved)"
                display_name = "Current (Unsaved)" if scenario == "__current__" else scenario

                results_table.insertRow(row)
                results_table.setItem(row, 0, QTableWidgetItem(display_name))
                results_table.setItem(row, 1, QTableWidgetItem(format_currency(data['ending_net_worth'])))
                results_table.setItem(row, 2, QTableWidgetItem(format_currency(data['min_net_worth'])))
                results_table.setItem(row, 3, QTableWidgetItem(format_currency(data['max_annual_expense'])))
                results_table.setItem(row, 4, QTableWidgetItem(format_currency(data['retirement_income'])))

            layout.addWidget(results_table)

            # Add close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            # Show dialog
            dialog.exec()

        except Exception as e:
            logger.error(f"Error showing comparison results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to display comparison results: {str(e)}")


def create_sample_scenario():
    """Create a sample financial scenario for testing."""
    try:
        # Create some persons
        person1 = Person(
            name="John Doe",
            birth_year=1980,
            base_income=85000,
            income_growth_rate=0.03,
            retirement_age=65,
            filing_status='single',
            state_tax_rate=0.05
        )

        person2 = Person(
            name="Jane Smith",
            birth_year=1982,
            base_income=92000,
            income_growth_rate=0.025,
            retirement_age=62,
            filing_status='married',
            state_tax_rate=0.05
        )

        # Create a child template
        default_expenses = ChildTemplate.get_default_expenses()

        template = ChildTemplate(
            name="Standard Child",
            yearly_expenses=default_expenses
        )

        # Create a child
        child = Child(
            name="Emily",
            birth_year=2021,
            template=template
        )

        # Create major purchases
        purchase1 = MajorPurchase(
            name="Home Renovation",
            year=2025,
            amount=75000,
            financing_years=10,
            interest_rate=0.05
        )

        purchase2 = MajorPurchase(
            name="New Car",
            year=2026,
            amount=45000,
            financing_years=5,
            interest_rate=0.04
        )

        # Create planner with all components
        planner = FinancialPlanner(
            persons=[person1, person2],
            children=[child],
            current_year=2024,
            current_net_worth=350000,
            yearly_expenses=72000,
            major_purchases=[purchase1, purchase2],
            child_templates=[template]
        )

        return planner

    except Exception as e:
        logger.error(f"Error creating sample scenario: {e}")
        return None


def main():
    """Main application entry point."""
    try:
        logger.info("Starting Financial Planner application")
        app = QApplication(sys.argv)

        # Create initial planner
        try:
            # First try to load default scenario if it exists
            default_path = Path.home() / "financial_planner_default.json"
            if default_path.exists():
                logger.info(f"Loading default scenario from {default_path}")
                planner = FinancialPlanner.load_scenario(str(default_path))
            else:
                # If no default exists, create a simple scenario
                logger.info("Creating simple default scenario")
                # Create a person
                person = Person(
                    name="Sample Person",
                    birth_year=1980,
                    base_income=75000,
                    income_growth_rate=0.03,
                    retirement_age=65,
                    filing_status='single',
                    state_tax_rate=0.05
                )

                # Create planner with minimal components
                planner = FinancialPlanner(
                    persons=[person],
                    children=[],
                    current_year=date.today().year,
                    current_net_worth=100000,
                    yearly_expenses=50000
                )
        except Exception as e:
            logger.error(f"Error setting up initial planner: {e}")
            logger.error(traceback.format_exc())

            # Fall back to minimal planner
            logger.info("Creating minimal planner due to error")
            planner = FinancialPlanner(
                persons=[],
                children=[],
                current_year=date.today().year,
                current_net_worth=0,
                yearly_expenses=0
            )

        # Create and show the main window
        main_window = FinancialPlannerGUI(planner)
        main_window.show()

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        logger.critical(traceback.format_exc())

        # Try to show error dialog if QApplication is already running
        try:
            if QApplication.instance():
                QMessageBox.critical(
                    None,
                    "Fatal Error",
                    f"A fatal error occurred: {str(e)}\n\nPlease check the log file for details."
                )
        except:
            # If that fails too, just print to console
            print(f"FATAL ERROR: {str(e)}")
            print(traceback.format_exc())

        sys.exit(1)


# Make sure this is at the very end of your file
if __name__ == "__main__":
    main()
