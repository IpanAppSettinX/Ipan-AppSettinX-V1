from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TEXT_EXTENSIONS = frozenset({".bat", ".cfg", ".cmd", ".ini", ".ps1", ".reg", ".txt"})
REGISTRY_KEY = re.compile(r"^\[(?P<key>-?[^\]]+)\]\s*$")
REGISTRY_VALUE = re.compile(r'^(?:"(?P<name>[^"]*)"|@)\s*=')
REG_COMMAND = re.compile(
    r"\breg(?:\.exe)?\s+(?:add|delete)\s+(?P<key>\"[^\"]+\"|\S+)",
    re.IGNORECASE,
)

INERT_MARKETING_NAMES = re.compile(
    r"(?:aim|aimbot|aimassist|autoh(?:ead)?shot|headshot|recoil|fov|drag|sensib)",
    re.IGNORECASE,
)
SECURITY_PATTERNS = re.compile(
    r"(?:windows defender|disableantispyware|disablerealtimemonitoring|"
    r"tamper|enablelua|firewallpolicy|exploitguard|featuresettingsoverride|"
    r"enablecfg|smartscreen|windows update|wuauserv|usosvc)",
    re.IGNORECASE,
)
BOOT_PATTERNS = re.compile(
    r"(?:\bbcdedit\b|useplatformclock|useplatformtick|disabledynamictick|"
    r"tscsyncpolicy|hypervisorlaunchtype)",
    re.IGNORECASE,
)
TDR_PATTERNS = re.compile(
    r"(?:graphicsdrivers.*tdr|tdrlevel|tdrdelay|tdrddidelay|tdrdebugmode)",
    re.IGNORECASE,
)
DESTRUCTIVE_PATTERNS = re.compile(
    r"(?:\brd\s+/s|\brmdir\s+/s|\bdel\s+/[fsq]|remove-appxpackage|"
    r"get-appxpackage|takeown|icacls|format\s|diskpart|emptyworkingset|"
    r"taskkill|prefetch|\\runonce?|\\run\\)",
    re.IGNORECASE,
)
SERVICE_PATTERNS = re.compile(
    r"(?:\bsc(?:\.exe)?\s+(?:config|delete|stop)|\bnet\s+stop\b|"
    r"currentcontrolset\\services)",
    re.IGNORECASE,
)
MOUSE_PATTERNS = re.compile(
    r"(?:control panel\\mouse|mousesensitivity|mousespeed|mousethreshold|"
    r"smoothmouse[xy]curve)",
    re.IGNORECASE,
)
CURATED_CANDIDATES = re.compile(
    r"(?:software\\microsoft\\gamebar.*autogamemodeenabled|"
    r"software\\microsoft\\windows\\currentversion\\gamedvr.*appcaptureenabled|"
    r"system\\gameconfigstore.*gamedvr_enabled)",
    re.IGNORECASE,
)


def decode_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def normalized_lines(content: str) -> list[str]:
    lines: list[str] = []
    pending = ""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "#")):
            continue
        pending += line
        if pending.endswith("\\"):
            pending = pending[:-1]
            continue
        lines.append(pending)
        pending = ""
    if pending:
        lines.append(pending)
    return lines


def classify(line: str, *, key_context: str = "") -> set[str]:
    combined = f"{key_context} {line}"
    categories: set[str] = set()
    if SECURITY_PATTERNS.search(combined):
        categories.add("critical_security_reduction")
    if BOOT_PATTERNS.search(combined):
        categories.add("dangerous_boot_configuration")
    if TDR_PATTERNS.search(combined):
        categories.add("dangerous_gpu_recovery")
    if DESTRUCTIVE_PATTERNS.search(combined):
        categories.add("dangerous_destructive_or_process")
    if SERVICE_PATTERNS.search(combined):
        categories.add("dangerous_service_change")
    if MOUSE_PATTERNS.search(combined):
        categories.add("conditional_mouse_behavior")
    if CURATED_CANDIDATES.search(combined):
        categories.add("curated_candidate")
    return categories


def analyze_file(path: Path, root: Path) -> dict[str, Any]:
    content = decode_text(path)
    lines = normalized_lines(content)
    current_key = ""
    registry_keys: set[str] = set()
    value_names: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    inert_names: Counter[str] = Counter()
    registry_command_count = 0

    for line in lines:
        key_match = REGISTRY_KEY.match(line)
        if key_match:
            current_key = key_match.group("key")
            registry_keys.add(current_key)
            for category in classify(line):
                categories[category] += 1
            continue

        value_match = REGISTRY_VALUE.match(line)
        if value_match:
            value_name = value_match.group("name") or "(Default)"
            value_names[value_name] += 1
            if INERT_MARKETING_NAMES.search(value_name):
                inert_names[value_name] += 1

        for command_match in REG_COMMAND.finditer(line):
            registry_command_count += 1
            registry_keys.add(command_match.group("key").strip('"'))
        for category in classify(line, key_context=current_key):
            categories[category] += 1

    raw = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "extension": path.suffix.casefold(),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
        "line_count": len(content.splitlines()),
        "registry_key_count": len(registry_keys),
        "registry_value_count": sum(value_names.values()),
        "registry_command_count": registry_command_count,
        "risk_matches": dict(categories),
        "inert_marketing_names": sorted(inert_names),
        "top_registry_keys": sorted(registry_keys)[:20],
    }


def build_report(root: Path) -> dict[str, Any]:
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in TEXT_EXTENSIONS
    )
    results = [analyze_file(path, root) for path in files]
    extensions: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    inert_names: Counter[str] = Counter()
    category_samples: dict[str, list[str]] = defaultdict(list)

    for item in results:
        extensions[item["extension"]] += 1
        for category, count in item["risk_matches"].items():
            categories[category] += count
            if count and len(category_samples[category]) < 12:
                category_samples[category].append(item["path"])
        for name in item["inert_marketing_names"]:
            inert_names[name] += 1

    return {
        "schema_version": 1,
        "root": str(root.resolve()),
        "summary": {
            "files_analyzed": len(results),
            "total_size_bytes": sum(item["size_bytes"] for item in results),
            "total_lines": sum(item["line_count"] for item in results),
            "registry_keys_observed": sum(item["registry_key_count"] for item in results),
            "registry_values_observed": sum(item["registry_value_count"] for item in results),
            "registry_commands_observed": sum(item["registry_command_count"] for item in results),
            "extensions": dict(extensions.most_common()),
            "risk_matches": dict(categories.most_common()),
            "inert_marketing_names": dict(inert_names.most_common()),
            "category_samples": dict(category_samples),
        },
        "files": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze downloaded public registry/script text without executing it."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
