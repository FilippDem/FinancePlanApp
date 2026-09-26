export class ApiError extends Error {
  status: number
  constructor(status: number, msg: string) { super(msg); this.status = status }
}

async function req<T = any>(method: string, url: string, body?: any): Promise<T> {
  const r = await fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  })
  if (!r.ok) {
    let msg = r.statusText
    try { const j = await r.json(); msg = j.detail || msg } catch { /* ignore */ }
    throw new ApiError(r.status, msg)
  }
  return r.json()
}

export const api = {
  me: () => req('GET', '/api/me'),
  login: (email: string) => req('POST', '/api/login', { email }),
  logout: () => req('POST', '/api/logout'),
  createHousehold: (name: string, passphrase?: string) => req('POST', '/api/households', { name, passphrase }),
  createTestHousehold: () => req('POST', '/api/households/test'),
  joinHousehold: (id: string) => req('POST', '/api/households/join', { id }),
  selectHousehold: (id: string, passphrase?: string) => req('POST', '/api/households/select', { id, passphrase }),
  getPlan: () => req('GET', '/api/plan'),
  putPlan: (plan: any) => req('PUT', '/api/plan', { plan }),
  project: (plan: any) => req('POST', '/api/project', { plan }),
  monteCarlo: (plan: any, n?: number, normalized?: boolean) => req('POST', '/api/montecarlo', { plan, n, normalized }),
  normalize: (plan: any) => req('POST', '/api/normalize', { plan }),
  scenarios: () => req('GET', '/api/scenarios'),
  saveScenario: (name: string, plan: any) => req('POST', '/api/scenarios', { name, plan }),
  renameScenario: (name: string, new_name: string) => req('POST', '/api/scenarios/rename', { name, new_name }),
  deleteScenario: (name: string) => req('DELETE', `/api/scenarios/${encodeURIComponent(name)}`),
  demos: () => req('GET', '/api/demos'),
  reference: () => req('GET', '/api/reference'),
  checkins: () => req('GET', '/api/checkins'),
  checkinSettings: (body: { cadence?: string; snooze_days?: number; next_due?: string; email_reminders?: boolean }) => req('PUT', '/api/checkins/settings', body),
  addCheckin: (checkin: any) => req('POST', '/api/checkins', { checkin }),
  deleteCheckin: (id: string) => req('DELETE', `/api/checkins/${encodeURIComponent(id)}`),
  evaluate: (plan: any, date: string, investable: number, net_worth?: number) => req('POST', '/api/checkins/evaluate', { plan, date, investable, net_worth }),
  rebase: (plan: any, balances: any, date: string) => req('POST', '/api/checkins/rebase', { plan, balances, date }),
  getActuals: () => req('GET', '/api/actuals'),
  putActualYear: (year: number, actual: any) => req('PUT', `/api/actuals/${year}`, { actual }),
  planned: (plan: any, year: number) => req('POST', '/api/actuals/planned', { plan, year }),
  importWorkbook: async (file: File) => {
    const r = await fetch('/api/actuals/import', { method: 'POST', body: await file.arrayBuffer(), credentials: 'same-origin',
      headers: { 'Content-Type': 'application/octet-stream' } })
    if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m } catch { /* */ } throw new ApiError(r.status, m) }
    return r.json()
  },
  history: () => req('GET', '/api/history'),
  previewVersion: (id: string) => req('POST', '/api/history/preview', { id }),
  restoreVersion: (id: string) => req('POST', '/api/history/restore', { id }),
  stressDefaults: (plan: any) => req('POST', '/api/stress/defaults', { plan }),
  stress: (plan: any, tests: any[], n = 400) => req('POST', '/api/stress', { plan, tests, n }),
  retirement: (plan: any, withdrawal_rate = 0.04) => req('POST', '/api/retirement', { plan, withdrawal_rate }),
  retireWhatif: (plan: any, n = 300) => req('POST', '/api/retirement/whatif', { plan, n }),
  notifyStatus: () => req('GET', '/api/notify/status'),
  testEmail: () => req('POST', '/api/checkins/test-email'),
  downloadReport: async (plan: any) => {
    const r = await fetch('/api/report.pdf', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan }) })
    if (!r.ok) throw new ApiError(r.status, r.statusText)
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `financial-plan-${new Date().toISOString().slice(0, 10)}.pdf`
    a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 5000)
  },
  template: (kind: 'adult' | 'family' | 'children', location: string, strategy: string, current_year: number, inflation: number, source: 'calibrated' | 'v08' = 'calibrated') =>
    req('POST', `/api/templates/${kind}`, { location, strategy, current_year, inflation, source }),
  spendingCurve: (location: string, current_year: number, inflation: number) =>
    req('GET', `/api/spending/curve?location=${encodeURIComponent(location)}&current_year=${current_year}&inflation=${inflation}`),
}
