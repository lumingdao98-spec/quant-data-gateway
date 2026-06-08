from quant_data.trading.broker import PTradeBrokerAdapter


def test_ptrade_adapter_import_guard_never_crashes():
    status = PTradeBrokerAdapter().health_check()

    assert status.status in {"unsupported", "disabled", "unauthorized", "not_connected"}
