from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_market_health_api_and_pages_show_cache_status():
    client = TestClient(api.app)
    health = client.get("/api/market/health").json()
    assert health["ok"] is True
    assert "cache_state" in health
    assert "market_session" in health
    assert "sources" in health

    cache = client.get("/api/cache/status").json()
    assert cache["ok"] is True
    assert "cache_status" in cache
    assert any(x["kind"] == "kline_cache" for x in cache["items"])

    assert "缓存状态" in client.get("/cache").text
    assert "数据源健康" in client.get("/health").text
