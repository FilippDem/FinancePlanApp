"""Regenerate engine/finplan/data/*.json from FinancialPlanner_v0_8.py.

Run from the repo root:  python v2/tools/extract_v08_data.py
Requires streamlit + pandas installed (the v0.8 module is imported in bare mode).
Writes: reference_data.json (templates/tax tables), demo_plans.json,
default_plan.json and tests/fixtures/v08_cashflow_reference.json.
"""
import sys, json, importlib.util, dataclasses, warnings, logging, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
warnings.filterwarnings('ignore'); logging.disable(logging.CRITICAL)
SRC=ROOT + '/FinancialPlanner_v0_8.py'
OUT=ROOT + '/v2/engine/finplan/data'
FIX=ROOT + '/v2/engine/tests/fixtures'
spec=importlib.util.spec_from_file_location('fp',SRC)
fp=importlib.util.module_from_spec(spec); spec.loader.exec_module(fp)
import streamlit as st
names=['HISTORICAL_STOCK_RETURNS','EXPENSE_TEMPLATE_BASE_YEAR','LOCATION_HIERARCHY','AVAILABLE_LOCATIONS_ADULTS','AVAILABLE_LOCATIONS_CHILDREN','AVAILABLE_LOCATIONS_FAMILY','LOCATION_DISPLAY_NAMES','STATISTICAL_STRATEGIES','ADULT_EXPENSE_CATEGORIES','ADULT_EXPENSE_CATEGORIES_FLAT','CHILDREN_EXPENSE_CATEGORIES_FLAT','FAMILY_SHARED_CATEGORIES','FAMILY_SHARED_CATEGORIES_FLAT','ADULT_EXPENSE_TEMPLATES','STATE_EXPENSE_TEMPLATES','PROVINCE_EXPENSE_TEMPLATES','CHILDREN_EXPENSE_TEMPLATES','FAMILY_EXPENSE_TEMPLATES','EXPENSE_DATA_SOURCES','US_STATE_TAX_INFO','COUNTRY_TAX_INFO']
data={n:getattr(fp,n) for n in names}
json.dump(data,open(f'{OUT}/reference_data.json','w'),indent=1)
json.dump(fp.LOCATION_COORDINATES,open(f'{OUT}/location_coordinates.json','w'),indent=1)
fp.initialize_session_state()
ss=st.session_state
def conv(o):
    if dataclasses.is_dataclass(o): return dataclasses.asdict(o)
    if hasattr(o,'to_dict'): return o.to_dict('records')
    raise TypeError(type(o))
demos={}
for k,v in ss.saved_scenarios.items():
    demos[k]=json.loads(json.dumps(v,default=conv))
json.dump(demos,open(f'{OUT}/demo_plans.json','w'),indent=1)
# default plan
json.dump(json.loads(fp.save_data()),open(f'{OUT}/default_plan.json','w'),indent=1)
# reference v0.8 cashflow outputs per demo
ref={}
for k,v in demos.items():
    fp.load_data(json.dumps(v))
    rows=fp.calculate_lifetime_cashflow()
    ref[k]=[{kk:r[kk] for kk in ('year','parent1_income','parent2_income','ss_income','taxes','total_expenses','house_expenses','children_expenses','net_worth') } for r in rows]
json.dump(ref,open(f'{FIX}/v08_cashflow_reference.json','w'))
print('ok', {k:len(v) for k,v in ref.items()})
