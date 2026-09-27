import React, { useEffect, useRef, useState } from 'react'
import { Target, Loader2, CheckCircle2, ArrowRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct } from '../lib/format'
import { Card, Segmented, Button } from './ui'

const TARGETS = ['0.75', '0.8', '0.85', '0.9', '0.95'] as const

function describe(l: any): string {
  const x = l.amount
  switch (l.id) {
    case 'retire_later': return `Retire ${x} year${x === 1 ? '' : 's'} later`
    case 'retire_earlier': return `Retire ${x} year${x === 1 ? '' : 's'} earlier`
    case 'spend_less': return `Spend ${x}% less on everyday living`
    case 'spend_more': return `Spend ${x}% more on everyday living`
    case 'claim_later': return `Claim Social Security ${x} year${x === 1 ? '' : 's'} later (up to 70)`
    case 'combined': {
      const q = l.parts || {}
      const bits = [q.retire_later ? `retire ${q.retire_later} yr later` : '', q.spend_less ? `spend ${q.spend_less}% less` : '', q.claim_later ? `claim SS ${q.claim_later} yr later` : ''].filter(Boolean)
      return `A mix: ${bits.join(', ') || 'small changes'}`
    }
    default: return l.label
  }
}

/** "What would it take?": the smallest single change (retire later, spend less, claim Social Security later, or a mix) that reaches a
 *  target chance of success, or the headroom when the plan is already there. One click applies it. */
export function WhatItTakes() {
  const { plan, update } = usePlan()
  const [target, setTarget] = useState<string>(() => { try { return localStorage.getItem('fp_target') || '0.85' } catch { return '0.85' } })
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [applied, setApplied] = useState('')
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  useEffect(() => { try { localStorage.setItem('fp_target', target) } catch { /* */ } }, [target])
  useEffect(() => {
    const s = ++seq.current
    setBusy(true)
    const tm = setTimeout(() => {
      api.solve(plan, +target).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}).finally(() => { if (s === seq.current) setBusy(false) })
    }, 900)
    return () => clearTimeout(tm)
  }, [key, target])

  const apply = async (l: any) => {
    try { await api.saveScenario(`Before: ${describe(l)}`, plan) } catch { /* the change can be undone from Version history too */ }
    update(d => { Object.assign(d, structuredClone(l.patch)) })
    setApplied(`${describe(l)}: applied. The previous plan is saved as a scenario.`)
  }

  return (
    <Card title={<span className="flex items-center gap-2"><Target size={16} className="text-accent" />What would it take?</span>}
      subtitle={`The smallest single change that gets the chance your money lasts to ${pct(+target, 0)}. Each option is tested on its own with the same market simulations.`}
      action={<Segmented value={target as any} onChange={v => { setTarget(v); setApplied('') }} options={TARGETS.map(t => ({ value: t, label: pct(+t, 0) }))} />}>
      {!res ? <div className="h-24 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Testing options…</div> : (
        <div className={busy ? 'opacity-60 transition-opacity' : ''}>
          <div className="text-sm mb-3">
            {res.reached
              ? <span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-good" />You're at <b>{pct(res.success, 0)}</b>, above {pct(res.target, 0)}. Room to spare:</span>
              : res.levers.some((l: any) => l.feasible)
                ? <span>Today: <b>{pct(res.success, 0)}</b>. Any one of these gets you to {pct(res.target, 0)}:</span>
                : <span>Today: <b>{pct(res.success, 0)}</b>. No single change below reaches {pct(res.target, 0)}. Try a lower target, or combine changes on the Retirement and Spending pages:</span>}
          </div>
          <ul className="divide-y divide-line">
            {res.levers.map((l: any) => (
              <li key={l.id} className="flex flex-wrap items-center gap-3 py-2.5">
                {!l.applicable ? <span className="text-sm text-muted">{l.label}: {l.note}</span>
                  : !l.feasible ? <span className="text-sm text-muted">{l.label}: {res.reached ? 'no room without dropping below the target' : `not enough on its own (${l.id === 'combined' ? `retiring 5 yrs later, spending 25% less and claiming 3 yrs later` : `${l.max_tried}${l.unit === '%' ? '%' : ' years'}`} reaches ${pct(l.success_after, 0)})`}</span>
                  : <>
                    <span className="flex-1 min-w-[220px] text-sm font-medium">{describe(l)}</span>
                    <span className="text-sm tnum text-ink2 flex items-center gap-1">{pct(res.success, 0)}<ArrowRight size={13} />{pct(l.success_after, 0)}</span>
                    <Button size="sm" onClick={() => apply(l)}>Apply</Button>
                  </>}
              </li>))}
          </ul>
          {applied && <p className="text-[12.5px] text-good mt-2">{applied}</p>}
          <p className="text-[12px] text-muted mt-2">Spending changes apply to personal and household costs (not housing, kids or healthcare) and recurring costs. Money you don't spend is already saved in the plan, so "save more" is the same lever as "spend less".</p>
        </div>)}
    </Card>
  )
}
