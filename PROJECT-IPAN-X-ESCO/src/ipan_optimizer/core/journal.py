from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class RecoveryJournal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._sequence = 0
        self._previous_hash = "0" * 64
        self._load_tail()

    def _load_tail(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            self._sequence = int(record["sequence"])
            self._previous_hash = str(record["record_hash"])

    def append(self, transaction_id: str, event: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._sequence += 1
            record = {
                "sequence": self._sequence,
                "timestamp": datetime.now(UTC).isoformat(),
                "transaction_id": transaction_id,
                "event": event,
                "payload": payload,
                "previous_hash": self._previous_hash,
            }
            canonical = json.dumps(
                record,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            record["record_hash"] = record_hash
            line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
            self._previous_hash = record_hash

    def validate(self) -> bool:
        if not self.path.exists():
            return True
        previous_hash = "0" * 64
        expected_sequence = 1
        for line in self.path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            record_hash = record.pop("record_hash")
            canonical = json.dumps(
                record,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            if record["sequence"] != expected_sequence:
                return False
            if record["previous_hash"] != previous_hash:
                return False
            if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != record_hash:
                return False
            previous_hash = record_hash
            expected_sequence += 1
        return True
