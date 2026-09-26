import React, { useEffect, useMemo, useState } from 'react'
import { Plus, Trash2, MapPin, Plane, AlertTriangle, Save, Pencil, Database, Building2 } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, clsx } from '../lib/format'
import { Card, PageHeader, Button, NumberInput, Money, Select, TextInput, Toggle, Badge, Note, Field, Modal, Empty } from '../components/ui'
import { S } from '../components/charts'
import { WorldMap, MapStop } from '../components/WorldMap'

const LIFESTYLES = ['Conservative', 'Average', 'High-end']

/** Country → State/Province → City picker (v0.8 location_picker), plus the user's own places. */
export function LocationPicker({ value, onChange, catalog, custom, compact }:
  { value: string; onChange: (v: string) => void; catalog: any; custom?: Record<string, any>; compact?: boolean }) {
  const find = (v: string) => {
    if (custom && v in custom) return { country: '★ My places', state: '', city: v }
    for (const [country, c] of Object.entries<any>(catalog || {})) {
      if (country === v) return { country, state: '', city: '' }
      if (c.has_states) {
        for (const [st, sd] of Object.entries<any>(c.states || {}))
          if ((sd.cities || []).includes(v)) return { country, state: st, city: v }   // a city wins over a same-named state
        for (const st of Object.keys(c.states || {})) if (st === v) return { country, state: st, city: '' }
      } else if ((c.cities || []).includes(v)) return { country, state: '', city: v }
    }
    return { country: 'United States', state: '', city: '' }
  }
  const cur = find(value)
  const countries = [...Object.keys(catalog || {}), ...(custom && Object.keys(custom).length ? ['★ My places'] : [])]
  const c = catalog?.[cur.country]
  const states = c?.has_states ? Object.keys(c.states || {}).sort() : []
  const cities = cur.country === '★ My places' ? Object.keys(custom || {}) : c?.has_states ? (c.states?.[cur.state]?.cities || []) : (c?.cities || [])
  const cls = compact ? 'min-w-[120px]' : 'min-w-[150px]'
  return (
    <div className="flex flex-wrap gap-2">
      <div className={cls}><Select value={cur.country} options={countries} onChange={v => {
        if (v === '★ My places') onChange(Object.keys(custom || {})[0])
        else { const cc = catalog[v]; onChange(cc?.has_states ? Object.keys(cc.states || {}).sort()[0] : (cc?.cities?.[0] || v)) }
      }} /></div>
      {states.length > 0 && <div className={cls}><Select value={cur.state || states[0]} options={states} onChange={onChange} /></div>}
      {cities.length > 0 && (
        <div className={cls}><Select value={cur.city || ''} onChange={v => onChange(v || (cur.state || cur.country))}
          options={[...(cur.country === '★ My places' ? [] : [{ value: '', label: cur.state ? `${cur.state} average` : `${cur.country} average` }]), ...cities.map((x: string) => ({ value: x, label: x }))]} /></div>
      )}
    </div>
  )
}

function factorChip(f: number | null | undefined, label: string) {
  if (f === null || f === undefined) return null
  const pct = Math.round((f - 1) * 100)
  return <Badge tone={Math.abs(pct) < 3 ? 'neutral' : pct < 0 ? 'good' : 'warn'}>{label} {pct === 0 ? '±0%' : `${pct > 0 ? '+' : ''}${pct}%`}</Badge>
}

export default function Locations() {
  const { plan, update, reference, names, single, proj } = usePlan()
  const [info, setInfo] = useState<any>(null)
  const catalog = reference?.location_catalog
  const custom: Record<string, any> = plan.custom_locations || {}
  const coords = { ...(reference?.coordinates || {}), ...Object.fromEntries(Object.entries(custom).filter(([, v]: any) => v.lat != null).map(([k, v]: any) => [k, { lat: v.lat, lon: v.lon }])) }
  const stl: any[] = plan.state_timeline || []
  const cy = plan.current_year
  const endYear = proj?.summary?.end_year ?? cy + 60

  useEffect(() => { let live = true; api.locationsInfo(plan).then(r => live && setInfo(r)).catch(() => {}); return () => { live = false } },
    [JSON.stringify(stl), JSON.stringify(custom), JSON.stringify(plan.custom_expense_templates || {}), plan.move_adjusts_spending])

  const segments = useMemo(() => stl.map((e, i) => ({ ...e, from: Math.max(e.year, cy), to: i + 1 < stl.length ? stl[i + 1].year - 1 : endYear }))
    .filter(s => s.to >= s.from), [stl, cy, endYear])
  const colorOf = useMemo(() => { const m: Record<string, string> = {}; let k = 0; stl.forEach(e => { if (!(e.state in m)) m[e.state] = S[k++ % 8] }); return m }, [stl])
  const stops: MapStop[] = useMemo(() => {
    const out: MapStop[] = []
    stl.forEach(e => {
      if (out.length && out[out.length - 1].name === e.state) return
      const c = coords[e.state]
      if (c) out.push({ n: out.length + 1, name: e.state, year: e.year, lat: c.lat, lon: c.lon })
    })
    return out
  }, [stl, coords])
  const missing = [...new Set(stl.map(e => e.state).filter(s => !coords[s]))]
  const death1 = cy + (plan.parentX_death_age - plan.parentX_age), death2 = cy + (plan.parentY_death_age - plan.parentY_age)
  const curEntry = [...stl].reverse().find(e => e.year <= cy) || stl[0]
  const soon = stl.filter(e => e.year > cy && e.year <= cy + 5)

  const journey = (() => {
    const lines: string[] = []
    let prev: any = null
    stl.forEach(e => {
      if (!prev) lines.push(`Start in ${e.state} (${e.spending_strategy} lifestyle) in ${Math.max(e.year, cy)}`)
      else if (prev.state !== e.state) lines.push(`After ${e.year - Math.max(prev.year, cy)} years, move to ${e.state} in ${e.year}${prev.spending_strategy !== e.spending_strategy ? ` and switch to ${e.spending_strategy}` : ''}`)
      else if (prev.spending_strategy !== e.spending_strategy) lines.push(`In ${e.year}, switch to a ${e.spending_strategy} lifestyle in ${e.state}`)
      prev = e
    })
    return lines
  })()

  return (
    <div className="space-y-5">
      <PageHeader title="Where you live" subtitle="Moves change your taxes and, if you want, your cost of living. Plan relocations and lifestyle changes over time." />

      <Card title="Moves & lifestyle" subtitle="Each row starts on January 1 of its year"
        action={<Button size="sm" onClick={() => update(d => { const last = d.state_timeline[d.state_timeline.length - 1]; d.state_timeline.push({ year: Math.max(last.year, cy) + 5, state: last.state, spending_strategy: last.spending_strategy }) })}><Plus size={14} />Add move</Button>}>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Toggle checked={plan.move_adjusts_spending !== false} onChange={v => update(d => { d.move_adjusts_spending = v })} label="Moving changes our everyday spending"
            hint="Everyday spending follows BEA price parities between US states and cities (World Bank price levels abroad); rent follows the BEA rent index. Off = the old app's behaviour, where a move only changes taxes." />
        </div>
        <div className="space-y-2.5">
          {stl.map((e, i) => {
            const inf = info?.entries?.[i]
            return (
              <div key={i} className="rounded-lg border border-line p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="w-24"><NumberInput value={e.year} step={1} onChange={v => update(d => { d.state_timeline[i].year = Math.round(v); d.state_timeline.sort((a: any, b: any) => a.year - b.year) })} /></div>
                  <LocationPicker value={e.state} catalog={catalog} custom={custom} onChange={v => update(d => { d.state_timeline[i].state = v })} />
                  <div className="w-36"><Select value={String(e.spending_strategy || 'Average').replace(' (statistical)', '')} options={LIFESTYLES} onChange={v => update(d => { d.state_timeline[i].spending_strategy = v })} /></div>
                  <span className="flex-1" />
                  <button disabled={stl.length === 1} className="p-1.5 rounded text-muted hover:text-bad disabled:opacity-30" onClick={() => update(d => { d.state_timeline.splice(i, 1) })}><Trash2 size={15} /></button>
                </div>
                {inf && (
                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[12.5px] text-ink2">
                    {plan.move_adjusts_spending !== false && i > 0 && factorChip(inf.spending_factor, 'Everyday spending')}
                    {plan.move_adjusts_spending !== false && i > 0 && inf.rent_factor != null && factorChip(inf.rent_factor, 'Rent')}
                    <span>{inf.tax.text}</span>
                    <span className="text-muted">· {({ bea: 'BEA price data', country: 'World Bank price level (rough)', relative: 'audited template', custom: 'your template', us: 'US-average prices (no local data)' } as any)[inf.basis]}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      <Card title="Timeline" subtitle={`Location and lifestyle from ${cy} until ${endYear}`}>
        <div className="flex h-12 rounded-lg overflow-hidden border border-line">
          {segments.map((s, i) => (
            <div key={i} title={`${s.state} · ${s.spending_strategy} · ${s.from}–${s.to}`} className="flex flex-col justify-center px-2 text-white text-[12px] leading-tight overflow-hidden whitespace-nowrap"
              style={{ width: `${((s.to - s.from + 1) / (endYear - cy + 1)) * 100}%`, background: colorOf[s.state], opacity: s.spending_strategy === 'Conservative' ? 0.8 : s.spending_strategy === 'High-end' ? 1 : 0.9 }}>
              <span className="font-semibold truncate">{s.state}</span><span className="truncate opacity-90">{s.spending_strategy} · {s.from}–{s.to}</span>
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[11.5px] text-muted mt-1 tnum">{Array.from({ length: 7 }, (_, k) => Math.round(cy + (endYear - cy) * k / 6)).map(y => <span key={y}>{y}</span>)}</div>
        <p className="text-[13px] text-ink2 mt-3">The timeline runs to <b>{endYear}</b>: {names[0]} reaches {plan.parentX_death_age} in {death1}{!single && <>, {names[1]} reaches {plan.parentY_death_age} in {death2}</>}.</p>
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <div className="rounded-lg bg-sunken/70 p-3 text-sm"><div className="text-[12px] text-muted mb-0.5">Now</div>
            <b>{curEntry?.state}</b> · {curEntry?.spending_strategy} lifestyle</div>
          <div className="rounded-lg bg-sunken/70 p-3 text-sm"><div className="text-[12px] text-muted mb-0.5">Next 5 years</div>
            {soon.length ? soon.map((e, i) => <div key={i}>{e.year}: {e.state} · {e.spending_strategy}</div>) : 'No changes planned'}</div>
        </div>
      </Card>

      <Card title={<span className="flex items-center gap-2"><Plane size={16} className="text-accent" />Your relocation journey</span>}>
        {stops.length ? <WorldMap stops={stops} /> : <Empty icon={<MapPin size={20} />} title="No map locations" body="Pick locations above to see them on the map." />}
        <ol className="mt-3 space-y-1 text-sm list-decimal pl-5">{journey.map((l, i) => <li key={i}>{l}</li>)}</ol>
        {missing.length > 0 && <div className="mt-3"><Note tone="warn"><span className="flex gap-2"><AlertTriangle size={15} className="shrink-0 mt-0.5" />
          No map coordinates for {missing.join(', ')}. Add them under My places below.</span></Note></div>}
      </Card>

      <TemplateBrowser />
      <MyPlaces />
    </div>
  )
}

// ── cost-of-living templates ──────────────────────────────────────────────
function TemplateBrowser() {
  const { plan, update, reference } = usePlan()
  const [loc, setLoc] = useState<string>(plan.state_timeline?.[0]?.state || 'Seattle')
  const [life, setLife] = useState('Average')
  const [source, setSource] = useState<'calibrated' | 'v08'>('calibrated')
  const [vals, setVals] = useState<Record<string, number> | null>(null)
  const [saveAs, setSaveAs] = useState<string | null>(null)
  const [editing, setEditing] = useState<{ loc: string; name: string; vals: Record<string, number> } | null>(null)
  const [confirmDel, setConfirmDel] = useState<{ loc: string; name: string } | null>(null)
  const infl = plan.economic_params?.inflation_rate ?? 0.03
  const scale = Math.pow(1 + infl, Math.max(0, plan.current_year - 2024))
  const customT: Record<string, Record<string, Record<string, number>>> = plan.custom_expense_templates || {}
  const groups: Record<string, string[]> = reference?.adult_categories || {}
  useEffect(() => { let live = true; setVals(null); api.template('adult', loc, `${life} (statistical)`, plan.current_year, infl, source).then(r => live && setVals(r)).catch(() => {}); return () => { live = false } }, [loc, life, source, plan.current_year, infl])
  const total = vals ? Object.values(vals).reduce((a, b) => a + b, 0) : 0
  const pie = useMemo(() => vals ? Object.entries(groups).map(([g, cats]) => ({ name: g, value: cats.reduce((a, c) => a + (vals[c] || 0), 0) })).filter(x => x.value > 0) : [], [vals, groups])
  const src = reference?.data_sources?.[loc] || reference?.data_sources?.[String(loc).split(',')[0]]

  return (
    <Card title={<span className="flex items-center gap-2"><Database size={16} className="text-accent" />Cost-of-living templates</span>}
      subtitle="Per-adult everyday spending (not housing or kids) behind the spending slider and moves. Browse, then save a copy you can edit.">
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <Field label="Location"><LocationPicker value={loc} onChange={setLoc} catalog={reference?.location_catalog} compact /></Field>
        <Field label="Lifestyle" className="w-40"><Select value={life} options={LIFESTYLES} onChange={setLife} /></Field>
        <Field label="Data" className="w-64"><Select value={source} options={[{ value: 'calibrated', label: 'BLS spending + BEA prices (2024)' }, { value: 'v08', label: 'v0.8 original (audited)' }]} onChange={setSource} /></Field>
      </div>
      {!vals ? <div className="h-40 text-sm text-muted">Loading…</div> : (
        <div className="grid lg:grid-cols-[260px_1fr] gap-5">
          <div>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pie} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={1} isAnimationActive={false}>
                  {pie.map((_, i) => <Cell key={i} fill={S[i % 8]} stroke="var(--chart-surface)" />)}
                </Pie>
                <Tooltip formatter={(v: any) => money(v, { compact: false })} contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="text-center -mt-2"><div className="text-[22px] font-semibold tnum">{money(total, { compact: false })}</div>
              <div className="text-[12px] text-muted">per adult per year · {money(total / 12, { compact: false })}/mo</div></div>
            <div className="mt-3 space-y-1">{pie.map((p, i) => (
              <div key={p.name} className="flex items-center gap-2 text-[12.5px]"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: S[i % 8] }} />
                <span className="flex-1">{p.name}</span><span className="tnum">{money(p.value)}</span><span className="text-muted w-10 text-right">{Math.round(p.value / total * 100)}%</span></div>))}</div>
          </div>
          <div>
            <table className="w-full text-sm">
              <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium">Category</th><th className="font-medium text-right">Per year</th><th className="font-medium text-right">Per month</th></tr></thead>
              <tbody>{Object.entries(groups).map(([g, cats]) => (
                <React.Fragment key={g}>
                  <tr><td colSpan={3} className="pt-2.5 pb-1 text-[11.5px] font-semibold uppercase tracking-wide text-muted">{g}</td></tr>
                  {cats.map(c => <tr key={c} className="border-b border-line/60"><td className="py-1">{c}</td><td className="text-right tnum">{money(vals[c] || 0, { compact: false })}</td><td className="text-right tnum text-ink2">{money((vals[c] || 0) / 12, { compact: false })}</td></tr>)}
                </React.Fragment>))}</tbody>
            </table>
            <div className="flex flex-wrap gap-2 mt-4">
              <Button onClick={() => setSaveAs(`${life} (custom)`)}><Save size={14} />Save as my template</Button>
            </div>
            <div className="mt-4 rounded-lg bg-sunken/70 p-3 text-[12.5px] text-ink2">
              <div className="font-medium mb-1">Data sources</div>
              {source === 'calibrated'
                ? <p>BLS Consumer Expenditure Survey (2022 income quintiles, grown to 2024 totals) for spending levels; BEA Regional Price Parities 2024 for US states and metros; World Bank price levels (2020) for other countries. See docs/COST_OF_LIVING_AUDIT.md.</p>
                : src ? <p>{src.source} ({src.year}). {src.notes} <span className="text-muted">{src.url}</span></p> : <p>v0.8 template, corrected by the 2026 audit (location scale, lifestyle ratios, state medical).</p>}
            </div>
          </div>
        </div>
      )}
      {Object.keys(customT).length > 0 && (
        <div className="mt-6">
          <div className="text-[12.5px] font-semibold uppercase tracking-wide text-muted mb-2">My templates</div>
          <div className="divide-y divide-line border border-line rounded-lg">
            {Object.entries(customT).flatMap(([l, strats]) => Object.entries(strats).map(([name, t]) => (
              <div key={l + name} className="flex items-center gap-3 px-3 py-2 text-sm">
                <Building2 size={15} className="text-muted" /><span className="flex-1">{l} · {name}</span>
                <span className="tnum text-ink2">{money(Object.values(t).reduce((a, b) => a + b, 0) * scale)}/yr</span>
                <Button size="sm" variant="ghost" onClick={() => setEditing({ loc: l, name, vals: Object.fromEntries(Object.entries(t).map(([k, v]) => [k, Math.round(v * scale)])) })}><Pencil size={13} />Edit</Button>
                <button className="p-1 text-muted hover:text-bad" onClick={() => setConfirmDel({ loc: l, name })}><Trash2 size={14} /></button>
              </div>)))}
          </div>
          <p className="text-[12px] text-muted mt-1.5">Your templates override the built-in data for that location, including when you move there.</p>
        </div>
      )}
      <Modal open={saveAs !== null} onClose={() => setSaveAs(null)} title={`Save ${loc} template`}
        footer={<><Button onClick={() => setSaveAs(null)}>Cancel</Button><Button variant="primary" onClick={() => {
          const name = (saveAs || '').trim() || `${life} (custom)`
          const nm = name.endsWith('(custom)') ? name : `${name} (custom)`
          update(d => { d.custom_expense_templates = d.custom_expense_templates || {}; d.custom_expense_templates[loc] = d.custom_expense_templates[loc] || {}
            d.custom_expense_templates[loc][nm] = Object.fromEntries(Object.entries(vals || {}).map(([k, v]) => [k, Math.round(v / scale)])) })
          setSaveAs(null); setEditing({ loc, name: nm, vals: { ...(vals || {}) } })
        }}>Save</Button></>}>
        <Field label="Template name"><TextInput value={saveAs || ''} onChange={setSaveAs} /></Field>
      </Modal>
      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing ? `${editing.loc} · ${editing.name}` : ''}
        footer={<><Button onClick={() => setEditing(null)}>Cancel</Button><Button variant="primary" onClick={() => {
          const e = editing!
          update(d => { d.custom_expense_templates[e.loc][e.name] = Object.fromEntries(Object.entries(e.vals).map(([k, v]) => [k, Math.round(v / scale)])) })
          setEditing(null)
        }}>Save changes</Button></>}>
        <div className="max-h-[55vh] overflow-y-auto space-y-1.5 pr-1">
          {editing && Object.entries(editing.vals).map(([k, v]) => (
            <div key={k} className="grid grid-cols-[1fr_130px] items-center gap-2 text-sm"><span>{k}</span>
              <Money value={v} step={100} onChange={nv => setEditing(e => e && { ...e, vals: { ...e.vals, [k]: nv } })} /></div>))}
        </div>
        <p className="text-[12px] text-muted">Amounts in {plan.current_year} dollars per adult per year.</p>
      </Modal>
      <Modal open={!!confirmDel} onClose={() => setConfirmDel(null)} title="Delete this template?"
        footer={<><Button onClick={() => setConfirmDel(null)}>Cancel</Button><Button variant="danger" onClick={() => {
          const c = confirmDel!
          update(d => { delete d.custom_expense_templates[c.loc][c.name]; if (!Object.keys(d.custom_expense_templates[c.loc]).length) delete d.custom_expense_templates[c.loc] })
          setConfirmDel(null)
        }}>Delete</Button></>}>
        <p className="text-sm text-ink2">{confirmDel?.loc} · {confirmDel?.name}. Spending you already applied from it stays as it is.</p>
      </Modal>
    </Card>
  )
}

// ── custom places ─────────────────────────────────────────────────────────
function MyPlaces() {
  const { plan, update, reference } = usePlan()
  const custom: Record<string, any> = plan.custom_locations || {}
  const blank = { name: '', country: 'United States', region: '', lat: null as number | null, lon: null as number | null, tax_location: 'Washington', cost_like: 'Seattle' }
  const [draft, setDraft] = useState<typeof blank | null>(null)
  const taxOptions = [...Object.keys(reference?.us_state_tax || {}).sort(), ...Object.keys(reference?.country_tax || {}).sort()]
  const costOptions = [...new Set([...(reference?.locations || []), ...Object.keys(reference?.country_tax || {})])].sort()
  return (
    <Card title={<span className="flex items-center gap-2"><MapPin size={16} className="text-accent" />My places</span>}
      subtitle="Add a city the app doesn't know: where it is on the map, which tax rules apply, and which known place its prices are like"
      action={<Button size="sm" onClick={() => setDraft({ ...blank })}><Plus size={14} />Add a place</Button>}>
      {Object.keys(custom).length === 0 ? <p className="text-sm text-muted">No custom places yet.</p> : (
        <table className="w-full text-sm">
          <thead><tr className="text-left text-[12px] text-muted border-b border-line"><th className="py-1.5 font-medium">Place</th><th className="font-medium">Country / region</th>
            <th className="font-medium">Taxed like</th><th className="font-medium">Prices like</th><th className="font-medium">Map</th><th /></tr></thead>
          <tbody>{Object.entries(custom).map(([name, c]) => (
            <tr key={name} className="border-b border-line last:border-0">
              <td className="py-2 font-medium">{name}</td><td>{c.country}{c.region ? ` · ${c.region}` : ''}</td><td>{c.tax_location}</td><td>{c.cost_like}</td>
              <td>{c.lat != null ? `${(+c.lat).toFixed(2)}, ${(+c.lon).toFixed(2)}` : <span className="text-warn">missing</span>}</td>
              <td className="text-right whitespace-nowrap">
                <Button size="sm" variant="ghost" onClick={() => setDraft({ ...blank, ...c, name })}><Pencil size={13} /></Button>
                <button className="p-1 text-muted hover:text-bad" disabled={(plan.state_timeline || []).some((e: any) => e.state === name)}
                  title={(plan.state_timeline || []).some((e: any) => e.state === name) ? 'Used in your moves' : 'Delete'}
                  onClick={() => update(d => { delete d.custom_locations[name] })}><Trash2 size={14} /></button></td>
            </tr>))}</tbody>
        </table>)}
      <Modal open={!!draft} onClose={() => setDraft(null)} title={draft && custom[draft.name] ? `Edit ${draft.name}` : 'Add a place'}
        footer={<><Button onClick={() => setDraft(null)}>Cancel</Button><Button variant="primary" disabled={!draft?.name.trim()} onClick={() => {
          const d0 = draft!
          update(d => { d.custom_locations = d.custom_locations || {}; d.custom_locations[d0.name.trim()] = { country: d0.country, region: d0.region, lat: d0.lat, lon: d0.lon, tax_location: d0.tax_location, cost_like: d0.cost_like } })
          setDraft(null)
        }}>Save</Button></>}>
        {draft && <div className="space-y-3">
          <Field label="Name"><TextInput value={draft.name} onChange={v => setDraft({ ...draft, name: v })} placeholder="e.g. Bend, OR or Lisbon" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Country"><TextInput value={draft.country} onChange={v => setDraft({ ...draft, country: v })} /></Field>
            <Field label="State / region"><TextInput value={draft.region} onChange={v => setDraft({ ...draft, region: v })} /></Field>
            <Field label="Latitude"><NumberInput value={draft.lat} decimals={4} onChange={v => setDraft({ ...draft, lat: v })} placeholder="47.61" /></Field>
            <Field label="Longitude"><NumberInput value={draft.lon} decimals={4} onChange={v => setDraft({ ...draft, lon: v })} placeholder="-122.33" /></Field>
          </div>
          <Field label="Taxed like" hint="Which state or country's income-tax rules apply"><Select value={draft.tax_location} options={taxOptions} onChange={v => setDraft({ ...draft, tax_location: v })} /></Field>
          <Field label="Prices like" hint="Everyday prices and rent are borrowed from this place (or save your own template for this name)"><Select value={draft.cost_like} options={costOptions} onChange={v => setDraft({ ...draft, cost_like: v })} /></Field>
        </div>}
      </Modal>
    </Card>
  )
}
