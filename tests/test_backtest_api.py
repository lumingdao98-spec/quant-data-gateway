from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import AssetType, Bar, Quote


def _bars(count: int = 120) -> list[Bar]:
    base = datetime(2025, 1, 1)
    rows = []
    for i in range(count):
        price = 30 + i * 0.12
        rows.append(
            Bar(
                symbol="300750",
                frame="1d",
                ts=base + timedelta(days=i),
                open=price * 0.996,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=900_000 + i * 800,
                amount=price * (900_000 + i * 800),
                source="unit:qfq",
            )
        )
    return rows


def _quote() -> Quote:
    return Quote(
        "300750",
        "宁德时代",
        datetime(2026, 5, 28, 10, 0),
        188.0,
        186.0,
        187.0,
        190.0,
        185.0,
        1_000_000,
        188_000_000,
        2.0,
        1.08,
        asset_type=AssetType.STOCK,
        source="unit",
    )


def test_backtest_api_run_uses_local_bars(monkeypatch):
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars())

    data = TestClient(api.app).get("/api/backtest/run?symbol=300750&strategy=score_driven&limit=120&buy_score=55&sell_score=45").json()

    assert data["ok"] is True
    result = data["data"]
    assert result["symbol"] == "300750"
    assert result["strategy"] == "score_driven"
    assert result["final_equity"] > 0
    assert "buy_hold_return_pct" in result
    assert "excess_return_pct" in result
    assert "equity_curve" in result
    assert "score_series" in result
    assert "score_formula" in result
    assert "kline" in result
    assert "markers" in result
    assert "anomaly_markers" in result


def test_backtest_page_is_visible():
    html = TestClient(api.app).get("/backtest").text

    assert "交易回测系统" in html
    assert "/api/backtest/run" in html
    assert "手续费" in html
    assert "滑点" in html
    assert "日评分驱动" in html
    assert "买卖点" in html
    assert "volumeChart" in html
    assert "signalChart" in html
    assert "100分口径" in html
    assert "异常点" in html
    assert "买卖明细" in html
    assert "收益诊断" in html
    assert "比较策略收益" in html
