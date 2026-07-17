from datetime import datetime, timedelta

from quant_data.services.news_service import NewsAnalysisService, NewsItem


def _news(title: str, *, days_ago: int | None, sentiment: float, source_type: str = "news") -> NewsItem:
    published = None if days_ago is None else (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return NewsItem(
        title=title,
        url=f"https://example.com/{abs(hash(title))}",
        source="测试权威源",
        source_type=source_type,
        published_at=published,
        published_at_norm=published,
        summary=title,
        relevance_score=90,
        sentiment_score=sentiment,
        credibility_score=90,
        impact_score=75,
        fake_risk_score=5,
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
