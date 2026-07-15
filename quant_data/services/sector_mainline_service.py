from __future__ import annotations

import math
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from quant_data.data.data_contracts import build_source_status
from quant_data.services.cache_state_service import CacheStateService
from quant_data.utils import ThrottledSession


EASTMONEY_SECTOR_API = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_SECTOR_PAGE = "https://data.eastmoney.com/bkzj/"
SECTOR_FIELDS = "f2,f3,f8,f12,f14,f62,f66,f69,f72,f75,f78,f81,f84,f87,f104,f105,f106,f124"
SECTOR_TTL_SECONDS = 120


def _number(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _percentile(values: list[float], value: float | None) -> float:
    if value is None or not values:
        return 50.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return 50.0
    below = sum(1 for item in ordered if item < value)
    equal = sum(1 for item in ordered if item == value)
    return round((below + max(0, equal - 1) / 2) / (len(ordered) - 1) * 100, 2)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _friendly_source_error(value: Any) -> str:
    message = str(value or "").strip()
    lowered = message.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "东方财富公开板块资金接口连接超时"
    if "502" in lowered:
        return "东方财富公开板块资金接口暂时不可用（HTTP 502）"
    if "remote end closed" in lowered or "connection aborted" in lowered:
        return "东方财富公开板块资金接口连接中断"
    if "connection" in lowered:
        return "东方财富公开板块资金接口连接失败"
    head = message.split(" for url:", 1)[0].split("https://", 1)[0].strip(" ;:")
    return (head or "东方财富公开板块资金接口未返回有效数据")[:120]


class SectorMainlineService:
    """Real-source sector flow and strength monitor.

    Eastmoney's public sector-flow fields are exposed as a public-data estimate,
    not as broker Level-2 truth. Strength combines return rank, flow rank,
    breadth, participation and persisted daily continuity.
    """

    def __init__(
        self,
        cache: CacheStateService | None = None,
        fetcher: Callable[[str], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.cache = cache or CacheStateService()
        self.fetcher = fetcher or self._fetch_rows

    def snapshot(
        self,
        *,
        limit: int = 20,
        include_concept: bool = True,
        force: bool = False,
        allow_network: bool = True,
        can_refresh: bool = True,
        session_label: str = "交易时段",
        session_date: str = "",
    ) -> dict[str, Any]:
        limit = max(5, min(int(limit or 20), 80))
        trading_date = session_date or datetime.now().date().isoformat()
        latest = self.cache.latest("sector_mainline_cache", allow_stale=True)
        if latest.data and not can_refresh:
            return self._cached_response(latest.data, latest.cache_status, limit, include_concept, session_label)
        if latest.data and not force and latest.cache_status.get("status") == "hit":
            return self._cached_response(latest.data, latest.cache_status, limit, include_concept, session_label)
        if not allow_network:
            if latest.data:
                return self._cached_response(latest.data, latest.cache_status, limit, include_concept, session_label)
            return self._missing_response(limit, include_concept, session_label, ["板块快照缓存缺失；等待主线板块接口完成一次真实抓取"])

        board_types = ["industry", "concept"] if include_concept else ["industry"]
        raw_by_type: dict[str, list[dict[str, Any]]] = {}
        errors: list[str] = []
        for board_type in board_types:
            try:
                raw_by_type[board_type] = self.fetcher(board_type)
            except Exception as exc:
                errors.append(f"{board_type}: {str(exc)[:180]}")
        if not any(raw_by_type.values()):
            if latest.data:
                payload = self._cached_response(latest.data, latest.cache_status, limit, include_concept, session_label)
                payload["errors"] = errors
                payload["quality_status"] = "stale_cache"
                friendly_errors = [_friendly_source_error(error) for error in errors]
                payload["missing_reasons"] = list(
                    dict.fromkeys((payload.get("missing_reasons") or []) + friendly_errors)
                )
                return payload
            return self._missing_response(limit, include_concept, session_label, errors)

        history = self._history(trading_date, days=10)
        all_items: list[dict[str, Any]] = []
        for board_type, rows in raw_by_type.items():
            all_items.extend(self._normalize_rows(board_type, rows, history))
        all_items.sort(key=lambda item: (item["mainline_score"], item["net_inflow"] or float("-inf")), reverse=True)
        fetched_at = datetime.now().isoformat(timespec="seconds")
        published_at = max((str(item.get("published_at") or "") for item in all_items), default=fetched_at) or fetched_at
        data_trading_date = published_at[:10] if len(published_at) >= 10 else trading_date
        source_status = build_source_status(
            source_id="eastmoney",
            source_name="东方财富公开板块资金",
            payload=raw_by_type,
            source_url=EASTMONEY_SECTOR_PAGE,
            source_ref=EASTMONEY_SECTOR_API,
            fetched_at=fetched_at,
            published_at=published_at,
            available_at=fetched_at,
            ttl_seconds=SECTOR_TTL_SECONDS,
            missing_reasons=errors,
            quality_status="ok" if not errors else "partial",
        ).to_dict()
        payload = {
            "version": "V3.23",
            "trading_date": data_trading_date,
            "session_label": session_label,
            "updated_at": fetched_at,
            "published_at": published_at,
            "items": all_items,
            "industry_count": sum(1 for item in all_items if item["board_type"] == "industry"),
            "concept_count": sum(1 for item in all_items if item["board_type"] == "concept"),
            "methodology": {
                "strength_score": "30%涨跌幅横截面排名 + 30%公开资金净流横截面排名 + 25%上涨家数宽度 + 15%换手参与度",
                "mainline_score": "70%当日强度 + 30%近10个已保存交易日持续性；无历史时持续性保持50分中性",
                "truth_boundary": "资金流为东方财富公开板块资金字段口径，不是券商逐笔成交或 Level-2 主力账户识别。",
            },
            "source_status": source_status,
            "source_id": source_status["source_id"],
            "source_name": source_status["source_name"],
            "source_url": source_status["source_url"],
            "source_ref": source_status["source_ref"],
            "fetched_at": source_status["fetched_at"],
            "available_at": source_status["available_at"],
            "ttl_seconds": source_status["ttl_seconds"],
            "stale": False,
            "quality_status": source_status["quality_status"],
            "missing_reasons": source_status["missing_reasons"],
            "raw_hash": source_status["raw_hash"],
            "errors": errors,
        }
        cache_key = f"{data_trading_date}:{fetched_at[11:19]}"
        cache_status = self.cache.put(
            "sector_mainline_cache",
            cache_key,
            payload,
            ttl_seconds=SECTOR_TTL_SECONDS,
            source="eastmoney_sector_flow",
        )
        self.cache.put(
            "sector_mainline_daily",
            data_trading_date,
            payload,
            ttl_seconds=45 * 24 * 60 * 60,
            source="eastmoney_sector_flow",
        )
        return self._slice_payload(payload, cache_status, limit, include_concept)

    def history(self, *, days: int = 10, limit: int = 20) -> dict[str, Any]:
        today = datetime.now().date().isoformat()
        rows = self._history(today, days=max(1, min(int(days or 10), 45)))
        return {
            "ok": True,
            "days": len(rows),
            "items": rows[: max(1, min(int(limit or 20), 100))],
            "note": "仅返回系统实际保存的公开板块快照；缺少日期不会回填或伪造。",
        }

    def _fetch_rows(self, board_type: str) -> list[dict[str, Any]]:
        session = ThrottledSession()
        rows: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        # The public endpoint caps a page at 100 rows. Read both ends of the
        # net-flow ranking so the UI can show inflow and outflow leaders.
        for order in (1, 0):
            params = {
                "pn": 1,
                "pz": 100,
                "po": order,
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fid": "f62",
                "fid0": "f62",
                "stat": "1",
                "ut": "b2884a393a59ad64002292a3e90d46a5",
                "rt": "52975239",
                "_": int(time.time() * 1000),
                "fs": "m:90 t:3" if board_type == "concept" else "m:90 t:2",
                "fields": SECTOR_FIELDS,
            }
            try:
                response = session.get(EASTMONEY_SECTOR_API, params=params, timeout=12)
                data = response.json().get("data") or {}
            except Exception as exc:
                errors.append(f"po={order}: {str(exc)[:140]}")
                continue
            for row in data.get("diff") or []:
                if isinstance(row, dict) and row.get("f12"):
                    rows[str(row["f12"])] = row
        if not rows and errors:
            raise RuntimeError("；".join(errors))
        return list(rows.values())

    def _normalize_rows(
        self,
        board_type: str,
        rows: list[dict[str, Any]],
        history: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        valid = [row for row in rows if row.get("f12") and row.get("f14")]
        changes = [_number(row.get("f3")) for row in valid]
        flows = [_number(row.get("f62")) for row in valid]
        turnovers = [_number(row.get("f8")) for row in valid]
        change_values = [value for value in changes if value is not None]
        flow_values = [value for value in flows if value is not None]
        turnover_values = [value for value in turnovers if value is not None]
        history_by_code: dict[str, list[dict[str, Any]]] = {}
        for snapshot in history:
            for item in snapshot.get("items") or []:
                if item.get("board_type") == board_type and item.get("board_code"):
                    history_by_code.setdefault(str(item["board_code"]), []).append(item)
        result = []
        for row in valid:
            code = str(row.get("f12"))
            change = _number(row.get("f3"))
            flow = _number(row.get("f62"))
            turnover = _number(row.get("f8"))
            up_count = int(_number(row.get("f104")) or 0)
            down_count = int(_number(row.get("f105")) or 0)
            flat_count = int(_number(row.get("f106")) or 0)
            breadth_total = up_count + down_count + flat_count
            breadth_score = up_count / breadth_total * 100 if breadth_total else 50.0
            change_rank = _percentile(change_values, change)
            flow_rank = _percentile(flow_values, flow)
            participation = _percentile(turnover_values, turnover)
            strength = _clamp(change_rank * 0.30 + flow_rank * 0.30 + breadth_score * 0.25 + participation * 0.15)
            old_items = history_by_code.get(code, [])
            persistence_values = [float(item.get("strength_score") or 50) for item in old_items[:10]]
            persistence = sum(persistence_values) / len(persistence_values) if persistence_values else 50.0
            mainline = _clamp(strength * 0.70 + persistence * 0.30)
            if flow is not None and flow < 0:
                mainline = max(0.0, mainline - min(12.0, abs(flow_rank - 50) * 0.12 + 3.0))
            if mainline >= 75 and (flow or 0) > 0 and breadth_score >= 60:
                stage = "主线"
            elif strength >= 65 and (flow or 0) > 0:
                stage = "强势"
            elif strength >= 52:
                stage = "轮动"
            elif (change or 0) >= 0 and (flow or 0) < 0:
                stage = "分歧"
            else:
                stage = "退潮"
            missing = []
            for key, label in ((change, "涨跌幅"), (flow, "资金净流"), (turnover, "换手率")):
                if key is None:
                    missing.append(f"{label}字段缺失")
            if not breadth_total:
                missing.append("上涨/下跌家数字段缺失")
            timestamp = int(_number(row.get("f124")) or 0)
            published_at = datetime.fromtimestamp(timestamp).isoformat(timespec="seconds") if timestamp else ""
            result.append(
                {
                    "board_code": code,
                    "board_name": str(row.get("f14")),
                    "board_type": board_type,
                    "board_type_name": "概念板块" if board_type == "concept" else "行业板块",
                    "latest": _number(row.get("f2")),
                    "change_pct": change,
                    "turnover_pct": turnover,
                    "net_inflow": flow,
                    "net_inflow_ratio_pct": _number(row.get("f69")),
                    "super_large_net_inflow": _number(row.get("f66")),
                    "large_net_inflow": _number(row.get("f72")),
                    "medium_net_inflow": _number(row.get("f78")),
                    "small_net_inflow": _number(row.get("f84")),
                    "up_count": up_count,
                    "down_count": down_count,
                    "flat_count": flat_count,
                    "breadth_pct": round(breadth_score, 2),
                    "change_rank": change_rank,
                    "flow_rank": flow_rank,
                    "participation_rank": participation,
                    "strength_score": round(strength, 2),
                    "persistence_score": round(persistence, 2),
                    "mainline_score": round(mainline, 2),
                    "stage": stage,
                    "history_days": len(persistence_values),
                    "published_at": published_at,
                    "source_id": "eastmoney",
                    "source_name": "东方财富公开板块资金",
                    "source_url": EASTMONEY_SECTOR_PAGE,
                    "source_ref": EASTMONEY_SECTOR_API,
                    "quality_status": "ok" if not missing else "partial",
                    "missing_reasons": missing,
                    "explanation": f"{stage}：强度{strength:.1f}，公开资金净流排名{flow_rank:.1f}，上涨宽度{breadth_score:.1f}%。",
                }
            )
        return result

    def _history(self, trading_date: str, *, days: int) -> list[dict[str, Any]]:
        try:
            current = datetime.fromisoformat(trading_date).date()
        except ValueError:
            current = datetime.now().date()
        snapshots = []
        for offset in range(days + 5):
            if len(snapshots) >= days:
                break
            day = (current - timedelta(days=offset)).isoformat()
            read = self.cache.get("sector_mainline_daily", day, allow_stale=True)
            if read.data:
                snapshots.append(read.data)
        return snapshots

    def _cached_response(
        self,
        payload: dict[str, Any],
        cache_status: dict[str, Any],
        limit: int,
        include_concept: bool,
        session_label: str,
    ) -> dict[str, Any]:
        result = self._slice_payload(payload, cache_status, limit, include_concept)
        result["session_label"] = session_label
        result["served_from_cache"] = True
        result["stale"] = bool(cache_status.get("stale"))
        result["note"] = f"{session_label}：复用最近成功板块快照，不重复抓取外部资金流。"
        return result

    def _slice_payload(
        self,
        payload: dict[str, Any],
        cache_status: dict[str, Any],
        limit: int,
        include_concept: bool,
    ) -> dict[str, Any]:
        items = [item for item in (payload.get("items") or []) if include_concept or item.get("board_type") == "industry"]
        lead_count = max(1, int(limit * 0.72))
        selected = list(items[:lead_count])
        selected_codes = {str(item.get("board_code")) for item in selected}
        outflows = sorted(
            (item for item in items if (item.get("net_inflow") or 0) < 0),
            key=lambda item: float(item.get("net_inflow") or 0),
        )
        for item in outflows:
            code = str(item.get("board_code"))
            if code not in selected_codes:
                selected.append(item)
                selected_codes.add(code)
            if len(selected) >= limit:
                break
        if len(selected) < limit:
            for item in items:
                code = str(item.get("board_code"))
                if code not in selected_codes:
                    selected.append(item)
                    selected_codes.add(code)
                if len(selected) >= limit:
                    break
        return {
            "ok": True,
            **{key: value for key, value in payload.items() if key != "items"},
            "items": selected[:limit],
            "count": min(len(selected), limit),
            "total_count": len(items),
            "cache_status": cache_status,
        }

    def _missing_response(
        self,
        limit: int,
        include_concept: bool,
        session_label: str,
        errors: list[str],
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "items": [],
            "count": 0,
            "limit": limit,
            "include_concept": include_concept,
            "session_label": session_label,
            "quality_status": "missing",
            "stale": False,
            "missing_reasons": (
                list(dict.fromkeys(_friendly_source_error(error) for error in errors))
                if errors
                else ["东方财富公开板块资金接口未返回有效数据"]
            ),
            "errors": errors,
            "source_id": "eastmoney",
            "source_name": "东方财富公开板块资金",
            "source_url": EASTMONEY_SECTOR_PAGE,
            "source_ref": EASTMONEY_SECTOR_API,
            "methodology": {
                "truth_boundary": "无真实板块数据时不生成资金流或板块强度。",
            },
            "cache_status": self.cache.status("miss", ttl_seconds=SECTOR_TTL_SECONDS, source="sector_mainline_cache"),
        }
