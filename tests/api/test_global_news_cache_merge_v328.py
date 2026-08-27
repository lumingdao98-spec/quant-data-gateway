from __future__ import annotations

from datetime import datetime, timedelta

import quant_data.api as api
from quant_data.services.cache_state_service import CacheStateService


def test_small_fresh_poll_does_not_erase_recent_official_event(monkeypatch, tmp_path) -> None:
    cache = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", cache)
    now = datetime.now()
    cache.put(
        "global_news_cache",
        "global:120",
        {
            "items": [
                {
                    "title": "官方确认电网设备准入规则调整",
                    "source": "官方机构",
                    "url": "https://example.gov/official-grid-rule",
                    "published_at": (now - timedelta(days=1)).isoformat(timespec="seconds"),
                    "confirmation_level": "official_confirmed",
                    "decision_scope": "industry",
                    "decision_use": "score_candidate",
                }
            ],
            "source_logs": [{"source": "官方机构", "status": "ok", "count": 1}],
        },
        source="official_feed",
    )
    cache.put(
        "global_news_cache",
        "global:80",
        {
            "items": [
                {
                    "title": "刚刚发布的商品快讯",
                    "source": "实时快讯",
                    "url": "https://example.com/latest-flash",
                    "published_at": now.isoformat(timespec="seconds"),
                }
            ],
            "source_logs": [{"source": "实时快讯", "status": "ok", "count": 1}],
        },
        source="fast_feed",
    )

    payload, status = api._read_global_news_cached(limit=200, force=False, schedule_refresh=False)
    titles = [item.get("title") for item in payload.get("items") or []]

    assert status["snapshot_id"] == "global:80"
    assert "刚刚发布的商品快讯" in titles
    assert "官方确认电网设备准入规则调整" in titles
    assert {"global:80", "global:120"}.issubset(set(payload["cache_selection"]["merged_keys"]))
    assert "事件级去重" in payload["cache_selection"]["reason_cn"]
