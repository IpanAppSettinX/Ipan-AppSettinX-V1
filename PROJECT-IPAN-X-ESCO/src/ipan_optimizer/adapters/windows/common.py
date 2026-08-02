from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence


def run_fixed_command(arguments: Sequence[str], *, timeout: float = 8.0) -> str:
    """Run a hard-coded adapter command without a shell."""
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run(  # noqa: S603 - adapter receives fixed argument arrays
        list(arguments),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        creationflags=creation_flags,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(stderr or f"Command failed with exit code {completed.returncode}")
    return completed.stdout.strip()
