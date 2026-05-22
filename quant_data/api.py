from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time
from statistics import mean

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from quant_data import __version__
from quant_data.market_calendar import MarketCalendar
from quant_data.models import Bar, IntradayPoint, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.services.screener_service import ScreenerConfig, ScreenerService
from quant_data.services.watchlist_service import WatchlistService
from quant_data.services.score_history_service import ScoreHistoryService
from quant_data.services.annotation_service import AnnotationService
from quant_data.services.strategy_library_service import StrategyLibraryService
from quant_data.services.technical_indicator_library import TechnicalIndicatorLibraryService
from quant_data.services.source_knowledge_service import SourceKnowledgeService
from quant_data.services.wordsource_system_service import WordSourceSystemService
from quant_data.services.source_registry import SourceRegistryService
from quant_data.services.technical_factor_registry import TechnicalFactorRegistryService
from quant_data.services.candidate_pool_service import CandidatePoolService
from quant_data.services.market_regime_service import MarketRegimeService
from quant_data.services.trading_framework_service import compute_indicator50_snapshot
from quant_data.services.fundamental_library_service import FundamentalLibraryService
from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.info_analysis_service import InfoAnalysisService
from quant_data.services.company_profile_service import CompanyProfileService
from quant_data.screener_ui import build_screener_ui
from quant_data.info_ui import build_info_ui
from quant_data.ui_v22 import build_ui_v22


service = MarketDataService()
screener_service = ScreenerService(service)
watchlist_service = WatchlistService()
score_history_service = ScoreHistoryService()
annotation_service = AnnotationService()
strategy_library_service = StrategyLibraryService()
technical_indicator_library_service = TechnicalIndicatorLibraryService()
source_knowledge_service = SourceKnowledgeService()
fundamental_library_service = FundamentalLibraryService()
news_service = NewsAnalysisService()
info_analysis_service = InfoAnalysisService(service, news_service)
company_profile_service = CompanyProfileService()
market_calendar = MarketCalendar()
wordsource_system_service = WordSourceSystemService()
source_registry_service = SourceRegistryService()
technical_factor_registry_service = TechnicalFactorRegistryService()
candidate_pool_service = CandidatePoolService()
market_regime_service = MarketRegimeService()
app = FastAPI(title="Quant Data Gateway", version=__version__, description="A股/基金实时行情、分时、K线与后续量化系统的数据网关")

def _make_snapshot_id(symbol: str | None = None, limit: int | None = None) -> str:
    core = datetime.now().strftime("%Y%m%d%H%M%S")
    sym = str(symbol or "batch").strip() or "batch"
    lim = str(limit or "")
    return f"snap-{core}-{sym}-{lim}".rstrip("-")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    # 避免浏览器默认请求 favicon 时在控制台产生 404 噪声。
    return Response(status_code=204)

@app.middleware("http")
async def no_cache_for_api(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/") or request.url.path in {"/ui"} or request.url.path.startswith("/chart/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _detect_market(symbol: str | None = None, fallback: str = "CN") -> str:
    return market_calendar.detect_market(symbol, fallback=fallback)


def _market_session(market: str = "CN") -> dict:
    return market_calendar.session(market)


def _now_cn() -> datetime:
    return datetime.fromisoformat(_market_session("CN")["now"])


def _calc_summary(bars: list[Bar]) -> dict:
    if not bars:
        return {
            "ma5": None,
            "ma10": None,
            "ma20": None,
            "recent_high": None,
            "recent_low": None,
            "last_close": None,
            "price_position_60": None,
            "volume_ma5": None,
            "volume_ma20": None,
        }
    closes = [_safe_float(b.close) for b in bars]
    highs = [_safe_float(b.high) for b in bars]
    lows = [_safe_float(b.low) for b in bars]
    volumes = [_safe_float(b.volume) for b in bars]
    recent_high = max(highs[-60:]) if highs else None
    recent_low = min(lows[-60:]) if lows else None
    denom = (recent_high - recent_low) if recent_high is not None and recent_low is not None else 0
    last_close = closes[-1]
    price_position_60 = ((last_close - recent_low) / denom * 100) if denom else None

    def ma(values, n):
        return mean(values[-n:]) if len(values) >= n else None

    return {
        "ma5": ma(closes, 5),
        "ma10": ma(closes, 10),
        "ma20": ma(closes, 20),
        "recent_high": recent_high,
        "recent_low": recent_low,
        "last_close": last_close,
        "price_position_60": price_position_60,
        "volume_ma5": ma(volumes, 5),
        "volume_ma20": ma(volumes, 20),
    }


def _sync_daily_bar_with_quote(bars: list[Bar], q: Quote, frame: str, adjust: str) -> tuple[list[Bar], bool, str]:
    """用实时行情修正不复权日K最后一根，保持行情表与日K收盘价一致。"""
    if frame != "1d" or adjust not in {"none", "", None} or not bars:
        return bars, False, "not_daily_or_adjusted"
    last_price = _safe_float(q.last)
    if last_price <= 0:
        return bars, False, "invalid_quote"
    today = _now_cn().date()
    out = list(bars)
    last = out[-1]
    last_date = last.ts.date()
    open_price = _safe_float(q.open, last.open or last_price) or last.open or last_price
    high_price = max(_safe_float(last.high), _safe_float(q.high), last_price, open_price)
    low_candidates = [x for x in [_safe_float(last.low), _safe_float(q.low), last_price, open_price] if x > 0]
    low_price = min(low_candidates) if low_candidates else last_price
    volume = _safe_float(q.volume, last.volume)
    amount = _safe_float(q.amount, last.amount)
    if last_date == today:
        out[-1] = replace(
            last,
            open=open_price,
            high=high_price,
            low=low_price,
            close=last_price,
            volume=volume or last.volume,
            amount=amount or last.amount,
            turnover=q.turnover if q.turnover is not None else last.turnover,
            change_pct=q.change_pct if q.change_pct is not None else last.change_pct,
            source=f"{last.source}+realtime",
        )
        return out, True, "update_today_bar"
    session = _market_session(q.market)
    if session.get("is_trading") and today > last_date:
        out.append(
            Bar(
                symbol=q.symbol,
                frame="1d",
                ts=datetime.combine(today, time(0, 0)),
                open=open_price,
                high=max(_safe_float(q.high), last_price, open_price),
                low=min(x for x in [_safe_float(q.low), last_price, open_price] if x > 0),
                close=last_price,
                volume=volume,
                amount=amount,
                turnover=q.turnover,
                change_pct=q.change_pct,
                source="realtime_virtual_daily",
            )
        )
        return out, True, "append_virtual_today_bar"
    return out, False, "not_today"


def _quote_extra(q: Quote) -> dict:
    pre = _safe_float(q.pre_close)
    last = _safe_float(q.last)
    limit_rate = 0.2 if q.symbol.startswith(("300", "301", "688", "689")) else 0.1
    limit_up = round(pre * (1 + limit_rate), 2) if pre else None
    limit_down = round(pre * (1 - limit_rate), 2) if pre else None
    avg_price = None
    if q.amount and q.volume:
        # A 股公开源常用 volume=手，amount=元；均价≈成交额/(成交量*100)。
        denom = _safe_float(q.volume) * 100
        avg_price = round(_safe_float(q.amount) / denom, 3) if denom else None
    return {
        "limit_up": limit_up,
        "limit_down": limit_down,
        "avg_price": avg_price,
        "real_turnover": q.turnover,
        "limit_rate": limit_rate,
    }


def _timeline_with_fallback(symbol: str, q: Quote | None, force: bool = False) -> list[IntradayPoint]:
    """获取真实分时数据。

    重要：这里不再用实时行情硬造 09:30/当前/15:00 三个点。
    那种 quote_fallback 会在休市时画出一条假的斜线，误导用户。
    分时数据缺失时，后端只返回真实缓存或空列表；前端显示“暂无真实分时数据/保留缓存”。
    """
    points = service.get_intraday(symbol, force_refresh=force)
    # 过滤旧版本曾经产生的 quote_fallback/单点快照，避免假分时继续显示。
    clean = [p for p in (points or []) if not str(getattr(p, "source", "")).startswith("quote_fallback")]
    if len(clean) < 2:
        return []
    return clean


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "version": __version__, "server_time": datetime.now().isoformat(timespec="seconds"), "session": _market_session("CN"), "cache": service.cache.stats()}




@app.get("/api/provider/warnings")
def provider_warnings() -> dict:
    warnings = getattr(service.providers, "warnings", [])[-30:]
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "data": [w.__dict__ for w in warnings],
        "note": "这里记录最近的数据源降级/超时情况；行情/K线/分时会优先使用缓存兜底。",
    }

@app.get("/api/session")
def session(market: str = "CN") -> dict:
    return {"ok": True, "data": _market_session(market)}


@app.get("/api/calendar/status")
def calendar_status(symbol: str | None = None, market: str | None = None) -> dict:
    m = (market or _detect_market(symbol)).upper()
    return {"ok": True, "data": _market_session(m)}


@app.get("/api/calendar/markets")
def calendar_markets() -> dict:
    return {"ok": True, "data": {m: _market_session(m) for m in ["CN", "HK", "US"]}}


@app.get("/api/quote/{symbol}")
def quote(symbol: str, force: bool = False) -> dict:
    q = service.get_quote(symbol, force_refresh=force)
    data = q.to_dict()
    data["extra"] = _quote_extra(q)
    return {"ok": True, "server_time": datetime.now().isoformat(timespec="seconds"), "force": force, "session": _market_session(q.market), "data": data}


@app.get("/api/quotes")
def quotes(symbols: str = Query(..., description="逗号分隔，如 300750,600519"), force: bool = False) -> dict:
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    qs = service.get_quotes(symbol_list, force_refresh=force)
    data = []
    for q in qs:
        item = q.to_dict()
        item["extra"] = _quote_extra(q)
        data.append(item)
    return {"ok": True, "server_time": datetime.now().isoformat(timespec="seconds"), "force": force, "session": _market_session("CN"), "count": len(data), "data": data}


@app.get("/api/timeline/{symbol}")
def timeline(symbol: str, force: bool = False) -> dict:
    q = None
    try:
        q = service.get_quote(symbol, force_refresh=force)
    except Exception:
        q = None
    points = _timeline_with_fallback(symbol, q, force=force)
    market = q.market if q else _detect_market(symbol)
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "force": force,
        "symbol": symbol,
        "session": _market_session(market),
        "quote": q.to_dict() if q else None,
        "quote_extra": _quote_extra(q) if q else {},
        "count": len(points),
        "data": [p.to_dict() for p in points],
    }


@app.get("/api/kline/{symbol}")
def kline(symbol: str, frame: str = "1d", limit: int = 260, adjust: str = "none", force: bool = False, sync_quote: bool = True) -> dict:
    if frame not in {"1d", "1w", "1M", "1mo"}:
        frame = "1d"
    if frame == "1mo":
        frame = "1M"
    q = service.get_quote(symbol, force_refresh=force) if sync_quote else None
    bars = service.get_kline(symbol, frame=frame, limit=limit, adjust=adjust, force_refresh=force)
    synced = False
    sync_reason = "disabled"
    if q is not None:
        bars, synced, sync_reason = _sync_daily_bar_with_quote(bars, q, frame, adjust)
    return {"ok": True, "server_time": datetime.now().isoformat(timespec="seconds"), "force": force, "adjust": adjust, "frame": frame, "synced": synced, "sync_reason": sync_reason, "count": len(bars), "data": [b.to_dict() for b in bars]}


@app.get("/api/detail/{symbol}")
def detail(symbol: str, frame: str = "1d", limit: int = 260, adjust: str = "none", force: bool = False, include_timeline: bool = False) -> dict:
    if frame not in {"1d", "1w", "1M", "1mo"}:
        frame = "1d"
    if frame == "1mo":
        frame = "1M"
    quote_error = None
    try:
        q = service.get_quote(symbol, force_refresh=force)
    except Exception as exc:
        q = None
        quote_error = str(exc)
    bars = service.get_kline(symbol, frame=frame, limit=limit, adjust=adjust, force_refresh=force)
    if q is None and bars:
        b = bars[-1]
        q = Quote(symbol=symbol, name=symbol, ts=b.ts, last=b.close, pre_close=b.open, open=b.open, high=b.high, low=b.low, volume=b.volume, amount=b.amount, change=b.close-b.open, change_pct=b.change_pct, turnover=b.turnover, source="bar_snapshot")
    if q is not None:
        bars, synced, sync_reason = _sync_daily_bar_with_quote(bars, q, frame, adjust)
        points = _timeline_with_fallback(symbol, q, force=force) if include_timeline else []
        qd = q.to_dict(); qd["extra"] = _quote_extra(q)
        session = _market_session(q.market)
        out_symbol = q.symbol
    else:
        synced, sync_reason, points, qd, session, out_symbol = False, "quote_unavailable", [], None, _market_session(_detect_market(symbol)), symbol
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "force": force,
        "adjust": adjust,
        "symbol": out_symbol,
        "quote": qd,
        "quote_error": quote_error,
        "frame": frame,
        "count": len(bars),
        "bars": [b.to_dict() for b in bars],
        "timeline": [p.to_dict() for p in points],
        "summary": _calc_summary(bars),
        "session": session,
        "synced": synced,
        "sync_reason": sync_reason,
    }


@app.get("/api/market/stocks")
def market_stocks(page: int = 1, page_size: int = 100) -> dict:
    qs = service.get_market_snapshot(page=page, page_size=page_size)
    data = []
    for q in qs:
        item = q.to_dict()
        item["extra"] = _quote_extra(q)
        data.append(item)
    return {"ok": True, "count": len(data), "data": data}


@app.get("/api/search")
def search(keyword: str, limit: int = 30) -> dict:
    assets = service.search_assets(keyword, limit=limit)
    return {"ok": True, "count": len(assets), "data": [a.to_dict() for a in assets]}


def _parse_symbol_text(symbols: str | None) -> list[str]:
    return [x.strip() for x in (symbols or "").replace("，", ",").replace("\n", ",").split(",") if x.strip()]


@app.get("/api/watchlist")
def watchlist_get() -> dict:
    data = watchlist_service.list()
    return {"ok": True, "data": data}


@app.post("/api/watchlist/add")
def watchlist_add(symbols: str = Query(..., description="逗号分隔，如 300750,600519")) -> dict:
    data = watchlist_service.add(_parse_symbol_text(symbols))
    return {"ok": True, "message": "已加入实时监测列表", "data": data}


@app.post("/api/watchlist/remove")
def watchlist_remove(symbols: str = Query(..., description="逗号分隔，如 300750,600519")) -> dict:
    data = watchlist_service.remove(_parse_symbol_text(symbols))
    return {"ok": True, "message": "已从实时监测列表移除", "data": data}


@app.post("/api/watchlist/set")
def watchlist_set(symbols: str = Query(..., description="逗号分隔，如 300750,600519")) -> dict:
    data = watchlist_service.set(_parse_symbol_text(symbols))
    return {"ok": True, "message": "实时监测列表已保存", "data": data}


@app.get("/jump/watchlist")
def jump_watchlist(symbols: str = Query(..., description="加入监测列表后跳转到行情页")):
    watchlist_service.add(_parse_symbol_text(symbols))
    return RedirectResponse(url=f"/ui?symbol={_parse_symbol_text(symbols)[0] if _parse_symbol_text(symbols) else '300750'}")


@app.get("/api/score/history/{symbol}")
def score_history(symbol: str, days: int = 90) -> dict:
    data = score_history_service.history(symbol, days=days)
    return {"ok": True, "symbol": symbol, "count": len(data), "data": data}


@app.get("/api/score/latest")
def score_latest(limit: int = 100, score_date: str | None = None) -> dict:
    data = score_history_service.latest(limit=limit, score_date=score_date)
    return {"ok": True, "count": len(data), "data": data}




@app.get("/api/wordsource/coverage")
def wordsource_coverage() -> dict:
    return {
        "ok": True,
        "version": __version__,
        "source_registry": source_registry_service.coverage_matrix(),
        "disabled_sources": source_registry_service.disabled_sources(),
        "source_plan": source_registry_service.plan_for_target(120),
        "technical_factor_coverage": technical_factor_registry_service.coverage(),
        "technical_factors_by_category": technical_factor_registry_service.by_category(),
        "note": "WordSource V1 已把消息面、技术面、风格资金面、量化交易文档映射为可运行服务与API。",
    }


@app.get("/api/wordsource/report/{symbol}")
def wordsource_report(symbol: str, limit: int = 260, adjust: str = "qfq", force: bool = False, info_limit: int = 120) -> dict:
    q = service.get_quote(symbol, force_refresh=force)
    bars = service.get_kline(symbol, frame="1d", limit=max(120, min(int(limit or 260), 520)), adjust=adjust, force_refresh=force)
    opens = [float(b.open or 0) for b in bars]
    highs = [float(b.high or 0) for b in bars]
    lows = [float(b.low or 0) for b in bars]
    closes = [float(b.close or 0) for b in bars]
    volumes = [float(b.volume or 0) for b in bars]
    amounts = [float(b.amount or 0) for b in bars]
    if q.last and closes:
        closes[-1] = float(q.last)
    indicator_snapshot = compute_indicator50_snapshot(opens, highs, lows, closes, volumes, amounts)
    news_items = []
    try:
        ir = info_analysis_service.analyze(symbol, name=q.name, limit=max(30, min(int(info_limit or 120), 300)), force=force)
        nr = ir.get("news", {}) if isinstance(ir, dict) else {}
        raw = nr.get("items") or ir.get("items") or []
        if isinstance(raw, list):
            news_items = raw
    except Exception:
        news_items = []
    report = wordsource_system_service.build_report(q, bars, indicator_snapshot=indicator_snapshot, base_score=None, tags=[], risk_flags=[], news_items=news_items)
    return {"ok": True, "data": report}


@app.get("/api/wordsource/candidates")
def wordsource_candidates(max_pages: int = 2, page_size: int = 100, max_items: int = 120) -> dict:
    quotes = []
    for page in range(1, max(1, min(int(max_pages or 2), 20)) + 1):
        block = service.get_market_snapshot(page=page, page_size=max(20, min(int(page_size or 100), 500)))
        quotes.extend(block or [])
    pool = candidate_pool_service.build(quotes, max_items=max(20, min(int(max_items or 120), 300)))
    regime = market_regime_service.analyze_quotes(quotes)
    return {"ok": True, "market_regime": regime, "candidate_pool": pool}

@app.get("/api/screener/strategies")
def screener_strategies() -> dict:
    return {
        "ok": True,
        "data": [
            {"key": "balanced", "name": "综合平衡", "description": "低位、趋势、量价、估值/流动性与风险扣分综合排序。"},
            {"key": "low_position", "name": "低位修复优先", "description": "提高低位与回撤充分权重，同时要求存在修复迹象。"},
            {"key": "oversold_rebound", "name": "超跌反弹观察", "description": "低位与RSI修复权重较高，适合寻找超跌后修复标的。"},
            {"key": "trend_volume", "name": "趋势放量优先", "description": "提高均线、MACD、RSI、成交活跃度权重。"},
            {"key": "short_swing", "name": "短线强势/异动", "description": "强化趋势、成交额、放量与动量，风险扣分也较高。"},
            {"key": "value_quality", "name": "价值质量稳健", "description": "提高估值、流动性和市值稳定性权重，降低单纯题材追涨影响。"},
            {"key": "risk_averse", "name": "保守风控优先", "description": "提高风险扣分权重，适合做观察池初筛。"},
            {"key": "info_fusion", "name": "信息面融合优先", "description": "技术底分偏稳健，配合启用信息面评分后进行新闻/公告/财报融合排序。"},
            {"key": "etf", "name": "ETF关注模式", "description": "弱化估值字段，重点考察位置、趋势和流动性。"},
        ],
    }


@app.get("/api/screener/run")
def screener_run(
    universe: str = "custom",
    symbols: str = "300750,600519,000001,159915,510300",
    max_items: int = 30,
    max_pages: int = 1,
    page_size: int = 100,
    kline_limit: int = 260,
    kline_adjust: str = "qfq",
    min_score: float = 0,
    min_amount: float = 0,
    include_stocks: bool = True,
    include_etf: bool = True,
    force_quotes: bool = False,
    force_kline: bool = False,
    mode: str = "balanced",
    strategies: str = "",
    enable_news: bool = False,
    info_limit: int = 180,
    info_weight: float | None = None,
) -> dict:
    symbol_list = [x.strip() for x in symbols.replace("，", ",").replace("\n", ",").split(",") if x.strip()]
    config = ScreenerConfig(
        universe=universe,
        symbols=symbol_list,
        max_items=max_items,
        max_pages=max_pages,
        page_size=page_size,
        kline_limit=kline_limit,
        kline_adjust=kline_adjust,
        min_score=min_score,
        min_amount=min_amount,
        include_stocks=include_stocks,
        include_etf=include_etf,
        force_quotes=force_quotes,
        force_kline=force_kline,
        mode=mode,
        strategies=[x.strip() for x in str(strategies or "").split(",") if x.strip()],
        enable_news=bool(enable_news),
    )
    result = screener_service.run(config)
    selected_strategies = [x.strip() for x in str(strategies or "").split(",") if x.strip()]
    result["selected_strategies"] = selected_strategies
    snapshot_id = _make_snapshot_id("screener", info_limit if enable_news else None)
    result["snapshot_id"] = snapshot_id
    result["strategy_note"] = "V3.15 默认使用前复权日K参与筛选评分；启用信息面时筛选页与详情页共享 snapshot_id 与 info_limit；搜索引擎关键词页禁用，全球/行业事件需经业务相关性映射后才扰动评分。"
    result["news_enabled"] = bool(enable_news)
    if enable_news:
        # 信息面只对筛选后的候选股低频分析，避免对全市场盲目抓取。
        # info_limit 与前端/详情页一致，避免“详情页抓了300条而筛选仍按120条”的内外评分不一致。
        info_count = 0
        info_limit = max(30, min(int(info_limit or 180), 500))
        selected_mode = str(mode or "balanced")
        selected_strategies_set = set(selected_strategies)
        if info_weight is None:
            # V3.13：消息面启用后默认权重提高；若使用信息面融合模式/事件驱动策略，前沿要闻和宏观行业映射对短线排序影响更明显。
            calc_info_weight = 0.45 if (selected_mode == "info_fusion" or "info_fusion" in selected_strategies_set or "event_driven" in selected_strategies_set) else 0.35
        else:
            calc_info_weight = max(0.05, min(float(info_weight), 0.65))
        result["info_weight"] = calc_info_weight
        result["info_limit"] = info_limit
        for item in result.get("data", [])[: min(20, len(result.get("data", [])))]:
            try:
                # V3.0：默认对候选股抓取/复用更多中文信息。limit 是聚合样本上限，不等于前端展示条数。
                ir = info_analysis_service.analyze(item.get("symbol", ""), name=item.get("name"), limit=info_limit, force=False)
                profile = company_profile_service.get_profile(item.get("symbol", ""), force=False)
                ir["snapshot_id"] = snapshot_id
                nr = ir.get("news", {})
                if isinstance(nr, dict):
                    nr["snapshot_id"] = snapshot_id
                detail_url = f"/info?symbol={item.get('symbol','')}&name={item.get('name','')}&limit={info_limit}&snapshot_id={snapshot_id}"
                item["news"] = {
                    "snapshot_id": snapshot_id,
                    "detail_url": detail_url,
                    "news_score": nr.get("news_score"),
                    "sentiment": nr.get("sentiment"),
                    "count": nr.get("count"),
                    "summary": nr.get("summary"),
                    "positive_count": nr.get("positive_count"),
                    "negative_count": nr.get("negative_count"),
                    "neutral_count": nr.get("neutral_count"),
                    "avg_credibility": nr.get("avg_credibility"),
                    "official_count": nr.get("official_count"),
                    "official_negative_count": nr.get("official_negative_count"),
                    "date_unknown_count": nr.get("date_unknown_count"),
                    "recent_count": nr.get("recent_count"),
                    "keywords": nr.get("keywords", [])[:12],
                    "category_counts": nr.get("category_counts", []),
                    "dimension_counts": nr.get("dimension_counts", []),
                    "source_counts": nr.get("source_counts", []),
                    "time_counts": nr.get("time_counts", []),
                    "risk_flags": nr.get("risk_flags", []),
                    "avg_fake_risk": nr.get("avg_fake_risk"),
                    "avg_relevance": nr.get("avg_relevance"),
                    "avg_impact": nr.get("avg_impact"),
                    "sentiment_cn": nr.get("sentiment_cn"),
                    "weighted_positive": nr.get("weighted_positive"),
                    "weighted_negative": nr.get("weighted_negative"),
                    "event_family_counts": nr.get("event_family_counts", []),
                    "duplicate_groups": nr.get("duplicate_groups", []),
                    "items": [],
                    "detail_only": True,
                    "sources_used": nr.get("sources_used", []),
                    "sources_status": nr.get("sources_status", []),
                    "credibility_method": nr.get("credibility_method"),
                    "scoring_note": nr.get("scoring_note"),
                }
                item["info"] = {
                    "snapshot_id": snapshot_id,
                    "detail_url": detail_url,
                    "info_score": ir.get("info_score"),
                    "summary": ir.get("summary"),
                    "finance": ir.get("finance", {}),
                    "policy": ir.get("policy", {}),
                    "breakdown": ir.get("breakdown", []),
                    "time_counts": ir.get("time_counts", []),
                    "risk_flags": ir.get("risk_flags", []),
                    "evidence_counts": ir.get("evidence_counts", {}),
                    "data_quality": ir.get("data_quality", {}),
                    "cache_info": ir.get("cache_info", {}),
                    "reuse_note": ir.get("reuse_note"),
                    "message_framework": ir.get("message_framework", {}),
                    "source_policy": ir.get("source_policy", {}),
                    "scoring_model": ir.get("scoring_model", {}),
                    "global_news_used": ir.get("global_news_used", {}),
                    "profile": profile,
                }
                base = float(item.get("total_score") or 0)
                info_score = float(ir.get("info_score") or 50)
                item["technical_score"] = round(base, 2)
                item["total_score_with_info"] = round(max(0, min(100, base * (1 - calc_info_weight) + info_score * calc_info_weight)), 2)
                item["info_weight"] = calc_info_weight
                item["score_formula"] = f"技术/量价底分×{1-calc_info_weight:.2f} + 信息面分×{calc_info_weight:.2f}"
                item["total_score_with_news"] = item["total_score_with_info"]
                item["total_score"] = item["total_score_with_info"]
                if nr.get("sentiment") == "positive":
                    item.setdefault("tags", []).append("信息面偏正面")
                elif nr.get("sentiment") == "negative":
                    item.setdefault("risk_flags", []).append("信息面偏负面")
                for rf in ir.get("risk_flags", [])[:3]:
                    item.setdefault("risk_flags", []).append(rf)
                info_count += 1
            except Exception as exc:
                item["info"] = {"error": str(exc)[:180], "info_score": None}
        result["news_analyzed_count"] = info_count
        result["info_analyzed_count"] = info_count
        result["news_note"] = f"已对筛选结果前20只候选股进行信息面评分；抓取上限={info_limit}，融合权重={calc_info_weight:.0%}，snapshot_id={snapshot_id}。V3.15 筛选页不展示长篇新闻，只保留信息面详情入口；清洗页头/页脚/JS脏数据，按事件簇去重，并区分 publish_time/event_time/crawl_time。"
        result["data"].sort(key=lambda x: x.get("total_score_with_info", x.get("total_score", 0)), reverse=True)
    try:
        saved = score_history_service.save_results(result.get("data", []), mode=mode)
        result["score_history_saved"] = saved
        result["score_history_note"] = "评分历史按天保存；同一股票同一天重复筛选会覆盖当天记录。"
    except Exception as exc:
        result["score_history_saved"] = 0
        result["score_history_error"] = str(exc)[:220]
    return result



@app.post("/api/watchlist/clear")
def watchlist_clear() -> dict:
    data = watchlist_service.set([])
    return {"ok": True, "message": "实时监测列表已清空", "data": data}


@app.get("/api/orderbook/{symbol}")
def orderbook(symbol: str, force: bool = False) -> dict:
    session = calendar_status(symbol=symbol)["data"]
    allow_external = bool(force or session.get("can_refresh"))
    book = service.get_order_book(symbol, allow_external=allow_external)
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "symbol": symbol,
        "market_status": session.get("status"),
        "market_label": session.get("label"),
        "skipped_external": not allow_external,
        "note": "非交易时段默认不主动请求外部盘口接口" if not allow_external else "",
        "data": book.to_dict() if book else None,
    }


@app.get("/api/signals/{symbol}")
def signals(symbol: str) -> dict:
    # 图表策略信号预留：后续回测/实盘/AI策略推荐生成的买卖点统一返回到这里。
    return {"ok": True, "symbol": symbol, "data": {"buy": [], "sell": [], "warning": [], "strategy": []}}


@app.get("/api/annotations/{symbol}")
def annotations_get(symbol: str) -> dict:
    return {"ok": True, "symbol": symbol, "data": annotation_service.list(symbol)}


@app.post("/api/annotations/{symbol}")
def annotations_add(symbol: str, item: dict = Body(default_factory=dict)) -> dict:
    return {"ok": True, "symbol": symbol, "data": annotation_service.add(symbol, item)}


@app.post("/api/annotations/{symbol}/clear")
def annotations_clear(symbol: str) -> dict:
    return {"ok": True, "symbol": symbol, "data": annotation_service.clear(symbol)}




@app.get("/api/source-knowledge/coverage")
def source_knowledge_coverage() -> dict:
    return {"ok": True, "data": source_knowledge_service.coverage()}


@app.get("/api/source-knowledge")
def source_knowledge_all() -> dict:
    return {"ok": True, "coverage": source_knowledge_service.coverage(), "data": source_knowledge_service.get_all()}


@app.get("/api/source-knowledge/doc/{key}")
def source_knowledge_doc(key: str, max_chars: int = Query(12000, ge=500, le=200000)) -> dict:
    return source_knowledge_service.source_doc_text(key, max_chars=max_chars)


@app.get("/api/strategy/library")
def strategy_library() -> dict:
    return {"ok": True, "data": strategy_library_service.list()}


@app.get("/api/technical/indicators")
def technical_indicators() -> dict:
    return {"ok": True, "coverage": technical_indicator_library_service.coverage(), "word_source_catalog": technical_indicator_library_service.word_source_catalog(), "data": technical_indicator_library_service.list()}


@app.get("/api/technical/indicators/by-category")
def technical_indicators_by_category() -> dict:
    return {"ok": True, "coverage": technical_indicator_library_service.coverage(), "data": technical_indicator_library_service.by_category()}




@app.get("/api/fundamental/library")
def fundamental_library() -> dict:
    return {"ok": True, "data": fundamental_library_service.list(), "categories": fundamental_library_service.by_category(), "source_tiers": fundamental_library_service.source_tiers(), "industry_event_rules": fundamental_library_service.industry_event_rules(), "checklist": fundamental_library_service.checklist()}


@app.get("/api/fundamental/library/by-category")
def fundamental_library_by_category() -> dict:
    return {"ok": True, "data": fundamental_library_service.by_category(), "source_tiers": fundamental_library_service.source_tiers(), "checklist": fundamental_library_service.checklist()}


@app.get("/api/fundamental/event-map")
def fundamental_event_map(text: str, stock_text: str = "") -> dict:
    return {"ok": True, "data": fundamental_library_service.map_event_to_industries(text, stock_text=stock_text)}


@app.post("/api/strategy/custom/validate")
def strategy_custom_validate(payload: dict = Body(default_factory=dict)) -> dict:
    code = str((payload or {}).get("code") or "")
    return strategy_library_service.validate_custom_code(code)


@app.get("/api/news/analyze/{symbol}")
def news_analyze(symbol: str, name: str | None = None, limit: int = 120, force: bool = False, snapshot_id: str | None = None) -> dict:
    qname = name
    if not qname:
        try:
            qname = service.get_quote(symbol, force_refresh=False).name
        except Exception:
            qname = symbol
    data = news_service.analyze(symbol, name=qname, limit=limit, force=force)
    sid = snapshot_id or _make_snapshot_id(symbol, limit)
    data["snapshot_id"] = sid
    return {"ok": True, "symbol": symbol, "snapshot_id": sid, "data": data}





@app.get("/api/news/global")
def global_news(limit: int = 80, force: bool = False) -> dict:
    data = news_service.fetch_global_news(limit=limit, force=force)
    return {"ok": True, "data": data}


@app.get("/api/company/profile/store/stats")
def company_profile_store_stats(symbol: str | None = None) -> dict:
    return {"ok": True, "data": company_profile_service.stats(symbol)}


@app.get("/api/company/profile/{symbol}")
def company_profile(symbol: str, force: bool = False) -> dict:
    data = company_profile_service.get_profile(symbol, force=force)
    return {"ok": True, "symbol": symbol, "data": data}


@app.get("/api/stock/overview/{symbol}")
def stock_overview(symbol: str, force: bool = False, news_limit: int = 60, global_limit: int = 30, snapshot_id: str | None = None) -> dict:
    """股票详情聚合：行情 + 公司简介 + 个股信息面 + 全球/国内要闻。"""
    quote_data = None
    quote_error = None
    try:
        q = service.get_quote(symbol, force_refresh=force)
        quote_data = q.to_dict()
        quote_data["extra"] = _quote_extra(q)
        name = q.name
    except Exception as exc:
        quote_error = str(exc)[:220]
        name = symbol
    profile = company_profile_service.get_profile(symbol, force=force)
    try:
        if profile.get("name"):
            name = profile.get("name")
        stock_news = news_service.analyze(symbol, name=name, limit=news_limit, force=force)
    except Exception as exc:
        stock_news = {"error": str(exc)[:220], "items": []}
    global_items = news_service.fetch_global_news(limit=global_limit, force=force)
    sid = snapshot_id or _make_snapshot_id(symbol, news_limit)
    if isinstance(stock_news, dict):
        stock_news["snapshot_id"] = sid
    return {
        "ok": True,
        "symbol": symbol,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "force": force,
        "snapshot_id": sid,
        "data": {
            "quote": quote_data,
            "quote_error": quote_error,
            "profile": profile,
            "stock_news": stock_news,
            "global_news": global_items,
            "fundamental_framework": fundamental_library_service.checklist(),
            "source_tiers": fundamental_library_service.source_tiers(),
        },
    }


@app.get("/api/info/analyze/{symbol}")
def info_analyze(symbol: str, name: str | None = None, limit: int = 120, force: bool = False, snapshot_id: str | None = None) -> dict:
    qname = name
    if not qname:
        try:
            qname = service.get_quote(symbol, force_refresh=False).name
        except Exception:
            qname = symbol
    data = info_analysis_service.analyze(symbol, name=qname, limit=limit, force=force)
    sid = snapshot_id or _make_snapshot_id(symbol, limit)
    data["snapshot_id"] = sid
    if isinstance(data.get("news"), dict):
        data["news"]["snapshot_id"] = sid
    data["detail_contract"] = {"snapshot_id": sid, "limit": limit, "note": "筛选页 detail_url 可把 snapshot_id 与 limit 传入详情页，保证同一次筛选和详情展示口径一致。"}
    return {"ok": True, "symbol": symbol, "snapshot_id": sid, "data": data}

@app.get("/api/news/search")
def news_search(keyword: str, limit: int = 80, force: bool = False) -> dict:
    data = news_service.search_keyword(keyword, limit=limit, force=force)
    return {"ok": True, "data": data}


@app.get("/api/info/items/{symbol}")
def info_items(
    symbol: str,
    limit: int = 80,
    history_days: int = 3650,
    page: int | None = None,
    page_size: int = 30,
    sort: str = "desc",
    category: str | None = None,
    source: str | None = None,
    include_unknown_date: bool = True,
) -> dict:
    # 兼容旧接口：未传 page 时仍返回旧版 list；传 page 时返回分页对象。
    if page is None:
        data = news_service.store.list_items(symbol, limit=limit, include_history_days=history_days)
        return {"ok": True, "symbol": symbol, "count": len(data), "data": data, "store": news_service.store.stats(symbol)}
    data = news_service.store.list_items_paged(
        symbol, page=page, page_size=page_size, include_history_days=history_days,
        sort=sort, category=category, source=source, include_unknown_date=include_unknown_date
    )
    return {"ok": True, "symbol": symbol, "data": data}


@app.get("/api/info/event-test")
def info_event_test(title: str, symbol: str = "600519", name: str = "贵州茅台") -> dict:
    # 调试信息面语义关系：用于检查“增持别的股票/当前标的退出持仓”等复杂标题。
    item = news_service._score_item(title, "", "手动测试", None, "", symbol, name, source_type="news")
    return {"ok": True, "data": item.to_dict()}


@app.get("/api/info/store/stats")
def info_store_stats(symbol: str | None = None) -> dict:
    return {"ok": True, "data": news_service.store.stats(symbol)}


def _tag_explain_from_result(item: dict, tag: str) -> dict:
    def f(x, default=None):
        try:
            return float(item.get(x)) if item.get(x) is not None else default
        except Exception:
            return default
    tag = str(tag or "")
    metrics = []
    spec = technical_indicator_library_service.get(tag) or {}
    conclusion = "该标签为规则化筛选信号，用于辅助排序，不构成买卖建议。"
    if spec:
        conclusion += f" 关联指标：{spec.get('name')}。"
    why = []
    annotations = []
    if "低位" in tag or "回撤" in tag or "低点" in tag or "贴近低点" in tag:
        metrics = [
            {"name": "近60日位置", "value": item.get("pos60"), "unit": "%", "better": "越低表示越靠近阶段低位"},
            {"name": "近120日位置", "value": item.get("pos120"), "unit": "%", "better": "越低表示中期位置越低"},
            {"name": "近250日位置", "value": item.get("pos250"), "unit": "%", "better": "低于35%通常认为处于中低位"},
            {"name": "距250日高点回撤", "value": item.get("drawdown250"), "unit": "%", "better": "绝对值越大说明回撤更充分；默认基于前复权K线"},
            {"name": "距250日低点反弹", "value": item.get("rebound250"), "unit": "%", "better": "过小表示仍贴近低点，过大则低位属性减弱"},
            {"name": "K线复权口径", "value": item.get("kline_adjust") or "qfq", "unit": "", "better": "qfq=前复权，能降低除权缺口对回撤/低位判断的污染"},
        ]
        why.append("系统用60/120/250日价格分位、高位回撤和低点反弹共同判断低位属性；筛选默认采用前复权日K，避免除权、分红、送转导致的假回撤。")
        if f("pos250", 999) <= 35: why.append("当前近250日位置偏低，符合低位观察条件。")
        if f("drawdown250", 0) <= -25: why.append("相对一年高点回撤较充分。")
        annotations.append({"type":"range", "label":"低位区间", "note":"可在K线中标注近250日高低点和当前位置。"})
    elif "MA" in tag or "均线" in tag or "趋势" in tag or "站上" in tag or "斜率" in tag:
        metrics = [
            {"name": "最新价", "value": item.get("last"), "unit": "元", "better": "与均线比较"},
            {"name": "MA5", "value": item.get("ma5"), "unit": "元"},
            {"name": "MA10", "value": item.get("ma10"), "unit": "元"},
            {"name": "MA20", "value": item.get("ma20"), "unit": "元"},
            {"name": "MA60", "value": item.get("ma60"), "unit": "元"},
        ]
        why.append("系统用MA5/MA10/MA20/MA60的相对位置、斜率和BOLL中轨判断趋势修复。")
        if f("last", 0) and f("ma20", 0) and f("last") >= f("ma20"): why.append("价格已站上或贴近MA20，短中期修复强于完全破位状态。")
        annotations.append({"type":"line", "label":"MA对比", "note":"后续可把MA20/MA60交叉点作为图表标注。"})
    elif any(k in tag for k in ["动量", "MACD", "RSI", "KDJ", "WR", "CCI", "ROC", "MOM", "超买", "超卖"]):
        metrics = [
            {"name": "RSI14", "value": item.get("rsi14"), "unit": "", "better":"30-40偏超卖修复，40-65较健康，过高需防追涨"},
            {"name": "KDJ K/D/J", "value": f"{item.get('kdj_k','--')} / {item.get('kdj_d','--')} / {item.get('kdj_j','--')}", "unit": "", "better":"K>D且J未极端过热时为短线转强"},
            {"name": "WR14", "value": item.get("wr14"), "unit": "", "better":"接近0偏超买，低于-80偏超卖"},
            {"name": "CCI20", "value": item.get("cci20"), "unit": "", "better":"-100到100为常态，过高/过低提示极端"},
            {"name": "ROC12", "value": item.get("roc12"), "unit": "%", "better":"温和为正表示动量改善，过高需防追涨"},
            {"name": "MOM10", "value": item.get("momentum10"), "unit": "元"},
            {"name": "DIF/DEA/MACD柱", "value": f"{item.get('macd_dif','--')} / {item.get('macd_dea','--')} / {item.get('macd_hist','--')}", "unit": ""},
            {"name": "动量分", "value": item.get("momentum_score"), "unit": "分"},
        ]
        why.append("动量类标签综合 RSI、KDJ、WR、CCI、ROC、MOM 与 MACD，避免只靠单一均线判断。")
        why.append("超买/超卖指标在强趋势中可能钝化，因此系统把它作为共振证据，而不是单独买卖信号。")
    elif any(k in tag for k in ["ATR", "BOLL", "箱体", "支撑", "阻力", "波动", "空间", "通道"]):
        metrics = [
            {"name": "ATR14", "value": item.get("atr14"), "unit": "元", "better":"用于衡量平均真实波幅"},
            {"name": "ATR占价格", "value": item.get("atr_pct"), "unit": "%", "better":"过高代表波动/止损空间变大"},
            {"name": "BOLL中/上/下轨", "value": f"{item.get('boll_mid','--')} / {item.get('boll_upper','--')} / {item.get('boll_lower','--')}", "unit": ""},
            {"name": "BOLL带宽", "value": item.get("boll_width"), "unit": "%", "better":"收口代表波动压缩，扩张代表趋势/风险放大"},
            {"name": "BOLL位置", "value": item.get("boll_position"), "unit": "%", "better":"0接近下轨，100接近上轨"},
            {"name": "60日支撑/压力", "value": f"{item.get('support60','--')} / {item.get('resistance60','--')}", "unit": "元"},
            {"name": "箱体位置", "value": item.get("channel_position"), "unit": "%"},
            {"name": "波动空间分", "value": item.get("volatility_score"), "unit": "分"},
        ]
        why.append("空间/波动类标签综合 ATR、BOLL 带宽、BOLL位置、60日支撑压力和箱体位置，用来判断变盘、突破和止损空间。")
    elif any(k in tag for k in ["资金", "OBV", "MFI", "VWAP", "ADX", "能量潮", "强度"]):
        metrics = [
            {"name": "VWAP20", "value": item.get("vwap20"), "unit": "元", "better":"价格站上VWAP代表成本线之上"},
            {"name": "MFI14", "value": item.get("mfi14"), "unit": "", "better":"40-75相对健康，过高/过低提示资金极端"},
            {"name": "OBV十日斜率", "value": item.get("obv_slope"), "unit": "%", "better":"为正代表能量潮改善"},
            {"name": "ADX14", "value": item.get("adx14"), "unit": "", "better":"大于20-25代表趋势强度上升"},
            {"name": "+DI / -DI", "value": f"{item.get('plus_di','--')} / {item.get('minus_di','--')}", "unit": ""},
            {"name": "资金强度分", "value": item.get("strength_score"), "unit": "分"},
        ]
        why.append("资金强度类标签使用 MFI、OBV、VWAP、ADX/+DI/-DI 和成交额变化进行估算。")
        why.append("免费公开源没有逐笔成交和Level-2队列，因此这里只能做资金强度估算，不能直接断言主力真实意图。")
    elif any(k in tag for k in ["成交", "换手", "量", "流动", "盘尾", "放量", "缩量", "对倒", "洗盘", "妖股", "高换手", "量比"]):
        metrics = [
            {"name": "成交额", "value": item.get("amount"), "unit": "元", "better":"成交额越高，流动性越好，但高位天量需谨慎"},
            {"name": "换手率", "value": item.get("turnover"), "unit": "%", "better":"1%-8%较健康，过高代表筹码分歧/游资博弈"},
            {"name": "量比", "value": item.get("volume_ratio"), "unit": "", "better":"温和放大较好，异常放大需看价格是否确认"},
            {"name": "近5/20日量比", "value": item.get("vol5_20"), "unit": "倍", "better":"约1.1-2.2为温和放量，过高可能过热"},
            {"name": "盘口行为分", "value": item.get("tape_score"), "unit": "分"},
            {"name": "换手状态", "value": item.get("turnover_state"), "unit": ""},
            {"name": "量能状态", "value": item.get("volume_state"), "unit": ""},
            {"name": "收盘位置", "value": item.get("close_signal"), "unit": ""},
        ]
        why.append("量价/盘口标签综合成交额、换手率、量比、近5/20日成交量、当日收盘在日内区间的位置进行估算。")
        why.append("公开免费行情没有逐笔成交和Level-2委托队列，所以‘主力抢筹、虚假单、左手倒右手’只能标为需核验风险，不能直接下确定结论。")
    elif any(k in tag for k in ["PE", "PB", "市值", "估值", "财报", "大中市值"]):
        metrics = [
            {"name": "动态PE", "value": item.get("pe_dynamic"), "unit": "倍", "better":"需结合行业，不是越低越好"},
            {"name": "PB", "value": item.get("pb"), "unit": "倍", "better":"资产型行业更有参考意义"},
            {"name": "总市值", "value": item.get("total_market_cap"), "unit": "元", "better":"大中市值通常流动性和稳定性更好"},
            {"name": "流通市值", "value": item.get("float_market_cap"), "unit": "元", "better":"过小更容易剧烈波动"},
        ]
        why.append("估值/市值标签用PE、PB、总市值、流通市值和成交活跃度进行粗筛；财报质量由信息面和公司画像继续补充。")
        if "大中市值" in tag: why.append("当前总市值达到规则阈值，因此标为大中市值；它只代表规模属性，不代表一定低风险。")
    elif any(k in tag for k in ["TD", "斐波时间", "PSY", "BRAR", "CYR", "时间窗口", "情绪温度", "心理"]):
        metrics = [
            {"name": "TD序列", "value": item.get("td_signal"), "unit": "", "better":"TD9只表示变盘窗口，不直接代表方向"},
            {"name": "PSY12", "value": item.get("psy12"), "unit": "%", "better":"25以下偏悲观，75以上偏乐观/过热"},
            {"name": "BR26/AR26", "value": f"{item.get('br26','--')} / {item.get('ar26','--')}", "unit": ""},
            {"name": "CYR13", "value": item.get("cyr13"), "unit": "%", "better":"为正说明短期强弱改善"},
            {"name": "时间分", "value": item.get("time_score"), "unit": "分"},
        ]
        why.append("时间/情绪类标签来自TD序列、斐波那契时间窗口、PSY心理线、BRAR情绪指标和CYR强弱指标。")
        why.append("时间窗口只提示可能变盘，不直接判断涨跌方向，必须配合趋势、量价和风险项。")
    elif any(k in tag for k in ["形态", "双底", "双顶", "三角", "ZigZag", "Pivot", "斐波回撤", "空间结构"]):
        metrics = [
            {"name": "价格形态", "value": item.get("price_pattern"), "unit": ""},
            {"name": "形态信号", "value": item.get("pattern_signal"), "unit": ""},
            {"name": "斐波最近位", "value": item.get("fibonacci_nearest"), "unit": ""},
            {"name": "斐波信号", "value": item.get("fibonacci_signal"), "unit": ""},
            {"name": "Pivot/R1/S1", "value": f"{item.get('pivot_point','--')} / {item.get('pivot_r1','--')} / {item.get('pivot_s1','--')}", "unit": ""},
            {"name": "ZigZag点数", "value": item.get("zigzag_count"), "unit": "个"},
            {"name": "形态分", "value": item.get("pattern_score"), "unit": "分"},
        ]
        why.append("形态/空间类标签来自双顶双底/三角收敛雏形、ZigZag过滤、斐波那契回调和Pivot支撑阻力。")
        why.append("当前形态识别是公开日线的弱识别，只作为观察标签，突破仍需成交量和后续K线确认。")
    elif any(k in tag for k in ["信息", "政策", "新闻", "公告", "监管", "减持", "诉讼", "亏损", "负面", "正面"]):
        info = item.get("info") or {}
        news = item.get("news") or {}
        metrics = [
            {"name": "信息面分", "value": info.get("info_score") or news.get("news_score"), "unit": "分"},
            {"name": "事件级正/负权重", "value": f"{news.get('weighted_positive','--')} / {news.get('weighted_negative','--')}", "unit": ""},
            {"name": "新闻条数", "value": news.get("count"), "unit": "条"},
            {"name": "官方/高可信", "value": (info.get("evidence_counts") or {}).get("high_confidence_items") or news.get("official_count"), "unit": "条"},
            {"name": "重复事件组", "value": len(news.get("duplicate_groups") or []), "unit": "组"},
        ]
        why.append("信息面采用事件级去重：同一亏损、问询、减持、订单等多源转载只计一次主权重，避免重复标题放大影响。")
        why.append("近期官方信息权重更高，社区/传闻只作为舆情观察，不进入核心利多利空。")
    else:
        metrics = [
            {"name": "低位分", "value": item.get("low_score"), "unit": "分"},
            {"name": "趋势分", "value": item.get("trend_score"), "unit": "分"},
            {"name": "动量分", "value": item.get("momentum_score"), "unit": "分"},
            {"name": "量能分", "value": item.get("volume_score"), "unit": "分"},
            {"name": "波动空间分", "value": item.get("volatility_score"), "unit": "分"},
            {"name": "资金强度分", "value": item.get("strength_score"), "unit": "分"},
            {"name": "盘口行为分", "value": item.get("tape_score"), "unit": "分"},
            {"name": "时间分", "value": item.get("time_score"), "unit": "分"},
            {"name": "形态分", "value": item.get("pattern_score"), "unit": "分"},
            {"name": "估值流动性分", "value": item.get("value_score"), "unit": "分"},
            {"name": "风险扣分", "value": item.get("risk_penalty"), "unit": "分"},
        ]
        why.append("该标签来自当前筛选结果的多因子评分矩阵；若某指标为空，通常是公开源没有返回对应字段或K线数量不足。")
    if spec:
        why.insert(0, f"指标知识库：公式={spec.get('formula')}；评判标准={spec.get('judgment')}；应用场景={spec.get('application')}。")
        if spec.get('caveat'):
            why.append(f"使用限制：{spec.get('caveat')}。")
    return {"tag": tag, "symbol": item.get("symbol"), "name": item.get("name"), "conclusion": conclusion, "why": why, "metrics": metrics, "indicator_spec": spec, "indicator_matrix": item.get("indicator_matrix"), "indicator_signals": item.get("indicator_signals", [])[:80], "annotations_preview": annotations, "future_interface": "后续可将 annotations_preview 写入 /api/annotations/{symbol}，在K线图上标注信号点、区间和买卖点。"}


@app.get("/api/screener/explain/{symbol}")
def screener_explain(symbol: str, tag: str = "", mode: str = "balanced", strategies: str = "") -> dict:
    q = service.get_quote(symbol, force_refresh=False)
    bars = service.get_kline(symbol, frame="1d", limit=260, adjust="none", force_refresh=False)
    r = screener_service.analyze(q, bars, mode=mode, strategies=[x.strip() for x in strategies.split(",") if x.strip()]).to_dict()
    if tag:
        return {"ok": True, "data": _tag_explain_from_result(r, tag), "result": r}
    tags = r.get("tags", []) + r.get("risk_flags", [])
    return {"ok": True, "symbol": symbol, "count": len(tags), "data": [_tag_explain_from_result(r, t) for t in tags], "result": r}



@app.get("/api/technical/drawdown/verify/{symbol}")
def verify_drawdown(symbol: str, adjust: str = "qfq", limit: int = 260, force: bool = False) -> dict:
    """验证近250日回撤率口径。

    定义：drawdown250 = 当前价 / 近250个交易日最高价 - 1。
    默认使用前复权 K 线，避免分红送转造成的假回撤。
    """
    code = normalize_symbol(symbol)
    quote = service.get_quote(code, force_refresh=force)
    bars = service.get_kline(code, frame="1d", limit=max(80, min(int(limit or 260), 520)), adjust=adjust, force_refresh=force)
    closes = [float(b.close or 0) for b in bars if b.close is not None]
    highs = [float(b.high or 0) for b in bars if b.high is not None and float(b.high or 0) > 0]
    lows = [float(b.low or 0) for b in bars if b.low is not None and float(b.low or 0) > 0]
    last = _safe_float(quote.last) or (closes[-1] if closes else 0.0)
    if last > 0 and highs:
        highs[-1] = max(highs[-1], last, _safe_float(quote.high))
    if last > 0 and lows:
        lows[-1] = min(x for x in [lows[-1], last, _safe_float(quote.low)] if x > 0)
    wh = highs[-250:] if len(highs) >= 60 else highs
    wl = lows[-250:] if len(lows) >= 60 else lows
    high250 = max(wh) if wh else None
    low250 = min(wl) if wl else None
    drawdown250 = (last / high250 - 1) * 100 if high250 and last else None
    rebound250 = (last / low250 - 1) * 100 if low250 and last else None
    return {
        "ok": True,
        "data": {
            "symbol": code,
            "name": quote.name,
            "adjust": adjust,
            "limit": limit,
            "bars_count": len(bars),
            "bars": len(bars),
            "last_close": round(last, 4),
            "last": round(last, 4),
            "high_250": round(high250, 4) if high250 else None,
            "high250": round(high250, 4) if high250 else None,
            "low_250": round(low250, 4) if low250 else None,
            "low250": round(low250, 4) if low250 else None,
            "drawdown250": round(drawdown250, 2) if drawdown250 is not None else None,
            "rebound250": round(rebound250, 2) if rebound250 is not None else None,
            "data_source": sorted(list({getattr(b, "source", "") for b in bars if getattr(b, "source", "")})),
            "basis": "drawdown250 = 当前收盘价 / 近250日前复权最高价 - 1；负值表示回撤；默认 adjust=qfq。",
            "formula": "drawdown250 = current_last / max(high[-250:]) - 1，单位%；负值表示回撤",
            "note": "筛选页默认 qfq 前复权；该接口用于核对回撤率是否由复权口径、缓存或实时价同步造成差异。",
        },
    }

@app.get("/info", response_class=HTMLResponse)
def info_page() -> str:
    return build_info_ui()


@app.get("/screener", response_class=HTMLResponse)
def screener_page() -> str:
    return build_screener_ui()


@app.get("/chart/{symbol}", response_class=HTMLResponse)
def chart_page(symbol: str, frame: str = "time") -> str:
    return _build_ui(initial_symbol=symbol, full=True, initial_frame=frame)


@app.get("/ui", response_class=HTMLResponse)
def ui(symbol: str = "300750") -> str:
    return _build_ui(initial_symbol=symbol or "300750", full=False, initial_frame="time")


def _build_ui(initial_symbol: str, full: bool = False, initial_frame: str = "time") -> str:
    return build_ui_v22(initial_symbol=initial_symbol, full=full, initial_frame=initial_frame)
