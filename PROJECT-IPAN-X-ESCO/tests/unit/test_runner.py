from __future__ import annotations

import json
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
