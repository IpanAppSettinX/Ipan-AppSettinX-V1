from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import ValidationError

from ipan_optimizer.app.auth import authenticate
from ipan_optimizer.app.service import OptimizerService
from ipan_optimizer.core.advanced_catalog import list_advanced_tweaks
from ipan_optimizer.core.rules import PROFILES
from ipan_optimizer.core.tweak_catalog import list_tweak_catalog
from ipan_optimizer.domain.models import ApiError, ApiResponse


class ApiBridge:
    def __init__(self, service: OptimizerService) -> None:
        self.service = service
        self._window: Any | None = None

    def _call(self, function: Callable[[], Any]) -> dict[str, Any]:
        try:
            data = function()
            if hasattr(data, "model_dump"):
                data = data.model_dump(mode="json")
            return ApiResponse(success=True, data=data).model_dump(mode="json")
        except (KeyError, ValueError, ValidationError) as exc:
            return ApiResponse(
                success=False,
                error=ApiError(
                    code="VALIDATION_ERROR",
                    user_message=str(exc).strip("'"),
                    developer_detail=type(exc).__name__,
                ),
            ).model_dump(mode="json")
        except Exception as exc:
            return ApiResponse(
                success=False,
                error=ApiError(
                    code="BACKEND_ERROR",
                    user_message="Operasi gagal dengan aman.",
                    developer_detail=f"{type(exc).__name__}: {exc}",
                    retryable=True,
                ),
            ).model_dump(mode="json")

    def scan_system(self) -> dict[str, Any]:
        return self._call(self.service.scan_system)

    def authenticate(self, username: str, password: str, license_key: str = "") -> dict[str, Any]:
        return self._call(lambda: authenticate(username, password, license_key))

    def get_scan_result(self, scan_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.get_scan(scan_id))

    def list_recommendations(self, scan_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.recommendations(scan_id))

    def list_profiles(self) -> dict[str, Any]:
        return self._call(lambda: PROFILES)

    def list_tweak_catalog(self) -> dict[str, Any]:
        return self._call(list_tweak_catalog)

    def apply_tweak(self, tweak_id: str) -> dict[str, Any]:
        def execute() -> dict[str, object]:
            from ipan_optimizer.core.tweak_catalog import get_tweak
            from ipan_optimizer.core.tweak_engine import execute_tweak, result_to_dict

            tweak = get_tweak(tweak_id)
            result = execute_tweak(tweak_id, tweak.title)
            self.service._log_activity(
                "tweak",
                result.message,
                tweak_id=tweak_id,
                title=tweak.title,
                applied=result.applied,
                failed=result.failed,
            )
            return result_to_dict(result)

        return self._call(execute)

    def list_advanced_tweaks(self) -> dict[str, Any]:
        return self._call(list_advanced_tweaks)

    def apply_advanced_tweak(self, tweak_id: str) -> dict[str, Any]:
        def execute() -> dict[str, object]:
            from ipan_optimizer.core.advanced_catalog import get_advanced_tweak
            from ipan_optimizer.core.tweak_engine import execute_tweak, result_to_dict

            tweak = get_advanced_tweak(tweak_id)
            result = execute_tweak(tweak_id, tweak.title)
            self.service._log_activity(
                "advanced_tweak",
                result.message,
                tweak_id=tweak_id,
                title=tweak.title,
                applied=result.applied,
                failed=result.failed,
            )
            return result_to_dict(result)

        return self._call(execute)

    def scan_hardware(self) -> dict[str, Any]:
        return self._call(self.service.scan_hardware)

    def save_remember(
        self, username: str, password: str, license_key: str, expires_at: float
    ) -> dict[str, Any]:
        return self._call(
            lambda: self.service.save_remember(username, password, license_key, expires_at)
        )

    def load_remember(self) -> dict[str, Any]:
        return self._call(self.service.load_remember)

    def get_realtime_stats(self) -> dict[str, Any]:
        return self._call(self.service.get_realtime_stats)

    def open_system_restore(self) -> dict[str, Any]:
        def open_restore() -> dict[str, object]:
            import os
            import sys

            self.service._log_activity("recovery", "System Restore dibuka.")
            if sys.platform != "win32":
                return {"opened": False, "target": "SystemPropertiesProtection.exe"}
            os.startfile("SystemPropertiesProtection.exe")  # noqa: S606, S607
            return {"opened": True, "target": "SystemPropertiesProtection.exe"}

        return self._call(open_restore)

    def preview_transaction(
        self,
        rule_ids: list[str],
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        del profile_id
        return self._call(lambda: self.service.transactions.preview(rule_ids))

    def apply_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.transactions.apply(transaction_id))

    def start_apply_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._call(
            lambda: self.service.jobs.submit_progress(
                "Menunggu pemeriksaan transaksi.",
                lambda progress: self.service.transactions.apply(transaction_id, progress),
            )
        )

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.jobs.get(job_id))

    def get_transaction_status(self, transaction_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.transactions.get(transaction_id))

    def keep_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.transactions.keep(transaction_id))

    def rollback_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.transactions.rollback(transaction_id))

    def list_recovery_items(self) -> dict[str, Any]:
        return self._call(self.service.transactions.list_recovery_items)

    def apply_gaming_tweak(self, tweak_id: str) -> dict[str, Any]:
        def execute() -> dict[str, object]:
            from ipan_optimizer.core.tweak_engine import execute_tweak, result_to_dict

            titles = {
                "aim_smooth": "OneTap Vector X",
                "aim_stabilizer": "Neural AimSync X",
                "easy_drag": "DragShot Velocity X",
                "boost_fps_menu": "Emulator Overdrive X",
            }
            title = titles.get(tweak_id, tweak_id)
            result = execute_tweak(tweak_id, title)
            self.service._log_activity(
                "gaming_tweak",
                result.message,
                tweak_id=tweak_id,
                title=title,
                applied=result.applied,
                failed=result.failed,
            )
            return result_to_dict(result)

        return self._call(execute)

    def apply_emulator_tweak(self, tweak_id: str) -> dict[str, Any]:
        def execute() -> dict[str, object]:
            from ipan_optimizer.core.tweak_engine import execute_tweak, result_to_dict

            titles = {
                "emulator.bluestacks5": "BlueStacks 5 Optimizer",
                "emulator.msi_app_player": "MSI App Player Optimizer",
            }
            title = titles.get(tweak_id, tweak_id)
            result = execute_tweak(tweak_id, title)
            self.service._log_activity(
                "emulator_tweak",
                result.message,
                tweak_id=tweak_id,
                title=title,
                applied=result.applied,
                failed=result.failed,
            )
            return result_to_dict(result)

        return self._call(execute)

    def apply_fix_tweak(self, tweak_id: str) -> dict[str, Any]:
        def execute() -> dict[str, object]:
            from ipan_optimizer.core.tweak_engine import execute_tweak, result_to_dict

            titles = {
                "fixes.camera": "Fix Camera All Windows",
                "fixes.obs_screenshot": "Fix OBS STUDIO Dan fitur screen shoot",
            }
            title = titles.get(tweak_id, tweak_id)
            result = execute_tweak(tweak_id, title)
            self.service._log_activity(
                "fix_tweak",
                result.message,
                tweak_id=tweak_id,
                title=title,
                applied=result.applied,
                failed=result.failed,
            )
            return result_to_dict(result)

        return self._call(execute)

    def discover_emulators(self) -> dict[str, Any]:
        return self._call(self.service.discover_emulators)

    def get_emulator_instances(self, product_id: str) -> dict[str, Any]:
        del product_id
        return self._call(lambda: [])

    def preview_emulator_profile(
        self,
        instance_id: str,
        profile_id: str,
    ) -> dict[str, Any]:
        return self._call(
            lambda: {
                "instance_id": instance_id,
                "profile_id": profile_id,
                "state": "UNKNOWN_READ_ONLY",
                "message": "Instance belum dikenali; tidak ada perubahan.",
            }
        )

    def apply_emulator_profile(
        self,
        instance_id: str,
        profile_id: str,
    ) -> dict[str, Any]:
        return self._call(
            lambda: {
                "instance_id": instance_id,
                "profile_id": profile_id,
                "state": "UNKNOWN_READ_ONLY",
                "message": "Apply ditolak: schema instance belum dikenali.",
            }
        )

    def verify_emulator_profile(self, instance_id: str) -> dict[str, Any]:
        return self._call(
            lambda: {
                "instance_id": instance_id,
                "state": "UNKNOWN_READ_ONLY",
                "message": "Tidak ada perubahan yang dapat diverifikasi.",
            }
        )

    def restore_emulator_profile(self, instance_id: str) -> dict[str, Any]:
        return self._call(
            lambda: {
                "instance_id": instance_id,
                "state": "UNKNOWN_READ_ONLY",
                "message": "Tidak ada snapshot emulator yang dapat dipulihkan.",
            }
        )

    def start_benchmark(self, config: dict[str, object]) -> dict[str, Any]:
        return self._call(lambda: self.service.start_benchmark(config))

    def cancel_benchmark(self, benchmark_id: str) -> dict[str, Any]:
        def cancel() -> dict[str, object]:
            benchmark = self.service.benchmarks.get(benchmark_id)
            if benchmark is None:
                raise KeyError("Benchmark tidak ditemukan.")
            benchmark["state"] = "CANCELLED"
            return benchmark

        return self._call(cancel)

    def get_benchmark_status(self, benchmark_id: str) -> dict[str, Any]:
        return self._call(lambda: self.service.benchmarks[benchmark_id])

    def compare_benchmarks(self, ids: list[str]) -> dict[str, Any]:
        return self._call(lambda: self.service.compare_benchmarks(ids))

    def list_activity_events(self, filter_value: str = "") -> dict[str, Any]:
        return self._call(
            lambda: [
                item
                for item in self.service.activity
                if filter_value.casefold() in str(item).casefold()
            ]
        )

    def get_settings(self) -> dict[str, Any]:
        return self._call(lambda: dict(self.service.settings))

    def save_settings(self, settings: dict[str, object]) -> dict[str, Any]:
        def save() -> dict[str, object]:
            if settings.get("dry_run") is not True:
                raise ValueError("Real Apply belum tersedia pada build ini.")
            self.service.settings.update(settings)
            self.service._log_activity("settings", "Pengaturan diperbarui.")
            return dict(self.service.settings)

        return self._call(save)

    def export_diagnostic_report(self, options: dict[str, object]) -> dict[str, Any]:
        return self._call(lambda: {"path": self.service.export_report(options)})

    def open_evidence_url(self, url: str) -> dict[str, Any]:
        allowlist = {
            "https://support.xbox.com/en-US/help/games-apps/"
            "game-setup-and-play/use-game-mode-gaming-on-pc",
            "https://learn.microsoft.com/en-us/windows-hardware/design/"
            "device-experiences/powercfg-command-line-options",
            "https://pywebview.flowrl.com/guide/architecture",
            "https://learn.microsoft.com/en-us/windows/win32/api/winuser/"
            "nf-winuser-systemparametersinfoa",
            "https://support.microsoft.com/en-us/windows/hardware/input-devices/"
            "change-mouse-settings",
            "https://learn.microsoft.com/en-us/windows/client-management/mdm/"
            "policy-csp-applicationmanagement",
            "https://learn.microsoft.com/en-us/defender-endpoint/"
            "manage-tamper-protection-individual-device",
            "https://support.microsoft.com/windows/"
            "firewall-network-protection-in-the-windows-security-app",
            "https://support.microsoft.com/windows/windows-update-faq",
            "https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/bcdedit--set",
            "https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys",
            "https://learn.microsoft.com/en-us/windows/win32/services/service-programs",
            "https://support.microsoft.com/en-us/windows/free-up-drive-space-in-windows",
        }

        def open_url() -> dict[str, object]:
            if url not in allowlist:
                raise ValueError("URL evidence tidak berada dalam allowlist.")
            import webbrowser

            opened = webbrowser.open(url, new=2)
            return {"opened": opened, "url": url}

        return self._call(open_url)

    def open_windows_mouse_settings(self) -> dict[str, Any]:
        def open_settings() -> dict[str, object]:
            import os
            import sys

            if sys.platform != "win32":
                return {"opened": False, "target": "ms-settings:mousetouchpad"}
            os.startfile("ms-settings:mousetouchpad")  # noqa: S606, S607
            return {"opened": True, "target": "ms-settings:mousetouchpad"}

        return self._call(open_settings)

    def open_support_url(self, url: str) -> dict[str, Any]:
        allowlist = {
            "https://ipanstore.my.id/",
            "https://wa.me/6288976496870",
            "https://discord.gg/FTQVJQEAtu",
            "https://www.instagram.com/ipaan.18/",
            "https://www.tiktok.com/@ipann.18",
            "https://whatsapp.com/channel/0029Vb54vP4JkK7CBBrxGf0r",
            (
                "https://wa.me/6281910123632?text=Halo%20Ipan%20Store%2C%20saya%20ingin%20"
                "membeli%20dan%20mendaftarkan%20akun%20Ipan%20AppSettinX."
            ),
            (
                "https://wa.me/6281910123632?text=Halo%20Ipan%20Store%2C%20saya%20ingin%20"
                "mengajukan%20Reset%20HWID%20akun%20Ipan%20AppSettinX."
            ),
        }

        def open_url() -> dict[str, object]:
            if url not in allowlist:
                raise ValueError("URL support tidak berada dalam allowlist.")
            import webbrowser

            opened = webbrowser.open(url, new=2)
            return {"opened": opened, "url": url}

        return self._call(open_url)

    def minimize_window(self) -> dict[str, object]:
        def action() -> dict[str, object]:
            hwnd = self._find_hwnd()
            if hwnd:
                import ctypes

                # SW_MINIMIZE works from every window state, including
                # maximized frameless windows where the pywebview helper can
                # silently no-op.
                ctypes.windll.user32.ShowWindow(hwnd, 6)
                return {"minimized": True}
            if self._window is None:
                raise RuntimeError("Window belum tersedia.")
            self._window.minimize()
            return {"minimized": True}

        return self._call(action)

    def maximize_window(self) -> dict[str, object]:
        def action() -> dict[str, object]:
            hwnd = self._find_hwnd()
            if hwnd:
                import ctypes

                user32 = ctypes.windll.user32
                if user32.IsZoomed(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    return {"maximized": False, "restored": True}
                user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                return {"maximized": True}
            if self._window is None:
                raise RuntimeError("Window belum tersedia.")
            self._window.maximize()
            return {"maximized": True}

        return self._call(action)

    def restore_window(self) -> dict[str, object]:
        def action() -> dict[str, object]:
            if self._window is None:
                raise RuntimeError("Window belum tersedia.")
            self._window.restore()
            return {"restored": True}

        return self._call(action)

    def close_window(self) -> dict[str, object]:
        def action() -> dict[str, object]:
            if self._window is None:
                raise RuntimeError("Window belum tersedia.")
            self._window.destroy()
            return {"closed": True}

        return self._call(action)

    _RESIZE_DIRECTIONS: ClassVar[dict[str, int]] = {
        "left": 1,
        "right": 2,
        "top": 3,
        "top_left": 4,
        "top_right": 5,
        "bottom": 6,
        "bottom_left": 7,
        "bottom_right": 8,
    }
    _WINDOW_TITLE = "Ipan AppSettinX"

    def _find_hwnd(self) -> int:
        import ctypes

        cached: int = getattr(self, "_hwnd", 0)
        if cached:
            return cached
        hwnd = ctypes.windll.user32.FindWindowW(None, self._WINDOW_TITLE)
        if hwnd:
            self._hwnd = int(hwnd)
        return int(hwnd or 0)

    def _ensure_resize_style(self, hwnd: int) -> None:
        """Give the frameless window a sizing border style once.

        ``WS_THICKFRAME`` lets the native ``SC_SIZE`` modal loop resize the
        window while the frameless chrome stays invisible.
        """
        if getattr(self, "_resize_style_ready", False):
            return
        import ctypes

        gwl_style = -16
        ws_thickframe = 0x00040000
        ws_maximizebox = 0x00010000
        ws_minimizebox = 0x00020000
        user32 = ctypes.windll.user32
        is_x64 = ctypes.sizeof(ctypes.c_void_p) == 8
        get_fn = user32.GetWindowLongPtrW if is_x64 else user32.GetWindowLongW
        set_fn = user32.SetWindowLongPtrW if is_x64 else user32.SetWindowLongW
        get_fn.restype = ctypes.c_longlong
        style = int(get_fn(hwnd, gwl_style))
        style |= ws_thickframe | ws_maximizebox | ws_minimizebox
        set_fn(hwnd, gwl_style, style)
        # Re-apply frame so the new style takes effect without moving.
        swp_flags = 0x0001 | 0x0002 | 0x0004 | 0x0020  # NOSIZE|NOMOVE|NOZORDER|FRAMECHANGED
        user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, swp_flags)
        self._resize_style_ready = True

    def begin_resize(self, direction: str) -> dict[str, object]:
        def action() -> dict[str, object]:
            if direction not in self._RESIZE_DIRECTIONS:
                raise ValueError("Arah resize tidak dikenal.")
            hwnd = self._find_hwnd()
            if not hwnd:
                raise RuntimeError("Window belum tersedia.")
            import ctypes

            user32 = ctypes.windll.user32
            if user32.IsZoomed(hwnd):
                return {"resizing": False, "reason": "maximized"}
            self._ensure_resize_style(hwnd)
            wm_syscommand = 0x0112
            sc_size = 0xF000
            user32.ReleaseCapture()
            user32.SendMessageW(
                hwnd, wm_syscommand, sc_size + self._RESIZE_DIRECTIONS[direction], 0
            )
            return {"resizing": True, "direction": direction}

        return self._call(action)
