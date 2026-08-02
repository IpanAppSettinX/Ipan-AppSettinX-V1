from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("release-sha256.json"))
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    files = sorted(path for path in root.rglob("*") if path.is_file())
    payload = {
        "algorithm": "SHA-256",
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": digest(path),
            }
            for path in files
        ],
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote hashes for {len(files)} files to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
