from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_has_default_score_sort_and_clickable_headers():
    html = TestClient(api.app).get("/screener").text
    assert "sortKey='total_score'" in html
    assert "sortDir=-1" in html
    assert "function setSort" in html
    assert "onclick=\"setSort('" in html
    for key in ["total_score", "manual_review_score", "last", "change_pct", "amount", "turnover", "volume_ratio", "pe", "pb", "market_cap", "ma20_deviation", "risk_penalty"]:
        assert key in html


def test_screener_has_sort_dropdown_modes_and_compact_first_screen():
    html = TestClient(api.app).get("/screener").text
    for label in ["综合分优先", "低位优先", "资金强度优先", "技术趋势优先", "信息面优先", "行为风险低优先"]:
        assert label in html
    assert "const compact=['代码','名称','等级','综合分','复核分','最新价','涨跌幅','候选通道','成交额','换手率','量比','PE/PB','市值风格','行为风险','操作']" in html
