# Compatibility

## Target

V1 target: Windows 10/11 x64, WebView2 Evergreen, at least two logical
processors, 4 GB RAM, and sufficient local storage.

Windows 10 remains technically supported with a non-blocking Indonesian notice
that regular support ended on 14 October 2025. Windows on ARM64 is explicitly
read-only/unsupported for mutation.

## Compatibility model

Compatibility is capability-based. Missing WMI, services, policies, Windows
components, or unknown emulator schemas produce unavailable or read-only
states, never blind repair. Every `sc config`, `reg add`, `bcdedit`,
`powercfg`, and `taskkill` step in `core/tweak_engine.py` runs with
`check=False` and a 30-second timeout; per-step failures are recorded but never
abort the whole apply pass. On stripped Windows where a target service has
already been removed (e.g. `WinDefend`, `wuauserv`, `DiagTrack` on AME Privacy+
or Tiny11 Core), the step logs a non-zero exit and the final message explains
that some operations may fail on custom Windows.

## Windows 10/11 all-version awareness

`installer/main.manifest` declares:

- `<supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>` — the canonical
  Windows 10 / Windows 11 GUID. Every Win10 build (1809–22H2), every Win11
  build (21H2–25H2), every LTSC/IoT edition, and every stripped variant that
  inherits the base build's identity shares this GUID.
- `<requestedExecutionLevel level="requireAdministrator"/>` — the EXE always
  prompts UAC and runs elevated so HKLM/`sc config`/`powercfg`/`bcdedit`
  tweaks apply without a manual "Run as administrator". Enforced in the
  PyInstaller spec via `uac_admin=True` (the `manifest=` argument alone does
  not override the bootloader's default `asInvoker` execution level).
- `<dpiAware>true/pm</dpiAware>` + `<dpiAwareness>PerMonitorV2</dpiAwareness>`
  — crisp DPI on all builds.
- `<activeCodePage>UTF-8</activeCodePage>` — Win10 1903+ and all Win11; gives
  the process UTF-8 as the active code page. Harmlessly ignored on older builds.
- `<longPathAware>true</longPathAware>` — Win10 1607+ with the
  `LongPathsEnabled` policy.

## Custom / debloated Windows variant support

The app is designed to run on the common debloated Windows variants. The table
below summarises the compatibility profile of each, based on primary-source
documentation where available and community reputation otherwise.

| Variant | Base | Edge | WebView2 RT | WMI | WinSxS | Defender | WU | Support |
|---|---|---|---|---|---|---|---|---|
| AtlasOS | Win11 24H2/25H2 | optional remove | kept | on | kept | toggle (on default) | supported | **Full** |
| ReviOS | Win10 22H2 + Win11 23/24/25H2 | removed (default) | **kept** | on | kept (CAB-emptied) | disabled | paused | **Full** |
| AME Privacy+ / AME 10 | Win11 / Win10 | removed | assume absent | verify | deleted | **removed** | removed | Best-effort |
| Tiny11 (regular) | any Win11 | removed | installable | on | kept | present | works | **Full** |
| Tiny11 Core | any Win11 | removed | may fail to install | on | **deleted** | disabled | broken | Best-effort |
| Ghost Spectre | Win10/11 | removed | assume absent | on | trimmed (Compact) | removed (Superlite) | disabled | **Full** (bundled bootstrapper required) |
| Nexus LiteOS | Win10/11 | removed | usually kept | on | kept | disabled | disabled | **Full** |
| X Lite OS | Win10/11 | removed | assume absent | on | trimmed | disabled | disabled | **Full** (bundled bootstrapper required) |
| KernelOS | Win11 | optional | likely kept | on | kept | toggle | disabled | **Full** |

### Key facts that make this work

1. **pywebview `edgechromium` does NOT require the Edge browser.** It requires
   the WebView2 Runtime only. Microsoft documents: "A production release of a
   WebView2 app can only use the WebView2 Runtime as the backing web platform,
   not Microsoft Edge." So ReviOS / Ghost Spectre / X Lite / Tiny11 — which
   remove Edge but keep (or can install) the WebView2 Runtime — all run the
   app's UI correctly.
2. **WebView2 bootstrapper is bundled.** `src/ipan_optimizer/data/
   MicrosoftEdgeWebview2Setup.exe` is collected into
   `_internal/ipan_optimizer/data/` by `installer/ipan_optimizer.spec`.
   `app/webview2_runtime.py::ensure_webview2` detects the runtime via the
   EdgeUpdate registry keys and, when absent, launches the bundled official
   Microsoft bootstrapper (never silent — the user always sees the Microsoft
   installer UI). This covers Ghost Spectre, X Lite, Tiny11 regular, AME
   Privacy+, and any variant where Edge and/or the runtime was removed.
3. **psutil does not require the WMI service.** Core CPU/mem/disk/process
   stats use native Win32 APIs. The WMI service (`winmgmt`) is running on
   every documented variant; even if it were disabled, psutil's core paths
   would still work.
4. **UCRT (`ucrtbase.dll`) is a core Windows system DLL on all Win10/11
   builds** and is not removed by any documented debloat. The floor is Win10
   1809, so UCRT is always present.
5. **VC runtime DLLs are bundled.** PyInstaller collects `vcruntime140.dll`,
   `msvcp140.dll`, and `vcruntime140_1.dll` next to the EXE, so the app does
   not depend on a system-installed VC++ redistributable package (which
   Atlas/ReviOS/Tiny11 do not bundle and which may fail to install on Tiny11
   Core or AME Privacy+ where the servicing stack is broken).
6. **`requireAdministrator` works on every variant.** None disable UAC by
   default. Variants that disable UCPD (Atlas, ReviOS) actually make
   `sc config`/file-association tweaks easier, not harder.

### Best-effort variants (Tiny11 Core, AME Privacy+)

On variants where WinSxS is deleted or the servicing stack is broken, the
WebView2 Evergreen bootstrapper may fail to install. The app will exit with
code 3 and a clear Indonesian message directing the user to install the
WebView2 Runtime manually. A future hardened build may bundle the **Fixed
Version** WebView2 runtime folder (no installer, no WinSxS dependency) as a
final fallback.

### Code-signing note

On variants with Defender removed (ReviOS, AME Privacy+, Ghost Spectre
Superlite, X Lite, Tiny11 Core, Nexus), the system has no AV by default — so
no false positive from Defender. But users typically install a third-party AV,
which is more aggressive than Defender on unsigned PyInstaller EXEs (the
bootloader is a common false-positive target). Code-signing the EXE, helper,
and installer with the same OV/EV certificate before public release is the
single most impactful mitigation. Submit the signed EXE to the Microsoft
Security Intelligence submission portal so reputation propagates to Smart App
Control and third-party cloud lookups.

## Automated testing

Automated compatibility uses deterministic fixtures. Real behavior requires
disposable Windows VMs and dedicated hardware QA. The recommended VM matrix:

- Stock Win10 22H2
- Stock Win11 24H2
- AtlasOS (Win11 24H2)
- ReviOS (Win11 24H2 with Edge removed)
- Tiny11 regular

These exercise every failure mode that matters for this app.
