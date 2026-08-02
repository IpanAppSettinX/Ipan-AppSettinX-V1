from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

from parse_public_drive_metadata import parse_entries

TEXT_EXTENSIONS = {".reg", ".bat", ".cmd", ".txt", ".ini", ".ps1"}
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024


def safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return cleaned[:120] or "unnamed"


def fetch(url: str, *, max_bytes: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    allowed_hosts = {"drive.google.com", "drive.usercontent.google.com"}
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("Only fixed HTTPS Google Drive hosts are allowed.")
    request = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"Response exceeds {max_bytes} bytes")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only crawler for a public Drive folder")
    parser.add_argument("--root-metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-folders", type=int, default=250)
    args = parser.parse_args()

    root_payload = json.loads(args.root_metadata.read_text(encoding="utf-8"))
    root_entries = root_payload["entries"]
    queue: deque[tuple[dict[str, Any], list[str], int]] = deque(
        (entry, [entry["name"]], 1) for entry in root_entries if entry["is_folder"]
    )
    visited: set[str] = set()
    inventory: list[dict[str, Any]] = list(root_entries)
    errors: list[dict[str, str]] = []
    downloaded: list[dict[str, Any]] = []
    total_bytes = 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    while queue and len(visited) < args.max_folders:
        folder, path_parts, depth = queue.popleft()
        if folder["id"] in visited:
            continue
        visited.add(folder["id"])
        try:
            raw = fetch(folder["folder_url"], max_bytes=2 * 1024 * 1024)
            children = parse_entries(raw.decode("utf-8", errors="replace"))
        except (OSError, ValueError, urllib.error.URLError) as exc:
            errors.append({"id": folder["id"], "name": folder["name"], "error": str(exc)})
            continue
        for child in children:
            child["parent_id"] = folder["id"]
            child["path"] = "/".join([*path_parts, child["name"]])
            child["depth"] = depth
            inventory.append(child)
            if child["is_folder"]:
                queue.append((child, [*path_parts, child["name"]], depth + 1))
                continue
            extension = Path(child["name"]).suffix.casefold()
            if extension not in TEXT_EXTENSIONS or total_bytes >= MAX_TOTAL_BYTES:
                continue
            try:
                content = fetch(child["download_url"], max_bytes=MAX_FILE_BYTES)
                if content.lstrip().startswith(b"<!DOCTYPE html"):
                    raise ValueError("Drive returned an HTML confirmation page")
                relative = Path(*[safe_name(part) for part in path_parts])
                target = (
                    args.output_dir
                    / "files"
                    / relative
                    / (f"{safe_name(Path(child['name']).stem)}__{child['id']}{extension}")
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                total_bytes += len(content)
                downloaded.append(
                    {
                        "id": child["id"],
                        "name": child["name"],
                        "source_path": child["path"],
                        "local_path": str(target),
                        "size": len(content),
                    }
                )
            except (OSError, ValueError, urllib.error.URLError) as exc:
                errors.append({"id": child["id"], "name": child["name"], "error": str(exc)})
        time.sleep(0.08)

    report = {
        "mode": "public_read_only_static_text_downloads_only",
        "folders_visited": len(visited),
        "inventory_count": len(inventory),
        "downloaded_count": len(downloaded),
        "downloaded_bytes": total_bytes,
        "inventory": inventory,
        "downloads": downloaded,
        "errors": errors,
        "queue_remaining": len(queue),
    }
    report_path = args.output_dir / "crawl-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "report": str(report_path),
                "folders_visited": len(visited),
                "inventory_count": len(inventory),
                "downloaded_count": len(downloaded),
                "downloaded_bytes": total_bytes,
                "errors": len(errors),
                "queue_remaining": len(queue),
            },
            indent=2,
        )
    )
    return 0 if not queue else 2


if __name__ == "__main__":
    raise SystemExit(main())
