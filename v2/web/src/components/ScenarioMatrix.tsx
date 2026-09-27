import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Grid3x3, Loader2, Plus, ShieldCheck, AlertTriangle, XCircle, Info } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, clsx } from '../lib/format'
import { Card, Button, Segmented, Badge, Modal, NumberInput, TextInput, Toggle, Field, Select, Note } from './ui'
import { LinesChart } from './charts'
import { LocationPicker } from '../pages/Locations'
import { lifestyleOptions } from '../lib/spending'

const TARGETS = ['0.75', '0.8', '0.85', '0.9', '0.95'] as const
const CUR = 'Current plan'
const LS = 'fp_matrix'

type Econ = { id: string; label: string; desc: string }
type Row = { name: string; plan: any }

function loadPrefs(): { rows?: string[]; econs?: string[]; target?: string } {
  try { return JSON.parse(localStorage.getItem(LS) || '{}') } catch { return {} }
}

/** Every life scenario (current plan + saved scenarios) against every economic condition.
 *  Each cell is a Monte Carlo success rate; all cells use the same market paths. */
export function ScenarioMatrix({ saved, onSaved, onLoad }: { saved: Record<string, any>; onSaved: () => Promise<void> | void; onLoad: (name: string, plan: any) => void }) {
  const { plan } = usePlan()
  const prefs = useMemo(loadPrefs, [])
  const [econs, setEcons] = useState<Econ[]>([])
  const [selE, setSelE] = useState<string[]>(prefs.econs || [])
  const [selR, setSelR] = useState<string[]>(prefs.rows || [])
  const [target, setTarget] = useState<string>(prefs.target || '0.85')
  const [res, setRes] = useState<Record<string, any>>({})
  const [busy, setBusy] = useState<Record<string, boolean>>({})
  const [chartE, setChartE] = useState('plan')
  const [builder, setBuilder] = useState(false)
  const cache = useRef<Record<string, any>>({})

  useEffect(() => {
    api.economies().then(r => { setEcons(r.economies); setSelE(s => s.length ? s.filter(x => r.economies.some((e: Econ) => e.id === x)) : r.default) }).catch(() => {})
  }, [])
  const names = Object.keys(saved).filter(n => !n.startsWith('[DEMO]'))
  useEffect(() => { setSelR(s => s.filter(n => n in saved)) }, [JSON.stringify(names)])
  useEffect(() => { try { localStorage.setItem(LS, JSON.stringify({ rows: selR, econs: selE, target })) } catch { /* */ } }, [selR, selE, target])

  const rows: Row[] = [{ name: CUR, plan }, ...selR.filter(n => saved[n]).map(n => ({ name: n, plan: saved[n] }))]
  const econKey = selE.join(',')
  const planKey = JSON.stringify(plan)

  // evaluate each row (in parallel, cached by plan + economies + target)
  useEffect(() => {
    if (!selE.length) return
    let live = true
    const tm = setTimeout(() => {
      rows.forEach(r => {
        const key = `${JSON.stringify(r.plan)}|${econKey}|${target}`
        if (cache.current[key]) { setRes(x => ({ ...x, [r.name]: cache.current[key] })); return }
        setBusy(b => ({ ...b, [r.name]: true }))
        api.evaluateScenario(r.plan, selE, +target).then(out => {
          cache.current[key] = out
          if (live) setRes(x => ({ ...x, [r.name]: out }))
        }).catch(() => {}).finally(() => live && setBusy(b => ({ ...b, [r.name]: false })))
      })
    }, 700)
    return () => { live = false; clearTimeout(tm) }
  }, [planKey, selR.join('|'), econKey, target, JSON.stringify(selR.map(n => saved[n]))])

  const shownE = econs.filter(e => selE.includes(e.id))
  const done = rows.filter(r => res[r.name] && res[r.name].economies.join(',') === econKey && res[r.name].target === +target)
  const toggleR = (n: string) => setSelR(s => s.includes(n) ? s.filter(x => x !== n) : s.length < 9 ? [...s, n] : s)
  const toggleE = (id: string) => setSelE(s => s.includes(id) ? (s.length > 1 ? s.filter(x => x !== id) : s) : econs.map(e => e.id).filter(x => x === id || s.includes(x)))

  const tone = (s: number) => s >= +target ? 'bg-good/15 text-good' : s >= +target - 0.15 ? 'bg-warn/15 text-warn' : 'bg-bad/15 text-bad'
  const verdict = (v: string) => v === 'robust' ? <Badge tone="good"><ShieldCheck size={12} className="inline -mt-0.5 mr-0.5" />Holds up</Badge>
    : v === 'fragile' ? <Badge tone="warn"><AlertTriangle size={12} className="inline -mt-0.5 mr-0.5" />Fragile</Badge>
    : <Badge tone="bad"><XCircle size={12} className="inline -mt-0.5 mr-0.5" />Falls short</Badge>

  const chartEcon = selE.includes(chartE) ? chartE : selE[0]
  const chart = useMemo(() => {
    const years = new Set<number>()
    done.forEach(r => (res[r.name].cells[chartEcon]?.years || []).forEach((y: number) => years.add(y)))
    return [...years].sort().map(y => {
      const o: any = { year: y }
      done.forEach((r, i) => { const c = res[r.name].cells[chartEcon]; if (c) { const k = c.years.indexOf(y); if (k >= 0) o[`s${i}`] = c.median_path[k] } })
      return o
    })
  }, [JSON.stringify(done.map(r => r.name)), res, chartEcon])

  const summary = (() => {
    if (done.length < rows.length || !done.length) return null
    const score = (r: Row) => { const x = res[r.name]; return x.passed * 10 + Math.min(...x.economies.map((e: string) => x.cells[e].success)) }
    const best = [...done].sort((a, b) => score(b) - score(a))[0]
    const bx = res[best.name]
    const cur = res[CUR]
    const failsIn = (x: any) => x.economies.filter((e: string) => !x.cells[e].ok).map((e: string) => econs.find(z => z.id === e)?.label || e)
    const lines: string[] = []
    if (done.length > 1) lines.push(`Most resilient: ${best.name} (reaches ${pct(+target, 0)} in ${bx.passed} of ${bx.total} economies; worst case ${pct(bx.cells[bx.worst].success, 0)} in ${econs.find(z => z.id === bx.worst)?.label}).`)
    if (cur) lines.push(cur.verdict === 'robust' ? `Your current plan holds up in every economy tested.`
      : `Your current plan reaches ${pct(+target, 0)} in ${cur.passed} of ${cur.total}; it falls short in ${failsIn(cur).join(', ')}.`)
    return lines
  })()

  return (
    <Card title={<span className="flex items-center gap-2"><Grid3x3 size={16} className="text-accent" />Scenario matrix</span>}
      subtitle="Test several versions of your life (2 kids or 3, move or stay, retire at 55 or 60) against several economies at once. Each cell is the chance your money lasts; every cell uses the same simulated markets, so differences come from the plans."
      action={<Segmented value={target as any} onChange={v => setTarget(v)} options={TARGETS.map(t => ({ value: t, label: pct(+t, 0) }))} />}>
      <div className="space-y-3">
        <div>
          <div className="text-[12px] font-semibold uppercase tracking-wide text-muted mb-1.5">Life scenarios</div>
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="px-2.5 h-7 inline-flex items-center rounded-full text-[12.5px] bg-accent text-white">{CUR}</span>
            {names.map(n => <button key={n} onClick={() => toggleR(n)}
              className={clsx('px-2.5 h-7 rounded-full text-[12.5px] border', selR.includes(n) ? 'bg-accentSoft border-accent/40 text-accent' : 'border-line text-ink2 hover:bg-sunken')}>{n}</button>)}
            <Button size="sm" onClick={() => setBuilder(true)}><Plus size={13} />New life scenario</Button>
          </div>
          {names.length === 0 && <p className="text-[12.5px] text-muted mt-1">Save scenarios below, or use “New life scenario” to make one from your plan (more kids, a move, a different retirement age).</p>}
        </div>
        <div>
          <div className="text-[12px] font-semibold uppercase tracking-wide text-muted mb-1.5">Economies</div>
          <div className="flex flex-wrap gap-1.5">
            {econs.map(e => <button key={e.id} title={e.desc} onClick={() => toggleE(e.id)}
              className={clsx('px-2.5 h-7 rounded-full text-[12.5px] border', selE.includes(e.id) ? 'bg-accentSoft border-accent/40 text-accent' : 'border-line text-ink2 hover:bg-sunken')}>{e.label}</button>)}
          </div>
        </div>

        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-sm min-w-[640px]">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line">
              <th className="py-2 px-1 font-medium">Scenario</th>
              {shownE.map(e => <th key={e.id} className="font-medium text-center px-1 cursor-pointer" title={e.desc} onClick={() => setChartE(e.id)}>
                <span className={clsx(chartEcon === e.id && 'text-accent underline underline-offset-4')}>{e.label}</span></th>)}
              <th className="font-medium text-center px-1">Reaches {pct(+target, 0)}</th><th /></tr></thead>
            <tbody>{rows.map(r => {
              const x = res[r.name]
              const fresh = x && x.economies.join(',') === econKey && x.target === +target
              const f = x?.facts
              return (
                <tr key={r.name} className="border-b border-line last:border-0 align-middle">
                  <td className="py-2 px-1">
                    <div className="font-medium">{r.name}</div>
                    {f && <div className="text-[11.5px] text-muted">{f.kids} kid{f.kids === 1 ? '' : 's'} · {f.places.join(' → ')} · retire {f.retire.join('/')}</div>}
                  </td>
                  {shownE.map(e => {
                    const c = fresh ? x.cells[e.id] : null
                    return <td key={e.id} className="px-1 py-1.5 text-center">
                      {c ? <div className={clsx('rounded-md py-1.5 tnum font-semibold', tone(c.success))}
                        title={`${e.label}: ${pct(c.success, 1)} chance the money lasts\nMedian net worth at the end: ${money(c.final_median)} (today's $)\nLowest savings: ${money(c.lowest_savings)} in ${c.lowest_year}${c.depletion_year ? `\nAverage path runs out in ${c.depletion_year}` : ''}`}>
                        {pct(c.success, 0)}<div className="text-[10.5px] font-normal opacity-80">{money(c.final_median)}</div></div>
                        : <div className="h-11 rounded-md bg-sunken/60 flex items-center justify-center">{busy[r.name] ? <Loader2 size={14} className="animate-spin text-muted" /> : null}</div>}
                    </td>
                  })}
                  <td className="text-center px-1">{fresh ? <div className="space-y-1"><div className="tnum text-[12.5px]">{x.passed} of {x.total}</div>{verdict(x.verdict)}</div> : null}</td>
                  <td className="text-right px-1">{r.name !== CUR && <Button size="sm" variant="ghost" onClick={() => onLoad(r.name, r.plan)}>Load</Button>}</td>
                </tr>)
            })}</tbody>
          </table>
        </div>
        <p className="text-[12px] text-muted flex gap-1.5"><Info size={13} className="shrink-0 mt-0.5" />Green reaches the target, amber is within 15 points, red is further off. The small figure is the median net worth at the end, in today's dollars. Hover a cell for details; click an economy to chart it.</p>
        {summary && <Note>{summary.map((l, i) => <div key={i}>{l}</div>)}</Note>}
        {done.length > 0 && <div>
          <div className="text-[12.5px] font-semibold text-ink2 mb-1">Median net worth (today's $): {econs.find(e => e.id === chartEcon)?.label}</div>
          <LinesChart data={chart} series={done.map((r, i) => ({ key: `s${i}`, label: r.name }))} height={260} />
        </div>}
      </div>
      <VariantBuilder open={builder} onClose={() => setBuilder(false)} taken={names}
        onCreated={async n => { await onSaved(); setSelR(s => [...s.filter(x => x !== n), n].slice(-9)) }} />
    </Card>
  )
}

function VariantBuilder({ open, onClose, onCreated, taken }: { open: boolean; onClose: () => void; onCreated: (name: string) => Promise<void> | void; taken: string[] }) {
  const { plan, reference, names: people, single } = usePlan()
  const cy = plan.current_year
  const kidsNow = (plan.children_list || []).length
  const loc0 = plan.state_timeline?.[0]?.state || 'Seattle'
  const [name, setName] = useState('')
  const [kids, setKids] = useState<number>(kidsNow)
  const [kidYears, setKidYears] = useState('')
  const [doMove, setDoMove] = useState(false)
  const [move, setMove] = useState<{ location: string; year: number; lifestyle: string }>({ location: loc0, year: cy + 3, lifestyle: '' })
  const [rx, setRx] = useState<number>(plan.parentX_retirement_age)
  const [ry, setRy] = useState<number>(plan.parentY_retirement_age)
  const [life, setLife] = useState('')
  const [err, setErr] = useState('')
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    if (!open) return
    setName(''); setKids(kidsNow); setKidYears(''); setDoMove(false); setErr('')
    setMove({ location: loc0, year: cy + 3, lifestyle: '' }); setRx(plan.parentX_retirement_age); setRy(plan.parentY_retirement_age); setLife('')
  }, [open])

  const auto = () => {
    const bits: string[] = []
    if (kids !== kidsNow) bits.push(`${kids} kid${kids === 1 ? '' : 's'}`)
    if (doMove) bits.push(`move to ${move.location} ${move.year}`)
    if (rx !== plan.parentX_retirement_age || (!single && ry !== plan.parentY_retirement_age)) bits.push(`retire ${rx}${single ? '' : `/${ry}`}`)
    if (life) bits.push(life)
    return bits.join(', ') || 'Copy of current plan'
  }
  const create = async () => {
    const n = (name.trim() || auto()).slice(0, 80)
    if (taken.includes(n)) { setErr(`“${n}” already exists; pick another name.`); return }
    const changes: any = {}
    if (kids !== kidsNow) { changes.kids = kids; const ys = kidYears.split(/[,\s]+/).map(Number).filter(y => y > 1900); if (ys.length) changes.kid_years = ys }
    if (doMove) changes.move = { location: move.location, year: move.year, lifestyle: move.lifestyle || undefined }
    if (rx !== plan.parentX_retirement_age) changes.retire_x = rx
    if (!single && ry !== plan.parentY_retirement_age) changes.retire_y = ry
    if (life) changes.lifestyle = life
    setSaving(true)
    try {
      const r = await api.buildVariant(plan, changes)
      await api.saveScenario(n, r.plan)
      await onCreated(n)
      onClose()
    } catch (e: any) { setErr(e.message || 'Could not create the scenario') } finally { setSaving(false) }
  }
  const lifeChoices = lifestyleOptions(plan, loc0)

  return (
    <Modal open={open} onClose={onClose} title="New life scenario"
      footer={<><Button onClick={onClose}>Cancel</Button><Button variant="primary" onClick={create} disabled={saving}>{saving ? 'Saving…' : 'Create and compare'}</Button></>}>
      <div className="space-y-4 text-sm">
        <p className="text-ink2">Starts from your current plan and changes only what you set here. Your plan itself is not changed; the result is saved as a scenario everyone in the household can see.</p>
        <Field label="Name" hint="Leave empty for an automatic name"><TextInput value={name} onChange={setName} placeholder={auto()} /></Field>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label={`Children (now ${kidsNow})`}><NumberInput value={kids} min={0} max={10} step={1} onChange={v => setKids(Math.max(0, Math.min(10, Math.round(v))))} /></Field>
          {kids > kidsNow && <Field label="Birth years of the new children" hint={`e.g. ${cy + 1}, ${cy + 3}; empty = every 2 years from next year`}>
            <TextInput value={kidYears} onChange={setKidYears} placeholder={`${cy + 1}, ${cy + 3}`} /></Field>}
          {kids < kidsNow && <p className="text-[12.5px] text-muted self-end">The youngest {kidsNow - kids === 1 ? 'child is' : `${kidsNow - kids} children are`} left out.</p>}
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label={`${people[0]} retires at`}><NumberInput value={rx} min={plan.parentX_age} max={85} step={1} onChange={v => setRx(Math.round(v))} /></Field>
          {!single && <Field label={`${people[1]} retires at`}><NumberInput value={ry} min={plan.parentY_age} max={85} step={1} onChange={v => setRy(Math.round(v))} /></Field>}
        </div>
        <div className="rounded-lg border border-line p-3 space-y-3">
          <Toggle checked={doMove} onChange={setDoMove} label="Move somewhere" hint="Replaces any planned moves from that year on" />
          {doMove && <>
            <LocationPicker value={move.location} catalog={reference?.location_catalog} custom={plan.custom_locations || {}} onChange={v => setMove(m => ({ ...m, location: v }))} />
            <div className="grid sm:grid-cols-2 gap-3">
              <Field label="Year"><NumberInput value={move.year} min={cy} max={cy + 60} step={1} onChange={v => setMove(m => ({ ...m, year: Math.round(v) }))} /></Field>
              <Field label="Lifestyle there"><Select value={move.lifestyle} onChange={v => setMove(m => ({ ...m, lifestyle: v }))}
                options={[{ value: '', label: 'Same as before' }, ...lifestyleOptions(plan, move.location).map((o: string) => ({ value: o, label: o }))]} /></Field>
            </div>
          </>}
        </div>
        <Field label="Lifestyle for the whole plan"><Select value={life} onChange={setLife} options={[{ value: '', label: 'Keep as planned' }, ...lifeChoices.map((o: string) => ({ value: o, label: o }))]} /></Field>
        {err && <p className="text-bad text-[12.5px]">{err}</p>}
      </div>
    </Modal>
  )
}
