from dataclasses import replace
from datetime import datetime

from quant_data.models import AssetType, Quote
from quant_data.services.market_data_service import MarketDataService


def _quote(symbol="601012", **kw):
    base = Quote(symbol=symbol, name=symbol, ts=datetime.now(), last=10, pre_close=9.8, open=9.8, high=10.2, low=9.7, volume=1000, amount=1000000, change=0.2, change_pct=2.0)
    return replace(base, **kw)


def test_stock_missing_metrics_has_explicit_reasons():
    q = MarketDataService().enrich_quote_metrics(_quote())
    assert q.metric_missing_reasons
    text = " ".join(q.metric_missing_reasons)
    assert "PE" in text and "PB" in text
    assert q.market_cap_style is None


def test_etf_pe_pb_are_not_applicable():
    q = MarketDataService().enrich_quote_metrics(_quote("510300", asset_type=AssetType.ETF))
    assert any("ETF" in x and "PE" in x for x in q.metric_missing_reasons)
    assert any("ETF" in x and "PB" in x for x in q.metric_missing_reasons)


def test_market_cap_style_uses_any_available_market_cap():
    q = MarketDataService().enrich_quote_metrics(_quote(total_market_cap=150_000_000_000, float_market_cap=None, pe_dynamic=12, pb=1.3, turnover=1.2, volume_ratio=1.1))
    assert q.market_cap_style in {"大盘", "超大盘"}
    assert q.total_share
