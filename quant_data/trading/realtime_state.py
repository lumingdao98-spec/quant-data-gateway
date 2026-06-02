from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class RealtimePaperConfig:
    symbols: list[str] = field(default_factory=list)
    interval_seconds: int = 15
    horizon: str = "intraday_paper"
    initial_cash: float = 100_000.0
    strategy: str = "three_dimension_score"
    allow_manual_replay: bool = True
    paper_only: bool = True
    fee_rate: float = 0.0003
    slippage_rate: float = 0.0005

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RealtimePaperState:
    status: str = "stopped"
    started_at: str | None = None
    stopped_at: str | None = None
    last_tick_at: str | None = None
    tick_count: int = 0
    is_trading_session: bool = False
    freshness_status: str = "--"
    message: str = "未启动"
    config: RealtimePaperConfig = field(default_factory=RealtimePaperConfig)

    def start(self, config: RealtimePaperConfig) -> None:
        self.status = "running"
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.stopped_at = None
        self.message = "实时模拟运行中"
        self.config = config

    def stop(self) -> None:
        self.status = "stopped"
        self.stopped_at = datetime.now().isoformat(timespec="seconds")
        self.message = "已停止"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["config"] = self.config.to_dict()
        return data
