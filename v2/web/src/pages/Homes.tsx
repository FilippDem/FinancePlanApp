import React, { useMemo, useState } from 'react'
import { Plus, Trash2, Home as HomeIcon, Pencil } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money } from '../lib/format'
import { Card, PageHeader, Field, Money, NumberInput, Percent, TextInput, Select, Button, Drawer, Empty, Badge, Stat, Note } from '../components/ui'
import { LinesChart } from '../components/charts'

const STATUS = [{ value: 'Own_Live', label: 'Live in it' }, { value: 'Own_Rent', label: 'Rent it out' }, { value: 'Sold', label: 'Sell' }]
const statusLabel = (s: string) => STATUS.find(x => x.value === s)?.label ?? s

function payment(bal: number, rate: number, yrs: number) {
  if (bal <= 0 || yrs <= 0) return 0
  const r = rate / 12, n = yrs * 12
  return r > 0 ? bal * r / (1 - Math.pow(1 + r, -n)) : bal / n
}

export default function Homes() {
  const { plan, update, proj, names, reference } = usePlan()
  const [edit, setEdit] = useState<number | null>(null)
  const houses: any[] = plan.houses || []
  const r0 = proj?.rows?.[0]
  const house = edit !== null ? houses[edit] : null
  const set = (k: string, v: any) => update(d => { d.houses[edit!][k] = v })
  const ownerOpts = [{ value: 'Shared', label: 'Shared' }, { value: 'Parent1', label: names[0] }, ...(names[1] ? [{ value: 'Parent2', label: names[1] }] : [])]
  const ownerValue = (o: string) => o === names[0] ? 'Parent1' : o === names[1] ? 'Parent2' : o

  const eqData = useMemo(() => (proj?.rows || []).map((r: any) => {
    const o: any = { year: r.year }
    for (const h of r.details.houses || []) if (h.equity !== undefined) o[h.name] = h.equity
    return o
  }), [proj])

  const add = () => {
    update(d => {
      d.houses.push({ name: 'New home', purchase_year: d.current_year + 2, purchase_price: 600000, current_value: 600000, mortgage_balance: 480000,
        mortgage_rate: 0.065, mortgage_years_left: 30, property_tax_rate: 0.01, home_insurance: 1800, maintenance_rate: 0.01, upkeep_costs: 2000,
        owner: 'Shared', location: '', appreciation_rate: 3.0, timeline: [{ year: d.current_year + 2, status: 'Own_Live', rental_income: 0 }] })
    })
    setEdit(houses.length)
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Homes" subtitle="Current and future properties — mortgages are amortized, equity counts toward net worth"
        actions={<Button variant="primary" onClick={add}><Plus size={15} />Add home</Button>} />
      {houses.length === 0 ? <Card><Empty icon={<HomeIcon size={20} />} title="No homes yet" body="Add the home you own now, or one you plan to buy. Renters: keep rent under Spending → Shared household." action={<Button variant="primary" onClick={add}><Plus size={15} />Add home</Button>} /></Card> : <>
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <Card><Stat label="Home value" value={money(r0?.home_value)} /></Card>
          <Card><Stat label="Mortgage balance" value={money(r0?.mortgage_balance)} /></Card>
          <Card><Stat label="Home equity" value={money(r0?.home_equity)} /></Card>
          <Card><Stat label={`Housing cost ${plan.current_year}`} value={money(r0?.exp_housing)} sub={`${money((r0?.exp_housing || 0) / 12, { compact: false })}/mo incl. taxes, insurance, upkeep`} /></Card>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {houses.map((h, i) => {
            const cur = r0?.details?.houses?.[i]
            const pmt = payment(h.mortgage_balance, h.mortgage_rate, h.mortgage_years_left)
            return (
              <Card key={i} title={h.name} subtitle={`${h.purchase_year > plan.current_year ? 'Buying' : 'Bought'} ${h.purchase_year} · ${ownerOpts.find(o => o.value === ownerValue(h.owner))?.label ?? h.owner}`}
                action={<Button size="sm" onClick={() => setEdit(i)}><Pencil size={13} />Edit</Button>}>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div><div className="text-muted text-[12px]">Value</div><div className="font-semibold tnum">{money(h.current_value)}</div></div>
                  <div><div className="text-muted text-[12px]">Mortgage</div><div className="font-semibold tnum">{money(h.mortgage_balance)}</div></div>
                  <div><div className="text-muted text-[12px]">P&I / month</div><div className="font-semibold tnum">{money(pmt, { compact: false })}</div></div>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {h.timeline.map((e: any, j: number) => (
                    <Badge key={j} tone={e.status === 'Sold' ? 'warn' : e.status === 'Own_Rent' ? 'accent' : 'neutral'}>
                      {e.year}: {statusLabel(e.status)}{e.status === 'Own_Rent' ? ` ${money(e.rental_income, { compact: false })}/mo` : ''}
                    </Badge>
                  ))}
                </div>
                {cur?.status === 'Not owned' && <p className="text-xs text-muted mt-3">Not owned yet in {plan.current_year}.</p>}
              </Card>
            )
          })}
        </div>
        <Card title="Home equity by property" subtitle="Nominal dollars">
          <LinesChart data={eqData} series={houses.slice(0, 8).map(h => ({ key: h.name, label: h.name }))} />
        </Card>
      </>}

      <Drawer open={!!house} onClose={() => setEdit(null)} title={house?.name || 'Home'}
        footer={<><Button variant="danger" onClick={() => { update(d => { d.houses.splice(edit!, 1) }); setEdit(null) }}><Trash2 size={14} />Delete home</Button>
          <Button variant="primary" onClick={() => setEdit(null)}>Done</Button></>}>
        {house && <>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Name" className="col-span-2"><TextInput value={house.name} onChange={v => set('name', v)} /></Field>
            <Field label="Owner"><Select value={ownerValue(house.owner)} options={ownerOpts} onChange={v => set('owner', v)} /></Field>
            <Field label="Location (optional)"><Select value={house.location || ''} options={['', ...(reference?.locations || [])].map(l => ({ value: l, label: l || '—' }))} onChange={v => set('location', v)} /></Field>
            <Field label="Purchase year"><NumberInput value={house.purchase_year} step={1} onChange={v => set('purchase_year', Math.round(v))} /></Field>
            <Field label="Purchase price" hint="For future purchases, the down payment = price − mortgage, paid that year"><Money value={house.purchase_price} onChange={v => set('purchase_price', v)} /></Field>
            <Field label={house.purchase_year > plan.current_year ? 'Value at purchase' : 'Value today'}><Money value={house.current_value} onChange={v => set('current_value', v)} /></Field>
            <Field label="Appreciation / year"><Percent value={house.appreciation_rate} onChange={v => set('appreciation_rate', v)} /></Field>
          </div>
          <div className="text-[12px] font-semibold uppercase tracking-wide text-muted pt-2">Mortgage</div>
          <div className="grid grid-cols-3 gap-4">
            <Field label={house.purchase_year > plan.current_year ? 'Loan amount' : 'Balance today'}><Money value={house.mortgage_balance} onChange={v => set('mortgage_balance', v)} /></Field>
            <Field label="Rate"><Percent fraction value={house.mortgage_rate} decimals={3} onChange={v => set('mortgage_rate', v)} /></Field>
            <Field label="Years left"><NumberInput value={house.mortgage_years_left} step={1} min={0} onChange={v => set('mortgage_years_left', Math.round(v))} /></Field>
          </div>
          <p className="text-sm text-ink2">Principal & interest: <b className="tnum">{money(payment(house.mortgage_balance, house.mortgage_rate, house.mortgage_years_left), { compact: false })}/mo</b></p>
          <div className="text-[12px] font-semibold uppercase tracking-wide text-muted pt-2">Ownership costs</div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Property tax rate"><Percent fraction value={house.property_tax_rate} decimals={3} onChange={v => set('property_tax_rate', v)} /></Field>
            <Field label="Insurance / year"><Money value={house.home_insurance} step={100} onChange={v => set('home_insurance', v)} /></Field>
            <Field label="Maintenance (% of value)"><Percent fraction value={house.maintenance_rate} decimals={2} onChange={v => set('maintenance_rate', v)} /></Field>
            <Field label="Other upkeep / year"><Money value={house.upkeep_costs} step={100} onChange={v => set('upkeep_costs', v)} /></Field>
          </div>
          <div className="flex items-center justify-between pt-2">
            <div className="text-[12px] font-semibold uppercase tracking-wide text-muted">Timeline</div>
            <Button size="sm" variant="ghost" onClick={() => update(d => {
              const tl = d.houses[edit!].timeline; const last = tl[tl.length - 1]
              tl.push({ year: (last?.year ?? d.current_year) + 5, status: 'Own_Rent', rental_income: 2500 })
            })}><Plus size={14} />Add change</Button>
          </div>
          <div className="space-y-2">
            {house.timeline.map((e: any, j: number) => (
              <div key={j} className="grid grid-cols-[88px_1fr_120px_28px] gap-2 items-center">
                <NumberInput value={e.year} step={1} onChange={v => update(d => { d.houses[edit!].timeline[j].year = Math.round(v); d.houses[edit!].timeline.sort((a: any, b: any) => a.year - b.year) })} />
                <Select value={e.status} options={STATUS} onChange={v => update(d => { d.houses[edit!].timeline[j].status = v })} />
                {e.status === 'Own_Rent'
                  ? <Money value={e.rental_income} step={100} onChange={v => update(d => { d.houses[edit!].timeline[j].rental_income = v })} />
                  : <span />}
                <button disabled={house.timeline.length === 1} className="p-1 rounded text-muted hover:text-bad disabled:opacity-30" onClick={() => update(d => { d.houses[edit!].timeline.splice(j, 1) })}><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
          <Note>Rent is monthly in today's dollars. Selling pays off the remaining mortgage and {plan.home_selling_cost_pct}% selling costs; the proceeds go to savings.</Note>
        </>}
      </Drawer>
    </div>
  )
}
