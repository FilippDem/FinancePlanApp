import React from 'react'
import { usePlan } from '../lib/store'
import { pct } from '../lib/format'
import { Card, Field, Percent, Toggle } from './ui'

const DEF = { enabled: false, lower: 20, cut: 10, upper: 20, raise: 10, retired_only: true }

/** Spending guardrails for Monte Carlo: cut flexible spending in bad markets, raise it in good ones. */
export function GuardrailsCard() {
  const { plan, update, mc } = usePlan()
  const g = { ...DEF, ...(plan.guardrails || {}) }
  const set = (k: string, v: any) => update(d => { d.guardrails = { ...DEF, ...(d.guardrails || {}), [k]: v } })
  const st = mc?.guardrails
  return (
    <Card title="Spending guardrails" subtitle="Real families spend less when markets fall. With guardrails, each simulation cuts flexible spending (personal, household and recurring, not housing, kids or healthcare) while its savings are well below the expected path, and allows a raise while they are well above.">
      <div className="space-y-4">
        <Toggle checked={g.enabled} onChange={v => set('enabled', v)} label="Use guardrails in Monte Carlo" hint="The expected-path projection is unchanged; only the simulations adapt." />
        {g.enabled && <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Field label="Cut when savings are below the path by"><Percent value={g.lower} decimals={0} onChange={v => set('lower', v)} /></Field>
            <Field label="Cut flexible spending by"><Percent value={g.cut} decimals={0} onChange={v => set('cut', v)} /></Field>
            <Field label="Raise when above the path by"><Percent value={g.upper} decimals={0} onChange={v => set('upper', v)} /></Field>
            <Field label="Raise flexible spending by"><Percent value={g.raise} decimals={0} onChange={v => set('raise', v)} /></Field>
          </div>
          <Toggle checked={g.retired_only} onChange={v => set('retired_only', v)} label="Only after retiring" />
          {st && <p className="text-[12.5px] text-ink2">In the latest simulations: {pct(st.prob_any_cut, 0)} of paths needed a cut at some point; retired years were cut {pct(st.share_years_cut, 0)} of the time and raised {pct(st.share_years_raised, 0)}.</p>}
        </>}
      </div>
    </Card>
  )
}
