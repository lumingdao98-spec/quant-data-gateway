from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar


def _bars(symbol: str = "300750", count: int = 120) -> list[Bar]:
    base = datetime(2026, 1, 1)
    rows = []
    for idx in range(count):
        close = 20 + idx * 0.1
        rows.append(
            Bar(
                symbol=symbol,
                frame="1d",
                ts=base + timedelta(days=idx),
                open=close * 0.99,
                high=close * 1.02,
                low=close * 0.98,
                close=close,
                volume=1_000_000 + idx * 3000,
                amount=close * (1_000_000 + idx * 3000),
                source="unit",
            )
        )
    return rows


def test_chinese_docs_keep_try_it_out_link_and_parameter_explanations():
    html = TestClient(api.app).get("/docs-cn").text

    assert "量化数据网关 API 文档" in html
    assert "/docs API 调试页" in html
    assert "常用参数中文说明" in html
    assert "market_weight" in html
    assert "position_sizing" in html


def test_strategy_library_returns_full_strategy_set():
    data = TestClient(api.app).get("/api/strategy/library").json()

    assert data["ok"] is True
    assert len(data["data"]) >= 55
    assert len(data["default_keys"]) >= 8
    assert any(item["key"] == "macro_liquidity" for item in data["data"])
    assert any(item["key"] == "fake_order_cancel_watch" for item in data["data"])


def test_v322_readiness_and_market_rules_endpoints():
    client = TestClient(api.app)

    ready = client.get("/api/backtest/v322/readiness").json()
    assert ready["ok"] is True
    assert ready["capabilities"]["score_provenance"] is True
    assert ready["capabilities"]["paper_only_no_broker"] is True

    rules = client.get("/api/market-rules/profiles?symbol=300750&asof=2026-06-01").json()
    assert rules["ok"] is True
    assert rules["count"] >= 5
    assert rules["resolved"]["profile_id"] == "SZSE_CHINEXT"


def test_historical_snapshot_endpoint_uses_service_bars(monkeypatch):
    monkeypatch.setattr(api.service, "get_kline", lambda symbol, *a, **k: _bars(symbol, 100))

    data = TestClient(api.app).get(
        "/api/screener/historical-snapshot?symbols=300750,600438&trade_date=2026-03-10&decision_time=2026-03-10%2015:05:00"
    ).json()

    assert data["ok"] is True
    snapshot = data["data"]
    assert snapshot["row_count"] == 2
    assert snapshot["immutable_hash"]
    assert all(row["asof_time"] == "2026-03-10 15:05:00" for row in snapshot["rows"])


def test_realtime_paper_confirmation_api_roundtrip():
    task = api.realtime_paper_engine_v321.human_confirm_queue.enqueue(
        symbol="300750",
        action="buy",
        reason="unit confirm",
    )
    client = TestClient(api.app)

    pending = client.get("/api/realtime-paper/confirmations").json()
    assert pending["ok"] is True
    assert any(row["task_id"] == task.task_id for row in pending["data"])

    approved = client.post(f"/api/realtime-paper/confirmations/{task.task_id}/approve", json={"operator": "tester"}).json()
    assert approved["ok"] is True
    assert approved["data"]["status"] == "approved"
