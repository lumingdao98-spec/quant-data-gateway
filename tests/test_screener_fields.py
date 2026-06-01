from datetime import datetime, timedelta

from quant_data.models import AssetType, Bar, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.services.screener_service import ScreenerService


def _bars():
    start = datetime(2025, 1, 1)
    bars = []
    for i in range(260):
        price = 8 + i * 0.01
        bars.append(Bar("600519", "1d", start + timedelta(days=i), price * 0.99, price * 1.025, price * 0.975, price, 120_000 + i * 50, price * (120_000 + i * 50), source="unit:qfq"))
    return bars


def _quote():
    return Quote(
        "600519", "贵州茅台", datetime.now(), 11.2, 11.0, 11.05, 11.4, 10.9,
        1_000_000, 1_120_000_000, 0.2, 1.82, turnover=1.2, volume_ratio=1.35,
        pe_dynamic=25, pb=6.2, total_market_cap=1_800_000_000_000,
        float_market_cap=1_790_000_000_000, asset_type=AssetType.STOCK, source="unit",
    )


def test_screener_result_contains_frontend_v317_fields():
    data = ScreenerService(MarketDataService()).analyze(_quote(), _bars(), kline_adjust="qfq").to_dict()
    required = [
        "candidate_channels", "turnover", "volume_ratio", "amount", "pe_dynamic", "pb",
        "total_market_cap", "float_market_cap", "ma20_deviation_pct", "amplitude_5d_pct",
        "pos20", "technical_signal_summary", "capital_signal", "theme_stage",
        "market_regime", "market_sentiment_score", "market_sentiment_adjustment", "market_sentiment_label",
        "market_cap_style", "support_resistance_distance", "chase_high_risk",
        "comprehensive_diagnosis", "script_score", "manual_review_score",
        "upgrade_reasons", "downgrade_reasons", "missing_data_hints",
        "technical_factor_details",
    ]
    for key in required:
        assert key in data
    assert data["technical_factor_details"]
    assert data["technical_signal_summary"]


def test_market_sentiment_is_small_visible_adjustment():
    data = ScreenerService(MarketDataService()).analyze(
        _quote(),
        _bars(),
        kline_adjust="qfq",
        market_regime={"score": 72, "regime": "震荡偏强", "sample_count": 200, "basis": "unit"},
    ).to_dict()

    assert data["market_sentiment_label"] in {"强势", "偏暖"}
    assert 0 < data["market_sentiment_adjustment"] <= 2
    assert "大盘情绪" in data["comprehensive_diagnosis"]
