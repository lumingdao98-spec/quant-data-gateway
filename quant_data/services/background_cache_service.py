from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable

from quant_data.services.cache_state_service import CacheStateService
from quant_data.services.watchlist_service import WatchlistService


class BackgroundCacheService:
    """Small coordinator for cache-first page loading.

    The service intentionally stays light: page APIs still own the actual data
    fetching, while this class centralizes watchlist state and refresh metadata
    so UI pages can render cached content first and refresh in the background.
    """

    def __init__(
        self,
        *,
        cache_state_service: CacheStateService,
        watchlist_service: WatchlistService,
    ) -> None:
        self.cache_state_service = cache_state_service
        self.watchlist_service = watchlist_service
        self.last_started_at: str | None = None
        self.last_finished_at: str | None = None
        self.last_errors: list[str] = []
        self.last_refresh: dict[str, Any] = {}

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def status(self) -> dict[str, Any]:
        watchlist = self.watchlist_service.list()
        return {
            "ok": True,
            "mode": "cache_first_background_refresh",
            "last_started_at": self.last_started_at,
            "last_finished_at": self.last_finished_at,
            "last_errors": self.last_errors[-8:],
            "last_refresh": self.last_refresh,
            "watchlist": watchlist,
            "cache": self.cache_state_service.overview(),
        }

    def refresh_watchlist_quotes(
        self,
        symbols: Iterable[str] | None,
        quote_loader: Callable[[str], tuple[Any, dict[str, Any], dict[str, Any]]],
        *,
        limit: int = 40,
    ) -> dict[str, Any]:
        self.last_started_at = self._now()
        self.last_errors = []
        raw_symbols = list(symbols or self.watchlist_service.list().get("symbols") or [])
        unique_symbols: list[str] = []
        for symbol in raw_symbols:
            s = str(symbol or "").strip()
            if s and s not in unique_symbols:
                unique_symbols.append(s)
        refreshed: list[str] = []
        for symbol in unique_symbols[: max(1, int(limit or 40))]:
            try:
                quote_loader(symbol)
                refreshed.append(symbol)
            except Exception as exc:  # pragma: no cover - defensive path
                self.last_errors.append(f"{symbol}: {str(exc)[:160]}")
        self.last_finished_at = self._now()
        self.last_refresh = {
            "kind": "watchlist_quotes",
            "symbols": unique_symbols,
            "refreshed": refreshed,
            "error_count": len(self.last_errors),
            "non_blocking": True,
        }
        return {"ok": True, **self.last_refresh, "last_errors": self.last_errors[-8:]}

    def mark_refresh(self, kind: str, **extra: Any) -> dict[str, Any]:
        self.last_started_at = self.last_started_at or self._now()
        self.last_finished_at = self._now()
        self.last_refresh = {"kind": kind, "non_blocking": True, **extra}
        return {"ok": True, **self.last_refresh}
