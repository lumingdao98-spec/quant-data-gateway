from quant_data.services.news_service import NewsAnalysisService, NewsItem
from quant_data.services.news_store_service import NewsStoreService


def _item(i: int, source: str = "巨潮资讯公告") -> NewsItem:
    return NewsItem(
        title=f"隆基绿能关于重大合同公告{i}",
        url=f"https://example.com/a{i}.html",
        source=source,
        source_type="announcement",
        summary="隆基绿能公告显示公司签订重大合同，经营改善。",
        relevance_score=80,
        credibility_score=92,
        event_key=f"evt-{i}",
    )


class LightProbeService(NewsAnalysisService):
    def __init__(self):
        super().__init__()
        self.calls = []

    def _search_eastmoney_ann(self, symbol, name, limit):
        self.calls.append("em_ann")
        return [_item(i, "东方财富公告") for i in range(90)]

    def _search_cninfo_fulltext(self, symbol, name, limit):
        self.calls.append("cninfo")
        return []

    def _search_eastmoney_hsf10(self, symbol, name, limit):
        self.calls.append("f10")
        return []

    def _search_eastmoney_page(self, *args):
        self.calls.append("eastmoney_site_search")
        return []

    def _search_sina_page(self, *args):
        self.calls.append("sina_site_search")
        return []

    def _search_10jqka_page(self, *args):
        self.calls.append("ths_site_search")
        return []

    def _search_professional_portals(self, *args):
        self.calls.append("professional_portal")
        return []

    def _search_eastmoney_guba(self, *args):
        self.calls.append("guba")
        return []

    def _search_xueqiu_page(self, *args):
        self.calls.append("xueqiu")
        return []


def test_light_mode_does_not_run_site_search_matrix_and_stops_at_80():
    svc = LightProbeService()
    items = svc._search_all("隆基绿能 601012", "601012", "隆基绿能", 180, mode="light")
    assert len(items) >= 80
    assert "eastmoney_site_search" not in svc.calls
    assert "sina_site_search" not in svc.calls
    assert "ths_site_search" not in svc.calls
    assert "professional_portal" not in svc.calls
    assert any(s["source"] == "light mode停止补源" for s in svc._source_status)


def test_info_limit_is_upper_bound_not_forced_target():
    svc = LightProbeService()
    items = svc._search_all("隆基绿能 601012", "601012", "隆基绿能", 180, mode="light")
    assert len(items) < 180
    assert any("停止补源" in s["source"] for s in svc._source_status)


def test_pre_1970_announcement_date_priority_does_not_raise():
    svc = NewsAnalysisService()
    item = NewsItem(**{**_item(1).to_dict(), "published_at_norm": "1900-01-01"})

    priority = svc._item_priority(item)

    assert isinstance(priority[-1], float)


def test_deep_mode_enables_professional_media(monkeypatch):
    svc = LightProbeService()

    monkeypatch.setattr(svc, "_search_eastmoney_ann", lambda *a: [])
    monkeypatch.setattr(svc, "_search_cninfo_fulltext", lambda *a: [])
    monkeypatch.setattr(svc, "_search_eastmoney_hsf10", lambda *a: [])
    monkeypatch.setattr(svc, "_search_sina_stock_news", lambda *a: [])
    monkeypatch.setattr(svc, "_search_10jqka_stock_news", lambda *a: [])
    monkeypatch.setattr(svc, "_search_eastmoney_page", lambda *a: [])
    monkeypatch.setattr(svc, "_search_sina_page", lambda *a: [])
    monkeypatch.setattr(svc, "_search_10jqka_page", lambda *a: [])

    def professional(*args):
        svc.calls.append("professional_portal")
        return [_item(1, "证券时报")]

    monkeypatch.setattr(svc, "_search_professional_portals", professional)
    svc._search_all("隆基绿能 601012", "601012", "隆基绿能", 120, mode="deep")
    assert "professional_portal" in svc.calls


def test_detail_enrichment_failure_keeps_title_level_items(monkeypatch, tmp_path):
    svc = NewsAnalysisService(cache_file=tmp_path / "news_cache.json")
    svc.store = NewsStoreService(tmp_path / "news_store.sqlite")
    monkeypatch.setattr(svc, "_search_all", lambda *a, **k: [_item(1)])
    monkeypatch.setattr(svc, "_enrich_announcement_content", lambda *a, **k: (_ for _ in ()).throw(OSError(22, "Invalid argument")))
    monkeypatch.setattr(svc, "_enrich_link_content", lambda items, *a, **k: items)

    result = svc.analyze("601012", name="隆基绿能", limit=80, force=True, mode="normal")

    assert result["count"] >= 1
    assert any(s["source"] == "公告正文补充" and "降级" in s["status"] for s in result["sources_status"])
