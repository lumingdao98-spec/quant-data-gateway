from __future__ import annotations


def build_auto_trading_workbench_ui() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V3.28 自动交易总控台</title><!-- V3.26/V3.27 自动交易总控台兼容入口 -->
<style>
:root{
  --bg:#07111f;--panel:#101a2c;--panel2:#152238;--line:#263955;--text:#e6f0ff;--muted:#92a6c4;
  --blue:#3b82f6;--cyan:#22d3ee;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;
  --shadow:0 22px 60px rgba(0,0,0,.32)
}
*{box-sizing:border-box}html,body{min-height:100%;margin:0}body{background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}button,input,select,textarea{font:inherit}select{background:#0d1728;border:1px solid #2f4364;border-radius:8px;color:#e5efff;padding:7px 9px;max-width:100%}a{color:inherit;text-decoration:none}
.app{display:grid;grid-template-columns:228px minmax(0,1fr);min-height:100vh;max-width:100vw;overflow-x:hidden}.app>section{min-width:0;max-width:100%;overflow:hidden}
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
.quick-config{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;align-items:center;border:1px solid #315077;background:#0b1728;border-radius:12px;padding:11px 12px}.quick-config>div{min-width:0}.quick-config b{display:block;margin-bottom:4px}.quick-config span{display:block;color:var(--muted);font-size:12px;line-height:1.5;overflow-wrap:anywhere}.quick-config .row{justify-content:flex-start}.home-config-details{margin-top:10px;border:1px solid #2f4364;border-radius:12px;background:#0b1628}.home-config-details>summary{cursor:pointer;padding:10px 12px;color:#bfdbfe;font-weight:900}.home-config-body{padding:0 12px 12px}
.module-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.module{display:block;background:#0d1728;padding:12px;cursor:pointer}.module:hover{border-color:#4b8cf7;background:#12213a}.module b{display:block;margin-bottom:5px}.module span{display:block;color:var(--muted);font-size:12px;line-height:1.45;overflow-wrap:anywhere}
.strategy-catalog{display:grid;grid-template-columns:1fr;gap:7px;max-height:226px;overflow:auto;padding-right:3px}.strategy-chip{display:grid;grid-template-columns:auto 1fr;gap:8px;border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:8px;cursor:pointer}.strategy-chip input{margin-top:3px}.strategy-chip b{display:block;font-size:13px}.strategy-chip span{display:block;color:var(--muted);font-size:11px;line-height:1.35;margin-top:2px}.strategy-chip.on{border-color:#22d3ee;background:#092536}
.strategy-param-wrap{max-height:250px;overflow:auto;border:1px solid #2f4364;border-radius:12px}.strategy-param{width:100%;border-collapse:collapse;min-width:820px;font-size:12px}.strategy-param th,.strategy-param td{border-bottom:1px solid #243653;padding:7px;text-align:left;vertical-align:middle}.strategy-param th{position:sticky;top:0;background:#12213a;color:#9fd4ff;z-index:1}.strategy-param input,.strategy-param select{background:#0d1728;border:1px solid #2f4364;color:#e5efff;border-radius:8px;padding:6px;width:100%}
.advanced-box{border:1px solid #2f4364;border-radius:12px;background:#0b1628;margin:10px 0}.advanced-box>summary{cursor:pointer;padding:10px 12px;color:#bfdbfe;font-weight:900}.advanced-box>.advanced-body{padding:0 10px 10px}.score-explain{margin-top:12px;border:1px solid #315077;border-radius:12px;background:#0b1628}.score-explain>summary{cursor:pointer;padding:10px 12px;font-weight:900;color:#bfdbfe}.score-explain-body{padding:0 12px 12px;display:grid;gap:7px}.score-contribution{display:grid;grid-template-columns:minmax(78px,1fr) auto;gap:8px;border-bottom:1px solid #213552;padding:6px 0;font-size:12px}.score-contribution:last-child{border-bottom:0}.score-contribution small{color:var(--muted);overflow-wrap:anywhere}.score-total{border-top:1px solid #3b82f6;padding-top:8px;color:#dbeafe}.recommend-box{border:1px solid #166534;background:#092319;border-radius:12px;padding:10px 12px;color:#bbf7d0;font-size:12px;line-height:1.55;margin-bottom:10px;overflow-wrap:anywhere}.event-factor-list,.position-review-list{display:grid;gap:7px;margin-top:9px}.event-factor,.position-review{border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:9px;min-width:0}.event-factor>div,.position-review>div{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.event-factor b,.position-review b{overflow-wrap:anywhere}.event-factor small,.position-review small{display:block;color:var(--muted);line-height:1.45;margin-top:4px;overflow-wrap:anywhere}.event-factor a{display:inline-flex;color:#93c5fd;font-size:11px;margin-top:5px}.factor-up{color:#86efac}.factor-down{color:#fecaca}.review-action{font-size:11px;border:1px solid #315077;border-radius:999px;padding:3px 7px;white-space:nowrap}.review-action.exit{border-color:#7f1d1d;color:#fecaca}.review-action.reduce{border-color:#854d0e;color:#fcd34d}.review-action.hold{border-color:#166534;color:#86efac}
.dimension-grid{display:grid;gap:8px}.dimension-row{border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:9px;min-width:0}.dimension-row>div{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.dimension-row small{display:block;color:var(--muted);line-height:1.45;margin-top:4px;overflow-wrap:anywhere}.dimension-state{font-size:11px;border:1px solid #315077;border-radius:999px;padding:3px 7px;white-space:nowrap}.dimension-state.ready{border-color:#166534;color:#86efac}.dimension-state.blocked{border-color:#7f1d1d;color:#fecaca}.dimension-state.optional{border-color:#854d0e;color:#fcd34d}.dimension-refresh{margin-top:7px;border:1px solid #315077;background:#14243c;color:#bfdbfe;border-radius:7px;padding:5px 8px;font-size:11px;font-weight:800;cursor:pointer}.dimension-refresh:disabled{opacity:.55;cursor:wait}
.bars{display:grid;gap:10px}.barline{height:8px;border-radius:99px;background:#1d2d49;overflow:hidden}.barline i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue));width:0%}.feed{display:grid;gap:8px;max-height:360px;overflow:auto}.feed.compact{max-height:220px}.feed-item{border:1px solid #2f4364;background:#0d1728;border-radius:10px;padding:9px}.feed-item time{color:#93c5fd;font-size:12px}.feed-item b{display:block;margin:4px 0;line-height:1.35}.feed-item span{display:block;color:var(--muted);font-size:12px;line-height:1.45;overflow-wrap:anywhere}.ticker-wrap{margin-top:10px;border:1px solid #315077;background:#071426;border-radius:12px;overflow:hidden;min-height:42px;display:flex;align-items:center}.ticker-label{flex:0 0 auto;color:#67e8f9;font-weight:1000;font-size:12px;padding:0 10px}.ticker-rail{min-width:0;flex:1;overflow:hidden}.ticker-track{display:flex;gap:22px;white-space:nowrap;animation:globalTicker 46s linear infinite;will-change:transform}.ticker-wrap.paused .ticker-track{animation-play-state:paused}.ticker-item{display:inline-flex;align-items:center;gap:8px;color:#dbeafe;font-size:13px;max-width:560px}.ticker-item b{color:#fcd34d}.ticker-item span{overflow:hidden;text-overflow:ellipsis}.stream-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:10px 0 8px}.stream-list .feed-item{border-left:3px solid #22d3ee}.stream-list .feed-item.jin10{border-left-color:#f97316}.stream-meta{display:flex;gap:8px;flex-wrap:wrap;color:#93c5fd;font-size:12px}.stream-meta i{font-style:normal;color:#fcd34d}.source-strip{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.source-strip span{border:1px solid #2f4364;background:#0b1728;border-radius:999px;padding:5px 8px;color:#b7c9e6;font-size:11px;max-width:100%;overflow-wrap:anywhere}@keyframes globalTicker{from{transform:translateX(0)}to{transform:translateX(-55%)}}.log{background:#0b1220;border:1px solid #2f4364;border-radius:12px;padding:10px;font-family:Consolas,monospace;font-size:12px;color:#b7c9e6;white-space:pre-wrap;overflow:auto;max-height:260px;overflow-wrap:anywhere}
.source-strip a{border:1px solid #2f4364;background:#0b1728;border-radius:999px;padding:5px 8px;color:#93c5fd;font-size:11px;max-width:100%;overflow-wrap:anywhere}.feed-item .impact-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}.impact-tag{border:1px solid #315077;background:#10233a;color:#bfdbfe;border-radius:999px;padding:3px 7px;font-size:11px}.source-link{display:inline-flex!important;width:auto!important;margin-top:7px;color:#93c5fd!important;font-size:12px!important}.feed-item .source-note{color:#fcd34d!important;font-size:11px!important}
.mini-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}.mini-table th,.mini-table td{border-bottom:1px solid #243653;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}.mini-table th{background:#12213a;color:#9fd4ff}
.sector-panel{margin-bottom:14px;min-width:0;max-width:100%}.sector-summary{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;margin-bottom:10px;min-width:0}.sector-rotation{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:0 0 10px}.sector-rotation>div{border:1px solid #29405f;background:#0d1a2e;padding:8px 10px;border-radius:7px;min-width:0}.sector-rotation b,.sector-rotation span{display:block;overflow-wrap:anywhere}.sector-rotation span{color:var(--muted);font-size:11px;line-height:1.45;margin-top:3px}.sector-table-wrap{overflow:auto;max-width:100%;max-height:280px;border:1px solid #2f4364;border-radius:8px}.sector-table{width:100%;border-collapse:collapse;min-width:1800px;font-size:12px}.sector-table th,.sector-table td{padding:9px 10px;border-bottom:1px solid #243653;text-align:right;white-space:nowrap}.sector-table th{position:sticky;top:0;background:#12213a;color:#9fd4ff;z-index:1}.sector-table th:first-child,.sector-table td:first-child,.sector-table th:nth-child(2),.sector-table td:nth-child(2){text-align:left}.sector-name{display:grid;gap:2px}.sector-name small{color:var(--muted)}.sector-stage,.flow-state{display:inline-flex;border:1px solid #315077;border-radius:999px;padding:3px 7px;color:#bfdbfe}.sector-stage.main,.flow-state.in{border-color:#166534;background:#0d2b1c;color:#86efac}.sector-stage.weak,.flow-state.out{border-color:#7f1d1d;background:#2a1116;color:#fecaca}.sector-link{color:#93c5fd}.sector-filter.active{background:#2563eb}.sector-method{color:var(--muted);font-size:11px;line-height:1.5;overflow-wrap:anywhere}@media(max-width:1050px){.sector-rotation{grid-template-columns:repeat(2,minmax(0,1fr))}}
.iframe-shell{position:fixed;top:0;right:0;bottom:0;left:228px;width:calc(100vw - 228px);max-width:none;min-width:0;background:#07111f;z-index:40;display:grid;grid-template-rows:56px minmax(0,1fr);transform:translateX(104%);transition:transform .2s ease;border-left:1px solid var(--line);box-shadow:-20px 0 60px rgba(0,0,0,.45);overflow:hidden}
.iframe-shell.open{transform:translateX(0)}.iframe-head{display:flex;align-items:center;gap:10px;padding:0 14px;background:#0b1424;border-bottom:1px solid var(--line);min-width:0}.iframe-head b{font-size:17px;white-space:nowrap}.iframe-head .grow{flex:1;min-width:0}.iframe-head .pill{max-width:min(52vw,720px)}.workspace-frame{width:100%;height:100%;min-width:0;border:0;background:#07111f;display:block}.iframe-empty{display:grid;place-items:center;color:var(--muted)}
.agent-box{border:1px solid #315077;background:linear-gradient(135deg,#0d1728,#10233a);border-radius:12px;padding:12px;line-height:1.6;font-size:13px}.agent-box b{display:block;color:#dbeafe;margin-bottom:5px}
.agent-decision{margin-top:10px;border:1px solid #2f4364;background:#081626;border-radius:12px;padding:10px;font-size:13px;line-height:1.55;overflow-wrap:anywhere;max-height:270px;overflow:auto}.agent-decision b{display:block;color:#dbeafe;margin-bottom:5px}.agent-decision ul{margin:7px 0 0 18px;padding:0}.agent-decision li{margin:3px 0;color:#c8d8ee}.agent-decision .risk{color:#fcd34d;margin-top:7px}
.agent-evidence-list{display:grid;gap:7px;margin-top:9px}.agent-evidence{border:1px solid #2f4364;background:#0b1728;border-radius:10px;padding:8px}.agent-evidence time{display:block;color:#93c5fd;font-size:11px}.agent-evidence strong{display:block;margin:3px 0;color:#dbeafe}.agent-evidence small{display:block;color:#b7c9e6;line-height:1.45}.agent-evidence a{display:inline-flex;margin-top:6px;color:#93c5fd;font-size:12px}.agent-evidence .impact-row{margin-top:6px}
.source-meta{display:grid;gap:3px;margin-top:6px;color:#b7c9e6;font-size:12px;line-height:1.45}.source-meta a{color:#93c5fd}.source-policy{border:1px solid #315077;background:#081626;border-radius:10px;padding:8px;margin:8px 0;color:#c8d8ee;font-size:12px;line-height:1.55}.impact-summary{border:1px solid #315077;background:#0b1d30;border-radius:10px;padding:7px;margin-top:7px;color:#dbeafe;font-size:12px;line-height:1.5}.impact-summary b{display:inline;color:#bfdbfe;margin:0}.symbol-impact-card{border-left:3px solid #60a5fa}.symbol-impact-card.none{border-left-color:#64748b}.source-link-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:7px}.source-link-row a,.source-link-row span{display:inline-flex!important;border:1px solid #2f4364;background:#0d1728;border-radius:999px;padding:4px 8px;font-size:11px!important;color:#93c5fd!important}.feed-item a.source-link{border:1px solid #2f4364;background:#0d1728;border-radius:999px;padding:4px 8px}.feed-item .impact-summary{margin-top:8px}
.dashboard-fold{margin-top:9px;border:1px solid #2f4364;border-radius:10px;background:#0b1628;overflow:hidden}.dashboard-fold>summary{cursor:pointer;padding:9px 11px;color:#bfdbfe;font-size:12px;font-weight:900;list-style-position:inside}.dashboard-fold>.dashboard-fold-body{padding:0 10px 10px}.dashboard-fold .mini-table{margin-top:8px}.dashboard-fold[open]>summary{border-bottom:1px solid #243653;margin-bottom:9px}
.home-internal-state{display:none!important}.home-overview-details{margin-top:10px;border:1px solid #2f4364;border-radius:10px;background:#0b1628;overflow:hidden}.home-overview-details>summary{cursor:pointer;padding:9px 11px;color:#bfdbfe;font-size:12px;font-weight:900}.home-overview-details[open]>summary{border-bottom:1px solid #243653}.home-overview-details>.home-overview-body{padding:10px}.home-overview-details .feed{max-height:220px}.home-overview-note{color:var(--muted);font-size:12px;line-height:1.55;overflow-wrap:anywhere}.sector-table-details{margin-top:10px}.sector-table-details>summary{cursor:pointer;color:#93c5fd;font-size:12px;font-weight:900;padding:7px 2px}.grid-main>.stack:empty{display:none}
.broker-setup-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.broker-fields{display:none}.broker-fields.active{display:block}.setup-result{display:grid;gap:7px;margin-top:10px}.setup-result ul{margin:4px 0 0;padding-left:20px;color:var(--muted);line-height:1.55}.broker-capabilities{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:7px;margin-top:8px}.broker-capability{border:1px solid #2f4364;background:#0c1728;border-radius:8px;padding:8px;min-width:0}.broker-capability b{display:block;font-size:11px;color:#8fb5e8;margin-bottom:4px}.broker-capability span{display:block;font-size:12px;line-height:1.4;overflow-wrap:anywhere}.setup-template{max-height:190px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;border:1px solid #2f4364;border-radius:10px;padding:10px;color:#b9d4f8;font-size:11px;line-height:1.5}.setup-links{display:flex;gap:7px;flex-wrap:wrap}.setup-links a{color:#93c5fd;border:1px solid #315077;border-radius:8px;padding:6px 8px;font-size:11px}
@media(max-width:1360px){.app{grid-template-columns:84px 1fr}.brand span,.nav span,.side-foot{display:none}.nav button,.nav a{justify-content:center;padding:12px}.iframe-shell{left:84px;width:calc(100vw - 84px);max-width:none}.hero,.grid-main{grid-template-columns:1fr}.hero>.panel:nth-child(2)>.panel-b{max-height:460px}.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.flow{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:820px){.app{grid-template-columns:1fr}.side{display:none}.iframe-shell{left:0;max-width:100vw}.top{position:static;height:auto;min-height:58px;padding:10px 12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}.top h1{flex:1 0 100%;font-size:17px;line-height:1.3}.top .pill.good{display:none}.top #brokerBadge{order:2;max-width:calc(100% - 8px)}.top .grow{display:none}.top .btn{padding:8px 10px}.hero,.grid-main,.flow,.kpis,.split,.check-grid,.module-grid{grid-template-columns:1fr}.main{padding:12px}.iframe-shell{grid-template-rows:58px 1fr}}
.score-policy{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin-bottom:12px}.score-policy span{border:1px solid #2f4364;background:#0d1728;border-radius:8px;padding:7px;text-align:center;color:var(--muted);font-size:11px;line-height:1.3}.score-policy b{display:block;color:#dbeafe;font-size:14px}.barline i.excluded{background:#64748b;opacity:.55}
@media(max-width:1360px) and (min-width:1051px){.hero{grid-template-columns:minmax(0,1.25fr) minmax(360px,.9fr)}.grid-main{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:1050px){.grid-main{grid-template-columns:1fr}}
@media(max-width:820px){.score-policy{grid-template-columns:repeat(2,minmax(0,1fr))}}
.sector-link{color:#67e8f9!important;font-weight:800;text-decoration:underline;text-underline-offset:3px}.sector-link:hover{color:#ecfeff!important}
.global-market-panel{margin-bottom:14px}.global-market-summary{display:grid;grid-template-columns:210px minmax(0,1fr);gap:14px;align-items:center}.global-market-score{border-right:1px solid var(--line);padding-right:14px}.global-market-score b{display:block;font-size:28px;margin:4px 0}.global-market-score span,.global-market-score small{display:block;color:var(--muted);font-size:12px;line-height:1.45;overflow-wrap:anywhere}.global-focus-select{max-width:180px;background:#0d1728;border:1px solid #315077;border-radius:8px;color:#dbeafe;padding:7px 9px;font-size:12px}.global-market-evidence{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.global-market-item{min-width:0;border-left:3px solid #22d3ee;padding:5px 8px;background:#0d1728}.global-market-item.industry{border-left-color:#f59e0b}.global-market-item b,.global-market-item span,.global-market-item small{display:block;overflow-wrap:anywhere}.global-market-item span{font-size:12px;margin:3px 0}.global-market-item small{color:var(--muted);font-size:11px;line-height:1.4}.global-market-role{display:inline-flex!important;width:max-content;padding:2px 6px;border:1px solid #31527d;border-radius:4px;color:#bfdbfe!important;margin-bottom:4px}.global-market-item.industry .global-market-role{border-color:#92400e;color:#fbbf24!important}.global-market-item a{display:inline-flex;color:#67e8f9;font-size:11px;margin-top:4px;text-decoration:underline}.global-market-policy{margin-top:9px;color:var(--muted);font-size:11px;line-height:1.5}.global-market-policy summary{cursor:pointer;color:#bfdbfe;font-weight:800}@media(max-width:1100px){.global-market-summary{grid-template-columns:1fr}.global-market-score{border-right:0;border-bottom:1px solid var(--line);padding:0 0 10px}.global-market-evidence{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:640px){.global-market-evidence{grid-template-columns:1fr}.global-focus-select{max-width:100%}}
.capital-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px}.capital-card{border:1px solid #2f4364;background:#0d1728;border-radius:9px;padding:9px;min-width:0}.capital-card b,.capital-card span,.capital-card small{display:block;overflow-wrap:anywhere}.capital-card b{font-size:15px;margin:3px 0}.capital-card span,.capital-card small{font-size:11px;line-height:1.45;color:var(--muted)}.capital-links{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}.capital-links a{color:#93c5fd;text-decoration:underline;font-size:11px}.capital-window{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-top:7px}.capital-window span{border:1px solid #29405f;border-radius:6px;padding:5px 2px;text-align:center;color:#cfe1ff;font-size:10px}.capital-window b{font-size:10px!important;line-height:1.25;white-space:nowrap;overflow-wrap:normal!important;margin:2px 0 0}@media(max-width:640px){.capital-grid{grid-template-columns:1fr}.capital-window{grid-template-columns:repeat(2,minmax(0,1fr))}}
.score-trend{border:1px solid #2f4364;background:#091425;border-radius:9px;padding:8px;margin-bottom:0}.score-trend-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}.score-trend-head b{font-size:12px}.score-trend-head span{color:var(--muted);font-size:11px;overflow-wrap:anywhere}.score-trend canvas{display:block;width:100%;height:84px}.score-legend{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:10px}.score-legend i{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:3px}.grid-main>.stack{display:contents}.home-score-layout{display:grid;grid-template-columns:minmax(300px,.9fr) minmax(0,1.1fr);gap:14px;align-items:start}.home-score-primary,.home-score-secondary{display:grid;gap:8px;align-content:start;min-width:0}#homeScorePanel{grid-column:1/-1;grid-row:1}#homeStatusPanel{grid-column:1;grid-row:2}#homePaperPanel{grid-column:2;grid-row:2}#homePortfolioPanel{grid-column:3;grid-row:2}#homeScorePanel .bars{grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}#homeScorePanel .bars>div{min-width:0;border:1px solid #243653;background:#0b1628;border-radius:8px;padding:6px}#homeScorePanel .bars .row{font-size:11px;gap:4px}#homeScorePanel .barline{height:5px;margin-top:4px}#homeScorePanel .score-explain{margin-top:0}
@media(max-width:1360px) and (min-width:1051px){#homeScorePanel{grid-column:1/-1;grid-row:1}#homeStatusPanel{grid-column:1;grid-row:2}#homePaperPanel{grid-column:2;grid-row:2}#homePortfolioPanel{grid-column:1/-1;grid-row:3}}
@media(max-width:1050px){.home-score-layout{grid-template-columns:1fr}#homeScorePanel,#homeStatusPanel,#homePaperPanel,#homePortfolioPanel{grid-column:1;grid-row:auto}}
@media(max-width:720px){#homeScorePanel .bars{grid-template-columns:repeat(2,minmax(0,1fr))}}
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
      <button type="button" data-module="broker" onclick="openModule('broker')"><b>接</b><span>券商配置</span></button>
      <button type="button" data-module="records" onclick="openModule('records')"><b>录</b><span>交易记录</span></button>
      <button type="button" data-module="data" onclick="openModule('data')"><b>数</b><span>数据中心</span></button>
      <button type="button" data-module="docs" onclick="openModule('docs')"><b>?</b><span>中文 API</span></button>
    </nav>
    <div class="side-foot">研究辅助，不构成投资建议。真实交易默认关闭，必须券商授权、风控通过、人工确认后才允许进入下单流程。</div>
  </aside>
  <section>
    <header class="top">
      <h1>V3.28 自动交易总控台</h1>
      <span class="pill good">首页总览 + 右侧覆盖模块</span>
      <span class="pill" id="brokerBadge">券商状态读取中...</span>
      <div class="grow"></div>
      <button class="btn ghost" onclick="openModule('quote')">行情</button>
      <button class="btn ghost" onclick="openModule('realtime')">模拟</button>
      <button class="btn ghost" onclick="openModule('broker')">券商配置</button>
      <button class="btn red" onclick="killLive(this)">实盘 Kill</button>
      <button class="btn primary" onclick="refreshAll(this)">刷新</button>
    </header>
    <main class="main">
      <section class="hero">
        <div class="panel">
          <div class="panel-h"><span>交易工作流</span><span class="muted">筛选 → 配置 → 回测 → 模拟 → 实盘确认</span></div>
          <div class="panel-b">
            <div class="notice">这个首页只做总览和关键动作。点击左侧模块后，会在右侧打开完整功能页；关闭或切换模块时会释放旧页面，避免越用越慢。原有功能和独立页面入口全部保留。</div>
            <div class="flow" style="margin-top:12px">
              <div class="step"><strong><i>1</i>先筛选</strong><p>股票池、四面评分、风险标签和策略适配是自动交易方向的来源。</p><div class="row"><button class="btn" onclick="openModule('screener')">打开筛选</button></div></div>
              <div class="step"><strong><i>2</i>一键配置</strong><p>从筛选结果生成策略组合、仓位、止损止盈、最大回撤和事件监控。</p><div class="row"><button class="btn green" onclick="oneClickConfig(this)">一键配置</button></div></div>
              <div class="step"><strong><i>3</i>先验证</strong><p>同一套配置先跑回测，再进入实时模拟，不直接上真实账户。</p><div class="row"><button class="btn" onclick="runConfigBacktest(this)">配置回测</button><button class="btn" onclick="startPaper(this)">启动模拟</button></div></div>
              <div class="step"><strong><i>4</i>后实盘</strong><p>QMT/PTrade 默认关闭；真实订单必须预检查、风控、确认队列和 kill switch。</p><div class="row"><button class="btn red" onclick="openModule('live')">实盘确认</button></div></div>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-h"><span>联网智能辅助 · 多角色证据复核</span><button class="btn" onclick="loadAgentBrief(true)">联网复核</button></div>
          <div class="panel-b">
            <div class="agent-box"><b>用途边界</b>只读取真实可追溯数据源和缓存；没有数据时显示缺失/过期，不生成假新闻。当前用于解释宏观、全球商品、非农/CPI/FOMC 等客观因素可能带来的风险，不直接等于买卖建议。</div>
            <div class="agent-decision" id="agentDecision"><b>多角色复核加载中...</b><span>正在分别核验评分技术、基本面、信息面、资金主线和大盘环境，再交给独立风控裁决。</span></div>
            <details class="home-overview-details">
              <summary>展开全球快讯、来源与宏观证据</summary>
              <div class="home-overview-body">
                <div class="home-overview-note">首页只显示智能摘要；这里展开后可核对原始快讯、来源链接、影响对象和事件时效。</div>
                <div class="ticker-wrap" id="globalTicker"><div class="ticker-label">7x24 快讯</div><div class="ticker-rail"><div class="ticker-track" id="globalTickerTrack"><span class="ticker-item"><b>等待</b><span>正在读取金十/全球要闻缓存...</span></span></div></div></div>
                <div class="stream-head"><b>全球实时要闻流</b><span class="row"><span class="pill" id="globalStreamStatus">等待加载</span><button class="btn" onclick="loadGlobalStream(true)">联网刷新</button><button class="btn" id="tickerPauseBtn" onclick="toggleGlobalTicker()">暂停轮播</button></span></div>
                <div class="source-strip" id="globalStreamSources"><span>金十直连状态等待中</span></div>
                <div class="feed compact stream-list" id="globalStream"><div class="feed-item"><b>等待加载全球快讯...</b><span>优先使用金十/金十期货、东方财富、华尔街见闻、财联社等真实来源；不可用时显示缺失原因。</span></div></div>
                <div class="stream-head"><b>宏观事件观察</b><span class="muted">非农 / CPI / FOMC / 商品 / 地缘</span></div>
                <div class="feed compact" id="macroFeed"><div class="feed-item"><b>等待加载全球信息面...</b><span>会优先使用缓存，手动联网刷新可能更慢。</span></div></div>
              </div>
            </details>
          </div>
        </div>
      </section>

      <section class="panel global-market-panel">
        <div class="panel-h"><span>所选板块的全球参照</span><span class="row"><select id="globalSectorFocus" class="global-focus-select" aria-label="海外参照行业" onchange="changeGlobalSectorFocus(this.value)"><option value="">按当前股票自动识别</option><option value="半导体">半导体</option><option value="光伏">光伏</option><option value="锂电池">锂电池/新能源车</option><option value="AI">人工智能/软件</option><option value="互联网">互联网平台</option><option value="医药">医药/生物科技</option><option value="银行">银行/金融</option><option value="黄金">黄金/贵金属</option><option value="能源">能源/油气</option><option value="有色材料">材料/有色/化工</option><option value="军工">工业/军工</option><option value="交通运输">交通运输</option><option value="可选消费">可选消费</option><option value="食品饮料">食品饮料/农业</option><option value="公用事业">公用事业/核能</option><option value="房地产">房地产/建筑</option></select><button class="btn" onclick="changeGlobalSectorFocus($('globalSectorFocus').value,this)">应用参照</button><span class="pill" id="globalMarketStatus">等待行业映射</span><button class="btn" onclick="loadGlobalMarketSentiment(true,this)">刷新全球行情</button></span></div>
        <div class="panel-b">
          <div class="global-market-summary">
            <div class="global-market-score"><span id="globalMarketFocus">当前股票 · 行业识别中</span><b id="globalMarketScore">--</b><small id="globalMarketLabel">按行业选择海外基准，并按各市场开盘时间分别判断</small></div>
            <div class="global-market-evidence" id="globalMarketEvidence"><div class="global-market-item"><b>等待行情</b><small>半导体、光伏、锂电、金融等使用不同海外参照，不会统一套用费城半导体。</small></div></div>
          </div>
          <details class="global-market-policy"><summary>查看行业映射、计分边界与相关性去重</summary><div id="globalMarketPolicy">A股本地指数和宽度为主体；匹配的海外行业基准与全球宽基合计最多占环境分15%，不构成独立买卖信号。</div></details>
        </div>
      </section>

      <section class="panel sector-panel">
        <div class="panel-h">
          <span>主线板块 · 日内资金轮动与近期强度</span>
          <span class="row"><select id="sectorWindow" aria-label="板块资金时间窗口" onchange="setSectorWindow(this.value)"><option value="interval_flow_15m">近15分钟</option><option value="interval_flow_5m">近5分钟</option><option value="interval_flow_30m">近30分钟</option><option value="interval_flow_60m">近60分钟</option><option value="morning_flow_change">上午</option><option value="afternoon_flow_change">下午</option><option value="net_inflow">当日累计</option><option value="recent_flow_5d_sum">近5日</option></select><select id="sectorFilterSelect" aria-label="板块榜单筛选" onchange="setSectorFilter(this.value)"><option value="all">主线榜</option><option value="industry">行业板块</option><option value="concept">概念板块</option><option value="inflow">区间流入</option><option value="outflow">区间流出</option><option value="returning">正在回流</option><option value="diverging">高位分歧</option></select><button class="btn" onclick="loadSectorMainline(true)">保存新快照</button></span>
        </div>
        <div class="panel-b">
          <div class="sector-summary"><div><b id="sectorHeadline">板块数据加载中...</b><div class="sector-method" id="sectorMethod">强度综合涨跌幅、公开资金净流、上涨宽度和换手参与度；不是 Level-2 主力账户识别。</div></div><span class="pill" id="sectorStatus">等待来源</span></div>
          <div class="sector-rotation" id="sectorRotation"><div><b>等待日内快照</b><span>至少两个真实快照后计算区间流入流出。</span></div></div>
          <details class="sector-table-details"><summary>展开完整板块资金表（20列）</summary><div class="sector-table-wrap"><table class="sector-table"><thead><tr><th>板块</th><th>阶段</th><th>强度</th><th>主线分</th><th>涨跌幅</th><th>当日累计净流</th><th>近5分</th><th>近15分</th><th>近30分</th><th>近60分</th><th>上午变化</th><th>下午变化</th><th>近5日净流</th><th>资金阶段</th><th>流向状态</th><th>资金占比</th><th>上涨/下跌</th><th>上涨宽度</th><th>近期持续</th><th>来源</th></tr></thead><tbody id="sectorRows"><tr><td colspan="20">正在读取真实板块数据...</td></tr></tbody></table></div></details>
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
          <div class="panel home-internal-state" aria-hidden="true">
            <div class="panel-h"><span>模块入口</span><span class="muted">右侧覆盖 iframe</span></div>
            <div class="panel-b module-grid" id="moduleCards"></div>
          </div>
          <div class="panel" id="homeStatusPanel">
            <div class="panel-h"><span>关键状态</span><button class="btn" onclick="refreshAll(this)">刷新状态</button></div>
            <div class="panel-b">
              <table class="mini-table"><tbody id="workflowBody"><tr><td>加载中...</td></tr></tbody></table>
            </div>
          </div>
        </div>

        <div class="stack home-internal-state" aria-hidden="true">
          <div class="panel home-internal-state" id="paperControl" aria-hidden="true">
            <div class="panel-h"><span>一键配置与组合策略</span><span class="muted">策略数量与模拟/回测共用</span></div>
            <div class="panel-b">
              <div class="quick-config">
                <div><b>首页只保留快速配置</b><span>完整股票池、50+ 策略目录、逐项阈值、仓位和事件门控仍在下方折叠区；建议先读取最新筛选，再回测、模拟，最后进入实盘确认。</span></div>
                <div class="row"><button class="btn green" onclick="oneClickConfig(this)">一键配置</button><button class="btn" onclick="loadLatestScreenerConfig(this)">读取筛选</button><button class="btn" onclick="openModule('realtime')">模拟详情</button></div>
              </div>
              <div class="notice" style="margin:10px 0">
                <label class="check"><input id="globalSectorReferenceToggle" type="checkbox" checked onchange="toggleGlobalReferenceStrategy(this.checked)"> 全球行业走势参照</label>
                <span class="muted">按每只股票所属行业匹配海外指数或期货；仅在证据有效时参与大盘情绪，内部权重上限 15%，不能单独触发买入。</span>
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
                  <div class="field"><label>内部策略标识（通常无需手工编辑）</label><textarea class="compact" id="strategyCombo" oninput="renderStrategyCatalog(lastAutoConfig||{})">score_driven, low_position, avoid_chasing_high, ma_repair, macd_cross, volume_breakout, atr_risk, position_risk, risk_control, event_driven, finance_quality, market_regime, global_sector_reference</textarea></div>
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
              <div class="field"><label>评分权重模式</label><select id="scoreWeightMode" onchange="toggleScoreWeightMode()"><option value="adaptive">按策略与大盘自适应（推荐）</option><option value="manual">手工固定权重</option></select></div>
              <div id="manualScoreWeights" class="split" style="display:none">
                <div class="field"><label>基本面%</label><input id="weightFundamental" type="number" min="0" max="100" value="22"></div>
                <div class="field"><label>技术面%</label><input id="weightTechnical" type="number" min="0" max="100" value="30"></div>
                <div class="field"><label>信息面%</label><input id="weightInformation" type="number" min="0" max="100" value="20"></div>
                <div class="field"><label>资金面%</label><input id="weightFundFlow" type="number" min="0" max="100" value="16"></div>
                <div class="field"><label>大盘情绪%</label><input id="weightMarket" type="number" min="0" max="100" value="12"></div>
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
          <div class="panel" id="homeScorePanel">
            <div class="panel-h"><span>当前个股评分与风险</span><span class="muted" id="scoreTime">--</span></div>
            <div class="panel-b">
              <div class="home-score-layout">
                <div class="home-score-primary">
                  <div class="row" style="justify-content:space-between"><b id="decisionAction" style="font-size:22px">等待评分</b><span class="pill" id="decisionScore">评分 --</span></div>
                  <div id="scorePolicyWeights" class="score-policy" aria-label="默认执行分目标权重（实际按策略与大盘自适应）"><span><b>30%</b>技术面</span><span><b>22%</b>基本面</span><span><b>20%</b>信息面</span><span><b>16%</b>资金面</span><span><b>12%</b>大盘情绪</span></div>
                  <div id="scorePolicySummary" class="muted" style="font-size:11px;line-height:1.5">按策略族和大盘环境选择有边界的权重、阈值与仓位；缺失项不补 50 分，剩余有效权重自动归一化。</div>
                  <div class="score-trend"><div class="score-trend-head"><b>评分走势</b><span id="dailyScoreStatus">正在读取每日交易池评分...</span><div class="grow"></div><button class="btn" onclick="runDailyScore(this)">保存今日评分</button></div><canvas id="scoreTrendCanvas" aria-label="每日与盘中评分走势"></canvas><div class="score-legend"><span><i style="background:#22c55e"></i>每日自动评分</span><span><i style="background:#60a5fa"></i>盘中评分</span><span><i style="background:#f59e0b"></i>手工筛选</span></div></div>
                </div>
                <div class="home-score-secondary">
                  <div class="bars">
                <div><div class="row" style="justify-content:space-between"><span>技术面</span><b id="techScore">--</b></div><div class="barline"><i id="techBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>基本面</span><b id="fundScore">--</b></div><div class="barline"><i id="fundBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>信息面</span><b id="infoScore">--</b></div><div class="barline"><i id="infoBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>资金面</span><b id="flowScore">--</b></div><div class="barline"><i id="flowBar"></i></div></div>
                <div><div class="row" style="justify-content:space-between"><span>大盘情绪</span><b id="marketScore">--</b></div><div class="barline"><i id="marketBar"></i></div></div>
                  </div>
                  <div id="globalScoreContribution" class="mini">当前个股的全球行业走势参照：等待策略与行情快照。</div>
                  <details class="score-explain">
                <summary>这个分数怎么来的</summary>
                <div id="scoreExplain" class="score-explain-body"><span class="muted">等待最新实时模拟信号；尚无信号时显示最近一次评分溯源。</span></div>
                  </details>
                  <details class="score-explain">
                <summary>基本/技术/信息/资金、大盘与自动入场门禁</summary>
                <div id="dimensionReadiness" class="score-explain-body"><span class="muted">正在核对本轮技术面、信息面、资金面和大盘证据。</span></div>
                  </details>
                  <details class="score-explain">
                <summary>个股资金流与机构持仓披露</summary>
                <div class="score-explain-body"><div class="row" style="justify-content:space-between"><span class="pill" id="capitalEvidenceStatus">等待资金证据</span><button class="btn" onclick="loadCapitalEvidence(true,this)">刷新真实来源</button></div><div id="capitalEvidence"><span class="muted">正在读取公开日资金流、当日分时量价、5/15/30/60分钟窗口和基金持仓披露。</span></div></div>
                  </details>
                </div>
              </div>
            </div>
          </div>
          <div class="panel" id="homePaperPanel">
            <div class="panel-h"><span>模拟账户/持仓</span><div class="row"><button class="btn" onclick="runDuePositionReviews(this)">检查每日复核</button><button class="btn" onclick="reviewPaperPositions(this)">复核全部持仓</button><button class="btn" onclick="openModule('realtime')">详情</button></div></div>
            <div class="panel-b">
              <div id="sessionSnapshot" class="notice">暂无 active session</div>
              <details class="dashboard-fold"><summary>展开自动复评、持仓复核和会话计数</summary><div class="dashboard-fold-body"><div id="paperSchedulerStatus" class="notice">正在读取服务端自动复评状态...</div><div id="reviewScheduleStatus" class="notice" style="margin-top:8px">正在读取每日持仓复核计划...</div><div id="paperPositionReviews" class="position-review-list"><span class="muted">有持仓后可执行每日复核；复核不会绕过实时模拟内核创建订单。</span></div><table class="mini-table"><tbody id="sessionRows"><tr><td>等待 session...</td></tr></tbody></table></div></details>
            </div>
          </div>
          <div class="panel home-internal-state" id="homeLiveSafetyPanel" aria-hidden="true">
            <div class="panel-h"><span>实盘安全</span><div class="row"><button class="btn" onclick="reviewLivePositions(this)">只读持仓复核</button><button class="btn red" onclick="killLive(this)">Kill</button></div></div>
            <div class="panel-b">
              <div class="notice" id="liveSafety">真实交易默认关闭。未配置券商 SDK、环境变量、账号授权时只显示“已关闭/不支持”。</div>
              <details class="dashboard-fold"><summary>展开券商预检查、同花顺提醒和持仓复核</summary><div class="dashboard-fold-body">
              <div class="notice">没有 QMT/PTrade/同花顺授权执行环境时仍可完成评分、批量预检查、风控和待确认票据；也可连接用户自行授权的本地 HTTP 券商桥。任何真实执行都必须通过服务端确认队列和全部安全门禁。</div>
              <details class="advanced-box" style="margin-top:10px" id="brokerSetupDetails">
                <summary>券商接入向导（QMT / PTrade / 同花顺授权桥 / 本地桥）</summary>
                <div class="advanced-body">
                  <div class="notice" id="brokerSetupSummary">正在读取本机券商组件和安全开关；该检查不会登录、保存密钥或下单。</div>
                  <div class="split" style="margin-top:10px">
                    <div class="field"><label>接入方式</label><select id="brokerSetupType" onchange="switchBrokerSetup(this.value)"><option value="qmt">迅投 QMT / MiniQMT</option><option value="ptrade">PTrade 券商托管</option><option value="tonghuashun">同花顺 / SuperMind 授权桥</option><option value="http_bridge">本地 HTTP 券商桥</option></select></div>
                    <div class="field"><label>安全说明</label><div class="notice">所有输入只发送到本机网关做一次校验，不写入磁盘。账号和令牌不会回显；真正配置请使用本地环境文件并重启。</div></div>
                  </div>
                  <div class="broker-fields active" data-broker-fields="qmt"><div class="broker-setup-grid"><div class="field"><label>QMT 数据目录</label><input id="setupQmtPath" placeholder="D:\\...\\userdata_mini"></div><div class="field"><label>资金账号</label><input id="setupQmtAccount" autocomplete="off" placeholder="仅本次校验，不保存"></div><div class="field"><label>账号类型</label><select id="setupQmtAccountType"><option value="STOCK">普通股票 STOCK</option><option value="CREDIT">信用账户 CREDIT</option></select></div><div class="field"><label>独占会话号</label><input id="setupQmtSession" inputmode="numeric" value="10001"></div></div></div>
                  <div class="broker-fields" data-broker-fields="ptrade"><div class="broker-setup-grid"><div class="field"><label>券商指定模块</label><input id="setupPtradeModule" placeholder="仅券商明确提供时填写"></div><div class="field"><label>券商账号标识</label><input id="setupPtradeAccount" autocomplete="off" placeholder="仅本次校验，不保存"></div></div><div class="notice">PTrade 通常运行在券商托管平台，不存在通用的本地 pip SDK。先向开户券商确认权限、运行环境和接口版本；需要与本系统联动时，优先部署受控执行端并接本地桥。</div></div>
                  <div class="broker-fields" data-broker-fields="tonghuashun"><div class="broker-setup-grid"><div class="field"><label>授权执行桥地址</label><input id="setupThsBridgeUrl" value="http://127.0.0.1:8765"></div><div class="field"><label>独立访问令牌</label><input id="setupThsBridgeToken" type="password" autocomplete="new-password" placeholder="仅本次校验，不保存"></div></div><div class="notice">普通同花顺客户端只做行情查看、启动和人工委托提醒；iFinD 只作为授权数据源。自动下单必须由券商授权的 SuperMind/托管执行端提供桥接，并在健康检查中声明身份。</div></div>
                  <div class="broker-fields" data-broker-fields="http_bridge"><div class="broker-setup-grid"><div class="field"><label>桥接地址</label><input id="setupBridgeUrl" value="http://127.0.0.1:8765"></div><div class="field"><label>独立访问令牌</label><input id="setupBridgeToken" type="password" autocomplete="new-password" placeholder="仅本次校验，不保存"></div></div></div>
                  <div class="row"><button class="btn" onclick="loadBrokerSetup(this)">读取当前环境</button><button class="btn primary" onclick="validateBrokerSetup(this)">只读校验</button><button class="btn" onclick="openModule('live')">进入真实交易页</button></div>
                  <div id="brokerSetupResult" class="setup-result"><span class="muted">等待诊断。</span></div>
                  <div id="brokerCapabilityMatrix" class="broker-capabilities"><div class="broker-capability"><b>接入能力</b><span>等待只读诊断。</span></div></div>
                  <details style="margin-top:8px"><summary>显示安全环境变量模板</summary><pre id="brokerSetupTemplate" class="setup-template">选择接入方式后生成模板。</pre></details>
                  <div id="brokerSetupDocs" class="setup-links"></div>
                </div>
              </details>
              <details class="advanced-box" style="margin-top:10px">
                <summary>移动端交易提醒（钉钉 / 飞书 / 企业微信）</summary>
                <div class="advanced-body">
                  <div id="mobileAlertStatus" class="notice">正在读取移动提醒状态。</div>
                  <div class="row"><button class="btn" onclick="previewMobileAlert(this)">预览提醒</button><button class="btn" onclick="testMobileAlert(this)">发送联通测试</button></div>
                  <pre id="mobileAlertPreview" class="setup-template">提醒只转发已落库状态，不代表券商受理或成交。</pre>
                  <details><summary>显示环境变量模板</summary><pre class="setup-template">MOBILE_ALERTS_ENABLED=false
MOBILE_ALERT_PROVIDER=dingtalk
MOBILE_ALERT_WEBHOOK_URL=
MOBILE_ALERT_SECRET=
MOBILE_ALERT_MIN_LEVEL=warning
MOBILE_ALERT_COOLDOWN_SECONDS=60</pre></details>
                </div>
              </details>
              <details class="advanced-box" style="margin-top:10px">
                <summary>同花顺委托提醒（本机客户端，人工录入）</summary>
                <div class="advanced-body">
                  <div class="notice" id="thsStatus">正在读取同花顺本地客户端状态...</div>
                  <div class="split" style="margin-top:10px"><div class="field"><label>行情启动器</label><input id="thsLauncherPath" value="" placeholder="例如 D:\\software\\同花顺\\hexinlauncher.exe"></div><div class="field"><label>委托程序</label><input id="thsOrderPath" value="" placeholder="例如 D:\\software\\同花顺\\xiadan.exe"></div></div>
                  <label class="check"><input id="thsEnabled" type="checkbox"> 启用本地唤起和委托提醒（仍不会自动点击下单）</label>
                  <div class="row" style="margin-top:10px"><button class="btn" onclick="saveTonghuashun(this)">保存本机配置</button><button class="btn" onclick="launchTonghuashun(this,'launcher')">打开行情客户端</button><button class="btn" onclick="launchTonghuashun(this,'order')">打开委托程序</button><button class="btn primary" onclick="createTonghuashunReminder(this)">生成当前委托提醒</button></div>
                  <div id="thsReminder" class="notice" style="margin-top:10px">提醒票据会记录代码、方向、价格、股数、评分溯源和风控结果；它不是券商委托或成交证明。</div>
                </div>
              </details>
              <div class="split" style="margin-top:10px"><div class="field"><label>预检查代码</label><input id="liveSymbol" value="300750"></div><div class="field"><label>方向</label><select id="liveSide"><option value="buy">买入</option><option value="sell">卖出</option></select></div></div>
              <div class="split"><div class="field"><label>股数</label><input id="liveQty" type="number" value="100"></div><div class="field"><label>限价</label><input id="livePrice" type="number" value="0"></div></div>
              <div class="row"><button class="btn" onclick="previewOrder()">首只订单预检查</button><button class="btn" onclick="previewOrderBatch()">股票池批量预检查</button><button class="btn" onclick="openModule('live')">进入实盘页</button></div>
              <div class="notice" id="livePreviewSummary" style="margin-top:10px">批量预检查会逐只经过数据新鲜度、评分溯源、白名单、仓位、Kill Switch 和人工确认门控，不会直接下单。</div>
              <div id="livePositionReviews" class="position-review-list"><span class="muted">连接并授权券商后可读取真实持仓；这里仅生成持有、减仓或退出复核建议。</span></div>
              </div></details>
            </div>
          </div>
          <div class="panel" id="homePortfolioPanel">
            <div class="panel-h"><span>资金/持仓/流水总览</span><button class="btn" onclick="openModule('records')">完整记录</button></div>
            <div class="panel-b">
              <div id="portfolioOverview" class="notice">正在读取实盘安全账户、模拟账户和统一交易流水...</div>
              <details class="dashboard-fold"><summary>展开最近订单、成交与盈亏</summary><div class="dashboard-fold-body"><table class="mini-table">
                <thead><tr><th>来源</th><th>代码</th><th>方向/状态</th><th>价格</th><th>数量</th><th>金额/盈亏</th></tr></thead>
                <tbody id="recordOverviewRows"><tr><td colspan="6">等待交易记录...</td></tr></tbody>
              </table></div></details>
            </div>
          </div>
          <div class="panel home-internal-state" id="homeAuditPanel" aria-hidden="true">
            <div class="panel-h"><span>审计日志</span><span class="muted">最近动作</span></div>
            <div class="panel-b"><details class="dashboard-fold" style="margin-top:0"><summary>展开最近动作与原始响应</summary><div class="dashboard-fold-body"><div class="log" id="auditLog">Ready.</div></div></details></div>
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
    <button class="btn" onclick="reloadWorkspaceFrame()">刷新页面</button>
    <button class="btn" onclick="openWorkspaceInNewWindow()">新窗口</button>
    <button class="btn red" onclick="closeWorkspace()">关闭</button>
  </header>
  <iframe id="workspaceFrame" class="workspace-frame" title="V3.28 自动交易右侧模块 iframe" src="about:blank"></iframe>
</section>
<div class="action-toast" id="actionToast" role="status" aria-live="polite"></div>
<script>
const $=id=>document.getElementById(id);
const MODULES={
  screener:{label:'股票筛选',icon:'筛',url:()=>'/screener?embedded=1',desc:'股票池、四面评分、风险标签、一键加入回测/模拟/实盘观察。'},
  quote:{label:'分时盘口',icon:'时',url:()=>'/ui?symbol='+encodeURIComponent(primarySymbol())+'&frame=time&embedded=1',desc:'分时、五档盘口、盘口观察、资金行为和当日状态。'},
  detail:{label:'K线详情',icon:'K',url:()=>'/detail/'+encodeURIComponent(primarySymbol())+'?frame=1d&embedded=1',desc:'日K/周K/月K、技术因子、异常标注、信息面与资金面。'},
  backtest:{label:'历史回测',icon:'测',url:()=>'/backtest?symbol='+encodeURIComponent(primarySymbol())+'&embedded=1',desc:'用同一套配置验证收益、回撤、买卖流水和策略跑输原因。'},
  realtime:{label:'实时模拟',icon:'模',url:()=>'/realtime-paper?embedded=1',desc:'真实行情驱动 paper trading，记录订单、成交、持仓、审计和图表 marker。'},
  live:{label:'真实交易',icon:'实',url:()=>'/live-trading?embedded=1',desc:'QMT、PTrade、本地 HTTP 券商桥、确认队列和紧急停止。'},
  broker:{label:'券商接入向导',icon:'接',url:()=>'/broker-setup?embedded=1',desc:'分步配置 QMT、PTrade、同花顺桌面伴随或券商授权执行桥，并只读检查安全开关。'},
  records:{label:'交易记录',icon:'录',url:()=>'/trading-records?embedded=1',desc:'回测、模拟、真实交易统一流水。'},
  data:{label:'数据中心',icon:'数',url:()=>'/data-center?embedded=1',desc:'缓存、缺失字段、数据源错误、券商状态。'},
  docs:{label:'中文 API',icon:'?',url:()=>'/docs-cn?embedded=1',desc:'中文接口说明和调试入口。'}
};
const MODULE_PATHS={
  '/screener':'screener','/ui':'quote','/backtest':'backtest','/realtime-paper':'realtime',
  '/live-trading':'live','/broker-setup':'broker','/trading-records':'records',
  '/data-center':'data','/docs-cn':'docs','/info':'detail'
};
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
let globalStreamRefreshMs=35000;
let globalStreamLastLoadedAt=0;
let globalStreamLastPayload=null;
let globalMarketRequestSeq=0;
let strategyEditorHydrated=false;
let deferredStrategyConfig=null;
let dashboardPanels=[];
let dashboardLayoutKey='';
function arrangeDashboardPanels(){
  const grid=document.querySelector('.grid-main');
  if(!grid)return;
  if(!dashboardPanels.length)dashboardPanels=[...grid.querySelectorAll(':scope > .stack > .panel')];
  if(dashboardPanels.length<8)return;
  const width=window.innerWidth;
  const layoutKey=width>1360?'wide':width>1050?'medium':'narrow';
  if(layoutKey===dashboardLayoutKey)return;
  // V3.27 旧布局参考：layoutKey==='medium'?[[3,0,6],[4,1,2,5,7]]；V3.28 只排列首页总览，隐藏状态节点仍保留在 DOM 供模块共用。
  const plan=layoutKey==='wide'?[[6,1,0,2,5,7],[3],[4]]:layoutKey==='medium'?[[6,1,0,2,5,7],[3,4]]:[[6,3,4,1,0,2,5,7]];
  const columns=plan.map(indexes=>{
    const column=document.createElement('div');
    column.className='stack';
    indexes.forEach(index=>dashboardPanels[index]&&column.appendChild(dashboardPanels[index]));
    return column;
  });
  grid.replaceChildren(...columns);
  dashboardLayoutKey=layoutKey;
}
let dashboardResizeTimer=null;
window.addEventListener('resize',()=>{clearTimeout(dashboardResizeTimer);dashboardResizeTimer=setTimeout(arrangeDashboardPanels,120)});
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
function money(v){const n=finiteNumber(v);return n!==null?n.toLocaleString('zh-CN',{maximumFractionDigits:2}):'--'}
function pct(v){const n=finiteNumber(v);return n!==null?n.toFixed(2)+'%':'--'}
function pnlClass(v){const n=finiteNumber(v);return n!==null&&n>0?'ok':n!==null&&n<0?'bad':''}
function cnEnum(v){
  const raw=String(v??'').trim();
  const map={macro:'宏观市场',fundamental:'基本面',technical:'技术面',information:'信息面',fund_flow:'资金面',market:'大盘情绪',sector:'板块强度',earnings:'财报业绩',ipo:'IPO上市',global:'全球市场',company_event:'公司事件',market_macro:'宏观市场',news:'新闻资讯',announcement:'公司公告',policy:'政策信息',research:'研究信息',positive:'偏利好',negative:'偏利空',neutral:'中性',no_direct_mapping:'暂无直接映射',mapping_error:'映射失败',connected:'已连接',disconnected:'未连接',disabled:'已关闭',unsupported:'不支持',blocked:'已阻断',qmt:'迅投 QMT',ptrade:'PTrade',tonghuashun:'同花顺 / SuperMind 授权桥',tonghuashun_supermind_bridge:'同花顺 / SuperMind 授权桥',http_bridge:'本地 HTTP 券商桥',simulator:'本地模拟器',running:'运行中',paused:'已暂停',stopped:'已停止',buy:'买入',sell:'卖出',hold:'观察',add:'加仓',reduce:'减仓',avoid:'回避',needs_confirmation:'待人工确认',score_weighted:'评分加权',atr_risk:'波动风险仓位',volatility_target:'波动率目标',fixed_weight:'固定权重',core_satellite:'核心-卫星',cash_first_defensive:'现金优先防守',equal_risk_contribution:'等风险分配',hybrid:'综合评分',etf_momentum_rotation:'ETF动量轮动',score_reversal:'评分拐点修复',event_driven:'事件驱动',available:'可用',proxy_available:'代理可用',partial:'部分可用',missing:'缺失',unavailable:'不可用',unusable:'不可交易',rejected:'已剔除',insufficient_sample:'样本不足',snapshot:'快照可用',refreshed:'已刷新',hit:'缓存命中',fresh:'最新',stale:'已过期',local:'本地缓存',fallback:'降级缓存',error:'错误',public_main_net_ratio:'公开主力净流占比',public_main_ratio_5d:'近5日公开主力净流占比',intraday_amount_direction_proxy:'当日分时量价方向代理',revenue_disclosed:'营业收入已披露',net_profit_sign:'净利润正负',eps_sign:'每股收益正负',pe:'市盈率',pb:'市净率',roe:'净资产收益率',gross_margin:'毛利率',debt_ratio:'资产负债率'};
  return map[raw]||raw;
}
function cnAction(v){return cnEnum(v)||'观察'}
function sizingLabel(v){return cnEnum(v)||'未设置'}
function setText(id,value){const el=$(id);if(el)el.textContent=value}
function finiteNumber(value){if(value===null||value===undefined||value===''||value==='--')return null;const n=Number(value);return Number.isFinite(n)?n:null}
function setScore(id,val,ready=null){const n=finiteNumber(val);const ok=n!==null;const suffix=ok&&ready===false?' 未参与':'';setText(id+'Score',ok?n.toFixed(1)+suffix:'缺失');const bar=$(id+'Bar');if(bar){bar.style.width=(ok?Math.max(0,Math.min(100,n)):0)+'%';bar.classList.toggle('excluded',ready===false)}}
function switchBrokerSetup(type){document.querySelectorAll('[data-broker-fields]').forEach(x=>x.classList.toggle('active',x.dataset.brokerFields===type));const cache=window.__brokerSetupData;if(cache)renderBrokerSetup(cache,type)}
function brokerSetupPayload(){const type=$('brokerSetupType')?.value||'qmt';return {broker_type:type,qmt_path:$('setupQmtPath')?.value?.trim()||'',qmt_account_id:$('setupQmtAccount')?.value?.trim()||'',qmt_account_type:$('setupQmtAccountType')?.value||'STOCK',qmt_session_id:$('setupQmtSession')?.value?.trim()||'',ptrade_module:$('setupPtradeModule')?.value?.trim()||'',ptrade_account_id:$('setupPtradeAccount')?.value?.trim()||'',http_bridge_url:type==='tonghuashun'?($('setupThsBridgeUrl')?.value?.trim()||''):($('setupBridgeUrl')?.value?.trim()||''),http_bridge_token:type==='tonghuashun'?($('setupThsBridgeToken')?.value||''):($('setupBridgeToken')?.value||'')}}
function renderBrokerSetup(js,selected=''){
  const requested=selected||$('brokerSetupType')?.value||js?.selected_broker||'qmt';const type=['qmt','ptrade','tonghuashun','http_bridge'].includes(requested)?requested:'qmt';window.__brokerSetupData=js||{};if($('brokerSetupType'))$('brokerSetupType').value=type;document.querySelectorAll('[data-broker-fields]').forEach(x=>x.classList.toggle('active',x.dataset.brokerFields===type));
  const active=js?.brokers?.[type]||js?.active||{},s=js?.safety||{},missing=active.missing_reasons||[],steps=active.next_steps||[];const ready=!!active.configuration_ready;
  if($('brokerSetupSummary'))$('brokerSetupSummary').innerHTML=`<b>${esc(cnEnum(type))}：${ready?'配置要素已识别，仍需连接验收':'尚未就绪'}</b><br>真实交易开关：${s.live_trading_enabled?'开启':'关闭'}；人工确认：${s.order_confirm_required?'必须':'未启用'}；白名单 ${esc(s.whitelist_count??0)} 只。<br><span class="muted">${esc(js?.truth_boundary||'诊断不代表券商已连接或可下单。')}</span>`;
  if($('brokerSetupResult'))$('brokerSetupResult').innerHTML=`<div class="notice ${ready?'ok':'warn'}"><b>${ready?'本机配置初检通过':'缺少配置或运行环境'}</b>${missing.length?`<ul>${missing.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:'<br>未发现配置字段缺失；请继续执行连接、只读账户和持仓验收。'}</div>${steps.length?`<div class="notice"><b>下一步</b><ul>${steps.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:''}`;
  const caps=active.capabilities||{};if($('brokerCapabilityMatrix'))$('brokerCapabilityMatrix').innerHTML=Object.entries(caps).map(([label,state])=>`<div class="broker-capability"><b>${esc(label)}</b><span>${esc(state)}</span></div>`).join('')||'<div class="broker-capability"><b>接入能力</b><span>当前诊断未返回能力说明。</span></div>';
  const template=js?.environment_templates?.[type]||'';if($('brokerSetupTemplate'))$('brokerSetupTemplate').textContent=template||'当前方式没有模板。';const docs=js?.official_docs?.[type]||[];if($('brokerSetupDocs'))$('brokerSetupDocs').innerHTML=docs.map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.label)}</a>`).join('');
}
async function loadBrokerSetup(btn=null){return withAction(btn,'检查中','券商环境已检查',async()=>{const type=$('brokerSetupType')?.value||'qmt';const js=await api('/api/live-broker/setup?broker_type='+encodeURIComponent(type));renderBrokerSetup(js,type);return js})}
async function validateBrokerSetup(btn=null){return withAction(btn,'校验中','只读校验完成',async()=>{const payload=brokerSetupPayload();const js=await api('/api/live-broker/setup/validate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});renderBrokerSetup(js,payload.broker_type);if($('setupQmtAccount'))$('setupQmtAccount').value='';if($('setupPtradeAccount'))$('setupPtradeAccount').value='';if($('setupBridgeToken'))$('setupBridgeToken').value='';if($('setupThsBridgeToken'))$('setupThsBridgeToken').value='';return js})}
function renderMobileAlertStatus(js){const enabled=!!js?.enabled,ready=!!js?.configuration_ready,reasons=js?.missing_reasons||[];if($('mobileAlertStatus'))$('mobileAlertStatus').innerHTML=`<b>状态：${enabled?'已启用':'默认关闭'} · ${esc(cnEnum(js?.provider||'disabled'))}</b><br>${ready?'Webhook 配置要素已识别。':'尚未形成可发送配置。'}${reasons.length?`<br><span class="muted">${esc(reasons.join('；'))}</span>`:''}<br><span class="muted">${esc(js?.truth_boundary||'提醒不是成交证明。')}</span>`}
async function previewMobileAlert(btn=null){return withAction(btn,'生成中','提醒预览已生成',async()=>{const body={event_type:'needs_confirmation',symbol:primarySymbol(),side:'buy',quantity:100,status:'待人工确认',reason:'示例预览，不创建订单或确认票据'};const js=await api('/api/notifications/mobile/preview',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});if($('mobileAlertPreview'))$('mobileAlertPreview').textContent=js.message||'预览为空';return js})}
async function testMobileAlert(btn=null){try{return await withAction(btn,'发送中','移动提醒测试已发送',async()=>{const js=await api('/api/notifications/mobile/test',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbol:primarySymbol()})});if($('mobileAlertPreview'))$('mobileAlertPreview').textContent=js.message||JSON.stringify(js,null,2);return js})}catch(e){if($('mobileAlertPreview'))$('mobileAlertPreview').textContent=String(e);return null}}
function scoreFrom(row,key){const b=row?.score_breakdown||{};const direct=row?.[key+'_score']??b[key+'_score']??b.raw_dimension_scores?.[key];if(direct!==null&&direct!==undefined&&direct!==''&&Number.isFinite(Number(direct)))return Number(direct);const hit=(b.contributions||[]).find(x=>x?.key===key);const value=hit?.score;return value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value))?Number(value):null}
function sessionIdOf(item){return item?.session_id||item?.id||item?.sessionId||''}
function renderModuleCards(){
  const box=$('moduleCards');
  box.innerHTML=Object.entries(MODULES).map(([key,m])=>`<a class="module" href="${esc(m.url())}" onclick="openModule('${key}');return false"><b>${esc(m.label)}</b><span>${esc(m.desc)}</span></a>`).join('');
}
arrangeDashboardPanels();
function markNav(key){
  document.querySelectorAll('#moduleNav button').forEach(btn=>btn.classList.toggle('active',btn.dataset.module===key || (!key && !btn.dataset.module)));
}
function embeddedModuleUrl(raw){
  const parsed=new URL(raw||'/',location.origin);
  if(parsed.origin!==location.origin)return raw;
  if(parsed.pathname==='/auto-trading')return '/auto-trading';
  parsed.searchParams.set('embedded','1');
  return parsed.pathname+parsed.search+parsed.hash;
}
function moduleKeyFromUrl(raw){
  try{
    const parsed=new URL(raw,location.origin);
    if(parsed.pathname.startsWith('/detail/'))return 'detail';
    if(parsed.pathname==='/backtest/trades')return 'backtest';
    return MODULE_PATHS[parsed.pathname]||'';
  }catch(_error){return ''}
}
function openModule(key,urlOverride){
  const mod=MODULES[key]||MODULES.screener;
  let url=urlOverride||mod.url();
  if(!/[?&]embedded=1\\b/.test(url))url=embeddedModuleUrl(url);
  if(url==='/auto-trading'){closeWorkspace();return}
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
function handleWorkspaceFrameLoad(){
  const frame=$('workspaceFrame');
  if(!frame||frame.src==='about:blank')return;
  let win,doc,href;
  try{win=frame.contentWindow;doc=frame.contentDocument;href=win.location.href}catch(_error){return}
  if(!doc||!href)return;
  const parsed=new URL(href,location.origin);
  if(parsed.pathname==='/auto-trading'){
    frame.src='about:blank';
    closeWorkspace();
    showActionToast('已返回总控台首页，未在 iframe 内重复嵌套','good');
    return;
  }
  const detected=moduleKeyFromUrl(href);
  if(detected&&detected!==currentModule){currentModule=detected;markNav(detected)}
  doc.documentElement.dataset.workbenchEmbedded='1';
  doc.addEventListener('click',event=>{
    const anchor=event.target?.closest?.('a[href]');
    if(!anchor||anchor.target==='_blank'||event.ctrlKey||event.metaKey||event.shiftKey)return;
    let target;
    try{target=new URL(anchor.href,location.origin)}catch(_error){return}
    if(target.origin!==location.origin)return;
    if(target.pathname==='/auto-trading'){
      event.preventDefault();
      closeWorkspace();
      return;
    }
    const targetKey=moduleKeyFromUrl(target.href);
    if(!targetKey)return;
    event.preventDefault();
    openModule(targetKey,embeddedModuleUrl(target.pathname+target.search+target.hash));
  },true);
  $('workspaceStatus').textContent=parsed.pathname+parsed.search;
}
$('workspaceFrame').addEventListener('load',handleWorkspaceFrameLoad);
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
function openWorkspaceInNewWindow(){
  if(!currentWorkspaceUrl||currentWorkspaceUrl==='about:blank')return;
  const parsed=new URL(currentWorkspaceUrl,location.origin);parsed.searchParams.delete('embedded');
  window.open(parsed.pathname+parsed.search+parsed.hash,'_blank','noopener');
}
function strategyNameMap(cfg){const out={};(cfg?.strategy_catalog||[]).forEach(x=>{if(x?.key)out[String(x.key)]=String(x.name||x.key)});return out}
function strategyLabel(key,cfg){
  const builtins={score_driven:'日常评分驱动',low_position:'低位修复',avoid_chasing_high:'高位追高过滤',source_reliability:'数据源可靠性',ma_repair:'均线修复',macd_cross:'MACD 金叉/多头',macd_hist_turn:'MACD 柱改善',volume_breakout:'温和放量',mfi_obv_resonance:'MFI/OBV 共振',rsi_kdj_resonance:'RSI/KDJ 共振',atr_risk:'ATR 风险过滤',position_risk:'仓位与止损',risk_control:'风险扣分',event_driven:'事件驱动',finance_quality:'财务质量',fundamental_quality:'基本面质量',cashflow_quality:'现金流质量',announcement_risk:'公告风险',policy_tailwind:'政策顺风',macro_liquidity:'宏观流动性',main_money_est:'主力资金估算',market_regime:'大盘情绪过滤',global_sector_reference:'全球行业走势参照',etf_liquidity:'ETF 流动性',adx_trend:'ADX 趋势'};
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
  if($('globalSectorReferenceToggle'))$('globalSectorReferenceToggle').checked=combo.includes('global_sector_reference');
  const pendingUpgrade=cfg?.strategy_combo_upgraded===true
    ? '<br><b class="warn-text">待确认：</b>旧版极简组合已在编辑器中补全为推荐策略；点击“保存配置”或“启动模拟”后才会成为运行配置。'
    : '';
  $('strategySelectedSummary').innerHTML=`<b>当前组合：</b>${esc(combo.length?combo.map(k=>strategyLabel(k,cfg)).join('、'):'尚未选择策略')}<br><b>统一风控：</b>止损 ${esc(risk.stop_loss_pct)}% · 止盈 ${esc(risk.take_profit_pct)}% · 最大回撤 ${esc(risk.max_drawdown_pct)}% · 单票 ${esc(risk.max_single_position_pct)}%${pendingUpgrade}`;
}
function currentComboSet(){return new Set(strategyCombo())}
function toggleGlobalReferenceStrategy(enabled){
  const combo=currentComboSet();
  if(enabled)combo.add('global_sector_reference');else combo.delete('global_sector_reference');
  setComboFromList([...combo]);
  showToast(enabled?'全球行业走势参照已加入当前编辑组合；保存后生效。':'全球行业走势参照已从当前编辑组合移除；保存后生效。',enabled?'good':'warn');
}
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
function toggleScoreWeightMode(){const manual=$('scoreWeightMode')?.value==='manual';$('manualScoreWeights').style.display=manual?'grid':'none'}
function collectScoreWeights(){
  const mode=$('scoreWeightMode')?.value||'adaptive';
  if(mode!=='manual')return {mode:'adaptive',screening:0};
  return {mode:'manual',screening:0,fundamental:num('weightFundamental',22)/100,technical:num('weightTechnical',30)/100,information:num('weightInformation',20)/100,fund_flow:num('weightFundFlow',16)/100,market_regime:num('weightMarket',12)/100};
}
function collectAutoConfig(){
  return {symbols:symbols(),strategy_family:$('strategy').value,selected_strategies:strategyCombo(),strategy_combo:strategyCombo(),strategy_parameters:collectStrategyParamEditor(),position_sizing:$('positionSizing').value,interval_seconds:Number($('interval').value||15),initial_cash:num('initialCash',100000),reset_account:checked('resetAccount'),risk_controls:{stop_loss_pct:num('stopLossPct',8),take_profit_pct:num('takeProfitPct',18),max_drawdown_pct:num('maxDrawdownPct',18),max_single_position_pct:num('maxSinglePositionPct',20),max_total_position_pct:num('maxTotalPositionPct',80),min_cash_pct:num('minCashPct',15),max_daily_loss_pct:4,atr_risk_pct:1.5,cooldown_days:2},score_weight_mode:$('scoreWeightMode')?.value||'adaptive',score_weights:collectScoreWeights(),event_watch:{financial_reports:checked('watchFinancialReports'),half_year_reports:checked('watchHalfYearReports'),earnings_preannouncements:checked('watchFinancialReports'),exchange_announcements:checked('watchAnnouncements'),major_negative_news:checked('watchMajorNews'),policy_industry_news:checked('watchPolicyNews'),event_lookahead_days:21,blackout_before_days:2,blackout_after_days:1},data_requirements:{require_fresh_quote:checked('requireFreshQuote'),block_stale_buy:checked('requireFreshQuote'),require_score_provenance:true,require_info_snapshot:false,require_orderbook_when_available:true},source_page:'auto-trading'};
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
  const weights=cfg.score_weights||{};const mode=String(cfg.score_weight_mode||weights.mode||weights.weight_mode||'manual');$('scoreWeightMode').value=mode==='adaptive'?'adaptive':'manual';
  const setWeight=(id,...keys)=>{for(const key of keys){if(weights[key]!=null){$(id).value=(Number(weights[key])*100).toFixed(1);break}}};
  setWeight('weightFundamental','fundamental','fundamental_score');setWeight('weightTechnical','technical','technical_score');setWeight('weightInformation','information','information_score');setWeight('weightFundFlow','fund_flow','fund_flow_score');setWeight('weightMarket','market','market_regime','market_score');toggleScoreWeightMode();
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
    ['策略组合',combo.length?combo.slice(0,5).map(k=>strategyLabel(k,cfg)).join('、')+(combo.length>5?` 等 ${combo.length} 项`:''):'--'],
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
  const liveConnected=Boolean(liveAccount?.source?.connected||livePositions?.source?.connected);
  const liveAuthorized=account.authorized!==false;
  const liveDataAvailable=liveAccount?.data_available===true&&liveConnected&&liveAuthorized;
  const missing=liveAccount?.missing_reason||livePositions?.missing_reason||account.missing_reason||account.quality_status||'';
  const positionsText=liveDataAvailable&&liveRows.length
    ? liveRows.slice(0,4).map(p=>`${esc(p.symbol)} ${esc(p.quantity??0)}股 成本${esc(p.cost_price??p.avg_cost??'--')} 市值${money(p.market_value)}`).join('；')
    : liveDataAvailable?'当前真实账户暂无持仓':'--（券商未连接或未授权）';
  const liveAccountText=liveDataAvailable
    ? `可用资金 ${money(cash)}；总资产 ${money(total)}；持仓 ${esc(liveRows.length)} 只；浮盈亏 <span class="${pnlClass(livePnl)}">${money(livePnl)}</span>${livePnlPct!=null?' / '+pct(livePnlPct):''}`
    : '可用资金 --；总资产 --；持仓 --；浮盈亏 --';
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
  $('portfolioOverview').innerHTML=`${paperText}<hr style="border:0;border-top:1px solid var(--line);margin:10px 0"><b>真实账户（安全隔离）</b> ${liveAccountText}<br><b>实盘持仓</b> ${positionsText}<br><b>券商状态</b> ${esc(cnEnum(liveStatus))}${missing?'；'+esc(missing):''}<hr style="border:0;border-top:1px solid var(--line);margin:10px 0"><b>统一流水</b> ${recordText}`;
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
async function loadSessionOverview(base){
  const overviewUrl=base+'/overview?orders_limit=500&fills_limit=500&markers_limit=50&audit_limit=100&reviews_limit=50';
  try{
    const overview=await api(overviewUrl);
    if(overview?.ok&&overview.data)return overview.data;
  }catch(error){
    console.warn('realtime paper overview fallback',error);
  }
  const [snapshot,orders,fills,positions,markers,audit,reviews]=await Promise.all([
    api(base),
    api(base+'/orders?limit=500'),
    api(base+'/fills?limit=500'),
    api(base+'/positions'),
    api(base+'/markers?limit=50'),
    api(base+'/audit?limit=100'),
    api(base+'/position-reviews?limit=50')
  ]);
  return {snapshot,orders,fills,positions,markers,audit,reviews};
}
async function loadSessionDetails(session){
  activeSessionId=sessionIdOf(session)||activeSessionId;
  if(!activeSessionId){$('sessionSnapshot').textContent='暂无 active session';$('paperPositionReviews').innerHTML='<span class="muted">暂无可复核模拟持仓。</span>';renderSessionRows({});return}
  const base='/api/realtime-paper/sessions/'+encodeURIComponent(activeSessionId);
  const {snapshot,orders,fills,positions,markers,audit,reviews}=await loadSessionOverview(base);
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
async function loadGlobalStream(force=false){
  if(globalStreamPromise)return globalStreamPromise;
  if(!force&&globalStreamLastPayload&&Date.now()-globalStreamLastLoadedAt<10000){
    renderGlobalStream(globalStreamLastPayload);
    scheduleGlobalStreamLoop();
    return globalStreamLastPayload;
  }
  const task=(async()=>{
    const stream=await api('/api/news/global/stream?limit=80&live=true&force='+(force?'true':'false'));
    globalStreamLastPayload=stream;
    globalStreamLastLoadedAt=Date.now();
    renderGlobalStream(stream);
    scheduleGlobalStreamLoop();
    return stream;
  })();
  globalStreamPromise=task;
  try{return await task}finally{if(globalStreamPromise===task)globalStreamPromise=null}
}
function toggleGlobalTicker(){
  globalTickerPaused=!globalTickerPaused;
  $('globalTicker').classList.toggle('paused',globalTickerPaused);
  $('tickerPauseBtn').textContent=globalTickerPaused?'继续轮播':'暂停轮播';
  if(globalTickerPaused){if(globalStreamTimer)clearTimeout(globalStreamTimer);globalStreamTimer=null}
  else{loadGlobalStream(false).catch(()=>{});scheduleGlobalStreamLoop()}
}
function scheduleGlobalStreamLoop(){
  if(globalStreamTimer)clearTimeout(globalStreamTimer);
  globalStreamTimer=null;
  if(document.hidden||globalTickerPaused)return;
  globalStreamTimer=setTimeout(()=>{if(!document.hidden&&!globalTickerPaused)loadGlobalStream(false).catch(()=>{})},globalStreamRefreshMs);
}
function startGlobalStreamLoop(){
  if(!window.__qdGlobalVisibilityBound){
    window.__qdGlobalVisibilityBound=true;
    document.addEventListener('visibilitychange',()=>{
      if(document.hidden){if(globalStreamTimer)clearTimeout(globalStreamTimer);globalStreamTimer=null;return}
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
    ...textList(x?.affected_products_cn),
    ...textList(x?.affected_industries_cn),
    ...textList(x?.affected_regions_cn),
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
function eventStatusHtml(x){
  if(!x?.confirmation_level&&!x?.event_type)return '';
  const confirmed=['official_confirmed','multi_source_confirmed'].includes(String(x.confirmation_level||''));
  const isEvent=String(x.event_type||'')!=='general_information';
  const eventType=x.event_type_cn||cnEnum(x.event_type||'一般信息');
  const stage=x.event_stage_cn||cnEnum(x.event_stage||'阶段未知');
  const confirmation=x.confirmation_level_cn||cnEnum(x.confirmation_level||'待复核');
  const gate=x.trade_gate_cn||cnEnum(x.trade_gate||'仅观察');
  const use=x.decision_use_cn||(!isEvent?'仅展示，不进入评分':confirmed?'确认后可进入映射评分':'提前预警，暂不计分');
  const scope=x.decision_scope_cn||'尚无可验证传导对象';
  const merged=Math.max(Number(x.event_cluster_size||0),Number(x.duplicate_count||0));
  const directionReason=x.event_direction_reason_cn?`<div class="impact-summary"><b>方向依据：</b>${esc(x.event_direction_reason_cn)}</div>`:'';
  return `<div class="impact-row"><span class="impact-tag">${!isEvent?'普通快讯':confirmed?'已确认':'早期线索'}</span><span class="impact-tag">${esc(eventType)}</span><span class="impact-tag">${esc(stage)}</span><span class="impact-tag">${esc(confirmation)}</span>${merged>1?`<span class="impact-tag">已合并 ${merged} 条同事件信息</span>`:''}</div><div class="impact-summary"><b>决策范围：</b>${esc(scope)}；<b>评分用途：</b>${esc(use)}；<b>交易用途：</b>${esc(gate)}</div>${directionReason}`;
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
  const itemRows=items.map(x=>`<div class="feed-item"><time>${esc(x.published_at||x.date||x.time||'时间缺失')}</time><b>${esc(x.title||x.summary||'未命名事件')}</b>${eventStatusHtml(x)}<span><b>影响说明：</b>${esc(impactNoteOf(x))}</span>${impactTagsHtml(x)}${sourceMetaHtml(x)}${sourceLinksHtml(x)}</div>`);
  $('macroFeed').innerHTML=[...watchRows,...itemRows].join('');
}
function renderAgentDecision(js){
  const d=js.data||{};
  const ai=d.ai_analysis||{};
  const aiView=ai.analysis||{};
  const review=d.multi_role_review||{};
  const reviewRoles=(review.roles||[]).slice(0,8);
  const debate=review.debate||{};
  const riskCommittee=review.risk_committee||{};
  const portfolioCommittee=review.portfolio_committee||{};
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
  if(review.review_id){
    const persisted=review.checkpoint?.persisted?'已写入审计':'本轮只读预览';
    chunks.push(`<div class="impact-summary"><b>多角色复核 ${esc(review.review_id)}</b> · ${esc(riskCommittee.verdict_cn||'等待风险裁决')}<br>${esc(portfolioCommittee.action_cn||'保持观察')} · ${esc(persisted)} · 不能直接创建订单</div>`);
    chunks.push(`<details class="dashboard-fold"><summary>展开五角色观点、正反辩论与复盘检查点</summary><div class="dashboard-fold-body"><div class="agent-evidence-list">${reviewRoles.map(role=>{
      const support=(role.supporting_evidence||[]).slice(0,4).join('；');
      const counter=(role.counter_evidence||[]).slice(0,4).join('；');
      const missing=(role.missing_data||[]).slice(0,4).join('；');
      return `<div class="agent-evidence"><time>${esc(role.label||role.role)} · ${esc(cnEnum(role.status||'--'))} · 置信度 ${esc(Math.round(Number(role.confidence||0)*100))}%</time><strong>${esc(role.stance||'观察')}</strong><small>${esc(role.summary||'暂无角色摘要')}</small>${support?`<div class="factor-up">支持：${esc(support)}</div>`:''}${counter?`<div class="factor-down">反证：${esc(counter)}</div>`:''}${missing?`<div class="source-note">缺失：${esc(missing)}</div>`:''}</div>`;
    }).join('')}</div><div class="split" style="margin-top:8px"><div class="notice"><b>支持观点</b><br>${esc((debate.bull_case||[]).slice(0,6).join('；')||'没有足够支持证据')}</div><div class="notice"><b>反对观点</b><br>${esc((debate.bear_case||[]).slice(0,6).join('；')||'未发现额外反证')}</div></div><div class="notice" style="margin-top:8px"><b>风险委员会：</b>${esc(riskCommittee.verdict_cn||'等待裁决')}<br>${esc((riskCommittee.blocking_reasons||[]).slice(0,8).join('；')||'没有新增阻断项')}<br><b>复盘：</b>${esc(review.retrospective?.status||'等待结果')}，对照 ${esc((review.retrospective?.compare_with||[]).join('、')||'买入持有与宽基指数')}。</div></div></details>`);
  }
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
  const refresh=Math.max(30,Math.min(90,Number(js.refresh_seconds||data.refresh_seconds||35)));
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
  const tickerItems=items.slice(0,24).map(x=>`<span class="ticker-item"><b>${esc(['official_confirmed','multi_source_confirmed'].includes(String(x.confirmation_level||''))?'已确认':'快讯')}</b><span>${esc(x.title||'未命名快讯')}</span></span>`).join('');
  $('globalTickerTrack').innerHTML=tickerItems+tickerItems;
  $('globalStream').innerHTML=items.slice(0,18).map(x=>{
    return `<div class="feed-item ${x.is_jin10?'jin10':''}"><div class="stream-meta"><time>${esc(x.published_at||'时间缺失')}</time><i>${esc(sourceLabelOf(x))}</i><span>${esc(cnEnum(x.category||x.message_dimension||'全球快讯'))}</span></div><b>${esc(x.title||'未命名快讯')}</b>${eventStatusHtml(x)}<span>${esc(x.summary||'')}</span><span>来源：${esc(sourceLabelOf(x))}</span><span><b>影响说明：</b>${esc(impactNoteOf(x))}</span>${impactTagsHtml(x,'影响对象')}${sourceMetaHtml(x)}${sourceLinksHtml(x)}</div>`;
  }).join('');
}

function renderScoreExplain(row,currentDecision={}){
  const b=row?.score_breakdown||row||{};
  const market={...(b?.sources?.market||{}),...(row?.market_regime||{})};
  const globalContext=market.global_context||{};
  const configuredGlobal=currentComboSet().has('global_sector_reference');
  const globalEnabled=typeof market.global_reference_enabled==='boolean'?market.global_reference_enabled:configuredGlobal;
  const globalUsed=!!market.global_score_used;
  const globalScore=finiteNumber(market.global_score??globalContext.score);
  const globalWeight=finiteNumber(market.global_weight)??0;
  const globalState=globalUsed?'已启用并参与本轮环境分':globalEnabled?'已启用，但证据缺失/过期，本轮权重为0%':'未启用，仅展示行情、本轮权重为0%';
  const globalCalc=globalUsed&&globalScore!==null?`；${globalScore.toFixed(1)} × ${(globalWeight*100).toFixed(0)}% = ${(globalScore*globalWeight).toFixed(2)} 环境分`:'';
  if($('globalScoreContribution'))$('globalScoreContribution').innerHTML=`<b>当前个股 ${esc(row?.symbol||primarySymbol())}</b>：全球行业走势参照 ${esc(globalState)}；参考 ${esc(globalContext.focus_label||'等待行业映射')}${esc(globalCalc)}。这里的15%只在“大盘情绪”内部，不是综合总分的15%。`;
  const adaptive=b.adaptive_policy||{};
  const adaptiveWeights=adaptive.weights||{};
  const adaptiveThresholds=adaptive.thresholds||b.thresholds||{};
  const weightLabels={technical:'技术面',fundamental:'基本面',information:'信息面',fund_flow:'资金面',market:'大盘情绪'};
  if(Object.keys(adaptiveWeights).length){
    $('scorePolicyWeights').innerHTML=['technical','fundamental','information','fund_flow','market'].map(key=>`<span><b>${(Number(adaptiveWeights[key]||0)*100).toFixed(0)}%</b>${weightLabels[key]}</span>`).join('');
    $('scorePolicySummary').textContent=`${adaptive.strategy_label||'自适应策略'} · ${adaptive.market_band||'市场档位缺失'} · ${adaptive.weight_mode==='manual'?'手工权重':'策略自适应'}；买入 ${adaptiveThresholds.buy??'--'}，加仓 ${adaptiveThresholds.add??'--'}，减仓/卖出 ${adaptiveThresholds.reduce_or_sell??'--'}，仓位系数 ${adaptive.position_scale??'--'}。`;
  }
  const currentScores=currentDecision?.current_dimension_scores||{};
  const currentDimensions=Array.isArray(currentDecision?.dimensions)?currentDecision.dimensions:[];
  const currentMarket=currentDecision?.market_context||{};
  const currentEntries=[...currentDimensions,currentMarket.label?{...currentMarket,key:'market'}:null].filter(Boolean);
  const currentRows=currentEntries.map(x=>{
    const score=finiteNumber(currentScores[x.key]??x.score);
    const weight=finiteNumber(x.configured_weight);
    const status=x.ready?'当前可用':'当前未参与';
    return `<div class="score-contribution"><b>${esc(x.label||cnEnum(x.key)||'评分维度')} · ${status}</b><small>${score!==null?score.toFixed(1)+'分':'分数缺失'}｜目标权重 ${weight!==null?(weight*100).toFixed(0)+'%':'未配置'}｜${esc(cnEnum(x.quality_status||'missing'))}｜${esc(x.source||'来源缺失')}</small></div>`;
  }).join('');
  const currentNote=currentEntries.length?`<div class="notice"><b>当前缓存只读评估（不生成订单）</b><small>${esc(currentDecision.snapshot_note||'当前卡片来自本地真实缓存重建；只有下一轮实时模拟/实盘决策通过新鲜度和风险门禁后，才会形成新的落库交易分。')}</small>${currentRows}</div>`:'';
  const historicalTime=row?.timestamp||row?.decision_time||'时间缺失';
  const contributions=Array.isArray(b.contributions)?b.contributions:[];
  const sourceRows=contributions.length?contributions:[
    ['筛选底座',row?.screening_score??b.screening_score],['基本面',row?.fundamental_score??b.fundamental_score],['实时择时',row?.technical_score??b.technical_score],['近期信息',row?.information_score??b.information_score],['量价资金',row?.fund_flow_score??b.fund_flow_score],['大盘环境',row?.market_score??row?.market_regime_score??b.market_score],
  ].filter(x=>finiteNumber(x[1])!==null).map(x=>({label:x[0],score:finiteNumber(x[1]),normalized_weight:null,contribution:null}));
  const lines=sourceRows.map(x=>{
    const weight=finiteNumber(x.normalized_weight),contribution=finiteNumber(x.contribution),score=finiteNumber(x.score);
    const calc=weight!==null&&contribution!==null&&score!==null?`${score.toFixed(1)} × ${(weight*100).toFixed(1)}% = ${contribution.toFixed(2)} 分`:`原始分 ${score!==null?score.toFixed(1):'缺失'}；等待本轮信号计算实际权重`;
    return `<div class="score-contribution"><b>${esc(x.label||x.key||'评分维度')}</b><small>${esc(calc)}</small></div>`;
  }).join('');
  const final=finiteNumber(row?.final_score??b.final_score??row?.final_trade_score);
  const before=finiteNumber(b.score_before_risk),deduct=finiteNumber(b.anomaly_deduction)??0;
  const timing=b.timing_formula||'实时择时分 = 日K结构55% + 当日分时45%';
  const missing=(b.missing_dimensions||row?.missing_data||[]).map(cnEnum).filter(Boolean);
  const invalid=Array.isArray(b.invalid_dimensions)?b.invalid_dimensions:[];
  const excluded=Array.isArray(b.excluded_by_readiness)?b.excluded_by_readiness:[];
  const auditOnly=Array.isArray(b.audit_only_dimensions)?b.audit_only_dimensions:[];
  const eventContext=row?.market_event_context||{};
  const eventFactors=Array.isArray(b.event_factors)?b.event_factors:(eventContext.factors||[]);
  const marketAdj=finiteNumber(b.market_event_adjustment??eventContext.market_adjustment)??0;
  const infoAdj=finiteNumber(b.information_event_adjustment??eventContext.information_adjustment)??0;
  const pit=eventContext.pit_input_status||{};
  const coverage=Array.isArray(eventContext.standard_factor_coverage)?eventContext.standard_factor_coverage:[];
  const pitDatasets=pit.datasets||{};
  const pitHits=Object.entries(pitDatasets).filter(([,x])=>x?.status==='available');
  const pitHtml=`<div class="event-factor-list"><div class="event-factor"><div><b>结构化事件覆盖</b><span>${eventContext.standard_factor_available??0} / ${eventContext.standard_factor_total??8} 项</span></div><small>${esc(pit.rule||'只使用不晚于决策时点、来源可追溯的快照。')}</small>${pitHits.length?pitHits.map(([key,x])=>`<small>${esc(cnEnum(key))}：${esc(x.source||'来源缺失')}｜${esc(x.available_at||'时间缺失')}｜记录 ${esc(x.record_id||'--')}</small>`).join(''):'<small>当前没有命中的结构化 PIT 快照，文字快讯仅用于有限事件解释。</small>'}</div>${coverage.length?`<details><summary>查看八项因子缺失原因</summary>${coverage.map(x=>`<div class="score-contribution"><b>${esc(x.factor_name_cn||cnEnum(x.factor_key))}</b><small>${x.status==='available'?'已进入本轮事件调整':esc(x.missing_reason||'近期没有可追溯证据')}</small></div>`).join('')}</details>`:''}</div>`;
  const factorHtml=eventFactors.length?`<div class="event-factor-list">${eventFactors.slice(0,8).map(x=>{
    const adj=Number(x.adjustment||0);const cls=adj>0?'factor-up':adj<0?'factor-down':'';const chain=(x.mapped_chain||[]).join(' → ');
    return `<div class="event-factor"><div><b>${esc(x.factor_name_cn||cnEnum(x.factor_key)||'市场事件')}</b><span class="${cls}">${adj>=0?'+':''}${adj.toFixed(2)} 分 · ${esc(x.scope||'影响范围缺失')}</span></div><small>${esc(x.explanation||'说明缺失')}</small>${chain?`<small>传导链：${esc(chain)}</small>`:''}<small>来源：${esc(x.source||'来源缺失')}｜${esc(x.published_at||'时间缺失')}｜置信度 ${Number.isFinite(Number(x.confidence))?(Number(x.confidence)*100).toFixed(0)+'%':'缺失'}</small>${x.source_ref?`<a href="${esc(x.source_ref)}" target="_blank" rel="noopener noreferrer">查看来源</a>`:''}</div>`;
  }).join('')}</div>`:'<div class="muted">近期没有进入评分的可追溯市场事件；全球快讯不会自动等同于个股利好或利空。</div>';
  const normalizedTotal=finiteNumber(b.normalized_weight_total);
  const adaptiveHtml=Object.keys(adaptive).length?`<div class="notice"><b>执行策略：${esc(adaptive.strategy_label||adaptive.strategy_family||'未标明')}｜市场档位：${esc(adaptive.market_band||'未标明')}｜${adaptive.weight_mode==='manual'?'手工权重':'自适应权重'}</b><small>实际阈值：买入 ${esc(adaptiveThresholds.buy??'--')} / 加仓 ${esc(adaptiveThresholds.add??'--')} / 减仓卖出 ${esc(adaptiveThresholds.reduce_or_sell??'--')}；仓位系数 ${esc(adaptive.position_scale??'--')}</small><small>${esc((adaptive.rationale||[]).join('；')||'暂无调整说明')}</small></div>`:'';
  $('scoreExplain').innerHTML=`${currentNote}${adaptiveHtml}<div class="mini"><b>最近一次落库决策快照 · ${esc(historicalTime)}</b><br>${esc(b.formula||'综合交易分 = 各可用维度按实际权重汇总 - 异常风险扣分')}</div><div class="mini">${esc(timing)}</div>${lines||'<span class="muted">尚无可解释的评分维度。</span>'}<div class="score-total"><b>该快照风险前 ${before!==null?before.toFixed(2):'--'} 分 - 异常扣分 ${deduct.toFixed(2)} = 最终 ${final!==null?final.toFixed(2):'--'} 分</b><small>有效权重合计 ${normalizedTotal!==null?(normalizedTotal*100).toFixed(1)+'%':'等待本轮信号'}；筛选总分${b.screening_fallback_used?'仅因分项全缺失而低置信兜底':'只作审计对照，不与分项重复计票'}。</small></div><details><summary>该快照市场事件调整：大盘 ${marketAdj>=0?'+':''}${marketAdj.toFixed(2)} 分 / 个股信息 ${infoAdj>=0?'+':''}${infoAdj.toFixed(2)} 分</summary>${pitHtml}${factorHtml}</details>${auditOnly.length?`<div class="notice">该历史快照的审计对照、不计入：${esc(auditOnly.join('、'))}。</div>`:''}${excluded.length?`<div class="warn">该历史快照曾被真实性/新鲜度门禁剔除：${esc(excluded.map(x=>`${cnEnum(x.key||'未知')} 原始${x.raw_score??'缺失'}分（${x.reason||cnEnum(x.quality_status)||'质量不足'}）`).join('；'))}。</div>`:''}${invalid.length?`<div class="warn">该历史快照的无效分值已剔除：${esc(invalid.map(x=>(x.key||'未知')+'='+String(x.value)).join('、'))}。</div>`:''}${missing.length?`<div class="warn">该历史快照缺失：${esc(missing.join('、'))}；不代表上方当前只读评估仍然缺失。</div>`:''}`;
}
function renderDimensionReadiness(payload,row={}){
  const d=payload?.data||payload||row?.dimension_readiness||{};
  const dimensions=Array.isArray(d.dimensions)?d.dimensions:[];
  const market=d.market_context||{};
  const entries=[...dimensions,market.label?{...market,key:'market',required:false}:null].filter(Boolean);
  const eligible=!!d.auto_entry_eligible;
  const blocks=d.entry_block_reasons||[];
  const warnings=d.warnings||[];
  const freshness=d.provenance_freshness||{};
  const refreshScope={fundamental:'fundamentals',technical:'kline',information:'information',fund_flow:'capital',market:'global_market'};
  const scoreAge=Number(freshness.age_seconds);
  const freshnessText=freshness.status?`<div class="notice ${freshness.recent_for_live?'ok':'warn'}"><b>评分时效：${esc(freshness.status)}</b>${Number.isFinite(scoreAge)?`｜已过去 ${Math.round(scoreAge)} 秒` : ''}｜实盘上限 ${esc(freshness.max_age_seconds??'--')} 秒</div>`:'';
  const rows=entries.map(x=>{
    const state=x.ready?'ready':x.required?'blocked':'optional';
    const stateText=x.ready?'本轮可用':x.required?'阻断入场':'未参与';
    const score=finiteNumber(x.score);
    const configured=finiteNumber(x.configured_weight);
    const missing=Array.isArray(x.missing_reasons)?x.missing_reasons.filter(Boolean):[];
    const scope=refreshScope[x.key]||'quote';
    return `<div class="dimension-row"><div><b>${esc(x.label||cnEnum(x.key)||'决策维度')} ${score!==null?score.toFixed(1)+'分':'--'}</b><span class="dimension-state ${state}">${stateText}</span></div><small>${esc(x.role||'')}</small><small>目标权重：${configured!==null?(configured*100).toFixed(0)+'%':'未配置'}｜用途：${esc(x.usage||'未说明')}｜质量：${esc(cnEnum(x.quality_status||'missing'))}｜来源：${esc(x.source||'数据源缺失')}</small>${x.truth_boundary?`<small>真实性边界：${esc(x.truth_boundary)}</small>`:''}${x.reason?`<small class="warn">${esc(x.reason)}</small>`:''}${missing.length&&missing.join('；')!==String(x.reason||'')?`<small class="warn">缺失明细：${esc(missing.join('；'))}</small>`:''}<button class="dimension-refresh" onclick="refreshDecisionDimension('${scope}',this)">刷新${esc(x.label||cnEnum(x.key)||'此项')}</button></div>`;
  }).join('');
  $('dimensionReadiness').innerHTML=`${freshnessText}<div class="notice ${eligible?'ok':'warn'}"><b>${eligible?'决策维度门禁通过，可继续进入风控':'当前禁止自动新增仓位'}</b><br>${esc(blocks.join('；')||'仍需通过数据新鲜度、风险网关、仓位和人工确认。')}</div>${d.snapshot_note?`<div class="mini">${esc(d.snapshot_note)}</div>`:''}<div class="dimension-grid">${rows||'<span class="muted">暂无完整性快照，请先运行筛选或模拟评分。</span>'}</div>${warnings.length?`<div class="muted">未参与/提醒：${esc(warnings.join('；'))}</div>`:''}<div class="mini">${esc(d.execution_score_policy||'执行分与审计分的角色尚未载入。')}</div>`;
}
async function refreshDecisionDimension(scope,btn){
  return withAction(btn,'刷新中','该决策维度已重新核对',async()=>{
    const symbol=primarySymbol();
    const result=await api('/api/data-center/refresh',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({symbols:[symbol],scopes:[scope],force:true,mode:'realtime_paper',strategy_family:$('strategy')?.value||'swing'})});
    const framework=await api('/api/decision-framework/'+encodeURIComponent(symbol)+'?mode=realtime_paper&strategy_family='+encodeURIComponent($('strategy')?.value||'swing'));
    const data=framework.data||framework;const current=data.current_readiness?.dimensions?{...data.current_readiness,current_dimension_scores:data.current_dimension_scores||{},snapshot_note:data.current_snapshot_note||''}:data;
    renderDimensionReadiness({data:current});
    const failures=(result.results||[]).filter(x=>!x.ok);
    if(failures.length)showActionToast(failures.map(x=>x.summary||x.error||'数据仍缺失').join('；'),'bad');
    $('auditLog').textContent='单项数据刷新 '+new Date().toLocaleTimeString()+'\\n'+JSON.stringify(result.results||[],null,2);
    return result;
  });
}
function sectorMoney(v){
  const n=Number(v);if(!Number.isFinite(n))return'字段缺失';
  const sign=n>0?'+':'';const a=Math.abs(n);
  return sign+(a>=1e8?(n/1e8).toFixed(2)+'亿':a>=1e4?(n/1e4).toFixed(1)+'万':n.toFixed(0));
}
function setSectorFilter(value){sectorFilter=value||'all';const select=$('sectorFilterSelect');if(select&&select.value!==sectorFilter)select.value=sectorFilter;renderSectorMainline(sectorMainlineData||{})}
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
function renderGlobalMarketSentiment(js){
  const d=js?.data||js?.global_market_sentiment||js||{};const selected=d.selected_evidence||[];const score=finiteNumber(d.score);const valid=!!d.valid_for_score;
  $('globalMarketScore').textContent=score!==null?score.toFixed(1)+' 分':'证据不足';
  $('globalMarketFocus').textContent=`${d.requested_symbol||primarySymbol()} · ${d.focus_label||'全球宽基背景'} · ${d.selection_mode||'等待映射'}`;
  $('globalMarketLabel').textContent=(d.label||'数据不足')+' · '+(valid?'可供环境策略使用，是否计分由“全球行业走势参照”开关决定，权重上限15%':'证据不足，不进入自动交易分');
  const status=$('globalMarketStatus');const cache=d.cache_status||{};status.textContent=`${d.focus_label||'宽基'} · ${cnEnum(d.quality_status||'missing')} · ${selected.length}组 · ${cnEnum(cache.status||'--')}`;status.className='pill '+(valid?'good':'warn');
  $('globalMarketEvidence').innerHTML=selected.length?selected.slice(0,4).map(x=>{
    const change=Number(x.change_pct);const href=x.source_ref||'';const phase=x.session_phase||'时段未知';const weight=Number(x.normalized_weight);
    const role=x.benchmark_role||'全球背景';
    return `<div class="global-market-item ${role==='行业基准'?'industry':''}"><small class="global-market-role">${esc(role)}</small><b>${esc(x.name||x.key||'全球市场')}</b><span class="${pnlClass(change)}">${Number.isFinite(change)?(change>0?'+':'')+change.toFixed(2)+'%':'涨跌缺失'} · ${esc(phase)}</span><small>${esc(x.observed_at||'行情时间缺失')}｜实际权重 ${Number.isFinite(weight)?(weight*100).toFixed(0)+'%':'--'}</small><small>${esc(x.phase_reason||'')}</small>${href?`<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">查看行情来源</a>`:''}</div>`;
  }).join(''):`<div class="global-market-item"><b>本轮不计分</b><small>${esc((d.missing_reasons||['真实全球市场证据不足']).join('；'))}</small></div>`;
  const terms=(d.matched_terms||[]).join('、')||'未匹配具体行业词';
  const focusMode=d.focus_source==='explicit'?'手工观察板块':'按当前股票自动映射';
  $('globalMarketPolicy').innerHTML=`<b>当前面板：</b>${esc(focusMode)}。手工选择只改变本观察面板；自动交易会按每只股票分别映射，并由策略“全球行业走势参照”决定是否计分。<br><b>映射依据：</b>${esc(d.focus_reason||'仅使用全球宽基背景')}<br><b>命中词：</b>${esc(terms)}；置信度 ${esc(d.focus_confidence||'--')}<br>${esc(d.time_alignment_policy||'按各市场开盘时间区分实时和前收盘。')}<br>${esc(d.correlation_policy||'相关指数只取一项。')}<br>${esc(d.truth_boundary||'缺失和过期数据不进入自动交易分。')}`;
}
async function loadGlobalMarketSentiment(force=false,btn=null,focusOverride=null){
  const manualFocus=focusOverride===null?($('globalSectorFocus')?.value||''):String(focusOverride||'');
  const requestSeq=++globalMarketRequestSeq;
  const run=async()=>{
    const status=$('globalMarketStatus');if(status){status.textContent=`${manualFocus||'自动识别'} · 更新中`;status.className='pill warn'}
    const js=await api('/api/market/global-sentiment?force='+(force?'true':'false')+'&symbol='+encodeURIComponent(primarySymbol())+'&industry='+encodeURIComponent(manualFocus));
    if(requestSeq===globalMarketRequestSeq)renderGlobalMarketSentiment(js);
    return js;
  };
  return btn?withAction(btn,'刷新中','全球行情已更新',run):run();
}
function changeGlobalSectorFocus(value,btn=null){
  const nextFocus=String(value||'');
  if($('globalSectorFocus'))$('globalSectorFocus').value=nextFocus;
  localStorage.setItem('qd-global-sector-focus',nextFocus);
  return loadGlobalMarketSentiment(false,btn,nextFocus).catch(error=>showToast('行业参照更新失败：'+error,'bad'));
}
function renderCapitalEvidence(js){
  const d=js?.data||js?.capital_evidence||js||{};const pub=d.public_daily_flow||{};const latest=pub.latest||{};const intra=d.intraday_proxy||{};const holding=d.institutional_holdings||{};const score=finiteNumber(d.score);
  const status=$('capitalEvidenceStatus');status.textContent=`${d.name||primarySymbol()} · ${score!==null?score.toFixed(1)+'分':'证据不足'} · ${cnEnum(d.quality_status||'missing')}`;status.className='pill '+(score!==null?'good':'warn');
  const ratio=v=>{const n=finiteNumber(v);return n!==null?`${n>0?'+':''}${n.toFixed(2)}%`:'字段缺失'};
  const windows=intra.windows||{};const windowHtml=[5,15,30,60].map(m=>{const x=windows[String(m)]||{};return `<span>${m}分<br><b class="${Number(x.net_proxy)>=0?'ok':'bad'}">${ratio(x.net_ratio_pct)}</b></span>`}).join('');
  const top=(holding.top_funds||[]).slice(0,4).map(x=>`${x.fund_name||x.fund_code||'基金'} ${x.float_share_pct==null?'占比缺失':Number(x.float_share_pct).toFixed(2)+'%'}`).join('；')||'暂无可展示基金明细';
  const links=[];if(pub.source_ref)links.push(`<a href="${esc(pub.source_ref)}" target="_blank" rel="noopener noreferrer">公开资金流来源</a>`);if(holding.source_ref)links.push(`<a href="${esc(holding.source_ref)}" target="_blank" rel="noopener noreferrer">基金持仓披露来源</a>`);
  $('capitalEvidence').innerHTML=`<div class="capital-grid"><div class="capital-card"><span>公开日资金流 · ${esc(latest.date||'日期缺失')}</span><b class="${Number(latest.main_net_inflow)>=0?'ok':'bad'}">主力净流 ${latest.main_net_inflow==null?'字段缺失':sectorMoney(latest.main_net_inflow)}</b><small>净流占比 ${ratio(latest.main_net_ratio_pct)}；近30日记录 ${pub.row_count??0} 条</small><small>${esc(pub.truth_boundary||'公开口径不等于真实机构账户。')}</small></div><div class="capital-card"><span>当日全天量价代理 · ${esc(intra.latest_at||'时间缺失')}</span><b class="${Number(intra.net_proxy)>=0?'ok':'bad'}">净额代理 ${intra.net_proxy==null?'字段缺失':sectorMoney(intra.net_proxy)}</b><small>估算流入 ${intra.estimated_inflow==null?'缺失':sectorMoney(intra.estimated_inflow)} / 流出 ${intra.estimated_outflow==null?'缺失':sectorMoney(intra.estimated_outflow)}</small><div class="capital-window">${windowHtml}</div><small>${esc(intra.truth_boundary||'按价格方向与成交额估算，不等于逐笔主动买卖。')}</small></div><div class="capital-card"><span>基金持仓披露 · ${esc(holding.report_date||'报告期缺失')}</span><b>${holding.fund_count??0} 只基金 · ${holding.total_disclosed_shares==null?'股数缺失':Number(holding.total_disclosed_shares).toLocaleString()+'股'}</b><small>较上一披露 ${holding.shares_change==null?'不可比':(Number(holding.shares_change)>=0?'+':'')+Number(holding.shares_change).toLocaleString()+'股'}</small><small>${esc(top)}</small><small>${esc(holding.truth_boundary||'披露期数据存在时滞，不代表当前实时机构持仓。')}</small></div><div class="capital-card"><span>数据完整性与限制</span><b>${esc((d.evidence_fields||[]).map(cnEnum).join('、')||'暂无可评分证据')}</b><small>${esc((d.missing_reasons||[]).join('；')||'当前字段已取得；仍需遵守来源口径。')}</small><small>${esc(d.truth_boundary||'没有真实数据时不生成资金结论。')}</small><div class="capital-links">${links.join('')}</div></div></div>`;
}
async function loadCapitalEvidence(force=false,btn=null){
  const run=async()=>{const js=await api('/api/market/capital-evidence/'+encodeURIComponent(primarySymbol())+'?force='+(force?'true':'false')+'&allow_network='+(force?'true':'false'));renderCapitalEvidence(js);return js};
  return btn?withAction(btn,'刷新中','个股资金证据已更新',run):run();
}
function renderScoreTrend(payload,status){
  const canvas=$('scoreTrendCanvas');if(!canvas)return;
  const rows=(payload?.data||[]).filter(x=>finiteNumber(x.final_score)!==null);
  const box=canvas.getBoundingClientRect();const dpr=Math.max(1,window.devicePixelRatio||1);
  const width=Math.max(320,Math.round(box.width||canvas.clientWidth||640));const height=Math.max(84,Math.round(box.height||96));
  canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
  const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
  const pad={left:34,right:12,top:12,bottom:24};const plotW=width-pad.left-pad.right;const plotH=height-pad.top-pad.bottom;
  ctx.font='11px sans-serif';ctx.lineWidth=1;ctx.textBaseline='middle';
  [0,25,50,75,100].forEach(value=>{const y=pad.top+plotH*(1-value/100);ctx.strokeStyle='#263751';ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(width-pad.right,y);ctx.stroke();ctx.fillStyle='#7f94b2';ctx.fillText(String(value),4,y)});
  const history=status?.history||{};
  $('dailyScoreStatus').textContent=`交易池 ${status?.target_count??0} 只 · 最近每日评分 ${history.latest_score_date||'尚未生成'} · ${status?.run_at||'15:10'} 收盘后自动保存`;
  if(!rows.length){ctx.fillStyle='#9cb0ca';ctx.textAlign='center';ctx.fillText('暂无评分历史；加入模拟/实盘观察池后会在交易日自动留痕',width/2,pad.top+plotH/2);ctx.textAlign='left';return}
  const timestamp=x=>Date.parse(x.timestamp||x.score_date||'')||0;const ordered=[...rows].sort((a,b)=>timestamp(a)-timestamp(b));
  const first=timestamp(ordered[0]);const last=timestamp(ordered[ordered.length-1]);const span=Math.max(1,last-first);
  const xOf=(row,index)=>ordered.length===1?pad.left+plotW/2:pad.left+plotW*((timestamp(row)-first)/span||index/(ordered.length-1));
  const yOf=row=>pad.top+plotH*(1-Math.max(0,Math.min(100,Number(row.final_score)))/100);
  const colors={daily_pool:'#22c55e',intraday_provenance:'#60a5fa',screener:'#f59e0b'};
  Object.keys(colors).forEach(kind=>{const subset=ordered.map((row,index)=>({row,index})).filter(item=>item.row.source_kind===kind);if(!subset.length)return;ctx.strokeStyle=colors[kind];ctx.lineWidth=2;ctx.beginPath();subset.forEach((item,i)=>{const x=xOf(item.row,item.index),y=yOf(item.row);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();ctx.fillStyle=colors[kind];subset.forEach(item=>{ctx.beginPath();ctx.arc(xOf(item.row,item.index),yOf(item.row),2.5,0,Math.PI*2);ctx.fill()})});
  const latest=ordered[ordered.length-1];ctx.fillStyle='#c9d7eb';ctx.textAlign='right';ctx.fillText(`${latest.score_date||''} · ${Number(latest.final_score).toFixed(1)}分`,width-pad.right,height-9);ctx.textAlign='left';
}
async function runDailyScore(btn){
  return withAction(btn,'评分中','今日交易池评分已保存',async()=>{
    const result=await api('/api/score/daily/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({force:true,refresh:false,limit:80})});
    const [trend,status]=await Promise.all([api('/api/score/trend/'+encodeURIComponent(primarySymbol())+'?days=180&mode=all'),api('/api/score/daily/status')]);
    renderScoreTrend(trend,status);return result;
  });
}
async function loadDashboardCoreOverview(){
  const keys=['broker','sessions','records','data_center','queue','live_account','live_positions','auto_config','readiness','live_reviews','review_schedule','paper_schedule'];
  try{
    const overview=await api('/api/auto-trading/dashboard-overview?records_limit=30');
    if(overview?.ok&&overview.data){
      const failedKeys=new Set((overview.component_errors||[]).map(x=>String(x.key||'')));
      if(failedKeys.has('live_sync')){failedKeys.add('live_account');failedKeys.add('live_positions')}
      return keys.map(key=>failedKeys.has(key)
        ?{status:'rejected',reason:new Error((overview.component_errors||[]).find(x=>x.key===key)?.error||key+' unavailable')}
        :{status:'fulfilled',value:overview.data[key]||{}});
    }
  }catch(error){
    console.warn('auto trading dashboard overview fallback',error);
  }
  return Promise.allSettled([
    api('/api/live-broker/status'),
    api('/api/realtime-paper/sessions'),
    api('/api/trading-records?limit=30'),
    api('/api/data-center/status'),
    api('/api/live/confirm-queue'),
    api('/api/live/account'),
    api('/api/live/positions'),
    api('/api/auto-trading/config'),
    api('/api/auto-trading/readiness'),
    api('/api/live/position-reviews?limit=50'),
    api('/api/position-reviews/scheduler/status'),
    api('/api/realtime-paper/scheduler/status')
  ]);
}
async function refreshAll(btn=null){
  if(workbenchRefreshPromise)return workbenchRefreshPromise;
  const task=withAction(btn,'刷新中','总控台已更新',async()=>{
  try{
    renderModuleCards();
    setText('scoreTime','正在更新核心状态…');
    const extraPromise=Promise.allSettled([api('/api/score/latest/'+encodeURIComponent(primarySymbol())),api('/api/macro/global-events?limit=80'),loadGlobalStream(false),api('/api/agent/market-brief?symbols='+encodeURIComponent(symbols().join(','))+'&limit=80'),api('/api/market/sectors/mainline?limit=50&include_concept=true'),api('/api/realtime-paper/signals?limit=100'),api('/api/market/event-factors/'+encodeURIComponent(primarySymbol())),api('/api/integrations/tonghuashun/status'),api('/api/decision-framework/'+encodeURIComponent(primarySymbol())+'?mode=realtime_paper&strategy_family='+encodeURIComponent($('strategy')?.value||'hybrid')),loadGlobalMarketSentiment(false),api('/api/market/capital-evidence/'+encodeURIComponent(primarySymbol())+'?force=false&allow_network=false'),api('/api/live-broker/setup'),api('/api/notifications/mobile/status'),api('/api/score/trend/'+encodeURIComponent(primarySymbol())+'?days=180&mode=all'),api('/api/score/daily/status')]);
    const core=await loadDashboardCoreOverview();
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
    const score=extraValue(0),macro=extraValue(1,{items:[]}),agent=extraValue(3,{data:{}}),sectors=extraValue(4,{items:[],missing_reasons:['板块服务暂不可用']}),signalData=extraValue(5,{data:[]}),eventData=extraValue(6,{data:{}}),ths=extraValue(7,{}),dimensionData=extraValue(8,{data:{}}),globalMarket=extraValue(9,{data:{missing_reasons:['全球市场服务暂不可用']}}),capitalData=extraValue(10,{data:{missing_reasons:['个股资金服务暂不可用']}}),brokerSetup=extraValue(11,{}),mobileAlerts=extraValue(12,{}),scoreTrend=extraValue(13,{data:[]}),dailyScoreStatus=extraValue(14,{});
    renderGlobalFeed(macro);renderAgentDecision(agent);renderSectorMainline(sectors);renderCapitalEvidence(capitalData);renderScoreTrend(scoreTrend,dailyScoreStatus);
    renderTonghuashun(ths);renderBrokerSetup(brokerSetup,brokerSetup.selected_broker||'qmt');renderMobileAlertStatus(mobileAlerts);
    const signalRows=signalData.data||[];
    const liveSignal=signalRows.find(x=>String(x.symbol||'')===primarySymbol())||null;
    const latest={...(liveSignal||score.data||{})};
    if(!latest.market_event_context)latest.market_event_context=eventData.data||{};
    latest.score_breakdown={...(latest.score_breakdown||{}),event_factors:(latest.score_breakdown?.event_factors||eventData.data?.factors||[]),market_event_adjustment:(latest.score_breakdown?.market_event_adjustment??eventData.data?.market_adjustment??0),information_event_adjustment:(latest.score_breakdown?.information_event_adjustment??eventData.data?.information_adjustment??0)};
    const s=finiteNumber(latest.final_score??latest.final_trade_score);
    const scoreFreshness=score.freshness||dimensionData?.data?.provenance_freshness||dimensionData?.provenance_freshness||{};
    const freshnessStatus=String(scoreFreshness.status||'');
    const freshnessText=scoreFreshness.recent_for_live===true?'新鲜':scoreFreshness.recent_for_live===false?'已过期/仅供复盘':freshnessStatus==='missing'?'时间缺失':'仅供审计';
    $('decisionScore').textContent='评分 '+(s!==null?s.toFixed(1):'--');$('decisionAction').textContent=liveSignal?cnAction(liveSignal.action):(s!==null?s>=70?'待确认买入':s>=55?'继续观察':'暂时回避':'等待评分');$('scoreTime').textContent=(latest.timestamp||latest.decision_time||'时间缺失')+' · '+freshnessText;
    const frameworkDecision=dimensionData?.data||{};const currentDecision=frameworkDecision.current_readiness?.dimensions?{...frameworkDecision.current_readiness,current_dimension_scores:frameworkDecision.current_dimension_scores||{},snapshot_note:frameworkDecision.current_snapshot_note||''}:frameworkDecision;const dr=(currentDecision.dimensions||currentDecision.market_context)?currentDecision:(latest.dimension_readiness||latest.score_breakdown?.dimension_readiness||{});const dm=Object.fromEntries((dr.dimensions||[]).map(x=>[x.key,x]));const currentScores=currentDecision.current_dimension_scores||{};
    const currentOrLatest=(key)=>finiteNumber(currentScores[key])??scoreFrom(latest,key);
    setScore('tech',currentOrLatest('technical'),dm.technical?.ready??null);setScore('fund',currentOrLatest('fundamental'),dm.fundamental?.ready??null);setScore('info',currentOrLatest('information'),dm.information?.ready??null);setScore('flow',currentOrLatest('fund_flow'),dm.fund_flow?.ready??null);setScore('market',currentOrLatest('market'),dr.market_context?.ready??null);
    renderScoreExplain(latest,currentDecision);
    renderDimensionReadiness((currentDecision.dimensions||currentDecision.market_context)?{data:currentDecision}:(latest.dimension_readiness||dimensionData),latest);
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
function renderTonghuashun(js){
  if(!js||!$('thsStatus'))return;
  $('thsLauncherPath').value=js.launcher_path||$('thsLauncherPath').value||'';
  $('thsOrderPath').value=js.order_app_path||$('thsOrderPath').value||'';
  $('thsEnabled').checked=!!js.enabled;
  const ready=!!js.ready_to_launch;
  $('thsStatus').innerHTML=`<b>${esc(js.integration||'同花顺本地客户端')}：${ready?'可唤起':'尚未就绪'}</b><br>模式：${esc(js.mode||'委托提醒 + 人工录入')}；行情程序：${js.launcher_exists?'已找到':'缺失'}；委托程序：${js.order_app_exists?'已找到':'缺失'}。<br>${esc(js.truth_boundary||'不会自动操作客户端或提交订单。')}${(js.missing_reasons||[]).length?'<br><span class="warn">'+esc(js.missing_reasons.join('；'))+'</span>':''}`;
}
async function saveTonghuashun(btn){return withAction(btn,'保存中','同花顺本机配置已保存',async()=>{const js=await api('/api/integrations/tonghuashun/configure',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:$('thsEnabled').checked,launcher_path:$('thsLauncherPath').value.trim(),order_app_path:$('thsOrderPath').value.trim()})});renderTonghuashun(js.data||js);$('auditLog').textContent=JSON.stringify(js,null,2);return js})}
async function launchTonghuashun(btn,target){return withAction(btn,'正在打开','已唤起客户端',async()=>{const js=await api('/api/integrations/tonghuashun/launch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({target})});$('thsReminder').textContent=js.message||'已唤起客户端';$('auditLog').textContent=JSON.stringify(js,null,2);return js})}
async function createTonghuashunReminder(btn){return withAction(btn,'正在生成','委托提醒已生成',async()=>{const body={...collectAutoConfig(),symbol:$('liveSymbol').value.trim(),side:$('liveSide').value,quantity:Number($('liveQty').value||0),limit_price:Number($('livePrice').value||0)||null,order_type:'limit',source_page:'auto-trading',reason:'总控台人工委托提醒'};const js=await api('/api/integrations/tonghuashun/reminders',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const d=js.data||{};$('thsReminder').innerHTML=`<b>${esc(d.status_cn||js.message||'已记录')}</b> · ${esc(d.symbol||body.symbol)} ${esc(d.side_cn||body.side)} ${esc(d.quantity||body.quantity)}股 @ ${esc(d.limit_price||'市价待人工确认')}<br>${esc(d.truth_boundary||'不是券商委托或成交证明。')}`;$('auditLog').textContent=JSON.stringify(js,null,2);return js})}
const savedGlobalSectorFocus=localStorage.getItem('qd-global-sector-focus')||'';
if($('globalSectorFocus')&&[...$('globalSectorFocus').options].some(option=>option.value===savedGlobalSectorFocus))$('globalSectorFocus').value=savedGlobalSectorFocus;
renderModuleCards();
refreshAll();
startGlobalStreamLoop();
</script>
</body>
</html>"""
