from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .models import DISCLAIMER, BacktestConfig


def field_value(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


def date_text(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    text = str(value)
    return text[:10]


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


class BacktestDataLoader:
    """Load and validate historical bars without using future rows."""

    def __init__(self, market_service: Any | None = None) -> None:
        self.market_service = market_service

    def load_bars(
        self,
        symbol: str,
        config: BacktestConfig | None = None,
        *,
        bars: list[Any] | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> tuple[list[Any], dict[str, Any]]:
        cfg = config or BacktestConfig(symbols=[symbol])
        if bars is None:
            if self.market_service is None:
                return [], self.quality_report([], cfg, symbol=symbol, cache_status="missing_service")
            bars = self.market_service.get_kline(
                symbol,
                frame=cfg.frame,
                limit=limit or 520,
                adjust=cfg.adjust,
                force_refresh=force_refresh,
            )
            cache_status = "service"
        else:
            cache_status = "memory"
        rows = sorted(list(bars), key=lambda x: date_text(field_value(x, "ts", field_value(x, "date", ""))))
        if limit:
            rows = rows[-int(limit) :]
        report = self.quality_report(rows, cfg, symbol=symbol, cache_status=cache_status)
        return rows, report

    def quality_report(
        self,
        bars: list[Any],
        config: BacktestConfig | None = None,
        *,
        symbol: str | None = None,
        cache_status: str = "memory",
    ) -> dict[str, Any]:
        cfg = config or BacktestConfig()
        dates = [date_text(field_value(x, "ts", field_value(x, "date", ""))) for x in bars]
        duplicate_dates = sorted({d for d in dates if d and dates.count(d) > 1})
        non_monotonic = any(a >= b for a, b in zip(dates, dates[1:]) if a and b)
        zero_volume = []
        ohlc_anomalies = []
        suspended = []
        limit_up = []
        limit_down = []
        missing_weekdays = []
        previous_close: float | None = None
        previous_date: date | None = None
        for row, d in zip(bars, dates):
            open_ = number(field_value(row, "open"))
            high = number(field_value(row, "high"))
            low = number(field_value(row, "low"))
            close = number(field_value(row, "close"))
            volume = number(field_value(row, "volume"))
            if volume <= 0:
                zero_volume.append(d)
                suspended.append(d)
            if high + 1e-9 < max(open_, close) or low - 1e-9 > min(open_, close) or high < low:
                ohlc_anomalies.append(d)
            if previous_close and previous_close > 0:
                change_pct = (close / previous_close - 1) * 100
                if change_pct >= 9.7:
                    limit_up.append(d)
                if change_pct <= -9.7:
                    limit_down.append(d)
            try:
                current_date = date.fromisoformat(d)
            except ValueError:
                current_date = None
            if previous_date and current_date:
                gap = current_date - previous_date
                if gap > timedelta(days=4):
                    missing_weekdays.append({"from": previous_date.isoformat(), "to": current_date.isoformat(), "days": gap.days})
            if current_date:
                previous_date = current_date
            previous_close = close if close > 0 else previous_close

        bars_count = len(bars)
        insufficient = bars_count < max(5, cfg.warmup_bars)
        warnings: list[str] = []
        if insufficient:
            warnings.append(f"样本不足：{bars_count} 根，少于 warmup {cfg.warmup_bars}")
        if duplicate_dates:
            warnings.append("存在重复交易日")
        if non_monotonic:
            warnings.append("交易日顺序异常")
        if zero_volume:
            warnings.append("存在零成交量/疑似停牌")
        if ohlc_anomalies:
            warnings.append("存在 OHLC 异常")
        if cfg.adjust not in {"qfq", "none", "hfq"}:
            warnings.append("复权口径未知")
        return {
            "symbol": symbol,
            "bars": bars_count,
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None,
            "adjust": cfg.adjust,
            "frame": cfg.frame,
            "cache_status": cache_status,
            "warmup_bars": cfg.warmup_bars,
            "sample_insufficient": insufficient,
            "duplicate_dates": duplicate_dates,
            "non_monotonic": non_monotonic,
            "missing_weekday_gaps": missing_weekdays,
            "zero_volume_dates": zero_volume,
            "suspended_dates": suspended,
            "limit_up_dates": limit_up,
            "limit_down_dates": limit_down,
            "ohlc_anomalies": ohlc_anomalies,
            "pit_note": "信号只允许读取当前交易日及以前数据，下一交易日或指定执行日成交。",
            "warnings": warnings,
            "disclaimer": DISCLAIMER,
        }

    @staticmethod
    def assert_no_lookahead(signal_date: str, execution_date: str, features_until: str | None = None) -> tuple[bool, str]:
        feature_date = features_until or signal_date
        if feature_date > signal_date:
            return False, "特征日期晚于信号日期，存在未来函数风险"
        if execution_date <= signal_date:
            return False, "成交日未晚于信号日，违反下一交易日成交假设"
        return True, "no_lookahead_ok"
