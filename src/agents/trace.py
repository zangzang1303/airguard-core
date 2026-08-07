from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger("airguard.agent.trace")

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "display_name",
    "email",
    "openai_api_key",
    "password",
    "prompt",
    "query",
    "secret",
    "token",
    "user_id",
}


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def emit_trace(trace: Mapping[str, Any]) -> None:
    logger.info("agent_trace %s", json.dumps(redact(trace), ensure_ascii=True, sort_keys=True))
