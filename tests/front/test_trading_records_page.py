from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_page_visible():
    html = TestClient(api.app).get("/trading-records").text

    assert "\u7edf\u4e00\u4ea4\u6613\u8bb0\u5f55 V3.23" in html
    assert "\u7edf\u4e00\u4ea4\u6613\u8bb0\u5f55 V3.26" in html
    assert "\u7d2f\u8ba1\u91d1\u989d/\u5e02\u503c" in html
    assert "\u7d2f\u8ba1\u76c8\u4e8f" in html
    assert "\u8d39\u7528" in html
    assert "\u5bfc\u51faJSON" in html
    assert "display_amount" in html
    assert "display_pnl_pct" in html
    assert "display_cost_price" in html
