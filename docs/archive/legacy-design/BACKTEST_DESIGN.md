# V3.19 Backtest Design

## Goals

- Make the score-driven trading idea testable without future data.
- Convert screener snapshots, factor rules and event-risk filters into typed strategy signals.
- Model A-share execution costs and constraints explicitly.
- Persist repeatable runs and expose API/UI outputs with clear warnings.
- Reserve paper trading without connecting to a real broker.

## Architecture

`quant_data/backtest/` is the new core package:

- `models.py`: `BacktestConfig`, `StrategySignal`, `Order`, `Fill`, `Position`, `PortfolioState`, `Trade`, `BacktestResult`.
- `data_loader.py`: OHLCV loading, qfq/none/hfq context, quality report, no-lookahead assertion.
- `signal_adapter.py`: `score_rank_rebalance`, `factor_rule_strategy`, `event_risk_filter`.
- `execution.py`: T+1, 100-share lots, no shorting, suspended/limit checks, costs, slippage and volume caps.
- `portfolio.py`: position sizing, cash reserve, max positions, stop loss/take profit/trailing stop and daily state.
- `risk.py`: return, annualized return, drawdown, Sharpe, Sortino, Calmar, win rate, profit factor, costs, turnover and benchmark/excess return fields.
- `engine.py`: daily loop: signal on day T, execute on T+1.
- `optimizer.py`: grid/random parameter search.
- `walk_forward.py`: rolling in-sample/out-of-sample validation.
- `storage.py`: save/load/list/delete/export run results.
- `paper_broker.py`: virtual order/fill flow only.

## API Shape

V3.19 endpoints return:

```json
{"ok": true, "run_id": "...", "data": {}, "metrics": {}, "errors": [], "warnings": [], "cache_status": "..."}
```

Added endpoints:

- `POST /api/backtest/run`
- `GET /api/backtest/result/{run_id}`
- `GET /api/backtest/runs`
- `DELETE /api/backtest/result/{run_id}`
- `GET /api/backtest/export/{run_id}`
- `POST /api/backtest/compare`
- `POST /api/backtest/optimize`
- `POST /api/backtest/walk-forward`
- `GET /api/backtest/report/{run_id}`
- `GET /api/paper/state`
- `POST /api/paper/signal`
- `POST /api/paper/fill`

The legacy `GET /api/backtest/run` remains for the current chart UI.

## No-Lookahead Rule

Features and signals are built from the current date and prior rows. Orders are scheduled for the next trading date. The loader exposes `assert_no_lookahead` and result payloads include the PIT note.

## A-Share Execution Model

- Buy/sell quantity rounded to 100-share lots.
- No shorting.
- T+1 sell availability.
- Suspended or zero-volume days block execution.
- Limit-up days block buys; limit-down days block sells.
- Volume cap can create partial fills.
- Costs include commission, minimum commission, stamp tax on sells, transfer fee and slippage.

## Screener Integration

`SignalAdapter.score_rank_rebalance` converts screener rows into target weights while filtering low grades, ST/suspended/limit-up and high-risk rows. `screener_snapshot_id` can be attached to signals and results for traceability.

## Paper Trading

The paper broker accepts strategy signals, creates virtual orders and simulates fills with the same execution model. It explicitly does not call real broker APIs.
