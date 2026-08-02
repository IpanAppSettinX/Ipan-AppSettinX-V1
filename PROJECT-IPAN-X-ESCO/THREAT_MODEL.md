# Threat model

## Assets

Windows configuration, Registry state, emulator configuration, transaction
snapshots, recovery journal, user reports, and the privilege boundary.

## Trust boundaries

- Hardware names, paths, logs, imported profiles, manifests, and `.reg` files
  are untrusted.
- Frontend data is untrusted when it crosses into Python.
- Elevated operations must distrust and revalidate the main process plan.

## Required controls

| Threat | Control |
|---|---|
| Manifest injection/downgrade | Strict versioned schema, typed operation union, signature and monotonic revision |
| Registry target injection | Exact catalog allowlist, HKCU/HKLM enum, explicit view, bounds and type validation |
| Type loss | Raw lossless snapshots for all supported Registry types |
| TOCTOU | Expected-state compare immediately before apply and rollback |
| Replay | One-time nonce tied to transaction identity |
| Path traversal/reparse | Canonical path, fixed roots, handle/file identity checks, reparse rejection |
| Journal corruption | Append-only hash chain, sequence validation, fail-closed recovery |
| XSS/log injection | CSP, text rendering, control-character stripping, structured logs |
| External navigation | Local UI only; explicit allowlisted system-browser open |
| Account/device sharing | Firebase ID token plus atomic Firestore Security Rules UID/device-hash binding |
| Device identifier disclosure | App-scoped SHA-256 digest; raw MachineGuid never leaves the process |
| Client-side auth bypass | Firestore rules are authoritative; rejected or partial binding writes fail closed |
| Dependency compromise | Exact pins, hashes for release locks, provenance and signing |

## Prohibited boundary

The schema and policy reject arbitrary commands, Registry ACL/owner changes,
remote hives, recursive deletion, `.reg` execution, BCD/timer packs, blanket
service disablement, Defender/Firewall/UAC/Update weakening, game memory access,
DLL injection, packets, macros, APK/client changes, and anti-cheat bypass.

