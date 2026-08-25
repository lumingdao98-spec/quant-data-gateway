# QDG PIT 数据要求

PIT 是 point-in-time，表示回测只能使用决策时间之前已经可见的数据。

## 当前实现

- `HistoricalScreenerSnapshotBuilder.build_historical_snapshot()` 会按 `trade_date` 和 `decision_time` 截断 K 线。
- 快照返回 `snapshot_id`、`immutable_hash`、`asof_time`、`source_refs` 和 `pit_note`。
- 回测信号使用 `signal_date` 生成，并在下一交易日撮合。
- 评分溯源会检查 `FactorValue.available_at <= asof_time`。

## 缺失数据处理

- 未指定的财务、公告、资金流和新闻数据按缺失处理，不用未来数据回填。
- 缺失不会默认变成利好或利空，只会降低覆盖率或进入风险提示。
- 页面可以展示缓存快照，但回测不能把未来缓存混入过去决策。

## 新接口

```text
GET /api/screener/historical-snapshot?symbols=300750,600438&trade_date=2026-03-10&decision_time=2026-03-10 15:05:00
```

## 测试

- `tests/backtest/test_v322_snapshot_suitability.py`
- `tests/api/test_v322_api.py`
