from __future__ import annotations

from datetime import datetime, time
from typing import Any

from .anomaly_guard import AnomalyGuard
from .audit_log import AuditLog
from .data_freshness import DataFreshnessGuard
from .human_confirm_queue import HumanConfirmQueue
from .order_manager import OrderManager
from .paper_account import PaperAccount
from .realtime_state import RealtimePaperConfig, RealtimePaperState
from .risk_gateway import RiskGateway
from .signal_fusion import SignalFusionEngine, UnifiedSignal


class RealtimePaperEngine:
    def __init__(
        self,
        *,
        account: PaperAccount | None = None,
        audit_log: AuditLog | None = None,
        risk_gateway: RiskGateway | None = None,
        signal_fusion: SignalFusionEngine | None = None,
        anomaly_guard: AnomalyGuard | None = None,
        freshness_guard: DataFreshnessGuard | None = None,
        human_confirm_queue: HumanConfirmQueue | None = None,
    ) -> None:
        self.account = account or PaperAccount()
        self.audit_log = audit_log or AuditLog()
        self.order_manager = OrderManager(self.account, self.audit_log)
        self.risk_gateway = risk_gateway or RiskGateway()
        self.signal_fusion = signal_fusion or SignalFusionEngine()
        self.anomaly_guard = anomaly_guard or AnomalyGuard()
        self.freshness_guard = freshness_guard or DataFreshnessGuard()
        self.human_confirm_queue = human_confirm_queue or HumanConfirmQueue()
        self.state = RealtimePaperState()
        self.signals: list[UnifiedSignal] = []
        self.signal_meta: list[dict[str, Any]] = []
        self.tick_log: list[dict[str, Any]] = []
        self.portfolio_curve: list[dict[str, Any]] = []

    def start(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        initial_cash = float(payload.get("initial_cash") or self.account.initial_cash)
        if initial_cash != self.account.initial_cash and not self.account.positions:
            self.account = PaperAccount(initial_cash=initial_cash, account_mode=str(payload.get("horizon") or "hybrid"))
            self.order_manager = OrderManager(self.account, self.audit_log)
        config = RealtimePaperConfig(
            symbols=self._symbols(payload.get("symbols") or payload.get("watchlist")),
            interval_seconds=max(5, min(int(payload.get("interval_seconds") or 15), 60)),
            horizon=str(payload.get("horizon") or "intraday_paper"),
            initial_cash=initial_cash,
            strategy=str(payload.get("strategy") or "three_dimension_score"),
            fee_rate=float(payload.get("fee_rate") or 0.0003),
            slippage_rate=float(payload.get("slippage_rate") or 0.0005),
        )
        self.state.start(config)
        self.audit_log.record("realtime_paper_start", {"config": config.to_dict(), "paper_only": True})
        return self.status()

    def stop(self) -> dict[str, Any]:
        self.state.stop()
        self.audit_log.record("realtime_paper_stop", self.state.to_dict())
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "state": self.state.to_dict(),
            "paper_only": True,
            "real_broker_connected": False,
            "portfolio": self.account.snapshot(),
            "order_count": len(self.order_manager.orders),
            "signal_count": len(self.signals),
            "human_confirm_pending": len(self.human_confirm_queue.list(status="pending")),
        }

    def portfolio(self) -> dict[str, Any]:
        return {"ok": True, "data": self.account.snapshot(), "curve": list(self.portfolio_curve[-300:])}

    def orders(self, limit: int = 200) -> dict[str, Any]:
        return {"ok": True, "data": self.order_manager.list_orders(limit)}

    def signal_rows(self, limit: int = 200) -> dict[str, Any]:
        size = max(1, int(limit or 200))
        if self.signal_meta:
            return {"ok": True, "data": list(self.signal_meta[-size:])[::-1]}
        return {"ok": True, "data": [x.to_dict() for x in self.signals[-size:]][::-1]}

    def audit(self, limit: int = 300) -> dict[str, Any]:
        return {"ok": True, "data": self.audit_log.list(limit)}

    def tick(self, payload: dict[str, Any] | None = None, *, manual_replay: bool = False) -> dict[str, Any]:
        payload = payload or {}
        now = self._parse_time(payload.get("now") or payload.get("ts")) or datetime.now()
        symbol = str(payload.get("symbol") or (self.state.config.symbols[0] if self.state.config.symbols else "300750")).strip()
        quote = dict(payload.get("quote") or {})
        if not quote:
            quote = {k: payload.get(k) for k in ["last", "price", "amount", "volume", "change_pct", "turnover", "volume_ratio", "name"] if k in payload}
        price = self._num(quote.get("last") or quote.get("price") or payload.get("price") or payload.get("last"))
        quote["last"] = price
        quote["symbol"] = symbol
        quote.setdefault("ts", payload.get("quote_ts") or payload.get("ts") or now.isoformat(timespec="seconds"))
        if "intraday_ts" not in payload:
            payload["intraday_ts"] = payload.get("ts") or now.isoformat(timespec="seconds")
        is_trading = bool(payload.get("is_trading_session", self._is_trading_time(now)))
        self.state.is_trading_session = is_trading
        self.state.last_tick_at = now.isoformat(timespec="seconds")
        self.state.tick_count += 1
        if self.state.status != "running" and not manual_replay:
            self.audit_log.record("tick_ignored", {"symbol": symbol, "reason": "engine stopped"})
            return {"ok": False, "message": "engine stopped", "state": self.state.to_dict()}
        if not is_trading and not manual_replay:
            self.audit_log.record("tick_rejected", {"symbol": symbol, "reason": "非交易时段禁止自动下单"})
            return {"ok": True, "message": "非交易时段，仅记录不下单", "state": self.state.to_dict(), "orders": []}

        timestamps = {
            "quote": quote.get("ts"),
            "intraday": payload.get("intraday_ts"),
            "news": payload.get("news_ts") or now.isoformat(timespec="seconds"),
            "technical": payload.get("technical_ts") or now.isoformat(timespec="seconds"),
            "company_profile": payload.get("company_profile_ts") or now.isoformat(timespec="seconds"),
        }
        freshness = self.freshness_guard.check(timestamps, now=now)
        self.state.freshness_status = freshness.freshness_status
        anomaly_features = dict(payload.get("anomaly_features") or {})
        anomaly_features.setdefault("stale_data", freshness.action == "block")
        anomaly = self.anomaly_guard.check(anomaly_features)
        signal = self.signal_fusion.fuse(
            symbol=symbol,
            horizon=str(payload.get("horizon") or self.state.config.horizon),
            fundamental_score=self._optional(payload.get("fundamental_score")),
            technical_score=self._optional(payload.get("technical_score")),
            information_score=self._optional(payload.get("information_score")),
            market_score=self._optional(payload.get("market_score")),
            anomaly_score=anomaly.anomaly_score,
            anomaly_action=anomaly.action_suggestion,
            info_negative_veto=bool(payload.get("info_negative_veto")),
            technical_broken=bool(payload.get("technical_broken")),
            fundamental_poor=bool(payload.get("fundamental_poor")),
            evidence=list(payload.get("evidence") or anomaly.evidence or ["手动 tick 生成信号"]),
            data_freshness=freshness.to_dict(),
            missing_data=list(payload.get("missing_data") or []),
            now=now,
        )
        self.signals.append(signal)
        signal_row = signal.to_dict()
        signal_row.update(
            {
                "name": str(quote.get("name") or payload.get("name") or symbol),
                "quote_price": price,
                "session_mode": "盘中实时" if is_trading else ("休市回放" if manual_replay else "休市观察"),
                "paper_only": True,
            }
        )
        self.signal_meta.append(signal_row)
        self.tick_log.append({"timestamp": now.isoformat(timespec="seconds"), "symbol": symbol, "name": signal_row["name"], "price": price, "signal": signal_row, "anomaly": anomaly.to_dict(), "freshness": freshness.to_dict()})
        orders: list[dict[str, Any]] = []
        if signal.action in {"buy", "add", "sell", "reduce"} and price > 0:
            order = self.order_manager.build_order(
                symbol=symbol,
                target_weight=signal.target_weight,
                side=signal.action,
                price=price,
                order_type=str(payload.get("order_type") or "market"),
                reason=signal.reason,
            )
            risk = self.risk_gateway.evaluate_order(
                order.to_dict(),
                portfolio=self.account.snapshot(),
                signal=signal_row,
                quote=quote,
                anomaly=anomaly.to_dict(),
                freshness=freshness.to_dict(),
                now=now,
                manual_replay=manual_replay,
            )
            confirm_task = None
            if risk["approved"] and risk["decision"] == "allow":
                self.order_manager.simulate_fill(order, fill_price=price, fee_rate=self.state.config.fee_rate, slippage_rate=self.state.config.slippage_rate)
                self.audit_log.record("fill_arrived", {"order": order.to_dict(), "paper_only": True})
            else:
                self.order_manager.reject(order, "；".join(risk.get("risk_reasons") or risk.get("warnings") or ["风控未通过"]))
                self.audit_log.record("risk_blocked", {"order": order.to_dict(), "risk": risk, "paper_only": True})
                if risk.get("required_confirm") or risk.get("require_human_confirmation"):
                    confirm_task = self.human_confirm_queue.enqueue(
                        symbol=symbol,
                        action=signal.action,
                        reason="；".join(risk.get("warnings") or ["需要人工确认"]),
                        risk_flags=list(risk.get("warnings") or []),
                        payload={"order": order.to_dict(), "risk": risk, "signal": signal_row},
                    )
            row = order.to_dict()
            row["risk"] = risk
            if confirm_task is not None:
                row["human_confirm_task"] = confirm_task.to_dict()
            orders.append(row)
        self.account.mark_to_market({symbol: price})
        curve = {"timestamp": now.isoformat(timespec="seconds"), **self.account.snapshot()}
        self.portfolio_curve.append(curve)
        self.audit_log.record("realtime_paper_tick", {"symbol": symbol, "signal": signal_row, "orders": orders, "paper_only": True})
        self.audit_log.record("signal_generated", {"symbol": symbol, "signal": signal_row, "paper_only": True})
        return {
            "ok": True,
            "state": self.state.to_dict(),
            "signal": signal_row,
            "anomaly": anomaly.to_dict(),
            "freshness": freshness.to_dict(),
            "orders": orders,
            "portfolio": self.account.snapshot(),
        }

    def replay(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        ticks = list(payload.get("ticks") or [])
        if not ticks and payload.get("symbol"):
            base = {k: payload.get(k) for k in ["symbol", "price", "fundamental_score", "technical_score", "information_score", "market_score"] if k in payload}
            ticks = [base]
        outputs = []
        for idx, tick in enumerate(ticks):
            item = dict(tick)
            item.setdefault("symbol", payload.get("symbol"))
            item.setdefault("horizon", payload.get("horizon") or "intraday_paper")
            item["used_points"] = idx + 1
            outputs.append(self.tick(item, manual_replay=True))
        return {
            "ok": True,
            "tick_log": self.tick_log[-len(outputs) :] if outputs else [],
            "signal_log": [x.get("signal") for x in outputs],
            "order_log": [o for x in outputs for o in x.get("orders", [])],
            "portfolio_curve": self.portfolio_curve[-len(outputs) :] if outputs else [],
            "no_lookahead": True,
        }

    def _symbols(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [x.strip() for x in value.replace("，", ",").split(",") if x.strip()]
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return []

    def _optional(self, value: Any) -> float | None:
        if value in (None, "", "--"):
            return None
        return self._num(value)

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _parse_time(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _is_trading_time(self, now: datetime) -> bool:
        t = now.time()
        return time(9, 30) <= t <= time(11, 30) or time(13, 0) <= t <= time(15, 0)
