import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Info } from 'lucide-react'
import { Curve, getCurve, levelAt, sum, xForTotal, describe } from '../lib/spending'
import { money, clsx } from '../lib/format'

export interface Milestone { x: number; label: string; desc: string; total: number }

/** Milestones shown on the track: BLS income groups, the local average, the US average and the old app's levels. */
export function milestones(c: Curve): Milestone[] {
  const out: Milestone[] = c.anchors.map(a => a.key === 'all'
    ? { x: a.x, label: `${c.location} avg`, desc: `Average US household at ${c.location} prices`, total: a.total }
    : { x: a.x, label: a.label, desc: a.desc, total: a.total })
  if (c.basis !== 'us' && c.us_average_total) {
    const x = xForTotal(c, c.us_average_total)
    out.push({ x, label: 'US avg', desc: 'Average US household at US-average prices', total: c.us_average_total })
  }
  return out.sort((a, b) => a.x - b.x)
}

export function useCurve(location: string, year: number, inflation: number) {
  const [c, setC] = useState<Curve | null>(null)
  useEffect(() => {
    let live = true
    setC(null)
    getCurve(location || 'Seattle', year, inflation).then(v => live && setC(v)).catch(() => {})
    return () => { live = false }
  }, [location, year, inflation])
  return c
}

/** Source ids behind a curve, in citation order: BLS spending always, plus the price data for the place. */
export const curveSources = (c: Curve | null) => ['bls_cex_2022', 'bls_cex_2024', ...(c?.basis === 'country' ? ['worldbank_pli'] : c?.basis === 'us' ? [] : ['bea_rpp_2024'])]

export function SpendingSlider({ curve, value, onChange, adults = 1, compact, cite }:
  { curve: Curve | null; value: number; onChange: (x: number) => void; adults?: number; compact?: boolean; cite?: React.ReactNode }) {
  const ms = useMemo(() => (curve ? milestones(curve) : []), [curve])
  const per = curve ? sum(levelAt(curve, value)) : 0
  // stagger labels into rows so they never overlap (greedy, using the measured track width)
  const trackRef = useRef<HTMLDivElement>(null)
  const [w, setW] = useState(600)
  useEffect(() => {
    const el = trackRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setW(el.clientWidth || 600))
    ro.observe(el); setW(el.clientWidth || 600)
    return () => ro.disconnect()
  }, [curve])
  const rows = useMemo(() => {
    const ends: number[] = []           // right edge (px) of the last label in each row
    return ms.map(m => {
      const width = Math.max(m.label.length * 6.4, 40) + 10
      const center = (m.x / 100) * w
      const left = m.x > 93 ? center - width : m.x < 7 ? center : center - width / 2
      let r = ends.findIndex(e => left > e)
      if (r === -1) { r = ends.length; ends.push(0) }
      ends[r] = left + width
      return r
    })
  }, [ms, w])
  const nRows = Math.max(1, ...rows.map(r => r + 1))
  if (!curve) return <div className="h-40 flex items-center justify-center text-sm text-muted">Loading spending data…</div>
  const pct = (x: number) => `${x}%`
  return (
    <div>
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className={clsx('font-semibold tnum tracking-tight', compact ? 'text-[26px]' : 'text-[32px]')}>{money(per * adults, { compact: false })}</span>
        <span className="text-sm text-muted">per year{adults > 1 ? ` for ${adults} adults` : ' per adult'} · {money(per * adults / 12, { compact: false })}/mo</span>
      </div>
      <div className="text-[13px] text-ink2 mt-0.5">{(ms.find(m => Math.abs(m.x - value) < 1.5)?.desc) ?? describe(curve, value).replace(' avg', ' average')}</div>
      <div className="relative mt-4 mb-2 px-1">
        <input type="range" min={0} max={100} step={1} value={value} onChange={e => onChange(+e.target.value)}
          aria-label="Spending level" className="w-full accent-[rgb(var(--accent))] relative z-10" />
        <div ref={trackRef} className="relative mt-1" style={{ height: nRows * 30 + 6 }}>
          {ms.map((m, i) => (
            <button key={m.label + m.x} type="button" title={`${m.desc}: ${money(m.total * adults, { compact: false })}/yr`}
              onClick={() => onChange(Math.round(m.x))}
              className={clsx('absolute flex flex-col group', m.x > 93 ? '-translate-x-full items-end' : m.x < 7 ? 'items-start' : '-translate-x-1/2 items-center')}
              style={{ left: pct(m.x), top: rows[i] * 30 }}>
              <span className={clsx('w-px', m.label.startsWith('Old app') ? 'bg-muted/50' : 'bg-ink2/60')} style={{ height: 8 + rows[i] * 30, marginTop: -rows[i] * 30 }} />
              <span className={clsx('text-[11px] whitespace-nowrap leading-4 group-hover:text-accent', Math.abs(m.x - value) < 1.5 ? 'text-accent font-semibold' : m.label.startsWith('Old app') ? 'text-muted' : 'text-ink2')}>
                {m.label}</span>
              <span className="text-[10.5px] text-muted tnum leading-3">{money(m.total * adults)}</span>
            </button>
          ))}
        </div>
      </div>
      {!compact && <p className="text-[12px] text-muted flex gap-1.5"><Info size={13} className="shrink-0 mt-0.5" />
        <span>{curve.note}{cite}. Personal spending only: housing, kids, healthcare premiums and big purchases are separate. The "Old app" marks are the v0.8 templates, about twice what BLS data shows.</span></p>}
    </div>
  )
}
