from quant_data.services.cache_state_service import CacheStateService
from quant_data.services.sector_mainline_service import SectorMainlineService


def _rows():
    return [
        {
            "f2": 101,
            "f3": 4.5,
            "f8": 3.1,
            "f12": "BK0001",
            "f14": "强势板块",
            "f62": 8_000_000_000,
            "f66": 5_000_000_000,
            "f69": 6.2,
            "f72": 3_000_000_000,
            "f78": -2_000_000_000,
            "f84": -6_000_000_000,
            "f104": 90,
            "f105": 10,
            "f106": 0,
            "f124": 1784077200,
        },
        {
            "f2": 99,
            "f3": -2.0,
            "f8": 0.8,
            "f12": "BK0002",
            "f14": "弱势板块",
            "f62": -3_000_000_000,
            "f69": -3.2,
            "f104": 12,
            "f105": 88,
            "f106": 0,
            "f124": 1784077200,
        },
        {
            "f2": 100,
            "f3": 0.3,
            "f8": 1.6,
            "f12": "BK0003",
            "f14": "中性板块",
            "f62": 200_000_000,
            "f69": 0.2,
            "f104": 52,
            "f105": 48,
            "f106": 0,
            "f124": 1784077200,
        },
    ]


def test_sector_mainline_uses_real_fields_and_deterministic_strength(tmp_path):
    service = SectorMainlineService(
        cache=CacheStateService(tmp_path / "cache.sqlite"),
        fetcher=lambda board_type: _rows() if board_type == "industry" else [],
    )
    result = service.snapshot(limit=10, include_concept=False, can_refresh=True, session_date="2026-07-15")

    assert result["ok"] is True
    assert result["items"][0]["board_name"] == "强势板块"
    assert result["items"][0]["net_inflow"] == 8_000_000_000
    assert result["items"][0]["strength_score"] > result["items"][-1]["strength_score"]
    assert result["items"][0]["source_id"] == "eastmoney"
    assert "Level-2" in result["methodology"]["truth_boundary"]
    assert result["raw_hash"]


def test_closed_market_reuses_snapshot_without_refetch(tmp_path):
    calls = []

    def fetcher(board_type):
        calls.append(board_type)
        return _rows()

    service = SectorMainlineService(cache=CacheStateService(tmp_path / "cache.sqlite"), fetcher=fetcher)
    first = service.snapshot(limit=10, include_concept=False, can_refresh=True, session_date="2026-07-15")
    second = service.snapshot(
        limit=10,
        include_concept=False,
        can_refresh=False,
        force=True,
        session_label="收盘休市",
        session_date="2026-07-16",
    )

    assert first["items"]
    assert len(calls) == 1
    assert second["served_from_cache"] is True
    assert "不重复抓取" in second["note"]


def test_missing_source_never_fabricates_sector_rows(tmp_path):
    service = SectorMainlineService(
        cache=CacheStateService(tmp_path / "cache.sqlite"),
        fetcher=lambda board_type: [],
    )
    result = service.snapshot(limit=10, can_refresh=True, session_date="2026-07-15")

    assert result["ok"] is False
    assert result["items"] == []
    assert result["quality_status"] == "missing"
    assert result["missing_reasons"]


def test_source_failure_keeps_a_short_user_facing_reason(tmp_path):
    def fail(_board_type):
        raise RuntimeError(
            "HTTPSConnectionPool timed out for url: "
            "https://push2.eastmoney.com/api/qt/clist/get?very=long&query=value"
        )

    service = SectorMainlineService(
        cache=CacheStateService(tmp_path / "cache.sqlite"),
        fetcher=fail,
    )
    result = service.snapshot(limit=10, can_refresh=True, session_date="2026-07-15")

    assert result["ok"] is False
    assert result["items"] == []
    assert result["missing_reasons"] == ["东方财富公开板块资金接口连接超时"]
    assert "push2.eastmoney.com" in result["errors"][0]
