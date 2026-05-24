from fastapi.testclient import TestClient

from quant_data import api


def test_ui_state_restore_keys_and_functions_are_visible():
    html = TestClient(api.app).get("/ui").text
    for key in [
        "quant_watchlist_symbols",
        "quant_watchlist_quotes",
        "quant_selected_symbol",
        "quant_selected_frame",
        "quant_chart_zoom",
        "quant_chart_scroll",
        "quant_last_intraday_data",
        "quant_last_kline_data",
        "quant_last_quote_snapshot",
        "quant_ui_last_update_time",
    ]:
        assert key in html
    assert "restoreWatchlistState" in html
    assert "persistWatchlistState" in html
    assert "restoreWatchlistState();renderModeButtons" in html
    assert "loadQuotes(false)" in html


def test_screener_and_info_state_restore_functions_are_visible():
    client = TestClient(api.app)
    screener = client.get("/screener").text
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
        assert key in screener
    assert "restoreScreenerState" in screener
    assert "restoreScreenerState();setTableMode" in screener

    info = client.get("/info?symbol=300274&name=Sungrow").text
    for key in ["quant_info_last_symbol", "quant_info_snapshot_id_", "quant_info_tab", "quant_info_filters", "quant_info_last_items_"]:
        assert key in info
    assert "restoreInfoState" in info
