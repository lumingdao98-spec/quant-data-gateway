from __future__ import annotations


def build_auto_trading_workbench_ui() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V3.23 自动交易总控台</title>
<style>
:root{--bg:#f4f7fb;--panel:#fff;--line:#e6ebf3;--text:#172033;--muted:#667085;--cyan:#19c6c0;--blue:#2f7cf6;--green:#18a761;--red:#ef4444;--amber:#f59e0b;--soft:#effdfa;--shadow:0 14px 34px rgba(25,38,71,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}button,input,select,textarea{font:inherit}a{color:inherit;text-decoration:none}
.app{display:grid;grid-template-columns:280px minmax(0,1fr);min-height:100vh}.side{background:#fff;border-right:1px solid var(--line);display:flex;flex-direction:column}.brand{height:78px;display:flex;align-items:center;gap:12px;padding:0 24px;border-bottom:1px solid var(--line);font-weight:900}.logo{width:42px;height:42px;border:2px solid #111827;border-radius:14px;display:grid;place-items:center}.nav{padding:14px 0}.nav a{display:flex;align-items:center;gap:12px;padding:14px 24px;color:#4c586d;font-weight:800}.nav a.active{background:#dcfbf8;color:#079d99;border-right:4px solid var(--cyan)}.side-foot{margin-top:auto;padding:20px 24px;color:#8a94a8;font-size:12px;line-height:1.8;border-top:1px solid var(--line)}
.top{height:76px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 26px;position:sticky;top:0;z-index:5}.top-left,.top-right,.row{display:flex;align-items:center;gap:12px}.top-right{color:#5c6678}.icon-btn{border:1px solid var(--line);background:#fff;border-radius:10px;width:40px;height:40px;display:grid;place-items:center;cursor:pointer}
.main{padding:28px 34px 42px}.title-row{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:20px}.title-row h1{font-size:24px;margin:0 0 5px}.title-row p{margin:0;color:var(--muted);line-height:1.6}.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #b8ece8;background:#ebfffc;color:#06968e;border-radius:999px;padding:7px 12px;font-weight:900;font-size:13px}.pill.warn{border-color:#ffe2a3;background:#fff7df;color:#ad6a00}.pill.danger{border-color:#fecaca;background:#fff1f2;color:#be123c}
.grid{display:grid;gap:18px}.kpis{grid-template-columns:repeat(5,minmax(150px,1fr));margin-bottom:22px}.card,.panel,.module{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:12px}.card{padding:18px}.card .label{color:#7a8498;font-size:13px}.card .value{font-size:26px;font-weight:900;margin-top:10px;overflow-wrap:anywhere}.card .sub{color:#7a8498;font-size:12px;margin-top:5px;line-height:1.5}
.layout{display:grid;grid-template-columns:330px minmax(520px,1fr) 380px;gap:18px;align-items:start}.panel{overflow:hidden}.panel h2{font-size:18px;margin:0;padding:15px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:10px}.panel-body{padding:16px 18px}.field{display:grid;gap:7px;margin-bottom:13px}.field label{font-size:13px;color:#667085;font-weight:800}.field input,.field select,.field textarea{border:1px solid var(--line);background:#f8fafc;border-radius:10px;padding:10px 12px;color:var(--text);min-width:0}.field textarea{min-height:82px;resize:vertical}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}.btn{border:0;border-radius:10px;padding:10px 14px;font-weight:900;color:#fff;background:var(--cyan);cursor:pointer}.btn.blue{background:var(--blue)}.btn.dark{background:#273247}.btn.red{background:var(--red)}.btn.ghost{background:#fff;color:#334155;border:1px solid var(--line)}.btn.small{padding:7px 10px;font-size:12px}.btn:disabled{opacity:.55;cursor:not-allowed}
.module-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.module{display:block;padding:13px;background:#fbfcff}.module b{display:block;margin-bottom:6px}.module span{display:block;color:#7a8498;font-size:12px;line-height:1.55;overflow-wrap:anywhere}.module:hover{border-color:var(--cyan);background:#f0fffd}.notice{background:#fff7df;border:1px solid #ffe2a3;color:#8a5a00;border-radius:10px;padding:12px;line-height:1.65;font-size:13px;overflow-wrap:anywhere}.ok{color:var(--green)}.bad{color:var(--red)}.muted{color:#7a8498}.log{max-height:250px;overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fbfcff;padding:10px;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;color:#334155;overflow-wrap:anywhere}.status-table{width:100%;border-collapse:collapse;table-layout:fixed}.status-table th,.status-table td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;font-size:13px;vertical-align:top;overflow-wrap:anywhere}.status-table th{color:#5c6678;background:#f8fafc}
.decision{padding:24px;border-top:5px solid var(--cyan)}.decision h3{font-size:34px;margin:0;color:#111827}.decision p{line-height:1.75;color:#4a5568;margin:16px 0}.score-bars{display:grid;gap:10px}.bar{height:9px;background:#edf1f7;border-radius:99px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue))}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);background:#fbfdff}.decision-grid div{padding:15px;text-align:center;border-right:1px solid var(--line)}.decision-grid div:last-child{border-right:0}.decision-grid b{display:block;font-size:20px;margin-top:7px;overflow-wrap:anywhere}
.mini-card{border:1px solid var(--line);border-radius:10px;padding:11px;background:#fbfcff;margin-bottom:10px}.mini-card b{display:block;margin-bottom:6px}.source-link{color:#079d99;text-decoration:underline}.footer-note{margin-top:18px;color:#7a8498;font-size:12px;line-height:1.7}
@media(max-width:1320px){.app{grid-template-columns:84px 1fr}.brand span,.nav span,.side-foot{display:none}.nav a{justify-content:center;padding:16px}.layout{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}@media(max-width:780px){.app{grid-template-columns:1fr}.side{display:none}.top{position:static}.main{padding:18px}.kpis,.split,.decision-grid,.module-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand"><div class="logo">Q</div><span>Quant Gateway<br><small>V3.23 Core</small></span></div>
    <nav class="nav">
      <a class="active" href="/auto-trading"><b>▦</b><span>自动交易总控台</span></a>
      <a href="/ui"><b>⌁</b><span>行情详情</span></a>
      <a href="/screener"><b>▤</b><span>股票筛选</span></a>
      <a href="/backtest"><b>↺</b><span>历史回测</span></a>
      <a href="/realtime-paper"><b>▶</b><span>实时模拟</span></a>
      <a href="/live-trading"><b>●</b><span>真实交易</span></a>
      <a href="/trading-records"><b>≡</b><span>交易记录</span></a>
      <a href="/data-center"><b>◆</b><span>数据中心</span></a>
    </nav>
    <div class="side-foot">研究辅助，不构成投资建议；真实交易默认关闭。启用真实券商前必须完成授权、风控、人工确认和合规自查。</div>
  </aside>
  <section>
    <header class="top">
      <div class="top-left"><button class="icon-btn" onclick="location.reload()">↻</button><b>V3.23 自动交易模块总控台</b><span class="pill" id="brokerBadge">读取券商状态...</span></div>
      <div class="top-right"><a href="/docs-cn">中文 API</a><a href="/ui">行情监控</a><a href="/screener">筛选系统</a></div>
    </header>
    <main class="main">
      <div class="title-row">
        <div><h1>V3.23 / Full Auto Trading Core</h1><p>回测、实时模拟、真实券商自动交易分离运行，共享统一评分、风控、订单、持仓、审计和图表标注内核。</p></div>
        <div class="row"><span class="pill warn">不伪造真实数据</span><button class="btn blue" onclick="refreshAll()">刷新状态</button></div>
      </div>

      <section class="grid kpis">
        <div class="card"><div class="label">实时模拟 session</div><div class="value" id="paperSessions">--</div><div class="sub" id="activeSessionText">可恢复、可暂停、可审计</div></div>
        <div class="card"><div class="label">统一交易记录</div><div class="value" id="recordCount">--</div><div class="sub">订单、成交、持仓、标注</div></div>
        <div class="card"><div class="label">数据中心</div><div class="value" id="dataHealth">--</div><div class="sub">缓存、缺失、过期、来源</div></div>
        <div class="card"><div class="label">真实交易</div><div class="value" id="liveEnabled">默认关闭</div><div class="sub">确认队列 + kill switch</div></div>
        <div class="card"><div class="label">确认队列</div><div class="value" id="confirmCount">--</div><div class="sub">人工批准后才提交券商</div></div>
      </section>

      <section class="layout">
        <div class="grid">
          <div class="panel">
            <h2>模块入口</h2>
            <div class="panel-body module-grid">
              <a class="module" href="/screener"><b>股票筛选</b><span>四面评分、策略适配、加入回测/模拟/实盘观察池。</span></a>
              <a class="module" href="/detail/300750"><b>详情决策</b><span>分时、K线、信息面、基本面、资金面和风控原因。</span></a>
              <a class="module" href="/backtest"><b>历史回测</b><span>订单、成交、买卖点、收益诊断和评分溯源。</span></a>
              <a class="module" href="/realtime-paper"><b>实时模拟</b><span>真实行情驱动的 paper trading session。</span></a>
              <a class="module" href="/live-trading"><b>真实交易</b><span>QMT/PTrade 状态、确认队列、kill switch。</span></a>
              <a class="module" href="/trading-records"><b>交易记录</b><span>回测、模拟、实盘统一流水和审计。</span></a>
              <a class="module" href="/data-center"><b>数据中心</b><span>缓存、缺失字段、数据源错误、后台任务。</span></a>
              <a class="module" href="/docs-cn"><b>中文 API</b><span>接口中文说明、参数和调试入口。</span></a>
            </div>
          </div>
          <div class="panel">
            <h2>实时模拟控制</h2>
            <div class="panel-body">
              <div class="field"><label>模拟股票池</label><textarea id="symbols">300750, 600438, 510300</textarea></div>
              <div class="split">
                <div class="field"><label>策略族</label><select id="strategy"><option value="hybrid">综合评分</option><option value="etf_momentum_rotation">ETF 动量轮动</option><option value="score_reversal">评分拐点修复</option><option value="core_satellite">核心-卫星</option></select></div>
                <div class="field"><label>刷新频率</label><select id="interval"><option value="15">15 秒</option><option value="30">30 秒</option><option value="60">60 秒</option><option value="0">仅手动执行一轮</option></select></div>
              </div>
              <div class="row"><button class="btn" onclick="startPaper()">启动模拟 session</button><button class="btn ghost" onclick="manualTick()">执行一轮模拟</button><button class="btn ghost" onclick="pausePaper()">暂停</button><button class="btn ghost" onclick="resumePaper()">恢复</button><button class="btn red" onclick="stopPaper()">停止</button><button class="btn red" onclick="killPaper()">模拟 Kill</button></div>
            </div>
          </div>
          <div class="panel">
            <h2>ETF 动量轮动结构 <a class="source-link" href="https://wu.run/posts/build-etf-momentum-rotation-system-from-scratch/" target="_blank">参考文章</a></h2>
            <div class="panel-body">
              <div class="mini-card"><b>ETF 池</b><span class="muted">维护可交易池，记录数据源、复权、滑点和可交易状态。</span></div>
              <div class="mini-card"><b>动量排序</b><span class="muted">结合绝对趋势、相对强弱、均线过滤和回撤约束。</span></div>
              <div class="mini-card"><b>实盘前模拟</b><span class="muted">先通过回测和实时模拟验证，再进入真实交易确认队列。</span></div>
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="panel">
            <h2>评分与交易假设</h2>
            <div class="decision">
              <div class="row" style="justify-content:space-between"><h3 id="decisionAction">WATCH</h3><span class="pill" id="decisionScore">评分 --</span></div>
              <p id="decisionText">系统会先检查真实数据新鲜度、评分溯源、策略适配、风控网关和订单预检查。真实交易必须进入确认队列或满足白名单确认策略。</p>
              <div class="score-bars">
                <div><div class="row" style="justify-content:space-between"><b>技术面</b><span id="techScore">--</span></div><div class="bar"><span id="techBar" style="width:0%"></span></div></div>
                <div><div class="row" style="justify-content:space-between"><b>基本面</b><span id="fundScore">--</span></div><div class="bar"><span id="fundBar" style="width:0%"></span></div></div>
                <div><div class="row" style="justify-content:space-between"><b>信息面</b><span id="infoScore">--</span></div><div class="bar"><span id="infoBar" style="width:0%"></span></div></div>
                <div><div class="row" style="justify-content:space-between"><b>大盘情绪</b><span id="marketScore">--</span></div><div class="bar"><span id="marketBar" style="width:0%"></span></div></div>
              </div>
            </div>
            <div class="decision-grid">
              <div><span>建议入场</span><b id="entryPrice">看信号</b></div>
              <div><span>止损</span><b class="bad" id="stopPrice">按策略</b></div>
              <div><span>止盈/跟踪</span><b class="ok" id="takePrice">跟踪</b></div>
              <div><span>风险动作</span><b id="riskAction">人工确认</b></div>
            </div>
          </div>
          <div class="panel">
            <h2>V3.23 会话详情 <span class="muted" id="sessionUpdated">--</span></h2>
            <div class="panel-body">
              <div class="split">
                <div class="mini-card"><b>账户快照</b><div id="sessionSnapshot" class="muted">暂无 active session</div></div>
                <div class="mini-card"><b>持仓</b><div id="sessionPositions" class="muted">暂无持仓</div></div>
              </div>
              <table class="status-table"><thead><tr><th>类型</th><th>数量</th><th>最近记录</th></tr></thead><tbody id="sessionRows"><tr><td colspan="3">等待 session...</td></tr></tbody></table>
            </div>
          </div>
          <div class="panel">
            <h2>统一交易记录预览 <a href="/trading-records">完整记录</a></h2>
            <div class="panel-body"><table class="status-table"><thead><tr><th>模式</th><th>类型</th><th>标的</th><th>状态/说明</th></tr></thead><tbody id="recordsBody"><tr><td colspan="4">加载中...</td></tr></tbody></table></div>
          </div>
        </div>

        <div class="grid">
          <div class="panel">
            <h2>真实券商 / QMT / PTrade 状态</h2>
            <div class="panel-body">
              <div class="notice">真实交易默认关闭。未配置 QMT/PTrade SDK、环境变量、账号授权时只显示 disabled/unsupported，不会真实下单。</div>
              <div class="split" style="margin-top:12px">
                <div class="field"><label>券商类型</label><input id="brokerType" readonly value="--"></div>
                <div class="field"><label>连接状态</label><input id="brokerStatus" readonly value="--"></div>
              </div>
              <div class="field"><label>QMT_PATH / PTRADE_PATH</label><input readonly placeholder="从环境变量读取，不在页面保存"></div>
              <div class="field"><label>账号/会话</label><input readonly placeholder="从环境变量读取，不提交 Git"></div>
              <div class="row"><button class="btn blue" onclick="connectLive()">连接检查</button><button class="btn red" onclick="killLive()">Live Kill Switch</button><a class="btn ghost" href="/live-trading">进入实盘页</a></div>
            </div>
          </div>
          <div class="panel">
            <h2>实盘订单预检查</h2>
            <div class="panel-body">
              <div class="split"><div class="field"><label>标的</label><input id="liveSymbol" value="300750"></div><div class="field"><label>方向</label><select id="liveSide"><option value="buy">买入</option><option value="sell">卖出</option></select></div></div>
              <div class="split"><div class="field"><label>股数</label><input id="liveQty" type="number" value="100"></div><div class="field"><label>限价</label><input id="livePrice" type="number" value="0"></div></div>
              <div class="row"><button class="btn" onclick="previewOrder()">预检查</button><button class="btn ghost" onclick="loadConfirmQueue()">确认队列</button></div>
              <div class="log" id="liveLog">等待操作...</div>
            </div>
          </div>
          <div class="panel">
            <h2>系统审计</h2>
            <div class="panel-body"><div class="log" id="auditLog">Ready.</div></div>
          </div>
        </div>
      </section>
      <div class="footer-note">数据缺失、缓存过期、休市无盘口、券商接口不支持、当前未授权都会明确展示；系统不会用随机数据冒充真实行情。研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。</div>
    </main>
  </section>
</div>
<script>
const $=id=>document.getElementById(id);
let activeSessionId='';
async function api(url,opt){const r=await fetch(url,opt);try{return await r.json()}catch(e){return {ok:false,message:String(e),status:r.status}}}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function symbols(){return $('symbols').value.split(/[，,;；\\s\\n]+/).map(s=>s.trim()).filter(Boolean)}
function pct(v){return Math.max(0,Math.min(100,Number(v||0)))}
function setScore(id,val){$(id+'Score').textContent=val==null?'--':Number(val).toFixed(1);$(id+'Bar').style.width=pct(val)+'%'}
function brief(row){return esc(row?.status||row?.event_type||row?.marker_type||row?.side||row?.order_id||row?.fill_id||row?.symbol||'--')}
function money(v){const n=Number(v);return Number.isFinite(n)?n.toLocaleString('zh-CN',{maximumFractionDigits:2}):'--'}
function sessionIdOf(item){return item?.session_id||item?.id||item?.sessionId||''}
function renderSessionRows(items){
  const rows=[
    ['订单',items.orders?.count??items.orders?.data?.length??0,(items.orders?.data||[])[0]],
    ['成交',items.fills?.count??items.fills?.data?.length??0,(items.fills?.data||[])[0]],
    ['图表 marker',items.markers?.count??items.markers?.data?.length??0,(items.markers?.data||[])[0]],
    ['审计',items.audit?.count??items.audit?.data?.length??0,(items.audit?.data||[])[0]]
  ];
  $('sessionRows').innerHTML=rows.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td>${brief(r[2])}</td></tr>`).join('');
}
async function loadSessionDetails(session){
  activeSessionId=sessionIdOf(session)||activeSessionId;
  if(!activeSessionId){$('sessionSnapshot').textContent='暂无 active session';$('sessionPositions').textContent='暂无持仓';renderSessionRows({});return}
  const base=`/api/realtime-paper/sessions/${encodeURIComponent(activeSessionId)}`;
  const [snapshot,orders,fills,positions,markers,audit]=await Promise.all([
    api(base),api(base+'/orders?limit=20'),api(base+'/fills?limit=20'),api(base+'/positions'),api(base+'/markers?limit=20'),api(base+'/audit?limit=20')
  ]);
  const sess=snapshot.data||session||{};
  $('activeSessionText').textContent=`${sess.status||'--'} · ${activeSessionId}`;
  $('sessionUpdated').textContent=new Date().toLocaleTimeString();
  const account=positions.data?.snapshot||{};
  $('sessionSnapshot').innerHTML=`现金 ${money(account.cash??account.available_cash)}<br>总资产 ${money(account.equity??account.total_value)}<br>回撤 ${esc(account.max_drawdown_pct??'--')}`;
  const posRows=positions.data?.positions||[];
  $('sessionPositions').innerHTML=posRows.length?posRows.slice(0,6).map(p=>`${esc(p.symbol)} ${esc(p.quantity??p.qty??0)}股 成本 ${esc(p.cost_price??p.avg_price??'--')}`).join('<br>'):'暂无持仓';
  renderSessionRows({orders,fills,markers,audit});
}
async function refreshAll(){
  try{
    const [broker,sessions,records,data,queue,score]=await Promise.all([
      api('/api/live-broker/status'),
      api('/api/realtime-paper/sessions'),
      api('/api/trading-records?limit=30'),
      api('/api/data-center/status'),
      api('/api/live/confirm-queue'),
      api('/api/score/latest/300750')
    ]);
    const brokerName=broker.broker?.broker||broker.config?.broker_type||'disabled';
    const brokerStatus=broker.broker?.status||broker.status||'disabled';
    $('brokerBadge').textContent=`${brokerName} / ${brokerStatus}`;
    $('brokerType').value=broker.config?.broker_type||brokerName;
    $('brokerStatus').value=brokerStatus;
    $('liveEnabled').textContent=broker.safety?.LIVE_TRADING_ENABLED?'已开启':'默认关闭';
    $('liveEnabled').className=broker.safety?.LIVE_TRADING_ENABLED?'value bad':'value';
    const sessList=sessions.data||[];
    const active=sessList.find(x=>['running','paused'].includes(x.status))||sessList[0]||null;
    $('paperSessions').textContent=sessList.length;
    $('confirmCount').textContent=queue.count??(queue.data||[]).length??0;
    const tableCount=Object.keys(data.trading_store?.tables||{}).length;
    $('dataHealth').textContent=tableCount?`${tableCount} 表`:'待检查';
    const rows=records.data||[];
    $('recordCount').textContent=rows.length;
    $('recordsBody').innerHTML=rows.slice(0,8).map(x=>`<tr><td>${esc(x.mode||'--')}</td><td>${esc(x.table||'--')}</td><td>${esc(x.symbol||'--')}</td><td>${brief(x)}</td></tr>`).join('')||'<tr><td colspan="4">暂无记录</td></tr>';
    const latest=score.data||{};
    const s=latest.final_score||latest.final_trade_score||0;
    $('decisionScore').textContent='评分 '+(s?Number(s).toFixed(1):'--');
    $('decisionAction').textContent=s>=70?'BUY / CONFIRM':s>=55?'WATCH':'AVOID';
    setScore('tech',latest.technical_score);
    setScore('fund',latest.fundamental_score);
    setScore('info',latest.information_score);
    setScore('market',latest.market_regime_score);
    $('entryPrice').textContent=latest.entry_price||'看信号';
    $('stopPrice').textContent=latest.stop_price||'按策略';
    $('takePrice').textContent=latest.take_profit||'跟踪';
    $('riskAction').textContent=broker.safety?.ORDER_CONFIRM_REQUIRED?'人工确认':'白名单确认';
    await loadSessionDetails(active);
    $('auditLog').textContent='最后刷新 '+new Date().toLocaleTimeString()+'\\n'+JSON.stringify({broker:broker.safety,active_session:activeSessionId,sessions:sessList.length,records:rows.length},null,2);
  }catch(e){$('auditLog').textContent='刷新失败：'+e}
}
async function startPaper(){
  const body={symbols:symbols(),strategy_family:$('strategy').value,interval_seconds:Number($('interval').value||15),initial_cash:100000,source_page:'auto-trading'};
  const js=await api('/api/realtime-paper/sessions/start',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  activeSessionId=sessionIdOf(js.session)||activeSessionId;
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function manualTick(){
  if(!activeSessionId){$('auditLog').textContent='请先启动或恢复一个实时模拟 session。';return}
  const sym=symbols()[0]||'300750';
  const js=await api('/api/realtime-paper/tick',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({session_id:activeSessionId,symbol:sym,technical_score:68,fundamental_score:60,information_score:58,market_score:55,manual_replay:true,source_page:'auto-trading'})});
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function pausePaper(){if(!activeSessionId)return;$('auditLog').textContent=JSON.stringify(await api(`/api/realtime-paper/sessions/${encodeURIComponent(activeSessionId)}/pause`,{method:'POST'}),null,2);refreshAll()}
async function resumePaper(){if(!activeSessionId)return;$('auditLog').textContent=JSON.stringify(await api(`/api/realtime-paper/sessions/${encodeURIComponent(activeSessionId)}/resume`,{method:'POST'}),null,2);refreshAll()}
async function stopPaper(){if(!activeSessionId)return;$('auditLog').textContent=JSON.stringify(await api(`/api/realtime-paper/sessions/${encodeURIComponent(activeSessionId)}/stop`,{method:'POST'}),null,2);refreshAll()}
async function killPaper(){if(!activeSessionId)return;$('auditLog').textContent=JSON.stringify(await api(`/api/realtime-paper/sessions/${encodeURIComponent(activeSessionId)}/kill-switch`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:true})}),null,2);refreshAll()}
async function connectLive(){const js=await api('/api/live-broker/connect',{method:'POST'});$('liveLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function killLive(){const js=await api('/api/live/kill-switch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:true})});$('liveLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function previewOrder(){
  const body={symbol:$('liveSymbol').value.trim(),side:$('liveSide').value,quantity:Number($('liveQty').value||0),limit_price:Number($('livePrice').value||0),order_type:'limit',source_page:'auto-trading'};
  const js=await api('/api/live/orders/preview',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  $('liveLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function loadConfirmQueue(){const js=await api('/api/live/confirm-queue');$('liveLog').textContent=JSON.stringify(js,null,2)}
refreshAll();
</script>
</body>
</html>"""
