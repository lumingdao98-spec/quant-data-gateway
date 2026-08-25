# V3.21 Money Management Design

资金管理模块位于 `quant_data/backtest/position_sizing.py` 和 `quant_data/backtest/money_management.py`。

## 账户字段

- `initial_cash`: 初始资金。
- `cash`: 当前现金。
- `market_value`: 持仓市值。
- `equity`: 总权益，等于现金加持仓市值。
- `realized_pnl`: 已实现盈亏。
- `unrealized_pnl`: 浮动盈亏。
- `available_cash`: 可用资金，扣除冻结和预留。
- `frozen_cash`: 已冻结资金。
- `reserved_cash`: 风险预留现金。
- `reinvestable_cash`: 可再投资资金；复利开启时跟随权益变化，关闭时以初始资金为基准。

## 仓位模式

- `fixed_percent`: 按总权益固定比例买入。
- `equal_weight`: 按目标持仓数量等权分配。
- `score_weighted`: 综合评分越高目标权重越高，同时受单票上限限制。
- `volatility_target`: 波动率越高仓位越低。
- `atr_risk`: 按 ATR 或止损距离反推股数，控制单笔最大亏损。
- `fixed_risk_per_trade`: 每笔固定风险预算。
- `fractional_kelly`: 使用胜率和赔率估算分数凯利，并强制上限。
- `pyramid`: 只在盈利且趋势确认时小比例加仓，不允许亏损加仓。
- `dca`: 固定周期和金额定投，适合 ETF 或指定长期标的。
- `core_satellite`: 核心仓低频持有，卫星仓使用短线评分信号。

## 复利与不复利

- `compound_returns=true`: 调仓基准使用最新 equity，盈利可进入下一次仓位计算。
- `compound_returns=false`: 调仓基准固定为 initial_cash，多出的盈利只作为现金留存。
- 每次买卖都会写入 ledger，记录日期、动作、现金变动、权益变动、费用、滑点和原因。

## 风险约束

仓位计算结果必须再经过总仓位上限、单票上限、行业上限、现金预留、最小成交额、100 股手数、连续亏损降仓等约束。仓位模块只给建议，真实下单前仍必须经过 `RiskGateway`。
