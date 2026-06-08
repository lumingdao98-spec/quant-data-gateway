from fastapi.testclient import TestClient

import quant_data.api as api


def test_detail_page_and_chart_marker_api_visible():
    client = TestClient(api.app)

    assert client.get("/detail/300750").status_code == 200
    assert client.get("/api/chart/300750/markers").json()["ok"] is True
