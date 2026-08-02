from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PATH_PATTERN = re.compile(r"(?i)(?:[a-z]:\\|\\\\)[^\s\"']+")
_USER_PATTERN = re.compile(r"(?i)(user(?:name)?|account|sid)=[^\s,;]+")


def redact(value: str) -> str:
    value = _PATH_PATTERN.sub("<redacted-path>", value)
    return _USER_PATTERN.sub(r"\1=<redacted>", value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlation_id"] = str(correlation_id)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(log_path: Path | None = None) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    handler: logging.Handler
    if log_path is None:
        handler = logging.StreamHandler()
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
