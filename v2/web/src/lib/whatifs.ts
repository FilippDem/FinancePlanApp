/** Decision playground (FinP4l-style what-ifs).
 *
 *  A what-if is a decision you're weighing ("retire 3 years earlier", "a 2-year job loss", "buy a rental").
 *  They live in plan.whatifs (saved with the household, merged like every other key) and are NOT part of the
 *  plan until you "make it part of my plan". Each one is turned into either
 *    - ordinary plan edits (via the life editor's applyDraft: kids, homes, moves, purchases, recurring costs…), or
 *    - engine stress events in plan._stress (income_loss, extra_cost, market_crash, inflation_spike, return_shift,
 *      early_death) that only exist in the copy sent to /api/project and /api/montecarlo — never saved.
 *  Timings are absolute years; start..end is inclusive.
 */
import { applyDraft, ageAt, yearAtAge, endYear } from './lifeEdit'

export type Cat = 'career' | 'family' | 'purchases' | 'wealth' | 'costs' | 'stress'
export type Timing = 'span' | 'point' | 'none'
export type Who = 'X' | 'Y' | 'both'

export interface WhatIf {
  id: string
  key: string            // catalog key
  on: boolean            // toggled on (stacked into the projection)
  start: number          // year
  end?: number | null    // year (inclusive) for spans
  amount?: number
  amount2?: number
  pct?: number
  person?: Who
  location?: string
  name?: string          // custom label
}

export interface Ctx {
  cy: number
  retYear: number        // first retirement year (earlier of the two people)
  retYearX: number
  retYearY: number
  last: number           // last plan year
  single: boolean
  flex: number           // flexible spending per year, today's $
  inflation: number
  hasHome: boolean
  hasDebt: boolean
}

export interface FieldDef { key: 'amount' | 'amount2' | 'pct' | 'person' | 'location'; label: string; unit?: '$' | '$/yr' | '$/mo' | '%' ; hint?: string }

export interface Def {
  key: string
  cat: Cat
  label: string
  emoji: string
  desc: string
  timing: Timing
  fields: FieldDef[]
  startLabel?: string     // what the start marker means ("Retire", "Crash", "Starts")
  endLabel?: string
  defaults: (p: any, c: Ctx) => Partial<WhatIf>
  available?: (p: any, c: Ctx) => string | null   // reason it can't be used yet
  apply: (d: any, w: WhatIf, c: Ctx) => void
  quick?: string          // a question pill, FinP4l style
}

export const CATS: { key: Cat; label: string; emoji: string }[] = [
  { key: 'career', label: 'Career & earning changes', emoji: '💼' },
  { key: 'family', label: 'Family & life milestones', emoji: '👨‍👩‍👧' },
  { key: 'purchases', label: 'Big purchases & lifestyle', emoji: '🏠' },
  { key: 'wealth', label: 'Building wealth & investing', emoji: '📈' },
  { key: 'costs', label: 'Reducing costs & simplifying', emoji: '✂️' },
  { key: 'stress', label: 'Stress testing & what-ifs', emoji: '⚠️' },
]

// ───────────────────────────── helpers ─────────────────────────────
const single = (p: any) => !p.parent2_name || p.parent2_name === 'N/A'
const people = (p: any, w: WhatIf): ('X' | 'Y')[] => single(p) ? ['X'] : w.person === 'X' ? ['X'] : w.person === 'Y' ? ['Y'] : ['X', 'Y']
const personNum = (who: 'X' | 'Y') => (who === 'X' ? 1 : 2)
const enginePerson = (p: any, w: WhatIf): 1 | 2 | 'both' => single(p) ? 1 : w.person === 'Y' ? 2 : w.person === 'X' ? 1 : 'both'
const yrs = (w: WhatIf) => Math.max(1, ((w.end ?? w.start) - w.start) + 1)
const n = (v: any, def = 0) => (v === null || v === undefined || v === '' || isNaN(+v) ? def : +v)
const stress = (d: any, ev: any) => { d._stress = [...(d._stress || []), ev] }
const title = (w: WhatIf, def: Def) => w.name || def.label

function incomeChange(d: any, w: WhatIf, start: number, years: number, pctCut: number) {
  // engine income_loss keeps (1 - pct/100) of wages and contributions; a negative pct is a raise
  stress(d, { type: 'income_loss', person: enginePerson(d, w), start_year: start, years, pct: pctCut })
}
function cost(d: any, name: string, perYear: number, start: number, years: number) {
  // a yearly cost (today's $) as a recurring expense — a normal plan item, so it can be made permanent
  if (!perYear) return
  applyDraft(d, { kind: 'recurring' }, { name, amount: Math.round(perYear), every: 1, year: start, until: start + years - 1 })
}
function cashIn(d: any, name: string, perYear: number, start: number, years: number) {
  // after-tax money coming in each year (modelled as a negative cost)
  if (!perYear) return
  stress(d, { type: 'extra_cost', name, amount: -Math.abs(perYear), start_year: start, years })
}
function oneOff(d: any, name: string, amount: number, year: number, financing = 0, rate = 0) {
  if (!amount) return
  applyDraft(d, { kind: 'purchase' }, { name, year, amount: Math.round(amount), financing, rate })
}
function retireShift(d: any, w: WhatIf, c: Ctx) {
  // the marker is the retirement year of the first person chosen; the others move by the same number of years
  const who = people(d, w)
  const anchor = who[0] === 'X' ? c.retYearX : c.retYearY
  const delta = w.start - anchor
  for (const p of who) d[`parent${p}_retirement_age`] = Math.max(d[`parent${p}_age`], d[`parent${p}_retirement_age`] + delta)
}
function move(d: any, w: WhatIf, lifestyle?: string) {
  const cur = (d.state_timeline || []).filter((e: any) => e.year <= w.start).slice(-1)[0]
  applyDraft(d, { kind: 'move' }, { location: w.location || cur?.state || 'Seattle', year: w.start, lifestyle: lifestyle || String(cur?.spending_strategy || 'Average').replace(' (statistical)', '') })
}
const curLoc = (p: any, y: number) => (p.state_timeline || []).filter((e: any) => e.year <= y).slice(-1)[0]?.state || p.state_timeline?.[0]?.state || 'Seattle'

const PERSON: FieldDef = { key: 'person', label: 'Who' }
const LOC: FieldDef = { key: 'location', label: 'Where to' }

// ───────────────────────────── catalog ─────────────────────────────
export const CATALOG: Def[] = [
  // Career & earning changes
  { key: 'retire_earlier', cat: 'career', label: 'Retire earlier', emoji: '🔥', timing: 'point', startLabel: 'Retire', fields: [PERSON],
    desc: 'Stop working sooner: pay and contributions end earlier and withdrawals start earlier.', quick: 'Can I retire earlier?',
    defaults: (_p, c) => ({ start: Math.max(c.cy, c.retYear - 3), person: 'both' }), apply: retireShift },
  { key: 'work_longer', cat: 'career', label: 'Work longer', emoji: '🧭', timing: 'point', startLabel: 'Retire', fields: [PERSON],
    desc: 'Keep working past your planned retirement: more years of pay and saving, fewer of withdrawals.',
    defaults: (_p, c) => ({ start: c.retYear + 3, person: 'both' }), apply: retireShift },
  { key: 'raise', cat: 'career', label: 'Pay raise', emoji: '📈', timing: 'point', startLabel: 'Raise', fields: [{ key: 'pct', label: 'Raise', unit: '%' }, PERSON],
    desc: 'A percentage raise from that year until retirement (on top of your normal raises).',
    defaults: (_p, c) => ({ start: c.cy + 1, pct: 5, person: 'X' }),
    apply: (d, w) => incomeChange(d, w, w.start, 200, -n(w.pct, 5)) },
  { key: 'part_time', cat: 'career', label: 'Go part-time', emoji: '⏳', timing: 'span', startLabel: 'Part-time', endLabel: 'Back full-time',
    fields: [{ key: 'pct', label: 'Pay cut', unit: '%' }, PERSON],
    desc: 'Work fewer hours for a while. Pay and retirement contributions drop by the cut.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: Math.max(c.cy + 2, c.retYear - 1), pct: 50, person: 'X' }),
    apply: (d, w) => incomeChange(d, w, w.start, yrs(w), n(w.pct, 50)) },
  { key: 'sabbatical', cat: 'career', label: 'Take a sabbatical', emoji: '🌴', timing: 'span', startLabel: 'Sabbatical', endLabel: 'Back to work',
    fields: [{ key: 'amount', label: 'Extra travel/fun', unit: '$/yr' }, PERSON], quick: 'What if I take a year off?',
    desc: 'A break from work with no pay, plus whatever you plan to spend while you are off.',
    defaults: (_p, c) => ({ start: c.cy + 3, end: c.cy + 3, amount: 15000, person: 'X' }),
    apply: (d, w) => { incomeChange(d, w, w.start, yrs(w), 100); cost(d, title(w, DEF.sabbatical), n(w.amount), w.start, yrs(w)) } },
  { key: 'unemployment', cat: 'career', label: 'Temporary unemployment', emoji: '📉', timing: 'span', startLabel: 'Job loss', endLabel: 'New job',
    fields: [{ key: 'pct', label: 'Income lost', unit: '%' }, PERSON], quick: 'What if I lose my job?',
    desc: 'A gap between jobs. Use less than 100% if severance or unemployment benefits cover part of it.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: c.cy + 2, pct: 70, person: 'X' }),
    apply: (d, w) => incomeChange(d, w, w.start, yrs(w), n(w.pct, 70)) },
  { key: 'freelance', cat: 'career', label: 'Side / freelance income', emoji: '💻', timing: 'span', startLabel: 'Starts', endLabel: 'Stops',
    fields: [{ key: 'amount', label: 'After tax', unit: '$/mo' }],
    desc: 'Extra money each month from side work (enter it after tax).',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.retYear - 1, amount: 800 }),
    apply: (d, w) => cashIn(d, title(w, DEF.freelance), n(w.amount) * 12, w.start, yrs(w)) },
  { key: 'career_change', cat: 'career', label: 'Career change', emoji: '🔀', timing: 'span', startLabel: 'Retraining', endLabel: 'New career',
    fields: [{ key: 'amount', label: 'Training cost', unit: '$' }, { key: 'pct', label: 'New pay vs today', unit: '%' }, PERSON],
    desc: 'No pay while you retrain, then a new salary (more or less than today) until retirement.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: c.cy + 2, amount: 10000, pct: 10, person: 'X' }),
    apply: (d, w) => { incomeChange(d, w, w.start, yrs(w), 100); incomeChange(d, w, w.start + yrs(w), 200, -n(w.pct)); oneOff(d, title(w, DEF.career_change), n(w.amount), w.start) } },
  { key: 'start_business', cat: 'career', label: 'Start a business', emoji: '🚀', timing: 'span', startLabel: 'Launch', endLabel: 'Profitable',
    fields: [{ key: 'amount', label: 'Startup cost', unit: '$' }, { key: 'pct', label: 'Pay while building', unit: '%' }, { key: 'amount2', label: 'Profit after that', unit: '$/yr' }, PERSON],
    desc: 'Lower pay while the business ramps up, a startup cost, then profit on top of your old pay level.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: c.cy + 3, amount: 35000, pct: 40, amount2: 20000, person: 'X' }),
    apply: (d, w) => { incomeChange(d, w, w.start, yrs(w), 100 - n(w.pct, 40)); oneOff(d, title(w, DEF.start_business), n(w.amount), w.start)
      cashIn(d, `${title(w, DEF.start_business)} profit`, n(w.amount2), w.start + yrs(w), Math.max(1, (yearAtAge(d, 'X', d.parentX_retirement_age)) - (w.start + yrs(w)))) } },
  { key: 'mba', cat: 'career', label: 'Go back to school (MBA)', emoji: '🎓', timing: 'span', startLabel: 'School', endLabel: 'Graduate',
    fields: [{ key: 'amount', label: 'Tuition (total)', unit: '$' }, { key: 'pct', label: 'Pay bump after', unit: '%' }, PERSON], quick: 'What if I go back to school?',
    desc: 'Full-time school with no pay, tuition, then a higher salary after graduating.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: c.cy + 3, amount: 120000, pct: 30, person: 'X' }),
    apply: (d, w) => { incomeChange(d, w, w.start, yrs(w), 100); cost(d, `${title(w, DEF.mba)} tuition`, n(w.amount) / yrs(w), w.start, yrs(w)); incomeChange(d, w, w.start + yrs(w), 200, -n(w.pct)) } },
  { key: 'bootcamp', cat: 'career', label: 'Coding bootcamp', emoji: '⌨️', timing: 'span', startLabel: 'Bootcamp', endLabel: 'New job',
    fields: [{ key: 'amount', label: 'Cost', unit: '$' }, { key: 'pct', label: 'Pay bump after', unit: '%' }, PERSON],
    desc: 'A short retraining (half pay that year) and a raise once you land the new job.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.cy + 1, amount: 15000, pct: 20, person: 'X' }),
    apply: (d, w) => { incomeChange(d, w, w.start, yrs(w), 50); oneOff(d, title(w, DEF.bootcamp), n(w.amount), w.start); incomeChange(d, w, w.start + yrs(w), 200, -n(w.pct)) } },

  // Family & life milestones
  { key: 'child', cat: 'family', label: 'Have a child', emoji: '👶', timing: 'point', startLabel: 'Born', fields: [],
    desc: 'A new child with costs from your location templates (childcare, school, college).',
    defaults: (_p, c) => ({ start: c.cy + 2 }),
    apply: (d, w) => { const nn = (d.children_list || []).length + 1; applyDraft(d, { kind: 'child' }, { name: w.name || `Child ${nn} (what-if)`, year: w.start, school: 'Public', college: 'Public', lifestyle: 'Average' }) } },
  { key: 'wedding', cat: 'family', label: 'Pay for a wedding', emoji: '💍', timing: 'point', startLabel: 'Wedding', fields: [{ key: 'amount', label: 'Cost', unit: '$' }],
    desc: 'A one-time wedding cost paid from savings.',
    defaults: (_p, c) => ({ start: c.cy + 1, amount: 35000 }), apply: (d, w) => oneOff(d, title(w, DEF.wedding), n(w.amount), w.start) },
  { key: 'elder_care', cat: 'family', label: 'Support aging parents', emoji: '🧓', timing: 'span', startLabel: 'Care starts', endLabel: 'Care ends',
    fields: [{ key: 'amount', label: 'Cost', unit: '$/mo' }],
    desc: 'Monthly help for a parent: care, housing or bills.',
    defaults: (_p, c) => ({ start: c.cy + 10, end: c.cy + 19, amount: 2500 }), apply: (d, w) => cost(d, title(w, DEF.elder_care), n(w.amount) * 12, w.start, yrs(w)) },
  { key: 'college', cat: 'family', label: "Pay for a child's college", emoji: '🏫', timing: 'span', startLabel: 'College', endLabel: 'Graduates',
    fields: [{ key: 'amount', label: 'Total cost', unit: '$' }], quick: 'Are we saving enough for college?',
    desc: 'Tuition and living costs spread over the college years (in addition to anything your kids already have).',
    defaults: (_p, c) => ({ start: c.cy + 16, end: c.cy + 19, amount: 160000 }), apply: (d, w) => cost(d, title(w, DEF.college), n(w.amount) / yrs(w), w.start, yrs(w)) },
  { key: 'inheritance', cat: 'family', label: 'Receive an inheritance', emoji: '🎁', timing: 'point', startLabel: 'Received', fields: [{ key: 'amount', label: 'Amount', unit: '$' }],
    desc: 'A one-time inheritance or gift coming in.',
    defaults: (_p, c) => ({ start: c.cy + 10, amount: 100000 }),
    apply: (d, w) => applyDraft(d, { kind: 'windfall' }, { name: title(w, DEF.inheritance), year: w.start, amount: n(w.amount), recipient: 'Parent 1', separate: true }) },
  { key: 'gift_out', cat: 'family', label: 'Yearly gifts to family', emoji: '🤝', timing: 'span', startLabel: 'Gifts start', endLabel: 'Gifts end',
    fields: [{ key: 'amount', label: 'Per year', unit: '$/yr' }],
    desc: 'Help children or family every year (up to the annual gift-tax exclusion per person).',
    defaults: (_p, c) => ({ start: c.cy, end: c.cy + 15, amount: 19000 }), apply: (d, w) => cost(d, title(w, DEF.gift_out), n(w.amount), w.start, yrs(w)) },
  { key: 'gift_in', cat: 'family', label: 'Receive yearly family gifts', emoji: '💝', timing: 'span', startLabel: 'Gifts start', endLabel: 'Gifts end',
    fields: [{ key: 'amount', label: 'Per year', unit: '$/yr' }],
    desc: 'Regular gifts coming in from parents or family.',
    defaults: (_p, c) => ({ start: c.cy, end: c.cy + 9, amount: 7500 }), apply: (d, w) => cashIn(d, title(w, DEF.gift_in), n(w.amount), w.start, yrs(w)) },
  { key: 'charity', cat: 'family', label: 'Charitable giving', emoji: '🌱', timing: 'span', startLabel: 'Giving starts', endLabel: 'Giving ends',
    fields: [{ key: 'amount', label: 'Per year', unit: '$/yr' }],
    desc: 'Donate a fixed amount every year (starting at retirement by default).',
    defaults: (_p, c) => ({ start: c.retYear, end: c.last, amount: 10000 }), apply: (d, w) => cost(d, title(w, DEF.charity), n(w.amount), w.start, yrs(w)) },

  // Big purchases & lifestyle
  { key: 'travel', cat: 'purchases', label: 'Extensive travel', emoji: '✈️', timing: 'span', startLabel: 'Travel', endLabel: 'Slow down',
    fields: [{ key: 'amount', label: 'Per year', unit: '$/yr' }],
    desc: 'Fund the go-go years: long trips, time abroad, adventures.',
    defaults: (_p, c) => ({ start: c.retYear, end: c.retYear + 9, amount: 15000 }), apply: (d, w) => cost(d, title(w, DEF.travel), n(w.amount), w.start, yrs(w)) },
  { key: 'big_purchase', cat: 'purchases', label: 'Big purchase', emoji: '🛍️', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Cost', unit: '$' }],
    desc: 'A one-off purchase paid from savings in the year you choose.',
    defaults: (_p, c) => ({ start: c.cy + 1, amount: 20000 }), apply: (d, w) => oneOff(d, title(w, DEF.big_purchase), n(w.amount), w.start) },
  { key: 'new_car', cat: 'purchases', label: 'Buy a new car', emoji: '🚗', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Price', unit: '$' }],
    desc: 'Replace your car with a new one, paid in cash.', quick: 'Can we afford this car?',
    defaults: (_p, c) => ({ start: c.cy + 1, amount: 45000 }), apply: (d, w) => oneOff(d, title(w, DEF.new_car), n(w.amount), w.start) },
  { key: 'car_cycle', cat: 'purchases', label: 'Replace the car every 8 years', emoji: '🔁', timing: 'span', startLabel: 'First car', endLabel: 'Last car',
    fields: [{ key: 'amount', label: 'Price', unit: '$' }],
    desc: 'A car purchase every 8 years for as long as you choose.',
    defaults: (_p, c) => ({ start: c.cy + 2, end: c.last - 10, amount: 40000 }),
    apply: (d, w) => applyDraft(d, { kind: 'recurring' }, { name: title(w, DEF.car_cycle), amount: n(w.amount), every: 8, year: w.start, until: w.end ?? null }) },
  { key: 'remodel_cash', cat: 'purchases', label: 'Major remodel (cash)', emoji: '🔨', timing: 'point', startLabel: 'Remodel', fields: [{ key: 'amount', label: 'Cost', unit: '$' }],
    desc: 'A renovation paid out of pocket.', quick: 'Can we afford a remodel?',
    defaults: (_p, c) => ({ start: c.cy + 1, amount: 75000 }), apply: (d, w) => oneOff(d, title(w, DEF.remodel_cash), n(w.amount), w.start) },
  { key: 'remodel_loan', cat: 'purchases', label: 'Major remodel (HELOC)', emoji: '🏗️', timing: 'point', startLabel: 'Remodel', fields: [{ key: 'amount', label: 'Cost', unit: '$' }],
    desc: 'A renovation financed over 10 years at 8.5%.',
    defaults: (_p, c) => ({ start: c.cy + 1, amount: 75000 }), apply: (d, w) => oneOff(d, title(w, DEF.remodel_loan), n(w.amount), w.start, 10, 8.5) },
  { key: 'buy_home', cat: 'purchases', label: 'Buy a home', emoji: '🏡', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Price', unit: '$' }, { key: 'pct', label: 'Down payment', unit: '%' }],
    desc: 'Buy a home with a 30-year mortgage at 6.5% (property tax, insurance and upkeep included).', quick: 'Can we afford this house?',
    defaults: (_p, c) => ({ start: c.cy + 2, amount: 850000, pct: 20 }),
    apply: (d, w, c) => applyDraft(d, { kind: 'house_buy' }, { name: title(w, DEF.buy_home), year: w.start, price: n(w.amount), down: n(w.pct, 20), rate: 6.5, term: 30, location: curLoc(d, w.start), appreciation: 3 }) },
  { key: 'vacation_home', cat: 'purchases', label: 'A place to get away', emoji: '🏕️', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Price', unit: '$' }, { key: 'pct', label: 'Down payment', unit: '%' }],
    desc: 'A cabin or vacation home with its own mortgage and running costs.',
    defaults: (_p, c) => ({ start: c.cy + 5, amount: 450000, pct: 25 }),
    apply: (d, w) => applyDraft(d, { kind: 'house_buy' }, { name: title(w, DEF.vacation_home), year: w.start, price: n(w.amount), down: n(w.pct, 25), rate: 7, term: 30, location: curLoc(d, w.start), appreciation: 3 }) },
  { key: 'move_up', cat: 'purchases', label: 'Move to a higher-cost city', emoji: '🌆', timing: 'point', startLabel: 'Move', fields: [LOC],
    desc: 'Relocate: prices, rent and taxes change to the new place from that year.',
    defaults: (_p, c) => ({ start: c.cy + 2, location: 'San Francisco' }), apply: (d, w) => move(d, w) },
  { key: 'lifestyle_up', cat: 'purchases', label: 'Upgrade your lifestyle', emoji: '🥂', timing: 'span', startLabel: 'Upgrade', endLabel: 'Ends',
    fields: [{ key: 'pct', label: 'Spend more on everyday things by', unit: '%' }],
    desc: 'Raise everyday (non-housing) spending: dining, travel, hobbies, nicer things.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.last, pct: 25 }), apply: (d, w, c) => cost(d, title(w, DEF.lifestyle_up), c.flex * n(w.pct, 25) / 100, w.start, yrs(w)) },
  { key: 'custom_cost', cat: 'purchases', label: 'Custom yearly cost', emoji: '🧾', timing: 'span', startLabel: 'Starts', endLabel: 'Ends',
    fields: [{ key: 'amount', label: 'Cost', unit: '$/yr' }],
    desc: 'Anything else that costs money every year for a while. Rename it to what it is.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.cy + 5, amount: 12000 }), apply: (d, w) => cost(d, title(w, DEF.custom_cost), n(w.amount), w.start, yrs(w)) },
  { key: 'custom_income', cat: 'career', label: 'Custom extra income', emoji: '💵', timing: 'span', startLabel: 'Starts', endLabel: 'Ends',
    fields: [{ key: 'amount', label: 'After tax', unit: '$/yr' }],
    desc: 'Any other money coming in every year for a while (after tax). Rename it to what it is.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.cy + 5, amount: 12000 }), apply: (d, w) => cashIn(d, title(w, DEF.custom_income), n(w.amount), w.start, yrs(w)) },

  // Building wealth & investing
  { key: 'max_401k', cat: 'wealth', label: 'Max out the 401(k)', emoji: '🏦', timing: 'none', fields: [{ key: 'amount', label: 'Per person', unit: '$/yr' }],
    desc: 'Contribute the yearly limit to pre-tax 401(k)s while working.',
    defaults: () => ({ amount: 24500 }),
    apply: (d, w) => { for (const p of people(d, { ...w, person: 'both' })) d[`parent${p}_pretax_401k`] = n(w.amount, 24500) } },
  { key: 'roth_ira', cat: 'wealth', label: 'Max out Roth IRAs', emoji: '🌳', timing: 'none', fields: [{ key: 'amount', label: 'Household', unit: '$/yr' }],
    desc: 'Add Roth IRA contributions every working year.',
    defaults: (p) => ({ amount: single(p) ? 7500 : 15000 }), apply: (d, w) => { d.roth_contribution = n(d.roth_contribution) + n(w.amount) } },
  { key: 'spend_less', cat: 'wealth', label: 'Spend less, invest the difference', emoji: '💰', timing: 'span', startLabel: 'Cut starts', endLabel: 'Cut ends',
    fields: [{ key: 'pct', label: 'Cut flexible spending by', unit: '%' }],
    desc: 'Trim everyday spending (not housing) by a percentage; the savings stay invested.',
    defaults: (_p, c) => ({ start: c.cy, end: c.retYear - 1, pct: 10 }), apply: (d, w, c) => cashIn(d, title(w, DEF.spend_less), c.flex * n(w.pct, 10) / 100, w.start, yrs(w)) },
  { key: 'rental', cat: 'wealth', label: 'Buy a rental property', emoji: '🏘️', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Price', unit: '$' }, { key: 'pct', label: 'Down payment', unit: '%' }, { key: 'amount2', label: 'Rent', unit: '$/mo' }],
    desc: 'A cash-flowing rental: mortgage and running costs out, rent in.',
    defaults: (_p, c) => ({ start: c.cy + 2, amount: 450000, pct: 25, amount2: 2800 }),
    apply: (d, w) => { applyDraft(d, { kind: 'house_buy' }, { name: title(w, DEF.rental), year: w.start, price: n(w.amount), down: n(w.pct, 25), rate: 7, term: 30, location: curLoc(d, w.start), appreciation: 3 })
      const h = d.houses[d.houses.length - 1]; h.timeline = [{ year: w.start, status: 'Own_Rent', rental_income: n(w.amount2) }] } },
  { key: 'stock_mix', cat: 'wealth', label: 'Change your investment mix', emoji: '⚖️', timing: 'none', fields: [{ key: 'pct', label: 'Stocks', unit: '%' }], quick: 'Is my portfolio balanced?',
    desc: 'Hold a different share of stocks vs bonds (affects returns and Monte Carlo swings).',
    defaults: () => ({ pct: 60 }),
    apply: (d, w) => {
      // investment_return is the expected return of today's mix: back out the stock return and re-mix (engine.py _returns)
      const a0 = Math.max(0.01, n(d.mc_stock_allocation, 100) / 100), a1 = Math.min(1, Math.max(0, n(w.pct, 60) / 100))
      const bond = n(d.bond_return, 0.04), r = n(d.economic_params?.investment_return, 0.06)
      const rs = (r - (1 - a0) * bond) / a0
      d.economic_params = { ...(d.economic_params || {}), investment_return: a1 * rs + (1 - a1) * bond }
      for (const k of ['mc_return_variability', 'mc_return_variability_positive', 'mc_return_variability_negative'])
        if (d[k] != null) d[k] = d[k] * Math.max(0.15, a1 / a0)
      d.mc_stock_allocation = a1 * 100
    } },
  { key: 'roth_ladder', cat: 'wealth', label: 'Roth conversion ladder', emoji: '🪜', timing: 'span', startLabel: 'Conversions', endLabel: 'Stop',
    fields: [{ key: 'pct', label: 'Fill up to bracket', unit: '%' }], quick: 'How much should I convert to Roth?',
    desc: 'Convert pre-tax money to Roth each year, filling a tax bracket (the cheap years between retiring and RMDs).',
    defaults: (_p, c) => ({ start: c.retYear, end: Math.min(c.last, c.retYear + 9), pct: 12 }),
    apply: (d, w) => { d.roth_conversion = { ...(d.roth_conversion || {}), mode: 'fill_bracket', bracket: n(w.pct, 12) / 100, start_age: ageAt(d, 'X', w.start), end_age: ageAt(d, 'X', w.end ?? w.start) } } },
  { key: 'ss_early', cat: 'wealth', label: 'Claim Social Security early', emoji: '⏩', timing: 'point', startLabel: 'Claim', fields: [PERSON],
    desc: 'Start benefits as early as 62: smaller checks, for more years.',
    defaults: (p) => ({ start: yearAtAge(p, 'X', 62), person: 'both' }),
    apply: (d, w) => { const a = ageAt(d, 'X', w.start); for (const p of people(d, w)) d[`parent${p}_ss_claim_age`] = Math.min(70, Math.max(62, a + (p === 'Y' ? d.parentY_age - d.parentX_age : 0))) } },
  { key: 'ss_delay', cat: 'wealth', label: 'Delay Social Security to 70', emoji: '⏸️', timing: 'point', startLabel: 'Claim', fields: [PERSON],
    desc: 'Wait for the biggest check: about 8% more for each year past full retirement age.',
    defaults: (p) => ({ start: yearAtAge(p, 'X', 70), person: 'both' }),
    apply: (d, w) => { const a = ageAt(d, 'X', w.start); for (const p of people(d, w)) d[`parent${p}_ss_claim_age`] = Math.min(70, Math.max(62, a + (p === 'Y' ? d.parentY_age - d.parentX_age : 0))) } },
  { key: 'annuity', cat: 'wealth', label: 'Buy an annuity', emoji: '🛡️', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Premium', unit: '$' }, { key: 'amount2', label: 'Pays', unit: '$/mo' }],
    desc: 'Trade a lump sum for guaranteed income for life (annuity vs keeping it invested).',
    defaults: (_p, c) => ({ start: c.retYear, amount: 200000, amount2: 1150 }),
    apply: (d, w) => { oneOff(d, `${title(w, DEF.annuity)} premium`, n(w.amount), w.start)
      applyDraft(d, { kind: 'pension' }, { name: title(w, DEF.annuity), person: 'Parent 1', year: w.start, monthly: n(w.amount2), cola: 0, survivor: 100 }) } },
  { key: 'buy_business', cat: 'wealth', label: 'Buy an existing business', emoji: '🏪', timing: 'point', startLabel: 'Buy', fields: [{ key: 'amount', label: 'Price', unit: '$' }, { key: 'amount2', label: 'Profit after tax', unit: '$/yr' }],
    desc: 'Buy a cash-flowing business: a lump sum out, profit in every year until you retire.',
    defaults: (_p, c) => ({ start: c.cy + 3, amount: 250000, amount2: 45000 }),
    apply: (d, w, c) => { oneOff(d, title(w, DEF.buy_business), n(w.amount), w.start); cashIn(d, `${title(w, DEF.buy_business)} profit`, n(w.amount2), w.start, Math.max(1, c.retYear - w.start)) } },

  // Reducing costs & simplifying
  { key: 'move_down', cat: 'costs', label: 'Move somewhere cheaper', emoji: '🏞️', timing: 'point', startLabel: 'Move', fields: [LOC],
    desc: 'Relocate (at retirement by default) to cut living costs and maybe taxes.',
    defaults: (_p, c) => ({ start: c.retYear, location: 'Austin' }), apply: (d, w) => move(d, w) },
  { key: 'rural', cat: 'costs', label: 'Move to a rural area', emoji: '🌾', timing: 'point', startLabel: 'Move', fields: [LOC],
    desc: 'A lower-cost state for retirement.',
    defaults: (_p, c) => ({ start: c.retYear, location: 'Mississippi' }), apply: (d, w) => move(d, w) },
  { key: 'overseas', cat: 'costs', label: 'Retire overseas', emoji: '🌍', timing: 'point', startLabel: 'Move abroad', fields: [LOC],
    desc: 'Move abroad at retirement: local prices and taxes apply.',
    defaults: (_p, c) => ({ start: c.retYear, location: 'Portugal' }), apply: (d, w) => move(d, w) },
  { key: 'simplify', cat: 'costs', label: 'Live more simply', emoji: '🌿', timing: 'span', startLabel: 'Simplify', endLabel: 'Ends',
    fields: [{ key: 'pct', label: 'Cut everyday spending by', unit: '%' }],
    desc: 'A simpler, minimalist life: everyday (non-housing) spending drops by this much for good.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.last, pct: 20 }), apply: (d, w, c) => cashIn(d, title(w, DEF.simplify), c.flex * n(w.pct, 20) / 100, w.start, yrs(w)) },
  { key: 'downsize', cat: 'costs', label: 'Downsize your home', emoji: '📦', timing: 'point', startLabel: 'Downsize', fields: [{ key: 'amount', label: 'Smaller home price', unit: '$' }],
    desc: 'Sell your home and buy a smaller one with cash from the sale.',
    available: (_p, c) => c.hasHome ? null : 'Add a home first',
    defaults: (_p, c) => ({ start: c.retYear, amount: 450000 }),
    apply: (d, w) => { const hi = (d.houses || []).findIndex((h: any) => h.purchase_year <= w.start); if (hi < 0) return
      applyDraft(d, { kind: 'house_event' }, { house: String(hi), status: 'Sold', year: w.start })
      applyDraft(d, { kind: 'house_buy' }, { name: title(w, DEF.downsize), year: w.start, price: n(w.amount), down: 100, rate: 0, term: 1, location: curLoc(d, w.start), appreciation: 3 }) } },
  { key: 'sell_home', cat: 'costs', label: 'Sell the house and rent', emoji: '🔑', timing: 'point', startLabel: 'Sell', fields: [{ key: 'amount', label: 'Rent', unit: '$/mo' }],
    desc: 'Sell your home, invest the equity and rent instead.',
    available: (_p, c) => c.hasHome ? null : 'Add a home first',
    defaults: (_p, c) => ({ start: c.retYear, amount: 2500 }),
    apply: (d, w, c) => { const hi = (d.houses || []).findIndex((h: any) => h.purchase_year <= w.start); if (hi < 0) return
      applyDraft(d, { kind: 'house_event' }, { house: String(hi), status: 'Sold', year: w.start }); cost(d, `${title(w, DEF.sell_home)} rent`, n(w.amount) * 12, w.start, Math.max(1, c.last - w.start + 1)) } },
  { key: 'cut_subs', cat: 'costs', label: 'Cut subscriptions & extras', emoji: '✂️', timing: 'span', startLabel: 'Cut', endLabel: 'Ends',
    fields: [{ key: 'amount', label: 'Saved', unit: '$/mo' }],
    desc: 'Cancel subscriptions and small recurring extras.',
    defaults: (_p, c) => ({ start: c.cy, end: c.last, amount: 150 }), apply: (d, w) => cashIn(d, title(w, DEF.cut_subs), n(w.amount) * 12, w.start, yrs(w)) },

  // Stress testing
  { key: 'job_loss_long', cat: 'stress', label: 'Extended job loss', emoji: '⚠️', timing: 'span', startLabel: 'Job loss', endLabel: 'Re-employed',
    fields: [{ key: 'pct', label: 'Income lost', unit: '%' }, PERSON],
    desc: 'A long stretch without work and with no benefits.',
    defaults: (_p, c) => ({ start: c.cy + 3, end: c.cy + 4, pct: 100, person: 'X' }), apply: (d, w) => incomeChange(d, w, w.start, yrs(w), n(w.pct, 100)) },
  { key: 'crash', cat: 'stress', label: 'Market crash', emoji: '📉', timing: 'point', startLabel: 'Crash', fields: [{ key: 'pct', label: 'Drop', unit: '%' }], quick: 'What if the market crashes?',
    desc: 'Investments fall by this much in one year. Drag the marker onto your retirement year to see sequence risk.',
    defaults: (_p, c) => ({ start: c.retYear, pct: 35 }), apply: (d, w) => stress(d, { type: 'market_crash', year: w.start, drop: -Math.abs(n(w.pct, 35)) / 100 }) },
  { key: 'boom_bust', cat: 'stress', label: 'Boom & bust market cycles', emoji: '🎢', timing: 'span', startLabel: 'First bust', endLabel: 'Cycles end',
    fields: [{ key: 'pct', label: 'Bust size', unit: '%' }],
    desc: 'A bust every 8 years with strong recoveries in between. The marker sets when the first bust hits.',
    defaults: (_p, c) => ({ start: c.cy + 4, end: c.last, pct: 25 }),
    apply: (d, w) => { const bust = -Math.abs(n(w.pct, 25)) / 100; const up = Math.pow(1 / (1 + bust), 1 / 7) - 1
      for (let y = w.start; y <= (w.end ?? w.start); y++) {
        if ((y - w.start) % 8 === 0) stress(d, { type: 'market_crash', year: y, drop: bust })
        else stress(d, { type: 'return_shift', shift: up * 0.9, start_year: y, years: 1 })
      } } },
  { key: 'lost_decade', cat: 'stress', label: 'A lost decade of returns', emoji: '🐌', timing: 'span', startLabel: 'Slump', endLabel: 'Recovery',
    fields: [{ key: 'pct', label: 'Lower returns by', unit: '%' }],
    desc: 'Returns lower than expected every year for a while (like 2000–2009).',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.cy + 10, pct: 4 }), apply: (d, w) => stress(d, { type: 'return_shift', shift: -Math.abs(n(w.pct, 4)) / 100, start_year: w.start, years: yrs(w) }) },
  { key: 'inflation', cat: 'stress', label: 'High inflation period', emoji: '🔥', timing: 'span', startLabel: 'Inflation', endLabel: 'Normal',
    fields: [{ key: 'pct', label: 'Inflation rate', unit: '%' }],
    desc: 'A burst of high inflation. Prices stay higher afterwards; pay catches up only partly.',
    defaults: (_p, c) => ({ start: c.cy + 1, end: c.cy + 5, pct: 8 }), apply: (d, w) => stress(d, { type: 'inflation_spike', start_year: w.start, years: yrs(w), rate: n(w.pct, 8) / 100, wage_passthrough: 50 }) },
  { key: 'medical', cat: 'stress', label: 'Major medical emergency', emoji: '🏥', timing: 'point', startLabel: 'Emergency', fields: [{ key: 'amount', label: 'Out of pocket', unit: '$' }],
    desc: 'Unexpected medical costs in one year.',
    defaults: (_p, c) => ({ start: c.cy + 4, amount: 50000 }), apply: (d, w) => oneOff(d, title(w, DEF.medical), n(w.amount), w.start) },
  { key: 'ltc', cat: 'stress', label: 'Long-term care', emoji: '🩺', timing: 'span', startLabel: 'Care starts', endLabel: 'Care ends',
    fields: [{ key: 'amount', label: 'Cost', unit: '$/yr' }],
    desc: 'Assisted living or in-home care late in life (today’s dollars). Drag the markers to change when it starts or how long it lasts.',
    defaults: (p) => ({ start: yearAtAge(p, 'X', 82), end: yearAtAge(p, 'X', 84), amount: 110000 }), apply: (d, w) => cost(d, title(w, DEF.ltc), n(w.amount), w.start, yrs(w)) },
  { key: 'ss_cut', cat: 'stress', label: 'Social Security cuts', emoji: '🏛️', timing: 'point', startLabel: 'Cuts start', fields: [{ key: 'pct', label: 'Cut', unit: '%' }],
    desc: 'The trust fund runs short and benefits are cut across the board from that year unless Congress acts.',
    defaults: () => ({ start: 2033, pct: 23 }), apply: (d, w) => { d.ss_insolvency_enabled = true; d.ss_insolvency_year = w.start; d.ss_shortfall_percentage = n(w.pct, 23) } },
  { key: 'disability', cat: 'stress', label: 'Disability', emoji: '🦽', timing: 'span', startLabel: 'Disabled', endLabel: 'Recovered',
    fields: [{ key: 'pct', label: 'Income lost', unit: '%' }, PERSON],
    desc: 'Unable to work for a while; use less than 100% if disability insurance replaces part of your pay.',
    defaults: (_p, c) => ({ start: c.cy + 6, end: c.cy + 8, pct: 40, person: 'X' }), apply: (d, w) => incomeChange(d, w, w.start, yrs(w), n(w.pct, 40)) },
  { key: 'early_death', cat: 'stress', label: 'Early death', emoji: '🕊️', timing: 'point', startLabel: 'Death', fields: [PERSON, { key: 'amount', label: 'Life insurance', unit: '$' }],
    desc: 'One partner dies early: their pay and Social Security stop (survivor benefits apply) and any life insurance pays out.',
    available: (_p, c) => c.single ? 'For couples' : null,
    defaults: (p, c) => ({ start: c.cy + 10, person: single(p) ? 'X' : 'Y', amount: 0 }),
    apply: (d, w) => stress(d, { type: 'early_death', person: w.person === 'Y' ? 2 : 1, year: w.start, life_insurance: n(w.amount) }) },
]
export const DEF: Record<string, Def> = Object.fromEntries(CATALOG.map(d => [d.key, d]))

// ───────────────────────────── plan-level API ─────────────────────────────
export function ctxFor(p: any): Ctx {
  const cy = p.current_year
  const s = single(p)
  const retYearX = yearAtAge(p, 'X', p.parentX_retirement_age)
  const retYearY = s ? retYearX : yearAtAge(p, 'Y', p.parentY_retirement_age)
  const HOUSING = new Set(['Mortgage/Rent', 'Property Tax', 'Home Insurance', 'HOA', 'Home Improvement'])
  let flex = Object.values(p.parentX_expenses || {}).reduce((a: number, v: any) => a + (+v || 0), 0)
  if (!s) flex += Object.values(p.parentY_expenses || {}).reduce((a: number, v: any) => a + (+v || 0), 0)
  flex += Object.entries(p.family_shared_expenses || {}).reduce((a: number, [k, v]: any) => a + (HOUSING.has(k) ? 0 : (+v || 0)), 0)
  return { cy, retYear: Math.min(retYearX, retYearY), retYearX, retYearY, last: endYear(p), single: s, flex,
    inflation: p.economic_params?.inflation_rate ?? 0.03, hasHome: (p.houses || []).length > 0, hasDebt: (p.debts || []).length > 0 }
}

const uid = () => `wi${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`

export function create(p: any, key: string, at?: number): WhatIf {
  const def = DEF[key]
  const c = ctxFor(p)
  const base: Partial<WhatIf> = { start: c.cy, ...def.defaults(p, c) }
  const w = { ...base, id: uid(), key, on: true } as WhatIf
  if (at != null && def.timing !== 'none') {
    const len = (w.end ?? w.start) - w.start
    w.start = at
    if (def.timing === 'span') w.end = at + Math.max(0, len)
  }
  return clampWhatIf(p, w)
}

export function clampWhatIf(p: any, w: WhatIf): WhatIf {
  const c = ctxFor(p)
  const def = DEF[w.key]
  const x = { ...w }
  x.start = Math.round(Math.min(Math.max(x.start, c.cy), c.last))
  if (def?.timing === 'span') x.end = Math.round(Math.min(Math.max(x.end ?? x.start, x.start), c.last))
  return x
}

/** The plan with every enabled what-if applied (plus the market lens). Never saved as-is. */
export function applyAll(p: any, list: WhatIf[] | undefined, lens: Lens = 'likely', skipId?: string): any {
  const d = structuredClone(p)
  delete d._stress
  const c = ctxFor(p)
  for (const w of list || []) {
    if (!w.on || w.id === skipId) continue
    const def = DEF[w.key]
    if (!def || def.available?.(p, c)) continue
    try { def.apply(d, w, c) } catch { /* a bad what-if never breaks the projection */ }
  }
  applyLens(d, lens, c)
  return d
}

/** Can this what-if be written into the plan for good? (Only if it is made of ordinary plan items.) */
export function canBake(p: any, w: WhatIf): boolean {
  const d = applyAll(p, [{ ...w, on: true }])
  return !(d._stress || []).length
}

/** Write one what-if into the plan draft permanently and drop it from the list. */
export function bake(d: any, w: WhatIf) {
  const c = ctxFor(d)
  DEF[w.key].apply(d, { ...w, name: w.name || DEF[w.key].label.replace(/ \(what-if\)$/, '') }, c)
  delete d._stress
  d.whatifs = (d.whatifs || []).filter((x: WhatIf) => x.id !== w.id)
}

/** A copy that other pages and the engine understand: plan items baked in, the rest stay listed as what-ifs. */
export function asScenario(p: any): any {
  const d = structuredClone(p)
  const keep: WhatIf[] = []
  for (const w of d.whatifs || []) {
    if (w.on && canBake(p, w)) bake(d, w)
    else keep.push(w)
  }
  d.whatifs = keep
  delete d._stress
  return d
}

// ───────────────────────────── market lens ─────────────────────────────
export type Lens = 'best' | 'likely' | 'conservative' | 'worst'
export const LENSES: { value: Lens; label: string; hint: string }[] = [
  { value: 'best', label: 'Best case', hint: 'Returns 1.5 points higher every year' },
  { value: 'likely', label: 'Likely', hint: 'Your plan’s assumptions' },
  { value: 'conservative', label: 'Conservative', hint: 'Returns 1.5 points lower every year' },
  { value: 'worst', label: 'Worst case', hint: 'Lower returns plus a 35% crash the year you retire' },
]
function applyLens(d: any, lens: Lens, c: Ctx) {
  if (lens === 'best') stress(d, { type: 'return_shift', shift: 0.015 })
  if (lens === 'conservative' || lens === 'worst') stress(d, { type: 'return_shift', shift: -0.015 })
  if (lens === 'worst') stress(d, { type: 'market_crash', year: c.retYear, drop: -0.35 })
}

// ───────────────────────────── markers & text ─────────────────────────────
export interface Marker { id: string; wid: string; edge: 'start' | 'end'; year: number; label: string; emoji: string; color: string; min: number; max: number }

export const COLORS = ['#2563eb', '#ea580c', '#059669', '#7c3aed', '#db2777', '#0891b2', '#ca8a04', '#dc2626', '#4f46e5', '#16a34a']
export const colorFor = (list: WhatIf[], id: string) => COLORS[Math.max(0, list.findIndex(w => w.id === id)) % COLORS.length]

export function markers(p: any, list: WhatIf[]): Marker[] {
  const c = ctxFor(p)
  const out: Marker[] = []
  for (const w of list) {
    const def = DEF[w.key]
    if (!def || !w.on || def.timing === 'none') continue
    const color = colorFor(list, w.id)
    out.push({ id: `${w.id}:s`, wid: w.id, edge: 'start', year: w.start, label: title(w, def), emoji: def.emoji, color,
      min: c.cy, max: def.timing === 'span' ? (w.end ?? c.last) : c.last })
    if (def.timing === 'span' && w.end != null)
      out.push({ id: `${w.id}:e`, wid: w.id, edge: 'end', year: w.end, label: `${def.endLabel || 'Ends'} (${title(w, def).toLowerCase()})`.slice(0, 34), emoji: '⏹', color,
        min: w.start, max: c.last })
  }
  return out
}

export function moveMarker(list: WhatIf[], m: Marker, year: number, keepLength: boolean): WhatIf[] {
  return list.map(w => {
    if (w.id !== m.wid) return w
    if (m.edge === 'end') return { ...w, end: Math.max(w.start, year) }
    if (keepLength && w.end != null) { const len = w.end - w.start; return { ...w, start: year, end: year + len } }
    return { ...w, start: year, end: w.end != null ? Math.max(year, w.end) : w.end }
  })
}

export function whenText(p: any, w: WhatIf): string {
  const def = DEF[w.key]
  if (!def || def.timing === 'none') return 'Every working year'
  const a = (y: number) => `age ${ageAt(p, 'X', y)}`
  if (def.timing === 'point' || (w.end ?? w.start) === w.start) return `${w.start} (${a(w.start)})`
  return `${w.start}–${w.end ?? w.start} (${a(w.start)}–${ageAt(p, 'X', w.end ?? w.start)})`
}

export function amountText(w: WhatIf): string {
  const def = DEF[w.key]
  const parts: string[] = []
  for (const f of def?.fields || []) {
    const v = (w as any)[f.key]
    if (v == null || f.key === 'person' || f.key === 'location') { if (f.key === 'location' && v) parts.push(String(v)); continue }
    const s = f.unit === '%' ? `${v}%` : `$${Math.round(+v).toLocaleString('en-US')}${f.unit === '$/mo' ? '/mo' : f.unit === '$/yr' ? '/yr' : ''}`
    parts.push(`${f.label}: ${s}`)
  }
  return parts.join(' · ')
}

/** Work-optional (financial independence) year: investable money covers the rest of life's spending at a 4% draw. */
export function fiYear(rows: any[]): number | null {
  for (const r of rows || []) {
    const spend = (r.total_expenses || 0) + (r.taxes || 0) * 0.5
    if (spend > 0 && r.investable >= spend * 25) return r.year
  }
  return null
}

export const personLabel = (p: any, who?: Who) => who === 'Y' ? (p.parent2_name || 'Person 2') : who === 'X' ? (p.parent1_name || 'Person 1') : 'Both'
export { personNum }
