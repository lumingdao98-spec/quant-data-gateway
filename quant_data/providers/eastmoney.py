from __future__ import annotations

from datetime import datetime
from typing import Any

from quant_data.models import Asset, AssetType, Bar, IntradayPoint, Quote, OrderBook, OrderBookLevel
from quant_data.providers.base import MarketDataProvider
from quant_data.utils import (
    ThrottledSession,
    normalize_symbol,
    parse_dt,
    safe_float,
    to_eastmoney_secid,
)


class EastmoneyProvider(MarketDataProvider):
    """东方财富公开行情源。

    本 Provider 只使用公开网页接口，适合研究、筛选、看盘辅助。
    不建议把它作为实盘自动下单的唯一触发源。
    """

    name = "eastmoney"

    QUOTE_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
    KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    KLINE_URLS = [
        "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "https://push2.eastmoney.com/api/qt/stock/kline/get",
    ]
    TREND_URL = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"

    QUOTE_FIELDS = ",".join(
        [
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10",
            "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f20", "f21", "f23",
        ]
    )

    def __init__(self) -> None:
        self.http = ThrottledSession()

    def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        resp = self.http.get(url, params=params)
        return resp.json()

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        if not symbols:
            return []
        secids = ",".join(to_eastmoney_secid(s) for s in symbols)
        params = {
            "fltt": "2",
            "invt": "2",
            "fields": self.QUOTE_FIELDS,
            "secids": secids,
        }
        data = self._get_json(self.QUOTE_URL, params=params)
        diff = ((data or {}).get("data") or {}).get("diff") or []
        quotes: list[Quote] = []
        for row in diff:
            q = self._parse_quote_row(row)
            if q:
                quotes.append(q)
        return quotes

    def get_spot_list(self, page: int = 1, page_size: int = 100, fs: str | None = None) -> list[Quote]:
        # A股 + 常用 ETF/基金场内品种。后续系统可按页面参数拆分股票/ETF/指数。
        fs = fs or "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048,m:1+t:2+s:2048,m:0+t:5,m:1+t:3"
        params = {
            "pn": int(page),
            "pz": int(page_size),
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": fs,
            "fields": self.QUOTE_FIELDS + ",f100",
        }
        data = self._get_json(self.CLIST_URL, params=params)
        diff = ((data or {}).get("data") or {}).get("diff") or []
        return [q for row in diff if (q := self._parse_quote_row(row))]

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        symbol = normalize_symbol(symbol)
        klt_map = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "60m": "60",
            "1d": "101",
            "1w": "102",
            "1M": "103",
            "1mo": "103",
        }
        if frame not in klt_map:
            raise ValueError(f"不支持的K线周期: {frame}; 可选 1m/5m/15m/30m/60m/1d/1w/1M")
        fqt_map = {"none": "0", "": "0", "qfq": "1", "hfq": "2"}
        # 除默认 secid 外，再尝试沪/深两种 secid，防止 ETF/北交所/接口路由变化导致空数据。
        secids = [to_eastmoney_secid(symbol), f"0.{symbol}", f"1.{symbol}"]
        secids = list(dict.fromkeys(secids))
        urls = getattr(self, "KLINE_URLS", [self.KLINE_URL])
        last_raw: list[str] = []
        for url in urls:
            for secid in secids:
                params = {
                    "secid": secid,
                    "klt": klt_map[frame],
                    "fqt": fqt_map.get(str(adjust or "none"), "0"),
                    "end": "20500101",
                    "lmt": int(limit),
                    "fields1": "f1,f2,f3,f4,f5,f6",
                    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                    # ut 并非总是必需，但部分环境下加上更稳定。
                    "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                }
                data = self._get_json(url, params=params)
                raw = (((data or {}).get("data") or {}).get("klines")) or []
                if raw:
                    last_raw = raw
                    break
            if last_raw:
                break
        bars: list[Bar] = []
        for item in last_raw[-int(limit):]:
            parts = str(item).split(",")
            if len(parts) < 7:
                continue
            ts = parse_dt(parts[0])
            open_ = safe_float(parts[1])
            close = safe_float(parts[2])
            high = safe_float(parts[3])
            low = safe_float(parts[4])
            if open_ <= 0 or close <= 0 or high <= 0 or low <= 0:
                continue
            bars.append(
                Bar(
                    symbol=symbol,
                    frame="1M" if frame in {"1M", "1mo"} else frame,
                    ts=ts,
                    open=open_,
                    close=close,
                    high=high,
                    low=low,
                    volume=safe_float(parts[5]),
                    amount=safe_float(parts[6]),
                    change_pct=safe_float(parts[8]) if len(parts) > 8 else None,
                    turnover=safe_float(parts[10]) if len(parts) > 10 else None,
                    source=self.name,
                )
            )
        return bars


    def get_intraday(self, symbol: str, force: bool = False) -> list[IntradayPoint]:
        """获取分时数据，并在休市/周末时回退到最近一个有分时数据的交易日。

        东方财富 trends2 在非交易时段有时会返回空数组，过去版本会让前端把
        已有分时图清空。这里先取 ndays=1；如果为空，再取 ndays=5，按日期分组
        返回最近一个完整交易日的分时点。这样休市打开或手动刷新，仍能看到
        最近收盘日的分时走势、成交量和副图。
        """
        symbol = normalize_symbol(symbol)

        def fetch_raw(ndays: int) -> list[str]:
            params = {
                "secid": to_eastmoney_secid(symbol),
                "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
                "iscr": "0",
                "iscca": "0",
                "ndays": str(ndays),
            }
            data = self._get_json(self.TREND_URL, params=params)
            return (((data or {}).get("data") or {}).get("trends")) or []

        def parse_points(raw: list[str]) -> list[IntradayPoint]:
            points: list[IntradayPoint] = []
            for item in raw:
                parts = str(item).split(",")
                if len(parts) < 2:
                    continue
                ts = parse_dt(parts[0])
                price = safe_float(parts[1])
                avg = safe_float(parts[2]) if len(parts) > 2 else None
                vol = safe_float(parts[5]) if len(parts) > 5 else None
                amt = safe_float(parts[6]) if len(parts) > 6 else None
                if price <= 0:
                    continue
                points.append(
                    IntradayPoint(
                        symbol=symbol,
                        ts=ts,
                        price=price,
                        avg_price=avg if avg and avg > 0 else None,
                        volume=vol if vol and vol >= 0 else None,
                        amount=amt if amt and amt >= 0 else None,
                        source=self.name,
                    )
                )
            return points

        raw = fetch_raw(1)
        points = parse_points(raw)
        if len(points) >= 2:
            return points

        raw5 = fetch_raw(5)
        points5 = parse_points(raw5)
        if not points5:
            return points
        # ndays=5 可能混合多个交易日；只返回最近日期的分时。
        by_date: dict[str, list[IntradayPoint]] = {}
        for p in points5:
            by_date.setdefault(p.ts.date().isoformat(), []).append(p)
        for d in sorted(by_date.keys(), reverse=True):
            group = by_date[d]
            if len(group) >= 2:
                return group
        return points5[-1:]


    def get_order_book(self, symbol: str) -> OrderBook:
        """获取五档盘口。

        说明：东方财富公开字段可能变化；这里做了保守解析。
        价格/挂单量返回为空时，前端显示 --，不影响主行情和K线功能。
        """
        symbol = normalize_symbol(symbol)
        params = {
            "secid": to_eastmoney_secid(symbol),
            "fltt": "2",
            "invt": "2",
            "fields": "f11,f12,f13,f14,f15,f16,f17,f18,f19,f20,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f49,f50",
        }
        data = self._get_json("https://push2.eastmoney.com/api/qt/stock/get", params=params)
        row = ((data or {}).get("data") or {})
        # 常见映射：买一 f11/f12, 买二 f13/f14 ... 买五 f19/f20；卖一 f39/f40, 卖二 f37/f38 ... 卖五 f31/f32。
        bids = [
            OrderBookLevel(safe_float(row.get("f11")) or None, safe_float(row.get("f12")) or None),
            OrderBookLevel(safe_float(row.get("f13")) or None, safe_float(row.get("f14")) or None),
            OrderBookLevel(safe_float(row.get("f15")) or None, safe_float(row.get("f16")) or None),
            OrderBookLevel(safe_float(row.get("f17")) or None, safe_float(row.get("f18")) or None),
            OrderBookLevel(safe_float(row.get("f19")) or None, safe_float(row.get("f20")) or None),
        ]
        asks = [
            OrderBookLevel(safe_float(row.get("f39")) or None, safe_float(row.get("f40")) or None),
            OrderBookLevel(safe_float(row.get("f37")) or None, safe_float(row.get("f38")) or None),
            OrderBookLevel(safe_float(row.get("f35")) or None, safe_float(row.get("f36")) or None),
            OrderBookLevel(safe_float(row.get("f33")) or None, safe_float(row.get("f34")) or None),
            OrderBookLevel(safe_float(row.get("f31")) or None, safe_float(row.get("f32")) or None),
        ]
        # 只要有一个有效价格就返回，否则也返回空结构，便于前端稳定展示。
        bid_sum = sum((x.volume or 0) for x in bids)
        ask_sum = sum((x.volume or 0) for x in asks)
        order_diff = bid_sum - ask_sum if (bid_sum or ask_sum) else None
        order_ratio = (order_diff / (bid_sum + ask_sum) * 100) if (bid_sum + ask_sum) else None
        return OrderBook(symbol=symbol, ts=datetime.now(), asks=asks, bids=bids, order_ratio=order_ratio, order_diff=order_diff, source=self.name)

    def _parse_quote_row(self, row: dict[str, Any]) -> Quote | None:
        symbol = normalize_symbol(row.get("f12", ""))
        if not symbol:
            return None
        name = str(row.get("f14") or symbol)
        last = safe_float(row.get("f2"))
        pre_close = safe_float(row.get("f18"), last)
        change = safe_float(row.get("f4"), last - pre_close)
        change_pct = safe_float(row.get("f3"), (last / pre_close - 1) * 100 if pre_close else 0.0)
        f13 = str(row.get("f13") or "")
        exchange = "SH" if f13 == "1" else "SZ" if f13 == "0" else ""
        asset_type = AssetType.ETF if symbol.startswith(("15", "51", "56", "58")) else AssetType.STOCK
        return Quote(
            symbol=symbol,
            name=name,
            ts=datetime.now(),
            last=last,
            pre_close=pre_close,
            open=safe_float(row.get("f17"), last),
            high=safe_float(row.get("f15"), last),
            low=safe_float(row.get("f16"), last),
            volume=safe_float(row.get("f5")),
            amount=safe_float(row.get("f6")),
            change=change,
            change_pct=change_pct,
            turnover=safe_float(row.get("f8")) if row.get("f8") not in (None, "-") else None,
            amplitude=safe_float(row.get("f7")) if row.get("f7") not in (None, "-") else None,
            pe_dynamic=safe_float(row.get("f9")) if row.get("f9") not in (None, "-") else None,
            pb=safe_float(row.get("f23")) if row.get("f23") not in (None, "-") else None,
            volume_ratio=safe_float(row.get("f10")) if row.get("f10") not in (None, "-") else None,
            total_market_cap=safe_float(row.get("f20")) if row.get("f20") not in (None, "-") else None,
            float_market_cap=safe_float(row.get("f21")) if row.get("f21") not in (None, "-") else None,
            market="CN",
            asset_type=asset_type,
            source=self.name,
        )

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        # 东方财富搜索接口变化较频繁。这里用全市场第一页/大页做轻量搜索，系统后续可换更稳定搜索源。
        quotes = self.get_spot_list(page=1, page_size=5000)
        keyword = keyword.strip().lower()
        assets: list[Asset] = []
        for q in quotes:
            if keyword in q.symbol.lower() or keyword in q.name.lower():
                assets.append(Asset(q.symbol, q.name, q.asset_type, market=q.market, source=self.name))
                if len(assets) >= limit:
                    break
        return assets
