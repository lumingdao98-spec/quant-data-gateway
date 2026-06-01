from pathlib import Path


def test_backtest_wordsource_trace_is_grounded_in_real_docx():
    trace = Path("docs/BACKTEST_WORDSOURCE_TRACE.md").read_text(encoding="utf-8")

    assert "docs/word_sources/炒股-量化相关.docx" in trace
    assert "188-195" in trace
    assert "手续费" in trace
    assert "滑点" in trace
    assert "最大回撤" in trace
    assert "夏普" in trace
    assert "研究辅助，不构成投资建议" in trace
