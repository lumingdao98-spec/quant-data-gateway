from __future__ import annotations

import math
import os
import re
import time
from datetime import datetime
from typing import Iterable, Iterator, Sequence, TypeVar

import requests

from quant_data.config import DEFAULT_HEADERS, DISABLE_PROXY, HTTP_TIMEOUT, MIN_REQUEST_INTERVAL

T = TypeVar("T")


def normalize_symbol(symbol: str | int) -> str:
    """标准化 A 股代码，只保留数字并补足 6 位。"""
    s = str(symbol).strip().lower()
    s = s.replace("sh", "").replace("sz", "").replace("bj", "")
    digits = re.sub(r"\D", "", s)
    if not digits:
        raise ValueError(f"无效证券代码: {symbol!r}")
    return digits.zfill(6)[-6:]


def infer_exchange(symbol: str | int) -> str:
    """粗略推断交易所，用于拼接公共接口代码。"""
    code = normalize_symbol(symbol)
    if code.startswith(("600", "601", "603", "605", "688", "689", "900")):
        return "SH"
    if code.startswith(("000", "001", "002", "003", "200", "300", "301", "159", "150", "184")):
        return "SZ"
    if code.startswith(("510", "511", "512", "513", "515", "516", "517", "518", "588", "589")):
        return "SH"
    if code.startswith(("430", "831", "832", "833", "834", "835", "836", "837", "838", "839", "870", "871", "872", "873", "920")):
        return "BJ"
    # 默认按深市尝试，若失败会由 ProviderManager 切换兜底源。
    return "SZ"


def eastmoney_market_id(symbol: str | int) -> int:
    """东方财富 secid 的市场编号。沪市 1，深市/北交所多数接口使用 0。"""
    exchange = infer_exchange(symbol)
    return 1 if exchange == "SH" else 0


def to_eastmoney_secid(symbol: str | int) -> str:
    code = normalize_symbol(symbol)
    return f"{eastmoney_market_id(code)}.{code}"


def to_sina_code(symbol: str | int) -> str:
    code = normalize_symbol(symbol)
    exchange = infer_exchange(code)
    prefix = {"SH": "sh", "SZ": "sz", "BJ": "bj"}.get(exchange, "sz")
    return f"{prefix}{code}"


def safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value in {"", "-", "--", "None", "null"}:
            return default
        value = value.replace(",", "")
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def safe_int(value, default: int = 0) -> int:
    try:
        return int(safe_float(value, float(default)))
    except Exception:
        return default


def chunked(seq: Sequence[T] | Iterable[T], size: int) -> Iterator[list[T]]:
    buf: list[T] = []
    for item in seq:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


class ThrottledSession:
    """带最小请求间隔的 requests.Session 包装。"""

    def __init__(self, min_interval: float = MIN_REQUEST_INTERVAL, timeout: float = HTTP_TIMEOUT) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.trust_env = not DISABLE_PROXY
        self.min_interval = min_interval
        self.timeout = timeout
        self._last_request_time = 0.0

    def get(self, url: str, **kwargs) -> requests.Response:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last_request_time)
        if wait > 0:
            time.sleep(wait)
        timeout = kwargs.pop("timeout", self.timeout)
        resp = self.session.get(url, timeout=timeout, **kwargs)
        self._last_request_time = time.monotonic()
        resp.raise_for_status()
        return resp


def parse_dt(value: str) -> datetime:
    """稳健解析公开行情接口中的日期时间。

    公开接口偶尔会返回带 T、斜杠、点号、中文年月日、纯时间、
    或者 HTML/JSON 片段中的日期。旧版本解析失败时直接使用
    datetime.now()，会导致 K 线横坐标全部变成当天日期。
    这里优先抽取真实日期，只有完全无法识别时才退回当前时间。
    """
    raw = str(value or "").strip()
    if not raw:
        return datetime.now()
    value = raw.replace("T", " ").replace("/", "-").replace(".", "-")
    value = value.replace("年", "-").replace("月", "-").replace("日", "")
    value = re.sub(r"\s+", " ", value).strip()
    # 秒级/毫秒级时间戳
    if re.fullmatch(r"\d{10,13}", value):
        try:
            ts = int(value) / (1000 if len(value) == 13 else 1)
            return datetime.fromtimestamp(ts)
        except Exception:
            pass
    # 先抽取完整日期时间，避免字符串里混入其他字段导致失败。
    m = re.search(r"(20\d{2}|19\d{2})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?", value)
    if m:
        y, mo, d, hh, mm, ss = m.groups()
        try:
            return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0), int(ss or 0))
        except Exception:
            pass
    # 东方财富 K 线常见格式：YYYYMMDD
    m = re.search(r"(20\d{2}|19\d{2})(\d{2})(\d{2})", value)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    # 分时接口可能只有 HH:MM，这时只能按当前日期补齐。
    m = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b", value)
    if m:
        now = datetime.now()
        try:
            return datetime(now.year, now.month, now.day, int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
        except Exception:
            pass
    return datetime.now()


def local_now() -> datetime:
    return datetime.now()
