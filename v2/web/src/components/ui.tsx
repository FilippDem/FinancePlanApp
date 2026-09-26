import React, { useEffect, useRef, useState } from 'react'
import { X, Info } from 'lucide-react'
import { clsx } from '../lib/format'

export function Card({ title, subtitle, action, children, className, pad = true }:
  { title?: React.ReactNode; subtitle?: React.ReactNode; action?: React.ReactNode; children?: React.ReactNode; className?: string; pad?: boolean }) {
  return (
    <section className={clsx('bg-surface rounded-xl border border-line shadow-card', className)}>
      {(title || action) && (
        <header className="flex items-start justify-between gap-3 px-5 pt-4">
          <div className="min-w-0">
            {title && <h3 className="text-[15px] font-semibold text-ink leading-6">{title}</h3>}
            {subtitle && <p className="text-[13px] text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0 flex items-center gap-2">{action}</div>}
        </header>
      )}
      <div className={clsx(pad && 'p-5', pad && (title || action) && 'pt-3')}>{children}</div>
    </section>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-muted mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; size?: 'sm' | 'md' }
export function Button({ variant = 'secondary', size = 'md', className, ...rest }: BtnProps) {
  return (
    <button
      {...rest}
      className={clsx(
        'inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap',
        size === 'sm' ? 'h-8 px-2.5 text-[13px]' : 'h-9 px-3.5 text-sm',
        variant === 'primary' && 'bg-accent text-white hover:brightness-110',
        variant === 'secondary' && 'bg-surface border border-line text-ink hover:bg-sunken',
        variant === 'ghost' && 'text-ink2 hover:bg-sunken hover:text-ink',
        variant === 'danger' && 'text-bad hover:bg-bad/10',
        className,
      )}
    />
  )
}

export function Label({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <span className="flex items-center gap-1 text-[12.5px] font-medium text-ink2 mb-1.5">
      {children}
      {hint && <span title={hint} className="text-muted cursor-help"><Info size={12} /></span>}
    </span>
  )
}

const inputCls = 'w-full h-9 rounded-lg border border-line bg-surface px-3 text-sm text-ink tnum outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 transition'

/** Numeric input that keeps its own text while typing and commits valid numbers. */
export function NumberInput({ value, onChange, prefix, suffix, step, min, max, decimals = 0, className, disabled, placeholder, big }:
  { value: number | null | undefined; onChange: (v: number) => void; prefix?: string; suffix?: string; step?: number; min?: number; max?: number;
    decimals?: number; className?: string; disabled?: boolean; placeholder?: string; big?: boolean }) {
  const fmt = (v: any) => (v === null || v === undefined || v === '' || !isFinite(v)) ? '' :
    Number(v).toLocaleString('en-US', { maximumFractionDigits: decimals, useGrouping: !!prefix })
  const [text, setText] = useState(fmt(value))
  const focused = useRef(false)
  useEffect(() => { if (!focused.current) setText(fmt(value)) }, [value])
  const commit = (t: string) => {
    const n = parseFloat(t.replace(/[,$%\s]/g, ''))
    if (!isNaN(n)) {
      let v = n
      if (min !== undefined) v = Math.max(min, v)
      if (max !== undefined) v = Math.min(max, v)
      onChange(v)
    }
  }
  return (
    <div className={clsx('relative', className)}>
      {prefix && <span className={clsx('absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none', big ? 'text-[17px] left-4' : 'text-sm')}>{prefix}</span>}
      <input
        inputMode="decimal"
        disabled={disabled}
        placeholder={placeholder}
        className={clsx(inputCls, prefix && (big ? 'pl-8' : 'pl-6'), suffix && 'pr-9', disabled && 'opacity-60', big && '!h-12 !text-[17px] !rounded-xl')}
        value={text}
        onFocus={e => { focused.current = true; setText(value === null || value === undefined ? '' : String(+Number(value).toFixed(decimals))); const el = e.currentTarget; requestAnimationFrame(() => el.select()) }}
        onBlur={() => { focused.current = false; commit(text); setText(fmt(value)) }}
        onChange={e => { setText(e.target.value); commit(e.target.value) }}
        onKeyDown={e => {
          if (e.key === 'Enter') (e.target as HTMLInputElement).blur()
          if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && step) {
            e.preventDefault()
            const cur = Number(value) || 0
            const nv = +(cur + (e.key === 'ArrowUp' ? step : -step)).toFixed(6)
            onChange(nv); setText(String(nv))
          }
        }}
      />
      {suffix && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted text-sm pointer-events-none">{suffix}</span>}
    </div>
  )
}

export const Money = (p: Omit<React.ComponentProps<typeof NumberInput>, 'prefix'>) => <NumberInput prefix="$" step={1000} {...p} />

/** Percent input. If `fraction`, the stored value is 0.05 for 5%. */
export function Percent({ value, onChange, fraction = false, decimals = 2, ...rest }:
  { value: number; onChange: (v: number) => void; fraction?: boolean; decimals?: number; min?: number; max?: number; disabled?: boolean; className?: string; big?: boolean }) {
  const shown = fraction ? +(Number(value || 0) * 100).toFixed(6) : value
  return <NumberInput value={shown} suffix="%" step={0.1} decimals={decimals}
    onChange={v => onChange(fraction ? +(v / 100).toFixed(8) : v)} {...rest} />
}

export function TextInput({ value, onChange, placeholder, className, big, autoFocus }: { value: string; onChange: (v: string) => void; placeholder?: string; className?: string; big?: boolean; autoFocus?: boolean }) {
  return <input autoFocus={autoFocus} className={clsx(inputCls, big && '!h-12 !text-[17px] !rounded-xl', className)} value={value ?? ''} placeholder={placeholder} onChange={e => onChange(e.target.value)} />
}

export function Select<T extends string | number>({ value, onChange, options, className }:
  { value: T; onChange: (v: T) => void; options: (T | { value: T; label: string })[]; className?: string }) {
  const opts = options.map(o => (typeof o === 'object' ? o : { value: o, label: String(o) }))
  return (
    <select className={clsx(inputCls, 'pr-8 appearance-none bg-no-repeat bg-[right_.6rem_center] bg-[length:14px]', className)}
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")" }}
      value={String(value)}
      onChange={e => {
        const o = opts.find(o => String(o.value) === e.target.value)
        if (o) onChange(o.value)
      }}>
      {opts.map(o => <option key={String(o.value)} value={String(o.value)}>{o.label}</option>)}
    </select>
  )
}

export function Field({ label, hint, children, className }: { label: string; hint?: string; children: React.ReactNode; className?: string }) {
  return <label className={clsx('block', className)}><Label hint={hint}>{label}</Label>{children}</label>
}

export function Toggle({ checked, onChange, label, hint }: { checked: boolean; onChange: (v: boolean) => void; label?: string; hint?: string }) {
  return (
    <label className="inline-flex items-center gap-2.5 cursor-pointer select-none">
      <button type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)}
        className={clsx('relative w-9 h-5 rounded-full transition-colors', checked ? 'bg-accent' : 'bg-line')}>
        <span className={clsx('absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform', checked && 'translate-x-4')} />
      </button>
      {label && <span className="text-sm text-ink">{label}</span>}
      {hint && <span title={hint} className="text-muted"><Info size={12} /></span>}
    </label>
  )
}

export function Segmented<T extends string>({ value, onChange, options }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[] }) {
  return (
    <div className="inline-flex p-0.5 rounded-lg bg-sunken border border-line">
      {options.map(o => (
        <button key={o.value} type="button" onClick={() => onChange(o.value)}
          className={clsx('px-3 h-7 rounded-md text-[13px] font-medium transition',
            value === o.value ? 'bg-surface text-ink shadow-card' : 'text-muted hover:text-ink')}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Tabs<T extends string>({ value, onChange, tabs }: { value: T; onChange: (v: T) => void; tabs: { value: T; label: string; count?: number }[] }) {
  return (
    <div className="flex gap-1 border-b border-line mb-5 overflow-x-auto">
      {tabs.map(t => (
        <button key={t.value} onClick={() => onChange(t.value)}
          className={clsx('px-3 pb-2.5 pt-1 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition',
            value === t.value ? 'border-accent text-ink' : 'border-transparent text-muted hover:text-ink')}>
          {t.label}{t.count !== undefined && <span className="ml-1.5 text-xs text-muted">{t.count}</span>}
        </button>
      ))}
    </div>
  )
}

export function Stat({ label, value, sub, tone, big }: { label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: 'good' | 'bad' | 'warn'; big?: boolean }) {
  return (
    <div>
      <div className="text-[12.5px] text-muted font-medium">{label}</div>
      <div className={clsx('font-semibold tracking-tight mt-1', big ? 'text-[32px] leading-9' : 'text-[22px] leading-7',
        tone === 'bad' && 'text-bad', tone === 'good' && 'text-good')}>{value}</div>
      {sub && <div className="text-[12.5px] text-muted mt-1">{sub}</div>}
    </div>
  )
}

export function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'good' | 'bad' | 'warn' | 'accent' }) {
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 h-[22px] rounded-md text-[12px] font-medium',
      tone === 'neutral' && 'bg-sunken text-ink2', tone === 'good' && 'bg-good/10 text-good',
      tone === 'bad' && 'bg-bad/10 text-bad', tone === 'warn' && 'bg-warn/10 text-warn', tone === 'accent' && 'bg-accentSoft text-accent')}>
      {children}
    </span>
  )
}

export function Drawer({ open, onClose, title, children, footer, wide }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; footer?: React.ReactNode; wide?: boolean }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    if (open) window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <aside className={clsx("absolute right-0 top-0 h-full w-full", wide ? 'max-w-[640px]' : 'max-w-[520px]', " bg-surface border-l border-line shadow-2xl flex flex-col")}>
        <header className="flex items-center justify-between px-5 h-14 border-b border-line">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-sunken text-muted"><X size={18} /></button>
        </header>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">{children}</div>
        {footer && <footer className="px-5 py-3 border-t border-line flex justify-end gap-2">{footer}</footer>}
      </aside>
    </div>
  )
}

export function Modal({ open, onClose, title, children, footer }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; footer?: React.ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-surface rounded-xl border border-line shadow-2xl w-full max-w-md">
        <header className="px-5 pt-4 pb-2 font-semibold">{title}</header>
        <div className="px-5 pb-4 space-y-3">{children}</div>
        {footer && <footer className="px-5 py-3 border-t border-line flex justify-end gap-2">{footer}</footer>}
      </div>
    </div>
  )
}

export function Empty({ icon, title, body, action }: { icon?: React.ReactNode; title: string; body?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center text-center py-10 px-4">
      {icon && <div className="w-11 h-11 rounded-full bg-accentSoft text-accent flex items-center justify-center mb-3">{icon}</div>}
      <div className="font-medium">{title}</div>
      {body && <p className="text-sm text-muted mt-1 max-w-sm">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Grid({ cols = 2, children, className }: { cols?: 2 | 3 | 4; children: React.ReactNode; className?: string }) {
  return <div className={clsx('grid gap-4', cols === 2 && 'sm:grid-cols-2', cols === 3 && 'sm:grid-cols-2 lg:grid-cols-3',
    cols === 4 && 'sm:grid-cols-2 lg:grid-cols-4', className)}>{children}</div>
}

export function Note({ children, tone = 'info' }: { children: React.ReactNode; tone?: 'info' | 'warn' }) {
  return (
    <div className={clsx('text-[13px] rounded-lg px-3.5 py-2.5 border',
      tone === 'info' ? 'bg-accentSoft/60 border-accent/20 text-ink2' : 'bg-warn/10 border-warn/30 text-ink2')}>
      {children}
    </div>
  )
}
