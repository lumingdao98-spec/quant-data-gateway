from fastapi.testclient import TestClient

from quant_data import api


class _SectorService:
    def snapshot(self, **kwargs):
        return {
            "ok": True,
            "items": [{"board_code": "BK0001", "board_name": "测试板块", "strength_score": 78}],
            "received": kwargs,
        }

    def history(self, **kwargs):
        return {"ok": True, "items": [], "received": kwargs}


def test_sector_mainline_api_exposes_session_and_filters(monkeypatch):
    monkeypatch.setattr(api, "sector_mainline_service", _SectorService())
    client = TestClient(api.app)

    response = client.get("/api/market/sectors/mainline?limit=12&include_concept=false&force=true")
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["board_name"] == "测试板块"
    assert body["received"]["limit"] == 12
    assert body["received"]["include_concept"] is False
    assert "can_refresh" in body["received"]

    history = client.get("/api/market/sectors/history?days=7&limit=10").json()
    assert history["received"] == {"days": 7, "limit": 10}
