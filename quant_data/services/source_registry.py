from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class SourceSpec:
    key: str
    name: str
    tier: str
    category: str
    role: str
    use_for_score: bool
    credibility: int
    notes: str = ""


class SourceRegistryService:
    """WordSource V1 信息源注册表。

    目标不是“多抓一点网页”，而是把源分层、证据角色、是否计分说清楚。
    搜索引擎结果页被永久禁用；社区只做情绪/传闻，不当公司事实。
    """

    def __init__(self) -> None:
        self.sources: list[SourceSpec] = [
            SourceSpec("cninfo", "巨潮资讯", "P0", "公司公告", "官方披露/财报/股东大会/监管问询", True, 94),
            SourceSpec("sse", "上交所", "P0", "交易所公告", "监管披露/上市公司公告", True, 95),
            SourceSpec("szse", "深交所", "P0", "交易所公告", "监管披露/上市公司公告", True, 95),
            SourceSpec("bse", "北交所", "P0", "交易所公告", "监管披露/上市公司公告", True, 95),
            SourceSpec("csrc", "证监会", "P0", "监管政策", "监管政策/处罚/市场制度", True, 96),
            SourceSpec("pbc", "央行", "P0", "宏观流动性", "利率/MLF/逆回购/降准", True, 96),
            SourceSpec("stats", "国家统计局", "P0", "宏观数据", "GDP/CPI/PPI/PMI等宏观数据", True, 95),
            SourceSpec("ndrc", "发改委", "P0", "产业政策", "产业规划/价格/投资政策", True, 94),
            SourceSpec("miit", "工信部", "P0", "产业政策", "制造业/新能源/半导体/通信政策", True, 94),
            SourceSpec("eastmoney_f10", "东方财富F10", "P2", "公司资料", "公司资料/公告索引/行情补充", True, 76),
            SourceSpec("eastmoney_flash", "东方财富快讯", "P1", "实时快讯", "市场/行业/公司实时消息", True, 82),
            SourceSpec("cls", "财联社", "P1", "专业实时源", "实时快讯/政策/行业/公司事件", True, 84),
            SourceSpec("wallstreetcn", "华尔街见闻", "P1", "宏观国际", "全球宏观/商品/央行", True, 80),
            SourceSpec("jin10", "金十数据", "P1", "宏观商品", "全球宏观/商品/外汇", True, 80),
            SourceSpec("stcn", "证券时报", "P2", "财经媒体", "新闻/研报转载/市场评论", True, 72),
            SourceSpec("cs", "中证网", "P2", "财经媒体", "新闻/行业/公司", True, 72),
            SourceSpec("cnstock", "上海证券报", "P2", "财经媒体", "政策/市场/公司新闻", True, 72),
            SourceSpec("sina", "新浪财经", "P2", "财经门户", "个股新闻/行情/F10补充", True, 66),
            SourceSpec("ths", "同花顺", "P2", "财经门户", "个股新闻/行情/F10补充", True, 66),
            SourceSpec("broker_report", "券商研报", "P2", "研究报告", "评级/目标价/盈利预测/风险提示", True, 78),
            SourceSpec("guba", "东方财富股吧", "P3", "社区舆情", "热度/情绪/分歧/传闻风险", False, 45),
            SourceSpec("xueqiu", "雪球", "P3", "社区舆情", "热度/情绪/分歧/传闻风险", False, 48),
            SourceSpec("weibo", "微博/公众号/知乎", "P3", "社交媒体", "观点热度/情绪，不作为事实源", False, 38),
        ]

    def all(self) -> list[dict]:
        return [asdict(s) for s in self.sources]

    def by_category(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for s in self.sources:
            out.setdefault(s.category, []).append(asdict(s))
        return out

    def coverage_matrix(self) -> dict:
        categories = ["宏观经济", "政策面", "行业消息", "公司消息", "市场资金面", "国际消息", "研报", "舆情"]
        mapping = {
            "宏观经济": ["stats", "pbc", "jin10", "wallstreetcn"],
            "政策面": ["csrc", "ndrc", "miit", "sse", "szse"],
            "行业消息": ["cls", "stcn", "cs", "cnstock", "eastmoney_flash"],
            "公司消息": ["cninfo", "eastmoney_f10", "sina", "ths"],
            "市场资金面": ["eastmoney_flash", "cls"],
            "国际消息": ["jin10", "wallstreetcn"],
            "研报": ["broker_report", "eastmoney_f10"],
            "舆情": ["guba", "xueqiu", "weibo"],
        }
        return {cat: [asdict(s) for s in self.sources if s.key in mapping[cat]] for cat in categories}

    def disabled_sources(self) -> list[dict]:
        return [
            {"key": "baidu_search", "name": "百度搜索结果页", "reason": "搜索结果页不是新闻证据，不抓取、不计分、不展示"},
            {"key": "360_search", "name": "360搜索结果页", "reason": "搜索结果页不是新闻证据，不抓取、不计分、不展示"},
            {"key": "sogou_search", "name": "搜狗搜索结果页", "reason": "搜索结果页不是新闻证据，不抓取、不计分、不展示"},
        ]

    def plan_for_target(self, target_effective_items: int = 120) -> dict:
        target_effective_items = max(20, min(int(target_effective_items or 120), 300))
        return {
            "target_effective_items": target_effective_items,
            "stop_rule": "按清洗后有效证据数停止，不按原始抓取数停止；低于目标时继续翻公告分页并补专业源。",
            "primary_order": ["P0官方公告", "P1专业实时源", "P2财经门户详情页", "P3社区舆情统计"],
            "min_valid_by_category": {
                "公司公告": max(8, target_effective_items // 8),
                "公司新闻": max(8, target_effective_items // 10),
                "行业/政策": max(6, target_effective_items // 12),
                "宏观/国际": max(6, target_effective_items // 12),
                "资金/市场": max(6, target_effective_items // 12),
                "舆情": max(6, target_effective_items // 15),
            },
            "disabled": self.disabled_sources(),
        }
