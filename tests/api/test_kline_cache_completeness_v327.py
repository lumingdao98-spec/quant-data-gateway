from __future__ import annotations

from datetime import datetime, timedelta

import quant_data.api as api
from quant_data.models import Bar
from quant_data.services.cache_state_service import CacheRead


def _bar(index: int) -> Bar:
    close = 100.0 + index
    return Bar(
        symbol="300750",
        frame="1d",
        ts=datetime(2026, 1, 1) + timedelta(days=index),
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=1000 + index,
        amount=(1000 + index) * close,
        source="unit_full_history",
    )


def test_short_fresh_cache_does_not_mask_full_history(monkeypatch):
    short_rows = [_bar(i).to_dict() for i in range(20)]
    full_rows = [_bar(i) for i in range(45)]
    calls = {"count": 0}

    monkeypatch.setattr(
        api.cache_state_service,
        "get_kline_cache",
        lambda key: CacheRead(
            data={"ok": True, "bars": short_rows, "data": short_rows, "count": len(short_rows)},
            cache_status={"status": "hit", "stale": False},
        ),
    )

    def load_full_history(*args, **kwargs):
        calls["count"] += 1
        return full_rows

    monkeypatch.setattr(api.service, "get_kline", load_full_history)
    monkeypatch.setattr(
        api.cache_state_service,
        "save_kline_cache",
        lambda key, symbol, payload: {"status": "refreshed", "stale": False},
    )

    payload = api._safe_kline_payload("300750", frame="1d", limit=520, adjust="none", sync_quote=False)

    assert calls["count"] == 1
    assert payload["count"] == 45
    assert payload["cache_status"]["status"] == "refreshed"


def test_complete_fresh_cache_remains_fast_path(monkeypatch):
    rows = [_bar(i).to_dict() for i in range(30)]
    monkeypatch.setattr(
        api.cache_state_service,
        "get_kline_cache",
        lambda key: CacheRead(
            data={"ok": True, "bars": rows, "data": rows, "count": len(rows)},
            cache_status={"status": "hit", "stale": False},
        ),
    )
    monkeypatch.setattr(
        api.service,
        "get_kline",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("full source should not be called")),
    )

    payload = api._safe_kline_payload("300750", frame="1d", limit=520, adjust="none", sync_quote=False)

    assert payload["count"] == 30
    assert "cache_state_fresh_hit" in payload["fallback_chain"]
