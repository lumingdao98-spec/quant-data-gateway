from fastapi.testclient import TestClient

import quant_data.api as api


def test_trading_records_page_visible():
    html = TestClient(api.app).get("/trading-records").text

    assert "\u7edf\u4e00\u4ea4\u6613\u8bb0\u5f55 V3.23" in html
    assert "\u7edf\u4e00\u4ea4\u6613\u8bb0\u5f55 V3.26" in html
    assert "\u5b9e\u9645\u6210\u4ea4\u91d1\u989d" in html
    assert "\u5f53\u524d\u603b\u76c8\u4e8f" in html
    assert "\u7edf\u4e00\u4e8b\u4ef6\u6d41\u6c34" in html
    assert "\u6a21\u62df\u4f1a\u8bdd\u542f\u52a8" in html
    assert "\u8d39\u7528" in html
    assert "\u5bfc\u51faJSON" in html
    assert "display_amount" in html
    assert "display_pnl_pct" in html
    assert "display_cost_price" in html
    assert 'id="queryStatus"' in html
    assert "AbortController" in html
    assert "Promise.allSettled" in html
    assert "beforeunload" in html
    assert "alert('查询失败" not in html
