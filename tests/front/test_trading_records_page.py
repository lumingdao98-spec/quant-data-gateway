from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_page_visible():
    html = TestClient(api.app).get("/trading-records").text

    assert "统一交易记录 V3.23" in html
    assert "累计金额" in html
    assert "累计盈亏" in html
    assert "费用" in html
    assert "导出JSON" in html
    assert "display_amount" in html
