import time

import quant_data.api as api
from quant_data.data.source_registry import default_source_registry
from quant_data.services.news_cleaner import valid_news_item
from quant_data.services.source_registry import SourceRegistryService


def test_news_source_health_is_read_only_and_exposes_circuit_state(monkeypatch):
    service = api.news_service
    previous_stock = list(service._last_source_status)
    previous_global = list(service._last_global_source_status)
    previous_failures = dict(service._source_failures)
    previous_circuits = dict(service._source_circuit_opened_at)
    try:
        service._last_source_status = [{"source": "官方公告", "count": 3, "status": "ok"}]
        service._last_global_source_status = [
            {"source": "全球快讯", "count": 0, "status": "ok", "skipped_reason": "缓存仍有效"}
        ]
        service._source_failures = {"临时来源": 2}
        service._source_circuit_opened_at = {"临时来源": time.time()}

        def forbidden_network(*args, **kwargs):
            raise AssertionError("source_health must not perform network I/O")

        monkeypatch.setattr(service.http, "get", forbidden_network)
        health = service.source_health()

        assert health["network_used"] is False
        assert health["stock_sources"][0]["quality_status"] == "有有效数据"
        assert health["global_sources"][0]["quality_status"] == "已跳过/降级"
        assert health["active_circuits"][0]["source"] == "临时来源"
        assert "百度/360/搜狗" in health["truth_boundary"]
    finally:
        service._last_source_status = previous_stock
        service._last_global_source_status = previous_global
        service._source_failures = previous_failures
        service._source_circuit_opened_at = previous_circuits


def test_global_official_catalog_is_broad_and_not_limited_to_example_regions():
    registry = default_source_registry()
    expected = {
        "in_rbi": "印度",
        "sg_mas": "新加坡",
        "ca_boc": "加拿大",
        "au_rba": "澳大利亚",
        "br_bcb": "巴西",
        "za_sarb": "南非",
        "oecd": "国际组织",
    }

    for source_id, region in expected.items():
        source = registry.get(source_id)
        assert source is not None
        assert source.region == region
        assert source.fetch_mode == "catalog_only"
        assert source.evidence_role == "primary_confirmation"


def test_global_coverage_matrix_discovers_catalog_sources_dynamically():
    matrix = SourceRegistryService().coverage_matrix()
    international = {item["key"]: item for item in matrix["国际消息"]}

    for source_id in ("in_rbi", "ca_stats", "au_abs", "br_bcb", "fao", "iea"):
        assert source_id in international
        assert international[source_id]["fetch_mode"] == "catalog_only"


def test_official_english_event_is_accepted_but_navigation_noise_is_rejected():
    accepted, accepted_reason = valid_news_item(
        "Monetary Policy Committee keeps the policy interest rate unchanged",
        "The Reserve Bank of India reviewed inflation, employment and financial market conditions at its meeting.",
        source="Reserve Bank of India",
        url="https://www.rbi.org.in/Scripts/PressReleaseUser.aspx?prid=example",
        source_type="macro",
        allow_macro=True,
    )
    rejected, rejected_reason = valid_news_item(
        "About Us and Contact Directory",
        "Home About Us Contact Directory Downloads Careers Copyright",
        source="Reserve Bank of India",
        url="https://www.rbi.org.in/aboutus/",
        source_type="macro",
        allow_macro=True,
    )

    assert accepted is True
    assert accepted_reason == "ok_macro"
    assert rejected is False
    assert rejected_reason in {"too_few_chinese_chars", "boilerplate_or_invalid_title", "menu_or_table_fragment"}
