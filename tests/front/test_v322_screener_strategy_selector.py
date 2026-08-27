import json
import re

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.screener_ui import build_screener_ui


def test_screener_page_embeds_full_strategy_fallback_for_cache_failures():
    html = build_screener_ui()

    assert "FALLBACK_STRATEGIES" in html
    assert "openStrategyModal" in html
    match = re.search(r"const FALLBACK_STRATEGIES=(\[.*?\]);", html, re.S)
    assert match is not None
    strategies = json.loads(match.group(1))
    keys = {item["key"] for item in strategies}
    assert len(strategies) >= 35
    assert {"low_position", "macro_liquidity", "position_risk"} <= keys


def test_screener_strategy_library_is_searchable_modal_and_keeps_python_draft():
    html = build_screener_ui()

    assert 'id="strategyModal"' in html
    assert 'id="strategySearch"' in html
    assert "已选策略" in html
    assert "Python 自定义" in html
    assert "toggleStrategyCard" in html
    assert "saveCustomCodeDraft" in html
    assert "quant_custom_python_strategy_draft" in html
    assert "不参与本轮筛选、回测或下单" in html


def test_custom_python_strategy_endpoint_is_validation_only_and_blocks_imports():
    client = TestClient(api.app)
    safe = client.post(
        "/api/strategy/custom/validate",
        json={"code": "def score(context):\n    return {'score': 60}"},
    ).json()
    unsafe = client.post(
        "/api/strategy/custom/validate",
        json={"code": "import os\ndef score(context):\n    return os.system('whoami')"},
    ).json()

    assert safe["ok"] is True
    assert safe["validation_only"] is True
    assert safe["execution_enabled"] is False
    assert unsafe["ok"] is False
    assert unsafe["execution_enabled"] is False
    assert unsafe["blocked_reasons"]
