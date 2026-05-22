from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FundamentalFactor:
    key: str
    name: str
    category: str
    dimension: str
    formula: str
    judgment: str
    application: str
    data_sources: list[str]
    caveat: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FUNDAMENTAL_FACTORS: list[FundamentalFactor] = [
    FundamentalFactor("gdp_growth", "GDP增长率", "宏观经济", "经济周期", "(本期GDP-上期GDP)/上期GDP×100%", ">6%偏扩张；<4%需警惕衰退压力；需结合基数和结构", "判断经济周期和顺周期/防御板块配置", ["国家统计局", "财经日历", "金十/华尔街见闻/财联社快讯"], "季度数据滞后，短线只能作为环境项"),
    FundamentalFactor("cpi_ppi", "CPI/PPI", "宏观经济", "通胀/成本", "同比/环比价格指数变化", "CPI>3%偏通胀压力；PPI连续回升说明工业品景气改善", "映射消费、资源、化工、制造业成本与需求", ["国家统计局", "财经日历", "金十数据", "央行/发改委"], "不同产业链对通胀传导能力不同"),
    FundamentalFactor("pmi", "PMI", "宏观经济", "景气度", "采购经理指数", ">50扩张；<50收缩；连续回升优于单月跳动", "判断制造业景气，映射周期、机械、建材、消费电子", ["国家统计局", "财新PMI", "财经日历"], "需分制造业/非制造业/新订单/库存结构"),
    FundamentalFactor("m2_social_financing", "M2/社融", "流动性", "资金面", "M2=M1+准货币；社融为实体融资总量", "M2和社融超预期偏宽松，低于预期说明信用扩张不足", "判断大盘流动性、成长/小盘弹性和金融地产环境", ["央行", "财经日历", "Wind/AKShare可选"], "宽货币不等于宽信用，需看中长期贷款结构"),
    FundamentalFactor("lpr_reverse_repo", "LPR/逆回购/降准降息", "流动性", "货币政策", "利率水平与公开市场净投放", "降息/降准/净投放偏利好流动性；收紧偏压制估值", "映射地产链、银行、券商、高负债行业、成长股估值", ["央行", "交易所公告", "金十/华尔街见闻快讯"], "政策落地、预期差和已定价程度同样重要"),
    FundamentalFactor("usd_cny", "美元指数/人民币汇率", "国际关联", "汇率", "美元指数、USD/CNY、CFETS篮子", "美元走强/人民币贬值通常压制外资风险偏好；出口链可能受益", "映射外资重仓、出口链、黄金、航空、进口成本", ["金十数据", "华尔街见闻", "外汇行情源"], "汇率影响有行业差异"),
    FundamentalFactor("us10y", "美债10年期收益率", "国际关联", "全球估值锚", "美国10Y国债收益率", ">4.5%通常压制高估值成长；下行利于估值修复", "映射科技、半导体、新能源、港股成长、黄金", ["金十数据", "华尔街见闻", "财经日历"], "A股影响间接，需结合国内流动性"),
    FundamentalFactor("brent_oil", "原油价格", "国际关联", "大宗商品", "Brent/WTI价格及涨跌幅", ">90美元/桶通胀和成本压力上升；下跌利于部分下游成本", "油气开采/油服偏利好，航空/物流/化工成本需分产品判断", ["金十期货", "金十数据", "华尔街见闻", "期货行情"], "油价上涨对化工不是统一利好，需看产品价差"),
    FundamentalFactor("gold_risk", "黄金/避险资产", "国际关联", "避险情绪", "黄金价格、美元、实际利率", "黄金上涨常反映避险或降息预期；对黄金股/贵金属ETF更直接", "判断避险情绪、贵金属板块、风险资产压力", ["金十期货", "金十数据", "华尔街见闻"], "黄金受美元和实际利率共同影响"),
    FundamentalFactor("industry_lifecycle", "行业生命周期", "行业分析", "成长阶段", "初创/成长/成熟/衰退阶段判断", "成长期看收入增速和渗透率；成熟期看格局和现金流；衰退期看转型", "用于行业权重和估值容忍度调整", ["行业研报", "上市公司年报", "政策文件", "行业协会"], "系统只能给线索，完整判断需人工研究"),
    FundamentalFactor("industry_competition", "行业竞争格局", "行业分析", "竞争/份额", "行业集中度、市场份额、进入壁垒", "龙头/高壁垒/份额提升偏正面；价格战/份额下降偏风险", "映射龙头溢价、利润率稳定性和长期质量", ["研报", "年报", "新闻", "公司画像库"], "公开新闻容易滞后或片面"),
    FundamentalFactor("policy_environment", "政策环境", "行业分析", "政策/监管", "扶持、补贴、限制、监管、出口管制", "扶持/补贴/国产替代偏正面；强监管/限制/处罚偏负面", "新能源、半导体、军工、低空经济、医药、教培等政策敏感行业", ["政府网站", "证监会/交易所", "金十/财联社/华尔街见闻"], "政策必须区分全行业利好和个股兑现能力"),
    FundamentalFactor("roe", "ROE净资产收益率", "公司财务", "盈利能力", "ROE=净利润/净资产×100%", "长期>15%通常较强；需看是否由高杠杆推动", "判断公司资本回报和经营质量", ["年报/季报", "东方财富F10", "AKShare", "公司画像库"], "单期ROE失真，需看3-5年稳定性"),
    FundamentalFactor("gross_margin", "毛利率/净利率", "公司财务", "盈利质量", "毛利率=(营收-成本)/营收；净利率=净利润/营收", "高且稳定说明产品力或壁垒；持续下滑说明价格战或成本压力", "评估产品竞争力和成本传导能力", ["财报", "F10", "AKShare"], "行业差异很大，必须同业比较"),
    FundamentalFactor("cashflow_quality", "现金流质量", "公司财务", "现金流", "经营现金流净额/净利润", ">1较好；长期<1或背离需警惕利润质量", "识别财务造假、回款压力和盈利含金量", ["现金流量表", "年报", "公告"], "周期行业和扩张期可能短期承压"),
    FundamentalFactor("debt_ratio", "资产负债率", "公司财务", "偿债能力", "资产负债率=负债总额/资产总额×100%", "40%-60%通常较稳健；过高需警惕利率和偿债压力", "评估长期偿债能力和财务杠杆", ["资产负债表", "F10"], "金融、地产、基建等行业阈值不同"),
    FundamentalFactor("current_quick_ratio", "流动/速动比率", "公司财务", "短期偿债", "流动比率=流动资产/流动负债；速动比率=(流动资产-存货)/流动负债", "流动比率约2、速动比率约1常作安全参考", "判断短期偿债压力", ["资产负债表"], "过高也可能代表资产利用效率低"),
    FundamentalFactor("turnover_efficiency", "应收/存货周转", "公司财务", "运营效率", "周转率=收入或成本/平均余额", "周转率上升说明效率改善；应收/存货异常增长需警惕", "识别经营效率、渠道库存和回款压力", ["财报", "年报附注"], "季节性和商业模式差异大"),
    FundamentalFactor("pe_pb_ps", "PE/PB/PS估值", "估值", "市场价值", "PE=股价/EPS；PB=股价/BPS；PS=市值/营收", "需与行业均值、增长率、盈利质量匹配；PE为负应标记亏损/不可比", "估值安全边际和泡沫风险过滤", ["行情快照", "F10", "AKShare"], "不同生命周期公司适用估值方法不同"),
    FundamentalFactor("management_governance", "管理层与治理", "公司治理", "治理/诚信", "管理层履历、承诺兑现、股权结构、激励、ESG", "优秀治理、长期激励偏正面；频繁减持/质押/造假历史偏风险", "公司画像和长期风险判断", ["公司公告", "年报", "监管函", "公司画像库"], "难以完全量化，系统只做证据链提示"),
    FundamentalFactor("fake_accounting_warning", "财务造假/经营异常信号", "风险识别", "避坑", "利润现金流背离、应收存货异常、关联交易、商誉减值、审计意见", "多项同时出现时大幅提高风险标签", "避雷、风险扣分、禁止高分推荐", ["年报", "审计报告", "问询函", "处罚公告"], "需阅读公告原文，不能只看标题"),
]


INDUSTRY_EVENT_RULES: list[dict[str, Any]] = [
    {"key": "oil_up", "keywords": ["原油上涨", "油价上涨", "布伦特", "WTI", "OPEC", "减产"], "positive": ["油气开采", "油服", "煤化工", "能源安全"], "negative": ["航空", "物流", "航运", "化工下游"], "note": "油价上行利好上游资源和油服，但抬升航空、物流及部分下游成本。"},
    {"key": "solar_policy", "keywords": ["光伏", "硅料", "多晶硅", "太阳能", "组件", "电池片", "光伏装机", "光伏政策", "消纳", "上网电价"], "positive": ["光伏", "硅料", "组件", "逆变器", "新能源"], "negative": ["产能过剩环节", "价格战环节"], "note": "光伏消息要区分需求/装机/政策利好与硅料、组件价格战及产能过剩风险。"},
    {"key": "silicon_price_down", "keywords": ["硅料价格下跌", "多晶硅价格下跌", "光伏价格战", "组件价格下跌", "产能过剩"], "positive": ["下游装机", "运营商"], "negative": ["硅料", "组件", "光伏制造", "产能过剩环节"], "note": "价格下跌可能利好下游装机和运营商，但压制制造环节利润。"},
    {"key": "liquidity_easing", "keywords": ["降息", "降准", "LPR下调", "宽松", "逆回购净投放", "流动性充裕", "社融超预期"], "positive": ["券商", "地产", "银行", "保险", "成长股", "小盘", "新能源", "半导体", "光伏"], "negative": [], "note": "流动性宽松通常改善风险偏好和估值，对高久期成长资产短期弹性更高。"},
    {"key": "liquidity_tight", "keywords": ["加息", "缩表", "收益率上行", "美债收益率上升", "流动性收紧", "通胀超预期", "鹰派"], "positive": ["银行", "保险", "美元资产"], "negative": ["高估值成长", "新能源", "半导体", "光伏", "港股科技"], "note": "贴现率上升压制高估值成长，对成长/新能源/半导体等估值敏感板块不利。"},
    {"key": "gold_up", "keywords": ["黄金上涨", "金价", "避险", "地缘冲突", "战争", "冲突升级"], "positive": ["黄金", "贵金属", "军工", "能源安全"], "negative": ["高估值成长", "风险资产"], "note": "黄金与避险/降息预期相关，直接映射黄金股和贵金属ETF。"},
    {"key": "rate_cut", "keywords": ["降息", "降准", "LPR下调", "宽松", "逆回购净投放"], "positive": ["券商", "地产链", "银行", "基建", "成长股", "小盘"], "negative": [], "note": "流动性宽松改善估值和风险偏好，但需要观察信用扩张是否跟上。"},
    {"key": "rate_hike", "keywords": ["加息", "缩表", "收益率上行", "美债收益率上升", "紧缩"], "positive": ["银行", "保险", "美元资产"], "negative": ["高估值成长", "新能源", "半导体", "港股科技"], "note": "贴现率上升压制高估值成长资产。"},
    {"key": "export_control", "keywords": ["出口管制", "制裁", "关税", "贸易摩擦", "实体清单"], "positive": ["国产替代", "半导体设备", "工业软件", "信创", "军工"], "negative": ["出口链", "消费电子", "外向型制造"], "note": "贸易摩擦强化国产替代，同时压制外向型企业订单和估值。"},
    {"key": "ai_chip", "keywords": ["人工智能", "AI", "大模型", "算力", "芯片", "英伟达", "数据中心"], "positive": ["算力", "服务器", "半导体", "光模块", "数据中心", "软件"], "negative": ["传统低景气行业"], "note": "AI事件需从产业链位置映射到上游芯片、服务器、光模块、软件应用等。"},
    {"key": "new_energy", "keywords": ["新能源", "锂电", "固态电池", "储能", "光伏", "风电", "充电桩"], "positive": ["新能源车", "锂电", "储能", "光伏", "电网设备"], "negative": ["高库存产能过剩环节"], "note": "新能源利好要区分需求改善、价格战、库存和产能过剩。"},
    {"key": "real_estate", "keywords": ["地产政策", "房地产", "首付比例", "房贷利率", "棚改", "城中村"], "positive": ["地产", "家居", "建材", "工程机械", "银行"], "negative": [], "note": "地产政策传导到家居、建材、工程机械和银行资产质量。"},
    {"key": "military", "keywords": ["军工", "国防", "地缘", "冲突", "航天", "无人机", "低空经济"], "positive": ["军工", "航空航天", "低空经济", "无人机", "北斗"], "negative": [], "note": "地缘风险和国防政策对军工、航天、无人机形成主题催化。"},
    {"key": "medical_policy", "keywords": ["集采", "创新药", "医保谈判", "医疗器械", "药审"], "positive": ["创新药", "医疗器械", "CXO"], "negative": ["仿制药", "高价耗材"], "note": "医药政策影响分化，创新审批和出海偏正面，集采压价偏负面。"},
]


SOURCE_TIERS: list[dict[str, Any]] = [
    {"tier": "A", "name": "官方披露", "examples": ["交易所", "巨潮资讯", "证监会", "央行", "国家统计局", "公司公告"], "credibility": 90, "usage": "作为事实证据和核心事件来源"},
    {"tier": "B", "name": "权威财经媒体/快讯", "examples": ["财联社", "华尔街见闻", "金十数据/金十期货", "证券时报", "中证报"], "credibility": 72, "usage": "作为宏观、行业、全球事件和新闻线索"},
    {"tier": "C", "name": "综合财经网站", "examples": ["东方财富", "同花顺", "新浪财经", "腾讯财经"], "credibility": 62, "usage": "用于聚合新闻、行情和F10补充"},
    {"tier": "D", "name": "社区舆情", "examples": ["股吧", "雪球", "微博", "论坛"], "credibility": 38, "usage": "只作为热度、分歧度、传闻风险观察，不作为事实利好利空"},
]


class FundamentalLibraryService:
    """基本面、宏观、消息面和行业映射知识库。

    该服务不直接给出买卖建议，只把网页中提到的宏观/行业/公司/消息源/量化风控框架
    固化成可查询、可复用、可在评分说明中展示的结构化规则。
    """

    def list(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in FUNDAMENTAL_FACTORS]

    def by_category(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for item in FUNDAMENTAL_FACTORS:
            out.setdefault(item.category, []).append(item.to_dict())
        return out

    def source_tiers(self) -> list[dict[str, Any]]:
        return SOURCE_TIERS

    def industry_event_rules(self) -> list[dict[str, Any]]:
        return INDUSTRY_EVENT_RULES

    def map_event_to_industries(self, text: str, stock_text: str = "") -> dict[str, Any]:
        text = str(text or "")
        stock_text = str(stock_text or "")
        matched: list[dict[str, Any]] = []
        positive_hits: list[str] = []
        negative_hits: list[str] = []
        for rule in INDUSTRY_EVENT_RULES:
            if any(k.lower() in text.lower() or k in text for k in rule.get("keywords", [])):
                pos = list(rule.get("positive", []))
                neg = list(rule.get("negative", []))
                positive_hits.extend(pos)
                negative_hits.extend(neg)
                matched.append({"key": rule["key"], "positive": pos, "negative": neg, "note": rule.get("note", "")})

        synonym = {
            "光伏": ["光伏", "硅料", "多晶硅", "硅片", "组件", "太阳能", "电池片"],
            "硅料": ["硅料", "多晶硅", "光伏", "通威"],
            "新能源": ["新能源", "电池", "锂电", "储能", "光伏", "新能源车"],
            "新能源车": ["新能源车", "汽车", "动力电池", "锂电"],
            "半导体": ["半导体", "芯片", "光刻", "集成电路", "中芯"],
            "高估值成长": ["成长", "创业板", "科创", "新能源", "半导体", "光伏", "AI"],
            "黄金": ["黄金", "贵金属", "金矿"],
            "油气开采": ["油气", "石油", "天然气", "能源"],
            "航空": ["航空", "机场", "航司"],
            "银行": ["银行", "金融"],
            "券商": ["券商", "证券", "金融"],
            "地产": ["地产", "房地产", "家居", "建材"],
            "白酒": ["白酒", "消费", "食品饮料", "茅台"],
        }
        def relevant(ind: str) -> bool:
            if not ind:
                return False
            if ind in stock_text:
                return True
            for x in synonym.get(ind, []):
                if x and x in stock_text:
                    return True
            return False

        direct_relevance = []
        for ind in set(positive_hits + negative_hits):
            if relevant(ind):
                direct_relevance.append(ind)
        direction = "中性/待观察"
        if direct_relevance:
            pos_rel = [x for x in direct_relevance if x in positive_hits]
            neg_rel = [x for x in direct_relevance if x in negative_hits]
            if pos_rel and not neg_rel:
                direction = "偏利好"
            elif neg_rel and not pos_rel:
                direction = "偏利空"
            elif pos_rel and neg_rel:
                direction = "影响分化"
        elif matched:
            direction = "行业相关，需结合标的主营确认"
        return {
            "matched": matched,
            "positive_industries": sorted(set(positive_hits)),
            "negative_industries": sorted(set(negative_hits)),
            "direct_relevance": direct_relevance,
            "direction": direction,
            "note": "宏观/全球/商品事件先映射到行业，再结合个股主营、估值、位置和资金面，不能直接等同于个股利好利空。",
        }

    def checklist(self) -> dict[str, Any]:
        return {
            "macro": ["GDP/PMI/CPI/PPI", "M2/社融/LPR/逆回购", "美元指数/美债收益率", "原油/黄金/地缘风险", "VIX/海外市场风险偏好"],
            "industry": ["生命周期", "竞争格局", "政策扶持或监管", "技术趋势", "上下游价格传导", "景气高频数据"],
            "company": ["盈利能力", "偿债能力", "营运效率", "成长能力", "现金流质量", "估值匹配", "管理层与治理", "股东质押/减持/激励"],
            "news": ["官方公告优先", "媒体快讯作为线索", "社区舆情只作热度/传闻风险", "事件级去重", "时效权重", "可信度分层", "行业映射"],
            "quant": ["数据清洗和复权", "手续费滑点", "止损止盈", "仓位管理", "夏普/最大回撤/VaR", "参数优化避免过拟合", "实盘前必须回测与模拟盘"],
        }
