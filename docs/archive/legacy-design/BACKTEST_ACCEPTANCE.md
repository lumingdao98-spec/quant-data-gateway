# V3.19 Backtest Acceptance

## Acceptance Checklist

- Core package exists under `quant_data/backtest/`.
- Backtest dataclasses are stable and serializable.
- Data loader reports duplicate dates, missing gaps, OHLC anomalies, zero volume, limit days, warmup status and PIT notes.
- Signal adapter supports screener rank rebalance, factor-rule strategy and event-risk filtering.
- Execution supports A-share T+1, 100-share lots, no shorting, suspended days, limit up/down, costs, slippage and volume caps.
- Portfolio outputs daily `PortfolioState` and supports position sizing, cash reserve, max positions and stops.
- Metrics avoid division-by-zero and include return, annualized return, max drawdown, Sharpe, Sortino, Calmar, win rate, turnover, costs and benchmark/excess fields.
- Optimizer and walk-forward APIs are available.
- Storage can save, load, list, delete and export runs.
- API responses follow the V3.19 shape with `ok`, `run_id`, `data`, `metrics`, `errors`, `warnings`, `cache_status`.
- `/backtest` remains compatible with existing UI tests; `/paper` is reserved and visible.
- Every output is marked `研究辅助，不构成投资建议`.

## Validation Commands

```bash
python -m compileall -q quant_data
pytest -q
```

## Expected Residual Risk

- Historical data source quality still depends on upstream providers and local cache state.
- Real intraday fills, auction microstructure and broker queue priority are approximated.
- Paper trading is intentionally virtual and cannot prove real-market fillability.
