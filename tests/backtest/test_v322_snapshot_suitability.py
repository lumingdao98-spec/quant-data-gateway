from datetime import datetime, timedelta

from quant_data.backtest.historical_snapshot import HistoricalScreenerSnapshotBuilder
from quant_data.models import Bar


def _bars(symbol: str, count: int = 90) -> list[Bar]:
    start = datetime(2026, 1, 1)
    rows = []
    for idx in range(count):
        close = 10 + idx * 0.08
        rows.append(
            Bar(
                symbol=symbol,
                frame="1d",
                ts=start + timedelta(days=idx),
                open=close * 0.99,
                high=close * 1.02,
                low=close * 0.98,
                close=close,
                volume=1_000_000 + idx * 1000,
                amount=close * (1_000_000 + idx * 1000),
                source="unit",
            )
        )
    return rows


def test_historical_screener_snapshot_is_point_in_time_and_hashable():
    builder = HistoricalScreenerSnapshotBuilder()
    snapshot = builder.build_historical_snapshot(
        "2026-02-20",
        "2026-02-20 15:05:00",
        ["300750", "510300"],
        bars_by_symbol={"300750": _bars("300750"), "510300": _bars("510300")},
        market_inputs={"index_change_pct": -0.3, "turnover_pct": 1.2},
    )

    assert snapshot["row_count"] == 2
    assert snapshot["immutable_hash"]
    assert snapshot["pit_note"]
    assert all(row["asof_time"] == "2026-02-20 15:05:00" for row in snapshot["rows"])
    assert all("strategy_family" in row for row in snapshot["rows"])
    assert snapshot["market_state"]["market_regime"] in {"bull", "neutral", "bear", "volatile", "range"}
