from fastapi.testclient import TestClient

import quant_data.api as api


def test_detail_page_and_chart_marker_api_visible():
    client = TestClient(api.app)

    assert client.get("/detail/300750").status_code == 200
    assert client.get("/api/chart/300750/markers").json()["ok"] is True


def test_chart_marker_api_merges_memory_and_sqlite_rows(monkeypatch):
    memory = {
        "marker_id": "memory-buy",
        "symbol": "300750",
        "mode": "live",
        "timestamp": "2026-07-22T10:00:00",
        "marker_type": "buy_order_submitted",
    }
    stored = {
        "marker_id": "stored-fill",
        "symbol": "300750",
        "mode": "realtime_paper",
        "timestamp": "2026-07-22T10:01:00",
        "marker_type": "buy_fill",
    }
    monkeypatch.setattr(api.chart_annotation_service_v323, "list_markers", lambda *args, **kwargs: [memory])
    monkeypatch.setattr(
        api.trading_store_v323,
        "list",
        lambda table, **kwargs: [stored] if table == "chart_markers" else [],
    )

    payload = TestClient(api.app).get("/api/chart/300750/markers").json()

    assert payload["count"] == 2
    assert {row["marker_id"] for row in payload["data"]} == {"memory-buy", "stored-fill"}
