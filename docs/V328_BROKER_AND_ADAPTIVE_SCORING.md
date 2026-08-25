# V3.28 券商接入与自适应交易说明

## 1. 本轮范围

V3.28 不重写已经稳定的股票映射和三面评分口径，而是在统一交易内核上补齐以下能力：

- QMT、PTrade、同花顺授权桥和通用 HTTP 本地桥的接入诊断；
- 评分溯源、策略适配、数据新鲜度、风险检查、人工确认、券商路由、成交回写的完整链路；
- 短线、波段、长线、定投、核心卫星和事件驱动的差异化评分与仓位约束；
- 钉钉、飞书、企业微信和通用 Webhook 的移动端提醒；
- 新闻源健康度、信息去重、影响对象、传导链和原文链接；
- 交易记录按真实成交口径汇总，避免把委托、图表标注和重复持仓快照计入成交金额。

所有真实交易功能仍默认关闭。没有真实、近期、可追溯的数据时，系统只允许观察、减仓建议或人工复核，不会自动新增仓位。

## 2. 统一决策链路

回测、实时模拟和真实交易共享以下决策顺序：

1. 读取带来源、抓取时间、可用时间和有效期的数据快照；
2. 计算基本面、技术面、信息面、资金面、大盘环境、行为风险和数据质量；
3. 生成 `ScoreProvenance`，保存每个因子的原值、归一值、权重、贡献、来源和解释；
4. 根据股票类型和交易周期选择策略配置；
5. 由自适应策略根据市场状态和数据质量调整门槛与目标仓位；
6. 进入 `RiskGateway` 检查交易时段、停牌/涨跌停、数据过期、仓位、现金、日亏损和重复委托；
7. 模拟交易进入本地撮合，真实交易进入人工确认队列；
8. 用户确认后重新执行一次数据和风控检查，再交给 `ExecutionRouter` 与券商适配器；
9. 订单、成交、持仓、账户、评分、风控、券商原始返回、审计和图表标注统一写入 SQLite。

真实交易不能由单一分数直接触发，也不能使用缺失或过期数据绕过门禁。

## 3. 策略与评分配置

系统根据交易目的使用不同配置，不对所有股票套用同一套权重：

| 策略 | 主要证据 | 风控重点 | 典型用途 |
| --- | --- | --- | --- |
| 短线 | 分时、VWAP、量能、盘口、行为风险 | 快速止损、高风险禁入、数据必须新鲜 | 盘中交易 |
| 波段 | MA20/MA60、MACD、板块强度、支撑压力 | ATR 止损、趋势破坏退出 | 数周级持有 |
| 长线 | 基本面、行业景气、估值、长期趋势 | 财务披露时点、重大负面、长期趋势 | 优质公司持有 |
| 定投 | ETF/指数估值、趋势和市场风险 | 极端风险暂停、周期投入 | ETF 和长期资产 |
| 核心卫星 | 核心基本面与卫星动量分别核算 | 分账户仓位和收益归因 | 长短结合 |
| 事件驱动 | 官方公告、财报、政策、行业催化 | 事件时效、来源可信度、负面否决 | 有明确催化的交易 |

自适应策略只在基础评分之上有限调整：市场弱势提高买入门槛并降低仓位；数据质量下降只降权或阻断，不把缺失数据记为中性满分；多个高度相关的海外指数和新闻不会重复加分。

## 4. 券商适配矩阵

| 适配器 | 用途 | 自动下单条件 | 未配置时表现 |
| --- | --- | --- | --- |
| Disabled | 默认安全状态 | 不支持 | `disabled` |
| Simulator | 回测/实时模拟 | 本地模拟撮合 | 可正常 paper trading |
| QMT | 迅投 QMT/miniQMT | 本机已安装并登录，`xtquant` 可导入，账户和路径已配置 | `unsupported` 或详细缺失项 |
| PTrade | 券商授权的 PTrade 环境 | 券商 SDK/桥已授权并配置 | `unsupported` 或详细缺失项 |
| 同花顺桌面端 | 启动软件、委托提醒 | 不提供通用安全自动下单接口 | 仅启动/提醒，不伪造成交 |
| 同花顺 iFinD | 授权数据接口 | 仅作为数据源，不等于交易通道 | 显示数据授权状态 |
| 同花顺 SuperMind/授权桥 | 量化交易 | 必须使用官方或券商授权交易环境 | 未授权时禁用 |
| HTTP 本地桥 | 用户自建合规桥接 | 仅本机、令牌、适配器身份和健康检查均通过 | `unsupported`/`disconnected` |

零售版同花顺桌面程序不能通过模拟点击冒充可靠自动交易。系统可以启动 `hexinlauncher.exe` 并发出委托提醒，但自动委托只能通过已授权且有明确订单回执的桥接接口。

## 5. 安全配置

默认环境必须保持：

```text
FEATURE_LIVE_BROKER=false
LIVE_TRADING_ENABLED=false
ORDER_CONFIRM_REQUIRED=true
LIVE_KILL_SWITCH=false
```

常用安全变量：

```text
BROKER_PROVIDER=disabled
TRADE_WHITELIST_SYMBOLS=300750,600438
MAX_LIVE_ORDER_VALUE=10000
MAX_DAILY_LIVE_ORDER_COUNT=10
MAX_DAILY_LOSS_PCT=2
```

QMT 还需要本机环境提供 `QMT_PATH`、`QMT_ACCOUNT_ID`、`QMT_ACCOUNT_TYPE` 和 `QMT_SESSION_ID`。PTrade、SuperMind 或 HTTP 桥的账号、令牌和地址只能放在本地环境变量或未纳入 Git 的配置中。

启用顺序：先在 `/broker-setup` 选择通道并进行只读校验，再在 `/live-trading` 连接和同步账户，使用预检查确认数据、现金、仓位与风控，最后由用户逐单确认。任何异常应先打开 kill switch。

## 6. 移动端提醒

提醒服务支持钉钉、飞书、企业微信和通用 Webhook。它只发送信号、风险、待确认、成交或故障通知，不能代替人工确认，也不能直接下单。未配置 Webhook 时返回 `disabled`，不会把发送失败当成已通知。

## 7. 数据真实性与信息面

- 新闻卡片必须显示来源、发布时间、原文链接、影响股票/行业/概念和传导逻辑；
- 同一事件按标题、正文、来源和时间窗口去重，转载不会重复放大评分；
- 未来财报、会议、交割、解禁和政策日程只形成观察/风险门禁，不预设结果；
- 搜索结果页永久禁用，不能作为新闻证据；
- 基本面缺少披露日期或真实来源时不进入可交易评分；
- 大盘环境必须有指数趋势或有效市场宽度，海外行业参照只作为有限环境调节；
- 公开资金流、量价代理和基金持仓披露必须分开标注，不能声称为券商逐笔主力持仓。

`/data-center` 可查看自动交易就绪度、数据源健康、缺失/过期字段、最近错误、按范围刷新结果，以及白名单 SQLite 的文件位置、表数、行数、完整性和 WAL 大小。数据库管理只允许只读盘点与 WAL checkpoint，不开放任意路径、任意 SQL 或删除操作。

## 8. 每日交易池评分与走势

自动交易配置池、自选监控池、运行/暂停中的实时模拟池、真实交易观察会话和真实持仓都会进入每日评分目标。默认在中国市场交易日 `15:10` 后运行一次：

1. 优先刷新真实行情与日 K；失败时只使用可追溯缓存并标记过期；
2. 通过统一决策服务计算基本面、技术面、信息面、资金面、大盘环境、日 K 与盘中评分；
3. 保存 `ScoreProvenance` 和 `daily_score_snapshots`；
4. 记录缺失、过期、数据源、策略族与自动入场门禁；
5. 始终保持 `orders_created=0` 和 `broker_submitted=false`。

因此筛选页仍可人工触发深度筛选，但交易池每天的评分留痕不依赖用户再次点击筛选。总控台走势会区分手工筛选、每日自动评分和盘中评分；接口为 `GET /api/score/trend/{symbol}`、`GET /api/score/daily/status` 和 `POST /api/score/daily/run`。

## 9. 页面与 API 入口

主要页面：`/auto-trading`、`/screener`、`/ui`、`/info`、`/backtest`、`/realtime-paper`、`/broker-setup`、`/live-trading`、`/trading-records`、`/data-center`。

主要新增/完善接口：

- `GET /api/live-broker/setup`
- `POST /api/live-broker/setup/validate`
- `GET /api/score/trend/{symbol}`
- `GET /api/score/daily/status`
- `POST /api/score/daily/run`
- `GET /api/auto-trading/config`
- `POST /api/auto-trading/config`
- `GET /api/auto-trading/readiness`
- `GET /api/data-center/decision-readiness`
- `POST /api/data-center/refresh`
- `GET /api/data-center/source-errors`
- `GET /api/data-center/databases`
- `POST /api/data-center/databases/{database_key}/checkpoint`
- `GET /api/notifications/mobile/status`
- `POST /api/notifications/mobile/test`
- `GET /api/trading-records`

## 10. 验收边界

- 本机没有 QMT/PTrade/同花顺授权 SDK 时，系统只能证明诊断、预检查、确认队列和降级逻辑可运行，不能声称已连接真实账户；
- 回测结果不等于未来收益；
- 实时模拟用于检验数据、评分、风控和执行流程，不是真实成交；
- 用户必须自行满足券商、监管、账户授权和交易风险要求。

所有交易页面均应显示：研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。
