from __future__ import annotations

import calendar
import hashlib
from datetime import date, datetime, time
from typing import Any, Iterable

from quant_data.services.news_cleaner import parse_datetime


EVENT_TYPE_NAMES = {
    "shareholder_meeting": "股东大会",
    "board_meeting": "董事会/监事会",
    "financial_report": "财报或业绩披露",
    "dividend": "分红派息/除权除息",
    "holder_change": "回购增减持/解禁",
    "regulatory": "监管事项",
    "contract_order": "合同/订单事项",
    "investment_project": "项目投产/投资事项",
    "market_macro": "宏观/市场事件",
    "derivatives_settlement": "股指衍生品交割观察日",
    "etf_option_expiry": "ETF期权行权观察日",
    "reporting_window": "定期报告集中披露窗口",
    "general_news": "待办事件",
}

EVENT_IMPACT_WINDOWS = {
    "shareholder_meeting": "会前3日至会后1日",
    "board_meeting": "会前2日至公告后1日",
    "financial_report": "披露前5日至披露后2日",
    "dividend": "登记日前2日至除权后2日",
    "holder_change": "执行日前3日至执行后3日",
    "regulatory": "事项落实前后持续观察",
    "contract_order": "生效前后3日",
    "investment_project": "投产/落地前后5日",
    "market_macro": "公布前1日至公布后1日",
    "derivatives_settlement": "当周三至下周一",
    "etf_option_expiry": "行权日前2日至后1日",
    "reporting_window": "窗口期内持续观察",
    "general_news": "事件日前后2日",
}


class InformationEventCalendarService:
    """Build an evidence-only calendar without treating future outcomes as facts."""

    def build(
        self,
        symbol: str,
        name: str,
        items: Iterable[dict[str, Any]] | None = None,
        global_items: Iterable[dict[str, Any]] | None = None,
        now: datetime | None = None,
        horizon_days: int = 120,
    ) -> dict[str, Any]:
        current = now or datetime.now()
        horizon_days = max(7, min(int(horizon_days or 120), 366))
        events: list[dict[str, Any]] = []
        for item in list(items or []) + list(global_items or []):
            event = self._from_information_item(symbol, name, item, current, horizon_days)
            if event:
                events.append(event)
        events.extend(self._rule_based_market_events(symbol, current, horizon_days))
        deduped = self._deduplicate(events)
        deduped.sort(key=lambda row: (row.get("scheduled_at") or "9999", row.get("event_type") or ""))
        confirmed = sum(1 for row in deduped if row.get("confirmation_status") == "公开来源已确认")
        inferred = sum(1 for row in deduped if row.get("confirmation_status") == "规则推算待确认")
        high_attention = sum(1 for row in deduped if row.get("attention_level") == "高")
        return {
            "symbol": str(symbol or ""),
            "name": str(name or symbol or ""),
            "generated_at": current.isoformat(timespec="seconds"),
            "horizon_days": horizon_days,
            "count": len(deduped),
            "confirmed_count": confirmed,
            "rule_inferred_count": inferred,
            "high_attention_count": high_attention,
            "events": deduped,
            "score_included": False,
            "scoring_rule": "未来事件在结果公布或事项发生前不预判方向、不直接加减当前信息分；仅用于提高刷新频率、限制自动新增仓位或触发人工确认。",
            "truth_rule": "公开来源明确日期标记为已确认；制度日期仅作规则推算，遇节假日或交易所调整必须以官方日历为准。",
        }

    def _from_information_item(
        self,
        symbol: str,
        name: str,
        item: dict[str, Any],
        current: datetime,
        horizon_days: int,
    ) -> dict[str, Any] | None:
        event_dt = parse_datetime(item.get("event_time"))
        if event_dt is None:
            return None
        delta_days = (event_dt.date() - current.date()).days
        if delta_days < 0 or delta_days > horizon_days:
            return None
        event_type = str(item.get("event_type") or "general_news")
        source = str(item.get("source") or item.get("source_name") or "未知来源")
        source_ref = str(item.get("attachment_url") or item.get("url") or item.get("source_ref") or "")
        credibility = float(item.get("credibility_score") or 0)
        source_type = str(item.get("source_type") or "")
        confirmed = bool(source_ref and (source_type == "announcement" or credibility >= 80))
        title = str(item.get("title") or EVENT_TYPE_NAMES.get(event_type) or "未来事项")
        attention_level = self._attention_level(event_type, delta_days)
        identity_title = str(item.get("period") or event_type) if event_type != "general_news" else title
        return {
            "event_id": self._event_id(symbol, event_type, event_dt.date(), identity_title),
            "symbol": str(symbol or ""),
            "name": str(name or symbol or ""),
            "event_type": event_type,
            "event_type_cn": EVENT_TYPE_NAMES.get(event_type, EVENT_TYPE_NAMES["general_news"]),
            "title": title,
            "scheduled_at": event_dt.isoformat(timespec="minutes"),
            "days_until": delta_days,
            "confirmation_status": "公开来源已确认" if confirmed else "公开来源待核验",
            "source_name": source,
            "source_ref": source_ref,
            "source_document_id": str(item.get("document_id") or ""),
            "impact_window": EVENT_IMPACT_WINDOWS.get(event_type, EVENT_IMPACT_WINDOWS["general_news"]),
            "impact_direction": "结果待确认",
            "attention_level": attention_level,
            "monitoring_action": self._monitoring_action(event_type, delta_days),
            "auto_trade_rule": "事件结果公布前不因日历事件自动买入；临近高关注事件时需最新数据和人工确认。",
            "score_included": False,
            "evidence_kind": "公开信息日期",
        }

    def _rule_based_market_events(self, symbol: str, current: datetime, horizon_days: int) -> list[dict[str, Any]]:
        end_date = current.date().fromordinal(current.date().toordinal() + horizon_days)
        dates: list[tuple[date, str, str, str]] = []
        year, month = current.year, current.month
        for offset in range(5):
            y = year + (month - 1 + offset) // 12
            m = (month - 1 + offset) % 12 + 1
            third_friday = self._nth_weekday(y, m, calendar.FRIDAY, 3)
            fourth_wednesday = self._nth_weekday(y, m, calendar.WEDNESDAY, 4)
            dates.append((third_friday, "derivatives_settlement", "股指期货/期权交割观察日", "中金所具体合约与节假日安排"))
            if self._is_etf_symbol(symbol):
                dates.append((fourth_wednesday, "etf_option_expiry", "ETF期权行权观察日", "交易所具体合约与节假日安排"))
        events = [
            self._rule_event(symbol, event_date, event_type, title, confirm_note, current)
            for event_date, event_type, title, confirm_note in dates
            if current.date() <= event_date <= end_date
        ]
        for reporting in self._reporting_windows(current.date(), end_date):
            events.append(self._rule_event(
                symbol,
                reporting[1],
                "reporting_window",
                reporting[2],
                f"制度性披露窗口 {reporting[0].isoformat()} 至 {reporting[1].isoformat()}；个股预约日期仍需公告确认",
                current,
                starts_at=reporting[0],
            ))
        return events

    def _rule_event(
        self,
        symbol: str,
        event_date: date,
        event_type: str,
        title: str,
        confirm_note: str,
        current: datetime,
        starts_at: date | None = None,
    ) -> dict[str, Any]:
        delta_days = (event_date - current.date()).days
        return {
            "event_id": self._event_id(symbol or "market", event_type, event_date, title),
            "symbol": str(symbol or ""),
            "name": "全市场观察",
            "event_type": event_type,
            "event_type_cn": EVENT_TYPE_NAMES[event_type],
            "title": title,
            "starts_at": starts_at.isoformat() if starts_at else "",
            "scheduled_at": datetime.combine(event_date, time(15, 0)).isoformat(timespec="minutes"),
            "days_until": delta_days,
            "confirmation_status": "规则推算待确认",
            "source_name": "交易制度规则观察",
            "source_ref": "",
            "source_document_id": "",
            "confirmation_note": confirm_note,
            "impact_window": EVENT_IMPACT_WINDOWS[event_type],
            "impact_direction": "结果待确认",
            "attention_level": self._attention_level(event_type, delta_days),
            "monitoring_action": self._monitoring_action(event_type, delta_days),
            "auto_trade_rule": "不得依据推算日期自动买卖；交易前必须再次核对交易所正式日历。",
            "score_included": False,
            "evidence_kind": "制度规则推算",
        }

    def _deduplicate(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            key = str(event.get("event_id") or "")
            groups.setdefault(key, []).append(event)
        output: list[dict[str, Any]] = []
        for rows in groups.values():
            rows.sort(key=lambda row: (row.get("confirmation_status") == "公开来源已确认", bool(row.get("source_ref"))), reverse=True)
            best = dict(rows[0])
            best["duplicate_count"] = len(rows)
            best["duplicate_sources"] = sorted({str(row.get("source_name") or "") for row in rows if row.get("source_name")})
            best["duplicate_source_refs"] = list(dict.fromkeys(str(row.get("source_ref") or "") for row in rows if row.get("source_ref")))
            output.append(best)
        return output

    def _event_id(self, symbol: str, event_type: str, event_date: date, title: str) -> str:
        raw = f"{symbol}|{event_type}|{event_date.isoformat()}|{self._canonical_title(title)}"
        return "evt-" + hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:18]

    def _canonical_title(self, title: str) -> str:
        value = "".join(ch for ch in str(title or "").lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")
        for token in ("公告", "关于", "提示性", "通知"):
            value = value.replace(token, "")
        return value[:80]

    def _attention_level(self, event_type: str, days_until: int) -> str:
        high_types = {"financial_report", "regulatory", "holder_change", "derivatives_settlement", "etf_option_expiry"}
        if days_until <= 3 and event_type in high_types:
            return "高"
        if days_until <= 7 or event_type in {"shareholder_meeting", "market_macro", "reporting_window"}:
            return "中"
        return "低"

    def _monitoring_action(self, event_type: str, days_until: int) -> str:
        if days_until <= 1:
            return "提高到盘中/公告级检查；自动新增仓位需最新数据和人工确认"
        if days_until <= 7:
            return "每日复核公告、宏观日历与持仓风险"
        if event_type == "reporting_window":
            return "等待个股预约披露公告，不因窗口本身调整方向"
        return "加入观察清单，临近7日再提高检查频率"

    def _nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        weeks = calendar.monthcalendar(year, month)
        days = [week[weekday] for week in weeks if week[weekday]]
        return date(year, month, days[n - 1])

    def _reporting_windows(self, start: date, end: date) -> list[tuple[date, date, str]]:
        candidates: list[tuple[date, date, str]] = []
        for year in {start.year, end.year}:
            candidates.extend([
                (date(year, 1, 1), date(year, 4, 30), f"{year - 1}年年报集中披露窗口"),
                (date(year, 4, 1), date(year, 4, 30), f"{year}年一季报集中披露窗口"),
                (date(year, 7, 1), date(year, 8, 31), f"{year}年中报集中披露窗口"),
                (date(year, 10, 1), date(year, 10, 31), f"{year}年三季报集中披露窗口"),
            ])
        overlapping = [row for row in candidates if row[1] >= start and row[0] <= end]
        overlapping.sort(key=lambda row: (max(row[0], start), row[1]))
        return overlapping

    def _is_etf_symbol(self, symbol: str) -> bool:
        value = str(symbol or "")[-6:]
        return value.startswith(("15", "16", "50", "51", "52", "56", "58"))
