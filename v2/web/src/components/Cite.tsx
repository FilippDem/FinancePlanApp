import React, { createContext, useContext } from 'react'
import { usePlan } from '../lib/store'

/** Numbered data citations: a page (or wizard step) declares the sources it uses, in order,
 *  and gets small [n] markers plus a matching list of links at the bottom.
 *
 *    const { Cite, Sources } = useCites(['bls_cex_2022', 'bea_rpp_2024'])
 *    <p>Spending by income group<Cite id="bls_cex_2022" /></p>
 *    <Sources />
 */
export interface Source { publisher: string; title: string; year: string; url: string; alt_url?: string; used_for?: string; note?: string }

const Ctx = createContext<string[] | null>(null)

function useSourceData(): Record<string, Source> {
  const { reference } = usePlan()
  return (reference?.sources || {}) as Record<string, Source>
}

export function useCites(ids: string[]) {
  const data = useSourceData()
  const n = (id: string) => ids.indexOf(id) + 1
  const Cite = ({ id }: { id: string | string[] }) => {
    const list = Array.isArray(id) ? id : [id]
    return (
      <sup className="ml-0.5 whitespace-nowrap text-[0.72em] font-medium">
        {list.map(i => {
          const s = data[i]
          const k = n(i)
          if (!k) return null
          return (
            <a key={i} href={s?.url || `#src-${i}`} target={s?.url ? '_blank' : undefined} rel="noreferrer"
              title={s ? `${s.publisher} — ${s.title} (${s.year})` : i} className="text-accent hover:underline no-underline">[{k}]</a>
          )
        })}
      </sup>
    )
  }
  const Sources = ({ className = '', title = 'Sources' }: { className?: string; title?: string }) => (
    <SourceList ids={ids} data={data} className={className} title={title} />
  )
  return { Cite, Sources, n }
}

function SourceList({ ids, data, className, title }: { ids: string[]; data: Record<string, Source>; className?: string; title: string }) {
  const rows = ids.map((id, i) => ({ id, k: i + 1, s: data[id] })).filter(r => r.s)
  if (!rows.length) return null
  return (
    <div className={`text-[12px] leading-5 text-muted ${className}`}>
      <div className="font-semibold uppercase tracking-wide text-[10.5px] mb-1">{title}</div>
      <ol className="space-y-0.5">
        {rows.map(({ id, k, s }) => (
          <li key={id} id={`src-${id}`} className="flex gap-1.5">
            <span className="tnum shrink-0">[{k}]</span>
            <span>
              {s.publisher}, <a href={s.url} target="_blank" rel="noreferrer" className="text-accent hover:underline">{s.title}</a> ({s.year})
              {s.alt_url && <> · <a href={s.alt_url} target="_blank" rel="noreferrer" className="hover:underline">data table</a></>}
              {s.note && <span className="italic"> — {s.note}</span>}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}

/** Context flavour for deeply nested components (e.g. the spending slider) that shouldn't own the numbering. */
export function CiteScope({ ids, children }: { ids: string[]; children: React.ReactNode }) {
  return <Ctx.Provider value={ids}>{children}</Ctx.Provider>
}
export function ScopedCite({ id }: { id: string | string[] }) {
  const ids = useContext(Ctx)
  const { Cite } = useCites(ids || (Array.isArray(id) ? id : [id]))
  return <Cite id={id} />
}
