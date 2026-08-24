from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.tonghuashun_companion import TonghuashunCompanion


def build_companion(tmp_path: Path) -> TonghuashunCompanion:
    return TonghuashunCompanion(
        store=TradingStore(tmp_path / "trading.sqlite"),
        config_db_path=tmp_path / "integrations.sqlite",
        env={},
    )


def test_companion_is_disabled_and_has_no_order_api_by_default(tmp_path):
    service = build_companion(tmp_path)
    status = service.status()
    assert status["enabled"] is False
    assert status["official_order_api"] is False
    assert status["automatic_order_submission"] is False
    assert status["broker_adapter"] is False


def test_companion_configures_and_only_launches_explicit_local_exe(tmp_path, monkeypatch):
    service = build_companion(tmp_path)
    launcher = tmp_path / "hexinlauncher.exe"
    order_app = tmp_path / "xiadan.exe"
    launcher.write_bytes(b"MZ")
    order_app.write_bytes(b"MZ")
    calls = []
    monkeypatch.setattr(
        "quant_data.trading.tonghuashun_companion.subprocess.Popen",
        lambda args, **kwargs: calls.append((args, kwargs)) or SimpleNamespace(pid=1234),
    )
    configured = service.configure({"enabled": True, "launcher_path": str(launcher), "order_app_path": str(order_app)})
    launched = service.launch("order")
    assert configured["ok"] is True
    assert configured["data"]["ready_to_launch"] is True
    assert launched["ok"] is True
    assert calls[0][0] == [str(order_app)]
    assert launched["data"]["broker_submitted"] is False


def test_reminder_never_claims_broker_submission_or_fill(tmp_path):
    service = build_companion(tmp_path)
    service.store.put(
        "score_provenance",
        {
            "provenance_id": "score-1",
            "symbol": "300750",
            "mode": "realtime_paper",
            "decision_time": datetime.now().isoformat(timespec="seconds"),
            "final_trade_score": 68.0,
            "dimension_readiness": {"auto_entry_eligible": True, "entry_block_reasons": []},
        },
        mode="realtime_paper",
        symbol="300750",
        record_id="score-1",
    )
    service.store.put(
        "risk_checks",
        {
            "symbol": "300750",
            "mode": "live",
            "approved": True,
            "order": {"symbol": "300750", "side": "buy", "quantity": 100},
        },
        mode="live",
        symbol="300750",
        record_id="risk-1",
    )
    result = service.create_reminder({
        "symbol": "300750", "name": "宁德时代", "side": "buy", "quantity": 100,
        "limit_price": 420.5, "risk_approved": True, "risk_check_id": "risk-1", "provenance_id": "score-1",
    })
    assert result["ok"] is True
    assert result["data"]["status"] == "ready_for_manual_entry"
    assert result["data"]["broker_submitted"] is False
    assert result["data"]["fill_verified"] is False
    assert result["data"]["decision_snapshot"]["final_trade_score"] == 68.0
    assert service.list_reminders()[0]["estimated_amount"] == 42050.0


def test_reminder_blocks_expired_score_provenance(tmp_path):
    service = build_companion(tmp_path)
    service.store.put(
        "score_provenance",
        {
            "provenance_id": "score-stale",
            "symbol": "300750",
            "mode": "realtime_paper",
            "decision_time": (datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds"),
            "dimension_readiness": {"auto_entry_eligible": True, "entry_block_reasons": []},
        },
        mode="realtime_paper",
        symbol="300750",
        record_id="score-stale",
    )
    service.store.put(
        "risk_checks",
        {
            "symbol": "300750",
            "mode": "live",
            "approved": True,
            "order": {"symbol": "300750", "side": "buy", "quantity": 100},
        },
        mode="live",
        symbol="300750",
        record_id="risk-stale",
    )

    result = service.create_reminder(
        {
            "symbol": "300750",
            "side": "buy",
            "quantity": 100,
            "limit_price": 420.5,
            "risk_check_id": "risk-stale",
            "provenance_id": "score-stale",
        }
    )

    assert result["ok"] is False
    assert result["data"]["score_provenance_recent"] is False
    assert any("评分溯源已过期" in reason for reason in result["data"]["risk_reasons"])


def test_risk_blocked_reminder_is_recorded_but_not_ready(tmp_path):
    service = build_companion(tmp_path)
    result = service.create_reminder({
        "symbol": "600438", "side": "sell", "quantity": 100, "limit_price": 12.8,
        "risk_approved": False, "risk_reasons": ["行情过期"],
    })
    assert result["ok"] is False
    assert result["data"]["status"] == "risk_blocked"
    assert "行情过期" in result["data"]["risk_reasons"]


def test_client_risk_boolean_cannot_create_ready_manual_ticket(tmp_path):
    service = build_companion(tmp_path)

    result = service.create_reminder(
        {
            "symbol": "300750",
            "side": "buy",
            "quantity": 100,
            "limit_price": 420.5,
            "risk_approved": True,
            "risk_check_id": "missing-risk",
            "provenance_id": "missing-score",
        }
    )

    assert result["ok"] is False
    assert result["data"]["status"] == "risk_blocked"
    assert any("服务端" in reason for reason in result["data"]["risk_reasons"])
