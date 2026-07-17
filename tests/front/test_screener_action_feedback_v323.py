from fastapi.testclient import TestClient

import quant_data.api as api


def test_screener_page_has_submission_and_completion_feedback():
    html = TestClient(api.app).get("/screener").text

    assert 'id="actionToast"' in html
    assert "筛选任务已提交" in html
    assert "筛选完成" in html
    assert "筛选中..." in html
    assert "btn.disabled=true" in html
    assert "showActionToast" in html
