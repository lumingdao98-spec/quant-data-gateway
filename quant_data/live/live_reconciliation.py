from __future__ import annotations

from typing import Any

from quant_data.trading.broker import BrokerAdapter, DisabledBrokerAdapter


class LiveReconciliation:
    def __init__(self, broker: BrokerAdapter | None = None) -> None:
        self.broker = broker or DisabledBrokerAdapter()

    def daily_check(self) -> dict[str, Any]:
        return {
            "ok": True,
            "status": self.broker.health_check().to_dict(),
            "orders": [x.to_dict() for x in self.broker.get_orders()],
            "trades": [x.to_dict() for x in self.broker.get_trades()],
            "message": "真实交易未启用时仅返回空对账快照。",
        }
