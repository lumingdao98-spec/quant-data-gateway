import time

import quant_data.api as api


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
