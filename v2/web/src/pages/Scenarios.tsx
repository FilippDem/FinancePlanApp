import React, { useEffect, useRef, useState } from 'react'
import { Save, Upload, Download, Trash2, Pencil, FolderOpen, Sparkles, GitCompare, RotateCcw } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct } from '../lib/format'
import { Card, PageHeader, Button, TextInput, Modal, Badge, Empty, Note } from '../components/ui'
import { LinesChart } from '../components/charts'

export default function Scenarios() {
  const { plan, replacePlan, household } = usePlan()
  const [saved, setSaved] = useState<Record<string, any>>({})
  const [demos, setDemos] = useState<Record<string, any>>({})
  const [name, setName] = useState('')
  const [confirm, setConfirm] = useState<{ title: string; body: string; run: () => Promise<void> | void } | null>(null)
  const [rename, setRename] = useState<{ from: string; to: string } | null>(null)
  const [sel, setSel] = useState<string[]>([])
  const [cmp, setCmp] = useState<any[] | null>(null)
  const [msg, setMsg] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const load = () => api.scenarios().then(r => setSaved(r.scenarios))
  useEffect(() => { load(); api.demos().then(r => setDemos(r.demos)) }, [])
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 2500) }

  const saveAs = async () => {
    const n = name.trim() || `Snapshot ${new Date().toLocaleDateString()}`
    await api.saveScenario(n, plan); setName(''); load(); flash(`Saved “${n}”`)
  }
  const exportJson = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' }))
    a.download = `financial_plan_${new Date().toISOString().slice(0, 10)}.json`; a.click()
  }
  const importJson = async (f: File) => {
    try {
      const data = JSON.parse(await f.text())
      const p = data.plan_data ?? data
      setConfirm({ title: 'Replace current plan?', body: `Load “${f.name}” into ${household?.name}. Save the current plan as a scenario first if you want to keep it.`, run: () => replacePlan(p) })
    } catch { flash('That file is not valid JSON') }
  }

  const compare = async () => {
    const items = [{ name: 'Current plan', plan }, ...sel.map(n => ({ name: n, plan: saved[n] ?? demos[n] }))]
    const res = await Promise.all(items.map(async it => {
      const [p, m] = await Promise.all([api.project(it.plan), api.monteCarlo(it.plan, 400)])
      return { name: it.name, proj: p, mc: m }
    }))
    setCmp(res)
  }

  const cmpData = cmp ? (() => {
    const years = new Set<number>(); cmp.forEach(c => c.proj.rows.forEach((r: any) => years.add(r.year)))
    return [...years].sort().map(y => {
      const o: any = { year: y }
      cmp.forEach((c, i) => { const r = c.proj.rows.find((x: any) => x.year === y); if (r) o[`s${i}`] = r.net_worth / r.infl_index })
      return o
    })
  })() : []

  const toggle = (n: string) => setSel(s => s.includes(n) ? s.filter(x => x !== n) : s.length < 4 ? [...s, n] : s)

  const ScenarioRow = ({ n, p, demo }: { n: string; p: any; demo?: boolean }) => (
    <li className="flex items-center gap-3 px-5 py-3">
      <input type="checkbox" className="accent-[rgb(var(--accent))] w-4 h-4" checked={sel.includes(n)} onChange={() => toggle(n)} title="Compare" />
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{n.replace('[DEMO] ', '')}</div>
        <div className="text-xs text-muted truncate">{p.parent1_name}{p.parent2_name && p.parent2_name !== 'N/A' ? ` & ${p.parent2_name}` : ''} · {(p.children_list || []).length} kids · {(p.houses || []).length} homes</div>
      </div>
      {demo && <Badge tone="accent">demo</Badge>}
      <Button size="sm" onClick={() => setConfirm({ title: `Load “${n.replace('[DEMO] ', '')}”?`, body: 'This replaces the current plan (it is auto-saved). Save the current plan as a scenario first if you want to keep it.', run: () => replacePlan(p) })}><FolderOpen size={13} />Load</Button>
      {!demo && <>
        <button className="p-1.5 rounded-md text-muted hover:bg-sunken" title="Rename" onClick={() => setRename({ from: n, to: n })}><Pencil size={14} /></button>
        <button className="p-1.5 rounded-md text-muted hover:text-bad hover:bg-bad/10" title="Delete" onClick={() => setConfirm({ title: `Delete “${n}”?`, body: 'This cannot be undone.', run: async () => { await api.deleteScenario(n); load() } })}><Trash2 size={14} /></button>
      </>}
    </li>
  )

  return (
    <div className="space-y-5">
      <PageHeader title="Scenarios" subtitle="Save what-ifs, compare them side by side, import and export" />
      {msg && <Note>{msg}</Note>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Save current plan" className="lg:col-span-2">
          <div className="flex gap-2">
            <TextInput value={name} onChange={setName} placeholder="Scenario name, e.g. Retire at 55" />
            <Button variant="primary" onClick={saveAs}><Save size={14} />Save</Button>
          </div>
          <p className="text-xs text-muted mt-2">Scenarios are stored in the household file on the server, shared with everyone in {household?.name}.</p>
        </Card>
        <Card title="File">
          <div className="flex flex-wrap gap-2">
            <Button onClick={exportJson}><Download size={14} />Export JSON</Button>
            <Button onClick={() => fileRef.current?.click()}><Upload size={14} />Import</Button>
            <Button variant="ghost" onClick={() => setConfirm({ title: 'Start over with defaults?', body: 'Resets the current plan to the default example. Saved scenarios are kept.', run: () => replacePlan({}) })}><RotateCcw size={14} />Reset</Button>
            <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={e => e.target.files?.[0] && importJson(e.target.files[0])} />
          </div>
          <p className="text-xs text-muted mt-2">Imports files from v0.8, V14 and V13.</p>
        </Card>
      </div>

      <Card title="Saved scenarios" pad={false} action={sel.length > 0 && <Button size="sm" variant="primary" onClick={compare}><GitCompare size={14} />Compare {sel.length + 1}</Button>}>
        {Object.keys(saved).filter(n => !n.startsWith('[DEMO]')).length === 0
          ? <Empty title="No saved scenarios yet" body="Save the current plan to keep a snapshot before trying a what-if." />
          : <ul className="divide-y divide-line">{Object.entries(saved).filter(([n]) => !n.startsWith('[DEMO]')).map(([n, p]) => <ScenarioRow key={n} n={n} p={p} />)}</ul>}
      </Card>

      {cmp && (
        <Card title="Comparison" subtitle="Net worth in today's dollars" action={<Button size="sm" variant="ghost" onClick={() => setCmp(null)}>Close</Button>}>
          <LinesChart data={cmpData} series={cmp.map((c, i) => ({ key: `s${i}`, label: c.name.replace('[DEMO] ', '') }))} height={320} />
          <table className="w-full text-sm mt-4">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-2 font-medium">Scenario</th>
              <th className="text-right font-medium">At retirement</th><th className="text-right font-medium">At end</th><th className="text-right font-medium">Savings run out</th><th className="text-right font-medium">Success</th></tr></thead>
            <tbody>{cmp.map(c => {
              const s = c.proj.summary
              const rr = c.proj.rows.find((r: any) => r.year === s.retirement_year)
              const last = c.proj.rows[c.proj.rows.length - 1]
              return <tr key={c.name} className="border-b border-line last:border-0">
                <td className="py-2 font-medium">{c.name.replace('[DEMO] ', '')}</td>
                <td className="text-right tnum">{rr ? money(rr.net_worth / rr.infl_index) : '—'}</td>
                <td className="text-right tnum">{money(last.net_worth / last.infl_index)}</td>
                <td className="text-right tnum">{s.depletion_year ?? 'Never'}</td>
                <td className="text-right tnum">{pct(c.mc.success_rate, 0)}</td></tr>
            })}</tbody>
          </table>
        </Card>
      )}

      <Card title={<span className="flex items-center gap-2"><Sparkles size={16} className="text-accent" />Demo households</span>} subtitle="Example plans to explore features" pad={false}>
        <ul className="divide-y divide-line">{Object.entries(demos).map(([n, p]) => <ScenarioRow key={n} n={n} p={p} demo />)}</ul>
      </Card>

      <Modal open={!!confirm} onClose={() => setConfirm(null)} title={confirm?.title || ''}
        footer={<><Button onClick={() => setConfirm(null)}>Cancel</Button><Button variant="primary" onClick={async () => { await confirm?.run(); setConfirm(null); flash('Done') }}>Continue</Button></>}>
        <p className="text-sm text-ink2">{confirm?.body}</p>
      </Modal>
      <Modal open={!!rename} onClose={() => setRename(null)} title="Rename scenario"
        footer={<><Button onClick={() => setRename(null)}>Cancel</Button><Button variant="primary" onClick={async () => { await api.renameScenario(rename!.from, rename!.to); setRename(null); load() }}>Rename</Button></>}>
        <TextInput value={rename?.to || ''} onChange={v => setRename(r => r && { ...r, to: v })} />
      </Modal>
    </div>
  )
}
