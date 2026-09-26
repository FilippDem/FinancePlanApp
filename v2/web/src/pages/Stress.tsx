import React, { useEffect, useMemo, useState } from 'react'
import {
  Play, Plus, Trash2, RotateCcw, ShieldAlert, TrendingDown, Briefcase, HeartHandshake, Flame, UserX, Loader2, Baby, Layers,
  CheckCircle2, XCircle, ChevronDown, ChevronRight,
} from 'lucide-react'
import { ResponsiveContainer, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, clsx } from '../lib/format'
import { Card, PageHeader, Button, NumberInput, Money, Select, TextInput, Badge, Note, Toggle, Segmented } from '../components/ui'
import { LinesChart, S } from '../components/charts'

const TYPES: Record<string, { label: string; icon: any; blurb: string }> = {
  market_crash: { label: 'Market crash', icon: TrendingDown, blurb: 'Your investments lose this share of their value in one year' },
  inflation_spike: { label: 'Hyperinflation', icon: Flame, blurb: 'Prices rise fast for several years; only part of it shows up in pay' },
  disabled_child: { label: 'Disabled child', icon: Baby, blurb: 'One parent stops working for good to care for the child (from birth, or now if already born)' },
  income_loss: { label: 'Unemployment / income loss', icon: Briefcase, blurb: 'Job loss, disability or a career break' },
  extra_cost: { label: 'Extra yearly cost', icon: HeartHandshake, blurb: 'Caring for a parent, long-term care, a big ongoing bill' },
  early_death: { label: 'Early death', icon: UserX, blurb: "Income, benefits and spending for one partner stop" },
  compound: { label: 'Compound', icon: Layers, blurb: 'Several bad events at once, starting the same year' },
}
const PCTS = ['10', '25', '50', '75', '90']
const VERDICT: Record<string, { tone: 'good' | 'warn' | 'bad'; text: string }> = {
  excellent: { tone: 'good', text: 'Excellent. Your plan is highly resilient to these stress scenarios.' },
  good: { tone: 'good', text: 'Good. Your plan handles most scenarios, but consider building more buffer.' },
  moderate: { tone: 'warn', text: 'Moderate risk. Your plan struggles with many of these scenarios. Consider saving more or spending less.' },
  high_risk: { tone: 'bad', text: 'High risk. Your plan is vulnerable to these scenarios. Significant adjustments are recommended.' },
}

function newTest(type: string, cy: number, kids: any[]): any {
  const id = `${type}_${Math.random().toString(36).slice(2, 7)}`
  switch (type) {
    case 'market_crash': return { id, type, label: 'Market crash', year: cy + 1, drop: -0.5, when: 'worst' }
    case 'income_loss': return { id, type, label: 'Unemployment', person: 1, start_year: cy + 1, years: 3, pct: 100, when: 'worst' }
    case 'extra_cost': return { id, type, label: 'Extra cost', name: 'Extra cost', amount: 25000, start_year: cy + 2, years: 5 }
    case 'inflation_spike': return { id, type, label: 'Hyperinflation', start_year: cy + 1, years: 5, rate: 0.15, wage_passthrough: 50, when: 'worst' }
    case 'disabled_child': return { id, type, label: `Disabled child${kids[0] ? `: ${kids[0].name}` : ''}`, child: kids[0]?.name, person: 2, extra_cost: 0, years_cost: 30 }
    case 'compound': return { id, type, label: 'Compound test', events: [], when: 'worst' }
    default: return { id, type, label: 'Early death', person: 1, year: cy + 5, life_insurance: 0 }
  }
}

function RangeField({ label, value, min, max, step = 1, onChange, fmt }: { label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void; fmt?: (v: number) => string }) {
  return (
    <label className="block">
      <span className="flex justify-between text-[12.5px] font-medium text-ink2 mb-1"><span>{label}</span><span className="tnum text-ink">{fmt ? fmt(value) : value}</span></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(+e.target.value)} className="w-full accent-[rgb(var(--accent))]" />
    </label>
  )
}
function Lbl({ l, children }: { l: string; children: React.ReactNode }) {
  return <label className="block"><span className="block text-[12.5px] font-medium text-ink2 mb-1.5">{l}</span>{children}</label>
}
const Light = ({ ok }: { ok: boolean }) => ok ? <CheckCircle2 size={17} className="text-good inline" /> : <XCircle size={17} className="text-bad inline" />

function Editor({ t, upd, cy, people, kids, nested }: { t: any; upd: (patch: any) => void; cy: number; people: any[]; kids: any[]; nested?: boolean }) {
  const worst = t.when === 'worst'
  const whenCtl = !nested && ['market_crash', 'inflation_spike', 'income_loss', 'extra_cost', 'compound'].includes(t.type) && (
    <Segmented value={worst ? 'worst' : 'year'} onChange={v => upd({ when: v === 'worst' ? 'worst' : undefined })}
      options={[{ value: 'worst', label: 'Worst possible year' }, { value: 'year', label: 'Pick the year' }]} />
  )
  const yearKey = t.type === 'market_crash' || t.type === 'early_death' ? 'year' : 'start_year'
  const yearField = (t.type !== 'disabled_child' && t.type !== 'compound') && (!worst || t.type === 'early_death') && !nested && (
    <Lbl l={t.type === 'market_crash' || t.type === 'early_death' ? 'Year' : 'Starting'}><NumberInput value={t[yearKey]} onChange={v => upd({ [yearKey]: v })} min={cy} /></Lbl>
  )
  return (
    <div className="space-y-3">
      {whenCtl}
      {t.type === 'market_crash' && <RangeField label="Portfolio loss" value={Math.round(-t.drop * 100)} min={10} max={90} step={5} fmt={v => `${v}%`} onChange={v => upd({ drop: -v / 100 })} />}
      {t.type === 'inflation_spike' && <>
        <RangeField label="Inflation rate" value={Math.round(t.rate * 100)} min={5} max={30} fmt={v => `${v}%`} onChange={v => upd({ rate: v / 100 })} />
        <RangeField label="Duration" value={t.years} min={2} max={10} fmt={v => `${v} years`} onChange={v => upd({ years: v })} />
        <RangeField label="Pay keeps up with" value={t.wage_passthrough ?? 50} min={0} max={100} step={10} fmt={v => `${v}% of the extra inflation`} onChange={v => upd({ wage_passthrough: v })} />
      </>}
      {t.type === 'income_loss' && <>
        <div className="grid grid-cols-2 gap-3">
          <Lbl l="Who"><Select value={t.person} options={people} onChange={v => upd({ person: v })} /></Lbl>
          <Lbl l="Income lost"><NumberInput value={t.pct} suffix="%" min={0} max={100} onChange={v => upd({ pct: v })} /></Lbl>
        </div>
        <RangeField label="Duration" value={t.years} min={1} max={10} fmt={v => `${v} year${v > 1 ? 's' : ''}`} onChange={v => upd({ years: v })} />
      </>}
      {t.type === 'disabled_child' && <>
        {kids.length === 0 ? <p className="text-sm text-muted">Add a child on the Kids page first.</p> : <>
          <div className="grid grid-cols-2 gap-3">
            <Lbl l="Child"><Select value={t.child || kids[0].name} options={kids.map(k => ({ value: k.name, label: `${k.name} (${k.birth_year})` }))} onChange={v => upd({ child: v })} /></Lbl>
            <Lbl l="Stops working"><Select value={t.person} options={people.filter(p => p.value !== 'both')} onChange={v => upd({ person: v })} /></Lbl>
          </div>
          <Lbl l="Extra care cost per year (today's $, optional)"><Money value={t.extra_cost} onChange={v => upd({ extra_cost: v })} /></Lbl>
        </>}
      </>}
      {t.type === 'extra_cost' && <>
        <Lbl l="Cost per year (today's $)"><Money value={t.amount} onChange={v => upd({ amount: v })} /></Lbl>
        <RangeField label="For" value={t.years} min={1} max={40} fmt={v => `${v} years`} onChange={v => upd({ years: v })} />
      </>}
      {t.type === 'early_death' && <>
        <Lbl l="Who"><Select value={t.person} options={people.filter(p => p.value !== 'both')} onChange={v => upd({ person: v })} /></Lbl>
        <Lbl l="Life insurance payout"><Money value={t.life_insurance} onChange={v => upd({ life_insurance: v })} /></Lbl>
      </>}
      {yearField}
    </div>
  )
}

export default function Stress() {
  const { plan, names, single } = usePlan()
  const cy = plan.current_year
  const kids: any[] = plan.children_list || []
  const [tests, setTests] = useState<any[] | null>(null)
  const [off, setOff] = useState<Record<string, boolean>>({})
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [addType, setAddType] = useState('market_crash')
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [combine, setCombine] = useState<string[]>([])

  const loadDefaults = async () => { const r = await api.stressDefaults(plan); setTests(r.tests); setOff({}); setRes(null) }
  useEffect(() => {
    try { const s = sessionStorage.getItem('fp_stress_tests_v2'); if (s) { setTests(JSON.parse(s)); return } } catch { /* */ }
    loadDefaults()
  }, [])
  useEffect(() => { if (tests) try { sessionStorage.setItem('fp_stress_tests_v2', JSON.stringify(tests)) } catch { /* */ } }, [tests])

  const run = async () => {
    if (!tests) return
    setBusy(true); setErr('')
    try { setRes(await api.stress(plan, tests.filter(t => !off[t.id]), 500)) } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  useEffect(() => { if (tests && !res) run() }, [tests])

  const upd = (id: string, patch: any) => setTests(ts => ts!.map(t => (t.id === id ? { ...t, ...patch } : t)))
  const people = [{ value: 1, label: names[0] }, ...(single ? [] : [{ value: 2, label: names[1] }, { value: 'both' as any, label: 'Both' }])]

  const makeCompound = () => {
    const evs = (tests || []).filter(t => combine.includes(t.id)).flatMap(t => (t.type === 'compound' ? t.events : [t]))
      .map(e => { const { id: _i, when: _w, group: _g, ...rest } = e; return rest })
    const label = 'Compound: ' + (tests || []).filter(t => combine.includes(t.id)).map(t => t.label.replace(/ at the worst time| for \d+ years?/g, '')).join(' + ')
    setTests([...(tests || []), { id: `compound_${Math.random().toString(36).slice(2, 7)}`, type: 'compound', label, events: evs, when: 'worst' }])
    setCombine([])
  }

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
  const v = res ? VERDICT[res.summary.verdict] : null

  return (
    <div className="space-y-5">
      <PageHeader title="Stress tests" subtitle="Test the plan against rare, severe events. Each test re-runs the plan with 500 market simulations; “worst possible year” searches every start year for the most damaging one."
        actions={<>
          <Button onClick={loadDefaults}><RotateCcw size={14} />Reset tests</Button>
          <Button variant="primary" onClick={run} disabled={busy}>{busy ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}Run tests</Button>
        </>} />
      {err && <Note tone="warn">{err}</Note>}

      {res && v && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card><div className="text-[12.5px] text-muted">Scenarios tested</div><div className="text-[26px] font-semibold tnum">{res.summary.total}</div><div className="text-[12px] text-muted">{res.results.length} tests × 5 market percentiles</div></Card>
          <Card><div className="text-[12.5px] text-muted">Scenarios passed</div><div className="text-[26px] font-semibold tnum">{res.summary.passed} / {res.summary.total}</div></Card>
          <Card><div className="text-[12.5px] text-muted">Overall success rate</div><div className={clsx('text-[26px] font-semibold tnum', v.tone === 'good' ? 'text-good' : v.tone === 'bad' ? 'text-bad' : 'text-warn')}>{pct(res.summary.rate, 0)}</div></Card>
          <Card><div className={clsx('text-sm font-medium', v.tone === 'good' ? 'text-good' : v.tone === 'bad' ? 'text-bad' : 'text-warn')}>{v.text}</div></Card>
        </div>
      )}

      {res && (
        <Card title="Stoplight" subtitle="✅ the plan survives, ❌ savings run out. Columns are market outcomes: the 10th percentile is a bad decade-long market, the 90th a great one. A column passes when fewer than that share of simulations fail." pad={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[860px]">
              <thead><tr className="text-left text-[12px] text-muted border-b border-line">
                <th className="px-5 py-2 font-medium">Event</th><th className="font-medium text-center">Worst year</th>
                {PCTS.map(q => <th key={q} className="font-medium text-center">{q}th</th>)}
                <th className="font-medium text-right">Success</th><th className="font-medium text-right">Change</th>
                <th className="font-medium text-right">Median end NW</th><th className="font-medium text-right pr-5">Run out (expected)</th></tr></thead>
              <tbody>
                <tr className="border-b border-line bg-sunken/40">
                  <td className="px-5 py-2.5 font-medium">Your plan as is</td><td />
                  {PCTS.map(q => <td key={q} className="text-center"><Light ok={res.base.stoplight[q]} /></td>)}
                  <td className="text-right tnum font-medium">{pct(res.base.success_rate, 0)}</td><td />
                  <td className="text-right tnum">{money(res.base.final_nw['50'])}</td>
                  <td className="text-right pr-5">{res.base.depletion_year ?? <span className="text-good">Never</span>}</td>
                </tr>
                {res.results.map((r: any) => {
                  const T = TYPES[r.test.type]
                  const isOpen = open[r.id]
                  return (
                    <React.Fragment key={r.id}>
                      <tr className="border-b border-line hover:bg-sunken/40 cursor-pointer" onClick={() => setOpen({ ...open, [r.id]: !isOpen })}>
                        <td className="px-5 py-2.5"><span className="flex items-center gap-2">{isOpen ? <ChevronDown size={14} className="text-muted" /> : <ChevronRight size={14} className="text-muted" />}
                          {T && <T.icon size={15} className="text-muted" />}{r.label}{res.worst === r.id && <Badge tone="bad">Biggest risk</Badge>}</span></td>
                        <td className="text-center tnum">{r.worst_year ?? '—'}</td>
                        {PCTS.map(q => <td key={q} className="text-center"><Light ok={r.stoplight[q]} /></td>)}
                        <td className={clsx('text-right tnum font-medium', r.success_rate < 0.7 ? 'text-bad' : r.success_rate < 0.85 ? 'text-warn' : 'text-good')}>{pct(r.success_rate, 0)}</td>
                        <td className={clsx('text-right tnum', r.delta_success < -0.005 ? 'text-bad' : 'text-muted')}>{(r.delta_success * 100).toFixed(0)} pts</td>
                        <td className="text-right tnum">{money(r.final_nw['50'])}</td>
                        <td className="text-right pr-5">{r.depletion_year ? <span className="text-bad">{r.depletion_year}</span> : <span className="text-good">Never</span>}</td>
                      </tr>
                      {isOpen && (
                        <tr className="border-b border-line bg-sunken/30"><td colSpan={11} className="px-5 py-4">
                          <div className="grid gap-5 md:grid-cols-[1fr_1.3fr]">
                            <div>
                              <div className="text-[12.5px] font-medium text-ink2 mb-1.5">By market outcome (today's $)</div>
                              <table className="w-full text-[13px]"><thead><tr className="text-muted text-left"><th className="font-medium py-1">Percentile</th><th className="font-medium">Status</th><th className="font-medium text-right">Final net worth</th></tr></thead>
                                <tbody>{PCTS.map(q => <tr key={q} className="border-t border-line"><td className="py-1">{q}th</td><td>{r.stoplight[q] ? 'Survives' : 'Runs out'}</td><td className="text-right tnum">{money(r.final_nw[q])}</td></tr>)}</tbody></table>
                              <div className="text-[12.5px] text-muted mt-2">Events applied: {r.events.map((e: any) => `${TYPES[e.type]?.label ?? e.type} ${e.year ?? e.start_year ?? ''}`).join(', ') || '—'}</div>
                            </div>
                            {r.search?.length > 1 && (
                              <div>
                                <div className="text-[12.5px] font-medium text-ink2 mb-1.5">Success rate by start year (the search)</div>
                                <ResponsiveContainer width="100%" height={150}>
                                  <ComposedChart data={r.search} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
                                    <CartesianGrid vertical={false} stroke="var(--grid)" />
                                    <XAxis dataKey="year" tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" />
                                    <YAxis domain={[0, 1]} tickFormatter={x => `${Math.round(x * 100)}%`} width={40} tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" />
                                    <Tooltip formatter={(x: any) => pct(x, 0)} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
                                    <ReferenceLine x={r.worst_year} stroke={S[7]} strokeDasharray="4 3" />
                                    <Line dataKey="success_rate" name="Success" stroke={S[0]} strokeWidth={2} dot={false} isAnimationActive={false} />
                                  </ComposedChart>
                                </ResponsiveContainer>
                              </div>
                            )}
                          </div>
                        </td></tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {chart && (
        <Card title="Savings under each scenario" subtitle="Expected path (no market randomness), today's dollars, at each test's worst year">
          <LinesChart data={chart.data} series={chart.series} height={300} />
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(tests || []).map(t => {
          const T = TYPES[t.type] || TYPES.market_crash
          return (
            <Card key={t.id} className={clsx(off[t.id] && 'opacity-55')}
              title={<span className="flex items-center gap-2"><input type="checkbox" title="Select to combine" className="accent-[rgb(var(--accent))]" checked={combine.includes(t.id)}
                onChange={e => setCombine(e.target.checked ? [...combine, t.id] : combine.filter(x => x !== t.id))} /><T.icon size={16} className="text-accent" />{T.label}</span>}
              action={<>
                <Toggle checked={!off[t.id]} onChange={v => setOff({ ...off, [t.id]: !v })} />
                <button className="p-1 text-muted hover:text-bad" onClick={() => setTests(tests!.filter(x => x.id !== t.id))}><Trash2 size={14} /></button>
              </>}>
              <div className="space-y-3">
                <Lbl l="Name"><TextInput value={t.label} onChange={v => upd(t.id, { label: v })} /></Lbl>
                {t.type === 'compound' ? <>
                  <Editor t={t} upd={p => upd(t.id, p)} cy={cy} people={people} kids={kids} />
                  <div className="text-[12.5px] font-medium text-ink2">Events (all start in the same year)</div>
                  {t.events.map((e: any, i: number) => (
                    <div key={i} className="rounded-lg border border-line p-3">
                      <div className="flex items-center justify-between text-sm font-medium mb-2">{TYPES[e.type]?.label}
                        <button className="text-muted hover:text-bad" onClick={() => upd(t.id, { events: t.events.filter((_: any, j: number) => j !== i) })}><Trash2 size={13} /></button></div>
                      <Editor t={e} nested upd={p => upd(t.id, { events: t.events.map((x: any, j: number) => (j === i ? { ...x, ...p } : x)) })} cy={cy} people={people} kids={kids} />
                    </div>
                  ))}
                  {t.events.length < 2 && <p className="text-[12.5px] text-warn">Add at least two events: tick two or more test cards and press “Combine selected”.</p>}
                </> : <Editor t={t} upd={p => upd(t.id, p)} cy={cy} people={people} kids={kids} />}
                <p className="text-[12px] text-muted">{T.blurb}</p>
              </div>
            </Card>
          )
        })}
        <Card title="Add a test">
          <div className="space-y-3">
            <Select value={addType} options={Object.entries(TYPES).map(([k, x]) => ({ value: k, label: x.label }))} onChange={setAddType} />
            <p className="text-[12.5px] text-muted">{TYPES[addType].blurb}</p>
            <Button onClick={() => setTests([...(tests || []), newTest(addType, cy, kids)])}><Plus size={14} />Add</Button>
          </div>
          <div className="border-t border-line mt-4 pt-4 space-y-2">
            <div className="text-sm font-medium flex items-center gap-2"><Layers size={15} className="text-accent" />Compound test</div>
            <p className="text-[12.5px] text-muted">Tick two or more test cards, then combine them into one scenario where everything happens together (at the worst possible year).</p>
            <Button disabled={combine.length < 2} onClick={makeCompound}>Combine selected ({combine.length})</Button>
          </div>
        </Card>
      </div>
      <Note><span className="flex gap-2"><ShieldAlert size={15} className="shrink-0 mt-0.5" />Stress tests never change your saved plan. If a scenario hurts a lot, consider an emergency fund, disability or life insurance, or a lower withdrawal rate, then check the effect under Scenarios.</span></Note>
    </div>
  )
}
