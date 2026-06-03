# V3.23 Baseline Audit

Generated: 2026-06-03

## Branch And Remote

- Current branch: `codex/backtest-combo-strategy-ui`
- Remote: `origin https://github.com/lumingdao98-spec/quant-data-gateway.git`
- Recent head before V3.23 polish: `52acfd1 Improve intraday chart markers and paper trading UI`
- Other local branches: `main`, `fix/v3.18.3-stable-recovery`, `backup-v3.18.2-broken`
- Runtime-only local change observed before this work: `data/watchlist.json`

## Current System Shape

- Market monitor page: `/ui`
- Screener page: `/screener`
- Historical backtest page: `/backtest`
- Realtime paper trading page: `/realtime-paper`
- Paper trading API: `/api/realtime-paper/*`
- Broker/live trading status remains disabled by design; current code is paper-only and does not connect to real brokers.

## V3.23 Work Scope Applied In This Pass

- Keep intraday chart fixed to a full 09:30-15:30 session axis; no drag or zoom on intraday mode.
- Keep daily/weekly/monthly K-line chart drag and wheel zoom behavior.
- Clamp/wrap long marker, order book, metric and tooltip text to reduce data overflow.
- Replace ambiguous realtime paper "tick" UI with a clear automatic simulation loop and "execute one simulation round" action.
- Show paper simulation mode, last run time, next run countdown, positions, cost, quantity and unrealized PnL.
- Preserve paper-only safety messaging: closed-session simulation is marked as paper replay, not live trading.

## Known Data Boundaries

- Five-level order book uses public quote snapshots when available. Spoofing, cancellation behavior and precise main-force absorption require Level-2 order queue and tick-by-tick data, so the UI labels these as low-confidence observations unless such data exists.
- Closed-market realtime simulation can replay cached/snapshot data for research only. It cannot represent real intraday execution after the market closes.
- Missing quote, PB/PE, turnover or order-book fields must be displayed as missing/stale/unsupported rather than fabricated.

## Verification Targets

- `python -m compileall -q quant_data`
- `pytest -q`
- Browser smoke check for `/ui?symbol=300750&frame=time`, `/ui?symbol=300750&frame=1d`, and `/realtime-paper`
