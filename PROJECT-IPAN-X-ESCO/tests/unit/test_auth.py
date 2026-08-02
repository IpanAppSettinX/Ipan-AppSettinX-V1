from __future__ import annotations

from typing import Any

import pytest

from ipan_optimizer.app import auth

DEVICE_HASH = "a" * 64


def _fake_session(uid: str = "uid-1") -> dict[str, Any]:
    return {"idToken": "firebase-token", "localId": uid}


def _install_fake_http(
    monkeypatch: pytest.MonkeyPatch, responses: dict[str, Any]
) -> list[tuple[str, Any, str | None, str]]:
    calls: list[tuple[str, Any, str | None, str]] = []

    def fake_request(
        url: str, payload: Any, token: str | None = None, method: str = "POST"
    ) -> dict[str, Any]:
        calls.append((url, payload, token, method))
        outcome = responses.get((method, url))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome if isinstance(outcome, dict) else {}

    monkeypatch.setattr(auth, "_https_request", fake_request)
    monkeypatch.setattr(auth, "device_fingerprint", lambda: DEVICE_HASH)
    return calls


def test_authentication_binds_new_device_with_atomic_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_doc = f"{auth.FIRESTORE_BASE}/deviceUsers/uid-1"
    binding_doc = f"{auth.FIRESTORE_BASE}/deviceBindings/{DEVICE_HASH}"
    calls = _install_fake_http(
        monkeypatch,
        {
            ("POST", f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}"): _fake_session(),
            ("GET", user_doc): auth._DocumentNotFound(),
            ("POST", f"{auth.FIRESTORE_BASE}:commit"): {},
        },
    )

    result = auth.authenticate(" member@example.com ", "password-valid", "IPAN-KEY-001")

    assert result == {"email": "member@example.com", "state": "AUTHORIZED"}
    assert calls[0][1] == {
        "email": "member@example.com",
        "password": "password-valid",
        "returnSecureToken": "true",
    }
    commit_url, commit_payload, commit_token, _ = calls[2]
    assert commit_url == f"{auth.FIRESTORE_BASE}:commit"
    assert commit_token == "firebase-token"
    assert commit_payload == {
        "writes": [
            {
                "update": {
                    "name": user_doc.split("/v1/", 1)[1],
                    "fields": {"deviceHash": {"stringValue": DEVICE_HASH}},
                },
                "currentDocument": {"exists": False},
            },
            {
                "update": {
                    "name": binding_doc.split("/v1/", 1)[1],
                    "fields": {"uid": {"stringValue": "uid-1"}},
                },
                "currentDocument": {"exists": False},
            },
        ]
    }


def test_authentication_accepts_existing_matching_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_doc = f"{auth.FIRESTORE_BASE}/deviceUsers/uid-1"
    calls = _install_fake_http(
        monkeypatch,
        {
            ("POST", f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}"): _fake_session(),
            ("GET", user_doc): {"fields": {"deviceHash": {"stringValue": DEVICE_HASH}}},
        },
    )

    result = auth.authenticate("member@example.com", "password-valid", "IPAN-KEY-001")

    assert result["state"] == "AUTHORIZED"
    assert [call[3] for call in calls] == ["POST", "GET"]


def test_authentication_rejects_account_bound_to_other_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_doc = f"{auth.FIRESTORE_BASE}/deviceUsers/uid-1"
    _install_fake_http(
        monkeypatch,
        {
            ("POST", f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}"): _fake_session(),
            ("GET", user_doc): {"fields": {"deviceHash": {"stringValue": "b" * 64}}},
        },
    )

    with pytest.raises(ValueError, match="sudah terikat ke perangkat lain"):
        auth.authenticate("member@example.com", "password-valid", "IPAN-KEY-001")


def test_authentication_fails_closed_when_rules_reject_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_doc = f"{auth.FIRESTORE_BASE}/deviceUsers/uid-1"
    _install_fake_http(
        monkeypatch,
        {
            ("POST", f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}"): _fake_session(),
            ("GET", user_doc): auth._DocumentNotFound(),
            ("POST", f"{auth.FIRESTORE_BASE}:commit"): ValueError(
                "Akun ini sudah terikat ke perangkat lain."
            ),
        },
    )

    with pytest.raises(ValueError, match="sudah terikat ke perangkat lain"):
        auth.authenticate("member@example.com", "password-valid", "IPAN-KEY-001")


def test_authentication_rejects_invalid_session_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_http(
        monkeypatch,
        {
            ("POST", f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}"): {"idToken": ""},
        },
    )

    with pytest.raises(ValueError, match="Token login tidak valid"):
        auth.authenticate("member@example.com", "password-valid", "IPAN-KEY-001")
