from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_strategy_library_api_returns_fixed_shape():
    data = TestClient(api.app).get("/api/strategy/library").json()
    assert data["ok"] is True
    assert isinstance(data["data"], list)
    assert isinstance(data["default_keys"], list)
    assert isinstance(data["errors"], list)
    assert len(data["data"]) >= 55
    assert {"低位修复", "高位追高过滤", "仓位与止损"} <= {x["name"] for x in data["data"]}
    assert {"VWAP收复", "虚假挂撤观察", "市场宽度过滤"} <= {x["name"] for x in data["data"]}


def test_strategy_library_service_failure_uses_backend_fallback(monkeypatch):
    monkeypatch.setattr(api.strategy_library_service, "list", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    data = TestClient(api.app).get("/api/strategy/library").json()
    assert data["ok"] is True
    assert len(data["data"]) >= 9
    assert data["default_keys"]
    assert any("fallback" in x.lower() for x in data["errors"])


def test_screener_frontend_has_timeout_fallback_and_can_run():
    html = TestClient(api.app).get("/screener").text
    assert "FALLBACK_STRATEGIES" in html
    assert "__FALLBACK_STRATEGIES_JSON__" not in html
    assert html.count('"key":') >= 55
    assert "虚假挂撤观察" in html
    assert "AbortController" in html
    assert "3000" in html
    assert "useFallbackStrategyLibrary" in html
    assert "runScreener()" in html
