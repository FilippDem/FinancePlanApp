import React, { useEffect, useState } from 'react'
import { FileDown, Loader2, Eye, X } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { Button, Toggle, TextInput, Segmented } from './ui'
import { clsx } from '../lib/format'

const FORMATS = [{ value: 'pdf', label: 'PDF' }, { value: 'xlsx', label: 'Excel' }, { value: 'csv', label: 'CSV' }, { value: 'json', label: 'JSON' }] as const
const ALL_DEFAULT = ['summary', 'charts', 'people', 'children', 'spending', 'homes', 'healthcare', 'purchases', 'locations', 'assumptions',
  'monte_carlo', 'year_by_year', 'category_detail', 'checkins']

function save(blob: Blob, filename: string) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 5000)
}

/** Export the plan on screen: choose sections, name, format and dollars; preview PDFs in place. */
export function ReportButton({ size = 'sm' as 'sm' | 'md' }) {
  const { plan, household } = usePlan()
  const [open, setOpen] = useState(false)
  const [sections, setSections] = useState<{ key: string; label: string }[]>([])
  const [sel, setSel] = useState<string[]>(() => { try { return JSON.parse(localStorage.getItem('fp_report_sections') || '') } catch { return ALL_DEFAULT } })
  const [title, setTitle] = useState('')
  const [format, setFormat] = useState<string>('pdf')
  const [today, setToday] = useState(true)
  const [detail, setDetail] = useState(false)
  const [busy, setBusy] = useState<'' | 'download' | 'preview'>('')
  const [err, setErr] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  useEffect(() => { if (open && !sections.length) api.reportSections().then(r => setSections(r.sections)).catch(() => {}) }, [open])
  useEffect(() => { try { localStorage.setItem('fp_report_sections', JSON.stringify(sel)) } catch { /* */ } }, [sel])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const run = async (mode: 'download' | 'preview') => {
    setBusy(mode); setErr('')
    try {
      const r = await api.report({ plan, format: mode === 'preview' ? 'pdf' : format, sections: sel, title: title || undefined, today, detail })
      if (mode === 'preview') { if (preview) URL.revokeObjectURL(preview); setPreview(URL.createObjectURL(r.blob)) }
      else save(r.blob, r.filename)
    } catch (e: any) { setErr(e.message) } finally { setBusy('') }
  }
  const toggle = (k: string) => setSel(s => s.includes(k) ? s.filter(x => x !== k) : [...s, k])

  return (
    <>
      <Button size={size} onClick={() => setOpen(true)}><FileDown size={14} />Report</Button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
          <div className={clsx('relative bg-surface rounded-xl border border-line shadow-2xl w-full flex flex-col max-h-[92vh]', preview ? 'max-w-[1200px] h-[92vh]' : 'max-w-xl')}>
            <header className="flex items-center justify-between px-5 h-14 border-b border-line">
              <h2 className="font-semibold">Export a report</h2>
              <button onClick={() => { setOpen(false); setPreview(null) }} className="p-1.5 rounded-md hover:bg-sunken text-muted"><X size={18} /></button>
            </header>
            <div className={clsx('flex-1 min-h-0', preview ? 'grid grid-cols-[340px_1fr]' : '')}>
              <div className="p-5 space-y-4 overflow-y-auto">
                <label className="block"><span className="block text-[12.5px] font-medium text-ink2 mb-1.5">Report name</span>
                  <TextInput value={title} onChange={setTitle} placeholder={`Financial plan — ${household?.name || ''}`} /></label>
                <div><span className="block text-[12.5px] font-medium text-ink2 mb-1.5">Format</span>
                  <Segmented value={format} onChange={setFormat} options={FORMATS as any} /></div>
                <div className="flex flex-wrap gap-x-5 gap-y-2">
                  <Toggle checked={today} onChange={setToday} label="Today's dollars" hint="Off: future (nominal) dollars" />
                  {format === 'csv' && <Toggle checked={detail} onChange={setDetail} label="Every line item" hint="Off: one row per year with category totals" />}
                </div>
                {(format === 'pdf' || format === 'xlsx') && (
                  <div>
                    <div className="flex items-baseline justify-between mb-1.5"><span className="text-[12.5px] font-medium text-ink2">Include</span>
                      <span className="text-[12px] space-x-2"><button className="text-accent" onClick={() => setSel(sections.map(x => x.key))}>All</button>
                        <button className="text-accent" onClick={() => setSel(['summary', 'charts'])}>Summary only</button></span></div>
                    <div className="grid gap-1">
                      {sections.map(x => (
                        <label key={x.key} className="flex items-center gap-2 text-sm cursor-pointer">
                          <input type="checkbox" className="w-4 h-4 accent-[rgb(var(--accent))]" checked={sel.includes(x.key)} onChange={() => toggle(x.key)} />{x.label}
                        </label>))}
                    </div>
                  </div>)}
                {err && <p className="text-sm text-bad">{err}</p>}
                <p className="text-[12px] text-muted">Uses the plan on screen, including unsaved what-ifs.</p>
                <div className="flex gap-2 pt-1">
                  <Button onClick={() => run('preview')} disabled={!!busy}>{busy === 'preview' ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}Preview PDF</Button>
                  <Button variant="primary" onClick={() => run('download')} disabled={!!busy}>{busy === 'download' ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}Download</Button>
                </div>
              </div>
              {preview && <iframe title="Report preview" src={preview} className="w-full h-full border-l border-line bg-sunken" />}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
