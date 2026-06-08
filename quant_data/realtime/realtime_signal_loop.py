from __future__ import annotations

from typing import Any

from quant_data.scoring import ScoreRequest, SignalFusionV323, build_score_provenance_v323


class RealtimeSignalLoop:
    def run_once(self, symbol: str, factor_values: dict[str, Any], *, data_sources: list[dict[str, Any]], decision_time: str, strategy_family: str = "hybrid") -> dict[str, Any]:
        provenance = build_score_provenance_v323(
            ScoreRequest(
                symbol=symbol,
                decision_time=decision_time,
                mode="realtime_paper",
                strategy_family=strategy_family,
                factor_values=factor_values,
                data_sources=data_sources,
            )
        )
        signal = SignalFusionV323().fuse(provenance)
        return {"provenance": provenance.to_dict(), "signal": signal.to_dict()}
