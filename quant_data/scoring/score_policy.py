from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any


@dataclass(slots=True)
class ScorePolicyV323:
    policy_version: str = "v3.28-execution-aligned"
    dimension_weights: dict[str, float] = field(
        default_factory=lambda: {
            "fundamental_score": 0.22,
            "technical_score": 0.30,
            "information_score": 0.20,
            "fund_flow_score": 0.16,
            "market_regime_score": 0.12,
            "behavior_risk_score": -0.10,
            # Data quality is a gate, not an alpha source. Keeping the
            # dimension at zero weight preserves provenance compatibility.
            "data_quality_score": 0.0,
        }
    )
    buy_threshold: float = 62.0
    sell_threshold: float = 48.0
    minimum_data_quality_for_new_position: float = 45.0
    stale_buy_block: bool = True
    live_requires_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def policy_hash(self) -> str:
        return sha256(repr(sorted(self.to_dict().items())).encode("utf-8")).hexdigest()[:16]
