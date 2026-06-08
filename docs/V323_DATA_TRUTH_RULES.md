# V3.23 Data Truth Rules

Hard rules:

- No fake market data.
- No random data as quote, K-line, news or broker data.
- No search result pages as news evidence.
- Baidu, 360 and Sogou search result pages are permanently disabled.
- Missing fields must be reported as missing, stale, unsupported, unauthorized or closed-market unavailable.

Every data object should carry:

- `source_id`
- `source_name`
- `source_url` or `source_ref`
- `fetched_at`
- `published_at`
- `available_at`
- `ttl_seconds`
- `stale`
- `quality_status`
- `missing_reasons`
- `raw_hash`

Backtests use point-in-time data only. Realtime paper and live trading use latest traceable data and block automatic buy when critical data is stale.
