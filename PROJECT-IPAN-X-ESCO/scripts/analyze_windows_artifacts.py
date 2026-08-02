from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pefile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    return -sum((count / len(data)) * math.log2(count / len(data)) for count in counts.values())


def printable_strings(data: bytes, minimum: int = 5) -> list[str]:
    ascii_strings = [
        match.decode("ascii", errors="replace")
        for match in re.findall(rb"[\x20-\x7e]{%d,}" % minimum, data)
    ]
    unicode_strings = [
        match.decode("utf-16le", errors="replace")
        for match in re.findall(rb"(?:[\x20-\x7e]\x00){%d,}" % minimum, data)
    ]
    return sorted(set(ascii_strings + unicode_strings))


def analyze_pe(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    pe = pefile.PE(data=data, fast_load=False)
    imports: dict[str, list[str]] = {}
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        library = entry.dll.decode("ascii", errors="replace")
        imports[library] = [
            (
                imported.name.decode("ascii", errors="replace")
                if imported.name
                else f"ordinal:{imported.ordinal}"
            )
            for imported in entry.imports
        ]
    strings = printable_strings(data)
    suspicious_terms = (
        "cmd.exe",
        "powershell",
        "reg.exe",
        "bcdedit",
        "netsh",
        "taskkill",
        "sc.exe",
        "defender",
        "firewall",
        "download",
        "http://",
        "https://",
        "createprocess",
        "shellexecute",
        "virtualalloc",
        "writeprocessmemory",
    )
    suspicious_strings = [
        value for value in strings if any(term in value.casefold() for term in suspicious_terms)
    ]
    timestamp = datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp, tz=UTC)
    sections = [
        {
            "name": section.Name.rstrip(b"\0").decode("ascii", errors="replace"),
            "virtual_size": section.Misc_VirtualSize,
            "raw_size": section.SizeOfRawData,
            "entropy": round(section.get_entropy(), 4),
            "characteristics": f"0x{section.Characteristics:08x}",
        }
        for section in pe.sections
    ]
    overlay_offset = pe.get_overlay_data_start_offset()
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": sha256(path),
        "machine": f"0x{pe.FILE_HEADER.Machine:04x}",
        "subsystem": pe.OPTIONAL_HEADER.Subsystem,
        "compile_timestamp_utc": timestamp.isoformat(),
        "entry_point": f"0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}",
        "image_base": f"0x{pe.OPTIONAL_HEADER.ImageBase:x}",
        "imphash": pe.get_imphash(),
        "sections": sections,
        "whole_file_entropy": round(entropy(data), 4),
        "imports": imports,
        "suspicious_strings": suspicious_strings,
        "all_strings_count": len(strings),
        "overlay_offset": overlay_offset,
        "overlay_size": len(data) - overlay_offset if overlay_offset is not None else 0,
        "has_debug_directory": hasattr(pe, "DIRECTORY_ENTRY_DEBUG"),
        "has_tls": hasattr(pe, "DIRECTORY_ENTRY_TLS"),
        "has_resources": hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"),
    }


def normalize_command(line: str) -> str:
    command = line.strip().lstrip("@").strip()
    if not command or command.startswith(("::", ":", "rem ")):
        return ""
    return command


def analyze_batch(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    commands = [command for line in lines if (command := normalize_command(line))]
    labels = [line.strip()[1:] for line in lines if line.strip().startswith(":")]
    command_heads = Counter(
        re.split(r"[\s/]+", command, maxsplit=1)[0].casefold() for command in commands
    )
    registry_commands = [
        command
        for command in commands
        if re.match(r"(?i)reg(?:\.exe)?\s+(add|delete|copy)", command)
    ]
    registry_paths = []
    registry_values = []
    for command in registry_commands:
        quoted = re.search(r'"([^"]+)"', command)
        if quoted:
            registry_paths.append(quoted.group(1))
        value = re.search(r'(?i)\s/v\s+"?([^"\s]+)"?', command)
        if value:
            registry_values.append(value.group(1))
    patterns = {
        "security_reduction": (
            r"(?i)defender|firewall|disableantispyware|disableantivirus|"
            r"disablerealtimemonitoring|spynet|securityhealth|mpssvc|windefend"
        ),
        "boot_configuration": r"(?i)\bbcdedit\b|\buseplatformclock\b|\bdisabledynamictick\b",
        "destructive_filesystem": r"(?i)\b(?:del|erase|rd|rmdir)\b.*(?:/s|/q|/f)",
        "service_changes": r"(?i)\bsc(?:\.exe)?\s+(?:stop|delete|config)\b|\\services\\.*\bstart\b",
        "network_stack": r"(?i)\bnetsh\b|tcpip\\parameters|defaultttl|tcpwindow|pmtu",
        "package_removal": r"(?i)remove-appxpackage|onedrivesetup\.exe\s+/uninstall",
        "process_termination": r"(?i)\btaskkill\b",
        "downloads_or_remote": r"(?i)https?://|invoke-webrequest|start-bitstransfer|certutil.*urlcache",
        "scheduler_changes": r"(?i)\bschtasks\b.*(?:/delete|/change|/create)",
        "update_reduction": r"(?i)wuauserv|usosvc|windowsupdate|updateorchestrator",
        "hypervisor_changes": r"(?i)hyper-v|hypervisorlaunchtype|vmcompute|hvhost",
    }
    matched: dict[str, list[str]] = {}
    for category, pattern in patterns.items():
        matched[category] = [command for command in commands if re.search(pattern, command)]
    urls = sorted(set(re.findall(r"https?://[^\s\"')]+", text, flags=re.IGNORECASE)))
    obviously_inert_names = sorted(
        {
            value
            for value in registry_values
            if re.search(r"(?i)aim|headshot|recoil|flames|haohao|superidol", value)
        }
    )
    malformed_paths = sorted(
        {
            registry_path
            for registry_path in registry_paths
            if registry_path.casefold().count("hkey_") > 1
            or "\\mouse\\hkey_" in registry_path.casefold()
        }
    )
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": sha256(path),
        "line_count": len(lines),
        "labels_count": len(labels),
        "labels": labels,
        "commands_count": len(commands),
        "command_heads": dict(command_heads.most_common()),
        "registry_commands_count": len(registry_commands),
        "unique_registry_paths_count": len(set(registry_paths)),
        "unique_registry_values_count": len(set(registry_values)),
        "obviously_inert_marketing_value_names": obviously_inert_names,
        "malformed_registry_paths": malformed_paths,
        "risk_matches": matched,
        "urls": urls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static-only Windows artifact analyzer")
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--bat", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "analysis_mode": "static_only_never_executed",
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "pe": analyze_pe(args.exe.resolve(strict=True)),
        "batch": analyze_batch(args.bat.resolve(strict=True)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "pe_sha256": report["pe"]["sha256"],
                "pe_import_libraries": list(report["pe"]["imports"]),
                "pe_suspicious_strings": report["pe"]["suspicious_strings"],
                "batch_sha256": report["batch"]["sha256"],
                "batch_lines": report["batch"]["line_count"],
                "batch_registry_commands": report["batch"]["registry_commands_count"],
                "batch_risk_match_counts": {
                    key: len(value) for key, value in report["batch"]["risk_matches"].items()
                },
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
