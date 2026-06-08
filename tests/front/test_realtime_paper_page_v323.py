from fastapi.testclient import TestClient

import quant_data.api as api


def test_realtime_paper_session_api_visible():
    data = TestClient(api.app).get("/api/backtest/v323/readiness").json()

    assert data["modules"]["realtime_paper"] is True
