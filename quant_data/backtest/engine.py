from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .data_loader import BacktestDataLoader, date_text, field_value, number
from .execution import ExecutionSimulator
from .models import BacktestConfig, BacktestResult, Order, StrategySignal, Trade
from .portfolio import PortfolioManager
from .risk import calculate_metrics
from .signal_adapter import SignalAdapter


class BacktestEngine:
    """Daily no-lookahead engine for V3.19 research backtests."""

    def __init__(self, market_service: Any | None = None) -> None:
        self.loader = BacktestDataLoader(market_service)
        self.adapter = SignalAdapter()
        self.execution = ExecutionSimulator()

    def run(
        self,
        config: BacktestConfig,
        *,
        market_data: dict[str, list[Any]] | None = None,
        screener_rows: list[dict[str, Any]] | None = None,
        signals: dict[str, list[StrategySignal]] | None = None,
    ) -> BacktestResult:
        started = datetime.now().isoformat(timespec="seconds")
        run_id = config.run_id or f"bt-{uuid4().hex[:12]}"
        symbols = config.symbols or sorted((market_data or {}).keys())
        errors: list[str] = []
        warnings: list[str] = []
        if not symbols:
            symbols = ["300750"]
        bars_by_symbol: dict[str, list[Any]] = {}
        reports: dict[str, Any] = {}
        for symbol in symbols:
            rows, report = self.loader.load_bars(
                symbol,
                config,
                bars=(market_data or {}).get(symbol),
                force_refresh=False,
            )
            bars_by_symbol[symbol] = rows
            reports[symbol] = report
            warnings.extend(report.get("warnings", []))
        calendar = self._shared_calendar(bars_by_symbol)
        portfolio = PortfolioManager(config)
        all_orders: list[Order] = []
        all_fills = []
        trades: list[Trade] = []
        open_trades: dict[str, Trade] = {}
        pending_orders: list[Order] = []
        states = []
        if len(calendar) <= config.warmup_bars + 1:
            warnings.append("样本不足以完成 warmup 后回测")
        for day_index, current_date in enumerate(calendar):
            todays_bars = {symbol: self._bar_on(rows, current_date) for symbol, rows in bars_by_symbol.items()}
            todays_bars = {k: v for k, v in todays_bars.items() if v is not None}
            day_fills = []
            if pending_orders:
                remaining: list[Order] = []
                for order in pending_orders:
                    bar = todays_bars.get(order.symbol)
                    if bar is None:
                        remaining.append(order)
                        continue
                    decision = self.execution.execute_order(
                        order,
                        bar,
                        cash=portfolio.cash,
                        position=portfolio.positions.get(order.symbol),
                        config=config,
                    )
                    if decision.fill:
                        all_fills.append(decision.fill)
                        day_fills.append(decision.fill)
                        portfolio.apply_fill(decision.fill)
                        self._update_trades(decision.fill, order, open_trades, trades)
                pending_orders = remaining
            state = portfolio.mark_to_market(todays_bars, current_date, day_fills)
            states.append(state)
            portfolio.unlock_t_plus_one()
            if day_index < config.warmup_bars or day_index >= len(calendar) - 1:
                continue
            generated = signals.get(current_date, []) if signals else self._signals_for_day(
                current_date,
                bars_by_symbol,
                day_index,
                config,
                screener_rows=screener_rows,
            )
            stop_orders = portfolio.stop_orders(current_date, todays_bars)
            orders = [*portfolio.build_orders(generated, current_date), *stop_orders]
            for order in orders:
                ok, msg = self.loader.assert_no_lookahead(order.signal_date or current_date, calendar[day_index + 1], order.signal_date)
                if not ok:
                    warnings.append(msg)
                    continue
                order.date = calendar[day_index + 1]
                pending_orders.append(order)
                all_orders.append(order)
        for symbol, trade in list(open_trades.items()):
            bar = self._bar_on(bars_by_symbol.get(symbol, []), calendar[-1] if calendar else "")
            if bar is not None:
                price = number(field_value(bar, "close"))
                trade.exit_date = calendar[-1]
                trade.exit_price = price
                trade.exit_reason = "期末持仓按收盘价估算"
                trade.pnl = round((price - trade.entry_price) * trade.quantity - trade.costs, 6)
                trade.pnl_pct = round((price / trade.entry_price - 1) * 100 if trade.entry_price else 0.0, 4)
                trades.append(trade)
        equity_curve = [s.to_dict() for s in states]
        metrics = calculate_metrics(equity_curve, trades, all_fills)
        ended = datetime.now().isoformat(timespec="seconds")
        return BacktestResult(
            run_id=run_id,
            config=config,
            status="ok" if not errors else "error",
            started_at=started,
            ended_at=ended,
            symbols=symbols,
            orders=all_orders,
            fills=all_fills,
            trades=trades,
            portfolio_states=states,
            equity_curve=equity_curve,
            metrics=metrics,
            data_quality={"symbols": reports, "no_lookahead": True, "pit_note": "信号日生成，下一交易日成交。"},
            warnings=warnings,
            errors=errors,
            cache_status="memory" if market_data else "service",
        )

    def _signals_for_day(
        self,
        current_date: str,
        bars_by_symbol: dict[str, list[Any]],
        day_index: int,
        config: BacktestConfig,
        *,
        screener_rows: list[dict[str, Any]] | None = None,
    ) -> list[StrategySignal]:
        if config.strategy == "score_rank_rebalance" and screener_rows:
            dated = [x for x in screener_rows if str(x.get("date", current_date)) <= current_date]
            return self.adapter.score_rank_rebalance(dated, current_date, config)
        rows = []
        for symbol, bars in bars_by_symbol.items():
            if day_index >= len(bars):
                continue
            history = bars[: day_index + 1]
            row = self._feature_row(symbol, history)
            if row:
                rows.append(row)
        if config.strategy in {"factor_rule_strategy", "score_rank_rebalance"}:
            return self.adapter.factor_rule_strategy(rows, config)
        return self.adapter.factor_rule_strategy(rows, config)

    def _feature_row(self, symbol: str, history: list[Any]) -> dict[str, Any] | None:
        if not history:
            return None
        closes = [number(field_value(x, "close")) for x in history]
        volumes = [number(field_value(x, "volume")) for x in history]
        last = history[-1]
        close = closes[-1]
        ma20 = sum(closes[-20:]) / min(len(closes), 20)
        ma60 = sum(closes[-60:]) / min(len(closes), 60)
        volume_ma20 = sum(volumes[-20:]) / max(1, min(len(volumes), 20))
        rsi = self._rsi(closes[-15:])
        return {
            "symbol": symbol,
            "date": date_text(field_value(last, "ts", field_value(last, "date", ""))),
            "open": number(field_value(last, "open")),
            "high": number(field_value(last, "high")),
            "low": number(field_value(last, "low")),
            "close": close,
            "ma20": ma20,
            "ma60": ma60,
            "rsi14": rsi,
            "volume_ratio": volumes[-1] / volume_ma20 if volume_ma20 else 1.0,
        }

    @staticmethod
    def _rsi(values: list[float]) -> float:
        if len(values) < 2:
            return 50.0
        gains = []
        losses = []
        for a, b in zip(values, values[1:]):
            delta = b - a
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))
        avg_gain = sum(gains) / max(len(gains), 1)
        avg_loss = sum(losses) / max(len(losses), 1)
        if avg_loss == 0:
            return 100.0 if avg_gain else 50.0
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    @staticmethod
    def _shared_calendar(bars_by_symbol: dict[str, list[Any]]) -> list[str]:
        dates = sorted({date_text(field_value(row, "ts", field_value(row, "date", ""))) for rows in bars_by_symbol.values() for row in rows})
        return [x for x in dates if x]

    @staticmethod
    def _bar_on(rows: list[Any], date: str) -> Any | None:
        for row in rows:
            if date_text(field_value(row, "ts", field_value(row, "date", ""))) == date:
                return row
        return None

    def _update_trades(self, fill: Any, order: Order, open_trades: dict[str, Trade], trades: list[Trade]) -> None:
        if fill.blocked or fill.quantity <= 0:
            return
        if fill.side == "buy":
            open_trades[fill.symbol] = Trade(
                symbol=fill.symbol,
                entry_date=fill.date,
                exit_date=None,
                entry_price=fill.price,
                exit_price=None,
                quantity=fill.quantity,
                entry_reason=order.reason,
                entry_signal_score=order.signal_score,
                costs=fill.total_cost,
            )
        elif fill.symbol in open_trades:
            trade = open_trades.pop(fill.symbol)
            trade.exit_date = fill.date
            trade.exit_price = fill.price
            trade.exit_reason = order.reason
            trade.exit_signal_score = order.signal_score
            trade.costs += fill.total_cost
            trade.pnl = round((fill.price - trade.entry_price) * min(fill.quantity, trade.quantity) - trade.costs, 6)
            trade.pnl_pct = round((fill.price / trade.entry_price - 1) * 100 if trade.entry_price else 0.0, 4)
            trades.append(trade)
