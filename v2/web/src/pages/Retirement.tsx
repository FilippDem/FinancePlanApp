import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, ArrowRight } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine } from 'recharts'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, clsx } from '../lib/format'
import { Card, PageHeader, Button, Badge, Note, Percent, Stat } from '../components/ui'
import { S } from '../components/charts'

export default function Retirement() {
  const { plan, update, single } = usePlan()
  const nav = useNavigate()
  const [wr, setWr] = useState(0.04)
  const [base, setBase] = useState<any>(null)
  const [what, setWhat] = useState<any[] | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    const t = setTimeout(() => api.retirement(plan, wr).then(r => live && setBase(r)).catch(() => {}), 300)
    return () => { live = false; clearTimeout(t) }
  }, [plan, wr])
  const runWhat = async () => { setBusy(true); try { setWhat((await api.retireWhatif(plan, 300)).rows) } finally { setBusy(false) } }
  useEffect(() => { setWhat(null); const t = setTimeout(runWhat, 900); return () => clearTimeout(t) }, [plan])

  const r = base?.replacement
  const ratio = r?.ratio ?? null
  const bars = r ? [
    { k: 'Social Security', v: r.ss }, { k: `Savings (${(wr * 100).toFixed(1)}% draw)`, v: r.portfolio_draw }, { k: 'Rental income', v: r.rent },
  ].filter(b => b.v > 0 || b.k.startsWith('Social')) : []

  const apply = (row: any) => update(d => { d.parentX_retirement_age = row.age1; if (!single) d.parentY_retirement_age = row.age2 })

  return (
    <div className="space-y-5">
      <PageHeader title="Retirement" subtitle="When to retire, when to claim Social Security, and whether retirement income will be enough (today's dollars)" />

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <Card title="Income replacement" subtitle={r ? `Last working year ${r.last_working_year} vs first retired year ${r.first_retired_year}` : undefined}>
          {!r ? <Loader2 className="animate-spin text-muted" /> : r.pre_income === 0 ? <p className="text-sm text-muted">No employment income in the plan.</p> : <>
            <div className="grid grid-cols-3 gap-4">
              <Stat label="Replacement ratio" value={ratio === null ? '—' : pct(ratio, 0)} tone={ratio !== null && ratio >= 0.8 ? 'good' : ratio !== null && ratio < 0.6 ? 'bad' : undefined} big
                sub="Common target: 70–80%" />
              <Stat label="Income before" value={money(r.pre_income)} sub="Household wages before retiring" />
              <Stat label="Income after" value={money(r.retirement_income)} sub={r.gap_80 > 0 ? `${money(r.gap_80)} short of 80%` : 'Meets the 80% target'} />
            </div>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={bars} layout="vertical" margin={{ top: 16, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke="var(--grid)" />
                <XAxis type="number" tickFormatter={v => money(v)} tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" />
                <YAxis type="category" dataKey="k" width={150} tickLine={false} axisLine={false} fontSize={12} stroke="var(--axis)" />
                <Tooltip formatter={(v: any) => money(v)} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
                <ReferenceLine x={r.target_80} stroke={S[7]} strokeDasharray="4 3" label={{ value: '80% target (total)', position: 'top', fontSize: 11, fill: 'var(--axis)' }} />
                <Bar dataKey="v" name="Per year" isAnimationActive={false} radius={[0, 4, 4, 0]}>{bars.map((_, i) => <Cell key={i} fill={S[i]} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-3 mt-2 text-sm">
              <span className="text-ink2">Withdrawal rate</span><div className="w-28"><Percent fraction value={wr} onChange={v => setWr(Math.min(0.1, Math.max(0.01, v)))} decimals={1} /></div>
              <span className="text-muted text-[12.5px]">Planned spending in that year: {money(r.spending_first_year)}</span>
            </div>
          </>}
        </Card>

        <Card title="Retire earlier or later?" subtitle="Everyone's retirement age shifted together; 300 market simulations each"
          action={busy ? <Loader2 size={15} className="animate-spin text-muted" /> : undefined}>
          {!what ? <div className="h-40 flex items-center justify-center text-muted text-sm"><Loader2 size={16} className="animate-spin mr-2" />Running…</div> : <>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={what} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--grid)" />
                <XAxis dataKey="delta" tickFormatter={d => (d === 0 ? 'Plan' : `${d > 0 ? '+' : ''}${d}y`)} tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" />
                <YAxis domain={[0, 1]} tickFormatter={v => `${Math.round(v * 100)}%`} tickLine={false} axisLine={false} width={40} fontSize={11} stroke="var(--axis)" />
                <Tooltip formatter={(v: any) => pct(v, 0)} labelFormatter={d => (d === 0 ? 'Your plan' : `${d > 0 ? '+' : ''}${d} years`)}
                  contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="success_rate" name="Plan success" isAnimationActive={false} radius={[4, 4, 0, 0]}>
                  {what.map(w => <Cell key={w.delta} fill={w.delta === 0 ? S[0] : S[0]} fillOpacity={w.delta === 0 ? 1 : 0.45} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
            <table className="w-full text-sm mt-2">
              <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium">Retire at</th>
                <th className="font-medium text-right">Success</th><th className="font-medium text-right">Savings at retirement</th><th className="font-medium text-right">Run out</th><th /></tr></thead>
              <tbody>{what.map(w => (
                <tr key={w.delta} className={clsx('border-b border-line last:border-0', w.delta === 0 && 'bg-accentSoft/40')}>
                  <td className="py-1.5 tnum">{w.age1}{!single && ` / ${w.age2}`}{w.delta === 0 && <Badge tone="accent">plan</Badge>}</td>
                  <td className="text-right tnum font-medium">{pct(w.success_rate, 0)}</td>
                  <td className="text-right tnum">{money(w.investable_at_retirement)}</td>
                  <td className="text-right">{w.depletion_year ?? <span className="text-good">Never</span>}</td>
                  <td className="text-right">{w.delta !== 0 && <button className="text-[12.5px] text-accent font-medium" onClick={() => apply(w)}>Use</button>}</td>
                </tr>))}</tbody>
            </table>
          </>}
        </Card>
      </div>

      <Card title="When to claim Social Security" subtitle="Benefit at 67 is from People & income; claiming earlier reduces it for life, waiting to 70 raises it 8% a year">
        {!base ? <Loader2 className="animate-spin text-muted" /> : (
          <div className="grid gap-5 md:grid-cols-2">
            {base.ss.map((p: any) => (
              <div key={p.who}>
                <div className="flex items-baseline justify-between mb-2">
                  <div className="font-medium">{p.name}</div>
                  <div className="text-[12.5px] text-muted">{p.break_even_70_vs_62 ? `Waiting to 70 beats 62 if you live past ${p.break_even_70_vs_62}` : ''}</div>
                </div>
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium">Claim at</th>
                    <th className="font-medium text-right">Per month</th><th className="font-medium text-right">Per year</th><th className="font-medium text-right">Lifetime (to {p.plan_until})</th><th /></tr></thead>
                  <tbody>{p.options.map((o: any) => (
                    <tr key={o.age} className={clsx('border-b border-line last:border-0', o.planned && 'bg-accentSoft/40')}>
                      <td className="py-1.5">{o.age} {o.planned && <Badge tone="accent">plan</Badge>}</td>
                      <td className="text-right tnum">{money(o.annual / 12)}</td>
                      <td className="text-right tnum">{money(o.annual)}</td>
                      <td className="text-right tnum font-medium">{money(o.lifetime)}</td>
                      <td className="text-right">{!o.planned && <button className="text-[12.5px] text-accent font-medium"
                        onClick={() => update(d => { d[`parent${p.who}_ss_claim_age`] = o.age })}>Use</button>}</td>
                    </tr>))}</tbody>
                </table>
              </div>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2 mt-4">
          <Note>Lifetime totals include the Social Security cut you set in Assumptions. They don't include investment growth on earlier checks, which is why the full plan's success rate matters more.</Note>
          <Button size="sm" onClick={() => nav('/people')}>Edit benefits<ArrowRight size={13} /></Button>
        </div>
      </Card>
    </div>
  )
}

