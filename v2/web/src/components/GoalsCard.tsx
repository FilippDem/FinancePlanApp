import React from 'react'
import { Target, ArrowRight, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { usePlan } from '../lib/store'
import { useGoals } from '../lib/useGoals'
import { Card, Button } from './ui'
import { GoalRow } from './Extras'

export function GoalsCard({ compact }: { compact?: boolean }) {
  const { plan } = usePlan()
  const nav = useNavigate()
  const { goals, busy } = useGoals()
  const list: any[] = plan.goals || []
  return (
    <Card title={<span className="flex items-center gap-2"><Target size={16} className="text-accent" />Goals{busy && <Loader2 size={13} className="animate-spin text-muted" />}</span>}
      action={<Button size="sm" variant="ghost" onClick={() => nav('/goals')}>{list.length ? 'All goals' : 'Add goals'}<ArrowRight size={14} /></Button>}>
      {list.length === 0 ? <p className="text-sm text-muted">Set milestones like “work optional by 55”, an emergency fund, college funded or the house paid off, and see your progress and odds.</p>
        : <div className="divide-y divide-line">{goals.slice(0, compact ? 4 : 20).map((g: any) => <GoalRow key={g.id} g={g} compact={compact} />)}</div>}
    </Card>
  )
}
