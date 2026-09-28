import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ResponsiveContainer, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts'
import { Loader2, Scale, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, axisMoney, clsx } from '../lib/format'
import { useCites } from '../components/Cite'
import { Card, PageHeader, Field, Money, NumberInput, Percent, Select, Segmented, Toggle, Button, Badge, Note, Stat } from '../components/ui'
import { S, axisProps, TipBox, LegendRow } from '../components/charts'

const SRC = ['irs_2024_tax', 'irs_ltcg_2024', 'irs_niit', 'irs_p590a', 'cms_irmaa_2026', 'irs_rp_2025_25', 'hhs_fpl_2025', 'irs_rmd']

function RothSettings() {
  const { plan, update } = usePlan()
  const rc = plan.roth_conversion || { mode: 'off', amount: 0, bracket: 0.12 }
  const set = (k: string, v: any) => update(d => { d.roth_conversion = { mode: 'off', amount: 0, bracket: 0.12, start_age: null, end_age: null, ...(d.roth_conversion || {}), [k]: v } })
  const rmdAge = (plan.current_year - plan.parentX_age) >= 1960 ? 75 : 73
  return (
    <div className="space-y-3">
      <Segmented value={rc.mode} onChange={v => set('mode', v)} options={[{ value: 'off', label: 'No conversions' }, { value: 'fixed', label: 'Fixed amount' }, { value: 'fill_bracket', label: 'Fill a tax bracket' }]} />
      {rc.mode !== 'off' && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {rc.mode === 'fixed'
            ? <Field label="Convert per year (today's $)"><Money value={rc.amount} onChange={v => set('amount', v)} /></Field>
            : <Field label="Fill up to the top of" hint="Converts just enough each year to reach the top of this federal bracket">
              <Select value={String(rc.bracket)} options={[0.10, 0.12, 0.22, 0.24, 0.32].map(b => ({ value: String(b), label: `${Math.round(b * 100)}% bracket` }))} onChange={v => set('bracket', Number(v))} /></Field>}
          <Field label="From age" hint={`Default: ${plan.parentX_retirement_age} (retirement)`}><NumberInput value={rc.start_age ?? null} placeholder={String(plan.parentX_retirement_age)} step={1} onChange={v => set('start_age', Math.round(v))} /></Field>
          <Field label="Until age" hint={`Default: ${rmdAge - 1}, the year before required withdrawals start`}><NumberInput value={rc.end_age ?? null} placeholder={String(rmdAge - 1)} step={1} onChange={v => set('end_age', Math.round(v))} /></Field>
        </div>)}
      <p className="text-[12.5px] text-muted">Ages are {plan.parent1_name}'s. Converted money moves from pre-tax accounts to Roth and is taxed as income that year; the tax is paid from cash and investments.</p>
    </div>
  )
}

function RothCompare() {
  const { plan, update } = usePlan()
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const seq = useRef(0)
  const key = JSON.stringify({ ...plan, roth_conversion: null })
  useEffect(() => {
    const s = ++seq.current
    setBusy(true)
    const t = setTimeout(() => api.rothCompare(plan).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}).finally(() => s === seq.current && setBusy(false)), 900)
    return () => clearTimeout(t)
  }, [key])
  if (!res) return <div className="h-24 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Comparing strategies…</div>
  if (!res.has_pretax) return <p className="text-sm text-muted">No pre-tax savings or 401(k) contributions in the plan, so there's nothing to convert.</p>
  return (
    <div className={clsx(busy && 'opacity-60')}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[720px]">
          <thead><tr className="text-left text-[12px] text-muted border-b border-line">
            <th className="py-2 font-medium">Strategy</th><th className="text-right font-medium">Converted</th><th className="text-right font-medium">Lifetime taxes</th>
            <th className="text-right font-medium">Medicare surcharges</th><th className="text-right font-medium" title={`Net worth at the end with pre-tax money counted at ${100 - res.heir_tax * 100}% (heirs pay income tax on it)`}>After-tax money left</th>
            <th className="text-right font-medium">vs none</th><th className="text-right font-medium">Success</th><th /></tr></thead>
          <tbody>{res.strategies.map((s: any) => (
            <tr key={s.id} className={clsx('border-b border-line last:border-0', s.id === res.best && 'bg-good/5')}>
              <td className="py-2 font-medium">{s.label} {s.id === res.best && <Badge tone="good">best</Badge>} {s.id === res.current && <Badge tone="accent">yours</Badge>}</td>
              <td className="text-right tnum">{money(s.lifetime_conversions)}</td>
              <td className="text-right tnum">{money(s.lifetime_taxes)}</td>
              <td className="text-right tnum">{money(s.lifetime_irmaa)}</td>
              <td className="text-right tnum font-medium">{money(s.after_tax_end)}</td>
              <td className={clsx('text-right tnum', s.vs_none > 0 ? 'text-good' : s.vs_none < 0 ? 'text-bad' : '')}>{s.id === 'off' ? '—' : `${s.vs_none > 0 ? '+' : ''}${money(s.vs_none)}`}</td>
              <td className="text-right tnum">{pct(s.success, 0)}</td>
              <td className="text-right">{s.id !== res.current && <Button size="sm" variant="ghost" onClick={() => update(d => { d.roth_conversion = { ...(d.roth_conversion || {}), ...s.settings } })}>Use</Button>}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <p className="text-[12px] text-muted mt-2">Today's dollars. Conversions pay tax now at today's rates to avoid tax later (required withdrawals, a widow's single-filer brackets, heirs). They win when your tax rate now is lower than it will be later; paying the tax from savings also costs the growth on that money.</p>
    </div>
  )
}

export default function Taxes() {
  const { plan, update, proj } = usePlan()
  const { Cite, Sources } = useCites(SRC)
  const [br, setBr] = useState<any>(null)
  useEffect(() => { api.brackets(plan).then(setBr).catch(() => {}) }, [plan.current_year, plan.parent2_name, plan.tax_filing_status, plan.economic_params?.inflation_rate])
  const rows: any[] = proj?.rows || []
  const s = proj?.summary || {}
  const [range, setRange] = useState<'work' | 'retire' | 'all'>('retire')
  const retYear = s.retirement_year ?? plan.current_year
  const data = useMemo(() => rows.filter(r => range === 'all' || (range === 'retire' ? r.year >= retYear - 2 : r.year < retYear + 2))
    .map(r => {
      const f = r.infl_index
      const conv = (r.roth_conversion || 0) / f
      const taxable = (r.taxable_ordinary || 0) / f
      return { year: r.year, base: Math.max(taxable - conv, 0), conv, gains: (r.cap_gains_realized || 0) / f, tax: r.taxes / f,
        irmaa: (r.irmaa || 0) / f, aca: (r.aca_credit || 0) / f }
    }), [rows, range, retYear])
  const tops = (br?.tops || []).filter((t: any) => t.top && t.rate <= 0.32)
  const irmaaYears: number[] = s.irmaa_years || []
  const cliff: number[] = s.aca_cliff_years || []
  const hasMarket = (plan.health_insurances || []).some((h: any) => h.marketplace)
  return (
    <div className="space-y-5">
      <PageHeader title="Tax planning" subtitle="Roth conversions, taxes on investment gains, Medicare income surcharges and ACA health credits, year by year" />
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card><Stat label="Lifetime taxes (today's $)" value={money(s.lifetime_taxes)} /></Card>
        <Card><Stat label="Tax on investment gains" value={money(s.lifetime_cap_gains_tax)} sub={plan.capital_gains_enabled === false ? 'off' : `basis ${plan.taxable_basis_pct ?? 80}% today`} /></Card>
        <Card><Stat label="Medicare surcharges" value={money(s.lifetime_irmaa)} sub={irmaaYears.length ? `${irmaaYears.length} years, first ${irmaaYears[0]}` : 'none'} tone={irmaaYears.length ? 'warn' : undefined} /></Card>
        <Card><Stat label="ACA premium credits" value={money(s.lifetime_aca_credit)} sub={hasMarket ? (cliff.length ? `over the 400% cliff in ${cliff.length} years` : 'marketplace plan') : 'no marketplace plan'} tone={cliff.length ? 'warn' : undefined} /></Card>
      </div>

      <Card title={<span className="flex items-center gap-2"><Scale size={16} className="text-accent" />Taxable income and the brackets<Cite id="irs_2024_tax" /></span>}
        subtitle="Ordinary taxable income each year (today's $) against the federal bracket tops. Room under a line is income you could add, for example a Roth conversion, at that rate."
        action={<Segmented value={range} onChange={setRange} options={[{ value: 'work', label: 'Working years' }, { value: 'retire', label: 'Retirement' }, { value: 'all', label: 'All' }]} />}>
        <LegendRow items={[{ label: 'Taxable income', color: S[0] }, { label: 'Roth conversion', color: S[2] }, { label: 'Investment gains realized', color: S[4] }]} />
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data} margin={{ top: 12, right: 60, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis dataKey="year" {...axisProps} minTickGap={24} />
            <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
            <Tooltip content={<TipBox />} />
            <Bar dataKey="base" name="Taxable income" stackId="a" fill={S[0]} />
            <Bar dataKey="conv" name="Roth conversion" stackId="a" fill={S[2]} />
            <Bar dataKey="gains" name="Gains realized" stackId="a" fill={S[4]} />
            {tops.map((t: any) => <ReferenceLine key={t.rate} y={t.top} stroke="var(--axis)" strokeDasharray="4 3"
              label={{ value: `${Math.round(t.rate * 100)}% top`, position: 'right', fill: 'var(--axis)', fontSize: 11 }} />)}
          </ComposedChart>
        </ResponsiveContainer>
        {br && <p className="text-[12px] text-muted mt-1">Filing {br.status === 'married' ? 'jointly' : 'single'}; standard deduction {money(br.std_deduction, { compact: false })} (today's $, before this line). Investment gains stack on top and use the 0/15/20% gains rates<Cite id="irs_ltcg_2024" />.</p>}
      </Card>

      <Card title={<span>Roth conversions<Cite id="irs_p590a" /></span>} subtitle="Move pre-tax money to Roth in low-income years (after retiring, before Social Security and required withdrawals)">
        <RothSettings />
      </Card>
      <Card title="Compare conversion strategies" subtitle="Each strategy run through the whole plan, with the same market simulations">
        <RothCompare />
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={<span>Medicare income surcharges (IRMAA)<Cite id="cms_irmaa_2026" /></span>} subtitle="Higher Part B and D premiums when income two years earlier is above $218,000 joint / $109,000 single (2026)">
          <Toggle checked={plan.irmaa_enabled !== false} onChange={v => update(d => { d.irmaa_enabled = v })} label="Include Medicare surcharges" />
          {irmaaYears.length
            ? <Note tone="warn"><span className="flex gap-2"><AlertTriangle size={15} className="shrink-0 mt-0.5" />Surcharges in {irmaaYears.length} years ({irmaaYears.slice(0, 6).join(', ')}{irmaaYears.length > 6 ? '…' : ''}), {money(s.lifetime_irmaa)} in total. Large conversions, home or stock sales two years before are the usual cause.</span></Note>
            : <p className="text-sm text-good mt-3 flex items-center gap-1.5"><CheckCircle2 size={15} />No surcharges in the expected path.</p>}
        </Card>
        <Card title={<span>ACA health insurance credits<Cite id="irs_rp_2025_25" /><Cite id="hhs_fpl_2025" /></span>} subtitle="Before 65, a marketplace plan's premium is cut by a tax credit based on income. No credit above 400% of the poverty level (the cliff).">
          <Toggle checked={plan.aca_enabled !== false} onChange={v => update(d => { d.aca_enabled = v })} label="Apply ACA premium credits to marketplace plans" />
          {!hasMarket ? <p className="text-[12.5px] text-muted mt-3">Mark a plan as “Marketplace (ACA)” on the Healthcare page to use this. Enter its full monthly premium (the benchmark silver price).</p>
            : cliff.length ? <Note tone="warn"><span className="flex gap-2"><AlertTriangle size={15} className="shrink-0 mt-0.5" />Income is over the cliff in {cliff.join(', ')}. Keeping income (including conversions and gains) under 400% of the poverty level those years restores the credit.</span></Note>
            : <p className="text-sm text-good mt-3 flex items-center gap-1.5"><CheckCircle2 size={15} />{money(s.lifetime_aca_credit)} of credits in the expected path.</p>}
        </Card>
      </div>

      <Card title={<span>Taxes on investment gains<Cite id="irs_ltcg_2024" /><Cite id="irs_niit" /></span>} subtitle="When you sell investments outside retirement accounts to pay for spending, the growth part is taxed">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          <Toggle checked={plan.capital_gains_enabled !== false} onChange={v => update(d => { d.capital_gains_enabled = v })} label="Tax realized gains" />
          <Field label="Original money in taxable savings today" hint="Cost basis as a share of your cash and brokerage balance. Cash is 100%; long-held index funds are often 40–60%.">
            <Percent value={plan.taxable_basis_pct ?? 80} decimals={0} min={0} max={100} onChange={v => update(d => { d.taxable_basis_pct = v })} /></Field>
          <p className="text-[12.5px] text-muted">0%, 15% or 20% federal depending on income, plus 3.8% above $250,000 joint and state tax. New savings add to the original money.</p>
        </div>
      </Card>

      <Card title="By year" subtitle="Today's dollars" pad={false}>
        <div className="overflow-x-auto max-h-[420px]">
          <table className="w-full text-sm min-w-[820px]">
            <thead className="sticky top-0 bg-surface"><tr className="text-left text-[12px] text-muted border-b border-line">
              {['Year', 'Taxable income', 'Total tax', 'Conversion', 'Gains realized', 'Gains tax', 'Medicare extra', 'ACA credit', 'Income vs poverty line'].map(h => <th key={h} className={clsx('py-2 font-medium px-3', h !== 'Year' && 'text-right')}>{h}</th>)}</tr></thead>
            <tbody>{rows.map(r => { const f = r.infl_index; return (
              <tr key={r.year} className="border-b border-line last:border-0">
                <td className="px-3 py-1.5 tnum">{r.year} <span className="text-muted text-[11.5px]">({r.age1})</span></td>
                <td className="px-3 text-right tnum">{money(r.taxable_ordinary / f)}</td>
                <td className="px-3 text-right tnum">{money(r.taxes / f)}</td>
                <td className="px-3 text-right tnum">{r.roth_conversion ? money(r.roth_conversion / f) : ''}</td>
                <td className="px-3 text-right tnum">{r.cap_gains_realized ? money(r.cap_gains_realized / f) : ''}</td>
                <td className="px-3 text-right tnum">{r.tax_cap_gains ? money(r.tax_cap_gains / f) : ''}</td>
                <td className={clsx('px-3 text-right tnum', r.irmaa > 0 && 'text-warn')}>{r.irmaa ? money(r.irmaa / f) : ''}</td>
                <td className="px-3 text-right tnum text-good">{r.aca_credit ? money(r.aca_credit / f) : ''}</td>
                <td className={clsx('px-3 text-right tnum', r.aca_benchmark > 0 && r.fpl_ratio > 4 && 'text-bad')}>{r.aca_benchmark > 0 ? `${Math.round(r.fpl_ratio * 100)}%` : ''}</td>
              </tr>) })}</tbody>
          </table>
        </div>
      </Card>
      <Sources className="px-1" />
      <p className="text-[12px] text-muted px-1 flex items-center gap-1">Required withdrawals start at 73 or 75<Cite id="irs_rmd" />; see Assumptions. <ArrowRight size={12} /></p>
    </div>
  )
}
