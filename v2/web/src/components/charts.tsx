import React from 'react'
import {
  ResponsiveContainer, ComposedChart, Area, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from 'recharts'
import { axisMoney, money } from '../lib/format'

export const S = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s6)', 'var(--s7)', 'var(--s8)']

const axisProps = { tickLine: false, axisLine: false, stroke: 'var(--axis)', fontSize: 11 }

function TipBox({ active, payload, label, title, hide = [] as string[] }: any) {
  if (!active || !payload?.length) return null
  const rows = payload.filter((p: any) => !hide.includes(p.dataKey) && p.value !== undefined && p.value !== null)
  return (
    <div className="bg-surface border border-line rounded-lg shadow-lg px-3 py-2 text-[12.5px] min-w-[180px]">
      <div className="font-semibold mb-1">{title ? title(label, payload) : label}</div>
      {rows.map((p: any) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4 py-0.5">
          <span className="flex items-center gap-1.5 text-ink2">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || p.stroke || p.fill }} />{p.name}
          </span>
          <span className="tnum font-medium text-ink">
            {Array.isArray(p.value) ? `${money(p.value[0])} – ${money(p.value[1])}` : money(p.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

function LegendRow({ items }: { items: { label: string; color: string; kind?: 'line' | 'box' | 'band' }[] }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12.5px] text-ink2 mb-2">
      {items.map(i => (
        <span key={i.label} className="flex items-center gap-1.5">
          {i.kind === 'line'
            ? <span className="w-3.5 h-[2px] rounded" style={{ background: i.color }} />
            : <span className="w-2.5 h-2.5 rounded-sm" style={{ background: i.color, opacity: i.kind === 'band' ? 0.35 : 1 }} />}
          {i.label}
        </span>
      ))}
    </div>
  )
}

export interface Marker { year: number; label: string }

function Markers({ markers }: { markers?: Marker[] }) {
  return <>{(markers || []).map(m => (
    <ReferenceLine key={m.label + m.year} x={m.year} stroke="var(--axis)" strokeOpacity={0.6}
      label={{ value: m.label, position: 'insideTopLeft', fill: 'var(--axis)', fontSize: 11 }} />
  ))}</>
}

/** Net worth + investable savings over time (deterministic). */
export function NetWorthChart({ rows, markers, height = 300 }: { rows: any[]; markers?: Marker[]; height?: number }) {
  const data = rows.map(r => ({ year: r.year, net_worth: r.net_worth, investable: r.investable, home_equity: r.home_equity }))
  return (
    <div>
      <LegendRow items={[{ label: 'Net worth', color: S[0], kind: 'line' }, { label: 'Savings & retirement accounts', color: S[1], kind: 'line' },
        { label: 'Home equity', color: S[2], kind: 'line' }]} />
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="nwFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={S[0]} stopOpacity={0.16} />
              <stop offset="100%" stopColor={S[0]} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="year" {...axisProps} minTickGap={24} />
          <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
          <Tooltip content={<TipBox />} />
          <ReferenceLine y={0} stroke="var(--axis)" />
          <Markers markers={markers} />
          <Area type="monotone" dataKey="net_worth" name="Net worth" stroke={S[0]} strokeWidth={2} fill="url(#nwFill)" isAnimationActive={false} />
          <Line type="monotone" dataKey="investable" name="Savings & retirement" stroke={S[1]} strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="home_equity" name="Home equity" stroke={S[2]} strokeWidth={2} dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Monte Carlo fan: 10–90 and 25–75 bands + median. */
export function FanChart({ mc, field = 'net_worth', markers, height = 320, compare }:
  { mc: any; field?: 'net_worth' | 'investable'; markers?: Marker[]; height?: number; compare?: { label: string; values: number[] } }) {
  if (!mc) return null
  const P = mc[field]
  const data = mc.years.map((y: number, i: number) => ({
    year: y, band90: [P['10'][i], P['90'][i]], band75: [P['25'][i], P['75'][i]], median: P['50'][i],
    compare: compare ? compare.values[i] : undefined,
  }))
  return (
    <div>
      <LegendRow items={[{ label: 'Median', color: S[0], kind: 'line' }, { label: '25th–75th percentile', color: S[0], kind: 'band' },
        { label: '10th–90th percentile', color: S[0], kind: 'band' }, ...(compare ? [{ label: compare.label, color: S[1], kind: 'line' as const }] : [])]} />
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="year" {...axisProps} minTickGap={24} />
          <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
          <Tooltip content={<TipBox />} />
          <ReferenceLine y={0} stroke="var(--axis)" />
          <Markers markers={markers} />
          <Area dataKey="band90" name="10th–90th" stroke="none" fill={S[0]} fillOpacity={0.10} isAnimationActive={false} />
          <Area dataKey="band75" name="25th–75th" stroke="none" fill={S[0]} fillOpacity={0.18} isAnimationActive={false} />
          <Line dataKey="median" name="Median" stroke={S[0]} strokeWidth={2} dot={false} isAnimationActive={false} />
          {compare && <Line dataKey="compare" name={compare.label} stroke={S[1]} strokeWidth={2} dot={false} isAnimationActive={false} />}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export const SPEND_SERIES = [
  { key: 'exp_living', label: 'Living' },
  { key: 'exp_housing', label: 'Housing' },
  { key: 'exp_children', label: 'Children' },
  { key: 'exp_healthcare', label: 'Healthcare' },
  { key: 'exp_recurring', label: 'Recurring' },
  { key: 'exp_onetime', label: 'One-time & down payments' },
  { key: 'taxes', label: 'Taxes' },
]

export function cashflowData(rows: any[]) {
  return rows.map(r => ({
    year: r.year,
    exp_living: r.exp_person1 + r.exp_person2 + r.exp_family,
    exp_housing: r.exp_housing, exp_children: r.exp_children, exp_healthcare: r.exp_healthcare,
    exp_recurring: r.exp_recurring, exp_onetime: r.exp_purchases + r.down_payment, taxes: r.taxes,
    income: r.total_income,
  }))
}

/** Stacked annual spending + taxes, with total income as a line (same $ axis). */
export function CashflowChart({ rows, height = 320, markers }: { rows: any[]; height?: number; markers?: Marker[] }) {
  const data = cashflowData(rows)
  return (
    <div>
      <LegendRow items={[...SPEND_SERIES.map((s, i) => ({ label: s.label, color: S[i] })), { label: 'Income', color: 'rgb(var(--ink))', kind: 'line' as const }]} />
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey="year" {...axisProps} minTickGap={24} />
          <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
          <Tooltip content={<TipBox />} cursor={{ fill: 'rgb(var(--ink) / .04)' }} />
          <Markers markers={markers} />
          {SPEND_SERIES.map((s, i) => (
            <Bar key={s.key} dataKey={s.key} name={s.label} stackId="a" fill={S[i]} stroke="var(--chart-surface)" strokeWidth={1}
              maxBarSize={24} isAnimationActive={false} radius={i === SPEND_SERIES.length - 1 ? [3, 3, 0, 0] : 0} />
          ))}
          <Line dataKey="income" name="Income" stroke="rgb(var(--ink))" strokeWidth={2} dot={false} isAnimationActive={false} type="stepAfter" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Generic multi-line chart (scenario comparison, per-house value etc). */
export function LinesChart({ data, series, height = 280, xKey = 'year' }:
  { data: any[]; series: { key: string; label: string }[]; height?: number; xKey?: string }) {
  return (
    <div>
      {series.length > 1 && <LegendRow items={series.map((s, i) => ({ label: s.label, color: S[i % 8], kind: 'line' as const }))} />}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey={xKey} {...axisProps} minTickGap={24} />
          <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
          <Tooltip content={<TipBox />} />
          <ReferenceLine y={0} stroke="var(--axis)" />
          {series.map((s, i) => (
            <Line key={s.key} dataKey={s.key} name={s.label} stroke={S[i % 8]} strokeWidth={2} dot={false} isAnimationActive={false} />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Stacked bars keyed by arbitrary series (children cost by age etc). */
export function StackedBars({ data, series, height = 260, xKey, xLabel }:
  { data: any[]; series: { key: string; label: string }[]; height?: number; xKey: string; xLabel?: (v: any) => string }) {
  return (
    <div>
      <LegendRow items={series.map((s, i) => ({ label: s.label, color: S[i % 8] }))} />
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 12, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
          <CartesianGrid vertical={false} stroke="var(--grid)" />
          <XAxis dataKey={xKey} {...axisProps} minTickGap={12} tickFormatter={xLabel} />
          <YAxis {...axisProps} tickFormatter={axisMoney} width={56} />
          <Tooltip content={<TipBox title={(l: any) => (xLabel ? xLabel(l) : l)} />} cursor={{ fill: 'rgb(var(--ink) / .04)' }} />
          {series.map((s, i) => (
            <Bar key={s.key} dataKey={s.key} name={s.label} stackId="a" fill={S[i % 8]} stroke="var(--chart-surface)" strokeWidth={1}
              maxBarSize={24} isAnimationActive={false} radius={i === series.length - 1 ? [3, 3, 0, 0] : 0} />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export function Sparkline({ values, height = 36, color = S[0] }: { values: number[]; height?: number; color?: string }) {
  const data = values.map((v, i) => ({ i, v }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
        <Line dataKey="v" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export { Legend }
