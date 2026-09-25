import React, { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import { api } from './lib/api'
import { PlanProvider } from './lib/store'
import { Shell } from './components/Shell'
import { Login, Households } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import People from './pages/People'
import Spending from './pages/Spending'
import Kids from './pages/Kids'
import Homes from './pages/Homes'
import Healthcare from './pages/Healthcare'
import Assumptions from './pages/Assumptions'
import Projections from './pages/Projections'
import Timeline from './pages/Timeline'
import Scenarios from './pages/Scenarios'

function Loading() {
  return <div className="min-h-full flex items-center justify-center text-muted text-sm">Loading…</div>
}

function Gate() {
  const [me, setMe] = useState<any>(null)
  const [planRes, setPlanRes] = useState<any>(null)
  const [err, setErr] = useState('')
  const loc = useLocation()

  const refresh = useCallback(async () => {
    setErr('')
    const m = await api.me()
    setMe(m)
    if (m.email && m.household && !m.household.locked) {
      try { setPlanRes(await api.getPlan()) } catch (e: any) { setErr(e.message) }
    } else setPlanRes(null)
  }, [])
  useEffect(() => { refresh() }, [refresh])

  if (!me) return <Loading />
  if (!me.email) return <Login onDone={refresh} />
  if (!me.household || me.household.locked || loc.pathname === '/households')
    return <Households me={me} onDone={() => { history.pushState(null, '', '/'); refresh() }} />
  if (err) return <div className="p-8 text-bad">{err}</div>
  if (!planRes) return <Loading />

  return (
    <PlanProvider key={me.household.id} initial={planRes.plan} lastSaved={planRes.last_saved} household={me.household}>
      <Shell me={me}>
        <Routes>
          <Route path="/" element={<Dashboard isNew={planRes.is_new} />} />
          <Route path="/people" element={<People />} />
          <Route path="/spending" element={<Spending />} />
          <Route path="/kids" element={<Kids />} />
          <Route path="/homes" element={<Homes />} />
          <Route path="/healthcare" element={<Healthcare />} />
          <Route path="/assumptions" element={<Assumptions />} />
          <Route path="/projections" element={<Projections />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="*" element={<Dashboard isNew={false} />} />
        </Routes>
      </Shell>
    </PlanProvider>
  )
}

export default function App() {
  return <BrowserRouter><Gate /></BrowserRouter>
}
