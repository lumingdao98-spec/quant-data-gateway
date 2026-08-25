# V3.23 Baseline Audit

Generated: 2026-06-05

## Baseline Used

- Repository: `lumingdao98-spec/quant-data-gateway`
- Current work branch: `feature/v3.23-full-auto-trading-core`
- Baseline branch: `codex/backtest-combo-strategy-ui`
- Baseline commit: `b19545d local v3.18 closedloop cache edition`
- Remote: `origin https://github.com/lumingdao98-spec/quant-data-gateway.git`

## Why Main Was Not Used

`main` and `origin/main` are at `a964c05 Implement V3.20 scientific backtest foundation`.
They do not contain the later V3.21 realtime-paper loop, V3.22 score provenance readiness, or V3.23 chart/paper trading polish that exists on `codex/backtest-combo-strategy-ui`.

## Branch Review

- `codex/backtest-combo-strategy-ui`: newest and most complete local branch. Contains V3.20 backtest, V3.21 realtime paper, V3.22 scoring/provenance readiness, and partial V3.23 UX work.
- `origin/codex/backtest-combo-strategy-ui`: at `52acfd1`, behind local branch by two commits.
- `fix/v3.18.3-stable-recovery`: older recovery branch with backtest/paper foundation but fewer V3.21/V3.22 changes.
- `backup-v3.18.2-broken`: older backup.

GitHub CLI was unavailable on this machine. GitHub connector search did not find open or merged PRs with V3.23/realtime/broker/autotrading/backtest keywords.

## Existing Auto-Trading Capability Before This Pass

- Historical backtest engine and legacy backtest UI.
- Paper-only realtime simulation engine and `/realtime-paper`.
- Risk gateway for paper orders.
- Human confirmation queue for paper warnings.
- V3.22 score provenance primitives in `quant_data/factors/`.
- Market rules config for A-share execution.

## Missing Capability Before This Pass

- Explicit live-trading module and broker adapters.
- Disabled-by-default live broker safety shell.
- Unified V3.23 scoring namespace for backtest/paper/live.
- Unified order lifecycle and execution router.
- Unified trading record persistence.
- Chart marker engine for orders/fills/risk markers.
- Data truth contracts and source registry at the data layer.
- V3.23 session APIs for realtime-paper.
- `/live-trading`, `/trading-records`, `/data-center` page entries.

## Scope Added In This Pass

- Added data truth layer, source registry, freshness checks, PIT store and snapshot contracts.
- Added V3.23 scoring provenance, factor engine, signal fusion and score explanation layer.
- Added V3.23 strategy classification, suitability, sizing and exit adapters.
- Added broker abstraction, disabled broker, simulator broker, QMT/PTrade import guards.
- Added live trading shell with kill switch, confirmation queue and safe rejection defaults.
- Added unified order lifecycle, execution router, chart markers and SQLite trading store.
- Added V3.23 APIs for backtest, realtime-paper sessions, live broker, live orders, chart markers, trading records and data center.
- Added page entries for live trading, trading records and data center.

## Safety Boundary

`FEATURE_LIVE_BROKER=false`, `LIVE_TRADING_ENABLED=false`, `ORDER_CONFIRM_REQUIRED=true` are the default operating assumptions. Without explicit local broker configuration and user confirmation, all true broker operations are disabled or rejected.
