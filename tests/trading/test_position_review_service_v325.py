from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.position_review_service import PositionReviewService


def _position() -> dict:
    return {
        "symbol": "300750",
        "quantity": 200,
        "available_quantity": 200,
        "avg_cost": 400,
        "market_price": 380,
    }


def test_low_score_creates_persisted_exit_review(tmp_path):
    store = TradingStore(tmp_path / "reviews.sqlite")
    service = PositionReviewService(store=store)

    review = service.review(
        mode="realtime_paper",
        session_id="paper-1",
        symbol="300750",
        position=_position(),
        decision={"final_score": 40, "missing_data": ["orderbook_missing"]},
        decision_time="2026-07-20T15:10:00",
    )

    assert review["action"] == "exit"
    assert review["blocking_missing_data"] == []
    assert store.list("position_reviews", session_id="paper-1")[0]["review_id"] == review["review_id"]


def test_missing_quote_blocks_automatic_position_adjustment(tmp_path):
    service = PositionReviewService(store=TradingStore(tmp_path / "reviews.sqlite"))

    review = service.review(
        mode="realtime_paper",
        session_id="paper-1",
        symbol="300750",
        position={**_position(), "market_price": 0},
        decision={"final_score": 40, "missing_data": ["行情快照缺失"]},
        decision_time="2026-07-20T15:10:00",
    )

    assert review["action"] == "manual_review"
    assert review["blocking_missing_data"]


def test_live_review_never_submits_to_broker(tmp_path):
    service = PositionReviewService(store=TradingStore(tmp_path / "reviews.sqlite"))

    review = service.review(
        mode="live",
        session_id="live-1",
        symbol="300750",
        position=_position(),
        decision={"final_score": 38, "missing_data": []},
        decision_time="2026-07-20T15:10:00",
    )

    assert review["action"] == "exit"
    assert review["needs_confirmation"] is True
    assert review["execution_allowed"] is False
    assert review["broker_submitted"] is False
