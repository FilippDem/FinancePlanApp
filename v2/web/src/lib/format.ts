export function money(v: number | null | undefined, opts: { compact?: boolean; sign?: boolean } = {}): string {
  if (v === null || v === undefined || !isFinite(v)) return '—'
  const { compact = true, sign = false } = opts
  const a = Math.abs(v)
  const s = v < 0 ? '−' : sign && v > 0 ? '+' : ''
  if (compact && a >= 1e9) return `${s}$${(a / 1e9).toFixed(2)}B`
  if (compact && a >= 1e6) return `${s}$${(a / 1e6).toFixed(a >= 1e7 ? 1 : 2)}M`
  if (compact && a >= 1e4) return `${s}$${Math.round(a / 1e3)}k`
  return `${s}$${Math.round(a).toLocaleString('en-US')}`
}
export const moneyFull = (v: number | null | undefined) => money(v, { compact: false })
export const pct = (v: number | null | undefined, d = 1) =>
  v === null || v === undefined || !isFinite(v) ? '—' : `${(v * 100).toFixed(d)}%`
export const axisMoney = (v: number) => {
  const a = Math.abs(v)
  const s = v < 0 ? '−' : ''
  if (a >= 1e9) return `${s}$${(a / 1e9).toFixed(1)}B`
  if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(a >= 1e7 ? 0 : 1)}M`
  if (a >= 1e3) return `${s}$${Math.round(a / 1e3)}k`
  return `${s}$${a}`
}
export const clsx = (...xs: any[]) => xs.filter(Boolean).join(' ')
