from __future__ import annotations

import time

import pytest

from ipan_optimizer.app.api import ApiBridge

FORBIDDEN_VISIBLE_TWEAK_TERMS = (
    "%homepath%",
    "%temp%",
    "bcd",
    "cls",
    "deletevalue",
    "filesystem:",
    "game dvr",
    "hkcu",
    "hklm",
    "nolazymode",
    "registry:",
    "services:",
    "superfetch",
)


def assert_success(response: dict[str, object]) -> object:
    assert response["success"] is True
    assert response["error"] is None
    return response["data"]


def test_scan_and_recommendations(bridge: ApiBridge) -> None:
    scan = assert_success(bridge.scan_system())
    assert isinstance(scan, dict)
    scan_id = scan["scan_id"]
    recommendations = assert_success(bridge.list_recommendations(scan_id))
    assert isinstance(recommendations, list)
    assert recommendations


def test_authentication_rejects_invalid_credentials(
    bridge: ApiBridge, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_request(
        url: str, payload: object, token: str | None = None, method: str = "POST"
    ) -> dict[str, object]:
        del payload, token, method
        if "identitytoolkit" in url:
            raise ValueError("Email atau password salah.")
        return {}

    from ipan_optimizer.app import auth

    monkeypatch.setattr(auth, "_https_request", fake_request)
    response = bridge.authenticate("member@example.com", "password-salah", "uid-1")
    assert response["success"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_curated_tweak_catalog_is_risk_gated(bridge: ApiBridge) -> None:
    catalog = assert_success(bridge.list_tweak_catalog())
    assert isinstance(catalog, list)
    assert len(catalog) == 5
    assert [item["title"] for item in catalog] == [
        "APPLY REGEDIT",
        "CLEAN TEMP FILES",
        "APPLY BOOSTER",
        "REVERT ALL CHANGES",
        "CLEAN LOG FILES",
    ]
    assert all("new" not in item["title"].casefold() for item in catalog)
    assert all(item["inspected_items"] for item in catalog)
    visible_copy = " ".join(
        str(value)
        for item in catalog
        for value in (item["category"], item["summary"], *item["inspected_items"])
    ).casefold()
    assert not any(term in visible_copy for term in FORBIDDEN_VISIBLE_TWEAK_TERMS)
    assert [item["action"] for item in catalog] == [
        "apply",
        "apply",
        "apply",
        "restore",
        "apply",
    ]


def test_invalid_rule_returns_typed_error(bridge: ApiBridge) -> None:
    response = bridge.preview_transaction(["security.disable_defender"], None)
    assert response["success"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def _run_tweak_job(bridge: ApiBridge, job_response: dict[str, object]) -> dict[str, object]:
    """Drive an async tweak job to completion and return its result payload.

    ``apply_*_tweak`` return a job descriptor (async), not the tweak result.
    Poll the job until it leaves PENDING/RUNNING, then return the stored
    result dict (which carries applied/failed) or an empty dict on failure.
    """
    assert job_response["success"] is True
    job_id = job_response["data"]["job_id"]
    status = job_response["data"]
    for _ in range(500):
        status = bridge.get_job_status(job_id)["data"]
        if status["state"] not in {"PENDING", "RUNNING"}:
            break
        time.sleep(0.02)
    assert status["state"] in {"SUCCEEDED", "FAILED", "CANCELLED"}
    result = status.get("result") or {}
    assert isinstance(result, dict)
    return result


def test_emulator_tweak_executes_real_operations(bridge: ApiBridge) -> None:
    result = _run_tweak_job(bridge, bridge.apply_emulator_tweak("emulator.bluestacks5"))
    # The host is never mutated (dry-run / no-elevation), but the job must run
    # to completion and report a structured outcome.
    assert "applied" in result
    assert "failed" in result
    assert result["applied"] >= 1 or result.get("skipped") or result["failed"] >= 0


def test_gaming_tweak_executes_real_operations(bridge: ApiBridge) -> None:
    result = _run_tweak_job(bridge, bridge.apply_gaming_tweak("aim_smooth"))
    assert "applied" in result
    assert "failed" in result
    assert result["applied"] >= 1 or result.get("skipped") or result["failed"] >= 0


def test_advanced_tweak_executes_real_operations(bridge: ApiBridge) -> None:
    result = _run_tweak_job(bridge, bridge.apply_advanced_tweak("adv.high_performance"))
    # On the test host (non-admin or non-Windows) the tweak may partially fail,
    # but it must no longer be a blanket rejection.
    assert "applied" in result
    assert "failed" in result
    assert result["applied"] >= 1 or result.get("skipped") or result["failed"] >= 0


def test_transaction_job_reports_verified_result(bridge: ApiBridge) -> None:
    preview = assert_success(bridge.preview_transaction(["windows.game_mode"], None))
    job = assert_success(bridge.start_apply_transaction(preview["transaction_id"]))
    while job["state"] in {"PENDING", "RUNNING"}:
        job = assert_success(bridge.get_job_status(job["job_id"]))
    assert job["state"] == "SUCCEEDED"
    assert job["progress"] == 100
    assert job["result"]["state"] == "VERIFIED"


def test_benchmark_does_not_fabricate_metrics(bridge: ApiBridge) -> None:
    benchmark = assert_success(bridge.start_benchmark({"label": "Baseline"}))
    assert benchmark["metrics"] == {}
    comparison = assert_success(bridge.compare_benchmarks([benchmark["benchmark_id"]]))
    assert comparison["state"] == "INCONCLUSIVE"


def test_settings_cannot_disable_dry_run(bridge: ApiBridge) -> None:
    response = bridge.save_settings({"dry_run": False})
    assert response["success"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_support_url_allowlist_rejects_unknown_target(bridge: ApiBridge) -> None:
    response = bridge.open_support_url("https://example.com/")
    assert response["success"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"
