# V3.23 Live Trading Safety

True broker orders are blocked unless all checks pass:

1. Broker adapter connected and supported.
2. `FEATURE_LIVE_BROKER=true`.
3. `LIVE_TRADING_ENABLED=true`.
4. Kill switch is off.
5. Symbol is allowed by whitelist when a whitelist is configured.
6. Order value is below `MAX_LIVE_ORDER_VALUE`.
7. Score provenance exists.
8. Data freshness is acceptable.
9. Risk gateway approves.
10. User confirmation exists when `ORDER_CONFIRM_REQUIRED=true`.

Default behavior is safe rejection. The system must never silently turn a paper order into a live broker order.
