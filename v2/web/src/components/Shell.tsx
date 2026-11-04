import React, { useEffect, useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { HELP } from '../lib/help'
import {
  LayoutDashboard, Users, Wallet, Baby, Home, HeartPulse, SlidersHorizontal, LineChart, CalendarRange, Layers,
  Moon, Sun, LogOut, Check, Loader2, AlertCircle, ArrowLeftRight, Menu, X, ClipboardCheck, Wand2, Receipt, Palmtree, ShieldAlert, MapPin, UserCog, FlaskConical, Scale, Link2, ChevronDown, ChevronUp, HelpCircle, Target, Calculator, Monitor, Server, Sparkles,
} from 'lucide-react'
import { fiYear } from '../lib/whatifs'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { clsx, money } from '../lib/format'
import { buildAlerts } from '../pages/Dashboard'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/decisions', label: 'Decision playground', icon: Sparkles },
  { to: '/goals', label: 'Goals', icon: Target },
  { to: '/checkins', label: 'Check-ins', icon: ClipboardCheck, badge: true },
  { to: '/actuals', label: 'Actuals', icon: Receipt },
  { to: '/accounts', label: 'Linked accounts', icon: Link2 },
  { group: 'Plan' },
  { to: '/people', label: 'People & income', icon: Users },
  { to: '/spending', label: 'Spending', icon: Wallet },
  { to: '/kids', label: 'Kids', icon: Baby },
  { to: '/homes', label: 'Homes', icon: Home },
  { to: '/healthcare', label: 'Healthcare', icon: HeartPulse },
  { to: '/locations', label: 'Where you live', icon: MapPin },
  { to: '/ownership', label: 'Who owns what', icon: Scale },
  { to: '/assumptions', label: 'Assumptions', icon: SlidersHorizontal },
  { group: 'Analyze' },
  { to: '/projections', label: 'Projections', icon: LineChart },
  { to: '/retirement', label: 'Retirement', icon: Palmtree },
  { to: '/taxes', label: 'Tax planning', icon: Calculator },
  { to: '/stress', label: 'Stress tests', icon: ShieldAlert },
  { to: '/timeline', label: 'Life timeline & editor', icon: CalendarRange },
  { to: '/scenarios', label: 'Scenarios', icon: Layers },
] as const

export function useDarkMode(): [boolean, (v: boolean) => void] {
  const [dark, setDark] = useState(() => {
    try { const s = localStorage.getItem('fp_theme'); if (s) return s === 'dark' } catch { /* */ }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  })
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('fp_theme', dark ? 'dark' : 'light') } catch { /* */ }
  }, [dark])
  return [dark, setDark]
}

function SaveIndicator({ onDark }: { onDark?: boolean }) {
  const { saveState, lastSaved } = usePlan()
  const time = lastSaved ? new Date(lastSaved).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : ''
  return (
    <span className={clsx('flex items-center gap-1.5 text-[12.5px]', onDark ? 'text-white/85' : 'text-muted')}>
      {saveState === 'saved' && <><Check size={14} className={onDark ? 'text-emerald-300' : 'text-good'} /> Saved {time && `· ${time}`}</>}
      {(saveState === 'dirty' || saveState === 'saving') && <><Loader2 size={14} className="animate-spin" /> Saving…</>}
      {saveState === 'error' && <><AlertCircle size={14} className={onDark ? 'text-red-200' : 'text-bad'} /> Not saved — retrying on next change</>}
    </span>
  )
}

/** When the planner runs inside the desktop window (launcher/desktop.py), pywebview exposes a small API:
 *  where the window is connected (this computer or the NAS) and a way to change it. Absent in a normal browser. */
export function useDesktop(): { mode: 'local' | 'nas'; nas_url: string; url: string } | null {
  const [d, setD] = useState<any>(null)
  useEffect(() => {
    const w = window as any
    const load = () => { try { w.pywebview?.api?.get_state?.().then(setD).catch(() => {}) } catch { /* */ } }
    if (w.pywebview?.api) load()
    window.addEventListener('pywebviewready', load)
    return () => window.removeEventListener('pywebviewready', load)
  }, [])
  return d
}

function DesktopConnection() {
  const d = useDesktop()
  if (!d) return null
  const nas = d.mode === 'nas'
  let host = ''
  try { host = nas ? new URL(d.nas_url).host : '' } catch { /* */ }
  return (
    <button onClick={() => (window as any).pywebview?.api?.choose_connection()}
      title={nas ? `Shared plan on ${host || 'the NAS'}. Click to change where this window gets your plan from.` : 'Plans on this computer. Click to change where this window gets your plan from.'}
      className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
      {nas ? <Server size={17} /> : <Monitor size={17} />}
      <span className="truncate">{nas ? 'Shared plan (NAS)' : 'This computer'}</span>
      <span className="ml-auto text-[11.5px] text-muted">Change</span>
    </button>
  )
}

export function Shell({ me, children }: { me: any; children: React.ReactNode }) {
  const [dark, setDark] = useDarkMode()
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const { household, ck } = usePlan()
  const initials = (me.email || '?').slice(0, 1).toUpperCase()

  const sidebar = (
    <nav className="flex flex-col h-full">
      <div className="flex items-center gap-2.5 px-4 h-16">
        <div className="w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center">
          <svg viewBox="0 0 32 32" width="18" height="18"><path d="M5 22l6-7 5 4 10-11" stroke="white" strokeWidth="3.2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </div>
        <div className="leading-tight">
          <div className="font-semibold text-[14px]">Financial Planner</div>
          <div className="text-[11.5px] text-muted truncate max-w-[150px]">{household?.name}</div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-2.5 pb-4">
        <FICard onOpen={() => { nav('/decisions'); setOpen(false) }} />
        {NAV.map((n: any, i) => n.group
          ? <div key={i} className="px-2.5 pt-5 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted">{n.group}</div>
          : (
            <NavLink key={n.to} to={n.to} end={n.end} onClick={() => setOpen(false)}
              className={({ isActive }) => clsx('flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] font-medium transition-colors',
                isActive ? 'bg-accentSoft text-accent' : 'text-ink2 hover:bg-sunken hover:text-ink')}>
              <n.icon size={17} strokeWidth={1.9} />{n.label}
              {n.badge && ck?.due && <span className="ml-auto text-[11px] font-semibold bg-accent text-white rounded-full px-1.5 py-0.5">Due</span>}
            </NavLink>
          ))}
        <QuickSummary />
      </div>
      <div className="border-t border-line p-2.5 space-y-0.5">
        <DesktopConnection />
        <button onClick={() => setDark(!dark)} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          {dark ? <Sun size={17} /> : <Moon size={17} />}{dark ? 'Light mode' : 'Dark mode'}
        </button>
        <button onClick={() => nav('/setup')} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          <Wand2 size={17} />Guided setup
        </button>
        <button onClick={() => { nav('/household'); setOpen(false) }} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          <UserCog size={17} />Household & members
        </button>
        <button onClick={() => nav('/households')} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          <ArrowLeftRight size={17} />Switch household
        </button>
        <div className="flex items-center gap-2.5 px-2.5 pt-2">
          <div className="w-7 h-7 rounded-full bg-sunken border border-line text-[12px] font-semibold flex items-center justify-center">{initials}</div>
          <div className="text-[12.5px] text-ink2 truncate flex-1">{me.email}</div>
          {!me.cloudflare && (
            <button title="Sign out" onClick={async () => { await api.logout(); location.href = '/' }} className="p-1.5 rounded-md hover:bg-sunken text-muted"><LogOut size={15} /></button>
          )}
        </div>
      </div>
    </nav>
  )

  return (
    <div className="min-h-full flex">
      <aside className="hidden lg:block w-[232px] shrink-0 border-r border-line bg-surface fixed inset-y-0">{sidebar}</aside>
      {open && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-[260px] bg-surface border-r border-line">{sidebar}</aside>
        </div>
      )}
      <div className="flex-1 lg:ml-[232px] min-w-0">
        <header className="sticky top-0 z-30 h-14 flex items-center justify-between gap-3 px-4 sm:px-8 text-white shadow-md bg-gradient-to-r from-[#1d4ed8] via-[#2563eb] to-[#4f46e5]">
          <button className="lg:hidden p-2 -ml-2 rounded-md hover:bg-white/15" onClick={() => setOpen(true)}>{open ? <X size={18} /> : <Menu size={18} />}</button>
          <div className="min-w-0 leading-tight">
            <div className="font-semibold text-[15px] truncate">{household?.name || 'Financial Planner'}</div>
            <div className="text-[11.5px] text-white/75 truncate hidden sm:block">Weigh your options · stack decisions · see your future</div>
          </div>
          <NavLink to="/decisions" className={({ isActive }) => clsx('hidden sm:inline-flex items-center gap-1.5 h-7 px-3 rounded-full text-[12.5px] font-semibold shadow-sm transition-colors',
            isActive ? 'bg-white text-[#1d4ed8]' : 'bg-amber-400 text-amber-950 hover:bg-amber-300')}><Sparkles size={13} />Decision playground</NavLink>
          <div className="flex-1" />
          {household?.is_test && <span className="flex items-center gap-1.5 text-[12.5px] font-medium text-amber-950 bg-amber-300 rounded-md px-2 h-7">
            <FlaskConical size={14} />Test mode<button className="underline ml-1" title="Delete this test household and go back to your own"
              onClick={async () => { try { const r = await api.exitTest(); location.href = r.id ? '/' : '/households' } catch { nav('/households') } }}>Exit</button></span>}
          <HelpButton onDark />
          <SaveIndicator onDark />
        </header>
        <main className="px-4 sm:px-8 py-6 max-w-[1280px] mx-auto">{children}</main>
      </div>
    </div>
  )
}


/** v0.8 sidebar quick summary: key numbers, location and alert counts. */
function QuickSummary() {
  const { plan, proj, mc } = usePlan()
  const [open, setOpen] = useState(() => { try { return localStorage.getItem('fp_qs') !== '0' } catch { return true } })
  useEffect(() => { try { localStorage.setItem('fp_qs', open ? '1' : '0') } catch { /* */ } }, [open])
  if (!proj) return null
  const r0 = proj.rows[0]
  const alerts = buildAlerts(proj, mc, plan)
  const bad = alerts.filter(a => a.tone === 'bad').length, warn = alerts.filter(a => a.tone === 'warn').length
  const loc = (plan.state_timeline || []).filter((e: any) => e.year <= plan.current_year).pop() || plan.state_timeline?.[0]
  return (
    <div className="mt-5 mx-1 rounded-lg border border-line bg-sunken/50 text-[12.5px]">
      <button className="w-full flex items-center justify-between px-2.5 h-8 font-semibold text-[11px] uppercase tracking-wider text-muted" onClick={() => setOpen(!open)}>
        Quick summary {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}</button>
      {open && <dl className="grid grid-cols-[1fr_auto] gap-y-1 px-2.5 pb-2.5">
        <dt className="text-ink2">Net worth</dt><dd className="tnum text-right">{money(proj.summary.net_worth_now)}</dd>
        <dt className="text-ink2">Income</dt><dd className="tnum text-right">{money(r0.total_income)}</dd>
        <dt className="text-ink2">Spending</dt><dd className="tnum text-right">{money(r0.total_expenses)}</dd>
        <dt className="text-ink2">Kids · homes</dt><dd className="tnum text-right">{(plan.children_list || []).length} · {(plan.houses || []).length}</dd>
        <dt className="text-ink2">Where</dt><dd className="text-right truncate max-w-[110px]" title={`${loc?.state} · ${loc?.spending_strategy}`}>{loc?.state}</dd>
        <dt className="text-ink2">Alerts</dt><dd className="text-right">
          {bad > 0 && <span className="text-bad font-medium">{bad} critical</span>}{bad > 0 && warn > 0 && ' · '}
          {warn > 0 && <span className="text-warn font-medium">{warn} warn</span>}{!bad && !warn && <span className="text-good">none</span>}</dd>
      </dl>}
    </div>
  )
}


function HelpButton({ onDark }: { onDark?: boolean }) {
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const h = HELP[loc.pathname]
  useEffect(() => setOpen(false), [loc.pathname])
  if (!h) return null
  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className={clsx('flex items-center gap-1 text-[12.5px] px-2 h-8 rounded-md', onDark ? 'text-white/90 hover:bg-white/15' : 'text-ink2 hover:text-ink hover:bg-sunken')} aria-label="Help for this page">
        <HelpCircle size={15} />Help</button>
      {open && <>
        <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
        <div className="absolute right-0 top-9 z-50 w-[340px] rounded-xl border border-line bg-surface text-ink shadow-2xl p-4 text-sm">
          <div className="font-semibold mb-1">About this page</div>
          <p className="text-ink2">{h.what}</p>
          {h.tips.length > 0 && <ul className="mt-2 space-y-1 list-disc pl-4 text-ink2">{h.tips.map(t => <li key={t}>{t}</li>)}</ul>}
        </div>
      </>}
    </div>
  )
}


/** FinP4l-style "FI age" card: when work becomes optional, plus today's net worth, assets and debts. */
function FICard({ onOpen }: { onOpen: () => void }) {
  const { plan, proj } = usePlan()
  if (!proj) return null
  const fi = fiYear(proj.rows)
  const r0 = proj.rows[0]
  const age = fi != null ? plan.parentX_age + (fi - plan.current_year) : null
  const debts = (r0.mortgage_balance || 0) + (r0.consumer_debt || 0) + (r0.debt_balance || 0)
  return (
    <button onClick={onOpen} title="When your savings could cover 25× a year of spending. Open the decision playground to change it."
      className="w-full mt-1 mb-3 rounded-xl border border-line bg-gradient-to-br from-accentSoft to-surface px-3 py-2.5 text-left hover:border-accent/50">
      <div className="text-[10.5px] font-semibold uppercase tracking-wider text-muted">Work optional at</div>
      <div className="flex items-baseline gap-1.5">
        <span className={clsx('text-[26px] font-bold tnum leading-tight', age == null ? 'text-muted' : 'text-accent')}>{age ?? '—'}</span>
        <span className="text-[12px] text-ink2">{fi != null ? (fi <= plan.current_year ? 'already there' : `in ${fi}`) : 'not reached'}</span>
      </div>
      <div className="grid grid-cols-3 gap-1 mt-1.5 text-[11px]">
        <div><div className="text-muted">Net worth</div><div className="tnum font-semibold">{money(proj.summary.net_worth_now)}</div></div>
        <div><div className="text-muted">Investable</div><div className="tnum font-semibold text-good">{money(r0.investable)}</div></div>
        <div><div className="text-muted">Debts</div><div className="tnum font-semibold text-bad">{money(debts)}</div></div>
      </div>
    </button>)
}
