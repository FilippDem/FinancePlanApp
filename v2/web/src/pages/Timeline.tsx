import React, { useMemo, useState } from 'react'
import { usePlan } from '../lib/store'
import { money } from '../lib/format'
import { Card, PageHeader, Segmented } from '../components/ui'
import { S } from '../components/charts'

const LANES: { key: string; label: string; types: string[] }[] = [
  { key: 'career', label: 'Career & retirement', types: ['job', 'retire', 'ss'] },
  { key: 'kids', label: 'Kids', types: ['birth', 'college'] },
  { key: 'homes', label: 'Homes & moves', types: ['house_buy', 'house_sell', 'house_status', 'move'] },
  { key: 'money', label: 'Big purchases', types: ['purchase', 'recurring'] },
]
const YW = 30

export default function Timeline() {
  const { plan, proj, names, single } = usePlan()
  const [range, setRange] = useState<'30' | 'all'>('30')
  const events: any[] = proj?.events || []
  const start = plan.current_year
  const end = range === '30' ? start + 30 : (proj?.summary?.end_year ?? start + 60)
  const years = Array.from({ length: end - start + 1 }, (_, i) => start + i)
  const vis = events.filter(e => e.year >= start && e.year <= end)
  const width = years.length * YW

  const lanes = useMemo(() => LANES.map((l, li) => {
    const evs = vis.filter(e => l.types.includes(e.type) && !(e.type === 'recurring' && (e.amount ?? 0) < 10000))
      .sort((a, b) => a.year - b.year)
    // greedy row packing so labels never overlap
    const ends: number[] = []
    const placed = evs.map(e => {
      const x = (e.year - start) * YW
      const w = 22 + e.label.length * 6.6
      let row = ends.findIndex(end => end < x)
      if (row === -1) { row = ends.length; ends.push(0) }
      ends[row] = x + w
      return { ...e, x, row }
    })
    return { ...l, color: S[li], placed, rows: Math.max(1, ends.length) }
  }), [vis, start])

  const decades = useMemo(() => {
    const g: Record<string, any[]> = {}
    events.forEach(e => (g[`${Math.floor(e.year / 10) * 10}s`] ||= []).push(e))
    return g
  }, [events])

  return (
    <div className="space-y-5">
      <PageHeader title="Life timeline" subtitle="Every event the plan knows about, from all pages"
        actions={<Segmented value={range} onChange={setRange} options={[{ value: '30', label: 'Next 30 years' }, { value: 'all', label: 'Whole plan' }]} />} />
      <Card pad={false}>
        <div className="flex">
          <div className="w-44 shrink-0 border-r border-line">
            <div className="h-12 px-4 flex items-end pb-2 text-[12px] text-muted">Ages</div>
            {lanes.map(l => (
              <div key={l.key} className="px-4 flex items-center gap-2 text-sm font-medium border-t border-line" style={{ height: 22 + l.rows * 26 }}>
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: l.color }} />{l.label}
              </div>
            ))}
          </div>
          <div className="overflow-x-auto flex-1">
            <div style={{ width }} className="relative">
              <div className="h-12 relative">
                {years.map((y, i) => (i % 5 === 0) && (
                  <div key={y} className="absolute top-1.5 text-[11px] text-muted tnum" style={{ left: i * YW }}>
                    <div className="font-medium text-ink2">{y}</div>
                    <div>{plan.parentX_age + (y - start)}{!single && `/${plan.parentY_age + (y - start)}`}</div>
                  </div>
                ))}
              </div>
              {lanes.map(l => (
                <div key={l.key} className="relative border-t border-line" style={{ height: 22 + l.rows * 26 }}>
                  {years.map((y, i) => i % 5 === 0 && <div key={y} className="absolute top-0 bottom-0 border-l border-line/60" style={{ left: i * YW + 4 }} />)}
                  {l.placed.map((e: any, k: number) => (
                    <div key={k} className="absolute flex items-center gap-1.5 whitespace-nowrap" style={{ left: e.x, top: 11 + e.row * 26 }}
                      title={`${e.year}: ${e.label}${e.amount ? ' · ' + money(e.amount) : ''}`}>
                      <span className="w-2.5 h-2.5 rounded-full ring-2 ring-surface shrink-0" style={{ background: l.color }} />
                      <span className="text-[12px] text-ink2">{e.label}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Object.entries(decades).map(([d, evs]) => (
          <Card key={d} title={d}>
            <ul className="space-y-1.5 text-sm">
              {evs.map((e, i) => (
                <li key={i} className="flex gap-3"><span className="tnum text-muted w-10">{e.year}</span><span className="flex-1">{e.label}</span>
                  {e.amount ? <span className="tnum text-ink2">{money(e.amount)}</span> : null}</li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  )
}
