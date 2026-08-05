# Tasks

## Build EXE + Windows custom compatibility

- [x] Scan hardware akurat untuk semua device: nama prosesor asli via WMI
  `Win32_Processor` (bukan CPUID string), VRAM GPU asli via registry
  `HardwareInformation.qwMemorySize`, tipe storage/bus via enum mapping
  (SSD/HDD/NVMe/SATA/USB), RAM via WMI COM `Win32_PhysicalMemory` (bisa di
  Win11 24H2 tanpa wmic), kecepatan link jaringan dari string win32com.
  Terverifikasi 2026-08-06.
- [x] Smart Scan & Live Telemetry memakai data gaya Task Manager (PDH
  performance counter: GPU Engine util, GPU Adapter Memory, PhysicalDisk,
  Network Interface) sehingga berfungsi di semua Windows 10/11 + custom mod
  (XLite, KernelOS, Ghost Spectre, dll) TANPA perlu MSI Afterburner. Ikon
  hardware scan memakai Fluent System Icons `currentColor` agar tampil di
  semua tema. Terverifikasi 2026-08-06.
- [x] Build EXE wajib pakai PyInstaller **6.16.0** (pinned di
  `requirements-dev.lock`). PyInstaller 6.21+ memicu crash `0xc0000005` di
  bootloader offset `0xa462` ("minimum supported platform is Windows...")
  karena layout onefile baru (arsip dalam `.reloc`) + PE header 1970/no-ASLR
  memicu injeksi `apphelp.dll` → CFG trap. Layout klasik 6.16 (arsip di-append
  setelah image, ASLR ON) jalan normal. Terverifikasi 2026-08-06.
- [x] Riset mendalam Windows custom/debloated: AtlasOS, ReviOS, X Lite, KernelOS,
  Ghost Spectre, Nexus LiteOS, Tiny10/11, AME Privacy+/AME 10. Dokumentasi
  matrix 9 variant di `docs/COMPATIBILITY.md`.
- [x] Tambah `<activeCodePage>UTF-8</activeCodePage>` ke `installer/main.manifest`.
- [x] Perbaiki bug kritis: `uac_admin=True` di `ipan_optimizer.spec` dan
  `helper.spec`. Sebelumnya manifest embed PyInstaller masih `asInvoker`
  meski file manifest berkata `requireAdministrator`.
- [x] Bundle `MicrosoftEdgeWebview2Setup.exe` resmi Microsoft (176.809 bytes
  dari `go.microsoft.com/fwlink/p/?LinkId=2124704`) ke
  `src/ipan_optimizer/data/`. Terkoleksi ke
  `_internal/ipan_optimizer/data/` di dist.
- [x] Perbarui pesan `TweakResult.message` untuk menjelaskan service yang
  sudah dihapus pada Windows custom (fail-soft per step tidak berubah).
- [x] Build `dist/IPANOptimizer/IPANOptimizer.exe` (5.829.436 bytes) +
  `dist/IPANOptimizerHelper.exe`. Manifest ter-embed verified via `pefile`:
  `requireAdministrator` + `activeCodePage` + Win10/11 GUID.
- [x] Smoke test `--no-window` exit 0; semua gate lulus (`ruff`, `mypy`,
  `pytest` 104+4 passed, control matrix 62, frontend policy, asset budget).
- [ ] Compile Inno Setup installer `dist-installer/IPANOptimizer-Setup-0.1.0.exe`
  (butuh Inno Setup terpasang — pending user).
- [ ] Code-sign EXE + helper + installer dengan sertifikat OV/EV organisasi
  (pending user).
- [ ] Bundle Fixed Version WebView2 runtime folder sebagai fallback final untuk
  Tiny11 Core / AME Privacy+ (WinSxS dihapus, servicing rusak).

## Phase 0 - Specification freeze

- [x] Preserve the three source documents.
- [x] Initialize repository and root rules.
- [x] Create specification, architecture, threat, design, performance, asset,
  evidence, compatibility, and recovery documentation.
- [x] Pin the Python 3.12 dependency set, including resolved transitive packages.

## Phase 1 - Foundation

- [x] Typed contracts and structured logging.
- [x] SQLite migrations and repositories.
- [x] Fake and Dry Run backends.
- [x] Base pywebview shell and Indonesian design tokens.
- [x] Control matrix and validation scripts.
- [x] Initial automated tests.

## Phase 2 - Read-only scan and providers

- [x] Capability vector and resource guards.
- [x] Read-only Registry, service, and power-plan adapters.
- [x] Typed snapshots and Dry Run operation ledger.

## Phase 3 - Functional UI

- [x] Complete primary navigation and routes.
- [x] Connect every canonical control to a bridge or local handler.
- [x] Fake bridge state/error paths and browser E2E coverage.

## Phase 4 - Safety engine and tweaks

- [x] Allowlisted rule/policy catalog.
- [x] Transaction preview, apply, verify, rollback, and recovery journal.
- [x] Safe Dry Run tweak modules and conflict handling.

## Phase 5-8 - Safe implementation baseline

- [x] Dry Run game-session lifecycle.
- [x] Emulator discovery and atomic configuration primitive.
- [x] PresentMon CSV import and benchmark comparison.
- [x] Signed-plan validation boundary for a one-shot privileged helper.
- [x] PyInstaller main/helper builds, installer source, tests, and documentation.

## External release gates

- [ ] Implement and approve real mutating providers in a disposable Windows VM.
- [ ] Complete vendor-specific emulator schemas and restore verification.
- [ ] Integrate a separately reviewed PresentMon capture binary.
- [ ] Compile and validate the Inno Setup installer on the Windows VM matrix.
- [ ] Run runtime performance, reboot recovery, game, emulator, and hardware QA.
- [ ] Code-sign final binaries and installer with an organization certificate.

## Firebase member authentication

- [x] Replace the placeholder login rejection with typed Firebase Email/Password authentication.
- [x] Add fail-closed one-account/one-device binding enforced by Firestore Security Rules (atomic `commit`, no Cloud Functions required).
- [x] Hash the app-scoped Windows identifier locally and never transmit its raw value.
- [x] Document Firebase enablement, rules deployment, runtime configuration, and HWID reset.
- [ ] Deploy `firestore.rules` to the production Firebase project (`firebase deploy --only firestore:rules`).

## Curated artifact research and UI integration

- [x] Analyze the supplied EXE and BAT statically without execution.
- [x] Inventory the public Drive folder and analyze all downloadable text
  Registry/script configurations without executing them.
- [x] Separate inert Aim/Headshot marketing values from documented Windows
  settings and reject unvalidated mouse curves.
- [x] Add Safe, Caution, Dangerous, and Critical/Blocked risk presentation.
- [x] Add typed Dry Run pointer-linear and Game DVR capture rules with exact
  snapshot, verification, and rollback.
- [x] Keep Defender/Firewall/Update/TDR/BCD/bulk-service requests visible as
  warning-only cards with no executable operation.
- [x] Bundle the user-supplied IPAN Store logo and pinned non-AI SVG social
  icons with provenance and license notes.
- [x] Connect the new Tweak Library, warning dialogs, evidence actions, and all
  support links to tested handlers.

## Ipan AppSettinX interface and control audit

- [x] Rename visible product branding to Ipan AppSettinX V1.
- [x] Replace fabricated success and performance claims with state-based Indonesian copy.
- [x] Center transient status notifications and separate polite status from urgent alerts.
- [x] Remove decorative hero rings, mixed inline navigation icons, and entrance animation.
- [x] Convert unsupported Gaming and Advanced actions to analysis or official Settings flows.
- [x] Detect BlueStacks and MSI App Player read-only and report the available product version.
- [x] Reject empty transactions and generic tweak execution fail-closed.
- [x] Keep supplied BAT/REG operations non-executable because they violate policy or lack evidence.

## Apply experience and product copy refresh

- [x] Rename navigation to Smart Scan, Tweak Menu, Advanced Tweak Menu, Restore,
  Activity, Settings, and About Ipan AppSettinX.
- [x] Restore visible Apply Tweak actions while preserving typed transaction and
  fail-closed safety behavior.
- [x] Restore the documented pointer-linear and background-capture typed rules
  with exact snapshot, verification, and rollback.
- [x] Add a professional process/result overlay driven by real bridge work, with
  success shown only after a `VERIFIED` transaction.
- [x] Replace hardware letter badges with a pinned local subset of Microsoft
  Fluent System Icons and record provenance, hashes, and license.
- [x] Refresh Dashboard, Gaming, Tweak, Advanced, Scan, and About copy without
  introducing universal FPS, latency, aim, or anti-ban guarantees.
- [x] Remove visible Dry Run, evidence, and official-source controls while
  retaining internal evidence and development safety boundaries.

## Static menu parity and visual feedback

- [x] Recover the five supplied menu labels and per-branch command scope through
  static PE inspection without executing the untrusted binary.
- [x] Present APPLY REGEDIT, CLEAN TEMP FILES, APPLY BOOSTER, REVERT ALL CHANGES,
  and CLEAN LOG FILES in the original order without the NEW marker or source branding.
- [x] Keep destructive cleanup, BCD, service, and hard-coded restore commands
  blocked while exposing an Indonesian summary of every detected command group.
- [x] Drive Apply Tweak progress from background transaction stages and expose a
  numeric 0-100 result instead of a decorative indeterminate wait state.
- [x] Add an IpanSettinX V1 startup screen and refine White Mode and Critical
  action contrast within the existing local design system.
- [x] Extend the startup brand presentation and add dual-orbit Apply animation,
  phase labels, and a legible post-completion result interval without portraying
  blocked tweaks as injected or successful.

## UI Polish — animated loading screen and apply dial

- [x] Rework startup screen into a clean multi-ring orbital loader with a
  subtle monogram breathe, progress shimmer, and longer brand presentation.
- [x] Replace the dual-orbit Apply Tweak animation with a stage dial: a rotating
  pointer and four phase nodes that light up as the transaction advances.
- [x] Preserve reduced-motion fallback, token-only colors, and no gradients or
  generated art.

## Microsoft Fluent Design System refresh

- [x] Restore `AGENTS.md` and keep all safety boundaries intact.
- [x] Adopt Fluent visual language: layered surfaces, rounded corners, elevated
  shadows, pill-shaped navigation selection, and cleaner typography.
- [x] Replace startup monogram with animated Ipan Store logo (floating motion)
  while keeping the orbital rings.
- [x] Update titlebar, sidebar, cards, buttons, dialogs, and hardware cards to
  match Fluent elevation and spacing.
- [x] Add extended radius/shadow/spacing tokens and remove decorative corner
  accents in favor of purposeful elevation.

## Premium Dark Gaming Command Center redesign

- [x] Research best UI model for a paid Windows gaming optimizer and settle on
  a Premium Dark Command Center direction (Fluent base + gaming dashboard DNA).
- [x] Overhaul color tokens: deeper background layers, richer surfaces, stronger
  shadows, accent glow token, and `radius-2xl`.
- [x] Redesign startup screen: cinematic layered background, larger identity
  card, bigger orbital rings, glowing logo wrap, pill progress track.
- [x] Redesign app shell: logo badge in titlebar, pill system status, wider
  sidebar with rounded icon badges and pill active state.
- [x] Redesign components across all routes: hero card with top accent line and
  orbital decoration, dashboard metric widgets, tweak cards with top color rail,
  hardware cards, settings toggles, support grid, about panel, dialogs, and
  toast notifications.
- [x] Add navigation icon badges to every sidebar button for a visual command
  center feel.
- [x] Keep all `data-control-id`, route structure, and test assertions intact.

## Frameless window, custom controls, scrollbar, and telemetry

- [x] Hide native Windows title bar and enable frameless pywebview window with
  easy drag on the custom titlebar.
- [x] Add custom window controls (minimize, maximize, close) wired to bridge
  methods; add them to the control matrix and tests.
- [x] Style custom scrollbar with theme-matched track, thumb, and hover state.
- [x] Redesign Smart Scan as a telemetry dashboard: live CPU speed/load and RAM
  usage charts rendered on HTML5 canvas and updated every second from real
  bridge samples.
- [x] Audit and clean up Indonesian copywriting across dashboard, routes,
  settings, about, and toast messages.
- [x] Confirm typography stays on Segoe UI Variable / Segoe UI / system-ui with
  refined sizes and weights; no webfonts or external assets added.

## AppSensiX commercial copy refresh

- [x] Rebrand the four AppSensiX feature cards with a more aggressive premium
  gaming naming system, proprietary subtitles, benefit-led copy, and distinct CTAs.
- [x] Preserve all existing control IDs, typed handlers, transaction behavior,
  and fail-closed safety boundaries behind the refreshed presentation.
- [x] Synchronize the control matrix and add UI assertions for the new names and CTAs.

## User-facing copy and social identity refresh

- [x] Rename the first AppSensiX engine to OneTap Vector X and keep the naming
  focused on precision rather than automatic targeting.
- [x] Rewrite Fixes feature scope as user-facing outcomes without exposing
  internal Windows storage, service, or capture-component names.
- [x] Refresh Dashboard wording, IPAN Store support heading, and social icon
  presentation while preserving existing controls and offline assets.
- [x] Rewrite the visible Tweak 1-5 scope as user benefits and safety boundaries
  without exposing implementation jargon, and reduce the About support heading
  to a left-aligned Official Partner badge.
- [x] Synchronize Tweak 1-5 benefit-focused copy across the native and browser
  fallback catalogs, with regression tests that prevent implementation jargon
  from returning to visible cards.
- [x] Add a responsive member login gate with PC optimization loading visuals,
  spatial Ipan Store logo motion, fail-closed license validation, and allowlisted
  WhatsApp actions for account purchase and HWID reset.
- [x] Replace the generic login composition with an asymmetric hardware terminal,
  transparent IPAN Store wordmark, focused license copy, and login-level drag,
  minimize, and close controls for the frameless desktop window.
- [x] Reframe the login around real product capabilities instead of simulated
  telemetry: Smart Scan, hardware-aware tweaks, AppSensiX, and the protected
  Check/Snapshot/Verify/Restore transaction path.
- [x] Replace the login dossier with a looping hardware-diagnostic terminal
  (Cascadia Code/Mono) driven by a JavaScript typewriter engine: staged
  BOOT/SCAN/LOAD/SYNC/AUTH lines, per-line status, live caret, and pacing slow
  enough for users to watch each component check in real time.
- [x] Remove the protocol strip from the login visual, add a Maximize/Restore
  control to the login windowbar with glyph and aria state sync, disable
  body-level easy_drag so text selection never moves the frameless window,
  keep titlebar-only drag plus double-click maximize, and replace the loading
  chip with a hardware node assembly animation.

## Login terminal and readability audit

- [x] Restore the original compact system-diagnostic terminal and ambient motion
  after the expanded hardware-check composition felt visually overdesigned.
- [x] Keep the original real-time typewriter loop active and verify that it starts
  another cycle after the completed output hold.
- [x] Retain the improved login-form typography, contrast, wrapping, and action-row
  geometry at DPI-scaled sizes.
- [x] Convert the diagnostic output into a continuous single-stage carousel so
  CPU, GPU, memory, and the remaining checks replace one another without a
  completed-state hold or terminal freeze.
- [x] Animate `IPAN APP SETTINX // SYSTEM DIAGNOSTIC` with an independent
  terminal typewriter and blinking hacker-style signal while preserving the
  existing monospace font stack.
- [x] Slow the title and diagnostic typewriter pacing, type tags and statuses
  character-by-character, compact the single-row terminal viewport, and reuse
  the application's canonical All Rights Reserved footer.
- [x] Remove title reset and WAIT-status blinking, keep the completed title
  permanently visible, and increase all typewriter intervals to a deliberately
  slow presentation pace.
- [x] Replace character typing with whole-word reveals across the title, tags,
  diagnostic labels, dotted leaders, and statuses, holding 2.2 seconds between
  tokens and never rendering partial words.
- [x] Refresh login registration, lifetime-payment, and Reset HWID support copy
  while preserving the existing WhatsApp controls and responsive wrapping.

## Startup animation parity with ipanstore.my.id

- [x] Audit the splash screen timing on `https://ipanstore.my.id/` and confirm
  the reference duration: ~1200ms progress, 400ms hold, 700ms fade (~2200ms total).
- [x] Reduce `STARTUP_MIN_PRESENTATION_MS` from 50000 to 1500 so the splash
  matches reference pacing: rapid progress, brief hold, smooth 700ms fade-out.
- [x] Shrink per-stage `wait()` calls from 1800–3500ms to 60–110ms, keeping
  14 progressive stages with loadTweakCatalog, loadAdvancedTweaks, and dashboard
  navigation integrated between them.
- [x] Speed up the progress bar `transition` from 2400ms to 200ms so the bar
  visibly catches up to each stage without lag.
- [x] Add three `subtask-nodes` (CPU TWEAK, RAM BOOST, GPU TUNE) wired to the
  live progress value: WAIT until threshold, DONE at 30%/60%, READY at 90%.
- [x] Keep pulse-wait and pulse-ready CSS keyframes, `reduced-motion` fallback,
  token-only colors, and no gradients or generated art.
- [x] Update E2E `wait_for` timeout to 30000ms and confirm all 80 tests still
  pass after the timing change.
- [x] Tune startup to a readable sweet spot: 8000ms `STARTUP_MIN_PRESENTATION_MS`,
  350–450ms per stage for 14 stages (~5.5s active loading + ~2.5s hold + 700ms
  fade-out ≈ 8.7s total visible splash), with the progress bar `transition`
  smoothed to 500ms so each stage advancement is seen clearly without rushing.
- [x] Extend startup to a more cinematic pace: 15000ms
  `STARTUP_MIN_PRESENTATION_MS`, per-stage wait 620–880ms with natural variation
  (lighter stages ~620ms, heavier module loads ~880ms, yielding ~11.2s active
  loading + ~3.8s final hold + 700ms fade-out ≈ 15.7s total visible splash),
  with the progress bar `transition` extended to 650ms for smoother cinematic
  fill and all 80 tests still passing.
- [x] Shorten startup to roughly five seconds per user request: 5000ms
  `STARTUP_MIN_PRESENTATION_MS`, per-stage `creepStartupProgress` waits scaled
  to 350–450ms (~3.6s active stage animation, remainder absorbed by the final
  hold), keeping the parallel `loadStageWithProgress` behavior unchanged.

## Startup freeze fix (progress stuck at 52%)
- [x] Diagnose the freeze: the async stage set the label then `await`-ed a bridge
  call, so a slow/unresponsive backend left the percentage frozen with no motion.
- [x] Add `invokeWithTimeout` in `bridge.js` (default 6000ms) so catalog loads can
  never hang the startup sequence indefinitely.
- [x] Replace the blocking async stages with `loadStageWithProgress`, which
  advances the bar within a bounded range *in parallel* with the bridge call and
  stops one step below the ceiling until data actually arrives — RAM/GPU nodes are
  never marked DONE/READY before their data is ready.
- [x] On timeout or empty response, continue gracefully to the login page instead
  of stalling, surfacing the skip via the startup message copy.
- [x] Add `test_startup_progress_does_not_freeze_on_slow_backend` E2E regression
  that injects a 15s unresponsive `window.pywebview.api`, asserts progress only
  moves forward, reaches ≥40%, completes, and lands on the login screen; full
  suite now 81 passing.

## PyInstaller bundle `ERR_FILE_NOT_FOUND` fix

- [x] Diagnose: `frontend_path()` used `Path(__file__).resolve()` which does not
  point to a real on-disk file inside a PyInstaller one-folder bundle (code is
  packed in the PYZ archive), so WebView2 showed `ERR_FILE_NOT_FOUND` even
  though the frontend assets were correctly collected to
  `_internal/ipan_optimizer/frontend`.
- [x] Fix `frontend_path()` to use `sys._MEIPASS` when running inside a bundle
  and fall back to the `__file__`-relative location in dev mode.
- [x] Rebuild the EXE, verify the window loads the dark app theme (programmatic
  screenshot analysis: ~95% dark pixels, no Edge error page), and confirm the
  full suite still passes (88 passed, 4 deselected).

## Login form refresh: Username + License Key, Auth Trace overlay

- [x] Replace the Email field with a Username field (label copy + `type="text"`,
  loose validation, still mapped to the Firebase sign-in payload).
- [x] Add a third License Key field beside Username and Password, wired as the
  third `authenticate(username, password, license_key)` argument through the
  JS bridge into `app/auth.py` and `app/api.py` (fail-closed empty/oversized
  validation; license is trimmed and never logged).
- [x] Replace the login CPU/GPU/RAM/SSD node map (`.optimizer-stage-map`,
  `.map-node/.map-link/.map-core/.map-sweep` and their keyframes) with an
  "Auth Trace Minimal" panel: a terminal card listing DEVICE / HWID / LICENSE /
  AUTH rows whose fill lines light up in sequence as the real login stages
  advance, plus a single accent progress meter — one strong motif, mono type,
  no busy multi-ring animation.
- [x] Drive the active/done trace rows from the real `runLoginSequence` stage
  loop (parallel with the actual `authenticate` bridge call), preserving
  fail-closed behaviour and reduced-motion fallbacks.
- [x] Update unit, integration, and E2E tests for the new field, the trace
  overlay structure, and the renamed labels; full suite 88 passed, control
  matrix / frontend policy / asset budget valid.

## Windows 10/11 compatibility, auto-install WebView2, auto-elevate (policy override)

- [x] Replace the placeholder Windows compatibility GUID in `main.manifest`
  with the canonical Windows 10/11 GUID `{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}`
  so the OS treats the app as Windows 10/11-aware on every build (1809 through
  Windows 11 24H2+). Add `activeCodePage=UTF-8`.
- [x] Switch `main.manifest` execution level from `asInvoker` to
  `requireAdministrator` so the EXE always prompts UAC and runs elevated. This
  unblocks the HKLM/service/powercfg/bcdedit tweaks added in the previous
  session without requiring the user to manually "Run as administrator".
  **Policy override:** this contradicts the original `asInvoker` contract in
  ARCHITECTURE.md/SPEC.md; documented below and in AGENTS.md.
- [x] New module `src/ipan_optimizer/app/webview2_runtime.py`:
  - `is_webview2_installed(reader=None)` — single source of truth that reads
    the EdgeUpdate registry keys (machine + user, WOW64 32-bit view) and
    treats the `0.0.0.0` staging sentinel as "not installed".
  - `bootstrapper_path()` — resolves the bundled `MicrosoftEdgeWebview2Setup.exe`
    inside `sys._MEIPASS` (PyInstaller) or `src/ipan_optimizer/data/` (dev).
  - `install_webview2(exe_path, runner=None)` — launches the official
    Microsoft bootstrapper with its default UI (never silent), waits for it,
    returns the exit code.
  - `ensure_webview2(reader, runner, bundle_root, headless)` — orchestration:
    detect → run bootstrapper if missing → recheck. `headless=True` only
    detects, never installs (safe for `--no-window` smoke tests).
  - All host interaction goes through seam functions so tests mock without
    touching the real host.
- [x] Refactor `adapters/windows/capabilities.py::_detect_webview2` to call
  `is_webview2_installed` so capability detection and runtime bootstrap share
  the same logic. No behavioural change for existing capability scans.
- [x] Wire `ensure_runtime_requirements(headless=...)` into `main.py::main()`.
  Before opening the window, the app now ensures WebView2 is present; if the
  bootstrapper is bundled it is launched, otherwise the app exits with code 3
  and a clear Indonesian message. `--no-window` runs detection only.
- [x] `installer/ipan_optimizer.spec` now conditionally bundles
  `MicrosoftEdgeWebview2Setup.exe` into `_internal/ipan_optimizer/data/` when
  the developer has placed the official Microsoft file in
  `src/ipan_optimizer/data/`.
- [x] `installer/IPANOptimizer.iss` rewritten: when WebView2 is missing, the
  installer extracts and runs the bundled official Microsoft bootstrapper
  (non-silent) instead of hard-aborting. Still `PrivilegesRequired=lowest`;
  the EXE handles its own UAC via manifest.
- [x] Update `tests/packaging/test_artifacts.py`: assert
  `requireAdministrator` in both manifests, assert the Windows 10/11 GUID, and
  assert the installer auto-installs (not silent) WebView2 via the bootstrapper.
- [x] New `tests/unit/test_webview2_runtime.py` (13 cases): detection truth
  table, staging sentinel, non-Windows guard, bootstrapper path resolution,
  install runner contract, exit-code propagation, `ensure_webview2`
  orchestration (already-installed / headless / success-after-install /
  missing-bootstrapper / nonzero-exit / recheck-still-missing). All use mocks;
  no host mutation.
- [x] Document the policy override in `AGENTS.md`, `SPEC.md`,
  `ARCHITECTURE.md`, `THREAT_MODEL.md`, and `LAST_ACTIVITY.md`.
