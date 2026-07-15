from datetime import datetime, timezone

from quant_data.trading.data_freshness import DataFreshnessGuard
from quant_data.trading.risk_gateway import RiskGateway
from quant_data.trading.time_utils import cn_market_time


def test_browser_utc_timestamp_is_converted_to_cn_market_time():
    assert cn_market_time("2026-07-15T05:39:00.000Z") == datetime(2026, 7, 15, 13, 39)
    assert cn_market_time(datetime(2026, 7, 15, 5, 39, tzinfo=timezone.utc)) == datetime(2026, 7, 15, 13, 39)


def test_risk_gateway_accepts_1339_browser_utc_as_cn_trading_time():
    gateway = RiskGateway()
    result = gateway.evaluate_order(
        {"symbol": "300750", "side": "buy", "quantity": 100, "price": 10},
        portfolio={"cash": 100000, "equity": 100000, "positions": {}},
        signal={"symbol": "300750", "action": "buy", "final_score": 80},
        quote={"last": 10, "amount": 100000000},
        freshness={"action": "allow"},
        now=datetime(2026, 7, 15, 5, 39, tzinfo=timezone.utc),
    )
    assert "非交易时段禁止自动下单" not in result["risk_reasons"]


def test_freshness_compares_utc_and_cn_timestamps_on_same_clock():
    result = DataFreshnessGuard().check(
        {
            "quote": "2026-07-15T05:38:55Z",
            "intraday": "2026-07-15T13:38:55+08:00",
            "news": "2026-07-15T13:38:55+08:00",
            "technical": "2026-07-15T13:38:55+08:00",
            "company_profile": "2026-07-15T13:38:55+08:00",
        },
        now=datetime(2026, 7, 15, 5, 39, tzinfo=timezone.utc),
    )
    assert result.freshness_status == "fresh"
    assert result.action == "allow"
