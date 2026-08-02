from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "src" / "ipan_optimizer" / "frontend"
TEXT_EXTENSIONS = frozenset({".css", ".html", ".js", ".json", ".svg"})


def main() -> int:
    errors: list[str] = []
    for path in FRONTEND.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        for forbidden in ('href="#"', "javascript:", "linear-gradient", "radial-gradient"):
            if forbidden in lowered:
                errors.append(f"{path.relative_to(ROOT)} contains {forbidden}")
        if path.suffix == ".html" and re.search(r"\son[a-z]+\s*=", lowered):
            errors.append(f"{path.relative_to(ROOT)} contains inline event handlers")
        if (
            path.suffix == ".css"
            and path.name != "tokens.css"
            and re.search(r"#[0-9a-fA-F]{3,8}\b", text)
        ):
            errors.append(f"{path.relative_to(ROOT)} contains a random hex color")
    if errors:
        print("\n".join(errors))
        return 1
    print("Frontend policy valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
