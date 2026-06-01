from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_default_filters_excluded_until_debug_view():
    html = TestClient(api.app).get("/screener").text
    assert "function isExcludedRow" in html
    assert "tableMode==='compact'?rows.filter" in html
    assert "完整视图显示全部" in html
    assert "debugBtn" in html
