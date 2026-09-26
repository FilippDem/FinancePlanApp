"""Cost-of-living calibration from public data (see docs/COST_DATA_AUDIT.md).

* Spending levels per adult come from the BLS Consumer Expenditure Survey (2022 income
  quintiles, grown to 2024 with the 2024 all-household category totals).
    Conservative = 2nd quintile, Average = midpoint of 3rd and 4th quintiles, High-end = top quintile.
  Household spending is split per adult as adults + 0.5 x children (children have their own templates).
* Location differences use BEA Regional Price Parities 2024: goods-type categories scale with the
  goods RPP, service-type categories with the "other services" RPP, and rent with the rents RPP.
* Locations without an RPP (outside the US) keep v0.8's relative level versus Seattle.
All amounts are 2024 dollars (the template base year).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / 'data' / 'cost_index.json'
LEVELS = {'Conservative': ('q2',), 'Average': ('q3', 'q4'), 'High-end': ('q5',)}
GOODS = {'Groceries', 'Auto Payment', 'Gas & Fuel', 'Clothing', 'Personal Care', 'Hobbies', 'Other Personal'}
# every other adult category is a service
CITY_METRO = {'NYC': 'New York', 'New York City': 'New York', 'District of Columbia': 'Washington DC',
              'Urban Honolulu': 'Honolulu'}
STATE_OF = {'Seattle': 'Washington', 'San Francisco': 'California', 'Los Angeles': 'California', 'San Diego': 'California',
            'Sacramento': 'California', 'Portland': 'Oregon', 'Austin': 'Texas', 'Houston': 'Texas', 'Dallas': 'Texas',
            'Chicago': 'Illinois', 'Miami': 'Florida', 'Denver': 'Colorado', 'Phoenix': 'Arizona', 'Las Vegas': 'Nevada',
            'Atlanta': 'Georgia', 'Philadelphia': 'Pennsylvania', 'Boston': 'Massachusetts', 'Columbus': 'Ohio',
            'Honolulu': 'Hawaii', 'Washington DC': 'District of Columbia'}


@lru_cache(maxsize=1)
def data() -> dict:
    with open(DATA, encoding='utf-8') as f:
        return json.load(f)


def _q(row: str, col: str) -> float:
    q = data()['cex_2022_quintiles']
    vals = list(q[row])
    cols = q['columns']
    # interpolate suppressed cells between neighbours
    for i, v in enumerate(vals):
        if v is None:
            lo = next(vals[j] for j in range(i - 1, -1, -1) if vals[j] is not None)
            hi = next(vals[j] for j in range(i + 1, len(vals)) if vals[j] is not None)
            vals[i] = (lo + hi) / 2
    return float(vals[cols.index(col)])


def _growth(cat: str) -> float:
    a24 = data()['cex_2024_all']
    base = {'food_home': 'food_home', 'food_away': 'food_away', 'apparel': 'apparel', 'transportation': 'transportation',
            'healthcare': 'healthcare', 'entertainment': 'entertainment', 'personal_care': 'personal_care', 'total': 'total'}[cat]
    return a24[base] / _q(base, 'all')


def _adult_share(col: str) -> float:
    persons, kids = _q('persons', col), _q('children', col)
    return (persons - kids) + 0.5 * kids


def national_adult_quintiles(level: str) -> dict:
    """(Legacy helper) per-adult spending averaged over the quintiles of a lifestyle, US prices."""
    base = level.replace(' (statistical)', '').replace(' (calibrated)', '')
    cols = LEVELS.get(base, LEVELS['Average'])
    out: dict[str, float] = {}
    for col in cols:
        d = _adult_share(col)
        g = _growth
        oop = _q('healthcare', col) - _q('health_insurance', col)
        cats = {
            'Groceries': _q('food_home', col) * g('food_home'),
            'Dining Out': _q('food_away', col) * 0.8 * g('food_away'),
            'Coffee Shops': _q('food_away', col) * 0.2 * g('food_away'),
            'Auto Payment': (_q('vehicle_purchases', col) + _q('vehicle_finance', col)) * g('transportation'),
            'Gas & Fuel': _q('gasoline', col) * g('transportation'),
            'Auto Maintenance': _q('maintenance', col) * g('transportation'),
            'Auto Insurance': _q('vehicle_insurance', col) * g('transportation'),
            'Parking & Tolls': _q('vehicle_fees', col) * g('transportation'),
            'Public Transit': _q('public_transport', col) * 0.6 * g('transportation'),
            'Ride Shares': _q('public_transport', col) * 0.4 * g('transportation'),
            'Clothing': _q('apparel', col) * g('apparel'),
            'Personal Care': _q('personal_care', col) * 0.6 * g('personal_care'),
            'Grooming': _q('personal_care', col) * 0.4 * g('personal_care'),
            'Medical': oop * 0.55 * g('healthcare'),
            'Dental': oop * 0.25 * g('healthcare'),
            'Vision': oop * 0.10 * g('healthcare'),
            'Mental Health': oop * 0.10 * g('healthcare'),
            'Fitness': _q('fees_admissions', col) * 0.4 * g('entertainment'),
            'Entertainment': (_q('fees_admissions', col) * 0.6 + _q('other_entertainment', col)) * g('entertainment'),
            'Hobbies': _q('pets_toys_hobbies', col) * g('entertainment'),
            'Subscriptions': _q('audio_visual', col) * g('entertainment'),
            'Phone': _q('telephone', col) * g('total'),
            'Other Personal': (_q('alcohol', col) + _q('tobacco', col) + _q('reading', col) + _q('misc', col)) * g('total'),
        }
        for k, v in cats.items():
            out[k] = out.get(k, 0.0) + v / d / len(cols)
    return out


def rpp(location: str) -> list | None:
    """[all_items, goods, rents, other_services] for a US state or metro, else None."""
    d = data()
    loc = CITY_METRO.get(location, location)
    if loc in d['rpp_metros']:
        return d['rpp_metros'][loc]
    if loc in d['rpp_states']:
        return d['rpp_states'][loc]
    st = STATE_OF.get(loc)
    if st and st in d['rpp_states']:
        return d['rpp_states'][st]
    return None


def calibrated_adult(location: str, level: str, v08_lookup=None) -> dict | None:
    """Per-adult template for a lifestyle label, taken from the spending slider
    (Conservative = US 2nd quintile, Average = US average household, High-end = US top 20%),
    at local prices. None only when nothing is known about the location and no lookup is given."""
    curve = spending_curve(location, v08_lookup)
    if curve['basis'] == 'us' and location not in ('United States', 'US', 'USA'):
        return None
    cats = level_at(curve, x_for_strategy(level))
    return {k: round(v / 10) * 10 for k, v in cats.items()}


def rent_factor(base: str, dest: str) -> float | None:
    a, b = rpp(base), rpp(dest)
    if a is None or b is None:
        return None
    return b[2] / a[2]


# ── spending-level slider ────────────────────────────────────────────────
# Slider position x in [0, 100]. Anchors are BLS income quintiles (per adult, local prices)
# plus the v0.8 "Average" and "High-end" templates so the old levels stay reachable.
ANCHORS = [
    (5, 'q1', 'Bare-bones', 'US lowest 20% of households'),
    (20, 'q2', 'Frugal', 'US 2nd 20% of households'),
    (40, 'q3', 'Middle', 'US middle 20% of households'),
    (50, 'all', 'US average', 'Average US household'),
    (60, 'q4', 'Upper-middle', 'US 4th 20% of households'),
    (78, 'q5', 'Top 20%', 'US top 20% of households'),
    (90, 'v08_avg', "Old app 'Average'", "v0.8 template 'Average'"),
    (100, 'v08_high', "Old app 'High-end'", "v0.8 template 'High-end'"),
]


def national_adult_col(col: str) -> dict:
    """Per-adult spending by category for one CEX column (q1..q5 or 'all'), US prices, 2024 $."""
    d = _adult_share(col)
    g = _growth
    oop = _q('healthcare', col) - _q('health_insurance', col)
    cats = {
        'Groceries': _q('food_home', col) * g('food_home'),
        'Dining Out': _q('food_away', col) * 0.8 * g('food_away'),
        'Coffee Shops': _q('food_away', col) * 0.2 * g('food_away'),
        'Auto Payment': (_q('vehicle_purchases', col) + _q('vehicle_finance', col)) * g('transportation'),
        'Gas & Fuel': _q('gasoline', col) * g('transportation'),
        'Auto Maintenance': _q('maintenance', col) * g('transportation'),
        'Auto Insurance': _q('vehicle_insurance', col) * g('transportation'),
        'Parking & Tolls': _q('vehicle_fees', col) * g('transportation'),
        'Public Transit': _q('public_transport', col) * 0.6 * g('transportation'),
        'Ride Shares': _q('public_transport', col) * 0.4 * g('transportation'),
        'Clothing': _q('apparel', col) * g('apparel'),
        'Personal Care': _q('personal_care', col) * 0.6 * g('personal_care'),
        'Grooming': _q('personal_care', col) * 0.4 * g('personal_care'),
        'Medical': oop * 0.55 * g('healthcare'),
        'Dental': oop * 0.25 * g('healthcare'),
        'Vision': oop * 0.10 * g('healthcare'),
        'Mental Health': oop * 0.10 * g('healthcare'),
        'Fitness': _q('fees_admissions', col) * 0.4 * g('entertainment'),
        'Entertainment': (_q('fees_admissions', col) * 0.6 + _q('other_entertainment', col)) * g('entertainment'),
        'Hobbies': _q('pets_toys_hobbies', col) * g('entertainment'),
        'Subscriptions': _q('audio_visual', col) * g('entertainment'),
        'Phone': _q('telephone', col) * g('total'),
        'Other Personal': (_q('alcohol', col) + _q('tobacco', col) + _q('reading', col) + _q('misc', col)) * g('total'),
    }
    return {k: v / d for k, v in cats.items()}


def _localize(nat: dict, location: str, v08_lookup) -> tuple[dict, str]:
    r = rpp(location)
    if r is not None:
        goods, other = r[1] / 100, r[3] / 100
        return {k: v * (goods if k in GOODS else other) for k, v in nat.items()}, 'bea'
    cpl = data().get('country_price_level', {}).get(location)
    if cpl is not None:
        return {k: v * cpl for k, v in nat.items()}, 'country'
    if v08_lookup is not None:
        t, ref_t = v08_lookup(location, 'Average'), v08_lookup('Seattle', 'Average')
        sea = rpp('Seattle')
        if t and ref_t and sea:
            ratio = sum(t.values()) / sum(ref_t.values())
            return {k: v * (sea[1] if k in GOODS else sea[3]) / 100 * ratio for k, v in nat.items()}, 'relative'
    return dict(nat), 'us'


def spending_curve(location: str, v08_lookup=None) -> dict:
    """Anchors for the spending slider at a location (per adult per year, 2024 $)."""
    anchors = []
    basis = 'us'
    for x, key, label, desc in ANCHORS:
        if key.startswith('v08'):
            t = v08_lookup(location, 'High-end' if key == 'v08_high' else 'Average') if v08_lookup else None
            if not t and v08_lookup:
                t = v08_lookup('Seattle', 'High-end' if key == 'v08_high' else 'Average')
            if not t:
                continue
            cats = {k: float(v) for k, v in t.items()}
        else:
            cats, basis = _localize(national_adult_col(key), location, v08_lookup)
        cats = {k: round(v / 10) * 10 for k, v in cats.items()}
        anchors.append({'x': x, 'key': key, 'label': label, 'desc': desc, 'total': sum(cats.values()), 'cats': cats})
    # keep totals increasing so the slider is monotone
    for i in range(1, len(anchors)):
        if anchors[i]['total'] < anchors[i - 1]['total']:
            k = anchors[i - 1]['total'] * 1.02 / max(anchors[i]['total'], 1)
            anchors[i]['cats'] = {c: round(v * k / 10) * 10 for c, v in anchors[i]['cats'].items()}
            anchors[i]['total'] = sum(anchors[i]['cats'].values())
    return {'location': location, 'basis': basis, 'anchors': anchors,
            'note': {'bea': 'BLS spending by income group, adjusted to local prices with BEA 2024 price parities',
                     'country': 'BLS spending by income group, scaled by the World Bank national price level (2020, rough)',
                     'relative': "BLS spending by income group; local prices estimated from the audited templates (no BEA data outside the US)",
                     'us': 'BLS spending by income group at US-average prices (no local price data)'}[basis]}


def level_at(curve: dict, x: float) -> dict:
    """Interpolated per-adult categories at slider position x."""
    a = curve['anchors']
    x = max(0.0, min(100.0, float(x)))
    if x <= a[0]['x']:
        lo = hi = a[0]; w = 0.0
        # below the first anchor: scale down toward 60% of it at x=0
        k = 0.6 + 0.4 * (x / a[0]['x'])
        return {c: v * k for c, v in lo['cats'].items()}
    for i in range(1, len(a)):
        if x <= a[i]['x']:
            lo, hi = a[i - 1], a[i]
            w = (x - lo['x']) / (hi['x'] - lo['x'])
            cats = set(lo['cats']) | set(hi['cats'])
            return {c: lo['cats'].get(c, 0) * (1 - w) + hi['cats'].get(c, 0) * w for c in cats}
    return dict(a[-1]['cats'])


def x_for_strategy(strategy: str) -> float:
    s = (strategy or 'Average').lower()
    return 20.0 if 'conservative' in s else 78.0 if 'high' in s else 50.0


def national_adult(level: str) -> dict:
    """Per-adult spending for a lifestyle label at US-average prices."""
    x = x_for_strategy(level)
    anchors = [a for a in ANCHORS if not a[1].startswith('v08')]
    curve = {'anchors': [{'x': ax, 'cats': national_adult_col(key)} for ax, key, *_ in anchors]}
    return level_at(curve, x)
