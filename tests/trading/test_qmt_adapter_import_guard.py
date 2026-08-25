from quant_data.trading.broker import QmtBrokerAdapter
from quant_data.trading.broker.qmt_adapter import _order_status, _side


def test_qmt_adapter_import_guard_never_crashes():
    status = QmtBrokerAdapter().health_check()

    assert status.status in {"unsupported", "disabled", "unauthorized", "not_connected"}


def test_qmt_order_status_maps_xttrader_states_to_shared_lifecycle():
    assert _order_status(48) == "submitted"
    assert _order_status(50) == "accepted"
    assert _order_status(52) == "cancel_requested"
    assert _order_status(55) == "partially_filled"
    assert _order_status(56) == "filled"
    assert _order_status(57) == "rejected"
    assert _order_status(255) == "unknown"


def test_qmt_side_does_not_treat_unknown_values_as_sell():
    assert _side(23) == "buy"
    assert _side(24) == "sell"
    assert _side("买入") == "buy"
    assert _side("unexpected") == ""
