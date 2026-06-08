# V3.23 Chart Markers

Marker sources:

- Strategy signals: buy, sell, reduce, avoid and risk block.
- Orders: submitted, needs confirmation, rejected and cancelled.
- Fills: buy fill, sell fill and partial fill.
- Risk markers: stale data, max position, limit-up/limit-down and major negative news.
- Behavior risk: fake breakout, high-volume stall, VWAP/MA20 break, late-session selloff and related public OHLCV signals.

API:

- `GET /api/chart/{symbol}/markers`
- `POST /api/chart/{symbol}/markers/rebuild`
- `GET /api/backtest/v323/runs/{run_id}/markers`
- `GET /api/realtime-paper/sessions/{session_id}/markers`

Every marker contains source references and explanation fields. If Level-2 data is unavailable, spoofing/cancel and main-force conclusions must remain low-confidence observations or missing.
