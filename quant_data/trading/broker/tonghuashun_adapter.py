from __future__ import annotations

from typing import Any

from .broker_config import BrokerConfig
from .broker_models import BrokerAccountSnapshot, BrokerConnectionStatus, BrokerOrder, BrokerPosition, BrokerTrade, LiveOrderAck, LiveOrderRequest
from .http_bridge_adapter import BridgeTransport, HttpBridgeBrokerAdapter


class TonghuashunBridgeBrokerAdapter(HttpBridgeBrokerAdapter):
    """Authorized Tonghuashun/SuperMind execution bridge.

    The retail desktop client is deliberately excluded. A connected bridge
    must identify itself as a Tonghuashun/SuperMind executor before any order
    can be routed through it.
    """

    ALLOWED_PROVIDERS = {"tonghuashun", "supermind", "ifind_supermind", "ths"}
    SOURCE = "authorized_tonghuashun_supermind_bridge"

    def __init__(self, config: BrokerConfig | None = None, *, transport: BridgeTransport | None = None) -> None:
        super().__init__(config, transport=transport)

    def health_check(self) -> BrokerConnectionStatus:
        status = super().health_check()
        if not status.connected:
            return status
        provider = str(status.raw.get("provider") or status.raw.get("broker") or "").strip().lower()
        if provider not in self.ALLOWED_PROVIDERS:
            return self._status(
                False,
                "blocked",
                "执行桥未声明同花顺/SuperMind 授权身份，已阻断自动交易",
                raw={**status.raw, "provider_identity_verified": False},
            )
        status.raw["provider_identity_verified"] = True
        return status

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        health = self.health_check()
        if not health.connected:
            return LiveOrderAck(False, "rejected", reason=health.message, raw_response=health.raw)
        return super().place_order(request)

    def get_account(self) -> BrokerAccountSnapshot:
        account = super().get_account()
        account.broker = "tonghuashun_supermind_bridge"
        account.source = self.SOURCE
        for position in account.positions:
            position.source = self.SOURCE
        return account

    def get_positions(self) -> list[BrokerPosition]:
        rows = super().get_positions()
        for row in rows:
            row.source = self.SOURCE
        return rows

    def get_orders(self) -> list[BrokerOrder]:
        rows = super().get_orders()
        for row in rows:
            row.source = self.SOURCE
        return rows

    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]:
        rows = super().get_trades(order_id)
        for row in rows:
            row.source = self.SOURCE
        return rows

    def _status(
        self,
        connected: bool,
        status: str,
        message: str,
        *,
        raw: dict[str, Any] | None = None,
    ) -> BrokerConnectionStatus:
        return BrokerConnectionStatus(
            connected=connected,
            status=status,
            broker="tonghuashun_supermind_bridge",
            message=message,
            live_trading_enabled=self.config.live_trading_enabled,
            order_confirm_required=self.config.order_confirm_required,
            raw=dict(raw or {}),
        )
