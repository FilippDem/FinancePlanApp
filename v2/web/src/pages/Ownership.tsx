import React, { useMemo, useState } from 'react'
import { Scale, Plus, Trash2, AlertTriangle, Gift, Home as HomeIcon, Calculator } from 'lucide-react'
import { usePlan } from '../lib/store'
import { money, pct, clsx } from '../lib/format'
import { useTodayDollars } from '../lib/hooks'
import { useCites } from '../components/Cite'
import { LinesChart, S } from '../components/charts'
import { Card, PageHeader, Field, Money, NumberInput, Percent, Select, Toggle, Button, Note, Badge, TextInput, Empty, Grid } from '../components/ui'

const REGIMES = [
  { value: 'auto', label: 'From our state (automatic)' },
  { value: 'community', label: 'Community property' },
  { value: 'equitable', label: 'Equitable distribution' },
  { value: 'prenup', label: 'Our prenup' },
]
const DEFAULT_OWN = { enabled: false, regime: 'auto', earnings: 'marital', separate_income: 'auto', marital_split_pct: 50, shortfall: 'balances',
  today: { p1: { liquid: 0, pretax: 0 }, p2: { liquid: 0, pretax: 0 } } }

/** "Who owns what": separate vs marital property, year by year. Labels only; totals never change. */
export default function Ownership() {
  const { plan, update, proj, names, single } = usePlan()
  const [today, setToday] = useTodayDollars()
  const { Cite, Sources } = useCites(['irs_pub555', 'lii_equitable'])
  const own = { ...DEFAULT_OWN, ...(plan.ownership_tracking || {}) }
  const setOwn = (patch: any) => update(d => { d.ownership_tracking = { ...DEFAULT_OWN, ...(d.ownership_tracking || {}), ...patch } })
  const setToday0 = (who: 'p1' | 'p2', k: 'liquid' | 'pretax', v: number) =>
    update(d => { const o = { ...DEFAULT_OWN, ...(d.ownership_tracking || {}) }; o.today = { ...o.today, [who]: { ...o.today[who], [k]: v } }; d.ownership_tracking = o })
  const sum = proj?.summary?.ownership
  const rows: any[] = (proj?.rows || []).filter((r: any) => r.ownership)
  const cy = plan.current_year
  const [year, setYear] = useState<number>(cy)
  const f = (r: any) => (today ? r.infl_index : 1)
  const chart = useMemo(() => rows.map(r => ({ year: r.year, s1: r.ownership.separate1 / f(r), s2: r.ownership.separate2 / f(r), m: r.ownership.marital / f(r) })), [rows, today])
  const snapRow = rows.find(r => r.year === year) || rows[0]
  const my = Number.isFinite(+plan.marriage_year) ? +plan.marriage_year : null
  const liq = [plan.parentX_net_worth - (plan.parentX_pretax_balance || 0), plan.parentY_net_worth - (plan.parentY_pretax_balance || 0)]
  const pre = [plan.parentX_pretax_balance || 0, plan.parentY_pretax_balance || 0]
  const regimeLabel = (r?: string) => r === 'community' ? 'community property' : r === 'prenup' ? 'your prenup' : 'equitable distribution'

  if (single) return (
    <div className="space-y-5">
      <PageHeader title="Who owns what" />
      <Card><Empty icon={<Scale size={20} />} title="For couples" body="Separate vs marital property tracking needs two people in the plan. Add a partner under People & income." /></Card>
    </div>)

  return (
    <div className="space-y-5">
      <PageHeader title="Who owns what" subtitle="Separate vs marital property over time: what each of you brought in, inherited or was given, and what you built together. These are labels only; your totals, taxes and success rates don't change."
        actions={<Toggle checked={today} onChange={setToday} label="Today's dollars" />} />

      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <Toggle checked={own.enabled} onChange={v => setOwn({ enabled: v })} label="Track separate and marital property" />
          {own.enabled && sum && <Badge tone="accent">Rules: {regimeLabel(sum.regime_resolved)}{sum.state ? ` (${sum.state})` : ''}</Badge>}
        </div>
        {!own.enabled && <p className="text-sm text-ink2 mt-3">Turn this on to label savings, retirement accounts and home equity as each person's separate property or as marital property,
          follow them year by year, and see what each of you would hold if property were divided.</p>}
        <p className="text-[12.5px] text-muted mt-3">A planning estimate, not legal advice. A prenup, how accounts are titled and how money was mixed decide the real answer; have your attorney check the rules below.</p>
      </Card>

      {own.enabled && <>
        <Grid cols={2}>
          <Card title="Rules" subtitle={<>Defaults follow your state: nine states use community property, where pay earned during the marriage belongs to both of you equally<Cite id="irs_pub555" />; the others divide marital property by fairness factors<Cite id="lii_equitable" />.</>}>
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Married (or joined finances) in"><NumberInput value={my} step={1} placeholder="year" onChange={v => update(d => { d.marriage_year = Math.round(v) })} /></Field>
              <Field label="Which rules"><Select value={own.regime} options={REGIMES} onChange={v => setOwn({ regime: v })} /></Field>
              <Field label="Pay earned during the marriage" hint="A prenup can keep each person's earnings separate">
                <Select value={own.earnings} options={[{ value: 'marital', label: 'Belongs to both (marital)' }, { value: 'separate', label: "Stays each person's own" }]} onChange={v => setOwn({ earnings: v })} /></Field>
              <Field label="Growth and rent from separate property" cite={<Cite id="irs_pub555" />}>
                <Select value={own.separate_income} options={[{ value: 'auto', label: `From our state (${sum?.separate_income_resolved === 'marital' ? 'becomes marital' : 'stays separate'})` },
                  { value: 'separate', label: 'Stays separate' }, { value: 'marital', label: 'Becomes marital' }]} onChange={v => setOwn({ separate_income: v })} /></Field>
              <Field label={`${names[0]}'s share of marital property if divided`} hint="Community property is split 50/50; equitable distribution or a prenup may differ">
                <Percent value={own.marital_split_pct} decimals={0} onChange={v => setOwn({ marital_split_pct: Math.min(100, Math.max(0, v)) })} /></Field>
              <Field label="If marital money runs out, separate money pays" hint="Using separate money for shared costs mixes it with marital property">
                <Select value={own.shortfall} options={[{ value: 'balances', label: 'In proportion to each balance' }, { value: 'split', label: `By the shared-cost split (${plan.shared_expense_split_pct ?? 50}% / ${100 - (plan.shared_expense_split_pct ?? 50)}%)` }]} onChange={v => setOwn({ shortfall: v })} /></Field>
            </div>
          </Card>

          <Card title="Separate property today" subtitle={my && my <= cy ? `The part of today's balances that is still separate: what each of you had at the wedding plus its growth, and gifts or inheritances kept apart.` : `You're not married yet in the plan, so everything each of you owns stays separate until ${my ?? 'the wedding'}.`}>
            {(my === null || my <= cy) ? (
              <div className="space-y-4">
                {(['p1', 'p2'] as const).map((w, i) => (
                  <div key={w}>
                    <div className="text-sm font-semibold mb-2">{names[i]}</div>
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Cash & investments" hint={`Of ${money(liq[i], { compact: false })} today`}><Money value={own.today[w].liquid} step={1000} onChange={v => setToday0(w, 'liquid', Math.min(v, Math.max(liq[i], 0)))} /></Field>
                      <Field label="Retirement accounts" hint={`Of ${money(pre[i], { compact: false })} today`}><Money value={own.today[w].pretax} step={1000} onChange={v => setToday0(w, 'pretax', Math.min(v, pre[i]))} /></Field>
                    </div>
                    <GrowthHelper my={my} cy={cy} r={plan.economic_params?.investment_return ?? 0.06} onUse={v => setToday0(w, 'pretax', Math.min(v, pre[i]))} onUseLiquid={v => setToday0(w, 'liquid', Math.min(v, Math.max(liq[i], 0)))} />
                  </div>))}
              </div>
            ) : <p className="text-sm text-ink2">Each person's savings, retirement accounts and homes are tracked as their own until the wedding year; from then on, new earnings follow the rules.</p>}
          </Card>
        </Grid>

        {sum && sum.commingled_total > 1 && (
          <Note tone="warn"><span className="flex gap-2"><AlertTriangle size={16} className="shrink-0 mt-0.5" />
            <span>In {sum.commingled_years.slice(0, 6).join(', ')}{sum.commingled_years.length > 6 ? '…' : ''} the plan runs out of marital money, and {money(sum.commingled_total)} of separate money pays shared costs.
              Spent separate money usually can't be claimed back, so this is where separate property quietly turns marital. Consider cutting shared costs, or deciding up front (in writing) how that money is treated.</span></span></Note>)}

        <Card title="Who owns what over time" subtitle={`Each person's separate property and your marital property: savings, retirement accounts and home equity${today ? ", today's dollars" : ''}`}>
          {chart.length ? <LinesChart data={chart} series={[{ key: 's1', label: `${names[0]} separate` }, { key: 's2', label: `${names[1]} separate` }, { key: 'm', label: 'Marital' }]} height={300} /> : <div className="h-40" />}
        </Card>

        {snapRow && (() => {
          const o = snapRow.ownership, k = f(snapRow)
          const tot = o.separate1 + o.separate2 + o.marital
          const phase = o.phase === 'before' ? 'before the wedding' : o.phase === 'after' ? 'after one of you has died (labels as of then)' : 'married'
          return (
            <Card title="Snapshot" subtitle={`What each of you would hold in ${snapRow.year} if property were divided under ${regimeLabel(sum?.regime_resolved)} (${phase})`}
              action={<div className="flex items-center gap-2 text-sm"><input type="range" min={rows[0].year} max={rows[rows.length - 1].year} value={snapRow.year}
                onChange={e => setYear(+e.target.value)} className="w-48 accent-[rgb(var(--accent))]" aria-label="Year" /><span className="tnum font-medium w-10">{snapRow.year}</span></div>}>
              <div className="grid gap-3 grid-cols-2 lg:grid-cols-5">
                {[[`${names[0]} separate`, o.separate1, S[0]], [`${names[1]} separate`, o.separate2, S[1]], ['Marital', o.marital, S[2]],
                  [`${names[0]} would get`, o.division.p1, null], [`${names[1]} would get`, o.division.p2, null]].map(([l, v, c]: any) => (
                  <div key={l} className="rounded-lg border border-line p-3">
                    <div className="flex items-center gap-1.5 text-[12.5px] text-muted">{c && <span className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />}{l}</div>
                    <div className="text-[20px] font-semibold tnum">{money(v / k)}</div>
                    <div className="text-[11.5px] text-muted">{tot > 0 ? pct(v / tot, 0) : '—'} of the total</div>
                  </div>))}
              </div>
              <table className="w-full text-sm mt-4">
                <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium" /><th className="font-medium text-right">{names[0]} separate</th>
                  <th className="font-medium text-right">{names[1]} separate</th><th className="font-medium text-right">Marital</th></tr></thead>
                <tbody>
                  {[['Cash & investments', o.liquid], ['Retirement accounts', o.pretax], ['Home equity', o.homes]].map(([l, v]: any) => (
                    <tr key={l} className="border-b border-line/60"><td className="py-1.5">{l}</td>
                      {(['s1', 's2', 'm'] as const).map(c => <td key={c} className={clsx('text-right tnum', v[c] < 0 && 'text-bad')}>{money(v[c] / k)}</td>)}</tr>))}
                  {Math.abs(o.other) > 1 && <tr className="border-b border-line/60"><td className="py-1.5">Other assets less loans</td><td /><td /><td className="text-right tnum">{money(o.other / k)}</td></tr>}
                  {(snapRow.details?.ownership_homes || []).map((h: any) => (
                    <tr key={h.name} className="text-[12.5px] text-muted"><td className="py-1 pl-3">{h.name}</td>
                      {(['s1', 's2', 'm'] as const).map(c => <td key={c} className="text-right tnum">{money(h[c] / k)}</td>)}</tr>))}
                </tbody>
              </table>
              <p className="text-[12px] text-muted mt-2">Negative marital cash means shared costs were paid ahead of withdrawals from marital retirement accounts. Other assets and loans (cars, financed purchases) count as marital.</p>
            </Card>)
        })()}

        <HomesCard />
      </>}
      <WindfallsCard />
      <Sources className="px-1" />
    </div>
  )
}

function GrowthHelper({ my, cy, r, onUse, onUseLiquid }: { my: number | null; cy: number; r: number; onUse: (v: number) => void; onUseLiquid: (v: number) => void }) {
  const [open, setOpen] = useState(false)
  const [amt, setAmt] = useState(0)
  if (!my || my >= cy) return null
  const grown = Math.round(amt * Math.pow(1 + r, cy - my))
  return (
    <div className="mt-2">
      <button className="text-[12.5px] text-accent hover:underline flex items-center gap-1" onClick={() => setOpen(!open)}><Calculator size={13} />Estimate from the balance at the wedding</button>
      {open && <div className="mt-2 flex flex-wrap items-end gap-2 rounded-lg bg-sunken/70 p-2.5">
        <Field label={`Balance in ${my}`} className="w-36"><Money value={amt} step={1000} onChange={setAmt} /></Field>
        <span className="text-sm text-ink2 mb-2">grown at {pct(r)} for {cy - my} years ≈ <b className="tnum">{money(grown, { compact: false })}</b></span>
        <Button size="sm" onClick={() => onUseLiquid(grown)}>Use as cash</Button>
        <Button size="sm" onClick={() => onUse(grown)}>Use as retirement</Button>
      </div>}
    </div>)
}

function WindfallsCard() {
  const { plan, update, names } = usePlan()
  const list: any[] = plan.windfalls || []
  const set = (i: number, k: string, v: any) => update(d => { d.windfalls[i][k] = v })
  return (
    <Card title={<span className="flex items-center gap-2"><Gift size={16} className="text-accent" />Gifts & inheritances</span>}
      subtitle="Money you expect to receive. Added to savings in that year; not taxed as income (a few states have an inheritance tax). Kept separate unless you mix it in."
      action={<Button size="sm" onClick={() => update(d => { d.windfalls = [...(d.windfalls || []), { name: 'Inheritance', year: d.current_year + 10, amount: 100000, recipient: 'Parent 1', kind: 'inheritance', separate: true, inflation_adjust: true }] })}><Plus size={14} />Add</Button>}>
      {list.length === 0 ? <p className="text-sm text-muted">None yet.</p> : (
        <div className="space-y-3">
          {list.map((w, i) => (
            <div key={i} className="grid grid-cols-2 sm:grid-cols-[1.3fr_90px_120px_1fr_28px] gap-2 items-end">
              <Field label="What"><TextInput value={w.name} onChange={v => set(i, 'name', v)} /></Field>
              <Field label="Year"><NumberInput value={w.year} step={1} onChange={v => set(i, 'year', Math.round(v))} /></Field>
              <Field label="Amount (today's $)"><Money value={w.amount} step={5000} onChange={v => set(i, 'amount', v)} /></Field>
              <Field label="To"><Select value={w.separate === false ? 'Both' : w.recipient} options={[{ value: 'Parent 1', label: `${names[0]} (separate)` }, { value: 'Parent 2', label: `${names[1]} (separate)` }, { value: 'Both', label: 'Both of us (marital)' }]}
                onChange={v => update(d => { d.windfalls[i].recipient = v; d.windfalls[i].separate = v !== 'Both' })} /></Field>
              <button className="h-9 text-muted hover:text-bad" onClick={() => update(d => { d.windfalls.splice(i, 1) })}><Trash2 size={14} /></button>
            </div>))}
        </div>)}
    </Card>)
}

function HomesCard() {
  const { plan, update, proj, names } = usePlan()
  const houses: any[] = plan.houses || []
  const r0 = proj?.rows?.[0]
  const split = (name: string) => (r0?.details?.ownership_homes || []).find((h: any) => h.name === name)
  return (
    <Card title={<span className="flex items-center gap-2"><HomeIcon size={16} className="text-accent" />Homes</span>}
      subtitle="Separate money put into each home (down payment, or payments before the wedding). Equity is shared out in proportion to the money each side put in, so appreciation follows the contributions.">
      {houses.length === 0 ? <p className="text-sm text-muted">No homes in the plan.</p> : (
        <div className="space-y-4">
          {houses.map((h, i) => {
            const sp = split(h.name)
            const tot = sp ? sp.s1 + sp.s2 + sp.m : 0
            return (
              <div key={i}>
                <div className="flex items-baseline justify-between"><span className="text-sm font-semibold">{h.name}</span>
                  <span className="text-[12px] text-muted">bought {h.purchase_year} · owner {h.owner === 'Parent1' || h.owner === names[0] ? names[0] : h.owner === 'Parent2' || h.owner === names[1] ? names[1] : 'both'}</span></div>
                <div className="grid grid-cols-2 gap-3 mt-1.5">
                  <Field label={`${names[0]}'s separate money`}><Money value={h.separate_funds?.p1 ?? 0} step={5000} onChange={v => update(d => { d.houses[i].separate_funds = { ...(d.houses[i].separate_funds || {}), p1: v } })} /></Field>
                  <Field label={`${names[1]}'s separate money`}><Money value={h.separate_funds?.p2 ?? 0} step={5000} onChange={v => update(d => { d.houses[i].separate_funds = { ...(d.houses[i].separate_funds || {}), p2: v } })} /></Field>
                </div>
                {sp && tot > 0 && (
                  <div className="mt-2">
                    <div className="flex h-2.5 rounded-full overflow-hidden gap-[2px]">
                      {[sp.s1, sp.s2, sp.m].map((v, k) => v > 0 && <div key={k} style={{ width: `${v / tot * 100}%`, background: S[k] }} />)}
                    </div>
                    <div className="text-[12px] text-muted mt-1">Today: {names[0]} {pct(sp.s1 / tot, 0)} · {names[1]} {pct(sp.s2 / tot, 0)} · marital {pct(sp.m / tot, 0)}</div>
                  </div>)}
              </div>)
          })}
        </div>)}
    </Card>)
}
