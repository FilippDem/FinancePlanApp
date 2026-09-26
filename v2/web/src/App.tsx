import React, { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes, useLocation, Navigate } from 'react-router-dom'
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
import Onboarding from './pages/Onboarding'
import CheckinFlow from './pages/CheckinFlow'
import Checkins from './pages/Checkins'
import Actuals from './pages/Actuals'
import Stress from './pages/Stress'
import Retirement from './pages/Retirement'

function skipSetup() {
  try { if (sessionStorage.getItem('fp_setup_seen')) return true; sessionStorage.setItem('fp_setup_seen', '1') } catch { /* */ }
  return false
}

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
      <Routes>
        <Route path="/setup" element={<Onboarding />} />
        <Route path="/checkin" element={<CheckinFlow />} />
        <Route path="*" element={
          <Shell me={me}>
            <Routes>
              <Route path="/" element={planRes.is_new && !skipSetup() ? <Navigate to="/setup" replace /> : <Dashboard isNew={planRes.is_new} />} />
              <Route path="/people" element={<People />} />
              <Route path="/spending" element={<Spending />} />
              <Route path="/kids" element={<Kids />} />
              <Route path="/homes" element={<Homes />} />
              <Route path="/healthcare" element={<Healthcare />} />
              <Route path="/assumptions" element={<Assumptions />} />
              <Route path="/projections" element={<Projections />} />
              <Route path="/timeline" element={<Timeline />} />
              <Route path="/scenarios" element={<Scenarios />} />
              <Route path="/checkins" element={<Checkins />} />
              <Route path="/actuals" element={<Actuals />} />
              <Route path="/stress" element={<Stress />} />
              <Route path="/retirement" element={<Retirement />} />
              <Route path="*" element={<Dashboard isNew={false} />} />
            </Routes>
          </Shell>} />
      </Routes>
    </PlanProvider>
  )
}

export default function App() {
  return <BrowserRouter><Gate /></BrowserRouter>
}
