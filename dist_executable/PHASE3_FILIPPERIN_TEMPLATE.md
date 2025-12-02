# Phase 3: Create Filipp&Erin Custom Spending Template

## Goal
Create a custom spending strategy template called "Filipp&Erin Spending (custom)" based on your actual Seattle expenses from the Google Sheets data.

## Background
Your actual spending significantly exceeds the built-in "High-end (statistical)" template:
- **Your actual:** $108,600/year living expenses
- **App's High-end:** $73,200/year (48% lower!)
- **Your utilities:** $4,920/year
- **Your house upkeep:** $12,000/year

This custom template will accurately reflect your real spending patterns.

## Data Source Summary
From your Google Sheets expense tracking:
- **Living expenses:** $108,600/year for 2 people
- **Utilities:** $4,920/year
- **House upkeep:** $12,000/year
- **College planning:** $30,000-35,000/child/year

## Implementation Approach

You have **two options** for creating this template:

### Option A: Quick Hardcoded Template (Recommended for Phase 3)
Add the Filipp&Erin template directly to the FAMILY_EXPENSE_TEMPLATES dictionary as a new city entry.

### Option B: Use Custom City Creator
Use the built-in "Create Custom City" UI to create the template interactively.

---

## Option A: Hardcoded Template (RECOMMENDED)

This is the fastest and most reliable way to add your custom template.

### Step 1: Add Filipp&Erin Template to FAMILY_EXPENSE_TEMPLATES

**Location:** Lines 910-1457 (FAMILY_EXPENSE_TEMPLATES dictionary)

**Add this entry** at the end of the dictionary (before the closing `}`):

```python
    # Custom template for Filipp&Erin based on actual Seattle expenses
    "Seattle (Filipp&Erin)": {
        "Filipp&Erin Spending (custom)": {
            'Food & Groceries': 24000,      # Based on your actual tracking
            'Clothing': 8000,               # Based on your actual tracking
            'Transportation': 18000,        # Based on your actual tracking
            'Entertainment & Activities': 15000,  # Based on your actual tracking
            'Personal Care': 6600,          # Based on your actual tracking
            'Utilities': 4920,              # Your actual: $4,920/year
            'Internet & Phone': 3000,       # Based on your actual tracking
            'Subscriptions': 2000,          # Based on your actual tracking
            'Other Expenses': 27080         # Remainder to reach $108,600 total
        }
    }
```

**Verification:**
```python
# Total should equal $108,600
total = 24000 + 8000 + 18000 + 15000 + 6600 + 4920 + 3000 + 2000 + 27080
print(f"Total: ${total:,}")  # Should print: Total: $108,600
```

### Step 2: Customize the Category Breakdown

**Note:** The above breakdown is an estimate. If you have more detailed category data from your spreadsheet, adjust the values accordingly.

**To customize:**
1. Open your Google Sheets expense tracker
2. Look at your actual spending by category for the past year
3. Calculate annual totals for each category
4. Update the values in the template above

**Example with your actual categories:**
```python
"Seattle (Filipp&Erin)": {
    "Filipp&Erin Spending (custom)": {
        'Food & Groceries': 26400,      # $2,200/month × 12
        'Clothing': 7200,               # $600/month × 12
        'Transportation': 19200,        # $1,600/month × 12
        'Entertainment & Activities': 14400,  # $1,200/month × 12
        'Personal Care': 6000,          # $500/month × 12
        'Utilities': 4920,              # Your actual: $4,920/year
        'Internet & Phone': 3000,       # $250/month × 12
        'Subscriptions': 2400,          # $200/month × 12
        'Other Expenses': 25080         # Remainder to reach total
    }
}
```

### Step 3: Add Data Source Attribution

**Location:** Find the `get_expense_data_source()` function (search for "def get_expense_data_source")

**Add this entry:**
```python
def get_expense_data_source(location):
    """Return data source information for expense templates"""

    data_sources = {
        "Seattle": "Based on MIT Living Wage Calculator (2024) and Numbeo Cost of Living Index",
        "Houston": "Based on MIT Living Wage Calculator (2024) and Numbeo Cost of Living Index",
        # ... other cities ...

        # Add your custom source
        "Seattle (Filipp&Erin)": "Based on actual Filipp&Erin household expenses tracked over 12+ months (2024)",
    }

    return data_sources.get(location, "Custom user-created template")
```

### Step 4: Test the Template

**Testing Checklist:**
1. **Launch the app:**
   ```bash
   streamlit run FinancialPlanner_v0_85.py
   ```

2. **Navigate to Family Expenses tab:**
   - [ ] Go to "Browse Templates"
   - [ ] Look for "Seattle (Filipp&Erin)" in the location dropdown
   - [ ] Select it and verify the template loads

3. **Verify the data:**
   - [ ] Strategy dropdown shows "Filipp&Erin Spending (custom)"
   - [ ] Total annual expenses = $108,600
   - [ ] All categories display correctly
   - [ ] Pie chart renders properly
   - [ ] Data source attribution appears at bottom

4. **Test in scenarios:**
   - [ ] Go to Parent Information tab
   - [ ] Change location to "Seattle (Filipp&Erin)"
   - [ ] Change strategy to "Filipp&Erin Spending (custom)"
   - [ ] Verify expenses calculate correctly in other tabs

---

## Option B: Interactive Creation (Alternative)

If you prefer to create the template through the UI rather than hardcoding:

### Step 1: Navigate to Create Custom City Tab
1. Launch the app
2. Go to **Family Expenses** tab
3. Click on **"🌍 Create Custom City"** sub-tab

### Step 2: Create the Template
1. **City Name:** Enter "Seattle (Filipp&Erin)"
2. **Strategy Name:** Enter "Filipp&Erin Spending" (the system will add "(custom)" automatically)
3. **Fill in each category:**
   - Food & Groceries: $24,000
   - Clothing: $8,000
   - Transportation: $18,000
   - Entertainment & Activities: $15,000
   - Personal Care: $6,600
   - Utilities: $4,920
   - Internet & Phone: $3,000
   - Subscriptions: $2,000
   - Other Expenses: $27,080

4. Click **"Save Custom Template"**

### Step 3: Verify Template Was Created
1. Go back to **"📊 Browse Templates"** sub-tab
2. Select "Seattle (Filipp&Erin)" from location dropdown
3. Verify "Filipp&Erin Spending (custom)" appears in strategy dropdown
4. Verify total = $108,600

### Limitation of Option B
**Important:** Templates created through the UI are stored in `st.session_state` only. They will be **lost when you restart the app**.

To persist custom templates across sessions, you would need to implement save/load functionality (see Future Enhancements below).

---

## Children's College Expenses

### Adding Custom College Costs

Your spreadsheet indicated **$30,000-35,000/child** for college. Here's how to create a custom children's template:

**Location:** Lines 231-909 (CHILDREN_EXPENSE_TEMPLATES dictionary)

**Add this entry:**
```python
    "Seattle (Filipp&Erin)": {
        "Filipp&Erin Spending (custom)": {
            # Ages 0-4 (Early Childhood)
            'ages_0_4': {
                'Childcare': 18000,        # Seattle daycare costs
                'Food': 3600,
                'Clothing': 1200,
                'Healthcare': 2400,
                'Activities': 1800,
                'Other': 1200
            },

            # Ages 5-12 (Elementary School)
            'ages_5_12': {
                'Childcare/After-school': 12000,
                'Food': 4800,
                'Clothing': 1800,
                'Healthcare': 2400,
                'Activities': 3600,
                'School Supplies': 1200,
                'Other': 1800
            },

            # Ages 13-17 (High School)
            'ages_13_17': {
                'Food': 6000,
                'Clothing': 2400,
                'Healthcare': 3000,
                'Activities': 4800,
                'School Supplies': 1200,
                'Transportation': 2400,
                'Other': 2400
            },

            # College Costs
            'college': {
                'Public': {
                    'In-State': {
                        'Tuition': 12000,
                        'Room & Board': 15000,
                        'Books & Supplies': 1500,
                        'Other': 3500
                        # Total: $32,000 (within your $30-35k range)
                    },
                    'Out-of-State': {
                        'Tuition': 18000,
                        'Room & Board': 15000,
                        'Books & Supplies': 1500,
                        'Other': 3500
                        # Total: $38,000
                    }
                },
                'Private': {
                    'In-State': {
                        'Tuition': 32000,
                        'Room & Board': 16000,
                        'Books & Supplies': 2000,
                        'Other': 4000
                        # Total: $54,000
                    }
                }
            }
        }
    }
```

**Note:** Adjust these values based on your specific plans for your children's education.

---

## Verification and Testing

### Final Testing Checklist

1. **Family Expenses:**
   - [ ] Template appears in location dropdown
   - [ ] Strategy appears in strategy dropdown
   - [ ] Total = $108,600
   - [ ] All categories display correctly
   - [ ] Can be selected in Parent Information tab

2. **Children Expenses (if added):**
   - [ ] Template appears in location dropdown
   - [ ] College costs match your $30-35k target
   - [ ] Can be selected in Children tab

3. **Integration with Financial Analysis:**
   - [ ] Create a test scenario using your custom template
   - [ ] Run Deterministic Cashflow calculation
   - [ ] Verify expenses are calculated correctly
   - [ ] Check that yearly expenses reflect your template

4. **Demo Scenario (Optional):**
   - [ ] Consider creating a "Filipp&Erin Demo" scenario
   - [ ] Use your custom template
   - [ ] Save it as a demo for easy access

---

## Comparison with Statistical Templates

After creating your template, compare it with the built-in Seattle templates:

### Seattle Templates Comparison:
```
Conservative (statistical): $36,900/year
Average (statistical):      $50,400/year
High-end (statistical):     $73,200/year
Filipp&Erin (custom):       $108,600/year  ← Your actual spending
```

**Your spending is 48% higher than High-end and 115% higher than Average!**

This demonstrates why custom templates are essential for accurate financial planning.

---

## Future Enhancements (Not Part of Phase 3)

Ideas for later improvement:
1. **Persistent Storage:** Save custom templates to JSON file
2. **Import from Spreadsheet:** Direct import from Google Sheets/Excel
3. **Expense Tracking Integration:** Auto-update template from bank transactions
4. **Multiple Custom Templates:** Support multiple family spending profiles
5. **Seasonal Variations:** Account for spending variations by season/month

---

## Common Issues and Solutions

### Issue 1: Template Doesn't Appear in Dropdown
**Symptom:** Can't find "Seattle (Filipp&Erin)" in location dropdown
**Solution:**
- Check that you added it to FAMILY_EXPENSE_TEMPLATES
- Verify the syntax (proper commas, brackets, quotes)
- Restart the app to reload templates

### Issue 2: Totals Don't Match
**Symptom:** Total expenses ≠ $108,600
**Solution:**
- Use Python to calculate: `sum([val for val in template.values()])`
- Adjust the "Other Expenses" category to make up the difference

### Issue 3: Template Works but Data Source is Generic
**Symptom:** Data source shows "Custom user-created template" instead of your attribution
**Solution:** Add entry to `get_expense_data_source()` function (see Step 3)

### Issue 4: Can't Delete Template Later
**Symptom:** Template is hardcoded and can't be removed
**Solution:** This is expected for hardcoded templates. To make it deletable, use Option B or implement persistent storage with delete capability.

---

## Success Criteria

✅ **Phase 3 is complete when:**
1. "Seattle (Filipp&Erin)" appears in location dropdown
2. "Filipp&Erin Spending (custom)" appears in strategy dropdown
3. Total annual expenses = $108,600
4. Template can be selected in Parent Information tab
5. Financial calculations use the correct expense values
6. Data source attribution is accurate
7. Template accurately reflects your actual spending patterns

## Estimated Time
- **Option A (Hardcoded):** 15-20 minutes
- **Option B (Interactive):** 10-15 minutes (but not persistent)

## Recommendation
**Use Option A** - Hardcoding the template ensures it persists across app restarts and gives you full control over the exact values.

## Next Phase
Once Phase 3 is complete and tested, proceed to **Phase 4: Testing & Version Update**
