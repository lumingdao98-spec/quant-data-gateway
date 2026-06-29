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
*{box-sizing:border-box}html,body{height:100%;margin:0}body{font-family:Segoe UI,Microsoft YaHei,Arial,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}.app{height:100vh;display:grid;grid-template-rows:56px 1fr 78px;grid-template-columns:330px 1fr 430px;grid-template-areas:"top top top" "side main right" "log log log"}.top{grid-area:top;background:#101827;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;padding:0 16px;overflow:hidden}.side{grid-area:side;background:#0f172a;border-right:1px solid var(--line);padding:14px;overflow:auto}.main{grid-area:main;padding:12px;overflow:auto}.right{grid-area:right;background:#0f172a;border-left:1px solid var(--line);padding:12px;overflow:auto}.log{grid-area:log;background:#0f172a;border-top:1px solid var(--line);padding:8px 12px;overflow:auto;font-family:Consolas,monospace;font-size:12px;color:#9fb4d4}.brand{font-weight:900;color:#bfdbfe;font-size:18px;white-space:nowrap}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green);flex:0 0 auto}.grow{flex:1;min-width:0}.pill{display:inline-flex;align-items:center;border:1px solid #30405d;background:#1f2a44;color:#bfdbfe;border-radius:999px;padding:5px 9px;font-size:12px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.panel,.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-h{min-height:44px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 12px;background:#141e32;border-bottom:1px solid var(--line);font-weight:900}.panel-b{padding:12px}.section{font-size:13px;color:#9fb4d4;margin:12px 0 7px}input,select,textarea{width:100%;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:10px;padding:9px 11px;outline:none}textarea{min-height:92px;resize:vertical;line-height:1.45}button{border:0;background:#2563eb;color:#fff;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer;white-space:nowrap}.btn2{background:#253149;color:#c7d2fe}.btn-green{background:#16a34a}.btn-red{background:#991b1b}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.cards{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:8px;margin-bottom:10px}.card{padding:10px;min-width:0}.card span{display:block;color:var(--muted);font-size:11px}.card b{display:block;text-align:right;font-size:19px;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#0f172a;max-height:330px}table{width:100%;border-collapse:collapse;font-size:13px;min-width:1060px}th,td{border-bottom:1px solid rgba(38,54,79,.8);padding:8px;text-align:right;white-space:nowrap;vertical-align:top}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2),th:nth-child(3),td:nth-child(3){text-align:left}td.reason,td.evidence{white-space:normal;min-width:220px;line-height:1.45;overflow-wrap:anywhere}th{position:sticky;top:0;background:#182238;color:#93c5fd}.muted{color:var(--muted)}.up{color:#fca5a5}.down{color:#86efac}.warn{color:#fcd34d}.hint{font-size:12px;line-height:1.55;color:#9fb4d4;background:#0d1428;border:1px solid #26364f;border-radius:12px;padding:10px;margin-top:10px;overflow-wrap:anywhere}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.symbol-tabs{display:flex;gap:6px;flex-wrap:wrap}.symbol-tabs button{padding:6px 9px;background:#1f2a44;color:#bfdbfe}.symbol-tabs button.active{background:#2563eb;color:#fff}.mini{font-size:11px;color:#91a7c7;line-height:1.4}.pos-row{display:grid;grid-template-columns:70px 1fr;gap:8px;border-bottom:1px solid rgba(38,54,79,.7);padding:7px 0}.pos-row b{color:#bfdbfe}.step-list{margin:0;padding-left:18px}.step-list li{margin:5px 0}@media(max-width:1180px){body{overflow:auto}.app{height:auto;min-height:100vh;grid-template-columns:1fr;grid-template-rows:56px auto auto auto 78px;grid-template-areas:"top" "side" "main" "right" "log"}.cards{grid-template-columns:repeat(2,1fr)}.table-wrap{max-height:420px}}
</style>
</head>
<body>
<div class="app">
  <header class="top"><span class="dot"></span><div class="brand">实时模拟交易</div><span class="pill">研究辅助，不构成投资建议 · paper_only · 不连接真实券商</span><div class="grow"></div><button class="btn2" onclick="location.href='/auto-trading'">自动交易总控台</button><button class="btn2" onclick="location.href='/backtest'">历史回测</button><button class="btn2" onclick="location.href='/screener'">筛选系统</button><button class="btn2" onclick="location.href='/ui'">行情监控</button></header>
  <aside class="side">
    <div class="section">监控标的，逗号或换行分隔</div><textarea id="symbols">300750,600438,510300</textarea>
    <div class="grid2">
      <div><div class="section">初始资金</div><input id="cash" type="number" value="100000"></div>
      <div><div class="section">自动频率</div><select id="interval"><option value="5">5秒</option><option value="15" selected>15秒</option><option value="30">30秒</option><option value="60">60秒</option></select></div>
      <div><div class="section">交易周期</div><select id="horizon"><option value="intraday_paper">盘中模拟</option><option value="short_term">短线</option><option value="swing">中线</option><option value="position">长线</option><option value="dca">定投</option><option value="hybrid">混合</option></select></div>
      <div><div class="section">手动价格兜底</div><input id="tickPrice" type="number" value="420"></div>
    </div>
    <div class="row" style="margin-top:12px"><button class="btn-green" onclick="startEngine()">启动自动模拟</button><button class="btn2" onclick="stopEngine()">停止</button><button onclick="runOneCycle('manual')">执行一轮模拟</button></div>
    <div class="hint">启动后页面会立即跑一轮，然后按频率循环。交易时段使用当前缓存/行情快照，休市时显示为纸面回放，不伪装真实盘中成交。多只股票会逐只生成信号，右上方标签可分别查看。</div>
  </aside>
  <main class="main">
    <div class="cards">
      <div class="card"><span>运行状态</span><b id="mStatus">--</b></div>
      <div class="card"><span>运行模式</span><b id="mMode">--</b></div>
      <div class="card"><span>下次循环</span><b id="mNext">--</b></div>
      <div class="card"><span>最近一轮</span><b id="mLast">--</b></div>
      <div class="card"><span>总权益</span><b id="mEquity">--</b></div>
      <div class="card"><span>现金/可用</span><b id="mCash">--</b></div>
      <div class="card"><span>持仓市值</span><b id="mMv">--</b></div>
      <div class="card"><span>总收益/回撤</span><b id="mRet">--</b></div>
    </div>
    <div class="panel">
      <div class="panel-h"><span>信号流</span><div class="row"><div id="symbolTabs" class="symbol-tabs"></div><button class="btn2" onclick="refreshAll()">刷新</button></div></div>
      <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>时间</th><th>名称</th><th>代码</th><th>动作</th><th>总分</th><th>基本/技术/信息/大盘</th><th>异常</th><th>目标仓位</th><th>模式</th><th>原因</th><th>依据</th></tr></thead><tbody id="signalRows"></tbody></table></div></div>
    </div>
    <div class="panel" style="margin-top:10px">
      <div class="panel-h"><span>订单流</span><span class="muted">拒单会显示风控原因；所有订单都是模拟订单</span></div>
      <div class="panel-b"><div class="table-wrap"><table><thead><tr><th>时间</th><th>代码</th><th>方向</th><th>状态</th><th>价格</th><th>股数</th><th>成交</th><th>原因</th></tr></thead><tbody id="orderRows"></tbody></table></div></div>
    </div>
  </main>
  <aside class="right">
    <div class="panel"><div class="panel-h"><span>模拟账户持仓</span><span id="symbolSummary" class="muted">--</span></div><div class="panel-b"><div id="positions" class="hint">--</div></div></div>
    <div class="panel" style="margin-top:10px"><div class="panel-h"><span>如何使用</span></div><div class="panel-b"><div class="hint"><ol class="step-list"><li>填入多只标的和初始资金。</li><li>点击“启动自动模拟”，页面会按频率循环抓取行情快照并生成纸面信号。</li><li>休市时只能做纸面回放观察，不能代表实时成交。</li><li>用“执行一轮模拟”手动跑一次，适合检查当前参数是否生效。</li></ol></div></div></div>
    <div class="panel" style="margin-top:10px"><div class="panel-h"><span>风控状态</span></div><div class="panel-b"><div id="riskBox" class="hint">--</div></div></div>
    <div class="panel" style="margin-top:10px"><div class="panel-h"><span>审计日志</span></div><div class="panel-b"><div id="auditBox" class="hint">--</div></div></div>
  </aside>
  <div class="log" id="log">Ready.</div>
</div>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const fmt=(v,d=2)=>v==null||Number.isNaN(Number(v))?'--':Number(v).toFixed(d);
const money=v=>Number(v||0).toLocaleString('zh-CN',{maximumFractionDigits:2});
const pct=v=>fmt(v,2)+'%';
const cls=v=>Number(v)>=0?'up':'down';
let selectedSymbol='all',lastSignals=[],loopTimer=null,countTimer=null,cycleBusy=false,nextAt=null,lastMode='--';
function log(s){$('log').textContent=new Date().toLocaleTimeString()+' '+s+'\n'+$('log').textContent}
async function api(url,opt={}){const r=await fetch(url,{cache:'no-store',...opt});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}
function symbols(){return [...new Set($('symbols').value.replace(/，/g,',').split(/[,\n\s]+/).map(x=>x.trim()).filter(Boolean))]}
function intervalSec(){return Math.max(5,Math.min(60,Number($('interval').value||15)))}
async function sessionInfo(){try{return (await api('/api/calendar/status?symbol='+(symbols()[0]||'300750'))).data||{}}catch(e){return {can_refresh:false,label:'交易日历读取失败'}}}
async function fetchQuotesForRun(){const syms=symbols();if(!syms.length)return[];try{const js=await api('/api/quotes?symbols='+encodeURIComponent(syms.join(','))+'&force=false&refresh=false');return js.data||[]}catch(e){log('行情快照失败，使用手动价格兜底：'+e);return syms.map(s=>({symbol:s,name:s,last:Number($('tickPrice').value||0),source:'manual_fallback'}))}
}
function scoreFromQuote(q,session){const chg=Number(q.change_pct||0),vr=Number(q.volume_ratio||1),turn=Number(q.turnover||0);return {technical_score:Math.max(20,Math.min(88,58+chg*3+Math.min(vr,3)*4)),information_score:55,fundamental_score:60,market_score:session.can_refresh?58:52,anomaly_features:{price_jump_pct:Math.abs(chg),volume_ratio:vr,turnover_rate:turn}}}
async function startEngine(){const payload={symbols:symbols(),initial_cash:Number($('cash').value||100000),interval_seconds:intervalSec(),horizon:$('horizon').value};const js=await api('/api/realtime-paper/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});renderStatus(js);renderSymbolTabs();startLoop();await runOneCycle('start');log('已启动自动模拟：每 '+intervalSec()+' 秒运行一轮')}
async function stopEngine(){clearLoop();const js=await api('/api/realtime-paper/stop',{method:'POST'});renderStatus(js);$('mNext').textContent='已停止';log('已停止自动模拟')}
function clearLoop(){if(loopTimer)clearInterval(loopTimer);if(countTimer)clearInterval(countTimer);loopTimer=null;countTimer=null;nextAt=null}
function startLoop(){clearLoop();const sec=intervalSec();nextAt=Date.now()+sec*1000;loopTimer=setInterval(()=>runOneCycle('auto'),sec*1000);countTimer=setInterval(updateCountdown,1000);updateCountdown()}
function updateCountdown(){if(!nextAt){$('mNext').textContent='--';return}const left=Math.max(0,Math.ceil((nextAt-Date.now())/1000));$('mNext').textContent=left+'秒';if(left===0)nextAt=Date.now()+intervalSec()*1000}
async function runOneCycle(source='manual'){if(cycleBusy){log('上一轮仍在运行，已跳过本次触发');return}cycleBusy=true;try{const session=await sessionInfo();const quotes=await fetchQuotesForRun();const manualReplay=!session.can_refresh;lastMode=manualReplay?'休市纸面回放':'盘中实时模拟';$('mMode').textContent=lastMode;let ok=0;for(const q of quotes){const price=Number(q.last||q.price||$('tickPrice').value||0);if(!price||Number.isNaN(price))continue;const scores=scoreFromQuote(q,session);const payload={symbol:q.symbol,name:q.name||q.symbol,price,last:price,quote:q,quote_ts:q.ts,now:new Date().toISOString(),horizon:$('horizon').value,is_trading_session:!!session.can_refresh,manual_replay:manualReplay,evidence:[manualReplay?'休市纸面回放：使用缓存/快照生成观察信号':'页面自动模拟：使用当前行情快照生成纸面信号'],...scores};await api('/api/realtime-paper/tick',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});ok++}await refreshAll();$('mLast').textContent=new Date().toLocaleTimeString();log((source==='manual'?'手动执行':'自动执行')+'一轮完成：'+ok+'/'+quotes.length+' 只 · '+lastMode)}catch(e){log('执行一轮失败：'+e)}finally{cycleBusy=false}}
function renderStatus(js){const st=js.state||js.data?.state||{};const p=js.portfolio||js.data||{};$('mStatus').textContent=st.status||'--';$('mMode').textContent=lastMode||((st.is_trading_session?'盘中实时模拟':'休市纸面回放'));$('mEquity').textContent=money(p.equity);$('mCash').textContent=money(p.cash)+' / '+money(p.available_cash);$('mRet').textContent=pct(p.total_return_pct)+' / '+pct((p.max_drawdown||0)*100);$('mRet').className=cls(p.total_return_pct);$('mMv').textContent=money(p.market_value);$('symbolSummary').textContent=(st.config?.symbols||symbols()).join(', ')||'--';$('riskBox').innerHTML=`状态 ${esc(st.status||'--')}；交易时段 ${st.is_trading_session?'是':'否'}；新鲜度 ${esc(st.freshness_status||'--')}<br>paper_only=true；real_broker_connected=false<br><span class="warn">休市自动模拟只做纸面回放，不代表真实盘中成交；真实券商接口默认禁用。</span>`}
function renderPortfolio(js){const p=js.data||js.portfolio||{};renderStatus({state:(window.lastState||{}),portfolio:p});const pos=p.positions||{};$('positions').innerHTML=Object.keys(pos).length?Object.values(pos).map(x=>`<div class="pos-row"><b>${esc(x.symbol)}</b><div>${esc(x.name||'')} ${x.quantity}股<br>成本 ${fmt(x.avg_cost)} · 现价 ${fmt(x.market_price)} · 市值 ${money(x.market_value)} · 浮盈 ${money(x.unrealized_pnl)}</div></div>`).join(''):'暂无持仓'}
function renderSymbolTabs(){const syms=['all',...new Set([...symbols(),...lastSignals.map(x=>x.symbol).filter(Boolean)])];$('symbolTabs').innerHTML=syms.map(s=>`<button class="${selectedSymbol===s?'active':''}" onclick="selectedSymbol='${s}';renderSignals({data:lastSignals});renderOrders(window.__lastOrders||{data:[]});renderSymbolTabs()">${s==='all'?'全部':esc(s)}</button>`).join('')}
function renderSignals(js){lastSignals=js.data||lastSignals||[];const rows=selectedSymbol==='all'?lastSignals:lastSignals.filter(x=>String(x.symbol)===String(selectedSymbol));$('signalRows').innerHTML=rows.map(x=>`<tr><td>${esc((x.timestamp||'').replace('T',' ').slice(11,19))}</td><td>${esc(x.name||'--')}</td><td>${esc(x.symbol)}</td><td>${esc(x.action)}</td><td>${fmt(x.final_score,1)}</td><td>${fmt(x.fundamental_score,1)} / ${fmt(x.technical_score,1)} / ${fmt(x.information_score,1)} / ${fmt(x.market_score,1)}</td><td>${fmt(x.anomaly_score,1)}</td><td>${pct((x.target_weight||0)*100)}</td><td>${esc(x.session_mode||'--')}</td><td class="reason">${esc(x.reason||'--')}</td><td class="evidence">${esc((x.evidence||[]).slice(0,3).join('；'))}</td></tr>`).join('')||'<tr><td colspan="11" class="muted">暂无信号；启动自动模拟或执行一轮后显示</td></tr>';renderSymbolTabs()}
function renderOrders(js){window.__lastOrders=js;const all=js.data||[];const rows=selectedSymbol==='all'?all:all.filter(x=>String(x.symbol)===String(selectedSymbol));$('orderRows').innerHTML=rows.map(x=>`<tr><td>${esc((x.created_at||'').replace('T',' ').slice(11,19))}</td><td>${esc(x.symbol)}</td><td>${esc(x.side)}</td><td>${esc(x.status)}</td><td>${fmt(x.price)}</td><td>${x.quantity??0}</td><td>${x.filled_quantity??0}</td><td class="reason">${esc(x.reason||'--')}</td></tr>`).join('')||'<tr><td colspan="8" class="muted">暂无订单；信号未触发或风控未放行时不会生成成交</td></tr>'}
function renderAudit(js){const rows=js.data||[];$('auditBox').innerHTML=rows.slice(0,14).map(x=>`<div>${esc((x.created_at||'').replace('T',' ').slice(11,19))} <b>${esc(x.event_type)}</b> ${esc(JSON.stringify(x.payload||{})).slice(0,180)}</div>`).join('')||'暂无审计'}
async function refreshAll(){const [st,p,s,o,a]=await Promise.all([api('/api/realtime-paper/status'),api('/api/realtime-paper/portfolio'),api('/api/realtime-paper/signals'),api('/api/realtime-paper/orders'),api('/api/realtime-paper/audit')]);window.lastState=st.state;renderStatus(st);renderPortfolio(p);renderSignals(s);renderOrders(o);renderAudit(a)}
refreshAll().catch(e=>log('初始化失败 '+e));
</script>
</body>
</html>'''
