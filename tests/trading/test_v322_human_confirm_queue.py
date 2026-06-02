from quant_data.trading.human_confirm_queue import HumanConfirmQueue
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine


def test_human_confirm_queue_tracks_approve_and_reject():
    queue = HumanConfirmQueue()
    task = queue.enqueue(symbol="300750", action="buy", reason="risk review", risk_flags=["limit_up"])

    assert queue.list(status="pending")[0]["task_id"] == task.task_id
    assert queue.approve(task.task_id, operator="tester").status == "approved"

    second = queue.enqueue(symbol="600438", action="sell", reason="manual risk")
    assert queue.reject(second.task_id).status == "rejected"
    assert len(queue.list(status="pending")) == 0


def test_realtime_paper_status_exposes_human_confirm_pending_count():
    engine = RealtimePaperEngine()
    engine.human_confirm_queue.enqueue(symbol="300750", action="buy", reason="manual confirm")

    status = engine.status()
    assert status["paper_only"] is True
    assert status["real_broker_connected"] is False
    assert status["human_confirm_pending"] == 1
