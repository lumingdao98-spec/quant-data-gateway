from datetime import datetime

from quant_data.models import AssetType, Quote
from quant_data.services.candidate_pool_service import CandidatePoolService


def _quote(i: int) -> Quote:
    return Quote(
        symbol=f"60{i:04d}",
        name=f"测试{i}",
        ts=datetime.now(),
        last=10 + i * 0.01,
        pre_close=10,
        open=10,
        high=10.4,
        low=9.8,
        volume=100_000 + i,
        amount=30_000_000 + i * 8_000_000,
        change=0.1,
        change_pct=(i % 12) - 2,
        turnover=(i % 20) + 0.2,
        volume_ratio=1 + (i % 7) * 0.25,
        pe_dynamic=10 + i % 30,
        pb=1 + (i % 5) * 0.2,
        total_market_cap=80_000_000_000 + i * 100_000_000,
        float_market_cap=60_000_000_000 + i * 80_000_000,
        asset_type=AssetType.STOCK,
        source="unit",
    )


def test_candidate_pool_has_three_channels_and_metadata():
    pool = CandidatePoolService().build([_quote(i) for i in range(90)], max_items=50)
    candidates = pool["candidates"]

    assert pool["candidate_count"] == len(candidates)
    assert pool["rules"]["channel1"].startswith("换手率TOP50")
    assert pool["rules"]["channel2"].startswith("成交额TOP20")
    assert "技术初筛" in pool["rules"]["channel3"]
    assert any("turnover_top50" in x["channels"] for x in candidates)
    assert any("amount_top20" in x["channels"] for x in candidates)
    assert any("technical_seed" in x["channels"] for x in candidates)
    assert all(x["reason"] and isinstance(x["rank_score"], float) for x in candidates)
