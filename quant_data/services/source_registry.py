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
    url: str = ""
    region: str = ""
    fetch_mode: str = "builtin"


class SourceRegistryService:
    """WordSource V2 信息源注册表。

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
            SourceSpec("eastmoney_sector_flow", "东方财富公开板块资金", "P2", "市场资金面", "行业/概念板块净流、涨跌与宽度；非Level-2账户识别", True, 74),
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
        self.sources.extend(self._global_official_sources())

    @staticmethod
    def _global_official_sources() -> list[SourceSpec]:
        def source(key: str, name: str, category: str, role: str, url: str, region: str) -> SourceSpec:
            return SourceSpec(
                key,
                name,
                "P0",
                category,
                role,
                True,
                96,
                "官方原文用于确认和溯源；catalog_only 表示不在每次页面加载时全量抓取。",
                url,
                region,
                "catalog_only",
            )

        return [
            source("cn_gov", "中国政府网", "国内政策", "国务院政策与已确认会议", "https://www.gov.cn/", "中国"),
            source("cn_mofcom", "商务部", "贸易政策", "进出口、制裁与贸易救济", "https://www.mofcom.gov.cn/", "中国"),
            source("cn_customs", "海关总署", "贸易数据", "进出口统计与海关政策", "http://www.customs.gov.cn/", "中国"),
            source("us_whitehouse", "美国白宫", "国际政策", "总统行动与行政政策", "https://www.whitehouse.gov/presidential-actions/", "美国"),
            source("us_federal_register", "美国联邦公报", "国际监管", "最终规则、拟议规则与生效日", "https://www.federalregister.gov/", "美国"),
            source("us_fed", "美联储", "海外央行", "利率决议、会议纪要与金融稳定", "https://www.federalreserve.gov/", "美国"),
            source("us_bls", "美国劳工统计局", "海外宏观", "非农、CPI、PPI 等定时数据", "https://www.bls.gov/", "美国"),
            source("eu_commission", "欧盟委员会", "国际政策", "贸易、产业、制裁和竞争政策", "https://commission.europa.eu/news-and-media_en", "欧盟"),
            source("eu_ecb", "欧洲中央银行", "海外央行", "利率决议与金融稳定", "https://www.ecb.europa.eu/", "欧盟"),
            source("eu_eurostat", "欧盟统计局", "海外宏观", "通胀、就业、产业和贸易数据", "https://ec.europa.eu/eurostat/", "欧盟"),
            source("uk_gov", "英国政府", "国际政策", "政策、监管和贸易公告", "https://www.gov.uk/search/news-and-communications", "英国"),
            source("uk_boe", "英格兰银行", "海外央行", "利率决议与金融稳定", "https://www.bankofengland.co.uk/", "英国"),
            source("jp_boj", "日本银行", "海外央行", "利率、汇率和金融稳定", "https://www.boj.or.jp/en/", "日本"),
            source("jp_meti", "日本经济产业省", "国际产业", "半导体、能源和贸易政策", "https://www.meti.go.jp/english/", "日本"),
            source("kr_bok", "韩国银行", "海外央行", "利率和宏观数据", "https://www.bok.or.kr/eng/", "韩国"),
            source("in_rbi", "印度储备银行", "海外央行", "利率、流动性和金融市场规则", "https://www.rbi.org.in/", "印度"),
            source("in_pib", "印度政府新闻信息局", "国际政策", "产业、贸易和政府政策", "https://pib.gov.in/", "印度"),
            source("sg_mas", "新加坡金融管理局", "海外央行", "货币政策和金融监管", "https://www.mas.gov.sg/news", "新加坡"),
            source("ca_boc", "加拿大银行", "海外央行", "利率决议和货币政策", "https://www.bankofcanada.ca/press/", "加拿大"),
            source("ca_stats", "加拿大统计局", "海外宏观", "就业、通胀、产业和贸易数据", "https://www.statcan.gc.ca/en/start", "加拿大"),
            source("au_rba", "澳大利亚储备银行", "海外央行", "利率决议和金融稳定", "https://www.rba.gov.au/media-releases/", "澳大利亚"),
            source("au_abs", "澳大利亚统计局", "海外宏观", "就业、通胀和商品经济数据", "https://www.abs.gov.au/media-centre/media-releases", "澳大利亚"),
            source("br_bcb", "巴西中央银行", "海外央行", "利率、汇率和金融市场规则", "https://www.bcb.gov.br/en", "巴西"),
            source("mx_banxico", "墨西哥银行", "海外央行", "利率和宏观数据", "https://www.banxico.org.mx/indexen.html", "墨西哥"),
            source("za_sarb", "南非储备银行", "海外央行", "利率和金融稳定", "https://www.resbank.co.za/en/home/publications/statements", "南非"),
            source("ru_government", "俄罗斯政府", "国际政策", "能源、贸易和政府决定", "http://government.ru/en/news/", "俄罗斯"),
            source("ru_cbr", "俄罗斯中央银行", "海外央行", "利率、汇率与金融市场规则", "https://www.cbr.ru/eng/", "俄罗斯"),
            source("imf", "国际货币基金组织", "国际组织", "全球经济展望与国别风险", "https://www.imf.org/en/News", "国际组织"),
            source("world_bank", "世界银行", "国际组织", "全球增长、产业和发展数据", "https://www.worldbank.org/en/news", "国际组织"),
            source("wto", "世界贸易组织", "国际组织", "贸易政策、争端与关税", "https://www.wto.org/english/news_e/news_e.htm", "国际组织"),
            source("oecd", "经济合作与发展组织", "国际组织", "全球景气、领先指标和国别展望", "https://www.oecd.org/en/about/news.html", "国际组织"),
            source("unctad", "联合国贸易和发展会议", "国际组织", "全球贸易、航运和投资", "https://unctad.org/news", "国际组织"),
            source("fao", "联合国粮农组织", "国际组织", "粮食、农业和食品价格", "https://www.fao.org/newsroom/en", "国际组织"),
            source("bis", "国际清算银行", "国际组织", "全球流动性和金融稳定", "https://www.bis.org/", "国际组织"),
            source("iea", "国际能源署", "国际组织", "能源供需与政策", "https://www.iea.org/news", "国际组织"),
            source("opec", "石油输出国组织", "国际组织", "原油供给与会议决定", "https://www.opec.org/", "国际组织"),
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
        global_official_keys = [
            item.key
            for item in self.sources
            if item.fetch_mode == "catalog_only" and item.region not in {"", "中国"}
        ]
        mapping = {
            "宏观经济": ["stats", "pbc", "jin10", "wallstreetcn"],
            "政策面": ["csrc", "ndrc", "miit", "sse", "szse"],
            "行业消息": ["cls", "stcn", "cs", "cnstock", "eastmoney_flash"],
            "公司消息": ["cninfo", "eastmoney_f10", "sina", "ths"],
            "市场资金面": ["eastmoney_flash", "eastmoney_sector_flow", "cls"],
            "国际消息": ["jin10", "wallstreetcn", *global_official_keys],
            "研报": ["broker_report", "eastmoney_f10"],
            "舆情": ["guba", "xueqiu", "weibo"],
        }
        return {cat: [asdict(s) for s in self.sources if s.key in mapping[cat]] for cat in categories}

    def disabled_sources(self) -> list[dict]:
        # V3.17 要求搜索结果页“不注册、不调用、不展示、不打印禁用日志”。
        # 因此这里保留兼容接口但返回空集合，不再把搜索页作为任何源清单的一员。
        return []

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
