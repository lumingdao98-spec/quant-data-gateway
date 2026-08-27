from __future__ import annotations

from types import SimpleNamespace

import quant_data.api as api


def test_restored_screener_row_uses_quote_cache_and_removes_stale_missing_hints(monkeypatch) -> None:
    cache_read = SimpleNamespace(
        data={
            "quote": {
                "symbol": "300274",
                "name": "阳光电源",
                "industry": "光伏设备",
                "pe_dynamic": 22.22,
                "pe_ttm": 22.22,
                "pb": 4.31,
                "turnover": 8.02,
                "turnover_rate": 8.02,
                "total_market_cap": 203630826065,
                "metric_sources": {
                    "industry": "eastmoney.f100",
                    "pe_dynamic": "eastmoney",
                    "pb": "eastmoney",
                    "turnover": "eastmoney",
                    "total_market_cap": "eastmoney",
                },
                "metric_missing_reasons": [],
            }
        },
        cache_status={"status": "fresh", "stale": False},
    )
    monkeypatch.setattr(api.cache_state_service, "get", lambda *args, **kwargs: cache_read)

    rows = api._reconcile_screener_rows_from_quote_cache(
        [
            {
                "symbol": "300274",
                "name": "阳光电源",
                "metric_missing_reasons": [
                    "行情源缺失 PE",
                    "行情源缺失 PB",
                    "行情源缺失换手率",
                    "东方财富 push2 未返回总市值",
                ],
            }
        ]
    )
    row = rows[0]

    assert row["industry"] == "光伏设备"
    assert row["pe_dynamic"] == 22.22
    assert row["pb"] == 4.31
    assert row["turnover_rate"] == 8.02
    assert row["total_market_cap"] == 203630826065
    assert row["metric_missing_reasons"] == []
    assert "光伏设备" in row["theme_labels"]
