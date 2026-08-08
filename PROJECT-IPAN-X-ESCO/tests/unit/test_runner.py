from __future__ import annotations

import json
import re
import sys
import types
from datetime import UTC, datetime, timedelta

from ipan_optimizer.privileged import runner
from ipan_optimizer.privileged.runner import (
    ExecStep,
    execute_plan_file,
    is_elevated,
    resolve_command,
    run_elevated_steps,
    run_step,
    validate_plan_file,
    write_plan,
)


def test_hidden_console_kwargs_requests_no_window(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    kwargs = runner._hidden_console_kwargs()
    # CREATE_NO_WINDOW (0x08000000) must be set so no console ever flashes.
    assert kwargs["creationflags"] & 0x08000000
    startupinfo = kwargs["startupinfo"]
    assert startupinfo.dwFlags & 0x00000001  # STARTF_USESHOWWINDOW
    assert startupinfo.wShowWindow == 0  # SW_HIDE


def test_hidden_console_kwargs_empty_off_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert runner._hidden_console_kwargs() == {}


def test_is_explorer_relaunch_detects_both_spellings():
    assert runner._is_explorer_relaunch(["start", "explorer.exe"]) is True
    assert runner._is_explorer_relaunch(["explorer.exe"]) is True
    assert runner._is_explorer_relaunch(["explorer"]) is True
    assert runner._is_explorer_relaunch(["START", "Explorer.EXE"]) is True
    assert runner._is_explorer_relaunch(["taskkill", "/f", "/im", "explorer.exe"]) is False
    assert runner._is_explorer_relaunch(["powershell", "-Command", "x"]) is False
    assert runner._is_explorer_relaunch([]) is False


def test_run_step_relaunches_explorer_detached(monkeypatch):
    """A shell relaunch must use Popen (detached), never subprocess.run."""
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(runner, "_file_exists_resolved", lambda _p: True)
    popen_calls: list[list[str]] = []

    class _FakePopen:
        def __init__(self, cmd, **_kwargs):
            popen_calls.append(cmd)

    def _boom_run(*_a, **_k):  # subprocess.run must NOT be used for explorer.
        raise AssertionError("subprocess.run must not be called for explorer relaunch")

    monkeypatch.setattr(runner.subprocess, "Popen", _FakePopen)
    monkeypatch.setattr(runner.subprocess, "run", _boom_run)

    for spelling in (["start", "explorer.exe"], ["explorer.exe"]):
        outcome = run_step(ExecStep("Restart Explorer", spelling, requires_admin=True))
        assert outcome["success"] is True
    assert popen_calls == [[r"%WINDIR%\explorer.exe"], [r"%WINDIR%\explorer.exe"]]


def test_run_step_skips_explorer_relaunch_when_binary_missing(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(runner, "_file_exists_resolved", lambda _p: False)
    outcome = run_step(ExecStep("Restart Explorer", ["start", "explorer.exe"]))
    assert outcome["success"] is True
    assert outcome["skipped"] is True


def test_run_step_isolated_skips_hung_step(monkeypatch):
    """A step that never returns must be skipped, not freeze the batch."""
    monkeypatch.setattr("sys.platform", "win32")
    import threading as _threading

    def _hang(_step):
        _threading.Event().wait(30)  # never returns within the test timeout
        return {"description": "x", "success": True}

    monkeypatch.setattr(runner, "run_step", _hang)
    outcome = runner._run_step_isolated(ExecStep("stuck", ["sc", "config"]), timeout=1)
    assert outcome["success"] is True
    assert outcome["skipped"] is True


def test_run_elevated_steps_isolates_each_step_in_process(monkeypatch):
    """In-process (elevated) path must guard each step individually."""
    monkeypatch.setenv(runner.NO_ELEVATION_ENV, "1")
    monkeypatch.setattr(runner, "is_elevated", lambda: False)
    seen: list[list[str]] = []

    def fake_isolated(step):
        seen.append(step.command)
        return {"description": step.description, "success": True}

    monkeypatch.setattr(runner, "_run_step_isolated", fake_isolated)
    outcomes = run_elevated_steps(
        [
            ExecStep("a", ["reg", "add"], requires_admin=True),
            ExecStep("b", ["sc", "config"], requires_admin=True),
        ],
        "tweak-x",
    )
    assert len(outcomes) == 2
    assert seen == [["reg", "add"], ["sc", "config"]]


def test_is_elevated_false_on_non_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert is_elevated() is False


def test_is_elevated_true_with_elevated_token(monkeypatch):
    import ctypes

    monkeypatch.setattr("sys.platform", "win32")

    def fake_open_process_token(*_a, **_k):
        return 1

    def fake_get_token_information(_h, _c, buf, _s, _r):
        buf._obj.value = 1
        return 1

    monkeypatch.setattr(ctypes.windll.advapi32, "OpenProcessToken", fake_open_process_token)
    monkeypatch.setattr(ctypes.windll.advapi32, "GetTokenInformation", fake_get_token_information)
    monkeypatch.setattr(ctypes.windll.kernel32, "CloseHandle", lambda *_a: 1)
    assert is_elevated() is True


def test_is_elevated_false_with_filtered_token(monkeypatch):
    import ctypes

    monkeypatch.setattr("sys.platform", "win32")

    def fake_open_process_token(*_a, **_k):
        return 1

    def fake_get_token_information(_h, _c, buf, _s, _r):
        buf._obj.value = 0
        return 1

    monkeypatch.setattr(ctypes.windll.advapi32, "OpenProcessToken", fake_open_process_token)
    monkeypatch.setattr(ctypes.windll.advapi32, "GetTokenInformation", fake_get_token_information)
    monkeypatch.setattr(ctypes.windll.kernel32, "CloseHandle", lambda *_a: 1)
    assert is_elevated() is False


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_resolve_command_expands_env(monkeypatch):
    monkeypatch.setenv("IPAN_TEST_VAR", "zzz")
    assert resolve_command(["echo", "%IPAN_TEST_VAR%"]) == ["cmd", "/c", "echo", "zzz"]


def test_resolve_command_leaves_executables():
    assert resolve_command(["reg", "add", "HKLM\\X", "/f"]) == [
        "reg",
        "add",
        "HKLM\\X",
        "/f",
    ]


def test_run_step_success(monkeypatch):
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *_a, **_k: _FakeCompleted(0, "ok"),
    )
    outcome = run_step(ExecStep("desc", ["reg", "add"]))
    assert outcome["success"] is True
    assert outcome["stdout"] == "ok"


def test_run_step_failure(monkeypatch):
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *_a, **_k: _FakeCompleted(5, "", "Access is denied"),
    )
    outcome = run_step(ExecStep("desc", ["reg", "add"]))
    assert outcome["success"] is False
    assert "Access is denied" in outcome["stderr"]


def test_run_step_rejects_non_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    outcome = run_step(ExecStep("desc", ["reg", "add"]))
    assert outcome["success"] is False


def test_run_elevated_steps_runs_in_process_when_no_elevation(monkeypatch):
    monkeypatch.setenv(runner.NO_ELEVATION_ENV, "1")
    monkeypatch.setattr(runner, "is_elevated", lambda: False)
    calls: list[list[str]] = []

    def fake_run(step):
        calls.append(step.command)
        return {"description": step.description, "success": True}

    monkeypatch.setattr(runner, "run_step", fake_run)
    monkeypatch.setattr(
        runner,
        "_launch_elevated",
        lambda *_: (_ for _ in ()).throw(AssertionError("must not launch")),
    )
    outcomes = run_elevated_steps(
        [ExecStep("a", ["reg", "add"], requires_admin=True)],
        "tweak-x",
    )
    assert len(outcomes) == 1
    assert calls == [["reg", "add"]]


def test_run_elevated_steps_reports_failure_when_uac_cancelled(monkeypatch, tmp_path):
    monkeypatch.delenv(runner.NO_ELEVATION_ENV, raising=False)
    monkeypatch.setattr(runner, "is_elevated", lambda: False)
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(runner, "_launch_elevated", lambda *_: False)
    outcomes = run_elevated_steps(
        [ExecStep("a", ["sc", "config"], requires_admin=True)],
        "tweak-x",
    )
    assert len(outcomes) == 1
    assert outcomes[0]["success"] is False


def test_write_and_validate_plan_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    steps = [ExecStep("a", ["reg", "add", "HKLM\\X", "/f"], requires_admin=True)]
    write_plan(steps, "tweak-x", plan_path)
    validated = validate_plan_file(plan_path)
    assert [step.command for step in validated] == [["reg", "add", "HKLM\\X", "/f"]]


def test_validate_plan_rejects_tampered_digest(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    write_plan([ExecStep("a", ["reg", "add"])], "tweak-x", plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["steps"][0]["command"] = ["reg", "delete"]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    try:
        validate_plan_file(plan_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Digest" in str(exc)


def test_validate_plan_rejects_expired(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    write_plan([ExecStep("a", ["reg", "add"])], "tweak-x", plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["expires_at"] = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    try:
        validate_plan_file(plan_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "kedaluwarsa" in str(exc)


def test_validate_plan_rejects_replay(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    write_plan([ExecStep("a", ["reg", "add"])], "tweak-x", plan_path)
    validate_plan_file(plan_path)
    try:
        validate_plan_file(plan_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "replay" in str(exc)


def test_execute_plan_file_reports_success(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    result_path = tmp_path / "result.json"
    write_plan([ExecStep("a", ["reg", "add"])], "tweak-x", plan_path)
    monkeypatch.setattr(
        runner,
        "run_step",
        lambda step: {
            "description": step.description,
            "success": True,
            "requires_admin": True,
        },
    )
    assert execute_plan_file(plan_path, result_path) == 0
    results = json.loads(result_path.read_text(encoding="utf-8"))
    assert results["steps"][0]["success"] is True


def test_execute_plan_file_reports_invalid_plan(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    plan_path = tmp_path / "plan.json"
    result_path = tmp_path / "result.json"
    plan_path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    assert execute_plan_file(plan_path, result_path) == 1
    results = json.loads(result_path.read_text(encoding="utf-8"))
    assert "error" in results


# ── Native AppX debloat (adv.debloat_windows) ───────────────────


class _FakePackageId:
    def __init__(self, name: str, full_name: str) -> None:
        self.Name = name
        self.FullName = full_name


class _FakePackage:
    def __init__(self, name: str, full_name: str) -> None:
        self.Id = _FakePackageId(name, full_name)


class _FakeOperation:
    def __init__(self, status: int = 1) -> None:
        self.Status = status
        self.ErrorCode = type("E", (), {"HResult": 0})()

    def Cancel(self) -> None:
        pass


class _FakePackageManager:
    """In-memory PackageManager used to test the debloat driver."""

    def __init__(self, packages: list[_FakePackage], fail_on: set[str] | None = None) -> None:
        self._packages = packages
        self._fail_on = fail_on or set()
        self.removed: list[str] = []

    def FindPackagesForUser(self, _sid: str) -> list[_FakePackage]:
        # A successfully removed package disappears from the deployment.
        return [p for p in self._packages if p.Id.FullName not in self.removed]

    def RemovePackageAsync(self, full_name: str) -> _FakeOperation:
        if full_name in self._fail_on:
            return _FakeOperation(status=3)
        self.removed.append(full_name)
        return _FakeOperation(status=1)


class _FakeAppxShell:
    """In-memory stand-in for ``_run_powershell_capture``: simulates the
    all-users PowerShell enumeration / removal / verification scripts without
    ever spawning a real process during tests."""

    def __init__(
        self,
        installed: list[str],
        stubborn: set[str] | None = None,
        fail_enumeration: bool = False,
    ) -> None:
        self.installed = list(installed)
        self.stubborn = set(stubborn or [])
        self.fail_enumeration = fail_enumeration
        self.calls: list[str] = []

    def capture(self, script: str, timeout: int = 45) -> tuple[bool, str, str]:
        self.calls.append(script)
        if self.fail_enumeration and "-match" in script and "Remove-AppxPackage" not in script:
            return (False, "", "deployment service tidak tersedia")
        if "Remove-AppxPackage" in script:
            failed = []
            for n in _parse_names(script):
                if n in self.installed and n not in self.stubborn:
                    self.installed.remove(n)
                elif n in self.installed:
                    failed.append(n + "|stubborn")
            if failed:
                return (True, "FAILED:" + ";;".join(failed), "")
            return (True, "", "")
        if "$names" in script:
            names = _parse_names(script)
            present = [n for n in self.installed if n in names]
        else:
            present = [n for n in self.installed if runner._name_matches_pattern(n)]
        return (True, "\n".join(present), "")


def _parse_names(script: str) -> list[str]:
    # Non-greedy: the remove script appends more single-quoted strings after the
    # $names array, so a greedy `.*` used to swallow the rest of the script.
    match = re.search(r"\$names = @\('(.*?)'\)", script)
    if not match:
        return []
    return match.group(1).replace("''", "'").split("','")


def _debloat_step() -> ExecStep:
    return ExecStep(
        description="Debloat Windows",
        command=[runner.APPSX_DEBLOAT_STEP_ID],
        requires_admin=True,
    )


def test_appx_patterns_match_and_protect():
    assert runner._name_matches_pattern("Microsoft.BingWeather") is True
    assert runner._name_matches_pattern("Microsoft.XboxApp") is True
    assert runner._name_matches_pattern("Microsoft.ZuneMusic") is True
    assert runner._name_matches_pattern("Microsoft.MSPaint") is True
    assert runner._name_matches_pattern("Microsoft.WindowsCamera") is True
    assert runner._name_matches_pattern("Microsoft.Windows.ShellExperienceHost") is False
    # Protected names are always skipped even when they match a pattern.
    assert runner._is_protected_package("Microsoft.Windows.ShellExperienceHost") is True
    assert runner._is_protected_package("Microsoft.WindowsStore") is True
    assert runner._is_protected_package("Microsoft.VCLibs.140.00") is True
    assert runner._is_protected_package("Microsoft.UI.Xaml.2.8") is True
    assert runner._is_protected_package("Microsoft.WindowsTerminal") is True
    assert runner._is_protected_package("Microsoft.BingWeather") is False
    assert runner._is_protected_package("Microsoft.ZuneMusic") is False


def test_run_step_dispatches_native_debloat(monkeypatch):
    """The sentinel step must route to run_appx_debloat, never subprocess."""
    monkeypatch.setattr("sys.platform", "win32")
    called: list[ExecStep] = []

    def _fake_debloat(step: ExecStep) -> dict:
        called.append(step)
        return {"description": step.description, "success": True, "requires_admin": True}

    def _boom_run(*_a, **_k):
        raise AssertionError("subprocess.run must not be called for the debloat sentinel")

    monkeypatch.setattr(runner, "run_appx_debloat", _fake_debloat)
    monkeypatch.setattr(runner.subprocess, "run", _boom_run)
    outcome = run_step(_debloat_step())
    assert outcome["success"] is True
    assert called and called[0].command == [runner.APPSX_DEBLOAT_STEP_ID]


def test_debloat_scripts_use_all_users():
    """The generated PowerShell commands must use -AllUsers (the documented
    all-user removal), isolate each package with try/catch, and filter via
    Where-Object (Get-AppxPackage -Name rejects arrays)."""
    remove = runner._debloat_remove_script(["Microsoft.BingWeather"])
    assert "Get-AppxPackage -AllUsers" in remove
    assert "Remove-AppxPackage -Package" in remove
    assert "-AllUsers" in remove
    assert "-Confirm:$false" in remove
    assert "foreach" in remove and "try {" in remove and "catch" in remove
    assert "$names -contains" not in remove
    target = runner._debloat_target_names_script()
    assert "Get-AppxPackage -AllUsers" in target
    assert "-match" in target
    assert "SystemApps" in target  # SystemApps are part of Windows, never removable
    verify = runner._debloat_verify_script(["Microsoft.BingWeather", "Microsoft.ZuneMusic"])
    assert "Get-AppxPackage -AllUsers" in verify
    assert "Microsoft.ZuneMusic" in verify


def test_run_appx_debloat_removes_all_matching(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    shell = _FakeAppxShell(
        [
            "Microsoft.BingWeather",
            "Microsoft.ZuneMusic",
            "Microsoft.Windows.ShellExperienceHost",  # matches pattern, protected
            "Microsoft.VCRedist",  # does not match any bloat pattern
        ]
    )
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is True
    assert "2 aplikasi" in outcome["stdout"]
    assert "Microsoft.BingWeather" not in shell.installed
    assert "Microsoft.ZuneMusic" not in shell.installed
    assert "Microsoft.Windows.ShellExperienceHost" in shell.installed


def test_run_appx_debloat_partial_removal_still_succeeds(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    shell = _FakeAppxShell(
        ["Microsoft.BingWeather", "Microsoft.ZuneMusic"],
        stubborn={"Microsoft.ZuneMusic"},
    )
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    outcome = runner.run_appx_debloat(_debloat_step())
    # One success is enough — a single stubborn app must not fail the tweak.
    assert outcome["success"] is True
    assert "1 aplikasi" in outcome["stdout"]
    assert "Gagal sebagian" in outcome["stdout"]


def test_run_appx_debloat_nothing_removed_reports_error(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    shell = _FakeAppxShell(
        ["Microsoft.BingWeather", "Microsoft.ZuneMusic"],
        stubborn={"Microsoft.BingWeather", "Microsoft.ZuneMusic"},
    )
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is False
    assert "Tidak ada aplikasi yang dapat dihapus" in outcome["error"]


def test_run_appx_debloat_no_candidates_is_skipped(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    shell = _FakeAppxShell(["Microsoft.VCRedist"])
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is True
    assert outcome.get("skipped") is True


def test_run_appx_debloat_all_protected_is_skipped(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    # PeopleExperienceHost matches a pattern ("people") but is a protected
    # SystemApp (part of Windows) that must never enter the target list.
    shell = _FakeAppxShell(["Microsoft.Windows.PeopleExperienceHost"])
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is True
    assert outcome.get("skipped") is True
    # Nothing was touched — the protected SystemApp stays installed.
    assert shell.installed == ["Microsoft.Windows.PeopleExperienceHost"]


def test_run_appx_debloat_enumeration_falls_back_to_native(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    shell = _FakeAppxShell(["Microsoft.BingWeather"], fail_enumeration=True)
    monkeypatch.setattr(runner, "_run_powershell_capture", shell.capture)
    pm = _FakePackageManager(
        [_FakePackage("Microsoft.BingWeather", "Microsoft.BingWeather_4.53_x64__8wekyb3d8bbwe")]
    )
    monkeypatch.setattr(runner, "_load_appx_package_manager", lambda: pm)
    monkeypatch.setattr(runner, "_current_user_sid", lambda: "S-1-5-21-1-2-3-1001")
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is True
    assert "1 aplikasi" in outcome["stdout"]


def test_run_appx_debloat_enumeration_failure_reports_error(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")

    def _boom() -> object:
        raise RuntimeError("Runtime .NET untuk AppX tidak tersedia")

    monkeypatch.setattr(runner, "_run_powershell_capture", lambda *_: (False, "", "broken"))
    monkeypatch.setattr(runner, "_load_appx_package_manager", _boom)
    outcome = runner.run_appx_debloat(_debloat_step())
    assert outcome["success"] is False
    assert "Enumerasi AppX gagal" in outcome["error"]


def test_load_appx_package_manager_is_idempotent(monkeypatch):
    """set_runtime must run only ONCE even if the Debloat tweak is applied
    many times in one process — the second+ call used to raise
    "The runtime ... has already been loaded"."""
    state = {"set_runtime_calls": 0, "runtime": None}
    pm = object()

    def get_runtime_info():
        return state["runtime"]

    def set_runtime(rt):
        state["set_runtime_calls"] += 1
        state["runtime"] = rt

    class _FakeType:
        @staticmethod
        def GetType(*_args):
            return object()  # not None -> GetTypeFromProgID path is skipped

        @staticmethod
        def GetTypeFromProgID(*_args):
            return None

    fake_pythonnet = types.SimpleNamespace(
        get_runtime_info=get_runtime_info, set_runtime=set_runtime
    )
    fake_clr_loader = types.SimpleNamespace(get_netfx=lambda: object())
    fake_system = types.SimpleNamespace(
        Activator=type("_A", (), {"CreateInstance": staticmethod(lambda *_: pm)}),
        Type=_FakeType,
    )
    monkeypatch.setitem(sys.modules, "pythonnet", fake_pythonnet)
    monkeypatch.setitem(sys.modules, "clr_loader", fake_clr_loader)
    monkeypatch.setitem(sys.modules, "clr", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "System", fake_system)

    assert runner._load_appx_package_manager() is pm
    assert runner._load_appx_package_manager() is pm
    assert runner._load_appx_package_manager() is pm
    assert state["set_runtime_calls"] == 1


def test_debloat_step_runs_in_process_without_admin():
    """The catalog step must NOT require admin so it never touches the
    UAC/elevated-helper relaunch path (the cause of "semua operasi gagal")."""
    from ipan_optimizer.core.tweak_engine import ADVANCED_TWEAK_COMMANDS

    step = ADVANCED_TWEAK_COMMANDS["adv.debloat_windows"][0]
    assert step.command == [runner.APPSX_DEBLOAT_STEP_ID]
    assert step.requires_admin is False
