from fastapi.testclient import TestClient

import quant_data.api as api


def test_dedicated_earnings_and_ipo_ingest_publish_canonical_pit_events(monkeypatch):
    published = []
    monkeypatch.setattr(api.event_bus_v324, "publish", lambda event: published.append(event))
    client = TestClient(api.app)

    earnings = client.post(
        "/api/earnings/ingest",
        json={
            "symbol": "688146",
            "report_period": "2026H1",
            "announced_at": "2026-07-17T18:00:00",
            "available_at": "2026-07-17T18:00:00",
            "net_profit": 3.48,
            "consensus_profit": 2.90,
            "source_id": "cninfo",
            "source_name": "巨潮资讯公告",
            "source_url": "https://www.cninfo.com.cn/example",
        },
    ).json()
    ipo = client.post(
        "/api/ipo/ingest",
        json={
            "issuer_symbol": "688999",
            "issuer_name": "长鑫科技",
            "exchange": "上交所",
            "announced_at": "2026-07-16T18:00:00",
            "available_at": "2026-07-16T18:00:00",
            "competitors": ["688146"],
            "sectors": ["半导体材料"],
            "liquidity_shock_score": 72,
            "competitor_listing_pressure": 45,
            "source_id": "sse_ipo",
            "source_name": "上海证券交易所",
            "source_url": "https://www.sse.com.cn/example",
        },
    ).json()

    assert earnings["ok"] is True
    assert ipo["ok"] is True
    assert [event.dataset for event in published] == ["earnings", "ipo"]
    assert published[0].payload["earnings_surprise_pct"] > 0
    assert published[1].payload["competitor_listing_pressure"] == 45


def test_structured_market_factor_ingest_requires_source_and_timestamp(monkeypatch):
    published = []
    monkeypatch.setattr(api.event_bus_v324, "publish", lambda event: published.append(event))
    client = TestClient(api.app)

    rejected = client.post(
        "/api/market-factors/ingest",
        json={"section": "macro", "liquidity_stress": 65},
    ).json()
    accepted = client.post(
        "/api/market-factors/ingest",
        json={
            "section": "macro",
            "available_at": "2026-07-17T20:30:00",
            "published_at": "2026-07-17T20:30:00",
            "liquidity_stress": 65,
            "rates_stress": 70,
            "source_id": "macro_official",
            "source_name": "官方宏观数据发布机构",
            "source_url": "https://example.gov.cn/release",
        },
    ).json()

    assert rejected["ok"] is False
    assert accepted["ok"] is True
    assert published[0].dataset == "macro"
    assert published[0].payload["liquidity_stress"] == 65


def test_global_stream_pit_sync_keeps_traceable_sources_and_deduplicates(monkeypatch):
    published = []
    monkeypatch.setattr(api.event_bus_v324, "publish", lambda event: published.append(event))
    api._pit_news_sync_seen.clear()
    item = {
        "title": "全球半导体板块回调",
        "summary": "费城半导体指数下跌。",
        "published_at": "2026-07-20T21:00:00",
        "source": "金十数据7x24",
        "source_ref": "https://flash.jin10.com/detail/test-v325",
        "affected_sectors": ["半导体"],
        "mapped_symbols": ["688146"],
        "quality_status": "ok",
    }

    first = api._sync_global_news_items_to_pit([item])
    second = api._sync_global_news_items_to_pit([item])

    assert first["stored"] == 1
    assert second["stored"] == 0
    assert published[0].dataset == "news"
    assert published[0].source_id == "jin10"
    assert published[0].symbols == ["688146"]


def test_global_stream_pit_sync_preserves_event_provenance(monkeypatch):
    published = []
    monkeypatch.setattr(api.event_bus_v324, "publish", lambda event: published.append(event))
    api._pit_news_sync_seen.clear()
    item = api.news_service.event_intelligence.enrich_items(
        [
            {
                "title": "美国正式宣布限制外国生产的并网逆变器",
                "summary": "官方命令对外国生产的电网逆变器和储能设备实施采购和进口限制。",
                "published_at": "2026-08-27T12:00:00",
                "source": "美国白宫总统行动",
                "source_ref": "https://www.whitehouse.gov/presidential-actions/2026/08/test/",
                "content_quality_status": "structured_excerpt",
                "mapped_symbols": ["300274"],
            }
        ]
    )[0]

    result = api._sync_global_news_items_to_pit([item])

    assert result["stored"] == 1
    assert published[0].source_id == "whitehouse_actions"
    assert published[0].impact_direction == "negative"
    assert published[0].payload["confirmation_level"] == "official_confirmed"
    assert published[0].payload["event_stage"] == "official"
    assert published[0].payload["trade_gate"] == "candidate_block"
    assert published[0].payload["decision_scope"] == "industry"
    assert published[0].payload["decision_use"] == "score_candidate"
    assert published[0].payload["score_candidate"] is True
