from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from html.parser import HTMLParser
from math import isfinite
from typing import Any, Iterable

from quant_data.models import IntradayPoint
from quant_data.providers.eastmoney import EastmoneyProvider
from quant_data.utils import ThrottledSession, normalize_symbol, to_eastmoney_secid


def _number(value: Any) -> float | None:
    if value in (None, "", "--", "-", "null"):
        return None
    raw = str(value).strip().replace(",", "").replace("％", "%")
    multiplier = 1.0
    if "万亿" in raw:
        multiplier = 1e12
    elif "亿" in raw:
        multiplier = 1e8
    elif "万" in raw:
        multiplier = 1e4
    match = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
    if not match:
        return None
    try:
        result = float(match.group(0)) * multiplier
    except ValueError:
        return None
    return result if isfinite(result) else None


def _iso_date(value: Any) -> str:
    raw = re.sub(r"[^0-9]", "", str(value or ""))
    if len(raw) < 8:
        return ""
    try:
        return datetime.strptime(raw[:8], "%Y%m%d").date().isoformat()
    except ValueError:
        return ""


class _HtmlRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None
            self._cell = None


class IndividualCapitalEvidenceService:
    """Traceable stock-level capital evidence without Level-2 overclaiming."""

    FUND_FLOW_URL = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    HOLDER_URL = "https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_FundStockHolder/stockid/{symbol}.phtml"

    def __init__(self, cache_state: Any, provider: EastmoneyProvider | None = None) -> None:
        self.cache_state = cache_state
        self.provider = provider or EastmoneyProvider()
        self.http = ThrottledSession()
        self.http.session.trust_env = False
        self._last_intraday_write: dict[str, float] = {}

    def snapshot(
        self,
        symbol: str,
        *,
        quote: dict[str, Any] | None = None,
        intraday: Iterable[IntradayPoint] | None = None,
        force: bool = False,
        allow_network: bool = True,
    ) -> dict[str, Any]:
        symbol = normalize_symbol(symbol)
        quote = dict(quote or {})
        points = list(intraday or [])
        public_daily = self._public_daily(symbol, force=force, allow_network=allow_network)
        holdings = self._institutional_holdings(symbol, force=force, allow_network=allow_network)
        intraday_proxy = self._intraday_proxy(points, quote)
        if intraday_proxy.get("available"):
            self._persist_intraday(symbol, intraday_proxy)

        score_result = self._score(public_daily, intraday_proxy)
        missing = list(public_daily.get("missing_reasons") or [])
        missing.extend(intraday_proxy.get("missing_reasons") or [])
        if not holdings.get("available"):
            missing.extend(holdings.get("missing_reasons") or [])
        missing = list(dict.fromkeys(str(row) for row in missing if str(row or "").strip()))
        return {
            "symbol": symbol,
            "score": score_result.get("score"),
            "quality_status": score_result.get("quality_status"),
            "source": score_result.get("source"),
            "source_ref": self.FUND_FLOW_URL,
            "available_at": score_result.get("available_at"),
            "stale": bool(score_result.get("stale")),
            "confidence": score_result.get("confidence"),
            "evidence_fields": score_result.get("evidence_fields", []),
            "contributions": score_result.get("contributions", []),
            "public_daily_flow": public_daily,
            "intraday_proxy": intraday_proxy,
            "institutional_holdings": holdings,
            "missing_reasons": missing,
            "truth_boundary": (
                "东方财富公开资金字段用于相对强弱；分时净流为价格方向乘成交额的量价代理；"
                "新浪基金持仓是滞后披露，三者都不是券商逐笔或Level-2主力账户证明。"
            ),
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
        }

    def _public_daily(self, symbol: str, *, force: bool, allow_network: bool) -> dict[str, Any]:
        cached = self.cache_state.get("individual_fund_flow_daily", symbol, allow_stale=True)
        cached_data = dict(cached.data or {})
        cache_fresh = bool(cached_data) and not bool(cached.cache_status.get("stale"))
        if cache_fresh and not force:
            cached_data["cache_status"] = cached.cache_status
            return cached_data
        if not allow_network:
            if cached_data:
                cached_data["cache_status"] = cached.cache_status
                return cached_data
            return {
                "available": False,
                "quality_status": "missing",
                "rows": [],
                "missing_reasons": ["公开个股日资金流缓存缺失；实时评分不会临时联网伪补"],
                "cache_status": cached.cache_status,
            }
        try:
            payload = self.provider._get_json(
                self.FUND_FLOW_URL,
                {
                    "lmt": "30",
                    "klt": "101",
                    "secid": to_eastmoney_secid(symbol),
                    "fields1": "f1,f2,f3,f7",
                    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
                },
            )
            rows = self._parse_daily_flow(payload)
            if not rows:
                raise RuntimeError("接口未返回有效资金流记录")
            data = {
                "available": True,
                "quality_status": "available",
                "latest": rows[-1],
                "rows": rows,
                "row_count": len(rows),
                "source_id": "eastmoney_individual_fund_flow",
                "source_name": "东方财富个股资金流",
                "source_ref": self.FUND_FLOW_URL,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "missing_reasons": [],
                "truth_boundary": "公开资金流口径，用于相对观察；不是逐笔账户或真实机构席位净买入。",
            }
            status = self.cache_state.put(
                "individual_fund_flow_daily",
                symbol,
                data,
                ttl_seconds=15 * 60,
                symbol=symbol,
                source="eastmoney_individual_fund_flow",
            )
            data["cache_status"] = status
            return data
        except Exception as exc:
            if cached_data:
                cached_data["cache_status"] = cached.cache_status
                cached_data.setdefault("missing_reasons", []).append(f"联网刷新失败，保留历史资金流缓存：{str(exc)[:160]}")
                return cached_data
            return {
                "available": False,
                "quality_status": "error",
                "rows": [],
                "source_ref": self.FUND_FLOW_URL,
                "missing_reasons": [f"东方财富个股资金流获取失败：{str(exc)[:160]}"],
                "cache_status": cached.cache_status,
            }

    @staticmethod
    def _parse_daily_flow(payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw_rows = (((payload or {}).get("data") or {}).get("klines")) or []
        result: list[dict[str, Any]] = []
        for raw in raw_rows:
            parts = str(raw).split(",")
            if len(parts) < 13:
                continue
            date = _iso_date(parts[0])
            if not date:
                continue
            result.append(
                {
                    "date": date,
                    "main_net_inflow": _number(parts[1]),
                    "small_net_inflow": _number(parts[2]),
                    "medium_net_inflow": _number(parts[3]),
                    "large_net_inflow": _number(parts[4]),
                    "super_large_net_inflow": _number(parts[5]),
                    "main_net_ratio_pct": _number(parts[6]),
                    "small_net_ratio_pct": _number(parts[7]),
                    "medium_net_ratio_pct": _number(parts[8]),
                    "large_net_ratio_pct": _number(parts[9]),
                    "super_large_net_ratio_pct": _number(parts[10]),
                    "close": _number(parts[11]),
                    "change_pct": _number(parts[12]),
                }
            )
        result.sort(key=lambda row: str(row.get("date") or ""))
        return result

    def _institutional_holdings(self, symbol: str, *, force: bool, allow_network: bool) -> dict[str, Any]:
        cached = self.cache_state.get("institutional_holding_snapshot", symbol, allow_stale=True)
        cached_data = dict(cached.data or {})
        if cached_data and not force and not cached.cache_status.get("stale"):
            cached_data["cache_status"] = cached.cache_status
            return cached_data
        if not allow_network:
            if cached_data:
                cached_data["cache_status"] = cached.cache_status
                return cached_data
            return {
                "available": False,
                "quality_status": "missing",
                "missing_reasons": ["基金持仓披露缓存缺失"],
                "cache_status": cached.cache_status,
            }
        url = self.HOLDER_URL.format(symbol=symbol)
        try:
            response = self.http.get(url)
            response.encoding = response.apparent_encoding or response.encoding or "gbk"
            parsed = self._parse_holder_html(response.text)
            if not parsed.get("available"):
                raise RuntimeError("页面未解析到基金持仓披露")
            parsed.update(
                {
                    "source_id": "sina_fund_stock_holder",
                    "source_name": "新浪财经基金持股",
                    "source_ref": url,
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "truth_boundary": "基金持仓为披露期快照，存在报告滞后；不代表当前实时机构或主力持仓。",
                }
            )
            status = self.cache_state.put(
                "institutional_holding_snapshot",
                symbol,
                parsed,
                ttl_seconds=24 * 60 * 60,
                symbol=symbol,
                source="sina_fund_stock_holder",
            )
            parsed["cache_status"] = status
            return parsed
        except Exception as exc:
            if cached_data:
                cached_data["cache_status"] = cached.cache_status
                cached_data.setdefault("missing_reasons", []).append(f"持仓披露刷新失败，保留缓存：{str(exc)[:160]}")
                return cached_data
            return {
                "available": False,
                "quality_status": "error",
                "source_ref": url,
                "missing_reasons": [f"基金持仓披露获取失败：{str(exc)[:160]}"],
                "cache_status": cached.cache_status,
            }

    @staticmethod
    def _parse_holder_html(text: str) -> dict[str, Any]:
        parser = _HtmlRows()
        parser.feed(text or "")
        groups: dict[str, list[dict[str, Any]]] = {}
        current_date = ""
        in_holder_table = False
        for row in parser.rows:
            cells = [str(cell or "").strip() for cell in row]
            if not cells:
                continue
            if cells[0] == "截止日期":
                current_date = _iso_date(cells[1] if len(cells) > 1 else "")
                in_holder_table = False
                continue
            if cells[0] == "基金名称" and "基金代码" in cells:
                in_holder_table = bool(current_date)
                continue
            if not in_holder_table or not current_date or len(cells) < 4:
                continue
            fund_code = re.sub(r"\D", "", cells[1] if len(cells) > 1 else "")
            if not fund_code:
                continue
            groups.setdefault(current_date, []).append(
                {
                    "fund_name": cells[0],
                    "fund_code": fund_code,
                    "shares": _number(cells[2] if len(cells) > 2 else None),
                    "float_share_pct": _number(cells[3] if len(cells) > 3 else None),
                    "market_value": _number(cells[4] if len(cells) > 4 else None),
                    "net_asset_pct": _number(cells[5] if len(cells) > 5 else None),
                }
            )
        candidates = sorted(groups.items(), key=lambda item: item[0], reverse=True)
        if not candidates:
            return {
                "available": False,
                "quality_status": "missing",
                "missing_reasons": ["页面没有可识别的基金持仓披露表"],
            }
        complete = [item for item in candidates if len(item[1]) >= 5]
        selected_date, rows = complete[0] if complete else candidates[0]
        previous = next((item for item in complete if item[0] < selected_date), None)
        rows = sorted(rows, key=lambda row: float(row.get("market_value") or 0), reverse=True)
        total_shares = sum(float(row.get("shares") or 0) for row in rows)
        total_value = sum(float(row.get("market_value") or 0) for row in rows)
        previous_shares = (
            sum(float(row.get("shares") or 0) for row in previous[1])
            if previous
            else None
        )
        return {
            "available": True,
            "quality_status": "available" if len(rows) >= 5 else "partial",
            "report_date": selected_date,
            "latest_observed_date": candidates[0][0],
            "partial_latest_skipped": candidates[0][0] != selected_date,
            "fund_count": len(rows),
            "total_disclosed_shares": round(total_shares, 4),
            "total_disclosed_market_value": round(total_value, 4),
            "previous_report_date": previous[0] if previous else "",
            "previous_total_disclosed_shares": round(previous_shares, 4) if previous_shares is not None else None,
            "shares_change": round(total_shares - previous_shares, 4) if previous_shares is not None else None,
            "top_funds": rows[:10],
            "missing_reasons": [] if len(rows) >= 5 else ["最新披露样本少于5只基金，按部分披露展示"],
        }

    @staticmethod
    def _intraday_proxy(points: list[IntradayPoint], quote: dict[str, Any]) -> dict[str, Any]:
        valid = [point for point in points if _number(getattr(point, "price", None)) not in (None, 0)]
        if len(valid) < 2:
            return {
                "available": False,
                "quality_status": "missing",
                "point_count": len(valid),
                "missing_reasons": ["当日分时有效点少于2个，无法形成全天量价资金代理"],
            }
        raw_amounts = [max(0.0, float(_number(getattr(point, "amount", None)) or 0.0)) for point in valid]
        increases = sum(1 for left, right in zip(raw_amounts, raw_amounts[1:]) if right >= left)
        cumulative = len(raw_amounts) >= 20 and increases / max(1, len(raw_amounts) - 1) >= 0.92
        amounts = raw_amounts
        if cumulative:
            amounts = [raw_amounts[0]] + [max(0.0, right - left) for left, right in zip(raw_amounts, raw_amounts[1:])]
        rows: list[dict[str, Any]] = []
        prior_price = float(valid[0].price)
        for point, amount in zip(valid, amounts):
            price = float(point.price)
            avg = _number(getattr(point, "avg_price", None))
            direction = 1 if price > prior_price else -1 if price < prior_price else 1 if avg and price >= avg else -1
            signed = amount * direction
            rows.append({"ts": point.ts, "amount": amount, "signed": signed, "price": price, "avg": avg})
            prior_price = price
        total = sum(row["amount"] for row in rows)
        net = sum(row["signed"] for row in rows)
        inflow = sum(row["amount"] for row in rows if row["signed"] >= 0)
        outflow = sum(row["amount"] for row in rows if row["signed"] < 0)
        last_ts = rows[-1]["ts"]

        def window(minutes: int) -> dict[str, Any]:
            cutoff = last_ts - timedelta(minutes=minutes)
            selected = [row for row in rows if row["ts"] >= cutoff]
            amount = sum(row["amount"] for row in selected)
            signed = sum(row["signed"] for row in selected)
            return {
                "minutes": minutes,
                "amount": round(amount, 4),
                "net_proxy": round(signed, 4),
                "net_ratio_pct": round(signed / amount * 100, 4) if amount > 0 else None,
            }

        morning = [row for row in rows if row["ts"].hour < 12]
        afternoon = [row for row in rows if row["ts"].hour >= 13]

        def period(selected: list[dict[str, Any]]) -> dict[str, Any]:
            amount = sum(row["amount"] for row in selected)
            signed = sum(row["signed"] for row in selected)
            return {
                "amount": round(amount, 4),
                "net_proxy": round(signed, 4),
                "net_ratio_pct": round(signed / amount * 100, 4) if amount > 0 else None,
            }

        last_avg = rows[-1].get("avg")
        return {
            "available": total > 0,
            "quality_status": "proxy_available" if total > 0 else "missing",
            "trade_date": last_ts.date().isoformat(),
            "latest_at": last_ts.isoformat(timespec="seconds"),
            "point_count": len(rows),
            "amount_is_cumulative_source": cumulative,
            "total_amount": round(total, 4),
            "estimated_inflow": round(inflow, 4),
            "estimated_outflow": round(outflow, 4),
            "net_proxy": round(net, 4),
            "net_ratio_pct": round(net / total * 100, 4) if total > 0 else None,
            "last_price": rows[-1]["price"],
            "avg_price": last_avg,
            "price_vs_avg_pct": round((rows[-1]["price"] / last_avg - 1) * 100, 4) if last_avg else None,
            "windows": {str(minutes): window(minutes) for minutes in (5, 15, 30, 60)},
            "morning": period(morning),
            "afternoon": period(afternoon),
            "source": str(quote.get("source") or getattr(valid[-1], "source", "") or "intraday_cache"),
            "missing_reasons": [] if total > 0 else ["分时点存在但成交额字段为空"],
            "truth_boundary": "按价格方向和真实分时成交额估算承接，仅为量价代理，不等同主动买卖盘或主力账户。",
        }

    def _persist_intraday(self, symbol: str, data: dict[str, Any]) -> None:
        now = time.monotonic()
        if now - self._last_intraday_write.get(symbol, 0.0) < 45:
            return
        latest = str(data.get("latest_at") or "")
        key = f"{symbol}:{latest[:16]}" if latest else f"{symbol}:{datetime.now():%Y-%m-%dT%H:%M}"
        self.cache_state.put(
            "individual_capital_intraday",
            key,
            data,
            ttl_seconds=45 * 24 * 60 * 60,
            symbol=symbol,
            source=str(data.get("source") or "intraday_proxy"),
        )
        self._last_intraday_write[symbol] = now

    @staticmethod
    def _score(public_daily: dict[str, Any], intraday_proxy: dict[str, Any]) -> dict[str, Any]:
        score = 50.0
        contributions: list[dict[str, Any]] = []
        evidence_fields: list[str] = []
        latest_date = ""
        public_valid = False
        public_stale = False
        latest = dict(public_daily.get("latest") or {})
        ratio = _number(latest.get("main_net_ratio_pct"))
        latest_date = str(latest.get("date") or "")
        if latest_date:
            try:
                public_stale = (datetime.now().date() - datetime.fromisoformat(latest_date).date()).days > 7
            except ValueError:
                public_stale = True
        if public_daily.get("available") and ratio is not None and not public_stale:
            adjustment = max(-14.0, min(14.0, ratio * 1.2))
            score += adjustment
            public_valid = True
            evidence_fields.append("public_main_net_ratio")
            contributions.append(
                {
                    "factor_key": "public_main_net_ratio",
                    "raw_value": ratio,
                    "adjustment": round(adjustment, 4),
                    "source": "东方财富个股资金流",
                    "explanation": "公开主力净流占比用于相对强弱，不解释为真实机构账户成交。",
                }
            )
            rows = list(public_daily.get("rows") or [])[-5:]
            recent_ratios = [_number(row.get("main_net_ratio_pct")) for row in rows]
            recent_ratios = [value for value in recent_ratios if value is not None]
            if recent_ratios:
                average = sum(recent_ratios) / len(recent_ratios)
                trend_adjustment = max(-6.0, min(6.0, average * 0.5))
                score += trend_adjustment
                evidence_fields.append("public_main_ratio_5d")
                contributions.append(
                    {
                        "factor_key": "public_main_ratio_5d",
                        "raw_value": round(average, 4),
                        "adjustment": round(trend_adjustment, 4),
                        "source": "东方财富近5日资金流",
                        "explanation": "观察近期资金方向是否连续，避免只看单日脉冲。",
                    }
                )

        proxy_valid = bool(intraday_proxy.get("available"))
        proxy_ratio = _number(intraday_proxy.get("net_ratio_pct"))
        if proxy_valid and proxy_ratio is not None:
            adjustment = max(-12.0, min(12.0, proxy_ratio * 0.45))
            score += adjustment
            evidence_fields.append("intraday_amount_direction_proxy")
            contributions.append(
                {
                    "factor_key": "intraday_amount_direction_proxy",
                    "raw_value": proxy_ratio,
                    "adjustment": round(adjustment, 4),
                    "source": "当日分时成交额量价代理",
                    "explanation": "覆盖当日全天和5/15/30/60分钟窗口，不冒充逐笔主动买卖。",
                }
            )
        price_vs_avg = _number(intraday_proxy.get("price_vs_avg_pct"))
        if proxy_valid and price_vs_avg is not None:
            adjustment = max(-5.0, min(5.0, price_vs_avg * 2.0))
            score += adjustment
            evidence_fields.append("price_vs_intraday_avg")
            contributions.append(
                {
                    "factor_key": "price_vs_intraday_avg",
                    "raw_value": price_vs_avg,
                    "adjustment": round(adjustment, 4),
                    "source": "分时均价线",
                    "explanation": "价格相对当日均价只作承接确认。",
                }
            )

        available = public_valid or proxy_valid
        quality = "available" if public_valid and proxy_valid else "partial" if available else "missing"
        sources = []
        if public_valid:
            sources.append("东方财富公开个股资金流")
        if proxy_valid:
            sources.append("当日分时量价代理")
        return {
            "score": round(max(5.0, min(95.0, score)), 2) if available else None,
            "quality_status": quality,
            "source": " + ".join(sources) if sources else "个股资金证据缺失",
            "available_at": intraday_proxy.get("latest_at") or latest_date,
            "stale": bool(public_stale and not proxy_valid),
            "confidence": "medium" if public_valid and proxy_valid else "low",
            "evidence_fields": evidence_fields,
            "contributions": contributions,
        }
