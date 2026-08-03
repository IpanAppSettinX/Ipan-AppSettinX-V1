# WebView2 Evergreen bootstrapper

This document records the provenance and license of the Microsoft Edge
WebView2 Runtime bootstrapper that the application bundles for automatic
runtime installation.

## File

- **Name:** `MicrosoftEdgeWebview2Setup.exe`
- **Source:** official Microsoft Edge WebView2 download page.
- **Vendor:** Microsoft Corporation.
- **License:** Microsoft Edge WebView2 Runtime license terms (displayed by
  the bootstrapper UI when the user runs it). Distribution of the
  bootstrapper alongside an application is permitted by the Microsoft Edge
  WebView2 license.

## Where it must be placed

```
src/ipan_optimizer/data/MicrosoftEdgeWebview2Setup.exe
```

`installer/ipan_optimizer.spec` conditionally collects this file into
`_internal/ipan_optimizer/data/` inside the PyInstaller bundle. If the file
is absent at build time the build still succeeds, but the runtime
auto-install path will not be available and the app will exit with code 3
when the WebView2 runtime is missing.

## How it is launched

`src/ipan_optimizer/app/webview2_runtime.py::install_webview2` starts the
bootstrapper with its default UI — no `/silent` flag, no `/install` flag.
The user always sees the official Microsoft installer window and can
confirm or cancel. The app waits for the bootstrapper to exit, then
re-checks the runtime. If the user cancels, the app exits with a clear
Indonesian message; it never downloads anything itself.

The Inno Setup installer (`installer/IPANOptimizer.iss`) performs the same
flow at install time when WebView2 is missing.

## Verification

Detection reads the EdgeUpdate registry keys documented by Microsoft:

- `HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}\pv`
  (WOW64 32-bit view) — machine-wide install.
- `HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}\pv`
  — per-user install.

The `0.0.0.0` sentinel is treated as "not yet installed" (staging state).

## Test safety

Unit tests in `tests/unit/test_webview2_runtime.py` inject mock `reader`
and `runner` seams so no real Microsoft binary is ever launched and no host
registry mutation occurs in CI. The `headless=True` path (used by
`--no-window`) only performs detection and never installs.
