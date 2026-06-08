from __future__ import annotations

from typing import Any

from quant_data.backtest.position_sizing import PositionSizingConfig, PositionSizingDecision, size_position


class PositionSizingEngine:
    """Unified V3.23 wrapper around the existing tested position sizer."""

    def size(
        self,
        signal: Any,
        portfolio: Any,
        risk_budget: Any,
        security_master: Any,
        latest_bar: Any,
        sizing_policy: PositionSizingConfig | dict[str, Any] | None = None,
    ) -> PositionSizingDecision:
        return size_position(signal, portfolio, risk_budget, security_master, latest_bar, sizing_policy)
