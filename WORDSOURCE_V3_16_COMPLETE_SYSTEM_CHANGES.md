# V3.16 / WordSource V1 完整系统代码包

本版不是占位框架，而是在 V16.4 基础上把上传的四个 Word 文档要求落成可运行服务、API 与测试。

## 新增完整服务

- `source_registry.py`：官方/专业/门户/社区源分层，搜索引擎结果页永久禁用，按有效证据数规划抓取。
- `candidate_pool_service.py`：三通道候选池，换手率 TOP50、成交额 TOP20、技术初筛，去重并保留通道证据。
- `technical_factor_registry.py`：50+ 技术因子库，每项包含公式原理、参数、看多/看空规则、应用场景、评分角色、风险规则。
- `capital_flow_service.py`：资金面独立评分，基于成交额强度、量比、近5日资金连续性，不伪造 Level-2。
- `style_classifier.py`：市值/流通盘/ETF/低估值/高弹性等风格分类。
- `theme_lifecycle_service.py`：题材关键词识别与启动/发酵/高潮/分歧/低热度阶段判断。
- `market_regime_service.py`：用市场快照估算牛熊/震荡体制。
- `position_risk_service.py`：模拟风控建议、单票仓位上限、ATR/支撑位止损参考。
- `strategy_signal_service.py`：趋势跟踪、均值回归、动量、事件驱动、波动率突破观察、网格/波段等可运行策略信号对象。
- `diagnosis_engine.py`：脚本判定 vs 复核建议；无政策证据时不会硬判政策驱动。
- `data_quality_service.py`：行情/K线/新闻质量评分，记录缺失、异常跳变、未知时间、事件唯一性。
- `feature_store_service.py`：SQLite Feature Store，保存综合报告特征。
- `macro_policy_event_service.py`：宏观/政策事件识别与行业影响链。
- `research_sentiment_service.py`：研报评级/目标价/盈利预测文本解析，社区舆情正负/分歧/传闻风险。
- `wordsource_system_service.py`：统一编排以上服务，输出完整个股综合报告。

## 新增 API

- `GET /api/wordsource/coverage`
- `GET /api/wordsource/report/{symbol}`
- `GET /api/wordsource/candidates`

## 筛选系统增强

`screener_service.py` 的每个筛选结果新增：

- `wordsource_report`
- 四面评分：技术面、基本面、信息面、资金面
- 资金/风格/题材/风控/策略信号/数据质量/诊断引擎结果

## 测试

新增 `tests/test_wordsource_v316.py`，覆盖：

- 信息源注册与搜索页禁用
- 50+ 技术因子库字段完整性
- 三通道候选池
- WordSource 综合报告完整性

本地验证：

```bash
PYTHONPATH=. pytest -q
# 28 passed
```
