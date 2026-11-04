/** Decision playground: stack what-if decisions as chips, drag their markers on the projection, and see what each one
 *  does to retirement, success odds, taxes and money left. Modelled on FinP4l's what-if scenarios. Decisions live in
 *  plan.whatifs and only change the plan when you choose "Make it part of my plan". */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, MoreHorizontal, Search, X, GripVertical, Undo2, Save, Wand2, Power, Pencil, Copy, Trash2, CheckCircle2, Sparkles, Layers } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { clsx, money, pct } from '../lib/format'
import { ageAt } from '../lib/lifeEdit'
import {
  CATALOG, CATS, DEF, LENSES, applyAll, asScenario, bake, canBake, clampWhatIf, colorFor, create, ctxFor, fiYear, markers as mkMarkers,
  moveMarker, whenText, amountText, type Cat, type Lens, type WhatIf,
} from '../lib/whatifs'
import { DecisionChart, type ChartHandle, type FixedMarker } from './DecisionChart'
import { Button, Drawer, Field, Money, NumberInput, Segmented, Select, TextInput, Toggle, Modal, Note } from './ui'
import { LocationPicker } from '../pages/Locations'

const RETIRE_ID = '__retire'
const strip = (p: any) => { const { whatifs, whatif_lens, ...rest } = p; return rest }

export function DecisionPlayground() {
  const { plan, update, reference, single, names } = usePlan()
  const nav = useNavigate()
  const list: WhatIf[] = plan.whatifs || []
  const lens: Lens = plan.whatif_lens || 'likely'
  const c = useMemo(() => ctxFor(plan), [plan])
  const [today, setToday] = useState(true)
  const [showBase, setShowBase] = useState(true)
  const [preview, setPreview] = useState<WhatIf[] | null>(null)
  const eff = preview ?? list
  const [msg, setMsg] = useState('')
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 3500) }

  // ── edits (with undo) ──
  const undo = useRef<WhatIf[][]>([])
  const setList = useCallback((fn: (l: WhatIf[]) => WhatIf[]) => {
    undo.current.push(list)
    if (undo.current.length > 50) undo.current.shift()
    update(d => { d.whatifs = fn(d.whatifs || []).map((w: WhatIf) => clampWhatIf(d, w)) })
  }, [list, update])
  const doUndo = () => { const prev = undo.current.pop(); if (prev) update(d => { d.whatifs = prev }) }
  const setLens = (l: Lens) => update(d => { d.whatif_lens = l })

  // ── projections: plan (with the market lens), plan + decisions, and each decision's own effect ──
  const baseKey = useMemo(() => JSON.stringify(strip(plan)) + lens, [plan, lens])
  const [base, setBase] = useState<any>(null)
  const [scen, setScen] = useState<any>(null)
  const [mcs, setMcs] = useState<{ base: number; scen: number } | null>(null)
  const [impact, setImpact] = useState<Record<string, number>>({})
  const [busy, setBusy] = useState(false)
  const seqB = useRef(0), seqS = useRef(0), seqM = useRef(0), seqI = useRef(0)

  useEffect(() => {
    const s = ++seqB.current
    const t = setTimeout(async () => { try { const r = await api.project(applyAll(strip(plan), [], lens)); if (s === seqB.current) setBase(r) } catch { /* */ } }, 120)
    return () => clearTimeout(t)
  }, [baseKey])
  const effKey = baseKey + JSON.stringify(eff)
  useEffect(() => {
    const s = ++seqS.current
    setBusy(true)
    const t = setTimeout(async () => {
      try { const r = await api.project(applyAll(plan, eff, lens)); if (s === seqS.current) setScen(r) }
      catch { /* */ } finally { if (s === seqS.current) setBusy(false) }
    }, preview ? 40 : 120)
    return () => clearTimeout(t)
  }, [effKey])
  const listKey = baseKey + JSON.stringify(list)
  useEffect(() => {
    if (preview) return
    const s = ++seqM.current
    const t = setTimeout(async () => {
      try {
        const [a, b] = await Promise.all([api.monteCarlo(applyAll(strip(plan), [], lens), 400, true), api.monteCarlo(applyAll(plan, list, lens), 400, true)])
        if (s === seqM.current) setMcs({ base: a.success_rate, scen: b.success_rate })
      } catch { /* */ }
    }, 650)
    return () => clearTimeout(t)
  }, [listKey, !!preview])
  useEffect(() => {
    if (preview) return
    const s = ++seqI.current
    const on = list.filter(w => w.on)
    if (!on.length) { setImpact({}); return }
    const t = setTimeout(async () => {
      try {
        const endNW = (r: any) => { const l = r.rows[r.rows.length - 1]; return l.net_worth / l.infl_index }
        const all = await api.project(applyAll(plan, list, lens))
        const res = await Promise.all(on.map(w => api.project(applyAll(plan, list, lens, w.id))))
        if (s === seqI.current) setImpact(Object.fromEntries(on.map((w, i) => [w.id, endNW(all) - endNW(res[i])])))
      } catch { /* */ }
    }, 800)
    return () => clearTimeout(t)
  }, [listKey, !!preview])

  // ── numbers ──
  const applied = useMemo(() => applyAll(plan, eff, lens), [plan, eff, lens])
  const appliedBase = useMemo(() => applyAll(strip(plan), [], lens), [plan, lens])
  const rows = scen?.rows || []
  const baseRows = base?.rows || null
  const onCount = list.filter(w => w.on).length
  const ageOf = useCallback((y: number) => `age ${ageAt(plan, 'X', y)}${single ? '' : `/${ageAt(plan, 'Y', y)}`}`, [plan, single])
  const retireYear = (p: any) => Math.min(p.current_year + p.parentX_retirement_age - p.parentX_age, single ? 9999 : p.current_year + p.parentY_retirement_age - p.parentY_age)
  const k = useMemo(() => {
    if (!scen || !base) return null
    const end = (r: any) => { const l = r.rows[r.rows.length - 1]; return today ? l.net_worth / l.infl_index : l.net_worth }
    const fiS = fiYear(scen.rows), fiB = fiYear(base.rows)
    return {
      retS: retireYear(applied), retB: retireYear(appliedBase),
      fiS, fiB,
      taxS: scen.summary.lifetime_taxes, taxB: base.summary.lifetime_taxes,
      endS: end(scen), endB: end(base),
      depS: scen.summary.depletion_year, depB: base.summary.depletion_year,
    }
  }, [scen, base, applied, appliedBase, today])

  // ── markers ──
  // retirement decisions are shown (and dragged) through the purple Retire flag, so they get no flag of their own
  const isRetire = (w: WhatIf) => w.key === 'retire_earlier' || w.key === 'work_longer'
  const mk = useMemo(() => mkMarkers(plan, eff).filter(m => !isRetire(eff.find(w => w.id === m.wid)!)), [plan, eff])
  const fixed: FixedMarker[] = useMemo(() => {
    const out: FixedMarker[] = []
    const ry = retireYear(applied)
    out.push({ id: RETIRE_ID, year: ry, label: single ? 'Retire' : 'First retirement', emoji: '🏁', color: '#7c3aed', draggable: true, min: c.cy, max: c.last })
    const fi = fiYear(rows)
    if (fi) out.push({ id: '__fi', year: fi, label: 'Work optional', emoji: '✨', color: '#059669' })
    const dep = scen?.summary?.depletion_year
    if (dep) out.push({ id: '__dep', year: dep, label: 'Savings run out', emoji: '⛔', color: '#dc2626' })
    return out
  }, [applied, rows, scen, c, single])

  /** The list with retirement moved to `year` (a "Retire earlier"/"Work longer" decision, created or updated). */
  const withRetire = (l: WhatIf[], year: number): WhatIf[] => {
    const cur = l.find(w => (w.key === 'retire_earlier' || w.key === 'work_longer'))
    const rest = l.filter(w => w !== cur)
    if (year === c.retYear) return rest
    const key = year < c.retYear ? 'retire_earlier' : 'work_longer'
    const w = cur ? { ...cur, key, on: true, start: year, person: cur.person || 'both' } : { ...create(plan, key, year), person: 'both' as const }
    return [...rest, w]
  }
  const moveTo = (l: WhatIf[], id: string, year: number) => {
    if (id === RETIRE_ID) return withRetire(l, year)
    const m = mkMarkers(plan, l).find(x => x.id === id)
    return m ? moveMarker(l, m, year, m.edge === 'start') : l
  }
  const onMove = (id: string, year: number) => setPreview(moveTo(list, id, year))
  const onDrop = (id: string, year: number) => { setPreview(null); setList(l => moveTo(l, id, year)) }

  // ── chip actions ──
  const [editing, setEditing] = useState<string | null>(null)
  const [menu, setMenu] = useState<string | null>(null)
  const [catalog, setCatalog] = useState(false)
  const [saveName, setSaveName] = useState<string | null>(null)
  const toggle = (id: string) => setList(l => l.map(w => (w.id === id ? { ...w, on: !w.on } : w)))
  const remove = (id: string) => { setList(l => l.filter(w => w.id !== id)); setEditing(null) }
  const dup = (id: string) => setList(l => { const w = l.find(x => x.id === id)!; return [...l, { ...w, id: create(plan, w.key).id, name: `${w.name || DEF[w.key].label} (copy)` }] })
  const add = (key: string, at?: number) => {
    const w = create(plan, key, at)
    setList(l => [...l, w])
    flash(`Added “${DEF[key].label}”${DEF[key].timing !== 'none' ? ' — drag its flag on the chart to change when' : ''}`)
    return w
  }
  const makePermanent = (w: WhatIf) => {
    update(d => bake(d, w))
    setEditing(null)
    flash(`“${w.name || DEF[w.key].label}” is now part of your plan. Find it on the Life timeline or its own page.`)
  }
  const allOn = list.length > 0 && list.every(w => w.on)

  // find earliest retirement that never runs out of money (with every decision that's on)
  const [finding, setFinding] = useState(false)
  const findEarliest = async () => {
    setFinding(true)
    try {
      // works = money never runs out from retirement on (a dip before retiring, e.g. a down payment, is a separate problem)
      const ok = async (y: number) => { const r = await api.project(applyAll(plan, withRetire(list, y), lens)); return !r.rows.some((x: any) => x.year >= y && x.investable < 0) }
      let lo = c.cy, hi = Math.min(c.last, c.retYear + 12)
      if (!(await ok(hi))) { flash('Even working 12 more years the money runs out with these decisions. Try turning some off.'); return }
      while (lo < hi) { const mid = Math.floor((lo + hi) / 2); if (await ok(mid)) hi = mid; else lo = mid + 1 }
      setList(l => withRetire(l, lo))
      flash(lo < c.retYear ? `You could retire in ${lo} (${ageOf(lo)}), ${c.retYear - lo} years earlier, without running out.` : lo === c.retYear ? 'Your planned retirement year is already the earliest that works.' : `You'd need to work until ${lo} (${ageOf(lo)}).`)
    } finally { setFinding(false) }
  }

  // ── drag a new decision from the palette onto the chart ──
  const chart = useRef<ChartHandle>(null)
  const [ghost, setGhost] = useState<{ key: string; x: number; y: number; year: number | null } | null>(null)
  const ghostRef = useRef(ghost); ghostRef.current = ghost
  const beginPalette = (e: React.PointerEvent, key: string, onClick: () => void) => {
    if (e.button !== 0) return
    e.preventDefault()
    const sx = e.clientX, sy = e.clientY
    let dragging = false
    const move = (ev: PointerEvent) => {
      if (!dragging && Math.hypot(ev.clientX - sx, ev.clientY - sy) > 6) { dragging = true; setCatalog(false) }
      if (dragging) setGhost({ key, x: ev.clientX, y: ev.clientY, year: chart.current?.yearAt(ev.clientX, ev.clientY) ?? null })
    }
    const up = (ev: PointerEvent) => {
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up)
      if (!dragging) { onClick(); return }
      const yr = chart.current?.yearAt(ev.clientX, ev.clientY) ?? null
      setGhost(null)
      if (yr != null && !DEF[key].available?.(plan, c)) add(key, yr)
    }
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', up)
  }

  const quick = CATALOG.filter(d => d.quick && !d.available?.(plan, c))
  const editW = list.find(w => w.id === editing) || null
  const chips = [...list.filter(w => DEF[w.key]?.cat !== 'stress'), ...list.filter(w => DEF[w.key]?.cat === 'stress')]
  const firstStress = chips.findIndex(w => DEF[w.key]?.cat === 'stress')

  return (
    <div className="space-y-4">
      {/* question pills: click to add, or drag onto the chart */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {quick.map(d => (
          <button key={d.key} onPointerDown={e => beginPalette(e, d.key, () => add(d.key))} title="Click to add, or drag onto the chart"
            className="shrink-0 inline-flex items-center gap-2 h-10 pl-2 pr-3.5 rounded-xl border border-line bg-surface shadow-card text-[13.5px] font-medium text-ink hover:border-accent/50 hover:bg-accentSoft/40 cursor-grab active:cursor-grabbing touch-none">
            <span className="w-7 h-7 rounded-lg bg-accentSoft flex items-center justify-center text-[15px]">{d.emoji}</span>{d.quick}
          </button>))}
      </div>

      <section className="bg-surface rounded-xl border border-line shadow-card">
        <header className="flex flex-wrap items-center gap-3 px-5 pt-4">
          <h3 className="text-[16px] font-semibold flex items-center gap-2"><Sparkles size={17} className="text-accent" />What-if decisions</h3>
          <span className="text-[12.5px] text-muted">{onCount ? `${onCount} on · stacked on your plan` : 'Nothing on: showing your plan'}</span>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <Segmented value={today ? 'today' : 'future'} onChange={v => setToday(v === 'today')} options={[{ value: 'today', label: "Today's $" }, { value: 'future', label: 'Future $' }]} />
          </div>
        </header>

        {/* chips */}
        <div className="flex flex-wrap items-center gap-2 px-5 pt-3">
          {chips.map((w, i) => {
            const def = DEF[w.key]; if (!def) return null
            const col = colorFor(list, w.id)
            const imp = impact[w.id]
            const unavailable = def.available?.(plan, c)
            return (
              <React.Fragment key={w.id}>
                {i === firstStress && <span className="text-[11px] font-bold tracking-wider text-bad bg-bad/10 rounded-md px-2 h-6 inline-flex items-center">STRESS TEST</span>}
                <div className={clsx('relative inline-flex items-center rounded-full border transition-colors', w.on ? 'text-white border-transparent shadow-sm' : 'bg-sunken text-ink2 border-line')}
                  style={w.on ? { background: col } : undefined}>
                  <button onClick={() => toggle(w.id)} onDoubleClick={() => setEditing(w.id)} title={`${def.desc}\n${whenText(plan, w)}\nClick to turn ${w.on ? 'off' : 'on'}; double-click to edit`}
                    className="inline-flex items-center gap-1.5 h-8 pl-2.5 pr-1.5 text-[13px] font-medium">
                    <span className={clsx('w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center', w.on ? 'border-white' : 'border-muted')}>
                      {w.on && <span className="w-1.5 h-1.5 rounded-full bg-white" />}</span>
                    <span>{def.emoji}</span><span className={clsx(unavailable && 'line-through')}>{w.name || def.label}</span>
                    {w.on && imp != null && Math.abs(imp) >= 500 && <span className="ml-1 rounded-full bg-white/20 px-1.5 text-[11.5px] tnum" title="What this one decision changes in money left at the end (today's $)">{money(imp, { sign: true })}</span>}
                  </button>
                  <button onClick={() => setMenu(menu === w.id ? null : w.id)} className={clsx('h-8 pr-2 pl-1 rounded-r-full', w.on ? 'hover:bg-white/15' : 'hover:bg-line/60')} aria-label={`Options for ${w.name || def.label}`}>
                    <MoreHorizontal size={15} /></button>
                  {menu === w.id && <>
                    <div className="fixed inset-0 z-30" onClick={() => setMenu(null)} />
                    <div className="absolute left-0 top-9 z-40 w-60 rounded-xl border border-line bg-surface text-ink shadow-2xl p-1 text-[13.5px]">
                      <MenuItem icon={Pencil} onClick={() => { setEditing(w.id); setMenu(null) }}>Edit details…</MenuItem>
                      <MenuItem icon={Power} onClick={() => { toggle(w.id); setMenu(null) }}>{w.on ? 'Turn off' : 'Turn on'}</MenuItem>
                      <MenuItem icon={Copy} onClick={() => { dup(w.id); setMenu(null) }}>Duplicate</MenuItem>
                      <MenuItem icon={CheckCircle2} disabled={!canBake(plan, w)} onClick={() => { makePermanent(w); setMenu(null) }}
                        title={canBake(plan, w) ? 'Write it into your plan for good' : 'This is a what-if only (a market event or a change to pay) — it stays here'}>Make it part of my plan</MenuItem>
                      <MenuItem icon={Trash2} danger onClick={() => { remove(w.id); setMenu(null) }}>Remove</MenuItem>
                    </div></>}
                </div>
              </React.Fragment>)
          })}
          <button onClick={() => setCatalog(true)} className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full border-2 border-dashed border-line text-[13px] font-medium text-ink2 hover:border-accent hover:text-accent">
            <Plus size={15} />Add what-if</button>
          {list.length > 0 && <button onClick={() => setList(l => l.map(w => ({ ...w, on: !allOn })))} className="h-8 px-2.5 rounded-full text-[12.5px] text-muted hover:bg-sunken" title="Turn every decision on or off">
            {allOn ? 'All off' : 'All on'}</button>}
          {undo.current.length > 0 && <button onClick={doUndo} className="h-8 px-2.5 rounded-full text-[12.5px] text-muted hover:bg-sunken inline-flex items-center gap-1"><Undo2 size={13} />Undo</button>}
        </div>
        {msg && <div className="px-5 pt-3"><Note>{msg}</Note></div>}

        {/* controls row */}
        <div className="flex flex-wrap items-center gap-2 px-5 pt-3">
          <button onClick={findEarliest} disabled={finding} className={clsx('inline-flex items-center gap-1.5 h-8 px-3 rounded-full text-[13px] font-medium border', 'border-accent/40 text-accent bg-accentSoft/60 hover:bg-accentSoft', finding && 'opacity-60')}>
            <Wand2 size={14} />{finding ? 'Searching…' : 'Find earliest retirement'}</button>
          <div className="inline-flex p-0.5 rounded-full bg-sunken border border-line" title="How markets behave in both lines">
            {LENSES.map(l => <button key={l.value} title={l.hint} onClick={() => setLens(l.value)}
              className={clsx('h-7 px-2.5 sm:px-3 rounded-full text-[12px] sm:text-[12.5px] font-medium whitespace-nowrap', lens === l.value ? 'bg-accent text-white shadow-sm' : 'text-ink2 hover:text-ink')}>{l.label}</button>)}
          </div>
          <Toggle checked={showBase} onChange={setShowBase} label="Show my plan" />
          <div className="ml-auto flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => nav('/scenarios')}><Layers size={14} />Saved scenarios</Button>
            <Button size="sm" onClick={() => setSaveName(`What-if ${new Date().toLocaleDateString()}`)} disabled={!onCount}><Save size={14} />Save as scenario</Button>
          </div>
        </div>

        {/* chart */}
        <div className={clsx('px-3 sm:px-5 pt-3 pb-2 transition-opacity', busy && 'opacity-80')}>
          {rows.length ? <DecisionChart ref={chart} rows={rows} baseRows={onCount || lens !== 'likely' ? baseRows : null} today={today} ageOf={ageOf}
            markers={mk} fixed={fixed} ghostYear={ghost?.year ?? null} ghostColor={ghost ? '#2563eb' : undefined} showBase={showBase && onCount > 0}
            onMove={onMove} onDrop={onDrop} onFlagClick={id => { if (id === RETIRE_ID) { const r = list.find(isRetire); if (r) setEditing(r.id); return } const w = mk.find(m => m.id === id); if (w) setEditing(w.wid) }} />
            : <div className="h-[420px] flex items-center justify-center text-muted text-sm">Calculating…</div>}
        </div>

        {/* KPI strip */}
        {k && <div className="grid grid-cols-2 md:grid-cols-5 border-t border-line">
          <Kpi label="Retire" value={ageOf(k.retS)} sub={String(k.retS)} delta={k.retS - k.retB} unit="yr" goodWhen="down" show={onCount > 0} />
          <Kpi label="Work optional" value={k.fiS ? ageOf(k.fiS) : 'Not reached'} sub={k.fiS ? `${k.fiS} · 25× spending saved` : 'savings never cover 25× spending'}
            delta={k.fiS && k.fiB ? k.fiS - k.fiB : null} unit="yr" goodWhen="down" show={onCount > 0} />
          <Kpi label="Chance of success" value={mcs ? pct(mcs.scen, 0) : '…'} sub="400 Monte Carlo runs" delta={mcs ? (mcs.scen - mcs.base) * 100 : null} unit="pts" goodWhen="up" show={onCount > 0} />
          <Kpi label="Lifetime taxes" value={money(k.taxS)} sub="today's $" delta={k.taxS - k.taxB} unit="$" goodWhen="down" show={onCount > 0} />
          <Kpi label="Money left at the end" value={money(k.endS)} sub={k.depS ? `runs out ${k.depS} (${ageOf(k.depS)})` : 'never runs out'} tone={k.depS ? 'bad' : undefined}
            delta={k.endS - k.endB} unit="$" goodWhen="up" show={onCount > 0} />
        </div>}
        {k && <PlanInWords k={k} onCount={onCount} list={list} impact={impact} ageOf={ageOf} />}
      </section>

      {/* catalog */}
      {catalog && <Catalog plan={plan} onClose={() => setCatalog(false)} onAdd={key => { add(key); setCatalog(false) }} onDragStart={beginPalette} />}

      {/* editor */}
      <Drawer open={!!editW} onClose={() => setEditing(null)} title={editW ? `${DEF[editW.key].emoji} ${editW.name || DEF[editW.key].label}` : ''}
        footer={editW && <>
          <Button variant="danger" onClick={() => remove(editW.id)}><Trash2 size={14} />Remove</Button>
          <div className="flex-1" />
          {canBake(plan, editW) && <Button onClick={() => makePermanent(editW)}><CheckCircle2 size={14} />Make it part of my plan</Button>}
          <Button variant="primary" onClick={() => setEditing(null)}>Done</Button></>}>
        {editW && <Editor w={editW} plan={plan} reference={reference} single={single} names={names} ageOf={ageOf}
          onChange={nw => setList(l => l.map(x => (x.id === nw.id ? nw : x)))} />}
      </Drawer>

      <Modal open={saveName != null} onClose={() => setSaveName(null)} title="Save these decisions as a scenario"
        footer={<><Button onClick={() => setSaveName(null)}>Cancel</Button>
          <Button variant="primary" onClick={async () => { const nm = (saveName || '').trim() || 'What-if'; await api.saveScenario(nm, asScenario(plan)); setSaveName(null); flash(`Saved “${nm}” — compare it on the Scenarios page.`) }}>Save</Button></>}>
        <TextInput value={saveName || ''} onChange={setSaveName} autoFocus />
        <p className="text-[13px] text-muted">A copy of your plan with every decision that's on. Life changes (homes, kids, moves, costs…) are written in, so the
          Scenarios page, the scenario matrix and reports see them; market and pay events stay as what-ifs in the copy. Your plan itself doesn't change.</p>
      </Modal>

      {/* palette ghost */}
      {ghost && <div className="fixed z-50 pointer-events-none -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent text-white text-[13px] font-semibold px-3 h-8 inline-flex items-center gap-1.5 shadow-xl"
        style={{ left: ghost.x, top: ghost.y }}>{DEF[ghost.key].emoji} {DEF[ghost.key].label}{ghost.year != null ? ` · ${ghost.year}` : ' · drop on the chart'}</div>}
    </div>
  )
}

function MenuItem({ icon: Icon, children, onClick, disabled, danger, title }: { icon: any; children: React.ReactNode; onClick: () => void; disabled?: boolean; danger?: boolean; title?: string }) {
  return <button title={title} disabled={disabled} onClick={onClick}
    className={clsx('w-full flex items-center gap-2 px-2.5 h-8 rounded-lg text-left', disabled ? 'opacity-45 cursor-not-allowed' : danger ? 'text-bad hover:bg-bad/10' : 'hover:bg-sunken')}>
    <Icon size={14} />{children}</button>
}

function Kpi({ label, value, sub, delta, unit, goodWhen, show, tone }:
  { label: string; value: string; sub: string; delta: number | null; unit: 'yr' | '$' | 'pts'; goodWhen: 'up' | 'down'; show: boolean; tone?: 'bad' }) {
  const d = delta ?? 0
  const sig = unit === '$' ? Math.abs(d) >= 1000 : unit === 'pts' ? Math.abs(d) >= 1 : d !== 0
  const good = goodWhen === 'up' ? d > 0 : d < 0
  const txt = unit === '$' ? money(d, { sign: true }) : unit === 'pts' ? `${d > 0 ? '+' : '−'}${Math.abs(d).toFixed(0)} pts` : `${d > 0 ? '+' : '−'}${Math.abs(d)} yr`
  return (
    <div className="px-5 py-4 border-line [&:not(:last-child)]:border-r text-center">
      <div className="text-[12.5px] text-muted font-medium">{label}</div>
      <div className={clsx('text-[22px] font-semibold tnum leading-tight mt-0.5', tone === 'bad' && 'text-bad')}>{value}</div>
      <div className="text-[12px] text-muted mt-0.5">{sub}</div>
      {show && delta != null && <div className={clsx('text-[12.5px] font-semibold mt-1 tnum', !sig ? 'text-muted' : good ? 'text-good' : 'text-bad')}>
        {sig ? `${txt} vs plan` : 'same as plan'}</div>}
    </div>)
}

function PlanInWords({ k, onCount, list, impact, ageOf }: { k: any; onCount: number; list: WhatIf[]; impact: Record<string, number>; ageOf: (y: number) => string }) {
  const end = money(k.endS)
  let s = `You retire in ${k.retS} (${ageOf(k.retS)})${k.fiS ? `, work becomes optional in ${k.fiS}` : ''}, and ${k.depS ? `savings run out in ${k.depS} (${ageOf(k.depS)})` : `you end with about ${end} in today's dollars`}.`
  let t = ''
  if (onCount) {
    const d = k.endS - k.endB
    const names = list.filter(w => w.on).map(w => w.name || DEF[w.key].label)
    const big = list.filter(w => w.on && impact[w.id] != null).sort((a, b) => Math.abs(impact[b.id]) - Math.abs(impact[a.id]))[0]
    t = `With ${names.length === 1 ? names[0] : `${names.length} decisions`} on, ` +
      (k.retS !== k.retB ? `retirement moves ${Math.abs(k.retS - k.retB)} years ${k.retS < k.retB ? 'earlier' : 'later'} and ` : 'retirement age stays the same and ') +
      (Math.abs(d) < 1000 ? 'money left at the end stays about the same.' : `you end with ${money(Math.abs(d))} ${d > 0 ? 'more' : 'less'} than your plan.`) +
      (big && names.length > 1 ? ` The biggest effect is ${big.name || DEF[big.key].label} (${money(impact[big.id], { sign: true })}).` : '')
  }
  return <div className="border-t border-line px-5 py-3 text-[13.5px] text-ink2"><span className="font-semibold text-ink">Your plan in words. </span>{s} {t}</div>
}

function Catalog({ plan, onClose, onAdd, onDragStart }: { plan: any; onClose: () => void; onAdd: (key: string) => void; onDragStart: (e: React.PointerEvent, key: string, onClick: () => void) => void }) {
  const [cat, setCat] = useState<Cat>('career')
  const [q, setQ] = useState('')
  const c = ctxFor(plan)
  useEffect(() => { const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h) }, [onClose])
  const ql = q.trim().toLowerCase()
  const items = CATALOG.filter(d => ql ? `${d.label} ${d.desc} ${d.quick || ''}`.toLowerCase().includes(ql) : d.cat === cat)
  const meta = (key: string) => { const w = create(plan, key); const parts = [amountText(w)]
    if (DEF[key].timing !== 'none') parts.push(`${DEF[key].timing === 'span' ? 'From' : 'In'} ${whenText(plan, w)}`)
    return parts.filter(Boolean).join(' · ') }
  return (
    <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center p-3 sm:p-6">
      <div className="absolute inset-0 bg-black/35" onClick={onClose} />
      <div className="relative w-full max-w-3xl max-h-[88vh] flex flex-col rounded-2xl border border-line bg-surface shadow-2xl overflow-hidden">
        <header className="px-6 pt-5 pb-4 bg-gradient-to-r from-accentSoft to-surface border-b border-line">
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <h2 className="text-[19px] font-semibold">What are you thinking about?</h2>
              <p className="text-[13px] text-muted mt-0.5">Pick a decision to stack on your plan. Click + to add it, or drag the handle straight onto the chart at the year you want.</p>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-md hover:bg-sunken text-muted"><X size={18} /></button>
          </div>
        </header>
        <div className="px-6 pt-4">
          <div className="relative"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Search all decisions… (e.g. roth, car, sabbatical)"
              className="w-full h-10 rounded-lg border border-line bg-surface pl-9 pr-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" /></div>
          {!ql && <div className="flex flex-wrap gap-2 mt-3">
            {CATS.map(x => <button key={x.key} onClick={() => setCat(x.key)}
              className={clsx('inline-flex items-center gap-1.5 h-9 px-3 rounded-lg text-[13.5px] font-medium border',
                cat === x.key ? (x.key === 'stress' ? 'bg-bad/10 border-bad/40 text-bad' : 'bg-accentSoft border-accent/40 text-accent') : 'bg-sunken border-transparent text-ink2 hover:text-ink')}>
              <span>{x.emoji}</span>{x.label}</button>)}
          </div>}
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
          {items.length === 0 && <div className="text-sm text-muted py-6 text-center">No decisions match “{q}”.</div>}
          {items.map(d => {
            const why = d.available?.(plan, c)
            return (
              <div key={d.key} className={clsx('flex items-center gap-3 rounded-xl border border-line px-3 py-3', why ? 'opacity-55' : 'hover:border-accent/50 hover:bg-accentSoft/25')}>
                <button disabled={!!why} onPointerDown={e => !why && onDragStart(e, d.key, () => onAdd(d.key))} title={why || 'Drag onto the chart'}
                  className="self-stretch flex items-center text-muted cursor-grab active:cursor-grabbing touch-none"><GripVertical size={16} /></button>
                <div className="w-10 h-10 shrink-0 rounded-xl bg-sunken flex items-center justify-center text-[19px]">{d.emoji}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-[14.5px]">{d.label}</div>
                  <div className="text-[13px] text-ink2">{d.desc}</div>
                  <div className="text-[12px] text-muted mt-0.5">{why || meta(d.key)}</div>
                </div>
                <button disabled={!!why} onClick={() => onAdd(d.key)} className="w-9 h-9 shrink-0 rounded-full flex items-center justify-center text-accent hover:bg-accentSoft disabled:opacity-40" aria-label={`Add ${d.label}`}>
                  <Plus size={20} /></button>
              </div>)
          })}
        </div>
      </div>
    </div>)
}

function Editor({ w, plan, reference, single, names, ageOf, onChange }: { w: WhatIf; plan: any; reference: any; single: boolean; names: [string, string]; ageOf: (y: number) => string; onChange: (w: WhatIf) => void }) {
  const def = DEF[w.key]
  const set = (patch: Partial<WhatIf>) => onChange({ ...w, ...patch })
  const c = ctxFor(plan)
  return (
    <div className="space-y-4">
      <p className="text-[13.5px] text-ink2">{def.desc}</p>
      {def.available?.(plan, c) && <Note tone="warn">{def.available(plan, c)} — this decision is ignored until then.</Note>}
      <div className="flex items-center justify-between"><Toggle checked={w.on} onChange={v => set({ on: v })} label="On (stacked on the plan)" />
        <span className="text-[12px] text-muted">{canBake(plan, w) ? 'Can become part of the plan' : 'What-if only'}</span></div>
      <Field label="Name"><TextInput value={w.name || ''} placeholder={def.label} onChange={v => set({ name: v || undefined })} /></Field>
      {def.timing !== 'none' && <div className="grid grid-cols-2 gap-3">
        <Field label={def.startLabel || 'Starts'} hint="Drag its flag on the chart, or type a year">
          <NumberInput value={w.start} min={c.cy} max={c.last} step={1} onChange={v => set({ start: Math.round(v), end: w.end != null ? Math.max(Math.round(v), w.end) : w.end })} />
          <div className="text-[12px] text-muted mt-1">{ageOf(w.start)}</div></Field>
        {def.timing === 'span' && <Field label={def.endLabel || 'Ends'} hint="Last year it applies">
          <NumberInput value={w.end ?? w.start} min={w.start} max={c.last} step={1} onChange={v => set({ end: Math.round(v) })} />
          <div className="text-[12px] text-muted mt-1">{ageOf(w.end ?? w.start)} · {(w.end ?? w.start) - w.start + 1} yr</div></Field>}
      </div>}
      <div className="grid grid-cols-2 gap-3">
        {def.fields.map(f => {
          if (f.key === 'person') return single ? null : <Field key={f.key} label={f.label}>
            <Select value={w.person || 'both'} onChange={v => set({ person: v as any })}
              options={[...(w.key.startsWith('retire') || w.key.startsWith('work') || w.key.startsWith('ss_') ? [{ value: 'both', label: 'Both' }] : []), { value: 'X', label: names[0] }, { value: 'Y', label: names[1] }]} /></Field>
          if (f.key === 'location') return <Field key={f.key} label={f.label} className="col-span-2">
            <LocationPicker value={w.location || 'Seattle'} catalog={reference?.location_catalog} custom={plan.custom_locations || {}} onChange={v => set({ location: v })} /></Field>
          const v = (w as any)[f.key]
          return <Field key={f.key} label={f.label} hint={f.hint}>
            {f.unit === '%' ? <NumberInput value={v} suffix="%" step={1} decimals={1} onChange={x => set({ [f.key]: x } as any)} />
              : <Money value={v} suffix={f.unit === '$/mo' ? '/mo' : f.unit === '$/yr' ? '/yr' : undefined} onChange={x => set({ [f.key]: x } as any)} />}</Field>
        })}
      </div>
      <p className="text-[12px] text-muted">Amounts are in today's dollars. Every change recalculates the chart and numbers right away.</p>
    </div>)
}
