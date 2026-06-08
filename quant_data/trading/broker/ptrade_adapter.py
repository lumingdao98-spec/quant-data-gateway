from __future__ import annotations

from .broker_config import BrokerConfig, load_broker_config
from .broker_models import BrokerConnectionStatus
from .disabled import DisabledBrokerAdapter


class PTradeBrokerAdapter(DisabledBrokerAdapter):
    def __init__(self, config: BrokerConfig | None = None) -> None:
        super().__init__(config or load_broker_config())
        self._supported = self._check_sdk()

    def _check_sdk(self) -> bool:
        try:
            __import__("ptrade")
            return True
        except Exception:
            return False

    def health_check(self) -> BrokerConnectionStatus:
        if not self._supported:
            return BrokerConnectionStatus(False, "unsupported", "ptrade", "本机未安装或不可导入 PTrade SDK，适配器降级为 unsupported。")
        if not (self.config.feature_live_broker and self.config.live_trading_enabled):
            return BrokerConnectionStatus(False, "disabled", "ptrade", "PTrade SDK 存在，但真实交易开关未开启。")
        if not self.config.ptrade_account_id:
            return BrokerConnectionStatus(False, "unauthorized", "ptrade", "PTRADE_ACCOUNT_ID 未配置。")
        return BrokerConnectionStatus(False, "not_connected", "ptrade", "PTrade 适配器已识别，但本轮不自动连接真实账户。")
