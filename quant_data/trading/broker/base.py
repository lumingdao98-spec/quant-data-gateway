from __future__ import annotations

from abc import ABC, abstractmethod

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


class BrokerAdapter(ABC):
    @abstractmethod
    def connect(self) -> BrokerConnectionStatus: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def health_check(self) -> BrokerConnectionStatus: ...

    @abstractmethod
    def get_account(self) -> BrokerAccountSnapshot: ...

    @abstractmethod
    def get_positions(self) -> list[BrokerPosition]: ...

    @abstractmethod
    def get_cash(self) -> BrokerCash: ...

    @abstractmethod
    def get_orders(self) -> list[BrokerOrder]: ...

    @abstractmethod
    def get_trades(self, order_id: str | None = None) -> list[BrokerTrade]: ...

    @abstractmethod
    def place_order(self, request: LiveOrderRequest) -> LiveOrderAck: ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> CancelOrderResult: ...

    @abstractmethod
    def query_order(self, order_id: str) -> BrokerOrder: ...
