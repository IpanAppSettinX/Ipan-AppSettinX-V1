from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return int(connection.getsockname()[1])


def wait_for_cdp(port: int, timeout: float = 25.0) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError("WebView2 remote debugging endpoint tidak tersedia.")


def main() -> int:
    artifacts = ROOT / "artifacts" / "pywebview-smoke"
    artifacts.mkdir(parents=True, exist_ok=True)
    port = free_port()
    environment = os.environ.copy()
    environment["IPAN_OPTIMIZER_DATA_DIR"] = str(artifacts / "data")
    environment["IPAN_OPTIMIZER_REMOTE_DEBUGGING_PORT"] = str(port)
    process = subprocess.Popen(
        [sys.executable, "-m", "ipan_optimizer.main", "--debug"],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    report: dict[str, object] = {
        "process_id": process.pid,
        "console_errors": [],
        "page_errors": [],
        "screenshots": [],
        "terminated_by_harness": False,
    }
    try:
        wait_for_cdp(port)
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            pages = [page for context in browser.contexts for page in context.pages]
            page = next((candidate for candidate in pages if "IPAN" in candidate.title()), None)
            if page is None:
                raise RuntimeError("Page IPAN Optimizer tidak ditemukan pada WebView2.")
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text) if message.type == "error" else None
                ),
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.locator('[data-view="dashboard"]').wait_for(state="visible")
            dashboard = artifacts / "dashboard-1280x800.png"
            page.screenshot(path=dashboard)
            page.locator('[data-control-id="nav.scan"]').click()
            page.locator('[data-control-id="scan.run"]').click()
            page.locator("#scan-status").filter(has_text="rekomendasi siap").wait_for(timeout=30000)
            scan = artifacts / "scan-1280x800.png"
            page.screenshot(path=scan)
            report["console_errors"] = console_errors
            report["page_errors"] = page_errors
            report["screenshots"] = [str(dashboard), str(scan)]
            browser.close()
    finally:
        if process.poll() is None:
            report["terminated_by_harness"] = True
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stdout, stderr = process.communicate()
        report["process_returncode"] = process.returncode
        report["process_exit_expected"] = bool(report["terminated_by_harness"])
        report["stdout"] = stdout[-2000:]
        report["stderr"] = stderr[-2000:]
        (artifacts / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    errors = [*report["console_errors"], *report["page_errors"]]
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
