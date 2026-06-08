from __future__ import annotations

from typing import Any

from quant_data.persistence.trading_store import TradingStore
from quant_data.trading.realtime_paper_engine import RealtimePaperEngine

from .realtime_session import RealtimeSession


class RealtimePaperEngineV323:
    """Session-oriented wrapper around the existing paper engine."""

    def __init__(self, engine: RealtimePaperEngine | None = None, store: TradingStore | None = None) -> None:
        self.engine = engine or RealtimePaperEngine()
        self.store = store or TradingStore()
        self.sessions: dict[str, RealtimeSession] = {}

    def start_session(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        session = RealtimeSession(
            symbols=_symbols(payload.get("symbols") or payload.get("watchlist")),
            strategy_family=str(payload.get("strategy_family") or payload.get("strategy") or "hybrid"),
            interval_seconds=max(5, min(60, int(payload.get("interval_seconds") or 15))),
            status="running",
        )
        self.sessions[session.session_id] = session
        base = self.engine.start({**payload, "symbols": session.symbols, "interval_seconds": session.interval_seconds})
        self.store.put("audit_events", {"event_type": "realtime_session_start", "session": session.to_dict(), "engine": base}, mode="realtime_paper", session_id=session.session_id)
        return {"ok": True, "session": session.to_dict(), "engine": base}

    def pause(self, session_id: str) -> dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            return {"ok": False, "message": "session not found"}
        s.paused = True
        s.status = "paused"
        return {"ok": True, "session": s.to_dict()}

    def resume(self, session_id: str) -> dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            return {"ok": False, "message": "session not found"}
        s.paused = False
        s.status = "running"
        return {"ok": True, "session": s.to_dict()}

    def stop_session(self, session_id: str) -> dict[str, Any]:
        s = self.sessions.get(session_id)
        if s:
            s.status = "stopped"
        base = self.engine.stop()
        return {"ok": True, "session": s.to_dict() if s else None, "engine": base}

    def kill_switch(self, session_id: str, enabled: bool = True) -> dict[str, Any]:
        s = self.sessions.get(session_id)
        if not s:
            return {"ok": False, "message": "session not found"}
        s.kill_switch = bool(enabled)
        if enabled:
            s.status = "killed"
        return {"ok": True, "session": s.to_dict()}

    def list_sessions(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.sessions.values()]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        s = self.sessions.get(session_id)
        return s.to_dict() if s else None


def _symbols(value: Any) -> list[str]:
    if isinstance(value, str):
        return [x.strip() for x in value.replace("，", ",").split(",") if x.strip()]
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []
