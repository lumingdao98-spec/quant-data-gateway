from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from quant_data.models import AssetType, Bar, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.services.screener_service import ScreenerConfig, ScreenerService


def _quote(**kwargs) -> Quote:
    data = {
        "symbol": "601012",
        "name": "隆基绿能",
        "ts": datetime(2026, 5, 23, 10, 0),
        "last": 15.0,
        "pre_close": 14.8,
        "open": 14.9,
        "high": 15.2,
        "low": 14.7,
        "volume": 100000,
        "amount": 150000000,
        "change": 0.2,
        "change_pct": 1.35,
        "source": "unit",
    }
    data.update(kwargs)
    return Quote(**data)


def _bars(symbol="601012", close=15.0) -> list[Bar]:
    start = datetime(2026, 4, 1)
    return [
        Bar(symbol, "1d", start + timedelta(days=i), close - 0.1, close + 0.2, close - 0.3, close, 1000 + i, close * 100000, turnover=1.0)
        for i in range(30)
    ]


class FakeMarketData:
    def __init__(self):
        self.enrich_calls = 0

    def get_quotes(self, symbols, force_refresh=False):
        return [_quote(symbol=symbols[0], turnover=None, volume_ratio=None, pe_dynamic=None, pb=None, total_market_cap=None, float_market_cap=None)]

    def enrich_quote_metrics(self, quote, force_refresh=False, bars=None):
        self.enrich_calls += 1
        return replace(
            quote,
            turnover=2.8,
            volume_ratio=1.7,
            pe_dynamic=18.5,
            pb=2.1,
            total_market_cap=180_000_000_000,
            float_market_cap=120_000_000_000,
            circulating_market_cap=120_000_000_000,
            metric_missing_reasons=[],
        )

    def get_kline(self, *args, **kwargs):
        return _bars()


class FailingProviders:
    def get_quote(self, symbol):
        raise RuntimeError("offline")


def test_custom_input_also_calls_enrich_quote_metrics():
    fake = FakeMarketData()
    svc = ScreenerService(fake)
    quotes = svc._load_universe(ScreenerConfig(universe="custom", symbols=["601012"], max_items=1))

    assert fake.enrich_calls == 1
    assert quotes[0].turnover == 2.8
    assert quotes[0].pe_dynamic == 18.5
    assert quotes[0].total_market_cap == 180_000_000_000


def test_missing_pe_pb_returns_explicit_reason_for_etf():
    svc = MarketDataService.__new__(MarketDataService)
    svc.providers = FailingProviders()
    quote = _quote(symbol="510300", name="沪深300ETF", asset_type=AssetType.ETF, pe_dynamic=None, pb=None, total_market_cap=None, float_market_cap=None)

    enriched = svc.enrich_quote_metrics(quote)

    assert "ETF不适用 PE" in enriched.metric_missing_reasons
    assert "ETF不适用 PB" in enriched.metric_missing_reasons
    assert any("总市值" in x for x in enriched.metric_missing_reasons)


def test_market_cap_style_uses_available_market_cap():
    svc = ScreenerService(MarketDataService.__new__(MarketDataService))
    quote = _quote(total_market_cap=180_000_000_000, float_market_cap=120_000_000_000, turnover=2, volume_ratio=1.2, pe_dynamic=16, pb=2)

    result = svc.analyze(quote, _bars(), mode="balanced")

    assert result.market_cap_style in {"微盘", "小盘", "中盘", "大盘", "超大盘"}
    assert result.market_cap_style != "未知"
