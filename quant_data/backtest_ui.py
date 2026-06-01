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
</style>
</head>
<body>
<div class="app">
  <div class="top"><span class="dot"></span><div class="brand">交易回测系统</div><span class="pill">日线 · 下一开盘成交 · 手续费/滑点</span><div class="grow"></div><button class="btn2" onclick="location.href='/screener'">筛选系统</button><button class="btn2" onclick="location.href='/ui'">行情监控</button></div>
  <aside class="side">
    <div class="section">标的代码</div>
    <input id="symbol" value="300750" />
    <div class="section">策略</div>
    <select id="strategy"><option value="score_driven" selected>日评分驱动</option><option value="score_reversal">评分拐点修复</option><option value="ma_cross">MA趋势跟随</option><option value="rsi_rebound">RSI超跌反弹</option><option value="breakout">20日突破放量</option><option value="macd_momentum">MACD动量确认</option><option value="boll_pullback">BOLL回踩修复</option><option value="trend_pullback">趋势回踩MA20</option></select>
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
    <div class="row" style="margin-top:12px"><button id="runBtn" class="btn-green" onclick="runBacktest()">运行回测</button><button class="btn2" onclick="fillSelected()">使用筛选选中</button></div>
    <div class="row" style="margin-top:8px"><button class="btn2" onclick="compareStrategies()">比较策略收益</button><button class="btn2" onclick="applyScorePreset()">宽松评分</button></div>
    <div class="hint">评分驱动策略会回放每日研究分：趋势、动量、量能、位置结构和风险扣分。收盘确认信号，下一交易日开盘成交；K线图会标出买入、卖出和异常点。</div>
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
        <div class="panel-h"><span id="title" class="panel-title">等待运行</span><span class="muted" id="dq">--</span></div>
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
        <div class="panel-h"><span>评分与回测假设</span><span id="strategyName" class="pill">--</span></div>
        <div class="panel-b">
          <div id="resultSummary" class="summary-box"><b>收益诊断</b><div class="muted">运行后显示当前策略、买入持有和超额收益对比。</div></div>
          <div id="compareBox" class="compare-box" style="display:none;margin-top:8px"></div>
          <div id="assumptions" class="assumptions" style="margin-top:8px"><div class="warn">请选择标的和策略后运行。</div></div>
          <div class="quick-trades" style="margin-top:8px"><div class="quick-head"><b>买卖明细</b><div class="trade-actions"><button class="link-btn" onclick="openTradeDrawer()">内置明细</button><button class="link-btn" onclick="openTradePage()">新窗口</button><button class="link-btn" onclick="scrollTradeTable()">完整表格</button></div></div><div id="tradeQuickList" class="quick-list"><div class="muted">运行后显示最近交易。</div></div></div>
        </div>
      </div>
    </div>
    <div class="panel" id="tradePanel">
      <div class="panel-h"><span>交易明细</span><span id="tradeNote" class="muted">--</span></div>
      <div class="table-wrap"><table><thead><tr><th>买入日</th><th>卖出日</th><th>买入价</th><th>卖出价</th><th>股数</th><th>盈亏</th><th>收益率</th><th>买入原因</th><th>卖出原因</th></tr></thead><tbody id="trades"><tr><td colspan="9" class="muted">暂无交易</td></tr></tbody></table></div>
    </div>
  </main>
  <div class="log" id="log">Ready.</div>
</div>
<div id="tradeDrawer" class="trade-drawer" aria-hidden="true">
  <div class="trade-drawer-panel">
    <div class="panel-h"><span>买卖明细</span><div class="trade-actions"><button class="link-btn" onclick="openTradePage()">新窗口打开</button><button class="link-btn" onclick="closeTradeDrawer()">关闭</button></div></div>
    <div class="trade-drawer-body">
      <div id="tradeDrawerSummary" class="drawer-summary"></div>
      <div class="table-wrap detail-table-wrap"><table><thead><tr><th>#</th><th>买入日</th><th>卖出日</th><th>买入价</th><th>卖出价</th><th>盈亏</th><th>收益率</th><th>买入依据</th><th>卖出依据</th></tr></thead><tbody id="tradeDrawerRows"><tr><td colspan="9" class="muted">运行回测后显示完整买卖明细</td></tr></tbody></table></div>
    </div>
  </div>
</div>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const money=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2});
const pct=n=>(Number(n||0)).toFixed(2)+'%';
let lastBacktest=null;
function log(s){$('log').textContent=new Date().toLocaleTimeString()+'  '+s+'\n'+$('log').textContent}
function cls(n){return Number(n)>=0?'up':'down'}
function fillSelected(){try{const s=localStorage.getItem('qdg_screener_selected');if(s){$('symbol').value=s;log('已读取筛选页选中标的 '+s)}else{log('未找到筛选页选中标的')}}catch(e){log('读取失败 '+e)}}
function params(){const p=new URLSearchParams();p.set('symbol',$('symbol').value.trim()||'300750');p.set('strategy',$('strategy').value);p.set('initial_cash',$('cash').value||'100000');p.set('position_pct',Number($('position').value||100)/100);p.set('fee_rate',Number($('fee').value||0)/100);p.set('slippage_rate',Number($('slip').value||0)/100);p.set('stop_loss_pct',$('stop').value||'8');p.set('take_profit_pct',$('take').value||'0');p.set('buy_score',$('buyScore').value||'62');p.set('sell_score',$('sellScore').value||'48');p.set('limit',$('limit').value||'520');p.set('adjust',$('adjust').value||'qfq');return p}
async function runBacktest(){const btn=$('runBtn');btn.disabled=true;btn.textContent='运行中...';try{log('开始回测');const resp=await fetch('/api/backtest/run?'+params().toString(),{cache:'no-store'});const js=await resp.json();if(!resp.ok||!js.ok)throw new Error(js.message||('HTTP '+resp.status));render(js.data);log('完成：'+js.data.symbol+' '+js.data.strategy_name)}catch(e){log('ERROR '+e);$('assumptions').innerHTML='<div class="warn">回测失败：'+esc(e)+'</div>'}finally{btn.disabled=false;btn.textContent='运行回测'}}
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
  $('assumptions').innerHTML=`<div class="formula"><b>100分口径</b><div>${esc(formula.formula||'score = 趋势 + 动量 + 量能 + 结构 - 风险')}</div><ul>${comp}</ul><div class="data-note">${esc(formula.note||'当前回测为历史日K量价评分版本。')}</div></div>`+(d.assumptions||[]).map(x=>'<div>'+esc(x)+'</div>').join('')+`<div class="muted">最新评分 ${esc(latest.score??'--')}；趋势/动量/量能/结构/风险 = ${esc(latest.trend_score??'--')} / ${esc(latest.momentum_score??'--')} / ${esc(latest.volume_score??'--')} / ${esc(latest.structure_score??'--')} / ${esc(latest.risk_penalty??'--')}</div><div class="legend"><span>B 买入</span><span>S 卖出</span><span>! 异常/风险</span><span>蓝线 评分</span><span>柱体 MACD</span></div><div class="muted">参数：${esc(JSON.stringify(d.params))}</div>`;
  $('tradeNote').textContent=d.trade_count+' 笔闭合交易 · 买卖点 '+((d.markers||[]).length)+' 个 · 异常点 '+((d.anomaly_markers||[]).length)+' 个';
  $('trades').innerHTML=(d.trades||[]).map(tradeRow).join('')||'<tr><td colspan="9" class="muted">本次参数下无闭合交易</td></tr>';
  renderQuickTrades(d.trades||[]);
  renderTradeDrawer(d);
  drawKline(d.kline||[]);drawVolume(d.kline||[]);drawSignal(d.kline||[],d.params||{});drawEquity(d.equity_curve||[]);
}
function tradeRow(t){return `<tr><td>${esc(t.entry_date)}</td><td>${esc(t.exit_date)}</td><td>${t.entry_price}</td><td>${t.exit_price}</td><td>${t.shares}</td><td class="${cls(t.pnl)}">${money(t.pnl)}</td><td class="${cls(t.pnl_pct)}">${pct(t.pnl_pct)}</td><td>${esc(t.entry_reason)}<br><small class="muted">信号日 ${esc(t.entry_signal_date||'--')} · 评分 ${esc(t.entry_signal_score??'--')}</small></td><td>${esc(t.exit_reason)}<br><small class="muted">信号日 ${esc(t.exit_signal_date||'--')} · 评分 ${esc(t.exit_signal_score??'--')}</small></td></tr>`}
function summaryHtml(d){const excess=Number(d.excess_return_pct||0);const low=Number(d.total_return_pct||0)<0||excess<0;return `<b>收益诊断</b><div class="summary-grid"><div><span>当前策略</span><strong class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</strong></div><div><span>买入持有</span><strong class="${cls(d.buy_hold_return_pct)}">${pct(d.buy_hold_return_pct)}</strong></div><div><span>超额收益</span><strong class="${cls(excess)}">${pct(excess)}</strong></div><div><span>交易频率</span><strong>${esc(d.trade_count||0)}笔</strong></div></div><div class="${low?'warn':'muted'}" style="margin-top:8px">${low?'当前参数偏防守或信号滞后，建议点“比较策略收益”看是否换策略/阈值更合适。':'当前策略相对基准尚可，仍要看回撤和交易次数。'}</div>`}
function renderQuickTrades(trades){const list=$('tradeQuickList');if(!trades.length){list.innerHTML='<div class="muted">本次参数下无闭合交易；可降低买入评分或切换策略再试。</div>';return}list.innerHTML=trades.slice(-8).reverse().map(t=>`<div class="trade-card"><div class="line"><b>B ${esc(t.entry_date)}</b><span>${esc(t.entry_price)}</span></div><div class="line"><b>S ${esc(t.exit_date)}</b><span>${esc(t.exit_price)}</span></div><div class="line"><span>收益率</span><strong class="${cls(t.pnl_pct)}">${pct(t.pnl_pct)}</strong></div><div class="trade-reason">买：${esc(t.entry_reason)}<br>卖：${esc(t.exit_reason)}<br>评分：${esc(t.entry_signal_score??'--')} → ${esc(t.exit_signal_score??'--')}</div></div>`).join('')}
function tradeDrawerRow(t,i){return `<tr><td>${i+1}</td><td>${esc(t.entry_date)}</td><td>${esc(t.exit_date)}</td><td>${esc(t.entry_price)}</td><td>${esc(t.exit_price)}</td><td class="${cls(t.pnl)}">${money(t.pnl)}</td><td class="${cls(t.pnl_pct)}">${pct(t.pnl_pct)}</td><td>${esc(t.entry_reason)}<br><small class="muted">信号日 ${esc(t.entry_signal_date||'--')} · 评分 ${esc(t.entry_signal_score??'--')}</small></td><td>${esc(t.exit_reason)}<br><small class="muted">信号日 ${esc(t.exit_signal_date||'--')} · 评分 ${esc(t.exit_signal_score??'--')}</small></td></tr>`}
function renderTradeDrawer(d){const trades=d.trades||[];$('tradeDrawerSummary').innerHTML=`<div><span>标的</span><b>${esc(d.name||d.symbol)} ${esc(d.symbol)}</b></div><div><span>策略收益</span><b class="${cls(d.total_return_pct)}">${pct(d.total_return_pct)}</b></div><div><span>交易次数</span><b>${esc(d.trade_count||0)}笔</b></div><div><span>买卖/异常点</span><b>${esc((d.markers||[]).length)} / ${esc((d.anomaly_markers||[]).length)}</b></div>`;$('tradeDrawerRows').innerHTML=trades.map(tradeDrawerRow).join('')||'<tr><td colspan="9" class="muted">本次参数下无闭合交易</td></tr>'}
function openTradeDrawer(){if(!lastBacktest){log('请先运行回测，再打开买卖明细');return}renderTradeDrawer(lastBacktest);$('tradeDrawer').classList.add('open');$('tradeDrawer').setAttribute('aria-hidden','false')}
function closeTradeDrawer(){$('tradeDrawer').classList.remove('open');$('tradeDrawer').setAttribute('aria-hidden','true')}
function openTradePage(){const p=params();p.set('autorun','1');window.open('/backtest/trades?'+p.toString(),'_blank')}
function scrollTradeTable(){$('tradePanel').scrollIntoView({behavior:'smooth',block:'start'})}
function applyScorePreset(){$('buyScore').value=58;$('sellScore').value=45;$('stop').value=8;log('已应用宽松评分参数：买入58 / 卖出45 / 止损8%');runBacktest()}
async function compareStrategies(){const box=$('compareBox');box.style.display='block';box.innerHTML='<b>策略收益比较</b><div class="muted">正在回测全部策略...</div>';try{const sr=await fetch('/api/backtest/strategies',{cache:'no-store'});const sj=await sr.json();const list=(sj.data||[]);const base=params();const current=$('strategy').value;const rows=await Promise.all(list.map(async s=>{const p=new URLSearchParams(base);p.set('strategy',s.key);const r=await fetch('/api/backtest/run?'+p.toString(),{cache:'no-store'});const j=await r.json();return j.ok?{key:s.key,name:s.name,ret:Number(j.data.total_return_pct||0),dd:Number(j.data.max_drawdown_pct||0),trades:j.data.trade_count}:null}));const ok=rows.filter(Boolean).sort((a,b)=>b.ret-a.ret);box.innerHTML='<b>策略收益比较</b>'+ok.map(x=>`<div class="compare-row ${x.key===current?'current':''}"><span>${esc(x.name)}${x.key===current?' · 当前':''}</span><b class="${cls(x.ret)}">${pct(x.ret)}</b><span>${esc(x.trades)}笔</span></div>`).join('')+'<div class="muted" style="margin-top:6px">只做同一标的、同一费用/滑点/仓位参数下的研究比较。</div>'}catch(e){box.innerHTML='<b>策略收益比较</b><div class="warn">比较失败：'+esc(e)+'</div>'}}
function setupCanvas(id,minH=80){const canvas=$(id),box=canvas.parentElement,ctx=canvas.getContext('2d');const rect=box.getBoundingClientRect();const ratio=window.devicePixelRatio||1;canvas.width=Math.max(320,Math.floor(rect.width*ratio));canvas.height=Math.max(minH,Math.floor(rect.height*ratio));ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,rect.width,rect.height);return{canvas,ctx,w:rect.width,h:rect.height}}
function grid(ctx,w,h,pad){ctx.strokeStyle='rgba(148,163,184,.16)';ctx.lineWidth=1;for(let i=0;i<5;i++){const y=pad.t+(h-pad.t-pad.b)*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke()}for(let i=1;i<4;i++){const x=pad.l+(w-pad.l-pad.r)*i/4;ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,h-pad.b);ctx.stroke()}}
function xScale(rows,w,pad){return i=>pad.l+(w-pad.l-pad.r)*(rows.length<=1?.5:i/(rows.length-1))}
function drawKline(rows){const {ctx,w,h}=setupCanvas('klineChart',260);$('klineEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:22,b:28};const markerPrices=rows.flatMap(r=>[...(r.markers||[]).map(m=>Number(m.price)),...(r.anomaly_markers||[]).map(m=>Number(m.price))]).filter(Number.isFinite);let max=Math.max(...rows.map(x=>Number(x.high||0)),...markerPrices),min=Math.min(...rows.map(x=>Number(x.low||0)),...markerPrices);const span=(max-min)||1;max+=span*.04;min-=span*.04;const y=v=>h-pad.b-(h-pad.t-pad.b)*((Number(v)-min)/(max-min||1));const x=xScale(rows,w,pad);grid(ctx,w,h,pad);ctx.font='11px Segoe UI';ctx.fillStyle='#8ea3c3';ctx.textAlign='right';for(let i=0;i<5;i++){const yy=pad.t+(h-pad.t-pad.b)*i/4;ctx.fillText((max-(max-min)*i/4).toFixed(2),pad.l-6,yy+3)}const cw=Math.max(1,Math.min(8,(w-pad.l-pad.r)/Math.max(1,rows.length)*.62));rows.forEach((r,i)=>{const xx=x(i),o=Number(r.open),c=Number(r.close),hi=Number(r.high),lo=Number(r.low),up=c>=o;ctx.strokeStyle=up?'#ef4444':'#22c55e';ctx.fillStyle=up?'rgba(239,68,68,.8)':'rgba(34,197,94,.8)';ctx.beginPath();ctx.moveTo(xx,y(hi));ctx.lineTo(xx,y(lo));ctx.stroke();const y1=y(o),y2=y(c);ctx.fillRect(xx-cw/2,Math.min(y1,y2),cw,Math.max(1,Math.abs(y2-y1)))});drawLine(ctx,rows,'ma5',x,y,'#a78bfa');drawLine(ctx,rows,'ma20',x,y,'#f59e0b');drawLine(ctx,rows,'ma60',x,y,'#60a5fa');rows.forEach((r,i)=>{(r.markers||[]).forEach(m=>{const xx=x(i),isBuy=m.side==='buy',yy=y(m.price)+(isBuy?12:-12);ctx.fillStyle=isBuy?'#22c55e':'#ef4444';ctx.beginPath();if(isBuy){ctx.moveTo(xx,yy-10);ctx.lineTo(xx-7,yy+4);ctx.lineTo(xx+7,yy+4)}else{ctx.moveTo(xx,yy+10);ctx.lineTo(xx-7,yy-4);ctx.lineTo(xx+7,yy-4)}ctx.closePath();ctx.fill();ctx.fillStyle='#dbeafe';ctx.textAlign='center';ctx.font='10px Segoe UI';ctx.fillText(isBuy?'B':'S',xx,yy+(isBuy?16:-8))});(r.anomaly_markers||[]).forEach((m,j)=>{const xx=x(i),yy=y(m.price)-j*14;ctx.fillStyle=m.severity>=3?'#fb923c':'#f59e0b';ctx.beginPath();ctx.arc(xx,yy,6,0,Math.PI*2);ctx.fill();ctx.fillStyle='#111827';ctx.textAlign='center';ctx.font='bold 10px Segoe UI';ctx.fillText('!',xx,yy+3)})});ctx.fillStyle='#8ea3c3';ctx.textAlign='left';ctx.fillText(rows[0].date,pad.l,h-8);ctx.textAlign='right';ctx.fillText(rows[rows.length-1].date,w-pad.r,h-8);ctx.textAlign='left';ctx.fillStyle='#a78bfa';ctx.fillText('MA5',pad.l+4,14);ctx.fillStyle='#f59e0b';ctx.fillText('MA20',pad.l+42,14);ctx.fillStyle='#60a5fa';ctx.fillText('MA60',pad.l+88,14);ctx.fillStyle='#22c55e';ctx.fillText('B买',pad.l+136,14);ctx.fillStyle='#ef4444';ctx.fillText('S卖',pad.l+174,14);ctx.fillStyle='#f59e0b';ctx.fillText('!异常',pad.l+212,14)}
function drawLine(ctx,rows,key,x,y,color){ctx.strokeStyle=color;ctx.lineWidth=1.4;ctx.beginPath();let started=false;rows.forEach((r,i)=>{if(r[key]==null)return;const xx=x(i),yy=y(r[key]);if(started)ctx.lineTo(xx,yy);else{ctx.moveTo(xx,yy);started=true}});ctx.stroke()}
function drawVolume(rows){const {ctx,w,h}=setupCanvas('volumeChart',80);$('volumeEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:12,b:18};grid(ctx,w,h,pad);const max=Math.max(...rows.map(r=>Number(r.volume||0)),1);const x=xScale(rows,w,pad);const bw=Math.max(1,Math.min(7,(w-pad.l-pad.r)/Math.max(1,rows.length)*.68));rows.forEach((r,i)=>{const vol=Number(r.volume||0),bh=(h-pad.t-pad.b)*vol/max,up=Number(r.close)>=Number(r.open);ctx.fillStyle=up?'rgba(239,68,68,.78)':'rgba(34,197,94,.78)';ctx.fillRect(x(i)-bw/2,h-pad.b-bh,bw,Math.max(1,bh));if(Number(r.volume_ratio||0)>=2.8){ctx.strokeStyle='#f59e0b';ctx.strokeRect(x(i)-bw/2-1,h-pad.b-bh-1,bw+2,Math.max(3,bh+2))}});ctx.fillStyle='#bfdbfe';ctx.font='12px Segoe UI';ctx.textAlign='left';ctx.fillText('成交量 / 量比异常高亮',pad.l,14);ctx.textAlign='right';ctx.fillStyle='#8ea3c3';ctx.fillText((max/10000).toFixed(1)+'万',w-pad.r,14)}
function drawSignal(rows,params){const {ctx,w,h}=setupCanvas('signalChart',96);$('signalEmpty').style.display=rows.length?'none':'flex';if(!rows.length)return;const pad={l:48,r:18,t:14,b:18};const x=xScale(rows,w,pad);ctx.font='11px Segoe UI';ctx.strokeStyle='rgba(148,163,184,.16)';ctx.lineWidth=1;for(const lv of [40,50,62,72]){const yy=pad.t+(h-pad.t-pad.b)*.58*(1-lv/100);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillStyle='#8ea3c3';ctx.textAlign='right';ctx.fillText(String(lv),pad.l-6,yy+3)}const scoreY=v=>pad.t+(h-pad.t-pad.b)*.58*(1-Number(v||0)/100);drawThreshold(Number(params.buy_score||62),'#22c55e');drawThreshold(Number(params.sell_score||48),'#ef4444');ctx.strokeStyle='#60a5fa';ctx.lineWidth=2;ctx.beginPath();let started=false;rows.forEach((r,i)=>{if(r.score==null)return;const xx=x(i),yy=scoreY(r.score);if(started)ctx.lineTo(xx,yy);else{ctx.moveTo(xx,yy);started=true}});ctx.stroke();const hist=rows.map(r=>Number(r.macd_hist||0));const maxAbs=Math.max(...hist.map(v=>Math.abs(v)),.001);const zero=h-pad.b-24;ctx.strokeStyle='rgba(148,163,184,.35)';ctx.beginPath();ctx.moveTo(pad.l,zero);ctx.lineTo(w-pad.r,zero);ctx.stroke();const bw=Math.max(1,Math.min(7,(w-pad.l-pad.r)/Math.max(1,rows.length)*.62));hist.forEach((v,i)=>{const bh=22*Math.abs(v)/maxAbs;ctx.fillStyle=v>=0?'rgba(239,68,68,.72)':'rgba(34,197,94,.72)';ctx.fillRect(x(i)-bw/2,v>=0?zero-bh:zero,bw,Math.max(1,bh))});ctx.fillStyle='#bfdbfe';ctx.textAlign='left';ctx.fillText('评分线 / MACD柱',pad.l,12);ctx.fillStyle='#60a5fa';ctx.fillText('最新评分 '+(rows[rows.length-1].score??'--'),pad.l+110,12);function drawThreshold(v,color){const yy=scoreY(v);ctx.save();ctx.strokeStyle=color;ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.restore()}}
function drawEquity(curve){const {ctx,w,h}=setupCanvas('chart',90);$('empty').style.display=curve.length?'none':'flex';if(!curve.length)return;const vals=curve.map(x=>Number(x.equity||0));const min=Math.min(...vals),max=Math.max(...vals);const pad={l:48,r:18,t:16,b:22};grid(ctx,w,h,pad);ctx.strokeStyle='#60a5fa';ctx.lineWidth=2;ctx.beginPath();vals.forEach((v,i)=>{const x=pad.l+(w-pad.l-pad.r)*(i/(vals.length-1||1));const y=h-pad.b-(h-pad.t-pad.b)*((v-min)/(max-min||1));if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y)});ctx.stroke();ctx.fillStyle='#bfdbfe';ctx.font='12px Segoe UI';ctx.textAlign='left';ctx.fillText('权益 '+money(vals[vals.length-1]),pad.l,14);ctx.textAlign='right';ctx.fillStyle='#8ea3c3';ctx.fillText(money(max),w-pad.r,14)}
const q=new URLSearchParams(location.search);if(q.get('symbol'))$('symbol').value=q.get('symbol');if(q.get('strategy'))$('strategy').value=q.get('strategy');window.addEventListener('resize',()=>{if(lastBacktest)render(lastBacktest)});if(q.get('autorun')==='1'||q.get('symbol'))runBacktest();
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
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif}header{height:58px;display:flex;align-items:center;gap:10px;padding:0 18px;background:#101827;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}.brand{font-weight:900;font-size:18px;color:#bfdbfe}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.grow{flex:1}button{border:0;background:#253149;color:#c7d2fe;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer}.main{padding:16px;display:flex;flex-direction:column;gap:12px}.cards{display:grid;grid-template-columns:repeat(5,minmax(140px,1fr));gap:10px}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px}.card{padding:10px}.card span{display:block;color:var(--muted);font-size:12px}.card b{display:block;text-align:right;font-size:22px;margin-top:4px}.panel{overflow:hidden}.panel-h{min-height:46px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 12px;background:#141f35;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.table-wrap{height:calc(100vh - 238px);min-height:420px;overflow:auto;border:1px solid var(--line);border-radius:12px;background:#0f172a}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid rgba(38,54,79,.8);padding:9px;text-align:right;white-space:nowrap}th{position:sticky;top:0;background:#182238;color:#93c5fd;z-index:2}th:first-child,td:first-child{text-align:left}td.reason{white-space:normal;min-width:260px;text-align:left;line-height:1.5}.muted{color:var(--muted)}.up{color:#fca5a5}.down{color:#86efac}.warn{color:#fcd34d}@media(max-width:1100px){.cards{grid-template-columns:repeat(2,1fr)}.table-wrap{height:auto;min-height:520px}}
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
  </div>
  <section class="panel">
    <div class="panel-h"><span>&#23436;&#25972;&#20080;&#21334;&#26126;&#32454;</span><span id="note" class="muted">--</span></div>
    <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>#</th><th>&#20080;&#20837;&#26085;</th><th>&#21334;&#20986;&#26085;</th><th>&#20080;&#20837;&#20215;</th><th>&#21334;&#20986;&#20215;</th><th>&#32929;&#25968;</th><th>&#30408;&#20111;</th><th>&#25910;&#30410;&#29575;</th><th>&#20080;&#20837;&#20381;&#25454;</th><th>&#21334;&#20986;&#20381;&#25454;</th></tr></thead><tbody id="rows"><tr><td colspan="10" class="muted">&#21152;&#36733;&#20013;...</td></tr></tbody></table></div></div>
  </section>
</main>
<script>
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const money=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2}),pct=n=>(Number(n||0)).toFixed(2)+'%',cls=n=>Number(n)>=0?'up':'down';
function params(){const p=new URLSearchParams(location.search);if(!p.get('symbol'))p.set('symbol','300750');p.delete('autorun');return p}
function row(t,i){return `<tr><td>${i+1}</td><td>${esc(t.entry_date)}</td><td>${esc(t.exit_date)}</td><td>${esc(t.entry_price)}</td><td>${esc(t.exit_price)}</td><td>${esc(t.shares)}</td><td class="${cls(t.pnl)}">${money(t.pnl)}</td><td class="${cls(t.pnl_pct)}">${pct(t.pnl_pct)}</td><td class="reason">${esc(t.entry_reason)}<br><small class="muted">&#20449;&#21495;&#26085; ${esc(t.entry_signal_date||'--')} · &#35780;&#20998; ${esc(t.entry_signal_score??'--')}</small></td><td class="reason">${esc(t.exit_reason)}<br><small class="muted">&#20449;&#21495;&#26085; ${esc(t.exit_signal_date||'--')} · &#35780;&#20998; ${esc(t.exit_signal_score??'--')}</small></td></tr>`}
async function load(){try{const p=params();const r=await fetch('/api/backtest/run?'+p.toString(),{cache:'no-store'});const js=await r.json();if(!r.ok||!js.ok)throw new Error(js.message||('HTTP '+r.status));const d=js.data;$('sub').textContent=`${d.name} ${d.symbol} · ${d.strategy_name}`;$('mRet').textContent=pct(d.total_return_pct);$('mRet').className=cls(d.total_return_pct);$('mHold').textContent=pct(d.buy_hold_return_pct);$('mHold').className=cls(d.buy_hold_return_pct);$('mExcess').textContent=pct(d.excess_return_pct);$('mExcess').className=cls(d.excess_return_pct);$('mTrades').textContent=(d.trade_count||0)+'笔';$('mDd').textContent=pct(d.max_drawdown_pct);$('note').textContent=`${d.data_quality.start} 至 ${d.data_quality.end} · ${(d.markers||[]).length} 买卖点 · ${(d.anomaly_markers||[]).length} 异常点`;$('rows').innerHTML=(d.trades||[]).map(row).join('')||'<tr><td colspan="10" class="muted">&#26412;&#27425;&#21442;&#25968;&#19979;&#26080;&#38381;&#21512;&#20132;&#26131;</td></tr>'}catch(e){$('rows').innerHTML='<tr><td colspan="10" class="warn">&#21152;&#36733;&#22833;&#36133; '+esc(e)+'</td></tr>'}}
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
<header><span class="dot"></span><div class="brand">纸面交易系统 V3.19</div><span class="disclaimer">研究辅助，不构成投资建议；未接入真实券商</span><div class="grow"></div><button class="btn2" onclick="location.href='/backtest'">交易回测</button><button class="btn2" onclick="location.href='/screener'">筛选系统</button></header>
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
