from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from typing import Any

FIREBASE_API_KEY = "AIzaSyD3pi_SzYpUpATrB41uJOpJOTwwUh_Kt4k"
FIREBASE_PROJECT_ID = "ipan-app-settinx"
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIRESTORE_BASE = (
    f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}"
    "/databases/(default)/documents"
)
DEVICE_HASH_LENGTH = 64


class _DocumentNotFound(Exception):
    """Firestore returned 404 for the requested document."""


def device_fingerprint() -> str:
    """Return an app-scoped digest; never expose or persist the Windows identifier."""
    if sys.platform != "win32":
        raise ValueError("Identitas perangkat hanya tersedia pada Windows.")

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            machine_guid, value_type = winreg.QueryValueEx(key, "MachineGuid")
    except OSError as exc:
        raise ValueError("Identitas perangkat tidak dapat diverifikasi.") from exc
    if value_type != winreg.REG_SZ or not isinstance(machine_guid, str) or not machine_guid:
        raise ValueError("Identitas perangkat tidak valid.")
    scoped = f"{FIREBASE_PROJECT_ID}\0{machine_guid}".encode()
    return hashlib.sha256(scoped).hexdigest()


def _https_request(
    url: str,
    payload: dict[str, Any] | None,
    token: str | None = None,
    method: str = "POST",
) -> dict[str, Any]:
    if not url.startswith("https://"):
        raise ValueError("Endpoint login tidak aman.")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(  # noqa: S310 -- HTTPS enforced above.
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:  # noqa: S310
            result = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("error", {})
            message = detail.get("message", "")
            status = detail.get("status", "")
        except (json.JSONDecodeError, AttributeError):
            message, status = "", ""
        if message in {"INVALID_LOGIN_CREDENTIALS", "EMAIL_NOT_FOUND", "INVALID_PASSWORD"}:
            raise ValueError("Email atau password salah.") from exc
        if message in {"OPERATION_NOT_ALLOWED", "PASSWORD_LOGIN_DISABLED"}:
            raise ValueError("Login Email/Password belum diaktifkan di pengaturan akun.") from exc
        if message == "USER_DISABLED":
            raise ValueError("Akun ini dinonaktifkan. Hubungi admin.") from exc
        if message == "TOO_MANY_ATTEMPTS_TRY_LATER":
            raise ValueError("Terlalu banyak percobaan. Coba lagi nanti.") from exc
        if exc.code == 404 and method == "GET":
            raise _DocumentNotFound from exc
        if status == "PERMISSION_DENIED" or exc.code in {401, 403, 409}:
            raise ValueError("Akun ini sudah terikat ke perangkat lain.") from exc
        detail_msg = message or status or f"HTTP {exc.code}"
        raise ValueError(f"Layanan login menolak permintaan ({detail_msg}).") from exc
    except (OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("Layanan login tidak dapat dihubungi.") from exc
    if not isinstance(result, dict):
        raise ValueError("Respons layanan login tidak valid.")
    return result


def _string_field(document: dict[str, Any], name: str) -> str | None:
    fields = document.get("fields")
    if not isinstance(fields, dict):
        return None
    value = fields.get(name)
    if not isinstance(value, dict):
        return None
    raw = value.get("stringValue")
    return raw if isinstance(raw, str) else None


def bind_device(uid: str, device_hash: str, token: str) -> None:
    """Bind one account to one device hash via Firestore Security Rules.

    Both documents are written in a single atomic commit; the deployed rules
    cross-check the pair with getAfter() and reject conflicting or partial
    writes. A 404 on the read means the account has never been bound; any
    other rejection keeps the login fail-closed.
    """
    user_document = f"{FIRESTORE_BASE}/deviceUsers/{uid}"
    binding_document = f"{FIRESTORE_BASE}/deviceBindings/{device_hash}"

    try:
        user = _https_request(user_document, None, token, method="GET")
    except _DocumentNotFound:
        user = {}
    existing = _string_field(user, "deviceHash") if user else None
    if existing is not None and existing != device_hash:
        raise ValueError("Akun ini sudah terikat ke perangkat lain.")
    if existing == device_hash:
        return

    commit = {
        "writes": [
            {
                "update": {
                    "name": user_document.split("/v1/", 1)[1],
                    "fields": {"deviceHash": {"stringValue": device_hash}},
                },
                "currentDocument": {"exists": False},
            },
            {
                "update": {
                    "name": binding_document.split("/v1/", 1)[1],
                    "fields": {"uid": {"stringValue": uid}},
                },
                "currentDocument": {"exists": False},
            },
        ]
    }
    _https_request(f"{FIRESTORE_BASE}:commit", commit, token)


def authenticate(username: str, password: str, license_key: str = "") -> dict[str, str]:
    """Authenticate against the account service and verify the license key.

    Flow:
    1. Sign in with Email/Password. The service returns ``localId``, the
       stable UID assigned when the account was created.
    2. Verify the user-supplied license key is exactly that UID. The license
       key is the account UID: when an account is created, the UID shown is
       the license the customer must enter.
    3. Bind the account to one device via Firestore Security Rules.
    """
    username = username.strip()
    license_key = license_key.strip()
    if not username or len(username) > 254 or not password or len(password) > 128:
        raise ValueError("Masukkan username dan password yang valid.")
    if not license_key or len(license_key) > 128:
        raise ValueError("Masukkan license key yang valid.")

    session = _https_request(
        f"{AUTH_URL}?key={FIREBASE_API_KEY}",
        {"email": username, "password": password, "returnSecureToken": "true"},
    )
    token = session.get("idToken")
    uid = session.get("localId")
    if not isinstance(token, str) or not token or not isinstance(uid, str) or not uid:
        raise ValueError("Token login tidak valid.")
    if license_key != uid:
        raise ValueError(
            "License key tidak valid. Pastikan Anda memasukkan kode lisensi "
            "yang sesuai dengan akun Anda, lalu coba lagi."
        )
    device_hash = device_fingerprint()
    if len(device_hash) != DEVICE_HASH_LENGTH:
        raise ValueError("Identitas perangkat tidak valid.")
    bind_device(uid, device_hash, token)
    return {"email": username, "state": "AUTHORIZED"}
