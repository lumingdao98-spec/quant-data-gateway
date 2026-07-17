from __future__ import annotations

import json

from quant_data.services.market_ai_service import MarketAiConfig, MarketAiService


class _Response:
    headers = {"x-request-id": "req-test"}

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "id": "resp-test",
            "output_text": json.dumps(
                {
                    "summary": "近期宏观证据提示先做模拟验证。",
                    "market_regime": "波动偏高",
                    "confidence": 0.72,
                    "symbol_views": [
                        {
                            "symbol": "300750",
                            "action": "模拟验证",
                            "reason": "美元与利率预期可能影响成长估值。",
                            "evidence_refs": ["E1", "E999"],
                        }
                    ],
                    "risks": ["证据仍有限"],
                    "missing_data": ["缺少券商实时成交"],
                },
                ensure_ascii=False,
            ),
        }


class _Session:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()


def test_market_ai_is_disabled_by_default_and_cannot_order():
    service = MarketAiService(MarketAiConfig())

    status = service.status()

    assert status["status"] == "disabled"
    assert status["order_capability"] is False


def test_market_ai_only_uses_traceable_evidence_and_sanitizes_output():
    session = _Session()
    service = MarketAiService(
        MarketAiConfig(enabled=True, api_key="secret", model="unit-model"),
        session=session,
    )

    result = service.analyze(
        symbols=["300750"],
        evidence=[
            {
                "title": "美国就业数据公布",
                "source": "公开宏观源",
                "source_ref": "https://example.com/macro/1",
                "published_at": "2026-07-16T20:30:00",
            },
            {"title": "缺少来源的传闻", "source": "未知"},
        ],
        rule_summary={"recommended_action": "观察"},
    )

    assert result["ok"] is True
    assert result["order_capability"] is False
    assert result["analysis"]["symbol_views"][0]["evidence_refs"] == ["E1"]
    assert result["analysis"]["research_only"] is True
    assert result["evidence_count"] == 1
    _, request = session.calls[0]
    assert request["json"]["store"] is False
    assert request["headers"]["Authorization"] == "Bearer secret"
    assert "secret" not in json.dumps(request["json"], ensure_ascii=False)
