from __future__ import annotations

from base64 import b64encode
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import hmac
import json
import os
import time
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from quant_data.persistence.trading_store import TradingStore


AlertTransport = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


@dataclass(slots=True)
class MobileAlertConfig:
    enabled: bool = False
    provider: str = "disabled"
    webhook_url: str = ""
    secret: str = ""
    minimum_level: str = "warning"
    cooldown_seconds: int = 60
    timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "MobileAlertConfig":
        data = env or os.environ
        return cls(
            enabled=_bool(data.get("MOBILE_ALERTS_ENABLED"), False),
            provider=str(data.get("MOBILE_ALERT_PROVIDER") or "disabled").strip().lower(),
            webhook_url=str(data.get("MOBILE_ALERT_WEBHOOK_URL") or "").strip(),
            secret=str(data.get("MOBILE_ALERT_SECRET") or "").strip(),
            minimum_level=str(data.get("MOBILE_ALERT_MIN_LEVEL") or "warning").strip().lower(),
            cooldown_seconds=max(0, min(3600, int(data.get("MOBILE_ALERT_COOLDOWN_SECONDS") or 60))),
            timeout_seconds=max(1.0, min(20.0, float(data.get("MOBILE_ALERT_TIMEOUT_SECONDS") or 5.0))),
        )

    def safe_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["webhook_url"] = _safe_webhook_label(self.webhook_url)
        data["secret"] = "已配置" if self.secret else ""
        return data


class MobileNotificationService:
    """Best-effort mobile alerts that never alter the trading decision path."""

    PROVIDERS = {"dingtalk", "feishu", "wecom", "generic"}
    LEVELS = {"info": 10, "warning": 20, "critical": 30}

    def __init__(
        self,
        config: MobileAlertConfig | None = None,
        *,
        store: TradingStore | None = None,
        transport: AlertTransport | None = None,
    ) -> None:
        self.config = config or MobileAlertConfig.from_env()
        self.store = store
        self.transport = transport or self._default_transport
        self._sent_at: dict[str, float] = {}

    def status(self) -> dict[str, Any]:
        reasons: list[str] = []
        if not self.config.enabled:
            reasons.append("移动端提醒默认关闭")
        if self.config.provider not in self.PROVIDERS:
            reasons.append("未选择受支持的提醒提供方")
        if not self._valid_webhook(self.config.webhook_url):
            reasons.append("Webhook 地址缺失或不是允许的 HTTPS/本机地址")
        return {
            "ok": True,
            "enabled": self.config.enabled,
            "provider": self.config.provider,
            "configuration_ready": not reasons or (len(reasons) == 1 and reasons[0] == "移动端提醒默认关闭"),
            "safe_config": self.config.safe_dict(),
            "missing_reasons": reasons,
            "supported_providers": ["dingtalk", "feishu", "wecom", "generic"],
            "event_types": ["needs_confirmation", "risk_blocked", "order_submitted", "kill_switch"],
            "truth_boundary": "移动提醒只转发已落库状态，不等于券商受理或成交证明；发送失败不会绕过或改变交易风控。",
        }

    def preview(self, event: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_event(event)
        return {
            "ok": True,
            "data": normalized,
            "message": self._message(normalized),
            "payload": self._provider_payload(normalized),
        }

    def send(self, event: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_event(event)
        if not self.config.enabled:
            return {"ok": False, "status": "disabled", "message": "移动端提醒未启用", "data": normalized}
        if self.config.provider not in self.PROVIDERS:
            return {"ok": False, "status": "unsupported", "message": "提醒提供方不支持", "data": normalized}
        if not self._valid_webhook(self.config.webhook_url):
            return {"ok": False, "status": "invalid_config", "message": "Webhook 配置无效", "data": normalized}
        if self.LEVELS.get(normalized["level"], 10) < self.LEVELS.get(self.config.minimum_level, 20):
            return {"ok": False, "status": "level_filtered", "message": "提醒级别低于发送阈值", "data": normalized}
        key = f"{normalized['event_type']}|{normalized['symbol']}|{normalized['status']}"
        now = time.monotonic()
        if self.config.cooldown_seconds and now - self._sent_at.get(key, -10_000) < self.config.cooldown_seconds:
            return {"ok": False, "status": "cooldown", "message": "同类提醒处于冷却期", "data": normalized}
        url = self._signed_url(self.config.webhook_url)
        try:
            response = self.transport(url, self._provider_payload(normalized), {"Content-Type": "application/json"})
        except Exception as exc:
            result = {"ok": False, "status": "failed", "message": f"提醒发送失败: {str(exc)[:180]}", "data": normalized}
            self._audit(result)
            return result
        self._sent_at[key] = now
        result = {"ok": True, "status": "sent", "message": "移动提醒已发送", "data": normalized, "provider_response": _redact_response(response)}
        self._audit(result)
        return result

    def _normalize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_type = str(event.get("event_type") or "trading_notice").strip().lower()
        labels = {
            "needs_confirmation": "真实订单待人工确认",
            "risk_blocked": "交易已被风控阻断",
            "order_submitted": "订单已提交券商",
            "kill_switch": "真实交易紧急停止状态变更",
            "manual_test": "移动提醒联通测试",
        }
        level = str(event.get("level") or ("critical" if event_type == "kill_switch" else "warning")).lower()
        if level not in self.LEVELS:
            level = "warning"
        return {
            "event_type": event_type,
            "title": str(event.get("title") or labels.get(event_type) or "量化网关交易提醒")[:80],
            "level": level,
            "mode": str(event.get("mode") or "live"),
            "symbol": str(event.get("symbol") or ""),
            "name": str(event.get("name") or ""),
            "side": str(event.get("side") or ""),
            "quantity": int(float(event.get("quantity") or 0)),
            "price": _number(event.get("price") or event.get("limit_price")),
            "status": str(event.get("status") or event_type),
            "reason": str(event.get("reason") or "")[:500],
            "order_id": str(event.get("order_id") or ""),
            "confirmation_id": str(event.get("confirmation_id") or event.get("confirm_id") or ""),
            "created_at": str(event.get("created_at") or datetime.now().isoformat(timespec="seconds")),
        }

    def _message(self, event: dict[str, Any]) -> str:
        side = {"buy": "买入", "sell": "卖出"}.get(event["side"], event["side"] or "方向缺失")
        target = " ".join(value for value in (event["name"], event["symbol"]) if value) or "标的缺失"
        price = f" @ {event['price']:.3f}" if event["price"] is not None else ""
        reason = event["reason"] or "原因见系统审计记录"
        return (
            f"### {event['title']}\n"
            f"- 标的：{target}\n"
            f"- 动作：{side} {event['quantity']} 股{price}\n"
            f"- 状态：{event['status']}\n"
            f"- 原因：{reason}\n"
            f"- 时间：{event['created_at']}\n\n"
            "研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。"
        )

    def _provider_payload(self, event: dict[str, Any]) -> dict[str, Any]:
        message = self._message(event)
        if self.config.provider == "dingtalk":
            return {"msgtype": "markdown", "markdown": {"title": event["title"], "text": message}}
        if self.config.provider == "feishu":
            return {"msg_type": "text", "content": {"text": message.replace("### ", "")}}
        if self.config.provider == "wecom":
            return {"msgtype": "markdown", "markdown": {"content": message}}
        return {"event": event, "message": message}

    def _signed_url(self, url: str) -> str:
        if self.config.provider != "dingtalk" or not self.config.secret:
            return url
        timestamp = str(int(time.time() * 1000))
        digest = hmac.new(
            self.config.secret.encode("utf-8"),
            f"{timestamp}\n{self.config.secret}".encode("utf-8"),
            sha256,
        ).digest()
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.update({"timestamp": timestamp, "sign": b64encode(digest).decode("ascii")})
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    def _audit(self, result: dict[str, Any]) -> None:
        if self.store is None:
            return
        event = dict(result.get("data") or {})
        payload = {
            "event_type": "mobile_alert",
            "notification_status": result.get("status"),
            "provider": self.config.provider,
            "message": result.get("message"),
            "trading_event": event,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        record_id = sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]
        self.store.put("audit_events", payload, mode="notification", symbol=str(event.get("symbol") or ""), record_id=record_id)

    @staticmethod
    def _valid_webhook(url: str) -> bool:
        parts = urlsplit(str(url or ""))
        host = (parts.hostname or "").lower()
        return bool(parts.scheme == "https" or (parts.scheme == "http" and host in {"127.0.0.1", "localhost", "::1"}))

    def _default_transport(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        request = Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST", headers=headers)
        with urlopen(request, timeout=self.config.timeout_seconds) as response:
            raw = response.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {"body": raw[:500]}
        return parsed if isinstance(parsed, dict) else {"data": parsed}


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _safe_webhook_label(url: str) -> str:
    parts = urlsplit(str(url or ""))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")) if parts.scheme and parts.netloc else ""


def _redact_response(response: dict[str, Any]) -> dict[str, Any]:
    blocked = {"token", "access_token", "secret", "authorization", "cookie"}
    return {str(key): ("已隐藏" if str(key).lower() in blocked else value) for key, value in dict(response or {}).items()}
