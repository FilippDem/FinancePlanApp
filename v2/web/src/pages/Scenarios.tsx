import React, { useEffect, useRef, useState } from 'react'
import { Save, Upload, Download, Trash2, Pencil, FolderOpen, Sparkles, GitCompare, RotateCcw, History, Eye } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct } from '../lib/format'
import { Card, PageHeader, Button, TextInput, Modal, Badge, Empty, Note } from '../components/ui'
import { LinesChart } from '../components/charts'
import { ReportButton } from '../components/ReportButton'

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
  const [versions, setVersions] = useState<any[]>([])
  const [showAll, setShowAll] = useState(false)
  const [preview, setPreview] = useState<{ v: any; plan: any; proj: any } | null>(null)
  const loadVersions = () => api.history().then(r => setVersions(r.versions)).catch(() => {})
  useEffect(() => { load(); loadVersions(); api.demos().then(r => setDemos(r.demos)) }, [])
  const openPreview = async (v: any) => {
    try {
      const { plan: vp } = await api.previewVersion(v.id)
      const pr = await api.project(vp)
      setPreview({ v, plan: vp, proj: pr })
    } catch (e: any) { flash(e.message) }
  }
  const restore = async (v: any) => {
    const r = await api.restoreVersion(v.id)
    await replacePlan(r.plan)
    setPreview(null); loadVersions(); flash('Restored. Your previous version is in the history too.')
  }
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

  const compare = async (extra?: { name: string; plan: any }[]) => {
    const items = extra ?? [{ name: 'Current plan', plan }, ...sel.map(n => ({ name: n, plan: saved[n] ?? demos[n] }))]
    const res = await Promise.all(items.map(async it => {
      const [p, m] = await Promise.all([api.project(it.plan), api.monteCarlo(it.plan, 400)])
      return { name: it.name, proj: p, mc: m, plan: p.plan ?? it.plan }
    }))
    setCmp(res)
  }

  // v0.8 one-click what-ifs: saves the current plan once as "Current Plan (before what-if)", then a changed copy as its own scenario
  const WHATIFS: { key: string; label: string; name: string; apply: (d: any) => void }[] = [
    { key: 'early', label: 'Retire 2 years earlier', name: 'Early Retirement (-2yr)', apply: d => { d.parentX_retirement_age -= 2; d.parentY_retirement_age -= 2 } },
    { key: 'late', label: 'Retire 2 years later', name: 'Late Retirement (+2yr)', apply: d => { d.parentX_retirement_age += 2; d.parentY_retirement_age += 2 } },
    { key: 'child', label: 'Add one more child', name: 'One More Child', apply: d => {
      const n = (d.children_list || []).length + 1
      const loc = d.state_timeline?.[0]?.state || 'Seattle'
      d.children_list = [...(d.children_list || []), { name: `Child ${n}`, birth_year: d.current_year + 1, use_template: true, template_state: loc,
        template_strategy: 'Average', school_type: 'Public', college_type: 'Public', college_location: loc }]
    } },
    { key: 'bull', label: 'Strong returns (8%)', name: 'Aggressive Returns', apply: d => { d.economic_params.investment_return = 0.08 } },
    { key: 'bear', label: 'Weak returns (4%)', name: 'Bear Market Returns', apply: d => { d.economic_params.investment_return = 0.04 } },
    { key: 'save', label: 'Save $500/mo more', name: 'Extra Savings (+$6k/yr)', apply: d => { d.pretax_401k = (d.pretax_401k || 0) + 6000 } },
  ]
  const runWhatIf = async (w: typeof WHATIFS[number]) => {
    const base = 'Current Plan (before what-if)'
    if (!saved[base]) await api.saveScenario(base, plan)
    const copy = structuredClone(plan)
    w.apply(copy)
    await api.saveScenario(w.name, copy)
    await load()
    flash(`Created “${w.name}”`)
    compare([{ name: 'Current plan', plan }, { name: w.name, plan: copy }])
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
        {demo && p.demo_note && <div className="text-xs text-ink2 mt-0.5 line-clamp-2" title={p.demo_note}>{p.demo_note}</div>}
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
            <ReportButton size="md" />
            <Button variant="ghost" onClick={() => setConfirm({ title: 'Start over with defaults?', body: 'Resets the current plan to the default example. Saved scenarios are kept.', run: () => replacePlan({}) })}><RotateCcw size={14} />Reset</Button>
            <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={e => e.target.files?.[0] && importJson(e.target.files[0])} />
          </div>
          <p className="text-xs text-muted mt-2">Imports files from v0.8, V14 and V13.</p>
        </Card>
      </div>

      <Card title="Quick what-ifs" subtitle="One click saves a changed copy of your plan as a scenario and compares it with the current plan. Your plan itself is not changed.">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {WHATIFS.map(w => <Button key={w.key} onClick={() => runWhatIf(w)}><Sparkles size={14} />{w.label}</Button>)}
        </div>
      </Card>

      <Card title="Saved scenarios" pad={false} action={sel.length > 0 && <Button size="sm" variant="primary" onClick={() => compare()}><GitCompare size={14} />Compare {sel.length + 1}</Button>}>
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
          <PlanInputsTable items={cmp} />
        </Card>
      )}

      <Card title={<span className="flex items-center gap-2"><History size={16} className="text-accent" />Version history</span>}
        subtitle="The server keeps the last 10 saves plus one snapshot per day (120 days). Restoring changes only the plan; check-ins, actuals and scenarios stay."
        pad={false} action={versions.length > 8 && <Button size="sm" variant="ghost" onClick={() => setShowAll(!showAll)}>{showAll ? 'Show fewer' : `Show all ${versions.length}`}</Button>}>
        {versions.length === 0 ? <Empty title="No history yet" body="Versions appear after the plan is saved a few times." /> : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="px-5 py-2 font-medium">Saved</th><th className="font-medium">By</th>
              <th className="font-medium text-right">Savings</th><th className="font-medium text-right">Homes</th><th className="font-medium text-right">Kids</th><th className="font-medium text-right">Retire at</th><th className="w-44" /></tr></thead>
            <tbody>{(showAll ? versions : versions.slice(0, 8)).map(v => (
              <tr key={v.id} className="border-b border-line last:border-0">
                <td className="px-5 py-2 tnum">{new Date(v.last_saved || v.file_time).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                  {v.kind === 'daily' && <span className="ml-1.5"><Badge>daily</Badge></span>}</td>
                <td className="text-[12.5px] text-muted truncate max-w-[160px]">{String(v.saved_by || '').split('@')[0]}{String(v.saved_by || '').includes('restored') ? ' (restore)' : ''}</td>
                <td className="text-right tnum">{v.summary ? money(v.summary.savings) : v.encrypted ? 'encrypted' : '—'}</td>
                <td className="text-right tnum">{v.summary?.homes ?? '—'}</td>
                <td className="text-right tnum">{v.summary?.kids ?? '—'}</td>
                <td className="text-right tnum">{v.summary ? v.summary.retire.filter((x: any) => x != null).join(' / ') : '—'}</td>
                <td className="text-right pr-4 whitespace-nowrap"><Button size="sm" variant="ghost" onClick={() => openPreview(v)}><Eye size={13} />Preview</Button>
                  <Button size="sm" onClick={() => setConfirm({ title: 'Restore this version?', body: 'The current plan is backed up first, so you can undo this from the history.', run: () => restore(v) })}><RotateCcw size={13} />Restore</Button></td>
              </tr>))}</tbody>
          </table>)}
      </Card>

      <Modal open={!!preview} onClose={() => setPreview(null)} title={preview ? `Version from ${new Date(preview.v.last_saved || preview.v.file_time).toLocaleString()}` : ''}
        footer={<><Button onClick={() => setPreview(null)}>Close</Button><Button variant="primary" onClick={() => preview && restore(preview.v)}><RotateCcw size={14} />Restore</Button></>}>
        {preview && (() => {
          const a = preview.proj.summary
          const lastA = preview.proj.rows[preview.proj.rows.length - 1]
          return <div className="text-sm space-y-1.5">
            <div className="flex justify-between"><span className="text-muted">People</span><span>{preview.plan.parent1_name}{preview.plan.parent2_name && preview.plan.parent2_name !== 'N/A' ? ` & ${preview.plan.parent2_name}` : ''}</span></div>
            <div className="flex justify-between"><span className="text-muted">Net worth today</span><span className="tnum">{money(a.net_worth_now)}</span></div>
            <div className="flex justify-between"><span className="text-muted">Retirement year</span><span className="tnum">{a.retirement_year}</span></div>
            <div className="flex justify-between"><span className="text-muted">Savings run out</span><span className="tnum">{a.depletion_year ?? 'Never'}</span></div>
            <div className="flex justify-between"><span className="text-muted">Net worth at end (today's $)</span><span className="tnum">{money(lastA.net_worth / lastA.infl_index)}</span></div>
            <div className="flex justify-between"><span className="text-muted">Homes · kids · recurring</span><span>{(preview.plan.houses || []).length} · {(preview.plan.children_list || []).length} · {(preview.plan.recurring_expenses || []).length}</span></div>
          </div>
        })()}
      </Modal>

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


function PlanInputsTable({ items }: { items: any[] }) {
  const attrs: [string, (p: any) => any, boolean][] = [
    ['People', p => `${p.parent1_name}${p.parent2_name && p.parent2_name !== 'N/A' ? ` & ${p.parent2_name}` : ''}`, false],
    ['Ages', p => `${p.parentX_age}${p.parent2_name && p.parent2_name !== 'N/A' ? ` / ${p.parentY_age}` : ''}`, false],
    ['Children', p => (p.children_list || []).length, true],
    ['Combined income', p => (p.parentX_income || 0) + (p.parentY_income || 0), true],
    ['Combined savings', p => (p.parentX_net_worth || 0) + (p.parentY_net_worth || 0), true],
    ['Earliest retirement age', p => Math.min(p.parentX_retirement_age, p.parent2_name && p.parent2_name !== 'N/A' ? p.parentY_retirement_age : 999), true],
    ['Properties', p => (p.houses || []).length, true],
    ['Investment return', p => `${((p.economic_params?.investment_return || 0) * 100).toFixed(1)}%`, false],
    ['401(k) per year', p => p.pretax_401k || 0, true],
    ['Starting location', p => p.state_timeline?.[0]?.state || '—', false],
    ['Locations over time', p => (p.state_timeline || []).length, true],
  ]
  const fmt = (label: string, v: any) => typeof v === 'number' && /income|savings|401/.test(label) ? money(v) : String(v)
  return (
    <div className="mt-6 overflow-x-auto">
      <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-1">Plan inputs</div>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium" />{items.map(c => <th key={c.name} className="font-medium text-right">{c.name.replace('[DEMO] ', '')}</th>)}</tr></thead>
        <tbody>{attrs.map(([label, get, numeric]) => {
          const base = get(items[0].plan)
          return (
            <tr key={label} className="border-b border-line last:border-0"><td className="py-1.5 text-ink2">{label}</td>
              {items.map((c, i) => {
                const v = get(c.plan)
                const diff = i > 0 && numeric && typeof v === 'number' && typeof base === 'number' && v !== base
                const changed = i > 0 && !numeric && v !== base
                return <td key={c.name} className={`text-right tnum ${changed ? 'text-accent font-medium' : ''}`}>{fmt(label, v)}
                  {diff && <span className={`ml-1.5 text-[12px] ${v > base ? 'text-good' : 'text-bad'}`}>{v > base ? '+' : '−'}{fmt(label, Math.abs(v - base))}</span>}</td>
              })}
            </tr>)
        })}</tbody>
      </table>
    </div>
  )
}
