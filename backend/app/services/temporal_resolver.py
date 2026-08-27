from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Any


class TemporalResolver:
    """
    Resolves natural-language temporal expressions into normalized time contexts,
    distinguishing LIVE queries from multi-step FORECAST horizons.
    """

    VN_TZ = timezone(timedelta(hours=7))

    @classmethod
    def resolve(cls, query: str, base_time: datetime | None = None) -> dict[str, Any]:
        now = base_time or datetime.now(UTC)
        vn_now = now.astimezone(cls.VN_TZ)
        current_vn_hour = vn_now.hour

        q = query.lower()

        # 1. Check relative offset ("1h nữa", "2 tiếng nữa", "sau 3 giờ")
        match_offset = re.search(r"(\d+)\s*(h|giờ|tiếng)\s*(nữa|sau|tới)", q)
        if match_offset:
            offset_h = max(1, min(24, int(match_offset.group(1))))
            target_dt = now + timedelta(hours=offset_h)
            target_vn = target_dt.astimezone(cls.VN_TZ)
            return {
                "type": "forecast",
                "is_forecast": True,
                "forecast_hour": offset_h,
                "target_datetime": target_dt.isoformat(),
                "start": target_dt.isoformat(),
                "end": (target_dt + timedelta(hours=1)).isoformat(),
                "label": f"Sau {offset_h} giờ ({target_vn.strftime('%H:%M')})",
                "raw_query_match": match_offset.group(0),
            }

        # 2. Check explicit clock times ("18:00", "19h", "20h30", "6 giờ tối", "7h tối")
        match_pm_hour = re.search(r"(\d{1,2})\s*(?:giờ|h)?\s*(?:tối|chiều)", q)
        if match_pm_hour:
            raw_h = int(match_pm_hour.group(1))
            clock_h = raw_h if raw_h >= 12 else raw_h + 12
            offset_h = clock_h - current_vn_hour
            if offset_h <= 0:
                offset_h += 24  # Tomorrow
            offset_h = max(1, min(24, offset_h))
            target_dt = now + timedelta(hours=offset_h)
            return {
                "type": "forecast",
                "is_forecast": True,
                "forecast_hour": offset_h,
                "target_datetime": target_dt.isoformat(),
                "start": target_dt.isoformat(),
                "end": (target_dt + timedelta(hours=2)).isoformat(),
                "label": f"{clock_h:02d}:00 hôm nay",
                "raw_query_match": match_pm_hour.group(0),
            }

        match_clock = re.search(r"(?:lúc\s*)?(\d{1,2})[:h](\d{2})?", q)
        if match_clock and any(term in q for term in ["lúc", "khi", "vào", "dự báo"]):
            raw_h = int(match_clock.group(1))
            if 0 <= raw_h <= 24:
                offset_h = raw_h - current_vn_hour
                if offset_h <= 0:
                    offset_h += 24
                offset_h = max(1, min(24, offset_h))
                target_dt = now + timedelta(hours=offset_h)
                return {
                    "type": "forecast",
                    "is_forecast": True,
                    "forecast_hour": offset_h,
                    "target_datetime": target_dt.isoformat(),
                    "start": target_dt.isoformat(),
                    "end": (target_dt + timedelta(hours=1)).isoformat(),
                    "label": f"{raw_h:02d}:00",
                    "raw_query_match": match_clock.group(0),
                }

        # 3. Check Named Part-of-Day expressions
        if any(term in q for term in ["tối nay", "buổi tối", "tonight", "this evening"]):
            target_h = 20
            offset_h = target_h - current_vn_hour if current_vn_hour < target_h else 2
            offset_h = max(1, min(24, offset_h))
            target_dt = now + timedelta(hours=offset_h)
            return {
                "type": "forecast",
                "is_forecast": True,
                "forecast_hour": offset_h,
                "target_datetime": target_dt.isoformat(),
                "start": target_dt.isoformat(),
                "end": (target_dt + timedelta(hours=2)).isoformat(),
                "label": f"Tối nay ({target_h}:00 - {target_h+2}:00)",
                "raw_query_match": "tối nay",
            }

        if any(term in q for term in ["chiều nay", "buổi chiều", "this afternoon"]):
            target_h = 17
            offset_h = target_h - current_vn_hour if current_vn_hour < target_h else 1
            offset_h = max(1, min(24, offset_h))
            target_dt = now + timedelta(hours=offset_h)
            return {
                "type": "forecast",
                "is_forecast": True,
                "forecast_hour": offset_h,
                "target_datetime": target_dt.isoformat(),
                "start": target_dt.isoformat(),
                "end": (target_dt + timedelta(hours=2)).isoformat(),
                "label": f"Chiều nay ({target_h}:00)",
                "raw_query_match": "chiều nay",
            }

        if any(term in q for term in ["sáng mai", "ngày mai", "tomorrow morning", "tomorrow"]):
            target_h = 7
            offset_h = (24 - current_vn_hour) + target_h
            offset_h = max(1, min(24, offset_h))
            target_dt = now + timedelta(hours=offset_h)
            return {
                "type": "forecast",
                "is_forecast": True,
                "forecast_hour": offset_h,
                "target_datetime": target_dt.isoformat(),
                "start": target_dt.isoformat(),
                "end": (target_dt + timedelta(hours=3)).isoformat(),
                "label": "Sáng mai (07:00 - 09:00)",
                "raw_query_match": "sáng mai",
            }

        # 4. Default to LIVE Real-time
        return {
            "type": "live",
            "is_forecast": False,
            "forecast_hour": 0,
            "target_datetime": now.isoformat(),
            "start": now.isoformat(),
            "end": now.isoformat(),
            "label": "Hiện tại",
            "raw_query_match": "now",
        }


temporal_resolver = TemporalResolver()
