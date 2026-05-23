from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_technical_factor_page_visible():
    html = TestClient(api.app).get("/technical/300750").text
    assert "V3.18" in html
    assert "技术因子矩阵" in html
    assert "/api/technical/factors/300750" in html
    assert "缓存状态" in html
