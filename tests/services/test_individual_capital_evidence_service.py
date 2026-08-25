from __future__ import annotations

from datetime import datetime, timedelta

from quant_data.models import IntradayPoint
from quant_data.services.individual_capital_evidence_service import (
    IndividualCapitalEvidenceService,
)


def test_parse_public_daily_flow_keeps_real_source_fields():
    rows = IndividualCapitalEvidenceService._parse_daily_flow(
        {
            "data": {
                "klines": [
                    "2026-08-25,1000000,-100000,200000,300000,500000,2.5,-0.2,0.4,0.7,1.2,410.5,1.8"
                ]
            }
        }
    )

    assert rows == [
        {
            "date": "2026-08-25",
            "main_net_inflow": 1000000.0,
            "small_net_inflow": -100000.0,
            "medium_net_inflow": 200000.0,
            "large_net_inflow": 300000.0,
            "super_large_net_inflow": 500000.0,
            "main_net_ratio_pct": 2.5,
            "small_net_ratio_pct": -0.2,
            "medium_net_ratio_pct": 0.4,
            "large_net_ratio_pct": 0.7,
            "super_large_net_ratio_pct": 1.2,
            "close": 410.5,
            "change_pct": 1.8,
        }
    ]


def test_intraday_proxy_exposes_all_day_and_rolling_windows_without_level2_claim():
    start = datetime(2026, 8, 25, 9, 30)
    points = [
        IntradayPoint(
            symbol="300750",
            ts=start + timedelta(minutes=index),
            price=400 + index * 0.1,
            avg_price=400 + index * 0.04,
            volume=1000,
            amount=400000 + index * 1000,
            source="unit_intraday",
        )
        for index in range(70)
    ]

    result = IndividualCapitalEvidenceService._intraday_proxy(
        points,
        {"source": "unit_quote"},
    )

    assert result["available"] is True
    assert result["point_count"] == 70
    assert set(result["windows"]) == {"5", "15", "30", "60"}
    assert result["estimated_inflow"] >= 0
    assert result["estimated_outflow"] >= 0
    assert "不等同" in result["truth_boundary"]


def test_holder_parser_marks_disclosure_as_lagged_snapshot():
    html = """
    <table>
      <tr><td>截止日期</td><td>2026-06-30</td></tr>
      <tr><th>基金名称</th><th>基金代码</th><th>持股数量</th><th>占流通股比例</th><th>持股市值</th><th>占净值比例</th></tr>
      <tr><td>基金A</td><td>000001</td><td>100</td><td>0.1</td><td>40000</td><td>1.0</td></tr>
      <tr><td>基金B</td><td>000002</td><td>200</td><td>0.2</td><td>80000</td><td>1.1</td></tr>
      <tr><td>基金C</td><td>000003</td><td>300</td><td>0.3</td><td>120000</td><td>1.2</td></tr>
      <tr><td>基金D</td><td>000004</td><td>400</td><td>0.4</td><td>160000</td><td>1.3</td></tr>
      <tr><td>基金E</td><td>000005</td><td>500</td><td>0.5</td><td>200000</td><td>1.4</td></tr>
    </table>
    """

    result = IndividualCapitalEvidenceService._parse_holder_html(html)

    assert result["available"] is True
    assert result["report_date"] == "2026-06-30"
    assert result["fund_count"] == 5
    assert result["total_disclosed_shares"] == 1500.0

