from __future__ import annotations

from statistics import mean, pstdev
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
    price_momentum_oscillator,
    price_oscillator_ppo,
    price_pattern_basic,
    price_position,
    psy,
    roc,
    rsi,
    rvi,
    slope_pct,
    support_resistance,
    td_sequential,
    volatility_pct,
    volume_momentum,
    volume_oscillator,
    volume_rate_vr,
    volume_volatility_pct,
    vwap,
    williams_r,
    zigzag_points,
)
from quant_data.services.technical_indicator_library import TechnicalIndicatorLibraryService
from quant_data.services.source_knowledge_service import SourceKnowledgeService


def _last(seq: list[Any] | tuple[Any, ...] | None, default=None):
    return seq[-1] if seq else default


def _safe(v, default=None):
    try:
        if v is None:
            return default
        x = float(v)
        if x != x:
            return default
        return x
    except Exception:
        return default


def weighted_moving_average(values: list[float], period: int = 20) -> float | None:
    if len(values) < period or period <= 0:
        return None
    part = values[-period:]
    den = period * (period + 1) / 2
    return sum((i + 1) * v for i, v in enumerate(part)) / den


def hma(values: list[float], period: int = 20) -> float | None:
    """Hull MA 近似，只取最后一个值。"""
    if len(values) < period or period <= 1:
        return None
    half = max(1, period // 2)
    sqrt_n = max(1, int(period ** 0.5))
    series: list[float] = []
    for i in range(period - 1, len(values)):
        sub = values[: i + 1]
        w_half = weighted_moving_average(sub, half)
        w_full = weighted_moving_average(sub, period)
        if w_half is None or w_full is None:
            continue
        series.append(2 * w_half - w_full)
    return weighted_moving_average(series, sqrt_n) if len(series) >= sqrt_n else (series[-1] if series else None)


def trix(values: list[float], period: int = 12) -> float | None:
    if len(values) < period * 3 + 2:
        return None
    e1 = ema_series(values, period)
    e2 = ema_series(e1, period)
    e3 = ema_series(e2, period)
    if len(e3) < 2 or abs(e3[-2]) < 1e-12:
        return None
    return (e3[-1] / e3[-2] - 1) * 100


def bbi(values: list[float]) -> float | None:
    mas = [moving_average(values, n) for n in (3, 6, 12, 24)]
    if any(x is None for x in mas):
        return None
    return sum(float(x) for x in mas if x is not None) / 4


def dma(values: list[float], short: int = 10, long: int = 50) -> float | None:
    s = moving_average(values, short)
    l = moving_average(values, long)
    return None if s is None or l is None else s - l


def vpt_series(closes: list[float], volumes: list[float]) -> list[float]:
    n = min(len(closes), len(volumes))
    if n <= 1:
        return []
    out = [0.0]
    for i in range(1, n):
        prev = closes[i - 1]
        pct = 0.0 if abs(prev) < 1e-12 else (closes[i] - prev) / prev
        out.append(out[-1] + volumes[i] * pct)
    return out


def mass_index(highs: list[float], lows: list[float], period: int = 25) -> float | None:
    n = min(len(highs), len(lows))
    if n < period + 9:
        return None
    ranges = [max(0.0, highs[i] - lows[i]) for i in range(n)]
    e1 = ema_series(ranges, 9)
    e2 = ema_series(e1, 9)
    vals = [0.0 if abs(b) < 1e-12 else a / b for a, b in zip(e1, e2)]
    return sum(vals[-period:]) if len(vals) >= period else None


def money_flow_strength(amounts: list[float], period: int = 20) -> float | None:
    if len(amounts) < period:
        return None
    ma = moving_average(amounts, period)
    if not ma:
        return None
    return amounts[-1] / ma


def compute_indicator50_snapshot(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
    amounts: list[float] | None = None,
) -> dict[str, Any]:
    """输出“量、价、时、空 + 盘口/风控”50项技术/量化分析快照。

    不强行伪造 Level-2、Tick、期权等公开源缺失数据；缺数据项保留为 not_available，前端可显示为“待接入”。
    """
    amounts = amounts or [0.0 for _ in closes]
    n = min(len(closes), len(highs), len(lows), len(volumes))
    if n == 0:
        return {"count": 0, "implemented_count": 0, "entries": [], "by_dimension": {}, "note": "无K线数据，无法计算技术指标"}
    opens = (opens or closes)[:n]
    highs, lows, closes, volumes, amounts = highs[:n], lows[:n], closes[:n], volumes[:n], amounts[:n]
    last = closes[-1]
    m = macd(closes)
    kd = kdj(highs, lows, closes)
    adx_info = adx(highs, lows, closes)
    boll = bollinger(closes)
    sr = support_resistance(highs, lows, closes)
    piv = pivot_points(highs, lows, closes)
    ichi = ichimoku(highs, lows, closes)
    fib = fibonacci_retracement(highs, lows, closes)
    td = td_sequential(closes)
    sar = parabolic_sar(highs, lows)
    br = brar(highs, lows, opens=opens, closes=closes)
    obv = obv_series(closes, volumes)
    adl = ad_line_series(highs, lows, closes, volumes)
    vpt = vpt_series(closes, volumes)
    # 一些相对强度/绩效指标需要市场基准或收益序列，这里给出个股自身近似项。
    returns = [(closes[i] / closes[i - 1] - 1) for i in range(1, n) if closes[i - 1] > 0]
    vol_ret = pstdev(returns[-60:]) * (252 ** 0.5) if len(returns) >= 20 else None
    avg_ret = mean(returns[-60:]) * 252 if len(returns) >= 20 else None
    sharpe_est = None if vol_ret in (None, 0) else (avg_ret or 0) / vol_ret

    def entry(key: str, name: str, dimension: str, value: Any, signal: str = "", status: str = "computed", caveat: str = ""):
        return {"key": key, "name": name, "dimension": dimension, "value": value, "signal": signal, "status": status, "caveat": caveat}

    ma5, ma10, ma20, ma60, ma120, ma250 = [moving_average(closes, x) for x in (5, 10, 20, 60, 120, 250)]
    ema12 = _last(ema_series(closes, 12))
    ema26 = _last(ema_series(closes, 26))
    vw = vwap(highs, lows, closes, volumes, 20)
    atr14 = atr(highs, lows, closes)
    atr_pct = atr14 / last * 100 if atr14 and last else None
    wr = williams_r(highs, lows, closes)
    cci20 = cci(highs, lows, closes)
    mfi14 = mfi(highs, lows, closes, volumes)
    vr26 = volume_rate_vr(closes, volumes)
    entries = [
        entry("kline", "K线/价格行为", "价", {"open": opens[-1], "high": highs[-1], "low": lows[-1], "close": closes[-1]}, "实体/影线用于判断日内多空"),
        entry("ma5", "MA5", "价/时", ma5, "短期均线"),
        entry("ma10", "MA10", "价/时", ma10, "短期均线"),
        entry("ma20", "MA20", "价/时", ma20, "中短期趋势线"),
        entry("ma60", "MA60", "价/时", ma60, "中期趋势线"),
        entry("ma120", "MA120", "价/时", ma120, "半年线"),
        entry("ma250", "MA250", "价/时", ma250, "年线"),
        entry("ema12", "EMA12", "价/时", ema12, "快速指数均线"),
        entry("ema26", "EMA26", "价/时", ema26, "慢速指数均线"),
        entry("wma20", "WMA20", "价/时", weighted_moving_average(closes, 20), "加权均线更重视近期价格"),
        entry("hma20", "HMA20", "价/时", hma(closes, 20), "Hull均线降低滞后"),
        entry("bbi", "BBI多空指数", "价/时", bbi(closes), "3/6/12/24均线综合"),
        entry("dma", "DMA均线差", "价/时", dma(closes), "短长均线差值"),
        entry("macd_dif", "MACD DIF", "价/动量", _last(m.get("dif")), "DIF上穿DEA偏强"),
        entry("macd_dea", "MACD DEA", "价/动量", _last(m.get("dea")), "信号线"),
        entry("macd_hist", "MACD柱", "价/动量", _last(m.get("hist")), "柱体扩大代表动能增强"),
        entry("trix", "TRIX三重指数平滑", "价/动量", trix(closes), "过滤短噪声后的趋势动量"),
        entry("ppo", "PPO价格振荡器", "价/动量", price_oscillator_ppo(closes), "跨价格标的可比动量"),
        entry("pmo", "PMO价格动量", "价/动量", price_momentum_oscillator(closes), "价格动量平滑"),
        entry("rsi14", "RSI14", "价/动量", rsi(closes), "70以上偏热，30以下偏冷"),
        entry("kdj_k", "KDJ K", "价/动量", _last(kd.get("k")), "K上穿D偏强"),
        entry("kdj_d", "KDJ D", "价/动量", _last(kd.get("d")), "慢速线"),
        entry("kdj_j", "KDJ J", "价/动量", _last(kd.get("j")), "J>100过热，J<0超卖"),
        entry("wr14", "Williams %R", "价/反转", wr, ">-20超买，<-80超卖"),
        entry("cci20", "CCI20", "价/反转", cci20, ">100强势，<-100弱势/超卖"),
        entry("roc12", "ROC12", "价/动量", roc(closes), "变动率"),
        entry("mom10", "MOM10", "价/动量", momentum(closes), "动量差值"),
        entry("bias20", "BIAS20", "价/均值回归", bias(closes), "乖离率"),
        entry("vol", "成交量", "量", volumes[-1], "成交活跃度"),
        entry("vol_ma5", "5日均量", "量", moving_average(volumes, 5), "短期量能"),
        entry("vol_ma20", "20日均量", "量", moving_average(volumes, 20), "中期量能"),
        entry("volume_ratio_5_20", "均量比5/20", "量", (moving_average(volumes,5) / moving_average(volumes,20) if moving_average(volumes,5) and moving_average(volumes,20) else None), "量能是否放大"),
        entry("amount_strength", "成交额强度", "量/资金", money_flow_strength(amounts), "当日成交额/20日均成交额"),
        entry("vwap20", "VWAP20", "量/价", vw, "价格高于VWAP偏强"),
        entry("obv_slope", "OBV斜率", "量/价", slope_pct(obv, 10) if obv else None, "能量潮方向"),
        entry("adline_slope", "A/D Line斜率", "量/价", slope_pct(adl, 10) if adl else None, "累积派发线方向"),
        entry("vpt_slope", "VPT斜率", "量/价", slope_pct(vpt, 10) if vpt else None, "量价趋势"),
        entry("mfi14", "MFI14", "量/价", mfi14, "资金流量超买超卖"),
        entry("vr26", "VR26", "量/情绪", vr26, "成交量变异率"),
        entry("vo5_20", "VO5/20", "量", volume_oscillator(volumes), "成交量振荡"),
        entry("vmi10", "VMI10", "量", volume_momentum(volumes), "成交量动量"),
        entry("atr14", "ATR14", "空/波动", atr14, "波动率和止损空间"),
        entry("atr_pct", "ATR%", "空/波动", atr_pct, "ATR占价格比例"),
        entry("boll_mid", "BOLL中轨", "空/波动", boll.get("mid"), "均值中枢"),
        entry("boll_upper", "BOLL上轨", "空/波动", boll.get("upper"), "上方波动边界"),
        entry("boll_lower", "BOLL下轨", "空/波动", boll.get("lower"), "下方波动边界"),
        entry("boll_width", "BOLL带宽", "空/波动", boll.get("width_pct"), "带宽收窄提示变盘"),
        entry("volatility20", "价格波动率20", "空/波动", volatility_pct(closes), "收益空间/风险"),
        entry("volume_volatility20", "成交量波动率20", "量/情绪", volume_volatility_pct(volumes), "情绪波动"),
        entry("rvi14", "RVI14", "空/波动", rvi(highs, lows, closes), "上涨/下跌波动对比"),
        entry("mass_index", "Mass Index", "空/波动", mass_index(highs, lows), "识别区间扩张和反转风险"),
        entry("adx14", "ADX14", "趋势强度", adx_info.get("adx"), "ADX>20/25趋势增强"),
        entry("plus_di", "+DI", "趋势强度", adx_info.get("plus_di"), "+DI>-DI偏多"),
        entry("minus_di", "-DI", "趋势强度", adx_info.get("minus_di"), "-DI>+DI偏空"),
        entry("sar", "SAR", "趋势跟随", sar.get("sar"), str(sar.get("signal") or "")),
        entry("ichimoku", "Ichimoku云图", "综合", ichi, str(ichi.get("cloud_signal") or "")),
        entry("support", "60日支撑", "空/支撑阻力", sr.get("support"), "区间低位"),
        entry("resistance", "60日压力", "空/支撑阻力", sr.get("resistance"), "区间高位"),
        entry("channel_pos", "通道位置", "空/支撑阻力", sr.get("channel_pos"), "0低位/100高位"),
        entry("fibonacci", "斐波那契回调", "空/时间", fib, str(fib.get("signal") or "")),
        entry("pivot", "Pivot枢轴", "空/支撑阻力", piv, "突破R1偏强，跌破S1偏弱"),
        entry("td", "TD序列", "时", td, str(td.get("signal") or "")),
        entry("fibo_time", "斐波时间窗口", "时", fibonacci_time_window(len(closes)), "接近窗口提示变盘观察"),
        entry("psy12", "PSY12心理线", "时/情绪", psy(closes), "上涨天数占比"),
        entry("brar", "BRAR情绪", "情绪", br, "多空意愿"),
        entry("cyr13", "CYR13强弱", "情绪", cyr(closes), "市场强弱"),
        entry("price_position_250", "250日区间位置", "空/位置", price_position(closes[-250:], last), "低位/高位判断"),
        entry("drawdown_250", "250日高点回撤", "空/位置", (last / max(highs[-250:]) - 1) * 100 if highs[-250:] and max(highs[-250:]) > 0 else None, "负值为高点回撤"),
        entry("zigzag", "ZigZag波段", "形态", zigzag_points(closes), "主波段结构"),
        entry("pattern", "价格形态", "形态", price_pattern_basic(highs, lows, closes), "双顶/双底/收敛雏形"),
        entry("sharpe_est", "近60日夏普估算", "风控", sharpe_est, "基于近60日收益的粗估", "estimated", "正式回测阶段会按资金曲线计算"),
        entry("realized_vol", "年化波动率估算", "风控", vol_ret, "近60日实现波动率", "estimated", "非期权隐含波动率"),
        entry("order_book", "盘口/委托簿", "盘口", None, "需Level-2/Tick数据", "not_available", "当前公开免费源不伪造盘口"),
        entry("tick_flow", "逐笔/Tick资金", "盘口", None, "需逐笔成交数据", "not_available", "当前公开免费源不伪造逐笔"),
        entry("vix_macro", "VIX/全球风险偏好", "宏观情绪", None, "由全球要闻/指数模块映射", "not_available", "个股日线源不直接提供"),
    ]
    # 保证不少于50项；前端也可以完整展示全部项。
    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        by_dimension.setdefault(str(e["dimension"]), []).append(e)
    computed = sum(1 for e in entries if e.get("status") in {"computed", "estimated"} and e.get("value") is not None)
    return {
        "count": len(entries),
        "computed_or_estimated_count": computed,
        "missing_count": len(entries) - computed,
        "entries": entries,
        "by_dimension": by_dimension,
        "coverage_note": "覆盖量、价、时、空、情绪、形态、支撑压力、风控与盘口接口占位；缺少Level-2/Tick/期权数据时明确标注not_available，不伪造。",
    }


def tradercore_reference_framework() -> dict[str, Any]:
    ks = SourceKnowledgeService()
    cov = ks.coverage()
    tech = ks.technical_framework()
    msg = ks.message_framework()
    quant = ks.quant_framework()
    style = ks.style_framework()
    return {
        "source_grounding": {
            "version": cov.get("version"),
            "doc_count": cov.get("doc_count"),
            "doc_char_count": cov.get("doc_char_count"),
            "doc_table_count": cov.get("doc_table_count"),
            "word_technical_indicator_count": cov.get("technical_indicator_count_from_word"),
            "image_count": cov.get("image_count"),
            "note": "V16.4 已把四份 Word 全文抽取到 quant_data/data/source_docs/*.txt，并把结构化框架写入 word_source_knowledge.json。",
        },
        "candidate_channels": [
            {"channel": "换手率榜TOP50", "purpose": "发现资金正在流动的活跃票", "gate": "按实时换手率排序，剔除ST/极低成交额/异常脏数据"},
            {"channel": "成交额榜TOP20", "purpose": "补漏大盘或放量但换手不突出的票", "gate": "按成交额排序，强调流动性和机构可交易性"},
            {"channel": "技术初筛", "purpose": "寻找量已放但价格未远离均线的潜伏票", "gate": "量比>=1.3、MA20偏离±3%、近5日振幅<8%、非高位追涨；来自用户截图0的TraderCore逻辑"},
        ],
        "candidate_merge": "三通道拉完后按symbol去重，形成候选池；进入analyze后继续计算MA20偏离和5日振幅，避免只按实时榜单误选。",
        "scoring_layers": [
            {"layer": "外层", "weight": 20, "checks": ["市场体制/牛熊", "涨因逻辑", "资金情绪", "板块资金", "宏观/国际/政策消息"]},
            {"layer": "中层", "weight": 45, "checks": ["板块生命周期", "量能趋势", "龙头强度", "资金连续性", "超大单占比", "题材持续性"]},
            {"layer": "底层", "weight": 35, "checks": ["量价分析", "50项技术指标", "筹码/支撑压力", "基本面雷点", "风险标签"]},
        ],
        "output_style": ["脚本结论", "人工判断", "信号", "涨因", "资金", "板块", "风险", "交易逻辑", "技术面"],
        "word_message_dimensions": msg.get("analysis_dimensions", []),
        "word_message_sources": msg.get("source_channels", []),
        "word_technical_categories": tech.get("categories", []),
        "word_quant_pipeline": quant.get("pipeline", []),
        "word_strategy_families": quant.get("strategy_families", []),
        "word_style_blocks": style.get("analysis_blocks", []),
    }


def build_tradercore_diagnosis(result_like: dict[str, Any]) -> dict[str, Any]:
    """生成类似用户截图中的“脚本判定 vs 人工判断”诊断块。"""
    score = _safe(result_like.get("total_score"), 0.0) or 0.0
    tags = list(result_like.get("tags") or [])
    risks = list(result_like.get("risk_flags") or [])
    vol_ratio = _safe(result_like.get("volume_ratio")) or _safe(result_like.get("vol5_20"))
    amount = _safe(result_like.get("amount"), 0.0) or 0.0
    change = _safe(result_like.get("change_pct"), 0.0) or 0.0
    ma20 = _safe(result_like.get("ma20"))
    last = _safe(result_like.get("last"))
    rsi14 = _safe(result_like.get("rsi14"))
    kdj_j = _safe(result_like.get("kdj_j"))
    pe = _safe(result_like.get("pe_dynamic"))
    sector = result_like.get("sector") or "待接入板块"
    grade = result_like.get("grade") or ("A" if score >= 75 else "B" if score >= 65 else "C" if score >= 50 else "D")
    script = []
    human = []
    ma20_dev_pct = _safe(result_like.get("ma20_dev_pct"))
    amp5_pct = _safe(result_like.get("amp5_pct"))
    if vol_ratio and vol_ratio >= 1.3:
        script.append("量比放大，资金开始关注")
    if ma20 and last:
        dev = ma20_dev_pct if ma20_dev_pct is not None else (last / ma20 - 1) * 100
        if abs(dev) <= 3:
            script.append("价格仍贴近MA20，不属于过度追高")
        elif dev > 8:
            risks.append("价格远离MA20，存在急拉后退潮风险")
    if amp5_pct is not None:
        if amp5_pct < 8:
            script.append("近5日振幅未爆发，仍属于潜伏/待观察区")
        elif amp5_pct > 15:
            risks.append("近5日振幅过大，可能已经快速拉升或剧烈分歧")
    if rsi14 is not None and 45 <= rsi14 <= 68:
        script.append("RSI处于健康区间")
    if kdj_j is not None and kdj_j > 100:
        risks.append("KDJ J值过热")
    if pe is not None and pe <= 0:
        risks.append("动态PE异常或亏损，需人工核验财报")
    if score < 55:
        human.append("降级至观察/剔除：多维度信号不足或存在明显风险")
    elif risks:
        human.append("有可观察信号，但需先核验风险项和涨因是否成立")
    else:
        human.append("技术与资金信号相对一致，可进入下一步信息面/基本面核验")
    if not script:
        script.append("暂无明确量价共振，保持观察")
    decision = "待观察" if score >= 60 and risks else ("可重点观察" if score >= 70 and not risks else "谨慎/剔除" if score < 50 else "备选观察")
    return {
        "framework": tradercore_reference_framework(),
        "script_conclusion": f"{score:.1f}分，{grade}，{decision}",
        "rows": [
            {"dimension": "评分", "script": f"{score:.1f}分", "human": "分数只代表候选排序，不能替代公告/财报核验"},
            {"dimension": "信号", "script": "；".join(script[:4]), "human": "重点看量价、均线、动量是否共振，而不是单指标金叉死叉"},
            {"dimension": "涨因", "script": "、".join([t for t in tags if "政策" in t or "策略" in t or "题材" in t][:4]) or "未识别强事件催化", "human": "涨因需由公告、政策、行业新闻或资金流证据支撑"},
            {"dimension": "资金", "script": f"量比/均量比={vol_ratio if vol_ratio is not None else '--'}，成交额={amount:.0f}", "human": "成交额和换手只说明活跃，需结合板块资金和大单连续性"},
            {"dimension": "技术初筛", "script": f"MA20偏离={ma20_dev_pct if ma20_dev_pct is not None else '--'}%，5日振幅={amp5_pct if amp5_pct is not None else '--'}%", "human": "截图逻辑强调找‘量已放、价还没动’：量比>=1.3、MA20偏离±3%、5日振幅<8%只是入库门槛，不是买入结论"},
            {"dimension": "板块", "script": str(sector), "human": "板块处于启动/主升/分歧/退潮阶段会显著改变同一技术信号含义"},
            {"dimension": "风险", "script": "；".join(list(dict.fromkeys(risks))[:5]) or "暂无硬风险", "human": "ST、监管、业绩不及预期、减持、流动性过低优先级高于技术信号"},
        ],
        "trading_logic": "先过候选三通道，再按外层20%市场环境、中层45%板块资金、底层35%量价技术与基本面雷点综合判断。",
    }
