from quant_data.data import PITRecord, PITStore, build_news_snapshot


def test_news_snapshot_exposes_available_at_and_pit_hides_future(tmp_path):
    snapshot = build_news_snapshot("300750", [{"title": "公告", "source_id": "cninfo", "published_at": "2026-07-20T10:00:00", "available_at": "2026-07-20T10:01:00"}], source_id="cninfo", source_name="巨潮资讯")
    assert snapshot.items[0]["available_at"] == "2026-07-20T10:01:00"

    store = PITStore(tmp_path / "pit.sqlite")
    store.put(PITRecord("n1", "300750", "news", "2026-07-20T10:01:00", "2026-07-20T10:01:00", snapshot.to_dict(), "cninfo"))
    assert store.query_asof(decision_time="2026-07-20T10:00:59", dataset="news", symbol="300750") == []
    assert len(store.query_asof(decision_time="2026-07-20T10:01:00", dataset="news", symbol="300750")) == 1
