from fastapi.testclient import TestClient

from quant_data import api


def test_strategy_library_api_returns_fixed_contract():
    js = TestClient(api.app).get("/api/strategy/library").json()
    assert js["ok"] is True
    assert isinstance(js["data"], list) and js["data"]
    assert isinstance(js["default_keys"], list)
    assert "errors" in js


def test_strategy_library_api_falls_back_on_exception(monkeypatch):
    monkeypatch.setattr(api.strategy_library_service, "list", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    js = TestClient(api.app).get("/api/strategy/library").json()
    assert js["ok"] is True
    assert {x["key"] for x in js["data"]} >= {"low_repair", "risk_penalty", "position_stop"}
    assert "fallback_strategy_library_used" in js["errors"]


def test_frontend_strategy_fallback_is_not_infinite_loading():
    html = TestClient(api.app).get("/screener").text
    assert "FALLBACK_STRATEGIES" in html
    assert "AbortController" in html
    assert "setTimeout(()=>ctl.abort(),3000)" in html
    assert "仍可开始筛选" in html
