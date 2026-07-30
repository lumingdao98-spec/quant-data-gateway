from quant_data.auto_trading_workbench_ui import build_auto_trading_workbench_ui
from quant_data.realtime_paper_ui import build_realtime_paper_ui
from quant_data.screener_ui import build_screener_ui


def test_workbench_pauses_global_stream_when_hidden_and_deduplicates_requests():
    html = build_auto_trading_workbench_ui()
    assert "document.hidden||globalTickerPaused" in html
    assert "globalStreamPromise" in html
    assert "workbenchRefreshPromise" in html
    assert "visibilitychange" in html


def test_realtime_paper_polling_is_visibility_aware_and_deduplicated():
    html = build_realtime_paper_ui()
    assert "function installVisiblePoll" in html
    assert "if(document.hidden||busy)return" in html
    assert "pageRefreshPromise" in html
    assert "installVisiblePoll(refresh,15000)" in html
    assert "installVisiblePoll(window.loadPaperConfirmations,15000)" in html


def test_screener_runtime_feedback_is_chinese():
    html = build_screener_ui()
    assert "Start screener" not in html
    assert "Screener done" not in html
    assert "Restored local screener rows" not in html
    assert "Backend restore failed" not in html
    assert "Snapshot has no rows" not in html
    assert "开始筛选；耗时取决于公开数据源响应和本地 K 线缓存。" in html
