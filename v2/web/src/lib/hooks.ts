import { useEffect, useState } from 'react'

/** Per-viewer display preference: show amounts in today's dollars. */
export function useTodayDollars(): [boolean, (v: boolean) => void] {
  const [v, setV] = useState(() => { try { return localStorage.getItem('fp_today') !== '0' } catch { return true } })
  useEffect(() => {
    try { localStorage.setItem('fp_today', v ? '1' : '0') } catch { /* */ }
    window.dispatchEvent(new CustomEvent('fp_today', { detail: v }))
  }, [v])
  useEffect(() => {
    const h = (e: any) => setV(e.detail)
    window.addEventListener('fp_today', h)
    return () => window.removeEventListener('fp_today', h)
  }, [])
  return [v, setV]
}

const MONEY_KEYS = ['wages1', 'wages2', 'ss_income', 'ss1', 'ss2', 'rent_income', 'sale_proceeds', 'total_income', 'taxes',
  'tax_federal', 'tax_state', 'tax_fica', 'tax_foreign', 'contrib_pretax', 'exp_person1', 'exp_person2', 'exp_family',
  'exp_children', 'exp_housing', 'exp_mortgage_pi', 'exp_healthcare', 'exp_recurring', 'exp_purchases', 'down_payment',
  'total_expenses', 'cashflow', 'withdrawal_pretax', 'liquid', 'pretax', 'investable', 'home_value', 'mortgage_balance',
  'home_equity', 'other_assets', 'consumer_debt', 'net_worth', 'liquid1', 'liquid2', 'investment_growth', 'windfalls']

/** Deflate projection rows to today's dollars. */
export function deflate(rows: any[], today: boolean): any[] {
  if (!today || !rows) return rows
  return rows.map(r => {
    const o: any = { ...r }
    for (const k of MONEY_KEYS) if (typeof o[k] === 'number') o[k] = o[k] / r.infl_index
    return o
  })
}
