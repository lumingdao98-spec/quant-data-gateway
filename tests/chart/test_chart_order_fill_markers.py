from quant_data.chart import TradingMarkerEngine


def test_chart_marker_engine_labels_order_and_fill():
    engine = TradingMarkerEngine()

    order = engine.from_order({"order_id": "o1", "symbol": "300750", "mode": "live", "status": "rejected", "created_at": "2026-06-05"})
    fill = engine.from_fill({"fill_id": "f1", "order_id": "o1", "symbol": "300750", "side": "sell", "quantity": 100, "price": 10, "filled_at": "2026-06-05"})

    assert order.marker_type == "rejected"
    assert fill.marker_type == "sell_fill"
