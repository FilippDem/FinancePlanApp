import React, { useEffect, useRef, useState } from 'react'
import { Wallet, CalendarClock, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct } from '../lib/format'
import { Card } from './ui'

const BAR = 0.9   // headroom is measured against a 90% chance the money lasts

/** When the success rate is near 100% it stops telling you anything. Lead with what the plan can afford instead
 *  (MaxiFi's "living standard" / Income Lab's "how much can I spend"): extra spending per year and how much earlier
 *  you could retire while keeping a 90% chance that the money lasts. */
export function SpendingPower() {
  const { plan, proj, mc, names, single } = usePlan()
  const [res, setRes] = useState<any>(null)
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  const show = !!mc && mc.success_rate >= 0.95
  useEffect(() => {
    if (!show) return
    const s = ++seq.current
    const tm = setTimeout(() => { api.solve(plan, BAR).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}) }, 1200)
    return () => clearTimeout(tm)
  }, [key, show])
  if (!show) return null
  const r0 = proj?.rows?.[0]
  const everyday = r0 ? r0.exp_person1 + r0.exp_person2 + r0.exp_family + r0.exp_recurring : 0
  const more = res?.levers?.find((l: any) => l.id === 'spend_more')
  const earlier = res?.levers?.find((l: any) => l.id === 'retire_earlier')
  const extra = more?.feasible ? everyday * more.amount / 100 : 0
  // the solver searches up to max_tried; hitting it means the real room is larger than shown
  const moreCap = more?.feasible && more.amount >= more.max_tried
  const earlierCap = earlier?.feasible && earlier.amount >= earlier.max_tried
  const retireAt = earlier?.feasible ? `${names[0]} at ${plan.parentX_retirement_age - earlier.amount}${single ? '' : `, ${names[1]} at ${plan.parentY_retirement_age - earlier.amount}`}` : ''
  return (
    <Card title="What your plan can afford" subtitle={`Your money lasts in ${pct(mc.success_rate, 0)} of simulations, so the success rate alone says little. This is the room you have while keeping at least a ${pct(BAR, 0)} chance.`}>
      {!res ? <div className="h-16 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Working out your headroom…</div> : (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex gap-3">
            <Wallet className="text-accent shrink-0 mt-1" size={20} />
            <div>
              <div className="text-[12.5px] text-muted">Extra everyday spending, every year</div>
              <div className="text-2xl font-semibold tnum">{more?.feasible ? `+${money(extra)}${moreCap ? ' or more' : ''}` : 'Little room'}</div>
              <div className="text-[12.5px] text-ink2">{more?.feasible ? `${more.amount}% more than today's ${money(everyday)} a year, for life` : 'Spending more would drop below the bar'}</div>
            </div>
          </div>
          <div className="flex gap-3">
            <CalendarClock className="text-accent shrink-0 mt-1" size={20} />
            <div>
              <div className="text-[12.5px] text-muted">Or retire earlier</div>
              <div className="text-2xl font-semibold tnum">{earlier?.feasible ? `${earlier.amount}${earlierCap ? '+' : ''} year${earlier.amount === 1 ? '' : 's'} sooner` : 'No earlier'}</div>
              <div className="text-[12.5px] text-ink2">{earlier?.feasible ? retireAt : earlier?.note || 'Retiring earlier would drop below the bar'}</div>
            </div>
          </div>
        </div>)}
      <p className="text-[12px] text-muted mt-3">Each option on its own, tested on the same market simulations.{(moreCap || earlierCap) ? ' "Or more" / "+": the search stops there, and your real room is larger.' : ''} Apply one from "What would it take?" below.</p>
    </Card>
  )
}
