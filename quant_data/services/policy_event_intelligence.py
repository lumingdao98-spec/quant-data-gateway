from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse


EVENT_RULES: tuple[dict[str, Any], ...] = (
    {
        "key": "sanction_or_blacklist",
        "label_cn": "制裁或清单限制",
        "direction": "negative",
        "severity": "high",
        "terms": (
            "制裁", "实体清单", "黑名单", "禁运", "冻结资产", "冻结的", "sanction",
            "entity list", "blacklist", "embargo", "blocked persons", "frozen assets",
        ),
    },
    {
        "key": "export_or_import_restriction",
        "label_cn": "进出口或市场准入限制",
        "direction": "negative",
        "severity": "high",
        "terms": (
            "出口管制", "出口限制", "进口限制", "进口禁令", "禁止进口", "限制进口", "市场准入限制",
            "采购限制", "禁令", "export control", "import restriction", "import ban",
            "procurement restriction", "prohibit", "restrict", "banning", "ban on foreign",
            "ban targeting", "working on ban",
        ),
    },
    {
        "key": "security_review",
        "label_cn": "国家安全或供应链审查",
        "direction": "negative",
        "severity": "high",
        "terms": (
            "国家紧急状态", "国家安全审查", "供应链安全", "安全风险", "外国设备",
            "national emergency", "national security review", "supply chain security",
            "security risk", "foreign-produced equipment", "covered foreign entity",
        ),
    },
    {
        "key": "regulatory_investigation",
        "label_cn": "监管调查或执法",
        "direction": "negative",
        "severity": "medium",
        "terms": (
            "立案调查", "反倾销调查", "反补贴调查", "监管调查", "召回", "处罚",
            "列入管制", "药物列入", "适航指令", "investigation", "anti-dumping", "countervailing",
            "recall", "enforcement action", "controlled substances", "placement of", "schedule iv",
            "airworthiness directive", "airworthiness directives", "notice of institution",
        ),
    },
    {
        "key": "tariff_change",
        "label_cn": "关税调整",
        "direction": "mixed",
        "severity": "medium",
        "terms": ("关税", "加征税", "tariff", "duties on", "duty rate"),
    },
    {
        "key": "support_or_subsidy",
        "label_cn": "产业支持或补贴",
        "direction": "positive",
        "severity": "medium",
        "terms": (
            "补贴", "财政支持", "税收抵免", "支持发展", "扩大采购", "补贴获批", "专项资金获批",
            "subsidy", "tax credit", "financial support", "grant program", "funding approved",
        ),
    },
    {
        "key": "monetary_policy",
        "label_cn": "货币与利率政策",
        "direction": "mixed",
        "severity": "medium",
        "terms": (
            "降息", "加息", "降准", "利率决议", "fomc", "rate cut", "rate hike",
            "interest rate decision", "quantitative tightening", "quantitative easing",
        ),
    },
    {
        "key": "earnings_or_guidance",
        "label_cn": "业绩或经营指引",
        "direction": "mixed",
        "severity": "medium",
        "terms": (
            "业绩预告", "业绩快报", "净利润", "营收", "经营指引", "盈利预警",
            "earnings", "profit warning", "revenue guidance", "financial results",
        ),
    },
    {
        "key": "operational_disruption",
        "label_cn": "停产或供应中断",
        "direction": "negative",
        "severity": "medium",
        "terms": (
            "停产", "停止运营", "暂停运营", "供应中断", "运输中断", "shutdown",
            "项目延期", "项目取消", "项目可能被拖延", "建设受阻", "建设约束",
            "halted operations", "stopped operations", "supply disruption", "production halt",
            "project delay", "projects delayed", "project cancelled", "projects cancelled",
            "delayed or cancelled", "construction constraint",
        ),
    },
    {
        "key": "economic_data_release",
        "label_cn": "宏观经济数据发布",
        "direction": "mixed",
        "severity": "medium",
        "terms": (
            "非农", "就业数据", "失业率", "通胀率", "居民消费价格", "生产者价格",
            "采购经理指数", "工业产出", "工厂产出", "零售销售", "国内生产总值", "消费者信心",
            "新增就业", "职位空缺", "初请失业金", "贸易帐", "进出口数据",
            "nonfarm", "unemployment rate", "consumer price index", "producer price index",
            "pmi", "industrial production", "factory output", "retail sales", "gross domestic product",
            "consumer confidence", "job openings", "jobless claims", "trade balance",
        ),
    },
    {
        "key": "legislation_or_policy_schedule",
        "label_cn": "法规、会议或政策日程",
        "direction": "mixed",
        "severity": "medium",
        "terms": (
            "法案", "听证会", "监管会议", "政策会议", "行业会议", "审议", "表决",
            "公开会议", "咨询委员会会议", "bill", "hearing", "regulatory meeting", "policy meeting",
            "public meeting", "advisory committee meeting", "committee vote",
        ),
    },
    {
        "key": "labor_or_logistics_disruption",
        "label_cn": "罢工或物流中断",
        "direction": "negative",
        "severity": "medium",
        "terms": (
            "罢工", "港口停摆", "航运中断", "铁路中断", "劳资谈判破裂",
            "strike", "walkout", "port shutdown", "rail disruption", "logistics disruption",
        ),
    },
    {
        "key": "cyber_or_infrastructure_incident",
        "label_cn": "网络安全或基础设施事故",
        "direction": "negative",
        "severity": "high",
        "terms": (
            "网络攻击", "数据泄露", "系统瘫痪", "大面积停电", "基础设施事故",
            "cyberattack", "data breach", "system outage", "grid outage", "infrastructure incident",
        ),
    },
    {
        "key": "natural_disaster_or_extreme_weather",
        "label_cn": "自然灾害或极端天气",
        "direction": "negative",
        "severity": "medium",
        "terms": (
            "台风", "飓风", "地震", "洪水", "山火", "极端高温", "极端寒潮", "干旱",
            "typhoon", "hurricane", "earthquake", "flood", "wildfire", "extreme heat", "drought",
        ),
    },
    {
        "key": "geopolitical_disruption",
        "label_cn": "地缘冲突或供应中断",
        "direction": "negative",
        "severity": "high",
        "terms": (
            "军事冲突", "军事行动", "空袭", "袭击", "封锁", "断供", "停运", "战争", "驱逐",
            "strike on", "military conflict", "military operation", "blockade", "shipping disruption",
        ),
    },
)


TOPIC_RULES: tuple[dict[str, Any], ...] = (
    {
        "key": "power_grid_inverter_storage",
        "products": ["并网逆变器", "储能系统", "大容量电力系统设备"],
        "industries": ["光伏设备", "逆变器", "储能系统", "电网设备"],
        "terms": (
            "逆变器", "储能系统", "电网设备", "大容量电力系统", "并网设备",
            "inverter", "battery energy storage", "bulk-power system", "electric grid",
        ),
    },
    {
        "key": "solar_photovoltaic",
        "products": ["多晶硅", "硅片", "光伏组件"],
        "industries": ["光伏设备", "硅料", "光伏组件"],
        "terms": ("光伏", "多晶硅", "硅片", "组件", "solar", "photovoltaic", "polysilicon"),
    },
    {
        "key": "semiconductor_ai",
        "products": ["芯片", "半导体设备", "人工智能算力"],
        "industries": ["半导体", "电子", "算力基础设施"],
        "terms": (
            "半导体", "芯片", "人工智能", "算力", "晶圆", "semiconductor", "chip",
            "artificial intelligence", "advanced computing", "gpu",
        ),
    },
    {
        "key": "battery_ev",
        "products": ["动力电池", "新能源汽车"],
        "industries": ["动力电池", "新能源汽车", "锂电材料"],
        "terms": ("动力电池", "锂电", "新能源汽车", "electric vehicle", "lithium battery", "ev battery"),
    },
    {
        "key": "critical_minerals_metals",
        "products": ["稀土", "关键矿产", "工业金属"],
        "industries": ["稀土", "有色金属", "矿业"],
        "terms": ("稀土", "关键矿产", "铜", "铝", "镍", "critical mineral", "rare earth", "copper", "nickel"),
    },
    {
        "key": "energy_oil_gas",
        "products": ["原油", "天然气", "成品油"],
        "industries": ["石油石化", "天然气", "航空物流", "化工"],
        "terms": ("原油", "油价", "天然气", "opec", "crude oil", "natural gas", "lng"),
    },
    {
        "key": "pharma_healthcare",
        "products": ["创新药", "医疗器械"],
        "industries": ["医药生物", "医疗器械", "医疗服务"],
        "terms": (
            "创新药", "医药", "医疗器械", "药物", "黑色素瘤", "pharmaceutical", "biotech",
            "medical device", "melanoma", "drug", "controlled substance", "controlled substances",
        ),
    },
    {
        "key": "agriculture_food",
        "products": ["粮食", "农产品", "饲料"],
        "industries": ["种植业", "养殖业", "饲料", "农产品加工"],
        "terms": ("大豆", "玉米", "粮食", "生猪", "农业", "soybean", "corn", "agriculture", "food security"),
    },
    {
        "key": "finance_liquidity",
        "products": ["利率", "汇率", "流动性"],
        "industries": ["银行", "证券", "高估值成长"],
        "terms": ("利率", "美元", "美债", "流动性", "interest rate", "treasury yield", "liquidity", "dollar index"),
    },
    {
        "key": "defense_aerospace",
        "products": ["军工装备", "航空航天", "卫星与无人机"],
        "industries": ["国防军工", "航空装备", "航天装备", "无人机"],
        "terms": (
            "军工", "国防", "导弹", "卫星", "无人机", "航空器", "飞机", "波音", "空客",
            "defense", "missile", "satellite", "drone", "aircraft", "boeing", "airbus", "airworthiness",
        ),
    },
    {
        "key": "shipping_logistics",
        "products": ["海运", "港口", "航空货运"],
        "industries": ["航运港口", "物流", "航空运输"],
        "terms": ("航运", "港口", "集装箱", "海运费", "shipping", "port", "container freight"),
    },
    {
        "key": "consumer_retail",
        "products": ["消费品", "零售", "旅游服务"],
        "industries": ["商贸零售", "食品饮料", "社会服务"],
        "terms": ("消费", "零售", "旅游", "免税", "consumer", "retail", "tourism", "travel demand"),
    },
    {
        "key": "communications_cyber",
        "products": ["通信设备", "云服务", "网络安全"],
        "industries": ["通信", "计算机", "网络安全"],
        "terms": ("通信设备", "云服务", "网络安全", "telecom", "cloud service", "cybersecurity"),
    },
    {
        "key": "data_center_compute_infrastructure",
        "products": ["数据中心", "服务器", "算力基础设施"],
        "industries": ["数据中心", "算力基础设施", "服务器", "高估值成长"],
        "terms": ("数据中心", "算力中心", "服务器", "data center", "datacenter", "server infrastructure"),
    },
    {
        "key": "building_materials_engineered_stone",
        "products": ["石英石板材", "人造石材", "建筑饰面材料"],
        "industries": ["建筑材料", "家居建材", "石英制品"],
        "terms": ("石英石", "人造石", "石英表面产品", "quartz surface", "engineered stone"),
    },
)


STAGE_TERMS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("effective", "已经生效", ("正式生效", "即日起施行", "开始执行", "takes effect", "effective immediately", "entered into force")),
    ("official", "官方已发布", ("签署", "发布命令", "发布公告", "正式宣布", "决定实施", "signed", "announced", "issued an order", "final rule", "presidential action")),
    ("scheduled", "已确认待发生", ("将于", "定于", "计划于", "scheduled for", "will take effect", "effective on")),
    ("draft", "拟议或讨论中", ("拟", "考虑", "研究禁止", "正在制定", "草案", "知情人士", "据悉", "sources say", "considering", "working on", "draft proposal", "may ban")),
    ("rumor", "传闻待核验", ("传闻", "网传", "未经证实", "rumor", "unconfirmed")),
)


STAGE_LABELS = {key: label for key, label, _ in STAGE_TERMS}
STAGE_LABELS["reported"] = "媒体已报道"
CONFIRMATION_LABELS = {
    "official_confirmed": "官方原文确认",
    "multi_source_confirmed": "多源交叉确认",
    "early_warning": "早期预警，待确认",
    "single_source": "单一来源，待复核",
}
TRADE_GATE_LABELS = {
    "candidate_block": "满足个股直接映射后可阻断新增仓位",
    "manual_review": "仅预警，需人工核验",
    "observe": "仅观察，不触发交易",
}


class PolicyEventIntelligence:
    """Turn heterogeneous headlines into traceable event states.

    Fast-news sources provide latency; primary sources and independent
    corroboration provide confirmation.  A single headline is never promoted
    directly to an automatic trading veto.
    """

    OFFICIAL_HOST_SUFFIXES = (
        ".gov",
        ".gov.cn",
        ".gov.uk",
        ".go.jp",
        ".go.kr",
        ".europa.eu",
        "federalregister.gov",
        "whitehouse.gov",
        "federalreserve.gov",
        "sec.gov",
        "bls.gov",
        "bea.gov",
        "government.ru",
        "cbr.ru",
        "imf.org",
        "worldbank.org",
        "wto.org",
        "bis.org",
        "iea.org",
        "opec.org",
        "sse.com.cn",
        "szse.cn",
        "cninfo.com.cn",
    )
    OFFICIAL_SOURCE_TERMS = (
        "白宫", "联邦公报", "交易所", "巨潮", "国务院", "财政部", "商务部",
        "发改委", "工信部", "证监会", "央行", "统计局", "商务部", "海关", "官方公告",
        "美联储", "欧洲央行", "欧盟委员会", "英格兰银行", "日本银行", "韩国银行", "俄罗斯政府",
        "Federal Reserve", "European Commission", "European Central Bank", "Bank of England", "Bank of Japan",
        "International Monetary Fund", "World Bank", "World Trade Organization", "OPEC", "IEA",
    )
    FAST_SOURCE_TERMS = ("金十", "财联社", "华尔街见闻", "7x24", "快讯", "电报")
    TRUSTED_MEDIA_TERMS = ("路透", "Reuters", "新华社", "证券时报", "中国证券报", "上海证券报")

    def enrich_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched = [self.enrich_item(dict(item)) for item in items if isinstance(item, dict)]
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in enriched:
            if item.get("event_type") == "general_information":
                continue
            groups.setdefault(str(item.get("event_fingerprint") or ""), []).append(item)

        for rows in groups.values():
            for row in rows:
                sources: set[str] = set()
                trusted_sources: set[str] = set()
                official = False
                corroborating_rows = [candidate for candidate in rows if self._same_event(row, candidate)]
                for candidate in corroborating_rows:
                    row_sources = [str(candidate.get("source") or "").strip()]
                    row_sources.extend(str(value).strip() for value in (candidate.get("duplicate_sources") or []))
                    for source in row_sources:
                        if not source:
                            continue
                        sources.add(source)
                        tier = self.source_tier(
                            source,
                            str(candidate.get("url") or candidate.get("source_ref") or ""),
                            candidate.get("credibility_score"),
                        )
                        if tier in {"official_primary", "trusted_media"}:
                            trusted_sources.add(source)
                        if tier == "official_primary":
                            official = True
                confirmation = (
                    "official_confirmed"
                    if official
                    else "multi_source_confirmed"
                    if len(trusted_sources) >= 2
                    else "early_warning"
                    if row.get("event_stage") in {"rumor", "draft"} or row.get("source_tier") == "fast_alert"
                    else "single_source"
                )
                row["confirmation_level"] = confirmation
                row["confirmation_level_cn"] = CONFIRMATION_LABELS[confirmation]
                row["confirmation_source_count"] = len(sources)
                row["confirmation_sources"] = sorted(sources)
                row["evidence_reliability"] = self._reliability(confirmation, str(row.get("content_quality_status") or ""))
                self._set_decision_use(row)
                row["trade_gate"] = self._trade_gate(row)
                row["trade_gate_cn"] = TRADE_GATE_LABELS[row["trade_gate"]]
        return enriched

    def collapse_event_clusters(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Collapse split headlines after confirmation, without losing provenance."""
        clusters: list[list[dict[str, Any]]] = []
        for raw in items:
            item = dict(raw or {})
            target: list[dict[str, Any]] | None = None
            for cluster in clusters:
                representative = cluster[0]
                if item.get("event_fingerprint") != representative.get("event_fingerprint"):
                    continue
                if item.get("event_type") == "general_information":
                    target = cluster
                    break
                if self._same_event(item, representative):
                    target = cluster
                    break
            if target is None:
                clusters.append([item])
            else:
                target.append(item)

        collapsed: list[dict[str, Any]] = []
        for cluster in clusters:
            best = max(cluster, key=self._representative_priority)
            row = dict(best)
            sources = sorted({
                str(source).strip()
                for item in cluster
                for source in ([item.get("source")] + list(item.get("duplicate_sources") or []))
                if str(source or "").strip()
            })
            refs = list(dict.fromkeys(
                str(ref).strip()
                for item in cluster
                for ref in ([item.get("url") or item.get("source_ref")] + list(item.get("duplicate_source_refs") or []))
                if str(ref or "").strip()
            ))
            titles = list(dict.fromkeys(str(item.get("title") or "").strip() for item in cluster if str(item.get("title") or "").strip()))
            times = sorted(
                str(item.get("published_at") or item.get("published_at_norm") or "").strip()
                for item in cluster
                if str(item.get("published_at") or item.get("published_at_norm") or "").strip()
            )
            row["event_cluster_size"] = len(cluster)
            row["duplicate_count"] = sum(max(1, int(item.get("duplicate_count") or 1)) for item in cluster)
            row["duplicate_sources"] = sources
            row["duplicate_source_refs"] = refs[:20]
            row["duplicate_titles"] = titles[:20]
            row["first_seen_at"] = times[0] if times else ""
            row["latest_seen_at"] = times[-1] if times else ""
            collapsed.append(row)
        return sorted(collapsed, key=self._representative_priority, reverse=True)

    @staticmethod
    def _representative_priority(item: dict[str, Any]) -> tuple[int, int, int, int]:
        confirmation = {
            "official_confirmed": 4,
            "multi_source_confirmed": 3,
            "single_source": 2,
            "early_warning": 1,
        }.get(str(item.get("confirmation_level") or ""), 0)
        source = {"official_primary": 4, "trusted_media": 3, "fast_alert": 2, "other": 1}.get(
            str(item.get("source_tier") or ""), 0
        )
        quality = {"full_text": 3, "structured_excerpt": 2, "title_only": 1}.get(
            str(item.get("content_quality_status") or ""), 0
        )
        return confirmation, source, quality, len(str(item.get("summary") or item.get("title") or ""))

    def enrich_item(self, item: dict[str, Any]) -> dict[str, Any]:
        text = self._text(item)
        source = str(item.get("source") or item.get("source_name") or "").strip()
        url = str(item.get("url") or item.get("source_url") or item.get("source_ref") or "").strip()
        event_rule = self._match_event_rule(text)
        matched_event_terms = sorted({
            str(term).lower()
            for term in (event_rule.get("terms") if event_rule else ())
            if self._contains(text, (str(term),))
        })
        topics = [rule for rule in TOPIC_RULES if self._contains(text, rule["terms"])]
        matched_topic_terms = sorted({
            str(term).lower()
            for rule in topics
            for term in rule["terms"]
            if self._contains(text, (str(term),))
        })
        stage = self._event_stage(text, source, url)
        source_tier = self.source_tier(source, url, item.get("credibility_score"))
        event_type = str(event_rule.get("key")) if event_rule else "general_information"
        direction, direction_reason = self._event_direction(text, event_rule)
        severity = str(event_rule.get("severity")) if event_rule else "low"
        topic_keys = [str(rule["key"]) for rule in topics]
        products = list(dict.fromkeys(value for rule in topics for value in rule["products"]))
        industries = list(dict.fromkeys(value for rule in topics for value in rule["industries"]))
        regions = self._regions(text)
        fingerprint = self._fingerprint(item, event_type, topic_keys, regions)
        initial_confirmation = (
            "official_confirmed"
            if source_tier == "official_primary" and stage in {"official", "effective", "scheduled"}
            else "early_warning"
            if stage in {"rumor", "draft"} or source_tier == "fast_alert"
            else "single_source"
        )
        item.update(
            {
                "event_type": event_type,
                "event_type_cn": str(event_rule.get("label_cn")) if event_rule else "一般信息",
                "event_stage": stage,
                "event_stage_cn": STAGE_LABELS.get(stage, "阶段未知"),
                "event_direction": direction,
                "event_direction_cn": {"positive": "正向", "negative": "负向", "mixed": "方向待确认", "neutral": "中性"}.get(direction, "中性"),
                "event_direction_reason_cn": direction_reason,
                "event_severity": severity,
                "event_severity_cn": {"high": "高", "medium": "中", "low": "低"}.get(severity, "低"),
                "source_tier": source_tier,
                "source_tier_cn": {"official_primary": "官方原始来源", "trusted_media": "高可信媒体", "fast_alert": "快速快讯", "other": "其他公开来源"}.get(source_tier, "其他公开来源"),
                "confirmation_level": initial_confirmation,
                "confirmation_level_cn": CONFIRMATION_LABELS[initial_confirmation],
                "confirmation_source_count": 1,
                "confirmation_sources": [source] if source else [],
                "event_actor": self._actor_anchor(text),
                "matched_event_terms": matched_event_terms,
                "detected_topics": topic_keys,
                "matched_topic_terms": matched_topic_terms,
                "affected_products_cn": products,
                "affected_industries_cn": industries,
                "affected_regions_cn": regions,
                "event_fingerprint": fingerprint,
                "evidence_reliability": self._reliability(initial_confirmation, str(item.get("content_quality_status") or "")),
                "named_subject": self._named_subject(text, event_type),
            }
        )
        self._set_decision_use(item)
        item["trade_gate"] = self._trade_gate(item)
        item["trade_gate_cn"] = TRADE_GATE_LABELS[item["trade_gate"]]
        return item

    @staticmethod
    def _set_decision_use(item: dict[str, Any]) -> None:
        event_type = str(item.get("event_type") or "general_information")
        industry_specific = bool(item.get("affected_industries_cn") or item.get("affected_products_cn"))
        market_wide = event_type in {
            "monetary_policy",
            "economic_data_release",
            "geopolitical_disruption",
        }
        issuer_specific = bool(item.get("named_subject")) or event_type == "earnings_or_guidance"
        product_case = event_type == "regulatory_investigation" and not issuer_specific
        broad_industry_event = event_type in {
            "sanction_or_blacklist",
            "export_or_import_restriction",
            "security_review",
            "tariff_change",
            "support_or_subsidy",
            "operational_disruption",
            "labor_or_logistics_disruption",
            "cyber_or_infrastructure_incident",
            "natural_disaster_or_extreme_weather",
        }
        scope = (
            "market"
            if market_wide
            else "issuer"
            if issuer_specific
            else "case"
            if product_case
            else "industry"
            if industry_specific and broad_industry_event
            else "unmapped"
        )
        confirmed = (
            item.get("confirmation_level") in {"official_confirmed", "multi_source_confirmed"}
            and item.get("event_stage") not in {"rumor", "draft"}
        )
        specific = event_type != "general_information" and scope != "unmapped"
        use = "score_candidate" if specific and confirmed else "early_warning" if specific else "display_only"
        item["decision_scope"] = scope
        item["decision_scope_cn"] = {
            "industry": "有明确行业/产品传导",
            "market": "仅进入市场环境判断",
            "issuer": "单一公司事件，需精确匹配标的",
            "case": "单一产品/监管案件，需精确暴露证据",
            "unmapped": "尚无可验证传导对象",
        }[scope]
        item["decision_use"] = use
        item["decision_use_cn"] = {
            "score_candidate": "确认后可进入映射评分",
            "early_warning": "提前预警，暂不计分",
            "display_only": "仅展示，不进入评分",
        }[use]
        item["score_candidate"] = use == "score_candidate"
        item["early_warning_candidate"] = use == "early_warning"

    @staticmethod
    def _named_subject(text: str, event_type: str) -> str:
        if event_type not in {"earnings_or_guidance", "regulatory_investigation", "operational_disruption"}:
            return ""
        title = str(text or "").split("\n", 1)[0].strip()
        patterns = (
            r"\b(?:The\s+)?([A-Z][A-Za-z0-9&.' -]{1,48}\s(?:Company|Corporation|Corp\.?|Inc\.?|Ltd\.?|Group|Airplanes))\b",
            r"^([\u4e00-\u9fffA-Za-z0-9]{2,18}(?:股份|集团|公司|科技|能源|银行|证券|药业|电源))(?=[：:,，\s])",
        )
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return re.sub(r"\s+", " ", str(match.group(1) or "").strip())
        return ""

    @staticmethod
    def _same_event(left: dict[str, Any], right: dict[str, Any]) -> bool:
        if left is right:
            return True
        if left.get("event_type") != right.get("event_type"):
            return False
        left_topics = set(left.get("detected_topics") or [])
        right_topics = set(right.get("detected_topics") or [])
        if left_topics and right_topics and not left_topics.intersection(right_topics):
            return False
        left_regions = set(left.get("affected_regions_cn") or [])
        right_regions = set(right.get("affected_regions_cn") or [])
        if left_regions and right_regions and not left_regions.intersection(right_regions):
            return False
        left_terms = set(left.get("matched_topic_terms") or [])
        right_terms = set(right.get("matched_topic_terms") or [])
        if left_terms and right_terms and left_terms.intersection(right_terms):
            return True
        left_event_terms = set(left.get("matched_event_terms") or [])
        right_event_terms = set(right.get("matched_event_terms") or [])
        same_actor = bool(
            left.get("event_actor")
            and left.get("event_actor") == right.get("event_actor")
        )
        if (
            same_actor
            and left_event_terms.intersection(right_event_terms)
            and PolicyEventIntelligence._time_distance_seconds(left, right) <= 30 * 60
        ):
            return True
        left_text = re.sub(r"[\W_]+", "", str(left.get("title") or "").lower())
        right_text = re.sub(r"[\W_]+", "", str(right.get("title") or "").lower())
        return bool(left_text and right_text and SequenceMatcher(None, left_text, right_text).ratio() >= 0.72)

    @staticmethod
    def _actor_anchor(text: str) -> str:
        title = str(text or "").split("\n", 1)[0].strip()
        prefix = re.split(r"[：:]", title, maxsplit=1)[0].strip()
        if not prefix or len(prefix) > 36:
            return ""
        actor_terms = (
            "央行", "美联储", "财政部", "商务部", "白宫", "国务院", "证监会", "交易所",
            "委员会", "部长", "总统", "总理", "主席", "行长", "副行长", "首席执行官",
            "central bank", "federal reserve", "ministry", "commission", "president", "governor", "ceo",
        )
        lowered = prefix.lower()
        return re.sub(r"\s+", " ", lowered) if any(term in lowered for term in actor_terms) else ""

    @staticmethod
    def _time_distance_seconds(left: dict[str, Any], right: dict[str, Any]) -> float:
        def parse(item: dict[str, Any]) -> datetime | None:
            value = str(item.get("published_at_norm") or item.get("published_at") or "").strip()
            if not value:
                return None
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return parsedate_to_datetime(value)
                except (TypeError, ValueError, OverflowError):
                    return None

        left_time = parse(left)
        right_time = parse(right)
        if not left_time or not right_time:
            return float("inf")
        try:
            return abs((left_time - right_time).total_seconds())
        except TypeError:
            return float("inf")

    def _event_direction(self, text: str, event_rule: dict[str, Any] | None) -> tuple[str, str]:
        if not event_rule:
            return "neutral", "未识别到可计算方向的事件类型"
        lowered = text.lower()
        event_type = str(event_rule.get("key") or "")
        default = str(event_rule.get("direction") or "neutral")
        relief_terms = (
            "解除制裁", "取消禁令", "撤销限制", "豁免", "暂停加征", "停止调查",
            "lift sanctions", "lifted sanctions", "repeal the ban", "remove restrictions", "waiver",
        )
        if event_type in {
            "sanction_or_blacklist", "export_or_import_restriction", "security_review",
            "regulatory_investigation", "tariff_change",
        } and self._contains(lowered, relief_terms):
            return "positive", "限制、制裁或调查出现解除、撤销或豁免信号"

        if event_type == "support_or_subsidy" and self._contains(
            lowered,
            ("取消补贴", "削减补贴", "停止支持", "补贴退坡", "withdraw subsidy", "cut subsidies", "end support"),
        ):
            return "negative", "产业支持被取消、削减或退出"

        negative_terms = (
            "下降", "下滑", "收缩", "恶化", "低于预期", "不及预期", "亏损", "转亏", "裁员",
            "declined", "fell", "contracted", "weaker than expected", "missed expectations", "loss",
        )
        positive_terms = (
            "增长", "上升", "改善", "回升", "高于预期", "超预期", "扭亏", "创纪录",
            "grew", "rose", "increased", "improved", "beat expectations", "record high",
        )
        if event_type in {"economic_data_release", "earnings_or_guidance"}:
            has_negative = self._contains(lowered, negative_terms)
            has_positive = self._contains(lowered, positive_terms)
            if has_negative and not has_positive:
                return "negative", "数据或经营表述显示下降、收缩、亏损或不及预期"
            if has_positive and not has_negative:
                return "positive", "数据或经营表述显示增长、改善或超预期"
            return "mixed", "数据方向需结合前值、预期值和具体指标含义复核"

        if event_type == "tariff_change":
            if self._contains(lowered, ("加征", "提高关税", "额外关税", "additional tariff", "raise tariffs")):
                return "negative", "新增或提高关税通常增加相关产业链成本或准入压力"
            return "mixed", "关税变化对进口方、出口方和替代产业的方向不同"
        if event_type == "regulatory_investigation" and self._contains(
            lowered,
            ("controlled substance", "controlled substances", "schedule iv", "药物列入", "列入管制"),
        ):
            return "mixed", "药物分级或列管影响取决于适应症、处方限制、商业化资格和具体涉事主体"
        return default, {
            "positive": "事件规则指向支持、获批或供需改善",
            "negative": "事件规则指向限制、执法、停产或风险冲击",
            "mixed": "事件影响依赖指标、资产和传导方向",
            "neutral": "事件暂不具备明确方向",
        }.get(default, "事件方向待复核")

    def source_tier(self, source: str, url: str = "", credibility: Any = None) -> str:
        host = urlparse(str(url or "")).netloc.lower().split(":", 1)[0]
        source_text = str(source or "")
        if any(host == suffix.lstrip(".") or host.endswith(suffix) for suffix in self.OFFICIAL_HOST_SUFFIXES):
            return "official_primary"
        if any(term in source_text for term in self.OFFICIAL_SOURCE_TERMS):
            return "official_primary"
        if any(term.lower() in source_text.lower() for term in self.TRUSTED_MEDIA_TERMS):
            return "trusted_media"
        try:
            if float(credibility or 0) >= 85:
                return "trusted_media"
        except (TypeError, ValueError):
            pass
        if any(host == domain or host.endswith(f".{domain}") for domain in ("jin10.com", "cls.cn", "wallstcn.com")):
            return "fast_alert"
        if any(term in source_text for term in self.FAST_SOURCE_TERMS):
            return "fast_alert"
        return "other"

    @staticmethod
    def _contains(text: str, terms: tuple[str, ...]) -> bool:
        lowered = text.lower()
        for raw_term in terms:
            term = str(raw_term).lower().strip()
            if not term:
                continue
            if re.fullmatch(r"[a-z0-9][a-z0-9 .+/_-]*", term):
                if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered):
                    return True
            elif term in lowered:
                return True
        return False

    def _match_event_rule(self, text: str) -> dict[str, Any] | None:
        direct = next((rule for rule in EVENT_RULES if self._contains(text, rule["terms"])), None)
        if direct:
            return direct
        lowered = text.lower()
        # Headlines often place the affected country/product between the verb
        # and "import/export". Keep this bounded so a generic word such as
        # "limit" cannot classify an unrelated long article as a trade ban.
        trade_pattern = (
            r"(?:限制|禁止|暂停|收紧).{0,24}(?:进口|出口|采购|市场准入)"
            r"|(?:进口|出口|采购|市场准入).{0,24}(?:限制|禁令|管制)"
            r"|(?:restrict|ban|prohibit|suspend).{0,48}(?:import|export|procurement|market access)"
        )
        if re.search(trade_pattern, lowered):
            return next(rule for rule in EVENT_RULES if rule["key"] == "export_or_import_restriction")
        return None

    @staticmethod
    def _text(item: dict[str, Any]) -> str:
        return " ".join(
            str(item.get(key) or "")
            for key in ("title", "summary", "content", "category", "event_label", "risk_tag")
        ).strip()

    def _event_stage(self, text: str, source: str, url: str) -> str:
        lowered = text.lower()
        # Rumours and drafts remain tentative even when a media headline uses
        # an authoritative organisation name.
        for key in ("rumor", "draft"):
            _, _, terms = next(row for row in STAGE_TERMS if row[0] == key)
            if any(term.lower() in lowered for term in terms):
                return key
        for key in ("effective", "scheduled", "official"):
            _, _, terms = next(row for row in STAGE_TERMS if row[0] == key)
            if any(term.lower() in lowered for term in terms):
                return key
        if self.source_tier(source, url) == "official_primary":
            return "official"
        return "reported"

    @staticmethod
    def _regions(text: str) -> list[str]:
        lowered = text.lower()
        rules = (
            ("美国", ("美国", "美方", "u.s.", "united states", "white house")),
            ("中国", ("中国", "中方", "china", "chinese")),
            ("欧盟", ("欧盟", "欧洲委员会", "european union", "eu commission")),
            ("日本", ("日本", "japan")),
            ("全球", ("全球", "global", "worldwide")),
        )
        return [label for label, terms in rules if any(term.lower() in lowered for term in terms)]

    def _fingerprint(self, item: dict[str, Any], event_type: str, topics: list[str], regions: list[str]) -> str:
        published = str(
            item.get("published_at_norm")
            or item.get("published_at")
            or item.get("publish_time")
            or item.get("date_display")
            or ""
        )
        day = self._parse_day(published)
        if event_type == "general_information":
            title = re.sub(r"[\W_]+", "", str(item.get("title") or "").lower())[:80]
            raw = f"general|{day}|{title}"
        else:
            raw = "|".join((event_type, ",".join(sorted(topics)) or "general", ",".join(sorted(regions)) or "global", day))
        return hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:20]

    @staticmethod
    def _parse_day(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return "undated"
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
        try:
            return parsedate_to_datetime(text).date().isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
        match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
        if match:
            return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        return "undated"

    @staticmethod
    def _reliability(confirmation: str, content_quality: str) -> float:
        base = {
            "official_confirmed": 1.0,
            "multi_source_confirmed": 0.86,
            "single_source": 0.55,
            "early_warning": 0.35,
        }.get(confirmation, 0.35)
        quality = {"full_text": 1.0, "structured_excerpt": 0.9, "title_only": 0.62}.get(content_quality, 0.72)
        return round(base * quality, 4)

    @staticmethod
    def _trade_gate(item: dict[str, Any]) -> str:
        if item.get("decision_scope") == "unmapped":
            return "observe"
        if item.get("event_direction") != "negative":
            return "observe"
        if item.get("event_stage") in {"rumor", "draft"}:
            return "manual_review"
        confirmed = item.get("confirmation_level") in {"official_confirmed", "multi_source_confirmed"}
        if confirmed and item.get("event_severity") == "high":
            return "candidate_block"
        return "manual_review"
