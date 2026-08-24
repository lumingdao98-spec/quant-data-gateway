from datetime import datetime, timedelta

from quant_data.models import Bar, Quote
from quant_data.services.market_regime_service import MarketRegimeService


def _quote(idx: int, change_pct: float) -> Quote:
    return Quote(
        symbol=f"{idx:06d}",
        name=f"标的{idx}",
        ts=datetime(2026, 5, 28, 10, 0),
        last=10.0,
        pre_close=10.0,
        open=10.0,
        high=10.2,
        low=9.8,
        volume=100_000,
        amount=10_000_000,
        change=change_pct / 100,
        change_pct=change_pct,
        source="unit",
    )


def _bars(symbol: str, start: float = 100.0, step: float = 0.5, count: int = 90) -> list[Bar]:
    base = datetime(2026, 1, 1)
    rows = []
    for i in range(count):
        price = start + i * step
        rows.append(
            Bar(
                symbol=symbol,
                frame="1d",
                ts=base + timedelta(days=i),
                open=price * 0.99,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=1_000_000 + i * 1000,
                amount=price * 1_000_000,
                source="unit:index",
            )
        )
    return rows


def test_market_regime_uses_index_trend_and_breadth_without_full_score():
    quotes = [_quote(i, 1.2 if i % 2 == 0 else -0.4) for i in range(120)]
    index_bars = {
        "shanghai": _bars("sh000001", step=0.25),
        "sz_component": _bars("sz399001", step=0.20),
        "chinext": _bars("sz399006", step=0.35),
        "csi300": _bars("sh000300", step=0.22),
        "star50": _bars("sh000688", step=0.18),
    }

    result = MarketRegimeService().analyze_market(quotes, index_bars=index_bars)

    assert result["index_count"] == 5
    assert result["index_score"] is not None
    assert result["breadth_score"] is not None
    assert 50 < result["score"] <= 95
    assert result["score"] != 100
    assert "70%指数趋势" in result["basis"]
    assert "50中性" in result["score_definition"]


def test_market_regime_falls_back_to_shrunk_breadth_when_indices_missing():
    quotes = [_quote(i, 8.0) for i in range(6)]

    result = MarketRegimeService().analyze_market(quotes, index_bars={})

    assert result["index_count"] == 0
    assert result["confidence"] == "low"
    assert result["score"] < 60
    assert "仅用市场宽度兜底" in result["basis"]


def test_single_index_and_tiny_breadth_are_not_enough_for_automatic_score():
    quotes = [_quote(1, 1.0), _quote(2, -1.0)]

    result = MarketRegimeService().analyze_market(
        quotes,
        index_bars={"shanghai": _bars("sh000001", step=0.25)},
    )

    assert result["index_count"] == 1
    assert result["valid_for_score"] is False
    assert result["quality_status"] == "insufficient_sample"
    assert any("两类独立证据" in reason for reason in result["missing_reasons"])
