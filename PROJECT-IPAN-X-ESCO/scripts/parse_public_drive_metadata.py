from __future__ import annotations

import argparse
import contextlib
import html
import json
import re
from pathlib import Path
from typing import Any

ENTRY_PATTERN = re.compile(
    r'\[\[null,"(?P<id>[A-Za-z0-9_-]{10,})"\],null,null,null,'
    r'"(?P<mime>[^"]+)"(?P<body>.{0,2400}?)'
    r'\[\[\["(?P<name>(?:\\.|[^"])*)"(?:,null,1)?\]\]',
    flags=re.DOTALL,
)


def decode_google_text(value: str) -> str:
    value = value.replace(r"\u003d", "=").replace(r"\u0026", "&")
    with contextlib.suppress(json.JSONDecodeError):
        value = json.loads(f'"{value}"')
    return html.unescape(value)


def parse_entries(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in ENTRY_PATTERN.finditer(text):
        file_id = match.group("id")
        if file_id in seen:
            continue
        seen.add(file_id)
        mime_type = decode_google_text(match.group("mime"))
        name = decode_google_text(match.group("name"))
        entries.append(
            {
                "id": file_id,
                "name": name,
                "mime_type": mime_type,
                "is_folder": mime_type == "application/vnd.google-apps.folder",
                "folder_url": (
                    f"https://drive.google.com/drive/folders/{file_id}?usp=sharing"
                    if mime_type == "application/vnd.google-apps.folder"
                    else None
                ),
                "download_url": (
                    None
                    if mime_type == "application/vnd.google-apps.folder"
                    else f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
                ),
            }
        )
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    entries = parse_entries(args.html_file.read_text(encoding="utf-8", errors="replace"))
    payload = {"count": len(entries), "entries": entries}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    folders = [item for item in entries if item["is_folder"]]
    files = [item for item in entries if not item["is_folder"]]
    print(f"Parsed {len(entries)} entries: {len(folders)} folders, {len(files)} files")
    for item in entries:
        print(f"{item['id']} | {item['mime_type']} | {item['name']}")
    return 0 if entries else 1


if __name__ == "__main__":
    raise SystemExit(main())
