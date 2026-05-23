import time

from quant_data.services.news_service import NewsAnalysisService, NewsItem


def _announcement(i: int) -> NewsItem:
    return NewsItem(
        title=f"测试公司公告{i}",
        url=f"https://example.com/{i}.html",
        source="巨潮资讯公告",
        source_type="announcement",
        credibility_score=92,
        summary="短摘要",
    )


def test_announcement_detail_fetch_is_concurrent_and_cached(monkeypatch):
    svc = NewsAnalysisService()
    calls = []

    def fake_fetch(url, max_chars=1200):
        calls.append(url)
        time.sleep(0.08)
        return "公告显示公司中标重大合同，经营改善，风险可控。" * 8

    monkeypatch.setattr(svc, "_fetch_text_excerpt", fake_fetch)
    items = [_announcement(i) for i in range(8)]

    started = time.perf_counter()
    enriched = svc._enrich_announcement_content(items, max_items=8)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.35
    assert sum(1 for x in enriched if x.content_loaded) == 8
    assert len(calls) == 8


def test_text_excerpt_cache_and_search_result_status_are_silent(monkeypatch):
    svc = NewsAnalysisService()

    class Resp:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        content = b"<html></html>"
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        text = "公告显示公司回购增持，盈利能力改善。" * 30

    calls = {"n": 0}

    def fake_get(*args, **kwargs):
        calls["n"] += 1
        return Resp()

    monkeypatch.setattr(svc.http, "get", fake_get)
    assert svc._fetch_text_excerpt("https://example.com/a.html")
    assert svc._fetch_text_excerpt("https://example.com/a.html")
    assert calls["n"] == 1

    svc._record_source("搜索引擎页", 0, "彻底禁用：搜索结果页不是新闻证据")
    assert not svc._source_status
