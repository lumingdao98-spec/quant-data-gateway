from __future__ import annotations

import pytest

from quant_data.indicators import support_resistance


def test_resistance_distance_is_positive_for_upper_resistance():
    sr = support_resistance([19.60] * 60, [10.0] * 60, [15.04] * 60)

    assert sr["resistance_dist_pct"] == pytest.approx((19.60 / 15.04 - 1) * 100, rel=1e-3)
    assert sr["resistance_dist_pct"] > 0
    assert sr["resistance_status"] == "压力上方空间"


def test_breakthrough_resistance_has_status():
    sr = support_resistance([19.60] * 60, [10.0] * 60, [20.0] * 60)

    assert sr["resistance_status"] == "已突破压力"


def test_breakdown_support_has_status():
    sr = support_resistance([20.0] * 60, [16.0] * 60, [15.0] * 60)

    assert sr["support_status"] == "已跌破支撑"
