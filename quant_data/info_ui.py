from __future__ import annotations


def build_info_ui() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>信息面分析详情 V3.15.2</title>
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
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.global-card{background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:10px;margin-bottom:8px}.global-card h4{font-size:14px;margin:0 0 6px}.global-list{max-height:680px;overflow:auto}.small{font-size:12px;color:#64748b}.log{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;border-radius:10px;padding:10px;max-height:150px;overflow:auto;font-size:12px;}.pager{display:flex;gap:8px;align-items:center;justify-content:center;margin:14px 0}.pager button{width:auto;padding:8px 14px}.pager span{font-size:13px;color:#475569}.empty{padding:26px;text-align:center;color:#64748b;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px}.warnbox{background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:12px;padding:10px;line-height:1.55;font-size:13px}.formula{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:9px;font-size:12px;line-height:1.6;color:#334155;}
  @media(max-width:1100px){.controls{grid-template-columns:repeat(2,1fr)}.layout{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header><h1>信息面分析详情 V3.15.2 / 分层、分页、去重、评分映射</h1><div><a class="toplink" href="/screener">返回筛选页</a><a class="toplink" href="/ui">行情监控</a></div></header>
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
      <div><button class="green" onclick="refreshAll(true)">强制抓取并重算</button></div>
      <div><button class="secondary" onclick="loadPage(1)">只刷新分页</button></div>
    </div>
    <div class="small" style="margin-top:8px">说明：搜索引擎关键词页彻底禁用；公司/公告信息需主动刷新或缓存过期才刷新。全球/国内/商品/政策要闻为短缓存自动刷新，只有与公司主营、业务标签、产业链暴露相关时才进入信息面映射分。</div>
  </section>

  <section class="panel summary" id="summary"></section>

  <div class="layout">
    <section>
      <div class="panel">
        <div class="tabs">
          <button class="tab active" data-tab="items" onclick="switchTab('items')">个股信息流</button>
          <button class="tab" data-tab="global" onclick="switchTab('global')">全球/前沿要闻</button>
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
function params(){const u=new URLSearchParams(location.search);return {symbol:$('symbol').value.trim(),name:$('name').value.trim(),limit:Math.max(30,Math.min(500,Number($('limit').value)||180)),page_size:Math.max(5,Math.min(200,Number($('pageSize').value)||30)),sort:$('sort').value,include_unknown_date:$('unknown').value,snapshot_id:u.get('snapshot_id')||''};}
function stat(k,v,s=''){return `<div class="stat"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div>${s?`<div class="s">${esc(s)}</div>`:''}</div>`}
function bars(rows, nameKey='name', countKey='count', cls=''){const max=Math.max(1,...(rows||[]).map(x=>Number(x[countKey]||0)));return (rows||[]).map(x=>`<div class="barline"><span>${esc(x[nameKey]||x.category||x.source||'--')}</span><div class="bar"><i class="${cls}" style="width:${Math.max(2,Number(x[countKey]||0)/max*100)}%"></i></div><b>${esc(x[countKey]||0)}</b></div>`).join('')||'<div class="small">暂无统计</div>'}
function sentCls(x){x=String(x||'');return x.includes('正')?'pos':x.includes('负')?'neg':'neu'}
function renderSummary(){const a=state.analysis||{};const n=a.news||{};const ec=a.evidence_counts||{};$('summary').innerHTML=[
  stat('信息面分',a.info_score??'--','已进入筛选综合分'),stat('公司/事件分',n.news_score??'--','事件级去重'),stat('要闻映射分',a.policy?.policy_score??'--',`相关${a.global_news_used?.related_count??0}条`),stat('财报估值分',a.finance?.finance_score??'--','估值+财务摘要'),stat('高可信信息',ec.high_confidence_items??'--','公告/权威源'),stat('负面证据',ec.negative_evidence??'--','新闻+财务+政策'),stat('未知日期',ec.unknown_date_items??'--','可筛掉'),stat('信息总量',n.count??a.news?.items?.length??'--','入库+新抓取')].join('');
  $('formula').innerHTML=`<b>信息面分公式：</b><br>${esc(a.scoring_model?.['信息面分公式']||'0.32×公司/公告事件 + 0.13×来源可信度 + 0.20×财报估值 + 0.28×前沿要闻/行业映射 + 0.07×(100-传闻噪声)')}<br><br><b>筛选融合：</b><br>${esc(a.scoring_model?.['筛选融合公式']||'启用信息面评分后进入综合评分')}<br><br><b>总结：</b><br>${esc(a.summary||'--')}`;
  renderCharts();renderSources();renderFramework();
}
function renderCharts(){const n=(state.analysis||{}).news||{};const pd=state.pageData||{};const st=(pd.stats||{});$('charts').innerHTML=`<div class="small">消息面模块</div>${bars(n.dimension_counts||[])}<div class="small" style="margin-top:10px">事件类别</div>${bars(n.category_counts||st.by_category||[])}<div class="small" style="margin-top:10px">来源占比</div>${bars(n.source_counts||st.by_source||[])}`;}
function renderSources(){const n=(state.analysis||{}).news||{};const status=n.sources_status||[];$('sources').innerHTML=status.length?status.map(s=>`<div>【${esc(s.source)}】${esc(s.count??0)}条：${esc(s.status||'--')}</div>`).join(''):'暂无诊断';}
function renderFramework(){const a=state.analysis||{};const fw=a.message_framework||{};const sp=a.source_policy||{};let html='<div class="warnbox">消息面按宏观经济、行业、公司、市场资金面、国际消息、舆情分层。官方公告优先；社区只作舆情；搜索引擎结果页禁用。</div>';
  html += '<h3>消息面分析框架</h3>'+Object.entries(fw).map(([k,v])=>`<div class="item"><b>${esc(k)}</b><div class="small">${Array.isArray(v)?v.map(esc).join('、'):esc(v)}</div></div>`).join('');
  html += '<h3>信息源分层</h3>'+Object.entries(sp).map(([k,v])=>`<div class="item"><b>${esc(k)}</b><div class="small">${Array.isArray(v)?v.map(esc).join('、'):esc(v)}</div></div>`).join('');
  $('frameworkBox').innerHTML=html;
}
async function refreshAll(force=false){const p=params();log((force?'强制':'缓存')+`分析 ${p.name||p.symbol}，limit=${p.limit}`);const url=`/api/info/analyze/${encodeURIComponent(p.symbol)}?name=${encodeURIComponent(p.name)}&limit=${p.limit}&force=${force}&snapshot_id=${encodeURIComponent(p.snapshot_id||'')}`;const res=await fetch(url,{cache:'no-store'});const js=await res.json();if(!js.ok){alert('分析失败');return}state.analysis=js.data;renderSummary();await loadPage(1);await loadGlobal(force);log(`分析完成：信息面分=${js.data.info_score}，新闻=${js.data.news?.count??0}条，政策线索=${js.data.policy?.policy_clue_count??0}`)}
async function loadPage(page=1){const p=params();page=Math.max(1,Math.min(page,state.total_pages||999));let url=`/api/info/items/${encodeURIComponent(p.symbol)}?page=${page}&page_size=${p.page_size}&sort=${p.sort}&include_unknown_date=${p.include_unknown_date}`;if($('category').value.trim())url+='&category='+encodeURIComponent($('category').value.trim());const res=await fetch(url,{cache:'no-store'});const js=await res.json();state.page=page;state.pageData=js.data||{};state.total_pages=state.pageData.total_pages||1;renderItems();renderCharts();renderDedup();}
function renderItems(){const d=state.pageData||{};let data=d.data||[];const dim=$('dimensionFilter').value;if(dim)data=data.filter(x=>(x.message_dimension||'')===dim);$('items').innerHTML=data.length?data.map(renderItem).join(''):'<div class="empty">暂无信息。可以强制抓取，或放宽过滤条件。</div>';$('pagerInfo').textContent=`第 ${state.page} / ${state.total_pages||1} 页，共 ${d.total??0} 条`;}
function renderItem(x){const sent=x.sentiment_label||((Number(x.sentiment_score||50)>=58)?'正面':(Number(x.sentiment_score||50)<=45?'负面':'中性'));const url=x.url||'#';const ev=(x.evidence||[]).map(esc).join('；');return `<article class="item"><h3><a href="${esc(url)}" target="_blank" rel="noreferrer">${esc(x.title||'--')}</a></h3><div class="meta"><span>发布:${esc(x.publish_time||x.published_at_norm||x.published_at||'未知')} / 事件:${esc(x.event_time||'--')} / 抓取:${esc(x.crawl_time||'--')}</span><span>${esc(x.source||'--')}</span><span class="badge macro">${esc(x.message_dimension||'公司消息')}</span><span class="badge ${sentCls(sent)}">${esc(sent)}</span><span class="badge neu">${esc(x.category||'其他')}</span><span class="badge warn">可信${esc(x.credibility_score??'--')} / 影响${esc(x.impact_score??'--')} / 传闻${esc(x.fake_risk_score??'--')}</span></div><div class="summary-text">${esc(x.summary||'')}</div>${x.target_relation?`<div class="evidence"><b>当前标的关系：</b>${esc(x.target_relation)}；${esc(x.relation_note||'')}</div>`:''}${ev?`<div class="evidence"><b>证据：</b>${ev}</div>`:''}<div class="small">事件类型：${esc(x.event_type||'general')}；周期：${esc(x.period||'--')}；去重键：${esc(x.event_key||x.duplicate_group||'--')}；${esc(x.dedup_reason||'')}</div></article>`}
function renderDedup(){const st=(state.pageData||{}).stats||{};const dups=st.duplicate_groups||[];$('dedupBox').innerHTML=`<div class="warnbox">重复组用于检查“同一事件多源转载是否重复计分”。系统按 event_key/duplicate_group 合并，只保留最高可信版本进入主评分。</div>${dups.length?dups.map(x=>`<div class="item"><b>${esc(x.title||'--')}</b><div class="small">重复 ${esc(x.c)} 条；key=${esc(x.duplicate_group||'')}</div></div>`).join(''):'<div class="empty">暂无重复组，或当前库已按事件合并。</div>'}`;}
async function loadGlobal(force=false){const p=params();log('刷新全球/国内/商品要闻');const res=await fetch(`/api/news/global?limit=${Math.min(200,p.limit)}&force=${force}`,{cache:'no-store'});const js=await res.json();state.global=js.data||{};renderGlobal();}
function renderGlobal(){const g=state.global||{};const items=g.items||[];$('globalDims').innerHTML='<div class="small">国内 '+(g.domestic_count||0)+' / 全球 '+(g.global_count||0)+' / 商品 '+(g.commodity_count||0)+'；更新时间 '+esc(g.updated_at||'--')+'</div>'+bars(g.dimension_counts||g.category_counts||[]);$('globalSent').innerHTML=bars(g.market_category_counts||g.category_counts||[])+'<div class="small" style="margin-top:8px">情绪结构</div>'+bars([{name:'正面',count:g.positive_count||0},{name:'负面',count:g.negative_count||0},{name:'中性',count:g.neutral_count||0}], 'name','count');$('globalItems').innerHTML=items.length?items.slice(0,180).map(renderItem).join(''):'<div class="empty">暂无全球要闻。检查命令窗和 sources_status。</div>';}
function switchTab(t){state.tab=t;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.tab===t));$('tabItems').style.display=t==='items'?'block':'none';$('tabGlobal').style.display=t==='global'?'block':'none';$('tabDedup').style.display=t==='dedup'?'block':'none';$('tabFramework').style.display=t==='framework'?'block':'none';}
(function init(){const u=new URLSearchParams(location.search);if(u.get('symbol'))$('symbol').value=u.get('symbol');if(u.get('name'))$('name').value=u.get('name');if(u.get('limit'))$('limit').value=u.get('limit'); if(u.get('snapshot_id'))log('沿用筛选页 snapshot_id='+u.get('snapshot_id')); refreshAll(false);setInterval(()=>{loadGlobal(false).catch(()=>{})},60000);})();
</script>
</body></html>'''
