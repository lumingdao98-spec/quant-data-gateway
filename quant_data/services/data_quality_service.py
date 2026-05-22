from __future__ import annotations
from typing import Any
from quant_data.models import Bar, Quote


def _num(x, default=0.0):
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


class DataQualityService:
    def assess_bars(self, bars: list[Bar], expected_min: int = 120, adjust: str = "qfq") -> dict:
        n = len(bars or [])
        missing = 0
        outliers = 0
        prev_close = None
        for b in bars or []:
            vals = [b.open, b.high, b.low, b.close]
            if any(v is None or _num(v) <= 0 for v in vals):
                missing += 1
            c = _num(b.close)
            if prev_close and prev_close > 0:
                pct = abs(c / prev_close - 1) * 100
                if pct > 25:
                    outliers += 1
            if c > 0:
                prev_close = c
        completeness = min(1.0, n / max(1, expected_min))
        penalty = missing * 2 + outliers * 4
        score = max(0, min(100, completeness * 100 - penalty))
        return {
            "bars_count": n,
            "expected_min": expected_min,
            "adjust": adjust,
            "missing_rows": missing,
            "outlier_rows": outliers,
            "quality_score": round(score, 2),
            "level": "good" if score >= 85 else "usable" if score >= 65 else "weak",
            "basis": "检查K线数量、缺失值、异常跳变；复权口径用于回撤和技术评分。",
        }

    def assess_quote(self, q: Quote) -> dict:
        fields = [q.last, q.amount, q.volume, q.change_pct]
        missing = sum(1 for x in fields if x is None)
        score = 100 - missing * 18
        if _num(q.last) <= 0:
            score -= 35
        if _num(q.amount) <= 0:
            score -= 15
        return {"quality_score": max(0, round(score, 2)), "missing_core_fields": missing, "source": q.source, "level": "good" if score >= 80 else "usable" if score >= 60 else "weak"}

    def assess_news(self, items: list[dict]) -> dict:
        n = len(items or [])
        valid = 0
        official = 0
        unknown_time = 0
        unique_keys: set[str] = set()
        categories: dict[str, int] = {}
        for it in items or []:
            title = str(it.get("title") or "")
            body = str(it.get("summary") or it.get("content") or "")
            if len(title) >= 6 and len(title + body) >= 20:
                valid += 1
            src = str(it.get("source") or "")
            if any(k in src for k in ["巨潮", "交易所", "公告", "证监", "央行", "统计局"]):
                official += 1
            if not (it.get("publish_time") or it.get("event_time") or it.get("time")):
                unknown_time += 1
            key = str(it.get("event_key") or it.get("dedup_key") or title)
            if key:
                unique_keys.add(key)
            cat = str(it.get("category") or it.get("event_type") or "未分类")
            categories[cat] = categories.get(cat, 0) + 1
        score = 0 if n == 0 else min(100, valid / n * 55 + official / max(1, n) * 25 + len(unique_keys) / max(1, n) * 20 - unknown_time / max(1, n) * 10)
        return {"raw_items": n, "valid_like_items": valid, "official_items": official, "unique_event_keys": len(unique_keys), "unknown_time_items": unknown_time, "category_counts": categories, "quality_score": round(score, 2)}
