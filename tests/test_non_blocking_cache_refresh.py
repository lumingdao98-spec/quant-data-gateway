from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_market_apis_accept_refresh_flag_without_forcing_blank_page():
    client = TestClient(api.app)
    assert client.get("/api/kline/300750?frame=1d&adjust=none&refresh=false").status_code == 200
    assert client.get("/api/detail/300750?frame=1d&refresh=false").status_code == 200
    assert client.get("/api/quotes?symbols=300750&refresh=false").status_code == 200


def test_frontend_uses_cache_first_and_background_refresh_language():
    ui = TestClient(api.app).get("/ui").text
    screener = TestClient(api.app).get("/screener").text
    assert "使用本地行情缓存" in ui
    assert "后台刷新" in ui
    assert "refresh=false" in ui or "refresh='+force" in ui
    assert "Restored local screener rows immediately" in screener
