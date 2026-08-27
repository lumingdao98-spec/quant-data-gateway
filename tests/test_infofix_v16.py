from datetime import datetime, timedelta

from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.news_store_service import NewsStoreService
from quant_data.models import Quote, Bar, AssetType
from quant_data.services.screener_service import ScreenerService
from quant_data.services.market_data_service import MarketDataService


def test_v16_rejects_boilerplate_titles_and_html_fragments():
    svc = NewsAnalysisService()
    bad_titles = [
        "桌面快捷方式", "加入自选股", "客户端", "关于同花顺", "软件下载", "法律声明",
        "Copyright 2026", "header.js", "pagehead", "div class layui-table", "友情链接", "招聘英才",
    ]
    for title in bad_titles:
        ok, reason = svc.valid_news_item(title, "<script src='header.js'></script>", source="同花顺个股资讯", symbol="688599", name="天合光能", base_relevant=True)
        assert not ok, (title, reason)


def test_v328_rejects_stream_section_headers_as_news():
    svc = NewsAnalysisService()
    ok, reason = svc.valid_news_item(
        "期货热点追踪",
        "期货热点追踪",
        source="金十数据7x24",
        url="https://flash.jin10.com/detail/section-header",
        source_type="macro",
        allow_macro=True,
    )

    assert ok is False
    assert reason == "boilerplate_or_invalid_title"


def test_v16_distinguishes_publish_event_and_crawl_time():
    svc = NewsAnalysisService()
    item = svc._score_item(
        "天合光能：将于2026年05月21日召开2025年年度股东大会",
        "https://example.com/notice.html?id=abc123",
        "东方财富F10",
        "2026-05-01 09:30:00",
        "公告显示，公司将于2026年05月21日召开2025年年度股东大会。",
        "688599",
        "天合光能",
        source_type="announcement",
    )
    assert item.publish_time.startswith("2026-05-01")
    assert item.published_at_norm == "2026-05-01"
    assert item.event_time == "2026-05-21"
    assert item.crawl_time
    assert item.time_confidence == "L1"
    assert item.event_type == "shareholder_meeting"
    assert item.period == "2025年度"


def test_v16_event_cluster_dedup_ignores_media_title_variation():
    svc = NewsAnalysisService()
    a = svc._score_item(
        "天合光能：将于2026年05月21日召开2025年年度股东大会",
        "https://example.com/a",
        "东方财富F10",
        "2026-05-01",
        "天合光能将于2026年05月21日召开2025年年度股东大会",
        "688599",
        "天合光能",
        source_type="announcement",
    )
    b = svc._score_item(
        "同花顺资讯：天合光能2025年度股东大会会议日期为2026年05月21日",
        "https://example.com/b",
        "同花顺个股资讯",
        "2026-05-02",
        "天合光能2025年度股东大会将于2026年05月21日召开",
        "688599",
        "天合光能",
        source_type="news",
    )
    assert a.event_key == b.event_key
    got = svc._deduplicate([a, b])
    assert len(got) == 1
    assert "同事件合并" in got[0].dedup_reason


def test_v16_store_filters_invalid_before_insert(tmp_path):
    svc = NewsAnalysisService(cache_file=tmp_path / "cache.json")
    store = NewsStoreService(tmp_path / "news.sqlite")
    bad = {"title": "关于同花顺", "summary": "软件下载 header.js", "source": "同花顺个股资讯", "source_type": "news", "duplicate_group": "bad"}
    good = svc._score_item("天合光能发布2025年度股东大会公告", "https://example.com/good.html", "东方财富F10", "2026-05-01", "天合光能公告显示股东大会事项", "688599", "天合光能", source_type="announcement")
    assert store.upsert_items("688599", "天合光能", [bad, good]) == 1
    rows = store.list_items("688599")
    assert len(rows) == 1
    assert rows[0]["event_type"] in {"shareholder_meeting", "announcement"}


def test_v16_drawdown_formula_uses_current_close_over_high250():
    q = Quote(
        symbol="000001", name="测试", ts=datetime.now(), last=80, pre_close=79, open=80, high=82, low=78,
        volume=1000, amount=100000, change=1, change_pct=1.2, asset_type=AssetType.STOCK,
    )
    start = datetime.now() - timedelta(days=260)
    bars = []
    for i in range(260):
        price = 100 if i == 30 else 80
        bars.append(Bar(symbol="000001", frame="1d", ts=start + timedelta(days=i), open=price, high=price, low=price, close=price, volume=1, amount=1, source="unit:qfq"))
    result = ScreenerService(MarketDataService()).analyze(q, bars, kline_adjust="qfq")
    assert result.drawdown250 == -20.0
    assert result.drawdown_basis["adjust"] == "qfq"


def test_v16_snapshot_id_helper_contract():
    from quant_data.api import _make_snapshot_id
    sid = _make_snapshot_id("688599", 180)
    assert sid.startswith("snap-")
    assert "688599" in sid and sid.endswith("180")


def test_v328_info_page_defaults_to_compact_evidence_pagination():
    from quant_data.info_ui import build_info_ui

    html = build_info_ui()
    assert 'id="pageSize" type="number" value="15"' in html
    assert "Number($('pageSize').value)||15" in html


def test_v16_1_rejects_stockpage_menu_and_table_fragments():
    svc = NewsAnalysisService()
    cases = [
        ("个股研报", 'padding-left:695px;"> 业绩预测 业绩预测详表 个股研报 同行业研报 --> 行业地位 行业新闻'),
        ("主力持仓", 'ref="/600438/news/">新闻公告 财务分析 经营分析 股东股本 主力持仓 公司大事 分红融资 价值分析 行业分析 行情走势'),
        ("现金流量表", 'playtype/4.p " target="_blank">资产负债表 利润表 现金流量表 业绩预告 杜邦分析 股东权'),
        ("公司资料", '45.02|7.77 首页概览 资金流向 公司资料 新闻公告 财务分析 经营分析 股东股本 主力持仓 公司大事'),
    ]
    for title, summary in cases:
        ok, reason = svc.valid_news_item(title, summary, source="同花顺个股资讯", url="https://stockpage.10jqka.com.cn/600438/news/", symbol="600438", name="通威股份", source_type="news", base_relevant=True)
        assert not ok, (title, reason)


def test_v16_1_research_report_sentiment_and_menu_separation():
    svc = NewsAnalysisService()
    item = svc._score_item(
        "通威股份：首次覆盖给予买入评级，硅料盈利有望修复",
        "https://finance.sina.com.cn/stock/report/2026-05-21/doc-test.shtml",
        "新浪个股新闻",
        "2026-05-21",
        "研报认为通威股份盈利能力改善，上调目标价，维持买入评级。",
        "600438",
        "通威股份",
        source_type="news",
    )
    assert item.source_type == "research"
    assert item.sentiment_label == "正面"
    assert item.sentiment_score >= 58
    assert item.category == "研报观点"


def test_v16_1_forum_sentiment_is_observed_but_not_forced_neutral():
    svc = NewsAnalysisService()
    item = svc._score_item(
        "通威股份股吧热议：净利润下降亏损风险引发担忧",
        "https://guba.eastmoney.com/news,600438,test.html",
        "东方财富股吧",
        "2026-05-21",
        "社区投资者讨论公司业绩亏损、净利润下降和减持风险，需等待公告核验。",
        "600438",
        "通威股份",
        source_type="forum",
    )
    assert item.category == "社区舆情"
    assert item.sentiment_label == "负面"
    assert item.sentiment_score <= 45
    assert item.fake_risk_score >= 58


def test_v16_1_store_uses_event_key_to_remove_old_duplicate_groups(tmp_path):
    svc = NewsAnalysisService(cache_file=tmp_path / "cache.json")
    store = NewsStoreService(tmp_path / "news.sqlite")
    a = svc._score_item("通威股份：北京金杜律师事务所关于2025年年度股东会之法律意见书", "https://example.com/a.pdf?id=same-doc", "巨潮资讯公告", "2026-05-21", "通威股份2025年年度股东会法律意见书", "600438", "通威股份", source_type="announcement")
    b = svc._score_item("通威股份 ：北京金杜律师事务所关于 通威股份 有限公司 2025年年度股东会之法律意见书", "https://example.com/a.pdf?id=same-doc", "东方财富F10", "2026-05-21", "同一公告转载", "600438", "通威股份", source_type="announcement")
    # 模拟旧版本 duplicate_group 不一致但 event_key/doc_id 一致。
    b = type(b)(**{**b.to_dict(), "duplicate_group": "old-different-group", "event_key": a.event_key})
    assert store.upsert_items("600438", "通威股份", [a, b]) == 2
    rows = store.list_items("600438")
    assert len(rows) == 1
    assert rows[0]["event_key"] == a.event_key


def test_v16_2_stockpage_source_extracts_only_deep_valid_articles():
    class DeepSvc(NewsAnalysisService):
        def _fetch_article_detail(self, url: str, max_chars: int = 1800, symbol: str = "", name: str = ""):
            if "c123456789" in url:
                return {
                    "title": "通威股份：硅料业务盈利改善，机构维持买入评级",
                    "text": "通威股份公告及研报显示，公司硅料业务盈利能力改善，机构认为公司成本优势明显，维持买入评级。公司表示将继续推进光伏产业链协同，预计经营质量改善。",
                }
            return {"title": "公司资料", "text": "首页 新闻公告 财务分析 经营分析 股东股本 主力持仓 公司大事 分红融资 价值分析 行业分析 行情走势"}

    svc = DeepSvc()
    html = '''
    <a href="https://stockpage.10jqka.com.cn/600438/company/">公司资料</a>
    <a href="https://stockpage.10jqka.com.cn/600438/news/">新闻公告</a>
    <a href="https://news.10jqka.com.cn/20260521/c123456789.shtml" title="通威股份研报">个股研报</a>
    <a href="https://stockpage.10jqka.com.cn/600438/finance/">现金流量表</a>
    '''
    got = svc._extract_links(html, "600438", "通威股份", "同花顺个股资讯", "news", limit=10, base_url="https://stockpage.10jqka.com.cn/600438/news/", base_relevant=True, strict_article=True, deep_validate=True)
    assert len(got) == 1
    assert got[0].title.startswith("通威股份：硅料业务盈利改善")
    assert got[0].source_type == "research"
    assert got[0].sentiment_label == "正面"


def test_v16_2_deep_validate_rejects_article_like_menu_pages():
    class MenuSvc(NewsAnalysisService):
        def _fetch_article_detail(self, url: str, max_chars: int = 1800, symbol: str = "", name: str = ""):
            return {
                "title": "主力持仓",
                "text": "首页概览 资金流向 公司资料 新闻公告 财务分析 经营分析 股东股本 主力持仓 公司大事 分红融资 价值分析 行业分析 行情走势",
            }

    svc = MenuSvc()
    html = '<a href="https://news.10jqka.com.cn/20260521/c987654321.shtml" title="主力持仓">主力持仓</a>'
    got = svc._extract_links(html, "600438", "通威股份", "同花顺个股资讯", "news", limit=10, base_url="https://stockpage.10jqka.com.cn/600438/news/", base_relevant=True, strict_article=True, deep_validate=True)
    assert got == []


def test_v16_2_sina_stock_nav_pages_fail_url_admission():
    svc = NewsAnalysisService()
    assert not svc._is_probable_article_url("https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/sh600438.phtml", source="新浪个股新闻", title="通威股份资讯")
    assert not svc._is_probable_article_url("https://finance.sina.com.cn/realstock/company/sh600438/nc.shtml", source="新浪个股新闻", title="行情中心")
    assert svc._is_probable_article_url("https://finance.sina.com.cn/stock/relnews/cn/2026-05-21/doc-abc123.shtml", source="新浪个股新闻", title="通威股份公告")


def test_v16_3_indicator50_snapshot_has_no_less_than_50_entries():
    from quant_data.services.trading_framework_service import compute_indicator50_snapshot, tradercore_reference_framework
    closes = [10 + i * 0.05 for i in range(260)]
    highs = [c * 1.02 for c in closes]
    lows = [c * 0.98 for c in closes]
    opens = [c * 0.995 for c in closes]
    volumes = [10000 + i * 10 for i in range(260)]
    amounts = [volumes[i] * closes[i] * 100 for i in range(260)]
    snap = compute_indicator50_snapshot(opens, highs, lows, closes, volumes, amounts)
    assert snap["count"] >= 50
    assert snap["computed_or_estimated_count"] >= 45
    fw = tradercore_reference_framework()
    assert len(fw["candidate_channels"]) == 3
    assert [x["weight"] for x in fw["scoring_layers"]] == [20, 45, 35]


def test_v16_3_screener_result_contains_indicator50_and_tradercore_diagnosis():
    q = Quote(
        symbol="000001", name="测试", ts=datetime.now(), last=12, pre_close=11.8, open=11.9, high=12.2, low=11.7,
        volume=50000, amount=60000000, change=0.2, change_pct=1.7, volume_ratio=1.5, pe_dynamic=20,
        asset_type=AssetType.STOCK,
    )
    start = datetime.now() - timedelta(days=260)
    bars = []
    for i in range(260):
        price = 10 + i * 0.005
        bars.append(Bar(symbol="000001", frame="1d", ts=start + timedelta(days=i), open=price, high=price*1.02, low=price*0.98, close=price, volume=10000+i, amount=(10000+i)*price*100, source="unit:qfq"))
    result = ScreenerService(MarketDataService()).analyze(q, bars, kline_adjust="qfq")
    assert result.indicator50_snapshot["count"] >= 50
    assert result.tradercore_diagnosis["framework"]["scoring_layers"][1]["weight"] == 45
    assert result.tradercore_diagnosis["rows"]


def test_v16_3_search_all_uses_effective_valid_count_not_raw_count():
    class Svc(NewsAnalysisService):
        def __init__(self):
            super().__init__()
            self.calls = []
        def _search_eastmoney_hsf10(self, symbol, name, limit):
            self.calls.append("hsf10")
            bad = []
            for i in range(80):
                bad.append(self._score_item("公司资料", f"https://stockpage.10jqka.com.cn/{symbol}/company/{i}", "东方财富F10", "", "首页 新闻公告 财务分析 经营分析 股东股本 主力持仓", symbol, name, source_type="news"))
            return bad
        def _search_eastmoney_ann(self, symbol, name, limit):
            self.calls.append("ann"); return []
        def _search_cninfo_fulltext(self, symbol, name, limit):
            self.calls.append("cninfo"); return []
        def _search_sina_stock_news(self, symbol, name, limit):
            self.calls.append("sina"); return []
        def _search_10jqka_stock_news(self, symbol, name, limit):
            self.calls.append("ths"); return []
        def _search_eastmoney_page(self, query, symbol, name, limit):
            self.calls.append("em_search")
            return [self._score_item(f"{name}公告显示公司签订重大合同", "https://finance.eastmoney.com/a/20260521-test.html", "东方财富搜索", "2026-05-21", f"{name}公告显示公司签订重大合同，订单金额较大。", symbol, name, source_type="news")]
        def _search_sina_page(self, query, symbol, name, limit):
            self.calls.append("sina_search"); return []
        def _search_10jqka_page(self, query, symbol, name, limit):
            self.calls.append("ths_search"); return []
        def _search_professional_portals(self, query, symbol, name, limit):
            self.calls.append("portal"); return []
        def _search_eastmoney_guba(self, symbol, name, limit):
            return []
        def _search_xueqiu_page(self, query, symbol, name, limit):
            return []
    svc = Svc()
    got = svc._search_all("通威股份 600438", "600438", "通威股份", 120, mode="deep")
    assert "em_search" in svc.calls or "portal" in svc.calls
    assert any("重大合同" in x.title for x in got)


def test_v16_4_word_sources_are_extracted_and_counted():
    from quant_data.services.source_knowledge_service import SourceKnowledgeService
    svc = SourceKnowledgeService()
    cov = svc.coverage()
    assert cov["doc_count"] == 4
    assert cov["docx_loaded"] is True
    assert cov["doc_char_count"] > 80000
    assert cov["doc_item_count"] > 1000
    assert cov["doc_table_count"] >= 30
    assert cov["technical_indicator_count_from_word"] >= 50
    assert cov["message_source_channels"] >= 20
    assert cov["quant_pipeline_steps"] >= 9
    assert cov["image_count"] >= 2


def test_v16_4_word_technical_catalog_contains_50_plus_indicators():
    from quant_data.services.source_knowledge_service import SourceKnowledgeService
    tech = SourceKnowledgeService().technical_framework()
    names = tech["normalized_indicators"]
    assert len(names) >= 50
    for required in ["移动平均线 MA", "MACD 平滑异同", "VWAP", "TD序列", "Ichimoku 一目均衡表", "Sharpe 夏普比率"]:
        assert any(required.split()[0] in x or required in x for x in names)
    assert len(tech["word_table_rows_extracted"]) == 50


def test_v16_4_tradercore_framework_is_word_and_image_grounded():
    from quant_data.services.trading_framework_service import tradercore_reference_framework
    fw = tradercore_reference_framework()
    assert fw["source_grounding"]["doc_count"] == 4
    assert fw["source_grounding"]["word_technical_indicator_count"] >= 50
    assert len(fw["word_message_sources"]) >= 20
    assert "量比>=1.3" in fw["candidate_channels"][2]["gate"]
    assert [x["weight"] for x in fw["scoring_layers"]] == [20, 45, 35]


def test_v16_4_api_source_knowledge_routes_contract():
    from quant_data.api import source_knowledge_coverage, source_knowledge_doc
    cov = source_knowledge_coverage()["data"]
    assert cov["doc_count"] == 4
    doc = source_knowledge_doc("technical", max_chars=1000)
    assert doc["ok"] is True
    assert "量价时空" in doc["text"]
