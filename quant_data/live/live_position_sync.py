from __future__ import annotations

from typing import Any

from quant_data.trading.broker import BrokerAdapter, DisabledBrokerAdapter


class LivePositionSync:
    def __init__(self, broker: BrokerAdapter | None = None) -> None:
        self.broker = broker or DisabledBrokerAdapter()

    def snapshot(self) -> dict[str, Any]:
        return {
            "account": self.broker.get_account().to_dict(),
            "positions": [x.to_dict() for x in self.broker.get_positions()],
            "cash": self.broker.get_cash().to_dict(),
        }
