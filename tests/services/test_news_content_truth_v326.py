from __future__ import annotations

from datetime import datetime, timedelta

from quant_data.services.information_event_calendar_service import InformationEventCalendarService
from quant_data.services.news_service import NewsAnalysisService


class _AnnouncementResponse:
    def json(self):
        return {
            "success": 1,
            "data": {
                "art_code": "AN202608071827754983",
                "notice_title": "阳光电源:关于首次回购公司股份的公告",
                "notice_date": "2026-08-07 00:00:00",
                "attach_url_web": "https://pdf.dfcfw.com/pdf/H2_AN202608071827754983_1.pdf",
                "notice_content": (
                    "阳光电源股份有限公司于2026年8月6日首次回购公司股份471800股，"
                    "占公司总股本的0.0228%，最高成交价106.64元，最低成交价105.26元，"
                    "支付总金额49993778元。本次回购符合既定回购方案。"
                ),
            },
        }


def test_eastmoney_announcement_uses_public_content_endpoint(monkeypatch):
    service = NewsAnalysisService()
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _AnnouncementResponse()

    monkeypatch.setattr(service.http, "get", fake_get)
    item = service._score_item(
        "阳光电源:关于首次回购公司股份的公告",
        "https://data.eastmoney.com/notices/detail/300274/AN202608071827754983.html",
        "东方财富公告",
        "2026-08-07",
        "",
        "300274",
        "阳光电源",
        source_type="announcement",
    )
    enriched = service._enrich_announcement_content([item], max_items=1)[0]

    assert calls[0][0] == "https://np-cnotice-stock.eastmoney.com/api/content/ann"
    assert "471800股" in enriched.summary
    assert "股 港股 期货 外汇" not in enriched.summary
    assert enriched.content_quality_status == "full_text"
    assert enriched.content_loaded is True
    assert enriched.attachment_url.endswith("AN202608071827754983_1.pdf")
    assert len(enriched.content_hash) == 64


def test_cached_page_chrome_is_removed_before_scoring():
    service = NewsAnalysisService()
    item = service._item_from_dict({
        "title": "阳光电源:关于首次回购公司股份的公告",
        "url": "https://data.eastmoney.com/notices/detail/300274/AN202608071827754983.html",
        "source": "东方财富公告",
        "source_type": "announcement",
        "published_at": "2026-08-07",
        "summary": "股 港股 期货 外汇 黄金 银行 基金 东方财富网 > 数据中心 > 公告大全 郑重声明 本网不保证其真实性和客观性",
        "content_loaded": True,
        "evidence": ["质押/冻结风险", "分红"],
    })

    assert item.summary == ""
    assert item.content_loaded is False
    assert item.content_quality_status == "boilerplate_rejected"
    assert "已拒绝" in item.content_missing_reason
    assert item.evidence == ["股东增持/回购", "公司回购/股东增持"]
    aggregate = service._aggregate("300274", "阳光电源", [item])
    assert aggregate["data_quality"]["current_scoring_count"] == 0
    assert aggregate["data_quality"]["quality_excluded_count"] == 1
    assert aggregate["news_score"] == 50.0


def test_investor_relations_announcement_is_not_mislabeled_as_forum():
    service = NewsAnalysisService()

    item = service._score_item(
        "阳光电源投资者关系活动记录表20260715",
        "https://data.eastmoney.com/notices/detail/300274/AN202607151826999765.html",
        "东方财富公告",
        "2026-07-15",
        "",
        "300274",
        "阳光电源",
        source_type="announcement",
    )

    assert item.category == "公司公告"
    assert item.message_dimension == "官方公告/公司披露"


def test_duplicate_event_keeps_sources_but_scores_once():
    service = NewsAnalysisService()
    event_day = (datetime.now() + timedelta(days=5)).date().isoformat()
    first = service._score_item(
        f"测试公司将于{event_day}召开2026年第一次临时股东大会",
        "https://example.com/official",
        "巨潮资讯公告",
        datetime.now().date().isoformat(),
        f"测试公司将于{event_day}召开临时股东大会。",
        "000001",
        "测试公司",
        source_type="announcement",
    )
    second = service._score_item(
        f"测试公司临时股东大会会议日期为{event_day}",
        "https://example.com/media",
        "新浪财经",
        datetime.now().date().isoformat(),
        f"测试公司公告显示会议将于{event_day}召开。",
        "000001",
        "测试公司",
        source_type="news",
    )
    deduped = service._deduplicate([first, second])
    aggregate = service._aggregate("000001", "测试公司", deduped)

    assert len(deduped) == 1
    assert deduped[0].duplicate_count == 2
    assert set(deduped[0].duplicate_sources or []) == {"巨潮资讯公告", "新浪财经"}
    assert len(deduped[0].duplicate_source_refs or []) == 2
    assert aggregate["data_quality"]["merged_duplicate_count"] == 1
    assert aggregate["data_quality"]["event_core_count"] == 1


def test_similar_progress_announcements_on_different_dates_are_not_duplicates():
    service = NewsAnalysisService()
    first = service._score_item(
        "测试公司:关于担保额度预计的进展公告",
        "https://data.eastmoney.com/notices/detail/000001/AN202608010001.html",
        "东方财富公告",
        "2026-08-01",
        "8月担保进展公告。",
        "000001",
        "测试公司",
        source_type="announcement",
    )
    second = service._score_item(
        "测试公司:关于担保额度预计的进展公告",
        "https://data.eastmoney.com/notices/detail/000001/AN202608150002.html",
        "东方财富公告",
        "2026-08-15",
        "8月中旬另一笔担保进展公告。",
        "000001",
        "测试公司",
        source_type="announcement",
    )

    deduped = service._deduplicate([first, second])

    assert len(deduped) == 2
    assert all(item.duplicate_count == 1 for item in deduped)


def test_similar_official_documents_on_same_day_remain_separate():
    service = NewsAnalysisService()
    first = service._score_item(
        "测试公司:独立董事候选人声明与承诺(张三)",
        "https://data.eastmoney.com/notices/detail/000001/AN202608240001.html",
        "东方财富公告",
        "2026-08-24",
        "",
        "000001",
        "测试公司",
        source_type="announcement",
    )
    second = service._score_item(
        "测试公司:独立董事候选人声明与承诺(李四)",
        "https://data.eastmoney.com/notices/detail/000001/AN202608240002.html",
        "东方财富公告",
        "2026-08-24",
        "",
        "000001",
        "测试公司",
        source_type="announcement",
    )

    assert len(service._deduplicate([first, second])) == 2


def test_announcement_body_recomputes_future_meeting_date(monkeypatch):
    service = NewsAnalysisService()

    class _MeetingResponse:
        def json(self):
            return {
                "success": 1,
                "data": {
                    "art_code": "AN202608241828000001",
                    "notice_title": "测试公司临时股东大会通知",
                    "notice_date": "2026-08-24 00:00:00",
                    "notice_content": (
                        "测试公司将于2026年8月28日召开2026年第一次临时股东大会。"
                        "本次会议将审议年度经营计划及相关议案，股权登记日和网络投票安排以本公告为准。"
                        "公司董事会保证本公告内容真实、准确、完整。"
                    ),
                },
            }

    monkeypatch.setattr(service.http, "get", lambda *args, **kwargs: _MeetingResponse())
    item = service._score_item(
        "测试公司临时股东大会通知",
        "https://data.eastmoney.com/notices/detail/000001/AN202608241828000001.html",
        "东方财富公告",
        "2026-08-24",
        "",
        "000001",
        "测试公司",
        source_type="announcement",
    )

    enriched = service._enrich_announcement_content([item], max_items=1)[0]

    assert enriched.event_time == "2026-08-28"
    assert enriched.event_type == "shareholder_meeting"


def test_future_calendar_separates_confirmed_and_rule_dates():
    now = datetime(2026, 8, 24, 10, 0)
    result = InformationEventCalendarService().build(
        "159915",
        "创业板ETF",
        items=[{
            "title": "创业板ETF基金份额持有人大会通知",
            "event_type": "shareholder_meeting",
            "event_time": "2026-08-28",
            "published_at": "2026-08-20",
            "source": "交易所公告",
            "source_type": "announcement",
            "credibility_score": 95,
            "url": "https://example.com/notice.pdf",
        }],
        now=now,
        horizon_days=50,
    )

    assert result["score_included"] is False
    assert result["confirmed_count"] >= 1
    assert result["rule_inferred_count"] >= 1
    assert any(row["confirmation_status"] == "公开来源已确认" for row in result["events"])
    assert any(row["event_type"] in {"derivatives_settlement", "etf_option_expiry", "reporting_window"} for row in result["events"])
    assert sum(row["event_type"] == "reporting_window" for row in result["events"]) >= 2
    assert all(row["impact_direction"] == "结果待确认" for row in result["events"])
