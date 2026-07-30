from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_info_page_has_broad_default_filter_and_clear_button():
    html = TestClient(api.app).get("/info?symbol=300274&name=Sungrow").text
    assert "include_unknown_date" in html
    assert "清空过滤条件" in html
    assert "$('unknown').value='true'" in html
    assert "当前过滤条件导致 0 条" in html
