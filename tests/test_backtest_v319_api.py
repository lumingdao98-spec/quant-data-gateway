from fastapi.testclient import TestClient

import quant_data.api as api


def _market_data(count: int = 80) -> list[dict]:
    return [
        {
            "symbol": "600438",
            "date": f"2025-04-{(i % 28) + 1:02d}" if i < 28 else f"2025-05-{((i - 28) % 28) + 1:02d}" if i < 56 else f"2025-06-{((i - 56) % 28) + 1:02d}",
            "open": 10 + i * 0.05,
            "high": 10.3 + i * 0.05,
            "low": 9.8 + i * 0.05,
            "close": 10.1 + i * 0.05,
            "volume": 1_000_000,
        }
        for i in range(count)
    ]


def test_v319_backtest_post_run_result_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "backtest_storage_v319", api.BacktestStorage(tmp_path))
    client = TestClient(api.app)
    payload = {
        "symbols": ["600438"],
        "strategy": "factor_rule_strategy",
        "warmup_bars": 10,
        "market_data": {"600438": _market_data()},
    }
    data = client.post("/api/backtest/run", json=payload).json()

    assert data["ok"] is True
    assert data["run_id"]
    assert "metrics" in data
    assert data["errors"] == []
    assert "cache_status" in data
    loaded = client.get(f"/api/backtest/result/{data['run_id']}").json()
    assert loaded["ok"] is True
    report = client.get(f"/api/backtest/report/{data['run_id']}").json()
    assert report["ok"] is True
    assert "研究辅助" in report["data"]["disclaimer"]


def test_v319_optimize_walk_forward_paper_and_pages():
    client = TestClient(api.app)
    market_data = {"600438": _market_data(100)}

    opt = client.post("/api/backtest/optimize", json={"symbols": ["600438"], "warmup_bars": 10, "market_data": market_data, "param_grid": {"buy_score": [55, 60]}}).json()
    assert opt["ok"] is True
    assert opt["data"]
    wf = client.post("/api/backtest/walk-forward", json={"symbols": ["600438"], "warmup_bars": 10, "market_data": market_data, "train_size": 40, "test_size": 20}).json()
    assert wf["ok"] is True
    assert "stability_score" in wf["metrics"]

    html = client.get("/paper").text
    assert "纸面交易系统 V3.19" in html
    assert "研究辅助，不构成投资建议" in html
    order = client.post("/api/paper/signal", json={"symbol": "600438", "date": "2025-01-01", "action": "buy", "score": 80, "target_weight": 0.2}).json()
    assert order["ok"] is True
    state = client.get("/api/paper/state").json()
    assert state["ok"] is True
