from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_html_contains_local_state_restore_keys():
    html = TestClient(api.app).get("/screener").text
    for key in [
        "quant_custom_symbols",
        "quant_selected_strategies",
        "quant_screener_mode",
        "quant_enable_news",
        "quant_view_mode",
        "quant_show_excluded",
        "quant_min_score",
        "quant_max_items",
        "last_screener_snapshot_id",
    ]:
        assert key in html
    assert "restoreLocalInputs()" in html
    assert "/api/screener/snapshot/" in html
    assert "/api/cache/screener/latest" in html
    assert "watchlist/set" in html
