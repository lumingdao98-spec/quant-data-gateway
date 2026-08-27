from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import RLock
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote

try:
    from ftfy import fix_text as _ftfy_fix_text
except Exception:  # pragma: no cover
    _ftfy_fix_text = None

from quant_data.utils import ThrottledSession, infer_exchange, normalize_symbol, to_eastmoney_secid
from quant_data.services.news_store_service import NewsStoreService
from quant_data.services.news_cleaner import (
    current_scoring_window_days,
    document_id_from_url,
    extract_time_fields,
    is_page_chrome_summary,
    is_menu_or_table_fragment,
    strip_html_boilerplate,
    valid_news_item as _valid_news_item,
)
from quant_data.services.policy_event_intelligence import PolicyEventIntelligence


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    source_type: str = "news"          # news / announcement / forum / policy / research / macro
    published_at: str | None = None
    published_at_norm: str | None = None
    date_display: str | None = None
    publish_time: str | None = None
    event_time: str | None = None
    crawl_time: str | None = None
    time_confidence: str = ""
    time_basis: str = ""
    event_type: str = "general_news"
    issuer: str = ""
    period: str = ""
    document_id: str = ""
    summary: str = ""
    relevance_score: float = 0.0
    sentiment_score: float = 50.0
    credibility_score: float = 40.0
    impact_score: float = 0.0
    fake_risk_score: float = 0.0        # 0低风险，100高疑似风险
    category: str = "其他信息"
    message_dimension: str = "公司消息"       # 宏观经济消息 / 行业消息 / 公司消息 / 市场资金面消息 / 国际消息 / 社区舆情 / 官方公告
    event_label: str = "一般资讯"
    sentiment_label: str = "中性"
    impact_scope: str = "company"
    impact_direction: str = "中性/待观察"
    risk_tag: str = ""
    duplicate_group: str = ""
    event_key: str = ""                 # 事件级去重键：同一财报/监管/减持/订单事件只计一次权重
    event_weight: float = 1.0             # 事件计分权重，受可信度/影响度/时效性修正
    recency_weight: float = 1.0           # 时效权重：近期信息更高，历史信息降低但不丢弃
    dedup_reason: str = ""
    industry_tags: list[str] | None = None
    evidence: list[str] | None = None
    content_loaded: bool = False
    target_relation: str = ""            # 当前标的在该信息中的真实关系：机构持仓上升/下降/公司公告/无明确关系
    relation_confidence: float = 0.0
    relation_note: str = ""
    attachment_url: str = ""
    content_source: str = ""
    content_quality_status: str = "title_only"
    content_missing_reason: str = ""
    content_hash: str = ""
    duplicate_count: int = 1
    duplicate_sources: list[str] | None = None
    duplicate_source_refs: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NewsAnalysisService:
    _cache_file_lock = RLock()
    """中文信息面抓取与轻量评分。

    V2.6 改进点：
    V3.12 改进点：
    1. 搜索引擎页面不再作为信息面证据；百度/360等只可作为诊断，不进入核心抓取和评分；
    2. 信息源按“宏观经济、行业、公司、资金面、国际消息、公告、舆情”分层；
    3. 同一事件按事件族去重，全球/前沿要闻可映射行业并参与信息面评分；
    4. 返回 sources_status、source_policy、scoring_model，便于检查为什么某些源为0。
    """

    POSITIVE_WORDS = {
        "增长", "大增", "创新高", "突破", "中标", "订单", "回购", "增持", "分红", "盈利能力改善", "扭亏",
        "扩产", "合作", "签约", "龙头", "景气", "利好", "上调", "超预期", "放量", "升级", "获批",
        "改善", "回暖", "复苏", "加速", "领先", "国产替代", "降本", "提效", "稳定增长", "高增长",
    }
    NEGATIVE_WORDS = {
        "下滑", "亏损", "亏", "为负", "亏损扩大", "扣非亏损", "净利润下降", "暴跌", "处罚", "立案", "调查", "减持", "诉讼", "风险", "利空", "违约",
        "终止", "退市", "问询", "监管", "召回", "裁员", "降价", "低于预期", "下调", "跌停",
        "不及预期", "债务", "冻结", "质押", "爆雷", "造假", "虚假", "澄清", "辟谣", "警示",
    }
    IMPACT_WORDS = {
        "业绩", "预告", "公告", "减持", "增持", "回购", "订单", "中标", "政策", "监管", "诉讼", "融资",
        "并购", "重组", "分红", "产能", "涨价", "降价", "出口", "海外", "AI", "新能源", "芯片", "机器人",
        "财报", "年报", "季报", "半年报", "营收", "净利润", "毛利率", "现金流", "研发", "市占率",
    }
    POLICY_WORDS = {"政策", "监管", "发改委", "工信部", "财政部", "国资委", "证监会", "交易所", "补贴", "关税", "出口管制", "产业链", "规划", "指导意见"}
    INDUSTRY_POLICY_TERMS = {
        "固态电池", "动力电池", "储能", "新能源车", "锂电", "光伏", "风电", "充电桩",
        "军工", "国防", "兵器", "弹药", "航天", "航空发动机", "低空经济", "无人机",
        "半导体", "芯片", "算力", "人工智能", "机器人", "数据中心",
        "创新药", "医药", "医疗器械", "消费", "白酒", "黄金", "有色",
    }
    FINANCE_WORDS = {"财报", "业绩", "营收", "净利润", "扣非", "毛利率", "现金流", "ROE", "每股收益", "年报", "季报", "半年报", "预告", "快报"}
    RISK_WORDS = {"立案", "处罚", "问询", "诉讼", "仲裁", "冻结", "减持", "退市", "ST", "违规", "监管", "召回", "安全事故", "债务", "违约", "澄清", "辟谣"}
    OPERATION_WORDS = {"订单", "中标", "合同", "合作", "投产", "扩产", "产能", "项目", "客户", "产品", "技术", "研发", "专利", "交付"}
    FORUM_WORDS = {"股吧", "雪球", "投资者", "网友", "热议", "评论", "讨论"}

    TRUSTED_DOMAINS = {
        "eastmoney.com": 68,
        "10jqka.com.cn": 66,
        "cls.cn": 75,
        "jin10.com": 74,
        "wallstcn.com": 74,
        "whitehouse.gov": 98,
        "federalregister.gov": 99,
        "stcn.com": 76,
        "cnstock.com": 74,
        "sina.com.cn": 62,
        "xueqiu.com": 48,
        "qq.com": 58,
        "163.com": 55,
        "thepaper.cn": 60,
        "cs.com.cn": 74,
        "sse.com.cn": 92,
        "szse.cn": 92,
        "cninfo.com.cn": 92,
        "neeq.com.cn": 88,
        "baidu.com": 52,
        "so.com": 50,
        "sogou.com": 48,
    }

    def __init__(self, cache_file: str | Path = "data/news_cache.json", cache_ttl_seconds: int = 30 * 60) -> None:
        self.http = ThrottledSession(min_interval=1.0, timeout=10)
        self.policy_http = ThrottledSession(min_interval=0.0, timeout=4)
        # 新闻搜索页面通常更像浏览器请求，补充可接受的HTML头。
        self.http.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,text/plain,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
        })
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.store = NewsStoreService()
        self.event_intelligence = PolicyEventIntelligence()
        self._source_status: list[dict[str, Any]] = []
        self._last_source_status: list[dict[str, Any]] = []
        self._last_source_checked_at: str = ""
        self._last_global_source_status: list[dict[str, Any]] = []
        self._last_global_checked_at: str = ""
        self._global_news_cache: dict[str, Any] | None = None
        self._global_news_cache_ts: float = 0.0
        self.source_timeout_seconds = 3.0
        self.detail_timeout_seconds = 5.0
        self.detail_workers = 6
        self.announcement_first_limit = 16
        self.finance_media_limit = 80
        self.community_limit = 30
        self._source_failures: dict[str, int] = {}
        self._source_circuit_opened_at: dict[str, float] = {}
        self._content_cache: dict[str, tuple[float, str]] = {}
        self._announcement_detail_cache: dict[str, tuple[float, dict[str, str]]] = {}
        self._round_started_at: float = 0.0
        self._round_budget_seconds: float | None = None
        self._current_mode: str = "light"
        self._budget_exhausted_recorded: bool = False
        self._last_cleaning_funnel: dict[str, Any] = {}

    def analyze(self, symbol: str, name: str | None = None, limit: int = 120, force: bool = False, mode: str = "light", budget_seconds: float | None = None, allow_network: bool = True) -> dict[str, Any]:
        symbol = normalize_symbol(symbol)
        name = (name or symbol).strip()
        limit = max(30, min(int(limit or 120), 500))
        mode_raw = str(mode or "light").lower()
        mode = "deep" if mode_raw in {"deep", "deep_refresh", "full"} else "normal" if mode_raw in {"normal", "detail"} else "light"
        if budget_seconds is None:
            # Cache-only screening never reaches this network budget. A manual
            # or background force refresh gets enough time for both official
            # announcement sources instead of persisting a fast empty result.
            budget_seconds = 10.0 if (mode == "light" and force and allow_network) else 8.0 if mode == "deep" else 5.0 if mode == "normal" else 4.0
        key = f"cn_v319_{mode}:{symbol}:{name}:{limit}"
        self._log_progress(f"开始信息面分析 {name}({symbol})，抓取上限={limit}，mode={mode}，force={force}")
        if not force:
            cached = self.store.read_analysis(symbol, key, self.cache_ttl_seconds) or self._read_cache(key)
            cached_saved_at = float((cached or {}).get("cache_info", {}).get("saved_at_ts") or 0)
            cached_age = time.time() - cached_saved_at if cached_saved_at else None
            if cached and (cached.get("items") or (cached_age is not None and cached_age <= 60)):
                cached = self._normalize_cached_result(cached, symbol=symbol, name=name, limit=limit)
                cached.setdefault("cache_info", {"hit": True, "ttl_seconds": self.cache_ttl_seconds})
                self._last_source_status = [
                    dict(row) for row in (cached.get("sources_status") or []) if isinstance(row, dict)
                ]
                self._last_source_checked_at = str(cached.get("updated_at") or "")
                self._log_progress(f"命中信息面缓存 {name}({symbol})，返回缓存结果")
                return cached

        self._source_status = []
        self._current_mode = mode
        self._round_started_at = time.monotonic()
        self._round_budget_seconds = float(budget_seconds) if budget_seconds else None
        self._budget_exhausted_recorded = False
        query = f"{name} {symbol}"
        # 先读持久化库中的历史信息，避免每次全量爬取，也用于识别历史大雷。
        stored_rows = self.store.list_items(symbol, limit=max(limit * 3, 220), include_history_days=3650)
        stored_items = [self._item_from_dict(x) for x in stored_rows]
        self._log_progress(f"历史信息库读取 {len(stored_items)} 条，开始多源抓取")
        stored_valid = self._valid_count_estimate(stored_items, symbol=symbol, name=name)
        items: list[NewsItem] = []
        light_evidence_target = min(limit, 30)
        if not allow_network:
            self._record_source("筛选缓存优先", stored_valid, "仅复用本地真实信息；官方源转为后台刷新", skipped_reason="background_refresh")
        elif mode == "light" and stored_valid >= light_evidence_target:
            self._record_source("light mode历史库复用", stored_valid, "历史高质量证据已足够，筛选页停止补源")
        else:
            items = self._search_all(query=query, symbol=symbol, name=name, limit=limit, mode=mode)
        try:
            self._log_progress(f"多源抓取完成：新抓取 {len(items)} 条，开始正文/公告补充")
            try:
                items = self._enrich_announcement_content(items, max_items=8 if mode == "light" else 8 if mode == "normal" else 16)
            except Exception as exc:
                self._record_source("公告正文补充", 0, "降级为标题级证据", skipped_reason=str(exc)[:160])
            # V16.2：新浪/同花顺等股票专页在抓取入口已做候选链接准入+详情页正文准入；
            # 这里继续作为兜底补强，不再依赖“先抓一堆再清洗”的后置策略。
            try:
                items = self._enrich_link_content(items, symbol=symbol, name=name, max_items=4 if mode == "light" else 6 if mode == "normal" else 20)
            except Exception as exc:
                self._record_source("新闻正文补充", 0, "降级为标题级证据", skipped_reason=str(exc)[:160])
            merged_items = self._filter_valid_items(stored_items + items, symbol=symbol, name=name)
            before_dedup = len(stored_items) + len(items)
            dropped_invalid = before_dedup - len(merged_items)
            if dropped_invalid > 0:
                self._log_progress(f"信息清洗完成：丢弃页头/页脚/JS/无关脏数据 {dropped_invalid} 条")
            deduped = self._deduplicate(merged_items)
        except Exception as exc:
            self._record_source("信息后处理", 0, "降级为标题级证据", skipped_reason=str(exc)[:160])
            try:
                merged_items = self._filter_valid_items(stored_items + items, symbol=symbol, name=name)
            except Exception:
                merged_items = [x for x in stored_items + items if isinstance(x, NewsItem)]
            deduped = self._deduplicate(merged_items)
        self._log_progress(f"事件簇去重完成：{len(merged_items)} 条 -> {len(deduped)} 个事件/信息组")
        saved_items = self.store.upsert_items(symbol, name, deduped)
        aggregate = self._aggregate(symbol, name, deduped)
        self._log_progress(f"信息面分析完成：保存/更新 {saved_items} 条，信息面得分 {aggregate.get('news_score')}")
        result = {
            "symbol": symbol,
            "name": name,
            "query": query,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(deduped),
            **aggregate,
            "items": [x.to_dict() for x in deduped[:min(limit, 80)]],
            "stored_items_used": len(stored_items),
            "stored_items_saved": saved_items,
            "sources_used": sorted(list({x.source for x in deduped})),
            "sources_status": self._source_status,
            "cleaning_funnel": dict(self._last_cleaning_funnel),
            "source_policy": self.message_source_policy(),
            "cache_info": {"hit": False, "store": "sqlite+json", "ttl_seconds": self.cache_ttl_seconds, "reuse_policy": "分析结果默认缓存约30分钟；新闻条目长期写入 data/news_store.sqlite 复用；force=true 将重新抓取并重算标签。"},
            "crawl_mode": mode,
            "crawl_budget_seconds": budget_seconds,
            "network_used": bool(allow_network),
            "note": "中文公开信息源轻量抓取；新闻/公告持久化保存并可复用；结果受公开接口可用性影响，仅作筛选辅助，关键结论需人工核验公告和财报。",
        }
        self._write_cache(key, result)
        self.store.save_analysis(symbol, key, result, name=name)
        self._last_source_status = [dict(row) for row in self._source_status]
        self._last_source_checked_at = str(result.get("updated_at") or "")
        return result

    def search_keyword(self, keyword: str, limit: int = 80, force: bool = False) -> dict[str, Any]:
        """不要求股票代码的普通中文新闻搜索。"""
        keyword = str(keyword or "").strip()
        if not keyword:
            return {"keyword": keyword, "count": 0, "items": [], "news_score": 50.0, "summary": "关键词为空"}
        limit = max(20, min(int(limit or 80), 500))
        key = f"kw_v315_v16_3:{keyword}:{limit}"
        if not force:
            cached = self._read_cache(key)
            if cached:
                return cached
        self._source_status = []
        items: list[NewsItem] = []
        for fn in [self._search_eastmoney_page, self._search_sina_page, self._search_10jqka_page]:
            try:
                items.extend(fn(keyword, "", keyword, limit))
            except Exception as exc:
                self._record_source(fn.__name__, 0, str(exc)[:160])
        items = self._filter_valid_items(items, symbol="", name=keyword, allow_macro=True)
        deduped = self._deduplicate(items)
        aggregate = self._aggregate("", keyword, deduped)
        result = {
            "keyword": keyword,
            "query": keyword,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(deduped),
            **aggregate,
            "items": [x.to_dict() for x in deduped[:limit]],
            "sources_used": sorted(list({x.source for x in deduped})),
            "sources_status": self._source_status,
            "cleaning_funnel": dict(self._last_cleaning_funnel),
        }
        self._write_cache(key, result)
        return result

    def message_source_policy(self) -> dict[str, Any]:
        """消息面信息源分层策略。"""
        return {
            "核心事实源": ["交易所公告", "巨潮资讯", "上市公司公告", "证监会/交易所监管信息"],
            "高频快讯源": ["财联社", "华尔街见闻", "金十/金十期货", "东方财富/新浪/同花顺财经"],
            "宏观政策源": ["中国政府网/央行/统计局/部委", "各主要经济体政府、央行、统计和监管机构", "IMF/世界银行/WTO/BIS/IEA/OPEC 等国际组织"],
            "行业信息源": ["行业协会", "产业政策", "券商/第三方研报摘要", "行业媒体"],
            "舆情源": ["股吧", "雪球", "微博/论坛等社区讨论"],
            "禁用为证据": ["百度/360/搜狗等搜索引擎关键词结果页", "广告页", "登录页", "导航页"],
            "原则": "官方公告和监管披露优先；快讯用于宏观/行业映射；社区只用于舆情热度和传闻风险；搜索引擎页不进入评分。",
            "国际确认规则": "不限定某几个国家。快讯负责尽早发现，官方原文负责确认；只有明确映射到行业、产品或公司并通过时效与可信度门槛，才参与个股信息分。",
        }

    def source_health(self) -> dict[str, Any]:
        """Read the latest source diagnostics without starting a crawl."""
        now = time.time()

        def decorate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            output: list[dict[str, Any]] = []
            for original in rows:
                row = dict(original)
                count = int(row.get("count") or 0)
                skipped = str(row.get("skipped_reason") or "").strip()
                status = str(row.get("status") or "").strip()
                if count > 0:
                    quality = "有有效数据"
                elif skipped:
                    quality = "已跳过/降级"
                elif status.lower() in {"ok", "healthy"}:
                    quality = "已连接但无有效条目"
                else:
                    quality = "异常或无数据"
                row["quality_status"] = quality
                output.append(row)
            return output

        circuits = []
        for source, opened_at in sorted(self._source_circuit_opened_at.items()):
            remaining = max(0.0, 120.0 - (now - float(opened_at or 0)))
            if remaining <= 0:
                continue
            circuits.append(
                {
                    "source": source,
                    "failures": int(self._source_failures.get(source) or 0),
                    "remaining_seconds": round(remaining, 1),
                    "status": "短时熔断，等待后续显式刷新重试",
                }
            )
        return {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "last_stock_source_checked_at": self._last_source_checked_at,
            "last_global_source_checked_at": self._last_global_checked_at,
            "stock_sources": decorate(self._last_source_status),
            "global_sources": decorate(self._last_global_source_status),
            "active_circuits": circuits,
            "store": self.store.stats(),
            "source_policy": self.message_source_policy(),
            "network_used": False,
            "truth_boundary": "这里只展示最近一次真实抓取诊断与本地信息库覆盖；没有数据的来源不会补分，百度/360/搜狗结果页永久不作为证据。",
        }



    def fetch_global_news(self, limit: int = 80, force: bool = False, ttl_seconds: int = 45, budget_seconds: float = 5.0) -> dict[str, Any]:
        """多源获取全球/国内/商品/政策要闻，并和个股新闻严格分开展示。

        V3.15 修复点：
        1. 东方财富快讯/金十/华尔街见闻/财联社/AKShare 多源拉取；
        2. 按国内、全球、商品、外汇、债券、央行、行业政策等分类；
        3. 全球要闻短缓存自动刷新，不依赖个股“强制抓取”；
        4. 用事件级去重，避免同一快讯被多源转载后重复进入信息面评分。
        """
        limit = max(20, min(int(limit or 80), 240))
        now = time.time()
        if (not force) and self._global_news_cache and now - self._global_news_cache_ts <= ttl_seconds:
            data = dict(self._global_news_cache)
            data.setdefault("cache_info", {})
            data["cache_info"].update({"hit": True, "ttl_seconds": ttl_seconds, "auto_refresh": True})
            self._last_global_source_status = [
                dict(row) for row in (data.get("sources_status") or []) if isinstance(row, dict)
            ]
            self._last_global_checked_at = str(data.get("updated_at") or "")
            return data

        raw_rows: list[dict[str, Any]] = []
        status: list[dict[str, Any]] = []
        started_at = time.monotonic()

        def budget_left() -> float:
            return max(0.0, float(budget_seconds or 0.0) - (time.monotonic() - started_at))

        def can_continue() -> bool:
            return budget_left() > 0.15

        def budget_status(source: str) -> None:
            status.append({
                "source": source,
                "count": 0,
                "status": "总刷新时限已到，保留先完成的真实来源",
                "skipped_reason": "budget_exhausted",
            })

        # Fast alerts come first for latency, then primary policy documents for
        # confirmation.  Slow broad aggregators can no longer consume the
        # whole refresh budget before the time-sensitive sources are queried.
        try:
            if not can_continue():
                raise TimeoutError("总刷新时限已到")
            jin10_rows = self._bounded_value(
                lambda: self._search_jin10_flash(limit=min(limit, 100)),
                timeout=min(1.4, budget_left()),
                label="金十/金十期货快讯",
            )
            raw_rows.extend(jin10_rows)
            status.append({"source": "金十/金十期货快讯", "count": len(jin10_rows), "status": "ok" if jin10_rows else "无公开数据或接口结构变化"})
        except Exception as exc:
            status.append({"source": "金十/金十期货快讯", "count": 0, "status": str(exc)[:160]})

        try:
            if not can_continue():
                raise TimeoutError("总刷新时限已到")
            official_rows = self._bounded_value(
                lambda: self._search_white_house_actions(limit=min(limit, 30)),
                timeout=min(1.8, budget_left()),
                label="美国白宫总统行动",
            )
            raw_rows.extend(official_rows)
            status.append({
                "source": "美国白宫总统行动",
                "count": len(official_rows),
                "status": "ok" if official_rows else "公开RSS暂无产业/市场相关条目",
            })
        except Exception as exc:
            status.append({"source": "美国白宫总统行动", "count": 0, "status": str(exc)[:160]})

        try:
            if not can_continue():
                raise TimeoutError("总刷新时限已到")
            federal_rows = self._bounded_value(
                lambda: self._search_federal_register(limit=min(limit, 50)),
                timeout=min(1.4, budget_left()),
                label="美国联邦公报",
            )
            raw_rows.extend(federal_rows)
            status.append({
                "source": "美国联邦公报",
                "count": len(federal_rows),
                "status": "ok" if federal_rows else "官方API暂无产业/市场相关条目",
            })
        except Exception as exc:
            status.append({"source": "美国联邦公报", "count": 0, "status": str(exc)[:160]})

        # 东方财富全球财经快讯：优先作为国内可访问的 7x24 要闻源。
        for category, url in self._eastmoney_kuaixun_urls().items():
            if len(raw_rows) >= max(12, min(24, limit // 3)):
                status.append({
                    "source": "东方财富快讯补充源",
                    "count": 0,
                    "status": "高优先级快讯与官方源已返回足够候选，本轮跳过慢速补充抓取",
                    "skipped_reason": "priority_sources_sufficient",
                })
                break
            if len(raw_rows) >= limit * 2:
                break
            if not can_continue():
                budget_status(f"东方财富快讯:{category}")
                break
            try:
                rows = self._bounded_value(
                    lambda url=url, category=category: self._search_eastmoney_kuaixun(url, category, limit=min(60, limit)),
                    timeout=min(1.4, budget_left()),
                    label=f"东方财富快讯:{category}",
                )
                raw_rows.extend(rows)
                status.append({"source": f"东方财富快讯:{category}", "count": len(rows), "status": "ok" if rows else "无公开条目/页面结构变化"})
            except Exception as exc:
                status.append({"source": f"东方财富快讯:{category}", "count": 0, "status": str(exc)[:160]})

        priority_sufficient = len(raw_rows) >= max(12, min(24, limit // 3))
        if priority_sufficient:
            ak = None  # type: ignore
            status.append({
                "source": "AKShare全球快讯补充源",
                "count": 0,
                "status": "高优先级来源候选充足，本轮跳过慢速补充抓取",
                "skipped_reason": "priority_sources_sufficient",
            })
        else:
            try:
                import akshare as ak  # type: ignore
            except Exception as exc:
                ak = None  # type: ignore
                status.append({"source": "akshare", "count": 0, "status": f"不可用：{exc}"[:160]})

        def records(df: Any) -> list[dict[str, Any]]:
            if df is None:
                return []
            if hasattr(df, "to_dict"):
                try:
                    return df.to_dict(orient="records")
                except Exception:
                    return []
            if isinstance(df, list):
                return [x for x in df if isinstance(x, dict)]
            return []

        if ak is not None and can_continue():
            calls = []
            if hasattr(ak, "stock_info_global_cls"):
                calls.append(("财联社电报", lambda: ak.stock_info_global_cls(symbol="全部")))
            if hasattr(ak, "stock_info_global_em"):
                calls.append(("东方财富全球快讯AK", lambda: ak.stock_info_global_em()))
            if hasattr(ak, "stock_info_global_sina"):
                calls.append(("新浪财经7x24", lambda: ak.stock_info_global_sina()))
            for source_name, fn in calls:
                if not can_continue():
                    budget_status(source_name)
                    break
                try:
                    rows = records(self._bounded_value(fn, timeout=min(1.8, budget_left()), label=source_name))
                    for r in rows:
                        r = dict(r)
                        r["_source_name"] = source_name
                        raw_rows.append(r)
                    status.append({"source": source_name, "count": len(rows), "status": "ok"})
                except Exception as exc:
                    status.append({"source": source_name, "count": 0, "status": str(exc)[:160]})

        api_calls = [
            ("华尔街见闻快讯", "https://api-one.wallstcn.com/apiv1/content/lives", {"channel": "global-channel", "limit": str(min(limit, 80))}),
            ("华尔街见闻市场", "https://api-one.wallstcn.com/apiv1/content/lives", {"channel": "global", "limit": str(min(limit, 80))}),
            ("财联社电报Web", "https://www.cls.cn/nodeapi/telegraphList", {"app": "CailianpressWeb", "category": "", "lastTime": "", "os": "web", "sv": "8.4.6"}),
        ]
        supplemental_completed = False
        for source_name, url, params in api_calls:
            if priority_sufficient and supplemental_completed:
                status.append({
                    "source": "华尔街见闻/财联社补充源",
                    "count": 0,
                    "status": "已尝试一个独立快讯源；候选充足，本轮不再扩展慢速补充抓取",
                    "skipped_reason": "priority_sources_sufficient",
                })
                break
            if not can_continue():
                budget_status(source_name)
                break
            try:
                resp = self._bounded_value(
                    lambda url=url, params=params: self.http.get(url, params=params, headers={"Referer": "https://wallstreetcn.com/" if "wallstcn" in url else "https://www.cls.cn/", "Accept": "application/json,text/plain,*/*"}),
                    timeout=min(1.4, budget_left()),
                    label=source_name,
                )
                data = self._decode_jsonish(resp.text)
                rows = self._extract_global_json_rows(data, source_name, limit=min(limit, 100))
                raw_rows.extend(rows)
                status.append({"source": source_name, "count": len(rows), "status": "ok" if rows else "无有效JSON条目"})
                supplemental_completed = bool(rows)
                if priority_sufficient and rows:
                    break
            except Exception as exc:
                status.append({"source": source_name, "count": 0, "status": str(exc)[:160]})

        items: list[NewsItem] = []
        for r in raw_rows:
            source = self._clean_text(str(r.get("_source_name") or r.get("文章来源") or r.get("source") or r.get("媒体") or ""))
            title = self._clean_text(str(r.get("标题") or r.get("新闻标题") or r.get("title") or r.get("内容") or r.get("content") or ""))
            summary = self._clean_text(str(r.get("摘要") or r.get("内容") or r.get("content") or r.get("summary") or ""))
            if not title and summary:
                title = summary[:90]
            pub = self._clean_text(str(r.get("发布时间") or r.get("发布日期") or r.get("时间") or r.get("datetime") or r.get("pub_time") or "")) or None
            url = self._clean_text(str(r.get("链接") or r.get("新闻链接") or r.get("url") or ""))
            ok, _reason = self.valid_news_item(title, summary, source=source or "全球要闻", url=url, source_type="macro", allow_macro=True)
            if not ok and title and url and not self._is_noise_title(title):
                event_probe = self.event_intelligence.enrich_item({
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "url": url,
                    "published_at": pub,
                    "credibility_score": self._credibility(url, source, "macro"),
                    "content_quality_status": str(r.get("_content_quality_status") or "title_only"),
                })
                ok = bool(
                    event_probe.get("event_type") != "general_information"
                    and event_probe.get("source_tier") in {"official_primary", "trusted_media", "fast_alert"}
                )
            if not ok:
                continue
            cat_hint = self._clean_text(str(r.get("_category") or ""))
            item = self._score_item(title, url, source or "全球要闻", pub, summary, "", "全球要闻", source_type="macro")
            text = f"{title} {summary} {cat_hint}"
            meta = self._classify_event(text)
            dim = self._global_message_dimension(text, source or "全球要闻", cat_hint)
            category = self._global_market_category(text, cat_hint)
            item = NewsItem(**{
                **item.to_dict(),
                **meta,
                "message_dimension": dim,
                "category": category,
                "impact_scope": self._infer_impact_scope(text, "macro", source or "全球要闻"),
                "dedup_reason": "全球/国内要闻按事件标题+时间窗口合并，自动刷新时同事件不重复计分",
                "event_key": self._event_key(text, meta.get("event_label", "宏观政策"), self._parse_item_date(pub) or self._extract_date_from_text(text) or self._extract_date_from_url(url)),
                "industry_tags": self._industry_tags(text),
                "content_loaded": bool(r.get("_content_loaded")),
                "content_source": str(r.get("_content_source") or url),
                "content_quality_status": str(r.get("_content_quality_status") or "title_only"),
                "content_missing_reason": str(r.get("_content_missing_reason") or ""),
            })
            items.append(item)

        deduped = self._deduplicate(items)[:limit]
        enriched_items = self.event_intelligence.enrich_items([item.to_dict() for item in deduped])
        enriched_items = self.event_intelligence.collapse_event_clusters(enriched_items)[:limit]
        representative_keys = {
            (str(item.get("url") or item.get("source_ref") or ""), str(item.get("title") or ""))
            for item in enriched_items
        }
        representative_items = [
            item for item in deduped
            if (str(item.url or ""), str(item.title or "")) in representative_keys
        ]
        aggregate = self._aggregate("", "全球要闻", representative_items)
        domestic_count = sum(1 for x in enriched_items if str(x.get("message_dimension") or "").startswith("国内"))
        global_count = sum(1 for x in enriched_items if x.get("message_dimension") in {"国际消息/全球市场", "海外央行/全球利率", "外汇债券/美元美债"})
        commodity_count = sum(1 for x in enriched_items if x.get("category") in {"商品/原材料", "能源/原油", "贵金属/黄金"})
        result = {
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(enriched_items),
            "pre_cluster_count": len(deduped),
            **aggregate,
            "items": enriched_items,
            "domestic_count": domestic_count,
            "global_count": global_count,
            "commodity_count": commodity_count,
            "market_category_counts": self._counts([str(x.get("category") or "") for x in enriched_items]),
            "sources_used": sorted({source for item in enriched_items for source in (item.get("duplicate_sources") or [item.get("source")]) if source}),
            "sources_status": status,
            "cleaning_funnel": {
                "raw_candidates": len(raw_rows),
                "accepted_after_truth_rules": len(items),
                "deduplicated_events": len(deduped),
                "final_event_clusters": len(enriched_items),
                "rejected_count": max(0, len(raw_rows) - len(items)),
                "duplicate_or_clustered_count": max(0, len(items) - len(enriched_items)),
                "rule": "先校验真实来源和正文，再按事件去重；快讯用于早期发现，官方或多源证据用于确认。",
            },
            "event_radar": {
                "confirmed_count": sum(
                    1 for item in enriched_items
                    if item.get("score_candidate")
                ),
                "early_warning_count": sum(
                    1 for item in enriched_items
                    if item.get("early_warning_candidate")
                ),
                "candidate_block_count": sum(
                    1 for item in enriched_items if item.get("trade_gate") == "candidate_block"
                ),
                "display_only_count": sum(
                    1 for item in enriched_items if item.get("decision_use") == "display_only"
                ),
                "rule": "快讯负责尽早发现；官方原文或两个独立高可信来源负责确认。单一快讯只能预警，不能直接阻断或触发自动交易。",
            },
            "refresh_elapsed_ms": round((time.monotonic() - started_at) * 1000, 2),
            "refresh_budget_seconds": float(budget_seconds or 0.0),
            "source_policy": self.message_source_policy(),
            "cache_info": {"hit": False, "ttl_seconds": ttl_seconds, "force": force, "auto_refresh": True, "note": "全球/国内/商品/政策要闻短缓存，前端可自动刷新；个股公司信息仍按主动刷新/缓存策略处理。"},
            "note": "全球/国内要闻为多源快讯聚合，不等同于单只股票相关新闻；对个股影响通过公司主营、行业标签和产业链暴露进行映射。",
        }
        self._global_news_cache = result
        self._global_news_cache_ts = now
        self._last_global_source_status = [dict(row) for row in status]
        self._last_global_checked_at = str(result.get("updated_at") or "")
        return result

    def _bounded_value(self, fn, *, timeout: float, label: str = "外部来源") -> Any:
        """Run an optional provider with a hard caller-side deadline.

        Some third-party SDK functions do not honour requests timeouts.  A
        daemon worker lets the caller keep the results that already completed;
        any late value is discarded and cannot overwrite the response/cache.
        """
        import queue
        import threading

        result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def runner() -> None:
            try:
                result_queue.put_nowait((True, fn()))
            except Exception as exc:  # pragma: no cover - provider specific
                try:
                    result_queue.put_nowait((False, exc))
                except queue.Full:
                    pass

        worker = threading.Thread(target=runner, name=f"news-{label[:24]}", daemon=True)
        worker.start()
        try:
            ok, value = result_queue.get(timeout=max(0.05, float(timeout or 0.05)))
        except queue.Empty as exc:
            raise TimeoutError(f"{label}超过{max(0.05, float(timeout or 0.05)):.1f}秒未返回") from exc
        if not ok:
            raise value
        return value


    def _eastmoney_kuaixun_urls(self) -> dict[str, str]:
        return {
            "焦点": "https://kuaixun.eastmoney.com/yw.html",
            "全球": "https://kuaixun.eastmoney.com/qqgs.html",
            "中国": "https://kuaixun.eastmoney.com/dq_zg.html",
            "美国": "https://kuaixun.eastmoney.com/dq_mg.html",
            "外汇": "https://kuaixun.eastmoney.com/wh.html",
            "商品": "https://kuaixun.eastmoney.com/jjsj.html",
            "基金": "https://kuaixun.eastmoney.com/jj.html",
            "股市直播": "https://kuaixun.eastmoney.com/zhibo.html",
        }

    def _search_white_house_actions(self, limit: int = 30) -> list[dict[str, Any]]:
        """Read industry-relevant presidential actions from the official RSS."""
        feed_url = "https://www.whitehouse.gov/presidential-actions/feed/"
        response = self.policy_http.get(
            feed_url,
            headers={
                "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.5",
                "Referer": "https://www.whitehouse.gov/presidential-actions/",
                "User-Agent": "Mozilla/5.0",
            },
        )
        raw = response.content if getattr(response, "content", None) else response.text.encode("utf-8", "ignore")
        root = ET.fromstring(raw)
        relevant_terms = (
            "bulk-power", "electric grid", "inverter", "battery energy storage",
            "semiconductor", "artificial intelligence", "critical mineral",
            "export control", "sanction", "tariff", "trade", "technology",
            "energy", "financial market", "national emergency", "china",
        )
        rows: list[dict[str, Any]] = []
        for node in root.findall(".//item"):
            original_title = self._clean_text(node.findtext("title") or "")
            link = self._clean_text(node.findtext("link") or "")
            description_html = html_lib.unescape(node.findtext("description") or "")
            description = self._clean_text(re.sub(r"<[^>]+>", " ", description_html))
            haystack = f"{original_title} {description}".lower()
            if not original_title or not any(term in haystack for term in relevant_terms):
                continue
            published_raw = self._clean_text(node.findtext("pubDate") or "")
            published = published_raw
            if published_raw:
                try:
                    published = parsedate_to_datetime(published_raw).isoformat(timespec="seconds")
                except Exception:
                    pass

            title = original_title
            summary = description or original_title
            if "declaring a national emergency to secure the united states bulk-power system" in original_title.lower():
                title = "美国宣布国家紧急状态以保护大容量电力系统"
                summary = (
                    "白宫官方文件将公用事业级及其他并网逆变器、电池储能系统等列入大容量电力系统设备范围；"
                    "对涉及受覆盖外国实体且被认定构成安全风险的采购、进口、转让或安装可实施限制。"
                    "是否影响具体企业和订单仍取决于后续认定、许可及实施规则，并非对全部外国设备的一概禁令。"
                    f" 原文标题：{original_title}"
                )
            elif "adjusting imports of polysilicon" in original_title.lower():
                title = "美国调整多晶硅及其衍生品进口措施"
                summary = f"白宫发布多晶硅及其衍生品进口调整文件；措施范围和生效条件以官方原文为准。原文标题：{original_title}"
            else:
                title = f"美国白宫政策文件：{original_title}"
                summary = f"官方英文政策摘要：{description or original_title}"
            rows.append({
                "标题": title,
                "内容": summary,
                "发布时间": published,
                "链接": link,
                "_source_name": "美国白宫总统行动",
                "_category": "美国政策/产业安全",
                "_official_title": original_title,
                "_source_api": feed_url,
                "_source_page": "https://www.whitehouse.gov/presidential-actions/",
                "_content_loaded": True,
                "_content_source": link or feed_url,
                "_content_quality_status": "structured_excerpt",
            })
            if len(rows) >= max(1, int(limit or 30)):
                break
        return rows

    def _search_federal_register(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read recent market-relevant rules from the official public API."""
        api_url = "https://www.federalregister.gov/api/v1/documents.json"
        response = self.policy_http.get(
            api_url,
            params={"per_page": str(max(20, min(int(limit or 50), 100))), "order": "newest"},
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        payload = response.json()
        rows: list[dict[str, Any]] = []
        for raw in payload.get("results") or []:
            if not isinstance(raw, dict):
                continue
            title = self._clean_text(raw.get("title") or "")
            abstract = self._clean_text(raw.get("abstract") or "")
            agency_names = "、".join(
                self._clean_text(agency.get("name") or agency.get("raw_name") or "")
                for agency in (raw.get("agencies") or [])
                if isinstance(agency, dict)
            )
            probe = self.event_intelligence.enrich_item({
                "title": title,
                "summary": abstract,
                "source": "美国联邦公报",
                "url": raw.get("html_url") or "",
                "published_at": raw.get("publication_date") or "",
                "credibility_score": 99,
                "content_quality_status": "structured_excerpt" if abstract else "title_only",
            })
            if probe.get("event_type") == "general_information" and not probe.get("affected_industries_cn"):
                continue
            summary = abstract or f"美国联邦公报发布《{title}》；文件类型：{raw.get('type') or '官方文件'}；发布机构：{agency_names or '未列明'}。具体范围以官方原文为准。"
            rows.append({
                "标题": f"美国联邦公报：{title}",
                "内容": summary,
                "发布时间": raw.get("publication_date") or "",
                "链接": raw.get("html_url") or "",
                "_source_name": "美国联邦公报",
                "_category": "美国政策/监管规则",
                "_document_number": raw.get("document_number") or "",
                "_source_api": api_url,
                "_source_page": raw.get("html_url") or api_url,
                "_content_loaded": bool(abstract),
                "_content_source": raw.get("html_url") or api_url,
                "_content_quality_status": "structured_excerpt" if abstract else "title_only",
            })
        return rows

    def _search_eastmoney_kuaixun(self, url: str, category: str, limit: int = 80) -> list[dict[str, Any]]:
        """东方财富 7x24 快讯页面抽取。失败时返回空，不伪造数据。"""
        html = self.http.get(url, headers={"Referer": "https://kuaixun.eastmoney.com/", "User-Agent": "Mozilla/5.0"}).text
        rows = self._extract_generic_news_links(html, f"东方财富快讯-{category}", url, limit=limit)
        for r in rows:
            r["_category"] = category
        return rows

    def _global_message_dimension(self, text: str, source: str = "", category_hint: str = "") -> str:
        t = self._clean_text(f"{text} {source} {category_hint}")
        if any(w in t for w in ["美联储", "欧洲央行", "日本央行", "FOMC", "ECB", "BOJ", "加息", "降息", "利率决议", "会议纪要"]):
            return "海外央行/全球利率"
        if any(w in t for w in ["美元", "美债", "汇率", "外汇", "人民币", "日元", "欧元", "收益率", "债券"]):
            return "外汇债券/美元美债"
        if any(w in t for w in ["美国", "欧洲", "日本", "中东", "俄乌", "全球", "纳指", "道指", "标普", "OPEC", "海外"]):
            return "国际消息/全球市场"
        if any(w in t for w in ["中国", "国内", "央行", "财政部", "国家统计局", "发改委", "工信部", "证监会", "A股", "沪指", "创业板"]):
            return "国内宏观/A股市场"
        if any(w in t for w in ["原油", "黄金", "铜", "铝", "煤炭", "铁矿", "螺纹", "期货", "商品", "大宗"]):
            return "大宗商品/原材料"
        return self._message_dimension(t, "macro", source)

    def _global_market_category(self, text: str, category_hint: str = "") -> str:
        t = self._clean_text(f"{text} {category_hint}")
        if any(w in t for w in ["原油", "WTI", "布伦特", "OPEC", "汽油", "油价"]):
            return "能源/原油"
        if any(w in t for w in ["黄金", "金价", "白银", "贵金属"]):
            return "贵金属/黄金"
        if any(w in t for w in ["铜", "铝", "锂", "镍", "煤炭", "铁矿", "螺纹", "焦煤", "焦炭", "商品", "期货"]):
            return "商品/原材料"
        if any(w in t for w in ["美联储", "欧洲央行", "日本央行", "降息", "加息", "LPR", "央行", "逆回购", "社融", "M2"]):
            return "利率/流动性"
        if any(w in t for w in ["关税", "制裁", "贸易摩擦", "出口管制", "地缘", "冲突", "战争"]):
            return "地缘/贸易"
        if any(w in t for w in ["光伏", "新能源", "锂电", "半导体", "AI", "算力", "机器人", "低空", "医药", "军工"]):
            return "产业/行业政策"
        if any(w in t for w in ["A股", "沪指", "创业板", "港股", "美股", "纳指", "道指", "标普"]):
            return "股市/风险偏好"
        return category_hint or "全球/国内要闻"

    def _canonical_event_text(self, text: str) -> str:
        s = self._clean_text(text)
        s = re.sub(r"阅读评论标题作者最后更新|class=|listitem|listit|<tr|</tr|<div|</div", " ", s, flags=re.I)
        s = re.sub(r"\d{1,8}\s*阅读|\d{1,8}\s*评论", " ", s)
        s = re.sub(r"\b\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}\b", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        # 保留标题前 120 字足够表达事件，避免股吧整页表格污染事件键。
        return s[:120]

    def _dedup_fingerprint(self, text: str) -> str:
        s = self._canonical_event_text(text).lower()
        # 去除常见时间和标点，让“同一股东大会/同一财报事件”的转载合并。
        s = re.sub(r"20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?", "DATE", s)
        s = re.sub(r"\d{1,2}:\d{2}(?::\d{2})?", "TIME", s)
        s = re.sub(r"[\W_]+", "", s)
        return hashlib.md5(s[:96].encode("utf-8")).hexdigest()[:16]

    def _similar_title(self, a: str, b: str) -> bool:
        ca = re.sub(r"[\W_]+", "", self._canonical_event_text(a))
        cb = re.sub(r"[\W_]+", "", self._canonical_event_text(b))
        if not ca or not cb:
            return False
        if ca in cb or cb in ca:
            return min(len(ca), len(cb)) >= 10
        sa = set(ca[i:i+2] for i in range(max(0, len(ca)-1)))
        sb = set(cb[i:i+2] for i in range(max(0, len(cb)-1)))
        if not sa or not sb:
            return False
        j = len(sa & sb) / max(1, len(sa | sb))
        return j >= 0.72


    def _extract_global_json_rows(self, data: Any, source_name: str, limit: int = 80) -> list[dict[str, Any]]:
        """从不同快讯 JSON 结构中递归提取标题/正文/时间。"""
        rows: list[dict[str, Any]] = []
        title_keys = {"title", "content", "summary", "brief", "digest", "content_text", "text"}
        time_keys = {"display_time", "created_at", "updated_at", "time", "pub_time", "publish_time", "ctime"}
        url_keys = {"url", "uri", "share_url", "source_url"}

        def norm_time(v: Any) -> str:
            if v is None:
                return ""
            try:
                fv = float(v)
                if fv > 10_000_000_000:
                    return datetime.fromtimestamp(fv / 1000).isoformat(timespec="seconds")
                if fv > 1_000_000_000:
                    return datetime.fromtimestamp(fv).isoformat(timespec="seconds")
            except Exception:
                pass
            return self._clean_text(str(v))

        def walk(x: Any):
            if len(rows) >= limit:
                return
            if isinstance(x, dict):
                text = ""
                for k in title_keys:
                    if x.get(k):
                        text = self._clean_text(str(x.get(k)))
                        if text:
                            break
                if text and not self._is_noise_title(text):
                    pub = ""
                    for k in time_keys:
                        if x.get(k) is not None:
                            pub = norm_time(x.get(k))
                            break
                    url = ""
                    for k in url_keys:
                        if x.get(k):
                            url = self._clean_text(str(x.get(k)))
                            break
                    ok, _reason = self.valid_news_item(text, text, source=source_name, url=url, source_type="macro", allow_macro=True)
                    if ok:
                        rows.append({"标题": text[:160], "内容": text, "发布时间": pub, "链接": url, "_source_name": source_name})
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(data)
        return rows[:limit]



    def _search_jin10_flash(self, limit: int = 80) -> list[dict[str, Any]]:
        """金十/金十期货全球 7x24 快讯尝试。

        说明：金十页面多为前端动态加载，公开接口可能调整或加防护。这里同时尝试
        flash-api JSON 与 xnews/qihuo 页面静态摘要；失败只记录诊断，不伪造数据。
        """
        limit = max(10, min(int(limit or 80), 200))
        rows: list[dict[str, Any]] = []
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Origin": "https://www.jin10.com",
            "Referer": "https://www.jin10.com/",
            # 常见金十前端接口头；若未来变更，异常会被外层 sources_status 捕获。
            "x-app-id": "SO1EJGmNgCtmpcPF",
            "x-version": "1.0.0",
        }
        api_candidates = [
            ("金十数据7x24", "https://flash-api.jin10.com/get_flash_list", {"channel": "-8200", "vip": "1"}),
            ("金十数据市场快讯", "https://flash-api.jin10.com/get_flash_list", {"channel": "-8200"}),
            ("金十期货快讯", "https://flash-api.jin10.com/get_flash_list", {"channel": "-1", "vip": "1"}),
            ("金十期货页面快讯", "https://flash-api.jin10.com/get_flash_list", {"channel": "-1"}),
        ]
        for src, url, params in api_candidates:
            if len(rows) >= limit:
                break
            try:
                resp = self.http.get(url, params=params, headers=headers)
                response_text = (
                    resp.content.decode("utf-8", "replace")
                    if getattr(resp, "content", None)
                    else resp.text
                )
                data = self._decode_jsonish(response_text)
                extracted = self._extract_jin10_flash_rows(data, src, limit=limit-len(rows)) if data is not None else []
                for r in extracted:
                    r["_source_name"] = src
                    r["_source_api"] = url
                    r["_source_page"] = "https://qihuo.jin10.com/" if "期货" in src else "https://www.jin10.com/"
                    key = re.sub(r"\W+", "", str(r.get("标题") or r.get("内容") or ""))[:120]
                    if key and not any(re.sub(r"\W+", "", str(x.get("标题") or x.get("内容") or ""))[:120] == key for x in rows):
                        rows.append(r)
                # The endpoint already returns a latest-page batch. Continuing
                # through near-identical channel variants adds seconds but
                # mostly duplicates the same events.
                if rows:
                    break
            except Exception:
                continue
        # HTML 摘要兜底：xnews/jin10 与 qihuo 首页常能返回最新标题片段。
        html_candidates = [("金十市场参考", "https://xnews.jin10.com/"), ("金十期货", "https://qihuo.jin10.com/")]
        for src, url in (html_candidates if not rows else []):
            if len(rows) >= limit:
                break
            try:
                html = self.http.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": url}).text
                for r in self._extract_generic_news_links(html, src, url, limit=limit-len(rows)):
                    rows.append(r)
            except Exception:
                continue
        return rows[:limit]

    def _extract_jin10_flash_rows(self, data: Any, source_name: str, limit: int = 80) -> list[dict[str, Any]]:
        """Extract Jin10 flash rows while preserving parent timestamp and de-duplicating content."""
        container = data.get("data") if isinstance(data, dict) else data
        if not isinstance(container, list):
            return self._extract_global_json_rows(data, source_name, limit=limit)
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in container:
            if len(rows) >= limit:
                break
            if not isinstance(item, dict):
                continue
            payload = item.get("data") if isinstance(item.get("data"), dict) else {}
            text = (
                payload.get("content")
                or payload.get("title")
                or payload.get("summary")
                or item.get("content")
                or item.get("title")
                or item.get("summary")
                or ""
            )
            text = html_lib.unescape(str(text))
            text = re.sub(r"(?i)<br\s*/?>", "\n", text)
            text = re.sub(r"<[^>]+>", "", text)
            text = self._clean_text(text)
            if not text or self._is_noise_title(text):
                continue
            title = text
            bracket = re.match(r"^【([^】]{4,120})】\s*(.*)$", text)
            if bracket:
                title = bracket.group(1).strip()
                summary = bracket.group(2).strip() or text
            else:
                summary = text
            source_item_id = str(item.get("id") or payload.get("id") or "").strip()
            source_link = str(payload.get("source_link") or payload.get("url") or item.get("url") or "")
            if not source_link and source_item_id:
                source_link = f"https://flash.jin10.com/detail/{source_item_id}"
            pub = str(item.get("time") or payload.get("time") or item.get("created_at") or "")
            real_source = str(payload.get("source") or source_name or "金十快讯").strip() or source_name
            ok, _reason = self.valid_news_item(title, summary, source=real_source, url=source_link, source_type="macro", allow_macro=True)
            if not ok:
                event_probe = self.event_intelligence.enrich_item({
                    "title": title,
                    "summary": summary,
                    "source": real_source or source_name,
                    "url": source_link,
                    "published_at": pub,
                    "content_quality_status": "structured_excerpt",
                })
                if (
                    event_probe.get("event_type") == "general_information"
                    or event_probe.get("source_tier") not in {"official_primary", "trusted_media", "fast_alert"}
                ) and ("金十" not in real_source or len(title) < 8):
                    continue
            key = re.sub(r"\W+", "", title + summary)[:160]
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "标题": title[:180],
                    "内容": summary[:600],
                    "发布时间": pub,
                    "链接": source_link,
                    "_source_name": real_source,
                    "_source_channel": source_name,
                    "_source_item_id": source_item_id,
                    "_source_page": "https://qihuo.jin10.com/" if "期货" in source_name else "https://www.jin10.com/",
                    "_content_loaded": True,
                    "_content_source": source_link or "https://www.jin10.com/",
                    "_content_quality_status": "structured_excerpt",
                }
            )
        return rows[:limit]

    def _extract_generic_news_links(self, html: str, source: str, base_url: str, limit: int = 80) -> list[dict[str, Any]]:
        """从财经资讯首页中抽取通用新闻标题，不要求个股相关。"""
        html = html or ""
        out: list[dict[str, Any]] = []
        pattern = re.compile(r'<a\b(?P<attrs1>[^>]*)href=["\'](?P<href>[^"\']+)["\'](?P<attrs2>[^>]*)>(?P<body>.*?)</a>', re.I | re.S)
        for m in pattern.finditer(html):
            body = re.sub(r"<.*?>", "", m.group("body") or "")
            attrs = (m.group("attrs1") or "") + " " + (m.group("attrs2") or "")
            title_attr = ""
            tm = re.search(r'title=["\']([^"\']+)["\']', attrs, flags=re.I)
            if tm:
                title_attr = tm.group(1)
            title = self._clean_text(body) or self._clean_text(title_attr)
            href = m.group("href") or ""
            ok, _reason = self.valid_news_item(title, "", source=source, url=urljoin(base_url, href), source_type="macro", allow_macro=True)
            if not ok:
                continue
            if len(title) > 160:
                title = title[:160]
            if href.startswith("//"):
                href = "https:" + href
            link = urljoin(base_url, href)
            if self._is_search_result_url(link):
                continue
            ctx_html = html[max(0, m.start()-260): min(len(html), m.end()+500)]
            ctx = self._clean_text(ctx_html)
            pub = self._extract_date_text(ctx) or ""
            out.append({"标题": title, "内容": title, "发布时间": pub, "链接": link, "_source_name": source})
            if len(out) >= limit:
                break
        return out

    def _search_sina_stock_news(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        """新浪个股新闻页。站内搜索经常返回空，优先用股票专页。"""
        prefix = "sh" if normalize_symbol(symbol).startswith(("5", "6", "9")) else "sz"
        candidates = [
            f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{prefix}{normalize_symbol(symbol)}.phtml",
            f"https://finance.sina.com.cn/realstock/company/{prefix}{normalize_symbol(symbol)}/nc.shtml",
        ]
        out: list[NewsItem] = []
        for url in candidates:
            try:
                html = self.http.get(url, headers={"Referer": "https://finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"}).text
                got = self._extract_links(html, symbol, name, source="新浪个股新闻", source_type="news", limit=limit-len(out), base_url=url, base_relevant=True, strict_article=True, deep_validate=True)
                out.extend(got)
            except Exception:
                continue
            if len(out) >= limit:
                break
        return out[:limit]

    def _search_10jqka_stock_news(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        """同花顺个股资讯页。"""
        url = f"https://stockpage.10jqka.com.cn/{normalize_symbol(symbol)}/news/"
        try:
            html = self.http.get(url, headers={"Referer": "https://stockpage.10jqka.com.cn/", "User-Agent": "Mozilla/5.0"}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="同花顺个股资讯", source_type="news", limit=limit, base_url=url, base_relevant=True, strict_article=True, deep_validate=True)

    def _item_from_dict(self, d: dict[str, Any]) -> NewsItem:
        title = self._clean_text(str(d.get("title") or ""))[:180]
        summary = self._clean_text(str(d.get("summary") or ""))[:300]
        content_loaded = bool(d.get("content_loaded"))
        content_quality_status = str(d.get("content_quality_status") or ("full_text" if content_loaded else "title_only"))
        content_missing_reason = str(d.get("content_missing_reason") or "")
        boilerplate_rejected = False
        if self._looks_like_page_chrome(summary):
            summary = ""
            content_loaded = False
            content_quality_status = "boilerplate_rejected"
            content_missing_reason = "缓存正文仅包含网页导航或免责声明，已拒绝参与正文评分"
            boilerplate_rejected = True
        source_type = str(d.get("source_type") or "news")
        meta = self._classify_event(f"{title} {summary}")
        title_meta = self._classify_event(title)
        title_sentiment, title_evidence = self._rule_sentiment(title, source_type, title_meta)
        title_impact = min(100.0, sum(12 for word in self.IMPACT_WORDS if word in title))
        if title_meta.get("event_label") not in {"一般资讯", "宏观政策"}:
            title_impact = max(title_impact, 55.0)
        time_meta = extract_time_fields(d.get("published_at") or d.get("publish_time"), title, summary, str(d.get("url") or ""), source_type=source_type)
        return NewsItem(
            title=title,
            url=str(d.get("url") or ""),
            source=str(d.get("source") or "本地信息库"),
            source_type=source_type,
            published_at=d.get("published_at") or d.get("publish_time") or None,
            published_at_norm=d.get("published_at_norm") or d.get("publish_time") or None,
            date_display=d.get("date_display") or d.get("publish_time") or d.get("published_at_norm") or d.get("published_at") or None,
            publish_time=d.get("publish_time") or time_meta.get("publish_time"),
            event_time=d.get("event_time") or time_meta.get("event_time"),
            crawl_time=d.get("crawl_time") or time_meta.get("crawl_time"),
            time_confidence=str(d.get("time_confidence") or time_meta.get("time_confidence") or ""),
            time_basis=str(d.get("time_basis") or time_meta.get("time_basis") or ""),
            event_type=str(d.get("event_type") or time_meta.get("event_type") or "general_news"),
            issuer=str(d.get("issuer") or ""),
            period=str(d.get("period") or time_meta.get("period") or ""),
            document_id=str(d.get("document_id") or time_meta.get("document_id") or document_id_from_url(str(d.get("url") or ""))),
            summary=summary,
            relevance_score=float(d.get("relevance_score") or 0),
            sentiment_score=round(title_sentiment, 2) if boilerplate_rejected else float(d.get("sentiment_score") or 50),
            credibility_score=float(d.get("credibility_score") or 40),
            impact_score=round(title_impact, 2) if boilerplate_rejected else float(d.get("impact_score") or 0),
            fake_risk_score=float(d.get("fake_risk_score") or 0),
            category=self._category(title, source_type) if boilerplate_rejected else str(d.get("category") or "其他信息"),
            message_dimension=str(d.get("message_dimension") or self._message_dimension(f"{title} {summary}", source_type, str(d.get("source") or ""))),
            event_label=str(title_meta.get("event_label") or "一般资讯") if boilerplate_rejected else str(d.get("event_label") or meta.get("event_label") or "一般资讯"),
            sentiment_label=str(title_meta.get("sentiment_label") or "中性") if boilerplate_rejected else str(d.get("sentiment_label") or meta.get("sentiment_label") or "中性"),
            impact_scope=str(d.get("impact_scope") or self._infer_impact_scope(f"{title} {summary}", source_type, str(d.get("source") or ""))),
            impact_direction=str(title_meta.get("impact_direction") or "中性/待观察") if boilerplate_rejected else str(d.get("impact_direction") or meta.get("impact_direction") or "中性/待观察"),
            risk_tag=str(title_meta.get("risk_tag") or "") if boilerplate_rejected else str(d.get("risk_tag") or meta.get("risk_tag") or ""),
            duplicate_group=str(d.get("duplicate_group") or self._fingerprint(title)),
            event_key=str(d.get("event_key") or ""),
            event_weight=float(d.get("event_weight") or 1.0),
            recency_weight=float(d.get("recency_weight") or 1.0),
            dedup_reason=str(d.get("dedup_reason") or ""),
            industry_tags=d.get("industry_tags") if isinstance(d.get("industry_tags"), list) else None,
            evidence=title_evidence if boilerplate_rejected else d.get("evidence") if isinstance(d.get("evidence"), list) else None,
            content_loaded=content_loaded,
            target_relation=str(d.get("target_relation") or ""),
            relation_confidence=float(d.get("relation_confidence") or 0),
            relation_note=str(d.get("relation_note") or ""),
            attachment_url=str(d.get("attachment_url") or ""),
            content_source=str(d.get("content_source") or ""),
            content_quality_status=content_quality_status,
            content_missing_reason=content_missing_reason,
            content_hash=str(d.get("content_hash") or ""),
            duplicate_count=max(1, int(d.get("duplicate_count") or 1)),
            duplicate_sources=d.get("duplicate_sources") if isinstance(d.get("duplicate_sources"), list) else None,
            duplicate_source_refs=d.get("duplicate_source_refs") if isinstance(d.get("duplicate_source_refs"), list) else None,
        )

    def _search_all(self, query: str, symbol: str, name: str, limit: int, mode: str = "light") -> list[NewsItem]:
        """多中文源、多关键词、按“有效证据数”扩展抓取。

        V16.3 不再用“原始抓到多少条”决定是否停止，而是先估算有效证据数。
        当结构化源原始返回很多但有效条目不足时，继续启用专业媒体/站内源补充；
        但百度/360/搜狗搜索结果页仍然彻底禁用。
        """
        items: list[NewsItem] = []
        limit = max(30, min(int(limit or 120), 500))
        mode_raw = str(mode or "light").lower()
        mode = "deep" if mode_raw in {"deep", "deep_refresh", "full"} else "normal" if mode_raw in {"normal", "detail"} else "light"
        target_valid = min(limit, 30) if mode == "light" else min(limit, max(70, int(limit * 0.68))) if mode == "deep" else min(limit, 90)
        per_source = max(30, min(90, int(limit * 0.45)))
        industry_queries = self._industry_queries(symbol, name)
        queries = list(dict.fromkeys([
            query,
            f"{name} {symbol} 公告",
            f"{name} {symbol} 业绩 财报",
            f"{name} {symbol} 研报 评级 目标价",
            f"{name} {symbol} 政策 行业 产业链",
            f"{name} {symbol} 风险 问询 处罚 减持 诉讼",
            *industry_queries,
        ]))

        official_limit = max(30, per_source) if mode == "light" else max(60, per_source)
        factual_sources = [
            ("东方财富公告接口", self._search_eastmoney_ann, (symbol, name, official_limit)),
            ("巨潮公告全文检索", self._search_cninfo_fulltext, (symbol, name, max(70, per_source))),
            ("东方财富F10资讯公告", self._search_eastmoney_hsf10, (symbol, name, max(50, per_source))),
        ]
        if mode in {"normal", "deep"}:
            factual_sources.extend([
                ("新浪个股新闻页", self._search_sina_stock_news, (symbol, name, max(35, min(80, per_source)))),
                ("同花顺个股资讯页", self._search_10jqka_stock_news, (symbol, name, max(35, min(80, per_source)))),
            ])
        for source_name, fn, args in factual_sources:
            if self._budget_exhausted():
                self._record_budget_exhausted()
                break
            got = self._run_source_call(source_name, fn, args)
            items.extend(got)
            if got:
                self._record_source(source_name, len(got), "ok")
            elif not self._source_circuit_open(source_name):
                self._record_source(source_name, 0, "无有效条目/页面结构可能变化")
            if mode == "light" and self._valid_count_estimate(items, symbol=symbol, name=name) >= target_valid:
                self._record_source("light mode官方源短路", len(items), "官方公告已经满足轻量筛选证据量，跳过较慢的后续来源")
                break

        valid_est = self._valid_count_estimate(items, symbol=symbol, name=name)
        self._record_source("有效证据预估", valid_est, f"目标有效证据≈{target_valid}；按清洗准入后条目而不是原始条目判断是否继续补充")
        if mode == "light" and valid_est >= target_valid:
            self._record_source("light mode停止补源", valid_est, f"官方公告有效证据已达{target_valid}，筛选页立即停止补源")
            return items[: max(limit * 3, limit)]

        # 专业财经媒体/站内源补充：只有当“有效条目”不足才启用；每个源仍走 URL/正文准入，不把搜索页当新闻证据。
        if mode == "light":
            self._record_source("light mode站内搜索关闭", valid_est, "筛选页不运行东方财富/新浪/同花顺/专业财经门户关键词矩阵", skipped_reason="light mode禁用关键词矩阵")
        elif mode == "normal":
            self._record_source("normal mode关键词矩阵关闭", valid_est, "普通详情刷新只使用官方源和常规个股新闻页，不运行关键词矩阵", skipped_reason="normal mode禁用关键词矩阵")
        elif valid_est < target_valid:
            self._record_source("专业媒体补充", 0, f"有效证据不足 {valid_est}/{target_valid}，继续抓取财经门户/研报/行业线索")
            fallback_queries = list(dict.fromkeys([query, f"{name} 公告", f"{name} 业绩", f"{name} 研报", f"{name} 行业 政策", f"{name} 风险", *industry_queries]))[:8]
            search_fns = [
                ("东方财富站内搜索", self._search_eastmoney_page),
                ("新浪财经站内搜索", self._search_sina_page),
                ("同花顺站内搜索", self._search_10jqka_page),
                ("专业财经门户", self._search_professional_portals),
            ]
            finance_media_count = 0
            for q in fallback_queries:
                if self._budget_exhausted():
                    self._record_budget_exhausted()
                    break
                if self._valid_count_estimate(items, symbol=symbol, name=name) >= target_valid or len(items) >= limit * 3 or finance_media_count >= self.finance_media_limit:
                    break
                for source_name, fn in search_fns:
                    if self._budget_exhausted():
                        self._record_budget_exhausted()
                        break
                    if self._valid_count_estimate(items, symbol=symbol, name=name) >= target_valid or len(items) >= limit * 3 or finance_media_count >= self.finance_media_limit:
                        break
                    per_call = max(8, min(24, per_source // 3, self.finance_media_limit - finance_media_count))
                    got = self._run_source_call(f"{source_name}:{q[:16]}", fn, (q, symbol, name, per_call))
                    items.extend(got)
                    finance_media_count += len(got)
                    self._record_source(f"{source_name}:{q[:16]}", len(got), "ok" if got else "无有效新闻链接")
        else:
            self._record_source("站内/门户补充", 0, f"已跳过：结构化源有效证据已达 {valid_est}/{target_valid}")

        # 社区舆情单独补充，按舆情统计和传闻风险处理，不作为公司事实。
        community_sources = [
            ("东方财富股吧", self._search_eastmoney_guba, (symbol, name, max(8, min(self.community_limit, 45, limit // 4)))),
            ("雪球/社区", self._search_xueqiu_page, (query, symbol, name, max(8, min(self.community_limit, 30, limit // 5)))),
        ]
        for source_name, fn, args in community_sources:
            if self._budget_exhausted():
                self._record_budget_exhausted()
                break
            got = self._run_source_call(source_name, fn, args)
            items.extend(got[: self.community_limit])
            self._record_source(source_name, min(len(got), self.community_limit), "ok" if got else "无有效舆情条目")

        return items[: max(limit * 3, limit)]

    def _valid_count_estimate(self, items: list[NewsItem], symbol: str = "", name: str = "") -> int:
        seen: set[str] = set()
        count = 0
        for item in items or []:
            ok, _ = self.valid_news_item(
                item.title, item.summary, source=item.source, url=item.url, symbol=symbol, name=name,
                source_type=item.source_type, base_relevant=item.relevance_score >= 20,
                allow_macro=item.source_type in {"macro", "policy", "global"},
            )
            if not ok:
                continue
            key = item.event_key or item.document_id or item.duplicate_group or self._dedup_fingerprint(f"{item.title} {item.url}")
            if key in seen:
                continue
            seen.add(key)
            count += 1
        return count

    def _search_professional_portals(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        """专业财经门户补充。

        这里抓的是各门户自己的搜索/列表页中的真实文章链接；不是百度/360/搜狗结果页。
        失败只记录0条，不伪造新闻。
        """
        portals = [
            ("财联社", "https://www.cls.cn/searchPage", {"keyword": query}),
            ("证券时报", "https://www.stcn.com/search", {"keyword": query}),
            ("中证网", "https://www.cs.com.cn/search/", {"key": query}),
            ("上海证券报", "https://search.cnstock.com/search", {"searchword": query}),
            ("每日经济新闻", "https://www.nbd.com.cn/search/articles/", {"keyword": query}),
            ("第一财经", "https://www.yicai.com/search", {"keys": query}),
        ]
        out: list[NewsItem] = []
        for source, url, params in portals:
            if len(out) >= limit:
                break
            try:
                html = self.http.get(url, params=params, headers={"Referer": url, "User-Agent": "Mozilla/5.0"}).text
            except Exception:
                continue
            got = self._extract_links(
                html, symbol, name, source=source, source_type="news", limit=limit-len(out),
                base_url=url, base_relevant=False, strict_article=True, deep_validate=False,
            )
            out.extend(got)
        return out[:limit]

    def _industry_queries(self, symbol: str, name: str) -> list[str]:
        text = f"{name} {symbol}"
        mapping = {
            "电池新能源": (["宁德", "比亚迪", "亿纬", "国轩", "天齐", "赣锋", "电池", "锂", "储能", "光伏", "新能源"], ["固态电池 政策", "动力电池 产业", "储能 政策", "新能源汽车 产业链"]),
            "军工国防": (["军工", "长城军工", "中航", "兵器", "航天", "国防", "弹药", "舰船"], ["军工 政策", "国防军工 产业", "兵器装备 重组", "军民融合 政策"]),
            "AI半导体": (["AI", "人工智能", "芯片", "半导体", "算力", "数据中心", "机器人"], ["人工智能 政策", "算力 产业", "半导体 政策", "机器人 产业"]),
            "医药消费": (["医药", "医疗", "药", "消费", "白酒", "食品"], ["医药 政策", "集采 政策", "消费 政策", "白酒 行业"]),
            "ETF宏观": (["ETF", "沪深300", "创业板", "中证", "上证", "深证"], ["ETF 资金流", "指数基金 政策", "沪深300 资金", "宽基ETF"]),
        }
        out: list[str] = []
        for _, (keys, queries) in mapping.items():
            if any(k in text for k in keys):
                out.extend([f"{name} {q}" for q in queries])
        return out[:8]

    def valid_news_item(self, title: str, summary: str = "", source: str = "", url: str = "", symbol: str = "", name: str = "", source_type: str = "news", base_relevant: bool = False, allow_macro: bool = False) -> tuple[bool, str]:
        return _valid_news_item(title, summary, source=source, url=url, symbol=symbol, name=name, source_type=source_type, base_relevant=base_relevant, allow_macro=allow_macro)

    def _filter_valid_items(self, items: list[NewsItem], symbol: str = "", name: str = "", allow_macro: bool = False) -> list[NewsItem]:
        out: list[NewsItem] = []
        rejects: dict[tuple[str, str], int] = {}
        seen_keys: set[str] = set()
        duplicate_count = 0
        for item in items:
            ok, reason = self.valid_news_item(
                item.title, item.summary, source=item.source, url=item.url, symbol=symbol, name=name,
                source_type=item.source_type, base_relevant=item.relevance_score >= 20,
                allow_macro=allow_macro or item.source_type in {"macro", "policy", "global"},
            )
            if ok:
                # 详情页/缓存合并前先做一次硬去重，防止旧库里同一 event_key 以不同 duplicate_group 重复展示。
                k = item.event_key or item.duplicate_group or self._dedup_fingerprint(f"{item.title} {item.url}")
                if k in seen_keys:
                    duplicate_count += 1
                    continue
                seen_keys.add(k)
                out.append(item)
            else:
                key = (item.source or "未知来源", reason)
                rejects[key] = rejects.get(key, 0) + 1
        for (source, reason), count in sorted(rejects.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:40]:
            self._record_source(f"清洗丢弃:{source}", count, reason)
        rejection_reasons: dict[str, int] = {}
        for (_source, reason), count in rejects.items():
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + count
        self._last_cleaning_funnel = {
            "raw_candidates": len(items),
            "accepted_after_truth_rules": len(out),
            "rejected_count": sum(rejects.values()),
            "duplicate_count": duplicate_count,
            "rejection_reasons": dict(sorted(rejection_reasons.items(), key=lambda row: (-row[1], row[0]))),
            "rule": "搜索结果页、页面导航、脚本残片和无关内容先丢弃；同一事件只保留一组可追溯证据。",
        }
        return out

    def _log_progress(self, message: str) -> None:
        try:
            print(f"[信息面] {time.strftime('%H:%M:%S')} {message}", flush=True)
        except Exception:
            pass

    def _record_source(self, source: str, count: int, status: str, *, elapsed_ms: float | None = None, skipped_reason: str | None = None) -> None:
        text = f"{source} {status}"
        if any(k in text for k in ["搜索引擎", "搜索结果页", "搜索页", "百度搜索", "360搜索", "搜狗搜索"]):
            return
        self._source_status.append({
            "source": source,
            "count": int(count),
            "status": status,
            "elapsed_ms": round(float(elapsed_ms), 2) if elapsed_ms is not None else None,
            "skipped_reason": skipped_reason,
            "mode": self._current_mode,
        })
        # 控制台展示抓取进度，方便判断是不是卡在某个新闻源。
        if len(self._source_status) <= 80:
            self._log_progress(f"源[{source}] 返回 {int(count)} 条，状态={status}")

    def _source_key(self, source: str) -> str:
        return str(source or "").split(":", 1)[0].strip() or str(source or "")

    def _budget_remaining(self) -> float | None:
        if not self._round_budget_seconds or not self._round_started_at:
            return None
        return max(0.0, self._round_budget_seconds - (time.monotonic() - self._round_started_at))

    def _budget_exhausted(self) -> bool:
        remaining = self._budget_remaining()
        return remaining is not None and remaining <= 0.05

    def _record_budget_exhausted(self) -> None:
        if self._budget_exhausted_recorded:
            return
        self._budget_exhausted_recorded = True
        self._record_source("总预算耗尽", 0, "总预算耗尽，停止后续任务队列", skipped_reason="budget_exhausted")

    def _source_circuit_open(self, source: str) -> bool:
        opened = self._source_circuit_opened_at.get(self._source_key(source))
        if not opened:
            return False
        return (time.time() - opened) < 120

    def _mark_source_failure(self, source: str) -> None:
        key = self._source_key(source)
        self._source_failures[key] = self._source_failures.get(key, 0) + 1
        if self._source_failures[key] >= 1:
            self._source_circuit_opened_at[key] = time.time()

    def _mark_source_success(self, source: str) -> None:
        key = self._source_key(source)
        self._source_failures.pop(key, None)
        self._source_circuit_opened_at.pop(key, None)

    def _run_source_call(self, source_name: str, fn, args: tuple) -> list[NewsItem]:
        if self._source_circuit_open(source_name):
            self._record_source(source_name, 0, "熔断中，跳过本轮", skipped_reason="source_circuit_open")
            return []
        if self._budget_exhausted():
            self._record_budget_exhausted()
            return []
        timeout = 5.0 if (self._round_budget_seconds or 0) >= 8.0 else self.source_timeout_seconds
        remaining = self._budget_remaining()
        if remaining is not None:
            timeout = max(0.1, min(timeout, remaining))
        executor = ThreadPoolExecutor(max_workers=1)
        started = time.monotonic()
        future = executor.submit(fn, *args)
        try:
            got = future.result(timeout=timeout)
            self._mark_source_success(source_name)
            elapsed = (time.monotonic() - started) * 1000
            if self._budget_exhausted():
                self._record_budget_exhausted()
            return list(got or [])
        except TimeoutError:
            self._mark_source_failure(source_name)
            self._record_source(source_name, 0, f"源级超时>{timeout:.1f}s", elapsed_ms=(time.monotonic() - started) * 1000, skipped_reason="timeout")
            return []
        except Exception as exc:
            self._mark_source_failure(source_name)
            self._record_source(source_name, 0, str(exc)[:180], elapsed_ms=(time.monotonic() - started) * 1000, skipped_reason="error")
            return []
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _em_code(self, symbol: str) -> str:
        ex = infer_exchange(symbol)
        prefix = {"SH": "SH", "SZ": "SZ", "BJ": "BJ"}.get(ex, "SZ")
        return f"{prefix}{normalize_symbol(symbol)}"

    def _search_eastmoney_hsf10(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        code = self._em_code(symbol)
        out: list[NewsItem] = []
        # 该接口经常随网页改名，因此同时尝试主域和 securities 子域，解析JSON/JSONP/HTML均可。
        candidates = [
            ("https://emweb.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax", {"code": code}),
            ("https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax", {"code": code}),
            ("https://emweb.eastmoney.com/PC_HSF10/NewsBulletin/Index", {"code": code, "type": "web"}),
        ]
        for url, params in candidates:
            try:
                text = self.http.get(url, params=params, headers={"Referer": f"https://emweb.eastmoney.com/PC_HSF10/NewsBulletin/Index?code={code}&type=web"}).text
            except Exception:
                continue
            data = self._decode_jsonish(text)
            if data is not None:
                rows = self._extract_json_items(data)
                for row in rows:
                    title = self._clean_text(row.get("title") or "")
                    link = row.get("url") or ""
                    pub = row.get("date") or row.get("time") or None
                    source_type = "announcement" if any(w in title for w in ["公告", "报告书", "年报", "季报", "问询", "函"]) else "news"
                    summary = row.get("summary") or ""
                    ok, _reason = self.valid_news_item(title, summary, source="东方财富F10", url=link, symbol=symbol, name=name, source_type=source_type, base_relevant=True)
                    if not ok or not self._is_relevant_title(title, symbol, name, base_relevant=True):
                        continue
                    out.append(self._score_item(title, link, "东方财富F10", pub, summary, symbol, name, source_type=source_type))
            else:
                out.extend(self._extract_links(text, symbol, name, source="东方财富F10", source_type="news", limit=limit, base_url=url, base_relevant=True))
            if len(out) >= limit:
                break
        return out[:limit]

    def _search_eastmoney_ann(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        out: list[NewsItem] = []
        page_size = min(80, max(30, limit))
        max_pages = max(1, min(4, (limit + page_size - 1) // page_size + 1))
        seen: set[str] = set()
        for page_index in range(1, max_pages + 1):
            try:
                data = self.http.get(url, params={
                    "sr": "-1", "page_size": str(page_size), "page_index": str(page_index), "ann_type": "A",
                    "client_source": "web", "stock_list": normalize_symbol(symbol), "f_node": "0", "s_node": "0",
                }, headers={"Referer": "https://data.eastmoney.com/"}).json()
            except Exception:
                break
            rows = (((data or {}).get("data") or {}).get("list") or [])
            if not rows:
                break
            for row in rows:
                title = self._clean_text(row.get("title") or row.get("notice_title") or "")
                art_code = str(row.get("art_code") or row.get("notice_id") or "")
                link = row.get("url") or (f"https://data.eastmoney.com/notices/detail/{symbol}/{art_code}.html" if art_code else "")
                key = art_code or link or title
                if key in seen:
                    continue
                seen.add(key)
                pub = self._clean_text(row.get("notice_date") or row.get("eiTime") or row.get("display_time") or "") or None
                ok, _reason = self.valid_news_item(title, "", source="东方财富公告", url=link, symbol=symbol, name=name, source_type="announcement", base_relevant=True)
                if not ok:
                    continue
                out.append(self._score_item(title, link, "东方财富公告", pub, "", symbol, name, source_type="announcement"))
                if len(out) >= limit:
                    return out[:limit]
        return out[:limit]

    def _search_cninfo_fulltext(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
        out: list[NewsItem] = []
        page_size = min(50, max(20, limit))
        max_pages = max(1, min(5, (limit + page_size - 1) // page_size + 1))
        seen: set[str] = set()
        for page_num in range(1, max_pages + 1):
            try:
                data = self.http.get(url, params={
                    "searchkey": normalize_symbol(symbol), "sdate": "", "edate": "", "isfulltext": "false",
                    "sortName": "pubdate", "sortType": "desc", "pageNum": str(page_num), "pageSize": str(page_size),
                }, headers={"Referer": "https://www.cninfo.com.cn/", "User-Agent": "Mozilla/5.0"}).json()
            except Exception:
                break
            rows = (data or {}).get("announcements") or (data or {}).get("data") or []
            if not rows:
                break
            for row in rows:
                title = self._clean_text(row.get("announcementTitle") or row.get("title") or "")
                adj = str(row.get("adjunctUrl") or "")
                link = "http://static.cninfo.com.cn/" + adj if adj and not adj.startswith("http") else adj
                key = str(row.get("announcementId") or row.get("announcementID") or adj or title)
                if key in seen:
                    continue
                seen.add(key)
                pub = self._clean_text(str(row.get("announcementTime") or row.get("pubdate") or "")) or None
                ok, _reason = self.valid_news_item(title, "", source="巨潮资讯公告", url=link, symbol=symbol, name=name, source_type="announcement", base_relevant=True)
                if not ok:
                    continue
                out.append(self._score_item(title, link, "巨潮资讯公告", pub, "", symbol, name, source_type="announcement"))
                if len(out) >= limit:
                    return out[:limit]
        return out[:limit]

    def _search_baidu_news_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "https://www.baidu.com/s"
        try:
            html = self.http.get(url, params={"tn": "news", "rtt": "1", "bsst": "1", "ie": "utf-8", "word": query}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="百度新闻", source_type="news", limit=limit, base_url=url)

    def _search_360_news_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "https://news.so.com/ns"
        try:
            html = self.http.get(url, params={"q": query, "rank": "rank", "j": "0", "src": "page"}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="360新闻", source_type="news", limit=limit, base_url=url)

    def _search_eastmoney_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        # 东方财富站内搜索对“名称+代码”有时返回少，分别尝试组合词和名称。
        out: list[NewsItem] = []
        for kw in [query, name or query]:
            if not kw:
                continue
            url = "https://so.eastmoney.com/news/s"
            try:
                html = self.http.get(url, params={"keyword": kw}).text
            except Exception:
                continue
            out.extend(self._extract_links(html, symbol, name, source="东方财富搜索", source_type="news", limit=limit, base_url=url))
            if len(out) >= limit:
                break
        return out[:limit]

    def _search_sina_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "https://search.sina.com.cn/"
        try:
            html = self.http.get(url, params={"q": query, "c": "news", "range": "title", "num": str(limit)}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="新浪财经搜索", source_type="news", limit=limit, base_url=url)

    def _search_10jqka_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = "https://search.10jqka.com.cn/search"
        try:
            html = self.http.get(url, params={"tid": "info", "qs": "box_ths", "w": query}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="同花顺搜索", source_type="news", limit=limit, base_url=url)


    def _search_eastmoney_guba(self, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = f"https://guba.eastmoney.com/list,{normalize_symbol(symbol)}.html"
        try:
            html = self.http.get(url, headers={"Referer": "https://guba.eastmoney.com/", "User-Agent": "Mozilla/5.0"}).text
        except Exception:
            return []
        # 股吧只提取标题链接，不把整页 table 作为摘要。这样“公告转载”和“普通评论”不会被同一大段表格污染。
        items = self._extract_links(html, symbol, name, source="东方财富股吧", source_type="forum", limit=limit, base_url=url, base_relevant=True)
        clean: list[NewsItem] = []
        for item in items:
            title = self._canonical_event_text(item.title)
            if not title or self._is_noise_title(title):
                continue
            clean.append(NewsItem(**{**item.to_dict(), "title": title[:90], "summary": "社区讨论标题，仅用于舆情热度与传闻风险观察，不作为事实证据。", "dedup_reason": "社区舆情按标题事件去重；同公告转载只保留最高可信事实源，社区帖仅作舆情"}))
        return clean[:limit]

    def _search_xueqiu_page(self, query: str, symbol: str, name: str, limit: int) -> list[NewsItem]:
        url = f"https://xueqiu.com/S/{'SZ' if symbol.startswith(('0','2','3','15')) else 'SH'}{symbol}"
        try:
            html = self.http.get(url, headers={"Referer": "https://xueqiu.com/"}).text
        except Exception:
            return []
        return self._extract_links(html, symbol, name, source="雪球/社区", source_type="forum", limit=limit, base_url=url, base_relevant=True)


    def _extract_links(
        self,
        html: str,
        symbol: str,
        name: str,
        source: str,
        source_type: str,
        limit: int,
        base_url: str = "",
        base_relevant: bool = False,
        strict_article: bool = False,
        deep_validate: bool = False,
    ) -> list[NewsItem]:
        """从列表页提取候选链接。

        V16.2 关键变化：新浪/同花顺股票专页不再“先抓列表所有 a 标签再靠后置清洗”。
        对这类专页启用 strict_article + deep_validate：
        1) URL 必须像真实文章/公告详情，而不是 F10 栏目入口；
        2) 进入详情页读取正文，正文必须通过 article-like 校验后才进入候选池；
        3) 列表页上下文只用于发布日期兜底，不再把一整段菜单作为 summary 入库。
        """
        html = html or ""
        out: list[NewsItem] = []
        seen_links: set[str] = set()
        pattern = re.compile(r'<a\b(?P<attrs1>[^>]*)href=["\'](?P<href>[^"\']+)["\'](?P<attrs2>[^>]*)>(?P<body>.*?)</a>', re.I | re.S)
        for m in pattern.finditer(html):
            attrs = (m.group("attrs1") or "") + " " + (m.group("attrs2") or "")
            body = re.sub(r"<.*?>", "", m.group("body") or "")
            title_attr = ""
            tm = re.search(r'title=["\']([^"\']+)["\']', attrs, flags=re.I)
            if tm:
                title_attr = tm.group(1)
            title = self._clean_text(title_attr) or self._clean_text(body)
            href = m.group("href") or ""
            if href.startswith("//"):
                href = "https:" + href
            link = urljoin(base_url, href) if base_url else href
            link = link.split("#", 1)[0]
            if not link or link in seen_links or self._is_search_result_url(link):
                continue
            seen_links.add(link)

            if self._is_non_article_link(link, title, base_url=base_url, ignore_title=strict_article):
                continue
            if strict_article and not self._is_probable_article_url(link, source=source, title=title):
                continue

            ctx_html = html[max(0, m.start()-260): min(len(html), m.end()+500)]
            ctx = self._clean_text(ctx_html)
            pub = self._extract_date_text(ctx) or self._extract_date_text(link) or ""
            summary = "" if strict_article else ctx
            final_title = title

            if deep_validate:
                try:
                    detail = self._fetch_article_detail(link, max_chars=2200, symbol=symbol, name=name)
                except Exception:
                    detail = {}
                detail_title = self._clean_text(detail.get("title") or "")
                detail_text = self._clean_text(detail.get("text") or "")
                if detail_title and not is_menu_or_table_fragment(detail_title, detail_text):
                    final_title = detail_title
                summary = detail_text
                if not self._is_article_detail_text(final_title, summary, source=source, symbol=symbol, name=name, source_type=source_type):
                    continue

            ok, _reason = self.valid_news_item(final_title, summary, source=source, url=link, symbol=symbol, name=name, source_type=source_type, base_relevant=base_relevant)
            if not ok:
                continue
            if len(final_title) > 180:
                final_title = final_title[:180]
            out.append(self._score_item(title=final_title, url=link, source=source, published_at=pub, summary=summary, symbol=symbol, name=name, source_type=source_type))
            if len(out) >= limit:
                break
        return out

    def _is_non_article_link(self, url: str, title: str = "", base_url: str = "", ignore_title: bool = False) -> bool:
        u = (url or "").lower().split("#", 1)[0]
        t = self._clean_text(title or "")
        if not u or u in {"#", "javascript:void(0)", "javascript:;"}:
            return True
        if base_url and u.rstrip("/") == (base_url or "").lower().rstrip("/"):
            return True
        # 股票页里的栏目入口，不是新闻详情。真实文章通常带日期、长数字ID或 .shtml/.html 文章路径。
        nav_path_patterns = [
            r"/\d{6}/(?:news|finance|funds|holder|company|bonus|worth|field|operate|position|analysis|fundflow|companyinfo|bonusfinancing)/?$",
            r"/(?:corp|stockpage)/.*(?:vFD_|vCI_|vCB_|news)/?$",
            r"stockid/\d{6}(?:/|$)",
            r"type/\d+\.p(?:html)?$",
            r"/(?:ggdp|gszl|cwfx|jyfx|gdgb|zlcg|fhrz|jzfx|hyfx|hqzs|lhb|dzjy|rzrq)(?:\.|/|$)",
        ]
        if any(re.search(p, u) for p in nav_path_patterns):
            return True
        if not ignore_title and is_menu_or_table_fragment(t, ""):
            return True
        return False

    def _is_probable_article_url(self, url: str, source: str = "", title: str = "") -> bool:
        """股票专页候选链接准入：只允许新闻/公告详情页，不允许栏目页/F10菜单页。"""
        u = (url or "").lower()
        parsed = urlparse(u)
        host = parsed.netloc
        if not u.startswith(("http://", "https://")):
            return False
        if self._is_non_article_link(u, title, ignore_title=True):
            return False
        # 明确栏目页/列表页/静态资源一律拒绝。
        if re.search(r"(stockpage\.10jqka\.com\.cn/\d{6}/(?:news|finance|funds|holder|company|bonus|worth|field|operate|position|analysis|fundflow)|vip\.stock\.finance\.sina\.com\.cn/corp/go\.php/vcb_allnewsstock|realstock/company/.*/nc\.shtml)", u):
            return False
        if re.search(r"\.(?:js|css|png|jpg|jpeg|gif|ico|svg)(?:\?|$)", u):
            return False
        # 新浪/同花顺的真实文章一般带 doc-id、日期路径、长数字ID、shtml/html 文章页；公告详情页也保留。
        article_like = bool(re.search(r"(doc-[a-z0-9]+|/20\d{2}[/-]?\d{2}[/-]?\d{2}/|/n/20\d{6}/|/c\d{9,}\.shtml|\d{7,}\.shtml|allbulletindetail|notice|announcement|\.shtml(?:\?|$)|\.html(?:\?|$))", u))
        if "10jqka" in host:
            return article_like and ("news.10jqka" in host or "field.10jqka" in host or "stockpage.10jqka" not in host)
        if "sina" in host:
            return article_like
        return article_like

    def _is_article_detail_text(self, title: str, text: str, source: str = "", symbol: str = "", name: str = "", source_type: str = "news") -> bool:
        """详情页正文准入：防止“进入页面了但里面仍是菜单/F10表格”。"""
        cleaned_title = self._clean_text(title or "")
        cleaned_text = self._clean_text(text or "")
        if is_menu_or_table_fragment(cleaned_title, cleaned_text):
            return False
        if len(cleaned_text) < 60 and source_type != "forum":
            return False
        if self._looks_garbled(cleaned_text):
            return False
        # 真实文章应有句子结构，不能只是栏目词堆叠。
        sentence_like = bool(re.search(r"[。！？；：，].{8,}", cleaned_text)) or any(k in cleaned_text for k in ["表示", "称", "披露", "公告", "显示", "认为", "预计", "同比", "环比"])
        if not sentence_like:
            return False
        all_text = f"{cleaned_title} {cleaned_text}"
        relation_hit = bool((name and name in all_text) or (symbol and symbol in all_text))
        finance_hit = any(k in all_text for k in (self.FINANCE_WORDS | self.RISK_WORDS | self.OPERATION_WORDS | self.POLICY_WORDS | {"评级", "目标价", "研报", "股东大会", "公告"}))
        if not relation_hit and not finance_hit:
            return False
        return True

    def _is_noise_title(self, title: str) -> bool:
        ok, _ = self.valid_news_item(title, "", source="东方财富资讯", source_type="news", base_relevant=True)
        return not ok

    def _is_relevant_title(self, title: str, symbol: str, name: str, base_relevant: bool = False) -> bool:
        if self._is_noise_title(title):
            return False
        if base_relevant:
            # 个股专页/股吧/F10页面已经限定标的，但过滤明显导航词和社区灌水标题。
            return True
        if symbol and symbol in title:
            return True
        if name and name in title:
            return True
        # 公司简称可能带“ETF/股份/集团”等，拆分后保留较长中文片段作宽松匹配。
        tokens = [t for t in re.split(r"[\s\-_/（）()·]+", name or "") if len(t) >= 3]
        if any(t in title for t in tokens):
            return True
        return False

    def _decode_jsonish(self, text: str) -> Any | None:
        s = (text or "").strip()
        if not s:
            return None
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                return None
        m = re.search(r"^[\w$\.]+\((.*)\)\s*;?$", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
        # 有些页面把JSON嵌在变量里。
        m = re.search(r"(\{\s*\"[^\n]+\})", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
        return None

    def _extract_json_items(self, data: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        title_keys = {"title", "Title", "notice_title", "announcementTitle", "NEWS_TITLE", "art_title", "Art_Title"}
        url_keys = {"url", "Url", "URL", "art_url", "Art_UniqueUrl", "attachPath", "adjunctUrl"}
        date_keys = {"date", "Date", "publishDate", "notice_date", "eiTime", "display_time", "pubdate", "datetime", "time"}
        summary_keys = {"summary", "content", "digest", "abstract", "description"}

        def walk(x: Any):
            if isinstance(x, dict):
                keys = set(x.keys())
                if keys & title_keys:
                    title = next((x.get(k) for k in title_keys if k in x and x.get(k)), "")
                    url = next((x.get(k) for k in url_keys if k in x and x.get(k)), "")
                    date = next((x.get(k) for k in date_keys if k in x and x.get(k)), "")
                    summary = next((x.get(k) for k in summary_keys if k in x and x.get(k)), "")
                    rows.append({"title": title, "url": url, "date": str(date) if date else None, "summary": summary})
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(data)
        return rows

    def _classify_event(self, text: str) -> dict[str, str]:
        """拆分事件、风险、情绪和影响方向，避免把不同标签混在一起。"""
        text = self._clean_text(text)
        rules = [
            ("持有人权益受损", "negative", "持有人权益受损风险", ["持股人收益受损", "持有人收益受损", "持股人权益受损", "股东权益受损", "投资者利益受损", "投资者损失", "持有人损失", "股民损失"]),
            ("业绩亏损", "negative", "业绩亏损风险", ["业绩亏损", "净利润亏损", "归母净利润亏损", "净利润为负", "归母净利润为负", "由盈转亏", "扭盈为亏", "亏损扩大", "预亏"]),
            ("业绩下滑", "negative", "业绩下滑风险", ["业绩下滑", "净利润下降", "营收下降", "利润下降", "同比下降", "业绩预减", "增收不增利"]),
            ("股东减持", "negative", "减持压力", ["减持", "拟减持", "清仓式减持", "被动减持", "大股东减持", "高管减持"]),
            ("质押/冻结风险", "negative", "股权质押/冻结风险", ["质押", "平仓风险", "司法冻结", "轮候冻结", "股份冻结"]),
            ("诉讼监管", "negative", "诉讼监管风险", ["立案", "调查", "处罚", "问询函", "监管函", "警示函", "诉讼", "仲裁", "违规", "信披违规"]),
            ("债务流动性风险", "negative", "债务流动性风险", ["债务逾期", "流动性紧张", "违约", "无法偿还", "资金链", "破产重整", "退市风险"]),
            ("安全/质量事件", "negative", "安全质量风险", ["事故", "召回", "质量问题", "安全隐患", "停产整改", "环保处罚"]),
            ("订单合同", "positive", "", ["中标", "签订合同", "重大合同", "订单", "采购协议", "战略合作", "合作协议"]),
            ("机构持仓下降", "negative", "机构重仓占比下降或退出前十大（需区分非公司减持）", ["退出持仓前十", "退出前十", "减仓", "持仓占比降低", "仓位下降"]),
            ("机构持仓上升", "positive", "", ["新进持仓前十", "进入持仓前十", "加仓", "获加仓"]),
            ("股东增持/回购", "positive", "", ["回购", "控股股东增持", "实控人增持", "高管增持", "董监高增持", "员工持股计划", "股权激励"]),
            ("业绩增长", "positive", "", ["业绩增长", "净利润增长", "同比增长", "扭亏为盈", "预增", "营收增长", "利润增长"]),
            ("分红派息", "positive", "", ["分红", "派息", "现金红利", "利润分配", "高送转"]),
            ("宏观政策", "neutral", "", ["美联储", "央行", "降息", "加息", "CPI", "PPI", "PMI", "GDP", "M2", "社融", "LPR", "逆回购", "汇率", "美元指数", "美债", "关税", "政策", "制裁", "原油", "黄金", "OPEC", "地缘", "贸易摩擦"]),
        ]
        for label, polarity, risk, words in rules:
            if any(w in text for w in words):
                return {
                    "event_label": label,
                    "sentiment_label": "正面" if polarity == "positive" else "负面" if polarity == "negative" else "中性",
                    "impact_direction": "偏利好" if polarity == "positive" else "偏利空" if polarity == "negative" else "中性/待观察",
                    "risk_tag": risk,
                }
        if any(w in text for w in ["利好", "上涨", "大涨", "改善", "获批", "突破", "创新高"]):
            return {"event_label": "一般正面", "sentiment_label": "正面", "impact_direction": "偏利好", "risk_tag": ""}
        if any(w in text for w in ["利空", "下跌", "大跌", "暴跌", "风险", "受损", "损失", "下调", "暂停"]):
            return {"event_label": "一般负面", "sentiment_label": "负面", "impact_direction": "偏利空", "risk_tag": "负面舆情"}
        return {"event_label": "一般资讯", "sentiment_label": "中性", "impact_direction": "中性/待观察", "risk_tag": ""}

    def _infer_impact_scope(self, text: str, source_type: str = "news", source: str = "") -> str:
        text = self._clean_text(text)
        if source_type in {"announcement", "forum"}:
            return "company"
        if source_type == "macro":
            return "macro"
        if any(w in text for w in ["美联储", "央行", "CPI", "PPI", "PMI", "GDP", "M2", "社融", "LPR", "逆回购", "关税", "汇率", "美元指数", "美债", "原油", "黄金", "战争", "冲突", "地缘", "制裁", "OPEC"]):
            return "macro"
        if any(w in text for w in ["A股", "沪指", "深成指", "创业板", "港股", "美股", "纳指", "标普", "道指", "全球市场"]):
            return "market"
        if any(w in text for w in self.INDUSTRY_POLICY_TERMS):
            return "industry"
        return "company"

    def _score_item(self, title: str, url: str, source: str, published_at: str | None, summary: str, symbol: str, name: str, source_type: str = "news") -> NewsItem:
        title = self._clean_text(title)
        summary = self._clean_text(summary)
        text = f"{title} {summary}".strip()
        time_meta = extract_time_fields(published_at, title, summary, url, source_type=source_type)
        publish_dt = self._parse_item_date(time_meta.get("publish_time"))
        event_dt = self._parse_item_date(time_meta.get("event_time"))
        published_norm = publish_dt.date().isoformat() if publish_dt else None
        if published_norm:
            date_display = published_norm
        elif event_dt:
            date_display = f"事件:{event_dt.date().isoformat()} / 发布日期未知"
        else:
            date_display = str(published_at).strip() if published_at else None

        relevance = 0.0
        if symbol and symbol in text:
            relevance += 35
        if name and name in text:
            relevance += 45
        if source in {"东方财富F10", "东方财富股吧", "雪球/社区"}:
            relevance += 22
        relevance += min(20, sum(1 for w in self.IMPACT_WORDS if w in text) * 4)
        credibility = self._credibility(url, source, source_type)
        category = self._category(text, source_type)
        message_dimension = self._message_dimension(text, source_type, source)
        event_meta = self._classify_event(text)
        relation = self._target_relation_analysis(text, symbol=symbol, name=name, source_type=source_type)
        if relation.get("event_label"):
            event_meta.update({k: v for k, v in relation.items() if k in {"event_label", "sentiment_label", "impact_direction", "risk_tag"} and v})
        impact_scope = self._infer_impact_scope(text, source_type, source)
        fake_risk = self._fake_risk(title, url, source, credibility)
        impact = min(100.0, sum(12 for w in self.IMPACT_WORDS if w in text))
        if event_meta.get("event_label") not in {"一般资讯", "宏观政策"}:
            impact = max(impact, 55.0)
        sentiment, evidence = self._rule_sentiment(text, source_type, event_meta)
        if relation.get("evidence"):
            evidence = list(dict.fromkeys(evidence + list(relation.get("evidence") or [])))
        if relation.get("relation") == "机构持仓下降":
            sentiment = min(sentiment, 43.0)
            category = "机构持仓变动"
        elif relation.get("relation") == "机构持仓上升":
            sentiment = max(min(sentiment, 60.0), 56.0)
            category = "机构持仓变动"
        elif relation.get("relation") == "非目标增持":
            sentiment = min(sentiment, 52.0)
            evidence.append("增持对象不是当前标的，已取消增持利好判定")
        # 研报/评级方向：只对真实研报标题或正文生效；栏目入口“个股研报/研究报告”会在 valid_news_item 阶段被拦截。
        if any(k in text for k in ["研报", "研究报告", "评级", "目标价", "买入", "增持评级", "推荐", "跑赢行业", "上调评级", "下调评级"]):
            if any(k in text for k in ["买入", "推荐", "强烈推荐", "跑赢行业", "上调评级", "上调目标价", "维持增持", "首次覆盖"]):
                sentiment = max(sentiment, 58.0)
                event_meta = {**event_meta, "event_label": "研报正面观点", "sentiment_label": "正面", "impact_direction": "偏利好/研报观点"}
                evidence.append("研报/评级偏正面")
                category = "研报观点"
                source_type = "research" if source_type == "news" else source_type
            elif any(k in text for k in ["卖出", "减持评级", "下调评级", "下调目标价", "低于预期", "不及预期"]):
                sentiment = min(sentiment, 43.0)
                event_meta = {**event_meta, "event_label": "研报负面观点", "sentiment_label": "负面", "impact_direction": "偏利空/研报观点", "risk_tag": "研报下调或不及预期"}
                evidence.append("研报/评级偏负面")
                category = "研报观点"
                source_type = "research" if source_type == "news" else source_type
        if source_type == "announcement":
            fake_risk = min(fake_risk, 12)
            sentiment = 50 + (sentiment - 50) * 0.90
        elif source_type == "forum":
            # 舆情不作为公司事实，但需要判断情绪方向：正/负只影响“舆情观察”和传闻风险，
            # 不进入核心公司事实计分。
            fake_risk = max(fake_risk, 58)
            credibility = min(credibility, 45)
            raw_sentiment = sentiment
            if raw_sentiment >= 58:
                sentiment = min(raw_sentiment, 57.0)
                event_meta = {"event_label": "正面舆情", "sentiment_label": "正面", "impact_direction": "舆情偏正/需核验", "risk_tag": ""}
            elif raw_sentiment <= 45:
                sentiment = max(raw_sentiment, 38.0)
                event_meta = {"event_label": "负面舆情", "sentiment_label": "负面", "impact_direction": "舆情偏负/需核验", "risk_tag": "社区负面舆情或传闻风险"}
            else:
                sentiment = 50.0
                event_meta = {"event_label": "中性舆情", "sentiment_label": "中性", "impact_direction": "中性/需核验", "risk_tag": ""}
            impact = min(max(impact, 8.0), 24.0)
            category = "社区舆情"

        # 时效只按 publish_time 计算；event_time 仅用于事件发生/召开时间，不把未来会议日期当作新闻发布日期。
        recency_weight = self._recency_weight(publish_dt)
        event_type = str(time_meta.get("event_type") or "general_news")
        period = str(time_meta.get("period") or "")
        event_day = event_dt.date().isoformat() if event_dt else "unknown"
        doc_id = str(time_meta.get("document_id") or document_id_from_url(url) or "")
        issuer = name or symbol or ""
        if doc_id:
            event_key = f"doc:{doc_id}"
        elif event_type in {"shareholder_meeting", "board_meeting", "financial_report", "dividend", "holder_change", "regulatory", "contract_order", "investment_project", "derivatives_settlement"}:
            event_key = f"issuer:{issuer}:{event_type}:{period or 'na'}:{event_day}"
        else:
            dt_for_key = publish_dt or event_dt
            event_key = self._event_key(text, event_meta.get("event_label", "一般资讯"), dt_for_key)
        event_weight = self._event_weight(credibility, impact, fake_risk, recency_weight, source_type)
        group = event_key or self._fingerprint(title)
        industries = self._industry_tags(text)
        initial_content_status = "title_only"
        initial_missing_reason = "公开来源当前仅返回标题，尚未取得可核验正文"
        if summary and not self._looks_like_page_chrome(summary):
            initial_content_status = "structured_excerpt"
            initial_missing_reason = ""
        return NewsItem(
            title=title[:180],
            url=url,
            source=source,
            source_type=source_type,
            published_at=published_at,
            published_at_norm=published_norm,
            date_display=date_display,
            publish_time=time_meta.get("publish_time"),
            event_time=time_meta.get("event_time"),
            crawl_time=time_meta.get("crawl_time"),
            time_confidence=str(time_meta.get("time_confidence") or ""),
            time_basis=str(time_meta.get("time_basis") or ""),
            event_type=event_type,
            issuer=issuer,
            period=period,
            document_id=doc_id,
            summary=summary[:300],
            relevance_score=round(max(0, min(100, relevance)), 2),
            sentiment_score=round(max(0, min(100, sentiment)), 2),
            credibility_score=round(max(0, min(100, credibility)), 2),
            impact_score=round(max(0, min(100, impact)), 2),
            fake_risk_score=round(max(0, min(100, fake_risk)), 2),
            category=category,
            message_dimension=message_dimension,
            event_label=event_meta.get("event_label", "一般资讯"),
            sentiment_label=event_meta.get("sentiment_label", "中性"),
            impact_scope=impact_scope,
            impact_direction=event_meta.get("impact_direction", "中性/待观察"),
            risk_tag=event_meta.get("risk_tag", ""),
            duplicate_group=group,
            event_key=event_key,
            event_weight=round(event_weight, 4),
            recency_weight=round(recency_weight, 4),
            industry_tags=industries,
            evidence=evidence[:8],
            target_relation=str(relation.get("relation") or ""),
            relation_confidence=float(relation.get("confidence") or 0.0),
            relation_note=str(relation.get("note") or ""),
            content_quality_status=initial_content_status,
            content_missing_reason=initial_missing_reason,
        )


    def _aggregate(self, symbol: str, name: str, items: list[NewsItem]) -> dict[str, Any]:
        if not items:
            return {
                "news_score": 50.0,
                "sentiment": "neutral",
                "sentiment_cn": "中性",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "weighted_positive": 0.0,
                "weighted_negative": 0.0,
                "weighted_neutral": 0.0,
                "avg_credibility": None,
                "avg_relevance": None,
                "avg_impact": None,
                "avg_fake_risk": None,
                "keywords": [],
                "category_counts": [],
                "dimension_counts": [],
                "source_counts": [],
                "risk_flags": ["未抓取到有效中文新闻/公告或公开接口暂不可用"],
                "summary": "暂未获取到有效中文新闻/公告，保持中性评分。可在日志查看各新闻源返回状态，或稍后强制刷新。",
                "time_counts": [],
                "official_count": 0,
                "recent_count": 0,
                "official_negative_count": 0,
                "date_unknown_count": 0,
                "event_family_counts": [],
                "duplicate_groups": [],
                "data_quality": {"date_unknown_count": 0, "official_count": 0, "stored_items_used": 0, "verified_full_text_count": 0, "structured_excerpt_count": 0, "title_only_count": 0, "boilerplate_rejected_count": 0, "merged_duplicate_count": 0},
            }
        # 社区/论坛不作为核心利多利空证据；高疑似传闻降权但保留在明细里。
        quality_excluded_count = sum(1 for x in items if x.content_quality_status == "boilerplate_rejected")
        eligible_core_items = [
            x for x in items
            if x.source_type != "forum"
            and x.fake_risk_score < 75
            and x.content_quality_status != "boilerplate_rejected"
        ]
        core_items = [x for x in eligible_core_items if self._is_current_scoring_item(x)]
        upcoming_core_items = [x for x in eligible_core_items if self._is_upcoming_observation_item(x)]
        historical_excluded_count = max(0, len(eligible_core_items) - len(core_items) - len(upcoming_core_items))
        # 事件级聚合：同一财报亏损、同一监管事项、多源转载只计一次主权重。
        event_best: dict[str, NewsItem] = {}
        event_counts: dict[str, int] = {}
        for x in core_items:
            key = x.event_key or x.duplicate_group or self._fingerprint(x.title)
            event_counts[key] = event_counts.get(key, 0) + 1
            prev = event_best.get(key)
            if prev is None or self._item_priority(x) > self._item_priority(prev):
                event_best[key] = x
        unique_core = list(event_best.values())
        upcoming_event_count = len({
            x.event_key or x.duplicate_group or self._fingerprint(x.title)
            for x in upcoming_core_items
        })
        def w(x: NewsItem) -> float:
            content_factor = {
                "full_text": 1.0,
                "structured_excerpt": 0.88,
                "title_only": 0.68,
                "boilerplate_rejected": 0.25,
            }.get(str(x.content_quality_status or "title_only"), 0.60)
            return max(0.12, float(x.event_weight or 1.0) * content_factor)
        if unique_core:
            total_w = sum(w(x) for x in unique_core) or 1.0
            avg_sent = sum(x.sentiment_score * w(x) for x in unique_core) / total_w
            avg_cred = sum(x.credibility_score * w(x) for x in unique_core) / total_w
            avg_rel = sum(x.relevance_score * w(x) for x in unique_core) / total_w
            avg_imp = sum(x.impact_score * w(x) for x in unique_core) / total_w
            avg_fake = sum(x.fake_risk_score * w(x) for x in unique_core) / total_w
            weighted_pos = sum(w(x) for x in unique_core if x.sentiment_score >= 58)
            weighted_neg = sum(w(x) for x in unique_core if x.sentiment_score <= 45 or (x.evidence and any("风险" in e or "亏" in e or "下降" in e or "减持" in e or "问询" in e or "处罚" in e for e in x.evidence)))
            weighted_neu = max(0.0, total_w - weighted_pos - weighted_neg)
            pos = sum(1 for x in unique_core if x.sentiment_score >= 58)
            neg = sum(1 for x in unique_core if x.sentiment_score <= 45 or (x.evidence and any("风险" in e or "亏" in e or "下降" in e or "减持" in e or "问询" in e or "处罚" in e for e in x.evidence)))
            neu = len(unique_core) - pos - neg
            # 当前分只使用近期可核验事件，历史内容仍保留在明细供追溯。
            score = avg_sent * 0.42 + avg_cred * 0.20 + avg_rel * 0.16 + avg_imp * 0.12 + (100 - avg_fake) * 0.10
        else:
            total_w = weighted_pos = weighted_neg = weighted_neu = 0.0
            avg_sent = avg_cred = avg_rel = avg_fake = 50.0
            avg_imp = 0.0
            pos = neg = neu = 0
            score = 50.0
        # 负面官方事件按事件族扣分，不按转载条数扣分。
        official_neg_families = [x for x in unique_core if (x.source_type == "announcement" or x.credibility_score >= 85) and x.sentiment_score <= 45]
        if official_neg_families:
            score -= min(12, 3.5 * len(official_neg_families))
        all_text = " ".join(x.title + " " + x.summary for x in core_items)
        kws = self._keywords(all_text)
        risk_flags = []
        if not unique_core:
            risk_flags.append("近期计分窗口内无可核验信息，当前信息分保持中性")
        if upcoming_event_count:
            risk_flags.append(f"未来观察事件 {upcoming_event_count} 组：提高监控频率，不直接加减当前信息分")
        if quality_excluded_count:
            risk_flags.append(f"网页导航/免责声明正文 {quality_excluded_count} 条已排除，等待重新抓取")
        if weighted_neg >= max(1.3, weighted_pos + 0.6):
            risk_flags.append("负面事件权重偏高")
        if avg_cred < 45:
            risk_flags.append("新闻来源可信度偏低")
        if avg_fake >= 45:
            risk_flags.append("疑似传闻/社区噪声偏多")
        if any(x.category == "监管/风险" and x.source_type != "forum" for x in core_items):
            risk_flags.append("存在监管/诉讼/风险类信息")
        if official_neg_families:
            risk_flags.append(f"官方/高可信负面事件 {len(official_neg_families)} 组")
        sentiment = "positive" if avg_sent >= 60 and weighted_pos > weighted_neg else "negative" if avg_sent <= 43 or weighted_neg >= weighted_pos + 1.2 else "neutral"
        sentiment_cn = {"positive": "正面", "negative": "负面", "neutral": "中性"}.get(sentiment, "中性")
        category_counts = self._counts([x.category for x in items])
        dimension_counts = self._counts([x.message_dimension for x in items])
        source_counts = self._counts([x.source for x in items])
        time_counts = self._time_counts(items)
        official_count = sum(1 for x in items if x.source_type == "announcement" or x.credibility_score >= 85)
        recent90_count = sum(x.get("count", 0) for x in time_counts if x.get("name") in {"近30天", "近90天"})
        date_unknown_count = sum(1 for x in items if not self._parse_item_date(x.published_at_norm or x.published_at))
        official_neg = len(official_neg_families)
        forum_count = sum(1 for x in items if x.source_type == "forum")
        verified_full_text_count = sum(1 for x in items if x.content_quality_status == "full_text")
        structured_excerpt_count = sum(1 for x in items if x.content_quality_status == "structured_excerpt")
        title_only_count = sum(1 for x in items if x.content_quality_status == "title_only")
        boilerplate_rejected_count = sum(1 for x in items if x.content_quality_status == "boilerplate_rejected")
        merged_duplicate_count = sum(max(0, int(x.duplicate_count or 1) - 1) for x in items)
        duplicate_groups = [
            {"event_key": k, "count": c, "kept_title": event_best.get(k).title if event_best.get(k) else ""}
            for k, c in sorted(event_counts.items(), key=lambda kv: kv[1], reverse=True) if c > 1
        ][:12]
        event_family_counts = self._counts([x.event_label for x in unique_core])
        summary = (
            f"中文信息 {len(items)} 条，近期事件级计分 {len(unique_core)} 组（未来观察 {upcoming_event_count} 组、社区舆情 {forum_count} 条、网页壳 {quality_excluded_count} 条不进核心计分，过期/日期缺失 {historical_excluded_count} 条仅供查阅）："
            f"正面 {pos}组/权重{weighted_pos:.1f}，负面 {neg}组/权重{weighted_neg:.1f}，中性 {neu}组/权重{weighted_neu:.1f}；"
            f"近90天 {recent90_count} 条，官方/高可信 {official_count} 条，平均可信度 {avg_cred:.1f}，疑似噪声 {avg_fake:.1f}，未知日期 {date_unknown_count} 条。"
        )
        return {
            "news_score": round(max(0, min(100, score)), 2),
            "sentiment": sentiment,
            "sentiment_cn": sentiment_cn,
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "weighted_positive": round(weighted_pos, 2),
            "weighted_negative": round(weighted_neg, 2),
            "weighted_neutral": round(weighted_neu, 2),
            "avg_credibility": round(avg_cred, 2),
            "avg_relevance": round(avg_rel, 2),
            "avg_impact": round(avg_imp, 2),
            "avg_fake_risk": round(avg_fake, 2),
            "keywords": kws,
            "category_counts": category_counts,
            "dimension_counts": dimension_counts,
            "source_counts": source_counts,
            "time_counts": time_counts,
            "official_count": official_count,
            "recent_count": recent90_count,
            "date_unknown_count": date_unknown_count,
            "official_negative_count": official_neg,
            "risk_flags": list(dict.fromkeys(risk_flags)),
            "summary": summary,
            "event_family_counts": event_family_counts,
            "duplicate_groups": duplicate_groups,
            "data_quality": {"date_unknown_count": date_unknown_count, "official_count": official_count, "official_negative_count": official_neg, "item_count": len(items), "core_item_count": len(core_items), "event_core_count": len(unique_core), "current_scoring_count": len(unique_core), "upcoming_observation_count": upcoming_event_count, "historical_excluded_count": historical_excluded_count, "quality_excluded_count": quality_excluded_count, "forum_count": forum_count, "duplicate_group_count": len(duplicate_groups), "merged_duplicate_count": merged_duplicate_count, "verified_full_text_count": verified_full_text_count, "structured_excerpt_count": structured_excerpt_count, "title_only_count": title_only_count, "boilerplate_rejected_count": boilerplate_rejected_count, "search_engine_evidence": 0},
            "credibility_method": "可信度为规则化来源权重：交易所/巨潮/公司公告最高，权威财经媒体较高，搜索聚合与社区较低；社区帖不作为核心利多利空证据。",
            "scoring_note": "V3.15/V16.2采用源头候选准入+详情正文准入+深度清洗+事件簇去重+实时全球要闻行业映射+时效权重：官方公告/交易所/巨潮为核心事实源，权威快讯进入宏观/行业映射，社区只作舆情，搜索引擎关键词页不参与评分；同一亏损/问询/减持/订单事件多源转载只计一次主权重。",
        }


    def _deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        """Merge retransmissions while preserving dated event progress.

        Similar wording alone is not enough. A different announcement date or
        document id is a separate point in an event series and must remain
        visible.
        """
        groups: dict[str, list[NewsItem]] = {}
        representatives: dict[str, NewsItem] = {}
        for item in items:
            title_core = self._canonical_event_text(item.title)
            key = self._strict_duplicate_key(item, title_core)
            if key not in groups:
                for gk, representative in representatives.items():
                    if self._can_merge_duplicate(item, representative):
                        key = gk
                        break
            groups.setdefault(key, []).append(item)
            representatives.setdefault(key, item)
        kept: list[NewsItem] = []
        for key, arr in groups.items():
            arr.sort(key=self._item_priority, reverse=True)
            best = arr[0]
            if len(arr) > 1:
                source_list = sorted({x.source for x in arr if x.source})
                source_refs = list(dict.fromkeys(x.url for x in arr if x.url))[:12]
                sources = "、".join(source_list[:4])
                best = NewsItem(**{
                    **best.to_dict(),
                    "dedup_reason": f"同事件合并：{len(arr)} 条相近/转载信息，来源={sources}；仅最高可信版本进入主展示和主计分",
                    "duplicate_group": key,
                    "event_key": best.event_key or key,
                    "duplicate_count": len(arr),
                    "duplicate_sources": source_list[:12],
                    "duplicate_source_refs": source_refs,
                })
            kept.append(best)
        kept.sort(key=self._item_priority, reverse=True)
        return kept

    def _strict_duplicate_key(self, item: NewsItem, title_core: str | None = None) -> str:
        if item.content_hash:
            return f"content:{item.content_hash}"
        if item.document_id:
            return f"doc:{item.document_id}"
        url = str(item.url or "").split("#", 1)[0].rstrip("/")
        if url:
            return "url:" + hashlib.sha1(url.encode("utf-8", "ignore")).hexdigest()[:18]
        day = self._item_event_day(item) or "unknown"
        core = title_core or self._canonical_event_text(item.title)
        return f"title:{day}:{self._dedup_fingerprint(core)}"

    def _item_event_day(self, item: NewsItem) -> str:
        value = item.event_time or item.publish_time or item.published_at_norm or item.published_at or item.date_display
        dt = self._parse_item_date(value)
        return dt.date().isoformat() if dt else ""

    def _can_merge_duplicate(self, item: NewsItem, representative: NewsItem) -> bool:
        if item.content_hash and representative.content_hash and item.content_hash == representative.content_hash:
            return True
        if item.document_id and representative.document_id and item.document_id == representative.document_id:
            return True
        left_url = str(item.url or "").split("#", 1)[0].rstrip("/")
        right_url = str(representative.url or "").split("#", 1)[0].rstrip("/")
        if left_url and right_url and left_url == right_url:
            return True
        left_day = self._item_event_day(item)
        right_day = self._item_event_day(representative)
        if not left_day or left_day != right_day:
            return False
        left_type = str(item.event_type or "general_news")
        right_type = str(representative.event_type or "general_news")
        scheduled_types = {
            "shareholder_meeting",
            "board_meeting",
            "financial_report",
            "dividend",
            "derivatives_settlement",
        }
        if item.event_time and representative.event_time and left_type == right_type and left_type in scheduled_types:
            return True
        exact_title = self._exact_title_key(item.title) == self._exact_title_key(representative.title)
        if item.document_id and representative.document_id and item.document_id != representative.document_id:
            left_host = urlparse(left_url).netloc.lower() if left_url else ""
            right_host = urlparse(right_url).netloc.lower() if right_url else ""
            if left_host and right_host and left_host == right_host:
                return False
            return exact_title
        if item.source_type == "announcement" or representative.source_type == "announcement":
            return exact_title
        compatible_types = left_type == right_type or "announcement" in {left_type, right_type}
        return compatible_types and self._similar_title(item.title, representative.title)

    def _exact_title_key(self, title: str) -> str:
        value = re.sub(r"[\W_]+", "", self._canonical_event_text(title).lower())
        return value[:140]

    def _item_priority(self, x: NewsItem) -> tuple:
        dt = self._parse_item_date(x.published_at_norm or x.published_at or x.date_display)
        ts = 0.0
        if dt:
            try:
                ts = dt.timestamp()
            except (OSError, OverflowError, ValueError):
                # Windows raises OSError for pre-1970 datetimes. Keep old or
                # placeholder announcement dates sortable without failing the
                # whole information refresh.
                ts = float(dt.toordinal())
        official = 1 if x.source_type == "announcement" or x.credibility_score >= 85 else 0
        verified_content = 1 if x.content_loaded and x.content_quality_status == "full_text" else 0
        return (official, verified_content, x.relevance_score, x.credibility_score, x.impact_score, x.recency_weight, ts)

    def _is_current_scoring_item(self, item: NewsItem) -> bool:
        """Limit live information scoring to dated, decision-relevant events."""
        dt = self._parse_item_date(item.published_at_norm or item.published_at or item.date_display)
        if not dt:
            return False
        now = datetime.now()
        age_days = (now - dt).days
        if age_days < -1:
            return False
        event_time = self._parse_item_date(item.event_time)
        if event_time and event_time > now:
            return False
        max_days = current_scoring_window_days(
            item.source_type,
            item.event_type,
            item.risk_tag,
            item.sentiment_score,
        )
        return age_days <= max_days

    def _is_upcoming_observation_item(self, item: NewsItem) -> bool:
        """Keep announced future events visible without treating outcomes as known."""
        now = datetime.now()
        published = self._parse_item_date(item.published_at_norm or item.published_at or item.date_display)
        event_time = self._parse_item_date(item.event_time)
        if not published or not event_time or event_time <= now:
            return False
        age_days = (now - published).days
        max_days = current_scoring_window_days(
            item.source_type,
            item.event_type,
            item.risk_tag,
            item.sentiment_score,
        )
        return -1 <= age_days <= max_days

    def _rule_sentiment(self, text: str, source_type: str, event_meta: dict[str, str]) -> tuple[float, list[str]]:
        t = text or ""
        evidence: list[str] = []
        score = 50.0
        label = event_meta.get("event_label", "")
        if event_meta.get("sentiment_label") == "负面":
            score -= 14; evidence.append(label or "负面事件")
        elif event_meta.get("sentiment_label") == "正面":
            score += 12; evidence.append(label or "正面事件")
        # 财报类负面必须在财报语境中命中，避免“持有人收益受损”误判为业绩亏损。
        finance_context = any(k in t for k in ["业绩", "财报", "年报", "半年报", "季报", "预告", "快报", "净利润", "营收", "扣非", "归母"])
        finance_negative = [
            ("归母净利润为负", ["归母", "为负"]), ("扣非净利润亏损", ["扣非", "亏损"]),
            ("业绩亏损", ["业绩", "亏损"]), ("净利润亏损", ["净利润", "亏损"]),
            ("业绩预亏", ["预亏"]), ("净利润同比下降", ["净利润", "下降"]),
            ("业绩预减", ["预减"]), ("增收不增利", ["增收不增利"]),
        ]
        if finance_context:
            for ev, keys in finance_negative:
                if all(k in t for k in keys):
                    score -= 13 if source_type == "announcement" else 9
                    evidence.append(ev)
        risk_patterns = [
            ("监管/问询/处罚", ["问询", "立案", "监管", "处罚", "警示函"]),
            ("股东减持", ["减持"]), ("诉讼/仲裁风险", ["诉讼", "仲裁"]),
            ("债务/违约风险", ["债务", "违约", "逾期"]), ("质押/冻结风险", ["质押", "冻结"]),
            ("投资者权益受损", ["受损", "损失"]),
        ]
        for ev, keys in risk_patterns:
            if any(k in t for k in keys):
                score -= 8 if source_type == "announcement" else 5
                evidence.append(ev)
        positive_strong = [
            ("业绩增长/预增", ["预增", "净利润增长", "业绩增长", "同比增长", "增长"]),
            ("扭亏为盈", ["扭亏为盈"]),
            ("公司回购/股东增持", ["回购", "控股股东增持", "实控人增持", "高管增持", "董监高增持", "公司增持"]),
            ("中标/订单/合同", ["中标", "订单", "合同"]), ("分红", ["分红", "派息", "现金红利"]),
            ("获批/突破", ["获批", "突破", "创新高"]),
        ]
        for ev, keys in positive_strong:
            if any(k in t for k in keys):
                # 单独“盈利”不加分；必须是增长、扭亏、回购、中标等更明确事件。
                score += 7 if source_type == "announcement" else 5
                evidence.append(ev)
        # 转折/担忧语义：虽盈利但承压、盈利但忧于发展，不按利好处理。
        cautious_words = ["但", "然而", "不过", "忧", "担忧", "承压", "隐忧", "不确定", "低于预期", "放缓", "压力"]
        if any(w in t for w in cautious_words) and any(w in t for w in ["盈利", "增长", "利润", "营收"]):
            score = min(score, 54)
            score -= 4
            evidence.append("正面表述带转折/担忧，按中性偏谨慎")
        if any(w in t for w in ["传闻", "网传", "据称", "小作文", "未经证实"]):
            score = 50.0
            evidence.append("传闻未核验，不参与方向性判断")
        return max(0, min(100, score)), list(dict.fromkeys([e for e in evidence if e]))[:10]

    def _extract_finance_period(self, text: str) -> str:
        t = text or ""
        year = ""
        m = re.search(r"(20\d{2})\s*年", t) or re.search(r"(20\d{2})[-/.]", t)
        if m:
            year = m.group(1)
        period = ""
        if any(k in t for k in ["一季报", "第一季度", "Q1"]): period = "Q1"
        elif any(k in t for k in ["半年报", "半年度", "中报", "上半年", "H1"]): period = "H1"
        elif any(k in t for k in ["三季报", "前三季度", "第三季度", "Q3"]): period = "Q3"
        elif any(k in t for k in ["年报", "年度", "全年"]): period = "FY"
        # 年份有但周期不明时，归到同一年度财报风险，避免“2025年亏损/2025半年亏损”机械翻倍。
        return f"{year}:{period or 'FY'}" if year else (period or "unknown")


    def _event_key(self, text: str, event_label: str, dt: datetime | None) -> str:
        t = self._canonical_event_text(text)
        label = event_label or "一般资讯"
        day = dt.date().isoformat() if dt else (self._extract_date_text(t) or "unknown")
        # 股东大会/董事会/监事会/业绩说明会等日期类公告，按会议类型+日期+年度合并。
        if any(k in t for k in ["股东大会", "董事会", "监事会", "业绩说明会"]):
            kind = "股东大会" if "股东大会" in t else "董事会" if "董事会" in t else "监事会" if "监事会" in t else "业绩说明会"
            year = re.search(r"(20\d{2})\s*年", t)
            period = year.group(1) if year else "unknown"
            return f"meeting:{kind}:{day}:{period}"
        if label in {"机构持仓上升", "机构持仓下降", "股东增持/回购"}:
            core = re.sub(r"[\W_]+", "", t)[:52]
            return f"{label}:{day}:{hashlib.md5(core.encode('utf-8')).hexdigest()[:10]}"
        if label in {"业绩亏损", "业绩下滑", "业绩增长"} or any(k in t for k in ["财报", "业绩", "净利润", "营收", "预告", "年报", "半年报", "季报", "年度报告"]):
            period = self._extract_finance_period(t)
            year = period.split(":", 1)[0] if ":" in period else period
            if label in {"业绩亏损", "业绩下滑"}:
                return "finance:" + (year or "unknown") + ":" + label
            return "finance:" + period + ":" + label
        if label in {"诉讼监管", "股东减持", "质押/冻结风险", "债务流动性风险", "安全/质量事件", "回购/增持", "股东增持/回购", "订单合同", "分红派息", "持有人权益受损"}:
            core = re.sub(r"[\W_]+", "", t)[:42]
            return f"{label}:{day}:{hashlib.md5(core.encode('utf-8')).hexdigest()[:10]}"
        # 宏观/全球快讯按标题核心+日期窗口归并，避免多源同一快讯放大。
        if any(k in t for k in ["美联储", "央行", "原油", "黄金", "美元", "美债", "关税", "地缘", "A股", "港股", "美股"]):
            return f"macro:{day}:{self._dedup_fingerprint(t)}"
        return f"text:{self._dedup_fingerprint(t)}"

    def _recency_weight(self, dt: datetime | None) -> float:
        if not dt:
            return 0.55
        days = max(0, (datetime.now() - dt).days)
        if days <= 7: return 1.25
        if days <= 30: return 1.10
        if days <= 90: return 0.90
        if days <= 365: return 0.62
        return 0.35

    def _event_weight(self, credibility: float, impact: float, fake_risk: float, recency_weight: float, source_type: str) -> float:
        base = 0.45 + credibility / 100 * 0.35 + impact / 100 * 0.25 - fake_risk / 100 * 0.20
        if source_type == "announcement":
            base += 0.25
        if source_type == "forum":
            base *= 0.35
        return max(0.12, min(1.65, base * recency_weight))

    def _target_tokens(self, symbol: str, name: str) -> list[str]:
        toks: list[str] = []
        for x in [name, symbol]:
            x = self._clean_text(x or "")
            if x and x not in toks:
                toks.append(x)
        # 拆出常见简称，提升“贵州茅台/茅台”“宁德时代/宁德”的关系识别。
        for sep in [" ", "-", "_", "/", "（", "(", "·"]:
            for part in list(toks):
                p = part.split(sep)[0]
                if len(p) >= 2 and p not in toks:
                    toks.append(p)
        if name and len(name) >= 4:
            for suffix in ["股份", "集团", "科技", "有限", "公司", "控股", "银行", "证券"]:
                p = name.replace(suffix, "")
                if len(p) >= 2 and p not in toks:
                    toks.append(p)
        return [t for t in toks if t]

    def _target_relation_analysis(self, text: str, symbol: str, name: str, source_type: str = "news") -> dict[str, Any]:
        """识别“当前标的”在一条信息里的真实动作关系。

        解决典型误判：标题里有“增持小米集团，贵州茅台退出持仓前十”，不能因为出现“增持”就给贵州茅台打增持标签。
        """
        t = self._clean_text(text)
        tokens = self._target_tokens(symbol, name)
        if not t or not tokens:
            return {"relation": "", "confidence": 0.0, "note": ""}
        target = next((tok for tok in tokens if tok and tok in t), "")
        if not target:
            # F10/股吧专页本身限定标的，但标题不含名称时不做目标关系强判。
            return {"relation": "", "confidence": 0.0, "note": "标题/摘要未直接出现当前标的，未做目标动作强判"}

        # 按中文逗号/分号/句号/换行切句，先在包含当前标的的分句内判断。
        parts = [p for p in re.split(r"[。；;，,\n]", t) if p.strip()]
        target_parts = [p for p in parts if any(tok in p for tok in tokens)]
        local = " ".join(target_parts) or t[max(0, t.find(target)-36): t.find(target)+len(target)+48]

        neg_words = ["退出持仓前十", "退出前十", "退出十大", "退出", "剔除", "不再位列", "不再持有", "减持", "减仓", "持仓占比降低", "占比降低", "占比下降", "仓位下降", "清仓", "卖出"]
        pos_words = ["新进持仓前十", "进入持仓前十", "新进前十", "买入", "加仓", "获加仓", "增持", "持仓占比提升", "占比提升", "仓位提升"]

        def has_target_action(words: list[str]) -> str:
            def span_has_other_security(span: str, tok: str) -> bool:
                # 如果动作与当前标的之间夹着其他证券代码，通常说明动作属于另一只股票。
                codes = set(re.findall(r"(?<!\d)(\d{5,6})(?!\d)", span))
                cur_codes = {c for c in [symbol, re.sub(r"\D", "", tok)] if c}
                return bool(codes - cur_codes)
            for tok in tokens:
                if not tok:
                    continue
                for w in words:
                    # 当前标的与动作必须在同一短分句中，且距离不能太远；若中间夹其他证券代码，认为不是当前标的动作。
                    pats = [
                        rf"{re.escape(tok)}[^。；;，,]{{0,24}}{re.escape(w)}",
                        rf"{re.escape(w)}[^。；;，,]{{0,18}}{re.escape(tok)}",
                    ]
                    for pat in pats:
                        m = re.search(pat, local)
                        if m and not span_has_other_security(m.group(0), tok):
                            return w
            return ""

        neg = has_target_action(neg_words)
        pos = has_target_action(pos_words)
        if neg:
            return {
                "relation": "机构持仓下降",
                "confidence": 92.0,
                "event_label": "机构持仓下降",
                "sentiment_label": "负面",
                "impact_direction": "偏利空/持仓层面",
                "risk_tag": "机构重仓占比下降或退出前十大（非公司股东减持）",
                "evidence": [f"当前标的命中持仓下降动作：{neg}", "该类信息属于机构/基金持仓变化，不等同于公司基本面恶化"],
                "note": f"当前标的片段：{local[:120]}",
            }
        if pos:
            # 若是基金经理/基金产品/重仓股语境，归入机构持仓上升；若是控股股东/高管，则属于股东增持。
            shareholder_ctx = any(k in local for k in ["控股股东", "实际控制人", "实控人", "高管", "董事", "董监高", "公司股东"])
            if shareholder_ctx or any(k in local for k in ["回购", "员工持股计划", "股权激励"]):
                return {
                    "relation": "股东增持/回购",
                    "confidence": 88.0,
                    "event_label": "股东增持/回购",
                    "sentiment_label": "正面",
                    "impact_direction": "偏利好",
                    "risk_tag": "",
                    "evidence": [f"当前标的命中股东/公司层面增持或回购：{pos}"],
                    "note": f"当前标的片段：{local[:120]}",
                }
            return {
                "relation": "机构持仓上升",
                "confidence": 82.0,
                "event_label": "机构持仓上升",
                "sentiment_label": "正面",
                "impact_direction": "偏利好/持仓层面",
                "risk_tag": "",
                "evidence": [f"当前标的命中机构持仓上升动作：{pos}", "该类信息属于基金/机构持仓变化，强度低于公司公告回购或股东增持"],
                "note": f"当前标的片段：{local[:120]}",
            }

        # 全文有“增持/加仓”，但当前标的所在分句没有对应动作，同时当前标的另有退出/降低语义，防止误打增持。
        if any(w in t for w in ["增持", "加仓", "买入"]) and any(tok in t for tok in tokens):
            if any(w in local for w in ["退出", "降低", "下降", "减仓", "减持"]):
                return {
                    "relation": "非目标增持",
                    "confidence": 78.0,
                    "event_label": "一般资讯",
                    "sentiment_label": "中性",
                    "impact_direction": "中性/需核验",
                    "risk_tag": "",
                    "evidence": ["全文存在增持字样，但增持对象不是当前标的"],
                    "note": f"当前标的片段：{local[:120]}",
                }
        return {"relation": "", "confidence": 0.0, "note": f"未识别到当前标的专属持仓/增减持动作：{local[:120]}"}

    def _extract_date_from_url(self, url: str | None) -> datetime | None:
        u = str(url or "")
        if not u:
            return None
        # 例如 /2025/07/21070751834298.shtml 中 2025/07/21 是发布日期。
        patterns = [
            r"/(20\d{2})/(\d{1,2})/(\d{2})\d{4,}",
            r"/(20\d{2})[-_/\.](\d{1,2})[-_/\.](\d{1,2})",
            r"(20\d{2})(\d{2})(\d{2})",
        ]
        for pat in patterns:
            m = re.search(pat, u)
            if not m:
                continue
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                continue
        return None

    def _industry_tags(self, text: str) -> list[str]:
        industry_map = {
            "新能源": ["新能源", "锂电", "电池", "储能", "光伏", "风电", "充电桩", "新能源车"],
            "半导体/算力": ["半导体", "芯片", "算力", "AI", "人工智能", "数据中心", "光刻", "GPU"],
            "机器人/低空": ["机器人", "人形", "低空", "无人机", "eVTOL", "通航"],
            "军工航空": ["军工", "国防", "航空", "航天", "兵器", "舰船"],
            "医药": ["医药", "创新药", "医疗器械", "医保"],
            "消费": ["消费", "白酒", "食品", "家电", "旅游"],
            "金融地产": ["银行", "券商", "保险", "房地产", "地产"],
            "资源品": ["黄金", "有色", "铜", "铝", "煤炭", "原油", "钢铁"],
        }
        tags = [k for k, vals in industry_map.items() if any(v in text for v in vals)]
        return tags[:6]

    def _credibility(self, url: str, source: str, source_type: str) -> float:
        if source_type == "announcement":
            return 90.0
        if source_type == "research":
            return 70.0
        url_l = (url or "").lower()
        for domain, score in self.TRUSTED_DOMAINS.items():
            if domain in url_l:
                return float(score)
        if "东方财富" in source:
            return 66.0
        if "同花顺" in source:
            return 64.0
        if "新浪" in source:
            return 60.0
        if "百度" in source:
            return 52.0
        if "360" in source:
            return 50.0
        if "雪球" in source or "股吧" in source:
            return 46.0
        return 42.0


    def _message_dimension(self, text: str, source_type: str = "news", source: str = "") -> str:
        """按消息面分析框架分层：宏观经济、行业、公司、资金面、国际、公告、舆情。"""
        t = self._clean_text(text)
        if source_type == "announcement" or any(x in source for x in ["公告", "巨潮", "交易所"]):
            return "官方公告/公司披露"
        if source_type == "forum":
            return "社会舆情/社区讨论"
        if source_type == "research":
            return "研报观点/机构观点"
        if any(w in t for w in ["美联储", "美国", "欧洲", "日本", "中东", "俄乌", "地缘", "制裁", "贸易摩擦", "关税", "美元", "美债", "纳指", "道指", "标普", "全球", "OPEC"]):
            return "国际消息/全球市场"
        if any(w in t for w in ["央行", "降准", "降息", "加息", "逆回购", "LPR", "M2", "社融", "GDP", "CPI", "PPI", "PMI", "财政", "货币政策", "国家统计局", "发改委"]):
            return "宏观经济消息"
        if any(w in t for w in ["资金流", "北向资金", "融资融券", "龙虎榜", "基金", "机构", "主力", "社保", "养老金", "公募", "私募", "重仓", "持仓", "增持", "减持"]):
            return "市场资金面消息"
        if any(w in t for w in self.POLICY_WORDS) or any(w in t for w in self.INDUSTRY_POLICY_TERMS):
            return "行业消息/政策消息"
        return "公司消息"

    def _is_search_result_url(self, url: str) -> bool:
        """过滤搜索引擎结果页/关键词页，避免把“百度搜索页”当作新闻。"""
        u = (url or "").lower()
        bad_patterns = [
            "www.baidu.com/s", "m.baidu.com/s", "baidu.com/s?", "news.so.com/ns",
            "www.sogou.com/web", "weixin.sogou.com/weixin", "so.eastmoney.com/news/s",
            "search.sina.com.cn", "search.10jqka.com.cn/search"
        ]
        # 站内搜索页本身不能作为新闻链接，但从这些页面解析出的真实文章链接可以保留。
        if any(p in u for p in bad_patterns):
            return True
        if any(x in u for x in ["word=", "keyword=", "q="]) and any(domain in u for domain in ["baidu.com", "so.com", "sogou.com"]):
            return True
        return False

    def _category(self, text: str, source_type: str) -> str:
        if any(w in text for w in ["持股人收益受损", "持有人收益受损", "股东权益受损", "投资者利益受损", "持有人损失"]):
            return "持有人权益受损"
        if source_type == "macro":
            return "全球/国内要闻"
        if source_type == "forum":
            return "社区舆情"
        if source_type == "research":
            return "研报观点"
        if source_type == "announcement":
            if any(w in text for w in self.RISK_WORDS):
                return "监管/风险"
            if any(w in text for w in self.FINANCE_WORDS):
                return "财报业绩"
            if any(w in text for w in self.OPERATION_WORDS):
                return "经营业务"
            return "公司公告"
        if any(w in text for w in self.FORUM_WORDS):
            return "社区舆情"
        if any(w in text for w in ["研报", "研究报告", "评级", "目标价"]):
            return "研报观点"
        if any(w in text for w in self.RISK_WORDS):
            return "监管/风险"
        if any(w in text for w in self.FINANCE_WORDS):
            return "财报业绩"
        if any(w in text for w in self.POLICY_WORDS) or any(w in text for w in self.INDUSTRY_POLICY_TERMS):
            return "政策行业"
        if any(w in text for w in self.OPERATION_WORDS):
            return "经营业务"
        return "市场新闻"

    def _fake_risk(self, title: str, url: str, source: str, credibility: float) -> float:
        text = title or ""
        risk = max(0.0, 55.0 - credibility * 0.55)
        if any(w in text for w in {"传闻", "网传", "疑似", "爆料", "小作文", "未经证实", "据称", "听说", "内幕", "消息人士"}):
            risk += 35
        if any(w in text for w in {"澄清", "辟谣", "不实"}):
            risk += 18
        if "雪球" in source or "股吧" in source:
            risk += 18
        if any(domain in (url or "") for domain in ["cninfo.com.cn", "sse.com.cn", "szse.cn"]):
            risk = min(risk, 10)
        return max(0.0, min(100.0, risk))

    def _keywords(self, text: str) -> list[dict[str, Any]]:
        pool = list(self.POSITIVE_WORDS | self.NEGATIVE_WORDS | self.IMPACT_WORDS | self.POLICY_WORDS | self.FINANCE_WORDS | self.RISK_WORDS | self.OPERATION_WORDS)
        found = []
        for w in pool:
            c = text.count(w)
            if c:
                found.append({"word": w, "count": c})
        found.sort(key=lambda x: x["count"], reverse=True)
        return found[:20]



    def _extract_date_text(self, text: str) -> str | None:
        s = str(text or "")
        patterns = [
            r"20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?",
            r"\d{1,2}月\d{1,2}日(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?",
            r"\d+天前", r"\d+小时前", r"\d+分钟前", r"昨天", r"今天", r"前天",
        ]
        for pat in patterns:
            m = re.search(pat, s)
            if m:
                return m.group(0)
        return None

    def _extract_date_from_text(self, text: str) -> datetime | None:
        return self._parse_item_date(text)

    def _adjust_sentiment_by_evidence(self, base: float, text: str, source_type: str) -> tuple[float, list[str]]:
        """对公告正文/高可信正文进行二次修正，沿用 V3.6 事件规则。"""
        meta = self._classify_event(text or "")
        score, ev = self._rule_sentiment(text or "", source_type, meta)
        # 正文为空时保留原分；正文有效时让正文判断占主导，标题分占小权重。
        if not (text or "").strip():
            return base, []
        return max(0, min(100, score * 0.78 + base * 0.22)), ev

    def _extract_html_title(self, html: str) -> str:
        if not html:
            return ""
        for pat in [r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', r'<meta[^>]+name=["\']title["\'][^>]+content=["\']([^"\']+)["\']', r'<title[^>]*>(.*?)</title>']:
            m = re.search(pat, html, flags=re.I | re.S)
            if m:
                t = self._clean_text(m.group(1))
                t = re.sub(r"[_-].{0,20}(新浪财经|同花顺财经|东方财富网|股票频道).*$", "", t).strip()
                if t:
                    return t[:180]
        return ""

    def _extract_article_body_text(self, html: str, max_chars: int = 3600) -> str:
        """从详情页 HTML 中尽量提取正文段落，而不是整页导航。"""
        if not html:
            return ""
        h = re.sub(r"(?is)<(script|style|noscript|iframe)[^>]*>.*?</\1>", " ", html)
        blocks: list[str] = []
        # 先取 p 标签；财经新闻/公告解读通常正文都在 p 中。
        for m in re.finditer(r"(?is)<p[^>]*>(.*?)</p>", h):
            txt = self._clean_text(m.group(1))
            if len(txt) >= 12 and not is_menu_or_table_fragment("正文", txt):
                blocks.append(txt)
        # 其次取疑似 article/content/main 的 div。
        if len(" ".join(blocks)) < 120:
            div_pat = r"(?is)<div[^>]+(?:id|class)=[\"'][^\"']*(?:article|content|main|text|body|detail)[^\"']*[\"'][^>]*>(.*?)</div>"
            for m in re.finditer(div_pat, h):
                txt = self._clean_text(m.group(1))
                if len(txt) >= 40 and not is_menu_or_table_fragment("正文", txt):
                    blocks.append(txt)
        text = " ".join(blocks)
        if not text:
            text = self._clean_text(h)
        # 去除连续菜单短语造成的伪正文。
        text = re.sub(r"(?:首页|行情|新闻公告|财务分析|经营分析|股东股本|主力持仓|公司大事|分红融资|价值分析|行业分析|行情走势|个股研报|公司资料|相关资料)\s*", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]

    def _fetch_article_detail(self, url: str, max_chars: int = 1800, symbol: str = "", name: str = "") -> dict[str, str]:
        if not url or not str(url).startswith("http"):
            return {}
        resp = self.http.get(url, headers={"Referer": "https://finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"})
        ctype = (resp.headers.get("Content-Type") or "").lower()
        raw = resp.content or b""
        if "pdf" in ctype or url.lower().split("?", 1)[0].endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")) or raw[:5] == b"%PDF-":
            return {}
        try:
            if not resp.encoding or resp.encoding.lower() in {"iso-8859-1", "latin-1"}:
                resp.encoding = resp.apparent_encoding or "utf-8"
        except Exception:
            pass
        html = resp.text or ""
        title = self._extract_html_title(html)
        text = self._extract_article_body_text(html, max_chars=max_chars * 2)
        if not text:
            text = self._clean_text(html)
        if self._looks_garbled(text):
            return {}
        # 去掉明显页面噪声后，从正文关键词附近截取；保留足够长度用于情绪判断。
        keys = list(self.FINANCE_WORDS | self.RISK_WORDS | self.OPERATION_WORDS | self.POLICY_WORDS | {"评级", "目标价", "研报", "买入", "增持", "减持", str(name or ""), str(symbol or "")})
        keys = [k for k in keys if k]
        positions = [text.find(k) for k in keys if k in text]
        pos = min(positions) if positions else 0
        start = max(0, pos - 180)
        return {"title": title, "text": text[start:start+max_chars]}

    def _enrich_link_content(self, items: list[NewsItem], symbol: str = "", name: str = "", max_items: int = 24) -> list[NewsItem]:
        """进入普通新闻/研报链接详情页，使用正文二次清洗、情绪与事件字段重算。

        解决“看似进入了页面，但实际只把栏目菜单/表格导航当新闻”的问题。
        """
        out: list[NewsItem] = list(items)
        targets: list[tuple[int, NewsItem]] = []
        for idx, item in enumerate(items):
            need = (
                item.url and item.source_type in {"news", "research", "forum"}
                and ("新浪" in item.source or "同花顺" in item.source or "研报" in item.title or "研究报告" in item.title or item.published_at_norm is None)
                and not self._is_non_article_link(item.url, item.title)
            )
            if need:
                targets.append((idx, item))
            if len(targets) >= max_items:
                break

        if not targets:
            return out

        def load(pair: tuple[int, NewsItem]) -> tuple[int, NewsItem | None]:
            idx, item = pair
            detail = self._fetch_article_detail(item.url, max_chars=1800, symbol=symbol, name=name)
            detail_title = detail.get("title") or ""
            detail_text = detail.get("text") or ""
            new_title = detail_title if detail_title and not is_menu_or_table_fragment(detail_title, detail_text) else item.title
            new_summary = detail_text if len(detail_text) > len(item.summary or "") else item.summary
            ok, _reason = self.valid_news_item(new_title, new_summary, source=item.source, url=item.url, symbol=symbol, name=name, source_type=item.source_type, base_relevant=item.relevance_score >= 20)
            if ok and new_summary and self._is_article_detail_text(new_title, new_summary, source=item.source, symbol=symbol, name=name, source_type=item.source_type) and len(new_summary) > len(item.summary or ""):
                rescored = self._score_item(new_title, item.url, item.source, item.published_at, new_summary, symbol, name, source_type=item.source_type)
                return idx, NewsItem(**{
                    **rescored.to_dict(),
                    "content_loaded": True,
                    "content_source": item.url,
                    "content_quality_status": "full_text",
                    "content_missing_reason": "",
                    "content_hash": hashlib.sha256(new_summary.encode("utf-8", "ignore")).hexdigest(),
                })
            return idx, None

        with ThreadPoolExecutor(max_workers=max(1, min(self.detail_workers, len(targets)))) as executor:
            futures = [executor.submit(load, pair) for pair in targets]
            for future in as_completed(futures):
                try:
                    idx, new_item = future.result(timeout=0)
                    if new_item is not None:
                        out[idx] = new_item
                except Exception:
                    continue
        return out

    def _enrich_announcement_content(self, items: list[NewsItem], max_items: int = 5) -> list[NewsItem]:
        """低频读取公告/高可信链接的正文片段，用于判断利多利空。

        不登录、不绕过验证码；只尝试公开 URL。失败时保留标题级判断。
        """
        out: list[NewsItem] = list(items)
        ordered_targets = [
            (idx, item) for idx, item in enumerate(items)
            if item.url and (item.source_type == "announcement" or item.credibility_score >= 85)
        ][:max_items]
        if not ordered_targets:
            return out

        def load(pair: tuple[int, NewsItem]) -> tuple[int, NewsItem | None]:
            idx, item = pair
            detail = self._fetch_eastmoney_announcement_detail(item.url, max_chars=2400)
            text = detail.get("text", "") if detail else ""
            if not text:
                text = self._fetch_text_excerpt(item.url, max_chars=1200)
                if self._looks_like_page_chrome(text):
                    text = ""
            if text and len(text) > len(item.summary or ""):
                summary = self._clean_text(text)[:500]
                rescored = self._score_item(
                    item.title,
                    item.url,
                    item.source,
                    item.publish_time or item.published_at,
                    summary,
                    "",
                    item.issuer or "",
                    source_type=item.source_type,
                )
                score, ev = self._adjust_sentiment_by_evidence(rescored.sentiment_score, item.title + " " + summary, item.source_type)
                evidence = list(dict.fromkeys((rescored.evidence or []) + ev + (["已读取公开公告正文"] if detail else [])))
                return idx, NewsItem(**{
                    **rescored.to_dict(),
                    "summary": summary,
                    "sentiment_score": round(score, 2),
                    "evidence": evidence,
                    "content_loaded": True,
                    "attachment_url": detail.get("attachment_url", "") if detail else item.attachment_url,
                    "content_source": detail.get("content_source", "generic_public_page") if detail else "generic_public_page",
                    "content_quality_status": "full_text",
                    "content_missing_reason": "",
                    "content_hash": hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest(),
                })
            usable_existing_summary = bool(item.summary and not self._looks_like_page_chrome(item.summary))
            return idx, NewsItem(**{
                **item.to_dict(),
                "summary": item.summary if usable_existing_summary else "",
                "content_loaded": False,
                "content_quality_status": "structured_excerpt" if usable_existing_summary else "title_only",
                "content_missing_reason": "" if usable_existing_summary else "公开正文接口未返回可验证正文，当前仅保留标题级证据",
            })

        with ThreadPoolExecutor(max_workers=max(1, min(self.detail_workers, len(ordered_targets)))) as executor:
            futures = [executor.submit(load, pair) for pair in ordered_targets]
            for future in as_completed(futures):
                try:
                    idx, new_item = future.result(timeout=0)
                    if new_item is not None:
                        out[idx] = new_item
                except Exception:
                    continue
        return out

    def _looks_like_page_chrome(self, text: str) -> bool:
        """Reject navigation/footer text that must never be treated as article evidence."""
        return is_page_chrome_summary(text)

    def _normalize_cached_result(self, cached: dict[str, Any], symbol: str, name: str, limit: int) -> dict[str, Any]:
        """Migrate older cached rows through current truth, dedup and scoring rules."""
        data = dict(cached or {})
        raw_items = data.get("items") or []
        normalized = [self._item_from_dict(row) for row in raw_items if isinstance(row, dict)]
        normalized = self._filter_valid_items(normalized, symbol=symbol, name=name)
        normalized = self._deduplicate(normalized)
        aggregate = self._aggregate(symbol, name, normalized)
        data.update(aggregate)
        data["items"] = [item.to_dict() for item in normalized[:min(limit, 80)]]
        data["count"] = len(normalized)
        data["cleaning_funnel"] = dict(self._last_cleaning_funnel)
        data.setdefault("cache_info", {})
        data["cache_info"].update({"hit": True, "normalized_with_current_rules": True})
        return data

    def _eastmoney_announcement_art_code(self, url: str) -> str:
        value = str(url or "")
        match = re.search(r"\b(AN\d{12,24})\b", value, flags=re.I)
        return match.group(1).upper() if match else ""

    def _fetch_eastmoney_announcement_detail(self, url: str, max_chars: int = 2400) -> dict[str, str]:
        """Read Eastmoney's public announcement-content endpoint, not the HTML shell."""
        art_code = self._eastmoney_announcement_art_code(url)
        if not art_code or "eastmoney.com" not in str(url or "").lower():
            return {}
        cached = self._announcement_detail_cache.get(art_code)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return dict(cached[1])
        endpoint = "https://np-cnotice-stock.eastmoney.com/api/content/ann"
        try:
            response = self.http.get(
                endpoint,
                params={"art_code": art_code, "client_source": "web", "page_index": "1"},
                headers={"Referer": str(url), "User-Agent": "Mozilla/5.0"},
            )
            payload = response.json()
            data = (payload or {}).get("data") or {}
            if int((payload or {}).get("success") or 0) != 1 or str(data.get("art_code") or "").upper() != art_code:
                return {}
            text = self._clean_text(str(data.get("notice_content") or ""))
            if len(text) < 80 or self._looks_like_page_chrome(text):
                return {}
            attachment_url = str(data.get("attach_url_web") or data.get("attach_url") or "")
            result = {
                "text": text[:max_chars],
                "title": self._clean_text(str(data.get("notice_title") or ""))[:180],
                "published_at": self._clean_text(str(data.get("notice_date") or data.get("eitime") or ""))[:19],
                "attachment_url": attachment_url if attachment_url.startswith("https://") else "",
                "content_source": endpoint,
                "art_code": art_code,
            }
            self._announcement_detail_cache[art_code] = (time.time(), result)
            return dict(result)
        except Exception:
            return {}

    def _fetch_text_excerpt(self, url: str, max_chars: int = 1200) -> str:
        if not url or not str(url).startswith("http"):
            return ""
        cached = self._content_cache.get(url)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return cached[1]
        resp = self.http.get(url, headers={"Referer": "https://www.eastmoney.com/"})
        ctype = (resp.headers.get("Content-Type") or "").lower()
        raw = resp.content or b""
        # 公告 PDF / 附件二进制不做 HTML 文本解码，避免前端出现大量乱码。
        if "pdf" in ctype or url.lower().split("?")[0].endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")) or raw[:5] == b"%PDF-":
            self._content_cache[url] = (time.time(), "")
            return ""
        try:
            if not resp.encoding or resp.encoding.lower() in {"iso-8859-1", "latin-1"}:
                resp.encoding = resp.apparent_encoding or "utf-8"
        except Exception:
            pass
        text = resp.text or ""
        text = self._clean_text(text)
        if self._looks_garbled(text):
            self._content_cache[url] = (time.time(), "")
            return ""
        # 截取和业务/风险/财报相关的段落附近。
        keys = list(self.FINANCE_WORDS | self.RISK_WORDS | self.OPERATION_WORDS | self.POLICY_WORDS)
        pos = min([text.find(k) for k in keys if k in text] or [0])
        start = max(0, pos - 120)
        excerpt = text[start:start+max_chars]
        self._content_cache[url] = (time.time(), excerpt)
        return excerpt

    def _parse_item_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        s = str(value).strip()
        if not s:
            return None
        # 兼容“3天前/昨天/今天”等中文相对时间，以及 13位毫秒时间戳、10位秒时间戳、YYYY-MM-DD。
        now = datetime.now()
        if "刚刚" in s or "今天" in s:
            return now
        if "昨天" in s:
            return now - timedelta(days=1)
        if "前天" in s:
            return now - timedelta(days=2)
        mrel = re.search(r"(\d+)\s*(分钟前|小时前|天前|周前|月前)", s)
        if mrel:
            n = int(mrel.group(1)); unit = mrel.group(2)
            if unit == "分钟前": return now - timedelta(minutes=n)
            if unit == "小时前": return now - timedelta(hours=n)
            if unit == "天前": return now - timedelta(days=n)
            if unit == "周前": return now - timedelta(days=n*7)
            if unit == "月前": return now - timedelta(days=n*30)
        md = re.search(r"(\d{1,2})月(\d{1,2})日", s)
        if md:
            try:
                dt = datetime(now.year, int(md.group(1)), int(md.group(2)))
                if dt > now + timedelta(days=7):
                    dt = datetime(now.year-1, int(md.group(1)), int(md.group(2)))
                return dt
            except Exception:
                pass
        try:
            if re.fullmatch(r"\d{13}", s):
                return datetime.fromtimestamp(int(s) / 1000)
            if re.fullmatch(r"\d{10}", s):
                return datetime.fromtimestamp(int(s))
        except Exception:
            pass
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日 %H:%M:%S", "%Y年%m月%d日 %H:%M", "%Y年%m月%d日"]:
            try:
                target = s[:19] if "%S" in fmt else s[:16] if "%H" in fmt else s[:11] if "年" in fmt else s[:10]
                return datetime.strptime(target.strip(), fmt)
            except Exception:
                continue
        # 兼容“2025年07月21日07:07:34”“2025-7-21 7:07”等非固定宽度日期。
        mfull = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})(?:日)?(?:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?)?", s)
        if mfull:
            try:
                return datetime(int(mfull.group(1)), int(mfull.group(2)), int(mfull.group(3)), int(mfull.group(4) or 0), int(mfull.group(5) or 0), int(mfull.group(6) or 0))
            except Exception:
                pass
        m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", s)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                return None
        return None

    def _time_counts(self, items: list[NewsItem]) -> list[dict[str, Any]]:
        now = datetime.now()
        buckets = {"近30天": 0, "近90天": 0, "近1年": 0, "更早历史": 0, "未知日期": 0}
        for item in items:
            dt = self._parse_item_date(item.published_at_norm or item.published_at or item.date_display)
            if not dt:
                buckets["未知日期"] += 1
                continue
            days = (now - dt).days
            if days <= 30:
                buckets["近30天"] += 1
            elif days <= 90:
                buckets["近90天"] += 1
            elif days <= 365:
                buckets["近1年"] += 1
            else:
                buckets["更早历史"] += 1
        return [{"name": k, "count": v, "pct": round(v / max(1, len(items)) * 100, 1)} for k, v in buckets.items() if v]

    def _counts(self, values: list[str]) -> list[dict[str, Any]]:
        d: dict[str, int] = {}
        for v in values:
            d[v] = d.get(v, 0) + 1
        total = sum(d.values()) or 1
        return [{"name": k, "count": v, "pct": round(v / total * 100, 1)} for k, v in sorted(d.items(), key=lambda kv: kv[1], reverse=True)]

    def _fingerprint(self, title: str) -> str:
        s = re.sub(r"[\W_]+", "", title.lower())
        return s[:32]

    def _looks_garbled(self, text: str) -> bool:
        s = str(text or "")
        if not s:
            return False
        bad = s.count("�")
        controls = sum(1 for ch in s if ord(ch) < 32 and ch not in "\n\r\t")
        # 中文财经正文一般不会有高比例替换字符/控制字符；PDF二进制误读会明显超过该阈值。
        return (bad + controls) >= max(6, int(len(s) * 0.04))

    def _clean_text(self, text: str) -> str:
        text = strip_html_boilerplate(text)
        text = text.replace("​", "").replace("﻿", "").replace(" ", " ")
        text = re.sub(r"&nbsp;|&#160;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if _ftfy_fix_text is not None:
            try:
                # Repair mojibake without converting Chinese full-width punctuation.
                # Punctuation is part of titles and event fingerprints in the news pipeline.
                text = _ftfy_fix_text(text, fix_character_width=False)
            except Exception:
                pass
        if self._looks_garbled(text):
            return ""
        return text.strip()

    def _load_cache(self) -> dict[str, Any]:
        with self._cache_file_lock:
            try:
                if self.cache_file.exists():
                    return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        data = self._load_cache().get(key)
        if not data:
            return None
        if time.time() - float(data.get("_saved_at", 0)) > self.cache_ttl_seconds:
            return None
        result = data.get("result")
        return result if isinstance(result, dict) else None

    def _write_cache(self, key: str, result: dict[str, Any]) -> None:
        with self._cache_file_lock:
            cache = self._load_cache()
            cache[key] = {"_saved_at": time.time(), "result": result}
            if len(cache) > 260:
                items = sorted(cache.items(), key=lambda kv: kv[1].get("_saved_at", 0), reverse=True)[:210]
                cache = dict(items)
            self.cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
