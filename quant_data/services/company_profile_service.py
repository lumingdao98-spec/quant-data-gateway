from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from quant_data.utils import normalize_symbol, infer_exchange, safe_float


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _clean(value: Any, limit: int | None = None) -> str:
    if value is None:
        return ""
    s = str(value).replace("\xa0", " ").replace("\u3000", " ").strip()
    s = " ".join(s.split())
    if limit and len(s) > limit:
        return s[:limit].rstrip() + "..."
    return s


def _records(df: Any) -> list[dict[str, Any]]:
    if df is None:
        return []
    if isinstance(df, list):
        return [x for x in df if isinstance(x, dict)]
    if isinstance(df, dict):
        return [df]
    if hasattr(df, "to_dict"):
        try:
            rows = df.to_dict(orient="records")
            return [x for x in rows if isinstance(x, dict)]
        except Exception:
            return []
    return []


def _json_default(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return ""


def _kv_records(df: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for r in _records(df):
        k = (
            r.get("item") or r.get("ITEM") or r.get("指标") or r.get("项目")
            or r.get("name") or r.get("名称") or r.get("字段")
        )
        v = r.get("value") or r.get("VALUE") or r.get("值") or r.get("内容") or r.get("数据")
        if k is not None:
            out[_clean(k)] = v
    return out


def _format_cny(value: Any) -> str:
    v = safe_float(value, 0.0)
    if not v:
        return _clean(value)
    if abs(v) >= 1e12:
        return f"{v / 1e12:.2f}万亿"
    if abs(v) >= 1e8:
        return f"{v / 1e8:.2f}亿"
    if abs(v) >= 1e4:
        return f"{v / 1e4:.2f}万"
    return f"{v:.0f}元"


def _first(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in row and row.get(k) not in (None, ""):
            return row.get(k)
    # 模糊匹配：akshare 不同版本字段名会变化。
    for want in keys:
        for k, v in row.items():
            if want and want in str(k) and v not in (None, ""):
                return v
    return ""


def _pick_columns(row: dict[str, Any], candidates: list[str]) -> str:
    return _clean(_first(row, candidates), 80)


class CompanyProfileService:
    """公司画像聚合与本地持久化。

    目标不是依赖单一网页，而是把巨潮、东方财富、akshare 可用的高管/财务接口
    整理成稳定结构，写入本地 SQLite。公开源临时失败时仍可返回上次成功结果。
    """

    def __init__(self, ttl_seconds: int = 7 * 86400, db_path: str | Path | None = None) -> None:
        self.ttl_seconds = ttl_seconds
        self.db_path = Path(db_path) if db_path else DATA_DIR / "company_profile.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_profiles (
                    symbol TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    saved_at REAL NOT NULL,
                    first_seen_at REAL NOT NULL,
                    last_seen_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_profile_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_date TEXT,
                    title TEXT NOT NULL,
                    payload_json TEXT,
                    saved_at REAL NOT NULL,
                    UNIQUE(symbol, event_type, event_date, title)
                )
                """
            )
            conn.commit()

    def _read_store(self, code: str, allow_stale: bool = False) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT result_json, saved_at, first_seen_at, last_seen_at FROM company_profiles WHERE symbol=?",
                (code,),
            ).fetchone()
        if not row:
            return None
        saved_at = float(row[1] or 0)
        if not allow_stale and time.time() - saved_at > self.ttl_seconds:
            return None
        try:
            data = json.loads(row[0])
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        data.setdefault("cache_info", {})
        data["cache_info"].update({
            "hit": True,
            "store": "sqlite",
            "ttl_seconds": self.ttl_seconds,
            "age_seconds": round(time.time() - saved_at, 1),
            "saved_at": datetime.fromtimestamp(saved_at).isoformat(timespec="seconds"),
            "stale": time.time() - saved_at > self.ttl_seconds,
        })
        return data

    def _write_store(self, code: str, data: dict[str, Any]) -> None:
        now = time.time()
        payload = json.dumps(data, ensure_ascii=False, default=_json_default)
        with sqlite3.connect(self.db_path) as conn:
            old = conn.execute("SELECT first_seen_at FROM company_profiles WHERE symbol=?", (code,)).fetchone()
            first = float(old[0]) if old else now
            conn.execute(
                """
                INSERT INTO company_profiles(symbol,result_json,saved_at,first_seen_at,last_seen_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(symbol) DO UPDATE SET
                    result_json=excluded.result_json,
                    saved_at=excluded.saved_at,
                    last_seen_at=excluded.last_seen_at
                """,
                (code, payload, now, first, now),
            )
            for ev in (data.get("personnel_changes") or [])[:30]:
                title = _clean(ev.get("title") or ev.get("name") or ev.get("summary"), 180)
                if not title:
                    continue
                conn.execute(
                    """
                    INSERT OR IGNORE INTO company_profile_events
                    (symbol,event_type,event_date,title,payload_json,saved_at)
                    VALUES(?,?,?,?,?,?)
                    """,
                    (
                        code,
                        "personnel_change",
                        _clean(ev.get("date") or ev.get("report_date"), 30),
                        title,
                        json.dumps(ev, ensure_ascii=False, default=_json_default),
                        now,
                    ),
                )
            conn.commit()

    def stats(self, symbol: str | None = None) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            if symbol:
                code = normalize_symbol(symbol)
                row = conn.execute(
                    "SELECT saved_at, first_seen_at, last_seen_at FROM company_profiles WHERE symbol=?",
                    (code,),
                ).fetchone()
                events = conn.execute(
                    "SELECT COUNT(*) FROM company_profile_events WHERE symbol=?",
                    (code,),
                ).fetchone()[0]
                return {
                    "symbol": code,
                    "exists": bool(row),
                    "events": events,
                    "saved_at": datetime.fromtimestamp(row[0]).isoformat(timespec="seconds") if row else "",
                    "db_path": str(self.db_path),
                }
            total = conn.execute("SELECT COUNT(*) FROM company_profiles").fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM company_profile_events").fetchone()[0]
        return {"profiles": total, "events": events, "db_path": str(self.db_path)}

    def _empty_profile(self, code: str) -> dict[str, Any]:
        return {
            "code": code,
            "exchange": infer_exchange(code),
            "name": "",
            "company_name": "",
            "profile_type": "ETF" if code.startswith(("15", "51", "56", "58")) else "STOCK",
            "fund_manager": "",
            "tracking_index": "",
            "fund_company": "",
            "industry": "",
            "market": "",
            "listed_date": "",
            "website": "",
            "main_business": "",
            "business_scope": "",
            "business_tags": [],
            "main_products": [],
            "upstream": [],
            "downstream": [],
            "business_segments": [],
            "industry_exposure_text": "",
            "org_intro": "",
            "summary": "",
            "total_market_value": "",
            "float_market_value": "",
            "executives": [],
            "personnel_changes": [],
            "financial_history": [],
            "financial_summary": {},
            "sources": [],
            "source_status": [],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "cache_info": {"hit": False, "store": "sqlite", "ttl_seconds": self.ttl_seconds},
        }

    def get_profile(self, symbol: str, force: bool = False) -> dict[str, Any]:
        code = normalize_symbol(symbol)
        if not code:
            code = str(symbol or "").strip()
        if not force:
            cached = self._cache.get(code)
            if cached and time.time() - cached[0] <= self.ttl_seconds:
                data = json.loads(json.dumps(cached[1], ensure_ascii=False, default=_json_default))
                data.setdefault("cache_info", {})
                data["cache_info"].update({"hit": True, "store": "memory", "ttl_seconds": self.ttl_seconds})
                return data
            stored = self._read_store(code, allow_stale=False)
            if stored:
                self._cache[code] = (time.time(), stored)
                return stored

        profile = self._empty_profile(code)
        try:
            import akshare as ak  # type: ignore
        except Exception as exc:
            stale = self._read_store(code, allow_stale=True)
            if stale:
                stale.setdefault("source_status", []).append({"source": "akshare", "status": f"当前不可用，返回历史画像：{exc}"[:160]})
                stale.setdefault("cache_info", {})["stale_fallback"] = True
                return stale
            profile["source_status"].append({"source": "akshare", "status": f"不可用：{exc}"[:160]})
            self._enrich_business_profile(profile)
            self._finalize_summary(profile)
            return profile

        if profile.get("profile_type") == "ETF":
            self._fetch_etf_profile(ak, profile)
        self._fetch_base_cninfo(ak, profile)
        self._fetch_base_em(ak, profile)
        self._fetch_executives(ak, profile)
        self._fetch_personnel_changes(ak, profile)
        self._fetch_financial_history(ak, profile)
        self._enrich_business_profile(profile)
        self._finalize_summary(profile)

        # 如果本次接口全部失败，回退历史画像，但保留本次诊断。
        if not profile.get("summary") or (not profile.get("sources") and not profile.get("financial_history")):
            stale = self._read_store(code, allow_stale=True)
            if stale:
                stale.setdefault("source_status", []).extend(profile.get("source_status", []))
                stale.setdefault("cache_info", {})["stale_fallback"] = True
                return stale

        profile["sources"] = sorted(set(profile.get("sources") or []))
        self._write_store(code, profile)
        self._cache[code] = (time.time(), profile)
        return profile

    def _mark(self, profile: dict[str, Any], source: str, status: str, count: int | None = None) -> None:
        row = {"source": source, "status": status[:160]}
        if count is not None:
            row["count"] = count
        profile.setdefault("source_status", []).append(row)

    def _fetch_etf_profile(self, ak: Any, profile: dict[str, Any]) -> None:
        """ETF 没有公司简介，改为基金/跟踪指数/管理人画像。"""
        code = profile["code"]
        candidates = [
            ("fund_etf_spot_em", {}),
            ("fund_name_em", {}),
            ("fund_individual_basic_info_xq", {"symbol": code}),
        ]
        found = False
        for fn_name, kwargs in candidates:
            if not hasattr(ak, fn_name):
                continue
            try:
                rows = _records(getattr(ak, fn_name)(**kwargs))
                for r in rows[:5000]:
                    raw = " ".join(str(v) for v in r.values())
                    if code not in raw:
                        continue
                    profile["name"] = profile.get("name") or _pick_columns(r, ["基金简称", "名称", "基金名称", "name"])
                    profile["company_name"] = profile.get("company_name") or profile.get("name")
                    profile["fund_company"] = profile.get("fund_company") or _pick_columns(r, ["基金公司", "管理人", "基金管理人", "company"])
                    profile["fund_manager"] = profile.get("fund_manager") or _pick_columns(r, ["基金经理", "经理", "manager"])
                    profile["tracking_index"] = profile.get("tracking_index") or _pick_columns(r, ["跟踪指数", "标的指数", "指数名称", "index"])
                    found = True
                    break
                if found:
                    profile.setdefault("sources", []).append("ETF资料")
                    self._mark(profile, f"ETF资料:{fn_name}", "ok", 1)
                    break
                self._mark(profile, f"ETF资料:{fn_name}", "未匹配该代码", len(rows))
            except Exception as exc:
                self._mark(profile, f"ETF资料:{fn_name}", str(exc))
        if not profile.get("name"):
            profile["name"] = code
        if not profile.get("industry"):
            profile["industry"] = "ETF/场内基金"
        if not profile.get("main_business"):
            bits = ["场内交易型基金"]
            if profile.get("tracking_index"):
                bits.append(f"跟踪指数：{profile['tracking_index']}")
            if profile.get("fund_company"):
                bits.append(f"基金管理人：{profile['fund_company']}")
            profile["main_business"] = "；".join(bits)

    def _fetch_base_cninfo(self, ak: Any, profile: dict[str, Any]) -> None:
        code = profile["code"]
        if not hasattr(ak, "stock_profile_cninfo"):
            self._mark(profile, "巨潮资讯公司概况", "akshare 当前版本无此接口")
            return
        try:
            rows = _records(ak.stock_profile_cninfo(symbol=code))
            if not rows:
                self._mark(profile, "巨潮资讯公司概况", "无数据", 0)
                return
            r = rows[0]
            profile.update({
                "name": _clean(_first(r, ["A股简称", "证券简称", "简称"]) or profile.get("name")),
                "company_name": _clean(_first(r, ["公司名称", "机构名称", "中文名称"]) or profile.get("company_name")),
                "industry": _clean(_first(r, ["所属行业", "行业"]) or profile.get("industry")),
                "market": _clean(_first(r, ["所属市场", "上市板块", "市场"]) or profile.get("market")),
                "listed_date": _clean(_first(r, ["上市日期", "A股上市日期"]) or profile.get("listed_date")),
                "website": _clean(_first(r, ["官方网站", "公司网址", "网址"]) or profile.get("website")),
                "main_business": _clean(_first(r, ["主营业务", "主营范围"]), 520) or profile.get("main_business"),
                "business_scope": _clean(_first(r, ["经营范围"]), 800) or profile.get("business_scope"),
                "org_intro": _clean(_first(r, ["机构简介", "公司简介", "简介"]), 900) or profile.get("org_intro"),
            })
            profile.setdefault("sources", []).append("巨潮资讯")
            self._mark(profile, "巨潮资讯公司概况", "ok", len(rows))
        except Exception as exc:
            self._mark(profile, "巨潮资讯公司概况", str(exc))

    def _fetch_base_em(self, ak: Any, profile: dict[str, Any]) -> None:
        code = profile["code"]
        if not hasattr(ak, "stock_individual_info_em"):
            self._mark(profile, "东方财富个股信息", "akshare 当前版本无此接口")
            return
        try:
            kv = _kv_records(ak.stock_individual_info_em(symbol=code))
            if not kv:
                self._mark(profile, "东方财富个股信息", "无数据", 0)
                return
            profile["name"] = profile.get("name") or _clean(kv.get("股票简称") or kv.get("简称"))
            profile["industry"] = profile.get("industry") or _clean(kv.get("行业"))
            profile["listed_date"] = profile.get("listed_date") or _clean(kv.get("上市时间") or kv.get("上市日期"))
            if kv.get("总市值") is not None:
                profile["total_market_value"] = _format_cny(kv.get("总市值"))
            if kv.get("流通市值") is not None:
                profile["float_market_value"] = _format_cny(kv.get("流通市值"))
            profile.setdefault("sources", []).append("东方财富")
            self._mark(profile, "东方财富个股信息", "ok", len(kv))
        except Exception as exc:
            self._mark(profile, "东方财富个股信息", str(exc))

    def _fetch_executives(self, ak: Any, profile: dict[str, Any]) -> None:
        code = profile["code"]
        candidates = [
            ("stock_management_info_ths", {"symbol": code}),
            ("stock_manager_info", {"symbol": code}),
            ("stock_zygc_ym", {"symbol": code}),
            ("stock_hold_management_detail_cninfo", {"symbol": code}),
        ]
        for fn_name, kwargs in candidates:
            if not hasattr(ak, fn_name):
                continue
            try:
                rows = _records(getattr(ak, fn_name)(**kwargs))
                executives: list[dict[str, str]] = []
                for r in rows[:30]:
                    name = _pick_columns(r, ["姓名", "高管姓名", "人员姓名", "name"])
                    title = _pick_columns(r, ["职务", "职位", "任职", "title"])
                    if not name and not title:
                        continue
                    executives.append({
                        "name": name or title,
                        "title": title,
                        "start_date": _pick_columns(r, ["任职日期", "起始日期", "开始日期", "公告日期"]),
                        "gender": _pick_columns(r, ["性别"]),
                    })
                if executives:
                    profile["executives"] = executives[:12]
                    profile.setdefault("sources", []).append("高管资料")
                    self._mark(profile, f"高管资料:{fn_name}", "ok", len(executives))
                    return
                self._mark(profile, f"高管资料:{fn_name}", "无有效字段", 0)
            except Exception as exc:
                self._mark(profile, f"高管资料:{fn_name}", str(exc))

    def _fetch_personnel_changes(self, ak: Any, profile: dict[str, Any]) -> None:
        code = profile["code"]
        candidates = [
            ("stock_hold_management_detail_cninfo", {"symbol": code}),
            ("stock_management_info_ths", {"symbol": code}),
            ("stock_manager_info", {"symbol": code}),
        ]
        seen: set[str] = set()
        changes: list[dict[str, str]] = []
        for fn_name, kwargs in candidates:
            if not hasattr(ak, fn_name):
                continue
            try:
                rows = _records(getattr(ak, fn_name)(**kwargs))
                for r in rows[:80]:
                    name = _pick_columns(r, ["姓名", "高管姓名", "人员姓名", "变动人", "name"])
                    title = _pick_columns(r, ["职务", "职位", "变动类型", "类型", "title"])
                    date = _pick_columns(r, ["公告日期", "变动日期", "日期", "任职日期"])
                    summary = _clean(_first(r, ["变动原因", "原因", "说明", "内容"]), 160)
                    if not (name or title or summary):
                        continue
                    key = f"{date}|{name}|{title}|{summary}"
                    if key in seen:
                        continue
                    seen.add(key)
                    changes.append({
                        "date": date,
                        "name": name,
                        "title": title,
                        "summary": summary or f"{name} {title}".strip(),
                    })
                if rows:
                    self._mark(profile, f"人员变动:{fn_name}", "ok", len(rows))
            except Exception as exc:
                self._mark(profile, f"人员变动:{fn_name}", str(exc))
        if changes:
            # 日期降序粗排，空日期放后。
            changes.sort(key=lambda x: x.get("date") or "", reverse=True)
            profile["personnel_changes"] = changes[:12]
            profile.setdefault("sources", []).append("人员变动")

    def _fetch_financial_history(self, ak: Any, profile: dict[str, Any]) -> None:
        code = profile["code"]
        candidates = [
            ("stock_financial_analysis_indicator", {"symbol": code}),
            ("stock_financial_abstract", {"symbol": code}),
            ("stock_financial_report_sina", {"stock": code, "symbol": "利润表"}),
        ]
        for fn_name, kwargs in candidates:
            if not hasattr(ak, fn_name):
                continue
            try:
                rows = _records(getattr(ak, fn_name)(**kwargs))
                if not rows:
                    self._mark(profile, f"历史业绩:{fn_name}", "无数据", 0)
                    continue
                history: list[dict[str, str]] = []
                for r in rows[:12]:
                    item = {
                        "report_date": _pick_columns(r, ["日期", "报告期", "报告日期", "截止日期"]),
                        "revenue": _pick_columns(r, ["营业总收入", "营业收入", "主营业务收入", "营收"]),
                        "net_profit": _pick_columns(r, ["归属净利润", "归母净利润", "净利润", "扣非净利润"]),
                        "roe": _pick_columns(r, ["净资产收益率", "ROE", "加权净资产收益率"]),
                        "gross_margin": _pick_columns(r, ["销售毛利率", "毛利率"]),
                        "debt_ratio": _pick_columns(r, ["资产负债率", "负债率"]),
                        "eps": _pick_columns(r, ["每股收益", "基本每股收益", "EPS"]),
                    }
                    if any(item.values()):
                        history.append(item)
                if history:
                    profile["financial_history"] = history[:8]
                    profile["financial_summary"] = self._financial_summary(history)
                    profile.setdefault("sources", []).append("历史业绩")
                    self._mark(profile, f"历史业绩:{fn_name}", "ok", len(history))
                    return
                self._mark(profile, f"历史业绩:{fn_name}", "无有效字段", len(rows))
            except TypeError:
                # 不同 akshare 版本函数签名不同，继续尝试下一个。
                self._mark(profile, f"历史业绩:{fn_name}", "接口参数不兼容")
            except Exception as exc:
                self._mark(profile, f"历史业绩:{fn_name}", str(exc))

    def _financial_summary(self, history: list[dict[str, str]]) -> dict[str, Any]:
        latest = history[0] if history else {}
        prev = history[1] if len(history) > 1 else {}
        return {
            "latest_report_date": latest.get("report_date", ""),
            "latest_revenue": latest.get("revenue", ""),
            "latest_net_profit": latest.get("net_profit", ""),
            "latest_roe": latest.get("roe", ""),
            "previous_report_date": prev.get("report_date", ""),
            "records": len(history),
        }


    def _known_business_map(self) -> dict[str, dict[str, Any]]:
        """常见 A 股公司主营/产业链画像兜底。

        公开接口失败时，至少保留“主营业务—上游—下游—产品—行业暴露”这些用于全球要闻映射的关键词。
        后续可把这里迁移为 data/company_business_map.json。
        """
        return {
            "688599": {"name": "天合光能", "industry": "光伏设备/新能源", "tags": ["光伏", "新能源", "组件", "电池片", "储能", "分布式电站"], "products": ["光伏组件", "太阳能电池片", "光伏系统", "储能系统", "智慧能源解决方案"], "upstream": ["硅料", "硅片", "银浆", "玻璃", "EVA胶膜"], "downstream": ["集中式电站", "分布式光伏", "工商业储能", "海外光伏需求"], "segments": ["光伏组件制造", "电池片研发制造", "储能及智慧能源", "光伏电站系统解决方案"]},
            "300750": {"name": "宁德时代", "industry": "动力电池/储能", "tags": ["动力电池", "锂电", "储能", "新能源车", "固态电池"], "products": ["动力电池系统", "储能电池系统", "电池材料", "电池回收"], "upstream": ["锂", "镍", "钴", "隔膜", "电解液", "正负极材料"], "downstream": ["新能源汽车", "储能电站", "海外车企"], "segments": ["动力电池", "储能电池", "电池材料及回收"]},
            "600438": {"name": "通威股份", "industry": "光伏硅料/电池片/农牧", "tags": ["光伏", "硅料", "多晶硅", "电池片", "新能源", "农牧饲料"], "products": ["高纯晶硅", "太阳能电池", "光伏组件", "水产饲料"], "upstream": ["工业硅", "电力", "硅片"], "downstream": ["光伏组件", "新能源电站", "水产养殖"], "segments": ["高纯晶硅", "太阳能电池", "组件", "农牧饲料"]},
            "601012": {"name": "隆基绿能", "industry": "光伏硅片/组件", "tags": ["光伏", "硅片", "组件", "电池片", "BC电池", "新能源"], "products": ["单晶硅片", "光伏组件", "太阳能电池", "分布式解决方案"], "upstream": ["硅料", "石英坩埚", "电力"], "downstream": ["光伏电站", "分布式光伏", "海外装机"], "segments": ["硅片", "电池组件", "光伏系统"]},
            "002594": {"name": "比亚迪", "industry": "新能源汽车/动力电池", "tags": ["新能源汽车", "动力电池", "储能", "汽车电子", "半导体"], "products": ["新能源汽车", "动力电池", "储能系统", "电子代工", "汽车半导体"], "upstream": ["锂电材料", "汽车零部件", "芯片"], "downstream": ["乘用车", "商用车", "海外汽车市场", "储能客户"], "segments": ["汽车", "手机部件及组装", "二次充电电池及光伏"]},
            "600519": {"name": "贵州茅台", "industry": "白酒/食品饮料", "tags": ["白酒", "高端消费", "食品饮料", "消费升级"], "products": ["茅台酒", "系列酒"], "upstream": ["高粱", "小麦", "包装材料"], "downstream": ["经销商", "直销渠道", "宴请/礼赠消费"], "segments": ["高端白酒", "系列酒"]},
            "000858": {"name": "五粮液", "industry": "白酒/食品饮料", "tags": ["白酒", "高端消费", "食品饮料"], "products": ["五粮液酒", "系列酒"], "upstream": ["粮食", "包装材料"], "downstream": ["经销商", "团购", "宴请消费"], "segments": ["高端白酒", "系列酒"]},
            "300059": {"name": "东方财富", "industry": "互联网券商/金融信息服务", "tags": ["券商", "金融科技", "基金销售", "互联网金融", "证券信息服务"], "products": ["证券经纪", "基金销售", "金融数据终端", "财富管理"], "upstream": ["行情数据", "交易所服务", "金融牌照"], "downstream": ["个人投资者", "机构客户", "基金公司"], "segments": ["证券服务", "金融电子商务服务", "金融数据服务"]},
        }

    def _infer_business_from_text(self, profile: dict[str, Any]) -> dict[str, list[str]]:
        text = " ".join(str(profile.get(k) or "") for k in ["name", "company_name", "industry", "main_business", "business_scope", "org_intro"])
        rules = {
            "光伏": ["光伏", "硅料", "多晶硅", "硅片", "组件", "太阳能", "电池片"],
            "动力电池": ["动力电池", "锂电", "储能电池", "新能源车", "固态电池"],
            "半导体": ["半导体", "芯片", "集成电路", "封测", "光刻"],
            "人工智能": ["人工智能", "AI", "算力", "数据中心", "服务器"],
            "军工航空": ["军工", "航空", "航天", "国防", "无人机", "低空"],
            "医药医疗": ["医药", "创新药", "医疗器械", "疫苗", "CXO"],
            "白酒消费": ["白酒", "食品", "饮料", "消费"],
            "资源能源": ["煤炭", "原油", "天然气", "黄金", "有色", "铜", "铝", "锂"],
            "金融地产": ["银行", "证券", "保险", "地产", "房地产", "家居", "建材"],
        }
        tags = [k for k, words in rules.items() if any(w in text for w in words)]
        products = []
        for k in tags:
            products.extend(rules.get(k, [])[:5])
        return {"tags": tags, "products": list(dict.fromkeys(products))[:12]}

    def _enrich_business_profile(self, profile: dict[str, Any]) -> None:
        code = str(profile.get("code") or "")
        known = self._known_business_map().get(code, {})
        if known:
            profile["name"] = profile.get("name") or known.get("name", "")
            profile["industry"] = profile.get("industry") or known.get("industry", "")
            profile["main_business"] = profile.get("main_business") or "；".join(known.get("segments", []))
            profile["business_tags"] = list(dict.fromkeys((profile.get("business_tags") or []) + known.get("tags", [])))
            profile["main_products"] = list(dict.fromkeys((profile.get("main_products") or []) + known.get("products", [])))
            profile["upstream"] = list(dict.fromkeys((profile.get("upstream") or []) + known.get("upstream", [])))
            profile["downstream"] = list(dict.fromkeys((profile.get("downstream") or []) + known.get("downstream", [])))
            profile["business_segments"] = list(dict.fromkeys((profile.get("business_segments") or []) + known.get("segments", [])))
            profile.setdefault("sources", []).append("内置主营业务画像")
            self._mark(profile, "内置主营业务画像", "ok", 1)
        inferred = self._infer_business_from_text(profile)
        profile["business_tags"] = list(dict.fromkeys((profile.get("business_tags") or []) + inferred.get("tags", [])))[:16]
        profile["main_products"] = list(dict.fromkeys((profile.get("main_products") or []) + inferred.get("products", [])))[:20]
        exposure_parts = []
        for k in ["name", "company_name", "industry", "main_business", "business_scope"]:
            if profile.get(k):
                exposure_parts.append(str(profile.get(k)))
        for key in ["business_tags", "main_products", "upstream", "downstream", "business_segments"]:
            exposure_parts.extend([str(x) for x in (profile.get(key) or [])])
        profile["industry_exposure_text"] = _clean(" ".join(exposure_parts), 1400)

    def _finalize_summary(self, profile: dict[str, Any]) -> None:
        parts: list[str] = []
        display_name = profile.get("company_name") or profile.get("name") or profile.get("code")
        parts.append(f"{display_name}（{profile.get('code')}）")
        if profile.get("industry"):
            parts.append(f"所属行业/类型：{profile['industry']}")
        if profile.get("listed_date"):
            parts.append(f"上市日期：{profile['listed_date']}")
        if profile.get("profile_type") == "ETF":
            if profile.get("tracking_index"):
                parts.append(f"跟踪指数：{profile['tracking_index']}")
            if profile.get("fund_company"):
                parts.append(f"基金管理人：{profile['fund_company']}")
            if profile.get("fund_manager"):
                parts.append(f"基金经理：{profile['fund_manager']}")
        if profile.get("main_business"):
            parts.append(f"主营业务：{_clean(profile['main_business'], 300)}")
        elif profile.get("business_scope"):
            parts.append(f"经营范围：{_clean(profile['business_scope'], 300)}")
        if profile.get("business_tags"):
            parts.append("业务标签：" + "、".join(profile.get("business_tags", [])[:8]))
        if profile.get("main_products"):
            parts.append("主要产品/服务：" + "、".join(profile.get("main_products", [])[:8]))
        if profile.get("upstream") or profile.get("downstream"):
            up = "、".join(profile.get("upstream", [])[:5]) or "--"
            down = "、".join(profile.get("downstream", [])[:5]) or "--"
            parts.append(f"产业链：上游 {up}；下游 {down}")
        elif profile.get("org_intro"):
            parts.append(_clean(profile["org_intro"], 260))
        fin = profile.get("financial_summary") or {}
        if fin.get("latest_report_date"):
            parts.append(
                f"最新业绩期：{fin.get('latest_report_date')}，营收{fin.get('latest_revenue') or '--'}，净利润{fin.get('latest_net_profit') or '--'}"
            )
        if profile.get("executives"):
            names = "、".join([x.get("name", "") for x in profile["executives"][:3] if x.get("name")])
            if names:
                parts.append(f"管理层：{names}")
        profile["summary"] = "；".join([p for p in parts if p]).strip("；") or f"{profile.get('code')} 暂无可用公司简介。"
