from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
import json


@dataclass(frozen=True)
class MarketSpec:
    market: str
    name: str
    timezone: str
    sessions: list[tuple[str, time, time]]
    refresh_statuses: set[str]
    weekend_closed: bool = True


class MarketCalendar:
    """交易时段与简易交易日历。

    V1.9 的设计原则：
    - UI 不再每 5 秒检查一次休市状态；
    - 如果当前不能自动刷新，返回 next_refresh_at/seconds_to_next_refresh，前端直接 sleep 到下一次开盘/复盘；
    - 初始页面仍然可以展示缓存/最近数据，只有自动拉取外部行情受交易时段约束。
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.config_path = Path(config_path) if config_path else root / "config" / "trading_calendar.json"
        self.extra: dict[str, Any] = self._load_extra()
        self.specs = self._default_specs()

    def _load_extra(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _default_specs(self) -> dict[str, MarketSpec]:
        return {
            "CN": MarketSpec(
                market="CN",
                name="A股/场内基金",
                timezone="Asia/Shanghai",
                sessions=[
                    ("pre_open_auction", time(9, 15), time(9, 25)),
                    ("call_auction_cooldown", time(9, 25), time(9, 30)),
                    ("morning", time(9, 30), time(11, 30)),
                    ("lunch", time(11, 30), time(13, 0)),
                    ("afternoon", time(13, 0), time(14, 57)),
                    ("closing_auction", time(14, 57), time(15, 0)),
                ],
                refresh_statuses={"pre_open_auction", "morning", "afternoon", "closing_auction"},
            ),
            "HK": MarketSpec(
                market="HK",
                name="港股",
                timezone="Asia/Hong_Kong",
                sessions=[
                    ("pre_open_auction", time(9, 0), time(9, 30)),
                    ("morning", time(9, 30), time(12, 0)),
                    ("lunch", time(12, 0), time(13, 0)),
                    ("afternoon", time(13, 0), time(16, 0)),
                    ("closing_auction", time(16, 0), time(16, 10)),
                ],
                refresh_statuses={"pre_open_auction", "morning", "afternoon", "closing_auction"},
            ),
            "US": MarketSpec(
                market="US",
                name="美股",
                timezone="America/New_York",
                sessions=[
                    ("pre_market", time(4, 0), time(9, 30)),
                    ("regular", time(9, 30), time(16, 0)),
                    ("after_hours", time(16, 0), time(20, 0)),
                ],
                # V1.9 默认仅常规交易时段自动刷新；盘前/盘后数据可展示，但不自动高频拉取。
                refresh_statuses={"regular"},
            ),
        }

    def detect_market(self, symbol: str | None = None, fallback: str = "CN") -> str:
        s = str(symbol or "").strip().upper()
        if not s:
            return fallback.upper()
        if s.startswith(("HK", "0HK", "H")) or s.endswith(".HK"):
            return "HK"
        if s.endswith((".US", ".NASDAQ", ".NYSE")):
            return "US"
        return "CN"

    def is_holiday(self, market: str, d: date) -> bool:
        market = market.upper()
        holidays = set(self.extra.get(market, {}).get("holidays", []))
        extra_trading_days = set(self.extra.get(market, {}).get("extra_trading_days", []))
        day = d.isoformat()
        if day in extra_trading_days:
            return False
        if day in holidays:
            return True
        spec = self.specs.get(market, self.specs["CN"])
        if spec.weekend_closed and d.weekday() >= 5:
            return True
        return False

    def next_trading_day(self, market: str, d: date) -> date:
        cur = d
        for _ in range(370):
            if not self.is_holiday(market, cur):
                return cur
            cur += timedelta(days=1)
        return cur

    def _next_refresh_at(self, spec: MarketSpec, now: datetime) -> datetime | None:
        """返回下一次允许自动拉取外部行情的时间。"""
        tz = ZoneInfo(spec.timezone)
        now = now.astimezone(tz)
        d = now.date()
        # 最多向后找一年，通常当天/下个交易日就能找到。
        for day_offset in range(0, 370):
            day = d + timedelta(days=day_offset)
            if self.is_holiday(spec.market, day):
                continue
            for status, start, end in spec.sessions:
                if status not in spec.refresh_statuses:
                    continue
                candidate = datetime.combine(day, start, tzinfo=tz)
                if candidate > now:
                    return candidate
                # 如果当前已经在可刷新时段内，则下一次刷新就是现在。
                end_dt = datetime.combine(day, end, tzinfo=tz)
                if candidate <= now < end_dt:
                    return now
        return None

    def session(self, market: str = "CN", now: datetime | None = None) -> dict[str, Any]:
        market = (market or "CN").upper()
        spec = self.specs.get(market, self.specs["CN"])
        tz = ZoneInfo(spec.timezone)
        now = now.astimezone(tz) if now else datetime.now(tz)
        local_t = now.time()

        if self.is_holiday(market, now.date()):
            return self._result(spec, now, "closed", "休市/非交易日", False)

        current_status = "closed"
        label = "休市"
        for status, start, end in spec.sessions:
            if start <= local_t < end:
                current_status = status
                label = self._label(status)
                break

        can_refresh = current_status in spec.refresh_statuses
        return self._result(spec, now, current_status, label, can_refresh)

    def _result(self, spec: MarketSpec, now: datetime, status: str, label: str, can_refresh: bool) -> dict[str, Any]:
        next_at = self._next_refresh_at(spec, now)
        seconds = None
        if next_at is not None:
            seconds = max(0, int((next_at - now).total_seconds()))
        return {
            "market": spec.market,
            "name": spec.name,
            "timezone": spec.timezone,
            "now": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "status": status,
            "label": label,
            "is_trading": can_refresh,
            "can_refresh": can_refresh,
            "is_trading_day": not self.is_holiday(spec.market, now.date()),
            "next_refresh_at": next_at.isoformat(timespec="seconds") if next_at else None,
            "seconds_to_next_refresh": seconds,
            "sessions": [
                {"status": s, "label": self._label(s), "start": a.strftime("%H:%M"), "end": b.strftime("%H:%M")}
                for s, a, b in spec.sessions
            ],
        }

    def _label(self, status: str) -> str:
        return {
            "pre_open_auction": "集合竞价/开市前竞价",
            "call_auction_cooldown": "竞价撮合过渡",
            "morning": "上午连续竞价",
            "lunch": "午间休市",
            "afternoon": "下午连续竞价",
            "closing_auction": "收盘集合竞价",
            "pre_market": "盘前交易",
            "regular": "常规交易",
            "after_hours": "盘后交易",
            "closed": "休市",
        }.get(status, status)
