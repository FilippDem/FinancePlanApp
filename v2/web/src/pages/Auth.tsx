import React, { useState } from 'react'
import { Lock, Plus, LogIn, FlaskConical, Home } from 'lucide-react'
import { api } from '../lib/api'
import { Button, Card, Field, TextInput, Badge } from '../components/ui'
import { useDarkMode } from '../components/Shell'

function Brand() {
  return (
    <div className="flex flex-col items-center mb-7">
      <div className="w-12 h-12 rounded-xl bg-accent text-white flex items-center justify-center mb-3 shadow-card">
        <svg viewBox="0 0 32 32" width="26" height="26"><path d="M5 22l6-7 5 4 10-11" stroke="white" strokeWidth="3.2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
      <h1 className="text-2xl font-semibold tracking-tight">Financial Planning Suite</h1>
      <p className="text-sm text-muted mt-1">Lifetime planning for your household</p>
    </div>
  )
}

export function Login({ onDone }: { onDone: () => void }) {
  useDarkMode()
  const [email, setEmail] = useState('')
  const [err, setErr] = useState('')
  return (
    <div className="min-h-full flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <Brand />
        <Card>
          <form className="space-y-4" onSubmit={async e => {
            e.preventDefault()
            try { await api.login(email); onDone() } catch (x: any) { setErr(x.message) }
          }}>
            <Field label="Email"><TextInput value={email} onChange={setEmail} placeholder="you@example.com" /></Field>
            {err && <p className="text-sm text-bad">{err}</p>}
            <Button variant="primary" className="w-full" type="submit">Continue</Button>
          </form>
        </Card>
        <p className="text-xs text-muted text-center mt-4">On your NAS, sign-in happens through Cloudflare Access automatically.</p>
      </div>
    </div>
  )
}

export function Households({ me, onDone }: { me: any; onDone: () => void }) {
  useDarkMode()
  const [name, setName] = useState('')
  const [pass, setPass] = useState('')
  const [joinId, setJoinId] = useState('')
  const [unlock, setUnlock] = useState<{ id: string; pass: string } | null>(null)
  const [err, setErr] = useState('')
  const run = async (f: () => Promise<any>) => { setErr(''); try { await f(); onDone() } catch (x: any) { setErr(x.message) } }

  return (
    <div className="min-h-full flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <Brand />
        <p className="text-center text-sm text-muted -mt-4 mb-5">Signed in as <b className="text-ink">{me.email}</b></p>
        {err && <p className="text-sm text-bad mb-3 text-center">{err}</p>}
        {me.households?.length > 0 && (
          <Card title="Your households" className="mb-4" pad={false}>
            <ul className="divide-y divide-line">
              {me.households.map((h: any) => (
                <li key={h.id} className="flex items-center gap-3 px-5 py-3">
                  <div className="w-9 h-9 rounded-lg bg-accentSoft text-accent flex items-center justify-center"><Home size={17} /></div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{h.name} {h.is_test && <Badge tone="warn">test</Badge>}</div>
                    <div className="text-xs text-muted truncate">{h.members.join(', ')} · code <span className="font-mono">{h.id}</span></div>
                  </div>
                  {h.encrypted && unlock?.id === h.id ? (
                    <div className="flex gap-2">
                      <input type="password" autoFocus className="h-8 w-32 rounded-lg border border-line bg-surface px-2 text-sm"
                        placeholder="Passphrase" value={unlock!.pass} onChange={e => setUnlock({ id: h.id, pass: e.target.value })} />
                      <Button size="sm" variant="primary" onClick={() => run(() => api.selectHousehold(h.id, unlock!.pass))}>Unlock</Button>
                    </div>
                  ) : (
                    <Button size="sm" variant="primary" onClick={() => h.encrypted ? setUnlock({ id: h.id, pass: '' }) : run(() => api.selectHousehold(h.id))}>
                      {h.encrypted && <Lock size={13} />}Open
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          </Card>
        )}
        <div className="grid sm:grid-cols-2 gap-4">
          <Card title="New household">
            <div className="space-y-3">
              <TextInput value={name} onChange={setName} placeholder="e.g. Filipp & Erin" />
              <input type="password" className="w-full h-9 rounded-lg border border-line bg-surface px-3 text-sm" placeholder="Passphrase (optional, encrypts plan)"
                value={pass} onChange={e => setPass(e.target.value)} />
              <Button variant="primary" className="w-full" onClick={() => run(() => api.createHousehold(name || 'My Household', pass || undefined))}><Plus size={15} />Create</Button>
            </div>
          </Card>
          <Card title="Join with a code">
            <div className="space-y-3">
              <TextInput value={joinId} onChange={setJoinId} placeholder="Household code" />
              <p className="text-xs text-muted">Ask your partner for the 8-character code shown in their household list.</p>
              <Button className="w-full" onClick={() => run(() => api.joinHousehold(joinId))}><LogIn size={15} />Join</Button>
            </div>
          </Card>
        </div>
        {me.is_admin && (
          <div className="text-center mt-4">
            <Button variant="ghost" size="sm" onClick={() => run(() => api.createTestHousehold())}><FlaskConical size={14} />Test as a new user (isolated)</Button>
          </div>
        )}
      </div>
    </div>
  )
}
