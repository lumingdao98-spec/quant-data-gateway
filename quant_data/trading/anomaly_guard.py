from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AnomalyResult:
    anomaly_tags: list[str] = field(default_factory=list)
    anomaly_score: float = 0.0
    severity: int = 0
    action_suggestion: str = "allow"
    evidence: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnomalyGuard:
    """Detects public-data observable anomalies without pretending to have Level-2 flow."""

    def check(self, features: dict[str, Any] | None = None) -> AnomalyResult:
        f = features or {}
        tags: list[str] = []
        evidence: list[str] = []
        score = 0.0

        def add(tag: str, weight: float, text: str) -> None:
            nonlocal score
            tags.append(tag)
            evidence.append(text)
            score += weight

        if self._num(f.get("intraday_spike_reversal_pct")) <= -3:
            add("快速拉升后回落", 18, "分时冲高后快速回落超过 3%")
        if self._num(f.get("high_position_pct")) >= 80 and self._num(f.get("volume_ratio")) >= 2 and self._num(f.get("change_pct")) < 1:
            add("高位放量滞涨", 18, "高位区域放量但价格推进不足")
        if f.get("false_breakout") or (self._num(f.get("breakout_failed_pct")) <= -1):
            add("假突破", 16, "突破后跌回关键位")
        if self._num(f.get("upper_shadow_pct")) >= 4:
            add("长上影诱多", 12, "长上影线显示上方抛压")
        if self._num(f.get("turnover")) >= 8 and self._num(f.get("change_pct")) <= 0.5:
            add("高换手不涨", 12, "高换手但涨幅不足")
        if f.get("break_ma20") or self._num(f.get("ma20_deviation_pct")) <= -2:
            add("跌破MA20", 15, "收盘或现价明显跌破 MA20")
        if f.get("break_vwap") or self._num(f.get("vwap_distance_pct")) <= -1.5:
            add("跌破VWAP", 12, "价格跌破 VWAP/成本线")
        if f.get("intraday_avg_lost"):
            add("分时均价线失守", 10, "分时均价线失守")
        if self._num(f.get("late_selloff_pct")) <= -2:
            add("尾盘砸盘", 12, "尾盘快速下杀")
        if f.get("limit_up_broken"):
            add("涨停炸板", 20, "涨停板打开后回落")
        if f.get("large_order_no_price_up"):
            add("大单异动但价格不涨", 10, "公开盘口/成交额仅提示需人工核验")
        if f.get("negative_news") or f.get("info_negative_veto"):
            add("信息面突发负面", 28, "重大负面信息触发买入 veto")
        if self._num(f.get("gap_open_pct")) <= -3:
            add("跳空低开", 14, "跳空低开超过 3%")
        if f.get("sector_cooling") or self._num(f.get("sector_score")) < 35:
            add("板块退潮", 10, "板块/题材强度退潮")
        if f.get("liquidity_drop") or self._num(f.get("amount_change_pct")) <= -40:
            add("流动性骤降", 10, "成交额/流动性明显下降")
        if f.get("stale_data") or f.get("quote_stale"):
            add("行情过期", 22, "行情或分时数据过期")

        score = min(100.0, score)
        severity = 0 if score < 15 else 1 if score < 30 else 2 if score < 55 else 3 if score < 80 else 4
        if any(x in tags for x in ["信息面突发负面", "行情过期"]):
            action = "block_buy"
        elif severity >= 4:
            action = "force_exit"
        elif severity >= 3:
            action = "block_buy"
        elif severity >= 2:
            action = "reduce"
        elif severity >= 1:
            action = "manual_confirm"
        else:
            action = "allow"
        return AnomalyResult(
            anomaly_tags=list(dict.fromkeys(tags)),
            anomaly_score=round(score, 2),
            severity=severity,
            action_suggestion=action,
            evidence=list(dict.fromkeys(evidence)),
        )

    def _num(self, value: Any) -> float:
        try:
            return float(value if value is not None else 0.0)
        except Exception:
            return 0.0
