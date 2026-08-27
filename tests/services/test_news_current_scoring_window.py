from datetime import datetime, timedelta

from quant_data.services.news_service import NewsAnalysisService, NewsItem


def _news(
    title: str,
    *,
    days_ago: int | None,
    sentiment: float,
    source_type: str = "news",
    event_type: str = "general_news",
    event_time: str | None = None,
    risk_tag: str = "",
) -> NewsItem:
    published = None if days_ago is None else (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return NewsItem(
        title=title,
        url=f"https://example.com/{abs(hash(title))}",
        source="测试权威源",
        source_type=source_type,
        event_type=event_type,
        event_time=event_time,
        published_at=published,
        published_at_norm=published,
        summary=title,
        relevance_score=90,
        sentiment_score=sentiment,
        credibility_score=90,
        impact_score=75,
        fake_risk_score=5,
        risk_tag=risk_tag,
        event_key=title,
        event_weight=1.2,
    )


def test_current_information_score_excludes_old_and_unknown_news():
    service = NewsAnalysisService()
    result = service._aggregate(
        "600438",
        "通威股份",
        [
            _news("近期订单落地", days_ago=2, sentiment=72),
            _news("两年前历史风险", days_ago=730, sentiment=10, source_type="announcement"),
            _news("日期未知转载", days_ago=None, sentiment=5),
        ],
    )

    assert result["news_score"] > 50
    assert result["data_quality"]["current_scoring_count"] == 1
    assert result["data_quality"]["historical_excluded_count"] == 2
    assert result["official_negative_count"] == 0


def test_no_recent_verifiable_information_keeps_neutral_score():
    service = NewsAnalysisService()
    result = service._aggregate(
        "600438",
        "通威股份",
        [_news("过期历史公告", days_ago=365, sentiment=10, source_type="announcement")],
    )

    assert result["news_score"] == 50.0
    assert result["sentiment"] == "neutral"
    assert "近期计分窗口" in result["risk_flags"][0]


def test_generic_announcement_does_not_remain_current_for_half_a_year():
    service = NewsAnalysisService()
    result = service._aggregate(
        "300274",
        "阳光电源",
        [_news("两个月前普通董事会公告", days_ago=60, sentiment=50, source_type="announcement", event_type="board_meeting")],
    )

    assert result["data_quality"]["current_scoring_count"] == 0
    assert result["data_quality"]["historical_excluded_count"] == 1


def test_financial_report_keeps_a_longer_but_bounded_current_window():
    service = NewsAnalysisService()
    result = service._aggregate(
        "300274",
        "阳光电源",
        [_news("年度报告经营数据", days_ago=100, sentiment=62, source_type="announcement", event_type="financial_report")],
    )

    assert result["data_quality"]["current_scoring_count"] == 1


def test_future_event_result_is_visible_but_cannot_change_current_score():
    service = NewsAnalysisService()
    future = (datetime.now() + timedelta(days=14)).isoformat(timespec="seconds")
    result = service._aggregate(
        "300274",
        "阳光电源",
        [_news("两周后召开股东大会", days_ago=0, sentiment=68, source_type="announcement", event_type="shareholder_meeting", event_time=future)],
    )

    assert result["data_quality"]["current_scoring_count"] == 0
    assert result["data_quality"]["upcoming_observation_count"] == 1
    assert result["data_quality"]["historical_excluded_count"] == 0
    assert result["news_score"] == 50.0
