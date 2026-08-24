from datetime import datetime, timedelta
from types import SimpleNamespace

from quant_data.models import Bar
from quant_data.services.market_regime_service import MarketRegimeService
from quant_data.services.screener_service import ScreenerService


def _quote(change):
    return SimpleNamespace(change_pct=change, amount=1_000_000)


def test_market_breadth_excludes_invalid_changes_and_marks_small_sample_unusable():
    result = MarketRegimeService().analyze_quotes([_quote(None), _quote("bad"), _quote(1.2), _quote(-0.5)])

    assert result["sample_count"] == 2
    assert result["invalid_count"] == 2
    assert result["valid_for_score"] is False
    assert result["quality_status"] == "insufficient_sample"


def test_market_breadth_becomes_score_eligible_with_valid_scope():
    result = MarketRegimeService().analyze_quotes([_quote(1 if index < 13 else -1) for index in range(25)])

    assert result["sample_count"] == 25
    assert result["valid_for_score"] is True
    assert result["quality_status"] == "available"


def test_screener_does_not_apply_neutral_market_score_when_market_evidence_is_invalid():
    service = ScreenerService.__new__(ScreenerService)

    result = service._market_sentiment_adjustment(
        {
            "score": 50,
            "valid_for_score": False,
            "quality_status": "insufficient_sample",
            "missing_reasons": ["指数样本不足"],
        },
        SimpleNamespace(asset_type="stock"),
    )

    assert result["score"] is None
    assert result["adjustment"] == 0.0
    assert result["label"] == "大盘证据不足"


def test_invalid_breadth_is_excluded_instead_of_mixing_neutral_50_into_index_score():
    base = datetime(2026, 1, 1)
    bars = [
        Bar(
            symbol="sh000001",
            frame="1d",
            ts=base + timedelta(days=index),
            open=100 + index,
            high=101 + index,
            low=99 + index,
            close=100 + index,
            volume=1_000_000,
            amount=100_000_000,
            source="unit:index",
        )
        for index in range(90)
    ]

    result = MarketRegimeService().analyze_market(
        [_quote(1.0), _quote(-1.0)],
        index_bars={"shanghai": bars, "csi300": bars},
    )

    assert result["valid_for_score"] is True
    assert [row["key"] for row in result["components"]] == ["index_trend"]
    assert result["components"][0]["normalized_weight"] == 1.0
    assert any(row["key"] == "market_breadth" for row in result["excluded_components"])
