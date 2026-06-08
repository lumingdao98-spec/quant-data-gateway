from quant_data.strategy import StockClassifierV323


def test_stock_classifier_identifies_etf_and_high_risk():
    classifier = StockClassifierV323()

    assert classifier.classify("510300").stock_type == "etf_index"
    assert classifier.classify("600001", {"name": "ST测试"}, {"is_st": True}).stock_type == "high_risk"
