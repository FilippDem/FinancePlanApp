import React, { useEffect, useRef, useState } from 'react'
import { Wallet, Loader2, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, clsx } from '../lib/format'
import { Card, Segmented, Button } from './ui'

const TARGETS = ['0.75', '0.8', '0.85', '0.9'] as const

/** "You can spend $X a month and keep an 85% chance": the flexible spending that meets a target success rate. */
export function SafeSpending() {
  const { plan, update } = usePlan()
  const nav = useNavigate()
  const [target, setTarget] = useState<string>(() => { try { return localStorage.getItem('fp_safe_target') || '0.85' } catch { return '0.85' } })
  const [res, setRes] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  useEffect(() => { try { localStorage.setItem('fp_safe_target', target) } catch { /* */ } }, [target])
  useEffect(() => {
    const s = ++seq.current
    setBusy(true)
    const t = setTimeout(() => api.safeSpending(plan, +target).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}).finally(() => s === seq.current && setBusy(false)), 1000)
    return () => clearTimeout(t)
  }, [key, target])
  const apply = async () => {
    if (!res?.patch) return
    try { await api.saveScenario(`Before safe spending (${pct(+target, 0)})`, plan) } catch { /* */ }
    update(d => { Object.assign(d, structuredClone(res.patch)) })
    setMsg('Applied. The previous plan is saved as a scenario.')
  }
  const up = res && res.delta_month > 0
  return (
    <Card title={<span className="flex items-center gap-2"><Wallet size={16} className="text-accent" />Safe spending</span>}
      subtitle="The most you can spend on flexible items (personal, household and recurring costs, not housing, kids or healthcare) and keep this chance your money lasts"
      action={<Segmented value={target as any} onChange={v => { setTarget(v); setMsg('') }} options={TARGETS.map(t => ({ value: t, label: pct(+t, 0) }))} />}>
      {!res ? <div className="h-16 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Working it out…</div> : (
        <div className={clsx('space-y-3', busy && 'opacity-60')}>
          {res.multiplier == null
            ? <p className="text-sm">Even cutting flexible spending by 70% doesn't reach {pct(res.target, 0)} (today {pct(res.success, 0)}). The gap is in fixed costs, income or timing; see “What would it take?”.</p>
            : <div className="flex flex-wrap items-end gap-6">
              <div><div className="text-[12.5px] text-muted">Safe flexible spending</div><div className="text-[26px] font-semibold tnum">{money(res.safe / 12, { compact: false })}<span className="text-sm text-muted font-normal">/month</span></div></div>
              <div><div className="text-[12.5px] text-muted">Planned now</div><div className="text-lg tnum">{money(res.current / 12, { compact: false })}/month</div></div>
              <div className={clsx('text-lg font-semibold tnum', up ? 'text-good' : 'text-bad')}>{up ? '+' : '−'}{money(Math.abs(res.delta_month), { compact: false })}/month
                <div className="text-[12px] font-normal text-muted">{up ? 'room to spend more' : 'to cut to reach the target'}</div></div>
              {res.multiplier >= 3 && <p className="text-[12.5px] text-muted">(capped at 3× today's spending)</p>}
            </div>}
          <div className="flex flex-wrap items-center gap-2">
            {res.patch && Math.abs(res.delta_month) >= 10 && <Button size="sm" onClick={apply}>Set my spending to this</Button>}
            <Button size="sm" variant="ghost" onClick={() => nav('/assumptions')}>Spending guardrails<ArrowRight size={13} /></Button>
            {msg && <span className="text-[12.5px] text-good">{msg}</span>}
          </div>
          <p className="text-[12px] text-muted">Today's dollars, grows with inflation. Today: {pct(res.success, 0)} chance. With guardrails on (Assumptions), the simulations also trim spending in bad markets.</p>
        </div>)}
    </Card>
  )
}
