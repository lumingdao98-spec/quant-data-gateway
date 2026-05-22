from __future__ import annotations


def build_screener_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Quant Data Gateway V3.15.3 - 三通道候选/50项技术/信息源扩展</title>
<style>
:root{--bg:#0b1020;--panel:#101827;--panel2:#151f34;--line:#283956;--text:#dbeafe;--muted:#8ea3c3;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b;--purple:#a78bfa;--shadow:0 18px 48px rgba(0,0,0,.28)}
*{box-sizing:border-box}html,body{height:100%;margin:0}body{background:var(--bg);color:var(--text);font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;overflow:hidden}.app{height:100vh;display:grid;grid-template-rows:52px 1fr 120px;grid-template-columns:320px 1fr 360px;grid-template-areas:"top top top" "left main right" "log log log";gap:0}.top{grid-area:top;background:#111827;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;padding:0 14px}.left{grid-area:left;background:#0f172a;border-right:1px solid var(--line);padding:14px;overflow:auto}.main{grid-area:main;padding:12px;overflow:hidden;display:flex;flex-direction:column;gap:10px}.right{grid-area:right;background:#0f172a;border-left:1px solid var(--line);padding:12px;overflow:auto}.log{grid-area:log;background:#0f172a;border-top:1px solid var(--line);padding:8px 12px;overflow:auto;font-family:Consolas,monospace;font-size:12px;color:#a8bbd8}.brand{font-weight:900;color:#bfdbfe;font-size:16px;display:flex;align-items:center;gap:8px}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 16px var(--green)}.pill{display:inline-flex;align-items:center;border:1px solid #30405d;background:#1f2a44;color:#bfdbfe;border-radius:999px;padding:5px 9px;font-size:12px}.pill.green{color:#86efac;border-color:#166534;background:#112e21}.pill.yellow{color:#fcd34d;border-color:#854d0e;background:#2a2112}.grow{flex:1}.card{background:rgba(16,24,39,.98);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);overflow:hidden}.card-h{height:46px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;border-bottom:1px solid var(--line);background:#141e32}.card-title{font-weight:900}.card-b{padding:12px}.section-title{font-size:13px;color:#93a4c1;margin:12px 0 7px}.row{display:flex;gap:8px;align-items:center}.row.wrap{flex-wrap:wrap}input,select,textarea{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px 11px;outline:none}textarea{min-height:86px;resize:vertical;line-height:1.45}input:focus,select:focus,textarea:focus{border-color:#60a5fa;box-shadow:0 0 0 3px rgba(59,130,246,.12)}button{background:#2563eb;color:#fff;border:0;border-radius:10px;padding:9px 12px;cursor:pointer;font-weight:800;white-space:nowrap}button:hover{background:#1d4ed8}button:disabled{opacity:.45;cursor:not-allowed}.btn2{background:#243145;color:#c7d2fe}.btn2:hover{background:#30405d}.btn-green{background:#16a34a}.btn-green:hover{background:#15803d}.btn-red{background:#991b1b}.btn-red:hover{background:#7f1d1d}.check{display:flex;gap:8px;align-items:center;margin:8px 0;font-size:13px;color:#cbd5e1}.check input{width:auto}.hint{font-size:12px;color:#9fb2d4;line-height:1.55;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}.summary{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.metric{background:#172033;border:1px solid #26364f;border-radius:12px;padding:9px;min-width:0}.metric .k{font-size:11px;color:#8ea3c3}.metric .v{font-size:18px;font-weight:900;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.table-wrap{flex:1;min-height:0;overflow:auto;border:1px solid var(--line);border-radius:14px;background:#0f172a}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px 8px;border-bottom:1px solid rgba(38,54,79,.8);text-align:right;white-space:nowrap}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}th{position:sticky;top:0;background:#182238;color:#93c5fd;z-index:1;cursor:pointer}tbody tr{cursor:pointer}tbody tr:hover{background:#1e293b}.selected{background:#233555!important}.up{color:var(--red)}.down{color:var(--green)}.flat{color:#cbd5e1}.muted{color:var(--muted)}.small{font-size:12px;color:var(--muted)}.tag{display:inline-block;padding:2px 6px;border-radius:999px;background:#1f2a44;color:#bfdbfe;border:1px solid #30405d;font-size:11px;margin:1px;cursor:pointer}.tag:hover{filter:brightness(1.25);border-color:#60a5fa}.explain-box{position:fixed;right:390px;top:72px;width:420px;max-height:72vh;overflow:auto;background:#0b1224;border:1px solid #40608f;border-radius:16px;box-shadow:0 22px 60px rgba(0,0,0,.45);z-index:99;padding:14px;display:none}.explain-box h3{margin:0 0 8px}.explain-box .x{float:right;background:#243145;padding:4px 8px}.explain-metric{display:grid;grid-template-columns:118px 1fr;gap:8px;border-top:1px solid #26364f;padding:6px 0;font-size:12px}.tag.risk{color:#fecaca;border-color:#7f1d1d;background:#2a1111}.score{font-weight:900}.score.a{color:#fbbf24}.score.b{color:#22c55e}.score.c{color:#93c5fd}.score.d{color:#94a3b8}.detail-title{font-size:20px;font-weight:900}.kv{display:grid;grid-template-columns:1fr 1fr;gap:8px}.kv .item{background:#101a2e;border:1px solid #26364f;border-radius:10px;padding:8px}.kv span{display:block;font-size:11px;color:#8ea3c3}.kv b{display:block;margin-top:3px;text-align:right}.bar{height:8px;background:#0b1224;border-radius:999px;overflow:hidden;border:1px solid #26364f}.bar i{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#3b82f6,#f59e0b);width:0}.quick{display:grid;grid-template-columns:1fr 1fr;gap:7px}.quick button{font-size:12px;padding:8px 9px;text-align:left;background:#172033;color:#bfdbfe;border:1px solid #26364f}.quick button:hover{background:#1f2a44}.err{color:#fecaca}.ok{color:#86efac}@media(max-width:1200px){.app{grid-template-columns:300px 1fr;grid-template-areas:"top top" "left main" "log log"}.right{display:none}.summary{grid-template-columns:repeat(3,1fr)}}
.trend-box{height:150px;background:#0b1225;border:1px solid #26364f;border-radius:12px;margin-top:8px;padding:8px;position:relative}.trend-canvas{width:100%;height:100%;display:block}.trend-empty{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8ea3c3;font-size:12px}.btn-red{background:#b91c1c}.btn-red:hover{background:#991b1b}
.strategy-grid{display:grid;grid-template-columns:1fr;gap:7px;max-height:230px;overflow:auto}.strategy-card{background:#101a2e;border:1px solid #26364f;border-radius:10px;padding:8px;font-size:12px}.strategy-card label{display:flex;gap:7px;align-items:flex-start}.strategy-card input{width:auto;margin-top:2px}.strategy-card b{color:#dbeafe}.strategy-card p{margin:4px 0 0;color:#9fb2d4;line-height:1.35}.codebox{font-family:Consolas,monospace;font-size:12px;min-height:90px}.info-list{display:flex;flex-direction:column;gap:6px}.info-row{display:grid;grid-template-columns:82px 1fr 46px;gap:6px;align-items:center;font-size:12px}.mini-bar{height:8px;background:#0b1224;border:1px solid #26364f;border-radius:999px;overflow:hidden}.mini-bar i{display:block;height:100%;background:#60a5fa;width:0}.news-item{font-size:12px;line-height:1.35;border-top:1px solid rgba(38,54,79,.75);padding:6px 0}.news-item a{color:#bfdbfe;text-decoration:none}.news-item a:hover{text-decoration:underline}.bad{color:#fecaca}.good{color:#86efac}

.tag{max-width:100%;white-space:normal;word-break:break-word;overflow-wrap:anywhere;line-height:1.45}.tag.event{background:#172554;border-color:#1d4ed8;color:#bfdbfe}.tag.scope{background:#2e1065;border-color:#6d28d9;color:#ddd6fe}.tag.good{background:#052e16;border-color:#166534;color:#bbf7d0}.news-item{background:#0d1428;border:1px solid rgba(38,54,79,.75);border-radius:10px;padding:8px;margin:7px 0;overflow:hidden}.news-title{font-weight:800;color:#bfdbfe;text-decoration:none;line-height:1.45;white-space:normal;word-break:break-word;overflow-wrap:anywhere}.news-meta{margin-top:5px;font-size:12px;color:#8ea3c3;line-height:1.45}.news-summary{margin-top:6px;font-size:12px;color:#9fb2d4;line-height:1.55;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;white-space:normal;word-break:break-word;overflow-wrap:anywhere}.profile-box{background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:9px;margin:8px 0;line-height:1.55;white-space:normal;word-break:break-word;overflow-wrap:anywhere}.global-news-head{display:flex;align-items:center;justify-content:space-between;gap:8px}.global-news-head button{font-size:11px;padding:5px 7px}

.strategy-mini{background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.strategy-mini .row{justify-content:space-between}.strategy-summary-tags{margin-top:8px;max-height:74px;overflow:auto}.modal-backdrop{position:fixed;inset:0;background:rgba(2,6,23,.72);z-index:120;display:none;align-items:center;justify-content:center;padding:18px}.modal-backdrop.show{display:flex}.strategy-modal{width:min(1060px,96vw);height:min(760px,92vh);background:#0f172a;border:1px solid #41618e;border-radius:18px;box-shadow:0 28px 80px rgba(0,0,0,.55);display:flex;flex-direction:column;overflow:hidden}.strategy-modal-h{height:54px;display:flex;align-items:center;gap:10px;justify-content:space-between;padding:0 14px;border-bottom:1px solid #283956;background:#141e32}.strategy-modal-b{padding:12px;overflow:hidden;display:flex;flex-direction:column;gap:10px;min-height:0}.strategy-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.strategy-tabs{display:flex;gap:6px;flex-wrap:wrap}.strategy-tabs button{font-size:12px;padding:6px 9px;background:#172033;border:1px solid #26364f;color:#bfdbfe}.strategy-tabs button.active{background:#2563eb;color:#fff;border-color:#60a5fa}.strategy-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:9px;max-height:none;overflow:auto;min-height:0}.strategy-modal .strategy-grid{flex:1}.strategy-card{background:#101a2e;border:1px solid #26364f;border-radius:12px;padding:10px;font-size:12px}.strategy-card .cat-title{font-size:14px;color:#bfdbfe;font-weight:900;margin-bottom:6px}.strategy-card label{display:flex;gap:8px;align-items:flex-start;padding:6px 4px;border-top:1px solid rgba(38,54,79,.45)}.strategy-card label:first-of-type{border-top:0}.strategy-card input{width:auto;margin-top:2px}.strategy-card b{color:#dbeafe}.strategy-card p{margin:3px 0 0;color:#9fb2d4;line-height:1.35}.strategy-card .meta{color:#8ea3c3;font-size:11px;margin-top:2px}.adjust-note{background:#102037;border:1px solid #27548b;color:#bfdbfe;border-radius:10px;padding:8px;font-size:12px;line-height:1.45}

</style>
</head>
<body>
<div class="app">
  <div class="top">
    <div class="brand"><span class="dot"></span>量化数据网关 V3.15.2 · 深度清洗/舆情研报/snapshot</div>
    <span class="pill green">保留V1.9行情/分时/K线详情</span>
    <span class="pill yellow">筛选评分仅作研究辅助</span>
    <div class="grow"></div>
    <button class="btn2" onclick="location.href='/ui'">行情监控</button>
    <button class="btn2" onclick="openSelectedDetail()">打开选中详情</button>
  </div>

  <aside class="left">
    <div class="section-title">筛选范围</div>
    <select id="universe">
      <option value="custom">自定义股票池 / 自选池</option>
      <option value="stocks">A股股票快照</option>
      <option value="etf">ETF快照</option>
      <option value="market">股票 + ETF快照</option>
    </select>
    <div class="section-title">自定义代码，逗号或换行分隔</div>
    <textarea id="symbols">300750,600519,000001,159915,510300,512100</textarea>
    <div class="quick" style="margin-top:8px">
      <button onclick="setPool('300750,600519,000001,159915,510300,512100')">常用验证池</button>
      <button onclick="setPool('300750,002594,601012,688599,300274,600438')">新能源观察</button>
      <button onclick="setPool('159915,510300,512100,512880,588000,513050')">ETF观察池</button>
      <button onclick="savePool()">保存自选池</button>
    </div>

    <div class="section-title">筛选模式</div>
    <select id="mode">
      <option value="balanced">综合平衡：低位 + 趋势 + 量价 + 风险</option>
      <option value="low_position">低位修复优先：回撤充分 + 均线修复</option>
      <option value="oversold_rebound">超跌反弹观察：低位 + RSI修复</option>
      <option value="trend_volume">趋势放量优先：均线/MACD + 量价</option>
      <option value="short_swing">短线强势/异动：动量 + 放量</option>
      <option value="value_quality">价值质量稳健：估值/流动性更高权重</option>
      <option value="risk_averse">保守风控优先：风险扣分更严格</option>
      <option value="info_fusion">信息面融合优先：配合新闻/公告/财报二次评分</option>
      <option value="etf">ETF关注模式：弱化PE/PB</option>
    </select>
    <div class="hint" style="margin-top:8px">筛选模式 = 大类权重模板；策略组合 = 具体因子加减分。建议先选一个模式，再多选策略因子，系统会输出总分、标签和风险提示。</div>

    <div class="section-title">策略组合 <span class="small">可多选</span></div>
    <div class="strategy-mini">
      <div class="row"><button class="btn2" onclick="openStrategyModal()">打开分类策略选择器</button><span id="strategyCount" class="pill">加载中</span></div>
      <div id="strategySummary" class="strategy-summary-tags small">策略库加载中...</div>
    </div>
    <label class="check"><input id="enableNews" type="checkbox"> 启用信息面评分（公告/公司/宏观/行业/资金/国际/舆情分层；搜索引擎页彻底禁用）</label>
    <div class="section-title">自定义策略 Python 代码</div>
    <textarea id="customCode" class="codebox" placeholder="示例：
def score(context):
    # context 包含 quote、bars、indicators 等，后续版本会开放安全沙箱执行
    return {'score': 60, 'tags': ['自定义观察']}
"></textarea>
    <div class="row" style="margin-top:8px"><button class="btn2" onclick="validateCustomCode()">检查代码结构</button><span id="codeStatus" class="small">当前为接口预留，默认不执行任意代码</span></div>

    <div class="section-title">参数控制</div>
    <div class="grid2">
      <div><div class="small">最多分析</div><input id="maxItems" type="number" value="30" min="1" max="500"></div>
      <div><div class="small">最低评分</div><input id="minScore" type="number" value="45" min="0" max="100"></div>
      <div><div class="small">快照页数</div><input id="maxPages" type="number" value="1" min="1" max="50"></div>
      <div><div class="small">每页数量</div><input id="pageSize" type="number" value="100" min="20" max="500"></div>
      <div><div class="small">K线数量</div><input id="klineLimit" type="number" value="260" min="80" max="520"></div>
      <div><div class="small">复权口径</div><select id="klineAdjust"><option value="qfq" selected>前复权-推荐筛选</option><option value="none">不复权-原始走势</option><option value="hfq">后复权-长期复盘</option></select></div>
      <div><div class="small">最低成交额(万元)</div><input id="minAmountWan" type="number" value="0" min="0"></div>
      <div><div class="small">信息面抓取上限</div><input id="infoLimit" type="number" value="180" min="30" max="500"></div>
    </div>
    <label class="check"><input id="includeStocks" type="checkbox" checked> 包含股票</label>
    <label class="check"><input id="includeEtf" type="checkbox" checked> 包含ETF</label>
    <label class="check"><input id="forceQuotes" type="checkbox"> 强制刷新实时行情</label>
    <label class="check"><input id="forceKline" type="checkbox"> 强制刷新K线，不建议大批量开启</label>
    <div class="row" style="margin-top:12px">
      <button id="runBtn" class="btn-green" onclick="runScreener()">开始筛选</button>
      <button class="btn2" onclick="clearResults()">清空</button>
    </div>
    <div class="hint" style="margin-top:12px">
当前版本保留原有行情/技术指标/公司画像功能。信息面不再在筛选页展开，只提供入口；启用信息面后会按同一抓取上限把信息面分融合进综合评分。
    </div>
  </aside>

  <main class="main">
    <div class="summary">
      <div class="metric"><div class="k">候选数量</div><div id="mCount" class="v">--</div></div>
      <div class="metric"><div class="k">分析股票数</div><div id="mUniverse" class="v">--</div></div>
      <div class="metric"><div class="k">最高评分</div><div id="mTop" class="v">--</div></div>
      <div class="metric"><div class="k">平均评分</div><div id="mAvg" class="v">--</div></div>
      <div class="metric"><div class="k">耗时</div><div id="mTime" class="v">--</div></div>
      <div class="metric"><div class="k">错误数</div><div id="mErr" class="v">--</div></div>
    </div>
    <div class="card" style="flex:1;display:flex;flex-direction:column;min-height:0">
      <div class="card-h"><div class="card-title">筛选结果</div><div class="small">点击表头可排序，点击行可查看右侧摘要</div></div>
      <div class="table-wrap">
        <table id="resultTable">
          <thead>
            <tr>
              <th data-k="symbol">代码</th><th data-k="name">名称</th><th data-k="total_score">总分</th><th data-k="grade">等级</th><th data-k="last">最新</th><th data-k="change_pct">涨跌%</th><th data-k="amount">成交额</th><th data-k="pos250">250日位置</th><th data-k="drawdown250">高位回撤(复权)</th><th data-k="low_score">低位</th><th data-k="trend_score">趋势</th><th data-k="momentum_score">动量</th><th data-k="volume_score">量能</th><th data-k="volatility_score">波动/空间</th><th data-k="strength_score">资金强度</th><th data-k="value_score">估值/流动</th><th data-k="risk_penalty">风险扣分</th><th>核心标签</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </main>

  <aside class="right">
    <div class="detail-title" id="dTitle">未选择标的</div>
    <div class="small" id="dSub">运行筛选后点击结果行</div>
    <div style="margin:12px 0" class="bar"><i id="scoreBar"></i></div>
    <div class="row wrap" style="margin-bottom:10px">
      <button class="btn2" onclick="openSelectedDetail()">打开分时/K线详情</button>
      <button class="btn-green" onclick="addSelectedToMonitor()">加入实时监测</button>
      <button class="btn2" onclick="jumpSelectedToMonitor()">加入并跳转</button>
      <button class="btn2" onclick="appendSelectedToPool()">加入筛选池</button>
    </div>
    <div class="kv" id="detailKv"></div>
    <div class="section-title">命中标签</div><div id="detailTags"></div>
    <div class="section-title">风险提示</div><div id="detailRisks" class="small">--</div>
    <div class="section-title">评分趋势 <span id="trendHint" class="small">按天记录</span></div>
    <div class="trend-box"><canvas id="trendCanvas" class="trend-canvas"></canvas><div id="trendEmpty" class="trend-empty">暂无评分历史，运行筛选后自动记录</div></div>
    <div class="section-title">综合判断</div><div id="detailReason" class="hint">--</div>
    <div class="section-title">信息面详情</div>
    <div id="infoNewsList" class="hint"><button class="btn2" onclick="openInfoDetailPage()">打开信息面分析详情页</button><div class="small" style="margin-top:8px">筛选页只保留综合判断和入口；新闻明细、全球要闻、统计图、去重组、来源诊断请进入详情页查看。</div></div>
    <div id="infoPanel" style="display:none"></div>
    <div id="infoCategories" style="display:none"></div>
    <div id="globalNewsList" style="display:none"></div>
  </aside>

  <div class="log" id="log"></div>
</div>
<div id="explainBox" class="explain-box">
  <button class="x" onclick="hideExplain()">关闭</button>
  <h3 id="explainTitle">标签解释</h3>
  <div id="explainBody" class="small">请选择标签</div>
</div>

<div id="strategyModal" class="modal-backdrop" onclick="if(event.target===this)closeStrategyModal()">
  <div class="strategy-modal">
    <div class="strategy-modal-h">
      <div><b>分类策略选择器</b><div class="small">按低位、趋势、量价、宏观大势、基本面财务、消息面事件驱动、回测风控等分类框选；不减少原有策略。</div></div>
      <div class="row"><button class="btn2" onclick="selectDefaultStrategies()">默认组合</button><button class="btn2" onclick="selectAllStrategies(true)">全选</button><button class="btn2" onclick="selectAllStrategies(false)">清空</button><button onclick="closeStrategyModal()">完成</button></div>
    </div>
    <div class="strategy-modal-b">
      <div class="adjust-note">提示：策略只是“因子组合开关”。真正评分仍由当前数据、公式、权重和风险扣分计算；宏观/基本面/消息面只作为证据链，不直接等同于买卖建议；Level-2相关主力/虚假单不会伪造，只给“需核验”提示。</div>
      <div id="strategyTabs" class="strategy-tabs"></div>
      <div id="strategyBox" class="strategy-grid"><div class="small">策略库加载中...</div></div>
    </div>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);let rows=[],selected=null,sortKey='total_score',sortDir=-1;const LS='quant_v2_watch_pool';

let strategyLibrary=[];let currentStrategyCategory='全部';let selectedStrategyKeys=new Set();let defaultStrategyKeys=new Set();
function selectedStrategies(){return Array.from(selectedStrategyKeys)}
function strategyCategories(){const order=['低位/价值','K线趋势','趋势跟随','动量/反转','量价/盘口','技术形态','支撑阻力','时间周期','能量/情绪','新闻/基本面','基本面/财务','消息面/事件驱动','宏观/大势','ETF/基金','均值回归','回测/风控/执行','风控过滤'];const cats=Array.from(new Set(strategyLibrary.map(x=>x.category||'其他')));return order.filter(x=>cats.includes(x)).concat(cats.filter(x=>!order.includes(x)).sort())}
function renderStrategyTabs(){const cats=['全部',...strategyCategories()];$('strategyTabs').innerHTML=cats.map(c=>`<button class="${c===currentStrategyCategory?'active':''}" onclick="setStrategyCategory('${htmlEsc(c)}')">${htmlEsc(c)}</button>`).join('')}
function syncStrategySelection(key,checked){if(checked)selectedStrategyKeys.add(key);else selectedStrategyKeys.delete(key);updateStrategySummary()}
function renderStrategyLibrary(){const cats={};strategyLibrary.forEach(x=>{if(currentStrategyCategory!=='全部'&&x.category!==currentStrategyCategory)return;(cats[x.category]||(cats[x.category]=[])).push(x)});$('strategyBox').innerHTML=Object.entries(cats).map(([cat,items])=>`<div class="strategy-card"><div class="cat-title">${htmlEsc(cat)} <span class="small">${items.length}项</span></div>${items.map(it=>`<label><input class="strategy-check" type="checkbox" value="${htmlEsc(it.key)}" ${selectedStrategyKeys.has(it.key)?'checked':''} onchange="syncStrategySelection('${htmlEsc(it.key)}',this.checked)"><span><b>${htmlEsc(it.name)}</b><p>${htmlEsc(it.description)}</p><div class="meta">权重 ${fmt(it.default_weight??1,1)} · ${(it.tags||[]).map(htmlEsc).join(' / ')}</div></span></label>`).join('')}</div>`).join('')||'<div class="small">该分类暂无策略</div>';updateStrategySummary()}
function setStrategyCategory(cat){currentStrategyCategory=cat;renderStrategyTabs();renderStrategyLibrary()}
async function loadStrategyLibrary(){try{const r=await fetch('/api/strategy/library',{cache:'no-store'});const js=await r.json();strategyLibrary=js.data||[];defaultStrategyKeys=new Set(strategyLibrary.filter(x=>x.enabled).map(x=>x.key));selectedStrategyKeys=new Set(defaultStrategyKeys);currentStrategyCategory='全部';renderStrategyTabs();renderStrategyLibrary()}catch(e){$('strategyBox').innerHTML='<div class="err">策略库加载失败：'+e+'</div>';if($('strategySummary'))$('strategySummary').innerHTML='<span class="err">策略库加载失败</span>'}}
function updateStrategySummary(){const sel=selectedStrategies();if($('strategyCount'))$('strategyCount').textContent=`已选 ${sel.length} 项`;if($('strategySummary')){const map=Object.fromEntries(strategyLibrary.map(x=>[x.key,x]));$('strategySummary').innerHTML=sel.length?sel.slice(0,12).map(k=>`<span class="tag">${htmlEsc(map[k]?.name||k)}</span>`).join('')+(sel.length>12?`<span class="small"> 等${sel.length}项</span>`:''):'<span class="small">未选择策略，仍按筛选模式基础评分运行</span>'}}
function openStrategyModal(){document.getElementById('strategyModal').classList.add('show');renderStrategyTabs();renderStrategyLibrary()}
function closeStrategyModal(){document.getElementById('strategyModal').classList.remove('show');updateStrategySummary()}
function selectAllStrategies(flag){selectedStrategyKeys=flag?new Set(strategyLibrary.map(x=>x.key)):new Set();renderStrategyLibrary();updateStrategySummary()}
function selectDefaultStrategies(){selectedStrategyKeys=new Set(defaultStrategyKeys);renderStrategyLibrary();updateStrategySummary()}
async function validateCustomCode(){try{const r=await fetch('/api/strategy/custom/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:$('customCode').value})});const js=await r.json();$('codeStatus').textContent=js.message+(js.warnings&&js.warnings.length?'；'+js.warnings.join('；'):'');$('codeStatus').className=js.ok?'small ok':'small err'}catch(e){$('codeStatus').textContent='检查失败：'+e;$('codeStatus').className='small err'}}

function log(msg,level='INFO'){const t=new Date().toLocaleTimeString();$('log').innerHTML+=`<div><span class="muted">${t}</span> <b>${level}</b> ${String(msg).replace(/[<>&]/g,s=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[s]))}</div>`;$('log').scrollTop=$('log').scrollHeight}
function fmt(v,d=2){if(v===null||v===undefined||Number.isNaN(Number(v)))return'--';return Number(v).toFixed(d)}
function pct(v){return v===null||v===undefined?'--':Number(v).toFixed(2)+'%'}
function money(v){v=Number(v||0);if(!v)return'--';if(v>=1e12)return(v/1e12).toFixed(2)+'万亿';if(v>=1e8)return(v/1e8).toFixed(2)+'亿';if(v>=1e4)return(v/1e4).toFixed(2)+'万';return v.toFixed(0)}
function clsPct(v){v=Number(v||0);return v>0?'up':v<0?'down':'flat'}
function scoreClass(v){v=Number(v||0);if(v>=75)return'a';if(v>=60)return'b';if(v>=45)return'c';return'd'}
function sentCN(s){const v=String(s||'').toLowerCase();return ({positive:'正面',negative:'负面',neutral:'中性'}[v]||s||'--')}
function scopeCN(s){const v=String(s||'').toLowerCase();return ({company:'个股',industry:'行业',market:'市场',macro:'宏观'}[v]||s||'--')}
function uniq(arr){return Array.from(new Set((arr||[]).filter(Boolean).map(x=>String(x))))}
function parseSymbols(){return $('symbols').value.split(/[，,\s]+/).map(s=>s.trim()).filter(Boolean).join(',')}
function setPool(s){$('symbols').value=s;savePool()}
function savePool(){localStorage.setItem(LS,$('symbols').value);log('自选池已保存')}
function buildQuery(){const p=new URLSearchParams();p.set('universe',$('universe').value);p.set('symbols',parseSymbols());p.set('mode',$('mode').value);p.set('strategies',selectedStrategies().join(','));p.set('enable_news',$('enableNews')?.checked?'true':'false');p.set('info_limit',$('infoLimit')?.value||'180');p.set('max_items',$('maxItems').value||'30');p.set('max_pages',$('maxPages').value||'1');p.set('page_size',$('pageSize').value||'100');p.set('kline_limit',$('klineLimit').value||'260');p.set('kline_adjust',$('klineAdjust')?.value||'qfq');p.set('min_score',$('minScore').value||'0');p.set('min_amount',String((Number($('minAmountWan').value)||0)*10000));p.set('include_stocks',$('includeStocks').checked?'true':'false');p.set('include_etf',$('includeEtf').checked?'true':'false');p.set('force_quotes',$('forceQuotes').checked?'true':'false');p.set('force_kline',$('forceKline').checked?'true':'false');return p}
async function runScreener(){const btn=$('runBtn');btn.disabled=true;btn.textContent='筛选中...';rows=[];render();selected=null;renderDetail(null);try{log('开始筛选，请稍候。大批量时耗时取决于公开接口和K线缓存。');const resp=await fetch('/api/screener/run?'+buildQuery().toString(),{cache:'no-store'});if(!resp.ok)throw new Error('HTTP '+resp.status);const js=await resp.json();if(!js.ok)throw new Error(js.message||'筛选失败');rows=js.data||[];log(`筛选完成：候选 ${js.result_count} / 成功分析 ${js.analyzed_count??'--'} / 股票池 ${js.pool_count??js.universe_count}，过滤 ${js.filtered_out_count??0}，耗时 ${js.elapsed_seconds}s，错误 ${js.error_count}，评分历史记录 ${js.score_history_saved??0} 条；信息面=${js.news_enabled?'启用':'未启用'}，抓取上限=${js.info_limit||'--'}，权重=${js.info_weight?Math.round(js.info_weight*100)+'%':'--'}`);if(js.errors&&js.errors.length)log('部分标的失败：'+js.errors.slice(0,5).map(e=>e.symbol+':'+e.error).join('；'),'WARN');updateMetrics(js);sortRows(false);render();if(rows[0])selectRow(rows[0].symbol)}catch(e){log(e,'ERROR')}finally{btn.disabled=false;btn.textContent='开始筛选'}}
function updateMetrics(js){$('mCount').textContent=js.result_count??rows.length;$('mUniverse').textContent=(js.analyzed_count??'--')+'/'+(js.pool_count??js.universe_count??'--');$('mTime').textContent=(js.elapsed_seconds??'--')+'s';$('mErr').textContent=js.error_count??'--';const scores=rows.map(x=>Number(x.total_score||0));$('mTop').textContent=scores.length?Math.max(...scores).toFixed(1):'--';$('mAvg').textContent=scores.length?(scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1):'--'}
function clearResults(){rows=[];selected=null;render();renderDetail(null);['mCount','mUniverse','mTop','mAvg','mTime','mErr'].forEach(id=>$(id).textContent='--')}
function sortRows(toggle=true){if(toggle)sortDir*=-1;rows.sort((a,b)=>{let av=a[sortKey],bv=b[sortKey];if(typeof av==='string')return String(av).localeCompare(String(bv),'zh')*sortDir;return ((Number(av)||0)-(Number(bv)||0))*sortDir})}
function render(){const tb=document.querySelector('#resultTable tbody');tb.innerHTML=rows.map(r=>`<tr class="${selected&&selected.symbol===r.symbol?'selected':''}" onclick="selectRow('${htmlEsc(r.symbol)}')"><td>${htmlEsc(r.symbol)}</td><td>${htmlEsc(r.name)}</td><td class="score ${scoreClass(r.total_score)}">${fmt(r.total_score,1)}</td><td>${htmlEsc(r.grade)}</td><td>${fmt(r.last)}</td><td class="${clsPct(r.change_pct)}">${pct(r.change_pct)}</td><td>${money(r.amount)}</td><td>${pct(r.pos250)}</td><td>${pct(r.drawdown250)}</td><td>${fmt(r.low_score,0)}</td><td>${fmt(r.trend_score,0)}</td><td>${fmt(r.momentum_score,0)}</td><td>${fmt(r.volume_score,0)}</td><td>${fmt(r.volatility_score,0)}</td><td>${fmt(r.strength_score,0)}</td><td>${fmt(r.value_score,0)}</td><td>${fmt(r.risk_penalty,0)}</td><td>${(r.tags||[]).slice(0,8).map(t=>`<span class="tag" onclick="event.stopPropagation();selectRow('${htmlEsc(r.symbol)}');showTagExplain('${encodeURIComponent(t)}')">${htmlEsc(t)}</span>`).join('')}</td></tr>`).join('')||'<tr><td colspan="18" class="muted">暂无结果，请设置参数后点击“开始筛选”</td></tr>'}
function selectRow(symbol){selected=rows.find(x=>x.symbol===symbol)||null;render();renderDetail(selected)}
function renderDetail(r){if(!r){$('dTitle').textContent='未选择标的';$('dSub').textContent='运行筛选后点击结果行';$('scoreBar').style.width='0';$('detailKv').innerHTML='';$('detailTags').innerHTML='';$('detailRisks').textContent='--';$('detailReason').textContent='--';$('infoPanel').innerHTML='';$('infoCategories').innerHTML='';$('infoNewsList').innerHTML='<button class="btn2" onclick="openInfoDetailPage()">打开信息面分析详情页</button><div class="small" style="margin-top:8px">选择标的后将携带代码和名称打开详情页。</div>';clearTrend();return}$('dTitle').textContent=`${r.name} ${r.symbol}`;$('dSub').textContent=`${r.asset_type} · ${r.grade} · 综合评分 ${fmt(r.total_score,1)}`;$('scoreBar').style.width=Math.max(0,Math.min(100,Number(r.total_score||0)))+'%';const items=[['最新价',fmt(r.last)],['涨跌幅',pct(r.change_pct)],['成交额',money(r.amount)],['换手率',pct(r.turnover)],['量比',fmt(r.volume_ratio,2)],['PE/PB',`${fmt(r.pe_dynamic,2)} / ${fmt(r.pb,2)}`],['250日位置',pct(r.pos250)],['高位回撤',pct(r.drawdown250)],['低点反弹',pct(r.rebound250)],['复权口径',htmlEsc(r.kline_adjust||'qfq')],['MA5/10/20',`${fmt(r.ma5)} / ${fmt(r.ma10)} / ${fmt(r.ma20)}`],['RSI14/KDJ-J',`${fmt(r.rsi14,1)} / ${fmt(r.kdj_j,1)}`],['MACD柱/ROC12',`${fmt(r.macd_hist,4)} / ${fmt(r.roc12,1)}%`],['ATR%/BOLL宽',`${fmt(r.atr_pct,1)}% / ${fmt(r.boll_width,1)}%`],['VWAP20/MFI',`${fmt(r.vwap20)} / ${fmt(r.mfi14,1)}`],['ADX/+DI/-DI',`${fmt(r.adx14,1)} / ${fmt(r.plus_di,1)} / ${fmt(r.minus_di,1)}`],['支撑/压力',`${fmt(r.support60)} / ${fmt(r.resistance60)}`],['低位分',fmt(r.low_score,0)],['趋势分',fmt(r.trend_score,0)],['动量分',fmt(r.momentum_score,0)],['量能分',fmt(r.volume_score,0)],['波动空间分',fmt(r.volatility_score,0)],['资金强度分',fmt(r.strength_score,0)],['风险扣分',fmt(r.risk_penalty,0)]];$('detailKv').innerHTML=items.map(x=>`<div class="item"><span>${x[0]}</span><b>${x[1]}</b></div>`).join('');$('detailTags').innerHTML=(r.tags||[]).map(t=>`<span class="tag" onclick="event.stopPropagation();showTagExplain('${encodeURIComponent(t)}')">${htmlEsc(t)}</span>`).join('')||'<span class="small">--</span>';$('detailRisks').innerHTML=uniq(r.risk_flags||[]).map(t=>`<span class="tag risk" onclick="event.stopPropagation();showTagExplain('${encodeURIComponent(t)}')">${htmlEsc(t)}</span>`).join('')||'<span class="ok">暂无明显风险标签</span>';let infoTxt='';if(r.info){infoTxt=`；信息面评分 ${fmt(r.info.info_score,1)}，${r.info.summary||''}`}else if(r.news){infoTxt=`；新闻评分 ${fmt(r.news.news_score,1)}，情绪 ${sentCN(r.news.sentiment)}，${r.news.summary||''}`}$('detailReason').textContent=(r.reason||'--')+infoTxt;renderInfoPanel(r);loadScoreTrend(r.symbol)}


function renderProfileBox(profile){
  if(!profile||!(profile.summary||profile.executives?.length||profile.financial_history?.length))return'';
  const caps=[];
  if(profile.total_market_value)caps.push(`总市值：${htmlEsc(profile.total_market_value)}`);
  if(profile.float_market_value)caps.push(`流通市值：${htmlEsc(profile.float_market_value)}`);
  const execs=(profile.executives||[]).slice(0,5).map(e=>`<span class="tag">${htmlEsc(e.name||'--')} ${htmlEsc(e.title||'')}</span>`).join('');
  const changes=(profile.personnel_changes||[]).slice(0,4).map(e=>`<div class="small">${htmlEsc(e.date||'日期未知')} ${htmlEsc(e.name||'')} ${htmlEsc(e.title||'')} ${htmlEsc(e.summary||'')}</div>`).join('');
  const fin=(profile.financial_history||[]).slice(0,4).map(r=>`<div class="small">${htmlEsc(r.report_date||'--')}　营收${htmlEsc(r.revenue||'--')}　净利${htmlEsc(r.net_profit||'--')}　ROE${htmlEsc(r.roe||'--')}</div>`).join('');
  const source=(profile.sources||[]).length?`<div class="small">来源：${(profile.sources||[]).map(htmlEsc).join('、')}；${profile.cache_info?.hit?'画像缓存':'本次更新'}</div>`:'';
  return `<div class="profile-box"><b>公司简介</b><br>${htmlEsc(profile.summary||'--')}${caps.length?`<br><span class="small">${caps.join('　')}</span>`:''}${execs?`<div style="margin-top:6px"><b class="small">管理层：</b>${execs}</div>`:''}${changes?`<div style="margin-top:6px"><b class="small">人员变动：</b>${changes}</div>`:''}${fin?`<div style="margin-top:6px"><b class="small">历史业绩：</b>${fin}</div>`:''}${source}</div>`;
}

function openInfoDetailPage(){
  const r=selected || rows[0];
  if(!r){alert('请先选择一只股票');return}
  const sid=(r.info&&r.info.snapshot_id)||(r.news&&r.news.snapshot_id)||''; const lim=$('infoLimit')?.value||180; const url='/info?symbol='+encodeURIComponent(r.symbol||'')+'&name='+encodeURIComponent(r.name||'')+'&limit='+encodeURIComponent(lim)+'&snapshot_id='+encodeURIComponent(sid);
  window.open(url,'_blank');
}
function renderInfoPanel(r){
  // V3.15：筛选页不再展示信息流、全球要闻、来源诊断和说明块，只保留入口，避免筛选页信息过载。
  const btn = `<button class="btn2" onclick="openInfoDetailPage()">打开信息面分析详情页</button>`;
  let note = '<div class="small" style="margin-top:8px">新闻明细、全球/前沿要闻、宏观/行业/公司/资金/国际/舆情分层、publish/event/crawl 时间、统计图、事件簇去重组和来源诊断均在详情页查看。</div>';
  if(r&&r.info){
    note += `<div class="small" style="margin-top:8px">当前筛选已融合信息面分 ${fmt(r.info.info_score,1)}；权重 ${r.info_weight?Math.round(r.info_weight*100)+'%':'--'}；抓取上限 ${$('infoLimit')?.value||'--'}。</div>`;
  }else if(r){
    note += '<div class="small" style="margin-top:8px">未启用信息面评分时，详情页仍可单独强制抓取并查看，但不会自动改写本次筛选总分。</div>';
  }
  let tech='';
  if(r&&r.indicator50_snapshot){
    const s=r.indicator50_snapshot;
    const entries=(s.entries||[]).slice(0,14).map(x=>`<span class="tag" title="${htmlEsc(x.signal||'')}">${htmlEsc(x.name||x.key)}:${htmlEsc(x.value===null||x.value===undefined?'--':(typeof x.value==='object'?x.status:String(x.value).slice(0,12)))}</span>`).join('');
    tech+=`<div class="profile-box"><b>50项技术/量价时空快照</b><div class="small">覆盖${s.count||0}项，已计算/估算${s.computed_or_estimated_count||0}项，缺失${s.missing_count||0}项；Level-2/Tick/期权类不伪造。</div><div style="margin-top:6px">${entries}</div></div>`;
  }
  if(r&&r.tradercore_diagnosis){
    const d=r.tradercore_diagnosis;
    const rows=(d.rows||[]).map(x=>`<div class="small" style="border-top:1px solid #26364f;padding:5px 0"><b>${htmlEsc(x.dimension)}</b>：${htmlEsc(x.script)}<br><span class="muted">人工复核：${htmlEsc(x.human)}</span></div>`).join('');
    tech+=`<div class="profile-box"><b>三通道/三层诊断</b><div class="small">${htmlEsc(d.script_conclusion||'')}</div>${rows}<div class="small" style="margin-top:6px">${htmlEsc(d.trading_logic||'')}</div></div>`;
  }
  $('infoPanel').innerHTML=tech;
  $('infoCategories').innerHTML='';
  $('infoNewsList').innerHTML=btn+note;
}
function renderNewsItem(x){
  const url=x.url||'#';
  const title=htmlEsc(x.title||'--');
  const date=htmlEsc(x.date_display||x.published_at_norm||x.published_at||'日期未知');
  const source=htmlEsc(x.source||'--');
  const event=htmlEsc(x.event_label||x.category||'一般资讯');
  const risk=x.risk_tag?`<span class="tag risk" title="${htmlEsc(x.risk_tag)}">风险：${htmlEsc(x.risk_tag)}</span>`:'';
  const sent=htmlEsc(x.sentiment_label||((Number(x.sentiment_score||50)>=58)?'正面':(Number(x.sentiment_score||50)<=45?'负面':'中性')));
  const sentCls=sent==='正面'?'good':(sent==='负面'?'risk':'');
  const scope=htmlEsc(scopeCN(x.impact_scope||'company'));
  const dir=htmlEsc(x.impact_direction||'中性/待观察');
  const evidence=(x.evidence&&x.evidence.length)?`<div>${x.evidence.map(e=>`<span class="tag risk">${htmlEsc(e)}</span>`).join('')}</div>`:'';
  const relation=x.target_relation?`<span class="tag event">关系：${htmlEsc(x.target_relation)}</span>`:'';
  const relationNote=x.relation_note?`<div class="small">关系识别：${htmlEsc(x.relation_note)}</div>`:'';
  return `<div class="news-item"><a class="news-title" href="${htmlEsc(url)}" target="_blank">${title}</a><div class="news-meta">${date} · ${source} · 可信${fmt(x.credibility_score,0)} · 相关${fmt(x.relevance_score,0)}${x.content_loaded?' · 已读取正文':''}</div><div style="margin-top:6px"><span class="tag event">事件：${event}</span>${risk}<span class="tag ${sentCls}">情绪：${sent}</span><span class="tag scope">影响：${dir}/${scope}</span>${relation}</div>${x.summary?`<div class="news-summary">${htmlEsc(x.summary).slice(0,240)}</div>`:''}${evidence}${relationNote}</div>`;
}
async function loadGlobalNews(force=false){
  const box=$('globalNewsList');if(!box)return;
  box.innerHTML='<span class="small">正在刷新全球/国内要闻...</span>';
  try{
    const resp=await fetch('/api/news/global?limit=18&force='+force,{cache:'no-store'});
    const js=await resp.json();
    const data=js.data||{};const items=(data.items||[]).slice(0,18);
    const cache=data.cache_info||{};
    let html=`<div class="small">${htmlEsc(data.updated_at||'')} · ${cache.hit?'短缓存':'本次刷新'} · ${items.length}条</div>`;
    html+=items.length?items.map(renderNewsItem).join(''):'<span class="small">暂无全球/国内要闻。可稍后刷新，或检查 akshare/网络。</span>';
    const status=data.sources_status||[];
    if(status.length)html+=`<div class="hint">${status.slice(0,8).map(s=>`${htmlEsc(s.source||'--')}:${s.count??0}条(${htmlEsc(s.status||'--')})`).join('；')}</div>`;
    box.innerHTML=html;
  }catch(e){box.innerHTML='<span class="err">全球/国内要闻读取失败：'+htmlEsc(e)+'</span>'}
}
function openSelectedDetail(){const s=selected?.symbol||parseSymbols().split(',')[0]||'300750';window.open('/chart/'+encodeURIComponent(s)+'?frame=time','_blank')}
function appendSelectedToPool(){if(!selected)return;const old=parseSymbols().split(',').filter(Boolean);if(!old.includes(selected.symbol))old.push(selected.symbol);$('symbols').value=old.join(',');savePool()}
async function addSelectedToMonitor(){if(!selected){log('请先选择一只筛选结果','WARN');return}try{const resp=await fetch('/api/watchlist/add?symbols='+encodeURIComponent(selected.symbol),{method:'POST',cache:'no-store'});const js=await resp.json();if(!js.ok)throw new Error(js.message||'加入失败');log(`${selected.symbol} ${selected.name} 已加入实时监测列表，当前 ${js.data.count} 只`)}catch(e){log(e,'ERROR')}}
function jumpSelectedToMonitor(){if(!selected){log('请先选择一只筛选结果','WARN');return}window.open('/jump/watchlist?symbols='+encodeURIComponent(selected.symbol),'_blank')}
function clearTrend(){const c=$('trendCanvas');if(c){const ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height)}$('trendEmpty').style.display='flex';$('trendHint').textContent='按天记录'}
function resizeCanvas2(canvas){const dpr=window.devicePixelRatio||1;const rect=canvas.getBoundingClientRect();canvas.width=Math.max(10,Math.floor(rect.width*dpr));canvas.height=Math.max(10,Math.floor(rect.height*dpr));const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);return{ctx,w:rect.width,h:rect.height}}
async function loadScoreTrend(symbol){try{const resp=await fetch('/api/score/history/'+encodeURIComponent(symbol)+'?days=180',{cache:'no-store'});const js=await resp.json();const data=js.data||[];drawTrend(data);$('trendHint').textContent=data.length?`${data.length}日记录`:'暂无历史'}catch(e){clearTrend();log('评分趋势读取失败：'+e,'WARN')}}
function drawTrend(data){const canvas=$('trendCanvas');const empty=$('trendEmpty');const {ctx,w,h}=resizeCanvas2(canvas);ctx.clearRect(0,0,w,h);if(!data||data.length<1){empty.style.display='flex';return}empty.style.display='none';const pad={l:34,r:14,t:14,b:26};ctx.strokeStyle='rgba(148,163,184,.18)';ctx.lineWidth=1;ctx.font='11px Segoe UI';ctx.fillStyle='#8ea3c3';for(let i=0;i<=4;i++){const y=pad.t+(h-pad.t-pad.b)*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();const v=100-i*25;ctx.textAlign='right';ctx.textBaseline='middle';ctx.fillText(v,pad.l-6,y)}const xs=(i)=>pad.l+(w-pad.l-pad.r)*(data.length===1?0.5:i/(data.length-1));const ys=(v)=>pad.t+(100-Number(v||0))/100*(h-pad.t-pad.b);ctx.strokeStyle='#60a5fa';ctx.lineWidth=2;ctx.beginPath();data.forEach((r,i)=>{const x=xs(i),y=ys(r.total_score);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();data.forEach((r,i)=>{const x=xs(i),y=ys(r.total_score);ctx.fillStyle=Number(r.total_score)>=75?'#22c55e':Number(r.total_score)>=60?'#f59e0b':'#94a3b8';ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill()});ctx.fillStyle='#8ea3c3';ctx.textAlign='left';ctx.textBaseline='alphabetic';ctx.fillText(data[0].score_date,pad.l,h-8);ctx.textAlign='right';ctx.fillText(data[data.length-1].score_date,w-pad.r,h-8);const last=data[data.length-1];ctx.fillStyle='#dbeafe';ctx.textAlign='right';ctx.fillText('最新 '+Number(last.total_score||0).toFixed(1),w-pad.r,12)}

document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=(k==='symbol'||k==='name'||k==='grade')?1:-1}sortRows(false);render()});

function hideExplain(){const b=$('explainBox');if(b)b.style.display='none'}
function htmlEsc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
async function showTagExplain(tagEnc){
  const tag=decodeURIComponent(tagEnc||'');
  if(!selected){log('请先选择一只股票再查看标签解释','WARN');return}
  const box=$('explainBox'), title=$('explainTitle'), body=$('explainBody');
  box.style.display='block';title.textContent='标签解释：'+tag;body.innerHTML='正在读取解释...';
  try{
    const params=new URLSearchParams({tag,mode:$('mode').value,strategies:selectedStrategies().join(',')});
    const resp=await fetch('/api/screener/explain/'+encodeURIComponent(selected.symbol)+'?'+params.toString(),{cache:'no-store'});
    const js=await resp.json();
    if(!js.ok) throw new Error(js.message||'解释接口失败');
    const d=js.data||{};
    const metrics=(d.metrics||[]).map(m=>`<div class="explain-metric"><b>${htmlEsc(m.name)}</b><span>${htmlEsc(m.value??'--')}${htmlEsc(m.unit||'')}<br><em class="muted">${htmlEsc(m.better||'')}</em></span></div>`).join('');
    const why=(d.why||[]).map(x=>`<li>${htmlEsc(x)}</li>`).join('');
    const anns=(d.annotations_preview||[]).map(a=>`<span class="tag">${htmlEsc(a.label||a.type)}</span>`).join('')||'<span class="small">暂无临时标注</span>';
    body.innerHTML=`<div class="hint">${htmlEsc(d.conclusion||'')}</div><div class="section-title">判断逻辑</div><ul>${why}</ul><div class="section-title">数据对比</div>${metrics}<div class="section-title">K线标注预留</div>${anns}<div class="hint" style="margin-top:8px">${htmlEsc(d.future_interface||'')}</div>`;
  }catch(e){body.innerHTML='<span class="err">读取失败：'+htmlEsc(e)+'</span>'}
}

(function init(){const old=localStorage.getItem(LS);if(old)$('symbols').value=old;render();renderDetail(null);loadStrategyLibrary();log('V3.15.3 筛选模块初始化完成：三通道候选、50项技术快照、三层评分和信息源有效证据扩展已启用')})();
</script>
</body>
</html>'''
