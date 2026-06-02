# V3.21 Realtime Paper Trading Design

实时模拟交易模块位于 `quant_data/trading/realtime_paper_engine.py`，页面入口是 `/realtime-paper`。它用于自动交易前验证策略，不连接真实券商。

## 闭环

1. 读取实时 quote、分时、技术因子、信息快照、市场环境和当前持仓。
2. `DataFreshnessGuard` 检查行情、分时、新闻、技术因子和公司资料是否过期。
3. `AnomalyGuard` 检查高位放量滞涨、假突破、跌破 MA20/VWAP、尾盘砸盘、信息面负面等异常。
4. `SignalFusionEngine` 生成 `UnifiedSignal`，动态融合基本面、技术面、信息面和市场环境。
5. `PositionSizer` 计算目标仓位。
6. `OrderManager` 生成 paper order。
7. `RiskGateway` 在订单前做最终审批。
8. `PaperAccount` 模拟成交、更新现金、持仓、成本和盈亏。
9. engine 写入信号、订单、成交、拒单和风险原因到 audit log。

## 运行规则

- 非交易时段不自动交易，只允许手动 tick 或历史分时回放。
- stale 数据不得自动下单，必须刷新或降权。
- 信息面正在抓取时可以使用最近快照，但必须标注 stale。
- 每个信号必须带证据；每个拒单必须带原因。
- `paper_only=true` 是强制约束，所有接口都不得调用真实券商。

## API

- `POST /api/realtime-paper/start`
- `POST /api/realtime-paper/stop`
- `GET /api/realtime-paper/status`
- `GET /api/realtime-paper/portfolio`
- `GET /api/realtime-paper/orders`
- `GET /api/realtime-paper/signals`
- `GET /api/realtime-paper/audit`
- `POST /api/realtime-paper/tick`
- `POST /api/realtime-paper/replay`

## 筛选系统接入

`/screener` 可以把当前筛选结果加入实时模拟池，也可以用当前策略启动盘中模拟。无日期的当前筛选快照不能回填历史，只能从当前时点开始 paper trading，并且每个订单仍会再次经过 `RiskGateway`。
