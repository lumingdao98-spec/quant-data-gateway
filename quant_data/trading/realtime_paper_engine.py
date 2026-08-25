from __future__ import annotations

from datetime import datetime, time
from typing import Any

from quant_data.backtest.market_rules import MarketRuleEngine

from .anomaly_guard import AnomalyGuard
from .audit_log import AuditLog
from .data_freshness import DataFreshnessGuard
from .human_confirm_queue import HumanConfirmQueue
from .order_manager import OrderManager
from .paper_account import PaperAccount
from .realtime_state import RealtimePaperConfig, RealtimePaperState
from .risk_gateway import RiskGateway
from .signal_fusion import SignalFusionEngine, UnifiedSignal
from .time_utils import cn_market_now, cn_market_time


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
        self.market_rules = MarketRuleEngine.default()
        self.state = RealtimePaperState()
        self.signals: list[UnifiedSignal] = []
        self.signal_meta: list[dict[str, Any]] = []
        self.tick_log: list[dict[str, Any]] = []
        self.portfolio_curve: list[dict[str, Any]] = []

    def start(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        initial_cash = float(payload.get("initial_cash") or self.account.initial_cash)
        reset_account = bool(payload.get("reset_account", True))
        if reset_account or (initial_cash != self.account.initial_cash and not self.account.positions):
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
            min_commission=max(0.0, float(payload.get("min_commission", 5.0))),
            sell_tax_rate=max(0.0, float(payload.get("sell_tax_rate", 0.0005))),
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

    def approve_confirmation(self, task_id: str, *, operator: str = "paper_user") -> dict[str, Any]:
        task = self.human_confirm_queue.tasks.get(task_id)
        if task is None:
            raise KeyError(f"confirm task not found: {task_id}")
        if task.status != "pending":
            return {"ok": False, "message": f"确认任务状态为 {task.status}，不能重复执行", "data": task.to_dict()}
        if self.state.status != "running" or not self._is_trading_time(cn_market_now()):
            return {"ok": False, "message": "当前非交易时段或模拟会话未运行，确认任务保持待处理", "data": task.to_dict()}
        payload = dict(task.payload or {})
        risk = dict(payload.get("risk") or {})
        signal = dict(payload.get("signal") or {})
        freshness = dict(signal.get("data_freshness") or signal.get("freshness") or {})
        hard_reasons = list(risk.get("risk_reasons") or risk.get("reasons") or [])
        if hard_reasons or freshness.get("action") == "block":
            return {
                "ok": False,
                "message": "硬风控或过期数据不允许人工绕过",
                "risk_reasons": hard_reasons,
                "freshness": freshness,
                "data": task.to_dict(),
            }
        source_order = dict(payload.get("order") or {})
        symbol = str(source_order.get("symbol") or task.symbol)
        side = str(source_order.get("side") or task.action)
        price = float(source_order.get("price") or signal.get("quote_price") or 0.0)
        if not symbol or price <= 0:
            return {"ok": False, "message": "订单代码或价格缺失，不能模拟成交", "data": task.to_dict()}
        task = self.human_confirm_queue.approve(task_id, operator=operator)
        now = cn_market_now()
        rule = self.market_rules.resolve_profile(symbol, asof=now)
        self.account.settle_t_plus_one(now)
        order = self.order_manager.build_order(
            symbol=symbol,
            target_weight=float(source_order.get("target_weight") or signal.get("target_weight") or 0.0),
            side=side,
            price=price,
            order_type=str(source_order.get("order_type") or "market"),
            reason=f"人工确认 {task_id}：{task.reason}",
            lot_size=rule.lot_size_buy,
        )
        self.order_manager.simulate_fill(
            order,
            fill_price=price,
            fee_rate=self.state.config.fee_rate,
            slippage_rate=self.state.config.slippage_rate,
            min_commission=self.state.config.min_commission,
            tax_rate=self.state.config.sell_tax_rate if rule.security_type == "stock" else 0.0,
            filled_at=now.isoformat(timespec="seconds"),
            t_plus_one=rule.t_plus_one,
        )
        self.account.mark_to_market({symbol: price})
        self.audit_log.record(
            "paper_confirmation_executed",
            {
                "task": task.to_dict(),
                "order": order.to_dict(),
                "portfolio": self.account.snapshot(),
                "paper_only": True,
            },
        )
        return {
            "ok": order.status in {"filled", "partial"},
            "data": task.to_dict(),
            "order": order.to_dict(),
            "portfolio": self.account.snapshot(),
            "paper_only": True,
        }

    def tick(self, payload: dict[str, Any] | None = None, *, manual_replay: bool = False) -> dict[str, Any]:
        payload = payload or {}
        now = self._parse_time(payload.get("now") or payload.get("ts")) or cn_market_now()
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
        rule = self.market_rules.resolve_profile(
            symbol,
            asof=now,
            security_master=payload.get("security_master") if isinstance(payload.get("security_master"), dict) else None,
        )
        self.account.settle_t_plus_one(now)
        self.state.is_trading_session = is_trading
        self.state.last_tick_at = now.isoformat(timespec="seconds")
        self.state.tick_count += 1
        if self.state.status != "running" and not manual_replay:
            self.audit_log.record("tick_ignored", {"symbol": symbol, "reason": "engine stopped"})
            return {"ok": False, "message": "engine stopped", "state": self.state.to_dict()}
        if not is_trading and not manual_replay:
            self.audit_log.record("tick_rejected", {"symbol": symbol, "reason": "非交易时段禁止自动下单"})
            return {"ok": True, "message": "非交易时段，仅记录不下单", "state": self.state.to_dict(), "orders": []}

        decision_hydrated = bool(payload.get("score_source") or payload.get("recent_information"))
        compatibility_now = None if decision_hydrated else now.isoformat(timespec="seconds")
        timestamps = {
            "quote": quote.get("ts"),
            "intraday": payload.get("intraday_ts"),
            "news": payload.get("news_ts") or compatibility_now,
            "technical": payload.get("technical_ts") or compatibility_now,
            "company_profile": payload.get("company_profile_ts") or compatibility_now,
        }
        freshness = self.freshness_guard.check(timestamps, now=now)
        self.state.freshness_status = freshness.freshness_status
        anomaly_features = dict(payload.get("anomaly_features") or {})
        anomaly_features.setdefault("stale_data", freshness.action == "block")
        anomaly = self.anomaly_guard.check(anomaly_features)
        event_context = self._event_watch_context(payload)
        missing_data = list(payload.get("missing_data") or []) + list(event_context.get("missing_data") or [])
        evidence = list(payload.get("evidence") or anomaly.evidence or ["手动 tick 生成信号"])
        evidence.extend(event_context.get("evidence") or [])
        raw_dimension_scores = {
            "fundamental": self._optional(payload.get("fundamental_score")),
            "technical": self._optional(payload.get("technical_score")),
            "information": self._optional(payload.get("information_score")),
            "fund_flow": self._optional(payload.get("fund_flow_score")),
            "market": self._optional(payload.get("market_score")),
        }
        execution_scores: dict[str, float | None] = {}
        excluded_by_readiness: list[dict[str, Any]] = []
        for key in ("fundamental", "technical", "information", "fund_flow", "market"):
            value, exclusion = self._execution_score(payload, key)
            execution_scores[key] = value
            if exclusion:
                excluded_by_readiness.append(exclusion)
                missing_data.append(f"{key}_excluded_by_readiness")
        configured_score_weights = (
            dict(payload.get("score_weights"))
            if isinstance(payload.get("score_weights"), dict)
            else {}
        )
        configured_score_weights["mode"] = str(
            payload.get("score_weight_mode")
            or configured_score_weights.get("mode")
            or "manual"
        )
        signal = self.signal_fusion.fuse(
            symbol=symbol,
            horizon=str(payload.get("horizon") or self.state.config.horizon),
            screening_score=self._optional(payload.get("screening_score")),
            daily_k_score=self._optional(payload.get("daily_k_score")),
            intraday_score=self._optional(payload.get("intraday_score")),
            fundamental_score=execution_scores["fundamental"],
            technical_score=execution_scores["technical"],
            information_score=execution_scores["information"],
            fund_flow_score=execution_scores["fund_flow"],
            market_score=execution_scores["market"],
            score_weights=configured_score_weights,
            anomaly_score=anomaly.anomaly_score,
            anomaly_action=anomaly.action_suggestion,
            info_negative_veto=bool(payload.get("info_negative_veto") or event_context.get("veto")),
            technical_broken=bool(payload.get("technical_broken")),
            fundamental_poor=bool(payload.get("fundamental_poor")),
            strategy_family=str(payload.get("strategy_family") or payload.get("strategy") or ""),
            evidence=list(dict.fromkeys(evidence)),
            data_freshness=freshness.to_dict(),
            missing_data=list(dict.fromkeys(missing_data)),
            now=now,
        )
        if event_context.get("block_new_position") and signal.action in {"buy", "add"}:
            signal.action = "hold"
            signal.target_weight = 0.0
            signal.requires_manual_confirm = True
            block_reason = str(event_context.get("block_reason") or "信息质量或临近事件不满足自动新增仓位条件")
            signal.reason = f"{signal.reason}；{block_reason}" if signal.reason else block_reason
            signal.evidence = list(dict.fromkeys(signal.evidence + [block_reason]))
        dimension_readiness = dict(payload.get("dimension_readiness") or {})
        if dimension_readiness and not dimension_readiness.get("auto_entry_eligible", False) and signal.action in {"buy", "add"}:
            signal.action = "hold"
            signal.target_weight = 0.0
            signal.requires_manual_confirm = True
            reasons = [str(value) for value in (dimension_readiness.get("entry_block_reasons") or []) if str(value)]
            block_reason = "三面决策门禁未通过" + (f"：{'；'.join(reasons[:4])}" if reasons else "")
            signal.reason = f"{signal.reason}；{block_reason}" if signal.reason else block_reason
            signal.evidence = list(dict.fromkeys(signal.evidence + reasons + [block_reason]))
        strategy_controls = self._apply_strategy_controls(signal, payload, price)
        self.signals.append(signal)
        previous_signal = next(
            (row for row in reversed(self.signal_meta) if str(row.get("symbol") or "") == symbol),
            None,
        )
        previous_score = self._optional((previous_signal or {}).get("final_score"))
        score_delta = round(signal.final_score - previous_score, 2) if previous_score is not None else None
        score_breakdown = dict(payload.get("score_breakdown") or {})
        signal_score_breakdown = dict(signal.score_breakdown or {})
        sources = dict(score_breakdown.get("sources") or {})
        score_breakdown.update(signal_score_breakdown)
        if sources:
            score_breakdown["sources"] = sources
        score_breakdown["raw_dimension_scores"] = raw_dimension_scores
        score_breakdown["execution_dimension_scores"] = execution_scores
        score_breakdown["excluded_by_readiness"] = excluded_by_readiness
        score_breakdown["final_score_delta"] = score_delta
        signal_row = signal.to_dict()
        signal_row.update(
            {
                "name": str(quote.get("name") or payload.get("name") or symbol),
                "quote_price": price,
                "bid1": self._best_price(quote, "bid"),
                "ask1": self._best_price(quote, "ask"),
                "orderbook_source": quote.get("orderbook_source") or (payload.get("orderbook_snapshot") or {}).get("source") or "missing",
                "orderbook_snapshot": dict(payload.get("orderbook_snapshot") or {}),
                "recent_information": dict(payload.get("recent_information") or {}),
                "market_regime": dict(payload.get("market_regime") or {}),
                "score_delta": score_delta,
                "score_breakdown": score_breakdown,
                "score_source": str(payload.get("score_source") or "unified_realtime_score"),
                "session_mode": "盘中实时" if is_trading else ("休市回放" if manual_replay else "休市观察"),
                "paper_only": True,
                "strategy_controls": strategy_controls,
                "event_watch_context": event_context,
                "dimension_readiness": dimension_readiness,
                "auto_entry_eligible": bool(dimension_readiness.get("auto_entry_eligible", True)),
                "entry_block_reasons": list(dimension_readiness.get("entry_block_reasons") or []),
                "market_rule": rule.to_dict(),
            }
        )
        self.signal_meta.append(signal_row)
        self.tick_log.append({"timestamp": now.isoformat(timespec="seconds"), "symbol": symbol, "name": signal_row["name"], "price": price, "signal": signal_row, "anomaly": anomaly.to_dict(), "freshness": freshness.to_dict()})
        orders: list[dict[str, Any]] = []
        execution_diagnostic: dict[str, Any] | None = None
        if signal.action in {"buy", "add", "sell", "reduce"} and price > 0:
            sizing = self.order_manager.preview_order(
                symbol=symbol,
                target_weight=signal.target_weight,
                side=signal.action,
                price=price,
                lot_size=rule.lot_size_buy,
            )
            if int(sizing.get("quantity") or 0) <= 0:
                execution_diagnostic = sizing
                signal_row["execution_diagnostic"] = sizing
                self.audit_log.record(
                    "order_skipped_sizing",
                    {"symbol": symbol, "signal": signal_row, "sizing": sizing, "paper_only": True},
                )
            else:
                order = self.order_manager.build_order(
                    symbol=symbol,
                    target_weight=signal.target_weight,
                    side=signal.action,
                    price=price,
                    order_type=str(payload.get("order_type") or "market"),
                    reason=signal.reason,
                    lot_size=rule.lot_size_buy,
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
                    execution_price = self._execution_price(quote, signal.action, price)
                    self.order_manager.simulate_fill(
                        order,
                        fill_price=execution_price,
                        fee_rate=self.state.config.fee_rate,
                        slippage_rate=self.state.config.slippage_rate,
                        min_commission=self.state.config.min_commission,
                        tax_rate=self.state.config.sell_tax_rate if rule.security_type == "stock" else 0.0,
                        filled_at=now.isoformat(timespec="seconds"),
                        t_plus_one=rule.t_plus_one,
                    )
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
        signal_ref = {
            "symbol": symbol,
            "timestamp": signal_row.get("timestamp") or now.isoformat(timespec="seconds"),
            "action": signal_row.get("action"),
            "final_score": signal_row.get("final_score"),
            "target_weight": signal_row.get("target_weight"),
            "quote_price": signal_row.get("quote_price"),
            "score_source": signal_row.get("score_source"),
            "missing_data": list(signal_row.get("missing_data") or [])[:12],
        }
        order_refs = [
            {
                "order_id": row.get("order_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "status": row.get("status"),
                "quantity": row.get("quantity"),
            }
            for row in orders
        ]
        self.audit_log.record("realtime_paper_tick", {"signal_ref": signal_ref, "order_refs": order_refs, "paper_only": True})
        self.audit_log.record("signal_generated", {"signal_ref": signal_ref, "paper_only": True})
        return {
            "ok": True,
            "state": self.state.to_dict(),
            "signal": signal_row,
            "anomaly": anomaly.to_dict(),
            "freshness": freshness.to_dict(),
            "orders": orders,
            "portfolio": self.account.snapshot(),
            "execution_diagnostic": execution_diagnostic,
        }

    @staticmethod
    def _best_price(quote: dict[str, Any], side: str) -> float | None:
        direct_keys = ("bid1", "buy1", "best_bid") if side == "bid" else ("ask1", "sell1", "best_ask")
        for key in direct_keys:
            try:
                value = quote.get(key)
                if value not in (None, "", "--") and float(value) > 0:
                    return float(value)
            except (TypeError, ValueError):
                continue
        levels = quote.get("bids" if side == "bid" else "asks") or []
        if levels and isinstance(levels[0], dict):
            try:
                value = float(levels[0].get("price") or 0)
                return value if value > 0 else None
            except (TypeError, ValueError):
                return None
        return None

    def _execution_price(self, quote: dict[str, Any], action: str, fallback: float) -> float:
        side = "ask" if action in {"buy", "add"} else "bid"
        price = self._best_price(quote, side) or fallback
        return round(max(float(price or fallback), 0.0), 4)

    def replay(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        ticks = list(payload.get("ticks") or [])
        if not ticks and payload.get("symbol"):
            base = {
                k: payload.get(k)
                for k in ["symbol", "price", "fundamental_score", "technical_score", "information_score", "fund_flow_score", "market_score"]
                if k in payload
            }
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
            if any(sep in value for sep in ["，", "；", "、", "|", ";", "\n", "\t", " "]):
                text = value
                for sep in ["，", "；", "、", "|", ";", "\n", "\t", " "]:
                    text = text.replace(sep, ",")
                return [x.strip() for x in text.split(",") if x.strip()]
            return [x.strip() for x in value.replace("，", ",").split(",") if x.strip()]
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return []

    def _list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if value in (None, ""):
            return []
        return self._symbols(str(value))

    def _pct(self, value: Any, default: float = 0.0) -> float:
        try:
            if value in (None, "", "--"):
                return float(default)
            return float(value)
        except Exception:
            return float(default)

    def _strategy_param_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw = payload.get("strategy_parameters")
        if not isinstance(raw, dict):
            return []
        combo = self._list(payload.get("strategy_combo")) or list(raw.keys())
        rows: list[dict[str, Any]] = []
        for key in combo:
            item = raw.get(key)
            if isinstance(item, dict) and item.get("enabled", True) is not False:
                rows.append({**item, "strategy": str(item.get("strategy") or key)})
        return rows

    def _apply_strategy_controls(self, signal: UnifiedSignal, payload: dict[str, Any], price: float) -> dict[str, Any]:
        risk = dict(payload.get("risk_controls") or {})
        profile = dict(payload.get("screener_signal") or {})
        rows = self._strategy_param_rows(payload)
        strategy_combo = self._list(payload.get("strategy_combo"))
        tags = {str(x) for x in (profile.get("strategy_tags") or profile.get("tags") or [])}
        selected_row = next((row for row in rows if str(row.get("strategy") or "") in tags), None)
        if selected_row is None:
            selected_row = next((row for row in rows if str(row.get("strategy") or "") == "score_driven"), None)
        if selected_row is None and rows:
            selected_row = rows[0]
        selected_row = dict(selected_row or {})
        selected_strategy = str(selected_row.get("strategy") or "global_risk")
        stop_pct = self._pct(selected_row.get("stop_loss_pct"), self._pct(risk.get("stop_loss_pct"), 8.0))
        take_pct = self._pct(selected_row.get("take_profit_pct"), self._pct(risk.get("take_profit_pct"), 18.0))
        max_drawdown_pct = self._pct(selected_row.get("max_drawdown_pct"), self._pct(risk.get("max_drawdown_pct"), 18.0))
        strategy_cap = self._pct(selected_row.get("max_single_position_pct"), self._pct(risk.get("max_single_position_pct"), 20.0))
        global_cap = self._pct(risk.get("max_single_position_pct"), strategy_cap)
        max_single_pct = min(strategy_cap, global_cap) if global_cap > 0 else strategy_cap
        cap = max(0.0, min(max_single_pct / 100.0, 1.0))
        hints: list[str] = []

        profile_action = str(profile.get("action") or "").lower()
        if profile_action in {"avoid", "sell"}:
            signal.action = "avoid" if profile_action == "avoid" else "sell"
            signal.target_weight = 0.0
            hints.append(f"screener_action={profile_action}")
        elif profile_action == "reduce" and signal.action in {"buy", "add", "hold"}:
            signal.action = "reduce"
            signal.target_weight = min(signal.target_weight, cap * 0.35 if cap else signal.target_weight)
            hints.append("screener_action=reduce")
        elif profile_action == "buy":
            hints.append("screener_buy_audit_only")

        hint_pct = self._pct(profile.get("target_weight_hint_pct"), 0.0)
        if signal.action in {"buy", "add"}:
            if hint_pct > 0:
                signal.target_weight = min(signal.target_weight, hint_pct / 100.0)
                hints.append(f"screener_target_cap={hint_pct:.2f}%")
            if cap > 0:
                signal.target_weight = min(signal.target_weight, cap)
                hints.append(f"max_single_position={max_single_pct:.2f}%")

        pos = self.account.positions.get(signal.symbol)
        current_weight = 0.0
        if pos and self.account.equity > 0:
            market_price = price or pos.market_price or pos.avg_cost
            current_value = max(0.0, pos.quantity * market_price)
            current_weight = current_value / max(self.account.equity, 1.0)
            if price > 0 and pos.avg_cost > 0 and stop_pct > 0 and price <= pos.avg_cost * (1 - stop_pct / 100.0):
                signal.action = "sell"
                signal.target_weight = 0.0
                hints.append(f"stop_loss_triggered={stop_pct:.2f}%")
            elif price > 0 and pos.avg_cost > 0 and take_pct > 0 and price >= pos.avg_cost * (1 + take_pct / 100.0):
                signal.action = "reduce"
                signal.target_weight = min(signal.target_weight, max(0.0, current_weight * 0.5))
                hints.append(f"take_profit_reduce={take_pct:.2f}%")

        if max_drawdown_pct > 0 and self.account.max_drawdown <= -(max_drawdown_pct / 100.0):
            signal.action = "reduce" if current_weight > 0 else "hold"
            signal.target_weight = min(signal.target_weight, max(0.0, current_weight * 0.5))
            hints.append(f"max_drawdown_guard={max_drawdown_pct:.2f}%")

        if hints:
            signal.reason = (signal.reason + "；" if signal.reason else "") + "；".join(hints)
            signal.evidence = list(dict.fromkeys(list(signal.evidence) + hints))
        return {
            "strategy_combo": strategy_combo,
            "position_sizing": str(payload.get("position_sizing") or ""),
            "active_strategy_parameters": rows,
            "selected_strategy": selected_strategy,
            "selected_strategy_parameters": selected_row,
            "stop_loss_pct": stop_pct,
            "take_profit_pct": take_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "max_single_position_pct": max_single_pct,
            "current_weight": round(current_weight, 6),
            "applied_hints": hints,
        }

    def _event_watch_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        watch = dict(payload.get("event_watch") or {})
        enabled_keys = [key for key, value in watch.items() if isinstance(value, bool) and value]
        evidence: list[str] = []
        missing: list[str] = []
        veto = False
        block_new_position = False
        block_reason = ""
        recent_information = dict(payload.get("recent_information") or {})
        future_calendar = recent_information.get("future_event_calendar") or payload.get("future_event_calendar") or {}
        future_events = [dict(row) for row in (future_calendar.get("events") or []) if isinstance(row, dict)] if isinstance(future_calendar, dict) else []
        confirmed_events = [
            row for row in future_events
            if row.get("confirmation_status") == "公开来源已确认"
            and row.get("attention_level") == "高"
        ]
        inferred_events = [row for row in future_events if row.get("confirmation_status") == "规则推算待确认"]
        lookahead_days = int(self._pct(watch.get("event_lookahead_days"), 7.0))
        blackout_before_days = int(self._pct(watch.get("blackout_before_days"), 3.0))
        upcoming_confirmed = [
            row for row in confirmed_events
            if 0 <= int(self._pct(row.get("days_until"), 999.0)) <= max(0, lookahead_days)
        ]
        blackout_events = [
            row for row in upcoming_confirmed
            if int(self._pct(row.get("days_until"), 999.0)) <= max(0, blackout_before_days)
        ]
        if recent_information:
            if recent_information.get("stale"):
                block_new_position = True
                block_reason = "信息快照已过期，禁止自动新增仓位"
                missing.append("recent_information_stale")
            elif recent_information.get("auto_buy_eligible") is False:
                block_new_position = True
                block_reason = "近期信息正文质量或可核验证据不足，禁止自动新增仓位"
                missing.append("recent_information_not_trade_eligible")
            if blackout_events:
                block_new_position = True
                event_titles = "、".join(str(row.get("title") or row.get("event_type_cn") or "高关注事件") for row in blackout_events[:3])
                block_reason = f"临近已确认高关注事件：{event_titles}；新增仓位需人工确认"
                evidence.append("confirmed_future_event_blackout")
            elif upcoming_confirmed:
                evidence.append("confirmed_future_event_watch")
            if inferred_events:
                evidence.append("rule_inferred_calendar_watch_only")
        info_present = any(payload.get(key) for key in ("news_ts", "info_snapshot_ts", "announcement_ts", "financial_report_ts"))
        if enabled_keys and not info_present:
            missing.append("event_watch_snapshot_missing")
        if watch.get("financial_reports") and payload.get("financial_report_blackout"):
            evidence.append("financial_report_blackout")
            veto = True
        if watch.get("half_year_reports") and payload.get("half_year_report_window"):
            evidence.append("half_year_report_window")
        if watch.get("exchange_announcements") and payload.get("announcement_risk"):
            evidence.append("announcement_risk")
            veto = True
        if watch.get("major_negative_news") and payload.get("major_negative_news"):
            evidence.append("major_negative_news")
            veto = True
        if watch.get("policy_industry_news") and payload.get("policy_industry_risk"):
            evidence.append("policy_industry_risk")
        return {
            "enabled": bool(enabled_keys),
            "event_watch_enabled": bool(enabled_keys),
            "enabled_keys": enabled_keys,
            "watched_events": enabled_keys,
            "missing_data": missing,
            "evidence": evidence,
            "veto": veto,
            "block_new_position": block_new_position,
            "block_reason": block_reason,
            "confirmed_future_events": upcoming_confirmed,
            "rule_inferred_events": inferred_events,
            "lookahead_days": lookahead_days,
            "blackout_before_days": blackout_before_days,
            "blackout_after_days": int(self._pct(watch.get("blackout_after_days"), 0.0)),
        }

    def _optional(self, value: Any) -> float | None:
        if value in (None, "", "--"):
            return None
        return self._num(value)

    def _execution_score(self, payload: dict[str, Any], key: str) -> tuple[float | None, dict[str, Any] | None]:
        value = self._optional(payload.get(f"{key}_score"))
        readiness = payload.get("dimension_readiness")
        if not isinstance(readiness, dict):
            return value, None
        row: dict[str, Any] | None = None
        if key == "market":
            candidate = readiness.get("market_context")
            row = dict(candidate) if isinstance(candidate, dict) else None
        else:
            for candidate in readiness.get("dimensions") or []:
                if isinstance(candidate, dict) and str(candidate.get("key") or "") == key:
                    row = dict(candidate)
                    break
        if not row or bool(row.get("ready")):
            return value, None
        return None, {
            "key": key,
            "raw_score": value,
            "quality_status": str(row.get("quality_status") or "missing"),
            "reason": str(row.get("reason") or "该维度本轮未通过真实性或新鲜度门禁"),
        }

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _parse_time(self, value: Any) -> datetime | None:
        return cn_market_time(value)

    def _is_trading_time(self, now: datetime) -> bool:
        t = now.time()
        return time(9, 30) <= t <= time(11, 30) or time(13, 0) <= t <= time(15, 0)
