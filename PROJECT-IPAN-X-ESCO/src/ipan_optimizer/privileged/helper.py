from __future__ import annotations

import argparse
from pathlib import Path

from ipan_optimizer.privileged.runner import execute_plan_file


def main() -> int:
    parser = argparse.ArgumentParser(description="IPAN Optimizer elevated helper")
    parser.add_argument("--apply-plan", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    return execute_plan_file(Path(args.apply_plan), Path(args.result))


if __name__ == "__main__":
    raise SystemExit(main())
