from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_info_snapshot_persists_items_and_items_api_falls_back(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    payload = {
        "snapshot_id": "info-items",
        "symbol": "600438",
        "name": "TW",
        "items": [{"title": "A notice", "source": "cninfo", "summary": "x"}],
        "news": {"count": 1, "items": [{"title": "A notice", "source": "cninfo"}]},
        "source_logs": [{"source": "cache", "status": "ok", "count": 1}],
        "score_model": {"formula": "x"},
    }
    svc.save_info_snapshot("info-items", "600438", payload, mode="light")
    client = TestClient(api.app)
    analyzed = client.get("/api/info/analyze/600438?snapshot_id=info-items&force=false").json()
    assert analyzed["items"][0]["title"] == "A notice"
    paged = client.get("/api/info/items/600438?page=9&page_size=1&include_unknown_date=true").json()
    assert paged["data"]["page"] == 1
    assert paged["data"]["data"][0]["title"] == "A notice"


def test_empty_items_with_raw_count_reports_reason():
    payload = api._normalize_info_payload({"news": {"count": 3, "items": []}}, "600438", "TW", "sid", {"status": "refreshed"}, used_snapshot=False, mode="light")
    assert payload["errors"]
    assert "filtered" in payload["diagnostics"]["filter_empty_reason"] or "empty" in payload["diagnostics"]["filter_empty_reason"]


def test_normalized_info_exposes_current_scoring_scope():
    payload = api._normalize_info_payload(
        {
            "items": [
                {"title": "近期公告", "published_at": "2026-07-16T10:00:00"},
                {"title": "日期未知历史档案"},
            ],
            "data_quality": {
                "current_scoring_count": 1,
                "historical_excluded_count": 4,
                "unknown_date_count": 1,
            },
        },
        "600438",
        "TW",
        "sid-current",
        {"status": "hit"},
        used_snapshot=True,
        mode="snapshot",
    )

    summary = payload["current_information_summary"]
    assert summary["current_scoring_count"] == 1
    assert summary["historical_excluded_count"] == 4
    assert summary["unknown_date_count"] == 1
    assert summary["latest_published_at"] == "2026-07-16T10:00:00"
    assert "历史信息" in summary["score_scope"]


def test_old_info_snapshot_derives_recent_count_when_quality_fields_are_missing():
    now = datetime.now()
    payload = api._normalize_info_payload(
        {
            "items": [
                {"title": "近期公告", "source": "巨潮", "source_type": "announcement", "published_at": (now - timedelta(days=3)).isoformat()},
                {"title": "重复转载", "source": "巨潮", "source_type": "announcement", "published_at": (now - timedelta(days=3)).isoformat(), "event_key": "same"},
                {"title": "重复转载2", "source": "门户", "source_type": "announcement", "published_at": (now - timedelta(days=3)).isoformat(), "event_key": "same"},
                {"title": "过期旧闻", "source": "历史", "source_type": "news", "published_at": (now - timedelta(days=120)).isoformat()},
                {"title": "论坛传闻", "source": "社区", "source_type": "community", "published_at": now.isoformat()},
            ]
        },
        "600438",
        "TW",
        "sid-old",
        {"status": "hit"},
        used_snapshot=True,
        mode="snapshot",
    )

    summary = payload["current_information_summary"]
    assert summary["current_scoring_count"] == 2
    assert summary["historical_excluded_count"] == 2
