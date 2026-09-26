import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CalendarPlus, Zap, ClipboardCheck, Trash2, BellRing, CheckCircle2, ArrowRight, Mail, Receipt } from 'lucide-react'
import { ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Scatter } from 'recharts'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { money, pct, axisMoney } from '../lib/format'
import { Card, PageHeader, Button, Select, Badge, Empty, Note, Toggle } from '../components/ui'
import { S } from '../components/charts'
import { STATUS_META } from './CheckinFlow'

const CADENCES = [{ value: 'quarterly', label: 'Every quarter' }, { value: 'semiannual', label: 'Twice a year' },
  { value: 'annual', label: 'Once a year' }, { value: 'off', label: 'Off (manual only)' }]
const CHANGE_LINKS: Record<string, [string, string]> = {
  new_job: ['Update income', '/people'], lost_job: ['Update income', '/people'], baby: ['Add a child', '/kids'], moved: ['Update where you live', '/assumptions'],
  home: ['Update homes', '/homes'], purchase: ['Add the purchase', '/spending'], health: ['Update healthcare', '/healthcare'],
}

export function StatusBadge({ status }: { status: string }) {
  const m = STATUS_META[status]
  return <Badge tone={m?.tone === 'accent' ? 'accent' : m?.tone ?? 'neutral'}>{m?.label ?? status}</Badge>
}

export function DueBanner() {
  const { ck, refreshCheckins } = usePlan()
  const nav = useNavigate()
  if (!ck?.due) return null
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-accent/30 bg-accentSoft/70 px-5 py-3.5">
      <BellRing className="text-accent" size={20} />
      <div className="flex-1 min-w-[200px]"><div className="font-medium">Your {ck.period.replace('-', ' ')} check-in is due</div>
        <div className="text-sm text-ink2">5 minutes to update balances and see if you're on track.</div></div>
      <Button variant="primary" onClick={() => nav('/checkin')}>Start check-in<ArrowRight size={15} /></Button>
      <Button variant="ghost" onClick={async () => { await api.checkinSettings({ snooze_days: 14 }); refreshCheckins() }}>Remind me in 2 weeks</Button>
    </div>
  )
}

export function CheckinStrip() {
  const { ck } = usePlan()
  const nav = useNavigate()
  if (!ck || ck.due) return null
  const items: any[] = ck.checkins || []
  const lastScored = [...items].reverse().find(c => c.status !== 'baseline')
  const last = items[items.length - 1]
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-line bg-surface px-5 py-3 text-sm">
      <ClipboardCheck size={17} className="text-accent" />
      {lastScored ? <span className="flex items-center gap-2">Last check-in <StatusBadge status={lastScored.status} />
        <span className="text-muted">{Math.round(lastScored.percentile)}th percentile · {new Date(lastScored.date + 'T12:00:00').toLocaleDateString()}</span></span>
        : last ? <span>Starting point recorded {new Date(last.date + 'T12:00:00').toLocaleDateString()}</span> : <span>No check-ins yet</span>}
      {ck.settings?.cadence !== 'off' && ck.settings?.next_due && <span className="text-muted">Next: {new Date(ck.settings.next_due + 'T12:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>}
      <span className="flex-1" />
      <Button size="sm" variant="ghost" onClick={() => nav('/checkin?mode=quick')}><Zap size={14} />Quick update</Button>
      <Button size="sm" onClick={() => nav('/checkins')}>Check-ins<ArrowRight size={13} /></Button>
    </div>
  )
}

export default function Checkins() {
  const { ck, refreshCheckins } = usePlan()
  const nav = useNavigate()
  const [params, setParams] = useSearchParams()
  const [confirmDel, setConfirmDel] = useState<string | null>(null)
  const [notify, setNotify] = useState<any>(null)
  const [mailMsg, setMailMsg] = useState('')
  useEffect(() => { api.notifyStatus().then(setNotify).catch(() => {}) }, [])
  const items: any[] = ck?.checkins || []
  const lastScored = [...items].reverse().find(c => c.status !== 'baseline')
  const last = items[items.length - 1]
  const done = params.get('done') === '1'
  const changes = (params.get('changes') || '').split(',').filter(c => CHANGE_LINKS[c])

  const data = useMemo(() => items.filter(c => c.totals).map(c => ({
    t: new Date(c.date + 'T12:00:00').getTime(),
    actual: c.totals.investable,
    expected: c.expected?.investable ?? c.totals.investable,
    band: c.expected?.p25 !== undefined ? [c.expected.p25, c.expected.p75] : [c.totals.investable, c.totals.investable],
  })), [items])

  return (
    <div className="space-y-5">
      <PageHeader title="Check-ins" subtitle="Keep the plan true to life: update balances, see if you're on track, roll forward"
        actions={<>
          <Button onClick={() => nav('/checkin?mode=quick')}><Zap size={15} />Quick update</Button>
          <Button variant="primary" onClick={() => nav('/checkin')}><ClipboardCheck size={15} />Start check-in</Button>
        </>} />
      {done && (
        <div className="rounded-xl border border-good/30 bg-good/10 px-5 py-3.5">
          <div className="flex items-center gap-2 font-medium"><CheckCircle2 className="text-good" size={18} />Check-in saved</div>
          {changes.length > 0 && <div className="flex flex-wrap gap-2 mt-2.5">{[...new Set(changes.map(c => CHANGE_LINKS[c][1]))].map(to => {
            const c = changes.find(x => CHANGE_LINKS[x][1] === to)!
            return <Button key={to} size="sm" onClick={() => nav(to)}>{CHANGE_LINKS[c][0]}<ArrowRight size={13} /></Button>
          })}</div>}
          {params.get('year_end') === '1' || new Date().getMonth() >= 9 ? <div className="mt-2.5"><Button size="sm" onClick={() => nav('/actuals')}><Receipt size={13} />Log this year's income & spending</Button></div> : null}
          <button className="text-[12.5px] text-muted mt-2" onClick={() => setParams({})}>Dismiss</button>
        </div>
      )}
      <DueBanner />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Latest status">
          {lastScored ? <>
            <div className="flex items-center gap-2"><StatusBadge status={lastScored.status} /><span className="text-sm text-muted">{new Date(lastScored.date + 'T12:00:00').toLocaleDateString()}</span></div>
            <div className="text-[28px] font-semibold tracking-tight mt-2 tnum">{Math.round(lastScored.percentile)}<span className="text-base text-muted font-normal">th percentile</span></div>
            <p className="text-sm text-ink2">Savings {money(lastScored.totals.investable)} vs {money(lastScored.expected?.investable)} expected
              ({money(lastScored.totals.investable - (lastScored.expected?.investable ?? 0), { sign: true })}).</p>
          </> : <p className="text-sm text-muted">No scored check-ins yet. {last?.status === 'baseline' ? 'Your starting point is recorded; the first check-in compares against it.' : ''}</p>}
        </Card>
        <Card title="Next check-in">
          {ck?.settings?.cadence === 'off' ? <p className="text-sm text-muted">Scheduled check-ins are off. You can still check in any time.</p> : <>
            <div className="text-[22px] font-semibold">{ck?.settings?.next_due ? new Date(ck.settings.next_due + 'T12:00:00').toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' }) : '—'}</div>
            <p className="text-sm text-muted mt-0.5">{ck?.due ? 'Due now' : 'We\'ll remind you here when it\'s due.'}</p>
          </>}
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <div className="w-44"><Select value={ck?.settings?.cadence || 'quarterly'} options={CADENCES} onChange={async v => { await api.checkinSettings({ cadence: v }); refreshCheckins() }} /></div>
            {ck?.settings?.cadence !== 'off' && <a href="/api/checkins/calendar.ics" className="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-line text-sm font-medium hover:bg-sunken"><CalendarPlus size={15} />Add to calendar</a>}
          </div>
          {ck?.settings?.cadence !== 'off' && (
            <div className="mt-4 pt-3 border-t border-line">
              <Toggle checked={!!ck?.settings?.email_reminders} label="Email reminders"
                hint="Emails everyone in the household when a check-in is due, plus one follow-up a week later"
                onChange={async v => { await api.checkinSettings({ email_reminders: v }); refreshCheckins() }} />
              {notify && !notify.configured && <p className="text-[12px] text-muted mt-1.5">Email isn't set up on the server yet (SMTP settings in docker-compose.yml). Until then, use Add to calendar.</p>}
              {notify?.configured && ck?.settings?.email_reminders && (
                <button className="mt-1.5 text-[12.5px] text-accent font-medium inline-flex items-center gap-1" onClick={async () => {
                  try { const r = await api.testEmail(); setMailMsg(`Test email sent to ${r.to}`) } catch (e: any) { setMailMsg(e.message) }
                  setTimeout(() => setMailMsg(''), 4000)
                }}><Mail size={13} />Send me a test email</button>)}
              {mailMsg && <p className="text-[12px] text-ink2 mt-1">{mailMsg}</p>}
            </div>
          )}
        </Card>
        <Card title="History">
          <div className="text-[28px] font-semibold tnum">{items.length}</div>
          <p className="text-sm text-muted">check-ins{items.length ? ` since ${new Date(items[0].date + 'T12:00:00').toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}` : ''}</p>
          {items.length >= 2 && <p className="text-sm text-ink2 mt-2">Savings {money(items[items.length - 1].totals.investable - items[0].totals.investable, { sign: true })} since the first one.</p>}
        </Card>
      </div>

      <Card title="Actual vs plan over time" subtitle="Dots are your check-ins; the band is the range the plan expected at each one (25th–75th percentile)">
        {data.length < 1 ? <Empty title="No check-ins yet" body="Finish guided setup or run a check-in to start the history." /> : (
          <>
            <div className="flex flex-wrap gap-4 text-[12.5px] text-ink2 mb-2">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: S[0] }} />Your savings</span>
              <span className="flex items-center gap-1.5"><span className="w-3.5 h-[2px]" style={{ background: S[1] }} />Plan expected</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm opacity-40" style={{ background: S[1] }} />Expected range</span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--grid)" />
                <XAxis dataKey="t" type="number" scale="time" domain={['dataMin - 2592000000', 'dataMax + 2592000000']} tickLine={false} axisLine={false}
                  tickFormatter={v => new Date(v).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })} />
                <YAxis tickLine={false} axisLine={false} tickFormatter={axisMoney} width={56} domain={['auto', 'auto']} />
                <Tooltip labelFormatter={v => new Date(v as number).toLocaleDateString()} formatter={(v: any, n: any) => [Array.isArray(v) ? `${money(v[0])} – ${money(v[1])}` : money(v), n]}
                  contentStyle={{ background: 'rgb(var(--surface))', border: '1px solid rgb(var(--line))', borderRadius: 8, fontSize: 12 }} />
                <Area dataKey="band" name="Expected range" stroke="none" fill={S[1]} fillOpacity={0.15} isAnimationActive={false} />
                <Line dataKey="expected" name="Plan expected" stroke={S[1]} strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line dataKey="actual" name="Your savings" stroke={S[0]} strokeWidth={2} dot={{ r: 5, fill: S[0], stroke: 'var(--chart-surface)', strokeWidth: 2 }} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </>
        )}
      </Card>

      {items.length > 0 && (
        <Card title="All check-ins" pad={false}>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[12px] text-muted border-b border-line">
              <th className="px-5 py-2 font-medium">Date</th><th className="font-medium">Type</th><th className="font-medium text-right">Savings</th>
              <th className="font-medium text-right">Expected</th><th className="font-medium text-right">Net worth</th><th className="font-medium pl-4">Status</th>
              <th className="font-medium">Plan updated</th><th className="font-medium">By</th><th className="w-10" /></tr></thead>
            <tbody>
              {[...items].reverse().map(c => (
                <tr key={c.id} className="border-b border-line last:border-0" title={c.notes || ''}>
                  <td className="px-5 py-2.5 tnum">{new Date(c.date + 'T12:00:00').toLocaleDateString()}<div className="text-[11.5px] text-muted">{c.period}</div></td>
                  <td className="capitalize">{c.kind}</td>
                  <td className="text-right tnum font-medium">{money(c.totals?.investable)}</td>
                  <td className="text-right tnum text-ink2">{money(c.expected?.investable)}</td>
                  <td className="text-right tnum">{money(c.totals?.net_worth)}</td>
                  <td className="pl-4"><StatusBadge status={c.status} />{c.percentile !== undefined && c.status !== 'baseline' && <span className="text-[12px] text-muted ml-1.5">{Math.round(c.percentile)}th</span>}</td>
                  <td>{c.applied_to_plan ? <span className="text-good">Yes</span> : <span className="text-muted">No</span>}
                    {c.success_rate_after != null && <span className="text-[12px] text-muted ml-1.5">→ {pct(c.success_rate_after, 0)} success</span>}</td>
                  <td className="text-[12.5px] text-muted truncate max-w-[140px]">{(c.entered_by || '').split('@')[0]}</td>
                  <td className="pr-3">{confirmDel === c.id
                    ? <button className="text-[12px] text-bad font-medium" onClick={async () => { await api.deleteCheckin(c.id); setConfirmDel(null); refreshCheckins() }}>Delete?</button>
                    : <button className="p-1 text-muted hover:text-bad" onClick={() => setConfirmDel(c.id)}><Trash2 size={14} /></button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      <Note>How scoring works: at each check-in we compare your savings with the range of outcomes the plan's Monte Carlo simulation expected for that date. The 25th–75th percentile counts as on track. See docs/CHECKINS.md for the full scheme.</Note>
    </div>
  )
}
