from fastapi.testclient import TestClient

import quant_data.api as api


def test_auto_trading_workbench_page_visible():
    html = TestClient(api.app).get("/auto-trading").text

    assert "V3.23 / Full Auto Trading Core" in html
    assert "真实券商 / QMT / PTrade 状态" in html
    assert "V3.23 会话详情" in html
    assert "一键配置" in html
    assert "策略组合" in html
    assert "仓位模型" in html
    assert "财报/业绩预告" in html
    assert "半年报/年报窗口" in html
    assert "/api/live-broker/status" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
    assert "/api/realtime-paper/sessions/" in html
    assert "/api/data-center/status" in html
    assert "strategyCombo" in html
    assert "positionSizing" in html
    assert "maxDrawdownPct" in html


def test_chinese_docs_include_auto_trading_v323_entrypoints():
    html = TestClient(api.app).get("/docs-cn").text

    assert "自动交易 V3.23" in html
    assert "/auto-trading" in html
    assert "/api/auto-trading/config" in html
    assert "/api/auto-trading/config/one-click" in html
    assert "/api/auto-trading/start-paper" in html
