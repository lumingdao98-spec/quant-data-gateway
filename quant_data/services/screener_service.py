from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterable

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
    pmi,
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
    volume_momentum,
    volume_oscillator,
    volume_rate_vr,
    volume_volatility_pct,
    volatility_pct,
    vwap,
    williams_r,
    zigzag_points,
)
from quant_data.services.technical_indicator_library import TechnicalIndicatorLibraryService
from quant_data.services.technical_factor_engine import TechnicalFactorEngine
from quant_data.services.market_behavior_engine import MarketBehaviorEngine
from quant_data.services.trading_framework_service import compute_indicator50_snapshot, build_tradercore_diagnosis
from quant_data.services.wordsource_system_service import WordSourceSystemService
from quant_data.services.candidate_pool_service import CandidatePoolService
from quant_data.models import AssetType, Bar, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.utils import normalize_symbol


@dataclass
class ScreenerConfig:
    universe: str = "custom"              # custom / market / stocks / etf
    symbols: list[str] | None = None
    max_items: int = 50                    # 最多分析多少只，避免公开接口请求过多
    max_pages: int = 1                     # 全市场快照最多读取页数
    page_size: int = 100
    kline_limit: int = 260
    kline_adjust: str = "qfq"             # none / qfq / hfq；筛选评分默认前复权，避免除权造成高位回撤误判
    min_score: float = 0
    min_amount: float = 0                  # 元
    include_stocks: bool = True
    include_etf: bool = True
    force_quotes: bool = False             # 只强制实时行情，不强制K线
    force_kline: bool = False
    mode: str = "balanced"                # balanced / low_position / trend_volume / etf
    strategies: list[str] | None = None     # 策略库多选，参与评分权重
    enable_news: bool = False               # 新闻评分由 api 层对候选结果二次分析


@dataclass
class ScreenerResult:
    symbol: str
    name: str
    asset_type: str
    last: float
    change_pct: float
    amount: float
    turnover: float | None
    volume_ratio: float | None
    pe_dynamic: float | None
    pb: float | None
    total_market_cap: float | None
    float_market_cap: float | None
    circulating_market_cap: float | None
    total_share: float | None
    float_share: float | None
    metric_missing_reasons: list[str]
    ma5: float | None
    ma10: float | None
    ma20: float | None
    ma60: float | None
    rsi14: float | None
    macd_dif: float | None
    macd_dea: float | None
    macd_hist: float | None
    pos20: float | None
    pos60: float | None
    pos120: float | None
    pos250: float | None
    drawdown250: float | None
    rebound250: float | None
    drawdown250_high: float | None
    drawdown250_low: float | None
    drawdown_basis: dict | None
    vol5_20: float | None
    atr14: float | None
    atr_pct: float | None
    boll_mid: float | None
    boll_upper: float | None
    boll_lower: float | None
    boll_width: float | None
    boll_position: float | None
    kdj_k: float | None
    kdj_d: float | None
    kdj_j: float | None
    wr14: float | None
    cci20: float | None
    mfi14: float | None
    obv_slope: float | None
    roc12: float | None
    momentum10: float | None
    adx14: float | None
    plus_di: float | None
    minus_di: float | None
    vwap20: float | None
    support60: float | None
    resistance60: float | None
    support_dist_pct: float | None
    resistance_dist_pct: float | None
    channel_position: float | None
    tape_score: float | None
    turnover_state: str | None
    volume_state: str | None
    close_signal: str | None
    # V3.8 指标知识库与完整技术指标矩阵
    sar: float | None
    sar_signal: str | None
    bias20: float | None
    vr26: float | None
    rvi14: float | None
    pmo10: float | None
    ppo: float | None
    pmi10: float | None
    vmi10: float | None
    vo5_20: float | None
    price_volatility20: float | None
    volume_volatility20: float | None
    ad_line_slope: float | None
    psy12: float | None
    br26: float | None
    ar26: float | None
    cyr13: float | None
    ichimoku_signal: str | None
    fibonacci_nearest: str | None
    fibonacci_signal: str | None
    td_signal: str | None
    pivot_point: float | None
    pivot_r1: float | None
    pivot_s1: float | None
    price_pattern: str | None
    pattern_signal: str | None
    zigzag_count: int
    time_score: float
    pattern_score: float
    indicator_coverage: dict
    indicator_matrix: dict
    indicator_signals: list[dict]
    indicator50_snapshot: dict
    tradercore_diagnosis: dict
    wordsource_report: dict
    technical_factor_details: list[dict]
    technical_signal_summary: str
    technical_factor_score: float
    technical_factor_risk: float
    candidate_channels: list[str]
    candidate_channel_reason: str
    candidate_rank_score: float
    ma20_deviation_pct: float | None
    amplitude_5d_pct: float | None
    capital_signal: str
    theme_stage: str
    theme_strength: float | None
    theme_labels: list[str]
    market_cap_style: str
    support_resistance_distance: dict
    chase_high_risk: str
    behavior_tags: list[str]
    behavior_score: float
    behavior_confidence: str
    behavior_evidence: list[str]
    manipulation_risk_label: str
    need_level2_confirm: bool
    kline_markers: list[dict]
    comprehensive_diagnosis: str
    script_score: float
    manual_review_score: float
    upgrade_reasons: list[str]
    downgrade_reasons: list[str]
    missing_data_hints: list[str]
    low_score: float
    trend_score: float
    momentum_score: float
    volume_score: float
    volatility_score: float
    strength_score: float
    value_score: float
    risk_penalty: float
    total_score: float
    grade: str
    tags: list[str]
    risk_flags: list[str]
    reason: str
    quote_source: str
    kline_source: str
    kline_adjust: str
    exright_adjusted: bool
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class ScreenerService:
    """股票/ETF技术筛选服务。

    设计原则：
    1. 只依赖 MarketDataService，不直接依赖具体网站接口；
    2. 公开接口请求量可控，默认不强制刷新K线；
    3. 每个评分子项独立，后续可无缝接入新闻、基本面和回测评分。
    """

    def __init__(self, market_data: MarketDataService) -> None:
        self.market_data = market_data
        self.wordsource_system = WordSourceSystemService()
        self.technical_factor_engine = TechnicalFactorEngine()
        self.market_behavior_engine = MarketBehaviorEngine()
        self.candidate_pool_service = CandidatePoolService()
        self._candidate_meta_by_symbol: dict[str, dict] = {}

    def run(self, config: ScreenerConfig) -> dict:
        started = datetime.now()
        config.max_items = max(1, min(int(config.max_items or 50), 500))
        config.max_pages = max(1, min(int(config.max_pages or 1), 50))
        config.page_size = max(20, min(int(config.page_size or 100), 500))
        config.kline_limit = max(80, min(int(config.kline_limit or 260), 520))
        config.kline_adjust = str(config.kline_adjust or "qfq").lower()
        if config.kline_adjust not in {"none", "qfq", "hfq"}:
            config.kline_adjust = "qfq"
        quotes = self._load_universe(config)
        analyzed: list[ScreenerResult] = []
        passed: list[ScreenerResult] = []
        errors: list[dict] = []
        skipped_low_amount = 0
        for q in quotes[: config.max_items]:
            try:
                if config.min_amount and (q.amount or 0) < config.min_amount:
                    skipped_low_amount += 1
                    continue
                bars = self.market_data.get_kline(q.symbol, frame="1d", limit=config.kline_limit, adjust=config.kline_adjust, force_refresh=config.force_kline)
                if len(bars) < 60:
                    errors.append({"symbol": q.symbol, "name": q.name, "error": "K线数量不足，无法稳定评分"})
                    continue
                q = self.market_data.enrich_quote_metrics(q, force_refresh=config.force_quotes, bars=bars)
                result = self.analyze(q, bars, mode=config.mode, strategies=config.strategies or [], kline_adjust=config.kline_adjust)
                analyzed.append(result)
                if result.total_score >= config.min_score:
                    passed.append(result)
            except Exception as exc:
                errors.append({"symbol": q.symbol, "name": q.name, "error": str(exc)[:220]})
        passed.sort(key=lambda x: x.total_score, reverse=True)
        ended = datetime.now()
        return {
            "ok": True,
            "config": asdict(config),
            "started_at": started.isoformat(timespec="seconds"),
            "ended_at": ended.isoformat(timespec="seconds"),
            "elapsed_seconds": round((ended - started).total_seconds(), 3),
            "pool_count": len(quotes),
            "universe_count": len(quotes),
            "analyzed_count": len(analyzed),
            "filtered_out_count": max(0, len(analyzed) - len(passed)),
            "skipped_low_amount": skipped_low_amount,
            "result_count": len(passed),
            "error_count": len(errors),
            "data": [x.to_dict() for x in passed],
            "errors": errors[:80],
            "note": "候选数量=通过最低评分过滤的结果；分析数量=成功完成行情+K线+技术评分的标的；股票池数量=本次输入/快照标的。评分仅作研究辅助，不构成投资建议。",
        }

    def _load_universe(self, config: ScreenerConfig) -> list[Quote]:
        universe = (config.universe or "custom").lower()
        self._candidate_meta_by_symbol = {}
        quotes: list[Quote] = []
        if universe in {"custom", "watch", "watchlist"}:
            symbols = [normalize_symbol(s) for s in (config.symbols or []) if str(s).strip()]
            # 去重但保序
            symbols = list(dict.fromkeys(symbols))
            custom_quotes = self.market_data.get_quotes(symbols[: config.max_items], force_refresh=config.force_quotes)
            custom_quotes = [self.market_data.enrich_quote_metrics(q, force_refresh=config.force_quotes) for q in custom_quotes]
            self._candidate_meta_by_symbol = {
                q.symbol: {
                    "symbol": q.symbol,
                    "name": q.name,
                    "channels": ["custom_input"],
                    "reason": "自定义/自选池输入",
                    "rank_score": 0.0,
                }
                for q in custom_quotes
            }
            return custom_quotes

        for page in range(1, config.max_pages + 1):
            page_quotes = self.market_data.get_market_snapshot(page=page, page_size=config.page_size)
            if not page_quotes:
                break
            quotes.extend(page_quotes)
            if len(quotes) >= config.max_items:
                break
        filtered: list[Quote] = []
        for q in quotes:
            if q.asset_type == AssetType.ETF and not config.include_etf:
                continue
            if q.asset_type == AssetType.STOCK and not config.include_stocks:
                continue
            if universe == "stocks" and q.asset_type != AssetType.STOCK:
                continue
            if universe == "etf" and q.asset_type != AssetType.ETF:
                continue
            filtered.append(q)
        filtered = [self.market_data.enrich_quote_metrics(q, force_refresh=config.force_quotes) for q in filtered]
        # V3.17 三通道候选池：换手率 TOP50、成交额 TOP20、技术初筛互补，避免只盯单一榜单。
        if universe in {"market", "stocks", "all", "custom_market"}:
            pool = self.candidate_pool_service.build(filtered, max_items=max(config.max_items, 120))
            self._candidate_meta_by_symbol = {m["symbol"]: m for m in pool.get("candidates", [])}
            by_quote = {q.symbol: q for q in filtered}
            ordered = [by_quote[s] for s in pool.get("selected_symbols", []) if s in by_quote]
            filtered = ordered or self._three_channel_candidates(filtered, config.max_items)
        else:
            self._candidate_meta_by_symbol = {
                q.symbol: {
                    "symbol": q.symbol,
                    "name": q.name,
                    "channels": ["snapshot"],
                    "reason": "实时行情快照输入",
                    "rank_score": 0.0,
                }
                for q in filtered
            }
        # 去重但保序
        by_symbol: dict[str, Quote] = {}
        for q in filtered:
            if q.symbol not in by_symbol:
                by_symbol[q.symbol] = q
        return list(by_symbol.values())[: config.max_items]

    def _three_channel_candidates(self, quotes: list[Quote], max_items: int) -> list[Quote]:
        """参考截图中的三通道候选逻辑。

        公开快照阶段无法直接算MA20偏离和5日振幅，所以先用实时换手率、成交额、量比/涨幅做轻量候选；
        进入 analyze 后再用完整K线做底层技术评分。
        """
        def ok(q: Quote) -> bool:
            n = (q.name or "").upper()
            if "ST" in n or "退" in n:
                return False
            if q.amount is not None and q.amount < 10_000_000:
                return False
            return True
        pool = [q for q in quotes if ok(q)]
        turnover_top = sorted(pool, key=lambda q: float(q.turnover or 0), reverse=True)[:50]
        amount_top = sorted(pool, key=lambda q: float(q.amount or 0), reverse=True)[:20]
        tech_seed = [q for q in pool if (q.volume_ratio or 0) >= 1.3 and -4.5 <= float(q.change_pct or 0) <= 8.5]
        tech_seed = sorted(tech_seed, key=lambda q: (float(q.volume_ratio or 0), float(q.amount or 0)), reverse=True)[:80]
        ordered: list[Quote] = []
        seen: set[str] = set()
        for block in (turnover_top, amount_top, tech_seed, pool):
            for q in block:
                if q.symbol in seen:
                    continue
                seen.add(q.symbol); ordered.append(q)
                if len(ordered) >= max(max_items, 120):
                    return ordered
        return ordered

    def analyze(self, q: Quote, bars: list[Bar], mode: str = "balanced", strategies: list[str] | None = None, kline_adjust: str = "qfq") -> ScreenerResult:
        strategies = set(strategies or [])
        closes = [float(b.close or 0) for b in bars if b.close is not None]
        opens = [float(b.open or 0) for b in bars if b.open is not None]
        highs = [float(b.high or 0) for b in bars if b.high is not None]
        lows = [float(b.low or 0) for b in bars if b.low is not None]
        volumes = [float(b.volume or 0) for b in bars]
        amounts = [float(b.amount or 0) for b in bars]
        last = float(q.last or closes[-1])
        # 若实时价有效，技术指标的最后收盘价按实时价同步。
        if last > 0 and closes:
            closes[-1] = last
            highs[-1] = max(highs[-1], last, float(q.high or 0))
            lows[-1] = min(x for x in [lows[-1], last, float(q.low or 0)] if x > 0)
            if opens:
                opens[-1] = float(q.open or opens[-1] or last)
            if q.volume:
                volumes[-1] = float(q.volume)
            if q.amount:
                amounts[-1] = float(q.amount)
        ma5 = moving_average(closes, 5)
        ma10 = moving_average(closes, 10)
        ma20 = moving_average(closes, 20)
        ma60 = moving_average(closes, 60)
        ma20_prev = sum(closes[-25:-5]) / 20 if len(closes) >= 25 else None
        ma60_prev = sum(closes[-80:-20]) / 60 if len(closes) >= 80 else None
        m = macd(closes)
        dif = m["dif"][-1] if m["dif"] else None
        dea = m["dea"][-1] if m["dea"] else None
        hist = m["hist"][-1] if m["hist"] else None
        hist_prev = m["hist"][-2] if len(m["hist"]) >= 2 else None
        rsi14 = rsi(closes, 14)
        boll = bollinger(closes, 20)
        b_mid = boll.get("mid")
        b_upper = boll.get("upper")
        b_lower = boll.get("lower")
        b_width = boll.get("width_pct")
        b_pos = boll.get("position")
        pos20 = price_position(closes[-20:], last)
        pos60 = price_position(closes[-60:], last)
        pos120 = price_position(closes[-120:], last)
        pos250 = price_position(closes[-250:], last)
        window_highs = [x for x in (highs[-250:] if len(highs) >= 60 else highs) if x and x > 0]
        window_lows = [x for x in (lows[-250:] if len(lows) >= 60 else lows) if x and x > 0]
        high250 = max(window_highs) if window_highs else None
        low250 = min(window_lows) if window_lows else None
        # 回撤率统一定义为：当前价/近250交易日最高价 - 1，结果为负值；低点反弹为当前价/近250交易日最低价 - 1。
        # 使用筛选配置中的复权K线口径；默认 qfq，避免除权缺口导致“假深回撤”。
        drawdown250 = (last / high250 - 1) * 100 if high250 and high250 > 0 and last > 0 else None
        rebound250 = (last / low250 - 1) * 100 if low250 and low250 > 0 and last > 0 else None
        drawdown_basis = {
            "formula": "drawdown250 = current_last / max(high[-250:]) - 1",
            "unit": "%",
            "sign": "负值表示相对近250日高点回撤；例如 -30 表示回撤30%",
            "kline_adjust": kline_adjust or "qfq",
            "adjust": kline_adjust or "qfq",
            "window_days": min(250, len(window_highs)),
            "current_last": round(last, 4),
            "last_close": round(last, 4),
            "high250": round(high250, 4) if high250 else None,
            "high_250": round(high250, 4) if high250 else None,
            "low250": round(low250, 4) if low250 else None,
            "low_250": round(low250, 4) if low250 else None,
            "note": "若公开源返回不复权数据或最新行情与K线不同步，系统优先使用同复权口径缓存并在该字段说明口径。",
        }
        vol5 = moving_average(volumes, 5)
        vol20 = moving_average(volumes, 20)
        amt20 = moving_average(amounts, 20)
        vol5_20 = vol5 / vol20 if vol5 and vol20 else None
        ma20_dev_pct = (last / ma20 - 1) * 100 if ma20 and last else None
        amp5_pct = None
        if len(highs) >= 5 and len(lows) >= 5 and last:
            lo5 = min(x for x in lows[-5:] if x > 0) if any(x > 0 for x in lows[-5:]) else None
            hi5 = max(highs[-5:]) if highs[-5:] else None
            if lo5 and hi5:
                amp5_pct = (hi5 / lo5 - 1) * 100

        # V3.7 技术指标矩阵：量、价、时、空四维共振。
        atr14 = atr(highs, lows, closes, 14)
        atr_pct = atr14 / last * 100 if atr14 and last else None
        kd = kdj(highs, lows, closes, 9)
        kdj_k = kd["k"][-1] if kd["k"] else None
        kdj_d = kd["d"][-1] if kd["d"] else None
        kdj_j = kd["j"][-1] if kd["j"] else None
        wr14 = williams_r(highs, lows, closes, 14)
        cci20 = cci(highs, lows, closes, 20)
        mfi14 = mfi(highs, lows, closes, volumes, 14)
        obv_values = obv_series(closes, volumes)
        obv_slope = slope_pct(obv_values, 10)
        roc12 = roc(closes, 12)
        momentum10 = momentum(closes, 10)
        adx_info = adx(highs, lows, closes, 14)
        adx14 = adx_info.get("adx")
        plus_di = adx_info.get("plus_di")
        minus_di = adx_info.get("minus_di")
        vwap20 = vwap(highs, lows, closes, volumes, 20)
        sr = support_resistance(highs, lows, closes, 60)
        support60 = sr.get("support")
        resistance60 = sr.get("resistance")
        support_dist_pct = sr.get("support_dist_pct")
        resistance_dist_pct = sr.get("resistance_dist_pct")
        channel_position = sr.get("channel_pos")

        # V3.8 完整技术指标：把文章中“公式/评判标准/应用场景”对应的主要指标全部落成可计算字段、信号或知识库条目。
        sar_info = parabolic_sar(highs, lows)
        sar_value = sar_info.get("sar")
        sar_signal = sar_info.get("signal")
        bias20 = bias(closes, 20)
        vr26 = volume_rate_vr(closes, volumes, 26)
        rvi14 = rvi(highs, lows, closes, 14)
        pmo10 = price_momentum_oscillator(closes, 1, 10)
        ppo_val = price_oscillator_ppo(closes, 12, 26)
        pmi10 = pmi(closes, 10)
        vmi10 = volume_momentum(volumes, 10)
        vo5_20 = volume_oscillator(volumes, 5, 20)
        price_vol20 = volatility_pct(closes, 20)
        volume_vol20 = volume_volatility_pct(volumes, 20)
        ad_values = ad_line_series(highs, lows, closes, volumes)
        ad_line_slope = slope_pct(ad_values, 10) if ad_values else None
        psy12 = psy(closes, 12)
        brar26 = brar(highs, lows, closes=closes, period=26)
        br26 = brar26.get("br")
        ar26 = brar26.get("ar")
        cyr13 = cyr(closes, 13)
        ichi = ichimoku(highs, lows, closes)
        ichimoku_signal = ichi.get("cloud_signal")
        fib = fibonacci_retracement(highs, lows, closes, 120)
        fibonacci_nearest = fib.get("nearest")
        fibonacci_signal = fib.get("signal")
        td = td_sequential(closes)
        td_signal = td.get("signal")
        piv = pivot_points(highs, lows, closes)
        pivot_point = piv.get("pivot")
        pivot_r1 = piv.get("r1")
        pivot_s1 = piv.get("s1")
        pattern = price_pattern_basic(highs, lows, closes, 40)
        price_pattern = pattern.get("pattern")
        pattern_signal = pattern.get("signal")
        zigs = zigzag_points(closes, threshold_pct=5.0)
        fib_time = fibonacci_time_window(len(closes))
        technical_detail_report = self.technical_factor_engine.analyze(q, bars)
        indicator_matrix = {
            "trend": {"MA5": ma5, "MA10": ma10, "MA20": ma20, "MA60": ma60, "MACD_DIF": dif, "MACD_DEA": dea, "ADX14": adx14, "+DI": plus_di, "-DI": minus_di, "SAR": sar_value, "SAR信号": sar_signal, "PPO": ppo_val, "Ichimoku": ichimoku_signal},
            "momentum": {"RSI14": rsi14, "KDJ_K": kdj_k, "KDJ_D": kdj_d, "KDJ_J": kdj_j, "WR14": wr14, "CCI20": cci20, "ROC12": roc12, "MOM10": momentum10, "PMO10": pmo10, "PMI10": pmi10, "BIAS20": bias20},
            "volume": {"VOL5/VOL20": vol5_20, "VR26": vr26, "MFI14": mfi14, "OBV斜率": obv_slope, "ADLine斜率": ad_line_slope, "VO5_20": vo5_20, "VMI10": vmi10, "VWAP20": vwap20, "成交量波动率20": volume_vol20},
            "volatility_space": {"ATR14": atr14, "ATR%": atr_pct, "BOLL带宽": b_width, "BOLL位置": b_pos, "价格波动率20": price_vol20, "RVI14": rvi14, "支撑60": support60, "压力60": resistance60, "斐波那契最近位": fibonacci_nearest, "斐波那契信号": fibonacci_signal, "Pivot": pivot_point, "R1": pivot_r1, "S1": pivot_s1},
            "time_pattern_sentiment": {"TD序列": td_signal, "斐波时间": fib_time, "PSY12": psy12, "BR26": br26, "AR26": ar26, "CYR13": cyr13, "价格形态": price_pattern, "形态信号": pattern_signal, "ZigZag点数": len(zigs)},
        }

        mode = (mode or "balanced").lower()
        kline_adjust = str(kline_adjust or "qfq").lower()
        if kline_adjust not in {"none", "qfq", "hfq"}:
            kline_adjust = "qfq"
        low_score, low_tags = self._score_low_position(pos60, pos120, pos250, drawdown250, rebound250, last, ma20, ma60)
        trend_score, trend_tags = self._score_trend(last, closes, ma5, ma10, ma20, ma60, ma20_prev, ma60_prev, dif, dea, hist, hist_prev, rsi14, boll)
        momentum_score, momentum_tags, momentum_risks = self._score_momentum(rsi14, kdj_k, kdj_d, kdj_j, wr14, cci20, roc12, momentum10, dif, dea, hist, hist_prev)
        volume_score, volume_tags, volume_risks = self._score_volume(q, closes, volumes, amounts, vol5_20, amt20)
        tape_score, tape_tags, tape_risks, tape_meta = self._score_tape(q, closes, highs, lows, volumes, amounts, vol5_20)
        volatility_score, volatility_tags, volatility_risks = self._score_volatility_space(last, atr_pct, b_width, b_pos, channel_position, support_dist_pct, resistance_dist_pct)
        strength_score, strength_tags, strength_risks = self._score_strength(last, vwap20, mfi14, obv_slope, adx14, plus_di, minus_di, q, closes, volumes)
        time_score, time_tags, time_risks = self._score_time_dimension(td_signal, fib_time, psy12, br26, ar26, cyr13)
        pattern_score, pattern_tags, pattern_risks = self._score_pattern_dimension(price_pattern, pattern_signal, fibonacci_signal, pivot_point, pivot_r1, pivot_s1, last, zigs)
        value_score, value_tags, value_risks = self._score_value(q)
        risk_penalty, risk_flags = self._score_risk(q, last, closes, ma20, ma60, rsi14, drawdown250, vol5_20, amt20)
        risk_flags += momentum_risks + volatility_risks + strength_risks + time_risks + pattern_risks
        indicator_signals = self._build_indicator_signals(indicator_matrix)
        indicator50_snapshot = compute_indicator50_snapshot(opens, highs, lows, closes, volumes, amounts)
        behavior_analysis = self.market_behavior_engine.analyze(
            q,
            bars,
            technical_context={
                "support": support60,
                "resistance": resistance60,
                "vwap20": vwap20,
                "pos20": pos20,
                "ma20": ma20,
            },
        )
        behavior_tags = list(behavior_analysis.get("behavior_tags") or [])
        behavior_risk = float(behavior_analysis.get("risk_penalty_contribution") or 0.0)
        if behavior_risk:
            risk_penalty += behavior_risk
        risk_flags += [t for t in behavior_tags if t in getattr(self.market_behavior_engine, "high_risk_tags", set())]

        total = self._weighted_total(
            mode,
            {
                "low": low_score,
                "trend": trend_score,
                "momentum": momentum_score,
                "volume": volume_score,
                "volatility": volatility_score,
                "strength": strength_score,
                "tape": tape_score,
                "time": time_score,
                "pattern": pattern_score,
                "value": value_score,
            },
            risk_penalty,
        )

        strategy_tags: list[str] = []
        strategy_risks: list[str] = []
        # 策略多选真正参与评分：每个策略基于已计算的技术因子进行轻量加减权。
        if strategies:
            if "low_position" in strategies and (pos250 is not None and pos250 <= 40):
                total += 4; strategy_tags.append("策略:低位修复")
            if "oversold_rebound" in strategies and (rsi14 is not None and 28 <= rsi14 <= 45) and ma5 and last >= ma5:
                total += 3; strategy_tags.append("策略:超卖回升")
            if "ma_repair" in strategies and ma5 and ma10 and ma20 and ma5 >= ma10 and last >= ma20 * 0.985:
                total += 3; strategy_tags.append("策略:均线修复")
            if "ma_bull" in strategies and ma5 and ma10 and ma20 and ma5 > ma10 > ma20:
                total += 3; strategy_tags.append("策略:均线多头")
            if "macd_cross" in strategies and dif is not None and dea is not None and dif > dea:
                total += 2.5; strategy_tags.append("策略:MACD多头")
            if "macd_hist_turn" in strategies and hist is not None and hist_prev is not None and hist > hist_prev:
                total += 2; strategy_tags.append("策略:MACD柱改善")
            if "volume_breakout" in strategies and vol5_20 is not None and 1.15 <= vol5_20 <= 2.8:
                total += 2.5; strategy_tags.append("策略:温和放量")
            if "boll_mid_break" in strategies and b_mid and last > b_mid:
                total += 2; strategy_tags.append("策略:BOLL中轨突破")
            if "amount_active" in strategies and q.amount and q.amount >= 200_000_000:
                total += 2; strategy_tags.append("策略:成交额活跃")
            if "finance_quality" in strategies and value_score >= 10 and not value_risks:
                total += 1.5; strategy_tags.append("策略:财报/估值质量可观察")
            if "main_money_est" in strategies and strength_score >= 10:
                total += 2; strategy_tags.append("策略:资金强度估算")
            if "breakout_platform" in strategies and channel_position is not None and channel_position >= 78 and vol5_20 is not None and vol5_20 >= 1.1:
                total += 2.5; strategy_tags.append("策略:箱体上沿突破观察")
            if "gap_open" in strategies and len(closes) >= 2 and abs((closes[-1] / closes[-2] - 1) * 100) >= 5:
                strategy_tags.append("策略:跳空/波动观察")
            if "etf_liquidity" in strategies and q.asset_type == AssetType.ETF and q.amount and q.amount >= 50_000_000:
                total += 3; strategy_tags.append("策略:ETF流动性")
            if "adx_trend" in strategies and adx14 is not None and adx14 >= 22 and plus_di is not None and minus_di is not None and plus_di > minus_di:
                total += 2.5; strategy_tags.append("策略:ADX趋势强度")
            if "rsi_kdj_resonance" in strategies and rsi14 is not None and kdj_j is not None and 35 <= rsi14 <= 68 and kdj_j >= 45:
                total += 2; strategy_tags.append("策略:RSI/KDJ共振")
            if "mfi_obv_resonance" in strategies and mfi14 is not None and obv_slope is not None and mfi14 >= 45 and obv_slope > 0:
                total += 2; strategy_tags.append("策略:MFI/OBV资金共振")
            if "atr_risk" in strategies and atr_pct is not None and atr_pct >= 8:
                total -= 3; strategy_risks.append("策略:ATR高波动扣分")
            if "risk_control" in strategies and (risk_penalty >= 12 or volume_risks or value_risks or volatility_risks):
                total -= 4; strategy_risks.append("策略风控扣分")
            if "avoid_chasing_high" in strategies and (pos250 is not None and pos250 >= 88 or (rsi14 is not None and rsi14 >= 78)):
                total -= 4; strategy_risks.append("高位/过热追涨过滤")
            if "exright_drawdown_guard" in strategies:
                if kline_adjust in {"qfq", "hfq"}:
                    strategy_tags.append("策略:复权回撤校正")
                elif drawdown250 is not None and drawdown250 <= -25:
                    strategy_risks.append("未复权回撤可能受除权影响")
            if "sar_trend" in strategies and sar_signal and "下方" in str(sar_signal):
                total += 1.8; strategy_tags.append("策略:SAR趋势跟随")
            if "bias_reversion" in strategies and bias20 is not None and -8 <= bias20 <= -1 and rsi14 is not None and rsi14 >= 30:
                total += 2.2; strategy_tags.append("策略:BIAS乖离修复")
            if "vr_mfi_energy" in strategies and vr26 is not None and 80 <= vr26 <= 320 and mfi14 is not None and 35 <= mfi14 <= 75:
                total += 2.0; strategy_tags.append("策略:VR/MFI能量共振")
            if "td_time_window" in strategies and ("TD" in str(td_signal) or (isinstance(fib_time, dict) and "接近" in str(fib_time.get("signal")))):
                total += 1.2; strategy_tags.append("策略:时间窗口观察")
            if "fibo_pivot_space" in strategies and ("修复较强" in str(fibonacci_signal) or (pivot_point and last > pivot_point)):
                total += 1.8; strategy_tags.append("策略:空间结构确认")
            if "ichimoku_cloud" in strategies and "云上" in str(ichimoku_signal):
                total += 2.0; strategy_tags.append("策略:一目云图多头")
            if "pattern_zigzag" in strategies and price_pattern and any(k in str(price_pattern) for k in ["双底", "三角"]):
                total += 1.5; strategy_tags.append("策略:形态结构观察")
            if "psy_brar_sentiment" in strategies and psy12 is not None and 30 <= psy12 <= 70 and (br26 is None or br26 < 350):
                total += 1.2; strategy_tags.append("策略:情绪温度正常")

        total_score = round(clamp(total, 0, 100), 2)
        tags = low_tags + trend_tags + momentum_tags + volume_tags + volatility_tags + strength_tags + tape_tags + time_tags + pattern_tags + value_tags + strategy_tags + behavior_tags
        risk_flags = risk_flags + volume_risks + tape_risks + value_risks + strategy_risks
        tags = self._prioritize_tags(tags, risk_flags)
        risk_flags = list(dict.fromkeys(risk_flags))
        grade = self._grade(total_score)
        reason = self._reason(tags, risk_flags, low_score, trend_score, volume_score, value_score, risk_penalty, momentum_score, volatility_score, strength_score) + f"/时间{time_score:.0f}/形态{pattern_score:.0f}"
        tradercore_diagnosis = build_tradercore_diagnosis({
            "symbol": q.symbol,
            "name": q.name,
            "total_score": total_score,
            "grade": grade,
            "last": last,
            "change_pct": q.change_pct,
            "amount": q.amount,
            "volume_ratio": q.volume_ratio,
            "vol5_20": vol5_20,
            "ma20": ma20,
            "ma20_dev_pct": round(ma20_dev_pct, 3) if ma20_dev_pct is not None else None,
            "amp5_pct": round(amp5_pct, 3) if amp5_pct is not None else None,
            "rsi14": rsi14,
            "kdj_j": kdj_j,
            "pe_dynamic": q.pe_dynamic,
            "tags": tags,
            "risk_flags": risk_flags,
        })
        wordsource_report = self.wordsource_system.build_report(
            q=q,
            bars=bars,
            indicator_snapshot=indicator50_snapshot,
            base_score=total_score,
            tags=tags,
            risk_flags=risk_flags,
            news_items=[],
        )
        candidate_meta = self._candidate_meta_by_symbol.get(q.symbol, {
            "channels": ["direct_analyze"],
            "reason": "直接分析接口输入",
            "rank_score": 0.0,
        })
        style_info = wordsource_report.get("style") or {}
        theme_info = wordsource_report.get("theme") or {}
        diagnosis_info = wordsource_report.get("diagnosis") or {}
        capital_info = wordsource_report.get("capital") or {}
        theme_labels = list(theme_info.get("themes") or [])
        style_labels = list(style_info.get("style_labels") or [])
        cap_style_candidates = {"微小盘", "小盘", "中盘", "大盘", "超大盘", "ETF"}
        market_cap_style = next((x for x in style_labels if x in cap_style_candidates), style_labels[0] if style_labels else "未知")
        if market_cap_style == "未知":
            cap_for_style = q.float_market_cap or q.total_market_cap
            if q.asset_type == AssetType.ETF:
                market_cap_style = "ETF"
            elif cap_for_style:
                yi = float(cap_for_style) / 100_000_000
                if yi < 50:
                    market_cap_style = "微盘"
                elif yi < 200:
                    market_cap_style = "小盘"
                elif yi < 800:
                    market_cap_style = "中盘"
                elif yi < 3000:
                    market_cap_style = "大盘"
                else:
                    market_cap_style = "超大盘"
        capital_level = str(capital_info.get("capital_level") or "")
        if capital_level == "强" or strength_score >= 10:
            capital_signal = "资金面偏强"
        elif capital_level == "弱" or strength_score <= 4:
            capital_signal = "资金面偏弱"
        else:
            capital_signal = "资金面中性"
        if (pos250 is not None and pos250 >= 88) or (b_pos is not None and b_pos >= 95) or (rsi14 is not None and rsi14 >= 78):
            chase_high_risk = "高"
        elif (pos250 is not None and pos250 >= 75) or (rsi14 is not None and rsi14 >= 70):
            chase_high_risk = "中"
        else:
            chase_high_risk = "低"
        high_behavior_tags = set(behavior_tags) & getattr(self.market_behavior_engine, "high_risk_tags", set())
        if high_behavior_tags and chase_high_risk == "低":
            chase_high_risk = "中"
        if len(high_behavior_tags) >= 2:
            chase_high_risk = "高"
        missing_data_hints = []
        missing_data_hints.extend(technical_detail_report.get("missing_data_hints") or [])
        missing_data_hints.extend(getattr(q, "metric_missing_reasons", None) or [])
        for field_name, value in [
            ("换手率", q.turnover),
            ("量比", q.volume_ratio),
            ("PE", q.pe_dynamic),
            ("PB", q.pb),
            ("总市值", q.total_market_cap),
            ("流通市值", q.float_market_cap),
        ]:
            if value is None:
                missing_data_hints.append(f"{field_name}缺失")
        kline_quality = (wordsource_report.get("data_quality") or {}).get("kline") or {}
        missing_data_hints.extend(kline_quality.get("missing_fields") or [])
        missing_data_hints.extend(diagnosis_info.get("missing_evidence") or [])
        missing_data_hints = list(dict.fromkeys([str(x) for x in missing_data_hints if x]))
        script_score = float(diagnosis_info.get("script_score", total_score) or total_score)
        manual_review_score = float(diagnosis_info.get("review_score", total_score) or total_score)
        upgrade_reasons = list(diagnosis_info.get("upgrade_reasons") or [])
        downgrade_reasons = list(diagnosis_info.get("downgrade_reasons") or [])
        technical_summary_text = self._grade_aware_technical_summary(
            grade,
            str(technical_detail_report.get("summary") or ""),
            tags,
            risk_flags,
            behavior_tags,
            last,
            ma20,
            ma60,
            vwap20,
        )
        risk_prefix = ""
        if grade.startswith("D") or high_behavior_tags:
            headline = "、".join(list(dict.fromkeys(risk_flags + behavior_tags))[:3]) or "技术结构偏弱"
            risk_prefix = f"风险优先：{headline}；"
        comprehensive_diagnosis = (
            f"{risk_prefix}{grade}，{capital_signal}，"
            f"板块阶段={theme_info.get('theme_stage', '待确认')}，"
            f"市值风格={market_cap_style}，追高风险={chase_high_risk}；{reason}"
        )
        rf = lambda x, d=2: round(x, d) if x is not None else None
        return ScreenerResult(
            symbol=q.symbol,
            name=q.name,
            asset_type=q.asset_type.value,
            last=round(last, 4),
            change_pct=round(float(q.change_pct or 0), 3),
            amount=float(q.amount or 0),
            turnover=q.turnover,
            volume_ratio=q.volume_ratio,
            pe_dynamic=q.pe_dynamic,
            pb=q.pb,
            total_market_cap=q.total_market_cap,
            float_market_cap=q.float_market_cap,
            circulating_market_cap=q.circulating_market_cap,
            total_share=q.total_share,
            float_share=q.float_share,
            metric_missing_reasons=list(getattr(q, "metric_missing_reasons", None) or []),
            ma5=rf(ma5, 4),
            ma10=rf(ma10, 4),
            ma20=rf(ma20, 4),
            ma60=rf(ma60, 4),
            rsi14=rf(rsi14, 2),
            macd_dif=rf(dif, 4),
            macd_dea=rf(dea, 4),
            macd_hist=rf(hist, 4),
            pos20=rf(pos20, 2),
            pos60=rf(pos60, 2),
            pos120=rf(pos120, 2),
            pos250=rf(pos250, 2),
            drawdown250=rf(drawdown250, 2),
            rebound250=rf(rebound250, 2),
            drawdown250_high=rf(high250, 4),
            drawdown250_low=rf(low250, 4),
            drawdown_basis=drawdown_basis,
            vol5_20=rf(vol5_20, 3),
            atr14=rf(atr14, 4),
            atr_pct=rf(atr_pct, 2),
            boll_mid=rf(b_mid, 4),
            boll_upper=rf(b_upper, 4),
            boll_lower=rf(b_lower, 4),
            boll_width=rf(b_width, 2),
            boll_position=rf(b_pos, 2),
            kdj_k=rf(kdj_k, 2),
            kdj_d=rf(kdj_d, 2),
            kdj_j=rf(kdj_j, 2),
            wr14=rf(wr14, 2),
            cci20=rf(cci20, 2),
            mfi14=rf(mfi14, 2),
            obv_slope=rf(obv_slope, 2),
            roc12=rf(roc12, 2),
            momentum10=rf(momentum10, 4),
            adx14=rf(adx14, 2),
            plus_di=rf(plus_di, 2),
            minus_di=rf(minus_di, 2),
            vwap20=rf(vwap20, 4),
            support60=rf(support60, 4),
            resistance60=rf(resistance60, 4),
            support_dist_pct=rf(support_dist_pct, 2),
            resistance_dist_pct=rf(resistance_dist_pct, 2),
            channel_position=rf(channel_position, 2),
            tape_score=round(tape_score, 2),
            turnover_state=tape_meta.get("turnover_state"),
            volume_state=tape_meta.get("volume_state"),
            close_signal=tape_meta.get("close_signal"),
            sar=rf(sar_value, 4),
            sar_signal=str(sar_signal) if sar_signal is not None else None,
            bias20=rf(bias20, 2),
            vr26=rf(vr26, 2),
            rvi14=rf(rvi14, 2),
            pmo10=rf(pmo10, 2),
            ppo=rf(ppo_val, 2),
            pmi10=rf(pmi10, 2),
            vmi10=rf(vmi10, 2),
            vo5_20=rf(vo5_20, 2),
            price_volatility20=rf(price_vol20, 2),
            volume_volatility20=rf(volume_vol20, 2),
            ad_line_slope=rf(ad_line_slope, 2),
            psy12=rf(psy12, 2),
            br26=rf(br26, 2),
            ar26=rf(ar26, 2),
            cyr13=rf(cyr13, 2),
            ichimoku_signal=str(ichimoku_signal) if ichimoku_signal is not None else None,
            fibonacci_nearest=str(fibonacci_nearest) if fibonacci_nearest is not None else None,
            fibonacci_signal=str(fibonacci_signal) if fibonacci_signal is not None else None,
            td_signal=str(td_signal) if td_signal is not None else None,
            pivot_point=rf(pivot_point, 4),
            pivot_r1=rf(pivot_r1, 4),
            pivot_s1=rf(pivot_s1, 4),
            price_pattern=str(price_pattern) if price_pattern is not None else None,
            pattern_signal=str(pattern_signal) if pattern_signal is not None else None,
            zigzag_count=len(zigs),
            time_score=round(time_score, 2),
            pattern_score=round(pattern_score, 2),
            indicator_coverage=TechnicalIndicatorLibraryService().coverage(),
            indicator_matrix=indicator_matrix,
            indicator_signals=indicator_signals,
            indicator50_snapshot=indicator50_snapshot,
            tradercore_diagnosis=tradercore_diagnosis,
            wordsource_report=wordsource_report,
            technical_factor_details=technical_detail_report.get("factors", []),
            technical_signal_summary=technical_summary_text,
            technical_factor_score=round(float(technical_detail_report.get("score_total") or 0), 2),
            technical_factor_risk=round(float(technical_detail_report.get("risk_total") or 0), 2),
            candidate_channels=list(candidate_meta.get("channels") or []),
            candidate_channel_reason=str(candidate_meta.get("reason") or ""),
            candidate_rank_score=round(float(candidate_meta.get("rank_score") or 0), 2),
            ma20_deviation_pct=rf(ma20_dev_pct, 3),
            amplitude_5d_pct=rf(amp5_pct, 3),
            capital_signal=capital_signal,
            theme_stage=str(theme_info.get("theme_stage") or "待确认"),
            theme_strength=rf(theme_info.get("theme_score"), 2) if isinstance(theme_info.get("theme_score"), (int, float)) else None,
            theme_labels=theme_labels,
            market_cap_style=market_cap_style,
            support_resistance_distance={
                "support_dist_pct": rf(support_dist_pct, 2),
                "resistance_dist_pct": rf(resistance_dist_pct, 2),
                "support_status": sr.get("support_status"),
                "resistance_status": sr.get("resistance_status"),
                "support_price": rf(support60, 4),
                "resistance_price": rf(resistance60, 4),
            },
            chase_high_risk=chase_high_risk,
            behavior_tags=behavior_tags,
            behavior_score=round(float(behavior_analysis.get("behavior_score") or 0), 2),
            behavior_confidence=str(behavior_analysis.get("behavior_confidence") or "low"),
            behavior_evidence=list(behavior_analysis.get("behavior_evidence") or []),
            manipulation_risk_label=str(behavior_analysis.get("manipulation_risk_label") or "观察"),
            need_level2_confirm=bool(behavior_analysis.get("need_level2_confirm")),
            kline_markers=list(behavior_analysis.get("kline_markers") or []),
            comprehensive_diagnosis=comprehensive_diagnosis,
            script_score=round(script_score, 2),
            manual_review_score=round(manual_review_score, 2),
            upgrade_reasons=upgrade_reasons,
            downgrade_reasons=downgrade_reasons,
            missing_data_hints=missing_data_hints,
            low_score=round(low_score, 2),
            trend_score=round(trend_score, 2),
            momentum_score=round(momentum_score, 2),
            volume_score=round(volume_score, 2),
            volatility_score=round(volatility_score, 2),
            strength_score=round(strength_score, 2),
            value_score=round(value_score, 2),
            risk_penalty=round(risk_penalty, 2),
            total_score=total_score,
            grade=grade,
            tags=tags,
            risk_flags=risk_flags,
            reason=reason,
            quote_source=q.source,
            kline_source=bars[-1].source if bars else "unknown",
            kline_adjust=kline_adjust,
            exright_adjusted=(kline_adjust in {"qfq", "hfq"}),
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _grade_aware_technical_summary(
        self,
        grade: str,
        base_summary: str,
        tags: list[str],
        risk_flags: list[str],
        behavior_tags: list[str],
        last: float,
        ma20: float | None,
        ma60: float | None,
        vwap20: float | None,
    ) -> str:
        optimistic = ["低位修复动量改善", "量能配合", "空间结构较好", "时间窗口观察"]
        clean = str(base_summary or "").strip()
        for phrase in optimistic:
            clean = clean.replace(phrase, "").strip("；; ，,")
        risks = list(dict.fromkeys([x for x in (risk_flags or []) + (behavior_tags or []) if x]))[:4]
        positives = [x for x in tags or [] if x not in risks][:4]
        ma_bits = []
        if ma20 and last < ma20:
            ma_bits.append("价格低于MA20")
        if ma60 and last < ma60:
            ma_bits.append("价格低于MA60")
        if vwap20 and last < vwap20:
            ma_bits.append("VWAP承压")
        if grade.startswith("D"):
            risk_text = "、".join(risks or ma_bits or ["趋势确认不足"])
            observe = "、".join(positives[:2]) if positives else "低位指标有修复迹象"
            return f"技术面偏弱：{risk_text}；{observe}，但尚未形成趋势确认。"
        if grade.startswith("C"):
            split = "、".join(risks[:2] or ["趋势与量价信号不一致"])
            edge = "、".join(positives[:3] or [clean or "仍有观察点"])
            return f"技术面分化：{split}；观察点为{edge}。"
        edge = "、".join(positives[:4] or [clean or "趋势和量价结构较好"])
        risk_tail = f"；需跟踪{'、'.join(risks[:2])}" if risks else ""
        return f"技术面优势：{edge}{risk_tail}。"

    def _weighted_total(self, mode: str, scores: dict[str, float], risk_penalty: float) -> float:
        """把各维度分数按上限归一后加权，避免“想给几分就给几分”。"""
        max_scores = {"low": 30, "trend": 25, "momentum": 18, "volume": 20, "volatility": 15, "strength": 15, "tape": 18, "time": 10, "pattern": 10, "value": 15}
        weights = {
            "balanced": {"low": 1.00, "trend": 1.10, "momentum": 0.95, "volume": 1.00, "volatility": 0.75, "strength": 0.95, "tape": 0.60, "time": 0.45, "pattern": 0.55, "value": 0.70},
            "low_position": {"low": 1.45, "trend": 0.90, "momentum": 0.75, "volume": 0.85, "volatility": 0.80, "strength": 0.70, "tape": 0.45, "time": 0.40, "pattern": 0.65, "value": 0.95},
            "oversold_rebound": {"low": 1.35, "trend": 0.90, "momentum": 1.20, "volume": 0.80, "volatility": 0.80, "strength": 0.75, "tape": 0.45, "time": 0.70, "pattern": 0.65, "value": 0.70},
            "trend_volume": {"low": 0.75, "trend": 1.35, "momentum": 1.00, "volume": 1.25, "volatility": 0.70, "strength": 1.10, "tape": 0.70, "time": 0.35, "pattern": 0.65, "value": 0.55},
            "short_swing": {"low": 0.55, "trend": 1.15, "momentum": 1.35, "volume": 1.25, "volatility": 1.00, "strength": 1.10, "tape": 0.90, "time": 0.70, "pattern": 0.80, "value": 0.35},
            "value_quality": {"low": 0.95, "trend": 0.75, "momentum": 0.55, "volume": 0.65, "volatility": 0.65, "strength": 0.65, "tape": 0.35, "time": 0.25, "pattern": 0.35, "value": 1.65},
            "risk_averse": {"low": 1.15, "trend": 1.00, "momentum": 0.75, "volume": 0.80, "volatility": 1.05, "strength": 0.70, "tape": 0.30, "time": 0.40, "pattern": 0.50, "value": 1.05},
            "info_fusion": {"low": 0.90, "trend": 0.90, "momentum": 0.75, "volume": 0.80, "volatility": 0.70, "strength": 0.80, "tape": 0.50, "time": 0.45, "pattern": 0.55, "value": 1.10},
            "etf": {"low": 1.00, "trend": 1.20, "momentum": 0.90, "volume": 1.15, "volatility": 0.85, "strength": 0.90, "tape": 0.55, "time": 0.35, "pattern": 0.45, "value": 0.35},
        }.get(mode, {})
        if not weights:
            weights = {"low": 1.0, "trend": 1.1, "momentum": 0.95, "volume": 1.0, "volatility": 0.75, "strength": 0.95, "tape": 0.60, "time": 0.45, "pattern": 0.55, "value": 0.70}
        weighted = 0.0
        wsum = 0.0
        for key, w in weights.items():
            ms = max_scores.get(key, 1)
            weighted += clamp(scores.get(key, 0) / ms * 100, 0, 100) * w
            wsum += w
        base = weighted / wsum if wsum else 0.0
        # 风险扣分来自 ST/退市、破位、放量下跌、异常量比、极端波动等，直接扣减。
        risk_mult = 1.45 if mode == "risk_averse" else 1.10
        return base - risk_penalty * risk_mult

    def _prioritize_tags(self, tags: list[str], risks: list[str], limit: int = 12) -> list[str]:
        """合并同类标签，避免筛选结果被 MA 标签刷屏。"""
        tags = list(dict.fromkeys([t for t in tags if t]))
        groups: list[tuple[str, list[str]]] = [
            ("低位修复", ["近一年低位", "阶段低位", "中低位", "低位修复中", "高位回撤充分", "回撤较充分", "贴近低点"]),
            ("均线/趋势修复", ["站上MA20", "站上MA60", "MA5上穿MA10", "MA10贴近/站上MA20", "价格站上MA20", "价格站上MA60", "MA20斜率转正", "MA60走平", "均线多头修复"]),
            ("动量改善", ["MACD多头", "MACD柱改善", "RSI健康", "RSI低位回升观察", "RSI/KDJ共振", "KDJ短线转强", "ROC动量为正", "CCI修复"]),
            ("量能配合", ["近5日放量", "量能平稳", "上涨放量", "温和放量", "成交额充足", "流动性较好", "流动性可用", "量比温和放大"]),
            ("资金强度观察", ["MFI资金流健康", "OBV能量潮向上", "价格站上VWAP", "ADX趋势较强"]),
            ("空间结构较好", ["BOLL中轨站稳", "BOLL收口待变盘", "ATR波动可控", "支撑位上方", "箱体上沿突破观察", "斐波回撤较浅", "突破Pivot R1", "站上Pivot中枢", "三角收敛待突破"]),
            ("时间窗口观察", ["TD下跌九转观察", "TD时间序列", "斐波时间窗口", "PSY情绪均衡", "PSY低迷修复观察", "BRAR情绪正常", "CYR市场强弱转正"]),
            ("形态结构观察", ["双底雏形观察", "三角收敛待突破", "ZigZag波段结构可读"]),
        ]
        result: list[str] = []
        used: set[str] = set()
        for label, members in groups:
            hit = [t for t in tags if t in members]
            if hit:
                result.append(label)
                used.update(hit)
        for t in tags:
            if t not in used and t not in result:
                result.append(t)
        return result[:limit]

    def _score_low_position(self, pos60, pos120, pos250, drawdown250, rebound250, last, ma20, ma60) -> tuple[float, list[str]]:
        score = 0.0
        tags: list[str] = []
        p = pos250 if pos250 is not None else pos120
        if p is not None:
            if p <= 20:
                score += 18; tags.append("近一年低位")
            elif p <= 35:
                score += 14; tags.append("阶段低位")
            elif p <= 50:
                score += 9; tags.append("中低位")
            elif p <= 70:
                score += 4
        if drawdown250 is not None:
            dd = abs(min(drawdown250, 0))
            if dd >= 40:
                score += 7; tags.append("高位回撤充分")
            elif dd >= 25:
                score += 5; tags.append("回撤较充分")
            elif dd >= 15:
                score += 2
        if rebound250 is not None:
            if 5 <= rebound250 <= 40:
                score += 4; tags.append("低位修复中")
            elif rebound250 < 5:
                score += 1; tags.append("贴近低点")
            elif rebound250 > 100:
                score -= 2
        if ma20 and last >= ma20:
            score += 3; tags.append("站上MA20")
        if ma60 and last >= ma60:
            score += 2; tags.append("站上MA60")
        return clamp(score, 0, 30), tags

    def _score_trend(self, last, closes, ma5, ma10, ma20, ma60, ma20_prev, ma60_prev, dif, dea, hist, hist_prev, rsi14, boll) -> tuple[float, list[str]]:
        score = 0.0; tags: list[str] = []
        if ma5 and ma10 and ma5 > ma10:
            score += 4; tags.append("MA5上穿MA10")
        if ma10 and ma20 and ma10 >= ma20 * 0.995:
            score += 4; tags.append("MA10贴近/站上MA20")
        if ma20 and last > ma20:
            score += 4; tags.append("价格站上MA20")
        if ma60 and last > ma60:
            score += 3; tags.append("价格站上MA60")
        if ma20 and ma20_prev and ma20 > ma20_prev:
            score += 3; tags.append("MA20斜率转正")
        if ma60 and ma60_prev and ma60 >= ma60_prev:
            score += 2; tags.append("MA60走平")
        if dif is not None and dea is not None:
            if dif > dea:
                score += 3; tags.append("MACD多头")
            if hist is not None and hist_prev is not None and hist > hist_prev:
                score += 2; tags.append("MACD柱改善")
        if rsi14 is not None:
            if 40 <= rsi14 <= 65:
                score += 3; tags.append("RSI健康")
            elif 30 <= rsi14 < 40:
                score += 2; tags.append("RSI低位回升观察")
            elif 65 < rsi14 <= 75:
                score += 1; tags.append("RSI偏强")
        mid = boll.get("mid") if boll else None
        if mid and last > mid:
            score += 2; tags.append("突破BOLL中轨")
        return clamp(score, 0, 25), tags


    def _score_momentum(self, rsi14, kdj_k, kdj_d, kdj_j, wr14, cci20, roc12, momentum10, dif, dea, hist, hist_prev) -> tuple[float, list[str], list[str]]:
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        if rsi14 is not None:
            if 40 <= rsi14 <= 65:
                score += 3; tags.append("RSI健康")
            elif 30 <= rsi14 < 40:
                score += 2; tags.append("RSI低位回升观察")
            elif 65 < rsi14 <= 75:
                score += 1.5; tags.append("RSI偏强")
            elif rsi14 > 80:
                risks.append("RSI严重超买")
            elif rsi14 < 25:
                risks.append("RSI极弱")
        if kdj_k is not None and kdj_d is not None and kdj_j is not None:
            if kdj_k > kdj_d and 20 <= kdj_j <= 100:
                score += 3; tags.append("KDJ短线转强")
            elif kdj_j < 0:
                score += 1; tags.append("KDJ超卖观察")
            elif kdj_j > 110:
                risks.append("KDJ过热")
        if wr14 is not None:
            # Williams %R 范围通常为[-100,0]，越接近0越超买。
            if -80 <= wr14 <= -35:
                score += 2; tags.append("WR修复区间")
            elif wr14 > -15:
                risks.append("WR超买")
            elif wr14 < -90:
                tags.append("WR超卖观察")
        if cci20 is not None:
            if -80 <= cci20 <= 120:
                score += 2; tags.append("CCI修复")
            elif cci20 > 220:
                risks.append("CCI过热")
            elif cci20 < -180:
                risks.append("CCI弱势")
        if roc12 is not None:
            if 0 < roc12 <= 12:
                score += 2; tags.append("ROC动量为正")
            elif roc12 > 25:
                risks.append("ROC短期过热")
            elif roc12 < -12:
                risks.append("ROC动量偏弱")
        if momentum10 is not None:
            if momentum10 > 0:
                score += 1; tags.append("MOM短期改善")
            elif momentum10 < 0:
                score -= 0.5
        if dif is not None and dea is not None:
            if dif > dea:
                score += 2; tags.append("MACD多头")
            if hist is not None and hist_prev is not None:
                if hist > hist_prev:
                    score += 1.5; tags.append("MACD柱改善")
                elif hist < hist_prev and hist < 0:
                    risks.append("MACD动能走弱")
        return clamp(score, 0, 18), list(dict.fromkeys(tags)), list(dict.fromkeys(risks))

    def _score_volatility_space(self, last, atr_pct, boll_width, boll_pos, channel_position, support_dist_pct, resistance_dist_pct) -> tuple[float, list[str], list[str]]:
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        if atr_pct is not None:
            if 1 <= atr_pct <= 5.5:
                score += 4; tags.append("ATR波动可控")
            elif 5.5 < atr_pct <= 8:
                score += 1.5; tags.append("ATR波动偏高")
            elif atr_pct > 8:
                risks.append("ATR高波动风险")
            elif atr_pct < 0.8:
                tags.append("波动率较低")
                score += 1
        if boll_width is not None:
            if boll_width <= 8:
                score += 3; tags.append("BOLL收口待变盘")
            elif 8 < boll_width <= 22:
                score += 2; tags.append("BOLL波动正常")
            elif boll_width > 35:
                risks.append("BOLL通道过宽")
        if boll_pos is not None:
            if 42 <= boll_pos <= 82:
                score += 3; tags.append("BOLL中轨站稳")
            elif boll_pos > 95:
                risks.append("贴近BOLL上轨过热")
            elif boll_pos < 8:
                tags.append("贴近BOLL下轨")
        if channel_position is not None:
            if 25 <= channel_position <= 78:
                score += 2; tags.append("箱体位置适中")
            elif channel_position >= 85:
                if resistance_dist_pct is not None and resistance_dist_pct < 0:
                    score += 1.5; tags.append("箱体上沿突破观察")
                elif resistance_dist_pct is not None and resistance_dist_pct <= 3:
                    risks.append("贴近箱体压力")
                else:
                    risks.append("接近箱体高位")
            elif channel_position <= 15:
                tags.append("接近箱体低位")
                score += 1
        if support_dist_pct is not None and support_dist_pct >= 0:
            if 2 <= support_dist_pct <= 18:
                score += 1.5; tags.append("支撑位上方")
            elif support_dist_pct < 1:
                tags.append("贴近支撑位")
        return clamp(score, 0, 15), list(dict.fromkeys(tags)), list(dict.fromkeys(risks))

    def _score_strength(self, last, vwap20, mfi14, obv_slope, adx14, plus_di, minus_di, q: Quote, closes: list[float], volumes: list[float]) -> tuple[float, list[str], list[str]]:
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        if vwap20 is not None and last:
            if last >= vwap20:
                score += 3; tags.append("价格站上VWAP")
            elif last < vwap20 * 0.97:
                risks.append("价格低于VWAP")
        if mfi14 is not None:
            if 40 <= mfi14 <= 75:
                score += 3; tags.append("MFI资金流健康")
            elif mfi14 > 85:
                risks.append("MFI超买")
            elif mfi14 < 20:
                risks.append("MFI超卖/资金偏弱")
        if obv_slope is not None:
            if obv_slope > 3:
                score += 3; tags.append("OBV能量潮向上")
            elif obv_slope < -8:
                risks.append("OBV能量潮走弱")
        if adx14 is not None and plus_di is not None and minus_di is not None:
            if adx14 >= 22 and plus_di > minus_di:
                score += 4; tags.append("ADX趋势较强")
            elif adx14 >= 28 and plus_di < minus_di:
                risks.append("ADX空头趋势较强")
            elif adx14 < 15:
                tags.append("ADX趋势不明显")
        if q.amount and q.change_pct is not None:
            if q.amount >= 300_000_000 and q.change_pct > 0:
                score += 2; tags.append("资金活跃估算")
            elif q.amount >= 300_000_000 and q.change_pct < -2:
                risks.append("大额成交下跌")
        # 价格与OBV/MFI背离的弱判断，免费数据只能作提示。
        if len(closes) >= 20 and obv_slope is not None and mfi14 is not None:
            price_chg = (closes[-1] / closes[-20] - 1) * 100 if closes[-20] else 0
            if price_chg > 8 and obv_slope < 0:
                risks.append("价格上涨但OBV未确认")
            if price_chg > 8 and mfi14 < 45:
                risks.append("价格上涨但MFI偏弱")
        return clamp(score, 0, 15), list(dict.fromkeys(tags)), list(dict.fromkeys(risks))

    def _score_volume(self, q: Quote, closes: list[float], volumes: list[float], amounts: list[float], vol5_20, amt20) -> tuple[float, list[str], list[str]]:
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        amount = float(q.amount or 0)
        if amount >= 1_000_000_000:
            score += 6; tags.append("成交额充足")
        elif amount >= 300_000_000:
            score += 5; tags.append("流动性较好")
        elif amount >= 100_000_000:
            score += 3; tags.append("流动性可用")
        elif amount >= 30_000_000:
            score += 1
        else:
            risks.append("成交额偏低")
        if q.turnover is not None:
            if 0.5 <= q.turnover <= 8:
                score += 4; tags.append("换手适中")
            elif q.turnover > 15:
                score += 1; risks.append("换手过高")
        if q.volume_ratio is not None:
            if 1.05 <= q.volume_ratio <= 2.5:
                score += 4; tags.append("量比温和放大")
            elif 2.5 < q.volume_ratio <= 5:
                score += 2; tags.append("量比明显放大")
            elif q.volume_ratio > 5:
                risks.append("量比异常偏高")
        if vol5_20 is not None:
            if 1.1 <= vol5_20 <= 2.2:
                score += 4; tags.append("近5日放量")
            elif 0.65 <= vol5_20 < 1.1:
                score += 1; tags.append("量能平稳")
            elif vol5_20 > 3:
                risks.append("近期放量过猛")
        # 区分上涨放量/下跌放量
        if len(closes) >= 2 and len(volumes) >= 20:
            day_up = closes[-1] >= closes[-2]
            last_vol = volumes[-1]
            v20 = sum(volumes[-20:]) / 20
            if day_up and v20 and last_vol > v20 * 1.1:
                score += 2; tags.append("上涨放量")
            if (not day_up) and v20 and last_vol > v20 * 1.6:
                risks.append("放量下跌")
                score -= 2
        return clamp(score, 0, 20), tags, risks

    def _score_tape(self, q: Quote, closes: list[float], highs: list[float], lows: list[float], volumes: list[float], amounts: list[float], vol5_20) -> tuple[float, list[str], list[str], dict]:
        """盘口/量价行为估算。

        说明：公开日线/实时快照没有逐笔成交和 Level-2 委托队列，因此“抢筹、洗盘、对倒、虚假单”只能做风险提示，不能下确定结论。
        """
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        meta: dict[str, str] = {}
        if len(closes) < 25:
            return 0.0, tags, ["盘口行为样本不足"], meta
        last = float(q.last or closes[-1] or 0)
        prev = closes[-2] if len(closes) >= 2 else last
        chg1 = (last / prev - 1) * 100 if prev else 0.0
        chg3 = (last / closes[-4] - 1) * 100 if len(closes) >= 4 and closes[-4] else 0.0
        chg5 = (last / closes[-6] - 1) * 100 if len(closes) >= 6 and closes[-6] else 0.0
        chg20 = (last / closes[-21] - 1) * 100 if len(closes) >= 21 and closes[-21] else 0.0
        high20 = max(highs[-20:]) if highs[-20:] else last
        low20 = min(lows[-20:]) if lows[-20:] else last
        close_pos_day = (last - lows[-1]) / max(highs[-1] - lows[-1], 1e-9) if highs and lows else 0.5
        close_pos20 = (last - low20) / max(high20 - low20, 1e-9)
        turnover = q.turnover if q.turnover is not None else 0.0
        vr = q.volume_ratio if q.volume_ratio is not None else 0.0
        amount = q.amount or 0.0
        # 缩量/放量状态
        if vol5_20 is not None:
            if vol5_20 >= 2.8:
                meta["volume_state"] = "明显放量"
                tags.append("明显放量")
                score += 2
            elif vol5_20 >= 1.15:
                meta["volume_state"] = "温和放量"
                tags.append("温和放量")
                score += 4
            elif vol5_20 <= 0.62:
                meta["volume_state"] = "缩量"
                if -3 <= chg5 <= 3:
                    tags.append("缩量整理")
                    score += 2
                elif chg5 < -3:
                    tags.append("缩量回踩")
                    score += 1
            else:
                meta["volume_state"] = "量能平稳"
                tags.append("量能平稳")
                score += 1
        # 换手状态：妖股/洗盘风险提示
        if turnover:
            if 1 <= turnover <= 8:
                meta["turnover_state"] = "换手健康"
                tags.append("换手健康")
                score += 2
            elif 8 < turnover <= 18:
                meta["turnover_state"] = "高换手"
                tags.append("高换手博弈")
                risks.append("高换手，筹码分歧较大")
            elif turnover > 18:
                meta["turnover_state"] = "极高换手"
                risks.append("极高换手，疑似筹码大幅换手/游资博弈")
        # 盘尾行为只能用日内收盘位置近似
        if close_pos_day >= 0.82 and chg1 > 0 and amount >= 80_000_000:
            meta["close_signal"] = "收盘靠近日内高位"
            tags.append("盘尾强收估算")
            score += 3
        elif close_pos_day <= 0.25 and chg1 < 0:
            meta["close_signal"] = "收盘靠近日内低位"
            risks.append("盘尾走弱估算")
            score -= 2
        else:
            meta["close_signal"] = "收盘位置中性"
        # 妖股急拉后洗盘/退潮信号
        if chg5 >= 18 and (turnover >= 10 or (vol5_20 and vol5_20 >= 2.5)):
            risks.append("短期急拉后高换手，需防洗盘/退潮")
            score -= 4
        if chg20 >= 35 and close_pos20 >= 0.82 and vr >= 3:
            risks.append("高位放量加速，追涨风险升高")
            score -= 4
        if chg5 > 8 and vol5_20 is not None and vol5_20 < 0.75:
            risks.append("缩量上涨，量价确认不足")
            score -= 2
        if chg1 < -2 and vol5_20 is not None and vol5_20 > 1.6:
            risks.append("放量下跌/资金分歧")
            score -= 3
        if abs(chg1) < 0.8 and vr >= 3.5 and turnover >= 8:
            risks.append("放量滞涨，疑似分歧或对倒，需Level-2核验")
            score -= 2
        # 主力持仓/虚假单：没有可靠公开字段，只提供可验证说明
        if vr >= 5 and amount >= 300_000_000 and abs(chg1) <= 1.5:
            risks.append("异常量比但价格不动，可能存在对倒/虚假活跃，需逐笔成交确认")
        return max(0.0, min(18.0, score + 6.0)), list(dict.fromkeys(tags)), list(dict.fromkeys(risks)), meta


    def _score_time_dimension(self, td_signal: str | None, fib_time: dict, psy12, br26, ar26, cyr13) -> tuple[float, list[str], list[str]]:
        """时间/情绪维度：TD序列、斐波那契时间、PSY/BRAR/CYR。"""
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        td_text = str(td_signal or "")
        if "下跌TD9" in td_text:
            score += 3; tags.append("TD下跌九转观察")
        elif "上涨TD9" in td_text:
            risks.append("TD上涨九转风险")
        elif "TD" in td_text and td_text not in {"TD中性", "样本不足"}:
            score += 1; tags.append("TD时间序列")
        if isinstance(fib_time, dict) and "接近" in str(fib_time.get("signal")):
            score += 2; tags.append("斐波时间窗口")
        if psy12 is not None:
            if 35 <= psy12 <= 65:
                score += 2; tags.append("PSY情绪均衡")
            elif psy12 < 25:
                score += 1.5; tags.append("PSY低迷修复观察")
            elif psy12 > 80:
                risks.append("PSY情绪过热")
        if br26 is not None and ar26 is not None:
            if 70 <= br26 <= 250 and 70 <= ar26 <= 250:
                score += 1.5; tags.append("BRAR情绪正常")
            elif br26 > 400 or ar26 > 400:
                risks.append("BRAR情绪过热")
        if cyr13 is not None:
            if cyr13 > 0:
                score += 1.5; tags.append("CYR市场强弱转正")
            elif cyr13 < -1.5:
                risks.append("CYR短期转弱")
        return clamp(score, 0, 10), list(dict.fromkeys(tags)), list(dict.fromkeys(risks))

    def _score_pattern_dimension(self, price_pattern: str | None, pattern_signal: str | None, fibonacci_signal: str | None, pivot_point, pivot_r1, pivot_s1, last, zigs: list) -> tuple[float, list[str], list[str]]:
        """空间/形态维度：形态、斐波回调、Pivot、ZigZag结构。"""
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        pattern_text = str(price_pattern or "")
        signal_text = str(pattern_signal or "")
        fib_text = str(fibonacci_signal or "")
        if "双底" in pattern_text:
            score += 3; tags.append("双底雏形观察")
        elif "双顶" in pattern_text:
            risks.append("双顶雏形风险")
        elif "三角" in pattern_text:
            score += 1.5; tags.append("三角收敛待突破")
        if "回撤较浅" in fib_text or "修复较强" in fib_text:
            score += 2; tags.append("斐波回撤较浅")
        elif "61.8" in fib_text and "风险" in fib_text:
            risks.append("跌破斐波61.8%风险")
        if pivot_point and last:
            if pivot_r1 and last > pivot_r1:
                score += 2; tags.append("突破Pivot R1")
            elif pivot_point and last > pivot_point:
                score += 1; tags.append("站上Pivot中枢")
            elif pivot_s1 and last < pivot_s1:
                risks.append("跌破Pivot S1")
        if len(zigs) >= 4:
            score += 1; tags.append("ZigZag波段结构可读")
        return clamp(score, 0, 10), list(dict.fromkeys(tags)), list(dict.fromkeys(risks))

    def _build_indicator_signals(self, matrix: dict) -> list[dict]:
        """把指标矩阵变成前端可读的信号清单，避免标签解释空白。"""
        signals: list[dict] = []
        lib = TechnicalIndicatorLibraryService()
        for dimension, vals in (matrix or {}).items():
            if not isinstance(vals, dict):
                continue
            for name, value in vals.items():
                spec = lib.get(str(name)) or {}
                signals.append({
                    "dimension": dimension,
                    "indicator": name,
                    "value": value,
                    "formula": spec.get("formula", "见指标知识库"),
                    "judgment": spec.get("judgment", "结合多指标共振判断"),
                    "application": spec.get("application", "技术面辅助分析"),
                    "caveat": spec.get("caveat", "单一指标不能作为买卖依据"),
                })
        return signals

    def _score_value(self, q: Quote) -> tuple[float, list[str], list[str]]:
        score = 0.0; tags: list[str] = []; risks: list[str] = []
        if q.asset_type == AssetType.ETF:
            score += 10; tags.append("ETF品种")
            if q.amount and q.amount >= 50_000_000:
                score += 5; tags.append("ETF流动性可用")
            return clamp(score, 0, 15), tags, risks
        if q.total_market_cap:
            if q.total_market_cap >= 50_000_000_000:
                score += 4; tags.append("大中市值")
            elif q.total_market_cap >= 8_000_000_000:
                score += 3; tags.append("市值可用")
            else:
                risks.append("市值偏小")
        if q.pe_dynamic is not None and q.pe_dynamic > 0:
            if 5 <= q.pe_dynamic <= 45:
                score += 5; tags.append("PE区间可接受")
            elif 45 < q.pe_dynamic <= 80:
                score += 2; risks.append("PE偏高")
            elif q.pe_dynamic > 120:
                risks.append("PE过高")
        if q.pb is not None and q.pb > 0:
            if 0.6 <= q.pb <= 6:
                score += 4; tags.append("PB区间可接受")
            elif q.pb > 10:
                risks.append("PB过高")
        if q.float_market_cap and q.float_market_cap >= 3_000_000_000:
            score += 2
        return clamp(score, 0, 15), tags, risks

    def _score_risk(self, q: Quote, last, closes, ma20, ma60, rsi14, drawdown250, vol5_20, amt20) -> tuple[float, list[str]]:
        risk = 0.0; flags: list[str] = []
        name = (q.name or "").upper()
        if "ST" in name or "退" in name:
            risk += 30; flags.append("ST/退市风险")
        if q.amount and q.amount < 30_000_000:
            risk += 6; flags.append("成交额过低")
        if q.change_pct is not None and q.change_pct <= -7:
            risk += 5; flags.append("当日大跌")
        if ma20 and last < ma20 * 0.93:
            risk += 4; flags.append("明显跌破MA20")
        if ma60 and last < ma60 * 0.88:
            risk += 5; flags.append("明显跌破MA60")
        if rsi14 is not None and rsi14 < 25:
            risk += 4; flags.append("RSI极弱")
        if drawdown250 is not None and drawdown250 < -65:
            risk += 5; flags.append("长期弱势深跌")
        if vol5_20 is not None and vol5_20 > 4 and q.change_pct is not None and q.change_pct < 0:
            risk += 5; flags.append("放量下跌风险")
        if q.volume_ratio is not None and q.volume_ratio > 8:
            risk += 4; flags.append("量比异常")
        return clamp(risk, 0, 30), flags

    def _grade(self, score: float) -> str:
        if score >= 85:
            return "A+ 重点"
        if score >= 75:
            return "A 关注"
        if score >= 65:
            return "B 观察"
        if score >= 50:
            return "C 备选"
        return "D 剔除"

    def _reason(self, tags: list[str], risks: list[str], low: float, trend: float, volume: float, value: float, risk: float, momentum: float = 0.0, volatility: float = 0.0, strength: float = 0.0) -> str:
        main = "、".join(tags[:6]) if tags else "暂未出现明显优势信号"
        score_txt = f"低位{low:.0f}/趋势{trend:.0f}/动量{momentum:.0f}/量能{volume:.0f}/波动空间{volatility:.0f}/资金强度{strength:.0f}/估值流动性{value:.0f}/风险扣{risk:.0f}"
        if risks:
            return f"{main}；风险：{'、'.join(risks[:5])}；{score_txt}"
        return f"{main}；{score_txt}"
