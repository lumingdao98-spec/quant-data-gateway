from quant_data.persistence import TradingStore


def test_normalized_account_snapshot_and_equity_are_queryable(tmp_path):
    store = TradingStore(tmp_path / "account.sqlite")
    store.put_normalized("broker_accounts", {"snapshot_id": "a1", "session_id": "s1", "account_id": "acct", "cash": 80_000, "equity": 100_000, "market_value": 20_000, "available_cash": 80_000, "realized_pnl": 500, "unrealized_pnl": 1_000, "daily_pnl": 200, "max_drawdown": 0.03, "fetched_at": "2026-07-20T10:00:00"})
    store.put_normalized("account_equity_curve", {"point_id": "p1", "mode": "live", "session_id": "s1", "account_id": "acct", "equity": 100_000, "timestamp": "2026-07-20T10:00:00"})

    account = store.list_normalized("broker_accounts", session_id="s1")[0]
    curve = store.list_normalized("account_equity_curve", mode="live", session_id="s1")[0]
    assert account["equity"] == 100_000
    assert account["realized_pnl"] == 500
    assert curve["equity"] == 100_000
