from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
import pytest

import quant_data.api as api


@pytest.fixture(autouse=True)
def _verified_open_market(monkeypatch):
    monkeypatch.setattr(
        api,
        "_market_session",
        lambda market="CN": {
            "market": market,
            "status": "continuous_auction",
            "label": "交易中",
            "can_refresh": True,
            "now": "2026-06-01T10:00:00",
        },
    )


def test_auto_trading_one_click_config_and_start_paper():
    client = TestClient(api.app)
    payload = {
        "symbols": "300750，600438;510300",
        "strategy_family": "hybrid",
        "strategy_combo": ["score_driven", "ma_repair", "event_driven", "risk_control"],
        "position_sizing": "atr_risk",
        "interval_seconds": 15,
        "initial_cash": 120000,
        "risk_controls": {
            "stop_loss_pct": 7,
            "take_profit_pct": 16,
            "max_drawdown_pct": 12,
            "max_single_position_pct": 18,
            "max_total_position_pct": 70,
            "min_cash_pct": 20,
        },
        "event_watch": {
            "financial_reports": True,
            "half_year_reports": True,
            "exchange_announcements": True,
            "major_negative_news": True,
            "policy_industry_news": True,
        },
    }

    configured = client.post("/api/auto-trading/config/one-click", json=payload).json()

    assert configured["ok"] is True
    assert configured["data"]["symbols"] == ["300750", "600438", "510300"]
    assert configured["data"]["strategy_combo"] == ["score_driven", "ma_repair", "event_driven", "risk_control"]
    assert configured["data"]["position_sizing"] == "atr_risk"
    assert configured["data"]["risk_controls"]["stop_loss_pct"] == 7.0
    assert configured["data"]["risk_controls"]["max_drawdown_pct"] == 12.0
    assert configured["data"]["event_watch"]["half_year_reports"] is True
    assert configured["readiness"]["ready_for_paper"] is True

    started = client.post("/api/auto-trading/start-paper", json=payload).json()

    assert started["ok"] is True
    assert started["session"]["status"] == "running"
    assert started["config"]["symbols"] == ["300750", "600438", "510300"]
    assert started["config"]["strategy_combo"] == ["score_driven", "ma_repair", "event_driven", "risk_control"]
    assert started["readiness"]["ready_for_paper"] is True


def test_auto_trading_config_exposes_catalog_and_beginner_presets():
    client = TestClient(api.app)

    configured = client.post(
        "/api/auto-trading/config/one-click",
        json={"symbols": ["300750"], "strategy_combo": ["score_driven", "ma_repair", "risk_control"]},
    ).json()

    data = configured["data"]
    assert configured["ok"] is True
    assert "strategy_catalog" in data
    assert len(data["strategy_catalog"]) >= 55
    catalog_keys = {item["key"] for item in data["strategy_catalog"]}
    assert {"vwap_reclaim", "fake_order_cancel_watch", "market_breadth_filter", "dca_core_plan"} <= catalog_keys
    assert {"balanced", "defensive", "etf_rotation"}.issubset(set(data["beginner_presets"]))
    assert data["strategy_parameters"]["ma_repair"]["name"]
    assert data["strategy_parameters"]["ma_repair"]["category"]
    assert data["strategy_parameters"]["risk_control"]["beginner_note"]
    assert len(data["workflow_steps"]) == 5


def test_auto_trading_config_get_upgrades_minimal_cached_strategy_combo():
    client = TestClient(api.app)
    saved = client.post(
        "/api/auto-trading/config",
        json={"symbols": ["300750", "600438"], "strategy_combo": ["score_driven", "ma_repair"]},
    ).json()
    assert saved["ok"] is True
    assert saved["data"]["strategy_combo"] == ["score_driven", "ma_repair"]

    loaded = client.get("/api/auto-trading/config").json()

    data = loaded["data"]
    combo = set(data["strategy_combo"])
    assert loaded["ok"] is True
    assert data["strategy_combo_upgraded"] is True
    assert len(data["strategy_combo"]) >= 12
    assert {"fund_flow_watch", "vwap_reclaim", "global_commodity_map", "market_breadth_filter", "risk_control"} <= combo
    assert len(data["live_intraday_strategy_combo"]) >= len(data["default_strategy_combo"])
    assert data["strategy_parameters"]["vwap_reclaim"]["name"]


def test_auto_trading_config_exposes_strategy_matrix_and_decision_policy():
    client = TestClient(api.app)
    configured = client.post(
        "/api/auto-trading/config/one-click",
        json={
            "symbols": ["300750", "600438"],
            "strategy_combo": ["score_driven", "ma_repair", "fund_flow_watch", "vwap_reclaim", "risk_control"],
            "score_weights": {
                "technical": 0.34,
                "fundamental": 0.22,
                "information": 0.16,
                "fund_flow": 0.18,
                "market": 0.10,
            },
            "event_watch": {
                "financial_reports": True,
                "half_year_reports": True,
                "exchange_announcements": True,
                "major_negative_news": True,
            },
            "strategy_parameters": {
                "ma_repair": {
                    "enabled": True,
                    "position_sizing": "atr_risk",
                    "max_single_position_pct": 8,
                    "stop_loss_pct": 6,
                    "take_profit_pct": 15,
                    "max_strategy_drawdown_pct": 9,
                    "buy_threshold": 63,
                    "sell_threshold": 46,
                },
                "fund_flow_watch": {
                    "enabled": True,
                    "position_sizing": "score_weighted",
                    "max_single_position_pct": 6,
                    "stop_loss_pct": 5,
                    "take_profit_pct": 12,
                    "max_strategy_drawdown_pct": 8,
                    "buy_threshold": 66,
                    "sell_threshold": 48,
                },
                "vwap_reclaim": {
                    "enabled": True,
                    "position_sizing": "atr_risk",
                    "max_single_position_pct": 7,
                    "stop_loss_pct": 6,
                    "take_profit_pct": 13,
                    "max_strategy_drawdown_pct": 8,
                    "buy_threshold": 64,
                    "sell_threshold": 47,
                },
            },
        },
    ).json()

    assert configured["ok"] is True
    data = configured["data"]
    assert "parameter_schema" in data
    assert "strategy_matrix" in data
    assert "decision_policy" in data
    assert data["decision_policy"]["action_source"] == "screener_signal_map_first_then_realtime_score"
    assert any(item["key"] == "fund_flow" for item in data["integrated_score_dimensions"])
    assert any(item["key"] == "half_year_reports" and item["enabled"] for item in data["key_event_watchlist"])
    matrix = {row["key"]: row for row in data["strategy_matrix"]}
    assert matrix["ma_repair"]["max_strategy_drawdown_pct"] == 9.0
    assert matrix["ma_repair"]["buy_threshold"] == 63.0
    assert data["strategy_parameters"]["fund_flow_watch"]["take_profit_pct"] == 12.0
    assert matrix["vwap_reclaim"]["max_single_position_pct"] == 7.0
    assert matrix["vwap_reclaim"]["position_sizing"] == "atr_risk"


def test_realtime_paper_tick_hydrates_quote_when_price_missing(monkeypatch):
    client = TestClient(api.app)
    now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

    def fake_get_quote(symbol: str, force_refresh: bool = False):
        return api.Quote(
            symbol=symbol,
            name="Hydrated",
            ts=now,
            last=10.0,
            pre_close=9.6,
            open=9.8,
            high=10.2,
            low=9.7,
            volume=100000,
            amount=1000000,
            change=0.4,
            change_pct=4.17,
            source="unit_quote",
        )

    monkeypatch.setattr(api.service, "get_quote", fake_get_quote)
    started = client.post(
        "/api/auto-trading/start-paper",
        json={
            "rows": [{"symbol": "399993", "total_score": 78, "technical_score": 84, "fundamental_score": 72, "information_score": 68, "market_score": 62}],
            "symbols": ["399993"],
            "strategy_combo": ["score_driven"],
            "initial_cash": 100000,
        },
    ).json()

    tick = client.post(
        "/api/realtime-paper/tick",
        json={"session_id": started["session"]["session_id"], "symbol": "399993", "manual_replay": True, "now": now.isoformat(), "news_ts": now.isoformat()},
    ).json()

    assert tick["ok"] is True
    assert tick["signal"]["quote_price"] == 10.0
    assert tick["signal"]["name"] == "Hydrated"
    assert "quote_hydrated_from_market_service" in " ".join(tick["signal"]["evidence"])
    assert tick["orders"]


def test_auto_trading_reuses_screener_signal_profile_for_paper_tick():
    client = TestClient(api.app)
    payload = {
        "rows": [
            {
                "symbol": "300750",
                "name": "CATL",
                "total_score": 76,
                "technical_score": 82,
                "fundamental_score": 66,
                "information_score": 61,
                "fund_flow_score": 58,
                "market_score": 55,
                "tags": ["ma_repair", "volume_confirm"],
                "risk_flags": [],
            }
        ],
        "strategy_family": "hybrid",
        "strategy_combo": ["score_driven", "ma_repair"],
        "position_sizing": "atr_risk",
        "event_watch": {"financial_reports": True, "half_year_reports": True},
        "strategy_parameters": {
            "ma_repair": {
                "position_sizing": "atr_risk",
                "stop_loss_pct": 6,
                "take_profit_pct": 14,
                "max_drawdown_pct": 10,
            }
        },
        "risk_controls": {"stop_loss_pct": 7, "take_profit_pct": 16, "max_drawdown_pct": 12},
    }

    configured = client.post("/api/auto-trading/config/one-click", json=payload).json()

    profile = configured["data"]["screener_signal_map"]["300750"]
    assert profile["action"] == "buy"
    assert profile["technical_score"] == 82.0
    assert configured["data"]["strategy_parameters"]["ma_repair"]["stop_loss_pct"] == 6.0

    started = client.post("/api/auto-trading/start-paper", json=payload).json()
    session_id = started["session"]["session_id"]

    assert started["session"]["config"]["screener_signal_map"]["300750"]["final_score"] == 76.0

    tick = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": session_id,
            "symbol": "300750",
            "price": 100,
            "ts": "2026-06-01T10:00:00",
            "manual_replay": True,
            "news_ts": "2026-06-01T09:55:00",
        },
    ).json()

    assert tick["ok"] is True
    assert tick["signal"]["technical_score"] == 82.0
    assert tick["signal"]["fundamental_score"] == 66.0
    assert tick["signal"]["information_score"] == 61.0
    assert tick["signal"]["fund_flow_score"] == 58.0
    assert tick["signal"]["event_watch_context"]["event_watch_enabled"] is True
    assert tick["signal"]["strategy_controls"]["stop_loss_pct"] == 6.0
    assert "screener_target_hint" in " ".join(tick["signal"]["evidence"])


def test_realtime_paper_applies_strategy_position_and_stop_controls():
    client = TestClient(api.app)
    payload = {
        "rows": [
            {
                "symbol": "399991",
                "name": "CATL",
                "total_score": 78,
                "technical_score": 84,
                "fundamental_score": 72,
                "information_score": 68,
                "market_score": 62,
                "tags": ["ma_repair", "volume_confirm"],
            }
        ],
        "symbols": ["399991"],
        "strategy_family": "hybrid",
        "strategy_combo": ["score_driven", "ma_repair"],
        "position_sizing": "score_weighted",
        "strategy_parameters": {
            "ma_repair": {
                "stop_loss_pct": 6,
                "take_profit_pct": 14,
                "max_drawdown_pct": 10,
                "max_single_position_pct": 5,
            }
        },
        "risk_controls": {"stop_loss_pct": 8, "take_profit_pct": 18, "max_drawdown_pct": 18, "max_single_position_pct": 20},
        "initial_cash": 100000,
    }
    started = client.post("/api/auto-trading/start-paper", json=payload).json()
    session_id = started["session"]["session_id"]

    first = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": session_id,
            "symbol": "399991",
            "price": 10,
            "ts": "2026-06-01T10:00:00",
            "manual_replay": True,
            "news_ts": "2026-06-01T09:55:00",
        },
    ).json()

    assert first["ok"] is True
    assert first["signal"]["action"] in {"buy", "add"}
    assert first["signal"]["target_weight"] == 0.05
    assert first["signal"]["strategy_controls"]["max_single_position_pct"] == 5.0
    assert first["orders"] and first["orders"][0]["quantity"] == 500

    second = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": session_id,
            "symbol": "399991",
            "price": 9.35,
            "ts": "2026-06-02T10:00:00",
            "manual_replay": True,
            "news_ts": "2026-06-02T09:55:00",
        },
    ).json()

    assert second["ok"] is True
    assert second["signal"]["action"] == "sell"
    assert second["signal"]["target_weight"] == 0.0
    assert "stop_loss_triggered=6.00%" in " ".join(second["signal"]["evidence"])
    assert second["orders"] and second["orders"][0]["side"] == "sell"


def test_realtime_paper_event_watch_blocks_major_negative_news_buy():
    client = TestClient(api.app)
    payload = {
        "rows": [
            {
                "symbol": "600438",
                "name": "Tongwei",
                "total_score": 80,
                "technical_score": 82,
                "fundamental_score": 75,
                "information_score": 70,
                "market_score": 62,
            }
        ],
        "symbols": ["600438"],
        "strategy_combo": ["score_driven", "event_driven"],
        "event_watch": {"financial_reports": True, "major_negative_news": True, "exchange_announcements": True},
        "initial_cash": 100000,
    }
    started = client.post("/api/auto-trading/start-paper", json=payload).json()
    session_id = started["session"]["session_id"]

    tick = client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": session_id,
            "symbol": "600438",
            "price": 10,
            "ts": "2026-06-01T10:00:00",
            "manual_replay": True,
            "news_ts": "2026-06-01T09:55:00",
            "major_negative_news": True,
        },
    ).json()

    assert tick["ok"] is True
    assert tick["signal"]["action"] == "avoid"
    assert tick["signal"]["event_watch_context"]["veto"] is True
    assert "major_negative_news" in tick["signal"]["event_watch_context"]["evidence"]
    assert tick["orders"] == []


def test_auto_trading_start_paper_resets_account_when_explicitly_requested():
    client = TestClient(api.app)
    payload = {
        "rows": [{"symbol": "300750", "total_score": 78, "technical_score": 84, "fundamental_score": 72, "information_score": 68, "market_score": 62}],
        "symbols": ["300750"],
        "strategy_combo": ["score_driven"],
        "initial_cash": 100000,
    }
    first = client.post("/api/auto-trading/start-paper", json={**payload, "reset_account": True}).json()
    first_session_id = first["session"]["session_id"]
    client.post(
        "/api/realtime-paper/tick",
        json={
            "session_id": first_session_id,
            "symbol": "300750",
            "price": 10,
            "ts": "2026-06-01T10:00:00",
            "manual_replay": True,
            "news_ts": "2026-06-01T09:55:00",
        },
    )

    second = client.post(
        "/api/auto-trading/start-paper",
        json={**payload, "initial_cash": 50000, "reset_account": True},
    ).json()
    second_session_id = second["session"]["session_id"]
    positions = client.get(f"/api/realtime-paper/sessions/{second_session_id}/positions").json()

    assert positions["ok"] is True
    assert positions["data"]["snapshot"]["cash"] == 50000.0
    assert positions["data"]["snapshot"]["positions"] == {}


def test_auto_trading_repeated_start_preserves_active_account_and_positions():
    from quant_data.trading.paper_account import PaperFill

    client = TestClient(api.app)
    payload = {
        "symbols": ["600438"],
        "strategy_combo": ["score_driven"],
        "initial_cash": 100000,
        "reset_account": True,
    }
    first = client.post("/api/auto-trading/start-paper", json=payload).json()
    session_id = first["session"]["session_id"]
    account = api.realtime_paper_engine_v323.engines[session_id].account
    account.apply_fill(
        PaperFill(
            order_id="preserved-buy",
            symbol="600438",
            side="buy",
            quantity=100,
            price=12.0,
            amount=1200.0,
            fee=1.0,
        )
    )
    api.realtime_paper_engine_v323.sync_engine_state(session_id)

    repeated = client.post(
        "/api/auto-trading/start-paper",
        json={**payload, "symbols": ["600438", "510300"], "initial_cash": 50000, "reset_account": False},
    ).json()
    positions = client.get(f"/api/realtime-paper/sessions/{session_id}/positions").json()

    assert repeated["session"]["session_id"] == session_id
    assert repeated["reused_session"] is True
    assert repeated["account_preserved"] is True
    assert repeated["session"]["symbols"] == ["600438", "510300"]
    assert positions["data"]["snapshot"]["initial_cash"] == 100000.0
    assert positions["data"]["snapshot"]["positions"]["600438"]["quantity"] == 100


def _v323_bars(symbol: str = "399992", count: int = 90) -> list[dict]:
    start = date(2026, 1, 1)
    rows = []
    for i in range(count):
        close = 10.0 + i * 0.06
        rows.append(
            {
                "symbol": symbol,
                "date": (start + timedelta(days=i)).isoformat(),
                "open": close - 0.04,
                "high": close + 0.16,
                "low": close - 0.18,
                "close": close,
                "volume": 1_000_000 + i * 5000,
                "amount": (1_000_000 + i * 5000) * close,
            }
        )
    return rows


def test_v323_backtest_embeds_auto_trading_controls(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "backtest_storage_v319", api.BacktestStorage(tmp_path))
    client = TestClient(api.app)
    payload = {
        "symbols": ["399992"],
        "limit": 90,
        "warmup_bars": 10,
        "use_auto_config": True,
        "auto_trading_config": {
            "config_id": "test-auto",
            "symbols": ["399992"],
            "strategy_family": "hybrid",
            "strategy_combo": ["score_driven", "ma_repair"],
            "position_sizing": "atr_risk",
            "risk_controls": {
                "stop_loss_pct": 8,
                "take_profit_pct": 18,
                "max_drawdown_pct": 18,
                "max_single_position_pct": 20,
                "max_total_position_pct": 80,
                "min_cash_pct": 15,
            },
            "strategy_parameters": {
                "ma_repair": {
                    "enabled": True,
                    "position_sizing": "atr_risk",
                    "stop_loss_pct": 6,
                    "take_profit_pct": 14,
                    "max_drawdown_pct": 10,
                    "max_single_position_pct": 5,
                }
            },
            "screener_signal_map": {
                "399992": {
                    "symbol": "399992",
                    "name": "AutoTest",
                    "action": "buy",
                    "final_score": 76,
                    "technical_score": 82,
                    "fundamental_score": 66,
                    "information_score": 61,
                    "fund_flow_score": 58,
                    "market_score": 55,
                    "target_weight_hint_pct": 5,
                    "strategy_tags": ["ma_repair"],
                    "risk_flags": [],
                    "missing_data": [],
                    "evidence": ["unit-test screener profile"],
                    "source_row": {"symbol": "399992", "score": 76, "total_score": 76, "grade": "B", "date": "2026-01-10"},
                    "source": "unit_test",
                }
            },
        },
        "market_data": {"399992": _v323_bars()},
    }

    response = client.post("/api/backtest/v323/run", json=payload).json()

    assert response["ok"] is True
    data = response["data"]
    assert data["auto_trading_config_applied"] is True
    assert data["config"]["max_single_position_pct"] == 0.05
    assert data["config"]["position_pct"] == 0.8
    assert data["config"]["cash_reserve_pct"] == 0.15
    assert data["config"]["stop_loss_pct"] == 6.0
    assert data["config"]["take_profit_pct"] == 14.0
    assert data["strategy_parameters"]["ma_repair"]["max_single_position_pct"] == 5
    profile = data["screener_signal_profiles"]["399992"]
    assert profile["action"] == "buy"
    assert profile["final_score"] == 76.0
    controls = data["effective_auto_controls"]["symbols"]["399992"]
    assert controls["selected_strategy"] == "ma_repair"
    assert controls["effective_position_weight"] == 0.05
    assert controls["effective_stop_loss_pct"] == 6.0
    assert data["params_cn"]["自动交易配置"] == "已接入 V3.23 回测内核"


def test_legacy_backtest_get_can_use_saved_auto_trading_config():
    client = TestClient(api.app)
    payload = {
        "rows": [
            {
                "symbol": "300750",
                "name": "宁德时代",
                "total_score": 76,
                "technical_score": 82,
                "fundamental_score": 66,
                "information_score": 61,
                "fund_flow_score": 58,
                "market_score": 55,
                "tags": ["ma_repair", "volume_confirm"],
            }
        ],
        "symbols": ["300750"],
        "strategy_combo": ["score_driven", "ma_repair"],
        "position_sizing": "atr_risk",
        "strategy_parameters": {
            "ma_repair": {
                "stop_loss_pct": 6,
                "take_profit_pct": 14,
                "max_drawdown_pct": 10,
                "max_single_position_pct": 5,
            }
        },
        "risk_controls": {"stop_loss_pct": 8, "take_profit_pct": 18, "max_drawdown_pct": 18, "max_single_position_pct": 20},
    }
    client.post("/api/auto-trading/config/one-click", json=payload)

    response = client.get(
        "/api/backtest/run",
        params={"symbol": "300750", "use_auto_config": "true", "limit": 120, "legacy": "true"},
    ).json()

    assert response["ok"] is True
    data = response["data"]
    assert data["auto_trading_config_applied"] is True
    assert data["config"]["strategy_combo"] == ["score_driven", "ma_repair"]
    assert data["config"]["stop_loss_pct"] == 6.0
    assert data["config"]["take_profit_pct"] == 14.0
    assert data["strategy_parameters"]["ma_repair"]["max_single_position_pct"] == 5.0
    assert data["effective_auto_controls"]["symbols"]["300750"]["selected_strategy"] == "ma_repair"
