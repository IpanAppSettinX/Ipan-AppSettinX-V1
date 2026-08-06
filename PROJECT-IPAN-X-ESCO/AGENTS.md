# Repository rules

## Session start (mandatory)

At the start of every new session, before doing anything else, read
`LAST_ACTIVITY.md` to recover the context of the most recent work. When you
finish work in the current session, you must update `LAST_ACTIVITY.md` with the
latest entry placed at the top.

Read `SPEC.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, and `TASKS.md` before
changing behavior. The product specification is `Blueprint_IPAN_Optimizer.md`;
`Riset_Tweak_Gaming_Windows_10_11.md` is the evidence baseline and
`Prompt_Codex_IPAN_Optimizer.md` is the implementation contract.

## Safety boundaries

- Development and automated tests use fake or Dry Run backends only.
- Never execute a real tweak, Registry mutation, service change, process close,
  power-plan change, emulator-config write, or elevated helper on a developer
  host.
- The UI receives only narrow typed API methods. Never expose generic Registry,
  filesystem, command, subprocess, or elevation APIs.
- Defender, Firewall, UAC, Windows Update, tamper protection, and exploit
  mitigations remain enabled. Prohibited operations must fail closed.
- Preserve exact typed snapshots and compare expected state before apply and
  rollback.

## Policy overrides (user-approved, documented)

The following production behaviours intentionally override the default safety
contract above. They are confined to the packaged release EXE and installer,
never to test runs, and each carries a documented mitigation.

1. **`requireAdministrator` execution level (release EXE).** The release EXE
   must run elevated (UAC on double-click). It is a system-tweaking tool
   (HKLM Registry, services, `powercfg`, `bcdedit`) and WebView2 has been
   verified to run fine elevated on this stack. Privileged tweak steps are
   executed directly with the elevated token (see
   `src/ipan_optimizer/privileged/runner.py`); the `runner` module also keeps
   a self-elevation path (`ShellExecuteExW "runas"` → `--apply-plan`) that is
   used only if the EXE is ever built `asInvoker`. Historical note: an earlier
   `asInvoker` + relaunch-guard design (see LAST_ACTIVITY 2026-08-06) was
   replaced because the product requirement is that the app MUST run as
   administrator. `requireAdministrator` + the old 1970-timestamp PyInstaller
   bootloader previously triggered `apphelp` injection → `0xc0000005`; current
   builds (PyInstaller 6.21, patched header with real TimeDateStamp + CheckSum)
   run elevated cleanly. Mitigation: tests set
   `IPAN_OPTIMIZER_NO_ELEVATION=1` (autouse fixture in `tests/conftest.py`) so
   no host mutation beyond existing integration tests happens in CI; the Dry
   Run overlay remains the default backend in development.
2. **Automatic WebView2 runtime install.** When the Microsoft Edge WebView2
   Runtime is missing, the app launches the official Microsoft bootstrapper
   (`MicrosoftEdgeWebview2Setup.exe`) bundled under
   `src/ipan_optimizer/data/`. The installer is never silent: the user always
   sees the official Microsoft installer UI. If the bootstrapper is not
   bundled, the app exits with a clear message and never downloads anything.
   Mitigation: detection and launch go through seam functions in
   `src/ipan_optimizer/app/webview2_runtime.py`; tests inject mocks so no
   real Microsoft binary is ever launched and no host mutation occurs in CI.
3. **Windows 10/11 all-version compatibility.** `main.manifest` declares the
   canonical Windows 10/11 supportedOS GUID so every build (1809 through
   Windows 11 24H2+) treats the app as Windows-aware.

## Structure and style

- Python source lives under `src/ipan_optimizer`; use Python 3.12 type hints.
- Frontend is packaged local HTML/CSS/vanilla ES modules with Indonesian copy.
- Use semantic controls with unique `data-control-id` values.
- Component CSS uses tokens from `tokens.css`; no gradients, webfonts, emoji
  controls, generated art, or mixed icon families.
- Keep user data out of logs; structured logs must redact paths and identifiers.

## Commands

Run from the repository root with the pinned venv (`.venv\Scripts\python.exe`).
The venv must be rebuilt after a Windows reinstall: `pyvenv.cfg` points at the
base interpreter (`C:\Python312` on this host); fix `home`/`executable` there
if Python moved, then `python -m pip install -r requirements-dev.lock`.

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest
python scripts/check_control_matrix.py
python scripts/check_frontend_policy.py
python scripts/check_asset_budget.py
```

## Packaging build (release EXE)

- **Build with PyInstaller 6.21.0 from the global interpreter
  `C:\Python312`** (the pinned venv keeps `pyinstaller==6.16.0` for gates
  only — PyInstaller is not part of the test gates). Earlier builds pinned
  6.16.0 because of a misdiagnosis: the intermittent `0xc0000005` at
  bootloader offset `0xa462` was blamed on PyInstaller 6.21, but it is a
  host-environment problem (it also crashes `ruff.exe`, an unrelated Rust
  binary, at the same offset). On this host the 6.16 bootloader's appended
  onefile layout is rejected at load time ("not a valid application for this
  OS platform") while the 6.21 bootloader loads and runs correctly.
- Build: `C:\Python312\python.exe -m PyInstaller --clean --noconfirm installer/ipan_optimizer.spec`
- Output: `dist/Ipan AppSettinX V1.exe` (single file). Copy to
  `dist_new/` so both locations ship the same artifact.
- **Verify before shipping:**
  `python scripts/verify_exe.py "dist/Ipan AppSettinX V1.exe"` — checks the
  PE (x64, GUI subsystem, sane subsystem version), that the manifest is
  `requireAdministrator`, and that `--no-window` starts and exits 0 (launched
  elevated). Do not ship an EXE that fails this.
- **The release EXE requires Administrator.** Double-clicking shows a UAC
  prompt and the app runs elevated; every tweak (Tweak Menu, Advanced Menu,
  AppSensiX) is then applied directly with the elevated token — HKLM registry,
  service config, powercfg, bcdedit all actually take effect. There is no
  per-tweak UAC and no "Run as administrator is forbidden" guard.
- **Never run the release EXE "as administrator".** The app is `asInvoker`
  and elevates on demand. Running it elevated breaks the WebView2 host and
  surfaces "minimum supported platform is Windows..." errors. `main.py`
  detects elevation and relaunches without elevation
  (`_is_elevated` / `_relaunch_without_elevation`).
- The host occasionally kills process startups (the `0xa462` crash). When an
  EXE fails to start, retry; check the app log at
  `%LOCALAPPDATA%\IPAN Optimizer\logs\ipan-optimizer.jsonl`.

## Definition of done

A change is complete only when formatting, static checks, relevant unit,
integration, security, and UI tests pass; documentation, `TASKS.md`, and
`LAST_ACTIVITY.md` reflect the result; no test mutates the host; and every
visible control is mapped to a handler and test in `docs/CONTROL_MATRIX.md`.
