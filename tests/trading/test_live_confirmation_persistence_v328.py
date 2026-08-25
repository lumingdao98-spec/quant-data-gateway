from quant_data.live.live_sync_service import LiveSyncService
from quant_data.live.live_trading_engine import LiveTradingEngine
from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.broker.broker_config import BrokerConfig
from quant_data.trading.broker.broker_models import BrokerConnectionStatus, CancelOrderResult
from quant_data.trading.broker.disabled import DisabledBrokerAdapter


class _CancelBroker(DisabledBrokerAdapter):
    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self.cancelled_ids: list[str] = []

    def cancel_order(self, order_id: str) -> CancelOrderResult:
        self.cancelled_ids.append(order_id)
        return CancelOrderResult(True, order_id, "cancel_requested", "券商已受理撤单")


class _UnverifiedBroker:
    def __init__(self):
        self.data_calls = 0

    def health_check(self):
        return BrokerConnectionStatus(
            False,
            "blocked",
            "tonghuashun_supermind_bridge",
            "执行桥身份未通过",
        )

    def _unexpected(self, *args, **kwargs):
        self.data_calls += 1
        raise AssertionError("unverified broker data endpoint must not be called")

    get_account = _unexpected
    get_cash = _unexpected
    get_positions = _unexpected
    get_orders = _unexpected
    get_trades = _unexpected


def _config() -> BrokerConfig:
    return BrokerConfig(
        broker_type="http_bridge",
        feature_live_broker=True,
        live_trading_enabled=True,
        order_confirm_required=True,
        trade_whitelist_symbols=["300750"],
    )


def test_live_confirmation_queue_restores_sqlite_rows_and_refuses_replay(tmp_path):
    store = TradingStore(tmp_path / "live-confirm.sqlite")
    store.put(
        "manual_confirmations",
        {
            "task_id": "confirm-restored",
            "symbol": "300750",
            "action": "buy",
            "reason": "已由用户处理",
            "risk_flags": ["ORDER_CONFIRM_REQUIRED"],
            "status": "approved",
            "operator": "user",
            "payload": {"order": {"symbol": "300750", "side": "buy", "quantity": 100}},
        },
        mode="live",
        symbol="300750",
        record_id="confirm-restored",
    )
    broker = _CancelBroker(_config())
    engine = LiveTradingEngine(config=_config(), broker=broker, store=store)

    assert engine.confirm_queue.tasks["confirm-restored"].status == "approved"
    result = engine.approve_confirmation("confirm-restored")
    assert result["ok"] is False
    assert "already decided" in result["message"]


def test_live_cancel_resolves_local_order_to_broker_order_and_persists_lifecycle(tmp_path):
    store = TradingStore(tmp_path / "live-cancel.sqlite")
    config = _config()
    broker = _CancelBroker(config)
    engine = LiveTradingEngine(config=config, broker=broker, store=store)
    store.put(
        "orders",
        {
            "order_id": "local-order-1",
            "broker_order_id": "broker-order-99",
            "symbol": "300750",
            "side": "buy",
            "quantity": 100,
            "limit_price": 400,
            "status": "accepted",
            "broker_submitted": True,
            "session_id": engine.session.session_id,
        },
        mode="live",
        symbol="300750",
        session_id=engine.session.session_id,
        record_id="local-order-1",
    )

    result = engine.cancel_order("local-order-1")

    assert result["ok"] is True
    assert broker.cancelled_ids == ["broker-order-99"]
    stored = store.get("orders", "local-order-1")
    assert stored["status"] == "cancel_requested"
    assert stored["record_stage"] == "cancel"
    assert store.list("broker_raw_responses", mode="live", symbol="300750")


def test_live_cancel_never_sends_a_precheck_only_order_to_broker(tmp_path):
    store = TradingStore(tmp_path / "live-cancel-blocked.sqlite")
    config = _config()
    broker = _CancelBroker(config)
    engine = LiveTradingEngine(config=config, broker=broker, store=store)
    store.put(
        "orders",
        {"order_id": "precheck-only", "symbol": "300750", "status": "prechecked", "broker_submitted": False},
        mode="live",
        symbol="300750",
        record_id="precheck-only",
    )

    result = engine.cancel_order("precheck-only")

    assert result["ok"] is False
    assert broker.cancelled_ids == []
    assert "预检查" in result["reason"]


def test_live_sync_does_not_read_account_data_from_unverified_bridge(tmp_path):
    store = TradingStore(tmp_path / "unverified-sync.sqlite")
    broker = _UnverifiedBroker()

    result = LiveSyncService(broker, store).sync(session_id="live-unverified", force=True)

    assert result["data_available"] is False
    assert result["broker"]["status"] == "blocked"
    assert broker.data_calls == 0
