import React, { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Star } from 'lucide-react'
import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Scatter, PieChart, Pie, Cell, Sankey,
} from 'recharts'
import { money, pct, axisMoney, clsx } from '../lib/format'
import { Card, Badge, Select } from './ui'
import { S } from './charts'

const EVENT_TYPES: Record<string, string> = { retire: 'Retirement', job: 'Job change', college: 'College starts', college_end: 'College ends', birth: 'Birth', house_buy: 'Home purchase', house_sell: 'Home sale', move: 'Move' }

/** Everything v0.8's Analysis → Cashflow tab showed, rebuilt: timeline with surplus/deficit and events,
 *  a year drill-down (pies, Sankey, taxes, complete expense summary), critical years and life stages. */
export function CashflowExplorer({ rows, rawRows, events, names, single, today }:
  { rows: any[]; rawRows: any[]; events: any[]; names: [string, string]; single: boolean; today: boolean }) {
  const [year, setYear] = useState<number>(rows[0]?.year)
  const idx = rows.findIndex(r => r.year === year)
  const r = rows[Math.max(0, idx)]
  const raw = rawRows[Math.max(0, idx)]
  const f = today ? raw?.infl_index || 1 : 1

  // college end events are implied (age 22); add them for markers
  const evs = useMemo(() => {
    const out = [...(events || [])]
    for (const e of events || []) if (e.type === 'college') out.push({ ...e, type: 'college_end', year: e.year + 4, label: e.label.replace('starts college', 'finishes college') })
    return out.filter(e => ['retire', 'job', 'college', 'college_end', 'house_buy', 'house_sell', 'move'].includes(e.type))
  }, [events])
  const evByYear = useMemo(() => { const m: Record<number, any[]> = {}; evs.forEach(e => { (m[e.year] = m[e.year] || []).push(e) }); return m }, [evs])

  const data = rows.map(x => {
    const out = x.total_expenses + x.taxes
    const inc = x.total_income + x.sale_proceeds
    return { year: x.year, income: inc, outflow: out, surplus: inc >= out ? [out, inc] : [inc, inc], deficit: out > inc ? [inc, out] : [out, out],
      marker: evByYear[x.year] ? inc : null, markerLabel: (evByYear[x.year] || []).map(e => e.label).join(' · ') }
  })

  return (
    <div className="space-y-4">
      <Card title="Cash flow timeline" subtitle="Money in vs money out (spending + taxes). Green = surplus saved, red = drawn from savings. Stars mark life events; click any year for details.">
        <div className="flex flex-wrap gap-4 text-[12.5px] text-ink2 mb-2">
          <span className="flex items-center gap-1.5"><span className="w-3.5 h-[2px]" style={{ background: S[0] }} />Money in</span>
          <span className="flex items-center gap-1.5"><span className="w-3.5 h-[2px]" style={{ background: S[1] }} />Money out</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-good/40" />Surplus</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-bad/40" />Deficit</span>
          <span className="flex items-center gap-1.5"><Star size={12} className="text-warn fill-warn" />Life event</span>
        </div>
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={data} margin={{ top: 10, right: 12, left: 0, bottom: 0 }} onClick={(e: any) => e?.activeLabel && setYear(+e.activeLabel)}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis dataKey="year" tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" minTickGap={24} />
            <YAxis tickLine={false} axisLine={false} tickFormatter={axisMoney} width={56} fontSize={11} stroke="var(--axis)" />
            <Tooltip content={({ active, payload, label }: any) => active && payload?.length ? (
              <div className="bg-surface border border-line rounded-lg shadow-lg px-3 py-2 text-[12.5px]">
                <div className="font-semibold">{label}</div>
                <div>In {money(payload[0].payload.income)} · Out {money(payload[0].payload.outflow)}</div>
                <div className={payload[0].payload.income >= payload[0].payload.outflow ? 'text-good' : 'text-bad'}>{money(payload[0].payload.income - payload[0].payload.outflow, { sign: true })}</div>
                {payload[0].payload.markerLabel && <div className="text-warn mt-1">★ {payload[0].payload.markerLabel}</div>}
              </div>) : null} />
            <Area dataKey="surplus" stroke="none" fill="rgb(var(--good))" fillOpacity={0.25} isAnimationActive={false} />
            <Area dataKey="deficit" stroke="none" fill="rgb(var(--bad))" fillOpacity={0.25} isAnimationActive={false} />
            <Line dataKey="income" stroke={S[0]} strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line dataKey="outflow" stroke={S[1]} strokeWidth={2} dot={false} isAnimationActive={false} />
            <Scatter dataKey="marker" isAnimationActive={false} shape={(p: any) => p.payload.marker == null ? <g /> :
              <path transform={`translate(${p.cx},${p.cy})`} d="M0,-8 L2.4,-2.5 8,-2.5 3.5,1 5,7 0,3.6 -5,7 -3.5,1 -8,-2.5 -2.4,-2.5Z" fill="var(--s4)" stroke="var(--chart-surface)" strokeWidth={1} />} />
            <ReferenceLine x={year} stroke="rgb(var(--ink))" strokeDasharray="3 3" />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      {r && raw && <YearPanel r={r} raw={raw} f={f} names={names} single={single} year={year} setYear={setYear} years={rows.map(x => x.year)} evs={evByYear[year] || []} />}

      <CriticalYears rows={rows} rawRows={rawRows} evByYear={evByYear} single={single} onPick={setYear} />
      <LifeStages rows={rows} />
    </div>
  )
}

export function Donut({ items, title }: { items: { name: string; value: number }[]; title: string }) {
  const total = items.reduce((a, b) => a + b.value, 0)
  return (
    <div>
      <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-1">{title}</div>
      <div className="grid grid-cols-[150px_1fr] gap-3 items-center">
        <ResponsiveContainer width="100%" height={150}>
          <PieChart><Pie data={items} dataKey="value" nameKey="name" innerRadius={42} outerRadius={70} paddingAngle={1} isAnimationActive={false}>
            {items.map((_, i) => <Cell key={i} fill={S[i % 8]} stroke="var(--chart-surface)" />)}</Pie>
            <Tooltip formatter={(v: any) => money(v, { compact: false })} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} /></PieChart>
        </ResponsiveContainer>
        <div className="space-y-1 text-[12.5px]">
          {items.map((it, i) => (
            <div key={it.name} className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: S[i % 8] }} />
              <span className="flex-1 truncate">{it.name}</span><span className="tnum">{money(it.value)}</span>
              <span className="text-muted w-9 text-right tnum">{total ? Math.round(it.value / total * 100) : 0}%</span></div>))}
          <div className="flex justify-between border-t border-line pt-1 font-medium"><span>Total</span><span className="tnum">{money(total, { compact: false })}</span></div>
        </div>
      </div>
    </div>
  )
}

function YearPanel({ r, raw, f, names, single, year, setYear, years, evs }: any) {
  const d = raw.details || {}
  const n2 = names[1] || 'Partner'
  const income = [
    { name: `${names[0]} wages`, value: r.wages1 }, ...(single ? [] : [{ name: `${n2} wages`, value: r.wages2 }]),
    { name: 'Social Security', value: r.ss_income }, { name: 'Rental income', value: r.rent_income }, { name: 'Home sale', value: r.sale_proceeds },
    { name: 'Investment growth', value: Math.max(0, r.investment_growth || 0) },
  ].filter(x => x.value > 0.5)
  const spend = [
    { name: 'Taxes', value: r.taxes }, { name: `${names[0]} living`, value: r.exp_person1 }, ...(single ? [] : [{ name: `${n2} living`, value: r.exp_person2 }]),
    { name: 'Household', value: r.exp_family }, { name: 'Children', value: r.exp_children }, { name: 'Healthcare', value: r.exp_healthcare },
    { name: 'Housing', value: r.exp_housing }, { name: 'Recurring', value: r.exp_recurring }, { name: 'One-time', value: r.exp_purchases },
    { name: 'Down payments', value: r.down_payment }, { name: '401(k)/HSA saving', value: r.contrib_pretax },
  ].filter(x => x.value > 0.5)
  const cashIn = income.filter(x => x.name !== 'Investment growth').reduce((a, b) => a + b.value, 0)
  const cashOut = spend.reduce((a, b) => a + b.value, 0)
  const net = cashIn - cashOut
  const inCollege = (d.children || []).filter((c: any) => c.in_college).map((c: any) => c.name)

  // Sankey: income sources -> "Money in" -> spending categories (+ savings or a withdrawal source)
  const sankey = useMemo(() => {
    const srcs = income.filter(x => x.name !== 'Investment growth')
    const nodes: any[] = [...srcs.map(s => ({ name: s.name })), ...(net < 0 ? [{ name: 'From savings' }] : []), { name: 'Money in' },
      ...spend.map(s => ({ name: s.name })), ...(net > 0 ? [{ name: 'Added to savings' }] : [])]
    const hub = srcs.length + (net < 0 ? 1 : 0)
    const links: any[] = srcs.map((s, i) => ({ source: i, target: hub, value: s.value }))
    if (net < 0) links.push({ source: srcs.length, target: hub, value: -net })
    spend.forEach((s, i) => links.push({ source: hub, target: hub + 1 + i, value: s.value }))
    if (net > 0) links.push({ source: hub, target: hub + 1 + spend.length, value: net })
    return { nodes, links: links.filter(l => l.value > 0.5) }
  }, [r])

  const [openGrp, setOpenGrp] = useState<Record<string, boolean>>({})
  const groups: { title: string; items: { label: string; value: number }[] }[] = []
  const add = (title: string, items: { label: string; value: number }[]) => { const it = items.filter(i => Math.abs(i.value) >= 0.5); if (it.length) groups.push({ title, items: it }) }
  const liv = d.living || {}
  add(`${names[0]} living`, Object.entries(liv.p1 || {}).map(([k, v]: any) => ({ label: k, value: v / f })))
  if (!single) add(`${n2} living`, Object.entries(liv.p2 || {}).map(([k, v]: any) => ({ label: k, value: v / f })))
  add('Household', Object.entries(liv.shared || {}).map(([k, v]: any) => ({ label: k, value: v / f })))
  for (const c of d.children || []) add(`${c.name} (age ${c.age}${c.in_college ? ', in college' : ''})`, Object.entries(c.cats || {}).map(([k, v]: any) => ({ label: k, value: v / f })))
  add('Healthcare', (d.healthcare || []).map((h: any) => ({ label: `${h.name} · ${h.who}`, value: h.amount / f })))
  for (const h of d.houses || []) if (h.total || h.proceeds)
    add(`Home: ${h.name}`, [['Mortgage P&I', h.mortgage_pi], ['PMI', h.pmi], ['HOA', h.hoa], ['Property tax', h.property_tax], ['Insurance', h.insurance],
      ['Maintenance', h.maintenance], ['Upkeep', h.upkeep]].map(([l, v]: any) => ({ label: l, value: (v || 0) / f })))
  add('Recurring', (d.recurring || []).map((x: any) => ({ label: x.name, value: x.amount / f })))
  add('One-time', (d.purchases || []).map((x: any) => ({ label: x.name, value: x.amount / f })))
  add('Taxes', [['Federal income tax', r.tax_federal], ['State income tax', r.tax_state], ['Social Security & Medicare (FICA)', r.tax_fica], ['Foreign income tax', r.tax_foreign]]
    .map(([l, v]: any) => ({ label: l, value: v })))
  const grand = groups.reduce((a, g) => a + g.items.reduce((s, i) => s + i.value, 0), 0)

  return (
    <Card title={`${year} in detail`} subtitle={`Ages ${r.age1}${single ? '' : ` / ${r.age2}`}${inCollege.length ? ` · in college: ${inCollege.join(', ')}` : ''}${evs.length ? ` · ${evs.map((e: any) => e.label).join(' · ')}` : ''}`}
      action={<div className="flex items-center gap-2">
        <button className="px-2 h-8 rounded-md border border-line text-sm" onClick={() => setYear(years[Math.max(0, years.indexOf(year) - 1)])}>‹</button>
        <div className="w-24"><Select value={year} options={years} onChange={setYear} /></div>
        <button className="px-2 h-8 rounded-md border border-line text-sm" onClick={() => setYear(years[Math.min(years.length - 1, years.indexOf(year) + 1)])}>›</button>
      </div>}>
      <div className="grid md:grid-cols-4 gap-3 mb-5">
        {[['Money in', cashIn], ['Money out', cashOut], [net >= 0 ? 'Saved' : 'Drawn from savings', net], ['Net worth (end of year)', r.net_worth]].map(([l, v]: any, i) => (
          <div key={l} className="rounded-lg bg-sunken/70 p-3"><div className="text-[12px] text-muted">{l}</div>
            <div className={clsx('text-[20px] font-semibold tnum', i === 2 && (v >= 0 ? 'text-good' : 'text-bad'))}>{money(v, { compact: false, sign: i === 2 })}</div></div>))}
      </div>
      <div className="grid lg:grid-cols-2 gap-6">
        <Donut items={income} title="Where money comes from" />
        <Donut items={spend} title="Where it goes" />
      </div>

      <div className="mt-6">
        <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-1">Money flow</div>
        {sankey.links.length > 1 && (
          <ResponsiveContainer width="100%" height={Math.max(260, 26 * Math.max(income.length, spend.length + 1))}>
            <Sankey data={sankey} nodePadding={14} nodeWidth={10} margin={{ left: 150, right: 170, top: 10, bottom: 10 }} iterations={0}
              link={{ stroke: 'var(--s1)', strokeOpacity: 0.25 } as any}
              node={({ x, y, width, height, index, payload }: any) => {
                const left = index < (sankey.nodes.findIndex((n: any) => n.name === 'Money in'))
                const hub = payload.name === 'Money in'
                return (
                  <g>
                    <rect x={x} y={y} width={width} height={height} fill={hub ? 'rgb(var(--ink))' : payload.name === 'Added to savings' ? 'rgb(var(--good))' : payload.name === 'From savings' ? 'rgb(var(--bad))' : 'var(--s1)'} rx={2} />
                    {!hub && <text x={left ? x - 6 : x + width + 6} y={y + height / 2} dy="0.35em" textAnchor={left ? 'end' : 'start'} fontSize={12} fill="rgb(var(--ink))">
                      {payload.name} <tspan fill="var(--axis)">{money(payload.value)}</tspan></text>}
                  </g>)
              }} />
          </ResponsiveContainer>)}
        <p className="text-[12.5px] text-ink2 mt-1">{net >= 0 ? `Net addition to savings: ${money(net, { compact: false })}` : `Savings cover a shortfall of ${money(-net, { compact: false })}`}
          {r.investment_growth ? `; investments ${r.investment_growth >= 0 ? 'grew' : 'cost'} ${money(Math.abs(r.investment_growth), { compact: false })} on top.` : '.'}</p>
      </div>

      <div className="grid lg:grid-cols-[1fr_320px] gap-6 mt-6">
        <div>
          <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-1">Complete expense summary</div>
          <div className="border border-line rounded-lg divide-y divide-line">
            {groups.map(g => {
              const sub = g.items.reduce((a, b) => a + b.value, 0)
              const open = openGrp[g.title]
              return (
                <div key={g.title}>
                  <button className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-sunken/60" onClick={() => setOpenGrp({ ...openGrp, [g.title]: !open })}>
                    {open ? <ChevronDown size={14} className="text-muted" /> : <ChevronRight size={14} className="text-muted" />}
                    <span className="flex-1 text-left font-medium">{g.title}</span><span className="tnum">{money(sub, { compact: false })}</span>
                    <span className="w-10 text-right text-[12px] text-muted tnum">{grand ? Math.round(sub / grand * 100) : 0}%</span>
                  </button>
                  {open && <div className="px-9 pb-2 space-y-0.5">{g.items.map(i => (
                    <div key={i.label} className="flex justify-between text-[13px]"><span className="text-ink2">{i.label}</span><span className="tnum">{money(i.value, { compact: false })}</span></div>))}</div>}
                </div>)
            })}
            <div className="flex justify-between px-3 py-2 text-sm font-semibold"><span>Total</span><span className="tnum">{money(grand, { compact: false })}</span></div>
          </div>
        </div>
        <div>
          <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-1">Taxes</div>
          <div className="space-y-1 text-sm">
            {[['Federal income tax', r.tax_federal], ['State income tax', r.tax_state], ['FICA', r.tax_fica], ['Foreign income tax', r.tax_foreign]].map(([l, v]: any) =>
              <div key={l} className="flex justify-between"><span className="text-ink2">{l}</span><span className="tnum">{money(v, { compact: false })}</span></div>)}
            <div className="flex justify-between border-t border-line pt-1 font-medium"><span>Total</span><span className="tnum">{money(r.taxes, { compact: false })}</span></div>
            <div className="flex justify-between"><span className="text-ink2">Effective rate</span><span className="tnum">{pct(raw.effective_tax_rate, 1)}</span></div>
            <div className="text-[12.5px] text-muted">Taxed as: {raw.location}{raw.col_factor && Math.abs(raw.col_factor - 1) > 0.01 ? ` · spending ×${raw.col_factor.toFixed(2)} vs today's location` : ''}</div>
          </div>
        </div>
      </div>
    </Card>
  )
}

function CriticalYears({ rows, rawRows, evByYear, single, onPick }: any) {
  const [all, setAll] = useState(false)
  const crit = rows.map((r: any, i: number) => {
    const raw = rawRows[i]
    const tags: string[] = []
    if (r.cashflow < 0 && (r.wages1 + r.wages2) > 0) tags.push('Negative cash flow while working')
    else if (r.cashflow < 0) tags.push('Drawing on savings')
    if (r.investable < 0) tags.push('Savings below zero')
    if (r.net_worth < 0) tags.push('Negative net worth')
    const ev = (evByYear[r.year] || []).map((e: any) => EVENT_TYPES[e.type] ? e.label : null).filter(Boolean)
    const college = (raw.details?.children || []).filter((c: any) => c.in_college).map((c: any) => c.name)
    return { r, tags, ev, college, important: tags.some(t => t !== 'Drawing on savings') || ev.length > 0 }
  }).filter((x: any) => x.important || (all && (x.tags.length || x.college.length)))
  return (
    <Card title="Critical years" subtitle="Years with a life event, a deficit while working, or savings/net worth below zero" pad={false}
      action={<label className="flex items-center gap-2 text-[12.5px] text-ink2"><input type="checkbox" checked={all} onChange={e => setAll(e.target.checked)} />Include all drawdown & college years</label>}>
      <div className="max-h-[420px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface"><tr className="text-left text-[12px] text-muted border-b border-line"><th className="px-5 py-2 font-medium">Year</th><th className="font-medium">Ages</th>
            <th className="font-medium text-right">Cash flow</th><th className="font-medium text-right">Savings</th><th className="font-medium text-right pr-4">Net worth</th><th className="font-medium">Events</th><th className="font-medium">In college</th></tr></thead>
          <tbody>{crit.map(({ r, tags, ev, college }: any) => (
            <tr key={r.year} className="border-b border-line last:border-0 hover:bg-sunken/50 cursor-pointer" onClick={() => onPick(r.year)}>
              <td className="px-5 py-1.5 tnum">{r.year}</td><td className="tnum">{r.age1}{single ? '' : `/${r.age2}`}</td>
              <td className={clsx('text-right tnum', r.cashflow < 0 && 'text-bad')}>{money(r.cashflow)}</td>
              <td className={clsx('text-right tnum', r.investable < 0 && 'text-bad')}>{money(r.investable)}</td>
              <td className={clsx('text-right tnum pr-4', r.net_worth < 0 && 'text-bad')}>{money(r.net_worth)}</td>
              <td className="text-[12.5px]">{[...ev, ...tags].map((t: string) => <span key={t} className="inline-block mr-1 mb-0.5"><Badge tone={tags.includes(t) ? 'bad' : 'accent'}>{t}</Badge></span>)}</td>
              <td className="text-[12.5px] text-ink2">{college.join(', ')}</td>
            </tr>))}</tbody>
        </table>
        {crit.length === 0 && <p className="px-5 py-6 text-sm text-muted">No critical years.</p>}
      </div>
    </Card>
  )
}

function LifeStages({ rows }: { rows: any[] }) {
  const stage = (r: any) => (r.wages1 + r.wages2) > 0 ? 'Working years' : r.age1 < 75 ? 'Early retirement (before 75)' : 'Late retirement (75+)'
  const groups: Record<string, any[]> = {}
  rows.forEach(r => { (groups[stage(r)] = groups[stage(r)] || []).push(r) })
  const avg = (xs: any[], k: string) => xs.reduce((a, r) => a + r[k], 0) / xs.length
  return (
    <Card title="Life stages" subtitle="Averages per year in each stage">
      <div className="grid md:grid-cols-3 gap-3">
        {['Working years', 'Early retirement (before 75)', 'Late retirement (75+)'].filter(s => groups[s]).map((s, i) => {
          const xs = groups[s]
          const cf = avg(xs, 'cashflow')
          return (
            <div key={s} className="rounded-lg border border-line p-4">
              <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: S[i] }} /><span className="font-medium">{s}</span></div>
              <div className="text-[12.5px] text-muted mt-0.5">{xs[0].year}–{xs[xs.length - 1].year} · {xs.length} years</div>
              <dl className="grid grid-cols-2 gap-y-1 text-sm mt-3">
                <dt className="text-ink2">Income</dt><dd className="text-right tnum">{money(avg(xs, 'total_income'))}</dd>
                <dt className="text-ink2">Spending</dt><dd className="text-right tnum">{money(avg(xs, 'total_expenses'))}</dd>
                <dt className="text-ink2">Taxes</dt><dd className="text-right tnum">{money(avg(xs, 'taxes'))}</dd>
                <dt className="text-ink2">Cash flow</dt><dd className={clsx('text-right tnum font-medium', cf < 0 ? 'text-bad' : 'text-good')}>{money(cf, { sign: true })}</dd>
              </dl>
            </div>)
        })}
      </div>
    </Card>
  )
}
