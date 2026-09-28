/** Pure helpers for the drag-and-drop life editor: turn a plan into timeline items, and apply edits back.
 *  Every function takes a mutable plan draft `d` (inside usePlan().update or a scenario copy). */

export type Lane = 'people' | 'where' | 'home' | 'kids' | 'money' | 'goals'
export type Kind = 'retire' | 'ss' | 'end' | 'job' | 'phase' | 'move' | 'house_buy' | 'house_event' | 'child' | 'purchase' | 'recurring'
  | 'windfall' | 'pension' | 'debt' | 'goal'
export interface Ref { kind: Kind; idx?: number; who?: 'X' | 'Y'; e?: number }
export interface Item { id: string; lane: Lane; ref: Ref; year: number; end?: number; label: string; sub?: string; draggable: boolean;
  min?: number; max?: number; tone?: string }

export const LANES: { key: Lane; label: string }[] = [
  { key: 'people', label: 'People & work' }, { key: 'where', label: 'Where you live' }, { key: 'home', label: 'Homes' },
  { key: 'kids', label: 'Kids' }, { key: 'money', label: 'Money events' }, { key: 'goals', label: 'Goals' },
]

export const PALETTE: { kind: Kind; label: string; lane: Lane; hint: string }[] = [
  { kind: 'move', label: 'Move', lane: 'where', hint: 'Relocate (changes taxes and prices)' },
  { kind: 'child', label: 'Child', lane: 'kids', hint: 'A new child, born that year' },
  { kind: 'house_buy', label: 'Buy a home', lane: 'home', hint: 'Buy with a mortgage' },
  { kind: 'house_event', label: 'Sell / rent out', lane: 'home', hint: 'Sell a home, rent it out or move back in' },
  { kind: 'job', label: 'Job change', lane: 'people', hint: 'New salary from that year' },
  { kind: 'purchase', label: 'Big purchase', lane: 'money', hint: 'Wedding, car, renovation…' },
  { kind: 'recurring', label: 'Recurring cost', lane: 'money', hint: 'Every N years: cars, trips…' },
  { kind: 'windfall', label: 'Gift / inheritance', lane: 'money', hint: 'Cash coming in' },
  { kind: 'pension', label: 'Pension', lane: 'money', hint: 'Guaranteed income from an age' },
  { kind: 'debt', label: 'Loan', lane: 'money', hint: 'Student or car loan' },
  { kind: 'goal', label: 'Goal', lane: 'goals', hint: 'A milestone to track' },
]

const nm = (p: any, who: 'X' | 'Y') => (who === 'X' ? p.parent1_name : p.parent2_name) || (who === 'X' ? 'Person 1' : 'Person 2')
const single = (p: any) => !p.parent2_name || p.parent2_name === 'N/A'
export const ageAt = (p: any, who: 'X' | 'Y', y: number) => p[`parent${who}_age`] + (y - p.current_year)
export const yearAtAge = (p: any, who: 'X' | 'Y', a: number) => p.current_year + (a - p[`parent${who}_age`])
export const endYear = (p: any) => Math.max(yearAtAge(p, 'X', p.parentX_death_age), single(p) ? 0 : yearAtAge(p, 'Y', p.parentY_death_age))
const whoKey = (w: string) => (w === 'Parent 2' ? 'Y' : 'X') as 'X' | 'Y'

export function items(p: any, proj?: any): Item[] {
  const cy = p.current_year
  const end = endYear(p)
  const out: Item[] = []
  const people: ('X' | 'Y')[] = single(p) ? ['X'] : ['X', 'Y']
  for (const w of people) {
    const ry = yearAtAge(p, w, p[`parent${w}_retirement_age`])
    out.push({ id: `retire${w}`, lane: 'people', ref: { kind: 'retire', who: w }, year: ry, label: `${nm(p, w)} retires`, sub: `age ${p[`parent${w}_retirement_age`]}`, draggable: true, min: cy, max: end, tone: 'accent' })
    const claim = p[`parent${w}_ss_claim_age`] ?? Math.min(Math.max(p[`parent${w}_retirement_age`], 62), 70)
    out.push({ id: `ss${w}`, lane: 'people', ref: { kind: 'ss', who: w }, year: yearAtAge(p, w, claim), label: `${nm(p, w)}: Social Security`, sub: `age ${claim}`, draggable: true,
      min: Math.max(cy, yearAtAge(p, w, 62)), max: yearAtAge(p, w, 70) })
    out.push({ id: `end${w}`, lane: 'people', ref: { kind: 'end', who: w }, year: yearAtAge(p, w, p[`parent${w}_death_age`]), label: `${nm(p, w)}: plan to ${p[`parent${w}_death_age`]}`, draggable: true,
      min: yearAtAge(p, w, Math.max(60, p[`parent${w}_age`] + 1)), max: yearAtAge(p, w, 115), tone: 'muted' })
    const phases: any[] = p[`parent${w}_career_phases`] || []
    if (phases.length) {
      phases.forEach((ph, i) => {
        if (i === 0) return
        const y = yearAtAge(p, w, ph.start_age)
        if (y <= cy) return
        out.push({ id: `phase${w}${i}`, lane: 'people', ref: { kind: 'phase', who: w, idx: i }, year: y, label: `${nm(p, w)}: ${ph.label || 'new phase'}`, sub: `$${Math.round(ph.base_salary / 1000)}k`, draggable: true, min: cy + 1, max: ry })
      })
    } else {
      (p[`parent${w}_job_changes`] || []).forEach((j: any, i: number) => {
        out.push({ id: `job${w}${i}`, lane: 'people', ref: { kind: 'job', who: w, idx: i }, year: j.Year, label: `${nm(p, w)}: new job`, sub: `$${Math.round(j['New Income'] / 1000)}k`, draggable: true, min: cy, max: ry })
      })
    }
  }
  ;(p.state_timeline || []).forEach((e: any, i: number) => {
    if (i === 0) return
    out.push({ id: `move${i}`, lane: 'where', ref: { kind: 'move', idx: i }, year: e.year, label: `Move to ${e.state}`, sub: e.spending_strategy, draggable: true, min: cy + 1, max: end })
  })
  ;(p.houses || []).forEach((h: any, i: number) => {
    if (h.purchase_year > cy) out.push({ id: `buy${i}`, lane: 'home', ref: { kind: 'house_buy', idx: i }, year: h.purchase_year, label: `Buy ${h.name}`, sub: `$${Math.round((h.purchase_price || h.current_value) / 1000)}k`, draggable: true, min: cy + 1, max: end })
    ;(h.timeline || []).forEach((e: any, k: number) => {
      if (k === 0 || e.year <= cy) return
      const what = e.status === 'Sold' ? 'Sell' : e.status === 'Own_Rent' ? 'Rent out' : 'Move into'
      out.push({ id: `hev${i}_${k}`, lane: 'home', ref: { kind: 'house_event', idx: i, e: k }, year: e.year, label: `${what} ${h.name}`, draggable: true, min: Math.max(cy + 1, h.purchase_year + 1), max: end })
    })
  })
  ;(p.children_list || []).forEach((c: any, i: number) => {
    const born = c.birth_year >= cy
    out.push({ id: `kid${i}`, lane: 'kids', ref: { kind: 'child', idx: i }, year: born ? c.birth_year : cy, end: c.birth_year + 21,
      label: born ? `${c.name} born` : `${c.name} (${cy - c.birth_year})`, sub: `college ${c.birth_year + 18}–${c.birth_year + 21}`, draggable: born, min: cy, max: end })
  })
  ;(p.major_purchases || []).forEach((m: any, i: number) => {
    out.push({ id: `pur${i}`, lane: 'money', ref: { kind: 'purchase', idx: i }, year: m.year, label: m.name, sub: `$${Math.round(m.amount / 1000)}k`, draggable: true, min: cy, max: end })
  })
  ;(p.recurring_expenses || []).forEach((r: any, i: number) => {
    if (r.frequency_years <= 1 && r.amount < 5000) return   // small yearly items stay on the Spending page
    out.push({ id: `rec${i}`, lane: 'money', ref: { kind: 'recurring', idx: i }, year: Math.max(r.start_year, cy), end: r.end_year ?? undefined, label: r.name,
      sub: `$${Math.round(r.amount / 1000)}k every ${r.frequency_years} yr`, draggable: true, min: cy, max: end })
  })
  ;(p.windfalls || []).forEach((w: any, i: number) => {
    out.push({ id: `wf${i}`, lane: 'money', ref: { kind: 'windfall', idx: i }, year: w.year, label: w.name, sub: `+$${Math.round(w.amount / 1000)}k`, draggable: true, min: cy, max: end, tone: 'good' })
  })
  ;(p.pensions || []).forEach((x: any, i: number) => {
    const w = whoKey(x.person)
    out.push({ id: `pen${i}`, lane: 'money', ref: { kind: 'pension', idx: i }, year: Math.max(cy, yearAtAge(p, w, x.start_age)), label: x.name, sub: `$${Math.round(x.monthly).toLocaleString()}/mo`, draggable: true, min: cy, max: end, tone: 'good' })
  })
  const evs: any[] = proj?.events || []
  ;(p.debts || []).forEach((x: any, i: number) => {
    const paid = evs.find(e => e.type === 'debt_paid' && e.label.startsWith(x.name))
    out.push({ id: `debt${i}`, lane: 'money', ref: { kind: 'debt', idx: i }, year: Math.max(cy, x.start_year), end: paid?.year, label: x.name,
      sub: paid ? `paid off ${paid.year}` : `$${Math.round(x.balance / 1000)}k`, draggable: x.start_year > cy, min: cy, max: end, tone: 'bad' })
  })
  ;(p.goals || []).forEach((g: any, i: number) => {
    if (g.type === 'emergency_fund') return
    const ev = (proj?.goals || []).find((x: any) => x.id === g.id)
    out.push({ id: `goal${i}`, lane: 'goals', ref: { kind: 'goal', idx: i }, year: g.type === 'college' ? (ev?.year ?? g.year) : g.year, label: g.name,
      sub: ev ? ({ on_track: 'on track', at_risk: 'at risk', off_track: 'off track' } as any)[ev.status] : '', draggable: g.type !== 'college', min: cy, max: end,
      tone: ev ? ({ on_track: 'good', at_risk: 'warn', off_track: 'bad' } as any)[ev.status] : 'accent' })
  })
  return out
}

/** Move an item to a new year (drag). */
export function setYear(d: any, ref: Ref, y: number) {
  const w = ref.who as 'X' | 'Y'
  switch (ref.kind) {
    case 'retire': d[`parent${w}_retirement_age`] = ageAt(d, w, y); break
    case 'ss': d[`parent${w}_ss_claim_age`] = Math.min(70, Math.max(62, ageAt(d, w, y))); break
    case 'end': d[`parent${w}_death_age`] = ageAt(d, w, y); break
    case 'job': d[`parent${w}_job_changes`][ref.idx!].Year = y; d[`parent${w}_job_changes`].sort((a: any, b: any) => a.Year - b.Year); break
    case 'phase': {
      const ps = d[`parent${w}_career_phases`]; const a = ageAt(d, w, y)
      const prev = ps[ref.idx! - 1]; const ph = ps[ref.idx!]
      const lo = prev.start_age + 1, hi = ph.end_age - 1
      const na = Math.min(Math.max(a, lo), hi)
      ph.start_age = na; prev.end_age = na
      break
    }
    case 'move': d.state_timeline[ref.idx!].year = y; d.state_timeline.sort((a: any, b: any) => a.year - b.year); break
    case 'house_buy': {
      const h = d.houses[ref.idx!]; const dy = y - h.purchase_year
      h.purchase_year = y
      // keep the home's own timeline in step
      for (const e of h.timeline || []) e.year += dy
      break
    }
    case 'house_event': d.houses[ref.idx!].timeline[ref.e!].year = y; d.houses[ref.idx!].timeline.sort((a: any, b: any) => a.year - b.year); break
    case 'child': d.children_list[ref.idx!].birth_year = y; break
    case 'purchase': d.major_purchases[ref.idx!].year = y; break
    case 'recurring': {
      const r = d.recurring_expenses[ref.idx!]; const dy = y - r.start_year
      r.start_year = y; if (r.end_year != null) r.end_year += dy
      break
    }
    case 'windfall': d.windfalls[ref.idx!].year = y; break
    case 'pension': { const x = d.pensions[ref.idx!]; x.start_age = ageAt(d, whoKey(x.person), y); break }
    case 'debt': d.debts[ref.idx!].start_year = y; break
    case 'goal': d.goals[ref.idx!].year = y; break
  }
}

export function remove(d: any, ref: Ref) {
  switch (ref.kind) {
    case 'job': d[`parent${ref.who}_job_changes`].splice(ref.idx!, 1); break
    case 'phase': {
      const ps = d[`parent${ref.who}_career_phases`]; const ph = ps[ref.idx!]
      ps[ref.idx! - 1].end_age = ph.end_age; ps.splice(ref.idx!, 1); break
    }
    case 'move': d.state_timeline.splice(ref.idx!, 1); break
    case 'house_buy': d.houses.splice(ref.idx!, 1); break
    case 'house_event': d.houses[ref.idx!].timeline.splice(ref.e!, 1); break
    case 'child': {
      const c = d.children_list[ref.idx!]
      d.children_list.splice(ref.idx!, 1)
      d.college_529 = (d.college_529 || []).filter((x: any) => x.child !== c.name)
      break
    }
    case 'purchase': d.major_purchases.splice(ref.idx!, 1); break
    case 'recurring': d.recurring_expenses.splice(ref.idx!, 1); break
    case 'windfall': d.windfalls.splice(ref.idx!, 1); break
    case 'pension': d.pensions.splice(ref.idx!, 1); break
    case 'debt': d.debts.splice(ref.idx!, 1); break
    case 'goal': d.goals.splice(ref.idx!, 1); break
  }
}

export const removable = (k: Kind) => !['retire', 'ss', 'end'].includes(k)

/* ── editor forms ──────────────────────────────────────────────────────── */
export type FieldT = 'text' | 'money' | 'number' | 'year' | 'percent' | 'select' | 'location' | 'toggle'
export interface FieldSpec { key: string; label: string; type: FieldT; options?: (string | { value: string; label: string })[]; hint?: string; show?: (x: any) => boolean }

const LIFESTYLES = ['Conservative', 'Average', 'High-end']
const personOpts = (p: any) => [{ value: 'Parent 1', label: nm(p, 'X') }, ...(single(p) ? [] : [{ value: 'Parent 2', label: nm(p, 'Y') }])]

export function fields(p: any, kind: Kind, isNew: boolean): FieldSpec[] {
  switch (kind) {
    case 'retire': return [{ key: 'age', label: 'Retirement age', type: 'number' }]
    case 'ss': return [{ key: 'age', label: 'Claim Social Security at age (62–70)', type: 'number' }]
    case 'end': return [{ key: 'age', label: 'Plan until age', type: 'number' }]
    case 'job': return [...(isNew ? [{ key: 'person', label: 'Who', type: 'select' as FieldT, options: personOpts(p) }] : []), { key: 'year', label: 'From year', type: 'year' },
      { key: 'income', label: 'New salary (per year)', type: 'money' }, { key: 'raise', label: 'Yearly raise', type: 'percent', hint: 'Leave empty to keep the current raise' },
      ...(isNew ? [{ key: 'label', label: 'Job name', type: 'text' as FieldT }] : [])]
    case 'phase': return [{ key: 'year', label: 'Starts in year', type: 'year' }, { key: 'label', label: 'Phase name', type: 'text' },
      { key: 'income', label: 'Base salary', type: 'money' }, { key: 'raise', label: 'Yearly raise', type: 'percent' }, { key: 'bonus', label: 'Bonus', type: 'percent' }]
    case 'move': return [{ key: 'location', label: 'Move to', type: 'location' }, { key: 'year', label: 'Year', type: 'year' },
      { key: 'lifestyle', label: 'Lifestyle there', type: 'select', options: LIFESTYLES }]
    case 'house_buy': return [{ key: 'name', label: 'Name', type: 'text' }, { key: 'year', label: 'Buy in year', type: 'year' },
      { key: 'price', label: 'Price (in the year you buy)', type: 'money' }, { key: 'down', label: 'Down payment', type: 'percent' },
      { key: 'rate', label: 'Mortgage rate', type: 'percent' }, { key: 'term', label: 'Loan term (years)', type: 'number' },
      { key: 'location', label: 'Where', type: 'location' }, { key: 'appreciation', label: 'Appreciation per year', type: 'percent' }]
    case 'house_event': return [{ key: 'house', label: 'Home', type: 'select', options: (p.houses || []).map((h: any, i: number) => ({ value: String(i), label: h.name })) },
      { key: 'status', label: 'What happens', type: 'select', options: [{ value: 'Sold', label: 'Sell it' }, { value: 'Own_Rent', label: 'Rent it out' }, { value: 'Own_Live', label: 'Live in it' }] },
      { key: 'year', label: 'Year', type: 'year' }, { key: 'rent', label: 'Rent per month', type: 'money', show: x => x.status === 'Own_Rent' }]
    case 'child': return [{ key: 'name', label: 'Name', type: 'text' }, { key: 'year', label: 'Birth year', type: 'year' },
      { key: 'school', label: 'K-12 school', type: 'select', options: ['Public', 'Private'] }, { key: 'college', label: 'College', type: 'select', options: ['Public', 'Private'] },
      { key: 'lifestyle', label: 'Cost level', type: 'select', options: LIFESTYLES }]
    case 'purchase': return [{ key: 'name', label: 'What', type: 'text' }, { key: 'year', label: 'Year', type: 'year' }, { key: 'amount', label: "Cost (today's $)", type: 'money' },
      { key: 'financing', label: 'Financed over (years, 0 = cash)', type: 'number' }, { key: 'rate', label: 'Loan rate', type: 'percent', show: x => x.financing > 0 }]
    case 'recurring': return [{ key: 'name', label: 'What', type: 'text' }, { key: 'amount', label: "Cost each time (today's $)", type: 'money' },
      { key: 'every', label: 'Every N years', type: 'number' }, { key: 'year', label: 'First year', type: 'year' }, { key: 'until', label: 'Last year (empty = forever)', type: 'year' }]
    case 'windfall': return [{ key: 'name', label: 'What', type: 'text' }, { key: 'year', label: 'Year', type: 'year' }, { key: 'amount', label: "Amount (today's $)", type: 'money' },
      { key: 'recipient', label: 'Received by', type: 'select', options: [...personOpts(p), ...(single(p) ? [] : [{ value: 'Both', label: 'Both' }])] },
      { key: 'separate', label: 'Separate property (a gift or inheritance to one person)', type: 'toggle' }]
    case 'pension': return [{ key: 'name', label: 'Name', type: 'text' }, { key: 'person', label: 'Paid to', type: 'select', options: personOpts(p) },
      { key: 'year', label: 'Starts in year', type: 'year' }, { key: 'monthly', label: "Per month (today's $)", type: 'money' }, { key: 'cola', label: 'Yearly increase', type: 'percent' },
      ...(single(p) ? [] : [{ key: 'survivor', label: 'Survivor keeps', type: 'percent' as FieldT }])]
    case 'debt': return [{ key: 'name', label: 'Loan', type: 'text' }, { key: 'kind', label: 'Kind', type: 'select', options: [{ value: 'student', label: 'Student loan' }, { value: 'auto', label: 'Car loan' }, { value: 'credit_card', label: 'Credit card' }, { value: 'personal', label: 'Personal loan' }, { value: 'other', label: 'Other' }] },
      { key: 'year', label: 'Starts (this year = existing loan)', type: 'year' }, { key: 'balance', label: 'Balance', type: 'money' }, { key: 'rate', label: 'Interest rate', type: 'percent' },
      { key: 'monthly', label: 'Payment per month', type: 'money' }]
    case 'goal': return [{ key: 'type', label: 'Kind', type: 'select', options: [{ value: 'fi', label: 'Work optional' }, { value: 'net_worth', label: 'Net worth target' },
      { value: 'savings', label: 'Savings target' }, { value: 'house_paid_off', label: 'House paid off' }, { value: 'debt_free', label: 'Debt free' }] },
      { key: 'name', label: 'Name', type: 'text' }, { key: 'year', label: 'By year', type: 'year' },
      { key: 'amount', label: "Amount (today's $)", type: 'money', show: x => ['net_worth', 'savings'].includes(x.type) },
      { key: 'house', label: 'Home', type: 'select', options: (p.houses || []).map((h: any) => h.name), show: x => x.type === 'house_paid_off' }]
  }
}

/** Current values for the editor (existing item) or defaults (new item dropped at `year`). */
export function draftFor(p: any, ref: Ref, year: number): any {
  const cy = p.current_year
  const w = (ref.who || 'X') as 'X' | 'Y'
  const loc = (p.state_timeline || []).filter((e: any) => e.year <= year).slice(-1)[0]?.state || p.state_timeline?.[0]?.state || 'Seattle'
  switch (ref.kind) {
    case 'retire': return { age: p[`parent${w}_retirement_age`] }
    case 'ss': return { age: p[`parent${w}_ss_claim_age`] ?? Math.min(Math.max(p[`parent${w}_retirement_age`], 62), 70) }
    case 'end': return { age: p[`parent${w}_death_age`] }
    case 'job': {
      if (ref.idx == null) return { person: 'Parent 1', year, income: Math.round((p.parentX_income || 80000) * 1.15), raise: null, label: 'New job' }
      const j = p[`parent${w}_job_changes`][ref.idx]; return { year: j.Year, income: j['New Income'], raise: j['New Raise %'] ?? null }
    }
    case 'phase': { const ph = p[`parent${w}_career_phases`][ref.idx!]; return { year: yearAtAge(p, w, ph.start_age), label: ph.label, income: ph.base_salary, raise: ph.annual_raise_pct, bonus: ph.annual_bonus_pct } }
    case 'move': {
      if (ref.idx == null) return { location: loc, year, lifestyle: 'Average' }
      const e = p.state_timeline[ref.idx]; return { location: e.state, year: e.year, lifestyle: String(e.spending_strategy || 'Average').replace(' (statistical)', '') }
    }
    case 'house_buy': {
      if (ref.idx == null) return { name: `Home ${(p.houses || []).length + 1}`, year, price: 750000, down: 20, rate: 6.5, term: 30, location: loc, appreciation: 3 }
      const h = p.houses[ref.idx]; return { name: h.name, year: h.purchase_year, price: h.purchase_price, down: h.down_payment_pct ?? 20, rate: (h.mortgage_rate || 0) * 100,
        term: h.loan_term_years || 30, location: h.location || loc, appreciation: h.appreciation_rate }
    }
    case 'house_event': {
      if (ref.idx == null || ref.e == null) return { house: String(Math.max(0, (p.houses || []).findIndex((h: any) => h.purchase_year < year))), status: 'Sold', year, rent: 2500 }
      const e = p.houses[ref.idx].timeline[ref.e]; return { house: String(ref.idx), status: e.status, year: e.year, rent: e.rental_income || 0 }
    }
    case 'child': {
      if (ref.idx == null) { let n = (p.children_list || []).length + 1; const names = new Set((p.children_list || []).map((c: any) => c.name.toLowerCase())); while (names.has(`child ${n}`)) n++
        return { name: `Child ${n}`, year, school: 'Public', college: 'Public', lifestyle: 'Average' } }
      const c = p.children_list[ref.idx]; return { name: c.name, year: c.birth_year, school: c.school_type, college: c.college_type, lifestyle: String(c.template_strategy || 'Average').replace(' (statistical)', '') }
    }
    case 'purchase': {
      if (ref.idx == null) return { name: 'Big purchase', year, amount: 30000, financing: 0, rate: 7 }
      const m = p.major_purchases[ref.idx]; return { name: m.name, year: m.year, amount: m.amount, financing: m.financing_years, rate: (m.interest_rate || 0) * 100 }
    }
    case 'recurring': {
      if (ref.idx == null) return { name: 'New car', amount: 40000, every: 8, year, until: null }
      const r = p.recurring_expenses[ref.idx]; return { name: r.name, amount: r.amount, every: r.frequency_years, year: r.start_year, until: r.end_year }
    }
    case 'windfall': {
      if (ref.idx == null) return { name: 'Inheritance', year, amount: 100000, recipient: 'Parent 1', separate: true }
      const x = p.windfalls[ref.idx]; return { name: x.name, year: x.year, amount: x.amount, recipient: x.recipient, separate: x.separate }
    }
    case 'pension': {
      if (ref.idx == null) return { name: 'Pension', person: 'Parent 1', year, monthly: 2000, cola: 2, survivor: 50 }
      const x = p.pensions[ref.idx]; return { name: x.name, person: x.person, year: yearAtAge(p, whoKey(x.person), x.start_age), monthly: x.monthly, cola: x.cola_pct, survivor: x.survivor_pct }
    }
    case 'debt': {
      if (ref.idx == null) return { name: 'Car loan', kind: 'auto', year: Math.max(cy, year), balance: 30000, rate: 7, monthly: 600 }
      const x = p.debts[ref.idx]; return { name: x.name, kind: x.kind, year: x.start_year, balance: x.balance, rate: x.rate, monthly: x.monthly_payment }
    }
    case 'goal': {
      if (ref.idx == null) return { type: 'net_worth', name: 'Net worth target', year, amount: 1000000, house: p.houses?.[0]?.name || '' }
      const g = p.goals[ref.idx]; return { type: g.type, name: g.name, year: g.year, amount: g.amount, house: g.house }
    }
  }
}

const uid = (s: string) => `${s}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`

/** Write an editor draft into the plan (creates the item when ref.idx is undefined). */
export function applyDraft(d: any, ref: Ref, x: any) {
  const w = (ref.who || 'X') as 'X' | 'Y'
  const cy = d.current_year
  const num = (v: any, def = 0) => (v === null || v === undefined || v === '' || isNaN(+v) ? def : +v)
  switch (ref.kind) {
    case 'retire': d[`parent${w}_retirement_age`] = Math.round(num(x.age, 65)); break
    case 'ss': d[`parent${w}_ss_claim_age`] = Math.min(70, Math.max(62, Math.round(num(x.age, 67)))); break
    case 'end': d[`parent${w}_death_age`] = Math.round(num(x.age, 95)); break
    case 'job': {
      const who = ref.idx == null ? whoKey(x.person) : w
      const phases: any[] = d[`parent${who}_career_phases`] || []
      if (ref.idx == null && phases.length) {
        // career phases: split the phase running at that age
        const a = ageAt(d, who, num(x.year, cy))
        const k = phases.findIndex(ph => ph.start_age <= a && a < ph.end_age)
        const base = k >= 0 ? phases[k] : phases[phases.length - 1]
        const np = { ...base, start_age: a, end_age: k >= 0 ? base.end_age : Math.max(a + 1, d[`parent${who}_retirement_age`]), base_salary: num(x.income),
          annual_raise_pct: x.raise == null || x.raise === '' ? base.annual_raise_pct : num(x.raise), label: x.label || 'New job' }
        if (k >= 0) base.end_age = a
        phases.splice(k >= 0 ? k + 1 : phases.length, 0, np)
        phases.sort((a1: any, b1: any) => a1.start_age - b1.start_age)
        break
      }
      const row: any = { Year: Math.round(num(x.year, cy)), 'New Income': num(x.income) }
      if (x.raise !== null && x.raise !== undefined && x.raise !== '') row['New Raise %'] = num(x.raise)
      const list = (d[`parent${who}_job_changes`] ||= [])
      if (ref.idx == null) list.push(row); else list[ref.idx] = row
      list.sort((a1: any, b1: any) => a1.Year - b1.Year)
      break
    }
    case 'phase': {
      const ph = d[`parent${w}_career_phases`][ref.idx!]
      ph.label = x.label; ph.base_salary = num(x.income); ph.annual_raise_pct = num(x.raise); ph.annual_bonus_pct = num(x.bonus)
      setYear(d, ref, Math.round(num(x.year)))
      break
    }
    case 'move': {
      const e = { year: Math.round(num(x.year, cy + 1)), state: x.location, spending_strategy: x.lifestyle || 'Average' }
      if (ref.idx == null) d.state_timeline.push(e); else d.state_timeline[ref.idx] = e
      d.state_timeline.sort((a: any, b: any) => a.year - b.year)
      break
    }
    case 'house_buy': {
      const price = num(x.price), down = num(x.down, 20)
      if (ref.idx == null) {
        const y = Math.round(num(x.year, cy + 1))
        ;(d.houses ||= []).push({ name: x.name || 'Home', purchase_year: y, purchase_price: price, current_value: price, mortgage_balance: price * (1 - down / 100),
          mortgage_rate: num(x.rate, 6.5) / 100, mortgage_years_left: num(x.term, 30), loan_term_years: num(x.term, 30), mortgage_mode: 'estimate', down_payment_pct: down,
          property_tax_rate: 0.01, home_insurance: 1500, maintenance_rate: 0.01, upkeep_costs: 0, owner: 'Shared', location: x.location || '', appreciation_rate: num(x.appreciation, 3),
          timeline: [{ year: y, status: 'Own_Live', rental_income: 0 }], pmi_rate: 0.5, pmi_monthly: 0, hoa_monthly: 0, closing_cost_pct: 2 })
      } else {
        const h = d.houses[ref.idx]
        h.name = x.name; h.purchase_price = price; h.current_value = price; h.down_payment_pct = down; h.mortgage_rate = num(x.rate) / 100
        h.loan_term_years = num(x.term, 30); h.location = x.location; h.appreciation_rate = num(x.appreciation, 3)
        if (h.mortgage_mode === 'estimate') { h.mortgage_balance = price * (1 - down / 100); h.mortgage_years_left = h.loan_term_years }
        setYear(d, ref, Math.round(num(x.year)))
      }
      break
    }
    case 'house_event': {
      const hi = Math.round(num(x.house, 0))
      const h = d.houses[hi]
      if (!h) break
      const e = { year: Math.round(num(x.year, cy + 1)), status: x.status, rental_income: x.status === 'Own_Rent' ? num(x.rent) : 0 }
      if (ref.idx == null || ref.e == null || ref.idx !== hi) {
        if (ref.idx != null && ref.e != null) d.houses[ref.idx].timeline.splice(ref.e, 1)
        h.timeline.push(e)
      } else h.timeline[ref.e] = e
      h.timeline.sort((a: any, b: any) => a.year - b.year)
      break
    }
    case 'child': {
      const loc = d.state_timeline?.[0]?.state || 'Seattle'
      if (ref.idx == null) {
        ;(d.children_list ||= []).push({ name: x.name, birth_year: Math.round(num(x.year, cy + 1)), use_template: true, template_state: loc, template_strategy: x.lifestyle || 'Average',
          school_type: x.school || 'Public', college_type: x.college || 'Public', college_location: loc })
      } else {
        const c = d.children_list[ref.idx]; const old = c.name
        Object.assign(c, { name: x.name, birth_year: Math.round(num(x.year)), school_type: x.school, college_type: x.college, template_strategy: x.lifestyle })
        for (const e of d.college_529 || []) if (e.child === old) e.child = x.name
        for (const g of d.goals || []) if (g.child === old) g.child = x.name
      }
      break
    }
    case 'purchase': {
      const m = { name: x.name, year: Math.round(num(x.year, cy)), amount: num(x.amount), financing_years: Math.round(num(x.financing)), interest_rate: num(x.rate) / 100,
        asset_type: 'Expense', appreciation_rate: 0 }
      if (ref.idx == null) (d.major_purchases ||= []).push(m); else d.major_purchases[ref.idx] = { ...d.major_purchases[ref.idx], ...m }
      break
    }
    case 'recurring': {
      const r = { name: x.name, category: 'Other', amount: num(x.amount), frequency_years: Math.max(1, Math.round(num(x.every, 1))), start_year: Math.round(num(x.year, cy)),
        end_year: x.until ? Math.round(num(x.until)) : null, inflation_adjust: true, parent: 'Both', financing_years: 0, interest_rate: 0 }
      if (ref.idx == null) (d.recurring_expenses ||= []).push(r); else d.recurring_expenses[ref.idx] = { ...d.recurring_expenses[ref.idx], ...r }
      break
    }
    case 'windfall': {
      const wf = { name: x.name, year: Math.round(num(x.year, cy)), amount: num(x.amount), recipient: x.recipient || 'Parent 1', kind: 'inheritance', separate: !!x.separate, inflation_adjust: true }
      if (ref.idx == null) (d.windfalls ||= []).push(wf); else d.windfalls[ref.idx] = { ...d.windfalls[ref.idx], ...wf }
      break
    }
    case 'pension': {
      const who = whoKey(x.person)
      const pen = { name: x.name, person: x.person, start_age: ageAt(d, who, Math.round(num(x.year, cy))), monthly: num(x.monthly), cola_pct: num(x.cola), survivor_pct: num(x.survivor, 50) }
      if (ref.idx == null) (d.pensions ||= []).push({ id: uid('pen'), kind: 'pension', taxable_pct: 100, todays_dollars: true, ...pen })
      else d.pensions[ref.idx] = { ...d.pensions[ref.idx], ...pen }
      break
    }
    case 'debt': {
      const db = { name: x.name, kind: x.kind, start_year: Math.round(num(x.year, cy)), balance: num(x.balance), rate: num(x.rate), monthly_payment: num(x.monthly) }
      if (ref.idx == null) (d.debts ||= []).push({ id: uid('debt'), extra_monthly: 0, ...db }); else d.debts[ref.idx] = { ...d.debts[ref.idx], ...db }
      break
    }
    case 'goal': {
      const g = { type: x.type, name: x.name, year: Math.round(num(x.year, cy + 10)), amount: num(x.amount), house: x.house || '', months: 6, child: '' }
      if (ref.idx == null) (d.goals ||= []).push({ id: uid('goal'), ...g }); else d.goals[ref.idx] = { ...d.goals[ref.idx], ...g }
      break
    }
  }
}

export const KIND_LABEL: Record<Kind, string> = {
  retire: 'Retirement', ss: 'Social Security', end: 'Plan end', job: 'Job change', phase: 'Career phase', move: 'Move', house_buy: 'Buy a home',
  house_event: 'Home change', child: 'Child', purchase: 'Big purchase', recurring: 'Recurring cost', windfall: 'Gift / inheritance', pension: 'Pension',
  debt: 'Loan', goal: 'Goal',
}
