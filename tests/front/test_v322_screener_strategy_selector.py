import json
import re

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
