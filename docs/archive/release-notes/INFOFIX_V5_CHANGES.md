# 信息面修复 V5 合并说明

本版本已直接修改项目源码，不再依赖外置补丁。

## 主要修改

1. 成交量单位修正
   - 后端统一约定 `volume` 为“手”，`amount` 为“元”。
   - `Quote`、`Bar`、`IntradayPoint` 的 `to_dict()` 新增：
     - `volume_unit`
     - `volume_hand`
     - `volume_shares`
     - `volume_display`
     - `amount_unit`
     - `amount_yuan`
     - `amount_display`

2. 新闻标签体系重构
   - `NewsItem` 新增：
     - `event_label`
     - `sentiment_label`
     - `impact_scope`
     - `impact_direction`
     - `risk_tag`
   - “持股人收益受损/持有人收益受损/股东权益受损/投资者利益受损”单独归类为“持有人权益受损”，不再误判为“业绩亏损”。

3. 编码与乱码修复
   - 新闻文本清洗新增不可见字符处理。
   - 可选使用 `ftfy` 修复常见乱码。
   - `requirements_full.txt` 已新增 `ftfy>=6.2.0`。

4. 全球/国内要闻
   - 新增接口：`GET /api/news/global?limit=80&force=false`
   - 默认短缓存 60 秒。
   - `force=true` 强制刷新。
   - 多源聚合财联社、东方财富全球快讯、新浪财经 7x24；失败时走中文新闻搜索兜底。

5. 公司简介
   - 新增 `CompanyProfileService`。
   - 新增接口：`GET /api/company/profile/{symbol}?force=false`
   - 优先使用巨潮资讯公司概况，补充东方财富个股基础信息。

6. 股票总览接口
   - 新增接口：`GET /api/stock/overview/{symbol}?force=false`
   - 返回行情、公司简介、个股信息面、全球/国内要闻。

7. 筛选页展示修复
   - 标签支持换行、自动撑开，不再不可读。
   - 个股新闻卡片展示事件、风险、情绪、影响方向、影响范围。
   - 信息面区域新增公司简介。
   - 右侧新增全球/国内要闻板块，可手动刷新。

## 验证

已执行：

```bash
python -m compileall -q quant_data tests
PYTHONPATH=. pytest -q
```

测试结果：`1 passed`。
