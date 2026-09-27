import React, { useMemo, useState } from 'react'
import { usePlan } from '../lib/store'
import { S } from './charts'
import { Segmented } from './ui'

type Seg = { label: string; sub?: string; from: number; to: number; color: string; faded?: boolean }

/** Merge consecutive years with the same label into bars. */
function segs(years: number[], labelOf: (y: number, i: number) => string, colorOf: (label: string) => string, subOf?: (y: number, i: number) => string): Seg[] {
  const out: Seg[] = []
  years.forEach((y, i) => {
    const l = labelOf(y, i), s = subOf ? subOf(y, i) : undefined
    const last = out[out.length - 1]
    if (last && last.label === l && last.sub === s && last.to === y - 1) last.to = y
    else out.push({ label: l, sub: s, from: y, to: y, color: colorOf(l) })
  })
  return out
}

function Lane({ name, items, start, end }: { name: string; items: Seg[]; start: number; end: number }) {
  const span = end - start + 1
  return (
    <div className="flex items-stretch gap-2">
      <div className="w-24 shrink-0 text-[12px] text-muted pt-2">{name}</div>
      <div className="flex-1 flex h-10 rounded-lg overflow-hidden border border-line">
        {items.map((s, i) => (
          <div key={i} title={`${s.label}${s.sub ? ` · ${s.sub}` : ''} · ${s.from}–${s.to}`}
            className="flex flex-col justify-center px-2 text-[11.5px] leading-tight overflow-hidden whitespace-nowrap border-r border-white/30 last:border-r-0"
            style={{ width: `${((s.to - s.from + 1) / span) * 100}%`, background: s.color, color: s.faded ? 'rgb(var(--ink2))' : 'white' }}>
            <span className="font-semibold truncate">{s.label}</span>
            <span className="truncate opacity-90">{s.sub ? `${s.sub} · ` : ''}{s.from}{s.to !== s.from ? `–${s.to}` : ''}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Where the family lives, year by year: city/country (and lifestyle), which home (or renting), and kids at home. */
export function LivingTimeline() {
  const { plan, proj } = usePlan()
  const [win, setWin] = useState<'20' | '40' | 'all'>(() => { try { return (localStorage.getItem('fp_live_win') as any) || '40' } catch { return '40' } })
  const all: any[] = proj?.rows || []
  const rows: any[] = win === 'all' ? all : all.slice(0, +win)
  const data = useMemo(() => {
    if (!rows.length) return null
    const years = rows.map(r => r.year)
    const start = years[0], end = years[years.length - 1]
    const stl: any[] = plan.state_timeline || []
    const locAt = (y: number) => [...stl].reverse().find(e => e.year <= y) || stl[0] || { state: '—', spending_strategy: '' }
    const locColors: Record<string, string> = {}
    let k = 0
    const colorLoc = (l: string) => (locColors[l] ??= S[k++ % 8])
    const where = segs(years, y => locAt(y).state, colorLoc, y => String(locAt(y).spending_strategy || '').replace(' (statistical)', ''))
    const homeColors: Record<string, string> = {}
    let h = 3
    const colorHome = (l: string) => l === 'Renting' ? 'rgb(var(--sunken))' : (homeColors[l] ??= S[h++ % 8])
    const home = segs(years, (_, i) => {
      const hs: any[] = rows[i].details?.houses || []
      const live = hs.find(x => x.status === 'Own_Live')
      return live ? live.name : 'Renting'
    }, colorHome, (_, i) => {
      const hs: any[] = rows[i].details?.houses || []
      const rented = hs.filter(x => x.status === 'Own_Rent').length
      return rented ? `+${rented} rented out` : ''
    }).map(s => ({ ...s, faded: s.label === 'Renting', sub: s.sub || undefined }))
    const kids: any[] = plan.children_list || []
    const kidsAt = (y: number) => kids.filter(c => y - c.birth_year >= 0 && y - c.birth_year < 18).length
    const kidLane = segs(years, y => { const n = kidsAt(y); return n ? `${n} kid${n === 1 ? '' : 's'} at home` : 'No kids at home' },
      l => l.startsWith('No') ? 'rgb(var(--sunken))' : S[6]).map(s => ({ ...s, faded: s.label.startsWith('No') }))
    const moves = stl.filter((e, i) => i > 0 && e.year > start && e.state !== stl[i - 1].state)
    return { start, end, where, home, kidLane, moves }
  }, [rows.length, all, JSON.stringify(plan.state_timeline), JSON.stringify(plan.children_list)])
  if (!data) return null
  return (
    <div className="space-y-2">
      <div className="flex justify-end"><Segmented value={win} onChange={v => { setWin(v); try { localStorage.setItem('fp_live_win', v) } catch { /* */ } }}
        options={[{ value: '20', label: 'Next 20 years' }, { value: '40', label: '40 years' }, { value: 'all', label: 'Whole plan' }]} /></div>
      <Lane name="Where" items={data.where} start={data.start} end={data.end} />
      <Lane name="Home" items={data.home} start={data.start} end={data.end} />
      {(plan.children_list || []).length > 0 && <Lane name="Kids" items={data.kidLane} start={data.start} end={data.end} />}
      <div className="flex justify-between text-[11.5px] text-muted tnum" style={{ paddingLeft: '6.5rem' }}>
        {Array.from({ length: 7 }, (_, i) => Math.round(data.start + (data.end - data.start) * i / 6)).map(y => <span key={y}>{y}</span>)}
      </div>
    </div>
  )
}
