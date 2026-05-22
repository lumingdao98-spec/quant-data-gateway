from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DB = Path(os.environ.get("QUANT_CACHE_DB", str(DATA_DIR / "market_cache.sqlite")))
HTTP_TIMEOUT = float(os.environ.get("QUANT_HTTP_TIMEOUT", "8"))

# 公共网页接口要低频使用，避免给目标站点造成压力，也降低封锁风险。
MIN_REQUEST_INTERVAL = float(os.environ.get("QUANT_MIN_REQUEST_INTERVAL", "0.8"))
QUOTE_CACHE_SECONDS = float(os.environ.get("QUANT_QUOTE_CACHE_SECONDS", "3"))
MINUTE_KLINE_CACHE_SECONDS = float(os.environ.get("QUANT_MINUTE_KLINE_CACHE_SECONDS", "20"))
DAILY_KLINE_CACHE_SECONDS = float(os.environ.get("QUANT_DAILY_KLINE_CACHE_SECONDS", "3600"))

DISABLE_PROXY = os.environ.get("QUANT_DISABLE_PROXY", "0") == "1"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://quote.eastmoney.com/",
}
