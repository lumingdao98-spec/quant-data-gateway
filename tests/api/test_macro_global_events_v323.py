from fastapi.testclient import TestClient

import quant_data.api as api


def test_macro_global_events_api_is_truthful_and_cached():
    data = TestClient(api.app).get("/api/macro/global-events?limit=20").json()

    assert data["ok"] is True
    assert "watchlist" in data
    assert any(item["key"] == "nonfarm_payrolls" for item in data["watchlist"])
    assert any(item["key"] == "fomc_rate" for item in data["watchlist"])
    assert "不单独构成买卖建议" in data["disclaimer"]
    assert "cache_status" in data
