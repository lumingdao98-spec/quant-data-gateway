from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class StrategyItem:
    key: str
    name: str
    category: str
    tags: list[str]
    description: str
    default_weight: float = 1.0
    enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StrategyLibraryService:
    """策略库元数据与自定义 Python 策略校验。"""

    def list(self) -> list[dict[str, Any]]:
        items = [
            StrategyItem("low_position", "低位修复", "低位/价值", ["低位", "回撤", "修复"], "近60/120/250日价格位置、阶段回撤与均线修复综合判断。", 1.2, True),
            StrategyItem("oversold_rebound", "超卖回升", "低位/价值", ["RSI", "低位", "反弹"], "RSI处于低位回升区间，同时价格重新靠近短均线。", .9, False),
            StrategyItem("avoid_chasing_high", "高位追高过滤", "风控过滤", ["高位", "过滤"], "处于近一年高位时降低追涨权重，避免高位接力风险。", 1.0, True),
            StrategyItem("exright_drawdown_guard", "复权回撤校正", "风控过滤", ["除权", "前复权", "回撤"], "筛选默认使用前复权日K计算高位回撤/低位位置，降低分红、送转、除权导致的假回撤。", 1.0, True),
            StrategyItem("ma_repair", "均线修复", "K线趋势", ["MA", "趋势", "修复"], "MA5/MA10/MA20修复，价格重新站上或接近MA20。", 1.0, True),
            StrategyItem("ma_bull", "均线多头", "K线趋势", ["MA", "多头"], "MA5>MA10>MA20，趋势延续性较强。", 1.0, False),
            StrategyItem("macd_cross", "MACD金叉/多头", "K线趋势", ["MACD", "金叉"], "DIF在DEA上方或形成金叉，表示动能改善。", 1.0, True),
            StrategyItem("macd_hist_turn", "MACD柱改善", "K线趋势", ["MACD", "柱体"], "MACD柱连续改善，适合捕捉弱转强。", .8, True),
            StrategyItem("boll_mid_break", "BOLL中轨突破", "技术形态", ["BOLL", "突破"], "价格突破BOLL中轨或站稳中轨，作为修复确认信号。", .8, False),
            StrategyItem("volume_breakout", "温和放量", "量价/盘口", ["量比", "成交额"], "近5日量能相对20日温和放大，排除异常天量。", 1.0, True),
            StrategyItem("amount_active", "成交额活跃", "量价/盘口", ["成交额", "流动性"], "成交额和换手满足流动性条件，便于后续回测/实盘模拟。", .8, False),
            StrategyItem("fund_flow_watch", "资金面观察", "量价/盘口", ["资金面", "成交额", "量比"], "综合成交额、量比、换手率和资金强度估算；无主力资金公开源时只做观察，不伪造流入。", .8, False),
            StrategyItem("vwap_reclaim", "VWAP收复", "量价/盘口", ["VWAP", "成本线", "收复"], "价格重新收复VWAP或20日估算成本线，配合量能改善作为修复确认。", .8, False),
            StrategyItem("volume_dryup_reversal", "缩量企稳", "量价/盘口", ["缩量", "企稳", "回踩"], "回踩均线或支撑附近时量能萎缩，观察抛压衰减后的修复机会。", .7, False),
            StrategyItem("orderbook_imbalance_watch", "盘口偏承接", "量价/盘口", ["委比", "委差", "五档"], "使用公开盘口的委比/委差观察承接；数据源缺盘口时只提示缺失。", .7, False),
            StrategyItem("fake_order_cancel_watch", "虚假挂撤观察", "量价/盘口", ["盘口", "撤单", "Level-2"], "需要Level-2或券商盘口流水才能判断虚假撤单；普通公开源不足时必须标记数据缺失。", .6, False),
            StrategyItem("risk_control", "风险扣分", "风控过滤", ["ST", "破位", "放量下跌"], "ST/退市、破位、放量下跌、成交额过低等风险扣分。", 1.0, True),
            StrategyItem("etf_liquidity", "ETF流动性", "ETF/基金", ["ETF", "流动性"], "ETF成交额、趋势位置和阶段低位综合筛选。", .9, False),
            StrategyItem("news_sentiment", "新闻舆情评分", "新闻/基本面", ["新闻", "情绪", "可信度"], "筛选后低频抓取候选股新闻，计算情绪、可信度、关键词和风险标签。", .7, False),
            StrategyItem("announcement_risk", "公告风险提示", "新闻/基本面", ["公告", "监管", "减持"], "提示监管、减持、问询、诉讼、亏损、处罚等公告风险。", .8, False),
            StrategyItem("finance_quality", "财报质量观察", "新闻/基本面", ["财报", "净利润", "ROE"], "关注营收、归母净利润、扣非净利润、毛利率、现金流和ROE等质量指标。", .9, False),
            StrategyItem("policy_tailwind", "政策/行业催化", "新闻/基本面", ["政策", "行业", "风口"], "从政策、产业趋势和行业关键词中识别潜在催化线索。", .7, False),
            StrategyItem("main_money_est", "资金流估算", "量价/盘口", ["资金", "主力", "大单"], "在无Level-2数据时基于价格方向和成交额估算资金流，后续可替换为券商/Level-2源。", .6, False),
            StrategyItem("northbound_flow_watch", "北向资金观察", "资金/机构", ["北向资金", "沪深股通"], "如果公开数据源提供北向资金则纳入资金面；没有可追溯数据时显示缺失，不参与买入。", .6, False),
            StrategyItem("margin_financing_watch", "融资融券观察", "资金/机构", ["融资", "融券", "杠杆"], "观察融资余额、融券余额和杠杆拥挤度；公开源缺失时只保留风险提示。", .6, False),
            StrategyItem("gap_open", "跳空/缺口观察", "技术形态", ["跳空", "缺口"], "识别高开/低开缺口、回补和连续跳空风险。", .6, False),
            StrategyItem("breakout_platform", "平台突破", "技术形态", ["突破", "平台", "箱体"], "关注横盘平台后放量突破，同时配合风险过滤。", .8, False),
            StrategyItem("boll_squeeze_break", "BOLL收窄突破", "技术形态", ["BOLL", "箱体", "突破"], "BOLL带宽收窄后价格站回中轨或上轨，作为波动压缩后的方向观察。", .8, False),
            StrategyItem("roc_momentum_turn", "ROC动量转正", "动量/反转", ["ROC", "动量", "转强"], "短期ROC和10日动量由弱转强时，提高修复确认权重。", .7, False),
            StrategyItem("support_retest", "支撑回踩确认", "支撑阻力", ["支撑", "回踩", "止损位"], "价格靠近60日支撑但未明显跌破，适合观察止损空间和性价比。", .7, False),
            StrategyItem("resistance_break_confirm", "阻力突破确认", "支撑阻力", ["阻力", "突破", "放量"], "接近箱体上沿时必须配合放量和收盘确认，避免假突破。", .7, False),
            StrategyItem("ma60_regime_filter", "MA60趋势过滤", "趋势跟随", ["MA60", "中期趋势", "过滤"], "MA60向上且价格在其上方时允许提高趋势仓位；跌破MA60则降低新增仓位。", .8, False),
            StrategyItem("adx_trend", "ADX趋势强度", "技术形态", ["ADX", "DI", "趋势强度"], "ADX>=22且+DI>-DI时提高趋势确认权重，避免只看均线。", .8, False),
            StrategyItem("rsi_kdj_resonance", "RSI/KDJ共振", "动量/反转", ["RSI", "KDJ", "超买超卖"], "RSI处于健康或修复区间，KDJ同步改善时加权。", .8, False),
            StrategyItem("mfi_obv_resonance", "MFI/OBV资金共振", "量价/盘口", ["MFI", "OBV", "VWAP"], "用资金流量指标和能量潮确认量价配合，降低单看成交量的误判。", .8, False),
            StrategyItem("atr_risk", "ATR高波动过滤", "风控过滤", ["ATR", "波动率", "止损空间"], "ATR占价格过高时扣分，提示波动和止损空间扩大。", .8, True),
            StrategyItem("sar_trend", "SAR趋势跟随", "趋势跟随", ["SAR", "止损", "趋势"], "SAR位于价格下方且趋势向上时作为趋势跟随确认。", .7, False),
            StrategyItem("bias_reversion", "BIAS乖离修复", "均值回归", ["BIAS", "乖离率", "均值回归"], "价格相对MA20负乖离后修复，配合RSI/KDJ做低位观察。", .7, False),
            StrategyItem("vr_mfi_energy", "VR/MFI能量共振", "量价/盘口", ["VR", "MFI", "能量"], "VR处于非极端区间且MFI改善时，作为量价能量确认。", .7, False),
            StrategyItem("td_time_window", "TD/斐波时间窗口", "时间周期", ["TD", "斐波那契时间", "变盘"], "TD序列和斐波那契时间窗口只提示变盘概率，不单独决定方向。", .6, False),
            StrategyItem("fibo_pivot_space", "斐波/Pivot空间结构", "支撑阻力", ["斐波那契", "Pivot", "支撑阻力"], "结合斐波回调、Pivot与箱体位置判断空间结构。", .7, False),
            StrategyItem("ichimoku_cloud", "一目均衡云图", "趋势跟随", ["Ichimoku", "云图"], "价格在云上偏多、云下偏空，云内以震荡处理。", .7, False),
            StrategyItem("pattern_zigzag", "形态/ZigZag结构", "技术形态", ["双底", "双顶", "三角形", "ZigZag"], "识别双底/双顶/三角收敛雏形，所有形态信号均需成交量确认。", .6, False),
            StrategyItem("psy_brar_sentiment", "PSY/BRAR情绪温度", "能量/情绪", ["PSY", "BRAR", "CYR"], "心理线、BRAR与CYR综合判断市场情绪是否过热或低迷。", .6, False),
            StrategyItem("macro_liquidity", "宏观流动性框架", "宏观/大势", ["M2", "社融", "LPR", "逆回购"], "把M2、社融、LPR、逆回购、降准降息等作为大盘风险偏好和估值环境的背景项。", .7, False),
            StrategyItem("global_sector_reference", "全球行业走势参照", "宏观/大势", ["海外行业", "全球指数", "交易时段", "环境分"], "按每只股票所属行业选择可追溯的海外行业指数或期货，并按各市场开盘时段校准；最多占大盘环境分15%，不能单独触发买入。", .7, False),
            StrategyItem("global_commodity_map", "全球商品事件映射", "宏观/大势", ["金十期货", "原油", "黄金", "美债", "美元"], "接入金十/金十期货、华尔街见闻、财联社等全球要闻，将原油、黄金、美债、美元等事件映射到行业。", .7, False),
            StrategyItem("sector_strength", "板块强度观察", "宏观/大势", ["板块", "行业", "相对强弱"], "结合行业/主题热度和宽基表现，避免个股脱离板块孤立判断。", .7, False),
            StrategyItem("market_breadth_filter", "市场宽度过滤", "宏观/大势", ["上涨家数", "宽基指数", "大盘情绪"], "使用上证、创业板、沪深300等宽基状态和市场宽度控制新增仓位。", .8, False),
            StrategyItem("fundamental_quality", "基本面质量", "基本面/财务", ["ROE", "毛利率", "净利率", "成长"], "使用ROE、毛利率、净利率、营收和利润增长等判断公司经营质量，而不是只看PE/PB。", .8, False),
            StrategyItem("cashflow_quality", "现金流含金量", "基本面/财务", ["经营现金流", "净利润", "应收账款"], "关注利润与经营现金流是否背离，应收账款/存货是否异常增长，作为财务质量风险提示。", .8, False),
            StrategyItem("governance_risk", "治理与股东风险", "基本面/财务", ["减持", "质押", "高管", "ESG"], "关注管理层变动、大股东减持/质押、监管处罚、ESG合规等长期风险。", .7, False),
            StrategyItem("source_reliability", "消息来源可信度", "消息面/事件驱动", ["官方", "媒体", "社区", "传闻"], "按官方公告、权威媒体、综合网站、社区舆情分层，不把股吧/雪球小作文当事实利好利空。", .8, True),
            StrategyItem("event_driven", "事件驱动", "消息面/事件驱动", ["公告", "订单", "重组", "监管", "财报"], "对财报、订单、重组、监管、诉讼、减持等事件做事件级去重和时效权重。", .8, False),
            StrategyItem("industry_policy_map", "政策行业映射", "消息面/事件驱动", ["政策", "行业", "产业链"], "把宏观政策、行业政策、技术突破、地缘和商品价格变化映射到行业，再映射到个股。", .7, False),
            StrategyItem("report_blackout", "财报窗口保护", "消息面/事件驱动", ["财报", "预告", "窗口期"], "财报、业绩预告、半年报窗口期降低追高和新增仓位，避免事件落地前盲目下单。", .8, False),
            StrategyItem("backtest_required", "回测约束", "回测/风控/执行", ["手续费", "滑点", "过拟合", "参数优化"], "提醒策略必须经过数据清洗、复权、手续费滑点、参数稳健性和样本外验证，避免只看当期评分。", .6, False),
            StrategyItem("position_risk", "仓位与止损", "回测/风控/执行", ["仓位", "止损", "ATR", "最大回撤"], "结合ATR、最大回撤、VaR/波动率进行仓位约束，避免高波动标的满仓追涨。", .7, True),
            StrategyItem("trailing_take_profit", "移动止盈", "回测/风控/执行", ["止盈", "移动止损", "保护利润"], "趋势策略盈利后用移动止盈或分批止盈保护利润，而不是只靠固定止盈。", .7, False),
            StrategyItem("dca_core_plan", "定投/核心仓计划", "回测/风控/执行", ["定投", "核心仓", "长期"], "适用于ETF或长期资产，按周期和估值调节核心仓，短线策略不得替代长期计划。", .7, False),
        ]
        return [x.to_dict() for x in items]

    def validate_custom_code(self, code: str) -> dict[str, Any]:
        code = code or ""
        if not code.strip():
            return {
                "ok": True,
                "message": "未填写自定义策略代码",
                "warnings": [],
                "validation_only": True,
                "execution_enabled": False,
            }
        warnings: list[str] = []
        blocked_reasons: list[str] = []
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return {
                "ok": False,
                "message": f"语法错误: {exc}",
                "warnings": warnings,
                "blocked_reasons": ["语法错误"],
                "validation_only": True,
                "execution_enabled": False,
            }
        forbidden = {"exec", "eval", "open", "compile", "__import__", "subprocess", "socket", "requests", "os", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                blocked_reasons.append("当前版本不允许自定义策略中使用 import")
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in forbidden:
                    blocked_reasons.append(f"检测到潜在不安全调用: {name}")
        has_func = any(isinstance(n, ast.FunctionDef) and n.name == "score" for n in tree.body)
        if not has_func:
            warnings.append("建议定义 score(context) 函数，返回 0-100 分或包含 score/tags/risk 的字典。")
        blocked_reasons = list(dict.fromkeys(blocked_reasons))
        return {
            "ok": not blocked_reasons,
            "message": "自定义策略代码结构检查完成" if not blocked_reasons else "自定义策略代码未通过安全结构检查",
            "warnings": list(dict.fromkeys(warnings)),
            "blocked_reasons": blocked_reasons,
            "validation_only": True,
            "execution_enabled": False,
        }
