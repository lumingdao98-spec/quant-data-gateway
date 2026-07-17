from __future__ import annotations

from typing import Any

from quant_data.models import Quote


def _n(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


class ThemeLifecycleService:
    """Evidence-first theme classifier used by the screener.

    This is a taxonomy matcher, not a source of company facts. The API layer
    later merges persisted company profiles and sector-flow snapshots.
    """

    THEME_KEYWORDS = {
        "AI/算力": ["AI", "人工智能", "算力", "服务器", "数据中心", "光模块", "CPO", "大模型", "信创"],
        "半导体/国产替代": ["半导体", "芯片", "晶圆", "EDA", "光刻", "集成电路", "封测", "国产替代"],
        "机器人/智能制造": ["机器人", "减速器", "伺服", "工业母机", "自动化", "智能制造"],
        "低空经济/军工": ["无人机", "航空", "航天", "军工", "低空", "卫星", "雷达"],
        "光伏": ["光伏", "硅料", "硅片", "组件", "太阳能", "逆变器", "BC电池", "钙钛矿"],
        "风电/电网": ["风电", "海风", "电网", "特高压", "变压器", "电力设备", "绿电"],
        "锂电/新能源车": ["锂", "电池", "新能源车", "动力电池", "固态电池", "电解液", "正负极"],
        "储能": ["储能", "储能系统", "储能电池", "抽水蓄能", "虚拟电厂"],
        "汽车/智能驾驶": ["汽车", "整车", "汽车零部件", "智能驾驶", "车联网", "座舱"],
        "医药/医疗": ["医药", "创新药", "中药", "医疗", "生物", "CXO", "器械"],
        "大消费": ["白酒", "食品饮料", "消费", "零售", "家电", "旅游", "免税"],
        "金融": ["银行", "证券", "券商", "保险", "金融", "财富管理"],
        "资源周期": ["煤", "钢", "有色", "黄金", "石油", "化工", "稀土", "铜", "铝"],
        "农业/养殖": ["农业", "种业", "养殖", "饲料", "猪", "水产"],
        "航运/物流": ["航运", "港口", "物流", "集运", "油运", "快递"],
        "红利/公用事业": ["红利", "电力", "水务", "燃气", "高速", "运营商"],
    }

    def infer_theme_matches(self, text: str) -> list[dict[str, Any]]:
        haystack = str(text or "").lower()
        matches = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            hits = list(dict.fromkeys(keyword for keyword in keywords if keyword.lower() in haystack))
            if hits:
                matches.append(
                    {
                        "theme": theme,
                        "matched_keywords": hits[:8],
                        "match_count": len(hits),
                        "confidence": "较高" if len(hits) >= 3 else ("中" if len(hits) == 2 else "低"),
                    }
                )
        return sorted(matches, key=lambda item: item["match_count"], reverse=True)

    def infer_themes(self, text: str) -> list[str]:
        matches = self.infer_theme_matches(text)
        return [item["theme"] for item in matches] or ["未识别题材"]

    def analyze(self, q: Quote, evidence_text: str = "") -> dict[str, Any]:
        matches = self.infer_theme_matches(f"{q.name or ''} {evidence_text}")
        themes = [item["theme"] for item in matches] or ["未识别题材"]
        change = _n(q.change_pct)
        volume_ratio = _n(q.volume_ratio)
        turnover = _n(q.turnover)
        if change >= 7 and volume_ratio >= 2:
            stage = "个股加速，题材阶段待板块确认"
        elif change >= 3 and volume_ratio >= 1.3:
            stage = "个股活跃，题材发酵待确认"
        elif -2 <= change <= 3 and volume_ratio >= 1.1:
            stage = "启动观察"
        elif change < -3 and volume_ratio >= 1.5:
            stage = "个股分歧，题材退潮待确认"
        else:
            stage = "低热度/待确认"
        score = 50 + min(max(change, -10), 10) * 2 + min(volume_ratio, 5) * 5 + min(turnover, 20) * 0.8
        return {
            "themes": themes,
            "theme_stage": stage,
            "theme_score": round(max(0, min(100, score)), 2),
            "theme_matches": matches[:8],
            "classification_source": "名称与已提供证据文本的规则映射",
            "basis": "这里只识别题材候选；公司画像/主营和板块资金由API层补充，题材阶段必须结合板块成分股与真实资金快照确认。",
        }
