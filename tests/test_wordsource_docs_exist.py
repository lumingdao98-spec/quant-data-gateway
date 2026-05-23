from pathlib import Path

from quant_data.services.wordsource_loader import WORD_SOURCE_FILES, WordSourceLoader


def test_required_word_docx_exist_and_have_body_text():
    loader = WordSourceLoader()
    for key, path in loader.expected_files().items():
        assert path.exists(), f"missing docx: {WORD_SOURCE_FILES[key]}"
        doc = loader.read_docx(key)
        assert doc["ok"] is True
        assert doc["char_count"] > 0
        assert doc["item_count"] > 0
        assert doc["text"].strip()


def test_word_source_trace_exists_and_has_mapping_table():
    trace = Path("docs/WORD_SOURCE_TRACE.md")
    assert trace.exists()
    text = trace.read_text(encoding="utf-8")
    for name in WORD_SOURCE_FILES.values():
        assert name in text
    for term in ["系统功能", "代码文件", "函数/类", "API", "前端展示位置", "测试文件"]:
        assert term in text
    assert "WordSourceLoader" in text
