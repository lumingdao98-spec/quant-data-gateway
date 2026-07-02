from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_page_visible():
    html = TestClient(api.app).get("/live-trading").text

    assert "真实自动交易 V3.23" in html
    assert "默认禁用" in html
    assert "多股票实盘观察池" in html
    assert "实盘策略目录" in html
    assert "账户与持仓" in html
    assert "今日委托 / 成交 / 统一记录" in html
    assert "确认队列" in html
    assert "batchPreview" in html
    assert "selected_strategies" in html
    assert "/api/auto-trading/config" in html
    assert "/api/live/orders/preview" in html
    assert "/api/live/positions" in html
    assert "/api/live/trades" in html
