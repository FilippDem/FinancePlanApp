import React, { useMemo, useRef, useState } from 'react'
import { Plus, Trash2, Baby, Download, Upload, RotateCcw } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { Card, PageHeader, Field, NumberInput, TextInput, Select, Button, Empty, Badge, Grid, Stat, Note } from '../components/ui'
import { StackedBars } from '../components/charts'
import { useTodayDollars } from '../lib/hooks'

const STRATS = ['Conservative', 'Average', 'High-end']
const RANGES: [string, number, number][] = [['Infant 0–2', 0, 2], ['Toddler 3–5', 3, 5], ['Child 6–12', 6, 12], ['Teen 13–17', 13, 17], ['College 18–21', 18, 21], ['Young adult 22–30', 22, 30]]

function download(name: string, text: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv' }))
  a.download = name; a.click()
}

function ChildCard({ i }: { i: number }) {
  const { plan, update, reference } = usePlan()
  const c = plan.children_list[i]
  const [err, setErr] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const set = (k: string, v: any) => update(d => { d.children_list[i][k] = v })
  const age = plan.current_year - c.birth_year
  const locs = reference?.locations || ['Seattle']
  const rename = (v: string) => {
    const dup = plan.children_list.some((o: any, j: number) => j !== i && o.name.toLowerCase() === v.trim().toLowerCase())
    setErr(dup ? 'Another child already has this name' : '')
    if (!dup) set('name', v)
  }
  const exportCsv = async () => {
    const t = c.custom_expenses || await api.template('children', c.template_state, c.template_strategy, plan.current_year, plan.economic_params.inflation_rate)
    const cats = Object.keys(t)
    const lines = ['Age,' + cats.map(x => `"${x}"`).join(',')]
    for (let a = 0; a <= 30; a++) lines.push([a, ...cats.map(k => Math.round(t[k][a] || 0))].join(','))
    download(`${c.name}_costs_by_age.csv`, lines.join('\n'))
  }
  const importCsv = async (f: File) => {
    const text = await f.text()
    const [head, ...rows] = text.trim().split(/\r?\n/)
    const cats = head.split(',').slice(1).map(s => s.replace(/^"|"$/g, '').trim())
    if (rows.length !== 31) { setErr('CSV must have 31 rows (ages 0–30)'); return }
    const out: Record<string, number[]> = Object.fromEntries(cats.map(k => [k, []]))
    rows.forEach(r => { const v = r.split(','); cats.forEach((k, j) => out[k].push(parseFloat(v[j + 1]) || 0)) })
    set('custom_expenses', out); set('use_template', false); setErr('')
  }
  return (
    <Card title={<span className="flex items-center gap-2">{c.name}{c.custom_expenses && <Badge tone="accent">custom costs</Badge>}</span>}
      subtitle={age >= 0 ? `Age ${age} · born ${c.birth_year}` : `Arrives in ${-age} year${age === -1 ? '' : 's'} (${c.birth_year})`}
      action={<Button size="sm" variant="danger" onClick={() => update(d => { d.children_list.splice(i, 1) })}><Trash2 size={14} /></Button>}>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Name"><TextInput value={c.name} onChange={rename} /></Field>
        <Field label="Birth year"><NumberInput value={c.birth_year} step={1} onChange={v => set('birth_year', Math.round(v))} /></Field>
        <Field label="Cost template: where they grow up"><Select value={c.template_state} options={locs.includes(c.template_state) ? locs : [c.template_state, ...locs]} onChange={v => set('template_state', v)} /></Field>
        <Field label="Lifestyle"><Select value={c.template_strategy.replace(' (statistical)', '')} options={STRATS.includes(c.template_strategy.replace(' (statistical)', '')) ? STRATS : [c.template_strategy, ...STRATS]} onChange={v => set('template_strategy', v)} /></Field>
        <Field label="K-12 school"><Select value={c.school_type} options={['Public', 'Private']} onChange={v => set('school_type', v)} /></Field>
        <Field label="College"><Select value={c.college_type} options={['Public', 'Private']} onChange={v => set('college_type', v)} /></Field>
        <Field label="College location" className="col-span-2"><Select value={c.college_location} options={locs.includes(c.college_location) ? locs : [c.college_location, ...locs]} onChange={v => set('college_location', v)} /></Field>
      </div>
      {err && <p className="text-sm text-bad mt-2">{err}</p>}
      <div className="flex flex-wrap gap-2 mt-4">
        <Button size="sm" variant="ghost" onClick={exportCsv}><Download size={14} />Export costs CSV</Button>
        <Button size="sm" variant="ghost" onClick={() => fileRef.current?.click()}><Upload size={14} />Import custom CSV</Button>
        {c.custom_expenses && <Button size="sm" variant="ghost" onClick={() => update(d => { delete d.children_list[i].custom_expenses; d.children_list[i].use_template = true })}><RotateCcw size={14} />Back to template</Button>}
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => e.target.files?.[0] && importCsv(e.target.files[0])} />
      </div>
    </Card>
  )
}

export default function Kids() {
  const { plan, update, proj } = usePlan()
  const [today] = useTodayDollars()
  const kids: any[] = plan.children_list || []
  const { data, perChild } = useMemo(() => {
    const data: any[] = []
    const perChild: Record<string, { total: number; byAge: Record<number, number>; peak: [number, number] }> = {}
    for (const r of proj?.rows || []) {
      const o: any = { year: r.year }
      let any = false
      for (const c of r.details.children || []) {
        const v = today ? c.total / r.infl_index : c.total
        o[c.name] = v; any = true
        const p = perChild[c.name] ||= { total: 0, byAge: {}, peak: [0, 0] }
        p.total += v; p.byAge[c.age] = v
        if (v > p.peak[1]) p.peak = [c.age, v]
      }
      if (any) data.push(o)
    }
    return { data, perChild }
  }, [proj, today])

  const add = () => update(d => {
    let name = 'Child', n = 1
    while (d.children_list.some((c: any) => c.name.toLowerCase() === name.toLowerCase())) name = `Child ${++n}`
    d.children_list.push({ name, birth_year: d.current_year + 1, use_template: true, template_state: 'Seattle', template_strategy: 'Average',
      school_type: 'Public', college_type: 'Public', college_location: 'Seattle' })
  })

  return (
    <div className="space-y-5">
      <PageHeader title="Kids" subtitle="Costs by age from regional templates, plus private school and college"
        actions={<Button variant="primary" onClick={add}><Plus size={15} />Add child</Button>} />
      {kids.length === 0 ? <Card><Empty icon={<Baby size={20} />} title="No children in the plan" body="Add current or future children to include their costs from birth through age 30." action={<Button variant="primary" onClick={add}><Plus size={15} />Add child</Button>} /></Card> : <>
        <Card title="Children's costs by year" subtitle={today ? "Today's dollars" : 'Nominal dollars'}>
          <StackedBars data={data} xKey="year" series={kids.slice(0, 8).map(k => ({ key: k.name, label: k.name }))} />
        </Card>
        <Grid cols={2}>{kids.map((_, i) => <ChildCard key={i} i={i} />)}</Grid>
        <Card title="Cost summary per child" pad={false}>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line">
              <th className="px-5 py-2 font-medium">Age range</th>
              {kids.map(k => <th key={k.name} className="py-2 font-medium text-right pr-5">{k.name}</th>)}</tr></thead>
            <tbody>
              {RANGES.map(([label, a, b]) => (
                <tr key={label} className="border-b border-line">
                  <td className="px-5 py-2">{label}</td>
                  {kids.map(k => {
                    const by = perChild[k.name]?.byAge || {}
                    let s = 0; for (let x = a; x <= b; x++) s += by[x] || 0
                    return <td key={k.name} className="text-right pr-5 tnum">{s ? money(s) : '—'}</td>
                  })}
                </tr>
              ))}
              <tr className="font-semibold"><td className="px-5 py-2.5">Lifetime (remaining)</td>
                {kids.map(k => <td key={k.name} className="text-right pr-5 tnum">{money(perChild[k.name]?.total || 0)}</td>)}</tr>
              <tr className="text-muted"><td className="px-5 pb-3">Peak year</td>
                {kids.map(k => <td key={k.name} className="text-right pr-5 tnum pb-3">{perChild[k.name] ? `${money(perChild[k.name].peak[1])} at ${perChild[k.name].peak[0]}` : '—'}</td>)}</tr>
            </tbody>
          </table>
        </Card>
        <Note>Healthcare categories grow with healthcare inflation; everything else with general inflation. College adds tuition plus room & board for the college location (ages 18–21).</Note>
      </>}
    </div>
  )
}
