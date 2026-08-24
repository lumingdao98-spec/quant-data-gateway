from datetime import datetime

import quant_data.live.live_trading_engine as live_engine_module
from quant_data.live import LiveTradingEngine
from quant_data.persistence import TradingStore
from quant_data.trading.broker import BrokerConfig, SimulatorBrokerAdapter


def _engine(tmp_path):
    store = TradingStore(tmp_path / "live-precheck.sqlite")
    broker = SimulatorBrokerAdapter(initial_cash=100_000)
    config = BrokerConfig(
        broker_type="http_bridge",
        feature_live_broker=True,
        live_trading_enabled=True,
        order_confirm_required=True,
        trade_whitelist_symbols=["300750"],
        max_live_order_value=50_000,
        max_daily_live_order_count=5,
    )
    return LiveTradingEngine(config=config, broker=broker, store=store), broker, store


def _evidence(store, *, side="buy", quantity=100, provenance_mode="realtime_paper"):
    now = datetime.now().isoformat(timespec="seconds")
    store.put(
        "score_provenance",
        {
            "provenance_id": "sp-live-1",
            "symbol": "300750",
            "mode": provenance_mode,
            "decision_time": now,
            "final_score": 68.0,
            "stale_data": [],
            "dimension_readiness": {
                "auto_entry_eligible": True,
                "entry_block_reasons": [],
                "dimensions": [
                    {"key": "technical", "ready": True},
                    {"key": "information", "ready": True},
                    {"key": "fund_flow", "ready": True},
                ],
            },
        },
        mode=provenance_mode,
        symbol="300750",
        record_id="sp-live-1",
    )
    store.put(
        "risk_checks",
        {
            "id": "risk-live-1",
            "symbol": "300750",
            "mode": "live",
            "approved": True,
            "allowed": True,
            "order": {"symbol": "300750", "side": side, "quantity": quantity, "price": 10},
            "created_at": now,
        },
        mode="live",
        symbol="300750",
        record_id="risk-live-1",
    )
    return {
        "provenance_id": "sp-live-1",
        "risk_check_id": "risk-live-1",
        "quote": {"last": 10, "source": "unit_quote", "fetched_at": now},
        "quote_fetched_at": now,
        "data_freshness": {"fresh": True, "stale": False, "action": "allow"},
    }


def test_real_provider_blocks_confirmed_order_without_persisted_evidence(tmp_path, monkeypatch):
    engine, broker, _ = _engine(tmp_path)
    monkeypatch.setattr(
        live_engine_module,
        "market_session_status",
        lambda: {"is_trading_day": True, "is_trading_time": True},
    )

    result = engine.place_order(
        {"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10},
        confirmed=True,
    )

    assert result["ok"] is False
    assert result["data"]["precheck"]["reason_code"] == "score_provenance"
    assert broker.get_orders() == []


def test_real_provider_rechecks_all_evidence_before_broker_submission(tmp_path, monkeypatch):
    engine, broker, store = _engine(tmp_path)
    monkeypatch.setattr(
        live_engine_module,
        "market_session_status",
        lambda: {"is_trading_day": True, "is_trading_time": True},
    )
    payload = {
        "symbol": "300750",
        "side": "buy",
        "quantity": 100,
        "limit_price": 10,
        **_evidence(store),
    }

    result = engine.place_order(payload, confirmed=True)

    assert result["ok"] is True
    assert result["data"]["broker_ack"]["accepted"] is True
    assert len(broker.get_orders()) == 1


def test_real_provider_rejects_backtest_score_provenance(tmp_path, monkeypatch):
    engine, broker, store = _engine(tmp_path)
    monkeypatch.setattr(
        live_engine_module,
        "market_session_status",
        lambda: {"is_trading_day": True, "is_trading_time": True},
    )
    payload = {
        "symbol": "300750",
        "side": "buy",
        "quantity": 100,
        "limit_price": 10,
        **_evidence(store, provenance_mode="backtest"),
    }

    result = engine.place_order(payload, confirmed=True)

    assert result["ok"] is False
    assert result["data"]["precheck"]["reason_code"] == "score_provenance_mode"
    assert broker.get_orders() == []


def test_real_provider_blocks_buy_when_decision_dimensions_are_not_ready(tmp_path, monkeypatch):
    engine, broker, store = _engine(tmp_path)
    monkeypatch.setattr(
        live_engine_module,
        "market_session_status",
        lambda: {"is_trading_day": True, "is_trading_time": True},
    )
    evidence = _evidence(store)
    provenance = store.get("score_provenance", evidence["provenance_id"])
    provenance["dimension_readiness"] = {
        "auto_entry_eligible": False,
        "entry_block_reasons": ["信息面数据过期", "资金面仅有量价代理"],
        "dimensions": [],
    }
    store.put(
        "score_provenance",
        provenance,
        mode="realtime_paper",
        symbol="300750",
        record_id=evidence["provenance_id"],
    )

    result = engine.place_order(
        {
            "symbol": "300750",
            "side": "buy",
            "quantity": 100,
            "limit_price": 10,
            **evidence,
        },
        confirmed=True,
    )

    assert result["ok"] is False
    assert result["data"]["precheck"]["reason_code"] == "decision_dimensions_ready"
    assert "信息面数据过期" in result["data"]["precheck"]["reason"]
    assert broker.get_orders() == []


def test_confirmation_rechecks_freshness_instead_of_reusing_old_boolean(tmp_path, monkeypatch):
    engine, broker, store = _engine(tmp_path)
    monkeypatch.setattr(
        live_engine_module,
        "market_session_status",
        lambda: {"is_trading_day": True, "is_trading_time": True},
    )
    payload = {
        "symbol": "300750",
        "side": "buy",
        "quantity": 100,
        "limit_price": 10,
        **_evidence(store),
    }
    pending = engine.place_order(payload, confirmed=False)
    monkeypatch.setattr(engine, "_freshness_context_ok", lambda *args, **kwargs: False)

    approved = engine.approve_confirmation(pending["confirmation"]["task_id"])

    assert approved["ok"] is False
    assert approved["execution"]["data"]["precheck"]["reason_code"] == "fresh_market_data"
    assert broker.get_orders() == []


def test_disabled_broker_cannot_execute_after_human_confirmation(tmp_path):
    store = TradingStore(tmp_path / "disabled-confirm.sqlite")
    engine = LiveTradingEngine(
        config=BrokerConfig(
            feature_live_broker=True,
            live_trading_enabled=True,
            trade_whitelist_symbols=["300750"],
            max_live_order_value=50_000,
        ),
        store=store,
    )
    pending = engine.place_order({"symbol": "300750", "side": "buy", "quantity": 100, "limit_price": 10})

    approved = engine.approve_confirmation(pending["confirmation"]["task_id"])

    assert approved["ok"] is False
    assert approved["execution"]["data"]["precheck"]["reason_code"] == "broker_connected"
