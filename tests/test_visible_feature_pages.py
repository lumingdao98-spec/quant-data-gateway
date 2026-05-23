from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_visible_feature_pages_are_non_blank_and_v318():
    client = TestClient(api.app)
    for path in ["/screener", "/info?symbol=300274&name=Sungrow", "/ui", "/chart/300750?frame=1d", "/wordsource", "/technical/300750", "/health", "/cache"]:
        res = client.get(path)
        assert res.status_code == 200, path
        text = res.text
        assert len(text) > 200, path
        assert "V3.18" in text, path
        assert "traceback" not in text.lower(), path
        assert "V3.17" not in text, path


def test_visible_pages_include_core_containers_and_cache_state():
    client = TestClient(api.app)
    assert "cacheHint" in client.get("/screener").text
    assert "cacheStateBox" in client.get("/info?symbol=300274").text
    assert "behaviorMarkerList" in client.get("/chart/300750?frame=1d").text
    assert "缓存状态" in client.get("/cache").text
    assert "数据源健康" in client.get("/health").text
