from __future__ import annotations

from datetime import datetime, timedelta

from quant_data.models import Bar, Quote
from quant_data.services.market_behavior_engine import MarketBehaviorEngine


def _quote(change_pct=0.5, turnover=2.0, volume_ratio=1.0, last=10.0) -> Quote:
    return Quote(
        symbol="601012",
        name="隆基绿能",
        ts=datetime(2026, 5, 23, 10, 0),
        last=last,
        pre_close=last / (1 + change_pct / 100),
        open=last,
        high=last,
        low=last,
        volume=100000,
        amount=100000000,
        change=last - last / (1 + change_pct / 100),
        change_pct=change_pct,
        turnover=turnover,
        volume_ratio=volume_ratio,
        source="unit",
    )


def _bar(i, open_=10, high=10.2, low=9.8, close=10, volume=1000) -> Bar:
    return Bar("601012", "1d", datetime(2026, 4, 1) + timedelta(days=i), open_, high, low, close, volume, close * volume * 100)


def _base_bars(n=21, start=10.0, step=0.02, volume=1000) -> list[Bar]:
    return [_bar(i, close=start + i * step, high=start + i * step + 0.2, low=start + i * step - 0.2, volume=volume) for i in range(n)]


def _labels(result):
    return set(result["behavior_tags"])


def test_long_upper_shadow_with_volume_is_pullback_risk():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.4, high=12.0, low=10.0, close=10.3, volume=2600))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=0.8, last=10.3), bars)

    assert "冲高回落风险" in _labels(result)
    assert "长上影诱多" in _labels(result)
    assert result["risk_penalty_contribution"] > 0


def test_breakout_above_resistance_then_close_below_is_fake_breakout():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.8, high=11.5, low=10.6, close=10.8, volume=2200))
    result = MarketBehaviorEngine().analyze(_quote(last=10.8), bars, technical_context={"resistance": 11.0})

    assert "假突破风险" in _labels(result)


def test_high_position_high_volume_but_small_gain_is_stagflation():
    bars = _base_bars(21, start=10.0, step=0.1, volume=1000)
    bars.append(_bar(22, open_=12.0, high=12.25, low=11.9, close=12.02, volume=2600))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=0.4, last=12.02), bars)

    assert "高位放量滞涨" in _labels(result)


def test_high_turnover_without_price_gain_is_flagged():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.3, high=10.5, low=10.0, close=10.25, volume=1200))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=0.3, turnover=9.5, last=10.25), bars, technical_context={"vwap20": 10.4})

    assert "高换手不涨" in _labels(result)


def test_next_day_after_volume_upper_shadow_is_wash_confirmation():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.2, high=12.2, low=10.0, close=10.5, volume=2600))
    bars.append(_bar(23, open_=10.3, high=10.45, low=10.0, close=10.2, volume=1300))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=-2.8, last=10.2), bars)

    assert "次日洗盘确认" in _labels(result)


def test_level2_missing_does_not_output_deterministic_manipulation():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.6, high=11.2, low=10.0, close=10.1, volume=2600))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=-1.0, volume_ratio=3.5, last=10.1), bars)
    combined = " ".join(result["behavior_tags"] + result["behavior_evidence"] + [m["tooltip"] for m in result["kline_markers"]])

    assert "主力对倒" not in combined
    assert "庄家出货" not in combined
    assert result["need_level2_confirm"] is True


def test_kline_markers_have_required_shape():
    bars = _base_bars()
    bars.append(_bar(22, open_=10.4, high=12.0, low=10.0, close=10.3, volume=2600))
    result = MarketBehaviorEngine().analyze(_quote(change_pct=0.8, last=10.3), bars)

    assert result["kline_markers"]
    for marker in result["kline_markers"]:
        assert {"date", "type", "label", "price", "tooltip", "evidence"} <= set(marker)
        assert marker["tooltip"]
        assert isinstance(marker["evidence"], list)


def test_recent_days_scan_keeps_prior_week_markers():
    bars = _base_bars(35)
    risk_day = datetime(2026, 5, 20)
    bars[-4] = Bar("601012", "1d", risk_day, 10.4, 12.0, 10.0, 10.3, 2600, 2600000, source="unit_daily")
    result = MarketBehaviorEngine().analyze(_quote(change_pct=0.2, last=bars[-1].close), bars, recent_days=7)

    assert any(marker["date"] == risk_day.date().isoformat() for marker in result["kline_markers"])
    assert result["recent_marker_days"] == 7
