from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="IPAN Optimizer elevated helper")
    parser.add_argument("--transaction-id", required=True)
    parser.add_argument("--nonce", required=True)
    parser.parse_args()
    # Real IPC/execution is deliberately release-gated. Packaging a helper entry
    # point does not grant it a generic command or filesystem interface.
    print("Helper nyata belum diaktifkan; tidak ada perubahan yang dijalankan.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
