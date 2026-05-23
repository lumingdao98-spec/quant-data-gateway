from datetime import datetime, timedelta

from quant_data.models import AssetType, Bar, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.services.screener_service import ScreenerService


def _bars(n=260):
    start = datetime(2025, 1, 1)
    out = []
    for i in range(n):
        price = 10 + i * 0.012
        out.append(Bar("000001", "1d", start + timedelta(days=i), price * 0.99, price * 1.02, price * 0.98, price, 100_000 + i * 100, price * (100_000 + i * 100), source="unit:qfq"))
    return out


def _quote():
    return Quote(
        symbol="000001", name="平安银行", ts=datetime.now(), last=13.2, pre_close=13,
        open=13.05, high=13.4, low=12.9, volume=800_000, amount=880_000_000,
        change=0.2, change_pct=1.54, turnover=2.4, volume_ratio=1.7,
        pe_dynamic=8.5, pb=0.72, total_market_cap=260_000_000_000,
        float_market_cap=240_000_000_000, asset_type=AssetType.STOCK, source="unit",
    )


def test_diagnosis_engine_is_embedded_in_screener_result():
    result = ScreenerService(MarketDataService()).analyze(_quote(), _bars(), kline_adjust="qfq")
    data = result.to_dict()

    assert data["wordsource_report"]["version"].startswith("3.18")
    assert data["capital_signal"] in {"资金面偏强", "资金面中性", "资金面偏弱"}
    assert data["theme_stage"]
    assert data["market_cap_style"]
    assert data["script_score"] >= 0
    assert data["manual_review_score"] >= 0
    assert data["comprehensive_diagnosis"]
    assert "support_dist_pct" in data["support_resistance_distance"]
