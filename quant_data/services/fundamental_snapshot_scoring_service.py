from __future__ import annotations

import re
from datetime import datetime
from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    if value in (None, "", "--", "null"):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if isfinite(result) else None
    raw = str(value).strip().replace(",", "").replace("％", "%")
    if not raw or raw in {"-", "--"}:
        return None
    multiplier = 1.0
    if "万亿" in raw:
        multiplier = 1e12
    elif "亿" in raw:
        multiplier = 1e8
    elif "万" in raw:
        multiplier = 1e4
    match = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
    if not match:
        return None
    try:
        result = float(match.group(0)) * multiplier
    except ValueError:
        return None
    return result if isfinite(result) else None


def _percent(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    raw = str(value or "")
    if "%" not in raw and abs(number) <= 1:
        return number * 100
    return number


def _date(value: Any) -> datetime | None:
    raw = re.sub(r"[^0-9]", "", str(value or ""))
    if len(raw) < 8:
        return None
    try:
        return datetime.strptime(raw[:8], "%Y%m%d")
    except ValueError:
        return None


class FundamentalSnapshotScoringService:
    """Score only traceable, already disclosed company fundamentals.

    Absolute revenue size is deliberately not treated as quality and periods
    are not compared unless the upstream snapshot provides a comparable growth
    field. This prevents a current cumulative report from being compared with
    a different reporting period merely to manufacture growth.
    """

    def evaluate(
        self,
        *,
        symbol: str,
        profile: dict[str, Any] | None,
        quote: dict[str, Any] | None = None,
        decision_time: datetime | None = None,
    ) -> dict[str, Any]:
        profile = dict(profile or {})
        quote = dict(quote or {})
        now = decision_time or datetime.now()
        profile_type = str(profile.get("profile_type") or "").upper()
        if profile_type == "ETF" or str(quote.get("asset_type") or "").lower() == "etf":
            return {
                "score": None,
                "quality_status": "not_applicable",
                "source": "ETF不适用个股财务评分",
                "source_ref": f"/api/company/profile/{symbol}",
                "available_at": "",
                "pit_status": "not_applicable",
                "stale": False,
                "confidence": "not_applicable",
                "evidence_fields": [],
                "contributions": [],
                "missing_reasons": ["ETF按指数、跟踪误差、流动性和估值带分析，不套用个股PE/ROE经营质量模型"],
            }

        summary = dict(profile.get("financial_summary") or {})
        history = [dict(row) for row in (profile.get("financial_history") or []) if isinstance(row, dict)]
        latest = history[0] if history else {}
        report_raw = summary.get("latest_report_date") or latest.get("report_date")
        report_date = _date(report_raw)
        sources = [str(value) for value in (profile.get("sources") or []) if str(value or "").strip()]
        financial_sources = [value for value in sources if any(token in value for token in ("业绩", "财务", "巨潮", "交易所", "年报", "季报"))]
        missing: list[str] = []
        if report_date is None:
            missing.append("财务快照缺少可解析披露/报告日期")
        elif report_date > now:
            missing.append("财务快照日期晚于决策时点，禁止回填")
        if not financial_sources:
            missing.append("公司画像没有可追溯财务来源标识")
        if missing:
            return {
                "score": None,
                "quality_status": "missing",
                "source": "数据源缺失",
                "source_ref": f"/api/company/profile/{symbol}",
                "available_at": report_date.date().isoformat() if report_date else "",
                "pit_status": "rejected" if report_date and report_date > now else "missing",
                "stale": False,
                "confidence": "low",
                "evidence_fields": [],
                "contributions": [],
                "missing_reasons": missing,
            }

        report_age_days = max(0, (now.date() - report_date.date()).days)
        stale = report_age_days > 550
        score = 50.0
        evidence: list[dict[str, Any]] = []

        def add(key: str, label: str, raw: Any, adjustment: float, explanation: str) -> None:
            nonlocal score
            score += adjustment
            evidence.append(
                {
                    "factor_key": key,
                    "label": label,
                    "raw_value": raw,
                    "adjustment": round(adjustment, 4),
                    "explanation": explanation,
                }
            )

        pe = _number(quote.get("pe_dynamic") or quote.get("pe_ttm"))
        if pe is not None:
            adjustment = -10.0 if pe <= 0 else 10.0 if pe <= 15 else 6.0 if pe <= 25 else 2.0 if pe <= 40 else -4.0 if pe <= 60 else -9.0
            add("pe", "市盈率", pe, adjustment, "只用于估值区间校验；亏损或极高估值扣分，不代表低PE必然低风险。")

        pb = _number(quote.get("pb"))
        if pb is not None and pb > 0:
            adjustment = 7.0 if pb <= 1.5 else 4.0 if pb <= 3 else 0.0 if pb <= 6 else -4.0 if pb <= 10 else -8.0
            add("pb", "市净率", pb, adjustment, "按宽区间做估值约束；行业差异仍需在策略适配中解释。")

        roe_raw = summary.get("latest_roe") or latest.get("roe")
        roe = _percent(roe_raw)
        if roe is not None:
            adjustment = 12.0 if roe >= 20 else 8.0 if roe >= 12 else 3.0 if roe >= 6 else -2.0 if roe >= 0 else -12.0
            add("roe", "净资产收益率", roe_raw, adjustment, "使用最新已披露ROE验证盈利质量。")

        gross_raw = latest.get("gross_margin")
        gross = _percent(gross_raw)
        if gross is not None:
            adjustment = 5.0 if gross >= 35 else 2.0 if gross >= 18 else -3.0 if gross >= 5 else -7.0
            add("gross_margin", "毛利率", gross_raw, adjustment, "毛利率只作经营质量辅证，不跨行业直接排名。")

        debt_raw = latest.get("debt_ratio")
        debt = _percent(debt_raw)
        if debt is not None:
            adjustment = 5.0 if debt < 30 else 2.0 if debt < 55 else -3.0 if debt < 75 else -9.0
            add("debt_ratio", "资产负债率", debt_raw, adjustment, "高杠杆增加财务风险；金融行业需结合行业模型复核。")

        net_profit_raw = summary.get("latest_net_profit") or latest.get("net_profit")
        net_profit = _number(net_profit_raw)
        if net_profit is not None:
            add(
                "net_profit_sign",
                "净利润符号",
                net_profit_raw,
                4.0 if net_profit > 0 else -12.0,
                "只验证是否盈利，不以绝对规模冒充成长性，也不跨不同报告期计算增长。",
            )

        eps_raw = latest.get("eps")
        eps = _number(eps_raw)
        if eps is not None:
            add("eps_sign", "每股收益符号", eps_raw, 3.0 if eps > 0 else -8.0, "仅验证最新披露EPS正负。")

        latest_revenue = summary.get("latest_revenue") or latest.get("revenue")
        if _number(latest_revenue) is not None:
            evidence.append(
                {
                    "factor_key": "revenue_disclosed",
                    "label": "营业收入已披露",
                    "raw_value": latest_revenue,
                    "adjustment": 0.0,
                    "explanation": "记录披露完整性，不按收入绝对规模加分。",
                }
            )

        if len(evidence) < 2:
            missing.append("可评分财务/估值字段少于2项")
            return {
                "score": None,
                "quality_status": "missing",
                "source": "公开财务快照字段不足",
                "source_ref": f"/api/company/profile/{symbol}",
                "available_at": report_date.date().isoformat(),
                "pit_status": "point_in_time",
                "stale": stale,
                "confidence": "low",
                "evidence_fields": [row["factor_key"] for row in evidence],
                "contributions": evidence,
                "missing_reasons": missing,
            }

        score = max(5.0, min(95.0, score))
        quality = "stale" if stale else "available" if len(evidence) >= 5 else "partial"
        confidence = "high" if len(evidence) >= 6 and report_age_days <= 240 else "medium" if len(evidence) >= 4 else "low"
        missing_fields = [
            label
            for key, label in (
                ("roe", "ROE"),
                ("gross_margin", "毛利率"),
                ("debt_ratio", "资产负债率"),
                ("pe", "PE"),
                ("pb", "PB"),
            )
            if key not in {row["factor_key"] for row in evidence}
        ]
        if missing_fields:
            missing.append("尚缺字段：" + "、".join(missing_fields))
        return {
            "score": round(score, 2),
            "quality_status": quality,
            "source": "公开财务快照（" + "/".join(financial_sources[:2]) + "）",
            "source_ref": f"/api/company/profile/{symbol}",
            "available_at": report_date.date().isoformat(),
            "report_date": report_date.date().isoformat(),
            "report_age_days": report_age_days,
            "pit_status": "point_in_time",
            "stale": stale,
            "confidence": confidence,
            "evidence_fields": [row["factor_key"] for row in evidence],
            "contributions": evidence,
            "missing_reasons": missing,
            "truth_boundary": "只使用不晚于决策时点的已披露财务与当前估值；未取得可比期间时不计算营收/利润增长。",
        }
