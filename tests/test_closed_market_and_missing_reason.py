from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import AssetType, Quote


def _quote(symbol: str = "300274", asset_type: AssetType = AssetType.STOCK) -> Quote:
    return Quote(
        symbol=symbol,
        name="Unit",
        ts=datetime(2026, 5, 23, 16, 0),
        last=10,
        pre_close=10,
        open=10,
        high=10,
        low=10,
        volume=1000,
        amount=1000000,
        change=0,
        change_pct=0,
        asset_type=asset_type,
        source="unit",
    )


def test_orderbook_closed_market_explains_no_level1_book(monkeypatch):
    monkeypatch.setattr(api, "calendar_status", lambda symbol=None, market=None: {"data": {"status": "closed", "label": "\u4f11\u5e02", "can_refresh": False}})
    monkeypatch.setattr(api.service, "get_order_book", lambda symbol, allow_external=False: None)

    data = TestClient(api.app).get("/api/orderbook/300274").json()
    assert data["skipped_external"] is True
    assert data["note"] == "\u4f11\u5e02\u65e0\u76d8\u53e3"


def test_orderbook_open_market_explains_missing_public_level2_book(monkeypatch):
    monkeypatch.setattr(api, "calendar_status", lambda symbol=None, market=None: {"data": {"status": "morning", "label": "\u4ea4\u6613\u4e2d", "can_refresh": True}})
    monkeypatch.setattr(api.service, "get_order_book", lambda symbol, allow_external=True: None)

    data = TestClient(api.app).get("/api/orderbook/300274").json()

    assert data["skipped_external"] is False
    assert "Level-2" in data["note"]
    assert "\u516c\u5f00\u884c\u60c5\u6e90" in data["note"]


def test_missing_quote_metrics_have_explicit_reasons(monkeypatch):
    monkeypatch.setattr(api.service.providers, "get_quote", lambda symbol: (_ for _ in ()).throw(RuntimeError("down")))
    enriched = api.service.enrich_quote_metrics(_quote())
    reasons = " ".join(enriched.metric_missing_reasons or [])

    assert "PE" in reasons
    assert "PB" in reasons
    assert "\u6362\u624b\u7387" in reasons
    assert "\u5e02\u503c" in reasons


def test_etf_pe_pb_are_marked_not_applicable(monkeypatch):
    monkeypatch.setattr(api.service.providers, "get_quote", lambda symbol: (_ for _ in ()).throw(RuntimeError("down")))
    enriched = api.service.enrich_quote_metrics(_quote("510300", AssetType.ETF))
    reasons = " ".join(enriched.metric_missing_reasons or [])

    assert "ETF" in reasons
    assert "PE" in reasons
    assert "PB" in reasons
