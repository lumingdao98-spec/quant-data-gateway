from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.chart.trading_marker_engine import TradingMarkerEngine
from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.paper_account import PaperAccount
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine

from .realtime_session import RealtimeSession


class RealtimePaperEngineV323:
    """Persistent session wrapper around the tested realtime paper engine."""

    def __init__(self, engine: RealtimePaperEngine | None = None, store: TradingStore | None = None) -> None:
        self._template_engine = engine or RealtimePaperEngine()
        self.engine = self._template_engine
        self.engines: dict[str, RealtimePaperEngine] = {}
        self.store = store or TradingStore()
        self.marker_engine = TradingMarkerEngine()
        self.sessions: dict[str, RealtimeSession] = {}
        self.active_session_id = ""
        self._restore_sessions()

    def start_session(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if self.active_session_id and not bool(payload.get("parallel_session")):
            previous = self.sessions.get(self.active_session_id)
            if previous and previous.status in {"running", "paused"}:
                previous.status = "stopped"
                previous.paused = False
                previous_engine = self.engines.get(previous.session_id)
                if previous_engine:
                    previous_engine.stop()
                    self.sync_engine_state(previous.session_id)
                self._persist_session(previous)
                self.store.put(
                    "audit_events",
                    {"event_type": "realtime_session_superseded", "created_at": _now()},
                    mode="realtime_paper",
                    session_id=previous.session_id,
                )
        session = RealtimeSession(
            symbols=_symbols(payload.get("symbols") or payload.get("watchlist")),
            strategy_family=str(payload.get("strategy_family") or payload.get("strategy") or "hybrid"),
            interval_seconds=max(5, min(60, int(payload.get("interval_seconds") or 15))),
            status="running",
            config=_session_config(payload),
        )
        self.sessions[session.session_id] = session
        self.active_session_id = session.session_id
        current_engine = self._new_engine()
        self.engines[session.session_id] = current_engine
        self.engine = current_engine
        base = current_engine.start({**payload, "symbols": session.symbols, "interval_seconds": session.interval_seconds})
        self._persist_session(session)
        self.store.put(
            "audit_events",
            {
                "event_type": "realtime_session_start",
                "session_ref": {
                    "session_id": session.session_id,
                    "symbols": session.symbols,
                    "strategy_family": session.strategy_family,
                    "interval_seconds": session.interval_seconds,
                    "started_at": session.started_at,
                },
                "engine_ref": {
                    "status": (base.get("state") or {}).get("status"),
                    "paper_only": base.get("paper_only", True),
                    "initial_cash": (base.get("portfolio") or {}).get("initial_cash"),
                },
                "config_hash": _stable_id("session-config", session.config),
            },
            mode="realtime_paper",
            session_id=session.session_id,
        )
        self.sync_engine_state(session.session_id)
        return {"ok": True, "session": session.to_dict(), "engine": base}

    def update_active_session(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Reconfigure the active paper session without replacing its account or history."""

        payload = payload or {}
        session_id = str(payload.get("session_id") or self.active_session_id)
        session = self.sessions.get(session_id)
        if not session or session.status not in {"running", "paused"}:
            return {"ok": False, "message": "没有可恢复的实时模拟会话", "session": None}
        if session.kill_switch:
            return {"ok": False, "message": "会话 kill switch 已开启，请先解除后再恢复", "session": session.to_dict()}

        engine = self._engine_for(session_id, restore=True)
        if engine is None:
            return {"ok": False, "message": "实时模拟账户恢复失败", "session": session.to_dict()}

        self.sync_engine_state(session_id)
        started_at = session.started_at
        symbols = _symbols(payload.get("symbols") or payload.get("watchlist")) or list(session.symbols)
        interval_seconds = max(5, min(60, int(payload.get("interval_seconds") or session.interval_seconds or 15)))
        strategy_family = str(
            payload.get("strategy_family")
            or payload.get("strategy")
            or session.strategy_family
            or "hybrid"
        )
        previous_initial_cash = float(engine.account.initial_cash)
        requested_initial_cash = float(payload.get("initial_cash") or previous_initial_cash)
        session.symbols = symbols
        session.interval_seconds = interval_seconds
        session.strategy_family = strategy_family
        session.status = "running"
        session.paused = False
        session.config = {
            **(session.config or {}),
            **_session_config(payload),
            "initial_cash": previous_initial_cash,
            "reset_account": False,
        }

        base = engine.start(
            {
                **payload,
                **session.config,
                "symbols": symbols,
                "strategy": strategy_family,
                "strategy_family": strategy_family,
                "interval_seconds": interval_seconds,
                "initial_cash": previous_initial_cash,
                "reset_account": False,
            }
        )
        engine.state.started_at = started_at
        self.engine = engine
        self.active_session_id = session_id
        self._persist_session(session)
        self.store.put(
            "audit_events",
            {
                "event_type": "realtime_session_reconfigured",
                "account_preserved": True,
                "requested_initial_cash": requested_initial_cash,
                "effective_initial_cash": previous_initial_cash,
                "symbols": symbols,
                "strategy_family": strategy_family,
                "created_at": _now(),
            },
            mode="realtime_paper",
            session_id=session_id,
        )
        self.sync_engine_state(session_id)
        warning = ""
        if abs(requested_initial_cash - previous_initial_cash) > 0.000001:
            warning = "为保留现有持仓和成交，初始资金变更未生效；勾选强制新建账户后才会重置资金。"
        return {
            "ok": True,
            "session": session.to_dict(),
            "engine": base,
            "reused_session": True,
            "account_preserved": True,
            "warning": warning,
        }

    def pause(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"ok": False, "message": "session not found"}
        session.paused = True
        session.status = "paused"
        engine = self.engines.get(session_id)
        if engine:
            engine.state.status = "paused"
            engine.state.message = "实时模拟已暂停"
        self._persist_session(session)
        self.store.put("audit_events", {"event_type": "realtime_session_pause"}, mode="realtime_paper", session_id=session_id)
        return {"ok": True, "session": session.to_dict()}

    def resume(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"ok": False, "message": "session not found"}
        session.paused = False
        session.status = "running"
        self.active_session_id = session_id
        engine = self._engine_for(session_id, restore=True)
        if engine:
            engine.state.status = "running"
            engine.state.message = "实时模拟运行中"
            self.engine = engine
        self._persist_session(session)
        self.store.put("audit_events", {"event_type": "realtime_session_resume"}, mode="realtime_paper", session_id=session_id)
        return {"ok": True, "session": session.to_dict()}

    def stop_session(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if session:
            session.status = "stopped"
            session.paused = False
            self._persist_session(session)
        engine = self._engine_for(session_id, restore=False)
        base = engine.stop() if engine else self._stored_status(session_id)
        self.sync_engine_state(session_id)
        return {"ok": True, "session": session.to_dict() if session else None, "engine": base}

    def stop_active_session(self) -> dict[str, Any]:
        return self.stop_session(self.active_session_id) if self.active_session_id else {"ok": True, "engine": self.engine.stop(), "session": None}

    def kill_switch(self, session_id: str, enabled: bool = True) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"ok": False, "message": "session not found"}
        session.kill_switch = bool(enabled)
        session.status = "killed" if enabled else "running"
        session.paused = bool(enabled)
        self._persist_session(session)
        self.store.put("audit_events", {"event_type": "realtime_session_kill_switch", "enabled": enabled}, mode="realtime_paper", session_id=session_id)
        return {"ok": True, "session": session.to_dict()}

    def tick(self, payload: dict[str, Any] | None = None, *, manual_replay: bool = False, session_id: str = "") -> dict[str, Any]:
        payload = payload or {}
        sid = session_id or str(payload.get("session_id") or self.active_session_id)
        session = self.sessions.get(sid)
        if session and session.kill_switch:
            return {"ok": False, "message": "session kill switch enabled", "session": session.to_dict()}
        if session and session.paused and not manual_replay:
            return {"ok": False, "message": "session paused", "session": session.to_dict()}
        if session:
            payload = _merge_session_signal(payload, session)
        engine = self._engine_for(sid, restore=True)
        if engine is None:
            return {"ok": False, "message": "session not found", "session_id": sid}
        self.engine = engine
        result = engine.tick(payload, manual_replay=manual_replay)
        self.sync_engine_state(sid)
        if session:
            result["v323_session"] = session.to_dict()
            result["session_id"] = sid
        return result

    def observe_market_closed(
        self,
        payload: dict[str, Any] | None = None,
        *,
        session_id: str = "",
        market_session: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a read-only closed-market snapshot without creating trading records."""
        payload = payload or {}
        sid = session_id or str(payload.get("session_id") or self.active_session_id)
        session = self.sessions.get(sid)
        engine = self._engine_for(sid, restore=True)
        if engine is None:
            return {"ok": False, "message": "session not found", "session_id": sid}
        self.engine = engine
        engine.state.is_trading_session = False
        engine.state.message = "休市待机：不生成信号、委托或成交"
        result: dict[str, Any] = {
            "ok": True,
            "skipped": True,
            "reason": "market_closed",
            "message": "当前为非交易时段，实时模拟已待机；未生成信号、委托或成交。历史回放请使用 /api/realtime-paper/replay。",
            "state": engine.state.to_dict(),
            "signal": None,
            "orders": [],
            "fills": [],
            "portfolio": engine.account.snapshot(),
            "market_session": dict(market_session or {}),
            "paper_only": True,
            "records_written": False,
        }
        if session:
            result["v323_session"] = session.to_dict()
            result["session_id"] = sid
        return result

    def replay(self, payload: dict[str, Any] | None = None, *, session_id: str = "") -> dict[str, Any]:
        sid = session_id or str((payload or {}).get("session_id") or self.active_session_id)
        engine = self._engine_for(sid, restore=True)
        if engine is None:
            return {"ok": False, "message": "session not found", "session_id": sid}
        self.engine = engine
        result = engine.replay(payload)
        self.sync_engine_state(sid)
        result["session_id"] = sid
        return result

    def list_sessions(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in sorted(self.sessions.values(), key=lambda item: item.started_at, reverse=True)]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = self.sessions.get(session_id)
        return session.to_dict() if session else None

    def active_session(self) -> dict[str, Any] | None:
        return self.get_session(self.active_session_id) if self.active_session_id else None

    def status(self, session_id: str = "") -> dict[str, Any]:
        sid = session_id or self.active_session_id
        engine = self._engine_for(sid, restore=True) if sid else None
        data = engine.status() if engine else self._stored_status(sid)
        data["v323_session"] = self.get_session(sid) if sid else None
        data["session_id"] = sid
        return data

    def portfolio(self, session_id: str = "") -> dict[str, Any]:
        sid = session_id or self.active_session_id
        engine = self._engine_for(sid, restore=True) if sid else None
        if engine:
            return {**engine.portfolio(), "session_id": sid}
        snapshots = self.store.list("account_snapshots", mode="realtime_paper", session_id=sid, limit=1) if sid else []
        return {"ok": True, "data": snapshots[0] if snapshots else PaperAccount().snapshot(), "curve": [], "session_id": sid}

    def confirmations(self, session_id: str = ""):
        engine = self._engine_for(session_id or self.active_session_id, restore=True)
        return engine.human_confirm_queue if engine else self._template_engine.human_confirm_queue

    def sync_engine_state(self, session_id: str = "") -> dict[str, Any]:
        sid = session_id or self.active_session_id
        counts = {"signals": 0, "orders": 0, "fills": 0, "positions": 0, "markers": 0, "audit_events": 0}
        if not sid:
            return counts
        engine = self.engines.get(sid)
        if engine is None:
            return counts

        for row in engine.signal_rows(limit=1000).get("data") or []:
            item = dict(row)
            item.setdefault("mode", "realtime_paper")
            item.setdefault("session_id", sid)
            item.setdefault("created_at", item.get("timestamp") or item.get("decision_time") or _now())
            record_id = str(item.get("signal_id") or _stable_id("signal", sid, item))
            self.store.put("signals", item, mode="realtime_paper", symbol=str(item.get("symbol") or ""), session_id=sid, record_id=record_id)
            counts["signals"] += 1

        for row in engine.orders(limit=1000).get("data") or []:
            item = dict(row)
            item.setdefault("mode", "realtime_paper")
            item.setdefault("session_id", sid)
            item.setdefault("created_at", item.get("created_at") or item.get("timestamp") or _now())
            record_id = str(item.get("order_id") or _stable_id("order", sid, item))
            item.setdefault("order_id", record_id)
            self.store.put("orders", item, mode="realtime_paper", symbol=str(item.get("symbol") or ""), session_id=sid, record_id=record_id)
            marker = self.marker_engine.from_order(item).to_dict()
            self.store.put("chart_markers", marker, mode="realtime_paper", symbol=marker.get("symbol", ""), session_id=sid, record_id=marker["marker_id"])
            counts["orders"] += 1
            counts["markers"] += 1

        fills = list(engine.account.fills_dicts() or [])
        for row in fills:
            item = dict(row)
            item.setdefault("mode", "realtime_paper")
            item.setdefault("session_id", sid)
            item.setdefault("filled_at", item.get("created_at") or item.get("timestamp") or _now())
            fill_id = str(item.get("fill_id") or _stable_id("fill", sid, item))
            item["fill_id"] = fill_id
            self.store.put("fills", item, mode="realtime_paper", symbol=str(item.get("symbol") or ""), session_id=sid, record_id=fill_id)
            marker = self.marker_engine.from_fill(item, mode="realtime_paper", session_id=sid).to_dict()
            self.store.put("chart_markers", marker, mode="realtime_paper", symbol=marker.get("symbol", ""), session_id=sid, record_id=marker["marker_id"])
            counts["fills"] += 1
            counts["markers"] += 1

        portfolio = engine.account.snapshot()
        portfolio.setdefault("session_id", sid)
        self.store.put("account_snapshots", portfolio, mode="realtime_paper", session_id=sid, record_id=_stable_id("account", sid, portfolio.get("cash"), len(fills)))
        self.store.delete("positions", mode="realtime_paper", session_id=sid)
        for symbol, pos in (portfolio.get("positions") or {}).items():
            item = dict(pos)
            item.setdefault("symbol", symbol)
            item.setdefault("session_id", sid)
            self.store.put("positions", item, mode="realtime_paper", symbol=str(symbol), session_id=sid, record_id=_stable_id("position", sid, symbol))
            counts["positions"] += 1

        for row in engine.audit(limit=1000).get("data") or []:
            item = dict(row)
            item.setdefault("mode", "realtime_paper")
            item.setdefault("session_id", sid)
            item.setdefault("created_at", item.get("timestamp") or _now())
            self.store.put("audit_events", item, mode="realtime_paper", symbol=str(item.get("symbol") or ""), session_id=sid, record_id=_stable_id("audit", sid, item))
            counts["audit_events"] += 1
        return counts

    def stored_orders(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("orders", mode="realtime_paper", session_id=session_id, limit=limit)

    def stored_signals(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("signals", mode="realtime_paper", session_id=session_id, limit=limit)

    def stored_fills(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("fills", mode="realtime_paper", session_id=session_id, limit=limit)

    def stored_positions(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        snapshots = self.store.list("account_snapshots", mode="realtime_paper", session_id=session_id, limit=1)
        snapshot = snapshots[0] if snapshots else {}
        canonical = []
        for symbol, raw in (snapshot.get("positions") or {}).items():
            item = dict(raw or {})
            item.setdefault("symbol", symbol)
            canonical.append(item)
        return [{"snapshot": snapshot, "positions": canonical[: max(1, int(limit or 200))]}]

    def stored_markers(self, session_id: str, symbol: str = "", limit: int = 300) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("chart_markers", mode="realtime_paper", symbol=symbol, session_id=session_id, limit=limit)

    def stored_audit(self, session_id: str, limit: int = 300) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("audit_events", mode="realtime_paper", session_id=session_id, limit=limit)

    def _restore_sessions(self) -> None:
        rows = self.store.list("paper_sessions", mode="realtime_paper", limit=500)
        names = {item.name for item in fields(RealtimeSession)}
        for row in rows:
            data = {key: row.get(key) for key in names if key in row}
            if not data.get("session_id"):
                continue
            data["symbols"] = _symbols(data.get("symbols"))
            data["interval_seconds"] = int(data.get("interval_seconds") or 15)
            data["paused"] = bool(data.get("paused"))
            data["kill_switch"] = bool(data.get("kill_switch"))
            data["config"] = data.get("config") if isinstance(data.get("config"), dict) else {}
            session = RealtimeSession(**data)
            self.sessions[session.session_id] = session
        candidates = sorted(
            (item for item in self.sessions.values() if item.status in {"running", "paused"}),
            key=lambda item: item.started_at,
            reverse=True,
        )
        if candidates:
            active = candidates[0]
            self.active_session_id = active.session_id
            for orphan in candidates[1:]:
                orphan.status = "stopped"
                orphan.paused = False
                self._persist_session(orphan)
            restored = self._engine_for(active.session_id, restore=True)
            if restored:
                self.engine = restored

    def _new_engine(self, account: PaperAccount | None = None) -> RealtimePaperEngine:
        return RealtimePaperEngine(
            account=account,
            risk_gateway=self._template_engine.risk_gateway,
            signal_fusion=self._template_engine.signal_fusion,
            anomaly_guard=self._template_engine.anomaly_guard,
            freshness_guard=self._template_engine.freshness_guard,
        )

    def _engine_for(self, session_id: str, *, restore: bool) -> RealtimePaperEngine | None:
        if not session_id or session_id not in self.sessions:
            return None
        existing = self.engines.get(session_id)
        if existing or not restore:
            return existing
        session = self.sessions[session_id]
        snapshots = self.store.list("account_snapshots", mode="realtime_paper", session_id=session_id, limit=1)
        fills = self.store.list("fills", mode="realtime_paper", session_id=session_id, limit=5000)
        account = PaperAccount.from_snapshot(
            snapshots[0] if snapshots else {"initial_cash": (session.config or {}).get("initial_cash", 100_000)},
            fills=list(reversed(fills)),
        )
        engine = self._new_engine(account)
        engine.start(
            {
                **(session.config or {}),
                "symbols": session.symbols,
                "strategy": session.strategy_family,
                "interval_seconds": session.interval_seconds,
                "initial_cash": account.initial_cash,
                "reset_account": False,
            }
        )
        engine.state.started_at = session.started_at
        if session.status != "running":
            engine.state.status = session.status
            engine.state.message = "实时模拟已暂停" if session.status == "paused" else "已停止"
        self.engines[session_id] = engine
        return engine

    def _stored_status(self, session_id: str) -> dict[str, Any]:
        snapshots = self.store.list("account_snapshots", mode="realtime_paper", session_id=session_id, limit=1) if session_id else []
        session = self.sessions.get(session_id)
        state = {
            "status": session.status if session else "stopped",
            "started_at": session.started_at if session else None,
            "config": session.config if session else {},
        }
        return {
            "ok": True,
            "state": state,
            "paper_only": True,
            "real_broker_connected": False,
            "portfolio": snapshots[0] if snapshots else PaperAccount().snapshot(),
            "order_count": len(self.store.list("orders", mode="realtime_paper", session_id=session_id, limit=1000)) if session_id else 0,
            "signal_count": len(self.store.list("signals", mode="realtime_paper", session_id=session_id, limit=1000)) if session_id else 0,
            "human_confirm_pending": 0,
        }

    def _persist_session(self, session: RealtimeSession) -> None:
        self.store.put("paper_sessions", session.to_dict(), mode="realtime_paper", session_id=session.session_id, record_id=session.session_id)


def _session_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep the V3.23 auto-trading config with the paper session for restore/tick."""

    keys = {
        "strategy_combo",
        "strategy_parameters",
        "position_sizing",
        "risk_controls",
        "score_weights",
        "event_watch",
        "data_requirements",
        "decision_policy",
        "parameter_schema",
        "strategy_matrix",
        "strategy_blueprints",
        "integrated_score_dimensions",
        "key_event_watchlist",
        "screener_signal_map",
        "screener_signal_count",
        "screener_snapshot_id",
        "symbols_source",
        "source_page",
        "initial_cash",
        "reset_account",
    }
    return {key: payload.get(key) for key in keys if key in payload}


def _merge_session_signal(payload: dict[str, Any], session: RealtimeSession) -> dict[str, Any]:
    """Inject screener-derived scores into a realtime tick without fabricating data."""

    config = session.config or {}
    merged = {**config, **(payload or {})}
    symbol = str(merged.get("symbol") or (session.symbols[0] if session.symbols else "")).strip()
    signal_map = config.get("screener_signal_map") if isinstance(config.get("screener_signal_map"), dict) else {}
    profile = dict(signal_map.get(symbol) or {}) if symbol else {}
    if not profile:
        return merged

    merged.setdefault("symbol", symbol)
    merged.setdefault("name", profile.get("name") or symbol)
    score_fields = {
        "technical_score": "technical_score",
        "fundamental_score": "fundamental_score",
        "information_score": "information_score",
        "market_score": "market_score",
        "fund_flow_score": "fund_flow_score",
        "final_score": "final_score",
    }
    for payload_key, profile_key in score_fields.items():
        if merged.get(payload_key) in {None, "", "--"}:
            merged[payload_key] = profile.get(profile_key)

    # The screening snapshot is the stable baseline, the daily K score is the
    # medium-term structure, and the intraday score only times the current
    # session. An intraday fluctuation must not overwrite the other two.
    screening_score = _score_number(profile.get("final_score"))
    daily_k_score = _score_number(merged.get("daily_k_score"))
    if daily_k_score is None:
        daily_k_score = _score_number(profile.get("technical_score"))
    intraday_score = _score_number(merged.get("intraday_score"))
    score_source = str(merged.get("score_source") or "").lower()
    if intraday_score is None and ("quote" in score_source or "intraday" in score_source):
        intraday_score = _score_number((payload or {}).get("technical_score"))
    usable_technical = [
        (value, weight)
        for value, weight in ((daily_k_score, 0.55), (intraday_score, 0.45))
        if value is not None
    ]
    if usable_technical:
        weight_sum = sum(weight for _, weight in usable_technical) or 1.0
        merged["technical_score"] = round(
            sum(float(value) * weight for value, weight in usable_technical) / weight_sum,
            4,
        )
    merged["screening_score"] = screening_score
    merged["daily_k_score"] = daily_k_score
    merged["intraday_score"] = intraday_score

    live_fund_flow = _score_number((payload or {}).get("fund_flow_score"))
    baseline_fund_flow = _score_number(profile.get("fund_flow_score"))
    if "server_cache_realtime_decision" in score_source:
        merged["fund_flow_score"] = live_fund_flow if live_fund_flow is not None else baseline_fund_flow
    elif live_fund_flow is not None and baseline_fund_flow is not None:
        merged["fund_flow_score"] = round(baseline_fund_flow * 0.45 + live_fund_flow * 0.55, 4)
    existing_breakdown = dict(merged.get("score_breakdown") or {})
    existing_sources = dict(existing_breakdown.get("sources") or {})
    existing_sources.update({
        "screening": profile.get("source") or "auto_trading_screener_snapshot",
        "daily_k": existing_sources.get("daily_k") or "screener_technical_snapshot",
        "intraday": existing_sources.get("intraday") or str(merged.get("score_source") or "realtime_quote_snapshot"),
    })
    existing_breakdown.update({
        "screening_score": screening_score,
        "daily_k_score": daily_k_score,
        "intraday_score": intraday_score,
        "timing_score": merged.get("technical_score"),
        "technical_score": merged.get("technical_score"),
        "fund_flow_score": merged.get("fund_flow_score"),
        "formula": existing_breakdown.get("formula") or "综合交易分=筛选底座+实时择时（日K55%+分时45%）+近期信息+资金+大盘-异常风险",
        "sources": existing_sources,
        "screener_snapshot_id": config.get("screener_snapshot_id"),
    })
    merged["score_breakdown"] = existing_breakdown

    evidence = [f"来自自动交易筛选信号画像：{profile.get('action') or 'watch'}"] + list(profile.get("evidence") or [])
    evidence += list(merged.get("evidence") or [])
    evidence.append(
        f"三路评分：筛选 {screening_score if screening_score is not None else '--'} / "
        f"日K {daily_k_score if daily_k_score is not None else '--'} / "
        f"分时 {intraday_score if intraday_score is not None else '--'}"
    )
    merged["evidence"] = list(dict.fromkeys(evidence))
    merged.setdefault("missing_data", list(profile.get("missing_data") or []))
    merged["screener_signal"] = profile

    action = str(profile.get("action") or "").lower()
    if action == "avoid":
        merged.setdefault("info_negative_veto", True)
    elif action in {"reduce", "sell"}:
        merged.setdefault("technical_broken", True)

    risk_flags = [str(x) for x in profile.get("risk_flags") or []]
    if risk_flags:
        merged.setdefault("risk_flags", risk_flags)
        anomaly = merged.get("anomaly_features")
        if not isinstance(anomaly, dict):
            anomaly = {}
            merged["anomaly_features"] = anomaly
        joined = " ".join(risk_flags)
        if "过期" in joined or "stale" in joined.lower() or "缺失" in joined:
            anomaly.setdefault("stale_data", True)
    return merged


def _score_number(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        return round(max(0.0, min(100.0, float(value))), 4)
    except (TypeError, ValueError):
        return None


def _symbols(value: Any) -> list[str]:
    if isinstance(value, str):
        if any(sep in value for sep in ["，", "；", "、", "|", ";", "\n", "\t", " "]):
            text = value
            for sep in ["，", "；", "、", "|", ";", "\n", "\t", " "]:
                text = text.replace(sep, ",")
            return [x.strip() for x in text.split(",") if x.strip()]
        text = value.replace("，", ",").replace("；", ",").replace(";", ",").replace("\n", ",")
        return [x.strip() for x in text.split(",") if x.strip()]
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stable_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]
