from __future__ import annotations

from quant_data.services.score_history_service import ScoreHistoryService


def test_daily_score_history_is_idempotent_per_day_mode_and_strategy(tmp_path):
    service = ScoreHistoryService(tmp_path / "scores.sqlite")
    first = {
        "score_date": "2026-08-25",
        "symbol": "300750",
        "name": "宁德时代",
        "mode": "realtime_paper",
        "strategy_family": "swing",
        "final_score": 61.0,
        "technical_score": 64.0,
        "action": "观察",
        "quality_status": "partial",
        "auto_entry_eligible": False,
    }
    updated = {**first, "final_score": 68.5, "action": "待确认"}

    assert service.save_daily_snapshots([first]) == 1
    assert service.save_daily_snapshots([updated]) == 1
    rows = service.daily_history("300750", days=30)

    assert len(rows) == 1
    assert rows[0]["final_score"] == 68.5
    assert rows[0]["action"] == "待确认"
    assert service.daily_status()["symbol_count"] == 1
