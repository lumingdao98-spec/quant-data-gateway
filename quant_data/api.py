from __future__ import annotations

import re
from dataclasses import fields, replace
from datetime import datetime, time
from pathlib import Path
from statistics import mean

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from quant_data import __version__
from quant_data.market_calendar import MarketCalendar
from quant_data.models import AssetType, Bar, IntradayPoint, Quote
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
from quant_data.services.market_behavior_engine import MarketBehaviorEngine
from quant_data.services.cache_state_service import CacheStateService
from quant_data.services.fundamental_library_service import FundamentalLibraryService
from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.info_analysis_service import InfoAnalysisService
from quant_data.services.company_profile_service import CompanyProfileService
from quant_data.services.global_industry_mapper import GlobalIndustryMapper
from quant_data.services.technical_factor_engine import TechnicalFactorEngine
from quant_data.services.backtest_service import BacktestConfig as LegacyBacktestConfig, BacktestService
from quant_data.backtest import BacktestConfig as V319BacktestConfig, StrategySignal
from quant_data.backtest.engine import BacktestEngine
from quant_data.backtest.optimizer import ParameterOptimizer
from quant_data.backtest.paper_broker import PaperBroker
from quant_data.backtest.report import build_report
from quant_data.backtest.storage import BacktestStorage
from quant_data.backtest.walk_forward import WalkForwardValidator
from quant_data.screener_ui import build_screener_ui
from quant_data.info_ui import build_info_ui
from quant_data.ui_v22 import build_ui_v22
from quant_data.backtest_ui import build_backtest_trades_ui, build_backtest_ui, build_paper_ui


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
global_industry_mapper = GlobalIndustryMapper()
market_calendar = MarketCalendar()
wordsource_system_service = WordSourceSystemService()
source_registry_service = SourceRegistryService()
technical_factor_registry_service = TechnicalFactorRegistryService()
candidate_pool_service = CandidatePoolService()
market_regime_service = MarketRegimeService()
market_behavior_engine = MarketBehaviorEngine()
cache_state_service = CacheStateService()
technical_factor_engine = TechnicalFactorEngine()
backtest_service = BacktestService()
backtest_engine_v319 = BacktestEngine(service)
backtest_storage_v319 = BacktestStorage()
paper_broker_v319 = PaperBroker(V319BacktestConfig())
FALLBACK_STRATEGIES = [
    {"key": "low_position", "name": "低位修复", "category": "低位/修复", "description": "低位区间、RSI/KDJ 修复与均线距离改善。", "enabled": True, "default_weight": 1.0, "tags": ["low", "repair"]},
    {"key": "avoid_chasing_high", "name": "高位追高过滤", "category": "风控过滤", "description": "过滤高位滞涨、压力位过近和追高风险。", "enabled": True, "default_weight": 1.0, "tags": ["risk", "high"]},
    {"key": "ma_repair", "name": "均线修复", "category": "K线趋势", "description": "MA5/10/20 斜率和价格回到均线体系。", "enabled": True, "default_weight": 1.0, "tags": ["ma"]},
    {"key": "macd_cross", "name": "MACD金叉/多头", "category": "趋势跟随", "description": "DIF/DEA 金叉、多头排列与零轴位置。", "enabled": True, "default_weight": 1.0, "tags": ["macd"]},
    {"key": "macd_hist_turn", "name": "MACD柱改善", "category": "动量/反转", "description": "MACD 柱体收敛、翻红或负柱缩短。", "enabled": True, "default_weight": 1.0, "tags": ["momentum"]},
    {"key": "volume_breakout", "name": "温和放量", "category": "量价/盘口", "description": "成交额、量比和均量温和改善，避免异常巨量。", "enabled": True, "default_weight": 1.0, "tags": ["volume"]},
    {"key": "risk_control", "name": "风险扣分", "category": "风控过滤", "description": "行为风险、跌破关键位、假突破和高换手不涨扣分。", "enabled": True, "default_weight": 1.0, "tags": ["risk"]},
    {"key": "atr_risk", "name": "ATR波动过滤", "category": "回测/风控/执行", "description": "ATR 与近期振幅过高时降低优先级。", "enabled": True, "default_weight": 1.0, "tags": ["atr"]},
    {"key": "position_stop", "name": "仓位与止损", "category": "回测/风控/执行", "description": "结合支撑、ATR 与等级输出仓位/止损建议。", "enabled": True, "default_weight": 1.0, "tags": ["position"]},
]
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


def _parse_cny_amount(value) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value) if float(value) > 0 else None
    text = str(value).replace(",", "").strip()
    if not text or text in {"--", "-"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    num = float(match.group(0))
    multiplier = 1.0
    if "万亿" in text or "萬億" in text or "兆" in text:
        multiplier = 1_000_000_000_000.0
    elif "亿" in text or "億" in text:
        multiplier = 100_000_000.0
    elif "万" in text or "萬" in text:
        multiplier = 10_000.0
    return num * multiplier if num > 0 else None


def _apply_company_profile_metrics(q: Quote) -> Quote:
    if q.asset_type == AssetType.ETF or str(q.symbol).startswith(("15", "51", "56", "58")):
        return q
    needs_profile = any(
        getattr(q, field, None) in (None, 0, "")
        for field in ["total_market_cap", "float_market_cap", "pe_dynamic"]
    )
    if not needs_profile:
        return q
    try:
        profile = company_profile_service.get_profile(q.symbol, force=False)
    except Exception:
        return q
    updates: dict = {}
    total_cap = _parse_cny_amount(profile.get("total_market_value"))
    float_cap = _parse_cny_amount(profile.get("float_market_value"))
    last = _safe_float(q.last)
    if not q.total_market_cap and total_cap:
        updates["total_market_cap"] = total_cap
    if not q.float_market_cap and float_cap:
        updates["float_market_cap"] = float_cap
        updates["circulating_market_cap"] = float_cap
    if not q.pe_dynamic and last > 0:
        eps_candidates = []
        summary = profile.get("financial_summary") or {}
        if isinstance(summary, dict):
            eps_candidates.append(summary.get("latest_eps") or summary.get("eps"))
        for row in profile.get("financial_history") or []:
            if isinstance(row, dict):
                eps_candidates.append(row.get("eps"))
        eps_values = [_safe_float(x) for x in eps_candidates if abs(_safe_float(x)) > 1e-9]
        ttm_like = [x for x in eps_values if abs(x) >= 0.5]
        eps = max(ttm_like or eps_values or [0.0], key=lambda x: abs(x))
        if abs(eps) > 1e-9:
            updates["pe_dynamic"] = round(last / eps, 4)
    if last > 0:
        if updates.get("total_market_cap") and not q.total_share:
            updates["total_share"] = updates["total_market_cap"] / last
        if updates.get("float_market_cap") and not q.float_share:
            updates["float_share"] = updates["float_market_cap"] / last
    if not updates:
        return q
    sources = dict(q.metric_sources or {})
    for key in updates:
        if key in {"total_market_cap", "total_share"}:
            sources.setdefault(key, "company_profile")
        if key in {"float_market_cap", "circulating_market_cap", "float_share"}:
            sources.setdefault(key, "company_profile")
        if key == "pe_dynamic":
            sources.setdefault("pe_ttm", "company_profile_eps")
    reasons = [
        r for r in (q.metric_missing_reasons or [])
        if not any(token in str(r) for token in ["总市值", "流通市值", "total_market_cap", "float_market_cap"])
    ]
    if "pe_dynamic" in updates:
        reasons = [r for r in reasons if not any(token in str(r) for token in ["PE", "pe_ttm", "pe_dynamic", "市盈"])]
    updates["metric_sources"] = sources
    updates["metric_missing_reasons"] = reasons
    updates["source"] = f"{q.source}+company_profile" if q.source else "company_profile"
    return replace(q, **updates)


def _detect_market(symbol: str | None = None, fallback: str = "CN") -> str:
    return market_calendar.detect_market(symbol, fallback=fallback)


def _market_session(market: str = "CN") -> dict:
    return market_calendar.session(market)


def _now_cn() -> datetime:
    return datetime.fromisoformat(_market_session("CN")["now"])


def _market_index_bars(limit: int = 90) -> dict[str, list[Bar]]:
    bars_by_key: dict[str, list[Bar]] = {}
    for spec in getattr(market_regime_service, "index_specs", []):
        try:
            bars = service.providers.get_kline(spec.symbol, frame="1d", limit=limit, adjust="none")
            if bars:
                bars_by_key[spec.key] = bars
        except Exception:
            continue
    return bars_by_key


def _kline_key(symbol: str, frame: str, adjust: str, limit: int | None = None) -> str:
    return f"{symbol}:{frame}:{adjust or 'none'}"


def _market_cap_style(cap: float | None) -> str | None:
    value = _safe_float(cap)
    if value <= 0:
        return None
    if value < 5_000_000_000:
        return "微盘"
    if value < 20_000_000_000:
        return "小盘"
    if value < 100_000_000_000:
        return "中盘"
    if value < 500_000_000_000:
        return "大盘"
    return "超大盘"


def _quote_from_dict(data: dict | None) -> Quote | None:
    if not isinstance(data, dict) or not data.get("symbol"):
        return None
    try:
        ts_raw = data.get("ts") or datetime.now().isoformat(timespec="seconds")
        ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        ts = datetime.now()
    try:
        asset_type = AssetType(str(data.get("asset_type") or "stock"))
    except Exception:
        asset_type = AssetType.UNKNOWN
    return Quote(
        symbol=str(data.get("symbol")),
        name=str(data.get("name") or data.get("symbol")),
        ts=ts,
        last=_safe_float(data.get("last")),
        pre_close=_safe_float(data.get("pre_close")),
        open=_safe_float(data.get("open")),
        high=_safe_float(data.get("high")),
        low=_safe_float(data.get("low")),
        volume=_safe_float(data.get("volume")),
        amount=_safe_float(data.get("amount")),
        change=_safe_float(data.get("change")),
        change_pct=_safe_float(data.get("change_pct")),
        turnover=data.get("turnover_rate") if data.get("turnover") is None else data.get("turnover"),
        amplitude=data.get("amplitude"),
        pe_dynamic=data.get("pe_ttm") if data.get("pe_dynamic") is None else data.get("pe_dynamic"),
        pb=data.get("pb"),
        volume_ratio=data.get("volume_ratio"),
        total_market_cap=data.get("total_market_cap"),
        float_market_cap=data.get("float_market_cap"),
        circulating_market_cap=data.get("circulating_market_cap"),
        total_share=data.get("total_share"),
        float_share=data.get("float_share"),
        metric_missing_reasons=data.get("metric_missing_reasons") or [],
        market_cap_style=data.get("market_cap_style"),
        metric_sources=data.get("metric_sources") or {},
        order_ratio=data.get("order_ratio"),
        order_diff=data.get("order_diff"),
        market=str(data.get("market") or "CN"),
        asset_type=asset_type,
        source=str(data.get("source") or "quote_cache"),
    )


def _merge_quote_from_cache(q: Quote, cached_q: Quote | None, cache_status: dict | None = None) -> Quote:
    if cached_q is None:
        return q
    fields = [
        "turnover", "volume_ratio", "amount", "pe_dynamic", "pb", "total_market_cap",
        "float_market_cap", "circulating_market_cap", "total_share", "float_share",
        "market_cap_style", "metric_sources",
    ]
    updates = {}
    for field in fields:
        current = getattr(q, field, None)
        cached = getattr(cached_q, field, None)
        if current in (None, 0, "", {}) and cached not in (None, 0, "", {}):
            updates[field] = cached
    reasons = list(q.metric_missing_reasons or [])
    if cache_status and cache_status.get("stale") and updates:
        reasons.append("quote_cache stale used")
    if updates or reasons:
        updates["metric_missing_reasons"] = list(dict.fromkeys(reasons))
        updates["source"] = f"{q.source}+quote_cache" if updates else q.source
        return replace(q, **updates)
    return q


def _quote_dict_with_aliases(q: Quote, cache_status: dict | None = None) -> dict:
    data = q.to_dict()
    data["turnover_rate"] = data.get("turnover")
    data["pe_ttm"] = data.get("pe_dynamic")
    data["circulating_market_cap"] = data.get("circulating_market_cap") or data.get("float_market_cap")
    data["market_cap_style"] = data.get("market_cap_style") or _market_cap_style(data.get("float_market_cap") or data.get("total_market_cap")) or "未知"
    if str(data.get("market_cap_style") or "").strip() in {"未知", "鏈煡", "δ֪", "--", "-"}:
        data["market_cap_style"] = _market_cap_style(data.get("float_market_cap") or data.get("total_market_cap")) or "未知"
    sources = dict(data.get("metric_sources") or {})
    for field in ["turnover_rate", "volume_ratio", "amount", "pe_ttm", "pb", "total_market_cap", "float_market_cap", "total_share", "float_share"]:
        if data.get(field) not in (None, 0, ""):
            sources.setdefault(field, q.source or "quote_snapshot")
    data["metric_sources"] = sources
    if cache_status:
        data["quote_cache_status"] = cache_status
    return data


def _enrich_quote_real(symbol: str, *, force: bool = False, quote_obj: Quote | None = None, bars: list[Bar] | None = None) -> tuple[Quote, dict, dict]:
    q = quote_obj
    cache_read = cache_state_service.get("quote_cache", symbol, allow_stale=True)
    cached_q = _quote_from_dict((cache_read.data or {}).get("quote") if cache_read.data else None)
    used_cached_quote = False
    service_quote_ok = q is not None
    if q is None:
        try:
            q = service.get_quote(symbol, force_refresh=force)
            service_quote_ok = True
        except Exception:
            if cached_q is None:
                raise
            q = cached_q
            used_cached_quote = True
    q = _merge_quote_from_cache(q, cached_q, cache_read.cache_status if used_cached_quote else None)
    q = service.enrich_quote_metrics(q, force_refresh=force, bars=bars)
    q = _merge_quote_from_cache(q, cached_q, cache_read.cache_status if used_cached_quote else None)
    q = _apply_company_profile_metrics(q)
    q = service.enrich_quote_metrics(q, force_refresh=False, bars=bars)
    if cached_q is not None and cache_read.cache_status.get("stale") and used_cached_quote:
        q = replace(q, metric_missing_reasons=list(dict.fromkeys((q.metric_missing_reasons or []) + ["quote_cache stale used"])))
    data = _quote_dict_with_aliases(q, cache_read.cache_status if used_cached_quote else None)
    if service_quote_ok and not used_cached_quote:
        data["metric_missing_reasons"] = [
            reason for reason in (data.get("metric_missing_reasons") or [])
            if "quote_cache stale used" not in str(reason)
        ]
    cache_status = cache_state_service.put("quote_cache", q.symbol, {
        "symbol": q.symbol,
        "quote": data,
        "enriched_metrics": {k: data.get(k) for k in ["turnover_rate", "volume_ratio", "amount", "pe_ttm", "pb", "total_market_cap", "float_market_cap", "total_share", "float_share", "market_cap_style"]},
        "missing_reasons": data.get("metric_missing_reasons") or [],
        "metric_sources": data.get("metric_sources") or {},
        "market_session": _market_session(q.market),
    }, symbol=q.symbol, source=q.source)
    data["cache_status"] = cache_status
    if not used_cached_quote:
        data["quote_cache_status"] = cache_status
    return q, data, cache_status


def _normalize_info_payload(data: dict, symbol: str, name: str | None, snapshot_id: str, cache_status: dict, *, used_snapshot: bool, mode: str, errors: list[str] | None = None) -> dict:
    data = dict(data or {})
    news = data.get("news") if isinstance(data.get("news"), dict) else {}
    items = data.get("items") or news.get("items") or []
    source_logs = data.get("source_logs") or news.get("sources_status") or data.get("sources_status") or []
    grouped = data.get("grouped_items") or news.get("duplicate_groups") or []
    global_items = data.get("global_items") or (data.get("global_news") or {}).get("items") or []
    mapped = data.get("industry_mapped_items") or (data.get("policy") or {}).get("industry_mapped_items") or []
    raw_count = _safe_float(news.get("raw_count") or news.get("count") or data.get("raw_count") or len(items))
    errors = list(errors or data.get("errors") or [])
    if not items and raw_count:
        errors.append("raw news existed but normalized items are empty; check dedup/date/category filters")
    stats = data.get("stats") or {
        "item_count": len(items),
        "raw_item_count": int(raw_count or len(items)),
        "global_count": len(global_items),
        "industry_mapped_count": len(mapped),
        "source_count": len(source_logs),
        "unknown_date_count": len([x for x in items if not (x.get("publish_time") or x.get("published_at_norm") or x.get("published_at") or x.get("date"))]),
    }
    diagnostics = data.get("diagnostics") or {
        "summary": data.get("summary") or ("items empty; source logs/errors are still returned" if not items else "info snapshot normalized"),
        "data_quality": data.get("data_quality") or {},
        "cache_status": cache_status,
        "filter_empty_reason": "items empty after normalization or filtering" if not items else "",
    }
    score_model = data.get("score_model") or data.get("scoring_model") or {
        "formula": "company/events + source credibility + finance + global/industry mapping - rumor risk",
        "screener_formula": "technical/fundamental/capital/info/style with risk penalties",
    }
    created_at = data.get("created_at") or data.get("updated_at") or datetime.now().isoformat(timespec="seconds")
    data.update({
        "symbol": symbol,
        "name": name or data.get("name") or symbol,
        "mode": mode,
        "snapshot_id": snapshot_id,
        "used_snapshot": bool(used_snapshot),
        "snapshot_reused": bool(used_snapshot),
        "created_at": created_at,
        "updated_at": data.get("updated_at") or created_at,
        "cache_status": cache_status,
        "items": items,
        "grouped_items": grouped,
        "global_items": global_items,
        "industry_mapped_items": mapped,
        "mapped_industries": data.get("mapped_industries") or (data.get("policy") or {}).get("mapped_industries") or [],
        "mapped_concepts": data.get("mapped_concepts") or (data.get("policy") or {}).get("mapped_concepts") or [],
        "mapped_symbols": data.get("mapped_symbols") or (data.get("policy") or {}).get("mapped_symbols") or [],
        "stats": stats,
        "score_model": score_model,
        "diagnostics": diagnostics,
        "source_logs": source_logs,
        "errors": errors,
    })
    return data


def _read_global_news_cached(limit: int = 120, *, force: bool = False) -> tuple[dict, dict]:
    limit = max(30, min(int(limit or 120), 500))
    if not force:
        cached = cache_state_service.get("global_news_cache", f"global:{limit}", allow_stale=True)
        if cached.data and (cached.data.get("items") or not cached.cache_status.get("stale")):
            return dict(cached.data), cached.cache_status
        latest = cache_state_service.latest("global_news_cache", allow_stale=True)
        if latest.data and latest.data.get("items"):
            return dict(latest.data), latest.cache_status
        return {
            "items": [],
            "source_logs": [{"source": "global_news_cache", "status": "miss_no_sync_fetch", "count": 0}],
            "cache_info": {"hit": False, "status": "miss_no_sync_fetch"},
        }, cache_state_service.status("miss", key=f"global:{limit}", source="global_news_cache", error="no cached global news; skipped synchronous fetch")
    data = news_service.fetch_global_news(limit=limit, force=force)
    status = cache_state_service.put("global_news_cache", f"global:{limit}", {
        "created_at": data.get("updated_at") or datetime.now().isoformat(timespec="seconds"),
        "items": data.get("items", []),
        "mapped_industries": data.get("mapped_industries", []),
        "mapped_concepts": data.get("mapped_concepts", []),
        "mapped_symbols": data.get("mapped_symbols", []),
        "source_logs": data.get("sources_status", []),
    }, source="news_global")
    return data, status


def _ensure_info_visible_content(data: dict, symbol: str, name: str | None, limit: int, *, allow_history_fallback: bool = True) -> dict:
    data = dict(data or {})
    source_logs = list(data.get("source_logs") or [])
    errors = list(data.get("errors") or [])
    items = list(data.get("items") or [])
    if not items and allow_history_fallback:
        try:
            cached_items = news_service.store.list_items(symbol, limit=min(max(limit, 30), 180), include_history_days=3650)
        except Exception as exc:
            cached_items = []
            errors.append(f"history news cache fallback failed: {str(exc)[:160]}")
        if cached_items:
            items = cached_items
            data["items"] = items
            news = dict(data.get("news") or {})
            news.setdefault("items", items)
            news["count"] = len(items)
            data["news"] = news
            source_logs.append({"source": "history_news_store", "status": "fallback_hit", "count": len(items), "mode": data.get("mode") or "snapshot"})
        else:
            source_logs.append({"source": "history_news_store", "status": "empty", "count": 0, "mode": data.get("mode") or "snapshot", "skipped_reason": "no persisted stock-specific items"})
    elif not items:
        source_logs.append({"source": "history_news_store", "status": "skipped", "count": 0, "mode": data.get("mode") or "snapshot", "skipped_reason": "request ended in fetch error; avoid unrelated persisted history fallback"})
    global_items = list(data.get("global_items") or [])
    global_status = None
    if not global_items:
        try:
            global_data, global_status = _read_global_news_cached(limit=min(max(limit, 60), 180), force=False)
            global_items = list(global_data.get("items") or [])
            data["global_items"] = global_items
            source_logs.append({"source": "global_news_cache", "status": global_status.get("status") if global_status else "hit", "count": len(global_items), "mode": data.get("mode") or "snapshot"})
        except Exception as exc:
            errors.append(f"global news cache fallback failed: {str(exc)[:160]}")
            source_logs.append({"source": "global_news_cache", "status": "error", "count": 0, "mode": data.get("mode") or "snapshot", "skipped_reason": str(exc)[:160]})
    if global_items:
        try:
            profile = company_profile_service.get_profile(symbol, force=False)
        except Exception:
            profile = {}
        mapped = global_industry_mapper.map_items(global_items, symbol, name or data.get("name") or symbol, profile=profile)
        mapped_items = sorted(mapped.get("industry_mapped_items") or [], key=lambda x: (not bool(x.get("included_in_score") or x.get("score_included")), -float(x.get("relevance_score") or 0)))
        data.update({
            "company_exposure": mapped.get("company_exposure"),
            "industry_mapped_items": mapped_items,
            "mapped_industries": mapped.get("mapped_industries") or [],
            "mapped_concepts": mapped.get("mapped_concepts") or [],
            "mapped_symbols": mapped.get("mapped_symbols") or [],
            "global_news_used": {"related_count": mapped.get("related_count", 0), "cache_status": global_status or {}},
        })
        source_logs.append({"source": "global_industry_mapper", "status": "mapped", "count": len(data.get("industry_mapped_items") or []), "mode": data.get("mode") or "snapshot", "skipped_reason": ""})
    stats = dict(data.get("stats") or {})
    stats.update({
        "item_count": len(data.get("items") or []),
        "raw_item_count": max(int(stats.get("raw_item_count") or 0), len(data.get("items") or [])),
        "global_count": len(data.get("global_items") or []),
        "industry_mapped_count": len(data.get("industry_mapped_items") or []),
        "source_count": len(source_logs),
        "unknown_date_count": len([x for x in data.get("items", []) if not (x.get("publish_time") or x.get("published_at_norm") or x.get("published_at") or x.get("date"))]),
    })
    diagnostics = dict(data.get("diagnostics") or {})
    if not data.get("items"):
        diagnostics["summary"] = "个股信息为空；已保留抓取日志，并补充全球/行业映射作为背景证据"
        diagnostics["empty_reason"] = "stock-specific official/F10/news sources returned no valid items or previous empty snapshot was reused"
    elif not diagnostics.get("summary"):
        diagnostics["summary"] = "个股历史信息已从持久化库恢复"
    data["stats"] = stats
    data["diagnostics"] = diagnostics
    data["source_logs"] = source_logs
    data["errors"] = errors
    return data


def _safe_kline_payload(symbol: str, frame: str = "1d", limit: int = 260, adjust: str = "none", force: bool = False, sync_quote: bool = True) -> dict:
    if frame not in {"1d", "1w", "1M", "1mo"}:
        frame = "1d"
    if frame == "1mo":
        frame = "1M"
    key = _kline_key(symbol, frame, adjust, limit)
    errors: list[str] = []
    fallback_chain: list[str] = []
    q = None
    cache_status = cache_state_service.status("miss", key=key, source="kline_api")
    cached = cache_state_service.get_kline_cache(key)
    session = _market_session("CN")
    # UI/chart pages pass force=true during active sessions. Keep the API-level
    # cache contract predictable for background callers and tests: force=false
    # may hit fresh cache, stale cache is used only when the market is closed
    # or the live source fails.
    effective_force = bool(force)
    if cached.data and not effective_force and not cached.cache_status.get("stale"):
        payload = dict(cached.data)
        payload.update({
            "ok": True,
            "cache_status": cached.cache_status,
            "stale_cache_used": False,
            "fallback_chain": list(dict.fromkeys((payload.get("fallback_chain") or []) + ["cache_state_fresh_hit"])),
        })
        return payload
    if cached.data and not effective_force and not session.get("can_refresh"):
        payload = dict(cached.data)
        payload.update({
            "ok": True,
            "cache_status": cached.cache_status,
            "stale_cache_used": True,
            "fallback_chain": list(dict.fromkeys((payload.get("fallback_chain") or []) + ["cache_state_stale_closed_market"])),
        })
        return payload
    try:
        q = _enrich_quote_real(symbol, force=effective_force)[0] if sync_quote else None
    except Exception as exc:
        errors.append(f"quote_error: {str(exc)[:160]}")
    try:
        bars = service.get_kline(symbol, frame=frame, limit=limit, adjust=adjust, force_refresh=effective_force)
        fallback_chain.append("market_data_service.get_kline")
        if frame == "1d" and any(str(getattr(b, "source", "")).lower().find("minute") >= 0 or str(getattr(b, "source", "")).lower().find("intraday") >= 0 for b in bars):
            raise RuntimeError("daily kline source returned minute/intraday data; refused to draw fake daily chart")
        if len(bars) < min(5, max(2, int(limit or 260))):
            raise RuntimeError(f"K线数量不足：{len(bars)}")
        if q is not None:
            bars, synced, sync_reason = _sync_daily_bar_with_quote(bars, q, frame, adjust)
        else:
            synced, sync_reason = False, "quote_unavailable"
        behavior = market_behavior_engine.analyze(q, bars) if len(bars) >= 5 else market_behavior_engine.analyze(q, [])
        payload = {
            "ok": True,
            "server_time": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "frame": frame,
            "adjust": adjust,
            "cache_key": key,
            "bars": [b.to_dict() for b in bars],
            "data": [b.to_dict() for b in bars],
            "count": len(bars),
            "source": sorted(list({getattr(b, "source", "") for b in bars if getattr(b, "source", "")})),
            "fallback_chain": fallback_chain,
            "errors": errors,
            "stale_cache_used": False,
            "synced": synced,
            "sync_reason": sync_reason,
            "behavior_analysis": behavior,
            "kline_markers": behavior.get("kline_markers", []),
        }
        payload["cache_status"] = cache_state_service.save_kline_cache(key, symbol, payload)
        return payload
    except Exception as exc:
        errors.append(str(exc)[:220])
        if cached.data:
            payload = dict(cached.data)
            payload.update({
                "ok": True,
                "cache_status": cached.cache_status,
                "stale_cache_used": True,
                "errors": list(dict.fromkeys((payload.get("errors") or []) + errors)),
                "fallback_chain": list(dict.fromkeys((payload.get("fallback_chain") or []) + ["cache_state_stale_fallback"])),
            })
            return payload
        try:
            cache_state_service._record_event("kline_cache", key, "read", "error", "; ".join(errors), "kline_api")
        except Exception:
            pass
        return {
            "ok": False,
            "server_time": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "frame": frame,
            "adjust": adjust,
            "cache_key": key,
            "bars": [],
            "data": [],
            "count": 0,
            "source": [],
            "fallback_chain": fallback_chain,
            "errors": errors,
            "stale_cache_used": False,
            "cache_status": cache_state_service.status("error", key=key, source="kline_api", error="; ".join(errors)),
            "behavior_analysis": market_behavior_engine.analyze(None, []),
            "kline_markers": [],
        }


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


def _clean_intraday_points(points: list[IntradayPoint] | None) -> list[IntradayPoint]:
    return [p for p in (points or []) if not str(getattr(p, "source", "")).startswith("quote_fallback")]


def _timeline_latest_date(points: list[IntradayPoint]) -> object | None:
    dates = [getattr(getattr(p, "ts", None), "date", lambda: None)() for p in points if getattr(p, "ts", None)]
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else None


def _timeline_expected_date(q: Quote | None) -> object | None:
    market = q.market if q else "CN"
    session = _market_session(market)
    status = str(session.get("status") or "")
    if status not in {"pre_open_auction", "morning", "lunch", "afternoon", "closing_auction", "call_auction_cooldown"}:
        return None
    if q and getattr(q, "ts", None):
        return q.ts.date()
    try:
        return datetime.fromisoformat(str(session.get("date"))).date()
    except Exception:
        return None


def _filter_timeline_date(points: list[IntradayPoint], expected) -> list[IntradayPoint]:
    if expected is None:
        return points
    same_day = [p for p in points if getattr(getattr(p, "ts", None), "date", lambda: None)() == expected]
    return same_day or points


def _timeline_with_fallback(symbol: str, q: Quote | None, force: bool = False) -> list[IntradayPoint]:
    """获取真实分时数据。

    重要：这里不再用实时行情硬造 09:30/当前/15:00 三个点。
    那种 quote_fallback 会在休市时画出一条假的斜线，误导用户。
    分时数据缺失时，后端只返回真实缓存或空列表；前端显示“暂无真实分时数据/保留缓存”。
    """
    expected_date = _timeline_expected_date(q)
    points = service.get_intraday(symbol, force_refresh=force)
    # 过滤旧版本曾经产生的 quote_fallback/单点快照，避免假分时继续显示。
    clean = _clean_intraday_points(points)
    latest = _timeline_latest_date(clean)
    if expected_date is not None and latest is not None and latest < expected_date and not force:
        refreshed = _clean_intraday_points(service.get_intraday(symbol, force_refresh=True))
        refreshed_latest = _timeline_latest_date(refreshed)
        if refreshed_latest is not None and refreshed_latest >= expected_date:
            clean = refreshed
            latest = refreshed_latest
    if expected_date is not None and latest is not None and latest < expected_date:
        return []
    clean = _filter_timeline_date(clean, expected_date)
    if len(clean) < 2:
        return []
    return clean


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "version": __version__, "server_time": datetime.now().isoformat(timespec="seconds"), "session": _market_session("CN"), "cache": service.cache.stats(), "cache_state": cache_state_service.overview()}


@app.get("/api/market/health")
def market_health() -> dict:
    warnings = [w.__dict__ for w in getattr(service.providers, "warnings", [])[-20:]]
    cache_overview = cache_state_service.overview()
    return {
        "ok": True,
        "version": __version__,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "market_session": _market_session("CN"),
        "sources": {
            "quote_source": "provider_manager + quote_cache",
            "kline_source": "eastmoney/akshare provider chain + kline_cache",
            "info_source": "announcement/F10/news pages + info_snapshot",
            "f10_source": "eastmoney F10/company profile cache",
        },
        "cache_status": cache_overview,
        "cache_state": cache_overview,
        "recent_errors": warnings,
        "recent_success_note": "公开源成功结果会写入 MarketCache 与 CacheStateService；失败时优先返回 stale cache，不画伪数据。",
    }




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
def quote(symbol: str, force: bool = False, refresh: bool = False) -> dict:
    force = bool(force or refresh)
    q, data, cache_status = _enrich_quote_real(symbol, force=force)
    data["extra"] = _quote_extra(q)
    return {"ok": True, "server_time": datetime.now().isoformat(timespec="seconds"), "force": force, "session": _market_session(q.market), "cache_status": cache_status, "data": data}


@app.get("/api/quotes")
def quotes(symbols: str = Query(..., description="逗号分隔，如 300750,600519"), force: bool = False, refresh: bool = False) -> dict:
    force = bool(force or refresh)
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    qs = service.get_quotes(symbol_list, force_refresh=force)
    data = []
    for q in qs:
        q, item, _ = _enrich_quote_real(q.symbol, force=force, quote_obj=q)
        item["extra"] = _quote_extra(q)
        data.append(item)
    return {"ok": True, "server_time": datetime.now().isoformat(timespec="seconds"), "force": force, "session": _market_session("CN"), "count": len(data), "data": data}


def _merge_screener_item_quote_metrics(item: dict, *, force: bool = False) -> None:
    symbol = str(item.get("symbol") or "").strip()
    if not symbol:
        return
    try:
        _q, qd, cache_status = _enrich_quote_real(symbol, force=force)
    except Exception as exc:
        item.setdefault("metric_missing_reasons", []).append(f"quote enrichment failed: {str(exc)[:120]}")
        return
    mapping = {
        "turnover": "turnover",
        "turnover_rate": "turnover_rate",
        "volume_ratio": "volume_ratio",
        "amount": "amount",
        "pe_dynamic": "pe_dynamic",
        "pe_ttm": "pe_ttm",
        "pb": "pb",
        "total_market_cap": "total_market_cap",
        "float_market_cap": "float_market_cap",
        "circulating_market_cap": "circulating_market_cap",
        "total_share": "total_share",
        "float_share": "float_share",
        "market_cap_style": "market_cap_style",
    }
    for dest, src in mapping.items():
        value = qd.get(src)
        if item.get(dest) in (None, "", 0, "--", "未知") and value not in (None, "", 0):
            item[dest] = value
    item["metric_missing_reasons"] = list(dict.fromkeys((item.get("metric_missing_reasons") or []) + (qd.get("metric_missing_reasons") or [])))
    item["metric_sources"] = {**(item.get("metric_sources") or {}), **(qd.get("metric_sources") or {})}
    item["quote_cache_status"] = cache_status
    _clean_screener_metric_missing_reasons(item)
    _fill_screener_theme_from_profile(item)


def _metric_has_value(value) -> bool:
    return value not in (None, "", "--", "未知", "不适用", 0)


def _clean_screener_metric_missing_reasons(item: dict) -> None:
    """Remove stale missing-field hints after quote/F10 enrichment fills metrics."""
    tokens: list[str] = []
    if _metric_has_value(item.get("pe_dynamic")) or _metric_has_value(item.get("pe_ttm")):
        tokens.extend(["PE", "pe_ttm", "pe_dynamic", "市盈"])
    if _metric_has_value(item.get("pb")):
        tokens.extend(["PB", "市净"])
    if _metric_has_value(item.get("total_market_cap")):
        tokens.extend(["总市值", "total_market_cap"])
    if _metric_has_value(item.get("float_market_cap")) or _metric_has_value(item.get("circulating_market_cap")):
        tokens.extend(["流通市值", "float_market_cap", "circulating_market_cap"])
    if _metric_has_value(item.get("turnover")) or _metric_has_value(item.get("turnover_rate")):
        tokens.extend(["换手率", "turnover"])
    if _metric_has_value(item.get("volume_ratio")):
        tokens.extend(["量比", "volume_ratio"])
    if not tokens:
        return

    def keep(reason: object) -> bool:
        text = str(reason)
        return not any(token and token in text for token in tokens)

    for key in ("metric_missing_reasons", "missing_data_hints"):
        cleaned = [str(x) for x in (item.get(key) or []) if x and keep(x)]
        item[key] = list(dict.fromkeys(cleaned))


def _fill_screener_theme_from_profile(item: dict) -> None:
    labels = [str(x) for x in (item.get("theme_labels") or item.get("themes") or []) if str(x).strip()]
    usable = [x for x in labels if x not in {"未知", "未识别题材", "--", "None"}]
    if usable:
        item["theme_labels"] = list(dict.fromkeys(usable))
        return
    symbol = str(item.get("symbol") or "").strip()
    if not symbol:
        return
    try:
        profile = company_profile_service.get_profile(symbol, force=False)
    except Exception:
        profile = {}
    try:
        exposure = global_industry_mapper.company_exposure(symbol, profile=profile, name=str(item.get("name") or symbol))
    except Exception:
        exposure = {}
    concepts = [str(x) for x in exposure.get("concepts") or [] if str(x).strip()]
    industries = [str(x) for x in exposure.get("industries") or [] if str(x).strip()]
    labels = list(dict.fromkeys(concepts[:4] + industries[:3]))
    if labels:
        item["theme_labels"] = labels
        if item.get("theme_stage") in (None, "", "--", "未知", "未识别题材"):
            item["theme_stage"] = "题材待确认"


@app.get("/api/timeline/{symbol}")
def timeline(symbol: str, force: bool = False, refresh: bool = False) -> dict:
    force = bool(force or refresh)
    q = None
    try:
        q = _enrich_quote_real(symbol, force=force)[0]
    except Exception:
        q = None
    points = _timeline_with_fallback(symbol, q, force=force)
    market = q.market if q else _detect_market(symbol)
    expected_date = _timeline_expected_date(q)
    latest_date = _timeline_latest_date(points)
    stale_rejected = bool(expected_date is not None and latest_date is None and force)
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "force": force,
        "symbol": symbol,
        "session": _market_session(market),
        "quote": q.to_dict() if q else None,
        "quote_extra": _quote_extra(q) if q else {},
        "count": len(points),
        "data_quality": {
            "expected_date": expected_date.isoformat() if expected_date else None,
            "latest_date": latest_date.isoformat() if latest_date else None,
            "fresh_for_session": bool(expected_date is None or latest_date == expected_date),
            "stale_cache_rejected": stale_rejected,
            "note": "实时分时源暂无当日有效点，未使用跨日缓存" if stale_rejected else "",
        },
        "data": [p.to_dict() for p in points],
    }


@app.get("/api/kline/{symbol}")
def kline(symbol: str, frame: str = "1d", limit: int = 260, adjust: str = "none", force: bool = False, sync_quote: bool = True, refresh: bool = False) -> dict:
    force = bool(force or refresh)
    payload = _safe_kline_payload(symbol, frame=frame, limit=limit, adjust=adjust, force=force, sync_quote=sync_quote)
    payload["force"] = force
    return payload


@app.get("/api/detail/{symbol}")
def detail(symbol: str, frame: str = "1d", limit: int = 260, adjust: str = "none", force: bool = False, include_timeline: bool = False, refresh: bool = False) -> dict:
    force = bool(force or refresh)
    if frame not in {"1d", "1w", "1M", "1mo"}:
        frame = "1d"
    if frame == "1mo":
        frame = "1M"
    quote_error = None
    try:
        q = _enrich_quote_real(symbol, force=force)[0]
    except Exception as exc:
        q = None
        quote_error = str(exc)
    kpayload = _safe_kline_payload(symbol, frame=frame, limit=limit, adjust=adjust, force=force, sync_quote=False)
    bars_data = kpayload.get("bars") or []
    bars = [Bar(symbol=x.get("symbol") or symbol, frame=frame, ts=datetime.fromisoformat(str(x.get("ts")).replace("Z", "+00:00")).replace(tzinfo=None) if x.get("ts") else datetime.now(), open=float(x.get("open") or 0), high=float(x.get("high") or 0), low=float(x.get("low") or 0), close=float(x.get("close") or 0), volume=float(x.get("volume") or 0), amount=float(x.get("amount") or 0), turnover=x.get("turnover"), change_pct=x.get("change_pct"), source=x.get("source") or "cache_state") for x in bars_data]
    if q is None and bars:
        b = bars[-1]
        q = Quote(symbol=symbol, name=symbol, ts=b.ts, last=b.close, pre_close=b.open, open=b.open, high=b.high, low=b.low, volume=b.volume, amount=b.amount, change=b.close-b.open, change_pct=b.change_pct, turnover=b.turnover, source="bar_snapshot")
    if q is not None:
        q, qd, quote_cache_status = _enrich_quote_real(symbol, force=False, quote_obj=q, bars=bars)
        bars, synced, sync_reason = _sync_daily_bar_with_quote(bars, q, frame, adjust)
        points = _timeline_with_fallback(symbol, q, force=force) if include_timeline else []
        qd["extra"] = _quote_extra(q)
        qd["cache_status"] = quote_cache_status
        session = _market_session(q.market)
        out_symbol = q.symbol
    else:
        synced, sync_reason, points, qd, session, out_symbol = False, "quote_unavailable", [], None, _market_session(_detect_market(symbol)), symbol
    behavior = market_behavior_engine.analyze(q, bars, intraday=points) if len(bars) >= 5 else kpayload.get("behavior_analysis") or market_behavior_engine.analyze(q, [])
    return {
        "ok": bool(kpayload.get("ok", True)),
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
        "behavior_analysis": behavior,
        "kline_markers": behavior.get("kline_markers", []),
        "session": session,
        "synced": synced,
        "sync_reason": sync_reason,
        "source": kpayload.get("source", []),
        "fallback_chain": kpayload.get("fallback_chain", []),
        "errors": kpayload.get("errors", []),
        "cache_status": kpayload.get("cache_status"),
        "stale_cache_used": kpayload.get("stale_cache_used", False),
    }


@app.get("/api/market/stocks")
def market_stocks(page: int = 1, page_size: int = 100) -> dict:
    qs = service.get_market_snapshot(page=page, page_size=page_size)
    data = []
    for q in qs:
        q, item, _ = _enrich_quote_real(q.symbol, quote_obj=q)
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
        "source_knowledge": source_knowledge_service.coverage(),
        "disabled_sources": source_registry_service.disabled_sources(),
        "source_plan": source_registry_service.plan_for_target(120),
        "technical_factor_coverage": technical_factor_registry_service.coverage(),
        "technical_factors_by_category": technical_factor_registry_service.by_category(),
        "note": "WordSource V1 已把消息面、技术面、风格资金面、量化交易文档映射为可运行服务与API。",
    }


@app.get("/api/wordsource/trace")
def wordsource_trace() -> dict:
    path = Path("docs/WORD_SOURCE_TRACE.md")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or "原文要点" in line or "---" in line:
            continue
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if len(cells) >= 7:
            status = "已落地" if cells[1] and cells[2] and cells[3] and cells[4] and cells[5] else "部分落地"
            rows.append({
                "source": cells[0],
                "original": cells[1] if len(cells) > 1 else "",
                "feature": cells[2] if len(cells) > 2 else "",
                "code": cells[3] if len(cells) > 3 else "",
                "api": cells[4] if len(cells) > 4 else "",
                "frontend": cells[5] if len(cells) > 5 else "",
                "tests": cells[6] if len(cells) > 6 else "",
                "test": cells[6] if len(cells) > 6 else "",
                "status": status,
            })
    if rows and all(r["status"] == "已落地" for r in rows):
        rows[-1]["status"] = "部分落地"
    return {"ok": True, "path": str(path), "count": len(rows), "data": rows, "items": rows, "text": text[:200000]}


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
    regime = market_regime_service.analyze_market(quotes, index_bars=_market_index_bars())
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


@app.get("/api/backtest/strategies")
def backtest_strategies() -> dict:
    return {"ok": True, "data": backtest_service.strategies}


@app.get("/api/backtest/run")
def backtest_run(
    symbol: str = "300750",
    strategy: str = "ma_cross",
    initial_cash: float = 100_000.0,
    fee_rate: float = 0.0003,
    slippage_rate: float = 0.0005,
    position_pct: float = 1.0,
    stop_loss_pct: float = 8.0,
    take_profit_pct: float = 0.0,
    buy_score: float = 62.0,
    sell_score: float = 48.0,
    limit: int = 520,
    adjust: str = "qfq",
    force: bool = False,
) -> dict:
    symbol = str(symbol or "300750").strip()
    limit = max(60, min(int(limit or 520), 1200))
    adjust = str(adjust or "qfq").lower()
    if adjust not in {"none", "qfq", "hfq"}:
        adjust = "qfq"
    try:
        q = service.get_quote(symbol, force_refresh=force)
    except Exception:
        q = None
    try:
        bars = service.get_kline(symbol, frame="1d", limit=limit, adjust=adjust, force_refresh=force)
        if not force and len(bars) < min(limit, 120):
            bars = service.get_kline(symbol, frame="1d", limit=limit, adjust=adjust, force_refresh=True)
        result = backtest_service.run(
            symbol,
            bars,
            LegacyBacktestConfig(
                strategy=strategy,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                slippage_rate=slippage_rate,
                position_pct=position_pct,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                buy_score=buy_score,
                sell_score=sell_score,
            ),
            name=getattr(q, "name", None) if q else symbol,
        )
        result["quote_source"] = getattr(q, "source", None) if q else None
        result["kline_source"] = sorted({getattr(b, "source", "") for b in bars if getattr(b, "source", "")})
        result["adjust"] = adjust
        result["requested_limit"] = limit
        result["data_quality"]["requested_bars"] = limit
        result["data_quality"]["short_kline"] = len(bars) < min(limit, 120)
        return {"ok": True, "data": result}
    except Exception as exc:
        return {"ok": False, "message": str(exc)[:240], "symbol": symbol, "strategy": strategy}


def _v319_response(ok: bool, **payload: object) -> dict:
    base = {"ok": ok, "run_id": None, "data": None, "metrics": {}, "errors": [], "warnings": [], "cache_status": "memory"}
    base.update(payload)
    base.setdefault("errors", [])
    base.setdefault("warnings", [])
    base.setdefault("cache_status", "memory")
    return base


def _v319_config(payload: dict | None = None) -> V319BacktestConfig:
    payload = payload or {}
    raw = dict(payload.get("config") or payload)
    if "symbol" in raw and "symbols" not in raw:
        raw["symbols"] = [str(raw.get("symbol"))]
    if isinstance(raw.get("symbols"), str):
        raw["symbols"] = [x.strip() for x in raw["symbols"].replace("，", ",").split(",") if x.strip()]
    allowed = {f.name for f in fields(V319BacktestConfig)}
    data = {k: v for k, v in raw.items() if k in allowed}
    return V319BacktestConfig(**data)


def _v319_market_data(payload: dict, cfg: V319BacktestConfig) -> dict | None:
    raw = payload.get("market_data")
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        symbol = cfg.symbols[0] if cfg.symbols else str(payload.get("symbol") or "300750")
        return {symbol: raw}
    return None


@app.post("/api/backtest/run")
def backtest_run_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        cfg = _v319_config(payload)
        result = backtest_engine_v319.run(
            cfg,
            market_data=_v319_market_data(payload, cfg),
            screener_rows=payload.get("screener_rows") or payload.get("snapshot_rows"),
        )
        backtest_storage_v319.save(result)
        return _v319_response(
            True,
            run_id=result.run_id,
            data=result.to_dict(),
            metrics=result.metrics,
            errors=result.errors,
            warnings=result.warnings,
            cache_status=result.cache_status,
        )
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]], message=str(exc)[:300])


@app.get("/api/backtest/result/{run_id}")
def backtest_result_v319(run_id: str) -> dict:
    try:
        data = backtest_storage_v319.load(run_id)
        return _v319_response(True, run_id=run_id, data=data, metrics=data.get("metrics", {}), warnings=data.get("warnings", []), cache_status="disk")
    except FileNotFoundError:
        return _v319_response(False, run_id=run_id, errors=["run_id not found"], cache_status="miss")


@app.get("/api/backtest/runs")
def backtest_runs_v319(limit: int = 50) -> dict:
    return _v319_response(True, data=backtest_storage_v319.list_runs(limit=max(1, min(int(limit or 50), 200))), cache_status="disk")


@app.delete("/api/backtest/result/{run_id}")
def backtest_delete_v319(run_id: str) -> dict:
    ok = backtest_storage_v319.delete(run_id)
    return _v319_response(ok, run_id=run_id, data={"deleted": ok}, errors=[] if ok else ["run_id not found"], cache_status="disk")


@app.get("/api/backtest/export/{run_id}")
def backtest_export_v319(run_id: str, fmt: str = "json") -> Response:
    if fmt.lower() == "csv":
        path = backtest_storage_v319.export_trades_csv(run_id)
        return Response(path.read_text(encoding="utf-8-sig"), media_type="text/csv; charset=utf-8")
    return Response(backtest_storage_v319.export_json(run_id), media_type="application/json; charset=utf-8")


@app.post("/api/backtest/compare")
def backtest_compare_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        cfg = _v319_config(payload)
        strategies = payload.get("strategies") or ["score_rank_rebalance", "factor_rule_strategy", "event_risk_filter"]
        market_data = _v319_market_data(payload, cfg)
        rows = []
        for strategy in strategies:
            result = backtest_engine_v319.run(replace(cfg, strategy=str(strategy), run_id=None), market_data=market_data)
            rows.append({"strategy": strategy, "run_id": result.run_id, "metrics": result.metrics, "warnings": result.warnings})
        return _v319_response(True, data=rows, cache_status="memory")
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]])


@app.post("/api/backtest/optimize")
def backtest_optimize_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        cfg = _v319_config(payload)
        grid = payload.get("param_grid") or {"buy_score": [58, 62, 66], "sell_score": [42, 48]}
        objective = str(payload.get("objective") or "sharpe")
        optimizer = ParameterOptimizer(backtest_engine_v319)
        rows = optimizer.grid_search(cfg, grid, market_data=_v319_market_data(payload, cfg), objective=objective)
        return _v319_response(True, data=rows, metrics={"best": rows[0] if rows else None}, cache_status="memory")
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]])


@app.post("/api/backtest/walk-forward")
def backtest_walk_forward_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        cfg = _v319_config(payload)
        market_data = _v319_market_data(payload, cfg)
        if not market_data:
            return _v319_response(False, errors=["walk-forward requires market_data in V3.19 API"], cache_status="missing")
        validator = WalkForwardValidator(backtest_engine_v319)
        data = validator.run(
            market_data,
            cfg,
            train_size=int(payload.get("train_size") or 180),
            test_size=int(payload.get("test_size") or 60),
            expanding=bool(payload.get("expanding", True)),
        )
        return _v319_response(True, data=data, metrics={"stability_score": data["stability_score"]}, cache_status="memory")
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]])


@app.get("/api/backtest/report/{run_id}")
def backtest_report_v319(run_id: str) -> dict:
    try:
        data = backtest_storage_v319.load(run_id)
        report = build_report(data)
        return _v319_response(True, run_id=run_id, data=report, warnings=data.get("warnings", []), cache_status="disk")
    except FileNotFoundError:
        return _v319_response(False, run_id=run_id, errors=["run_id not found"], cache_status="miss")


@app.get("/api/paper/state")
def paper_state_v319() -> dict:
    data = paper_broker_v319.snapshot()
    return _v319_response(True, data=data, cache_status="memory")


@app.post("/api/paper/signal")
def paper_signal_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        signal = StrategySignal(
            symbol=str(payload.get("symbol") or "300750"),
            date=str(payload.get("date") or datetime.now().date().isoformat()),
            action=str(payload.get("action") or "buy"),
            score=float(payload.get("score") or 0.0),
            strength=float(payload.get("strength") or 0.0),
            target_weight=float(payload.get("target_weight") or 0.0),
            price=payload.get("price"),
            reason=str(payload.get("reason") or "manual paper signal"),
            source=str(payload.get("source") or "paper_api"),
        )
        order = paper_broker_v319.receive_signal(signal)
        return _v319_response(True, data={"order": order.to_dict() if order else None, "snapshot": paper_broker_v319.snapshot()}, cache_status="memory")
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]])


@app.post("/api/paper/fill")
def paper_fill_v319(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        order_id = str(payload.get("order_id") or "")
        order = next((x for x in paper_broker_v319.orders if x.order_id == order_id), None)
        if order is None:
            return _v319_response(False, errors=["order_id not found"], cache_status="memory")
        bar = payload.get("bar") or {
            "date": payload.get("date") or datetime.now().date().isoformat(),
            "open": payload.get("open") or payload.get("price") or 0,
            "high": payload.get("high") or payload.get("price") or 0,
            "low": payload.get("low") or payload.get("price") or 0,
            "close": payload.get("close") or payload.get("price") or 0,
            "volume": payload.get("volume") or 1_000_000,
        }
        fill = paper_broker_v319.simulate_fill(order, bar)
        return _v319_response(True, data={"fill": fill.to_dict() if fill else None, "snapshot": paper_broker_v319.snapshot()}, cache_status="memory")
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]])


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
    selected_symbol: str | None = None,
    view_mode: str = "compact",
    scroll_position: int = 0,
    show_excluded: bool = False,
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
    for item in result.get("data", []) or []:
        _merge_screener_item_quote_metrics(item, force=force_quotes)
    selected_strategies = [x.strip() for x in str(strategies or "").split(",") if x.strip()]
    result["selected_strategies"] = selected_strategies
    snapshot_id = _make_snapshot_id("screener", info_limit if enable_news else None)
    result["snapshot_id"] = snapshot_id
    result["strategy_note"] = "V3.18.3 默认使用前复权日K参与筛选评分；三通道候选池、WordSource V2 技术因子、资金/基本/信息/风格诊断嵌入主流程；筛选快照和信息快照持久化，可返回恢复。"
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
                item_snapshot_id = f"{snapshot_id}-{item.get('symbol','')}"
                ir = info_analysis_service.analyze(item.get("symbol", ""), name=item.get("name"), limit=info_limit, force=False, mode="light")
                profile = company_profile_service.get_profile(item.get("symbol", ""), force=False)
                ir["snapshot_id"] = item_snapshot_id
                nr = ir.get("news", {})
                if isinstance(nr, dict):
                    nr["snapshot_id"] = item_snapshot_id
                news_service.store.save_analysis(item.get("symbol", ""), f"snapshot:{item_snapshot_id}", ir, name=item.get("name"))
                cache_state_service.save_info_snapshot(item_snapshot_id, item.get("symbol", ""), _normalize_info_payload(ir, item.get("symbol", ""), item.get("name"), item_snapshot_id, cache_state_service.status("refreshed", key=item_snapshot_id, source="screener_info"), used_snapshot=False, mode="light"), mode="light")
                detail_url = f"/info?symbol={item.get('symbol','')}&name={item.get('name','')}&limit={info_limit}&snapshot_id={item_snapshot_id}&force=false"
                item["info_snapshot_id"] = item_snapshot_id
                item["info_crawl_time"] = ir.get("updated_at")
                item["info_effective_count"] = (ir.get("evidence_counts") or {}).get("news_items") or nr.get("count") or 0
                item["info_unique_event_count"] = nr.get("count") or 0
                item["news"] = {
                    "snapshot_id": item_snapshot_id,
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
                    "snapshot_id": item_snapshot_id,
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
                usable_info = bool(
                    item.get("info_effective_count")
                    or nr.get("count")
                    or ir.get("items")
                    or ir.get("industry_mapped_items")
                )
                effective_info_weight = calc_info_weight if usable_info else 0.0
                info_delta_raw = (info_score - base) * effective_info_weight
                info_delta_cap = 12.0 if calc_info_weight >= 0.45 else 8.0
                info_delta = max(-info_delta_cap, min(info_delta_raw, info_delta_cap))
                item["technical_score"] = round(base, 2)
                item["info_score_delta_raw"] = round(info_delta_raw, 2)
                item["info_score_delta"] = round(info_delta, 2)
                item["info_score_delta_cap"] = info_delta_cap if effective_info_weight else 0.0
                item["total_score_with_info"] = round(max(0, min(100, base + info_delta)), 2)
                item["info_weight"] = effective_info_weight
                item["score_formula"] = (
                    f"技术/量价底分×{1-effective_info_weight:.2f} + 信息面分×{effective_info_weight:.2f}"
                    + (f"；信息面单次调分限制±{info_delta_cap:.0f}" if usable_info else "；信息面无有效证据，本轮不改写评分")
                )
                if usable_info and abs(info_delta_raw - info_delta) > 0.001:
                    item.setdefault("risk_flags", []).append("信息面调分已限幅，避免单次抓取过度扰动")
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
                item_snapshot_id = f"{snapshot_id}-{item.get('symbol','')}"
                detail_url = f"/info?symbol={item.get('symbol','')}&name={item.get('name','')}&limit={info_limit}&snapshot_id={item_snapshot_id}&force=false"
                err_payload = _normalize_info_payload(
                    {
                        "errors": [str(exc)[:220]],
                        "source_logs": [{
                            "source": "screener_info_light",
                            "status": "error",
                            "count": 0,
                            "mode": "light",
                            "skipped_reason": str(exc)[:160],
                        }],
                    },
                    item.get("symbol", ""),
                    item.get("name"),
                    item_snapshot_id,
                    cache_state_service.status("error", key=item_snapshot_id, source="screener_info", error=str(exc)[:180]),
                    used_snapshot=False,
                    mode="light",
                    errors=[str(exc)[:220]],
                )
                news_service.store.save_analysis(item.get("symbol", ""), f"snapshot:{item_snapshot_id}", err_payload, name=item.get("name"))
                cache_state_service.save_info_snapshot(item_snapshot_id, item.get("symbol", ""), err_payload, mode="light")
                item["info_snapshot_id"] = item_snapshot_id
                item["info_crawl_time"] = err_payload.get("created_at")
                item["info_effective_count"] = 0
                item["info_unique_event_count"] = 0
                item["info"] = {"error": str(exc)[:180], "info_score": None, "snapshot_id": item_snapshot_id, "detail_url": detail_url}
                item["news"] = {"snapshot_id": item_snapshot_id, "detail_url": detail_url, "count": 0, "summary": "信息面 light 快照为空，详情页会显示错误原因而不自动重抓。"}
        result["news_analyzed_count"] = info_count
        result["info_analyzed_count"] = info_count
        result["news_note"] = f"已对筛选结果前20只候选股进行信息面评分；抓取上限={info_limit}，融合权重={calc_info_weight:.0%}，snapshot_id={snapshot_id}。V3.18.3 筛选页可恢复快照，新闻长列表进入信息面详情；清洗页头/页脚/JS脏数据，按事件簇去重，并区分 publish_time/event_time/crawl_time。"
        result["data"].sort(key=lambda x: x.get("total_score_with_info", x.get("total_score", 0)), reverse=True)
    result["score_stability_note"] = (
        "筛选评分不使用随机数；短时间差异主要来自实时行情、K线强刷、信息面缓存/刷新口径和外部公开源可用性。"
        "大盘情绪由指数趋势和市场宽度合成，只做±2分内的小幅背景调分；启用信息面时会先保留技术底分，并对单次信息面调分限幅，降低重复抓取造成的大幅波动。"
    )
    try:
        saved = score_history_service.save_results(result.get("data", []), mode=mode)
        result["score_history_saved"] = saved
        result["score_history_note"] = "评分历史按天保存；同一股票同一天重复筛选会覆盖当天记录。"
    except Exception as exc:
        result["score_history_saved"] = 0
        result["score_history_error"] = str(exc)[:220]
    available_symbols = {str(x.get("symbol")) for x in result.get("data", []) if x.get("symbol")}
    selected_symbol = selected_symbol if selected_symbol in available_symbols else (result.get("data") or [{}])[0].get("symbol")
    selected_row = next((x for x in result.get("data", []) if x.get("symbol") == selected_symbol), None)
    created_at = datetime.now().isoformat(timespec="seconds")
    result["screener_snapshot_id"] = snapshot_id
    result["created_at"] = created_at
    result["selected_symbol"] = selected_symbol
    result["selected_row"] = selected_row
    result["view_mode"] = view_mode
    result["scroll_position"] = scroll_position
    result["summary"] = {
        "result_count": result.get("result_count", len(result.get("data", []))),
        "analyzed_count": result.get("analyzed_count"),
        "error_count": result.get("error_count", 0),
        "top_score": max([float(x.get("total_score") or 0) for x in result.get("data", [])], default=0),
    }
    result["results"] = result.get("data", [])
    snap_payload = {
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "universe": universe,
        "symbols": symbol_list,
        "mode": mode,
        "strategies": selected_strategies,
        "enable_news": bool(enable_news),
        "params": {
            "max_items": max_items,
            "max_pages": max_pages,
            "page_size": page_size,
            "kline_limit": kline_limit,
            "kline_adjust": kline_adjust,
            "min_score": min_score,
            "min_amount": min_amount,
            "include_stocks": include_stocks,
            "include_etf": include_etf,
            "info_limit": info_limit,
        },
        "results": result.get("data", []),
        "data": result.get("data", []),
        "selected_symbol": selected_symbol,
        "selected_row": selected_row,
        "view_mode": view_mode,
        "scroll_position": scroll_position,
        "custom_symbols": symbols,
        "enabled_strategies": selected_strategies,
        "summary": result["summary"],
        "source_status": result.get("errors", []),
    }
    result["cache_status"] = cache_state_service.save_screener_snapshot(snapshot_id, snap_payload)
    return result


@app.get("/api/screener/snapshot/{snapshot_id}")
def screener_snapshot(snapshot_id: str) -> dict:
    cached = cache_state_service.get_screener_snapshot(snapshot_id)
    data = cached.data or {}
    results = data.get("results") or data.get("data") or []
    return {
        "ok": bool(cached.data),
        "restored": bool(cached.data and results),
        "message": "" if results else "snapshot has no results",
        "snapshot_id": snapshot_id,
        "cache_status": cached.cache_status,
        "data": results,
        "results": results,
        "summary": data.get("summary") or {},
        "selected_symbol": data.get("selected_symbol"),
        "selected_row": data.get("selected_row"),
        "view_mode": data.get("view_mode"),
        "scroll_position": data.get("scroll_position"),
        "custom_symbols": data.get("custom_symbols"),
        "enabled_strategies": data.get("enabled_strategies") or data.get("strategies") or [],
        "enable_news": data.get("enable_news"),
        "params": data.get("params") or {},
        "created_at": data.get("created_at"),
        "snapshot": data,
    }


@app.get("/api/cache/status")
def cache_status() -> dict:
    return cache_state_service.overview()


@app.get("/api/cache/screener/latest")
def cache_screener_latest() -> dict:
    cached = cache_state_service.latest_screener_snapshot()
    data = cached.data or {}
    results = data.get("results") or data.get("data") or []
    return {
        "ok": bool(cached.data),
        "restored": bool(cached.data and results),
        "message": "" if results else "snapshot has no results",
        "cache_status": cached.cache_status,
        "snapshot_id": data.get("snapshot_id"),
        "created_at": data.get("created_at"),
        "data": results,
        "results": results,
        "summary": data.get("summary") or {},
        "selected_symbol": data.get("selected_symbol"),
        "selected_row": data.get("selected_row"),
        "view_mode": data.get("view_mode"),
        "scroll_position": data.get("scroll_position"),
        "custom_symbols": data.get("custom_symbols"),
        "enabled_strategies": data.get("enabled_strategies") or data.get("strategies") or [],
        "enable_news": data.get("enable_news"),
        "params": data.get("params") or {},
        "snapshot": data,
    }


@app.get("/api/cache/info/latest/{symbol}")
def cache_info_latest(symbol: str) -> dict:
    cached = cache_state_service.latest_info_snapshot(symbol)
    data = cached.data or {}
    return {"ok": bool(cached.data), "symbol": symbol, "snapshot_id": data.get("snapshot_id"), "cache_status": cached.cache_status, "data": data}


@app.get("/api/cache/kline/{symbol}")
def cache_kline(symbol: str, frame: str = "1d", adjust: str = "none", limit: int = 260) -> dict:
    key = _kline_key(symbol, "1M" if frame == "1mo" else frame, adjust, limit)
    cached = cache_state_service.get_kline_cache(key)
    return {"ok": bool(cached.data), "symbol": symbol, "frame": frame, "adjust": adjust, "cache_status": cached.cache_status, "data": cached.data}


@app.post("/api/cache/clear")
def cache_clear(kind: str | None = None, key: str | None = None, symbol: str | None = None) -> dict:
    count = cache_state_service.clear(kind=kind, key=key, symbol=symbol)
    return {"ok": True, "cleared": count, "kind": kind, "key": key, "symbol": symbol}



@app.post("/api/watchlist/clear")
def watchlist_clear() -> dict:
    data = watchlist_service.set([])
    return {"ok": True, "message": "实时监测列表已清空", "data": data}


@app.get("/api/orderbook/{symbol}")
def orderbook(symbol: str, force: bool = False) -> dict:
    session = calendar_status(symbol=symbol)["data"]
    allow_external = bool(force or session.get("can_refresh"))
    book = service.get_order_book(symbol, allow_external=allow_external)
    note = ""
    if not allow_external:
        status = str(session.get("status") or "")
        label = str(session.get("label") or "")
        if status == "lunch" or "午" in label:
            note = "午休无盘口"
        elif status == "closed" or "休" in label:
            note = "休市无盘口"
        else:
            note = "非交易时段不适用"
    elif not book:
        note = "公开行情源未返回五档盘口；普通免费源通常没有稳定 Level-2 深度，交易时段会继续尝试。"
    elif not ((book.asks or []) and (book.bids or [])):
        note = "盘口字段不完整；仅展示公开源实际返回的档位。"
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "symbol": symbol,
        "market_status": session.get("status"),
        "market_label": session.get("label"),
        "skipped_external": not allow_external,
        "note": note,
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
    errors: list[str] = []
    try:
        data = strategy_library_service.list()
    except Exception as exc:
        errors.append(f"strategy_library_service failed: {str(exc)[:160]}")
        data = []
    if not data:
        errors.append("strategy library empty; fallback strategies returned")
        data = FALLBACK_STRATEGIES
    else:
        existing = {str(x.get("key") or x.get("name")) for x in data}
        for item in FALLBACK_STRATEGIES:
            if str(item.get("key")) not in existing and str(item.get("name")) not in existing:
                data.append(item)
    default_keys = [str(x.get("key")) for x in data if x.get("enabled", True) and x.get("key")]
    if not default_keys:
        default_keys = [str(x["key"]) for x in FALLBACK_STRATEGIES]
    return {"ok": True, "data": data, "default_keys": default_keys, "errors": errors}


@app.get("/api/technical/indicators")
def technical_indicators() -> dict:
    return {"ok": True, "coverage": technical_indicator_library_service.coverage(), "word_source_catalog": technical_indicator_library_service.word_source_catalog(), "data": technical_indicator_library_service.list()}


@app.get("/api/technical/indicators/by-category")
def technical_indicators_by_category() -> dict:
    return {"ok": True, "coverage": technical_indicator_library_service.coverage(), "data": technical_indicator_library_service.by_category()}


@app.get("/api/technical/factors/{symbol}")
def technical_factors(symbol: str, frame: str = "1d", adjust: str = "qfq", limit: int = 260, force: bool = False) -> dict:
    cache_key = f"{symbol}:{frame}:{adjust}:{limit}"
    if not force:
        cached = cache_state_service.get("technical_factor_cache", cache_key, allow_stale=True)
        if cached.data and not cached.cache_status.get("stale"):
            data = dict(cached.data)
            data["cache_status"] = cached.cache_status
            return {"ok": True, **data}
    q = service.get_quote(symbol, force_refresh=force)
    bars = service.get_kline(symbol, frame=frame, limit=limit, adjust=adjust, force_refresh=force)
    q = service.enrich_quote_metrics(q, force_refresh=force, bars=bars)
    report = technical_factor_engine.analyze(q, bars)
    factors = []
    for f in report.get("factors", []):
        factors.append({
            "key": f.get("key"),
            "name": f.get("name"),
            "category": _factor_category(str(f.get("key") or "")),
            "value": f.get("value"),
            "formula": f.get("formula_source") or f.get("logic"),
            "params": _factor_params(str(f.get("key") or "")),
            "signal": f.get("signal"),
            "explanation": f.get("explanation"),
            "score_contribution": f.get("score_contribution", 0),
            "risk_penalty": f.get("risk_penalty", 0),
            "score_note": _factor_score_note(f),
            "applicable_market": f.get("application") or "A股/ETF日K",
        })
    closes = [float(b.close) for b in bars if b.close]
    volumes = [float(b.volume or 0) for b in bars]
    last = float(q.last or (closes[-1] if closes else 0))
    extras = [
        ("ma5_deviation", "MA5偏离", (last / (sum(closes[-5:]) / 5) - 1) * 100 if len(closes) >= 5 and sum(closes[-5:]) else None, "last/MA5-1"),
        ("ma10_deviation", "MA10偏离", (last / (sum(closes[-10:]) / 10) - 1) * 100 if len(closes) >= 10 and sum(closes[-10:]) else None, "last/MA10-1"),
        ("ma20_deviation", "MA20偏离", (last / (sum(closes[-20:]) / 20) - 1) * 100 if len(closes) >= 20 and sum(closes[-20:]) else None, "last/MA20-1"),
        ("amount_strength", "成交额强度", q.amount, "实时成交额/成交额缓存"),
        ("turnover_rate", "换手率", q.turnover, "实时快照/F10/缓存换手率"),
        ("volume_ratio", "量比", q.volume_ratio, "实时快照量比或K线均量估算"),
    ]
    for key, name, value, formula in extras:
        if len(factors) >= 44:
            break
        signal = "中性"
        if isinstance(value, (int, float)):
            signal = "看多" if float(value) > 3 else "看空" if float(value) < -5 else "中性"
        factors.append({
            "key": key,
            "name": name,
            "category": "closed_loop_extra",
            "value": round(float(value), 4) if isinstance(value, (int, float)) else value,
            "formula": formula,
            "params": {},
            "signal": signal,
            "explanation": f"{name}用于补充筛选页可见闭环字段，来自行情/K线缓存。",
            "score_contribution": 0,
            "risk_penalty": 0,
            "score_note": "闭环展示项，默认不直接加扣分",
            "applicable_market": "A股/ETF",
        })
    payload = {
        "symbol": q.symbol,
        "name": q.name,
        "frame": frame,
        "adjust": adjust,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "factor_count": len(factors),
        "factors": factors,
        "summary": report.get("summary") or report.get("signals") or [],
        "data_quality": report.get("data_quality") or {"bars": len(bars), "source": sorted(list({b.source for b in bars}))},
    }
    payload["cache_status"] = cache_state_service.put("technical_factor_cache", cache_key, payload, symbol=q.symbol, source="technical_factor_engine")
    return {"ok": True, **payload}


def _factor_category(key: str) -> str:
    if key in {"ma", "ema", "macd", "rsi", "kdj", "boll", "bias", "sar", "ichimoku", "ichimoku_cloud"}:
        return "trend_momentum"
    if key in {"atr", "volatility", "price_channel", "range_position", "support_resistance"}:
        return "space_volatility"
    if key in {"obv", "mfi", "vr", "volume_ma", "price_volume_state", "volume_divergence", "vwap", "vwap_strength"}:
        return "volume_capital"
    return "pattern_timing"


def _factor_num(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _factor_score_note(f: dict) -> str:
    score = _factor_num(f.get("score_contribution"), 0.0)
    risk = _factor_num(f.get("risk_penalty"), 0.0)
    signal = str(f.get("signal") or "")
    value = f.get("value")
    if score == 0 and risk == 0:
        if value is None:
            return "数据为空，未参与加扣分"
        if signal == "中性":
            return "中性未触发，不代表缺数据"
        return "仅提示方向，本项未直接加扣分"
    if score > 0 and risk > 0:
        return "同时存在积极信号和风险提示"
    if score > 0:
        return "触发加分"
    return "触发风险扣分"


def _factor_params(key: str) -> dict:
    params = {
        "ma": {"windows": [5, 10, 20, 60]},
        "ema": {"windows": [12, 26]},
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "rsi": {"period": 14},
        "kdj": {"period": 9},
        "boll": {"period": 20, "std": 2},
        "atr": {"period": 14},
        "vwap": {"period": 20},
    }
    return params.get(key, {})




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
def news_analyze(symbol: str, name: str | None = None, limit: int = 120, force: bool = False, snapshot_id: str | None = None, mode: str = "light", deep_refresh: bool = False) -> dict:
    qname = name
    if not qname:
        try:
            qname = service.get_quote(symbol, force_refresh=False).name
        except Exception:
            qname = symbol
    data = news_service.analyze(symbol, name=qname, limit=limit, force=force or deep_refresh, mode="deep" if deep_refresh else mode)
    sid = snapshot_id or _make_snapshot_id(symbol, limit)
    data["snapshot_id"] = sid
    news_service.store.save_analysis(symbol, f"news_snapshot:{sid}", data, name=qname)
    return {"ok": True, "symbol": symbol, "snapshot_id": sid, "data": data}





@app.get("/api/news/global")
def global_news(limit: int = 80, force: bool = False) -> dict:
    data, cache_status = _read_global_news_cached(limit=limit, force=force)
    data["cache_status"] = cache_status
    return {"ok": True, "cache_status": cache_status, "data": data}


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
def info_analyze(symbol: str, name: str | None = None, limit: int = 120, force: bool = False, snapshot_id: str | None = None, deep_refresh: bool = False, mode: str = "normal") -> dict:
    qname = name
    if not qname:
        try:
            qname = service.get_quote(symbol, force_refresh=False).name
        except Exception:
            qname = symbol
    mode_raw = str(mode or "normal").lower()
    use_mode = "deep" if deep_refresh or mode_raw in {"deep", "deep_refresh", "full"} else "light" if mode_raw == "light" else "normal"
    sid = (snapshot_id or "").strip()
    errors: list[str] = []
    used_snapshot = False
    data = None
    cache_status = cache_state_service.status("miss", key=sid, source="info_snapshot")
    if sid and not force and not deep_refresh:
        cached = cache_state_service.get_info_snapshot(sid)
        if cached.data:
            data = cached.data
            cache_status = cached.cache_status
            used_snapshot = True
        else:
            legacy = news_service.store.read_analysis(symbol, f"snapshot:{sid}", 7 * 86400)
            if legacy:
                cache_status = cache_state_service.status("hit", key=sid, source="legacy_news_store")
                data = legacy
                used_snapshot = True
    if data is None and not sid and not force and not deep_refresh:
        cached = cache_state_service.latest_info_snapshot(symbol)
        if cached.data:
            sid = str(cached.data.get("snapshot_id") or cached.cache_status.get("snapshot_id") or "")
            data = cached.data
            cache_status = cached.cache_status
            used_snapshot = True
    if data is None and sid and not force and not deep_refresh:
        cached = cache_state_service.latest_info_snapshot(symbol)
        if cached.data:
            requested_sid = sid
            sid = str(cached.data.get("snapshot_id") or cached.cache_status.get("snapshot_id") or sid)
            data = cached.data
            cache_status = cached.cache_status
            used_snapshot = True
            errors.append(f"requested snapshot not found: {requested_sid}; used latest snapshot for {symbol}")
        else:
            errors.append(f"requested snapshot not found: {sid}; no refresh was started automatically")
            cache_status = cache_state_service.status("miss", key=sid, source="info_snapshot", error=errors[-1])
            data = _normalize_info_payload(
                {},
                symbol,
                qname,
                sid,
                cache_status,
                used_snapshot=False,
                mode="snapshot_miss",
                errors=errors,
            )
            data["snapshot_notice"] = "请求的筛选页快照不存在，详情页未自动重抓；请点击普通刷新或深度刷新。"
    if data is None:
        sid = sid or _make_snapshot_id(symbol, limit)
        try:
            raw = info_analysis_service.analyze(symbol, name=qname, limit=limit, force=force or deep_refresh, mode=use_mode, deep_refresh=deep_refresh)
            cache_status = cache_state_service.status("refreshed", key=sid, source=f"info_{use_mode}")
            data = _normalize_info_payload(raw, symbol, qname, sid, cache_status, used_snapshot=False, mode=use_mode)
            news_service.store.save_analysis(symbol, f"snapshot:{sid}", data, name=qname)
            cache_status = cache_state_service.save_info_snapshot(sid, symbol, data, mode=use_mode)
            data["cache_status"] = cache_status
        except Exception as exc:
            errors.append(str(exc)[:240])
            cache_status = cache_state_service.status("error", key=sid, source=f"info_{use_mode}", error=errors[-1])
            data = _normalize_info_payload({}, symbol, qname, sid, cache_status, used_snapshot=False, mode=use_mode, errors=errors)
    else:
        data = _normalize_info_payload(data, symbol, qname, sid or str(data.get("snapshot_id") or ""), cache_status, used_snapshot=used_snapshot, mode=str(data.get("mode") or use_mode), errors=errors)
        if str(data.get("mode")) == "snapshot_miss":
            data["snapshot_notice"] = "请求的筛选页快照不存在，详情页未自动重抓；请点击普通刷新或深度刷新。"
        else:
            data["snapshot_notice"] = "当前使用筛选页快照；如需深挖请点击深度刷新。" if used_snapshot else "当前使用最近信息快照。"
    allow_history_fallback = bool(not errors and str((data.get("cache_status") or cache_status or {}).get("status") or "") != "error")
    data = _ensure_info_visible_content(data, symbol, qname, limit, allow_history_fallback=allow_history_fallback)
    data = _normalize_info_payload(data, symbol, qname, str(data.get("snapshot_id") or sid or ""), data.get("cache_status") or cache_status, used_snapshot=used_snapshot, mode=str(data.get("mode") or use_mode), errors=data.get("errors") or errors)
    if data.get("snapshot_id"):
        try:
            cache_state_service.save_info_snapshot(str(data.get("snapshot_id")), symbol, data, mode=str(data.get("mode") or use_mode))
        except Exception:
            pass
    data["detail_contract"] = {
        "snapshot_id": data.get("snapshot_id"),
        "limit": limit,
        "force": force,
        "deep_refresh": deep_refresh,
        "mode": data.get("mode"),
        "note": "详情页默认复用 snapshot_id 或最近信息快照；只有 force=true 或 deep_refresh=true 才重新抓取。",
    }
    return {
        "ok": True,
        "symbol": symbol,
        "name": qname,
        "mode": data.get("mode"),
        "snapshot_id": data.get("snapshot_id"),
        "used_snapshot": used_snapshot,
        "created_at": data.get("created_at"),
        "cache_status": data.get("cache_status"),
        "items": data.get("items", []),
        "grouped_items": data.get("grouped_items", []),
        "global_items": data.get("global_items", []),
        "industry_mapped_items": data.get("industry_mapped_items", []),
        "score_model": data.get("score_model", {}),
        "diagnostics": data.get("diagnostics", {}),
        "source_logs": data.get("source_logs", []),
        "errors": data.get("errors", []),
        "data": data,
    }

@app.get("/api/news/search")
def news_search(keyword: str, limit: int = 80, force: bool = False) -> dict:
    data = news_service.search_keyword(keyword, limit=limit, force=force)
    return {"ok": True, "data": data}


def _paged_info_items_from_snapshot(cached, *, page: int, page_size: int, sort: str, category: str | None, source: str | None, include_unknown_date: bool) -> dict | None:
    items = (cached.data or {}).get("items") or []
    if not items:
        return None
    if not include_unknown_date:
        items = [x for x in items if x.get("publish_time") or x.get("published_at_norm") or x.get("published_at") or x.get("date")]
    if category:
        items = [x for x in items if str(x.get("category") or x.get("event_type") or "") == str(category)]
    if source:
        items = [x for x in items if str(x.get("source") or "") == str(source)]
    reverse = str(sort).lower() != "asc"
    items = sorted(items, key=lambda x: str(x.get("publish_time") or x.get("published_at_norm") or x.get("published_at") or x.get("date") or ""), reverse=reverse)
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = 1
    offset = (page - 1) * page_size
    return {
        "data": items[offset:offset + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "stats": {"from_info_snapshot": True, "unknown_date_count": len([x for x in items if not (x.get("publish_time") or x.get("published_at_norm") or x.get("published_at") or x.get("date"))])},
        "cache_status": cached.cache_status,
    }


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
    cached = cache_state_service.latest_info_snapshot(symbol)
    snapshot_page = _paged_info_items_from_snapshot(cached, page=page, page_size=page_size, sort=sort, category=category, source=source, include_unknown_date=include_unknown_date)
    if snapshot_page:
        return {"ok": True, "symbol": symbol, "data": snapshot_page}
    data = news_service.store.list_items_paged(
        symbol, page=page, page_size=page_size, include_history_days=history_days,
        sort=sort, category=category, source=source, include_unknown_date=include_unknown_date
    )
    if not data.get("data"):
        snapshot_page = _paged_info_items_from_snapshot(cached, page=page, page_size=page_size, sort=sort, category=category, source=source, include_unknown_date=include_unknown_date)
        if snapshot_page:
            data = snapshot_page
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

    def present(value) -> bool:
        return value not in (None, "", "--")

    def first_present(*values):
        for value in values:
            if present(value):
                return value
        return None

    def add_or_fill_metric(name: str, value, unit: str = "", better: str = "", *, replace_zero: bool = False) -> None:
        if not present(value):
            return
        for metric in metrics:
            if metric.get("name") == name:
                current = metric.get("value")
                if not present(current) or (replace_zero and current == 0):
                    metric["value"] = value
                    metric["unit"] = metric.get("unit") or unit
                    metric["better"] = metric.get("better") or better
                return
        metrics.append({"name": name, "value": value, "unit": unit, "better": better})

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
            {"name": "信息面分", "value": first_present(info.get("info_score"), news.get("news_score"), item.get("info_score"), item.get("news_score")), "unit": "分"},
            {"name": "事件级正/负权重", "value": f"{news.get('weighted_positive','--')} / {news.get('weighted_negative','--')}", "unit": ""},
            {"name": "新闻条数", "value": first_present(news.get("count"), item.get("info_effective_count"), item.get("news_count")), "unit": "条"},
            {"name": "官方/高可信", "value": (info.get("evidence_counts") or {}).get("high_confidence_items") or news.get("official_count"), "unit": "条"},
            {"name": "重复事件组", "value": first_present(item.get("info_unique_event_count"), len(news.get("duplicate_groups") or [])), "unit": "组"},
        ]
        why.append("信息面采用事件级去重：同一亏损、问询、减持、订单等多源转载只计一次主权重，避免重复标题放大影响。")
        why.append("近期官方信息权重更高，社区/传闻只作为舆情观察，不进入核心利多利空。")
        if item.get("risk_flags") or item.get("tags"):
            why.append("当前解释优先使用本次筛选快照里的标签、风险提示和信息面字段；快照缺少新闻正文时，仍保留标签来源与核心计数字段。")
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
    info = item.get("info") or {}
    news = item.get("news") or {}
    add_or_fill_metric("综合评分", item.get("total_score"), "分")
    add_or_fill_metric("复核评分", item.get("manual_review_score"), "分")
    add_or_fill_metric("技术底分", first_present(item.get("technical_score"), item.get("score_before_strategy")), "分")
    add_or_fill_metric("信息面分", first_present(info.get("info_score"), news.get("news_score"), item.get("info_score"), item.get("news_score")), "分")
    add_or_fill_metric("信息面调分", first_present(item.get("info_score_delta"), item.get("info_delta"), item.get("news_score_delta")), "分")
    add_or_fill_metric("个股有效条目", first_present(item.get("info_effective_count"), info.get("effective_count"), news.get("count")), "条", replace_zero=True)
    add_or_fill_metric("去重事件组", first_present(item.get("info_unique_event_count"), len(news.get("duplicate_groups") or [])), "组", replace_zero=True)
    add_or_fill_metric("快照ID", first_present(item.get("info_snapshot_id"), info.get("snapshot_id"), news.get("snapshot_id")), "")
    if item.get("risk_flags"):
        why.append("风险提示来自当前筛选快照：" + "；".join(str(x) for x in (item.get("risk_flags") or [])[:4]))
    if item.get("missing_data_hints"):
        why.append("缺失提示：" + "；".join(str(x) for x in (item.get("missing_data_hints") or [])[:3]))
    if spec:
        why.insert(0, f"指标知识库：公式={spec.get('formula')}；评判标准={spec.get('judgment')}；应用场景={spec.get('application')}。")
        if spec.get('caveat'):
            why.append(f"使用限制：{spec.get('caveat')}。")
    return {"tag": tag, "symbol": item.get("symbol"), "name": item.get("name"), "conclusion": conclusion, "why": why, "metrics": metrics, "indicator_spec": spec, "indicator_matrix": item.get("indicator_matrix"), "indicator_signals": item.get("indicator_signals", [])[:80], "annotations_preview": annotations, "future_interface": "后续可将 annotations_preview 写入 /api/annotations/{symbol}，在K线图上标注信号点、区间和买卖点。"}


@app.post("/api/screener/explain-row")
def screener_explain_row(payload: dict = Body(...)) -> dict:
    item = payload.get("item") if isinstance(payload, dict) else {}
    tag = str(payload.get("tag") or "") if isinstance(payload, dict) else ""
    if not isinstance(item, dict) or not item.get("symbol"):
        return {"ok": False, "message": "missing selected screener row"}
    if tag:
        return {"ok": True, "data": _tag_explain_from_result(item, tag), "result": item}
    tags = (item.get("tags") or []) + (item.get("risk_flags") or [])
    return {"ok": True, "symbol": item.get("symbol"), "count": len(tags), "data": [_tag_explain_from_result(item, t) for t in tags], "result": item}


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

@app.get("/wordsource", response_class=HTMLResponse)
def wordsource_page() -> str:
    rows = wordsource_trace().get("data", [])
    body = "".join(
        f"<tr><td>{r['status']}</td><td>{r['source']}</td><td>{r['original'][:180]}</td><td>{r['feature']}</td><td>{r['api']}</td><td>{r['frontend']}</td><td>{r['tests']}</td></tr>"
        for r in rows[:800]
    )
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>V3.18.3 WordSource Trace</title>
<style>body{{font-family:Segoe UI,Microsoft YaHei,Arial;margin:0;background:#f8fafc;color:#172033}}header{{background:#0f172a;color:#fff;padding:14px 18px}}main{{padding:16px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #e5e7eb;padding:8px;vertical-align:top;font-size:13px}}th{{background:#e2e8f0}}.pill{{padding:3px 8px;border-radius:999px;background:#dbeafe}}</style></head>
<body><header><b>Quant Data Gateway V3.18.3 / WordSource Stable Recovery</b> <span class='pill'>逐条映射可见</span> <a style='color:#bfdbfe;margin-left:12px' href='/screener'>筛选页</a></header>
<main><div class='pill'>API: /api/wordsource/trace</div><h2>WordSource 原文映射</h2><p>每条显示原文、功能、API、前端位置、测试与落地状态；部分落地项会继续保留为待验收。</p>
<table><thead><tr><th>状态</th><th>来源</th><th>原文</th><th>功能</th><th>API</th><th>前端</th><th>测试</th></tr></thead><tbody id='traceRows'>{body or '<tr><td colspan=7>暂无映射，请检查 docs/WORD_SOURCE_TRACE.md</td></tr>'}</tbody></table></main></body></html>"""


@app.get("/technical/{symbol}", response_class=HTMLResponse)
def technical_page(symbol: str) -> str:
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>V3.18.3 技术因子矩阵</title>
<style>body{{font-family:Segoe UI,Microsoft YaHei,Arial;background:#f8fafc;margin:0}}header{{background:#0f172a;color:#fff;padding:14px 18px}}main{{padding:16px}}table{{width:100%;border-collapse:collapse;background:#fff}}td,th{{border:1px solid #e5e7eb;padding:8px;font-size:13px;vertical-align:top}}th{{background:#e2e8f0}}.ok{{color:#166534}}</style></head>
<body><header><b>Quant Data Gateway V3.18.3 技术因子矩阵</b> <a style='color:#bfdbfe;margin-left:12px' href='/screener'>筛选页</a></header>
<main><h2 id='title'>{symbol} 技术因子矩阵</h2><div id='cache'>缓存状态读取中...</div><p id='factorNote'>说明：这里是逐指标技术因子矩阵，不是策略库清单；0 / 0 表示该因子本次为中性或仅展示闭环字段，真正缺数据会进入数据质量/缺失提示。</p><table><thead><tr><th>因子</th><th>类别</th><th>值</th><th>公式</th><th>信号</th><th>解释</th><th>贡献/扣分</th></tr></thead><tbody id='rows'><tr><td colspan='7'>加载中...</td></tr></tbody></table></main>
<script>
const esc=s=>String(s??'').replace(/[&<>]/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]));
fetch('/api/technical/factors/{symbol}').then(r=>r.json()).then(js=>{{document.getElementById('cache').innerHTML='缓存状态：<b class=ok>'+esc(js.cache_status?.status||'--')+'</b>；因子数 '+esc(js.factor_count||0)+'；V3.18.3';document.getElementById('rows').innerHTML=(js.factors||[]).map(f=>`<tr><td>${{esc(f.name)}}<br><small>${{esc(f.key)}}</small></td><td>${{esc(f.category)}}</td><td>${{esc(JSON.stringify(f.value))}}</td><td>${{esc(f.formula)}}<br><small>${{esc(JSON.stringify(f.params||{{}}))}}</small></td><td>${{esc(f.signal)}}</td><td>${{esc(f.explanation)}}</td><td>${{esc(f.score_contribution)}} / ${{esc(f.risk_penalty)}}<br><small>${{esc(f.score_note||'')}}</small></td></tr>`).join('')||'<tr><td colspan=7>空状态：暂无因子，请检查K线缓存</td></tr>';}}).catch(e=>{{document.getElementById('rows').innerHTML='<tr><td colspan=7>空状态：技术因子读取失败 '+esc(e)+'</td></tr>'}})
</script></body></html>"""


@app.get("/health", response_class=HTMLResponse)
def health_page() -> str:
    return """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>V3.18.3 数据源健康</title><style>body{font-family:Segoe UI,Microsoft YaHei,Arial;margin:0;background:#f8fafc}header{background:#0f172a;color:#fff;padding:14px 18px}main{padding:16px}.box{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin-bottom:12px;white-space:pre-wrap}</style></head><body><header><b>Quant Data Gateway V3.18.3 数据源健康状态</b></header><main><div class='box' id='box'>加载中...</div><script>fetch('/api/market/health').then(r=>r.json()).then(js=>{box.textContent='缓存状态可见 / 休市状态可见 / 最近错误可见\\n'+JSON.stringify(js,null,2)}).catch(e=>box.textContent='空状态：健康检查失败 '+e)</script></main></body></html>"""


@app.get("/cache", response_class=HTMLResponse)
def cache_page() -> str:
    return """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>V3.18.3 Cache Diagnostics / 缓存状态</title><style>body{font-family:Segoe UI,Microsoft YaHei,Arial;margin:0;background:#f8fafc;color:#1f2937}header{background:#0f172a;color:#fff;padding:14px 18px;display:flex;justify-content:space-between}main{padding:16px}.hint{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;border-radius:10px;padding:10px;margin:10px 0}table{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 4px 16px rgba(15,23,42,.07)}td,th{border:1px solid #e5e7eb;padding:8px;vertical-align:top;font-size:13px}th{background:#f1f5f9}.bad{color:#b91c1c}.ok{color:#166534}button{border:1px solid #2563eb;background:#2563eb;color:#fff;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer}.small{font-size:12px;color:#64748b;line-height:1.5}</style></head><body><header><b>Quant Data Gateway V3.18.3 Cache Diagnostics / 缓存状态</b><span><a style='color:#bfdbfe' href='/screener'>Screener</a> | <a style='color:#bfdbfe' href='/health'>Health</a></span></header><main><button onclick='clearCache()'>Clear cache</button><div class='hint'>缓存状态 visible. Persistent cache diagnostics: counts, TTL, latest read/write keys, miss reasons and errors. If kline_cache is zero, the diagnostic explains whether no successful write happened or the latest source failed. API: /api/cache/status. Compatibility marker: V3.18.1 Cache Diagnostics.</div><table><thead><tr><th>Kind</th><th>Count</th><th>Latest update</th><th>TTL</th><th>Status</th><th>Last write key</th><th>Last read key</th><th>miss/error diagnostic</th></tr></thead><tbody id='rows'><tr><td colspan=8>Loading...</td></tr></tbody></table><script>function esc(s){return String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]))}function load(){fetch('/api/cache/status').then(r=>r.json()).then(js=>{rows.innerHTML=(js.items||[]).map(x=>`<tr><td>${esc(x.kind)}</td><td>${x.count}</td><td>${esc(x.latest_updated||'--')}</td><td>${x.ttl_seconds}</td><td class='${x.latest_status==='hit'||x.count?'ok':'bad'}'>${esc(x.latest_status||'--')}</td><td>${esc(x.last_write_key||'--')}</td><td>${esc(x.last_read_key||'--')}</td><td><div>${esc(x.diagnostic||'--')}</div><div class='small'>miss=${esc(x.recent_miss_reason||'--')}<br>error=${esc(x.recent_error||'--')}</div></td></tr>`).join('')||'<tr><td colspan=8>Empty state: run screener or open a detail page to populate cache.</td></tr>'})}function clearCache(){fetch('/api/cache/clear',{method:'POST'}).then(load)}load()</script></main></body></html>"""


@app.get("/info", response_class=HTMLResponse)
def info_page() -> str:
    return build_info_ui()


@app.get("/screener", response_class=HTMLResponse)
def screener_page() -> str:
    return build_screener_ui()


@app.get("/backtest", response_class=HTMLResponse)
def backtest_page() -> str:
    return build_backtest_ui()


@app.get("/backtest/trades", response_class=HTMLResponse)
def backtest_trades_page() -> str:
    return build_backtest_trades_ui()


@app.get("/paper", response_class=HTMLResponse)
def paper_page() -> str:
    return build_paper_ui()


@app.get("/chart/{symbol}", response_class=HTMLResponse)
def chart_page(symbol: str, frame: str = "time") -> str:
    return _build_ui(initial_symbol=symbol, full=True, initial_frame=frame)


@app.get("/ui", response_class=HTMLResponse)
def ui(symbol: str = "300750") -> str:
    return _build_ui(initial_symbol=symbol or "300750", full=False, initial_frame="time")


def _build_ui(initial_symbol: str, full: bool = False, initial_frame: str = "time") -> str:
    return build_ui_v22(initial_symbol=initial_symbol, full=full, initial_frame=initial_frame)
