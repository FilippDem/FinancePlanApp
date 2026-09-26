import React, { useMemo, useState } from 'react'
import { Download, Play, ChevronDown, ChevronRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money, pct } from '../lib/format'
import { Card, PageHeader, Tabs, Stat, Button, Segmented, Toggle, NumberInput, Badge } from '../components/ui'
import { NetWorthChart, CashflowChart, FanChart, StackedBars, LinesChart } from '../components/charts'
import { useTodayDollars, deflate } from '../lib/hooks'
import { retirementMarkers } from './Dashboard'
import { ReportButton } from '../components/ReportButton'

const COLS: [string, string][] = [
  ['year', 'Year'], ['age1', 'Age'], ['total_income', 'Income'], ['taxes', 'Taxes'], ['total_expenses', 'Spending'],
  ['cashflow', 'Cash flow'], ['investable', 'Savings'], ['home_equity', 'Home equity'], ['net_worth', 'Net worth'],
]

function toCsv(rows: any[]) {
  const keys = Object.keys(rows[0]).filter(k => k !== 'details')
  return [keys.join(','), ...rows.map(r => keys.map(k => typeof r[k] === 'number' ? Math.round(r[k] * 100) / 100 : JSON.stringify(r[k] ?? '')).join(','))].join('\n')
}

function YearDetail({ r, names }: { r: any; names: [string, string] }) {
  const d = r.details
  const line = (l: string, v: number) => v ? <div className="flex justify-between"><span className="text-ink2">{l}</span><span className="tnum">{money(v, { compact: false })}</span></div> : null
  return (
    <div className="grid md:grid-cols-3 gap-6 text-[13px] p-4 bg-sunken/60">
      <div className="space-y-1">
        <div className="font-semibold mb-1">Income</div>
        {line(`${names[0]} salary`, r.wages1)}{line(`${names[1] || 'Partner'} salary`, r.wages2)}
        {line('Social Security', r.ss_income)}{line('Rent', r.rent_income)}{line('Home sale proceeds', r.sale_proceeds)}
        {line('Pre-tax withdrawals', r.withdrawal_pretax)}
        <div className="font-semibold mt-3 mb-1">Taxes</div>
        {line('Federal', r.tax_federal)}{line('State', r.tax_state)}{line('FICA', r.tax_fica)}{line('Foreign', r.tax_foreign)}
        {r.location && <div className="text-muted">Tax location: {r.location}</div>}
      </div>
      <div className="space-y-1">
        <div className="font-semibold mb-1">Spending</div>
        {line(`${names[0]} personal`, r.exp_person1)}{line(`${names[1] || 'Partner'} personal`, r.exp_person2)}{line('Shared household', r.exp_family)}
        {line('Children', r.exp_children)}{line('Healthcare', r.exp_healthcare)}{line('Housing (incl. P&I)', r.exp_housing)}
        {line('Recurring', r.exp_recurring)}{line('One-time', r.exp_purchases)}{line('Down payments', r.down_payment)}{line('401(k)/HSA contributions', r.contrib_pretax)}
      </div>
      <div className="space-y-1">
        {(d.houses || []).filter((h: any) => h.total || h.proceeds).map((h: any) => (
          <div key={h.name}><span className="font-semibold">{h.name}</span> <Badge>{h.status}</Badge>
            {h.total ? <div className="text-ink2">P&I {money(h.mortgage_pi)} · tax {money(h.property_tax)} · upkeep {money(h.maintenance + h.upkeep + h.insurance)}</div> : null}
            {h.proceeds ? <div className="text-ink2">Sold for {money(h.sale_price)}, payoff {money(h.payoff)}</div> : null}
          </div>))}
        {(d.children || []).map((c: any) => <div key={c.name} className="flex justify-between"><span className="text-ink2">{c.name} (age {c.age})</span><span className="tnum">{money(c.total)}</span></div>)}
        {[...(d.recurring || []), ...(d.purchases || [])].map((x: any, i: number) => <div key={i} className="flex justify-between"><span className="text-ink2">{x.name}</span><span className="tnum">{money(x.amount)}</span></div>)}
      </div>
    </div>
  )
}

export default function Projections() {
  const { plan, update, proj, mc, mcLoading, runMC, names, single } = usePlan()
  const [tab, setTab] = useState<'networth' | 'cashflow' | 'mc' | 'taxes' | 'table'>('networth')
  const [today, setToday] = useTodayDollars()
  const [field, setField] = useState<'net_worth' | 'investable'>('investable')
  const [open, setOpen] = useState<number | null>(null)
  const rows = useMemo(() => deflate(proj?.rows || [], today), [proj, today])
  const markers = retirementMarkers(plan, names, single)

  const mcView = useMemo(() => {
    if (!mc || !today || mc.normalized) return mc
    const idx = (proj?.rows || []).map((r: any) => r.infl_index)
    const m = structuredClone(mc)
    for (const f of ['net_worth', 'investable']) for (const q of Object.keys(m[f])) m[f][q] = m[f][q].map((v: number, i: number) => v / (idx[i] || 1))
    const lastIdx = idx[idx.length - 1] || 1
    for (const k of ['median', 'p10', 'p25', 'p75', 'p90', 'min', 'max', 'std']) m.final[k] = m.final[k] / lastIdx
    return m
  }, [mc, today, proj])

  const taxData = rows.map((r: any) => ({ year: r.year, federal: r.tax_federal, state: r.tax_state, fica: r.tax_fica, foreign: r.tax_foreign }))
  const solvency = mc ? mc.years.map((y: number, i: number) => ({ year: y, solvent: mc.solvent_by_year[i] * 100 })) : []

  return (
    <div>
      <PageHeader title="Projections" subtitle={`${plan.current_year}–${proj?.summary?.end_year ?? '…'} · ${today ? "today's dollars" : 'nominal dollars'}`}
        actions={<>
          <Toggle checked={today} onChange={setToday} label="Today's dollars" />
          <Button size="sm" onClick={() => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([toCsv(rows)], { type: 'text/csv' })); a.download = `projection_${today ? 'todays' : 'nominal'}_dollars.csv`; a.click() }}><Download size={14} />CSV</Button>
          <ReportButton />
        </>} />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'networth', label: 'Net worth' }, { value: 'cashflow', label: 'Cash flow' },
        { value: 'mc', label: 'Monte Carlo' }, { value: 'taxes', label: 'Taxes' }, { value: 'table', label: 'Year by year' }]} />

      {tab === 'networth' && <div className="space-y-4">
        <Card title="Expected path"><NetWorthChart rows={rows} markers={markers} height={340} /></Card>
        {mcView && <Card title="Range of outcomes" subtitle={`${mcView.n.toLocaleString()} simulations`}><FanChart mc={mcView} field="net_worth" markers={markers} /></Card>}
      </div>}

      {tab === 'cashflow' && <Card title="Income vs spending" subtitle="Spending stacked by category, taxes on top; the line is total income">
        <CashflowChart rows={rows} markers={markers} height={380} />
      </Card>}

      {tab === 'mc' && <div className="space-y-4">
        <Card title="Monte Carlo" subtitle={mc ? `${mc.n.toLocaleString()} runs · ${mc.mode === 'historical' ? 'historical S&P 500 returns' : 'statistical returns'} · avg return ${pct(mc.avg_return)} ± ${pct(mc.return_std)}` : ''}
          action={<>
            <Segmented value={field} onChange={setField} options={[{ value: 'investable', label: 'Savings' }, { value: 'net_worth', label: 'Net worth' }]} />
            <div className="w-24"><NumberInput value={plan.mc_simulations} step={500} min={100} max={20000} onChange={v => update(d => { d.mc_simulations = Math.round(v) })} /></div>
            <Button size="sm" variant="primary" onClick={() => runMC()} disabled={mcLoading}><Play size={13} />{mcLoading ? 'Running…' : 'Run'}</Button>
          </>}>
          {mcView && <FanChart mc={mcView} field={field} markers={markers} height={360} />}
        </Card>
        {mcView && <>
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            <Card><Stat label="Success rate" value={pct(mcView.success_rate, 0)} tone={mcView.success_rate >= 0.8 ? 'good' : mcView.success_rate < 0.6 ? 'bad' : undefined} sub="Savings never run out" /></Card>
            <Card><Stat label="Median final net worth" value={money(mcView.final.median)} sub={`${money(mcView.final.p25)} – ${money(mcView.final.p75)} (25th–75th)`} /></Card>
            <Card><Stat label="Bad case (10th pct)" value={money(mcView.final.p10)} sub={`Worst ${money(mcView.final.min)}`} /></Card>
            <Card><Stat label="Good case (90th pct)" value={money(mcView.final.p90)} sub={`Best ${money(mcView.final.max)}`} /></Card>
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="More statistics">
              <dl className="grid grid-cols-2 gap-y-2 text-sm">
                <dt className="text-muted">Ends positive</dt><dd className="text-right tnum">{pct(mcView.final.prob_positive, 0)}</dd>
                <dt className="text-muted">Ends ≥ $1M</dt><dd className="text-right tnum">{pct(mcView.final.prob_millionaire, 0)}</dd>
                <dt className="text-muted">Negative outcomes</dt><dd className="text-right tnum">{mcView.final.count_negative.toLocaleString()} / {mcView.n.toLocaleString()}</dd>
                <dt className="text-muted">Std. deviation</dt><dd className="text-right tnum">{money(mcView.final.std)}</dd>
                <dt className="text-muted">Typical depletion year</dt><dd className="text-right tnum">{mcView.depletion_year_median ?? '—'}</dd>
              </dl>
            </Card>
            <Card title="Chance savings are still positive" className="lg:col-span-2">
              <LinesChartPct data={solvency} />
            </Card>
          </div>
        </>}
      </div>}

      {tab === 'taxes' && <Card title="Taxes by year">
        <StackedBars data={taxData} xKey="year" series={[{ key: 'federal', label: 'Federal' }, { key: 'state', label: 'State' }, { key: 'fica', label: 'FICA' }, { key: 'foreign', label: 'Foreign' }]} height={340} />
      </Card>}

      {tab === 'table' && <Card pad={false}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-14 bg-surface"><tr className="text-[12px] text-muted border-b border-line">
              <th className="w-8" />{COLS.map(([k, l]) => <th key={k} className={`py-2.5 pr-4 font-medium ${k === 'year' || k === 'age1' ? 'text-left' : 'text-right'}`}>{l}</th>)}</tr></thead>
            <tbody>
              {rows.map((r: any, i: number) => (
                <React.Fragment key={r.year}>
                  <tr className="border-b border-line hover:bg-sunken/50 cursor-pointer" onClick={() => setOpen(open === i ? null : i)}>
                    <td className="pl-3 text-muted">{open === i ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</td>
                    {COLS.map(([k]) => (
                      <td key={k} className={`py-2 pr-4 tnum ${k === 'year' || k === 'age1' ? '' : 'text-right'} ${k === 'cashflow' && r[k] < 0 ? 'text-bad' : ''} ${k === 'investable' && r[k] < 0 ? 'text-bad' : ''}`}>
                        {k === 'year' ? r.year : k === 'age1' ? `${r.age1}${single ? '' : ` / ${r.age2}`}` : money(r[k])}
                      </td>))}
                  </tr>
                  {open === i && <tr><td colSpan={COLS.length + 1}><YearDetail r={r} names={names} /></td></tr>}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </Card>}
    </div>
  )
}

function LinesChartPct({ data }: { data: any[] }) {
  // percentages, not dollars: simple inline chart
  const max = data.length
  if (!max) return null
  const w = 600, h = 160
  const pts = data.map((d, i) => `${(i / (max - 1)) * w},${h - (d.solvent / 100) * h}`).join(' ')
  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h + 18}`} className="w-full h-[180px]" preserveAspectRatio="none">
        {[0, 50, 100].map(p => <line key={p} x1={0} x2={w} y1={h - p / 100 * h} y2={h - p / 100 * h} stroke="var(--grid)" strokeWidth={1} vectorEffect="non-scaling-stroke" />)}
        <polyline points={pts} fill="none" stroke="var(--s1)" strokeWidth={2} vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="flex justify-between text-[11px] text-muted -mt-3"><span>{data[0].year}</span><span>{data[data.length - 1].year}</span></div>
      <p className="text-[12.5px] text-ink2 mt-2">In {data[data.length - 1].year}: {data[data.length - 1].solvent.toFixed(0)}% of simulations still have savings.</p>
    </div>
  )
}
