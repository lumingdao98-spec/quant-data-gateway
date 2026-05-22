# V3.15 / InfoFix V16.4 Word 源文档逐项落地修复版

本版修正 V16.3 的问题：不能只凭片段或截图摘要硬编码，必须把用户上传的 Word 文档真正读入系统。

## 已读入的 Word 源

- 炒股-消息面分析.docx
- 炒股-技术面分析.docx
- 炒股-风格与分析.docx
- 炒股-量化相关.docx

系统已把全文抽取到：

- `quant_data/data/source_docs/message.txt`
- `quant_data/data/source_docs/technical.txt`
- `quant_data/data/source_docs/style.txt`
- `quant_data/data/source_docs/quant.txt`

结构化框架写入：

- `quant_data/data/word_source_knowledge.json`

## 关键新增

1. 新增 `SourceKnowledgeService`，统一读取 Word 来源知识。
2. 新增接口：
   - `/api/source-knowledge/coverage`
   - `/api/source-knowledge`
   - `/api/source-knowledge/doc/{key}`
3. 技术指标接口返回 `word_source_catalog`，不再只看硬编码指标库。
4. TraderCore 诊断加入 Word 源覆盖信息、截图三通道候选、20/45/35 三层评分、MA20偏离和5日振幅判断。
5. 新增测试验证：Word 源已完整抽取、50项技术指标来自 Word 表格、消息/风格/量化框架完整进入系统。

## 注意

本版仍不会伪造不可获得的数据。Level-2、逐笔、期权、外部终端专属数据会标为待接入或知识库项。
