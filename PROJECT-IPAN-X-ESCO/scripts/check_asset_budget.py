from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "src" / "ipan_optimizer" / "frontend"


def size_for(suffix: str) -> int:
    return sum(path.stat().st_size for path in FRONTEND.rglob(f"*{suffix}"))


def main() -> int:
    js = size_for(".js")
    css = size_for(".css")
    html = size_for(".html")
    images = sum(size_for(suffix) for suffix in (".jpg", ".jpeg", ".png", ".svg", ".webp"))
    total = js + css + html + images
    limits = {"js": 180 * 1024, "css": 100 * 1024, "total": 500 * 1024}
    values = {"js": js, "css": css, "total": total}
    failed = [name for name, value in values.items() if value > limits[name]]
    print(
        f"HTML={html} bytes CSS={css} bytes JS={js} bytes images={images} bytes total={total} bytes"
    )
    if failed:
        print(f"Budget exceeded: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
