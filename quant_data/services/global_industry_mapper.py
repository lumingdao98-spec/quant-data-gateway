from __future__ import annotations

from typing import Any


RULES = [
    {
        "keywords": ["光伏", "硅料", "硅片", "组件", "N型", "TOPCon", "HJT"],
        "industries": ["光伏设备", "硅料", "硅片", "组件", "电站"],
        "concepts": ["光伏", "新能源", "绿色电力"],
        "symbols": ["601012", "600438", "300274"],
        "reason": "光伏政策、硅料价格或组件需求会影响硅料/硅片/组件/逆变器/电站产业链盈利预期。",
    },
    {
        "keywords": ["储能", "逆变器", "PCS", "电化学储能", "新型储能"],
        "industries": ["储能系统", "逆变器", "电池"],
        "concepts": ["储能", "新能源", "电力设备"],
        "symbols": ["300274", "300750"],
        "reason": "储能政策和招标需求会影响逆变器、储能系统和电池供应链订单。",
    },
    {
        "keywords": ["美债", "利率", "降息", "加息", "美元", "流动性"],
        "industries": ["高估值成长股", "科技成长", "新能源"],
        "concepts": ["利率敏感", "成长风格"],
        "symbols": [],
        "reason": "利率和流动性变化会影响高估值成长资产的估值折现率。",
    },
    {
        "keywords": ["原油", "油价", "OPEC", "天然气"],
        "industries": ["油气", "化工", "航空", "物流"],
        "concepts": ["能源价格", "周期资源"],
        "symbols": [],
        "reason": "原油价格影响油气收入、化工成本，以及航空物流燃油成本。",
    },
    {
        "keywords": ["黄金", "金价", "贵金属"],
        "industries": ["黄金", "有色金属"],
        "concepts": ["避险资产", "贵金属"],
        "symbols": [],
        "reason": "金价变化直接影响黄金采选冶企业盈利和有色板块风险偏好。",
    },
    {
        "keywords": ["AI", "算力", "芯片", "半导体", "出口管制"],
        "industries": ["半导体", "算力基础设施", "电子"],
        "concepts": ["AI", "国产替代", "芯片"],
        "symbols": [],
        "reason": "AI/芯片政策和供应链变化影响算力、半导体和电子产业链景气度。",
    },
]


SYMBOL_PROFILE_HINTS = {
    "300274": {"industries": ["光伏设备", "逆变器", "储能系统"], "concepts": ["光伏", "储能", "新能源"], "chain": ["逆变器", "储能系统"]},
    "300750": {"industries": ["电池", "储能系统", "新能源车"], "concepts": ["动力电池", "储能", "新能源"], "chain": ["电池", "储能"]},
    "601012": {"industries": ["光伏设备", "硅片", "组件"], "concepts": ["光伏", "新能源"], "chain": ["硅片", "组件"]},
    "600438": {"industries": ["硅料", "光伏", "农业"], "concepts": ["光伏", "硅料"], "chain": ["硅料", "电池片"]},
}


class GlobalIndustryMapper:
    def company_exposure(self, symbol: str, profile: dict[str, Any] | None = None, name: str = "") -> dict[str, Any]:
        base = dict(SYMBOL_PROFILE_HINTS.get(str(symbol), {}))
        text = " ".join(str(x) for x in [name, profile or {}])
        industries = set(base.get("industries") or [])
        concepts = set(base.get("concepts") or [])
        chain = set(base.get("chain") or [])
        for rule in RULES:
            if any(k.lower() in text.lower() for k in rule["keywords"]):
                industries.update(rule["industries"])
                concepts.update(rule["concepts"])
                chain.update(rule["industries"][:2])
        return {
            "symbol": symbol,
            "name": name or (profile or {}).get("name") or symbol,
            "main_business": (profile or {}).get("summary") or "公开画像不足，按行业/概念关键词和常识产业链映射",
            "industries": sorted(industries),
            "concepts": sorted(concepts),
            "chain_position": sorted(chain),
            "upstream": ["硅料", "锂矿", "能源", "利率资金"] if concepts else [],
            "downstream": ["组件", "储能系统", "电站", "新能源车"] if concepts else [],
            "commodity_sensitivity": ["硅料", "锂", "原油", "黄金"],
            "policy_sensitivity": ["新能源政策", "储能政策", "利率政策", "出口管制"],
        }

    def map_items(self, items: list[dict[str, Any]], symbol: str, name: str = "", profile: dict[str, Any] | None = None) -> dict[str, Any]:
        exposure = self.company_exposure(symbol, profile=profile, name=name)
        mapped = [self.map_item(item, symbol, exposure) for item in items or []]
        return {
            "company_exposure": exposure,
            "industry_mapped_items": mapped,
            "mapped_industries": sorted({x for m in mapped for x in m.get("mapped_industries", [])}),
            "mapped_concepts": sorted({x for m in mapped for x in m.get("mapped_concepts", [])}),
            "mapped_symbols": sorted({x for m in mapped for x in m.get("mapped_symbols", [])}),
            "related_count": len([m for m in mapped if m.get("score_included")]),
        }

    def map_item(self, item: dict[str, Any], symbol: str, exposure: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(str(item.get(k) or "") for k in ["title", "summary", "content", "category"])
        hit_rules = [r for r in RULES if any(k.lower() in text.lower() for k in r["keywords"])]
        industries = sorted({x for r in hit_rules for x in r["industries"]})
        concepts = sorted({x for r in hit_rules for x in r["concepts"]})
        symbols = sorted({x for r in hit_rules for x in r["symbols"]})
        exp_words = set(exposure.get("industries", []) + exposure.get("concepts", []) + exposure.get("chain_position", []))
        overlap = exp_words.intersection(set(industries + concepts))
        direct = symbol in symbols
        relevance = 35 + len(hit_rules) * 12 + len(overlap) * 10 + (18 if direct else 0)
        relevance = max(0, min(100, relevance if hit_rules else 18))
        positive_words = ["利好", "支持", "增长", "降息", "补贴", "招标", "需求", "上行"]
        negative_words = ["利空", "下跌", "制裁", "风险", "收紧", "亏损", "下滑", "加息"]
        impact_direction = "positive" if any(w in text for w in positive_words) else "negative" if any(w in text for w in negative_words) else "neutral"
        reason = "；".join(r["reason"] for r in hit_rules[:2]) if hit_rules else "未命中当前个股行业/概念/产业链关键词，不纳入个股评分。"
        if overlap:
            reason += f" 与当前标的暴露重合：{'、'.join(sorted(overlap))}。"
        elif not hit_rules:
            reason += " 不相关全球新闻只作为市场背景。"
        return {
            **item,
            "is_related_to_symbol": bool(relevance >= 55 and (overlap or direct)),
            "mapped_industries": industries,
            "mapped_concepts": concepts,
            "mapped_symbols": symbols,
            "mapped_chain": sorted(overlap),
            "relevance_score": relevance,
            "impact_direction": impact_direction,
            "impact_reason": reason,
            "score_included": bool(relevance >= 55 and (overlap or direct)),
        }
