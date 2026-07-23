from quant_data.trading.broker import load_broker_config


def test_trade_whitelist_accepts_chinese_and_ascii_separators():
    config = load_broker_config(
        {
            "TRADE_WHITELIST_SYMBOLS": "300750，600438；510300、000001;159915",
        }
    )

    assert config.trade_whitelist_symbols == ["300750", "600438", "510300", "000001", "159915"]
