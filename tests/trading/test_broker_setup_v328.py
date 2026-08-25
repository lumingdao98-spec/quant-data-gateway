from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api
import quant_data.trading.broker.broker_setup as broker_setup_module
from quant_data.trading.broker import BrokerConfig, BrokerSetupService


def test_broker_status_safe_config_redacts_accounts_and_token():
    config = BrokerConfig(
        broker_type="http_bridge",
        qmt_account_id="1234567890",
        ptrade_account_id="abcdefgh",
        http_bridge_token="top-secret-token",
    )

    safe = config.to_safe_dict()

    assert safe["qmt_account_id"] != "1234567890"
    assert safe["ptrade_account_id"] != "abcdefgh"
    assert safe["http_bridge_token"] == "已配置"
    assert "top-secret-token" not in str(safe)


def test_qmt_onboarding_checks_runtime_path_account_and_session(tmp_path, monkeypatch):
    userdata = tmp_path / "userdata_mini"
    userdata.mkdir()
    monkeypatch.setattr(broker_setup_module, "_module_available", lambda name: True)
    service = BrokerSetupService(
        BrokerConfig(
            broker_type="qmt",
            qmt_path=str(userdata),
            qmt_account_id="12345678",
            qmt_account_type="STOCK",
            qmt_session_id="10001",
        )
    )

    result = service.inspect("qmt")

    assert result["active"]["configuration_ready"] is True
    assert result["active"]["ready_to_connect"] is False
    assert result["safety"]["live_trading_enabled"] is False
    assert "LIVE_TRADING_ENABLED=false" in result["environment_templates"]["qmt"]
    assert "12345678" not in str(result)


def test_ptrade_default_is_reported_as_broker_hosted_not_fake_local_sdk():
    result = BrokerSetupService(BrokerConfig(broker_type="ptrade")).inspect("ptrade")

    assert result["active"]["deployment_model"] == "broker_hosted"
    assert result["active"]["configuration_ready"] is False
    assert any("券商托管" in reason for reason in result["active"]["missing_reasons"])


def test_setup_validation_endpoint_never_echoes_plain_credentials():
    secret = "plain-test-secret-should-not-return"
    account = "998877665544"
    response = TestClient(api.app).post(
        "/api/live-broker/setup/validate",
        json={
            "broker_type": "http_bridge",
            "http_bridge_url": "http://127.0.0.1:8765",
            "http_bridge_token": secret,
            "qmt_account_id": account,
        },
    )
    text = response.text
    payload = response.json()

    assert response.status_code == 200
    assert payload["validation_only"] is True
    assert payload["restart_required"] is True
    assert secret not in text
    assert account not in text


def test_tonghuashun_setup_separates_desktop_data_and_authorized_execution(monkeypatch):
    monkeypatch.setattr(broker_setup_module, "_module_available", lambda name: name == "iFinDPy")
    result = BrokerSetupService(
        BrokerConfig(
            broker_type="tonghuashun",
            http_bridge_url="http://127.0.0.1:8765",
            http_bridge_token="local-bridge-secret",
        )
    ).inspect("tonghuashun")

    active = result["active"]
    assert active["broker"] == "tonghuashun"
    assert active["ifind_sdk_available"] is True
    assert active["desktop_automatic_order"] is False
    assert active["execution_bridge_configured"] is True
    assert active["capabilities"]["自动委托"] == "待授权桥连接验收"
    assert active["configuration_ready"] is True
    assert active["ready_to_connect"] is False
    assert "BROKER_TYPE=tonghuashun" in result["environment_templates"]["tonghuashun"]
    assert "local-bridge-secret" not in str(result)


def test_tonghuashun_setup_reuses_local_companion_status_without_claiming_auto_order(tmp_path):
    launcher = tmp_path / "hexinlauncher.exe"
    order_app = tmp_path / "xiadan.exe"
    launcher.write_bytes(b"launcher")
    order_app.write_bytes(b"order")
    service = BrokerSetupService(
        BrokerConfig(broker_type="tonghuashun"),
        companion_status_provider=lambda: {
            "enabled": True,
            "launcher_path": str(launcher),
            "launcher_exists": True,
            "order_app_path": str(order_app),
            "order_app_exists": True,
        },
    )

    active = service.inspect("tonghuashun")["active"]

    assert active["desktop_companion_available"] is True
    assert active["desktop_companion_enabled"] is True
    assert active["desktop_launcher_source"] == "local_companion"
    assert active["desktop_order_app_available"] is True
    assert active["desktop_automatic_order"] is False
    assert active["execution_bridge_configured"] is False
    assert active["configuration_ready"] is False
