from __future__ import annotations

from fastapi.testclient import TestClient

from quant_data.services.global_industry_mapper import GlobalIndustryMapper
import quant_data.api as api


def test_photovoltaic_news_maps_to_pv_industry_and_symbol_score():
    mapper = GlobalIndustryMapper()
    item = {"title": "\u5149\u4f0f\u653f\u7b56\u652f\u6301\u7ec4\u4ef6\u9700\u6c42\u589e\u957f", "summary": "\u7845\u6599\u4ef7\u683c\u4e0a\u884c\u5f71\u54cd\u4ea7\u4e1a\u94fe"}
    mapped = mapper.map_items([item], "300274", "\u9633\u5149\u7535\u6e90")
    first = mapped["industry_mapped_items"][0]

    assert "\u5149\u4f0f\u8bbe\u5907" in first["mapped_industries"]
    assert "\u5149\u4f0f" in first["mapped_concepts"]
    assert first["score_included"] is True
    assert first["impact_reason"]


def test_storage_news_maps_to_inverter_and_storage():
    mapper = GlobalIndustryMapper()
    item = {"title": "\u50a8\u80fd\u653f\u7b56\u63a8\u52a8\u9006\u53d8\u5668\u548cPCS\u62db\u6807", "summary": ""}
    first = mapper.map_items([item], "300274", "\u9633\u5149\u7535\u6e90")["industry_mapped_items"][0]

    assert "\u50a8\u80fd\u7cfb\u7edf" in first["mapped_industries"]
    assert "\u9006\u53d8\u5668" in first["mapped_industries"]
    assert first["relevance_score"] >= 55


def test_unrelated_global_news_is_background_only():
    mapper = GlobalIndustryMapper()
    item = {"title": "\u6b27\u6d32\u65c5\u6e38\u5b63\u822a\u7a7a\u5ba2\u6d41\u4e0a\u5347", "summary": "\u9152\u5e97\u9700\u6c42\u6539\u5584"}
    first = mapper.map_items([item], "300274", "\u9633\u5149\u7535\u6e90")["industry_mapped_items"][0]

    assert first["score_included"] is False
    assert first["relevance_score"] < 55
    assert "\u4e0d\u7eb3\u5165\u4e2a\u80a1\u8bc4\u5206" in first["impact_reason"]


def test_market_wide_rate_event_never_becomes_individual_score_from_style_overlap():
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure(
        "300750",
        profile={"industry": "动力电池", "concepts": ["利率敏感", "全球流动性"]},
        name="宁德时代",
    )
    first = mapper.map_item(
        {"title": "美国非农数据公布后美债收益率上升", "summary": "美联储利率路径仍有不确定性"},
        "300750",
        exposure,
    )

    assert first["market_wide"] is True
    assert first["score_included"] is False
    assert first["impact_scope_cn"] == "市场环境"


def test_info_page_has_global_industry_mapping_tab():
    html = TestClient(api.app).get("/info?symbol=300274&name=Sungrow").text
    assert "\u5168\u7403/\u884c\u4e1a\u6620\u5c04" in html
    assert "industryMappedItems" in html
    assert "relevance_score" in html or "\u76f8\u5173\u6027" in html
