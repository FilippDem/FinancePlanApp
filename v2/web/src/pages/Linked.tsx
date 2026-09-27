import React, { useEffect, useRef, useState } from 'react'
import { Link2, RefreshCw, Upload, Trash2, ExternalLink, AlertTriangle, CheckCircle2, KeyRound, Plug, FileSpreadsheet, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { useCites } from '../components/Cite'
import { Card, PageHeader, Field, Select, Toggle, Button, Note, Badge, TextInput, Empty } from '../components/ui'

const KIND_OPTS = [{ value: 'liquid', label: 'Cash & investments' }, { value: 'retirement', label: 'Pre-tax retirement' }, { value: 'roth', label: 'Roth' },
  { value: 'hsa', label: 'HSA' }, { value: 'ignore', label: "Don't count" }]
const STALE_HOURS = 12

export const fmtWhen = (iso?: string | null) => {
  if (!iso) return 'never'
  const d = new Date(iso)
  return isNaN(+d) ? iso : d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
export const isStale = (iso?: string | null) => !iso || (Date.now() - +new Date(iso)) / 36e5 > STALE_HOURS

/** Balances from Fidelity and other brokerages. Everything here is optional: a CSV works with no setup,
 *  SnapTrade makes it automatic, and the rest of the app works the same without either. */
export default function Linked() {
  const { plan, names, single } = usePlan()
  const { Cite, Sources } = useCites(['snaptrade_personal', 'snaptrade_fidelity', 'snaptrade_sync'])
  const [st, setSt] = useState<any>(null)
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [keys, setKeys] = useState({ client_id: '', consumer_key: '', user_id: '', user_secret: '' })
  const [adv, setAdv] = useState(false)
  const [inst, setInst] = useState('Fidelity')
  const fileRef = useRef<HTMLInputElement>(null)
  const ownOn = !!plan.ownership_tracking?.enabled && !single

  const run = async (label: string, fn: () => Promise<any>, ok?: string) => {
    setBusy(label); setErr(''); setMsg('')
    try { const r = await fn(); if (r?.accounts) setSt(r); if (ok) setMsg(ok) } catch (e: any) { setErr(e.message || String(e)) } finally { setBusy('') }
  }
  useEffect(() => {
    api.linked().then(r => {
      setSt(r)
      // keep automatic balances fresh when the page opens (the server also syncs daily on its own)
      if (r.snaptrade?.configured && isStale(r.last_sync)) run('sync', api.linkedSync)
    }).catch(e => setErr(e.message))
  }, [])

  const openPortal = (reconnect?: string, broker: string | null = 'FIDELITY') => run('portal', async () => {
    const { url } = await api.linkedPortal({ broker, reconnect })
    window.open(url, '_blank', 'noopener')
    setMsg('Finish signing in at the tab that opened, then press Sync now.')
  })
  const upload = async (files: FileList | null) => {
    if (!files?.length) return
    for (const f of Array.from(files)) {
      await run('csv', async () => {
        const r = await api.linkedCsv(f, inst)
        setMsg(`${f.name}: ${r.imported.length} account${r.imported.length === 1 ? '' : 's'} imported. Check who each belongs to below.`)
        return r
      })
    }
    if (fileRef.current) fileRef.current.value = ''
  }

  if (!st) return <div className="space-y-5"><PageHeader title="Linked accounts" />{err ? <Note tone="warn">{err}</Note> : <div className="h-40" />}</div>

  const t = st.totals
  const disabled = (st.connections || []).filter((c: any) => c.disabled)
  const ownerOpts = [{ value: 'p1', label: names[0] }, ...(single ? [] : [{ value: 'p2', label: names[1] }, { value: 'joint', label: 'Joint' }])]

  return (
    <div className="space-y-5">
      <PageHeader title="Linked accounts" subtitle="Pull balances from Fidelity and other brokerages so check-ins fill themselves in. Optional: typing balances always works, and nothing else in the app depends on this." />
      {err && <Note tone="warn">{err}</Note>}
      {msg && <Note>{msg}</Note>}
      {disabled.length > 0 && (
        <Note tone="warn"><span className="flex flex-wrap items-center gap-2"><AlertTriangle size={15} />
          {disabled.map((c: any) => c.institution || 'A brokerage').join(', ')} needs you to sign in again (password change or expired session). Balances shown are the last ones received.
          {disabled.map((c: any) => <Button key={c.id} size="sm" onClick={() => openPortal(c.id, null)}>Reconnect {c.institution}</Button>)}</span></Note>)}

      {st.accounts.length > 0 && (
        <Card title="What the linked accounts add up to" subtitle={`${t.accounts} account${t.accounts === 1 ? '' : 's'} counted · oldest balance ${fmtWhen(t.as_of)}`}
          action={<Toggle checked={!!st.covers_all} onChange={v => run('settings', () => api.linkedSettings({ covers_all: v }))} label="These are all our savings"
            hint="On: check-ins start from these totals. Off: check-ins show them as a hint and you add accounts held elsewhere." />}>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {(single ? ['p1'] : ['p1', 'p2']).map((w, i) => (
              <React.Fragment key={w}>
                <div className="rounded-lg border border-line p-3"><div className="text-[12.5px] text-muted">{names[i]}: cash & investments</div>
                  <div className="text-[20px] font-semibold tnum">{money(t[w].liquid)}</div>
                  <div className="text-[11.5px] text-muted">Plan says {money(plan[`parent${w === 'p1' ? 'X' : 'Y'}_net_worth`] - (plan[`parent${w === 'p1' ? 'X' : 'Y'}_pretax_balance`] || 0) - (plan[`parent${w === 'p1' ? 'X' : 'Y'}_roth_balance`] || 0))}{ownOn && t[w].separate_liquid > 0 ? ` · ${money(t[w].separate_liquid)} separate` : ''}</div></div>
                <div className="rounded-lg border border-line p-3"><div className="text-[12.5px] text-muted">{names[i]}: retirement & HSA</div>
                  <div className="text-[20px] font-semibold tnum">{money(t[w].pretax + (t[w].roth || 0))}</div>
                  <div className="text-[11.5px] text-muted">{t[w].roth > 0 ? `${money(t[w].roth)} Roth · ` : ''}Plan says {money((plan[`parent${w === 'p1' ? 'X' : 'Y'}_pretax_balance`] || 0) + (plan[`parent${w === 'p1' ? 'X' : 'Y'}_roth_balance`] || 0))}{ownOn && t[w].separate_pretax > 0 ? ` · ${money(t[w].separate_pretax)} separate` : ''}</div></div>
              </React.Fragment>))}
          </div>
          {st.covers_all == null && (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-accent/25 bg-accentSoft/60 px-3 py-2.5 text-sm">
              <span className="font-medium">Do these accounts hold all your savings and retirement money?</span>
              <Button size="sm" variant="primary" onClick={() => run('settings', () => api.linkedSettings({ covers_all: true }))}>Yes, start check-ins from them</Button>
              <Button size="sm" onClick={() => run('settings', () => api.linkedSettings({ covers_all: false }))}>No, we have money elsewhere</Button>
            </div>)}
          <p className="text-[12.5px] text-muted mt-3">{st.covers_all
            ? 'Check-ins start from these totals, and the plan updates from them when you finish a check-in, so you can review before anything changes.'
            : 'Check-ins show these totals next to your balances with a "Use these" button; add anything held elsewhere.'}</p>
        </Card>)}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={<span className="flex items-center gap-2"><Plug size={16} className="text-accent" />Automatic (optional)</span>}
          subtitle={<>Read-only sync through SnapTrade: you sign in at Fidelity itself, so your password is never shared with SnapTrade or this app<Cite id="snaptrade_fidelity" />. Balances refresh once a day<Cite id="snaptrade_sync" />; the app checks every hour while it's running.</>}>
          {!st.snaptrade.configured ? (
            <div className="space-y-3">
              <ol className="list-decimal pl-5 text-sm text-ink2 space-y-1">
                <li>Create a free SnapTrade Personal account and copy its Client ID and Consumer Key<Cite id="snaptrade_personal" />.
                  <a className="text-accent ml-1 inline-flex items-center gap-0.5" href="https://snaptrade.com/personal" target="_blank" rel="noreferrer">snaptrade.com/personal<ExternalLink size={12} /></a></li>
                <li>Paste them here. They're checked, then stored with your household and never shown again.</li>
                <li>Press Connect Fidelity and sign in at Fidelity.</li>
              </ol>
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="Client ID"><TextInput value={keys.client_id} onChange={v => setKeys({ ...keys, client_id: v })} /></Field>
                <Field label="Consumer key"><input type="password" autoComplete="off" value={keys.consumer_key} onChange={e => setKeys({ ...keys, consumer_key: e.target.value })}
                  className="w-full h-9 rounded-lg border border-line bg-surface px-3 text-sm" /></Field>
              </div>
              <button className="text-[12.5px] text-muted hover:text-ink" onClick={() => setAdv(!adv)}>{adv ? 'Hide' : 'Using commercial keys?'}</button>
              {adv && <div className="grid sm:grid-cols-2 gap-3">
                <Field label="User ID"><TextInput value={keys.user_id} onChange={v => setKeys({ ...keys, user_id: v })} /></Field>
                <Field label="User secret"><input type="password" autoComplete="off" value={keys.user_secret} onChange={e => setKeys({ ...keys, user_secret: e.target.value })}
                  className="w-full h-9 rounded-lg border border-line bg-surface px-3 text-sm" /></Field>
              </div>}
              <Button variant="primary" disabled={!keys.client_id || !keys.consumer_key || !!busy}
                onClick={() => run('keys', async () => { const r = await api.linkedSetKeys({ ...keys, user_id: keys.user_id || undefined, user_secret: keys.user_secret || undefined }); setKeys({ client_id: '', consumer_key: '', user_id: '', user_secret: '' }); return r }, 'Keys saved. Now connect Fidelity.')}>
                {busy === 'keys' ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />}Save keys</Button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <CheckCircle2 size={16} className="text-good" />SnapTrade {st.snaptrade.mode} keys ({st.snaptrade.client_id}) added by {st.snaptrade.added_by}
              </div>
              <div className="text-[13px] text-ink2">Last sync: <b>{fmtWhen(st.last_sync)}</b>{st.last_error && <span className="text-bad"> · last attempt failed: {st.last_error}</span>}</div>
              {(st.connections || []).length > 0 && <div className="flex flex-wrap gap-2">{st.connections.map((c: any) => (
                <Badge key={c.id} tone={c.disabled ? 'warn' : 'good'}>{c.institution || 'Brokerage'}{c.disabled ? ': sign in again' : ': connected'}</Badge>))}</div>}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary" onClick={() => openPortal()} disabled={!!busy}><Link2 size={14} />{(st.connections || []).some((c: any) => /fidelity/i.test(c.institution)) ? 'Connect another Fidelity login' : 'Connect Fidelity'}</Button>
                <Button onClick={() => openPortal(undefined, null)} disabled={!!busy}>Other brokerage</Button>
                <Button onClick={() => run('sync', api.linkedSync, 'Synced.')} disabled={!!busy}>{busy === 'sync' ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}Sync now</Button>
                <Button variant="ghost" onClick={() => run('remove', api.linkedRemoveKeys, 'Keys removed. Imported balances stay until you delete them.')} disabled={!!busy}>Remove keys</Button>
              </div>
              <p className="text-[12px] text-muted">Encrypted households sync when you open the app (the server can't read their keys on its own). A "Sync now" during the day may count against SnapTrade limits; daily is plenty for planning.</p>
            </div>)}
        </Card>

        <Card title={<span className="flex items-center gap-2"><FileSpreadsheet size={16} className="text-accent" />Import a CSV (no setup)</span>}
          subtitle="Works for any brokerage or bank that exports balances or positions. Import again any time to update.">
          <ol className="list-decimal pl-5 text-sm text-ink2 space-y-1 mb-3">
            <li>At Fidelity.com: Accounts & Trade → Portfolio → Positions, then the Download button (all accounts in one file, or one account at a time).</li>
            <li>Choose the file here. Positions are added up per account.</li>
          </ol>
          <div className="flex flex-wrap items-end gap-3">
            <Field label="From" className="w-44"><TextInput value={inst} onChange={setInst} /></Field>
            <input ref={fileRef} type="file" accept=".csv,text/csv" multiple className="hidden" onChange={e => upload(e.target.files)} />
            <Button onClick={() => fileRef.current?.click()} disabled={!!busy}>{busy === 'csv' ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}Choose CSV files</Button>
          </div>
          <p className="text-[12px] text-muted mt-2">Also reads simple two-column files (account, balance) from other institutions.</p>
        </Card>
      </div>

      <Card title="Accounts" subtitle="Say once who each account belongs to and what kind it is; syncs and imports keep your choices." pad={false}>
        {st.accounts.length === 0 ? <Empty icon={<Link2 size={20} />} title="No accounts yet" body="Import a CSV or connect a brokerage above." /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[820px]">
              <thead><tr className="text-left text-[12px] text-muted border-b border-line">
                <th className="px-5 py-2 font-medium">Account</th><th className="font-medium">Source</th><th className="font-medium text-right">Balance</th><th className="font-medium pl-4">As of</th>
                {!single && <th className="font-medium">Belongs to</th>}<th className="font-medium">Counts as</th>{ownOn && <th className="font-medium">Separate</th>}<th className="font-medium">Count it</th><th /></tr></thead>
              <tbody>{st.accounts.map((a: any) => (
                <tr key={a.key} className={`border-b border-line last:border-0 ${a.include === false || a.kind === 'ignore' ? 'opacity-55' : ''}`}>
                  <td className="px-5 py-2"><div className="font-medium">{a.name}</div><div className="text-[12px] text-muted">{a.institution}{a.number ? ` · ${a.number}` : ''}{a.missing ? ' · no longer reported' : ''}</div></td>
                  <td>{a.source === 'snaptrade' ? <Badge tone={a.disabled ? 'warn' : 'accent'}>{a.disabled ? 'Auto (reconnect)' : 'Auto'}</Badge> : <Badge>CSV</Badge>}</td>
                  <td className="text-right tnum">{money(a.balance, { compact: false })}</td>
                  <td className="pl-4 text-[12.5px] text-muted whitespace-nowrap">{fmtWhen(a.as_of)}</td>
                  {!single && <td className="pr-2 w-36"><Select value={a.owner} options={ownerOpts} onChange={v => run('upd', () => api.linkedUpdate(a.key, { owner: v }))} /></td>}
                  <td className="pr-2 w-44"><Select value={a.kind} options={KIND_OPTS} onChange={v => run('upd', () => api.linkedUpdate(a.key, { kind: v }))} /></td>
                  {ownOn && <td className="text-center">{a.owner !== 'joint' && <input type="checkbox" checked={!!a.separate} className="accent-[rgb(var(--accent))]"
                    title="Separate property (premarital, gift or inheritance)" onChange={e => run('upd', () => api.linkedUpdate(a.key, { separate: e.target.checked }))} />}</td>}
                  <td><Toggle checked={a.include !== false} onChange={v => run('upd', () => api.linkedUpdate(a.key, { include: v }))} /></td>
                  <td className="pr-4 text-right">{a.source !== 'snaptrade' && <button className="p-1 text-muted hover:text-bad" title="Delete" onClick={() => run('del', () => api.linkedDelete(a.key))}><Trash2 size={14} /></button>}</td>
                </tr>))}</tbody>
            </table>
          </div>)}
        <p className="px-5 pb-4 pt-2 text-[12px] text-muted">Pre-tax retirement accounts and HSAs count toward the plan's pre-tax balance (taxed on withdrawal, with required minimum distributions); Roth accounts are tracked separately (tax-free). Joint accounts are split evenly.</p>
      </Card>
      <Sources className="px-1" />
    </div>
  )
}
