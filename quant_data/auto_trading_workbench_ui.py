from __future__ import annotations


def build_auto_trading_workbench_ui() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V3.25 自动交易总控台</title>
<style>
:root{
  --bg:#07111f;--panel:#101a2c;--panel2:#152238;--line:#263955;--text:#e6f0ff;--muted:#92a6c4;
  --blue:#3b82f6;--cyan:#22d3ee;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;
  --shadow:0 22px 60px rgba(0,0,0,.32)
}
*{box-sizing:border-box}html,body{min-height:100%;margin:0}body{background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}button,input,select,textarea{font:inherit}a{color:inherit;text-decoration:none}
.app{display:grid;grid-template-columns:268px minmax(0,1fr);min-height:100vh;max-width:100vw;overflow-x:hidden}.app>section{min-width:0;max-width:100%;overflow:hidden}
.side{background:#0b1424;border-right:1px solid var(--line);display:flex;flex-direction:column;min-width:0}
.brand{height:74px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid var(--line);font-weight:900;color:#bfdbfe}
.logo{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--cyan),var(--blue));display:grid;place-items:center;color:#00121f;font-weight:1000}
.brand small{display:block;color:var(--muted);font-weight:700;margin-top:2px}
.nav{padding:12px}.nav button,.nav a{width:100%;border:1px solid transparent;background:transparent;color:#bfd2f0;text-align:left;border-radius:12px;padding:11px 12px;margin:3px 0;display:flex;align-items:center;gap:10px;font-weight:900;cursor:pointer}
.nav button:hover,.nav a:hover,.nav button.active{background:#12213a;border-color:#315077;color:#fff}.nav b{width:24px;height:24px;border-radius:8px;background:#1b2b46;display:grid;place-items:center;color:#8bdcf4;flex:0 0 auto}
.side-foot{margin-top:auto;border-top:1px solid var(--line);padding:14px 18px;color:var(--muted);font-size:12px;line-height:1.65}
.top{height:66px;background:#0b1424;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;padding:0 20px;position:sticky;top:0;z-index:8}
.top h1{font-size:20px;margin:0;color:#dbeafe}.top .grow{flex:1}.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #315077;background:#13233b;color:#cfe1ff;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:900;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pill.good{border-color:#14532d;background:#0d2b1c;color:#86efac}.pill.warn{border-color:#854d0e;background:#2a1c08;color:#fcd34d}.pill.bad{border-color:#7f1d1d;background:#2a1116;color:#fecaca}.ok{color:#86efac}.bad{color:#fecaca}.warn{color:#fcd34d}
.btn{border:0;border-radius:10px;padding:9px 12px;background:#253755;color:#e5efff;font-weight:900;cursor:pointer;white-space:nowrap}.btn:hover{filter:brightness(1.1)}.btn:disabled{opacity:.55;cursor:wait;filter:none}.btn.primary{background:var(--blue);color:#fff}.btn.green{background:#16a34a;color:#fff}.btn.red{background:#991b1b;color:#fff}.btn.ghost{background:#111c31;border:1px solid var(--line)}
.action-toast{position:fixed;right:22px;bottom:22px;z-index:90;max-width:min(420px,calc(100vw - 44px));padding:11px 14px;border:1px solid #315077;border-radius:10px;background:#10233a;color:#dbeafe;box-shadow:var(--shadow);opacity:0;transform:translateY(14px);pointer-events:none;transition:.18s}.action-toast.show{opacity:1;transform:translateY(0)}.action-toast.good{border-color:#166534;color:#bbf7d0}.action-toast.bad{border-color:#991b1b;color:#fecaca}
.main{padding:18px 22px 30px;min-width:0;max-width:100%;overflow-x:hidden}.hero{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(340px,.9fr);gap:14px;margin-bottom:14px;min-width:0;max-width:100%;align-items:start}.hero>.panel{align-self:start}.hero>.panel:nth-child(2)>.panel-b{max-height:248px;overflow:auto;scrollbar-gutter:stable}.panel,.card,.module{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);min-width:0;max-width:100%}.panel{overflow:hidden}.panel-h{min-height:46px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 14px;background:#121e33;border-bottom:1px solid var(--line);font-weight:1000;min-width:0}.panel-h>.row{min-width:0}.panel-b{padding:14px;min-width:0;max-width:100%}.muted{color:var(--muted)}.notice{border:1px solid #315077;background:#0d1728;border-radius:12px;padding:11px 12px;color:#c9d8ee;font-size:13px;line-height:1.65;overflow-wrap:anywhere}
.kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-bottom:14px}.card{padding:13px}.card span{display:block;color:var(--muted);font-size:12px}.card b{display:block;font-size:22px;margin-top:8px;overflow-wrap:anywhere}.card small{display:block;color:var(--muted);margin-top:5px;line-height:1.35}
.flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.flow .step{background:#0f1b2e;border:1px solid var(--line);border-radius:14px;padding:12px;min-width:0}.step strong{display:flex;align-items:center;gap:8px;margin-bottom:6px}.step i{font-style:normal;width:24px;height:24px;border-radius:99px;background:#123a4a;color:#67e8f9;display:grid;place-items:center}.step p{margin:0;color:var(--muted);font-size:12px;line-height:1.55;overflow-wrap:anywhere}.step .row{margin-top:9px}
.grid-main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:start}.grid-main>.stack{display:grid;gap:14px;align-content:start;min-width:0}.grid-main .panel{align-self:start}.stack{display:grid;gap:14px}.row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.split{display:grid;grid-template-columns:1fr 1fr;gap:10px}.field{display:grid;gap:6px;margin-bottom:10px}.field label{font-size:12px;font-weight:900;color:#9db4d4}.field input,.field select,.field textarea{width:100%;background:#0d1728;border:1px solid #2f4364;border-radius:10px;color:#e5efff;padding:9px 10px;outline:none;min-width:0}.field textarea{min-height:74px;resize:vertical;line-height:1.45}.field textarea.compact{min-height:48px}.check-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.check{display:flex;gap:8px;align-items:flex-start;background:#0d1728;border:1px solid #2f4364;border-radius:10px;padding:8px;color:#c8d8ee;font-size:12px;line-height:1.45}.check input{width:auto;margin-top:2px}
.quick-config{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;border:1px solid #315077;background:#0b1728;border-radius:12px;padding:11px 12px}.quick-config b{display:block;margin-bottom:4px}.quick-config span{display:block;color:var(--muted);font-size:12px;line-height:1.5;overflow-wrap:anywhere}.quick-config .row{justify-content:flex-end}.home-config-details{margin-top:10px;border:1px solid #2f4364;border-radius:12px;background:#0b1628}.home-config-details>summary{cursor:pointer;padding:10px 12px;color:#bfdbfe;font-weight:900}.home-config-body{padding:0 12px 12px}
.module-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.module{display:block;background:#0d1728;padding:12px;cursor:pointer}.module:hover{border-color:#4b8cf7;background:#12213a}.module b{display:block;margin-bottom:5px}.module span{display:block;color:var(--muted);font-size:12px;line-height:1.45;overflow-wrap:anywhere}
.strategy-catalog{display:grid;grid-template-columns:1fr;gap:7px;max-height:226px;overflow:auto;padding-right:3px}.strategy-chip{display:grid;grid-template-columns:auto 1fr;gap:8px;border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:8px;cursor:pointer}.strategy-chip input{margin-top:3px}.strategy-chip b{display:block;font-size:13px}.strategy-chip span{display:block;color:var(--muted);font-size:11px;line-height:1.35;margin-top:2px}.strategy-chip.on{border-color:#22d3ee;background:#092536}
.strategy-param-wrap{max-height:250px;overflow:auto;border:1px solid #2f4364;border-radius:12px}.strategy-param{width:100%;border-collapse:collapse;min-width:820px;font-size:12px}.strategy-param th,.strategy-param td{border-bottom:1px solid #243653;padding:7px;text-align:left;vertical-align:middle}.strategy-param th{position:sticky;top:0;background:#12213a;color:#9fd4ff;z-index:1}.strategy-param input,.strategy-param select{background:#0d1728;border:1px solid #2f4364;color:#e5efff;border-radius:8px;padding:6px;width:100%}
.advanced-box{border:1px solid #2f4364;border-radius:12px;background:#0b1628;margin:10px 0}.advanced-box>summary{cursor:pointer;padding:10px 12px;color:#bfdbfe;font-weight:900}.advanced-box>.advanced-body{padding:0 10px 10px}.score-explain{margin-top:12px;border:1px solid #315077;border-radius:12px;background:#0b1628}.score-explain>summary{cursor:pointer;padding:10px 12px;font-weight:900;color:#bfdbfe}.score-explain-body{padding:0 12px 12px;display:grid;gap:7px}.score-contribution{display:grid;grid-template-columns:minmax(78px,1fr) auto;gap:8px;border-bottom:1px solid #213552;padding:6px 0;font-size:12px}.score-contribution:last-child{border-bottom:0}.score-contribution small{color:var(--muted);overflow-wrap:anywhere}.score-total{border-top:1px solid #3b82f6;padding-top:8px;color:#dbeafe}.recommend-box{border:1px solid #166534;background:#092319;border-radius:12px;padding:10px 12px;color:#bbf7d0;font-size:12px;line-height:1.55;margin-bottom:10px;overflow-wrap:anywhere}.event-factor-list,.position-review-list{display:grid;gap:7px;margin-top:9px}.event-factor,.position-review{border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:9px;min-width:0}.event-factor>div,.position-review>div{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.event-factor b,.position-review b{overflow-wrap:anywhere}.event-factor small,.position-review small{display:block;color:var(--muted);line-height:1.45;margin-top:4px;overflow-wrap:anywhere}.event-factor a{display:inline-flex;color:#93c5fd;font-size:11px;margin-top:5px}.factor-up{color:#86efac}.factor-down{color:#fecaca}.review-action{font-size:11px;border:1px solid #315077;border-radius:999px;padding:3px 7px;white-space:nowrap}.review-action.exit{border-color:#7f1d1d;color:#fecaca}.review-action.reduce{border-color:#854d0e;color:#fcd34d}.review-action.hold{border-color:#166534;color:#86efac}
.bars{display:grid;gap:10px}.barline{height:8px;border-radius:99px;background:#1d2d49;overflow:hidden}.barline i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue));width:0%}.feed{display:grid;gap:8px;max-height:360px;overflow:auto}.feed.compact{max-height:220px}.feed-item{border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:9px}.feed-item time{color:#93c5fd;font-size:12px}.feed-item b{display:block;margin:4px 0;line-height:1.35}.feed-item span{display:block;color:var(--muted);font-size:12px;line-height:1.45;overflow-wrap:anywhere}.ticker-wrap{margin-top:10px;border:1px solid #315077;background:#071426;border-radius:12px;overflow:hidden;min-height:42px;display:flex;align-items:center}.ticker-label{flex:0 0 auto;color:#67e8f9;font-weight:1000;font-size:12px;padding:0 10px}.ticker-rail{min-width:0;flex:1;overflow:hidden}.ticker-track{display:flex;gap:22px;white-space:nowrap;animation:globalTicker 46s linear infinite;will-change:transform}.ticker-wrap.paused .ticker-track{animation-play-state:paused}.ticker-item{display:inline-flex;align-items:center;gap:8px;color:#dbeafe;font-size:13px;max-width:560px}.ticker-item b{color:#fcd34d}.ticker-item span{overflow:hidden;text-overflow:ellipsis}.stream-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:10px 0 8px}.stream-list .feed-item{border-left:3px solid #22d3ee}.stream-list .feed-item.jin10{border-left-color:#f97316}.stream-meta{display:flex;gap:8px;flex-wrap:wrap;color:#93c5fd;font-size:12px}.stream-meta i{font-style:normal;color:#fcd34d}.source-strip{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.source-strip span{border:1px solid #2f4364;background:#0b1728;border-radius:999px;padding:5px 8px;color:#b7c9e6;font-size:11px;max-width:100%;overflow-wrap:anywhere}@keyframes globalTicker{from{transform:translateX(0)}to{transform:translateX(-55%)}}.log{background:#0b1220;border:1px solid #2f4364;border-radius:12px;padding:10px;font-family:Consolas,monospace;font-size:12px;color:#b7c9e6;white-space:pre-wrap;overflow:auto;max-height:260px;overflow-wrap:anywhere}
.source-strip a{border:1px solid #2f4364;background:#0b1728;border-radius:999px;padding:5px 8px;color:#93c5fd;font-size:11px;max-width:100%;overflow-wrap:anywhere}.feed-item .impact-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}.impact-tag{border:1px solid #315077;background:#10233a;color:#bfdbfe;border-radius:999px;padding:3px 7px;font-size:11px}.source-link{display:inline-flex!important;width:auto!important;margin-top:7px;color:#93c5fd!important;font-size:12px!important}.feed-item .source-note{color:#fcd34d!important;font-size:11px!important}
.mini-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}.mini-table th,.mini-table td{border-bottom:1px solid #243653;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}.mini-table th{background:#12213a;color:#9fd4ff}
.sector-panel{margin-bottom:14px;min-width:0;max-width:100%}.sector-summary{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;margin-bottom:10px;min-width:0}.sector-rotation{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:0 0 10px}.sector-rotation>div{border:1px solid #29405f;background:#0d1a2e;padding:8px 10px;border-radius:7px;min-width:0}.sector-rotation b,.sector-rotation span{display:block;overflow-wrap:anywhere}.sector-rotation span{color:var(--muted);font-size:11px;line-height:1.45;margin-top:3px}.sector-table-wrap{overflow:auto;max-width:100%;max-height:280px;border:1px solid #2f4364;border-radius:8px}.sector-table{width:100%;border-collapse:collapse;min-width:1800px;font-size:12px}.sector-table th,.sector-table td{padding:9px 10px;border-bottom:1px solid #243653;text-align:right;white-space:nowrap}.sector-table th{position:sticky;top:0;background:#12213a;color:#9fd4ff;z-index:1}.sector-table th:first-child,.sector-table td:first-child,.sector-table th:nth-child(2),.sector-table td:nth-child(2){text-align:left}.sector-name{display:grid;gap:2px}.sector-name small{color:var(--muted)}.sector-stage,.flow-state{display:inline-flex;border:1px solid #315077;border-radius:999px;padding:3px 7px;color:#bfdbfe}.sector-stage.main,.flow-state.in{border-color:#166534;background:#0d2b1c;color:#86efac}.sector-stage.weak,.flow-state.out{border-color:#7f1d1d;background:#2a1116;color:#fecaca}.sector-link{color:#93c5fd}.sector-filter.active{background:#2563eb}.sector-method{color:var(--muted);font-size:11px;line-height:1.5;overflow-wrap:anywhere}@media(max-width:1050px){.sector-rotation{grid-template-columns:repeat(2,minmax(0,1fr))}}
.iframe-shell{position:fixed;top:0;right:0;bottom:0;left:268px;width:calc(100vw - 268px);max-width:none;min-width:0;background:#07111f;z-index:40;display:grid;grid-template-rows:56px minmax(0,1fr);transform:translateX(104%);transition:transform .2s ease;border-left:1px solid var(--line);box-shadow:-20px 0 60px rgba(0,0,0,.45);overflow:hidden}
.iframe-shell.open{transform:translateX(0)}.iframe-head{display:flex;align-items:center;gap:10px;padding:0 14px;background:#0b1424;border-bottom:1px solid var(--line);min-width:0}.iframe-head b{font-size:17px;white-space:nowrap}.iframe-head .grow{flex:1;min-width:0}.iframe-head .pill{max-width:min(52vw,720px)}.workspace-frame{width:100%;height:100%;min-width:0;border:0;background:#07111f;display:block}.iframe-empty{display:grid;place-items:center;color:var(--muted)}
.agent-box{border:1px solid #315077;background:linear-gradient(135deg,#0d1728,#10233a);border-radius:12px;padding:12px;line-height:1.6;font-size:13px}.agent-box b{display:block;color:#dbeafe;margin-bottom:5px}
.agent-decision{margin-top:10px;border:1px solid #2f4364;background:#081626;border-radius:12px;padding:10px;font-size:13px;line-height:1.55;overflow-wrap:anywhere;max-height:270px;overflow:auto}.agent-decision b{display:block;color:#dbeafe;margin-bottom:5px}.agent-decision ul{margin:7px 0 0 18px;padding:0}.agent-decision li{margin:3px 0;color:#c8d8ee}.agent-decision .risk{color:#fcd34d;margin-top:7px}
.agent-evidence-list{display:grid;gap:7px;margin-top:9px}.agent-evidence{border:1px solid #2f4364;background:#0b1728;border-radius:10px;padding:8px}.agent-evidence time{display:block;color:#93c5fd;font-size:11px}.agent-evidence strong{display:block;margin:3px 0;color:#dbeafe}.agent-evidence small{display:block;color:#b7c9e6;line-height:1.45}.agent-evidence a{display:inline-flex;margin-top:6px;color:#93c5fd;font-size:12px}.agent-evidence .impact-row{margin-top:6px}
.source-meta{display:grid;gap:3px;margin-top:6px;color:#b7c9e6;font-size:12px;line-height:1.45}.source-meta a{color:#93c5fd}.source-policy{border:1px solid #315077;background:#081626;border-radius:10px;padding:8px;margin:8px 0;color:#c8d8ee;font-size:12px;line-height:1.55}.impact-summary{border:1px solid #315077;background:#0b1d30;border-radius:10px;padding:7px;margin-top:7px;color:#dbeafe;font-size:12px;line-height:1.5}.impact-summary b{display:inline;color:#bfdbfe;margin:0}.symbol-impact-card{border-left:3px solid #60a5fa}.symbol-impact-card.none{border-left-color:#64748b}.source-link-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:7px}.source-link-row a,.source-link-row span{display:inline-flex!important;border:1px solid #2f4364;background:#0d1728;border-radius:999px;padding:4px 8px;font-size:11px!important;color:#93c5fd!important}.feed-item a.source-link{border:1px solid #2f4364;background:#0d1728;border-radius:999px;padding:4px 8px}.feed-item .impact-summary{margin-top:8px}
@media(max-width:1360px){.app{grid-template-columns:84px 1fr}.brand span,.nav span,.side-foot{display:none}.nav button,.nav a{justify-content:center;padding:12px}.iframe-shell{left:84px;width:calc(100vw - 84px);max-width:none}.hero,.grid-main{grid-template-columns:1fr}.hero>.panel:nth-child(2)>.panel-b{max-height:460px}.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.flow{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:820px){.app{grid-template-columns:1fr}.side{display:none}.iframe-shell{left:0;max-width:100vw}.top{position:static}.hero,.grid-main,.flow,.kpis,.split,.check-grid,.module-grid{grid-template-columns:1fr}.main{padding:14px}.iframe-shell{grid-template-rows:58px 1fr}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand"><div class="logo">Q</div><span>量化网关<br><small>自动交易总控台</small></span></div>
    <nav class="nav" id="moduleNav">
      <button class="active" type="button" onclick="closeWorkspace()"><b>⌂</b><span>首页总览</span></button>
      <button type="button" data-module="screener" onclick="openModule('screener')"><b>筛</b><span>股票筛选</span></button>
      <button type="button" data-module="quote" onclick="openModule('quote')"><b>时</b><span>分时盘口</span></button>
      <button type="button" data-module="detail" onclick="openModule('detail')"><b>K</b><span>K线详情</span></button>
      <button type="button" data-module="backtest" onclick="openModule('backtest')"><b>测</b><span>历史回测</span></button>
      <button type="button" data-module="realtime" onclick="openModule('realtime')"><b>模</b><span>实时模拟</span></button>
      <button type="button" data-module="live" onclick="openModule('live')"><b>实</b><span>真实交易</span></button>
      <button type="button" data-module="records" onclick="openModule('records')"><b>录</b><span>交易记录</span></button>
      <button type="button" data-module="data" onclick="openModule('data')"><b>数</b><span>数据中心</span></button>
      <button type="button" data-module="docs" onclick="openModule('docs')"><b>?</b><span>中文 API</span></button>
    </nav>
    <div class="side-foot">研究辅助，不构成投资建议。真实交易默认关闭，必须券商授权、风控通过、人工确认后才允许进入下单流程。</div>
  </aside>
  <section>
    <header class="top">
      <h1>V3.25 自动交易总控台</h1>
      <span class="pill good">首页总览 + 右侧覆盖模块</span>
      <span class="pill" id="brokerBadge">券商状态读取中...</span>
      <div class="grow"></div>
      <button class="btn ghost" onclick="openModule('quote')">行情</button>
      <button class="btn ghost" onclick="openModule('realtime')">模拟</button>
      <button class="btn red" onclick="killLive(this)">实盘 Kill</button>
      <button class="btn primary" onclick="refreshAll(this)">刷新</button>
    </header>
    <main class="main">
      <section class="hero">
        <div class="panel">
          <div class="panel-h"><span>交易工作流</span><span class="muted">筛选 → 配置 → 回测 → 模拟 → 实盘确认</span></div>
          <div class="panel-b">
            <div class="notice">这个首页只做总览和关键动作。左侧列表点击后，会在右侧覆盖打开原来的页面 iframe；关闭或切换模块时会释放旧 iframe，避免页面越开越慢。所有旧页面入口仍保留。</div>
            <div class="flow" style="margin-top:12px">
              <div class="step"><strong><i>1</i>先筛选</strong><p>股票池、四面评分、风险标签和策略适配是自动交易方向的来源。</p><div class="row"><button class="btn" onclick="openModule('screener')">打开筛选</button></div></div>
              <div class="step"><strong><i>2</i>一键配置</strong><p>从筛选结果生成策略组合、仓位、止损止盈、最大回撤和事件监控。</p><div class="row"><button class="btn green" onclick="oneClickConfig(this)">一键配置</button></div></div>
              <div class="step"><strong><i>3</i>先验证</strong><p>同一套配置先跑回测，再进入实时模拟，不直接上真实账户。</p><div class="row"><button class="btn" onclick="runConfigBacktest(this)">配置回测</button><button class="btn" onclick="startPaper(this)">启动模拟</button></div></div>
              <div class="step"><strong><i>4</i>后实盘</strong><p>QMT/PTrade 默认关闭；真实订单必须预检查、风控、确认队列和 kill switch。</p><div class="row"><button class="btn red" onclick="openModule('live')">实盘确认</button></div></div>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-h"><span>联网智能辅助</span><button class="btn" onclick="loadAgentBrief(true)">联网AI研判</button></div>
          <div class="panel-b">
            <div class="agent-box"><b>用途边界</b>只读取真实可追溯数据源和缓存；没有数据时显示缺失/过期，不生成假新闻。当前用于解释宏观、全球商品、非农/CPI/FOMC 等客观因素可能带来的风险，不直接等于买卖建议。</div>
            <div class="agent-decision" id="agentDecision"><b>智能体结论加载中...</b><span>正在聚合金十快讯、全球宏观事件、评分溯源和实盘安全门控。</span></div>
            <div class="ticker-wrap" id="globalTicker"><div class="ticker-label">7x24 快讯</div><div class="ticker-rail"><div class="ticker-track" id="globalTickerTrack"><span class="ticker-item"><b>等待</b><span>正在读取金十/全球要闻缓存...</span></span></div></div></div>
            <div class="stream-head"><b>全球实时要闻流</b><span class="row"><span class="pill" id="globalStreamStatus">等待加载</span><button class="btn" onclick="loadGlobalStream(true)">联网刷新</button><button class="btn" id="tickerPauseBtn" onclick="toggleGlobalTicker()">暂停轮播</button></span></div>
            <div class="source-strip" id="globalStreamSources"><span>金十直连状态等待中</span></div>
            <div class="feed compact stream-list" id="globalStream"><div class="feed-item"><b>等待加载全球快讯...</b><span>优先使用金十/金十期货、东方财富、华尔街见闻、财联社等真实来源；不可用时显示缺失原因。</span></div></div>
            <div class="stream-head"><b>宏观事件观察</b><span class="muted">非农 / CPI / FOMC / 商品 / 地缘</span></div>
            <div class="feed compact" id="macroFeed"><div class="feed-item"><b>等待加载全球信息面...</b><span>会优先使用缓存，手动联网刷新可能更慢。</span></div></div>
          </div>
        </div>
      </section>

      <section class="panel sector-panel">
        <div class="panel-h">
          <span>主线板块 · 日内资金轮动与近期强度</span>
          <span class="row"><select id="sectorWindow" aria-label="板块资金时间窗口" onchange="setSectorWindow(this.value)"><option value="interval_flow_15m">近15分钟</option><option value="interval_flow_5m">近5分钟</option><option value="interval_flow_30m">近30分钟</option><option value="interval_flow_60m">近60分钟</option><option value="morning_flow_change">上午</option><option value="afternoon_flow_change">下午</option><option value="net_inflow">当日累计</option><option value="recent_flow_5d_sum">近5日</option></select><button class="btn sector-filter active" data-sector-filter="all" onclick="setSectorFilter('all')">主线榜</button><button class="btn sector-filter" data-sector-filter="industry" onclick="setSectorFilter('industry')">行业</button><button class="btn sector-filter" data-sector-filter="concept" onclick="setSectorFilter('concept')">概念</button><button class="btn sector-filter" data-sector-filter="inflow" onclick="setSectorFilter('inflow')">区间流入</button><button class="btn sector-filter" data-sector-filter="outflow" onclick="setSectorFilter('outflow')">区间流出</button><button class="btn sector-filter" data-sector-filter="returning" onclick="setSectorFilter('returning')">正在回流</button><button class="btn sector-filter" data-sector-filter="diverging" onclick="setSectorFilter('diverging')">高位分歧</button><button class="btn" onclick="loadSectorMainline(true)">保存新快照</button></span>
        </div>
        <div class="panel-b">
          <div class="sector-summary"><div><b id="sectorHeadline">板块数据加载中...</b><div class="sector-method" id="sectorMethod">强度综合涨跌幅、公开资金净流、上涨宽度和换手参与度；不是 Level-2 主力账户识别。</div></div><span class="pill" id="sectorStatus">等待来源</span></div>
          <div class="sector-rotation" id="sectorRotation"><div><b>等待日内快照</b><span>至少两个真实快照后计算区间流入流出。</span></div></div>
          <div class="sector-table-wrap"><table class="sector-table"><thead><tr><th>板块</th><th>阶段</th><th>强度</th><th>主线分</th><th>涨跌幅</th><th>当日累计净流</th><th>近5分</th><th>近15分</th><th>近30分</th><th>近60分</th><th>上午变化</th><th>下午变化</th><th>近5日净流</th><th>资金阶段</th><th>流向状态</th><th>资金占比</th><th>上涨/下跌</th><th>上涨宽度</th><th>近期持续</th><th>来源</th></tr></thead><tbody id="sectorRows"><tr><td colspan="20">正在读取真实板块数据...</td></tr></tbody></table></div>
        </div>
      </section>

      <section class="kpis">
        <div class="card"><span>实时模拟 session</span><b id="paperSessions">--</b><small id="activeSessionText">可恢复、可暂停、可审计</small></div>
        <div class="card"><span>统一交易记录</span><b id="recordCount">--</b><small>订单、成交、持仓、标注</small></div>
        <div class="card"><span>数据中心</span><b id="dataHealth">--</b><small>缓存、缺失、过期、来源</small></div>
        <div class="card"><span>真实交易</span><b id="liveEnabled">默认关闭</b><small>确认队列 + kill switch</small></div>
        <div class="card"><span>确认队列</span><b id="confirmCount">--</b><small>批准后才提交券商</small></div>
        <div class="card"><span>当前股票池</span><b id="wfSymbols">--</b><small id="wfCombo">策略加载中</small></div>
      </section>

      <section class="grid-main">
        <div class="stack">
          <div class="panel">
            <div class="panel-h"><span>模块入口</span><span class="muted">右侧覆盖 iframe</span></div>
            <div class="panel-b module-grid" id="moduleCards"></div>
          </div>
          <div class="panel">
            <div class="panel-h"><span>关键状态</span><button class="btn" onclick="refreshAll(this)">刷新状态</button></div>
            <div class="panel-b">
              <table class="mini-table"><tbody id="workflowBody"><tr><td>加载中...</td></tr></tbody></table>
            </div>
          </div>
        </div>

        <div class="stack">
          <div class="panel" id="paperControl">
            <div class="panel-h"><span>一键配置与组合策略</span><span class="muted">策略数量与模拟/回测共用</span></div>
            <div class="panel-b">
              <div class="quick-config">
                <div><b>首页只保留快速配置</b><span>完整股票池、50+ 策略目录、逐项阈值、仓位和事件门控仍在下方折叠区；建议先读取最新筛选，再回测、模拟，最后进入实盘确认。</span></div>
                <div class="row"><button class="btn green" onclick="oneClickConfig(this)">一键配置</button><button class="btn" onclick="loadLatestScreenerConfig(this)">读取筛选</button><button class="btn" onclick="openModule('realtime')">模拟详情</button></div>
              </div>
              <details class="home-config-details">
                <summary>展开完整配置与逐项参数</summary>
                <div class="home-config-body">
              <div class="split">
                <div class="field"><label>股票池</label><textarea id="symbols" oninput="renderWorkflow()">300750, 600438, 510300</textarea></div>
                <div class="field"><label>配置说明</label><div class="notice" id="configSummary">正在读取总控台配置...</div></div>
              </div>
              <div class="split">
                <div class="field"><label>策略族</label><select id="strategy"><option value="hybrid">综合评分</option><option value="etf_momentum_rotation">ETF 动量轮动</option><option value="score_reversal">评分拐点修复</option><option value="core_satellite">核心-卫星</option><option value="event_driven">事件驱动</option></select></div>
                <div class="field"><label>刷新频率</label><select id="interval"><option value="15">15 秒</option><option value="30">30 秒</option><option value="60">60 秒</option><option value="0">仅手动执行</option></select></div>
              </div>
              <div class="row" style="margin-bottom:10px">
                <button class="btn" onclick="selectBeginnerPreset('balanced')">均衡入门</button>
                <button class="btn" onclick="selectBeginnerPreset('defensive')">防守学习</button>
                <button class="btn" onclick="selectBeginnerPreset('swing')">波段观察</button>
                <button class="btn" onclick="selectBeginnerPreset('etf_rotation')">ETF 轮动</button>
                <button class="btn green" onclick="recommendPreset()">按股票池推荐</button>
                <span class="pill" id="strategyCatalogHint">策略目录加载中...</span>
              </div>
              <div id="strategyRecommendation" class="recommend-box">组合原则：选 1 个主策略，配 2-3 个确认因子，再保留风险、数据质量和大盘环境门控；不建议把全部策略同时勾选。</div>
              <div id="strategySelectedSummary" class="notice" style="margin-bottom:10px">已选策略会在这里翻译成中文。</div>
              <details class="advanced-box" id="strategyAdvancedDetails" ontoggle="onStrategyEditorToggle(this)">
                <summary>高级自定义（完整策略目录与逐项参数）</summary>
                <div class="advanced-body">
                  <div class="field"><label>内部策略标识（通常无需手工编辑）</label><textarea class="compact" id="strategyCombo" oninput="renderStrategyCatalog(lastAutoConfig||{})">score_driven, low_position, avoid_chasing_high, ma_repair, macd_cross, volume_breakout, atr_risk, position_risk, risk_control, event_driven, finance_quality, market_regime</textarea></div>
                  <div class="strategy-catalog" id="strategyCatalog"><div class="notice">展开高级自定义后加载完整策略目录。</div></div>
                  <div class="strategy-param-wrap" style="margin-top:10px">
                    <table class="strategy-param">
                      <thead><tr><th>策略</th><th>启用</th><th>仓位模型</th><th>单票%</th><th>止损%</th><th>止盈%</th><th>最大回撤%</th><th>买入分</th><th>卖出分</th></tr></thead>
                      <tbody id="strategyParamRows"><tr><td colspan="9" class="muted">展开高级自定义后加载逐项参数。</td></tr></tbody>
                    </table>
                  </div>
                </div>
              </details>
              <div class="split" style="margin-top:10px">
                <div class="field"><label>仓位模型</label><select id="positionSizing"><option value="score_weighted">评分加权</option><option value="atr_risk">ATR 风险仓位</option><option value="volatility_target">波动率目标</option><option value="fixed_weight">固定权重</option><option value="core_satellite">核心-卫星</option><option value="cash_first_defensive">现金优先防守</option></select></div>
                <div class="field"><label>初始资金</label><input id="initialCash" type="number" value="100000"></div>
              </div>
              <div class="split">
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
                <label class="check"><input id="requireFreshQuote" type="checkbox" checked> 过期数据禁止新增仓位</label>
                <label class="check danger-check"><input id="resetAccount" type="checkbox"> 强制新建模拟账户（清空当前持仓与成交）</label>
              </div>
              <div class="row" style="margin-top:12px">
                <button class="btn green" onclick="oneClickConfig(this)">一键配置</button>
                <button class="btn" onclick="loadLatestScreenerConfig(this)">读取最新筛选</button>
                <button class="btn" onclick="saveAutoConfig(this)">保存配置</button>
                <button class="btn primary" onclick="startPaper(this)">启动模拟</button>
                <button class="btn" onclick="manualTick()">执行一轮</button>
                <button class="btn" onclick="runConfigBacktest(this)">配置回测</button>
              </div>
                </div>
              </details>
            </div>
          </div>
        </div>

        <div class="stack">
          <div class="panel">
            <div class="panel-h"><span>评分与风险</span><span class="muted" id="scoreTime">--</span></div>
            <div class="panel-b">
              <div class="row" style="justify-content:space-between;margin-bottom:10px"><b id="decisionAction" style="font-size:24px">等待评分</b><span class="pill" id="decisionScore">评分 --</span></div>
              <div class="bars">
                <div><div class="row" style="justify-content:space-between"><span>技术面</span><b id="techScore">--</b></div><div class="barline"><i id="techBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>基本面</span><b id="fundScore">--</b></div><div class="barline"><i id="fundBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>信息面</span><b id="infoScore">--</b></div><div class="barline"><i id="infoBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>大盘情绪</span><b id="marketScore">--</b></div><div class="barline"><i id="marketBar"></i></div></div>
              </div>
              <details class="score-explain" open>
                <summary>这个分数怎么来的</summary>
                <div id="scoreExplain" class="score-explain-body"><span class="muted">等待最新实时模拟信号；尚无信号时显示最近一次评分溯源。</span></div>
              </details>
            </div>
          </div>
          <div class="panel">
            <div class="panel-h"><span>模拟账户/持仓</span><div class="row"><button class="btn" onclick="runDuePositionReviews(this)">检查每日复核</button><button class="btn" onclick="reviewPaperPositions(this)">复核全部持仓</button><button class="btn" onclick="openModule('realtime')">详情</button></div></div>
            <div class="panel-b"><div id="paperSchedulerStatus" class="notice">正在读取服务端自动复评状态...</div><div id="reviewScheduleStatus" class="notice" style="margin-top:8px">正在读取每日持仓复核计划...</div><div id="sessionSnapshot" class="notice" style="margin-top:8px">暂无 active session</div><div id="paperPositionReviews" class="position-review-list"><span class="muted">有持仓后可执行每日复核；复核不会绕过实时模拟内核创建订单。</span></div><table class="mini-table" style="margin-top:10px"><tbody id="sessionRows"><tr><td>等待 session...</td></tr></tbody></table></div>
          </div>
          <div class="panel">
            <div class="panel-h"><span>实盘安全</span><div class="row"><button class="btn" onclick="reviewLivePositions(this)">只读持仓复核</button><button class="btn red" onclick="killLive(this)">Kill</button></div></div>
            <div class="panel-b">
              <div class="notice" id="liveSafety">真实交易默认关闭。未配置券商 SDK、环境变量、账号授权时只显示“已关闭/不支持”。</div>
              <div class="notice" style="margin-top:8px">没有 QMT/PTrade SDK 时仍可完成评分、批量预检查、风控和待确认票据；也可连接用户自行授权的本地 HTTP 券商桥。任何真实执行都必须通过服务端确认队列和全部安全门禁。</div>
              <div class="split" style="margin-top:10px"><div class="field"><label>预检查代码</label><input id="liveSymbol" value="300750"></div><div class="field"><label>方向</label><select id="liveSide"><option value="buy">买入</option><option value="sell">卖出</option></select></div></div>
              <div class="split"><div class="field"><label>股数</label><input id="liveQty" type="number" value="100"></div><div class="field"><label>限价</label><input id="livePrice" type="number" value="0"></div></div>
              <div class="row"><button class="btn" onclick="previewOrder()">首只订单预检查</button><button class="btn" onclick="previewOrderBatch()">股票池批量预检查</button><button class="btn" onclick="openModule('live')">进入实盘页</button></div>
              <div class="notice" id="livePreviewSummary" style="margin-top:10px">批量预检查会逐只经过数据新鲜度、评分溯源、白名单、仓位、Kill Switch 和人工确认门控，不会直接下单。</div>
              <div id="livePositionReviews" class="position-review-list"><span class="muted">连接并授权券商后可读取真实持仓；这里仅生成持有、减仓或退出复核建议。</span></div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-h"><span>资金/持仓/流水总览</span><button class="btn" onclick="openModule('records')">完整记录</button></div>
            <div class="panel-b">
              <div id="portfolioOverview" class="notice">正在读取实盘安全账户、模拟账户和统一交易流水...</div>
              <table class="mini-table" style="margin-top:10px">
                <thead><tr><th>来源</th><th>代码</th><th>方向/状态</th><th>价格</th><th>数量</th><th>金额/盈亏</th></tr></thead>
                <tbody id="recordOverviewRows"><tr><td colspan="6">等待交易记录...</td></tr></tbody>
              </table>
            </div>
          </div>
          <div class="panel">
            <div class="panel-h"><span>审计日志</span><span class="muted">最近动作</span></div>
            <div class="panel-b"><div class="log" id="auditLog">Ready.</div></div>
          </div>
        </div>
      </section>
    </main>
  </section>
</div>
<section class="iframe-shell" id="workspaceShell" aria-hidden="true">
  <header class="iframe-head">
    <b id="workspaceTitle">模块页面</b>
    <span class="pill" id="workspaceStatus">未打开</span>
    <div class="grow"></div>
    <button class="btn" onclick="reloadWorkspaceFrame()">刷新 iframe</button>
    <button class="btn" onclick="openWorkspaceInNewWindow()">新窗口</button>
    <button class="btn red" onclick="closeWorkspace()">关闭</button>
  </header>
  <iframe id="workspaceFrame" class="workspace-frame" title="V3.25 自动交易右侧模块 iframe" src="about:blank"></iframe>
</section>
<div class="action-toast" id="actionToast" role="status" aria-live="polite"></div>
<script>
const $=id=>document.getElementById(id);
const MODULES={
  screener:{label:'股票筛选',icon:'筛',url:()=>'/screener',desc:'股票池、四面评分、风险标签、一键加入回测/模拟/实盘观察。'},
  quote:{label:'分时盘口',icon:'时',url:()=>'/ui?symbol='+encodeURIComponent(primarySymbol())+'&frame=time',desc:'分时、五档盘口、盘口观察、资金行为和当日状态。'},
  detail:{label:'K线详情',icon:'K',url:()=>'/detail/'+encodeURIComponent(primarySymbol())+'?frame=1d',desc:'日K/周K/月K、技术因子、异常标注、信息面与资金面。'},
  backtest:{label:'历史回测',icon:'测',url:()=>'/backtest?symbol='+encodeURIComponent(primarySymbol()),desc:'用同一套配置验证收益、回撤、买卖流水和策略跑输原因。'},
  realtime:{label:'实时模拟',icon:'模',url:()=>'/realtime-paper',desc:'真实行情驱动 paper trading，记录订单、成交、持仓、审计和图表 marker。'},
  live:{label:'真实交易',icon:'实',url:()=>'/live-trading',desc:'QMT、PTrade、本地 HTTP 券商桥、确认队列和紧急停止。'},
  records:{label:'交易记录',icon:'录',url:()=>'/trading-records',desc:'回测、模拟、真实交易统一流水。'},
  data:{label:'数据中心',icon:'数',url:()=>'/data-center',desc:'缓存、缺失字段、数据源错误、券商状态。'},
  docs:{label:'中文 API',icon:'?',url:()=>'/docs-cn',desc:'中文接口说明和调试入口。'}
};
MODULES.quote.url=()=>'/ui?symbol='+encodeURIComponent(primarySymbol())+'&frame=time&embedded=1';
MODULES.detail.url=()=>'/detail/'+encodeURIComponent(primarySymbol())+'?frame=1d&embedded=1';
let lastAutoConfig=null;
let activeSessionId='';
let currentModule='';
let sectorMainlineData=null,sectorFilter='all',sectorWindow='interval_flow_15m';
let currentWorkspaceUrl='about:blank';
let latestPaperPortfolio=null;
let latestPortfolioInputs={liveAccount:null,livePositions:null,records:null};
let globalStreamTimer=null;
let globalStreamPromise=null;
let workbenchRefreshPromise=null;
let globalTickerPaused=false;
let globalStreamRefreshMs=20000;
let strategyEditorHydrated=false;
let deferredStrategyConfig=null;
function arrangeDashboardPanels(){
  const grid=document.querySelector('.grid-main');
  if(!grid||grid.dataset.arranged==='1')return;
  const panels=[...grid.querySelectorAll(':scope > .stack > .panel')];
  if(panels.length<8)return;
  const columns=[[6,0],[3,1,2],[4,5,7]].map(indexes=>{
    const column=document.createElement('div');
    column.className='stack';
    indexes.forEach(index=>panels[index]&&column.appendChild(panels[index]));
    return column;
  });
  grid.replaceChildren(...columns);
  grid.dataset.arranged='1';
}
async function api(url,opt={}){const r=await fetch(url,{cache:'no-store',...opt});let data;try{data=await r.json()}catch(e){throw new Error(`接口 ${url} 返回的不是 JSON`)}if(!r.ok)throw new Error(data?.message||data?.reason||`HTTP ${r.status}`);return data}
let actionToastTimer=null;
function showActionToast(message,type='good'){
  const box=$('actionToast');if(!box)return;
  box.textContent=String(message||'操作完成');box.className='action-toast show '+type;
  clearTimeout(actionToastTimer);actionToastTimer=setTimeout(()=>box.classList.remove('show'),2600);
}
async function withAction(btn,pending,done,task){
  const old=btn?.textContent;if(btn){btn.disabled=true;btn.textContent=pending}
  try{const value=await task();if(value?.ok===false)throw new Error(value.message||value.reason||'操作未完成');showActionToast(done,'good');return value}
  catch(e){showActionToast('操作失败：'+e,'bad');throw e}
  finally{if(btn){btn.disabled=false;btn.textContent=old}}
}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function splitListText(v){return String(v||'').split(/[\\s,，;；、]+/).map(s=>s.trim()).filter(Boolean)}
function symbols(){return splitListText($('symbols')?.value)}
function strategyCombo(){return splitListText($('strategyCombo')?.value)}
function primarySymbol(){return (symbols()[0]||$('liveSymbol')?.value||'300750').trim()||'300750'}
function num(id,fallback){const n=Number($(id)?.value);return Number.isFinite(n)?n:fallback}
function checked(id){return !!$(id)?.checked}
function money(v){const n=Number(v);return Number.isFinite(n)?n.toLocaleString('zh-CN',{maximumFractionDigits:2}):'--'}
function pct(v){const n=Number(v);return Number.isFinite(n)?n.toFixed(2)+'%':'--'}
function pnlClass(v){const n=Number(v);return n>0?'ok':n<0?'bad':''}
function cnEnum(v){
  const raw=String(v??'').trim();
  const map={macro:'宏观市场',fund_flow:'资金流',sector:'板块强度',earnings:'财报业绩',ipo:'IPO上市',global:'全球市场',market:'市场环境',company_event:'公司事件',market_macro:'宏观市场',news:'新闻资讯',announcement:'公司公告',policy:'政策信息',research:'研究信息',positive:'偏利好',negative:'偏利空',neutral:'中性',no_direct_mapping:'暂无直接映射',mapping_error:'映射失败',connected:'已连接',disconnected:'未连接',disabled:'已关闭',unsupported:'不支持',blocked:'已阻断',qmt:'迅投 QMT',ptrade:'PTrade',http_bridge:'本地 HTTP 券商桥',simulator:'本地模拟器',running:'运行中',paused:'已暂停',stopped:'已停止',buy:'买入',sell:'卖出',hold:'观察',add:'加仓',reduce:'减仓',avoid:'回避',needs_confirmation:'待人工确认',score_weighted:'评分加权',atr_risk:'波动风险仓位',volatility_target:'波动率目标',fixed_weight:'固定权重',core_satellite:'核心-卫星',cash_first_defensive:'现金优先防守',equal_risk_contribution:'等风险分配',hybrid:'综合评分',etf_momentum_rotation:'ETF动量轮动',score_reversal:'评分拐点修复',event_driven:'事件驱动'};
  return map[raw]||raw;
}
function cnAction(v){return cnEnum(v)||'观察'}
function sizingLabel(v){return cnEnum(v)||'未设置'}
function setText(id,value){const el=$(id);if(el)el.textContent=value}
function setScore(id,val){const n=Number(val);const ok=Number.isFinite(n);setText(id+'Score',ok?n.toFixed(1):'--');const bar=$(id+'Bar');if(bar)bar.style.width=(ok?Math.max(0,Math.min(100,n)):0)+'%'}
function sessionIdOf(item){return item?.session_id||item?.id||item?.sessionId||''}
function renderModuleCards(){
  const box=$('moduleCards');
  box.innerHTML=Object.entries(MODULES).map(([key,m])=>`<a class="module" href="${esc(m.url())}" onclick="openModule('${key}');return false"><b>${esc(m.label)}</b><span>${esc(m.desc)}</span></a>`).join('');
}
arrangeDashboardPanels();
function markNav(key){
  document.querySelectorAll('#moduleNav button').forEach(btn=>btn.classList.toggle('active',btn.dataset.module===key || (!key && !btn.dataset.module)));
}
function openModule(key,urlOverride){
  const mod=MODULES[key]||MODULES.screener;
  let url=urlOverride||mod.url();
  if((key==='quote'||key==='detail')&&!/[?&]embedded=1\\b/.test(url)){
    url+=url.includes('?')?'&embedded=1':'?embedded=1';
  }
  const frame=$('workspaceFrame');
  if(currentModule && currentModule!==key)frame.src='about:blank';
  currentModule=key;
  currentWorkspaceUrl=url;
  $('workspaceTitle').textContent=mod.label;
  $('workspaceStatus').textContent=url;
  $('workspaceShell').classList.add('open');
  $('workspaceShell').setAttribute('aria-hidden','false');
  markNav(key);
  setTimeout(()=>{frame.src=url},20);
}
function closeWorkspace(){
  $('workspaceFrame').src='about:blank';
  currentModule='';
  currentWorkspaceUrl='about:blank';
  $('workspaceShell').classList.remove('open');
  $('workspaceShell').setAttribute('aria-hidden','true');
  $('workspaceStatus').textContent='已关闭';
  markNav('');
}
function reloadWorkspaceFrame(){if(currentWorkspaceUrl&&currentWorkspaceUrl!=='about:blank')$('workspaceFrame').src=currentWorkspaceUrl}
function openWorkspaceInNewWindow(){if(currentWorkspaceUrl&&currentWorkspaceUrl!=='about:blank')window.open(currentWorkspaceUrl,'_blank','noopener')}
function strategyNameMap(cfg){const out={};(cfg?.strategy_catalog||[]).forEach(x=>{if(x?.key)out[String(x.key)]=String(x.name||x.key)});return out}
function strategyLabel(key,cfg){
  const builtins={score_driven:'日常评分驱动',low_position:'低位修复',avoid_chasing_high:'高位追高过滤',source_reliability:'数据源可靠性',ma_repair:'均线修复',macd_cross:'MACD 金叉/多头',macd_hist_turn:'MACD 柱改善',volume_breakout:'温和放量',mfi_obv_resonance:'MFI/OBV 共振',rsi_kdj_resonance:'RSI/KDJ 共振',atr_risk:'ATR 风险过滤',position_risk:'仓位与止损',risk_control:'风险扣分',event_driven:'事件驱动',finance_quality:'财务质量',fundamental_quality:'基本面质量',cashflow_quality:'现金流质量',announcement_risk:'公告风险',policy_tailwind:'政策顺风',macro_liquidity:'宏观流动性',main_money_est:'主力资金估算',market_regime:'大盘情绪过滤',etf_liquidity:'ETF 流动性',adx_trend:'ADX 趋势'};
  const map=strategyNameMap(cfg||lastAutoConfig);
  return map[key]||builtins[key]||key;
}
function recommendPreset(){
  const syms=symbols();
  const etfOnly=syms.length>0&&syms.every(s=>/^[15]/.test(String(s)));
  const key=etfOnly?'etf_rotation':syms.length>8?'defensive':'balanced';
  selectBeginnerPreset(key);
  const text=etfOnly?'当前股票池均为 ETF，推荐“ETF 轮动”：流动性与趋势排序为主，风险仓位和大盘门控兜底。':syms.length>8?'股票池较大，推荐“防守学习”：降低单票和总仓位，先控制数据缺失、公告和市场风险。':'个股池规模适中，推荐“均衡入门”：日常评分为主，均线/量价确认，公告与大盘风险兜底。';
  $('strategyRecommendation').textContent=text+' 建议先回测，再实时模拟，最后才进入实盘确认。';
}
function renderStrategySelectionSummary(cfg){
  const combo=strategyCombo();
  const risk=cfg?.risk_controls||collectAutoConfig().risk_controls;
  $('strategySelectedSummary').innerHTML=`<b>当前组合：</b>${esc(combo.length?combo.map(k=>strategyLabel(k,cfg)).join('、'):'尚未选择策略')}<br><b>统一风控：</b>止损 ${esc(risk.stop_loss_pct)}% · 止盈 ${esc(risk.take_profit_pct)}% · 最大回撤 ${esc(risk.max_drawdown_pct)}% · 单票 ${esc(risk.max_single_position_pct)}%`;
}
function currentComboSet(){return new Set(strategyCombo())}
function setComboFromList(list){
  $('strategyCombo').value=[...new Set((list||[]).map(x=>String(x||'').trim()).filter(Boolean))].join(', ');
  renderStrategyCatalog(lastAutoConfig||{});
  renderWorkflow();
}
function strategyEditorIsOpen(){return !!$('strategyAdvancedDetails')?.open}
function onStrategyEditorToggle(details){
  if(!details?.open||strategyEditorHydrated)return;
  strategyEditorHydrated=true;
  renderStrategyCatalog(deferredStrategyConfig||lastAutoConfig||{});
}
function renderStrategyCatalog(cfg){
  deferredStrategyConfig=cfg||deferredStrategyConfig||lastAutoConfig||{};
  const activeCfg=deferredStrategyConfig;
  const catalog=activeCfg?.strategy_catalog||[];
  const selected=currentComboSet();
  $('strategyCatalogHint').textContent=`已选 ${selected.size} 项 / 可用 ${catalog.length} 项`;
  renderStrategySelectionSummary(activeCfg);
  if(!strategyEditorHydrated&&!strategyEditorIsOpen())return;
  strategyEditorHydrated=true;
  renderStrategyParamEditor(activeCfg);
  if(!catalog.length){$('strategyCatalog').innerHTML='<div class="notice">策略目录暂未返回，仍可手动输入策略 key。</div>';return}
  $('strategyCatalog').innerHTML=catalog.map(item=>{
    const key=String(item.key||'');
    const on=selected.has(key);
    return `<label class="strategy-chip ${on?'on':''}" title="${esc(item.description||item.beginner_note||'')}"><input type="checkbox" data-strategy-key="${esc(key)}" ${on?'checked':''} onchange="toggleStrategyFromCatalog(this)"><span><b>${esc(item.name||key)}</b><span>${esc(item.category||'策略')} · ${esc(item.beginner_note||item.description||'')}</span></span></label>`;
  }).join('');
}
function toggleStrategyFromCatalog(el){const set=currentComboSet();if(el.checked)set.add(el.dataset.strategyKey);else set.delete(el.dataset.strategyKey);setComboFromList([...set])}
function collectStrategyParamEditor(){
  const out={};
  const rows=[...document.querySelectorAll('[data-strategy-row]')];
  if(!rows.length){
    const cfg=deferredStrategyConfig||lastAutoConfig||{};
    const existing=cfg.strategy_parameters||{};
    strategyCombo().forEach(key=>{
      const row=existing[key]||{};
      out[key]={strategy:key,name:strategyLabel(key,cfg),enabled:row.enabled!==false,position_sizing:row.position_sizing||$('positionSizing').value||'score_weighted',max_single_position_pct:Number(row.max_single_position_pct??num('maxSinglePositionPct',20)),stop_loss_pct:Number(row.stop_loss_pct??num('stopLossPct',8)),take_profit_pct:Number(row.take_profit_pct??num('takeProfitPct',18)),max_drawdown_pct:Number(row.max_drawdown_pct??row.max_strategy_drawdown_pct??num('maxDrawdownPct',18)),buy_threshold:Number(row.buy_threshold??62),sell_threshold:Number(row.sell_threshold??45)};
    });
    return out;
  }
  rows.forEach(row=>{
    const key=row.dataset.strategyRow;
    out[key]={strategy:key,name:strategyLabel(key,lastAutoConfig),enabled:!!row.querySelector('[data-param="enabled"]')?.checked,position_sizing:row.querySelector('[data-param="position_sizing"]')?.value||$('positionSizing').value,max_single_position_pct:Number(row.querySelector('[data-param="max_single_position_pct"]')?.value||20),stop_loss_pct:Number(row.querySelector('[data-param="stop_loss_pct"]')?.value||8),take_profit_pct:Number(row.querySelector('[data-param="take_profit_pct"]')?.value||18),max_drawdown_pct:Number(row.querySelector('[data-param="max_drawdown_pct"]')?.value||18),buy_threshold:Number(row.querySelector('[data-param="buy_threshold"]')?.value||62),sell_threshold:Number(row.querySelector('[data-param="sell_threshold"]')?.value||45)};
  });
  return out;
}
function renderStrategyParamEditor(cfg){
  const combo=strategyCombo();
  const params=cfg?.strategy_parameters||{};
  if(!combo.length){$('strategyParamRows').innerHTML='<tr><td colspan="9" class="muted">请先选择策略组合</td></tr>';return}
  $('strategyParamRows').innerHTML=combo.map(key=>{
    const row=params[key]||{};
    const sizing=row.position_sizing||$('positionSizing').value||'score_weighted';
    const opt=v=>`<option value="${v}" ${sizing===v?'selected':''}>${esc(sizingLabel(v))}</option>`;
    return `<tr data-strategy-row="${esc(key)}"><td><b>${esc(strategyLabel(key,cfg))}</b><br><span class="muted" title="内部标识">内部标识：${esc(key)}</span></td><td><input data-param="enabled" type="checkbox" ${row.enabled===false?'':'checked'}></td><td><select data-param="position_sizing">${['score_weighted','atr_risk','volatility_target','fixed_weight','core_satellite','cash_first_defensive'].map(opt).join('')}</select></td><td><input data-param="max_single_position_pct" type="number" step="0.5" value="${esc(row.max_single_position_pct??$('maxSinglePositionPct').value)}"></td><td><input data-param="stop_loss_pct" type="number" step="0.5" value="${esc(row.stop_loss_pct??$('stopLossPct').value)}"></td><td><input data-param="take_profit_pct" type="number" step="0.5" value="${esc(row.take_profit_pct??$('takeProfitPct').value)}"></td><td><input data-param="max_drawdown_pct" type="number" step="0.5" value="${esc(row.max_drawdown_pct??row.max_strategy_drawdown_pct??$('maxDrawdownPct').value)}"></td><td><input data-param="buy_threshold" type="number" step="0.5" value="${esc(row.buy_threshold??62)}"></td><td><input data-param="sell_threshold" type="number" step="0.5" value="${esc(row.sell_threshold??45)}"></td></tr>`;
  }).join('');
}
function selectBeginnerPreset(key){
  const preset=lastAutoConfig?.beginner_presets?.[key];
  if(!preset){$('auditLog').textContent='预设尚未加载，请先刷新状态。';return}
  if(preset.strategy_family)$('strategy').value=preset.strategy_family;
  if(preset.position_sizing)$('positionSizing').value=preset.position_sizing;
  setComboFromList(preset.strategy_combo||[]);
  const r=preset.risk_controls||{};
  ['stopLossPct','takeProfitPct','maxDrawdownPct','maxSinglePositionPct','maxTotalPositionPct','minCashPct'].forEach(id=>{
    const keyMap={stopLossPct:'stop_loss_pct',takeProfitPct:'take_profit_pct',maxDrawdownPct:'max_drawdown_pct',maxSinglePositionPct:'max_single_position_pct',maxTotalPositionPct:'max_total_position_pct',minCashPct:'min_cash_pct'};
    if(r[keyMap[id]]!=null)$(id).value=r[keyMap[id]];
  });
  renderWorkflow();
  $('auditLog').textContent='已套用预设：'+(preset.label||key)+'\\n'+(preset.description||'');
}
function collectAutoConfig(){
  return {symbols:symbols(),strategy_family:$('strategy').value,selected_strategies:strategyCombo(),strategy_combo:strategyCombo(),strategy_parameters:collectStrategyParamEditor(),position_sizing:$('positionSizing').value,interval_seconds:Number($('interval').value||15),initial_cash:num('initialCash',100000),reset_account:checked('resetAccount'),risk_controls:{stop_loss_pct:num('stopLossPct',8),take_profit_pct:num('takeProfitPct',18),max_drawdown_pct:num('maxDrawdownPct',18),max_single_position_pct:num('maxSinglePositionPct',20),max_total_position_pct:num('maxTotalPositionPct',80),min_cash_pct:num('minCashPct',15),max_daily_loss_pct:4,atr_risk_pct:1.5,cooldown_days:2},score_weights:{screening:.30,technical:.30,fundamental:.22,information:.20,fund_flow:.16,market_regime:.12},event_watch:{financial_reports:checked('watchFinancialReports'),half_year_reports:checked('watchHalfYearReports'),earnings_preannouncements:checked('watchFinancialReports'),exchange_announcements:checked('watchAnnouncements'),major_negative_news:checked('watchMajorNews'),policy_industry_news:checked('watchPolicyNews'),event_lookahead_days:21,blackout_before_days:2,blackout_after_days:1},data_requirements:{require_fresh_quote:checked('requireFreshQuote'),block_stale_buy:checked('requireFreshQuote'),require_score_provenance:true,require_info_snapshot:false,require_orderbook_when_available:true},source_page:'auto-trading'};
}
function applyAutoConfig(cfg){
  if(!cfg)return;
  lastAutoConfig=cfg;
  if((cfg.symbols||[]).length)$('symbols').value=cfg.symbols.join(', ');
  if(cfg.strategy_family)$('strategy').value=cfg.strategy_family;
  if(cfg.interval_seconds!=null)$('interval').value=String(cfg.interval_seconds);
  if((cfg.strategy_combo||[]).length)$('strategyCombo').value=cfg.strategy_combo.join(', ');
  if(cfg.position_sizing)$('positionSizing').value=cfg.position_sizing;
  const r=cfg.risk_controls||{};
  const set=(id,k)=>{if(r[k]!=null)$(id).value=r[k]};
  set('stopLossPct','stop_loss_pct');set('takeProfitPct','take_profit_pct');set('maxDrawdownPct','max_drawdown_pct');set('maxSinglePositionPct','max_single_position_pct');set('maxTotalPositionPct','max_total_position_pct');set('minCashPct','min_cash_pct');
  if(cfg.initial_cash!=null)$('initialCash').value=cfg.initial_cash;
  renderStrategyCatalog(cfg);
  renderWorkflow();
}
function renderWorkflow(state={}){
  const cfg=state.cfg||lastAutoConfig||collectAutoConfig();
  const combo=(cfg.strategy_combo||strategyCombo()).filter(Boolean);
  const syms=(cfg.symbols||symbols()).filter(Boolean);
  const risk=cfg.risk_controls||collectAutoConfig().risk_controls;
  setText('wfSymbols',syms.length?syms.slice(0,4).join(', '):'--');
  setText('wfCombo',combo.length?combo.slice(0,3).map(k=>strategyLabel(k,cfg)).join(' / '):'未选择策略');
  $('workflowBody').innerHTML=[
    ['股票池',syms.length?syms.join(', '):'--'],
    ['策略组合',combo.length?combo.map(k=>strategyLabel(k,cfg)).join('、'):'--'],
    ['仓位/风控',`${sizingLabel(cfg.position_sizing)}；止损 ${risk.stop_loss_pct??'--'}%；止盈 ${risk.take_profit_pct??'--'}%；最大回撤 ${risk.max_drawdown_pct??'--'}%`],
    ['事件监控','财报、半年报、公告、重大负面、政策/宏观事件'],
    ['实盘安全','默认关闭；需要券商授权、风控、确认队列和 kill switch']
  ].map(x=>`<tr><th>${x[0]}</th><td>${esc(x[1])}</td></tr>`).join('');
}
function renderConfigSummary(cfg,readiness){
  const combo=(cfg?.strategy_combo||[]).map(k=>strategyLabel(k,cfg)).join('、')||'--';
  const events=(cfg?.key_event_watchlist||[]).filter(x=>x.enabled).map(x=>x.label).slice(0,5).join('、')||'未开启';
  const gates=(readiness?.gates||[]).slice(0,5).map(g=>(g.ok?'通过 ':'待处理 ')+g.label).join('；');
  $('configSummary').innerHTML=`<b>股票池</b> ${(cfg?.symbols||[]).join(', ')||'--'}<br><b>策略</b> ${esc(combo)}<br><b>仓位</b> ${esc(sizingLabel(cfg?.position_sizing))}；<b>事件</b> ${esc(events)}<br>${esc(gates||'等待就绪检查')}`;
}
function renderSessionRows(items){
  const rows=[['订单',items.orders?.count??0],['成交',items.fills?.count??0],['图表标注',items.markers?.count??0],['审计',items.audit?.count??0]];
  $('sessionRows').innerHTML=rows.map(x=>`<tr><th>${x[0]}</th><td>${x[1]}</td></tr>`).join('');
}
function renderPortfolioOverview(liveAccount,livePositions,records,paperPortfolio){
  latestPortfolioInputs={liveAccount,livePositions,records};
  const account=liveAccount?.data||{};
  const liveRows=Array.isArray(livePositions?.data)?livePositions.data:[];
  const summary=livePositions?.summary||{};
  const recordSummary=records?.summary||{};
  const recRows=(records?.data||[]).slice(0,10);
  const cash=account.available_cash??account.cash?.available_cash??account.cash;
  const total=account.total_value??account.equity??account.total_assets;
  const livePnl=summary.unrealized_pnl??account.unrealized_pnl;
  const livePnlPct=summary.unrealized_pnl_pct;
  const liveStatus=livePositions?.source?.status||liveAccount?.source?.status||'disabled';
  const missing=livePositions?.missing_reason||account.quality_status||'';
  const positionsText=liveRows.length
    ? liveRows.slice(0,4).map(p=>`${esc(p.symbol)} ${esc(p.quantity??0)}股 成本${esc(p.cost_price??p.avg_cost??'--')} 市值${money(p.market_value)}`).join('；')
    : '暂无真实持仓或券商未授权';
  const paper=paperPortfolio||latestPaperPortfolio||{};
  const paperSummary=paper.summary||{};
  const paperPositions=paper.positions||[];
  const paperSession=paper.session||{};
  const paperPositionText=paperPositions.length
    ? paperPositions.slice(0,6).map(p=>{
        const qty=p.quantity??p.qty??0;
        const cost=p.avg_cost??p.cost_price??p.avg_price;
        const last=p.market_price??p.last_price;
        const upnl=p.unrealized_pnl;
        return `${esc(p.symbol)} ${esc(qty)}股｜成本 ${money(cost)}｜现价 ${money(last)}｜浮盈亏 <span class="${pnlClass(upnl)}">${money(upnl)}${p.unrealized_pnl_pct!=null?' / '+pct(p.unrealized_pnl_pct):''}</span>`;
      }).join('<br>')
    : '暂无模拟持仓；请查看订单诊断，可能尚未达到买入阈值、休市被拦截或最小 100 股超过单票仓位上限。';
  const recordText=[
    `流水 ${esc(recordSummary.rows_count??recRows.length)} 条`,
    `委托 ${esc(recordSummary.orders_count??0)}`,
    `成交 ${esc(recordSummary.fills_count??0)}`,
    `持仓 ${esc(recordSummary.positions_count??0)}`,
    `持仓市值 ${money(recordSummary.position_market_value)}`,
    `持仓成本 ${money(recordSummary.position_cost_value)}`,
    `已实现 ${money(recordSummary.realized_pnl)}`,
    `浮动 ${money(recordSummary.unrealized_pnl)}${recordSummary.position_unrealized_pnl_pct!=null?' / '+pct(recordSummary.position_unrealized_pnl_pct):''}`
  ].join('；');
  const paperText=paper.session_id
    ? `<b>当前模拟账户</b> ${esc(paperSession.status||'--')}｜现金 ${money(paperSummary.cash)}｜总资产 ${money(paperSummary.equity)}｜持仓成本 ${money(paperSummary.position_cost_value)}｜持仓市值 ${money(paperSummary.position_market_value)}<br><b>模拟盈亏/成交</b> 已实现 <span class="${pnlClass(paperSummary.realized_pnl)}">${money(paperSummary.realized_pnl)}</span>；浮动 <span class="${pnlClass(paperSummary.unrealized_pnl)}">${money(paperSummary.unrealized_pnl)}</span>；收益率 <span class="${pnlClass(paperSummary.total_return_pct)}">${pct(paperSummary.total_return_pct)}</span>；买入 ${money(paperSummary.buy_amount)}；卖出 ${money(paperSummary.sell_amount)}；总成交 ${money(paperSummary.turnover_amount)}；交易成本 ${money(paperSummary.total_trading_cost)}（佣金 ${money(paperSummary.commission)} / 卖出税 ${money(paperSummary.sell_tax)} / 滑点 ${money(paperSummary.slippage_cost)}）<br><b>模拟持仓明细</b><br>${paperPositionText}`
    : '<b>当前模拟账户</b> 暂无会话；启动实时模拟后会在这里显示现金、成本、市值、盈亏和逐股持仓。';
  $('portfolioOverview').innerHTML=`${paperText}<hr style="border:0;border-top:1px solid var(--line);margin:10px 0"><b>真实账户（安全隔离）</b> 可用资金 ${money(cash)}；总资产 ${money(total)}；持仓 ${esc(liveRows.length)} 只；浮盈亏 <span class="${pnlClass(livePnl)}">${money(livePnl)}</span>${livePnlPct!=null?' / '+pct(livePnlPct):''}<br><b>实盘持仓</b> ${positionsText}<br><b>券商状态</b> ${esc(liveStatus)}${missing?'；'+esc(missing):''}<hr style="border:0;border-top:1px solid var(--line);margin:10px 0"><b>统一流水</b> ${recordText}`;
  $('recordOverviewRows').innerHTML=recRows.map(x=>{
    const price=x.display_price??x.price??x.limit_price??'--';
    const qty=x.display_quantity??x.quantity??x.qty??'--';
    const amount=x.display_amount??x.amount;
    const pnl=x.display_pnl??x.realized_pnl??x.unrealized_pnl??x.pnl;
    const pnlPct=x.display_pnl_pct??x.unrealized_pnl_pct??x.pnl_pct;
    const cost=x.display_cost_price??x.cost_price??x.avg_cost??x.avg_price;
    const amountText=pnl!=null?`盈亏 ${money(pnl)}${pnlPct!=null?' / '+pct(pnlPct):''}`:`金额 ${money(amount)}`;
    const detail=[amountText,cost!=null?`成本 ${esc(cost)}`:''].filter(Boolean).join('；');
    return `<tr><td>${esc(x.record_type_cn||x.table||'记录')}</td><td>${esc(x.symbol||'--')}</td><td>${esc(x.display_side||x.side||x.display_status||x.status||'--')}</td><td>${esc(price)}</td><td>${esc(qty)}</td><td class="${pnlClass(pnl)}">${detail}</td></tr>`;
  }).join('')||'<tr><td colspan="6">暂无交易流水；预检查、确认、成交后会自动出现在这里。</td></tr>';
}
async function loadSessionDetails(session){
  activeSessionId=sessionIdOf(session)||activeSessionId;
  if(!activeSessionId){$('sessionSnapshot').textContent='暂无 active session';$('paperPositionReviews').innerHTML='<span class="muted">暂无可复核模拟持仓。</span>';renderSessionRows({});return}
  const base='/api/realtime-paper/sessions/'+encodeURIComponent(activeSessionId);
  const [snapshot,orders,fills,positions,markers,audit,reviews]=await Promise.all([api(base),api(base+'/orders?limit=500'),api(base+'/fills?limit=500'),api(base+'/positions'),api(base+'/markers?limit=50'),api(base+'/audit?limit=100'),api(base+'/position-reviews?limit=50')]);
  const sess=snapshot.data||session||{};
  $('activeSessionText').textContent=(sess.status||'--')+' · '+activeSessionId;
  const account=positions.data?.snapshot||{};
  const posRows=positions.data?.positions||[];
  const summary=positions.summary||{};
  const pendingSettlement=account.pending_settlement||{};
  const pendingBySymbol={};
  for(const [symbol,batches] of Object.entries(pendingSettlement)){
    pendingBySymbol[symbol]=(Array.isArray(batches)?batches:[]).reduce((sum,row)=>sum+Number(row?.quantity||0),0);
  }
  const pendingQty=Object.values(pendingBySymbol).reduce((sum,qty)=>sum+Number(qty||0),0);
  const rejected=(orders.data||[]).filter(x=>['rejected','risk_blocked','failed'].includes(String(x.status||''))).length;
  const zeroQty=(orders.data||[]).filter(x=>Number(x.quantity||0)<=0).length;
  $('sessionSnapshot').innerHTML=`<b>${esc((sess.symbols||[]).join(', ')||'模拟股票池')}</b>｜状态 ${esc(sess.status||'--')}<br>本金 ${money(summary.initial_cash??account.initial_cash)}｜现金 ${money(summary.cash??account.cash??account.available_cash)}｜总资产 ${money(summary.equity??account.equity??account.total_value)}｜T+1待交收 ${esc(pendingQty)}股<br>成本 ${money(summary.position_cost_value)}｜市值 ${money(summary.position_market_value)}｜已实现 <span class="${pnlClass(summary.realized_pnl)}">${money(summary.realized_pnl)}</span>｜浮盈亏 <span class="${pnlClass(summary.unrealized_pnl)}">${money(summary.unrealized_pnl)}</span>｜收益率 <span class="${pnlClass(summary.total_return_pct)}">${pct(summary.total_return_pct)}</span><br>买入额 ${money(summary.buy_amount)}｜卖出额 ${money(summary.sell_amount)}｜总成交额 ${money(summary.turnover_amount)}｜交易成本 ${money(summary.total_trading_cost)}｜拒单/拦截 ${rejected}${zeroQty?'｜零数量旧单 '+zeroQty:''}<br>${posRows.length?posRows.slice(0,8).map(p=>`${esc(p.symbol)}：持仓 ${esc(p.quantity??p.qty??0)}股｜可卖 ${esc(p.available_quantity??p.quantity??0)}股｜待交收 ${esc(pendingBySymbol[p.symbol]||0)}股｜成本 ${money(p.avg_cost??p.cost_price)}｜现价 ${money(p.market_price??p.last_price)}｜市值 ${money(p.market_value)}｜浮盈亏 <span class="${pnlClass(p.unrealized_pnl)}">${money(p.unrealized_pnl)}${p.unrealized_pnl_pct!=null?' / '+pct(p.unrealized_pnl_pct):''}</span>`).join('<br>'):'暂无持仓；系统不会为凑成交而伪造订单。'}`;
  latestPaperPortfolio={session_id:activeSessionId,session:sess,summary,positions:posRows};
  renderPortfolioOverview(latestPortfolioInputs.liveAccount,latestPortfolioInputs.livePositions,latestPortfolioInputs.records,latestPaperPortfolio);
  renderPositionReviews(reviews.data||[],'paperPositionReviews','尚无持仓复核记录；点击“复核全部持仓”会按当前真实缓存重新评分。');
  renderSessionRows({orders,fills,markers,audit});
}
function renderPositionReviews(rows,targetId,emptyText){
  const target=$(targetId);if(!target)return;
  const latest=[];const seen=new Set();
  for(const row of rows||[]){const key=String(row.symbol||'');if(!key||seen.has(key))continue;seen.add(key);latest.push(row)}
  if(!latest.length){target.innerHTML=`<span class="muted">${esc(emptyText||'暂无持仓复核记录。')}</span>`;return}
  target.innerHTML=latest.slice(0,12).map(row=>{
    const action=String(row.action||'manual_review');
    const css=action==='exit'?'exit':action==='reduce'?'reduce':action==='hold'?'hold':'';
    const delta=Number(row.score_delta),pnl=Number(row.unrealized_pnl),pnlPct=Number(row.unrealized_pnl_pct);
    const reasons=(row.reasons||[]).join('；')||'未提供复核原因';
    const blocked=(row.blocking_missing_data||[]).join('、');
    return `<div class="position-review"><div><b>${esc(row.name||row.symbol)} ${esc(row.symbol||'')}</b><span class="review-action ${css}">${esc(row.action_cn||cnEnum(action))}</span></div><small>持仓 ${esc(row.quantity??0)} 股｜成本 ${money(row.avg_cost)}｜现价 ${money(row.market_price)}｜浮盈亏 <span class="${pnlClass(pnl)}">${money(pnl)}${Number.isFinite(pnlPct)?' / '+pct(pnlPct):''}</span></small><small>当前评分 ${Number.isFinite(Number(row.final_score))?Number(row.final_score).toFixed(2):'缺失'}${Number.isFinite(delta)?`｜较上次 ${delta>=0?'+':''}${delta.toFixed(2)} 分`:''}｜${esc(reasons)}</small>${blocked?`<small class="warn">阻断缺失：${esc(blocked)}</small>`:''}</div>`;
  }).join('');
}
async function reviewPaperPositions(btn=null){
  if(!activeSessionId){showToast('请先启动或恢复实时模拟会话','bad');return}
  return withAction(btn,'复核中','模拟持仓复核完成',async()=>{
    const base='/api/realtime-paper/sessions/'+encodeURIComponent(activeSessionId);
    const js=await api(base+'/review-positions',{method:'POST'});
    renderPositionReviews(js.data||[],'paperPositionReviews',js.message||'暂无可复核持仓。');
    $('auditLog').textContent=JSON.stringify(js,null,2);
    return js;
  });
}
async function reviewLivePositions(btn=null){
  return withAction(btn,'复核中','实盘持仓只读复核完成',async()=>{
    const js=await api('/api/live/review-positions',{method:'POST'});
    renderPositionReviews(js.data||[],'livePositionReviews',js.missing_reason||'当前没有可复核真实持仓。');
    $('auditLog').textContent=JSON.stringify(js,null,2);
    return js;
  });
}
function renderReviewSchedule(js){
  const row=js?.data||{};const last=js?.last_run||{};
  const state=row.due?'已到期':(row.reason||'等待计划');
  $('reviewScheduleStatus').innerHTML=`<b>每日持仓复核：</b>${esc(state)}｜上次 ${esc(last.review_date||'尚未运行')}｜下次 ${esc(row.next_run_at||'待计算')}<br><span class="muted">收盘后每日一次；只更新持仓评分和建议，不创建订单。</span>`;
}
function renderPaperScheduler(js){
  const running=!!js?.running,enabled=!!js?.enabled;
  const session=js?.market_session||{};
  const state=!enabled?'已关闭':running?'运行中':'未启动';
  const market=session.state_cn||session.status_cn||session.state||session.status||'交易时段待确认';
  const error=js?.last_error?`<br><span class="bad">最近错误：${esc(js.last_error)}</span>`:'';
  const sessions=(js?.sessions||[]).slice(0,4);
  const detail=sessions.length?'<div class="agent-evidence-list">'+sessions.map(x=>{
    const sid=String(x.session_id||'未命名').slice(0,12);
    const next=x.next_due_at?String(x.next_due_at).replace('T',' '):'等待下个交易时段';
    const reason=x.blocked_reason||((x.due?'已到复评时间':'等待频率到期'));
    return `<div class="agent-evidence"><time>${esc(cnEnum(x.status||'--'))} · ${Number(x.symbol_count||0)}只</time><strong>${esc(sid)} · ${esc(reason)}</strong><small>股票池 ${esc((x.symbols||[]).join(', ')||'缺失')}；最后复评 ${esc(x.last_tick_at||'尚无')}；下次 ${esc(next)}</small></div>`;
  }).join('')+'</div>':'';
  $('paperSchedulerStatus').innerHTML=`<b>服务端自动复评：</b>${esc(state)}｜活跃会话 ${Number(js?.active_sessions||0)}｜待执行 ${Number(js?.due_sessions||0)}｜${esc(market)}<br><span class="muted">${esc(js?.policy||'开盘按会话频率逐只复评；页面关闭后仍保存会话，休市和午休不下单。')}</span>${detail}${error}`;
  if(!activeSessionId)$('activeSessionText').textContent=`后台复评 ${state}`;
}
async function runDuePositionReviews(btn=null){
  return withAction(btn,'检查中','每日持仓复核检查完成',async()=>{
    const js=await api('/api/position-reviews/scheduler/run-due',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({force:false})});
    const status=await api('/api/position-reviews/scheduler/status');renderReviewSchedule(status);
    $('auditLog').textContent=JSON.stringify(js,null,2);await refreshAll();return js;
  });
}
async function loadAgentDecision(force=false){
  const js=await api('/api/agent/market-brief?symbols='+encodeURIComponent(symbols().join(','))+'&limit=80&force='+(force?'true':'false')+'&use_llm='+(force?'true':'false'));
  renderAgentDecision(js);
  return js;
}
async function loadAgentBrief(force=false){
  if(force)await loadGlobalStream(true);
  const [agent,js]=await Promise.all([loadAgentDecision(force),api('/api/macro/global-events?limit=80&force='+(force?'true':'false'))]);
  renderAgentDecision(agent);
  renderGlobalFeed(js);
}
function streamItemsOf(js){return (js?.items||js?.data?.items||[]).filter(Boolean)}
function mergeGlobalStreams(jin10,global){
  const seen=new Set();
  const items=[];
  for(const item of [...streamItemsOf(jin10),...streamItemsOf(global)]){
    const title=String(item.title||item.summary||'').trim();
    if(!title)continue;
    const key=(String(item.source||'')+':'+title).replace(/\\W+/g,'').slice(0,140);
    if(seen.has(key))continue;
    seen.add(key);
    items.push({...item,rank:items.length+1});
    if(items.length>=80)break;
  }
  const jd=jin10?.data||{};
  const gd=global?.data||{};
  const sources=[...(jd.sources_status||[]),...(gd.sources_status||[])];
  const refresh=Math.max(12,Math.min(60,Number(jin10?.refresh_seconds||jd.refresh_seconds||global?.refresh_seconds||gd.refresh_seconds||20)));
  return {
    ok:true,
    items,
    cache_status:jin10?.cache_status||global?.cache_status||{},
    data:{
      ...gd,
      items,
      raw_count:items.length,
      updated_at:jd.updated_at||gd.updated_at||new Date().toISOString(),
      stream_mode:(jd.stream_mode||'jin10')+' + '+(gd.stream_mode||'global'),
      sources_status:sources,
      refresh_seconds:refresh,
      missing_reason:items.length?'':(jd.missing_reason||gd.missing_reason||'金十和全球快讯源暂未返回有效条目；不会伪造新闻。'),
      source_candidates:[...(jd.source_candidates||[]),...(gd.source_candidates||[])]
    },
    refresh_seconds:refresh
  };
}
async function loadGlobalStream(force=false){
  if(globalStreamPromise)return globalStreamPromise;
  const task=(async()=>{
    const [jin10,global]=await Promise.all([
      api('/api/news/jin10/realtime?limit=80&force='+(force?'true':'false')),
      api('/api/news/global/stream?limit=80&live=true&force='+(force?'true':'false'))
    ]);
    const merged=mergeGlobalStreams(jin10,global);
    renderGlobalStream(merged);
    scheduleGlobalStreamLoop();
    return merged;
  })();
  globalStreamPromise=task;
  try{return await task}finally{if(globalStreamPromise===task)globalStreamPromise=null}
}
function toggleGlobalTicker(){
  globalTickerPaused=!globalTickerPaused;
  $('globalTicker').classList.toggle('paused',globalTickerPaused);
  $('tickerPauseBtn').textContent=globalTickerPaused?'继续轮播':'暂停轮播';
  if(globalTickerPaused){if(globalStreamTimer)clearInterval(globalStreamTimer);globalStreamTimer=null}
  else{loadGlobalStream(false).catch(()=>{});scheduleGlobalStreamLoop()}
}
function scheduleGlobalStreamLoop(){
  if(globalStreamTimer)clearInterval(globalStreamTimer);
  globalStreamTimer=null;
  if(document.hidden||globalTickerPaused)return;
  globalStreamTimer=setInterval(()=>{if(!document.hidden&&!globalTickerPaused)loadGlobalStream(false).catch(()=>{})},globalStreamRefreshMs);
}
function startGlobalStreamLoop(){
  if(!window.__qdGlobalVisibilityBound){
    window.__qdGlobalVisibilityBound=true;
    document.addEventListener('visibilitychange',()=>{
      if(document.hidden){if(globalStreamTimer)clearInterval(globalStreamTimer);globalStreamTimer=null;return}
      loadGlobalStream(false).catch(()=>{});
      scheduleGlobalStreamLoop();
    });
  }
  scheduleGlobalStreamLoop();
}
// V3.23 readable global-info renderer override. The older renderer stayed compact;
// this one makes source, link, affected target and symbol mapping explicit.
function textList(v){
  if(Array.isArray(v))return v.map(x=>String(x||'').trim()).filter(Boolean);
  return String(v||'').split(/[\\s,，、;；|/]+/).map(x=>x.trim()).filter(Boolean);
}
function uniqueList(arr,limit=10){
  const out=[];
  (arr||[]).forEach(x=>{const s=String(x||'').trim();if(s&&!out.includes(s))out.push(s)});
  return out.slice(0,limit);
}
function sourceUrlOf(x){
  return String(x?.source_ref||x?.source_url||x?.url||x?.source_page||x?.source_api||'').trim();
}
function sourceLabelOf(x){
  return String(x?.source||x?.source_name||x?.media||x?.latest_source||'全球信息源').trim();
}
function sourceMetaHtml(x){
  const label=sourceLabelOf(x);
  const api=String(x?.source_api||x?.latest_source_api||'').trim();
  const page=String(x?.source_page||x?.latest_source_page||'').trim();
  const ref=sourceUrlOf(x);
  const parts=[`<span>数据来源：${esc(label)}</span>`];
  if(api)parts.push(`<span>接口：<a href="${esc(api)}" target="_blank" rel="noopener noreferrer">${esc(api)}</a></span>`);
  if(page&&page!==api)parts.push(`<span>页面：<a href="${esc(page)}" target="_blank" rel="noopener noreferrer">${esc(page)}</a></span>`);
  if(ref&&ref!==api&&ref!==page)parts.push(`<span>原始链接：<a href="${esc(ref)}" target="_blank" rel="noopener noreferrer">${esc(ref)}</a></span>`);
  if(!ref&&!api&&!page)parts.push('<span class="warn">该来源未提供可跳转链接，只保留标题、时间和来源名。</span>');
  return `<div class="source-meta">${parts.join('')}</div>`;
}
function impactTagsOf(x){
  return uniqueList([
    ...textList(x?.affected_companies),
    ...textList(x?.mapped_symbols).map(s=>`证券代码 ${s}`),
    ...textList(x?.impact_targets),
    ...textList(x?.affected_sectors),
    ...textList(x?.affected_assets),
    ...textList(x?.industry_tags),
    ...textList(x?.related_symbols),
    ...textList(x?.matched_terms),
    cnEnum(x?.impact_level||''),
  ],10);
}
function impactNoteOf(x){
  return x?.impact_note||x?.reason||x?.impact_scope||x?.sentiment_label||'仅作宏观、商品、政策或信息面风险观察，不直接等于买卖信号。';
}
function impactTagsHtml(x,prefix='影响对象'){
  const tags=impactTagsOf(x);
  if(!tags.length)return `<div class="impact-summary"><b>${esc(prefix)}：</b>暂无明确映射，需结合个股行业、资金面和技术面继续确认。</div>`;
  return `<div class="impact-row"><span class="impact-tag">${esc(prefix)}</span>${tags.map(t=>`<span class="impact-tag">${esc(t)}</span>`).join('')}</div>`;
}
function sourceLinksHtml(x,primaryLabel='查看来源 / 原文'){
  const api=String(x?.source_api||x?.latest_source_api||'').trim();
  const page=String(x?.source_page||x?.latest_source_page||'').trim();
  const ref=sourceUrlOf(x);
  const links=[];
  if(ref)links.push(`<a href="${esc(ref)}" target="_blank" rel="noopener noreferrer" title="打开来源 / 原文">${esc(primaryLabel)}</a>`);
  if(api&&api!==ref)links.push(`<a href="${esc(api)}" target="_blank" rel="noopener noreferrer">查看数据接口</a>`);
  if(page&&page!==ref&&page!==api)links.push(`<a href="${esc(page)}" target="_blank" rel="noopener noreferrer">查看来源页面</a>`);
  if(!links.length)links.push('<span>无公开跳转链接：仅展示可追溯来源名称和缓存记录</span>');
  return `<div class="source-link-row">${links.join('')}</div>`;
}
function renderGlobalFeed(js){
  const items=(js.data?.items||js.items||[]).slice(0,10);
  const watch=(js.watchlist||js.data?.watchlist||[]).slice(0,7);
  if(!items.length&&!watch.length){
    $('macroFeed').innerHTML='<div class="feed-item"><b>暂无全球信息缓存</b><span>可以点击“联网刷新”。如果真实来源不可用，只显示缺失原因，不生成假新闻。</span></div>';
    return;
  }
  const watchRows=watch.map(x=>{
    const latest=x.latest_title?`<div class="impact-summary"><b>最近命中：</b>${esc(x.latest_title)}${x.latest_source?` · ${esc(x.latest_source)}`:''}</div>`:'';
    return `<div class="feed-item"><time>${esc(cnEnum(x.status||'观察'))}</time><b>${esc(x.label||x.key)}</b><span>${esc(x.reason||x.missing_reason||'等待真实数据源命中')}</span>${impactTagsHtml(x,'影响维度')}${latest}${sourceMetaHtml(x)}${sourceLinksHtml(x,'打开命中来源')}</div>`;
  });
  const itemRows=items.map(x=>`<div class="feed-item"><time>${esc(x.published_at||x.date||x.time||'时间缺失')}</time><b>${esc(x.title||x.summary||'未命名事件')}</b><span><b>影响说明：</b>${esc(impactNoteOf(x))}</span>${impactTagsHtml(x)}${sourceMetaHtml(x)}${sourceLinksHtml(x)}</div>`);
  $('macroFeed').innerHTML=[...watchRows,...itemRows].join('');
}
function renderAgentDecision(js){
  const d=js.data||{};
  const ai=d.ai_analysis||{};
  const aiView=ai.analysis||{};
  const decisions=(d.symbol_decisions||[]).slice(0,6);
  const themeTrends=(d.theme_trends||[]).slice(0,10);
  const risks=(d.risk_flags||[]).slice(0,5);
  const evidence=(d.evidence||[]).slice(0,5);
  const symbolImpacts=(d.symbol_global_impacts||[]).slice(0,8);
  const chunks=[
    `<b>${esc(d.headline||'暂无智能辅助结论')}</b>`,
    `<span>建议动作：${esc(cnAction(d.recommended_action||'--'))} · 置信度：${esc(cnEnum(d.confidence||'--'))} · 全球快讯 ${esc(d.global_flash_count??0)} 条 · 可跳转来源 ${esc(d.source_link_count??0)} 个 · ${esc(d.llm_status||'联网证据代理')}</span>`,
    '<div class="source-policy">来源说明：只读取金十/全球快讯、东方财富等真实来源与本地缓存；没有来源链接时会明确显示“无公开跳转链接”。宏观事件只进入信息面和风控解释，不会单独触发自动买入。</div>'
  ];
  if(ai.ok&&aiView.summary){
    chunks.push(`<div class="agent-evidence"><time>外部模型 · 仅研究解释</time><strong>${esc(cnEnum(aiView.market_regime||'市场环境复核'))}</strong><small>${esc(aiView.summary)}</small>${(aiView.symbol_views||[]).slice(0,6).map(x=>`<div>${esc(x.symbol)} · ${esc(cnAction(x.action))}：${esc(x.reason)} <span class="muted">证据 ${esc((x.evidence_refs||[]).join(', ')||'缺失')}</span></div>`).join('')}<div class="risk">${esc((aiView.risks||[]).join('；')||'模型未补充额外风险')}；该结果不能创建、确认或提交订单。</div></div>`);
  }else if(ai.status&&ai.status!=='not_requested'){
    chunks.push(`<div class="source-note">模型状态：${esc(ai.reason||ai.status)}；继续保留上面的规则证据结论。</div>`);
  }
  if(decisions.length){
    chunks.push('<ul>'+decisions.map(x=>`<li>${esc(x.symbol)} ${esc(x.name||'')}：${esc(cnAction(x.action||'观察'))}${x.score!=null?' · 评分 '+esc(x.score):''}；${esc(x.reason||'')}</li>`).join('')+'</ul>');
  }
  if(themeTrends.length){
    chunks.push('<div class="agent-evidence-list"><div class="source-note">题材趋势：由公开板块净流、15/30/60分钟快照差、近5日累计和主线强度确定性计算；“等待数据”不会被补成趋势。</div>'+themeTrends.map(x=>{
      const support=(x.support_evidence||[]).slice(0,4).join('；');
      const counter=(x.counter_evidence||[]).slice(0,4).join('；');
      const missing=(x.missing_data||[]).slice(0,4).join('；');
      const detail=[support?'支持：'+support:'',counter?'反证：'+counter:'',missing?'缺失：'+missing:''].filter(Boolean).join('；');
      const link=x.source_ref||x.source_url;
      return `<div class="agent-evidence"><time>${esc(x.published_at||x.flow_state||'快照时间缺失')}</time><strong>${esc(x.theme)} · ${esc(x.trend)} · 置信度 ${esc(Math.round(Number(x.confidence||0)*100))}%</strong><small>${esc(detail||'当前没有足够真实资金快照形成判断。')}</small><div class="impact-row"><span class="impact-tag">${esc(x.stage||'观察')}</span><span class="impact-tag">${esc(x.flow_state||'等待快照')}</span><span class="impact-tag">主线分 ${x.mainline_score==null?'缺失':esc(Number(x.mainline_score).toFixed(1))}</span></div>${link?`<a href="${esc(link)}" target="_blank" rel="noopener noreferrer">查看 ${esc(x.source_name||'板块资金来源')}</a>`:'<span class="muted">来源链接缺失</span>'}<div class="source-note">${esc(x.truth_boundary||'公开板块资金不是逐笔或 Level-2 主力账户识别。')}</div></div>`;
    }).join('')+'</div>');
  }
  if(symbolImpacts.length){
    chunks.push('<div class="agent-evidence-list"><div class="source-note">个股影响映射：下面逐只说明全球要闻是否命中当前股票池，以及命中的依据。</div>'+symbolImpacts.map(s=>{
      const ev=(s.related_events||[])[0]||{};
      const exposure=uniqueList([...(s.exposure_terms||[]),...(ev.matched_terms||[])],8);
      const exposureHtml=exposure.length?`<div class="impact-row"><span class="impact-tag">映射依据</span>${exposure.map(t=>`<span class="impact-tag">${esc(t)}</span>`).join('')}</div>`:'';
      if(!ev.title){
        return `<div class="agent-evidence symbol-impact-card none"><time>${esc(cnEnum(s.status||'no_direct_mapping'))}</time><strong>${esc(s.symbol)} ${esc(s.name||'')} · 暂无全球快讯直接命中</strong><small>${esc(s.explain||'当前真实全球快讯未直接命中该标的产业链；仍可作为大盘环境观察。')}</small>${exposureHtml}</div>`;
      }
      return `<div class="agent-evidence symbol-impact-card"><time>${esc(ev.published_at||'影响映射')}</time><strong>${esc(s.symbol)} ${esc(s.name||'')} · ${esc(ev.title||'全球事件映射')}</strong><small>${esc(ev.impact_note||s.explain||'仅作信息面风险观察。')}</small>${impactTagsHtml(ev,'命中影响')}${exposureHtml}${sourceMetaHtml(ev)}${sourceLinksHtml(ev,'查看影响来源 / 原文')}</div>`;
    }).join('')+'</div>');
  }
  if(evidence.length){
    chunks.push('<div class="agent-evidence-list"><div class="source-note">证据列表：用于解释信息面和风控，不直接等同于交易指令。</div>'+evidence.map(x=>`<div class="agent-evidence"><time>${esc(x.published_at||x.type||'证据')}</time><strong>${esc(x.title||x.reason||'事件')}</strong><small>${esc(impactNoteOf(x))}</small>${impactTagsHtml(x)}${sourceMetaHtml(x)}${sourceLinksHtml(x)}</div>`).join('')+'</div>');
  }
  if(risks.length)chunks.push('<div class="risk">'+risks.map(esc).join('；')+'</div>');
  $('agentDecision').innerHTML=chunks.join('');
}
function renderGlobalStreamSources(data){
  const rows=(data.sources_status||[]).slice(0,8);
  if(!rows.length){$('globalStreamSources').innerHTML='<span>来源状态：等待金十直连和全球源返回</span>';return}
  $('globalStreamSources').innerHTML=rows.map(x=>{
    const label=`${x.source||'来源'} · ${x.count??0}条 · ${cnEnum(x.status||'--')}`;
    const url=x.source_api||x.source_page||'';
    return url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:`<span>${esc(label)}</span>`;
  }).join('');
}
function renderGlobalStream(js){
  const data=js.data||{};
  const items=(js.items||data.items||[]).slice(0,60);
  const status=$('globalStreamStatus');
  const mode=cnEnum(data.stream_mode||js.cache_status?.status||'实时流');
  const refresh=Math.max(12,Math.min(60,Number(js.refresh_seconds||data.refresh_seconds||20)));
  globalStreamRefreshMs=refresh*1000;
  status.textContent=(items.length?items.length+' 条':'暂无快讯')+' · '+mode;
  status.className='pill '+(items.length?'good':'warn');
  renderGlobalStreamSources(data);
  if(!items.length){
    const reason=data.missing_reason||js.cache_status?.error||'当前真实来源暂未返回快讯；不会伪造新闻。';
    $('globalTickerTrack').innerHTML=`<span class="ticker-item"><b>缺失</b><span>${esc(reason)}</span></span>`;
    $('globalStream').innerHTML=`<div class="feed-item"><time>${esc(data.updated_at||'')}</time><b>暂无可展示全球快讯</b><span>${esc(reason)}</span></div>`;
    return;
  }
  const tickerItems=items.slice(0,24).map(x=>`<span class="ticker-item"><b>${esc(sourceLabelOf(x))}</b><span>${esc(x.title||'未命名快讯')}</span></span>`).join('');
  $('globalTickerTrack').innerHTML=tickerItems+tickerItems;
  $('globalStream').innerHTML=items.slice(0,18).map(x=>{
    return `<div class="feed-item ${x.is_jin10?'jin10':''}"><div class="stream-meta"><time>${esc(x.published_at||'时间缺失')}</time><i>${esc(sourceLabelOf(x))}</i><span>${esc(cnEnum(x.category||x.message_dimension||'全球快讯'))}</span></div><b>${esc(x.title||'未命名快讯')}</b><span>${esc(x.summary||'')}</span><span>来源：${esc(sourceLabelOf(x))}</span><span><b>影响说明：</b>${esc(impactNoteOf(x))}</span>${impactTagsHtml(x,'影响对象')}${sourceMetaHtml(x)}${sourceLinksHtml(x)}</div>`;
  }).join('');
}

function renderScoreExplain(row){
  const b=row?.score_breakdown||row||{};
  const contributions=Array.isArray(b.contributions)?b.contributions:[];
  const sourceRows=contributions.length?contributions:[
    ['筛选底座',row?.screening_score??b.screening_score],['基本面',row?.fundamental_score??b.fundamental_score],['实时择时',row?.technical_score??b.technical_score],['近期信息',row?.information_score??b.information_score],['量价资金',row?.fund_flow_score??b.fund_flow_score],['大盘环境',row?.market_score??row?.market_regime_score??b.market_score],
  ].filter(x=>Number.isFinite(Number(x[1]))).map(x=>({label:x[0],score:Number(x[1]),normalized_weight:null,contribution:null}));
  const lines=sourceRows.map(x=>{
    const weight=Number(x.normalized_weight),contribution=Number(x.contribution),score=Number(x.score);
    const calc=Number.isFinite(weight)&&Number.isFinite(contribution)?`${score.toFixed(1)} × ${(weight*100).toFixed(1)}% = ${contribution.toFixed(2)} 分`:`原始分 ${score.toFixed(1)}；等待本轮信号计算实际权重`;
    return `<div class="score-contribution"><b>${esc(x.label||x.key||'评分维度')}</b><small>${esc(calc)}</small></div>`;
  }).join('');
  const final=Number(row?.final_score??b.final_score??row?.final_trade_score);
  const before=Number(b.score_before_risk),deduct=Number(b.anomaly_deduction||0);
  const timing=b.timing_formula||'实时择时分 = 日K结构55% + 当日分时45%';
  const missing=(b.missing_dimensions||row?.missing_data||[]).map(cnEnum).filter(Boolean);
  const eventContext=row?.market_event_context||{};
  const eventFactors=Array.isArray(b.event_factors)?b.event_factors:(eventContext.factors||[]);
  const marketAdj=Number(b.market_event_adjustment??eventContext.market_adjustment??0);
  const infoAdj=Number(b.information_event_adjustment??eventContext.information_adjustment??0);
  const pit=eventContext.pit_input_status||{};
  const coverage=Array.isArray(eventContext.standard_factor_coverage)?eventContext.standard_factor_coverage:[];
  const pitDatasets=pit.datasets||{};
  const pitHits=Object.entries(pitDatasets).filter(([,x])=>x?.status==='available');
  const pitHtml=`<div class="event-factor-list"><div class="event-factor"><div><b>结构化事件覆盖</b><span>${eventContext.standard_factor_available??0} / ${eventContext.standard_factor_total??8} 项</span></div><small>${esc(pit.rule||'只使用不晚于决策时点、来源可追溯的快照。')}</small>${pitHits.length?pitHits.map(([key,x])=>`<small>${esc(cnEnum(key))}：${esc(x.source||'来源缺失')}｜${esc(x.available_at||'时间缺失')}｜记录 ${esc(x.record_id||'--')}</small>`).join(''):'<small>当前没有命中的结构化 PIT 快照，文字快讯仅用于有限事件解释。</small>'}</div>${coverage.length?`<details><summary>查看八项因子缺失原因</summary>${coverage.map(x=>`<div class="score-contribution"><b>${esc(x.factor_name_cn||cnEnum(x.factor_key))}</b><small>${x.status==='available'?'已进入本轮事件调整':esc(x.missing_reason||'近期没有可追溯证据')}</small></div>`).join('')}</details>`:''}</div>`;
  const factorHtml=eventFactors.length?`<div class="event-factor-list">${eventFactors.slice(0,8).map(x=>{
    const adj=Number(x.adjustment||0);const cls=adj>0?'factor-up':adj<0?'factor-down':'';const chain=(x.mapped_chain||[]).join(' → ');
    return `<div class="event-factor"><div><b>${esc(x.factor_name_cn||cnEnum(x.factor_key)||'市场事件')}</b><span class="${cls}">${adj>=0?'+':''}${adj.toFixed(2)} 分 · ${esc(x.scope||'影响范围缺失')}</span></div><small>${esc(x.explanation||'说明缺失')}</small>${chain?`<small>传导链：${esc(chain)}</small>`:''}<small>来源：${esc(x.source||'来源缺失')}｜${esc(x.published_at||'时间缺失')}｜置信度 ${Number.isFinite(Number(x.confidence))?(Number(x.confidence)*100).toFixed(0)+'%':'缺失'}</small>${x.source_ref?`<a href="${esc(x.source_ref)}" target="_blank" rel="noopener noreferrer">查看来源</a>`:''}</div>`;
  }).join('')}</div>`:'<div class="muted">近期没有进入评分的可追溯市场事件；全球快讯不会自动等同于个股利好或利空。</div>';
  $('scoreExplain').innerHTML=`<div class="mini">${esc(b.formula||'综合交易分 = 各可用维度按实际权重汇总 - 异常风险扣分')}</div><div class="mini">${esc(timing)}</div>${lines||'<span class="muted">尚无可解释的评分维度。</span>'}<div class="score-total"><b>风险前 ${Number.isFinite(before)?before.toFixed(2):'--'} 分 - 异常扣分 ${Number.isFinite(deduct)?deduct.toFixed(2):'0.00'} = 最终 ${Number.isFinite(final)?final.toFixed(2):'--'} 分</b></div><details><summary>市场事件调整：大盘 ${marketAdj>=0?'+':''}${marketAdj.toFixed(2)} 分 / 个股信息 ${infoAdj>=0?'+':''}${infoAdj.toFixed(2)} 分</summary>${pitHtml}${factorHtml}</details>${missing.length?`<div class="warn">本轮缺失：${esc(missing.join('、'))}；缺失维度不会被伪造，剩余权重重新归一化。</div>`:''}`;
}
function sectorMoney(v){
  const n=Number(v);if(!Number.isFinite(n))return'字段缺失';
  const sign=n>0?'+':'';const a=Math.abs(n);
  return sign+(a>=1e8?(n/1e8).toFixed(2)+'亿':a>=1e4?(n/1e4).toFixed(1)+'万':n.toFixed(0));
}
function setSectorFilter(value){sectorFilter=value||'all';document.querySelectorAll('.sector-filter').forEach(x=>x.classList.toggle('active',x.dataset.sectorFilter===sectorFilter));renderSectorMainline(sectorMainlineData||{})}
function setSectorWindow(value){sectorWindow=value||'interval_flow_15m';renderSectorMainline(sectorMainlineData||{})}
function sectorWindowLabel(){return ({interval_flow_5m:'近5分钟',interval_flow_15m:'近15分钟',interval_flow_30m:'近30分钟',interval_flow_60m:'近60分钟',morning_flow_change:'上午',afternoon_flow_change:'下午',net_inflow:'当日累计',recent_flow_5d_sum:'近5日'})[sectorWindow]||'所选时段'}
function sectorWindowValue(row){const value=Number(row?.[sectorWindow]);return Number.isFinite(value)?value:null}
function renderSectorMainline(js){
  sectorMainlineData=js||{};let rows=[...(js.items||[])];
  if(sectorFilter==='industry'||sectorFilter==='concept')rows=rows.filter(x=>x.board_type===sectorFilter);
  if(sectorFilter==='inflow')rows=rows.filter(x=>(sectorWindowValue(x)??0)>0).sort((a,b)=>(sectorWindowValue(b)??-Infinity)-(sectorWindowValue(a)??-Infinity));
  if(sectorFilter==='outflow')rows=rows.filter(x=>(sectorWindowValue(x)??0)<0).sort((a,b)=>(sectorWindowValue(a)??Infinity)-(sectorWindowValue(b)??Infinity));
  if(sectorFilter==='returning')rows=rows.filter(x=>x.flow_state==='资金回流').sort((a,b)=>Number(b.interval_flow_15m)-Number(a.interval_flow_15m));
  if(sectorFilter==='diverging')rows=rows.filter(x=>['高位分歧','流入放缓'].includes(x.flow_state)).sort((a,b)=>Number(a.interval_flow_15m)-Number(b.interval_flow_15m));
  const items=rows.slice(0,24);
  const status=$('sectorStatus');const cache=js.cache_status||{};
  status.textContent=`${js.session_label||'--'} · ${items.length}板块 · ${cache.status||js.quality_status||'--'}`;
  status.className='pill '+(items.length?'good':'warn');
  const main=items.filter(x=>x.stage==='主线');const lead=items[0];const rotation=js.rotation_summary||{};
  $('sectorHeadline').textContent=rotation.summary||(lead?`${main.length} 个主线板块；当前领先 ${lead.board_name}，主线分 ${Number(lead.mainline_score||0).toFixed(1)}`:'暂无可用真实板块快照');
  $('sectorMethod').textContent=(js.methodology?.intraday_change||'时间段资金变化由真实累计净流快照做差。')+' '+(js.methodology?.truth_boundary||'不等于 Level-2 主力账户识别。');
  const available=[...(js.items||[])].filter(x=>sectorWindowValue(x)!=null);
  const inflow=[...available].filter(x=>sectorWindowValue(x)>0).sort((a,b)=>sectorWindowValue(b)-sectorWindowValue(a)).slice(0,3);
  const outflow=[...available].filter(x=>sectorWindowValue(x)<0).sort((a,b)=>sectorWindowValue(a)-sectorWindowValue(b)).slice(0,3);
  const leaderText=list=>list.map(x=>`${x.board_name} ${sectorMoney(sectorWindowValue(x))}`).join('；')||'等待真实快照';
  $('sectorRotation').innerHTML=`<div><b>${esc(sectorWindowLabel())}流入</b><span>${esc(leaderText(inflow))}</span></div><div><b>${esc(sectorWindowLabel())}流出</b><span>${esc(leaderText(outflow))}</span></div><div><b>资金回流</b><span>${esc((rotation.returning_boards||[]).slice(0,4).map(x=>x.board_name).join('、')||'尚未识别')}</span></div><div><b>分歧/放缓</b><span>${esc((rotation.diverging_boards||[]).slice(0,4).map(x=>x.board_name).join('、')||'尚未识别')}</span></div>`;
  $('sectorRows').innerHTML=items.length?items.map(x=>{
    const stageClass=x.stage==='主线'?'main':x.stage==='退潮'?'weak':'';const change=Number(x.change_pct);const stateClass=['加速流入','持续流入','资金回流'].includes(x.flow_state)?'in':['持续流出','高位分歧'].includes(x.flow_state)?'out':'';
    const flowCell=v=>`<td class="${Number(v)>=0?'ok':'bad'}">${v==null?'等待快照':sectorMoney(v)}</td>`;
    return `<tr><td><div class="sector-name"><b>${esc(x.board_name||x.board_code)}</b><small>${esc(x.board_type_name||'板块')} · ${esc(x.board_code||'')}</small></div></td><td><span class="sector-stage ${stageClass}">${esc(x.stage||'观察')}</span></td><td>${Number(x.strength_score||0).toFixed(1)}</td><td>${Number(x.mainline_score||0).toFixed(1)}</td><td class="${change>=0?'ok':'bad'}">${Number.isFinite(change)?(change>0?'+':'')+change.toFixed(2)+'%':'缺失'}</td><td class="${Number(x.net_inflow)>=0?'ok':'bad'}">${sectorMoney(x.net_inflow)}</td>${flowCell(x.interval_flow_5m)}${flowCell(x.interval_flow_15m)}${flowCell(x.interval_flow_30m)}${flowCell(x.interval_flow_60m)}${flowCell(x.morning_flow_change)}${flowCell(x.afternoon_flow_change)}${flowCell(x.recent_flow_5d_sum)}<td>${esc(x.capital_phase||'近期样本不足')}</td><td><span class="flow-state ${stateClass}" title="${esc(x.flow_state_reason||x.flow_truth_boundary||'')}">${esc(x.flow_state||'等待快照')}</span></td><td>${x.net_inflow_ratio_pct==null?'缺失':Number(x.net_inflow_ratio_pct).toFixed(2)+'%'}</td><td>${x.up_count??0}/${x.down_count??0}</td><td>${x.breadth_pct==null?'缺失':Number(x.breadth_pct).toFixed(1)+'%'}</td><td>${x.history_days??0}日 / ${x.intraday_sample_count??0}点</td><td><a class="sector-link" href="${esc(x.source_url||js.source_url||'#')}" target="_blank" rel="noopener noreferrer">${esc(x.source_name||js.source_name||'来源')}</a></td></tr>`;
  }).join(''):`<tr><td colspan="20">${esc((js.missing_reasons||['当前没有真实板块资金数据']).join('；'))}</td></tr>`;
}
async function loadSectorMainline(force=false){const js=await api('/api/market/sectors/mainline?limit=50&include_concept=true&force='+force);renderSectorMainline(js);return js}
async function refreshAll(btn=null){
  if(workbenchRefreshPromise)return workbenchRefreshPromise;
  const task=withAction(btn,'刷新中','总控台已更新',async()=>{
  try{
    renderModuleCards();
    setText('scoreTime','正在更新核心状态…');
    const extraPromise=Promise.allSettled([api('/api/score/latest/'+encodeURIComponent(primarySymbol())),api('/api/macro/global-events?limit=80'),loadGlobalStream(false),api('/api/agent/market-brief?symbols='+encodeURIComponent(symbols().join(','))+'&limit=80'),api('/api/market/sectors/mainline?limit=50&include_concept=true'),api('/api/realtime-paper/signals?limit=100'),api('/api/market/event-factors/'+encodeURIComponent(primarySymbol()))]);
    const core=await Promise.allSettled([api('/api/live-broker/status'),api('/api/realtime-paper/sessions'),api('/api/trading-records?limit=30'),api('/api/data-center/status'),api('/api/live/confirm-queue'),api('/api/live/account'),api('/api/live/positions'),api('/api/auto-trading/config'),api('/api/auto-trading/readiness'),api('/api/live/position-reviews?limit=50'),api('/api/position-reviews/scheduler/status'),api('/api/realtime-paper/scheduler/status')]);
    const value=(idx,fallback={})=>core[idx].status==='fulfilled'?core[idx].value:fallback;
    const broker=value(0),sessions=value(1,{data:[]}),records=value(2,{data:[],summary:{}}),data=value(3),queue=value(4,{data:[],count:0}),liveAccount=value(5),livePositions=value(6,{data:[]}),autoConfig=value(7,{data:{}}),readiness=value(8,{gates:{}}),liveReviews=value(9,{data:[]}),reviewSchedule=value(10,{data:{}}),paperSchedule=value(11,{});
    applyAutoConfig(autoConfig.data);
    renderConfigSummary(autoConfig.data,readiness);
    renderPortfolioOverview(liveAccount,livePositions,records);
    renderPositionReviews(liveReviews.data||[],'livePositionReviews','当前没有真实持仓复核记录。');
    renderReviewSchedule(reviewSchedule);
    renderPaperScheduler(paperSchedule);
    const brokerName=broker.broker?.broker||broker.config?.broker_type||'disabled';
    const brokerStatus=broker.broker?.status||broker.status||'disabled';
    $('brokerBadge').textContent=cnEnum(brokerName)+' / '+cnEnum(brokerStatus);
    $('brokerBadge').className='pill '+(brokerStatus==='connected'?'good':brokerStatus==='disabled'?'warn':'bad');
    $('liveEnabled').textContent=broker.safety?.LIVE_TRADING_ENABLED?'已开启':'默认关闭';
    $('liveSafety').innerHTML=`券商：${esc(cnEnum(brokerName))} / ${esc(cnEnum(brokerStatus))}<br>真实交易：${broker.safety?.LIVE_TRADING_ENABLED?'开启':'关闭'}；人工确认：${broker.safety?.ORDER_CONFIRM_REQUIRED?'必须':'未要求'}；紧急停止：${broker.safety?.LIVE_KILL_SWITCH?'已开启':'关闭'}`;
    const sessList=sessions.data||[];
    const active=sessList.find(x=>['running','paused'].includes(x.status))||sessList[0]||null;
    $('paperSessions').textContent=sessList.length;
    $('recordCount').textContent=records.summary?.rows_count??(records.data||[]).length;
    $('confirmCount').textContent=queue.count??(queue.data||[]).length??0;
    const tableCount=Object.keys(data.trading_store?.tables||{}).length;
    $('dataHealth').textContent=tableCount?tableCount+' 表':'待检查';
    await loadSessionDetails(active).catch(e=>{$('auditLog').textContent='模拟账户详情读取失败：'+e});
    renderWorkflow({cfg:autoConfig.data});
    $('auditLog').textContent='核心状态已更新 '+new Date().toLocaleTimeString()+'；正在加载评分、信息和板块…';
    const extra=await extraPromise;
    const extraValue=(idx,fallback={})=>extra[idx].status==='fulfilled'?extra[idx].value:fallback;
    const score=extraValue(0),macro=extraValue(1,{items:[]}),agent=extraValue(3,{data:{}}),sectors=extraValue(4,{items:[],missing_reasons:['板块服务暂不可用']}),signalData=extraValue(5,{data:[]}),eventData=extraValue(6,{data:{}});
    renderGlobalFeed(macro);renderAgentDecision(agent);renderSectorMainline(sectors);
    const signalRows=signalData.data||[];
    const liveSignal=signalRows.find(x=>String(x.symbol||'')===primarySymbol())||signalRows[0];
    const latest={...(liveSignal||score.data||{})};
    if(!latest.market_event_context)latest.market_event_context=eventData.data||{};
    latest.score_breakdown={...(latest.score_breakdown||{}),event_factors:(latest.score_breakdown?.event_factors||eventData.data?.factors||[]),market_event_adjustment:(latest.score_breakdown?.market_event_adjustment??eventData.data?.market_adjustment??0),information_event_adjustment:(latest.score_breakdown?.information_event_adjustment??eventData.data?.information_adjustment??0)};
    const s=Number(latest.final_score??latest.final_trade_score);
    $('decisionScore').textContent='评分 '+(Number.isFinite(s)?s.toFixed(1):'--');$('decisionAction').textContent=liveSignal?cnAction(liveSignal.action):(Number.isFinite(s)?s>=70?'待确认买入':s>=55?'继续观察':'暂时回避':'等待评分');$('scoreTime').textContent=latest.timestamp||latest.decision_time||new Date().toLocaleTimeString();
    setScore('tech',latest.technical_score);setScore('fund',latest.fundamental_score);setScore('info',latest.information_score);setScore('market',latest.market_regime_score??latest.market_score);
    renderScoreExplain(latest);
    const failed=[...core,...extra].filter(x=>x.status==='rejected');
    $('auditLog').textContent='最后刷新 '+new Date().toLocaleTimeString()+(failed.length?'；部分模块失败 '+failed.length+' 项':'；全部模块完成')+'\\n'+JSON.stringify({broker:broker.safety,readiness:readiness.gates,paper_scheduler:{enabled:paperSchedule.enabled,running:paperSchedule.running,active_sessions:paperSchedule.active_sessions,market_session:paperSchedule.market_session},active_session:activeSessionId,records:(records.data||[]).length},null,2);
    return {ok:true,failed:failed.length};
  }catch(e){$('auditLog').textContent='刷新失败：'+e;throw e}
  });
  workbenchRefreshPromise=task;
  try{return await task}finally{if(workbenchRefreshPromise===task)workbenchRefreshPromise=null}
}
async function oneClickConfig(btn=null){return withAction(btn,'配置中','组合配置已生成',async()=>{
  const js=await api('/api/auto-trading/config/one-click',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(collectAutoConfig())});
  applyAutoConfig(js.data);renderConfigSummary(js.data,js.readiness);$('auditLog').textContent=JSON.stringify(js,null,2);await refreshAll();return js;
})}
async function saveAutoConfig(btn=null){return withAction(btn,'保存中','配置已保存',async()=>{
  const js=await api('/api/auto-trading/config',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(collectAutoConfig())});
  applyAutoConfig(js.data);$('auditLog').textContent=JSON.stringify(js,null,2);await refreshAll();return js;
})}
async function loadLatestScreenerConfig(btn=null){return withAction(btn,'读取中','已载入最近筛选',async()=>{
  const body=collectAutoConfig();delete body.symbols;body.use_latest_screener=true;
  const js=await api('/api/auto-trading/config/one-click',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  applyAutoConfig(js.data);renderConfigSummary(js.data,js.readiness);$('auditLog').textContent=JSON.stringify(js,null,2);await refreshAll();return js;
})}
async function startPaper(btn=null){return withAction(btn,'启动中','实时模拟已启动',async()=>{
  const js=await api('/api/auto-trading/start-paper',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(collectAutoConfig())});
  activeSessionId=sessionIdOf(js.session)||activeSessionId;
  $('auditLog').textContent=(js.account_preserved?'已恢复当前模拟账户，持仓、成交和资金均已保留。\\n':'')+(js.warning?js.warning+'\\n':'')+JSON.stringify(js,null,2);
  await refreshAll();openModule('realtime');return js;
})}
async function manualTick(){
  if(!activeSessionId){$('auditLog').textContent='请先启动或恢复一个实时模拟 session。';return}
  const cfg=collectAutoConfig();
  const js=await api('/api/realtime-paper/tick',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({session_id:activeSessionId,symbol:primarySymbol(),quote_hydrate_request:true,...cfg})});
  $('auditLog').textContent=JSON.stringify(js,null,2);refreshAll();
}
async function runConfigBacktest(btn=null){return withAction(btn,'回测中','回测已完成',async()=>{
  const cfg=collectAutoConfig();const sym=(cfg.symbols||[])[0]||'300750';
  const js=await api('/api/backtest/v323/run',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbol:sym,symbols:[sym],limit:520,use_auto_config:true,auto_trading_config:cfg,source_page:'auto-trading'})});
  $('auditLog').textContent=JSON.stringify(js,null,2);
  openModule('backtest','/backtest?symbol='+encodeURIComponent(sym)+(js.run_id?'&run_id='+encodeURIComponent(js.run_id):''));return js;
})}
async function killLive(btn=null){return withAction(btn,'执行中','实盘 Kill 已开启',async()=>{const js=await api('/api/live/kill-switch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:true})});$('auditLog').textContent=JSON.stringify(js,null,2);await refreshAll();return js})}
async function previewOrder(){
  const body={...collectAutoConfig(),symbol:$('liveSymbol').value.trim(),side:$('liveSide').value,quantity:Number($('liveQty').value||0),limit_price:Number($('livePrice').value||0)||null,order_type:'limit',source_page:'auto-trading'};
  const js=await api('/api/live/orders/preview',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  $('livePreviewSummary').innerHTML=renderLivePreviewSummary([{symbol:body.symbol,preview:js}]);
  $('auditLog').textContent=JSON.stringify(js,null,2);refreshAll();
}
function renderLivePreviewSummary(rows){
  if(!rows.length)return '暂无预检查结果。';
  return rows.map(row=>{
    const r=row.preview||row.result||row||{};
    const ok=!!(r.ok||r.approved||r.status==='needs_confirmation');
    const reason=r.status_reason||r.reason||r.message||r.risk?.reason||r.data?.risk?.reason||(ok?'通过或等待人工确认':'未通过');
    return `<div><b>${esc(row.symbol||r.symbol||'--')}</b> · <span class="${ok?'ok':'warn'}">${esc(r.status||(ok?'通过/待确认':'阻断'))}</span> · ${esc(reason)}</div>`;
  }).join('');
}
async function previewOrderBatch(){
  const cfg=collectAutoConfig();
  const body={...cfg,symbols:cfg.symbols,side:$('liveSide').value,quantity:Number($('liveQty').value||0),limit_price:Number($('livePrice').value||0)||null,order_type:'limit',source_page:'auto-trading'};
  const js=await api('/api/live/orders/preview-batch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  const rows=(js.data||[]).map(x=>({symbol:x.symbol,preview:x.preview||x.result||x}));
  $('livePreviewSummary').innerHTML=renderLivePreviewSummary(rows);
  $('auditLog').textContent=JSON.stringify(js,null,2);
  refreshAll();
}
renderModuleCards();
refreshAll();
startGlobalStreamLoop();
</script>
</body>
</html>"""
