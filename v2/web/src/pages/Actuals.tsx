import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, Upload, Save, ChevronDown, ChevronRight, CheckCircle2, AlertCircle, FileSpreadsheet } from 'lucide-react'
import { ResponsiveContainer, ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, axisMoney, clsx } from '../lib/format'
import { Card, PageHeader, Button, Money, Select, Stat, Note, Empty } from '../components/ui'
import { S } from '../components/charts'

const INCOME: [string, string][] = [['parent1_employment', 'Employment (%1)'], ['parent2_employment', 'Employment (%2)'],
  ['ss_income', 'Social Security'], ['investment_income', 'Investment income'], ['other_income', 'Rental & other']]
const HEALTH_LABELS: Record<string, string> = { insurance_premiums: 'Insurance premiums', medicare: 'Medicare', ltc_premiums: 'Long-term care', out_of_pocket: 'Out of pocket' }
const HOUSE_LABELS: Record<string, string> = { mortgage: 'Mortgage (P&I + PMI)', property_tax: 'Property tax', home_insurance: 'Insurance & HOA', maintenance: 'Maintenance', upkeep: 'Upkeep' }

type Row = { path: string[]; label: string; planned: number }
type Group = { key: string; title: string; rows: Row[] }

const num = (v: any) => (typeof v === 'number' && isFinite(v) ? v : null)
function getIn(o: any, path: string[]) { return path.reduce((a, k) => (a == null ? undefined : a[k]), o) }
function setIn(o: any, path: string[], v: any) {
  let cur = o
  path.slice(0, -1).forEach(k => { if (typeof cur[k] !== 'object' || cur[k] === null) cur[k] = {}; cur = cur[k] })
  cur[path[path.length - 1]] = v
}

function buildGroups(planned: any, actual: any, names: [string, string], single: boolean): Group[] {
  const e = planned?.expenses || {}
  const a = actual?.expenses || {}
  const flat = (key: string, title: string, labels?: Record<string, string>) => {
    const cats = new Set([...Object.keys(e[key] || {}), ...Object.keys(a[key] || {})])
    return { key, title, rows: [...cats].map(c => ({ path: ['expenses', key, c], label: labels?.[c] ?? c, planned: num(e[key]?.[c]) ?? 0 })) }
  }
  const gs: Group[] = [flat('parentX', `${names[0]} — personal`)]
  if (!single) gs.push(flat('parentY', `${names[1]} — personal`))
  gs.push(flat('family', 'Household'))
  const kids = new Set([...Object.keys(e.children || {}), ...Object.keys(a.children || {})])
  if (kids.size) gs.push({ key: 'children', title: 'Children', rows: [...kids].map(k => ({ path: ['expenses', 'children', k, 'Total'], label: k, planned: num(e.children?.[k]?.Total) ?? 0 })) })
  const houses = new Set([...Object.keys(e.housing || {}), ...Object.keys(a.housing || {})])
  houses.forEach(h => {
    const cats = new Set([...Object.keys(e.housing?.[h] || {}), ...Object.keys(a.housing?.[h] || {})])
    gs.push({ key: `housing:${h}`, title: `Home — ${h}`, rows: [...cats].map(c => ({ path: ['expenses', 'housing', h, c], label: HOUSE_LABELS[c] ?? c, planned: num(e.housing?.[h]?.[c]) ?? 0 })) })
  })
  gs.push(flat('healthcare', 'Healthcare', HEALTH_LABELS))
  const rec = flat('recurring', 'Recurring (cars, travel …)')
  if (rec.rows.length) gs.push(rec)
  const mp = flat('major_purchases', 'One-time purchases')
  if (mp.rows.length) gs.push(mp)
  return gs.filter(g => g.rows.length)
}

function Variance({ planned, actual, spend = true }: { planned: number; actual: number | null; spend?: boolean }) {
  if (actual === null) return <span className="text-muted">—</span>
  const d = actual - planned
  const bad = spend ? d > Math.max(50, planned * 0.05) : d < -Math.max(50, planned * 0.05)
  const good = spend ? d < -Math.max(50, planned * 0.05) : d > Math.max(50, planned * 0.05)
  return <span className={clsx('tnum', bad && 'text-bad', good && 'text-good', !bad && !good && 'text-ink2')}>{money(d, { sign: true })}</span>
}

export default function Actuals() {
  const { plan, proj, names, single } = usePlan()
  const nav = useNavigate()
  const cy = plan.current_year as number
  const [all, setAll] = useState<Record<string, any>>({})
  const [year, setYear] = useState<number>(new Date().getFullYear())
  const [draft, setDraft] = useState<any>({})
  const [dirty, setDirty] = useState(false)
  const [planned, setPlanned] = useState<any>(null)
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [msg, setMsg] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null)
  const [xlYears, setXlYears] = useState(1)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = async () => { const r = await api.getActuals(); setAll(r.actuals || {}); return r.actuals || {} }
  useEffect(() => { load() }, [])
  useEffect(() => { setDraft(structuredClone(all[String(year)] || {})); setDirty(false) }, [year, all])
  useEffect(() => { let live = true; api.planned(plan, year).then(r => live && setPlanned(r)).catch(() => {}); return () => { live = false } }, [plan, year])
  const flash = (tone: 'good' | 'bad', text: string) => { setMsg({ tone, text }); setTimeout(() => setMsg(null), 3500) }

  const years = useMemo(() => {
    const ys = new Set<number>([...Object.keys(all).map(Number).filter(n => !isNaN(n))])
    for (let y = Math.min(cy, new Date().getFullYear()) - 3; y <= Math.max(cy, new Date().getFullYear()) + 1; y++) ys.add(y)
    return [...ys].sort((a, b) => b - a)
  }, [all, cy])

  const groups = useMemo(() => buildGroups(planned, draft, names, single), [planned, draft, names, single])
  const set = (path: string[], v: number | null) => { setDraft((d: any) => { const n = structuredClone(d); setIn(n, path, v); return n }); setDirty(true) }

  const groupSum = (g: Group, which: 'planned' | 'actual') => g.rows.reduce((s, r) => s + (which === 'planned' ? r.planned : (num(getIn(draft, r.path)) ?? 0)), 0)
  const hasDetail = groups.some(g => g.rows.some(r => num(getIn(draft, r.path)) !== null))
  const spendingActual = hasDetail ? groups.reduce((s, g) => s + groupSum(g, 'actual'), 0) : num(draft.total_spending)
  const incomeDetail = INCOME.some(([k]) => num(draft.income?.[k]) !== null)
  const incomeActual = incomeDetail ? INCOME.reduce((s, [k]) => s + (num(draft.income?.[k]) ?? 0), 0) : num(draft.income?.total)
  const t = planned?.totals || {}

  const save = async () => {
    const body = structuredClone(draft)
    if (hasDetail) body.total_spending = spendingActual
    if (incomeDetail) body.income = { ...(body.income || {}), total: incomeActual }
    await api.putActualYear(year, body)
    await load()
    flash('good', `Saved ${year}`)
  }

  const importXl = async (f: File) => {
    try {
      const r = await api.importWorkbook(f)
      setAll(r.actuals || {})
      flash('good', r.years.length ? `Imported ${r.years.join(', ')}` : 'No filled-in values found in that workbook')
    } catch (e: any) { flash('bad', e.message) }
  }

  // plan vs actual net worth over years
  const nwData = useMemo(() => {
    const rows = proj?.rows || []
    const byYear: Record<number, any> = {}
    rows.forEach((r: any) => { byYear[r.year] = { year: r.year, plan: r.net_worth } })
    Object.entries(all).forEach(([y, v]: any) => { const n = num(v?.net_worth); if (n !== null) byYear[+y] = { ...(byYear[+y] || { year: +y }), actual: n } })
    const ys = Object.keys(all).map(Number).filter(n => !isNaN(n))
    const lo = Math.min(cy, ...ys), hi = Math.max(cy + 10, ...ys)
    return Object.values(byYear).filter((d: any) => d.year >= lo && d.year <= hi).sort((a: any, b: any) => a.year - b.year)
  }, [proj, all, cy])
  const history = Object.entries(all).filter(([y]) => !isNaN(+y)).sort(([a], [b]) => +b - +a)

  return (
    <div className="space-y-5">
      <PageHeader title="Actuals" subtitle="Record what really happened each year and compare it with the plan"
        actions={<>
          <div className="w-28"><Select value={year} options={years} onChange={setYear} /></div>
          <Button variant="primary" onClick={save} disabled={!dirty}><Save size={15} />{dirty ? 'Save year' : 'Saved'}</Button>
        </>} />
      {msg && <div className={clsx('flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm', msg.tone === 'good' ? 'bg-good/10 text-good' : 'bg-bad/10 text-bad')}>
        {msg.tone === 'good' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}{msg.text}</div>}
      {planned && !planned.in_projection && <Note tone="warn">{year} is before the plan's start year ({cy}), so there are no planned numbers to compare with. You can still record actuals.</Note>}

      <div className="grid gap-4 md:grid-cols-4">
        <Card><Stat label={`Net worth, end of ${year}`} value={money(num(draft.net_worth))} sub={t.net_worth != null ? `Plan ${money(t.net_worth)}` : 'Enter below'} /></Card>
        <Card><Stat label="Income" value={money(incomeActual)} sub={<>Plan {money(t.income)} · <Variance planned={t.income ?? 0} actual={incomeActual} spend={false} /></>} /></Card>
        <Card><Stat label="Spending" value={money(spendingActual)} sub={<>Plan {money(t.spending)} · <Variance planned={t.spending ?? 0} actual={spendingActual} /></>} /></Card>
        <Card><Stat label="Taxes paid" value={money(num(draft.taxes_paid))} sub={`Plan ${money(t.taxes)}`} /></Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
        <div className="space-y-4">
          <Card title="Year-end totals" subtitle="Nominal dollars for that year">
            <div className="space-y-3">
              <Row label="Net worth (incl. home equity)" planned={t.net_worth} value={num(draft.net_worth)} onChange={v => set(['net_worth'], v)} spend={false} />
              <Row label="Taxes paid" planned={t.taxes} value={num(draft.taxes_paid)} onChange={v => set(['taxes_paid'], v)} />
              {!hasDetail && <Row label="Total spending (if you don't track categories)" planned={t.spending} value={num(draft.total_spending)} onChange={v => set(['total_spending'], v)} />}
              {!incomeDetail && <Row label="Total income (if you don't split it)" planned={t.income} value={num(draft.income?.total)} onChange={v => set(['income', 'total'], v)} spend={false} />}
            </div>
          </Card>
          <Card title="Income">
            <div className="space-y-3">
              {INCOME.filter(([k]) => !(single && k === 'parent2_employment')).map(([k, l]) => (
                <Row key={k} label={l.replace('%1', names[0]).replace('%2', names[1])} planned={planned?.income?.[k]} value={num(draft.income?.[k])}
                  onChange={v => set(['income', k], v)} spend={false} />
              ))}
            </div>
          </Card>
          <Card title="Notes">
            <textarea className="w-full min-h-[90px] rounded-lg border border-line bg-surface p-3 text-sm outline-none focus:border-accent"
              placeholder="Anything unusual this year: a bonus, a big repair, a new job…" value={draft.notes || ''}
              onChange={e => { setDraft({ ...draft, notes: e.target.value }); setDirty(true) }} />
            {draft.entered_by && <p className="text-[12px] text-muted mt-2">Last updated by {String(draft.entered_by).split('@')[0]}{draft.entered_at ? ` · ${new Date(draft.entered_at).toLocaleDateString()}` : ''}</p>}
          </Card>
        </div>

        <Card title="Spending by category" subtitle="Annual amounts. Leave blank what you don't track; group totals count only what you fill in." pad={false}>
          <div className="divide-y divide-line">
            {groups.map(g => {
              const isOpen = open[g.key] ?? false
              const pa = groupSum(g, 'planned')
              const filled = g.rows.some(r => num(getIn(draft, r.path)) !== null)
              const aa = groupSum(g, 'actual')
              return (
                <div key={g.key}>
                  <button className="w-full flex items-center gap-2 px-5 py-3 text-left hover:bg-sunken/60" onClick={() => setOpen({ ...open, [g.key]: !isOpen })}>
                    {isOpen ? <ChevronDown size={16} className="text-muted" /> : <ChevronRight size={16} className="text-muted" />}
                    <span className="font-medium flex-1">{g.title}</span>
                    <span className="text-[12.5px] text-muted tnum w-24 text-right">plan {money(pa)}</span>
                    <span className="text-sm font-medium tnum w-24 text-right">{filled ? money(aa) : '—'}</span>
                    <span className="text-[12.5px] w-20 text-right">{filled ? <Variance planned={pa} actual={aa} /> : ''}</span>
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-4 space-y-2">
                      {g.rows.map(r => (
                        <div key={r.path.join('/')} className="grid grid-cols-[1fr_90px_140px_80px] items-center gap-3 text-sm">
                          <span className="text-ink2 truncate">{r.label}</span>
                          <span className="text-right text-muted tnum">{money(r.planned)}</span>
                          <Money value={num(getIn(draft, r.path))} placeholder="—" onChange={v => set(r.path, v)} />
                          <span className="text-right text-[12.5px]"><Variance planned={r.planned} actual={num(getIn(draft, r.path))} /></span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Net worth: plan vs actual" subtitle="Line is the plan (nominal $); dots are the year-end net worth you recorded">
          {nwData.some((d: any) => d.actual != null) ? (
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={nwData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--grid)" />
                <XAxis dataKey="year" tickLine={false} axisLine={false} fontSize={11} stroke="var(--axis)" />
                <YAxis tickLine={false} axisLine={false} tickFormatter={axisMoney} width={56} fontSize={11} stroke="var(--axis)" />
                <Tooltip formatter={(v: any, n: any) => [money(v), n]} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
                <Line dataKey="plan" name="Plan" stroke={S[1]} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
                <Scatter dataKey="actual" name="Actual" fill={S[0]} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <Empty title="No year-end net worth yet" body="Enter it above, import a workbook, or do a check-in in Oct–Dec (it's recorded automatically)." />}
        </Card>
        <Card title="Excel tracking workbook" subtitle="Fill in month by month in Excel or Google Sheets, then import it here">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-ink2">Years</span>
            <div className="w-40"><Select value={xlYears} options={[{ value: 1, label: `${year} only` }, { value: 3, label: `${year}–${year + 2}` }, { value: 5, label: `${year}–${year + 4}` }]} onChange={setXlYears} /></div>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            <a className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-line text-sm font-medium hover:bg-sunken"
              href={`/api/actuals/workbook.xlsx?start=${year}&end=${year + xlYears - 1}`}><Download size={15} />Download workbook</a>
            <Button onClick={() => fileRef.current?.click()}><Upload size={15} />Import filled workbook</Button>
            <input ref={fileRef} type="file" accept=".xlsx" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) importXl(f); e.target.value = '' }} />
          </div>
          <p className="text-[12.5px] text-muted mt-3 flex gap-1.5"><FileSpreadsheet size={14} className="shrink-0 mt-0.5" />Importing merges into what's here; nothing you've entered is erased.</p>
          {history.length > 0 && (
            <div className="mt-4 border-t border-line pt-3">
              <div className="text-[12.5px] font-medium text-ink2 mb-1.5">Years with actuals</div>
              <div className="flex flex-wrap gap-1.5">{history.map(([y, v]: any) => (
                <button key={y} onClick={() => setYear(+y)} className={clsx('px-2 h-7 rounded-md text-[12.5px] border', +y === year ? 'border-accent text-accent bg-accentSoft' : 'border-line hover:bg-sunken')}>
                  {y}{v?.net_worth != null && <span className="text-muted ml-1">{money(v.net_worth)}</span>}</button>))}</div>
            </div>
          )}
        </Card>
      </div>
      <Note>Tip: quarterly check-ins keep your balances current; Actuals is for the fuller yearly picture (income and where the money went). <button className="underline" onClick={() => nav('/checkins')}>Go to check-ins</button></Note>
    </div>
  )
}

function Row({ label, planned, value, onChange, spend = true }: { label: string; planned?: number | null; value: number | null; onChange: (v: number | null) => void; spend?: boolean }) {
  return (
    <div className="grid grid-cols-[1fr_140px] items-center gap-3">
      <div className="min-w-0">
        <div className="text-sm text-ink2">{label}</div>
        <div className="text-[12px] text-muted">Plan {money(planned)}{value !== null && planned != null && <> · <Variance planned={planned} actual={value} spend={spend} /></>}</div>
      </div>
      <Money value={value} placeholder="—" onChange={onChange} />
    </div>
  )
}

