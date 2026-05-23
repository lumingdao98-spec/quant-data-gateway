from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Iterable


def safe_float(value, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _series(values: Iterable[float | int | None]) -> list[float]:
    out: list[float] = []
    for v in values:
        x = safe_float(v)
        if x is None:
            continue
        out.append(float(x))
    return out


def moving_average(values: list[float], n: int) -> float | None:
    if n <= 0 or len(values) < n:
        return None
    part = [v for v in values[-n:] if v is not None]
    if len(part) < n:
        return None
    return mean(part)


def rolling_ma(values: list[float], n: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append(mean(values[i + 1 - n : i + 1]))
    return out


def ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def wilder_smooth(values: list[float], period: int) -> list[float]:
    """Wilder smoothing used by ATR/ADX/RSI-like indicators."""
    if not values:
        return []
    if period <= 1:
        return list(values)
    out: list[float] = []
    prev: float | None = None
    for i, v in enumerate(values):
        if i + 1 < period:
            out.append(mean(values[: i + 1]))
        elif i + 1 == period:
            prev = mean(values[:period])
            out.append(prev)
        else:
            assert prev is not None
            prev = (prev * (period - 1) + v) / period
            out.append(prev)
    return out


def macd(values: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, list[float]]:
    if not values:
        return {"dif": [], "dea": [], "hist": []}
    e_fast = ema_series(values, fast)
    e_slow = ema_series(values, slow)
    dif = [a - b for a, b in zip(e_fast, e_slow)]
    dea = ema_series(dif, signal)
    hist = [(d - e) * 2 for d, e in zip(dif, dea)]
    return {"dif": dif, "dea": dea, "hist": hist}


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(len(values) - period, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def bollinger(values: list[float], period: int = 20, width: float = 2.0) -> dict[str, float | None]:
    if len(values) < period:
        return {"mid": None, "upper": None, "lower": None, "width_pct": None, "position": None}
    part = values[-period:]
    mid = mean(part)
    sd = pstdev(part) if len(part) > 1 else 0.0
    upper = mid + width * sd
    lower = mid - width * sd
    width_pct = (upper - lower) / mid * 100 if mid else None
    last = values[-1]
    position = (last - lower) / (upper - lower) * 100 if upper and lower and upper > lower else 50.0
    return {"mid": mid, "upper": upper, "lower": lower, "width_pct": width_pct, "position": position}


def true_range_series(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    n = min(len(highs), len(lows), len(closes))
    if n <= 0:
        return []
    out: list[float] = []
    for i in range(n):
        h, l = highs[i], lows[i]
        if i == 0:
            out.append(max(0.0, h - l))
        else:
            pc = closes[i - 1]
            out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def atr_series(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
    trs = true_range_series(highs, lows, closes)
    if len(trs) < 1:
        return []
    return wilder_smooth(trs, period)


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    values = atr_series(highs, lows, closes, period)
    return values[-1] if len(values) >= period else None


def kdj(highs: list[float], lows: list[float], closes: list[float], period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> dict[str, list[float]]:
    n = min(len(highs), len(lows), len(closes))
    if n <= 0:
        return {"k": [], "d": [], "j": []}
    k_values: list[float] = []
    d_values: list[float] = []
    j_values: list[float] = []
    k_prev = 50.0
    d_prev = 50.0
    for i in range(n):
        start = max(0, i + 1 - period)
        hh = max(highs[start : i + 1])
        ll = min(lows[start : i + 1])
        rsv = 50.0 if hh <= ll else (closes[i] - ll) / (hh - ll) * 100
        k_now = (k_prev * (k_smooth - 1) + rsv) / k_smooth
        d_now = (d_prev * (d_smooth - 1) + k_now) / d_smooth
        j_now = 3 * k_now - 2 * d_now
        k_values.append(k_now)
        d_values.append(d_now)
        j_values.append(j_now)
        k_prev, d_prev = k_now, d_now
    return {"k": k_values, "d": d_values, "j": j_values}


def williams_r(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    n = min(len(highs), len(lows), len(closes))
    if n < period:
        return None
    hh = max(highs[n - period : n])
    ll = min(lows[n - period : n])
    if hh <= ll:
        return -50.0
    return -100 * (hh - closes[n - 1]) / (hh - ll)


def cci(highs: list[float], lows: list[float], closes: list[float], period: int = 20) -> float | None:
    n = min(len(highs), len(lows), len(closes))
    if n < period:
        return None
    tps = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n - period, n)]
    ma = mean(tps)
    md = mean(abs(x - ma) for x in tps)
    if md == 0:
        return 0.0
    return (tps[-1] - ma) / (0.015 * md)


def roc(values: list[float], period: int = 12) -> float | None:
    if len(values) <= period or not values[-period - 1]:
        return None
    return (values[-1] / values[-period - 1] - 1) * 100


def momentum(values: list[float], period: int = 10) -> float | None:
    if len(values) <= period:
        return None
    return values[-1] - values[-period - 1]


def obv_series(closes: list[float], volumes: list[float]) -> list[float]:
    n = min(len(closes), len(volumes))
    if n <= 0:
        return []
    out = [0.0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            out.append(out[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            out.append(out[-1] - volumes[i])
        else:
            out.append(out[-1])
    return out


def slope_pct(values: list[float], period: int = 10) -> float | None:
    if len(values) <= period:
        return None
    base = abs(values[-period - 1])
    if base < 1e-9:
        # OBV可能从0开始，用近段绝对均值兜底。
        base = mean(abs(x) for x in values[-period - 1 :]) or 1.0
    return (values[-1] - values[-period - 1]) / base * 100


def mfi(highs: list[float], lows: list[float], closes: list[float], volumes: list[float], period: int = 14) -> float | None:
    n = min(len(highs), len(lows), len(closes), len(volumes))
    if n <= period:
        return None
    pos = 0.0
    neg = 0.0
    prev_tp = (highs[n - period - 1] + lows[n - period - 1] + closes[n - period - 1]) / 3
    for i in range(n - period, n):
        tp = (highs[i] + lows[i] + closes[i]) / 3
        raw = tp * volumes[i]
        if tp > prev_tp:
            pos += raw
        elif tp < prev_tp:
            neg += raw
        prev_tp = tp
    if neg == 0:
        return 100.0 if pos > 0 else 50.0
    mr = pos / neg
    return 100 - 100 / (1 + mr)


def vwap(highs: list[float], lows: list[float], closes: list[float], volumes: list[float], period: int = 20) -> float | None:
    n = min(len(highs), len(lows), len(closes), len(volumes))
    if n < period:
        return None
    num = 0.0
    den = 0.0
    for i in range(n - period, n):
        tp = (highs[i] + lows[i] + closes[i]) / 3
        vol = max(0.0, volumes[i])
        num += tp * vol
        den += vol
    if den <= 0:
        return None
    return num / den


def adx(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> dict[str, float | None]:
    n = min(len(highs), len(lows), len(closes))
    if n <= period + 1:
        return {"adx": None, "plus_di": None, "minus_di": None}
    plus_dm = [0.0]
    minus_dm = [0.0]
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
    tr = true_range_series(highs, lows, closes)
    atr_sm = wilder_smooth(tr, period)
    plus_sm = wilder_smooth(plus_dm, period)
    minus_sm = wilder_smooth(minus_dm, period)
    plus_di: list[float] = []
    minus_di: list[float] = []
    dx: list[float] = []
    for a, p, m in zip(atr_sm, plus_sm, minus_sm):
        if a <= 1e-12:
            plus_di.append(0.0); minus_di.append(0.0); dx.append(0.0)
            continue
        pdi = 100 * p / a
        mdi = 100 * m / a
        plus_di.append(pdi); minus_di.append(mdi)
        dx.append(0.0 if pdi + mdi == 0 else 100 * abs(pdi - mdi) / (pdi + mdi))
    adx_values = wilder_smooth(dx, period)
    return {
        "adx": adx_values[-1] if len(adx_values) >= period else None,
        "plus_di": plus_di[-1] if plus_di else None,
        "minus_di": minus_di[-1] if minus_di else None,
    }


def support_resistance(highs: list[float], lows: list[float], closes: list[float], period: int = 60) -> dict[str, object]:
    n = min(len(highs), len(lows), len(closes))
    if n < 5:
        return {"support": None, "resistance": None, "support_dist_pct": None, "resistance_dist_pct": None, "channel_pos": None, "support_status": "样本不足", "resistance_status": "样本不足"}
    p = min(period, n)
    hs = highs[n - p : n]
    ls = lows[n - p : n]
    support = min(ls)
    resistance = max(hs)
    last = closes[n - 1]
    support_dist = (last / support - 1) * 100 if support else None
    resistance_dist = (resistance / last - 1) * 100 if resistance and last else None
    channel_pos = (last - support) / (resistance - support) * 100 if resistance > support else 50.0
    support_status = "已跌破支撑" if support and last < support else "支撑上方"
    resistance_status = "已突破压力" if resistance and last > resistance else "压力上方空间"
    return {
        "support": support,
        "resistance": resistance,
        "support_dist_pct": support_dist,
        "resistance_dist_pct": resistance_dist,
        "channel_pos": channel_pos,
        "support_status": support_status,
        "resistance_status": resistance_status,
    }


def price_position(closes_or_prices: Iterable[float], last: float | None = None) -> float | None:
    values = [v for v in closes_or_prices if v is not None and v > 0]
    if not values:
        return None
    hi = max(values)
    lo = min(values)
    price = last if last is not None else values[-1]
    if hi <= lo:
        return 50.0
    return (price - lo) / (hi - lo) * 100

# -----------------------------
# V3.8: CSDN技术指标完整融入扩展
# 说明：以下函数只使用OHLCV基础数据，适合公开行情源；涉及Level-2/Tick的指标只做估算或留空说明。
# -----------------------------

def bias(values: list[float], period: int = 20) -> float | None:
    ma = moving_average(values, period)
    if ma is None or abs(ma) < 1e-12 or not values:
        return None
    return (values[-1] - ma) / ma * 100


def volume_ratio_ma(volumes: list[float], short: int = 5, long: int = 20) -> float | None:
    s = moving_average(volumes, short)
    l = moving_average(volumes, long)
    if s is None or l is None or l <= 0:
        return None
    return s / l


def volume_momentum(volumes: list[float], period: int = 10) -> float | None:
    if len(volumes) <= period or volumes[-period - 1] <= 0:
        return None
    return (volumes[-1] - volumes[-period - 1]) / volumes[-period - 1] * 100


def pmi(values: list[float], period: int = 10) -> float | None:
    if len(values) <= period or abs(values[-period - 1]) < 1e-12:
        return None
    return (values[-1] - values[-period - 1]) / values[-period - 1] * 100


def volatility_pct(values: list[float], period: int = 20) -> float | None:
    if len(values) < period:
        return None
    part = values[-period:]
    ma = mean(part)
    if abs(ma) < 1e-12:
        return None
    return pstdev(part) / ma * 100


def volume_volatility_pct(volumes: list[float], period: int = 20) -> float | None:
    if len(volumes) < period:
        return None
    part = [max(0.0, v) for v in volumes[-period:]]
    ma = mean(part)
    if ma <= 0:
        return None
    return pstdev(part) / ma * 100


def price_oscillator_ppo(values: list[float], fast: int = 12, slow: int = 26) -> float | None:
    if len(values) < slow:
        return None
    e_fast = ema_series(values, fast)
    e_slow = ema_series(values, slow)
    if not e_slow or abs(e_slow[-1]) < 1e-12:
        return None
    return (e_fast[-1] - e_slow[-1]) / e_slow[-1] * 100


def price_momentum_oscillator(values: list[float], roc_period: int = 1, ema_period: int = 10) -> float | None:
    if len(values) <= max(roc_period + ema_period, ema_period):
        return None
    rocs: list[float] = []
    for i in range(roc_period, len(values)):
        base = values[i - roc_period]
        rocs.append(0.0 if abs(base) < 1e-12 else (values[i] / base - 1) * 100)
    sm = ema_series(rocs, ema_period)
    return sm[-1] if sm else None


def volume_oscillator(volumes: list[float], short: int = 5, long: int = 20) -> float | None:
    if len(volumes) < long:
        return None
    e_short = ema_series(volumes, short)
    e_long = ema_series(volumes, long)
    den = e_short[-1] + e_long[-1]
    if abs(den) < 1e-12:
        return None
    return (e_short[-1] - e_long[-1]) / den * 100


def volume_rate_vr(closes: list[float], volumes: list[float], period: int = 26) -> float | None:
    n = min(len(closes), len(volumes))
    if n <= period:
        return None
    uv = dv = mv = 0.0
    for i in range(n - period, n):
        if closes[i] > closes[i - 1]:
            uv += volumes[i]
        elif closes[i] < closes[i - 1]:
            dv += volumes[i]
        else:
            mv += volumes[i]
    den = dv + 0.5 * mv
    if den <= 0:
        return 450.0 if uv > 0 else None
    return (uv + 0.5 * mv) / den * 100


def ad_line_series(highs: list[float], lows: list[float], closes: list[float], volumes: list[float]) -> list[float]:
    n = min(len(highs), len(lows), len(closes), len(volumes))
    out: list[float] = []
    acc = 0.0
    for i in range(n):
        h, l, c, v = highs[i], lows[i], closes[i], volumes[i]
        mfm = 0.0 if h <= l else ((c - l) - (h - c)) / (h - l)
        acc += mfm * v
        out.append(acc)
    return out


def rvi(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    """Relative Volatility Index：用收盘涨跌方向分组的真实波幅标准差近似。"""
    n = min(len(highs), len(lows), len(closes))
    if n <= period + 1:
        return None
    up_vol: list[float] = []
    down_vol: list[float] = []
    trs = true_range_series(highs, lows, closes)
    for i in range(n - period, n):
        if closes[i] >= closes[i - 1]:
            up_vol.append(trs[i])
        else:
            down_vol.append(trs[i])
    up_std = pstdev(up_vol) if len(up_vol) > 1 else (mean(up_vol) if up_vol else 0.0)
    down_std = pstdev(down_vol) if len(down_vol) > 1 else (mean(down_vol) if down_vol else 0.0)
    if down_std <= 1e-12:
        return 100.0 if up_std > 0 else 50.0
    return up_std / down_std * 100


def parabolic_sar(highs: list[float], lows: list[float], step: float = 0.02, max_step: float = 0.2) -> dict[str, float | str | None]:
    n = min(len(highs), len(lows))
    if n < 3:
        return {"sar": None, "trend": None, "signal": "样本不足"}
    long = highs[1] >= highs[0]
    sar = lows[0] if long else highs[0]
    ep = highs[0] if long else lows[0]
    af = step
    for i in range(1, n):
        prev_sar = sar
        sar = prev_sar + af * (ep - prev_sar)
        if long:
            sar = min(sar, lows[i - 1], lows[i - 2] if i >= 2 else lows[i - 1])
            if lows[i] < sar:
                long = False
                sar = ep
                ep = lows[i]
                af = step
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(max_step, af + step)
        else:
            sar = max(sar, highs[i - 1], highs[i - 2] if i >= 2 else highs[i - 1])
            if highs[i] > sar:
                long = True
                sar = ep
                ep = highs[i]
                af = step
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(max_step, af + step)
    return {"sar": sar, "trend": "多头" if long else "空头", "signal": "SAR在价格下方" if long else "SAR在价格上方"}


def ichimoku(highs: list[float], lows: list[float], closes: list[float]) -> dict[str, float | str | None]:
    n = min(len(highs), len(lows), len(closes))
    if n < 52:
        return {"tenkan": None, "kijun": None, "span_a": None, "span_b": None, "cloud_signal": "样本不足"}
    def mid(period: int) -> float:
        return (max(highs[n - period:n]) + min(lows[n - period:n])) / 2
    tenkan = mid(9)
    kijun = mid(26)
    span_a = (tenkan + kijun) / 2
    span_b = mid(52)
    top = max(span_a, span_b)
    bottom = min(span_a, span_b)
    c = closes[-1]
    if c > top:
        signal = "价格在云上，多头"
    elif c < bottom:
        signal = "价格在云下，空头"
    else:
        signal = "价格在云内，震荡"
    return {"tenkan": tenkan, "kijun": kijun, "span_a": span_a, "span_b": span_b, "cloud_signal": signal}


def fibonacci_retracement(highs: list[float], lows: list[float], closes: list[float], period: int = 120) -> dict[str, float | str | None]:
    n = min(len(highs), len(lows), len(closes))
    if n < 20:
        return {"levels": {}, "nearest": None, "signal": "样本不足"}
    p = min(period, n)
    hh = max(highs[n - p:n]); ll = min(lows[n - p:n]); c = closes[-1]
    rng = hh - ll
    if rng <= 0:
        return {"levels": {}, "nearest": None, "signal": "区间过窄"}
    levels = {
        "0%": hh,
        "23.6%": hh - rng * 0.236,
        "38.2%": hh - rng * 0.382,
        "50%": hh - rng * 0.5,
        "61.8%": hh - rng * 0.618,
        "100%": ll,
    }
    nearest_name, nearest_value = min(levels.items(), key=lambda kv: abs(kv[1] - c))
    if c < levels["61.8%"]:
        signal = "跌破61.8%回撤，趋势反转风险上升"
    elif c >= levels["38.2%"]:
        signal = "回撤较浅或修复较强"
    else:
        signal = "处于中等回撤区域"
    return {"levels": levels, "nearest": f"{nearest_name}:{nearest_value:.4f}", "signal": signal}


def fibonacci_time_window(length: int) -> dict[str, object]:
    fibs = [5, 8, 13, 21, 34, 55, 89, 144, 233]
    hits = [x for x in fibs if length >= x]
    nexts = [x for x in fibs if length < x]
    last = hits[-1] if hits else None
    nxt = nexts[0] if nexts else None
    signal = "接近斐波那契时间窗口" if nxt is not None and abs(nxt - length) <= 2 else "普通时间窗口"
    return {"bar_count": length, "last_window": last, "next_window": nxt, "signal": signal}


def td_sequential(closes: list[float]) -> dict[str, int | str | None]:
    if len(closes) < 5:
        return {"td_up": 0, "td_down": 0, "signal": "样本不足"}
    up = down = 0
    for i in range(len(closes) - 1, 3, -1):
        if closes[i] > closes[i - 4]:
            up += 1
            if down:
                break
        elif closes[i] < closes[i - 4]:
            down += 1
            if up:
                break
        else:
            break
    if up >= 9:
        sig = "上涨TD9，短线可能进入变盘/回落窗口"
    elif down >= 9:
        sig = "下跌TD9，短线可能进入变盘/反弹窗口"
    elif up > 0:
        sig = f"上涨TD{up}"
    elif down > 0:
        sig = f"下跌TD{down}"
    else:
        sig = "TD中性"
    return {"td_up": up, "td_down": down, "signal": sig}


def pivot_points(highs: list[float], lows: list[float], closes: list[float]) -> dict[str, float | None]:
    if len(highs) < 2 or len(lows) < 2 or len(closes) < 2:
        return {"pivot": None, "r1": None, "s1": None, "r2": None, "s2": None}
    h, l, c = highs[-2], lows[-2], closes[-2]
    p = (h + l + c) / 3
    return {"pivot": p, "r1": 2 * p - l, "s1": 2 * p - h, "r2": p + (h - l), "s2": p - (h - l)}


def price_pattern_basic(highs: list[float], lows: list[float], closes: list[float], period: int = 40) -> dict[str, str | float | None]:
    n = min(len(highs), len(lows), len(closes))
    if n < 20:
        return {"pattern": "样本不足", "signal": "样本不足", "confidence": 0.0}
    p = min(period, n)
    hs = highs[n - p:n]; ls = lows[n - p:n]; cs = closes[n - p:n]
    high1 = max(hs[:p//2]); high2 = max(hs[p//2:])
    low1 = min(ls[:p//2]); low2 = min(ls[p//2:])
    tol_h = max(high1, high2) * 0.035
    tol_l = max(low1, low2) * 0.035
    if abs(high1 - high2) <= tol_h and cs[-1] < mean(cs[-5:]):
        return {"pattern": "双顶雏形", "signal": "疑似压力区反复受阻，需确认是否跌破颈线", "confidence": 0.45}
    if abs(low1 - low2) <= tol_l and cs[-1] > mean(cs[-5:]):
        return {"pattern": "双底雏形", "signal": "疑似支撑区反复企稳，需确认是否突破颈线", "confidence": 0.45}
    if max(hs[-10:]) < max(hs[:10]) and min(ls[-10:]) > min(ls[:10]):
        return {"pattern": "三角收敛雏形", "signal": "波动收敛，等待放量方向选择", "confidence": 0.35}
    return {"pattern": "未识别明显形态", "signal": "形态中性", "confidence": 0.0}


def zigzag_points(closes: list[float], threshold_pct: float = 5.0) -> list[tuple[int, float]]:
    if not closes:
        return []
    points: list[tuple[int, float]] = [(0, closes[0])]
    last_idx = 0; last_val = closes[0]; direction = 0
    for i, price in enumerate(closes[1:], 1):
        if last_val <= 0:
            continue
        change = (price / last_val - 1) * 100
        if direction >= 0 and change <= -threshold_pct:
            points.append((last_idx, last_val)); direction = -1; last_idx = i; last_val = price
        elif direction <= 0 and change >= threshold_pct:
            points.append((last_idx, last_val)); direction = 1; last_idx = i; last_val = price
        else:
            if (direction >= 0 and price > last_val) or (direction <= 0 and price < last_val):
                last_idx = i; last_val = price
    if points[-1][0] != last_idx:
        points.append((last_idx, last_val))
    return points[-10:]


def psy(closes: list[float], period: int = 12) -> float | None:
    if len(closes) <= period:
        return None
    up = 0
    for i in range(len(closes) - period, len(closes)):
        if closes[i] > closes[i - 1]:
            up += 1
    return up / period * 100


def brar(highs: list[float], lows: list[float], opens: list[float] | None = None, closes: list[float] | None = None, period: int = 26) -> dict[str, float | None]:
    # 没有开盘价时用前收盘近似开盘价，避免接口缺字段导致完全不可用。
    n = min(len(highs), len(lows), len(closes or highs))
    if n <= period:
        return {"br": None, "ar": None}
    if opens is None or len(opens) < n:
        cc = closes or highs
        opens = [cc[i - 1] if i > 0 else cc[0] for i in range(n)]
    br_up = br_down = ar_up = ar_down = 0.0
    cc = closes or highs
    for i in range(n - period, n):
        prev_close = cc[i - 1] if i > 0 else cc[i]
        br_up += max(0.0, highs[i] - prev_close)
        br_down += max(0.0, prev_close - lows[i])
        ar_up += max(0.0, highs[i] - opens[i])
        ar_down += max(0.0, opens[i] - lows[i])
    return {"br": None if br_down <= 0 else br_up / br_down * 100, "ar": None if ar_down <= 0 else ar_up / ar_down * 100}


def cyr(values: list[float], period: int = 13) -> float | None:
    """市场强弱CYR近似：13日成本/价格均线的升降幅度。"""
    ma = rolling_ma(values, period)
    vals = [x for x in ma if x is not None]
    if len(vals) < 2 or vals[-2] == 0:
        return None
    return (vals[-1] / vals[-2] - 1) * 100
