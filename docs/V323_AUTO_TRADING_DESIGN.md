# V3.23 Full Auto Trading Core Design

V3.23 separates four user-facing modes while sharing one trading kernel:

- `/backtest`: historical, point-in-time, no realtime quote dependency and no real broker.
- `/realtime-paper`: realtime or replayed paper simulation, no real broker.
- `/live-trading`: true broker integration shell, disabled by default.
- `/trading-records`: unified records for backtest, paper and live modes.

Shared kernel modules:

- Data truth: `quant_data/data/*`
- Unified scoring: `quant_data/scoring/*`
- Strategy suitability: `quant_data/strategy/*`
- Risk and order routing: `quant_data/trading/risk_gateway.py`, `quant_data/trading/order_models.py`, `quant_data/trading/execution_router.py`
- Broker adapters: `quant_data/trading/broker/*`
- Chart markers: `quant_data/chart/*`
- Persistence: `quant_data/persistence/trading_store.py`

All modes must show `研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。`
