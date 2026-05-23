from __future__ import annotations

from dataclasses import asdict
from typing import Any

from quant_data.indicators import macd, mfi, moving_average, obv_series, rsi, support_resistance, vwap
from quant_data.models import Bar, IntradayPoint, Quote


SUPPORTED_BEHAVIOR_TAGS = [
    "疑似放量诱多",
    "疑似骗量拉升",
    "冲高回落风险",
    "高位放量滞涨",
    "假突破风险",
    "次日洗盘确认",
    "长上影诱多",
    "尾盘急拉诱多",
    "高开低走",
    "高换手不涨",
    "放量不涨",
    "涨停炸板风险",
    "涨停回封失败",
    "缩量洗盘",
    "长下影洗盘",
    "假跌破支撑",
    "回踩均线支撑",
    "高位巨量阴线",
    "量价背离",
    "OBV背离",
    "MFI背离",
    "MACD顶背离",
    "RSI顶背离",
    "跌破MA20",
    "跌破箱体",
    "反抽无量",
    "尾盘砸盘",
    "尾盘抢筹",
    "分时均价线失守",
    "早盘急拉回落",
]

HIGH_RISK_TAGS = {
    "疑似放量诱多",
    "疑似骗量拉升",
    "假突破风险",
    "高位放量滞涨",
    "高换手不涨",
    "高位巨量阴线",
    "跌破MA20",
    "跌破箱体",
}

LEVEL2_CONFIRM_TAGS = {
    "疑似放量诱多",
    "疑似骗量拉升",
    "尾盘急拉诱多",
    "尾盘砸盘",
    "尾盘抢筹",
    "分时均价线失守",
    "早盘急拉回落",
}


class MarketBehaviorEngine:
    """资金行为/K线行为识别。

    只使用公开行情和技术指标做“疑似/风险”级判断。缺少 Level-2、逐笔和账户级数据时，
    不输出确定性“主力对倒/庄家出货”。
    """

    supported_tags = SUPPORTED_BEHAVIOR_TAGS
    high_risk_tags = HIGH_RISK_TAGS

    def analyze(
        self,
        quote: Quote | dict[str, Any] | None,
        bars: list[Bar | dict[str, Any]],
        intraday: list[IntradayPoint | dict[str, Any]] | None = None,
        technical_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = [self._bar_dict(b) for b in bars or []]
        rows = [r for r in rows if self._num(r.get("close")) and self._num(r.get("high")) and self._num(r.get("low"))]
        q = self._quote_dict(quote)
        intraday_rows = [self._point_dict(p) for p in intraday or []]
        if len(rows) < 5:
            return self._empty("样本不足，无法稳定识别市场行为")

        closes = [float(r["close"]) for r in rows]
        highs = [float(r["high"]) for r in rows]
        lows = [float(r["low"]) for r in rows]
        opens = [float(r.get("open") or r["close"]) for r in rows]
        volumes = [float(r.get("volume") or 0.0) for r in rows]
        amounts = [float(r.get("amount") or 0.0) for r in rows]
        latest = rows[-1]
        prev = rows[-2] if len(rows) >= 2 else latest
        close = closes[-1]
        prev_close = closes[-2] if len(closes) >= 2 else close
        open_ = opens[-1]
        high = highs[-1]
        low = lows[-1]
        volume = volumes[-1]
        ma20_volume = moving_average(volumes[:-1], 20) or moving_average(volumes, min(20, len(volumes))) or 0.0
        volume_multiple = volume / ma20_volume if ma20_volume else 0.0
        day_range = max(high - low, 1e-9)
        upper_shadow_ratio = max(high - max(open_, close), 0.0) / day_range
        lower_shadow_ratio = max(min(open_, close) - low, 0.0) / day_range
        close_pos_day = (close - low) / day_range
        change_pct = self._num(q.get("change_pct"))
        if change_pct is None and prev_close:
            change_pct = (close / prev_close - 1) * 100
        turnover = self._num(q.get("turnover"))
        volume_ratio = self._num(q.get("volume_ratio"))
        pos20 = self._position(closes[-20:], close)
        high20_prev = max(highs[-21:-1]) if len(highs) >= 21 else max(highs[:-1] or highs)
        low20_prev = min(lows[-21:-1]) if len(lows) >= 21 else min(lows[:-1] or lows)
        ma20 = moving_average(closes, 20)
        ma10 = moving_average(closes, 10)
        vwap20 = technical_context.get("vwap20") if technical_context else None
        vwap20 = vwap20 if vwap20 is not None else vwap(highs, lows, closes, volumes, 20)
        sr_ctx = technical_context or {}
        sr = support_resistance(highs[:-1] or highs, lows[:-1] or lows, closes[:-1] or closes, 60)
        support = self._num(sr_ctx.get("support") or sr_ctx.get("support60") or sr.get("support"))
        resistance = self._num(sr_ctx.get("resistance") or sr_ctx.get("resistance60") or sr.get("resistance"))

        tags: list[str] = []
        evidence: list[str] = []
        markers: list[dict[str, Any]] = []

        def add(label: str, marker_type: str, price: float | None, ev: list[str], idx: int = -1) -> None:
            if label not in tags:
                tags.append(label)
            evidence.extend(ev)
            row = rows[idx]
            tooltip = f"{label}：{'；'.join(ev[:4])}"
            markers.append({
                "date": str(row.get("ts", ""))[:10] or str(row.get("date", ""))[:10],
                "type": marker_type,
                "label": label,
                "price": round(float(price or row.get("close") or 0.0), 4),
                "tooltip": tooltip,
                "evidence": ev,
            })

        if volume_multiple > 1.8 and upper_shadow_ratio > 0.45 and close_pos_day < 0.45:
            ev = [
                f"上影线占比{upper_shadow_ratio * 100:.0f}%",
                f"成交量为20日均量{volume_multiple:.1f}倍",
                f"收盘位于日内区间{close_pos_day * 100:.0f}%",
            ]
            add("冲高回落风险", "risk", high, ev)
            add("长上影诱多", "risk", high, ev)
            if close >= prev_close:
                add("疑似放量诱多", "risk", high, ev + ["缺少 Level-2，需确认是否存在骗量特征"])

        if pos20 is not None and pos20 > 75 and volume_multiple > 1.8 and abs(change_pct or 0) < 2.5 and high <= high20_prev * 1.01:
            add("高位放量滞涨", "risk", close, [
                f"近20日位置{pos20:.0f}%",
                f"成交量为20日均量{volume_multiple:.1f}倍",
                f"涨跌幅{change_pct or 0:.2f}%",
            ])

        if resistance and high > resistance and close < resistance:
            add("假突破风险", "risk", high, [
                f"盘中高点{high:.2f}突破压力{resistance:.2f}",
                f"收盘{close:.2f}跌回压力位下方",
            ])

        if support and low < support and close > support:
            add("假跌破支撑", "watch", low, [
                f"盘中低点{low:.2f}跌破支撑{support:.2f}",
                f"收盘{close:.2f}收回支撑上方",
            ])

        if turnover is not None and turnover >= 8 and abs(change_pct or 0) < 2.5 and (vwap20 is None or close < float(vwap20) * 1.005):
            add("高换手不涨", "risk", close, [
                f"换手率{turnover:.2f}%",
                f"涨跌幅{change_pct or 0:.2f}%",
                "收盘未有效站稳VWAP" if vwap20 else "VWAP缺失，按涨幅/换手判断",
            ])

        if volume_multiple > 1.8 and abs(change_pct or 0) < 1.5:
            add("放量不涨", "risk", close, [
                f"成交量为20日均量{volume_multiple:.1f}倍",
                f"涨跌幅{change_pct or 0:.2f}%",
            ])

        if volume_ratio is not None and volume_ratio >= 3.0 and close < open_ and close_pos_day < 0.35:
            add("疑似骗量拉升", "risk", high, [
                f"量比{volume_ratio:.2f}",
                f"收盘位置{close_pos_day * 100:.0f}%",
                "缺少 Level-2，需确认是否存在资金对倒/骗量特征",
            ])

        if open_ > prev_close * 1.025 and close < open_ and close_pos_day < 0.45:
            add("高开低走", "risk", open_, [
                f"开盘较前收盘高{(open_ / prev_close - 1) * 100:.2f}%",
                f"收盘低于开盘{(close / open_ - 1) * 100:.2f}%",
            ])

        limit_up_price = self._num(q.get("limit_up"))
        if not limit_up_price and prev_close:
            limit_rate = 0.2 if str(q.get("symbol", "")).startswith(("300", "301", "688", "689")) else 0.1
            limit_up_price = round(prev_close * (1 + limit_rate), 2)
        if limit_up_price and high >= limit_up_price * 0.995 and close < limit_up_price * 0.985:
            add("涨停炸板风险", "risk", high, [f"盘中接近涨停{limit_up_price:.2f}", f"收盘{close:.2f}未封住"])
            if close_pos_day < 0.5:
                add("涨停回封失败", "risk", high, [f"收盘位置{close_pos_day * 100:.0f}%", "涨停回封未确认"])

        if ma20 and close < ma20 and prev_close >= ma20:
            add("跌破MA20", "risk", close, [f"收盘{close:.2f}跌破MA20 {ma20:.2f}"])
        if low20_prev and close < low20_prev:
            add("跌破箱体", "risk", close, [f"收盘{close:.2f}跌破近20日箱体低点{low20_prev:.2f}"])

        if ma20 and low <= ma20 * 1.02 and close >= ma20 and volume < ma20_volume:
            add("缩量洗盘", "positive", low, [f"回踩MA20 {ma20:.2f}", f"成交量低于20日均量{volume_multiple:.1f}倍"])
            add("回踩均线支撑", "positive", low, [f"低点{low:.2f}接近MA20 {ma20:.2f}", "收盘收回均线上方"])
        elif ma10 and low <= ma10 * 1.015 and close >= ma10 and volume < ma20_volume:
            add("回踩均线支撑", "positive", low, [f"低点{low:.2f}接近MA10 {ma10:.2f}", "缩量回踩后收回"])
        if lower_shadow_ratio > 0.45 and close_pos_day > 0.55 and volume <= ma20_volume * 1.25:
            add("长下影洗盘", "positive", low, [f"下影线占比{lower_shadow_ratio * 100:.0f}%", "收盘回到日内中上部"])

        if len(rows) >= 2:
            prev_range = max(float(prev.get("high") or 0) - float(prev.get("low") or 0), 1e-9)
            prev_upper = max(float(prev.get("high") or 0) - max(float(prev.get("open") or 0), float(prev.get("close") or 0)), 0) / prev_range
            prev_vol_ma20 = moving_average(volumes[:-2], 20) or ma20_volume
            prev_vol_multi = float(prev.get("volume") or 0) / prev_vol_ma20 if prev_vol_ma20 else 0
            if prev_upper > 0.45 and prev_vol_multi > 1.8 and open_ < float(prev.get("close") or close) * 0.985 and close < float(prev.get("close") or close):
                add("次日洗盘确认", "watch", close, [
                    f"前日上影线占比{prev_upper * 100:.0f}%",
                    f"前日成交量为20日均量{prev_vol_multi:.1f}倍",
                    "次日低开且跌破前日收盘",
                ])

        if pos20 is not None and pos20 > 80 and volume_multiple > 2.4 and close < open_ and (change_pct or 0) < -2:
            add("高位巨量阴线", "risk", close, [
                f"近20日位置{pos20:.0f}%",
                f"成交量为20日均量{volume_multiple:.1f}倍",
                f"跌幅{change_pct or 0:.2f}%",
            ])

        price_chg20 = (closes[-1] / closes[-20] - 1) * 100 if len(closes) >= 20 and closes[-20] else 0.0
        if len(closes) >= 20 and price_chg20 > 8 and volumes[-1] < moving_average(volumes[-20:], 20) * 0.8:
            add("量价背离", "risk", close, [f"20日涨幅{price_chg20:.1f}%", "最新成交量低于20日均量80%"])
        obv = obv_series(closes, volumes)
        if len(obv) >= 20 and price_chg20 > 8 and obv[-1] < obv[-10]:
            add("OBV背离", "risk", close, [f"20日涨幅{price_chg20:.1f}%", "OBV近10日走弱"])
        mfi14 = mfi(highs, lows, closes, volumes, 14)
        if price_chg20 > 8 and mfi14 is not None and mfi14 < 45:
            add("MFI背离", "risk", close, [f"20日涨幅{price_chg20:.1f}%", f"MFI14仅{mfi14:.1f}"])
        macd_info = macd(closes)
        if len(macd_info.get("hist") or []) >= 10 and price_chg20 > 8 and macd_info["hist"][-1] < macd_info["hist"][-5]:
            add("MACD顶背离", "risk", close, [f"20日涨幅{price_chg20:.1f}%", "MACD柱近5日走弱"])
        rsi14 = rsi(closes, 14)
        if price_chg20 > 8 and rsi14 is not None and rsi14 < 55:
            add("RSI顶背离", "risk", close, [f"20日涨幅{price_chg20:.1f}%", f"RSI14仅{rsi14:.1f}"])

        if len(closes) >= 6:
            rebound = close > closes[-3] and close < closes[-6] and volume < ma20_volume * 0.85
            if rebound:
                add("反抽无量", "watch", close, ["短线反抽未收复5日前价格", "成交量低于20日均量85%"])

        self._intraday_rules(intraday_rows, add)

        tags = [t for t in SUPPORTED_BEHAVIOR_TAGS if t in tags] + [t for t in tags if t not in SUPPORTED_BEHAVIOR_TAGS]
        risk_hits = [t for t in tags if t in HIGH_RISK_TAGS]
        watch_hits = [t for t in tags if t not in HIGH_RISK_TAGS]
        behavior_score = min(45.0, len(risk_hits) * 8.0 + len(watch_hits) * 3.0)
        confidence = "high" if len(tags) >= 4 and len(evidence) >= 8 else "medium" if len(tags) >= 2 else "low"
        need_level2 = any(t in LEVEL2_CONFIRM_TAGS for t in tags)
        risk_label = "高风险" if len(risk_hits) >= 2 or behavior_score >= 18 else "中风险" if risk_hits else "观察"
        if need_level2:
            evidence.append("缺少 Level-2/逐笔/账户级数据，疑似骗量或尾盘异常仅作风险提示")
        return {
            "behavior_tags": tags,
            "behavior_score": round(behavior_score, 2),
            "behavior_confidence": confidence,
            "behavior_evidence": list(dict.fromkeys(evidence))[:30],
            "manipulation_risk_label": risk_label,
            "need_level2_confirm": need_level2,
            "kline_markers": self._dedup_markers(markers),
            "risk_penalty_contribution": round(min(18.0, behavior_score * 0.45), 2),
            "supported_tags": SUPPORTED_BEHAVIOR_TAGS,
        }

    def _intraday_rules(self, points: list[dict[str, Any]], add) -> None:
        if len(points) < 8:
            return
        prices = [self._num(p.get("price")) for p in points]
        prices = [p for p in prices if p is not None]
        if len(prices) < 8:
            return
        avg_prices = [self._num(p.get("avg_price")) for p in points]
        first = prices[0]
        last = prices[-1]
        high = max(prices)
        low = min(prices)
        early_high = max(prices[: max(3, len(prices) // 5)])
        tail = prices[-max(3, len(prices) // 8):]
        tail_change = (tail[-1] / tail[0] - 1) * 100 if tail[0] else 0.0
        day_range = max(high - low, 1e-9)
        if early_high > first * 1.025 and last < early_high * 0.985:
            add("早盘急拉回落", "risk", early_high, [f"早盘最高较开盘上涨{(early_high / first - 1) * 100:.2f}%", "尾段未能维持高位"])
        if tail_change > 1.8 and last < high * 0.995:
            add("尾盘急拉诱多", "risk", last, [f"尾盘涨幅{tail_change:.2f}%", "缺少 Level-2 需确认尾盘资金真实意图"])
        if tail_change < -1.8:
            add("尾盘砸盘", "risk", last, [f"尾盘跌幅{tail_change:.2f}%", "尾盘抛压明显"])
        if tail_change > 1.0 and last >= high - day_range * 0.15:
            add("尾盘抢筹", "watch", last, [f"尾盘涨幅{tail_change:.2f}%", "收盘接近日内高位"])
        valid_avg = [x for x in avg_prices if x is not None]
        if valid_avg and last < valid_avg[-1] * 0.995:
            add("分时均价线失守", "risk", last, [f"最新价低于分时均价线{(last / valid_avg[-1] - 1) * 100:.2f}%"])

    def _empty(self, reason: str) -> dict[str, Any]:
        return {
            "behavior_tags": [],
            "behavior_score": 0.0,
            "behavior_confidence": "low",
            "behavior_evidence": [reason],
            "manipulation_risk_label": "观察",
            "need_level2_confirm": False,
            "kline_markers": [],
            "risk_penalty_contribution": 0.0,
            "supported_tags": SUPPORTED_BEHAVIOR_TAGS,
        }

    def _dedup_markers(self, markers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for m in markers:
            key = (str(m.get("date")), str(m.get("label")))
            if key in seen:
                continue
            if not all(k in m for k in ["date", "type", "label", "price", "tooltip", "evidence"]):
                continue
            seen.add(key)
            out.append(m)
        return out[:40]

    def _position(self, values: list[float], price: float) -> float | None:
        vals = [v for v in values if v and v > 0]
        if not vals:
            return None
        hi = max(vals)
        lo = min(vals)
        if hi <= lo:
            return 50.0
        return (price - lo) / (hi - lo) * 100

    def _num(self, value: Any) -> float | None:
        try:
            if value is None:
                return None
            v = float(value)
            return v if v == v else None
        except Exception:
            return None

    def _bar_dict(self, bar: Bar | dict[str, Any]) -> dict[str, Any]:
        if isinstance(bar, dict):
            return dict(bar)
        data = asdict(bar)
        data["ts"] = getattr(bar.ts, "isoformat", lambda: str(bar.ts))()
        return data

    def _point_dict(self, point: IntradayPoint | dict[str, Any]) -> dict[str, Any]:
        if isinstance(point, dict):
            return dict(point)
        data = asdict(point)
        data["ts"] = getattr(point.ts, "isoformat", lambda: str(point.ts))()
        return data

    def _quote_dict(self, quote: Quote | dict[str, Any] | None) -> dict[str, Any]:
        if quote is None:
            return {}
        if isinstance(quote, dict):
            return dict(quote)
        return asdict(quote)
