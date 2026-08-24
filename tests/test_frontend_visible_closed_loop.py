from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.models import Bar
from quant_data.services.cache_state_service import CacheStateService


def test_closed_loop_smoke_pages_and_cached_apis(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.save_screener_snapshot("screen-smoke", {"snapshot_id": "screen-smoke", "results": [{"symbol": "300274", "name": "Sungrow", "grade": "B", "total_score": 70}], "summary": {"result_count": 1}})
    svc.save_info_snapshot("info-smoke", "600438", {"snapshot_id": "info-smoke", "symbol": "600438", "items": [{"title": "notice"}], "source_logs": [{"source": "cache", "status": "ok"}], "score_model": {"formula": "x"}}, mode="light")
    bars = [Bar("300750", "1d", datetime(2026, 5, 1) + timedelta(days=i), 1, 2, 1, 2, 1, 1, source="cache").to_dict() for i in range(8)]
    svc.save_kline_cache("300750:1d:qfq", "300750", {"ok": True, "symbol": "300750", "frame": "1d", "adjust": "qfq", "bars": bars, "data": bars, "source": ["cache"], "fallback_chain": ["test"], "errors": [], "behavior_analysis": {}, "kline_markers": []})

    client = TestClient(api.app)
    for path in ["/screener", "/info?symbol=600438&name=TW", "/ui", "/chart/300750?frame=1d", "/wordsource", "/health", "/cache"]:
        res = client.get(path)
        assert res.status_code == 200
        text = res.text
        assert text.strip()
        assert "traceback" not in text.lower()

    assert "V3.26" in client.get("/screener").text
    assert "V3.26" in client.get("/ui").text

    assert client.get("/api/cache/screener/latest").json()["results"]
    info = client.get("/api/info/analyze/600438?name=TW&force=false&deep_refresh=false&snapshot_id=").json()
    assert info["ok"] is True
    assert info["items"]
    kline = client.get("/api/kline/300750?frame=1d&adjust=qfq").json()
    assert kline["ok"] is True
    assert kline["cache_status"]["status"] in {"hit", "stale"}
