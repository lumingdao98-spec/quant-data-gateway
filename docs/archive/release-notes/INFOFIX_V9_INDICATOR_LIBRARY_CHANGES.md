# V3.8 / InfoFix V9 指标知识库完整融入版

本版把用户指定技术指标文章中的“量价时空、指标分类、公式、评判标准、应用场景”落到系统中，不再只是简单加入几个指标名称。

## 1. 新增指标知识库

新增 `quant_data/services/technical_indicator_library.py`：

- 每个指标包含：名称、分类、量价时空维度、公式、评判标准、应用场景、适用场景、使用限制、是否已实现。
- 新增接口：
  - `/api/technical/indicators`
  - `/api/technical/indicators/by-category`
- 当前覆盖 53 个指标/工具，其中 48 个为可计算或可估算，5 个因需要 Level-2、Tick、期权或组合回测数据而作为知识库提示。

## 2. 新增/补全计算指标

新增或补全：

- SAR 抛物线转向
- BIAS 乖离率
- VR 成交量变异率
- RVI 相对波动指数
- PMO 价格动量振荡器
- PPO 价格振荡器
- PMI 价格动量指数
- VMI 成交量动量
- VO 成交量振荡器
- A/D Line 累积派发线
- PSY 心理线
- BRAR 情绪指标
- CYR 市场强弱
- Ichimoku 一目均衡表
- Fibonacci 回调
- Fibonacci 时间窗口
- TD Sequential TD序列
- Pivot Points 枢轴点
- 价格形态初步识别
- ZigZag 波段点
- 价格波动率与成交量波动率

保留并继续使用：MA、EMA、MACD、RSI、KDJ、BOLL、ATR、VWAP、WR、CCI、ROC、MOM、OBV、MFI、ADX、DMI、支撑阻力、价格通道等。

## 3. 筛选评分升级

新增两个评分维度：

- 时间分：TD、斐波时间、PSY、BRAR、CYR
- 形态分：价格形态、斐波回调、Pivot、ZigZag

综合评分由原来的低位、趋势、动量、量能、波动空间、资金强度、盘口行为、估值流动性、风险扣分，扩展为：

```text
低位 + 趋势 + 动量 + 量能 + 波动空间 + 资金强度 + 盘口行为 + 时间周期 + 形态空间 + 估值流动性 - 风险扣分
```

## 4. 标签解释修复

`/api/screener/explain/{symbol}` 现在会返回：

- 当前标签对应的指标知识库条目
- 公式
- 评判标准
- 应用场景
- 使用限制
- 当前个股指标矩阵
- 当前个股指标信号清单

用于修复“标签解释没有数据”的问题。

## 5. 策略库新增

新增策略项：

- SAR趋势跟随
- BIAS乖离修复
- VR/MFI能量共振
- TD/斐波时间窗口
- 斐波/Pivot空间结构
- 一目均衡云图
- 形态/ZigZag结构
- PSY/BRAR情绪温度

## 6. 重要说明

Order Book、Tick、VIX、Put/Call Ratio 等需要 Level-2、逐笔成交、期权或海外宏观数据，当前公开免费源无法严谨实现，系统已作为知识库提示并避免直接参与确定性结论。
