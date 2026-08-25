from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import re
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from quant_data.market_calendar import MarketCalendar
from quant_data.utils import ThrottledSession


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        number = float(str(value).replace(",", ""))
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _as_shanghai(value: datetime | None = None) -> datetime:
    current = value or datetime.now(SHANGHAI_TZ)
    if current.tzinfo is None:
        return current.replace(tzinfo=SHANGHAI_TZ)
    return current.astimezone(SHANGHAI_TZ)


@dataclass(frozen=True)
class GlobalMarketSpec:
    key: str
    name: str
    code: str
    region: str
    timezone: str
    cluster: str
    instrument_type: str
    base_weight: float
    technology_relevance: float
    priority: int
    source_url: str
    correlation_family: str = ""
    family_cap: float = 1.0


@dataclass(frozen=True)
class SectorBenchmarkProfile:
    key: str
    label: str
    keywords: tuple[str, ...]
    benchmark_keys: tuple[str, ...]
    reason: str


GLOBAL_TECH_SPECS = (
    GlobalMarketSpec(
        "hang_seng_tech",
        "恒生科技指数",
        "rt_hkHSTECH",
        "中国香港",
        "Asia/Hong_Kong",
        "hong_kong_tech",
        "cash_index",
        0.36,
        1.0,
        100,
        "https://finance.sina.com.cn/stock/hkstock/marketalerts.shtml",
        "greater_china_technology",
        0.30,
    ),
    GlobalMarketSpec(
        "nasdaq_100_futures",
        "纳斯达克100指数期货",
        "hf_NQ",
        "美国期货",
        "America/New_York",
        "us_tech_direction",
        "futures",
        0.40,
        1.0,
        95,
        "https://finance.sina.com.cn/futures/quotes/NQ.shtml",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "nasdaq_100",
        "纳斯达克100指数",
        "gb_ndx",
        "美国",
        "America/New_York",
        "us_tech_direction",
        "cash_index",
        0.40,
        1.0,
        100,
        "https://stock.finance.sina.com.cn/usstock/quotes/.NDX.html",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "nasdaq_composite",
        "纳斯达克综合指数",
        "gb_ixic",
        "美国",
        "America/New_York",
        "us_tech_direction",
        "cash_index",
        0.34,
        0.85,
        80,
        "https://stock.finance.sina.com.cn/usstock/quotes/.IXIC.html",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "philadelphia_semiconductor",
        "费城半导体指数",
        "gb_sox",
        "美国",
        "America/New_York",
        "us_semiconductor_direction",
        "cash_index",
        0.20,
        1.0,
        100,
        "https://stock.finance.sina.com.cn/usstock/quotes/.SOX.html",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "sp500_futures",
        "标普500指数期货",
        "hf_ES",
        "美国期货",
        "America/New_York",
        "us_broad_market_direction",
        "futures",
        0.12,
        0.58,
        90,
        "https://finance.sina.com.cn/futures/quotes/ES.shtml",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "dow_jones",
        "道琼斯工业指数",
        "gb_dji",
        "美国",
        "America/New_York",
        "us_broad_market_direction",
        "cash_index",
        0.08,
        0.32,
        80,
        "https://stock.finance.sina.com.cn/usstock/quotes/.DJI.html",
        "us_equity_risk",
        0.52,
    ),
    GlobalMarketSpec(
        "nikkei_225",
        "日经225指数",
        "b_NKY",
        "日本",
        "Asia/Tokyo",
        "japan_risk_proxy",
        "cash_index",
        0.12,
        0.42,
        60,
        "https://finance.sina.com.cn/stock/globalindex/quotes/NKY.shtml",
        "japan_equity_risk",
        0.12,
    ),
    GlobalMarketSpec(
        "kospi",
        "韩国综合指数",
        "b_KOSPI",
        "韩国",
        "Asia/Seoul",
        "korea_risk_proxy",
        "cash_index",
        0.12,
        0.45,
        60,
        "https://finance.sina.com.cn/stock/globalindex/quotes/KOSPI.shtml",
        "korea_equity_risk",
        0.12,
    ),
)


def _us_etf_spec(key: str, name: str, ticker: str, *, cluster: str | None = None) -> GlobalMarketSpec:
    return GlobalMarketSpec(
        key,
        name,
        f"gb_{ticker.lower()}",
        "美国",
        "America/New_York",
        cluster or f"sector_{key}",
        "cash_index",
        0.52,
        1.0,
        100,
        f"https://stock.finance.sina.com.cn/usstock/quotes/{ticker.upper()}.html",
        "sector_benchmark",
        0.68,
    )


def _global_future_spec(key: str, name: str, code: str) -> GlobalMarketSpec:
    return GlobalMarketSpec(
        key,
        name,
        f"hf_{code.upper()}",
        "全球商品",
        "America/New_York",
        f"sector_{key}",
        "futures",
        0.52,
        1.0,
        100,
        f"https://finance.sina.com.cn/futures/quotes/{code.upper()}.shtml",
        "sector_benchmark",
        0.68,
    )


INDUSTRY_MARKET_SPECS = (
    _us_etf_spec("us_technology", "美国科技板块ETF", "XLK"),
    _us_etf_spec("us_financial", "美国金融板块ETF", "XLF"),
    _us_etf_spec("us_healthcare", "美国医疗保健板块ETF", "XLV"),
    _us_etf_spec("us_energy", "美国能源板块ETF", "XLE"),
    _us_etf_spec("us_industrial", "美国工业板块ETF", "XLI"),
    _us_etf_spec("us_consumer_discretionary", "美国可选消费板块ETF", "XLY"),
    _us_etf_spec("us_consumer_staples", "美国必选消费板块ETF", "XLP"),
    _us_etf_spec("us_materials", "美国材料板块ETF", "XLB"),
    _us_etf_spec("us_utilities", "美国公用事业板块ETF", "XLU"),
    _us_etf_spec("us_real_estate", "美国房地产板块ETF", "XLRE"),
    _us_etf_spec("us_biotech", "美国生物科技板块ETF", "XBI"),
    _us_etf_spec("global_solar", "全球太阳能板块ETF", "TAN"),
    _us_etf_spec("global_lithium_battery", "全球锂电池产业ETF", "LIT"),
    _us_etf_spec("china_internet", "中国互联网公司ETF", "KWEB"),
    _us_etf_spec("us_aerospace_defense", "美国航空航天与国防ETF", "ITA"),
    _us_etf_spec("us_transportation", "美国运输板块ETF", "IYT"),
    _us_etf_spec("global_cybersecurity", "全球网络安全ETF", "CIBR"),
    _us_etf_spec("global_robotics_ai", "全球机器人与人工智能ETF", "BOTZ"),
    _us_etf_spec("global_rare_earth", "全球稀土战略金属ETF", "REMX"),
    _us_etf_spec("global_uranium", "全球铀与核能ETF", "URA"),
    _global_future_spec("crude_oil", "纽约原油期货", "CL"),
    _global_future_spec("gold", "纽约黄金期货", "GC"),
    _global_future_spec("copper", "纽约铜期货", "HG"),
)


BROAD_GLOBAL_KEYS = frozenset(
    {
        "hang_seng_tech",
        "nasdaq_100_futures",
        "nasdaq_100",
        "nasdaq_composite",
        "sp500_futures",
        "dow_jones",
        "nikkei_225",
        "kospi",
    }
)


SECTOR_BENCHMARK_PROFILES = (
    SectorBenchmarkProfile(
        "semiconductor",
        "半导体",
        ("半导体", "芯片", "集成电路", "晶圆", "封测", "功率器件", "存储芯片"),
        ("philadelphia_semiconductor", "us_technology"),
        "半导体优先参考费城半导体指数，科技板块ETF只作补充。",
    ),
    SectorBenchmarkProfile(
        "solar",
        "光伏与太阳能",
        ("光伏", "太阳能", "硅料", "硅片", "逆变器", "光伏组件"),
        ("global_solar",),
        "光伏产业参考全球太阳能板块ETF，不使用费城半导体替代。",
    ),
    SectorBenchmarkProfile(
        "lithium_battery",
        "锂电池与新能源车",
        ("锂电", "动力电池", "新能源车", "新能源汽车", "储能", "固态电池", "电池材料"),
        ("global_lithium_battery", "us_consumer_discretionary"),
        "锂电与新能源车优先参考全球锂电池产业ETF，可选消费仅作需求侧补充。",
    ),
    SectorBenchmarkProfile(
        "ai_software",
        "人工智能与软件",
        ("人工智能", "AI", "算力", "机器人", "软件", "云计算", "网络安全", "数据中心"),
        ("global_robotics_ai", "global_cybersecurity", "us_technology"),
        "人工智能和软件按机器人、网络安全及科技板块代理组合观察。",
    ),
    SectorBenchmarkProfile(
        "internet",
        "互联网平台",
        ("互联网", "电商", "平台经济", "网络游戏", "传媒", "在线服务"),
        ("china_internet", "hang_seng_tech"),
        "中国互联网公司优先参考海外上市中国互联网ETF和恒生科技。",
    ),
    SectorBenchmarkProfile(
        "healthcare",
        "医药与生物科技",
        ("医药", "医疗", "创新药", "生物", "疫苗", "医疗器械", "制药"),
        ("us_healthcare", "us_biotech"),
        "医药板块参考医疗保健宽行业和生物科技高弹性代理。",
    ),
    SectorBenchmarkProfile(
        "financial",
        "银行与金融",
        ("银行", "券商", "证券", "保险", "金融", "财富管理", "期货公司"),
        ("us_financial",),
        "银行、券商和保险参考海外金融板块ETF。",
    ),
    SectorBenchmarkProfile(
        "gold",
        "黄金与贵金属",
        ("黄金", "贵金属", "金矿"),
        ("gold", "us_materials"),
        "黄金产业优先参考黄金期货，材料板块只作权益侧补充。",
    ),
    SectorBenchmarkProfile(
        "energy",
        "能源与油气",
        ("石油", "天然气", "油气", "能源", "煤炭", "炼化"),
        ("us_energy", "crude_oil"),
        "能源板块结合能源权益代理和原油期货方向。",
    ),
    SectorBenchmarkProfile(
        "materials",
        "材料、有色与化工",
        ("有色", "铜", "稀土", "材料", "化工", "钢铁", "矿业", "金属"),
        ("us_materials", "copper", "global_rare_earth"),
        "材料板块按海外材料权益、铜价和稀土战略金属代理组合观察。",
    ),
    SectorBenchmarkProfile(
        "industrial_defense",
        "工业制造与军工",
        ("工业", "机械", "军工", "国防", "航空", "航天", "船舶", "高端制造"),
        ("us_industrial", "us_aerospace_defense"),
        "工业制造参考工业板块，军工航空再叠加航空航天与国防代理。",
    ),
    SectorBenchmarkProfile(
        "transportation",
        "交通运输与物流",
        ("交通", "运输", "航运", "物流", "港口", "航空运输"),
        ("us_transportation",),
        "交通运输参考海外运输板块ETF。",
    ),
    SectorBenchmarkProfile(
        "consumer_discretionary",
        "可选消费",
        ("汽车", "家电", "旅游", "酒店", "零售", "可选消费"),
        ("us_consumer_discretionary",),
        "汽车、家电、旅游和零售参考可选消费板块ETF。",
    ),
    SectorBenchmarkProfile(
        "consumer_staples",
        "食品饮料与农业",
        ("食品", "饮料", "白酒", "农业", "农牧", "饲料", "养殖", "必选消费"),
        ("us_consumer_staples",),
        "食品饮料和农业使用必选消费板块作为公开市场风险代理。",
    ),
    SectorBenchmarkProfile(
        "utilities_nuclear",
        "公用事业与核能",
        ("电力", "公用事业", "核电", "核能", "铀"),
        ("us_utilities", "global_uranium"),
        "公用事业参考防御型公用事业板块，核能主题补充铀产业代理。",
    ),
    SectorBenchmarkProfile(
        "real_estate",
        "房地产与建筑",
        ("房地产", "地产", "物业", "建筑", "建材"),
        ("us_real_estate", "us_industrial"),
        "房地产优先参考海外房地产板块，建筑只以工业板块辅助。",
    ),
)


SPEC_BY_KEY = {spec.key: spec for spec in (*GLOBAL_TECH_SPECS, *INDUSTRY_MARKET_SPECS)}
ALL_GLOBAL_MARKET_SPECS = tuple(SPEC_BY_KEY.values())


class SinaGlobalMarketProvider:
    """Read a small, explicit global index set from Sina's public quote page API."""

    source_id = "sina_global_quote"
    source_name = "新浪全球行情"
    endpoint = "https://hq.sinajs.cn/list={codes}"

    def __init__(self) -> None:
        self.http = ThrottledSession()
        self.http.session.headers.update({"Referer": "https://finance.sina.com.cn/"})

    def fetch(self, specs: Iterable[GlobalMarketSpec] = ALL_GLOBAL_MARKET_SPECS) -> list[dict[str, Any]]:
        selected = list(specs)
        response = self.http.get(self.endpoint.format(codes=",".join(item.code for item in selected)))
        text = response.content.decode("gbk", errors="ignore")
        raw = {
            match.group(1): match.group(2)
            for match in re.finditer(r'var\s+hq_str_([^=]+)="(.*?)";', text)
        }
        rows = []
        for spec in selected:
            values = str(raw.get(spec.code) or "").split(",")
            parsed = self._parse(spec, values)
            if parsed:
                rows.append(parsed)
        return rows

    def _parse(self, spec: GlobalMarketSpec, values: list[str]) -> dict[str, Any] | None:
        last: float | None = None
        change_pct: float | None = None
        observed_at: datetime | None = None
        name = spec.name
        try:
            if spec.code.startswith("gb_") and len(values) >= 4:
                name = values[0] or name
                last = _number(values[1])
                change_pct = _number(values[2])
                observed_at = self._parse_datetime(values[3], spec.timezone)
            elif spec.code.startswith("hf_") and len(values) >= 13:
                last = _number(values[0])
                previous_settlement = _number(values[7])
                change_pct = (last / previous_settlement - 1.0) * 100 if last and previous_settlement else None
                observed_at = self._parse_datetime(f"{values[12]} {values[6]}", "Asia/Shanghai")
                name = values[13] if len(values) > 13 and values[13] else name
            elif spec.code.startswith(("rt_hk", "hk")) and len(values) >= 19:
                name = values[1] or name
                last = _number(values[6])
                change_pct = _number(values[8])
                observed_at = self._parse_datetime(f"{values[17]} {values[18]}", spec.timezone)
            elif spec.code.startswith("b_") and len(values) >= 7:
                name = values[0] or name
                last = _number(values[1])
                change_pct = _number(values[3])
                observed_at = self._parse_datetime(f"{values[6]} {values[5]}", spec.timezone)
        except (IndexError, ValueError):
            return None
        if last is None or last <= 0 or change_pct is None or observed_at is None:
            return None
        return {
            "key": spec.key,
            "name": name,
            "code": spec.code,
            "region": spec.region,
            "timezone": spec.timezone,
            "cluster": spec.cluster,
            "instrument_type": spec.instrument_type,
            "base_weight": spec.base_weight,
            "technology_relevance": spec.technology_relevance,
            "priority": spec.priority,
            "correlation_family": spec.correlation_family or spec.cluster,
            "family_cap": spec.family_cap,
            "last": round(last, 6),
            "change_pct": round(change_pct, 6),
            "observed_at": observed_at.isoformat(timespec="seconds"),
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_ref": spec.source_url,
        }

    @staticmethod
    def _parse_datetime(value: str, timezone_name: str) -> datetime | None:
        raw = str(value or "").strip().replace("/", "-")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=ZoneInfo(timezone_name))
            except ValueError:
                continue
        return None


class GlobalMarketSentimentService:
    """Build a session-aware global context using the selected sector's benchmarks."""

    cache_kind = "global_market_sentiment"
    cache_key = "latest"
    cache_ttl_seconds = 45

    def __init__(self, cache_state: Any | None = None, provider: Any | None = None, calendar: MarketCalendar | None = None) -> None:
        self.cache_state = cache_state
        self.provider = provider or SinaGlobalMarketProvider()
        self.calendar = calendar or MarketCalendar()

    def snapshot(
        self,
        *,
        force: bool = False,
        allow_network: bool = True,
        now: datetime | None = None,
        symbol: str = "",
        profile: dict[str, Any] | None = None,
        focus_terms: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        current = _as_shanghai(now)
        focus = self.resolve_focus(profile=profile, focus_terms=focus_terms)
        cached = self._read_cache(allow_stale=True)
        cache_status = dict(cached.get("cache_status") or {})
        cached_payload = dict(cached.get("data") or {})
        cached_observations = list(cached_payload.get("observations") or [])
        cached_fetched_keys = list(cached_payload.get("fetched_keys") or [])
        cache_covers_focus = self._cache_covers_focus(cached_observations, focus, cached_fetched_keys)
        if cached_observations and cache_covers_focus and not force and not bool(cache_status.get("stale")):
            result = self.analyze(cached_observations, now=current, focus=focus, requested_symbol=symbol)
            result["cache_status"] = cache_status
            return result
        if not allow_network:
            result = self.analyze(cached_observations, now=current, focus=focus, requested_symbol=symbol)
            result["cache_status"] = cache_status or {"status": "miss", "stale": True}
            if not cached_observations:
                result["missing_reasons"].append("全球市场缓存缺失；当前调用禁止联网刷新")
            elif not cache_covers_focus:
                result["missing_reasons"].append(f"缓存尚未包含{focus['profile_label']}对应的海外行业基准")
            return result
        try:
            observations = list(self.provider.fetch(ALL_GLOBAL_MARKET_SPECS) or [])
        except Exception as exc:
            result = self.analyze(cached_observations, now=current, focus=focus, requested_symbol=symbol)
            result["cache_status"] = cache_status or {"status": "error", "stale": True}
            result["source_error"] = str(exc)[:240]
            if not cached_observations:
                result["missing_reasons"].append(f"新浪全球行情请求失败：{str(exc)[:160]}")
            return result
        result = self.analyze(observations, now=current, focus=focus, requested_symbol=symbol)
        result["cache_status"] = self._write_cache(observations, result)
        return result

    def analyze(
        self,
        observations: Iterable[dict[str, Any]],
        *,
        now: datetime | None = None,
        focus: dict[str, Any] | None = None,
        requested_symbol: str = "",
        profile: dict[str, Any] | None = None,
        focus_terms: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        current = _as_shanghai(now)
        source_rows = [dict(row) for row in observations if isinstance(row, dict)]
        focus_context = focus or self.resolve_focus(profile=profile, focus_terms=focus_terms)
        if focus is not None or profile is not None or focus_terms:
            source_rows = self._observations_for_focus(source_rows, focus_context)
        rows = [self._decorate(row, current) for row in source_rows]
        rows = [row for row in rows if row.get("change_pct") is not None and row.get("observed_at")]
        candidates = [row for row in rows if row.get("score_eligible")]
        selected: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for cluster in sorted({str(row.get("cluster") or row.get("key")) for row in candidates}):
            grouped = [row for row in candidates if str(row.get("cluster") or row.get("key")) == cluster]
            grouped.sort(key=lambda row: (float(row.get("phase_multiplier") or 0), int(row.get("priority") or 0)), reverse=True)
            selected.append(grouped[0])
            excluded.extend({**row, "excluded_reason": f"与 {grouped[0].get('name')} 同属相关性分组，避免重复计分"} for row in grouped[1:])
        excluded.extend({**row, "excluded_reason": row.get("missing_reason") or "数据不可用于评分"} for row in rows if not row.get("score_eligible"))
        family_rows: dict[str, list[dict[str, Any]]] = {}
        for row in selected:
            family = str(row.get("correlation_family") or row.get("cluster") or row.get("key"))
            row["correlation_family"] = family
            family_rows.setdefault(family, []).append(row)
        family_weights: dict[str, float] = {}
        for family, grouped in family_rows.items():
            raw_family_weight = sum(float(row.get("effective_weight") or 0) for row in grouped)
            caps = [float(row.get("family_cap") or 1.0) for row in grouped]
            family_weights[family] = min(raw_family_weight, min(caps) if caps else raw_family_weight)
        total_family_weight = sum(family_weights.values())
        for family, grouped in family_rows.items():
            raw_family_weight = sum(float(row.get("effective_weight") or 0) for row in grouped)
            normalized_family_weight = family_weights[family] / total_family_weight if total_family_weight > 0 else 0.0
            for row in grouped:
                inside_family = float(row.get("effective_weight") or 0) / raw_family_weight if raw_family_weight > 0 else 0.0
                normalized = normalized_family_weight * inside_family
                row["family_normalized_weight"] = round(normalized_family_weight, 6)
                row["normalized_weight"] = round(normalized, 6)
                row["contribution"] = round(float(row.get("raw_score") or 50) * normalized, 4)
        if selected:
            rounding_drift = round(1.0 - sum(float(row.get("normalized_weight") or 0) for row in selected), 6)
            selected[-1]["normalized_weight"] = round(float(selected[-1].get("normalized_weight") or 0) + rounding_drift, 6)
            selected[-1]["contribution"] = round(
                float(selected[-1].get("raw_score") or 50) * float(selected[-1]["normalized_weight"]),
                4,
            )
        score = sum(float(row.get("contribution") or 0) for row in selected) if selected else None
        direct_count = sum(1 for row in selected if float(row.get("focus_relevance") or row.get("technology_relevance") or 0) >= 0.8)
        sector_count = sum(1 for row in selected if row.get("benchmark_role") == "行业基准")
        live_count = sum(1 for row in selected if row.get("session_phase") in {"实时交易", "期货实时", "盘前实时", "盘后实时"})
        family_count = len(family_rows)
        mapped = focus_context.get("mapping_status") == "matched"
        valid_for_score = family_count >= 2 and live_count >= 1 and (sector_count >= 1 if mapped else direct_count >= 1)
        missing_reasons: list[str] = []
        if family_count < 2:
            missing_reasons.append("全球行业背景至少需要两个去重后的行业/宽基资产族证据")
        if mapped and sector_count < 1:
            missing_reasons.append(f"缺少{focus_context['profile_label']}对应的可用海外行业基准")
        if not mapped and direct_count < 1:
            missing_reasons.append("未匹配具体行业，且缺少可用的全球宽基方向证据")
        if live_count < 1:
            missing_reasons.append("当前只有前收盘或过期数据，不能作为实时交易环境分")
        if not rows:
            missing_reasons.append("所选行业的海外基准/全球宽基行情源未返回有效数据")
        label = self._label(score) if score is not None else "数据不足"
        benchmark_catalog = [
            {
                "key": key,
                "name": SPEC_BY_KEY[key].name,
                "code": SPEC_BY_KEY[key].code,
                "source_ref": SPEC_BY_KEY[key].source_url,
            }
            for key in focus_context.get("benchmark_keys") or []
            if key in SPEC_BY_KEY
        ]
        return {
            "as_of": current.isoformat(timespec="seconds"),
            "target_market": "A股",
            "requested_symbol": requested_symbol,
            "selection_mode": "行业动态映射" if mapped else "全球宽基背景",
            "focus_key": focus_context.get("profile_key"),
            "focus_label": focus_context.get("profile_label"),
            "focus_reason": focus_context.get("mapping_reason"),
            "focus_confidence": focus_context.get("confidence"),
            "matched_terms": focus_context.get("matched_terms") or [],
            "mapping_status": focus_context.get("mapping_status"),
            "benchmark_catalog": benchmark_catalog,
            "score": round(score, 2) if score is not None else None,
            "label": label,
            "quality_status": "available" if valid_for_score and len(selected) >= 3 else "partial" if valid_for_score else "insufficient_evidence",
            "valid_for_score": valid_for_score,
            "evidence_units": len(selected),
            "correlation_family_units": family_count,
            "direct_technology_units": direct_count,
            "sector_benchmark_units": sector_count,
            "broad_benchmark_units": sum(1 for row in selected if row.get("benchmark_role") == "全球宽基背景"),
            "live_units": live_count,
            "observations": rows,
            "selected_evidence": selected,
            "excluded_evidence": excluded,
            "missing_reasons": list(dict.fromkeys(missing_reasons)),
            "score_definition": "先按当前股票的行业、主营和题材选择对应海外行业指数/ETF/商品期货，再叠加少量全球宽基背景；以50为中性，按真实涨跌幅、交易阶段和陈旧度加权。",
            "time_alignment_policy": "各国家和资产按当地开盘时间分别判断；现金盘休市时只以前收盘降权参考，仍在交易的期货可作为实时背景，不把隔夜走势伪装成当前行情。",
            "correlation_policy": "同一指数簇先去重，行业代理合计权重设上限，全球宽基只作背景；例如半导体优先费城半导体，光伏不会套用费城半导体。",
            "truth_boundary": "行业海外基准只说明外部同类资产和风险偏好的可能传导，不代表A股个股必然同步；缺失、过期、无法映射或单一证据不触发自动买入。",
        }

    def resolve_focus(
        self,
        *,
        profile: dict[str, Any] | None = None,
        focus_terms: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        data = dict(profile or {})
        explicit_values = self._as_terms(focus_terms)
        buckets = {
            "explicit": explicit_values,
            "industry": self._as_terms([data.get("industry"), data.get("sector"), data.get("board_name")]),
            "tags": self._as_terms([data.get("business_tags"), data.get("tags"), data.get("concepts")]),
            "products": self._as_terms(
                [
                    data.get("main_products"),
                    data.get("business_segments"),
                    data.get("upstream"),
                    data.get("downstream"),
                ]
            ),
        }
        weights = {"explicit": 6.0, "industry": 4.0, "tags": 2.0, "products": 1.0}
        matches: list[tuple[float, int, SectorBenchmarkProfile, list[str]]] = []
        for order, candidate in enumerate(SECTOR_BENCHMARK_PROFILES):
            score = 0.0
            matched: list[str] = []
            for keyword in candidate.keywords:
                hit = False
                for bucket, values in buckets.items():
                    if any(self._term_contains(value, keyword) for value in values):
                        score += weights[bucket]
                        hit = True
                if hit:
                    matched.append(keyword)
            if score > 0:
                matches.append((score, -order, candidate, list(dict.fromkeys(matched))))
        if not matches:
            return {
                "profile_key": "broad_market",
                "profile_label": "全球宽基背景",
                "benchmark_keys": [],
                "mapping_reason": "当前公司画像没有匹配到可靠行业代理，仅使用全球宽基背景，不强行套用费城半导体或其他行业指数。",
                "matched_terms": [],
                "confidence": "未映射",
                "mapping_status": "broad_only",
            }
        score, _, selected, matched = max(matches, key=lambda item: (item[0], item[1]))
        confidence = "高" if score >= 10 else "中" if score >= 5 else "低"
        return {
            "profile_key": selected.key,
            "profile_label": selected.label,
            "benchmark_keys": list(selected.benchmark_keys),
            "mapping_reason": selected.reason,
            "matched_terms": matched,
            "confidence": confidence,
            "mapping_score": round(score, 2),
            "mapping_status": "matched",
        }

    def _observations_for_focus(self, observations: list[dict[str, Any]], focus: dict[str, Any]) -> list[dict[str, Any]]:
        benchmark_keys = set(focus.get("benchmark_keys") or [])
        allowed = set(BROAD_GLOBAL_KEYS) | benchmark_keys
        mapped = focus.get("mapping_status") == "matched"
        selected: list[dict[str, Any]] = []
        for original in observations:
            key = str(original.get("key") or "")
            if key not in allowed:
                continue
            row = dict(original)
            if key in benchmark_keys:
                row.update(
                    {
                        "benchmark_role": "行业基准",
                        "focus_relevance": 1.0,
                        "technology_relevance": 1.0,
                        "base_weight": max(0.52, float(row.get("base_weight") or 0.0)),
                        "correlation_family": "sector_benchmark",
                        "family_cap": 0.68,
                        "selection_reason": focus.get("mapping_reason"),
                    }
                )
            else:
                row["benchmark_role"] = "全球宽基背景"
                row["focus_relevance"] = float(row.get("technology_relevance") or 0.5)
                row["selection_reason"] = "用于控制全球整体风险背景，不替代所选行业基准"
                if mapped:
                    row["base_weight"] = float(row.get("base_weight") or 0.0) * 0.28
            selected.append(row)
        return selected

    @staticmethod
    def _as_terms(values: Any) -> list[str]:
        output: list[str] = []

        def visit(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)
                return
            for item in re.split(r"[，,；;、|/\n]+", str(value)):
                cleaned = item.strip()
                if cleaned:
                    output.append(cleaned)

        visit(values)
        return list(dict.fromkeys(output))

    @staticmethod
    def _term_contains(value: str, keyword: str) -> bool:
        text = str(value or "").casefold()
        needle = str(keyword or "").casefold()
        if not needle:
            return False
        if needle.isascii() and len(needle) <= 3:
            return bool(re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text))
        return needle in text

    @staticmethod
    def _cache_covers_focus(
        observations: list[dict[str, Any]],
        focus: dict[str, Any],
        fetched_keys: Iterable[str] | None = None,
    ) -> bool:
        keys = {str(value or "") for value in (fetched_keys or [])}
        keys.update(str(row.get("key") or "") for row in observations)
        required = set(focus.get("benchmark_keys") or [])
        return bool(keys & BROAD_GLOBAL_KEYS) and (not required or required.issubset(keys))

    def _decorate(self, row: dict[str, Any], now: datetime) -> dict[str, Any]:
        observed = self._parse_observed(row.get("observed_at"), row.get("timezone") or "Asia/Shanghai")
        age_seconds = max(0.0, (now.astimezone(observed.tzinfo) - observed).total_seconds()) if observed else None
        phase, phase_multiplier, phase_reason = self._phase(row, observed, now, age_seconds)
        change_pct = _number(row.get("change_pct"))
        technology_relevance = _clamp(
            _number(row.get("focus_relevance"))
            if row.get("focus_relevance") is not None
            else _number(row.get("technology_relevance")) or 0.0,
            0.0,
            1.0,
        )
        raw_score = _clamp(50 + (change_pct or 0.0) * 8.0, 20, 80) if change_pct is not None else None
        effective_weight = (
            float(row.get("base_weight") or 0.0) * technology_relevance * phase_multiplier
            if raw_score is not None
            else 0.0
        )
        score_eligible = bool(observed and change_pct is not None and phase_multiplier > 0 and effective_weight > 0)
        return {
            **row,
            "observed_at": observed.isoformat(timespec="seconds") if observed else None,
            "age_seconds": round(age_seconds, 2) if age_seconds is not None else None,
            "session_phase": phase,
            "phase_multiplier": round(phase_multiplier, 4),
            "phase_reason": phase_reason,
            "raw_score": round(raw_score, 2) if raw_score is not None else None,
            "focus_relevance": round(technology_relevance, 4),
            "effective_weight": round(effective_weight, 6),
            "score_eligible": score_eligible,
            "stale": phase_multiplier <= 0,
            "missing_reason": "" if score_eligible else phase_reason,
        }

    def _phase(
        self,
        row: dict[str, Any],
        observed: datetime | None,
        now: datetime,
        age_seconds: float | None,
    ) -> tuple[str, float, str]:
        if observed is None or age_seconds is None:
            return "时间缺失", 0.0, "数据源没有可解析的行情时间"
        instrument_type = str(row.get("instrument_type") or "cash_index")
        key = str(row.get("key") or "")
        source_date = observed.date()
        if instrument_type == "futures":
            if age_seconds <= 15 * 60:
                return "期货实时", 1.0, "电子盘行情在15分钟新鲜度范围内"
            if age_seconds <= 36 * 3600:
                return "前结算参考", 0.35, "期货行情不是实时，仅以前结算方向降权参考"
            return "已过期", 0.0, "期货行情超过36小时"
        if key == "hang_seng_tech":
            session = self.calendar.session("HK", now=now)
            if session.get("status") in {"pre_open_auction", "morning", "afternoon", "closing_auction"} and age_seconds <= 15 * 60:
                return "实时交易", 1.0, str(session.get("label") or "港股交易时段")
            if age_seconds <= 72 * 3600:
                return "前收盘参考", 0.45, f"港股当前{session.get('label') or '未交易'}，使用最近收盘并降权"
            return "已过期", 0.0, "港股行情超过72小时"
        if instrument_type == "cash_index" and str(row.get("timezone") or "") == "America/New_York":
            session = self.calendar.session("US", now=now)
            us_now = now.astimezone(ZoneInfo("America/New_York"))
            source_date = observed.astimezone(ZoneInfo("America/New_York")).date()
            if session.get("status") == "regular" and source_date == us_now.date() and age_seconds <= 15 * 60:
                return "实时交易", 1.0, "美股常规交易时段实时行业指数/ETF"
            if age_seconds <= 96 * 3600:
                return "前收盘参考", 0.42, f"美股当前{session.get('label') or '未交易'}，行业指数/ETF只作前收盘参考"
            return "已过期", 0.0, "美股行业指数/ETF行情超过96小时"
        local_now = now.astimezone(ZoneInfo(str(row.get("timezone") or "Asia/Shanghai")))
        open_now = self._regional_cash_open(key, local_now)
        if open_now and source_date == local_now.date() and age_seconds <= 15 * 60:
            return "实时交易", 1.0, "当地现金市场交易时段"
        if age_seconds <= 72 * 3600:
            return "前收盘参考", 0.38, "当地市场未开盘或已收盘，使用最近收盘并降权"
        return "已过期", 0.0, "区域指数行情超过72小时"

    @staticmethod
    def _regional_cash_open(key: str, now: datetime) -> bool:
        if now.weekday() >= 5:
            return False
        current = now.time()
        if key == "nikkei_225":
            return time(9, 0) <= current < time(11, 30) or time(12, 30) <= current < time(15, 30)
        if key == "kospi":
            return time(9, 0) <= current < time(15, 30)
        return False

    @staticmethod
    def _parse_observed(value: Any, timezone_name: str) -> datetime | None:
        if isinstance(value, datetime):
            parsed = value
        else:
            raw = str(value or "").strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(raw)
            except ValueError:
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
        return parsed

    def _read_cache(self, *, allow_stale: bool) -> dict[str, Any]:
        if self.cache_state is None:
            return {"data": None, "cache_status": {"status": "miss", "stale": True}}
        read = self.cache_state.get(
            self.cache_kind,
            self.cache_key,
            allow_stale=allow_stale,
            ttl_seconds=self.cache_ttl_seconds,
        )
        return {"data": read.data, "cache_status": read.cache_status}

    def _write_cache(self, observations: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
        if self.cache_state is None:
            return {"status": "memory", "stale": False}
        payload = {
            "observations": observations,
            "fetched_keys": [spec.key for spec in ALL_GLOBAL_MARKET_SPECS],
            "catalog_version": "v327-sector-aware-1",
            "score": result.get("score"),
            "quality_status": result.get("quality_status"),
            "valid_for_score": result.get("valid_for_score"),
            "as_of": result.get("as_of"),
        }
        return self.cache_state.put(
            self.cache_kind,
            self.cache_key,
            payload,
            ttl_seconds=self.cache_ttl_seconds,
            source="sina_global_quote",
        )

    @staticmethod
    def _label(score: float | None) -> str:
        if score is None:
            return "数据不足"
        return "明显偏强" if score >= 65 else "偏强" if score >= 56 else "中性" if score >= 44 else "偏弱" if score >= 35 else "明显承压"
