from __future__ import annotations

import hashlib
import html as html_lib
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

BOILERPLATE_TERMS = {
    "桌面快捷方式", "加入自选股", "客户端", "关于同花顺", "软件下载", "法律声明", "copyright",
    "header.js", "pagehead", "script src", "友情链接", "网友意见箱", "招聘英才", "网站地图",
    "意见反馈", "免责条款", "风险提示", "广告服务", "帮助中心", "浏览器", "收藏本站", "设为首页",
    "div class", "layui", "DOCTYPE", "html", "body", "head", "meta", "charset", "function", "var ", "window.",
    "document.", "return false", "加入收藏", "返回顶部", "联系我们", "公司简介", "营业执照", "ICP备案",
}

SEARCH_ENGINE_HOSTS = ("baidu.com", "so.com", "sogou.com", "m.sm.cn", "toutiao.com/search")

# 股票专页/F10页常见栏目词。单独作为标题时不是新闻；
# 若这些词只出现在一整串菜单/导航里，也应在入库前丢弃。
SECTION_ONLY_TITLES = {
    "个股研报", "同行业研报", "研究报告", "研报", "主力持仓", "龙虎榜数据", "公司资料", "相关资料",
    "现金流量表", "资产负债表", "利润表", "财务附注", "利润表附注", "现金流量表附注",
    "年度报告", "上市公告", "最新公告", "新闻公告", "公司公告", "财务分析", "经营分析", "股东股本",
    "公司大事", "分红融资", "价值分析", "行业分析", "行情走势", "业绩预测", "业绩预测详表",
    "行业地位", "行业新闻", "公司章程", "证券资料", "募资投向", "招股说明书", "新股申购",
    "千股千评", "资金流向", "大单统计", "大宗交易", "融资融券", "收入构成", "公司运作",
    "首页概览", "概念题材", "核心题材", "产品业务", "控股参股", "投资评级", "评级统计",
    "个股点评", "机构预测", "估值分析", "盘口数据", "阶段排行", "技术分析",
}
MENU_WORDS = SECTION_ONLY_TITLES | {"首页", "概览", "行情", "资讯", "股吧", "数据", "交易", "登录", "注册", "自选股", "更多"}
RAW_HTML_FRAGMENT_RE = re.compile(r"(?is)(href=|src=|class=|style=|rel=|target=|stat=|menu\s*:|padding-left|layui-|<a\b|</a>|<div|</div>|javascript:|\.phtml|/news/|/finance/|stockid/|stockpage)")

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style|noscript|iframe)[^>]*>.*?</\1>")
SPACE_RE = re.compile(r"\s+")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
HTML_JS_RE = re.compile(r"(?is)(<script|</script>|<div|</div>|class=|layui-|function\s*\(|var\s+\w+\s*=|document\.|window\.|\.js\b|\.css\b|href=|src=)")

DATE_PATTERNS = [
    re.compile(r"(?P<y>20\d{2}|19\d{2})[年\-/\.](?P<m>\d{1,2})[月\-/\.](?P<d>\d{1,2})日?(?:\s*(?P<h>\d{1,2})[:：](?P<mi>\d{1,2})(?::(?P<s>\d{1,2}))?)?"),
    re.compile(r"(?P<y>20\d{2}|19\d{2})(?P<m>\d{2})(?P<d>\d{2})(?:\s*(?P<h>\d{1,2})[:：](?P<mi>\d{1,2})(?::(?P<s>\d{1,2}))?)?"),
]
URL_DATE_RE = re.compile(r"/(20\d{2})[\-/]?(\d{2})[\-/]?(\d{2})(?:/|_|-|\.|$)")
EVENT_DATE_HINT_RE = re.compile(
    r"(?:将于|拟于|定于|计划于|召开时间[:：]?|会议时间[:：]?|生效日[:：]?|登记日[:：]?|除权除息日[:：]?|解禁日[:：]?|截止日[:：]?|交割日[:：]?|到期日[:：]?|最后交易日[:：]?|实施|召开|生效|解禁|登记|派发|披露|交割|到期)"
    r".{0,18}?((?:20\d{2}|19\d{2})[年\-/\.]\d{1,2}[月\-/\.]\d{1,2}日?)"
)
PERIOD_RE = re.compile(r"((?:20\d{2}|19\d{2})\s*(?:年|年度|一季报|半年度|半年报|三季报|年报|第一季度|第三季度)|(?:20\d{2}|19\d{2})Q[1-4])")

EVENT_TYPE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("shareholder_meeting", ("股东大会", "年度股东大会", "临时股东大会")),
    ("board_meeting", ("董事会", "监事会")),
    ("financial_report", ("年报", "半年报", "季报", "一季报", "三季报", "财报", "业绩预告", "业绩快报")),
    ("dividend", ("分红", "派息", "权益分派", "除权除息", "利润分配")),
    ("holder_change", ("减持", "增持", "回购", "质押", "解禁", "限售股")),
    ("research_report", ("研报", "研究报告", "评级", "目标价", "买入评级", "增持评级", "卖出评级")),
    ("regulatory", ("问询函", "监管函", "立案", "处罚", "纪律处分", "警示函")),
    ("contract_order", ("中标", "订单", "合同", "合作协议", "签约")),
    ("investment_project", ("投产", "扩产", "项目投资", "募投", "产能")),
    ("derivatives_settlement", ("股指期货交割", "股指期权交割", "交割日", "最后交易日", "合约到期")),
    ("market_macro", ("降息", "加息", "降准", "美债", "原油", "黄金", "汇率", "关税", "出口管制")),
]

SOURCE_REAL_TERMS = ("公告", "资讯", "快讯", "财经", "财联社", "金十", "华尔街见闻", "东方财富", "新浪", "同花顺", "巨潮", "交易所", "股吧", "雪球")
RELATION_TERMS = (
    "公告", "财报", "年报", "季报", "半年报", "业绩", "营收", "净利润", "股东大会", "董事会", "监事会", "分红",
    "回购", "增持", "减持", "质押", "解禁", "问询", "监管", "处罚", "诉讼", "中标", "订单", "合同", "项目",
    "光伏", "硅料", "组件", "新能源", "锂", "半导体", "AI", "算力", "黄金", "原油", "券商", "地产", "消费", "出口", "关税",
)


def strip_html_boilerplate(text: Any, max_len: int = 4000) -> str:
    if text is None:
        return ""
    s = html_lib.unescape(str(text))
    s = SCRIPT_STYLE_RE.sub(" ", s)
    s = TAG_RE.sub(" ", s)
    for term in BOILERPLATE_TERMS:
        s = s.replace(term, " ")
    s = SPACE_RE.sub(" ", s).strip()
    return s[:max_len]


def is_page_chrome_summary(text: Any) -> bool:
    """Detect page navigation/disclaimer text that is not article evidence."""
    value = strip_html_boilerplate(text, max_len=2400)
    if not value:
        return False
    boilerplate_markers = (
        "股 港股 期货 外汇 黄金 银行 基金",
        "数据中心 全球财经快讯 行情中心",
        "东方财富网 > 数据中心 > 公告大全",
        "个股公告查询",
        "郑重声明 本网不保证其真实性和客观性",
        "行情中心 指数 | 期指 | 期权 | 个股",
    )
    marker_hits = sum(1 for marker in boilerplate_markers if marker in value)
    nav_terms = sum(value.count(term) for term in ("行情", "基金", "研报", "数据中心", "公告大全", "自选股"))
    return marker_hits >= 1 or (nav_terms >= 8 and "本公司及董事会" not in value)


def chinese_count(text: str) -> int:
    return len(CHINESE_RE.findall(text or ""))


def chinese_ratio(text: str) -> float:
    s = re.sub(r"\s+", "", text or "")
    if not s:
        return 0.0
    return chinese_count(s) / max(len(s), 1)


def is_search_engine_url(url: str) -> bool:
    u = (url or "").lower()
    host = urlparse(u).netloc.lower()
    return any(h in host or h in u for h in SEARCH_ENGINE_HOSTS)


def _norm_title_token(title: str) -> str:
    return re.sub(r"[\s　:：|｜/\\\-—_]+", "", title or "")


def is_menu_or_table_fragment(title: str, summary: str = "") -> bool:
    raw = f"{title or ''} {summary or ''}"
    cleaned = strip_html_boilerplate(raw, max_len=1600)
    nt = _norm_title_token(title)
    # 单独栏目词/表名不是新闻；真实公告一般会带公司名、年度、事项或完整句式。
    if nt in {_norm_title_token(x) for x in SECTION_ONLY_TITLES}:
        return True
    # HTML属性残片 + 多个栏目词，典型为股票页菜单或表格导航。
    menu_hits = sum(1 for w in MENU_WORDS if w and w in cleaned)
    raw_hit = bool(RAW_HTML_FRAGMENT_RE.search(raw))
    has_sentence = bool(re.search(r"[。！？；，：].{6,}", cleaned)) or any(k in cleaned for k in ["公告称", "显示", "披露", "表示", "同比", "将于", "召开", "发布"])
    if raw_hit and menu_hits >= 3 and not has_sentence:
        return True
    # 一整串菜单词，没有有效句子，也没有明确发布时间/事件事项。
    if menu_hits >= 6 and not has_sentence:
        return True
    # 常见链接路径/属性残留，且正文很短，基本不是文章详情正文。
    if raw_hit and chinese_count(cleaned) < 80 and not has_sentence:
        return True
    return False


def is_boilerplate_title(title: str) -> bool:
    t = (title or "").strip()
    tl = t.lower()
    if not t or len(t) < 4:
        return True
    if len(t) > 120:
        return True
    if chinese_count(t) < 2 and not re.search(r"[A-Za-z]{3,}", t):
        return True
    if any(term.lower() in tl for term in BOILERPLATE_TERMS):
        return True
    if HTML_JS_RE.search(t):
        return True
    nav_tokens = {"首页", "行情中心", "数据中心", "下载中心", "新闻中心", "关于我们", "联系我们", "登录", "注册"}
    if t in nav_tokens or _norm_title_token(t) in {_norm_title_token(x) for x in SECTION_ONLY_TITLES}:
        return True
    return False


def valid_news_item(
    title: str,
    summary: str = "",
    source: str = "",
    url: str = "",
    symbol: str = "",
    name: str = "",
    source_type: str = "news",
    base_relevant: bool = False,
    allow_macro: bool = False,
) -> tuple[bool, str]:
    """Validate if a row is a real news/announcement/structured information item.

    Invalid page headers, footers, JS/CSS snippets, search result pages and table/comment fragments
    are rejected before they can enter storage, detail pages, or scoring.
    """
    raw_title = str(title or "").strip()
    raw_summary = str(summary or "").strip()
    if is_search_engine_url(url):
        return False, "search_engine_page"
    if is_boilerplate_title(raw_title):
        return False, "boilerplate_or_invalid_title"
    if not any(x in str(source or "") for x in SOURCE_REAL_TERMS) and not url:
        return False, "unknown_source"

    cleaned_title = strip_html_boilerplate(raw_title, max_len=200)
    cleaned_summary = strip_html_boilerplate(raw_summary, max_len=1200)
    body = f"{cleaned_title} {cleaned_summary}".strip()
    if is_menu_or_table_fragment(raw_title, raw_summary):
        return False, "menu_or_table_fragment"
    if HTML_JS_RE.search(raw_title):
        return False, "html_js_fragment"
    if len(raw_summary) > 20 and HTML_JS_RE.search(raw_summary) and (chinese_ratio(raw_summary) < 0.55 or is_menu_or_table_fragment(raw_title, raw_summary)):
        return False, "html_js_fragment"
    if chinese_count(body) < 6:
        return False, "too_few_chinese_chars"
    if len(cleaned_summary) >= 40 and chinese_ratio(cleaned_summary) < 0.32:
        return False, "low_chinese_ratio"

    st = (source_type or "news").lower()
    if allow_macro or st in {"macro", "policy", "global", "market"}:
        if any(term in body for term in RELATION_TERMS):
            return True, "ok_macro"
        return False, "macro_without_finance_terms"

    if base_relevant:
        return True, "ok_base_relevant"
    rel_symbols = {str(symbol or "").strip(), str(symbol or "").strip()[-6:]}
    rel_symbols = {x for x in rel_symbols if x}
    if (name and str(name).strip() in body) or any(x and x in body for x in rel_symbols) or any(term in body for term in RELATION_TERMS):
        return True, "ok_related"
    if st in {"announcement", "forum"} and (name or symbol):
        return False, "company_source_unrelated"
    return False, "unrelated_to_target_or_finance"


def _mk_dt(y: str, m: str, d: str, h: str | None = None, mi: str | None = None, s: str | None = None) -> datetime | None:
    try:
        return datetime(int(y), int(m), int(d), int(h or 0), int(mi or 0), int(s or 0))
    except Exception:
        return None


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # accept seconds or milliseconds epoch
        v = float(value)
        if v > 10_000_000_000:
            v = v / 1000.0
        try:
            return datetime.fromtimestamp(v)
        except Exception:
            return None
    s = str(value).strip()
    if not s:
        return None
    # avoid copyright years / template years without month/day
    for pat in DATE_PATTERNS:
        m = pat.search(s)
        if m:
            return _mk_dt(m.group("y"), m.group("m"), m.group("d"), m.groupdict().get("h"), m.groupdict().get("mi"), m.groupdict().get("s"))
    try:
        return datetime.fromisoformat(s[:19].replace("/", "-"))
    except Exception:
        return None


def extract_url_date(url: str) -> datetime | None:
    m = URL_DATE_RE.search(url or "")
    if not m:
        return None
    return _mk_dt(m.group(1), m.group(2), m.group(3))


def extract_event_time(title: str, summary: str = "") -> datetime | None:
    text = f"{title or ''} {summary or ''}"
    m = EVENT_DATE_HINT_RE.search(text)
    if m:
        return parse_datetime(m.group(1))
    # shareholder-meeting and disclosure titles often contain a single date without explicit prefix.
    if any(k in text for k in ("股东大会", "会议", "解禁", "除权除息", "登记日", "生效")):
        for pat in DATE_PATTERNS:
            mm = pat.search(text)
            if mm:
                return _mk_dt(mm.group("y"), mm.group("m"), mm.group("d"), mm.groupdict().get("h"), mm.groupdict().get("mi"), mm.groupdict().get("s"))
    return None


def extract_period(text: str) -> str:
    t = SPACE_RE.sub("", text or "")
    # Prefer explicit report/meeting periods over ordinary event dates.
    patterns = [
        r"(20\d{2})年?年度",
        r"(20\d{2})年?(?:一季报|第一季度|半年度|半年报|三季报|第三季度|年报)",
        r"(20\d{2})Q[1-4]",
    ]
    for pat in patterns:
        m = re.search(pat, t, flags=re.I)
        if m:
            if "年度" in m.group(0):
                return f"{m.group(1)}年度"
            return m.group(0)
    return ""


def infer_event_type(title: str, summary: str = "", source_type: str = "") -> str:
    text = f"{title or ''} {summary or ''}"
    for event_type, terms in EVENT_TYPE_RULES:
        if any(t in text for t in terms):
            return event_type
    st = (source_type or "").lower()
    if st == "announcement":
        return "announcement"
    if st in {"macro", "policy", "global"}:
        return "market_macro"
    if st == "forum":
        return "sentiment_forum"
    return "general_news"


def document_id_from_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    # Prefer explicit PDF/report ids in query/path, else stable URL hash.
    m = re.search(r"(?:announcementId|art_code|notice_id|pdfFileId|pdffileid|id|code)=([A-Za-z0-9_\-]+)", u, re.I)
    if m:
        return m.group(1)[:80]
    if re.search(r"\.(?:pdf|html?)(?:$|[?#])", u, re.I):
        return hashlib.sha1(u.encode("utf-8", "ignore")).hexdigest()[:16]
    return ""


def _fmt_dt(dt: datetime | None, date_only: bool = False) -> str | None:
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d" if date_only or (dt.hour == 0 and dt.minute == 0 and dt.second == 0) else "%Y-%m-%d %H:%M:%S")


def extract_time_fields(published_at: Any, title: str = "", summary: str = "", url: str = "", source_type: str = "") -> dict[str, str | None]:
    now = datetime.now().isoformat(timespec="seconds")
    publish_dt = parse_datetime(published_at)
    confidence = "L1" if publish_dt else ""
    basis = "structured_field" if publish_dt else ""
    if not publish_dt:
        url_dt = extract_url_date(url)
        if url_dt:
            publish_dt = url_dt
            confidence = "L3"
            basis = "url_date"
    if not publish_dt:
        # title/header dates are usable as publish only if not an event-date phrase.
        body_dt = parse_datetime(f"{title} {summary[:120]}")
        if body_dt and not extract_event_time(title, summary):
            publish_dt = body_dt
            confidence = "L4"
            basis = "body_date"
    event_dt = extract_event_time(title, summary)
    text = f"{title or ''} {summary or ''}"
    return {
        "publish_time": _fmt_dt(publish_dt),
        "event_time": _fmt_dt(event_dt, date_only=True),
        "crawl_time": now,
        "time_confidence": confidence or "L5",
        "time_basis": basis or "crawl_time_fallback",
        "period": extract_period(text),
        "event_type": infer_event_type(title, summary, source_type=source_type),
        "document_id": document_id_from_url(url),
    }
