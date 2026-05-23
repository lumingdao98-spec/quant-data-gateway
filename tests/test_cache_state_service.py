from __future__ import annotations

from quant_data.services.cache_state_service import CacheStateService


def test_cache_state_write_read_stale_and_clear(tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")

    status = svc.put("screener_snapshot", "screen-1", {"results": [{"symbol": "300274"}]}, ttl_seconds=30)
    assert status["status"] == "refreshed"
    cached = svc.get("screener_snapshot", "screen-1")
    assert cached.data["results"][0]["symbol"] == "300274"
    assert cached.cache_status["status"] == "hit"

    svc.put("quote_cache", "300274", {"quote": {"last": 88.8}}, ttl_seconds=-1, symbol="300274")
    stale = svc.get("quote_cache", "300274", allow_stale=True)
    assert stale.data["quote"]["last"] == 88.8
    assert stale.cache_status["status"] == "stale"

    overview = svc.overview()
    kinds = {x["kind"] for x in overview["items"]}
    assert {"screener_snapshot", "info_snapshot", "kline_cache", "quote_cache", "global_news_cache"} <= kinds

    assert svc.clear(kind="quote_cache", key="300274") == 1
    assert svc.get("quote_cache", "300274").data is None
