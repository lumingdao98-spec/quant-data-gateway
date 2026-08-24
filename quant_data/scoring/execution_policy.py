from __future__ import annotations


EXECUTION_SCORE_WEIGHTS = {
    "fundamental": 0.22,
    "technical": 0.30,
    "information": 0.20,
    "fund_flow": 0.16,
    "market": 0.12,
}

EXECUTION_SCORE_THRESHOLDS = {
    "buy": 62.0,
    "add": 72.0,
    "reduce_or_sell": 45.0,
}

