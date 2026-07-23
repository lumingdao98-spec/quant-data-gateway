from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .data_contracts import assert_truthful_source


@dataclass(slots=True)
class SourceDefinition:
    source_id: str
    source_name: str
    category: str
    url: str = ""
    supports: list[str] = field(default_factory=list)
    enabled: bool = True
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceRegistry:
    def __init__(self, sources: list[SourceDefinition] | None = None) -> None:
        self.sources = {s.source_id: s for s in (sources or _default_sources())}

    def list(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in self.sources.values()]

    def get(self, source_id: str) -> SourceDefinition | None:
        return self.sources.get(source_id)

    def validate(self, source_id: str, source_url: str = "", source_ref: str = "") -> dict[str, Any]:
        truth = assert_truthful_source(source_id, source_url, source_ref)
        definition = self.get(source_id)
        return {
            "accepted": truth.accepted and bool(definition and definition.enabled),
            "source": definition.to_dict() if definition else None,
            "reasons": truth.reasons + ([] if definition else ["数据源未注册"]) + ([] if not definition or definition.enabled else ["数据源已禁用"]),
        }


def default_source_registry() -> SourceRegistry:
    return SourceRegistry()


def _default_sources() -> list[SourceDefinition]:
    return [
        SourceDefinition("eastmoney", "东方财富公开行情/F10", "quote", supports=["quote", "kline", "fundamentals", "orderbook", "sector_flow"]),
        SourceDefinition("sina", "新浪财经公开行情", "quote", supports=["quote", "intraday"]),
        SourceDefinition("cninfo", "巨潮资讯公告", "news", supports=["official_announcement"]),
        SourceDefinition("exchange", "交易所公告", "news", supports=["official_announcement"]),
        SourceDefinition("f10", "公开 F10 数据", "fundamentals", supports=["fundamentals", "industry"]),
        SourceDefinition("cache", "本地最近成功缓存", "cache", supports=["quote", "kline", "snapshot"]),
        SourceDefinition("broker_disabled", "默认禁用券商适配器", "broker", supports=["status"]),
        SourceDefinition("jin10", "金十数据公开快讯", "news", url="https://www.jin10.com/", supports=["global_news", "macro_event", "commodity_event"]),
        SourceDefinition("wallstreetcn", "华尔街见闻公开快讯", "news", url="https://wallstreetcn.com/", supports=["global_news", "macro_event"]),
        SourceDefinition("cls", "财联社公开电报", "news", url="https://www.cls.cn/", supports=["global_news", "company_event"]),
        SourceDefinition("sina_news", "新浪财经公开快讯", "news", url="https://finance.sina.com.cn/", supports=["global_news", "company_event"]),
        SourceDefinition("reuters", "路透社授权数据", "news", supports=["global_news", "company_event"], enabled=False, note="需要用户自行配置合法授权数据接口"),
        SourceDefinition("bloomberg", "彭博授权数据", "news", supports=["global_news", "market_event"], enabled=False, note="需要用户自行配置合法授权数据接口"),
        SourceDefinition("sse_ipo", "上海证券交易所发行上市公开信息", "event", url="https://www.sse.com.cn/", supports=["ipo_event", "listing_event"]),
        SourceDefinition("szse_ipo", "深圳证券交易所发行上市公开信息", "event", url="https://www.szse.cn/", supports=["ipo_event", "listing_event"]),
        SourceDefinition("macro_official", "官方宏观数据发布机构", "event", supports=["macro_event", "calendar_event"]),
    ]
