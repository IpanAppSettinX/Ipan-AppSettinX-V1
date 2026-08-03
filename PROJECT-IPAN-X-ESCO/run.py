# ruff: noqa: E402, I001
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ipan_optimizer.main import main


if __name__ == "__main__":
    raise SystemExit(main())
