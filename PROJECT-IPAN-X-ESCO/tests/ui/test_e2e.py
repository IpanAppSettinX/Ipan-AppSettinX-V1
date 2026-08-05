from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "src" / "ipan_optimizer" / "frontend"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        del format, args


@contextlib.contextmanager
def frontend_server() -> Iterator[str]:
    handler = lambda *args, **kwargs: QuietHandler(  # noqa: E731
        *args,
        directory=str(FRONTEND),
        **kwargs,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def click(page: Page, control_id: str) -> None:
    page.locator(f'[data-control-id="{control_id}"]').click()


@pytest.mark.ui
def test_primary_workflows_have_no_browser_errors(tmp_path: Path) -> None:
    edge_candidates = [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        *sorted(
            (Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "EdgeCore").glob(
                "*/msedge.exe"
            ),
            reverse=True,
        ),
    ]
    edge = next((candidate for candidate in edge_candidates if candidate.is_file()), None)
    if edge is None:
        pytest.skip("Microsoft Edge tidak tersedia untuk Playwright UI test.")
    console_errors: list[str] = []
    page_errors: list[str] = []
    external_requests: list[str] = []
    with frontend_server() as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(edge), headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.emulate_media(reduced_motion="reduce")
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external_requests.append(request.url)
                if not request.url.startswith("http://127.0.0.1:")
                else None
            ),
        )
        page.goto(url, wait_until="domcontentloaded")
        page.locator("#startup-screen").wait_for(state="hidden", timeout=30000)
        page.locator("#login-screen").wait_for(state="visible")
        assert page.locator("#login-title").inner_text() == "Masuk ke Ipan AppSettinX."
        assert page.locator(".login-heading p").inner_text() == (
            "Daftar Akun untuk merasakan Benefit Dari AppSensiX, Optimize Boost FPS "
            "dan Optimize emulator dari IpanAppSettinX."
        )
        assert page.get_by_text("Lupa password").count() == 0
        assert page.locator(".protection-chain").count() == 0
        assert page.locator(".chain-heading").count() == 0
        assert page.locator(".login-windowbar.pywebview-drag-region").count() == 1
        assert page.locator('[data-control-id="auth.window_minimize"]').count() == 1
        assert page.locator('[data-control-id="auth.window_maximize"]').count() == 1
        assert page.locator('[data-control-id="auth.window_close"]').count() == 1
        assert page.locator('[data-control-id="auth.login"]').inner_text().startswith("Login")
        assert "Initialize" not in page.locator('[data-control-id="auth.login"]').inner_text()
        assert (
            page.locator('[data-control-id="auth.register"] small').inner_text()
            == "Bayar sekali, pakai selamanya"
        )
        assert page.locator('[data-control-id="auth.reset_hwid"] small').inner_text() == (
            "Akun bermasalah, atau ganti windows dan akun tidak bisa dipakai? langsung "
            "Reset HWID aja! Bayar sekali, pakai selamanya"
        )
        assert (
            page.locator(".hw-terminal-head img")
            .get_attribute("src")
            .endswith("ipan-store-logo.png")
        )
        title = page.locator(".hw-term-title")
        title.wait_for(state="visible")
        assert title.inner_text() == "IPAN APP SETTINX // SYSTEM DIAGNOSTIC"
        assert "Cascadia" in title.evaluate("element => getComputedStyle(element).fontFamily")
        page.locator(".hw-term-title.is-complete").wait_for(timeout=3000)
        page.wait_for_timeout(3500)
        assert title.inner_text() == "IPAN APP SETTINX // SYSTEM DIAGNOSTIC"
        assert page.locator(".hw-term-live").inner_text() == "LIVE"
        assert page.locator('[data-control-id="auth.terminal_toggle"]').count() == 0
        page.locator("#hw-log .hw-line").first.wait_for()
        assert page.locator("#hw-log .hw-line").count() == 1
        assert page.locator("#hw-log .hw-tag").inner_text() != ""
        assert page.locator("#hw-log .hw-status").inner_text() in {"", "[OK]", "[WAIT]"}
        assert page.locator(".hw-terminal-body").evaluate("element => element.clientHeight <= 120")
        assert page.locator(".hw-terminal-foot").inner_text() == (
            "© 2026 Ipan AppSettinX — All Rights Reserved"
        )
        page.locator('#hw-log[data-stage="cpu"]').wait_for(timeout=30000)
        assert page.locator("#hw-log .hw-line").count() == 1
        assert (
            page.locator(".hw-line").evaluate(
                "element => parseFloat(getComputedStyle(element).fontSize)"
            )
            >= 10
        )
        assert (
            page.locator(".login-form label").first.evaluate(
                "element => parseFloat(getComputedStyle(element).fontSize)"
            )
            >= 14
        )
        assert (
            page.locator(".login-link small").first.evaluate(
                "element => parseFloat(getComputedStyle(element).fontSize)"
            )
            >= 12
        )
        for selector in [".hw-terminal", ".login-content", ".login-actions"]:
            assert page.locator(selector).evaluate(
                "element => element.scrollWidth <= element.clientWidth + 1"
            )
        for action in page.locator(".login-link").all():
            copy_box = action.locator(".login-link-copy").bounding_box()
            cta_box = action.locator(".login-link-cta").bounding_box()
            assert copy_box is not None and cta_box is not None
            assert copy_box["x"] + copy_box["width"] <= cta_box["x"] + 1
        page.set_viewport_size({"width": 1024, "height": 640})
        for selector in [".hw-terminal", ".login-content", ".login-actions"]:
            assert page.locator(selector).evaluate(
                "element => element.scrollWidth <= element.clientWidth + 1"
            )
        assert page.locator(".login-panel").evaluate(
            "element => element.scrollHeight >= element.clientHeight"
        )
        for action in page.locator(".login-link").all():
            copy_box = action.locator(".login-link-copy").bounding_box()
            cta_box = action.locator(".login-link-cta").bounding_box()
            assert copy_box is not None and cta_box is not None
            assert copy_box["x"] + copy_box["width"] <= cta_box["x"] + 1
        page.set_viewport_size({"width": 1280, "height": 800})
        assert page.locator("label[for='login-username']").inner_text().startswith("Username")
        assert page.locator("label[for='login-password']").inner_text().startswith("Password")
        assert page.locator("label[for='login-license']").inner_text().startswith("License Key")
        assert page.get_by_text("20T", exact=True).count() == 0
        assert page.get_by_text("DDR5", exact=True).count() == 0
        assert (
            page.locator('[data-control-id="auth.register"]')
            .get_attribute("data-support-url")
            .startswith("https://wa.me/6281910123632")
        )
        assert (
            page.locator('[data-control-id="auth.reset_hwid"]')
            .get_attribute("data-support-url")
            .startswith("https://wa.me/6281910123632")
        )
        page.locator("#login-username").fill("fixture-member@example.com")
        page.locator("#login-password").fill("fixture-password")
        page.locator("#login-license").fill("FIXTURE-LICENSE-KEY")
        click(page, "auth.login")
        page.locator(".login-optimizer").wait_for(state="visible")
        assert page.locator(".auth-trace .auth-trace-row").count() == 4
        page.locator("#login-status").filter(has_text="aplikasi desktop").wait_for()
        assert page.locator(".app-shell").get_attribute("aria-hidden") == "true"
        login_maximize = page.locator('[data-control-id="auth.window_maximize"]')
        assert login_maximize.get_attribute("aria-label") == "Maximize"
        login_maximize.click()
        page.wait_for_timeout(100)
        assert login_maximize.get_attribute("aria-label") == "Restore"
        assert page.locator("body").get_attribute("data-maximized") == "true"
        assert (
            page.locator("body").evaluate(
                "element => getComputedStyle(document.querySelector('.resize-zone-top')).display"
            )
            == "none"
        )
        page.locator("body").evaluate("element => { element.dataset.maximized = 'false'; }")
        assert (
            page.locator("body").evaluate("element => getComputedStyle(element).userSelect")
            == "text"
        )
        page.locator("#login-screen").evaluate("element => { element.hidden = true; }")
        page.locator(".app-shell").evaluate(
            "element => { element.removeAttribute('aria-hidden'); }"
        )
        page.locator('[data-view="dashboard"]').wait_for(state="visible")
        shell_maximize = page.locator('[data-control-id="window.maximize"]')
        assert shell_maximize.get_attribute("aria-label") == "Restore"
        shell_maximize.click()
        page.wait_for_timeout(100)
        assert shell_maximize.get_attribute("aria-label") == "Restore"
        page.locator("body").evaluate("element => { element.dataset.maximized = 'false'; }")
        hero_copy = page.locator('[data-view="dashboard"] .hero-copy p').inner_text()
        assert "PC lo" in hero_copy
        assert "Langsung pakai." in hero_copy
        assert "rig lo" not in hero_copy

        click(page, "nav.scan")
        click(page, "scan.run")
        page.locator("#scan-status").filter(has_text="Scan selesai").wait_for()
        assert page.locator(".hw-icon img").count() == 5
        first_icon = page.locator(".hw-icon img").first.get_attribute("src")
        assert first_icon is not None
        assert "fluent/" in first_icon

        click(page, "nav.tweaks")
        page.locator("#tweak-status").filter(has_text="tweak ditampilkan").wait_for()
        titles = page.locator("#tweak-list .tweak-card h2").all_inner_texts()
        assert titles == [
            "1 APPLY REGEDIT",
            "2 CLEAN TEMP FILES",
            "3 APPLY BOOSTER",
            "4 REVERT ALL CHANGES",
            "5 CLEAN LOG FILES",
        ]
        assert page.get_by_text("(NEW!)").count() == 0
        assert page.locator("#tweak-list .inspected-scope").count() == 5
        visible_tweak_copy = page.locator("#tweak-list").inner_text().casefold()
        forbidden_tweak_terms = [
            "%homepath%",
            "%temp%",
            "deletevalue",
            "filesystem:",
            "game dvr",
            "hkcu",
            "hklm",
            "nolazymode",
            "registry:",
            "services:",
            "superfetch",
        ]
        assert not any(term in visible_tweak_copy for term in forbidden_tweak_terms)
        critical_button = page.locator('[data-control-id="tweak.action.cleanup.clean_temp_files"]')
        standard_button = page.locator('[data-control-id="tweak.action.system.apply_regedit"]')
        critical_color = critical_button.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        standard_color = standard_button.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        assert critical_color != standard_color

        click(page, "nav.profiles")
        assert page.locator('[data-view="profiles"] .page-header h1').inner_text() == "AppSensiX"
        assert page.locator('[data-view="profiles"] .tweak-card h2').all_inner_texts() == [
            "OneTap Vector X",
            "Neural AimSync X",
            "DragShot Velocity X",
            "Emulator Overdrive X",
        ]
        assert page.locator('[data-view="profiles"] .tweak-card button').all_inner_texts() == [
            "Apply Tweak",
            "Apply Tweak",
            "Apply Tweak",
            "Apply Tweak",
        ]
        click(page, "gaming.aim_stabilizer")
        page.locator("#apply-process-dialog").wait_for(state="visible", timeout=30000)
        click(page, "process.close")
        click(page, "gaming.aim_smooth")
        page.locator("#apply-process-dialog").wait_for(state="visible", timeout=30000)
        click(page, "process.close")
        click(page, "gaming.easy_drag")
        page.locator("#apply-process-dialog").wait_for(state="visible", timeout=30000)
        click(page, "process.close")

        click(page, "gaming.boost_fps_menu")
        page.locator("#apply-process-dialog").wait_for(state="visible", timeout=30000)
        click(page, "process.close")

        click(page, "nav.emulator")
        click(page, "emulator.discover")
        page.locator("#emulator-status").filter(has_text="Pencarian selesai").wait_for()
        click(page, "process.close")

        click(page, "nav.restore")
        click(page, "restore.open")
        page.locator("#restore-status").filter(has_text="System Restore").wait_for()

        click(page, "nav.fixes")
        fixes_copy = page.locator('[data-view="fixes"]').inner_text()
        assert "kamera" in fixes_copy.casefold()
        assert "OBS" in fixes_copy
        assert all(term not in fixes_copy for term in ("HKCU", "HKLM", "GameDVR"))

        click(page, "nav.advanced")
        page.locator("#advanced-status").filter(has_text="advanced tweak ditampilkan").wait_for()
        first_advanced_action = page.locator(
            '#advanced-list [data-control-id^="advanced.action."]'
        ).first
        assert first_advanced_action.inner_text() == "Apply Tweak"
        page.locator('[data-control-id="advanced.filter"]').select_option("Security")
        page.locator('[data-control-id="advanced.action.adv.turn_off_defender"]').click()
        page.locator("#apply-process-title").filter(has_text="tidak diterapkan").wait_for()
        click(page, "process.close")
        page.locator('[data-control-id="advanced.filter"]').select_option("")

        click(page, "nav.activity")
        click(page, "activity.refresh")
        page.locator("#activity-list").wait_for(state="visible")

        click(page, "nav.settings")
        page.locator('[data-control-id="settings.theme"]').check()
        assert page.locator("html").get_attribute("data-theme") == "light"
        assert page.locator(".sidebar").evaluate(
            "element => getComputedStyle(element).backgroundColor !== "
            "getComputedStyle(document.body).backgroundColor"
        )
        click(page, "settings.save")
        page.locator("#settings-status").filter(has_text="tersimpan").wait_for()

        click(page, "nav.evidence")
        assert page.locator(".support-heading .status-badge").inner_text() == "Official Partner"
        assert (
            page.locator(".support-heading").evaluate(
                "element => getComputedStyle(element).justifyContent"
            )
            == "flex-start"
        )
        assert page.get_by_text("Mengapa memilih Ipan AppSettinX V1?").is_visible()
        assert page.get_by_text("Buka evidence resmi").count() == 0
        assert page.get_by_text("Buka sumber resmi").count() == 0
        for control_id in (
            "support.website",
            "support.whatsapp",
            "support.discord",
            "support.instagram",
            "support.tiktok",
            "support.whatsapp_channel",
        ):
            click(page, control_id)
            page.locator("#evidence-status").filter(has_text="dibuka").wait_for()

        screenshot_dir = tmp_path / "screenshots"
        screenshot_dir.mkdir()
        for width, height in ((1024, 700), (1280, 800), (1440, 900)):
            page.set_viewport_size({"width": width, "height": height})
            click(page, "nav.dashboard")
            page.screenshot(path=screenshot_dir / f"dashboard-{width}x{height}.png")
        page.set_viewport_size({"width": 1280, "height": 800})
        click(page, "nav.tweaks")
        page.wait_for_timeout(350)
        page.screenshot(path=screenshot_dir / "tweak-library-1280x800.png")
        click(page, "nav.evidence")
        page.wait_for_timeout(350)
        page.screenshot(path=screenshot_dir / "about-support-1280x800.png")

        browser.close()
    assert not console_errors
    assert not page_errors
    assert not external_requests


def test_startup_progress_does_not_freeze_on_slow_backend() -> None:
    edge_candidates = [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        *sorted(
            (Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "EdgeCore").glob(
                "*/msedge.exe"
            ),
            reverse=True,
        ),
    ]
    edge = next((candidate for candidate in edge_candidates if candidate.is_file()), None)
    if edge is None:
        pytest.skip("Microsoft Edge tidak tersedia untuk Playwright UI test.")
    with frontend_server() as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(edge), headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        hooks_js_path = Path(__file__).parent / "freeze_test_hooks.js"
        hooks_js_body = hooks_js_path.read_text(encoding="utf-8")

        def handle_route(route):
            request = route.request
            if request.resource_type == "document":
                original = route.fetch()
                body = original.body().decode("utf-8")
                inject_tag = (
                    '<script src="js/freeze_test_hooks.js"></script>\n'
                    '<script type="module" src="js/app.js"></script>'
                )
                body = body.replace(
                    '<script type="module" src="js/app.js"></script>',
                    inject_tag,
                )
                headers = dict(original.headers)
                headers.pop("content-security-policy", None)
                headers.pop("content-security-policy-report-only", None)
                route.fulfill(status=200, body=body, headers=headers)
            elif request.url.endswith("freeze_test_hooks.js"):
                route.fulfill(
                    status=200,
                    body=hooks_js_body,
                    headers={"Content-Type": "application/javascript"},
                )
            else:
                route.continue_()

        page.route("**/*", handle_route)
        page.emulate_media(reduced_motion="reduce")
        page.goto(url, wait_until="domcontentloaded")
        page.locator("#startup-screen").wait_for(state="visible", timeout=10000)
        page.locator("#startup-screen").wait_for(state="hidden", timeout=60000)
        page.locator("#login-screen").wait_for(state="visible", timeout=5000)
        samples = page.evaluate("window.__startupFreezeTest.samples")
        assert isinstance(samples, list) and len(samples) >= 4
        progress_values = [float(entry["width"]) for entry in samples]
        for i in range(1, len(progress_values)):
            previous, current = progress_values[i - 1], progress_values[i]
            assert current >= previous - 1, (
                f"progress mundur pada sample {i}: {previous} -> {current}"
            )
        assert progress_values[-1] >= 40, (
            "progress harus mencapai minimal 40% sebelum complete, "
            f"tetapi berhenti di {progress_values[-1]}"
        )
        assert page.locator("#login-title").inner_text() == "Masuk ke Ipan AppSettinX."
        browser.close()


@pytest.mark.ui
def test_login_success_unlocks_app_shell(tmp_path: Path) -> None:
    edge_candidates = [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        *sorted(
            (Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "EdgeCore").glob(
                "*/msedge.exe"
            ),
            reverse=True,
        ),
    ]
    edge = next((candidate for candidate in edge_candidates if candidate.is_file()), None)
    if edge is None:
        pytest.skip("Microsoft Edge tidak tersedia untuk Playwright UI test.")
    with frontend_server() as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(edge), headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.emulate_media(reduced_motion="reduce")
        page.goto(url, wait_until="domcontentloaded")
        page.locator("#login-screen").wait_for(state="visible", timeout=30000)
        page.evaluate(
            """() => {
                window.pywebview = {
                    api: {
                        async authenticate() {
                            return {
                                success: true,
                                data: { email: "member@example.com", state: "AUTHORIZED" },
                                error: null,
                            };
                        },
                    },
                };
            }"""
        )
        page.locator("#login-username").fill("member@example.com")
        page.locator("#login-password").fill("password-valid")
        page.locator("#login-license").fill("IPAN-KEY-001")
        click(page, "auth.login")
        page.locator("#login-screen").wait_for(state="hidden", timeout=10000)
        assert page.locator(".app-shell").get_attribute("aria-hidden") != "true"
        page.locator('[data-view="dashboard"]').wait_for(state="visible")
        browser.close()
