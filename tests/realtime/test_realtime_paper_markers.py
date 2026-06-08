from quant_data.chart import ChartAnnotationService


def test_realtime_order_marker_created():
    svc = ChartAnnotationService()
    marker = svc.add_order({"order_id": "o1", "symbol": "300750", "mode": "realtime_paper", "status": "needs_confirmation", "created_at": "2026-06-05", "side": "buy", "quantity": 100})

    assert marker["marker_type"] == "needs_confirmation"
