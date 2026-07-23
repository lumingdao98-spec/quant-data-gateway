from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
import json
import re
from typing import Any, Iterable

from quant_data.data.pit_store import PITRecord, PITStore
from quant_data.scoring.extension_factors import V324ExtensionFactorEngine

from .global_industry_mapper import GlobalIndustryMapper


STANDARD_FACTOR_NAMES_CN = {
    "macro_liquidity_stress": "宏观流动性压力",
    "global_semis_drawdown": "全球半导体回撤",
    "ipo_liquidity_shock": "IPO资金分流冲击",
    "earnings_surprise": "业绩超预期幅度",
    "guidance_delta": "业绩指引变化",
    "northbound_flow_regime": "北向资金状态",
    "sector_sentiment_velocity": "板块情绪变化速度",
    "competitor_listing_pressure": "竞品上市压力",
}


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    raw = str(value or "").strip().replace("Z", "+00:00")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


def _stable_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


class MarketEventFactorService:
    """Convert cached, traceable events into bounded market/stock adjustments.

    The service never performs network I/O and never invents an event value. A
    market-wide event can change the market environment score, while an item can
    change a symbol's information score only after an explicit business-chain
    mapping. Stable score policy modules remain untouched.
    """

    def __init__(
        self,
        cache_state: Any | None = None,
        mapper: GlobalIndustryMapper | None = None,
        pit_store: PITStore | None = None,
    ) -> None:
        self.cache_state = cache_state
        self.mapper = mapper or GlobalIndustryMapper()
        self.pit_store = pit_store
        self.extension_engine = V324ExtensionFactorEngine()

    def build_context(
        self,
        *,
        symbol: str,
        name: str = "",
        profile: dict[str, Any] | None = None,
        global_items: Iterable[dict[str, Any]] | None = None,
        sector_snapshot: dict[str, Any] | None = None,
        structured_inputs: dict[str, dict[str, Any]] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = (now or datetime.now()).replace(tzinfo=None)
        profile = dict(profile or {})
        items, cache_status = self._items(global_items)
        exposure = self.mapper.company_exposure(symbol, profile=profile, name=name)
        factors: dict[str, dict[str, Any]] = {}
        excluded = 0
        future_excluded = 0
        undated_excluded = 0

        for raw in items:
            item = dict(raw or {})
            published = _parse_time(
                item.get("available_at")
                or item.get("published_at")
                or item.get("published_at_norm")
                or item.get("publish_time")
                or item.get("date_display")
            )
            if published is None:
                undated_excluded += 1
                continue
            if published > current + timedelta(minutes=2):
                future_excluded += 1
                continue
            text = " ".join(str(item.get(key) or "") for key in ("title", "summary", "content", "category"))
            max_age_days = 21 if self._is_ipo(text) else 5
            if current - published > timedelta(days=max_age_days):
                excluded += 1
                continue
            mapped = self.mapper.map_item(item, symbol, exposure)
            source = str(item.get("source") or item.get("source_name") or "来源未标明")
            source_ref = str(item.get("source_ref") or item.get("source_url") or item.get("url") or "")

            tech_factor = self._global_technology_factor(text, mapped, published, source, source_ref)
            self._keep_strongest(factors, tech_factor)
            liquidity_factor = self._global_liquidity_factor(text, mapped, published, source, source_ref)
            self._keep_strongest(factors, liquidity_factor)
            for factor in self._ipo_factors(text, item, mapped, published, source, source_ref):
                self._keep_strongest(factors, factor)

            if mapped.get("included_in_score") and not self._is_ipo(text):
                factor = self._mapped_industry_factor(text, mapped, published, source, source_ref)
                self._keep_strongest(factors, factor)

        resolved_sector = sector_snapshot if sector_snapshot is not None else self._cached_sector_snapshot()
        sector_factor = self._sector_factor(exposure, resolved_sector)
        self._keep_strongest(factors, sector_factor)
        pit_inputs, pit_input_status = self._pit_structured_inputs(
            symbol=symbol,
            current=current,
            exposure=exposure,
        )
        supplied_inputs = {
            key: dict(value)
            for key, value in dict(structured_inputs or {}).items()
            if isinstance(value, dict) and value
        }
        merged_inputs = {**pit_inputs, **supplied_inputs}
        merged_inputs["sector"] = dict(supplied_inputs.get("sector") or pit_inputs.get("sector") or resolved_sector)
        extension_rows, extension_missing = self._structured_factor_rows(
            symbol=symbol,
            current=current,
            structured_inputs=merged_inputs,
        )
        for factor in extension_rows:
            self._keep_strongest(factors, factor)
        rows = sorted(factors.values(), key=lambda row: (row.get("scope") != "市场环境", -abs(float(row.get("adjustment") or 0))))
        market_adjustment = _clamp(sum(float(row["adjustment"]) for row in rows if row.get("scope") == "市场环境"), -18.0, 12.0)
        information_adjustment = _clamp(sum(float(row["adjustment"]) for row in rows if row.get("scope") == "个股信息"), -10.0, 10.0)
        negative_veto = any(bool(row.get("veto")) for row in rows)
        missing: list[str] = []
        if not items:
            missing.append("全球事件缓存缺失")
        if not rows:
            missing.append("近期没有可映射且可追溯的市场事件")
        if any(row.get("factor_key") == "ipo_liquidity_watch" and row.get("adjustment") == 0 for row in rows):
            missing.append("IPO发行规模缺失，未量化资金分流")
        standard_coverage = self._standard_coverage(rows, extension_missing)
        return {
            "symbol": symbol,
            "name": name or profile.get("name") or symbol,
            "as_of": current.isoformat(timespec="seconds"),
            "market_adjustment": round(market_adjustment, 2),
            "information_adjustment": round(information_adjustment, 2),
            "negative_veto": negative_veto,
            "factors": rows,
            "factor_count": len(rows),
            "evidence": [str(row.get("explanation") or "") for row in rows if row.get("explanation")],
            "data_sources": list(dict.fromkeys(str(row.get("source") or "") for row in rows if row.get("source"))),
            "missing_data": missing,
            "standard_factor_coverage": standard_coverage,
            "standard_factor_available": sum(1 for row in standard_coverage if row["status"] == "available"),
            "standard_factor_total": len(STANDARD_FACTOR_NAMES_CN),
            "excluded_expired": excluded,
            "excluded_future": future_excluded,
            "excluded_undated": undated_excluded,
            "cache_status": cache_status,
            "pit_input_status": pit_input_status,
            "company_exposure": exposure,
            "truth_boundary": "事件调整是有来源证据的模型解释，不等于事实收益或自动交易指令。",
        }

    def apply_scores(
        self,
        context: dict[str, Any],
        *,
        market_score: float | None,
        information_score: float | None,
    ) -> dict[str, Any]:
        market_adjustment = float(context.get("market_adjustment") or 0.0)
        information_adjustment = float(context.get("information_adjustment") or 0.0)
        return {
            "market_score": round(_clamp(market_score + market_adjustment, 0, 100), 2) if market_score is not None else None,
            "information_score": round(_clamp(information_score + information_adjustment, 0, 100), 2) if information_score is not None else None,
            "market_adjustment": round(market_adjustment, 2),
            "information_adjustment": round(information_adjustment, 2),
        }

    def _items(self, items: Iterable[dict[str, Any]] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if items is not None:
            return [dict(item) for item in items if isinstance(item, dict)], {"status": "provided", "stale": False}
        if self.cache_state is None:
            return [], {"status": "miss", "stale": True}
        try:
            cached = self.cache_state.get("global_news_cache", "stream:latest", allow_stale=True)
            if not cached.data:
                cached = self.cache_state.latest("global_news_cache", allow_stale=True)
            return [dict(item) for item in (cached.data or {}).get("items", []) if isinstance(item, dict)], dict(cached.cache_status or {})
        except Exception as exc:
            return [], {"status": "error", "stale": True, "error": str(exc)[:180]}

    def _cached_sector_snapshot(self) -> dict[str, Any]:
        if self.cache_state is None:
            return {}
        for kind in ("sector_mainline_cache", "sector_mainline_intraday", "sector_mainline_daily"):
            try:
                cached = self.cache_state.latest(kind, allow_stale=True)
            except Exception:
                continue
            if cached.data and cached.data.get("items"):
                return dict(cached.data)
        return {}

    def _pit_structured_inputs(
        self,
        *,
        symbol: str,
        current: datetime,
        exposure: dict[str, Any],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """Load canonical structured factors as-of the decision time.

        Text news remains useful for explaining transmission chains, while PIT
        records are the only automatic source for numeric earnings, IPO, macro
        and northbound-flow factors. This keeps historical replay and realtime
        decisions on the same no-look-ahead contract.
        """

        status: dict[str, Any] = {
            "enabled": self.pit_store is not None,
            "decision_time": current.isoformat(timespec="seconds"),
            "datasets": {},
            "rule": "仅使用 available_at 不晚于决策时点且带可追溯来源的快照。",
        }
        if self.pit_store is None:
            status["message"] = "PIT 存储未接入；结构化事件因子保持缺失。"
            return {}, status

        output: dict[str, dict[str, Any]] = {}
        specs = {
            "earnings": {"symbol": symbol, "max_age_days": 550, "limit": 12},
            "macro": {"symbol": "", "max_age_days": 7, "limit": 80},
            "fund_flow": {"symbol": symbol, "max_age_days": 5, "limit": 40},
            "sector": {"symbol": symbol, "max_age_days": 5, "limit": 40},
        }
        for section, spec in specs.items():
            records = self._query_pit_records(
                dataset=section,
                symbol=str(spec["symbol"]),
                current=current,
                limit=int(spec["limit"]),
            )
            selected, section_status = self._select_pit_input(
                records,
                section=section,
                current=current,
                max_age_days=int(spec["max_age_days"]),
            )
            status["datasets"][section] = section_status
            if selected:
                output[section] = selected

        ipo_records = self._query_pit_records(
            dataset="ipo",
            symbol="",
            current=current,
            limit=120,
        )
        ipo_selected, ipo_status = self._select_ipo_input(
            ipo_records,
            symbol=symbol,
            exposure=exposure,
            current=current,
        )
        status["datasets"]["ipo"] = ipo_status
        if ipo_selected:
            output["ipo"] = ipo_selected

        status["available_sections"] = sorted(output)
        status["missing_sections"] = sorted(set(("earnings", "macro", "fund_flow", "sector", "ipo")) - set(output))
        return output, status

    def _query_pit_records(
        self,
        *,
        dataset: str,
        symbol: str,
        current: datetime,
        limit: int,
    ) -> list[PITRecord]:
        if self.pit_store is None:
            return []
        try:
            return list(
                self.pit_store.query_asof(
                    decision_time=current.isoformat(timespec="seconds"),
                    dataset=dataset,
                    symbol=symbol,
                    limit=limit,
                )
            )
        except Exception:
            return []

    def _select_pit_input(
        self,
        records: list[PITRecord],
        *,
        section: str,
        current: datetime,
        max_age_days: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not records:
            return {}, {"status": "missing", "reason": f"没有 {section} PIT 快照"}
        rejected = 0
        for record in records:
            available_at = _parse_time(record.available_at)
            if available_at is None or available_at > current + timedelta(minutes=2):
                rejected += 1
                continue
            age_days = max(0.0, (current - available_at).total_seconds() / 86400.0)
            if age_days > max_age_days:
                rejected += 1
                continue
            data = self._pit_record_payload(record)
            if not self._has_traceable_source(data):
                rejected += 1
                continue
            return data, {
                "status": "available",
                "record_id": record.record_id,
                "available_at": record.available_at,
                "source": data.get("source"),
                "source_ref": data.get("source_ref"),
                "age_days": round(age_days, 3),
                "rejected": rejected,
            }
        return {}, {
            "status": "excluded",
            "reason": "快照过期、晚于决策时点或缺少可追溯来源",
            "rejected": rejected,
        }

    def _select_ipo_input(
        self,
        records: list[PITRecord],
        *,
        symbol: str,
        exposure: dict[str, Any],
        current: datetime,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not records:
            return {}, {"status": "missing", "reason": "没有 IPO PIT 快照"}
        exposure_words = set(
            str(value).strip()
            for value in (
                list(exposure.get("industries") or [])
                + list(exposure.get("concepts") or [])
                + list(exposure.get("chain_position") or [])
            )
            if str(value).strip()
        )
        candidates: list[tuple[float, float, PITRecord, dict[str, Any]]] = []
        rejected = 0
        for record in records:
            available_at = _parse_time(record.available_at)
            if available_at is None or available_at > current + timedelta(minutes=2):
                rejected += 1
                continue
            age_days = max(0.0, (current - available_at).total_seconds() / 86400.0)
            if age_days > 180:
                rejected += 1
                continue
            data = self._pit_record_payload(record)
            if not self._has_traceable_source(data):
                rejected += 1
                continue
            competitors = {
                str(value).strip()
                for value in (data.get("competitor_symbols") or data.get("competitors") or [])
                if str(value).strip()
            }
            sectors = {
                str(value).strip()
                for value in (data.get("sectors") or ([data.get("sector")] if data.get("sector") else []))
                if str(value).strip()
            }
            issuer = str(data.get("issuer_symbol") or data.get("symbol") or "").strip()
            symbol_related = symbol in competitors or symbol == issuer or bool(exposure_words.intersection(sectors))
            data["competitor_symbols"] = sorted(competitors)
            data["symbol_relevance"] = "direct" if symbol_related else "market_only"
            shock = abs(
                _number(
                    data.get("liquidity_shock_score")
                    or data.get("ipo_shock_score")
                    or data.get("fund_diversion_score")
                )
                or 0.0
            )
            candidates.append((1.0 if symbol_related else 0.0, shock, record, data))
        if not candidates:
            return {}, {
                "status": "excluded",
                "reason": "IPO 快照过期、晚于决策时点或缺少可追溯来源",
                "rejected": rejected,
            }
        _, _, record, selected = max(
            candidates,
            key=lambda row: (row[0], row[1], str(row[2].available_at)),
        )
        available_at = _parse_time(record.available_at) or current
        return selected, {
            "status": "available",
            "record_id": record.record_id,
            "available_at": record.available_at,
            "source": selected.get("source"),
            "source_ref": selected.get("source_ref"),
            "symbol_relevance": selected.get("symbol_relevance"),
            "age_days": round(max(0.0, (current - available_at).total_seconds() / 86400.0), 3),
            "rejected": rejected,
        }

    @staticmethod
    def _pit_record_payload(record: PITRecord) -> dict[str, Any]:
        outer = dict(record.payload or {})
        nested = dict(outer.get("payload") or {}) if isinstance(outer.get("payload"), dict) else {}
        data = {**outer, **nested}
        data["available_at"] = str(record.available_at or data.get("available_at") or "")
        data["source"] = str(
            outer.get("source_name")
            or nested.get("source_name")
            or outer.get("source_id")
            or nested.get("source_id")
            or record.source_id
            or ""
        )
        data["source_ref"] = str(
            outer.get("source_ref")
            or outer.get("source_url")
            or nested.get("source_ref")
            or nested.get("source_url")
            or ""
        )
        data["pit_record_id"] = record.record_id
        if "competitor_symbols" not in data and isinstance(data.get("competitors"), list):
            data["competitor_symbols"] = list(data["competitors"])
        return data

    @staticmethod
    def _has_traceable_source(data: dict[str, Any]) -> bool:
        return bool(str(data.get("source") or "").strip() and str(data.get("source_ref") or "").strip())

    def _global_technology_factor(self, text: str, mapped: dict[str, Any], published: datetime, source: str, source_ref: str) -> dict[str, Any] | None:
        technology = any(word.lower() in text.lower() for word in ("纳斯达克", "科技股", "芯片股", "半导体", "AI交易", "人工智能"))
        semiconductors = any(word.lower() in text.lower() for word in ("芯片股", "半导体", "费城半导体", "SOX"))
        risk = any(word in text for word in ("抛售", "下跌", "重挫", "暴跌", "回调", "承压", "泡沫", "去杠杆", "估值过高"))
        if not (technology and risk):
            return None
        key = "global_semis_drawdown" if semiconductors else "global_technology_risk"
        raw_value = self._parse_signed_percent(text) if semiconductors else None
        return self._factor(
            key,
            "市场环境",
            -7.0,
            "海外半导体板块回撤经风险偏好和成长估值链路压低大盘环境分。" if semiconductors else "海外科技风险偏好走弱，经成长估值和情绪链路压低大盘环境分。",
            published,
            source,
            source_ref,
            mapped,
            raw_value=raw_value,
        )

    def _global_liquidity_factor(self, text: str, mapped: dict[str, Any], published: datetime, source: str, source_ref: str) -> dict[str, Any] | None:
        trigger = any(word in text for word in ("非农", "CPI", "PCE", "美联储", "美债收益率", "加息", "降息"))
        tightening = any(word in text for word in ("超预期", "上升", "走高", "鹰派", "加息", "推迟降息", "降息预期下降"))
        easing = any(word in text for word in ("低于预期", "回落", "鸽派", "降息", "降息预期上升"))
        if not trigger or not (tightening or easing):
            return None
        adjustment = -4.5 if tightening and not easing else 3.0 if easing and not tightening else 0.0
        return self._factor(
            "macro_liquidity_stress",
            "市场环境",
            adjustment,
            "海外利率/流动性证据经估值折现和汇率风险传导至A股市场环境。",
            published,
            source,
            source_ref,
            mapped,
        )

    def _structured_factor_rows(
        self,
        *,
        symbol: str,
        current: datetime,
        structured_inputs: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        valid: dict[str, dict[str, Any]] = {}
        missing: dict[str, str] = {}
        factor_sections = {
            "macro_liquidity_stress": "macro",
            "global_semis_drawdown": "sector",
            "ipo_liquidity_shock": "ipo",
            "earnings_surprise": "earnings",
            "guidance_delta": "earnings",
            "northbound_flow_regime": "fund_flow",
            "sector_sentiment_velocity": "sector",
            "competitor_listing_pressure": "ipo",
        }
        for section in set(factor_sections.values()):
            data = dict(structured_inputs.get(section) or {})
            if not data:
                continue
            available_at = _parse_time(data.get("available_at") or data.get("updated_at") or data.get("fetched_at"))
            source = str(data.get("source") or data.get("source_name") or "").strip()
            source_ref = str(data.get("source_ref") or data.get("source_url") or data.get("url") or "").strip()
            if available_at is None:
                for key, owner in factor_sections.items():
                    if owner == section:
                        missing[key] = "快照缺少 available_at，未进入评分"
                continue
            if available_at > current + timedelta(minutes=2):
                for key, owner in factor_sections.items():
                    if owner == section:
                        missing[key] = "快照在决策时点之后才可用，已按 PIT 规则排除"
                continue
            if not source or not source_ref:
                for key, owner in factor_sections.items():
                    if owner == section:
                        missing[key] = "快照缺少可追溯来源，未进入评分"
                continue
            valid[section] = data

        computed = self.extension_engine.compute(
            macro=valid.get("macro"),
            sector=valid.get("sector"),
            earnings=valid.get("earnings"),
            ipo=valid.get("ipo"),
            fund_flow=valid.get("fund_flow"),
        )
        rows: list[dict[str, Any]] = []
        for key, raw_value in computed.values.items():
            section = factor_sections[key]
            data = valid[section]
            if key == "competitor_listing_pressure":
                competitors = {str(value).strip() for value in data.get("competitor_symbols", []) if str(value).strip()}
                if not competitors or symbol not in competitors:
                    missing[key] = "未提供包含当前标的的 competitor_symbols，未计竞品上市压力"
                    continue
            adjustment, scope = self._extension_adjustment(key, raw_value)
            available_at = _parse_time(data.get("available_at") or data.get("updated_at") or data.get("fetched_at")) or current
            rows.append(
                self._factor(
                    key,
                    scope,
                    adjustment,
                    f"{STANDARD_FACTOR_NAMES_CN[key]}来自带时点与来源的结构化快照；原始值 {raw_value:.4f}，按有限权重进入事件调整。",
                    available_at,
                    str(data.get("source") or data.get("source_name")),
                    str(data.get("source_ref") or data.get("source_url") or data.get("url")),
                    {"relevance_score": data.get("confidence", 75) if _number(data.get("confidence")) is not None else 75},
                    raw_value=raw_value,
                )
            )
        for key in STANDARD_FACTOR_NAMES_CN:
            if key not in computed.values and key not in missing:
                missing[key] = "当前快照没有该字段，保持缺失而不是按 0 分处理"
        return rows, missing

    @staticmethod
    def _extension_adjustment(key: str, raw_value: float) -> tuple[float, str]:
        value = float(raw_value)
        if key == "macro_liquidity_stress":
            return -_clamp(abs(value) * 0.08, 0.0, 8.0), "市场环境"
        if key == "global_semis_drawdown":
            return -_clamp(abs(value) * 0.5, 0.0, 8.0), "市场环境"
        if key == "ipo_liquidity_shock":
            return -_clamp(abs(value) * 0.08, 0.0, 8.0), "市场环境"
        if key == "earnings_surprise":
            return _clamp(value * 0.12, -8.0, 8.0), "个股信息"
        if key == "guidance_delta":
            return _clamp(value * 0.10, -6.0, 6.0), "个股信息"
        if key == "northbound_flow_regime":
            return _clamp(value * 0.06, -6.0, 6.0), "市场环境"
        if key == "sector_sentiment_velocity":
            return _clamp(value * 0.08, -5.0, 5.0), "个股信息"
        return -_clamp(abs(value) * 0.05, 0.0, 5.0), "个股信息"

    @staticmethod
    def _standard_coverage(rows: list[dict[str, Any]], missing: dict[str, str]) -> list[dict[str, str]]:
        available = {str(row.get("factor_key") or "") for row in rows}
        return [
            {
                "factor_key": key,
                "factor_name_cn": name,
                "status": "available" if key in available else "missing",
                "missing_reason": "" if key in available else missing.get(key, "近期没有可追溯证据"),
            }
            for key, name in STANDARD_FACTOR_NAMES_CN.items()
        ]

    def _ipo_factors(self, text: str, item: dict[str, Any], mapped: dict[str, Any], published: datetime, source: str, source_ref: str) -> list[dict[str, Any]]:
        if not self._is_ipo(text):
            return []
        is_changxin = any(word in text for word in ("长鑫科技", "长鑫存储"))
        if not is_changxin:
            return []
        amount = _number(item.get("issue_amount") or item.get("issue_size"))
        if amount is None:
            amount = self._parse_issue_amount(text)
        adjustment = 0.0
        if amount is not None:
            amount_yi = amount / 100_000_000
            adjustment = -8.0 if amount_yi >= 500 else -6.0 if amount_yi >= 200 else -4.0 if amount_yi >= 50 else -2.0
        amount_text = f"；已识别发行/募资规模约 {amount / 100_000_000:.2f} 亿元" if amount is not None else "；发行规模未从证据中识别，未量化扣分"
        rows = [
            self._factor(
                "ipo_liquidity_shock" if amount is not None else "ipo_liquidity_watch",
                "市场环境",
                adjustment,
                "长鑫科技IPO在申购、缴款和上市窗口可能形成资金占用" + amount_text + "。",
                published,
                source,
                source_ref,
                mapped,
                raw_value=amount,
            )
        ]
        if mapped.get("included_in_score") and "dram_memory_chain" in (mapped.get("matched_rule_keys") or []):
            rows.append(
                self._factor(
                    "dram_supply_chain_catalyst",
                    "个股信息",
                    4.0,
                    "长鑫科技IPO同时是国产DRAM产业事件；当前标的主营/产业链暴露已核验重合，因此仅小幅计入个股信息分。",
                    published,
                    source,
                    source_ref,
                    mapped,
                )
            )
        return rows

    def _mapped_industry_factor(self, text: str, mapped: dict[str, Any], published: datetime, source: str, source_ref: str) -> dict[str, Any] | None:
        positive = any(word in text for word in ("增长", "支持", "中标", "回暖", "增持", "上调", "超预期"))
        negative = any(word in text for word in ("下滑", "亏损", "处罚", "立案", "制裁", "下调", "低于预期"))
        if not (positive or negative):
            return None
        adjustment = 3.0 if positive and not negative else -4.0 if negative and not positive else 0.0
        veto = negative and any(word in text for word in ("退市", "立案调查", "重大违法", "债务违约"))
        return self._factor(
            "mapped_industry_information",
            "个股信息",
            adjustment,
            "近期信息与公司主营/产业链有直接结构化重合，按有限权重进入个股信息分。",
            published,
            source,
            source_ref,
            mapped,
            veto=veto,
        )

    def _sector_factor(self, exposure: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any] | None:
        rows = [dict(row) for row in snapshot.get("items", []) if isinstance(row, dict)]
        if not rows:
            return None
        exposure_words = set(exposure.get("industries", []) + exposure.get("concepts", []) + exposure.get("chain_position", []))
        matched = [row for row in rows if str(row.get("board_name") or "") in exposure_words]
        if not matched:
            return None
        best = max(matched, key=lambda row: float(_number(row.get("mainline_score")) or 0.0))
        strength = _number(best.get("mainline_score") or best.get("strength_score"))
        if strength is None:
            return None
        adjustment = _clamp((strength - 50.0) * 0.08, -4.0, 4.0)
        source = str(best.get("source_name") or snapshot.get("source_name") or "板块资金快照")
        source_ref = str(best.get("source_url") or snapshot.get("source_url") or "")
        published = _parse_time(snapshot.get("updated_at") or snapshot.get("created_at")) or datetime.now()
        return self._factor(
            "sector_mainline_strength",
            "个股信息",
            adjustment,
            f"标的产业暴露与板块“{best.get('board_name')}”重合，主线强度 {strength:.2f}，按有限权重调整信息环境。",
            published,
            source,
            source_ref,
            {"mapped_chain": [best.get("board_name")], "relevance_score": strength},
            raw_value=strength,
        )

    def _factor(
        self,
        key: str,
        scope: str,
        adjustment: float,
        explanation: str,
        published: datetime,
        source: str,
        source_ref: str,
        mapped: dict[str, Any],
        *,
        raw_value: float | None = None,
        veto: bool = False,
    ) -> dict[str, Any]:
        return {
            "factor_id": _stable_id(key, source_ref, published.isoformat(), explanation),
            "factor_key": key,
            "factor_name_cn": {
                "global_technology_risk": "全球科技风险",
                "global_semis_drawdown": "全球半导体回撤",
                "macro_liquidity_stress": "宏观流动性压力",
                "ipo_liquidity_shock": "IPO资金分流",
                "ipo_liquidity_watch": "IPO资金分流观察",
                "dram_supply_chain_catalyst": "国产DRAM产业催化",
                "mapped_industry_information": "产业链近期信息",
                "sector_mainline_strength": "板块主线强度",
            }.get(key, key),
            "scope": scope,
            "adjustment": round(float(adjustment), 2),
            "raw_value": raw_value,
            "confidence": round(_clamp(float(mapped.get("relevance_score") or 70.0) / 100.0, 0.35, 0.92), 2),
            "published_at": published.isoformat(timespec="seconds"),
            "available_at": published.isoformat(timespec="seconds"),
            "source": source,
            "source_ref": source_ref,
            "quality_status": "可追溯" if source_ref else "来源链接缺失",
            "mapped_chain": list(mapped.get("mapped_chain") or mapped.get("transmission_chain") or []),
            "explanation": explanation,
            "veto": bool(veto),
        }

    @staticmethod
    def _keep_strongest(target: dict[str, dict[str, Any]], factor: dict[str, Any] | None) -> None:
        if not factor:
            return
        key = str(factor.get("factor_key") or "")
        current = target.get(key)
        if current is None or abs(float(factor.get("adjustment") or 0)) > abs(float(current.get("adjustment") or 0)):
            target[key] = factor

    @staticmethod
    def _is_ipo(text: str) -> bool:
        return any(word in text for word in ("IPO", "首次公开发行", "发行上市", "申购", "募集资金", "募资", "战略配售"))

    @staticmethod
    def _parse_issue_amount(text: str) -> float | None:
        match = re.search(
            r"(?:募资|募集资金|发行规模|发行金额|融资)(?:总额|规模|金额)?(?:约|预计|为|达|不超过|将)?\s*([0-9]+(?:\.[0-9]+)?)\s*(万亿|亿元|亿|万元|万|元)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2)
        multiplier = {"万亿": 1_000_000_000_000, "亿元": 100_000_000, "亿": 100_000_000, "万元": 10_000, "万": 10_000, "元": 1}.get(unit, 1)
        return value * multiplier

    @staticmethod
    def _parse_signed_percent(text: str) -> float | None:
        match = re.search(r"(?:下跌|回撤|重挫|暴跌|跌幅|跌逾|跌超)\s*([0-9]+(?:\.[0-9]+)?)\s*%", text, flags=re.IGNORECASE)
        return -float(match.group(1)) if match else None
