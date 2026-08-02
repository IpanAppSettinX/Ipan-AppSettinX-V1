# Validation record

Date: 2026-07-27  
Fixture: Windows 10 22H2 build 19045, Python 3.12.10 x64

## Automated source gates

| Gate | Result |
|---|---|
| Ruff formatting and lint | Pass |
| mypy strict source check | Pass, 42 source files |
| Unit/integration/security/UI tests | Pass, 76 |
| Packaging tests | Pass, 4 |
| Canonical control matrix | Pass, 59 of 59 mapped |
| Frontend external-resource policy | Pass |
| Static frontend asset budget | Pass, 108,172 bytes of 512,000 |

## UI smoke

A real pywebview/WebView2 run at 1280x800 loaded the dashboard, navigated to
Scan, invoked the Python bridge, waited for recommendations, and captured both
screens. Browser E2E additionally exercised the Tweak Library, critical warning
dialog, official Mouse Settings action, six support links, every primary
workflow, and 1024x700, 1280x800, and 1440x900 screenshots. The harnesses
recorded zero console errors, zero page errors, and zero external startup
requests. The pywebview harness terminates the GUI process after capture; that
termination is marked explicitly in the JSON report and is not treated as an
application failure.

## Packaging

- Main PyInstaller onedir: 170 files, 35,462,748 bytes.
- Separate helper executable: 7,275,904 bytes.
- Packaged main `--no-window` smoke: pass, including SQLite creation.
- SHA-256 manifest: 171 files.
- Inno Setup compile: not run because `ISCC.exe` is not installed.

The artifacts above are development outputs. Production release gates are
listed in `docs/IMPLEMENTATION_STATUS.md` and `docs/RELEASE_CHECKLIST.md`.
