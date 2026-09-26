import React, { useState } from 'react'
import { ArrowLeft, ArrowRight, X, HelpCircle, Check } from 'lucide-react'
import { clsx } from '../lib/format'

/** TurboTax-style full-screen flow: section progress on top, one question per screen. */
export function FlowShell({ sections, section, progress, onBack, onNext, onClose, nextLabel = 'Continue', canNext = true,
  aside, children, hideNav }: {
  sections: string[]; section: number; progress: number; onBack?: () => void; onNext?: () => void; onClose?: () => void
  nextLabel?: string; canNext?: boolean; aside?: React.ReactNode; children: React.ReactNode; hideNav?: boolean
}) {
  return (
    <div className="min-h-full flex flex-col bg-bg">
      <header className="h-14 shrink-0 flex items-center gap-4 px-4 sm:px-8 border-b border-line bg-surface">
        <div className="w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center shrink-0">
          <svg viewBox="0 0 32 32" width="18" height="18"><path d="M5 22l6-7 5 4 10-11" stroke="white" strokeWidth="3.2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </div>
        <ol className="hidden md:flex items-center gap-1 flex-1 overflow-hidden">
          {sections.map((s, i) => (
            <li key={s} className="flex items-center gap-1 text-[13px] whitespace-nowrap">
              <span className={clsx('flex items-center gap-1.5 px-2 py-1 rounded-md',
                i === section ? 'text-accent font-semibold bg-accentSoft' : i < section ? 'text-ink2' : 'text-muted')}>
                {i < section ? <Check size={13} className="text-good" /> : <span className="tnum">{i + 1}</span>}{s}
              </span>
              {i < sections.length - 1 && <span className="text-line">—</span>}
            </li>
          ))}
        </ol>
        <div className="md:hidden flex-1 text-sm font-medium">{sections[section]}</div>
        {onClose && <button onClick={onClose} className="p-2 rounded-md text-muted hover:bg-sunken" title="Save & exit"><X size={18} /></button>}
      </header>
      <div className="h-1 bg-line/60"><div className="h-1 bg-accent transition-all duration-300" style={{ width: `${Math.round(progress * 100)}%` }} /></div>
      <div className="flex-1 flex justify-center px-4 sm:px-8 py-8 sm:py-12">
        <div className={clsx('w-full flex gap-10', aside ? 'max-w-[1040px]' : 'max-w-[640px]')}>
          <div className="flex-1 min-w-0 max-w-[640px]">
            {children}
            {!hideNav && (
              <div className="flex items-center justify-between mt-10">
                {onBack ? <button onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-ink2 hover:text-ink"><ArrowLeft size={16} />Back</button> : <span />}
                {onNext && <button onClick={onNext} disabled={!canNext}
                  className="inline-flex items-center gap-2 h-11 px-6 rounded-xl bg-accent text-white font-semibold text-[15px] hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed shadow-card">
                  {nextLabel}<ArrowRight size={17} /></button>}
              </div>
            )}
          </div>
          {aside && <aside className="hidden lg:block w-[320px] shrink-0">{aside}</aside>}
        </div>
      </div>
    </div>
  )
}

export function Question({ title, subtitle, why, children }: { title: React.ReactNode; subtitle?: React.ReactNode; why?: React.ReactNode; children?: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <h1 className="text-[26px] sm:text-[30px] leading-tight font-semibold tracking-tight">{title}</h1>
      {subtitle && <p className="text-[15px] text-ink2 mt-2">{subtitle}</p>}
      {why && (
        <div className="mt-3">
          <button onClick={() => setOpen(!open)} className="inline-flex items-center gap-1.5 text-[13px] font-medium text-accent"><HelpCircle size={14} />Why we ask</button>
          {open && <p className="mt-2 text-[13.5px] text-ink2 bg-accentSoft/60 border border-accent/15 rounded-lg px-3.5 py-2.5">{why}</p>}
        </div>
      )}
      <div className="mt-7 space-y-5">{children}</div>
    </div>
  )
}

export interface Choice<T> { value: T; label: string; desc?: React.ReactNode; icon?: React.ReactNode; badge?: string }

export function ChoiceCards<T extends string | number>({ options, value, onChange, cols = 1 }:
  { options: Choice<T>[]; value: T | null | undefined; onChange: (v: T) => void; cols?: 1 | 2 | 3 }) {
  return (
    <div className={clsx('grid gap-3', cols === 2 && 'sm:grid-cols-2', cols === 3 && 'sm:grid-cols-3')}>
      {options.map(o => {
        const on = o.value === value
        return (
          <button key={String(o.value)} type="button" onClick={() => onChange(o.value)}
            className={clsx('text-left rounded-xl border-2 px-4 py-3.5 transition flex items-start gap-3 bg-surface',
              on ? 'border-accent bg-accentSoft/40' : 'border-line hover:border-accent/40')}>
            {o.icon && <span className={clsx('mt-0.5 shrink-0', on ? 'text-accent' : 'text-muted')}>{o.icon}</span>}
            <span className="flex-1 min-w-0">
              <span className="flex items-center gap-2 font-semibold text-[15px]">{o.label}
                {o.badge && <span className="text-[11px] font-medium text-accent bg-accentSoft px-1.5 py-0.5 rounded">{o.badge}</span>}</span>
              {o.desc && <span className="block text-[13px] text-ink2 mt-0.5">{o.desc}</span>}
            </span>
            <span className={clsx('w-5 h-5 rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center', on ? 'border-accent bg-accent' : 'border-line')}>
              {on && <Check size={12} className="text-white" strokeWidth={3} />}
            </span>
          </button>
        )
      })}
    </div>
  )
}

export function Chips<T extends string>({ options, values, onToggle }: { options: { value: T; label: string }[]; values: T[]; onToggle: (v: T) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => {
        const on = values.includes(o.value)
        return (
          <button key={o.value} type="button" onClick={() => onToggle(o.value)}
            className={clsx('h-9 px-3.5 rounded-full border text-sm font-medium transition',
              on ? 'bg-accent text-white border-accent' : 'bg-surface border-line text-ink2 hover:border-accent/50')}>
            {on && '✓ '}{o.label}
          </button>
        )
      })}
    </div>
  )
}

export function BigField({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[14px] font-medium mb-1.5">{label}</span>
      {children}
      {hint && <span className="block text-[12.5px] text-muted mt-1.5">{hint}</span>}
    </label>
  )
}

export function Slider({ value, min, max, step = 1, onChange, format }: { value: number; min: number; max: number; step?: number; onChange: (v: number) => void; format?: (v: number) => string }) {
  return (
    <div>
      <div className="text-[34px] font-semibold tnum tracking-tight">{format ? format(value) : value}</div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(+e.target.value)}
        className="w-full accent-[rgb(var(--accent))] mt-2" />
      <div className="flex justify-between text-[12px] text-muted"><span>{format ? format(min) : min}</span><span>{format ? format(max) : max}</span></div>
    </div>
  )
}
