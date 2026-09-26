import React, { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Wallet, Baby, Home, HeartPulse, SlidersHorizontal, LineChart, CalendarRange, Layers,
  Moon, Sun, LogOut, Check, Loader2, AlertCircle, ArrowLeftRight, Menu, X, ClipboardCheck, Wand2, Receipt, Palmtree, ShieldAlert,
} from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { clsx } from '../lib/format'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/checkins', label: 'Check-ins', icon: ClipboardCheck, badge: true },
  { to: '/actuals', label: 'Actuals', icon: Receipt },
  { group: 'Plan' },
  { to: '/people', label: 'People & income', icon: Users },
  { to: '/spending', label: 'Spending', icon: Wallet },
  { to: '/kids', label: 'Kids', icon: Baby },
  { to: '/homes', label: 'Homes', icon: Home },
  { to: '/healthcare', label: 'Healthcare', icon: HeartPulse },
  { to: '/assumptions', label: 'Assumptions', icon: SlidersHorizontal },
  { group: 'Analyze' },
  { to: '/projections', label: 'Projections', icon: LineChart },
  { to: '/retirement', label: 'Retirement', icon: Palmtree },
  { to: '/stress', label: 'Stress tests', icon: ShieldAlert },
  { to: '/timeline', label: 'Life timeline', icon: CalendarRange },
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

function SaveIndicator() {
  const { saveState, lastSaved } = usePlan()
  const time = lastSaved ? new Date(lastSaved).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : ''
  return (
    <span className="flex items-center gap-1.5 text-[12.5px] text-muted">
      {saveState === 'saved' && <><Check size={14} className="text-good" /> Saved {time && `· ${time}`}</>}
      {(saveState === 'dirty' || saveState === 'saving') && <><Loader2 size={14} className="animate-spin" /> Saving…</>}
      {saveState === 'error' && <><AlertCircle size={14} className="text-bad" /> Not saved — retrying on next change</>}
    </span>
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
      </div>
      <div className="border-t border-line p-2.5 space-y-0.5">
        <button onClick={() => setDark(!dark)} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          {dark ? <Sun size={17} /> : <Moon size={17} />}{dark ? 'Light mode' : 'Dark mode'}
        </button>
        <button onClick={() => nav('/setup')} className="w-full flex items-center gap-2.5 px-2.5 h-9 rounded-lg text-[14px] text-ink2 hover:bg-sunken">
          <Wand2 size={17} />Guided setup
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
        <header className="sticky top-0 z-30 h-14 flex items-center justify-between gap-3 px-4 sm:px-8 bg-bg/85 backdrop-blur border-b border-line/60">
          <button className="lg:hidden p-2 -ml-2 rounded-md hover:bg-sunken" onClick={() => setOpen(true)}>{open ? <X size={18} /> : <Menu size={18} />}</button>
          <div className="flex-1" />
          <SaveIndicator />
        </header>
        <main className="px-4 sm:px-8 py-6 max-w-[1280px] mx-auto">{children}</main>
      </div>
    </div>
  )
}
