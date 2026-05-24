from fastapi.testclient import TestClient

from quant_data import api


def test_pages_render_cache_first_and_background_refresh_controls():
    client = TestClient(api.app)
    ui = client.get("/ui").text
    assert "restoreWatchlistState" in ui
    assert "background/refresh/watchlist" in ui
    assert "using local quote cache" in ui

    screener = client.get("/screener").text
    assert "已先显示本地筛选缓存" in screener
    assert "previous rows preserved" in screener

    info = client.get("/info?symbol=300274").text
    assert "已先显示本地信息缓存" in info
    assert "分析失败，保留当前缓存内容" in info


def test_background_refresh_endpoints_do_not_block_main_page(monkeypatch):
    monkeypatch.setattr(api.background_cache_service, "mark_refresh", lambda kind, **extra: {"ok": True, "kind": kind, "non_blocking": True, **extra})
    monkeypatch.setattr(api, "info_analyze", lambda symbol, **kwargs: {"snapshot_id": "mock", "cache_status": {"status": "hit"}, "used_snapshot": True})
    client = TestClient(api.app)
    assert client.post("/api/background/refresh/screener").json()["non_blocking"] is True
    assert client.post("/api/background/refresh/info/300274").json()["non_blocking"] is True
