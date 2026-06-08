from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from quant_data.chart.trading_marker_engine import TradingMarkerEngine
from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine

from .realtime_session import RealtimeSession


class RealtimePaperEngineV323:
    """Persistent session wrapper around the tested realtime paper engine."""

    def __init__(self, engine: RealtimePaperEngine | None = None, store: TradingStore | None = None) -> None:
        self.engine = engine or RealtimePaperEngine()
        self.store = store or TradingStore()
        self.marker_engine = TradingMarkerEngine()
        self.sessions: dict[str, RealtimeSession] = {}
        self.active_session_id = ""
        self._restore_sessions()

    def start_session(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        session = RealtimeSession(
            symbols=_symbols(payload.get("symbols") or payload.get("watchlist")),
            strategy_family=str(payload.get("strategy_family") or payload.get("strategy") or "hybrid"),
            interval_seconds=max(5, min(60, int(payload.get("interval_seconds") or 15))),
            status="running",
        )
        self.sessions[session.session_id] = session
        self.active_session_id = session.session_id
        base = self.engine.start({**payload, "symbols": session.symbols, "interval_seconds": session.interval_seconds})
        self._persist_session(session)
        self.store.put(
            "audit_events",
            {"event_type": "realtime_session_start", "session": session.to_dict(), "engine": base},
            mode="realtime_paper",
            session_id=session.session_id,
        )
        self.sync_engine_state(session.session_id)
        return {"ok": True, "session": session.to_dict(), "engine": base}

    def pause(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"ok": False, "message": "session not found"}
        session.paused = True
        session.status = "paused"
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
        self._persist_session(session)
        self.store.put("audit_events", {"event_type": "realtime_session_resume"}, mode="realtime_paper", session_id=session_id)
        return {"ok": True, "session": session.to_dict()}

    def stop_session(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if session:
            session.status = "stopped"
            session.paused = False
            self._persist_session(session)
        base = self.engine.stop()
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
        result = self.engine.tick(payload, manual_replay=manual_replay)
        self.sync_engine_state(sid)
        if session:
            result["v323_session"] = session.to_dict()
            result["session_id"] = sid
        return result

    def replay(self, payload: dict[str, Any] | None = None, *, session_id: str = "") -> dict[str, Any]:
        sid = session_id or str((payload or {}).get("session_id") or self.active_session_id)
        result = self.engine.replay(payload)
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

    def sync_engine_state(self, session_id: str = "") -> dict[str, Any]:
        sid = session_id or self.active_session_id
        counts = {"signals": 0, "orders": 0, "fills": 0, "positions": 0, "markers": 0, "audit_events": 0}
        if not sid:
            return counts

        for row in self.engine.signal_rows(limit=1000).get("data") or []:
            item = dict(row)
            item.setdefault("mode", "realtime_paper")
            item.setdefault("session_id", sid)
            item.setdefault("created_at", item.get("timestamp") or item.get("decision_time") or _now())
            record_id = str(item.get("signal_id") or _stable_id("signal", sid, item))
            self.store.put("signals", item, mode="realtime_paper", symbol=str(item.get("symbol") or ""), session_id=sid, record_id=record_id)
            counts["signals"] += 1

        for row in self.engine.orders(limit=1000).get("data") or []:
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

        fills = list(self.engine.account.fills_dicts() or [])
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

        portfolio = self.engine.account.snapshot()
        portfolio.setdefault("session_id", sid)
        self.store.put("account_snapshots", portfolio, mode="realtime_paper", session_id=sid, record_id=_stable_id("account", sid, portfolio.get("cash"), len(fills)))
        for symbol, pos in (portfolio.get("positions") or {}).items():
            item = dict(pos)
            item.setdefault("symbol", symbol)
            item.setdefault("session_id", sid)
            self.store.put("positions", item, mode="realtime_paper", symbol=str(symbol), session_id=sid, record_id=_stable_id("position", sid, symbol, item))
            counts["positions"] += 1

        for row in self.engine.audit(limit=1000).get("data") or []:
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

    def stored_fills(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        return self.store.list("fills", mode="realtime_paper", session_id=session_id, limit=limit)

    def stored_positions(self, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
        self.sync_engine_state(session_id)
        positions = self.store.list("positions", mode="realtime_paper", session_id=session_id, limit=limit)
        snapshots = self.store.list("account_snapshots", mode="realtime_paper", session_id=session_id, limit=1)
        return [{"snapshot": snapshots[0] if snapshots else {}, "positions": positions}]

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
            session = RealtimeSession(**data)
            self.sessions[session.session_id] = session
            if not self.active_session_id and session.status in {"running", "paused"}:
                self.active_session_id = session.session_id

    def _persist_session(self, session: RealtimeSession) -> None:
        self.store.put("paper_sessions", session.to_dict(), mode="realtime_paper", session_id=session.session_id, record_id=session.session_id)


def _symbols(value: Any) -> list[str]:
    if isinstance(value, str):
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
