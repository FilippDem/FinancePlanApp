/** Dashboard strip: the decisions you're weighing in the playground (or a way in when there are none). */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, ArrowRight } from 'lucide-react'
import { usePlan } from '../lib/store'
import { CATALOG, DEF, colorFor, create, type WhatIf } from '../lib/whatifs'

export function DecisionsStrip() {
  const { plan, update } = usePlan()
  const nav = useNavigate()
  const list: WhatIf[] = plan.whatifs || []
  const on = list.filter(w => w.on && DEF[w.key])
  const quick = CATALOG.filter(d => d.quick).slice(0, 5)
  const tryIt = (key: string) => { update(d => { d.whatifs = [...(d.whatifs || []), create(d, key)] }); nav('/decisions') }
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-accent/25 bg-gradient-to-r from-accentSoft/80 to-surface px-4 py-3">
      <Sparkles size={18} className="text-accent" />
      <span className="font-medium text-[14px] mr-1">{on.length ? `Weighing ${on.length} decision${on.length > 1 ? 's' : ''}:` : 'Weighing a decision?'}</span>
      {on.length
        ? on.map(w => <button key={w.id} onClick={() => nav('/decisions')} className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full text-white text-[12.5px] font-medium"
            style={{ background: colorFor(list, w.id) }}>{DEF[w.key].emoji} {w.name || DEF[w.key].label}</button>)
        : quick.map(d => <button key={d.key} onClick={() => tryIt(d.key)} className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full border border-line bg-surface text-[12.5px] hover:border-accent/50">
            {d.emoji} {d.quick}</button>)}
      <button onClick={() => nav('/decisions')} className="ml-auto inline-flex items-center gap-1 text-[13px] font-medium text-accent hover:underline">
        Open the decision playground<ArrowRight size={14} /></button>
    </div>)
}
