from __future__ import annotations


def build_backtest_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Quant Data Gateway - 交易回测系统</title>
<style>
:root{--bg:#0b1020;--panel:#111827;--panel2:#172033;--line:#283956;--text:#dbeafe;--muted:#91a7c7;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b}
*{box-sizing:border-box}html,body{height:100%;margin:0}body{font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}.app{height:100vh;display:grid;grid-template-rows:56px 1fr 86px;grid-template-columns:320px 1fr;grid-template-areas:"top top" "side main" "log log"}.top{grid-area:top;display:flex;align-items:center;gap:10px;padding:0 16px;background:#101827;border-bottom:1px solid var(--line)}.brand{font-weight:900;font-size:18px;color:#bfdbfe}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.grow{flex:1}.side{grid-area:side;background:#0f172a;border-right:1px solid var(--line);padding:14px;overflow:auto}.main{grid-area:main;padding:14px;display:flex;flex-direction:column;gap:12px;overflow:auto}.log{grid-area:log;background:#0f172a;border-top:1px solid var(--line);padding:8px 14px;overflow:auto;font-family:Consolas,monospace;font-size:12px;color:#9fb4d4}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-h{min-height:44px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 12px;background:#141f35;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.section{font-size:13px;color:#9fb4d4;margin:13px 0 7px}input,select{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px 11px;outline:none}input:focus,select:focus{border-color:#60a5fa;box-shadow:0 0 0 3px rgba(59,130,246,.12)}button{border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer;white-space:nowrap}button:hover{background:#1d4ed8}button:disabled{opacity:.45;cursor:not-allowed}.btn2{background:#253149;color:#c7d2fe}.btn2:hover{background:#30405d}.btn-green{background:#16a34a}.btn-green:hover{background:#15803d}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.row{display:flex;gap:8px;align-items:center}.hint{font-size:12px;color:#9fb4d4;line-height:1.55;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px;margin-top:10px}.cards{display:grid;grid-template-columns:repeat(7,minmax(120px,1fr));gap:8px}.card{background:#141e32;border:1px solid #26364f;border-radius:12px;padding:10px;min-width:0}.card span{display:block;font-size:11px;color:#91a7c7}.card b{display:block;margin-top:4px;font-size:20px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.up{color:#fca5a5}.down{color:#86efac}.muted{color:var(--muted)}.warn{color:#fcd34d}.work{display:grid;grid-template-columns:minmax(700px,1fr) 430px;gap:12px;align-items:start}.chart-stack{display:grid;grid-template-rows:410px 108px 128px 118px;gap:8px}.chart-wrap{background:#0b1224;border:1px solid #26364f;border-radius:12px;padding:10px;position:relative;min-width:0}.chart-wrap canvas{width:100%;height:100%;display:block}.empty{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8ea3c3;text-align:center;padding:20px}.table-wrap{max-height:260px;overflow:auto;border:1px solid var(--line);border-radius:12px;background:#0f172a}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid rgba(38,54,79,.8);padding:8px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{position:sticky;top:0;background:#182238;color:#93c5fd}.assumptions{display:flex;flex-direction:column;gap:8px;font-size:13px;color:#b6c7e2;line-height:1.5}.pill{display:inline-flex;align-items:center;border:1px solid #30405d;background:#1f2a44;color:#bfdbfe;border-radius:999px;padding:5px 9px;font-size:12px}.formula,.summary-box,.quick-trades,.compare-box{background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.formula b,.summary-box b,.quick-trades b{color:#bfdbfe}.formula ul{margin:8px 0 0 18px;padding:0}.formula li{margin:4px 0}.legend{display:flex;gap:8px;flex-wrap:wrap}.legend span{border:1px solid #30405d;border-radius:999px;padding:3px 8px;background:#172033;color:#bfdbfe;font-size:12px}.panel-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.data-note{font-size:12px;color:#9fb4d4}.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.summary-grid div{background:#121c31;border:1px solid #26364f;border-radius:10px;padding:8px}.summary-grid span{display:block;color:#91a7c7;font-size:11px}.summary-grid strong{display:block;text-align:right;font-size:18px}.quick-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}.quick-list{display:flex;flex-direction:column;gap:8px;max-height:340px;overflow:auto}.trade-card{background:#121c31;border:1px solid #26364f;border-radius:10px;padding:8px;font-size:12px}.trade-card .line{display:flex;justify-content:space-between;gap:8px}.trade-reason{color:#9fb4d4;line-height:1.45;margin-top:6px}.link-btn{background:#253149;color:#c7d2fe;border-radius:8px;padding:6px 8px;font-size:12px}.compare-row{display:grid;grid-template-columns:1fr 64px 54px;gap:6px;align-items:center;padding:6px;border-bottom:1px solid rgba(38,54,79,.7);font-size:12px}.compare-row.current{background:#172a4d;border-radius:8px}.compare-row:last-child{border-bottom:0}@media(max-width:1180px){body{overflow:auto}.app{height:auto;min-height:100vh;grid-template-columns:1fr;grid-template-rows:56px auto auto 86px;grid-template-areas:"top" "side" "main" "log"}.work{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}.chart-stack{grid-template-rows:360px 96px 120px 112px}}
</style>
<style>
.trade-drawer{position:fixed;inset:0;background:rgba(3,7,18,.58);z-index:30;display:none;justify-content:flex-end}.trade-drawer.open{display:flex}.trade-drawer-panel{width:min(960px,calc(100vw - 42px));height:100%;background:#0f172a;border-left:1px solid var(--line);box-shadow:-24px 0 60px rgba(0,0,0,.4);display:flex;flex-direction:column}.trade-drawer-body{padding:12px;overflow:auto;min-height:0}.drawer-summary{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:8px;margin-bottom:10px}.drawer-summary div{background:#121c31;border:1px solid #26364f;border-radius:10px;padding:8px}.drawer-summary span{display:block;color:#91a7c7;font-size:11px}.drawer-summary b{display:block;text-align:right;font-size:18px}.detail-table-wrap{max-height:none;height:calc(100vh - 170px)}.detail-table-wrap td:nth-child(8),.detail-table-wrap td:nth-child(9){white-space:normal;min-width:220px;text-align:left;line-height:1.45}.trade-actions{display:flex;gap:6px;align-items:center;flex-wrap:wrap}@media(max-width:1180px){.drawer-summary{grid-template-columns:repeat(2,1fr)}.trade-drawer-panel{width:100vw}}
.combo-box{margin-top:10px;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.combo-checks{display:grid;grid-template-columns:1fr;gap:6px;max-height:168px;overflow:auto;margin-top:8px}.combo-checks label{display:flex;gap:8px;align-items:flex-start;background:#121c31;border:1px solid #26364f;border-radius:10px;padding:7px;font-size:12px}.combo-checks input{width:auto;margin-top:2px}.combo-rules{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.v321-box{margin-top:10px;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.v321-box .mini{display:grid;grid-template-columns:1fr 1fr;gap:8px}.v321-box label.check{display:flex;gap:8px;align-items:center;font-size:12px;color:#b6c7e2;margin-top:8px}.v321-box label.check input{width:auto}.trade-drawer-panel{width:min(1180px,calc(100vw - 24px));max-width:100vw}.table-wrap.trade-table-wrap{max-height:300px;overflow:auto}.trade-table{min-width:1360px;table-layout:auto}.trade-table td.reason,.trade-table th.reason{white-space:normal;min-width:320px;text-align:left;line-height:1.45}.trade-table td{vertical-align:top}.detail-table-wrap{overflow:auto}.detail-table-wrap .trade-table{min-width:1420px}.param-cn{margin-top:8px;background:#0d1428;border:1px solid #26364f;border-radius:10px;padding:8px;color:#b6c7e2;font-size:12px;line-height:1.55}.param-cn b{color:#bfdbfe}.main-trade-panel{display:none}.main-trade-panel .panel-b{padding:10px}
</style>
<style>
.auto-config-box{margin-top:10px;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px}.auto-config-box .head{display:flex;align-items:center;justify-content:space-between;gap:8px}.auto-config-box .mini-line{font-size:12px;color:#9fb4d4;line-height:1.5;margin-top:6px;overflow-wrap:anywhere}.auto-catalog{display:grid;grid-template-columns:1fr;gap:6px;max-height:146px;overflow:auto;margin-top:8px;padding-right:2px}.auto-catalog label{display:flex;gap:8px;align-items:flex-start;background:#121c31;border:1px solid #26364f;border-radius:10px;padding:7px;font-size:12px;line-height:1.35}.auto-catalog input{width:auto;margin-top:2px}.auto-catalog b{color:#bfdbfe}.auto-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.marker-controls{display:flex;align-items:center;justify-content:flex-end;gap:6px;flex-wrap:wrap}.marker-controls button{padding:5px 8px;border-radius:8px;font-size:12px;background:#253149}.marker-controls button.active{background:#1d4ed8}
.action-toast{position:fixed;right:22px;bottom:104px;z-index:80;max-width:min(420px,calc(100vw - 44px));padding:11px 14px;border:1px solid #166534;border-radius:10px;background:#10233a;color:#bbf7d0;box-shadow:0 18px 55px rgba(0,0,0,.45);opacity:0;transform:translateY(10px);pointer-events:none;transition:.18s}.action-toast.show{opacity:1;transform:none}.action-toast.bad{border-color:#991b1b;color:#fecaca}
.work{grid-template-columns:minmax(0,1fr) minmax(300px,380px);min-width:0}
</style>
</head>
<body>
<div class="app">
  <div class="top"><span class="dot"></span><div class="brand">交易回测系统</div><span class="pill">legacy 快速验证 · 科学组合回测走 V3.20 API</span><div class="grow"></div><button class="btn2" onclick="location.href='/auto-trading'">自动交易总控台</button><button class="btn2" onclick="location.href='/screener'">筛选系统</button><button class="btn2" onclick="location.href='/ui'">行情监控</button></div>
  <aside class="side">
    <div class="section">标的代码</div>
    <input id="symbol" value="300750" />
    <div class="section">策略</div>
    <select id="strategy" onchange="toggleComboBox()"><option value="combo_signal">组合策略判断</option><option value="score_driven" selected>日评分驱动</option><option value="score_reversal">评分拐点修复</option><option value="ma_cross">MA趋势跟随</option><option value="rsi_rebound">RSI超跌反弹</option><option value="breakout">20日突破放量</option><option value="macd_momentum">MACD动量确认</option><option value="boll_pullback">BOLL回踩修复</option><option value="trend_pullback">趋势回踩MA20</option></select>
    <div id="comboBox" class="combo-box">
      <div class="row"><b>组合判断</b><span class="muted">买入需多策略共振，卖出可任一转弱退出</span></div>
      <div class="combo-checks">
        <label><input class="combo-strategy" type="checkbox" value="score_driven" checked><span><b>日评分驱动</b><br><span class="muted">研究分达到阈值且风险不高</span></span></label>
        <label><input class="combo-strategy" type="checkbox" value="ma_cross" checked><span><b>MA趋势跟随</b><br><span class="muted">MA5/MA20 和收盘位置确认趋势</span></span></label>
        <label><input class="combo-strategy" type="checkbox" value="macd_momentum" checked><span><b>MACD动量确认</b><br><span class="muted">MACD柱体转强过滤弱反弹</span></span></label>
        <label><input class="combo-strategy" type="checkbox" value="breakout" checked><span><b>20日突破放量</b><br><span class="muted">突破平台并有量能配合</span></span></label>
        <label><input class="combo-strategy" type="checkbox" value="boll_pullback"><span><b>BOLL回踩修复</b><br><span class="muted">回踩下轨/中轨后的修复</span></span></label>
        <label><input class="combo-strategy" type="checkbox" value="trend_pullback"><span><b>趋势回踩MA20</b><br><span class="muted">趋势背景下低吸修复</span></span></label>
      </div>
      <div class="combo-rules">
        <div><div class="section">买入规则</div><select id="comboBuyRule"><option value="at_least_2" selected>至少2项命中</option><option value="at_least_3">至少3项命中</option><option value="any">任一命中</option><option value="all">全部命中</option></select></div>
        <div><div class="section">卖出规则</div><select id="comboSellRule"><option value="any" selected>任一转弱卖出</option><option value="all">全部转弱卖出</option></select></div>
      </div>
    </div>
    <div class="grid2">
      <div><div class="section">初始资金</div><input id="cash" type="number" value="100000" min="1000" step="1000"></div>
      <div><div class="section">仓位比例</div><input id="position" type="number" value="100" min="5" max="100"></div>
      <div><div class="section">手续费%</div><input id="fee" type="number" value="0.03" min="0" step="0.01"></div>
      <div><div class="section">滑点%</div><input id="slip" type="number" value="0.05" min="0" step="0.01"></div>
      <div><div class="section">止损%</div><input id="stop" type="number" value="8" min="0" step="0.5"></div>
      <div><div class="section">止盈%</div><input id="take" type="number" value="0" min="0" step="1"></div>
      <div><div class="section">买入评分</div><input id="buyScore" type="number" value="62" min="0" max="100" step="1"></div>
      <div><div class="section">卖出评分</div><input id="sellScore" type="number" value="48" min="0" max="100" step="1"></div>
      <div><div class="section">K线数量</div><input id="limit" type="number" value="520" min="60" max="1200"></div>
      <div><div class="section">复权口径</div><select id="adjust"><option value="qfq" selected>前复权</option><option value="none">不复权</option><option value="hfq">后复权</option></select></div>
    </div>
    <div class="v321-box">
      <div class="row"><b>V3.21 资金/周期</b><span class="muted">仓位、复利、止损止盈与评分一起进回测</span></div>
      <div class="mini">
        <div><div class="section">仓位模式</div><select id="sizingMode"><option value="score_weighted" selected>评分加权</option><option value="fixed_percent">固定仓位</option><option value="equal_weight">等权</option><option value="volatility_target">波动率目标</option><option value="atr_risk">ATR风险仓位</option><option value="fractional_kelly">分数凯利</option><option value="pyramid">金字塔加仓</option><option value="dca">定投</option><option value="core_satellite">核心卫星</option></select></div>
        <div><div class="section">交易周期</div><select id="horizonMode"><option value="short_term">短线</option><option value="swing" selected>中线/波段</option><option value="position">长线</option><option value="dca">定投</option><option value="hybrid">组合</option></select></div>
        <div><div class="section">定投金额</div><input id="dcaAmount" type="number" value="1000" min="0" step="100"></div>
        <div><div class="section">ATR风险%</div><input id="atrRisk" type="number" value="2" min="0" max="20" step="0.5"></div>
        <div><div class="section">加仓阶梯%</div><input id="pyramidStep" type="number" value="5" min="0" max="50" step="0.5"></div>
        <div><div class="section">最多加仓</div><input id="pyramidAdds" type="number" value="3" min="0" max="8" step="1"></div>
      </div>
      <label class="check"><input id="compoundReturns" type="checkbox" checked>收益进入下一次仓位计算</label>
      <label class="check"><input id="qualityFilter" type="checkbox" checked>启用质量过滤</label>
      <label class="check"><input id="anomalyFilter" type="checkbox" checked>启用异常波动过滤</label>
      <div class="section">实时交易目标权重（只展示）</div>
      <div class="mini" style="margin-top:8px">
        <div><div class="section">基本面</div><input id="fundamentalWeight" type="number" value="0.22" readonly></div>
        <div><div class="section">技术面</div><input id="technicalWeight" type="number" value="0.30" readonly></div>
        <div><div class="section">信息面</div><input id="informationWeight" type="number" value="0.20" readonly></div>
        <div><div class="section">资金面</div><input id="fundFlowWeight" type="number" value="0.16" readonly></div>
        <div><div class="section">大盘情绪</div><input id="marketWeight" type="number" value="0.12" readonly></div>
      </div>
      <div class="param-cn">当前单票快速回测只有历史日K/量价的逐日可用证据，所以实际成交评分按技术/量价 100% 运行。基本面、信息面、资金面和大盘权重仅同步展示实时配置；没有 PIT 历史快照时不会拿今天的数据回填过去。</div>
    </div>
    <div class="auto-config-box">
      <div class="head"><b>V3.23 自动交易配置</b><button class="link-btn" onclick="loadAutoConfigForBacktest(true)">读取总控台</button></div>
      <div id="autoBacktestSummary" class="mini-line">读取总控台配置后，可把筛选策略、仓位模型、止盈止损、最大回撤和信息节点一起带入回测。</div>
      <div id="autoStrategyCatalog" class="auto-catalog"></div>
      <div class="auto-actions"><button class="btn2" onclick="applyAutoConfigToBacktest(backtestAutoConfig)">应用到参数</button><button class="btn2" onclick="runAutoConfigBacktest()">用配置回测</button><button class="btn2" onclick="location.href='/auto-trading'">打开总控台</button></div>
    </div>
    <div class="row" style="margin-top:12px"><button id="runBtn" class="btn-green" onclick="runBacktest()">运行回测</button><button class="btn2" onclick="fillSelected()">使用筛选选中</button></div>
    <div class="row" style="margin-top:8px"><button class="btn2" onclick="compareStrategies()">比较策略收益</button><button class="btn2" onclick="applyScorePreset()">宽松评分</button></div>
    <div class="hint">此页面保留为 legacy 快速单票验证，不作为科学组合回测。评分驱动策略会回放每日研究分：趋势、动量、量能、位置结构和风险扣分；K线图会标出买入、卖出和异常点。</div>
  </aside>
  <main class="main">
    <div class="cards">
      <div class="card"><span>期末权益</span><b id="mFinal">--</b></div>
      <div class="card"><span>总收益</span><b id="mRet">--</b></div>
      <div class="card"><span>年化</span><b id="mAnn">--</b></div>
      <div class="card"><span>最大回撤</span><b id="mDd">--</b></div>
      <div class="card"><span>夏普</span><b id="mSharpe">--</b></div>
      <div class="card"><span>胜率</span><b id="mWin">--</b></div>
      <div class="card"><span>交易次数</span><b id="mTrades">--</b></div>
    </div>
    <div class="work">
      <div class="panel">
        <div class="panel-h"><span id="title" class="panel-title">等待运行</span><div class="marker-controls"><button id="tradeMarkerBtn" class="active" onclick="toggleTradeMarkers(this)">买卖点：显示</button><button id="anomalyMarkerBtn" class="active" onclick="toggleAnomalyMarkers(this)">异常：近7日/严重</button><span class="muted" id="dq">--</span></div></div>
        <div class="panel-b">
          <div class="chart-stack">
            <div class="chart-wrap"><canvas id="klineChart"></canvas><div id="klineEmpty" class="empty">运行回测后显示完整日K、买卖点和异常点</div></div>
            <div class="chart-wrap"><canvas id="volumeChart"></canvas><div id="volumeEmpty" class="empty">成交量副图</div></div>
            <div class="chart-wrap"><canvas id="signalChart"></canvas><div id="signalEmpty" class="empty">评分 / MACD副图</div></div>
            <div class="chart-wrap"><canvas id="chart"></canvas><div id="empty" class="empty">权益曲线</div></div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-h"><span>评分与回测假设</span><div class="trade-actions"><span id="strategyName" class="pill">--</span><button class="link-btn" onclick="openTradeDrawer()">买卖明细</button><button class="link-btn" onclick="openTradePage()">新窗口</button></div></div>
        <div class="panel-b">
          <div id="resultSummary" class="summary-box"><b>收益诊断</b><div class="muted">运行后显示当前策略、买入持有和超额收益对比。</div></div>
          <div id="compareBox" class="compare-box" style="display:none;margin-top:8px"></div>
          <div id="assumptions" class="assumptions" style="margin-top:8px"><div class="warn">请选择标的和策略后运行。</div></div>
        </div>
      </div>
    </div>
    <div class="panel main-trade-panel" id="tradePanel">
      <div class="panel-h"><span>交易明细</span><span id="tradeNote" class="muted">--</span></div>
      <div class="table-wrap trade-table-wrap"><table class="trade-table"><thead><tr><th>#</th><th>交易日</th><th>动作</th><th>价格</th><th>股数</th><th>成交额</th><th>费用</th><th>现金变动</th><th>现金余额</th><th>持仓股数</th><th>成本/股</th><th>已实现盈亏</th><th class="reason">交易依据</th></tr></thead><tbody id="trades"><tr><td colspan="13" class="muted">暂无交易流水</td></tr></tbody></table></div>
    </div>
  </main>
  <div class="log" id="log">Ready.</div>
</div>
<div id="tradeDrawer" class="trade-drawer" aria-hidden="true">
  <div class="trade-drawer-panel">
    <div class="panel-h"><span>买卖明细</span><div class="trade-actions"><button class="link-btn" onclick="openTradePage()">新窗口打开</button><button class="link-btn" onclick="closeTradeDrawer()">关闭</button></div></div>
    <div class="trade-drawer-body">
      <div id="tradeDrawerSummary" class="drawer-summary"></div>
      <div class="table-wrap detail-table-wrap"><table class="trade-table"><thead><tr><th>#</th><th>交易日</th><th>动作</th><th>价格</th><th>股数</th><th>成交额</th><th>费用</th><th>现金变动</th><th>现金余额</th><th>持仓股数</th><th>成本/股</th><th>已实现盈亏</th><th class="reason">交易依据</th></tr></thead><tbody id="tradeDrawerRows"><tr><td colspan="13" class="muted">运行回测后显示买入/卖出交易流水</td></tr></tbody></table></div>
    </div>
  </div>
</div>
<div id="actionToast" class="action-toast" role="status" aria-live="polite"></div>
<script>
const $=id=>document.getElementById(id);
let actionToastTimer=null;function showActionToast(message,bad=false){const box=$('actionToast');if(!box)return;box.textContent=String(message||'操作完成');box.className='action-toast show'+(bad?' bad':'');clearTimeout(actionToastTimer);actionToastTimer=setTimeout(()=>box.className='action-toast',3200)}
const esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const money=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2});
const pct=n=>(Number(n||0)).toFixed(2)+'%';
const sizingNames={score_weighted:'评分加权',fixed_percent:'固定仓位',equal_weight:'等权仓位',volatility_target:'波动率目标',atr_risk:'ATR风险仓位',fractional_kelly:'分数凯利',pyramid:'金字塔加仓',dca:'定投',core_satellite:'核心卫星'};
const horizonNames={short_term:'短线',swing:'中线/波段',position:'长线',dca:'定投',hybrid:'组合'};
const paramName=(dict,value,fallback='--')=>dict[String(value||'')]||String(value||fallback);
let lastBacktest=null,showTradeMarkers=true,showAllAnomalies=false;
function log(s){$('log').textContent=new Date().toLocaleTimeString()+'  '+s+'\n'+$('log').textContent}
function cls(n){return Number(n)>=0?'up':'down'}
function fillSelected(){try{const s=localStorage.getItem('qdg_screener_selected');if(s){$('symbol').value=s;log('已读取筛选页选中标的 '+s)}else{log('未找到筛选页选中标的')}}catch(e){log('读取失败 '+e)}}
function selectedComboStrategies(){return Array.from(document.querySelectorAll('.combo-strategy:checked')).map(x=>x.value)}
function toggleComboBox(){const show=$('strategy').value==='combo_signal';$('comboBox').style.display=show?'block':'none'}
let backtestAutoConfig=null;
function splitListText(v){return String(v||'').split(/[\s,，;；、|]+/).map(s=>s.trim()).filter(Boolean)}
function setComboStrategies(keys){
  const chosen=new Set(keys||[]);
  document.querySelectorAll('.combo-strategy').forEach(x=>{x.checked=chosen.has(x.value)});
  if($('autoStrategyCatalog'))$('autoStrategyCatalog').querySelectorAll('.combo-strategy').forEach(x=>{x.checked=chosen.has(x.value)});
}
function renderAutoStrategyCatalog(cfg){
  const box=$('autoStrategyCatalog');if(!box)return;
  const catalog=cfg?.strategy_catalog||[],selected=new Set((cfg?.strategy_combo&&cfg.strategy_combo.length)?cfg.strategy_combo:selectedComboStrategies());
  if(!catalog.length){box.innerHTML='<div class="muted">策略目录暂未返回，仍可使用上方固定策略。</div>';return}
  box.innerHTML=catalog.map(item=>{const key=String(item.key||''),on=selected.has(key);return `<label title="${esc(item.description||item.beginner_note||'')}"><input class="combo-strategy" type="checkbox" value="${esc(key)}" ${on?'checked':''}><span><b>${esc(item.name||key)}</b><br><span class="muted">${esc(item.category||'策略')} · ${esc(item.beginner_note||item.description||'')}</span></span></label>`}).join('');
}
function renderAutoBacktestSummary(cfg){
  if(!$('autoBacktestSummary'))return;
  const combo=(cfg?.strategy_combo||[]).slice(0,8).join('、')||'--',r=cfg?.risk_controls||{};
  $('autoBacktestSummary').innerHTML=`股票池 ${(cfg?.symbols||[]).slice(0,6).join(', ')||'--'}；策略 ${esc(combo)}；仓位 ${esc(paramName(sizingNames,cfg?.position_sizing))}；止损/止盈/最大回撤 ${esc(r.stop_loss_pct??'--')}% / ${esc(r.take_profit_pct??'--')}% / ${esc(r.max_drawdown_pct??'--')}%；财报/公告/重大负面将作为事件风控进入参数。`;
}
function applyAutoConfigToBacktest(cfg){
  if(!cfg)return;
  backtestAutoConfig=cfg;
  if((cfg.symbols||[]).length)$('symbol').value=cfg.symbols[0];
  $('strategy').value='combo_signal';
  if((cfg.strategy_combo||[]).length)setComboStrategies(cfg.strategy_combo);
  if(cfg.position_sizing&&$('sizingMode'))$('sizingMode').value=cfg.position_sizing;
  if(cfg.initial_cash!=null)$('cash').value=cfg.initial_cash;
  const r=cfg.risk_controls||{};
  if(r.stop_loss_pct!=null)$('stop').value=r.stop_loss_pct;
  if(r.take_profit_pct!=null)$('take').value=r.take_profit_pct;
  if(r.max_single_position_pct!=null)$('position').value=r.max_single_position_pct;
  const w=cfg.score_weights||{};
  if(w.fundamental!=null)$('fundamentalWeight').value=w.fundamental;
  if(w.technical!=null)$('technicalWeight').value=w.technical;
  if(w.information!=null)$('informationWeight').value=w.information;
  if(w.fund_flow!=null)$('fundFlowWeight').value=w.fund_flow;
  if(w.market_regime!=null)$('marketWeight').value=w.market_regime;
  toggleComboBox();renderAutoStrategyCatalog(cfg);renderAutoBacktestSummary(cfg);
}
async function loadAutoConfigForBacktest(apply=false){
  try{const r=await fetch('/api/auto-trading/config',{cache:'no-store'});const js=await r.json();backtestAutoConfig=js.data||{};renderAutoStrategyCatalog(backtestAutoConfig);renderAutoBacktestSummary(backtestAutoConfig);if(apply)applyAutoConfigToBacktest(backtestAutoConfig);log('已读取总控台自动交易配置')}catch(e){$('autoBacktestSummary').textContent='总控台配置读取失败：'+e}
}
async function runAutoConfigBacktest(){if(!backtestAutoConfig)await loadAutoConfigForBacktest(true);applyAutoConfigToBacktest(backtestAutoConfig);await runBacktest(true)}
function params(){
  const p=new URLSearchParams();
  p.set('legacy','true');
  p.set('symbol',$('symbol').value.trim()||'300750');
  p.set('strategy',$('strategy').value);
  p.set('strategy_combo',selectedComboStrategies().join(','));
  p.set('combo_buy_rule',$('comboBuyRule').value||'at_least_2');
  p.set('combo_sell_rule',$('comboSellRule').value||'any');
  p.set('initial_cash',$('cash').value||'100000');
  p.set('position_pct',Number($('position').value||100)/100);
  p.set('fee_rate',Number($('fee').value||0)/100);
  p.set('slippage_rate',Number($('slip').value||0)/100);
  p.set('stop_loss_pct',$('stop').value||'8');
  p.set('take_profit_pct',$('take').value||'0');
  p.set('buy_score',$('buyScore').value||'62');
  p.set('sell_score',$('sellScore').value||'48');
  p.set('limit',$('limit').value||'520');
  p.set('adjust',$('adjust').value||'qfq');
  p.set('position_sizing',$('sizingMode')?.value||'score_weighted');
  p.set('sizing_mode',$('sizingMode')?.value||'score_weighted');
  p.set('horizon',$('horizonMode')?.value||'swing');
  p.set('compound_returns',$('compoundReturns')?.checked?'true':'false');
  p.set('dca_amount',$('dcaAmount')?.value||'1000');
  p.set('dca_frequency','monthly');
  p.set('pyramid_step_pct',$('pyramidStep')?.value||'5');
  p.set('pyramid_max_adds',$('pyramidAdds')?.value||'3');
  p.set('atr_risk_pct',$('atrRisk')?.value||'2');
  p.set('quality_filter',$('qualityFilter')?.checked?'true':'false');
  p.set('anomaly_filter',$('anomalyFilter')?.checked?'true':'false');
  p.set('fundamental_weight',$('fundamentalWeight')?.value||'0.22');
  p.set('technical_weight',$('technicalWeight')?.value||'0.30');
  p.set('information_weight',$('informationWeight')?.value||'0.20');
  p.set('fund_flow_weight',$('fundFlowWeight')?.value||'0.16');
  p.set('market_weight',$('marketWeight')?.value||'0.12');
  return p
}
async function runBacktest(useAutoConfig=false){const btn=$('runBtn');btn.disabled=true;btn.textContent='运行中...';showActionToast('回测任务已提交，正在读取历史K线并计算交易流水');try{log(useAutoConfig?'开始回测（使用总控台自动交易配置）':'开始回测');const p=params();if(useAutoConfig)p.set('use_auto_config','true');const resp=await fetch('/api/backtest/run?'+p.toString(),{cache:'no-store'});const js=await resp.json();if(!resp.ok||!js.ok)throw new Error(js.message||('HTTP '+resp.status));render(js.data);log('完成：'+js.data.symbol+' '+js.data.strategy_name+(js.data.auto_trading_config_applied?' · 已接入自动交易配置':''));showActionToast(`回测完成：${js.data.symbol}，${js.data.trade_count||0} 笔交易`)}catch(e){log('ERROR '+e);$('assumptions').innerHTML='<div class="warn">回测失败：'+esc(e)+'</div>';showActionToast('回测失败：'+e,true)}finally{btn.disabled=false;btn.textContent='运行回测'}}
function render(d){
  lastBacktest=d;
  $('title').textContent=d.name+' '+d.symbol+' · '+d.strategy_name;
  $('strategyName').textContent=d.strategy_name;
  const short=d.data_quality.short_kline?' · K线不足已尽力补齐':'';
  $('dq').textContent=d.data_quality.start+' 至 '+d.data_quality.end+' · '+d.data_quality.bars+'根'+short;
  $('mFinal').textContent=money(d.final_equity);
  $('mRet').textContent=pct(d.total_return_pct);$('mRet').className=cls(d.total_return_pct);
  $('mAnn').textContent=pct(d.annualized_return_pct);$('mAnn').className=cls(d.annualized_return_pct);
  $('mDd').textContent=pct(d.max_drawdown_pct);
  $('mSharpe').textContent=d.sharpe;
  $('mWin').textContent=pct(d.win_rate_pct);
  $('mTrades').textContent=d.trade_count;
  const latest=(d.score_series||[]).slice(-1)[0]||{};
  const formula=d.score_formula||{};
  const comp=(formula.components||[]).map(x=>`<li><b>${esc(x.name)}</b> ${Number(x.weight||0)>0?'+':''}${Math.round(Number(x.weight||0)*100)}%：${esc(x.basis)}</li>`).join('');
  $('resultSummary').innerHTML=summaryHtml(d);
  $('assumptions').innerHTML=`<div class="formula"><b>100分口径</b><div>${esc(formula.formula||'score = 趋势 + 动量 + 量能 + 结构 - 风险')}</div><ul>${comp}</ul><div class="data-note">${esc(formula.note||'当前回测为历史日K量价评分版本。')}</div></div>`+(d.assumptions||[]).map(x=>'<div>'+esc(x)+'</div>').join('')+`<div class="muted">最新评分 ${esc(latest.score??'--')}；趋势/动量/量能/结构/风险 = ${esc(latest.trend_score??'--')} / ${esc(latest.momentum_score??'--')} / ${esc(latest.volume_score??'--')} / ${esc(latest.structure_score??'--')} / ${esc(latest.risk_penalty??'--')}</div><div class="legend"><span>B 买入</span><span>S 卖出</span><span>! 异常/风险</span><span>蓝线 评分</span><span>柱体 MACD</span></div>${paramCnHtml(d)}<div class="muted">原始参数：${esc(JSON.stringify(d.params))}</div>`;
  $('assumptions').insertAdjacentHTML('beforeend','<div class="param-cn"><b>全球情绪 PIT 约束</b>：今天的恒生科技、纳指期货、费城半导体、日韩指数等实时行情绝不回填到历史日期；只有决策当时已落库且可追溯的历史快照才允许进入科学回测，否则该维度显示缺失并退出计分。</div>');
  const events=tradeEvents(d);
  $('tradeNote').textContent=(d.trade_event_count||events.length)+' 条交易流水 · '+d.trade_count+' 笔闭合交易 · 买卖点 '+((d.markers||[]).length)+' 个 · 异常点 '+((d.anomaly_markers||[]).length)+' 个';
  $('trades').innerHTML=events.map(tradeRow).join('')||'<tr><td colspan="13" class="muted">本次参数下无交易流水</td></tr>';
  renderTradeDrawer(d);
  drawKline(d.kline||[]);drawVolume(d.kline||[]);drawSignal(d.kline||[],d.params||{});drawEquity(d.equity_curve||[]);
}
function tradeEvents(d){if(Array.isArray(d.trade_events)&&d.trade_events.length)return d.trade_events;return (d.trades||[]).flatMap((t,i)=>legacyTradeEvents(t,i))}
function legacyTradeEvents(t,i){const shares=t.buy_shares??t.shares??0;return [{event_id:`${i+1}-B`,trade_index:i+1,date:t.entry_date,side:'buy',action:'买入',price:t.entry_price,shares,amount:t.entry_value,fee:t.entry_fee,cash_change:-(Number(t.entry_cost??0)),cash_after:Number(t.cash_before_entry||0)-Number(t.entry_cost||0),position_shares:shares,cost_basis:t.cost_basis,realized_pnl:0,realized_pct:0,reason:t.entry_reason,signal_date:t.entry_signal_date,score:t.entry_signal_score},{event_id:`${i+1}-S`,trade_index:i+1,date:t.exit_date,side:'sell',action:'卖出',price:t.exit_price,shares:t.sell_shares??shares,amount:t.exit_value,fee:t.exit_fee,cash_change:t.exit_proceeds,cash_after:t.cash_after_exit,position_shares:0,cost_basis:t.cost_basis,realized_pnl:t.pnl,realized_pct:t.pnl_pct,reason:t.exit_reason,signal_date:t.exit_signal_date,score:t.exit_signal_score}]}
function tradeRow(e,i){const isSell=e.side==='sell';const sideCls=e.side==='buy'?'up':'down';const pnl=isSell?money(e.realized_pnl):'--';const pnlCls=isSell?cls(e.realized_pnl):'muted';const score=e.score==null?'--':e.score;return `<tr><td>${i+1}</td><td>${esc(e.date||'--')}</td><td class="${sideCls}">${esc(e.action||e.side||'--')}</td><td>${esc(e.price??'--')}</td><td>${esc(e.shares??0)}</td><td>${money(e.amount)}</td><td>${money(e.fee)}</td><td class="${cls(e.cash_change)}">${money(e.cash_change)}</td><td>${e.cash_after==null?'--':money(e.cash_after)}</td><td>${esc(e.position_shares??'--')}</td><td>${esc(e.cost_basis??'--')}</td><td class="${pnlCls}">${pnl}${isSell?' / '+pct(e.realized_pct):''}</td><td class="reason">${esc(e.reason||'--')}<br><small class="muted">信号日 ${esc(e.signal_date||'--')} · 评分 ${esc(score)} · 闭合#${esc(e.trade_index||'--')}</small></td></tr>`}
function paramCnHtml(d){const obj=d.params_cn||{};const rows=Object.entries(obj).map(([k,v])=>`<span><b>${esc(k)}</b>：${esc(v)}</span>`).join('　');return rows?`<div class="param-cn">${rows}</div>`:''}
function summaryHtml(d){const excess=Number(d.excess_return_pct||0);const low=Number(d.total_return_pct||0)<0||excess<0;return `<b>收益诊断</b><div class="summary-grid"><div><span>当前策略</span><strong class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</strong></div><div><span>买入持有</span><strong class="${cls(d.buy_hold_return_pct)}">${pct(d.buy_hold_return_pct)}</strong></div><div><span>超额收益</span><strong class="${cls(excess)}">${pct(excess)}</strong></div><div><span>交易频率</span><strong>${esc(d.trade_count||0)}笔</strong></div></div><div class="${low?'warn':'muted'}" style="margin-top:8px">${low?'当前参数偏防守或信号滞后，建议点“比较策略收益”看是否换策略/阈值更合适。':'当前策略相对基准尚可，仍要看回撤和交易次数。'}</div>`}
function renderQuickTrades(trades){}
function tradeDrawerRow(e,i){return tradeRow(e,i)}
function renderTradeDrawer(d){const events=tradeEvents(d);$('tradeDrawerSummary').innerHTML=`<div><span>标的</span><b>${esc(d.name||d.symbol)} ${esc(d.symbol)}</b></div><div><span>策略收益</span><b class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</b></div><div><span>闭合交易</span><b>${esc(d.trade_count||0)}笔</b></div><div><span>交易流水</span><b>${esc(d.trade_event_count||events.length)}条</b></div><div><span>买卖/异常点</span><b>${esc((d.markers||[]).length)} / ${esc((d.anomaly_markers||[]).length)}</b></div>`;$('tradeDrawerRows').innerHTML=events.map(tradeDrawerRow).join('')||'<tr><td colspan="13" class="muted">本次参数下无交易流水</td></tr>'}
function openTradeDrawer(){if(!lastBacktest){log('请先运行回测，再打开买卖明细');return}renderTradeDrawer(lastBacktest);$('tradeDrawer').classList.add('open');$('tradeDrawer').setAttribute('aria-hidden','false')}
function closeTradeDrawer(){$('tradeDrawer').classList.remove('open');$('tradeDrawer').setAttribute('aria-hidden','true')}
function openTradePage(){const p=params();p.set('autorun','1');window.open('/backtest/trades?'+p.toString(),'_blank')}
function scrollTradeTable(){$('tradePanel').scrollIntoView({behavior:'smooth',block:'start'})}
function applyScorePreset(){$('buyScore').value=58;$('sellScore').value=45;$('stop').value=8;log('已应用宽松评分参数：买入58 / 卖出45 / 止损8%');runBacktest()}
async function compareStrategies(){const box=$('compareBox');box.style.display='block';box.innerHTML='<b>策略收益比较</b><div class="muted">正在回测全部策略...</div>';try{const sr=await fetch('/api/backtest/strategies',{cache:'no-store'});const sj=await sr.json();const list=(sj.data||[]);const base=params();const current=$('strategy').value;const rows=await Promise.all(list.map(async s=>{const p=new URLSearchParams(base);p.set('strategy',s.key);const r=await fetch('/api/backtest/run?'+p.toString(),{cache:'no-store'});const j=await r.json();return j.ok?{key:s.key,name:s.name,ret:Number(j.data.total_return_pct||0),dd:Number(j.data.max_drawdown_pct||0),trades:j.data.trade_count}:null}));const ok=rows.filter(Boolean).sort((a,b)=>b.ret-a.ret);box.innerHTML='<b>策略收益比较</b>'+ok.map(x=>`<div class="compare-row ${x.key===current?'current':''}"><span>${esc(x.name)}${x.key===current?' · 当前':''}</span><b class="${cls(x.ret)}">${pct(x.ret)}</b><span>${esc(x.trades)}笔</span></div>`).join('')+'<div class="muted" style="margin-top:6px">只做同一标的、同一费用/滑点/仓位参数下的研究比较。</div>'}catch(e){box.innerHTML='<b>策略收益比较</b><div class="warn">比较失败：'+esc(e)+'</div>'}}
function setupCanvas(id,minH=80){const canvas=$(id),box=canvas.parentElement,ctx=canvas.getContext('2d');const rect=box.getBoundingClientRect();const ratio=window.devicePixelRatio||1;canvas.width=Math.max(320,Math.floor(rect.width*ratio));canvas.height=Math.max(minH,Math.floor(rect.height*ratio));ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,rect.width,rect.height);return{canvas,ctx,w:rect.width,h:rect.height}}
function grid(ctx,w,h,pad){ctx.strokeStyle='rgba(148,163,184,.16)';ctx.lineWidth=1;for(let i=0;i<5;i++){const y=pad.t+(h-pad.t-pad.b)*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke()}for(let i=1;i<4;i++){const x=pad.l+(w-pad.l-pad.r)*i/4;ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,h-pad.b);ctx.stroke()}}
function xScale(rows,w,pad){return i=>pad.l+(w-pad.l-pad.r)*(rows.length<=1?.5:i/(rows.length-1))}
function isRecentAnomaly(row,latestDate){const current=new Date(String(row.date||'')+'T00:00:00');return Number.isFinite(current.getTime())&&Number.isFinite(latestDate.getTime())&&(latestDate-current)/(24*3600*1000)<=7}
function visibleAnomalies(row,latestDate){const values=row.anomaly_markers||[];return (showAllAnomalies?values:values.filter(m=>Number(m.severity||0)>=3||isRecentAnomaly(row,latestDate))).slice(0,showAllAnomalies?4:2)}
function toggleTradeMarkers(btn){showTradeMarkers=!showTradeMarkers;btn.classList.toggle('active',showTradeMarkers);btn.textContent='买卖点：'+(showTradeMarkers?'显示':'隐藏');if(lastBacktest)drawKline(lastBacktest.kline||[])}
function toggleAnomalyMarkers(btn){showAllAnomalies=!showAllAnomalies;btn.textContent=showAllAnomalies?'异常：全部（每日最多4个）':'异常：近7日/严重';if(lastBacktest)drawKline(lastBacktest.kline||[])}
function drawKline(rows){const {ctx,w,h}=setupCanvas('klineChart',260);$('klineEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:22,b:28},latestDate=new Date(String(rows[rows.length-1].date||'')+'T00:00:00');const markerPrices=rows.flatMap(r=>[...(showTradeMarkers?(r.markers||[]):[]).map(m=>Number(m.price)),...visibleAnomalies(r,latestDate).map(m=>Number(m.price))]).filter(Number.isFinite);let max=Math.max(...rows.map(x=>Number(x.high||0)),...markerPrices),min=Math.min(...rows.map(x=>Number(x.low||0)),...markerPrices);const span=(max-min)||1;max+=span*.04;min-=span*.04;const y=v=>h-pad.b-(h-pad.t-pad.b)*((Number(v)-min)/(max-min||1));const x=xScale(rows,w,pad);grid(ctx,w,h,pad);ctx.font='11px Segoe UI';ctx.fillStyle='#8ea3c3';ctx.textAlign='right';for(let i=0;i<5;i++){const yy=pad.t+(h-pad.t-pad.b)*i/4;ctx.fillText((max-(max-min)*i/4).toFixed(2),pad.l-6,yy+3)}const cw=Math.max(1,Math.min(8,(w-pad.l-pad.r)/Math.max(1,rows.length)*.62));rows.forEach((r,i)=>{const xx=x(i),o=Number(r.open),c=Number(r.close),hi=Number(r.high),lo=Number(r.low),up=c>=o;ctx.strokeStyle=up?'#ef4444':'#22c55e';ctx.fillStyle=up?'rgba(239,68,68,.8)':'rgba(34,197,94,.8)';ctx.beginPath();ctx.moveTo(xx,y(hi));ctx.lineTo(xx,y(lo));ctx.stroke();const y1=y(o),y2=y(c);ctx.fillRect(xx-cw/2,Math.min(y1,y2),cw,Math.max(1,Math.abs(y2-y1)))});drawLine(ctx,rows,'ma5',x,y,'#a78bfa');drawLine(ctx,rows,'ma20',x,y,'#f59e0b');drawLine(ctx,rows,'ma60',x,y,'#60a5fa');rows.forEach((r,i)=>{if(showTradeMarkers)(r.markers||[]).forEach(m=>{const xx=x(i),isBuy=m.side==='buy',yy=y(m.price)+(isBuy?12:-12);ctx.fillStyle=isBuy?'#22c55e':'#ef4444';ctx.beginPath();if(isBuy){ctx.moveTo(xx,yy-10);ctx.lineTo(xx-7,yy+4);ctx.lineTo(xx+7,yy+4)}else{ctx.moveTo(xx,yy+10);ctx.lineTo(xx-7,yy-4);ctx.lineTo(xx+7,yy-4)}ctx.closePath();ctx.fill();ctx.fillStyle='#dbeafe';ctx.textAlign='center';ctx.font='10px Segoe UI';ctx.fillText(isBuy?'B':'S',xx,yy+(isBuy?16:-8))});visibleAnomalies(r,latestDate).forEach((m,j)=>{const xx=x(i),yy=y(m.price)-j*14;ctx.fillStyle=Number(m.severity||0)>=3?'#fb923c':'#f59e0b';ctx.beginPath();ctx.arc(xx,yy,6,0,Math.PI*2);ctx.fill();ctx.fillStyle='#111827';ctx.textAlign='center';ctx.font='bold 10px Segoe UI';ctx.fillText('!',xx,yy+3)})});ctx.fillStyle='#8ea3c3';ctx.textAlign='left';ctx.fillText(rows[0].date,pad.l,h-8);ctx.textAlign='right';ctx.fillText(rows[rows.length-1].date,w-pad.r,h-8);ctx.textAlign='left';ctx.fillStyle='#a78bfa';ctx.fillText('MA5',pad.l+4,14);ctx.fillStyle='#f59e0b';ctx.fillText('MA20',pad.l+42,14);ctx.fillStyle='#60a5fa';ctx.fillText('MA60',pad.l+88,14);ctx.fillStyle='#22c55e';ctx.fillText('B买',pad.l+136,14);ctx.fillStyle='#ef4444';ctx.fillText('S卖',pad.l+174,14);ctx.fillStyle='#f59e0b';ctx.fillText(showAllAnomalies?'!全部':'!近7日/严重',pad.l+212,14)}
function drawLine(ctx,rows,key,x,y,color){ctx.strokeStyle=color;ctx.lineWidth=1.4;ctx.beginPath();let started=false;rows.forEach((r,i)=>{if(r[key]==null)return;const xx=x(i),yy=y(r[key]);if(started)ctx.lineTo(xx,yy);else{ctx.moveTo(xx,yy);started=true}});ctx.stroke()}
function drawVolume(rows){const {ctx,w,h}=setupCanvas('volumeChart',80);$('volumeEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:12,b:18};grid(ctx,w,h,pad);const max=Math.max(...rows.map(r=>Number(r.volume||0)),1);const x=xScale(rows,w,pad);const bw=Math.max(1,Math.min(7,(w-pad.l-pad.r)/Math.max(1,rows.length)*.68));rows.forEach((r,i)=>{const vol=Number(r.volume||0),bh=(h-pad.t-pad.b)*vol/max,up=Number(r.close)>=Number(r.open);ctx.fillStyle=up?'rgba(239,68,68,.78)':'rgba(34,197,94,.78)';ctx.fillRect(x(i)-bw/2,h-pad.b-bh,bw,Math.max(1,bh));if(Number(r.volume_ratio||0)>=2.8){ctx.strokeStyle='#f59e0b';ctx.strokeRect(x(i)-bw/2-1,h-pad.b-bh-1,bw+2,Math.max(3,bh+2))}});ctx.fillStyle='#bfdbfe';ctx.font='12px Segoe UI';ctx.textAlign='left';ctx.fillText('成交量 / 量比异常高亮',pad.l,14);ctx.textAlign='right';ctx.fillStyle='#8ea3c3';ctx.fillText((max/10000).toFixed(1)+'万',w-pad.r,14)}
function drawSignal(rows,params){const {ctx,w,h}=setupCanvas('signalChart',96);$('signalEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:14,b:18};const x=xScale(rows,w,pad);ctx.font='11px Segoe UI';ctx.strokeStyle='rgba(148,163,184,.16)';ctx.lineWidth=1;for(const lv of [40,50,62,72]){const yy=pad.t+(h-pad.t-pad.b)*.58*(1-lv/100);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillStyle='#8ea3c3';ctx.textAlign='right';ctx.fillText(String(lv),pad.l-6,yy+3)}const scoreY=v=>pad.t+(h-pad.t-pad.b)*.58*(1-Number(v||0)/100);drawThreshold(Number(params.buy_score||62),'#22c55e');drawThreshold(Number(params.sell_score||48),'#ef4444');ctx.strokeStyle='#60a5fa';ctx.lineWidth=2;ctx.beginPath();let started=false;rows.forEach((r,i)=>{if(r.score==null)return;const xx=x(i),yy=scoreY(r.score);if(started)ctx.lineTo(xx,yy);else{ctx.moveTo(xx,yy);started=true}});ctx.stroke();const hist=rows.map(r=>Number(r.macd_hist||0));const maxAbs=Math.max(...hist.map(v=>Math.abs(v)),.001);const zero=h-pad.b-24;ctx.strokeStyle='rgba(148,163,184,.35)';ctx.beginPath();ctx.moveTo(pad.l,zero);ctx.lineTo(w-pad.r,zero);ctx.stroke();const bw=Math.max(1,Math.min(7,(w-pad.l-pad.r)/Math.max(1,rows.length)*.62));hist.forEach((v,i)=>{const bh=22*Math.abs(v)/maxAbs;ctx.fillStyle=v>=0?'rgba(239,68,68,.72)':'rgba(34,197,94,.72)';ctx.fillRect(x(i)-bw/2,v>=0?zero-bh:zero,bw,Math.max(1,bh))});ctx.fillStyle='#bfdbfe';ctx.textAlign='left';ctx.fillText('评分线 / MACD柱',pad.l,12);ctx.fillStyle='#60a5fa';ctx.fillText('最新评分 '+(rows[rows.length-1].score??'--'),pad.l+110,12);function drawThreshold(v,color){const yy=scoreY(v);ctx.save();ctx.strokeStyle=color;ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.restore()}}
function drawEquity(curve){const {ctx,w,h}=setupCanvas('chart',90);$('empty').style.display=curve.length?'none':'flex';if(!curve.length)return;const vals=curve.map(x=>Number(x.equity||0));const min=Math.min(...vals),max=Math.max(...vals);const pad={l:48,r:18,t:16,b:22};grid(ctx,w,h,pad);ctx.strokeStyle='#60a5fa';ctx.lineWidth=2;ctx.beginPath();vals.forEach((v,i)=>{const x=pad.l+(w-pad.l-pad.r)*(i/(vals.length-1||1));const y=h-pad.b-(h-pad.t-pad.b)*((v-min)/(max-min||1));if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y)});ctx.stroke();ctx.fillStyle='#bfdbfe';ctx.font='12px Segoe UI';ctx.textAlign='left';ctx.fillText('权益 '+money(vals[vals.length-1]),pad.l,14);ctx.textAlign='right';ctx.fillStyle='#8ea3c3';ctx.fillText(money(max),w-pad.r,14)}
function btPeriod(d){const p=d.period||{};const q=d.data_quality||{};return {start:p.start||q.start||'--',end:p.end||q.end||'--',bars:p.bars||q.bars||0,days:p.calendar_days||'--'}}
function summaryHtml(d){const excess=Number(d.excess_return_pct||0),cost=d.cost_summary||{},pos=d.position_summary||{},p=btPeriod(d),low=Number(d.total_return_pct||0)<0||excess<0;return `<b>收益诊断</b><div class="summary-grid"><div><span>当前策略</span><strong class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</strong></div><div><span>买入持有</span><strong class="${cls(d.buy_hold_return_pct)}">${pct(d.buy_hold_return_pct)}</strong></div><div><span>超额收益</span><strong class="${cls(excess)}">${pct(excess)}</strong></div><div><span>交易频率</span><strong>${esc(d.trade_count||0)}笔</strong></div><div><span>回测区间</span><strong style="font-size:13px">${esc(p.start)} 至 ${esc(p.end)}</strong></div><div><span>K线/自然日</span><strong>${esc(p.bars)} / ${esc(p.days)}</strong></div><div><span>交易成本</span><strong>${money(cost.total_cost||0)}</strong></div><div><span>佣金/滑点</span><strong style="font-size:13px">${money(cost.commission||0)} / ${money(cost.slippage_cost_est||0)}</strong></div><div><span>期末现金</span><strong>${money(pos.cash||d.final_equity)}</strong></div><div><span>期末持仓</span><strong>${esc(pos.shares||0)}股</strong></div></div><div class="${low?'warn':'muted'}" style="margin-top:8px">${low?'当前参数偏防守或信号滞后，建议点“比较策略收益”查看是否换策略/阈值更合适。':'当前策略相对基准尚可，仍要看回撤、交易次数和成本占比。'}</div><div class="muted" style="margin-top:6px">${esc(pos.note||'')}</div>`}
function summaryHtml(d){const excess=Number(d.excess_return_pct||0),cost=d.cost_summary||{},pos=d.position_summary||{},p=btPeriod(d),params=d.params||{},combo=(d.strategy_combo_names||[]).join('、')||'未启用',low=Number(d.total_return_pct||0)<0||excess<0;return `<b>收益诊断</b><div class="summary-grid"><div><span>当前策略</span><strong class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</strong></div><div><span>买入持有</span><strong class="${cls(d.buy_hold_return_pct)}">${pct(d.buy_hold_return_pct)}</strong></div><div><span>超额收益</span><strong class="${cls(excess)}">${pct(excess)}</strong></div><div><span>交易频率</span><strong>${esc(d.trade_count||0)}笔</strong></div><div><span>回测区间</span><strong style="font-size:13px">${esc(p.start)} 至 ${esc(p.end)}</strong></div><div><span>K线/自然日</span><strong>${esc(p.bars)} / ${esc(p.days)}</strong></div><div><span>组合策略</span><strong style="font-size:13px" title="${esc(combo)}">${esc(combo.length>20?combo.slice(0,20)+'...':combo)}</strong></div><div><span>止损/止盈</span><strong style="font-size:13px">${esc(params.stop_loss_pct??'--')}% / ${esc(params.take_profit_pct??0)}%</strong></div><div><span>平均成本/股</span><strong>${esc(pos.avg_cost_basis||cost.avg_cost_basis||'--')}</strong></div><div><span>最大持仓</span><strong>${esc(pos.max_shares||cost.max_position_shares||0)}股</strong></div><div><span>交易成本</span><strong>${money(cost.total_cost||0)}</strong></div><div><span>期末现金/持仓</span><strong style="font-size:13px">${money(pos.cash||d.final_equity)} / ${esc(pos.shares||0)}股</strong></div></div><div class="${low?'warn':'muted'}" style="margin-top:8px">${low?'当前参数偏防守或信号滞后，建议用“比较策略收益”查看是否换策略/阈值更合适。':'当前策略相对基准尚可，仍要看回撤、交易次数和成本占比。'}</div><div class="muted" style="margin-top:6px">${esc(pos.note||'')} 固定止盈为0表示不开启；止损和止盈会在收盘信号后，下一交易日开盘执行。</div>`}
function renderTradeDrawer(d){const events=tradeEvents(d),cost=d.cost_summary||{},pos=d.position_summary||{},p=btPeriod(d),params=d.params||{},metrics=d.metrics||{};$('tradeDrawerSummary').innerHTML=`<div><span>标的</span><b>${esc(d.name||d.symbol)} ${esc(d.symbol)}</b></div><div><span>回测区间</span><b style="font-size:15px">${esc(p.start)} 至 ${esc(p.end)}</b></div><div><span>策略收益</span><b class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</b></div><div><span>闭合交易</span><b>${esc(d.trade_count||0)}笔</b></div><div><span>交易流水</span><b>${esc(d.trade_event_count||events.length)}条</b></div><div><span>仓位模式</span><b>${esc(paramName(sizingNames,params.position_sizing||'score_weighted'))}</b></div><div><span>交易周期</span><b>${esc(paramName(horizonNames,params.horizon||'swing'))}</b></div><div><span>复利</span><b>${params.compound_returns===false?'关闭':'开启'}</b></div><div><span>总成本</span><b>${money(cost.total_cost||0)}</b></div><div><span>成交额</span><b>${money(cost.turnover||0)}</b></div><div><span>平均成本/股</span><b>${esc(pos.avg_cost_basis||cost.avg_cost_basis||'--')}</b></div><div><span>最大持仓</span><b>${esc(pos.max_shares||cost.max_position_shares||0)}股</b></div><div><span>期末现金</span><b>${money(pos.cash||d.final_equity)}</b></div><div><span>期末持仓</span><b>${esc(pos.shares||0)}股</b></div><div><span>期望/赔率</span><b style="font-size:15px">${esc(metrics.expectancy??'--')} / ${esc(metrics.payoff_ratio??'--')}</b></div>`;$('tradeDrawerRows').innerHTML=events.map(tradeDrawerRow).join('')||'<tr><td colspan="13" class="muted">本次参数下无交易流水</td></tr>'}
function summaryHtml(d){const excess=Number(d.excess_return_pct||0),cost=d.cost_summary||{},pos=d.position_summary||{},p=btPeriod(d),params=d.params||{},metrics=d.metrics||{},combo=(d.strategy_combo_names||[]).join('、')||'未启用',low=Number(d.total_return_pct||0)<0||excess<0;const sizing=paramName(sizingNames,params.position_sizing||params.sizing_mode||'score_weighted');const horizon=paramName(horizonNames,params.horizon||'swing');const effPos=params.effective_position_pct!=null?(Number(params.effective_position_pct)*100).toFixed(1)+'%':'--';const effStop=params.effective_stop_loss_pct??params.stop_loss_pct??'--';const effTake=params.effective_take_profit_pct??params.take_profit_pct??0;return `<b>收益诊断</b><div class="summary-grid"><div><span>当前策略</span><strong class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</strong></div><div><span>买入持有</span><strong class="${cls(d.buy_hold_return_pct)}">${pct(d.buy_hold_return_pct)}</strong></div><div><span>超额收益</span><strong class="${cls(excess)}">${pct(excess)}</strong></div><div><span>交易频率</span><strong>${esc(d.trade_count||0)}笔</strong></div><div><span>回测区间</span><strong style="font-size:13px">${esc(p.start)} 至 ${esc(p.end)}</strong></div><div><span>K线/自然日</span><strong>${esc(p.bars)} / ${esc(p.days)}</strong></div><div><span>组合策略</span><strong style="font-size:13px" title="${esc(combo)}">${esc(combo.length>20?combo.slice(0,20)+'...':combo)}</strong></div><div><span>仓位/周期</span><strong style="font-size:13px">${esc(sizing)} / ${esc(horizon)} / ${esc(effPos)}</strong></div><div><span>复利</span><strong>${params.compound_returns===false?'关闭':'开启'}</strong></div><div><span>期望/赔率</span><strong style="font-size:13px">${esc(metrics.expectancy??'--')} / ${esc(metrics.payoff_ratio??'--')}</strong></div><div><span>均盈/均亏</span><strong style="font-size:13px">${esc(metrics.avg_win??'--')} / ${esc(metrics.avg_loss??'--')}</strong></div><div><span>连亏上限观察</span><strong>${esc(metrics.max_consecutive_losses??0)}次</strong></div><div><span>止损/止盈</span><strong style="font-size:13px">${esc(effStop)}% / ${esc(effTake)}%</strong></div><div><span>平均成本/股</span><strong>${esc(pos.avg_cost_basis||cost.avg_cost_basis||'--')}</strong></div><div><span>最大持仓</span><strong>${esc(pos.max_shares||cost.max_position_shares||0)}股</strong></div><div><span>期末现金/持仓</span><strong style="font-size:13px">${money(pos.cash||d.final_equity)} / ${esc(pos.shares||0)}股</strong></div></div><div class="${low?'warn':'muted'}" style="margin-top:8px">${low?'当前参数偏防守或信号滞后，可用“比较策略收益”和仓位模式继续调参。':'当前策略相对基准尚可，仍要看回撤、交易次数、成本和仓位风险。'}</div><div class="muted" style="margin-top:6px">买入/卖出已经拆成独立流水；固定止盈为0表示不开启，止损/止盈信号下一交易日开盘执行。${esc(pos.note||'')}</div>`}
const q=new URLSearchParams(location.search);
if(q.get('symbol'))$('symbol').value=q.get('symbol');
if(q.get('strategy'))$('strategy').value=q.get('strategy');
if(q.get('strategy_combo')){const chosen=new Set(q.get('strategy_combo').split(',').filter(Boolean));document.querySelectorAll('.combo-strategy').forEach(x=>x.checked=chosen.has(x.value))}
if(q.get('combo_buy_rule'))$('comboBuyRule').value=q.get('combo_buy_rule');
if(q.get('combo_sell_rule'))$('comboSellRule').value=q.get('combo_sell_rule');
if(q.get('position_sizing')&&$('sizingMode'))$('sizingMode').value=q.get('position_sizing');
if(q.get('sizing_mode')&&$('sizingMode'))$('sizingMode').value=q.get('sizing_mode');
if(q.get('horizon')&&$('horizonMode'))$('horizonMode').value=q.get('horizon');
if(q.get('compound_returns')&&$('compoundReturns'))$('compoundReturns').checked=q.get('compound_returns')!=='false';
[['dcaAmount','dca_amount'],['pyramidStep','pyramid_step_pct'],['pyramidAdds','pyramid_max_adds'],['atrRisk','atr_risk_pct'],['fundamentalWeight','fundamental_weight'],['technicalWeight','technical_weight'],['informationWeight','information_weight'],['fundFlowWeight','fund_flow_weight'],['marketWeight','market_weight']].forEach(([id,key])=>{if(q.get(key)&&$(id))$(id).value=q.get(key)});
toggleComboBox();
loadAutoConfigForBacktest(false).catch(e=>log('总控台配置初始化失败 '+e));
window.addEventListener('resize',()=>{if(lastBacktest)render(lastBacktest)});
if(q.get('autorun')==='1'||q.get('symbol'))runBacktest();
</script>
</body>
</html>'''


def build_backtest_trades_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Backtest Trades</title>
<style>
:root{--bg:#0b1020;--panel:#111827;--line:#283956;--text:#dbeafe;--muted:#91a7c7;--green:#22c55e;--red:#ef4444}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif}header{height:58px;display:flex;align-items:center;gap:10px;padding:0 18px;background:#101827;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}.brand{font-weight:900;font-size:18px;color:#bfdbfe}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.grow{flex:1}button{border:0;background:#253149;color:#c7d2fe;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer}.main{padding:16px;display:flex;flex-direction:column;gap:12px}.cards{display:grid;grid-template-columns:repeat(8,minmax(130px,1fr));gap:10px}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px}.card{padding:10px;min-width:0}.card span{display:block;color:var(--muted);font-size:12px}.card b{display:block;text-align:right;font-size:20px;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.panel{overflow:hidden}.panel-h{min-height:46px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 12px;background:#141f35;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.table-wrap{height:calc(100vh - 238px);min-height:420px;overflow:auto;border:1px solid var(--line);border-radius:12px;background:#0f172a}table{width:100%;min-width:1420px;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid rgba(38,54,79,.8);padding:9px;text-align:right;white-space:nowrap;vertical-align:top}th{position:sticky;top:0;background:#182238;color:#93c5fd;z-index:2}th:first-child,td:first-child{text-align:left}td.reason,th.reason{white-space:normal;min-width:340px;text-align:left;line-height:1.5}.muted{color:var(--muted)}.up{color:#fca5a5}.down{color:#86efac}.warn{color:#fcd34d}@media(max-width:1100px){.cards{grid-template-columns:repeat(2,1fr)}.table-wrap{height:auto;min-height:520px}}
</style>
</head>
<body>
<header><span class="dot"></span><div class="brand">&#20132;&#26131;&#22238;&#27979;&#20080;&#21334;&#26126;&#32454;</div><span id="sub" class="muted">--</span><div class="grow"></div><button onclick="history.back()">&#36820;&#22238;</button><button onclick="location.href='/backtest?'+params().toString()">&#22238;&#27979;&#39029;</button></header>
<main class="main">
  <div class="cards">
    <div class="card"><span>&#31574;&#30053;&#25910;&#30410;</span><b id="mRet">--</b></div>
    <div class="card"><span>&#20080;&#20837;&#25345;&#26377;</span><b id="mHold">--</b></div>
    <div class="card"><span>&#36229;&#39069;&#25910;&#30410;</span><b id="mExcess">--</b></div>
    <div class="card"><span>&#20132;&#26131;&#27425;&#25968;</span><b id="mTrades">--</b></div>
    <div class="card"><span>&#26368;&#22823;&#22238;&#25764;</span><b id="mDd">--</b></div>
    <div class="card"><span>回测区间</span><b id="mPeriod">--</b></div>
    <div class="card"><span>总成本</span><b id="mCost">--</b></div>
    <div class="card"><span>期末现金/持仓</span><b id="mPos">--</b></div>
  </div>
  <section class="panel">
    <div class="panel-h"><span>完整交易流水</span><span id="note" class="muted">--</span></div>
    <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>#</th><th>交易日</th><th>动作</th><th>价格</th><th>股数</th><th>成交额</th><th>费用</th><th>现金变动</th><th>现金余额</th><th>持仓股数</th><th>成本/股</th><th>已实现盈亏</th><th class="reason">交易依据</th></tr></thead><tbody id="rows"><tr><td colspan="13" class="muted">加载交易流水中...</td></tr></tbody></table></div></div>
  </section>
</main>
<script>
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const money=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2}),pct=n=>(Number(n||0)).toFixed(2)+'%',cls=n=>Number(n)>=0?'up':'down';
function params(){const p=new URLSearchParams(location.search);if(!p.get('symbol'))p.set('symbol','300750');p.set('legacy','true');p.delete('autorun');return p}
function tradeEvents(d){if(Array.isArray(d.trade_events)&&d.trade_events.length)return d.trade_events;return (d.trades||[]).flatMap((t,i)=>legacyTradeEvents(t,i))}
function legacyTradeEvents(t,i){const shares=t.buy_shares??t.shares??0;return [{event_id:`${i+1}-B`,trade_index:i+1,date:t.entry_date,side:'buy',action:'买入',price:t.entry_price,shares,amount:t.entry_value,fee:t.entry_fee,cash_change:-(Number(t.entry_cost??0)),cash_after:Number(t.cash_before_entry||0)-Number(t.entry_cost||0),position_shares:shares,cost_basis:t.cost_basis,realized_pnl:0,realized_pct:0,reason:t.entry_reason,signal_date:t.entry_signal_date,score:t.entry_signal_score},{event_id:`${i+1}-S`,trade_index:i+1,date:t.exit_date,side:'sell',action:'卖出',price:t.exit_price,shares:t.sell_shares??shares,amount:t.exit_value,fee:t.exit_fee,cash_change:t.exit_proceeds,cash_after:t.cash_after_exit,position_shares:0,cost_basis:t.cost_basis,realized_pnl:t.pnl,realized_pct:t.pnl_pct,reason:t.exit_reason,signal_date:t.exit_signal_date,score:t.exit_signal_score}]}
function row(e,i){const isSell=e.side==='sell';const sideCls=e.side==='buy'?'up':'down';const pnl=isSell?money(e.realized_pnl):'--';const pnlCls=isSell?cls(e.realized_pnl):'muted';const score=e.score==null?'--':e.score;return `<tr><td>${i+1}</td><td>${esc(e.date||'--')}</td><td class="${sideCls}">${esc(e.action||e.side||'--')}</td><td>${esc(e.price??'--')}</td><td>${esc(e.shares??0)}</td><td>${money(e.amount)}</td><td>${money(e.fee)}</td><td class="${cls(e.cash_change)}">${money(e.cash_change)}</td><td>${e.cash_after==null?'--':money(e.cash_after)}</td><td>${esc(e.position_shares??'--')}</td><td>${esc(e.cost_basis??'--')}</td><td class="${pnlCls}">${pnl}${isSell?' / '+pct(e.realized_pct):''}</td><td class="reason">${esc(e.reason||'--')}<br><small class="muted">信号日 ${esc(e.signal_date||'--')} · 评分 ${esc(score)} · 闭合#${esc(e.trade_index||'--')}</small></td></tr>`}
async function load(){try{const p=params();const r=await fetch('/api/backtest/run?'+p.toString(),{cache:'no-store'});const js=await r.json();if(!r.ok||!js.ok)throw new Error(js.message||('HTTP '+r.status));const d=js.data;const events=tradeEvents(d),cost=d.cost_summary||{},pos=d.position_summary||{},period=d.period||d.data_quality||{};$('sub').textContent=`${d.name} ${d.symbol} · ${d.strategy_name}`;$('mRet').textContent=pct(d.total_return_pct);$('mRet').className=cls(d.total_return_pct);$('mHold').textContent=pct(d.buy_hold_return_pct);$('mHold').className=cls(d.buy_hold_return_pct);$('mExcess').textContent=pct(d.excess_return_pct);$('mExcess').className=cls(d.excess_return_pct);$('mTrades').textContent=(d.trade_count||0)+'笔';$('mDd').textContent=pct(d.max_drawdown_pct);$('mPeriod').textContent=`${period.start||'--'} 至 ${period.end||'--'}`;$('mCost').textContent=money(cost.total_cost||0);$('mPos').textContent=`${money(pos.cash||d.final_equity)} / ${pos.shares||0}股`;$('note').textContent=`${d.data_quality.start} 至 ${d.data_quality.end} · ${events.length} 条流水 · ${d.trade_count||0} 笔闭合 · 最大持仓 ${(d.position_summary||{}).max_shares||0}股 · 平均成本/股 ${pos.avg_cost_basis||cost.avg_cost_basis||'--'}`;$('rows').innerHTML=events.map(row).join('')||'<tr><td colspan="13" class="muted">本次参数下无交易流水</td></tr>'}catch(e){$('rows').innerHTML='<tr><td colspan="13" class="warn">&#21152;&#36733;&#22833;&#36133; '+esc(e)+'</td></tr>'}}
load();
</script>
</body>
</html>'''


def build_paper_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Paper Trading V3.19</title>
<style>
:root{--bg:#0b1020;--panel:#111827;--line:#283956;--text:#dbeafe;--muted:#91a7c7;--green:#22c55e}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif}header{height:58px;display:flex;align-items:center;gap:10px;padding:0 18px;background:#101827;border-bottom:1px solid var(--line)}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.brand{font-weight:900;color:#bfdbfe;font-size:18px}.grow{flex:1}button{border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:800;padding:9px 12px;cursor:pointer}.btn2{background:#253149;color:#c7d2fe}main{padding:16px;display:grid;grid-template-columns:360px 1fr;gap:14px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-h{min-height:46px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;background:#141f35;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.section{font-size:13px;color:var(--muted);margin:12px 0 6px}input,select{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px 11px}.hint,.card{background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px;color:#b6c7e2;line-height:1.55}.cards{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:10px}.card span{display:block;color:var(--muted);font-size:12px}.card b{display:block;text-align:right;font-size:20px}pre{white-space:pre-wrap;word-break:break-word;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:12px;max-height:520px;overflow:auto}.disclaimer{color:#fcd34d}@media(max-width:1000px){main{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header><span class="dot"></span><div class="brand">纸面交易系统 V3.19</div><span class="disclaimer">研究辅助，不构成投资建议；未接入真实券商</span><div class="grow"></div><button class="btn2" onclick="location.href='/auto-trading'">自动交易总控台</button><button class="btn2" onclick="location.href='/backtest'">交易回测</button><button class="btn2" onclick="location.href='/screener'">筛选系统</button></header>
<main>
  <section class="panel">
    <div class="panel-h">纸面信号</div>
    <div class="panel-b">
      <div class="grid2">
        <div><div class="section">代码</div><input id="symbol" value="300750"></div>
        <div><div class="section">动作</div><select id="action"><option value="buy">买入</option><option value="sell">卖出</option></select></div>
        <div><div class="section">评分</div><input id="score" value="68" type="number"></div>
        <div><div class="section">目标仓位</div><input id="weight" value="0.2" type="number" step="0.01"></div>
        <div><div class="section">成交价</div><input id="price" value="20" type="number" step="0.01"></div>
        <div><div class="section">成交量</div><input id="volume" value="1000000" type="number"></div>
      </div>
      <div class="section">理由</div><input id="reason" value="手动纸面信号验证">
      <div style="display:flex;gap:8px;margin-top:12px"><button onclick="sendSignal()">生成纸面订单</button><button class="btn2" onclick="fillLast()">模拟成交</button><button class="btn2" onclick="loadState()">刷新状态</button></div>
      <div class="hint" style="margin-top:12px">纸面交易只接收策略信号、生成虚拟订单并按 V3.19 执行模型撮合，用于把回测逻辑延伸到仿真跟踪，不会提交真实委托。</div>
    </div>
  </section>
  <section class="panel">
    <div class="panel-h">账户状态</div>
    <div class="panel-b">
      <div class="cards">
        <div class="card"><span>现金</span><b id="cash">--</b></div>
        <div class="card"><span>权益</span><b id="equity">--</b></div>
        <div class="card"><span>订单</span><b id="orders">--</b></div>
        <div class="card"><span>成交</span><b id="fills">--</b></div>
      </div>
      <pre id="state">Loading...</pre>
    </div>
  </section>
</main>
<script>
const $=id=>document.getElementById(id),money=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2});let lastOrder=null;
async function loadState(){const r=await fetch('/api/paper/state',{cache:'no-store'});const js=await r.json();const d=js.data||{};$('cash').textContent=money(d.cash);$('equity').textContent=money(d.equity);$('orders').textContent=(d.orders||[]).length;$('fills').textContent=(d.fills||[]).length;$('state').textContent=JSON.stringify(js,null,2);lastOrder=(d.orders||[]).slice(-1)[0]||lastOrder}
async function sendSignal(){const body={symbol:$('symbol').value,action:$('action').value,score:Number($('score').value),target_weight:Number($('weight').value),reason:$('reason').value,date:new Date().toISOString().slice(0,10)};const r=await fetch('/api/paper/signal',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const js=await r.json();lastOrder=(js.data||{}).order;$('state').textContent=JSON.stringify(js,null,2);await loadState()}
async function fillLast(){if(!lastOrder){await loadState()}if(!lastOrder){return}const price=Number($('price').value||0);const body={order_id:lastOrder.order_id,price,open:price,high:price*1.01,low:price*.99,close:price,volume:Number($('volume').value||1000000),date:new Date().toISOString().slice(0,10)};const r=await fetch('/api/paper/fill',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const js=await r.json();$('state').textContent=JSON.stringify(js,null,2);await loadState()}
loadState();
</script>
</body>
</html>'''
