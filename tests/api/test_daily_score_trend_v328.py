from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_daily_score_run_only_scores_and_never_creates_orders(monkeypatch):
    targets = [
        {"symbol": "300750", "mode": "realtime_paper", "strategy_family": "swing"},
        {"symbol": "600519", "mode": "live", "strategy_family": "long_term"},
    ]
    saved: list[dict] = []
    monkeypatch.setattr(api, "_daily_score_targets", lambda limit=80: targets[:limit])
    monkeypatch.setattr(
        api,
        "_daily_score_snapshot",
        lambda target, refresh, decision_time: {
            **target,
            "score_date": decision_time.date().isoformat(),
            "final_score": 65.0,
        },
    )
    monkeypatch.setattr(
        api.score_history_service,
        "save_daily_snapshots",
        lambda rows, score_date=None: saved.extend(rows) or len(rows),
    )
    monkeypatch.setattr(api.trading_store_v323, "put", lambda *args, **kwargs: None)

    result = api._run_daily_score_snapshots(force=True, refresh=False, limit=80)

    assert result["status"] == "complete"
    assert result["created"] == 2
    assert result["orders_created"] == 0
    assert result["broker_submitted"] is False
    assert {row["symbol"] for row in saved} == {"300750", "600519"}


def test_score_trend_preserves_a_real_zero_score(monkeypatch):
    monkeypatch.setattr(api.score_history_service, "history", lambda symbol, days=90: [])
    monkeypatch.setattr(api.score_history_service, "daily_history", lambda symbol, days=90, mode="": [])
    monkeypatch.setattr(
        api.trading_store_v323,
        "list",
        lambda table, **kwargs: [
            {
                "symbol": "300750",
                "mode": "realtime_paper",
                "decision_time": "2026-08-25T10:00:00",
                "final_score": 0.0,
                "final_trade_score": 73.0,
            }
        ],
    )
    monkeypatch.setattr(api, "_daily_score_scheduler_status", lambda: {"enabled": True})

    result = api._score_trend_payload("300750", days=30)

    assert result["count"] == 1
    assert result["data"][0]["final_score"] == 0.0


def test_daily_score_and_database_management_endpoints_are_visible():
    client = TestClient(api.app)

    assert client.get("/api/score/daily/status").status_code == 200
    assert client.get("/api/score/trend/300750?days=30").status_code == 200
    assert client.get("/api/data-center/databases?quick_check=false").status_code == 200
    assert client.post("/api/data-center/databases/not-allowed/checkpoint", json={}).status_code == 404
