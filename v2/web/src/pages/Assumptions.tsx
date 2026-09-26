import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine } from 'recharts'
import { usePlan } from '../lib/store'
import { pct } from '../lib/format'
import { Card, PageHeader, Field, Money, NumberInput, Percent, Select, Button, Toggle, Segmented, Note, Grid } from '../components/ui'
import { S } from '../components/charts'

export default function Assumptions() {
  const { plan, update, reference } = usePlan()
  const ep = plan.economic_params
  const setE = (k: string, v: any) => update(d => { d.economic_params[k] = v })
  const hist = reference?.historical
  const locs = reference?.locations || ['Seattle']
  const asym = plan.mc_use_asymmetric !== false

  return (
    <div className="space-y-5">
      <PageHeader title="Assumptions" subtitle="Economy, taxes, Social Security and simulation settings" />
      <Grid cols={2}>
        <Card title="Economy">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Investment return (nominal)" hint="Expected average annual return of your portfolio">
              <Percent fraction value={ep.investment_return} onChange={v => update(d => { d.economic_params.investment_return = v; d.economic_params.use_historical_returns = false })} /></Field>
            <Field label="Inflation"><Percent fraction value={ep.inflation_rate} onChange={v => update(d => { d.economic_params.inflation_rate = v; d.economic_params.use_historical_inflation = false })} /></Field>
            <Field label="Healthcare inflation"><Percent fraction value={ep.healthcare_inflation_rate} onChange={v => setE('healthcare_inflation_rate', v)} /></Field>
            <Field label="Borrowing rate if savings go negative"><Percent fraction value={plan.debt_interest_rate} onChange={v => update(d => { d.debt_interest_rate = v })} /></Field>
          </div>
          {hist && <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-[12.5px] text-muted w-full">Historical averages (v0.8 “Historical average” option):</span>
            <Button size="sm" onClick={() => update(d => { d.economic_params.investment_return = +hist.mean.toFixed(4); d.economic_params.use_historical_returns = true })}>Return: S&P 500 ({pct(hist.mean)})</Button>
            <Button size="sm" onClick={() => update(d => { d.economic_params.investment_return = 0.06; d.economic_params.use_historical_returns = false })}>Return: balanced 60/40 (~6%)</Button>
            <Button size="sm" onClick={() => update(d => { d.economic_params.inflation_rate = 0.03; d.economic_params.use_historical_inflation = true })}>Inflation: 3.0%</Button>
            <Button size="sm" onClick={() => update(d => { d.economic_params.healthcare_inflation_rate = 0.055; d.economic_params.use_historical_healthcare_inflation = true })}>Healthcare: 5.5%</Button>
            <Button size="sm" onClick={() => update(d => { d.economic_params.expense_growth_rate = 0.02; d.economic_params.use_historical_expense_growth = true })}>Expense growth: 2.0%</Button>
          </div>}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <Field label="Expense growth (kept from v0.8)" hint="v0.8 stored this but never used it; spending grows with inflation. Kept so old files round-trip.">
              <Percent fraction value={ep.expense_growth_rate ?? 0.02} onChange={v => setE('expense_growth_rate', v)} /></Field>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4">
            {[['Real return', ep.investment_return - ep.inflation_rate, 'after inflation'], ['Money doubles in', Math.log(2) / Math.log(1 + Math.max(ep.investment_return, 0.001)), 'years (nominal)'],
              ['Prices double in', Math.log(2) / Math.log(1 + Math.max(ep.inflation_rate, 0.001)), 'years']].map(([l, v, sub]: any, i) => (
              <div key={l} className="rounded-lg bg-sunken/70 p-2.5"><div className="text-[11.5px] text-muted">{l}</div>
                <div className="font-semibold tnum">{i === 0 ? pct(v) : v.toFixed(0)}</div><div className="text-[11px] text-muted">{sub}</div></div>))}
          </div>
          {ep.investment_return > 0.09 && <div className="mt-3"><Note tone="warn">Returns above ~9% assume an all-stock portfolio with no fees. {pct(hist?.mean ?? 0.124)} is the 100-year S&P 500 arithmetic average; the compound (geometric) return is lower.</Note></div>}
        </Card>
        <Card title="Social Security">
          <div className="space-y-4">
            <div><Toggle checked={plan.ss_cola !== false} onChange={v => update(d => { d.ss_cola = v })} label="Benefits rise with inflation (COLA)" /></div>
            <div><Toggle checked={plan.ss_insolvency_enabled} onChange={v => update(d => { d.ss_insolvency_enabled = v })} label="Model trust-fund shortfall" /></div>
            {plan.ss_insolvency_enabled && <div className="grid grid-cols-2 gap-4">
              <Field label="Benefit cut"><Percent value={plan.ss_shortfall_percentage} decimals={0} onChange={v => update(d => { d.ss_shortfall_percentage = v })} /></Field>
              <Field label="Starting in"><NumberInput value={plan.ss_insolvency_year} step={1} onChange={v => update(d => { d.ss_insolvency_year = Math.round(v) })} /></Field>
            </div>}
            <p className="text-xs text-muted">Claim ages and benefit amounts are set per person under People & income.</p>
          </div>
        </Card>
        <Card title="Taxes" subtitle="Federal brackets, standard deduction and FICA are indexed to inflation">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Pre-tax 401(k) contributions / yr" hint="Household total, today's dollars; stops when each person retires"><Money value={plan.pretax_401k} step={500} onChange={v => update(d => { d.pretax_401k = v })} /></Field>
            <Field label="Filing status"><Select value={plan.tax_filing_status || 'married'} options={[{ value: 'married', label: 'Married filing jointly' }, { value: 'single', label: 'Single' }]} onChange={v => update(d => { d.tax_filing_status = v })} /></Field>
            <Field label="State tax override" hint="Only used for locations the app doesn't know. Leave at 0 to use the location's rate.">
              <Percent fraction value={plan.state_tax_rate || 0} onChange={v => update(d => { d.state_tax_rate = v })} /></Field>
            <Field label="Home selling costs"><Percent value={plan.home_selling_cost_pct} decimals={1} onChange={v => update(d => { d.home_selling_cost_pct = v })} /></Field>
          </div>
        </Card>
        <Card title="Where you live" subtitle={<>Sets income tax each year{plan.move_adjusts_spending !== false ? ' and scales everyday spending' : ''}. <a className="text-accent" href="/locations">Map, cost of living and custom places →</a></>}
          action={<Button size="sm" variant="ghost" onClick={() => update(d => { const last = d.state_timeline[d.state_timeline.length - 1]; d.state_timeline.push({ year: last.year + 5, state: last.state, spending_strategy: last.spending_strategy }) })}><Plus size={14} />Add move</Button>}>
          <div className="space-y-2">
            {plan.state_timeline.map((e: any, i: number) => (
              <div key={i} className="grid grid-cols-[90px_1fr_150px_28px] gap-2 items-center">
                <NumberInput value={e.year} step={1} onChange={v => update(d => { d.state_timeline[i].year = Math.round(v); d.state_timeline.sort((a: any, b: any) => a.year - b.year) })} />
                <Select value={e.state} options={locs.includes(e.state) ? locs : [e.state, ...locs]} onChange={v => update(d => { d.state_timeline[i].state = v })} />
                <Select value={e.spending_strategy.replace(' (statistical)', '')} options={['Conservative', 'Average', 'High-end']} onChange={v => update(d => { d.state_timeline[i].spending_strategy = v })} />
                <button disabled={plan.state_timeline.length === 1} className="p-1 rounded text-muted hover:text-bad disabled:opacity-30" onClick={() => update(d => { d.state_timeline.splice(i, 1) })}><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
        </Card>
      </Grid>

      <Card title="Monte Carlo simulation" subtitle="How the range of outcomes is generated">
        <div className="flex flex-wrap items-center gap-4 mb-5">
          <Segmented value={plan.mc_use_historical ? 'hist' : 'param'} onChange={v => update(d => { d.mc_use_historical = v === 'hist' })}
            options={[{ value: 'param', label: 'Statistical returns' }, { value: 'hist', label: 'Historical S&P 500' }]} />
          <Field label="" className="w-40"><div className="flex items-center gap-2"><span className="text-sm text-ink2">Runs</span>
            <NumberInput value={plan.mc_simulations} step={100} min={100} max={20000} onChange={v => update(d => { d.mc_simulations = Math.round(v) })} /></div></Field>
          <Toggle checked={plan.mc_normalize_to_today_dollars} onChange={v => update(d => { d.mc_normalize_to_today_dollars = v })} label="Report in today's dollars" />
        </div>
        {plan.mc_use_historical ? (
          <div className="grid sm:grid-cols-4 gap-4">
            <Field label="Stock allocation"><Percent value={plan.mc_stock_allocation} decimals={0} onChange={v => update(d => { d.mc_stock_allocation = v })} /></Field>
            <Field label="Bond return (rest)"><Percent fraction value={plan.bond_return} onChange={v => update(d => { d.bond_return = v })} /></Field>
            <Field label="Sampling"><Select value={plan.mc_historical_mode} options={[{ value: 'random', label: 'Random years' }, { value: 'sequential', label: 'Historical sequences' }]} onChange={v => update(d => { d.mc_historical_mode = v })} /></Field>
            <Field label="Income / expense wobble ±"><div className="grid grid-cols-2 gap-2">
              <Percent value={plan.mc_income_variability} decimals={1} onChange={v => update(d => { d.mc_income_variability = v })} />
              <Percent value={plan.mc_expense_variability} decimals={1} onChange={v => update(d => { d.mc_expense_variability = v })} /></div></Field>
          </div>
        ) : (
          <div className="space-y-4">
            <Toggle checked={asym} onChange={v => update(d => { d.mc_use_asymmetric = v })} label="Different upside and downside" />
            <div className="grid sm:grid-cols-3 gap-4">
              {(['return', 'income', 'expense'] as const).map(k => (
                <Field key={k} label={k === 'return' ? 'Return volatility (± percentage points)' : k === 'income' ? 'Income variability ±' : 'Expense variability ±'}
                  hint={k === 'return' ? 'Standard deviation of yearly returns around the expected return. 15 ≈ stock-heavy, 10 ≈ balanced.' : 'Uniform yearly swing'}>
                  {asym ? <div className="grid grid-cols-2 gap-2">
                    <Percent value={plan[`mc_${k}_variability_positive`]} decimals={1} onChange={v => update(d => { d[`mc_${k}_variability_positive`] = v })} />
                    <Percent value={plan[`mc_${k}_variability_negative`]} decimals={1} onChange={v => update(d => { d[`mc_${k}_variability_negative`] = v })} />
                  </div> : <Percent value={plan[`mc_${k}_variability`]} decimals={1} onChange={v => update(d => { d[`mc_${k}_variability`] = v })} />}
                </Field>
              ))}
            </div>
            {asym && <p className="text-xs text-muted">Left: upside · right: downside</p>}
          </div>
        )}
      </Card>

      {hist && (
        <Card title="Historical S&P 500 returns" subtitle={`${hist.start_year}–${hist.start_year + hist.total_years - 1} · average ${pct(hist.mean)} · std dev ${pct(hist.std)} · ${hist.positive_years} up years, ${hist.negative_years} down`}>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={hist.returns.map((r: number, i: number) => ({ year: hist.start_year + i, r: r * 100 }))} barCategoryGap={1}>
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="year" tickLine={false} axisLine={false} minTickGap={30} />
              <YAxis tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} width={44} />
              <Tooltip formatter={(v: any) => [`${(+v).toFixed(0)}%`, 'Return']} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
              <ReferenceLine y={0} stroke="var(--axis)" />
              <Bar dataKey="r" maxBarSize={8} isAnimationActive={false}>
                {hist.returns.map((r: number, i: number) => <Cell key={i} fill={r >= 0 ? S[0] : S[7]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  )
}
