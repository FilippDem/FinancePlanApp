/** Projection chart for the decision playground: net worth (with decisions vs your plan) on top, cash flow below,
 *  and a vertical marker for every decision. Drag a marker's flag (or its line) left/right to change when that
 *  decision happens; arrow keys nudge a focused flag by a year. FinP4l-style. */
import React, { forwardRef, useImperativeHandle, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { axisMoney, money } from '../lib/format'
import type { Marker } from '../lib/whatifs'

export interface FixedMarker { id: string; year: number; label: string; color: string; emoji: string; draggable?: boolean; min?: number; max?: number }
export interface ChartHandle { yearAt: (clientX: number, clientY: number) => number | null }

interface Props {
  rows: any[]
  baseRows: any[] | null
  today: boolean
  ageOf: (year: number) => string
  markers: Marker[]
  fixed: FixedMarker[]
  ghostYear?: number | null
  ghostColor?: string
  showBase: boolean
  onMove: (id: string, year: number) => void        // live while dragging
  onDrop: (id: string, year: number) => void        // released (commit)
  onFlagClick?: (id: string) => void
}

const PAD_L = 62, PAD_R = 14, FLAG_H = 22, FLAG_GAP = 4, TOP_H = 250, MID = 30, BOT_H = 104, AXIS = 34

export const DecisionChart = forwardRef<ChartHandle, Props>(function DecisionChart(
  { rows, baseRows, today, ageOf, markers, fixed, ghostYear, ghostColor, showBase, onMove, onDrop, onFlagClick }, ref) {
  const wrap = useRef<HTMLDivElement>(null)
  const svg = useRef<SVGSVGElement>(null)
  const [W, setW] = useState(900)
  useLayoutEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(e => setW(Math.max(320, Math.round(e[0].contentRect.width))))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const y0 = rows[0]?.year ?? 2026, y1 = rows[rows.length - 1]?.year ?? y0 + 1
  const plotW = W - PAD_L - PAD_R
  const x = (y: number) => PAD_L + ((y - y0) / Math.max(1, y1 - y0)) * plotW
  const yearAtX = (px: number) => Math.round(y0 + ((px - PAD_L) / plotW) * (y1 - y0))
  const val = (r: any, k: string) => (today ? (r?.[k] ?? 0) / (r?.infl_index || 1) : (r?.[k] ?? 0))

  // ── drag state ──
  const [drag, setDrag] = useState<{ id: string; year: number; min: number; max: number } | null>(null)
  const [hover, setHover] = useState<number | null>(null)
  const dragRef = useRef(drag); dragRef.current = drag
  const moved = useRef(false)

  // ── flags: every decision marker plus the fixed ones, stacked in rows so labels never overlap ──
  type Flag = { id: string; year: number; label: string; color: string; emoji: string; draggable: boolean; min: number; max: number; dashed: boolean }
  const flagsRaw: Flag[] = useMemo(() => [
    ...fixed.map(f => ({ id: f.id, year: f.year, label: f.label, color: f.color, emoji: f.emoji, draggable: !!f.draggable, min: f.min ?? y0, max: f.max ?? y1, dashed: false })),
    ...markers.map(m => ({ id: m.id, year: m.year, label: m.label, color: m.color, emoji: m.emoji, draggable: true, min: m.min, max: m.max, dashed: true })),
  ], [fixed, markers, y0, y1])
  const flags = flagsRaw.map(f => (drag && f.id === drag.id ? { ...f, year: drag.year } : f))
  const placed = useMemo(() => {
    const out: (Flag & { row: number; fx: number; fw: number; text: string })[] = []
    const ends: number[] = []
    for (const f of [...flags].sort((a, b) => a.year - b.year)) {
      const text = `${f.emoji} ${f.label} · ${ageOf(f.year)}`
      const fw = Math.min(260, W - 8, 18 + text.length * 6.1)
      const lx = x(f.year)
      const fx = Math.max(2, Math.min(lx + fw > W - PAD_R ? lx - fw : lx, W - fw - 2))
      let row = ends.findIndex(e => e < fx - 4)
      if (row < 0) { row = ends.length; ends.push(0) }
      ends[row] = fx + fw
      out.push({ ...f, row, fx, fw, text })
    }
    return out
  }, [flags, W, y0, y1, ageOf])
  const nRows = Math.max(1, ...placed.map(p => p.row + 1))
  const bandH = nRows * (FLAG_H + FLAG_GAP) + 6
  const topY = bandH, topB = topY + TOP_H, botY = topB + MID, botB = botY + BOT_H, H = botB + AXIS

  // ── scales ──
  const nwKey = 'net_worth'
  const all = [...rows.map(r => val(r, nwKey)), ...(showBase && baseRows ? baseRows.map(r => val(r, nwKey)) : [])]
  let vMax = Math.max(1, ...all), vMin = Math.min(0, ...all)
  const pad = (vMax - vMin) * 0.06; vMax += pad; if (vMin < 0) vMin -= pad
  const ty = (v: number) => topB - ((v - vMin) / (vMax - vMin || 1)) * TOP_H
  const cf = (r: any) => ({ inc: val(r, 'total_income') + val(r, 'windfalls'), out: val(r, 'total_expenses') + val(r, 'taxes') })
  const cMax = Math.max(1, ...rows.map(r => Math.max(cf(r).inc, cf(r).out)), ...(showBase && baseRows ? baseRows.map(r => cf(r).out) : [])) * 1.08
  const by = (v: number) => botB - (Math.max(0, v) / cMax) * BOT_H
  const ticks = (lo: number, hi: number, k = 4) => {
    // round tick values (1, 2, 2.5, 5 × 10^n) that stay inside the axis
    const raw = (hi - lo) / k, mag = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1e-9))))
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(st => st >= raw) || raw
    const out: number[] = []
    for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) out.push(Math.abs(t) < step / 1e6 ? 0 : t)
    return out
  }

  const line = (rs: any[], f: (r: any) => number, yf: (v: number) => number) => rs.map((r, i) => `${i ? 'L' : 'M'}${x(r.year).toFixed(1)},${yf(f(r)).toFixed(1)}`).join('')
  const area = (rs: any[], f: (r: any) => number) => rs.length ? `${line(rs, f, ty)}L${x(rs[rs.length - 1].year)},${ty(Math.max(0, vMin))}L${x(rs[0].year)},${ty(Math.max(0, vMin))}Z` : ''

  // year ticks every 5 (or 10 on narrow screens)
  const every = plotW < 520 ? 10 : 5
  const yTicks: number[] = []
  for (let y = Math.ceil(y0 / every) * every; y <= y1; y += every) yTicks.push(y)

  // ── pointer handling ──
  const localX = (clientX: number) => { const b = svg.current!.getBoundingClientRect(); return (clientX - b.left) * (W / b.width) }
  useImperativeHandle(ref, () => ({
    yearAt: (cx: number, cy: number) => {
      const el = svg.current; if (!el) return null
      const b = el.getBoundingClientRect()
      if (cx < b.left || cx > b.right || cy < b.top || cy > b.bottom) return null
      return Math.min(y1, Math.max(y0, yearAtX(localX(cx))))
    },
  }), [W, y0, y1])

  const start = (e: React.PointerEvent, f: Flag) => {
    if (!f.draggable) { onFlagClick?.(f.id); return }
    e.preventDefault(); e.stopPropagation()
    svg.current?.setPointerCapture(e.pointerId)
    setDrag({ id: f.id, year: f.year, min: f.min, max: f.max })
    moved.current = false
  }
  const onPointerMove = (e: React.PointerEvent) => {
    const px = localX(e.clientX)
    const d = dragRef.current
    if (d) {
      const yr = Math.min(d.max, Math.max(d.min, yearAtX(px)))
      if (yr !== d.year) { setDrag({ ...d, year: yr }); moved.current = true; onMove(d.id, yr) }
    } else setHover(px >= PAD_L && px <= W - PAD_R ? Math.min(y1, Math.max(y0, yearAtX(px))) : null)
  }
  const onPointerUp = (e: React.PointerEvent) => {
    const d = dragRef.current
    if (!d) return
    svg.current?.releasePointerCapture(e.pointerId)
    setDrag(null)
    if (moved.current) onDrop(d.id, d.year)
    else onFlagClick?.(d.id)
  }
  const onKey = (e: React.KeyboardEvent, f: Flag) => {
    if (!f.draggable) return
    const k = e.key === 'ArrowLeft' ? -1 : e.key === 'ArrowRight' ? 1 : 0
    if (k) { e.preventDefault(); onDrop(f.id, Math.min(f.max, Math.max(f.min, f.year + k))) }
    if (e.key === 'Enter') onFlagClick?.(f.id)
  }

  // hover readout
  const hr = hover != null && !drag ? rows.find(r => r.year === hover) : null
  const hb = hover != null && !drag && baseRows ? baseRows.find(r => r.year === hover) : null
  const depl = rows.filter(r => r.investable < 0)

  return (
    <div ref={wrap} className="relative select-none">
      <svg ref={svg} viewBox={`0 0 ${W} ${H}`} width="100%" height={H} className="touch-none"
        onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp} onPointerLeave={() => !drag && setHover(null)}
        style={{ cursor: drag ? 'grabbing' : 'default' }}>
        {/* grid + axes */}
        {ticks(vMin, vMax).map((t, i) => <g key={`t${i}`}>
          <line x1={PAD_L} x2={W - PAD_R} y1={ty(t)} y2={ty(t)} stroke="var(--grid)" />
          <text x={PAD_L - 8} y={ty(t) + 4} textAnchor="end" fontSize="11" fill="var(--axis)">{axisMoney(t)}</text></g>)}
        {ticks(0, cMax, 2).map((t, i) => <g key={`b${i}`}>
          <line x1={PAD_L} x2={W - PAD_R} y1={by(t)} y2={by(t)} stroke="var(--grid)" />
          <text x={PAD_L - 8} y={by(t) + 4} textAnchor="end" fontSize="11" fill="var(--axis)">{axisMoney(t)}</text></g>)}
        <text x={PAD_L + 2} y={topY + 13} fontSize="11.5" fontWeight="600" fill="var(--axis)">Net worth{today ? ' (today’s $)' : ''}</text>
        <text x={PAD_L + 2} y={botY - 6} fontSize="11.5" fontWeight="600" fill="var(--axis)">Money in vs out per year</text>
        {yTicks.map(y => <g key={y}>
          <line x1={x(y)} x2={x(y)} y1={topY} y2={botB} stroke="var(--grid)" strokeDasharray="2 4" />
          <text x={x(y)} y={botB + 14} textAnchor="middle" fontSize="11" fill="var(--axis)">{y}</text>
          <text x={x(y)} y={botB + 27} textAnchor="middle" fontSize="10.5" fill="var(--axis)" opacity=".8">{ageOf(y)}</text></g>)}
        {/* years with savings gone */}
        {depl.map(r => <rect key={`d${r.year}`} x={x(r.year) - plotW / Math.max(1, y1 - y0) / 2} width={plotW / Math.max(1, y1 - y0)} y={topY} height={botB - topY} fill="rgb(var(--bad))" opacity=".07" />)}
        {ty(0) > topY && ty(0) < topB && <line x1={PAD_L} x2={W - PAD_R} y1={ty(0)} y2={ty(0)} stroke="var(--axis)" strokeWidth="1" />}

        {/* net worth */}
        <path d={area(rows, r => val(r, nwKey))} fill="var(--s1)" opacity=".14" />
        {showBase && baseRows && <path d={line(baseRows, r => val(r, nwKey), ty)} fill="none" stroke="var(--axis)" strokeWidth="2" strokeDasharray="6 5" />}
        <path d={line(rows, r => val(r, nwKey), ty)} fill="none" stroke="var(--s1)" strokeWidth="2.6" strokeLinejoin="round" />
        {/* investable (money you can spend) as thin bars */}
        {rows.map(r => { const v = val(r, 'investable'); const h = ty(Math.max(0, vMin)) - ty(v)
          return <rect key={`i${r.year}`} x={x(r.year) - 1.5} width="3" y={h >= 0 ? ty(v) : ty(Math.max(0, vMin))} height={Math.abs(h)} fill={v < 0 ? 'rgb(var(--bad))' : 'var(--s3)'} opacity=".55" /> })}

        {/* cash flow */}
        {showBase && baseRows && <path d={line(baseRows, r => cf(r).out, by)} fill="none" stroke="var(--s2)" strokeWidth="1.5" strokeDasharray="5 4" opacity=".55" />}
        <path d={line(rows, r => cf(r).inc, by)} fill="none" stroke="var(--s3)" strokeWidth="2.2" />
        <path d={line(rows, r => cf(r).out, by)} fill="none" stroke="var(--s2)" strokeWidth="2.2" />

        {/* ghost (dragging a new decision from the palette) */}
        {ghostYear != null && <g pointerEvents="none">
          <line x1={x(ghostYear)} x2={x(ghostYear)} y1={0} y2={botB} stroke={ghostColor || 'var(--s1)'} strokeWidth="2" strokeDasharray="4 3" />
          <rect x={x(ghostYear) - 40} y={topY + 4} width="80" height="20" rx="10" fill={ghostColor || 'var(--s1)'} />
          <text x={x(ghostYear)} y={topY + 18} textAnchor="middle" fontSize="11.5" fontWeight="600" fill="#fff">{ghostYear} · {ageOf(ghostYear)}</text></g>}

        {/* markers */}
        {placed.map(f => {
          const lx = x(f.year)
          const fy = 4 + f.row * (FLAG_H + FLAG_GAP)
          const active = drag?.id === f.id
          return (
            <g key={f.id} className={f.draggable ? 'outline-none' : ''} tabIndex={f.draggable ? 0 : -1} role={f.draggable ? 'slider' : undefined}
              aria-label={f.text} aria-valuenow={f.year} onKeyDown={e => onKey(e, f)}>
              <line x1={lx} x2={lx} y1={fy + FLAG_H} y2={botB} stroke={f.color} strokeWidth={active ? 2.5 : 1.6} strokeDasharray={f.dashed ? '5 4' : undefined} />
              {f.draggable && <rect x={lx - 6} width="12" y={fy + FLAG_H} height={botB - fy - FLAG_H} fill="transparent" style={{ cursor: 'ew-resize' }} onPointerDown={e => start(e, f)} />}
              <g onPointerDown={e => start(e, f)} style={{ cursor: f.draggable ? (active ? 'grabbing' : 'grab') : 'pointer' }}>
                <rect x={f.fx} y={fy} width={f.fw} height={FLAG_H} rx="6" fill={f.color} opacity={active ? 1 : 0.92}
                  stroke={active ? 'var(--chart-surface)' : 'none'} strokeWidth="2" />
                <text x={f.fx + 8} y={fy + 15} fontSize="11.5" fontWeight="600" fill="#fff">{f.text.length > 44 ? f.text.slice(0, 43) + '…' : f.text}</text>
                {f.draggable && <text x={f.fx + f.fw - 9} y={fy + 15} fontSize="11" fill="#fff" opacity=".8" textAnchor="middle">⇔</text>}
              </g>
            </g>)
        })}

        {/* hover */}
        {hr && <line x1={x(hr.year)} x2={x(hr.year)} y1={topY} y2={botB} stroke="var(--axis)" strokeWidth="1" opacity=".6" pointerEvents="none" />}
      </svg>

      {drag && (
        <div className="pointer-events-none absolute top-1 right-2 rounded-lg bg-ink text-bg text-[12.5px] font-semibold px-2.5 py-1 shadow-lg">
          {drag.year} · {ageOf(drag.year)}
        </div>)}
      {hr && (
        <div className="pointer-events-none absolute right-2 rounded-lg border border-line bg-surface/95 shadow-lg px-3 py-2 text-[12.5px] min-w-[190px]"
          style={{ top: bandH + 6 }}>
          <div className="font-semibold mb-1">{hr.year} · {ageOf(hr.year)}</div>
          <Row c="var(--s1)" l="Net worth" v={money(val(hr, 'net_worth'))} />
          {showBase && hb && <Row c="var(--axis)" l="Your plan" v={money(val(hb, 'net_worth'))} dashed />}
          <Row c="var(--s3)" l="Investable" v={money(val(hr, 'investable'))} />
          <Row c="var(--s3)" l="Money in" v={money(cf(hr).inc)} />
          <Row c="var(--s2)" l="Spending + taxes" v={money(cf(hr).out)} />
        </div>)}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 pt-1 text-[12px] text-ink2">
        <Leg c="var(--s1)" l="Net worth with decisions" />
        {showBase && <Leg c="var(--axis)" l="Your plan" dashed />}
        <Leg c="var(--s3)" l="Investable (bars) · money in" />
        <Leg c="var(--s2)" l="Spending + taxes" />
        <span className="text-muted ml-auto">Drag a flag left or right to change when it happens</span>
      </div>
    </div>
  )
})

const Row = ({ c, l, v, dashed }: { c: string; l: string; v: string; dashed?: boolean }) => (
  <div className="flex items-center gap-2"><span className="w-3 h-0.5" style={{ background: c, opacity: dashed ? 0.6 : 1 }} />
    <span className="text-ink2 flex-1">{l}</span><span className="tnum font-medium">{v}</span></div>)
const Leg = ({ c, l, dashed }: { c: string; l: string; dashed?: boolean }) => (
  <span className="flex items-center gap-1.5"><svg width="18" height="6"><line x1="0" x2="18" y1="3" y2="3" stroke={c} strokeWidth="2.4" strokeDasharray={dashed ? '4 3' : undefined} /></svg>{l}</span>)
