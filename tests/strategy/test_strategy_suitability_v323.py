from quant_data.strategy import StockClassifierV323, StrategySuitabilityV323


def test_strategy_suitability_avoids_data_poor_names():
    profile = StockClassifierV323().classify("300750", {"roe": 15, "net_profit_growth": 20})

    decision = StrategySuitabilityV323().evaluate(profile, score=70, data_quality_score=30)

    assert decision.strategy_family == "avoid"
    assert decision.can_auto_trade is False
