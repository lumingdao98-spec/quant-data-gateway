from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_wordsource_trace_api_and_page_visible():
    client = TestClient(api.app)
    data = client.get("/api/wordsource/trace").json()
    assert data["ok"] is True
    assert data["count"] > 0
    assert any(row.get("api") for row in data["items"])
    assert any(row.get("frontend") for row in data["items"])
    assert any(row.get("test") for row in data["items"])
    statuses = {row.get("status") for row in data["items"]}
    assert statuses - {"已落地"}  # not everything may be marked completed

    html = client.get("/wordsource").text
    assert "WordSource ClosedLoop" in html or "WordSource" in html
    assert "traceRows" in html
    assert "/api/wordsource/trace" in html
