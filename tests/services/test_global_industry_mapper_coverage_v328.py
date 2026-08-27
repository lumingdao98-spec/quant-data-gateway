from __future__ import annotations

import pytest

from quant_data.services.global_industry_mapper import GlobalIndustryMapper


@pytest.mark.parametrize(
    ("industry", "headline", "expected_family"),
    [
        ("白色家电", "家电以旧换新带动空调需求增长", "home_appliance"),
        ("航运港口", "集运运价上涨，红海航线继续扰动", "transport"),
        ("软件开发", "信创与云计算项目加快落地", "software"),
        ("有色金属", "铜价上涨改善有色金属盈利预期", "metals_mining"),
        ("养殖业", "猪价回升，生猪养殖利润改善", "agriculture"),
        ("保险", "保险资金与资本市场政策进一步完善", "insurance"),
        ("医药生物", "创新药医保政策出现新进展", "medicine"),
        ("证券", "券商两融业务活跃度回升", "broker"),
        ("机械设备", "设备更新推动工业自动化订单", "machinery"),
        ("传媒", "游戏版号发放改善内容供给", "media"),
    ],
)
def test_market_industry_drives_general_sector_mapping(industry: str, headline: str, expected_family: str) -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure(
        "999999",
        profile={
            "name": "测试公司",
            "industry": industry,
            "market_industry": industry,
            "sources": ["eastmoney.f100"],
            "quality_status": "available",
        },
        name="测试公司",
    )
    mapped = mapper.map_item({"title": headline, "summary": ""}, "999999", exposure)

    assert expected_family in exposure["matched_sector_families"]
    assert exposure["classification_confidence"] == "high"
    assert mapped["is_related_to_symbol"] is True
    assert mapped["score_included"] is True


def test_mapper_catalog_covers_main_a_share_sector_families() -> None:
    catalog = GlobalIndustryMapper().coverage_catalog()

    assert catalog["sector_family_count"] >= 25
    assert catalog["event_rule_count"] >= 25
    assert {"home_appliance", "transport", "software", "medicine", "bank", "agriculture"}.issubset(
        set(catalog["sector_families"])
    )


def test_missing_profile_does_not_turn_name_guess_into_trade_score() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure("999999", profile={}, name="某科技公司")
    mapped = mapper.map_item({"title": "半导体出口限制升级", "summary": ""}, "999999", exposure)

    assert exposure["classification_confidence"] == "low"
    assert mapped["score_included"] is False
    assert mapped["is_related_to_symbol"] is False


def test_upstream_chip_terms_do_not_turn_pv_company_into_semiconductor_exposure() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure(
        "300274",
        profile={
            "name": "阳光电源",
            "industry": "电气机械和器材制造业",
            "main_business": "太阳能光伏逆变器、储能系统及电力电源研发制造",
            "business_tags": ["光伏", "逆变器", "储能"],
            "upstream": ["电子元件", "芯片"],
            "downstream": ["光伏电站", "储能电站"],
        },
        name="阳光电源",
    )
    mapped = mapper.map_item({"title": "半导体芯片板块上涨，存储芯片活跃"}, "300274", exposure)

    assert "electronics" not in exposure["matched_sector_families"]
    assert "automotive" not in exposure["matched_sector_families"]
    assert mapped["is_related_to_symbol"] is False
    assert mapped["score_included"] is False


def test_ev_only_news_does_not_score_for_pv_storage_company() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure("300274", name="阳光电源")
    mapped = mapper.map_item({"title": "新能源汽车销量增长，汽车整车板块走强"}, "300274", exposure)

    assert mapped["is_related_to_symbol"] is False
    assert mapped["score_included"] is False
    assert "电池与储能" in exposure["matched_sector_family_labels_cn"] or "储能系统" in exposure["industries"]


def test_confirmed_industry_event_maps_non_sample_grid_company_by_profile() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure(
        "600406",
        profile={
            "name": "国电南瑞",
            "industry": "电网设备",
            "market_industry": "电网设备",
            "main_business": "电网自动化、继电保护和输配电控制设备",
            "sources": ["eastmoney.f100"],
        },
        name="国电南瑞",
    )
    mapped = mapper.map_item(
        {
            "title": "电网安全新规覆盖输配电设备与变压器采购",
            "event_type": "policy",
            "decision_scope": "industry",
            "confirmation_level": "official_confirmed",
            "event_stage": "effective",
        },
        "600406",
        exposure,
    )

    assert mapped["is_related_to_symbol"] is True
    assert mapped["score_included"] is True
    assert mapped["mapped_symbols"] == []
    assert "power_grid" in exposure["matched_sector_families"]


def test_sector_rule_does_not_make_old_example_symbol_a_direct_hit() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure("300274", name="阳光电源")
    mapped = mapper.map_item(
        {
            "title": "美国电网审查某境外供应商的并网逆变器",
            "event_type": "regulatory",
            "decision_scope": "issuer",
            "confirmation_level": "official_confirmed",
            "event_stage": "effective",
        },
        "300274",
        exposure,
    )

    assert mapped["mapped_symbols"] == []
    assert mapped["is_related_to_symbol"] is False
    assert mapped["score_included"] is False


def test_explicit_company_name_still_creates_direct_relevance() -> None:
    mapper = GlobalIndustryMapper()
    exposure = mapper.company_exposure("688146", name="中船特气")
    mapped = mapper.map_item(
        {
            "title": "中船特气发布半年度业绩公告",
            "event_type": "financial_report",
            "decision_scope": "issuer",
            "confirmation_level": "official_confirmed",
            "event_stage": "effective",
        },
        "688146",
        exposure,
    )

    assert "688146" in mapped["mapped_symbols"]
    assert mapped["is_related_to_symbol"] is True
    assert mapped["score_included"] is True
