# Phase 1: Tab Reorganization

## Goal
Split the "Analysis & Cashflow" tab into two separate top-level tabs:
1. **💰 Deterministic Lifetime Cashflow** (formerly Section 1)
2. **🎲 Monte Carlo Simulation** (formerly Section 2)

## Current State
- Single tab function: `combined_analysis_cashflow_tab()` (lines 5763-6806, 1044 lines)
- Section 1: Lines 5775-6209 (Deterministic Cashflow)
- Section 2: Lines 6211-6806 (Monte Carlo Simulation)

## Implementation Steps

### Step 1: Create New Function for Deterministic Cashflow

**Location:** Add this new function right BEFORE line 5763 (before `combined_analysis_cashflow_tab`)

**Function to create:**
```python
def deterministic_cashflow_tab():
    """Deterministic Lifetime Cashflow Analysis - shows exactly how money flows through your entire life"""
    st.header("💰 Deterministic Lifetime Cashflow")

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
            # REST OF SECTION 1 CODE GOES HERE (lines 5805-6205)
            # Copy everything from line 5805 through line 6205
        else:
            st.warning("No cashflow data available. Please configure your financial details first.")
    else:
        st.warning("⚠️ No cashflow data calculated yet. Click the button above to generate your lifetime cashflow analysis.")
```

**Detailed Instructions:**
1. Navigate to line 5763
2. Create a new function called `deterministic_cashflow_tab()`
3. Copy the function header and intro text shown above
4. Copy lines 5784-6205 from the original `combined_analysis_cashflow_tab()` function
5. Make sure to maintain all indentation correctly

### Step 2: Create New Function for Monte Carlo Simulation

**Location:** Add this new function right AFTER the `deterministic_cashflow_tab()` function you just created

**Function to create:**
```python
def monte_carlo_simulation_tab():
    """Monte Carlo Simulation Analysis - probabilistic view of financial outcomes"""
    st.header("🎲 Monte Carlo Simulation")

    st.markdown("""
    Add uncertainty to your plan and see the range of possible outcomes.
    This probabilistic view shows how market volatility and life's unpredictability might affect your financial future.

    **Focus:** Net worth trajectories and probability of success (not income/expense details - see Deterministic Cashflow tab for that).
    """)

    st.subheader("⚙️ Simulation Settings")

    # REST OF SECTION 2 CODE GOES HERE (lines 6224-6806)
    # Copy everything from line 6224 through line 6806
```

**Detailed Instructions:**
1. Right after the `deterministic_cashflow_tab()` function, create `monte_carlo_simulation_tab()`
2. Copy the function header and intro text shown above
3. Copy lines 6224-6806 from the original `combined_analysis_cashflow_tab()` function
4. Make sure to maintain all indentation correctly

### Step 3: Update Tab Configuration

**Location:** Lines 3595-3604

**Current configuration (line 3600):**
```python
("📊 Analysis & Cashflow", combined_analysis_cashflow_tab, True),
```

**Replace with TWO entries:**
```python
("💰 Deterministic Cashflow", deterministic_cashflow_tab, True),
("🎲 Monte Carlo Simulation", monte_carlo_simulation_tab, True),
```

**Full updated section should look like:**
```python
    tab_configs = [
        ("👤 Parent Information", parent_info_tab, True),
        ("👶 Children", children_tab, True),
        ("💰 Family Expenses", family_expenses_tab, True),
        ("🎓 Children Expenses", children_expenses_tab, True),
        ("💼 Career", career_tab, True),
        ("💵 Income", additional_income_tab, True),
        ("📦 Assets", assets_tab, True),
        ("🏠 House Portfolio", house_tab, True),
        ("🗓️ Timeline", timeline_tab, True),
        ("📈 Economy", economy_tab, True),
        ("🖼️ Retirement", retirement_tab, True),
        ("🏥 Healthcare & Insurance", healthcare_insurance_tab, st.session_state.get('show_healthcare', False)),
        ("💰 Deterministic Cashflow", deterministic_cashflow_tab, True),
        ("🎲 Monte Carlo Simulation", monte_carlo_simulation_tab, True),
        ("🧪 Stress Test", stress_test_tab, True),
        ("📄 Export Reports", report_export_tab, st.session_state.get('show_export', True)),
        ("💾 Save/Load", save_load_tab, True)
    ]
```

### Step 4: Delete or Comment Out Old Function

**Location:** Lines 5763-6806

Once you've confirmed the new tabs work correctly, you can:
- **Option A (Recommended):** Delete the entire `combined_analysis_cashflow_tab()` function
- **Option B (Safe):** Comment it out for now with a note:
  ```python
  # DEPRECATED: This function has been split into deterministic_cashflow_tab()
  # and monte_carlo_simulation_tab() for better organization
  # def combined_analysis_cashflow_tab():
  #     ... (rest of old function)
  ```

### Step 5: Test the Changes

**Testing Checklist:**

1. **Launch the application:**
   ```bash
   streamlit run FinancialPlanner_v0_85.py
   ```

2. **Verify tab structure:**
   - [ ] Check that "Analysis & Cashflow" tab is gone
   - [ ] Check that "Deterministic Cashflow" tab appears
   - [ ] Check that "Monte Carlo Simulation" tab appears
   - [ ] Verify tabs are in the correct order

3. **Test Deterministic Cashflow tab:**
   - [ ] Click "Calculate Lifetime Cashflow" button
   - [ ] Verify the timeline chart displays correctly
   - [ ] Click on a year in the chart to see breakdown
   - [ ] Check all three sub-tabs: Timeline View, Critical Years Table, Life Stages
   - [ ] Verify all metrics display correctly

4. **Test Monte Carlo Simulation tab:**
   - [ ] Adjust simulation settings (number of simulations, years, etc.)
   - [ ] Click "Run Monte Carlo Simulation" button
   - [ ] Verify the probability distributions display correctly
   - [ ] Check percentile lines (10th, 50th, 90th)
   - [ ] Verify success probability metrics

5. **Test navigation:**
   - [ ] Switch between the two new tabs
   - [ ] Verify session state persists (calculated data doesn't disappear)
   - [ ] Check that other tabs still work correctly

## Common Issues and Solutions

### Issue 1: Indentation Errors
**Symptom:** `IndentationError` when running the app
**Solution:** Make sure you maintain exact indentation when copying code blocks. Python is very sensitive to indentation.

### Issue 2: Session State Key Conflicts
**Symptom:** Buttons don't work or cause errors
**Solution:** Each `st.button()` needs a unique `key` parameter. If you see duplicate key errors, add unique suffixes like `_det` or `_mc`.

### Issue 3: Data Not Persisting Between Tabs
**Symptom:** Switching tabs clears calculated data
**Solution:** Ensure you're using `st.session_state` for all cached data:
- `st.session_state.cashflow_data_cached` for deterministic results
- `st.session_state.mc_results` for Monte Carlo results

### Issue 4: Old Function Still Being Called
**Symptom:** Changes to new functions don't appear
**Solution:** Make sure you updated the tab configuration in Step 3 and removed/commented the old function.

## Success Criteria

✅ **Phase 1 is complete when:**
1. "Analysis & Cashflow" tab no longer appears
2. Two new tabs appear: "Deterministic Cashflow" and "Monte Carlo Simulation"
3. Both tabs function exactly as they did in the original combined tab
4. No errors or warnings appear when using either tab
5. All data calculations work correctly
6. Navigation between tabs is smooth

## Estimated Time
**30-45 minutes** (including testing)

## Next Phase
Once Phase 1 is complete and tested, proceed to **Phase 2: Custom Spending Templates**
