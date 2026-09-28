import React, { useState } from 'react'
import { Plus, Trash2, Target, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { useGoals } from '../lib/useGoals'
import { Card, PageHeader, Button, Empty, Note } from '../components/ui'
import { GOAL_TYPES, GoalRow, GoalEditor, newGoal } from '../components/Extras'

export default function Goals() {
  const { plan, update } = usePlan()
  const { goals, busy } = useGoals(400)
  const [open, setOpen] = useState<string | null>(null)
  const list: any[] = plan.goals || []
  const byId = Object.fromEntries(goals.map((g: any) => [g.id, g]))
  const add = (type: string) => { const g = newGoal(plan, type); update(d => { (d.goals ||= []).push(g) }); setOpen(g.id) }
  return (
    <div className="space-y-5">
      <PageHeader title="Goals" subtitle="Milestones you want to hit, checked against your plan and thousands of market simulations"
        actions={busy ? <span className="text-[12.5px] text-muted flex items-center gap-1.5"><Loader2 size={13} className="animate-spin" />Updating chances…</span> : null} />
      <Card title="Add a goal" subtitle="You can also drop goals straight onto the Life timeline">
        <div className="flex flex-wrap gap-2">{GOAL_TYPES.map(t => <Button key={t.value} size="sm" onClick={() => add(t.value)}><Plus size={13} />{t.label}</Button>)}</div>
      </Card>
      <Card title={<span className="flex items-center gap-2"><Target size={16} className="text-accent" />Your goals</span>} pad={false}>
        {list.length === 0 ? <Empty title="No goals yet" body="Add one above: for example work optional by 55, $2M by 60, or the house paid off by retirement." /> : (
          <ul className="divide-y divide-line">
            {list.map((g, i) => {
              const ev = byId[g.id]
              return (
                <li key={g.id} className="px-5 py-1">
                  <div className="flex items-start gap-2">
                    <button className="mt-3 text-muted" onClick={() => setOpen(open === g.id ? null : g.id)} aria-label="Edit">{open === g.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
                    <div className="flex-1 min-w-0">{ev ? <GoalRow g={ev} /> : <div className="py-3 text-sm">{g.name}</div>}</div>
                    <button className="mt-2.5 p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" onClick={() => update(d => { d.goals.splice(i, 1) })}><Trash2 size={15} /></button>
                  </div>
                  {open === g.id && <div className="pl-6 pb-4 pt-1"><GoalEditor g={g} i={i} /></div>}
                </li>)
            })}
          </ul>)}
      </Card>
      <Note>On track means the expected path meets the goal and, where a chance is shown, at least 75% of market simulations do (at risk: 50–75%). Amounts are in today's dollars. Goals also show on the Dashboard and in every check-in.</Note>
    </div>
  )
}
