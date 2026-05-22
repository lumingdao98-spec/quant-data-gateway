from quant_data.services.news_service import NewsAnalysisService
from quant_data.services.company_profile_service import CompanyProfileService
from quant_data.models import Quote, Bar, AssetType
from quant_data.services.screener_service import ScreenerService
from quant_data.services.market_data_service import MarketDataService
from datetime import datetime, timedelta


def test_shareholder_meeting_dedup_between_f10_and_guba():
    svc = NewsAnalysisService()
    a = svc._score_item(
        "天合光能：将于2026年05月21日召开2025年年度股东大会",
        "https://example.com/a",
        "东方财富F10",
        "2026-05-21",
        "天合光能将于2026年05月21日召开2025年年度股东大会",
        "688599",
        "天合光能",
        source_type="news",
    )
    b = svc._score_item(
        "天合光能：将于2026年05月21日召开2025年年度股东大会",
        "https://example.com/b",
        "东方财富股吧",
        "2026-05-21",
        "阅读评论标题作者最后更新2331天合光能：将于2026年05月21日召开2025年年度股东大会",
        "688599",
        "天合光能",
        source_type="forum",
    )
    got = svc._deduplicate([a, b])
    assert len(got) == 1
    assert "同事件合并" in got[0].dedup_reason


def test_company_profile_has_business_exposure_for_trina():
    p = CompanyProfileService().get_profile("688599", force=False)
    assert "光伏" in " ".join(p.get("business_tags") or [])
    assert p.get("industry_exposure_text")


def test_drawdown_definition_is_negative_from_high():
    q = Quote(
        symbol="000001",
        name="测试",
        ts=datetime.now(),
        last=80,
        pre_close=79,
        open=80,
        high=82,
        low=78,
        volume=1000,
        amount=100000,
        change=1,
        change_pct=1.2,
        asset_type=AssetType.STOCK,
    )
    start = datetime.now() - timedelta(days=100)
    bars = []
    for i in range(100):
        price = 100 if i == 20 else 80 + i * 0.01
        bars.append(Bar(symbol="000001", frame="1d", ts=start + timedelta(days=i), open=price, high=price, low=price, close=price, volume=1, amount=1))
    result = ScreenerService(MarketDataService()).analyze(q, bars, kline_adjust="qfq")
    assert result.drawdown250 is not None
    assert result.drawdown250 <= 0
    assert result.drawdown_basis["formula"].startswith("drawdown250")
