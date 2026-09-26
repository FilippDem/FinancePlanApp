// Client-side mirror of engine/finplan/mortgage.py for instant calculator feedback.
export function monthlyPayment(principal: number, annualRate: number, years: number) {
  if (principal <= 0 || years <= 0) return 0
  const n = Math.round(years * 12), r = annualRate / 12
  return r <= 0 ? principal / n : principal * r / (1 - Math.pow(1 + r, -n))
}

export interface LoanTerms { start: number; principal: number; rate: number; pmt: number; required: number; down: number; original: number; price: number }

export function loanTerms(h: any, currentYear: number): LoanTerms {
  const rate = +h.mortgage_rate || 0
  const price = +h.purchase_price || 0
  if (h.mortgage_mode === 'estimate') {
    const dp = +(h.down_payment_pct ?? 20)
    const principal = Math.max(price * (1 - dp / 100), 0)
    const pmt = monthlyPayment(principal, rate, +h.loan_term_years || 30)
    return { start: +h.purchase_year, principal, rate, pmt, required: pmt, down: price * dp / 100, original: principal, price }
  }
  const principal = +h.mortgage_balance || 0
  const required = monthlyPayment(principal, rate, +h.mortgage_years_left || 0)
  const ov = +h.mortgage_payment_override || 0
  return { start: Math.max(currentYear, +h.purchase_year), principal, rate, pmt: ov > 0 ? ov : required, required,
    down: Math.max(price - principal, 0), original: principal, price }
}

export interface AmortYear { year: number; principal: number; interest: number; balance: number }

export function amortize(t: LoanTerms): AmortYear[] {
  const out: AmortYear[] = []
  let b = t.principal
  const r = t.rate / 12
  if (b <= 0 || t.pmt <= 0) return out
  for (let y = 0; y < 60 && b > 0.005; y++) {
    let pi = 0, ii = 0
    for (let m = 0; m < 12 && b > 0.005; m++) {
      const int = b * r
      const pay = Math.min(t.pmt, b + int)
      if (pay <= int) return out  // never pays off
      ii += int; pi += pay - int; b = Math.max(b + int - pay, 0)
    }
    out.push({ year: t.start + y, principal: pi, interest: ii, balance: b })
  }
  return out
}

/** Balance at the start of `year`. */
export function balanceAt(t: LoanTerms, year: number) {
  if (year <= t.start) return t.principal
  const a = amortize(t)
  const row = a.find(x => x.year === year - 1)
  return row ? row.balance : 0
}

/** Keep the legacy keys (read by v0.8 and the summary cards) consistent in estimate mode. */
export function syncLegacy(h: any, currentYear: number) {
  if (h.mortgage_mode !== 'estimate') return
  const t = loanTerms(h, currentYear)
  const y = Math.max(currentYear, +h.purchase_year)
  const a = amortize(t)
  h.mortgage_balance = Math.round(balanceAt(t, y) * 100) / 100
  const payoff = a.length ? a[a.length - 1].year : y
  h.mortgage_years_left = Math.max(0, payoff + 1 - y)
}

/** Monthly housing payment breakdown (Redfin style) at purchase / today. */
export function monthlyBreakdown(h: any, currentYear: number) {
  const t = loanTerms(h, currentYear)
  const y = Math.max(currentYear, +h.purchase_year)
  const bal = balanceAt(t, y)
  const pi = bal > 0.5 ? t.pmt : 0
  const base = t.price || +h.current_value || 0
  let pmi = 0
  if (pi > 0 && bal > 0.78 * base) {
    if (h.mortgage_mode === 'estimate') { if (Number(h.down_payment_pct ?? 20) < 20) pmi = t.original * (+h.pmi_rate || 0) / 100 / 12 }
    else pmi = +h.pmi_monthly || 0
  }
  const tax = (+h.current_value || 0) * (+h.property_tax_rate || 0) / 12
  const ins = (+h.home_insurance || 0) / 12
  const hoa = +h.hoa_monthly || 0
  const upkeep = ((+h.current_value || 0) * (+h.maintenance_rate || 0) + (+h.upkeep_costs || 0)) / 12
  return { pi, tax, ins, hoa, pmi, total: pi + tax + ins + hoa + pmi, upkeep, terms: t }
}
