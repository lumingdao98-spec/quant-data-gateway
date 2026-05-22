from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from quant_data.models import AssetType, Bar, IntradayPoint, Quote
from quant_data.providers.base import MarketDataProvider
from quant_data.utils import ThrottledSession, normalize_symbol, safe_float, to_sina_code


class SinaProvider(MarketDataProvider):
    """新浪财经实时行情与分钟K线兜底源。

    说明：新浪接口作为东方财富分时/K线为空时的补充，不作为实盘交易唯一依据。
    """

    name = "sina"
    QUOTE_URL = "https://hq.sinajs.cn/list={codes}"
    KLINE_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"

    def __init__(self) -> None:
        self.http = ThrottledSession()
        self.http.session.headers.update({"Referer": "https://finance.sina.com.cn/"})

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        if not symbols:
            return []
        codes = ",".join(to_sina_code(s) for s in symbols)
        resp = self.http.get(self.QUOTE_URL.format(codes=codes))
        try:
            text = resp.content.decode("gbk", errors="ignore")
        except Exception:
            text = resp.text
        quotes: list[Quote] = []
        for line in text.split(";"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            try:
                left, right = line.split("=", 1)
                sina_code = left.split("hq_str_")[-1]
                symbol = normalize_symbol(sina_code)
                payload = right.strip().strip('"')
                parts = payload.split(",")
                if len(parts) < 32 or not parts[0]:
                    continue
                name = parts[0]
                open_ = safe_float(parts[1])
                pre_close = safe_float(parts[2])
                last = safe_float(parts[3])
                high = safe_float(parts[4])
                low = safe_float(parts[5])
                volume_shares = safe_float(parts[8])
                amount = safe_float(parts[9])
                date_s = parts[30] if len(parts) > 30 else ""
                time_s = parts[31] if len(parts) > 31 else ""
                try:
                    ts = datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts = datetime.now()
                change = last - pre_close if pre_close else 0.0
                change_pct = change / pre_close * 100 if pre_close else 0.0
                asset_type = AssetType.ETF if symbol.startswith(("15", "51", "56", "58")) else AssetType.STOCK
                quotes.append(
                    Quote(
                        symbol=symbol,
                        name=name,
                        ts=ts,
                        last=last,
                        pre_close=pre_close,
                        open=open_,
                        high=high,
                        low=low,
                        volume=volume_shares / 100.0,
                        amount=amount,
                        change=change,
                        change_pct=change_pct,
                        market="CN",
                        asset_type=asset_type,
                        source=self.name,
                    )
                )
            except Exception:
                continue
        return quotes

    def _json_or_text_list(self, text: str) -> list[dict[str, Any]]:
        text = (text or "").strip()
        if not text:
            return []
        # 正常情况下返回 JSON 数组；个别情况下可能有 callback 包裹。
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except Exception:
            pass
        m = re.search(r"(\[\s*\{.*\}\s*\])", text, flags=re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                return data if isinstance(data, list) else []
            except Exception:
                return []
        return []

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        """新浪分钟K线兜底。

        支持 1m/5m/15m/30m/60m。日/周/月仍由东方财富/腾讯负责。
        """
        symbol = normalize_symbol(symbol)
        scale_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}
        if frame not in scale_map:
            raise NotImplementedError(f"{self.name} 仅支持分钟K线兜底，不支持: {frame}")
        params = {
            "symbol": to_sina_code(symbol),
            "scale": scale_map[frame],
            "ma": "no",
            "datalen": int(limit),
        }
        resp = self.http.get(self.KLINE_URL, params=params)
        try:
            text = resp.content.decode("utf-8", errors="ignore")
        except Exception:
            text = resp.text
        raw = self._json_or_text_list(text)
        bars: list[Bar] = []
        for item in raw[-int(limit):]:
            if not isinstance(item, dict):
                continue
            day = str(item.get("day") or item.get("date") or item.get("time") or "")
            ts = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    ts = datetime.strptime(day[:19], fmt)
                    break
                except Exception:
                    pass
            if ts is None:
                continue
            open_ = safe_float(item.get("open"))
            high = safe_float(item.get("high"))
            low = safe_float(item.get("low"))
            close = safe_float(item.get("close"))
            volume_raw = safe_float(item.get("volume"))
            amount = safe_float(item.get("amount"))
            if open_ <= 0 or high <= 0 or low <= 0 or close <= 0:
                continue
            # 新浪分钟K线 volume 单位不总是稳定，这里保守按接口原值保留，前端只作走势参考。
            bars.append(Bar(
                symbol=symbol,
                frame=frame,
                ts=ts,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume_raw,
                amount=amount,
                source="sina_minute",
            ))
        return bars

    def get_intraday(self, symbol: str, force: bool = False) -> list[IntradayPoint]:
        bars = self.get_kline(symbol, frame="1m", limit=360, adjust="none")
        if not bars:
            return []
        last_day = max(b.ts.date() for b in bars)
        day_bars = [b for b in bars if b.ts.date() == last_day]
        if len(day_bars) < 2:
            return []
        points: list[IntradayPoint] = []
        cum_amount = 0.0
        cum_volume = 0.0
        for b in day_bars:
            vol = float(b.volume or 0.0)
            amt = float(b.amount or 0.0)
            cum_amount += amt
            cum_volume += vol
            avg = None
            if cum_amount > 0 and cum_volume > 0:
                # 不同源 volume 单位可能不同；均价不可靠时前端仍可显示价格线。
                avg = cum_amount / max(cum_volume, 1.0)
                if avg > b.high * 10 or avg < b.low / 10:
                    avg = None
            points.append(IntradayPoint(
                symbol=symbol,
                ts=b.ts,
                price=b.close,
                avg_price=avg,
                volume=vol,
                amount=amt,
                source="sina_1m_fallback",
            ))
        return points
