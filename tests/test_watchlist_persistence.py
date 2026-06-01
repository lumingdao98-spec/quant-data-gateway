from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.watchlist_service import WatchlistService


def test_watchlist_is_persisted_on_backend(monkeypatch, tmp_path):
    svc = WatchlistService(tmp_path / "watchlist.json")
    monkeypatch.setattr(api, "watchlist_service", svc)
    client = TestClient(api.app)

    saved = client.post("/api/watchlist/set?symbols=300750,600519").json()
    loaded = client.get("/api/watchlist").json()

    assert saved["ok"] is True
    assert loaded["data"]["symbols"] == ["300750", "600519"]
    assert (tmp_path / "watchlist.json").exists()


def test_ui_syncs_local_and_backend_watchlist_without_blank_reload():
    html = TestClient(api.app).get("/ui").text
    assert "/api/watchlist" in html
    assert "/api/watchlist/set" in html
    assert "restoreWatchlistState" in html
    assert "后台刷新" in html
    assert "window.open('/chart/'" in html
