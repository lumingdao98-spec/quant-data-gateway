from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_js_clears_detail_when_rows_empty_and_restores_selection():
    html = TestClient(api.app).get("/screener").text
    assert "renderDetail(null)" in html
    assert "Snapshot has no rows" in html
    assert "restoreSelection" in html
    assert "rows[0].symbol" in html
    assert "previous rows preserved" in html
