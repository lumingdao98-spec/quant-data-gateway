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
    "macro_release": "宏观数据公布",
    "central_bank_decision": "央行利率/政策会议",
    "employment_release": "就业/非农数据公布",
    "lockup_expiry": "限售股解禁",
    "index_rebalance": "指数调样/再平衡",
    "shareholder_reduction": "股东减持计划",
    "buyback": "股份回购计划",
    "placement": "定增/配股/再融资",
    "commodity_supply": "大宗商品供需事件",
    "fx_rate_shock": "汇率/利率冲击观察",
    "geopolitical": "地缘政治事件",
    "export_control": "出口管制/关税/制裁",
    "shipping_logistics": "航运/物流扰动",
    "cybersecurity": "网络安全/数据风险",
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
    "macro_release": "公布前1日至公布后1日",
    "central_bank_decision": "会议前2日至声明后1日",
    "employment_release": "公布前1日至公布后1日",
    "lockup_expiry": "解禁前5日至后3日",
    "index_rebalance": "公告日至生效后2日",
    "shareholder_reduction": "计划公告日至执行结束",
    "buyback": "计划公告日至执行结束",
    "placement": "预案公告至发行结果披露",
    "commodity_supply": "事项前后3个交易日",
    "fx_rate_shock": "公布/异动前后2个交易日",
    "geopolitical": "事件发展期持续观察",
    "export_control": "公布日至落地后5个交易日",
    "shipping_logistics": "扰动发生至运价/供给恢复",
    "cybersecurity": "披露日至处置结果确认",
    "derivatives_settlement": "当周三至下周一",
    "etf_option_expiry": "行权日前2日至后1日",
    "reporting_window": "窗口期内持续观察",
    "general_news": "事件日前后2日",
}

EVENT_TRANSMISSION_CHANNELS = {
    "macro_release": ["利率预期", "汇率", "风险偏好", "行业景气预期"],
    "central_bank_decision": ["无风险利率", "美元/人民币汇率", "全球流动性", "成长股估值"],
    "employment_release": ["海外利率预期", "美元指数", "全球科技估值", "外资风险偏好"],
    "lockup_expiry": ["潜在供给", "流动性", "个股波动"],
    "index_rebalance": ["被动资金调仓", "尾盘成交", "短期流动性"],
    "shareholder_reduction": ["潜在供给", "治理预期", "个股风险偏好"],
    "buyback": ["公司资本动作", "潜在需求", "治理预期"],
    "placement": ["股本摊薄", "融资用途", "潜在供给"],
    "commodity_supply": ["原材料成本", "产品价格", "产业链利润再分配"],
    "fx_rate_shock": ["外资流向", "进口成本", "出口竞争力", "估值折现率"],
    "geopolitical": ["能源/运价", "供应链", "避险情绪", "风险溢价"],
    "export_control": ["供应链可得性", "国产替代", "订单预期", "风险溢价"],
    "shipping_logistics": ["运价", "交付周期", "库存", "进出口成本"],
    "cybersecurity": ["运营连续性", "监管风险", "修复成本", "声誉风险"],
    "derivatives_settlement": ["期现基差", "套保/移仓", "尾盘成交", "短期波动"],
    "etf_option_expiry": ["期权行权", "做市对冲", "ETF申赎", "尾盘流动性"],
    "reporting_window": ["业绩预期", "估值修正", "行业比较", "个股波动"],
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
        title = str(item.get("title") or "未来事项")
        event_type = self._normalize_event_type(str(item.get("event_type") or "general_news"), title)
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
            "transmission_channels": EVENT_TRANSMISSION_CHANNELS.get(event_type, []),
            "event_scope": "全球/市场环境" if event_type in {"macro_release", "central_bank_decision", "employment_release", "commodity_supply", "fx_rate_shock", "geopolitical", "export_control", "shipping_logistics"} else "个股/公司事项",
            "risk_gate": self._risk_gate(event_type, delta_days),
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
            "transmission_channels": EVENT_TRANSMISSION_CHANNELS.get(event_type, []),
            "event_scope": "全市场制度事件",
            "risk_gate": self._risk_gate(event_type, delta_days),
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
        high_types = {
            "financial_report", "regulatory", "holder_change", "derivatives_settlement", "etf_option_expiry",
            "central_bank_decision", "employment_release", "lockup_expiry", "index_rebalance",
            "shareholder_reduction", "geopolitical", "export_control", "cybersecurity",
        }
        if days_until <= 3 and event_type in high_types:
            return "高"
        if days_until <= 7 or event_type in {
            "shareholder_meeting", "market_macro", "macro_release", "commodity_supply",
            "fx_rate_shock", "shipping_logistics", "reporting_window",
        }:
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

    def _risk_gate(self, event_type: str, days_until: int) -> str:
        if days_until <= 1 and event_type in {
            "financial_report", "central_bank_decision", "employment_release", "lockup_expiry",
            "shareholder_reduction", "geopolitical", "export_control", "cybersecurity",
        }:
            return "自动新增仓位暂停，等待结果/公告并人工复核"
        if days_until <= 3:
            return "提高数据新鲜度要求；放大仓位或实盘委托需人工确认"
        return "仅观察，不预判方向、不直接改变当前评分"

    def _normalize_event_type(self, event_type: str, title: str) -> str:
        value = str(event_type or "general_news")
        if value not in {"general_news", "market_macro"}:
            return value
        text = str(title or "")
        keyword_groups = (
            ("employment_release", ("非农", "就业数据", "失业率", "初请失业金")),
            ("central_bank_decision", ("FOMC", "美联储", "央行会议", "利率决议", "降息", "加息")),
            ("macro_release", ("CPI", "PPI", "PMI", "GDP", "通胀数据", "社会融资", "社融", "M2")),
            ("lockup_expiry", ("限售股解禁", "解禁上市")),
            ("index_rebalance", ("指数调样", "指数调整", "调入指数", "调出指数", "再平衡")),
            ("shareholder_reduction", ("减持计划", "拟减持")),
            ("buyback", ("股份回购", "回购计划")),
            ("placement", ("定增", "配股", "再融资")),
            ("export_control", ("出口管制", "加征关税", "制裁清单", "实体清单")),
            ("geopolitical", ("地缘冲突", "军事冲突", "停火谈判", "战争")),
            ("shipping_logistics", ("红海航运", "港口罢工", "航运中断", "物流中断")),
            ("cybersecurity", ("网络攻击", "数据泄露", "网络安全事件")),
            ("fx_rate_shock", ("美元指数", "人民币汇率", "外汇干预", "汇率异动")),
            ("commodity_supply", ("原油供应", "天然气供应", "铜供应", "稀土供应", "减产会议")),
        )
        lower = text.lower()
        for candidate, keywords in keyword_groups:
            if any(keyword.lower() in lower for keyword in keywords):
                return candidate
        return value

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
