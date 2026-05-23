from pathlib import Path


TRACE = Path("docs/WORD_SOURCE_TRACE.md")


def test_wordsource_trace_exists_and_mentions_all_source_docs():
    text = TRACE.read_text(encoding="utf-8")
    for name in [
        "炒股-消息面分析.docx",
        "炒股-技术面分析.docx",
        "炒股-风格与分析.docx",
        "炒股-量化相关.docx",
    ]:
        assert name in text
    for source in [
        "quant_data/data/source_docs/message.txt",
        "quant_data/data/source_docs/technical.txt",
        "quant_data/data/source_docs/style.txt",
        "quant_data/data/source_docs/quant.txt",
    ]:
        assert source in text


def test_wordsource_trace_maps_each_required_dimension_to_code_api_frontend_tests():
    text = TRACE.read_text(encoding="utf-8")
    required_terms = [
        "系统功能", "代码文件", "函数/类", "API", "前端展示位置", "测试文件",
        "三通道候选池", "技术面公式计算和解释", "信息面事件评分", "风格/板块/大盘分析",
        "综合评分与诊断解释", "模拟交易接口预留",
    ]
    for term in required_terms:
        assert term in text
    for test_file in [
        "tests/test_wordsource_mapping.py",
        "tests/test_candidate_pool.py",
        "tests/test_technical_factor_engine.py",
        "tests/test_diagnosis_engine.py",
        "tests/test_news_fetch_performance.py",
        "tests/test_screener_fields.py",
    ]:
        assert test_file in text


def test_wordsource_trace_covers_required_technical_indicators():
    text = TRACE.read_text(encoding="utf-8")
    for indicator in [
        "MA", "EMA", "MACD", "RSI", "KDJ", "BOLL", "ATR", "VWAP", "WR", "CCI",
        "ROC", "MOM", "OBV", "MFI", "ADX", "DMI", "BIAS", "SAR", "VR", "PSY",
        "BRAR", "CYR", "Ichimoku", "一目均衡表", "Fibonacci 回调", "Fibonacci 时间窗口",
        "TD序列", "Pivot Points", "ZigZag", "支撑压力", "价格通道", "区间位置",
        "量价状态", "波动率", "均量", "VWAP 强弱", "成交量背离", "价格形态",
    ]:
        assert indicator in text
