# Changelog

## 0.1.0 - Unreleased

- Debloat Windows (`adv.debloat_windows`) fifth fix (final): switched to the
  all-users removal the user's manual script confirmed works —
  `Get-AppxPackage -AllUsers | Remove-AppxPackage -AllUsers` (requires admin;
  the release EXE runs `requireAdministrator` so the spawned PowerShell inherits
  the elevated token). Per-user native removal (HRESULT 0x80073CFA) and per-user
  PowerShell (exit 1) both failed because the packages are provisioned for all
  users. Verified elevated with `-WhatIf`: all 22 target packages are targeted
  without removing anything. Flow: enumerate(-AllUsers) -> remove(-AllUsers) ->
  verify re-scan -> per-package retry -> native last resort -> report the true
  removed count.
- Debloat Windows (`adv.debloat_windows`) fourth fix: the PowerShell fallback
  used `Get-AppxPackage -Name @('x')`, which the `-Name` (String) parameter
  rejects with a binding error — so the fallback never actually removed
  anything exactly when it was needed. It now filters via
  `Get-AppxPackage | Where-Object { $names -contains $_.Name } |
  Remove-AppxPackage` (verified working for 1..N names). `run_appx_debloat`
  also re-scans the deployment after both paths and reports the true number of
  removed packages, with native + fallback error detail when nothing was
  removed.
- Debloat Windows (`adv.debloat_windows`) third fix: the pythonnet runtime
  initialisation is now idempotent. The bundled pythonnet raises
  `RuntimeError: The runtime ... has already been loaded` when `set_runtime()`
  is called again after `import clr`, so the second Debloat run in the same app
  process failed with "semua operasi gagal". `set_runtime(get_netfx())` is now
  only invoked when `get_runtime_info()` is `None`, making repeated applies
  safe. Verified with a frozen probe (3 consecutive loads succeed, elevated and
  non-elevated).
- Debloat Windows (`adv.debloat_windows`) second fix: the tweak no longer goes
  through the UAC/elevated-helper relaunch path (which failed with "semua
  operasi gagal" even when the EXE ran as Administrator on custom Windows).
  The step now runs in-process with `requires_admin=False` — per-user AppX
  removal needs no elevation, matching the manual `Remove-AppxPackage` script
  users confirm works. Added a per-user PowerShell fallback (no `-AllUsers`) for
  packages the native deployment call cannot remove, a 240 s watchdog specific
  to this step, and richer error detail in the failure message.
- Fixed Debloat Windows (`adv.debloat_windows`) so Apply really removes the
  bundled bloatware: replaced the `powershell.exe Get-AppxPackage -AllUsers |
  Remove-AppxPackage` command (which fails or hangs — `-AllUsers` needs a
  trusted-package capability even when elevated, and stripped Windows can ship
  a broken powershell) with a native in-process implementation via pythonnet →
  `Windows.Management.Deployment.PackageManager` (COM to AppXSVC). Each target
  package is removed per-user with its own 25 s watchdog (nothing can freeze
  the progress bar); system-critical packages are protected; one stubborn app
  never fails the whole tweak.
- Established specification-driven project structure.
- Added safe fake/Dry Run architecture and initial local UI.
- Added capability, transaction, control-matrix, security, and packaging gates.
- Reworked the pywebview interface into a professional gaming command center
  with simplified navigation, technical status panels, and clearer workflows.
- Fixed persistent action-state handling for game and benchmark controls, added
  one-click safe recommendation selection, and expanded end-to-end interaction
  coverage.
- Added an audited Tweak Library with Safe, Caution, Dangerous, and
  Critical/Blocked distinctions, transaction warning acknowledgement, and
  warning-only cards for Defender, Firewall, Update, BCD, TDR, service, and
  cleanup risks.
- Added conservative pointer-linear and Game DVR capture Dry Run rules with
  snapshot, verification, and rollback; rejected fabricated Aim/Headshot value
  names and unvalidated binary mouse curves.
- Added the user-supplied IPAN Store logo, pinned local SVG social icons, and
  allowlisted Website, WhatsApp, Discord, Instagram, TikTok, and WhatsApp
  Channel actions.
- Documented static analysis of the supplied unsigned EXE, BAT, and 303 text
  configurations from the public Drive corpus without executing untrusted
  content.
- Refreshed navigation and product copy, restored functional Apply Tweak entry
  points, and added a stateful gaming process overlay that reports success only
  after transaction verification.
- Reinstated pointer-linear and background-capture typed rules and replaced
  Smart Scan letter badges with pinned Microsoft Fluent System Icons.
