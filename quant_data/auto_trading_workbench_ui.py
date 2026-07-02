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
.layout{display:grid;grid-template-columns:330px minmax(520px,1fr) 380px;gap:18px;align-items:start}.panel{overflow:hidden}.panel h2{font-size:18px;margin:0;padding:15px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:10px}.panel-body{padding:16px 18px}.field{display:grid;gap:7px;margin-bottom:13px}.field label{font-size:13px;color:#667085;font-weight:800}.field input,.field select,.field textarea{border:1px solid var(--line);background:#f8fafc;border-radius:10px;padding:10px 12px;color:var(--text);min-width:0}.field textarea{min-height:82px;resize:vertical}.field textarea.compact{min-height:58px}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}.config-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.check-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:2px 0 12px}.check{display:flex;align-items:flex-start;gap:8px;border:1px solid var(--line);background:#fbfcff;border-radius:10px;padding:9px;color:#475569;font-size:12px;font-weight:800;line-height:1.45}.check input{width:auto;margin-top:2px}.btn{border:0;border-radius:10px;padding:10px 14px;font-weight:900;color:#fff;background:var(--cyan);cursor:pointer}.btn.blue{background:var(--blue)}.btn.dark{background:#273247}.btn.red{background:var(--red)}.btn.ghost{background:#fff;color:#334155;border:1px solid var(--line)}.btn.small{padding:7px 10px;font-size:12px}.btn:disabled{opacity:.55;cursor:not-allowed}
.module-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.module{display:block;padding:13px;background:#fbfcff}.module b{display:block;margin-bottom:6px}.module span{display:block;color:#7a8498;font-size:12px;line-height:1.55;overflow-wrap:anywhere}.module:hover{border-color:var(--cyan);background:#f0fffd}.notice{background:#fff7df;border:1px solid #ffe2a3;color:#8a5a00;border-radius:10px;padding:12px;line-height:1.65;font-size:13px;overflow-wrap:anywhere}.ok{color:var(--green)}.bad{color:var(--red)}.muted{color:#7a8498}.log{max-height:250px;overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fbfcff;padding:10px;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;color:#334155;overflow-wrap:anywhere}.status-table{width:100%;border-collapse:collapse;table-layout:fixed}.status-table th,.status-table td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;font-size:13px;vertical-align:top;overflow-wrap:anywhere}.status-table th{color:#5c6678;background:#f8fafc}
.decision{padding:24px;border-top:5px solid var(--cyan)}.decision h3{font-size:34px;margin:0;color:#111827}.decision p{line-height:1.75;color:#4a5568;margin:16px 0}.score-bars{display:grid;gap:10px}.bar{height:9px;background:#edf1f7;border-radius:99px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue))}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);background:#fbfdff}.decision-grid div{padding:15px;text-align:center;border-right:1px solid var(--line)}.decision-grid div:last-child{border-right:0}.decision-grid b{display:block;font-size:20px;margin-top:7px;overflow-wrap:anywhere}
.mini-card{border:1px solid var(--line);border-radius:10px;padding:11px;background:#fbfcff;margin-bottom:10px}.mini-card b{display:block;margin-bottom:6px}.source-link{color:#079d99;text-decoration:underline}.footer-note{margin-top:18px;color:#7a8498;font-size:12px;line-height:1.7}
.quick-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:0 0 18px}.quick-step{border:1px solid var(--line);background:#fff;border-radius:12px;padding:12px;box-shadow:var(--shadow);display:flex;gap:10px;align-items:flex-start}.quick-step b{display:grid;place-items:center;width:28px;height:28px;border-radius:999px;background:#e7fdfa;color:#078f89;flex:0 0 auto}.quick-step strong{display:block;font-size:14px;margin-bottom:3px}.quick-step span{display:block;color:#667085;font-size:12px;line-height:1.45;overflow-wrap:anywhere}.preset-row,.catalog-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.preset-row{margin:8px 0 12px}.preset{border:1px solid var(--line);background:#f8fafc;color:#334155;border-radius:999px;padding:7px 10px;font-weight:900;font-size:12px;cursor:pointer}.preset:hover,.preset.active{border-color:var(--cyan);background:#e9fffc;color:#078f89}.strategy-catalog{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;max-height:220px;overflow:auto;margin:8px 0 12px;padding-right:3px}.strategy-chip{border:1px solid var(--line);background:#fbfcff;border-radius:10px;padding:9px;display:grid;grid-template-columns:auto 1fr;gap:8px;align-items:flex-start;cursor:pointer}.strategy-chip input{margin-top:2px}.strategy-chip b{display:block;font-size:13px;line-height:1.25}.strategy-chip span{display:block;color:#6b7280;font-size:11px;line-height:1.35;margin-top:3px;overflow-wrap:anywhere}.strategy-chip.on{border-color:#7dd3fc;background:#f0fdff}.helper-strip{border:1px solid #c8f3ee;background:#f1fffd;color:#0f766e;border-radius:12px;padding:10px 12px;font-size:13px;line-height:1.55;margin-bottom:12px}.action-row{display:flex;flex-wrap:wrap;gap:8px}.compact-link{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 10px;font-weight:900;font-size:12px;color:#334155}.compact-link:hover{border-color:var(--cyan);color:#078f89}.card .value{font-size:22px}.decision h3{font-size:28px}.main{padding:22px 24px 34px}.layout{grid-template-columns:310px minmax(540px,1fr) 340px}.module-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.module-jump{display:flex;gap:8px;flex-wrap:wrap;margin:-8px 0 14px}.module-jump a{display:inline-flex;align-items:center;border:1px solid var(--line);background:#fff;border-radius:999px;padding:8px 12px;font-size:12px;font-weight:900;color:#334155;box-shadow:0 8px 20px rgba(25,38,71,.05)}.module-jump a.primary{background:#e9fffc;border-color:#8ee8df;color:#078f89}.module-jump a:hover{border-color:var(--cyan);color:#078f89}.beginner-note{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0 0 14px}.beginner-note div{border:1px solid #c8f3ee;background:#f1fffd;border-radius:12px;padding:10px 12px;font-size:12px;line-height:1.5;color:#0f766e}.beginner-note b{display:block;color:#065f5b;margin-bottom:3px}.app{grid-template-columns:252px minmax(0,1fr)}.brand{height:66px;padding:0 18px}.logo{width:34px;height:34px;border-radius:10px}.nav{padding:8px 0}.nav a{padding:11px 18px;font-size:14px}.top{height:64px;padding:0 18px}.main{padding:16px 20px 26px}.title-row{margin-bottom:12px}.title-row h1{font-size:21px}.title-row p{font-size:13px;line-height:1.45}.quick-flow{gap:8px;margin-bottom:14px}.quick-step{padding:9px}.quick-step b{width:24px;height:24px}.quick-step strong{font-size:13px}.kpis{gap:10px;margin-bottom:14px}.card{padding:12px}.card .value{font-size:18px;margin-top:6px}.layout{grid-template-columns:280px minmax(560px,1fr) 320px;gap:12px}.panel h2{font-size:15px;padding:11px 13px}.panel-body{padding:12px 13px}.module{padding:10px}.module span{line-height:1.4}.field{gap:5px;margin-bottom:9px}.field input,.field select,.field textarea{padding:8px 10px}.strategy-catalog{max-height:170px}.decision{padding:16px}.decision h3{font-size:23px}.decision p{font-size:13px;line-height:1.6;margin:10px 0}.decision-grid div{padding:10px}.decision-grid b{font-size:16px}.log{max-height:190px}
@media(max-width:1320px){.app{grid-template-columns:84px 1fr}.brand span,.nav span,.side-foot{display:none}.nav a{justify-content:center;padding:16px}.layout{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.quick-flow{grid-template-columns:repeat(2,minmax(0,1fr))}.strategy-catalog{grid-template-columns:1fr}.beginner-note{grid-template-columns:1fr}}@media(max-width:780px){.app{grid-template-columns:1fr}.side{display:none}.top{position:static}.main{padding:18px}.quick-flow,.kpis,.split,.decision-grid,.module-grid,.config-grid,.check-grid,.beginner-note{grid-template-columns:1fr}}
</style>
<style>
.path-board{display:grid;grid-template-columns:1.1fr 1fr 1fr 1fr;gap:10px;margin:0 0 14px}.path-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:11px;box-shadow:var(--shadow);min-width:0}.path-card strong{display:flex;align-items:center;gap:8px;font-size:14px;margin-bottom:6px}.path-card strong i{font-style:normal;display:grid;place-items:center;width:24px;height:24px;border-radius:999px;background:#e7fdfa;color:#078f89}.path-card p{margin:0;color:#667085;font-size:12px;line-height:1.45;overflow-wrap:anywhere}.path-card .mini-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.path-card .mini-actions button,.path-card .mini-actions a{border:1px solid var(--line);border-radius:999px;background:#f8fafc;color:#334155;padding:6px 9px;font-size:12px;font-weight:900;cursor:pointer}.path-card .mini-actions .primary{background:#19c6c0;border-color:#19c6c0;color:#fff}.path-card .mini-actions .blue{background:#2f7cf6;border-color:#2f7cf6;color:#fff}.path-card .mini-actions .red{background:#fff1f2;border-color:#fecaca;color:#be123c}.workflow-status{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:8px}.workflow-status span{border:1px solid var(--line);background:#fbfcff;border-radius:8px;padding:6px;font-size:11px;color:#667085;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.workflow-status b{color:#172033}.module-jump{position:sticky;top:64px;background:linear-gradient(#f4f7fb 70%,rgba(244,247,251,.72));z-index:4;padding:4px 0 8px}@media(max-width:1320px){.path-board{grid-template-columns:1fr 1fr}.module-jump{position:static}}@media(max-width:780px){.path-board,.workflow-status{grid-template-columns:1fr}}
.coach-strip{display:grid;grid-template-columns:minmax(220px,1.2fr) repeat(4,minmax(120px,.8fr));gap:8px;align-items:stretch;margin:0 0 12px}.coach-strip .coach-copy{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow);min-width:0}.coach-strip b{display:block;font-size:14px}.coach-strip span{display:block;color:#667085;font-size:12px;line-height:1.45;margin-top:3px;overflow-wrap:anywhere}.coach-action{border:1px solid var(--line);background:#fff;border-radius:12px;padding:10px 12px;text-align:left;font-weight:900;box-shadow:var(--shadow);cursor:pointer;min-width:0}.coach-action small{display:block;color:#667085;font-size:11px;font-weight:700;line-height:1.35;margin-top:3px}.coach-action.primary{background:#19c6c0;border-color:#19c6c0;color:#fff}.coach-action.primary small{color:#ecfeff}.selected-strategy-summary{border:1px solid #c8f3ee;background:#f1fffd;border-radius:10px;padding:9px 10px;font-size:12px;line-height:1.5;color:#0f766e;margin:-2px 0 9px;max-height:72px;overflow:auto}.advanced-box{border:1px dashed var(--line);border-radius:10px;padding:8px 10px;margin-bottom:10px;background:#fbfcff}.advanced-box summary{cursor:pointer;font-weight:900;color:#475569;font-size:12px}.advanced-box .field{margin-top:8px;margin-bottom:0}.mini-help{color:#667085;font-size:12px;line-height:1.45;margin-top:-4px;margin-bottom:8px;overflow-wrap:anywhere}@media(max-width:1320px){.coach-strip{grid-template-columns:1fr 1fr}}@media(max-width:780px){.coach-strip{grid-template-columns:1fr}}
</style>
<style>
.strategy-param-panel{border:1px solid var(--line);border-radius:12px;background:#fbfcff;margin:8px 0 12px;overflow:hidden}.strategy-param-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border-bottom:1px solid var(--line);font-size:12px;color:#475569}.strategy-param-table-wrap{max-height:230px;overflow:auto}.strategy-param-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}.strategy-param-table th,.strategy-param-table td{border-bottom:1px solid var(--line);padding:7px;vertical-align:middle;overflow-wrap:anywhere}.strategy-param-table th{position:sticky;top:0;background:#eef6ff;color:#334155;z-index:1}.strategy-param-table input,.strategy-param-table select{padding:6px 7px;border-radius:8px}.strategy-param-table .strategy-name{font-weight:900;color:#172033}.strategy-param-table .strategy-note{display:block;color:#667085;font-size:11px;line-height:1.35;margin-top:2px}.dimension-strip{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin:8px 0 10px}.dimension-strip div{border:1px solid #dbeafe;background:#f8fbff;border-radius:10px;padding:8px;font-size:11px;line-height:1.35;color:#475569}.dimension-strip b{display:block;color:#1d4ed8;margin-bottom:2px}@media(max-width:1320px){.dimension-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.strategy-param-table{min-width:820px}}@media(max-width:780px){.dimension-strip{grid-template-columns:1fr}}
</style>
<style>
.embedded-workspace{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;margin:0 0 14px}
.workspace-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#f0fffd,#f8fbff)}
.workspace-head b{display:block;font-size:16px}.workspace-head span{display:block;color:#667085;font-size:12px;line-height:1.45;margin-top:3px;overflow-wrap:anywhere}
.workspace-tabs{display:flex;gap:8px;flex-wrap:wrap;padding:10px 12px;border-bottom:1px solid var(--line);background:#fbfcff}
.workspace-tab{border:1px solid var(--line);background:#fff;border-radius:999px;color:#334155;padding:7px 10px;font-weight:900;font-size:12px;cursor:pointer}
.workspace-tab.active{background:#19c6c0;border-color:#19c6c0;color:#fff}
.workspace-frame-wrap{height:min(78vh,900px);min-height:620px;background:#0b1020;position:relative}
.workspace-frame{width:100%;height:100%;border:0;display:none;background:#0b1020}
.workspace-frame.active{display:block}
.workspace-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.workspace-tools a,.workspace-tools button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 10px;font-size:12px;font-weight:900;color:#334155;cursor:pointer}
.workspace-status{color:#667085;font-size:12px;max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:1320px){.workspace-frame-wrap{height:760px;min-height:560px}.workspace-head{align-items:flex-start;flex-direction:column}.workspace-status{max-width:100%}}
@media(max-width:780px){.workspace-frame-wrap{height:700px;min-height:520px}.workspace-tabs{overflow:auto;flex-wrap:nowrap}.workspace-tab{flex:0 0 auto}}
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
        <div><h1>自动交易总控台</h1><p>给不想盯工程参数的人用：先筛选建池，再一键配置，先回测，再实时模拟，最后才进入真实交易确认。</p></div>
        <div class="row"><span class="pill warn">不伪造真实数据</span><button class="btn blue" onclick="refreshAll()">刷新状态</button></div>
      </div>
      <section class="coach-strip" aria-label="新手交易路径">
        <div class="coach-copy"><b>当前推荐路径</b><span>没有金融背景也按这条线走：系统会用筛选分、技术、信息、资金、大盘和风控合成动作；真实交易永远需要确认。</span></div>
        <button class="coach-action primary" type="button" onclick="oneClickConfig()">一键生成配置<small>从股票池和预设写入策略/仓位/风控</small></button>
        <button class="coach-action" type="button" onclick="runConfigBacktest()">跑一次回测<small>先看收益、回撤和买卖点是否合理</small></button>
        <button class="coach-action" type="button" onclick="startPaper()">启动实时模拟<small>开盘用真实行情，休市只做观察回放</small></button>
        <button class="coach-action" type="button" onclick="openWorkspaceKey('records','交易记录')">查看交易记录<small>订单、成交、持仓、审计统一查看</small></button>
      </section>
      <nav class="module-jump">
        <a class="primary" href="/screener" onclick="openWorkspaceKey('screener','筛选建池');return false">筛选建池</a>
        <a href="#paperControl">一键配置</a>
        <a href="/backtest" onclick="openWorkspaceKey('backtest','历史回测');return false">历史回测</a>
        <a href="/realtime-paper" onclick="openWorkspaceKey('realtime','实时模拟');return false">实时模拟</a>
        <a href="/live-trading" onclick="openWorkspaceKey('live','实盘确认');return false">实盘确认</a>
        <a href="/trading-records" onclick="openWorkspaceKey('records','交易记录');return false">交易记录</a>
        <a href="/data-center" onclick="openWorkspaceKey('data','数据中心');return false">数据中心</a>
        <a href="/docs-cn" onclick="openWorkspaceKey('docs','中文 API');return false">中文 API</a>
      </nav>
      <section class="embedded-workspace" id="embeddedWorkspace">
        <div class="workspace-head">
          <div><b>一页式模块工作区</b><span>下面直接嵌入原来的完整页面：筛选、行情详情、回测、实时模拟、真实交易、交易记录、数据中心和中文 API 都保留原功能，不做缩水版。</span></div>
          <div class="workspace-tools">
            <span class="workspace-status" id="workspaceStatus">当前：股票筛选</span>
            <button type="button" onclick="reloadWorkspaceFrame()">刷新内置页</button>
            <button type="button" onclick="openWorkspaceInNewWindow()">新窗口打开</button>
          </div>
        </div>
        <div class="workspace-tabs" id="workspaceTabs">
          <button class="workspace-tab active" type="button" data-module="screener" data-url="/screener" data-label="股票筛选" onclick="openWorkspaceKey('screener','股票筛选',this)">股票筛选</button>
          <button class="workspace-tab" type="button" data-module="quote" data-url="/ui?symbol=300750&frame=time" data-label="行情监控/分时" onclick="openWorkspaceKey('quote','行情监控/分时',this)">行情监控</button>
          <button class="workspace-tab" type="button" data-module="detail" data-url="/detail/300750?frame=1d" data-label="详情/K线" onclick="openWorkspaceKey('detail','详情/K线',this)">详情/K线</button>
          <button class="workspace-tab" type="button" data-module="backtest" data-url="/backtest?symbol=300750" data-label="历史回测" onclick="openWorkspaceKey('backtest','历史回测',this)">历史回测</button>
          <button class="workspace-tab" type="button" data-module="realtime" data-url="/realtime-paper" data-label="实时模拟" onclick="openWorkspaceKey('realtime','实时模拟',this)">实时模拟</button>
          <button class="workspace-tab" type="button" data-module="live" data-url="/live-trading" data-label="真实交易" onclick="openWorkspaceKey('live','真实交易',this)">真实交易</button>
          <button class="workspace-tab" type="button" data-module="records" data-url="/trading-records" data-label="交易记录" onclick="openWorkspaceKey('records','交易记录',this)">交易记录</button>
          <button class="workspace-tab" type="button" data-module="data" data-url="/data-center" data-label="数据中心" onclick="openWorkspaceKey('data','数据中心',this)">数据中心</button>
          <button class="workspace-tab" type="button" data-module="docs" data-url="/docs-cn" data-label="中文 API" onclick="openWorkspaceKey('docs','中文 API',this)">中文 API</button>
        </div>
        <div class="workspace-frame-wrap">
          <iframe id="workspaceFrame" class="workspace-frame active" data-module="screener" data-src="/screener" data-current-url="/screener" data-loaded="true" title="V3.23 自动交易内置模块工作区 · 股票筛选" src="/screener"></iframe>
          <iframe id="workspaceFrameQuote" class="workspace-frame" data-module="quote" data-src="/ui?symbol=300750&frame=time" title="V3.23 自动交易内置模块工作区 · 行情监控/分时"></iframe>
          <iframe id="workspaceFrameDetail" class="workspace-frame" data-module="detail" data-src="/detail/300750?frame=1d" title="V3.23 自动交易内置模块工作区 · 详情/K线"></iframe>
          <iframe id="workspaceFrameBacktest" class="workspace-frame" data-module="backtest" data-src="/backtest?symbol=300750" title="V3.23 自动交易内置模块工作区 · 历史回测"></iframe>
          <iframe id="workspaceFrameRealtime" class="workspace-frame" data-module="realtime" data-src="/realtime-paper" title="V3.23 自动交易内置模块工作区 · 实时模拟"></iframe>
          <iframe id="workspaceFrameLive" class="workspace-frame" data-module="live" data-src="/live-trading" title="V3.23 自动交易内置模块工作区 · 真实交易"></iframe>
          <iframe id="workspaceFrameRecords" class="workspace-frame" data-module="records" data-src="/trading-records" title="V3.23 自动交易内置模块工作区 · 交易记录"></iframe>
          <iframe id="workspaceFrameData" class="workspace-frame" data-module="data" data-src="/data-center" title="V3.23 自动交易内置模块工作区 · 数据中心"></iframe>
          <iframe id="workspaceFrameDocs" class="workspace-frame" data-module="docs" data-src="/docs-cn" title="V3.23 自动交易内置模块工作区 · 中文 API"></iframe>
        </div>
      </section>
      <section class="beginner-note">
        <div><b>不会金融也能用</b>先选“均衡入门/防守学习/ETF轮动”，系统会自动填仓位、止损止盈、最大回撤和事件监控。</div>
        <div><b>交易方向来自筛选</b>筛选分、技术面、资金面、信息面、基本面和大盘情绪共同进入信号，不用手动猜买卖方向。</div>
        <div><b>实盘默认锁住</b>QMT/PTrade 未授权时只显示 disabled/unsupported；真实下单必须风控通过和人工确认。</div>
      </section>
      <section class="path-board" aria-label="自动交易工作流">
        <div class="path-card">
          <strong><i>1</i>从筛选生成交易配置</strong>
          <p>把最新筛选结果、自选池或手动股票池转换成策略组合，自动带入仓位、止盈止损、回撤和事件监控。</p>
          <div class="mini-actions"><button class="primary" onclick="loadLatestScreenerConfig()">读取最新筛选</button><button onclick="oneClickConfig()">一键配置</button><a href="/screener" onclick="openWorkspaceKey('screener','去筛选');return false">去筛选</a></div>
          <div class="workflow-status"><span>股票池 <b id="wfSymbols">--</b></span><span>策略 <b id="wfCombo">--</b></span><span>仓位 <b id="wfSizing">--</b></span><span>事件 <b id="wfEvents">开启</b></span></div>
        </div>
        <div class="path-card">
          <strong><i>2</i>先回测，不直接实盘</strong>
          <p>用同一套配置回放历史 K 线，检查收益、最大回撤、交易次数、买卖点和跑输原因。</p>
          <div class="mini-actions"><button class="blue" onclick="runConfigBacktest()">用配置回测</button><a href="/backtest" onclick="openWorkspaceKey('backtest','打开回测页');return false">打开回测页</a></div>
        </div>
        <div class="path-card">
          <strong><i>3</i>再实时模拟</strong>
          <p>开盘时按真实行情生成 paper 信号；休市只做观察回放，不伪装真实成交。订单、持仓、标注和审计都会落库。</p>
          <div class="mini-actions"><button class="primary" onclick="startPaper()">启动模拟</button><button onclick="manualTick()">执行一轮</button><a href="/realtime-paper" onclick="openWorkspaceKey('realtime','打开模拟页');return false">打开模拟页</a></div>
          <div class="workflow-status"><span>session <b id="wfSession">--</b></span><span>记录 <b id="wfRecords">--</b></span><span>确认 <b id="wfConfirm">--</b></span><span>数据 <b id="wfData">--</b></span></div>
        </div>
        <div class="path-card">
          <strong><i>4</i>最后才进入实盘确认</strong>
          <p>QMT/PTrade 默认关闭。未授权只显示状态；真实订单必须通过风控、确认队列和 kill switch 检查。</p>
          <div class="mini-actions"><a class="red" href="/live-trading" onclick="openWorkspaceKey('live','实盘确认页');return false">实盘确认页</a><a href="/trading-records" onclick="openWorkspaceKey('records','交易记录');return false">交易记录</a><a href="/data-center" onclick="openWorkspaceKey('data','数据中心');return false">数据中心</a></div>
          <div class="workflow-status"><span>券商 <b id="wfBroker">--</b></span><span>实盘 <b id="wfLive">关闭</b></span><span>风控 <b id="wfRisk">确认</b></span><span>Kill <b id="wfKill">--</b></span></div>
        </div>
      </section>
      <section class="quick-flow">
        <a class="quick-step" href="/screener" onclick="openWorkspaceKey('screener','先筛选');return false"><b>1</b><span><strong>先筛选</strong>生成股票池、四面评分和风险标签。</span></a>
        <a class="quick-step" href="#paperControl"><b>2</b><span><strong>一键配置</strong>选择新手预设或策略组合，自动写入风控参数。</span></a>
        <a class="quick-step" href="/backtest" onclick="openWorkspaceKey('backtest','先回测');return false"><b>3</b><span><strong>先回测</strong>验证收益、回撤、买卖点和跑输原因。</span></a>
        <a class="quick-step" href="/realtime-paper" onclick="openWorkspaceKey('realtime','再模拟');return false"><b>4</b><span><strong>再模拟</strong>真实行情驱动 paper trading，记录订单和持仓。</span></a>
        <a class="quick-step" href="/live-trading" onclick="openWorkspaceKey('live','后实盘');return false"><b>5</b><span><strong>后实盘</strong>默认关闭，必须券商可用、风控通过并人工确认。</span></a>
      </section>

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
              <a class="module" href="/screener" onclick="openWorkspaceKey('screener','股票筛选');return false"><b>股票筛选</b><span>四面评分、策略适配、加入回测/模拟/实盘观察池。</span></a>
              <a class="module" href="/detail/300750" onclick="openWorkspaceKey('detail','详情决策');return false"><b>详情决策</b><span>分时、K线、信息面、基本面、资金面和风控原因。</span></a>
              <a class="module" href="/backtest" onclick="openWorkspaceKey('backtest','历史回测');return false"><b>历史回测</b><span>订单、成交、买卖点、收益诊断和评分溯源。</span></a>
              <a class="module" href="/realtime-paper" onclick="openWorkspaceKey('realtime','实时模拟');return false"><b>实时模拟</b><span>真实行情驱动的 paper trading session。</span></a>
              <a class="module" href="/live-trading" onclick="openWorkspaceKey('live','真实交易');return false"><b>真实交易</b><span>QMT/PTrade 状态、确认队列、kill switch。</span></a>
              <a class="module" href="/trading-records" onclick="openWorkspaceKey('records','交易记录');return false"><b>交易记录</b><span>回测、模拟、实盘统一流水和审计。</span></a>
              <a class="module" href="/data-center" onclick="openWorkspaceKey('data','数据中心');return false"><b>数据中心</b><span>缓存、缺失字段、数据源错误、后台任务。</span></a>
              <a class="module" href="/docs-cn" onclick="openWorkspaceKey('docs','中文 API');return false"><b>中文 API</b><span>接口中文说明、参数和调试入口。</span></a>
            </div>
          </div>
          <div class="panel" id="paperControl">
            <h2>实时模拟控制</h2>
            <div class="panel-body">
              <div class="field"><label>模拟股票池</label><textarea id="symbols" oninput="syncWorkspaceTabUrls()">300750, 600438, 510300</textarea></div>
              <div class="split">
                <div class="field"><label>策略族</label><select id="strategy"><option value="hybrid">综合评分</option><option value="etf_momentum_rotation">ETF 动量轮动</option><option value="score_reversal">评分拐点修复</option><option value="core_satellite">核心-卫星</option></select></div>
                <div class="field"><label>刷新频率</label><select id="interval"><option value="15">15 秒</option><option value="30">30 秒</option><option value="60">60 秒</option><option value="0">仅手动执行一轮</option></select></div>
              </div>
              <div class="notice" id="configSummary">自动交易配置尚未加载；可一键从最新筛选结果生成模拟配置。</div>
              <div class="helper-strip">新手路径：先点“均衡入门”或“防守学习”，再点“一键配置”，最后先跑回测和实时模拟。真实交易入口只做确认队列和券商状态，不会默认下单。</div>
              <div class="catalog-head"><b>新手预设</b><span class="muted">会自动填策略组合、仓位模型、止盈止损和最大回撤</span></div>
              <div class="preset-row" id="presetRow">
                <button class="preset" type="button" onclick="selectBeginnerPreset('balanced')">均衡入门</button>
                <button class="preset" type="button" onclick="selectBeginnerPreset('defensive')">防守学习</button>
                <button class="preset" type="button" onclick="selectBeginnerPreset('etf_rotation')">ETF轮动</button>
              </div>
              <div class="field"><label>策略组合（下方中文勾选；英文 key 仅供系统保存）</label><textarea class="compact" id="strategyCombo" oninput="renderStrategyCatalog(lastAutoConfig||{})">score_driven, low_position, avoid_chasing_high, ma_repair, macd_cross, volume_breakout, atr_risk, position_risk, risk_control, event_driven, finance_quality, market_regime</textarea></div>
              <div id="strategySelectedSummary" class="selected-strategy-summary">已选策略会在这里翻译成中文，方便确认系统到底在看什么。</div>
              <div class="catalog-head"><b>策略目录</b><span class="muted" id="strategyCatalogHint">加载中...</span></div>
              <div id="strategyCatalog" class="strategy-catalog"></div>
              <div id="dimensionStrip" class="dimension-strip"></div>
              <div class="strategy-param-panel">
                <div class="strategy-param-head"><b>组合策略参数表</b><span>每个策略可独立设置仓位控制、止损、止盈和最大回撤</span></div>
                <div class="strategy-param-table-wrap">
                  <table class="strategy-param-table">
                    <thead><tr><th>策略</th><th>启用</th><th>仓位</th><th>单票%</th><th>止损%</th><th>止盈%</th><th>最大回撤%</th><th>买入分</th><th>卖出分</th></tr></thead>
                    <tbody id="strategyParamRows"><tr><td colspan="9" class="muted">选择策略或一键配置后自动生成</td></tr></tbody>
                  </table>
                </div>
              </div>
              <details class="advanced-box">
                <summary>高级策略参数 JSON（可选，不懂可以不填）</summary>
                <div class="field"><label>每个策略可单独配置仓位/止盈/止损/最大回撤</label><textarea class="compact" id="strategyParamJson">{}</textarea></div>
              </details>
              <div class="mini-help">简单用法：选“均衡入门/防守学习/ETF轮动”即可。想更细再勾选“低位修复、均线修复、MACD、温和放量、大盘情绪过滤”等策略。</div>
              <div class="split">
                <div class="field"><label>仓位模型</label><select id="positionSizing"><option value="score_weighted">评分加权</option><option value="atr_risk">ATR风险仓位</option><option value="volatility_target">波动率目标</option><option value="fixed_weight">固定权重</option><option value="core_satellite">核心-卫星</option><option value="cash_first_defensive">现金优先防守</option></select></div>
                <div class="field"><label>初始资金</label><input id="initialCash" type="number" value="100000"></div>
              </div>
              <div class="config-grid">
                <div class="field"><label>止损%</label><input id="stopLossPct" type="number" value="8" step="0.1"></div>
                <div class="field"><label>止盈%</label><input id="takeProfitPct" type="number" value="18" step="0.1"></div>
                <div class="field"><label>最大回撤%</label><input id="maxDrawdownPct" type="number" value="18" step="0.1"></div>
                <div class="field"><label>单票上限%</label><input id="maxSinglePositionPct" type="number" value="20" step="0.1"></div>
                <div class="field"><label>总仓位上限%</label><input id="maxTotalPositionPct" type="number" value="80" step="0.1"></div>
                <div class="field"><label>现金保留%</label><input id="minCashPct" type="number" value="15" step="0.1"></div>
              </div>
              <div class="check-grid">
                <label class="check"><input id="watchFinancialReports" type="checkbox" checked> 财报/业绩预告</label>
                <label class="check"><input id="watchHalfYearReports" type="checkbox" checked> 半年报/年报窗口</label>
                <label class="check"><input id="watchAnnouncements" type="checkbox" checked> 交易所/巨潮公告</label>
                <label class="check"><input id="watchMajorNews" type="checkbox" checked> 重大负面/舆情风险</label>
                <label class="check"><input id="watchPolicyNews" type="checkbox" checked> 行业政策/宏观事件</label>
                <label class="check"><input id="requireFreshQuote" type="checkbox" checked> 数据过期禁止新增仓位</label>
                <label class="check"><input id="resetAccount" type="checkbox" checked> 启动时新建模拟账户，不继承上次持仓</label>
              </div>
              <div class="row" style="margin-bottom:12px"><button class="btn blue" onclick="oneClickConfig()">一键配置</button><button class="btn ghost" onclick="loadLatestScreenerConfig()">读取最新筛选</button><button class="btn ghost" onclick="saveAutoConfig()">保存配置</button></div>
              <div class="row"><button class="btn" onclick="startPaper()">启动模拟 session</button><button class="btn ghost" onclick="manualTick()">执行一轮模拟</button><button class="btn ghost" onclick="runConfigBacktest()">用配置回测</button><button class="btn ghost" onclick="pausePaper()">暂停</button><button class="btn ghost" onclick="resumePaper()">恢复</button><button class="btn red" onclick="stopPaper()">停止</button><button class="btn red" onclick="killPaper()">模拟 Kill</button></div>
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
              <div class="row"><button class="btn blue" onclick="connectLive()">连接检查</button><button class="btn red" onclick="killLive()">Live Kill Switch</button><a class="btn ghost" href="/live-trading" onclick="openWorkspaceKey('live','进入实盘页');return false">进入实盘页</a></div>
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
let lastAutoConfig=null;
let currentWorkspaceUrl='/screener';
async function api(url,opt){const r=await fetch(url,opt);try{return await r.json()}catch(e){return {ok:false,message:String(e),status:r.status}}}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function primarySymbol(){const list=typeof symbols==='function'?symbols():splitListText($('symbols')?.value);return (list[0]||'300750').trim()||'300750'}
function workspaceUrl(key){
  const sym=encodeURIComponent(primarySymbol());
  const map={
    screener:'/screener',
    quote:'/ui?symbol='+sym+'&frame=time',
    detail:'/detail/'+sym+'?frame=1d',
    backtest:'/backtest?symbol='+sym,
    realtime:'/realtime-paper',
    live:'/live-trading',
    records:'/trading-records',
    data:'/data-center',
    docs:'/docs-cn',
  };
  return map[key]||'/screener';
}
function syncWorkspaceTabUrls(){
  document.querySelectorAll('#workspaceTabs .workspace-tab[data-module]').forEach(tab=>{
    const url=workspaceUrl(tab.dataset.module);
    tab.dataset.url=url;
    const frame=workspaceFrameForModule(tab.dataset.module);
    if(frame && frame.dataset.loaded!=='true')frame.dataset.src=url;
  });
}
function openWorkspaceKey(key,label,btn){
  syncWorkspaceTabUrls();
  const tab=btn||document.querySelector(`#workspaceTabs .workspace-tab[data-module="${key}"]`);
  openWorkspaceModule(workspaceUrl(key),label||tab?.dataset.label||key,tab);
}
function workspaceTabForUrl(url){
  syncWorkspaceTabUrls();
  const tabs=[...document.querySelectorAll('#workspaceTabs .workspace-tab')];
  return tabs.find(t=>t.dataset.url===url)||tabs.find(t=>url.startsWith((t.dataset.url||'').split('?')[0]));
}
function setWorkspaceActive(btn){
  document.querySelectorAll('#workspaceTabs .workspace-tab').forEach(t=>t.classList.toggle('active',t===btn));
}
function workspaceKeyForUrl(url,btn){
  if(btn?.dataset?.module)return btn.dataset.module;
  const tab=workspaceTabForUrl(url||'');
  return tab?.dataset?.module||'screener';
}
function workspaceFrameForModule(key){
  return document.querySelector(`.workspace-frame[data-module="${key}"]`)||$('workspaceFrame');
}
function activeWorkspaceFrame(){
  return document.querySelector('.workspace-frame.active')||$('workspaceFrame');
}
function setWorkspaceFrameActive(frame){
  document.querySelectorAll('.workspace-frame').forEach(f=>f.classList.toggle('active',f===frame));
}
function ensureWorkspaceFrame(key,url){
  const frame=workspaceFrameForModule(key);
  if(!frame)return null;
  const next=url||frame.dataset.src||workspaceUrl(key);
  frame.dataset.src=next;
  if(frame.dataset.currentUrl!==next || frame.dataset.loaded!=='true'){
    frame.src=next;
    frame.dataset.currentUrl=next;
    frame.dataset.loaded='true';
  }
  setWorkspaceFrameActive(frame);
  return frame;
}
function openWorkspaceModule(url,label,btn){
  currentWorkspaceUrl=url||'/screener';
  const key=workspaceKeyForUrl(currentWorkspaceUrl,btn);
  ensureWorkspaceFrame(key,currentWorkspaceUrl);
  const status=$('workspaceStatus');
  if(status)status.textContent='当前：'+(label||currentWorkspaceUrl);
  setWorkspaceActive(btn||workspaceTabForUrl(currentWorkspaceUrl));
  try{localStorage.setItem('v323_auto_workspace_url',currentWorkspaceUrl);localStorage.setItem('v323_auto_workspace_label',label||'')}catch(e){}
}
function reloadWorkspaceFrame(){const frame=activeWorkspaceFrame();if(frame)frame.src=frame.src||frame.dataset.src||currentWorkspaceUrl||'/screener'}
function openWorkspaceInNewWindow(){const frame=activeWorkspaceFrame();window.open(currentWorkspaceUrl||frame?.getAttribute('src')||frame?.dataset.src||'/screener','_blank','noopener')}
function initWorkspaceFrame(){
  syncWorkspaceTabUrls();
  let saved='/screener',label='股票筛选';
  try{saved=localStorage.getItem('v323_auto_workspace_url')||saved;label=localStorage.getItem('v323_auto_workspace_label')||label}catch(e){}
  const btn=workspaceTabForUrl(saved);
  openWorkspaceModule(saved,label,btn);
}
function splitListText(v){return String(v||'').split(/[\s,，;；、|]+/).map(s=>s.trim()).filter(Boolean)}
function symbols(){return splitListText($('symbols').value)}
function strategyCombo(){return splitListText($('strategyCombo').value)}
function pct(v){return Math.max(0,Math.min(100,Number(v||0)))}
function setScore(id,val){$(id+'Score').textContent=val==null?'--':Number(val).toFixed(1);$(id+'Bar').style.width=pct(val)+'%'}
function brief(row){return esc(row?.status||row?.event_type||row?.marker_type||row?.side||row?.order_id||row?.fill_id||row?.symbol||'--')}
function money(v){const n=Number(v);return Number.isFinite(n)?n.toLocaleString('zh-CN',{maximumFractionDigits:2}):'--'}
function sessionIdOf(item){return item?.session_id||item?.id||item?.sessionId||''}
function num(id,fallback){const n=Number($(id)?.value);return Number.isFinite(n)?n:fallback}
function checked(id){return !!$(id)?.checked}
function parseStrategyParams(){
  let raw={};
  try{raw=JSON.parse($('strategyParamJson')?.value||'{}')}
  catch(e){$('auditLog').textContent='策略参数 JSON 解析失败：'+e;raw={}}
  return {...raw,...collectStrategyParamEditor(raw)};
}
function strategyParamNumber(el,fallback){
  const n=Number(el?.value);
  return Number.isFinite(n)?n:fallback;
}
function collectStrategyParamEditor(base={}){
  const rows=[...document.querySelectorAll('[data-strategy-row]')];
  const out={};
  rows.forEach(row=>{
    const key=row.dataset.strategyRow;
    if(!key)return;
    const current={...(base[key]||{})};
    out[key]={
      ...current,
      strategy:key,
      enabled:!!row.querySelector('[data-param="enabled"]')?.checked,
      position_sizing:row.querySelector('[data-param="position_sizing"]')?.value||current.position_sizing||$('positionSizing')?.value||'score_weighted',
      position_control:row.querySelector('[data-param="position_sizing"]')?.value||current.position_control||$('positionSizing')?.value||'score_weighted',
      max_single_position_pct:strategyParamNumber(row.querySelector('[data-param="max_single_position_pct"]'),Number(current.max_single_position_pct??$('maxSinglePositionPct')?.value??20)),
      stop_loss_pct:strategyParamNumber(row.querySelector('[data-param="stop_loss_pct"]'),Number(current.stop_loss_pct??$('stopLossPct')?.value??8)),
      take_profit_pct:strategyParamNumber(row.querySelector('[data-param="take_profit_pct"]'),Number(current.take_profit_pct??$('takeProfitPct')?.value??18)),
      max_drawdown_pct:strategyParamNumber(row.querySelector('[data-param="max_strategy_drawdown_pct"]'),Number(current.max_strategy_drawdown_pct??current.max_drawdown_pct??$('maxDrawdownPct')?.value??18)),
      max_strategy_drawdown_pct:strategyParamNumber(row.querySelector('[data-param="max_strategy_drawdown_pct"]'),Number(current.max_strategy_drawdown_pct??current.max_drawdown_pct??$('maxDrawdownPct')?.value??18)),
      buy_threshold:strategyParamNumber(row.querySelector('[data-param="buy_threshold"]'),Number(current.buy_threshold??62)),
      sell_threshold:strategyParamNumber(row.querySelector('[data-param="sell_threshold"]'),Number(current.sell_threshold??45))
    };
  });
  return out;
}
function renderScoreDimensions(cfg){
  const box=$('dimensionStrip');if(!box)return;
  const dims=cfg?.integrated_score_dimensions||[
    {label:'技术面',weight:.30,examples:['均线','MACD','量价']},
    {label:'基本面',weight:.22,examples:['PE/PB','ROE','现金流']},
    {label:'信息面',weight:.20,examples:['公告','财报','新闻']},
    {label:'资金面',weight:.16,examples:['成交额','量比','盘口']},
    {label:'大盘情绪',weight:.12,examples:['上证','创业板','宽基']}
  ];
  box.innerHTML=dims.map(d=>`<div><b>${esc(d.label||d.key)}</b>权重 ${esc(d.weight??'--')}<br>${esc((d.examples||[]).slice(0,3).join(' / '))}</div>`).join('');
}
function renderStrategyParamEditor(cfg){
  const body=$('strategyParamRows');if(!body)return;
  const matrix=cfg?.strategy_matrix||[];
  const byKey={};
  matrix.forEach(x=>{if(x?.strategy)byKey[String(x.strategy)]=x});
  const params=cfg?.strategy_parameters||{};
  const combo=strategyCombo();
  if(!combo.length){body.innerHTML='<tr><td colspan="9" class="muted">请先选择策略组合</td></tr>';return}
  body.innerHTML=combo.map(key=>{
    const row={...(params[key]||{}),...(byKey[key]||{})};
    const label=strategyLabel(key,cfg);
    const sizing=row.position_sizing||row.position_control||$('positionSizing')?.value||'score_weighted';
    const enabled=row.enabled!==false;
    const opt=v=>`<option value="${v}" ${sizing===v?'selected':''}>${v}</option>`;
    return `<tr data-strategy-row="${esc(key)}">
      <td><span class="strategy-name">${esc(label)}</span><span class="strategy-note">${esc(key)} · ${esc(row.category||'custom')}</span></td>
      <td><input type="checkbox" data-param="enabled" ${enabled?'checked':''}></td>
      <td><select data-param="position_sizing">${['score_weighted','atr_risk','volatility_target','fixed_weight','core_satellite','cash_first_defensive'].map(opt).join('')}</select></td>
      <td><input data-param="max_single_position_pct" type="number" step="0.5" value="${esc(row.max_single_position_pct??$('maxSinglePositionPct')?.value??20)}"></td>
      <td><input data-param="stop_loss_pct" type="number" step="0.5" value="${esc(row.stop_loss_pct??$('stopLossPct')?.value??8)}"></td>
      <td><input data-param="take_profit_pct" type="number" step="0.5" value="${esc(row.take_profit_pct??$('takeProfitPct')?.value??18)}"></td>
      <td><input data-param="max_strategy_drawdown_pct" type="number" step="0.5" value="${esc(row.max_strategy_drawdown_pct??row.max_drawdown_pct??$('maxDrawdownPct')?.value??18)}"></td>
      <td><input data-param="buy_threshold" type="number" step="0.5" value="${esc(row.buy_threshold??62)}"></td>
      <td><input data-param="sell_threshold" type="number" step="0.5" value="${esc(row.sell_threshold??45)}"></td>
    </tr>`;
  }).join('');
}
function strategyNameMap(cfg){
  const out={};
  (cfg?.strategy_catalog||[]).forEach(x=>{if(x?.key)out[String(x.key)]=String(x.name||x.key)});
  return out;
}
function strategyLabel(key,cfg){
  const builtins={
    score_driven:'日常评分驱动',
    low_position:'低位修复',
    avoid_chasing_high:'高位追高过滤',
    ma_repair:'均线修复',
    macd_cross:'MACD金叉/多头',
    volume_breakout:'温和放量',
    atr_risk:'ATR波动过滤',
    position_risk:'仓位与止损',
    risk_control:'风险扣分',
    event_driven:'事件驱动',
    finance_quality:'财务质量',
    market_regime:'大盘情绪过滤'
  };
  const map=strategyNameMap(cfg||lastAutoConfig);
  return map[key]||builtins[key]||key;
}
function renderStrategySelectionSummary(cfg){
  const box=$('strategySelectedSummary');
  if(!box)return;
  const combo=strategyCombo();
  const text=combo.length?combo.map(k=>strategyLabel(k,cfg)).join('、'):'尚未选择策略';
  const risk=cfg?.risk_controls||collectAutoConfig().risk_controls||{};
  box.innerHTML=`<b>当前组合：</b>${esc(text)}<br><b>风控：</b>止损 ${esc(risk.stop_loss_pct??'--')}% · 止盈 ${esc(risk.take_profit_pct??'--')}% · 单票上限 ${esc(risk.max_single_position_pct??'--')}% · 最大回撤 ${esc(risk.max_drawdown_pct??'--')}%`;
}
function currentComboSet(){return new Set(strategyCombo())}
function setComboFromList(list){
  const unique=[...new Set((list||[]).map(x=>String(x||'').trim()).filter(Boolean))];
  $('strategyCombo').value=unique.join(', ');
  if(lastAutoConfig)renderStrategyCatalog(lastAutoConfig);
  renderStrategySelectionSummary(lastAutoConfig);
  renderStrategyParamEditor(lastAutoConfig||{});
}
function renderStrategyCatalog(cfg){
  const box=$('strategyCatalog'),hint=$('strategyCatalogHint');
  if(!box)return;
  const catalog=cfg?.strategy_catalog||[];
  const selected=currentComboSet();
  if(hint)hint.textContent=`已选 ${selected.size} 项 / 可用 ${catalog.length} 项`;
  renderStrategySelectionSummary(cfg);
  renderScoreDimensions(cfg);
  renderStrategyParamEditor(cfg);
  if(!catalog.length){box.innerHTML='<div class="muted">策略目录暂未返回，仍可手动输入策略 key。</div>';return}
  box.innerHTML=catalog.map(item=>{
    const key=String(item.key||'');
    const on=selected.has(key);
    const name=esc(item.name||key);
    const category=esc(item.category||'custom');
    const desc=esc(item.description||item.beginner_note||'');
    return `<label class="strategy-chip ${on?'on':''}" title="${desc}"><input type="checkbox" data-strategy-key="${esc(key)}" ${on?'checked':''} onchange="toggleStrategyFromCatalog(this)"><span><b>${name}</b><span>${category} · ${desc}</span></span></label>`;
  }).join('');
}
function toggleStrategyFromCatalog(el){
  const key=el.dataset.strategyKey;
  const set=currentComboSet();
  if(el.checked)set.add(key);else set.delete(key);
  setComboFromList([...set]);
}
function selectBeginnerPreset(key){
  const preset=lastAutoConfig?.beginner_presets?.[key];
  if(!preset){$('auditLog').textContent='预设尚未加载，请先刷新状态或点击一键配置。';return}
  document.querySelectorAll('.preset').forEach(x=>x.classList.remove('active'));
  const btn=[...document.querySelectorAll('.preset')].find(x=>String(x.getAttribute('onclick')||'').includes(key));
  if(btn)btn.classList.add('active');
  if(preset.strategy_family)$('strategy').value=preset.strategy_family;
  if(preset.position_sizing)$('positionSizing').value=preset.position_sizing;
  setComboFromList(preset.strategy_combo||[]);
  const r=preset.risk_controls||{};
  if(r.stop_loss_pct!=null)$('stopLossPct').value=r.stop_loss_pct;
  if(r.take_profit_pct!=null)$('takeProfitPct').value=r.take_profit_pct;
  if(r.max_drawdown_pct!=null)$('maxDrawdownPct').value=r.max_drawdown_pct;
  if(r.max_single_position_pct!=null)$('maxSinglePositionPct').value=r.max_single_position_pct;
  if(r.max_total_position_pct!=null)$('maxTotalPositionPct').value=r.max_total_position_pct;
  if(r.min_cash_pct!=null)$('minCashPct').value=r.min_cash_pct;
  $('auditLog').textContent=`已套用预设：${preset.label||key}\n${preset.description||''}`;
}
function collectAutoConfig(){
  return {
    symbols:symbols(),
    strategy_family:$('strategy').value,
    strategy_combo:strategyCombo(),
    position_sizing:$('positionSizing').value,
    strategy_parameters:parseStrategyParams(),
    interval_seconds:Number($('interval').value||15),
    initial_cash:num('initialCash',100000),
    reset_account:checked('resetAccount'),
    risk_controls:{
      stop_loss_pct:num('stopLossPct',8),
      take_profit_pct:num('takeProfitPct',18),
      max_drawdown_pct:num('maxDrawdownPct',18),
      max_single_position_pct:num('maxSinglePositionPct',20),
      max_total_position_pct:num('maxTotalPositionPct',80),
      min_cash_pct:num('minCashPct',15),
      max_daily_loss_pct:4,
      atr_risk_pct:1.5,
      cooldown_days:2
    },
    score_weights:{technical:.30,fundamental:.22,information:.20,fund_flow:.16,market_regime:.12},
    event_watch:{
      financial_reports:checked('watchFinancialReports'),
      half_year_reports:checked('watchHalfYearReports'),
      earnings_preannouncements:checked('watchFinancialReports'),
      exchange_announcements:checked('watchAnnouncements'),
      major_negative_news:checked('watchMajorNews'),
      policy_industry_news:checked('watchPolicyNews'),
      event_lookahead_days:21,
      blackout_before_days:2,
      blackout_after_days:1
    },
    data_requirements:{
      require_fresh_quote:checked('requireFreshQuote'),
      block_stale_buy:checked('requireFreshQuote'),
      require_score_provenance:true,
      require_info_snapshot:false,
      require_orderbook_when_available:true
    },
    source_page:'auto-trading'
  };
}
function applyAutoConfig(cfg){
  if(!cfg)return;
  lastAutoConfig=cfg;
  if((cfg.symbols||[]).length)$('symbols').value=(cfg.symbols||[]).join(', ');
  if(cfg.strategy_family)$('strategy').value=cfg.strategy_family;
  if(cfg.interval_seconds!=null)$('interval').value=String(cfg.interval_seconds);
  if((cfg.strategy_combo||[]).length)$('strategyCombo').value=(cfg.strategy_combo||[]).join(', ');
  if(cfg.strategy_parameters)$('strategyParamJson').value=JSON.stringify(cfg.strategy_parameters,null,2);
  if(cfg.position_sizing)$('positionSizing').value=cfg.position_sizing;
  const r=cfg.risk_controls||{};
  if(r.stop_loss_pct!=null)$('stopLossPct').value=r.stop_loss_pct;
  if(r.take_profit_pct!=null)$('takeProfitPct').value=r.take_profit_pct;
  if(r.max_drawdown_pct!=null)$('maxDrawdownPct').value=r.max_drawdown_pct;
  if(r.max_single_position_pct!=null)$('maxSinglePositionPct').value=r.max_single_position_pct;
  if(r.max_total_position_pct!=null)$('maxTotalPositionPct').value=r.max_total_position_pct;
  if(r.min_cash_pct!=null)$('minCashPct').value=r.min_cash_pct;
  if(cfg.initial_cash!=null)$('initialCash').value=cfg.initial_cash;
  const e=cfg.event_watch||{};
  if(e.financial_reports!=null)$('watchFinancialReports').checked=!!e.financial_reports;
  if(e.half_year_reports!=null)$('watchHalfYearReports').checked=!!e.half_year_reports;
  if(e.exchange_announcements!=null)$('watchAnnouncements').checked=!!e.exchange_announcements;
  if(e.major_negative_news!=null)$('watchMajorNews').checked=!!e.major_negative_news;
  if(e.policy_industry_news!=null)$('watchPolicyNews').checked=!!e.policy_industry_news;
  const d=cfg.data_requirements||{};
  if(d.require_fresh_quote!=null)$('requireFreshQuote').checked=!!d.require_fresh_quote;
  if(cfg.reset_account!=null && $('resetAccount'))$('resetAccount').checked=!!cfg.reset_account;
  renderStrategyCatalog(cfg);
  renderStrategySelectionSummary(cfg);
  renderScoreDimensions(cfg);
  renderStrategyParamEditor(cfg);
}
function setText(id,value){const el=$(id);if(el)el.textContent=value}
function updateWorkflowStatus(state={}){
  const cfg=state.cfg||lastAutoConfig||{};
  const risk=cfg.risk_controls||{};
  const combo=(cfg.strategy_combo||strategyCombo()).filter(Boolean);
  const cfgSymbols=(cfg.symbols||symbols()).filter(Boolean);
  const event=cfg.event_watch||{};
  const eventOn=Object.values(event).some(v=>v===true);
  setText('wfSymbols',cfgSymbols.length?cfgSymbols.slice(0,4).join(', '):'--');
  setText('wfCombo',combo.length?combo.slice(0,3).map(k=>strategyLabel(k,cfg)).join('/'):($('strategy')?.value||'--'));
  setText('wfSizing',`${cfg.position_sizing||$('positionSizing')?.value||'--'} · ${risk.stop_loss_pct??$('stopLossPct')?.value??'--'}%`);
  setText('wfEvents',eventOn?'开启':'关闭');
  const sessions=state.sessions||[];
  const active=sessions.find(x=>['running','paused'].includes(x.status))||sessions[0]||null;
  setText('wfSession',active?`${active.status||'--'} ${sessionIdOf(active).slice(-6)}`:'--');
  setText('wfRecords',String((state.records||[]).length||0));
  const queue=state.queue||{};
  setText('wfConfirm',String(queue.count??(queue.data||[]).length??0));
  const tables=Object.keys((state.data||{}).trading_store?.tables||{}).length;
  setText('wfData',tables?`${tables}表`:'待检查');
  const broker=state.broker||{};
  const brokerStatus=broker.broker?.status||broker.status||'disabled';
  setText('wfBroker',brokerStatus);
  setText('wfLive',broker.safety?.LIVE_TRADING_ENABLED?'开启':'关闭');
  const gates=state.readiness?.gates||[];
  const blocked=gates.filter(g=>!g.ok).length;
  setText('wfRisk',blocked?`${blocked}项待处理`:'通过');
  setText('wfKill',broker.safety?.LIVE_KILL_SWITCH?'已开启':'关闭');
}
function renderConfigSummary(cfg, readiness){
  const gates=readiness?.gates||[];
  const gateText=gates.slice(0,6).map(g=>`${g.ok?'✓':'!'} ${g.label}`).join(' · ');
  const source=cfg?.symbols_source||'--';
  const symbols=(cfg?.symbols||[]).slice(0,8).join(', ')||'--';
  const combo=(cfg?.strategy_combo||[]).slice(0,6).map(k=>strategyLabel(k,cfg)).join('、')||'--';
  const events=(cfg?.key_event_watchlist||[]).filter(x=>x.enabled).slice(0,4).map(x=>x.label).join('、')||'未开启';
  const signalCount=Object.keys(cfg?.screener_signal_map||{}).length;
  $('configSummary').innerHTML=`<b>自动交易配置</b>：股票池 ${symbols}；来源 ${esc(source)}；策略 ${esc(combo)}；仓位 ${esc(cfg?.position_sizing||'--')}；筛选信号画像 ${signalCount} 只；止损/止盈/回撤 ${esc(cfg?.risk_controls?.stop_loss_pct??'--')}% / ${esc(cfg?.risk_controls?.take_profit_pct??'--')}% / ${esc(cfg?.risk_controls?.max_drawdown_pct??'--')}%；关键事件 ${esc(events)}。<br>${esc(gateText||'等待 readiness 检查')}`;
  renderStrategySelectionSummary(cfg);
  updateWorkflowStatus({cfg,readiness});
}
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
    const [broker,sessions,records,data,queue,score,autoConfig,readiness]=await Promise.all([
      api('/api/live-broker/status'),
      api('/api/realtime-paper/sessions'),
      api('/api/trading-records?limit=30'),
      api('/api/data-center/status'),
      api('/api/live/confirm-queue'),
      api('/api/score/latest/300750'),
      api('/api/auto-trading/config'),
      api('/api/auto-trading/readiness')
    ]);
    applyAutoConfig(autoConfig.data);
    renderConfigSummary(autoConfig.data,readiness);
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
    updateWorkflowStatus({cfg:autoConfig.data,broker,sessions:sessList,records:rows,data,queue,readiness});
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
    $('auditLog').textContent='最后刷新 '+new Date().toLocaleTimeString()+'\\n'+JSON.stringify({broker:broker.safety,auto_trading_config:autoConfig.data,readiness:readiness.gates,active_session:activeSessionId,sessions:sessList.length,records:rows.length},null,2);
  }catch(e){$('auditLog').textContent='刷新失败：'+e}
}
async function oneClickConfig(){
  const body=collectAutoConfig();
  const js=await api('/api/auto-trading/config/one-click',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  applyAutoConfig(js.data);
  renderConfigSummary(js.data,js.readiness);
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function saveAutoConfig(){
  const js=await api('/api/auto-trading/config',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(collectAutoConfig())});
  applyAutoConfig(js.data);
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function loadLatestScreenerConfig(){
  const body=collectAutoConfig();
  delete body.symbols;
  body.use_latest_screener=true;
  const js=await api('/api/auto-trading/config/one-click',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  applyAutoConfig(js.data);
  renderConfigSummary(js.data,js.readiness);
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function startPaper(){
  const body=collectAutoConfig();
  const js=await api('/api/auto-trading/start-paper',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  activeSessionId=sessionIdOf(js.session)||activeSessionId;
  $('auditLog').textContent=JSON.stringify(js,null,2);
  openWorkspaceKey('realtime','实时模拟');
  refreshAll();
}
async function manualTick(){
  if(!activeSessionId){$('auditLog').textContent='请先启动或恢复一个实时模拟 session。';return}
  const sym=symbols()[0]||'300750';
  const cfg=collectAutoConfig();
  const js=await api('/api/realtime-paper/tick',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({session_id:activeSessionId,symbol:sym,manual_replay:true,quote_hydrate_request:true,source_page:'auto-trading',...cfg})});
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
async function runConfigBacktest(){
  const cfg=collectAutoConfig();
  const sym=(cfg.symbols||[])[0]||'300750';
  const js=await api('/api/backtest/v323/run',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbol:sym,symbols:[sym],limit:520,use_auto_config:true,auto_trading_config:cfg,source_page:'auto-trading'})});
  $('auditLog').textContent=JSON.stringify(js,null,2);
  const url='/backtest?symbol='+encodeURIComponent(sym)+(js.run_id?'&run_id='+encodeURIComponent(js.run_id):'');
  openWorkspaceModule(url,'历史回测结果',workspaceTabForUrl('/backtest'));
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
initWorkspaceFrame();
refreshAll();
</script>
</body>
</html>"""
