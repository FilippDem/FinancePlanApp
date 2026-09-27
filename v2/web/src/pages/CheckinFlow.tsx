import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { TrendingUp, TrendingDown, CheckCircle2, AlertTriangle, ClipboardList, Landmark, Home, Scale, Sparkles, ArrowRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct } from '../lib/format'
import { FlowShell, Question, Chips, BigField } from '../components/flow'
import { Money, TextInput, Button, Note } from '../components/ui'
import { fmtWhen, isStale } from './Linked'

export const STATUS_META: Record<string, { label: string; tone: 'good' | 'warn' | 'bad' | 'accent'; blurb: string }> = {
  ahead: { label: 'Ahead of plan', tone: 'good', blurb: "You're ahead of where the plan expected." },
  on_track: { label: 'On track', tone: 'good', blurb: "You're right where the plan expected." },
  behind: { label: 'A bit behind', tone: 'warn', blurb: 'Slightly behind; small changes can close the gap.' },
  off_track: { label: 'Off track', tone: 'bad', blurb: "Well below the plan's expected range." },
  baseline: { label: 'Starting point', tone: 'accent', blurb: 'The baseline future check-ins are measured against.' },
}

const CHANGES = [
  { value: 'new_job', label: 'New job or raise', to: '/people' }, { value: 'lost_job', label: 'Lost a job', to: '/people' },
  { value: 'baby', label: 'Baby on the way', to: '/kids' }, { value: 'moved', label: 'Moved', to: '/assumptions' },
  { value: 'home', label: 'Bought / sold a home', to: '/homes' }, { value: 'purchase', label: 'Big purchase', to: '/spending' },
  { value: 'health', label: 'Health event', to: '/healthcare' }, { value: 'nothing', label: 'Nothing major', to: '' },
]
const round100 = (v: number) => Math.round(v / 100) * 100

/** Horizontal band showing where the actual value falls in the plan's range. */
export function RangeBar({ exp, actual }: { exp: any; actual: number }) {
  const lo = Math.min(exp.p5, actual), hi = Math.max(exp.p95, actual)
  const x = (v: number) => `${((v - lo) / Math.max(hi - lo, 1)) * 100}%`
  return (
    <div className="mt-2">
      <div className="relative h-10">
        <div className="absolute top-4 h-2 rounded-full bg-sunken" style={{ left: 0, right: 0 }} />
        <div className="absolute top-4 h-2 rounded-full bg-accent/20" style={{ left: x(exp.p10), width: `calc(${x(exp.p90)} - ${x(exp.p10)})` }} />
        <div className="absolute top-4 h-2 rounded-full bg-accent/45" style={{ left: x(exp.p25), width: `calc(${x(exp.p75)} - ${x(exp.p25)})` }} />
        <div className="absolute top-2.5 w-[2px] h-5 bg-ink2" style={{ left: x(exp.p50) }} title="Plan's median" />
        <div className="absolute top-[9px] w-4 h-4 -ml-2 rounded-full bg-accent ring-4 ring-surface" style={{ left: x(actual) }} />
      </div>
      <div className="flex justify-between text-[12px] text-muted tnum"><span>{money(exp.p10)} (10th)</span><span>plan median {money(exp.p50)}</span><span>{money(exp.p90)} (90th)</span></div>
    </div>
  )
}

export default function CheckinFlow() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const quick = params.get('mode') === 'quick'
  const { plan, proj, replacePlan, ck, refreshCheckins, names, single } = usePlan()
  const today = new Date().toISOString().slice(0, 10)
  const [i, setI] = useState(0)
  const [exp, setExp] = useState<any>(null)
  const [b, setB] = useState<any>(null)
  const [total, setTotal] = useState<number>(0)
  const [changes, setChanges] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [result, setResult] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [linked, setLinked] = useState<any>(null)   // linked-account balances (optional)
  const last = (ck?.checkins || []).slice(-1)[0]

  // homes owned today (from the projection's current-year row)
  const owned = useMemo(() => {
    const row = (proj?.rows || []).find((r: any) => r.year === new Date().getFullYear()) || proj?.rows?.[0]
    const f = (new Date().getMonth() + 0.5) / 12
    return (plan.houses || []).map((h: any, k: number) => ({ h, d: row?.details?.houses?.[k] }))
      .filter((x: any) => x.d && (x.d.status === 'Own_Live' || x.d.status === 'Own_Rent'))
      .map((x: any) => ({
        name: x.h.name,
        value: round100(x.h.current_value + ((x.d.value ?? x.h.current_value) - x.h.current_value) * f),
        mortgage: round100(x.h.mortgage_balance + ((x.d.balance ?? x.h.mortgage_balance) - x.h.mortgage_balance) * f),
      }))
  }, [plan, proj])

  // pre-fill with what the plan expects today
  useEffect(() => {
    if (!proj || b) return
    // linked accounts (optional): refresh if stale, then use them as the starting balances
    const lk = api.linked().then(async (l: any) => {
      if (l.snaptrade?.configured && isStale(l.last_sync)) { try { l = await api.linkedSync() } catch { /* keep last */ } }
      return l.totals?.accounts > 0 ? l : null
    }).catch(() => null)
    Promise.all([api.evaluate(plan, today, 0), lk]).then(([ev, l]) => {
      setExp(ev.expected)
      setLinked(l)
      const start = (plan.parentX_net_worth || 0) + (single ? 0 : plan.parentY_net_worth || 0) + (plan.hsa_balance || 0)
      const r = start > 0 ? ev.expected.investable / start : 1
      const ot = plan.ownership_tracking?.enabled && !single ? plan.ownership_tracking.today : null
      const per = (w: 'X' | 'Y') => ({ liquid: round100(((plan[`parent${w}_net_worth`] || 0) - (plan[`parent${w}_pretax_balance`] || 0)) * r),
        pretax: round100((plan[`parent${w}_pretax_balance`] || 0) * r),
        // who-owns-what: how much of each balance is still separate property
        ...(ot ? { separate_liquid: round100((ot[w === 'X' ? 'p1' : 'p2']?.liquid || 0) * r), separate_pretax: round100((ot[w === 'X' ? 'p1' : 'p2']?.pretax || 0) * r) } : {}) })
      const init: any = { p1: per('X'), ...(single ? {} : { p2: per('Y') }), homes: owned, other_debts: last?.balances?.other_debts ?? 0 }
      if (l && l.covers_all) {
        for (const w of (single ? ['p1'] : ['p1', 'p2']) as ('p1' | 'p2')[]) {
          const t = l.totals[w]
          init[w] = { ...init[w], liquid: round100(t.liquid), pretax: round100(t.pretax) }
          if (ot) {
            // separate property: from accounts marked separate if any; otherwise keep the plan's estimate (capped)
            init[w].separate_liquid = t.any_separate ? round100(t.separate_liquid) : Math.min(init[w].separate_liquid || 0, init[w].liquid)
            init[w].separate_pretax = t.any_separate ? round100(t.separate_pretax) : Math.min(init[w].separate_pretax || 0, init[w].pretax)
          }
        }
        init.from_linked = true
      }
      setB(init)
      setTotal(round100(init.from_linked
        ? init.p1.liquid + init.p1.pretax + (init.p2 ? init.p2.liquid + init.p2.pretax : 0) - (init.other_debts || 0)
        : ev.expected.investable))
    })
  }, [proj])

  const investable = quick ? total : (b ? b.p1.liquid + b.p1.pretax + (b.p2 ? b.p2.liquid + b.p2.pretax : 0) - (b.other_debts || 0) : 0)
  const equity = b ? b.homes.reduce((a: number, h: any) => a + (h.value - h.mortgage), 0) : 0
  const netWorth = investable + equity

  // quick mode: split the total the same way the plan splits savings today
  const balancesForSave = () => {
    if (!quick) return b
    const s1 = (plan.parentX_net_worth || 0), s2 = single ? 0 : (plan.parentY_net_worth || 0)
    const share = s1 + s2 > 0 ? s1 / (s1 + s2) : 1
    const split = (w: 'X' | 'Y', part: number) => {
      const nw = plan[`parent${w}_net_worth`] || 0, pre = plan[`parent${w}_pretax_balance`] || 0
      const preShare = nw > 0 ? pre / nw : 0
      return { liquid: round100(part * (1 - preShare)), pretax: round100(part * preShare) }
    }
    return { p1: split('X', total * share), ...(single ? {} : { p2: split('Y', total * (1 - share)) }), homes: b.homes, other_debts: 0 }
  }

  const evaluateNow = async () => {
    setBusy(true)
    try { setResult(await api.evaluate(plan, today, investable, netWorth)) } finally { setBusy(false) }
  }

  const save = async (apply: boolean) => {
    setBusy(true)
    try {
      const balances = balancesForSave()
      let after: number | null = null
      if (apply) {
        await api.saveScenario(`Before check-in ${ck?.period || today}`, plan)
        const { plan: np } = await api.rebase(plan, balances, today)
        await replacePlan(np)
        after = (await api.monteCarlo(np, 500)).success_rate
      }
      await api.addCheckin({
        date: today, kind: quick ? 'quick' : (ck?.due ? 'scheduled' : 'manual'), balances,
        totals: { investable, home_equity: equity, net_worth: netWorth },
        expected: result.expected, percentile: result.percentile, status: result.status,
        life_changes: changes, notes, applied_to_plan: apply, success_rate_after: after,
      })
      await refreshCheckins()
      nav(changes.filter(c => c !== 'nothing').length ? `/checkins?done=1&changes=${changes.join(',')}` : '/checkins?done=1')
    } finally { setBusy(false) }
  }

  const P = (w: 'p1' | 'p2', k: 'liquid' | 'pretax' | 'separate_liquid' | 'separate_pretax', v: number) => setB((x: any) => ({ ...x, [w]: { ...x[w], [k]: v } }))
  const sections = quick ? ['Update', 'Result'] : ['Start', 'Savings', 'Homes', 'Life', 'Result']

  const steps: { section: number; body: React.ReactNode; next?: string; onNext?: () => void; valid?: boolean }[] = quick ? [
    { section: 0, next: 'See how I’m doing', onNext: evaluateNow, valid: !!b, body: (
      <Question title="Quick update" subtitle={b?.from_linked ? 'Just the big numbers. Savings are filled in from your linked accounts; change anything that\'s off.' : "Just the big numbers. Pre-filled with what the plan expected today; change what's different."}>
        {linked && <LinkedNote linked={linked} used={!!b?.from_linked} names={names} single={single} onUse={() => setTotal(round100(['p1', 'p2'].reduce((a, w) => a + (linked.totals[w]?.liquid || 0) + (linked.totals[w]?.pretax || 0), 0)))} />}
        <BigField label="Total savings & investments today" hint="All accounts: cash, brokerage, retirement, HSA. Minus credit card or car debt.">
          <Money big value={total} step={1000} onChange={setTotal} /></BigField>
        {b?.homes.map((h: any, k: number) => (
          <div key={h.name} className="grid grid-cols-2 gap-3">
            <BigField label={`${h.name}: value`}><Money big value={h.value} step={5000} onChange={v => setB((x: any) => ({ ...x, homes: x.homes.map((y: any, j: number) => j === k ? { ...y, value: v } : y) }))} /></BigField>
            <BigField label="Mortgage balance"><Money big value={h.mortgage} step={1000} onChange={v => setB((x: any) => ({ ...x, homes: x.homes.map((y: any, j: number) => j === k ? { ...y, mortgage: v } : y) }))} /></BigField>
          </div>
        ))}
      </Question>) },
  ] : [
    { section: 0, next: "Let's go", valid: !!b, body: (
      <Question title={`${ck?.period ? ck.period.replace('-', ' ') + ' check-in' : 'Check-in'}`} subtitle="About 5 minutes. Have these handy:">
        <div className="grid sm:grid-cols-3 gap-3">
          {[[<Landmark size={20} />, 'Bank & brokerage', 'Current balances'], [<ClipboardList size={20} />, 'Retirement accounts', '401(k), IRA, HSA'],
            [<Home size={20} />, 'Home & mortgage', 'Zillow/Redfin estimate, loan statement']].map(([ic, t, d]) => (
            <div key={t as string} className="rounded-xl border border-line bg-surface p-4"><div className="text-accent mb-2">{ic}</div>
              <div className="font-semibold text-sm">{t}</div><div className="text-[13px] text-muted">{d}</div></div>
          ))}
        </div>
        {last && <p className="text-sm text-muted">Last check-in: {new Date(last.date).toLocaleDateString()} · {STATUS_META[last.status]?.label ?? last.status} · savings {money(last.totals?.investable)}</p>}
        <Note>Each field starts at what your plan expected for today, so you only change what's different.</Note>
      </Question>) },
    { section: 1, body: b && (
      <Question title="What are your balances today?" why="Separating retirement accounts matters because withdrawals from them are taxed.">
        {linked && <LinkedNote linked={linked} used={!!b.from_linked} names={names} single={single} onUse={() => setB((x: any) => {
          const y = { ...x, from_linked: true }
          for (const w of (single ? ['p1'] : ['p1', 'p2'])) y[w] = { ...x[w], liquid: round100(linked.totals[w].liquid), pretax: round100(linked.totals[w].pretax) }
          return y })} />}
        {(['p1', ...(single ? [] : ['p2'])] as ('p1' | 'p2')[]).map((w, k) => (
          <div key={w}>
            {!single && <div className="text-sm font-semibold mb-2">{names[k]}</div>}
            <div className="grid sm:grid-cols-2 gap-3">
              <BigField label="Cash & investments" hint="Checking, savings, brokerage"><Money big value={b[w].liquid} step={1000} onChange={v => P(w, 'liquid', v)} /></BigField>
              <BigField label="Retirement accounts" hint="401(k), IRA, HSA"><Money big value={b[w].pretax} step={1000} onChange={v => P(w, 'pretax', v)} /></BigField>
            </div>
            {b[w].separate_liquid !== undefined && <div className="grid sm:grid-cols-2 gap-3 mt-2">
              <BigField label="…of which separate property" hint="Kept apart: premarital money, gifts, inheritances"><Money value={b[w].separate_liquid} step={1000} onChange={v => P(w, 'separate_liquid', Math.min(v, b[w].liquid))} /></BigField>
              <BigField label="…of which separate property" hint="Usually the wedding-day balance plus its growth"><Money value={b[w].separate_pretax} step={1000} onChange={v => P(w, 'separate_pretax', Math.min(v, b[w].pretax))} /></BigField>
            </div>}
          </div>
        ))}
        <BigField label="Other debts (household)" hint="Credit cards, car loans, student loans. Not your mortgage.">
          <Money big value={b.other_debts} step={500} onChange={v => setB((x: any) => ({ ...x, other_debts: v }))} /></BigField>
      </Question>) },
    { section: 2, body: b && (
      <Question title={b.homes.length ? 'How about your home?' : 'No homes to update'} subtitle={b.homes.length ? 'An online estimate is fine for value; the balance is on your mortgage statement.' : 'Add homes any time under Homes.'}>
        {b.homes.map((h: any, k: number) => (
          <div key={h.name} className="grid sm:grid-cols-2 gap-3">
            <BigField label={`${h.name}: estimated value`}><Money big value={h.value} step={5000} onChange={v => setB((x: any) => ({ ...x, homes: x.homes.map((y: any, j: number) => j === k ? { ...y, value: v } : y) }))} /></BigField>
            <BigField label="Mortgage balance"><Money big value={h.mortgage} step={1000} onChange={v => setB((x: any) => ({ ...x, homes: x.homes.map((y: any, j: number) => j === k ? { ...y, mortgage: v } : y) }))} /></BigField>
          </div>
        ))}
      </Question>) },
    { section: 3, next: 'See how we’re doing', onNext: evaluateNow, body: (
      <Question title="Anything change since last time?" subtitle="We'll point you to the right place to update the plan afterward.">
        <Chips values={changes as any} onToggle={v => setChanges(c => v === 'nothing' ? ['nothing'] : c.includes(v) ? c.filter(x => x !== v) : [...c.filter(x => x !== 'nothing'), v])}
          options={CHANGES.map(c => ({ value: c.value, label: c.label }))} />
        <BigField label="Notes (optional)"><TextInput value={notes} onChange={setNotes} placeholder="e.g. Bonus came in lower; paid off the car" /></BigField>
      </Question>) },
  ]

  const resultStep = result && (() => {
    const m = STATUS_META[result.status] ?? STATUS_META.on_track
    const gap = result.gap
    const dLast = last ? investable - (last.totals?.investable ?? 0) : null
    const hint = gap < -0.05 * Math.max(result.expected.investable, 1)
      ? "Savings are below plan. The usual causes are spending above plan, a smaller raise or bonus, or a market dip. After updating, check Spending and Projections."
      : gap > 0.05 * Math.max(result.expected.investable, 1)
        ? 'Nice work. Updating the plan will show how much further ahead this puts your future.' : 'Steady as she goes.'
    return (
      <Question title={<span className="flex items-center gap-3">{m.tone === 'good' ? <CheckCircle2 className="text-good" size={30} /> : <AlertTriangle className={m.tone === 'bad' ? 'text-bad' : 'text-warn'} size={30} />}{m.label}</span>}
        subtitle={m.blurb}>
        <div className="rounded-2xl border border-line bg-surface p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div><div className="text-[13px] text-muted">Your savings today</div><div className="text-[30px] font-semibold tnum">{money(investable, { compact: false })}</div></div>
            <div className="text-right"><div className="text-[13px] text-muted">Plan expected</div><div className="text-lg font-semibold tnum">{money(result.expected.investable, { compact: false })}</div>
              <div className={`text-sm font-medium tnum ${gap >= 0 ? 'text-good' : 'text-bad'}`}>{gap >= 0 ? <TrendingUp size={14} className="inline" /> : <TrendingDown size={14} className="inline" />} {money(gap, { sign: true })}</div></div>
          </div>
          <RangeBar exp={result.expected} actual={investable} />
          <p className="text-sm text-ink2 mt-3">You're at the <b>{Math.round(result.percentile)}th percentile</b> of the outcomes the plan considered likely for today.</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="rounded-xl border border-line bg-surface p-3"><div className="text-muted text-[12px]">Net worth</div><div className="font-semibold tnum">{money(netWorth)}</div></div>
          <div className="rounded-xl border border-line bg-surface p-3"><div className="text-muted text-[12px]">Home equity</div><div className="font-semibold tnum">{money(equity)}</div></div>
          <div className="rounded-xl border border-line bg-surface p-3"><div className="text-muted text-[12px]">Since last check-in</div>
            <div className={`font-semibold tnum ${dLast !== null && dLast < 0 ? 'text-bad' : ''}`}>{dLast === null ? '—' : money(dLast, { sign: true })}</div></div>
        </div>
        <Note>{hint}</Note>
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button disabled={busy} onClick={() => save(true)} className="flex-1 inline-flex items-center justify-center gap-2 h-12 rounded-xl bg-accent text-white font-semibold hover:brightness-110 disabled:opacity-50">
            <Sparkles size={17} />{busy ? 'Updating…' : 'Update my plan with these numbers'}</button>
          <Button disabled={busy} className="h-12 rounded-xl" onClick={() => save(false)}>Just save the check-in</Button>
        </div>
        <p className="text-[12.5px] text-muted">Updating saves a copy of today's plan as “Before check-in {ck?.period}”, then starts the projection from these balances{new Date().getFullYear() > plan.current_year ? ` and rolls the plan to ${new Date().getFullYear()}` : ''}.</p>
      </Question>)
  })()

  const onResult = !!result
  const step = steps[Math.min(i, steps.length - 1)]
  return (
    <FlowShell sections={sections} section={onResult ? sections.length - 1 : step.section} progress={onResult ? 1 : (i + 1) / (steps.length + 1)}
      onBack={onResult ? () => setResult(null) : i > 0 ? () => setI(i - 1) : undefined}
      onNext={onResult ? undefined : async () => { if (step.onNext) await step.onNext(); else setI(i + 1) }}
      nextLabel={step.next || 'Continue'} canNext={step.valid !== false && !!b && !busy} onClose={() => nav('/checkins')} hideNav={onResult ? false : undefined}>
      {onResult ? resultStep : (b ? step.body : <p className="text-muted">Loading your plan…</p>)}
    </FlowShell>
  )
}


function LinkedNote({ linked, used, names, single, onUse }: { linked: any; used: boolean; names: string[]; single: boolean; onUse: () => void }) {
  const t = linked.totals
  const disabled = (linked.connections || []).filter((c: any) => c.disabled)
  return (
    <div className="rounded-lg border border-accent/25 bg-accentSoft/60 px-4 py-3 text-sm space-y-1">
      <div className="font-medium">{used ? 'Filled in from your linked accounts' : 'Your linked accounts'} <span className="text-muted font-normal">· {t.accounts} account{t.accounts === 1 ? '' : 's'}, as of {fmtWhen(t.as_of)}</span></div>
      <div className="text-ink2">{(single ? ['p1'] : ['p1', 'p2']).map((w, i) => `${names[i]}: ${money(t[w].liquid)} cash & investments, ${money(t[w].pretax)} retirement`).join(' · ')}</div>
      {!used && <div className="flex items-center gap-2"><span className="text-muted">They may not include accounts held elsewhere.</span><Button size="sm" onClick={onUse}>Use these</Button></div>}
      {used && <div className="text-muted">Add anything held outside the linked accounts.</div>}
      {disabled.length > 0 && <div className="text-warn">{disabled.map((c: any) => c.institution).join(', ')} needs you to sign in again under Linked accounts; these are the last balances received.</div>}
    </div>)
}
