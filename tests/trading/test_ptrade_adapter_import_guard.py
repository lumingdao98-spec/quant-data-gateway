from quant_data.trading.broker import PTradeBrokerAdapter
from quant_data.trading.broker.ptrade_adapter import _order_status, _side


def test_ptrade_adapter_import_guard_never_crashes():
    status = PTradeBrokerAdapter().health_check()

    assert status.status in {"unsupported", "disabled", "unauthorized", "not_connected"}


def test_ptrade_chinese_order_fields_map_to_shared_lifecycle():
    assert _order_status("已报") == "accepted"
    assert _order_status("部成") == "partially_filled"
    assert _order_status("已成") == "filled"
    assert _order_status("已撤") == "cancelled"
    assert _order_status("废单") == "rejected"
    assert _side("证券买入") == "buy"
    assert _side("证券卖出") == "sell"
    assert _side("其他业务") == ""
