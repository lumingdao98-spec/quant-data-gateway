# Quant Data Gateway V2.8 - K线容灾、信息库、标签解释与融合评分增强版

本版本在 V2.6 基础上继续完善信息面与筛选解释能力：

1. **信息面持久化入库**：中文新闻、公告、社区信息会写入 `data/news_store.sqlite`，短时间重复筛选会复用信息库与分析缓存，减少重复爬取。
2. **新闻日期与数据质量增强**：新闻/公告条目显示发布时间、日期归一化、未知日期数量、官方/高可信数量、负面证据数量。
3. **公告正文轻量读取**：对公开可访问的公告链接低频读取正文片段，辅助判断利多/利空；不登录、不绕过验证码。
4. **财报风险与新闻负面分开统计**：新闻负面只统计新闻/公告文本情绪；财报亏损、动态PE异常等作为“信息面负面证据”单独计入融合评分。
5. **信息库接口**：新增 `/api/info/items/{symbol}` 与 `/api/info/store/stats`，可以查看本地已保存的信息条目和缓存规模。
6. **标签解释接口**：新增 `/api/screener/explain/{symbol}?tag=...`，可查看每个命中标签的判断逻辑、指标对比和未来K线标注预留信息。
7. **筛选页交互增强**：命中标签和风险标签可点击查看解释，近期中文信息列表显示日期、证据和正文读取状态。

## 运行方式

```bat
cd quant_data_gateway_v2_7_info_store_explain
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
run_app_auto.bat
```

或手动启动：

```bat
python main.py api --host 127.0.0.1 --port 8000 --auto-port
```

## 页面入口

- 行情监控：http://127.0.0.1:8000/ui
- 筛选模块：http://127.0.0.1:8000/screener
- API文档：http://127.0.0.1:8000/docs

## 新增接口

```text
GET /api/info/items/601606?limit=80&history_days=3650
GET /api/info/store/stats?symbol=601606
GET /api/screener/explain/601606?tag=近一年低位
```

## 安全与效率说明

- 本系统当前定位为研究和辅助分析工具，不构成投资建议。
- 中文信息源仅抓取公开页面，不做验证码绕过，不做登录态突破。
- 若部分网站需要登录才能看完整内容，系统会保留标题/摘要级信息；后续可在配置文件里支持用户手动提供 Cookie，但默认不启用。
- 自定义 Python 策略当前仍只做结构校验，不直接执行，避免本地文件、网络、系统命令等安全风险。
- 进入模拟交易与自动化交易前，应先完成回测、模拟盘、风控开关、异常断线保护和交易日志模块。
