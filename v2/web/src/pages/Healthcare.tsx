import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money } from '../lib/format'
import { Card, PageHeader, Field, Money, NumberInput, Percent, TextInput, Select, Button, Toggle, Note, Grid } from '../components/ui'
import { LinesChart } from '../components/charts'

function Rows({ items, render, onAdd, onRemove, empty }: { items: any[]; render: (x: any, i: number) => React.ReactNode; onAdd: () => void; onRemove: (i: number) => void; empty: string }) {
  return (
    <div className="space-y-3">
      {items.length === 0 && <p className="text-sm text-muted">{empty}</p>}
      {items.map((x, i) => (
        <div key={i} className="rounded-lg border border-line p-3.5 relative">
          <button className="absolute top-2.5 right-2.5 p-1 rounded text-muted hover:text-bad" onClick={() => onRemove(i)}><Trash2 size={14} /></button>
          {render(x, i)}
        </div>
      ))}
      <Button size="sm" onClick={onAdd}><Plus size={14} />Add</Button>
    </div>
  )
}

export default function Healthcare() {
  const { plan, update, proj, names } = usePlan()
  const who = [{ value: 'Parent 1', label: names[0] }, ...(names[1] ? [{ value: 'Parent 2', label: names[1] }] : []), { value: 'Both', label: 'Both' }, { value: 'Family', label: 'Whole family' }]
  const setL = (list: string, i: number, k: string, v: any) => update(d => { d[list][i][k] = v })
  const data = (proj?.rows || []).map((r: any) => ({ year: r.year, hc: r.exp_healthcare }))
  return (
    <div className="space-y-5">
      <PageHeader title="Healthcare" subtitle="Premiums and care costs grow with healthcare inflation" />
      <Card title="Health insurance" subtitle="Premiums apply while the covered person's age is in range (e.g. until Medicare at 65)">
        <Rows items={plan.health_insurances} empty="No insurance plans. Add employer or marketplace coverage, especially for early retirement."
          onAdd={() => update(d => { d.health_insurances.push({ name: 'Marketplace plan', type: 'Marketplace', monthly_premium: 900, annual_deductible: 4000, annual_out_of_pocket_max: 9000, copay_primary: 30, copay_specialist: 60, covered_by: 'Both', start_age: d.parentX_retirement_age, end_age: 64 }) })}
          onRemove={i => update(d => { d.health_insurances.splice(i, 1) })}
          render={(x, i) => (
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 pr-6">
              <Field label="Name" className="col-span-2"><TextInput value={x.name} onChange={v => setL('health_insurances', i, 'name', v)} /></Field>
              <Field label="Type"><Select value={x.type} options={['Employer', 'Marketplace', 'Medicare', 'Medicaid', 'COBRA']} onChange={v => setL('health_insurances', i, 'type', v)} /></Field>
              <Field label="Covers"><Select value={x.covered_by} options={who} onChange={v => setL('health_insurances', i, 'covered_by', v)} /></Field>
              <Field label="From age"><NumberInput value={x.start_age} step={1} onChange={v => setL('health_insurances', i, 'start_age', Math.round(v))} /></Field>
              <Field label="To age"><NumberInput value={x.end_age} step={1} onChange={v => setL('health_insurances', i, 'end_age', Math.round(v))} /></Field>
              <Field label="Premium / month"><Money value={x.monthly_premium} step={50} onChange={v => setL('health_insurances', i, 'monthly_premium', v)} /></Field>
              <Field label="Deductible"><Money value={x.annual_deductible} step={250} onChange={v => setL('health_insurances', i, 'annual_deductible', v)} /></Field>
              <Field label="Out-of-pocket max"><Money value={x.annual_out_of_pocket_max} step={250} onChange={v => setL('health_insurances', i, 'annual_out_of_pocket_max', v)} /></Field>
            </div>
          )} />
      </Card>
      <Grid cols={2}>
        <Card title="Medicare (65+)" subtitle="Per person, monthly, today's dollars">
          <div className="grid grid-cols-3 gap-3">
            <Field label="Part B"><Money value={plan.medicare_part_b_premium} step={5} onChange={v => update(d => { d.medicare_part_b_premium = v })} /></Field>
            <Field label="Part D"><Money value={plan.medicare_part_d_premium} step={5} onChange={v => update(d => { d.medicare_part_d_premium = v })} /></Field>
            <Field label="Medigap"><Money value={plan.medigap_premium} step={10} onChange={v => update(d => { d.medigap_premium = v })} /></Field>
          </div>
        </Card>
        <Card title="HSA" subtitle="Treated as a pre-tax account">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Balance"><Money value={plan.hsa_balance} onChange={v => update(d => { d.hsa_balance = v })} /></Field>
            <Field label="Contribution / year"><Money value={plan.hsa_contribution} step={100} onChange={v => update(d => { d.hsa_contribution = v })} /></Field>
          </div>
        </Card>
      </Grid>
      <Card title="Long-term care insurance">
        <Rows items={plan.ltc_insurances} empty="No long-term care policies."
          onAdd={() => update(d => { d.ltc_insurances.push({ name: 'LTC policy', monthly_premium: 250, daily_benefit: 200, benefit_period_days: 1095, elimination_period_days: 90, covered_person: 'Parent 1', start_age: 55, inflation_protection: 0.03 }) })}
          onRemove={i => update(d => { d.ltc_insurances.splice(i, 1) })}
          render={(x, i) => (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pr-6">
              <Field label="Name" className="col-span-2"><TextInput value={x.name} onChange={v => setL('ltc_insurances', i, 'name', v)} /></Field>
              <Field label="Covers"><Select value={x.covered_person} options={who.slice(0, names[1] ? 2 : 1)} onChange={v => setL('ltc_insurances', i, 'covered_person', v)} /></Field>
              <Field label="Starts at age"><NumberInput value={x.start_age} step={1} onChange={v => setL('ltc_insurances', i, 'start_age', Math.round(v))} /></Field>
              <Field label="Premium / month"><Money value={x.monthly_premium} step={10} onChange={v => setL('ltc_insurances', i, 'monthly_premium', v)} /></Field>
              <Field label="Daily benefit"><Money value={x.daily_benefit} step={10} onChange={v => setL('ltc_insurances', i, 'daily_benefit', v)} /></Field>
              <Field label="Benefit days"><NumberInput value={x.benefit_period_days} step={30} onChange={v => setL('ltc_insurances', i, 'benefit_period_days', Math.round(v))} /></Field>
              <Field label="Waiting days"><NumberInput value={x.elimination_period_days} step={30} onChange={v => setL('ltc_insurances', i, 'elimination_period_days', Math.round(v))} /></Field>
              <Field label="Inflation rider"><Percent fraction value={x.inflation_protection} onChange={v => setL('ltc_insurances', i, 'inflation_protection', v)} /></Field>
            </div>
          )} />
        <p className="text-xs text-muted mt-3">Premiums are level (not inflated). Benefits are stored for reference and not yet used in projections.</p>
      </Card>
      <Card title="Other health expenses" subtitle="Out-of-pocket care, prescriptions, dental, therapy…">
        <Rows items={plan.health_expenses} empty="No extra health expenses."
          onAdd={() => update(d => { d.health_expenses.push({ category: 'Routine Care', annual_amount: 1500, covered_by_insurance: false, start_age: 0, end_age: 100, affected_person: 'Both' }) })}
          onRemove={i => update(d => { d.health_expenses.splice(i, 1) })}
          render={(x, i) => (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pr-6 items-end">
              <Field label="Category"><Select value={x.category} options={['Routine Care', 'Prescription', 'Emergency', 'Dental', 'Vision', 'Mental Health', 'Other']} onChange={v => setL('health_expenses', i, 'category', v)} /></Field>
              <Field label="For"><Select value={x.affected_person} options={who.slice(0, names[1] ? 3 : 1).concat(names[1] ? [] : [{ value: 'Both', label: 'Household' }])} onChange={v => setL('health_expenses', i, 'affected_person', v)} /></Field>
              <Field label="Per year"><Money value={x.annual_amount} step={100} onChange={v => setL('health_expenses', i, 'annual_amount', v)} /></Field>
              <Field label="From age"><NumberInput value={x.start_age} step={1} onChange={v => setL('health_expenses', i, 'start_age', Math.round(v))} /></Field>
              <Field label="To age"><NumberInput value={x.end_age} step={1} onChange={v => setL('health_expenses', i, 'end_age', Math.round(v))} /></Field>
            </div>
          )} />
      </Card>
      {data.length > 0 && <Card title="Healthcare costs over time" subtitle="Nominal dollars"><LinesChart data={data} series={[{ key: 'hc', label: 'Healthcare' }]} height={220} /></Card>}
    </div>
  )
}
