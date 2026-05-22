from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from quant_data.models import Asset, AssetType, Bar, Quote
from quant_data.providers.base import MarketDataProvider
from quant_data.utils import normalize_symbol, safe_float


class AkshareOptionalProvider(MarketDataProvider):
    """AKShare 可选数据源。

    该模块不是唯一依赖。安装 AKShare 后可作为第三数据源使用；
    如果 AKShare 或其上游接口异常，ProviderManager 会继续使用其他源或缓存。
    """

    name = "akshare"

    def __init__(self) -> None:
        try:
            import akshare as ak  # type: ignore
        except Exception as exc:
            raise RuntimeError("未安装 AKShare，可运行 pip install akshare，或直接使用 eastmoney/sina 源") from exc
        self.ak: Any = ak
        self._spot_cache: dict[str, dict[str, Any]] = {}
        self._spot_cache_ts: datetime | None = None

    def _refresh_spot(self) -> None:
        if self._spot_cache_ts and (datetime.now() - self._spot_cache_ts).total_seconds() < 8:
            return
        df = self.ak.stock_zh_a_spot_em()
        cache: dict[str, dict[str, Any]] = {}
        for _, row in df.iterrows():
            code = normalize_symbol(row.get("代码", ""))
            cache[code] = dict(row)
        self._spot_cache = cache
        self._spot_cache_ts = datetime.now()

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        self._refresh_spot()
        quotes: list[Quote] = []
        for s in symbols:
            symbol = normalize_symbol(s)
            row = self._spot_cache.get(symbol)
            if not row:
                continue
            last = safe_float(row.get("最新价"))
            pre_close = safe_float(row.get("昨收"), last)
            asset_type = AssetType.ETF if symbol.startswith(("15", "51", "56", "58")) else AssetType.STOCK
            quotes.append(
                Quote(
                    symbol=symbol,
                    name=str(row.get("名称") or symbol),
                    ts=datetime.now(),
                    last=last,
                    pre_close=pre_close,
                    open=safe_float(row.get("今开"), last),
                    high=safe_float(row.get("最高"), last),
                    low=safe_float(row.get("最低"), last),
                    volume=safe_float(row.get("成交量")),
                    amount=safe_float(row.get("成交额")),
                    change=safe_float(row.get("涨跌额"), last - pre_close),
                    change_pct=safe_float(row.get("涨跌幅")),
                    turnover=safe_float(row.get("换手率")) if row.get("换手率") not in (None, "-") else None,
                    market="CN",
                    asset_type=asset_type,
                    source=self.name,
                )
            )
        return quotes

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        symbol = normalize_symbol(symbol)
        if frame == "1d":
            start_date = (datetime.now() - timedelta(days=max(limit * 3, 900))).strftime("%Y%m%d")
            df = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust=adjust,
            )
            bars: list[Bar] = []
            for _, row in df.tail(limit).iterrows():
                ts = row.get("日期")
                if not isinstance(ts, datetime):
                    ts = datetime.strptime(str(ts), "%Y-%m-%d")
                bars.append(
                    Bar(
                        symbol=symbol,
                        frame="1d",
                        ts=ts,
                        open=safe_float(row.get("开盘")),
                        high=safe_float(row.get("最高")),
                        low=safe_float(row.get("最低")),
                        close=safe_float(row.get("收盘")),
                        volume=safe_float(row.get("成交量")),
                        amount=safe_float(row.get("成交额")),
                        turnover=safe_float(row.get("换手率")) if "换手率" in row else None,
                        change_pct=safe_float(row.get("涨跌幅")) if "涨跌幅" in row else None,
                        source=self.name,
                    )
                )
            return bars
        period = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}.get(frame)
        if not period:
            raise ValueError(f"AKShare 不支持该周期或未适配: {frame}")
        df = self.ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            adjust="",
            start_date="1979-09-01 09:32:00",
            end_date="2222-01-01 09:32:00",
        )
        bars: list[Bar] = []
        for _, row in df.tail(limit).iterrows():
            ts = row.get("时间") or row.get("日期")
            if not isinstance(ts, datetime):
                ts = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
            bars.append(
                Bar(
                    symbol=symbol,
                    frame=frame,
                    ts=ts,
                    open=safe_float(row.get("开盘")),
                    high=safe_float(row.get("最高")),
                    low=safe_float(row.get("最低")),
                    close=safe_float(row.get("收盘")),
                    volume=safe_float(row.get("成交量")),
                    amount=safe_float(row.get("成交额")),
                    source=self.name,
                )
            )
        return bars

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        df = self.ak.stock_info_a_code_name()
        keyword = keyword.strip().lower()
        assets: list[Asset] = []
        for _, row in df.iterrows():
            code = normalize_symbol(row.get("code") or row.get("代码"))
            name = str(row.get("name") or row.get("名称") or code)
            if keyword in code.lower() or keyword in name.lower():
                assets.append(Asset(code, name, AssetType.STOCK, source=self.name))
                if len(assets) >= limit:
                    break
        return assets
