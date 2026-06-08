from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any


@dataclass(slots=True)
class ScorePolicyV323:
    policy_version: str = "v3.23-default"
    dimension_weights: dict[str, float] = field(
        default_factory=lambda: {
            "fundamental_score": 0.20,
            "technical_score": 0.24,
            "information_score": 0.16,
            "fund_flow_score": 0.14,
            "market_regime_score": 0.12,
            "behavior_risk_score": -0.10,
            "data_quality_score": 0.14,
        }
    )
    buy_threshold: float = 62.0
    sell_threshold: float = 48.0
    stale_buy_block: bool = True
    live_requires_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def policy_hash(self) -> str:
        return sha256(repr(sorted(self.to_dict().items())).encode("utf-8")).hexdigest()[:16]
