from quant_data.utils import normalize_symbol, to_eastmoney_secid, to_sina_code


def test_symbol_helpers():
    assert normalize_symbol("300750") == "300750"
    assert normalize_symbol("sz300750") == "300750"
    assert to_eastmoney_secid("600519") == "1.600519"
    assert to_eastmoney_secid("300750") == "0.300750"
    assert to_sina_code("600519") == "sh600519"
    assert to_sina_code("300750") == "sz300750"
