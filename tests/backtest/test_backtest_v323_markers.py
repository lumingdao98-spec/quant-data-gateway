from quant_data.chart import ChartAnnotationService


def test_backtest_order_and_fill_rebuild_markers():
    svc = ChartAnnotationService()

    rows = svc.rebuild(
        "300750",
        orders=[{"order_id": "o1", "symbol": "300750", "mode": "backtest", "status": "accepted", "side": "buy", "created_at": "2026-06-05", "limit_price": 10}],
        fills=[{"fill_id": "f1", "order_id": "o1", "symbol": "300750", "side": "buy", "quantity": 100, "price": 10, "filled_at": "2026-06-05"}],
        mode="backtest",
    )

    assert len(rows) == 2
    assert any(x["marker_type"] == "buy_fill" for x in rows)
