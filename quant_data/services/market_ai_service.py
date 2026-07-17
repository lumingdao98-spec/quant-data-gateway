from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
import os
from threading import RLock
from typing import Any

import requests


def _bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


@dataclass(slots=True)
class MarketAiConfig:
    enabled: bool = False
    provider: str = "openai"
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    timeout_seconds: float = 20.0
    cache_seconds: int = 180

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "MarketAiConfig":
        data = env or os.environ
        return cls(
            enabled=_bool(data.get("MARKET_AI_ENABLED"), False),
            provider=str(data.get("MARKET_AI_PROVIDER") or "openai").strip().lower(),
            api_base=str(data.get("MARKET_AI_API_BASE") or data.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
            api_key=str(data.get("MARKET_AI_API_KEY") or data.get("OPENAI_API_KEY") or ""),
            model=str(data.get("MARKET_AI_MODEL") or "").strip(),
            timeout_seconds=max(3.0, min(_float(data.get("MARKET_AI_TIMEOUT_SECONDS"), 20.0), 60.0)),
            cache_seconds=max(30, min(int(_float(data.get("MARKET_AI_CACHE_SECONDS"), 180)), 1800)),
        )

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("api_key", None)
        data["configured"] = bool(self.enabled and self.api_key and self.model)
        return data


class MarketAiService:
    """Optional evidence-grounded market analyst.

    It can explain evidence but never returns or routes executable orders.  The
    deterministic rule engine remains available when no model is configured.
    """

    _allowed_actions = {"观察", "模拟验证", "人工复核", "降低风险"}

    def __init__(self, config: MarketAiConfig | None = None, session: requests.Session | None = None) -> None:
        self.config = config or MarketAiConfig.from_env()
        self.session = session or requests.Session()
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}
        self._lock = RLock()

    def status(self) -> dict[str, Any]:
        cfg = self.config.public_dict()
        if not self.config.enabled:
            status, reason = "disabled", "MARKET_AI_ENABLED=false；仅使用联网数据与规则证据代理。"
        elif not self.config.api_key:
            status, reason = "missing_api_key", "未配置 MARKET_AI_API_KEY/OPENAI_API_KEY。"
        elif not self.config.model:
            status, reason = "missing_model", "未配置 MARKET_AI_MODEL。"
        elif self.config.provider not in {"openai", "openai_compatible"}:
            status, reason = "unsupported", f"暂不支持模型提供方 {self.config.provider}。"
        else:
            status, reason = "ready", "模型仅用于证据解释，不能直接创建、确认或提交订单。"
        return {"status": status, "reason": reason, **cfg, "order_capability": False}

    def analyze(
        self,
        *,
        symbols: list[str],
        evidence: list[dict[str, Any]],
        rule_summary: dict[str, Any],
        force: bool = False,
    ) -> dict[str, Any]:
        status = self.status()
        if status["status"] != "ready":
            return {"ok": False, "status": status["status"], "reason": status["reason"], "analysis": None, "provider": status}

        grounded = self._ground_evidence(evidence)
        if not grounded:
            return {
                "ok": False,
                "status": "missing_evidence",
                "reason": "没有近期、可追溯证据，拒绝调用模型生成市场结论。",
                "analysis": None,
                "provider": status,
            }
        cache_key = self._cache_key(symbols, grounded, rule_summary)
        if not force:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return {**cached, "cache_hit": True}

        payload = self._request_payload(symbols, grounded, rule_summary)
        try:
            response = self.session.post(
                f"{self.config.api_base}/responses",
                headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            raw = response.json()
            parsed = self._parse_response(raw)
            analysis = self._validate_analysis(parsed, grounded, symbols)
            result = {
                "ok": True,
                "status": "completed",
                "analysis": analysis,
                "provider": status,
                "model": self.config.model,
                "request_id": str(raw.get("id") or response.headers.get("x-request-id") or ""),
                "evidence_count": len(grounded),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "cache_hit": False,
                "order_capability": False,
            }
            self._put_cache(cache_key, result)
            return result
        except Exception as exc:
            return {
                "ok": False,
                "status": "provider_error",
                "reason": f"联网模型调用失败：{str(exc)[:240]}",
                "analysis": None,
                "provider": status,
                "order_capability": False,
            }

    def _ground_evidence(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in evidence or []:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or row.get("reason") or "").strip()
            source = str(row.get("source") or "").strip()
            source_ref = str(row.get("source_ref") or row.get("source_page") or "").strip()
            published_at = str(row.get("published_at") or "").strip()
            if not title or not source or not (source_ref or row.get("source_api")):
                continue
            out.append(
                {
                    "evidence_id": f"E{len(out) + 1}",
                    "title": title[:260],
                    "source": source[:80],
                    "source_ref": source_ref[:500],
                    "source_api": str(row.get("source_api") or "")[:500],
                    "published_at": published_at[:40],
                    "impact_targets": [str(x)[:60] for x in list(row.get("impact_targets") or [])[:10]],
                    "impact_note": str(row.get("impact_note") or "")[:300],
                }
            )
            if len(out) >= 20:
                break
        return out

    def _request_payload(self, symbols: list[str], evidence: list[dict[str, Any]], rule_summary: dict[str, Any]) -> dict[str, Any]:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "summary": {"type": "string"},
                "market_regime": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "symbol_views": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "symbol": {"type": "string"},
                            "action": {"type": "string", "enum": sorted(self._allowed_actions)},
                            "reason": {"type": "string"},
                            "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["symbol", "action", "reason", "evidence_refs"],
                    },
                },
                "risks": {"type": "array", "items": {"type": "string"}},
                "missing_data": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "market_regime", "confidence", "symbol_views", "risks", "missing_data"],
        }
        system = (
            "你是A股研究辅助分析员。只能根据输入的真实证据和规则摘要作解释，不得补写新闻、价格、日期或来源。"
            "不得发出可执行买卖指令，不得绕过风控；动作只能是观察、模拟验证、人工复核、降低风险。"
            "每个个股理由必须引用 evidence_id；没有证据时写入 missing_data。输出简洁中文结构化JSON。"
        )
        user = json.dumps(
            {"symbols": symbols[:30], "evidence": evidence, "rule_summary": rule_summary, "research_only": True},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return {
            "model": self.config.model,
            "store": False,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            "text": {"format": {"type": "json_schema", "name": "grounded_market_brief", "strict": True, "schema": schema}},
            "max_output_tokens": 1400,
        }

    @staticmethod
    def _parse_response(raw: dict[str, Any]) -> dict[str, Any]:
        text = str(raw.get("output_text") or "").strip()
        if not text:
            for item in raw.get("output") or []:
                for content in item.get("content") or []:
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        text = str(content.get("text")).strip()
                        break
                if text:
                    break
        if not text:
            raise ValueError("模型响应缺少 output_text")
        return json.loads(text)

    def _validate_analysis(self, parsed: dict[str, Any], evidence: list[dict[str, Any]], symbols: list[str]) -> dict[str, Any]:
        allowed_refs = {x["evidence_id"] for x in evidence}
        allowed_symbols = {str(x) for x in symbols}
        views = []
        for item in parsed.get("symbol_views") or []:
            symbol = str(item.get("symbol") or "")
            if symbol not in allowed_symbols:
                continue
            action = str(item.get("action") or "观察")
            if action not in self._allowed_actions:
                action = "人工复核"
            refs = [str(x) for x in item.get("evidence_refs") or [] if str(x) in allowed_refs]
            views.append({"symbol": symbol, "action": action, "reason": str(item.get("reason") or "")[:500], "evidence_refs": refs})
        return {
            "summary": str(parsed.get("summary") or "")[:800],
            "market_regime": str(parsed.get("market_regime") or "")[:200],
            "confidence": max(0.0, min(_float(parsed.get("confidence"), 0.0), 1.0)),
            "symbol_views": views,
            "risks": [str(x)[:300] for x in list(parsed.get("risks") or [])[:12]],
            "missing_data": [str(x)[:300] for x in list(parsed.get("missing_data") or [])[:12]],
            "evidence": evidence,
            "research_only": True,
            "order_capability": False,
        }

    def _cache_key(self, symbols: list[str], evidence: list[dict[str, Any]], rule_summary: dict[str, Any]) -> str:
        raw = json.dumps([symbols, evidence, rule_summary, self.config.model], ensure_ascii=False, sort_keys=True, default=str)
        return sha256(raw.encode("utf-8")).hexdigest()

    def _get_cache(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._cache.get(key)
            if not row:
                return None
            created_at, data = row
            if datetime.now() - created_at > timedelta(seconds=self.config.cache_seconds):
                self._cache.pop(key, None)
                return None
            return dict(data)

    def _put_cache(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._cache[key] = (datetime.now(), dict(value))
