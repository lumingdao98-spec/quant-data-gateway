# V3.23 Order Lifecycle

Unified order statuses:

- `signal_created`
- `prechecked`
- `risk_blocked`
- `needs_confirmation`
- `confirmed`
- `submitted`
- `accepted`
- `partially_filled`
- `filled`
- `cancel_requested`
- `cancelled`
- `rejected`
- `expired`
- `failed`
- `unknown`
- `reconciled`

Backtest orders route to the historical execution simulator. Paper orders route to the paper engine. Live orders route to `ExecutionRouter`, then a broker adapter only after precheck and confirmation.
