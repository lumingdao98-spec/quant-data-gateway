# V3.24 实盘同步、PIT 事件与统一账本

## 目标与边界

V3.24 基于 `feature/v3.23-full-auto-trading-core`，补齐多股票实盘预检查、券商账户同步、统一策略族、规范化账本以及新闻/财报/IPO 的 point-in-time 查询。既有评分映射文件 `score_policy.py`、`score_provenance.py`、`score_models.py` 未重写；扩展事件因子只作为可选上下文和门禁证据。

真实交易仍默认关闭。未安装 SDK、未配置环境变量、未授权账户、未通过风控或未人工确认时，系统只返回 `disabled`、`unsupported`、`risk_blocked` 或 `needs_confirmation`，不会伪造连接、余额、订单或成交。

## 统一交易流程

回测、实时模拟和真实交易共用以下约束：

1. 策略族规范化为 `short`、`swing`、`position`、`dca`、`core_satellite`、`event_driven`、`avoid`。
2. 每个执行配置保存 `strategy_family`、`strategy_profile_hash`、`policy_hash` 和 `execution_profile_version`。
3. 订单经过统一状态机：`created -> prechecked -> needs_confirmation -> submitted -> accepted -> partially_filled -> filled/cancelled/rejected`。
4. 成交进入统一账本，并按 FIFO 更新 `position_lots`。
5. 订单、成交、撤单、拒单、确认和风控拦截生成图表 marker。

三种模式保持隔离：

- `backtest` 使用历史 K 线与决策时点可得快照，不连接实时行情或券商。
- `realtime_paper` 使用真实输入进行本地模拟撮合，休市和 stale 数据不自动下单。
- `live` 通过 BrokerAdapter 路由，必须经过实盘开关、数据新鲜度、白名单、风控和人工确认。

## 多股票实盘与券商同步

`LiveTradingEngine.preview_orders_batch()` 和 `place_orders_batch()` 对每个股票独立执行预检查、确认与审计。单个失败不会伪造成整批成功。

`LiveSyncService.sync_live_account_state()` 一次同步：

- account / cash；
- positions；
- orders；
- trades；
- fills、ledger 和 chart markers。

QMT 和 PTrade 适配器实现连接、账户、资金、持仓、委托、成交、下单、撤单和查询接口。SDK 不存在时返回 `unsupported`，导入错误不会使 API 服务崩溃。

## 规范化数据库表

保留原 JSON payload 表，并增加：

- `ledger_entries`：买入、卖出、佣金、税费、滑点、已实现盈亏等独立流水；
- `broker_accounts`：账户资金、权益、已实现/浮动盈亏和授权状态；
- `broker_positions`：券商持仓快照；
- `broker_orders`：券商委托快照；
- `broker_trades`：券商成交回报；
- `account_equity_curve`：回测、模拟、实盘统一权益曲线；
- `position_lots`：FIFO 持仓批次、剩余数量和成本。

回测成交也写入同一账本、持仓批次、账户快照和权益曲线，因此 `/trading-records` 可以跨模式查询，而不是只展示实盘数据。

## PIT 数据规则

新闻、财报、IPO 和通用事件统一使用 `available_at`。任何 as-of 查询都必须满足：

```text
available_at <= decision_time
```

`published_at` 不是可交易时间的替代字段；缺少可验证时间或来源时返回 missing/rejected，不回填未来信息。Jin10 仅作为快讯补充，交易所、巨潮、公司 filing 和官方宏观源优先；Reuters/Bloomberg 只有在本地存在授权接入时才可使用。

事件扩展因子包括：

- `macro_liquidity_stress`
- `global_semis_drawdown`
- `ipo_liquidity_shock`
- `earnings_surprise`
- `guidance_delta`
- `northbound_flow_regime`
- `sector_sentiment_velocity`
- `competitor_listing_pressure`

它们携带来源、`available_at`、置信度和解释，不修改既有评分权重映射。

## API 变更

实盘与记录：

- `POST /api/live/orders/preview-batch`
- `POST /api/live/orders/place-batch`
- `GET /api/live/account`
- `GET /api/live/positions`
- `GET /api/live/orders`
- `GET /api/live/trades`
- `GET /api/live/fills`
- `GET /api/live/ledger`
- `GET /api/live/account-snapshots`
- `GET /api/live/position-lots`
- `POST /api/live/reconciliation/run`
- `GET /api/trading-records/ledger`
- `GET /api/trading-records/account-snapshots`
- `GET /api/trading-records/fills`
- `GET /api/trading-records/position-lots`

事件与 PIT：

- `GET /api/events/replay`
- `GET /api/news/asof`
- `GET /api/earnings/asof`
- `GET /api/ipo/asof`
- `GET /api/events/triggers/live`
- `POST /api/events/triggers/evaluate`

## 页面

- `/auto-trading`：V3.24 总控台；
- `/live-trading`：多股票观察池、实盘策略目录、批量预检、确认队列、账户、持仓、成交、账本和对账；
- `/realtime-paper`：会话 ID、刷新频率、最后行情/决策、数据新鲜度、事件数和人工确认；
- `/trading-records`：订单成交、统一账本、持仓批次和账户快照。

## 安全开关

默认配置：

```text
FEATURE_LIVE_BROKER=false
LIVE_TRADING_ENABLED=false
ORDER_CONFIRM_REQUIRED=true
LIVE_KILL_SWITCH=false
```

真实下单必须同时满足：券商已连接且授权、实盘已启用、无 kill switch、交易时间有效、数据新鲜、评分溯源存在、风控通过、标的与金额符合限制、人工确认完成。

研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。
