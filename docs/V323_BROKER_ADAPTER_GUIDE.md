# V3.23 Broker Adapter Guide

Adapters:

- `DisabledBrokerAdapter`: default. Never places real orders.
- `SimulatorBrokerAdapter`: local simulator for rehearsal, still not a real broker.
- `QmtBrokerAdapter`: import guard for `xtquant`; returns `unsupported` if SDK is absent.
- `PTradeBrokerAdapter`: import guard for `ptrade`; returns `unsupported` if SDK is absent.

Environment variables:

- `FEATURE_LIVE_BROKER=false`
- `LIVE_TRADING_ENABLED=false`
- `ORDER_CONFIRM_REQUIRED=true`
- `LIVE_KILL_SWITCH=false`
- `BROKER_TYPE=disabled|simulator|qmt|ptrade`
- `TRADE_WHITELIST_SYMBOLS=300750,600438`
- `MAX_LIVE_ORDER_VALUE=50000`
- QMT: `QMT_PATH`, `QMT_ACCOUNT_ID`, `QMT_ACCOUNT_TYPE`, `QMT_SESSION_ID`
- PTrade: `PTRADE_PATH`, `PTRADE_ACCOUNT_ID`

No account, password, token, cookie or broker secret is committed to the repository.
