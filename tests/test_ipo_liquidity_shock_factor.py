from quant_data.scoring.extension_factors import V324ExtensionFactorEngine


def test_ipo_liquidity_shock_is_optional_and_never_fabricated():
    missing = V324ExtensionFactorEngine().compute()
    present = V324ExtensionFactorEngine().compute(ipo={"liquidity_shock_score": 72})

    assert "ipo_liquidity_shock" not in missing.values
    assert "ipo_liquidity_shock 数据缺失" in missing.missing_data
    assert present.values["ipo_liquidity_shock"] == 72
