import React, { useMemo, useState } from 'react'
import { money } from '../lib/format'
import { amortize, monthlyBreakdown } from '../lib/mortgage'
import { Field, Money, NumberInput, Percent, Segmented, Select, Note } from './ui'
import { S, StackedBars } from './charts'

const TERMS = [10, 15, 20, 25, 30, 40]

/** Redfin-style payment calculator for one home. `patch` merges fields into the house. */
export function MortgageCalculator({ h, cy, patch }: { h: any; cy: number; patch: (p: Record<string, any>) => void }) {
  const [taxUnit, setTaxUnit] = useState<'pct' | 'usd'>('pct')
  const b = useMemo(() => monthlyBreakdown(h, cy), [h, cy])
  const sched = useMemo(() => amortize(b.terms), [b.terms])
  const totalInterest = sched.reduce((a, r) => a + r.interest, 0)
  const payoff = sched.length ? sched[sched.length - 1].year : null
  const future = +h.purchase_year > cy
  const est = h.mortgage_mode === 'estimate'
  const price = +h.purchase_price || 0
  const value = +h.current_value || 0

  const parts = [
    { key: 'pi', label: 'Principal and interest', v: b.pi, color: S[0] },
    { key: 'tax', label: 'Property taxes', v: b.tax, color: S[1] },
    { key: 'ins', label: 'Home insurance', v: b.ins, color: S[2] },
    { key: 'hoa', label: 'HOA dues', v: b.hoa, color: S[3] },
    { key: 'pmi', label: 'Mortgage insurance (PMI)', v: b.pmi, color: S[4] },
  ].filter(x => x.v > 0 || x.key === 'pi' || x.key === 'tax' || x.key === 'ins')
  const cash = future ? b.terms.down + (+h.closing_cost_pct || 0) / 100 * price : 0
  const required = b.terms.required

  return (
    <div className="space-y-5">
      {/* payment summary */}
      <div className="rounded-xl border border-line p-4 bg-sunken/40">
        <div className="flex items-baseline justify-between">
          <div className="text-[26px] font-semibold tracking-tight tnum">{money(b.total, { compact: false })}<span className="text-base font-medium text-ink2"> per month</span></div>
          <span className="text-[12px] text-muted">{future ? `at purchase (${h.purchase_year})` : `in ${cy}`}</span>
        </div>
        <div className="flex h-2.5 rounded-full overflow-hidden mt-3 gap-[2px] bg-surface">
          {parts.filter(p => p.v > 0).map(p => <div key={p.key} style={{ width: `${p.v / Math.max(b.total, 1) * 100}%`, background: p.color }} />)}
        </div>
        <ul className="mt-3 space-y-1.5">
          {parts.map(p => (
            <li key={p.key} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-ink2"><span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />{p.label}</span>
              <span className="tnum">{money(p.v, { compact: false })}</span>
            </li>
          ))}
        </ul>
        {b.upkeep > 0 && <p className="text-[12px] text-muted mt-2">Plus about {money(b.upkeep, { compact: false })}/mo maintenance & upkeep (included in projections).</p>}
      </div>

      <Segmented value={est ? 'estimate' : 'actual'} onChange={v => {
        // carry numbers across so switching modes doesn't change the payment
        if (v === 'estimate') patch({ mortgage_mode: 'estimate',
          down_payment_pct: price > 0 ? Math.min(100, Math.max(0, (1 - (+h.mortgage_balance || 0) / price) * 100)) : 20,
          loan_term_years: TERMS.includes(+h.mortgage_years_left) ? +h.mortgage_years_left : +h.loan_term_years || 30 })
        else patch({ mortgage_mode: 'actual', ...(b.pmi > 0 && !(+h.pmi_monthly) ? { pmi_monthly: Math.round(b.pmi) } : {}) })
      }} options={[{ value: 'estimate', label: 'Estimate from rate' }, { value: 'actual', label: 'I have my loan details' }]} />

      {est ? (
        <div className="grid grid-cols-2 gap-4">
          <Field label="Home price"><Money value={price} step={10000} onChange={v => patch({ purchase_price: v, ...(future || value === price ? { current_value: v } : {}) })} /></Field>
          <Field label="Down payment">
            <div className="grid grid-cols-[1fr_88px] gap-2">
              <Money value={Math.round(price * (+h.down_payment_pct || 0) / 100)} step={5000}
                onChange={v => patch({ down_payment_pct: price > 0 ? Math.min(100, Math.max(0, v / price * 100)) : 20 })} />
              <Percent value={+h.down_payment_pct} decimals={1} onChange={v => patch({ down_payment_pct: Math.min(100, Math.max(0, v)) })} />
            </div>
          </Field>
          <Field label="Loan term">
            <Select value={TERMS.includes(+h.loan_term_years) ? +h.loan_term_years : 30} options={TERMS.map(t => ({ value: t, label: `${t}-year fixed` }))}
              onChange={v => patch({ loan_term_years: v })} /></Field>
          <Field label="Interest rate"><Percent fraction value={+h.mortgage_rate} decimals={3} onChange={v => patch({ mortgage_rate: v })} /></Field>
          {(+h.down_payment_pct || 0) < 20 && <Field label="PMI rate (per year)" hint="Charged on the loan until the balance reaches 78% of the price">
            <Percent value={+h.pmi_rate} decimals={2} onChange={v => patch({ pmi_rate: v })} /></Field>}
          {future && <Field label="Closing costs" hint="Paid with the down payment in the purchase year"><Percent value={+h.closing_cost_pct} decimals={1} onChange={v => patch({ closing_cost_pct: v })} /></Field>}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <Field label={future ? 'Loan amount' : 'Current balance'}><Money value={+h.mortgage_balance} step={5000} onChange={v => patch({ mortgage_balance: v })} /></Field>
          <Field label="Interest rate"><Percent fraction value={+h.mortgage_rate} decimals={3} onChange={v => patch({ mortgage_rate: v })} /></Field>
          <Field label="Years left"><NumberInput value={+h.mortgage_years_left} min={0} step={1} onChange={v => patch({ mortgage_years_left: Math.round(v) })} /></Field>
          <Field label="Monthly P&I you pay" hint="Leave blank to use the required payment. Paying more goes to principal and shortens the loan.">
            <Money value={h.mortgage_payment_override ?? null} placeholder={required ? Math.round(required).toLocaleString() : ''} step={50}
              onChange={v => patch({ mortgage_payment_override: v > 0 ? v : null })} /></Field>
          <Field label="PMI per month"><Money value={+h.pmi_monthly} step={10} onChange={v => patch({ pmi_monthly: v })} /></Field>
          {future && <Field label="Closing costs"><Percent value={+h.closing_cost_pct} decimals={1} onChange={v => patch({ closing_cost_pct: v })} /></Field>}
          {h.mortgage_payment_override > 0 && h.mortgage_payment_override < required - 1 &&
            <div className="col-span-2"><Note tone="warn">That's below the required {money(required, { compact: false })}/mo for this balance, rate and term.</Note></div>}
        </div>
      )}

      <div>
        <div className="text-[12px] font-semibold uppercase tracking-wide text-muted mb-3">Taxes, insurance & fees</div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Property tax">
            <div className="grid grid-cols-[1fr_auto] gap-2 items-center">
              {taxUnit === 'pct'
                ? <Percent fraction value={+h.property_tax_rate} decimals={3} onChange={v => patch({ property_tax_rate: v })} />
                : <Money value={Math.round(value * (+h.property_tax_rate || 0))} step={100} onChange={v => patch({ property_tax_rate: value > 0 ? v / value : 0 })} />}
              <Segmented value={taxUnit} onChange={setTaxUnit} options={[{ value: 'pct', label: '%' }, { value: 'usd', label: '$/yr' }]} />
            </div>
          </Field>
          <Field label="Home insurance / year"><Money value={+h.home_insurance} step={100} onChange={v => patch({ home_insurance: v })} /></Field>
          <Field label="HOA dues / month"><Money value={+h.hoa_monthly} step={25} onChange={v => patch({ hoa_monthly: v })} /></Field>
          <Field label="Maintenance (% of value / yr)"><Percent fraction value={+h.maintenance_rate} decimals={2} onChange={v => patch({ maintenance_rate: v })} /></Field>
          <Field label="Other upkeep / year"><Money value={+h.upkeep_costs} step={100} onChange={v => patch({ upkeep_costs: v })} /></Field>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 rounded-xl border border-line p-3.5">
        <div><div className="text-[12px] text-muted">Loan</div><div className="font-semibold tnum">{money(b.terms.principal)}</div></div>
        <div><div className="text-[12px] text-muted">Total interest</div><div className="font-semibold tnum">{money(totalInterest)}</div></div>
        <div><div className="text-[12px] text-muted">Paid off</div><div className="font-semibold tnum">{payoff ?? (b.terms.principal > 0 ? 'Never' : '—')}</div></div>
        <div><div className="text-[12px] text-muted">{future ? 'Cash to close' : 'Equity today'}</div>
          <div className="font-semibold tnum">{future ? money(cash) : money(value - (+h.mortgage_balance || 0))}</div></div>
      </div>

      {sched.length > 0 && (
        <div>
          <div className="text-[12px] font-semibold uppercase tracking-wide text-muted mb-1">Where each year's payments go</div>
          <StackedBars data={sched.map(r => ({ year: r.year, principal: r.principal, interest: r.interest }))} xKey="year" height={200}
            series={[{ key: 'principal', label: 'Principal' }, { key: 'interest', label: 'Interest' }]} />
        </div>
      )}
      {est && <p className="text-[12px] text-muted">Estimate mode derives today's balance from the original loan; switch to “I have my loan details” to enter numbers from your statement.</p>}
    </div>
  )
}
