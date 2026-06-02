from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from statistics import mean, pstdev

from quant_data.models import Bar


@dataclass
class BacktestConfig:
    strategy: str = "ma_cross"
    strategy_combo: tuple[str, ...] = ()
    combo_buy_rule: str = "at_least_2"
    combo_sell_rule: str = "any"
    initial_cash: float = 100_000.0
    fee_rate: float = 0.0003
    slippage_rate: float = 0.0005
    position_pct: float = 1.0
    stop_loss_pct: float = 8.0
    take_profit_pct: float = 0.0
    buy_score: float = 62.0
    sell_score: float = 48.0
    lot_size: int = 100


SUPPORTED_STRATEGIES = [
    {
        "key": "combo_signal",
        "name": "组合策略判断",
        "description": "可同时勾选评分、均线、突破、MACD、BOLL等策略，买入按命中数量确认，卖出按任一/全部转弱确认。",
    },
    {
        "key": "score_driven",
        "name": "日评分驱动",
        "description": "每天按趋势、动量、量能、位置和风险生成研究分；分数达到买入阈值后，下一交易日开盘买入，低于卖出阈值或风险升高卖出。",
    },
    {
        "key": "score_reversal",
        "name": "评分拐点修复",
        "description": "评分从低位重新站回阈值，且价格未明显追高时买入；评分转弱或跌破MA20卖出。",
    },
    {
        "key": "ma_cross",
        "name": "MA趋势跟随",
        "description": "收盘价站上MA20且MA5高于MA20后，下一交易日开盘买入；跌破MA20或MA5下穿MA20卖出。",
    },
    {
        "key": "rsi_rebound",
        "name": "RSI超跌反弹",
        "description": "RSI14低位后出现价格修复，下一交易日开盘买入；RSI过热或跌回MA20卖出。",
    },
    {
        "key": "breakout",
        "name": "20日突破放量",
        "description": "收盘突破前20日高点且成交量高于20日均量，下一交易日开盘买入；跌破MA10或触发止损卖出。",
    },
    {
        "key": "macd_momentum",
        "name": "MACD动量确认",
        "description": "MACD柱由弱转强且价格站上MA20买入；MACD转弱或跌回MA20卖出。",
    },
    {
        "key": "boll_pullback",
        "name": "BOLL回踩修复",
        "description": "价格从BOLL下轨/中轨附近修复且RSI不过热买入；触及上轨或跌破中轨卖出。",
    },
    {
        "key": "trend_pullback",
        "name": "趋势回踩MA20",
        "description": "MA60向上背景下，价格回踩MA20后重新转强买入；跌破MA20或评分转弱卖出。",
    },
]


SCORE_FORMULA = {
    "scale": "0-100",
    "formula": "score = trend_score*0.34 + momentum_score*0.25 + volume_score*0.19 + structure_score*0.22 - risk_penalty*0.45",
    "components": [
        {"key": "trend_score", "name": "趋势", "weight": 0.34, "basis": "收盘价相对MA20/MA60/MA120、MA5/MA20关系、MA20斜率"},
        {"key": "momentum_score", "name": "动量", "weight": 0.25, "basis": "5日/20日涨跌、RSI14区间、MACD柱变化"},
        {"key": "volume_score", "name": "量能", "weight": 0.19, "basis": "成交量/成交额相对20日均值，放量上涨加分，放量下跌扣分"},
        {"key": "structure_score", "name": "位置结构", "weight": 0.22, "basis": "60日区间位置、BOLL轨道位置、是否处于过热区"},
        {"key": "risk_penalty", "name": "风险扣分", "weight": -0.45, "basis": "高位、RSI过热、放量下跌、深回撤、跌破MA20"},
    ],
    "note": "当前回测评分只回放历史日K可见数据；还没有把历史新闻、公告、财务和大盘情绪逐日复盘进去，所以它是实盘筛选评分的量价技术底分版本。",
}


def _num(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def _pct(value: float) -> float:
    return round(value * 100, 2)


def _ma_at(values: list[float], idx: int, period: int) -> float | None:
    if period <= 0 or idx + 1 < period:
        return None
    window = values[idx + 1 - period : idx + 1]
    if len(window) < period:
        return None
    return mean(window)


def _rsi_at(values: list[float], idx: int, period: int = 14) -> float | None:
    if idx < period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for pos in range(idx + 1 - period, idx + 1):
        diff = values[pos] - values[pos - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(value * k + out[-1] * (1 - k))
    return out


def _macd_hist_series(values: list[float]) -> list[float]:
    if not values:
        return []
    fast = _ema_series(values, 12)
    slow = _ema_series(values, 26)
    dif = [a - b for a, b in zip(fast, slow)]
    dea = _ema_series(dif, 9)
    return [(d - e) * 2 for d, e in zip(dif, dea)]


def _boll_at(values: list[float], idx: int, period: int = 20) -> dict[str, float | None]:
    if idx + 1 < period:
        return {"mid": None, "upper": None, "lower": None, "width_pct": None}
    window = values[idx + 1 - period : idx + 1]
    mid = mean(window)
    sd = pstdev(window) if len(window) > 1 else 0.0
    upper = mid + sd * 2
    lower = mid - sd * 2
    return {
        "mid": mid,
        "upper": upper,
        "lower": lower,
        "width_pct": (upper - lower) / mid * 100 if mid else None,
    }


def _position_at(values: list[float], idx: int, period: int) -> float | None:
    if idx + 1 < period:
        return None
    window = values[idx + 1 - period : idx + 1]
    lo = min(window)
    hi = max(window)
    if hi <= lo:
        return 50.0
    return (values[idx] - lo) / (hi - lo) * 100


def _ret_pct(values: list[float], idx: int, period: int) -> float:
    if idx < period or values[idx - period] == 0:
        return 0.0
    return (values[idx] / values[idx - period] - 1) * 100


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


class BacktestService:
    """日线交易回测服务。

    默认口径偏保守：信号在收盘后确认，下一交易日开盘成交，计入手续费和滑点。
    """

    strategies = SUPPORTED_STRATEGIES

    def run(self, symbol: str, bars: list[Bar], config: BacktestConfig | None = None, name: str | None = None) -> dict:
        cfg = config or BacktestConfig()
        cfg = self._normalize_config(cfg)
        clean = sorted(
            [b for b in bars if _num(b.close) > 0 and _num(b.open) > 0],
            key=lambda b: b.ts,
        )
        if len(clean) < 35:
            raise ValueError("回测至少需要35根有效日K线")

        closes = [_num(b.close) for b in clean]
        highs = [_num(b.high, _num(b.close)) for b in clean]
        lows = [_num(b.low, _num(b.close)) for b in clean]
        volumes = [_num(b.volume) for b in clean]
        amounts = [_num(b.amount) for b in clean]
        macd_hist = _macd_hist_series(closes)
        score_series = [
            self._score_snapshot(i, closes, highs, lows, volumes, amounts, macd_hist)
            for i in range(len(clean))
        ]

        cash = cfg.initial_cash
        shares = 0
        entry_price = 0.0
        entry_date = ""
        entry_reason = ""
        entry_signal_date = ""
        entry_signal_score = None
        entry_fee = 0.0
        entry_cash = cash
        peak_price = 0.0
        pending: dict | None = None
        trades: list[dict] = []
        markers: list[dict] = []
        equity_curve: list[dict] = []
        peak_equity = cash
        forced_flat_at_end = False

        for idx, bar in enumerate(clean):
            open_price = _num(bar.open, _num(bar.close))
            if pending:
                if pending["side"] == "buy" and shares <= 0:
                    buy_price = open_price * (1 + cfg.slippage_rate)
                    budget = cash * cfg.position_pct
                    lot = max(1, int(cfg.lot_size or 1))
                    qty = int(budget / (buy_price * (1 + cfg.fee_rate)) // lot) * lot
                    if qty > 0:
                        value = qty * buy_price
                        fee = value * cfg.fee_rate
                        if value + fee <= cash + 1e-6:
                            cash -= value + fee
                            shares = qty
                            entry_price = buy_price
                            entry_date = bar.ts.date().isoformat()
                            entry_reason = pending.get("reason", "signal")
                            entry_signal_date = pending.get("signal_date", "")
                            entry_signal_score = pending.get("score")
                            entry_fee = fee
                            entry_cash = cash + value + fee
                            peak_price = _num(bar.high, buy_price)
                            markers.append(
                                {
                                    "date": entry_date,
                                    "side": "buy",
                                    "price": round(buy_price, 4),
                                    "reason": entry_reason,
                                    "signal_date": entry_signal_date,
                                    "score": entry_signal_score,
                                }
                            )
                elif pending["side"] == "sell" and shares > 0:
                    sell_price = open_price * (1 - cfg.slippage_rate)
                    trade = self._close_trade(
                        bar,
                        sell_price,
                        shares,
                        cash,
                        entry_price,
                        entry_date,
                        entry_reason,
                        pending.get("reason", "signal"),
                        entry_cash,
                        entry_fee,
                        cfg.fee_rate,
                        entry_signal_date=entry_signal_date,
                        entry_signal_score=entry_signal_score,
                        exit_signal_date=pending.get("signal_date", ""),
                        exit_signal_score=pending.get("score"),
                    )
                    cash = trade.pop("_cash_after")
                    trades.append(trade)
                    markers.append(
                        {
                            "date": trade["exit_date"],
                            "side": "sell",
                            "price": trade["exit_price"],
                            "reason": trade["exit_reason"],
                            "signal_date": trade.get("exit_signal_date"),
                            "score": trade.get("exit_signal_score"),
                        }
                    )
                    shares = 0
                    entry_price = 0.0
                    entry_date = ""
                    entry_reason = ""
                    entry_signal_date = ""
                    entry_signal_score = None
                    entry_fee = 0.0
                    peak_price = 0.0
                pending = None

            close_price = _num(bar.close)
            if shares > 0:
                peak_price = max(peak_price, _num(bar.high, close_price), close_price)
            equity = cash + shares * close_price
            peak_equity = max(peak_equity, equity)
            drawdown = (equity / peak_equity - 1) if peak_equity > 0 else 0.0
            equity_curve.append(
                {
                    "date": bar.ts.date().isoformat(),
                    "equity": round(equity, 2),
                    "cash": round(cash, 2),
                    "position_value": round(shares * close_price, 2),
                    "close": round(close_price, 4),
                    "shares": shares,
                    "score": score_series[idx].get("score"),
                    "drawdown_pct": _pct(drawdown),
                }
            )

            if idx >= len(clean) - 1:
                continue
            signal = self._signal(cfg.strategy, idx, closes, highs, lows, volumes, macd_hist, score_series, shares > 0, entry_price, peak_price, cfg)
            if signal:
                signal["signal_date"] = bar.ts.date().isoformat()
                signal["score"] = score_series[idx].get("score")
                pending = signal

        if shares > 0:
            forced_flat_at_end = True
            last_bar = clean[-1]
            sell_price = _num(last_bar.close) * (1 - cfg.slippage_rate)
            trade = self._close_trade(
                last_bar,
                sell_price,
                shares,
                cash,
                entry_price,
                entry_date,
                entry_reason,
                "期末平仓",
                entry_cash,
                entry_fee,
                cfg.fee_rate,
                entry_signal_date=entry_signal_date,
                entry_signal_score=entry_signal_score,
                exit_signal_date=last_bar.ts.date().isoformat(),
                exit_signal_score=score_series[-1].get("score"),
            )
            cash = trade.pop("_cash_after")
            trades.append(trade)
            markers.append(
                {
                    "date": trade["exit_date"],
                    "side": "sell",
                    "price": trade["exit_price"],
                    "reason": trade["exit_reason"],
                    "signal_date": trade.get("exit_signal_date"),
                    "score": trade.get("exit_signal_score"),
                }
            )
            final_close = _num(last_bar.close)
            equity_curve[-1].update({"equity": round(cash, 2), "cash": round(cash, 2), "position_value": 0.0, "shares": 0})
            equity_curve[-1]["close"] = round(final_close, 4)

        final_equity = float(equity_curve[-1]["equity"]) if equity_curve else cash
        total_return = final_equity / cfg.initial_cash - 1 if cfg.initial_cash > 0 else 0.0
        first_open = _num(clean[0].open, _num(clean[0].close))
        last_close = _num(clean[-1].close)
        buy_hold_return = last_close / first_open - 1 if first_open > 0 else 0.0
        day_span = max(1, (clean[-1].ts.date() - clean[0].ts.date()).days)
        annualized = (final_equity / cfg.initial_cash) ** (365 / day_span) - 1 if cfg.initial_cash > 0 and final_equity > 0 else 0.0
        daily_returns = self._daily_returns(equity_curve)
        wins = [t for t in trades if _num(t.get("pnl")) > 0]
        trade_events = self._trade_events(trades)
        anomaly_markers = self._anomaly_markers(clean, score_series)
        total_return_pct = _pct(total_return)
        buy_hold_return_pct = _pct(buy_hold_return)
        turnover_value = sum(_num(t.get("entry_price")) * _num(t.get("shares")) + _num(t.get("exit_price")) * _num(t.get("shares")) for t in trades)
        total_entry_fee = sum(_num(t.get("entry_fee")) for t in trades)
        total_exit_fee = sum(_num(t.get("exit_fee")) for t in trades)
        slippage_cost_est = turnover_value * cfg.slippage_rate
        total_cost = total_entry_fee + total_exit_fee + slippage_cost_est
        final_position = equity_curve[-1] if equity_curve else {}
        entry_value_sum = sum(_num(t.get("entry_value")) for t in trades)
        entry_cost_sum = sum(_num(t.get("entry_cost")) for t in trades)
        entry_shares_sum = sum(_num(t.get("buy_shares"), _num(t.get("shares"))) for t in trades)
        avg_entry_price = entry_value_sum / entry_shares_sum if entry_shares_sum > 0 else 0.0
        avg_cost_basis = entry_cost_sum / entry_shares_sum if entry_shares_sum > 0 else 0.0
        max_position_shares = max([int(_num(x.get("shares"), 0)) for x in equity_curve] or [0])
        period = {
            "start": clean[0].ts.date().isoformat(),
            "end": clean[-1].ts.date().isoformat(),
            "bars": len(clean),
            "calendar_days": day_span,
        }
        cost_summary = {
            "turnover": round(turnover_value, 2),
            "entry_fee": round(total_entry_fee, 2),
            "exit_fee": round(total_exit_fee, 2),
            "commission": round(total_entry_fee + total_exit_fee, 2),
            "slippage_cost_est": round(slippage_cost_est, 2),
            "total_cost": round(total_cost, 2),
            "fee_rate": cfg.fee_rate,
            "slippage_rate": cfg.slippage_rate,
            "avg_entry_price": round(avg_entry_price, 4),
            "avg_cost_basis": round(avg_cost_basis, 4),
            "total_buy_shares": int(entry_shares_sum),
            "max_position_shares": int(max_position_shares),
        }
        position_summary = {
            "shares": int(_num(final_position.get("shares"), 0)),
            "cash": round(_num(final_position.get("cash"), final_equity), 2),
            "position_value": round(_num(final_position.get("position_value"), 0.0), 2),
            "last_close": round(last_close, 4),
            "max_shares": int(max_position_shares),
            "avg_entry_price": round(avg_entry_price, 4),
            "avg_cost_basis": round(avg_cost_basis, 4),
            "forced_flat_at_end": forced_flat_at_end,
            "note": "期末仍持仓时已按最后收盘价模拟平仓，便于统计闭合交易收益。" if forced_flat_at_end else "期末无持仓或已由策略信号卖出。",
        }

        return {
            "symbol": symbol,
            "name": name or symbol,
            "strategy": cfg.strategy,
            "strategy_name": self._strategy_name(cfg.strategy),
            "strategy_combo": list(cfg.strategy_combo),
            "strategy_combo_names": [self._strategy_name(x) for x in cfg.strategy_combo],
            "combo_rules": {
                "buy": cfg.combo_buy_rule,
                "sell": cfg.combo_sell_rule,
            },
            "initial_cash": round(cfg.initial_cash, 2),
            "final_equity": round(final_equity, 2),
            "total_return_pct": total_return_pct,
            "buy_hold_return_pct": buy_hold_return_pct,
            "excess_return_pct": round(total_return_pct - buy_hold_return_pct, 2),
            "annualized_return_pct": _pct(annualized),
            "max_drawdown_pct": self._max_drawdown_pct(equity_curve),
            "sharpe": self._sharpe(daily_returns),
            "win_rate_pct": round(len(wins) / len(trades) * 100, 2) if trades else 0.0,
            "trade_count": len(trades),
            "trade_event_count": len(trade_events),
            "trades": trades,
            "trade_events": trade_events,
            "markers": markers,
            "anomaly_markers": anomaly_markers,
            "kline": self._kline_payload(clean, score_series, markers, anomaly_markers),
            "equity_curve": equity_curve,
            "score_series": score_series,
            "score_formula": SCORE_FORMULA,
            "params": asdict(cfg),
            "params_cn": self._params_cn(cfg),
            "api_labels": self._api_labels(),
            "period": period,
            "cost_summary": cost_summary,
            "position_summary": position_summary,
            "data_quality": {
                "bars": len(clean),
                "kline_bars": len(clean),
                "markers": len(markers),
                "anomaly_markers": len(anomaly_markers),
                "start": clean[0].ts.date().isoformat(),
                "end": clean[-1].ts.date().isoformat(),
            },
            "assumptions": [
                "信号使用当日收盘数据计算，下一交易日开盘成交，避免收盘后才知道的信号当日成交。",
                "默认计入手续费和滑点，按整手交易；暂不模拟涨跌停无法成交、盘口深度、停牌和分红税。",
                "评分范围为0-100分：趋势34%、动量25%、量能19%、位置结构22%，再按风险扣分45%折减。",
                "组合策略判断会把多个子策略的买入/卖出信号合并，买入按命中数量确认，卖出默认任一策略转弱即退出。",
                "日评分驱动只使用历史K线可见数据回放，不使用未来数据；实盘还需要人工复核信息面和大盘环境。",
                "回测结果用于研究策略口径，不等于实盘收益或买卖建议。",
            ],
        }

    def _normalize_config(self, cfg: BacktestConfig) -> BacktestConfig:
        strategy = str(cfg.strategy or "ma_cross")
        if strategy not in {x["key"] for x in self.strategies}:
            strategy = "ma_cross"
        valid = {x["key"] for x in self.strategies if x["key"] != "combo_signal"}
        raw_combo = cfg.strategy_combo
        if isinstance(raw_combo, str):
            combo = tuple(x.strip() for x in raw_combo.split(",") if x.strip() in valid)
        else:
            combo = tuple(str(x).strip() for x in (raw_combo or ()) if str(x).strip() in valid)
        if strategy == "combo_signal" and not combo:
            combo = ("score_driven", "ma_cross", "macd_momentum", "breakout")
        buy_rule = str(cfg.combo_buy_rule or "at_least_2")
        if buy_rule not in {"any", "at_least_2", "at_least_3", "all"}:
            buy_rule = "at_least_2"
        sell_rule = str(cfg.combo_sell_rule or "any")
        if sell_rule not in {"any", "all"}:
            sell_rule = "any"
        return BacktestConfig(
            strategy=strategy,
            strategy_combo=combo,
            combo_buy_rule=buy_rule,
            combo_sell_rule=sell_rule,
            initial_cash=max(1_000.0, _num(cfg.initial_cash, 100_000.0)),
            fee_rate=max(0.0, min(0.02, _num(cfg.fee_rate, 0.0003))),
            slippage_rate=max(0.0, min(0.02, _num(cfg.slippage_rate, 0.0005))),
            position_pct=max(0.05, min(1.0, _num(cfg.position_pct, 1.0))),
            stop_loss_pct=max(0.0, min(50.0, _num(cfg.stop_loss_pct, 8.0))),
            take_profit_pct=max(0.0, min(200.0, _num(cfg.take_profit_pct, 0.0))),
            buy_score=max(0.0, min(100.0, _num(cfg.buy_score, 62.0))),
            sell_score=max(0.0, min(100.0, _num(cfg.sell_score, 48.0))),
            lot_size=max(1, int(_num(cfg.lot_size, 100))),
        )

    def _score_snapshot(
        self,
        idx: int,
        closes: list[float],
        highs: list[float],
        lows: list[float],
        volumes: list[float],
        amounts: list[float],
        macd_hist: list[float],
    ) -> dict:
        close = closes[idx]
        ma5 = _ma_at(closes, idx, 5)
        ma10 = _ma_at(closes, idx, 10)
        ma20 = _ma_at(closes, idx, 20)
        ma60 = _ma_at(closes, idx, 60)
        ma120 = _ma_at(closes, idx, 120)
        rsi14 = _rsi_at(closes, idx, 14)
        boll = _boll_at(closes, idx, 20)
        pos60 = _position_at(closes, idx, 60)
        pos120 = _position_at(closes, idx, 120)
        ret1 = _ret_pct(closes, idx, 1)
        ret5 = _ret_pct(closes, idx, 5)
        ret20 = _ret_pct(closes, idx, 20)
        vol_ma20 = _ma_at(volumes, idx, 20)
        amount_ma20 = _ma_at(amounts, idx, 20)
        volume_ratio = volumes[idx] / vol_ma20 if vol_ma20 and vol_ma20 > 0 else None
        amount_ratio = amounts[idx] / amount_ma20 if amount_ma20 and amount_ma20 > 0 else None
        hist = macd_hist[idx] if idx < len(macd_hist) else 0.0
        hist_prev = macd_hist[idx - 1] if idx > 0 and idx - 1 < len(macd_hist) else 0.0
        high120 = max(highs[max(0, idx - 119) : idx + 1])
        drawdown120 = (close / high120 - 1) * 100 if high120 else 0.0

        trend = 50.0
        if ma20:
            trend += _clamp((close / ma20 - 1) * 100 * 2.0, -16, 16)
        if ma60:
            trend += _clamp((close / ma60 - 1) * 100 * 1.2, -12, 12)
        if ma5 and ma20:
            trend += 8 if ma5 > ma20 else -7
        if ma20 and idx >= 25:
            ma20_prev = _ma_at(closes, idx - 5, 20)
            if ma20_prev:
                trend += 7 if ma20 > ma20_prev else -6
        if ma120:
            trend += 5 if close > ma120 else -5
        trend_score = _clamp(trend)

        momentum = 50.0
        momentum += _clamp(ret5 * 2.2, -14, 14)
        momentum += _clamp(ret20 * 0.8, -12, 12)
        if rsi14 is not None:
            if 45 <= rsi14 <= 68:
                momentum += 8
            elif rsi14 < 30:
                momentum -= 6
            elif rsi14 > 78:
                momentum -= 10
        momentum += 8 if hist > 0 and hist >= hist_prev else -5 if hist < 0 and hist < hist_prev else 0
        momentum_score = _clamp(momentum)

        volume = 50.0
        if volume_ratio is not None:
            if 1.1 <= volume_ratio <= 2.5 and ret1 >= -1.0:
                volume += 12
            elif volume_ratio > 3.5 and ret1 < 0:
                volume -= 12
            elif volume_ratio < 0.6:
                volume -= 5
        if amount_ratio is not None and amount_ratio >= 1.1 and ret1 >= 0:
            volume += 6
        volume_score = _clamp(volume)

        structure = 50.0
        if pos60 is not None:
            if 25 <= pos60 <= 75:
                structure += 8
            elif pos60 > 90:
                structure -= 8
            elif pos60 < 15 and ret5 > 0:
                structure += 4
        if boll.get("mid") and boll.get("upper") and boll.get("lower"):
            mid = float(boll["mid"])
            upper = float(boll["upper"])
            lower = float(boll["lower"])
            if lower < close < upper:
                structure += 4
            if close > upper * 1.03:
                structure -= 10
            if close > mid and ret5 > 0:
                structure += 5
        structure_score = _clamp(structure)

        risk = 0.0
        if pos120 is not None and pos120 > 88:
            risk += 10
        if rsi14 is not None and rsi14 > 78:
            risk += 10
        if volume_ratio is not None and volume_ratio > 3.5 and ret1 < 0:
            risk += 12
        if drawdown120 < -35:
            risk += 6
        if ma20 and close < ma20:
            risk += 6
        risk_penalty = _clamp(risk, 0, 45)

        score = _clamp(
            trend_score * 0.34
            + momentum_score * 0.25
            + volume_score * 0.19
            + structure_score * 0.22
            - risk_penalty * 0.45,
            0,
            100,
        )
        return {
            "date": "",  # filled in _kline_payload for chart alignment
            "score": round(score, 2),
            "trend_score": round(trend_score, 2),
            "momentum_score": round(momentum_score, 2),
            "volume_score": round(volume_score, 2),
            "structure_score": round(structure_score, 2),
            "risk_penalty": round(risk_penalty, 2),
            "ma5": round(ma5, 4) if ma5 is not None else None,
            "ma10": round(ma10, 4) if ma10 is not None else None,
            "ma20": round(ma20, 4) if ma20 is not None else None,
            "ma60": round(ma60, 4) if ma60 is not None else None,
            "ma120": round(ma120, 4) if ma120 is not None else None,
            "rsi14": round(rsi14, 2) if rsi14 is not None else None,
            "macd_hist": round(hist, 4),
            "volume_ratio": round(volume_ratio, 3) if volume_ratio is not None else None,
            "amount_ratio": round(amount_ratio, 3) if amount_ratio is not None else None,
            "pos60": round(pos60, 2) if pos60 is not None else None,
            "pos120": round(pos120, 2) if pos120 is not None else None,
            "drawdown120_pct": round(drawdown120, 2),
        }

    def _anomaly_markers(self, bars: list[Bar], score_series: list[dict]) -> list[dict]:
        out: list[dict] = []
        previous_score: float | None = None
        previous_hist = 0.0
        previous_states = {
            "risk_high": False,
            "rsi_hot": False,
            "below_ma20_weak": False,
            "deep_drawdown": False,
        }
        for idx, bar in enumerate(bars):
            if idx >= len(score_series):
                continue
            snap = score_series[idx]
            date = bar.ts.date().isoformat()
            close = _num(bar.close)
            prev_close = _num(bars[idx - 1].close, close) if idx > 0 else close
            ret1 = (close / prev_close - 1) * 100 if prev_close else 0.0
            risk = _num(snap.get("risk_penalty"))
            rsi14 = snap.get("rsi14")
            volume_ratio = snap.get("volume_ratio")
            drawdown120 = _num(snap.get("drawdown120_pct"))
            score = _num(snap.get("score"), 50)
            hist = _num(snap.get("macd_hist"))
            ma20 = snap.get("ma20")

            day_flags: list[dict] = []
            risk_high = risk >= 30
            rsi_hot = rsi14 is not None and _num(rsi14) >= 78
            below_ma20_weak = ma20 is not None and close < _num(ma20) and score <= 48
            deep_drawdown = drawdown120 <= -35
            if risk_high and not previous_states["risk_high"]:
                day_flags.append({"label": "风险扣分升高", "reason": f"风险扣分 {risk:.1f}", "severity": 3, "type": "risk"})
            if volume_ratio is not None and _num(volume_ratio) >= 2.8 and ret1 < 0:
                day_flags.append({"label": "放量下跌", "reason": f"量比 {_num(volume_ratio):.2f}，日涨跌 {ret1:.2f}%", "severity": 3, "type": "risk"})
            if rsi_hot and not previous_states["rsi_hot"]:
                day_flags.append({"label": "RSI过热", "reason": f"RSI14 {_num(rsi14):.1f}", "severity": 2, "type": "risk"})
            if below_ma20_weak and not previous_states["below_ma20_weak"]:
                day_flags.append({"label": "跌破MA20且评分弱", "reason": f"评分 {score:.1f}，收盘低于MA20", "severity": 2, "type": "risk"})
            if deep_drawdown and not previous_states["deep_drawdown"]:
                day_flags.append({"label": "深回撤", "reason": f"120日高点回撤 {drawdown120:.1f}%", "severity": 2, "type": "watch"})
            if previous_score is not None and previous_score - score >= 10:
                day_flags.append({"label": "评分急降", "reason": f"评分从 {previous_score:.1f} 降至 {score:.1f}", "severity": 2, "type": "risk"})
            if idx > 0 and hist < 0 <= previous_hist and score <= 52:
                day_flags.append({"label": "MACD转弱", "reason": f"MACD柱 {hist:.4f}", "severity": 1, "type": "watch"})

            day_flags = sorted(day_flags, key=lambda x: x["severity"], reverse=True)[:2]
            for flag in day_flags:
                out.append(
                    {
                        "date": date,
                        "price": round(max(_num(bar.high, close), close) * (1.012 + flag["severity"] * 0.002), 4),
                        "close": round(close, 4),
                        "label": flag["label"],
                        "reason": flag["reason"],
                        "severity": flag["severity"],
                        "type": flag["type"],
                        "score": round(score, 2),
                    }
                )
            previous_score = score
            previous_hist = hist
            previous_states["risk_high"] = risk_high
            previous_states["rsi_hot"] = rsi_hot
            previous_states["below_ma20_weak"] = below_ma20_weak
            previous_states["deep_drawdown"] = deep_drawdown
        return out

    def _kline_payload(self, bars: list[Bar], score_series: list[dict], markers: list[dict], anomaly_markers: list[dict]) -> list[dict]:
        markers_by_date: dict[str, list[dict]] = {}
        for marker in markers:
            markers_by_date.setdefault(str(marker.get("date")), []).append(marker)
        anomaly_by_date: dict[str, list[dict]] = {}
        for marker in anomaly_markers:
            anomaly_by_date.setdefault(str(marker.get("date")), []).append(marker)
        out = []
        for idx, bar in enumerate(bars):
            date = bar.ts.date().isoformat()
            snap = dict(score_series[idx] if idx < len(score_series) else {})
            snap["date"] = date
            out.append(
                {
                    "date": date,
                    "open": round(_num(bar.open), 4),
                    "high": round(_num(bar.high), 4),
                    "low": round(_num(bar.low), 4),
                    "close": round(_num(bar.close), 4),
                    "volume": round(_num(bar.volume), 2),
                    "amount": round(_num(bar.amount), 2),
                    "score": snap.get("score"),
                    "ma5": snap.get("ma5"),
                    "ma10": snap.get("ma10"),
                    "ma20": snap.get("ma20"),
                    "ma60": snap.get("ma60"),
                    "ma120": snap.get("ma120"),
                    "rsi14": snap.get("rsi14"),
                    "macd_hist": snap.get("macd_hist"),
                    "volume_ratio": snap.get("volume_ratio"),
                    "amount_ratio": snap.get("amount_ratio"),
                    "pos60": snap.get("pos60"),
                    "pos120": snap.get("pos120"),
                    "drawdown120_pct": snap.get("drawdown120_pct"),
                    "risk_penalty": snap.get("risk_penalty"),
                    "markers": markers_by_date.get(date, []),
                    "anomaly_markers": anomaly_by_date.get(date, []),
                }
            )
        return out

    def _signal(
        self,
        strategy: str,
        idx: int,
        closes: list[float],
        highs: list[float],
        lows: list[float],
        volumes: list[float],
        macd_hist: list[float],
        score_series: list[dict],
        in_position: bool,
        entry_price: float,
        peak_price: float,
        cfg: BacktestConfig,
    ) -> dict | None:
        close = closes[idx]
        if in_position:
            if cfg.stop_loss_pct > 0 and entry_price > 0 and close <= entry_price * (1 - cfg.stop_loss_pct / 100):
                return {"side": "sell", "reason": f"止损{cfg.stop_loss_pct:.1f}%"}
            if cfg.take_profit_pct > 0 and entry_price > 0 and close >= entry_price * (1 + cfg.take_profit_pct / 100):
                return {"side": "sell", "reason": f"止盈{cfg.take_profit_pct:.1f}%"}

        if strategy == "combo_signal":
            return self._combo_signal(idx, closes, highs, lows, volumes, macd_hist, score_series, in_position, peak_price, cfg)
        return self._single_strategy_signal(strategy, idx, closes, highs, lows, volumes, macd_hist, score_series, in_position, peak_price, cfg)

    def _single_strategy_signal(
        self,
        strategy: str,
        idx: int,
        closes: list[float],
        highs: list[float],
        lows: list[float],
        volumes: list[float],
        macd_hist: list[float],
        score_series: list[dict],
        in_position: bool,
        peak_price: float,
        cfg: BacktestConfig,
    ) -> dict | None:
        if strategy == "score_driven":
            return self._score_driven_signal(idx, closes, score_series, in_position, cfg)
        if strategy == "score_reversal":
            return self._score_reversal_signal(idx, closes, score_series, in_position, cfg)
        if strategy == "rsi_rebound":
            return self._rsi_rebound_signal(idx, closes, in_position)
        if strategy == "breakout":
            return self._breakout_signal(idx, closes, highs, volumes, in_position, peak_price, cfg)
        if strategy == "macd_momentum":
            return self._macd_momentum_signal(idx, closes, macd_hist, in_position)
        if strategy == "boll_pullback":
            return self._boll_pullback_signal(idx, closes, lows, in_position)
        if strategy == "trend_pullback":
            return self._trend_pullback_signal(idx, closes, score_series, in_position)
        return self._ma_cross_signal(idx, closes, in_position)

    def _combo_signal(
        self,
        idx: int,
        closes: list[float],
        highs: list[float],
        lows: list[float],
        volumes: list[float],
        macd_hist: list[float],
        score_series: list[dict],
        in_position: bool,
        peak_price: float,
        cfg: BacktestConfig,
    ) -> dict | None:
        combo = tuple(x for x in cfg.strategy_combo if x and x != "combo_signal")
        if not combo:
            combo = ("score_driven", "ma_cross", "macd_momentum", "breakout")
        hits: list[tuple[str, dict]] = []
        for key in combo:
            signal = self._single_strategy_signal(key, idx, closes, highs, lows, volumes, macd_hist, score_series, in_position, peak_price, cfg)
            if signal and signal.get("side") == ("sell" if in_position else "buy"):
                hits.append((key, signal))
        if not hits:
            return None
        names = [self._strategy_name(key) for key, _ in hits]
        if in_position:
            required = len(combo) if cfg.combo_sell_rule == "all" else 1
            if len(hits) >= required:
                reasons = "；".join(str(x.get("reason") or "") for _, x in hits[:3])
                return {"side": "sell", "reason": f"组合策略卖出：{','.join(names)} 命中；{reasons}"}
            return None
        if cfg.combo_buy_rule == "all":
            required = len(combo)
        elif cfg.combo_buy_rule == "at_least_3":
            required = min(3, len(combo))
        elif cfg.combo_buy_rule == "any":
            required = 1
        else:
            required = min(2, len(combo))
        snap = score_series[idx]
        risk = _num(snap.get("risk_penalty"), 0)
        if len(hits) >= required and risk <= 38:
            reasons = "；".join(str(x.get("reason") or "") for _, x in hits[:3])
            return {"side": "buy", "reason": f"组合策略买入：{','.join(names)} 命中，满足{required}/{len(combo)}项；{reasons}"}
        return None

    def _score_driven_signal(self, idx: int, closes: list[float], score_series: list[dict], in_position: bool, cfg: BacktestConfig) -> dict | None:
        snap = score_series[idx]
        score = _num(snap.get("score"), 50)
        risk = _num(snap.get("risk_penalty"), 0)
        trend = _num(snap.get("trend_score"), 50)
        if not in_position and score >= cfg.buy_score and trend >= 52 and risk <= 34:
            return {"side": "buy", "reason": f"日评分{score:.1f}达到买入阈值{cfg.buy_score:.1f}"}
        if in_position and (score <= cfg.sell_score or risk >= 42):
            return {"side": "sell", "reason": f"日评分{score:.1f}低于卖出阈值或风险升高"}
        return None

    def _score_reversal_signal(self, idx: int, closes: list[float], score_series: list[dict], in_position: bool, cfg: BacktestConfig) -> dict | None:
        if idx < 2:
            return None
        score = _num(score_series[idx].get("score"), 50)
        prev = _num(score_series[idx - 1].get("score"), 50)
        pos120 = score_series[idx].get("pos120")
        ma20 = _ma_at(closes, idx, 20)
        if not in_position and prev < cfg.buy_score <= score and (pos120 is None or _num(pos120, 50) <= 75):
            return {"side": "buy", "reason": f"评分拐点上穿{cfg.buy_score:.1f}，位置未明显追高"}
        if in_position and (score < cfg.sell_score or (ma20 and closes[idx] < ma20)):
            return {"side": "sell", "reason": "评分转弱或跌破MA20"}
        return None

    def _ma_cross_signal(self, idx: int, closes: list[float], in_position: bool) -> dict | None:
        ma5 = _ma_at(closes, idx, 5)
        ma20 = _ma_at(closes, idx, 20)
        if ma5 is None or ma20 is None:
            return None
        close = closes[idx]
        if not in_position and close > ma20 and ma5 > ma20:
            return {"side": "buy", "reason": "收盘站上MA20且MA5强于MA20"}
        if in_position and (close < ma20 or ma5 < ma20):
            return {"side": "sell", "reason": "跌破MA20或MA5走弱"}
        return None

    def _rsi_rebound_signal(self, idx: int, closes: list[float], in_position: bool) -> dict | None:
        rsi14 = _rsi_at(closes, idx, 14)
        ma5 = _ma_at(closes, idx, 5)
        ma20 = _ma_at(closes, idx, 20)
        if rsi14 is None or ma5 is None or ma20 is None:
            return None
        close = closes[idx]
        prev = closes[idx - 1] if idx > 0 else close
        if not in_position and rsi14 <= 35 and close > prev and close >= ma5:
            return {"side": "buy", "reason": f"RSI14={rsi14:.1f}低位修复"}
        if in_position and (rsi14 >= 65 or close < ma20):
            return {"side": "sell", "reason": f"RSI14={rsi14:.1f}过热或跌回MA20"}
        return None

    def _breakout_signal(
        self,
        idx: int,
        closes: list[float],
        highs: list[float],
        volumes: list[float],
        in_position: bool,
        peak_price: float,
        cfg: BacktestConfig,
    ) -> dict | None:
        if idx < 21:
            return None
        close = closes[idx]
        prev_high = max(highs[idx - 20 : idx])
        vol_ma20 = mean(volumes[idx - 20 : idx]) if idx >= 20 else 0.0
        ma10 = _ma_at(closes, idx, 10)
        if not in_position and close > prev_high and vol_ma20 > 0 and volumes[idx] >= vol_ma20 * 1.2:
            return {"side": "buy", "reason": "突破前20日高点且成交量放大"}
        trail = peak_price * (1 - cfg.stop_loss_pct / 100) if peak_price > 0 and cfg.stop_loss_pct > 0 else 0.0
        if in_position and ((ma10 is not None and close < ma10) or (trail > 0 and close < trail)):
            return {"side": "sell", "reason": "跌破MA10或突破回撤止损"}
        return None

    def _macd_momentum_signal(self, idx: int, closes: list[float], macd_hist: list[float], in_position: bool) -> dict | None:
        if idx < 35:
            return None
        ma20 = _ma_at(closes, idx, 20)
        hist = macd_hist[idx] if idx < len(macd_hist) else 0.0
        prev_hist = macd_hist[idx - 1] if idx - 1 < len(macd_hist) else 0.0
        if not in_position and ma20 and closes[idx] > ma20 and hist > 0 and prev_hist <= 0:
            return {"side": "buy", "reason": "MACD柱翻正且价格站上MA20"}
        if in_position and (hist < 0 or (ma20 and closes[idx] < ma20)):
            return {"side": "sell", "reason": "MACD柱转弱或跌回MA20"}
        return None

    def _boll_pullback_signal(self, idx: int, closes: list[float], lows: list[float], in_position: bool) -> dict | None:
        boll = _boll_at(closes, idx, 20)
        mid = boll.get("mid")
        upper = boll.get("upper")
        lower = boll.get("lower")
        rsi14 = _rsi_at(closes, idx, 14)
        if mid is None or upper is None or lower is None or rsi14 is None:
            return None
        close = closes[idx]
        prev = closes[idx - 1] if idx > 0 else close
        touched_lower = min(lows[max(0, idx - 3) : idx + 1]) <= lower * 1.02
        if not in_position and touched_lower and close > prev and close > lower and rsi14 < 55:
            return {"side": "buy", "reason": "BOLL下轨附近回踩后价格修复"}
        if in_position and (close >= upper or close < mid):
            return {"side": "sell", "reason": "触及BOLL上轨或跌破中轨"}
        return None

    def _trend_pullback_signal(self, idx: int, closes: list[float], score_series: list[dict], in_position: bool) -> dict | None:
        if idx < 65:
            return None
        ma20 = _ma_at(closes, idx, 20)
        ma60 = _ma_at(closes, idx, 60)
        ma60_prev = _ma_at(closes[: idx - 4], len(closes[: idx - 4]) - 1, 60) if idx >= 65 else None
        score = _num(score_series[idx].get("score"), 50)
        if not in_position and ma20 and ma60 and ma60_prev and ma60 > ma60_prev and closes[idx] >= ma20 and closes[idx - 1] < ma20 * 1.015 and score >= 56:
            return {"side": "buy", "reason": "MA60向上，回踩MA20后评分修复"}
        if in_position and (ma20 and closes[idx] < ma20 or score < 48):
            return {"side": "sell", "reason": "跌破MA20或评分转弱"}
        return None

    def _close_trade(
        self,
        bar: Bar,
        sell_price: float,
        shares: int,
        cash: float,
        entry_price: float,
        entry_date: str,
        entry_reason: str,
        exit_reason: str,
        entry_cash: float,
        entry_fee: float,
        fee_rate: float,
        entry_signal_date: str = "",
        entry_signal_score=None,
        exit_signal_date: str = "",
        exit_signal_score=None,
    ) -> dict:
        value = shares * sell_price
        exit_fee = value * fee_rate
        cash_after = cash + value - exit_fee
        cost = shares * entry_price
        entry_cost = cost + entry_fee
        exit_proceeds = value - exit_fee
        pnl = exit_proceeds - entry_cost
        hold_days = 0
        try:
            hold_days = (bar.ts.date() - datetime.fromisoformat(entry_date).date()).days
        except Exception:
            hold_days = 0
        return {
            "entry_date": entry_date,
            "exit_date": bar.ts.date().isoformat(),
            "entry_price": round(entry_price, 4),
            "exit_price": round(sell_price, 4),
            "shares": shares,
            "buy_shares": shares,
            "sell_shares": shares,
            "entry_value": round(cost, 2),
            "entry_cost": round(entry_cost, 2),
            "exit_value": round(value, 2),
            "exit_proceeds": round(exit_proceeds, 2),
            "cost_basis": round(entry_cost / shares, 4) if shares > 0 else 0.0,
            "cash_before_entry": round(entry_cash, 2),
            "cash_after_exit": round(cash_after, 2),
            "holding_days": hold_days,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl / entry_cost * 100, 2) if entry_cost > 0 else 0.0,
            "return_on_equity_pct": round((cash_after / entry_cash - 1) * 100, 2) if entry_cash > 0 else 0.0,
            "entry_fee": round(entry_fee, 2),
            "exit_fee": round(exit_fee, 2),
            "entry_signal_date": entry_signal_date,
            "entry_signal_score": entry_signal_score,
            "exit_signal_date": exit_signal_date,
            "exit_signal_score": exit_signal_score,
            "entry_reason": entry_reason,
            "exit_reason": exit_reason,
            "_cash_after": cash_after,
        }

    def _trade_events(self, trades: list[dict]) -> list[dict]:
        events: list[dict] = []
        for idx, trade in enumerate(trades, 1):
            shares = int(_num(trade.get("buy_shares"), _num(trade.get("shares"))))
            entry_value = _num(trade.get("entry_value"))
            entry_cost = _num(trade.get("entry_cost"), entry_value + _num(trade.get("entry_fee")))
            entry_fee = _num(trade.get("entry_fee"))
            entry_cash = _num(trade.get("cash_before_entry"))
            exit_value = _num(trade.get("exit_value"))
            exit_proceeds = _num(trade.get("exit_proceeds"), exit_value - _num(trade.get("exit_fee")))
            exit_fee = _num(trade.get("exit_fee"))
            cost_basis = _num(trade.get("cost_basis"))
            buy_cash_after = entry_cash - entry_cost if entry_cash else None
            events.append(
                {
                    "event_id": f"{idx}-B",
                    "trade_index": idx,
                    "date": trade.get("entry_date"),
                    "side": "buy",
                    "action": "买入",
                    "price": trade.get("entry_price"),
                    "shares": shares,
                    "amount": round(entry_value, 2),
                    "fee": round(entry_fee, 2),
                    "cash_change": round(-entry_cost, 2),
                    "cash_after": round(buy_cash_after, 2) if buy_cash_after is not None else None,
                    "position_shares": shares,
                    "cost_basis": round(cost_basis, 4),
                    "realized_pnl": 0.0,
                    "realized_pct": 0.0,
                    "reason": trade.get("entry_reason"),
                    "signal_date": trade.get("entry_signal_date"),
                    "score": trade.get("entry_signal_score"),
                    "paired_date": trade.get("exit_date"),
                }
            )
            events.append(
                {
                    "event_id": f"{idx}-S",
                    "trade_index": idx,
                    "date": trade.get("exit_date"),
                    "side": "sell",
                    "action": "卖出",
                    "price": trade.get("exit_price"),
                    "shares": int(_num(trade.get("sell_shares"), shares)),
                    "amount": round(exit_value, 2),
                    "fee": round(exit_fee, 2),
                    "cash_change": round(exit_proceeds, 2),
                    "cash_after": trade.get("cash_after_exit"),
                    "position_shares": 0,
                    "cost_basis": round(cost_basis, 4),
                    "realized_pnl": trade.get("pnl"),
                    "realized_pct": trade.get("pnl_pct"),
                    "reason": trade.get("exit_reason"),
                    "signal_date": trade.get("exit_signal_date"),
                    "score": trade.get("exit_signal_score"),
                    "paired_date": trade.get("entry_date"),
                }
            )
        return events

    def _params_cn(self, cfg: BacktestConfig) -> dict:
        return {
            "策略": self._strategy_name(cfg.strategy),
            "组合策略": "、".join(self._strategy_name(x) for x in cfg.strategy_combo) if cfg.strategy_combo else "未启用",
            "组合买入规则": {"any": "任一命中", "at_least_2": "至少2项命中", "at_least_3": "至少3项命中", "all": "全部命中"}.get(cfg.combo_buy_rule, cfg.combo_buy_rule),
            "组合卖出规则": {"any": "任一转弱卖出", "all": "全部转弱卖出"}.get(cfg.combo_sell_rule, cfg.combo_sell_rule),
            "初始资金": round(cfg.initial_cash, 2),
            "仓位比例": f"{cfg.position_pct * 100:.1f}%",
            "手续费率": f"{cfg.fee_rate * 100:.4f}%",
            "滑点率": f"{cfg.slippage_rate * 100:.4f}%",
            "止损": f"{cfg.stop_loss_pct:.1f}%",
            "止盈": f"{cfg.take_profit_pct:.1f}%" if cfg.take_profit_pct > 0 else "未启用",
            "买入评分阈值": cfg.buy_score,
            "卖出评分阈值": cfg.sell_score,
            "整手股数": cfg.lot_size,
        }

    def _api_labels(self) -> dict:
        return {
            "strategy": "策略",
            "strategy_combo": "组合策略",
            "combo_buy_rule": "组合买入规则",
            "combo_sell_rule": "组合卖出规则",
            "initial_cash": "初始资金",
            "fee_rate": "手续费率",
            "slippage_rate": "滑点率",
            "position_pct": "仓位比例",
            "stop_loss_pct": "止损%",
            "take_profit_pct": "止盈%",
            "buy_score": "买入评分",
            "sell_score": "卖出评分",
            "lot_size": "整手股数",
            "trade_events": "买卖流水",
            "position_summary": "持仓与成本",
            "cost_summary": "成本汇总",
            "period": "回测区间",
        }

    def _daily_returns(self, equity_curve: list[dict]) -> list[float]:
        returns: list[float] = []
        prev = None
        for row in equity_curve:
            equity = _num(row.get("equity"))
            if prev and prev > 0:
                returns.append(equity / prev - 1)
            prev = equity
        return returns

    def _max_drawdown_pct(self, equity_curve: list[dict]) -> float:
        if not equity_curve:
            return 0.0
        peak = 0.0
        worst = 0.0
        for row in equity_curve:
            equity = _num(row.get("equity"))
            peak = max(peak, equity)
            if peak > 0:
                worst = min(worst, equity / peak - 1)
        return _pct(worst)

    def _sharpe(self, daily_returns: list[float]) -> float:
        if len(daily_returns) < 2:
            return 0.0
        sd = pstdev(daily_returns)
        if sd <= 1e-12:
            return 0.0
        return round(mean(daily_returns) / sd * math.sqrt(252), 3)

    def _strategy_name(self, strategy: str) -> str:
        return next((x["name"] for x in self.strategies if x["key"] == strategy), strategy)
