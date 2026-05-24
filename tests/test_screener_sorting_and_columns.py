from fastapi.testclient import TestClient

from quant_data import api


def test_screener_backend_sorts_score_desc_and_risk_later(monkeypatch):
    rows = [
        {"symbol": "A", "name": "A", "total_score": 80, "manual_review_score": 70, "behavior_score": 10, "grade": "B"},
        {"symbol": "B", "name": "B", "total_score": 90, "manual_review_score": 60, "behavior_score": 50, "grade": "B"},
        {"symbol": "C", "name": "C", "total_score": 80, "manual_review_score": 75, "behavior_score": 1, "grade": "B"},
    ]
    monkeypatch.setattr(api.screener_service, "run", lambda config: {"ok": True, "data": [dict(x) for x in rows], "result_count": 3, "errors": [], "error_count": 0})
    monkeypatch.setattr(api, "_merge_screener_item_quote_metrics", lambda item, force=False: None)
    js = TestClient(api.app).get("/api/screener/run?symbols=300750,600519&max_items=3").json()
    assert [x["symbol"] for x in js["results"]] == ["B", "C", "A"]


def test_screener_frontend_has_sort_controls_and_first_screen_columns():
    html = TestClient(api.app).get("/screener").text
    assert "默认：综合分降序" in html
    assert "低位优先" in html
    assert "行为风险低优先" in html
    for label in ["代码", "名称", "等级", "综合分", "复核分", "最新价", "涨跌幅", "成交额", "换手率", "量比", "PE/PB", "市值风格", "行为风险", "操作"]:
        assert label in html
    assert "setSort" in html
    assert "applySortMode" in html
