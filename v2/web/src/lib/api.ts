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
  checkinSettings: (body: { cadence?: string; snooze_days?: number }) => req('PUT', '/api/checkins/settings', body),
  addCheckin: (checkin: any) => req('POST', '/api/checkins', { checkin }),
  deleteCheckin: (id: string) => req('DELETE', `/api/checkins/${encodeURIComponent(id)}`),
  evaluate: (plan: any, date: string, investable: number, net_worth?: number) => req('POST', '/api/checkins/evaluate', { plan, date, investable, net_worth }),
  rebase: (plan: any, balances: any, date: string) => req('POST', '/api/checkins/rebase', { plan, balances, date }),
  template: (kind: 'adult' | 'family' | 'children', location: string, strategy: string, current_year: number, inflation: number) =>
    req('POST', `/api/templates/${kind}`, { location, strategy, current_year, inflation }),
}
