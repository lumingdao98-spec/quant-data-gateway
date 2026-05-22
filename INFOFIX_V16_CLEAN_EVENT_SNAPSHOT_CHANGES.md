# V3.15 / InfoFix V16 信息源清洗、事件簇去重与三维评分一致性修复版

本版基于 V3.14 / InfoFix V15 继续增量开发，未从零重写，保留实时行情、分时图、日/周/月K、复权口径、技术指标矩阵、策略筛选、信息面详情、全球要闻、公司画像、ETF画像、事件去重、舆情观察、回撤校验、多源兜底和信息面评分融合等已有功能。

## 主要改动

1. 新增 `quant_data/services/news_cleaner.py`
   - 新增 `valid_news_item`，统一拦截页头、页脚、导航、JS/CSS、广告、搜索结果页、table/comment/html 残片。
   - 新增 `strip_html_boilerplate`，对新浪、同花顺、东方财富股吧等 HTML 片段进行入库/展示前清洗。
   - 新增 `extract_time_fields`，明确输出 `publish_time`、`event_time`、`crawl_time`、`time_confidence`、`time_basis`、`event_type`、`period`、`document_id`。

2. 强化 `quant_data/services/news_service.py`
   - 抓取链路中加入有效新闻判定，减少“桌面快捷方式、关于同花顺、软件下载、Copyright、header.js、div class”等脏数据进入详情页或评分。
   - `_score_item` 不再把未来会议日期当作新闻发布时间；时效权重只按 `publish_time` 计算。
   - 事件级去重优先使用 `document_id` / `issuer + event_type + period + event_date`，同一股东大会、财报、分红、监管、订单等事件跨 F10/新浪/同花顺/股吧合并为一个事件簇。
   - 全球要闻继续独立短缓存刷新，进入个股评分前仍由行业/业务相关性映射控制。

3. 强化 `quant_data/services/news_store_service.py`
   - SQLite 表新增并迁移 `publish_time/event_time/crawl_time/time_confidence/time_basis/event_type/issuer/period/document_id`。
   - 入库前二次调用 `valid_news_item`，防止历史脏数据和 HTML 残片继续污染详情页。
   - 分页读取时返回新的时间字段和事件字段，支持详情页展示事件证据链。

4. 修复 `quant_data/api.py`
   - 筛选页和详情页统一 `snapshot_id` 与 `info_limit`，筛选页生成的详情入口会携带同一口径。
   - 筛选页不再返回长篇新闻列表，只保留摘要、统计和 `detail_url`。
   - `/api/technical/drawdown/verify/{symbol}` 输出 `symbol、adjust、limit、last_close、high_250、low_250、drawdown250、data_source、bars_count、basis` 等校验字段。

5. 修复行情/K线兜底
   - `provider_manager.py` 对日/周/月复权K线先严格按指定复权口径跨源兜底，避免东方财富 qfq 失败后直接拿不复权数据冒充 qfq。
   - `market_data_service.py` 如必须使用旧版不复权缓存，会在 source 中标记 `unadjusted_fallback_for_qfq/hfq`，便于回撤校验发现数据质量风险。

6. 前端更新
   - `screener_ui.py`：筛选页只保留信息面详情入口，携带 `snapshot_id` 和 `limit`。
   - `info_ui.py`：详情页显示 `publish_time / event_time / crawl_time`，并展示事件类型、周期和去重键。

## 新增测试

新增 `tests/test_infofix_v16.py`，覆盖：

- 有效新闻过滤；
- `publish_time/event_time/crawl_time` 拆分；
- 同一事件跨来源标题差异合并；
- 入库前清洗；
- 回撤公式；
- `snapshot_id` 接口契约。

本地验证：

```bash
PYTHONPATH=. pytest -q
# 10 passed
```

## 运行方式

```bash
pip install -r requirements.txt
python -m uvicorn quant_data.api:app --host 127.0.0.1 --port 8001
```

打开：

- 筛选页：http://127.0.0.1:8001/screener
- 信息面详情页：http://127.0.0.1:8001/info
- 行情页：http://127.0.0.1:8001/ui

## 验证建议

1. 在筛选页启用“信息面评分”，检查返回行只展示摘要与“打开信息面分析详情页”入口。
2. 对天合光能等标的强制刷新信息面，确认“桌面快捷方式/关于同花顺/header.js/div class/Copyright”等内容不再入库。
3. 在详情页查看同一股东大会事件是否只保留一个主事件，相关转载与社区内容进入同事件簇说明。
4. 调用 `/api/technical/drawdown/verify/600519?adjust=qfq&limit=260` 检查回撤口径和数据源标记。
