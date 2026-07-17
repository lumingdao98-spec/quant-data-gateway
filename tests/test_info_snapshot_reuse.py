from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import quant_data.api as api


class MemorySnapshotStore:
    def __init__(self):
        self.saved = {}

    def read_analysis(self, symbol, key, ttl_seconds):
        return self.saved.get((symbol, key))

    def save_analysis(self, symbol, key, data, name=None):
        payload = dict(data)
        payload["saved_name"] = name
        self.saved[(symbol, key)] = payload
        return True


def _info_payload(mode="light"):
    return {
        "symbol": "601012",
        "name": "隆基绿能",
        "updated_at": datetime(2026, 5, 23, 10, 0, 0).isoformat(),
        "info_score": 66,
        "summary": "公告和F10快照已复用",
        "crawl_mode": mode,
        "news": {"count": 3, "summary": "快照新闻", "news_score": 61},
        "evidence_counts": {"news_items": 3},
    }


def test_info_detail_reuses_snapshot_without_refresh(monkeypatch):
    store = MemorySnapshotStore()
    store.save_analysis("601012", "snapshot:abc", _info_payload(), name="隆基绿能")
    monkeypatch.setattr(api.news_service, "store", store)

    def fail_analyze(*args, **kwargs):
        raise AssertionError("snapshot_id 存在时不应重新抓取")

    monkeypatch.setattr(api.info_analysis_service, "analyze", fail_analyze)
    result = api.info_analyze("601012", name="隆基绿能", snapshot_id="abc", force=False, deep_refresh=False)

    assert result["data"]["snapshot_reused"] is True
    assert result["data"]["snapshot_id"] == "abc"
    assert "筛选页快照" in result["data"]["snapshot_notice"]


def test_force_true_refreshes_snapshot(monkeypatch):
    store = MemorySnapshotStore()
    store.save_analysis("601012", "snapshot:abc", _info_payload(), name="隆基绿能")
    monkeypatch.setattr(api.news_service, "store", store)
    calls = []

    def analyze(symbol, **kwargs):
        calls.append(kwargs)
        return _info_payload(mode=kwargs.get("mode"))

    monkeypatch.setattr(api.info_analysis_service, "analyze", analyze)
    result = api.info_analyze("601012", name="隆基绿能", snapshot_id="abc", force=True, deep_refresh=False)

    assert calls
    assert calls[-1]["force"] is True
    assert calls[-1]["mode"] == "normal"
    assert result["data"]["snapshot_reused"] is False


def test_deep_refresh_enables_deep_mode(monkeypatch):
    store = MemorySnapshotStore()
    monkeypatch.setattr(api.news_service, "store", store)
    calls = []

    def analyze(symbol, **kwargs):
        calls.append(kwargs)
        return _info_payload(mode=kwargs.get("mode"))

    monkeypatch.setattr(api.info_analysis_service, "analyze", analyze)
    result = api.info_analyze("601012", name="隆基绿能", snapshot_id="abc", deep_refresh=True)

    assert calls[-1]["mode"] == "deep"
    assert calls[-1]["deep_refresh"] is True
    assert result["data"]["crawl_mode"] == "deep"


def test_missing_explicit_snapshot_does_not_auto_refresh(monkeypatch):
    store = MemorySnapshotStore()
    monkeypatch.setattr(api.news_service, "store", store)
    monkeypatch.setattr(api.cache_state_service, "get_info_snapshot", lambda sid: SimpleNamespace(data=None, cache_status={"status": "miss"}))
    monkeypatch.setattr(api.cache_state_service, "latest_info_snapshot", lambda symbol: SimpleNamespace(data=None, cache_status={"status": "miss"}))

    def fail_analyze(*args, **kwargs):
        raise AssertionError("missing explicit snapshot should not auto refresh")

    monkeypatch.setattr(api.info_analysis_service, "analyze", fail_analyze)
    result = api.info_analyze("601012", name="隆基绿能", snapshot_id="missing-sid", force=False, deep_refresh=False)

    assert result["ok"] is True
    assert result["data"]["mode"] == "snapshot_miss"
    assert result["data"]["items"] == []
    assert any("not found" in str(x) for x in result["data"]["errors"])


def test_screener_returns_info_snapshot_fields(monkeypatch):
    store = MemorySnapshotStore()
    monkeypatch.setattr(api.news_service, "store", store)
    monkeypatch.setattr(
        api.cache_state_service,
        "latest_info_snapshot",
        lambda symbol: SimpleNamespace(data=None, cache_status={"status": "miss", "stale": False}),
    )
    monkeypatch.setattr(api.company_profile_service, "get_profile", lambda *a, **k: {"name": "隆基绿能"})
    monkeypatch.setattr(api.score_history_service, "save_results", lambda data, mode="balanced": len(data))

    monkeypatch.setattr(
        api.screener_service,
        "run",
        lambda config: {
            "ok": True,
            "data": [{"symbol": "601012", "name": "隆基绿能", "total_score": 60.0, "tags": [], "risk_flags": []}],
            "result_count": 1,
            "universe_count": 1,
            "analyzed_count": 1,
            "elapsed_seconds": 0.01,
            "error_count": 0,
        },
    )
    monkeypatch.setattr(api.info_analysis_service, "analyze", lambda *a, **k: _info_payload())

    result = api.screener_run(symbols="601012", max_items=1, enable_news=True, info_limit=180)
    item = result["data"][0]

    assert item["info_snapshot_id"].endswith("-601012")
    assert item["info_crawl_time"]
    assert item["info_effective_count"] == 3
    assert item["info_unique_event_count"] == 3
    assert item["technical_score"] == 60.0
    assert item["info_score_delta"] == 2.1
    assert item["total_score"] == 62.1
    assert "score_stability_note" in result
    assert "snapshot_id=" in item["info"]["detail_url"]
    assert "force=false" in item["info"]["detail_url"]
