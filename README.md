# Quant Data Gateway V3.28

面向 A 股与 ETF 的研究、筛选、行情、信息分析、历史回测、实时模拟和券商交易接入平台。回测、模拟和实盘共享同一套数据真实性、评分溯源、策略适配、仓位、风控、订单、持仓、审计和图表标注内核。

> 研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。

## 当前能力

- 股票筛选：股票池、策略组合、四面评分、市场环境、风险标签和缓存恢复；
- 行情详情：分时、日/周/月 K 线、成交量、MACD、KDJ、五档盘口、近 7 日异常和订单成交标注；
- 信息面：官方公告、财经新闻、全球事件、未来日程、去重、来源链接、影响股票/行业/概念和传导链；
- 多角色证据复核：评分技术、基本面、信息面、资金主线和大盘环境分别出具证据/反证/缺失项，再由独立风险委员会和组合裁决汇总；
- 资金与市场：公开资金流、分时量价方向代理、板块主线、市场宽度、国内指数和可映射的海外行业背景；
- 历史回测：point-in-time 数据、组合策略、资金管理、止损止盈、交易成本、买卖点、买入持有对比和完整流水；
- 实时模拟：真实行情驱动、会话恢复、交易时段门禁、模拟撮合、持仓复核、账户/订单/成交/标注/审计落库；
- 真实交易：QMT、PTrade、同花顺授权环境和通用本地 HTTP 桥的配置诊断、人工确认队列、重新风控和券商回执；
- 统一记录：回测、模拟和实盘的委托、成交、持仓、账户、费用、盈亏、评分、风控、确认和审计；
- 移动提醒：钉钉、飞书、企业微信和通用 Webhook，默认关闭，不代替人工确认；
- 数据中心：缓存、来源健康、缺失/过期字段、自动交易就绪度、最近错误和按范围刷新。

## 启动

日常使用只需双击项目根目录的 `QuantDataGateway.exe`。它会使用项目自带的 `.venv`，自动选择空闲端口、启动服务、等待健康检查通过并打开自动交易总控台；重复双击只会打开已运行的总控台，不会重复启动服务。关闭启动器时会一并停止由它启动的后台服务。

首次部署仍需由开发者安装依赖；普通使用不需要系统全局存在 `python` 命令。QMT 用户推荐 Python 3.11。以下命令仅用于开发和维护，不是日常入口：

```powershell
py -3 -m pip install -r requirements_full.txt
py -3 -m uvicorn quant_data.api:app --host 127.0.0.1 --port 8001
```

默认打开 `http://127.0.0.1:8001/auto-trading`。总控台通过右侧完整功能页打开并释放各模块，原页面和 API 仍可独立使用。

## 页面

| 页面 | 路径 | 用途 |
| --- | --- | --- |
| 自动交易总控台 | `/auto-trading` | 全平台总览、模块入口、评分、券商、事件和安全状态 |
| 股票筛选 | `/screener` | 股票池、评分、策略适配和加入回测/模拟/实盘观察池 |
| 行情与 K 线 | `/ui` | 分时、K 线、盘口、因子、异常和交易标注 |
| 信息面 | `/info?symbol=300750` | 近期信息、全球事件、未来日程、映射与来源 |
| 历史回测 | `/backtest` | 组合策略、资金周期、止损止盈和完整流水 |
| 实时模拟 | `/realtime-paper` | 多股票 paper trading 会话、账户、持仓和订单 |
| 券商接入向导 | `/broker-setup` | 分步检查 QMT、PTrade、同花顺桌面伴随与授权执行桥 |
| 真实交易 | `/live-trading` | 券商诊断、账户同步、批量预检、确认和 kill switch |
| 交易记录 | `/trading-records` | 跨模式事件流水、成交账本、持仓批次和账户快照 |
| 数据中心 | `/data-center` | 数据源、缓存、新鲜度、缺失字段和刷新 |
| 中文 API | `/docs-cn` | 中文接口说明 |
| Swagger | `/docs` | 可直接填写参数并调用 API |

## 统一评分与交易链路

系统记录基本面、技术面、信息面、资金面、大盘环境、行为风险和数据质量。每个参与评分的因子必须保存原值、归一值、权重、贡献、来源、可用时间、置信度和解释。

1. 获取真实、可追溯且未过期的数据；
2. 生成评分溯源和策略适配结果；
3. 根据短线、波段、长线、定投、核心卫星或事件驱动配置调整门槛和仓位；
4. 通过数据新鲜度、交易时段、现金、仓位、涨跌停、停牌、日亏损、重复委托和重大风险检查；
5. 回测/模拟进入各自拍摄或撮合，实盘进入人工确认队列；
6. 实盘确认后重新检查，再路由至授权券商；
7. 订单、成交、持仓、账户、风控、原始回执和图表标注统一落 SQLite。

缺失或无效维度不会被填成 50 分；可选维度缺失时剩余有效权重重新归一化，必需维度缺失、数据过期或来源不可追溯会阻断自动新增仓位。

总控台的多角色复核借鉴 TradingAgents 的角色分工、正反辩论、独立风控和结果复盘结构，但不把语言模型放进订单执行路径。`GET /api/agent/market-brief` 返回稳定复核编号、五角色观点、支持/反对证据、风险裁决和复盘基准；只有用户主动联网复核时才覆盖写入审计记录。可选外部模型只能解释已有可追溯证据，始终保持 `order_capability=false`。

## 券商与同花顺

真实交易默认关闭：

```text
FEATURE_LIVE_BROKER=false
LIVE_TRADING_ENABLED=false
ORDER_CONFIRM_REQUIRED=true
LIVE_KILL_SWITCH=false
BROKER_PROVIDER=disabled
```

- QMT：需要本机已安装并登录 QMT/miniQMT，`xtquant` 可导入，并配置 `QMT_PATH`、`QMT_ACCOUNT_ID`、`QMT_ACCOUNT_TYPE`、`QMT_SESSION_ID`；
- PTrade：需要券商提供的授权环境、SDK 或合规交易桥；
- 同花顺零售桌面端：只支持启动客户端和委托提醒，不能把界面自动点击伪装成可靠自动下单；
- 同花顺 iFinD：作为授权数据接口，不等于交易通道；
- 同花顺 SuperMind/券商授权桥：只有具备正式授权、订单回执和账户接口时才能配置为交易适配器；
- HTTP 本地桥：仅面向用户自建的合规本地服务，必须校验地址、令牌、适配器身份、健康状态和订单回执。

未安装 SDK、未登录、未授权或配置不完整时，接口返回 `disabled`、`unsupported` 或具体缺失原因，不会生成虚假账户、委托和成交。

配置入口为 `/broker-setup`。网页只做本机组件和配置的只读校验，账号与令牌不会由页面写入仓库或数据库；按页面生成的环境变量模板在本机配置并重启服务后，再到 `/live-trading` 做账户只读同步、预检查和人工确认。

## 数据库与每日评分

服务端关键状态存放在项目 `data/` 下的白名单 SQLite，包括 `market_cache.sqlite`（行情、手工筛选和每日评分）、`cache_state.sqlite`（筛选池、配置与任务状态）、`news_store.sqlite`（去重后的新闻和公告）、`feature_store.sqlite`（技术因子）、`company_profile.sqlite`（基本面画像）、`v323_trading_store.sqlite`（订单、成交、持仓、账户、评分溯源和审计）以及 `local_integrations.sqlite`（不含密码/令牌的本地伴随配置）。实际路径以 `/data-center` 的“SQLite 数据库管理”为准。

加入自动交易配置池、自选监控池、运行中的实时模拟池或真实持仓后，后台会在交易日收盘后默认 `15:10` 为每只股票保存一次可追溯评分。它不依赖再次点击筛选，也不会创建订单。总控台“评分走势”和 `/api/score/trend/{symbol}` 会分别标明每日自动评分、盘中评分与手工筛选评分；需要立即留痕时可点击“保存今日评分”。

## 数据真实性

- 没有真实数据时展示数据源缺失、字段缺失、缓存过期、休市无盘口、接口不支持或未授权；
- 百度、360、搜狗等搜索结果页永久禁用，不抓取、不计分、不展示；
- 新闻必须带来源、发布时间和原文链接，转载事件会去重；
- 未来财报、会议、交割、解禁和政策日程仅用于观察和风险门禁，不预设结果；
- 回测只使用决策时点前可得数据，不用当前新闻、财务或海外行情回填历史；
- 公开资金流、量价代理、基金持仓披露和券商逐笔数据分别标注，不互相冒充；
- 数据过期可用于观察、减仓或人工复核，但不能自动新增仓位。

## 常用 API

```text
GET  /api/auto-trading/config
GET  /api/auto-trading/readiness
GET  /api/agent/market-brief
GET  /api/live-broker/setup
POST /api/live-broker/setup/validate
GET  /api/score/trend/{symbol}
GET  /api/score/daily/status
POST /api/score/daily/run
GET  /api/live-broker/status
POST /api/live-broker/connect
POST /api/live/orders/preview
POST /api/live/orders/confirm
GET  /api/live/confirm-queue
GET  /api/realtime-paper/sessions
POST /api/realtime-paper/sessions/start
POST /api/realtime-paper/sessions/{session_id}/tick
GET  /api/trading-records
GET  /api/data-center/decision-readiness
GET  /api/data-center/source-errors
GET  /api/data-center/databases
POST /api/data-center/databases/{database_key}/checkpoint
POST /api/data-center/refresh
GET  /api/notifications/mobile/status
POST /api/notifications/mobile/test
```

完整接口以 `/docs-cn` 和 `/docs` 为准。

## 测试

```powershell
.\.venv\Scripts\python.exe -m compileall -q quant_data
.\.venv\Scripts\python.exe -m pytest -q
```

测试覆盖数据真实性、新鲜度、评分溯源、自适应策略、仓位、风控、订单生命周期、模拟会话恢复、实盘默认禁用、确认队列、QMT/PTrade import guard、同花顺能力边界、移动提醒、交易记录和主要页面。

## 文档

- 当前配置、安全和评分说明：`docs/V328_BROKER_AND_ADAPTIVE_SCORING.md`
- 单包迁移、历史数据合并和完整性校验：`docs/V328_SINGLE_PACKAGE_MIGRATION.md`
- WordSource 实现追溯：`docs/WORD_SOURCE_TRACE.md`
- 回测 WordSource 追溯：`docs/BACKTEST_WORDSOURCE_TRACE.md`
- 历史版本和发布笔记：`docs/archive/README.md`

历史设计文档仅用于审计和版本追溯；当前行为以代码、V3.28 文档和测试为准。
