from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from lxml import etree


REPO_ROOT = Path(__file__).resolve().parents[2]
WORD_SOURCE_DIR = REPO_ROOT / "docs" / "word_sources"

WORD_SOURCE_FILES = {
    "message": "炒股-消息面分析.docx",
    "technical": "炒股-技术面分析.docx",
    "style": "炒股-风格与分析.docx",
    "quant": "炒股-量化相关.docx",
}

_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class WordSourceItem:
    doc_key: str
    doc_name: str
    index: int
    text: str
    kind: str = "paragraph"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ").replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _node_text(node: etree._Element) -> str:
    pieces = node.xpath(".//w:t/text()", namespaces=_NS)
    return _clean_text("".join(str(x) for x in pieces))


def _split_points(text: str) -> list[str]:
    text = _clean_text(text)
    if not text:
        return []
    # Word 中很多“句子”本质是编号条目；先按换行/分号/句号拆，过短碎片再合并。
    chunks = re.split(r"(?<=[。；;])\s+|[\r\n]+", text)
    out: list[str] = []
    for chunk in chunks:
        chunk = _clean_text(chunk)
        if not chunk:
            continue
        if len(chunk) <= 8 and out:
            out[-1] = _clean_text(out[-1] + " " + chunk)
        else:
            out.append(chunk)
    return out or [text]


class WordSourceLoader:
    """Read the real DOCX files under docs/word_sources.

    The loader extracts body paragraphs and table rows directly from OOXML. It
    does not rely on file names, old text exports, or hard-coded chapter titles.
    """

    def __init__(self, source_dir: str | Path | None = None) -> None:
        self.source_dir = Path(source_dir) if source_dir else WORD_SOURCE_DIR

    def expected_files(self) -> dict[str, Path]:
        return {key: self.source_dir / name for key, name in WORD_SOURCE_FILES.items()}

    def read_docx(self, key: str) -> dict[str, Any]:
        key = str(key or "").strip().lower()
        files = self.expected_files()
        if key not in files:
            return {"ok": False, "error": "unknown_doc_key", "available": list(files)}
        path = files[key]
        if not path.exists():
            return {"ok": False, "error": "missing_docx", "path": str(path)}
        try:
            with zipfile.ZipFile(path) as zf:
                xml = zf.read("word/document.xml")
                image_count = sum(1 for n in zf.namelist() if n.startswith("word/media/"))
        except Exception as exc:
            return {"ok": False, "error": f"docx_open_failed:{exc}", "path": str(path)}

        root = etree.fromstring(xml)
        body = root.find("w:body", namespaces=_NS)
        if body is None:
            return {"ok": False, "error": "missing_body", "path": str(path)}

        raw_items: list[tuple[str, str]] = []
        table_count = 0
        for child in body:
            tag = etree.QName(child).localname
            if tag == "p":
                text = _node_text(child)
                for point in _split_points(text):
                    raw_items.append(("paragraph", point))
            elif tag == "tbl":
                table_count += 1
                for row in child.xpath(".//w:tr", namespaces=_NS):
                    cells = [_node_text(tc) for tc in row.xpath("./w:tc", namespaces=_NS)]
                    cells = [c for c in cells if c]
                    if cells:
                        raw_items.append(("table_row", " | ".join(cells)))

        items = [
            WordSourceItem(key, path.name, idx + 1, text, kind).to_dict()
            for idx, (kind, text) in enumerate(raw_items)
            if text
        ]
        full_text = "\n".join(x["text"] for x in items)
        return {
            "ok": True,
            "doc_key": key,
            "doc_name": path.name,
            "path": str(path),
            "char_count": len(full_text),
            "item_count": len(items),
            "table_count": table_count,
            "image_count": image_count,
            "text": full_text,
            "items": items,
        }

    def load_all(self) -> dict[str, Any]:
        docs = {key: self.read_docx(key) for key in self.expected_files()}
        ok = all(d.get("ok") and d.get("char_count", 0) > 0 for d in docs.values())
        return {
            "ok": ok,
            "source_dir": str(self.source_dir),
            "docs": docs,
            "doc_count": len(docs),
            "doc_char_count": sum(int(d.get("char_count") or 0) for d in docs.values()),
            "doc_item_count": sum(int(d.get("item_count") or 0) for d in docs.values()),
            "doc_table_count": sum(int(d.get("table_count") or 0) for d in docs.values()),
            "image_count": sum(int(d.get("image_count") or 0) for d in docs.values()),
        }

    def mapping_for_item(self, doc_key: str, text: str) -> dict[str, str]:
        lower = text.lower()
        if doc_key == "technical":
            return {
                "system": "WordSource V2.1 技术因子逐指标计算、信号解释、风险扣分",
                "code": "quant_data/services/technical_factor_engine.py; quant_data/services/screener_service.py",
                "symbol": "TechnicalFactorEngine.analyze; ScreenerService.analyze",
                "api": "/api/screener/run; /api/technical/indicators",
                "frontend": "/screener 技术摘要、右侧 WordSource V2 技术因子、K线详情标注",
                "tests": "tests/test_technical_factor_engine.py; tests/test_technical_summary_consistency.py",
            }
        if doc_key == "message":
            return {
                "system": "信息面 light/deep 分层抓取、公告优先、事件评分、快照复用",
                "code": "quant_data/services/news_service.py; quant_data/services/info_analysis_service.py; quant_data/api.py",
                "symbol": "NewsAnalysisService.analyze; InfoAnalysisService.analyze; info_analyze",
                "api": "/api/info/analyze/{symbol}; /api/news/analyze/{symbol}; /api/screener/run",
                "frontend": "/info 快照提示/深度刷新; /screener 信息面入口",
                "tests": "tests/test_news_light_mode.py; tests/test_info_snapshot_reuse.py",
            }
        if doc_key == "style":
            if any(k in text for k in ["支撑", "压力", "趋势", "高位", "回踩"]):
                system = "风格/趋势/支撑压力/追高风险/回踩观察"
            else:
                system = "市值风格、题材生命周期、仓位止损建议"
            return {
                "system": system,
                "code": "quant_data/services/style_classifier.py; quant_data/services/theme_lifecycle_service.py; quant_data/services/screener_service.py",
                "symbol": "StyleClassifierService.classify; ThemeLifecycleService.analyze; ScreenerService.analyze",
                "api": "/api/screener/run; /api/wordsource/report/{symbol}",
                "frontend": "/screener 市值风格、题材阶段、支撑/压力距离、追高风险",
                "tests": "tests/test_custom_input_enrichment.py; tests/test_support_resistance_distance.py",
            }
        if doc_key == "quant":
            if any(k in lower for k in ["var", "cvar", "sharpe", "夏普", "回撤"]):
                system = "量化风险指标、仓位管理、V4+ 模拟交易结构预留"
            else:
                system = "数据获取、清洗、特征工程、策略信号、多因子筛选"
            return {
                "system": system,
                "code": "quant_data/services/screener_service.py; quant_data/services/market_behavior_engine.py; quant_data/services/strategy_signal_service.py",
                "symbol": "ScreenerService.run; MarketBehaviorEngine.analyze; StrategySignalService.generate",
                "api": "/api/screener/run; /api/detail/{symbol}; /api/wordsource/report/{symbol}",
                "frontend": "/screener 行为风险/综合诊断; /ui K线标注列表",
                "tests": "tests/test_market_behavior_engine.py; tests/test_screener_fields.py",
            }
        return {
            "system": "WordSource V2.1 综合主流程",
            "code": "quant_data/services/wordsource_loader.py",
            "symbol": "WordSourceLoader",
            "api": "/api/wordsource/coverage",
            "frontend": "/screener",
            "tests": "tests/test_wordsource_docs_exist.py",
        }

    def build_trace_markdown(self, max_items_per_doc: int | None = None) -> str:
        data = self.load_all()
        lines = [
            "# WordSource V2.1 主流程逐句映射",
            "",
            "本文件由 `WordSourceLoader` 直接读取 `docs/word_sources/*.docx` 正文生成；映射行来自 DOCX 正文段落或表格行，不来自文件名或记忆内容。",
            "",
            f"- DOCX 数量：{data['doc_count']}",
            f"- 正文要点数量：{data['doc_item_count']}",
            f"- 正文字数：{data['doc_char_count']}",
            f"- 表格数量：{data['doc_table_count']}",
            "- 旧版文本导出留痕：`quant_data/data/source_docs/message.txt`、`quant_data/data/source_docs/technical.txt`、`quant_data/data/source_docs/style.txt`、`quant_data/data/source_docs/quant.txt`",
            "",
            "## 主流程落地总览",
            "",
            "| 系统功能 | 代码文件 | 函数/类 | API | 前端展示位置 | 测试文件 |",
            "|---|---|---|---|---|---|",
            "| 三通道候选池 | `quant_data/services/candidate_pool_service.py; quant_data/services/screener_service.py` | `CandidatePoolService.build; ScreenerService._load_universe` | `/api/screener/run` | `/screener 候选来源通道` | `tests/test_candidate_pool.py; tests/test_custom_input_enrichment.py` |",
            "| 技术面公式计算和解释 | `quant_data/services/technical_factor_engine.py; quant_data/indicators.py` | `TechnicalFactorEngine.analyze; support_resistance` | `/api/screener/run; /api/technical/indicators` | `/screener 技术摘要/右侧技术因子矩阵` | `tests/test_technical_factor_engine.py; tests/test_support_resistance_distance.py; tests/test_technical_summary_consistency.py` |",
            "| 信息面事件评分 | `quant_data/services/news_service.py; quant_data/services/info_analysis_service.py; quant_data/api.py` | `NewsAnalysisService.analyze; InfoAnalysisService.analyze; info_analyze` | `/api/info/analyze/{symbol}; /api/news/analyze/{symbol}` | `/info light/deep/snapshot 提示` | `tests/test_news_fetch_performance.py; tests/test_news_light_mode.py; tests/test_info_snapshot_reuse.py` |",
            "| 风格/板块/大盘分析 | `quant_data/services/style_classifier.py; quant_data/services/theme_lifecycle_service.py; quant_data/services/market_regime_service.py` | `StyleClassifierService.classify; ThemeLifecycleService.analyze` | `/api/screener/run; /api/wordsource/report/{symbol}` | `/screener 市值风格/题材阶段/追高风险` | `tests/test_diagnosis_engine.py; tests/test_screener_fields.py` |",
            "| 综合评分与诊断解释 | `quant_data/services/screener_service.py; quant_data/services/market_behavior_engine.py` | `ScreenerService.analyze; MarketBehaviorEngine.analyze` | `/api/screener/run; /api/detail/{symbol}; /api/kline/{symbol}` | `/screener 综合诊断/行为风险; /ui K线标注` | `tests/test_market_behavior_engine.py; tests/test_screener_compact_fields.py` |",
            "| 模拟交易接口预留 | `quant_data/services/strategy_signal_service.py; quant_data/services/trading_framework_service.py` | `StrategySignalService.generate; build_tradercore_diagnosis` | `/api/strategy/*; /api/wordsource/report/{symbol}` | `/screener 脚本分/人工复核建议分` | `tests/test_wordsource_mapping.py` |",
            "",
            "## 技术指标覆盖",
            "",
            "MA、EMA、MACD、RSI、KDJ、BOLL、ATR、VWAP、WR、CCI、ROC、MOM、OBV、MFI、ADX、DMI、BIAS、SAR、VR、PSY、BRAR、CYR、Ichimoku、一目均衡表、Fibonacci 回调、Fibonacci 时间窗口、TD序列、Pivot Points、ZigZag、支撑压力、价格通道、区间位置、量价状态、波动率、均量、VWAP 强弱、成交量背离、价格形态。",
            "",
        ]
        for key, doc in data["docs"].items():
            lines.extend([
                f"## {doc.get('doc_name', key)}",
                "",
                "| # | Word 原文要点 | 系统功能 | 代码文件 | 函数/类 | API | 前端展示位置 | 测试文件 |",
                "|---:|---|---|---|---|---|---|---|",
            ])
            items = doc.get("items") or []
            if max_items_per_doc:
                items = items[:max_items_per_doc]
            for item in items:
                mapping = self.mapping_for_item(key, item.get("text", ""))
                text = str(item.get("text", "")).replace("|", "\\|")
                lines.append(
                    f"| {item.get('index')} | {text} | {mapping['system']} | `{mapping['code']}` | `{mapping['symbol']}` | `{mapping['api']}` | {mapping['frontend']} | `{mapping['tests']}` |"
                )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
