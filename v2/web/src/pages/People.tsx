import React from 'react'
import { Plus, Trash2, Briefcase } from 'lucide-react'
import { usePlan, pk } from '../lib/store'
import { money } from '../lib/format'
import { useCites } from '../components/Cite'
import { Card, PageHeader, Field, Money, NumberInput, Percent, TextInput, Select, Segmented, Button, Grid, Note, Toggle, Badge } from '../components/ui'
import { LinesChart } from '../components/charts'

const EMOJIS = ['👨', '👩', '🧑', '👤', '🧔', '👱‍♀️', '⭐', '🎯']
const STYLE_DEFAULTS: Record<string, { raise: number; bonus: number }> = {
  'Stable': { raise: 3, bonus: 5 }, 'Climbing the Ladder': { raise: 5, bonus: 15 }, 'Startup': { raise: 2, bonus: 10 }, 'Part-time': { raise: 1, bonus: 0 }, 'Coasting': { raise: 2, bonus: 5 } }
const PHILOSOPHIES = ['Stable', 'Climbing the Ladder', 'Startup', 'Part-time', 'Coasting']

function ssFactor(age: number) {
  const m = Math.round((age - 67) * 12)
  if (m >= 0) return 1 + Math.min(m, 36) * (2 / 3) / 100
  const e = -m
  return 1 - (Math.min(e, 36) * 5 / 9 + Math.max(e - 36, 0) * 5 / 12) / 100
}

const PEOPLE_SRC = ['ssa_claiming']

function PersonCard({ who }: { who: 'X' | 'Y' }) {
  const { plan, update } = usePlan()
  const { Cite } = useCites(PEOPLE_SRC)
  const n = who === 'X' ? '1' : '2'
  const set = (k: string, v: any) => update(d => { d[pk(who, k)] = v })
  const claimDefault = Math.min(Math.max(plan[pk(who, 'retirement_age')], 62), 70)
  const claim = plan[pk(who, 'ss_claim_age')] ?? claimDefault
  const nw = plan[pk(who, 'net_worth')]
  return (
    <Card title={<span className="flex items-center gap-2"><span className="text-xl">{plan[`parent${n}_emoji`]}</span>{plan[`parent${n}_name`]}</span>}
      subtitle={`Age ${plan[pk(who, 'age')]} in ${plan.current_year}`}>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Name"><TextInput value={plan[`parent${n}_name`]} onChange={v => update(d => { d[`parent${n}_name`] = v })} /></Field>
        <Field label="Emoji"><Select value={plan[`parent${n}_emoji`]} options={EMOJIS} onChange={v => update(d => { d[`parent${n}_emoji`] = v })} /></Field>
        <Field label={`Age in ${plan.current_year}`}><NumberInput value={plan[pk(who, 'age')]} min={16} max={100} step={1} onChange={v => set('age', Math.round(v))} /></Field>
        <Field label="Plan until age" hint="Life expectancy used to end the projection"><NumberInput value={plan[pk(who, 'death_age')]} min={60} max={115} step={1} onChange={v => set('death_age', Math.round(v))} /></Field>
        <Field label="Savings & investments" hint="Cash, brokerage and retirement accounts. Exclude home equity — homes are added under Homes.">
          <Money value={nw} onChange={v => set('net_worth', v)} /></Field>
        <Field label="…of which pre-tax (401k/IRA)" hint="Withdrawals from pre-tax accounts are taxed as income">
          <Money value={plan[pk(who, 'pretax_balance')]} max={Math.max(nw, 0)} onChange={v => set('pretax_balance', v)} /></Field>
        <Field label="Retirement age"><NumberInput value={plan[pk(who, 'retirement_age')]} min={30} max={85} step={1} onChange={v => set('retirement_age', Math.round(v))} /></Field>
        <Field label="Social Security claim age" hint="62–70. Defaults to your retirement age (at least 62).">
          <NumberInput value={claim} min={62} max={70} step={1} onChange={v => set('ss_claim_age', Math.round(v))} /></Field>
        <Field label="SS benefit at 67 (monthly)" hint="From your ssa.gov statement, in today's dollars" cite={<Cite id="ssa_claiming" />}>
          <Money value={plan[pk(who, 'ss_benefit')]} step={50} onChange={v => set('ss_benefit', v)} /></Field>
        <div className="flex flex-col justify-end pb-1.5">
          <div className="text-[12.5px] text-muted">Claiming at {claim}</div>
          <div className="font-semibold tnum">{money(plan[pk(who, 'ss_benefit')] * ssFactor(claim) * 12, { compact: false })}/yr <span className="text-muted font-normal text-[12.5px]">today’s $</span></div>
        </div>
      </div>
    </Card>
  )
}

function IncomeCard({ who }: { who: 'X' | 'Y' }) {
  const { plan, update } = usePlan()
  const n = who === 'X' ? '1' : '2'
  const phases: any[] = plan[pk(who, 'career_phases')] || []
  const jobs: any[] = plan[pk(who, 'job_changes')] || []
  const mode = phases.length ? 'phases' : 'simple'
  const setMode = (m: string) => update(d => {
    if (m === 'phases' && !phases.length) {
      d[pk(who, 'career_phases')] = [{ start_age: d[pk(who, 'age')], end_age: d[pk(who, 'retirement_age')], philosophy: 'Stable',
        base_salary: d[pk(who, 'income')], annual_raise_pct: d[pk(who, 'raise')], annual_bonus_pct: 0, rsu_annual_grant: 0,
        rsu_vesting_years: 4, stock_options_grant: 0, stock_options_growth_pct: 0, stock_options_liquidity_year: 0, label: 'Current job' }]
    }
    if (m === 'simple') d[pk(who, 'career_phases')] = []
  })
  const setPhase = (i: number, k: string, v: any) => update(d => { d[pk(who, 'career_phases')][i][k] = v })

  return (
    <Card title={`${plan[`parent${n}_name`]}'s income`} subtitle="Salary is in nominal dollars and grows by the raise %"
      action={<Segmented value={mode} onChange={setMode} options={[{ value: 'simple', label: 'Simple' }, { value: 'phases', label: 'Career phases' }]} />}>
      {mode === 'simple' ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Current annual income"><Money value={plan[pk(who, 'income')]} onChange={v => update(d => { d[pk(who, 'income')] = v })} /></Field>
            <Field label="Annual raise"><Percent value={plan[pk(who, 'raise')]} onChange={v => update(d => { d[pk(who, 'raise')] = v })} /></Field>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12.5px] font-medium text-ink2">Job changes</span>
              <Button size="sm" variant="ghost" onClick={() => update(d => { d[pk(who, 'job_changes')] = [...jobs, { Year: plan.current_year + 2, 'New Income': Math.round(plan[pk(who, 'income')] * 1.15) }] })}><Plus size={14} />Add</Button>
            </div>
            {jobs.length === 0 && <p className="text-sm text-muted">No job changes planned.</p>}
            <div className="space-y-2">
              {jobs.map((j, i) => (
                <div key={i} className="grid grid-cols-[90px_1fr_100px_32px] gap-2 items-center">
                  <NumberInput value={j.Year} step={1} onChange={v => update(d => { d[pk(who, 'job_changes')][i].Year = Math.round(v) })} />
                  <Money value={j['New Income']} onChange={v => update(d => { d[pk(who, 'job_changes')][i]['New Income'] = v })} />
                  <NumberInput value={j['New Raise %'] ?? null} placeholder="raise" suffix="%" decimals={2}
                    onChange={v => update(d => { d[pk(who, 'job_changes')][i]['New Raise %'] = v })} />
                  <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d[pk(who, 'job_changes')].splice(i, 1) })}><Trash2 size={15} /></button>
                </div>
              ))}
            </div>
            {jobs.length > 0 && <p className="text-xs text-muted mt-2">Year · new salary · optional new raise % (blank keeps the current raise)</p>}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {phases.map((ph, i) => (
            <div key={i} className="rounded-lg border border-line p-3.5 space-y-3">
              <div className="flex items-center gap-2">
                <Briefcase size={15} className="text-muted" />
                <input className="flex-1 bg-transparent font-medium outline-none" value={ph.label} placeholder="Phase name" onChange={e => setPhase(i, 'label', e.target.value)} />
                <Badge>ages {ph.start_age}–{ph.end_age}</Badge>
                <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d[pk(who, 'career_phases')].splice(i, 1) })}><Trash2 size={15} /></button>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Field label="From age"><NumberInput value={ph.start_age} step={1} onChange={v => setPhase(i, 'start_age', Math.round(v))} /></Field>
                <Field label="To age"><NumberInput value={ph.end_age} step={1} onChange={v => setPhase(i, 'end_age', Math.round(v))} /></Field>
                <Field label="Style" hint="Choosing a style fills in its typical raise and bonus"><Select value={ph.philosophy} options={PHILOSOPHIES} onChange={v => update(d => {
                  const x = d[pk(who, 'career_phases')][i]; x.philosophy = v
                  const def = STYLE_DEFAULTS[v]; if (def) { x.annual_raise_pct = def.raise; x.annual_bonus_pct = def.bonus } })} /></Field>
                <Field label="Base salary"><Money value={ph.base_salary} onChange={v => setPhase(i, 'base_salary', v)} /></Field>
                <Field label="Raise"><Percent value={ph.annual_raise_pct} onChange={v => setPhase(i, 'annual_raise_pct', v)} /></Field>
                <Field label="Bonus"><Percent value={ph.annual_bonus_pct} onChange={v => setPhase(i, 'annual_bonus_pct', v)} /></Field>
                <Field label="RSUs / year"><Money value={ph.rsu_annual_grant} onChange={v => setPhase(i, 'rsu_annual_grant', v)} /></Field>
                {ph.rsu_annual_grant > 0 && <Field label="Vesting (years)" hint="Each year's grant vests evenly over this period, so RSU income ramps up"><NumberInput value={ph.rsu_vesting_years ?? 4} min={1} max={6} step={1} onChange={v => setPhase(i, 'rsu_vesting_years', Math.round(v))} /></Field>}
                <Field label="Stock options grant"><Money value={ph.stock_options_grant} onChange={v => setPhase(i, 'stock_options_grant', v)} /></Field>
                {ph.stock_options_grant > 0 && <>
                  <Field label="Options growth"><Percent value={ph.stock_options_growth_pct} onChange={v => setPhase(i, 'stock_options_growth_pct', v)} /></Field>
                  <Field label="Liquidity year"><NumberInput value={ph.stock_options_liquidity_year} step={1} onChange={v => setPhase(i, 'stock_options_liquidity_year', Math.round(v))} /></Field>
                </>}
              </div>
              {ph.end_age > plan[pk(who, 'retirement_age')] && <p className="text-[12.5px] text-warn">This phase runs past the retirement age ({plan[pk(who, 'retirement_age')]}); income after retiring is not counted.</p>}
            </div>
          ))}
          <Button size="sm" onClick={() => update(d => {
            const ps = d[pk(who, 'career_phases')]; const last = ps[ps.length - 1]
            ps.push({ ...last, start_age: last.end_age, end_age: Math.max(last.end_age + 5, d[pk(who, 'retirement_age')]), label: 'Next phase' })
          })}><Plus size={14} />Add phase</Button>
          <Note>Career phases replace the simple income model. Income is zero for ages not covered by a phase, and always stops at retirement age.</Note>
        </div>
      )}
    </Card>
  )
}

export default function People() {
  const { plan, update, proj, single, names } = usePlan()
  const { Sources } = useCites(PEOPLE_SRC)
  const marriageOpts = ['N/A', ...Array.from({ length: plan.current_year - 1969 }, (_, i) => String(plan.current_year - i))]
  const incomeData = (proj?.rows || []).filter((r: any) => r.wages1 + r.wages2 + r.ss_income > 0).map((r: any) => ({
    year: r.year, w1: r.wages1, w2: r.wages2, ss: r.ss_income }))
  return (
    <div className="space-y-5">
      <PageHeader title="People & income" subtitle="Who is in the plan, what they earn and when they retire" />
      <Card title="Household">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <Field label="Current year"><NumberInput value={plan.current_year} step={1} onChange={v => update(d => { d.current_year = Math.round(v) })} /></Field>
          <Field label="Marriage year" hint="When individual assets became shared">
            <Select value={String(plan.marriage_year ?? 'N/A')} options={marriageOpts} onChange={v => update(d => { d.marriage_year = v === 'N/A' ? 'N/A' : Number(v) })} /></Field>
          <Field label="Money is managed" hint="Pooled: one household pot. Separate: each person keeps their own savings and shared costs are split.">
            <Select value={plan.finance_mode} options={['Pooled', 'Separate']} onChange={v => update(d => { d.finance_mode = v })} /></Field>
          {plan.finance_mode === 'Separate'
            ? <Field label={`${names[0]} pays of shared costs`}><Percent value={plan.shared_expense_split_pct} decimals={0} onChange={v => update(d => { d.shared_expense_split_pct = v })} /></Field>
            : <div className="pb-2"><Toggle checked={single} label="Planning for one person"
                onChange={v => update(d => { d.parent2_name = v ? 'N/A' : 'Partner'; if (v) { d.parentY_income = 0; d.parentY_net_worth = 0; d.parentY_ss_benefit = 0; d.parentY_expenses = Object.fromEntries(Object.keys(d.parentY_expenses || {}).map(k => [k, 0])) } })} /></div>}
        </div>
        {plan.finance_mode === 'Separate' && <div className="mt-4"><Toggle checked={single} label="Planning for one person"
          onChange={v => update(d => { d.parent2_name = v ? 'N/A' : 'Partner' })} /></div>}
      </Card>
      <Grid cols={2}>
        <PersonCard who="X" />
        {!single && <PersonCard who="Y" />}
      </Grid>
      <Grid cols={2}>
        <IncomeCard who="X" />
        {!single && <IncomeCard who="Y" />}
      </Grid>
      {incomeData.length > 0 && (
        <Card title="Income over time" subtitle="Salaries and Social Security, nominal dollars">
          <LinesChart data={incomeData} series={[{ key: 'w1', label: names[0] }, ...(single ? [] : [{ key: 'w2', label: names[1] }]), { key: 'ss', label: 'Social Security' }]} />
        </Card>
      )}
      <Sources className="px-1" />
    </div>
  )
}
