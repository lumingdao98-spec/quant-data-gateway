from __future__ import annotations

from datetime import datetime
from typing import Any

from quant_data.models import Bar, Quote, IntradayPoint
from quant_data.providers.base import MarketDataProvider
from quant_data.utils import ThrottledSession, normalize_symbol, safe_float, to_sina_code


class TencentKlineProvider(MarketDataProvider):
    """腾讯/富途公开K线兜底源。

    仅作为东方财富K线短暂为空时的备用来源。该公开接口主要用于日/周/月K线，
    不承担实盘交易触发依据。返回字段在不同品种上可能略有差异，所以解析时做
    保守处理，只要能得到 OHLCV 即可进入本地缓存。
    """

    name = "tencent_kline"
    KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    MINUTE_URLS = [
        "https://web.ifzq.gtimg.cn/appstock/app/minute/query",
        "https://ifzq.gtimg.cn/appstock/app/minute/query",
    ]

    def __init__(self) -> None:
        self.http = ThrottledSession()
        self.http.session.headers.update({
            "Referer": "https://gu.qq.com/",
            "Accept": "application/json,text/plain,*/*",
        })


    def get_intraday(self, symbol: str, force: bool = False) -> list[IntradayPoint]:
        """腾讯分钟分时兜底。

        公开接口返回格式会随品种变化；这里按多种常见格式保守解析。
        若无法解析足够点数则返回空，由上层继续使用其它兜底。
        """
        symbol = normalize_symbol(symbol)
        code = self._code(symbol)
        last_error: Exception | None = None
        for url in self.MINUTE_URLS:
            try:
                data: dict[str, Any] = self.http.get(url, params={"code": code}).json()
                node = (((data or {}).get("data") or {}).get(code) or {})
                payload = node.get("data") or node
                trade_date = None
                raw = []
                if isinstance(payload, dict):
                    trade_date = payload.get("date") or payload.get("today") or payload.get("time")
                    raw = payload.get("data") or payload.get("minute") or payload.get("minutes") or []
                elif isinstance(payload, list):
                    raw = payload
                if not raw:
                    continue
                points: list[IntradayPoint] = []
                base_date = datetime.now().date()
                if trade_date:
                    txt = str(trade_date)
                    for fmt in ("%Y%m%d", "%Y-%m-%d"):
                        try:
                            base_date = datetime.strptime(txt[:10], fmt).date()
                            break
                        except Exception:
                            pass
                cum_amount = 0.0
                cum_volume = 0.0
                for item in raw:
                    if isinstance(item, str):
                        parts = item.replace(",", " ").split()
                    elif isinstance(item, (list, tuple)):
                        parts = [str(x) for x in item]
                    else:
                        continue
                    if len(parts) < 2:
                        continue
                    t = parts[0].strip()
                    # 0930 / 09:30 / 2026-05-15 09:30:00 都兼容。
                    ts = None
                    if ":" in t and "-" in t:
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                            try:
                                ts = datetime.strptime(t[:19], fmt)
                                break
                            except Exception:
                                pass
                    elif ":" in t:
                        try:
                            hh, mm = t.split(":")[:2]
                            ts = datetime(base_date.year, base_date.month, base_date.day, int(hh), int(mm))
                        except Exception:
                            pass
                    else:
                        digits = ''.join(ch for ch in t if ch.isdigit())
                        if len(digits) >= 4:
                            try:
                                ts = datetime(base_date.year, base_date.month, base_date.day, int(digits[:2]), int(digits[2:4]))
                            except Exception:
                                pass
                    if ts is None:
                        continue
                    price = safe_float(parts[1])
                    if price <= 0:
                        continue
                    # 常见格式：time price volume amount avg；字段不稳定，保守处理。
                    vol = safe_float(parts[2]) if len(parts) > 2 else 0.0
                    amt = safe_float(parts[3]) if len(parts) > 3 else 0.0
                    avg = safe_float(parts[4]) if len(parts) > 4 else 0.0
                    cum_volume += vol
                    cum_amount += amt
                    if not avg and cum_amount > 0 and cum_volume > 0:
                        avg = cum_amount / max(cum_volume, 1.0)
                        if avg > price * 10 or avg < price / 10:
                            avg = 0.0
                    points.append(IntradayPoint(
                        symbol=symbol,
                        ts=ts,
                        price=price,
                        avg_price=avg if avg > 0 else None,
                        volume=vol,
                        amount=amt,
                        source="tencent_minute",
                    ))
                # 去重排序，过滤午休/盘外异常点也交给前端固定时间轴处理。
                uniq = {p.ts: p for p in points}
                out = [uniq[k] for k in sorted(uniq)]
                if len(out) >= 2:
                    return out
            except Exception as exc:
                last_error = exc
                continue
        if last_error:
            raise last_error
        return []

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        # 本源仅用于K线兜底，行情仍走东方财富/新浪。
        return []

    def _code(self, symbol: str) -> str:
        return to_sina_code(symbol)

    def _period_key(self, frame: str) -> tuple[str, str]:
        frame = "1M" if frame == "1mo" else frame
        if frame == "1d":
            return "day", "day"
        if frame == "1w":
            return "week", "week"
        if frame == "1M":
            return "month", "month"
        raise ValueError(f"腾讯K线兜底仅支持日/周/月K线，不支持: {frame}")

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        symbol = normalize_symbol(symbol)
        frame = "1M" if frame == "1mo" else frame
        period, plain_key = self._period_key(frame)
        adj = "" if adjust in {"none", "", None} else str(adjust).lower()
        # 公开接口格式：sh600519,day,,,260,qfq 或 sh600519,week,,,260,qfq
        # 不复权时最后一项留空；部分品种只返回不复权，所以后面会多key兜底。
        param = f"{self._code(symbol)},{period},,,{int(limit)},{adj}"
        params = {"param": param, "_": int(datetime.now().timestamp() * 1000)}
        data: dict[str, Any] = self.http.get(self.KLINE_URL, params=params).json()
        code = self._code(symbol)
        node = (((data or {}).get("data") or {}).get(code) or {})
        candidate_keys = []
        if adj:
            candidate_keys.append(f"{adj}{plain_key}")
        candidate_keys.extend([plain_key, f"qfq{plain_key}", f"hfq{plain_key}"])
        raw = []
        for key in candidate_keys:
            value = node.get(key)
            if isinstance(value, list) and value:
                raw = value
                break
        bars: list[Bar] = []
        for item in raw[-int(limit):]:
            if not isinstance(item, (list, tuple)) or len(item) < 5:
                continue
            # 常见格式：[date, open, close, high, low, volume, ...]
            try:
                ts = datetime.strptime(str(item[0])[:10], "%Y-%m-%d")
            except Exception:
                continue
            open_ = safe_float(item[1])
            close = safe_float(item[2])
            high = safe_float(item[3])
            low = safe_float(item[4])
            volume = safe_float(item[5]) if len(item) > 5 else 0.0
            amount = safe_float(item[6]) if len(item) > 6 else 0.0
            if open_ <= 0 or high <= 0 or low <= 0 or close <= 0:
                continue
            bars.append(Bar(
                symbol=symbol,
                frame=frame,
                ts=ts,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                amount=amount,
                source=self.name,
            ))
        return bars
