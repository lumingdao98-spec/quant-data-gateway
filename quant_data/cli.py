from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

from quant_data.cache import MarketCache
from quant_data.services.market_data_service import MarketDataService


def _fmt_float(x, digits: int = 2) -> str:
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return "-"


def print_quotes_table(quotes) -> None:
    if not quotes:
        print("未获取到行情。请检查网络、代码、代理设置或稍后重试。")
        return
    headers = ["代码", "名称", "最新", "涨跌幅%", "今开", "最高", "最低", "成交额(亿)", "来源", "时间"]
    rows = []
    for q in quotes:
        rows.append(
            [
                q.symbol,
                q.name,
                _fmt_float(q.last),
                _fmt_float(q.change_pct),
                _fmt_float(q.open),
                _fmt_float(q.high),
                _fmt_float(q.low),
                _fmt_float(q.amount / 1e8),
                q.source,
                q.ts.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    widths = [max(len(str(h)), *(len(str(row[i])) for row in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def print_bars_table(bars, max_rows: int = 12) -> None:
    if not bars:
        print("未获取到K线。")
        return
    rows = bars[-max_rows:]
    headers = ["时间", "开", "高", "低", "收", "量", "额(亿)", "来源"]
    data = []
    for b in rows:
        data.append(
            [
                b.ts.strftime("%Y-%m-%d %H:%M"),
                _fmt_float(b.open),
                _fmt_float(b.high),
                _fmt_float(b.low),
                _fmt_float(b.close),
                _fmt_float(b.volume, 0),
                _fmt_float(b.amount / 1e8),
                b.source,
            ]
        )
    widths = [max(len(str(h)), *(len(str(row[i])) for row in data)) for i, h in enumerate(headers)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in data:
        print(fmt.format(*row))




def is_port_available(host: str, port: int) -> bool:
    """检查 host:port 是否可以绑定。False 表示端口已被其他程序占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, int(port)))
            return True
        except OSError:
            return False


def find_available_port(host: str, start_port: int, max_tries: int = 50) -> int:
    """从 start_port 开始寻找可用端口。"""
    port = int(start_port)
    for candidate in range(port, port + max_tries):
        if is_port_available(host, candidate):
            return candidate
    raise RuntimeError(f"从 {start_port} 到 {start_port + max_tries - 1} 没有找到可用端口")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A股实时数据网关：行情、K线、缓存、API服务")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_quote = sub.add_parser("quote", help="获取一个或多个股票/ETF实时行情")
    p_quote.add_argument("symbols", nargs="+", help="如 300750 600519 000001")
    p_quote.add_argument("--force", action="store_true", help="忽略3秒缓存，强制联网刷新")

    p_watch = sub.add_parser("watch", help="循环盯盘，默认每5秒刷新一次")
    p_watch.add_argument("symbols", nargs="+", help="如 300750 600519")
    p_watch.add_argument("--interval", type=float, default=5.0, help="刷新间隔，建议 >= 3 秒")

    p_kline = sub.add_parser("kline", help="获取K线")
    p_kline.add_argument("symbol", help="股票代码")
    p_kline.add_argument("--frame", default="1d", choices=["1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M"], help="周期")
    p_kline.add_argument("--limit", type=int, default=120, help="返回根数")
    p_kline.add_argument("--adjust", default="qfq", choices=["qfq", "hfq", "none", ""], help="复权方式")
    p_kline.add_argument("--csv", default="", help="保存CSV路径")
    p_kline.add_argument("--force", action="store_true", help="强制联网刷新")

    p_market = sub.add_parser("market", help="获取全市场行情快照的一页")
    p_market.add_argument("--page", type=int, default=1)
    p_market.add_argument("--page-size", type=int, default=50)

    p_search = sub.add_parser("search", help="搜索股票/ETF")
    p_search.add_argument("keyword", help="名称或代码，如 宁德 300750")
    p_search.add_argument("--limit", type=int, default=30)

    sub.add_parser("cache", help="查看本地缓存统计")

    p_api = sub.add_parser("api", help="启动 FastAPI 服务")
    p_api.add_argument("--host", default="127.0.0.1")
    p_api.add_argument("--port", type=int, default=8000)
    p_api.add_argument("--auto-port", action="store_true", help="如果端口被占用，则自动切换到下一个可用端口")
    p_api.add_argument("--reload", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = MarketDataService()

    try:
        if args.cmd == "quote":
            quotes = service.get_quotes(args.symbols, force_refresh=args.force)
            print_quotes_table(quotes)
            return 0

        if args.cmd == "watch":
            interval = max(float(args.interval), 3.0)
            print("按 Ctrl+C 退出。公共接口请低频刷新，建议 interval >= 3。")
            while True:
                print("\n" + "=" * 100)
                quotes = service.get_quotes(args.symbols, force_refresh=True)
                print_quotes_table(quotes)
                time.sleep(interval)

        if args.cmd == "kline":
            bars = service.get_kline(args.symbol, frame=args.frame, limit=args.limit, adjust=args.adjust, force_refresh=args.force)
            print_bars_table(bars)
            if args.csv:
                path = service.export_bars_csv(args.symbol, args.frame, bars, Path(args.csv))
                print(f"已保存: {path}")
            return 0

        if args.cmd == "market":
            quotes = service.get_market_snapshot(page=args.page, page_size=args.page_size)
            print_quotes_table(quotes)
            return 0

        if args.cmd == "search":
            assets = service.search_assets(args.keyword, limit=args.limit)
            for a in assets:
                print(f"{a.symbol}\t{a.name}\t{a.asset_type.value}\t{a.source}")
            return 0

        if args.cmd == "cache":
            print(MarketCache().stats())
            return 0

        if args.cmd == "api":
            import uvicorn

            port = int(args.port)
            if not is_port_available(args.host, port):
                if args.auto_port:
                    new_port = find_available_port(args.host, port + 1)
                    print(f"提示：{args.host}:{port} 已被占用，已自动切换到 {args.host}:{new_port}")
                    port = new_port
                else:
                    print(f"错误：{args.host}:{port} 端口已被占用。", file=sys.stderr)
                    print("解决办法1：换一个端口启动，例如：python main.py api --port 8001", file=sys.stderr)
                    print("解决办法2：结束占用8000端口的进程。Windows命令：netstat -ano | findstr :8000", file=sys.stderr)
                    print("解决办法3：使用自动端口：python main.py api --port 8000 --auto-port", file=sys.stderr)
                    return 2

            print(f"API 服务地址：http://{args.host}:{port}")
            print(f"API 文档地址：http://{args.host}:{port}/docs")
            print(f"测试页面地址：http://{args.host}:{port}/ui")
            uvicorn.run("quant_data.api:app", host=args.host, port=port, reload=args.reload)
            return 0

        parser.print_help()
        return 1
    except KeyboardInterrupt:
        print("\n已退出。")
        return 0
    except Exception as exc:
        print(f"错误: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("建议：检查网络、代理、股票代码；如使用代理异常，可在 Windows CMD 执行 set QUANT_DISABLE_PROXY=1 后重试。", file=sys.stderr)
        return 2
