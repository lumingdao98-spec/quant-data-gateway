from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_page_visible():
    html = TestClient(api.app).get("/live-trading").text

    assert "真实自动交易 V3.23" in html
    assert "默认禁用" in html
