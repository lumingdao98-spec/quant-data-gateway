from __future__ import annotations

from .base import BrokerAdapter
from .broker_config import BrokerConfig, load_broker_config
from .broker_models import (
    BrokerAccountSnapshot,
    BrokerCash,
    BrokerConnectionStatus,
    BrokerOrder,
    BrokerPosition,
    BrokerTrade,
    CancelOrderResult,
    LiveOrderAck,
    LiveOrderRequest,
)


class DisabledBrokerAdapter(BrokerAdapter):
    def __init__(self, config: BrokerConfig | None = None) -> None:
        self.config = config or load_broker_config()

    def connect(self) -> BrokerConnectionStatus:
        return self.health_check()

    def disconnect(self) -> None:
        return None

    def health_check(self) -> BrokerConnectionStatus:
        return BrokerConnectionStatus(
            connected=False,
            status="disabled",
            broker="disabled",
            message="真实券商默认关闭；未授权前只能 paper trading。",
            live_trading_enabled=False,
            order_confirm_required=True,
        )

    def get_account(self) -> BrokerAccountSnapshot:
        return BrokerAccountSnapshot(broker="disabled", authorized=False)

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def get_cash(self) -> BrokerCash:
        return BrokerCash()

    def get_orders(self) -> list[BrokerOrder]:
        return []

    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]:
        return []

    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck:
        return LiveOrderAck(
            accepted=False,
            status="rejected",
            reason="LIVE_TRADING_ENABLED=false 或券商适配器未启用，真实下单被拒绝。",
            raw_response={"request": request.to_dict(), "broker": "disabled"},
        )

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        return CancelOrderResult(ok=False, order_id=order_id, status="unsupported", reason="券商适配器禁用，无可撤订单")

    def query_order(self, order_id: str) -> BrokerOrder:
        return BrokerOrder(order_id=order_id, symbol="", side="", status="unknown", raw_response={"reason": "disabled"})
