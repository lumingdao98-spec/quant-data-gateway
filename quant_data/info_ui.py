from __future__ import annotations


def build_info_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>信息面分析详情 V3.18.3</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;margin:0;background:#f5f7fb;color:#1f2937;}
  header{background:#0f172a;color:#fff;padding:14px 22px;display:flex;align-items:center;justify-content:space-between;gap:16px;position:sticky;top:0;z-index:10;box-shadow:0 6px 20px rgba(15,23,42,.18)}
  header h1{font-size:18px;margin:0;font-weight:800}.toplink{color:#bfdbfe;text-decoration:none;margin-left:12px;font-size:13px}
  main{padding:16px 20px;max-width:1420px;margin:0 auto;}
  .panel{background:#fff;border-radius:14px;box-shadow:0 4px 18px rgba(15,23,42,.08);padding:14px;margin-bottom:14px;border:1px solid #e5e7eb;}
  .controls{display:grid;grid-template-columns:repeat(10,minmax(92px,1fr));gap:10px;align-items:end;}
  label{font-size:12px;color:#64748b;display:block;margin-bottom:4px;} input,select,button{border:1px solid #d1d5db;border-radius:10px;padding:9px 10px;font-size:14px;background:#fff;box-sizing:border-box;width:100%;}
  button{cursor:pointer;background:#2563eb;color:#fff;border-color:#2563eb;font-weight:700;}button.secondary{background:#f8fafc;color:#334155;border-color:#cbd5e1;}button.green{background:#16a34a;border-color:#16a34a}
  .summary{display:grid;grid-template-columns:repeat(8,1fr);gap:10px;}.stat{background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:10px;min-width:0}.stat .k{font-size:12px;color:#64748b}.stat .v{font-size:19px;font-weight:800;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.stat .s{font-size:11px;color:#94a3b8;margin-top:3px;}
  .layout{display:grid;grid-template-columns:1fr 360px;gap:14px;align-items:start}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}.tab{width:auto;background:#f8fafc;color:#334155;border:1px solid #cbd5e1;padding:8px 12px}.tab.active{background:#2563eb;color:#fff;border-color:#2563eb}
  .item{border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin-bottom:10px;background:#fff;}.item h3{font-size:15px;margin:0 0 8px 0;line-height:1.45;}.item h3 a{color:#1e40af;text-decoration:none}.item h3 a:hover{text-decoration:underline}.meta{display:flex;flex-wrap:wrap;gap:6px 10px;font-size:12px;color:#64748b;margin-bottom:8px;}
  .badge{display:inline-flex;border-radius:999px;padding:2px 8px;background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe;font-size:12px;align-items:center}.badge.neg{background:#fef2f2;color:#991b1b;border-color:#fecaca}.badge.pos{background:#f0fdf4;color:#166534;border-color:#bbf7d0}.badge.neu{background:#f8fafc;color:#475569;border-color:#e2e8f0}.badge.warn{background:#fffbeb;color:#92400e;border-color:#fde68a}.badge.macro{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.summary-text{font-size:13px;color:#475569;line-height:1.65;}.evidence{font-size:12px;color:#334155;background:#f8fafc;border-radius:8px;padding:7px 9px;margin-top:8px;line-height:1.55;}
  .side h3{font-size:15px;margin:4px 0 10px}.barline{display:grid;grid-template-columns:90px 1fr 46px;gap:8px;align-items:center;border-bottom:1px dashed #e5e7eb;padding:7px 0;font-size:13px;}.bar{height:10px;background:#eef2f7;border-radius:999px;overflow:hidden;border:1px solid #e2e8f0}.bar i{display:block;height:100%;background:#60a5fa;width:0}.bar i.neg{background:#f87171}.bar i.pos{background:#4ade80}.bar i.warn{background:#facc15}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.global-card{background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:10px;margin-bottom:8px}.global-card h4{font-size:14px;margin:0 0 6px}.global-list{max-height:680px;overflow:auto}.small{font-size:12px;color:#64748b}.log{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;border-radius:10px;padding:10px;max-height:150px;overflow:auto;font-size:12px;}.pager{display:flex;gap:8px;align-items:center;justify-content:center;margin:14px 0}.pager button{width:auto;padding:8px 14px}.pager span{font-size:13px;color:#475569}.empty{padding:26px;text-align:center;color:#64748b;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px}.warnbox{background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:12px;padding:10px;line-height:1.55;font-size:13px}.snapshot-box{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;border-radius:12px;padding:10px;line-height:1.55;font-size:13px;margin-top:10px}.formula{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:9px;font-size:12px;line-height:1.6;color:#334155;}
  @media(max-width:1100px){.controls{grid-template-columns:repeat(2,1fr)}.layout{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header><h1>信息面分析详情 V3.18.3 / 快照复用、缓存状态、全球行业映射</h1><div><a class="toplink" href="/screener">返回筛选页</a><a class="toplink" href="/cache">缓存状态</a><a class="toplink" href="/ui">行情监控</a></div></header>
<main>
  <section class="panel">
    <div class="controls">
      <div><label>股票代码</label><input id="symbol" value="600519"></div>
      <div><label>股票名称</label><input id="name" value="贵州茅台"></div>
      <div><label>抓取/聚合上限</label><input id="limit" type="number" value="180" min="30" max="500"></div>
      <div><label>分页大小</label><input id="pageSize" type="number" value="30" min="5" max="200"></div>
      <div><label>排序</label><select id="sort"><option value="desc">时间倒序</option><option value="asc">时间正序</option></select></div>
      <div><label>信息模块</label><select id="dimensionFilter"><option value="">全部模块</option><option>官方公告/公司披露</option><option>公司消息</option><option>行业消息/政策消息</option><option>宏观经济消息</option><option>市场资金面消息</option><option>国际消息/全球市场</option><option>社会舆情/社区讨论</option></select></div>
      <div><label>事件类别</label><input id="category" placeholder="如 财报业绩"></div>
      <div><label>包含未知日期</label><select id="unknown"><option value="true">包含</option><option value="false">不包含</option></select></div>
      <div><button class="secondary" onclick="loadLatestSnapshot()">读取最近快照</button></div>
      <div><button class="green" onclick="refreshAll(true,false)">普通刷新</button></div>
      <div><button class="secondary" onclick="refreshAll(false,true)">深度刷新</button></div>
      <div><button class="secondary" onclick="clearInfoCache()">清除缓存</button></div>
    </div>
    <div id="snapshotBox" class="snapshot-box">当前使用筛选页快照时，详情页会优先读取 snapshot_id；只有强制抓取或深度刷新才重新抓取。</div>
    <div id="cacheStateBox" class="snapshot-box">缓存状态：等待加载。空数据时会显示 source_logs 和可执行动作，不再空白。</div>
    <div class="small" style="margin-top:8px">说明：搜索引擎关键词页彻底禁用；公司/公告信息需主动刷新或缓存过期才刷新。全球/国内/商品/政策要闻为短缓存自动刷新，只有与公司主营、业务标签、产业链暴露相关时才进入信息面映射分。</div>
  </section>

  <section class="panel summary" id="summary"></section>

  <div class="layout">
    <section>
      <div class="panel">
        <div class="tabs">
          <button class="tab active" data-tab="items" onclick="switchTab('items')">个股信息流</button>
          <button class="tab" data-tab="global" onclick="switchTab('global')">全球/行业映射</button>
          <button class="tab" data-tab="dedup" onclick="switchTab('dedup')">去重与重复组</button>
          <button class="tab" data-tab="framework" onclick="switchTab('framework')">消息面框架</button>
        </div>
        <div id="tabItems">
          <div id="items"></div>
          <div class="pager"><button class="secondary" onclick="loadPage(state.page-1)">上一页</button><span id="pagerInfo">--</span><button class="secondary" onclick="loadPage(state.page+1)">下一页</button></div>
        </div>
        <div id="tabGlobal" style="display:none">
          <div class="grid2">
            <div class="global-card"><h4>全球/国内要闻模块分布</h4><div id="globalDims"></div></div>
            <div class="global-card"><h4>全球要闻情绪/风险结构</h4><div id="globalSent"></div></div>
          </div>
          <div class="global-card"><h4>全球信息与当前个股映射证据</h4><div id="industryMappedItems" class="global-list"></div></div>
          <div class="global-card"><h4>最新全球/国内/商品快讯</h4><div id="globalItems" class="global-list"></div></div>
        </div>
        <div id="tabDedup" style="display:none"><div id="dedupBox"></div></div>
        <div id="tabFramework" style="display:none"><div id="frameworkBox"></div></div>
      </div>
    </section>
    <aside class="side">
      <div class="panel"><h3>统计图</h3><div id="charts"></div></div>
      <div class="panel"><h3>评分模型</h3><div id="formula" class="formula">--</div></div>
      <div class="panel"><h3>信息源诊断</h3><div id="sources" class="small">--</div></div>
      <div class="panel"><h3>后台进度提示</h3><div class="log" id="log">页面日志会显示请求进度；命令窗也会同步打印 [信息面] 进度。</div></div>
    </aside>
  </div>
</main>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
let state={page:1,total_pages:1,analysis:null,pageData:null,global:null,tab:'items'};
function log(msg){$('log').textContent = new Date().toLocaleTimeString()+' '+msg+'\n'+$('log').textContent;}
function params(){const u=new URLSearchParams(location.search);return {symbol:$('symbol').value.trim(),name:$('name').value.trim(),limit:Math.max(30,Math.min(500,Number($('limit').value)||180)),page_size:Math.max(5,Math.min(200,Number($('pageSize').value)||30)),sort:$('sort').value,include_unknown_date:$('unknown').value,snapshot_id:u.get('snapshot_id')||'',force:u.get('force')==='true'};}
function stat(k,v,s=''){return `<div class="stat"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div>${s?`<div class="s">${esc(s)}</div>`:''}</div>`}
function bars(rows, nameKey='name', countKey='count', cls=''){const max=Math.max(1,...(rows||[]).map(x=>Number(x[countKey]||0)));return (rows||[]).map(x=>`<div class="barline"><span>${esc(x[nameKey]||x.category||x.source||'--')}</span><div class="bar"><i class="${cls}" style="width:${Math.max(2,Number(x[countKey]||0)/max*100)}%"></i></div><b>${esc(x[countKey]||0)}</b></div>`).join('')||'<div class="small">暂无统计</div>'}
function sentCls(x){x=String(x||'');return x.includes('正')?'pos':x.includes('负')?'neg':'neu'}
function renderSummary(){const a=state.analysis||{};const n=a.news||{};const ec=a.evidence_counts||{};const raw=(a.items||n.items||[]).length||n.count||0;const unknown=(a.items||n.items||[]).filter(x=>!(x.publish_time||x.published_at_norm||x.published_at||x.date)).length;$('summary').innerHTML=[
  stat('Info score',a.info_score??'--','merged into screener score'),stat('Event score',n.news_score??'--','deduped event score'),stat('Global map score',a.policy?.policy_score??'--',`related ${a.global_news_used?.related_count??0}`),stat('Finance score',a.finance?.finance_score??'--','valuation and finance'),stat('Raw items',raw,'default filter is broad'),stat('Filtered items',state.pageData?.data?.length??raw,'after page/filter'),stat('Unknown date',ec.unknown_date_items??unknown,'included by default'),stat('Total items',n.count??a.news?.items?.length??'--','cached plus fetched')].join('');
  $('formula').innerHTML=`<b>Info score formula:</b><br>${esc(a.score_model?.formula||'company/events + credibility + finance + global/industry mapping - rumor risk')}<br><br><b>Screener merge:</b><br>${esc(a.score_model?.screener_formula||'info score joins total score when enabled')}<br><br><b>Summary:</b><br>${esc(a.summary||a.diagnostics?.summary||'--')}`;
  const cs=a.cache_status||{};const usingSnapshot=!!(a.used_snapshot||a.snapshot_reused||(['hit','stale'].includes(String(cs.status||''))&&String(cs.source||'').includes('info_')));const snapshotLabel=a.mode==='snapshot_miss'?'Snapshot missing, no auto refresh':usingSnapshot?'Using screener/recent snapshot':'Using manual refreshed result';$('snapshotBox').innerHTML=`${snapshotLabel}; snapshot_id=${esc(a.snapshot_id||'--')}; created_at=${esc(a.updated_at||a.created_at||'--')}; effective=${esc(ec.item_count??n.count??a.items?.length??'--')}; unique_events=${esc(n.count??'--')}. Use deep refresh only when needed.`;
  $('cacheStateBox').innerHTML=`cache_status=${esc(cs.status||'--')}; age=${esc(cs.age_seconds??'--')}s; ttl=${esc(cs.ttl_seconds??'--')}s; source=${esc(cs.source||'--')}. ${cs.stale?'Stale cache is still displayed; refresh manually.':'Cache is usable.'}`;
  renderCharts();renderSources();renderFramework();renderGlobal();
}
function renderCharts(){const n=(state.analysis||{}).news||{};const pd=state.pageData||{};const st=(pd.stats||{});$('charts').innerHTML=`<div class="small">消息面模块</div>${bars(n.dimension_counts||[])}<div class="small" style="margin-top:10px">事件类别</div>${bars(n.category_counts||st.by_category||[])}<div class="small" style="margin-top:10px">来源占比</div>${bars(n.source_counts||st.by_source||[])}`;}
function renderSources(){const a=state.analysis||{};const n=a.news||{};const status=a.source_logs||n.sources_status||[];$('sources').innerHTML=status.length?status.map(s=>`<div>【${esc(s.source)}】${esc(s.count??0)}条：${esc(s.status||'--')} ${s.elapsed_ms!=null?' · '+esc(s.elapsed_ms)+'ms':''} ${s.skipped_reason?' · '+esc(s.skipped_reason):''}</div>`).join(''):'暂无诊断；如果个股信息为空，这里会显示最近抓取日志和错误原因。';}
function renderFramework(){const a=state.analysis||{};const fw=a.message_framework||{};const sp=a.source_policy||{};let html='<div class="warnbox">消息面按宏观经济、行业、公司、市场资金面、国际消息、舆情分层。官方公告优先；社区只作舆情；搜索引擎结果页禁用。</div>';
  html += '<h3>消息面分析框架</h3>'+Object.entries(fw).map(([k,v])=>`<div class="item"><b>${esc(k)}</b><div class="small">${Array.isArray(v)?v.map(esc).join('、'):esc(v)}</div></div>`).join('');
  html += '<h3>信息源分层</h3>'+Object.entries(sp).map(([k,v])=>`<div class="item"><b>${esc(k)}</b><div class="small">${Array.isArray(v)?v.map(esc).join('、'):esc(v)}</div></div>`).join('');
  $('frameworkBox').innerHTML=html;
}
async function refreshAll(force=false, deep=false){const p=params();log((deep?'深度刷新':force?'强制':'快照/缓存')+`分析 ${p.name||p.symbol}，limit=${p.limit}`);const url=`/api/info/analyze/${encodeURIComponent(p.symbol)}?name=${encodeURIComponent(p.name)}&limit=${p.limit}&force=${force}&deep_refresh=${deep}&snapshot_id=${encodeURIComponent(p.snapshot_id||'')}`;const res=await fetch(url,{cache:'no-store'});const js=await res.json();if(!js.ok){alert('分析失败');return}state.analysis=js.data;renderSummary();await loadPage(1);if(deep)await loadGlobal(force);log(`分析完成：信息面分=${js.data.info_score}，新闻=${js.data.news?.count??0}条，政策线索=${js.data.policy?.policy_clue_count??0}，${js.data.snapshot_reused?'复用筛选页快照':'已刷新'}`)}
async function loadLatestSnapshot(){const p=params();const res=await fetch(`/api/cache/info/latest/${encodeURIComponent(p.symbol)}`,{cache:'no-store'});const js=await res.json();if(js.ok&&js.data){state.analysis=js.data;renderSummary();state.pageData={data:state.analysis.items||[],total:(state.analysis.items||[]).length,total_pages:1,stats:state.analysis.stats||{}};state.total_pages=1;renderItems();renderCharts();renderDedup();log('已读取最近信息快照 '+(js.snapshot_id||''));}else{log('暂无最近快照，自动普通刷新');await refreshAll(false,false)}}
async function clearInfoCache(){const p=params();await fetch(`/api/cache/clear?kind=info_snapshot&symbol=${encodeURIComponent(p.symbol)}`,{method:'POST'});log('已清除该股信息快照缓存，可重新普通刷新或深度刷新');}
async function loadPage(page=1){const p=params();page=Math.max(1,page);let url=`/api/info/items/${encodeURIComponent(p.symbol)}?page=${page}&page_size=${p.page_size}&sort=${p.sort}&include_unknown_date=${p.include_unknown_date}`;if($('category').value.trim())url+='&category='+encodeURIComponent($('category').value.trim());const res=await fetch(url,{cache:'no-store'});const js=await res.json();state.pageData=js.data||{};state.total_pages=state.pageData.total_pages||1;if(page>state.total_pages&&state.total_pages>0){return loadPage(1)}state.page=page;renderItems();renderCharts();renderDedup();}
function clearInfoFilters(){if($('dimensionFilter'))$('dimensionFilter').value='';if($('category'))$('category').value='';if($('unknown'))$('unknown').value='true';state.page=1;loadPage(1)}
function renderItems(){const d=state.pageData||{};const original=d.data||[];let data=original;const dim=$('dimensionFilter').value;if(dim)data=data.filter(x=>(x.message_dimension||'')===dim);const rawTotal=(state.analysis?.items||state.analysis?.news?.items||[]).length||d.total||original.length;const unknown=(state.analysis?.items||[]).filter(x=>!(x.publish_time||x.published_at_norm||x.published_at||x.date)).length;const mappedRelated=(state.analysis?.industry_mapped_items||[]).filter(x=>x.included_in_score||x.score_included).length;let empty=mappedRelated?`<div class="empty">No stock-specific items yet / 暂无个股新闻；已找到 ${mappedRelated} 条全球/行业/题材映射证据，请切到“全球/行业映射”查看政策、行业和概念影响链。</div>`:'<div class="empty">No stock-specific items yet / 暂无信息. Source logs and errors remain visible; use latest snapshot, normal refresh, or deep refresh.</div>';if(!data.length&&original.length)empty='<div class="empty">Current filters hide all items. <button class="secondary" onclick="clearInfoFilters()">Clear filters</button></div>';$('items').innerHTML=data.length?data.map(renderItem).join(''):empty;$('pagerInfo').textContent=`page ${state.page} / ${state.total_pages||1}; total ${d.total??0}; raw ${rawTotal}; filtered ${data.length}; unknown_date ${unknown}; module=${$('dimensionFilter').value||'all'}; event=${$('category').value||'all'}; include_unknown_date=${$('unknown').value}`;}
function renderItem(x){const sent=x.sentiment_label||((Number(x.sentiment_score||50)>=58)?'正面':(Number(x.sentiment_score||50)<=45?'负面':'中性'));const url=x.url||'#';const ev=(x.evidence||[]).map(esc).join('；');return `<article class="item"><h3><a href="${esc(url)}" target="_blank" rel="noreferrer">${esc(x.title||'--')}</a></h3><div class="meta"><span>发布:${esc(x.publish_time||x.published_at_norm||x.published_at||'未知')} / 事件:${esc(x.event_time||'--')} / 抓取:${esc(x.crawl_time||'--')}</span><span>${esc(x.source||'--')}</span><span class="badge macro">${esc(x.message_dimension||'公司消息')}</span><span class="badge ${sentCls(sent)}">${esc(sent)}</span><span class="badge neu">${esc(x.category||'其他')}</span><span class="badge warn">可信${esc(x.credibility_score??'--')} / 影响${esc(x.impact_score??'--')} / 传闻${esc(x.fake_risk_score??'--')}</span></div><div class="summary-text">${esc(x.summary||'')}</div>${x.target_relation?`<div class="evidence"><b>当前标的关系：</b>${esc(x.target_relation)}；${esc(x.relation_note||'')}</div>`:''}${ev?`<div class="evidence"><b>证据：</b>${ev}</div>`:''}<div class="small">事件类型：${esc(x.event_type||'general')}；周期：${esc(x.period||'--')}；去重键：${esc(x.event_key||x.duplicate_group||'--')}；${esc(x.dedup_reason||'')}</div></article>`}
function renderDedup(){const st=(state.pageData||{}).stats||{};const dups=st.duplicate_groups||[];$('dedupBox').innerHTML=`<div class="warnbox">重复组用于检查“同一事件多源转载是否重复计分”。系统按 event_key/duplicate_group 合并，只保留最高可信版本进入主评分。</div>${dups.length?dups.map(x=>`<div class="item"><b>${esc(x.title||'--')}</b><div class="small">重复 ${esc(x.c)} 条；key=${esc(x.duplicate_group||'')}</div></div>`).join(''):'<div class="empty">暂无重复组，或当前库已按事件合并。</div>'}`;}
async function loadGlobal(force=false){const p=params();log('刷新全球/国内/商品要闻');const res=await fetch(`/api/news/global?limit=${Math.min(200,p.limit)}&force=${force}`,{cache:'no-store'});const js=await res.json();state.global=js.data||{};renderGlobal();}
function renderGlobal(){const g=state.global||{};const items=g.items||state.analysis?.global_items||[];const mapped=(state.analysis?.industry_mapped_items||[]);$('globalDims').innerHTML='<div class="small">domestic '+(g.domestic_count||0)+' / global '+(g.global_count||items.length||0)+' / commodity '+(g.commodity_count||0)+'; updated '+esc(g.updated_at||state.analysis?.created_at||'--')+'</div>'+bars(g.dimension_counts||g.category_counts||[]);$('globalSent').innerHTML=bars(g.market_category_counts||g.category_counts||[])+'<div class="small" style="margin-top:8px">sentiment</div>'+bars([{name:'positive',count:g.positive_count||0},{name:'negative',count:g.negative_count||0},{name:'neutral',count:g.neutral_count||0}], 'name','count');$('industryMappedItems').innerHTML=mapped.length?mapped.slice(0,80).map(x=>`<div class="global-card"><h4>${esc(x.title||'--')}</h4><div class="small">industries: ${esc((x.mapped_industries||[]).join(', ')||'--')}; concepts: ${esc((x.mapped_concepts||[]).join(', ')||'--')}; symbols: ${esc((x.mapped_symbols||[]).join(', ')||'--')}; direction: ${esc(x.impact_direction||'neutral')}; relevance: ${esc(x.relevance_score??'--')}; ${(x.included_in_score??x.score_included)?'included in score':'not included in score'}</div><div class="summary-text">impact_reason: ${esc(x.impact_reason||'missing company profile or no industry keyword hit')}</div></div>`).join(''):'<div class="empty">No global/industry mapping evidence yet: no global news, no strong relevance, or missing company profile. Unrelated global news stays market background.</div>';$('globalItems').innerHTML=items.length?items.slice(0,180).map(renderItem).join(''):'<div class="empty">No global news yet. Check source_logs.</div>';}
function switchTab(t){state.tab=t;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.tab===t));$('tabItems').style.display=t==='items'?'block':'none';$('tabGlobal').style.display=t==='global'?'block':'none';$('tabDedup').style.display=t==='dedup'?'block':'none';$('tabFramework').style.display=t==='framework'?'block':'none';}
(function init(){const u=new URLSearchParams(location.search);if(u.get('symbol'))$('symbol').value=u.get('symbol');if(u.get('name'))$('name').value=u.get('name');if(u.get('limit'))$('limit').value=u.get('limit');$('dimensionFilter').value='';$('category').value='';$('unknown').value='true'; if(u.get('snapshot_id'))log('using snapshot_id='+u.get('snapshot_id')); refreshAll(u.get('force')==='true',false);setInterval(()=>{loadGlobal(false).catch(()=>{})},60000);})();
</script>
</body></html>'''
