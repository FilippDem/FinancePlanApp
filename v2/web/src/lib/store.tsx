import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api'

export type Plan = Record<string, any>
type SaveState = 'saved' | 'dirty' | 'saving' | 'error'

interface Ctx {
  plan: Plan
  update: (fn: (d: Plan) => void) => void
  replacePlan: (p: Plan) => Promise<void>
  saveState: SaveState
  lastSaved: string | null
  proj: any | null
  projecting: boolean
  mc: any | null
  mcLoading: boolean
  runMC: (n?: number) => Promise<void>
  reference: any | null
  names: [string, string]
  single: boolean
  household: any
}

const PlanCtx = createContext<Ctx | null>(null)
export const usePlan = () => {
  const c = useContext(PlanCtx)
  if (!c) throw new Error('usePlan outside provider')
  return c
}

export function isSingle(p: Plan) {
  const n2 = p.parent2_name ?? ''
  return n2 === 'N/A' || n2 === ''
}

export function PlanProvider({ initial, lastSaved: ls, household, children }:
  { initial: Plan; lastSaved: string | null; household: any; children: React.ReactNode }) {
  const [plan, setPlan] = useState<Plan>(initial)
  const [saveState, setSaveState] = useState<SaveState>('saved')
  const [lastSaved, setLastSaved] = useState<string | null>(ls)
  const [proj, setProj] = useState<any>(null)
  const [projecting, setProjecting] = useState(false)
  const [mc, setMc] = useState<any>(null)
  const [mcLoading, setMcLoading] = useState(false)
  const [reference, setReference] = useState<any>(null)
  const dirtyRef = useRef(false)
  const planRef = useRef(plan)
  planRef.current = plan

  useEffect(() => { api.reference().then(setReference).catch(() => {}) }, [])

  const update = useCallback((fn: (d: Plan) => void) => {
    setPlan(prev => {
      const d = structuredClone(prev)
      fn(d)
      return d
    })
    dirtyRef.current = true
    setSaveState('dirty')
  }, [])

  const replacePlan = useCallback(async (p: Plan) => {
    const { plan: norm } = await api.normalize(p)
    setPlan(norm)
    dirtyRef.current = true
    setSaveState('dirty')
  }, [])

  // autosave (debounced) — the server merges, so unknown keys are never lost
  useEffect(() => {
    if (!dirtyRef.current) return
    const t = setTimeout(async () => {
      setSaveState('saving')
      try {
        const r = await api.putPlan(planRef.current)
        dirtyRef.current = false
        setLastSaved(r.last_saved)
        setSaveState('saved')
      } catch {
        setSaveState('error')
      }
    }, 900)
    return () => clearTimeout(t)
  }, [plan])

  // live projection
  const projSeq = useRef(0)
  useEffect(() => {
    const seq = ++projSeq.current
    setProjecting(true)
    const t = setTimeout(async () => {
      try {
        const r = await api.project(plan)
        if (seq === projSeq.current) setProj(r)
      } finally {
        if (seq === projSeq.current) setProjecting(false)
      }
    }, 200)
    return () => clearTimeout(t)
  }, [plan])

  // quick Monte Carlo for the dashboard (debounced)
  const mcSeq = useRef(0)
  const runMC = useCallback(async (n?: number) => {
    const seq = ++mcSeq.current
    setMcLoading(true)
    try {
      const r = await api.monteCarlo(planRef.current, n ?? planRef.current.mc_simulations ?? 1000)
      if (seq === mcSeq.current) setMc(r)
    } finally {
      if (seq === mcSeq.current) setMcLoading(false)
    }
  }, [])
  useEffect(() => {
    const t = setTimeout(() => runMC(), 700)
    return () => clearTimeout(t)
  }, [plan, runMC])

  const single = isSingle(plan)
  const names: [string, string] = [plan.parent1_name || 'Person 1', single ? '' : (plan.parent2_name || 'Person 2')]

  const value = useMemo(() => ({
    plan, update, replacePlan, saveState, lastSaved, proj, projecting, mc, mcLoading, runMC, reference, names, single, household,
  }), [plan, update, replacePlan, saveState, lastSaved, proj, projecting, mc, mcLoading, runMC, reference, names[0], names[1], single, household])

  return <PlanCtx.Provider value={value}>{children}</PlanCtx.Provider>
}

/** Helpers to read/write person-scoped keys: who = 'X' | 'Y' */
export const pk = (who: 'X' | 'Y', key: string) => `parent${who}_${key}`
