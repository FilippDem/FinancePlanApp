# Phase 2: Custom Spending Strategy System

## Goal
Implement a comprehensive custom spending strategy system that allows users to:
1. Rename existing strategies to add "(statistical)" suffix
2. Create custom spending templates that show as "Name (custom)" in dropdowns
3. Save custom templates to session state and persist them
4. Delete custom templates with confirmation (cannot delete statistical templates)

## Overview
This phase modifies both the **Family Expenses** and **Children Expenses** tabs to support custom user-created spending strategies alongside the built-in statistical templates.

## Part A: Rename Statistical Strategies

### Step 1: Update Family Expense Templates

**Location:** Lines 910-1457 (FAMILY_EXPENSE_TEMPLATES dictionary)

**Task:** Add " (statistical)" suffix to all strategy names

**Find all instances of these strategy keys:**
- `"Conservative"` → `"Conservative (statistical)"`
- `"Average"` → `"Average (statistical)"`
- `"High-end"` → `"High-end (statistical)"`

**Example transformation:**
```python
# BEFORE:
"Seattle": {
    "Conservative": {
        'Food & Groceries': 13200,
        'Clothing': 3000,
        ...
    },
    "Average": {
        'Food & Groceries': 16800,
        ...
    },
    "High-end": {
        'Food & Groceries': 22800,
        ...
    }
},

# AFTER:
"Seattle": {
    "Conservative (statistical)": {
        'Food & Groceries': 13200,
        'Clothing': 3000,
        ...
    },
    "Average (statistical)": {
        'Food & Groceries': 16800,
        ...
    },
    "High-end (statistical)": {
        'Food & Groceries': 22800,
        ...
    }
},
```

**How to do this efficiently:**
1. Use Find & Replace in your editor
2. Find: `"Conservative": {` → Replace with: `"Conservative (statistical)": {`
3. Find: `"Average": {` → Replace with: `"Average (statistical)": {`
4. Find: `"High-end": {` → Replace with: `"High-end (statistical)": {`
5. Do this for ALL city entries in FAMILY_EXPENSE_TEMPLATES

**Cities to update (approximately 18 cities):**
- Seattle, Houston, Phoenix, Philadelphia, San Antonio, San Diego, Dallas, San Jose, Austin, Jacksonville, San Francisco, Columbus, Fort Worth, Charlotte, Indianapolis, Denver, Boston, Sacramento

### Step 2: Update Children Expense Templates

**Location:** Lines 231-909 (CHILDREN_EXPENSE_TEMPLATES dictionary)

**Task:** Same as Step 1, but for children's expenses

**Apply the same Find & Replace operations to:**
- `"Conservative"` → `"Conservative (statistical)"`
- `"Average"` → `"Average (statistical)"`
- `"High-end"` → `"High-end (statistical)"`

**Note:** Children templates also have additional stratifications like:
- College types: "Public", "Private", "Elite"
- College locations: "In-State", "Out-of-State"

Make sure to update ALL strategy keys in the nested structure.

### Step 3: Update Demo Scenarios

**Important:** After renaming strategies, you'll need to update all demo scenarios that reference these strategies.

**Search for:** `'template_strategy':`

**Example locations to update:**
```python
# Demo scenarios use template_strategy field
'template_strategy': 'Average'  # Change to 'Average (statistical)'
```

**Use Find & Replace:**
1. `'template_strategy': 'Conservative'` → `'template_strategy': 'Conservative (statistical)'`
2. `'template_strategy': 'Average'` → `'template_strategy': 'Average (statistical)'`
3. `'template_strategy': 'High-end'` → `'template_strategy': 'High-end (statistical)'`

## Part B: Enhance Custom Template System

### Step 4: Initialize Custom Template Storage

**Location:** Find where session state is initialized (search for `st.session_state.custom_family_templates`)

**Verify this code exists:**
```python
# Initialize custom templates storage
if 'custom_family_templates' not in st.session_state:
    st.session_state.custom_family_templates = {}

if 'custom_children_templates' not in st.session_state:
    st.session_state.custom_children_templates = {}
```

**If it doesn't exist, add it near the top of the main app initialization.**

### Step 5: Add Custom Template Naming Convention

**Location:** In the "Create Custom City" tab of `family_expenses_tab()` function

**Find the code where custom templates are saved** (search for "Create Custom City")

**Modify the save logic to add "(custom)" suffix:**

```python
# When creating a new custom city, ensure strategy names have (custom) suffix
def save_custom_template(city_name, strategy_name, template_data):
    """Save a custom template with proper naming convention"""

    # Ensure strategy name has (custom) suffix
    if not strategy_name.endswith("(custom)"):
        strategy_name = f"{strategy_name} (custom)"

    # Initialize city if it doesn't exist
    if city_name not in st.session_state.custom_family_templates:
        st.session_state.custom_family_templates[city_name] = {}

    # Save the template
    st.session_state.custom_family_templates[city_name][strategy_name] = template_data

    return True
```

### Step 6: Add Delete Functionality with Confirmation

**Location:** Family Expenses tab, after the browse/edit tabs

**Add a new sub-tab for managing custom templates:**

```python
expense_tab1, expense_tab2, expense_tab3, expense_tab4 = st.tabs([
    "📊 Browse Templates",
    "✏️ Edit Templates",
    "🌍 Create Custom City",
    "🗑️ Manage Custom Templates"  # NEW TAB
])

# New tab for managing custom templates
with expense_tab4:
    st.subheader("🗑️ Manage Custom Templates")

    st.markdown("""
    View and delete your custom spending templates.

    **Note:** Statistical templates cannot be deleted - only custom templates you created.
    """)

    # Get all custom templates
    if not st.session_state.custom_family_templates:
        st.info("No custom templates found. Create one in the 'Create Custom City' tab.")
    else:
        st.markdown("### Your Custom Templates")

        # Display each custom city and its strategies
        for city_name in sorted(st.session_state.custom_family_templates.keys()):
            with st.expander(f"📍 {city_name}"):
                strategies = st.session_state.custom_family_templates[city_name]

                for strategy_name, template_data in strategies.items():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"**{strategy_name}**")

                    with col2:
                        total = sum(template_data.values())
                        st.write(f"Total: ${total:,.0f}/year")

                    with col3:
                        # Delete button with unique key
                        delete_key = f"delete_{city_name}_{strategy_name}".replace(" ", "_").replace("(", "").replace(")", "")

                        if st.button("🗑️ Delete", key=delete_key, type="secondary"):
                            st.session_state[f'confirm_delete_{delete_key}'] = True

                    # Show confirmation dialog if delete was clicked
                    if st.session_state.get(f'confirm_delete_{delete_key}', False):
                        st.warning(f"⚠️ Are you sure you want to delete **{strategy_name}** from **{city_name}**?")

                        col_yes, col_no = st.columns(2)

                        with col_yes:
                            if st.button("✅ Yes, Delete", key=f"confirm_yes_{delete_key}"):
                                # Perform deletion
                                del st.session_state.custom_family_templates[city_name][strategy_name]

                                # If city has no more strategies, remove city
                                if not st.session_state.custom_family_templates[city_name]:
                                    del st.session_state.custom_family_templates[city_name]

                                # Clear confirmation state
                                del st.session_state[f'confirm_delete_{delete_key}']

                                st.success(f"✅ Deleted {strategy_name} from {city_name}")
                                st.rerun()

                        with col_no:
                            if st.button("❌ Cancel", key=f"confirm_no_{delete_key}"):
                                # Clear confirmation state
                                del st.session_state[f'confirm_delete_{delete_key}']
                                st.rerun()
```

### Step 7: Update Children Expenses Tab (Same Pattern)

**Location:** `children_expenses_tab()` function

**Apply the same changes as Steps 5-6 to the Children Expenses tab:**
1. Add "(custom)" suffix to custom strategy names
2. Add a "Manage Custom Templates" sub-tab
3. Implement delete functionality with confirmation

**Note:** The structure is very similar to Family Expenses, so you can adapt the code from Steps 5-6.

### Step 8: Prevent Deletion of Statistical Templates

**Add validation in the delete functionality:**

```python
# Before deleting, check if it's a statistical template
if "(statistical)" in strategy_name:
    st.error("❌ Cannot delete statistical templates. Only custom templates can be deleted.")
    return
```

**Add this check in both:**
- Family Expenses delete function
- Children Expenses delete function

## Part C: Testing and Validation

### Step 9: Test Strategy Renaming

**Testing Checklist:**
1. **Launch app and check all dropdowns:**
   - [ ] Family Expenses tab → Browse Templates → All strategies show "(statistical)" suffix
   - [ ] Children Expenses tab → Browse Templates → All strategies show "(statistical)" suffix
   - [ ] Demo scenarios still work correctly

2. **Check for any errors:**
   - [ ] No KeyError exceptions when loading templates
   - [ ] Demo scenarios load without issues
   - [ ] All calculations work correctly

### Step 10: Test Custom Template Creation

**Testing Checklist:**
1. **Create a test custom template:**
   - [ ] Go to Family Expenses → Create Custom City
   - [ ] Create a new city with a custom strategy
   - [ ] Verify the strategy name has "(custom)" suffix in dropdown
   - [ ] Template data is saved correctly

2. **Verify custom template appears:**
   - [ ] Browse Templates tab shows custom city
   - [ ] Custom strategy appears in strategy dropdown
   - [ ] Custom strategy displays "(custom)" suffix

### Step 11: Test Delete Functionality

**Testing Checklist:**
1. **Test custom template deletion:**
   - [ ] Go to Manage Custom Templates tab
   - [ ] Click delete on a custom template
   - [ ] Confirmation dialog appears
   - [ ] Clicking "Yes" deletes the template
   - [ ] Template no longer appears in Browse Templates
   - [ ] Clicking "Cancel" keeps the template

2. **Test statistical template protection:**
   - [ ] Try to delete a statistical template (if exposed)
   - [ ] Verify error message appears
   - [ ] Statistical template is NOT deleted

## Common Issues and Solutions

### Issue 1: KeyError After Renaming Strategies
**Symptom:** `KeyError: 'Average'` when loading templates
**Solution:** You missed updating a reference to the old strategy name. Search for the old name (e.g., `'Average'`) and ensure it's updated to `'Average (statistical)'`.

### Issue 2: Demo Scenarios Don't Load
**Symptom:** Demo scenarios fail to load after strategy renaming
**Solution:** Update all `'template_strategy'` references in demo scenarios to use the new names with "(statistical)" suffix.

### Issue 3: Custom Suffix Not Appearing
**Symptom:** Custom templates don't show "(custom)" in dropdown
**Solution:** Check the `save_custom_template()` function and ensure it's adding the suffix before saving.

### Issue 4: Delete Button Doesn't Work
**Symptom:** Clicking delete does nothing
**Solution:** Check that each delete button has a unique `key` parameter. The key must be unique for each template.

### Issue 5: Confirmation Dialog Doesn't Appear
**Symptom:** Delete happens immediately without confirmation
**Solution:** Ensure you're using session state to track confirmation state: `st.session_state[f'confirm_delete_{delete_key}']`

## Success Criteria

✅ **Phase 2 is complete when:**
1. All built-in strategies show "(statistical)" suffix in all dropdowns
2. Custom templates can be created and show "(custom)" suffix
3. Custom templates appear in Browse Templates tab
4. Delete functionality works with confirmation dialog
5. Statistical templates cannot be deleted
6. Demo scenarios still work correctly
7. No errors or warnings when browsing/creating/deleting templates

## Estimated Time
**60-90 minutes** (including careful find-replace and testing)

## Important Notes

### Find & Replace Safety Tips
1. **Always preview** before replacing all instances
2. **Replace one at a time** for the first few to verify correctness
3. **Test frequently** after each major change
4. **Keep a backup** of the file before making changes

### Session State Persistence
- Custom templates are stored in `st.session_state`
- Templates will be lost when the app is restarted
- **Phase 3** will add persistent storage (save to file)
- For now, focus on the in-session functionality

## Next Phase
Once Phase 2 is complete and tested, proceed to **Phase 3: Create Filipp&Erin Custom Template**
