from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "word_source_knowledge.json"


@lru_cache(maxsize=1)
def _load_knowledge() -> dict[str, Any]:
    if not _DATA_FILE.exists():
        return {
            "version": "missing",
            "doc_sources": {},
            "message_framework": {},
            "technical_framework": {},
            "style_framework": {},
            "quant_framework": {},
        }
    return json.loads(_DATA_FILE.read_text(encoding="utf-8"))


class SourceKnowledgeService:
    """Word来源知识服务。

    V16.4 开始，系统不再只靠人工硬编码指标名，而是把用户上传的四份 Word 文档全文抽取为
    source_docs/*.txt，并把结构化框架沉淀到 word_source_knowledge.json，供前端、筛选器、
    技术指标库、消息面和量化路线共同引用。
    """

    def get_all(self) -> dict[str, Any]:
        return _load_knowledge()

    def doc_sources(self) -> dict[str, Any]:
        return self.get_all().get("doc_sources", {})

    def technical_framework(self) -> dict[str, Any]:
        return self.get_all().get("technical_framework", {})

    def message_framework(self) -> dict[str, Any]:
        return self.get_all().get("message_framework", {})

    def style_framework(self) -> dict[str, Any]:
        return self.get_all().get("style_framework", {})

    def quant_framework(self) -> dict[str, Any]:
        return self.get_all().get("quant_framework", {})

    def image_sources(self) -> dict[str, Any]:
        return self.get_all().get("image_sources", {})

    def source_doc_text(self, key: str, max_chars: int = 12000) -> dict[str, Any]:
        key = str(key or "").strip().lower()
        meta = self.doc_sources().get(key)
        if not meta:
            return {"ok": False, "error": "unknown_source_key", "available": list(self.doc_sources().keys())}
        path = Path(meta.get("txt_path") or "")
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        max_chars = max(500, min(int(max_chars or 12000), 200000))
        return {"ok": True, "meta": meta, "text": text[:max_chars], "truncated": len(text) > max_chars, "char_count": len(text)}

    def coverage(self) -> dict[str, Any]:
        docs = self.doc_sources()
        tech = self.technical_framework()
        return {
            "version": self.get_all().get("version"),
            "doc_count": len(docs),
            "doc_char_count": sum(int(v.get("char_count") or 0) for v in docs.values()),
            "doc_table_count": sum(int(v.get("table_count") or 0) for v in docs.values()),
            "technical_indicator_count_from_word": int(tech.get("normalized_indicator_count") or 0),
            "word_table_rows_extracted": len(tech.get("word_table_rows_extracted") or []),
            "message_source_channels": len(self.message_framework().get("source_channels") or []),
            "quant_pipeline_steps": len(self.quant_framework().get("pipeline") or []),
            "style_blocks": len(self.style_framework().get("analysis_blocks") or []),
            "image_count": len(self.image_sources()),
        }


def source_knowledge() -> dict[str, Any]:
    return SourceKnowledgeService().get_all()
