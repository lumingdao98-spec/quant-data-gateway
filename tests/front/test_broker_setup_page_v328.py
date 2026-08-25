from fastapi.testclient import TestClient

import quant_data.api as api


def test_broker_setup_page_is_a_guided_safe_configuration_surface():
    html = TestClient(api.app).get("/broker-setup").text

    assert "券商接入向导" in html
    assert "QMT" in html
    assert "PTrade" in html
    assert "同花顺" in html
    assert "HTTP" in html
    assert "/api/live-broker/setup/validate" in html
    assert "/api/integrations/tonghuashun/config" in html
    assert "/api/integrations/tonghuashun/launch" in html
    assert "只读校验" in html
    assert "真实交易默认关闭" in html
    assert "系统不会用鼠标脚本代替券商 API" in html


def test_workbench_exposes_broker_setup_and_daily_score_trend():
    html = TestClient(api.app).get("/auto-trading").text

    assert "/broker-setup" in html
    assert 'id="scoreTrendCanvas"' in html
    assert "/api/score/trend/" in html
    assert "/api/score/daily/status" in html
    assert "/api/score/daily/run" in html
    assert "只评分和留痕" in html or "评分走势" in html
