import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Copy, Check, Users, ShieldCheck, Trash2, Pencil, FlaskConical, Lock, HardDrive, Cloud } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { Card, PageHeader, Button, TextInput, Badge, Note, Modal } from '../components/ui'

/** v0.8 Users tab: household name, invite code, members, last saved, auto-save, data security. */
export default function Household() {
  const { household, saveState, lastSaved } = usePlan()
  const nav = useNavigate()
  const [h, setH] = useState<any>(null)
  const [edit, setEdit] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [remove, setRemove] = useState<string | null>(null)
  const [msg, setMsg] = useState('')
  const load = () => api.householdDetails().then(setH).catch(() => {})
  useEffect(() => { load() }, [lastSaved])
  if (!h) return <div className="text-sm text-muted">Loading…</div>
  return (
    <div className="space-y-5">
      <PageHeader title="Household & members" subtitle="Everyone in the household sees and edits the same plan" />
      {msg && <Note>{msg}</Note>}
      {h.is_test && <Note tone="warn"><span className="flex items-center gap-2"><FlaskConical size={15} />This is an isolated test household. It isn't backed up and can be cleaned up at any time.</span></Note>}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Household">
          <dl className="grid grid-cols-[140px_1fr] gap-y-3 text-sm items-center">
            <dt className="text-muted">Name</dt>
            <dd className="flex items-center gap-2">{edit === null ? <><span className="font-medium">{h.name}</span>
              <button className="p-1 text-muted hover:text-ink" onClick={() => setEdit(h.name)}><Pencil size={14} /></button></> : <>
              <TextInput value={edit} onChange={setEdit} className="max-w-[220px]" />
              <Button size="sm" variant="primary" onClick={async () => { await api.renameHousehold(edit); setEdit(null); load(); setMsg('Renamed. Other members see the new name next time they open the app.') }}>Save</Button>
              <Button size="sm" variant="ghost" onClick={() => setEdit(null)}>Cancel</Button></>}</dd>
            <dt className="text-muted">Household code</dt>
            <dd className="flex items-center gap-2"><span className="font-mono text-[15px] px-2 py-0.5 rounded bg-sunken">{h.id}</span>
              <Button size="sm" variant="ghost" onClick={() => { navigator.clipboard?.writeText(h.id); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>
                {copied ? <Check size={14} /> : <Copy size={14} />}{copied ? 'Copied' : 'Copy'}</Button></dd>
            <dt className="text-muted">Created</dt><dd>{h.created_at ? new Date(h.created_at).toLocaleDateString() : '—'}{h.created_by ? ` by ${h.created_by}` : ''}</dd>
            <dt className="text-muted">Last saved</dt><dd>{h.last_saved ? new Date(h.last_saved).toLocaleString() : '—'}{h.saved_by ? ` · ${h.saved_by}` : ''}</dd>
            <dt className="text-muted">Auto-save</dt><dd>{saveState === 'saved' ? <Badge tone="good">On · all changes saved</Badge> : saveState === 'error' ? <Badge tone="bad">Retrying</Badge> : <Badge tone="accent">Saving…</Badge>}</dd>
            <dt className="text-muted">Saved versions</dt><dd>{h.versions} <button className="text-accent ml-1" onClick={() => nav('/scenarios')}>Version history →</button></dd>
          </dl>
        </Card>
        <Card title={<span className="flex items-center gap-2"><Users size={16} className="text-accent" />Members</span>}>
          <ul className="divide-y divide-line">
            {h.members.map((m: string) => (
              <li key={m} className="flex items-center gap-3 py-2 text-sm">
                <div className="w-8 h-8 rounded-full bg-sunken border border-line flex items-center justify-center text-[12px] font-semibold">{m[0].toUpperCase()}</div>
                <span className="flex-1">{m} {m === h.you && <span className="text-muted">(you)</span>}</span>
                {h.members.length > 1 && <button className="p-1 text-muted hover:text-bad" title="Remove from household" onClick={() => setRemove(m)}><Trash2 size={14} /></button>}
              </li>))}
          </ul>
          <div className="mt-4 rounded-lg bg-sunken/70 p-3 text-[13px] text-ink2">
            <div className="font-medium text-ink mb-1">Invite your partner</div>
            <ol className="list-decimal pl-5 space-y-0.5">
              <li>Send them this app's address{h.cloudflare ? ' (they sign in with their email through Cloudflare Access; add them to your Access policy first)' : ''}.</li>
              <li>After signing in they choose <b>Join with a code</b> and enter <span className="font-mono">{h.id}</span>.</li>
              <li>You'll both see the same plan, check-ins and scenarios. Changes save automatically.</li>
            </ol>
          </div>
        </Card>
      </div>
      <Card title={<span className="flex items-center gap-2"><ShieldCheck size={16} className="text-accent" />How is my data secured?</span>}>
        <div className="grid md:grid-cols-3 gap-4 text-[13px] text-ink2">
          <div><div className="flex items-center gap-2 font-medium text-ink mb-1"><Cloud size={15} />Sign-in</div>
            {h.cloudflare ? 'You are signed in through Cloudflare Access: only the email addresses in your Access policy can reach the app.' : 'You are using the simple email sign-in meant for your home network. Put the app behind Cloudflare Access (or your VPN) before exposing it to the internet.'}</div>
          <div><div className="flex items-center gap-2 font-medium text-ink mb-1"><HardDrive size={15} />Storage</div>
            Plans are files on your own server (the NAS), never sent to a third party. Every save first makes a backup, and a daily snapshot is kept for 120 days.</div>
          <div><div className="flex items-center gap-2 font-medium text-ink mb-1"><Lock size={15} />Encryption</div>
            {h.encrypted ? 'This household is encrypted with a passphrase. The plan on disk is unreadable without it; nobody can recover it if the passphrase is lost.' : 'This household is not encrypted. Anyone with access to the server\'s files could read it. Create an encrypted household (with a passphrase) if you need that protection.'}</div>
        </div>
      </Card>
      {household?.is_admin && (
        <Card title={<span className="flex items-center gap-2"><FlaskConical size={16} className="text-warn" />Admin</span>}>
          <div className="flex flex-wrap gap-2">
            <Button onClick={async () => { const r = await api.cleanupTests(); setMsg(`Removed ${r.removed} test household${r.removed === 1 ? '' : 's'}.`); if (h.is_test) location.href = '/households' }}>Clean up my test households</Button>
            <Button onClick={() => nav('/households')}>Switch household</Button>
          </div>
        </Card>
      )}
      <Modal open={!!remove} onClose={() => setRemove(null)} title="Remove member?"
        footer={<><Button onClick={() => setRemove(null)}>Cancel</Button><Button variant="danger" onClick={async () => {
          await api.removeMember(remove!); setRemove(null); load(); if (remove === h.you) location.href = '/households' }}>Remove</Button></>}>
        <p className="text-sm text-ink2">{remove} will no longer see this household. The plan itself is not changed.</p>
      </Modal>
    </div>
  )
}
