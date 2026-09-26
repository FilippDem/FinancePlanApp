import React, { useMemo } from 'react'
import { geoEqualEarth, geoPath, geoInterpolate } from 'd3-geo'
import { feature } from 'topojson-client'
import land110 from 'world-atlas/land-110m.json'
import { S } from './charts'

export interface MapStop { n: number; name: string; year: number; lat: number; lon: number }

const LAND: any = feature(land110 as any, (land110 as any).objects.land)

/** Equal-Earth world map with numbered stops and great-circle "flight paths" between them. */
export function WorldMap({ stops, height = 360 }: { stops: MapStop[]; height?: number }) {
  const W = 960
  const { path, proj } = useMemo(() => {
    const proj = geoEqualEarth()
    const pts = stops.map(s => [s.lon, s.lat] as [number, number])
    const lons = pts.map(p => p[0]), lats = pts.map(p => p[1])
    const spanLon = pts.length ? Math.max(...lons) - Math.min(...lons) : 360
    const spanLat = pts.length ? Math.max(...lats) - Math.min(...lats) : 180
    if (pts.length && spanLon < 120 && spanLat < 70) {
      // zoom to the region around the stops (with generous padding)
      const pad = Math.max(12, Math.max(spanLon, spanLat) * 0.35)
      const box = { type: 'MultiPoint', coordinates: [
        [Math.min(...lons) - pad, Math.min(...lats) - pad * 0.6], [Math.max(...lons) + pad, Math.max(...lats) + pad * 0.6]] } as any
      proj.fitExtent([[20, 20], [W - 20, height - 20]], box)
    } else {
      proj.fitExtent([[10, 10], [W - 10, height - 10]], { type: 'Sphere' } as any)
    }
    return { path: geoPath(proj), proj }
  }, [stops, height])

  const arcs = stops.slice(1).map((s, i) => {
    const a = stops[i]
    const interp = geoInterpolate([a.lon, a.lat], [s.lon, s.lat])
    const line = { type: 'LineString', coordinates: Array.from({ length: 33 }, (_, k) => interp(k / 32)) } as any
    return path(line) || ''
  })

  return (
    <svg viewBox={`0 0 ${W} ${height}`} className="w-full h-auto rounded-lg bg-sunken/60" role="img" aria-label="Map of your moves">
      <path d={path({ type: 'Sphere' } as any) || ''} fill="none" stroke="var(--grid)" />
      <path d={path(LAND) || ''} fill="rgb(var(--line))" stroke="var(--chart-surface)" strokeWidth={0.5} />
      {arcs.map((d, i) => <path key={i} d={d} fill="none" stroke={S[1]} strokeWidth={2} strokeDasharray="5 4" opacity={0.9} />)}
      {stops.map((s, i) => {
        const p = proj([s.lon, s.lat])
        if (!p) return null
        return (
          <g key={s.n} transform={`translate(${p[0]},${p[1]})`}>
            <circle r={11} fill={S[0]} stroke="var(--chart-surface)" strokeWidth={2} />
            <text textAnchor="middle" dy="0.35em" fontSize={11} fontWeight={700} fill="white">{s.n}</text>
            <text x={14} dy="0.35em" fontSize={12} fill="rgb(var(--ink))" stroke="var(--chart-surface)" strokeWidth={3} paintOrder="stroke"
              style={{ transform: i % 2 ? 'translateY(14px)' : undefined }}>{s.name} · {s.year}</text>
          </g>
        )
      })}
    </svg>
  )
}
