from quant_data.trading.broker import BrokerConfig, PTradeBrokerAdapter, QmtBrokerAdapter


def test_qmt_and_ptrade_never_report_connected_without_sdk_and_authorization():
    qmt = QmtBrokerAdapter(BrokerConfig(broker_type="qmt"))
    ptrade = PTradeBrokerAdapter(BrokerConfig(broker_type="ptrade", ptrade_module="definitely_missing_ptrade_sdk"))

    assert qmt.health_check().status in {"unsupported", "disabled", "unauthorized", "not_connected"}
    assert ptrade.health_check().status == "unsupported"
    assert qmt.health_check().connected is False
    assert ptrade.health_check().connected is False
