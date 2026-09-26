import { api } from './api'

export interface Anchor { x: number; key: string; label: string; desc: string; total: number; cats: Record<string, number> }
export interface Curve { location: string; basis: string; note: string; anchors: Anchor[]; us_average_total: number }

const cache = new Map<string, Promise<Curve>>()
export function getCurve(location: string, year: number, inflation: number): Promise<Curve> {
  const k = `${location}|${year}|${inflation}`
  if (!cache.has(k)) cache.set(k, api.spendingCurve(location, year, inflation).catch(e => { cache.delete(k); throw e }))
  return cache.get(k)!
}

/** Per-adult categories at slider position x (same math as calibrate.level_at). */
export function levelAt(c: Curve, x: number): Record<string, number> {
  const a = c.anchors
  x = Math.max(0, Math.min(100, x))
  if (x <= a[0].x) {
    const k = 0.6 + 0.4 * (x / a[0].x)
    return Object.fromEntries(Object.entries(a[0].cats).map(([cat, v]) => [cat, v * k]))
  }
  for (let i = 1; i < a.length; i++) {
    if (x <= a[i].x) {
      const lo = a[i - 1], hi = a[i]
      const w = (x - lo.x) / (hi.x - lo.x)
      const cats = new Set([...Object.keys(lo.cats), ...Object.keys(hi.cats)])
      return Object.fromEntries([...cats].map(cat => [cat, (lo.cats[cat] || 0) * (1 - w) + (hi.cats[cat] || 0) * w]))
    }
  }
  return { ...a[a.length - 1].cats }
}

export const sum = (o: Record<string, number>) => Object.values(o || {}).reduce((s, v) => s + (+v || 0), 0)
export const round10 = (v: number) => Math.round(v / 10) * 10

/** Position whose total per adult equals `total` (inverse of the curve). */
export function xForTotal(c: Curve, total: number): number {
  let lo = 0, hi = 100
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2
    if (sum(levelAt(c, mid)) < total) lo = mid; else hi = mid
  }
  return (lo + hi) / 2
}

/** Move the slider: untouched categories follow the curve; ones the user edited keep their
 *  proportion to the curve; custom categories scale with the total. */
export function rescale(current: Record<string, number>, c: Curve, fromX: number | null, toX: number): Record<string, number> {
  const next = levelAt(c, toX)
  if (fromX === null || fromX === undefined || !current || !Object.keys(current).length)
    return Object.fromEntries(Object.entries(next).map(([k, v]) => [k, round10(v)]))
  const prev = levelAt(c, fromX)
  const tRatio = sum(next) / Math.max(sum(prev), 1)
  const out: Record<string, number> = {}
  for (const [k, v] of Object.entries(current)) {
    if (k in next) {
      const p = prev[k] || 0
      out[k] = Math.abs(v - round10(p)) <= 10 ? round10(next[k]) : round10(p > 0 ? v * next[k] / p : next[k])
    } else out[k] = round10(v * tRatio)
  }
  for (const k of Object.keys(next)) if (!(k in out)) out[k] = round10(next[k])
  return out
}

export function strategyFor(x: number) {
  return x < 32 ? 'Conservative (statistical)' : x < 70 ? 'Average (statistical)' : 'High-end (statistical)'
}

/** Label for where x sits between milestones. */
export function describe(c: Curve, x: number) {
  const a = c.anchors
  const exact = a.find(m => Math.abs(m.x - x) < 1.5)
  if (exact) return exact.desc
  const hi = a.find(m => m.x > x)
  const lo = [...a].reverse().find(m => m.x < x)
  if (!lo) return `Below ${hi!.label.toLowerCase()}`
  if (!hi) return `Above ${lo.label.toLowerCase()}`
  return `Between ${lo.label} and ${hi.label}`
}
