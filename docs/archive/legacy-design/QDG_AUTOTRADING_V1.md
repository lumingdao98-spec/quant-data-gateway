# QDG 自动交易研究版 V1

本文档描述 V3.22 当前实现范围。系统只做研究、回测和纸面模拟，不连接真实券商，不自动真实下单。

## 总体链路

1. 研究层：`quant_data/research/` 负责大盘状态、个股分类和策略适配。
2. 因子层：`quant_data/factors/` 负责技术/量价因子、评分溯源、信号融合和异常防护。
3. 回测层：`quant_data/backtest/` 负责历史快照、交易规则、仓位、资金、退出和撮合。
4. 纸面交易层：`quant_data/trading/` 负责实时纸面账户、风险网关、审计日志和人工确认队列。
5. API/页面层：`quant_data/api.py` 暴露中文文档、规则配置、V3.22 readiness、历史快照和纸面确认接口。

## 关键接口

- `GET /docs-cn`：中文 API 总览和参数解释。
- `GET /docs`：Swagger 调试页，可直接填写参数。
- `GET /api/backtest/v322/readiness`：V3.22 能力状态。
- `GET /api/market-rules/profiles`：交易规则配置和按标的解析结果。
- `GET /api/screener/historical-snapshot`：按决策时点重建筛选快照。
- `GET /api/realtime-paper/confirmations`：查看待人工确认的纸面交易。

## 交易边界

- 默认使用信号日生成、下一交易日执行，避免收盘后才知道的信号当日成交。
- A 股 T+1、涨跌停、买入整手、卖出零股、停牌和成交量上限进入撮合。
- 交易规则来自 `config/market_rules/a_share_rules.yaml`，执行层不再直接硬编码板块前缀。
- 人工确认队列只改变纸面状态，不触发真实委托。

## 后续路线

- 将更多历史公告、财务和大盘指数快照并入 PIT 快照。
- 为 `/realtime-paper` 页面增加人工确认处理动作。
- 把回测评分溯源和盘中纸面信号统一到同一个 provenance 报告视图。
