from __future__ import annotations

from abc import ABC, abstractmethod

from quant_data.models import Asset, Bar, IntradayPoint, Quote, OrderBook


class MarketDataProvider(ABC):
    name = "base"

    @abstractmethod
    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        raise NotImplementedError

    def get_quote(self, symbol: str) -> Quote:
        quotes = self.get_quotes([symbol])
        if not quotes:
            raise RuntimeError(f"{self.name} 无法获取行情: {symbol}")
        return quotes[0]

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        raise NotImplementedError(f"{self.name} 不支持 K 线")

    def get_spot_list(self, page: int = 1, page_size: int = 100, fs: str | None = None) -> list[Quote]:
        raise NotImplementedError(f"{self.name} 不支持全市场快照")

    def get_intraday(self, symbol: str, force: bool = False) -> list[IntradayPoint]:
        raise NotImplementedError(f"{self.name} 不支持分时数据")

    def get_order_book(self, symbol: str) -> OrderBook:
        raise NotImplementedError(f"{self.name} 不支持五档盘口")

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        return []
