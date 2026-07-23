from datetime import datetime

from quant_data.data import EarningsSnapshot, IpoSnapshot, PITStore
from quant_data.services.market_event_factor_service import MarketEventFactorService


NOW = datetime(2026, 7, 20, 12, 0, 0)


def _item(title: str, *, published_at: str = "2026-07-17T10:00:00") -> dict:
    return {
        "title": title,
        "summary": title,
        "published_at": published_at,
        "source": "测试权威源",
        "source_ref": "https://example.com/evidence",
    }


def test_global_technology_selloff_only_adjusts_market_for_unrelated_stock():
    context = MarketEventFactorService().build_context(
        symbol="600519",
        name="贵州茅台",
        profile={"industry": "白酒", "main_business": "高端白酒"},
        global_items=[_item("纳斯达克科技股和芯片股抛售，AI交易承压")],
        now=NOW,
    )

    assert context["market_adjustment"] < 0
    assert context["information_adjustment"] == 0
    assert all(row["scope"] == "市场环境" for row in context["factors"])
    assert "global_semis_drawdown" in {row["factor_key"] for row in context["factors"]}


def test_changxin_ipo_has_market_drag_and_bounded_dram_chain_catalyst():
    context = MarketEventFactorService().build_context(
        symbol="688001",
        name="存储设备公司",
        profile={"industry": "半导体设备", "main_business": "DRAM存储芯片制造设备"},
        global_items=[_item("长鑫科技首次公开发行预计募资579亿元，推进国产DRAM产业链")],
        now=NOW,
    )

    keys = {row["factor_key"] for row in context["factors"]}
    assert context["market_adjustment"] <= -8
    assert context["information_adjustment"] == 4
    assert "ipo_liquidity_shock" in keys
    assert "dram_supply_chain_catalyst" in keys


def test_changxin_ipo_does_not_adjust_unrelated_company_information_score():
    context = MarketEventFactorService().build_context(
        symbol="600519",
        name="贵州茅台",
        profile={"industry": "白酒", "main_business": "高端白酒"},
        global_items=[_item("长鑫科技首次公开发行预计募资579亿元")],
        now=NOW,
    )

    assert context["market_adjustment"] < 0
    assert context["information_adjustment"] == 0
    assert "dram_supply_chain_catalyst" not in {row["factor_key"] for row in context["factors"]}


def test_future_event_is_excluded_from_score():
    context = MarketEventFactorService().build_context(
        symbol="300750",
        name="宁德时代",
        profile={"industry": "动力电池"},
        global_items=[_item("纳斯达克科技股抛售", published_at="2026-07-21T10:00:00")],
        now=NOW,
    )

    assert context["factor_count"] == 0
    assert context["excluded_future"] == 1
    assert context["market_adjustment"] == 0


def test_standard_factor_coverage_keeps_missing_inputs_missing_instead_of_zero():
    context = MarketEventFactorService().build_context(
        symbol="300750",
        name="宁德时代",
        profile={"industry": "动力电池"},
        global_items=[],
        now=NOW,
    )

    coverage = {row["factor_key"]: row for row in context["standard_factor_coverage"]}
    assert context["standard_factor_available"] == 0
    assert context["standard_factor_total"] == 8
    assert coverage["earnings_surprise"]["status"] == "missing"
    assert "0 分" in coverage["earnings_surprise"]["missing_reason"]


def test_structured_factors_require_pit_timestamp_and_traceable_source():
    context = MarketEventFactorService().build_context(
        symbol="688146",
        name="中船特气",
        profile={"industry": "电子特气"},
        global_items=[],
        structured_inputs={
            "earnings": {
                "earnings_surprise_pct": 18.5,
                "guidance_delta_pct": 12.0,
                "available_at": "2026-07-17T18:00:00",
                "source_name": "交易所公告",
                "source_url": "https://example.com/announcement",
            },
            "fund_flow": {
                "northbound_regime_score": -30,
                "available_at": "2026-07-21T09:00:00",
                "source_name": "未来数据",
                "source_url": "https://example.com/future",
            },
        },
        now=NOW,
    )

    keys = {row["factor_key"] for row in context["factors"]}
    coverage = {row["factor_key"]: row for row in context["standard_factor_coverage"]}
    assert {"earnings_surprise", "guidance_delta"}.issubset(keys)
    assert "northbound_flow_regime" not in keys
    assert "PIT" in coverage["northbound_flow_regime"]["missing_reason"]


def test_yoy_growth_text_is_not_mistaken_for_earnings_surprise():
    context = MarketEventFactorService().build_context(
        symbol="688146",
        name="中船特气",
        profile={"industry": "电子特气", "main_business": "电子特种气体"},
        global_items=[_item("中船特气上半年净利润3.48亿元，同比增长95.63%")],
        now=NOW,
    )

    assert "earnings_surprise" not in {row["factor_key"] for row in context["factors"]}


def test_competitor_listing_pressure_requires_explicit_symbol_mapping():
    base = {
        "competitor_listing_pressure": 60,
        "available_at": "2026-07-17T10:00:00",
        "source_name": "招股书",
        "source_url": "https://example.com/prospectus",
    }
    unrelated = MarketEventFactorService().build_context(
        symbol="600519",
        global_items=[],
        structured_inputs={"ipo": {**base, "competitor_symbols": ["688001"]}},
        now=NOW,
    )
    related = MarketEventFactorService().build_context(
        symbol="688001",
        global_items=[],
        structured_inputs={"ipo": {**base, "competitor_symbols": ["688001"]}},
        now=NOW,
    )

    assert "competitor_listing_pressure" not in {row["factor_key"] for row in unrelated["factors"]}
    assert "competitor_listing_pressure" in {row["factor_key"] for row in related["factors"]}


def test_pit_structured_snapshots_automatically_enter_realtime_event_scores(tmp_path):
    store = PITStore(tmp_path / "pit.sqlite")
    earnings = EarningsSnapshot(
        symbol="688146",
        report_period="2026H1",
        announced_at="2026-07-17T18:00:00",
        available_at="2026-07-17T18:00:00",
        net_profit=3.48,
        consensus_profit=2.90,
        guidance_low=3.2,
        guidance_high=3.7,
        surprise=20.0,
        source_id="cninfo",
        source_name="巨潮资讯公告",
        source_url="https://www.cninfo.com.cn/example",
    )
    for record in earnings.to_event().to_pit_records():
        store.put(record)
    ipo = IpoSnapshot(
        issuer_symbol="688999",
        issuer_name="长鑫科技",
        exchange="上交所",
        announced_at="2026-07-16T18:00:00",
        available_at="2026-07-16T18:00:00",
        liquidity_shock_score=72,
        competitor_listing_pressure=45,
        competitors=["688146"],
        sectors=["半导体材料"],
        source_id="sse_ipo",
        source_name="上海证券交易所",
        source_url="https://www.sse.com.cn/example",
    )
    for record in ipo.to_event().to_pit_records():
        store.put(record)

    context = MarketEventFactorService(pit_store=store).build_context(
        symbol="688146",
        name="中船特气",
        profile={"industry": "半导体材料", "main_business": "电子特种气体"},
        global_items=[],
        now=NOW,
    )

    keys = {row["factor_key"] for row in context["factors"]}
    assert {"earnings_surprise", "ipo_liquidity_shock", "competitor_listing_pressure"} <= keys
    assert context["information_adjustment"] != 0
    assert context["market_adjustment"] < 0
    assert context["pit_input_status"]["datasets"]["earnings"]["status"] == "available"
    assert context["pit_input_status"]["datasets"]["ipo"]["symbol_relevance"] == "direct"


def test_pit_loader_never_uses_future_structured_snapshot(tmp_path):
    store = PITStore(tmp_path / "pit.sqlite")
    future = EarningsSnapshot(
        symbol="688146",
        report_period="2026H1",
        announced_at="2026-07-21T18:00:00",
        available_at="2026-07-21T18:00:00",
        surprise=80.0,
        source_id="cninfo",
        source_name="巨潮资讯公告",
        source_url="https://www.cninfo.com.cn/future",
    )
    for record in future.to_event().to_pit_records():
        store.put(record)

    context = MarketEventFactorService(pit_store=store).build_context(
        symbol="688146",
        global_items=[],
        now=NOW,
    )

    assert "earnings_surprise" not in {row["factor_key"] for row in context["factors"]}
    assert context["pit_input_status"]["datasets"]["earnings"]["status"] == "missing"
