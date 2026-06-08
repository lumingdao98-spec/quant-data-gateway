from datetime import datetime, timedelta

from quant_data.data import DataFreshnessPolicy, check_data_freshness


def test_stale_data_blocks_buy_but_allows_hold_reduce_observation():
    now = datetime(2026, 6, 5, 10, 0, 0)
    old = now - timedelta(minutes=5)

    result = check_data_freshness(old, now=now, policy=DataFreshnessPolicy(ttl_seconds=30))

    assert result.stale is True
    assert result.action == "hold_reduce_only"
