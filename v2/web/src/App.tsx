import React, { Suspense, lazy, useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes, useLocation, Navigate } from 'react-router-dom'
import { api } from './lib/api'
import { PlanProvider } from './lib/store'
import { Shell } from './components/Shell'
import { Login, Households } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import CheckinFlow from './pages/CheckinFlow'
import Checkins from './pages/Checkins'
import Linked from './pages/Linked'
// the rest load on first visit (smaller first download, especially on phones)
const People = lazy(() => import('./pages/People'))
const Spending = lazy(() => import('./pages/Spending'))
const Kids = lazy(() => import('./pages/Kids'))
const Homes = lazy(() => import('./pages/Homes'))
const Healthcare = lazy(() => import('./pages/Healthcare'))
const Assumptions = lazy(() => import('./pages/Assumptions'))
const Projections = lazy(() => import('./pages/Projections'))
const Timeline = lazy(() => import('./pages/Timeline'))
const Scenarios = lazy(() => import('./pages/Scenarios'))
const Onboarding = lazy(() => import('./pages/Onboarding'))
const Actuals = lazy(() => import('./pages/Actuals'))
const Stress = lazy(() => import('./pages/Stress'))
const Retirement = lazy(() => import('./pages/Retirement'))
const Locations = lazy(() => import('./pages/Locations'))
const Household = lazy(() => import('./pages/Household'))
const Ownership = lazy(() => import('./pages/Ownership'))

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
    <PlanProvider key={me.household.id} initial={planRes.plan} lastSaved={planRes.last_saved} household={{ ...me.household, is_admin: me.is_admin, email: me.email }}>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/setup" element={<Onboarding />} />
          <Route path="/checkin" element={<CheckinFlow />} />
          <Route path="*" element={
            <Shell me={me}>
              <Suspense fallback={<Loading />}>
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
                  <Route path="/locations" element={<Locations />} />
                  <Route path="/household" element={<Household />} />
                  <Route path="/ownership" element={<Ownership />} />
                  <Route path="/accounts" element={<Linked />} />
                  <Route path="*" element={<Dashboard isNew={false} />} />
                </Routes>
              </Suspense>
            </Shell>} />
        </Routes>
      </Suspense>
    </PlanProvider>
  )
}

export default function App() {
  return <BrowserRouter><Gate /></BrowserRouter>
}
