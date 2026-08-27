from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Any


def _number(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and result not in {float("inf"), float("-inf")} else None


def _unique(values: list[Any], limit: int = 12) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in rows:
            rows.append(text)
        if len(rows) >= limit:
            break
    return rows


class MultiRoleMarketReviewService:
    """Deterministic, evidence-only review inspired by multi-agent research flows.

    This service never creates an order. It separates evidence gathering,
    opposing arguments, risk vetoes and the final research-only action so that
    an optional language model cannot bypass the deterministic trading core.
    """

    version = "v3.28-multi-role-evidence-review"

    def build(
        self,
        *,
        symbols: list[str],
        decisions: list[dict[str, Any]],
        score_rows: dict[str, dict[str, Any]],
        evidence: list[dict[str, Any]],
        symbol_impacts: list[dict[str, Any]],
        theme_trends: list[dict[str, Any]],
        macro_watchlist: list[dict[str, Any]],
        risk_flags: list[str],
        safety: dict[str, Any],
        broker_connected: bool,
        recommended_action: str,
    ) -> dict[str, Any]:
        normalized_symbols = _unique(symbols, 30)
        score_values = [_number(row.get("score")) for row in decisions]
        valid_scores = [value for value in score_values if value is not None]
        high_scores = [row for row in decisions if (_number(row.get("score")) or 0) >= 70]
        low_scores = [row for row in decisions if 0 < (_number(row.get("score")) or 0) < 55]
        missing_scores = [row for row in decisions if _number(row.get("score")) is None]

        direct_impacts = [row for row in symbol_impacts if row.get("related_events")]
        traceable_evidence = [
            row
            for row in evidence
            if row.get("source") and (row.get("source_ref") or row.get("source_api") or row.get("source_page"))
        ]
        positive_themes = [row for row in theme_trends if row.get("trend") == "增强"]
        negative_themes = [row for row in theme_trends if row.get("trend") in {"走弱", "分歧"}]
        missing_themes = [row for row in theme_trends if row.get("trend") == "等待数据"]
        macro_hits = [row for row in macro_watchlist if int(row.get("evidence_count") or 0) > 0]

        technical_support = [
            f"{row.get('symbol')} 综合评分 {float(row.get('score')):.1f}，可进入模拟验证"
            for row in high_scores[:6]
        ]
        technical_counter = [
            f"{row.get('symbol')} 综合评分 {float(row.get('score')):.1f}，低于自动新增仓位观察线"
            for row in low_scores[:6]
        ]
        score_refs = [
            f"score:{row.get('symbol')}:{row.get('score_time') or 'time-missing'}"
            for row in decisions
            if row.get("score") is not None
        ]
        roles = [
            self._role(
                key="technical_score",
                label="评分与技术核验",
                status="ready" if valid_scores else "missing",
                stance=self._stance(len(technical_support), len(technical_counter)),
                confidence=self._coverage_confidence(len(valid_scores), len(normalized_symbols)),
                summary=(
                    f"{len(valid_scores)}/{len(normalized_symbols)} 只标的具有评分溯源，平均 {sum(valid_scores) / len(valid_scores):.1f} 分。"
                    if valid_scores
                    else "当前股票池没有可用评分溯源，不能用技术或综合得分替代真实证据。"
                ),
                support=technical_support,
                counter=technical_counter,
                missing=[f"{row.get('symbol')} 缺少评分溯源" for row in missing_scores],
                evidence_refs=score_refs,
            ),
            self._fundamental_role(normalized_symbols, score_rows),
            self._role(
                key="information",
                label="信息面核验",
                status="ready" if traceable_evidence else "missing",
                stance="有直接命中" if direct_impacts else "仅作环境观察",
                confidence=min(0.9, 0.25 + len(traceable_evidence) * 0.04 + len(direct_impacts) * 0.08),
                summary=f"可追溯信息 {len(traceable_evidence)} 条，直接映射当前股票池 {len(direct_impacts)} 只。",
                support=[
                    f"{row.get('symbol')} {row.get('name') or ''} 命中 {len(row.get('related_events') or [])} 条产业链/公司事件"
                    for row in direct_impacts[:6]
                ],
                counter=_unique([str(x) for x in risk_flags if any(word in str(x) for word in ("新闻", "信息", "公告", "负面"))], 6),
                missing=[] if traceable_evidence else ["缺少近期且可跳转的真实信息来源"],
                evidence_refs=[self._source_ref(row, "news") for row in traceable_evidence[:10]],
            ),
            self._role(
                key="capital_flow",
                label="资金与主线板块核验",
                status="partial" if theme_trends else "missing",
                stance=self._stance(len(positive_themes), len(negative_themes)),
                confidence=min(0.85, 0.25 + len(theme_trends) * 0.04),
                summary=f"板块增强 {len(positive_themes)} 个，分歧/走弱 {len(negative_themes)} 个；公开板块资金不等于 Level-2 主力账户。",
                support=[f"{row.get('theme')}：{'; '.join(row.get('support_evidence') or [])}" for row in positive_themes[:6]],
                counter=[f"{row.get('theme')}：{'; '.join(row.get('counter_evidence') or [])}" for row in negative_themes[:6]],
                missing=[f"{row.get('theme')}：{'; '.join(row.get('missing_data') or [])}" for row in missing_themes[:6]],
                evidence_refs=[self._source_ref(row, "sector") for row in theme_trends if row.get("source_ref")][:10],
            ),
            self._role(
                key="market_macro",
                label="大盘与全球环境核验",
                status="ready" if macro_hits else "partial",
                stance="风险环境复核",
                confidence=min(0.85, 0.3 + len(macro_hits) * 0.06),
                summary=f"宏观观察项命中 {len(macro_hits)} 个；只用于环境调分和风险解释，不能单独触发买入。",
                support=[f"{row.get('label')}：{row.get('latest_title')}" for row in macro_hits[:6]],
                counter=[],
                missing=[row.get("label") for row in macro_watchlist if not row.get("evidence_count")][:6],
                evidence_refs=[self._source_ref(row, "macro") for row in macro_hits[:10]],
            ),
        ]

        bull_case = _unique(
            technical_support
            + [f"{row.get('theme')} 板块资金/强度增强" for row in positive_themes]
            + [f"{row.get('symbol')} 存在可追溯直接事件映射" for row in direct_impacts],
            10,
        )
        bear_case = _unique(
            technical_counter
            + [f"{row.get('theme')} 当前{row.get('trend')}" for row in negative_themes]
            + list(risk_flags),
            12,
        )
        unresolved = _unique(
            [f"{row.get('symbol')} 缺少评分" for row in missing_scores]
            + [f"{row.get('theme')} 板块资金样本不足" for row in missing_themes]
            + [missing for role in roles for missing in role.get("missing_data") or []],
            12,
        )

        blockers: list[str] = []
        if safety.get("LIVE_KILL_SWITCH"):
            blockers.append("实盘紧急停止已开启")
        if not safety.get("LIVE_TRADING_ENABLED"):
            blockers.append("真实交易总开关未开启")
        if not broker_connected:
            blockers.append("券商未连接或未授权")
        if not valid_scores:
            blockers.append("股票池缺少评分溯源")
        if safety.get("ORDER_CONFIRM_REQUIRED"):
            blockers.append("真实订单必须进入人工确认队列")
        blockers = _unique(blockers + list(risk_flags), 16)
        hard_block = bool(safety.get("LIVE_KILL_SWITCH") or not safety.get("LIVE_TRADING_ENABLED") or not broker_connected)
        risk_verdict = "实盘阻断，仅允许研究/模拟" if hard_block else "通过预检查后仍需人工确认"

        action_map = {
            "paper_then_precheck": "先回测，再实时模拟和实盘预检查",
            "watch": "继续观察并等待证据确认",
            "hold_or_collect_data": "补充数据并保持观察",
        }
        final_action = action_map.get(recommended_action, "保持观察并人工复核")
        if hard_block:
            final_action = f"{final_action}；禁止直接真实下单"

        canonical = {
            "version": self.version,
            "symbols": normalized_symbols,
            "decisions": [
                {
                    "symbol": row.get("symbol"),
                    "score": row.get("score"),
                    "action": row.get("action"),
                    "score_time": row.get("score_time"),
                    "risk_flags": row.get("risk_flags") or [],
                }
                for row in decisions
            ],
            "evidence": [
                {
                    "title": row.get("title"),
                    "source": row.get("source"),
                    "published_at": row.get("published_at"),
                    "source_ref": row.get("source_ref"),
                }
                for row in evidence
            ],
            "themes": [
                {"theme": row.get("theme"), "trend": row.get("trend"), "published_at": row.get("published_at")}
                for row in theme_trends
            ],
            "safety": safety,
            "broker_connected": broker_connected,
        }
        evidence_hash = sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return {
            "review_id": f"MRR-{evidence_hash[:16]}",
            "version": self.version,
            "roles": roles,
            "debate": {
                "bull_case": bull_case or ["没有足够真实证据形成支持新增仓位的观点"],
                "bear_case": bear_case or ["当前未发现额外反证，但这不代表风险为零"],
                "unresolved": unresolved,
                "consensus": "先让证据相互校验，再由独立风控裁决；单一角色不能创建订单。",
            },
            "risk_committee": {
                "verdict": "blocked" if hard_block else "confirmation_required",
                "verdict_cn": risk_verdict,
                "blocking_reasons": blockers,
                "safe_modes": ["历史回测", "实时模拟", "实盘预检查"] if hard_block else ["历史回测", "实时模拟", "实盘预检查", "人工确认队列"],
                "kill_switch": bool(safety.get("LIVE_KILL_SWITCH")),
            },
            "portfolio_committee": {
                "action": recommended_action,
                "action_cn": final_action,
                "order_capability": False,
                "real_order_allowed": False,
                "reason": "最终执行仍由统一风控、订单预检查、确认队列和 BrokerAdapter 决定。",
            },
            "checkpoint": {
                "evidence_hash": evidence_hash,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "input_counts": {
                    "symbols": len(normalized_symbols),
                    "scores": len(valid_scores),
                    "traceable_evidence": len(traceable_evidence),
                    "direct_symbol_impacts": len(direct_impacts),
                    "theme_trends": len(theme_trends),
                },
                "persisted": False,
            },
            "retrospective": {
                "status": "等待回测/模拟结果",
                "compare_with": ["买入持有", "对应宽基指数", "策略自身历史版本"],
                "metrics": ["收益率", "最大回撤", "夏普", "胜率", "证据命中率", "风控阻断有效率"],
                "note": "复盘只评价证据和决策质量，不把未来结果反向写入历史时点。",
            },
            "research_only": True,
            "order_capability": False,
        }

    @staticmethod
    def _role(
        *,
        key: str,
        label: str,
        status: str,
        stance: str,
        confidence: float,
        summary: str,
        support: list[str],
        counter: list[str],
        missing: list[str],
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        return {
            "role": key,
            "label": label,
            "status": status,
            "stance": stance,
            "confidence": round(max(0.0, min(float(confidence), 1.0)), 2),
            "summary": summary,
            "supporting_evidence": _unique(support, 8),
            "counter_evidence": _unique(counter, 8),
            "missing_data": _unique(missing, 8),
            "evidence_refs": _unique(evidence_refs, 12),
        }

    def _fundamental_role(self, symbols: list[str], score_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
        available: list[str] = []
        missing: list[str] = []
        for symbol in symbols:
            row = score_rows.get(symbol) or {}
            snapshot = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
            value = next(
                (
                    _number(source.get(key))
                    for source in (row, snapshot)
                    for key in ("fundamental_score", "finance_score", "value_score")
                    if _number(source.get(key)) is not None
                ),
                None,
            )
            if value is None:
                missing.append(f"{symbol} 缺少可追溯基本面分项")
            else:
                available.append(f"{symbol} 基本面/价值分项 {value:.1f}")
        return self._role(
            key="fundamental",
            label="基本面核验",
            status="ready" if available and not missing else "partial" if available else "missing",
            stance="需结合披露时点复核" if available else "不参与裁决",
            confidence=self._coverage_confidence(len(available), len(symbols)),
            summary=f"{len(available)}/{len(symbols)} 只标的具有独立基本面/价值分项；缺失时不会用综合分代替。",
            support=available,
            counter=[],
            missing=missing,
            evidence_refs=[f"fundamental:{text.split()[0]}" for text in available],
        )

    @staticmethod
    def _coverage_confidence(available: int, total: int) -> float:
        if total <= 0:
            return 0.1
        return min(0.9, 0.2 + 0.7 * available / total)

    @staticmethod
    def _stance(support: int, counter: int) -> str:
        if support > counter:
            return "支持模拟验证"
        if counter > support:
            return "偏谨慎"
        return "证据分歧/观察"

    @staticmethod
    def _source_ref(row: dict[str, Any], prefix: str) -> str:
        source = str(
            row.get("source_ref")
            or row.get("latest_source_ref")
            or row.get("source_url")
            or row.get("source_page")
            or row.get("latest_source_page")
            or row.get("source_api")
            or row.get("latest_source_api")
            or "source-missing"
        )
        stamp = str(row.get("published_at") or row.get("latest_title") or row.get("theme") or "time-missing")
        digest = sha256(f"{prefix}|{source}|{stamp}".encode("utf-8")).hexdigest()[:12]
        return f"{prefix}:{digest}"
