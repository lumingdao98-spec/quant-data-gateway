from __future__ import annotations

from datetime import datetime, timedelta

from quant_data.services.fundamental_snapshot_scoring_service import (
    FundamentalSnapshotScoringService,
)


def _profile(report_date: datetime) -> dict:
    date_text = report_date.strftime("%Y%m%d")
    return {
        "profile_type": "STOCK",
        "sources": ["历史业绩", "巨潮资讯"],
        "financial_summary": {
            "latest_report_date": date_text,
            "latest_revenue": "2769.16亿",
            "latest_net_profit": "470.30亿",
            "latest_roe": "18.6%",
        },
        "financial_history": [
            {
                "report_date": date_text,
                "revenue": "2769.16亿",
                "net_profit": "470.30亿",
                "roe": "18.6%",
                "gross_margin": "27.4%",
                "debt_ratio": "58.2%",
                "eps": "9.51",
            }
        ],
    }


def test_traceable_disclosed_financial_snapshot_produces_a_score():
    decision_time = datetime(2026, 8, 25, 10, 0)
    result = FundamentalSnapshotScoringService().evaluate(
        symbol="300750",
        profile=_profile(decision_time - timedelta(days=30)),
        quote={"pe_dynamic": 22.0, "pb": 4.2},
        decision_time=decision_time,
    )

    assert result["score"] is not None
    assert result["quality_status"] in {"available", "partial"}
    assert result["pit_status"] == "point_in_time"
    assert "roe" in result["evidence_fields"]
    assert "net_profit_sign" in result["evidence_fields"]
    assert "不晚于决策时点" in result["truth_boundary"]


def test_future_financial_snapshot_is_rejected_instead_of_backfilled():
    decision_time = datetime(2026, 8, 25, 10, 0)
    result = FundamentalSnapshotScoringService().evaluate(
        symbol="300750",
        profile=_profile(decision_time + timedelta(days=1)),
        quote={"pe_dynamic": 22.0, "pb": 4.2},
        decision_time=decision_time,
    )

    assert result["score"] is None
    assert result["pit_status"] == "rejected"
    assert any("晚于决策时点" in reason for reason in result["missing_reasons"])

