# V3.22 测试计划

## 已覆盖

- 评分溯源剔除未来因子：`tests/backtest/test_v322_score_provenance.py`
- 市场规则和撮合：`tests/backtest/test_v322_market_rules_execution.py`
- 仓位、资金和退出策略：`tests/backtest/test_v322_money_position_exit.py`
- 历史筛选快照和策略适配：`tests/backtest/test_v322_snapshot_suitability.py`
- 人工确认队列：`tests/trading/test_v322_human_confirm_queue.py`
- API 中文文档、规则、readiness、快照、确认队列：`tests/api/test_v322_api.py`
- 筛选页策略库兜底：`tests/front/test_v322_screener_strategy_selector.py`

## 建议继续补

- 对真实行情源失败场景增加 Playwright 截图回归。
- 对 `/realtime-paper` 页面增加人工确认操作的前端测试。
- 对回测买卖流水完整窗口增加横向滚动和列宽测试。
- 对休市后缓存不刷新、控制台静默增加端到端测试。
