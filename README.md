# Quant Data Gateway V3.18.3 / Stable Recovery

## V3.25 Market Intelligence / Position Review

在 V3.24 交易内核之上新增可追溯市场事件调分和每日持仓复核，不修改已稳定的评分权重与映射核心：

- `/api/market/event-factors/{symbol}` 区分“大盘环境”和“个股信息”，只读取带时间、来源和链接的真实缓存；
- 海外科技风险、流动性变化和大额 IPO 可有限调整大盘环境，只有公司主营/产业链明确重合才调整个股信息；
- `/api/realtime-paper/sessions/{session_id}/review-positions` 保存模拟持仓的成本、现价、盈亏、评分变化与持有/减仓/退出建议；
- `/api/live/review-positions` 只读复核真实持仓，永不直接调用券商，减仓和退出仍需标准风控及人工确认；
- `/api/position-reviews/scheduler/status` 和 `/api/position-reviews/scheduler/run-due` 提供可恢复的每日持仓复评调度；
- 无 QMT/PTrade SDK 时仍可回测、模拟、批量预检查并保存待确认票据；如用户已有合规授权的本地交易桥，可选择 `http_bridge` 适配器，否则不会伪造成券商委托或真实成交；
- 浏览器不能绕过人工确认：批准时会重新校验服务器行情、评分溯源、风控、交易时段、券商连接、现金/持仓和重复订单。

详细规则见 `docs/V325_MARKET_EVENT_POSITION_REVIEW.md` 和 `docs/V325_PROGRAMMATIC_BROKER_BRIDGE.md`。

## V3.24 Live Sync / PIT / Ledger

V3.24 在 V3.23 自动交易核心上补齐多股票实盘批量预检查、QMT/PTrade 安全适配、账户/持仓/委托/成交同步、统一策略族、FIFO 持仓批次、跨模式账本与新闻/财报/IPO 的 point-in-time 事件查询。既有评分权重和映射逻辑不重写。

关键增强：

- `/auto-trading` 升级为 V3.24 总控台，继续用右侧 iframe 保留全部既有模块；
- `/live-trading` 支持多股票观察池、实盘分时策略预设、批量预检查、逐单人工确认、账户/持仓/成交/账本/对账；
- `/realtime-paper` 显示会话 ID、最后行情、最后决策、数据新鲜度、事件次数与待确认操作；
- `/trading-records` 统一查询回测、模拟和实盘的订单成交、账本、FIFO 持仓批次与账户权益；
- 新闻、财报、IPO 和事件回放严格执行 `available_at <= decision_time`，没有真实来源时明确返回缺失或拒绝；
- QMT/PTrade SDK 或授权不存在时返回 `unsupported`，真实交易仍默认关闭。

详细设计与接口见 `docs/V324_LIVE_SYNC_PIT_LEDGER.md`。

## V3.23 Full Auto Trading Core

V3.23 把历史回测、实时模拟交易和真实券商自动交易拆成独立入口，同时共享统一的数据、评分、风控、订单、持仓、审计和图表标注内核。

页面入口：

- `/auto-trading`：V3.23 总控台首页，以右侧 iframe 打开并释放各功能页，集中查看流程、模拟账户、实盘安全、全球要闻和板块主线。
- `/screener`：股票筛选，支持加入自选池、回测池、实时模拟池和真实交易观察池。
- `/detail/{symbol}` 或 `/ui?symbol=300750`：分时/K线、盘口、信息面、技术面、行为风险和图表标注。
- `/backtest`：历史回测，使用历史数据和 point-in-time 快照，不连接真实行情和券商。
- `/realtime-paper`：实时模拟交易，只做 paper trading，不真实下单。
- `/live-trading`：真实交易接口页，默认禁用，未配置/未授权/未确认时只返回拒单或确认队列。
- `/trading-records`：统一交易记录，展示回测、模拟、真实交易的订单、成交、风控、评分溯源和审计。
- `/data-center`：缓存、数据源、缺失字段、过期状态和券商状态。

核心安全规则：

- `FEATURE_LIVE_BROKER=false`、`LIVE_TRADING_ENABLED=false`、`ORDER_CONFIRM_REQUIRED=true` 是默认状态。
- 开启真实交易需要本地券商终端、用户授权、环境变量、风控配置、人工确认和用户自行完成合规要求。
- 当前支持 `DisabledBrokerAdapter`、`SimulatorBrokerAdapter`、QMT/PTrade import guard。若本机没有 `xtquant` 或 PTrade SDK，会返回 `unsupported`，不会导致服务崩溃。
- 没有真实数据时系统不会伪造；会显示数据源缺失、字段缺失、缓存过期、休市无盘口、券商不支持或未授权。
- 百度、360、搜狗搜索结果页永久禁用，不抓取、不计分、不展示。

可选联网 AI 研判默认关闭，只能对真实、近期且带来源链接/API 的证据做研究解释，不能创建、确认或提交订单。需要使用时在本地环境配置：

```bash
MARKET_AI_ENABLED=true
MARKET_AI_MODEL=<支持结构化输出的模型>
MARKET_AI_API_KEY=<仅保存在本地环境>
# 可选：MARKET_AI_API_BASE=https://api.openai.com/v1
```

未配置密钥或模型时，`/api/agent/market-brief` 继续返回规则证据代理结果并明确显示缺失原因；密钥不会写入页面、日志或 Git。

V3.23 文档：

- `docs/V323_BASELINE_AUDIT.md`
- `docs/V323_AUTO_TRADING_DESIGN.md`
- `docs/V323_BROKER_ADAPTER_GUIDE.md`
- `docs/V323_LIVE_TRADING_SAFETY.md`
- `docs/V323_ORDER_LIFECYCLE.md`
- `docs/V323_CHART_MARKERS.md`
- `docs/V323_DATA_TRUTH_RULES.md`
- `docs/V323_COMPLIANCE_NOTES.md`

## V3.22 研究回测与纸面交易增强

本分支继续保留 V3.20/V3.21 兼容入口，并新增 V3.22 核心能力：

- 评分溯源：`BacktestResult.score_provenance` 记录因子贡献、门禁、策略 hash、PIT 覆盖率和 no-lookahead 状态。
- 大盘/个股/策略适配：`quant_data/research/` 提供大盘状态、个股分类和策略族建议。
- 交易规则配置：`config/market_rules/a_share_rules.yaml` 管理涨跌停、T+1、买入手数和卖出零股，执行层不再直接硬编码板块前缀。
- 资金与仓位：支持固定、评分、波动率、ATR、定投、金字塔、Kelly 等模式，并输出仓位利用和现金拖累。
- 历史筛选快照：`/api/screener/historical-snapshot` 按决策时点重建筛选结果，避免回测偷看未来。
- 纸面交易：`/api/realtime-paper/*` 仍然只做模拟，新增人工确认队列，不连接真实券商。
- 中文 API：`/docs-cn` 是中文总览，`/docs` 保留 Swagger Try it out，可直接调参数。

配套文档见 `docs/QDG_AUTOTRADING_V1.md`、`docs/QDG_SCORE_PROVENANCE_SPEC.md`、`docs/QDG_PIT_DATA_REQUIREMENTS.md` 和 `docs/TEST_PLAN_V322.md`。

面向 A 股和 ETF 的研究辅助系统。V3.18.3 把 WordSource、筛选快照、信息快照、K 线缓存、技术因子、全球行业映射、市场行为标注和前端恢复状态接成闭环：页面打开不再默认空白，返回筛选页不丢结果，详情页优先复用缓存。

## 启动方式

```bash
pip install -r requirements.txt
python -m uvicorn quant_data.api:app --host 127.0.0.1 --port 8001
```

常用页面：

- `http://127.0.0.1:8001/auto-trading`：自动交易总控台，统一进入筛选、回测、实时模拟、实盘安全、记录和数据中心。
- `http://127.0.0.1:8001/screener`：筛选页，默认精简视图，可恢复上次筛选。
- `http://127.0.0.1:8001/info?symbol=300274&name=阳光电源`：信息详情页，自动读取快照或普通刷新。
- `http://127.0.0.1:8001/ui`：行情监控与 K 线详情。
- `http://127.0.0.1:8001/chart/300750?frame=1d`：独立 K 线页。
- `http://127.0.0.1:8001/wordsource`：WordSource 映射表。
- `http://127.0.0.1:8001/technical/300750`：技术因子矩阵。
- `http://127.0.0.1:8001/health`：数据源健康。
- `http://127.0.0.1:8001/cache`：缓存状态。
- `http://127.0.0.1:8001/backtest`：legacy 单票快速回测页，页面会显式提示不作为科学组合回测。
- `http://127.0.0.1:8001/trading`：V3.20 纸面交易风控网关，不连接真实券商。

新增解释与复核接口：

- `GET /api/market/event-factors/{symbol}`
- `POST /api/realtime-paper/sessions/{session_id}/review-positions`
- `GET /api/realtime-paper/sessions/{session_id}/position-reviews`
- `POST /api/live/review-positions`
- `GET /api/live/position-reviews`

## V3.20 回测体系说明

V3.20 默认回测入口为 `quant_data/backtest/engine.py` 中的 `BacktestEngineV320`，API `POST /api/backtest/run` 以及未显式 `legacy=true` 的 `GET /api/backtest/run` 均走统一科学回测引擎。旧版 `quant_data/services/backtest_service.py` 保留为 legacy 单标的快速验证，用于前端兼容和肉眼检查 K 线，不作为科学组合回测或自动交易依据。

关键差异：

- V3.20 引擎使用信号日生成、下一交易日成交，默认避免未来函数。
- 滑点默认 `price_adjusted_slippage`：成交价已体现滑点，现金不重复扣滑点。
- 限价单必须 high/low 触达才成交，未触达会 pending 或 expired。
- A 股 T+1、手数、涨跌停、停牌、成交量上限和最小成交额进入撮合约束。
- 交易风控仅提供 paper trading 底座，不接真实券商、不真实下单。

审计文档见 `docs/BACKTEST_V320_AUDIT.md`。

## 缓存与恢复

统一缓存层位于 `quant_data/services/cache_state_service.py`，使用 SQLite 持久化，覆盖：

- `screener_snapshot`：默认 TTL 30 分钟。
- `info_snapshot`：默认 TTL 6 小时。
- `kline_cache`：日 K 默认 TTL 6 小时。
- `quote_cache`：交易时段短 TTL。
- `technical_factor_cache`：默认 TTL 6 小时。
- `global_news_cache`：默认 TTL 45 分钟。

相关 API：

- `GET /api/cache/status`
- `GET /api/cache/screener/latest`
- `GET /api/screener/snapshot/{snapshot_id}`
- `GET /api/cache/info/latest/{symbol}`
- `GET /api/cache/kline/{symbol}`
- `POST /api/cache/clear`

所有快照读取都会返回 `cache_status`，包含 `hit/miss/stale/refreshed/error`、`snapshot_id`、`created_at`、`ttl_seconds`、`age_seconds` 和 `source`。前端 `/screener`、`/info`、`/chart`、`/cache` 都显示缓存状态。

## 筛选结果如何恢复

`/api/screener/run` 会生成 `screener_snapshot_id`，并返回 `results`、`summary`、`selected_symbol`、`cache_status`。前端把 snapshot、参数、选中行、滚动位置和视图模式写入 localStorage。返回 `/screener` 时会自动调用缓存接口恢复旧结果；缓存过期也保留旧结果，只提示“缓存已过期，可刷新”。

筛选页按钮：

- 恢复上次筛选
- 重新筛选
- 清空本地状态
- 精简视图 / 完整视图 / 调试视图

## 信息快照复用

筛选页启用信息面后，每个标的返回：

- `info_snapshot_id`
- `info_crawl_time`
- `info_effective_count`
- `info_unique_event_count`

详情页 URL 支持：

```text
/info?symbol=600438&name=通威股份&snapshot_id=xxxx&force=false
```

详情页优先读取 `snapshot_id`，没有时读取该股最近 `info_snapshot`，再没有才普通刷新。只有点击“普通刷新”“强制刷新”或“深度刷新”才重新抓。即使外部接口失败，页面也显示空状态、错误原因和 `source_logs`，不会白屏。

## Light / Normal / Deep

- `light`：筛选页使用。只跑历史库、巨潮公告、东方财富 F10、东方财富公告接口、少量股吧/雪球；不跑关键词矩阵；官方公告/F10/巨潮有效证据达到阈值后立即停止补源。
- `normal`：信息详情页普通刷新。官方源加常规个股新闻页，不跑关键词矩阵。
- `deep`：只有点击“深度刷新”才启用。允许财经门户、研报、行业政策、更多舆情和关键词矩阵；全局预算 8 秒，单源超时 3 秒，单源超时本轮熔断，预算耗尽后停止任务队列。

`info_limit` 是上限，不是必须凑满的目标。

## 全球新闻行业映射

`quant_data/services/global_industry_mapper.py` 会把全球/宏观/政策/商品信息映射到：

- 相关行业
- 相关概念
- 产业链位置
- 相关个股
- `relevance_score`
- `impact_direction`
- `impact_reason`

只有相关性达标的全球信息进入当前个股信息面评分；不相关信息只作为市场背景。信息详情页“全球/行业映射”tab 会展示映射证据和“不纳入个股评分”的原因。

## K 线缓存和失败兜底

`/api/kline/{symbol}` 和 `/api/detail/{symbol}` 返回：

- `ok`
- `bars`
- `source`
- `fallback_chain`
- `errors`
- `cache_status`
- `stale_cache_used`
- `behavior_analysis`
- `kline_markers`

日 K 不允许用新浪分钟接口伪装。真实日 K 获取失败时先读最近成功缓存；缓存也没有时返回 `ok=false`，前端显示错误原因和 fallback 链，不画假图。周 K/月 K 使用对应周期源或由日 K 聚合，分时与日 K 数据结构分开。

## 休市字段显示

- 委比、委差、五档盘口：休市显示“休市无盘口”，午休显示“午休无盘口”，非交易时段显示“不适用”。
- 换手率：实时快照、最近交易日缓存、F10 依次兜底。
- PE/PB/总市值/流通市值：实时快照、公司画像/F10、基本面缓存依次兜底。
- ETF 的 PE/PB 显示“不适用”。
- 缺失字段必须带原因，例如“行情源缺失 PE”“ETF 不适用 PE/PB”“数据源缺失”。

## 技术因子矩阵

接口：`GET /api/technical/factors/{symbol}`

每个因子返回：

- `key`
- `name`
- `category`
- `value`
- `formula`
- `params`
- `signal`
- `explanation`
- `score_contribution`
- `risk_penalty`
- `applicable_market`

至少覆盖 MA、EMA、MACD、RSI、KDJ、BOLL、ATR、VWAP、WR、CCI、ROC、MOM、OBV、MFI、ADX、DMI、BIAS、SAR、VR、PSY、BRAR、CYR、Ichimoku、Fibonacci、TD、Pivot、ZigZag、支撑压力、量价状态、波动率、均量、成交额强度、价格区间位置、VWAP 强弱等 40+ 因子。筛选右侧详情卡提供“查看技术因子矩阵”入口。

## 行为风险标注

`quant_data/services/market_behavior_engine.py` 识别公开 OHLCV 可支撑的资金/K 线行为，包括：

- 疑似放量诱多、疑似骗量拉升、冲高回落风险、高位放量滞涨、假突破风险、次日洗盘确认
- 长上影诱多、高换手不涨、缩量洗盘、高位巨量阴线
- OBV/MFI/MACD/RSI 背离、跌破 MA20、跌破箱体
- 尾盘砸盘、尾盘抢筹等

缺少 Level-2、逐笔成交、账户级数据时，只输出“疑似资金对倒/骗量特征，需 Level-2 确认”，不输出确定性“主力对倒”或“庄家出货”。K 线页显示 `kline_markers` 列表，稳定后可继续扩展图层。

## WordSource 检查

Word 原件必须位于：

```text
docs/word_sources/炒股-消息面分析.docx
docs/word_sources/炒股-技术面分析.docx
docs/word_sources/炒股-风格与分析.docx
docs/word_sources/炒股-量化相关.docx
```

映射输出：

```text
docs/WORD_SOURCE_TRACE.md
```

页面和 API：

- `GET /wordsource`
- `GET /api/wordsource/trace`

映射状态支持“已落地 / 部分落地 / 未落地”，不会把所有条目无条件标成已落地。

## V3.19 Backtest / Paper Trading

V3.19 adds a typed backtest foundation in `quant_data/backtest/` while keeping the existing `/backtest` visual replay page compatible.

- `models.py`: BacktestConfig, StrategySignal, Order, Fill, Position, PortfolioState, Trade, BacktestResult.
- `data_loader.py`: adjust mode, warmup, data quality checks and no-lookahead notes.
- `signal_adapter.py`: screener snapshot signals, factor-rule signals and event-risk filtering.
- `execution.py`: A-share T+1, 100-share lots, no shorting, suspended/limit checks, fees, stamp tax, transfer fee, slippage and volume caps.
- `portfolio.py`: sizing, cash reserve, max positions, stops and daily portfolio states.
- `risk.py`: return, annualized return, max drawdown, Sharpe, Sortino, Calmar, win rate, turnover, costs and excess return.
- `optimizer.py` / `walk_forward.py`: parameter search and rolling out-of-sample validation.
- `storage.py` / `report.py`: result persistence, export and report generation.
- `paper_broker.py`: paper-only virtual broker; no real broker API is connected.

V3.19 response shape:

```json
{"ok": true, "run_id": "...", "data": {}, "metrics": {}, "errors": [], "warnings": [], "cache_status": "..."}
```

Core endpoints: `POST /api/backtest/run`, `GET /api/backtest/result/{run_id}`, `GET /api/backtest/runs`, `POST /api/backtest/compare`, `POST /api/backtest/optimize`, `POST /api/backtest/walk-forward`, `GET /api/paper/state`, `POST /api/paper/signal`, `POST /api/paper/fill`.

All outputs are research-only: `研究辅助，不构成投资建议`.

## 测试

```bash
python -m compileall -q quant_data
pytest -q
```

重点测试：

- `tests/test_cache_state_service.py`
- `tests/test_cache_status_api.py`
- `tests/test_screener_snapshot_restore.py`
- `tests/test_info_snapshot_autoload.py`
- `tests/test_news_fetch_modes_and_budget.py`
- `tests/test_global_industry_mapping.py`
- `tests/test_kline_cache_and_fallback.py`
- `tests/test_technical_factor_closed_loop.py`
- `tests/test_behavior_marker_visible_closed_loop.py`
- `tests/test_ui_smoke_closed_loop.py`

## 外部接口限制

本系统依赖公开行情、公告、F10、新闻和社区页面。公开接口可能限流、改版、休市返回空、字段缺失或响应慢。V3.18.3 的处理原则是：优先复用缓存、展示缺失原因、保留 stale 结果、避免伪造 K 线和 Level-2 结论。当前 V3.x 不接真实券商实盘接口；交易接口只保留给 V4/V5/V6/V7 的结构演进。

## V3.21 Dynamic Position & Realtime Paper Trading

V3.21 增加动态仓位、资金管理和实时模拟交易闭环。历史回测仍在 `/backtest`，用于验证历史 K 线、评分、止损止盈、仓位模式和买卖流水；实时模拟在 `/realtime-paper`，用于交易时段或手动 tick 的 paper-only 仿真。

核心能力：

- 资金管理模式：固定仓位、等权、评分加权、波动率目标、ATR 风险、单笔固定风险、分数凯利、金字塔、定投、核心-卫星。
- 收益再投资：`compound_returns=true` 使用最新 equity 计算下一次仓位，关闭时固定以 initial_cash 为基准。
- 策略周期：`intraday_paper`、`short_term`、`swing`、`position`、`dca`、`hybrid`。
- 三面评分：基本面、技术面、信息面，加上大盘/市场环境权重；缺失数据动态降权，不简单补 0。
- 异常过滤：高位滞涨、假突破、跌破 MA20/VWAP、尾盘砸盘、信息面负面和数据 stale 会降权、阻断或要求人工确认。
- 风控网关：订单前检查总仓位、单票/行业上限、现金、交易时段、涨跌停、ST/黑名单、低流动性、数据新鲜度和大额确认。
- paper trading：只生成模拟订单、模拟成交、模拟持仓和审计日志，不连接真实券商。

新增页面和 API：

- `/realtime-paper`
- `POST /api/realtime-paper/start`
- `POST /api/realtime-paper/stop`
- `GET /api/realtime-paper/status`
- `GET /api/realtime-paper/portfolio`
- `GET /api/realtime-paper/orders`
- `GET /api/realtime-paper/signals`
- `GET /api/realtime-paper/audit`
- `POST /api/realtime-paper/tick`
- `POST /api/realtime-paper/replay`

设计文档：

- `docs/BACKTEST_V321_GAP_AUDIT.md`
- `docs/MONEY_MANAGEMENT_DESIGN.md`
- `docs/REALTIME_PAPER_TRADING_DESIGN.md`
- `docs/TRADING_RISK_GATEWAY.md`
- `docs/AUTO_TRADING_ROADMAP.md`
