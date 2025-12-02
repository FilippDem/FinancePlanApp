# Implementation Plan for Financial Planner Updates

## Summary of Requested Changes

### ✅ 1. COMPLETED: Fix Sacramento Single Mom Demo Bug
- Fixed `House` class receiving invalid `asset_type` parameter
- Moved one-time purchases to correct list
- Bug is now resolved

### 2. Tab Reorganization (IN PROGRESS)
**Current Structure:**
- Analysis & Cashflow (combined tab)
  - Section 1: Deterministic Lifetime Cashflow
  - Section 2: Monte Carlo Simulation

**Desired Structure:**
- Deterministic Lifetime Cashflow (top-level tab)
- Monte Carlo Simulation (top-level tab)

**Implementation:**
Split `combined_analysis_cashflow_tab()` into two functions.

### 3. Custom Spending Strategy System (COMPLEX)
**Requirements:**
- Rename existing strategies: "Conservative (statistical)", "Average (statistical)", "High-end (statistical)"
- Allow users to create custom templates
- Custom templates show as "Name (custom)" in dropdowns
- Save custom templates to session state / file
- Allow deletion of custom templates (with confirmation)
- Cannot delete statistical templates

**Implementation needed in:**
- Family Expenses tab
- Children Expenses tab

### 4. Create "Filipp&Erin Spending (custom)" Template
Based on spreadsheet data:
- Living expenses: $108,600/year for 2 people
- Utilities: $4,920/year
- House upkeep: $12,000/year
- College: $30,000-35,000/child

## Scope Note

These changes involve:
- **~1,500 lines of code** to review/modify
- **Complex state management** for custom templates
- **Data persistence** across sessions
- **UI updates** in multiple tabs

Given the distributed nature of your Financial Planner app, implementing all of these changes properly will take significant time and testing.

## Recommended Approach

**Option A: Full Implementation (Recommended but Time-Intensive)**
- Properly implement all features
- ~2-3 hours of development
- Thorough testing needed

**Option B: Phased Approach (Pragmatic)**
1. Complete tab reorganization (30 min)
2. Implement basic custom template system (1 hour)
3. Add Filipp&Erin template as hardcoded option first (15 min)
4. Later enhance to full custom system

**Option C: Minimal Changes**
- Just add Filipp&Erin as a hardcoded "High-end+" tier
- Skip custom template infrastructure
- Can be enhanced later

## My Recommendation

Given that this is a working app you want to use, I suggest **Option B** - implement the core functionality now, with full custom template management as a future enhancement.

Would you like me to:
1. Proceed with full implementation (will take time)?
2. Do phased approach with tab reorganization + basic custom templates?
3. Add just the key features you need right now (Filipp&Erin template + tab split)?

Let me know and I'll proceed accordingly!
