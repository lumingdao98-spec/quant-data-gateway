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
from quant_data.models import Quote
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
    assert "quant_postclose_refresh_" in html
    assert "currentQuoteExtra=js.quote_extra" in html
    assert "limitUp=extra.limit_up" in html
    assert "grid-template-rows:52px 1fr 82px" in html
    assert "max-height:52px" in html
    assert "MACD指标" in html
    assert "均线5/10/20" in html


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
