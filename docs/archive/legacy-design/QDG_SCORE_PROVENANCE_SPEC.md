# QDG 评分溯源规范

V3.22 的评分不再只是一个最终分数，必须同时返回为什么得到这个分数，以及哪些数据在决策时点可见。

## 100 分口径

默认回测口径使用基础分 50 分，加上因子贡献，再扣除风险门禁：

```text
final_score = clip(base_score + sum(factor_contribution) - sum(gate_penalty), 0, 100)
```

贡献由 `FactorValue.normalized_value` 和策略权重决定。`available_at` 晚于 `asof_time` 的因子会被剔除，且 `no_lookahead=false`、`coverage_pct` 下降。

## 核心字段

- `score_provenance_id`：本次溯源记录 ID。
- `symbol`：标的代码。
- `decision_time`：策略产生判断的时间。
- `asof_time`：数据允许可见的截止时间。
- `strategy_family`：适配后的策略族。
- `final_score`：0-100 最终评分。
- `contributions`：每个因子的原始值、标准化值、权重、贡献和数据来源。
- `gates`：停牌、ST、数据过期、重大事件等门禁结果。
- `policy_version_hash`：评分策略版本 hash。
- `source_refs`：参与评分的数据来源引用。
- `no_lookahead`：是否没有使用未来数据。
- `coverage_pct`：可用因子覆盖率。

## 代码入口

- `quant_data/factors/score_provenance.py`
- `quant_data/factors/factor_engine.py`
- `quant_data/backtest/provenance_report.py`
- `BacktestResult.score_provenance`

## 测试

- `tests/backtest/test_v322_score_provenance.py`
- `tests/api/test_v322_api.py`
