from fastapi.testclient import TestClient

import quant_data.api as api


def test_global_news_stream_returns_real_source_shape(monkeypatch):
    def fake_jin10_flash(limit=80):
        return [
            {
                "标题": "金十期货7x24：美国非农就业数据公布前，美元指数震荡",
                "内容": "宏观快讯样例来自测试替身，用于验证结构，不进入真实缓存评分。",
                "发布时间": "2026-07-02 21:08:00",
                "链接": "https://qihuo.jin10.com/",
                "_source_name": "金十期货快讯",
            }
        ]

    monkeypatch.setattr(api.news_service, "_search_jin10_flash", fake_jin10_flash)
    monkeypatch.setattr(api.news_service, "_search_eastmoney_kuaixun", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        api.cache_state_service,
        "put",
        lambda kind, key, payload, **kwargs: {"status": "test_no_write", "snapshot_id": key, "stale": False},
    )

    data = TestClient(api.app).get("/api/news/global/stream?limit=20&force=true").json()

    assert data["ok"] is True
    assert data["items"]
    assert data["items"][0]["source"] == "金十期货快讯"
    assert data["items"][0]["is_jin10"] is True
    assert data["items"][0]["published_at"] == "2026-07-02 21:08:00"
    assert "不伪造新闻" in data["disclaimer"]


def test_global_news_stream_cache_only_reports_missing_without_fake_data():
    data = TestClient(api.app).get("/api/news/global/stream?limit=20&live=false&force=false").json()

    assert data["ok"] is True
    assert "items" in data
    assert "cache_status" in data
    assert "disclaimer" in data
    if not data["items"]:
        assert data["data"]["missing_reason"]


def test_generic_global_news_link_parser_keeps_href_available(monkeypatch):
    seen_urls = []

    def fake_valid(title, summary="", source="", url="", **kwargs):
        seen_urls.append(url)
        return True, "ok"

    monkeypatch.setattr(api.news_service, "valid_news_item", fake_valid)
    html = '<a href="/a/20260702.html" title="全球商品市场快讯">全球商品市场快讯</a>'

    rows = api.news_service._extract_generic_news_links(html, "测试全球快讯", "https://example.com/", limit=5)

    assert rows
    assert seen_urls == ["https://example.com/a/20260702.html"]
    assert rows[0]["链接"] == "https://example.com/a/20260702.html"
