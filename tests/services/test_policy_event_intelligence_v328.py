from __future__ import annotations

from quant_data.services.global_industry_mapper import GlobalIndustryMapper
from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.policy_event_intelligence import PolicyEventIntelligence


def _draft_item(source: str = "路透 Reuters") -> dict:
    return {
        "title": "消息人士称美国正考虑限制中国能源逆变器进入电网",
        "summary": "The U.S. is working on a ban targeting Chinese energy inverters, sources say.",
        "source": source,
        "url": "https://example.com/draft-inverter-rule",
        "published_at": "2026-08-26T09:00:00",
        "credibility_score": 92,
        "content_quality_status": "structured_excerpt",
    }


def _official_item() -> dict:
    return {
        "title": "美国宣布国家紧急状态以保护大容量电力系统",
        "summary": "官方命令对涉及受覆盖外国实体的并网逆变器和电池储能系统实施采购及进口限制。",
        "source": "美国白宫总统行动",
        "url": "https://www.whitehouse.gov/presidential-actions/2026/08/example/",
        "published_at": "2026-08-26T12:00:00",
        "credibility_score": 98,
        "content_quality_status": "structured_excerpt",
    }


def test_draft_fast_or_media_report_is_early_warning_not_trade_block() -> None:
    event = PolicyEventIntelligence().enrich_items([_draft_item()])[0]

    assert event["event_type"] == "export_or_import_restriction"
    assert event["event_stage"] == "draft"
    assert event["confirmation_level"] == "early_warning"
    assert event["event_direction"] == "negative"
    assert "逆变器" in event["affected_industries_cn"]
    assert event["trade_gate"] == "manual_review"


def test_two_sources_can_confirm_the_report_but_not_turn_a_draft_into_effective_policy() -> None:
    second = {
        **_draft_item("新华社"),
        "title": "美国拟限制中国生产的并网逆变器",
        "url": "https://example.org/second-report",
    }
    events = PolicyEventIntelligence().enrich_items([_draft_item(), second])

    assert {event["confirmation_level"] for event in events} == {"multi_source_confirmed"}
    assert {event["event_stage"] for event in events} == {"draft"}
    assert {event["trade_gate"] for event in events} == {"manual_review"}


def test_same_day_same_sector_but_different_products_are_not_cross_confirmed() -> None:
    events = PolicyEventIntelligence().enrich_items(
        [
            {
                "title": "美国拟限制中国人工智能芯片出口",
                "source": "路透 Reuters",
                "url": "https://example.com/ai-chip-rule",
                "published_at": "2026-08-26T09:00:00",
                "credibility_score": 92,
            },
            {
                "title": "美国考虑限制中国半导体制造设备进口",
                "source": "新华社",
                "url": "https://example.org/equipment-rule",
                "published_at": "2026-08-26T10:00:00",
                "credibility_score": 92,
            },
        ]
    )

    assert {event["confirmation_level"] for event in events} == {"early_warning"}
    assert all(event["confirmation_source_count"] == 1 for event in events)


def test_split_speech_headlines_collapse_to_one_auditable_event() -> None:
    engine = PolicyEventIntelligence()
    events = engine.enrich_items(
        [
            {
                "title": "日本央行副行长：将在每次会议讨论加息步伐",
                "source": "金十数据7x24",
                "url": "https://flash.jin10.com/detail/boj-1",
                "published_at": "2026-08-27T13:00:00",
            },
            {
                "title": "日本央行副行长：将评估风险并考虑加息时机",
                "source": "金十数据7x24",
                "url": "https://flash.jin10.com/detail/boj-2",
                "published_at": "2026-08-27T13:02:00",
            },
        ]
    )

    collapsed = engine.collapse_event_clusters(events)

    assert len(collapsed) == 1
    assert collapsed[0]["event_cluster_size"] == 2
    assert collapsed[0]["duplicate_count"] == 2
    assert len(collapsed[0]["duplicate_titles"]) == 2
    assert collapsed[0]["first_seen_at"] == "2026-08-27T13:00:00"
    assert collapsed[0]["latest_seen_at"] == "2026-08-27T13:02:00"


def test_research_meeting_is_not_misclassified_as_an_earthquake_disaster() -> None:
    event = PolicyEventIntelligence().enrich_items(
        [
            {
                "title": "Public Meeting of Scientific Earthquake Studies Advisory Committee",
                "source": "美国联邦公报",
                "url": "https://www.federalregister.gov/example/earthquake-studies-meeting",
                "published_at": "2026-08-27T09:00:00",
            }
        ]
    )[0]

    assert event["event_type"] == "legislation_or_policy_schedule"
    assert event["event_direction"] == "mixed"
    assert event["decision_use"] == "display_only"
    assert event["trade_gate"] == "observe"


def test_drug_scheduling_notice_is_regulatory_not_subsidy_support() -> None:
    event = PolicyEventIntelligence().enrich_items(
        [
            {
                "title": "Schedules of Controlled Substances: Placement of Cipepofol in Schedule IV",
                "source": "美国联邦公报",
                "url": "https://www.federalregister.gov/example/cipepofol-schedule-iv",
                "published_at": "2026-08-27T09:00:00",
            }
        ]
    )[0]

    assert event["event_type"] == "regulatory_investigation"
    assert event["event_type"] != "support_or_subsidy"
    assert "医药生物" in event["affected_industries_cn"]
    assert event["event_direction"] == "mixed"
    assert event["decision_scope"] == "case"
    assert event["decision_use"] == "score_candidate"

    mapped = GlobalIndustryMapper().map_item(
        event,
        "600000",
        {
            "name": "某医药公司",
            "industries": ["医药生物"],
            "concepts": [],
            "chain_position": [],
        },
    )
    assert mapped["is_related_to_symbol"] is False
    assert mapped["score_included"] is False


def test_industry_project_delay_is_early_negative_warning_but_not_yet_scored() -> None:
    event = PolicyEventIntelligence().enrich_items(
        [
            {
                "title": "美国数据中心扩张受阻，多项拟议项目可能被拖延甚至取消",
                "source": "金十数据7x24",
                "url": "https://flash.jin10.com/detail/data-center-delay",
                "published_at": "2026-08-27T13:30:00",
            }
        ]
    )[0]

    assert event["event_type"] == "operational_disruption"
    assert event["event_direction"] == "negative"
    assert "算力基础设施" in event["affected_industries_cn"]
    assert event["decision_use"] == "early_warning"
    assert event["score_candidate"] is False
    assert event["trade_gate"] == "manual_review"


def test_named_foreign_issuer_case_does_not_penalize_an_entire_a_share_sector() -> None:
    event = PolicyEventIntelligence().enrich_items(
        [
            {
                "title": "Airworthiness Directives; The Boeing Company Airplanes",
                "source": "美国联邦公报",
                "url": "https://www.federalregister.gov/example/boeing-airworthiness",
                "published_at": "2026-08-27T09:00:00",
            }
        ]
    )[0]
    mapped = GlobalIndustryMapper().map_item(
        event,
        "600000",
        {
            "name": "某航空装备公司",
            "industries": ["航空装备"],
            "concepts": ["军工"],
            "chain_position": [],
        },
    )

    assert event["decision_scope"] == "issuer"
    assert event["named_subject"]
    assert mapped["is_related_to_symbol"] is False
    assert mapped["score_included"] is False


def test_official_direct_negative_event_can_reach_stock_risk_gate() -> None:
    event = PolicyEventIntelligence().enrich_items([_official_item()])[0]
    mapper = GlobalIndustryMapper()
    mapped = mapper.map_item(event, "300274", mapper.company_exposure("300274", name="阳光电源"))

    assert event["confirmation_level"] == "official_confirmed"
    assert event["event_stage"] == "official"
    assert event["trade_gate"] == "candidate_block"
    assert mapped["is_related_to_symbol"] is True
    assert mapped["score_included"] is True
    assert mapped["mapped_trade_gate"] == "block_new_position"
    assert mapped["sentiment_score"] <= 22
    assert "公司海外业务预期" in mapped["transmission_chain"]


def test_direct_draft_event_is_visible_but_not_scored() -> None:
    event = PolicyEventIntelligence().enrich_items([_draft_item()])[0]
    mapper = GlobalIndustryMapper()
    mapped = mapper.map_item(event, "300274", mapper.company_exposure("300274", name="阳光电源"))

    assert mapped["is_related_to_symbol"] is True
    assert mapped["score_included"] is False
    assert mapped["mapped_trade_gate"] == "manual_confirmation"


def test_federal_register_parser_keeps_only_market_relevant_documents(tmp_path) -> None:
    class Response:
        @staticmethod
        def json() -> dict:
            return {
                "results": [
                    {
                        "title": "Restrictions on Foreign-Produced Power Inverters",
                        "abstract": "A final rule restricts foreign-produced power inverter equipment used by the electric grid.",
                        "type": "Rule",
                        "document_number": "2026-TEST",
                        "publication_date": "2026-08-26",
                        "html_url": "https://www.federalregister.gov/documents/2026/08/26/test",
                        "agencies": [{"name": "Department of Energy"}],
                    },
                    {
                        "title": "Routine Museum Committee Meeting",
                        "abstract": "The committee will discuss museum operations.",
                        "type": "Notice",
                        "document_number": "2026-OTHER",
                        "publication_date": "2026-08-26",
                        "html_url": "https://www.federalregister.gov/documents/2026/08/26/other",
                        "agencies": [{"name": "National Archives"}],
                    },
                ]
            }

    class Http:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    service = NewsAnalysisService(cache_file=tmp_path / "news.json")
    service.http = Http()
    service.policy_http = Http()
    rows = service._search_federal_register(limit=20)

    assert len(rows) == 1
    assert rows[0]["_source_name"] == "美国联邦公报"
    assert rows[0]["_content_quality_status"] == "structured_excerpt"
    assert rows[0]["链接"].startswith("https://www.federalregister.gov/")


def test_context_direction_distinguishes_weak_data_and_policy_relief() -> None:
    engine = PolicyEventIntelligence()
    weak_data, relief = engine.enrich_items(
        [
            {
                "title": "芬兰八月消费者信心指数下降3.0点",
                "source": "金十数据7x24",
                "url": "https://flash.jin10.com/detail/test-confidence",
                "published_at": "2026-08-27T13:00:00",
            },
            {
                "title": "官方宣布解除半导体设备出口限制并给予豁免",
                "source": "美国联邦公报",
                "url": "https://www.federalregister.gov/documents/test-relief",
                "published_at": "2026-08-27T14:00:00",
            },
        ]
    )

    assert weak_data["event_type"] == "economic_data_release"
    assert weak_data["event_direction"] == "negative"
    assert "下降" in weak_data["event_direction_reason_cn"]
    assert relief["event_type"] == "export_or_import_restriction"
    assert relief["event_direction"] == "positive"
    assert relief["trade_gate"] == "observe"


def test_short_english_topic_terms_do_not_match_inside_unrelated_words() -> None:
    event = PolicyEventIntelligence().enrich_item(
        {
            "title": "Safety Zone on Navigable Waters",
            "summary": "A temporary safety zone is established for transportation operations.",
            "source": "美国联邦公报",
            "url": "https://www.federalregister.gov/documents/test-safety-zone",
        }
    )

    assert event["event_type"] == "general_information"
    assert event["affected_industries_cn"] == []
