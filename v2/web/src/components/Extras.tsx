import React from 'react'
import { Plus, Trash2, Landmark, CreditCard, GraduationCap, Target, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money, pct, clsx } from '../lib/format'
import { Card, Field, Money, NumberInput, Percent, TextInput, Select, Button, Toggle, Badge, Note } from './ui'

const uid = (p: string) => `${p}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`

/* ── pensions & annuities ─────────────────────────────────────────────── */
export function PensionsCard({ cite }: { cite?: React.ReactNode }) {
  const { plan, update, names, single, proj } = usePlan()
  const list: any[] = plan.pensions || []
  const set = (i: number, k: string, v: any) => update(d => { d.pensions[i][k] = v })
  const add = (kind: 'pension' | 'annuity') => update(d => {
    (d.pensions ||= []).push({ id: uid('pen'), name: kind === 'pension' ? 'Pension' : 'Annuity', person: 'Parent 1', kind, start_age: 65,
      monthly: 1500, cola_pct: kind === 'pension' ? 2 : 0, survivor_pct: kind === 'pension' ? 50 : 100, taxable_pct: kind === 'pension' ? 100 : 50,
      todays_dollars: true, purchase_year: null, purchase_amount: 0 })
  })
  const people = [{ value: 'Parent 1', label: names[0] }, ...(single ? [] : [{ value: 'Parent 2', label: names[1] }])]
  const startIncome = (x: any) => {
    const who = x.person === 'Parent 1' ? 'X' : 'Y'
    const row = (proj?.rows || []).find((r: any) => (who === 'X' ? r.age1 : r.age2) === x.start_age)
    return row ? (who === 'X' ? row.pension1 : row.pension2) / row.infl_index : null
  }
  return (
    <Card title={<span className="flex items-center gap-2"><Landmark size={16} className="text-accent" />Pensions & annuities{cite}</span>}
      subtitle="Guaranteed income from an employer pension or an annuity you buy. Taxed as income (an annuity bought with after-tax money is only partly taxable)."
      action={<><Button size="sm" onClick={() => add('pension')}><Plus size={14} />Pension</Button><Button size="sm" onClick={() => add('annuity')}><Plus size={14} />Annuity</Button></>}>
      {list.length === 0 ? <p className="text-sm text-muted">No pensions or annuities. Teachers, government, military and many union jobs come with one.</p> : (
        <div className="space-y-3">
          {list.map((x, i) => (
            <div key={x.id || i} className="rounded-lg border border-line p-3.5 space-y-3">
              <div className="flex items-center gap-2">
                <input className="flex-1 bg-transparent font-medium outline-none" value={x.name} onChange={e => set(i, 'name', e.target.value)} />
                <Badge tone="accent">{x.kind}</Badge>
                <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d.pensions.splice(i, 1) })}><Trash2 size={15} /></button>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Field label="Paid to"><Select value={x.person} options={people} onChange={v => set(i, 'person', v)} /></Field>
                <Field label="Starts at age"><NumberInput value={x.start_age} min={40} max={90} step={1} onChange={v => set(i, 'start_age', Math.round(v))} /></Field>
                <Field label="Per month" hint={x.todays_dollars ? "In today's dollars; grows with inflation until it starts" : 'The amount on your statement, in the dollars of the start year'}>
                  <Money value={x.monthly} step={100} onChange={v => set(i, 'monthly', v)} /></Field>
                <Field label="Yearly increase (COLA)" hint="0% if the payment is fixed"><Percent value={x.cola_pct} decimals={1} onChange={v => set(i, 'cola_pct', v)} /></Field>
                {!single && <Field label="Survivor keeps" hint="Share paid to the spouse after the owner dies (joint-and-survivor option)"><Percent value={x.survivor_pct} decimals={0} onChange={v => set(i, 'survivor_pct', v)} /></Field>}
                <Field label="Taxable share" hint="100% for most pensions. Annuities bought with after-tax money: roughly the earnings share."><Percent value={x.taxable_pct} decimals={0} onChange={v => set(i, 'taxable_pct', v)} /></Field>
                {x.kind === 'annuity' && <>
                  <Field label="Buy in year" hint="Leave empty if you already own it"><NumberInput value={x.purchase_year} step={1} placeholder="owned" onChange={v => set(i, 'purchase_year', Math.round(v))} /></Field>
                  <Field label="Price (today's $)"><Money value={x.purchase_amount} onChange={v => set(i, 'purchase_amount', v)} /></Field>
                </>}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Toggle checked={x.todays_dollars !== false} onChange={v => set(i, 'todays_dollars', v)} label="Amount is in today's dollars" />
                {startIncome(x) != null && <span className="text-[12.5px] text-muted">First year: {money(startIncome(x), { compact: false })} (today's $)</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

/* ── loans & debts ────────────────────────────────────────────────────── */
const KINDS = [{ value: 'student', label: 'Student loan' }, { value: 'auto', label: 'Car loan' }, { value: 'credit_card', label: 'Credit card' },
  { value: 'personal', label: 'Personal loan' }, { value: 'medical', label: 'Medical debt' }, { value: 'other', label: 'Other' }]

function payoff(balance: number, ratePct: number, monthly: number) {
  const r = ratePct / 100 / 12
  if (balance <= 0) return 0
  if (monthly <= balance * r) return Infinity
  if (r === 0) return balance / monthly
  return -Math.log(1 - (r * balance) / monthly) / Math.log(1 + r)
}

export function DebtsCard() {
  const { plan, update, proj } = usePlan()
  const list: any[] = plan.debts || []
  const set = (i: number, k: string, v: any) => update(d => { d.debts[i][k] = v })
  const events: any[] = proj?.events || []
  return (
    <Card title={<span className="flex items-center gap-2"><CreditCard size={16} className="text-accent" />Loans & debts</span>}
      subtitle="Balances you owe today (not your mortgage — that's under Homes). Payments are fixed dollars; the balance counts against net worth."
      action={<Button size="sm" onClick={() => update(d => { (d.debts ||= []).push({ id: uid('debt'), name: 'Student loan', kind: 'student', balance: 25000, rate: 6, monthly_payment: 300, extra_monthly: 0, start_year: d.current_year }) })}><Plus size={14} />Add loan</Button>}>
      {list.length === 0 ? <p className="text-sm text-muted">No loans. Add student loans, car loans or card balances to see when they're paid off and what they cost.</p> : (
        <div className="space-y-2">
          <div className="hidden md:grid grid-cols-[1.3fr_1fr_1fr_.7fr_.9fr_.9fr_1fr_32px] gap-2 text-[12px] text-muted px-1">
            <span>Name</span><span>Kind</span><span>Balance</span><span>Rate</span><span>Per month</span><span>Extra / month</span><span>Paid off</span><span /></div>
          {list.map((x, i) => {
            const m = payoff(x.balance, x.rate, (x.monthly_payment || 0) + (x.extra_monthly || 0))
            const ev = events.find(e => e.type === 'debt_paid' && e.label.startsWith(x.name))
            const interest = isFinite(m) ? ((x.monthly_payment || 0) + (x.extra_monthly || 0)) * m - x.balance : null
            return (
              <div key={x.id || i} className="grid grid-cols-2 md:grid-cols-[1.3fr_1fr_1fr_.7fr_.9fr_.9fr_1fr_32px] gap-2 items-center">
                <TextInput value={x.name} onChange={v => set(i, 'name', v)} />
                <Select value={x.kind} options={KINDS} onChange={v => set(i, 'kind', v)} />
                <Money value={x.balance} step={500} onChange={v => set(i, 'balance', v)} />
                <Percent value={x.rate} decimals={2} onChange={v => set(i, 'rate', v)} />
                <Money value={x.monthly_payment} step={25} onChange={v => set(i, 'monthly_payment', v)} />
                <Money value={x.extra_monthly || 0} step={25} onChange={v => set(i, 'extra_monthly', v)} />
                <span className={clsx('text-[12.5px] tnum', !isFinite(m) && 'text-bad')} title={interest != null ? `Total interest about ${money(interest, { compact: false })}` : ''}>
                  {!isFinite(m) ? "Payment doesn't cover interest" : ev ? `${ev.year} (${Math.ceil(m)} mo)` : `${Math.ceil(m)} months`}</span>
                <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d.debts.splice(i, 1) })}><Trash2 size={15} /></button>
              </div>)
          })}
          <p className="text-[12px] text-muted mt-1">Tip: an extra payment on the highest-rate loan saves the most interest. Hover "Paid off" for the total interest.</p>
        </div>
      )}
    </Card>
  )
}

/* ── 529 college plans (one per child) ───────────────────────────────── */
export function College529({ child, cite }: { child: any; cite?: React.ReactNode }) {
  const { plan, update, proj } = usePlan()
  const list: any[] = plan.college_529 || []
  const i = list.findIndex(x => x.child === child.name)
  const x = i >= 0 ? list[i] : null
  const set = (k: string, v: any) => update(d => { const j = d.college_529.findIndex((y: any) => y.child === child.name); d.college_529[j][k] = v })
  const rows: any[] = proj?.rows || []
  let paid = 0, cost = 0
  for (const r of rows) {
    for (const e of r.details?.edu529 || []) if (e.child === child.name) paid += e.paid / r.infl_index
    for (const c of r.details?.children || []) if (c.name === child.name && c.in_college) cost += c.total / r.infl_index
  }
  if (!x) return (
    <div className="flex items-center gap-3 text-sm">
      <GraduationCap size={15} className="text-muted" />
      <span className="text-muted flex-1">No 529 college savings plan{cost > 0 ? ` — college costs about ${money(cost)} in today's dollars` : ''}.</span>
      <Button size="sm" onClick={() => update(d => { (d.college_529 ||= []).push({ child: child.name, balance: 0, monthly: 250, until_age: 18 }) })}><Plus size={14} />Add a 529</Button>
    </div>)
  return (
    <div className="rounded-lg border border-line p-3 space-y-2">
      <div className="flex items-center gap-2"><GraduationCap size={15} className="text-accent" /><span className="font-medium text-sm flex-1">529 plan{cite}</span>
        <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d.college_529.splice(i, 1) })}><Trash2 size={14} /></button></div>
      <div className="grid grid-cols-3 gap-2">
        <Field label="Balance today"><Money value={x.balance} step={500} onChange={v => set('balance', v)} /></Field>
        <Field label="Per month" hint="Today's dollars; grows with inflation"><Money value={x.monthly} step={25} onChange={v => set('monthly', v)} /></Field>
        <Field label="Until age"><NumberInput value={x.until_age} min={1} max={22} step={1} onChange={v => set('until_age', Math.round(v))} /></Field>
      </div>
      {cost > 0 && (
        <div>
          <div className="h-2 rounded-full bg-sunken overflow-hidden"><div className="h-full bg-good" style={{ width: `${Math.min(100, paid / cost * 100)}%` }} /></div>
          <p className="text-[12.5px] text-muted mt-1">Pays {money(paid)} of about {money(cost)} in college costs ({pct(Math.min(1, paid / cost), 0)}, today's $). Leftover money passes to a younger sibling's 529, or back to savings after tax and the 10% penalty on earnings.</p>
        </div>)}
    </div>
  )
}

/* ── goals ─────────────────────────────────────────────────────────────── */
export const GOAL_TYPES = [
  { value: 'fi', label: 'Work optional (financial independence)' },
  { value: 'net_worth', label: 'Net worth target' },
  { value: 'savings', label: 'Savings target (outside retirement accounts)' },
  { value: 'emergency_fund', label: 'Emergency fund' },
  { value: 'college', label: 'College funded' },
  { value: 'house_paid_off', label: 'House paid off' },
  { value: 'debt_free', label: 'Debt free' },
]

export function newGoal(plan: any, type = 'fi', year?: number) {
  const cy = plan.current_year
  const g: any = { id: uid('goal'), type, name: GOAL_TYPES.find(t => t.value === type)?.label.replace(/ \(.*\)/, '') || 'Goal', year: year ?? cy + 10, amount: 0, months: 6 }
  if (type === 'net_worth') g.amount = 2000000
  if (type === 'savings') { g.amount = 100000; g.name = 'Savings target' }
  if (type === 'fi') g.year = year ?? cy + Math.max(1, (plan.parentX_retirement_age - plan.parentX_age))
  if (type === 'college') g.child = plan.children_list?.[0]?.name || ''
  if (type === 'house_paid_off') g.house = plan.houses?.[0]?.name || ''
  return g
}

export function GoalStatus({ s }: { s: string }) {
  return s === 'on_track' ? <Badge tone="good"><CheckCircle2 size={12} className="inline -mt-0.5 mr-0.5" />On track</Badge>
    : s === 'at_risk' ? <Badge tone="warn"><AlertTriangle size={12} className="inline -mt-0.5 mr-0.5" />At risk</Badge>
    : <Badge tone="bad"><XCircle size={12} className="inline -mt-0.5 mr-0.5" />Off track</Badge>
}

export function GoalRow({ g, compact }: { g: any; compact?: boolean }) {
  const moneyish = !['house_paid_off', 'debt_free', 'college'].includes(g.type)
  return (
    <div className="py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <Target size={14} className="text-accent" />
        <span className="font-medium text-sm flex-1 min-w-[140px]">{g.name}</span>
        <span className="text-[12.5px] text-muted tnum">{g.type === 'emergency_fund' ? 'now' : g.year}</span>
        {g.probability != null && <span className="text-[12.5px] tnum text-ink2" title="Share of market simulations where this goal is met">{pct(g.probability, 0)} chance</span>}
        <GoalStatus s={g.status} />
      </div>
      <div className="h-2 rounded-full bg-sunken overflow-hidden mt-1.5">
        <div className={clsx('h-full', g.status === 'on_track' ? 'bg-good' : g.status === 'at_risk' ? 'bg-warn' : 'bg-bad')} style={{ width: `${Math.max(2, g.progress * 100)}%` }} />
      </div>
      {!compact && <p className="text-[12px] text-muted mt-1">
        {moneyish && g.target > 0 && <>Now {money(g.now)} of {money(g.target)} · projected {money(g.projected)} by {g.year} (today's $). </>}
        {g.note}</p>}
    </div>
  )
}

export function GoalEditor({ g, i }: { g: any; i: number }) {
  const { plan, update } = usePlan()
  const set = (k: string, v: any) => update(d => { d.goals[i][k] = v })
  const age = (y: number) => plan.parentX_age + (y - plan.current_year)
  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 items-end">
      <Field label="Name"><TextInput value={g.name} onChange={v => set('name', v)} /></Field>
      <Field label="Kind"><Select value={g.type} options={GOAL_TYPES} onChange={v => update(d => { const n = newGoal(plan, v, g.year); d.goals[i] = { ...n, id: g.id } })} /></Field>
      {g.type !== 'emergency_fund' && g.type !== 'college' && <Field label={`Year (age ${age(g.year)})`}><NumberInput value={g.year} step={1} min={plan.current_year} max={plan.current_year + 80} onChange={v => set('year', Math.round(v))} /></Field>}
      {['net_worth', 'savings'].includes(g.type) && <Field label="Amount (today's $)"><Money value={g.amount} onChange={v => set('amount', v)} /></Field>}
      {g.type === 'fi' && <Field label="Target (optional)" hint="Leave 0 to use 25× the yearly spending not covered by Social Security and pensions"><Money value={g.amount} onChange={v => set('amount', v)} /></Field>}
      {g.type === 'emergency_fund' && <Field label="Months of spending"><NumberInput value={g.months} min={1} max={24} step={1} onChange={v => set('months', Math.round(v))} /></Field>}
      {g.type === 'college' && <Field label="Child"><Select value={g.child} options={(plan.children_list || []).map((c: any) => c.name)} onChange={v => set('child', v)} /></Field>}
      {g.type === 'house_paid_off' && <Field label="Home"><Select value={g.house} options={(plan.houses || []).map((h: any) => h.name)} onChange={v => set('house', v)} /></Field>}
    </div>
  )
}

