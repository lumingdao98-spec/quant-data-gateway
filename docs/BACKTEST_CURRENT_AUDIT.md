# V3.19 Backtest Current Audit

Date: 2026-06-01

## Conclusion

The pre-V3.19 backtest implementation is useful as a visual single-symbol replay, but it is not yet a complete research backtest system. It mixes strategy scoring, execution, chart payloads and metrics in `quant_data/services/backtest_service.py`, so the UI can show buy/sell marks, but the architecture cannot reliably answer portfolio-level questions such as A-share execution constraints, no-lookahead data lineage, parameter optimization, walk-forward validation or paper-trading handoff.

V3.19 adds a separated foundation under `quant_data/backtest/` while keeping the existing GET `/api/backtest/run` compatibility route intact.

## Existing Surface

| Area | Current files | Status | Gap |
| --- | --- | --- | --- |
| Backtest UI | `quant_data/backtest_ui.py` | Present | Tied to legacy single-symbol API; not a typed engine contract. |
| Legacy service | `quant_data/services/backtest_service.py` | Present | Single-symbol daily replay; execution, scoring and reporting are bundled together. |
| API | `quant_data/api.py` | Present | Existing GET route preserved; V3.19 needs POST run/result/history/export/optimize/walk-forward/paper routes. |
| Tests | `tests/test_backtest_service.py`, `tests/test_backtest_api.py` | Present | Covers legacy UI/API smoke and markers; lacks core execution, no-lookahead, optimizer and storage tests. |
| Screener integration | `quant_data/services/screener_service.py` and UI localStorage | Partial | Needs explicit snapshot-to-signal adapter and traceable snapshot id. |
| Paper trading | None dedicated | Missing | Needs a virtual broker that never connects to a real broker. |

## Risk Notes

- Legacy score-driven backtest uses visible daily K-line fields only, but the code did not provide a reusable proof boundary for no-lookahead checks.
- Costs existed as fee/slippage inputs, but A-share details such as stamp tax, transfer fee, 100-share lots, T+1 availability, limit up/down blocking and volume caps were not isolated.
- Metrics existed for headline return/risk, but optimizer and walk-forward workflows were absent.
- UI detail and chart needs should remain backward compatible; V3.19 therefore adds a new engine beside the old route instead of removing it.

## V3.19 Audit Decision

Keep the legacy route for the current pages and add a typed backtest package:

- `models.py`: stable dataclasses and result schema.
- `data_loader.py`: data quality and no-lookahead checks.
- `signal_adapter.py`: screener/factor/event signals.
- `execution.py`: A-share execution model.
- `portfolio.py`: portfolio state and sizing.
- `risk.py`: metrics and safe math.
- `engine.py`: daily engine using signal date then next execution date.
- `optimizer.py`, `walk_forward.py`: parameter and sample-out validation.
- `storage.py`, `report.py`: persisted runs and reports.
- `paper_broker.py`: paper-trading bridge with no real broker integration.

Every V3.19 output must carry `研究辅助，不构成投资建议`.
