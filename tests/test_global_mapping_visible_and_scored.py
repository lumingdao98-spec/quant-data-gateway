from __future__ import annotations

from fastapi.testclient import TestClient

from quant_data.services.global_industry_mapper import GlobalIndustryMapper
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
    assert "global/industry mapping evidence" in html or "Global Mapping" in html
    assert "industries:" in html
    assert "impact_reason" in html
    assert "included in score" in html
