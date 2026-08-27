from __future__ import annotations


def build_data_center_ui() -> str:
    return r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>数据中心 V3.28</title>
  <style>
    :root{color-scheme:dark;--bg:#08111f;--panel:#101b2e;--panel2:#0c1728;--line:#263a58;--text:#e5efff;--muted:#8ea7ca;--blue:#60a5fa;--green:#4ade80;--amber:#fbbf24;--red:#f87171}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:14px}button,input,select{font:inherit}
    header{height:64px;display:flex;align-items:center;gap:14px;padding:0 20px;background:#0d1829;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}.brand{font-size:20px;font-weight:900}.brand small{display:block;color:var(--muted);font-size:12px;margin-top:2px}.grow{flex:1}.nav{display:flex;gap:8px;flex-wrap:wrap}.nav a{color:var(--text);text-decoration:none;background:#17243a;border:1px solid #263a58;border-radius:7px;padding:8px 10px;font-weight:700}
    main{max-width:1760px;margin:auto;padding:16px;display:grid;gap:14px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;min-width:0;overflow:hidden}.panel-head{padding:12px 14px;background:#142138;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;font-weight:900}.panel-body{padding:14px}.toolbar{display:grid;grid-template-columns:minmax(260px,1.5fr) repeat(2,minmax(150px,.7fr));gap:10px}.field label{display:block;color:var(--muted);font-size:12px;margin-bottom:5px}.field input,.field select{width:100%;height:40px;color:var(--text);background:#0a1424;border:1px solid #31496c;border-radius:7px;padding:0 10px}.scope-list{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.scope-list label{display:flex;align-items:center;gap:6px;padding:7px 9px;border:1px solid #2d4568;border-radius:7px;background:#0c1728}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.btn{border:1px solid #31517f;border-radius:7px;background:#1b2c48;color:var(--text);padding:9px 13px;font-weight:800;cursor:pointer}.btn.primary{background:#2563eb;border-color:#3b82f6}.btn.green{background:#15803d;border-color:#22c55e}.btn:disabled{opacity:.55;cursor:wait}
    .summary{display:grid;grid-template-columns:repeat(5,minmax(130px,1fr));gap:10px}.metric{background:var(--panel2);border:1px solid #263a58;border-radius:8px;padding:11px}.metric span{display:block;color:var(--muted);font-size:12px}.metric b{display:block;font-size:22px;margin-top:5px;overflow-wrap:anywhere}.ok{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}.muted{color:var(--muted)}
    .grid-two{display:grid;grid-template-columns:minmax(0,2fr) minmax(300px,.8fr);gap:14px}.table-wrap{overflow:auto;max-height:540px;border:1px solid #263a58;border-radius:7px}table{width:100%;border-collapse:collapse;min-width:1050px}th,td{padding:9px 10px;text-align:left;border-bottom:1px solid #223451;vertical-align:top}th{position:sticky;top:0;background:#142138;color:#9dc4ff;z-index:2}.pill{display:inline-flex;padding:3px 7px;border-radius:999px;border:1px solid #35547d;font-size:12px}.pill.ok{border-color:#166534}.pill.warn{border-color:#854d0e}.pill.bad{border-color:#7f1d1d}.reason{max-width:360px;line-height:1.45;overflow-wrap:anywhere}.score{font-size:17px;font-weight:900}.mini-btn{border:1px solid #33537c;background:#162742;color:#dbeafe;border-radius:6px;padding:5px 8px;cursor:pointer;white-space:nowrap}
    .list{display:grid;gap:8px;max-height:540px;overflow:auto}.item{background:#0c1728;border:1px solid #263a58;border-radius:7px;padding:9px;line-height:1.5;overflow-wrap:anywhere}.item strong{display:block}.source-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.source-row{display:grid;grid-template-columns:minmax(120px,1fr) auto;gap:8px;border-bottom:1px solid #223451;padding:8px 0}.source-row:last-child{border-bottom:0}.source-row small{grid-column:1/-1;color:var(--muted);overflow-wrap:anywhere}
    .db-path{max-width:420px;overflow-wrap:anywhere;color:#a9c7ef;font-size:12px}.db-tables{max-width:420px;overflow-wrap:anywhere;color:var(--muted);font-size:12px}.db-actions{display:flex;gap:6px;flex-wrap:wrap}.db-state{font-weight:900}
    details{border:1px solid #263a58;border-radius:7px;background:#0b1525}summary{cursor:pointer;padding:10px;font-weight:800}pre{margin:0;padding:12px;max-height:340px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;color:#a9c7ef}.notice{border:1px solid #31517f;background:#0b1b31;border-radius:7px;padding:10px;line-height:1.55;color:#bad5fa}.toast{position:fixed;right:18px;bottom:18px;z-index:30;max-width:min(480px,calc(100vw - 36px));padding:11px 14px;background:#17243a;border:1px solid #44658f;border-radius:7px;box-shadow:0 12px 32px #0008;display:none}.toast.show{display:block}.toast.bad{color:#fecaca;border-color:#7f1d1d}
    @media(max-width:1050px){.grid-two{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,minmax(0,1fr))}.toolbar{grid-template-columns:1fr}.source-grid{grid-template-columns:1fr}}
    @media(max-width:680px){header{height:auto;padding:10px;align-items:flex-start}.nav{display:none}.summary{grid-template-columns:1fr 1fr}main{padding:8px}.panel-body{padding:10px}}
  </style>
</head>
<body>
<header>
  <div class="brand">数据中心 V3.28<small>真实缓存、评分可用性与来源诊断</small></div><div class="grow"></div>
  <nav class="nav"><a href="/auto-trading">总控台</a><a href="/screener">股票筛选</a><a href="/ui">行情详情</a><a href="/backtest">历史回测</a><a href="/realtime-paper">实时模拟</a><a href="/broker-setup">券商配置</a><a href="/live-trading">真实交易</a></nav>
</header>
<main>
  <section class="panel">
    <div class="panel-head">诊断范围 <span class="muted">读取诊断不联网；只有显式刷新会访问外部数据源</span></div>
    <div class="panel-body">
      <div class="toolbar">
        <div class="field"><label>股票代码（逗号分隔，最多 20 只）</label><input id="symbols" value="300750,600438,159915"></div>
        <div class="field"><label>决策模式</label><select id="mode"><option value="realtime_paper">实时模拟</option><option value="backtest">历史回测</option><option value="live">真实交易预检</option></select></div>
        <div class="field"><label>策略族</label><select id="strategy"><option value="swing">波段</option><option value="short">短线</option><option value="position">长线持仓</option><option value="core_satellite">核心-卫星</option><option value="dca">定投</option><option value="event_driven">事件驱动</option></select></div>
      </div>
      <div class="scope-list" id="scopes">
        <label><input type="checkbox" value="quote" checked>实时行情</label><label><input type="checkbox" value="kline" checked>K线</label><label><input type="checkbox" value="fundamentals" checked>基本面</label><label><input type="checkbox" value="information" checked>信息面</label><label><input type="checkbox" value="capital" checked>资金面</label><label><input type="checkbox" value="global_market" checked>大盘/全球市场</label>
      </div>
      <div class="actions"><button class="btn primary" onclick="diagnose(this)">读取缓存诊断</button><button class="btn green" onclick="refreshSelected(this,false)">刷新勾选数据</button><button class="btn" onclick="refreshSelected(this,true)">强制重新抓取</button></div>
      <div class="notice" style="margin-top:12px">基本面 0 分不会自动补齐；ETF 的基本面会标为“不适用”。过期信息、缺少披露日期的财务数据和无来源的资金数据不能触发自动买入。真实交易仍需券商连接、风险通过和人工确认。</div>
    </div>
  </section>

  <section class="summary">
    <div class="metric"><span>诊断股票</span><b id="symbolCount">--</b></div><div class="metric"><span>可用维度</span><b id="readyCount" class="ok">--</b></div><div class="metric"><span>缺失/阻断维度</span><b id="missingCount" class="warn">--</b></div><div class="metric"><span>可新增仓位</span><b id="eligibleCount">--</b></div><div class="metric"><span>最近诊断</span><b id="generatedAt" style="font-size:14px">--</b></div>
  </section>

  <div class="grid-two">
    <section class="panel"><div class="panel-head">决策维度可用性 <span class="muted">分数、来源和阻断原因逐项显示</span></div><div class="panel-body"><div class="table-wrap"><table><thead><tr><th>标的</th><th>维度</th><th>得分</th><th>状态</th><th>来源</th><th>作用/缺失原因</th><th>操作</th></tr></thead><tbody id="readinessRows"><tr><td colspan="7" class="muted">正在读取本地缓存...</td></tr></tbody></table></div></div></section>
    <section class="panel"><div class="panel-head">交易阻断与缺失项</div><div class="panel-body"><div class="list" id="reasons"><div class="item muted">暂无诊断</div></div></div></section>
  </div>

  <section class="panel"><div class="panel-head">信息来源健康度 <span class="muted">只显示最近一次真实抓取结果，不把搜索结果页作为证据</span></div><div class="panel-body"><div class="source-grid"><div><b>个股/公告来源</b><div id="stockSources" class="list" style="margin-top:8px;max-height:320px"></div></div><div><b>全球/宏观来源</b><div id="globalSources" class="list" style="margin-top:8px;max-height:320px"></div></div></div><div id="sourcePolicy" class="notice" style="margin-top:10px"></div></div></section>

  <section class="panel"><div class="panel-head">SQLite 数据库管理 <span class="muted">白名单只读统计 + WAL 检查点，不提供任意 SQL 或删除</span><div class="grow"></div><button class="mini-btn" onclick="loadDatabases(this)">重新检查</button></div><div class="panel-body"><div id="databasePolicy" class="notice">正在读取数据库位置与完整性...</div><div class="table-wrap" style="margin-top:10px;max-height:520px"><table><thead><tr><th>数据库/用途</th><th>存储位置</th><th>大小</th><th>WAL</th><th>完整性</th><th>表与记录</th><th>维护</th></tr></thead><tbody id="databaseRows"><tr><td colspan="7" class="muted">正在读取...</td></tr></tbody></table></div></div></section>

  <section class="panel"><div class="panel-head">底层诊断</div><div class="panel-body" style="display:grid;gap:8px"><details><summary>缓存与数据库状态</summary><pre id="rawStatus">--</pre></details><details><summary>来源错误与熔断状态</summary><pre id="rawErrors">--</pre></details><details><summary>缺失字段原始记录</summary><pre id="rawMissing">--</pre></details></div></section>
</main>
<div id="toast" class="toast"></div>
<script>
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={fundamental:'基本面',technical:'技术面',information:'信息面',fund_flow:'资金面',market:'大盘情绪',quote:'实时行情',kline:'K线',fundamentals:'基本面',capital:'资金面',global_market:'大盘/全球市场',available:'可用',partial:'部分可用',missing:'缺失',stale:'已过期',not_applicable:'不适用',unusable:'不可交易',insufficient_sample:'样本不足'};
const scopeFor={fundamental:'fundamentals',technical:'kline',information:'information',fund_flow:'capital',market:'global_market'};
function toast(message,bad=false){const el=$('toast');el.textContent=message;el.className='toast show'+(bad?' bad':'');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>el.className='toast',4500)}
let pageUnloading=false;
window.addEventListener('beforeunload',()=>{pageUnloading=true});
function requestCancelled(error){return pageUnloading||error?.name==='AbortError'||error?.cancelled===true}
async function api(url,options={}){
  const requestOptions={cache:'no-store',credentials:'same-origin',...options};
  const timeoutMs=Number(requestOptions.timeoutMs||30000);delete requestOptions.timeoutMs;
  const controller=requestOptions.signal?null:new AbortController();
  if(controller)requestOptions.signal=controller.signal;
  const timer=controller?setTimeout(()=>controller.abort(),timeoutMs):null;
  let response;
  try{response=await fetch(new URL(url,location.origin),requestOptions)}catch(error){
    if(requestCancelled(error)){const cancelled=new Error('请求已取消');cancelled.cancelled=true;throw cancelled}
    throw new Error(`接口 ${url} 无法连接，请确认当前总控台服务仍在运行`)
  }finally{if(timer)clearTimeout(timer)}
  let data={};try{data=await response.json()}catch(_){throw new Error(`接口 ${url} 未返回有效 JSON`)}
  if(!response.ok||data.ok===false)throw new Error(data.detail||data.message||`接口 ${url} 请求失败（HTTP ${response.status}）`);
  return data
}
function selectedScopes(){return [...document.querySelectorAll('#scopes input:checked')].map(x=>x.value)}
function query(){return new URLSearchParams({symbols:$('symbols').value.trim(),mode:$('mode').value,strategy_family:$('strategy').value}).toString()}
async function busy(button,label,task){const old=button.textContent;button.disabled=true;button.textContent=label;try{return await task()}finally{button.disabled=false;button.textContent=old}}
function stateClass(row){if(row.ready)return 'ok';const q=String(row.quality_status||'').toLowerCase();return q==='not_applicable'?'warn':'bad'}
function stateText(row){if(row.ready)return '可用于决策';const q=String(row.quality_status||'missing');return labels[q]||q||'缺失'}
function renderReadiness(payload){const rows=payload.data||[];let ready=0,missing=0,eligible=0;const html=[];const reasons=[];
  for(const item of rows){ready+=Number(item.ready_count||0);missing+=Number(item.missing_count||0);eligible+=item.dimension_gate_eligible?1:0;for(const reason of [...(item.entry_block_reasons||[]),...(item.warnings||[])])reasons.push({symbol:item.symbol,text:reason});
    for(const dim of item.dimensions||[]){const key=dim.key||'unknown',score=Number.isFinite(Number(dim.score))?Number(dim.score):null,why=[dim.role,dim.usage,dim.reason,...(dim.missing_reasons||[])].filter(Boolean).join('；');
      html.push(`<tr><td><b>${esc(item.name||item.symbol)}</b><br><small class="muted">${esc(item.symbol)}</small></td><td>${esc(dim.label||labels[key]||key)}</td><td><span class="score">${score===null?'--':score.toFixed(1)}</span></td><td><span class="pill ${stateClass(dim)}">${esc(stateText(dim))}</span></td><td class="reason">${esc(dim.source||'数据源缺失')}<br><small class="muted">${esc(labels[dim.quality_status]||dim.quality_status||'')}</small></td><td class="reason">${esc(why||dim.truth_boundary||'无附加说明')}</td><td><button class="mini-btn" onclick="refreshOne('${esc(item.symbol)}','${esc(scopeFor[key]||'quote')}',this)">刷新此项</button></td></tr>`)}
  }
  $('readinessRows').innerHTML=html.join('')||'<tr><td colspan="7" class="muted">没有可诊断的股票</td></tr>';$('symbolCount').textContent=rows.length;$('readyCount').textContent=ready;$('missingCount').textContent=missing;$('eligibleCount').textContent=eligible+'/'+rows.length;$('generatedAt').textContent=payload.generated_at||new Date().toLocaleString();
  $('reasons').innerHTML=reasons.length?reasons.map(x=>`<div class="item"><strong>${esc(x.symbol)}</strong>${esc(x.text)}</div>`).join(''):'<div class="item ok">当前缓存没有额外阻断说明；仍须通过下单前风险网关。</div>'}
function renderSources(sourcePayload){const data=sourcePayload.data||{},health=data.news_sources||{};const render=(id,rows)=>{$(id).innerHTML=(rows||[]).map(row=>`<div class="item"><strong>${esc(row.source_name||row.source||row.name||'未知来源')} <span class="pill ${Number(row.count||0)>0?'ok':'warn'}">${esc(row.quality_status||row.status||'未检查')}</span></strong><small class="muted">有效条目 ${esc(row.count||0)}${row.error?' · '+esc(row.error):''}${row.skipped_reason?' · '+esc(row.skipped_reason):''}</small></div>`).join('')||'<div class="item muted">本进程尚未执行过该类抓取；请显式刷新信息面后再查看。</div>'};render('stockSources',health.stock_sources);render('globalSources',health.global_sources);const circuits=health.active_circuits||[];$('sourcePolicy').textContent=(health.truth_boundary||'未提供信息源诊断')+(circuits.length?' 当前短时熔断：'+circuits.map(x=>x.source).join('、'):'')}
function bytes(value){let n=Number(value||0);for(const unit of ['B','KB','MB','GB']){if(n<1024||unit==='GB')return `${n.toFixed(unit==='B'?0:1)} ${unit}`;n/=1024}return '--'}
function renderDatabases(payload){$('databasePolicy').textContent=`${payload.policy||''} 共 ${payload.existing_count||0}/${payload.database_count||0} 个数据库，合计 ${bytes(payload.total_size_bytes)}，WAL ${bytes(payload.total_wal_bytes)}。`;$('databaseRows').innerHTML=(payload.data||[]).map(row=>{const tables=(row.tables||[]).map(x=>`${x.name} ${x.rows===null?'?':x.rows}`).join('；');const state=row.quick_check==='ok'?'ok':row.exists?'warn':'bad';return `<tr><td><b>${esc(row.label||row.key)}</b><br><small class="muted">${esc(row.purpose||'')}</small></td><td class="db-path">${esc(row.path||'')}</td><td>${bytes(row.size_bytes)}<br><small class="muted">${esc(row.modified_at||'尚未创建')}</small></td><td>${bytes(row.wal_size_bytes)}<br><small class="muted">共享内存 ${bytes(row.shm_size_bytes)}</small></td><td><span class="db-state ${state}">${esc(row.quick_check||'未检查')}</span>${row.error?`<br><small class="bad">${esc(row.error)}</small>`:''}</td><td class="db-tables">${row.table_count||0} 张表 / ${row.total_rows||0} 条<br>${esc(tables||'无表')}</td><td><div class="db-actions"><button class="mini-btn" onclick="checkpointDb('${esc(row.key)}',false,this)" ${row.exists?'':'disabled'}>安全检查点</button><button class="mini-btn" onclick="checkpointDb('${esc(row.key)}',true,this)" ${row.exists?'':'disabled'}>截断空闲 WAL</button></div></td></tr>`}).join('')||'<tr><td colspan="7" class="muted">未发现系统数据库</td></tr>'}
async function loadDatabases(button){const run=async()=>{const data=await api('/api/data-center/databases');renderDatabases(data);return data};try{return await (button?busy(button,'检查中...',run):run())}catch(error){if(!requestCancelled(error))toast(error.message,true)}}
async function checkpointDb(key,truncate,button){if(truncate&&!confirm('只截断已写回数据库的空闲 WAL，不删除业务记录。继续吗？'))return;try{return await busy(button,'处理中...',async()=>{const data=await api('/api/data-center/databases/'+encodeURIComponent(key)+'/checkpoint',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({truncate})});toast(data.message||'检查点已完成',!data.ok);await loadDatabases()})}catch(error){if(!requestCancelled(error))toast(error.message,true)}}
async function diagnose(button){return busy(button,'诊断中...',async()=>{
  const requests=[
    ['readiness',api('/api/data-center/decision-readiness?'+query())],
    ['status',api('/api/data-center/status')],
    ['missing',api('/api/data-center/missing-fields')],
    ['errors',api('/api/data-center/source-errors')],
    ['databases',api('/api/data-center/databases')],
  ];
  const settled=await Promise.allSettled(requests.map(x=>x[1]));if(pageUnloading)return;
  const values={},failures=[],componentLabels={readiness:'决策就绪度',status:'缓存状态',missing:'缺失字段',errors:'数据源错误',databases:'数据库'};
  settled.forEach((result,index)=>{const key=requests[index][0];if(result.status==='fulfilled')values[key]=result.value;else if(!requestCancelled(result.reason))failures.push(`${componentLabels[key]||key}：${result.reason?.message||result.reason}`)});
  if(values.readiness)renderReadiness(values.readiness);
  if(values.errors)renderSources(values.errors);
  if(values.databases)renderDatabases(values.databases);
  if(values.status)$('rawStatus').textContent=JSON.stringify(values.status,null,2);
  if(values.missing)$('rawMissing').textContent=JSON.stringify(values.missing,null,2);
  $('rawErrors').textContent=JSON.stringify({source_errors:values.errors||null,request_failures:failures},null,2);
  if(failures.length)toast(`诊断已部分完成；${failures.join('；')}`,true);else toast('缓存与数据库诊断已更新，未访问外部网络');
})}
async function doRefresh(symbols,scopes,force,button){return busy(button,force?'强制抓取中...':'刷新中...',async()=>{const result=await api('/api/data-center/refresh',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbols,scopes,force,mode:$('mode').value,strategy_family:$('strategy').value})});renderReadiness(result.readiness||{data:[]});$('rawErrors').textContent=JSON.stringify(result,null,2);const failed=(result.results||[]).filter(x=>!x.ok);toast(`刷新完成：${(result.results||[]).length-failed.length} 项成功，${failed.length} 项缺失/失败`,failed.length>0);const errors=await api('/api/data-center/source-errors');renderSources(errors);return result})}
async function refreshSelected(button,force){const scopes=selectedScopes();if(!scopes.length){toast('请至少勾选一个数据类别',true);return}try{return await doRefresh($('symbols').value.trim(),scopes,force,button)}catch(error){if(!requestCancelled(error))toast(error.message,true)}}
async function refreshOne(symbol,scope,button){try{return await doRefresh(symbol,[scope],true,button)}catch(error){if(!requestCancelled(error))toast(error.message,true)}}
window.addEventListener('DOMContentLoaded',()=>diagnose(document.querySelector('.btn.primary')).catch(error=>{if(!requestCancelled(error))toast(error.message,true)}));
</script>
</body></html>"""
