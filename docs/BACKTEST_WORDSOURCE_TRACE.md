# V3.19 WordSource Trace

Source document: `docs/word_sources/炒股-量化相关.docx`

The V3.19 backtest foundation was traced against the real Word source rather than inferred from the old UI. The document emphasizes that a valid quant workflow needs data preparation, strategy signals, simulated trading, costs, risk metrics, optimization and execution constraints.

## Trace Table

| Source paragraph | Source requirement | V3.19 implementation |
| --- | --- | --- |
| 188-195 | 回测与优化要素 include data quality, 手续费与滑点, risk control, performance indicators and real-market constraints. | `data_loader.py`, `execution.py`, `risk.py`, `engine.py`. |
| 201-202 | Define backtest period and simulate buy/sell operations; record time, price and quantity. | `BacktestConfig.start/end`; `Order`, `Fill`, `Trade`; `BacktestEngine.run`. |
| 203-206 | Parameter optimization should use grid/random search and evaluate risk-return such as Sharpe and max drawdown. | `optimizer.py`; `risk.calculate_metrics`; `walk_forward.py`. |
| 212-215 | Data preparation must collect OHLCV and handle missing/anomalous values. | `BacktestDataLoader.quality_report`. |
| 216-221 | Strategy rules generate buy/sell/hold signals; simulated trades should update equity and include transaction costs. | `SignalAdapter`, `PortfolioManager`, `ExecutionSimulator`. |
| 222-238 | Metrics include cumulative return, annualized return, volatility, 最大回撤, 夏普 and Sortino. | `risk.calculate_metrics`. |
| 243-251 | Optimization includes grid search, random search, strategy adjustment, data quality and feature engineering. | `optimizer.py`, `walk_forward.py`, `signal_adapter.py`. |
| 252-265 | Risk management includes Sharpe, max drawdown, stop loss, take profit and position management. | `risk.py`, `portfolio.stop_orders`, `BacktestConfig.stop_loss_pct/take_profit_pct/max_single_position_pct`. |
| 290-298 | Execution must understand APIs and order types such as market/limit/stop, but security and compliance matter. | `paper_broker.py` is paper-only; no real broker API is connected. |

## Mapping Notes

- The source document is conceptual and not A-share-specific. V3.19 extends it with local market rules: T+1, 100-share lots, no shorting, limit up/down blocking, suspended/zero-volume blocking, volume-limit partial fills, stamp tax and transfer fee.
- The source document calls for optimization, but warns through risk sections that performance alone is insufficient. V3.19 therefore includes walk-forward validation and explicit warnings.
- The source document mentions real execution APIs. V3.19 intentionally implements only paper trading; real broker order submission is out of scope.

All new reports and API payloads include `研究辅助，不构成投资建议`.
