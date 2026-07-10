from __future__ import annotations

import time as time_module
from concurrent.futures import ThreadPoolExecutor
import re
from dataclasses import fields, replace
from datetime import datetime, time
from pathlib import Path
from statistics import mean
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from quant_data import __version__
from quant_data.market_calendar import MarketCalendar
from quant_data.models import AssetType, Bar, IntradayPoint, OrderBook, Quote
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
from quant_data.services.orderbook_behavior_service import OrderBookBehaviorService
from quant_data.services.trading_framework_service import compute_indicator50_snapshot
from quant_data.services.market_behavior_engine import MarketBehaviorEngine
from quant_data.services.cache_state_service import CacheStateService
from quant_data.services.fundamental_library_service import FundamentalLibraryService
from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.info_analysis_service import InfoAnalysisService
from quant_data.services.company_profile_service import CompanyProfileService
from quant_data.services.global_industry_mapper import GlobalIndustryMapper
from quant_data.services.technical_factor_engine import TechnicalFactorEngine
from quant_data.services.background_cache_service import BackgroundCacheService
from quant_data.services.backtest_service import BacktestConfig as LegacyBacktestConfig, BacktestService, SCORE_FORMULA
from quant_data.utils import normalize_symbol
from quant_data.backtest import BacktestConfig as V319BacktestConfig, StrategyHorizonConfig, StrategySignal
from quant_data.backtest.position_sizing import PositionSizingConfig
from quant_data.backtest.engine import BacktestEngine, BacktestEngineV320
from quant_data.backtest.historical_snapshot import HistoricalScreenerSnapshotBuilder
from quant_data.backtest.market_rules import MarketRuleEngine
from quant_data.backtest.optimizer import ParameterOptimizer
from quant_data.backtest.paper_broker import PaperBroker
from quant_data.backtest.report import build_report
from quant_data.backtest.storage import BacktestStorage
from quant_data.backtest.walk_forward import WalkForwardValidator
from quant_data.screener_ui import build_screener_ui
from quant_data.info_ui import build_info_ui
from quant_data.ui_v22 import build_ui_v22
from quant_data.backtest_ui import build_backtest_trades_ui, build_backtest_ui, build_paper_ui
from quant_data.realtime_paper_ui import build_realtime_paper_ui
from quant_data.live_trading_ui import build_live_trading_ui
from quant_data.trading_records_ui import build_trading_records_ui
from quant_data.data_center_ui import build_data_center_ui
from quant_data.auto_trading_workbench_ui import build_auto_trading_workbench_ui
from quant_data.chart import ChartAnnotationService
from quant_data.data import (
    PITStore,
    build_fundamentals_snapshot,
    build_news_snapshot,
    build_quote_snapshot,
    default_source_registry,
    market_session_status,
)
from quant_data.live import LiveTradingEngine
from quant_data.persistence import TradingStore
from quant_data.realtime import RealtimePaperEngineV323
from quant_data.scoring import (
    ScoreRequest,
    SignalFusionV323,
    V323FactorEngine,
    build_score_provenance_v323,
    explain_score,
)
from quant_data.strategy import StockClassifierV323, StrategySuitabilityV323
from quant_data.trading import (
    AnomalyGuard,
    DataFreshnessGuard,
    PaperTradingGateway,
    RealtimePaperEngine,
    SignalFusionEngine,
    TradingSignal,
)


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
orderbook_behavior_service = OrderBookBehaviorService()
cache_state_service = CacheStateService()
background_cache_service = BackgroundCacheService(cache_state_service=cache_state_service, watchlist_service=watchlist_service)
technical_factor_engine = TechnicalFactorEngine()
backtest_service = BacktestService()
backtest_engine_v319 = BacktestEngine(service)
backtest_engine_v320 = BacktestEngineV320(service)
backtest_storage_v319 = BacktestStorage()
historical_snapshot_builder_v322 = HistoricalScreenerSnapshotBuilder()
market_rule_engine_v322 = MarketRuleEngine.default()
paper_broker_v319 = PaperBroker(V319BacktestConfig())
paper_trading_gateway_v320 = PaperTradingGateway()
realtime_paper_engine_v321 = RealtimePaperEngine(
    signal_fusion=SignalFusionEngine(),
    anomaly_guard=AnomalyGuard(),
    freshness_guard=DataFreshnessGuard(),
)
trading_store_v323 = TradingStore()
pit_store_v323 = PITStore()
chart_annotation_service_v323 = ChartAnnotationService()
source_registry_v323 = default_source_registry()
factor_engine_v323 = V323FactorEngine()
stock_classifier_v323 = StockClassifierV323()
strategy_suitability_v323 = StrategySuitabilityV323()
live_trading_engine_v323 = LiveTradingEngine(store=trading_store_v323)
realtime_paper_engine_v323 = RealtimePaperEngineV323(realtime_paper_engine_v321, trading_store_v323)
score_provenance_memory_v323: dict[str, dict] = {}
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
app = FastAPI(title="量化数据网关 API", version=__version__, description="A股/ETF 实时行情、筛选、回测、评分溯源与纸面交易系统。", docs_url=None, redoc_url=None)

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


@app.get("/docs", include_in_schema=False)
def swagger_api_docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="量化数据网关 API 调试",
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": -1,
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
            "filter": True,
        },
    )


def _render_chinese_api_docs() -> str:
    groups = [
        (
            "行情与盘口",
            [
                ("GET", "/api/quotes?symbols=300750,600519&force=false", "批量实时行情。force=false 时优先使用交易时段缓存，休市后不反复刷新。"),
                ("GET", "/api/timeline/{symbol}?force=false", "分时走势。只返回真实分时或同交易日缓存，不伪造分时线。"),
                ("GET", "/api/orderbook/{symbol}?force=true", "五档盘口。公开源缺 Level-2 时返回缺失原因、委比和委差兜底字段。"),
                ("GET", "/api/detail/{symbol}?frame=1d&limit=520&adjust=qfq", "K线详情，支持分时、日K、周K、月K、副图、行为标注和缓存状态。"),
            ],
        ),
        (
            "筛选与策略",
            [
                ("GET", "/api/strategy/library", "完整策略库。返回 key、中文名、分类、说明、默认权重和默认选中项。"),
                ("GET", "/api/screener/run", "执行筛选，支持股票池、策略组合、排序、缓存快照、技术面和信息面字段。"),
                ("GET", "/api/cache/screener/latest", "读取最近筛选快照，用于页面恢复和休市缓存兜底。"),
                ("GET", "/api/technical/factors/{symbol}", "技术因子矩阵，返回指标分类、原始值、解释、方向和评分。"),
            ],
        ),
        (
            "回测系统",
            [
                ("GET", "/api/backtest/run", "单标的快速回测。参数可在 /docs 中直接调试，保留英文键名以兼容前端。"),
                ("POST", "/api/backtest/run", "V3.20/V3.22 科学回测入口，支持多标的、订单撮合、成本、滑点、组合约束和评分溯源。"),
                ("GET", "/api/backtest/v322/readiness", "V3.22 能力检查：评分溯源、规则引擎、资金管理、纸面交易和历史快照。"),
                ("GET", "/api/market-rules/profiles", "交易规则配置，按生效日期返回涨跌停、T+1、买入手数、卖出零股等规则。"),
                ("GET", "/backtest?symbol=300750", "回测可视化页面，K线标注买入、卖出、异常点，并提供买卖流水内置窗口。"),
            ],
        ),
        (
            "纸面交易",
            [
                ("POST", "/api/realtime-paper/start", "启动盘中纸面交易，只模拟不连真实券商。"),
                ("GET", "/api/realtime-paper/status", "查看资金、持仓、最近信号、风险拦截和人工确认队列数量。"),
                ("GET", "/api/realtime-paper/orders", "纸面订单流水。"),
                ("GET", "/api/realtime-paper/confirmations", "需要人工确认的候选交易。"),
            ],
        ),
        (
            "自动交易 V3.23",
            [
                ("GET", "/auto-trading", "自动交易总控台入口，汇总筛选、详情、回测、实时模拟、真实交易、记录和数据中心。"),
                ("GET", "/api/auto-trading/config", "读取当前自动交易配置，包含股票池、策略组合、仓位模型、止盈止损、最大回撤和事件监控。"),
                ("POST", "/api/auto-trading/config/one-click", "从最新筛选/自选池一键生成配置；没有真实数据时只标注缺失，不伪造。"),
                ("GET", "/api/auto-trading/readiness", "检查 paper/live readiness，显示 QMT/PTrade、kill switch、确认队列和风控门槛。"),
                ("POST", "/api/auto-trading/start-paper", "使用保存的 V3.23 配置启动实时模拟 session，订单/成交/持仓/标注/审计落 SQLite。"),
                ("GET", "/api/news/jin10/realtime", "金十/金十期货直连快讯流；优先公开 JSON 接口，页面摘要兜底，不抓搜索结果页。"),
                ("GET", "/api/agent/market-brief", "联网证据代理：聚合金十快讯、全球宏观事件、评分溯源和实盘安全状态，只做辅助判断，不自动下单。"),
                ("POST", "/api/live/orders/preview-batch", "真实交易多股票批量预检查；逐只经过风控、白名单、kill switch 和确认要求，不会直接下单。"),
                ("POST", "/api/live/orders/place-batch", "真实交易多股票批量提交入口；默认配置下会被禁用或进入确认队列，不能绕过安全门控。"),
            ],
        ),
        (
            "信息面与大盘",
            [
                ("GET", "/api/info/{symbol}", "个股信息面分析，包含新闻、公告、风险事件和来源可信度。"),
                ("GET", "/api/market/regime", "大盘环境分析，可用于评分里的市场情绪权重。"),
                ("GET", "/api/screener/historical-snapshot?symbols=300750,600438", "按决策时点重建筛选快照，保证回测不偷看未来。"),
            ],
        ),
    ]
    params = [
        ("symbol", "标的代码", "300750、600438、510300"),
        ("strategy", "回测策略", "score_driven、score_reversal、combo_signal"),
        ("strategy_combo", "组合策略 key，逗号分隔", "ma_repair,macd_cross,risk_control"),
        ("initial_cash", "初始资金", "100000"),
        ("position_pct", "仓位比例", "0.5 到 1.0"),
        ("stop_loss_pct / take_profit_pct", "止损 / 止盈百分比", "8 / 20；0 表示关闭固定止盈"),
        ("position_sizing", "仓位模式", "score_weighted、volatility_target、atr_risk、dca、pyramid"),
        ("horizon", "交易周期", "short_term、swing、position、dca、hybrid"),
        ("market_weight", "大盘情绪权重", "0.14，可与其他三面权重一起调"),
        ("force", "是否强制刷新", "false；休市确认后建议保持 false"),
    ]
    sections = []
    for title, rows in groups:
        items = "".join(
            f"<tr><td><b>{method}</b></td><td><code>{path}</code></td><td>{desc}</td></tr>"
            for method, path, desc in rows
        )
        sections.append(f"<section><h2>{title}</h2><table><tbody>{items}</tbody></table></section>")
    param_rows = "".join(
        f"<tr><td><code>{key}</code></td><td>{desc}</td><td>{example}</td></tr>"
        for key, desc, example in params
    )
    sections.append(f"<section><h2>常用参数中文说明</h2><table><tbody>{param_rows}</tbody></table></section>")
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>量化数据网关 API 文档</title><style>
body{margin:0;background:#0b1020;color:#dbeafe;font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;line-height:1.55}
header{position:sticky;top:0;background:#101827;border-bottom:1px solid #283956;padding:16px 22px;z-index:2}
h1{margin:0;font-size:24px}main{max-width:1160px;margin:0 auto;padding:18px 18px 40px}
section{background:#101827;border:1px solid #283956;border-radius:12px;margin:12px 0;overflow:hidden}
h2{font-size:18px;margin:0;padding:12px 14px;background:#141e32;border-bottom:1px solid #283956}
table{width:100%;border-collapse:collapse}td{padding:10px 12px;border-bottom:1px solid rgba(40,57,86,.72);vertical-align:top}
td:first-child{width:180px;color:#93c5fd}td:nth-child(2){width:430px}code{color:#bfdbfe;background:#172033;border:1px solid #26364f;border-radius:8px;padding:3px 6px}
.note{color:#9fb2d4;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:12px;margin:12px 0}
a{color:#93c5fd}</style></head><body><header><h1>量化数据网关 API 文档</h1></header><main>
<div class="note">中文页用于快速理解接口。需要直接填写参数并调用时，请打开 <a href="/docs">/docs API 调试页</a>；它保留 Try it out，可调所有查询参数和 POST JSON。程序化调用可读取 <a href="/openapi.json">/openapi.json</a>。</div>
""" + "".join(sections) + "</main></body></html>"


@app.get("/docs-cn", response_class=HTMLResponse, include_in_schema=False)
def chinese_api_docs() -> str:
    return _render_chinese_api_docs()
    groups = [
        ("行情与盘口", [
            ("GET", "/api/quotes?symbols=300750,600519&force=false", "批量实时行情，返回最新价、涨跌幅、成交额、换手率、量比、市值、缺失原因。"),
            ("GET", "/api/timeline/{symbol}?force=false", "分时走势。只返回真实分时或同交易日缓存，不伪造分时线。"),
            ("GET", "/api/orderbook/{symbol}?force=true", "五档盘口。公开源缺 Level-2 时返回委比、委差和缺失说明。"),
            ("GET", "/api/detail/{symbol}?frame=1d&limit=520&adjust=qfq", "K线详情，支持日K、周K、月K、复权、行为标注和缓存状态。"),
        ]),
        ("筛选与策略", [
            ("GET", "/api/strategy/library", "完整策略库，包含低位、趋势、量价、风控、基本面、消息面、宏观等策略元数据。"),
            ("GET", "/api/screener/run", "执行筛选，支持自选池、策略组合、排序、信息面/技术面字段。"),
            ("GET", "/api/cache/screener/latest", "读取最近筛选快照，用于页面恢复和缓存兜底。"),
            ("GET", "/api/technical/factors/{symbol}", "技术因子矩阵，返回指标分类、原始值、解释、方向和评分。"),
        ]),
        ("回测系统", [
            ("GET", "/api/backtest/run", "单标的回测。支持组合策略、仓位模式、交易周期、止损止盈、复利、ATR风险、金字塔和定投。"),
            ("POST", "/api/backtest/run", "V3.20科学回测入口，支持多标的、订单撮合、成本、滑点和组合约束。"),
            ("GET", "/api/backtest/strategies", "回测策略列表。"),
            ("GET", "/backtest?symbol=300750", "回测可视化页面，K线标注买入、卖出、异常点，并提供买卖流水内置窗口。"),
        ]),
        ("盘中模拟交易", [
            ("POST", "/api/realtime-paper/start", "启动纸面盘中模拟，使用信号融合、异常防护和风险网关。"),
            ("GET", "/api/realtime-paper/status", "查看模拟交易状态、资金、持仓和最近信号。"),
            ("GET", "/api/realtime-paper/orders", "订单流水。"),
            ("GET", "/api/realtime-paper/audit", "风险与执行审计记录。"),
        ]),
        ("信息面与大盘", [
            ("GET", "/api/info/{symbol}", "个股信息面分析，包含新闻、公告、风险事件和来源可信度。"),
            ("GET", "/api/wordsource/report/{symbol}", "信息面/技术面/资金面映射报告。"),
            ("GET", "/api/market/regime", "大盘环境分析，用于评分中的市场情绪权重。"),
            ("GET", "/api/source-knowledge", "数据源知识库和覆盖说明。"),
        ]),
        ("系统与缓存", [
            ("GET", "/api/calendar/status", "交易时段、午休、休市和下一次刷新时间。"),
            ("GET", "/api/cache/status", "缓存健康状态。"),
            ("POST", "/api/background/refresh/watchlist", "后台刷新监控列表。"),
            ("GET", "/openapi.json", "机器可读 OpenAPI JSON。"),
        ]),
    ]
    sections = []
    for title, rows in groups:
        items = "".join(
            f"<tr><td><b>{method}</b></td><td><code>{path}</code></td><td>{desc}</td></tr>"
            for method, path, desc in rows
        )
        sections.append(f"<section><h2>{title}</h2><table><tbody>{items}</tbody></table></section>")
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>量化数据网关 API 文档</title><style>
body{margin:0;background:#0b1020;color:#dbeafe;font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;line-height:1.55}
header{position:sticky;top:0;background:#101827;border-bottom:1px solid #283956;padding:16px 22px;z-index:2}
h1{margin:0;font-size:24px}main{max-width:1160px;margin:0 auto;padding:18px 18px 40px}
section{background:#101827;border:1px solid #283956;border-radius:12px;margin:12px 0;overflow:hidden}
h2{font-size:18px;margin:0;padding:12px 14px;background:#141e32;border-bottom:1px solid #283956}
table{width:100%;border-collapse:collapse}td{padding:10px 12px;border-bottom:1px solid rgba(40,57,86,.72);vertical-align:top}
td:first-child{width:72px;color:#93c5fd}td:nth-child(2){width:390px}code{color:#bfdbfe;background:#172033;border:1px solid #26364f;border-radius:8px;padding:3px 6px}
.note{color:#9fb2d4;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:12px;margin:12px 0}
a{color:#93c5fd}</style></head><body><header><h1>量化数据网关 API 文档</h1></header><main>
<div class="note">这是中文 API 总览页。需要填写参数并直接调用接口时使用 <a href="/docs">/docs 交互调试页</a>；程序化调试可使用 <a href="/openapi.json">/openapi.json</a>；页面入口包括 <a href="/auto-trading">自动交易总控台 V3.23</a>、<a href="/ui">行情监控</a>、<a href="/screener">筛选系统</a>、<a href="/backtest">交易回测</a>、<a href="/realtime-paper">实时模拟</a>、<a href="/live-trading">真实交易</a>、<a href="/trading-records">交易记录</a>、<a href="/data-center">数据中心</a>。</div>
""" + "".join(sections) + "</main></body></html>"




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
        behavior = market_behavior_engine.analyze(q, bars, recent_days=7) if len(bars) >= 5 else market_behavior_engine.analyze(q, [])
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
    if q and getattr(q, "ts", None):
        return q.ts.date()
    market = q.market if q else "CN"
    session = _market_session(market)
    status = str(session.get("status") or "")
    if status not in {"pre_open_auction", "morning", "lunch", "afternoon", "closing_auction", "call_auction_cooldown"}:
        return None
    try:
        return datetime.fromisoformat(str(session.get("date"))).date()
    except Exception:
        return None


def _filter_timeline_date(points: list[IntradayPoint], expected) -> list[IntradayPoint]:
    if expected is None:
        return points
    same_day = [p for p in points if getattr(getattr(p, "ts", None), "date", lambda: None)() == expected]
    return same_day or points


def _filter_timeline_quote_range(points: list[IntradayPoint], q: Quote | None) -> list[IntradayPoint]:
    if not points or q is None:
        return points
    highs = [_safe_float(v) for v in [q.high, q.open, q.last, q.pre_close] if _safe_float(v) > 0]
    lows = [_safe_float(v) for v in [q.low, q.open, q.last, q.pre_close] if _safe_float(v) > 0]
    if not highs or not lows:
        return points
    hi = max(highs)
    lo = min(lows)
    if hi <= 0 or lo <= 0 or hi < lo:
        return points
    pad = max((hi - lo) * 0.08, hi * 0.015, 0.02)
    upper = hi + pad
    lower = max(0.01, lo - pad)
    clean: list[IntradayPoint] = []
    for p in points:
        price = _safe_float(getattr(p, "price", None))
        if lower <= price <= upper:
            avg = _safe_float(getattr(p, "avg_price", None))
            if avg and not (lower <= avg <= upper):
                p = replace(p, avg_price=price)
            clean.append(p)
    return clean


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
    clean = _filter_timeline_quote_range(clean, q)
    if len(clean) < 2:
        return []
    return clean


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/auto-trading")


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
    market = _detect_market(symbol)
    session = _market_session(market)
    if not force and not session.get("can_refresh"):
        cache_read = cache_state_service.get("quote_cache", symbol, allow_stale=True)
        q = _quote_from_dict((cache_read.data or {}).get("quote") if cache_read.data else None)
        points = _clean_intraday_points(service.cache.get_intraday(symbol))
        if q is not None:
            points = _filter_timeline_quote_range(points, q)
        latest_date = _timeline_latest_date(points)
        return {
            "ok": True,
            "server_time": datetime.now().isoformat(timespec="seconds"),
            "force": force,
            "symbol": symbol,
            "session": session,
            "quote": q.to_dict() if q else None,
            "quote_extra": _quote_extra(q) if q else {},
            "count": len(points),
            "cache_fast_path": True,
            "data_quality": {
                "expected_date": None,
                "latest_date": latest_date.isoformat() if latest_date else None,
                "fresh_for_session": bool(points),
                "stale_cache_rejected": False,
                "note": "休市/午休不可刷新：已直接返回本地真实分时缓存；无缓存时前端显示缺失，不触发外部慢接口。",
                "quote_cache_status": cache_read.cache_status,
            },
            "data": [p.to_dict() for p in points],
        }
    q = None
    try:
        q = _enrich_quote_real(symbol, force=force)[0]
    except Exception:
        q = None
    points = _timeline_with_fallback(symbol, q, force=force)
    market = q.market if q else market
    expected_date = _timeline_expected_date(q)
    latest_date = _timeline_latest_date(points)
    stale_rejected = bool(expected_date is not None and latest_date is None)
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
            "note": "实时分时源暂无当日有效点，未使用跨日缓存或异常价格缓存" if stale_rejected else "",
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
def detail(
    symbol: str,
    frame: str = "1d",
    limit: int = 260,
    adjust: str = "none",
    force: bool = False,
    include_timeline: bool = False,
    refresh: bool = False,
    include_quote: bool = True,
) -> dict:
    force = bool(force or refresh)
    if frame not in {"1d", "1w", "1M", "1mo"}:
        frame = "1d"
    if frame == "1mo":
        frame = "1M"
    quote_error = None
    q = None
    if include_quote:
        try:
            q = _enrich_quote_real(symbol, force=force)[0]
        except Exception as exc:
            quote_error = str(exc)
    kpayload = _safe_kline_payload(symbol, frame=frame, limit=limit, adjust=adjust, force=force, sync_quote=False)
    bars_data = kpayload.get("bars") or []
    if limit and len(bars_data) > limit:
        bars_data = bars_data[-max(1, int(limit)):]
    bars = [Bar(symbol=x.get("symbol") or symbol, frame=frame, ts=datetime.fromisoformat(str(x.get("ts")).replace("Z", "+00:00")).replace(tzinfo=None) if x.get("ts") else datetime.now(), open=float(x.get("open") or 0), high=float(x.get("high") or 0), low=float(x.get("low") or 0), close=float(x.get("close") or 0), volume=float(x.get("volume") or 0), amount=float(x.get("amount") or 0), turnover=x.get("turnover"), change_pct=x.get("change_pct"), source=x.get("source") or "cache_state") for x in bars_data]
    if q is None and bars:
        b = bars[-1]
        q = Quote(symbol=symbol, name=symbol, ts=b.ts, last=b.close, pre_close=b.open, open=b.open, high=b.high, low=b.low, volume=b.volume, amount=b.amount, change=b.close-b.open, change_pct=b.change_pct, turnover=b.turnover, source="bar_snapshot")
    if q is not None and include_quote:
        q, qd, quote_cache_status = _enrich_quote_real(symbol, force=False, quote_obj=q, bars=bars)
        bars, synced, sync_reason = _sync_daily_bar_with_quote(bars, q, frame, adjust)
        points = _timeline_with_fallback(symbol, q, force=force) if include_timeline else []
        qd["extra"] = _quote_extra(q)
        qd["cache_status"] = quote_cache_status
        session = _market_session(q.market)
        out_symbol = q.symbol
    elif q is not None:
        synced, sync_reason, points = False, "quote_skipped", []
        qd = q.to_dict()
        qd["extra"] = _quote_extra(q)
        qd["cache_status"] = {"status": "skipped", "source": "include_quote=false"}
        session = _market_session(q.market)
        out_symbol = q.symbol
    else:
        synced, sync_reason, points, qd, session, out_symbol = False, "quote_unavailable", [], None, _market_session(_detect_market(symbol)), symbol
    if limit and len(bars) > limit:
        bars = bars[-max(1, int(limit)) :]
    behavior = market_behavior_engine.analyze(q, bars, intraday=points, recent_days=7) if len(bars) >= 5 else kpayload.get("behavior_analysis") or market_behavior_engine.analyze(q, [])
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
    normalized = re.sub(r"[，；;、|\s]+", ",", symbols or "")
    parsed = [x.strip() for x in normalized.split(",") if x.strip()]
    if parsed:
        return parsed
    return [x.strip() for x in re.split(r"[\s,，;；、|]+", symbols or "") if x.strip()]


def _symbols_from_payload(payload: dict | None) -> list[str]:
    payload = payload or {}
    raw = payload.get("symbols") or payload.get("watchlist") or payload.get("symbol") or ""
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return _parse_symbol_text(str(raw))


AUTO_TRADING_CONFIG_TTL_SECONDS = 7 * 24 * 60 * 60
DEFAULT_AUTO_STRATEGY_COMBO = [
    "score_driven",
    "low_position",
    "avoid_chasing_high",
    "source_reliability",
    "ma_repair",
    "macd_cross",
    "macd_hist_turn",
    "volume_breakout",
    "mfi_obv_resonance",
    "rsi_kdj_resonance",
    "atr_risk",
    "position_risk",
    "risk_control",
    "event_driven",
    "finance_quality",
    "fundamental_quality",
    "cashflow_quality",
    "announcement_risk",
    "policy_tailwind",
    "macro_liquidity",
    "main_money_est",
    "market_regime",
]

AUTO_TRADING_VIRTUAL_STRATEGIES = {
    "score_driven": {
        "key": "score_driven",
        "name": "日常评分驱动",
        "category": "核心评分",
        "tags": ["score", "four-side"],
        "description": "把技术面、基本面、信息面、资金面和大盘情绪作为主决策锚点，适合作为新手默认策略骨架。",
        "default_weight": 1.0,
        "enabled": True,
    },
    "market_regime": {
        "key": "market_regime",
        "name": "大盘情绪过滤",
        "category": "风险控制",
        "tags": ["index", "sentiment", "risk"],
        "description": "当上证、创业板、宽基指数趋势或市场波动不利时，降低新开仓和追高冲动。",
        "default_weight": 0.8,
        "enabled": True,
    },
}

AUTO_TRADING_BEGINNER_PRESETS = {
    "balanced": {
        "label": "均衡入门",
        "description": "给金融基础不多的用户使用：评分驱动为主，保留清晰止损、止盈、仓位上限和数据新鲜度检查。",
        "strategy_family": "hybrid",
        "position_sizing": "score_weighted",
        "strategy_combo": [
            "score_driven",
            "low_position",
            "ma_repair",
            "macd_cross",
            "volume_breakout",
            "risk_control",
            "event_driven",
            "finance_quality",
            "market_regime",
        ],
        "risk_controls": {"stop_loss_pct": 8, "take_profit_pct": 18, "max_drawdown_pct": 18, "max_single_position_pct": 20, "max_total_position_pct": 80, "min_cash_pct": 15},
    },
    "defensive": {
        "label": "防守学习",
        "description": "适合弱市或刚开始学习：单票仓位更低，止损更严格，重大负面、数据缺失和大盘风险优先拦截。",
        "strategy_family": "hybrid",
        "position_sizing": "cash_first_defensive",
        "strategy_combo": [
            "score_driven",
            "avoid_chasing_high",
            "source_reliability",
            "ma_repair",
            "atr_risk",
            "position_risk",
            "risk_control",
            "announcement_risk",
            "market_regime",
        ],
        "risk_controls": {"stop_loss_pct": 6, "take_profit_pct": 12, "max_drawdown_pct": 10, "max_single_position_pct": 10, "max_total_position_pct": 45, "min_cash_pct": 35},
    },
    "etf_rotation": {
        "label": "ETF动量轮动",
        "description": "维护 ETF 池，按动量和趋势排序，先通过回撤、滑点和实时模拟验证，再进入实盘确认流程。",
        "strategy_family": "etf_momentum_rotation",
        "position_sizing": "equal_risk_contribution",
        "strategy_combo": [
            "score_driven",
            "etf_liquidity",
            "ma_repair",
            "adx_trend",
            "atr_risk",
            "position_risk",
            "risk_control",
            "market_regime",
        ],
        "risk_controls": {"stop_loss_pct": 5, "take_profit_pct": 0, "max_drawdown_pct": 8, "max_single_position_pct": 25, "max_total_position_pct": 90, "min_cash_pct": 10},
    },
}


def _auto_strategy_catalog() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for item in strategy_library_service.list():
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if not key:
            continue
        row = dict(item)
        row["auto_default"] = key in DEFAULT_AUTO_STRATEGY_COMBO
        row["beginner_note"] = "可作为组合里的一个信号开关；最终买卖仍会经过统一评分、数据新鲜度和风控网关。"
        rows.append(row)
        seen.add(key)
    for key, item in AUTO_TRADING_VIRTUAL_STRATEGIES.items():
        if key in seen:
            continue
        row = dict(item)
        row["auto_default"] = key in DEFAULT_AUTO_STRATEGY_COMBO
        row["beginner_note"] = "V3.23 自动交易工作流核心策略。"
        rows.insert(0, row)
    return rows


def _auto_strategy_meta_map() -> dict[str, dict]:
    return {str(x.get("key")): x for x in _auto_strategy_catalog() if x.get("key")}


def _auto_beginner_presets() -> dict:
    return {key: dict(value) for key, value in AUTO_TRADING_BEGINNER_PRESETS.items()}


def _as_float(value, default: float) -> float:
    try:
        if value in (None, ""):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _first_present(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是", "开启", "启用"}


def _strategy_combo_from(raw) -> list[str]:
    if isinstance(raw, list):
        combo = [str(x).strip() for x in raw if str(x).strip()]
    else:
        combo = _parse_symbol_text(str(raw or ""))
    return list(dict.fromkeys(combo))


def _screener_rows_from_snapshot(data) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("results", "rows", "candidates", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    nested = data.get("data")
    if isinstance(nested, (dict, list)):
        return _screener_rows_from_snapshot(nested)
    return []


def _symbol_from_screener_row(row: dict) -> str:
    for key in ("symbol", "code", "ts_code", "asset_code"):
        value = row.get(key)
        if value:
            return str(value).strip()
    return ""


def _symbols_from_latest_screener(limit: int = 12) -> tuple[list[str], str, bool]:
    latest = cache_state_service.latest("screener_snapshot")
    rows = _screener_rows_from_snapshot(latest.data)
    symbols: list[str] = []
    for row in rows:
        sym = _symbol_from_screener_row(row)
        if sym and sym not in symbols:
            symbols.append(sym)
        if len(symbols) >= limit:
            break
    snapshot_id = str((latest.cache_status or {}).get("snapshot_id") or (latest.data or {}).get("snapshot_id") or "")
    return symbols, snapshot_id, bool(latest.data)


def _auto_screener_rows_for_config(payload: dict, *, prefer_latest_screener: bool = False) -> list[dict]:
    rows = _screener_rows_from_snapshot(payload)
    if rows:
        return rows
    if prefer_latest_screener or payload.get("use_latest_screener"):
        latest = cache_state_service.latest("screener_snapshot")
        return _screener_rows_from_snapshot(latest.data)
    existing = cache_state_service.get("auto_trading_config", "default").data or {}
    saved_map = existing.get("screener_signal_map") if isinstance(existing, dict) else {}
    if isinstance(saved_map, dict):
        saved_rows = [item.get("source_row") for item in saved_map.values() if isinstance(item, dict) and isinstance(item.get("source_row"), dict)]
        if saved_rows:
            return saved_rows
    return []


def _auto_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value in (None, ""):
        return []
    return _parse_symbol_text(str(value))


def _row_text_items(row: dict, *keys: str) -> list[str]:
    out: list[str] = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out.extend(str(x).strip() for x in value if str(x).strip())
        elif value not in (None, ""):
            out.append(str(value).strip())
    return out


def _auto_score(row: dict, *keys: str, default: float = 50.0) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", "--"):
            return _as_float(value, default)
    return float(default)


def _auto_action_from_screener(row: dict, final_score: float, risk_flags: list[str]) -> str:
    grade = str(row.get("grade") or row.get("level") or "").upper()
    risk_text = " ".join(risk_flags + _row_text_items(row, "risk_summary", "missing_data_hints", "missing_data"))
    hard_risk_words = ("退市", "ST", "重大负面", "监管", "诉讼", "处罚", "数据不足", "缺失", "stale")
    if any(word in risk_text for word in hard_risk_words) or grade.startswith("D") or final_score < 45:
        return "avoid"
    if final_score >= 70:
        return "buy"
    if final_score >= 58:
        return "watch"
    return "reduce"


def _auto_screener_signal_map(rows: list[dict], symbols: list[str], risk_controls: dict) -> dict:
    by_symbol: dict[str, dict] = {}
    row_map = {_symbol_from_screener_row(row): row for row in rows if _symbol_from_screener_row(row)}
    max_single = _as_float(risk_controls.get("max_single_position_pct"), 20.0)
    for symbol in symbols:
        row = dict(row_map.get(symbol) or {"symbol": symbol})
        final_score = _auto_score(row, "final_trade_score", "total_score", "manual_review_score", "script_score", default=50.0)
        risk_flags = _row_text_items(row, "risk_flags", "risk_tags", "risk_warnings", "missing_data_hints", "missing_data")
        tags = _row_text_items(row, "tags", "hit_tags", "core_tags", "upgrade_reasons", "strategy_tags")
        action = _auto_action_from_screener(row, final_score, risk_flags)
        target_weight_hint = 0.0 if action == "avoid" else max(0.0, min(max_single, (final_score - 45.0) * 0.55))
        by_symbol[symbol] = {
            "symbol": symbol,
            "name": str(row.get("name") or row.get("asset_name") or symbol),
            "action": action,
            "final_score": round(final_score, 4),
            "technical_score": _auto_score(row, "technical_score", "technical_factor_score", "total_score", default=final_score),
            "fundamental_score": _auto_score(row, "fundamental_score", "manual_review_score", "total_score", default=55.0),
            "information_score": _auto_score(row, "information_score", "info_score", "info_sentiment_score", default=50.0),
            "fund_flow_score": _auto_score(row, "fund_flow_score", "strength_score", "amount_score", default=50.0),
            "market_score": _auto_score(row, "market_score", "market_mood_score", "market_sentiment_score", default=50.0),
            "target_weight_hint_pct": round(target_weight_hint, 4),
            "risk_flags": risk_flags[:12],
            "strategy_tags": tags[:16],
            "missing_data": _row_text_items(row, "missing_data_hints", "missing_data")[:12],
            "evidence": (tags or ["来自筛选快照的综合评分"])[:10],
            "source_row": row,
            "source": "latest_screener" if row_map.get(symbol) else "config_symbol_only",
        }
    return by_symbol


def _auto_strategy_parameters(combo: list[str], merged: dict, risk_controls: dict) -> dict:
    raw = merged.get("strategy_parameters") or merged.get("strategy_rules") or {}
    raw_map: dict[str, dict] = {}
    if isinstance(raw, dict):
        raw_map = {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                key = str(item.get("strategy") or item.get("key") or "").strip()
                if key:
                    raw_map[key] = dict(item)
    position_sizing = str(merged.get("position_sizing") or "score_weighted")
    meta_map = _auto_strategy_meta_map()
    out: dict[str, dict] = {}
    for key in combo:
        override = raw_map.get(key) or {}
        meta = meta_map.get(key) or {}
        out[key] = {
            "strategy": key,
            "name": str(meta.get("name") or key),
            "category": str(meta.get("category") or "custom"),
            "description": str(meta.get("description") or "Custom strategy module."),
            "tags": list(meta.get("tags") or []),
            "default_weight": _as_float(override.get("default_weight"), _as_float(meta.get("default_weight"), 1.0)),
            "enabled": _as_bool(override.get("enabled"), True),
            "position_sizing": str(override.get("position_sizing") or position_sizing),
            "position_control": str(override.get("position_control") or override.get("position_sizing") or position_sizing),
            "stop_loss_pct": _as_float(override.get("stop_loss_pct"), _as_float(risk_controls.get("stop_loss_pct"), 8.0)),
            "take_profit_pct": _as_float(override.get("take_profit_pct"), _as_float(risk_controls.get("take_profit_pct"), 18.0)),
            "max_drawdown_pct": _as_float(override.get("max_drawdown_pct"), _as_float(risk_controls.get("max_drawdown_pct"), 18.0)),
            "max_strategy_drawdown_pct": _as_float(
                override.get("max_strategy_drawdown_pct"),
                _as_float(override.get("max_drawdown_pct"), _as_float(risk_controls.get("max_drawdown_pct"), 18.0)),
            ),
            "max_single_position_pct": _as_float(override.get("max_single_position_pct"), _as_float(risk_controls.get("max_single_position_pct"), 20.0)),
            "buy_threshold": _as_float(override.get("buy_threshold"), 62.0),
            "sell_threshold": _as_float(override.get("sell_threshold"), 45.0),
            "reduce_threshold": _as_float(override.get("reduce_threshold"), 50.0),
            "stop_loss_mode": str(override.get("stop_loss_mode") or ("atr_or_fixed" if "atr" in key else "fixed_pct")),
            "take_profit_mode": str(override.get("take_profit_mode") or ("trailing_or_staged" if key in {"ma_repair", "macd_cross", "score_driven"} else "fixed_pct")),
            "beginner_note": str(meta.get("beginner_note") or "Trades still require fresh data, score provenance and risk approval."),
        }
    return out


def _auto_parameter_schema() -> list[dict]:
    return [
        {"field": "enabled", "label": "启用", "type": "bool", "help": "关闭后该策略不参与组合判断。"},
        {"field": "default_weight", "label": "策略权重", "type": "number", "min": 0, "max": 5, "step": 0.1, "help": "用于多策略投票和排序，不直接等于仓位。"},
        {"field": "position_sizing", "label": "仓位控制", "type": "select", "options": ["score_weighted", "atr_risk", "volatility_target", "fixed_weight", "core_satellite", "cash_first_defensive"], "help": "决定买入时用评分、ATR、波动率或固定比例确定目标仓位。"},
        {"field": "max_single_position_pct", "label": "单票上限%", "type": "number", "min": 0, "max": 100, "step": 0.5, "help": "该策略允许的单只股票最大仓位。"},
        {"field": "stop_loss_pct", "label": "止损%", "type": "number", "min": 0, "max": 50, "step": 0.5, "help": "0 表示关闭固定止损；实盘仍会经过风控网关。"},
        {"field": "take_profit_pct", "label": "止盈%", "type": "number", "min": 0, "max": 200, "step": 0.5, "help": "0 表示不固定止盈，可用移动止盈/分批止盈。"},
        {"field": "max_strategy_drawdown_pct", "label": "策略最大回撤%", "type": "number", "min": 0, "max": 80, "step": 0.5, "help": "该策略触发降仓/暂停的最大回撤阈值。"},
        {"field": "buy_threshold", "label": "买入评分", "type": "number", "min": 0, "max": 100, "step": 0.5, "help": "筛选画像和实时评分达到该值才允许新增仓位。"},
        {"field": "sell_threshold", "label": "卖出评分", "type": "number", "min": 0, "max": 100, "step": 0.5, "help": "低于该值时倾向减仓或卖出。"},
    ]


def _auto_strategy_matrix(strategy_parameters: dict) -> list[dict]:
    rows: list[dict] = []
    for key, item in (strategy_parameters or {}).items():
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "key": key,
                "strategy": key,
                "name": item.get("name") or key,
                "category": item.get("category") or "custom",
                "enabled": _as_bool(item.get("enabled"), True),
                "weight": _as_float(item.get("default_weight"), 1.0),
                "position_sizing": item.get("position_sizing") or item.get("position_control") or "score_weighted",
                "max_single_position_pct": _as_float(item.get("max_single_position_pct"), 20.0),
                "stop_loss_pct": _as_float(item.get("stop_loss_pct"), 8.0),
                "take_profit_pct": _as_float(item.get("take_profit_pct"), 18.0),
                "max_strategy_drawdown_pct": _as_float(item.get("max_strategy_drawdown_pct"), _as_float(item.get("max_drawdown_pct"), 18.0)),
                "buy_threshold": _as_float(item.get("buy_threshold"), 62.0),
                "sell_threshold": _as_float(item.get("sell_threshold"), 45.0),
                "stop_loss_mode": item.get("stop_loss_mode") or "fixed_pct",
                "take_profit_mode": item.get("take_profit_mode") or "fixed_pct",
                "beginner_note": item.get("beginner_note") or "",
            }
        )
    return rows


def _auto_decision_policy(risk_controls: dict, score_weights: dict) -> dict:
    return {
        "action_source": "screener_signal_map_first_then_realtime_score",
        "buy_rule": "筛选画像为 buy/watch 且综合交易分达到买入阈值，数据新鲜且风控通过，才允许新增仓位。",
        "sell_rule": "筛选画像为 reduce/avoid/sell、分数跌破卖出阈值、止损/最大回撤/重大负面触发时减仓或卖出。",
        "hold_rule": "评分处于观察区间、缺少关键数据或事件窗口未确认时只观察，不自动新增仓位。",
        "global_buy_threshold": 62.0,
        "global_sell_threshold": 45.0,
        "risk_controls": risk_controls,
        "score_weights": score_weights,
    }


def _auto_integrated_dimensions(score_weights: dict) -> list[dict]:
    return [
        {"key": "technical", "label": "技术面", "weight": score_weights.get("technical"), "examples": ["均线", "MACD", "KDJ", "支撑压力", "量价结构"]},
        {"key": "fundamental", "label": "基本面", "weight": score_weights.get("fundamental"), "examples": ["PE/PB", "ROE", "利润", "现金流", "行业/是否ST"]},
        {"key": "information", "label": "信息面", "weight": score_weights.get("information"), "examples": ["公告", "财报", "半年报", "新闻", "重大负面"]},
        {"key": "fund_flow", "label": "资金面", "weight": score_weights.get("fund_flow"), "examples": ["成交额", "换手率", "量比", "盘口", "公开资金流"]},
        {"key": "market_regime", "label": "大盘情绪", "weight": score_weights.get("market_regime"), "examples": ["上证指数", "创业板", "宽基ETF", "市场波动"]},
    ]


def _auto_key_event_watchlist(event_watch: dict) -> list[dict]:
    return [
        {"key": "financial_reports", "label": "财报披露", "enabled": bool(event_watch.get("financial_reports")), "action": "披露窗口前后进入观察或人工确认。"},
        {"key": "half_year_reports", "label": "半年报/年报窗口", "enabled": bool(event_watch.get("half_year_reports")), "action": "半年度/年度报告前后避免无确认追高。"},
        {"key": "earnings_preannouncements", "label": "业绩预告", "enabled": bool(event_watch.get("earnings_preannouncements")), "action": "预增/预减/亏损预告进入信息面评分。"},
        {"key": "exchange_announcements", "label": "交易所/巨潮公告", "enabled": bool(event_watch.get("exchange_announcements")), "action": "监管问询、诉讼、处罚等重大事项可 veto 买入。"},
        {"key": "major_negative_news", "label": "重大负面", "enabled": bool(event_watch.get("major_negative_news")), "action": "重大负面默认阻断新增仓位。"},
        {"key": "policy_industry_news", "label": "政策/行业事件", "enabled": bool(event_watch.get("policy_industry_news")), "action": "行业政策和宏观事件进入大盘/信息面调分。"},
    ]


def _apply_auto_config_to_backtest_payload(payload: dict) -> dict:
    payload = dict(payload or {})
    if not (payload.get("use_auto_config") or payload.get("auto_trading_config")):
        return payload
    config = payload.get("auto_trading_config") if isinstance(payload.get("auto_trading_config"), dict) else auto_trading_config_get()["data"]
    risk = dict(config.get("risk_controls") or {})
    out = {**config, **payload}
    out.setdefault("symbols", config.get("symbols") or [])
    out.setdefault("strategy", "combo_signal")
    out.setdefault("strategy_combo", ",".join(config.get("strategy_combo") or []))
    out.setdefault("position_sizing", config.get("position_sizing") or "score_weighted")
    out.setdefault("sizing", out.get("position_sizing") or "score_weighted")
    out.setdefault("initial_cash", config.get("initial_cash") or 100000)
    combo = _strategy_combo_from(config.get("strategy_combo") or out.get("strategy_combo") or [])
    strategy_parameters = config.get("strategy_parameters") if isinstance(config.get("strategy_parameters"), dict) else {}
    enabled_controls = [
        dict(strategy_parameters.get(key) or {})
        for key in combo
        if isinstance(strategy_parameters.get(key), dict) and _as_bool(strategy_parameters.get(key, {}).get("enabled"), True)
    ]
    stop_candidates = [_as_float(x.get("stop_loss_pct"), _as_float(risk.get("stop_loss_pct"), 8.0)) for x in enabled_controls]
    take_candidates = [_as_float(x.get("take_profit_pct"), _as_float(risk.get("take_profit_pct"), 18.0)) for x in enabled_controls]
    single_candidates = [_as_float(x.get("max_single_position_pct"), _as_float(risk.get("max_single_position_pct"), 20.0)) for x in enabled_controls]
    stop_loss_pct = min(stop_candidates) if stop_candidates else _as_float(risk.get("stop_loss_pct"), 8.0)
    take_profit_pct = min([x for x in take_candidates if x > 0] or [_as_float(risk.get("take_profit_pct"), 18.0)])
    max_single_pct = min(single_candidates) if single_candidates else _as_float(risk.get("max_single_position_pct"), 20.0)
    max_total_pct = _as_float(risk.get("max_total_position_pct"), 80.0)
    min_cash_pct = _as_float(risk.get("min_cash_pct"), 15.0)
    max_single_fraction = _percent_to_fraction(max_single_pct, default=0.20)
    max_total_fraction = _percent_to_fraction(max_total_pct, default=0.80)
    out.setdefault("stop_loss_pct", stop_loss_pct)
    out.setdefault("take_profit_pct", take_profit_pct)
    out.setdefault("max_drawdown_pct", min([_as_float(x.get("max_drawdown_pct"), _as_float(risk.get("max_drawdown_pct"), 18.0)) for x in enabled_controls] or [_as_float(risk.get("max_drawdown_pct"), 18.0)]))
    out["max_single_position_pct"] = max_single_fraction
    out["position_pct"] = _percent_to_fraction(out.get("position_pct", max_total_fraction), default=max_total_fraction)
    out["cash_reserve_pct"] = _percent_to_fraction(out.get("cash_reserve_pct", min_cash_pct), default=_percent_to_fraction(min_cash_pct, default=0.15))
    out["auto_trading_config_applied"] = True
    out["auto_trading_config_snapshot"] = config
    out["auto_strategy_parameters"] = strategy_parameters
    signal_map = config.get("screener_signal_map") or {}
    if "screener_rows" not in out and isinstance(signal_map, dict):
        rows = [item.get("source_row") for item in signal_map.values() if isinstance(item, dict) and isinstance(item.get("source_row"), dict)]
        if rows:
            out["screener_rows"] = rows
    return out


def _percent_to_fraction(value: object, *, default: float = 0.0) -> float:
    raw = _as_float(value, default * 100.0 if 0.0 <= default <= 1.0 else default)
    if raw > 1.0:
        raw = raw / 100.0
    return round(max(0.0, min(raw, 1.0)), 6)


def _auto_selected_strategy(profile: dict, combo: list[str], strategy_parameters: dict) -> str:
    tags = {str(x) for x in (profile.get("strategy_tags") or profile.get("tags") or [])}
    for key in combo:
        if key in tags and _as_bool((strategy_parameters.get(key) or {}).get("enabled"), True):
            return key
    for key in combo:
        if _as_bool((strategy_parameters.get(key) or {}).get("enabled"), True):
            return key
    return combo[0] if combo else "score_driven"


def _auto_backtest_effective_controls(payload: dict, cfg: V319BacktestConfig) -> dict:
    config = payload.get("auto_trading_config_snapshot") if isinstance(payload.get("auto_trading_config_snapshot"), dict) else {}
    config = config or (payload.get("auto_trading_config") if isinstance(payload.get("auto_trading_config"), dict) else {})
    risk = dict(config.get("risk_controls") or payload.get("risk_controls") or {})
    combo = _strategy_combo_from(config.get("strategy_combo") or payload.get("strategy_combo") or [])
    strategy_parameters = config.get("strategy_parameters") or payload.get("auto_strategy_parameters") or payload.get("strategy_parameters") or {}
    if not isinstance(strategy_parameters, dict):
        strategy_parameters = {}
    signal_map = config.get("screener_signal_map") or payload.get("screener_signal_map") or {}
    if not isinstance(signal_map, dict):
        signal_map = {}
    symbols = list(cfg.symbols or _symbols_from_payload(payload))
    profiles: dict[str, dict] = {}
    symbol_controls: dict[str, dict] = {}
    for symbol in symbols:
        profile = dict(signal_map.get(symbol) or {"symbol": symbol, "action": "watch", "source": "no_screener_profile"})
        selected = _auto_selected_strategy(profile, combo, strategy_parameters)
        controls = dict(strategy_parameters.get(selected) or {})
        stop = _as_float(controls.get("stop_loss_pct"), _as_float(risk.get("stop_loss_pct"), cfg.stop_loss_pct))
        take = _as_float(controls.get("take_profit_pct"), _as_float(risk.get("take_profit_pct"), cfg.take_profit_pct))
        max_single_pct = _as_float(controls.get("max_single_position_pct"), _as_float(risk.get("max_single_position_pct"), cfg.max_single_position_pct * 100.0))
        target_hint_pct = _as_float(profile.get("target_weight_hint_pct"), max_single_pct)
        effective_pct = min(max_single_pct, target_hint_pct if target_hint_pct > 0 else max_single_pct)
        profiles[symbol] = {
            "symbol": symbol,
            "name": profile.get("name") or symbol,
            "action": profile.get("action") or "watch",
            "final_score": _as_float(profile.get("final_score"), 50.0),
            "technical_score": _as_float(profile.get("technical_score"), 50.0),
            "fundamental_score": _as_float(profile.get("fundamental_score"), 50.0),
            "information_score": _as_float(profile.get("information_score"), 50.0),
            "fund_flow_score": _as_float(profile.get("fund_flow_score"), 50.0),
            "market_score": _as_float(profile.get("market_score"), 50.0),
            "risk_flags": list(profile.get("risk_flags") or [])[:12],
            "missing_data": list(profile.get("missing_data") or [])[:12],
            "evidence": list(profile.get("evidence") or [])[:10],
            "source": profile.get("source") or "auto_config",
        }
        symbol_controls[symbol] = {
            "selected_strategy": selected,
            "position_sizing": str(controls.get("position_sizing") or config.get("position_sizing") or payload.get("position_sizing") or cfg.sizing),
            "effective_stop_loss_pct": round(stop, 4),
            "effective_take_profit_pct": round(take, 4),
            "effective_max_drawdown_pct": round(_as_float(controls.get("max_drawdown_pct"), _as_float(risk.get("max_drawdown_pct"), payload.get("max_drawdown_pct", 18.0))), 4),
            "effective_max_single_position_pct": round(effective_pct, 4),
            "effective_position_weight": _percent_to_fraction(effective_pct, default=cfg.max_single_position_pct),
            "target_weight_hint_pct": round(target_hint_pct, 4),
        }
    return {
        "auto_trading_config_applied": bool(payload.get("auto_trading_config_applied")),
        "config_id": config.get("config_id") or "inline",
        "strategy_family": config.get("strategy_family") or payload.get("strategy_family") or "hybrid",
        "strategy_combo": combo,
        "position_sizing": config.get("position_sizing") or payload.get("position_sizing") or cfg.sizing,
        "risk_controls": risk,
        "strategy_parameters": strategy_parameters,
        "screener_signal_profiles": profiles,
        "symbols": symbol_controls,
        "global": {
            "position_pct": cfg.position_pct,
            "max_single_position_pct": cfg.max_single_position_pct,
            "cash_reserve_pct": cfg.cash_reserve_pct,
            "stop_loss_pct": cfg.stop_loss_pct,
            "take_profit_pct": cfg.take_profit_pct,
            "sizing": cfg.sizing,
        },
        "trace_note": "V3.23 回测已读取自动交易配置；真实交易仍默认关闭，回测只做历史撮合验证。",
    }


def _attach_auto_config_to_backtest_data(data: dict, payload: dict, cfg: V319BacktestConfig) -> dict:
    data = dict(data or {})
    if not payload.get("auto_trading_config_applied"):
        return data
    effective = _auto_backtest_effective_controls(payload, cfg)
    data["auto_trading_config_applied"] = True
    data["effective_auto_controls"] = effective
    data["screener_signal_profiles"] = effective.get("screener_signal_profiles", {})
    data["strategy_parameters"] = effective.get("strategy_parameters", {})
    data.setdefault("config", {})
    data["config"].update(
        {
            "strategy_combo": effective.get("strategy_combo"),
            "position_sizing": effective.get("position_sizing"),
            "sizing": cfg.sizing,
            "position_pct": cfg.position_pct,
            "cash_reserve_pct": cfg.cash_reserve_pct,
            "max_single_position_pct": cfg.max_single_position_pct,
            "stop_loss_pct": cfg.stop_loss_pct,
            "take_profit_pct": cfg.take_profit_pct,
        }
    )
    data.setdefault("params_cn", {})
    data["params_cn"].update(
        {
            "自动交易配置": "已接入 V3.23 回测内核",
            "策略组合": "、".join(effective.get("strategy_combo") or []) or "未选择",
            "仓位模型": str(effective.get("position_sizing") or ""),
            "全局仓位/单票上限": f"{cfg.position_pct * 100:.2f}% / {cfg.max_single_position_pct * 100:.2f}%",
            "止损/止盈": f"{cfg.stop_loss_pct}% / {cfg.take_profit_pct}%",
        }
    )
    warnings = list(data.get("warnings") or [])
    if not effective.get("screener_signal_profiles"):
        warnings.append("自动交易配置未携带筛选信号画像，回测仅按历史K线技术信号验证。")
    data["warnings"] = list(dict.fromkeys(str(x) for x in warnings if str(x)))
    return data


def _build_auto_trading_config(payload: dict | None = None, *, prefer_latest_screener: bool = False) -> dict:
    payload = dict(payload or {})
    existing = cache_state_service.get("auto_trading_config", "default").data or {}
    merged = {**existing, **payload}
    screener_rows = _auto_screener_rows_for_config(payload, prefer_latest_screener=prefer_latest_screener)
    screener_symbols, screener_snapshot_id, has_screener = _symbols_from_latest_screener()
    row_symbols = []
    for row in screener_rows:
        sym = _symbol_from_screener_row(row)
        if sym and sym not in row_symbols:
            row_symbols.append(sym)
    watch_symbols = list(watchlist_service.list().get("symbols") or [])
    payload_symbols = _symbols_from_payload(payload)
    existing_symbols = _symbols_from_payload(existing)
    if payload_symbols:
        symbols = payload_symbols
        symbols_source = "payload"
    elif prefer_latest_screener and row_symbols:
        symbols = row_symbols
        symbols_source = "latest_screener"
    elif prefer_latest_screener and screener_symbols:
        symbols = screener_symbols
        symbols_source = "latest_screener"
    elif existing_symbols:
        symbols = existing_symbols
        symbols_source = "saved_config"
    elif screener_symbols:
        symbols = screener_symbols
        symbols_source = "latest_screener"
    elif watch_symbols:
        symbols = watch_symbols
        symbols_source = "watchlist"
    else:
        symbols = ["300750", "600438", "510300"]
        symbols_source = "default_seed"

    risk_in = dict(merged.get("risk_controls") or {})
    score_in = dict(merged.get("score_weights") or {})
    event_in = dict(merged.get("event_watch") or {})
    data_in = dict(merged.get("data_requirements") or {})
    combo = _strategy_combo_from(
        merged.get("strategy_combo")
        or merged.get("selected_strategies")
        or merged.get("strategies")
        or DEFAULT_AUTO_STRATEGY_COMBO
    ) or list(DEFAULT_AUTO_STRATEGY_COMBO)
    risk_controls = {
        "stop_loss_pct": _as_float(risk_in.get("stop_loss_pct"), 8.0),
        "take_profit_pct": _as_float(risk_in.get("take_profit_pct"), 18.0),
        "max_drawdown_pct": _as_float(risk_in.get("max_drawdown_pct"), 18.0),
        "max_single_position_pct": _as_float(risk_in.get("max_single_position_pct"), 20.0),
        "max_total_position_pct": _as_float(risk_in.get("max_total_position_pct"), 80.0),
        "max_daily_loss_pct": _as_float(risk_in.get("max_daily_loss_pct"), 4.0),
        "min_cash_pct": _as_float(risk_in.get("min_cash_pct"), 15.0),
        "atr_risk_pct": _as_float(risk_in.get("atr_risk_pct"), 1.5),
        "cooldown_days": int(_as_float(risk_in.get("cooldown_days"), 2.0)),
    }
    score_weights = {
        "technical": _as_float(score_in.get("technical"), 0.30),
        "fundamental": _as_float(score_in.get("fundamental"), 0.22),
        "information": _as_float(score_in.get("information"), 0.20),
        "fund_flow": _as_float(score_in.get("fund_flow"), 0.16),
        "market_regime": _as_float(score_in.get("market_regime"), 0.12),
    }
    event_watch = {
        "financial_reports": _as_bool(event_in.get("financial_reports"), True),
        "half_year_reports": _as_bool(event_in.get("half_year_reports"), True),
        "earnings_preannouncements": _as_bool(event_in.get("earnings_preannouncements"), True),
        "exchange_announcements": _as_bool(event_in.get("exchange_announcements"), True),
        "major_negative_news": _as_bool(event_in.get("major_negative_news"), True),
        "policy_industry_news": _as_bool(event_in.get("policy_industry_news"), True),
        "event_lookahead_days": int(_as_float(event_in.get("event_lookahead_days"), 21.0)),
        "blackout_before_days": int(_as_float(event_in.get("blackout_before_days"), 2.0)),
        "blackout_after_days": int(_as_float(event_in.get("blackout_after_days"), 1.0)),
    }
    data_requirements = {
        "require_fresh_quote": _as_bool(data_in.get("require_fresh_quote"), True),
        "block_stale_buy": _as_bool(data_in.get("block_stale_buy"), True),
        "require_score_provenance": _as_bool(data_in.get("require_score_provenance"), True),
        "require_info_snapshot": _as_bool(data_in.get("require_info_snapshot"), False),
        "require_orderbook_when_available": _as_bool(data_in.get("require_orderbook_when_available"), True),
    }
    strategy_parameters = _auto_strategy_parameters(combo, merged, risk_controls)

    config = {
        "config_id": str(merged.get("config_id") or "default"),
        "version": "V3.23",
        "mode": "auto_trading_core",
        "symbols": list(dict.fromkeys(str(x).strip() for x in symbols if str(x).strip()))[:80],
        "symbols_source": symbols_source,
        "screener_snapshot_id": str(merged.get("screener_snapshot_id") or screener_snapshot_id),
        "screener_snapshot_available": has_screener,
        "strategy_family": str(merged.get("strategy_family") or merged.get("strategy") or "hybrid"),
        "strategy_combo": combo,
        "strategy_catalog": _auto_strategy_catalog(),
        "beginner_presets": _auto_beginner_presets(),
        "workflow_steps": [
            {"step": 1, "key": "screen", "label": "筛选建池", "description": "复用最新筛选结果、自选池或手动股票池，形成四面评分和风险标签。"},
            {"step": 2, "key": "configure", "label": "一键配置", "description": "选择策略组合、仓位模型、止盈止损、最大回撤和事件监控。"},
            {"step": 3, "key": "backtest", "label": "历史回测", "description": "验证订单、成交、回撤、评分溯源和跑输/跑赢原因。"},
            {"step": 4, "key": "paper", "label": "实时模拟", "description": "开盘期间用真实行情跑 paper trading，订单、持仓和审计落库。"},
            {"step": 5, "key": "live_confirm", "label": "实盘确认", "description": "只有券商状态、风控网关和人工确认全部通过后才可能真实下单。"},
        ],
        "position_sizing": str(merged.get("position_sizing") or "score_weighted"),
        "risk_controls": risk_controls,
        "strategy_parameters": strategy_parameters,
        "parameter_schema": _auto_parameter_schema(),
        "strategy_matrix": _auto_strategy_matrix(strategy_parameters),
        "strategy_blueprints": _auto_strategy_matrix(strategy_parameters),
        "score_weights": score_weights,
        "decision_policy": _auto_decision_policy(risk_controls, score_weights),
        "integrated_score_dimensions": _auto_integrated_dimensions(score_weights),
        "event_watch": event_watch,
        "key_event_watchlist": _auto_key_event_watchlist(event_watch),
        "data_requirements": data_requirements,
        "interval_seconds": max(0, min(60, int(_as_float(merged.get("interval_seconds"), 15.0)))),
        "initial_cash": _as_float(merged.get("initial_cash"), 100000.0),
        "reset_account": _as_bool(merged.get("reset_account"), True),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "source_page": str(merged.get("source_page") or "auto-trading"),
        "disclaimer": "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。",
    }
    config["screener_signal_map"] = _auto_screener_signal_map(screener_rows, config["symbols"], config["risk_controls"])
    config["screener_signal_count"] = len([x for x in config["screener_signal_map"].values() if x.get("source") == "latest_screener"])
    config["readiness_gates"] = [
        "股票池不为空",
        "策略组合不为空",
        "仓位/止盈止损/最大回撤已配置",
        "财报/半年报/公告/重大负面事件已纳入观察",
        "真实交易默认关闭，未授权前只允许 paper trading",
    ]
    return config


def _save_auto_trading_config(config: dict, *, event_type: str = "auto_trading_config_saved") -> dict:
    saved = cache_state_service.put(
        "auto_trading_config",
        str(config.get("config_id") or "default"),
        config,
        ttl_seconds=AUTO_TRADING_CONFIG_TTL_SECONDS,
        source="api/auto-trading/config",
    )
    trading_store_v323.put(
        "audit_events",
        {
            "event_type": event_type,
            "config_id": config.get("config_id"),
            "symbols": config.get("symbols"),
            "strategy_family": config.get("strategy_family"),
            "strategy_combo": config.get("strategy_combo"),
            "strategy_parameters": config.get("strategy_parameters"),
            "strategy_matrix": config.get("strategy_matrix"),
            "decision_policy": config.get("decision_policy"),
            "position_sizing": config.get("position_sizing"),
            "risk_controls": config.get("risk_controls"),
            "event_watch": config.get("event_watch"),
            "key_event_watchlist": config.get("key_event_watchlist"),
            "screener_signal_count": config.get("screener_signal_count"),
            "created_at": config.get("updated_at"),
            "source_page": "auto-trading",
        },
        mode="config",
        session_id="auto_trading",
        record_id=f"auto-config-{config.get('config_id')}-{config.get('updated_at')}",
    )
    return {"ok": True, "data": config, "cache_status": saved}


def _auto_trading_readiness(config: dict) -> dict:
    broker = live_trading_engine_v323.status()
    safety = broker.get("safety") or {}
    gates = [
        {"key": "symbols", "label": "股票池", "ok": bool(config.get("symbols")), "detail": f"{len(config.get('symbols') or [])} 只"},
        {"key": "strategy_combo", "label": "策略组合", "ok": bool(config.get("strategy_combo")), "detail": ", ".join(config.get("strategy_combo") or [])},
        {"key": "position_sizing", "label": "仓位模型", "ok": bool(config.get("position_sizing")), "detail": str(config.get("position_sizing") or "--")},
        {"key": "risk_controls", "label": "止盈止损/最大回撤", "ok": bool(config.get("risk_controls")), "detail": str(config.get("risk_controls") or {})},
        {"key": "screener_signal_map", "label": "筛选信号画像", "ok": bool(config.get("screener_signal_map")), "detail": f"{config.get('screener_signal_count') or 0}/{len(config.get('symbols') or [])} 只来自筛选快照"},
        {"key": "event_watch", "label": "财报/公告/重大事件", "ok": bool(config.get("event_watch", {}).get("financial_reports") or config.get("event_watch", {}).get("major_negative_news")), "detail": str(config.get("event_watch") or {})},
        {"key": "paper_ready", "label": "实时模拟", "ok": True, "detail": "可用，订单/成交/持仓/审计落 SQLite"},
        {"key": "live_disabled_by_default", "label": "真实交易安全状态", "ok": not bool(safety.get("LIVE_TRADING_ENABLED")), "detail": "默认关闭" if not bool(safety.get("LIVE_TRADING_ENABLED")) else "已开启，需重点复核"},
        {"key": "broker_connected", "label": "QMT/PTrade 券商连接", "ok": bool((broker.get("broker") or {}).get("connected")), "detail": str((broker.get("broker") or {}).get("status") or "disabled/unsupported")},
    ]
    return {
        "ok": True,
        "config": config,
        "gates": gates,
        "ready_for_paper": all(g["ok"] for g in gates[:6]),
        "ready_for_live": all(g["ok"] for g in gates[:6]) and bool((broker.get("broker") or {}).get("connected")) and bool(safety.get("LIVE_TRADING_ENABLED")),
        "broker": broker,
    }


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


@app.get("/api/market/regime")
def market_regime(max_pages: int = 2, page_size: int = 100) -> dict:
    quotes = []
    for page in range(1, max(1, min(int(max_pages or 2), 10)) + 1):
        try:
            quotes.extend(service.get_market_snapshot(page=page, page_size=max(20, min(int(page_size or 100), 500))) or [])
        except Exception:
            break
    regime = market_regime_service.analyze_market(quotes, index_bars=_market_index_bars())
    return {"ok": True, "data": regime, "market_regime": regime, "count": len(quotes)}


@app.get("/api/market-rules/profiles")
def market_rule_profiles(symbol: str = "", asof: str = "") -> dict:
    profiles = {key: value.to_dict() for key, value in market_rule_engine_v322.profiles.items()}
    resolved = None
    if symbol:
        resolved = market_rule_engine_v322.resolve_profile(symbol, asof=asof or None).to_dict()
    return {
        "ok": True,
        "version": market_rule_engine_v322.version,
        "timezone": market_rule_engine_v322.timezone,
        "count": len(profiles),
        "profiles": profiles,
        "resolved": resolved,
        "note": "交易规则来自 config/market_rules/a_share_rules.yaml，执行撮合不再在 execution.py 里硬编码前缀。",
    }


@app.get("/api/backtest/v322/readiness")
def backtest_v322_readiness() -> dict:
    return {
        "ok": True,
        "version": "V3.22",
        "capabilities": {
            "score_provenance": True,
            "pit_historical_snapshot": True,
            "market_rule_engine": True,
            "position_sizing": True,
            "money_management": True,
            "exit_policy": True,
            "realtime_paper": True,
            "human_confirm": True,
            "paper_only_no_broker": True,
        },
        "endpoints": [
            "/api/backtest/run",
            "/api/backtest/v322/readiness",
            "/api/market-rules/profiles",
            "/api/screener/historical-snapshot",
            "/api/realtime-paper/status",
            "/api/realtime-paper/confirmations",
        ],
        "note": "V3.22 回测信号使用历史可见数据和评分溯源；真实交易仍需要人工复核，本系统只做纸面模拟。",
    }


@app.get("/api/backtest/v323/readiness")
def backtest_v323_readiness() -> dict:
    return {
        "ok": True,
        "version": "V3.23 / Full Auto Trading Core",
        "baseline": "feature/v3.23-full-auto-trading-core from codex/backtest-combo-strategy-ui@b19545d",
        "main_latest": False,
        "modules": {
            "backtest": True,
            "realtime_paper": True,
            "live_trading_disabled_by_default": True,
            "unified_scoring": True,
            "broker_adapters": ["disabled", "simulator", "qmt_import_guard", "ptrade_import_guard"],
            "chart_markers": True,
            "trading_records": True,
            "data_truth_rules": True,
        },
        "safety": live_trading_engine_v323.status()["safety"],
        "disclaimer": "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。",
    }


@app.get("/api/rules/effective")
def rules_effective(symbol: str = "300750", asof: str = "") -> dict:
    rule = market_rule_engine_v322.resolve_profile(symbol, asof=asof or None).to_dict()
    return {"ok": True, "symbol": symbol, "asof": asof, "data": rule, "source": "config/market_rules/a_share_rules.yaml"}


@app.post("/api/risk/pretrade/check")
def risk_pretrade_check(payload: dict = Body(default_factory=dict)) -> dict:
    order = dict(payload.get("order") or payload)
    portfolio = dict(payload.get("portfolio") or {})
    signal = dict(payload.get("signal") or {})
    quote = dict(payload.get("quote") or {})
    result = paper_trading_gateway_v320.risk_gateway.evaluate_order(order, portfolio=portfolio, signal=signal, quote=quote)
    trading_store_v323.put("risk_checks", result, mode=str(order.get("mode") or "paper"), symbol=str(order.get("symbol") or ""))
    return {"ok": True, "data": result}


@app.get("/api/score/latest/{symbol}")
def score_latest_v323(symbol: str) -> dict:
    rows = [x for x in score_provenance_memory_v323.values() if x.get("symbol") == symbol]
    rows.sort(key=lambda x: str(x.get("decision_time") or ""), reverse=True)
    return {"ok": True, "data": rows[0] if rows else None, "missing_reason": "" if rows else "暂无评分溯源，请先运行筛选/回测/模拟。"}


@app.get("/api/score/provenance/{provenance_id}")
def score_provenance_get_v323(provenance_id: str) -> dict:
    data = score_provenance_memory_v323.get(provenance_id)
    if not data:
        stored = trading_store_v323.list("score_provenance", limit=1000)
        data = next((x for x in stored if x.get("provenance_id") == provenance_id), None)
    return {"ok": bool(data), "data": data, "explain": explain_score(data) if data else None, "errors": [] if data else ["provenance_id not found"]}


@app.post("/api/score/recompute")
def score_recompute_v323(payload: dict = Body(default_factory=dict)) -> dict:
    symbol = str(payload.get("symbol") or "300750")
    decision_time = str(payload.get("decision_time") or datetime.now().isoformat(timespec="seconds"))
    quote_payload = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
    fundamentals_payload = payload.get("fundamentals") if isinstance(payload.get("fundamentals"), dict) else {}
    info_payload = payload.get("information") if isinstance(payload.get("information"), dict) else {}
    market_payload = payload.get("market_state") if isinstance(payload.get("market_state"), dict) else {}
    quote_snapshot = build_quote_snapshot(symbol, quote_payload, source_id=str(quote_payload.get("source_id") or quote_payload.get("source") or "manual"))
    fund_snapshot = build_fundamentals_snapshot(symbol, fundamentals_payload, source_id=str(fundamentals_payload.get("source_id") or fundamentals_payload.get("source") or "manual"))
    news_snapshot = build_news_snapshot(symbol, info_payload.get("items") if isinstance(info_payload.get("items"), list) else [], source_id=str(info_payload.get("source_id") or "manual"))
    bundle = factor_engine_v323.compute(
        symbol,
        decision_time=decision_time,
        bars=list(payload.get("bars") or []),
        quote=quote_payload,
        fundamentals=fundamentals_payload,
        information=info_payload,
        fund_flow=dict(payload.get("fund_flow") or {}),
        market_state=market_payload,
        behavior_risk=dict(payload.get("behavior_risk") or {}),
        data_sources=[quote_snapshot.source.to_dict(), fund_snapshot.source.to_dict(), news_snapshot.source.to_dict()],
    )
    provenance = build_score_provenance_v323(
        ScoreRequest(
            symbol=symbol,
            decision_time=decision_time,
            mode=str(payload.get("mode") or "realtime_paper"),
            strategy_family=str(payload.get("strategy_family") or "hybrid"),
            factor_values=bundle.values,
            data_sources=bundle.sources,
        )
    )
    signal = SignalFusionV323().fuse(provenance)
    pdata = provenance.to_dict()
    score_provenance_memory_v323[provenance.provenance_id] = pdata
    trading_store_v323.put("score_provenance", pdata, mode=provenance.mode, symbol=symbol, record_id=provenance.provenance_id)
    trading_store_v323.put("signals", signal.to_dict(), mode=provenance.mode, symbol=symbol, record_id=signal.signal_id)
    return {"ok": True, "data": pdata, "signal": signal.to_dict(), "explain": explain_score(pdata)}


@app.get("/api/screener/historical-snapshot")
def screener_historical_snapshot(
    symbols: str = "300750,600438",
    trade_date: str = "",
    decision_time: str = "",
    limit: int = 260,
    adjust: str = "qfq",
) -> dict:
    symbol_list = _parse_symbol_text(symbols) if symbols else []
    symbol_list = symbol_list[: max(1, min(len(symbol_list) or 1, 80))]
    today = datetime.now().strftime("%Y-%m-%d")
    trade_date = str(trade_date or today)[:10]
    decision_time = str(decision_time or f"{trade_date} 15:10:00")
    bars_by_symbol = {}
    for code in symbol_list:
        try:
            bars_by_symbol[code] = service.get_kline(
                code,
                frame="1d",
                limit=max(60, min(int(limit or 260), 1200)),
                adjust=adjust,
                force_refresh=False,
            )
        except Exception:
            bars_by_symbol[code] = []
    snapshot = historical_snapshot_builder_v322.build_historical_snapshot(
        trade_date,
        decision_time,
        symbol_list,
        bars_by_symbol=bars_by_symbol,
        market_inputs={"symbol_count": len(symbol_list)},
    )
    return {"ok": True, "data": snapshot, "snapshot": snapshot}

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


def _v321_effective_legacy_params(
    *,
    position_pct: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    buy_score: float,
    sell_score: float,
    initial_cash: float,
    sizing_mode: str,
    horizon: str,
    dca_amount: float,
    atr_risk_pct: float,
) -> dict:
    valid_horizon = horizon if horizon in {"intraday_paper", "short_term", "swing", "position", "dca", "hybrid"} else "swing"
    rules = StrategyHorizonConfig(horizon=valid_horizon).resolved_rules()
    base_position = max(0.01, min(float(position_pct or 0.0), 1.0))
    stop = float(stop_loss_pct or 0.0)
    take = float(take_profit_pct or 0.0)
    buy = float(buy_score or 0.0)
    sell = float(sell_score or 0.0)
    notes: list[str] = []
    horizon_cap = base_position
    if valid_horizon == "short_term":
        horizon_cap = min(horizon_cap, 0.45)
        stop = min(stop or 4.0, 4.0)
        take = take or 8.0
        sell = max(sell, 52.0)
        notes.append("短线周期：仓位上限45%，止损收紧到4%，卖出评分阈值不低于52")
    elif valid_horizon == "swing":
        stop = 7.0 if not stop or abs(stop - 8.0) < 1e-9 else stop
        take = take or 15.0
        notes.append("波段周期：默认使用7%止损、15%止盈")
    elif valid_horizon == "position":
        horizon_cap = min(horizon_cap, 0.75)
        stop = max(stop, 12.0)
        take = 0.0 if take <= 0 else take
        sell = min(sell, 42.0) if sell else 42.0
        notes.append("长线周期：仓位上限75%，止损放宽到12%，降低评分卖出频率")
    elif valid_horizon == "dca":
        dca_weight = max(0.01, min(float(dca_amount or 0.0) / max(float(initial_cash or 1.0), 1.0), 0.20))
        horizon_cap = min(horizon_cap, dca_weight)
        stop = 0.0
        take = 0.0
        notes.append("定投周期：按定投金额折算单次仓位，默认不启用固定止损止盈")
    elif valid_horizon == "hybrid":
        horizon_cap = min(horizon_cap, 0.60)
        stop = stop or 8.0
        take = take or 12.0
        notes.append("组合周期：核心/卫星上限60%，保留止损止盈")
    mode = str(sizing_mode or "score_weighted")
    mode_cap = base_position
    if mode == "equal_weight":
        mode_cap = min(mode_cap, 0.25)
        notes.append("等权仓位：单票按25%上限参与")
    elif mode == "score_weighted":
        mode_cap = min(mode_cap, 0.70)
        notes.append("评分加权：legacy回测用70%上限近似评分仓位")
    elif mode == "volatility_target":
        mode_cap = min(mode_cap, 0.35)
        notes.append("波动率目标：高波动标的仓位上限35%")
    elif mode in {"atr_risk", "fixed_risk_per_trade"}:
        risk_budget = max(0.001, float(atr_risk_pct or 0.0) / 100.0)
        stop_distance = max(0.01, (stop or rules.get("stop_loss_pct") or 8.0) / 100.0)
        mode_cap = min(mode_cap, max(0.03, min(0.55, risk_budget / stop_distance)))
        notes.append("ATR/固定风险：按风险预算 ÷ 止损距离反推仓位")
    elif mode == "fractional_kelly":
        mode_cap = min(mode_cap, 0.50)
        notes.append("分数凯利：legacy回测先按50%上限保守近似")
    elif mode == "pyramid":
        mode_cap = min(mode_cap, 0.40)
        notes.append("金字塔：首笔仓位按40%上限，后续加仓由报告提示")
    elif mode == "dca":
        dca_weight = max(0.01, min(float(dca_amount or 0.0) / max(float(initial_cash or 1.0), 1.0), 0.20))
        mode_cap = min(mode_cap, dca_weight)
        notes.append("定投仓位：按定投金额折算单次买入比例")
    elif mode == "core_satellite":
        mode_cap = min(mode_cap, 0.65)
        notes.append("核心卫星：单票上限65%")
    effective_position = max(0.01, min(base_position, horizon_cap, mode_cap))
    return {
        "position_pct": round(effective_position, 6),
        "stop_loss_pct": round(float(stop or 0.0), 6),
        "take_profit_pct": round(float(take or 0.0), 6),
        "buy_score": round(float(buy), 6),
        "sell_score": round(float(sell), 6),
        "horizon_rules": rules,
        "notes": list(dict.fromkeys(notes)),
    }


def _attach_v321_effective_controls(data: dict, effective: dict) -> dict:
    data = dict(data or {})
    data["v321_effective_controls"] = effective
    data.setdefault("params", {})
    data["params"].update(
        {
            "effective_position_pct": effective.get("position_pct"),
            "effective_stop_loss_pct": effective.get("stop_loss_pct"),
            "effective_take_profit_pct": effective.get("take_profit_pct"),
            "effective_buy_score": effective.get("buy_score"),
            "effective_sell_score": effective.get("sell_score"),
        }
    )
    data.setdefault("params_cn", {})
    data["params_cn"].update(
        {
            "实际仓位比例": f"{float(effective.get('position_pct') or 0.0) * 100:.2f}%",
            "实际止损/止盈": f"{effective.get('stop_loss_pct')}% / {effective.get('take_profit_pct')}%",
            "实际买入/卖出评分": f"{effective.get('buy_score')} / {effective.get('sell_score')}",
            "资金与周期说明": "；".join(effective.get("notes") or []),
        }
    )
    data.setdefault("metrics", {})
    data["metrics"].update(
        {
            "effective_position_pct": effective.get("position_pct"),
            "effective_stop_loss_pct": effective.get("stop_loss_pct"),
            "effective_take_profit_pct": effective.get("take_profit_pct"),
        }
    )
    if isinstance(data.get("position_summary"), dict):
        note = data["position_summary"].get("note") or ""
        extra = "；".join(effective.get("notes") or [])
        data["position_summary"]["note"] = (note + ("；" if note and extra else "") + extra)[:600]
    return data


@app.get("/api/backtest/run")
def backtest_run(
    symbol: str = "300750",
    strategy: str = "ma_cross",
    strategy_combo: str = "",
    combo_buy_rule: str = "at_least_2",
    combo_sell_rule: str = "any",
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
    legacy: bool = False,
    position_sizing: str = "score_weighted",
    sizing_mode: str | None = None,
    horizon: str = "swing",
    compound_returns: bool = True,
    dca_amount: float = 1000.0,
    dca_frequency: str = "monthly",
    pyramid_step_pct: float = 5.0,
    pyramid_max_adds: int = 3,
    atr_risk_pct: float = 2.0,
    anomaly_filter: bool = True,
    quality_filter: bool = True,
    fundamental_weight: float = 0.28,
    technical_weight: float = 0.34,
    information_weight: float = 0.24,
    market_weight: float = 0.14,
    use_auto_config: bool = False,
) -> dict:
    symbol = str(symbol or "300750").strip()
    limit = max(60, min(int(limit or 520), 1200))
    adjust = str(adjust or "qfq").lower()
    if adjust not in {"none", "qfq", "hfq"}:
        adjust = "qfq"
    # The combo strategy is implemented in the single-symbol research backtester.
    # Route it there even when callers omit legacy=true so API and UI behavior match.
    if strategy == "combo_signal":
        legacy = True
    try:
        q = service.get_quote(symbol, force_refresh=force)
    except Exception:
        q = None
    try:
        bars = service.get_kline(symbol, frame="1d", limit=limit, adjust=adjust, force_refresh=force)
        if not force and len(bars) < min(limit, 120):
            bars = service.get_kline(symbol, frame="1d", limit=limit, adjust=adjust, force_refresh=True)
        sizing_mode = str(sizing_mode or position_sizing or "score_weighted")
        auto_payload: dict = {}
        if use_auto_config:
            auto_payload = _apply_auto_config_to_backtest_payload(
                {"use_auto_config": True, "symbol": symbol, "limit": limit, "adjust": adjust}
            )
            strategy = str(auto_payload.get("strategy") or strategy)
            strategy_combo = str(auto_payload.get("strategy_combo") or strategy_combo)
            position_sizing = str(auto_payload.get("position_sizing") or position_sizing)
            sizing_mode = str(auto_payload.get("sizing") or auto_payload.get("sizing_mode") or position_sizing)
            initial_cash = _as_float(auto_payload.get("initial_cash"), initial_cash)
            position_pct = _as_float(auto_payload.get("position_pct"), position_pct)
            stop_loss_pct = _as_float(auto_payload.get("stop_loss_pct"), stop_loss_pct)
            take_profit_pct = _as_float(auto_payload.get("take_profit_pct"), take_profit_pct)
            if strategy == "combo_signal":
                legacy = True
        effective = _v321_effective_legacy_params(
            position_pct=position_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            buy_score=buy_score,
            sell_score=sell_score,
            initial_cash=initial_cash,
            sizing_mode=sizing_mode,
            horizon=horizon,
            dca_amount=dca_amount,
            atr_risk_pct=atr_risk_pct,
        )
        if not legacy:
            cfg = V319BacktestConfig(
                strategy="factor_rule_strategy" if strategy in {x["key"] for x in backtest_service.strategies} else strategy,
                symbols=[symbol],
                initial_cash=initial_cash,
                position_pct=effective["position_pct"],
                sizing=sizing_mode,
                commission_rate=fee_rate,
                slippage_bps=slippage_rate * 10000,
                stop_loss_pct=effective["stop_loss_pct"],
                take_profit_pct=effective["take_profit_pct"],
                buy_score=effective["buy_score"],
                sell_score=effective["sell_score"],
                adjust=adjust,
                warmup_bars=min(60, max(10, limit // 5)),
                volume_limit_pct=1.0,
            )
            result_v320 = backtest_engine_v320.run(cfg, market_data={symbol: bars})
            data = _v320_compatible_backtest_payload(result_v320, symbol, strategy, bars, q, limit, adjust)
            data = _augment_v321_backtest_payload(
                data,
                sizing_mode=sizing_mode,
                horizon=horizon,
                compound_returns=compound_returns,
                dca_amount=dca_amount,
                dca_frequency=dca_frequency,
                pyramid_step_pct=pyramid_step_pct,
                pyramid_max_adds=pyramid_max_adds,
                atr_risk_pct=atr_risk_pct,
                anomaly_filter=anomaly_filter,
                quality_filter=quality_filter,
                weights={
                    "fundamental": fundamental_weight,
                    "technical": technical_weight,
                    "information": information_weight,
                    "market": market_weight,
                },
            )
            data = _attach_v321_effective_controls(data, effective)
            if auto_payload:
                data = _attach_auto_config_to_backtest_data(data, auto_payload, cfg)
            backtest_storage_v319.save(result_v320)
            return _v319_response(
                True,
                run_id=result_v320.run_id,
                data=data,
                metrics=result_v320.metrics,
                warnings=result_v320.warnings,
                cache_status=result_v320.cache_status,
                engine_version="v3.20",
            )
        result = backtest_service.run(
            symbol,
            [_legacy_bar_like(b) for b in bars],
            LegacyBacktestConfig(
                strategy=strategy,
                strategy_combo=tuple(x.strip() for x in str(strategy_combo or "").split(",") if x.strip()),
                combo_buy_rule=combo_buy_rule,
                combo_sell_rule=combo_sell_rule,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                slippage_rate=slippage_rate,
                position_pct=effective["position_pct"],
                stop_loss_pct=effective["stop_loss_pct"],
                take_profit_pct=effective["take_profit_pct"],
                buy_score=effective["buy_score"],
                sell_score=effective["sell_score"],
            ),
            name=getattr(q, "name", None) if q else symbol,
        )
        result["quote_source"] = getattr(q, "source", None) if q else None
        result["kline_source"] = sorted({getattr(b, "source", "") for b in bars if getattr(b, "source", "")})
        result["adjust"] = adjust
        result["engine_version"] = "legacy_single_symbol_backtest"
        result["legacy"] = True
        result["legacy_warning"] = "legacy 快速验证，不作为科学组合回测。V3.20 科学回测请使用默认 API 或 POST /api/backtest/run。"
        result["requested_limit"] = limit
        result["data_quality"]["requested_bars"] = limit
        result["data_quality"]["short_kline"] = len(bars) < min(limit, 120)
        result = _augment_v321_backtest_payload(
            result,
            sizing_mode=sizing_mode,
            horizon=horizon,
            compound_returns=compound_returns,
            dca_amount=dca_amount,
            dca_frequency=dca_frequency,
            pyramid_step_pct=pyramid_step_pct,
            pyramid_max_adds=pyramid_max_adds,
            atr_risk_pct=atr_risk_pct,
            anomaly_filter=anomaly_filter,
            quality_filter=quality_filter,
            weights={
                "fundamental": fundamental_weight,
                "technical": technical_weight,
                "information": information_weight,
                "market": market_weight,
            },
        )
        result = _attach_v321_effective_controls(result, effective)
        if auto_payload:
            legacy_auto_cfg = V319BacktestConfig(
                strategy="combo_signal",
                symbols=[symbol],
                initial_cash=initial_cash,
                position_pct=effective["position_pct"],
                sizing=sizing_mode,
                commission_rate=fee_rate,
                slippage_bps=slippage_rate * 10000,
                stop_loss_pct=effective["stop_loss_pct"],
                take_profit_pct=effective["take_profit_pct"],
                max_single_position_pct=_as_float(auto_payload.get("max_single_position_pct"), effective["position_pct"]),
                cash_reserve_pct=_as_float(auto_payload.get("cash_reserve_pct"), 0.02),
            )
            result = _attach_auto_config_to_backtest_data(result, auto_payload, legacy_auto_cfg)
        return {"ok": True, "data": result}
    except Exception as exc:
        return {"ok": False, "message": str(exc)[:240], "symbol": symbol, "strategy": strategy}


def _v320_compatible_backtest_payload(result: object, symbol: str, strategy: str, bars: list, quote: object | None, limit: int, adjust: str) -> dict:
    data = result.to_dict()
    metrics = data.get("metrics", {})
    equity_curve = data.get("equity_curve", [])
    initial_cash = float(data.get("config", {}).get("initial_cash", 0.0) or 0.0)
    final_equity = float(equity_curve[-1].get("equity", 0.0)) if equity_curve else initial_cash
    start_close = _bar_number(bars[0], "close") if bars else 0.0
    end_close = _bar_number(bars[-1], "close") if bars else 0.0
    buy_hold = (end_close / start_close - 1) * 100 if start_close else 0.0
    trades = [_v320_compat_trade(t, idx + 1) for idx, t in enumerate(data.get("trades", []))]
    score_provenance = [dict(x) for x in (data.get("score_provenance") or []) if isinstance(x, dict)]
    score_provenance_summary = [
        x.get("summary") or {
            "symbol": x.get("symbol"),
            "score": x.get("final_score"),
            "strategy_family": x.get("strategy_family"),
            "no_lookahead": x.get("no_lookahead"),
            "coverage_pct": x.get("coverage_pct"),
        }
        for x in score_provenance[:20]
    ]
    score_series = [
        {
            "date": str(x.get("decision_time") or "")[:10],
            "symbol": x.get("symbol"),
            "score": x.get("final_score"),
            "strategy_family": x.get("strategy_family"),
            "action": x.get("signal_action"),
        }
        for x in score_provenance
    ]
    fills = [x for x in data.get("fills", []) if not x.get("blocked") and int(x.get("quantity") or 0) > 0]
    trade_events = _hydrate_trade_event_cash(
        _v320_trade_events_from_trades(trades) if trades else _v320_trade_events(fills),
        initial_cash,
    )
    cost_summary = {
        "commission": round(sum(float(x.get("commission") or 0) for x in fills), 6),
        "stamp_tax": round(sum(float(x.get("stamp_tax") or 0) for x in fills), 6),
        "transfer_fee": round(sum(float(x.get("transfer_fee") or 0) for x in fills), 6),
        "slippage_cost_est": round(sum(float(x.get("slippage_cost") or 0) for x in fills), 6),
        "total_cost": round(sum(float(x.get("total_cost") or 0) for x in fills), 6),
        "turnover": round(sum(abs(float(x.get("gross_amount") or 0)) for x in fills), 6),
    }
    last_state = data.get("portfolio_states", [])[-1] if data.get("portfolio_states") else {}
    positions = last_state.get("positions") or {}
    first_pos = next(iter(positions.values()), {}) if positions else {}
    kline = [_bar_dict(x) for x in bars]
    return {
        "run_id": data.get("run_id"),
        "engine_version": "v3.20",
        "symbol": symbol,
        "name": getattr(quote, "name", None) if quote else symbol,
        "strategy": strategy,
        "strategy_name": f"{strategy} · V3.20",
        "final_equity": round(final_equity, 6),
        "total_return_pct": metrics.get("total_return_pct", 0.0),
        "annualized_return_pct": metrics.get("annualized_return_pct", 0.0),
        "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
        "sharpe": metrics.get("sharpe", 0.0),
        "win_rate_pct": metrics.get("win_rate_pct", 0.0),
        "trade_count": metrics.get("trade_count", len(trades)),
        "buy_hold_return_pct": round(buy_hold, 4),
        "excess_return_pct": round(float(metrics.get("total_return_pct", 0.0) or 0.0) - buy_hold, 4),
        "equity_curve": equity_curve,
        "score_series": score_series,
        "score_provenance": score_provenance,
        "score_provenance_summary": score_provenance_summary,
        "score_provenance_count": len(score_provenance),
        "strategy_family": (score_provenance_summary[-1] or {}).get("strategy_family") if score_provenance_summary else "",
        "market_regime": ((score_provenance[-1] or {}).get("market_state") or {}).get("market_regime") if score_provenance else "",
        "score_formula": {**SCORE_FORMULA, "note": SCORE_FORMULA.get("note", "") + "；本次默认接口已切换到 V3.20 科学回测引擎。"},
        "kline": kline,
        "markers": _v320_markers(fills),
        "anomaly_markers": [x for x in _v320_markers(data.get("fills", [])) if x.get("type") == "blocked"],
        "period": {
            "start": kline[0]["date"] if kline else None,
            "end": kline[-1]["date"] if kline else None,
            "bars": len(kline),
            "calendar_days": len(kline),
        },
        "data_quality": {
            "start": kline[0]["date"] if kline else None,
            "end": kline[-1]["date"] if kline else None,
            "bars": len(kline),
            "requested_bars": limit,
            "short_kline": len(kline) < min(limit, 120),
        },
        "cost_summary": cost_summary,
        "position_summary": {
            "cash": last_state.get("cash", final_equity),
            "shares": first_pos.get("quantity", 0),
            "max_shares": max([int(e.get("position_shares") or 0) for e in trade_events] or [0]),
            "avg_cost_basis": first_pos.get("avg_cost", "--"),
            "note": "V3.20 默认使用下一交易日执行、A股涨跌停/T+1/手数约束和滑点模式。",
        },
        "trades": trades,
        "trade_events": trade_events,
        "trade_event_count": len(trade_events),
        "params": data.get("config", {}),
        "params_cn": {
            "策略": f"{strategy} · V3.20",
            "初始资金": data.get("config", {}).get("initial_cash"),
            "仓位比例": data.get("config", {}).get("position_pct"),
            "手续费率": data.get("config", {}).get("commission_rate"),
            "滑点基点": data.get("config", {}).get("slippage_bps"),
            "止损": data.get("config", {}).get("stop_loss_pct"),
            "止盈": data.get("config", {}).get("take_profit_pct"),
            "复权口径": adjust,
        },
        "api_labels": {
            "strategy": "策略",
            "initial_cash": "初始资金",
            "commission_rate": "手续费率",
            "slippage_bps": "滑点基点",
            "position_pct": "仓位比例",
            "trade_events": "买卖流水",
            "position_summary": "持仓与成本",
            "cost_summary": "成本汇总",
            "period": "回测区间",
        },
        "assumptions": [
            "V3.20 科学回测：默认下一交易日成交，避免收盘后才知道的信号当日成交。",
            "滑点默认使用 price_adjusted_slippage：成交价已反映滑点，现金不再重复扣滑点。",
            "本接口仍为研究辅助，不构成投资建议。",
        ],
        "metrics": metrics,
        "warnings": data.get("warnings", []),
    }


def _augment_v321_backtest_payload(
    data: dict,
    *,
    sizing_mode: str,
    horizon: str,
    compound_returns: bool,
    dca_amount: float,
    dca_frequency: str,
    pyramid_step_pct: float,
    pyramid_max_adds: int,
    atr_risk_pct: float,
    anomaly_filter: bool,
    quality_filter: bool,
    weights: dict[str, float],
) -> dict:
    data = dict(data or {})
    metrics = dict(data.get("metrics") or {})
    trades = data.get("trades") or []
    returns = [float(t.get("pnl_pct") or 0.0) for t in trades if isinstance(t, dict)]
    wins = [x for x in returns if x > 0]
    losses = [x for x in returns if x < 0]
    metrics.setdefault("expectancy", round((sum(returns) / len(returns)) if returns else 0.0, 6))
    metrics.setdefault("payoff_ratio", round((abs(sum(wins) / len(wins)) / abs(sum(losses) / len(losses))) if wins and losses else 0.0, 6))
    metrics.setdefault("avg_win", round(sum(wins) / len(wins), 6) if wins else 0.0)
    metrics.setdefault("avg_loss", round(sum(losses) / len(losses), 6) if losses else 0.0)
    metrics.setdefault("max_consecutive_losses", _max_consecutive_losses(returns))
    metrics.setdefault("MFE", metrics.get("avg_mfe_pct", 0.0))
    metrics.setdefault("MAE", metrics.get("avg_mae_pct", 0.0))
    metrics.setdefault("stop_loss_efficiency", metrics.get("stop_loss_efficiency", 0.0))
    metrics.setdefault("take_profit_efficiency", metrics.get("take_profit_efficiency", 0.0))
    final_equity = float(data.get("final_equity") or 0.0)
    cash = _safe_float((data.get("position_summary") or {}).get("cash"))
    if final_equity > 0 and cash is not None:
        metrics.setdefault("cash_drag_pct", round(max(0.0, min(cash / final_equity * 100.0, 100.0)), 4))
        metrics.setdefault("position_utilization_pct", round(max(0.0, min(100.0 - metrics["cash_drag_pct"], 100.0)), 4))
    else:
        metrics.setdefault("cash_drag_pct", 0.0)
        metrics.setdefault("position_utilization_pct", 0.0)
    score_rows = [x for x in (data.get("score_provenance") or []) if isinstance(x, dict)]
    data.setdefault(
        "score_provenance_summary",
        [
            x.get("summary") or {
                "symbol": x.get("symbol"),
                "score": x.get("final_score"),
                "strategy_family": x.get("strategy_family"),
                "no_lookahead": x.get("no_lookahead"),
                "coverage_pct": x.get("coverage_pct"),
            }
            for x in score_rows[:20]
        ],
    )
    horizon_cfg = StrategyHorizonConfig(horizon=horizon if horizon in {"intraday_paper", "short_term", "swing", "position", "dca", "hybrid"} else "swing")
    valid_sizing_modes = {
        "fixed_percent",
        "equal_weight",
        "score_weighted",
        "volatility_target",
        "atr_risk",
        "fixed_risk_per_trade",
        "fractional_kelly",
        "pyramid",
        "dca",
        "core_satellite",
    }
    sizing_cfg = PositionSizingConfig(
        sizing_mode=sizing_mode if sizing_mode in valid_sizing_modes else "score_weighted",
        compound_returns=bool(compound_returns),
        dca_amount=float(dca_amount or 0.0),
        dca_frequency=str(dca_frequency or "monthly"),
        pyramid_step_pct=float(pyramid_step_pct or 0.0) / (100.0 if float(pyramid_step_pct or 0.0) > 1 else 1.0),
        pyramid_max_adds=int(pyramid_max_adds or 0),
        risk_per_trade_pct=float(atr_risk_pct or 0.0) / (100.0 if float(atr_risk_pct or 0.0) > 1 else 1.0),
    )
    metrics["position_sizing_attribution"] = {
        "mode": sizing_mode,
        "compound_returns": bool(compound_returns),
        "reinvestment_basis": "equity" if compound_returns else "initial_cash",
        "atr_risk_pct": atr_risk_pct,
    }
    metrics["filter_attribution"] = {
        "quality_filter": bool(quality_filter),
        "anomaly_filter": bool(anomaly_filter),
        "weights": weights,
    }
    metrics["horizon_attribution"] = horizon_cfg.resolved_rules()
    data["metrics"] = metrics
    data["position_sizing_config"] = sizing_cfg.to_dict()
    data["horizon_config"] = horizon_cfg.to_dict()
    data["compound_returns"] = bool(compound_returns)
    data["research_disclaimer"] = "研究辅助，不构成投资建议；回测和实时模拟均不连接真实券商。"
    data.setdefault("api_labels", {})
    data["api_labels"].update(
        {
            "position_sizing": "资金管理模式",
            "horizon": "交易周期",
            "compound_returns": "收益再投资",
            "expectancy": "期望收益",
            "payoff_ratio": "赔率",
            "MFE": "最大有利波动",
            "MAE": "最大不利波动",
        }
    )
    data.setdefault("params", {})
    data["params"].update(
        {
            "position_sizing": sizing_mode,
            "horizon": horizon,
            "compound_returns": bool(compound_returns),
            "dca_amount": dca_amount,
            "dca_frequency": dca_frequency,
            "pyramid_step_pct": pyramid_step_pct,
            "pyramid_max_adds": pyramid_max_adds,
            "atr_risk_pct": atr_risk_pct,
            "quality_filter": bool(quality_filter),
            "anomaly_filter": bool(anomaly_filter),
            "three_dimension_weights": weights,
        }
    )
    data.setdefault("params_cn", {})
    data["params_cn"].update(
        {
            "资金管理": sizing_mode,
            "交易周期": horizon,
            "收益再投资": "开启" if compound_returns else "关闭",
            "定投金额": dca_amount,
            "金字塔加仓": f"{pyramid_step_pct}% / {pyramid_max_adds}次",
            "ATR风险": f"{atr_risk_pct}%",
            "三面权重": f"基本{weights.get('fundamental')} / 技术{weights.get('technical')} / 信息{weights.get('information')} / 大盘{weights.get('market')}",
        }
    )
    return data


def _max_consecutive_losses(values: list[float]) -> int:
    best = cur = 0
    for value in values:
        if value < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _bar_dict(bar: object) -> dict:
    return {
        "date": str(getattr(bar, "ts", None) or getattr(bar, "date", ""))[:10] if not isinstance(bar, dict) else str(bar.get("ts") or bar.get("date") or "")[:10],
        "open": _bar_number(bar, "open"),
        "high": _bar_number(bar, "high"),
        "low": _bar_number(bar, "low"),
        "close": _bar_number(bar, "close"),
        "volume": _bar_number(bar, "volume"),
        "amount": _bar_number(bar, "amount"),
    }


def _bar_number(bar: object, key: str) -> float:
    try:
        value = bar.get(key) if isinstance(bar, dict) else getattr(bar, key)
        return float(value or 0.0)
    except Exception:
        return 0.0


def _v320_markers(fills: list[dict]) -> list[dict]:
    markers = []
    for fill in fills:
        markers.append(
            {
                "date": fill.get("date"),
                "type": "blocked" if fill.get("blocked") else fill.get("side"),
                "price": fill.get("price"),
                "label": "!" if fill.get("blocked") else ("B" if fill.get("side") == "buy" else "S"),
                "reason": fill.get("reason"),
            }
        )
    return markers


def _v320_trade_events(fills: list[dict]) -> list[dict]:
    events = []
    cash_after = None
    position = 0
    cost_basis = 0.0
    for idx, fill in enumerate(fills, start=1):
        side = fill.get("side")
        qty = int(fill.get("quantity") or 0)
        gross = float(fill.get("gross_amount") or 0.0)
        fee = float(fill.get("cash_cost") or fill.get("total_cost") or 0.0)
        if side == "buy":
            position += qty
            cost_basis = float(fill.get("price") or 0.0)
            cash_change = -(gross + fee)
        else:
            position = max(0, position - qty)
            cash_change = gross - fee
        events.append(
            {
                "event_id": f"{idx}-{side}",
                "trade_index": (idx + 1) // 2,
                "date": fill.get("date"),
                "side": side,
                "action": "买入" if side == "buy" else "卖出",
                "price": fill.get("price"),
                "shares": qty,
                "amount": gross,
                "fee": fee,
                "cash_change": round(cash_change, 6),
                "cash_after": cash_after,
                "position_shares": position,
                "cost_basis": cost_basis,
                "realized_pnl": 0.0,
                "realized_pct": 0.0,
                "reason": fill.get("reason"),
                "signal_date": None,
                "score": None,
            }
        )
    return events


def _v320_compat_trade(trade: dict, index: int) -> dict:
    qty = int(trade.get("quantity") or trade.get("shares") or 0)
    entry_price = float(trade.get("entry_price") or 0.0)
    exit_price = float(trade.get("exit_price") or entry_price or 0.0)
    costs = float(trade.get("costs") or 0.0)
    entry_fee = round(costs / 2, 6)
    exit_fee = round(costs - entry_fee, 6)
    entry_value = entry_price * qty
    exit_value = exit_price * qty
    row = dict(trade)
    row.update(
        {
            "trade_index": index,
            "entry_value": round(entry_value, 6),
            "exit_value": round(exit_value, 6),
            "entry_fee": entry_fee,
            "exit_fee": exit_fee,
            "entry_cost": round(entry_value + entry_fee, 6),
            "exit_proceeds": round(exit_value - exit_fee, 6),
            "buy_shares": qty,
            "sell_shares": qty,
            "cost_basis": round(entry_price + entry_fee / max(qty, 1), 6),
            "entry_signal_date": trade.get("entry_date"),
            "exit_signal_date": trade.get("exit_date"),
            "cash_before_entry": None,
            "cash_after_exit": None,
        }
    )
    return row


def _v320_trade_events_from_trades(trades: list[dict]) -> list[dict]:
    events: list[dict] = []
    for idx, trade in enumerate(trades, start=1):
        qty = int(trade.get("buy_shares") or 0)
        events.append(
            {
                "event_id": f"{idx}-B",
                "trade_index": idx,
                "date": trade.get("entry_date"),
                "side": "buy",
                "action": "买入",
                "price": trade.get("entry_price"),
                "shares": qty,
                "amount": trade.get("entry_value"),
                "fee": trade.get("entry_fee"),
                "cash_change": -float(trade.get("entry_cost") or 0.0),
                "cash_after": None,
                "position_shares": qty,
                "cost_basis": trade.get("cost_basis"),
                "realized_pnl": 0.0,
                "realized_pct": 0.0,
                "reason": trade.get("entry_reason"),
                "signal_date": trade.get("entry_signal_date"),
                "score": trade.get("entry_signal_score"),
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
                "shares": int(trade.get("sell_shares") or qty),
                "amount": trade.get("exit_value"),
                "fee": trade.get("exit_fee"),
                "cash_change": trade.get("exit_proceeds"),
                "cash_after": trade.get("cash_after_exit"),
                "position_shares": 0,
                "cost_basis": trade.get("cost_basis"),
                "realized_pnl": trade.get("pnl"),
                "realized_pct": trade.get("pnl_pct"),
                "reason": trade.get("exit_reason"),
                "signal_date": trade.get("exit_signal_date"),
                "score": trade.get("exit_signal_score"),
            }
        )
    return events


def _hydrate_trade_event_cash(events: list[dict], initial_cash: float) -> list[dict]:
    cash = float(initial_cash or 0.0)
    hydrated: list[dict] = []
    for event in events:
        row = dict(event)
        try:
            cash += float(row.get("cash_change") or 0.0)
        except (TypeError, ValueError):
            pass
        if row.get("cash_after") in (None, ""):
            row["cash_after"] = round(cash, 6)
        hydrated.append(row)
    return hydrated


def _legacy_bar_like(bar: object) -> object:
    if not isinstance(bar, dict):
        return bar
    raw_ts = bar.get("ts") or bar.get("date")
    if isinstance(raw_ts, str):
        try:
            raw_ts = datetime.fromisoformat(raw_ts[:10])
        except ValueError:
            raw_ts = datetime.now()
    return SimpleNamespace(
        symbol=bar.get("symbol", ""),
        frame=bar.get("frame", "1d"),
        ts=raw_ts,
        open=bar.get("open", 0.0),
        high=bar.get("high", 0.0),
        low=bar.get("low", 0.0),
        close=bar.get("close", 0.0),
        volume=bar.get("volume", 0.0),
        amount=bar.get("amount", 0.0),
        source=bar.get("source", "memory"),
    )


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


@app.get("/api/backtest/runs/{run_id}")
def backtest_run_alias_v323(run_id: str) -> dict:
    return backtest_result_v319(run_id)


@app.post("/api/backtest/v323/run")
def backtest_run_v323(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        payload = _apply_auto_config_to_backtest_payload(payload)
        cfg = _v319_config({**payload, "engine_version": "v3.23"})
        result = backtest_engine_v319.run(
            cfg,
            market_data=_v319_market_data(payload, cfg),
            screener_rows=payload.get("screener_rows") or payload.get("snapshot_rows"),
        )
        data = _attach_auto_config_to_backtest_data(result.to_dict(), payload, cfg)
        backtest_storage_v319.save(data)
        for row in data.get("orders") or []:
            row["mode"] = "backtest"
            row["session_id"] = result.run_id
            trading_store_v323.put("orders", row, mode="backtest", symbol=str(row.get("symbol") or ""), session_id=result.run_id, record_id=str(row.get("order_id") or ""))
        for row in data.get("fills") or []:
            row["mode"] = "backtest"
            row["session_id"] = result.run_id
            trading_store_v323.put("fills", row, mode="backtest", symbol=str(row.get("symbol") or ""), session_id=result.run_id, record_id=str(row.get("fill_id") or ""))
        for row in data.get("score_provenance") or []:
            rid = str(row.get("score_provenance_id") or row.get("provenance_id") or "")
            if rid:
                row.setdefault("provenance_id", rid)
                score_provenance_memory_v323[rid] = row
                trading_store_v323.put("score_provenance", row, mode="backtest", symbol=str(row.get("symbol") or ""), session_id=result.run_id, record_id=rid)
        for symbol in result.symbols:
            chart_annotation_service_v323.rebuild(symbol, orders=data.get("orders") or [], fills=data.get("fills") or [], mode="backtest")
        trading_store_v323.put(
            "audit_events",
            {
                "event_type": "backtest_v323_run",
                "run_id": result.run_id,
                "metrics": result.metrics,
                "auto_trading_config_applied": bool(data.get("auto_trading_config_applied")),
                "effective_auto_controls": data.get("effective_auto_controls") or {},
            },
            mode="backtest",
            session_id=result.run_id,
        )
        return _v319_response(
            True,
            run_id=result.run_id,
            data=data,
            metrics=result.metrics,
            warnings=data.get("warnings", result.warnings),
            errors=result.errors,
            cache_status=result.cache_status,
        )
    except Exception as exc:
        return _v319_response(False, errors=[str(exc)[:300]], message=str(exc)[:300])


@app.get("/api/backtest/v323/runs")
def backtest_v323_runs(limit: int = 50) -> dict:
    return backtest_runs_v319(limit)


@app.get("/api/backtest/v323/runs/{run_id}")
def backtest_v323_run_detail(run_id: str) -> dict:
    return backtest_result_v319(run_id)


@app.get("/api/backtest/v323/runs/{run_id}/markers")
def backtest_v323_run_markers(run_id: str, symbol: str = "") -> dict:
    try:
        data = backtest_storage_v319.load(run_id)
        symbols = [symbol] if symbol else list(data.get("symbols") or [])
        rows = []
        for sym in symbols:
            rows.extend(chart_annotation_service_v323.rebuild(sym, orders=data.get("orders") or [], fills=data.get("fills") or [], mode="backtest"))
        return {"ok": True, "run_id": run_id, "data": rows, "count": len(rows)}
    except FileNotFoundError:
        return {"ok": False, "run_id": run_id, "data": [], "errors": ["run_id not found"]}


@app.get("/api/backtest/v323/runs/{run_id}/provenance")
def backtest_v323_run_provenance(run_id: str) -> dict:
    try:
        data = backtest_storage_v319.load(run_id)
        rows = data.get("score_provenance") or []
        return {"ok": True, "run_id": run_id, "data": rows, "count": len(rows)}
    except FileNotFoundError:
        return {"ok": False, "run_id": run_id, "data": [], "errors": ["run_id not found"]}


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


@app.post("/api/trading/signal")
def trading_signal_v320(payload: dict = Body(default_factory=dict)) -> dict:
    try:
        signal = TradingSignal(
            symbol=str(payload.get("symbol") or "300750"),
            side=str(payload.get("side") or payload.get("action") or "buy").lower(),
            quantity=int(payload.get("quantity") or 0),
            target_weight=float(payload.get("target_weight") or 0.0),
            price=float(payload.get("price")) if payload.get("price") is not None else None,
            score=float(payload.get("score") or 0.0),
            reason=str(payload.get("reason") or "manual paper signal"),
            source=str(payload.get("source") or "api"),
        )
        quote = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
        data = paper_trading_gateway_v320.submit_signal(signal, quote=quote)
        return {"ok": True, "data": data, "disclaimer": "paper trading only; no real broker connected"}
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)[:300]], "disclaimer": "paper trading only"}


@app.get("/api/trading/paper/orders")
def trading_paper_orders_v320() -> dict:
    return {"ok": True, "data": paper_trading_gateway_v320.orders_snapshot(), "paper_only": True}


@app.get("/api/trading/paper/positions")
def trading_paper_positions_v320() -> dict:
    return {"ok": True, "data": paper_trading_gateway_v320.positions_snapshot(), "paper_only": True}


@app.get("/api/trading/risk/status")
def trading_risk_status_v320() -> dict:
    return {"ok": True, "data": paper_trading_gateway_v320.risk_gateway.status()}


@app.get("/api/trading/audit")
def trading_audit_v320(limit: int = 200) -> dict:
    return {"ok": True, "data": paper_trading_gateway_v320.audit.list(limit=max(1, min(int(limit or 200), 1000)))}


@app.post("/api/realtime-paper/start")
def realtime_paper_start(payload: dict = Body(default_factory=dict)) -> dict:
    result = realtime_paper_engine_v323.start_session(payload)
    engine = dict(result.get("engine") or {})
    engine["v323_session"] = result.get("session")
    engine["session_id"] = (result.get("session") or {}).get("session_id")
    return engine


@app.post("/api/realtime-paper/stop")
def realtime_paper_stop() -> dict:
    result = realtime_paper_engine_v323.stop_active_session()
    engine = dict(result.get("engine") or {})
    engine["v323_session"] = result.get("session")
    return engine


@app.get("/api/realtime-paper/status")
def realtime_paper_status() -> dict:
    realtime_paper_engine_v323.sync_engine_state()
    data = realtime_paper_engine_v321.status()
    data["v323_session"] = realtime_paper_engine_v323.active_session()
    return data


@app.get("/api/realtime-paper/portfolio")
def realtime_paper_portfolio() -> dict:
    realtime_paper_engine_v323.sync_engine_state()
    data = realtime_paper_engine_v321.portfolio()
    data["v323_session"] = realtime_paper_engine_v323.active_session()
    return data


@app.get("/api/realtime-paper/orders")
def realtime_paper_orders(limit: int = 200) -> dict:
    realtime_paper_engine_v323.sync_engine_state()
    return realtime_paper_engine_v321.orders(limit=max(1, min(int(limit or 200), 1000)))


@app.get("/api/realtime-paper/signals")
def realtime_paper_signals(limit: int = 200) -> dict:
    realtime_paper_engine_v323.sync_engine_state()
    return realtime_paper_engine_v321.signal_rows(limit=max(1, min(int(limit or 200), 1000)))


@app.get("/api/realtime-paper/audit")
def realtime_paper_audit(limit: int = 300) -> dict:
    realtime_paper_engine_v323.sync_engine_state()
    return realtime_paper_engine_v321.audit(limit=max(1, min(int(limit or 300), 1000)))


@app.get("/api/realtime-paper/confirmations")
def realtime_paper_confirmations(status: str = "pending", limit: int = 200) -> dict:
    rows = realtime_paper_engine_v321.human_confirm_queue.list(
        status=status or None,
        limit=max(1, min(int(limit or 200), 1000)),
    )
    return {"ok": True, "data": rows, "count": len(rows), "paper_only": True}


@app.post("/api/realtime-paper/confirmations/{task_id}/approve")
def realtime_paper_confirm_approve(task_id: str, payload: dict = Body(default_factory=dict)) -> dict:
    try:
        task = realtime_paper_engine_v321.human_confirm_queue.approve(
            task_id,
            operator=str(payload.get("operator") or "paper_user"),
        )
        return {"ok": True, "data": task.to_dict(), "paper_only": True}
    except KeyError as exc:
        return {"ok": False, "message": str(exc), "paper_only": True}


@app.post("/api/realtime-paper/confirmations/{task_id}/reject")
def realtime_paper_confirm_reject(task_id: str, payload: dict = Body(default_factory=dict)) -> dict:
    try:
        task = realtime_paper_engine_v321.human_confirm_queue.reject(
            task_id,
            operator=str(payload.get("operator") or "paper_user"),
        )
        return {"ok": True, "data": task.to_dict(), "paper_only": True}
    except KeyError as exc:
        return {"ok": False, "message": str(exc), "paper_only": True}


def _payload_has_trade_price(payload: dict) -> bool:
    quote = payload.get("quote") if isinstance(payload.get("quote"), dict) else {}
    for value in (payload.get("price"), payload.get("last"), quote.get("last"), quote.get("price")):
        try:
            if value not in (None, "", "--") and float(value) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _hydrate_realtime_tick_payload(payload: dict | None) -> dict:
    out = dict(payload or {})
    symbol = str(out.get("symbol") or "").strip()
    if not symbol or _payload_has_trade_price(out):
        return out
    missing = list(out.get("missing_data") or [])
    try:
        quote_obj = service.get_quote(symbol, force_refresh=False)
        quote = quote_obj.to_dict() if hasattr(quote_obj, "to_dict") else dict(getattr(quote_obj, "__dict__", {}) or {})
    except Exception as exc:
        if "quote_snapshot_missing" not in missing:
            missing.append("quote_snapshot_missing")
        out["missing_data"] = missing
        out["quote_hydrated"] = False
        out["quote_hydrate_error"] = str(exc)[:180]
        return out
    if not quote or not _payload_has_trade_price({"quote": quote}):
        if "quote_snapshot_missing" not in missing:
            missing.append("quote_snapshot_missing")
        out["missing_data"] = missing
        out["quote_hydrated"] = False
        return out
    merged_quote = {**quote, **dict(out.get("quote") or {})}
    out["quote"] = merged_quote
    out.setdefault("price", merged_quote.get("last") or merged_quote.get("price"))
    out.setdefault("last", merged_quote.get("last") or merged_quote.get("price"))
    out.setdefault("quote_ts", merged_quote.get("ts") or merged_quote.get("fetched_at"))
    out.setdefault("name", merged_quote.get("name"))
    out["quote_hydrated"] = True
    evidence = list(out.get("evidence") or [])
    evidence.append("quote_hydrated_from_market_service")
    out["evidence"] = list(dict.fromkeys(evidence))
    return out


@app.post("/api/realtime-paper/tick")
def realtime_paper_tick(payload: dict = Body(default_factory=dict)) -> dict:
    payload = _hydrate_realtime_tick_payload(payload)
    return realtime_paper_engine_v323.tick(
        payload,
        manual_replay=bool(payload.get("manual_replay") or payload.get("paper_replay")),
    )


@app.post("/api/realtime-paper/replay")
def realtime_paper_replay(payload: dict = Body(default_factory=dict)) -> dict:
    return realtime_paper_engine_v323.replay(payload)


@app.get("/api/auto-trading/config")
def auto_trading_config_get() -> dict:
    latest = cache_state_service.get("auto_trading_config", "default")
    if latest.data:
        upgraded = _build_auto_trading_config(latest.data if isinstance(latest.data, dict) else {})
        return {"ok": True, "data": upgraded, "cache_status": latest.cache_status, "defaulted": False, "upgraded": True}
    config = _build_auto_trading_config()
    return {"ok": True, "data": config, "cache_status": latest.cache_status, "defaulted": True}


@app.post("/api/auto-trading/config")
def auto_trading_config_save(payload: dict = Body(default_factory=dict)) -> dict:
    config = _build_auto_trading_config(payload)
    return _save_auto_trading_config(config)


@app.post("/api/auto-trading/config/one-click")
def auto_trading_config_one_click(payload: dict = Body(default_factory=dict)) -> dict:
    config = _build_auto_trading_config(payload, prefer_latest_screener=True)
    saved = _save_auto_trading_config(config, event_type="auto_trading_one_click_config")
    readiness = _auto_trading_readiness(config)
    return {
        **saved,
        "readiness": readiness,
        "symbols_source": config.get("symbols_source"),
        "screener_snapshot_id": config.get("screener_snapshot_id"),
        "warnings": [] if config.get("symbols") else ["未找到可交易股票池，已阻止自动启动"],
    }


@app.get("/api/auto-trading/readiness")
def auto_trading_readiness_get() -> dict:
    config = auto_trading_config_get()["data"]
    return _auto_trading_readiness(config)


@app.post("/api/auto-trading/start-paper")
def auto_trading_start_paper(payload: dict = Body(default_factory=dict)) -> dict:
    config = _build_auto_trading_config(payload)
    saved = _save_auto_trading_config(config, event_type="auto_trading_start_paper_config")
    session_payload = {
        **payload,
        **config,
        "symbols": config.get("symbols") or [],
        "strategy_family": config.get("strategy_family") or "hybrid",
        "selected_strategies": config.get("strategy_combo") or [],
        "interval_seconds": int(config.get("interval_seconds") or 15),
        "initial_cash": float(config.get("initial_cash") or 100000),
        "source_page": "auto-trading",
    }
    session = realtime_paper_engine_v323.start_session(session_payload)
    session_id = str((session.get("session") or {}).get("session_id") or "")
    trading_store_v323.put(
        "audit_events",
        {
            "event_type": "auto_trading_start_paper",
            "config": config,
            "session": session.get("session"),
            "engine": session.get("engine"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        mode="realtime_paper",
        session_id=session_id,
        record_id=f"auto-trading-start-{session_id}",
    )
    return {
        "ok": bool(session.get("ok")),
        "config": config,
        "session": session.get("session"),
        "engine": session.get("engine"),
        "saved": saved.get("cache_status"),
        "readiness": _auto_trading_readiness(config),
    }


@app.post("/api/realtime-paper/sessions/start")
def realtime_paper_session_start(payload: dict = Body(default_factory=dict)) -> dict:
    return realtime_paper_engine_v323.start_session(payload)


@app.get("/api/realtime-paper/sessions")
def realtime_paper_sessions() -> dict:
    return {"ok": True, "data": realtime_paper_engine_v323.list_sessions()}


@app.get("/api/realtime-paper/sessions/{session_id}")
def realtime_paper_session_get(session_id: str) -> dict:
    session = realtime_paper_engine_v323.get_session(session_id)
    if session:
        realtime_paper_engine_v323.sync_engine_state(session_id)
    return {"ok": bool(session), "data": session, "engine": realtime_paper_engine_v321.status() if session else None}


@app.post("/api/realtime-paper/sessions/{session_id}/pause")
def realtime_paper_session_pause(session_id: str) -> dict:
    return realtime_paper_engine_v323.pause(session_id)


@app.post("/api/realtime-paper/sessions/{session_id}/resume")
def realtime_paper_session_resume(session_id: str) -> dict:
    return realtime_paper_engine_v323.resume(session_id)


@app.post("/api/realtime-paper/sessions/{session_id}/stop")
def realtime_paper_session_stop(session_id: str) -> dict:
    return realtime_paper_engine_v323.stop_session(session_id)


@app.post("/api/realtime-paper/sessions/{session_id}/kill-switch")
def realtime_paper_session_kill(session_id: str, payload: dict = Body(default_factory=dict)) -> dict:
    return realtime_paper_engine_v323.kill_switch(session_id, enabled=bool(payload.get("enabled", True)))


@app.get("/api/realtime-paper/sessions/{session_id}/orders")
def realtime_paper_session_orders(session_id: str, limit: int = 200) -> dict:
    rows = realtime_paper_engine_v323.stored_orders(session_id, limit=max(1, min(int(limit or 200), 1000)))
    return {"ok": True, "data": rows, "count": len(rows), "session_id": session_id}


@app.get("/api/realtime-paper/sessions/{session_id}/fills")
def realtime_paper_session_fills(session_id: str, limit: int = 200) -> dict:
    rows = realtime_paper_engine_v323.stored_fills(session_id, limit=max(1, min(int(limit or 200), 1000)))
    return {"ok": True, "data": rows, "count": len(rows), "session_id": session_id}


@app.get("/api/realtime-paper/sessions/{session_id}/positions")
def realtime_paper_session_positions(session_id: str) -> dict:
    data = realtime_paper_engine_v321.portfolio()
    stored = realtime_paper_engine_v323.stored_positions(session_id)
    return {"ok": True, "data": (stored[0] if stored else {}), "curve": data.get("curve") or [], "session_id": session_id}


@app.get("/api/realtime-paper/sessions/{session_id}/markers")
def realtime_paper_session_markers(session_id: str, symbol: str = "", mode: str = "realtime_paper") -> dict:
    rows = realtime_paper_engine_v323.stored_markers(session_id, symbol=symbol, limit=1000)
    if not rows:
        symbols = [symbol] if symbol else [s for sess in realtime_paper_engine_v323.sessions.values() for s in sess.symbols]
        rows = []
        for sym in symbols:
            rows.extend(chart_annotation_service_v323.list_markers(sym, mode=mode))
    return {"ok": True, "data": rows, "count": len(rows), "session_id": session_id}


@app.get("/api/realtime-paper/sessions/{session_id}/audit")
def realtime_paper_session_audit(session_id: str, limit: int = 300) -> dict:
    rows = realtime_paper_engine_v323.stored_audit(session_id, limit=max(1, min(int(limit or 300), 1000)))
    return {"ok": True, "data": rows, "count": len(rows), "session_id": session_id}


def _normalize_live_position(row: dict) -> dict:
    row = dict(row or {})
    qty = _as_float(row.get("quantity") or row.get("volume") or row.get("qty"), 0.0)
    available = _as_float(row.get("available_quantity") or row.get("available") or row.get("enable_amount"), 0.0)
    cost = _as_float(row.get("cost_price") or row.get("avg_price") or row.get("avg_cost"), 0.0)
    last = _as_float(row.get("last_price") or row.get("price") or row.get("market_price"), 0.0)
    market_value = _as_float(row.get("market_value") or row.get("amount"), qty * last if qty and last else 0.0)
    unrealized = _as_float(row.get("unrealized_pnl") or row.get("pnl"), (last - cost) * qty if qty and cost and last else 0.0)
    pnl_pct = _as_float(row.get("unrealized_pnl_pct") or row.get("pnl_pct"), ((last - cost) / cost * 100) if cost and last else 0.0)
    out = {
        **row,
        "symbol": str(row.get("symbol") or row.get("code") or "").strip(),
        "name": row.get("name") or row.get("stock_name") or "",
        "quantity": int(qty) if float(qty).is_integer() else qty,
        "available_quantity": int(available) if float(available).is_integer() else available,
        "cost_price": round(cost, 6) if cost or "cost_price" in row or "avg_price" in row or "avg_cost" in row else None,
        "avg_price": round(cost, 6) if cost or "cost_price" in row or "avg_price" in row or "avg_cost" in row else None,
        "avg_cost": round(cost, 6) if cost or "cost_price" in row or "avg_price" in row or "avg_cost" in row else None,
        "last_price": round(last, 6) if last or "last_price" in row or "price" in row or "market_price" in row else None,
        "market_price": round(last, 6) if last or "last_price" in row or "price" in row or "market_price" in row else None,
        "market_value": round(market_value, 4),
        "unrealized_pnl": round(unrealized, 4),
        "pnl": round(unrealized, 4),
        "unrealized_pnl_pct": round(pnl_pct, 4),
        "pnl_pct": round(pnl_pct, 4),
        "source": row.get("source") or "broker_position",
    }
    out["display_summary"] = f"{out['symbol']} 持仓 {out['quantity']} 股，成本 {out.get('cost_price') if out.get('cost_price') is not None else '--'}，市价 {out.get('last_price') if out.get('last_price') is not None else '--'}，浮盈亏 {out['unrealized_pnl']}"
    return out


def _live_positions_summary(rows: list[dict]) -> dict:
    market_value = sum(_as_float(x.get("market_value"), 0.0) for x in rows)
    pnl = sum(_as_float(x.get("unrealized_pnl"), 0.0) for x in rows)
    cost_value = sum(_as_float(x.get("cost_price"), 0.0) * _as_float(x.get("quantity"), 0.0) for x in rows)
    return {
        "positions_count": len(rows),
        "market_value": round(market_value, 4),
        "unrealized_pnl": round(pnl, 4),
        "unrealized_pnl_pct": round(pnl / cost_value * 100, 4) if cost_value else None,
        "symbols": [x.get("symbol") for x in rows if x.get("symbol")],
    }


def _enrich_trading_record_row(table: str, item: dict) -> dict:
    row = {"table": table, **dict(item or {})}
    price = _as_float(_first_present(row.get("price"), row.get("limit_price"), row.get("avg_fill_price")), 0.0)
    qty = _as_float(_first_present(row.get("quantity"), row.get("filled_quantity"), row.get("qty")), 0.0)
    amount_default = price * qty if price and qty else 0.0
    if table == "positions":
        price = _as_float(_first_present(row.get("last_price"), row.get("market_price"), row.get("price")), price)
        amount_default = _as_float(row.get("market_value"), price * qty if price and qty else 0.0)
    elif table == "account_snapshots":
        amount_default = _as_float(_first_present(row.get("total_value"), row.get("equity"), row.get("total_assets")), 0.0)
    else:
        amount_default = _as_float(_first_present(row.get("target_value"), row.get("filled_amount")), amount_default)
    amount = _as_float(row.get("amount"), amount_default)
    fee = _as_float(_first_present(row.get("fee"), row.get("tax"), row.get("commission")), 0.0)
    pnl = _as_float(_first_present(row.get("realized_pnl"), row.get("unrealized_pnl"), row.get("pnl")), 0.0)
    pnl_pct = _as_float(_first_present(row.get("realized_pnl_pct"), row.get("unrealized_pnl_pct"), row.get("pnl_pct")), 0.0)
    if table == "fills":
        record_type = "成交"
    elif table == "orders":
        record_type = "委托"
    elif table == "positions":
        record_type = "持仓"
    elif table == "account_snapshots":
        record_type = "账户"
    elif table == "manual_confirmations":
        record_type = "确认"
    elif table == "risk_checks":
        record_type = "风控"
    elif table == "audit_events":
        record_type = "审计"
    else:
        record_type = "记录"
    row["record_type_cn"] = record_type
    row["display_price"] = round(price, 6) if price or row.get("price") is not None or row.get("last_price") is not None or row.get("market_price") is not None else None
    row["display_quantity"] = int(qty) if qty and float(qty).is_integer() else (qty if qty or any(k in row for k in ("quantity", "qty", "filled_quantity")) else None)
    row["display_amount"] = round(amount, 4) if amount or any(k in row for k in ("amount", "market_value", "target_value", "filled_amount", "total_value", "equity", "total_assets")) else None
    row["display_fee"] = round(fee, 4) if fee or any(k in row for k in ("fee", "tax", "commission")) else None
    row["display_pnl"] = round(pnl, 4) if pnl or any(k in row for k in ("realized_pnl", "unrealized_pnl", "pnl")) else None
    row["display_pnl_pct"] = round(pnl_pct, 4) if pnl_pct or any(k in row for k in ("realized_pnl_pct", "unrealized_pnl_pct", "pnl_pct")) else None
    row["display_cost_price"] = _first_present(row.get("cost_price"), row.get("avg_cost"), row.get("avg_price"))
    row["display_market_value"] = row.get("market_value")
    row["display_side"] = row.get("side") or row.get("action") or row.get("status") or row.get("event_type") or ""
    row["display_status"] = row.get("status") or row.get("status_reason") or row.get("event_type") or ""
    row["display_summary"] = "；".join(
        x
        for x in [
            f"{record_type}",
            f"方向/状态 {row['display_side']}" if row.get("display_side") else "",
            f"价格 {row['display_price']}" if row.get("display_price") is not None else "",
            f"数量 {row['display_quantity']}" if row.get("display_quantity") is not None else "",
            f"成本 {row['display_cost_price']}" if row.get("display_cost_price") is not None else "",
            f"市值 {row['display_market_value']}" if row.get("display_market_value") is not None else "",
            f"金额 {row['display_amount']}" if row.get("display_amount") is not None else "",
            f"盈亏 {row['display_pnl']}" if row.get("display_pnl") is not None else "",
            f"收益率 {row['display_pnl_pct']}%" if row.get("display_pnl_pct") is not None else "",
        ]
        if x
    )
    return row


@app.get("/api/live-broker/status")
def live_broker_status() -> dict:
    return live_trading_engine_v323.status()


@app.post("/api/live-broker/connect")
def live_broker_connect() -> dict:
    return live_trading_engine_v323.connect()


@app.post("/api/live-broker/disconnect")
def live_broker_disconnect() -> dict:
    return live_trading_engine_v323.disconnect()


@app.get("/api/live/account")
def live_account() -> dict:
    snapshot = live_trading_engine_v323.position_sync.snapshot()
    positions = [_normalize_live_position(x) for x in snapshot.get("positions") or []]
    cash = snapshot.get("cash") or {}
    available_cash = _as_float(cash.get("available_cash") or snapshot.get("available_cash") or 0, 0.0)
    frozen_cash = _as_float(cash.get("frozen_cash") or snapshot.get("frozen_cash") or 0, 0.0)
    position_value = sum(_as_float(p.get("market_value"), 0.0) for p in positions)
    unrealized_pnl = sum(_as_float(p.get("unrealized_pnl"), 0.0) for p in positions)
    enriched = {
        **snapshot,
        "positions": positions,
        "available_cash": available_cash,
        "frozen_cash": frozen_cash,
        "position_market_value": round(position_value, 4),
        "unrealized_pnl": round(unrealized_pnl, 4),
        "total_value": round(available_cash + frozen_cash + position_value, 4),
        "equity": round(available_cash + frozen_cash + position_value, 4),
        "positions_count": len(positions),
        "quality_status": "ok" if positions or available_cash or snapshot.get("authorized") else "券商未连接/未授权或无持仓",
    }
    trading_store_v323.put("account_snapshots", enriched, mode="live", session_id=str(enriched.get("session_id") or live_trading_engine_v323.session.session_id))
    return {"ok": True, "data": enriched, "source": live_trading_engine_v323.broker.health_check().to_dict()}


@app.get("/api/live/positions")
def live_positions() -> dict:
    rows = [_normalize_live_position(x.to_dict()) for x in live_trading_engine_v323.broker.get_positions()]
    for row in rows:
        trading_store_v323.put("positions", row, mode="live", symbol=str(row.get("symbol") or ""), session_id=live_trading_engine_v323.session.session_id)
    source = live_trading_engine_v323.broker.health_check().to_dict()
    return {
        "ok": True,
        "data": rows,
        "count": len(rows),
        "summary": _live_positions_summary(rows),
        "source": source,
        "missing_reason": "" if rows else "当前券商未返回持仓；可能是 disabled/unsupported、未授权或账户暂无持仓。",
    }


@app.get("/api/live/orders")
def live_orders() -> dict:
    rows = [x.to_dict() for x in live_trading_engine_v323.broker.get_orders()]
    stored = trading_store_v323.list("orders", mode="live", limit=200)
    return {"ok": True, "data": rows or stored, "source": live_trading_engine_v323.broker.health_check().to_dict()}


@app.get("/api/live/trades")
def live_trades() -> dict:
    return {"ok": True, "data": [x.to_dict() for x in live_trading_engine_v323.broker.get_trades()], "source": live_trading_engine_v323.broker.health_check().to_dict()}


@app.post("/api/live/orders/preview")
def live_order_preview(payload: dict = Body(default_factory=dict)) -> dict:
    return live_trading_engine_v323.preview_order(payload)


@app.post("/api/live/orders/preview-batch")
def live_order_preview_batch(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _symbols_from_payload(payload)
    if not symbols:
        return {"ok": False, "message": "symbols required", "data": []}
    rows = []
    for sym in symbols[:50]:
        order_payload = {**payload, "symbol": sym}
        rows.append({"symbol": sym, "preview": live_trading_engine_v323.preview_order(order_payload)})
    return {
        "ok": True,
        "data": rows,
        "count": len(rows),
        "note": "批量预检查只进入风控/确认流程，不会绕过 LIVE_TRADING_ENABLED、kill switch 或人工确认。",
    }


@app.post("/api/live/orders/place-batch")
def live_order_place_batch(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _symbols_from_payload(payload)
    if not symbols:
        return {"ok": False, "message": "symbols required", "data": []}
    confirmed = bool(payload.get("confirmed"))
    rows = []
    for sym in symbols[:50]:
        order_payload = {**payload, "symbol": sym}
        rows.append({"symbol": sym, "result": live_trading_engine_v323.place_order(order_payload, confirmed=confirmed)})
    return {
        "ok": all(bool((row.get("result") or {}).get("ok")) for row in rows),
        "data": rows,
        "count": len(rows),
        "note": "真实批量下单仍逐笔经过风控、白名单、确认队列和券商适配器；默认配置下不会真实下单。",
    }


@app.post("/api/live/orders/confirm")
def live_order_confirm(payload: dict = Body(default_factory=dict)) -> dict:
    confirm_id = str(payload.get("confirm_id") or "")
    if not confirm_id:
        return {"ok": False, "message": "confirm_id required"}
    return live_trading_engine_v323.approve_confirmation(confirm_id)


@app.post("/api/live/orders/place")
def live_order_place(payload: dict = Body(default_factory=dict)) -> dict:
    return live_trading_engine_v323.place_order(payload, confirmed=bool(payload.get("confirmed")))


@app.post("/api/live/orders/{order_id}/cancel")
def live_order_cancel(order_id: str) -> dict:
    result = live_trading_engine_v323.broker.cancel_order(order_id).to_dict()
    trading_store_v323.put("orders", {"order_id": order_id, "status": result.get("status"), "status_reason": result.get("reason"), "mode": "live"}, mode="live", record_id=order_id)
    return {"ok": bool(result.get("ok")), "data": result}


@app.post("/api/live/kill-switch")
def live_kill_switch(payload: dict = Body(default_factory=dict)) -> dict:
    return live_trading_engine_v323.kill_switch(enabled=bool(payload.get("enabled", True)))


@app.get("/api/live/confirm-queue")
def live_confirm_queue(status: str = "pending", limit: int = 200) -> dict:
    rows = live_trading_engine_v323.confirm_queue.list(status=status or None, limit=max(1, min(int(limit or 200), 1000)))
    return {"ok": True, "data": rows, "count": len(rows)}


@app.post("/api/live/confirm-queue/{confirm_id}/approve")
def live_confirm_approve(confirm_id: str) -> dict:
    return live_trading_engine_v323.approve_confirmation(confirm_id)


@app.post("/api/live/confirm-queue/{confirm_id}/reject")
def live_confirm_reject(confirm_id: str) -> dict:
    return live_trading_engine_v323.reject_confirmation(confirm_id)


@app.get("/api/watchlists")
def watchlists_v323() -> dict:
    data = watchlist_service.list()
    return {"ok": True, "data": [{"id": "default", "name": "默认自选池", **data}]}


@app.post("/api/watchlists")
def watchlists_create_v323(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = payload.get("symbols") or payload.get("watchlist") or []
    data = watchlist_service.set(symbols)
    return {"ok": True, "data": {"id": "default", "name": str(payload.get("name") or "默认自选池"), **data}}


@app.put("/api/watchlists/{watchlist_id}")
def watchlists_update_v323(watchlist_id: str, payload: dict = Body(default_factory=dict)) -> dict:
    symbols = payload.get("symbols") or payload.get("watchlist") or []
    data = watchlist_service.set(symbols)
    return {"ok": True, "data": {"id": watchlist_id, "name": str(payload.get("name") or "默认自选池"), **data}}


@app.delete("/api/watchlists/{watchlist_id}")
def watchlists_delete_v323(watchlist_id: str) -> dict:
    data = watchlist_service.set([])
    return {"ok": True, "data": {"id": watchlist_id, "deleted": True, **data}}


@app.get("/api/screener/session/latest")
def screener_session_latest_v323() -> dict:
    latest = cache_state_service.latest("screener_snapshot")
    return {"ok": bool(latest.data), "data": latest.data, "cache_status": latest.cache_status, "missing_reason": "" if latest.data else "暂无筛选快照缓存"}


@app.get("/api/screener/session/{session_id}")
def screener_session_get_v323(session_id: str) -> dict:
    snap = cache_state_service.get("screener_snapshot", session_id)
    return {"ok": bool(snap.data), "data": snap.data, "cache_status": snap.cache_status, "errors": [] if snap.data else ["session_id not found"]}


@app.post("/api/screener/session/save")
def screener_session_save_v323(payload: dict = Body(default_factory=dict)) -> dict:
    snapshot_id = str(payload.get("snapshot_id") or _make_snapshot_id("screener", len(payload.get("results") or [])))
    cache_state_service.put("screener_snapshot", snapshot_id, payload, ttl_seconds=1800, source="api/screener/session/save")
    return {"ok": True, "snapshot_id": snapshot_id, "data": payload}


@app.post("/api/screener/add-to-paper")
def screener_add_to_paper_v323(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _symbols_from_payload(payload)
    watchlist_service.add(symbols)
    session = realtime_paper_engine_v323.start_session({"symbols": symbols, "strategy_family": payload.get("strategy_family") or "hybrid"})
    return {"ok": True, "symbols": symbols, "session": session}


@app.post("/api/screener/add-to-live-watch")
def screener_add_to_live_watch_v323(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _symbols_from_payload(payload)
    watchlist_service.add(symbols)
    for sym in symbols:
        trading_store_v323.put("audit_events", {"event_type": "live_watch_added", "symbol": sym, "source": "screener"}, mode="live", symbol=sym)
    return {"ok": True, "symbols": symbols, "message": "已加入真实交易观察池；真实交易默认关闭，不会自动下单。"}


@app.get("/api/chart/{symbol}/markers")
def chart_markers_v323(symbol: str, mode: str = "", limit: int = 300) -> dict:
    rows = chart_annotation_service_v323.list_markers(symbol, mode=mode or None, limit=max(1, min(int(limit or 300), 1000)))
    if not rows:
        stored = trading_store_v323.list("chart_markers", mode=mode, symbol=symbol, limit=limit)
        rows = stored
    return {"ok": True, "symbol": symbol, "mode": mode, "data": rows, "count": len(rows)}


@app.post("/api/chart/{symbol}/markers/rebuild")
def chart_markers_rebuild_v323(symbol: str, payload: dict = Body(default_factory=dict)) -> dict:
    rows = chart_annotation_service_v323.rebuild(
        symbol,
        orders=list(payload.get("orders") or trading_store_v323.list("orders", symbol=symbol, limit=1000)),
        fills=list(payload.get("fills") or trading_store_v323.list("fills", symbol=symbol, limit=1000)),
        mode=str(payload.get("mode") or "backtest"),
    )
    for row in rows:
        trading_store_v323.put("chart_markers", row, mode=str(row.get("mode") or ""), symbol=symbol, session_id=str(row.get("session_id") or ""), record_id=str(row.get("marker_id") or ""))
    return {"ok": True, "symbol": symbol, "data": rows, "count": len(rows)}


@app.get("/api/trading-records")
def trading_records_v323(mode: str = "", symbol: str = "", status: str = "", limit: int = 200) -> dict:
    tables = ["signals", "score_provenance", "risk_checks", "orders", "fills", "positions", "account_snapshots", "chart_markers", "audit_events", "manual_confirmations"]
    rows = []
    for table in tables:
        for item in trading_store_v323.list(table, mode=mode, symbol=symbol, limit=max(1, min(int(limit or 200), 1000))):
            if status and str(item.get("status") or item.get("event_type") or "") != status:
                continue
            rows.append(_enrich_trading_record_row(table, item))
    rows.sort(key=lambda x: str(x.get("created_at") or x.get("timestamp") or ""), reverse=True)
    return {"ok": True, "data": rows[: max(1, min(int(limit or 200), 1000))], "count": len(rows)}


@app.get("/api/trading-records/{record_id}")
def trading_record_detail_v323(record_id: str) -> dict:
    for table in ["signals", "score_provenance", "risk_checks", "orders", "fills", "positions", "account_snapshots", "broker_raw_responses", "chart_markers", "audit_events", "data_source_status", "manual_confirmations"]:
        row = next((x for x in trading_store_v323.list(table, limit=1000) if x.get("id") == record_id or x.get("order_id") == record_id or x.get("fill_id") == record_id or x.get("provenance_id") == record_id), None)
        if row:
            return {"ok": True, "table": table, "data": row}
    return {"ok": False, "errors": ["record_id not found"], "data": None}


@app.get("/api/trading-records/export")
def trading_records_export_v323(mode: str = "", symbol: str = "") -> dict:
    return trading_records_v323(mode=mode, symbol=symbol, limit=1000)


@app.get("/api/data-center/status")
def data_center_status_v323() -> dict:
    cache = cache_state_service.overview()
    return {
        "ok": True,
        "market_session": market_session_status(),
        "cache": cache,
        "trading_store": trading_store_v323.stats(),
        "pit_store": pit_store_v323.stats(),
        "sources": source_registry_v323.list(),
        "broker": live_trading_engine_v323.status()["broker"],
        "disclaimer": "没有真实数据时系统显示缺失/过期/不支持，不伪造。",
    }


@app.get("/api/data-center/missing-fields")
def data_center_missing_fields_v323() -> dict:
    records = []
    for table in ["data_source_status", "score_provenance"]:
        records.extend({"table": table, **x} for x in trading_store_v323.list(table, limit=500))
    missing = []
    for row in records:
        missing.extend(row.get("missing_reasons") or row.get("missing_data") or [])
    return {"ok": True, "data": list(dict.fromkeys(str(x) for x in missing)), "count": len(missing)}


@app.get("/api/data-center/source-errors")
def data_center_source_errors_v323() -> dict:
    warnings = source_registry_service.warnings() if hasattr(source_registry_service, "warnings") else []
    providers = provider_warnings().get("data") if "provider_warnings" in globals() else []
    return {"ok": True, "data": {"registry": source_registry_v323.list(), "warnings": warnings, "provider_warnings": providers, "live_broker": live_trading_engine_v323.status()["broker"]}}


@app.post("/api/data-center/refresh")
def data_center_refresh_v323(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _symbols_from_payload(payload) or watchlist_service.list().get("symbols", [])
    refreshed = []
    for sym in symbols[:20]:
        try:
            q = service.get_quote(sym, force_refresh=bool(payload.get("force")))
            qdict = q.to_dict() if hasattr(q, "to_dict") else q.__dict__
            snap = build_quote_snapshot(sym, qdict, source_id=str(qdict.get("source") or "quote"))
            trading_store_v323.put("data_source_status", snap.source.to_dict(), mode="data", symbol=sym, record_id=f"quote-{sym}-{snap.source.raw_hash}")
            refreshed.append(sym)
        except Exception as exc:
            trading_store_v323.put("data_source_status", {"symbol": sym, "quality_status": "error", "missing_reasons": [str(exc)[:200]]}, mode="data", symbol=sym)
    return {"ok": True, "refreshed": refreshed, "count": len(refreshed)}


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


@app.get("/api/background/status")
def background_status() -> dict:
    return background_cache_service.status()


@app.post("/api/background/refresh/watchlist")
def background_refresh_watchlist(symbols: str | None = None, force: bool = False, limit: int = 40) -> dict:
    symbol_list = _parse_symbol_text(symbols) if symbols else None

    def _loader(sym: str):
        return _enrich_quote_real(sym, force=force)

    return background_cache_service.refresh_watchlist_quotes(symbol_list, _loader, limit=limit)


@app.post("/api/background/refresh/screener")
def background_refresh_screener() -> dict:
    cached = cache_state_service.latest_screener_snapshot()
    data = cached.data or {}
    return background_cache_service.mark_refresh(
        "screener_snapshot",
        cache_status=cached.cache_status,
        snapshot_id=data.get("snapshot_id"),
        result_count=len(data.get("results") or data.get("data") or []),
    )


@app.post("/api/background/refresh/kline/{symbol}")
def background_refresh_kline(symbol: str, frame: str = "1d", adjust: str = "none", limit: int = 260, force: bool = False) -> dict:
    payload = _safe_kline_payload(symbol, frame=frame, adjust=adjust, limit=limit, force=force)
    return background_cache_service.mark_refresh(
        "kline_cache",
        symbol=symbol,
        frame=frame,
        adjust=adjust,
        payload_ok=payload.get("ok"),
        cache_status=payload.get("cache_status"),
        stale_cache_used=payload.get("stale_cache_used", False),
    )


@app.post("/api/background/refresh/info/{symbol}")
def background_refresh_info(symbol: str, name: str | None = None, force: bool = False, deep_refresh: bool = False) -> dict:
    latest = cache_state_service.latest_info_snapshot(symbol)
    if latest.data and not force and not deep_refresh:
        return background_cache_service.mark_refresh(
            "info_snapshot",
            symbol=symbol,
            snapshot_id=latest.data.get("snapshot_id"),
            cache_status=latest.cache_status,
            used_snapshot=True,
        )
    data = info_analyze(symbol, name=name, force=force, deep_refresh=deep_refresh)
    return background_cache_service.mark_refresh(
        "info_snapshot",
        symbol=symbol,
        snapshot_id=data.get("snapshot_id"),
        cache_status=data.get("cache_status"),
        used_snapshot=data.get("used_snapshot", False),
    )



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
    if book is None:
        try:
            q = service.get_quote(symbol, force_refresh=bool(force and allow_external))
            if getattr(q, "order_ratio", None) is not None or getattr(q, "order_diff", None) is not None:
                book = OrderBook(
                    symbol=symbol,
                    ts=datetime.now(),
                    asks=[],
                    bids=[],
                    order_ratio=getattr(q, "order_ratio", None),
                    order_diff=getattr(q, "order_diff", None),
                    source=f"{getattr(q, 'source', 'quote')}:quote-metrics",
                )
                note = "公开行情源未返回五档价量，仅返回委比/委差；五档档位需要等待盘口源可用。"
        except Exception:
            pass
    if not allow_external:
        status = str(session.get("status") or "")
        label = str(session.get("label") or "")
        if status == "lunch" or "午" in label:
            note = note or "午休无盘口"
        elif status == "closed" or "休" in label:
            note = note or "休市无盘口"
        else:
            note = note or "非交易时段不适用"
    elif not book:
        note = note or "公开行情源未返回五档盘口；普通免费源通常没有稳定 Level-2 深度，交易时段会继续尝试。"
    elif not ((book.asks or []) and (book.bids or [])):
        note = note or "盘口字段不完整；仅展示公开源实际返回的档位。"
    behavior = orderbook_behavior_service.analyze(
        book,
        symbol=symbol,
        skipped_external=not allow_external,
        note=note,
    )
    if book:
        payload = book.to_dict()
    else:
        payload = {
            "symbol": symbol,
            "ts": datetime.now().isoformat(timespec="seconds"),
            "asks": [],
            "bids": [],
            "order_ratio": None,
            "order_diff": None,
            "source": "none",
        }
    payload["behavior"] = behavior
    return {
        "ok": True,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "symbol": symbol,
        "market_status": session.get("status"),
        "market_label": session.get("label"),
        "skipped_external": not allow_external,
        "note": note,
        "data": payload,
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


def _latest_screener_rows() -> list[dict]:
    try:
        cached = cache_state_service.latest_screener_snapshot()
        data = cached.data or {}
        rows = data.get("results") or data.get("data") or data.get("snapshot", {}).get("results") or []
        return [dict(x) for x in rows if isinstance(x, dict)]
    except Exception:
        return []


def _screener_rows_from_payload(payload: dict | None = None) -> list[dict]:
    payload = payload or {}
    rows = payload.get("rows") or payload.get("data") or payload.get("results")
    if isinstance(rows, list):
        return [dict(x) for x in rows if isinstance(x, dict)]
    return _latest_screener_rows()


def _screener_symbols_from_payload(payload: dict | None = None) -> list[str]:
    payload = payload or {}
    raw = payload.get("symbols") or payload.get("watchlist") or payload.get("symbol") or ""
    symbols: list[str] = []
    if isinstance(raw, list):
        symbols = [str(x).strip() for x in raw if str(x).strip()]
    elif isinstance(raw, str):
        symbols = _parse_symbol_text(raw)
    for row in _screener_rows_from_payload(payload):
        sym = str(row.get("symbol") or "").strip()
        if sym and sym not in symbols:
            symbols.append(sym)
    return symbols[: max(1, min(int(payload.get("limit") or 30), 200))]


def _screener_row_for_signal(symbol: str, payload: dict | None = None) -> dict:
    payload = payload or {}
    if isinstance(payload.get("row"), dict):
        row = dict(payload["row"])
        row.setdefault("symbol", symbol)
        return row
    for row in _screener_rows_from_payload(payload):
        if str(row.get("symbol") or "").strip() == str(symbol).strip():
            return row
    try:
        q = service.get_quote(symbol, force_refresh=bool(payload.get("force")))
        return {
            "symbol": getattr(q, "symbol", symbol),
            "name": getattr(q, "name", symbol),
            "last": getattr(q, "last", None),
            "amount": getattr(q, "amount", None),
            "change_pct": getattr(q, "change_pct", None),
            "turnover": getattr(q, "turnover", None),
            "volume_ratio": getattr(q, "volume_ratio", None),
            "total_score": payload.get("score", 50),
        }
    except Exception:
        return {"symbol": symbol, "total_score": payload.get("score", 50)}


def _screener_anomaly_features(row: dict) -> dict:
    risk_items = row.get("risk_warnings") or row.get("risk_tags") or row.get("risk_flags") or []
    if not isinstance(risk_items, list):
        risk_items = [risk_items]
    return {
        "high_position_pct": _safe_float(row.get("pos250"), _safe_float(row.get("pos20"), 0.0)),
        "volume_ratio": _safe_float(row.get("volume_ratio"), 0.0),
        "change_pct": _safe_float(row.get("change_pct"), 0.0),
        "turnover": _safe_float(row.get("turnover"), 0.0),
        "ma20_deviation_pct": _safe_float(row.get("ma20_deviation_pct"), 0.0),
        "vwap_distance_pct": _safe_float(row.get("vwap_distance_pct"), 0.0),
        "negative_news": "负面" in " ".join(str(x) for x in risk_items),
        "sector_score": _safe_float(row.get("sector_score"), 50.0),
        "amount_change_pct": _safe_float(row.get("amount_change_pct"), 0.0),
        "stale_data": bool(row.get("cache_status", {}).get("stale")) if isinstance(row.get("cache_status"), dict) else False,
    }


def _screener_signal_preview(symbol: str, payload: dict | None = None) -> dict:
    row = _screener_row_for_signal(symbol, payload)
    anomaly = realtime_paper_engine_v321.anomaly_guard.check(_screener_anomaly_features(row))
    now = datetime.now()
    freshness = realtime_paper_engine_v321.freshness_guard.check(
        {
            "quote": now,
            "intraday": now,
            "news": now,
            "technical": now,
            "company_profile": now,
        },
        now=now,
        missing_fields=list(row.get("missing_data_hints") or row.get("missing_data") or []),
    )
    signal = realtime_paper_engine_v321.signal_fusion.fuse(
        symbol=symbol,
        horizon=str((payload or {}).get("horizon") or "swing"),
        fundamental_score=_safe_float(row.get("fundamental_score"), _safe_float(row.get("manual_review_score"), 55.0)),
        technical_score=_safe_float(row.get("technical_score"), _safe_float(row.get("total_score"), 50.0)),
        information_score=_safe_float(row.get("information_score"), _safe_float(row.get("info_score"), 50.0)),
        market_score=_safe_float(row.get("market_score"), _safe_float(row.get("market_mood_score"), 50.0)),
        anomaly_score=anomaly.anomaly_score,
        anomaly_action=anomaly.action_suggestion,
        evidence=list(row.get("tags") or row.get("upgrade_reasons") or row.get("hit_tags") or ["来自当前筛选快照"]),
        data_freshness=freshness.to_dict(),
        missing_data=list(row.get("missing_data_hints") or row.get("missing_data") or []),
        now=now,
    )
    return {"ok": True, "symbol": symbol, "row": row, "signal": signal.to_dict(), "anomaly": anomaly.to_dict(), "freshness": freshness.to_dict(), "paper_only": True}


@app.post("/api/screener/realtime-paper/add")
def screener_realtime_paper_add(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _screener_symbols_from_payload(payload)
    watchlist = watchlist_service.add(symbols)
    return {"ok": True, "message": "已加入实时模拟池/监控列表", "symbols": symbols, "watchlist": watchlist, "paper_only": True}


@app.post("/api/screener/realtime-paper/start")
def screener_realtime_paper_start(payload: dict = Body(default_factory=dict)) -> dict:
    symbols = _screener_symbols_from_payload(payload)
    if not symbols:
        return {"ok": False, "message": "没有可用于实时模拟的筛选标的"}
    watchlist_service.add(symbols)
    start_payload = {
        "symbols": symbols,
        "initial_cash": payload.get("initial_cash", 100000),
        "interval_seconds": payload.get("interval_seconds", 15),
        "horizon": payload.get("horizon", "intraday_paper"),
        "strategy": payload.get("strategy", "three_dimension_score"),
    }
    data = realtime_paper_engine_v321.start(start_payload)
    data["symbols"] = symbols
    data["message"] = "已用当前筛选结果启动盘中实时模拟"
    return data


@app.get("/api/screener/signal-preview/{symbol}")
def screener_signal_preview_get(symbol: str, horizon: str = "swing") -> dict:
    return _screener_signal_preview(symbol, {"horizon": horizon})


@app.post("/api/screener/signal-preview/{symbol}")
def screener_signal_preview_post(symbol: str, payload: dict = Body(default_factory=dict)) -> dict:
    return _screener_signal_preview(symbol, payload)


@app.get("/api/screener/anomaly-preview/{symbol}")
def screener_anomaly_preview_get(symbol: str) -> dict:
    row = _screener_row_for_signal(symbol)
    return {"ok": True, "symbol": symbol, "row": row, "anomaly": realtime_paper_engine_v321.anomaly_guard.check(_screener_anomaly_features(row)).to_dict()}


@app.post("/api/screener/anomaly-preview/{symbol}")
def screener_anomaly_preview_post(symbol: str, payload: dict = Body(default_factory=dict)) -> dict:
    row = _screener_row_for_signal(symbol, payload)
    return {"ok": True, "symbol": symbol, "row": row, "anomaly": realtime_paper_engine_v321.anomaly_guard.check(_screener_anomaly_features(row)).to_dict()}


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


def _global_impact_fields(text: str, category: str = "", dimension: str = "", existing_tags: Any | None = None) -> dict:
    """Map global flash/news text to transparent impact hints.

    These hints are not trading signals. They only explain which assets/sectors a
    macro or commodity event may touch, so the UI can show why the information
    panel matters.
    """
    raw_tags = existing_tags if isinstance(existing_tags, list) else []
    sectors: list[str] = []
    assets: list[str] = []
    evidence: list[str] = []

    def add_many(dst: list[str], values: list[str]) -> None:
        for value in values:
            v = str(value or "").strip()
            if v and v not in dst:
                dst.append(v)

    def matched(words: list[str], label: str) -> bool:
        ok = any(w in t for w in words)
        if ok and label not in evidence:
            evidence.append(label)
        return ok

    t = f"{text} {category} {dimension}"
    macro_hit = False
    if matched(["非农", "就业", "失业率", "初请", "ADP", "CPI", "PPI", "PMI", "ISM", "FOMC", "美联储", "降息", "加息", "通胀", "利率决议"], "宏观/利率"):
        macro_hit = True
        add_many(sectors, ["银行", "券商", "成长股估值", "出口链"])
        add_many(assets, ["A股指数", "美元指数", "美债收益率", "人民币汇率"])
    if matched(["美元", "美债", "汇率", "外汇", "人民币", "日元", "欧元"], "汇率/美债"):
        macro_hit = True
        add_many(sectors, ["出口链", "航空运输", "贵金属"])
        add_many(assets, ["美元指数", "人民币汇率", "黄金"])
    if matched(["原油", "OPEC", "石油", "布伦特", "WTI", "能源", "天然气", "燃油"], "能源商品"):
        macro_hit = True
        add_many(sectors, ["石油石化", "煤化工", "航空运输", "新能源"])
        add_many(assets, ["原油", "能源化工"])
    if matched(["黄金", "白银", "贵金属", "避险"], "贵金属/避险"):
        macro_hit = True
        add_many(sectors, ["贵金属", "有色金属"])
        add_many(assets, ["黄金", "白银", "美元指数"])
    if matched(["铜", "铝", "镍", "锂", "有色", "工业金属", "商品", "期货", "黑色系", "焦煤", "焦炭", "铁矿"], "工业品/期货"):
        macro_hit = True
        add_many(sectors, ["有色金属", "钢铁", "煤炭", "化工", "制造成本"])
        add_many(assets, ["大宗商品", "工业品"])
    if matched(["地缘", "冲突", "制裁", "战争", "袭击", "空袭", "无人机袭击", "导弹", "以色列", "加沙", "巴勒斯坦", "伊朗", "黎巴嫩", "叙利亚", "乌克兰", "俄罗斯", "北约", "中东", "红海"], "地缘风险"):
        macro_hit = True
        add_many(sectors, ["军工", "能源", "航运", "避险资产"])
        add_many(assets, ["原油", "黄金", "航运"])
    if matched(["USDA", "农业部", "大豆", "玉米", "小麦", "棉花", "农作物", "干旱", "洪水", "厄尔尼诺", "拉尼娜"], "农业/天气"):
        macro_hit = True
        add_many(sectors, ["农业种植", "饲料养殖", "农产品加工", "化肥农药"])
        add_many(assets, ["农产品期货", "大豆", "玉米", "棉花"])
    if matched(["AI", "芯片", "半导体", "算力", "光伏", "储能", "新能源汽车"], "科技/新能源"):
        add_many(sectors, ["半导体/算力", "新能源", "光伏储能"])
        add_many(assets, ["成长股", "科技主题"])
    if not macro_hit:
        add_many(sectors, [str(x) for x in raw_tags])
        try:
            inferred_tags = news_service._industry_tags(text)  # noqa: SLF001
        except Exception:
            inferred_tags = []
        add_many(sectors, [str(x) for x in inferred_tags])

    targets = (sectors + assets)[:10]
    note = "影响提示：仅解释宏观/商品/信息面对板块和资产的可能传导，不直接等于买卖建议。"
    if targets:
        note = f"影响提示：可能影响 {', '.join(targets[:6])}；仅作信息面风险观察。"
    return {
        "affected_sectors": sectors[:8],
        "affected_assets": assets[:8],
        "impact_targets": targets,
        "impact_note": note,
        "impact_evidence": evidence[:6],
    }


def _global_stream_items(items: list[dict]) -> list[dict]:
    stream: list[dict] = []
    for idx, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or item.get("source_name") or item.get("media") or "全球信息源")
        title = str(item.get("title") or item.get("summary") or item.get("content") or "").strip()
        if not title:
            continue
        published_at = (
            item.get("published_at")
            or item.get("published_at_norm")
            or item.get("date_display")
            or item.get("publish_time")
            or item.get("event_time")
            or item.get("crawl_time")
            or ""
        )
        url = str(item.get("url") or "")
        category = item.get("category") or "全球要闻"
        dimension = item.get("message_dimension") or item.get("dimension") or "全球快讯"
        impact_scope = item.get("impact_scope") or ""
        impact = _global_impact_fields(
            f"{title} {item.get('summary') or ''} {impact_scope}",
            str(category),
            str(dimension),
            item.get("industry_tags") or item.get("affected_sectors"),
        )
        stream.append(
            {
                "rank": idx + 1,
                "title": title[:220],
                "summary": str(item.get("summary") or title)[:360],
                "source": source,
                "source_ref": url,
                "published_at": published_at,
                "category": category,
                "message_dimension": dimension,
                "impact_scope": impact_scope,
                **impact,
                "sentiment_label": item.get("sentiment_label") or "",
                "event_label": item.get("event_label") or "",
                "is_jin10": ("金十" in source) or ("jin10" in url.lower()),
                "quality_status": "ok",
            }
        )
    return stream


def _global_stream_items_from_rows(rows: list[dict], fallback_source: str = "全球快讯") -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for idx, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        source = str(row.get("_source_name") or row.get("source") or row.get("文章来源") or row.get("媒体") or fallback_source)
        title = str(row.get("标题") or row.get("新闻标题") or row.get("title") or row.get("内容") or row.get("content") or "").strip()
        summary = str(row.get("摘要") or row.get("summary") or row.get("内容") or row.get("content") or title).strip()
        if not title and summary:
            title = summary[:140]
        if not title:
            continue
        key = re.sub(r"\W+", "", f"{source}:{title}")[:120]
        if key in seen:
            continue
        seen.add(key)
        published_at = str(row.get("发布时间") or row.get("发布日期") or row.get("时间") or row.get("datetime") or row.get("pub_time") or row.get("发布于") or "")
        url = str(row.get("链接") or row.get("新闻链接") or row.get("url") or row.get("_source_page") or "")
        category_hint = str(row.get("_category") or "")
        text = f"{title} {summary} {category_hint}"
        try:
            dimension = news_service._global_message_dimension(text, source, category_hint)  # noqa: SLF001
            category = news_service._global_market_category(text, category_hint)  # noqa: SLF001
            impact_scope = news_service._infer_impact_scope(text, "macro", source)  # noqa: SLF001
        except Exception:
            dimension = "全球快讯"
            category = category_hint or "全球要闻"
            impact_scope = ""
        impact = _global_impact_fields(text, str(category), str(dimension), row.get("industry_tags") or row.get("_industry_tags"))
        out.append(
            {
                "rank": idx + 1,
                "title": title[:220],
                "summary": summary[:360],
                "source": source,
                "source_ref": url,
                "source_api": row.get("_source_api") or row.get("source_api") or "",
                "source_page": row.get("_source_page") or row.get("source_page") or "",
                "published_at": published_at,
                "category": category,
                "message_dimension": dimension,
                "impact_scope": impact_scope,
                **impact,
                "sentiment_label": "",
                "event_label": "",
                "is_jin10": ("金十" in source) or ("jin10" in url.lower()),
                "quality_status": "ok",
            }
        )
    return out


def _dedupe_stream_items(items: list[dict], limit: int) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("summary") or "").strip()
        if not title:
            continue
        source = str(item.get("source") or "")
        key = re.sub(r"\W+", "", f"{source}:{title}")[:140]
        if key in seen:
            continue
        seen.add(key)
        next_item = dict(item)
        next_item["rank"] = len(out) + 1
        out.append(next_item)
        if len(out) >= limit:
            break
    return out


def _read_jin10_realtime_stream(limit: int = 80, *, force: bool = False) -> tuple[dict, dict]:
    """Read Jin10/Jin10 Futures flash as a first-class realtime stream.

    The Jin10 futures page is a dynamic front-end. We avoid embedding or scraping
    search pages; the primary source is Jin10's public flash JSON endpoint, with
    qihuo/xnews HTML title extraction as a transparent fallback.
    """
    limit = max(20, min(int(limit or 80), 160))
    key = f"jin10:{limit}"
    ttl_seconds = 20
    if not force:
        cached = cache_state_service.get("global_news_cache", key, allow_stale=False, ttl_seconds=ttl_seconds)
        if cached.data and cached.data.get("items"):
            payload = dict(cached.data)
            payload["stream_mode"] = payload.get("stream_mode") or "jin10_cache"
            return payload, cached.cache_status
    try:
        rows = news_service._search_jin10_flash(limit=limit)  # noqa: SLF001
        items = _global_stream_items_from_rows(rows, "金十/金十期货快讯")[:limit]
        payload = {
            "items": items,
            "raw_count": len(items),
            "sources_status": [
                {
                    "source": "金十/金十期货直连",
                    "count": len(items),
                    "status": "ok" if items else "无公开数据或页面结构变化",
                    "source_api": "https://flash-api.jin10.com/get_flash_list",
                    "source_page": "https://qihuo.jin10.com/",
                }
            ],
            "sources_used": sorted({str(x.get("source") or "") for x in items if x.get("source")}),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stream_mode": "jin10_realtime_direct" if items else "jin10_empty",
            "cache_info": {"hit": False, "ttl_seconds": ttl_seconds, "source": "jin10_realtime"},
            "refresh_seconds": ttl_seconds,
            "missing_reason": "" if items else "金十公开快讯接口和页面摘要暂未返回有效条目；不会伪造新闻。",
            "source_candidates": ["https://flash-api.jin10.com/get_flash_list", "https://qihuo.jin10.com/", "https://xnews.jin10.com/"],
        }
        status = cache_state_service.put("global_news_cache", key, payload, ttl_seconds=ttl_seconds, source="jin10_realtime")
        return payload, status
    except Exception as exc:
        latest = cache_state_service.get("global_news_cache", key, allow_stale=True)
        if latest.data and latest.data.get("items"):
            payload = dict(latest.data)
            payload["stream_mode"] = "jin10_stale_cache_fallback"
            payload["missing_reason"] = f"本轮金十直连失败，保留上一轮真实缓存：{str(exc)[:160]}"
            payload["refresh_seconds"] = ttl_seconds
            return payload, latest.cache_status
        return {
            "items": [],
            "raw_count": 0,
            "sources_status": [{"source": "金十/金十期货直连", "status": "error", "count": 0, "skipped_reason": str(exc)[:180]}],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stream_mode": "jin10_error",
            "refresh_seconds": ttl_seconds,
            "missing_reason": f"金十直连刷新失败：{str(exc)[:180]}",
            "source_candidates": ["https://flash-api.jin10.com/get_flash_list", "https://qihuo.jin10.com/", "https://xnews.jin10.com/"],
        }, cache_state_service.status("error", key=key, ttl_seconds=ttl_seconds, source="jin10_realtime", error=str(exc)[:180])


def _fetch_global_stream_fast(limit: int = 80, *, force: bool = False) -> tuple[list[dict], list[dict]]:
    limit = max(20, min(int(limit or 80), 160))
    jobs = [
        ("金十/金十期货快讯", lambda: news_service._search_jin10_flash(limit=min(limit, 100))),  # noqa: SLF001
        ("东方财富快讯:全球", lambda: news_service._search_eastmoney_kuaixun("https://kuaixun.eastmoney.com/qqgs.html", "全球", limit=min(limit, 50))),  # noqa: SLF001
        ("东方财富快讯:商品", lambda: news_service._search_eastmoney_kuaixun("https://kuaixun.eastmoney.com/jjsj.html", "商品", limit=min(limit, 50))),  # noqa: SLF001
    ]
    rows: list[dict] = []
    status: list[dict] = []
    executor = ThreadPoolExecutor(max_workers=len(jobs))
    futures = [(name, executor.submit(fn)) for name, fn in jobs]
    # 金十公开接口通常需要连续尝试 JSON + 页面兜底，4 秒左右容易刚好卡在边界。
    # 这里仍是快路径，但给首次加载留足时间，避免把“短暂超时”写成空快照。
    deadline = time_module.monotonic() + (8.0 if force else 6.5)
    try:
        for name, future in futures:
            timeout = max(0.05, deadline - time_module.monotonic())
            try:
                got = list(future.result(timeout=timeout) or [])
                rows.extend(got)
                status.append({"source": name, "count": len(got), "status": "ok" if got else "无公开数据或页面结构变化"})
            except Exception as exc:
                status_text = str(exc)[:160] or exc.__class__.__name__
                status.append({"source": name, "count": 0, "status": status_text, "skipped_reason": "fast_stream_timeout_or_error"})
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    return _global_stream_items_from_rows(rows, "全球快讯")[:limit], status


def _read_global_news_stream(limit: int = 80, *, force: bool = False, live: bool = True) -> tuple[dict, dict]:
    limit = max(20, min(int(limit or 80), 160))
    key = f"stream:{limit}"
    if not force:
        cached = cache_state_service.get("global_news_cache", key, allow_stale=False, ttl_seconds=45)
        if cached.data and cached.data.get("items"):
            return dict(cached.data), cached.cache_status
        latest = cache_state_service.latest("global_news_cache", allow_stale=True)
        if latest.data and latest.data.get("items") and not live:
            payload = {
                "items": _global_stream_items(list(latest.data.get("items") or [])[:limit]),
                "raw_count": len(latest.data.get("items") or []),
                "sources_status": latest.data.get("source_logs") or latest.data.get("sources_status") or [],
                "updated_at": latest.data.get("updated_at") or latest.data.get("created_at"),
                "stream_mode": "cache_latest",
                "refresh_seconds": 35,
                "missing_reason": "",
            }
            return payload, latest.cache_status
    if not live and not force:
        return {
            "items": [],
            "raw_count": 0,
            "sources_status": [{"source": "global_news_cache", "status": "miss_live_disabled", "count": 0}],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stream_mode": "cache_only",
            "refresh_seconds": 35,
            "missing_reason": "当前没有全球快讯缓存，且本次请求关闭了联网刷新。",
        }, cache_state_service.status("miss", key=key, ttl_seconds=45, source="global_news_stream", error="cache miss and live=false")
    try:
        items, source_status = _fetch_global_stream_fast(limit=limit, force=force)
        if not items:
            latest = cache_state_service.latest("global_news_cache", allow_stale=True)
            if latest.data and latest.data.get("items"):
                fallback_items = _global_stream_items(list(latest.data.get("items") or [])[:limit])
                if not fallback_items:
                    fallback_items = [x for x in latest.data.get("items", []) if isinstance(x, dict)][:limit]
                if fallback_items:
                    payload = {
                        "items": fallback_items,
                        "raw_count": len(fallback_items),
                        "sources_status": source_status + [{"source": "global_news_cache", "count": len(fallback_items), "status": "stale_fallback"}],
                        "sources_used": sorted({str(x.get("source") or "") for x in fallback_items if x.get("source")}),
                        "updated_at": datetime.now().isoformat(timespec="seconds"),
                        "stream_mode": "stale_cache_fallback",
                        "cache_info": {"hit": True, "fast_stream": True, "fallback": True, "reason": "live_fast_stream_empty"},
                        "refresh_seconds": 35,
                        "missing_reason": "本轮实时快讯源暂未返回，已保留上一轮真实快讯缓存。",
                        "source_candidates": ["金十/金十期货快讯", "东方财富快讯", "华尔街见闻快讯", "财联社电报", "新浪财经7x24"],
                    }
                    return payload, latest.cache_status
        payload = {
            "items": items,
            "raw_count": len(items),
            "sources_status": source_status,
            "sources_used": sorted({x.get("source", "") for x in items if x.get("source")}),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stream_mode": "fast_live_fetch",
            "cache_info": {"hit": False, "fast_stream": True, "ttl_seconds": 45},
            "refresh_seconds": 35,
            "missing_reason": "" if items else "全球快讯源暂未返回有效条目；不会伪造新闻。",
            "source_candidates": ["金十/金十期货快讯", "东方财富快讯", "华尔街见闻快讯", "财联社电报", "新浪财经7x24"],
        }
        status = cache_state_service.put("global_news_cache", key, payload, ttl_seconds=45, source="news_global_stream")
        return payload, status
    except Exception as exc:
        return {
            "items": [],
            "raw_count": 0,
            "sources_status": [{"source": "global_news_stream", "status": "error", "count": 0, "skipped_reason": str(exc)[:180]}],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stream_mode": "error",
            "refresh_seconds": 35,
            "missing_reason": f"全球快讯联网刷新失败：{str(exc)[:180]}",
        }, cache_state_service.status("error", key=key, ttl_seconds=45, source="global_news_stream", error=str(exc)[:180])


@app.get("/api/news/jin10/realtime")
def jin10_realtime_news(limit: int = 80, force: bool = False) -> dict:
    data, cache_status = _read_jin10_realtime_stream(limit=limit, force=force)
    return {
        "ok": True,
        "data": data,
        "items": data.get("items", []),
        "cache_status": cache_status,
        "refresh_seconds": data.get("refresh_seconds", 20),
        "source_policy": "金十期货/金十数据直连优先；公开接口不可用时仅使用页面摘要兜底，不抓搜索结果页，不伪造新闻。",
        "disclaimer": "金十快讯只展示真实可追溯来源；抓不到时显示缺失/错误，不构成投资建议。",
    }


@app.get("/api/news/global/stream")
def global_news_stream(limit: int = 80, force: bool = False, live: bool = True) -> dict:
    data, cache_status = _read_global_news_stream(limit=limit, force=force, live=live)
    return {
        "ok": True,
        "data": data,
        "items": data.get("items", []),
        "cache_status": cache_status,
        "refresh_seconds": data.get("refresh_seconds", 35),
        "disclaimer": "全球快讯只展示真实可追溯来源；抓不到时显示缺失/错误，不伪造新闻，不构成投资建议。",
    }


def _agent_score_rows(symbols: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    latest_rows = score_history_service.latest(limit=1000)
    for row in latest_rows or []:
        sym = str(row.get("symbol") or "").strip()
        if sym and sym in symbols and sym not in out:
            out[sym] = row
    for row in score_provenance_memory_v323.values():
        sym = str(row.get("symbol") or "").strip()
        if sym in symbols:
            score = row.get("final_trade_score") or row.get("final_score") or row.get("total_score")
            out[sym] = {
                **out.get(sym, {}),
                "symbol": sym,
                "name": row.get("name") or out.get(sym, {}).get("name") or sym,
                "total_score": score,
                "grade": row.get("action") or out.get(sym, {}).get("grade") or "",
                "reason": row.get("explanation") or row.get("summary") or out.get(sym, {}).get("reason") or "",
                "updated_at": row.get("decision_time") or out.get(sym, {}).get("updated_at") or "",
                "risk_flags": row.get("missing_data") or row.get("risk_flags") or out.get(sym, {}).get("risk_flags") or [],
                "tags": row.get("gates") or out.get(sym, {}).get("tags") or [],
            }
    return out


def _agent_symbol_decisions(symbols: list[str], scores: dict[str, dict], config: dict, safety: dict) -> list[dict]:
    decisions: list[dict] = []
    signal_map = dict(config.get("screener_signal_map") or {})
    for sym in symbols[:30]:
        row = scores.get(sym) or {}
        profile = signal_map.get(sym) or {}
        score = _as_float(row.get("total_score") or row.get("final_trade_score") or profile.get("final_score"), 0.0)
        risk_flags = row.get("risk_flags") or profile.get("risk_flags") or []
        if score >= 70:
            action = "模拟验证/实盘预检查"
            reason = "评分较高，但真实交易仍需券商连接、风控和人工确认。"
        elif score >= 55:
            action = "观察"
            reason = "评分在观察区间，适合加入实时模拟或等待更明确触发。"
        elif score > 0:
            action = "回避/仅观察"
            reason = "评分偏低，先查看风险标签和数据缺失。"
        else:
            action = "数据不足"
            reason = "暂无评分溯源，请先运行筛选、回测或实时模拟。"
        if safety.get("LIVE_KILL_SWITCH"):
            action = "实盘阻断"
            reason = "Kill switch 已开启，真实下单被阻断。"
        elif not safety.get("LIVE_TRADING_ENABLED"):
            reason += " 当前 LIVE_TRADING_ENABLED=false，只允许模拟或预检查。"
        decisions.append(
            {
                "symbol": sym,
                "name": row.get("name") or profile.get("name") or sym,
                "score": round(score, 2) if score else None,
                "action": action,
                "reason": reason,
                "risk_flags": risk_flags[:6] if isinstance(risk_flags, list) else risk_flags,
                "tags": (row.get("tags") or profile.get("tags") or [])[:8] if isinstance(row.get("tags") or profile.get("tags") or [], list) else [],
                "score_time": row.get("updated_at") or profile.get("updated_at") or "",
                "source": "score_provenance_or_screener_history" if row or profile else "missing_score",
            }
        )
    return decisions


def _unique_text(values: list[Any], limit: int = 12) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _has_explicit_ai_tech_exposure(symbol: str, name: str, profile: dict) -> bool:
    """Guard against strategy tags such as ma_repair being read as an AI industry signal."""
    tokens: list[str] = []
    for key in ("industry", "industries", "concept", "concepts", "tags", "strategy_tags", "summary", "business", "sector"):
        value = profile.get(key)
        if isinstance(value, (list, tuple, set)):
            tokens.extend(str(x) for x in value)
        elif value is not None:
            tokens.append(str(value))
    tokens.append(str(name or ""))
    tokens.append(str(symbol or ""))
    text = " ".join(tokens)
    tech_words = ("半导体", "芯片", "算力", "人工智能", "云计算", "服务器", "电子", "软件", "机器人")
    if any(word in text for word in tech_words):
        return True
    return any(token.strip().upper() == "AI" for token in tokens)


def _agent_symbol_global_impacts(symbols: list[str], stream_items: list[dict], scores: dict[str, dict], config: dict) -> list[dict]:
    """Map real global events to the current symbol pool with explainable rules."""
    signal_map = dict(config.get("screener_signal_map") or {})
    out: list[dict] = []
    for sym in symbols[:30]:
        row = scores.get(sym) or {}
        profile = dict(signal_map.get(sym) or {})
        name = str(profile.get("name") or row.get("name") or sym)
        try:
            exposure = global_industry_mapper.company_exposure(sym, profile=profile, name=name)
            mapped = global_industry_mapper.map_items(stream_items[:30], sym, name=name, profile=profile).get("industry_mapped_items", [])
        except Exception as exc:
            out.append(
                {
                    "symbol": sym,
                    "name": name,
                    "status": "mapping_error",
                    "missing_reason": f"全球事件映射失败：{str(exc)[:120]}",
                    "related_events": [],
                }
            )
            continue
        exposure_terms = _unique_text(
            list(exposure.get("industries") or [])
            + list(exposure.get("concepts") or [])
            + list(exposure.get("chain_position") or [])
            + list(exposure.get("upstream") or [])
            + list(exposure.get("downstream") or [])
            + list(exposure.get("policy_sensitivity") or [])
            + list(exposure.get("commodity_sensitivity") or []),
            limit=24,
        )
        matching_terms = _unique_text(
            list(exposure.get("industries") or [])
            + list(exposure.get("concepts") or [])
            + list(exposure.get("chain_position") or [])
            + list(exposure.get("upstream") or [])
            + list(exposure.get("downstream") or [])
            + list(exposure.get("policy_sensitivity") or []),
            limit=28,
        )
        if not _has_explicit_ai_tech_exposure(sym, name, profile):
            ai_noise_terms = {"AI", "半导体", "芯片", "电子", "国产替代", "算力基础设施", "半导体/算力", "科技主题"}
            exposure_terms = [term for term in exposure_terms if term not in ai_noise_terms]
            matching_terms = [term for term in matching_terms if term not in ai_noise_terms]
        related: list[dict] = []
        exposure_set = set(matching_terms)
        for item in mapped:
            targets = _unique_text(
                list(item.get("impact_targets") or [])
                + list(item.get("affected_sectors") or [])
                + list(item.get("affected_assets") or [])
                + list(item.get("mapped_industries") or [])
                + list(item.get("mapped_concepts") or []),
                limit=24,
            )
            overlap = sorted(exposure_set.intersection(set(targets + list(item.get("mapped_chain") or []))))
            broad_hits: list[str] = []
            raw_text = f"{item.get('title') or ''} {item.get('summary') or ''}"
            direct_symbol_hit = sym in {str(x) for x in (item.get("mapped_symbols") or [])} or sym in raw_text or (name and name in raw_text)
            overlap = [x for x in overlap if direct_symbol_hit or (x and x in raw_text)]
            rate_text_hit = any(x in raw_text for x in ["利率", "降息", "加息", "美联储", "逆回购", "流动性", "美元", "美债", "非农", "CPI", "FOMC"])
            trade_text_hit = any(x in raw_text for x in ["出口管制", "关税", "反倾销", "贸易制裁", "人民币", "汇率", "美元指数", "外需", "海外订单", "欧盟", "美国市场", "国际贸易"])
            if "成长股估值" in targets and rate_text_hit and any(x in exposure_set for x in ["新能源", "储能", "电池", "光伏", "利率政策"]):
                broad_hits.append("成长股估值/利率敏感")
            if "出口链" in targets and trade_text_hit and any(x in exposure_set for x in ["光伏", "新能源", "电池", "硅料", "组件"]):
                broad_hits.append("出口链/汇率敏感")
            silicon_text_hit = any(x in raw_text for x in ["硅料", "工业硅", "多晶硅"])
            power_text_hit = any(x in raw_text for x in ["电价", "电力价格", "煤炭", "动力煤", "天然气", "LNG"])
            oil_text_hit = any(x in raw_text for x in ["原油", "石油", "油价", "布伦特", "WTI", "OPEC"])
            commodity_exposure_hit = any(x in exposure_set for x in ["硅料", "化工", "原油", "天然气", "煤炭", "电力", "电价"])
            direct_cost_exposure_hit = (silicon_text_hit and "硅料" in exposure_set) or (
                power_text_hit and any(x in exposure_set for x in ["电力", "电价", "煤炭", "天然气", "化工"])
            )
            oil_exposure_hit = any(x in exposure_set for x in ["原油", "石油石化", "化工", "航空运输"])
            commodity_event = silicon_text_hit or power_text_hit or oil_text_hit
            if commodity_event and not (direct_cost_exposure_hit or oil_exposure_hit):
                overlap = [x for x in overlap if x not in {"新能源", "能源", "大宗商品", "能源化工"}]
            overlap = [x for x in overlap if not (x in {"能源", "大宗商品"} and not (commodity_exposure_hit and commodity_event))]
            if any(x in targets for x in ["原油", "能源化工", "大宗商品"]) and (
                (direct_cost_exposure_hit and (silicon_text_hit or power_text_hit)) or (oil_text_hit and oil_exposure_hit)
            ):
                broad_hits.append("能源成本/商品价格")
            supply_chain_text_hit = any(x in raw_text for x in ["出口管制", "关税", "反倾销"]) or (
                "制裁" in raw_text and any(x in raw_text for x in ["出口", "技术", "芯片", "半导体", "光伏", "电池", "新能源", "供应链"])
            )
            if supply_chain_text_hit and any(x in exposure_set for x in ["光伏", "新能源", "芯片", "半导体", "出口链"]):
                broad_hits.append("贸易政策/供应链风险")
            is_related = bool(direct_symbol_hit or overlap or broad_hits)
            if not is_related:
                continue
            related.append(
                {
                    "title": item.get("title"),
                    "published_at": item.get("published_at"),
                    "source": item.get("source"),
                    "source_ref": item.get("source_ref") or item.get("source_url") or item.get("url") or item.get("source_page"),
                    "source_api": item.get("source_api"),
                    "source_page": item.get("source_page"),
                    "impact_note": item.get("impact_note") or item.get("impact_reason") or "全球事件规则映射，仅用于信息面和风控解释。",
                    "impact_targets": targets[:10],
                    "matched_terms": _unique_text(overlap + broad_hits, limit=8),
                    "relevance_score": round(_as_float(item.get("relevance_score"), 0.0), 2),
                    "mapping_policy": "global_event_to_symbol_exposure_v323",
                }
            )
            if len(related) >= 5:
                break
        out.append(
            {
                "symbol": sym,
                "name": name,
                "status": "related" if related else "no_direct_mapping",
                "exposure_terms": exposure_terms[:14],
                "related_count": len(related),
                "related_events": related,
                "explain": "命中时仅表示宏观/商品/政策事件可能影响该标的产业链或估值环境，不直接构成买卖建议。"
                if related
                else "当前真实全球快讯未直接命中该标的产业链；仍作为大盘环境观察。",
            }
        )
    return out


@app.get("/api/agent/market-brief")
def agent_market_brief(symbols: str | None = None, force: bool = False, limit: int = 80) -> dict:
    config = _build_auto_trading_config({"symbols": _parse_symbol_text(symbols)} if symbols else {})
    symbol_list = _parse_symbol_text(symbols) if symbols else list(config.get("symbols") or [])[:20]
    stream_data, stream_status = _read_global_news_stream(limit=limit, force=force, live=True)
    stream_items = [x for x in (stream_data.get("items") or []) if isinstance(x, dict)]
    macro_watch = _macro_event_watchlist(stream_items)
    broker_status = live_trading_engine_v323.status()
    safety = broker_status.get("safety") or {}
    scores = _agent_score_rows(symbol_list)
    decisions = _agent_symbol_decisions(symbol_list, scores, config, safety)
    symbol_global_impacts = _agent_symbol_global_impacts(symbol_list, stream_items, scores, config)
    evidence = []
    for item in stream_items[:8]:
        evidence.append(
            {
                "type": "global_flash",
                "title": item.get("title"),
                "source": item.get("source"),
                "published_at": item.get("published_at"),
                "source_ref": item.get("source_ref") or item.get("source_url") or item.get("url") or item.get("source_page"),
                "source_api": item.get("source_api"),
                "source_page": item.get("source_page"),
                "impact_scope": item.get("impact_scope") or item.get("message_dimension"),
                "impact_targets": item.get("impact_targets") or [],
                "affected_sectors": item.get("affected_sectors") or [],
                "affected_assets": item.get("affected_assets") or [],
                "impact_note": item.get("impact_note") or "全球信息面证据，只进入风险解释与信息面辅助判断。",
            }
        )
    for item in macro_watch:
        if item.get("evidence_count"):
            evidence.append(
                {
                    "type": "macro_watch",
                    "title": item.get("label"),
                    "source": item.get("latest_source"),
                    "source_ref": item.get("latest_source_ref"),
                    "source_api": item.get("latest_source_api"),
                    "source_page": item.get("latest_source_page"),
                    "reason": item.get("reason"),
                    "impact_targets": item.get("impact_targets") or [],
                    "affected_sectors": item.get("affected_sectors") or [],
                    "affected_assets": item.get("affected_assets") or [],
                    "impact_note": item.get("impact_note") or item.get("reason"),
                }
            )
    risk_flags = []
    if not stream_items:
        risk_flags.append("全球快讯暂未命中：信息面只能使用缓存或等待真实来源")
    if safety.get("LIVE_KILL_SWITCH"):
        risk_flags.append("LIVE_KILL_SWITCH 已开启，真实交易全部阻断")
    if not safety.get("LIVE_TRADING_ENABLED"):
        risk_flags.append("LIVE_TRADING_ENABLED=false，当前只能模拟/预检查")
    if safety.get("ORDER_CONFIRM_REQUIRED"):
        risk_flags.append("ORDER_CONFIRM_REQUIRED=true，真实订单必须人工确认")
    if not (broker_status.get("broker") or {}).get("connected"):
        risk_flags.append("券商未连接或未授权，QMT/PTrade 只显示 disabled/unsupported")
    if not any(d.get("score") for d in decisions):
        risk_flags.append("股票池暂无评分溯源，请先运行筛选/回测/实时模拟")
    strong = [d for d in decisions if (d.get("score") or 0) >= 70]
    watch = [d for d in decisions if 55 <= (d.get("score") or 0) < 70]
    if strong:
        headline = f"{len(strong)} 只标的评分较高：先进入实时模拟和实盘预检查。"
        action = "paper_then_precheck"
    elif watch:
        headline = f"{len(watch)} 只标的处于观察区间：等待信号确认。"
        action = "watch"
    else:
        headline = "当前更适合观察/补充数据，不建议自动新增真实仓位。"
        action = "hold_or_collect_data"
    if risk_flags:
        headline += " 真实交易仍受安全门控约束。"
    return {
        "ok": True,
        "data": {
            "agent_id": "connected_market_agent_v323",
            "mode": "evidence_only_online_agent",
            "headline": headline,
            "recommended_action": action,
            "confidence": "medium" if stream_items or any(d.get("score") for d in decisions) else "low",
            "symbols": symbol_list,
            "symbol_decisions": decisions,
            "global_flash_count": len(stream_items),
            "global_stream_mode": stream_data.get("stream_mode"),
            "macro_watchlist": macro_watch,
            "symbol_global_impacts": symbol_global_impacts,
            "evidence": evidence[:16],
            "items": stream_items[:16],
            "source_link_count": len([x for x in evidence if x.get("source_ref")]),
            "unlinked_evidence_count": len([x for x in evidence if not x.get("source_ref")]),
            "risk_flags": list(dict.fromkeys(risk_flags)),
            "next_steps": [
                "先运行筛选或读取总控台配置，确认股票池和策略组合。",
                "用同一套策略先跑回测，再启动实时模拟。",
                "只有券商连接、风控通过、确认队列批准后，才允许真实下单。",
            ],
            "broker_safety": safety,
            "source_status": stream_data.get("sources_status") or [],
            "cache_status": stream_status,
            "llm_status": "未接入外部 LLM 下单；当前为联网数据 + 规则证据代理。",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "disclaimer": "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。",
        },
    }


def _macro_event_watchlist(items: list[dict]) -> list[dict]:
    """Build an evidence-only macro watchlist from real global-news items."""
    patterns = [
        ("nonfarm_payrolls", "美国非农就业", r"非农|nonfarm|payroll|就业报告|劳动力市场"),
        ("us_cpi", "美国 CPI/PCE 通胀", r"CPI|PCE|通胀|物价|inflation"),
        ("fomc_rate", "美联储/FOMC/利率", r"美联储|FOMC|降息|加息|利率|鲍威尔|Fed"),
        ("usd_treasury", "美元/美债收益率", r"美元|美债|收益率|DXY|Treasury|汇率"),
        ("crude_gold", "原油/黄金/大宗商品", r"原油|黄金|铜|煤炭|商品|OPEC|WTI|Brent|金价"),
        ("geopolitics", "地缘风险", r"地缘|冲突|制裁|关税|出口管制|战争|袭击"),
        ("china_policy", "国内政策/流动性", r"央行|降准|逆回购|LPR|社融|财政|政策|房地产"),
    ]
    watch: list[dict] = []
    for key, label, pattern in patterns:
        matched = []
        regex = re.compile(pattern, re.I)
        for item in items:
            text = f"{item.get('title') or ''} {item.get('summary') or ''} {item.get('source') or ''}"
            if regex.search(text):
                matched.append(item)
        latest = matched[0] if matched else {}
        watch.append(
            {
                "key": key,
                "label": label,
                "status": "有真实新闻命中" if matched else "等待真实来源",
                "evidence_count": len(matched),
                "latest_title": str(latest.get("title") or "") if matched else "",
                "latest_source": str(latest.get("source") or "") if matched else "",
                "latest_source_ref": str(latest.get("source_ref") or latest.get("source_url") or latest.get("url") or latest.get("source_page") or "") if matched else "",
                "latest_source_api": str(latest.get("source_api") or "") if matched else "",
                "latest_source_page": str(latest.get("source_page") or "") if matched else "",
                "impact_targets": list(latest.get("impact_targets") or []) if isinstance(latest.get("impact_targets"), list) else [],
                "affected_sectors": list(latest.get("affected_sectors") or []) if isinstance(latest.get("affected_sectors"), list) else [],
                "affected_assets": list(latest.get("affected_assets") or []) if isinstance(latest.get("affected_assets"), list) else [],
                "impact_note": str(latest.get("impact_note") or "") if matched else "",
                "reason": "来自全球信息面缓存/联网源，进入信息面与大盘情绪辅助判断。"
                if matched
                else "当前缓存未命中该事件；不填充假日期或假影响。",
            }
        )
    return watch


@app.get("/api/macro/global-events")
def macro_global_events(limit: int = 80, force: bool = False) -> dict:
    limit = max(10, min(int(limit or 80), 120))
    data, cache_status = _read_global_news_stream(limit=limit, force=force, live=True)
    items = [x for x in (data.get("items") or []) if isinstance(x, dict)]
    return {
        "ok": True,
        "data": {**data, "items": items, "cache_status": cache_status},
        "items": items,
        "watchlist": _macro_event_watchlist(items),
        "cache_status": cache_status,
        "agent_status": "联网辅助：使用真实全球信息面/缓存做规则归因；未接入外部 LLM 下单。",
        "disclaimer": "宏观事件只作为风险和解释变量，不单独构成买卖建议；无真实来源时显示等待真实来源。",
    }


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
        if f("pos250", 999) <= 35:
            why.append("当前近250日位置偏低，符合低位观察条件。")
        if f("drawdown250", 0) <= -25:
            why.append("相对一年高点回撤较充分。")
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
        if f("last", 0) and f("ma20", 0) and f("last") >= f("ma20"):
            why.append("价格已站上或贴近MA20，短中期修复强于完全破位状态。")
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
        if "大中市值" in tag:
            why.append("当前总市值达到规则阈值，因此标为大中市值；它只代表规模属性，不代表一定低风险。")
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


@app.get("/realtime-paper", response_class=HTMLResponse)
def realtime_paper_page() -> str:
    return build_realtime_paper_ui()


@app.get("/auto-trading", response_class=HTMLResponse)
def auto_trading_page() -> str:
    return build_auto_trading_workbench_ui()


@app.get("/live-trading", response_class=HTMLResponse)
def live_trading_page() -> str:
    return build_live_trading_ui()


@app.get("/trading-records", response_class=HTMLResponse)
def trading_records_page() -> str:
    return build_trading_records_ui()


@app.get("/data-center", response_class=HTMLResponse)
def data_center_page() -> str:
    return build_data_center_ui()


@app.get("/detail/{symbol}", response_class=HTMLResponse)
def detail_page(symbol: str, frame: str = "time", embedded: bool = False) -> str:
    return _build_ui(initial_symbol=symbol, full=True, initial_frame=frame, embedded=embedded)


@app.get("/trading", response_class=HTMLResponse)
def trading_page() -> str:
    return """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>Trading Risk Gateway V3.20</title>
<style>body{margin:0;background:#0b1020;color:#dbeafe;font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif}header{height:58px;display:flex;align-items:center;gap:10px;padding:0 18px;background:#101827;border-bottom:1px solid #283956}.dot{width:10px;height:10px;border-radius:50%;background:#22c55e;box-shadow:0 0 14px #22c55e}.brand{font-weight:900;color:#bfdbfe;font-size:18px}.pill{border:1px solid #30405d;background:#172033;border-radius:999px;padding:5px 9px;color:#fcd34d}.grow{flex:1}a{color:#bfdbfe}main{padding:16px;display:grid;grid-template-columns:360px 1fr;gap:14px}.panel{background:#111827;border:1px solid #283956;border-radius:14px;overflow:hidden}.h{padding:12px;background:#141f35;border-bottom:1px solid #283956;font-weight:900}.b{padding:12px}input,select{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px;margin:5px 0 10px}button{border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:800;padding:9px 12px;cursor:pointer}pre{white-space:pre-wrap;word-break:break-word;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:12px;min-height:360px}.muted{color:#91a7c7}</style></head>
<body><header><span class='dot'></span><div class='brand'>交易风控网关 V3.20</div><span class='pill'>paper only · 未接真实券商</span><div class='grow'></div><a href='/backtest'>回测</a><a href='/paper'>旧纸面页</a></header>
<main><section class='panel'><div class='h'>提交纸面信号</div><div class='b'><label>代码</label><input id='symbol' value='300750'><label>动作</label><select id='side'><option value='buy'>buy</option><option value='sell'>sell</option></select><label>数量</label><input id='quantity' type='number' value='100'><label>价格</label><input id='price' type='number' value='20'><label>评分</label><input id='score' type='number' value='68'><label>理由</label><input id='reason' value='V3.20 风控网关验证'><button onclick='send()'>发送信号</button><button onclick='load()'>刷新</button><p class='muted'>所有请求只进入风控、纸面订单和审计日志，不会连接券商。</p></div></section><section class='panel'><div class='h'>状态</div><div class='b'><pre id='out'>Loading...</pre></div></section></main>
<script>const $=id=>document.getElementById(id);async function send(){const p={symbol:$('symbol').value,side:$('side').value,quantity:Number($('quantity').value),price:Number($('price').value),score:Number($('score').value),reason:$('reason').value};const r=await fetch('/api/trading/signal',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(p)});$('out').textContent=JSON.stringify(await r.json(),null,2)}async function load(){const a=await fetch('/api/trading/risk/status').then(r=>r.json());const b=await fetch('/api/trading/paper/orders').then(r=>r.json());const c=await fetch('/api/trading/paper/positions').then(r=>r.json());const d=await fetch('/api/trading/audit').then(r=>r.json());$('out').textContent=JSON.stringify({risk:a.data,orders:b.data,positions:c.data,audit:d.data},null,2)}load()</script></body></html>"""


@app.get("/chart/{symbol}", response_class=HTMLResponse)
def chart_page(symbol: str, frame: str = "time", embedded: bool = False) -> str:
    return _build_ui(initial_symbol=symbol, full=True, initial_frame=frame, embedded=embedded)


@app.get("/ui", response_class=HTMLResponse)
def ui(symbol: str = "300750", frame: str | None = None, mode: str | None = None, embedded: bool = False) -> str:
    initial_frame = frame or mode or "time"
    return _build_ui(initial_symbol=symbol or "300750", full=False, initial_frame=initial_frame, embedded=embedded)


def _build_ui(initial_symbol: str, full: bool = False, initial_frame: str = "time", embedded: bool = False) -> str:
    return build_ui_v22(initial_symbol=initial_symbol, full=full, initial_frame=initial_frame, embedded=embedded)
