from fastapi.testclient import TestClient

import quant_data.api as api


def test_live_trading_page_visible():
    html = TestClient(api.app).get("/live-trading").text

    assert "真实自动交易 V3.23" in html
    assert "真实自动交易 V3.26" in html
    assert "默认禁用" in html
    assert "多股票实盘观察池" in html
    assert "实盘策略目录" in html
    assert "载入实盘分时策略" in html
    assert "使用全部可用策略" in html
    assert "LIVE_INTRADAY_STRATEGIES" in html
    assert "fake_order_cancel_watch" in html
    assert "orderbook_imbalance_watch" in html
    assert "global_commodity_map" in html
    assert "watchRows" in html
    assert "账户与持仓" in html
    assert "浮盈亏" in html
    assert "盈亏%" in html
    assert "实盘委托与成交" in html
    assert "真实委托/成交" in html
    assert "待人工确认" in html
    assert "预检查/拦截" in html
    assert "打开统一记录" in html
    assert "确认队列" in html
    assert "batchPreview" in html
    assert "selected_strategies" in html
    assert "/api/auto-trading/config" in html
    assert "/api/live/orders/preview" in html
    assert "/api/live/orders/preview-batch" in html
    assert "/api/strategy/library" in html
    assert "/api/live/positions" in html
    assert "/api/live/trades" in html
    assert "/api/live/orders?scope=all" in html
    assert "display_pnl_pct" in html
    assert "display_cost_price" in html
    assert "未连接真实账户" in html
    assert "预检查不会计入这里" in html
    assert "同花顺人工委托伴随" in html
    assert "/api/integrations/tonghuashun/status" in html
    assert "/api/integrations/tonghuashun/reminders" in html
    assert "自动下单：不支持" in html
