from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from quant_data.services.source_knowledge_service import SourceKnowledgeService


@dataclass(frozen=True)
class TechnicalIndicatorSpec:
    key: str
    name: str
    category: str
    dimension: str
    formula: str
    judgment: str
    application: str
    scenario: str
    caveat: str
    implemented: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# V3.8 指标知识库：按用户给定CSDN文章的“公式、评判标准、应用场景”结构沉淀。
# 注意：部分大势型/Level-2/Tick指标在公开免费源下只能作为知识库或弱估算，不直接下确定交易结论。
TECHNICAL_INDICATORS: list[TechnicalIndicatorSpec] = [
    TechnicalIndicatorSpec("ma", "移动平均线 MA", "均线型/趋势", "价/时", "MA(n)=ΣClose/n；常用5/10/20/60日", "短线上穿长期为金叉；跌破长期均线为走弱", "趋势跟踪、支撑阻力、方向过滤", "趋势市", "震荡市易频繁假突破"),
    TechnicalIndicatorSpec("ema", "指数移动平均 EMA", "均线型/趋势", "价/时", "EMA_t=α×P_t+(1-α)×EMA_{t-1}, α=2/(n+1)", "反应比MA更快；短EMA上穿长EMA偏多", "短线趋势、MACD基础", "趋势市/短线", "对噪声更敏感"),
    TechnicalIndicatorSpec("rsi", "相对强弱 RSI", "动量/超买超卖", "价", "RSI=100-100/(1+平均涨幅/平均跌幅)", "RSI>70超买，RSI<30超卖，50为多空中轴", "震荡市反转、趋势背离预警", "震荡市/短线", "强趋势中可持续超买/超卖"),
    TechnicalIndicatorSpec("boll", "布林带 BOLL", "波动率/支撑阻力", "价/空", "中轨=MA20；上轨=中轨+2σ；下轨=中轨-2σ", "触及上轨偏过热，触及下轨偏超卖；缩口预示变盘", "震荡区间、波动压缩、突破确认", "震荡市/突破前", "单独触轨不是买卖依据"),
    TechnicalIndicatorSpec("macd", "MACD 平滑异同", "趋势/动量", "价", "DIF=EMA12-EMA26；DEA=EMA9(DIF)；柱=DIF-DEA", "DIF上穿DEA偏多，下穿偏空；柱体扩大代表动能增强", "中长期趋势确认、背离观察", "趋势市", "滞后指标，急跌急涨时反应慢"),
    TechnicalIndicatorSpec("kdj", "KDJ 随机指标", "动量/反转", "价", "K=(C-Ln)/(Hn-Ln)×100；D=K平滑；J=3K-2D", "K>D偏强；J>100过热；J<0超卖", "短线反转、震荡交易", "震荡市/短线", "趋势市中易钝化"),
    TechnicalIndicatorSpec("volume", "成交量 VOL", "成交量", "量", "直接取成交量；可计算VMA5/VMA20", "放量上涨确认趋势，缩量上涨需谨慎，放量下跌偏风险", "突破确认、参与度判断", "所有场景", "公开量无法区分真实主力/对倒"),
    TechnicalIndicatorSpec("vwap", "成交量加权均价 VWAP", "成交量/日内成本", "量/价", "VWAP=Σ(典型价×成交量)/Σ成交量", "价格高于VWAP偏强，低于VWAP偏弱", "日内强弱、机构成本参考", "日内/短线", "日K用VWAP20只是近似成本线"),
    TechnicalIndicatorSpec("atr", "平均真实波幅 ATR", "波动率/风控", "空", "TR=max(H-L,|H-Cp|,|L-Cp|)，ATR=TR的n日平均", "ATR扩大代表波动增加；止损常参考2×ATR", "止损、仓位、波动过滤", "风控", "ATR只衡量幅度不判断方向"),
    TechnicalIndicatorSpec("bias", "乖离率 BIAS", "超买超卖/均值回归", "价", "BIAS=(Close-MA)/MA×100%", "正乖离过大偏过热，负乖离过大偏超跌", "均值回归、低位修复", "震荡市", "强趋势中高乖离可延续"),
    TechnicalIndicatorSpec("wr", "威廉指标 W%R", "超买超卖/反转", "价", "W%R=(Hn-C)/(Hn-Ln)×(-100)", ">-20超买，<-80超卖", "短线反转点和超买超卖", "震荡市/短线", "趋势市钝化"),
    TechnicalIndicatorSpec("momentum", "动量 MOM", "动量", "价", "MOM=Close_t-Close_{t-n}", ">0为正动量，<0为负动量", "趋势强弱、转折观察", "趋势市", "不考虑波动风险"),
    TechnicalIndicatorSpec("roc", "变动率 ROC", "动量", "价", "ROC=(Close_t/Close_{t-n}-1)×100%", "ROC为正偏强，过高防过热", "趋势动量、强弱排序", "趋势市/短线", "极端行情容易追高"),
    TechnicalIndicatorSpec("adx", "平均趋向指数 ADX", "趋势强度", "价/空", "ADX=DX的n日平均，DX=|+DI--DI|/(+DI+-DI)×100", "ADX>20/25趋势增强；+DI>-DI偏多", "过滤震荡、确认趋势强度", "趋势市", "ADX不表示方向，需配合DI"),
    TechnicalIndicatorSpec("dmi", "趋向指标 DMI", "趋势方向", "价/空", "+DI=+DM/ATR×100；-DI=-DM/ATR×100", "+DI>-DI偏多，-DI>+DI偏空", "趋势方向确认", "趋势市", "震荡市多假信号"),
    TechnicalIndicatorSpec("sar", "抛物线 SAR", "趋势跟随/止损", "价/时", "SAR_new=SAR_prev+AF×(EP-SAR_prev)", "SAR在价格下方偏多；上方偏空", "趋势止损、反转跟踪", "趋势明显市场", "横盘震荡会频繁反转"),
    TechnicalIndicatorSpec("obv", "能量潮 OBV", "成交量/能量", "量/价", "上涨日累加成交量，下跌日扣减成交量", "OBV与价格同向确认；背离预警反转", "资金能量、趋势确认", "趋势确认", "不能代表真实主力持仓"),
    TechnicalIndicatorSpec("ad_line", "累积/派发线 A/D Line", "市场强度/量价", "量/价", "AD=Σ[((C-L)-(H-C))/(H-L)×Volume]", "A/D上行说明收盘靠近高位且放量", "量价确认、背离分析", "趋势确认", "H=L时需做异常处理"),
    TechnicalIndicatorSpec("mfi", "资金流量 MFI", "成交量/超买超卖", "量/价", "MFI=100-100/(1+正资金流/负资金流)", "MFI>80超买，MFI<20超卖", "资金流向、量价背离", "震荡/短线", "不等同于真实大单资金"),
    TechnicalIndicatorSpec("vr", "成交量变异率 VR", "能量/情绪", "量", "VR=(UV+0.5MV)/(DV+0.5MV)×100", "VR>450偏过热，VR<70偏低迷", "市场情绪、量能反转", "量能分析", "阈值需结合个股历史"),
    TechnicalIndicatorSpec("rvi", "相对波动指数 RVI", "波动率", "空", "RVI=上涨波动标准差/下跌波动标准差×100", ">100为上涨波动更强，<100为下跌波动更强", "波动方向强弱", "趋势/波动", "公开日线为近似计算"),
    TechnicalIndicatorSpec("pmo", "价格动量振荡器 PMO", "动量", "价", "PMO=EMA(ROC,n)", "PMO>0偏上涨动量，<0偏下行动量", "趋势动量、转折观察", "趋势/短线", "参数敏感"),
    TechnicalIndicatorSpec("vo", "成交量振荡器 VO", "成交量", "量", "VO=(EMA短量-EMA长量)/(EMA短量+EMA长量)×100", ">0为短期量能增强，<0为量能减弱", "量能趋势、资金活跃度", "量能分析", "只看量不看价容易误判"),
    TechnicalIndicatorSpec("ppo", "价格振荡器 PPO", "趋势/动量", "价", "PPO=(EMA短-EMA长)/EMA长×100", ">0偏多，<0偏空", "跨价格标的动量比较", "趋势市", "与MACD类似但归一化"),
    TechnicalIndicatorSpec("pmi", "价格动量指数 PMI", "动量", "价", "PMI=(P_t-P_{t-n})/P_{t-n}×100", ">0上涨动量，<0下跌动量", "强弱排序、短线动量", "趋势/短线", "急涨后需结合风险扣分"),
    TechnicalIndicatorSpec("vmi", "成交量动量 VMI", "成交量/情绪", "量", "VMI=(V_t-V_{t-n})/V_{t-n}×100", ">0量能增强，<0量能减弱", "放量/缩量确认", "量价配合", "异常天量需要过滤"),
    TechnicalIndicatorSpec("volatility", "价格波动率", "波动率", "空", "Volatility=σ(Close)/MA(Close)×100", "越高表示风险/机会空间越大", "风险管理、波动筛选", "风控", "不判断方向"),
    TechnicalIndicatorSpec("volume_volatility", "成交量波动率", "成交量/情绪", "量", "VolVol=σ(Volume)/MA(Volume)×100", "越高表示量能情绪越不稳定", "异常放量识别、风险提示", "量能分析", "高波动不等于利好"),
    TechnicalIndicatorSpec("price_channel", "价格通道", "支撑阻力", "空", "上轨=周期最高价；下轨=周期最低价", "触及上轨为压力/突破观察，触及下轨为支撑/破位观察", "箱体、突破、支撑阻力", "震荡/突破", "突破需成交量确认"),
    TechnicalIndicatorSpec("support_resistance", "支撑/阻力位", "支撑阻力", "空", "历史高低点/密集成交区近似", "突破阻力偏多，跌破支撑偏空", "突破交易、回踩观察", "所有场景", "公开数据无法精确筹码密集区"),
    TechnicalIndicatorSpec("fibonacci_retracement", "斐波那契回调", "空间/支撑阻力", "空", "基于0/23.6/38.2/50/61.8/100%分位", "61.8%常作强支撑/阻力，跌破需警惕", "趋势回调、目标区间", "趋势回调", "主观选高低点会影响结果"),
    TechnicalIndicatorSpec("fibonacci_time", "斐波那契时间窗口", "时间周期", "时", "5/8/13/21/34/55/89...交易日窗口", "接近关键窗口提示变盘概率上升", "变盘窗口提醒", "时间周期", "不能单独决定方向"),
    TechnicalIndicatorSpec("td_sequential", "TD序列", "时间反转", "时", "收盘价连续与4日前比较，计数至9", "上涨TD9防回落，下跌TD9看反弹", "短线时间窗口捕捉", "短线/反转", "只表示时间窗口，不保证反转"),
    TechnicalIndicatorSpec("ichimoku", "一目均衡表 Ichimoku", "综合趋势", "价/时/空", "转折线9、基准线26、云层SpanA/SpanB", "价格在云上偏多，云下偏空，云内震荡", "多周期趋势和支撑阻力", "趋势市", "需要较长样本"),
    TechnicalIndicatorSpec("pivot", "枢轴点 Pivot Points", "支撑阻力", "空", "P=(H+L+C)/3；R1=2P-L；S1=2P-H", "突破R1偏强，跌破S1偏弱", "短线支撑阻力、日内交易", "短线/日内", "日线级为近似参考"),
    TechnicalIndicatorSpec("price_pattern", "价格形态", "形态/空间", "空", "双顶/双底/三角形等基于高低点结构识别", "破颈线/放量突破才可确认", "形态突破、反转预警", "形态交易", "算法识别只做疑似，不替代人工确认"),
    TechnicalIndicatorSpec("zigzag", "ZigZag", "趋势结构", "价/空", "过滤小波动，只保留超过阈值的转折点", "转折点用于观察主趋势结构", "结构过滤、波段识别", "波段分析", "滞后且阈值敏感"),
    TechnicalIndicatorSpec("psy", "心理线 PSY", "情绪/能量", "时/价", "PSY=N日上涨天数/N×100", ">75偏乐观/过热，<25偏悲观/超卖", "市场心理、超买超卖", "震荡/情绪", "单个股有效性有限"),
    TechnicalIndicatorSpec("brar", "BRAR 情绪指标", "能量/情绪", "价/量", "BR=(Σ(H-Cp)/Σ(Cp-L))×100；AR=(Σ(H-O)/Σ(O-L))×100", "BR/AR过高偏热，过低偏冷", "多空意愿、情绪温度", "情绪分析", "无开盘价时只能近似"),
    TechnicalIndicatorSpec("cyr", "CYR 市场强弱", "能量/强弱", "价/时", "CYR=成本/价格均线升降幅度近似", "CYR为正偏强，为负偏弱", "强弱排序、市场活跃度", "强弱比较", "公开数据无法精确成本均线"),
    TechnicalIndicatorSpec("vwm_macd", "成交量加权MACD", "量价动量", "量/价", "VW-MACD=MACD柱×成交量归一化", ">0代表量价动能偏多，<0偏弱", "资金动量确认", "量价配合", "成交量异常会放大噪声"),
    TechnicalIndicatorSpec("twap", "时间加权平均价 TWAP", "执行/日内", "时/价", "TWAP=ΣPrice/n", "价格高于TWAP偏强，低于偏弱", "执行基准、日内均价", "日内", "日线数据只能近似"),
    TechnicalIndicatorSpec("order_book", "市场深度 Order Book", "高频/盘口", "量/价", "委托簿买卖盘深度与撤单率", "买盘厚度/撤单异常用于盘口判断", "高频交易、虚假单识别", "Level-2/Tick", "当前免费公开源未实现", False),
    TechnicalIndicatorSpec("tick", "Tick逐笔数据", "高频/盘口", "量/价/时", "逐笔成交价格、数量、方向", "大单连续成交、对倒需逐笔核验", "主力行为、虚假活跃核验", "Level-2/Tick", "当前免费公开源未实现", False),
    TechnicalIndicatorSpec("vix", "VIX/恐慌指数", "市场情绪", "空/情绪", "市场预期波动率指数", "VIX上升代表风险偏好下降", "大盘风险、海外映射", "宏观/对冲", "A股个股只作外围参考", False),
    TechnicalIndicatorSpec("adr", "涨跌比率 ADR", "大势/情绪", "市场", "ADR=上涨家数/下跌家数", "ADR上升代表市场广度改善", "大盘情绪、市场环境", "大势研判", "需要全市场涨跌家数"),
    TechnicalIndicatorSpec("put_call", "Put/Call Ratio", "市场情绪", "衍生品", "PCR=看跌期权成交量/看涨期权成交量", "过高偏恐慌，过低偏乐观", "期权市场情绪", "衍生品", "A股个股公开源暂不接入", False),
    TechnicalIndicatorSpec("elliott", "艾略特波浪", "综合/周期", "时/空", "8浪循环及1.618/0.618等比例", "3浪常为主升，5浪需防衰竭", "中长期结构分析", "波段/趋势", "主观性强，系统仅提示不打确定分"),
    TechnicalIndicatorSpec("gann_time", "江恩时间法则", "时间周期", "时", "时间对称、角度线、关键日期窗口", "接近关键时间点提示变盘观察", "中长期时间窗口", "周期分析", "主观性强，暂作知识库提示"),
    TechnicalIndicatorSpec("spread", "价差/Spread", "套利", "价", "Spread=A-B或标准化价差", "价差偏离均值后观察回归", "统计套利/跨市场套利", "套利", "需要关联标的和回测验证", False),
    TechnicalIndicatorSpec("beta", "Beta系数", "对冲/风险", "市场", "Beta=Cov(个股收益,市场收益)/Var(市场收益)", ">1弹性大，<1防御性强", "组合风险、对冲比例", "组合/对冲", "需要指数收益序列"),
    TechnicalIndicatorSpec("sharpe", "夏普比率", "绩效/风险", "收益/风险", "Sharpe=(Rp-Rf)/σp", "越高代表单位风险收益越好", "策略回测、组合评价", "回测/组合", "不是单日选股指标"),
    TechnicalIndicatorSpec("var", "风险价值 VaR", "风险管理", "风险", "给定置信度下的最大潜在损失", "VaR越大风险越高", "仓位和风险控制", "组合/风控", "依赖历史分布假设"),
]


class TechnicalIndicatorLibraryService:
    def list(self) -> list[dict[str, Any]]:
        return [x.to_dict() for x in TECHNICAL_INDICATORS]

    def get(self, key_or_tag: str) -> dict[str, Any] | None:
        s_raw = str(key_or_tag or "")
        s = s_raw.lower()
        specs = {x.key.lower(): x for x in TECHNICAL_INDICATORS}
        if s in specs:
            return specs[s].to_dict()
        for spec in TECHNICAL_INDICATORS:
            if spec.key.lower() in s or spec.name.lower() in s:
                return spec.to_dict()
        # 中文/缩写标签映射，避免递归查找造成循环。
        aliases = {
            "均线": "ma", "ema": "ema", "macd": "macd", "rsi": "rsi", "kdj": "kdj", "boll": "boll", "布林": "boll",
            "atr": "atr", "vwap": "vwap", "wr": "wr", "威廉": "wr", "cci": "cci", "bias": "bias", "乖离": "bias",
            "obv": "obv", "能量潮": "obv", "mfi": "mfi", "资金流": "mfi", "adx": "adx", "dmi": "dmi", "sar": "sar",
            "vr": "vr", "psy": "psy", "brar": "brar", "cyr": "cyr", "ichimoku": "ichimoku", "一目": "ichimoku",
            "斐波时间": "fibonacci_time", "斐波": "fibonacci_retracement", "td": "td_sequential", "pivot": "pivot", "枢轴": "pivot",
            "形态": "price_pattern", "zigzag": "zigzag", "支撑": "support_resistance", "阻力": "support_resistance", "通道": "price_channel",
            "量比": "volume", "成交": "volume", "波动": "volatility", "量能": "volume", "动量": "momentum", "心理": "psy",
        }
        for k, v in aliases.items():
            if k.lower() in s or k in s_raw:
                spec = specs.get(v.lower())
                return spec.to_dict() if spec else None
        return None

    def by_category(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for spec in TECHNICAL_INDICATORS:
            out.setdefault(spec.category, []).append(spec.to_dict())
        return out

    def coverage(self) -> dict[str, Any]:
        total = len(TECHNICAL_INDICATORS)
        implemented = sum(1 for x in TECHNICAL_INDICATORS if x.implemented)
        word = SourceKnowledgeService().technical_framework()
        return {
            "total": total,
            "implemented_or_estimated": implemented,
            "knowledge_only": total - implemented,
            "word_source_indicator_count": int(word.get("normalized_indicator_count") or 0),
            "word_table_rows_extracted": len(word.get("word_table_rows_extracted") or []),
            "word_source_categories": word.get("categories", []),
            "word_core_model": word.get("core_model", ""),
        }

    def word_source_catalog(self) -> dict[str, Any]:
        return SourceKnowledgeService().technical_framework()
