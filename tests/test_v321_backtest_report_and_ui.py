from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import AssetType, Bar, Quote


def _bars(count: int = 140) -> list[Bar]:
    base = datetime(2025, 1, 1)
    return [
        Bar(
            symbol="300750",
            frame="1d",
            ts=base + timedelta(days=i),
            open=50 + i * 0.1,
            high=51 + i * 0.1,
            low=49 + i * 0.1,
            close=50.5 + i * 0.1,
            volume=1_000_000 + i * 1000,
            amount=(50.5 + i * 0.1) * (1_000_000 + i * 1000),
            source="unit",
        )
        for i in range(count)
    ]


def _quote() -> Quote:
    return Quote(
        "300750",
        "宁德时代",
        datetime(2026, 6, 1, 10, 0),
        65,
        64,
        64,
        66,
        63,
        1_000_000,
        65_000_000,
        1,
        1.2,
        asset_type=AssetType.STOCK,
        source="unit",
    )


def test_backtest_api_exposes_v321_report_fields(monkeypatch):
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: _quote())
    monkeypatch.setattr(api.service, "get_kline", lambda *a, **k: _bars())

    result = TestClient(api.app).get(
        "/api/backtest/run?symbol=300750&strategy=combo_signal&strategy_combo=score_driven,ma_cross"
        "&position_sizing=atr_risk&horizon=short_term&compound_returns=false&atr_risk_pct=1.5&limit=140"
    ).json()["data"]

    assert result["params"]["position_sizing"] == "atr_risk"
    assert result["params"]["horizon"] == "short_term"
    assert result["compound_returns"] is False
    assert "position_sizing_config" in result
    assert "horizon_config" in result
    assert "expectancy" in result["metrics"]
    assert "position_sizing_attribution" in result["metrics"]
    assert "filter_attribution" in result["metrics"]
    assert "horizon_attribution" in result["metrics"]


def test_v321_ui_entry_points_are_visible():
    client = TestClient(api.app)
    backtest_html = client.get("/backtest").text
    screener_html = client.get("/screener").text
    paper_html = client.get("/realtime-paper").text

    assert "sizingMode" in backtest_html
    assert "compoundReturns" in backtest_html
    assert "position_sizing" in backtest_html
    assert "backtestCurrentScreener" in screener_html
    assert "startRealtimeFromScreener" in screener_html
    assert "viewThreeDimSignal" in screener_html
    assert "/api/realtime-paper/start" in paper_html
    assert "paper_only" in paper_html
