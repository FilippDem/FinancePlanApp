import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ZoomIn, ZoomOut, Maximize2, Undo2, GripVertical, Save, Layers, Info, Trash2, Loader2, MousePointerClick } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, clsx } from '../lib/format'
import { Card, Button, Select, Modal, Field, TextInput, NumberInput, Money, Percent, Toggle, Note, Badge } from './ui'
import { S } from './charts'
import { LocationPicker } from '../pages/Locations'
import { LANES, PALETTE, Item, Ref, Kind, items as buildItems, setYear, remove, removable, fields, draftFor, applyDraft, KIND_LABEL, endYear } from '../lib/lifeEdit'

const PAD = 14            // px before the first year
const LABEL_W = 132       // left lane labels
const ROW_H = 30
const MIN_PPY = 6, MAX_PPY = 140

const TONE: Record<string, string> = { accent: 'var(--s1)', good: 'rgb(var(--good))', warn: 'rgb(var(--warn))', bad: 'rgb(var(--bad))', muted: 'rgb(var(--muted))' }
const LANE_COLOR: Record<string, string> = { people: S[0], where: S[1], home: S[2], kids: S[3], money: S[4], goals: S[5] }

type Editing = { ref: Ref; year: number; isNew: boolean; draft: any } | null

/** Zoomable, editable timeline of the whole plan: drag milestones to change their year, drop new ones from the palette,
 *  click to edit. Edits go to the current plan (auto-saved) or to a saved scenario. */
export function LifeEditor({ initialTarget }: { initialTarget?: string }) {
  const { plan: cur, update: curUpdate, proj: curProj, reference } = usePlan()
  const nav = useNavigate()
  const [target, setTarget] = useState<string>(initialTarget || '')
  const [scen, setScen] = useState<Record<string, any>>({})
  const [sPlan, setSPlan] = useState<any>(null)
  const [sProj, setSProj] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const loadScen = useCallback(() => api.scenarios().then(r => setScen(r.scenarios)).catch(() => {}), [])
  useEffect(() => { loadScen() }, [loadScen])
  useEffect(() => {
    if (!target) { setSPlan(null); setSProj(null); return }
    const raw = scen[target]
    if (raw) api.normalize(raw).then(r => setSPlan(r.plan)).catch(() => setSPlan(raw))
  }, [target, scen[target] ? 1 : 0])
  // scenario: project + save (debounced)
  const sKey = sPlan ? JSON.stringify(sPlan) : ''
  const dirtyScen = useRef(false)
  useEffect(() => {
    if (!sPlan) return
    const t = setTimeout(async () => {
      try { const r = await api.project(sPlan); setSProj(r) } catch { /* */ }
      if (dirtyScen.current) {
        setSaving(true)
        try { await api.saveScenario(target, sPlan); dirtyScen.current = false } catch { /* */ } finally { setSaving(false) }
      }
    }, 500)
    return () => clearTimeout(t)
  }, [sKey])

  const plan = target ? sPlan : cur
  const proj = target ? sProj : curProj

  // undo + "what changed"
  const undo = useRef<any[]>([])
  const [lastDelta, setLastDelta] = useState<{ before: number; label: string } | null>(null)
  const endNW = (pr: any) => { const r = pr?.rows?.[pr.rows.length - 1]; return r ? r.net_worth / r.infl_index : null }
  const edit = (fn: (d: any) => void, label: string) => {
    if (!plan) return
    undo.current.push(structuredClone(plan)); if (undo.current.length > 40) undo.current.shift()
    const before = endNW(proj)
    if (before != null) setLastDelta({ before, label })
    if (target) { dirtyScen.current = true; setSPlan((p: any) => { const d = structuredClone(p); fn(d); return d }) }
    else curUpdate(fn)
  }
  const doUndo = () => {
    const prev = undo.current.pop()
    if (!prev) return
    setLastDelta(null)
    if (target) { dirtyScen.current = true; setSPlan(prev) }
    else curUpdate(d => { for (const k of Object.keys(d)) delete d[k]; Object.assign(d, prev) })
  }
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !(e.target as HTMLElement)?.closest?.('input,textarea,select')) { e.preventDefault(); doUndo() } }
    window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h)
  })

  // geometry
  const scrollRef = useRef<HTMLDivElement>(null)
  const [ppy, setPpy] = useState<number>(() => { try { return +(localStorage.getItem('fp_ppy') || 0) || 26 } catch { return 26 } })
  useEffect(() => { try { localStorage.setItem('fp_ppy', String(ppy)) } catch { /* */ } }, [ppy])
  const start = plan?.current_year ?? 2026
  const end = plan ? Math.max(endYear(plan), start + 1) : start + 60
  const nYears = end - start + 1
  const width = PAD * 2 + nYears * ppy
  const xOf = (y: number) => PAD + (y - start) * ppy + ppy / 2
  const yearAtClient = (clientX: number) => {
    const el = scrollRef.current!
    const r = el.getBoundingClientRect()
    return Math.min(end, Math.max(start, start + Math.floor((clientX - r.left + el.scrollLeft - PAD) / ppy)))
  }
  const zoomTo = (next: number, anchorClientX?: number) => {
    const el = scrollRef.current
    const np = Math.min(MAX_PPY, Math.max(MIN_PPY, next))
    if (!el) { setPpy(np); return }
    const r = el.getBoundingClientRect()
    const ax = anchorClientX != null ? anchorClientX - r.left : r.width / 2
    const yearPos = (el.scrollLeft + ax - PAD) / ppy
    setPpy(np)
    requestAnimationFrame(() => { el.scrollLeft = Math.max(0, yearPos * np + PAD - ax) })
  }
  const fit = (years = nYears) => {
    const el = scrollRef.current
    if (!el) return
    setPpy(Math.min(MAX_PPY, Math.max(MIN_PPY, (el.clientWidth - PAD * 2) / years)))
    requestAnimationFrame(() => { el.scrollLeft = 0 })
  }
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const h = (e: WheelEvent) => { if (e.ctrlKey || e.metaKey) { e.preventDefault(); zoomTo(ppy * (e.deltaY < 0 ? 1.15 : 1 / 1.15), e.clientX) } }
    el.addEventListener('wheel', h, { passive: false })
    return () => el.removeEventListener('wheel', h)
  })

  // items and lane packing
  const all = useMemo(() => (plan ? buildItems(plan, proj) : []), [plan, proj])
  const [drag, setDrag] = useState<{ id: string; year: number } | null>(null)
  const lanes = useMemo(() => LANES.map(l => {
    const its = all.filter(i => i.lane === l.key).map(i => (drag && drag.id === i.id ? { ...i, year: drag.year } : i)).sort((a, b) => a.year - b.year)
    const ends: number[] = []
    const placed = its.map(i => {
      const x = xOf(i.year) - 5
      const w = 26 + Math.max(i.label.length, (i.sub || '').length) * 6.3
      const barEnd = i.end ? xOf(i.end) : x + w
      let row = ends.findIndex(e => e < x - 4)
      if (row === -1) { row = ends.length; ends.push(0) }
      ends[row] = Math.max(x + w, barEnd)
      return { ...i, x, row }
    })
    return { ...l, placed, rows: Math.max(1, ends.length) }
  }), [all, ppy, start, drag])

  // background bands: where you live, which home, work years
  const bands = useMemo(() => {
    if (!plan) return { where: [], home: [], work: [] as any[] }
    const stl: any[] = plan.state_timeline || []
    const colors: Record<string, string> = {}; let k = 0
    const where = stl.map((e, i) => ({ from: Math.max(e.year, start), to: i + 1 < stl.length ? stl[i + 1].year - 1 : end, label: e.state, color: (colors[e.state] ??= S[k++ % 8]) }))
      .filter(s => s.to >= s.from)
    const home: any[] = []
    for (const r of proj?.rows || []) {
      const live = (r.details?.houses || []).find((h: any) => h.status === 'Own_Live')
      const lab = live ? live.name : 'Renting'
      const last = home[home.length - 1]
      if (last && last.label === lab && last.to === r.year - 1) last.to = r.year
      else home.push({ from: r.year, to: r.year, label: lab })
    }
    const hc: Record<string, string> = {}; let j = 2
    home.forEach(h => { h.color = h.label === 'Renting' ? 'transparent' : (hc[h.label] ??= S[j++ % 8]) })
    const work = (['X', 'Y'] as const).filter(w => w === 'X' || (plan.parent2_name && plan.parent2_name !== 'N/A')).map(w => ({
      from: start, to: start + (plan[`parent${w}_retirement_age`] - plan[`parent${w}_age`]) - 1, label: `${w === 'X' ? plan.parent1_name : plan.parent2_name} working` }))
    return { where, home, work }
  }, [plan, proj, start, end])

  // net-worth strip
  const nw = useMemo(() => (proj?.rows || []).map((r: any) => ({ year: r.year, v: r.net_worth / r.infl_index, inv: r.investable / r.infl_index })), [proj])
  const nwMax = Math.max(1, ...nw.map((r: any) => Math.max(r.v, r.inv, 0)))
  const nwMin = Math.min(0, ...nw.map((r: any) => Math.min(r.v, r.inv)))
  const STRIP = 64
  const yOf = (v: number) => STRIP - 6 - ((v - nwMin) / (nwMax - nwMin || 1)) * (STRIP - 14)
  const path = (key: 'v' | 'inv') => nw.map((r: any, i: number) => `${i ? 'L' : 'M'}${xOf(r.year).toFixed(1)},${yOf(r[key]).toFixed(1)}`).join(' ')
  const [hoverYear, setHoverYear] = useState<number | null>(null)

  // editor
  const [editing, setEditing] = useState<Editing>(null)
  const openEdit = (ref: Ref, year: number, isNew: boolean) => { if (plan) setEditing({ ref, year, isNew, draft: draftFor(plan, ref, year) }) }
  const saveEdit = () => {
    if (!editing) return
    const { ref, draft, isNew } = editing
    edit(d => applyDraft(d, ref, draft), `${isNew ? 'Added' : 'Changed'} ${KIND_LABEL[ref.kind].toLowerCase()}`)
    setEditing(null)
  }

  // drag existing items
  const dragRef = useRef<{ it: Item; x0: number; moved: boolean; year: number } | null>(null)
  const onItemDown = (e: React.PointerEvent, it: Item) => {
    e.stopPropagation()
    ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
    dragRef.current = { it, x0: e.clientX, moved: false, year: it.year }
  }
  const onItemMove = (e: React.PointerEvent) => {
    const d = dragRef.current
    if (!d) return
    const dx = e.clientX - d.x0
    if (Math.abs(dx) > 3) d.moved = true
    if (!d.moved || !d.it.draggable) return
    const ny = Math.min(d.it.max ?? end, Math.max(d.it.min ?? start, d.it.year + Math.round(dx / ppy)))
    if (ny !== d.year) { d.year = ny; setDrag({ id: d.it.id, year: ny }) }
  }
  const onItemUp = () => {
    const d = dragRef.current
    dragRef.current = null
    setDrag(null)
    if (!d) return
    if (!d.moved) { openEdit(d.it.ref, d.it.year, false); return }
    if (d.it.draggable && d.year !== d.it.year) edit(pl => setYear(pl, d.it.ref, d.year), `Moved ${d.it.label} to ${d.year}`)
  }

  // pan the background
  const panRef = useRef<{ x0: number; s0: number } | null>(null)
  const onBgDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return
    panRef.current = { x0: e.clientX, s0: scrollRef.current?.scrollLeft || 0 }
    ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
  }
  const onBgMove = (e: React.PointerEvent) => {
    if (panRef.current && scrollRef.current) scrollRef.current.scrollLeft = panRef.current.s0 - (e.clientX - panRef.current.x0)
  }
  const onBgUp = () => { panRef.current = null }

  // drop new items from the palette
  const [ghost, setGhost] = useState<{ kind: Kind; label: string; x: number; y: number; year: number | null } | null>(null)
  const onPaletteDown = (e: React.PointerEvent, kind: Kind, label: string) => {
    e.preventDefault()
    const x0 = e.clientX, y0 = e.clientY
    let moved = false
    const over = (cx: number, cy: number) => {
      const el = scrollRef.current
      if (!el) return null
      const r = el.getBoundingClientRect()
      return cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom ? yearAtClient(cx) : null
    }
    const mv = (ev: PointerEvent) => {
      if (Math.abs(ev.clientX - x0) + Math.abs(ev.clientY - y0) > 4) moved = true
      if (moved) setGhost({ kind, label, x: ev.clientX, y: ev.clientY, year: over(ev.clientX, ev.clientY) })
    }
    const up = (ev: PointerEvent) => {
      window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up)
      setGhost(null)
      if (!moved) { openEdit({ kind }, Math.min(end, start + 5), true); return }
      const y = over(ev.clientX, ev.clientY)
      if (y != null) openEdit({ kind }, y, true)
    }
    window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up)
  }

  const ticks = ppy >= 34 ? 1 : ppy >= 13 ? 5 : 10
  const scenNames = Object.keys(scen).filter(n => !n.startsWith('[DEMO]'))
  const [saveAs, setSaveAs] = useState<string | null>(null)
  const nowEnd = endNW(proj)
  const lanesH = lanes.reduce((a, l) => a + 14 + l.rows * ROW_H, 0)
  const single = !plan?.parent2_name || plan?.parent2_name === 'N/A'
  const retireYears = plan ? (['X', 'Y'] as const).filter(w => w === 'X' || !single).map(w => plan.current_year + plan[`parent${w}_retirement_age`] - plan[`parent${w}_age`]) : []

  return (
    <Card title="Plan editor" subtitle="Drag milestones to change their year, drop new ones from the palette, click anything to edit. Ctrl/⌘ + scroll to zoom, drag the background to pan."
      action={<div className="flex items-center gap-2">
        <span className="text-[12.5px] text-muted hidden sm:inline">Editing</span>
        <Select value={target} onChange={v => { setTarget(v); undo.current = []; setLastDelta(null) }}
          options={[{ value: '', label: 'My plan' }, ...scenNames.map(n => ({ value: n, label: `Scenario: ${n}` }))]} />
        {!target && <Button size="sm" onClick={() => setSaveAs('')}><Save size={13} />Save as scenario</Button>}
        {target && <Button size="sm" variant="ghost" onClick={() => nav('/scenarios')}><Layers size={13} />Matrix</Button>}
      </div>}>
      {!plan ? <div className="h-40 flex items-center gap-2 text-muted text-sm"><Loader2 size={15} className="animate-spin" />Loading scenario…</div> : <>
        {/* palette + zoom */}
        <div className="flex flex-wrap items-center gap-1.5 mb-3">
          <span className="text-[12px] font-semibold uppercase tracking-wide text-muted mr-1 flex items-center gap-1"><MousePointerClick size={13} />Drag onto the timeline</span>
          {PALETTE.map(pk => (
            <button key={pk.kind} title={pk.hint} onPointerDown={e => onPaletteDown(e, pk.kind, pk.label)}
              className="touch-none select-none cursor-grab active:cursor-grabbing inline-flex items-center gap-1 h-7 px-2 rounded-full border border-line text-[12.5px] hover:bg-sunken">
              <GripVertical size={12} className="text-muted" /><span className="w-2 h-2 rounded-full" style={{ background: LANE_COLOR[pk.lane] }} />{pk.label}</button>
          ))}
          <span className="flex-1" />
          <div className="flex items-center gap-1">
            <Button size="sm" variant="ghost" title="Undo (Ctrl/⌘+Z)" disabled={!undo.current.length} onClick={doUndo}><Undo2 size={14} /></Button>
            <Button size="sm" variant="ghost" title="Zoom out" onClick={() => zoomTo(ppy / 1.4)}><ZoomOut size={14} /></Button>
            <input type="range" min={MIN_PPY} max={MAX_PPY} value={ppy} onChange={e => zoomTo(+e.target.value)} className="w-24 accent-[rgb(var(--accent))]" aria-label="Zoom" />
            <Button size="sm" variant="ghost" title="Zoom in" onClick={() => zoomTo(ppy * 1.4)}><ZoomIn size={14} /></Button>
            <Button size="sm" variant="ghost" onClick={() => fit(10)}>10 yrs</Button>
            <Button size="sm" variant="ghost" onClick={() => fit(30)}>30 yrs</Button>
            <Button size="sm" variant="ghost" title="Whole plan" onClick={() => fit()}><Maximize2 size={14} /></Button>
          </div>
        </div>
        {lastDelta && nowEnd != null && (
          <div className="mb-2 text-[12.5px] flex flex-wrap items-center gap-2">
            <Badge tone="accent">{lastDelta.label}</Badge>
            <span className="text-ink2">Money left at the end: {money(nowEnd)} <span className={clsx('tnum font-medium', nowEnd - lastDelta.before >= 0 ? 'text-good' : 'text-bad')}>
              ({nowEnd - lastDelta.before >= 0 ? '+' : '−'}{money(Math.abs(nowEnd - lastDelta.before))})</span> in today's dollars</span>
            {proj?.summary?.depletion_year && <span className="text-bad">Savings run out in {proj.summary.depletion_year}</span>}
            {saving && <span className="text-muted flex items-center gap-1"><Loader2 size={12} className="animate-spin" />saving scenario</span>}
          </div>)}

        <div className="flex border border-line rounded-lg overflow-hidden select-none">
          {/* lane labels */}
          <div className="shrink-0 border-r border-line bg-sunken/40" style={{ width: LABEL_W }}>
            <div className="px-3 flex items-end text-[11.5px] text-muted pb-1" style={{ height: 40 }}>Year · age</div>
            <div className="px-3 flex items-center text-[12.5px] font-medium border-t border-line" style={{ height: STRIP }}>Net worth<br />(today's $)</div>
            {lanes.map(l => (
              <div key={l.key} className="px-3 flex items-center gap-2 text-[12.5px] font-medium border-t border-line" style={{ height: 14 + l.rows * ROW_H }}>
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: LANE_COLOR[l.key] }} />{l.label}</div>
            ))}
          </div>
          {/* scrollable timeline */}
          <div ref={scrollRef} className="overflow-x-auto flex-1 relative" onPointerDown={onBgDown} onPointerMove={onBgMove} onPointerUp={onBgUp}
            style={{ cursor: panRef.current ? 'grabbing' : 'grab' }}>
            <div className="relative" style={{ width, height: 40 + STRIP + lanesH }}>
              {/* axis */}
              {Array.from({ length: nYears }, (_, i) => start + i).filter(y => (y - start) % ticks === 0).map(y => (
                <div key={y} className="absolute top-0 text-[11px] tnum pointer-events-none" style={{ left: xOf(y) - 14 }}>
                  <div className="font-medium text-ink2">{y}</div>
                  <div className="text-muted">{plan.parentX_age + (y - start)}{!single && `/${plan.parentY_age + (y - start)}`}</div>
                </div>))}
              {Array.from({ length: nYears }, (_, i) => start + i).filter(y => (y - start) % ticks === 0).map(y => (
                <div key={`g${y}`} className="absolute border-l border-line/60 pointer-events-none" style={{ left: xOf(y), top: 40, bottom: 0 }} />))}
              {retireYears.map((y, i) => <div key={`r${i}`} className="absolute border-l-2 border-dashed pointer-events-none" style={{ left: xOf(y), top: 40, bottom: 0, borderColor: S[0], opacity: 0.45 }} />)}
              {hoverYear != null && <div className="absolute border-l border-ink/30 pointer-events-none" style={{ left: xOf(hoverYear), top: 40, bottom: 0 }} />}
              {/* net-worth strip */}
              <div className="absolute left-0 right-0 border-t border-line" style={{ top: 40, height: STRIP }}
                onPointerMove={e => setHoverYear(yearAtClient(e.clientX))} onPointerLeave={() => setHoverYear(null)}>
                <svg width={width} height={STRIP} className="block">
                  <line x1={0} x2={width} y1={yOf(0)} y2={yOf(0)} stroke="var(--axis)" strokeOpacity={0.4} />
                  <path d={path('v')} fill="none" stroke={S[0]} strokeWidth={2} />
                  <path d={path('inv')} fill="none" stroke={S[1]} strokeWidth={1.5} strokeDasharray="3 2" />
                </svg>
                {hoverYear != null && (() => { const r = nw.find((x: any) => x.year === hoverYear); return r ? (
                  <div className="absolute top-1 px-2 py-0.5 rounded bg-surface border border-line text-[11.5px] tnum shadow pointer-events-none whitespace-nowrap"
                    style={{ left: Math.min(xOf(hoverYear) + 6, width - 190) }}>{hoverYear}: net worth {money(r.v)} · savings {money(r.inv)}</div>) : null })()}
              </div>
              {/* lanes */}
              {(() => {
                let top = 40 + STRIP
                return lanes.map(l => {
                  const h = 14 + l.rows * ROW_H
                  const t0 = top
                  top += h
                  const band = l.key === 'where' ? bands.where : l.key === 'home' ? bands.home : l.key === 'people' ? bands.work : []
                  return (
                    <div key={l.key} className="absolute left-0 right-0 border-t border-line" style={{ top: t0, height: h }}>
                      {band.map((b: any, i: number) => (
                        <div key={i} className="absolute top-1 bottom-1 rounded-md pointer-events-none overflow-hidden" title={`${b.label} ${b.from}–${b.to}`}
                          style={{ left: xOf(b.from) - ppy / 2, width: Math.max(2, (b.to - b.from + 1) * ppy), background: b.color || S[0], opacity: b.color === 'transparent' ? 1 : 0.13,
                            border: b.color === 'transparent' ? '1px dashed rgb(var(--line))' : undefined }} />))}
                      {l.key !== 'people' && band.map((b: any, i: number) => (b.to - b.from + 1) * ppy > 60 && (
                        <div key={`t${i}`} className="absolute bottom-0.5 text-[10.5px] text-muted pointer-events-none truncate" style={{ left: xOf(b.from) - ppy / 2 + 4, maxWidth: (b.to - b.from + 1) * ppy - 8 }}>{b.label}</div>))}
                      {l.placed.map((it: any) => (
                        <React.Fragment key={it.id}>
                          {it.end && it.end > it.year && <div className="absolute h-1 rounded-full pointer-events-none" style={{ left: it.x + 5, width: Math.max(0, xOf(it.end) - it.x - 5), top: 7 + it.row * ROW_H + 20, background: LANE_COLOR[l.key], opacity: 0.35 }} />}
                          <div onPointerDown={e => onItemDown(e, it)} onPointerMove={onItemMove} onPointerUp={onItemUp}
                            className={clsx('absolute flex items-center gap-1.5 whitespace-nowrap rounded-full pr-2 pl-0.5 py-0.5 bg-surface/90 border touch-none',
                              it.draggable ? 'cursor-ew-resize hover:shadow' : 'cursor-pointer', drag?.id === it.id ? 'border-accent shadow-lg z-10' : 'border-transparent hover:border-line')}
                            style={{ left: it.x - 2, top: 7 + it.row * ROW_H }} title={`${it.year}: ${it.label}${it.sub ? ` · ${it.sub}` : ''}${it.draggable ? ' — drag to move, click to edit' : ' — click to edit'}`}>
                            <span className="w-3 h-3 rounded-full ring-2 ring-surface shrink-0" style={{ background: it.tone ? TONE[it.tone] : LANE_COLOR[l.key] }} />
                            <span className="text-[12px] leading-tight">
                              <span className="text-ink font-medium">{it.label}</span>
                              {drag?.id === it.id ? <span className="ml-1 text-accent tnum font-semibold">{it.year}</span> : it.sub ? <span className="ml-1 text-muted">{it.sub}</span> : null}
                            </span>
                          </div>
                        </React.Fragment>))}
                    </div>)
                })
              })()}
              {ghost?.year != null && <div className="absolute w-0.5 bg-accent pointer-events-none" style={{ left: xOf(ghost.year), top: 40, bottom: 0 }} />}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[12px] text-muted">
          <span className="flex items-center gap-1.5"><span className="w-4 h-0.5" style={{ background: S[0] }} />Net worth</span>
          <span className="flex items-center gap-1.5"><span className="w-4 h-0.5 border-t border-dashed" style={{ borderColor: S[1] }} />Savings & retirement accounts</span>
          <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed" style={{ borderColor: S[0] }} />Retirement</span>
          <span className="flex items-center gap-1"><Info size={12} />Small yearly costs stay on the Spending page; details for every item are on its own page.</span>
        </div>
      </>}

      {ghost && <div className="fixed z-50 pointer-events-none px-2.5 py-1 rounded-full bg-accent text-white text-[12.5px] shadow-lg" style={{ left: ghost.x + 10, top: ghost.y + 10 }}>
        {ghost.label}{ghost.year != null ? ` · ${ghost.year}` : ' — drop on the timeline'}</div>}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing ? `${editing.isNew ? 'Add' : 'Edit'}: ${KIND_LABEL[editing.ref.kind]}` : ''}
        footer={editing && <>
          {!editing.isNew && removable(editing.ref.kind) && <Button variant="danger" onClick={() => { const r = editing.ref; edit(d => remove(d, r), `Removed ${KIND_LABEL[r.kind].toLowerCase()}`); setEditing(null) }}><Trash2 size={14} />Delete</Button>}
          <span className="flex-1" />
          <Button onClick={() => setEditing(null)}>Cancel</Button>
          <Button variant="primary" onClick={saveEdit} disabled={editing.ref.kind === 'house_event' && !(plan?.houses || []).length}>Save</Button>
        </>}>
        {editing && plan && <EditorForm plan={plan} editing={editing} setDraft={dr => setEditing(e => e && { ...e, draft: dr })} reference={reference} />}
      </Modal>
      <Modal open={saveAs !== null} onClose={() => setSaveAs(null)} title="Save as a scenario"
        footer={<><Button onClick={() => setSaveAs(null)}>Cancel</Button><Button variant="primary" disabled={!saveAs?.trim()} onClick={async () => {
          const n = saveAs!.trim(); await api.saveScenario(n, cur); await loadScen(); setSaveAs(null); setTarget(n); undo.current = [] }}>Save and edit it</Button></>}>
        <p className="text-sm text-ink2 mb-3">Copies your plan into a scenario, then switches the editor to it, so you can try changes (a third child, a move, retiring earlier) without touching your plan. Compare scenarios in the Scenario matrix.</p>
        <TextInput value={saveAs || ''} onChange={setSaveAs} placeholder="e.g. Three kids, move to Austin" autoFocus />
      </Modal>
    </Card>
  )
}

function EditorForm({ plan, editing, setDraft, reference }: { plan: any; editing: NonNullable<Editing>; setDraft: (d: any) => void; reference: any }) {
  const { ref, draft, isNew } = editing
  const specs = fields(plan, ref.kind, isNew).filter(f => !f.show || f.show(draft))
  const set = (k: string, v: any) => setDraft({ ...draft, [k]: v })
  const w = (ref.who || 'X') as 'X' | 'Y'
  const age = (y: number, who: 'X' | 'Y' = w) => plan[`parent${who}_age`] + (y - plan.current_year)
  if (ref.kind === 'house_event' && !(plan.houses || []).length) return <Note>Add a home first (drag “Buy a home” onto the timeline, or use the Homes page).</Note>
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        {specs.map(f => (
          <Field key={f.key} label={f.type === 'year' && draft[f.key] ? `${f.label} (age ${age(+draft[f.key], ref.kind === 'pension' ? (draft.person === 'Parent 2' ? 'Y' : 'X') : w)})` : f.label} hint={f.hint}
            className={f.type === 'location' || f.type === 'toggle' || f.type === 'text' ? 'col-span-2' : ''}>
            {f.type === 'text' ? <TextInput value={draft[f.key] ?? ''} onChange={v => set(f.key, v)} />
              : f.type === 'money' ? <Money value={draft[f.key] ?? 0} onChange={v => set(f.key, v)} />
              : f.type === 'percent' ? <Percent value={draft[f.key] ?? null as any} decimals={2} onChange={v => set(f.key, v)} />
              : f.type === 'number' || f.type === 'year' ? <NumberInput value={draft[f.key] ?? null} step={1} onChange={v => set(f.key, Math.round(v))} placeholder={f.type === 'year' ? 'year' : ''} />
              : f.type === 'select' ? <Select value={String(draft[f.key] ?? '')} options={f.options as any} onChange={v => set(f.key, v)} />
              : f.type === 'location' ? <LocationPicker value={draft[f.key] || 'Seattle'} catalog={reference?.location_catalog} custom={plan.custom_locations || {}} onChange={v => set(f.key, v)} />
              : <Toggle checked={!!draft[f.key]} onChange={v => set(f.key, v)} />}
          </Field>))}
      </div>
      {ref.kind === 'house_buy' && isNew && <p className="text-[12.5px] text-muted">Uses an estimated mortgage (price, down payment, rate, term) with 2% closing costs and 1% property tax; fine-tune on the Homes page.</p>}
      {ref.kind === 'job' && isNew && (plan[`parent${draft.person === 'Parent 2' ? 'Y' : 'X'}_career_phases`] || []).length > 0 && <p className="text-[12.5px] text-muted">This person uses career phases, so a new phase starts that year.</p>}
      {ref.kind === 'child' && isNew && <p className="text-[12.5px] text-muted">Costs follow the child templates for where you live (childcare, school, college); change details on the Kids page.</p>}
    </div>
  )
}
