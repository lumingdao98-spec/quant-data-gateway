from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_ui_contains_watchlist_chart_state_restore_keys():
    html = TestClient(api.app).get("/ui").text
    for key in [
        "quant_watchlist_symbols",
        "quant_selected_symbol",
        "quant_selected_frame",
        "quant_selected_adjust",
        "quant_chart_zoom",
        "quant_chart_scroll",
        "quant_last_intraday_data",
        "quant_last_kline_data",
        "quant_last_quote_snapshot",
        "quant_ui_last_update_time",
    ]:
        assert key in html
    assert "restoreWatchlistState" in html
    assert "saveUiState" in html
    assert "renderQuoteRows" in html
    assert "restoreWatchlistState();renderModeButtons" in html
    assert "quoteBody').innerHTML=''" not in html


def test_screener_contains_closed_loop_local_restore_keys():
    html = TestClient(api.app).get("/screener").text
    for key in [
        "quant_screener_snapshot_id",
        "quant_screener_rows",
        "quant_screener_params",
        "quant_screener_selected_symbol",
        "quant_screener_view_mode",
        "quant_screener_scroll_position",
        "quant_screener_strategy_keys",
        "quant_screener_custom_symbols",
    ]:
        assert key in html
    assert "restoreScreenerState" in html
    assert "persistScreenerState" in html
