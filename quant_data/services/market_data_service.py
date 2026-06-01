from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from datetime import datetime
from typing import Iterable

from quant_data.cache import MarketCache
from quant_data.config import DAILY_KLINE_CACHE_SECONDS, MINUTE_KLINE_CACHE_SECONDS, QUOTE_CACHE_SECONDS
from quant_data.models import Asset, AssetType, Bar, IntradayPoint, Quote, OrderBook
from quant_data.providers.provider_manager import ProviderManager
from quant_data.utils import normalize_symbol


class MarketDataService:
    """系统上层统一调用的数据服务。

    UI、策略、回测以后都只调用这个服务，不直接依赖某个网站接口。
    """

    def __init__(self, cache: MarketCache | None = None, provider_manager: ProviderManager | None = None) -> None:
        self.cache = cache or MarketCache()
        self.providers = provider_manager or ProviderManager()
        self._order_book_runtime_cache: dict[str, OrderBook] = {}

    def get_quotes(self, symbols: Iterable[str], force_refresh: bool = False) -> list[Quote]:
        requested = [normalize_symbol(s) for s in symbols]
        cached: dict[str, Quote] = {}
        missing: list[str] = []

        if not force_refresh:
            for s in requested:
                q = self.cache.get_quote(s, max_age_seconds=QUOTE_CACHE_SECONDS)
                if q is not None:
                    cached[s] = q
                else:
                    missing.append(s)
        else:
            missing = list(requested)

        fresh: dict[str, Quote] = {}
        if missing:
            quotes = self.providers.get_quotes(missing)
            self.cache.save_quotes(quotes)
            fresh = {q.symbol: q for q in quotes}

        result: list[Quote] = []
        for s in requested:
            if s in fresh:
                result.append(fresh[s])
            elif s in cached:
                result.append(cached[s])
            else:
                # 最后尝试读取任意年龄缓存，避免网络短暂失败时前端完全无数据。
                old = self.cache.get_quote(s, max_age_seconds=None)
                if old:
                    result.append(old)
        return result

    def get_quote(self, symbol: str, force_refresh: bool = False) -> Quote:
        symbol = normalize_symbol(symbol)
        quotes = self.get_quotes([symbol], force_refresh=force_refresh)
        if quotes:
            return quotes[0]
        # 网络失败或公开源限流时，优先从任意年龄缓存读取，避免 /api/detail 直接报错导致图表空白。
        old = self.cache.get_quote(symbol, max_age_seconds=None)
        if old:
            return old
        # 最后用最近一根日K构造快照行情，至少保证K线详情页面可以打开。
        bars = self.cache.get_bars(symbol, "1d", limit=1, max_age_seconds=None)
        if bars:
            b = bars[-1]
            return Quote(
                symbol=symbol,
                name=symbol,
                ts=b.ts,
                last=b.close,
                pre_close=b.open,
                open=b.open,
                high=b.high,
                low=b.low,
                volume=b.volume,
                amount=b.amount,
                change=b.close - b.open,
                change_pct=b.change_pct,
                turnover=b.turnover,
                source="bar_snapshot",
            )
        raise RuntimeError(f"无法获取行情: {symbol}")

    def enrich_quote_metrics(self, quote: Quote, force_refresh: bool = False, bars: list[Bar] | None = None) -> Quote:
        """统一补齐筛选主流程需要的实时行情/估值/市值字段。

        custom_input、榜单池、技术初筛和 ETF 观察池都会走这里。公开源仍可能缺字段，
        所以返回值同时携带 metric_missing_reasons，前端可以展示明确缺失来源。
        """
        if quote is None:
            return quote

        def num(value):
            try:
                if value is None:
                    return None
                v = float(value)
                return v if v == v else None
            except Exception:
                return None

        q = quote
        missing_core = any(
            getattr(q, field, None) is None
            for field in ["turnover", "volume_ratio", "pe_dynamic", "pb", "total_market_cap", "float_market_cap"]
        )
        if missing_core or force_refresh:
            try:
                fresh = self.providers.get_quote(q.symbol)
                merged = {}
                for field in [
                    "name", "last", "pre_close", "open", "high", "low", "volume", "amount",
                    "change", "change_pct", "turnover", "amplitude", "pe_dynamic", "pb",
                    "volume_ratio", "total_market_cap", "float_market_cap", "asset_type",
                    "market", "source",
                ]:
                    value = getattr(fresh, field, None)
                    current = getattr(q, field, None)
                    if value not in (None, "", 0) or current in (None, "", 0):
                        merged[field] = value
                q = replace(q, **merged)
            except Exception:
                pass
        # ProviderManager returns the first source that has a quote. During closed
        # sessions Sina can return a usable price snapshot without valuation fields,
        # so explicitly ask EastMoney once when PE/PB/cap are still missing.
        valuation_missing = any(
            getattr(q, field, None) in (None, 0, "")
            for field in ["pe_dynamic", "pb", "total_market_cap", "float_market_cap"]
        )
        if valuation_missing and str(q.source or "") != "unit":
            for provider in getattr(self.providers, "providers", []):
                if getattr(provider, "name", "") != "eastmoney":
                    continue
                direct_supplement = getattr(provider, "_supplement_quote_metrics", None)
                if callable(direct_supplement):
                    try:
                        q2 = direct_supplement(q)
                        if q2 is not q and not any(getattr(q2, field, None) in (None, 0, "") for field in ["pe_dynamic", "pb", "total_market_cap", "float_market_cap"]):
                            q = q2
                            break
                        q = q2
                    except Exception:
                        pass
                try:
                    extras = provider.get_quotes([q.symbol])
                    fresh = extras[0] if extras else None
                except Exception:
                    fresh = None
                if not fresh:
                    continue
                merged = {}
                for field in [
                    "pe_dynamic", "pb", "total_market_cap", "float_market_cap",
                    "circulating_market_cap", "total_share", "float_share",
                    "turnover", "volume_ratio", "amount",
                ]:
                    current = getattr(q, field, None)
                    value = getattr(fresh, field, None)
                    if current in (None, 0, "") and value not in (None, 0, ""):
                        merged[field] = value
                if merged:
                    metric_sources = dict(q.metric_sources or {})
                    for field in merged:
                        metric_sources.setdefault(
                            "pe_ttm" if field == "pe_dynamic" else field,
                            "eastmoney_quote_fallback",
                        )
                    merged["metric_sources"] = metric_sources
                    merged["source"] = f"{q.source}+eastmoney_quote" if q.source else "eastmoney_quote"
                    q = replace(q, **merged)
                break

        bars = bars or []
        if q.amount in (None, 0) and bars:
            amount = num(bars[-1].amount)
            if amount:
                q = replace(q, amount=amount)
        if q.turnover is None and bars:
            turnover = next((num(b.turnover) for b in reversed(bars) if num(b.turnover) is not None), None)
            if turnover is not None:
                q = replace(q, turnover=turnover)
        if q.volume_ratio is None and bars and len(bars) >= 21:
            vols = [num(b.volume) or 0.0 for b in bars]
            ma20 = sum(vols[-21:-1]) / 20 if len(vols) >= 21 else 0.0
            if ma20 > 0:
                q = replace(q, volume_ratio=(num(q.volume) or vols[-1]) / ma20)

        last = num(q.last)
        total_cap = num(q.total_market_cap)
        float_cap = num(q.float_market_cap)
        circulating_cap = num(q.circulating_market_cap) or float_cap
        total_share = num(q.total_share)
        float_share = num(q.float_share)
        if last and last > 0:
            if total_cap and not total_share:
                total_share = total_cap / last
            if float_cap and not float_share:
                float_share = float_cap / last
        reasons: list[str] = []
        metric_sources = dict(q.metric_sources or {})
        for field, value in {
            "turnover_rate": q.turnover,
            "volume_ratio": q.volume_ratio,
            "amount": q.amount,
            "pe_ttm": q.pe_dynamic,
            "pb": q.pb,
            "total_market_cap": q.total_market_cap,
            "float_market_cap": q.float_market_cap,
            "total_share": total_share,
            "float_share": float_share,
        }.items():
            if value not in (None, 0, ""):
                metric_sources.setdefault(field, q.source or "quote_snapshot")

        def cap_style(cap):
            v = num(cap)
            if v is None or v <= 0:
                return None
            if v < 5_000_000_000:
                return "\u5fae\u76d8"
            if v < 20_000_000_000:
                return "\u5c0f\u76d8"
            if v < 100_000_000_000:
                return "\u4e2d\u76d8"
            if v < 500_000_000_000:
                return "\u5927\u76d8"
            return "\u8d85\u5927\u76d8"


        raw_style = str(q.market_cap_style or "").strip()
        market_cap_style = (q.market_cap_style if raw_style and raw_style not in {"未知", "鏈煡", "--", "-"} else None) or cap_style(float_cap or total_cap)
        is_etf = q.asset_type == AssetType.ETF or str(q.symbol).startswith(("15", "51", "56", "58"))
        if is_etf:
            if q.pe_dynamic is None:
                reasons.append("ETF不适用 PE")
            if q.pb is None:
                reasons.append("ETF不适用 PB")
        else:
            if q.pe_dynamic is None:
                reasons.append("行情源缺失 PE")
            if q.pb is None:
                reasons.append("行情源缺失 PB")
        if q.turnover is None:
            reasons.append("行情源缺失换手率")
        if q.volume_ratio is None:
            reasons.append("行情源缺失量比")
        if q.amount in (None, 0):
            reasons.append("行情源缺失成交额")
        if total_cap is None:
            reasons.append("东方财富 push2 未返回总市值")
        if float_cap is None:
            reasons.append("东方财富 push2 未返回流通市值")

        return replace(
            q,
            circulating_market_cap=circulating_cap,
            total_share=total_share,
            float_share=float_share,
            market_cap_style=market_cap_style,
            metric_sources=metric_sources,
            metric_missing_reasons=list(dict.fromkeys(reasons)),
        )

    def get_kline(self, symbol: str, frame: str = "1d", limit: int = 240, adjust: str = "qfq", force_refresh: bool = False) -> list[Bar]:
        symbol = normalize_symbol(symbol)
        frame = "1M" if frame == "1mo" else frame
        adjust_norm = str(adjust or "none").lower()
        if adjust_norm not in {"none", "qfq", "hfq"}:
            adjust_norm = "qfq"
        # 日线不同复权口径不能共用同一缓存，否则“高位回撤/低位位置”会被除权缺口污染。
        # 兼容旧版：不复权仍写入原 1d；前/后复权写入 1d:qfq / 1d:hfq。
        cache_frame = frame
        if frame == "1d" and adjust_norm not in {"none", ""}:
            cache_frame = f"{frame}:{adjust_norm}"

        def _restore_frame(items: list[Bar]) -> list[Bar]:
            if cache_frame == frame:
                return items
            return [replace(b, frame=frame) for b in items]

        cache_seconds = DAILY_KLINE_CACHE_SECONDS if frame == "1d" else MINUTE_KLINE_CACHE_SECONDS
        cached_any = _restore_frame(self.cache.get_bars(symbol, cache_frame, limit=limit, max_age_seconds=None))
        if not force_refresh:
            bars = _restore_frame(self.cache.get_bars(symbol, cache_frame, limit=limit, max_age_seconds=cache_seconds))
            if len(bars) >= min(limit, 30):
                return bars[-limit:]
        try:
            bars = self.providers.get_kline(symbol, frame=frame, limit=limit, adjust=adjust_norm)
            if bars:
                to_save = bars if cache_frame == frame else [replace(b, frame=cache_frame, source=f"{b.source}|{adjust_norm}") for b in bars]
                self.cache.save_bars(to_save)
                return bars[-limit:]
        except Exception:
            # 外部公开K线源短暂返回空/限流时，优先保留同复权口径旧缓存，避免UI和筛选页突然空白。
            if cached_any:
                return cached_any[-limit:]
            # 若请求复权数据失败，再只读旧版不复权缓存兜底，但不把它伪装成复权数据。
            legacy_any = self.cache.get_bars(symbol, frame, limit=limit, max_age_seconds=None) if cache_frame != frame else []
            if legacy_any:
                return [replace(b, source=f"{b.source}|unadjusted_fallback_for_{adjust_norm}") for b in legacy_any[-limit:]]
            raise
        if cached_any:
            return cached_any[-limit:]
        legacy_any = self.cache.get_bars(symbol, frame, limit=limit, max_age_seconds=None) if cache_frame != frame else []
        if legacy_any:
            return [replace(b, source=f"{b.source}|unadjusted_fallback_for_{adjust_norm}") for b in legacy_any[-limit:]]
        # UI兜底：若历史K线完全不可用，但实时行情可用，至少返回一根快照K线，
        # 避免详情页全空。筛选模块仍会因K线数量不足而跳过评分。
        try:
            q = self.get_quote(symbol, force_refresh=False)
            if q and q.last:
                snap = Bar(
                    symbol=symbol,
                    frame=frame,
                    ts=datetime.now(),
                    open=q.open or q.last,
                    high=max(q.high or q.last, q.last),
                    low=min(x for x in [q.low or q.last, q.last] if x and x > 0),
                    close=q.last,
                    volume=q.volume or 0.0,
                    amount=q.amount or 0.0,
                    turnover=q.turnover,
                    change_pct=q.change_pct,
                    source="quote_snapshot",
                )
                return [snap]
        except Exception:
            pass
        return []


    def _intraday_from_minute_bars(self, symbol: str) -> list[IntradayPoint]:
        """用分钟K线还原分时走势。

        休市后 trends 分时接口可能返回空；这里继续尝试多源 1m/5m K线。
        只有拿到真实分钟K线时才绘图，不用行情快照伪造分时线。
        """
        bars: list[Bar] = []
        # 先走统一 K线接口，里面会依次尝试东方财富、Sina、Tencent/AKShare。
        for frame, lim in [("1m", 360), ("5m", 120)]:
            for force in (False, True):
                try:
                    candidate = self.get_kline(symbol, frame=frame, limit=lim, adjust="none", force_refresh=force)
                except Exception:
                    candidate = []
                # 排除 quote_snapshot 这类单点伪K线。
                candidate = [b for b in candidate if b.close > 0 and b.source not in {"quote_snapshot", "bar_snapshot"}]
                if len(candidate) >= 2:
                    bars = candidate
                    break
            if bars:
                break

        if not bars:
            return []
        # 仅取最后一个交易日，避免跨日连在一起。
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
            cum_volume += vol
            cum_amount += amt
            avg = None
            if cum_volume > 0 and cum_amount > 0:
                # 不同分钟源 volume 单位可能不同；均价异常时舍弃均价线，仅保留价格线。
                avg = cum_amount / max(cum_volume * 100.0, 1.0)
                if avg > b.high * 10 or avg < b.low / 10:
                    avg = None
            points.append(IntradayPoint(
                symbol=symbol,
                ts=b.ts,
                price=float(b.close or 0.0),
                avg_price=avg if avg and avg > 0 else None,
                volume=vol,
                amount=amt,
                source=f"{b.source}_intraday_rebuild",
            ))
        return [p for p in points if p.price > 0]

    def _normalize_intraday_flow(self, points: list[IntradayPoint]) -> list[IntradayPoint]:
        """把部分公开分时源返回的累计成交量/成交额转换成单分钟增量。

        东方财富 / 腾讯等分时接口字段会在不同时间返回“累计量”或“本分钟量”。
        前端副图需要的是每分钟柱，否则就会出现成交量一路直线上涨的假象。
        这里按单日分组，只在绝大多数点单调递增时才做差分，避免误伤真实分钟量。
        """
        if len(points) < 3:
            return points

        def should_diff(vals: list[float | None]) -> bool:
            nums = [float(v or 0.0) for v in vals]
            if len(nums) < 6 or nums[-1] <= 0:
                return False
            diffs = [nums[i] - nums[i - 1] for i in range(1, len(nums))]
            tol = max(1.0, nums[-1] * 1e-7)
            non_dec = sum(1 for d in diffs if d >= -tol) / max(1, len(diffs))
            pos_diffs = [d for d in diffs if d > tol]
            if not pos_diffs:
                return False
            median_diff = sorted(pos_diffs)[len(pos_diffs) // 2]
            # 累计字段通常最后一个值远大于单分钟差分；真实分钟量则频繁上下波动。
            return non_dec >= 0.88 and nums[-1] >= max(median_diff * 4, 1.0)

        def diffed(vals: list[float | None]) -> list[float | None]:
            nums = [float(v or 0.0) for v in vals]
            out: list[float | None] = []
            for i, v in enumerate(nums):
                if i == 0:
                    out.append(max(v, 0.0))
                else:
                    out.append(max(v - nums[i - 1], 0.0))
            return out

        grouped: dict[str, list[IntradayPoint]] = {}
        for p in sorted(points, key=lambda x: x.ts):
            grouped.setdefault(p.ts.date().isoformat(), []).append(p)

        normalized: list[IntradayPoint] = []
        for _, group in grouped.items():
            vols = [p.volume for p in group]
            amts = [p.amount for p in group]
            conv_vol = should_diff(vols)
            conv_amt = should_diff(amts)
            new_vols = diffed(vols) if conv_vol else vols
            new_amts = diffed(amts) if conv_amt else amts
            for p, v, a in zip(group, new_vols, new_amts):
                src = p.source
                if conv_vol or conv_amt:
                    src = f"{src}_flowdiff"
                normalized.append(replace(p, volume=v, amount=a, source=src))
        return normalized

    def get_intraday(self, symbol: str, force_refresh: bool = False) -> list[IntradayPoint]:
        """获取当日/最近交易日分时，并对休市、接口波动做本地缓存和1mK线兜底。

        优先级：
        1. 未强刷且缓存足够完整：直接返回缓存；
        2. trends 分时接口返回足够完整数据：保存并返回；
        3. trends 为空但有旧缓存：返回旧缓存；
        4. 无缓存时用 1分钟K线还原最近交易日分时。
        """
        symbol = normalize_symbol(symbol)
        cached = self._normalize_intraday_flow(self.cache.get_intraday(symbol))
        if not force_refresh and len(cached) >= 30:
            return cached

        fresh: list[IntradayPoint] = []
        try:
            fresh = self.providers.get_intraday(symbol)
        except Exception:
            fresh = []

        if len(fresh) >= 2:
            fresh = self._normalize_intraday_flow(fresh)
            if self._intraday_looks_incomplete(fresh):
                rebuilt = self._normalize_intraday_flow(self._intraday_from_minute_bars(symbol))
                if self._intraday_is_better(rebuilt, fresh):
                    fresh = rebuilt
                elif self._intraday_is_better(cached, fresh):
                    return cached
            if len(cached) >= 30 and len(fresh) < max(10, int(len(cached) * 0.35)):
                return cached
            self.cache.save_intraday(fresh)
            return fresh

        if cached:
            return cached

        rebuilt = self._normalize_intraday_flow(self._intraday_from_minute_bars(symbol))
        if len(rebuilt) >= 2:
            self.cache.save_intraday(rebuilt)
            return rebuilt
        return []

    @staticmethod
    def _intraday_minutes(points: list[IntradayPoint]) -> int:
        if not points:
            return -1
        try:
            last = max(p.ts for p in points)
            return last.hour * 60 + last.minute
        except Exception:
            return -1

    def _intraday_looks_incomplete(self, points: list[IntradayPoint]) -> bool:
        if len(points) < 2:
            return True
        last_minute = self._intraday_minutes(points)
        # A normal CN full-day minute series should reach the late afternoon.
        # If a closed-session refresh only returns morning data, do not overwrite
        # a better cache with that half-day snapshot.
        return len(points) < 180 or (0 <= last_minute < 14 * 60 + 45)

    def _intraday_is_better(self, candidate: list[IntradayPoint], current: list[IntradayPoint]) -> bool:
        if len(candidate) < 2:
            return False
        if len(current) < 2:
            return True
        try:
            cand_date = max(p.ts for p in candidate).date()
            cur_date = max(p.ts for p in current).date()
            if cand_date != cur_date:
                return cand_date > cur_date
        except Exception:
            pass
        cand_last = self._intraday_minutes(candidate)
        cur_last = self._intraday_minutes(current)
        return cand_last > cur_last or len(candidate) >= max(len(current) + 30, int(len(current) * 1.25))


    def get_order_book(self, symbol: str, allow_external: bool = True) -> OrderBook | None:
        symbol = normalize_symbol(symbol)
        if not allow_external:
            # 休市/午休/非交易日时只返回本次运行期间最后一次成功盘口，
            # 不主动访问外部盘口接口，避免无意义超时和控制台噪声。
            return self._order_book_runtime_cache.get(symbol)
        try:
            book = self.providers.get_order_book(symbol)
            if book and (book.asks or book.bids):
                self._order_book_runtime_cache[symbol] = book
                return book
        except Exception:
            pass
        # 公共盘口接口在休市、网络波动、限流时很容易失败；优先返回本次运行期间最后一次成功盘口。
        return self._order_book_runtime_cache.get(symbol)

    def get_market_snapshot(self, page: int = 1, page_size: int = 100, save_assets: bool = True) -> list[Quote]:
        quotes = self.providers.get_spot_list(page=page, page_size=page_size)
        self.cache.save_quotes(quotes)
        if save_assets:
            self.cache.save_assets(
                Asset(symbol=q.symbol, name=q.name, asset_type=q.asset_type, market=q.market, source=q.source) for q in quotes
            )
        return quotes

    def search_assets(self, keyword: str, limit: int = 30) -> list[Asset]:
        assets = self.cache.search_assets(keyword, limit=limit)
        if assets:
            return assets
        assets = self.providers.search_assets(keyword, limit=limit)
        self.cache.save_assets(assets)
        return assets

    def export_bars_csv(self, symbol: str, frame: str, bars: list[Bar], output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "frame", "ts", "open", "high", "low", "close", "volume", "amount", "turnover", "change_pct", "source"])
            writer.writeheader()
            for b in bars:
                writer.writerow(b.to_dict())
        return path
