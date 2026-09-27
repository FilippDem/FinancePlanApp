# Linked accounts (Fidelity and other brokerages)

Optional. The app works exactly the same without it; typing balances in check-ins always works.

## Two ways in (use either or both)

| | CSV import | SnapTrade (automatic) |
|---|---|---|
| Setup | None | Free SnapTrade **Personal** keys, pasted once [1] |
| Fidelity steps | Fidelity.com → Accounts & Trade → Portfolio → Positions → Download | Linked accounts → Connect Fidelity → sign in at Fidelity |
| Freshness | When you import | Once a day [3]; the server checks hourly, and on Sync now / page open |
| Access | File you choose | Read-only; credentials stay with Fidelity (OAuth) [2] |
| Other institutions | Any CSV with an account and a value/balance column | Any brokerage SnapTrade supports (Other brokerage button) |

Each account is mapped once: who it belongs to (person 1, person 2, joint), what it counts as (cash & investments, retirement account, HSA, don't count) and, with Who owns what on, whether it's separate property. Later syncs and re-imports keep these choices.

## How balances reach the plan
- The page shows linked totals next to the plan's numbers.
- The first time, the app asks whether the linked accounts hold **all** your savings. Yes: check-ins start from the linked totals. No (default until you answer): check-ins show them with a "Use these" button, so money held elsewhere isn't lost.
- Nothing changes the plan until you finish a check-in; the plan is backed up first as usual.
- Roth accounts count toward the pre-tax balance for now (the engine has one pre-tax bucket). HSAs count as pre-tax, like the plan's HSA.
- Separate property: from accounts marked separate; if none are marked, the plan's own separate estimate is kept.

## Storage (additive household keys, encrypted in encrypted households)
- `integrations.snaptrade`: client ID, consumer key (and user ID/secret for commercial keys), who added them. Never returned to the browser.
- `linked_accounts`: `{accounts: {key: {source, institution, name, number (last 4), balance, as_of, owner, kind, separate, include, connection_id, disabled}}, covers_all, last_sync, last_error, connections}`.

## Operations
- Background sync thread: hourly check, syncs households whose last sync is over 20 hours old. Disable with `DISABLE_LINKED_SYNC=1`. Keep uvicorn at 1 worker (same as email reminders).
- Encrypted households can't be synced in the background (the server doesn't hold the passphrase); they sync when opened.
- When Fidelity needs a fresh sign-in, SnapTrade disables the connection [4]; the app keeps the last balances and shows a Reconnect button on Linked accounts and Check-ins.
- Requests are signed per SnapTrade's HMAC-SHA256 scheme (`server/linked.py: sign`), covered by a test.
- Not yet verified: whether SnapTrade reaches Fidelity NetBenefits (employer 401(k)) accounts. Use the CSV import for those if not.

## Sources
[1] SnapTrade, [Personal vs Commercial](https://docs.snaptrade.com/docs/personal-vs-commercial)
[2] SnapTrade, [Fidelity integration](https://snaptrade.com/brokerage-integrations/fidelity-api)
[3] SnapTrade, [Syncing and Data Freshness](https://docs.snaptrade.com/docs/syncing)
[4] SnapTrade, [Fix Disabled Connections](https://docs.snaptrade.com/docs/fix-broken-connections)
