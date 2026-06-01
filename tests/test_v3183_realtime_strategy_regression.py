from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import quant_data.api as api
from quant_data.models import IntradayPoint, OrderBook, OrderBookLevel, Quote
from quant_data.providers.eastmoney import EastmoneyProvider
from quant_data.providers.provider_manager import ProviderManager
from quant_data.providers.sina import SinaProvider
from quant_data.screener_ui import build_screener_ui
from quant_data.services.cache_state_service import CacheStateService


def _quote(symbol: str = "300750", price: float = 403.0) -> Quote:
    return Quote(
        symbol=symbol,
        name="CATL",
        ts=datetime(2026, 5, 26, 11, 20),
        last=price,
        pre_close=402.0,
        open=406.0,
        high=409.0,
        low=400.0,
        volume=100000,
        amount=4_030_000_000,
        change=1.0,
        change_pct=0.25,
        turnover=0.45,
        volume_ratio=1.6,
        pe_dynamic=22.5,
        pb=5.7,
        total_market_cap=1_860_000_000_000,
        float_market_cap=1_710_000_000_000,
        source="eastmoney",
    )


def test_screener_strategy_uses_immediate_fallback_not_loading():
    html = TestClient(api.app).get("/screener").text
    assert "startup fallback" in html
    assert "useFallbackStrategyLibrary('startup fallback')" in html
    assert "strategyInlineBox" in html
    assert "screener-actions" in html
    assert "renderStrategyInline" in html
    assert "策略库加载中" not in html


def test_screener_script_is_parseable_so_buttons_work(tmp_path):
    html = build_screener_ui()
    match = re.search(r"<script>([\s\S]*)</script>", html)
    assert match, "screener page must include its action script"
    script = match.group(1)
    assert "js.scroll_position??localStorage.getItem(LS_SCROLL)||0" not in script

    candidates = [
        os.environ.get("NODE"),
        shutil.which("node"),
        str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"),
    ]
    node = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            probe = subprocess.run([candidate, "--version"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            node = candidate
            break
    if not node:
        pytest.skip("node executable is not available for browser-script parse check")

    check = tmp_path / "screener_script_check.js"
    check.write_text("new Function(" + repr(script) + "); console.log('ok')", encoding="utf-8")
    result = subprocess.run([node, str(check)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_ui_starts_active_session_with_force_refresh_and_compact_subcharts():
    html = TestClient(api.app).get("/ui").text
    assert "shouldForceActiveRefresh" in html
    assert "loadQuotes(active)" in html
    assert "refreshDetail(active)" in html
    assert "quant_postclose_refresh_cn_" in html
    assert "postCloseRefreshUsed" in html
    assert "quant_postclose_refresh_'+currentSymbol" not in html
    assert "currentMode==='time'&&tcache.symbol===currentSymbol" in html
    assert "currentMode='time';$('chartLabel')" not in html
    assert "mr.height>80" in html
    assert "?'分时':'K线')+'刷新中" in html
    assert "currentQuoteExtra=js.quote_extra" in html
    assert "limitUp=extra.limit_up" in html
    assert "grid-template-rows:52px 1fr 82px" in html
    assert "max-height:52px" in html
    assert "MACD指标" in html
    assert "均线5/10/20" in html
    assert "subCanvas3" in html
    assert "副图3：KDJ" in html
    assert "timelineCacheUsable" in html
    assert "公开行情源未返回五档盘口" in html
    assert "position:fixed" in html


def _quote_with_ts(symbol: str, ts: datetime) -> Quote:
    q = _quote(symbol=symbol)
    return Quote(
        symbol=q.symbol,
        name=q.name,
        ts=ts,
        last=q.last,
        pre_close=q.pre_close,
        open=q.open,
        high=q.high,
        low=q.low,
        volume=q.volume,
        amount=q.amount,
        change=q.change,
        change_pct=q.change_pct,
        turnover=q.turnover,
        volume_ratio=q.volume_ratio,
        pe_dynamic=q.pe_dynamic,
        pb=q.pb,
        total_market_cap=q.total_market_cap,
        float_market_cap=q.float_market_cap,
        source=q.source,
    )


def test_timeline_refreshes_stale_intraday_cache_during_lunch(monkeypatch):
    q = _quote_with_ts("600438", datetime(2026, 5, 28, 11, 30))
    stale = [
        IntradayPoint("600438", datetime(2026, 5, 26, 9, 30), 15.0, source="unit_stale"),
        IntradayPoint("600438", datetime(2026, 5, 26, 15, 0), 15.2, source="unit_stale"),
    ]
    fresh = [
        IntradayPoint("600438", datetime(2026, 5, 28, 9, 30), 15.1, source="unit_fresh"),
        IntradayPoint("600438", datetime(2026, 5, 28, 11, 30), 15.0, source="unit_fresh"),
    ]
    calls = []

    monkeypatch.setattr(api, "_market_session", lambda market="CN": {"status": "lunch", "date": "2026-05-28"})

    def fake_intraday(symbol, force_refresh=False):
        calls.append(force_refresh)
        return fresh if force_refresh else stale

    monkeypatch.setattr(api.service, "get_intraday", fake_intraday)

    points = api._timeline_with_fallback("600438", q, force=False)

    assert calls == [False, True]
    assert [p.ts.date().isoformat() for p in points] == ["2026-05-28", "2026-05-28"]


def test_timeline_rejects_stale_intraday_cache_if_refresh_still_old(monkeypatch):
    q = _quote_with_ts("600438", datetime(2026, 5, 28, 11, 30))
    stale = [
        IntradayPoint("600438", datetime(2026, 5, 26, 9, 30), 15.0, source="unit_stale"),
        IntradayPoint("600438", datetime(2026, 5, 26, 15, 0), 15.2, source="unit_stale"),
    ]
    monkeypatch.setattr(api, "_market_session", lambda market="CN": {"status": "lunch", "date": "2026-05-28"})
    monkeypatch.setattr(api.service, "get_intraday", lambda symbol, force_refresh=False: stale)

    assert api._timeline_with_fallback("600438", q, force=False) == []


def test_timeline_endpoint_reports_rejected_cross_day_cache(monkeypatch):
    q = _quote_with_ts("600438", datetime(2026, 5, 28, 10, 30))
    stale = [
        IntradayPoint("600438", datetime(2026, 5, 26, 9, 30), 15.0, source="unit_stale"),
        IntradayPoint("600438", datetime(2026, 5, 26, 15, 0), 15.2, source="unit_stale"),
    ]
    monkeypatch.setattr(api, "_market_session", lambda market="CN": {"status": "morning", "date": "2026-05-28", "can_refresh": True})
    monkeypatch.setattr(api, "_enrich_quote_real", lambda *args, **kwargs: (q, q.to_dict(), {"status": "unit"}))
    monkeypatch.setattr(api.service, "get_intraday", lambda symbol, force_refresh=False: stale)

    data = TestClient(api.app).get("/api/timeline/600438?force=true").json()

    assert data["count"] == 0
    assert data["data_quality"]["expected_date"] == "2026-05-28"
    assert data["data_quality"]["stale_cache_rejected"] is True
    assert "未使用跨日缓存" in data["data_quality"]["note"]


def test_screener_explain_row_keeps_snapshot_info_metrics():
    client = TestClient(api.app)
    payload = {
        "tag": "存在监管/诉讼/风险类信息",
        "item": {
            "symbol": "600438",
            "name": "通威股份",
            "total_score": 43.5,
            "manual_review_score": 42.0,
            "technical_score": 51.0,
            "info_score_delta": -6.0,
            "info_effective_count": 13,
            "info_unique_event_count": 7,
            "info_snapshot_id": "snap-test-info",
            "risk_flags": ["存在监管/诉讼/风险类信息"],
            "missing_data_hints": ["行业/板块注释不足"],
        },
    }

    resp = client.post("/api/screener/explain-row", json=payload)
    js = resp.json()

    assert resp.status_code == 200
    assert js["ok"] is True
    metrics = {m["name"]: m["value"] for m in js["data"]["metrics"]}
    assert metrics["信息面调分"] == -6.0
    assert metrics["个股有效条目"] == 13
    assert metrics["去重事件组"] == 7
    assert metrics["快照ID"] == "snap-test-info"
    assert any("风险提示来自当前筛选快照" in x for x in js["data"]["why"])


def test_force_quote_success_does_not_carry_stale_missing_reason(monkeypatch, tmp_path):
    svc = CacheStateService(tmp_path / "cache_state.sqlite")
    monkeypatch.setattr(api, "cache_state_service", svc)
    stale = _quote(price=380.0)
    svc.put("quote_cache", "300750", {"quote": api._quote_dict_with_aliases(stale)}, ttl_seconds=-1, symbol="300750", source="unit")
    live = _quote(price=403.0)
    monkeypatch.setattr(api.service, "get_quote", lambda *args, **kwargs: live)
    monkeypatch.setattr(api.service, "enrich_quote_metrics", lambda q, **kwargs: q)

    _q, data, status = api._enrich_quote_real("300750", force=True)

    assert data["last"] == 403.0
    assert status["status"] == "refreshed"
    assert data["quote_cache_status"]["status"] == "refreshed"
    assert not any("stale" in str(reason).lower() for reason in data["metric_missing_reasons"])


def test_screener_has_single_primary_run_button_and_no_english_fallback_label():
    html = TestClient(api.app).get("/screener").text
    assert html.count('id="runBtn"') == 1
    assert "Start Screener" not in html
    assert "筛选中" in html or "绛涢€変腑" in html


def test_eastmoney_stock_get_supplements_real_valuation_metrics(monkeypatch):
    provider = EastmoneyProvider()
    q = Quote(
        symbol="300274",
        name="阳光电源",
        ts=datetime(2026, 5, 26, 15, 0),
        last=178.99,
        pre_close=167.24,
        open=166.8,
        high=181.77,
        low=163.7,
        volume=1,
        amount=1,
        change=0,
        change_pct=0,
        source="sina",
    )
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda *a, **k: {
            "data": {
                "f116": 371_084_112_781.76,
                "f117": 284_596_737_775.63,
                "f162": 4049,
                "f167": 786,
                "f168": 713,
                "f84": 2_073_211_424,
                "f85": 1_590_014_737,
            }
        },
    )

    enriched = provider._supplement_quote_metrics(q)

    assert enriched.pe_dynamic == 40.49
    assert enriched.pb == 7.86
    assert enriched.turnover == 7.13
    assert enriched.total_market_cap == 371_084_112_781.76
    assert enriched.float_market_cap == 284_596_737_775.63


def test_sina_order_book_parses_five_levels(monkeypatch):
    provider = SinaProvider()

    class Resp:
        content = (
            'var hq_str_sz300750="宁德时代,432.100,424.000,419.950,438.240,418.180,'
            '419.950,419.990,38077136,16334676180.850,12790,419.950,100,419.940,'
            '100,419.920,1500,419.900,1800,419.890,100,419.990,800,420.100,'
            '1100,420.120,200,420.130,200,420.140,2026-06-01,14:55:54,00";'
        ).encode("gbk")
        text = content.decode("gbk")

    monkeypatch.setattr(provider.http, "get", lambda *args, **kwargs: Resp())

    book = provider.get_order_book("300750")

    assert book.source == "sina"
    assert book.bids[0].price == 419.95
    assert book.bids[0].volume == 127.9
    assert book.asks[0].price == 419.99
    assert book.asks[4].price == 420.14
    assert book.order_diff is not None


def test_provider_manager_falls_back_when_eastmoney_depth_is_empty():
    class EmptyEastmoney:
        name = "eastmoney"

        def get_order_book(self, symbol):
            levels = [OrderBookLevel(None, None) for _ in range(5)]
            return OrderBook(symbol, datetime(2026, 6, 1, 10), levels, levels, source="eastmoney")

    class FullSina:
        name = "sina"

        def get_order_book(self, symbol):
            return OrderBook(
                symbol,
                datetime(2026, 6, 1, 10),
                [OrderBookLevel(10.02, 30)],
                [OrderBookLevel(10.01, 20)],
                source="sina",
            )

    manager = ProviderManager(enable_akshare=False)
    manager.providers = [EmptyEastmoney(), FullSina()]

    book = manager.get_order_book("300750")

    assert book is not None
    assert book.source == "sina"
    assert book.bids[0].price == 10.01
