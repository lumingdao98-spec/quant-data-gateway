from __future__ import annotations

import re

from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_default_layout_is_compact_and_restorable():
    html = TestClient(api.app).get("/screener").text
    compact = re.search(r"const compact=\[(.*?)\];", html)
    assert compact, "compact columns must be declared"
    assert compact.group(1).count("'") // 2 <= 16
    assert "技术摘要" not in compact.group(1)
    assert "综合诊断" not in compact.group(1)
    assert "compactBtn" in html and "fullBtn" in html and "debugBtn" in html
    assert "tableMode==='debug'?rows:rows.filter" in html
    assert "qdg_screener_snapshot_id" in html
    assert "qdg_screener_view" in html
    assert "normalizeStrategySelection" in html
    assert "syncStrategyCheckboxes" in html
    assert "本地内置策略" in html


def test_screener_right_detail_card_contains_full_sections():
    html = TestClient(api.app).get("/screener").text
    for text in ["基础行情", "估值市值", "技术状态", "资金行为", "支撑压力", "信息面快照", "缺失数据", "诊断结论"]:
        assert text in html
    assert "查看技术因子矩阵" in html
    assert "behavior_tags" in html
    assert "cache_status" in html
