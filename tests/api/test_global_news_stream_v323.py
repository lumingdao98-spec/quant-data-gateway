from fastapi.testclient import TestClient
from types import SimpleNamespace

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
    assert data["items"][0]["source_ref"] == "https://qihuo.jin10.com/"
    assert "impact_targets" in data["items"][0]
    assert "impact_note" in data["items"][0]
    assert "不伪造新闻" in data["disclaimer"]


def test_jin10_realtime_endpoint_is_first_class_direct_stream(monkeypatch):
    def fake_jin10_flash(limit=80):
        return [
            {
                "标题": "金十期货：美国非农公布在即，贵金属波动加大",
                "内容": "用于验证金十直连接口结构。",
                "发布时间": "2026-07-04 09:37:40",
                "链接": "https://qihuo.jin10.com/",
                "_source_name": "金十期货页面快讯",
                "_source_api": "https://flash-api.jin10.com/get_flash_list",
                "_source_page": "https://qihuo.jin10.com/",
            }
        ]

    monkeypatch.setattr(api.news_service, "_search_jin10_flash", fake_jin10_flash)
    monkeypatch.setattr(
        api.cache_state_service,
        "put",
        lambda kind, key, payload, **kwargs: {"status": "test_no_write", "snapshot_id": key, "stale": False},
    )

    data = TestClient(api.app).get("/api/news/jin10/realtime?limit=20&force=true").json()

    assert data["ok"] is True
    assert data["items"][0]["source"] == "金十期货页面快讯"
    assert data["items"][0]["source_api"] == "https://flash-api.jin10.com/get_flash_list"
    assert data["items"][0]["source_ref"] == "https://qihuo.jin10.com/"
    assert "impact_targets" in data["items"][0]
    assert "impact_note" in data["items"][0]
    assert data["data"]["stream_mode"] == "jin10_realtime_direct"
    assert data["refresh_seconds"] == 20
    assert "不抓搜索结果页" in data["source_policy"]


def test_global_news_stream_cache_only_reports_missing_without_fake_data():
    data = TestClient(api.app).get("/api/news/global/stream?limit=20&live=false&force=false").json()

    assert data["ok"] is True
    assert "items" in data
    assert "cache_status" in data
    assert "disclaimer" in data
    if not data["items"]:
        assert data["data"]["missing_reason"]


def test_macro_global_events_uses_fast_stream_with_source_and_impact(monkeypatch):
    def fake_stream(limit=80, force=False, live=True):
        assert live is True
        return (
            {
                "items": [
                    {
                        "title": "美国非农公布前美元和美债收益率波动",
                        "summary": "宏观事件测试项",
                        "source": "金十数据7x24",
                        "source_ref": "https://qihuo.jin10.com/",
                        "source_api": "https://flash-api.jin10.com/get_flash_list",
                        "published_at": "2026-07-04 21:50:00",
                        "impact_targets": ["宏观/利率", "美元指数", "美债收益率", "银行"],
                        "affected_sectors": ["银行"],
                        "affected_assets": ["美元指数", "美债收益率"],
                        "impact_note": "宏观数据会影响大盘风险偏好和利率敏感板块。",
                    }
                ],
                "stream_mode": "fast_test",
                "sources_status": [{"source": "金十数据7x24", "count": 1, "status": "ok"}],
                "updated_at": "2026-07-04T21:50:01",
            },
            {"status": "test_fast_stream", "stale": False},
        )

    monkeypatch.setattr(api, "_read_global_news_stream", fake_stream)

    data = TestClient(api.app).get("/api/macro/global-events?limit=20&force=true").json()

    assert data["ok"] is True
    assert data["data"]["stream_mode"] == "fast_test"
    assert data["cache_status"]["status"] == "test_fast_stream"
    assert data["items"][0]["source_ref"] == "https://qihuo.jin10.com/"
    assert data["items"][0]["source_api"] == "https://flash-api.jin10.com/get_flash_list"
    assert "美元指数" in data["items"][0]["impact_targets"]
    assert data["watchlist"]


def test_global_news_stream_keeps_last_real_items_when_live_round_empty(monkeypatch):
    monkeypatch.setattr(api, "_fetch_global_stream_fast", lambda limit=80, force=False: ([], [{"source": "金十/金十期货快讯", "count": 0, "status": "TimeoutError"}]))
    monkeypatch.setattr(api.cache_state_service, "get", lambda *args, **kwargs: SimpleNamespace(data=None, cache_status={"status": "miss"}))
    monkeypatch.setattr(
        api.cache_state_service,
        "latest",
        lambda *args, **kwargs: SimpleNamespace(
            data={"items": [{"title": "上一轮真实金十快讯", "source": "金十期货快讯", "published_at": "2026-07-04 08:00:00"}]},
            cache_status={"status": "stale", "source": "global_news_cache"},
        ),
    )

    data = TestClient(api.app).get("/api/news/global/stream?limit=20&live=true&force=false").json()

    assert data["ok"] is True
    assert data["items"][0]["title"] == "上一轮真实金十快讯"
    assert data["data"]["stream_mode"] == "stale_cache_fallback"
    assert "上一轮真实快讯缓存" in data["data"]["missing_reason"]


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


def test_jin10_flash_parser_keeps_parent_time_and_dedupes():
    payload = {
        "status": 200,
        "data": [
            {
                "id": "1",
                "time": "2026-07-04 08:40:17",
                "data": {
                    "content": "【美国非农数据公布前，美元指数震荡】金十数据7月4日讯，交易员等待劳动力市场报告。",
                    "source_link": "https://qihuo.jin10.com/",
                    "source": "",
                },
            },
            {
                "id": "2",
                "time": "2026-07-04 08:41:00",
                "data": {
                    "content": "【美国非农数据公布前，美元指数震荡】金十数据7月4日讯，交易员等待劳动力市场报告。",
                },
            },
        ],
    }

    rows = api.news_service._extract_jin10_flash_rows(payload, "金十期货快讯", limit=10)

    assert len(rows) == 1
    assert rows[0]["标题"] == "美国非农数据公布前，美元指数震荡"
    assert rows[0]["发布时间"] == "2026-07-04 08:40:17"
    assert rows[0]["_source_name"] == "金十期货快讯"


def test_global_impact_mapping_keeps_geopolitical_events_out_of_a_share_theme_noise(monkeypatch):
    monkeypatch.setattr(api.news_service, "_industry_tags", lambda text: ["机器人/低空"])

    fields = api._global_impact_fields("以色列无人机袭击加沙北部，巴勒斯坦多人伤亡", "全球/国内要闻", "行业消息/政策消息")

    assert "地缘风险" in fields["impact_evidence"]
    assert "军工" in fields["affected_sectors"]
    assert "能源" in fields["affected_sectors"]
    assert "黄金" in fields["affected_assets"]
    assert "机器人/低空" not in fields["impact_targets"]


def test_global_impact_mapping_explains_us_nonfarm_macro_chain():
    fields = api._global_impact_fields("美国非农就业数据公布前，美元指数和美债收益率震荡", "全球宏观", "经济数据")

    assert "宏观/利率" in fields["impact_evidence"]
    assert "银行" in fields["affected_sectors"]
    assert "美元指数" in fields["affected_assets"]
    assert "美债收益率" in fields["impact_targets"]
