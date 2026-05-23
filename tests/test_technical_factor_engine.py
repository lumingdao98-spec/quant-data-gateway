from datetime import datetime, timedelta

from quant_data.models import AssetType, Bar, Quote
from quant_data.services.technical_factor_engine import TECHNICAL_FACTOR_KEYS, TechnicalFactorEngine


def _bars(n=260):
    base = datetime(2025, 1, 1)
    out = []
    price = 10.0
    for i in range(n):
        price *= 1.002 if i % 7 else 0.997
        high = price * (1.02 + (i % 3) * 0.002)
        low = price * 0.98
        volume = 100_000 + i * 400
        out.append(Bar("600000", "1d", base + timedelta(days=i), price * 0.995, high, low, price, volume, volume * price * 100, source="unit:qfq"))
    return out


def _quote():
    return Quote(
        "600000", "浦发银行", datetime.now(), 15.8, 15.5, 15.55, 15.95, 15.4,
        280_000, 430_000_000, 0.3, 1.94, turnover=3.2, volume_ratio=1.6,
        pe_dynamic=9.8, pb=0.82, total_market_cap=390_000_000_000,
        float_market_cap=360_000_000_000, asset_type=AssetType.STOCK, source="unit",
    )


def test_technical_factor_engine_covers_word_required_indicators():
    report = TechnicalFactorEngine().analyze(_quote(), _bars())
    factors = report["factors"]
    by_key = {x["key"]: x for x in factors}

    assert set(TECHNICAL_FACTOR_KEYS) <= set(by_key)
    assert report["factor_count"] >= len(TECHNICAL_FACTOR_KEYS)
    assert report["score_total"] >= 0
    assert report["summary"]

    for key in TECHNICAL_FACTOR_KEYS:
        item = by_key[key]
        assert item["formula_source"]
        assert item["logic"]
        assert item["signal"] in {"看多", "看空", "中性"}
        assert item["explanation"]
        assert "score_contribution" in item
        assert "risk_penalty" in item
        assert item["application"]


def test_technical_factor_engine_outputs_real_values_for_core_indicators():
    by_key = {x["key"]: x for x in TechnicalFactorEngine().analyze(_quote(), _bars())["factors"]}
    for key in ["ma", "ema", "macd", "rsi", "kdj", "boll", "atr", "vwap", "obv", "mfi", "adx", "support_resistance", "price_pattern"]:
        assert by_key[key]["value"] is not None
