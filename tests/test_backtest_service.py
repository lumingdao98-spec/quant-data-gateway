from datetime import datetime, timedelta

from quant_data.models import Bar
from quant_data.services.backtest_service import BacktestConfig, BacktestService


def _trend_bars(count: int = 140) -> list[Bar]:
    base = datetime(2025, 1, 1)
    rows = []
    for i in range(count):
        price = 20 + i * 0.18
        rows.append(
            Bar(
                symbol="300750",
                frame="1d",
                ts=base + timedelta(days=i),
                open=price * 0.995,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=500_000 + i * 500,
                amount=price * (500_000 + i * 500),
                source="unit:qfq",
            )
        )
    return rows


def test_backtest_ma_cross_returns_metrics_and_assumptions():
    result = BacktestService().run("300750", _trend_bars(), BacktestConfig(strategy="ma_cross"))

    assert result["strategy"] == "ma_cross"
    assert result["final_equity"] > 0
    assert result["total_return_pct"] > 0
    assert "buy_hold_return_pct" in result
    assert "excess_return_pct" in result
    assert result["trade_count"] >= 1
    assert result["equity_curve"]
    assert result["data_quality"]["bars"] == 140
    assert any("下一交易日开盘成交" in x for x in result["assumptions"])


def test_backtest_unknown_strategy_falls_back_to_ma_cross():
    result = BacktestService().run("300750", _trend_bars(), BacktestConfig(strategy="missing"))

    assert result["strategy"] == "ma_cross"
    assert result["params"]["fee_rate"] >= 0


def test_backtest_score_driven_outputs_scores_kline_and_markers():
    result = BacktestService().run(
        "300750",
        _trend_bars(180),
        BacktestConfig(strategy="score_driven", buy_score=55, sell_score=45),
    )

    assert result["strategy"] == "score_driven"
    assert result["score_series"]
    assert result["kline"]
    assert len(result["kline"]) == result["data_quality"]["bars"]
    assert {"score", "ma20", "ma60", "macd_hist", "volume_ratio", "risk_penalty", "markers", "anomaly_markers"} <= set(result["kline"][-1])
    assert result["score_formula"]["scale"] == "0-100"
    assert "trend_score*0.34" in result["score_formula"]["formula"]
    assert "anomaly_markers" in result["data_quality"]
    assert result["markers"]
    assert {m["side"] for m in result["markers"]} <= {"buy", "sell"}
