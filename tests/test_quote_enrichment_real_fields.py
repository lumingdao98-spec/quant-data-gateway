from __future__ import annotations

from datetime import datetime

from dataclasses import replace

from quant_data.models import AssetType, Quote
from quant_data.services.cache_state_service import CacheStateService
import quant_data.api as api


def _quote(symbol: str = "601012", asset_type: AssetType = AssetType.STOCK) -> Quote:
    return Quote(
        symbol=symbol,
        name="Longi",
        ts=datetime(2026, 5, 22, 15, 0),
        last=20,
        pre_close=19,
        open=19,
        high=21,
        low=18,
        volume=1000,
        amount=2_000_000,
        change=1,
        change_pct=5,
        turnover=3.2,
        volume_ratio=1.4,
        pe_dynamic=18,
        pb=2.1,
        total_market_cap=120_000_000_000,
        float_market_cap=90_000_000_000,
        asset_type=asset_type,
        source="unit",
    )


def test_custom_input_merge_uses_enriched_quote(monkeypatch):
    item = {
        "symbol": "601012",
        "name": "Longi",
        "candidate_channels": ["custom_input"],
        "missing_data_hints": ["PE缺失", "PB缺失", "总市值缺失", "流通市值缺失"],
        "metric_missing_reasons": ["行情源缺失 PE", "行情源缺失 PB"],
    }
    q = _quote()
    qd = api._quote_dict_with_aliases(q)
    monkeypatch.setattr(api, "_enrich_quote_real", lambda symbol, force=False, quote_obj=None, bars=None: (q, qd, {"status": "hit"}))
    api._merge_screener_item_quote_metrics(item)
    assert item["pe_ttm"] == 18
    assert item["pb"] == 2.1
    assert item["market_cap_style"] not in (None, "", "未知")
    assert item["metric_sources"]["pe_ttm"] == "unit"
    assert not item["missing_data_hints"]
    assert not item["metric_missing_reasons"]


def test_stale_quote_cache_can_fill_fields(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    cached = api._quote_dict_with_aliases(_quote())
    svc.put("quote_cache", "601012", {"quote": cached}, ttl_seconds=-1, symbol="601012", source="test")
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    q, qd, status = api._enrich_quote_real("601012")
    assert qd["pe_ttm"] == 18
    assert qd["pb"] == 2.1
    assert qd["quote_cache_status"]["status"] == "stale"
    assert any("stale" in x for x in qd["metric_missing_reasons"])


def test_etf_pe_pb_not_applicable_reason():
    q = _quote("510300", AssetType.ETF)
    q = replace(q, pe_dynamic=None, pb=None, asset_type=AssetType.ETF)
    enriched = api.service.enrich_quote_metrics(q, force_refresh=False, bars=[])
    assert "ETF" in " ".join(enriched.metric_missing_reasons or [])


def test_company_profile_fills_market_cap_when_quote_source_lacks_it(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    q = replace(_quote("300750"), total_market_cap=None, float_market_cap=None, source="sina")
    monkeypatch.setattr(api.service, "get_quote", lambda *a, **k: q)
    monkeypatch.setattr(api.service, "enrich_quote_metrics", lambda q, **kwargs: q)
    monkeypatch.setattr(
        api.company_profile_service,
        "get_profile",
        lambda *a, **k: {"total_market_value": "1.87万亿", "float_market_value": "1.72万亿"},
    )

    _q, qd, _status = api._enrich_quote_real("300750")

    assert qd["total_market_cap"] == 1.87e12
    assert qd["float_market_cap"] == 1.72e12
    assert qd["metric_sources"]["total_market_cap"] == "company_profile"
