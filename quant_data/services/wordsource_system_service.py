from __future__ import annotations
from typing import Any
from quant_data.models import Quote, Bar
from quant_data.services.source_registry import SourceRegistryService
from quant_data.services.technical_factor_registry import TechnicalFactorRegistryService
from quant_data.services.data_quality_service import DataQualityService
from quant_data.services.capital_flow_service import CapitalFlowService
from quant_data.services.style_classifier import StyleClassifierService
from quant_data.services.theme_lifecycle_service import ThemeLifecycleService
from quant_data.services.position_risk_service import PositionRiskService
from quant_data.services.strategy_signal_service import StrategySignalService
from quant_data.services.diagnosis_engine import DiagnosisEngine
from quant_data.services.macro_policy_event_service import MacroPolicyEventService
from quant_data.services.research_sentiment_service import ResearchReportService, SentimentObserverService
from quant_data.services.feature_store_service import FeatureStoreService


def _score_from_indicator_snapshot(snapshot: dict) -> dict:
    entries = snapshot.get("entries") or []
    by_dim = snapshot.get("by_dimension") or {}
    computed = snapshot.get("implemented_count") or snapshot.get("computed_count") or 0
    total = snapshot.get("count") or len(entries) or 1
    coverage = computed / max(1, total) * 100
    return {"technical_score": round(min(100, 45 + coverage * 0.35), 2), "coverage_pct": round(coverage, 2), "dimension_count": {k: len(v) if isinstance(v, list) else v for k, v in by_dim.items()}}


class WordSourceSystemService:
    """把四个Word文档要求落到可运行的综合报告服务。

    输入为当前系统已能拿到的 Quote/K线/新闻文本，输出完整的：
    信息源规划、技术因子库、四面评分、资金/风格/题材/风控、策略信号、数据质量和脚本复核。
    """
    def __init__(self, feature_store_path: str = "data/feature_store.sqlite") -> None:
        self.sources = SourceRegistryService()
        self.factor_registry = TechnicalFactorRegistryService()
        self.quality = DataQualityService()
        self.capital = CapitalFlowService()
        self.style = StyleClassifierService()
        self.theme = ThemeLifecycleService()
        self.position_risk = PositionRiskService()
        self.strategy = StrategySignalService()
        self.diagnosis = DiagnosisEngine()
        self.macro = MacroPolicyEventService()
        self.research = ResearchReportService()
        self.sentiment = SentimentObserverService()
        self.feature_store = FeatureStoreService(feature_store_path)

    def build_report(
        self,
        q: Quote,
        bars: list[Bar],
        indicator_snapshot: dict | None = None,
        base_score: float | None = None,
        tags: list[str] | None = None,
        risk_flags: list[str] | None = None,
        news_items: list[dict] | None = None,
    ) -> dict:
        tags = tags or []
        risk_flags = risk_flags or []
        news_items = news_items or []
        evidence_text = " ".join(str(x.get("title", "")) + " " + str(x.get("summary", x.get("content", ""))) for x in news_items[:80])
        quote_quality = self.quality.assess_quote(q)
        bar_quality = self.quality.assess_bars(bars, expected_min=120)
        news_quality = self.quality.assess_news(news_items)
        capital = self.capital.analyze(q, bars)
        style = self.style.classify(q, bars)
        theme = self.theme.analyze(q, evidence_text)
        technical = _score_from_indicator_snapshot(indicator_snapshot or {})
        macro_policy = self.macro.classify_text(evidence_text)
        research = self.research.parse(evidence_text)
        sentiment = self.sentiment.analyze_texts([str(x.get("title", "")) + " " + str(x.get("summary", x.get("content", ""))) for x in news_items if "股吧" in str(x.get("source", "")) or "雪球" in str(x.get("source", ""))])
        info_score = min(100, 35 + news_quality.get("quality_score", 0) * 0.45 + (8 if macro_policy.get("has_macro_policy") else 0) + (8 if research.get("is_research_like") else 0))
        fundamental_score = self._fundamental_score(q, news_items)
        four_surface_scores = {
            "technical": technical.get("technical_score", 50),
            "fundamental": fundamental_score,
            "information": round(info_score, 2),
            "capital": capital.get("capital_score", 50),
        }
        final = self._final_score(base_score, four_surface_scores, risk_flags, quote_quality, bar_quality, news_quality)
        evidence = {
            "has_policy": bool(macro_policy.get("events")) or any("政策" in str(x) for x in tags),
            "has_industry": bool(theme.get("themes")) and theme.get("themes") != ["未识别题材"],
            "has_fundamental": bool(fundamental_score != 50 or any(str(x.get("event_type", "")).startswith("financial") for x in news_items)),
        }
        diagnosis = self.diagnosis.diagnose(q, base_score if base_score is not None else final, {"capital_score": capital.get("capital_score", 0), "theme_score": theme.get("theme_score", 0), "technical_score": technical.get("technical_score", 0)}, tags, risk_flags, evidence)
        position = self.position_risk.analyze(q, bars, risk_flags)
        strategies = self.strategy.generate(q, bars, info_score=info_score)
        source_plan = self.sources.plan_for_target(120)
        report = {
            "version": "3.16-wordsource-v1-complete",
            "symbol": q.symbol,
            "name": q.name,
            "source_system": {
                "registry_coverage": self.sources.coverage_matrix(),
                "source_plan": source_plan,
                "disabled_sources": self.sources.disabled_sources(),
            },
            "data_quality": {"quote": quote_quality, "kline": bar_quality, "news": news_quality},
            "factor_library": self.factor_registry.coverage(),
            "technical": technical,
            "fundamental": {"fundamental_score": fundamental_score, "basis": "由PE/PB、公告/财报事件、风险词初步结构化；完整财报字段由公司画像继续补充。"},
            "information": {"information_score": round(info_score, 2), "macro_policy": macro_policy, "research": research, "sentiment": sentiment},
            "capital": capital,
            "style": style,
            "theme": theme,
            "four_surface_scores": four_surface_scores,
            "final_score_wordsource": final,
            "diagnosis": diagnosis,
            "position_risk": position,
            "strategy_signals": strategies,
            "completion_statement": "本报告各模块均有可运行计算逻辑；对于Level-2/Tick/实盘券商等当前无真实数据授权的项目，系统明确不伪造，并以数据质量字段记录缺口。",
        }
        try:
            qscore = min(100, (quote_quality.get("quality_score",0)+bar_quality.get("quality_score",0)+news_quality.get("quality_score",0))/3)
            self.feature_store.put(q.symbol, "wordsource_report", report, qscore)
        except Exception:
            pass
        return report

    def _fundamental_score(self, q: Quote, news_items: list[dict]) -> float:
        score = 50.0
        pe = q.pe_dynamic
        pb = q.pb
        try:
            if pe is not None:
                pef = float(pe)
                if 0 < pef <= 20: score += 12
                elif 20 < pef <= 45: score += 4
                elif pef > 80: score -= 10
            if pb is not None:
                pbf = float(pb)
                if 0 < pbf <= 1.5: score += 8
                elif pbf > 6: score -= 8
        except Exception:
            pass
        text = " ".join(str(x.get("title", "")) + str(x.get("summary", x.get("content", ""))) for x in news_items[:80])
        if any(k in text for k in ["预增", "增长", "扭亏", "中标", "重大合同", "回购", "增持"]): score += 8
        if any(k in text for k in ["亏损", "预减", "问询", "处罚", "减持", "质押", "诉讼", "退市", "ST"]): score -= 12
        return round(max(0, min(100, score)), 2)

    def _final_score(self, base_score, scores: dict, risk_flags: list[str], quote_quality: dict, bar_quality: dict, news_quality: dict) -> float:
        if base_score is None:
            base = scores["technical"]*0.35 + scores["fundamental"]*0.20 + scores["information"]*0.25 + scores["capital"]*0.20
        else:
            base = base_score*0.55 + (scores["fundamental"]*0.15 + scores["information"]*0.15 + scores["capital"]*0.15)
        qpen = max(0, 70-quote_quality.get("quality_score",0))*0.05 + max(0, 70-bar_quality.get("quality_score",0))*0.06 + max(0, 60-news_quality.get("quality_score",0))*0.04
        rpen = min(20, len(risk_flags)*2.5)
        return round(max(0, min(100, base-qpen-rpen)), 2)
