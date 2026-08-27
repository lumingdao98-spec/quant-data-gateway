from __future__ import annotations

from quant_data.cache import MarketCache
from quant_data.providers.eastmoney import EastmoneyProvider


def test_eastmoney_quote_parser_keeps_real_market_industry() -> None:
    quote = EastmoneyProvider()._parse_quote_row(
        {
            "f2": 98.22,
            "f3": 1.2,
            "f4": 1.16,
            "f5": 100,
            "f6": 9822,
            "f8": 8.02,
            "f9": 22.22,
            "f12": "300274",
            "f13": "0",
            "f14": "阳光电源",
            "f15": 99.0,
            "f16": 96.0,
            "f17": 97.0,
            "f18": 97.06,
            "f20": 203630826065,
            "f21": 155926869920,
            "f23": 4.31,
            "f100": "光伏设备",
        }
    )

    assert quote is not None
    assert quote.industry == "光伏设备"
    assert quote.pe_dynamic == 22.22
    assert quote.pb == 4.31
    assert quote.turnover == 8.02


def test_market_cache_round_trips_quote_industry(tmp_path) -> None:
    provider = EastmoneyProvider()
    quote = provider._parse_quote_row(
        {
            "f2": 10.0,
            "f12": "000333",
            "f13": "0",
            "f14": "美的集团",
            "f18": 9.9,
            "f100": "白色家电",
        }
    )
    assert quote is not None

    cache = MarketCache(tmp_path / "market.sqlite")
    cache.save_quotes([quote])
    restored = cache.get_quote("000333")

    assert restored is not None
    assert restored.industry == "白色家电"
