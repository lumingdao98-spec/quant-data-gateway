from quant_data.trading.broker import QmtBrokerAdapter


def test_qmt_adapter_import_guard_never_crashes():
    status = QmtBrokerAdapter().health_check()

    assert status.status in {"unsupported", "disabled", "unauthorized", "not_connected"}
