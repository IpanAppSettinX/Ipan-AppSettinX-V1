"""Diagnosis alur login Firebase — tampilkan error mentah dari setiap tahap.

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/diagnose_login.py

Skrip ini TIDAK menyimpan kredensial; input hanya dipakai untuk satu panggilan.
"""

from __future__ import annotations

import getpass
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ipan_optimizer.app import auth


def show(title: str) -> None:
    print(f"\n=== {title} ===")


def raw_request(url: str, payload, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(  # noqa: S310 -- diagnosis tool, HTTPS endpoints only.
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:  # noqa: S310
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"raw": e.read().decode(errors="replace")}
        return e.code, body
    except Exception as e:
        return None, {"exception": f"{type(e).__name__}: {e}"}


def main() -> int:
    print("Diagnosis login Ipan AppSettinX")
    print("API key & project:", auth.FIREBASE_PROJECT_ID)
    username = input("Username (email akun Firebase): ").strip()
    password = getpass.getpass("Password: ")

    # Tahap 1: sign-in
    show("1) Sign-in Identity Toolkit")
    code, body = raw_request(
        f"{auth.AUTH_URL}?key={auth.FIREBASE_API_KEY}",
        {"email": username, "password": password, "returnSecureToken": "true"},
    )
    print("HTTP", code)
    print(json.dumps(body, indent=2)[:800])
    token = body.get("idToken") if isinstance(body, dict) else None
    uid = body.get("localId") if isinstance(body, dict) else None
    if not token or not uid:
        print("\n>> GAGAL di tahap sign-in. Perbaiki kredensial / aktifkan provider.")
        return 1

    # Tahap 2: device fingerprint
    show("2) Device fingerprint (HWID)")
    try:
        device_hash = auth.device_fingerprint()
        print("device_hash:", device_hash[:16], "... (len", len(device_hash), ")")
    except Exception as e:
        print("GAGAL fingerprint:", type(e).__name__, e)
        return 1

    # Tahap 3: GET deviceUsers/{uid}
    show("3) GET deviceUsers/{uid}")
    user_doc = f"{auth.FIRESTORE_BASE}/deviceUsers/{uid}"
    code, body = raw_request(user_doc, None, token, method="GET")
    print("HTTP", code)
    print(json.dumps(body, indent=2)[:800])

    # Tahap 4: coba commit binding bila belum ada
    if code == 404:
        show("4) POST :commit (binding baru)")
        binding_doc = f"{auth.FIRESTORE_BASE}/deviceBindings/{device_hash}"
        commit = {
            "writes": [
                {
                    "update": {
                        "name": user_doc.split("/v1/", 1)[1],
                        "fields": {"deviceHash": {"stringValue": device_hash}},
                    },
                    "currentDocument": {"exists": False},
                },
                {
                    "update": {
                        "name": binding_doc.split("/v1/", 1)[1],
                        "fields": {"uid": {"stringValue": uid}},
                    },
                    "currentDocument": {"exists": False},
                },
            ]
        }
        code, body = raw_request(f"{auth.FIRESTORE_BASE}:commit", commit, token)
        print("HTTP", code)
        print(json.dumps(body, indent=2)[:800])
        if code == 200:
            print("\n>> SUKSES: perangkat ini berhasil di-bind ke akun Anda.")
        else:
            print("\n>> GAGAL commit binding. Lihat pesan di atas.")
    elif code == 200:
        existing = auth._string_field(body, "deviceHash")
        if existing == device_hash:
            print("\n>> SUKSES: akun sudah ter-bind ke perangkat INI. Login seharusnya lolos.")
        else:
            print(
                f"\n>> AKUN TERIKAT PERANGKAT LAIN. "
                f"existing={existing[:12]}... != {device_hash[:12]}..."
            )
            print("   Minta admin Reset HWID, atau hapus kedua dokumen via Console.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
