from __future__ import annotations

import argparse
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from crawl_public_drive_registry import MAX_FILE_BYTES, fetch, safe_name

TEXT_EXTENSIONS = {".reg", ".bat", ".cmd", ".txt", ".ini", ".ps1", ".cfg"}
BINARY_MAGICS = (b"MZ", b"PK\x03\x04", b"Rar!", b"7z\xbc\xaf\x27\x1c")


def looks_like_text_configuration(data: bytes) -> bool:
    if not data or data.startswith(BINARY_MAGICS):
        return False
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = data.decode(encoding)
        except UnicodeError:
            continue
        printable = sum(character.isprintable() or character in "\r\n\t" for character in text)
        if printable / max(1, len(text)) > 0.82:
            return True
    return False


def download(entry: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    file_id = entry["id"]
    url = "https://drive.usercontent.google.com/download?" + urllib.parse.urlencode(
        {"id": file_id, "export": "download", "confirm": "t"}
    )
    data = fetch(url, max_bytes=MAX_FILE_BYTES)
    if not looks_like_text_configuration(data):
        raise ValueError("Downloaded content is not a recognized text configuration")
    source_parts = entry["path"].split("/")
    relative = Path(*[safe_name(part) for part in source_parts[:-1]])
    extension = Path(entry["name"]).suffix.casefold()
    target = (
        output_dir
        / "files"
        / relative
        / (f"{safe_name(Path(entry['name']).stem)}__{file_id}{extension}")
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "id": file_id,
        "name": entry["name"],
        "source_path": entry["path"],
        "local_path": str(target),
        "size": len(data),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crawl-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    payload = json.loads(args.crawl_report.read_text(encoding="utf-8"))
    candidates = [
        entry
        for entry in payload["inventory"]
        if not entry["is_folder"] and Path(entry["name"]).suffix.casefold() in TEXT_EXTENSIONS
    ]
    downloads: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as executor:
        futures = {executor.submit(download, entry, args.output_dir): entry for entry in candidates}
        for future in as_completed(futures):
            entry = futures[future]
            try:
                downloads.append(future.result())
            except Exception as exc:
                errors.append(
                    {
                        "id": entry["id"],
                        "name": entry["name"],
                        "path": entry["path"],
                        "error": str(exc),
                    }
                )
    report = {
        "mode": "public_read_only_text_configuration_downloads_only",
        "candidate_count": len(candidates),
        "downloaded_count": len(downloads),
        "downloaded_bytes": sum(item["size"] for item in downloads),
        "downloads": sorted(downloads, key=lambda item: item["source_path"].casefold()),
        "errors": errors,
    }
    report_path = args.output_dir / "text-download-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "report": str(report_path),
                "candidate_count": len(candidates),
                "downloaded_count": len(downloads),
                "downloaded_bytes": report["downloaded_bytes"],
                "errors": len(errors),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
