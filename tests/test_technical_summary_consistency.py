from __future__ import annotations

from quant_data.services.market_data_service import MarketDataService
from quant_data.services.screener_service import ScreenerService


OPTIMISTIC = ["低位修复动量改善", "量能配合", "空间结构较好", "时间窗口观察"]


def _service() -> ScreenerService:
    return ScreenerService(MarketDataService.__new__(MarketDataService))


def test_d_grade_summary_is_risk_first_and_not_optimistic():
    text = _service()._grade_aware_technical_summary(
        "D",
        "低位修复动量改善，量能配合，空间结构较好，时间窗口观察",
        tags=["低位观察"],
        risk_flags=["跌破MA20"],
        behavior_tags=["高换手不涨"],
        last=10,
        ma20=12,
        ma60=13,
        vwap20=11,
    )

    assert text.startswith("技术面偏弱")
    assert "跌破MA20" in text
    assert all(x not in text for x in OPTIMISTIC)


def test_c_grade_summary_shows_divergence():
    text = _service()._grade_aware_technical_summary(
        "C",
        "趋势修复",
        tags=["低位观察"],
        risk_flags=["趋势与量价信号不一致"],
        behavior_tags=[],
        last=10,
        ma20=10,
        ma60=11,
        vwap20=10,
    )

    assert text.startswith("技术面分化")


def test_a_b_grade_summary_is_edge_first():
    svc = _service()
    for grade in ["A", "B"]:
        text = svc._grade_aware_technical_summary(
            grade,
            "趋势较好",
            tags=["均线多头", "资金配合"],
            risk_flags=[],
            behavior_tags=[],
            last=12,
            ma20=10,
            ma60=9,
            vwap20=11,
        )
        assert text.startswith("技术面优势")
        assert "均线多头" in text
