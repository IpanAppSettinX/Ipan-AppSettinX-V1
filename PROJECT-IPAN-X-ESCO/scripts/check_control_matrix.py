from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "control_matrix.source.json"
OUTPUT = ROOT / "docs" / "CONTROL_MATRIX.md"
HTML = ROOT / "src" / "ipan_optimizer" / "frontend" / "index.html"
JS = ROOT / "src" / "ipan_optimizer" / "frontend" / "js" / "app.js"


class ControlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.controls: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del tag
        values = dict(attrs)
        control_id = values.get("data-control-id")
        if control_id:
            self.controls.append(control_id)


def load_source() -> list[dict[str, object]]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    return list(payload["controls"])


def render_markdown(controls: list[dict[str, object]]) -> str:
    lines = [
        "# Control matrix",
        "",
        "Generated from `docs/control_matrix.source.json`. Do not edit manually.",
        "",
        "| control_id | Route/component | Indonesian label | User intent | Handler | "
        "Bridge method | Backend operation | Risk/permission | States | Verification | "
        "Test IDs |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in controls:
        row = [
            f"`{item['control_id']}`",
            str(item["route"]),
            str(item["label"]),
            str(item["intent"]),
            str(item["handler"]),
            str(item["bridge_method"]),
            str(item["backend_operation"]),
            str(item["risk_permission"]),
            str(item["states"]),
            str(item["verification"]),
            ", ".join(item["test_ids"]),
        ]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    lines.extend(
        [
            "",
            f"Total canonical controls: **{len(controls)}**.",
            "",
        ]
    )
    return "\n".join(lines)


def validate(controls: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    source_ids = [str(item["control_id"]) for item in controls]
    if len(source_ids) != len(set(source_ids)):
        errors.append("Duplicate control_id in control matrix source.")
    parser = ControlParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    static_ids = parser.controls
    if len(static_ids) != len(set(static_ids)):
        errors.append("Duplicate static data-control-id in HTML.")
    canonical_static = {item for item in source_ids if not item.endswith(".*")}
    missing_matrix = sorted(set(static_ids) - canonical_static)
    missing_html = sorted(canonical_static - set(static_ids))
    if missing_matrix:
        errors.append(f"Controls missing from matrix: {missing_matrix}")
    if missing_html:
        errors.append(f"Controls missing from HTML: {missing_html}")
    js = JS.read_text(encoding="utf-8")
    for control_id in static_ids:
        if control_id not in js and control_id not in {
            "profiles.select",
            "game.executable",
            "emulator.instance",
            "emulator.profile",
            "benchmark.label",
            "activity.search",
            "settings.dry_run",
        }:
            errors.append(f"Control ID not referenced by JavaScript: {control_id}")
    bridge_methods = {str(item["bridge_method"]) for item in controls if str(item["bridge_method"])}
    bridge_source = (ROOT / "src" / "ipan_optimizer" / "app" / "api.py").read_text(encoding="utf-8")
    for method in sorted(bridge_methods):
        if not re.search(rf"def {re.escape(method)}\(", bridge_source):
            errors.append(f"Bridge method missing: {method}")
    for item in controls:
        if not item["test_ids"]:
            errors.append(f"Missing test mapping: {item['control_id']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    controls = load_source()
    errors = validate(controls)
    rendered = render_markdown(controls)
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")
    elif not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        errors.append("CONTROL_MATRIX.md is stale; run with --write.")
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"Control matrix valid: {len(controls)} canonical controls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
