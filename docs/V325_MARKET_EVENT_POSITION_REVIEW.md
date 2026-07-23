# V3.25 市场事件与持仓复核

## 目标

本轮在不修改稳定评分权重、评分溯源模型和既有策略映射的前提下，补充两项共享能力：可追溯市场事件因子，以及模拟/实盘持仓的每日复核。

## 市场事件因子

`MarketEventFactorService` 只读取全局要闻和板块资金缓存，不主动联网，也不补造缺失字段。事件必须有可用时间；未来事件、无日期事件和过期事件不会进入评分。

事件分为两类：

- 市场环境：海外科技风险、海外流动性、大额 IPO 资金占用等，只调整大盘环境分。
- 个股信息：只有公司主营、行业或产业链与事件的结构化映射明确重合时，才有限调整个股信息分。

每个因子保存中文名称、调整分、影响范围、来源、来源链接、发布时间、置信度、传导链和解释。事件调整有上下限，不是买卖指令。

## 持仓复核

`PositionReviewService` 复用统一信号融合内核，保存：

- 持仓数量、可卖数量、平均成本、现价和市值；
- 已实现/未实现盈亏相关字段；
- 当前评分、上次评分和变化；
- 持有、减仓、退出或人工复核建议；
- 止损、分批止盈、重大负面和数据新鲜度原因；
- 市场事件上下文、近期信息与缺失字段。

无五档盘口只作为提示，不阻断日线持仓复核。行情、关键 K 线、近期信息缺失或数据过期时，复核转为人工处理。

## 执行边界

- 模拟持仓复核接口本身不创建订单；真实订单仍由实时模拟循环和风控网关产生。
- 实盘持仓复核永不调用券商，`execution_allowed=false` 且 `broker_submitted=false`。
- 实盘减仓/退出建议必须重新经过风控、确认队列和 BrokerAdapter。
- QMT/PTrade 未安装、未登录或未授权时，只保留预检查和待确认票据，不标记真实成交。

## API

- `GET /api/market/event-factors/{symbol}`
- `POST /api/realtime-paper/sessions/{session_id}/review-positions`
- `GET /api/realtime-paper/sessions/{session_id}/position-reviews`
- `POST /api/live/review-positions`
- `GET /api/live/position-reviews`

研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。
