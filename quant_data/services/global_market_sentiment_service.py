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


class SinaGlobalMarketProvider:
    """Read a small, explicit global index set from Sina's public quote page API."""

    source_id = "sina_global_quote"
    source_name = "新浪全球行情"
    endpoint = "https://hq.sinajs.cn/list={codes}"

    def __init__(self) -> None:
        self.http = ThrottledSession()
        self.http.session.headers.update({"Referer": "https://finance.sina.com.cn/"})

    def fetch(self, specs: Iterable[GlobalMarketSpec] = GLOBAL_TECH_SPECS) -> list[dict[str, Any]]:
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
                observed_at = self._parse_datetime(values[3], "Asia/Shanghai")
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
    """Build a session-aware, correlation-deduplicated global technology context."""

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
    ) -> dict[str, Any]:
        current = _as_shanghai(now)
        cached = self._read_cache(allow_stale=True)
        cache_status = dict(cached.get("cache_status") or {})
        cached_observations = list((cached.get("data") or {}).get("observations") or [])
        if cached_observations and not force and not bool(cache_status.get("stale")):
            result = self.analyze(cached_observations, now=current)
            result["cache_status"] = cache_status
            return result
        if not allow_network:
            result = self.analyze(cached_observations, now=current)
            result["cache_status"] = cache_status or {"status": "miss", "stale": True}
            if not cached_observations:
                result["missing_reasons"].append("全球市场缓存缺失；当前调用禁止联网刷新")
            return result
        try:
            observations = list(self.provider.fetch(GLOBAL_TECH_SPECS) or [])
        except Exception as exc:
            result = self.analyze(cached_observations, now=current)
            result["cache_status"] = cache_status or {"status": "error", "stale": True}
            result["source_error"] = str(exc)[:240]
            if not cached_observations:
                result["missing_reasons"].append(f"新浪全球行情请求失败：{str(exc)[:160]}")
            return result
        result = self.analyze(observations, now=current)
        result["cache_status"] = self._write_cache(observations, result)
        return result

    def analyze(self, observations: Iterable[dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
        current = _as_shanghai(now)
        rows = [self._decorate(dict(row), current) for row in observations if isinstance(row, dict)]
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
        direct_count = sum(1 for row in selected if float(row.get("technology_relevance") or 0) >= 0.8)
        live_count = sum(1 for row in selected if row.get("session_phase") in {"实时交易", "期货实时", "盘前实时", "盘后实时"})
        family_count = len(family_rows)
        valid_for_score = family_count >= 2 and direct_count >= 1 and live_count >= 1
        missing_reasons: list[str] = []
        if family_count < 2:
            missing_reasons.append("全球科技情绪至少需要两个去重后的地区/资产族证据")
        if direct_count < 1:
            missing_reasons.append("缺少恒生科技、纳指或纳指期货等直接科技证据")
        if live_count < 1:
            missing_reasons.append("当前只有前收盘或过期数据，不能作为实时交易环境分")
        if not rows:
            missing_reasons.append("全球指数/期货行情源未返回有效数据")
        label = self._label(score) if score is not None else "数据不足"
        return {
            "as_of": current.isoformat(timespec="seconds"),
            "target_market": "A股",
            "score": round(score, 2) if score is not None else None,
            "label": label,
            "quality_status": "available" if valid_for_score and len(selected) >= 3 else "partial" if valid_for_score else "insufficient_evidence",
            "valid_for_score": valid_for_score,
            "evidence_units": len(selected),
            "correlation_family_units": family_count,
            "direct_technology_units": direct_count,
            "live_units": live_count,
            "observations": rows,
            "selected_evidence": selected,
            "excluded_evidence": excluded,
            "missing_reasons": list(dict.fromkeys(missing_reasons)),
            "score_definition": "全球科技情绪分以50为中性，按真实涨跌幅、交易阶段、陈旧度和科技相关度加权；先在指数簇内去重，再对同一地区的相关资产族设置上限。",
            "time_alignment_policy": "A股盘中优先恒生科技、亚洲在市指数和仍在交易的美股期货；美股现金指数仅在常规交易时段作为实时证据，其余时间标记前收盘并降权。",
            "correlation_policy": "纳指100、纳斯达克综合和纳指期货只选一项；费城半导体与美股宽基可补充行业/整体风险，但美国权益资产族合计权重设上限，避免高相关走势重复放大。",
            "truth_boundary": "该分数只描述可见的全球科技风险背景，不预测尚未开盘市场；缺失、过期或单一证据不进入自动交易分。",
        }

    def _decorate(self, row: dict[str, Any], now: datetime) -> dict[str, Any]:
        observed = self._parse_observed(row.get("observed_at"), row.get("timezone") or "Asia/Shanghai")
        age_seconds = max(0.0, (now.astimezone(observed.tzinfo) - observed).total_seconds()) if observed else None
        phase, phase_multiplier, phase_reason = self._phase(row, observed, now, age_seconds)
        change_pct = _number(row.get("change_pct"))
        technology_relevance = _clamp(_number(row.get("technology_relevance")) or 0.0, 0.0, 1.0)
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
        if key in {"nasdaq_100", "nasdaq_composite", "philadelphia_semiconductor", "dow_jones"}:
            session = self.calendar.session("US", now=now)
            us_now = now.astimezone(ZoneInfo("America/New_York"))
            source_date = observed.astimezone(ZoneInfo("America/New_York")).date()
            if session.get("status") == "regular" and source_date == us_now.date() and age_seconds <= 15 * 60:
                return "实时交易", 1.0, "美股常规交易时段实时指数"
            if age_seconds <= 96 * 3600:
                return "前收盘参考", 0.42, f"美股当前{session.get('label') or '未交易'}，现金指数只作前收盘参考"
            return "已过期", 0.0, "美股现金指数超过96小时"
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
