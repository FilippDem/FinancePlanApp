import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, Info, Sparkles, ArrowRight, TrendingUp, CalendarClock } from 'lucide-react'
import { useCites } from '../components/Cite'
import { usePlan } from '../lib/store'
import { money, pct } from '../lib/format'
import { Card, Stat, Segmented, Badge, Button, Toggle, Note } from '../components/ui'
import { NetWorthChart, FanChart, Marker, LinesChart } from '../components/charts'
import { Donut } from '../components/CashflowExplorer'
import { useTodayDollars, deflate } from '../lib/hooks'
import { DueBanner, CheckinStrip } from './Checkins'
import { ReportButton } from '../components/ReportButton'

export function retirementMarkers(plan: any, names: [string, string], single: boolean): Marker[] {
  const cy = plan.current_year
  const m: Marker[] = [{ year: cy + plan.parentX_retirement_age - plan.parentX_age, label: `${names[0]} retires` }]
  if (!single) {
    const y2 = cy + plan.parentY_retirement_age - plan.parentY_age
    if (y2 === m[0].year) m[0].label = 'Both retire'
    else m.push({ year: y2, label: `${names[1]} retires` })
  }
  return m
}

export function buildAlerts(proj: any, mc: any, plan: any) {
  const out: { tone: 'bad' | 'warn' | 'good' | 'info'; title: string; detail: string }[] = []
  if (!proj) return out
  const rows = proj.rows, s = proj.summary
  if (s.depletion_year) out.push({ tone: 'bad', title: `Savings run out in ${s.depletion_year}`, detail: `At age ${s.depletion_age1}, investable savings go negative in the projection. Spending after that is funded by debt.` })
  const working = rows.filter((r: any) => r.wages1 + r.wages2 > 0)
  const neg = working.filter((r: any) => r.cashflow < 0)
  if (neg.length) out.push({ tone: 'warn', title: `${neg.length} working year${neg.length > 1 ? 's' : ''} with negative cash flow`, detail: `First in ${neg[0].year} (${money(neg[0].cashflow)}). Spending exceeds after-tax income those years.` })
  for (const r of rows.filter((r: any) => r.down_payment > 0 && r.investable < 0)) {
    const buy = (proj.events || []).find((e: any) => e.type === 'house_buy' && e.year === r.year)
    out.push({ tone: 'bad', title: `Not enough savings to buy ${buy ? buy.label.replace(/^Buy /, '') : 'a home'} in ${r.year}`,
      detail: `The down payment and closing costs (${money(r.down_payment)}) push savings to ${money(r.investable)}. Lower the price, raise the down-payment savings or delay the purchase.` })
  }
  const r0 = rows[0]
  if (r0 && r0.total_income > 0 && r0.exp_housing / r0.total_income > 0.35)
    out.push({ tone: 'warn', title: 'Housing costs are high', detail: `Housing is ${pct(r0.exp_housing / r0.total_income, 0)} of gross income this year (a common guideline is under 30–35%).` })
  if (mc && mc.success_rate < 0.75) out.push({ tone: 'warn', title: `Plan succeeds in ${pct(mc.success_rate, 0)} of simulations`, detail: 'Consider saving more, retiring later or trimming spending. See Projections → Monte Carlo.' })
  // v0.8 alert set (per-person solvency, peak & drawdown, healthcare share, years covered at retirement, end of plan)
  if (plan.finance_mode === 'Separate') {
    const names = [plan.parent1_name, plan.parent2_name]
    for (const [k, i] of [['liquid1', 0], ['liquid2', 1]] as const) {
      const r = rows.find((x: any) => x[k] < 0)
      if (r) out.push({ tone: 'bad', title: `${names[i]}'s savings go negative in ${r.year}`, detail: 'Separate finances: consider rebalancing the shared-expense split or increasing savings.' })
    }
  }
  const nwT = (r: any) => r.net_worth / r.infl_index
  const peak = rows.reduce((a: any, b: any) => (nwT(b) > nwT(a) ? b : a), rows[0])
  if (peak && nwT(peak) > 0 && peak.year < rows[rows.length - 1].year)
    out.push({ tone: 'info', title: `Net worth peaks at ${money(nwT(peak))} in ${peak.year}`, detail: `Drawdown begins in ${peak.year + 1}; plan for declining assets after that (today's dollars).` })
  const hc = rows.find((r: any) => r.year > s.current_year && r.total_income > 0 && r.exp_healthcare / r.total_income > 0.25)
  if (hc) out.push({ tone: 'warn', title: `Healthcare exceeds 25% of income in ${hc.year}`, detail: `Healthcare ${money(hc.exp_healthcare)} vs income ${money(hc.total_income)} (${pct(hc.exp_healthcare / hc.total_income, 0)}).` })
  const retR = rows.find((r: any) => r.year === s.retirement_year)
  if (retR && retR.total_expenses > 0) {
    const yrs = retR.investable / retR.total_expenses
    out.push({ tone: yrs < 15 ? 'bad' : yrs < 25 ? 'warn' : 'good', title: yrs < 25 ? `Savings at retirement cover about ${Math.max(0, Math.round(yrs))} years of spending` : `Retirement savings look healthy (${Math.round(yrs)}+ years covered)`,
      detail: `In ${retR.year}: ${money(retR.investable / retR.infl_index)} saved vs ${money(retR.total_expenses / retR.infl_index)}/yr spending (today's dollars).` })
  }
  if (plan.ss_insolvency_enabled) out.push({ tone: 'info', title: `Social Security cut of ${plan.ss_shortfall_percentage}% from ${plan.ss_insolvency_year}`, detail: 'Modeled as a trust-fund shortfall. Change it under Assumptions.' })
  const last = rows[rows.length - 1]
  if (!s.depletion_year && last && last.net_worth > 0) out.push({ tone: 'info', title: `Plan ends with ${money(nwT(last))} remaining`, detail: `At age ${last.age1} in ${last.year} (today's dollars).` })
  if (!out.some(o => o.tone === 'bad' || o.tone === 'warn')) out.unshift({ tone: 'good', title: 'On track', detail: 'No cash-flow gaps or depletion in the base projection.' })
  const order = { bad: 0, warn: 1, good: 2, info: 3 }
  const firstRmd = rows.find((r: any) => r.rmd > 1)
  if (firstRmd) out.push({ tone: 'info', title: `Required withdrawals start in ${firstRmd.year}`,
    detail: `About ${money(firstRmd.rmd / firstRmd.infl_index)} that year (today's dollars) must come out of pre-tax accounts and is taxed as income, whether you need it or not.` })
  const own = s.ownership
  if (own && own.commingled_total > 1)
    out.push({ tone: 'warn', title: `Separate money pays shared costs from ${own.first_commingled_year}`,
      detail: `${money(own.commingled_total)} of separate property is spent on household costs once marital money runs out. See Who owns what.` })
  out.sort((a, b) => order[a.tone] - order[b.tone])
  return out
}

export function planCompletion(plan: any) {
  const checks: [boolean, string, string][] = [
    [!!plan.parent1_name && !/^(Parent 1|Me)$/.test(plan.parent1_name), 'Set your name', '/people'],
    [plan.parentX_income > 0 || plan.parentX_retirement_age <= plan.parentX_age, 'Enter your income', '/people'],
    [plan.parentX_net_worth > 0 || plan.parentY_net_worth > 0, 'Enter your savings', '/people'],
    [(plan.houses || []).length > 0 || (plan.family_shared_expenses?.['Mortgage/Rent'] || 0) > 0, 'Add your home or rent', '/homes'],
    [Object.values(plan.family_shared_expenses || {}).reduce((a: number, b: any) => a + (+b || 0), 0) > 0, 'Review household spending', '/spending'],
    [Object.values(plan.parentX_expenses || {}).reduce((a: number, b: any) => a + (+b || 0), 0) > 0, 'Set your spending level', '/spending'],
    [(plan.state_timeline || []).length > 0, 'Set where you live', '/locations'],
    [(plan.health_insurances || []).length > 0 || plan.parentX_retirement_age >= 65, 'Add health insurance', '/healthcare'],
  ]
  const missing = checks.filter(c => !c[0]).map(c => ({ label: c[1], to: c[2] }))
  return { pct: (checks.length - missing.length) / checks.length, missing }
}

export function validationWarnings(plan: any, names: [string, string], single: boolean) {
  const w: string[] = []
  const inc = (plan.parentX_income || 0) + (single ? 0 : plan.parentY_income || 0)
  const sum = (o: any) => Object.values(o || {}).reduce((a: number, b: any) => a + (+b || 0), 0)
  const exp = sum(plan.parentX_expenses) + (single ? 0 : sum(plan.parentY_expenses)) + sum(plan.family_shared_expenses)
  if (inc > 0 && exp > inc * 0.95) w.push(`Your yearly spending (${money(exp, { compact: false })}) is close to or above your gross income (${money(inc, { compact: false })}). After taxes you may be running a deficit.`)
  if ((plan.parentX_income || 0) === 0 && plan.parentX_retirement_age > plan.parentX_age) w.push(`${names[0]}'s income is $0 but retirement is at ${plan.parentX_retirement_age}. Is that intended?`)
  if (plan.parentX_retirement_age <= plan.parentX_age && (plan.parentX_income || 0) > 0) w.push(`${names[0]}'s retirement age (${plan.parentX_retirement_age}) is at or before their current age (${plan.parentX_age}), so the income entered is not used.`)
  if (!single && plan.parentY_retirement_age <= plan.parentY_age && (plan.parentY_income || 0) > 0) w.push(`${names[1]}'s retirement age (${plan.parentY_retirement_age}) is at or before their current age (${plan.parentY_age}), so the income entered is not used.`)
  return w
}

// Federal Reserve Survey of Consumer Finances 2022, net worth by age of head of household
export const SCF_2022 = [
  { max: 34, label: 'under 35', median: 39000, mean: 183500 }, { max: 44, label: '35–44', median: 135600, mean: 549600 },
  { max: 54, label: '45–54', median: 247200, mean: 975800 }, { max: 64, label: '55–64', median: 364500, mean: 1570000 },
  { max: 74, label: '65–74', median: 409900, mean: 1790000 }, { max: 200, label: '75+', median: 335600, mean: 1620000 }]

function HealthLights({ r0, nwNow, age, Cite }: { r0: any; nwNow: number; age: number; Cite: ReturnType<typeof useCites>['Cite'] }) {
  const inc = r0.total_income
  const saveRate = inc > 0 ? (inc - r0.total_expenses - r0.taxes + r0.contrib_pretax) / inc : 0
  const expRatio = inc > 0 ? r0.total_expenses / inc : 0
  const b = SCF_2022.find(x => age <= x.max)!
  const items = [
    { label: 'Savings rate', value: pct(saveRate, 0), tone: saveRate > 0.15 ? 'good' : saveRate > 0.05 ? 'warn' : 'bad',
      hint: <>Share of gross income saved, including 401(k). Green above 15%, yellow 5–15%. The US personal saving rate is about 3% of after-tax income (2026)<Cite id="bea_saving_rate" />.</> },
    { label: 'Net worth vs peers', value: nwNow >= b.median ? `${(nwNow / b.median).toFixed(1)}× median` : `${pct(nwNow / b.median, 0)} of median`,
      tone: nwNow > b.median * 1.2 ? 'good' : nwNow > b.median * 0.5 ? 'warn' : 'bad',
      hint: <>Households aged {b.label}: median {money(b.median)}, mean {money(b.mean)} (Federal Reserve SCF 2022)<Cite id="fed_scf_2022" />.</> },
    { label: 'Spending to income', value: pct(expRatio, 0), tone: expRatio < 0.6 ? 'good' : expRatio < 0.8 ? 'warn' : 'bad',
      hint: 'Spending (excluding taxes) as a share of gross income. Green below 60%, yellow 60–80%.' },
  ] as const
  return (
    <div className="grid sm:grid-cols-3 gap-3">
      {items.map(i => (
        <div key={i.label} className="rounded-lg border border-line p-3">
          <div className="flex items-center gap-2 text-[12.5px] text-muted"><span className={`w-2.5 h-2.5 rounded-full ${i.tone === 'good' ? 'bg-good' : i.tone === 'warn' ? 'bg-warn' : 'bg-bad'}`} />{i.label}</div>
          <div className="text-[20px] font-semibold tnum mt-0.5">{i.value}</div>
          <div className="text-[11.5px] text-muted leading-4 mt-0.5">{i.hint}</div>
        </div>))}
    </div>
  )
}

export default function Dashboard({ isNew }: { isNew: boolean }) {
  const { plan, proj, mc, mcLoading, names, single, ck } = usePlan()
  const { Cite, Sources } = useCites(['fed_scf_2022', 'bea_saving_rate', ...(plan.mc_use_historical ? ['damodaran_sp500'] : [])])
  const [view, setView] = useState<'projection' | 'range'>('projection')
  const [today, setToday] = useTodayDollars()
  const nav = useNavigate()
  const rows = useMemo(() => deflate(proj?.rows || [], today), [proj, today])
  const markers = retirementMarkers(plan, names, single)
  const s = proj?.summary
  const alerts = useMemo(() => buildAlerts(proj, mc, plan), [proj, mc, plan])
  const r0 = rows[0]
  const retRow = rows.find((r: any) => r.year === s?.retirement_year)
  const endRow = rows[rows.length - 1]

  const mcToday = useMemo(() => {
    if (!mc || !today || mc.normalized) return mc
    const idx = (proj?.rows || []).map((r: any) => r.infl_index)
    const scale = (arr: number[]) => arr.map((v, i) => v / (idx[i] || 1))
    const m = structuredClone(mc)
    for (const f of ['net_worth', 'investable']) for (const q of Object.keys(m[f])) m[f][q] = scale(m[f][q])
    return m
  }, [mc, today, proj])

  const completion = planCompletion(plan)
  const warnings = validationWarnings(plan, names, single)
  const yearsToRet = Math.min(plan.parentX_retirement_age - plan.parentX_age, single ? 999 : plan.parentY_retirement_age - plan.parentY_age)
  const peakRow = rows.length ? rows.reduce((a: any, b: any) => (b.net_worth > a.net_worth ? b : a), rows[0]) : null
  const upcoming = (proj?.events || []).filter((e: any) => e.year >= plan.current_year).slice(0, 7)
  const hour = new Date().getHours()
  const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight">{greet}, {names[0]}{!single && names[1] ? ` & ${names[1]}` : ''}</h1>
          <p className="text-sm text-muted mt-1">Your plan runs {plan.current_year}–{s?.end_year ?? '…'}. Every change recalculates instantly.</p>
        </div>
        <div className="flex items-center gap-3">
          <Toggle checked={today} onChange={setToday} label="Today's dollars" hint="Show future amounts in today's purchasing power" />
          <ReportButton />
        </div>
      </div>

      {completion.pct < 1 && (
        <div className="rounded-xl border border-line bg-surface px-5 py-3.5">
          <div className="flex items-center gap-3 text-sm"><span className="font-medium">Plan {Math.round(completion.pct * 100)}% complete</span>
            <div className="flex-1 h-1.5 rounded-full bg-sunken"><div className="h-1.5 rounded-full bg-accent" style={{ width: `${completion.pct * 100}%` }} /></div></div>
          <div className="flex flex-wrap gap-1.5 mt-2">{completion.missing.map(m => (
            <button key={m.label} onClick={() => nav(m.to)} className="text-[12.5px] px-2 h-7 rounded-md border border-line hover:bg-sunken">{m.label} →</button>))}</div>
        </div>)}
      {warnings.map((w, i) => <Note key={i} tone="warn">{w}</Note>)}
      <DueBanner />
      <CheckinStrip />
      {isNew && !(ck?.checkins?.length) && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-accent/25 bg-accentSoft/70 px-5 py-4">
          <Sparkles className="text-accent" size={20} />
          <div className="flex-1 min-w-[220px]">
            <div className="font-medium">This household is new</div>
            <div className="text-sm text-ink2">Answer a few easy questions (about 10 minutes), or load a demo household from Scenarios to explore.</div>
          </div>
          <Button variant="primary" onClick={() => nav('/setup')}>Start guided setup<ArrowRight size={15} /></Button>
          <Button onClick={() => nav('/scenarios')}>Browse demos</Button>
        </div>
      )}

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card><Stat label="Net worth today" value={money(s?.net_worth_now)}
          sub={`${money(s?.investable_now)} savings · ${money(r0?.home_equity)} home equity`} /></Card>
        <Card><Stat label={`At retirement (${s?.retirement_year ?? '—'})`} value={money(retRow?.net_worth)}
          sub={`${money(retRow?.investable)} investable${today ? ', today’s $' : ''}`} /></Card>
        <Card><Stat label="Plan success" value={mc ? pct(mc.success_rate, 0) : '…'}
          tone={mc ? (mc.success_rate >= 0.8 ? 'good' : mc.success_rate < 0.6 ? 'bad' : undefined) : undefined}
          sub={mcLoading ? 'Simulating…' : mc ? <>{mc.n.toLocaleString()} simulations · {mc.mode}{plan.mc_use_historical && <Cite id="damodaran_sp500" />}</> : ''} /></Card>
        <Card><Stat label="Savings last" value={s?.depletion_year ? `Until ${s.depletion_year}` : 'For life'}
          tone={s?.depletion_year ? 'bad' : 'good'}
          sub={s?.depletion_year ? `${names[0]} would be ${s.depletion_age1}` : `${money(endRow?.net_worth)} left at the end`} /></Card>
      </div>

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card><Stat label="Household income this year" value={money(r0?.total_income)} sub={single ? '' : `${names[0]} ${money(r0?.wages1)} · ${names[1]} ${money(r0?.wages2)}`} /></Card>
        <Card><Stat label="Years to retirement" value={yearsToRet <= 0 ? 'Retired' : `${yearsToRet}`}
          sub={single ? `${names[0]} at ${plan.parentX_retirement_age}` : `${names[0]} at ${plan.parentX_retirement_age} · ${names[1]} at ${plan.parentY_retirement_age}`} /></Card>
        <Card><Stat label="Peak net worth" value={money(peakRow?.net_worth)} sub={peakRow ? `${peakRow.year} · ${names[0]} age ${peakRow.age1}` : ''} /></Card>
        {plan.finance_mode === 'Separate' && !single
          ? <Card><Stat label="Savings by person today" value={`${money(plan.parentX_net_worth)} · ${money(plan.parentY_net_worth)}`} sub={`${names[0]} · ${names[1]} (separate finances)`} /></Card>
          : <Card><Stat label="End of plan" value={money(endRow?.net_worth)} sub={endRow ? `${endRow.year} · ${names[0]} age ${endRow.age1}` : ''} /></Card>}
      </div>

      <Card title="Net worth" subtitle={view === 'projection' ? 'Expected path with your assumptions' : 'Range of outcomes across simulations'}
        action={<Segmented value={view} onChange={setView} options={[{ value: 'projection', label: 'Projection' }, { value: 'range', label: 'Range' }]} />}>
        {view === 'projection'
          ? (rows.length ? <NetWorthChart rows={rows} markers={markers} /> : <div className="h-[300px]" />)
          : (mcToday ? <FanChart mc={mcToday} markers={markers} /> : <div className="h-[320px] flex items-center justify-center text-muted text-sm">Simulating…</div>)}
      </Card>

      {plan.finance_mode === 'Separate' && !single && rows.length > 0 && (
        <Card title="Savings by person" subtitle="Separate finances: each person's own savings (shared costs split by the percentage on People & income)">
          <LinesChart data={rows.map((r: any) => ({ year: r.year, a: r.liquid1, b: r.liquid2 }))} series={[{ key: 'a', label: names[0] }, { key: 'b', label: names[1] }]} height={240} />
        </Card>)}

      {r0 && <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Financial health" subtitle={`${plan.current_year}, compared with common guidelines and US households`}>
          <HealthLights r0={r0} nwNow={s?.net_worth_now || 0} age={plan.parentX_age} Cite={Cite} />
        </Card>
        <Card title="This year, per month">
          <dl className="grid grid-cols-2 gap-y-2 text-sm">
            {[['Income', r0.total_income], ['Spending', r0.total_expenses], ['Taxes', r0.taxes], ['401(k)/HSA', r0.contrib_pretax],
              ['Left over', r0.total_income - r0.total_expenses - r0.taxes]].map(([l, v]: any) => (
              <React.Fragment key={l}><dt className="text-ink2">{l}</dt>
                <dd className={`text-right tnum ${l === 'Left over' ? (v >= 0 ? 'text-good font-semibold' : 'text-bad font-semibold') : ''}`}>{money(v / 12, { compact: false })}</dd></React.Fragment>))}
          </dl>
          <p className="text-[12px] text-muted mt-2">Left over = income − spending − taxes (401(k) contributions are part of it).</p>
        </Card>
      </div>}

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Income sources" subtitle={`${plan.current_year}`}>
          {r0 && <Donut title="" items={[{ name: `${names[0]} wages`, value: r0.wages1 }, ...(single ? [] : [{ name: `${names[1]} wages`, value: r0.wages2 }]),
            { name: 'Social Security', value: r0.ss_income }, { name: 'Rental income', value: r0.rent_income },
            { name: 'Investment growth', value: Math.max(0, r0.investment_growth || 0) }].filter(x => x.value > 0.5)} />}
        </Card>
        <Card title={`Cash flow in ${plan.current_year}`} subtitle="Where this year's money goes">
          {r0 && <CashflowBreakdown r={r0} />}
        </Card>
        <Card title="Coming up" subtitle="Next life events" action={<Button size="sm" variant="ghost" onClick={() => nav('/timeline')}>All<ArrowRight size={14} /></Button>}>
          <ul className="space-y-2.5">
            {upcoming.length === 0 && <li className="text-sm text-muted">No upcoming events.</li>}
            {upcoming.map((e: any, i: number) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                <span className="w-12 shrink-0 tnum text-muted font-medium">{e.year}</span>
                <span className="flex-1 truncate">{e.label}</span>
                {e.amount ? <span className="tnum text-ink2">{money(e.amount)}</span> : null}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Insights">
          <ul className="space-y-3">
            {alerts.map((a, i) => (
              <li key={i} className="flex gap-2.5">
                {a.tone === 'bad' && <AlertTriangle size={17} className="text-bad shrink-0 mt-0.5" />}
                {a.tone === 'warn' && <AlertTriangle size={17} className="text-warn shrink-0 mt-0.5" />}
                {a.tone === 'good' && <CheckCircle2 size={17} className="text-good shrink-0 mt-0.5" />}
                {a.tone === 'info' && <Info size={17} className="text-accent shrink-0 mt-0.5" />}
                <div><div className="text-sm font-medium">{a.title}</div><div className="text-[12.5px] text-muted">{a.detail}</div></div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <Sources className="px-1" />
    </div>
  )
}

function CashflowBreakdown({ r }: { r: any }) {
  const income = r.total_income
  const items = [
    { label: 'Taxes', v: r.taxes },
    { label: 'Living', v: r.exp_person1 + r.exp_person2 + r.exp_family },
    { label: 'Housing', v: r.exp_housing },
    { label: 'Children', v: r.exp_children },
    { label: 'Healthcare', v: r.exp_healthcare },
    { label: 'Recurring & one-time', v: r.exp_recurring + r.exp_purchases + r.down_payment },
    { label: 'Retirement contributions', v: r.contrib_pretax },
  ].filter(i => i.v > 0)
  const saved = income + r.sale_proceeds - items.reduce((a, b) => a + b.v, 0) + r.contrib_pretax
  const max = Math.max(income, 1)
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <span className="text-sm text-muted">Income</span><span className="text-lg font-semibold tnum">{money(income, { compact: false })}</span>
      </div>
      <div className="space-y-2">
        {items.map(i => (
          <div key={i.label}>
            <div className="flex justify-between text-[13px]"><span className="text-ink2">{i.label}</span><span className="tnum">{money(i.v, { compact: false })}</span></div>
            <div className="h-1.5 rounded-full bg-sunken mt-1"><div className="h-1.5 rounded-full bg-accent" style={{ width: `${Math.min(100, i.v / max * 100)}%` }} /></div>
          </div>
        ))}
      </div>
      <div className="flex items-baseline justify-between mt-4 pt-3 border-t border-line">
        <span className="text-sm font-medium flex items-center gap-1.5"><TrendingUp size={15} />Saved</span>
        <span className={`tnum font-semibold ${saved < 0 ? 'text-bad' : 'text-good'}`}>{money(saved, { compact: false })}
          <span className="text-muted font-normal text-[12.5px] ml-1.5">{income > 0 ? pct(saved / income, 0) : ''}</span></span>
      </div>
    </div>
  )
}
