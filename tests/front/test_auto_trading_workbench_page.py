from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "V3.23 / Full Auto Trading Core" in html
    assert "真实券商 / QMT / PTrade 状态" in html
    assert "V3.23 会话详情" in html
    assert "/api/live-broker/status" in html
    assert "/api/realtime-paper/sessions/start" in html
    assert "/api/realtime-paper/sessions/" in html
    assert "/api/data-center/status" in html
