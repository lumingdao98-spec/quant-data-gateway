from __future__ import annotations

from quant_data.trading.realtime_paper_engine import RealtimePaperEngine


def _payload(recent_information: dict, future_event_calendar: dict | None = None) -> dict:
    timestamp = "2026-08-24T10:00:00"
    return {
        "symbol": "600438",
        "price": 12.0,
        "ts": timestamp,
        "manual_replay": True,
        "quote": {"last": 12.0, "ts": timestamp, "amount": 100_000_000},
        "intraday_ts": timestamp,
        "news_ts": timestamp,
        "technical_ts": timestamp,
        "company_profile_ts": timestamp,
        "score_source": "unit_v326",
        "screening_score": 80,
        "daily_k_score": 80,
        "intraday_score": 80,
        "technical_score": 80,
        "fundamental_score": 75,
        "information_score": 75,
        "fund_flow_score": 70,
        "market_score": 65,
        "recent_information": recent_information,
        "future_event_calendar": future_event_calendar or {},
    }


def test_paper_buy_is_blocked_when_information_is_not_trade_eligible():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["600438"], "initial_cash": 100_000})
    result = engine.tick(_payload({
        "auto_buy_eligible": False,
        "stale": False,
        "scoreable_count": 0,
        "quality_status": "仅观察/需刷新",
    }))

    assert result["signal"]["action"] == "hold"
    assert result["orders"] == []
    assert result["signal"]["event_watch_context"]["block_new_position"] is True


def test_rule_inferred_calendar_alone_does_not_block_paper_buy():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["600438"], "initial_cash": 100_000})
    calendar = {
        "events": [{
            "title": "股指期货/期权交割观察日",
            "confirmation_status": "规则推算待确认",
            "attention_level": "高",
            "days_until": 2,
        }]
    }
    result = engine.tick(_payload({
        "auto_buy_eligible": True,
        "stale": False,
        "scoreable_count": 3,
        "quality_coverage": 0.9,
        "future_event_calendar": calendar,
    }, calendar))

    assert result["signal"]["action"] in {"buy", "add"}
    assert result["signal"]["event_watch_context"]["block_new_position"] is False
    assert "rule_inferred_calendar_watch_only" in result["signal"]["event_watch_context"]["evidence"]


def test_confirmed_high_attention_event_requires_manual_observation():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["600438"], "initial_cash": 100_000})
    calendar = {
        "events": [{
            "title": "半年度报告披露",
            "confirmation_status": "公开来源已确认",
            "attention_level": "高",
            "days_until": 2,
        }]
    }
    result = engine.tick(_payload({
        "auto_buy_eligible": True,
        "stale": False,
        "scoreable_count": 3,
        "quality_coverage": 0.9,
        "future_event_calendar": calendar,
    }, calendar))

    assert result["signal"]["action"] == "hold"
    assert result["orders"] == []
    assert result["signal"]["requires_manual_confirm"] is True
    assert "半年度报告披露" in result["signal"]["event_watch_context"]["block_reason"]


def test_unready_information_score_is_audit_only_and_not_fused():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["600438"], "initial_cash": 100_000})
    payload = _payload({
        "auto_buy_eligible": False,
        "stale": False,
        "scoreable_count": 0,
        "quality_status": "unusable",
    })
    payload["dimension_readiness"] = {
        "auto_entry_eligible": False,
        "entry_block_reasons": ["信息面未就绪：证据质量不足"],
        "dimensions": [
            {"key": "technical", "ready": True, "quality_status": "available"},
            {"key": "information", "ready": False, "quality_status": "unusable", "reason": "证据质量不足"},
            {"key": "fund_flow", "ready": True, "quality_status": "proxy_available"},
        ],
        "market_context": {"ready": True, "quality_status": "available"},
    }

    result = engine.tick(payload)
    signal = result["signal"]
    breakdown = signal["score_breakdown"]

    assert signal["information_score"] is None
    assert breakdown["raw_dimension_scores"]["information"] == 75
    assert "information" not in {row["key"] for row in breakdown["contributions"]}
    assert breakdown["excluded_by_readiness"][0]["key"] == "information"


def test_untraceable_fundamental_score_is_audit_only_and_not_fused():
    engine = RealtimePaperEngine()
    engine.start({"symbols": ["600438"], "initial_cash": 100_000})
    payload = _payload({
        "auto_buy_eligible": True,
        "stale": False,
        "scoreable_count": 3,
        "quality_coverage": 0.9,
    })
    payload["fundamental_score"] = 92.0
    payload["dimension_readiness"] = {
        "auto_entry_eligible": True,
        "entry_block_reasons": [],
        "dimensions": [
            {"key": "fundamental", "ready": False, "quality_status": "missing", "reason": "基本面来源缺失"},
            {"key": "technical", "ready": True, "quality_status": "available"},
            {"key": "information", "ready": True, "quality_status": "available"},
            {"key": "fund_flow", "ready": True, "quality_status": "proxy_available"},
        ],
        "market_context": {"ready": True, "quality_status": "available"},
    }

    result = engine.tick(payload)
    breakdown = result["signal"]["score_breakdown"]

    assert breakdown["raw_dimension_scores"]["fundamental"] == 92.0
    assert breakdown["execution_dimension_scores"]["fundamental"] is None
    assert all(row["key"] != "fundamental" for row in breakdown["contributions"])
