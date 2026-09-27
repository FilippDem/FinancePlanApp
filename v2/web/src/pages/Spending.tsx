import React, { useMemo, useState } from 'react'
import { Plus, Trash2, Pencil, Wand2, Repeat, ShoppingBag } from 'lucide-react'
import { usePlan, pk } from '../lib/store'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { SpendingSlider, useCurve } from '../components/SpendingSlider'
import { rescale, strategyFor, xForTotal, levelAt, sum as sumCats, lifestyleOptions, BASE_LIFESTYLES, priceLoc } from '../lib/spending'

const SHARED_LIFESTYLE = ['Family Vacations', 'Shared Subscriptions', 'Pet Care', 'Other Family Expenses', 'Home Improvement']
import { Card, PageHeader, Tabs, Field, Money, NumberInput, Percent, TextInput, Select, Button, Drawer, Toggle, Empty, Badge, Note } from '../components/ui'

const STRATS = ['Conservative (statistical)', 'Average (statistical)', 'High-end (statistical)']

function CategoryEditor({ values, groups, onChange, onRemove }:
  { values: Record<string, number>; groups: Record<string, string[]>; onChange: (k: string, v: number) => void; onRemove?: (k: string) => void }) {
  const known = new Set(Object.values(groups).flat())
  const extra = Object.keys(values).filter(k => !known.has(k))
  const all = { ...groups, ...(extra.length ? { 'Other / custom': extra } : {}) }
  return (
    <div className="grid md:grid-cols-2 gap-x-8 gap-y-5">
      {Object.entries(all).map(([g, cats]) => {
        const present = cats.filter(c => c in values || g !== 'Other / custom')
        const sub = present.reduce((a, c) => a + (values[c] || 0), 0)
        return (
          <div key={g}>
            <div className="flex justify-between items-baseline mb-2">
              <span className="text-[12px] font-semibold uppercase tracking-wide text-muted">{g}</span>
              <span className="text-[12.5px] tnum text-ink2">{money(sub, { compact: false })}/yr</span>
            </div>
            <div className="space-y-1.5">
              {present.map(c => (
                <div key={c} className="grid grid-cols-[1fr_130px_28px] items-center gap-2">
                  <span className="text-sm text-ink truncate">{c}</span>
                  <Money value={values[c] ?? 0} step={100} onChange={v => onChange(c, v)} />
                  {onRemove && extra.includes(c)
                    ? <button className="p-1 rounded text-muted hover:text-bad" onClick={() => onRemove(c)}><Trash2 size={14} /></button>
                    : <span className="text-[11px] text-muted tnum text-right">{values[c] ? `${money((values[c] || 0) / 12)}/mo` : ''}</span>}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function PersonalTab() {
  const { plan, update, reference, names, single } = usePlan()
  const [who, setWho] = useState<'X' | 'Y'>('X')
  const [loc, setLoc] = useState<string>(plan[pk(who, 'expense_location')] || plan.state_timeline?.[0]?.state || 'Seattle')
  const [strat, setStrat] = useState<string>(plan[pk(who, 'expense_strategy')] || 'Average (statistical)')
  const [source, setSource] = useState<'calibrated' | 'v08'>('calibrated')
  const [both, setBoth] = useState(!single)
  const [busy, setBusy] = useState(false)
  const infl = plan.economic_params?.inflation_rate ?? 0.03
  const curve = useCurve(priceLoc(plan, loc), plan.current_year, infl)
  const customL: Record<string, any> = plan.custom_locations || {}
  const locOptions = [...new Set([loc, ...(reference?.locations || []), ...Object.keys(reference?.country_tax || {}), ...Object.keys(customL)])]
  const stratOptions = [...STRATS.map(s => ({ value: s, label: s.replace(' (statistical)', '') })),
    ...lifestyleOptions(plan, loc).filter(s => !BASE_LIFESTYLES.includes(s)).map(s => ({ value: s, label: `${s} · my template` })),
    ...(![...STRATS, ...lifestyleOptions(plan, loc)].includes(strat) ? [{ value: strat, label: strat.replace(' (statistical)', '') }] : [])]
  const vals = plan[pk(who, 'expenses')] || {}
  const total = Object.values(vals).reduce((a: number, b: any) => a + (+b || 0), 0)
  const stored = plan[pk(who, 'spending_level')]
  const x = typeof stored === 'number' ? stored : curve ? Math.round(xForTotal(curve, total)) : 50
  const [scaleShared, setScaleShared] = useState(true)
  const move = (nx: number) => {
    if (!curve) return
    const whoList: ('X' | 'Y')[] = both && !single ? ['X', 'Y'] : [who]
    update(d => {
      if (scaleShared) {
        const fromX = typeof d[pk(who, 'spending_level')] === 'number' ? d[pk(who, 'spending_level')] : x
        const k = sumCats(levelAt(curve, nx)) / Math.max(sumCats(levelAt(curve, fromX)), 1)
        for (const c of SHARED_LIFESTYLE) if (typeof d.family_shared_expenses?.[c] === 'number') d.family_shared_expenses[c] = Math.round(d.family_shared_expenses[c] * k / 10) * 10
      }
      for (const w of whoList) {
        const cur = d[pk(w, 'expenses')] || {}
        const curTotal = Object.values(cur).reduce((a: number, b: any) => a + (+b || 0), 0)
        const from = typeof d[pk(w, 'spending_level')] === 'number' ? d[pk(w, 'spending_level')] : (curTotal > 0 ? xForTotal(curve, curTotal) : null)
        d[pk(w, 'expenses')] = rescale(cur, curve, from, nx)
        d[pk(w, 'spending_level')] = nx
        d[pk(w, 'expense_location')] = loc
        d[pk(w, 'expense_strategy')] = strategyFor(nx)
        d[pk(w, 'use_template')] = true
      }
    })
  }
  const apply = async () => {
    setBusy(true)
    try {
      const t = await api.template('adult', loc, strat, plan.current_year, infl, source, plan)
      update(d => { d[pk(who, 'expenses')] = t; d[pk(who, 'expense_location')] = loc; d[pk(who, 'expense_strategy')] = strat; d[pk(who, 'use_template')] = true; delete d[pk(who, 'spending_level')] })
    } finally { setBusy(false) }
  }
  return (
    <div className="space-y-4">
      {!single && (
        <div className="flex gap-2">
          {(['X', 'Y'] as const).map((w, i) => (
            <Button key={w} variant={who === w ? 'primary' : 'secondary'} size="sm" onClick={() => {
              setWho(w); setLoc(plan[pk(w, 'expense_location')] || plan.state_timeline?.[0]?.state || 'Seattle'); setStrat(plan[pk(w, 'expense_strategy')] || 'Average (statistical)')
            }}>{names[i]} · {money(Object.values(plan[pk(w, 'expenses')] || {}).reduce((a: number, b: any) => a + (+b || 0), 0))}</Button>
          ))}
        </div>
      )}
      <Card title="Spending level" subtitle="Slide to a level that feels right; every category below follows. Edit any category afterwards and the slider keeps your changes in proportion."
        action={<div className="flex items-center gap-3">
          {!single && <Toggle checked={both} onChange={setBoth} label="Both adults" />}
          <Toggle checked={scaleShared} onChange={setScaleShared} label="Shared extras too" hint="Also scale vacations, shared subscriptions, pets, home improvement and other shared lifestyle costs" />
          <div className="w-44"><Select value={loc} options={locOptions} onChange={setLoc} /></div>
        </div>}>
        <SpendingSlider curve={curve} value={x} onChange={move} />
      </Card>
      <Card title={`${names[who === 'X' ? 0 : 1]}'s personal spending`} subtitle={`${money(total, { compact: false })} per year · ${money(total / 12, { compact: false })} per month, today's dollars`}>
        <details className="mb-6 rounded-lg bg-sunken/70 border border-line">
          <summary className="cursor-pointer px-3.5 py-2.5 text-sm text-ink2 flex items-center gap-2"><Wand2 size={15} className="text-accent" />Or fill from a lifestyle template</summary>
          <div className="flex flex-wrap items-end gap-3 px-3.5 pb-3.5">
            <Field label="Location" className="w-52">
              <Select value={loc} options={locOptions} onChange={setLoc} /></Field>
            <Field label="Lifestyle" className="w-56"><Select value={strat} options={stratOptions} onChange={setStrat} /></Field>
            <Field label="Data" className="w-56"><Select value={source} options={[{ value: 'calibrated', label: 'BLS / BEA 2024 (recommended)' }, { value: 'v08', label: 'v0.8 original (about 2x higher)' }]} onChange={setSource} /></Field>
            <Button onClick={apply} disabled={busy}>{busy ? 'Applying…' : 'Apply template'}</Button>
            <span className="text-xs text-muted mb-2.5 basis-full">Overwrites the amounts below (inflated to {plan.current_year}).</span>
          </div>
        </details>
        <CategoryEditor values={vals} groups={reference?.adult_categories || {}} onChange={(k, v) => update(d => { d[pk(who, 'expenses')][k] = v })} />
      </Card>
    </div>
  )
}

function SharedTab() {
  const { plan, update, reference } = usePlan()
  const [newCat, setNewCat] = useState('')
  const vals = plan.family_shared_expenses || {}
  const total = Object.values(vals).reduce((a: number, b: any) => a + (+b || 0), 0)
  return (
    <Card title="Shared household spending" subtitle={`${money(total, { compact: false })} per year · ${money(total / 12, { compact: false })} per month, today's dollars`}>
      <Note>Mortgage/Rent, Property Tax and Home Insurance here are skipped automatically in years you own a home — those costs come from the Homes page.</Note>
      <div className="mt-5">
        <CategoryEditor values={vals} groups={reference?.family_categories || {}}
          onChange={(k, v) => update(d => { d.family_shared_expenses[k] = v })}
          onRemove={k => update(d => { delete d.family_shared_expenses[k] })} />
      </div>
      <div className="flex gap-2 mt-6 max-w-md">
        <TextInput value={newCat} onChange={setNewCat} placeholder="New category, e.g. Childcare help" />
        <Button onClick={() => { if (newCat.trim()) { update(d => { d.family_shared_expenses[newCat.trim()] = 0 }); setNewCat('') } }}><Plus size={14} />Add</Button>
      </div>
    </Card>
  )
}

const REC_CATS = ['Vehicle', 'Home', 'Travel', 'Technology', 'Recreation', 'Children', 'Work Equipment', 'Other']

function RecurringTab() {
  const { plan, update, names } = usePlan()
  const [edit, setEdit] = useState<number | null>(null)
  const list: any[] = plan.recurring_expenses || []
  const blank = { name: 'New expense', category: 'Other', amount: 5000, frequency_years: 1, start_year: plan.current_year, end_year: null,
    inflation_adjust: true, parent: 'Both', financing_years: 0, interest_rate: 0 }
  const item = edit !== null ? list[edit] : null
  const set = (k: string, v: any) => update(d => { d.recurring_expenses[edit!][k] = v })
  return (
    <Card title="Recurring expenses" subtitle="Things that come back every N years — cars, trips, gadgets, renovations"
      action={<Button variant="primary" size="sm" onClick={() => { update(d => { d.recurring_expenses.push(blank) }); setEdit(list.length) }}><Plus size={14} />Add</Button>} pad={false}>
      {list.length === 0 ? <Empty icon={<Repeat size={20} />} title="No recurring expenses" body="Add a car every 10 years or an annual vacation." /> : (
        <table className="w-full text-sm">
          <thead><tr className="text-left text-[12px] text-muted border-b border-line">
            <th className="px-5 py-2 font-medium">Name</th><th className="py-2 font-medium">Every</th><th className="py-2 font-medium">Years</th>
            <th className="py-2 font-medium text-right">Amount</th><th className="py-2 font-medium pl-4">Financing</th><th className="w-20" /></tr></thead>
          <tbody>
            {list.map((r, i) => (
              <tr key={i} className="border-b border-line last:border-0 hover:bg-sunken/50 cursor-pointer" onClick={() => setEdit(i)}>
                <td className="px-5 py-2.5"><div className="font-medium">{r.name}</div><div className="text-xs text-muted">{r.category}</div></td>
                <td>{r.frequency_years === 1 ? 'Every year' : `${r.frequency_years} yrs`}</td>
                <td className="tnum">{r.start_year}–{r.end_year ?? '…'}</td>
                <td className="text-right tnum font-medium">{money(r.amount, { compact: false })}</td>
                <td className="pl-4">{r.financing_years > 0 ? <Badge>{r.financing_years} yrs @ {(r.interest_rate * 100).toFixed(1)}%</Badge> : <span className="text-muted">Cash</span>}</td>
                <td className="pr-4 text-right"><Pencil size={14} className="inline text-muted" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Drawer open={!!item} onClose={() => setEdit(null)} title="Recurring expense"
        footer={<><Button variant="danger" onClick={() => { update(d => { d.recurring_expenses.splice(edit!, 1) }); setEdit(null) }}><Trash2 size={14} />Delete</Button>
          <Button variant="primary" onClick={() => setEdit(null)}>Done</Button></>}>
        {item && <>
          <Field label="Name"><TextInput value={item.name} onChange={v => set('name', v)} /></Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Category"><Select value={item.category} options={REC_CATS.includes(item.category) ? REC_CATS : [...REC_CATS, item.category]} onChange={v => set('category', v)} /></Field>
            <Field label="For"><Select value={item.parent} options={['Both', names[0], ...(names[1] ? [names[1]] : [])]} onChange={v => set('parent', v)} /></Field>
            <Field label="Amount (today's $)"><Money value={item.amount} onChange={v => set('amount', v)} /></Field>
            <Field label="Every N years"><NumberInput value={item.frequency_years} min={1} step={1} onChange={v => set('frequency_years', Math.round(v))} /></Field>
            <Field label="First year"><NumberInput value={item.start_year} step={1} onChange={v => set('start_year', Math.round(v))} /></Field>
            <Field label="Last year (blank = forever)"><NumberInput value={item.end_year} step={1} placeholder="forever" onChange={v => set('end_year', Math.round(v) || null)} /></Field>
            <Field label="Financing years (0 = cash)"><NumberInput value={item.financing_years} min={0} step={1} onChange={v => set('financing_years', Math.round(v))} /></Field>
            <Field label="Loan rate"><Percent fraction value={item.interest_rate} onChange={v => set('interest_rate', v)} /></Field>
          </div>
          <Toggle checked={item.inflation_adjust} onChange={v => set('inflation_adjust', v)} label="Grows with inflation" />
          {item.end_year !== null && <Button size="sm" variant="ghost" onClick={() => set('end_year', null)}>Make it open-ended</Button>}
        </>}
      </Drawer>
    </Card>
  )
}

const ASSET_TYPES = ['Expense', 'Vehicle', 'Real Estate', 'Investment', 'Depreciating']

function OneTimeTab() {
  const { plan, update } = usePlan()
  const [edit, setEdit] = useState<number | null>(null)
  const list: any[] = plan.major_purchases || []
  const item = edit !== null ? list[edit] : null
  const set = (k: string, v: any) => update(d => { d.major_purchases[edit!][k] = v })
  const sorted = useMemo(() => list.map((m, i) => ({ m, i })).sort((a, b) => a.m.year - b.m.year), [list])
  return (
    <Card title="One-time purchases" subtitle="Weddings, renovations, a boat — paid once or financed"
      action={<Button variant="primary" size="sm" onClick={() => { update(d => { d.major_purchases.push({ name: 'New purchase', year: plan.current_year + 1, amount: 10000, financing_years: 0, interest_rate: 0, asset_type: 'Expense', appreciation_rate: 0 }) }); setEdit(list.length) }}><Plus size={14} />Add</Button>} pad={false}>
      {list.length === 0 ? <Empty icon={<ShoppingBag size={20} />} title="No one-time purchases" /> : (
        <table className="w-full text-sm">
          <thead><tr className="text-left text-[12px] text-muted border-b border-line">
            <th className="px-5 py-2 font-medium">Name</th><th className="py-2 font-medium">Year</th><th className="py-2 font-medium text-right">Amount</th>
            <th className="py-2 font-medium pl-4">Type</th><th className="py-2 font-medium">Financing</th><th className="w-12" /></tr></thead>
          <tbody>
            {sorted.map(({ m, i }) => (
              <tr key={i} className="border-b border-line last:border-0 hover:bg-sunken/50 cursor-pointer" onClick={() => setEdit(i)}>
                <td className="px-5 py-2.5 font-medium">{m.name}</td><td className="tnum">{m.year}</td>
                <td className="text-right tnum font-medium">{money(m.amount, { compact: false })}</td>
                <td className="pl-4">{m.asset_type === 'Expense' ? <span className="text-muted">Expense</span> : <Badge tone="accent">{m.asset_type}</Badge>}</td>
                <td>{m.financing_years > 0 ? `${m.financing_years} yrs` : <span className="text-muted">Cash</span>}</td>
                <td className="pr-4 text-right"><Pencil size={14} className="inline text-muted" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Drawer open={!!item} onClose={() => setEdit(null)} title="One-time purchase"
        footer={<><Button variant="danger" onClick={() => { update(d => { d.major_purchases.splice(edit!, 1) }); setEdit(null) }}><Trash2 size={14} />Delete</Button>
          <Button variant="primary" onClick={() => setEdit(null)}>Done</Button></>}>
        {item && <>
          <Field label="Name"><TextInput value={item.name} onChange={v => set('name', v)} /></Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Year"><NumberInput value={item.year} step={1} onChange={v => set('year', Math.round(v))} /></Field>
            <Field label="Amount (today's $)"><Money value={item.amount} onChange={v => set('amount', v)} /></Field>
            <Field label="Financing years (0 = cash)"><NumberInput value={item.financing_years} min={0} step={1} onChange={v => set('financing_years', Math.round(v))} /></Field>
            <Field label="Loan rate"><Percent fraction value={item.interest_rate} onChange={v => set('interest_rate', v)} /></Field>
            <Field label="Counts as" hint="Anything other than Expense is kept as an asset in net worth"><Select value={item.asset_type} options={ASSET_TYPES} onChange={v => set('asset_type', v)} /></Field>
            {item.asset_type !== 'Expense' && <Field label="Value change per year" hint="Negative for depreciation"><Percent fraction value={item.appreciation_rate} onChange={v => set('appreciation_rate', v)} /></Field>}
          </div>
        </>}
      </Drawer>
    </Card>
  )
}

export default function Spending() {
  const { plan } = usePlan()
  const [tab, setTab] = useState<'personal' | 'shared' | 'recurring' | 'onetime'>('personal')
  return (
    <div>
      <PageHeader title="Spending" subtitle="Everything in today's dollars — the projection adds inflation" />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'personal', label: 'Personal' }, { value: 'shared', label: 'Shared household' },
        { value: 'recurring', label: 'Recurring', count: plan.recurring_expenses?.length }, { value: 'onetime', label: 'One-time', count: plan.major_purchases?.length }]} />
      {tab === 'personal' && <PersonalTab />}
      {tab === 'shared' && <SharedTab />}
      {tab === 'recurring' && <RecurringTab />}
      {tab === 'onetime' && <OneTimeTab />}
    </div>
  )
}
