from quant_data.data import assert_truthful_source, build_news_snapshot, build_quote_snapshot


def test_search_result_pages_are_blocked():
    result = assert_truthful_source("baidu", "https://www.baidu.com/s?wd=300750")

    assert result.accepted is False
    assert result.reasons


def test_missing_quote_fields_are_explained_not_fabricated():
    snap = build_quote_snapshot("300750", {"last": 10.0, "source": "unit"}, source_id="unit")

    data = snap.to_dict()
    assert data["last"] == 10.0
    assert any("盘口" in x or "量比" in x for x in data["source"]["missing_reasons"])


def test_news_snapshot_drops_banned_search_result():
    snap = build_news_snapshot(
        "300750",
        [{"title": "搜索结果", "source_id": "baidu", "url": "https://www.baidu.com/s?wd=x"}],
        source_id="baidu",
    )

    assert snap.items == []
    assert snap.source.quality_status == "missing"
