# Financial check-ins: keeping the plan alive

> **Status:** implemented. It includes cadence settings, the due banner and nav badge, guided and quick check-ins, scoring, roll-forward with a snapshot, the history chart, the `.ics` reminder, the v0.8 actuals bridge, **email reminders** (SMTP, opt-in per household), and the yearly **Actuals** page with an Excel tracking workbook.

**Goal:** a plan should be something a family opens every few months, not something they set up once and forget. A check-in takes about 5 minutes. It records where you actually are, tells you plainly whether you're on track, and rolls the plan forward so the next projection starts from reality.

## 1. The loop

```
 Plan ──► Check-in due ──► Update balances ──► Compare with plan ──► Roll plan forward ──► (next check-in)
   ▲           │                 (5 min)          on track? why?        snapshot + rebase
   └───────────┴──────────── life changed? → edit the plan (new job, baby, move, home) ◄──┘
```

## 2. Cadence and prompts
| Setting | Default | Notes |
|---|---|---|
| Cadence | **Quarterly** (choose quarterly, every 6 months, yearly, or off) | Set during onboarding and changeable under Check-ins |
| Due date | Start of the next period after the last check-in (Jan 1 / Apr 1 / Jul 1 / Oct 1 for quarterly) | Stored as `checkin_settings.next_due` |
| In-app prompt | A banner on the Dashboard plus a badge on "Check-ins" in the sidebar once due. Snoozing moves it 2 weeks. | Everyone in the household sees it, so either partner can do it |
| Calendar reminder | "Add to calendar" downloads an `.ics` file with a repeating event (RRULE) that links back to the app | Works with Google, Apple and Outlook, with no email server needed |
| Email reminder | A background job in the server (hourly) emails every household member when a check-in is due, plus one follow-up 7 days later | Opt-in toggle on the Check-ins page; needs `SMTP_*` settings (see README). State kept in `checkin_settings.last_emailed_due / last_emailed_at / followup_sent` |

**Manual check-ins** are available at any time, off cycle. "Quick update" asks only for total savings and home values (about 30 seconds). A full check-in adds per-person accounts, debts and life changes. A manual check-in doesn't move the scheduled due date unless it happens within 3 weeks of it, in which case it counts as that period's check-in.

## 3. What a check-in asks (TurboTax-style, one screen at a time)
1. **Balances today.** For each person: cash and investments, and retirement accounts (401k/IRA/HSA). Each field is pre-filled with the plan's expected value so you only change what's different.
2. **Homes.** Estimated value (e.g. from Zillow or Redfin) and mortgage balance from your statement, for each home.
3. **Other debts.** Car loans, credit cards, student loans (a household total).
4. **What changed?** Chips for: new job or raise, lost job, baby on the way, moved, bought or sold a home, big purchase, health event, nothing. Each chip links to the right page after the check-in.
5. **Result** (see §4) and a choice: **"Update my plan with these numbers"** (recommended), or just record the check-in.

## 4. "Are we on track?" scoring
At check-in time the app computes, from the plan as it stood before the check-in:
- **Expected savings** at today's date, interpolated between the plan's yearly values.
- **The expected range:** the Monte Carlo 5th–95th percentile band at today's date.
- **Your percentile:** where the actual savings fall in that band.

| Status | Rule | Message |
|---|---|---|
| **Ahead** | ≥ 75th percentile | "You're ahead of plan by $X." |
| **On track** | 25th–75th | "You're right where the plan expected." |
| **A bit behind** | 10th–25th | "You're $X behind; small changes can close this." |
| **Off track** | < 10th | "Well below the plan's range. Let's look at why." |

Alongside that, the app shows:
- The change since the last check-in: savings Δ, home equity Δ, net worth Δ.
- The plan's success rate before and after rolling forward, so you can see whether the future got better or worse.
- Drift hints based on which bucket drifted most, e.g. "Savings grew $8k less than planned while markets were roughly flat, so spending was probably higher than planned. Review Spending?"

## 5. Rolling the plan forward (rebase)
When you choose "Update my plan":
1. The current plan is saved automatically as a scenario: `Before check-in 2026-Q3`. This builds a history of plans.
2. The balances are applied:
   - savings and pre-tax balances per person (`parentX_net_worth`, `parentX_pretax_balance`, …)
   - home values and mortgage balances (the home switches to "actual loan" mode)
   - other debts come off savings
3. If the calendar year has moved on, `current_year` advances and each person's age advances by the same amount. Absolute years (job changes, purchases, moves) don't change.

## 6. Data model (additive, stored in the household file next to `plan_data`)
```jsonc
"checkin_settings": { "cadence": "quarterly", "next_due": "2026-10-01", "snoozed_until": null },
"checkins": [{
  "id": "c_8f2a", "date": "2026-09-25", "period": "2026-Q3", "kind": "scheduled" | "manual" | "quick" | "baseline",
  "entered_by": "filippdem@gmail.com",
  "balances": { "p1": {"liquid": 120000, "pretax": 80000}, "p2": {...},
                "homes": [{"name": "Primary Home", "value": 820000, "mortgage": 402000}], "other_debts": 12000 },
  "totals":   { "investable": 388000, "home_equity": 418000, "net_worth": 794000 },
  "expected": { "investable": 371000, "p10": 330000, "p25": 352000, "p50": 371000, "p75": 392000, "p90": 410000,
                "net_worth": 770000, "success_rate": 0.83 },
  "percentile": 71, "status": "on_track",
  "life_changes": ["new_job"], "notes": "Filipp started at …",
  "applied_to_plan": true, "success_rate_after": 0.86
}]
```
- Check-ins are **household history**, so they live outside `plan_data`. Loading a scenario never erases them.
- **v0.8 bridge:** a check-in dated Oct–Dec also writes `actuals[<year>].net_worth` (merging, never overwriting other fields), so v0.8's Plan vs Actual keeps working.

## 7. Yearly actuals (the fuller picture)
Check-ins track balances. Once a year (the app suggests it after a Q4 check-in) you can also record **what actually happened**: income by source, spending by category, taxes and year-end net worth. The **Actuals** page lays each category next to the plan's number for that year and shows the variance. Leave blank whatever you don't track. For month-by-month tracking, download the **Excel workbook** (plan in blue, your cells in yellow, one sheet per year), fill it in, and import it; importing merges into what's already stored and never erases. Everything uses the v0.8 `actuals[year]` shape, so v0.8's Plan vs Actual still reads it.

## 8. Where it shows up
- **Dashboard:** the "Check-in due" banner, the last status chip ("On track · 71st percentile · Sep 25"), and a net worth chart with your actual check-ins drawn as dots over the plan's range. That picture is what makes it a living document.
- **Check-ins page:** status, the history chart, a table of all check-ins, the cadence setting, "Add to calendar", "Start check-in" and "Quick update".
- **Onboarding** finishes by choosing a cadence and recording a *baseline* check-in, the starting point every later check-in is measured against.
