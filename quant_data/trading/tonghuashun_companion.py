from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from typing import Any

from quant_data.persistence.trading_store import TradingStore
from quant_data.utils import normalize_symbol


class TonghuashunCompanion:
    """Safe local companion for Tonghuashun desktop clients.

    The retail desktop executables do not expose a verified order API here.
    This integration therefore launches the user-owned client and persists a
    risk-aware manual order reminder.  It never logs in, sends keystrokes,
    clicks controls, submits an order, or reports a manual reminder as a fill.
    """

    CONFIG_KEY = "tonghuashun_companion"
    ALLOWED_REMINDER_STATUS = {
        "ready_for_manual_entry",
        "risk_blocked",
        "acknowledged",
        "manually_submitted_unverified",
        "cancelled",
    }

    def __init__(
        self,
        store: TradingStore | None = None,
        config_db_path: str | Path = "data/local_integrations.sqlite",
        env: dict[str, str] | None = None,
    ) -> None:
        self.store = store or TradingStore()
        self.config_db_path = Path(config_db_path)
        self.config_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.env = env if env is not None else os.environ
        self._init_config_store()

    def _init_config_store(self) -> None:
        with sqlite3.connect(self.config_db_path) as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS local_integrations (
                    integration_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def configure(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self._load_config()
        config = {
            "enabled": _bool_value(payload.get("enabled"), bool(current.get("enabled", False))),
            "launcher_path": str(payload.get("launcher_path") or current.get("launcher_path") or "").strip(),
            "order_app_path": str(payload.get("order_app_path") or current.get("order_app_path") or "").strip(),
            "mode": "manual_order_reminder",
            "updated_at": _now(),
        }
        for key in ("launcher_path", "order_app_path"):
            value = config[key]
            if value and Path(value).suffix.lower() != ".exe":
                return {"ok": False, "message": f"{key} 必须指向本地 .exe 文件", "data": self.status()}
        with sqlite3.connect(self.config_db_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO local_integrations(integration_key,payload_json,updated_at) VALUES(?,?,?)",
                (self.CONFIG_KEY, json.dumps(config, ensure_ascii=False), config["updated_at"]),
            )
        return {"ok": True, "data": self.status(), "message": "同花顺本地伴随配置已保存"}

    def status(self) -> dict[str, Any]:
        config = self._effective_config()
        launcher = Path(config.get("launcher_path") or "") if config.get("launcher_path") else None
        order_app = Path(config.get("order_app_path") or "") if config.get("order_app_path") else None
        launcher_exists = bool(launcher and launcher.is_file())
        order_app_exists = bool(order_app and order_app.is_file())
        enabled = bool(config.get("enabled"))
        reasons: list[str] = []
        if not enabled:
            reasons.append("本地伴随功能未启用")
        if not launcher_exists:
            reasons.append("启动器路径未配置或文件不存在")
        if not order_app_exists:
            reasons.append("委托程序路径未配置或文件不存在")
        return {
            "ok": True,
            "integration": "同花顺本地客户端",
            "mode": "委托提醒 + 人工录入",
            "enabled": enabled,
            "launcher_path": str(launcher) if launcher else "",
            "launcher_exists": launcher_exists,
            "order_app_path": str(order_app) if order_app else "",
            "order_app_exists": order_app_exists,
            "ready_to_launch": bool(enabled and (launcher_exists or order_app_exists)),
            "official_order_api": False,
            "automatic_order_submission": False,
            "broker_adapter": False,
            "missing_reasons": reasons,
            "truth_boundary": "只唤起本地客户端并生成委托提醒；不登录、不操作界面、不提交订单、不确认成交。真实自动交易仍只走受支持券商适配器。",
            "updated_at": config.get("updated_at") or "",
        }

    def launch(self, target: str = "launcher") -> dict[str, Any]:
        status = self.status()
        if not status["enabled"]:
            return {"ok": False, "message": "请先显式启用同花顺本地伴随功能", "data": status}
        key = "order_app_path" if str(target).lower() in {"order", "xiadan", "trade"} else "launcher_path"
        path_text = str(status.get(key) or "")
        path = Path(path_text) if path_text else None
        if not path or not path.is_file():
            return {"ok": False, "message": f"{key} 未配置或文件不存在", "data": status}
        try:
            proc = subprocess.Popen([str(path)], cwd=str(path.parent), close_fds=True)
        except Exception as exc:
            return {"ok": False, "message": f"启动失败：{str(exc)[:180]}", "data": status}
        event = {
            "event_type": "tonghuashun_client_launched",
            "target": "委托程序" if key == "order_app_path" else "行情客户端",
            "executable": str(path),
            "pid": proc.pid,
            "created_at": _now(),
            "broker_submitted": False,
        }
        self.store.put("audit_events", event, mode="manual_companion", record_id=_stable_id("launch", event))
        return {"ok": True, "data": event, "message": "已唤起同花顺客户端；系统未执行登录或委托"}

    def create_reminder(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = normalize_symbol(str(payload.get("symbol") or ""))
        side = str(payload.get("side") or "").strip().lower()
        quantity = int(float(payload.get("quantity") or 0))
        limit_price = _number(payload.get("limit_price") or payload.get("price"))
        if len(symbol) != 6 or not symbol.isdigit():
            return {"ok": False, "message": "股票代码必须为6位数字"}
        if side not in {"buy", "sell"}:
            return {"ok": False, "message": "方向必须为买入或卖出"}
        if quantity <= 0:
            return {"ok": False, "message": "股数必须大于0"}
        risk_check_id = str(payload.get("risk_check_id") or "")
        provenance_id = str(payload.get("provenance_id") or "")
        risk_record = self.store.get("risk_checks", risk_check_id) if risk_check_id else None
        risk_order = (risk_record or {}).get("order") if isinstance((risk_record or {}).get("order"), dict) else {}
        risk_matches = (
            str((risk_record or {}).get("symbol") or risk_order.get("symbol") or "") == symbol
            and str((risk_record or {}).get("mode") or "") == "live"
            and str(risk_order.get("side") or "").lower() == side
            and int(float(risk_order.get("quantity") or 0)) == quantity
        )
        risk_approved = bool(risk_record) and risk_matches and bool(
            (risk_record or {}).get("approved", (risk_record or {}).get("allowed", False))
        )
        provenance = self.store.get("score_provenance", provenance_id) if provenance_id else None
        provenance_matches = (
            bool(provenance)
            and str((provenance or {}).get("symbol") or "") == symbol
            and str((provenance or {}).get("mode") or "") in {"realtime_paper", "live"}
        )
        readiness = (
            dict((provenance or {}).get("dimension_readiness") or {})
            if isinstance((provenance or {}).get("dimension_readiness"), dict)
            else {}
        )
        max_score_age = max(30, min(3600, int(self.env.get("LIVE_SCORE_MAX_AGE_SECONDS") or 300)))
        provenance_recent = self._provenance_recent(provenance or {}, max_age_seconds=max_score_age)
        dimensions_ready = bool(readiness.get("auto_entry_eligible")) if side == "buy" else provenance_matches
        risk_approved = risk_approved and provenance_matches and provenance_recent and dimensions_ready
        risk_reasons = list(payload.get("risk_reasons") or [])
        if not risk_record:
            risk_reasons.append("缺少服务端已落库的实盘风控记录")
        elif not risk_matches:
            risk_reasons.append("风控记录与代码、方向或股数不一致")
        elif not bool((risk_record or {}).get("approved", (risk_record or {}).get("allowed", False))):
            risk_reasons.append("服务端风控未通过")
        if not provenance_matches:
            risk_reasons.append("缺少同标的实时评分溯源")
        elif not provenance_recent:
            risk_reasons.append(f"评分溯源已过期或时间无效（最长{max_score_age}秒）")
        elif side == "buy" and not dimensions_ready:
            risk_reasons.extend(str(value) for value in readiness.get("entry_block_reasons") or ["三面决策门禁未通过"])
        risk_reasons = list(dict.fromkeys(reason for reason in risk_reasons if reason))
        status = "ready_for_manual_entry" if risk_approved else "risk_blocked"
        created_at = _now()
        reminder_id = _stable_id("ths-reminder", symbol, side, quantity, limit_price, created_at)
        reminder = {
            "reminder_id": reminder_id,
            "mode": "manual_companion",
            "symbol": symbol,
            "name": str(payload.get("name") or ""),
            "side": side,
            "side_cn": "买入" if side == "buy" else "卖出",
            "quantity": quantity,
            "limit_price": limit_price,
            "estimated_amount": round(quantity * limit_price, 2) if limit_price else None,
            "signal_score": _number(payload.get("signal_score")),
            "provenance_id": provenance_id,
            "risk_check_id": risk_check_id,
            "risk_approved": risk_approved,
            "risk_reasons": risk_reasons,
            "decision_dimensions_ready": dimensions_ready,
            "score_provenance_recent": provenance_recent,
            "score_max_age_seconds": max_score_age,
            "decision_snapshot": {
                "final_trade_score": (provenance or {}).get("final_trade_score", (provenance or {}).get("final_score")),
                "decision_time": (provenance or {}).get("decision_time") or (provenance or {}).get("created_at"),
                "strategy_family": (provenance or {}).get("strategy_family"),
                "dimension_readiness": readiness,
            },
            "reason": str(payload.get("reason") or ""),
            "status": status,
            "status_cn": "待人工录入" if risk_approved else "风控阻断",
            "created_at": created_at,
            "updated_at": created_at,
            "broker_submitted": False,
            "fill_verified": False,
            "truth_boundary": "这是一张人工委托提醒票据，不是券商委托、成交或持仓证明。",
        }
        self.store.put(
            "tonghuashun_reminders",
            reminder,
            mode="manual_companion",
            symbol=symbol,
            record_id=reminder_id,
        )
        self.store.put(
            "audit_events",
            {"event_type": "tonghuashun_reminder_created", **reminder},
            mode="manual_companion",
            symbol=symbol,
            record_id=_stable_id("audit", reminder_id),
        )
        return {
            "ok": risk_approved,
            "data": reminder,
            "message": "委托提醒已生成，请在同花顺中人工核对并录入" if risk_approved else "风控未通过，仅保存阻断记录",
        }

    def list_reminders(self, limit: int = 100, status: str = "") -> list[dict[str, Any]]:
        rows = self.store.list("tonghuashun_reminders", mode="manual_companion", limit=max(1, min(int(limit or 100), 1000)))
        if status:
            rows = [row for row in rows if str(row.get("status") or "") == status]
        return rows

    def update_reminder(self, reminder_id: str, status: str) -> dict[str, Any]:
        status = str(status or "").strip().lower()
        if status not in self.ALLOWED_REMINDER_STATUS:
            return {"ok": False, "message": "不支持的提醒状态"}
        current = next((row for row in self.list_reminders(limit=1000) if str(row.get("reminder_id") or row.get("id")) == reminder_id), None)
        if not current:
            return {"ok": False, "message": "未找到委托提醒"}
        labels = {
            "ready_for_manual_entry": "待人工录入",
            "risk_blocked": "风控阻断",
            "acknowledged": "已查看",
            "manually_submitted_unverified": "已人工提交/待券商核验",
            "cancelled": "已取消",
        }
        updated = {
            **current,
            "status": status,
            "status_cn": labels[status],
            "updated_at": _now(),
            "broker_submitted": False,
            "fill_verified": False,
        }
        self.store.put(
            "tonghuashun_reminders",
            updated,
            mode="manual_companion",
            symbol=str(updated.get("symbol") or ""),
            record_id=reminder_id,
        )
        return {"ok": True, "data": updated, "message": "状态已更新；仍不代表券商已受理或成交"}

    @staticmethod
    def _provenance_recent(provenance: dict[str, Any], *, max_age_seconds: int = 300) -> bool:
        raw = provenance.get("decision_time") or provenance.get("created_at")
        if not raw:
            return False
        try:
            decision_time = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            current = datetime.now(decision_time.tzinfo) if decision_time.tzinfo else datetime.now()
            age = (current - decision_time).total_seconds()
        except (TypeError, ValueError):
            return False
        return -5 <= age <= max(30, int(max_age_seconds or 300))

    def _effective_config(self) -> dict[str, Any]:
        config = self._load_config()
        if self.env.get("TONGHUASHUN_REMINDER_ENABLED") is not None:
            config["enabled"] = str(self.env.get("TONGHUASHUN_REMINDER_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}
        if self.env.get("TONGHUASHUN_LAUNCHER_PATH"):
            config["launcher_path"] = str(self.env["TONGHUASHUN_LAUNCHER_PATH"])
        if self.env.get("TONGHUASHUN_ORDER_APP_PATH"):
            config["order_app_path"] = str(self.env["TONGHUASHUN_ORDER_APP_PATH"])
        return config

    def _load_config(self) -> dict[str, Any]:
        with sqlite3.connect(self.config_db_path) as con:
            row = con.execute(
                "SELECT payload_json,updated_at FROM local_integrations WHERE integration_key=?",
                (self.CONFIG_KEY,),
            ).fetchone()
        if not row:
            return {"enabled": False, "launcher_path": "", "order_app_path": "", "updated_at": ""}
        try:
            data = json.loads(row[0])
            if isinstance(data, dict):
                data.setdefault("updated_at", row[1])
                return data
        except Exception:
            pass
        return {"enabled": False, "launcher_path": "", "order_app_path": "", "updated_at": ""}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _number(value: Any) -> float | None:
    try:
        number = float(value)
        return round(number, 4) if number > 0 else None
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _stable_id(*parts: Any) -> str:
    text = "|".join(json.dumps(part, ensure_ascii=False, sort_keys=True, default=str) for part in parts)
    return sha256(text.encode("utf-8", "ignore")).hexdigest()[:24]
