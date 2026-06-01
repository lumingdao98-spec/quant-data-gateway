from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, replace
from typing import Iterable

from quant_data.models import Asset, Bar, IntradayPoint, Quote, OrderBook
from quant_data.providers.base import MarketDataProvider
from quant_data.providers.eastmoney import EastmoneyProvider
from quant_data.providers.sina import SinaProvider
from quant_data.providers.tencent import TencentKlineProvider
from quant_data.utils import chunked, normalize_symbol


@dataclass
class ProviderWarning:
    provider: str
    operation: str
    message: str


class ProviderManager:
    """多数据源管理器。

    默认优先级：东方财富 -> 新浪 -> 腾讯K线兜底 -> AKShare可选。
    目的不是追求某一个接口“永远稳定”，而是让系统具有可替换、可降级能力。
    """

    def __init__(self, enable_akshare: bool = True) -> None:
        self.warnings: list[ProviderWarning] = []
        self._warning_last_seen: dict[tuple[str, str, str], float] = {}
        self.providers: list[MarketDataProvider] = [EastmoneyProvider(), SinaProvider(), TencentKlineProvider()]
        if enable_akshare:
            try:
                from quant_data.providers.akshare_optional import AkshareOptionalProvider

                self.providers.append(AkshareOptionalProvider())
            except Exception as exc:
                self._log_warning("akshare", "init", exc)

    def _log_warning(self, provider: str, operation: str, exc: BaseException, *, quiet_seconds: float = 60.0) -> None:
        msg = str(exc)
        if len(msg) > 260:
            msg = msg[:260] + "..."
        key = (provider, operation, msg[:120])
        now = time.monotonic()
        last = self._warning_last_seen.get(key, 0.0)
        # 同一接口同一类错误 60 秒内只打印一次，避免休市/网络波动时刷屏。
        if now - last < quiet_seconds:
            return
        self._warning_last_seen[key] = now
        self.warnings.append(ProviderWarning(provider, operation, msg))
        if len(self.warnings) > 100:
            del self.warnings[:-100]
        # 五档盘口公开接口很容易在休市、网络波动或被限流时超时。
        # 该告警保留在 /api/provider/warnings 中，但默认不刷控制台，避免影响使用体验。
        quiet_ops = {"get_order_book", "get_quotes"}
        verbose = os.environ.get("QUANT_VERBOSE_PROVIDER_WARNINGS", "0") == "1"
        if operation in quiet_ops and not verbose:
            return
        print(f"[ProviderManager] {provider}.{operation} failed: {msg}", file=sys.stderr, flush=True)

    def get_quotes(self, symbols: Iterable[str]) -> list[Quote]:
        requested = [normalize_symbol(s) for s in symbols]
        if not requested:
            return []
        result_by_symbol: dict[str, Quote] = {}
        missing = set(requested)

        for provider in self.providers:
            if not missing:
                break
            try:
                provider_result: list[Quote] = []
                # 东方财富与新浪都支持批量，但一次不要太多。
                for group in chunked(list(missing), 80):
                    provider_result.extend(provider.get_quotes(group))
                for quote in provider_result:
                    if quote.symbol in missing:
                        result_by_symbol[quote.symbol] = quote
                        missing.remove(quote.symbol)
            except Exception as exc:
                self._log_warning(provider.name, "get_quotes", exc)
                continue

        return [result_by_symbol[s] for s in requested if s in result_by_symbol]

    def get_quote(self, symbol: str) -> Quote:
        quotes = self.get_quotes([symbol])
        if not quotes:
            raise RuntimeError(f"所有数据源均未返回行情: {symbol}")
        return quotes[0]

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq") -> list[Bar]:
        last_error: BaseException | None = None
        empty_providers: list[str] = []
        desired = str(adjust or "none").lower()
        if desired not in {"none", "qfq", "hfq"}:
            desired = "qfq"

        # V3.15：日/周/月复权K线先严格按用户指定口径跨源兜底。
        # 不能在东方财富 qfq 失败后立刻拿 none 冒充 qfq，否则回撤率会被除权缺口污染。
        strict_adjusts = [desired]
        fallback_adjusts: list[str] = []
        if not (frame in {"1d", "1w", "1M", "1mo"} and desired in {"qfq", "hfq"}):
            for x in ["none", "qfq", "hfq"]:
                if x not in strict_adjusts and x not in fallback_adjusts:
                    fallback_adjusts.append(x)

        for phase, candidates in [("strict", strict_adjusts), ("fallback", fallback_adjusts)]:
            for provider in self.providers:
                for adj in candidates:
                    try:
                        bars = provider.get_kline(symbol, frame=frame, limit=limit, adjust=adj)
                        if bars:
                            if adj != desired:
                                return [replace(b, source=f"{b.source}|fallback_adjust:{adj}") for b in bars]
                            return bars
                        empty_providers.append(f"{provider.name}:{adj}:{phase}")
                    except Exception as exc:
                        last_error = exc
                        if "不支持 K 线" not in str(exc) and "不支持K线" not in str(exc):
                            self._log_warning(provider.name, "get_kline", exc)
                        # 当前 provider 不支持该K线类型时，继续换下一源；不要因为新浪分钟K不支持日K而中断日K兜底。
                        break
        detail = ",".join(empty_providers[-12:]) if empty_providers else "none"
        raise RuntimeError(f"所有数据源均未返回K线: {symbol}; adjust={desired}; empty={detail}; last_error={last_error}")


    def get_spot_list(self, page: int = 1, page_size: int = 100) -> list[Quote]:
        last_error: BaseException | None = None
        for provider in self.providers:
            try:
                quotes = provider.get_spot_list(page=page, page_size=page_size)
                if quotes:
                    return quotes
            except Exception as exc:
                last_error = exc
                self._log_warning(provider.name, "get_spot_list", exc)
        raise RuntimeError(f"所有数据源均未返回全市场快照; last_error={last_error}")

    def get_intraday(self, symbol: str) -> list[IntradayPoint]:
        last_error: BaseException | None = None
        empty_providers: list[str] = []
        # 分时公开源按稳定性依次尝试：东方财富 trends -> 新浪分钟K -> 腾讯分钟。
        # 休市后某个接口经常返回空，这里不能因为第一个源为空就放弃。
        for provider in self.providers:
            if provider.name not in {"eastmoney", "sina", "tencent_kline"}:
                continue
            try:
                points = provider.get_intraday(symbol)
                if points and len(points) >= 2:
                    return points
                empty_providers.append(provider.name)
            except Exception as exc:
                last_error = exc
                # 不支持分时属于正常情况；其它错误进入诊断接口。
                if "不支持" not in str(exc):
                    self._log_warning(provider.name, "get_intraday", exc)
        if last_error:
            self._log_warning("all", "get_intraday", last_error, quiet_seconds=180.0)
        if empty_providers:
            self._log_warning("all", "get_intraday_empty", RuntimeError("empty=" + ",".join(empty_providers)), quiet_seconds=180.0)
        return []


    def get_order_book(self, symbol: str) -> OrderBook | None:
        last_error: BaseException | None = None
        # 五档盘口目前也只有东方财富公开接口可用；其他 Provider 不支持时不刷屏。
        for provider in self.providers:
            if provider.name not in {"eastmoney", "sina"}:
                continue
            try:
                book = provider.get_order_book(symbol)
                levels = (list(book.asks or []) + list(book.bids or [])) if book else []
                if any((x.price is not None and x.price > 0) or (x.volume is not None and x.volume > 0) for x in levels):
                    return book
            except Exception as exc:
                last_error = exc
                self._log_warning(provider.name, "get_order_book", exc)
        # 不再额外打印 all.get_order_book；具体源失败已经记录到 warnings。
        return None

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        for provider in self.providers:
            try:
                assets = provider.search_assets(keyword, limit=limit)
                if assets:
                    return assets
            except Exception as exc:
                self._log_warning(provider.name, "search_assets", exc)
        return []
