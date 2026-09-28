import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { usePlan } from './store'

/** Goals with progress and Monte Carlo chances (debounced); falls back to the projection's goals. */
export function useGoals(n = 300) {
  const { plan, proj } = usePlan()
  const [goals, setGoals] = useState<any[] | null>(null)
  const [busy, setBusy] = useState(false)
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  useEffect(() => {
    if (!(plan.goals || []).length) { setGoals([]); return }
    const s = ++seq.current
    setBusy(true)
    const t = setTimeout(() => {
      api.goals(plan, n).then(r => { if (s === seq.current) setGoals(r.goals) }).catch(() => {}).finally(() => { if (s === seq.current) setBusy(false) })
    }, 800)
    return () => clearTimeout(t)
  }, [key])
  return { goals: goals ?? proj?.goals ?? [], busy }
}
