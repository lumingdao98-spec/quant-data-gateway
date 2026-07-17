from __future__ import annotations

from datetime import datetime
from typing import Any

from quant_data.models import AssetType, Quote
from quant_data.services.market_data_service import MarketDataService
from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.fundamental_library_service import FundamentalLibraryService
from quant_data.services.company_profile_service import CompanyProfileService
from quant_data.services.global_industry_mapper import GlobalIndustryMapper
from quant_data.utils import normalize_symbol, safe_float


class InfoAnalysisService:
    """信息面 + 技术面整合分析。

    当前版本优先整合：中文新闻/公告、估值与交易快照、可选 AKShare 财务摘要。
    AKShare 未安装或接口变化时自动降级，不影响主系统运行。
    """

    def __init__(self, market_data: MarketDataService, news_service: NewsAnalysisService) -> None:
        self.market_data = market_data
        self.news_service = news_service
        self.fundamental_library = FundamentalLibraryService()
        self.company_profile_service = CompanyProfileService()
        self.global_mapper = GlobalIndustryMapper()

    def analyze(self, symbol: str, name: str | None = None, limit: int = 120, force: bool = False, mode: str = "normal", deep_refresh: bool = False, allow_network: bool = True) -> dict[str, Any]:
        symbol = normalize_symbol(symbol)
        mode_raw = str(mode or "normal").lower()
        mode = "deep" if deep_refresh or mode_raw in {"deep", "deep_refresh", "full"} else "light" if mode_raw == "light" else "normal"
        quote: Quote | None = None
        # The screening path already owns quote/technical scoring. Re-fetching
        # the quote here added several seconds per candidate and duplicated
        # public endpoint traffic, so light mode remains news/profile-only.
        if mode != "light":
            try:
                quote = self.market_data.get_quote(symbol, force_refresh=force)
            except Exception:
                quote = None
        qname = name or (quote.name if quote else symbol)
        news = self.news_service.analyze(
            symbol,
            name=qname,
            limit=limit,
            force=force or deep_refresh,
            mode=mode,
            budget_seconds=(
                10.0
                if mode == "light" and force and allow_network
                else 8.0
                if mode == "deep"
                else 5.0
                if mode == "normal"
                else 4.0
            ),
            allow_network=allow_network,
        )
        # 公司画像只在 force=true 或本地缓存过期时主动刷新；全球/国内要闻按短缓存自动刷新。
        profile = self.company_profile_service.get_profile(
            symbol,
            force=(force and mode != "light"),
            local_only=(mode == "light"),
        )
        global_news = self._safe_global_news(force=bool(force or deep_refresh)) if mode in {"normal", "deep"} else {"items": [], "cache_info": {"skipped": "light_mode"}}
        global_mapping = self.global_mapper.map_items((global_news or {}).get("items", []), symbol, name=qname, profile=profile)
        finance = self._finance_snapshot(symbol, quote, allow_network=allow_network and mode != "light")
        policy = self._policy_summary(news, qname, symbol, global_news=global_news, profile=profile)
        policy["industry_mapped_items"] = global_mapping.get("industry_mapped_items", [])
        policy["mapped_industries"] = global_mapping.get("mapped_industries", [])
        policy["mapped_concepts"] = global_mapping.get("mapped_concepts", [])
        policy["mapped_symbols"] = global_mapping.get("mapped_symbols", [])
        policy["company_exposure"] = global_mapping.get("company_exposure", {})
        policy["policy_clue_count"] = int(policy.get("policy_clue_count") or 0) + int(global_mapping.get("related_count") or 0)
        related_mapped = [x for x in policy["industry_mapped_items"] if x.get("score_included")]
        if related_mapped:
            adjust = sum(1.5 if x.get("impact_direction") == "positive" else -1.8 if x.get("impact_direction") == "negative" else 0.4 for x in related_mapped[:10])
            policy["policy_score"] = round(max(0, min(100, safe_float(policy.get("policy_score"), 50) + adjust)), 2)
        evidence_counts = self._evidence_counts(news, finance, policy)
        info_score = self._info_score(news, finance, policy)
        data_quality = dict(news.get("data_quality") or {})
        data_quality.update({
            "dated_items": evidence_counts.get("dated_items"),
            "unknown_date_items": evidence_counts.get("unknown_date_items"),
            "stored_items_used": news.get("stored_items_used"),
            "stored_items_saved": news.get("stored_items_saved"),
        })
        return {
            "symbol": symbol,
            "name": qname,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "info_score": info_score,
            "news": news,
            "finance": finance,
            "policy": policy,
            "fundamental_framework": self.fundamental_library.checklist(),
            "source_tiers": self.fundamental_library.source_tiers(),
            "message_framework": self._message_framework(),
            "source_policy": self.news_service.message_source_policy() if hasattr(self.news_service, "message_source_policy") else {},
            "company_profile": profile,
            "global_news_used": {
                "count": len((global_news or {}).get("items", [])),
                "related_count": int(global_mapping.get("related_count") or 0),
                "updated_at": (global_news or {}).get("updated_at"),
                "sources_used": (global_news or {}).get("sources_used", []),
                "domestic_count": (global_news or {}).get("domestic_count", 0),
                "global_count": (global_news or {}).get("global_count", 0),
                "commodity_count": (global_news or {}).get("commodity_count", 0),
                "mapped_industries": global_mapping.get("mapped_industries", []),
                "mapped_concepts": global_mapping.get("mapped_concepts", []),
                "mapped_symbols": global_mapping.get("mapped_symbols", []),
                "note": "全球要闻自动短缓存刷新；只有与公司画像/行业暴露匹配时才进入信息面映射分。",
            },
            "global_items": (global_news or {}).get("items", []),
            "industry_mapped_items": global_mapping.get("industry_mapped_items", []),
            "mapped_industries": global_mapping.get("mapped_industries", []),
            "mapped_concepts": global_mapping.get("mapped_concepts", []),
            "mapped_symbols": global_mapping.get("mapped_symbols", []),
            "evidence_counts": evidence_counts,
            "policy_clue_count": policy.get("policy_clue_count", 0),
            "data_quality": data_quality,
            "cache_info": news.get("cache_info") or {},
            "crawl_mode": mode,
            "deep_refresh": bool(deep_refresh),
            "breakdown": [
                {"name": "公司/公告事件", "score": news.get("news_score", 50), "weight": 0.30},
                {"name": "来源可信度", "score": news.get("avg_credibility") or 50, "weight": 0.10},
                {"name": "财报/估值", "score": finance.get("finance_score", 50), "weight": 0.16},
                {"name": "前沿要闻/行业映射", "score": policy.get("policy_score", 50), "weight": 0.36},
                {"name": "传闻噪声惩罚", "score": max(0, 100 - safe_float(news.get("avg_fake_risk"), 20)), "weight": 0.08},
            ],
            "scoring_model": self._scoring_model(),
            "summary": self._summary(news, finance, policy, info_score),
            "risk_flags": list(dict.fromkeys((news.get("risk_flags") or []) + (finance.get("risk_flags") or []) + (policy.get("risk_flags") or []))),
            "time_counts": news.get("time_counts", []),
            "reuse_note": "个股新闻/公告有短缓存和长期信息库；force=true 会重新抓取并按事件级规则重算。全球/国内/前沿要闻为短缓存，并按行业关键词映射到所选标的；若启用信息面评分，会同步进入筛选综合分。",
            "scoring_note": news.get("scoring_note") or "可信度与情绪为规则化辅助评分，必须结合公告原文与财报人工核验。",
            "note": "信息面评分由中文新闻/公告、估值财务快照、政策行业关键词综合得到；非投资建议。",
        }

    def _message_framework(self) -> dict[str, Any]:
        return {
            "宏观经济消息": ["货币政策", "财政政策", "GDP/CPI/PPI/PMI", "利率/汇率", "社融/M2/逆回购"],
            "行业消息": ["行业政策", "技术突破", "竞争格局", "供需变化", "价格变化"],
            "公司消息": ["财报业绩", "重大合同", "并购重组", "管理层变动", "监管问询", "诉讼处罚"],
            "市场资金面消息": ["央行操作", "机构持仓", "基金重仓", "北向资金", "龙虎榜", "融资融券"],
            "国际消息": ["美联储", "美元/美债", "地缘政治", "贸易摩擦", "原油/黄金/大宗商品"],
            "社会舆情": ["股吧/雪球热度", "传闻风险", "观点分歧", "恐慌/贪婪情绪"],
            "说明": "消息面评分必须结合来源可靠性、时效性、事件新颖度、与标的/行业相关度；搜索引擎关键词页不作为证据。",
        }

    def _scoring_model(self) -> dict[str, Any]:
        return {
            "信息面分公式": "0.30×公司/公告事件 + 0.10×来源可信度 + 0.16×财报估值 + 0.36×全球/国内要闻相关映射 + 0.08×(100-传闻噪声) - 官方负面惩罚",
            "筛选融合公式": "启用信息面评分后：综合分 = 技术/量价底分×(1-信息权重) + 信息面分×信息权重；信息面融合模式/前沿要闻映射较强时权重更高。",
            "前沿要闻": "全球/国内/商品/政策快讯先映射行业和产业链，再结合个股主营判断。降息、加息、原油、黄金、关税、地缘、出口管制、AI/芯片/新能源等会形成行业加减分，但不会替代公司公告。",
        }

    def _safe_global_news(self, force: bool = False) -> dict[str, Any]:
        try:
            return self.news_service.fetch_global_news(limit=80, force=force, ttl_seconds=90)
        except Exception as exc:
            return {"items": [], "error": str(exc)[:160]}

    def _finance_snapshot(self, symbol: str, q: Quote | None, allow_network: bool = True) -> dict[str, Any]:
        qd: dict[str, Any] = {}
        if q is not None:
            qd = q.to_dict()
        pe = safe_float(qd.get("pe_dynamic"), 0)
        pb = safe_float(qd.get("pb"), 0)
        cap = safe_float(qd.get("total_market_cap"), 0)
        amount = safe_float(qd.get("amount"), 0)
        turnover = qd.get("turnover")
        score = 50.0
        tags: list[str] = []
        risks: list[str] = []
        if q and q.asset_type == AssetType.ETF:
            score = 62.0 if amount >= 50_000_000 else 50.0
            tags.append("ETF以流动性和趋势为主，弱化PE/PB")
        else:
            if 0 < pe <= 35:
                score += 8; tags.append("动态PE处于可观察区间")
            elif pe > 80:
                score -= 10; risks.append("动态PE偏高")
            elif pe <= 0:
                score -= 14; risks.append("动态PE异常或亏损")
            if 0 < pb <= 8:
                score += 5; tags.append("PB未见明显异常")
            elif pb > 12:
                score -= 6; risks.append("PB偏高")
            if cap >= 50_000_000_000:
                score += 5; tags.append("市值规模较高")
            if amount >= 200_000_000:
                score += 5; tags.append("成交额较活跃")
            elif amount and amount < 30_000_000:
                score -= 6; risks.append("成交额偏低")
        ak = self._try_akshare_financial(symbol) if allow_network else {
            "available": False,
            "missing_reason": "轻量筛选复用已有基本面评分，不重复请求财务接口",
        }
        if ak.get("available"):
            # 如果可获得 AKShare 财务摘要，使用最近一期增长指标修正评分。
            if ak.get("profit_growth") is not None:
                pg = safe_float(ak.get("profit_growth"), 0)
                if pg > 15:
                    score += 7; tags.append("净利润增长较好")
                elif pg < -10:
                    score -= 10; risks.append("净利润同比承压")
            if ak.get("net_profit") is not None and safe_float(ak.get("net_profit"), 0) < 0:
                score -= 12; risks.append("最近一期归母净利润为负")
            if ak.get("revenue_growth") is not None:
                rg = safe_float(ak.get("revenue_growth"), 0)
                if rg > 10:
                    score += 5; tags.append("营收增长较好")
                elif rg < -10:
                    score -= 5; risks.append("营收同比承压")
        else:
            tags.append("未启用AKShare财务摘要，当前以行情估值快照评估")
        return {
            "finance_score": round(max(0, min(100, score)), 2),
            "pe_dynamic": pe or None,
            "pb": pb or None,
            "total_market_cap": cap or None,
            "amount": amount or None,
            "turnover": turnover,
            "tags": tags,
            "risk_flags": risks,
            "akshare": ak,
        }

    def _try_akshare_financial(self, symbol: str) -> dict[str, Any]:
        try:
            import akshare as ak  # type: ignore
        except Exception:
            return {"available": False, "reason": "未安装 akshare，可选安装 pip install akshare 获取更多财务摘要"}
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            if df is None or len(df) == 0:
                return {"available": False, "reason": "AKShare未返回财务指标"}
            row = df.iloc[0].to_dict()
            def find(keys: list[str]):
                for k, v in row.items():
                    sk = str(k)
                    if any(x in sk for x in keys):
                        try:
                            return float(str(v).replace('%','').replace(',',''))
                        except Exception:
                            pass
                return None
            return {
                "available": True,
                "report_date": str(row.get("日期") or row.get("报告期") or ""),
                "revenue_growth": find(["营业收入增长率", "主营业务收入增长率", "营收"]),
                "profit_growth": find(["净利润增长率", "扣非净利润增长率", "净利润"]),
                "roe": find(["净资产收益率", "ROE"]),
                "net_profit": find(["归母净利润", "净利润"]),
                "source": "akshare.stock_financial_analysis_indicator",
            }
        except Exception as exc:
            return {"available": False, "reason": f"AKShare财务接口失败：{str(exc)[:120]}"}

    def _stock_exposure_text(self, symbol: str, name: str, news: dict[str, Any]) -> str:
        """生成“当前标的行业/主营暴露”文本，供全球要闻映射使用。

        仅靠股票简称往往判断不到行业，例如“通威股份”标题本身不含“光伏/硅料”。
        这里用本地常见公司映射 + 已抓新闻行业标签 + 关键词，避免全球新闻无法影响个股评分。
        """
        symbol = str(symbol or "")
        base = f"{name} {symbol}"
        known = {
            "600438": "通威股份 光伏 硅料 多晶硅 太阳能 电池片 组件 新能源 农牧 饲料",
            "300750": "宁德时代 动力电池 锂电 储能 新能源车 电池 新能源",
            "600519": "贵州茅台 白酒 高端消费 食品饮料 消费",
            "000858": "五粮液 白酒 高端消费 食品饮料 消费",
            "601318": "中国平安 保险 金融 银行 券商 大盘蓝筹",
            "600036": "招商银行 银行 金融 低估值 大盘蓝筹",
            "159915": "创业板ETF 创业板 成长股 新能源 医药 科技 宽基ETF",
            "510300": "沪深300ETF 沪深300 宽基ETF 大盘蓝筹 金融 消费 新能源",
        }
        if symbol in known:
            base += " " + known[symbol]
        for item in (news.get("items") or [])[:120]:
            base += " " + str(item.get("title", "")) + " " + str(item.get("summary", "")) + " " + " ".join(item.get("industry_tags") or [])
        # 简单公司名/行业别名兜底。
        alias_map = {
            "通威": "光伏 硅料 太阳能 新能源 农牧 饲料",
            "茅台": "白酒 消费 食品饮料",
            "宁德": "动力电池 锂电 储能 新能源车",
            "隆基": "光伏 组件 硅片 新能源",
            "中芯": "半导体 芯片 国产替代",
            "比亚迪": "新能源车 动力电池 汽车",
        }
        for k, v in alias_map.items():
            if k in base:
                base += " " + v
        return base

    def _policy_summary(self, news: dict[str, Any], name: str = "", symbol: str = "", global_news: dict[str, Any] | None = None, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        items = news.get("items") or []
        policy_items = []
        for item in items:
            cat = item.get("category")
            text = f"{item.get('title','')} {item.get('summary','')}"
            if cat == "政策行业" or any(w in text for w in ["政策", "监管", "补贴", "出口", "关税", "产业", "规划", "工信部", "发改委", "国资委", "军工", "低空经济", "机器人", "新能源", "芯片", "AI"]):
                policy_items.append(item)
        score = 50.0
        risks: list[str] = []
        tags: list[str] = []
        for item in policy_items:
            s = safe_float(item.get("sentiment_score"), 50)
            if s >= 60:
                score += 5
            elif s <= 40:
                score -= 6
            title = str(item.get("title", ""))
            if any(w in title for w in ["监管", "处罚", "问询", "调查", "立案"]):
                risks.append("存在监管/政策风险信息")
            else:
                tags.append("存在政策/行业催化信息")
        # 名称/行业关键词兜底：不把它当成新闻条数，只作为“行业线索”提示，避免政策信息永远为0。
        text_all = f"{name} {symbol} " + " ".join([str(x.get("title", "")) for x in items])
        industry_map = {
            "军工": ["军工", "兵器", "弹药", "航天", "航空", "国防", "舰船"],
            "机器人": ["机器人", "减速器", "伺服", "人形"],
            "新能源": ["新能源", "电池", "锂", "储能", "充电桩", "新能源车"],
            "光伏": ["光伏", "硅料", "多晶硅", "硅片", "组件", "太阳能", "电池片"],
            "半导体": ["芯片", "半导体", "光刻", "集成电路"],
            "人工智能": ["AI", "人工智能", "算力", "大模型", "数据中心"],
            "低空经济": ["低空", "无人机", "eVTOL", "通航"],
            "消费医药": ["医药", "医疗", "白酒", "食品", "消费"],
            "资源品": ["黄金", "有色", "铜", "铝", "煤炭", "原油", "油气"],
            "金融地产": ["银行", "券商", "保险", "地产", "房地产", "家居", "建材"],
        }
        industry_signals = []
        for ind, keys in industry_map.items():
            if any(k in text_all for k in keys):
                industry_signals.append(ind)
        if industry_signals:
            score += min(8, 2 * len(industry_signals))
            tags.append("行业线索：" + "、".join(industry_signals[:4]))
        # 将全球/国内宏观快讯按行业关键词映射到当前标的，不能直接当个股新闻，只作为行业/市场影响线索。
        mapped_global = []
        global_items = (global_news or {}).get("items", []) if isinstance(global_news, dict) else []
        for gi in global_items[:80]:
            gtext = f"{gi.get('title','')} {gi.get('summary','')} {' '.join(gi.get('industry_tags') or [])}"
            matched = [ind for ind in industry_signals if ind and ind in gtext]
            if not matched:
                for ind, keys in industry_map.items():
                    if ind in industry_signals and any(k in gtext for k in keys):
                        matched.append(ind)
            if matched:
                mapped_global.append({"title": gi.get("title"), "source": gi.get("source"), "sentiment_label": gi.get("sentiment_label"), "impact_direction": gi.get("impact_direction"), "industry": list(dict.fromkeys(matched))[:3], "published_at": gi.get("published_at") or gi.get("date_display")})
                if gi.get("sentiment_label") == "正面":
                    score += 1.2
                elif gi.get("sentiment_label") == "负面":
                    score -= 1.5
        macro_event_maps = []
        profile = profile or {}
        profile_text = " ".join([
            str(profile.get("industry") or ""),
            str(profile.get("main_business") or ""),
            str(profile.get("business_scope") or ""),
            str(profile.get("industry_exposure_text") or ""),
            " ".join(profile.get("business_tags") or []),
            " ".join(profile.get("main_products") or []),
            " ".join(profile.get("upstream") or []),
            " ".join(profile.get("downstream") or []),
            " ".join(profile.get("business_segments") or []),
        ])
        stock_text = self._stock_exposure_text(symbol, name, news) + " " + profile_text + " " + " ".join(industry_signals)
        for gi in global_items[:120]:
            ev_map = self.fundamental_library.map_event_to_industries(f"{gi.get('title','')} {gi.get('summary','')}", stock_text=stock_text)
            if ev_map.get("matched"):
                macro_event_maps.append({
                    "title": gi.get("title"),
                    "source": gi.get("source"),
                    "direction": ev_map.get("direction"),
                    "positive_industries": ev_map.get("positive_industries"),
                    "negative_industries": ev_map.get("negative_industries"),
                    "direct_relevance": ev_map.get("direct_relevance"),
                    "rules": ev_map.get("matched"),
                })
                direction = ev_map.get("direction")
                if direction == "偏利好":
                    score += 2.8
                elif direction == "偏利空":
                    score -= 3.2
                elif direction == "影响分化":
                    score -= 0.6
        if mapped_global:
            tags.append(f"全球/国内要闻映射 {len(mapped_global)} 条")
        if macro_event_maps:
            tags.append(f"宏观/商品事件映射 {len(macro_event_maps)} 条")
        score = max(0, min(100, score))
        policy_clue_count = len(policy_items) + len(industry_signals) + len(mapped_global) + len(macro_event_maps)
        return {
            "policy_score": round(score, 2),
            "policy_count": len(policy_items),
            "policy_clue_count": policy_clue_count,
            "industry_signals": industry_signals,
            "company_business_tags": profile.get("business_tags", []) if isinstance(profile, dict) else [],
            "company_main_products": profile.get("main_products", []) if isinstance(profile, dict) else [],
            "mapped_global_items": mapped_global[:12],
            "macro_event_maps": macro_event_maps[:12] if 'macro_event_maps' in locals() else [],
            "industry_event_rules_used": self.fundamental_library.industry_event_rules(),
            "source_tiers": self.fundamental_library.source_tiers(),
            "tags": list(dict.fromkeys(tags)),
            "risk_flags": list(dict.fromkeys(risks)),
            "items": policy_items[:12],
            "note": "policy_count 只统计实际抓取到的政策/行业/全球相关信息；policy_clue_count = 政策/行业/全球相关信息 + 行业线索 + 全球/国内要闻行业映射。行业映射只提示可能影响方向，不等同于个股公告。",
        }


    def _evidence_counts(self, news: dict[str, Any], finance: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        items = news.get("items") or []
        news_neg = int(news.get("negative_count") or 0)
        official_neg = int(news.get("official_negative_count") or 0)
        finance_neg = len(finance.get("risk_flags") or [])
        policy_neg = len(policy.get("risk_flags") or [])
        high_conf = int(news.get("official_count") or 0)
        return {
            "news_negative": news_neg,
            "official_negative": official_neg,
            "finance_negative": finance_neg,
            "policy_negative": policy_neg,
            "negative_evidence": news_neg + finance_neg + policy_neg,
            "high_confidence_items": high_conf,
            "dated_items": sum(1 for x in items if x.get("published_at_norm") or x.get("published_at")),
            "unknown_date_items": int(news.get("date_unknown_count") or 0),
            "item_count": len(items),
            "note": "news_negative 只统计新闻/公告文本情绪；finance_negative 单独统计估值、亏损等财报风险，因此财报亏损不会强行计入新闻负面条数，但会计入信息面负面证据。"
        }

    def _info_score(self, news: dict[str, Any], finance: dict[str, Any], policy: dict[str, Any]) -> float:
        # V3.12：信息面不再只是标题情绪。按“公司/公告事件、来源可信度、财报估值、前沿要闻行业映射、传闻噪声”综合。
        ns = safe_float(news.get("news_score"), 50)
        cred = safe_float(news.get("avg_credibility"), 50)
        fs = safe_float(finance.get("finance_score"), 50)
        ps = safe_float(policy.get("policy_score"), 50)
        fake = safe_float(news.get("avg_fake_risk"), 20)
        raw = ns * 0.30 + cred * 0.10 + fs * 0.16 + ps * 0.36 + max(0, 100 - fake) * 0.08
        # 官方/高可信负面事件额外惩罚；全球/商品/国际事件若与行业直接相关，短线权重提高。
        if int(news.get("official_negative_count") or 0) > 0:
            raw -= min(12, 3.5 * int(news.get("official_negative_count") or 0))
        direct_macro = [x for x in (policy.get("macro_event_maps") or []) if x.get("direction") in {"偏利好", "偏利空", "影响分化"}]
        if direct_macro:
            raw += 3.5 if ps >= 60 else -3.5 if ps <= 40 else 0
        elif len(policy.get("macro_event_maps") or []) >= 3:
            raw += 1.5 if ps >= 58 else -1.5 if ps <= 42 else 0
        return round(max(0, min(100, raw)), 2)

    def _summary(self, news: dict[str, Any], finance: dict[str, Any], policy: dict[str, Any], score: float) -> str:
        tc = news.get("time_counts") or []
        time_txt = "，".join([f"{x.get('name')} {x.get('count')}条" for x in tc[:4]]) or "暂无可解析时间"
        fin_risks = finance.get("risk_flags") or []
        pol_note = "；行业线索 " + "、".join(policy.get("industry_signals") or []) if policy.get("industry_signals") else ""
        evidence = self._evidence_counts(news, finance, policy)
        neg_note = f"；信息面负面证据 {evidence.get('negative_evidence',0)} 项" if evidence.get('negative_evidence',0) else ""
        cache = news.get("cache_info") or {}
        cache_note = "复用缓存" if cache.get("hit") else "本次更新"
        return (
            f"信息面评分 {score:.1f}。"
            f"{news.get('summary','')} "
            f"时间分布：{time_txt}。"
            f"财报/估值评分 {finance.get('finance_score','--')}"
            f"{'，风险：' + '、'.join(fin_risks[:3]) if fin_risks else ''}；"
            f"政策/行业/全球相关信息 {policy.get('policy_count',0)} 条，政策/行业线索 {policy.get('policy_clue_count',0)} 项{pol_note}{neg_note}。"
            f" 信息库状态：{cache_note}。"
        )
