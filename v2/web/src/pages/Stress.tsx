import React, { useEffect, useMemo, useState } from 'react'
import { Play, Plus, Trash2, RotateCcw, ShieldAlert, TrendingDown, Briefcase, HeartHandshake, Flame, UserX, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, clsx } from '../lib/format'
import { Card, PageHeader, Button, NumberInput, Money, Percent, Select, TextInput, Badge, Note, Toggle } from '../components/ui'
import { LinesChart } from '../components/charts'

const TYPES: Record<string, { label: string; icon: any; blurb: string }> = {
  market_crash: { label: 'Market crash', icon: TrendingDown, blurb: 'Stocks and bonds drop sharply in one year' },
  income_loss: { label: 'Income loss', icon: Briefcase, blurb: 'Job loss, disability or a career break' },
  extra_cost: { label: 'Extra cost', icon: HeartHandshake, blurb: 'Caring for a parent or child with special needs, long-term care' },
  inflation_spike: { label: 'High inflation', icon: Flame, blurb: 'Prices rise fast for several years' },
  early_death: { label: 'Early death', icon: UserX, blurb: 'Income, benefits and spending for one partner stop' },
}

function newTest(type: string, cy: number): any {
  const id = `${type}_${Math.random().toString(36).slice(2, 7)}`
  switch (type) {
    case 'market_crash': return { id, type, label: 'Market crash', year: cy + 1, drop: -0.3 }
    case 'income_loss': return { id, type, label: 'Income loss', person: 1, start_year: cy + 1, years: 1, pct: 100 }
    case 'extra_cost': return { id, type, label: 'Extra cost', name: 'Extra cost', amount: 25000, start_year: cy + 2, years: 5 }
    case 'inflation_spike': return { id, type, label: 'High inflation', start_year: cy + 1, years: 3, rate: 0.07 }
    default: return { id, type, label: 'Early death', person: 1, year: cy + 5, life_insurance: 0 }
  }
}

export default function Stress() {
  const { plan, names, single } = usePlan()
  const cy = plan.current_year
  const [tests, setTests] = useState<any[] | null>(null)
  const [off, setOff] = useState<Record<string, boolean>>({})
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [addType, setAddType] = useState('market_crash')

  const loadDefaults = async () => { const r = await api.stressDefaults(plan); setTests(r.tests); setRes(null) }
  useEffect(() => {
    try { const s = sessionStorage.getItem('fp_stress_tests'); if (s) { setTests(JSON.parse(s)); return } } catch { /* */ }
    loadDefaults()
  }, [])
  useEffect(() => { if (tests) try { sessionStorage.setItem('fp_stress_tests', JSON.stringify(tests)) } catch { /* */ } }, [tests])

  const run = async () => {
    if (!tests) return
    setBusy(true); setErr('')
    try { setRes(await api.stress(plan, tests.filter(t => !off[t.id]), 400)) } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  useEffect(() => { if (tests && !res) run() }, [tests])

  const upd = (id: string, patch: any) => { setTests(ts => ts!.map(t => (t.id === id ? { ...t, ...patch } : t))); }
  const people = [{ value: 1, label: names[0] }, ...(single ? [] : [{ value: 2, label: names[1] }, { value: 'both' as any, label: 'Both' }])]

  const chart = useMemo(() => {
    if (!res) return null
    const series = [{ key: 'base', label: 'Your plan' }, ...res.results.map((r: any) => ({ key: r.id, label: r.label }))]
    const data = res.base.years.map((y: number, i: number) => {
      const d: any = { year: y, base: res.base.investable[i] }
      res.results.forEach((r: any) => { d[r.id] = r.investable[i] })
      return d
    })
    return { series, data }
  }, [res])

  return (
    <div className="space-y-5">
      <PageHeader title="Stress tests" subtitle="What if something goes wrong? Each test re-runs the plan (and 400 market simulations) with one bad event"
        actions={<>
          <Button onClick={loadDefaults}><RotateCcw size={14} />Reset tests</Button>
          <Button variant="primary" onClick={run} disabled={busy}>{busy ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}Run tests</Button>
        </>} />
      {err && <Note tone="warn">{err}</Note>}

      {res && (
        <Card title="Results" subtitle="Today's dollars. Success = share of market simulations where savings never run out." pad={false}>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line">
              <th className="px-5 py-2 font-medium">Scenario</th><th className="font-medium text-right">Plan success</th><th className="font-medium text-right">Change</th>
              <th className="font-medium text-right">Savings run out</th><th className="font-medium text-right">Net worth at retirement</th><th className="font-medium text-right pr-5">Net worth at end</th></tr></thead>
            <tbody>
              <tr className="border-b border-line bg-sunken/40">
                <td className="px-5 py-2.5 font-medium">Your plan as is</td>
                <td className="text-right tnum font-medium">{pct(res.base.success_rate, 0)}</td><td />
                <td className="text-right">{res.base.depletion_year ?? <span className="text-good">Never</span>}</td>
                <td className="text-right tnum">{money(res.base.net_worth_at_retirement)}</td>
                <td className="text-right tnum pr-5">{money(res.base.net_worth_end)}</td>
              </tr>
              {res.results.map((r: any) => {
                const T = TYPES[r.test.type]
                return (
                  <tr key={r.id} className="border-b border-line last:border-0">
                    <td className="px-5 py-2.5"><span className="flex items-center gap-2">{T && <T.icon size={15} className="text-muted" />}{r.label}
                      {res.worst === r.id && <Badge tone="bad">Biggest risk</Badge>}</span></td>
                    <td className={clsx('text-right tnum font-medium', r.success_rate < 0.7 ? 'text-bad' : r.success_rate < 0.85 ? 'text-warn' : 'text-good')}>{pct(r.success_rate, 0)}</td>
                    <td className={clsx('text-right tnum', r.delta_success < -0.005 ? 'text-bad' : 'text-muted')}>{(r.delta_success * 100).toFixed(0)} pts</td>
                    <td className="text-right">{r.depletion_year ? <span className="text-bad">{r.depletion_year}</span> : <span className="text-good">Never</span>}</td>
                    <td className="text-right tnum">{money(r.net_worth_at_retirement)}</td>
                    <td className="text-right tnum pr-5">{money(r.net_worth_end)} <span className={clsx('text-[12px]', r.delta_end < 0 ? 'text-bad' : 'text-muted')}>{money(r.delta_end, { sign: true })}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      )}

      {chart && (
        <Card title="Savings under each scenario" subtitle="Expected path (no market randomness), today's dollars">
          <LinesChart data={chart.data} series={chart.series} height={300} />
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(tests || []).map(t => {
          const T = TYPES[t.type] || TYPES.market_crash
          return (
            <Card key={t.id} className={clsx(off[t.id] && 'opacity-55')}
              title={<span className="flex items-center gap-2"><T.icon size={16} className="text-accent" />{T.label}</span>}
              action={<>
                <Toggle checked={!off[t.id]} onChange={v => setOff({ ...off, [t.id]: !v })} />
                <button className="p-1 text-muted hover:text-bad" onClick={() => setTests(tests!.filter(x => x.id !== t.id))}><Trash2 size={14} /></button>
              </>}>
              <div className="space-y-3">
                <Lbl l="Name"><TextInput value={t.label} onChange={v => upd(t.id, { label: v })} /></Lbl>
                {t.type === 'market_crash' && <div className="grid grid-cols-2 gap-3">
                  <Lbl l="Year"><NumberInput value={t.year} onChange={v => upd(t.id, { year: v })} min={cy} /></Lbl>
                  <Lbl l="Portfolio drop"><Percent fraction value={t.drop} onChange={v => upd(t.id, { drop: -Math.abs(v) })} decimals={0} /></Lbl></div>}
                {t.type === 'income_loss' && <>
                  <div className="grid grid-cols-2 gap-3">
                    <Lbl l="Who"><Select value={t.person} options={people} onChange={v => upd(t.id, { person: v })} /></Lbl>
                    <Lbl l="Income lost"><Percent value={t.pct} onChange={v => upd(t.id, { pct: v })} decimals={0} /></Lbl></div>
                  <div className="grid grid-cols-2 gap-3">
                    <Lbl l="Starting"><NumberInput value={t.start_year} onChange={v => upd(t.id, { start_year: v })} min={cy} /></Lbl>
                    <Lbl l="For (years)"><NumberInput value={t.years} onChange={v => upd(t.id, { years: v })} min={1} max={40} /></Lbl></div></>}
                {t.type === 'extra_cost' && <>
                  <Lbl l="Cost per year (today's $)"><Money value={t.amount} onChange={v => upd(t.id, { amount: v })} /></Lbl>
                  <div className="grid grid-cols-2 gap-3">
                    <Lbl l="Starting"><NumberInput value={t.start_year} onChange={v => upd(t.id, { start_year: v })} min={cy} /></Lbl>
                    <Lbl l="For (years)"><NumberInput value={t.years} onChange={v => upd(t.id, { years: v })} min={1} max={60} /></Lbl></div></>}
                {t.type === 'inflation_spike' && <>
                  <Lbl l="Inflation rate"><Percent fraction value={t.rate} onChange={v => upd(t.id, { rate: v })} decimals={1} /></Lbl>
                  <div className="grid grid-cols-2 gap-3">
                    <Lbl l="Starting"><NumberInput value={t.start_year} onChange={v => upd(t.id, { start_year: v })} min={cy} /></Lbl>
                    <Lbl l="For (years)"><NumberInput value={t.years} onChange={v => upd(t.id, { years: v })} min={1} max={20} /></Lbl></div></>}
                {t.type === 'early_death' && <>
                  <div className="grid grid-cols-2 gap-3">
                    <Lbl l="Who"><Select value={t.person} options={people.filter(p => p.value !== 'both')} onChange={v => upd(t.id, { person: v })} /></Lbl>
                    <Lbl l="Year"><NumberInput value={t.year} onChange={v => upd(t.id, { year: v })} min={cy} /></Lbl></div>
                  <Lbl l="Life insurance payout"><Money value={t.life_insurance} onChange={v => upd(t.id, { life_insurance: v })} /></Lbl></>}
                <p className="text-[12px] text-muted">{T.blurb}</p>
              </div>
            </Card>
          )
        })}
        <Card title="Add a test">
          <div className="space-y-3">
            <Select value={addType} options={Object.entries(TYPES).map(([k, v]) => ({ value: k, label: v.label }))} onChange={setAddType} />
            <p className="text-[12.5px] text-muted">{TYPES[addType].blurb}</p>
            <Button onClick={() => setTests([...(tests || []), newTest(addType, cy)])}><Plus size={14} />Add</Button>
          </div>
        </Card>
      </div>
      <Note><span className="flex gap-2"><ShieldAlert size={15} className="shrink-0 mt-0.5" />Stress tests never change your saved plan. If one scenario hurts a lot, consider an emergency fund, disability or life insurance, or a lower withdrawal rate, then check the effect under Scenarios.</span></Note>
    </div>
  )
}

function Lbl({ l, children }: { l: string; children: React.ReactNode }) {
  return <label className="block"><span className="block text-[12.5px] font-medium text-ink2 mb-1.5">{l}</span>{children}</label>
}
