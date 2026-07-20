from quant_data.live.live_sync_service import LiveSyncService
from quant_data.persistence import TradingStore
from quant_data.trading.broker import (
    BrokerAccountSnapshot,
    BrokerCash,
    BrokerConnectionStatus,
    BrokerOrder,
    BrokerPosition,
    BrokerTrade,
    DisabledBrokerAdapter,
)


class FakeBroker(DisabledBrokerAdapter):
    def health_check(self):
        return BrokerConnectionStatus(True, "connected", "unit", "ok", True)

    def get_cash(self):
        return BrokerCash(available_cash=80_000, total_cash=80_000)

    def get_positions(self):
        return [BrokerPosition("300750", quantity=100, available_quantity=100, avg_cost=100, market_price=110, market_value=11_000)]

    def get_account(self):
        return BrokerAccountSnapshot("acct", "unit", self.get_cash(), self.get_positions(), authorized=True)

    def get_orders(self):
        return [BrokerOrder("bo1", "300750", "buy", "filled", 100, 100, broker_order_id="bo1", filled_quantity=100)]

    def get_trades(self, order_id=None):
        return [BrokerTrade("bt1", "bo1", "300750", "buy", 100, 100, 10_000, broker_order_id="bo1", fee=5)]


def test_live_sync_persists_account_positions_fills_ledger_and_marker(tmp_path):
    store = TradingStore(tmp_path / "sync.sqlite")
    result = LiveSyncService(FakeBroker(), store, cache_seconds=0).sync(session_id="live-unit", force=True)

    assert result["data_available"] is True
    assert store.list_normalized("broker_accounts", session_id="live-unit")
    assert store.list_normalized("broker_positions", session_id="live-unit", symbol="300750")
    assert store.list("fills", mode="live", session_id="live-unit")
    assert store.list_normalized("ledger_entries", mode="live", session_id="live-unit")
    assert store.list("chart_markers", mode="live", session_id="live-unit")
