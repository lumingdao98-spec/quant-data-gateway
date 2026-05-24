from fastapi.testclient import TestClient

from quant_data import api
from quant_data.services.watchlist_service import WatchlistService


def test_watchlist_service_persists_to_json(tmp_path):
    path = tmp_path / "watchlist.json"
    svc = WatchlistService(path)
    svc.set(["300750", "600519"])
    assert "300750" in WatchlistService(path).list()["symbols"]
    assert path.exists()


def test_watchlist_api_uses_backend_persistence(monkeypatch, tmp_path):
    svc = WatchlistService(tmp_path / "watchlist.json")
    monkeypatch.setattr(api, "watchlist_service", svc)
    client = TestClient(api.app)
    saved = client.post("/api/watchlist/set?symbols=300750,600519").json()
    assert saved["ok"] is True
    loaded = client.get("/api/watchlist").json()
    assert loaded["data"]["symbols"] == ["300750", "600519"]


def test_ui_has_new_tab_detail_and_server_watchlist_sync():
    html = TestClient(api.app).get("/ui").text
    assert "openStandaloneChart" in html
    assert "/api/watchlist" in html
    assert "quant_watchlist_symbols" in html
