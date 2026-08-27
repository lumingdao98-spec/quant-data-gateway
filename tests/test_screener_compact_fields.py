from __future__ import annotations

from quant_data.screener_ui import build_screener_ui


def test_screener_defaults_to_compact_view_columns():
    html = build_screener_ui()

    assert "tableMode='compact'" in html
    assert "精简视图" in html
    assert "完整视图" in html
    for col in ["代码", "名称", "等级", "综合分", "复核分", "现价", "涨跌幅", "候选通道", "成交额", "换手率", "量比", "PE/PB", "市值风格", "技术摘要", "行为风险", "风险", "操作"]:
        assert col in html


def test_full_fields_remain_in_right_detail_card():
    html = build_screener_ui()

    for text in ["总/流通市值", "MA20偏离", "近5日振幅", "20/250日位置", "大盘情绪", "高位回撤", "技术摘要", "资金面信号", "题材阶段", "支撑/压力距离", "缺失提示", "综合判断"]:
        assert text in html
    assert "0%表示贴近该周期低点" in html
    assert "不等于整行无数据" in html
    assert "资金行为识别" in html
    assert "behavior_tags" in html
    assert "behavior_score" in html


def test_long_text_uses_clipping_classes():
    html = build_screener_ui()

    assert "cell-clip" in html
    assert "cell-wrap-2" in html
    assert "technical_signal_summary||'--'" in html
    assert "r.comprehensive_diagnosis||r.reason||'--'" in html
    assert "更多字段在右侧详情卡展示" in html


def test_label_explain_uses_selected_row_snapshot_context():
    html = build_screener_ui()

    assert "/api/screener/explain-row" in html
    assert "JSON.stringify({tag,item:selected})" in html
    assert "本地恢复" in html
    assert "typeof elapsed==='number'?elapsed+'s'" in html
