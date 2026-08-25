from __future__ import annotations

from quant_data.notifications import MobileAlertConfig, MobileNotificationService


def test_mobile_alert_is_disabled_by_default_and_never_calls_network():
    calls = []
    service = MobileNotificationService(
        MobileAlertConfig(),
        transport=lambda url, payload, headers: calls.append(url) or {"ok": True},
    )

    result = service.send({"event_type": "needs_confirmation", "symbol": "300750"})

    assert result["ok"] is False
    assert result["status"] == "disabled"
    assert calls == []


def test_mobile_alert_redacts_webhook_token_and_sends_provider_payload():
    captured = {}

    def transport(url, payload, headers):
        captured.update({"url": url, "payload": payload, "headers": headers})
        return {"errcode": 0, "access_token": "must-not-surface"}

    service = MobileNotificationService(
        MobileAlertConfig(
            enabled=True,
            provider="dingtalk",
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=plain-secret-token",
            minimum_level="warning",
            cooldown_seconds=0,
        ),
        transport=transport,
    )

    status = service.status()
    result = service.send(
        {
            "event_type": "needs_confirmation",
            "symbol": "300750",
            "side": "buy",
            "quantity": 100,
            "price": 300,
            "status": "needs_confirmation",
        }
    )

    assert "plain-secret-token" not in str(status)
    assert result["ok"] is True
    assert captured["payload"]["msgtype"] == "markdown"
    assert result["provider_response"]["access_token"] == "已隐藏"
