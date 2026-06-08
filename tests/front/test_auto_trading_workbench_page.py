from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "V3.23 / Full Auto Trading Core" in html
    assert "真实券商 / QMT 接口" in html
    assert "/api/live-broker/status" in html
