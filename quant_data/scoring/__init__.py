"""V3.23 unified scoring and signal fusion."""

from .factor_engine import V323FactorEngine
from .extension_factors import ExtensionFactorResult, V324ExtensionFactorEngine
from .score_explain import explain_score
from .score_models import (
    FactorContribution,
    ScoreGate,
    ScoreProvenanceV323,
    ScoreRequest,
)
from .score_policy import ScorePolicyV323
from .score_provenance import ScoreProvenanceEngine, build_score_provenance_v323
from .signal_fusion import SignalFusionV323, TradeSignalV323

__all__ = [
    "FactorContribution",
    "ExtensionFactorResult",
    "ScoreGate",
    "ScorePolicyV323",
    "ScoreProvenanceEngine",
    "ScoreProvenanceV323",
    "ScoreRequest",
    "SignalFusionV323",
    "TradeSignalV323",
    "V323FactorEngine",
    "V324ExtensionFactorEngine",
    "build_score_provenance_v323",
    "explain_score",
]
