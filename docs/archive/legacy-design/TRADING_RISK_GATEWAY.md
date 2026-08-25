# V3.21 Trading Risk Gateway

`RiskGateway` 是 paper/live 订单前的统一风控入口。当前只用于 paper trading，不允许真实下单。

## 输入

- 订单：symbol、side、quantity、price、order_type、target_weight、reason。
- 账户：cash、equity、positions、daily_pnl、trade_count_today、win/loss streak。
- 市场：交易时段、涨跌停、流动性、是否 ST、是否黑名单、行业暴露。
- 数据状态：quote/intraday/news/technical 是否 stale。
- 信号状态：异常标签、信息 veto、人工确认要求。

## 规则

- 最大总仓位、最大单票仓位、最大行业仓位。
- 最大单笔亏损、最大单日亏损、最大连续亏损。
- 最大日内交易次数、最大换手率。
- 禁止 ST、黑名单、低流动性、stale 数据、非交易时段自动下单。
- 禁止涨停追买和跌停卖出。
- 异常波动、信息面重大负面和大额订单需要人工确认或直接 veto。

## 输出

- `approved`: 是否通过。
- `decision`: `allow`、`reject`、`manual_confirm`、`reduce` 等。
- `adjusted_order`: 调整后的订单。
- `risk_reasons`: 风控原因列表。
- `required_confirm`: 是否需要人工确认。
- `risk_snapshot`: 风控快照，便于复盘。

## 设计原则

评分只负责产生研究信号，风控网关负责决定订单是否允许进入模拟成交。即使筛选评分很高，只要数据过期、异常波动严重、信息面 veto 或仓位超限，订单也必须被阻断。
