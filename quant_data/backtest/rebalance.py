from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import BacktestConfig, Order, Position


@dataclass(slots=True)
class RebalancePlan:
    orders: list[Order] = field(default_factory=list)
    residuals: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class RebalanceEngine:
    """Portfolio-level sell-first rebalance planner for A-share constraints."""

    def generate_orders(
        self,
        *,
        date: str,
        equity: float,
        cash: float,
        positions: dict[str, Position],
        target_weights: dict[str, float],
        prices: dict[str, float],
        config: BacktestConfig | None = None,
        blocked: dict[str, str] | None = None,
    ) -> RebalancePlan:
        cfg = config or BacktestConfig()
        blocked = blocked or {}
        plan = RebalancePlan()
        equity = max(float(equity or 0.0), 1.0)
        clipped = self._clip_targets(target_weights, cfg)
        current_weights = {
            symbol: (pos.quantity * float(prices.get(symbol, pos.last_price or pos.avg_cost or 0.0))) / equity
            for symbol, pos in positions.items()
        }
        desired_symbols = set(clipped)
        for symbol, pos in sorted(positions.items()):
            price = float(prices.get(symbol, pos.last_price or pos.avg_cost or 0.0) or 0.0)
            target_value = equity * clipped.get(symbol, 0.0)
            current_value = pos.quantity * price
            diff = current_value - target_value
            if diff <= 0 or price <= 0:
                continue
            if blocked.get(symbol):
                plan.residuals.append({"symbol": symbol, "side": "sell", "reason": blocked[symbol], "residual_value": round(diff, 2)})
                continue
            quantity = self._round_lot(diff / price, cfg.lot_size)
            quantity = min(quantity, pos.available_quantity if cfg.t_plus_one else pos.quantity)
            quantity = self._round_lot(quantity, cfg.lot_size)
            if quantity * price < cfg.min_trade_amount or quantity <= 0:
                plan.residuals.append({"symbol": symbol, "side": "sell", "reason": "不足最小交易金额或可卖数量", "residual_value": round(diff, 2)})
                continue
            plan.orders.append(Order(f"{date}-{symbol}-rebalance-sell", symbol, date, "sell", quantity=quantity, reason="调仓卖出降至目标权重"))
            cash += quantity * price
        buy_budget = max(0.0, cash - equity * max(0.0, cfg.cash_reserve_pct))
        for symbol, weight in sorted(clipped.items(), key=lambda x: x[1], reverse=True):
            if len(desired_symbols) > cfg.max_positions and symbol not in list(dict(sorted(clipped.items(), key=lambda x: x[1], reverse=True))[: cfg.max_positions]):
                continue
            price = float(prices.get(symbol, 0.0) or 0.0)
            if price <= 0:
                continue
            current_value = positions.get(symbol, Position(symbol=symbol)).quantity * price
            target_value = equity * weight
            diff = target_value - current_value
            if diff <= 0:
                continue
            if blocked.get(symbol):
                plan.residuals.append({"symbol": symbol, "side": "buy", "reason": blocked[symbol], "residual_value": round(diff, 2)})
                continue
            quantity = self._round_lot(min(diff, buy_budget) / price, cfg.lot_size)
            if quantity * price < cfg.min_trade_amount or quantity <= 0:
                plan.residuals.append({"symbol": symbol, "side": "buy", "reason": "现金或最小交易金额不足", "residual_value": round(diff, 2)})
                continue
            plan.orders.append(
                Order(
                    f"{date}-{symbol}-rebalance-buy",
                    symbol,
                    date,
                    "buy",
                    quantity=quantity,
                    target_weight=weight,
                    reason="调仓买入补至目标权重",
                )
            )
            buy_budget -= quantity * price
        if current_weights:
            plan.notes.append(f"当前持仓权重 {current_weights}")
        return plan

    @staticmethod
    def _clip_targets(targets: dict[str, float], cfg: BacktestConfig) -> dict[str, float]:
        rows = sorted(((s, max(0.0, min(float(w), cfg.max_single_position_pct))) for s, w in targets.items()), key=lambda x: x[1], reverse=True)
        rows = rows[: max(1, int(cfg.max_positions or 1))]
        total = sum(w for _, w in rows)
        max_total = max(0.0, min(1.0 - cfg.cash_reserve_pct, cfg.position_pct))
        if total > max_total and total > 0:
            rows = [(s, w / total * max_total) for s, w in rows]
        return dict(rows)

    @staticmethod
    def _round_lot(quantity: float, lot_size: int) -> int:
        lot = max(1, int(lot_size or 100))
        return max(0, int(quantity) // lot * lot)
