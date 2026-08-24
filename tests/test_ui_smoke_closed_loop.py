from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_ui_smoke_closed_loop_pages():
    client = TestClient(api.app)
    pages = [
        ("/screener", ["V3.26", "cacheHint", "恢复上次筛选"]),
        ("/info?symbol=300274&name=Sungrow", ["V3.26", "cacheStateBox", "sources"]),
        ("/ui", ["V3.26", "quoteBody", "behaviorMarkerList"]),
        ("/chart/300750?frame=1d", ["V3.26", "chartLabel", "behaviorMarkerList"]),
        ("/wordsource", ["V3.18", "traceRows", "WordSource"]),
        ("/technical/300750", ["V3.18", "技术因子矩阵", "缓存状态"]),
        ("/health", ["V3.18", "数据源健康", "缓存状态"]),
        ("/cache", ["V3.18", "缓存状态", "cache/status"]),
    ]
    for path, needles in pages:
        res = client.get(path)
        assert res.status_code == 200, path
        text = res.text
        assert len(text.strip()) > 100, path
        assert "traceback" not in text.lower(), path
        assert "V3.17" not in text, path
        for needle in needles:
            assert needle in text, (path, needle)
