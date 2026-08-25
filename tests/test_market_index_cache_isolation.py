from __future__ import annotations

from datetime import datetime

from quant_data.cache import MarketCache
from quant_data.models import Bar


def test_index_cache_key_does_not_collide_with_stock_000001(tmp_path):
    cache = MarketCache(tmp_path / "market.sqlite")
    ts = datetime(2026, 8, 25)
    cache.save_bars(
        [
            Bar("000001", "1d", ts, 10, 11, 9, 10.5, 100, 1000, source="stock"),
            Bar("idx:sh000001", "1d", ts, 3300, 3350, 3290, 3340, 100, 1000, source="index"),
        ]
    )

    stock = cache.get_bars("000001", "1d")
    index = cache.get_bars("idx:sh000001", "1d")

    assert stock[-1].close == 10.5
    assert index[-1].close == 3340
    assert stock[-1].source == "stock"
    assert index[-1].source == "index"

