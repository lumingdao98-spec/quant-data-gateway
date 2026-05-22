# Quant Data Gateway V3.16 / WordSource V1 完整系统版

本系统面向 A股/ETF 量化交易自动化底座：数据采集、清洗、因子计算、三/四面评分、候选池、信息面证据、技术因子库、资金风格、策略信号与风控建议。

## 运行

```bash
pip install -r requirements.txt
python -m uvicorn quant_data.api:app --host 127.0.0.1 --port 8001
```

页面：

- `http://127.0.0.1:8001/screener`
- `http://127.0.0.1:8001/info`
- `http://127.0.0.1:8001/ui`

新增接口：

- `/api/wordsource/coverage`：查看 Word 文档映射后的信息源、技术因子和系统覆盖度。
- `/api/wordsource/report/600438?force=true&info_limit=180`：输出单票完整报告。
- `/api/wordsource/candidates?max_pages=3&page_size=100&max_items=120`：输出三通道候选池。

## V3.16 核心

1. 信息面不再按原始抓取数停止，而是按清洗后的有效证据数规划。
2. 搜索引擎结果页永久禁用，不作为新闻证据。
3. 50+ 技术因子库具备公式、参数、评判规则、应用场景、评分角色和风险规则。
4. 筛选从“评分列表”升级为“三通道候选池 → 四面评分 → 诊断复核”。
5. 资金面独立成面，不再只混在技术指标里。
6. 风格、市值、题材生命周期、大盘环境、模拟风控建议已可运行。
7. 策略信号输出统一对象，为 V4 回测和 V5 模拟交易衔接。
8. 对 Level-2、Tick、实盘券商等没有真实授权的数据，系统明确不伪造。

## 测试

```bash
PYTHONPATH=. pytest -q
```

当前通过：`28 passed`。
