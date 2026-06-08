from __future__ import annotations


def build_auto_trading_workbench_ui() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V3.23 自动交易总控台</title>
<style>
:root{--bg:#f5f7fb;--panel:#fff;--line:#e6eaf2;--text:#172033;--muted:#6b7487;--cyan:#17c9c3;--blue:#2f7cf6;--green:#18a761;--red:#ef4444;--amber:#f59e0b;--soft:#eefdfa;--shadow:0 10px 28px rgba(25,38,71,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}button,input,select,textarea{font:inherit}a{color:inherit;text-decoration:none}
.app{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid var(--line);display:flex;flex-direction:column}.brand{height:76px;display:flex;align-items:center;gap:12px;padding:0 26px;border-bottom:1px solid var(--line);font-weight:900}.logo{width:40px;height:40px;border:2px solid #111827;border-radius:12px;display:grid;place-items:center}.nav{padding:14px 0}.nav a{display:flex;align-items:center;gap:12px;padding:15px 26px;color:#4c586d;font-weight:700}.nav a.active{background:#dcfbf8;color:#079d99;border-right:4px solid var(--cyan)}.side-foot{margin-top:auto;padding:20px 26px;color:#8a94a8;font-size:12px;line-height:1.8;border-top:1px solid var(--line)}
.top{height:76px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 26px;position:sticky;top:0;z-index:5}.top-left{display:flex;align-items:center;gap:16px}.icon-btn{border:1px solid var(--line);background:#fff;border-radius:10px;width:40px;height:40px;display:grid;place-items:center;cursor:pointer}.top-right{display:flex;align-items:center;gap:14px;color:#5c6678}
.main{padding:28px 34px 44px}.title-row{display:flex;align-items:end;justify-content:space-between;margin-bottom:20px}.title-row h1{font-size:24px;margin:0 0 4px}.title-row p{margin:0;color:var(--muted)}.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #b8ece8;background:#ebfffc;color:#06968e;border-radius:999px;padding:7px 12px;font-weight:800;font-size:13px}.warn{border-color:#ffe2a3;background:#fff7df;color:#ad6a00}.grid{display:grid;gap:18px}.kpis{grid-template-columns:repeat(5,minmax(170px,1fr));margin-bottom:22px}.card,.panel,.tile{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:12px}.card{padding:18px}.card .label{color:#7a8498;font-size:13px}.card .value{font-size:28px;font-weight:900;margin-top:10px}.card .sub{color:#7a8498;font-size:12px;margin-top:4px}.up{color:var(--green)}.down{color:var(--red)}.layout{display:grid;grid-template-columns:330px minmax(520px,1fr) 360px;gap:18px;align-items:start}.panel{overflow:hidden}.panel h2{font-size:18px;margin:0;padding:16px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}.panel-body{padding:16px 18px}.tabs{display:flex;gap:8px;flex-wrap:wrap}.tab{border:1px solid var(--line);background:#f7f9fc;border-radius:10px;padding:9px 12px;font-weight:800;color:#566175}.tab.active{background:#e7fffc;color:#079d99;border-color:#9ee8e2}.btn{border:0;border-radius:10px;padding:11px 14px;font-weight:900;color:#fff;background:var(--cyan);cursor:pointer}.btn.blue{background:var(--blue)}.btn.dark{background:#273247}.btn.red{background:var(--red)}.btn.ghost{background:#fff;color:#334155;border:1px solid var(--line)}.btn:disabled{opacity:.55;cursor:not-allowed}.field{display:grid;gap:7px;margin-bottom:13px}.field label{font-size:13px;color:#667085;font-weight:700}.field input,.field select,.field textarea{border:1px solid var(--line);background:#f8fafc;border-radius:10px;padding:11px 12px;color:var(--text);min-width:0}.field textarea{min-height:82px;resize:vertical}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}.watch-row{display:grid;grid-template-columns:1fr auto;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}.watch-row:last-child{border-bottom:0}.spark{width:86px;height:30px}.mini{font-size:12px;color:#8a94a8}.metric{display:grid;grid-template-columns:1fr auto;gap:8px;border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:10px}.metric b{font-size:20px}.analysis-card{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}.decision{padding:28px;border-top:5px solid var(--cyan)}.decision h3{font-size:34px;margin:0;color:#111827}.decision p{line-height:1.75;color:#4a5568;margin:18px 0}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);background:#fbfdff}.decision-grid div{padding:16px;text-align:center;border-right:1px solid var(--line)}.decision-grid div:last-child{border-right:0}.decision-grid b{display:block;font-size:22px;margin-top:7px}.score-bars{display:grid;gap:10px;margin-top:14px}.bar{height:9px;background:#edf1f7;border-radius:99px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue))}.timeline{display:grid;gap:10px}.event{border-left:4px solid var(--cyan);padding:10px 12px;background:#f9fbff;border-radius:8px}.status-table{width:100%;border-collapse:collapse}.status-table th,.status-table td{border-bottom:1px solid var(--line);padding:10px;text-align:left;font-size:13px;vertical-align:top}.status-table th{color:#5c6678;background:#f8fafc}.log{max-height:260px;overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fbfcff;padding:10px;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;color:#334155}.route-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.route-grid a{padding:12px;border:1px solid var(--line);border-radius:10px;background:#fbfcff;font-weight:800;text-align:center}.route-grid a:hover{border-color:var(--cyan);background:#f0fffd}.notice{background:#fff7df;border:1px solid #ffe2a3;color:#8a5a00;border-radius:10px;padding:12px;line-height:1.6;font-size:13px}.source-link{color:#079d99;text-decoration:underline}.footer-note{margin-top:18px;color:#7a8498;font-size:12px}
@media(max-width:1300px){.app{grid-template-columns:86px 1fr}.brand span,.nav span,.side-foot{display:none}.nav a{justify-content:center;padding:16px}.layout{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}@media(max-width:760px){.top{position:static}.main{padding:18px}.kpis,.split,.decision-grid,.route-grid{grid-template-columns:1fr}.app{grid-template-columns:1fr}.side{display:none}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand"><div class="logo">Q</div><span>Quant Gateway<br><small>V3.23 Core</small></span></div>
    <nav class="nav">
      <a class="active" href="/auto-trading"><b>▦</b><span>AI资产分析</span></a>
      <a href="/screener"><b>▤</b><span>股票筛选</span></a>
      <a href="/backtest"><b>⌁</b><span>历史回测</span></a>
      <a href="/realtime-paper"><b>▶</b><span>实时模拟</span></a>
      <a href="/live-trading"><b>⎋</b><span>真实交易</span></a>
      <a href="/trading-records"><b>≣</b><span>交易记录</span></a>
      <a href="/data-center"><b>◎</b><span>数据中心</span></a>
    </nav>
    <div class="side-foot">研究辅助，不构成投资建议。真实交易默认关闭，启用前需用户自行确认合规与风险。</div>
  </aside>
  <section>
    <header class="top">
      <div class="top-left"><button class="icon-btn" onclick="location.reload()">↻</button><b>自动交易模块总控台</b><span class="pill" id="brokerBadge">读取券商状态...</span></div>
      <div class="top-right"><span>Admin</span><span>🔔</span><span>⚙</span></div>
    </header>
    <main class="main">
      <div class="title-row">
        <div><h1>V3.23 / Full Auto Trading Core</h1><p>回测、实时模拟、真实券商自动交易分离运行，共享统一评分、风控、订单、持仓、审计与图表标注内核。</p></div>
        <div class="row"><span class="pill warn" id="truthBadge">不造假数据</span><button class="btn blue" onclick="refreshAll()">刷新</button></div>
      </div>

      <section class="grid kpis">
        <div class="card"><div class="label">实时模拟会话</div><div class="value" id="paperSessions">--</div><div class="sub">可恢复 / 可暂停 / 可审计</div></div>
        <div class="card"><div class="label">交易记录</div><div class="value" id="recordCount">--</div><div class="sub">订单、成交、持仓、标注</div></div>
        <div class="card"><div class="label">数据中心</div><div class="value" id="dataHealth">--</div><div class="sub">缓存、缺失、过期、来源</div></div>
        <div class="card"><div class="label">真实交易</div><div class="value" id="liveEnabled">默认关闭</div><div class="sub">确认队列 + kill switch</div></div>
        <div class="card"><div class="label">确认队列</div><div class="value" id="confirmCount">--</div><div class="sub">人工批准后才实盘提交</div></div>
      </section>

      <section class="layout">
        <div class="grid">
          <div class="panel">
            <h2>交易池与频率</h2>
            <div class="panel-body">
              <div class="field"><label>监控标的</label><textarea id="symbols">300750, 600438, 510300</textarea></div>
              <div class="split">
                <div class="field"><label>策略族</label><select id="strategy"><option value="hybrid">综合评分</option><option value="etf_momentum_rotation">ETF动量轮动</option><option value="score_reversal">评分拐点修复</option><option value="core_satellite">核心-卫星</option></select></div>
                <div class="field"><label>模拟频率</label><select id="interval"><option value="15">15秒</option><option value="30">30秒</option><option value="60">60秒</option><option value="0">仅手动tick</option></select></div>
              </div>
              <div class="row"><button class="btn" onclick="startPaper()">启动模拟</button><button class="btn ghost" onclick="manualTick()">手动tick</button><button class="btn red" onclick="stopPaper()">停止</button></div>
            </div>
          </div>
          <div class="panel">
            <h2>ETF动量轮动模板 <a class="source-link" href="https://wu.run/posts/build-etf-momentum-rotation-system-from-scratch/" target="_blank">参考</a></h2>
            <div class="panel-body timeline">
              <div class="event"><b>排序</b><div class="mini">按动量、绝对趋势、均线过滤、相关性过滤生成候选。</div></div>
              <div class="event"><b>仓位</b><div class="mini">支持波动率目标、回撤降仓、冷却期和追踪止损。</div></div>
              <div class="event"><b>执行</b><div class="mini">交易日判断、状态持久化、通知和实盘前模拟验证。</div></div>
            </div>
          </div>
          <div class="panel">
            <h2>快捷入口</h2>
            <div class="panel-body route-grid">
              <a href="/screener">筛选</a><a href="/detail/300750">详情</a><a href="/backtest">回测</a><a href="/realtime-paper">模拟</a><a href="/live-trading">实盘</a><a href="/trading-records">记录</a><a href="/data-center">数据</a><a href="/docs-cn">中文API</a>
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="analysis-card">
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
              <div><span>建议入场</span><b id="entryPrice">--</b></div>
              <div><span>止损</span><b class="down" id="stopPrice">--</b></div>
              <div><span>止盈/跟踪</span><b class="up" id="takePrice">--</b></div>
              <div><span>风险动作</span><b id="riskAction">人工确认</b></div>
            </div>
          </div>
          <div class="panel">
            <h2>统一交易记录预览 <a href="/trading-records">完整记录</a></h2>
            <div class="panel-body"><table class="status-table"><thead><tr><th>模式</th><th>类型</th><th>标的</th><th>状态/说明</th></tr></thead><tbody id="recordsBody"><tr><td colspan="4">加载中...</td></tr></tbody></table></div>
          </div>
        </div>

        <div class="grid">
          <div class="panel">
            <h2>真实券商 / QMT 接口</h2>
            <div class="panel-body">
              <div class="notice">真实交易默认关闭。需要在本机配置券商终端、账号授权和环境变量；未授权或 SDK 缺失时只显示 disabled/unsupported，不会伪造连接。</div>
              <div class="split" style="margin-top:12px">
                <div class="field"><label>券商类型</label><input id="brokerType" readonly value="--"></div>
                <div class="field"><label>连接状态</label><input id="brokerStatus" readonly value="--"></div>
              </div>
              <div class="field"><label>QMT_PATH</label><input readonly placeholder="从环境变量读取，不在页面保存"></div>
              <div class="field"><label>QMT_ACCOUNT_ID / SESSION</label><input readonly placeholder="从环境变量读取，不提交 Git"></div>
              <div class="row"><button class="btn blue" onclick="connectLive()">连接检查</button><button class="btn red" onclick="killLive()">Kill Switch</button><a class="btn ghost" href="/live-trading">进入实盘页</a></div>
            </div>
          </div>
          <div class="panel">
            <h2>订单预检查</h2>
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
      <div class="footer-note">数据缺失、缓存过期、休市无盘口、券商接口不支持、未授权都会明确展示；系统不会用随机数据冒充真实行情。</div>
    </main>
  </section>
</div>
<script>
const $=id=>document.getElementById(id);
async function api(url,opt){const r=await fetch(url,opt);return await r.json()}
function symbols(){return $('symbols').value.split(/[，,;；\\n]+/).map(s=>s.trim()).filter(Boolean)}
function pct(v){return Math.max(0,Math.min(100,Number(v||0)))}
function setScore(id,val){$(id+'Score').textContent=val==null?'--':Number(val).toFixed(1);$(id+'Bar').style.width=pct(val)+'%'}
async function refreshAll(){
  try{
    const [broker,sessions,records,data,queue,score]=await Promise.all([
      api('/api/live-broker/status'),api('/api/realtime-paper/sessions'),api('/api/trading-records?limit=30'),api('/api/data-center/status'),api('/api/live/confirm-queue'),api('/api/score/latest/300750')
    ]);
    $('brokerBadge').textContent=(broker.broker?.broker||broker.config?.broker_type||'disabled')+' / '+(broker.broker?.status||'disabled');
    $('brokerType').value=broker.config?.broker_type||'disabled';$('brokerStatus').value=broker.broker?.status||'disabled';
    $('liveEnabled').textContent=broker.safety?.LIVE_TRADING_ENABLED?'已开启':'默认关闭';
    $('paperSessions').textContent=(sessions.data||[]).length; $('confirmCount').textContent=queue.count??0;
    const rows=records.data||[]; $('recordCount').textContent=rows.length; $('dataHealth').textContent=Object.keys(data.trading_store?.tables||{}).length+'表';
    $('recordsBody').innerHTML=rows.slice(0,8).map(x=>`<tr><td>${x.mode||'--'}</td><td>${x.table||'--'}</td><td>${x.symbol||'--'}</td><td>${x.status||x.event_type||x.marker_type||x.id||'--'}</td></tr>`).join('')||'<tr><td colspan="4">暂无记录</td></tr>';
    const latest=score.data||{}; const s=latest.final_score||latest.final_trade_score||0;
    $('decisionScore').textContent='评分 '+(s?Number(s).toFixed(1):'--'); $('decisionAction').textContent=s>=70?'BUY / CONFIRM':s>=55?'WATCH':'AVOID';
    setScore('tech',latest.technical_score); setScore('fund',latest.fundamental_score); setScore('info',latest.information_score); setScore('market',latest.market_regime_score);
    $('entryPrice').textContent=latest.entry_price||'看信号'; $('stopPrice').textContent=latest.stop_price||'按策略'; $('takePrice').textContent=latest.take_profit||'跟踪'; $('riskAction').textContent=broker.safety?.ORDER_CONFIRM_REQUIRED?'人工确认':'白名单确认';
    $('auditLog').textContent='最后刷新 '+new Date().toLocaleTimeString()+'\\n'+JSON.stringify({broker:broker.safety,sessions:sessions.data?.length,records:rows.length},null,2);
  }catch(e){$('auditLog').textContent='刷新失败：'+e}
}
async function startPaper(){const body={symbols:symbols(),strategy_family:$('strategy').value,interval_seconds:Number($('interval').value||15),initial_cash:100000};const js=await api('/api/realtime-paper/start',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});$('auditLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function manualTick(){const sym=symbols()[0]||'300750';const js=await api('/api/realtime-paper/tick',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbol:sym,price:Number($('livePrice').value||0),technical_score:68,fundamental_score:60,information_score:58,market_score:55,manual_replay:true})});$('auditLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function stopPaper(){const js=await api('/api/realtime-paper/stop',{method:'POST'});$('auditLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function connectLive(){const js=await api('/api/live-broker/connect',{method:'POST'});$('liveLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function killLive(){const js=await api('/api/live/kill-switch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:true})});$('liveLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function previewOrder(){const body={symbol:$('liveSymbol').value.trim(),side:$('liveSide').value,quantity:Number($('liveQty').value||0),limit_price:Number($('livePrice').value||0),order_type:'limit',source_page:'auto-trading'};const js=await api('/api/live/orders/preview',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});$('liveLog').textContent=JSON.stringify(js,null,2);refreshAll()}
async function loadConfirmQueue(){const js=await api('/api/live/confirm-queue');$('liveLog').textContent=JSON.stringify(js,null,2)}
refreshAll();
</script>
</body>
</html>"""
