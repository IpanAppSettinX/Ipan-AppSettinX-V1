from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfigSnapshot:
    path: str
    existed: bool
    content: bytes
    sha256: str


class AtomicConfigStore:
    def __init__(self, allowed_root: Path) -> None:
        self.allowed_root = allowed_root.resolve(strict=True)

    def _validate_path(self, path: Path) -> Path:
        resolved = path.resolve(strict=False)
        if resolved != self.allowed_root and self.allowed_root not in resolved.parents:
            raise ValueError("Path konfigurasi berada di luar root adapter.")
        cursor = resolved
        while cursor != self.allowed_root:
            if cursor.exists() and cursor.is_symlink():
                raise ValueError("Symlink/reparse-like path ditolak.")
            cursor = cursor.parent
        return resolved

    def snapshot(self, path: Path) -> ConfigSnapshot:
        target = self._validate_path(path)
        existed = target.is_file()
        content = target.read_bytes() if existed else b""
        return ConfigSnapshot(
            path=str(target),
            existed=existed,
            content=content,
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def atomic_write(self, path: Path, content: bytes, *, expected_hash: str) -> str:
        target = self._validate_path(path)
        current = target.read_bytes() if target.exists() else b""
        if hashlib.sha256(current).hexdigest() != expected_hash:
            raise RuntimeError("Config berubah setelah preview; write dihentikan.")
        target.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return hashlib.sha256(content).hexdigest()
