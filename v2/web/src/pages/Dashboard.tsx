import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, Info, Sparkles, ArrowRight, TrendingUp, CalendarClock } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money, pct } from '../lib/format'
import { Card, Stat, Segmented, Badge, Button, Toggle } from '../components/ui'
import { NetWorthChart, FanChart, Marker } from '../components/charts'
import { useTodayDollars, deflate } from '../lib/hooks'
import { DueBanner, CheckinStrip } from './Checkins'

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
  if (plan.ss_insolvency_enabled) out.push({ tone: 'info', title: `Social Security cut of ${plan.ss_shortfall_percentage}% from ${plan.ss_insolvency_year}`, detail: 'Modeled as a trust-fund shortfall. Change it under Assumptions.' })
  if (!out.some(o => o.tone === 'bad' || o.tone === 'warn')) out.unshift({ tone: 'good', title: 'On track', detail: 'No cash-flow gaps or depletion in the base projection.' })
  return out
}

export default function Dashboard({ isNew }: { isNew: boolean }) {
  const { plan, proj, mc, mcLoading, names, single, ck } = usePlan()
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
        <Toggle checked={today} onChange={setToday} label="Today's dollars" hint="Show future amounts in today's purchasing power" />
      </div>

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
          sub={mcLoading ? 'Simulating…' : mc ? `${mc.n.toLocaleString()} simulations · ${mc.mode}` : ''} /></Card>
        <Card><Stat label="Savings last" value={s?.depletion_year ? `Until ${s.depletion_year}` : 'For life'}
          tone={s?.depletion_year ? 'bad' : 'good'}
          sub={s?.depletion_year ? `${names[0]} would be ${s.depletion_age1}` : `${money(endRow?.net_worth)} left at the end`} /></Card>
      </div>

      <Card title="Net worth" subtitle={view === 'projection' ? 'Expected path with your assumptions' : 'Range of outcomes across simulations'}
        action={<Segmented value={view} onChange={setView} options={[{ value: 'projection', label: 'Projection' }, { value: 'range', label: 'Range' }]} />}>
        {view === 'projection'
          ? (rows.length ? <NetWorthChart rows={rows} markers={markers} /> : <div className="h-[300px]" />)
          : (mcToday ? <FanChart mc={mcToday} markers={markers} /> : <div className="h-[320px] flex items-center justify-center text-muted text-sm">Simulating…</div>)}
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
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
