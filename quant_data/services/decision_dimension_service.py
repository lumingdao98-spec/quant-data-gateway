from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from quant_data.scoring.execution_policy import EXECUTION_SCORE_THRESHOLDS, EXECUTION_SCORE_WEIGHTS


@dataclass(frozen=True, slots=True)
class DimensionRule:
    key: str
    label: str
    role: str


DIMENSION_RULES = (
    DimensionRule("fundamental", "基本面", "验证经营质量、估值和财务风险；短线可选，长线必须有可追溯财务快照"),
    DimensionRule("technical", "技术面", "决定趋势、位置和盘中择时，不单独证明公司价值"),
    DimensionRule("information", "信息面", "识别公告、事件和预期差，重大负面可否决买入"),
    DimensionRule("fund_flow", "资金面", "验证量价承接和公开资金流，不把成交量代理冒充主力账户"),
)


class DecisionDimensionService:
    """Explain and gate score dimensions without inventing data.

    This service is deliberately policy-only. It does not fetch data and does
    not calculate another competing trade score. The execution score remains
    the one emitted by ``SignalFusionEngine``; this layer records whether the
    inputs are suitable for backtest, paper entry, live entry, or reminders.
    """

    _SHORT_FAMILIES = {"intraday_paper", "short_term", "event_driven", "score_reversal"}
    _LONG_FAMILIES = {"long_term", "long_term_compounder", "core_satellite", "dividend_low_vol"}
    _ETF_FAMILIES = {"etf_index", "etf_momentum_rotation", "dca", "dca_schedule"}
    _UNUSABLE_QUALITY = {
        "missing",
        "unavailable",
        "unsupported",
        "unusable",
        "rejected",
        "invalid",
        "error",
        "insufficient_sample",
    }

    def evaluate(
        self,
        *,
        mode: str,
        strategy_family: str,
        scores: dict[str, Any] | None = None,
        sources: dict[str, Any] | None = None,
        freshness: dict[str, Any] | None = None,
        recent_information: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scores = dict(scores or {})
        sources = dict(sources or {})
        freshness = dict(freshness or {})
        recent_information = dict(recent_information or {})
        provenance = dict(provenance or {})
        family = str(strategy_family or "hybrid").strip().lower()
        normalized_mode = self._mode(mode)
        required = self._required_dimensions(family, normalized_mode)
        stale_fields = {str(x) for x in (freshness.get("stale_fields") or [])}
        missing_fields = {str(x) for x in (freshness.get("missing_fields") or [])}

        rows: list[dict[str, Any]] = []
        block_reasons: list[str] = []
        warnings: list[str] = []
        for rule in DIMENSION_RULES:
            score = self._number(scores.get(rule.key) if rule.key in scores else scores.get(f"{rule.key}_score"))
            source = self._source_for(rule.key, sources)
            source_missing = [
                str(item)
                for item in (source.get("missing_reasons") or [])
                if str(item or "").strip()
            ]
            available = score is not None
            stale = self._is_stale(rule.key, stale_fields, recent_information, source)
            quality = self._quality(rule.key, source, recent_information)
            pit_usable = self._pit_usable(rule.key, source, provenance)
            is_required = rule.key in required
            truth_boundary = self._truth_boundary(rule.key, source)
            use = self._usage(rule.key, normalized_mode, pit_usable, quality)
            reason = ""
            if not available:
                reason = "；".join(source_missing[:3]) or "分数或有效输入缺失"
            elif stale:
                reason = "；".join(source_missing[:3]) or "数据已过期"
            elif normalized_mode == "backtest" and not pit_usable:
                reason = "没有决策时点可用的 PIT 证据，回测排除"
            elif quality in self._UNUSABLE_QUALITY:
                reason = "；".join(source_missing[:3]) or "证据质量不足"

            ready = available and not stale and quality not in self._UNUSABLE_QUALITY
            if normalized_mode == "backtest":
                ready = ready and pit_usable
            if is_required and not ready:
                block_reasons.append(f"{rule.label}未就绪：{reason or '缺少可核验证据'}")
            elif not ready:
                warnings.append(f"{rule.label}未参与：{reason or '缺少可核验证据'}")
            rows.append(
                {
                    "key": rule.key,
                    "label": rule.label,
                    "score": round(score, 4) if score is not None else None,
                    "required": is_required,
                    "ready": ready,
                    "stale": stale,
                    "quality_status": quality,
                    "source": source.get("source") or source.get("source_name") or source.get("source_id") or "数据源缺失",
                    "source_ref": source.get("source_ref") or source.get("snapshot_id") or source.get("source_url") or "",
                    "pit_usable": pit_usable,
                    "role": rule.role,
                    "usage": use,
                    "truth_boundary": truth_boundary,
                    "reason": reason,
                    "missing_reasons": source_missing,
                    "configured_weight": EXECUTION_SCORE_WEIGHTS[rule.key],
                }
            )

        market_score = self._number(scores.get("market") if "market" in scores else scores.get("market_score"))
        market_source = self._source_for("market", sources)
        market_quality = self._quality("market", market_source, recent_information)
        market_stale = self._is_stale("market", stale_fields, recent_information, market_source)
        market_ready = market_score is not None and not market_stale and market_quality not in self._UNUSABLE_QUALITY
        market_missing = [
            str(item)
            for item in (market_source.get("missing_reasons") or [])
            if str(item or "").strip()
        ]
        market_context = {
            "label": "大盘情绪",
            "score": round(market_score, 4) if market_score is not None else None,
            "ready": market_ready,
            "stale": market_stale,
            "quality_status": market_quality,
            "source": market_source.get("source") or market_source.get("source_name") or "数据源缺失",
            "role": "用于市场环境调分和弱势降仓，不替代个股三面，也不能单独触发买入。",
            "usage": "参与有效权重并调节目标仓位" if market_ready else "未参与本轮评分",
            "reason": "" if market_ready else ("；".join(market_missing[:3]) or "指数趋势或有效市场宽度样本不足/过期"),
            "missing_reasons": market_missing,
            "configured_weight": EXECUTION_SCORE_WEIGHTS["market"],
        }
        if not market_ready:
            warnings.append("大盘情绪未参与：指数趋势或有效市场宽度证据不足")

        provenance_ok = self._provenance_ok(normalized_mode, provenance)
        if normalized_mode == "live" and not provenance_ok:
            block_reasons.append("缺少同标的、实时模式、未过期的评分溯源")
        if freshness.get("action") == "block":
            block_reasons.append("关键行情或分时数据过期")
        block_reasons = list(dict.fromkeys(block_reasons))
        warnings = list(dict.fromkeys(warnings))
        entry_eligible = not block_reasons
        return {
            "mode": normalized_mode,
            "strategy_family": family,
            "dimensions": rows,
            "market_context": market_context,
            "required_dimensions": sorted(required),
            "auto_entry_eligible": entry_eligible,
            "entry_block_reasons": block_reasons,
            "warnings": warnings,
            "alert_eligible": any(row["ready"] for row in rows),
            "reminder_policy": "提醒可展示观察或阻断原因，但只有自动入场门禁通过时才可生成待人工委托票据。",
            "backtest_policy": "只使用 decision_time 当时可得的 PIT 数据；缺少历史信息/资金快照时排除该维度，不用当前数据回填。",
            "paper_policy": "实时模拟使用最新缓存；策略必需的基本面、技术面、信息面或资金面缺失/过期时禁止自动新增仓位。",
            "live_policy": "真实交易复用实时决策分，并额外要求持久化评分溯源、实时行情、风控、确认队列和券商门禁。",
            "execution_score_policy": "SignalFusionEngine 的 final_score 是唯一执行分；policy_score 仅作审计对照，不直接下单。",
            "provenance_ready": provenance_ok,
            "freshness_action": freshness.get("action") or "unknown",
        }

    def framework(self) -> dict[str, Any]:
        return {
            "dimensions": [
                {
                    "key": row.key,
                    "label": row.label,
                    "role": row.role,
                    "configured_weight": EXECUTION_SCORE_WEIGHTS[row.key],
                }
                for row in DIMENSION_RULES
            ],
            "execution_weights": {
                "fundamental": {"label": "基本面", "weight": EXECUTION_SCORE_WEIGHTS["fundamental"]},
                "technical": {"label": "技术面/实时择时", "weight": EXECUTION_SCORE_WEIGHTS["technical"]},
                "information": {"label": "近期信息", "weight": EXECUTION_SCORE_WEIGHTS["information"]},
                "fund_flow": {"label": "量价资金", "weight": EXECUTION_SCORE_WEIGHTS["fund_flow"]},
                "market": {"label": "大盘情绪", "weight": EXECUTION_SCORE_WEIGHTS["market"]},
            },
            "execution_thresholds": {
                **EXECUTION_SCORE_THRESHOLDS,
            },
            "missing_policy": "缺失、过期、质量不足或超出0到100的分项不参与执行分；剩余有效权重重新归一化。必需维度缺失仍阻断自动新增仓位。",
            "screening_policy": "筛选总分仅作审计与候选排序，不得把实时观察强行提升为买入，也不得抬高实时仓位。",
            "mode_flow": {
                "backtest": "PIT数据 -> 因子/评分 -> 历史风控 -> 模拟撮合 -> 订单成交与归因",
                "realtime_paper": "最新真实缓存 -> 三面就绪门禁 -> 执行分 -> 风控 -> 模拟订单/成交",
                "live": "最新真实缓存 -> 三面就绪门禁 -> 执行分 -> 实盘风控 -> 人工确认 -> BrokerAdapter",
                "reminder": "同一决策快照与风控结果 -> 人工委托提醒；不声称已委托或成交",
            },
            "truth_boundaries": {
                "fundamental": "只使用有来源和披露/可用时间的财务快照；历史回测禁止拿当前财务回填过去。",
                "technical": "由真实K线/分时计算；指标是历史价格变换，不保证未来收益。",
                "information": "只用可追溯公告/新闻正文或结构化摘要；规则推算的未来事件只提醒，不计方向分。",
                "fund_flow": "优先公开资金流；没有逐笔/Level-2时只标为量价代理，不能解释为主力账户净买入。",
            },
        }

    def _required_dimensions(self, family: str, mode: str) -> set[str]:
        if mode == "backtest":
            return {"technical"}
        if family in self._LONG_FAMILIES:
            return {"fundamental", "technical", "information"}
        if family in self._ETF_FAMILIES:
            return {"technical", "fund_flow"}
        if family in self._SHORT_FAMILIES:
            return {"technical", "information", "fund_flow"}
        return {"technical", "information", "fund_flow"}

    @staticmethod
    def _mode(value: str) -> str:
        raw = str(value or "realtime_paper").lower()
        return "realtime_paper" if raw in {"paper", "realtime", "realtime-paper"} else raw

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value in (None, "", "--"):
                return None
            out = float(value)
            return out if isfinite(out) and 0.0 <= out <= 100.0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _source_for(key: str, sources: dict[str, Any]) -> dict[str, Any]:
        aliases = {
            "fundamental": ("fundamental", "fundamentals", "financial"),
            "technical": ("technical", "daily_k", "intraday"),
            "information": ("information", "news"),
            "fund_flow": ("fund_flow", "capital", "money"),
            "market": ("market", "market_regime", "market_score"),
        }
        for alias in aliases[key]:
            value = sources.get(alias)
            if isinstance(value, dict):
                return dict(value)
            if value not in (None, ""):
                return {"source": str(value)}
        return {}

    @staticmethod
    def _is_stale(key: str, stale_fields: set[str], info: dict[str, Any], source: dict[str, Any]) -> bool:
        if source.get("stale"):
            return True
        if key == "fundamental" and stale_fields.intersection({"fundamental", "fundamentals", "financial", "company_profile"}):
            return True
        if key == "technical" and stale_fields.intersection({"quote", "intraday", "technical", "daily_k"}):
            return True
        if key == "information" and (info.get("stale") or "news" in stale_fields or "information" in stale_fields):
            return True
        if key == "market" and stale_fields.intersection({"market", "market_regime", "index", "breadth"}):
            return True
        return key == "fund_flow" and bool(stale_fields.intersection({"quote", "intraday", "fund_flow"}))

    @staticmethod
    def _quality(key: str, source: dict[str, Any], info: dict[str, Any]) -> str:
        if key == "information":
            if info and info.get("auto_buy_eligible") is False:
                return "unusable"
            return str(info.get("quality_status") or source.get("quality_status") or ("missing" if not source else "available")).lower()
        return str(source.get("quality_status") or ("missing" if not source else "available")).lower()

    @staticmethod
    def _pit_usable(key: str, source: dict[str, Any], provenance: dict[str, Any]) -> bool:
        if key == "technical":
            return bool(source) or bool(provenance.get("no_lookahead") or provenance.get("pit_status") == "point_in_time")
        status = str(source.get("pit_status") or "").lower()
        return bool(source.get("available_at")) and status in {"point_in_time", "pit", "historical", "historical_snapshot"}

    @staticmethod
    def _provenance_ok(mode: str, provenance: dict[str, Any]) -> bool:
        if mode != "live":
            return True
        return bool(provenance) and str(provenance.get("mode") or "") in {"realtime_paper", "live"} and not list(provenance.get("stale_data") or [])

    @staticmethod
    def _truth_boundary(key: str, source: dict[str, Any]) -> str:
        if key == "fundamental":
            return "只使用披露日不晚于决策时点的财务/公司画像；缺少披露日期或来源时不得回填为可交易基本面。"
        if key == "fund_flow":
            text = " ".join(str(source.get(k) or "") for k in ("source", "source_name", "source_id", "quality_status")).lower()
            if any(token in text for token in ("eastmoney_sector_flow", "公开资金", "northbound", "北向")):
                return "公开数据源资金字段，可用于相对强弱；仍不是券商逐笔或Level-2账户识别。"
            return "成交额、量比、VWAP和分时量价代理，仅用于承接确认；不得称为主力净流入。"
        if key == "information":
            return "正文/公告优先并按事件去重；标题级证据降低置信度，规则推算未来事件不计方向分。"
        return "由决策时点可见K线/分时计算；指标用于结构与择时，不承诺预测收益。"

    @staticmethod
    def _usage(key: str, mode: str, pit_usable: bool, quality: str) -> str:
        if mode == "backtest":
            return "参与历史评分" if pit_usable and quality not in DecisionDimensionService._UNUSABLE_QUALITY else "仅展示/排除"
        if mode == "live":
            return "实盘预检查与评分" if quality not in DecisionDimensionService._UNUSABLE_QUALITY else "阻断新增仓位"
        return "模拟评分与下单门禁" if quality not in DecisionDimensionService._UNUSABLE_QUALITY else "仅提醒/阻断新增仓位"
