from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Literal





def _safe_num(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _format_volume_hand(value) -> str:
    v = _safe_num(value)
    if v is None or v <= 0:
        return "--"
    if abs(v) >= 100000000:
        return f"{v / 100000000:.2f}亿手"
    if abs(v) >= 10000:
        return f"{v / 10000:.2f}万手"
    return f"{v:.0f}手"


def _format_amount_yuan(value) -> str:
    v = _safe_num(value)
    if v is None or v == 0:
        return "--"
    if abs(v) >= 1000000000000:
        return f"{v / 1000000000000:.2f}万亿"
    if abs(v) >= 100000000:
        return f"{v / 100000000:.2f}亿"
    if abs(v) >= 10000:
        return f"{v / 10000:.2f}万"
    return f"{v:.0f}元"


def _append_market_display_fields(data: dict, volume, amount) -> dict:
    """A股公开源统一约定：volume 按“手”保存，amount 按“元”保存。"""
    volume_hand = _safe_num(volume)
    amount_yuan = _safe_num(amount)
    data["volume_unit"] = "手"
    data["amount_unit"] = "元"
    data["volume_hand"] = volume_hand
    data["volume_shares"] = volume_hand * 100.0 if volume_hand is not None else None
    data["volume_display"] = _format_volume_hand(volume_hand)
    data["amount_yuan"] = amount_yuan
    data["amount_display"] = _format_amount_yuan(amount_yuan)
    return data


class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    FUND = "fund"
    INDEX = "index"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Quote:
    """实时行情快照。

    说明：
    - volume 通常为“手”，amount 为“元”；不同源可能略有差异，已尽量统一。
    - ts 是本地获取时间，不等于交易所原始撮合时间。
    """

    symbol: str
    name: str
    ts: datetime
    last: float
    pre_close: float
    open: float
    high: float
    low: float
    volume: float
    amount: float
    change: float
    change_pct: float
    turnover: float | None = None
    amplitude: float | None = None
    pe_dynamic: float | None = None
    pb: float | None = None
    volume_ratio: float | None = None      # 量比
    total_market_cap: float | None = None  # 总市值，元
    float_market_cap: float | None = None  # 流通市值，元
    circulating_market_cap: float | None = None  # 流通市值别名，兼容前端/量化字段
    total_share: float | None = None       # 总股本，股
    float_share: float | None = None       # 流通股本，股
    metric_missing_reasons: list[str] | None = None
    market_cap_style: str | None = None
    metric_sources: dict | None = None
    order_ratio: float | None = None       # 委比，当前公开源可能为空
    order_diff: float | None = None        # 委差，当前公开源可能为空
    market: str = "CN"
    asset_type: AssetType = AssetType.STOCK
    source: str = "unknown"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["ts"] = self.ts.isoformat(timespec="seconds")
        data["asset_type"] = self.asset_type.value
        return _append_market_display_fields(data, self.volume, self.amount)


@dataclass(frozen=True)
class Bar:
    symbol: str
    frame: Literal["1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M"]
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    turnover: float | None = None
    change_pct: float | None = None
    source: str = "unknown"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["ts"] = self.ts.isoformat(timespec="seconds")
        return _append_market_display_fields(data, self.volume, self.amount)


@dataclass(frozen=True)
class IntradayPoint:
    """当日分时点。

    price: 最新成交价/分时价；avg_price: 均价线；volume 通常为手；amount 为元。
    """

    symbol: str
    ts: datetime
    price: float
    avg_price: float | None = None
    volume: float | None = None
    amount: float | None = None
    source: str = "unknown"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["ts"] = self.ts.isoformat(timespec="seconds")
        return _append_market_display_fields(data, self.volume, self.amount)


@dataclass(frozen=True)
class Asset:
    symbol: str
    name: str
    asset_type: AssetType = AssetType.STOCK
    market: str = "CN"
    exchange: str = ""
    source: str = "unknown"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["asset_type"] = self.asset_type.value
        return data

@dataclass(frozen=True)
class OrderBookLevel:
    price: float | None = None
    volume: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class OrderBook:
    symbol: str
    ts: datetime
    asks: list[OrderBookLevel]
    bids: list[OrderBookLevel]
    order_ratio: float | None = None
    order_diff: float | None = None
    source: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "ts": self.ts.isoformat(timespec="seconds"),
            "asks": [x.to_dict() for x in self.asks],
            "bids": [x.to_dict() for x in self.bids],
            "order_ratio": self.order_ratio,
            "order_diff": self.order_diff,
            "source": self.source,
        }
