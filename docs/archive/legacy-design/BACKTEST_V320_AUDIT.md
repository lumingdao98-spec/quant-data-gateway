# V3.20 Scientific Backtest & Trading Readiness Audit

## 1. 当前已有功能

- `quant_data/services/backtest_service.py`：legacy 单标的快速回测，支持日评分、均线、RSI、突破、MACD、BOLL 等策略，前端 `/backtest` 使用它做快速验证。
- `quant_data/backtest/engine.py`：统一无未来函数日线引擎，信号日生成、下一交易日成交，支持多标的、组合状态、订单/成交/持仓/权益曲线。
- `quant_data/backtest/execution.py`：已有 T+1、100 股手数、停牌/零成交量、涨跌停、成交量上限、手续费/印花税/过户费/滑点。
- `quant_data/backtest/portfolio.py`：现金、持仓、T+1 解锁、盯市、止损/止盈/跟踪止损订单。
- `quant_data/backtest/risk.py`：收益、年化、回撤、Sharpe/Sortino/Calmar、胜率、profit factor、换手和基准超额。
- `quant_data/backtest_ui.py`：旧单票回测页面，K 线、成交量、评分/MACD、副图、交易流水抽屉和新窗口。
- `quant_data/backtest/paper_broker.py` 与 `/api/paper/*`：初步 paper trading，不连接真实券商。

## 2. 当前不合理之处

- legacy 回测和新回测双体系长期并存，旧页面容易被误认为科学组合回测。
- legacy 评分主要回放量价技术底分，历史新闻、公告、财务、大盘情绪没有逐日 point-in-time 复盘。
- 原执行模型中 price-adjusted slippage 与 `slippage_cost` 同时扣现金，存在滑点重复计算风险。
- 原限价单用 `limit_price` 直接成交，没有先确认 high/low 是否触达。
- 原组合回测的调仓逻辑偏信号驱动，缺少 sell-first、现金约束、单票/行业上限、最小成交额和残差记录。

## 3. 未来函数风险

- 当前 V3.20 引擎使用信号日当日及以前数据，下一交易日成交；`BacktestDataLoader.assert_no_lookahead` 会阻断成交日不晚于信号日的订单。
- `screener_rows` 如果没有 `date` 字段，只能视为当前快照做向前模拟，不应当回填到历史日期。
- 历史信息面/基本面没有 point-in-time 数据时，默认不进入历史评分，只能作为实盘观察辅助。

## 4. 撮合模型风险

- V3.20 已修复滑点模式：
  - `price_adjusted_slippage` 默认使用成交价体现滑点，现金不额外扣滑点。
  - `explicit_slippage_cost` 使用基准价成交，滑点作为成本扣现金。
- V3.20 已修复限价触达：只有 `low <= limit_price <= high` 才能成交；未触达订单会 pending 或 expired 并写入 fills/log。
- A 股规则已补：T+1、100 股手数、停牌/零成交量、主板/ST/创业板科创板/北交所涨跌幅、默认不涨停买入/跌停卖出。
- 仍需后续增强真实盘口成交队列、集合竞价、逐笔成交和更精细的冲击成本模型。

## 5. 组合调仓风险

- 新增 `quant_data/backtest/rebalance.py` 的 `RebalanceEngine`，按目标权重、当前持仓、现金、最大持仓数、单票上限、T+1 可卖量、最小成交额做 sell-first 调仓。
- 残差会记录为 `residuals`，避免静默忽略未成交或金额不足。
- 行业上限字段已进入配置，后续需要接入稳定的行业映射快照后才能严格执行。

## 6. 指标评价不足

- V3.20 新增 expectancy、payoff ratio、胜负分布、当前/最大连亏、平均 MFE/MAE、止损/止盈效率、按信号评分分桶 precision。
- Walk-forward 增加 IS/OOS 指标、OOS 胜率、OOS 最大回撤、组合目标 `composite_score` 和过拟合警告。
- 仍建议后续补充行业归因、持仓集中度归因、市场环境分层表现。

## 7. 前端不足

- `/backtest` 目前保留为 legacy 单票快速验证页，并明确显示“legacy 快速验证，不作为科学组合回测”。
- V3.20 默认 API 可返回统一引擎结果；旧页面通过 `legacy=true` 使用旧兼容数据，避免破坏现有 K 线和交易流水体验。
- 后续需要新增完整 V3.20 研究面板：调仓计划、质量过滤归因、退出策略归因、walk-forward 窗口和风险闸状态。

## 8. Paper Trading 不足

- 旧 `paper_broker.py` 可生成纸面订单并模拟成交，但缺少独立风控闸、审计日志和信号队列。
- V3.20 新增 `quant_data/trading/*`：
  - `RiskGateway`：评分、ST/退市、涨跌停、现金、单票和总仓位检查。
  - `PaperTradingGateway`：只生成纸面订单，不接券商。
  - `AuditLog` 与 `SignalQueue`：记录信号、风险判断和订单状态。
- 新增 API：`POST /api/trading/signal`、`GET /api/trading/paper/orders`、`/positions`、`/api/trading/risk/status`、`/api/trading/audit`，以及 `/trading` 页面。

## 9. 自动交易前必须修复的事项

- 必须有稳定的历史 point-in-time 数据源，尤其是信息面、财务、行业、大盘环境。
- 必须用 paper trading 连续运行并对比真实可成交盘口，确认滑点和冲击成本。
- 必须引入人工确认、交易时段校验、撤单/重试/幂等、最大日亏损、最大连续亏损、黑名单和异常停机。
- 必须完成权限隔离和审计留痕，真实券商接入前不能复用研究 API 直接下单。

## 10. 本轮 V3.20 修复清单

- 新增 `BacktestEngineV320`，默认 API 支持 V3.20，引擎结果包含 `engine_version=v3.20`。
- legacy 单票接口需要显式 `legacy=true`，返回 `legacy_warning`；旧页面已展示 legacy 提示。
- 修复滑点与现金成本重复扣减。
- 修复限价单触达/过期逻辑。
- 完善 A 股涨跌停、T+1、手数、停牌和最小成交额约束。
- 新增 `RebalanceEngine`、`StrategyQualityFilter`、`ExitPolicy`、`HistoricalScreenerSnapshotBuilder`。
- 增加胜率/赔率和 walk-forward 稳健性诊断字段。
- 新增 paper-only 交易风控网关和 API。
- 新增 `.gitignore` 并计划移除缓存、日志、SQLite、pycache 等不应继续纳入版本控制的文件。
