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
    region: str = ""
    authority_type: str = ""
    evidence_role: str = ""
    fetch_mode: str = "builtin"
    language: str = ""

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
    sources = [
        SourceDefinition("eastmoney", "东方财富公开行情/F10", "quote", supports=["quote", "kline", "fundamentals", "orderbook", "sector_flow"]),
        SourceDefinition("sina", "新浪财经公开行情", "quote", supports=["quote", "intraday"]),
        SourceDefinition(
            "sina_global_quote",
            "新浪全球指数与期货行情",
            "quote",
            url="https://finance.sina.com.cn/",
            supports=["global_index", "index_futures", "session_aware_sentiment"],
            note="按各市场交易时段和数据时间判断新鲜度；相关指数去重后仅作市场环境背景。",
        ),
        SourceDefinition("cninfo", "巨潮资讯公告", "news", supports=["official_announcement"]),
        SourceDefinition("exchange", "交易所公告", "news", supports=["official_announcement"]),
        SourceDefinition("f10", "公开 F10 数据", "fundamentals", supports=["fundamentals", "industry"]),
        SourceDefinition("cache", "本地最近成功缓存", "cache", supports=["quote", "kline", "snapshot"]),
        SourceDefinition("broker_disabled", "默认禁用券商适配器", "broker", supports=["status"]),
        SourceDefinition("jin10", "金十数据公开快讯", "news", url="https://www.jin10.com/", supports=["global_news", "macro_event", "commodity_event"]),
        SourceDefinition(
            "whitehouse_actions",
            "美国白宫总统行动公开源",
            "event",
            url="https://www.whitehouse.gov/presidential-actions/",
            supports=["official_policy_event", "global_news"],
        ),
        SourceDefinition(
            "us_federal_register",
            "美国联邦公报公开 API",
            "event",
            url="https://www.federalregister.gov/",
            supports=["official_policy_event", "regulatory_event", "global_news"],
        ),
        SourceDefinition("wallstreetcn", "华尔街见闻公开快讯", "news", url="https://wallstreetcn.com/", supports=["global_news", "macro_event"]),
        SourceDefinition("cls", "财联社公开电报", "news", url="https://www.cls.cn/", supports=["global_news", "company_event"]),
        SourceDefinition("sina_news", "新浪财经公开快讯", "news", url="https://finance.sina.com.cn/", supports=["global_news", "company_event"]),
        SourceDefinition("reuters", "路透社授权数据", "news", supports=["global_news", "company_event"], enabled=False, note="需要用户自行配置合法授权数据接口"),
        SourceDefinition("bloomberg", "彭博授权数据", "news", supports=["global_news", "market_event"], enabled=False, note="需要用户自行配置合法授权数据接口"),
        SourceDefinition("sse_ipo", "上海证券交易所发行上市公开信息", "event", url="https://www.sse.com.cn/", supports=["ipo_event", "listing_event"]),
        SourceDefinition("szse_ipo", "深圳证券交易所发行上市公开信息", "event", url="https://www.szse.cn/", supports=["ipo_event", "listing_event"]),
        SourceDefinition("macro_official", "官方宏观数据发布机构", "event", supports=["macro_event", "calendar_event"]),
    ]
    sources.extend(_official_source_catalog())
    return sources


def _official_source_catalog() -> list[SourceDefinition]:
    """Primary-source catalogue used for verification and traceability.

    ``catalog_only`` means the source is registered for structured imports,
    provenance and link validation but is not silently scraped on every page
    load.  Background collectors may opt in source by source and must retain
    the publication URL and timestamp.
    """

    def official(
        source_id: str,
        name: str,
        region: str,
        url: str,
        supports: list[str],
        authority_type: str,
        *,
        fetch_mode: str = "catalog_only",
        language: str = "",
        note: str = "",
    ) -> SourceDefinition:
        return SourceDefinition(
            source_id,
            name,
            "official_event",
            url=url,
            supports=supports,
            note=note or "官方原文用于确认；快讯只负责早期发现，不能替代该来源。",
            region=region,
            authority_type=authority_type,
            evidence_role="primary_confirmation",
            fetch_mode=fetch_mode,
            language=language,
        )

    return [
        official("cn_gov", "中国政府网", "中国", "https://www.gov.cn/", ["policy_event", "calendar_event"], "government", language="zh-CN"),
        official("cn_pbc", "中国人民银行", "中国", "https://www.pbc.gov.cn/", ["central_bank", "liquidity_event"], "central_bank", language="zh-CN"),
        official("cn_nbs", "国家统计局", "中国", "https://www.stats.gov.cn/", ["economic_data", "calendar_event"], "statistics", language="zh-CN"),
        official("cn_ndrc", "国家发展改革委", "中国", "https://www.ndrc.gov.cn/", ["industry_policy", "price_policy"], "ministry", language="zh-CN"),
        official("cn_miit", "工业和信息化部", "中国", "https://www.miit.gov.cn/", ["industry_policy", "technology_policy"], "ministry", language="zh-CN"),
        official("cn_mofcom", "商务部", "中国", "https://www.mofcom.gov.cn/", ["trade_policy", "sanction_event"], "ministry", language="zh-CN"),
        official("cn_customs", "海关总署", "中国", "http://www.customs.gov.cn/", ["trade_data", "customs_policy"], "customs", language="zh-CN"),
        official("cn_csrc", "中国证监会", "中国", "https://www.csrc.gov.cn/", ["market_regulation", "enforcement_event"], "regulator", language="zh-CN"),
        official("us_fed", "美国联邦储备委员会", "美国", "https://www.federalreserve.gov/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("us_bls", "美国劳工统计局", "美国", "https://www.bls.gov/", ["economic_data", "calendar_event"], "statistics", language="en"),
        official("us_bea", "美国经济分析局", "美国", "https://www.bea.gov/", ["economic_data", "calendar_event"], "statistics", language="en"),
        official("us_sec", "美国证券交易委员会", "美国", "https://www.sec.gov/", ["market_regulation", "company_filing"], "regulator", language="en"),
        official("eu_commission", "欧盟委员会", "欧盟", "https://commission.europa.eu/news-and-media_en", ["policy_event", "trade_policy", "sanction_event"], "government", language="en"),
        official("eu_ecb", "欧洲中央银行", "欧盟", "https://www.ecb.europa.eu/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("eu_eurostat", "欧盟统计局", "欧盟", "https://ec.europa.eu/eurostat/", ["economic_data", "calendar_event"], "statistics", language="en"),
        official("uk_gov", "英国政府", "英国", "https://www.gov.uk/search/news-and-communications", ["policy_event", "trade_policy"], "government", language="en"),
        official("uk_boe", "英格兰银行", "英国", "https://www.bankofengland.co.uk/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("jp_boj", "日本银行", "日本", "https://www.boj.or.jp/en/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("jp_meti", "日本经济产业省", "日本", "https://www.meti.go.jp/english/", ["industry_policy", "trade_policy"], "ministry", language="en"),
        official("kr_bok", "韩国银行", "韩国", "https://www.bok.or.kr/eng/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("in_rbi", "印度储备银行", "印度", "https://www.rbi.org.in/", ["central_bank", "market_regulation"], "central_bank", language="en"),
        official("in_pib", "印度政府新闻信息局", "印度", "https://pib.gov.in/", ["policy_event", "industry_policy"], "government", language="en"),
        official("sg_mas", "新加坡金融管理局", "新加坡", "https://www.mas.gov.sg/news", ["central_bank", "market_regulation"], "central_bank", language="en"),
        official("ca_boc", "加拿大银行", "加拿大", "https://www.bankofcanada.ca/press/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("ca_stats", "加拿大统计局", "加拿大", "https://www.statcan.gc.ca/en/start", ["economic_data", "calendar_event"], "statistics", language="en"),
        official("au_rba", "澳大利亚储备银行", "澳大利亚", "https://www.rba.gov.au/media-releases/", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("au_abs", "澳大利亚统计局", "澳大利亚", "https://www.abs.gov.au/media-centre/media-releases", ["economic_data", "calendar_event"], "statistics", language="en"),
        official("br_bcb", "巴西中央银行", "巴西", "https://www.bcb.gov.br/en", ["central_bank", "market_regulation"], "central_bank", language="en"),
        official("mx_banxico", "墨西哥银行", "墨西哥", "https://www.banxico.org.mx/indexen.html", ["central_bank", "calendar_event"], "central_bank", language="en"),
        official("za_sarb", "南非储备银行", "南非", "https://www.resbank.co.za/en/home/publications/statements", ["central_bank", "market_regulation"], "central_bank", language="en"),
        official("ru_government", "俄罗斯政府", "俄罗斯", "http://government.ru/en/news/", ["policy_event", "trade_policy", "energy_policy"], "government", language="en"),
        official("ru_cbr", "俄罗斯中央银行", "俄罗斯", "https://www.cbr.ru/eng/", ["central_bank", "market_regulation"], "central_bank", language="en"),
        official("imf", "国际货币基金组织", "国际组织", "https://www.imf.org/en/News", ["global_macro", "economic_outlook"], "international_organization", language="en"),
        official("world_bank", "世界银行", "国际组织", "https://www.worldbank.org/en/news", ["global_macro", "economic_outlook"], "international_organization", language="en"),
        official("wto", "世界贸易组织", "国际组织", "https://www.wto.org/english/news_e/news_e.htm", ["trade_policy", "trade_dispute"], "international_organization", language="en"),
        official("oecd", "经济合作与发展组织", "国际组织", "https://www.oecd.org/en/about/news.html", ["global_macro", "economic_outlook"], "international_organization", language="en"),
        official("unctad", "联合国贸易和发展会议", "国际组织", "https://unctad.org/news", ["trade_policy", "global_trade"], "international_organization", language="en"),
        official("fao", "联合国粮农组织", "国际组织", "https://www.fao.org/newsroom/en", ["agriculture", "food_price"], "international_organization", language="en"),
        official("bis", "国际清算银行", "国际组织", "https://www.bis.org/", ["global_macro", "financial_stability"], "international_organization", language="en"),
        official("iea", "国际能源署", "国际组织", "https://www.iea.org/news", ["energy_policy", "energy_data"], "international_organization", language="en"),
        official("opec", "石油输出国组织", "国际组织", "https://www.opec.org/", ["energy_policy", "oil_market"], "international_organization", language="en"),
    ]
