from __future__ import annotations


def build_realtime_paper_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>实时模拟交易 · Quant Data Gateway</title>
<style>
:root{--bg:#0b1020;--panel:#101827;--panel2:#172033;--line:#283956;--text:#dbeafe;--muted:#91a7c7;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b}
*{box-sizing:border-box}html,body{height:100%;margin:0}body{font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}.app{height:100vh;display:grid;grid-template-rows:56px 1fr 78px;grid-template-columns:330px 1fr 430px;grid-template-areas:"top top top" "side main right" "log log log"}.top{grid-area:top;background:#101827;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;padding:0 16px}.side{grid-area:side;background:#0f172a;border-right:1px solid var(--line);padding:14px;overflow:auto}.main{grid-area:main;padding:12px;overflow:auto}.right{grid-area:right;background:#0f172a;border-left:1px solid var(--line);padding:12px;overflow:auto}.log{grid-area:log;background:#0f172a;border-top:1px solid var(--line);padding:8px 12px;overflow:auto;font-family:Consolas,monospace;font-size:12px;color:#9fb4d4}.brand{font-weight:900;color:#bfdbfe;font-size:18px}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.grow{flex:1}.pill{display:inline-flex;align-items:center;border:1px solid #30405d;background:#1f2a44;color:#bfdbfe;border-radius:999px;padding:5px 9px;font-size:12px}.panel,.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-h{min-height:44px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;background:#141e32;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.section{font-size:13px;color:#9fb4d4;margin:12px 0 7px}input,select,textarea{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px 11px;outline:none}textarea{min-height:92px;resize:vertical}button{border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer;white-space:nowrap}.btn2{background:#253149;color:#c7d2fe}.btn-green{background:#16a34a}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.cards{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:8px;margin-bottom:10px}.card{padding:10px}.card span{display:block;color:var(--muted);font-size:11px}.card b{display:block;text-align:right;font-size:20px;margin-top:4px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#0f172a;max-height:330px}table{width:100%;border-collapse:collapse;font-size:13px;min-width:780px}th,td{border-bottom:1px solid rgba(38,54,79,.8);padding:8px;text-align:right;white-space:nowrap;vertical-align:top}th:first-child,td:first-child{text-align:left}th{position:sticky;top:0;background:#182238;color:#93c5fd}.muted{color:var(--muted)}.up{color:#fca5a5}.down{color:#86efac}.warn{color:#fcd34d}.hint{font-size:12px;line-height:1.55;color:#9fb4d4;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px;margin-top:10px}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}@media(max-width:1180px){body{overflow:auto}.app{height:auto;min-height:100vh;grid-template-columns:1fr;grid-template-rows:56px auto auto auto 78px;grid-template-areas:"top" "side" "main" "right" "log"}.cards{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div class="app">
  <header class="top"><span class="dot"></span><div class="brand">实时模拟交易</div><span class="pill">研究辅助，不构成投资建议 · paper only</span><div class="grow"></div><button class="btn2" onclick="location.href='/backtest'">历史回测</button><button class="btn2" onclick="location.href='/screener'">筛选系统</button><button class="btn2" onclick="location.href='/ui'">行情监控</button></header>
  <aside class="side">
    <div class="section">监控标的</div><textarea id="symbols">300750,600438,510300</textarea>
    <div class="grid2">
      <div><div class="section">初始资金</div><input id="cash" type="number" value="100000"></div>
      <div><div class="section">频率</div><select id="interval"><option value="5">5秒</option><option value="15" selected>15秒</option><option value="30">30秒</option><option value="60">60秒</option></select></div>
      <div><div class="section">周期</div><select id="horizon"><option value="intraday_paper">盘中模拟</option><option value="short_term">短线</option><option value="swing">中线</option><option value="position">长线</option><option value="dca">定投</option><option value="hybrid">混合</option></select></div>
      <div><div class="section">手动价格</div><input id="tickPrice" type="number" value="420"></div>
    </div>
    <div class="row" style="margin-top:12px"><button class="btn-green" onclick="startEngine()">启动模拟</button><button class="btn2" onclick="stopEngine()">停止</button><button onclick="manualTick()">手动tick</button></div>
    <div class="hint">实时模拟会经过数据新鲜度、异常波动、三面评分和 RiskGateway，再进入模拟订单，不连接真实券商。</div>
  </aside>
  <main class="main">
    <div class="cards">
      <div class="card"><span>运行状态</span><b id="mStatus">--</b></div>
      <div class="card"><span>总权益</span><b id="mEquity">--</b></div>
      <div class="card"><span>现金/可用</span><b id="mCash">--</b></div>
      <div class="card"><span>总收益</span><b id="mRet">--</b></div>
      <div class="card"><span>持仓市值</span><b id="mMv">--</b></div>
      <div class="card"><span>当日盈亏</span><b id="mDay">--</b></div>
      <div class="card"><span>最大回撤</span><b id="mDd">--</b></div>
      <div class="card"><span>交易次数</span><b id="mTrades">--</b></div>
    </div>
    <div class="panel">
      <div class="panel-h"><span>信号流</span><button class="btn2" onclick="refreshAll()">刷新</button></div>
      <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>时间</th><th>标的</th><th>动作</th><th>总分</th><th>基本/技术/信息/大盘</th><th>异常</th><th>目标仓位</th><th>原因</th></tr></thead><tbody id="signalRows"></tbody></table></div></div>
    </div>
    <div class="panel" style="margin-top:10px">
      <div class="panel-h"><span>订单流</span><span class="muted">拒单会显示风控原因</span></div>
      <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>时间</th><th>标的</th><th>方向</th><th>状态</th><th>价格</th><th>股数</th><th>成交</th><th>原因</th></tr></thead><tbody id="orderRows"></tbody></table></div></div>
    </div>
  </main>
  <aside class="right">
    <div class="panel"><div class="panel-h"><span>模拟账户持仓</span></div><div class="panel-b"><div id="positions" class="hint">--</div></div></div>
    <div class="panel" style="margin-top:10px"><div class="panel-h"><span>风控状态</span></div><div class="panel-b"><div id="riskBox" class="hint">--</div></div></div>
    <div class="panel" style="margin-top:10px"><div class="panel-h"><span>审计日志</span></div><div class="panel-b"><div id="auditBox" class="hint">--</div></div></div>
  </aside>
  <div class="log" id="log">Ready.</div>
</div>
<script>
const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));const fmt=(v,d=2)=>v==null||Number.isNaN(Number(v))?'--':Number(v).toFixed(d);const money=v=>Number(v||0).toLocaleString('zh-CN',{maximumFractionDigits:2});const pct=v=>fmt(v,2)+'%';const cls=v=>Number(v)>=0?'up':'down';function log(s){$('log').textContent=new Date().toLocaleTimeString()+' '+s+'\n'+$('log').textContent}
async function api(url,opt={}){const r=await fetch(url,{cache:'no-store',...opt});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}
function symbols(){return $('symbols').value.replace(/，/g,',').split(/[,\n\s]+/).map(x=>x.trim()).filter(Boolean)}
async function startEngine(){const js=await api('/api/realtime-paper/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbols:symbols(),initial_cash:Number($('cash').value||100000),interval_seconds:Number($('interval').value||15),horizon:$('horizon').value})});renderStatus(js);log('已启动实时模拟')}
async function stopEngine(){const js=await api('/api/realtime-paper/stop',{method:'POST'});renderStatus(js);log('已停止')}
async function manualTick(){const s=symbols()[0]||'300750',price=Number($('tickPrice').value||0);const js=await api('/api/realtime-paper/tick',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:s,price,last:price,technical_score:68,information_score:58,fundamental_score:60,market_score:55,evidence:['手动tick'],is_trading_session:true})});log('tick '+s+' '+(js.signal?.action||'--'));await refreshAll()}
function renderStatus(js){const st=js.state||js.data?.state||{};const p=js.portfolio||js.data||{};$('mStatus').textContent=st.status||'--';$('mEquity').textContent=money(p.equity);$('mCash').textContent=money(p.cash)+' / '+money(p.available_cash);$('mRet').textContent=pct(p.total_return_pct);$('mRet').className=cls(p.total_return_pct);$('mMv').textContent=money(p.market_value);$('mDay').textContent=money(p.daily_pnl);$('mDd').textContent=pct((p.max_drawdown||0)*100);$('mTrades').textContent=p.trade_count_today??'--';$('riskBox').innerHTML=`状态 ${esc(st.status||'--')}；交易时段 ${st.is_trading_session?'是':'否'}；新鲜度 ${esc(st.freshness_status||'--')}<br>paper_only=true，real_broker_connected=false`}
function renderPortfolio(js){const p=js.data||js.portfolio||{};renderStatus({state:(window.lastState||{}),portfolio:p});const pos=p.positions||{};$('positions').innerHTML=Object.keys(pos).length?Object.values(pos).map(x=>`<div><b>${esc(x.symbol)}</b> ${x.quantity}股 · 成本 ${fmt(x.avg_cost)} · 现价 ${fmt(x.market_price)} · 市值 ${money(x.market_value)} · 浮盈 ${money(x.unrealized_pnl)}</div>`).join(''):'暂无持仓'}
function renderSignals(js){const rows=js.data||[];$('signalRows').innerHTML=rows.map(x=>`<tr><td>${esc((x.timestamp||'').slice(11,19))}</td><td>${esc(x.symbol)}</td><td>${esc(x.action)}</td><td>${fmt(x.final_score,1)}</td><td>${fmt(x.fundamental_score,1)} / ${fmt(x.technical_score,1)} / ${fmt(x.information_score,1)} / ${fmt(x.market_score,1)}</td><td>${fmt(x.anomaly_score,1)}</td><td>${pct((x.target_weight||0)*100)}</td><td>${esc(x.reason||'--')}</td></tr>`).join('')||'<tr><td colspan="8" class="muted">暂无信号</td></tr>'}
function renderOrders(js){const rows=js.data||[];$('orderRows').innerHTML=rows.map(x=>`<tr><td>${esc((x.created_at||'').slice(11,19))}</td><td>${esc(x.symbol)}</td><td>${esc(x.side)}</td><td>${esc(x.status)}</td><td>${fmt(x.price)}</td><td>${x.quantity??0}</td><td>${x.filled_quantity??0}</td><td>${esc(x.reason||'--')}</td></tr>`).join('')||'<tr><td colspan="8" class="muted">暂无订单</td></tr>'}
function renderAudit(js){const rows=js.data||[];$('auditBox').innerHTML=rows.slice(0,12).map(x=>`<div>${esc((x.created_at||'').slice(11,19))} <b>${esc(x.event_type)}</b> ${esc(JSON.stringify(x.payload||{})).slice(0,160)}</div>`).join('')||'暂无审计'}
async function refreshAll(){const [st,p,s,o,a]=await Promise.all([api('/api/realtime-paper/status'),api('/api/realtime-paper/portfolio'),api('/api/realtime-paper/signals'),api('/api/realtime-paper/orders'),api('/api/realtime-paper/audit')]);window.lastState=st.state;renderStatus(st);renderPortfolio(p);renderSignals(s);renderOrders(o);renderAudit(a)}
refreshAll().catch(e=>log('初始化失败 '+e));
</script>
</body>
</html>'''
