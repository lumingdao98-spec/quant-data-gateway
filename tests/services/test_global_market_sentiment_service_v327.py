from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from quant_data.models import Bar
from quant_data.services.global_market_sentiment_service import GlobalMarketSentimentService
from quant_data.services.market_regime_service import MarketRegimeService


SH = ZoneInfo("Asia/Shanghai")


def _row(
    key: str,
    *,
    observed_at: datetime,
    change_pct: float,
    cluster: str,
    instrument_type: str = "cash_index",
    timezone: str = "Asia/Shanghai",
    relevance: float = 1.0,
    weight: float = 0.4,
    priority: int = 90,
    family: str = "",
    family_cap: float = 1.0,
) -> dict:
    return {
        "key": key,
        "name": key,
        "code": key,
        "cluster": cluster,
        "instrument_type": instrument_type,
        "timezone": timezone,
        "technology_relevance": relevance,
        "base_weight": weight,
        "priority": priority,
        "correlation_family": family or cluster,
        "family_cap": family_cap,
        "change_pct": change_pct,
        "last": 100,
        "observed_at": observed_at.isoformat(timespec="seconds"),
        "source_id": "unit",
        "source_name": "单元测试",
        "source_ref": "https://example.com/quote",
    }


def test_global_context_is_session_aware_and_deduplicates_nasdaq_direction():
    now = datetime(2026, 8, 24, 10, 0, tzinfo=SH)
    observations = [
        _row(
            "hang_seng_tech",
            observed_at=now - timedelta(minutes=1),
            change_pct=1.2,
            cluster="hong_kong_tech",
            timezone="Asia/Hong_Kong",
            priority=100,
        ),
        _row(
            "nasdaq_100_futures",
            observed_at=now - timedelta(minutes=2),
            change_pct=0.8,
            cluster="us_tech_direction",
            instrument_type="futures",
            timezone="America/New_York",
            priority=95,
        ),
        _row(
            "nasdaq_100",
            observed_at=now - timedelta(hours=11),
            change_pct=0.9,
            cluster="us_tech_direction",
            timezone="America/New_York",
            priority=100,
        ),
        _row(
            "nikkei_225",
            observed_at=now - timedelta(minutes=3),
            change_pct=-0.4,
            cluster="japan_risk_proxy",
            timezone="Asia/Tokyo",
            relevance=0.42,
            weight=0.12,
            priority=60,
        ),
    ]

    result = GlobalMarketSentimentService(cache_state=None).analyze(observations, now=now)

    assert result["valid_for_score"] is True
    assert result["live_units"] >= 2
    selected_us = [x for x in result["selected_evidence"] if x["cluster"] == "us_tech_direction"]
    assert [x["key"] for x in selected_us] == ["nasdaq_100_futures"]
    assert any("避免重复计分" in x["excluded_reason"] for x in result["excluded_evidence"])
    assert sum(x["normalized_weight"] for x in result["selected_evidence"]) == pytest.approx(1.0)


def test_us_cash_index_wins_cluster_during_regular_session():
    now = datetime(2026, 8, 24, 22, 0, tzinfo=SH)
    observations = [
        _row(
            "nasdaq_100_futures",
            observed_at=now - timedelta(minutes=1),
            change_pct=0.3,
            cluster="us_tech_direction",
            instrument_type="futures",
            timezone="America/New_York",
            priority=95,
        ),
        _row(
            "nasdaq_100",
            observed_at=now - timedelta(minutes=1),
            change_pct=0.4,
            cluster="us_tech_direction",
            timezone="America/New_York",
            priority=100,
        ),
        _row(
            "hang_seng_tech",
            observed_at=now - timedelta(hours=6),
            change_pct=-0.2,
            cluster="hong_kong_tech",
            timezone="Asia/Hong_Kong",
            priority=100,
        ),
    ]

    result = GlobalMarketSentimentService(cache_state=None).analyze(observations, now=now)

    selected_us = [x for x in result["selected_evidence"] if x["cluster"] == "us_tech_direction"]
    assert [x["key"] for x in selected_us] == ["nasdaq_100"]
    assert selected_us[0]["session_phase"] == "实时交易"


def test_single_stale_observation_cannot_create_trade_score():
    now = datetime(2026, 8, 24, 10, 0, tzinfo=SH)
    result = GlobalMarketSentimentService(cache_state=None).analyze(
        [
            _row(
                "hang_seng_tech",
                observed_at=now - timedelta(days=5),
                change_pct=2.0,
                cluster="hong_kong_tech",
                timezone="Asia/Hong_Kong",
            )
        ],
        now=now,
    )

    assert result["valid_for_score"] is False
    assert result["score"] is None
    assert result["selected_evidence"] == []
    assert result["observations"][0]["stale"] is True


def test_us_indices_are_bounded_as_one_correlated_asset_family():
    now = datetime(2026, 8, 24, 22, 0, tzinfo=SH)
    observations = [
        _row(
            "hang_seng_tech",
            observed_at=now - timedelta(hours=6),
            change_pct=-0.4,
            cluster="hong_kong_tech",
            timezone="Asia/Hong_Kong",
            family="greater_china_technology",
            family_cap=0.30,
        ),
        _row(
            "nasdaq_100",
            observed_at=now - timedelta(minutes=1),
            change_pct=1.2,
            cluster="us_tech_direction",
            timezone="America/New_York",
            family="us_equity_risk",
            family_cap=0.52,
        ),
        _row(
            "philadelphia_semiconductor",
            observed_at=now - timedelta(minutes=1),
            change_pct=2.0,
            cluster="us_semiconductor_direction",
            timezone="America/New_York",
            family="us_equity_risk",
            family_cap=0.52,
            weight=0.2,
        ),
        _row(
            "sp500_futures",
            observed_at=now - timedelta(minutes=1),
            change_pct=0.8,
            cluster="us_broad_market_direction",
            instrument_type="futures",
            timezone="America/New_York",
            family="us_equity_risk",
            family_cap=0.52,
            relevance=0.58,
            weight=0.12,
        ),
    ]

    result = GlobalMarketSentimentService(cache_state=None).analyze(observations, now=now)

    assert result["valid_for_score"] is True
    us_rows = [row for row in result["selected_evidence"] if row["correlation_family"] == "us_equity_risk"]
    assert {row["key"] for row in us_rows} == {"nasdaq_100", "philadelphia_semiconductor", "sp500_futures"}
    assert sum(row["normalized_weight"] for row in us_rows) < 0.8
    assert sum(row["normalized_weight"] for row in result["selected_evidence"]) == pytest.approx(1.0)


def test_market_regime_caps_global_context_at_fifteen_percent():
    start = datetime(2026, 4, 1)
    bars = [
        Bar(
            symbol="sh000001",
            frame="1d",
            ts=start + timedelta(days=index),
            open=100 + index,
            high=101 + index,
            low=99 + index,
            close=100 + index,
            volume=1_000_000,
            amount=100_000_000,
            source="unit",
        )
        for index in range(90)
    ]
    quotes = [type("Q", (), {"change_pct": 1.0, "amount": 1_000_000})() for _ in range(25)]
    result = MarketRegimeService().analyze_market(
        quotes,
        index_bars={"shanghai": bars, "csi300": bars},
        global_context={"score": 20, "valid_for_score": True, "missing_reasons": []},
    )

    global_component = next(x for x in result["components"] if x["key"] == "global_technology_context")
    assert result["global_score_used"] is True
    assert global_component["normalized_weight"] == pytest.approx(0.15)
    assert sum(x["normalized_weight"] for x in result["components"]) == pytest.approx(1.0)
