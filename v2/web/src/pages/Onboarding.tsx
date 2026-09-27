import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Users, Home, Key, Building2, Baby, CalendarCheck, Sparkles, Briefcase, Coffee, Armchair, Plus, Trash2, HeartPulse } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { SpendingSlider, useCurve, curveSources } from '../components/SpendingSlider'
import { useCites } from '../components/Cite'
import { Curve, rescale, strategyFor, describe } from '../lib/spending'
import { money, pct } from '../lib/format'
import { FlowShell, Question, ChoiceCards, Chips, BigField, Slider } from '../components/flow'
import { LocationPicker } from './Locations'
import { Money, NumberInput, Percent, TextInput, Select, Button, Card, Note } from '../components/ui'
import { Sparkline } from '../components/charts'
import { monthlyPayment } from '../lib/mortgage'

// ── answers model ────────────────────────────────────────────────────────
type Work = 'working' | 'home' | 'retired'
interface Kid { name: string; birth_year: number; school: string; college: string }
interface Phase { label: string; from: number; to: number; salary: number; raise: number }
interface Answers {
  household: 'single' | 'couple'
  p1: { name: string; age: number; emoji: string; work: Work; income: number; raise: number; retire: number; savings: number; retirement: number; ss: number }
  p2: { name: string; age: number; emoji: string; work: Work; income: number; raise: number; retire: number; savings: number; retirement: number; ss: number }
  location: string
  contrib: number
  ss_mode: 'estimate' | 'known'
  housing: 'rent' | 'own' | 'family'
  rent: number
  home: { value: number; balance: number; rate: number; years: number; tax?: number }
  buy: 'no' | 'yes'
  buyPlan: { year: number; price: number; down: number; rate: number; term: number; sellCurrent: boolean }
  kids: 'none' | 'yes'
  children: Kid[]
  style: 'Conservative' | 'Average' | 'High-end'
  level?: number
  health: 'employer' | 'marketplace' | 'medicare'
  bridge: number
  plans: string[]
  planAmounts: Record<string, number>
  lifeExp: number
  life2?: number
  marriage?: number
  moves?: { year: number; location: string }[]
  jobs?: { p1: { year: number; income: number }[]; p2: { year: number; income: number }[] }
  monthly?: { utilities: number; water: number; internet: number; subs: number; pets: number; other: number }
  custom?: { name: string; amount: number; kind: 'once' | 'recurring'; year: number; every: number }[]
  hsa?: { balance: number; contrib: number }
  oop?: number
  phases?: { p1: Phase[]; p2: Phase[] }
  sep?: { on: boolean; prenup: boolean; earningsSeparate: boolean; p1: { liquid: number; pretax: number }; p2: { liquid: number; pretax: number } }
  gifts?: { name: string; year: number; amount: number; who: 'Parent 1' | 'Parent 2' | 'Both' }[]
  filing?: 'married' | 'single'
  empPremium?: number
  ssCut: boolean
  cadence: 'quarterly' | 'semiannual' | 'annual' | 'off'
}

const CY = new Date().getFullYear()
const DEFAULT: Answers = {
  household: 'couple',
  p1: { name: '', age: 35, emoji: '👨', work: 'working', income: 100000, raise: 3, retire: 65, savings: 50000, retirement: 50000, ss: 0 },
  p2: { name: '', age: 35, emoji: '👩', work: 'working', income: 90000, raise: 3, retire: 65, savings: 30000, retirement: 40000, ss: 0 },
  location: 'Seattle', contrib: 15000, ss_mode: 'estimate',
  housing: 'rent', rent: 2500, home: { value: 700000, balance: 450000, rate: 0.065, years: 27 },
  buy: 'no', buyPlan: { year: CY + 3, price: 800000, down: 20, rate: 0.065, term: 30, sellCurrent: true },
  kids: 'none', children: [], style: 'Average', health: 'employer', bridge: 1400, plans: ['vacation'],
  planAmounts: { car: 35000, vacation: 6000, wedding: 30000, renovation: 50000, boat: 40000, college_help: 0 },
  lifeExp: 95, ssCut: true, cadence: 'quarterly',
  moves: [], jobs: { p1: [], p2: [] }, custom: [],
  monthly: { utilities: 180, water: 60, internet: 120, subs: 40, pets: 0, other: 50 }, hsa: { balance: 0, contrib: 0 }, oop: 1500,
  phases: { p1: [], p2: [] }, empPremium: 250,
}
const EMOJIS = ['👨', '👩', '🧑', '👱', '👴', '👵', '🧔', '👩‍🦰', '👨‍🦱', '🧕', '🙂']

const BIG_PLANS: { value: string; label: string; kind: 'recurring' | 'once'; every?: number; desc: string }[] = [
  { value: 'car', label: 'New car every 8 years', kind: 'recurring', every: 8, desc: 'Replacement vehicle' },
  { value: 'vacation', label: 'Yearly family vacation', kind: 'recurring', every: 1, desc: 'Added to household spending as Family Vacations' },
  { value: 'renovation', label: 'Home renovation', kind: 'once', desc: 'In about 5 years' },
  { value: 'wedding', label: 'Help with a wedding', kind: 'once', desc: 'In about 20 years' },
  { value: 'boat', label: 'Boat / RV', kind: 'once', desc: 'In about 10 years' },
]

/** Rough Social Security estimate (2026 bend points and wage cap, 35 years at today's income; SSA). */
export function estimateSS(income: number) {
  const aime = Math.min(income, 184500) / 12
  const pia = 0.9 * Math.min(aime, 1286) + 0.32 * Math.max(0, Math.min(aime, 7749) - 1286) + 0.15 * Math.max(0, aime - 7749)
  return Math.round(pia / 10) * 10
}

function buildPlan(A: Answers, base: any, curve: Curve) {
  const p: any = structuredClone(base)
  const single = A.household === 'single'
  const level = A.level ?? 50
  const strat = strategyFor(level)
  p.current_year = CY
  const person = (who: 'X' | 'Y', a: Answers['p1'], n: string, idx: number) => {
    p[`parent${idx}_name`] = a.name || (idx === 1 ? 'Me' : 'Partner')
    p[`parent${idx}_emoji`] = a.emoji
    p[`parent${who}_age`] = a.age
    p[`parent${who}_death_age`] = who === 'Y' && A.life2 ? A.life2 : A.lifeExp
    p[`parent${who}_income`] = a.work === 'working' ? a.income : 0
    p[`parent${who}_raise`] = a.raise
    p[`parent${who}_retirement_age`] = a.work === 'retired' ? a.age : a.retire
    p[`parent${who}_net_worth`] = a.savings + a.retirement
    p[`parent${who}_pretax_balance`] = a.retirement
    p[`parent${who}_ss_benefit`] = A.ss_mode === 'known' ? a.ss : estimateSS(a.work === 'home' ? 0 : a.income)
    const ph = a.work === 'working' ? (A.phases?.[idx === 1 ? 'p1' : 'p2'] || []) : []
    // career stages (v0.8 wizard) replace the simple income + job changes when given
    p[`parent${who}_career_phases`] = ph.map(x => ({ label: x.label, start_age: x.from, end_age: x.to, base_salary: x.salary, annual_raise_pct: x.raise,
      philosophy: 'Stable', annual_bonus_pct: 0, rsu_annual_grant: 0, rsu_vesting_years: 4, stock_options_grant: 0, stock_options_growth_pct: 0, stock_options_liquidity_year: 0 }))
    p[`parent${who}_job_changes`] = ph.length ? [] : ((A.jobs?.[idx === 1 ? 'p1' : 'p2']) || []).filter(j => j.year > CY).map(j => ({ Year: j.year, 'New Income': j.income }))
    p[`parent${who}_expense_location`] = A.location
    p[`parent${who}_expense_strategy`] = strat
    p[`parent${who}_expenses`] = rescale({}, curve, null, level)
    p[`parent${who}_spending_level`] = level
  }
  person('X', A.p1, A.p1.name, 1)
  if (single) {
    p.parent2_name = 'N/A'; p.parent2_emoji = '👤'
    Object.assign(p, { parentY_age: A.p1.age, parentY_income: 0, parentY_net_worth: 0, parentY_ss_benefit: 0, parentY_pretax_balance: 0,
      parentY_career_phases: [], parentY_job_changes: [] })
    p.parentY_expenses = Object.fromEntries(Object.keys(p.parentX_expenses).map(k => [k, 0]))
    p.marriage_year = 'N/A'
    p.tax_filing_status = 'single'
  } else {
    person('Y', A.p2, A.p2.name, 2)
    p.tax_filing_status = A.filing || 'married'
  }
  p.pretax_401k = A.contrib
  p.state_timeline = [{ year: CY, state: A.location, spending_strategy: strat.replace(' (statistical)', '') },
    ...(A.moves || []).filter(m => m.year > CY && m.location).sort((a, b) => a.year - b.year)
      .map(m => ({ year: m.year, state: m.location, spending_strategy: strat.replace(' (statistical)', '') }))]
  if (!single && A.marriage) p.marriage_year = A.marriage
  // housing
  const fam = { ...p.family_shared_expenses }
  fam['Mortgage/Rent'] = A.housing === 'rent' ? A.rent * 12 : 0
  const mo = A.monthly
  if (mo) {
    fam['Gas & Electric'] = mo.utilities * 12; fam['Water'] = mo.water * 12; fam['Internet & Cable'] = mo.internet * 12
    fam['Shared Subscriptions'] = mo.subs * 12; fam['Pet Care'] = mo.pets * 12; fam['Other Family Expenses'] = mo.other * 12
    fam['Garbage'] = 0   // asked together with water
  }
  // the yearly vacation is a household category (v0.8 asked for it with the bills), not a separate recurring cost
  fam['Family Vacations'] = A.plans.includes('vacation') ? (A.planAmounts.vacation || 0) : 0
  // home improvement only applies to owners (houses carry their own maintenance too)
  if (A.housing !== 'own' && A.buy !== 'yes') fam['Home Improvement'] = 0
  fam['Property Tax'] = 0; fam['Home Insurance'] = 0   // carried by each home
  p.family_shared_expenses = fam
  p.houses = []
  if (A.housing === 'own') {
    const yearsIn = Math.max(0, 30 - A.home.years)
    p.houses.push({ name: 'Our home', mortgage_mode: 'actual', purchase_year: CY - yearsIn, purchase_price: A.home.value, current_value: A.home.value,
      mortgage_balance: A.home.balance, mortgage_rate: A.home.rate, mortgage_years_left: A.home.balance > 0 ? A.home.years : 0,
      property_tax_rate: A.home.value > 0 && A.home.tax != null ? A.home.tax / A.home.value : 0.01, home_insurance: 1800, maintenance_rate: 0.01, upkeep_costs: 1500, owner: 'Shared', appreciation_rate: 3,
      timeline: [{ year: CY - yearsIn, status: 'Own_Live', rental_income: 0 },
        ...(A.buy === 'yes' && A.buyPlan.sellCurrent ? [{ year: A.buyPlan.year, status: 'Sold', rental_income: 0 }] : [])] })
  }
  if (A.buy === 'yes') {
    const b = A.buyPlan
    p.houses.push({ name: 'Next home', mortgage_mode: 'estimate', purchase_year: b.year, purchase_price: b.price, current_value: b.price,
      down_payment_pct: b.down, loan_term_years: b.term, mortgage_rate: b.rate, mortgage_balance: b.price * (1 - b.down / 100), mortgage_years_left: b.term,
      pmi_rate: 0.5, closing_cost_pct: 3, property_tax_rate: 0.01, home_insurance: 1800, maintenance_rate: 0.01, upkeep_costs: 1500,
      owner: 'Shared', appreciation_rate: 3, timeline: [{ year: b.year, status: 'Own_Live', rental_income: 0 }] })
  }
  // kids
  p.children_list = A.kids === 'yes' ? A.children.map(k => ({ name: k.name || 'Child', birth_year: k.birth_year, use_template: true,
    template_state: A.location, template_strategy: strat.replace(' (statistical)', ''), school_type: k.school, college_type: k.college, college_location: A.location })) : []
  // healthcare: bridge coverage between early retirement and Medicare
  p.health_insurances = []
  const earliest = Math.min(A.p1.work === 'working' ? A.p1.retire : 99, !single && A.p2.work === 'working' ? A.p2.retire : 99)
  if (A.health === 'employer' && (A.empPremium || 0) > 0 && earliest < 99) {
    p.health_insurances.push({ name: 'Employer plan', type: 'Employer', monthly_premium: A.empPremium, annual_deductible: 2000,
      annual_out_of_pocket_max: 6000, copay_primary: 25, copay_specialist: 50, covered_by: 'Both', start_age: 0, end_age: Math.min(64, earliest - 1) })
  }
  if (A.health === 'marketplace' || earliest < 65) {
    p.health_insurances.push({ name: 'Marketplace plan', type: 'Marketplace', monthly_premium: A.bridge, annual_deductible: 5000,
      annual_out_of_pocket_max: 10000, copay_primary: 30, copay_specialist: 60, covered_by: 'Both',
      start_age: A.health === 'marketplace' ? 0 : earliest, end_age: 64 })
  }
  // big plans
  p.recurring_expenses = []; p.major_purchases = []
  for (const bp of BIG_PLANS.filter(b => A.plans.includes(b.value) && b.value !== 'vacation')) {
    const amt = A.planAmounts[bp.value] || 0
    if (bp.kind === 'recurring') p.recurring_expenses.push({ name: bp.label.replace(/ every.*| yearly/i, '').replace('Yearly ', ''), category: bp.value === 'car' ? 'Vehicle' : 'Travel',
      amount: amt, frequency_years: bp.every, start_year: CY + (bp.value === 'car' ? 2 : 0), end_year: null, inflation_adjust: true, parent: 'Both',
      financing_years: 0, interest_rate: 0 })
    else p.major_purchases.push({ name: bp.label, year: CY + (bp.value === 'renovation' ? 5 : bp.value === 'wedding' ? 20 : 10), amount: amt,
      financing_years: 0, interest_rate: 0, asset_type: bp.value === 'boat' ? 'Depreciating' : 'Expense', appreciation_rate: bp.value === 'boat' ? -0.1 : 0 })
  }
  for (const c of A.custom || []) {
    if (!c.name || !c.amount) continue
    if (c.kind === 'recurring') p.recurring_expenses.push({ name: c.name, category: 'Other', amount: c.amount, frequency_years: Math.max(1, c.every), start_year: c.year,
      end_year: null, inflation_adjust: true, parent: 'Both', financing_years: 0, interest_rate: 0 })
    else p.major_purchases.push({ name: c.name, year: c.year, amount: c.amount, financing_years: 0, interest_rate: 0, asset_type: 'Expense', appreciation_rate: 0 })
  }
  if (A.hsa) { p.hsa_balance = A.hsa.balance; p.hsa_contribution = A.hsa.contrib }
  if (A.oop) p.health_expenses = [{ name: 'Out-of-pocket medical', annual_amount: A.oop, affected_person: 'Both', start_age: 0, end_age: 120 }]
  if (!single && A.sep?.on) {
    p.ownership_tracking = { enabled: true, regime: A.sep.prenup ? 'prenup' : 'auto', earnings: A.sep.prenup && A.sep.earningsSeparate ? 'separate' : 'marital',
      separate_income: 'auto', marital_split_pct: 50, shortfall: 'balances',
      today: { p1: { liquid: Math.min(A.sep.p1.liquid, A.p1.savings), pretax: Math.min(A.sep.p1.pretax, A.p1.retirement) },
        p2: { liquid: Math.min(A.sep.p2.liquid, A.p2.savings), pretax: Math.min(A.sep.p2.pretax, A.p2.retirement) } } }
  }
  p.windfalls = (A.gifts || []).filter(g => g.amount > 0 && g.year >= CY).map(g => ({ name: g.name || 'Inheritance', year: g.year, amount: g.amount,
    recipient: single ? 'Parent 1' : g.who, kind: 'inheritance', separate: single ? true : g.who !== 'Both', inflation_adjust: true }))
  p.ss_insolvency_enabled = A.ssCut
  p.mc_simulations = 1000
  return p
}

function CareerStages({ w, A, set }: { w: 'p1' | 'p2'; A: Answers; set: (p: Partial<Answers>) => void }) {
  const ph = A.phases?.[w] || []
  const all = A.phases || { p1: [], p2: [] }
  const put = (list: Phase[]) => set({ phases: { ...all, [w]: list } })
  const a = A[w]
  if (!ph.length) return (
    <button className="text-[13.5px] text-accent font-medium hover:underline" onClick={() => put([{ label: 'Current job', from: a.age, to: a.retire, salary: a.income, raise: a.raise }])}>
      Or plan it in career stages (different salary and raise per stage)
    </button>)
  return (
    <div className="space-y-2 rounded-xl border border-line p-3">
      <div className="flex items-center justify-between"><span className="text-[14px] font-medium">Career stages</span>
        <button className="text-[12.5px] text-muted hover:text-bad" onClick={() => put([])}>Use a single income instead</button></div>
      <div className="grid grid-cols-[1fr_70px_70px_130px_80px_28px] gap-2 text-[12px] text-muted"><span>Stage</span><span>From age</span><span>To age</span><span>Salary</span><span>Raise %</span><span /></div>
      {ph.map((x, k) => {
        const upd = (patch: Partial<Phase>) => put(ph.map((y, q) => q === k ? { ...y, ...patch } : y))
        return (
          <div key={k} className="space-y-1">
            <div className="grid grid-cols-[1fr_70px_70px_130px_80px_28px] gap-2 items-center">
              <TextInput value={x.label} placeholder="e.g. Senior role" onChange={v => upd({ label: v })} />
              <NumberInput value={x.from} step={1} onChange={v => upd({ from: Math.round(v) })} />
              <NumberInput value={x.to} step={1} onChange={v => upd({ to: Math.round(v) })} />
              <Money value={x.salary} step={5000} onChange={v => upd({ salary: v })} />
              <NumberInput value={x.raise} step={0.5} onChange={v => upd({ raise: v })} />
              <button className="text-muted hover:text-bad" disabled={ph.length < 2} onClick={() => put(ph.filter((_, q) => q !== k))}><Trash2 size={14} /></button>
            </div>
            {x.to > a.retire && <p className="text-[12.5px] text-warn">{x.label || 'This stage'} ends at {x.to}, after retirement at {a.retire}. Pay stops at retirement.</p>}
          </div>)
      })}
      <Button size="sm" onClick={() => { const prev = ph[ph.length - 1]; put([...ph, { label: `Stage ${ph.length + 1}`, from: prev.to, to: Math.max(prev.to + 1, Math.min(prev.to + 10, a.retire)), salary: Math.round(prev.salary * 1.2 / 1000) * 1000, raise: prev.raise }]) }}>
        <Plus size={14} />Add a stage</Button>
    </div>)
}

// ── steps ────────────────────────────────────────────────────────────────
const SECTIONS = ['About you', 'Income', 'Savings', 'Home', 'Family', 'Lifestyle', 'Check-ins', 'Review']

export default function Onboarding() {
  const nav = useNavigate()
  const { replacePlan, reference, household, refreshCheckins } = usePlan()
  const [A, setA] = useState<Answers>(() => {
    try { const s = sessionStorage.getItem('fp_onboarding'); if (s) return { ...DEFAULT, ...JSON.parse(s) } } catch { /* */ }
    return DEFAULT
  })
  const [i, setI] = useState(0)
  const [base, setBase] = useState<any>(null)
  const [preview, setPreview] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const set = (patch: Partial<Answers>) => setA(a => ({ ...a, ...patch }))
  const setP = (who: 'p1' | 'p2', patch: Partial<Answers['p1']>) => setA(a => ({ ...a, [who]: { ...a[who], ...patch } }))
  const couple = A.household === 'couple'
  const n1 = A.p1.name || 'You', n2 = A.p2.name || 'your partner'

  useEffect(() => { try { sessionStorage.setItem('fp_onboarding', JSON.stringify(A)) } catch { /* */ } }, [A])
  useEffect(() => { api.normalize({}).then(r => setBase(r.plan)) }, [])
  const curve = useCurve(A.location, CY, 0.03)
  // per-step citations: each wizard screen numbers its own sources
  const cLoc = useCites(['bea_rpp_2024', 'taxfoundation_state_2025'])
  const c401 = useCites(['irs_401k_2026'])
  const cSS = useCites(['ssa_bend_points', 'ssa_wage_base', 'ssa_trustees_2026'])
  const cKids = useCites(['childcareaware_2024', 'collegeboard', 'mit_living_wage'])
  const cLife = useCites(curveSources(curve))
  const cOwn = useCites(['irs_pub555'])
  const cHealth = useCites(['kff_ehbs_2025', 'kff_benchmark_2026', 'cms_age_rating', 'cms_partb_2026', 'irs_hsa_2026'])

  const plan = useMemo(() => base && curve ? buildPlan(A, base, curve) : null, [A, base, curve])
  const seq = useRef(0)
  useEffect(() => {
    if (!plan || i < 3) return
    const s = ++seq.current
    const t = setTimeout(async () => {
      const [pr, mc] = await Promise.all([api.project(plan), api.monteCarlo(plan, 300)])
      if (s === seq.current) setPreview({ pr, mc })
    }, 350)
    return () => clearTimeout(t)
  }, [plan, i])


  const steps: { section: number; body: React.ReactNode; valid?: boolean; skip?: boolean; next?: string }[] = [
    { section: 0, next: "Let's start", body: (
      <Question title={<>Let’s build your lifetime plan</>} subtitle="About 10 minutes. We'll ask one thing at a time, and you can change any answer later.">
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          {[['1', 'Tell us about your life', 'Ages, income, savings, home, kids'], ['2', 'See your future', 'Net worth, retirement, and the odds your money lasts'],
            ['3', 'Keep it alive', 'Quick check-ins keep the plan true to life']].map(([n, t, d]) => (
            <div key={n} className="rounded-xl border border-line bg-surface p-4"><div className="w-7 h-7 rounded-full bg-accentSoft text-accent font-semibold flex items-center justify-center mb-2">{n}</div>
              <div className="font-semibold">{t}</div><div className="text-muted mt-0.5">{d}</div></div>
          ))}
        </div>
        <Note>Not sure about a number? Take your best guess — every screen has a sensible default.</Note>
      </Question>) },
    { section: 0, body: (
      <Question title="Who is this plan for?" why="Couples share expenses, taxes and Social Security rules differ for married households.">
        <ChoiceCards value={A.household} onChange={v => set({ household: v })} options={[
          { value: 'single', label: 'Just me', icon: <User size={22} /> },
          { value: 'couple', label: 'Me and my partner', icon: <Users size={22} />, desc: 'Married or sharing finances' }]} />
      </Question>) },
    { section: 0, valid: !!A.p1.name && (!couple || !!A.p2.name), body: (
      <Question title={couple ? 'What are your names and ages?' : "What's your name and age?"}>
        {(['p1', ...(couple ? ['p2'] : [])] as ('p1' | 'p2')[]).map((w, k) => (
          <div key={w} className="grid grid-cols-[1fr_120px] gap-3">
            <BigField label={k === 0 ? 'Your first name' : "Partner's first name"}><TextInput big autoFocus={k === 0} value={A[w].name} onChange={v => setP(w, { name: v })} /></BigField>
            <BigField label="Age"><NumberInput big value={A[w].age} min={18} max={100} step={1} onChange={v => setP(w, { age: Math.round(v) })} /></BigField>
            <div className="col-span-2 flex flex-wrap gap-1.5 -mt-1">{EMOJIS.map(e => (
              <button key={e} onClick={() => setP(w, { emoji: e })} className={`w-9 h-9 rounded-lg text-lg ${A[w].emoji === e ? 'bg-accentSoft ring-2 ring-accent' : 'hover:bg-sunken'}`}>{e}</button>))}</div>
          </div>
        ))}
        {couple && <div className="grid sm:grid-cols-2 gap-3">
          <BigField label="Year you married or joined finances (optional)"><NumberInput big value={A.marriage ?? null} placeholder="e.g. 2019" step={1} onChange={v => set({ marriage: Math.round(v) })} /></BigField>
          <BigField label="How do you file taxes?" hint="Joint filing usually costs less"><Select value={A.filing || 'married'}
            options={[{ value: 'married', label: 'Married filing jointly' }, { value: 'single', label: 'Separately / not married' }]} onChange={v => set({ filing: v as any })} /></BigField>
        </div>}
      </Question>) },
    { section: 0, body: (
      <Question title="Where do you live?" subtitle="We use it for local cost-of-living averages and state income tax." why={<>Price levels differ by about a quarter between the cheapest and most expensive states, and more between cities and for rent<cLoc.Cite id="bea_rpp_2024" />. Top state income-tax rates run from 0% to 13.3%<cLoc.Cite id="taxfoundation_state_2025" />.</>}>
        <BigField label="Country → state → city"><LocationPicker value={A.location} catalog={reference?.location_catalog} onChange={v => set({ location: v })} /></BigField>
        <div className="space-y-2">
          <span className="block text-[14px] font-medium">Planning to move?</span>
          {(A.moves || []).map((m, j) => (
            <div key={j} className="flex flex-wrap items-center gap-2">
              <div className="w-24"><NumberInput value={m.year} step={1} onChange={v => set({ moves: A.moves!.map((x, k) => k === j ? { ...x, year: Math.round(v) } : x) })} /></div>
              <LocationPicker value={m.location} catalog={reference?.location_catalog} compact onChange={v => set({ moves: A.moves!.map((x, k) => k === j ? { ...x, location: v } : x) })} />
              <button className="p-1.5 text-muted hover:text-bad" onClick={() => set({ moves: A.moves!.filter((_, k) => k !== j) })}><Trash2 size={15} /></button>
            </div>))}
          <Button size="sm" onClick={() => set({ moves: [...(A.moves || []), { year: CY + 5, location: A.location }] })}><Plus size={14} />Add a move</Button>
          <p className="text-[13px] text-muted">Taxes and everyday prices follow you when you move. Map and details under Where you live.</p>
        </div>
        <cLoc.Sources />
      </Question>) },
    ...(['p1', ...(couple ? ['p2'] : [])] as ('p1' | 'p2')[]).map(w => ({ section: 1, body: (
      <Question title={w === 'p1' ? 'Are you working right now?' : `Is ${n2} working right now?`}>
        <ChoiceCards value={A[w].work} onChange={v => setP(w, { work: v })} options={[
          { value: 'working', label: 'Yes, working', icon: <Briefcase size={20} /> },
          { value: 'home', label: 'Not working / at home', icon: <Coffee size={20} />, desc: 'Parenting, studying or between jobs' },
          { value: 'retired', label: 'Retired', icon: <Armchair size={20} /> }]} />
        {A[w].work === 'working' && <>
          <BigField label="Yearly income before taxes" hint="Salary plus typical bonus. Don't include your partner."><Money big value={A[w].income} step={5000} onChange={v => setP(w, { income: v })} /></BigField>
          <div>
            <span className="block text-[14px] font-medium mb-2">How do you expect it to grow?</span>
            <ChoiceCards cols={3} value={A[w].raise} onChange={v => setP(w, { raise: v })} options={[
              { value: 2, label: 'Steady', desc: '~2% a year' }, { value: 3, label: 'Typical', desc: '~3% a year' }, { value: 5, label: 'Fast-growing', desc: '~5% a year' }]} />
          </div>
          <CareerStages w={w} A={A} set={set} />
          {!(A.phases?.[w] || []).length && <div className="space-y-2">
            <span className="block text-[14px] font-medium">Expect a career change? (optional)</span>
            {((A.jobs || { p1: [], p2: [] })[w] || []).map((j, k) => (
              <div key={k} className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-ink2">In</span><div className="w-24"><NumberInput value={j.year} step={1} onChange={v => set({ jobs: { ...A.jobs!, [w]: A.jobs![w].map((x, q) => q === k ? { ...x, year: Math.round(v) } : x) } })} /></div>
                <span className="text-sm text-ink2">new income</span><div className="w-40"><Money value={j.income} step={5000} onChange={v => set({ jobs: { ...A.jobs!, [w]: A.jobs![w].map((x, q) => q === k ? { ...x, income: v } : x) } })} /></div>
                <button className="p-1.5 text-muted hover:text-bad" onClick={() => set({ jobs: { ...A.jobs!, [w]: A.jobs![w].filter((_, q) => q !== k) } })}><Trash2 size={15} /></button>
                {j.year - CY + A[w].age >= A[w].retire && <span className="text-[12.5px] text-warn">After the planned retirement age — it won't count</span>}
              </div>))}
            <Button size="sm" onClick={() => set({ jobs: { ...(A.jobs || { p1: [], p2: [] }), [w]: [...((A.jobs || { p1: [], p2: [] })[w] || []), { year: CY + 3, income: Math.round(A[w].income * 1.25 / 1000) * 1000 }] } })}><Plus size={14} />Add a change</Button>
          </div>}
        </>}
      </Question>) })),
    { section: 1, skip: A.p1.work === 'retired' && (!couple || A.p2.work === 'retired'), body: (
      <Question title="When would you like to retire?" subtitle="An age you'd be happy with, not a promise." why="Retirement age is the single biggest lever in most plans: it changes both how long you save and how long the money must last.">
        {(['p1', ...(couple ? ['p2'] : [])] as ('p1' | 'p2')[]).filter(w => A[w].work !== 'retired').map(w => (
          <Card key={w}><div className="text-sm font-medium mb-1">{w === 'p1' ? n1 : n2}</div>
            <Slider value={A[w].retire} min={Math.max(40, A[w].age)} max={75} onChange={v => setP(w, { retire: v })} format={v => `Age ${v}`} />
            <p className="text-[13px] text-muted mt-1">That's {CY + A[w].retire - A[w].age}, in {A[w].retire - A[w].age} years.</p></Card>
        ))}
      </Question>) },
    { section: 2, body: (
      <Question title="How much have you saved so far?" subtitle="Rough totals are fine. Don't include your home — that comes next."
        why="Your savings compound for decades. Splitting out retirement accounts lets us handle taxes on withdrawals correctly.">
        {(['p1', ...(couple ? ['p2'] : [])] as ('p1' | 'p2')[]).map(w => (
          <div key={w} className="space-y-3">
            {couple && <div className="text-sm font-semibold">{w === 'p1' ? n1 : n2}</div>}
            <div className="grid sm:grid-cols-2 gap-3">
              <BigField label="Cash & investments" hint="Checking, savings, brokerage, crypto"><Money big value={A[w].savings} step={5000} onChange={v => setP(w, { savings: v })} /></BigField>
              <BigField label="Retirement accounts" hint="401(k), 403(b), IRA, HSA"><Money big value={A[w].retirement} step={5000} onChange={v => setP(w, { retirement: v })} /></BigField>
            </div>
          </div>
        ))}
      </Question>) },
    { section: 2, skip: A.p1.work !== 'working' && (!couple || A.p2.work !== 'working'), body: (
      <Question title="How much do you put into retirement accounts each year?" subtitle={couple ? 'Both of you together, including any employer match.' : 'Including any employer match.'}
        why={<>Pre-tax contributions lower your taxes today and grow until retirement. The 2026 401(k) employee limit is $24,500 per person under 50<c401.Cite id="irs_401k_2026" />.</>}>
        <ChoiceCards cols={3} value={[0, 10000, 24500].includes(A.contrib) ? A.contrib : -1} onChange={v => v >= 0 && set({ contrib: v })} options={[
          { value: 0, label: 'Nothing yet' }, { value: 10000, label: 'About $10k' }, { value: 24500, label: 'About $24.5k' }]} />
        <BigField label="Or enter an amount per year"><Money big value={A.contrib} step={1000} onChange={v => set({ contrib: v })} /></BigField>
        <c401.Sources />
      </Question>) },
    { section: 2, body: (
      <Question title={couple ? 'Anything kept separate, or coming your way?' : 'Expecting an inheritance or a large gift?'}
        subtitle={couple ? 'Money one of you had before the marriage, or inherited, can stay separate property. Optional: skip if it doesn\'t apply.' : 'Optional: skip if it doesn\'t apply.'}
        why={couple ? <>Most states treat what each of you brought in, inherited or was given as that person's own, and pay earned during the marriage as shared<cOwn.Cite id="irs_pub555" />. The plan can track both, year by year, under Who owns what.</> : undefined}>
        {couple && <>
          <ChoiceCards cols={2} value={A.sep?.on ? 'yes' : 'no'} onChange={v => set({ sep: { ...(A.sep || { prenup: false, earningsSeparate: false, p1: { liquid: 0, pretax: 0 }, p2: { liquid: 0, pretax: 0 } }), on: v === 'yes' } })}
            options={[{ value: 'no', label: 'No, it\'s all shared' }, { value: 'yes', label: 'Yes, some is separate' }]} />
          {A.sep?.on && <div className="space-y-3">
            {(['p1', 'p2'] as const).map(w => (
              <div key={w} className="grid sm:grid-cols-2 gap-3">
                <BigField label={`${w === 'p1' ? n1 : n2}: separate cash & investments`} hint={`Of ${money(A[w].savings, { compact: false })}`}>
                  <Money big value={A.sep![w].liquid} step={5000} onChange={v => set({ sep: { ...A.sep!, [w]: { ...A.sep![w], liquid: v } } })} /></BigField>
                <BigField label="Separate retirement money" hint={`Of ${money(A[w].retirement, { compact: false })}; usually the balance at the wedding plus its growth`}>
                  <Money big value={A.sep![w].pretax} step={5000} onChange={v => set({ sep: { ...A.sep!, [w]: { ...A.sep![w], pretax: v } } })} /></BigField>
              </div>))}
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={A.sep.prenup} onChange={e => set({ sep: { ...A.sep!, prenup: e.target.checked } })} className="accent-[rgb(var(--accent))]" />
              We have a prenup</label>
            {A.sep.prenup && <label className="flex items-center gap-2 text-sm pl-6"><input type="checkbox" checked={A.sep.earningsSeparate} onChange={e => set({ sep: { ...A.sep!, earningsSeparate: e.target.checked } })} className="accent-[rgb(var(--accent))]" />
              It keeps each person's pay separate</label>}
            <p className="text-[13px] text-muted">Fine-tune the rules, homes and a year-by-year view under Who owns what. This is a planning estimate, not legal advice.</p>
          </div>}
        </>}
        <div className="space-y-2">
          <span className="block text-[14px] font-medium">Expected inheritance or large gift (optional)</span>
          {(A.gifts || []).map((g, j) => (
            <div key={j} className="flex flex-wrap items-center gap-2">
              <div className="w-40"><TextInput value={g.name} placeholder="e.g. Inheritance" onChange={v => set({ gifts: A.gifts!.map((x, k) => k === j ? { ...x, name: v } : x) })} /></div>
              <div className="w-36"><Money value={g.amount} step={5000} onChange={v => set({ gifts: A.gifts!.map((x, k) => k === j ? { ...x, amount: v } : x) })} /></div>
              <span className="text-sm text-ink2">in</span><div className="w-24"><NumberInput value={g.year} step={1} onChange={v => set({ gifts: A.gifts!.map((x, k) => k === j ? { ...x, year: Math.round(v) } : x) })} /></div>
              {couple && <div className="w-40"><Select value={g.who} options={[{ value: 'Parent 1', label: `To ${n1}` }, { value: 'Parent 2', label: `To ${n2}` }, { value: 'Both', label: 'To both of us' }]}
                onChange={v => set({ gifts: A.gifts!.map((x, k) => k === j ? { ...x, who: v as any } : x) })} /></div>}
              <button className="p-1.5 text-muted hover:text-bad" onClick={() => set({ gifts: A.gifts!.filter((_, k) => k !== j) })}><Trash2 size={15} /></button>
            </div>))}
          <Button size="sm" onClick={() => set({ gifts: [...(A.gifts || []), { name: 'Inheritance', year: CY + 15, amount: 100000, who: 'Parent 1' }] })}><Plus size={14} />Add one</Button>
          <p className="text-[13px] text-muted">In today's dollars. Gifts and inheritances generally aren't taxable income for the person receiving them (a few states have an inheritance tax).</p>
        </div>
        {couple && <cOwn.Sources />}
      </Question>) },
    { section: 2, body: (
      <Question title="Do you know your Social Security estimate?" why={<>Your statement at <a className="text-accent" href="https://www.ssa.gov/myaccount/" target="_blank" rel="noreferrer">ssa.gov/myaccount</a> shows your benefit at full retirement age (67). If you skip it, we estimate it from today's income with the 2026 benefit formula<cSS.Cite id={['ssa_bend_points', 'ssa_wage_base']} />, assuming a full 35-year career.</>}>
        <ChoiceCards value={A.ss_mode} onChange={v => set({ ss_mode: v })} options={[
          { value: 'estimate', label: 'Estimate it for me', desc: 'Rough, based on income' }, { value: 'known', label: 'Yes, I have my statement' }]} />
        {(['p1', ...(couple ? ['p2'] : [])] as ('p1' | 'p2')[]).map(w => (
          A.ss_mode === 'known'
            ? <BigField key={w} label={`${w === 'p1' ? n1 : n2}: monthly benefit at 67`}><Money big value={A[w].ss} step={50} onChange={v => setP(w, { ss: v })} /></BigField>
            : <div key={w} className="flex justify-between text-sm rounded-lg bg-sunken px-4 py-3"><span>{w === 'p1' ? n1 : n2}</span>
                <b className="tnum">~{money(estimateSS(A[w].work === 'home' ? 0 : A[w].income), { compact: false })}/mo at 67</b></div>
        ))}
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={A.ssCut} onChange={e => set({ ssCut: e.target.checked })} className="accent-[rgb(var(--accent))]" />
          <span>Plan for a possible Social Security cut in 2034 (30%; the Trustees project about 17%<cSS.Cite id="ssa_trustees_2026" />, so this leaves a cushion)</span></label>
        <cSS.Sources />
      </Question>) },
    { section: 3, body: (
      <Question title="What's your housing situation?">
        <ChoiceCards value={A.housing} onChange={v => set({ housing: v })} options={[
          { value: 'rent', label: 'I rent', icon: <Key size={20} /> }, { value: 'own', label: 'I own a home', icon: <Home size={20} /> },
          { value: 'family', label: 'I live with family / other', icon: <Building2 size={20} /> }]} />
        {A.housing === 'rent' && <BigField label="Monthly rent"><Money big value={A.rent} step={100} onChange={v => set({ rent: v })} /></BigField>}
        {A.housing === 'own' && <div className="grid sm:grid-cols-2 gap-3">
          <BigField label="What's it worth today?" hint="A Zillow or Redfin estimate is fine"><Money big value={A.home.value} step={10000} onChange={v => set({ home: { ...A.home, value: v } })} /></BigField>
          <BigField label="Mortgage balance" hint="0 if paid off"><Money big value={A.home.balance} step={10000} onChange={v => set({ home: { ...A.home, balance: v } })} /></BigField>
          {A.home.balance > 0 && <>
            <BigField label="Interest rate"><Percent big fraction value={A.home.rate} decimals={3} onChange={v => set({ home: { ...A.home, rate: v } })} /></BigField>
            <BigField label="Years left on the loan"><NumberInput big value={A.home.years} min={1} max={40} step={1} onChange={v => set({ home: { ...A.home, years: Math.round(v) } })} /></BigField>
            <p className="sm:col-span-2 text-sm text-muted">Principal & interest ≈ <b className="text-ink tnum">{money(monthlyPayment(A.home.balance, A.home.rate, A.home.years), { compact: false })}/mo</b></p>
          </>}
          <BigField label="Property tax per year" hint="On your tax bill or mortgage statement; about 1% of value is typical">
            <Money big value={A.home.tax ?? Math.round(A.home.value * 0.01)} step={250} onChange={v => set({ home: { ...A.home, tax: v } })} /></BigField>
        </div>}
      </Question>) },
    { section: 3, body: (
      <Question title={A.housing === 'own' ? 'Planning to buy a different home?' : 'Planning to buy a home?'}>
        <ChoiceCards cols={2} value={A.buy} onChange={v => set({ buy: v })} options={[{ value: 'no', label: 'Not planning to' }, { value: 'yes', label: 'Yes, at some point' }]} />
        {A.buy === 'yes' && <div className="grid sm:grid-cols-2 gap-3">
          <BigField label="Around which year?"><NumberInput big value={A.buyPlan.year} min={CY} max={CY + 40} step={1} onChange={v => set({ buyPlan: { ...A.buyPlan, year: Math.round(v) } })} /></BigField>
          <BigField label="Price (today's market)"><Money big value={A.buyPlan.price} step={25000} onChange={v => set({ buyPlan: { ...A.buyPlan, price: v } })} /></BigField>
          <BigField label="Down payment"><Percent big value={A.buyPlan.down} decimals={0} onChange={v => set({ buyPlan: { ...A.buyPlan, down: v } })} /></BigField>
          <BigField label="Mortgage rate"><Percent big fraction value={A.buyPlan.rate} decimals={3} onChange={v => set({ buyPlan: { ...A.buyPlan, rate: v } })} /></BigField>
          {A.housing === 'own' && <label className="sm:col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" checked={A.buyPlan.sellCurrent}
            onChange={e => set({ buyPlan: { ...A.buyPlan, sellCurrent: e.target.checked } })} className="accent-[rgb(var(--accent))]" />Sell our current home that year</label>}
          <p className="sm:col-span-2 text-sm text-muted">You'll need about <b className="text-ink">{money(A.buyPlan.price * (A.buyPlan.down / 100 + 0.03))}</b> for the down payment and closing costs;
            P&I ≈ <b className="text-ink">{money(monthlyPayment(A.buyPlan.price * (1 - A.buyPlan.down / 100), A.buyPlan.rate, 30), { compact: false })}/mo</b>. Fine-tune in Homes.</p>
        </div>}
      </Question>) },
    { section: 4, body: (
      <Question title="Do you have kids, or plan to?" why={<>Children are one of the largest lifetime costs, from daycare (about $13,100 a year on average in 2024<cKids.Cite id="childcareaware_2024" />) to college<cKids.Cite id="collegeboard" />. We use regional averages by age<cKids.Cite id="mit_living_wage" />.</>}>
        <ChoiceCards cols={2} value={A.kids} onChange={v => set({ kids: v, children: v === 'yes' && !A.children.length ? [{ name: '', birth_year: CY - 2, school: 'Public', college: 'Public' }] : A.children })}
          options={[{ value: 'none', label: 'No kids', icon: <User size={20} /> }, { value: 'yes', label: 'Yes / planning to', icon: <Baby size={20} /> }]} />
        {A.kids === 'yes' && <div className="space-y-3">
          {A.children.map((k, j) => (
            <div key={j} className="grid grid-cols-[1fr_110px_120px_120px_32px] gap-2 items-end">
              <BigField label={j === 0 ? 'Name' : ''}><TextInput value={k.name} placeholder={`Child ${j + 1}`} onChange={v => set({ children: A.children.map((c, x) => x === j ? { ...c, name: v } : c) })} /></BigField>
              <BigField label={j === 0 ? 'Birth year' : ''}><NumberInput value={k.birth_year} step={1} onChange={v => set({ children: A.children.map((c, x) => x === j ? { ...c, birth_year: Math.round(v) } : c) })} /></BigField>
              <BigField label={j === 0 ? 'School' : ''}><Select value={k.school} options={['Public', 'Private']} onChange={v => set({ children: A.children.map((c, x) => x === j ? { ...c, school: v } : c) })} /></BigField>
              <BigField label={j === 0 ? 'College' : ''}><Select value={k.college} options={['Public', 'Private']} onChange={v => set({ children: A.children.map((c, x) => x === j ? { ...c, college: v } : c) })} /></BigField>
              <button className="h-9 flex items-center justify-center text-muted hover:text-bad" onClick={() => set({ children: A.children.filter((_, x) => x !== j) })}><Trash2 size={15} /></button>
            </div>
          ))}
          <Button size="sm" onClick={() => set({ children: [...A.children, { name: '', birth_year: CY + 1, school: 'Public', college: 'Public' }] })}><Plus size={14} />Add a child</Button>
          <p className="text-[13px] text-muted">Use a future birth year for kids you're planning.</p>
        </div>}
        <cKids.Sources />
      </Question>) },
    { section: 5, body: (
      <Question title="How much do you spend on yourselves?" subtitle={`Everyday personal spending for ${couple ? 'two adults' : 'one adult'} in ${A.location}: food, transport, clothing, fun. Not housing, kids or healthcare premiums.`}>
        <SpendingSlider curve={curve} value={A.level ?? 50} adults={couple ? 2 : 1} cite={<cLife.Cite id={curveSources(curve)} />}
          onChange={x => set({ level: x, style: strategyFor(x).replace(' (statistical)', '') as Answers['style'] })} />
        <p className="text-sm text-muted">Tap a label to jump to it. You can fine-tune every category later under Spending.</p>
        <cLife.Sources />
      </Question>) },
    { section: 5, body: (
      <Question title="What do your household bills look like?" subtitle="Monthly amounts for the whole household. Rough guesses are fine."
        why="These shared costs sit on top of personal spending. Utilities and subscriptions add up to thousands a year.">
        <div className="grid sm:grid-cols-2 gap-3">
          {([['utilities', 'Gas & electric'], ['water', 'Water & garbage'], ['internet', 'Internet & phone plans'], ['subs', 'Shared subscriptions'],
            ['pets', 'Pets'], ['other', 'Other household costs']] as const).map(([k, l]) => (
            <BigField key={k} label={`${l} per month`}><Money big value={A.monthly?.[k] ?? 0} step={10} onChange={v => set({ monthly: { ...A.monthly!, [k]: v } })} /></BigField>))}
        </div>
        <p className="text-sm text-muted">About <b className="text-ink">{money(Object.values(A.monthly || {}).reduce((a, b) => a + b, 0) * 12, { compact: false })}</b> a year.</p>
      </Question>) },
    { section: 5, body: (
      <Question title="How do you get health insurance?" why="Healthcare is often the biggest surprise in retirement, especially if you retire before Medicare starts at 65.">
        <ChoiceCards value={A.health} onChange={v => set({ health: v })} options={[
          { value: 'employer', label: 'Through work', icon: <Briefcase size={20} /> }, { value: 'marketplace', label: 'I buy my own', icon: <HeartPulse size={20} />, desc: 'Marketplace / ACA' },
          { value: 'medicare', label: 'Medicare', icon: <Armchair size={20} /> }]} />
        {A.health === 'employer' && <BigField label="Your share of the premium per month" hint={<>What comes out of your paycheck for health insurance. Workers paid about $570/mo on average toward employer family coverage in 2025<cHealth.Cite id="kff_ehbs_2025" />.</>}>
          <Money big value={A.empPremium ?? 0} step={25} onChange={v => set({ empPremium: v })} /></BigField>}
        {(A.health === 'marketplace' || Math.min(A.p1.retire, couple ? A.p2.retire : 99) < 65) &&
          <BigField label={A.health === 'marketplace' ? 'Monthly premium' : 'Estimated premium between retiring and Medicare (65)'}
            hint={<>Unsubsidized benchmark plans averaged $625/mo for a 40-year-old in 2026<cHealth.Cite id="kff_benchmark_2026" />; at 60+ they cost roughly twice that per person<cHealth.Cite id="cms_age_rating" />. Subsidies depend on income. Medicare Part B is $202.90/mo from 65<cHealth.Cite id="cms_partb_2026" />.</>}>
            <Money big value={A.bridge} step={100} onChange={v => set({ bridge: v })} /></BigField>}
        <div className="grid sm:grid-cols-3 gap-3">
          <BigField label="Out-of-pocket medical per year" hint="Deductibles, copays, prescriptions"><Money big value={A.oop ?? 0} step={250} onChange={v => set({ oop: v })} /></BigField>
          <BigField label="HSA balance"><Money big value={A.hsa?.balance ?? 0} step={1000} onChange={v => set({ hsa: { ...(A.hsa || { balance: 0, contrib: 0 }), balance: v } })} /></BigField>
          <BigField label="HSA contribution per year" hint={<>2026 limit $4,400 self-only, $8,750 family<cHealth.Cite id="irs_hsa_2026" /></>}><Money big value={A.hsa?.contrib ?? 0} step={500} onChange={v => set({ hsa: { ...(A.hsa || { balance: 0, contrib: 0 }), contrib: v } })} /></BigField>
        </div>
        <cHealth.Sources />
      </Question>) },
    { section: 5, body: (
      <Question title="Any big plans we should include?" subtitle="Tap all that apply. Amounts are in today's dollars.">
        <Chips values={A.plans as any} onToggle={v => set({ plans: A.plans.includes(v) ? A.plans.filter(x => x !== v) : [...A.plans, v] })}
          options={BIG_PLANS.map(b => ({ value: b.value, label: b.label }))} />
        {BIG_PLANS.filter(b => A.plans.includes(b.value)).map(b => (
          <div key={b.value} className="grid grid-cols-[1fr_180px] gap-3 items-center">
            <span className="text-sm">{b.label}<span className="block text-muted text-[12.5px]">{b.desc}</span></span>
            <Money value={A.planAmounts[b.value]} step={1000} onChange={v => set({ planAmounts: { ...A.planAmounts, [b.value]: v } })} />
          </div>
        ))}
        <div className="space-y-2">
          <span className="block text-[14px] font-medium">Anything else? (optional)</span>
          {(A.custom || []).map((c, j) => (
            <div key={j} className="flex flex-wrap items-center gap-2">
              <div className="w-48"><TextInput value={c.name} placeholder="e.g. Sabbatical, new roof" onChange={v => set({ custom: A.custom!.map((x, k) => k === j ? { ...x, name: v } : x) })} /></div>
              <div className="w-36"><Money value={c.amount} step={1000} onChange={v => set({ custom: A.custom!.map((x, k) => k === j ? { ...x, amount: v } : x) })} /></div>
              <div className="w-32"><Select value={c.kind} options={[{ value: 'once', label: 'Once, in' }, { value: 'recurring', label: 'Every N yrs from' }]} onChange={v => set({ custom: A.custom!.map((x, k) => k === j ? { ...x, kind: v as any } : x) })} /></div>
              <div className="w-24"><NumberInput value={c.year} step={1} onChange={v => set({ custom: A.custom!.map((x, k) => k === j ? { ...x, year: Math.round(v) } : x) })} /></div>
              {c.kind === 'recurring' && <><span className="text-sm text-ink2">every</span><div className="w-20"><NumberInput value={c.every} min={1} step={1} onChange={v => set({ custom: A.custom!.map((x, k) => k === j ? { ...x, every: Math.round(v) } : x) })} /></div><span className="text-sm text-ink2">yrs</span></>}
              <button className="p-1.5 text-muted hover:text-bad" onClick={() => set({ custom: A.custom!.filter((_, k) => k !== j) })}><Trash2 size={15} /></button>
            </div>))}
          <Button size="sm" onClick={() => set({ custom: [...(A.custom || []), { name: '', amount: 10000, kind: 'once', year: CY + 5, every: 5 }] })}><Plus size={14} />Add your own</Button>
        </div>
        <BigField label={couple ? `Plan until what age? (${n1})` : 'Plan until what age?'} hint="Planning long is safer.">
          <ChoiceCards cols={3} value={A.lifeExp} onChange={v => set({ lifeExp: v })} options={[{ value: 90, label: '90' }, { value: 95, label: '95', badge: 'Recommended' }, { value: 100, label: '100' }]} />
        </BigField>
        {couple && <BigField label={`Plan until what age? (${n2})`}>
          <ChoiceCards cols={3} value={A.life2 ?? A.lifeExp} onChange={v => set({ life2: v })} options={[{ value: 90, label: '90' }, { value: 95, label: '95' }, { value: 100, label: '100' }]} />
        </BigField>}
      </Question>) },
    { section: 6, body: (
      <Question title="How often should we check in?" subtitle="A check-in takes about 5 minutes: update your balances, see if you're on track, and the plan rolls forward."
        why="Plans drift: raises, markets, surprises. Regular check-ins turn a one-time plan into a living one and catch problems while they're small.">
        <ChoiceCards value={A.cadence} onChange={v => set({ cadence: v })} options={[
          { value: 'quarterly', label: 'Every quarter', desc: 'January, April, July, October', badge: 'Recommended', icon: <CalendarCheck size={20} /> },
          { value: 'semiannual', label: 'Twice a year', desc: 'January and July', icon: <CalendarCheck size={20} /> },
          { value: 'annual', label: 'Once a year', desc: 'Every January', icon: <CalendarCheck size={20} /> },
          { value: 'off', label: "I'll check in when I want" }]} />
      </Question>) },
    { section: 7, next: busy ? 'Creating…' : 'Create my plan', body: (
      <Question title="Here's your starting plan" subtitle="Everything can be changed later. Tap a section to fix anything.">
        <div className="space-y-2.5">
          {[
            ['About you', couple ? `${n1} (${A.p1.age}) & ${n2} (${A.p2.age}) · ${A.location}` : `${n1} (${A.p1.age}) · ${A.location}`, 0],
            ['Income', `${money(A.p1.work === 'working' ? A.p1.income : 0)}${couple ? ` + ${money(A.p2.work === 'working' ? A.p2.income : 0)}` : ''} · retire at ${A.p1.retire}${couple ? ` / ${A.p2.retire}` : ''}`, 1],
            ['Savings', `${money(A.p1.savings + A.p1.retirement + (couple ? A.p2.savings + A.p2.retirement : 0))} saved · ${money(A.contrib)}/yr to retirement accounts`, 2],
            ['Home', A.housing === 'rent' ? `Renting at ${money(A.rent, { compact: false })}/mo` : A.housing === 'own' ? `Own ${money(A.home.value)} home, ${money(A.home.balance)} mortgage` : 'Living with family', 3],
            ['Family', A.kids === 'yes' ? `${A.children.length} ${A.children.length === 1 ? 'child' : 'children'}` : 'No kids', 4],
            ['Lifestyle', `${curve ? describe(curve, A.level ?? 50).replace(/^US /, '') : A.style} · ${A.plans.length} big plans · plan to ${A.lifeExp}`, 5],
            ['Check-ins', A.cadence === 'off' ? 'Whenever I want' : A.cadence === 'quarterly' ? 'Every quarter' : A.cadence === 'semiannual' ? 'Twice a year' : 'Once a year', 6],
          ].map(([t, d, go]) => (
            <button key={t as string} onClick={() => setI(steps.findIndex(x => x.section === go))} className="w-full text-left flex items-center justify-between rounded-xl border border-line bg-surface px-4 py-3 hover:border-accent/40">
              <span><span className="block font-semibold text-[15px]">{t}</span><span className="text-[13.5px] text-ink2">{d}</span></span>
              <span className="text-[13px] text-accent font-medium">Edit</span>
            </button>
          ))}
        </div>
      </Question>) },
  ].filter(s => !s.skip)

  const step = steps[Math.min(i, steps.length - 1)]
  const last = i >= steps.length - 1

  const finish = async () => {
    if (!plan) return
    setBusy(true)
    try {
      await replacePlan(plan)
      const saved = await api.normalize(plan)
      await api.saveScenario('Onboarding plan', saved.plan)
      await api.checkinSettings({ cadence: A.cadence })
      const inv = A.p1.savings + A.p1.retirement + (couple ? A.p2.savings + A.p2.retirement : 0)
      const eq = A.housing === 'own' ? A.home.value - A.home.balance : 0
      await api.addCheckin({ kind: 'baseline', date: new Date().toISOString().slice(0, 10),
        balances: { p1: { liquid: A.p1.savings, pretax: A.p1.retirement }, ...(couple ? { p2: { liquid: A.p2.savings, pretax: A.p2.retirement } } : {}),
          homes: A.housing === 'own' ? [{ name: 'Our home', value: A.home.value, mortgage: A.home.balance }] : [], other_debts: 0 },
        totals: { investable: inv, home_equity: eq, net_worth: inv + eq },
        expected: { investable: inv, net_worth: inv + eq, success_rate: preview?.mc?.success_rate ?? null },
        percentile: 50, status: 'baseline', applied_to_plan: true, notes: 'Starting point from guided setup' })
      await refreshCheckins()
      try { sessionStorage.removeItem('fp_onboarding') } catch { /* */ }
      nav('/?welcome=1')
    } finally { setBusy(false) }
  }

  const s = preview?.pr?.summary
  const retRow = preview?.pr?.rows?.find((r: any) => r.year === s?.retirement_year)
  const aside = i >= 3 && preview ? (
    <div className="sticky top-8 rounded-2xl border border-line bg-surface p-5 shadow-card">
      <div className="flex items-center gap-2 text-[13px] font-semibold text-accent"><Sparkles size={15} />Your plan so far</div>
      <div className="mt-4 space-y-4">
        <div><div className="text-[12.5px] text-muted">Net worth at retirement ({s?.retirement_year})</div>
          <div className="text-[28px] font-semibold tracking-tight tnum">{money(retRow ? retRow.net_worth / retRow.infl_index : 0)}</div>
          <div className="text-[12px] text-muted">in today's dollars</div></div>
        <Sparkline values={(preview.pr.rows || []).map((r: any) => r.net_worth / r.infl_index)} height={48} />
        <div className="grid grid-cols-2 gap-3">
          <div><div className="text-[12.5px] text-muted">Chance it lasts</div>
            <div className={`text-xl font-semibold tnum ${preview.mc.success_rate >= 0.8 ? 'text-good' : preview.mc.success_rate < 0.6 ? 'text-bad' : ''}`}>{pct(preview.mc.success_rate, 0)}</div></div>
          <div><div className="text-[12.5px] text-muted">Savings last</div>
            <div className={`text-xl font-semibold ${s?.depletion_year ? 'text-bad' : 'text-good'}`}>{s?.depletion_year ? `to ${s.depletion_year}` : 'For life'}</div></div>
        </div>
        <p className="text-[12px] text-muted">Updates as you answer. Rough until you finish.</p>
      </div>
    </div>
  ) : undefined

  return (
    <FlowShell sections={SECTIONS} section={step.section} progress={(i + 1) / steps.length}
      onBack={i > 0 ? () => setI(i - 1) : undefined}
      onNext={last ? finish : () => setI(i + 1)} nextLabel={step.next || (last ? 'Create my plan' : 'Continue')}
      canNext={step.valid !== false && !busy && (!last || !!plan)}
      onClose={() => nav('/')} aside={aside}>
      {step.body}
    </FlowShell>
  )
}
