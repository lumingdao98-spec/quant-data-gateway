from __future__ import annotations

from typing import Any


RULES: list[dict[str, Any]] = [
    {
        "key": "photovoltaic",
        "keywords": ["光伏", "硅料", "多晶硅", "硅片", "组件", "TOPCon", "HJT", "BC电池"],
        "industries": ["光伏设备", "硅料", "硅片", "光伏组件", "电站"],
        "concepts": ["光伏", "新能源", "绿色电力"],
        "symbols": ["601012", "600438", "300274"],
        "reason": "硅料价格、装机需求、出口政策和技术路线会影响光伏产业链盈利预期。",
    },
    {
        "key": "battery_storage",
        "keywords": ["动力电池", "锂电", "储能", "逆变器", "PCS", "固态电池", "新能源车"],
        "industries": ["动力电池", "储能系统", "逆变器", "新能源汽车"],
        "concepts": ["锂电池", "储能", "新能源车"],
        "symbols": ["300750", "002594", "300274"],
        "reason": "电池材料价格、车企需求和储能招标会影响电池及储能产业链订单。",
    },
    {
        "key": "ai_semiconductor",
        "keywords": ["人工智能", "AI", "算力", "芯片", "半导体", "存储芯片", "出口管制"],
        "industries": ["半导体", "算力基础设施", "电子", "通信设备"],
        "concepts": ["人工智能", "国产替代", "芯片", "算力"],
        "symbols": [],
        "reason": "算力需求、芯片周期和出口限制会改变半导体及电子产业链景气预期。",
    },
    {
        "key": "robot_low_altitude",
        "keywords": ["机器人", "人形机器人", "低空经济", "无人机", "飞行汽车", "航空航天"],
        "industries": ["机器人", "自动化设备", "航空装备", "低空经济"],
        "concepts": ["机器人", "低空经济", "高端制造"],
        "symbols": [],
        "reason": "订单、政策试点和关键零部件进展会影响机器人与低空经济主题强度。",
    },
    {
        "key": "liquor_consumption",
        "keywords": ["白酒", "食品饮料", "消费", "免税", "零售", "以旧换新"],
        "industries": ["白酒", "食品饮料", "零售"],
        "concepts": ["大消费", "消费复苏"],
        "symbols": ["600519", "000858"],
        "reason": "终端动销、库存、价格带和消费政策会影响食品饮料及零售预期。",
    },
    {
        "key": "finance",
        "keywords": ["银行", "券商", "保险", "资本市场", "两融", "降准", "净息差"],
        "industries": ["银行", "证券", "保险"],
        "concepts": ["大金融", "中特估"],
        "symbols": ["000001", "300059"],
        "reason": "利率、资本市场活跃度和信用环境会影响银行、券商和保险。",
    },
    {
        "key": "resources_energy",
        "keywords": ["原油", "油价", "OPEC", "天然气", "煤炭", "焦煤", "焦炭"],
        "industries": ["石油石化", "煤炭", "化工", "航空物流"],
        "concepts": ["能源价格", "周期资源"],
        "symbols": [],
        "reason": "能源价格影响资源企业收入，也影响化工、航空和物流成本。",
    },
    {
        "key": "metals_gold",
        "keywords": ["黄金", "金价", "贵金属", "铜价", "铝价", "稀土", "有色金属"],
        "industries": ["黄金", "有色金属", "稀土"],
        "concepts": ["避险资产", "贵金属", "周期资源"],
        "symbols": [],
        "reason": "商品价格和美元流动性会直接影响有色金属企业盈利预期。",
    },
    {
        "key": "agriculture",
        "keywords": ["生猪", "猪价", "粮食", "种业", "饲料", "大豆", "玉米", "农业"],
        "industries": ["养殖业", "饲料", "种植业", "农产品加工"],
        "concepts": ["农业", "猪周期", "粮食安全"],
        "symbols": ["600438"],
        "reason": "农产品价格、养殖周期和天气变化会影响饲料、养殖及种植产业链。",
    },
    {
        "key": "medicine",
        "keywords": ["创新药", "医疗器械", "医药", "集采", "医保", "CXO"],
        "industries": ["医药生物", "医疗器械", "医疗服务"],
        "concepts": ["创新药", "医疗健康"],
        "symbols": [],
        "reason": "研发进展、集采规则和医保政策会改变医药产业链估值与盈利预期。",
    },
    {
        "key": "defense",
        "keywords": ["军工", "国防", "军贸", "导弹", "卫星", "航空发动机"],
        "industries": ["国防军工", "航空装备", "卫星产业"],
        "concepts": ["军工", "商业航天"],
        "symbols": [],
        "reason": "订单、国防预算和地缘事件会影响军工产业链景气及风险偏好。",
    },
    {
        "key": "property_infrastructure",
        "keywords": ["房地产", "地产", "基建", "建材", "水泥", "城中村", "专项债"],
        "industries": ["房地产", "建筑材料", "基础建设"],
        "concepts": ["稳增长", "地产链"],
        "symbols": [],
        "reason": "销售、融资、土地和财政政策会影响地产及基建产业链现金流预期。",
    },
    {
        "key": "global_liquidity",
        "keywords": ["美联储", "非农", "CPI", "PCE", "降息", "加息", "美债", "美元"],
        "industries": ["高估值成长", "科技成长", "贵金属"],
        "concepts": ["利率敏感", "全球流动性"],
        "symbols": [],
        "reason": "美国就业和通胀数据会改变利率路径，通过估值折现、汇率和风险偏好影响A股。",
        "market_wide": True,
    },
]


SYMBOL_PROFILE_HINTS: dict[str, dict[str, list[str]]] = {
    "300274": {"industries": ["光伏设备", "逆变器", "储能系统"], "concepts": ["光伏", "储能", "新能源"], "chain": ["逆变器", "储能系统"]},
    "300750": {"industries": ["动力电池", "储能系统", "新能源汽车"], "concepts": ["锂电池", "储能", "新能源车"], "chain": ["电池", "储能"]},
    "601012": {"industries": ["光伏设备", "硅片", "光伏组件"], "concepts": ["光伏", "新能源"], "chain": ["硅片", "组件"]},
    "600438": {"industries": ["硅料", "光伏", "饲料"], "concepts": ["光伏", "硅料", "农业"], "chain": ["硅料", "电池片", "饲料"]},
    "002594": {"industries": ["新能源汽车", "动力电池", "汽车电子"], "concepts": ["新能源车", "锂电池", "储能"], "chain": ["整车", "动力电池"]},
    "600519": {"industries": ["白酒", "食品饮料"], "concepts": ["大消费", "高端白酒"], "chain": ["白酒"]},
    "000001": {"industries": ["银行"], "concepts": ["大金融", "中特估"], "chain": ["商业银行"]},
    "300059": {"industries": ["证券", "金融信息服务"], "concepts": ["券商", "金融科技"], "chain": ["证券经纪", "基金销售"]},
    "159915": {"industries": ["创业板指数"], "concepts": ["ETF", "成长风格"], "chain": ["指数基金"]},
    "510300": {"industries": ["沪深300指数"], "concepts": ["ETF", "核心资产"], "chain": ["指数基金"]},
    "512100": {"industries": ["中证1000指数"], "concepts": ["ETF", "小盘风格"], "chain": ["指数基金"]},
}


def _as_words(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


class GlobalIndustryMapper:
    def company_exposure(self, symbol: str, profile: dict[str, Any] | None = None, name: str = "") -> dict[str, Any]:
        profile = profile or {}
        base = dict(SYMBOL_PROFILE_HINTS.get(str(symbol), {}))
        profile_words: list[str] = []
        for key in ("name", "company_name", "industry", "main_business", "business_scope", "summary", "industry_exposure_text"):
            profile_words.extend(_as_words(profile.get(key)))
        for key in ("business_tags", "main_products", "upstream", "downstream", "business_segments", "tags"):
            profile_words.extend(_as_words(profile.get(key)))
        text = " ".join([name, *profile_words]).lower()
        industries = set(base.get("industries") or [])
        concepts = set(base.get("concepts") or [])
        chain = set(base.get("chain") or [])
        matched_rules: list[str] = []
        for rule in RULES:
            if any(keyword.lower() in text for keyword in rule["keywords"]):
                industries.update(rule["industries"])
                concepts.update(rule["concepts"])
                chain.update(rule["industries"][:2])
                matched_rules.append(rule["key"])
        return {
            "symbol": symbol,
            "name": name or profile.get("name") or symbol,
            "main_business": profile.get("summary") or profile.get("main_business") or "公司公开画像不足，暂不扩展推断题材。",
            "industries": sorted(industries),
            "concepts": sorted(concepts),
            "chain_position": sorted(chain),
            "upstream": _as_words(profile.get("upstream")),
            "downstream": _as_words(profile.get("downstream")),
            "matched_rules": matched_rules,
            "classification_confidence": "high" if profile_words and matched_rules else "medium" if base else "low",
            "classification_note": "基于公司主营、产业链和结构化画像映射；名称或新闻关键词不单独作为题材结论。",
        }

    def map_items(self, items: list[dict[str, Any]], symbol: str, name: str = "", profile: dict[str, Any] | None = None) -> dict[str, Any]:
        exposure = self.company_exposure(symbol, profile=profile, name=name)
        mapped = [self.map_item(item, symbol, exposure) for item in items or []]
        return {
            "company_exposure": exposure,
            "industry_mapped_items": mapped,
            "mapped_industries": sorted({value for item in mapped for value in item.get("mapped_industries", [])}),
            "mapped_concepts": sorted({value for item in mapped for value in item.get("mapped_concepts", [])}),
            "mapped_symbols": sorted({value for item in mapped for value in item.get("mapped_symbols", [])}),
            "related_count": len([item for item in mapped if item.get("included_in_score") or item.get("score_included")]),
        }

    def map_item(self, item: dict[str, Any], symbol: str, exposure: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(str(item.get(key) or "") for key in ("title", "summary", "content", "category")).lower()
        hit_rules = [rule for rule in RULES if any(keyword.lower() in text for keyword in rule["keywords"])]
        industries = sorted({value for rule in hit_rules for value in rule["industries"]})
        concepts = sorted({value for rule in hit_rules for value in rule["concepts"]})
        symbols = sorted({value for rule in hit_rules for value in rule["symbols"]})
        exposure_words = set(exposure.get("industries", []) + exposure.get("concepts", []) + exposure.get("chain_position", []))
        overlap = exposure_words.intersection(set(industries + concepts))
        direct = symbol in symbols
        market_wide = any(bool(rule.get("market_wide")) for rule in hit_rules)
        relevance = 18 if not hit_rules else 32 + len(hit_rules) * 10 + len(overlap) * 12 + (20 if direct else 0) + (5 if market_wide else 0)
        relevance = max(0, min(100, relevance))
        positive_words = ["利好", "支持", "增长", "降息", "补贴", "中标", "需求上升", "回暖"]
        negative_words = ["利空", "下跌", "制裁", "风险", "收紧", "亏损", "下滑", "加息", "冲突"]
        direction = "positive" if any(word in text for word in positive_words) else "negative" if any(word in text for word in negative_words) else "neutral"
        reasons = [rule["reason"] for rule in hit_rules[:2]]
        if overlap:
            reasons.append(f"与当前标的产业暴露重合：{'、'.join(sorted(overlap))}。")
        elif market_wide:
            reasons.append("这是市场级宏观变量，只进入大盘环境分，不直接作为个股利多或利空。")
        elif not hit_rules:
            reasons.append("未命中当前标的行业、概念或产业链，不纳入个股评分。")
        included = bool(relevance >= 55 and (overlap or direct))
        item_id = item.get("id") or item.get("url") or item.get("title") or f"global-{symbol}-{abs(hash(text)) % 1_000_000}"
        return {
            **item,
            "global_item_id": str(item_id),
            "is_related_to_symbol": included,
            "mapped_industries": industries,
            "mapped_concepts": concepts,
            "mapped_symbols": symbols,
            "mapped_chain": sorted(overlap),
            "relevance_score": relevance,
            "impact_direction": direction,
            "impact_reason": " ".join(reasons),
            "included_in_score": included,
            "score_included": included,
            "market_wide": market_wide,
        }
