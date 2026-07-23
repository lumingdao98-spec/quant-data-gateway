from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from quant_data.models import Bar, IntradayPoint, Quote

from .market_event_factor_service import MarketEventFactorService


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "--"):
            return None
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return dict(getattr(value, "__dict__", {}) or {})


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    raw = str(value or "").strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


class RealtimeDecisionService:
    """Build a cache-only realtime decision payload.

    The browser must not be the source of truth for trading scores. This service
    combines the saved screener baseline with cached daily bars, today's
    intraday path, an actual quote/order-book snapshot and recent dated news.
    It deliberately performs no network I/O; a missing input stays missing.
    """

    def __init__(
        self,
        market_data: Any,
        cache_state: Any,
        market_regime: Any,
        market_event_factors: MarketEventFactorService | None = None,
    ) -> None:
        self.market_data = market_data
        self.cache_state = cache_state
        self.market_regime = market_regime
        self.market_event_factors = market_event_factors or MarketEventFactorService(cache_state)

    def hydrate(
        self,
        payload: dict[str, Any] | None,
        *,
        profile: dict[str, Any] | None = None,
        symbols: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        out = dict(payload or {})
        profile = dict(profile or {})
        symbol = str(out.get("symbol") or profile.get("symbol") or "").strip()
        if not symbol:
            return out

        quote = _dict(out.get("quote"))
        bars = self._daily_bars(symbol)
        intraday = self._intraday_points(symbol, quote)

        daily = self._daily_score(bars)
        daily_score = daily.get("score")
        if daily_score is None:
            daily_score = _number(profile.get("technical_score"))
            daily["source"] = "筛选快照技术分兜底" if daily_score is not None else "日K缓存缺失"

        intraday_result = self._intraday_score(quote, intraday)
        intraday_score = intraday_result.get("score")
        technical_parts = [(daily_score, 0.55), (intraday_score, 0.45)]
        usable_technical = [(value, weight) for value, weight in technical_parts if value is not None]
        technical_score = None
        if usable_technical:
            total_weight = sum(weight for _, weight in usable_technical) or 1.0
            technical_score = sum(float(value) * weight for value, weight in usable_technical) / total_weight

        flow = self._fund_flow_score(quote, intraday)
        profile_flow = _number(profile.get("fund_flow_score"))
        live_flow = flow.get("score")
        fund_flow_score = None
        if live_flow is not None and profile_flow is not None:
            fund_flow_score = profile_flow * 0.35 + live_flow * 0.65
        else:
            fund_flow_score = live_flow if live_flow is not None else profile_flow

        info = self._recent_information(symbol, profile)
        market = self._market_score(symbols or [], profile)
        event_context = self.market_event_factors.build_context(
            symbol=symbol,
            name=str(out.get("name") or profile.get("name") or symbol),
            profile=profile,
        )
        adjusted = self.market_event_factors.apply_scores(
            event_context,
            market_score=_number(market.get("score")),
            information_score=_number(info.get("score")),
        )
        info["base_score"] = info.get("score")
        info["score"] = adjusted.get("information_score")
        info["event_adjustment"] = adjusted.get("information_adjustment")
        market["base_score"] = market.get("score")
        market["score"] = adjusted.get("market_score")
        market["event_adjustment"] = adjusted.get("market_adjustment")
        market["event_factors"] = [row for row in event_context.get("factors", []) if row.get("scope") == "市场环境"]

        screening_score = _number(profile.get("final_score"))
        if screening_score is None:
            screening_score = _number(out.get("screening_score"))
        out.update(
            {
                "screening_score": screening_score,
                "daily_k_score": round(daily_score, 4) if daily_score is not None else None,
                "intraday_score": round(intraday_score, 4) if intraday_score is not None else None,
                "technical_score": round(technical_score, 4) if technical_score is not None else None,
                "fundamental_score": _number(profile.get("fundamental_score"))
                if out.get("fundamental_score") in (None, "", "--")
                else _number(out.get("fundamental_score")),
                "information_score": info.get("score"),
                "fund_flow_score": round(fund_flow_score, 4) if fund_flow_score is not None else None,
                "market_score": market.get("score"),
                "score_source": "server_cache_realtime_decision_v323",
                "daily_k_ts": daily.get("latest_at"),
                "intraday_ts": intraday_result.get("latest_at") or out.get("intraday_ts"),
                "info_snapshot_ts": info.get("snapshot_at"),
                "news_ts": info.get("latest_published_at"),
                "recent_information": info,
                "market_regime": market,
                "market_event_context": event_context,
                "orderbook_snapshot": self._orderbook_summary(quote),
            }
        )

        if info.get("negative_veto") or event_context.get("negative_veto"):
            out["info_negative_veto"] = True
            out["major_negative_news"] = True

        missing = list(out.get("missing_data") or [])
        for key, value in (
            ("daily_k_cache_missing", daily_score),
            ("intraday_cache_missing", intraday_score),
            ("recent_information_missing", info.get("has_recent")),
            ("orderbook_missing", self._best_price(quote, "bid")),
        ):
            if value is None or value is False:
                missing.append(key)
        out["missing_data"] = list(dict.fromkeys(missing))

        existing = dict(out.get("score_breakdown") or {})
        existing_sources = dict(existing.get("sources") or {})
        existing_sources.update(
            {
                "screening": profile.get("source") or "筛选快照",
                "daily_k": daily.get("source"),
                "intraday": intraday_result.get("source"),
                "information": info.get("source"),
                "fund_flow": flow.get("source"),
                "market": market.get("source"),
                "market_events": "全球要闻/IPO/板块真实缓存",
            }
        )
        existing.update(
            {
                "screening_score": screening_score,
                "daily_k_score": out.get("daily_k_score"),
                "intraday_score": out.get("intraday_score"),
                "timing_score": out.get("technical_score"),
                "technical_score": out.get("technical_score"),
                "information_score": out.get("information_score"),
                "fund_flow_score": out.get("fund_flow_score"),
                "market_score": out.get("market_score"),
                "formula": "综合交易分=筛选底座+实时择时（日K55%+分时45%）+近期信息+资金+大盘-异常风险",
                "sources": existing_sources,
                "recent_information_count": info.get("recent_count", 0),
                "recent_information_latest": info.get("latest_published_at"),
                "excluded_information_count": info.get("excluded_count", 0),
                "market_event_adjustment": adjusted.get("market_adjustment"),
                "information_event_adjustment": adjusted.get("information_adjustment"),
                "event_factor_count": event_context.get("factor_count", 0),
                "event_factors": event_context.get("factors", []),
            }
        )
        out["score_breakdown"] = existing

        evidence = list(out.get("evidence") or [])
        evidence.extend(
            [
                f"服务端实时择时：日K {self._display(daily_score)} / 分时 {self._display(intraday_score)}",
                f"近期信息：{info.get('recent_count', 0)} 条，历史/无日期排除 {info.get('excluded_count', 0)} 条",
                f"盘口：{self._display(self._best_price(quote, 'bid'))} / {self._display(self._best_price(quote, 'ask'))}，来源 {quote.get('orderbook_source') or '缺失'}",
                f"市场事件调整：大盘 {adjusted.get('market_adjustment', 0):+.2f} / 个股信息 {adjusted.get('information_adjustment', 0):+.2f}，证据 {event_context.get('factor_count', 0)} 项",
            ]
        )
        evidence.extend(event_context.get("evidence") or [])
        out["evidence"] = list(dict.fromkeys(evidence))
        return out

    def _daily_bars(self, symbol: str) -> list[Bar]:
        cache = getattr(self.market_data, "cache", None)
        if cache is None:
            return []
        for frame in ("1d:qfq", "1d"):
            try:
                bars = cache.get_bars(symbol, frame, limit=90, max_age_seconds=None)
            except Exception:
                bars = []
            if len(bars) >= 20:
                return list(bars)
        return []

    def _intraday_points(self, symbol: str, quote: dict[str, Any]) -> list[IntradayPoint]:
        cache = getattr(self.market_data, "cache", None)
        if cache is None:
            return []
        try:
            points = list(cache.get_intraday(symbol) or [])
        except Exception:
            return []
        if not points:
            return []
        quote_time = _parse_time(quote.get("ts") or quote.get("fetched_at"))
        point_time = _parse_time(getattr(points[-1], "ts", None))
        if quote_time and point_time and quote_time.date() != point_time.date():
            return []
        return points

    def _daily_score(self, bars: list[Bar]) -> dict[str, Any]:
        closes = [_number(getattr(bar, "close", None)) for bar in bars]
        closes = [value for value in closes if value and value > 0]
        if len(closes) < 20:
            return {"score": None, "source": "日K缓存缺失", "bar_count": len(closes)}
        last = closes[-1]
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else None
        ret5 = (last / closes[-6] - 1) * 100 if len(closes) >= 6 and closes[-6] else 0.0
        ret20 = (last / closes[-20] - 1) * 100 if closes[-20] else 0.0
        score = 50.0
        score += max(-12.0, min(12.0, ret5 * 1.9))
        score += max(-10.0, min(10.0, ret20 * 0.75))
        score += 7.0 if ma5 > ma20 else -7.0
        score += max(-9.0, min(9.0, (last / ma20 - 1) * 100 * 1.6)) if ma20 else 0.0
        if ma60:
            score += 6.0 if ma20 > ma60 else -6.0
            score += max(-6.0, min(6.0, (last / ma60 - 1) * 100 * 0.6))
        volumes = [_number(getattr(bar, "volume", None)) or 0.0 for bar in bars]
        if len(volumes) >= 21:
            avg20 = sum(volumes[-21:-1]) / 20
            if avg20 > 0:
                ratio = volumes[-1] / avg20
                score += max(-4.0, min(5.0, (ratio - 1.0) * (3.0 if ret5 >= 0 else -3.0)))
        latest_at = getattr(bars[-1], "ts", None)
        return {
            "score": round(_clamp(score), 2),
            "source": f"本地日K缓存/{getattr(bars[-1], 'source', 'cache')}",
            "latest_at": latest_at.isoformat(timespec="seconds") if isinstance(latest_at, datetime) else str(latest_at or ""),
            "bar_count": len(closes),
            "ret5_pct": round(ret5, 2),
            "ret20_pct": round(ret20, 2),
        }

    def _intraday_score(self, quote: dict[str, Any], points: list[IntradayPoint]) -> dict[str, Any]:
        last = _number(quote.get("last") or quote.get("price"))
        if last is None:
            return {"score": None, "source": "实时行情缺失"}
        change_pct = _number(quote.get("change_pct"))
        open_price = _number(quote.get("open"))
        high = _number(quote.get("high"))
        low = _number(quote.get("low"))
        volume_ratio = _number(quote.get("volume_ratio"))
        score = 50.0
        score += max(-16.0, min(16.0, (change_pct or 0.0) * 3.0))
        if open_price and open_price > 0:
            score += max(-8.0, min(8.0, (last / open_price - 1) * 100 * 1.5))
        if high is not None and low is not None and high > low:
            score += ((last - low) / (high - low) - 0.5) * 16.0
        if volume_ratio is not None:
            pulse = max(-5.0, min(8.0, (volume_ratio - 1.0) * 5.0))
            score += pulse if (change_pct or 0.0) >= 0 else -abs(pulse) * 0.7

        prices = [_number(getattr(point, "price", None)) for point in points]
        prices = [value for value in prices if value and value > 0]
        latest_at = None
        if points:
            latest = getattr(points[-1], "ts", None)
            latest_at = latest.isoformat(timespec="seconds") if isinstance(latest, datetime) else str(latest or "")
        if len(prices) >= 6:
            ret5 = (prices[-1] / prices[-6] - 1) * 100 if prices[-6] else 0.0
            score += max(-9.0, min(9.0, ret5 * 7.0))
        if len(prices) >= 16:
            ret15 = (prices[-1] / prices[-16] - 1) * 100 if prices[-16] else 0.0
            score += max(-8.0, min(8.0, ret15 * 4.0))
        avg_price = None
        if points:
            avg_price = _number(getattr(points[-1], "avg_price", None))
        if avg_price and avg_price > 0:
            score += max(-8.0, min(8.0, (last / avg_price - 1) * 100 * 4.0))

        bid = self._best_price(quote, "bid")
        ask = self._best_price(quote, "ask")
        imbalance = _number(quote.get("order_ratio"))
        if imbalance is not None:
            score += max(-5.0, min(5.0, imbalance / 20.0))
        if bid and ask and ask >= bid:
            spread_pct = (ask - bid) / max(last, 1e-9) * 100
            score -= min(4.0, spread_pct * 12.0)
        return {
            "score": round(_clamp(score), 2),
            "source": f"实时行情+当日分时缓存/{quote.get('source') or 'unknown'}",
            "latest_at": latest_at or str(quote.get("ts") or ""),
            "point_count": len(points),
        }

    def _fund_flow_score(self, quote: dict[str, Any], points: list[IntradayPoint]) -> dict[str, Any]:
        change = _number(quote.get("change_pct")) or 0.0
        volume_ratio = _number(quote.get("volume_ratio"))
        turnover = _number(quote.get("turnover") or quote.get("turnover_rate"))
        order_ratio = _number(quote.get("order_ratio"))
        score = 50.0 + max(-12.0, min(12.0, change * 2.5))
        if volume_ratio is not None:
            pulse = max(-8.0, min(10.0, (volume_ratio - 1.0) * 6.0))
            score += pulse if change >= 0 else -abs(pulse)
        if turnover is not None:
            score += min(6.0, max(0.0, turnover) * 0.45)
        if order_ratio is not None:
            score += max(-7.0, min(7.0, order_ratio / 14.0))
        amounts = [_number(getattr(point, "amount", None)) for point in points]
        amounts = [value for value in amounts if value is not None and value >= 0]
        if len(amounts) >= 12:
            recent = sum(amounts[-5:]) / 5
            prior = sum(amounts[-12:-5]) / 7
            if prior > 0:
                score += max(-5.0, min(5.0, (recent / prior - 1.0) * 4.0))
        return {"score": round(_clamp(score), 2), "source": "真实量价/盘口快照（非主力资金伪估算）"}

    def _market_score(self, symbols: Iterable[str], profile: dict[str, Any]) -> dict[str, Any]:
        quotes: list[Quote] = []
        cache = getattr(self.market_data, "cache", None)
        for symbol in list(dict.fromkeys(str(item).strip() for item in symbols if str(item).strip()))[:80]:
            if cache is None:
                break
            try:
                quote = cache.get_quote(symbol, max_age_seconds=None)
            except Exception:
                quote = None
            if quote is not None:
                quotes.append(quote)
        live = self.market_regime.analyze_market(quotes, index_bars={}) if quotes else {}
        live_score = _number(live.get("score")) if quotes else None
        baseline = _number(profile.get("market_score"))
        if live_score is not None and baseline is not None:
            score = baseline * 0.55 + live_score * 0.45
        else:
            score = live_score if live_score is not None else baseline
        return {
            "score": round(score, 2) if score is not None else None,
            "source": "股票池缓存宽度+筛选大盘底座" if quotes else "筛选大盘底座/指数缓存缺失",
            "sample_count": len(quotes),
            "confidence": live.get("confidence") if quotes else "low",
            "regime": live.get("regime") if quotes else "unknown",
            "basis": live.get("basis") if quotes else "没有可用实时指数/宽度快照，未伪造大盘分。",
        }

    def _recent_information(self, symbol: str, profile: dict[str, Any]) -> dict[str, Any]:
        try:
            cached = self.cache_state.latest_info_snapshot(symbol)
            data = dict(cached.data or {})
            cache_status = dict(cached.cache_status or {})
        except Exception:
            data, cache_status = {}, {"status": "error", "stale": True}
        items: list[tuple[str, dict[str, Any]]] = []
        for bucket_name, bucket in (
            ("items", data.get("items")),
            ("news", (data.get("news") or {}).get("items") if isinstance(data.get("news"), dict) else None),
            ("global", data.get("global_items")),
            ("mapped_global", data.get("industry_mapped_items")),
        ):
            for item in bucket or []:
                if isinstance(item, dict):
                    items.append((bucket_name, dict(item)))
        unique: dict[str, dict[str, Any]] = {}
        recent: list[dict[str, Any]] = []
        excluded = 0
        now = datetime.now()
        global_unmapped_excluded = 0
        for bucket_name, item in items:
            if bucket_name in {"global", "mapped_global"} and not bool(
                item.get("included_in_score") or item.get("score_included") or item.get("is_related_to_symbol")
            ):
                excluded += 1
                global_unmapped_excluded += 1
                continue
            source_type = str(item.get("source_type") or item.get("type") or "news").lower()
            if source_type in {"forum", "community", "search"}:
                excluded += 1
                continue
            published = _parse_time(
                item.get("published_at_norm")
                or item.get("published_at")
                or item.get("publish_time")
                or item.get("date_display")
                or item.get("date")
            )
            if not published:
                excluded += 1
                continue
            age_days = (now - published).days
            max_days = 14 if source_type == "macro" else 90 if source_type == "announcement" else 45 if source_type in {"policy", "research"} else 30
            if age_days < -1 or age_days > max_days:
                excluded += 1
                continue
            title = str(item.get("title") or item.get("summary") or "").strip()
            source = str(item.get("source") or item.get("source_name") or "").strip()
            key = str(item.get("event_key") or item.get("document_id") or f"{source}|{published.date()}|{title[:80]}")
            if key in unique:
                continue
            sentiment_raw = item.get("sentiment_score")
            if sentiment_raw is None:
                sentiment_raw = item.get("score")
            normalized = {
                "title": title,
                "source": source,
                "source_ref": item.get("url") or item.get("source_url") or item.get("source_ref"),
                "published_at": published.isoformat(timespec="seconds"),
                "sentiment_score": _number(sentiment_raw),
                "credibility_score": _number(item.get("credibility_score")) or 50.0,
                "impact_score": _number(item.get("impact_score")) or 50.0,
                "source_type": source_type,
            }
            unique[key] = normalized
            recent.append(normalized)
        recent.sort(key=lambda item: item["published_at"], reverse=True)
        scored = [item for item in recent if item.get("sentiment_score") is not None]
        if scored:
            weighted = []
            for item in scored:
                weight = max(0.25, min(1.5, (item["credibility_score"] / 100.0) * 0.8 + (item["impact_score"] / 100.0) * 0.7))
                weighted.append((float(item["sentiment_score"]), weight))
            score = sum(value * weight for value, weight in weighted) / (sum(weight for _, weight in weighted) or 1.0)
        else:
            quality = data.get("data_quality") or (data.get("news") or {}).get("data_quality") or {}
            current_count = int(_number(quality.get("current_scoring_count")) or 0)
            snapshot_score = self._first_score(data)
            score = snapshot_score if current_count > 0 and snapshot_score is not None else 50.0
        high_conf_negative = [
            item for item in scored
            if float(item.get("sentiment_score") or 50) <= 32 and float(item.get("credibility_score") or 0) >= 80
        ]
        latest = recent[0]["published_at"] if recent else None
        return {
            "score": round(_clamp(score), 2),
            "has_recent": bool(recent),
            "recent_count": len(recent),
            "excluded_count": excluded,
            "global_unmapped_excluded": global_unmapped_excluded,
            "latest_published_at": latest,
            "snapshot_id": data.get("snapshot_id") or cache_status.get("snapshot_id"),
            "snapshot_at": data.get("created_at") or cache_status.get("created_at"),
            "cache_status": cache_status.get("status") or "miss",
            "stale": bool(cache_status.get("stale")),
            "source": "近期可核验信息快照" if recent else "近期可核验信息缺失/中性",
            "negative_veto": bool(high_conf_negative),
            "items": recent[:6],
        }

    def _first_score(self, data: dict[str, Any]) -> float | None:
        news = data.get("news") if isinstance(data.get("news"), dict) else {}
        score_model = data.get("score_model") if isinstance(data.get("score_model"), dict) else {}
        for value in (
            data.get("info_score"),
            data.get("news_score"),
            score_model.get("score"),
            news.get("news_score"),
            news.get("score"),
        ):
            score = _number(value)
            if score is not None:
                return _clamp(score)
        return None

    def _orderbook_summary(self, quote: dict[str, Any]) -> dict[str, Any]:
        bid = self._best_price(quote, "bid")
        ask = self._best_price(quote, "ask")
        last = _number(quote.get("last") or quote.get("price"))
        spread = None
        if bid and ask and ask >= bid:
            spread = ask - bid
        return {
            "bid1": bid,
            "ask1": ask,
            "spread": round(spread, 6) if spread is not None else None,
            "spread_pct": round(spread / last * 100, 4) if spread is not None and last else None,
            "source": quote.get("orderbook_source") or "missing",
            "timestamp": quote.get("orderbook_ts") or quote.get("ts"),
            "status": "available" if bid is not None and ask is not None else "missing",
        }

    def _best_price(self, quote: dict[str, Any], side: str) -> float | None:
        direct = ("bid1", "buy1", "best_bid") if side == "bid" else ("ask1", "sell1", "best_ask")
        for key in direct:
            value = _number(quote.get(key))
            if value is not None and value > 0:
                return value
        levels = quote.get("bids" if side == "bid" else "asks") or []
        if levels and isinstance(levels[0], dict):
            value = _number(levels[0].get("price"))
            return value if value and value > 0 else None
        return None

    @staticmethod
    def _display(value: Any) -> str:
        number = _number(value)
        return "--" if number is None else f"{number:.2f}"
