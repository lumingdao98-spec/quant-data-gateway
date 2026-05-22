from __future__ import annotations

class MacroPolicyEventService:
    MACRO_TYPES={
        "降息":"rate_cut", "降准":"rrr_cut", "加息":"rate_hike", "PMI":"pmi", "CPI":"cpi", "PPI":"ppi", "GDP":"gdp", "美债":"us_bond_yield", "美元":"usd_index", "原油":"oil", "黄金":"gold", "关税":"tariff", "出口管制":"export_control"
    }
    INDUSTRY_MAP={
        "rate_cut":["成长股","地产链","券商","消费"], "rrr_cut":["银行","券商","地产链","基建"], "rate_hike":["高估值成长承压","黄金/美元相关"], "oil":["油气上游","油服","航空物流承压"], "gold":["黄金","有色贵金属"], "export_control":["半导体","光伏","消费电子","出口制造"], "tariff":["出口制造","消费电子","光伏"]
    }
    def classify_text(self,text:str)->dict:
        text=text or ""
        hits=[]
        for kw,typ in self.MACRO_TYPES.items():
            if kw in text:
                hits.append({"keyword":kw,"event_type":typ,"affected_industries":self.INDUSTRY_MAP.get(typ,[])})
        return {"events":hits,"has_macro_policy":bool(hits)}
