from __future__ import annotations

from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any, Callable
from urllib.parse import urlparse

from .broker_config import BrokerConfig, load_broker_config


QMT_OFFICIAL_DOCS = [
    {
        "label": "QMT 原生 API 使用说明",
        "url": "https://dict.thinktrader.net/nativeApi/question_function.html",
    },
    {
        "label": "XtQuantTrader 交易接口",
        "url": "https://dict.thinktrader.net/nativeApi/xttrader.html",
    },
]

PTRADE_REFERENCE_DOCS = [
    {
        "label": "山西证券 PTrade 量化平台",
        "url": "https://www.sxzq.com/main/companybusi/wealth/quantitativetrading/ptradedoc/index.shtml",
    },
    {
        "label": "长江证券 PTrade 终端",
        "url": "https://www.cjsc.com.cn/main/software/index.shtml",
    },
]

TONGHUASHUN_OFFICIAL_DOCS = [
    {
        "label": "同花顺 iFinD 数据 API",
        "url": "https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/quantapi-web/",
    },
    {
        "label": "iFinD Python SDK 安装说明",
        "url": "https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html",
    },
    {
        "label": "同花顺 SuperMind 量化平台",
        "url": "https://quant.10jqka.com.cn/",
    },
    {
        "label": "SuperMind 实盘交易说明",
        "url": "https://quant.10jqka.com.cn/view/article/5G0JNYZPR4154366JH1M42QX5Q",
    },
]


class BrokerSetupService:
    """Read-only broker onboarding diagnostics.

    The service deliberately does not persist credentials or turn on live
    trading. Users configure environment variables or a private local launcher,
    restart the gateway, and then use the normal connect endpoint.
    """

    def __init__(
        self,
        config: BrokerConfig | None = None,
        *,
        companion_status_provider: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.config = config or load_broker_config()
        self.companion_status_provider = companion_status_provider

    def inspect(self, broker_type: str = "") -> dict[str, Any]:
        selected = str(broker_type or self.config.broker_type or "disabled").strip().lower()
        diagnostics = {
            "qmt": self._qmt_diagnostics(self.config),
            "ptrade": self._ptrade_diagnostics(self.config),
            "tonghuashun": self._tonghuashun_diagnostics(self.config),
            "http_bridge": self._http_bridge_diagnostics(self.config),
        }
        for broker_name, diagnostic in diagnostics.items():
            diagnostic["capabilities"] = self._capabilities(broker_name, diagnostic)
        active = diagnostics.get(selected) or {
            "status": "not_selected",
            "ready_to_connect": False,
            "missing_reasons": ["尚未选择 QMT、PTrade、同花顺授权桥或本地 HTTP 券商桥。"],
        }
        return {
            "ok": True,
            "selected_broker": selected,
            "active": active,
            "brokers": diagnostics,
            "safe_config": self.config.to_safe_dict(),
            "safety": self._safety(self.config),
            "environment_templates": {
                "qmt": self.environment_template("qmt"),
                "ptrade": self.environment_template("ptrade"),
                "tonghuashun": self.environment_template("tonghuashun"),
                "http_bridge": self.environment_template("http_bridge"),
            },
            "official_docs": {
                "qmt": QMT_OFFICIAL_DOCS,
                "ptrade": PTRADE_REFERENCE_DOCS,
                "tonghuashun": TONGHUASHUN_OFFICIAL_DOCS,
            },
            "truth_boundary": (
                "接入诊断只检查本机组件和配置，不登录券商、不保存账号密钥、不下单。"
                "真实交易仍需全部安全开关、白名单、评分溯源、风控和人工确认。"
            ),
        }

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        selected = str(payload.get("broker_type") or self.config.broker_type or "disabled").strip().lower()
        config = replace(
            self.config,
            broker_type=selected,
            qmt_path=str(payload.get("qmt_path", self.config.qmt_path) or "").strip(),
            qmt_account_id=str(payload.get("qmt_account_id", self.config.qmt_account_id) or "").strip(),
            qmt_account_type=str(payload.get("qmt_account_type", self.config.qmt_account_type) or "").strip(),
            qmt_session_id=str(payload.get("qmt_session_id", self.config.qmt_session_id) or "").strip(),
            ptrade_path=str(payload.get("ptrade_path", self.config.ptrade_path) or "").strip(),
            ptrade_account_id=str(payload.get("ptrade_account_id", self.config.ptrade_account_id) or "").strip(),
            ptrade_module=str(payload.get("ptrade_module", self.config.ptrade_module) or "ptrade").strip(),
            ptrade_client_factory=str(payload.get("ptrade_client_factory", self.config.ptrade_client_factory) or "").strip(),
            http_bridge_url=str(payload.get("http_bridge_url", self.config.http_bridge_url) or "").strip(),
            http_bridge_token=str(payload.get("http_bridge_token", self.config.http_bridge_token) or "").strip(),
        )
        result = BrokerSetupService(
            config,
            companion_status_provider=self.companion_status_provider,
        ).inspect(selected)
        result["validation_only"] = True
        result["restart_required"] = True
        result["message"] = "校验完成；网页输入未写入磁盘或环境变量。按模板配置并重启服务后再执行连接检查。"
        return result

    def environment_template(self, broker_type: str) -> str:
        common = [
            f"BROKER_TYPE={broker_type}",
            "FEATURE_LIVE_BROKER=false",
            "LIVE_TRADING_ENABLED=false",
            "ORDER_CONFIRM_REQUIRED=true",
            "LIVE_KILL_SWITCH=false",
            "TRADE_WHITELIST_SYMBOLS=",
            "MAX_LIVE_ORDER_VALUE=50000",
            "MAX_DAILY_LIVE_ORDER_COUNT=5",
            "MAX_DAILY_LOSS_PCT=0.03",
        ]
        if broker_type == "qmt":
            common.extend(
                [
                    r"QMT_PATH=D:\path\to\userdata_mini",
                    "QMT_ACCOUNT_ID=",
                    "QMT_ACCOUNT_TYPE=STOCK",
                    "QMT_SESSION_ID=10001",
                ]
            )
        elif broker_type == "ptrade":
            common.extend(
                [
                    "# PTrade 通常运行在券商托管平台；仅在券商明确提供本地模块时配置以下字段。",
                    "PTRADE_PATH=",
                    "PTRADE_ACCOUNT_ID=",
                    "PTRADE_MODULE=",
                    "PTRADE_CLIENT_FACTORY=",
                ]
            )
        elif broker_type == "http_bridge":
            common.extend(
                [
                    "BROKER_HTTP_URL=http://127.0.0.1:8765",
                    "BROKER_HTTP_TOKEN=",
                    "BROKER_HTTP_ALLOW_REMOTE=false",
                    "BROKER_HTTP_TIMEOUT_SECONDS=5",
                ]
            )
        elif broker_type == "tonghuashun":
            common.extend(
                [
                    "# 普通同花顺客户端只用于行情和人工提醒；自动下单必须连接券商授权的 SuperMind/执行桥。",
                    r"TONGHUASHUN_LAUNCHER_PATH=D:\path\to\hexinlauncher.exe",
                    "TONGHUASHUN_REMINDER_ENABLED=false",
                    "TONGHUASHUN_IFIND_ENABLED=false",
                    "BROKER_HTTP_URL=http://127.0.0.1:8765",
                    "BROKER_HTTP_TOKEN=",
                    "BROKER_HTTP_ALLOW_REMOTE=false",
                    "BROKER_HTTP_TIMEOUT_SECONDS=5",
                ]
            )
        return "\n".join(common)

    def _qmt_diagnostics(self, config: BrokerConfig) -> dict[str, Any]:
        path = Path(config.qmt_path).expanduser() if config.qmt_path else None
        path_exists = bool(path and path.is_dir())
        path_name = path.name.lower() if path else ""
        path_shape_ok = path_name in {"userdata", "userdata_mini"}
        sdk = _module_available("xtquant.xttrader") and _module_available("xtquant.xttype")
        py_supported = (3, 6) <= sys.version_info[:2] <= (3, 11)
        session_ok = str(config.qmt_session_id or "").isdigit() and int(config.qmt_session_id or 0) > 0
        missing: list[str] = []
        if not py_supported:
            missing.append(f"当前 Python {sys.version_info.major}.{sys.version_info.minor} 不在 QMT 文档列出的 3.6-3.11 范围。")
        if not sdk:
            missing.append("本机当前 Python 环境无法导入 xtquant。")
        if not path_exists:
            missing.append("QMT_PATH 未配置为存在的 userdata_mini/userdata 目录。")
        elif not path_shape_ok:
            missing.append("QMT_PATH 存在，但目录名不是 userdata_mini 或 userdata，请核对终端数据目录。")
        if not config.qmt_account_id:
            missing.append("QMT_ACCOUNT_ID 未配置。")
        if not session_ok:
            missing.append("QMT_SESSION_ID 必须是当前策略独占的正整数。")
        config_ready = py_supported and sdk and path_exists and path_shape_ok and bool(config.qmt_account_id) and session_ok
        return {
            "broker": "qmt",
            "status": "ready_to_test" if config_ready else "setup_required",
            "configuration_ready": config_ready,
            "ready_to_connect": config_ready and self._safety(config)["live_switches_enabled"],
            "sdk_available": sdk,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_supported": py_supported,
            "path_configured": bool(config.qmt_path),
            "path_exists": path_exists,
            "path_shape_ok": path_shape_ok,
            "account_configured": bool(config.qmt_account_id),
            "session_id_valid": session_ok,
            "missing_reasons": missing,
            "next_steps": [
                "在券商授权的 QMT/MiniQMT 中登录，并保持极简模式运行。",
                "把 QMT_PATH 指向该终端的 userdata_mini（研究端可能为 userdata）目录。",
                "在服务启动环境中配置账号类型和每个策略独占的会话号。",
                "先保持实盘开关关闭完成连接、账户、持仓和预检查验收，再由用户手工开启。",
            ],
        }

    def _ptrade_diagnostics(self, config: BrokerConfig) -> dict[str, Any]:
        explicit_module = bool(
            config.ptrade_client_factory
            or (config.ptrade_module and config.ptrade_module.strip().lower() not in {"", "ptrade"})
        )
        sdk = _module_available(config.ptrade_module) if explicit_module else False
        path_exists = bool(config.ptrade_path and Path(config.ptrade_path).expanduser().exists())
        custom_ready = explicit_module and sdk and bool(config.ptrade_account_id)
        missing = []
        if not explicit_module:
            missing.append("PTrade 通常是券商托管平台，没有统一可直接安装的本地 ptrade 模块。")
        elif not sdk:
            missing.append(f"无法导入券商指定模块 {config.ptrade_module}。")
        if explicit_module and not config.ptrade_account_id:
            missing.append("PTRADE_ACCOUNT_ID 未配置。")
        return {
            "broker": "ptrade",
            "status": "ready_to_test" if custom_ready else "broker_hosted_or_bridge_required",
            "deployment_model": "custom_local_module" if explicit_module else "broker_hosted",
            "configuration_ready": custom_ready,
            "ready_to_connect": custom_ready and self._safety(config)["live_switches_enabled"],
            "sdk_available": sdk,
            "path_configured": bool(config.ptrade_path),
            "path_exists": path_exists,
            "account_configured": bool(config.ptrade_account_id),
            "missing_reasons": missing,
            "next_steps": [
                "先向开户券商确认 PTrade 是否开放、运行环境、账号权限和接口版本。",
                "若策略只能在券商平台运行，应在平台侧部署受控执行端，并通过本地 HTTP 券商桥对接本系统。",
                "只有券商明确提供可导入模块和调用约定时，才配置 PTRADE_MODULE/PTRADE_CLIENT_FACTORY。",
            ],
        }

    def _http_bridge_diagnostics(self, config: BrokerConfig) -> dict[str, Any]:
        parsed = urlparse(config.http_bridge_url or "")
        scheme_ok = parsed.scheme in {"http", "https"}
        host = (parsed.hostname or "").lower()
        local_host = host in {"127.0.0.1", "localhost", "::1"}
        remote_allowed = bool(config.http_bridge_allow_remote)
        url_ok = bool(scheme_ok and host and (local_host or remote_allowed))
        token_ok = bool(config.http_bridge_token)
        missing = []
        if not url_ok:
            missing.append("BROKER_HTTP_URL 缺失，或远程地址未显式允许。")
        if not token_ok:
            missing.append("BROKER_HTTP_TOKEN 未配置。")
        ready = url_ok and token_ok
        return {
            "broker": "http_bridge",
            "status": "ready_to_test" if ready else "setup_required",
            "configuration_ready": ready,
            "ready_to_connect": ready and self._safety(config)["live_switches_enabled"],
            "url_configured": bool(config.http_bridge_url),
            "local_only": local_host and not remote_allowed,
            "token_configured": token_ok,
            "missing_reasons": missing,
            "next_steps": [
                "桥接服务应默认只监听 127.0.0.1，并使用独立随机令牌。",
                "先用健康检查、只读账户和持仓接口验收，再允许订单确认队列提交。",
            ],
        }

    def _tonghuashun_diagnostics(self, config: BrokerConfig) -> dict[str, Any]:
        bridge = self._http_bridge_diagnostics(config)
        ifind_sdk = _module_available("iFinDPy") or _module_available("iFinDAPI")
        launcher_text = str(os.environ.get("TONGHUASHUN_LAUNCHER_PATH") or "").strip()
        companion: dict[str, Any] = {}
        if self.companion_status_provider is not None:
            try:
                candidate = self.companion_status_provider()
                companion = candidate if isinstance(candidate, dict) else {}
            except Exception:
                companion = {}
        companion_launcher = str(companion.get("launcher_path") or "").strip()
        detected_launcher = launcher_text or companion_launcher
        launcher_exists = bool(detected_launcher and Path(detected_launcher).expanduser().is_file())
        order_app_exists = bool(companion.get("order_app_exists"))
        companion_enabled = bool(companion.get("enabled"))
        bridge_ready = bool(bridge.get("configuration_ready"))
        missing: list[str] = []
        if not bridge_ready:
            missing.append("未配置券商授权的 SuperMind/同花顺执行桥；普通桌面客户端不能作为自动下单接口。")
            missing.extend(str(item) for item in bridge.get("missing_reasons") or [])
        if not ifind_sdk:
            missing.append("当前 Python 环境未发现 iFinD SDK；这只影响授权行情/公告数据，不影响人工提醒。")
        if not launcher_exists:
            missing.append("环境变量中未发现有效同花顺启动器；也可在总控台的本地伴随区单独配置。")
        return {
            "broker": "tonghuashun",
            "status": "ready_to_test" if bridge_ready else ("data_or_companion_only" if ifind_sdk or launcher_exists else "setup_required"),
            "deployment_model": "authorized_supermind_or_broker_bridge",
            "configuration_ready": bridge_ready,
            "ready_to_connect": bridge_ready and self._safety(config)["live_switches_enabled"],
            "desktop_companion_available": launcher_exists,
            "desktop_companion_enabled": companion_enabled,
            "desktop_launcher_source": "environment" if launcher_text else ("local_companion" if companion_launcher else "missing"),
            "desktop_launcher_path": detected_launcher,
            "desktop_order_app_available": order_app_exists,
            "desktop_automatic_order": False,
            "ifind_sdk_available": ifind_sdk,
            "ifind_role": "授权数据源，不作为券商成交证明",
            "execution_bridge_configured": bridge_ready,
            "execution_identity_required": ["tonghuashun", "supermind", "ifind_supermind", "ths"],
            "missing_reasons": list(dict.fromkeys(missing)),
            "next_steps": [
                "普通同花顺客户端可继续用于行情查看和人工委托提醒，不做界面自动点击。",
                "如已购买 iFinD 数据权限，可安装官方 SDK 并在数据中心完成只读授权验收。",
                "自动交易需在券商授权的 SuperMind/托管环境部署执行端，通过本机受控桥接协议连接。",
                "先验收健康检查、只读账户、持仓、委托和成交查询，再由用户手工打开实盘开关。",
            ],
        }

    @staticmethod
    def _safety(config: BrokerConfig) -> dict[str, Any]:
        switches = bool(config.feature_live_broker and config.live_trading_enabled)
        return {
            "feature_live_broker": config.feature_live_broker,
            "live_trading_enabled": config.live_trading_enabled,
            "order_confirm_required": config.order_confirm_required,
            "kill_switch": config.live_kill_switch,
            "whitelist_count": len(config.trade_whitelist_symbols),
            "live_switches_enabled": switches,
            "safe_defaults_preserved": bool(
                config.order_confirm_required
                and (not switches or config.live_kill_switch or config.trade_whitelist_symbols)
            ),
        }

    @staticmethod
    def _capabilities(broker_type: str, diagnostic: dict[str, Any]) -> dict[str, str]:
        """Expose truthful onboarding capabilities without claiming a live connection."""

        configured = bool(diagnostic.get("configuration_ready"))
        sdk_available = bool(diagnostic.get("sdk_available"))
        execution = "待连接验收" if configured else "需配置授权环境"
        if broker_type == "qmt":
            readonly = "待连接验收" if sdk_available else "当前不可用"
            return {
                "行情/数据": "由网关真实行情源提供",
                "账户资金": readonly,
                "持仓同步": readonly,
                "委托/成交查询": readonly,
                "自动委托": execution,
                "撤单": execution,
                "人工确认": "强制保留",
            }
        if broker_type == "ptrade":
            readonly = "券商环境决定" if not configured else "待连接验收"
            return {
                "行情/数据": "由网关或券商授权源提供",
                "账户资金": readonly,
                "持仓同步": readonly,
                "委托/成交查询": readonly,
                "自动委托": execution,
                "撤单": execution,
                "人工确认": "强制保留",
            }
        if broker_type == "tonghuashun":
            bridge = bool(diagnostic.get("execution_bridge_configured"))
            companion = bool(diagnostic.get("desktop_companion_available"))
            ifind = bool(diagnostic.get("ifind_sdk_available"))
            trade_state = "待授权桥连接验收" if bridge else "普通客户端仅人工提醒"
            return {
                "行情/数据": "iFinD 待授权验收" if ifind else "使用网关真实来源",
                "客户端唤起": "可用（不自动点击）" if companion else "未配置",
                "账户资金": trade_state,
                "持仓同步": trade_state,
                "委托/成交查询": trade_state,
                "自动委托": trade_state,
                "撤单": trade_state,
                "人工确认": "强制保留",
            }
        return {
            "行情/数据": "由网关或桥接端提供",
            "账户资金": execution,
            "持仓同步": execution,
            "委托/成交查询": execution,
            "自动委托": execution,
            "撤单": execution,
            "人工确认": "强制保留",
        }


def _module_available(module_name: str) -> bool:
    name = str(module_name or "").strip()
    if not name:
        return False
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False
