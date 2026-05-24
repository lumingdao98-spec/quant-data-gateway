from datetime import datetime

from fastapi.testclient import TestClient

from quant_data import api
from quant_data.models import Quote
from quant_data.services.background_cache_service import BackgroundCacheService
from quant_data.services.cache_state_service import CacheStateService
from quant_data.services.watchlist_service import WatchlistService


def _quote(symbol="300750"):
    return Quote(symbol=symbol, name=symbol, ts=datetime.now(), last=100, pre_close=99, open=99, high=101, low=98, volume=1000, amount=1000000, change=1, change_pct=1)


def test_background_service_refreshes_watchlist_quote_cache(tmp_path):
    cache = CacheStateService(tmp_path / "cache.sqlite")
    watch = WatchlistService(tmp_path / "watchlist.json")
    watch.set(["300750", "600519"])
    svc = BackgroundCacheService(cache_state_service=cache, watchlist_service=watch)

    def loader(symbol):
        cache.put("quote_cache", symbol, {"quote": _quote(symbol).to_dict()}, symbol=symbol, source="test")
        return _quote(symbol), {}, {}

    out = svc.refresh_watchlist_quotes(None, loader)
    assert out["ok"] is True
    assert out["non_blocking"] is True
    assert cache.get("quote_cache", "300750").data
    assert svc.status()["watchlist"]["count"] == 2


def test_background_refresh_api_is_non_blocking(monkeypatch):
    monkeypatch.setattr(api, "_enrich_quote_real", lambda symbol, force=False: (_quote(symbol), _quote(symbol).to_dict(), {"status": "refreshed"}))
    res = TestClient(api.app).post("/api/background/refresh/watchlist?symbols=300750,600519").json()
    assert res["ok"] is True
    assert res["non_blocking"] is True
    assert "300750" in res["refreshed"]
