from fastapi.testclient import TestClient

import quant_data.api as api


def test_data_center_page_exposes_truthful_readiness_and_explicit_refresh_controls():
    html = TestClient(api.app).get("/data-center").text

    assert "数据中心 V3.28" in html
    assert "/api/data-center/decision-readiness" in html
    assert "/api/data-center/refresh" in html
    assert "/api/data-center/source-errors" in html
    assert "只有显式刷新会访问外部数据源" in html
    assert "基本面 0 分不会自动补齐" in html
    assert "信息来源健康度" in html
    assert "SQLite 数据库管理" in html
    assert "/api/data-center/databases" in html
    assert "WAL 检查点" in html
    assert "刷新此项" in html
    assert "overflow-wrap:anywhere" in html


def test_workbench_can_refresh_each_decision_dimension_without_creating_orders():
    html = TestClient(api.app).get("/auto-trading").text

    assert "refreshDecisionDimension" in html
    assert "'/api/data-center/refresh'" in html
    assert "fundamental:'fundamentals'" in html
    assert "fund_flow:'capital'" in html
    assert "market:'global_market'" in html
