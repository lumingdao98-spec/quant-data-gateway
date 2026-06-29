from datetime import date, timedelta

from fastapi.testclient import TestClient

import quant_data.api as api


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
                "market_score": 55,
                "tags": ["ma_repair", "volume_confirm"],
                "risk_flags": [],
            }
        ],
        "strategy_family": "hybrid",
        "strategy_combo": ["score_driven", "ma_repair"],
        "position_sizing": "atr_risk",
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


def test_auto_trading_start_paper_resets_account_by_default():
    client = TestClient(api.app)
    payload = {
        "rows": [{"symbol": "300750", "total_score": 78, "technical_score": 84, "fundamental_score": 72, "information_score": 68, "market_score": 62}],
        "symbols": ["300750"],
        "strategy_combo": ["score_driven"],
        "initial_cash": 100000,
    }
    first = client.post("/api/auto-trading/start-paper", json=payload).json()
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

    second = client.post("/api/auto-trading/start-paper", json={**payload, "initial_cash": 50000}).json()
    second_session_id = second["session"]["session_id"]
    positions = client.get(f"/api/realtime-paper/sessions/{second_session_id}/positions").json()

    assert positions["ok"] is True
    assert positions["data"]["snapshot"]["cash"] == 50000.0
    assert positions["data"]["snapshot"]["positions"] == {}


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
