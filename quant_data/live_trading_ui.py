from __future__ import annotations


def build_live_trading_ui() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>真实自动交易 V3.23</title>
<style>
:root{--bg:#07111f;--panel:#101a2c;--line:#263955;--text:#e6f0ff;--muted:#92a6c4;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--amber:#f59e0b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif}a{color:#cfe1ff;text-decoration:none}button,input,select,textarea{font:inherit}
header{height:60px;display:flex;align-items:center;gap:10px;padding:0 18px;background:#0b1424;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.dot{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.brand{font-weight:1000;font-size:20px;color:#bfdbfe}.pill{border:1px solid #315077;background:#13233b;border-radius:999px;padding:5px 10px;color:#cfe1ff;font-size:12px;font-weight:900}.danger{border-color:#7f1d1d;background:#2a1116;color:#fecaca}.grow{flex:1}
main{display:grid;grid-template-columns:360px minmax(0,1fr) 430px;gap:14px;padding:14px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.h{min-height:46px;padding:0 12px;background:#121e33;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:8px;font-weight:1000}.b{padding:12px}.stack{display:grid;gap:14px}.row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px}.card{background:#0d1728;border:1px solid #2f4364;border-radius:12px;padding:11px}.card span{display:block;color:var(--muted);font-size:12px}.card b{display:block;font-size:22px;margin-top:7px;overflow-wrap:anywhere}.muted{color:var(--muted)}.warn{color:#fcd34d}.bad{color:#fecaca}.ok{color:#86efac}
input,select,textarea{width:100%;background:#0d1728;color:#e5efff;border:1px solid #2f4364;border-radius:10px;padding:9px 10px;outline:none}textarea{min-height:92px;resize:vertical;line-height:1.45}.field{display:grid;gap:6px;margin-bottom:10px}.field label{font-size:12px;color:#9db4d4;font-weight:900}.btn,button{border:0;border-radius:10px;background:#253755;color:#e5efff;padding:9px 12px;font-weight:900;cursor:pointer}.btn.primary,button.primary{background:var(--blue);color:#fff}.btn.red,button.red{background:#991b1b;color:#fff}.btn.green,button.green{background:#16a34a;color:#fff}.notice{background:#0d1728;border:1px solid #2f4364;border-radius:12px;padding:10px;color:#c8d8ee;font-size:13px;line-height:1.6;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}th,td{border-bottom:1px solid #243653;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#12213a;color:#9fd4ff}.table-wrap{overflow:auto;border:1px solid #2f4364;border-radius:12px;max-height:360px}pre{white-space:pre-wrap;word-break:break-word;background:#0b1220;border:1px solid #2f4364;border-radius:12px;padding:10px;max-height:280px;overflow:auto;color:#b7c9e6}
.strategy-list{display:grid;gap:7px;max-height:250px;overflow:auto}.strategy-chip{display:grid;grid-template-columns:auto 1fr;gap:8px;border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:8px;cursor:pointer}.strategy-chip input{width:auto;margin-top:3px}.strategy-chip b{display:block}.strategy-chip span{display:block;color:var(--muted);font-size:11px;line-height:1.35;margin-top:2px}.strategy-chip.on{border-color:#22d3ee;background:#092536}
@media(max-width:1200px){main{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:720px){header{position:static}.grid,.cards{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><span class="dot"></span><div class="brand">真实自动交易 V3.23</div><span class="pill danger">默认禁用 · 必须人工确认</span><span class="pill">研究辅助，不构成投资建议</span><div class="grow"></div><a href="/auto-trading">总控台</a><a href="/realtime-paper">实时模拟</a><a href="/trading-records">交易记录</a><a href="/ui">行情</a></header>
<main>
  <section class="stack">
    <div class="panel">
      <div class="h"><span>多股票实盘观察池</span><button onclick="loadAutoConfig(true)">读取总控台</button></div>
      <div class="b">
        <div class="field"><label>监控标的（逗号/空格/换行分隔）</label><textarea id="symbols">300750, 600438, 510300</textarea></div>
        <div class="grid">
          <div class="field"><label>默认方向</label><select id="side"><option value="buy">买入预检查</option><option value="sell">卖出预检查</option></select></div>
          <div class="field"><label>默认数量</label><input id="quantity" type="number" value="100"></div>
          <div class="field"><label>限价（0=按预检查参考）</label><input id="limitPrice" type="number" value="0"></div>
          <div class="field"><label>订单类型</label><select id="orderType"><option value="limit">限价</option><option value="best_effort">最优五档/尽力</option><option value="target_percent">目标仓位</option><option value="target_value">目标金额</option></select></div>
        </div>
        <div class="row"><button class="primary" onclick="batchPreview()">批量预检查</button><button onclick="previewFirst()">预检查首只</button><button class="red" onclick="kill()">Kill Switch</button></div>
        <p class="notice">没有 QMT/PTrade SDK、账号授权、环境变量和人工确认时，所有真实下单都会被拒绝或进入确认队列，不会直接触达券商。</p>
        <div class="table-wrap" style="margin-top:10px;max-height:220px"><table><thead><tr><th>代码</th><th>策略数</th><th>方向</th><th>数量</th><th>参考限价</th><th>状态</th></tr></thead><tbody id="watchRows"><tr><td colspan="6">等待加载观察池</td></tr></tbody></table></div>
      </div>
    </div>
    <div class="panel">
      <div class="h"><span>实盘策略目录</span><span id="strategyHint" class="muted">加载中...</span></div>
      <div class="b">
        <div class="field"><label>策略组合（与回测/实时模拟共用）</label><textarea id="strategyCombo">score_driven, low_position, ma_repair, macd_cross, volume_breakout, atr_risk, risk_control, event_driven, finance_quality, market_regime</textarea></div>
        <div class="row" style="margin-bottom:10px"><button onclick="loadLiveIntradayPreset()">载入实盘分时策略</button><button onclick="selectAllAvailableStrategies()">使用全部可用策略</button><span class="pill" id="liveStrategyPreset">分时实盘预设会合并盘口、资金、宏观和风控策略</span></div>
        <div id="strategyList" class="strategy-list"></div>
      </div>
    </div>
    <div class="panel">
      <div class="h"><span>风控参数</span><span class="muted">实盘仍需确认</span></div>
      <div class="b grid">
        <div class="field"><label>止损%</label><input id="stopLossPct" type="number" value="8"></div>
        <div class="field"><label>止盈%</label><input id="takeProfitPct" type="number" value="18"></div>
        <div class="field"><label>单票上限%</label><input id="maxSinglePositionPct" type="number" value="20"></div>
        <div class="field"><label>最大回撤%</label><input id="maxDrawdownPct" type="number" value="18"></div>
      </div>
    </div>
  </section>
  <section class="stack">
    <div class="cards" id="cards"></div>
    <div class="panel">
      <div class="h"><span>账户与持仓</span><button onclick="load()">刷新</button></div>
      <div class="b"><div id="accountBox" class="notice">读取中...</div><div class="table-wrap" style="margin-top:10px"><table><thead><tr><th>代码</th><th>名称</th><th>数量</th><th>可用</th><th>成本</th><th>市价</th><th>市值</th><th>浮盈亏</th><th>盈亏%</th><th>来源</th></tr></thead><tbody id="positionsRows"><tr><td colspan="10">读取中...</td></tr></tbody></table></div></div>
    </div>
    <div class="panel">
      <div class="h"><span>预检查结果</span><span class="muted">不会真实下单</span></div>
      <div class="b"><div class="table-wrap"><table><thead><tr><th>代码</th><th>方向</th><th>数量</th><th>状态</th><th>原因/风控</th></tr></thead><tbody id="previewRows"><tr><td colspan="5">等待预检查</td></tr></tbody></table></div></div>
    </div>
    <div class="panel">
      <div class="h"><span>今日委托 / 成交 / 统一记录</span><button onclick="load()">刷新</button></div>
      <div class="b"><div class="table-wrap"><table><thead><tr><th>来源</th><th>代码</th><th>方向/状态</th><th>价格</th><th>数量</th><th>金额/盈亏</th><th>说明</th></tr></thead><tbody id="recordRows"><tr><td colspan="7">读取中...</td></tr></tbody></table></div></div>
    </div>
  </section>
  <section class="stack">
    <div class="panel">
      <div class="h"><span>券商与安全状态</span><button onclick="connect()">连接检查</button></div>
      <div class="b"><div id="safetyBox" class="notice">读取中...</div><pre id="out">Loading...</pre></div>
    </div>
    <div class="panel">
      <div class="h"><span>确认队列</span><button onclick="loadQueue()">刷新</button></div>
      <div class="b"><div class="table-wrap"><table><thead><tr><th>确认ID</th><th>代码</th><th>方向</th><th>状态</th><th>原因</th></tr></thead><tbody id="queueRows"><tr><td colspan="5">读取中...</td></tr></tbody></table></div></div>
    </div>
    <div class="panel">
      <div class="h"><span>审计输出</span><span class="muted">原始返回</span></div>
      <div class="b"><pre id="log">Ready.</pre></div>
    </div>
  </section>
</main>
<script>
const $=id=>document.getElementById(id);
let autoConfig=null;
const LIVE_INTRADAY_STRATEGIES=['score_driven','market_regime','main_money_est','fund_flow_watch','amount_active','vwap_reclaim','volume_breakout','orderbook_imbalance_watch','fake_order_cancel_watch','mfi_obv_resonance','rsi_kdj_resonance','macd_cross','macd_hist_turn','ma_repair','atr_risk','risk_control','avoid_chasing_high','news_sentiment','announcement_risk','global_commodity_map','sector_strength','source_reliability','event_driven'];
async function api(url,opt){const r=await fetch(url,opt);try{return await r.json()}catch(e){return {ok:false,status:r.status,message:String(e)}}}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function splitListText(v){return String(v||'').split(/[\s,，;；、]+/).map(s=>s.trim()).filter(Boolean)}
function symbols(){return splitListText($('symbols').value)}
function strategyCombo(){return splitListText($('strategyCombo').value)}
function num(id,fallback){const n=Number($(id).value);return Number.isFinite(n)?n:fallback}
function money(v){const n=Number(v);return Number.isFinite(n)?n.toLocaleString('zh-CN',{maximumFractionDigits:2}):'--'}
function pct(v){const n=Number(v);return Number.isFinite(n)?n.toFixed(2)+'%':'--'}
function cls(v){const n=Number(v);return n>0?'ok':n<0?'bad':''}
function strategyLabel(key){
  const map={};(autoConfig?.strategy_catalog||[]).forEach(x=>{if(x.key)map[x.key]=x.name||x.key});
  return map[key]||{score_driven:'日常评分驱动',low_position:'低位修复',avoid_chasing_high:'高位追高过滤',ma_repair:'均线修复',macd_cross:'MACD 金叉/多头',volume_breakout:'温和放量',atr_risk:'ATR 风险过滤',risk_control:'风险扣分',event_driven:'事件驱动',finance_quality:'财务质量',market_regime:'大盘情绪过滤'}[key]||key;
}
function renderStrategies(){
  const list=autoConfig?.strategy_catalog||[];
  const selected=new Set(strategyCombo());
  $('strategyHint').textContent=`已选 ${selected.size} 项 / 可用 ${list.length} 项`;
  $('liveStrategyPreset').textContent=`实盘当前 ${selected.size} 项；目录 ${list.length} 项，与回测/实时模拟共用`;
  $('strategyList').innerHTML=list.map(item=>{const key=String(item.key||'');const on=selected.has(key);return `<label class="strategy-chip ${on?'on':''}"><input type="checkbox" data-key="${esc(key)}" ${on?'checked':''} onchange="toggleStrategy(this)"><span><b>${esc(item.name||key)}</b><span>${esc(item.category||'策略')} · ${esc(item.beginner_note||item.description||'')}</span></span></label>`}).join('')||'<div class="notice">策略目录暂未返回，仍可手动输入策略 key。</div>';
  renderWatchRows();
}
function toggleStrategy(el){const set=new Set(strategyCombo());if(el.checked)set.add(el.dataset.key);else set.delete(el.dataset.key);$('strategyCombo').value=[...set].join(', ');renderStrategies()}
function loadLiveIntradayPreset(){const current=new Set(strategyCombo());LIVE_INTRADAY_STRATEGIES.forEach(x=>current.add(x));$('strategyCombo').value=[...current].join(', ');renderStrategies()}
function selectAllAvailableStrategies(){const list=(autoConfig?.strategy_catalog||[]).map(x=>String(x.key||'')).filter(Boolean);$('strategyCombo').value=list.join(', ');renderStrategies()}
function applyAutoConfig(cfg){
  if(!cfg)return;autoConfig=cfg;
  if((cfg.symbols||[]).length)$('symbols').value=cfg.symbols.join(', ');
  if((cfg.strategy_combo||[]).length){
    const merged=new Set(cfg.strategy_combo||[]);
    if(merged.size<8)LIVE_INTRADAY_STRATEGIES.forEach(x=>merged.add(x));
    $('strategyCombo').value=[...merged].join(', ');
  }
  const r=cfg.risk_controls||{};
  if(r.stop_loss_pct!=null)$('stopLossPct').value=r.stop_loss_pct;
  if(r.take_profit_pct!=null)$('takeProfitPct').value=r.take_profit_pct;
  if(r.max_single_position_pct!=null)$('maxSinglePositionPct').value=r.max_single_position_pct;
  if(r.max_drawdown_pct!=null)$('maxDrawdownPct').value=r.max_drawdown_pct;
  renderStrategies();
}
async function loadAutoConfig(apply=false){const js=await api('/api/auto-trading/config');autoConfig=js.data||{};if(apply)applyAutoConfig(autoConfig);else renderStrategies()}
function orderPayload(symbol){return {symbol,side:$('side').value,quantity:num('quantity',100),limit_price:num('limitPrice',0)||null,order_type:$('orderType').value,selected_strategies:strategyCombo(),strategy_combo:strategyCombo(),strategy_parameters:autoConfig?.strategy_parameters||{},risk_controls:{stop_loss_pct:num('stopLossPct',8),take_profit_pct:num('takeProfitPct',18),max_single_position_pct:num('maxSinglePositionPct',20),max_drawdown_pct:num('maxDrawdownPct',18)},event_watch:autoConfig?.event_watch||{},source_page:'live-trading'}}
async function previewSymbol(symbol){return await api('/api/live/orders/preview',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(orderPayload(symbol))})}
async function previewFirst(){const sym=symbols()[0]||'300750';const js=await previewSymbol(sym);$('log').textContent=JSON.stringify(js,null,2);renderPreviewRows([{symbol:sym,response:js}])}
async function batchPreview(){const syms=symbols();const rows=[];for(const sym of syms){rows.push({symbol:sym,response:await previewSymbol(sym)})}$('log').textContent=JSON.stringify(rows,null,2);renderPreviewRows(rows)}
function renderPreviewRows(rows){$('previewRows').innerHTML=rows.map(x=>{const r=x.response||{};const ok=r.ok||r.approved||r.status==='needs_confirmation';const risk=r.risk||r.data?.risk||{};return `<tr><td>${esc(x.symbol)}</td><td>${esc($('side').value)}</td><td>${esc($('quantity').value)}</td><td class="${ok?'ok':'bad'}">${esc(r.status||r.message||(ok?'通过/待确认':'未通过'))}</td><td>${esc(r.status_reason||risk.reason||r.reason||JSON.stringify(r).slice(0,180))}</td></tr>`}).join('')||'<tr><td colspan="5">暂无预检查结果</td></tr>';renderWatchRows(rows)}
function renderWatchRows(preview=[]){
  const previewMap={};(preview||[]).forEach(x=>previewMap[x.symbol]=x.response||{});
  const selected=strategyCombo();
  $('watchRows').innerHTML=symbols().map(sym=>{const r=previewMap[sym]||{};const ok=r.ok||r.approved||r.status==='needs_confirmation';const state=r.status||r.message||(Object.keys(r).length?(ok?'预检查通过/待确认':'预检查未通过'):'待预检查');return `<tr><td>${esc(sym)}</td><td>${selected.length}</td><td>${esc($('side').value)}</td><td>${esc($('quantity').value)}</td><td>${esc($('limitPrice').value||'0')}</td><td class="${Object.keys(r).length?(ok?'ok':'bad'):''}">${esc(state)}</td></tr>`}).join('')||'<tr><td colspan="6">请先输入监控标的</td></tr>';
}
async function connect(){const js=await api('/api/live-broker/connect',{method:'POST'});$('log').textContent=JSON.stringify(js,null,2);await load()}
async function kill(){const js=await api('/api/live/kill-switch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:true})});$('log').textContent=JSON.stringify(js,null,2);await load()}
function renderStatus(js){
  const s=js.safety||{},b=js.broker||{};
  $('cards').innerHTML=[['券商状态',b.status||js.status||'--'],['真实交易',s.LIVE_TRADING_ENABLED?'开启':'关闭'],['人工确认',s.ORDER_CONFIRM_REQUIRED?'必须':'关闭'],['Kill',s.LIVE_KILL_SWITCH?'开启':'关闭']].map(x=>`<div class="card"><span>${x[0]}</span><b>${esc(x[1])}</b></div>`).join('');
  $('safetyBox').innerHTML=`券商：${esc(b.broker||js.config?.broker_type||'disabled')} / ${esc(b.status||'disabled')}<br>SDK/环境变量/账号未配置时只能显示 disabled/unsupported；真实订单必须先进入预检查和确认队列。`;
  $('out').textContent=JSON.stringify(js,null,2);
}
function renderAccount(account){const d=account.data||{};$('accountBox').innerHTML=`可用资金 ${money(d.cash?.available_cash??d.available_cash??d.cash)}；总资产 ${money(d.total_assets??d.total_value??d.equity)}；数据源 ${esc(account.source?.status||d.source||'券商/模拟适配器')}`}
function renderPositions(js){
  const rows=Array.isArray(js.data)?js.data:[];
  $('positionsRows').innerHTML=rows.map(p=>{const qty=Number(p.quantity??p.volume??0);const qtyText=Number.isFinite(qty)?qty:(p.quantity??p.volume??0);const cost=Number(p.cost_price??p.avg_price);const last=Number(p.last_price??p.price);const mv=Number(p.market_value??p.amount??(Number.isFinite(qty)&&Number.isFinite(last)?qty*last:NaN));const pnl=Number(p.pnl??p.unrealized_pnl??(Number.isFinite(qty)&&Number.isFinite(cost)&&Number.isFinite(last)?(last-cost)*qty:NaN));const pnlPct=Number(p.pnl_pct??p.unrealized_pnl_pct??(Number.isFinite(cost)&&cost?((last-cost)/cost*100):NaN));return `<tr><td>${esc(p.symbol)}</td><td>${esc(p.name||'--')}</td><td>${esc(qtyText)}</td><td>${esc(p.available_quantity??p.available??'--')}</td><td>${esc(Number.isFinite(cost)?cost.toFixed(3):(p.cost_price??p.avg_price??'--'))}</td><td>${esc(Number.isFinite(last)?last.toFixed(3):(p.last_price??p.price??'--'))}</td><td>${money(mv)}</td><td class="${cls(pnl)}">${money(pnl)}</td><td class="${cls(pnlPct)}">${pct(pnlPct)}</td><td>${esc(p.source||js.source?.broker||js.source?.status||'券商接口')}</td></tr>`}).join('')||'<tr><td colspan="10">暂无持仓；若券商未连接则显示接口不支持/未授权。</td></tr>';
}
function normalizeRecordRows(orders,trades,records){
  const rows=[];
  const amt=x=>Number(x.amount??x.pnl??x.realized_pnl??((Number(x.price??x.limit_price)*Number(x.quantity))||NaN));
  (orders.data||[]).forEach(x=>rows.push({source:'委托',symbol:x.symbol,side:x.side||x.status,price:x.limit_price||x.price,qty:x.quantity,amount:amt(x),status:x.status||x.status_reason}));
  (trades.data||[]).forEach(x=>rows.push({source:'成交',symbol:x.symbol,side:x.side,price:x.price,qty:x.quantity,amount:amt(x)||x.fee,status:x.filled_at||x.source}));
  (records.data||[]).slice(0,30).forEach(x=>rows.push({source:x.table||'记录',symbol:x.symbol,side:x.side||x.status||x.event_type,price:x.price||x.limit_price,qty:x.quantity,amount:amt(x),status:x.status_reason||x.reason||x.event_type}));
  return rows.slice(0,80);
}
function renderRecords(rows){$('recordRows').innerHTML=rows.map(x=>`<tr><td>${esc(x.source)}</td><td>${esc(x.symbol||'--')}</td><td>${esc(x.side||'--')}</td><td>${esc(x.price??'--')}</td><td>${esc(x.qty??'--')}</td><td>${money(x.amount)}</td><td>${esc(x.status||'--')}</td></tr>`).join('')||'<tr><td colspan="7">暂无真实交易流水；默认关闭时只显示预检查和审计。</td></tr>'}
async function loadQueue(){const q=await api('/api/live/confirm-queue');$('queueRows').innerHTML=(q.data||[]).map(x=>`<tr><td>${esc(x.confirm_id||x.id)}</td><td>${esc(x.symbol||x.request?.symbol||'--')}</td><td>${esc(x.side||x.request?.side||'--')}</td><td>${esc(x.status||'--')}</td><td>${esc(x.reason||x.status_reason||'--')}</td></tr>`).join('')||'<tr><td colspan="5">暂无待确认订单</td></tr>';return q}
async function load(){
  const [status,account,positions,orders,trades,records,queue]=await Promise.all([api('/api/live-broker/status'),api('/api/live/account'),api('/api/live/positions'),api('/api/live/orders'),api('/api/live/trades'),api('/api/trading-records?mode=live&limit=80'),loadQueue()]);
  renderStatus(status);renderAccount(account);renderPositions(positions);renderRecords(normalizeRecordRows(orders,trades,records));
  $('log').textContent='最后刷新 '+new Date().toLocaleTimeString()+'\\n'+JSON.stringify({queue_count:queue.count,status:status.safety},null,2);
}
loadAutoConfig(true).then(load);
</script>
</body>
</html>"""
