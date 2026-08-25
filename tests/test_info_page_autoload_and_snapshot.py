from __future__ import annotations

from fastapi.testclient import TestClient

import quant_data.api as api


def test_info_page_autoloads_snapshot_and_has_empty_states():
    html = TestClient(api.app).get("/info?symbol=300274&name=阳光电源").text
    assert "refreshAll" in html
    assert "读取最近快照" in html or "最近快照" in html
    assert "source_logs" in html or "sources" in html
    assert "全球/行业映射" in html
    assert "global-columns" in html
    assert "信息映射" in html
    assert "全球信息" in html
    assert "深度刷新" in html
    assert "refreshSnapshot=force||deep" in html
    assert "incompleteSnapshot" in html


def test_info_analyze_empty_snapshot_id_returns_200():
    res = TestClient(api.app).get("/api/info/analyze/300274?snapshot_id=&force=false&deep_refresh=false")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "cache_status" in data


def test_info_page_uses_single_parallel_localized_render_pipeline():
    html = TestClient(api.app).get("/info?symbol=300274&name=阳光电源").text

    assert html.count("function renderSummary(") == 1
    assert html.count("function renderItems(") == 1
    assert html.count("function renderGlobal(") == 1
    assert "renderSummary=function" not in html
    assert "renderItems=function" not in html
    assert "renderGlobal=function" not in html

    assert "Promise.allSettled([loadPage(1),loadGlobal(" in html
    assert "new AbortController()" in html
    assert "处理中…" in html
    assert "document.hidden&&state.tab==='global'" in html
    assert "Array.isArray(state.analysis?.items)" in html
    assert "本地信息库暂无条目" in html
    assert "!(state.analysis?.items||[]).length" not in html

    assert "当前信息分" in html
    assert "快照编号" in html
    assert "缓存年龄" in html
    assert "未提供原文链接" in html
    assert "核对原始信息" in html
    assert "传导路径" in html
    assert "不提供可追溯原始链接" not in html
    assert "function renderLongText(" in html
    assert "展开完整摘要" in html
    assert "board_meeting:'董事会会议'" in html
    assert "global_news_cache:'全球要闻缓存'" in html
    assert "Info score" not in html
    assert "No stock-specific items yet" not in html
