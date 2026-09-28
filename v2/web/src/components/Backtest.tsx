import React, { useEffect, useRef, useState } from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine } from 'recharts'
import { History, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, axisMoney, clsx } from '../lib/format'
import { Card, Badge } from './ui'
import { axisProps } from './charts'

/** The plan run from every historical start year (1924–2023) with real S&P 500 returns in order. */
export function Backtest({ cite }: { cite?: React.ReactNode }) {
  const { plan } = usePlan()
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  useEffect(() => {
    const s = ++seq.current
    setBusy(true)
    const t = setTimeout(() => api.backtest(plan).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}).finally(() => s === seq.current && setBusy(false)), 700)
    return () => clearTimeout(t)
  }, [key])
  const data = (res?.starts || []).map((x: any) => ({ year: x.year, v: x.final_nw, ok: x.ok, dep: x.depletion_year, wrapped: x.wrapped }))
  const failed = (res?.starts || []).filter((x: any) => !x.ok)
  return (
    <Card title={<span className="flex items-center gap-2"><History size={16} className="text-accent" />Every historical start year{cite}{busy && <Loader2 size={13} className="animate-spin text-muted" />}</span>}
      subtitle="Your plan replayed once for each start year from 1924 to 2023, with the actual S&P 500 returns in order (at your stock share, the rest in bonds). Income and spending follow the plan exactly, so only the market sequence differs.">
      {!res ? <div className="h-24 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Replaying history…</div> : (
        <div className={clsx('space-y-3', busy && 'opacity-60')}>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className={clsx('text-[22px] font-semibold tnum', res.success_rate >= 0.9 ? 'text-good' : res.success_rate >= 0.75 ? 'text-warn' : 'text-bad')}>{pct(res.success_rate, 0)}</span>
            <span>of {res.n} start years never ran out of money.</span>
            <span className="text-muted">Median money left {money(res.median_final)}; worst 10% {money(res.p10_final)} (today's $).</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="year" {...axisProps} minTickGap={20} />
              <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
              <ReferenceLine y={0} stroke="var(--axis)" />
              <Tooltip formatter={(v: any) => money(v)} labelFormatter={(y: any) => { const d = data.find((x: any) => x.year === y); return `Start in ${y}${d && !d.ok ? ` — runs out in ${d.dep}` : ''}${d?.wrapped ? ' (wraps to 1924)' : ''}` }} />
              <Bar dataKey="v" name="Money left at the end">{data.map((d: any) => <Cell key={d.year} fill={d.ok ? 'var(--s2)' : 'rgb(var(--bad))'} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
          {failed.length > 0
            ? <p className="text-[12.5px]">Start years that ran out: {failed.slice(0, 12).map((x: any) => <Badge key={x.year} tone="bad">{x.year} → {x.depletion_year}</Badge>)}{failed.length > 12 ? ' …' : ''}</p>
            : <p className="text-[12.5px] text-good">No historical start year ran out of money.</p>}
          <p className="text-[12px] text-muted">Your plan runs {res.plan_years} years; only {res.full_periods} start years have that much history, so later starts continue from 1924 again. Returns are nominal; inflation follows your assumption.</p>
        </div>)}
    </Card>
  )
}
