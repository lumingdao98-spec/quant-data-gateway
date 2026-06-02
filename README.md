# Quant Data Gateway V3.18.3 / Stable Recovery

面向 A 股和 ETF 的研究辅助系统。V3.18.3 把 WordSource、筛选快照、信息快照、K 线缓存、技术因子、全球行业映射、市场行为标注和前端恢复状态接成闭环：页面打开不再默认空白，返回筛选页不丢结果，详情页优先复用缓存。

## 启动方式

```bash
pip install -r requirements.txt
python -m uvicorn quant_data.api:app --host 127.0.0.1 --port 8001
```

常用页面：

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
