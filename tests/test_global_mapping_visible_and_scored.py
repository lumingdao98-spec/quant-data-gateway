from __future__ import annotations

from fastapi.testclient import TestClient

from quant_data.services.global_industry_mapper import GlobalIndustryMapper
from quant_data.services.cache_state_service import CacheStateService
import quant_data.api as api


def test_global_mapping_outputs_visible_evidence_fields():
    mapper = GlobalIndustryMapper()
    data = mapper.map_items(
        [
            {"title": "\u5149\u4f0f\u653f\u7b56\u652f\u6301\u7ec4\u4ef6\u9700\u6c42"},
            {"title": "\u50a8\u80fd\u9006\u53d8\u5668\u62db\u6807\u589e\u957f"},
            {"title": "\u6b27\u6d32\u8db3\u7403\u8d5b\u7a0b\u66f4\u65b0"},
        ],
        "300274",
        "\u9633\u5149\u7535\u6e90",
    )
    mapped = data["industry_mapped_items"]
    assert mapped[0]["global_item_id"]
    assert mapped[0]["impact_reason"]
    assert mapped[0]["included_in_score"] is True
    assert any("\u5149\u4f0f" in x for x in mapped[0]["mapped_concepts"] + mapped[0]["mapped_industries"])
    assert mapped[-1]["included_in_score"] is False


def test_info_page_global_mapping_tab_has_evidence_columns():
    html = TestClient(api.app).get("/info?symbol=300274&name=Sungrow").text
    assert "全球/行业映射" in html
    assert "行业：" in html
    assert "概念：" in html
    assert "影响原因：" in html
    assert "纳入个股评分" in html
    assert "发布时间：" in html


def test_info_analyze_maps_cached_global_energy_policy(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    svc.put(
        "global_news_cache",
        "global:80",
        {
            "items": [
                {
                    "title": "光伏政策支持组件需求 储能逆变器招标增长",
                    "summary": "新能源政策和储能系统项目推进。",
                    "source": "unit",
                    "source_type": "macro",
                }
            ]
        },
        source="unit_global",
    )

    class EmptyStore:
        def list_items(self, *args, **kwargs):
            return []

        def read_analysis(self, *args, **kwargs):
            return None

        def save_analysis(self, *args, **kwargs):
            return True

    monkeypatch.setattr(api.news_service, "store", EmptyStore())
    monkeypatch.setattr(api.company_profile_service, "get_profile", lambda *a, **k: {})
    monkeypatch.setattr(api.info_analysis_service, "analyze", lambda *a, **k: {"items": [], "news": {"count": 0}, "source_logs": []})

    result = api.info_analyze("300274", name="阳光电源", limit=80, force=True)
    mapped = result["data"]["industry_mapped_items"]

    assert mapped
    assert mapped[0]["included_in_score"] is True
    assert mapped[0]["relevance_score"] >= 55
    assert any("光伏" in x for x in mapped[0]["mapped_concepts"] + mapped[0]["mapped_industries"])
    assert any("储能" in x for x in mapped[0]["mapped_concepts"] + mapped[0]["mapped_industries"])
    assert "impact_reason" in mapped[0]
