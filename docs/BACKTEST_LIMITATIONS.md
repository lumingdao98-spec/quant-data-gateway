# V3.19 Backtest Limitations

- This is a research tool, not investment advice: `研究辅助，不构成投资建议`.
- The engine prevents obvious lookahead by using T-day signals and T+1 execution, but upstream datasets can still contain survivorship or restatement bias.
- Corporate actions and qfq/hfq/none choices are tracked as config, but provider-level adjustment errors can still affect results.
- A-share execution is approximate: T+1, lots, limits, suspended days, costs, slippage and volume caps are modeled, but queue priority, auction matching and broker-specific behavior are not.
- Benchmark support is present in metrics fields, but V3.19 does not yet auto-download and align multiple index curves for every run.
- Screener snapshot integration is supported through adapter inputs and snapshot ids; long-term score history quality depends on saved snapshots.
- Optimizer and walk-forward APIs are foundational. They reduce overfitting risk but cannot eliminate it.
- Paper trading is virtual and deliberately has no real broker connection.
