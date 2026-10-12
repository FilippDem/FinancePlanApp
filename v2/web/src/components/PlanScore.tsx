import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Gauge, CheckCircle2, AlertTriangle, CircleDot, Loader2, ChevronRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { Card } from './ui'

const ICON = { good: <CheckCircle2 size={15} className="text-good" />, ok: <CircleDot size={15} className="text-warn" />,
  bad: <AlertTriangle size={15} className="text-bad" /> } as Record<string, React.ReactNode>

/** Plan score: the checks planners look at first (engine/finplan/health.py), each linking to where you fix it. */
export function PlanScore() {
  const { plan } = usePlan()
  const nav = useNavigate()
  const [res, setRes] = useState<any>(null)
  const seq = useRef(0)
  const key = JSON.stringify(plan)
  useEffect(() => {
    const s = ++seq.current
    const tm = setTimeout(() => { api.planHealth(plan).then(r => { if (s === seq.current) setRes(r) }).catch(() => {}) }, 1000)
    return () => clearTimeout(tm)
  }, [key])
  const tone = !res ? 'text-muted' : res.score >= 85 ? 'text-good' : res.score >= 70 ? 'text-accent' : res.score >= 50 ? 'text-warn' : 'text-bad'
  return (
    <Card title={<span className="flex items-center gap-2"><Gauge size={16} className="text-accent" />Plan score</span>}
      subtitle="Common rules of thumb, checked against your plan. Click a line to fix it."
      action={res && <span className={`text-xl font-semibold tnum ${tone}`}>{res.score}<span className="text-[13px] text-muted font-normal">/100 · {res.grade}</span></span>}>
      {!res ? <div className="h-24 flex items-center gap-2 text-sm text-muted"><Loader2 size={15} className="animate-spin" />Checking…</div> : (
        <ul className="divide-y divide-line -my-1">
          {res.items.map((i: any) => (
            <li key={i.id}>
              <button onClick={() => nav(i.to)} title={i.detail} className="w-full flex items-center gap-2.5 py-2 text-left hover:bg-sunken/60 rounded-md px-1">
                {ICON[i.status]}
                <span className="flex-1 text-sm">{i.label}</span>
                <span className="text-sm tnum text-ink2">{i.value}</span>
                <ChevronRight size={14} className="text-muted" />
              </button>
            </li>))}
        </ul>)}
    </Card>
  )
}
