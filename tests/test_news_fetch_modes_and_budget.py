from __future__ import annotations

import time

from quant_data.services.news_service import NewsAnalysisService, NewsItem


def _news(i: int = 1) -> NewsItem:
    return NewsItem(
        title=f"company official update {i}",
        url=f"https://example.com/{i}",
        source="official",
        source_type="announcement",
        summary="contract and earnings update",
        relevance_score=90,
        credibility_score=90,
        event_key=f"evt-{i}",
    )


class ModeProbeService(NewsAnalysisService):
    def __init__(self):
        super().__init__()
        self.calls: list[str] = []

    def _valid_count_estimate(self, items, symbol="", name=""):
        return len(items)

    def _search_eastmoney_ann(self, *args):
        self.calls.append("official_ann")
        return []

    def _search_cninfo_fulltext(self, *args):
        self.calls.append("cninfo")
        return []

    def _search_eastmoney_hsf10(self, *args):
        self.calls.append("f10")
        return []

    def _search_sina_stock_news(self, *args):
        self.calls.append("sina_stock_page")
        return []

    def _search_10jqka_stock_news(self, *args):
        self.calls.append("ths_stock_page")
        return []

    def _search_eastmoney_page(self, *args):
        self.calls.append("eastmoney_matrix")
        return []

    def _search_sina_page(self, *args):
        self.calls.append("sina_matrix")
        return []

    def _search_10jqka_page(self, *args):
        self.calls.append("ths_matrix")
        return []

    def _search_professional_portals(self, *args):
        self.calls.append("professional_matrix")
        return [_news(99)]

    def _search_eastmoney_guba(self, *args):
        self.calls.append("guba")
        return []

    def _search_xueqiu_page(self, *args):
        self.calls.append("xueqiu")
        return []


def test_light_and_normal_do_not_generate_keyword_matrix():
    light = ModeProbeService()
    light._search_all("q", "300274", "Sungrow", 60, mode="light")
    assert not {"eastmoney_matrix", "sina_matrix", "ths_matrix", "professional_matrix"} & set(light.calls)

    normal = ModeProbeService()
    normal._search_all("q", "300274", "Sungrow", 60, mode="normal")
    assert "sina_stock_page" in normal.calls
    assert "ths_stock_page" in normal.calls
    assert not {"eastmoney_matrix", "sina_matrix", "ths_matrix", "professional_matrix"} & set(normal.calls)


def test_deep_mode_budget_exhaustion_breaks_queue_and_logs_once():
    svc = ModeProbeService()
    svc._round_started_at = time.monotonic() - 10
    svc._round_budget_seconds = 0.001
    svc._budget_exhausted_recorded = False
    out = svc._search_all("q", "300274", "Sungrow", 60, mode="deep")

    assert out == []
    assert svc.calls == []
    budget_logs = [x for x in svc._source_status if x["skipped_reason"] == "budget_exhausted"]
    assert len(budget_logs) == 1


def test_deep_mode_is_the_only_mode_that_enables_professional_matrix():
    svc = ModeProbeService()
    svc._search_all("q", "300274", "Sungrow", 60, mode="deep")
    assert "professional_matrix" in svc.calls
