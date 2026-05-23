from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any

from quant_data.indicators import (
    ad_line_series,
    adx,
    atr,
    bias,
    bollinger,
    brar,
    cci,
    clamp,
    cyr,
    ema_series,
    fibonacci_retracement,
    fibonacci_time_window,
    ichimoku,
    kdj,
    macd,
    mfi,
    momentum,
    moving_average,
    obv_series,
    parabolic_sar,
    pivot_points,
    price_pattern_basic,
    price_position,
    psy,
    roc,
    rsi,
    slope_pct,
    support_resistance,
    td_sequential,
    volatility_pct,
    volume_rate_vr,
    vwap,
    williams_r,
    zigzag_points,
)
from quant_data.models import Bar, Quote


TECHNICAL_FACTOR_KEYS = [
    "ma",
    "ema",
    "macd",
    "rsi",
    "kdj",
    "boll",
    "atr",
    "vwap",
    "wr",
    "cci",
    "roc",
    "mom",
    "obv",
    "mfi",
    "adx",
    "dmi",
    "bias",
    "sar",
    "vr",
    "psy",
    "brar",
    "cyr",
    "ichimoku",
    "ichimoku_cloud",
    "fibonacci_retracement",
    "fibonacci_time_window",
    "td_sequential",
    "pivot_points",
    "zigzag",
    "support_resistance",
    "price_channel",
    "range_position",
    "price_volume_state",
    "volatility",
    "volume_ma",
    "vwap_strength",
    "volume_divergence",
    "price_pattern",
]


@dataclass(frozen=True)
class TechnicalFactorDetail:
    key: str
    name: str
    value: Any
    formula_source: str
    logic: str
    signal: str
    explanation: str
    score_contribution: float
    risk_penalty: float
    application: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _n(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _r(value: Any, digits: int = 4) -> Any:
    if isinstance(value, dict):
        return {k: _r(v, digits) for k, v in value.items()}
    if isinstance(value, list):
        return [_r(v, digits) for v in value]
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except Exception:
        return value


def _last(values: list[float] | None) -> float | None:
    return values[-1] if values else None


class TechnicalFactorEngine:
    """WordSource V2 technical factor engine.

    It turns the Word formulas and judging rules into concrete, per-indicator
    outputs. Level-2/Tick-only concepts are represented only when there is
    available public OHLCV evidence; no synthetic order-flow conclusions are
    produced here.
    """

    required_keys = TECHNICAL_FACTOR_KEYS

    def analyze(self, q: Quote, bars: list[Bar]) -> dict[str, Any]:
        opens = [_n(b.open) for b in bars]
        highs = [_n(b.high) for b in bars]
        lows = [_n(b.low) for b in bars]
        closes = [_n(b.close) for b in bars]
        volumes = [_n(b.volume) for b in bars]
        amounts = [_n(b.amount) for b in bars]
        n = min(len(opens), len(highs), len(lows), len(closes), len(volumes))
        if n == 0:
            factors = [
                self._detail(
                    key,
                    key,
                    None,
                    "无K线数据",
                    "K线样本为空，无法计算",
                    "中性",
                    "缺少K线，技术面不参与加分。",
                    0,
                    8,
                    "数据质量校验",
                ).to_dict()
                for key in self.required_keys
            ]
            return self._pack(factors, ["K线样本为空"], [])

        opens, highs, lows, closes, volumes, amounts = (
            opens[-n:],
            highs[-n:],
            lows[-n:],
            closes[-n:],
            volumes[-n:],
            amounts[-n:] if amounts else [0.0] * n,
        )
        last = _n(q.last, closes[-1])
        if last > 0:
            closes[-1] = last
            highs[-1] = max(highs[-1], last, _n(q.high))
            lows[-1] = min(x for x in [lows[-1], last, _n(q.low)] if x > 0)
            if q.volume:
                volumes[-1] = _n(q.volume)
            if q.amount:
                amounts[-1] = _n(q.amount)

        ma5 = moving_average(closes, 5)
        ma10 = moving_average(closes, 10)
        ma20 = moving_average(closes, 20)
        ma60 = moving_average(closes, 60)
        ema12 = _last(ema_series(closes, 12))
        ema26 = _last(ema_series(closes, 26))
        macd_data = macd(closes)
        dif = _last(macd_data.get("dif"))
        dea = _last(macd_data.get("dea"))
        hist = _last(macd_data.get("hist"))
        rsi14 = rsi(closes, 14)
        kd = kdj(highs, lows, closes)
        k_val = _last(kd.get("k"))
        d_val = _last(kd.get("d"))
        j_val = _last(kd.get("j"))
        boll = bollinger(closes, 20)
        atr14 = atr(highs, lows, closes, 14)
        atr_pct = atr14 / last * 100 if atr14 and last else None
        vwap20 = vwap(highs, lows, closes, volumes, 20)
        wr14 = williams_r(highs, lows, closes, 14)
        cci20 = cci(highs, lows, closes, 20)
        roc12 = roc(closes, 12)
        mom10 = momentum(closes, 10)
        obv = obv_series(closes, volumes)
        obv_slope = slope_pct(obv, 10) if obv else None
        mfi14 = mfi(highs, lows, closes, volumes, 14)
        adx_data = adx(highs, lows, closes, 14)
        adx14 = adx_data.get("adx")
        plus_di = adx_data.get("plus_di")
        minus_di = adx_data.get("minus_di")
        bias20 = bias(closes, 20)
        sar_data = parabolic_sar(highs, lows)
        vr26 = volume_rate_vr(closes, volumes, 26)
        psy12 = psy(closes, 12)
        brar_data = brar(highs, lows, opens=opens, closes=closes, period=26)
        cyr13 = cyr(closes, 13)
        ichi = ichimoku(highs, lows, closes)
        fib = fibonacci_retracement(highs, lows, closes, 120)
        fib_time = fibonacci_time_window(len(closes))
        td = td_sequential(closes)
        pivots = pivot_points(highs, lows, closes)
        zigs = zigzag_points(closes, threshold_pct=5.0)
        sr = support_resistance(highs, lows, closes, 60)
        pattern = price_pattern_basic(highs, lows, closes, 40)
        pos20 = price_position(closes[-20:], last)
        pos60 = price_position(closes[-60:], last)
        pos250 = price_position(closes[-250:], last)
        vol_ma5 = moving_average(volumes, 5)
        vol_ma20 = moving_average(volumes, 20)
        vol_ratio_ma = vol_ma5 / vol_ma20 if vol_ma5 and vol_ma20 else None
        price_vol20 = volatility_pct(closes, 20)
        ad_line = ad_line_series(highs, lows, closes, volumes)
        ad_line_slope = slope_pct(ad_line, 10) if ad_line else None

        factors: list[TechnicalFactorDetail] = []

        def add(
            key: str,
            name: str,
            value: Any,
            formula: str,
            logic: str,
            signal: str,
            explanation: str,
            score: float,
            risk: float,
            application: str,
        ) -> None:
            factors.append(self._detail(key, name, _r(value), formula, logic, signal, explanation, score, risk, application))

        ma_signal = "看多" if ma5 and ma10 and ma20 and last >= ma20 and ma5 >= ma10 else "看空" if ma20 and last < ma20 * 0.97 else "中性"
        add("ma", "MA均线", {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60}, "MA(n)=最近n日收盘价均值", "短中长期均线方向和价格相对MA20的位置", ma_signal, "价格站上MA20且短均线不弱时趋势修复更可信。", 4 if ma_signal == "看多" else 0, 3 if ma_signal == "看空" else 0, "趋势跟踪、支撑压力、回踩观察")

        ema_signal = "看多" if ema12 and ema26 and ema12 > ema26 else "看空" if ema12 and ema26 and ema12 < ema26 else "中性"
        add("ema", "EMA指数均线", {"ema12": ema12, "ema26": ema26}, "EMA_t=P_t*a+EMA_{t-1}*(1-a)", "EMA12/EMA26快慢线", ema_signal, "EMA比MA更重视近期价格，适合识别短期趋势拐点。", 2.5 if ema_signal == "看多" else 0, 2 if ema_signal == "看空" else 0, "短线趋势判断、MACD基础")

        macd_signal = "看多" if dif is not None and dea is not None and hist is not None and dif > dea and hist > 0 else "看空" if dif is not None and dea is not None and dif < dea and hist < 0 else "中性"
        add("macd", "MACD", {"dif": dif, "dea": dea, "hist": hist}, "DIF=EMA12-EMA26; DEA=EMA9(DIF); MACD柱=2*(DIF-DEA)", "DIF/DEA交叉和柱体方向", macd_signal, "MACD用于趋势和动量共振，柱体扩张代表动能增强。", 4 if macd_signal == "看多" else 0, 3 if macd_signal == "看空" else 0, "趋势市、动量确认")

        rsi_signal = "看多" if rsi14 is not None and 40 <= rsi14 <= 68 else "看空" if rsi14 is not None and rsi14 > 78 else "中性"
        add("rsi", "RSI14", rsi14, "RSI=100-100/(1+RS)", "衡量上涨平均幅度与下跌平均幅度的相对强弱", rsi_signal, "RSI健康区间比单纯超买/超卖更适合筛选，极端高位要防追高。", 3 if rsi_signal == "看多" else 0, 3 if rsi_signal == "看空" else 0, "震荡市、动量辅助、超买超卖预警")

        kdj_signal = "看多" if k_val is not None and d_val is not None and k_val >= d_val and (j_val is None or j_val < 100) else "看空" if j_val is not None and j_val > 105 else "中性"
        add("kdj", "KDJ", {"k": k_val, "d": d_val, "j": j_val}, "RSV=(C-Ln)/(Hn-Ln)*100; K/D平滑; J=3K-2D", "K/D交叉和J值极端状态", kdj_signal, "KDJ对短线更敏感，适合与RSI、成交量一起确认。", 2.5 if kdj_signal == "看多" else 0, 3 if kdj_signal == "看空" else 0, "短线反转、超买超卖")

        boll_pos = boll.get("position")
        boll_signal = "看多" if boll_pos is not None and 42 <= boll_pos <= 85 else "看空" if boll_pos is not None and boll_pos > 96 else "中性"
        add("boll", "BOLL布林带", boll, "中轨=MA20; 上轨=MA20+2σ; 下轨=MA20-2σ", "位置、带宽和上下轨约束", boll_signal, "价格位于中上轨且不过热，说明趋势修复仍在合理波动区间。", 3 if boll_signal == "看多" else 0, 3 if boll_signal == "看空" else 0, "波动率分析、突破/回撤观察")

        atr_signal = "中性" if atr_pct is None else "看多" if 1 <= atr_pct <= 5.5 else "看空" if atr_pct > 8 else "中性"
        add("atr", "ATR真实波幅", {"atr14": atr14, "atr_pct": atr_pct}, "TR=max(H-L,abs(H-Cp),abs(L-Cp)); ATR=TR的Wilder均值", "ATR占价格比例衡量止损空间和波动风险", atr_signal, "ATR过大代表仓位和止损难度上升，适中波动更利于执行。", 2 if atr_signal == "看多" else 0, 4 if atr_signal == "看空" else 0, "止损、仓位、波动风险")

        vwap_signal = "看多" if vwap20 and last >= vwap20 else "看空" if vwap20 and last < vwap20 * 0.97 else "中性"
        add("vwap", "VWAP", vwap20, "VWAP=sum(典型价*成交量)/sum(成交量)", "价格相对成交量加权成本线的位置", vwap_signal, "站上VWAP说明价格强于近期成交成本。", 3 if vwap_signal == "看多" else 0, 2.5 if vwap_signal == "看空" else 0, "日内/波段成本线、资金强弱")

        wr_signal = "看多" if wr14 is not None and wr14 < -80 else "看空" if wr14 is not None and wr14 > -20 else "中性"
        add("wr", "Williams %R", wr14, "WR=(Hn-C)/(Hn-Ln)*-100", "收盘价在近期高低区间中的位置", wr_signal, "WR低位提示超卖修复可能，高位提示短线过热。", 1.5 if wr_signal == "看多" else 0, 2.5 if wr_signal == "看空" else 0, "短线超买超卖")

        cci_signal = "看多" if cci20 is not None and cci20 > 100 else "看空" if cci20 is not None and cci20 < -150 else "中性"
        add("cci", "CCI", cci20, "CCI=(TP-MA(TP))/(0.015*平均偏差)", "典型价格相对均值的偏离", cci_signal, "CCI强势区说明趋势动能偏强，极端低位需要等待修复确认。", 2 if cci_signal == "看多" else 0, 2 if cci_signal == "看空" else 0, "趋势加速、反转预警")

        roc_signal = "看多" if roc12 is not None and roc12 > 0 else "看空" if roc12 is not None and roc12 < -6 else "中性"
        add("roc", "ROC", roc12, "ROC=(C/C_n-1)*100", "价格变化率", roc_signal, "ROC转正代表动量改善，过深为弱势信号。", 2 if roc_signal == "看多" else 0, 2 if roc_signal == "看空" else 0, "动量策略")

        mom_signal = "看多" if mom10 is not None and mom10 > 0 else "看空" if mom10 is not None and mom10 < 0 else "中性"
        add("mom", "MOM", mom10, "MOM=C-C_n", "当前价格和N日前价格差", mom_signal, "MOM为正说明短期价格动量仍在。", 1.5 if mom_signal == "看多" else 0, 1.5 if mom_signal == "看空" else 0, "动量确认")

        obv_signal = "看多" if obv_slope is not None and obv_slope > 2 else "看空" if obv_slope is not None and obv_slope < -5 else "中性"
        add("obv", "OBV能量潮", obv_slope, "涨日加成交量、跌日减成交量并累积", "OBV近10日斜率", obv_signal, "OBV上行说明量能潮改善，价格上涨但OBV不跟随需防背离。", 3 if obv_signal == "看多" else 0, 3 if obv_signal == "看空" else 0, "量价确认、背离观察")

        mfi_signal = "看多" if mfi14 is not None and 40 <= mfi14 <= 75 else "看空" if mfi14 is not None and (mfi14 > 85 or mfi14 < 20) else "中性"
        add("mfi", "MFI资金流量", mfi14, "典型价*成交量构造正负资金流，MFI=100-100/(1+MR)", "资金流入流出与价格结合", mfi_signal, "MFI健康区间说明资金流较稳，极端值提示过热或虚弱。", 3 if mfi_signal == "看多" else 0, 3 if mfi_signal == "看空" else 0, "资金流确认")

        adx_signal = "看多" if adx14 is not None and plus_di is not None and minus_di is not None and adx14 >= 22 and plus_di > minus_di else "看空" if adx14 is not None and plus_di is not None and minus_di is not None and adx14 >= 22 and minus_di > plus_di else "中性"
        add("adx", "ADX", adx14, "DX=abs(+DI--DI)/(+DI+-DI)*100; ADX=DX均值", "趋势强度，不单独表示方向", adx_signal, "ADX升高且+DI占优才是趋势偏强证据。", 3 if adx_signal == "看多" else 0, 3 if adx_signal == "看空" else 0, "趋势强弱确认")
        add("dmi", "DMI", {"+di": plus_di, "-di": minus_di}, "+DM/-DM与TR平滑得到+DI/-DI", "方向运动指标比较", adx_signal, "+DI大于-DI说明上涨方向运动占优，反之为空方占优。", 2 if adx_signal == "看多" else 0, 2 if adx_signal == "看空" else 0, "趋势方向判断")

        bias_signal = "看多" if bias20 is not None and -8 <= bias20 <= 5 else "看空" if bias20 is not None and bias20 > 12 else "中性"
        add("bias", "BIAS乖离率", bias20, "BIAS=(C-MA20)/MA20*100", "价格相对均线偏离程度", bias_signal, "合理乖离代表仍可观察，过大正乖离要防追高。", 1.5 if bias_signal == "看多" else 0, 3 if bias_signal == "看空" else 0, "均值回归、追高风险")

        sar_signal = "看多" if "下方" in str(sar_data.get("signal")) else "看空" if "上方" in str(sar_data.get("signal")) else "中性"
        add("sar", "SAR抛物线", sar_data, "SAR_{t+1}=SAR_t+AF*(EP-SAR_t)", "SAR相对价格的位置", sar_signal, "SAR在价格下方时偏多，在上方时偏空，可作为移动止损参考。", 2 if sar_signal == "看多" else 0, 2 if sar_signal == "看空" else 0, "趋势跟随、止损")

        vr_signal = "看多" if vr26 is not None and 80 <= vr26 <= 300 else "看空" if vr26 is not None and vr26 > 450 else "中性"
        add("vr", "VR成交量变异率", vr26, "VR=(上涨量+0.5*平量)/(下跌量+0.5*平量)*100", "量能情绪温度", vr_signal, "VR温和区间更可持续，极端高位要防筹码分歧。", 1.5 if vr_signal == "看多" else 0, 2.5 if vr_signal == "看空" else 0, "市场情绪、量能温度")

        psy_signal = "看多" if psy12 is not None and 30 <= psy12 <= 70 else "看空" if psy12 is not None and psy12 > 80 else "中性"
        add("psy", "PSY心理线", psy12, "PSY=N日内上涨天数/N*100", "上涨天数占比", psy_signal, "PSY过热说明连续上涨较多，均衡区间说明情绪未极端化。", 1 if psy_signal == "看多" else 0, 2 if psy_signal == "看空" else 0, "情绪温度")

        br_val = brar_data.get("br")
        ar_val = brar_data.get("ar")
        brar_signal = "看多" if br_val is not None and ar_val is not None and 70 <= br_val <= 250 and 70 <= ar_val <= 250 else "看空" if (br_val and br_val > 400) or (ar_val and ar_val > 400) else "中性"
        add("brar", "BRAR", brar_data, "BR/AR用昨日收盘和当日开盘衡量人气与意愿", "多空人气温度", brar_signal, "BRAR极端高位代表情绪拥挤，温和区间更利于观察。", 1 if brar_signal == "看多" else 0, 2 if brar_signal == "看空" else 0, "市场情绪")

        cyr_signal = "看多" if cyr13 is not None and cyr13 > 0 else "看空" if cyr13 is not None and cyr13 < -1.5 else "中性"
        add("cyr", "CYR市场强弱", cyr13, "13日成本均线升降幅", "短期成本线强弱", cyr_signal, "CYR转正说明短期强弱改善。", 1.5 if cyr_signal == "看多" else 0, 1.5 if cyr_signal == "看空" else 0, "强弱排序")

        ichi_signal = "看多" if "云上" in str(ichi.get("cloud_signal")) else "看空" if "云下" in str(ichi.get("cloud_signal")) else "中性"
        add("ichimoku", "Ichimoku", ichi, "转换线9、基准线26、先行A/B云层52", "价格相对云层和转换/基准线", ichi_signal, "价格在云上偏多，云下偏空，云内震荡。", 2 if ichi_signal == "看多" else 0, 2 if ichi_signal == "看空" else 0, "综合趋势支撑")
        add("ichimoku_cloud", "一目均衡表", ichi, "同Ichimoku云图计算", "云层支撑压力", ichi_signal, "一目均衡表用于观察趋势、支撑压力和震荡区。", 2 if ichi_signal == "看多" else 0, 2 if ichi_signal == "看空" else 0, "趋势、支撑压力")

        fib_signal = "看多" if "修复" in str(fib.get("signal")) or "较强" in str(fib.get("signal")) else "看空" if "跌破" in str(fib.get("signal")) else "中性"
        add("fibonacci_retracement", "Fibonacci回调", fib, "以阶段高低点计算23.6/38.2/50/61.8/100%回调位", "当前价最接近的黄金分割位", fib_signal, "回踩关键位企稳是观察点，跌破61.8%代表趋势破坏风险。", 1.8 if fib_signal == "看多" else 0, 2.5 if fib_signal == "看空" else 0, "支撑压力、回踩观察")

        fib_time_signal = "中性"
        add("fibonacci_time_window", "Fibonacci时间窗口", fib_time, "5/8/13/21/34/55/89等时间数列", "当前K线数是否接近时间窗口", fib_time_signal, "时间窗口只提示可能变盘，不直接判断方向。", 0.8 if "接近" in str(fib_time.get("signal")) else 0, 0.5 if "接近" in str(fib_time.get("signal")) else 0, "变盘观察")

        td_signal = "看多" if "下跌TD9" in str(td.get("signal")) else "看空" if "上涨TD9" in str(td.get("signal")) else "中性"
        add("td_sequential", "TD序列", td, "收盘价连续与4日前收盘价比较计数", "上涨/下跌TD计数", td_signal, "TD9是时间窗口信号，需要量价确认。", 1.5 if td_signal == "看多" else 0, 2 if td_signal == "看空" else 0, "短线变盘窗口")

        pivot_signal = "看多" if pivots.get("r1") and last > pivots["r1"] else "看空" if pivots.get("s1") and last < pivots["s1"] else "中性"
        add("pivot_points", "Pivot Points", pivots, "P=(H+L+C)/3; R1=2P-L; S1=2P-H", "相对P/R1/S1位置", pivot_signal, "站上Pivot中枢或R1偏强，跌破S1偏弱。", 1.5 if pivot_signal == "看多" else 0, 2 if pivot_signal == "看空" else 0, "日内/短线支撑压力")

        zig_signal = "中性"
        add("zigzag", "ZigZag", zigs, "按阈值过滤小波动，仅保留主要波段拐点", "最近波段数量与方向", zig_signal, "ZigZag用于结构阅读，不单独给买卖结论。", 0.8 if len(zigs) >= 4 else 0, 0, "波段结构")

        support_signal = "看多" if sr.get("support_dist_pct") is not None and 1 <= sr["support_dist_pct"] <= 15 else "看空" if sr.get("resistance_dist_pct") is not None and sr["resistance_dist_pct"] > -2 else "中性"
        add("support_resistance", "支撑压力", {"support": sr.get("support"), "resistance": sr.get("resistance"), "support_dist_pct": sr.get("support_dist_pct"), "resistance_dist_pct": sr.get("resistance_dist_pct")}, "最近60日高低点形成支撑压力区", "价格到支撑/压力的距离", support_signal, "离支撑不远且未跌破适合观察；贴近压力要等待放量突破。", 1.5 if support_signal == "看多" else 0, 2 if support_signal == "看空" else 0, "支撑压力、止损、追高风险")

        channel_signal = "看多" if sr.get("channel_pos") is not None and 25 <= sr["channel_pos"] <= 78 else "看空" if sr.get("channel_pos") is not None and sr["channel_pos"] >= 90 else "中性"
        add("price_channel", "价格通道", {"channel_position": sr.get("channel_pos"), "support": sr.get("support"), "resistance": sr.get("resistance")}, "通道上沿=周期高点，下沿=周期低点", "当前价在通道中的百分位", channel_signal, "中低位通道更适合回踩观察，高位拥挤要防追高。", 1.8 if channel_signal == "看多" else 0, 2.5 if channel_signal == "看空" else 0, "通道震荡、突破观察")

        range_signal = "看多" if pos20 is not None and pos250 is not None and 25 <= pos20 <= 85 and pos250 < 85 else "看空" if pos250 is not None and pos250 >= 92 else "中性"
        add("range_position", "区间位置", {"pos20": pos20, "pos60": pos60, "pos250": pos250}, "区间位置=(当前价-区间低点)/(区间高点-区间低点)*100", "20/60/250日位置", range_signal, "位置越高越需要确认突破质量，位置过低则要确认是否弱势。", 2 if range_signal == "看多" else 0, 3 if range_signal == "看空" else 0, "低位/高位判断、追高过滤")

        pv_signal = "看多" if _n(q.change_pct) >= 0 and (_n(q.volume_ratio) >= 1.1 or (vol_ratio_ma and vol_ratio_ma >= 1.1)) else "看空" if _n(q.change_pct) < -2 and (_n(q.volume_ratio) >= 1.5 or (vol_ratio_ma and vol_ratio_ma >= 1.5)) else "中性"
        add("price_volume_state", "量价状态", {"change_pct": q.change_pct, "volume_ratio": q.volume_ratio, "vol5_20": vol_ratio_ma}, "价格涨跌与量比/均量比交叉判断", "放量上涨、缩量回落或放量下跌", pv_signal, "放量上涨偏确认，放量下跌说明分歧和风险上升。", 3 if pv_signal == "看多" else 0, 3 if pv_signal == "看空" else 0, "突破确认、资金分歧")

        vol_signal = "看多" if price_vol20 is not None and price_vol20 <= 8 and (atr_pct is None or atr_pct <= 5.5) else "看空" if (price_vol20 is not None and price_vol20 > 12) or (atr_pct is not None and atr_pct > 8) else "中性"
        add("volatility", "波动率", {"price_volatility20": price_vol20, "atr_pct": atr_pct}, "20日收盘波动率与ATR%联合", "价格波动和真实波幅", vol_signal, "波动过大时胜率和仓位容错下降。", 1.5 if vol_signal == "看多" else 0, 3 if vol_signal == "看空" else 0, "风险指标、仓位")

        vma_signal = "看多" if vol_ratio_ma is not None and 1.1 <= vol_ratio_ma <= 2.5 else "看空" if vol_ratio_ma is not None and vol_ratio_ma > 4 else "中性"
        add("volume_ma", "均量", {"vol_ma5": vol_ma5, "vol_ma20": vol_ma20, "vol5_20": vol_ratio_ma}, "VMA5/VMA20", "短期均量相对中期均量", vma_signal, "温和放量比极端爆量更可持续。", 2 if vma_signal == "看多" else 0, 2 if vma_signal == "看空" else 0, "成交量确认")

        add("vwap_strength", "VWAP强弱", {"last": last, "vwap20": vwap20, "distance_pct": (last / vwap20 - 1) * 100 if vwap20 else None}, "价格/VWAP-1", "价格相对成交成本线强弱", vwap_signal, "VWAP上方代表持仓成本线支撑，跌破则成本压力上升。", 2 if vwap_signal == "看多" else 0, 2 if vwap_signal == "看空" else 0, "资金成本线")

        price_chg20 = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 and closes[-21] else None
        divergence_signal = "看空" if price_chg20 is not None and price_chg20 > 8 and (obv_slope is not None and obv_slope < 0) else "看多" if price_chg20 is not None and price_chg20 <= 0 and (obv_slope is not None and obv_slope > 5) else "中性"
        add("volume_divergence", "成交量背离", {"price_chg20": price_chg20, "obv_slope": obv_slope, "ad_line_slope": ad_line_slope}, "20日价格变化与OBV/A-D斜率对照", "价格上涨但量能线不确认属于顶背离风险", divergence_signal, "量价背离会降低突破可信度。", 1.5 if divergence_signal == "看多" else 0, 4 if divergence_signal == "看空" else 0, "量价背离、风险预警")

        pattern_signal = "看多" if "双底" in str(pattern.get("pattern")) else "看空" if "双顶" in str(pattern.get("pattern")) else "中性"
        add("price_pattern", "价格形态", pattern, "近40日高低点识别双顶/双底/三角收敛", "形态和确认信号", pattern_signal, "形态识别只是观察标签，突破仍需成交量和后续K线确认。", 1.5 if pattern_signal == "看多" else 0, 2.5 if pattern_signal == "看空" else 0, "形态观察、空间结构")

        missing = []
        if q.pe_dynamic is None:
            missing.append("PE缺失")
        if q.pb is None:
            missing.append("PB缺失")
        if q.total_market_cap is None:
            missing.append("总市值缺失")
        if q.float_market_cap is None:
            missing.append("流通市值缺失")
        if len(bars) < 120:
            missing.append("K线少于120根")
        if not vwap20:
            missing.append("VWAP成交量样本不足")

        return self._pack([x.to_dict() for x in factors], missing, [x.key for x in factors if x.signal == "看多"])

    def _detail(
        self,
        key: str,
        name: str,
        value: Any,
        formula_source: str,
        logic: str,
        signal: str,
        explanation: str,
        score: float,
        risk: float,
        application: str,
    ) -> TechnicalFactorDetail:
        return TechnicalFactorDetail(
            key=key,
            name=name,
            value=value,
            formula_source=formula_source,
            logic=logic,
            signal=signal,
            explanation=explanation,
            score_contribution=round(float(score or 0), 2),
            risk_penalty=round(float(risk or 0), 2),
            application=application,
        )

    def _pack(self, factors: list[dict[str, Any]], missing: list[str], bullish_keys: list[str]) -> dict[str, Any]:
        score = sum(_n(x.get("score_contribution")) for x in factors)
        risk = sum(_n(x.get("risk_penalty")) for x in factors)
        bulls = [x["name"] for x in factors if x.get("signal") == "看多"]
        bears = [x["name"] for x in factors if x.get("signal") == "看空"]
        if bulls and not bears:
            summary = "技术面偏多：" + "、".join(bulls[:6])
        elif bears and not bulls:
            summary = "技术面偏空：" + "、".join(bears[:6])
        elif bulls or bears:
            summary = "技术面分化：偏多 " + "、".join(bulls[:4]) + "；风险 " + "、".join(bears[:4])
        else:
            summary = "技术面中性，等待量价共振。"
        return {
            "factor_count": len(factors),
            "required_count": len(self.required_keys),
            "covered_required_keys": [x.get("key") for x in factors if x.get("key") in self.required_keys],
            "score_total": round(clamp(score, 0, 100), 2),
            "risk_total": round(clamp(risk, 0, 100), 2),
            "summary": summary,
            "missing_data_hints": list(dict.fromkeys(missing)),
            "bullish_keys": bullish_keys,
            "factors": factors,
        }
