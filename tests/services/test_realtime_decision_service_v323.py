from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from quant_data.data.earnings_snapshot import EarningsSnapshot
from quant_data.data.pit_store import PITStore
from quant_data.models import AssetType, Bar, IntradayPoint, Quote
from quant_data.services.market_event_factor_service import MarketEventFactorService
from quant_data.services.market_regime_service import MarketRegimeService
from quant_data.services.realtime_decision_service import RealtimeDecisionService
from quant_data.trading.signal_fusion import SignalFusionEngine


class _Cache:
    def __init__(self, *, bars=None, points=None, quotes=None):
        self.bars = bars or []
        self.points = points or []
        self.quotes = quotes or {}

    def get_bars(self, symbol, frame, limit=90, max_age_seconds=None):
        return self.bars[-limit:]

    def get_intraday(self, symbol):
        return list(self.points)

    def get_quote(self, symbol, max_age_seconds=None):
        return self.quotes.get(symbol)


class _InfoCache:
    def __init__(self, payload=None):
        self.payload = payload or {}

    def latest_info_snapshot(self, symbol):
        return SimpleNamespace(
            data=self.payload,
            cache_status={"status": "hit", "stale": False, "snapshot_id": "info-1", "created_at": datetime.now().isoformat()},
        )


def _bars():
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = []
    for index in range(70):
        close = 10 + index * 0.04
        rows.append(
            Bar(
                symbol="600438",
                frame="1d",
                ts=now - timedelta(days=69 - index),
                open=close - 0.03,
                high=close + 0.08,
                low=close - 0.08,
                close=close,
                volume=100_000 + index * 1_000,
                amount=close * (100_000 + index * 1_000),
                source="unit_cache",
            )
        )
    return rows


def _points(last_price: float):
    now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    return [
        IntradayPoint(
            symbol="600438",
            ts=now + timedelta(minutes=index),
            price=last_price - 0.15 + index * 0.01,
            avg_price=last_price - 0.08,
            volume=1_000 + index * 20,
            amount=(1_000 + index * 20) * last_price,
            source="unit_intraday",
        )
        for index in range(20)
    ]


def _quote(symbol: str = "600438", change_pct: float = 1.0) -> Quote:
    return Quote(
        symbol=symbol,
        name="通威股份",
        ts=datetime.now(),
        last=12.0,
        pre_close=11.88,
        open=11.9,
        high=12.1,
        low=11.82,
        volume=200_000,
        amount=2_400_000,
        change=0.12,
        change_pct=change_pct,
        turnover=1.2,
        volume_ratio=1.3,
        market="CN",
        asset_type=AssetType.STOCK,
        source="unit_quote",
    )


def _service(*, info=None, points=None):
    cache = _Cache(bars=_bars(), points=points or _points(12.0), quotes={"600438": _quote()})
    return RealtimeDecisionService(
        SimpleNamespace(cache=cache),
        _InfoCache(info),
        MarketRegimeService(),
    )


def test_realtime_decision_combines_screener_daily_and_intraday_scores():
    service = _service()
    profile = {
        "final_score": 68,
        "technical_score": 59,
        "fundamental_score": 62,
        "fund_flow_score": 54,
        "market_score": 51,
        "source": "screener_snapshot",
    }
    weak = service.hydrate(
        {
            "symbol": "600438",
            "quote": {**_quote(change_pct=-2.0).to_dict(), "bid1": 11.95, "ask1": 11.97, "orderbook_source": "unit_book"},
        },
        profile=profile,
        symbols=["600438"],
    )
    strong = service.hydrate(
        {
            "symbol": "600438",
            "quote": {**_quote(change_pct=3.0).to_dict(), "last": 12.3, "bid1": 12.29, "ask1": 12.3, "orderbook_source": "unit_book"},
        },
        profile=profile,
        symbols=["600438"],
    )

    assert weak["screening_score"] == strong["screening_score"] == 68
    assert weak["daily_k_score"] == strong["daily_k_score"]
    assert weak["intraday_score"] < strong["intraday_score"]
    assert weak["technical_score"] < strong["technical_score"]
    assert strong["score_source"] == "server_cache_realtime_decision_v323"
    assert "日K55%+分时45%" in strong["score_breakdown"]["formula"]


def test_realtime_information_uses_recent_dated_evidence_only():
    now = datetime.now()
    service = _service(
        info={
            "snapshot_id": "info-1",
            "items": [
                {
                    "title": "近期订单落地",
                    "source": "巨潮资讯",
                    "source_type": "announcement",
                    "published_at": (now - timedelta(days=2)).isoformat(),
                    "sentiment_score": 72,
                    "credibility_score": 92,
                    "impact_score": 80,
                    "url": "https://example.com/recent",
                },
                {
                    "title": "过期旧闻",
                    "source": "历史档案",
                    "source_type": "news",
                    "published_at": (now - timedelta(days=200)).isoformat(),
                    "sentiment_score": 5,
                },
                {"title": "日期未知转载", "source": "转载", "sentiment_score": 5},
            ],
        }
    )

    result = service.hydrate({"symbol": "600438", "quote": _quote().to_dict()}, profile={"final_score": 60})
    info = result["recent_information"]

    assert info["recent_count"] == 1
    assert info["excluded_count"] == 2
    assert info["score"] > 60
    assert info["items"][0]["source_ref"] == "https://example.com/recent"


def test_missing_orderbook_is_explicit_and_never_fabricated():
    result = _service().hydrate({"symbol": "600438", "quote": _quote().to_dict()}, profile={"final_score": 60})

    assert result["orderbook_snapshot"]["status"] == "missing"
    assert result["orderbook_snapshot"]["bid1"] is None
    assert "orderbook_missing" in result["missing_data"]


def test_traceable_pit_earnings_changes_realtime_information_and_trade_score(tmp_path):
    store = PITStore(tmp_path / "decision-pit.sqlite")
    available_at = datetime.now() - timedelta(hours=2)
    snapshot = EarningsSnapshot(
        symbol="600438",
        report_period="2026H1",
        announced_at=available_at.isoformat(timespec="seconds"),
        available_at=available_at.isoformat(timespec="seconds"),
        surprise=45.0,
        source_id="cninfo",
        source_name="巨潮资讯公告",
        source_url="https://www.cninfo.com.cn/traceable-earnings",
    )
    for record in snapshot.to_event().to_pit_records():
        store.put(record)

    base = _service().hydrate(
        {"symbol": "600438", "quote": _quote().to_dict()},
        profile={"final_score": 60, "fundamental_score": 60, "fund_flow_score": 55, "market_score": 50},
    )
    market_data = _Cache(bars=_bars(), points=_points(12.0), quotes={"600438": _quote()})
    event_service = MarketEventFactorService(pit_store=store)
    enriched_service = RealtimeDecisionService(
        SimpleNamespace(cache=market_data),
        _InfoCache(),
        MarketRegimeService(),
        event_service,
    )
    enriched = enriched_service.hydrate(
        {"symbol": "600438", "quote": _quote().to_dict()},
        profile={"final_score": 60, "fundamental_score": 60, "fund_flow_score": 55, "market_score": 50},
    )

    def trade_score(row):
        return SignalFusionEngine().fuse(
            symbol="600438",
            screening_score=row.get("screening_score"),
            fundamental_score=row.get("fundamental_score"),
            technical_score=row.get("technical_score"),
            information_score=row.get("information_score"),
            fund_flow_score=row.get("fund_flow_score"),
            market_score=row.get("market_score"),
        ).final_score

    assert enriched["information_score"] > base["information_score"]
    assert trade_score(enriched) > trade_score(base)
    assert enriched["market_event_context"]["pit_input_status"]["datasets"]["earnings"]["status"] == "available"
    assert any(
        row["factor_key"] == "earnings_surprise"
        for row in enriched["score_breakdown"]["event_factors"]
    )
