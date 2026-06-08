from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_page_visible():
    html = TestClient(api.app).get("/trading-records").text

    assert "统一交易记录 V3.23" in html
