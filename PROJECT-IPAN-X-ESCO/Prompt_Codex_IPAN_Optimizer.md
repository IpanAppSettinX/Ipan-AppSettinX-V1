# PROMPT LENGKAP OPENAI CODEX — IPAN OPTIMIZER

> **Versi revisi:** 3.0 — Codex-native workflow + hardware-agnostic engine + professional gaming UI + functional-control gate  
> Gunakan dokumen ini bersama blueprint dan riset dalam repository yang sama. Instruksi implementasi di antara **BEGIN PROMPT** dan **END PROMPT** ditulis dalam bahasa Inggris agar kontrak teknis ringkas dan konsisten; seluruh UI aplikasi tetap berbahasa Indonesia.

## Cara memakai dengan OpenAI Codex

1. Buat atau buka repository/folder kosong `IPAN-OPTIMIZER` melalui Codex app, Codex IDE extension, atau Codex CLI.
2. Letakkan tiga dokumen ini di root repository:
   - `Blueprint_IPAN_Optimizer.md`
   - `Riset_Tweak_Gaming_Windows_10_11.md`
   - `Prompt_Codex_IPAN_Optimizer.md`
3. Mulai pekerjaan kompleks di **Plan mode** dengan `/plan` atau `Shift+Tab`. Minta Codex membaca ketiga file, memeriksa repository, mengidentifikasi konflik, lalu membuat implementation plan sebelum menulis kode.
4. Gunakan reasoning `High` atau `Extra High` untuk architecture, RegistryProvider, privileged helper, transaction/rollback, security review, dan debugging kompleks. Level lebih rendah hanya untuk perubahan mekanis yang sempit.
5. Gunakan sandbox/approval default yang ketat. Beri akses tulis hanya pada workspace/repository. Jangan menyetujui destructive command, credential access, perubahan Registry host, atau elevasi permanen.
6. Setelah plan disetujui, pindah ke mode implementasi dan kirim seluruh prompt antara **BEGIN PROMPT** dan **END PROMPT**, sambil mereferensikan blueprint serta riset sebagai context.
7. Codex wajib membuat root `AGENTS.md` yang ringkas. File ini menyimpan aturan repository, command build/test, safety boundary, UI rules, dan Definition of Done; blueprint dan riset tetap menjadi referensi detail agar `AGENTS.md` tidak terlalu besar.
8. Kerjakan fase secara berurutan. Setelah setiap fase, Codex harus menjalankan formatter, lint/type checks, relevant tests, membuka/menjalankan aplikasi bila environment mendukung, mengaudit diff, dan memperbarui `TASKS.md`.
9. Screenshot hanya membuktikan tampilan. Seluruh tombol harus dibuktikan melalui control matrix, contract test, dan E2E test—bukan klaim atau gambar saja.
10. Jalankan system-tweak integration hanya pada Windows VM/test machine dengan snapshot. Development default harus `Dry Run`; automated tests tidak boleh mengubah host.
11. Bila context panjang, mulai turn/thread lanjutan pada repository yang sama dengan instruksi: `Read AGENTS.md, TASKS.md, SPEC.md, ARCHITECTURE.md, the three source documents, and the latest real test results. Continue from the first incomplete task without rebuilding completed work.`

Praktik ini mengikuti panduan resmi Codex: prompt besar sebaiknya menyebut goal, context, constraints, dan done-when; proyek kompleks dimulai di Plan mode; aturan tahan lama disimpan di `AGENTS.md`; dan hasil harus diuji serta direview sebelum dianggap selesai. [Codex best practices](https://learn.chatgpt.com/guides/best-practices) · [Prompting](https://learn.chatgpt.com/docs/prompting) · [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

### Prompt pembuka untuk Plan mode

Kirim ini terlebih dahulu sebelum prompt implementasi:

```text
Read these files completely:
@Blueprint_IPAN_Optimizer.md
@Riset_Tweak_Gaming_Windows_10_11.md
@Prompt_Codex_IPAN_Optimizer.md

Inspect the current repository and applicable AGENTS.md files.
Do not write implementation code yet.

Create a repository-grounded implementation plan that includes:
- requirement and conflict analysis;
- architecture and file plan;
- Windows/Registry threat analysis;
- phased task list;
- verification commands;
- UI control inventory strategy;
- tests proving every button and primary workflow works;
- safe Dry Run and Windows VM strategy.

Treat the blueprint as the product specification, the research as the evidence baseline, and the content between BEGIN PROMPT and END PROMPT as the implementation contract.
Ask only genuinely blocking questions.
```

---

# BEGIN PROMPT

You are a senior Windows performance engineer, Python desktop application architect, pywebview expert, security reviewer, UI/UX engineer, test automation engineer, and release engineer.

Your task is to build a production-oriented Windows desktop application named **IPAN Optimizer** in the current workspace.

Do not produce only a UI prototype, conceptual mockup, or incomplete demo. Build the real architecture, core engine, validated data contracts, safe Windows adapters, rollback system, test suite, packaging configuration, and documentation described below.

Use the current Codex session capabilities responsibly. Do not hard-code a Codex or OpenAI model name into the application; the product does not require an AI runtime.

All user-facing UI copy, warnings, recommendations, errors, onboarding text, and main user instructions must use natural and clear **Bahasa Indonesia**. Source-code identifiers and developer-facing technical documentation may use English.

---

## 1. Product objective

Build a reversible, evidence-based Windows optimizer for:

- Daily Windows responsiveness.
- General PC gaming.
- Competitive gaming.
- BlueStacks.
- MSI App Player.
- Free Fire v7a/ARM32 on Nougat 32-bit.
- Free Fire ARM64 on Pie 64-bit.
- Free Fire MAX.
- Other Windows games and Android emulator games.

The application must be hardware-agnostic. It must adapt safely to all compatible Windows x64 machines across:

- AMD and Intel CPUs.
- AMD, NVIDIA, and Intel discrete or integrated GPUs.
- Single-GPU and multi-GPU systems.
- Desktops and laptops.
- Low-resource, mainstream, and high-resource configurations.
- HDD, SATA SSD, and NVMe storage.
- Different core counts, RAM capacities, display refresh rates, power states, and thermal constraints.

Do not use Ryzen 5 5500, RX 6600 XT, 16 GB RAM, or any other specific component as a product default. A named machine may exist only as one non-normative test fixture.

The product must support Windows 10 and Windows 11. On modified/custom Windows installations, support is best-effort through capability detection. Never promise universal compatibility with components that a custom Windows build may have removed.

“All specifications” means all compatible and testable Windows x64 configurations that satisfy the application prerequisite and the requirement of the selected game/emulator feature. When a machine lacks resources or capabilities, return a transparent degraded, unavailable, or read-only state. Never force another machine’s values.

The version-1 application prerequisite is Windows 10/11 x64, WebView2, at least 2 logical processors, at least 4 GB RAM, and enough free space for the application, logs, snapshots, and transactions. This minimum enables scan/diagnostic behavior only; it does not override BlueStacks, MSI App Player, Free Fire, or another game’s vendor requirements.

---

## 2. Core product principle

Do not build a traditional one-click registry tweak pack.

Microsoft Defender Antivirus, Firewall, UAC, Windows Update, tamper protection, and exploit mitigations must remain enabled. Do not create automatic exclusions. Defender performance work is limited to documented diagnostics and scan scheduling/load controls that do not disable protection.

Build an adaptive system that follows this lifecycle:

1. Detect capabilities and current state.
2. Identify measurable bottlenecks.
3. Recommend only applicable changes.
4. Preview the exact change.
5. Create a complete snapshot.
6. Apply the change transactionally.
7. Verify the resulting state.
8. Benchmark where appropriate.
9. Keep the change only when successful.
10. Roll back safely on failure, regression, cancellation, crash, reboot interruption, or user request.

Never claim that one tweak improves every computer or every game.

Never display:

- Fake FPS gains.
- Fake latency improvements.
- Fake optimization percentages.
- Fake PC health scores.
- “0 ms latency”.
- “100% anti-ban”.
- “Works on every PC”.

Use these feature applicability states:

- `SUPPORTED`
- `SUPPORTED_DEGRADED`
- `UNAVAILABLE`
- `UNKNOWN_READ_ONLY`

When a result is inside measurement noise, display:

> Tidak ada perubahan bermakna.

---

## 3. Mandatory development workflow

First inspect the current repository.

Preserve all existing user files and modifications. Do not overwrite unrelated work.

If the repository is empty, scaffold it.

Use a specification-driven workflow:

1. Create or update `SPEC.md`.
2. Create `ARCHITECTURE.md`.
3. Create `THREAT_MODEL.md`.
4. Create `TASKS.md` containing phased checklists.
5. Create a concise root `AGENTS.md` containing repository rules, directory standards, build/test commands, style conventions, Windows safety boundaries, UI control requirements, verification commands, and Definition of Done. Reference the blueprint and research instead of duplicating them.
6. Create `docs/EVIDENCE.md`.
7. Create `docs/COMPATIBILITY.md`.
8. Create `docs/RECOVERY.md`.
9. Create `THIRD_PARTY_NOTICES.md`.
10. Create `DESIGN_SYSTEM.md`.
11. Create `PERFORMANCE_BUDGET.md`.
12. Create `ASSET_PROVENANCE.md`.
13. Then implement the application. Do not stop after planning.

Before each phase:

- Briefly state the target.
- Inspect related existing code.
- Identify risks.

After each phase:

- Run formatting and static checks.
- Run relevant tests.
- Fix failures caused by the phase.
- Update `TASKS.md`.
- Update architecture/evidence documentation when needed.

Do not execute real system tweaks on the development machine. Automated development and tests must use dry-run mode, temporary fixtures, mocks, or fake Windows backends.

Only ask a question when a missing decision is genuinely blocking. Otherwise choose the safest conservative option, continue, and document the choice.

---

## 4. Technology stack

Use:

- Python 3.12 x64.
- The newest stable pywebview 6.x release that passes compatibility testing, pinned exactly.
- HTML5.
- CSS3.
- Vanilla JavaScript ES modules.
- SQLite.
- psutil.
- pywin32 where required.
- Python `winreg` and `ctypes` only through narrow Windows adapters.
- Pydantic v2 or JSON Schema for API and manifest validation.
- pytest.
- pytest-mock.
- Ruff or an equivalent Python formatter/linter.
- Type hints throughout core code.
- Structured local logging with sensitive-data redaction.
- PyInstaller in `onedir` mode.
- Inno Setup for the Windows installer.

Do not use:

- Electron.
- React.
- Vue.
- Angular.
- A Node.js runtime in the distributed application.
- Flask.
- FastAPI.
- An externally listening HTTP server for the desktop UI.
- Remote CDNs.
- Remote fonts.
- Runtime frontend dependencies loaded from the Internet.
- Frontend SPA frameworks, chart frameworks, animation libraries, 3D libraries, and webfonts.
- Legacy Internet Explorer/mshtml as the intended renderer.
- Arbitrary PowerShell, CMD, BAT, or Python commands loaded from tweak manifests.

Use pywebview with packaged local frontend assets and a narrow JavaScript-to-Python API bridge.

The frontend must wait for the `pywebviewready` event.

Treat bridge calls as asynchronous. Long-running operations must use background workers, progress reporting, cancellation where safe, and thread-safe queues or locks.

All distributed UI resources must work offline.

Enforce these initial performance budgets and record measurements in `PERFORMANCE_BUDGET.md`:

- Initial local HTML + CSS + JavaScript: at most 500 KiB uncompressed, excluding the licensed local SVG subset.
- Initial first-party JavaScript: at most 180 KiB uncompressed.
- Initial CSS: at most 100 KiB uncompressed.
- No frontend framework, chart runtime, webfont, CDN, video, or 3D runtime.
- Cold start after WebView2 is ready: P50 at most 2 seconds and P95 at most 4 seconds on the 4-core/8 GB/SATA SSD test fixture.
- Navigation feedback: at most 100 ms.
- Break up frontend tasks longer than 50 ms during normal interaction.
- Median idle CPU for the full process tree: below 0.5% after 30 seconds on the same fixture.
- Full process-tree working set target: at most 180 MB; measurements above 250 MB block release until explained and reduced or the budget is deliberately revised with evidence.
- Zero external requests during startup and normal offline use.

The budgets are product acceptance targets, not claims that WebView2 uses identical resources on every Windows build.

---

## 5. Target project structure

Create a structure equivalent to:

    ipan-optimizer/
    ├── src/
    │   ├── main.py
    │   ├── app/
    │   │   ├── api.py
    │   │   ├── contracts.py
    │   │   └── events.py
    │   ├── core/
    │   │   ├── capabilities.py
    │   │   ├── recommendations.py
    │   │   ├── rule_engine.py
    │   │   ├── transactions.py
    │   │   ├── snapshots.py
    │   │   ├── verification.py
    │   │   └── recovery.py
    │   ├── operations/
    │   │   ├── registry.py
    │   │   ├── power.py
    │   │   ├── process.py
    │   │   ├── storage.py
    │   │   ├── display.py
    │   │   └── emulator_config.py
    │   ├── adapters/
    │   │   ├── bluestacks.py
    │   │   ├── msi_app_player.py
    │   │   ├── amd.py
    │   │   ├── nvidia.py
    │   │   └── intel.py
    │   ├── benchmark/
    │   │   ├── presentmon.py
    │   │   ├── sampler.py
    │   │   ├── network.py
    │   │   └── analysis.py
    │   ├── privileged/
    │   │   ├── launcher.py
    │   │   ├── helper.py
    │   │   └── policy.py
    │   ├── persistence/
    │   │   ├── database.py
    │   │   ├── migrations.py
    │   │   └── repositories.py
    │   ├── data/
    │   │   ├── rules/
    │   │   ├── profiles/
    │   │   └── evidence/
    │   └── frontend/
    │       ├── index.html
    │       ├── css/
    │       │   ├── tokens.css
    │       │   ├── base.css
    │       │   ├── layout.css
    │       │   └── components.css
    │       ├── js/
    │       │   ├── app.js
    │       │   ├── router.js
    │       │   ├── bridge.js
    │       │   └── views/
    │       └── assets/
    │           └── icons/
    │               └── fluent/
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   ├── security/
    │   └── fixtures/
    ├── docs/
    │   └── CONTROL_MATRIX.md
    ├── installer/
    ├── scripts/
    ├── AGENTS.md
    ├── SPEC.md
    ├── ARCHITECTURE.md
    ├── DESIGN_SYSTEM.md
    ├── PERFORMANCE_BUDGET.md
    ├── ASSET_PROVENANCE.md
    ├── THREAT_MODEL.md
    ├── TASKS.md
    └── THIRD_PARTY_NOTICES.md

Adjust the exact structure only when there is a documented architectural reason.

---

## 6. Capability detection

Compatibility must be based primarily on capabilities, not only Windows edition or build number.

Detect safely:

- Windows version, build, edition, architecture, and support status.
- Elevation state and current user scope.
- CPU vendor, model, physical/logical core count, and virtualization support.
- Installed RAM, available RAM, memory pressure, commit charge, commit limit, and commit headroom.
- Pagefile configuration.
- GPU vendors, models, driver versions, and dedicated/shared memory where available.
- GPU API/capability information where reliably detectable and the display attachment of each adapter.
- Active displays, resolutions, refresh rates, and multi-monitor state.
- Storage type, capacity, free space, TRIM capability, and documented health information.
- Game Mode availability and state through a supported implementation.
- HAGS support and state.
- Windowed game optimization availability.
- Hyper-V.
- Windows Hypervisor Platform.
- Virtual Machine Platform.
- VBS.
- Memory Integrity/HVCI.
- Relevant Windows services.
- WebView2 Evergreen Runtime.
- Installed BlueStacks products.
- Installed MSI App Player products.
- Installed emulator instances.
- Android instance type: Nougat 32, Nougat 64, Pie 64, Android 11, Android 13, or later known variants.
- Instance ABI settings where safely available.
- Candidate game and emulator executables.
- Missing components commonly removed by custom Windows builds.
- AC/battery state, active power scheme, and thermal/throttle signals where reliable.

Use typed capability states:

- `AVAILABLE`
- `UNAVAILABLE`
- `UNSUPPORTED`
- `UNKNOWN`
- `ERROR`

Each state must include a reason and evidence.

Build a typed `MachineCapabilityVector`; do not collapse it into a marketing label such as low/mid/high and do not branch on one hardware model name.

Implement these conservative resource guards with tested integer/rounding behavior:

    host_reserve_mb =
      max(3072, ceil_to_512(0.30 * total_ram_mb))

    safe_emulator_ram_cap_mb =
      floor_to_512(
        max(0,
          min(total_ram_mb - host_reserve_mb,
              available_ram_mb - 2048)
        )
      )

    detected_physical_core_budget =
      physical_cores when trustworthy,
      otherwise max(1, floor(logical_processors / 2))

    safe_emulator_cpu_cap =
      max(0,
        min(detected_physical_core_budget,
            logical_processors - 2)
      )

Rules:

- `ceil_to_512` and `floor_to_512` operate in 512 MB increments.
- Final allocation equals the documented profile target constrained by the safe cap.
- Never allocate every logical processor or nearly all host RAM.
- Re-check actual available memory, commit pressure, AC/battery, and thermal state immediately before apply.
- If the constrained result falls below a documented minimum, return `UNAVAILABLE`; use `SUPPORTED_DEGRADED` only when an existing instance is known to run and explain that it is below the preferred target.
- Large RAM/core counts are not permission to over-allocate; stop at measured workload need.
- iGPU/shared-memory systems are valid and must account for memory pressure.
- Vendor-specific rules appear only when vendor, driver, capability, graphics API, and exact render executable are known.
- Unknown GPU/driver receives generic Windows diagnostics and read-only vendor-specific rules.

Windows on ARM64 requires a separately built and tested native/dependency package. In version 1, detect it and return an explicit unsupported/read-only status instead of relying on x64 emulation and claiming support.

When a feature is missing:

- Do not crash.
- Do not invent a default.
- Do not blindly create registry keys.
- Do not silently reinstall components.
- Do not recreate removed Windows services.
- Mark dependent rules as unavailable.

On Windows 10, show a non-blocking Indonesian security notice explaining that regular Microsoft support ended on 14 October 2025. Do not prevent the application from running solely because the OS is Windows 10.

---

## 7. Tweak catalog and risk model

Every tweak must be classified as:

- `safe`
- `conditional`
- `experimental`
- `prohibited`

Every tweak must also have an evidence level:

- `vendor_documented`
- `repeatable_benchmark`
- `diagnostic_heuristic`
- `community_hypothesis`
- `rejected_myth`

Safe default features:

1. Read-only PC scan.
2. Startup application audit.
3. Background-process audit.
4. User-selected background process closing.
5. Visual-effects profiles: Windows Default, Balanced, and Best Performance.
6. Game Mode detection and supported configuration.
7. Per-executable high-performance GPU preference.
8. Display refresh-rate audit.
9. Power-plan inventory, snapshot/export, temporary activation, and restoration.
10. Storage space and TRIM/Optimize Drives status.
11. Safe temporary-file analysis with preview.
12. Pagefile diagnosis and recommendation to retain System Managed by default.
13. Virtualization/Hyper-V/VBS/Memory Integrity diagnostics.
14. Driver version diagnostics.
15. CPU/RAM/disk/thermal bottleneck diagnostics.
16. Network ping, jitter, packet-loss, adapter speed, Wi-Fi, and background-traffic diagnostics.
17. Restore Center.
18. Dry Run mode.
19. Searchable Activity Log.

Never silently close:

- Browsers.
- Communication software.
- Recording software.
- Accessibility software.
- Antivirus software.
- Applications containing unsaved work.

Require explicit user selection and warn about unsaved work.

---

## 8. Conditional and experimental features

Implement behind clear warnings and benchmark requirements:

- HAGS A/B testing.
- Windows windowed-game optimization.
- Per-game VSync.
- VRR/FreeSync/G-Sync recommendations.
- Per-game FPS caps.
- AMD/NVIDIA low-latency features only when GPU, driver, game, and graphics API support them.
- BlueStacks/MSI renderer comparison.
- Emulator resolution comparison.
- Emulator DPI comparison.
- `ABOVE_NORMAL` process priority.
- CPU affinity only for troubleshooting.
- Hyper-V/VBS/Memory Integrity changes only after individual security warnings.
- NIC interrupt moderation and advanced adapter properties only with exact snapshots.
- SysMain and indexing changes only when diagnostics show a relevant bottleneck.
- Background capture changes only when the feature is active.

A security-reducing change must never be included in:

- Safe Daily.
- Gaming Balanced.
- Default recommendation.

---

## 9. Explicitly prohibited tweaks

Do not implement, recommend, import, or execute:

- Realtime process priority.
- Blanket High priority.
- Disabling pagefile.
- A fixed “magic” pagefile size.
- HPET tweak packs.
- `useplatformclock`.
- `useplatformtick`.
- `tscsyncpolicy`.
- `disabledynamictick`.
- Permanent global timer-resolution manipulation.
- `SystemResponsiveness=0`.
- `GPU Priority=8`.
- `SFIO Priority=High`.
- Global `TcpAckFrequency`.
- Global `TCPNoDelay`.
- Global Nagle disabling.
- Global TCP autotuning hacks.
- Disabling Defender.
- Disabling Firewall.
- Disabling UAC.
- Disabling Windows Update.
- Disabling exploit protection.
- Disabling security mitigations.
- Mass Windows-service disabling.
- Mass UWP removal.
- Continuous standby-list purging.
- Continuous working-set trimming.
- Deleting Prefetch on every boot.
- Deleting shader caches on every boot.
- Forced universal CPU affinity.
- USB polling-rate overclock.
- Disabling thermal protection.
- Unsigned or unofficial driver installation.
- APK modification.
- ADB gameplay automation.
- Game-process memory reading or writing.
- DLL injection.
- Packet editing.
- Anti-cheat bypass.
- Emulator-detection bypass.
- Aim, recoil, fire-button, or gameplay macros.
- Editing Free Fire client data, INI, package, or anti-cheat.

Create tests proving prohibited rule IDs, operation classes, registry targets, and command patterns are rejected by the schema and policy layer.

---

## 9A. Windows Registry provider and evidence catalog

Treat Windows Registry as a typed state provider, not as a generic tweak executor. Do not ship a folder of `.reg` files and do not expose a generic Registry editor.

Implement these support classes:

- `OFFICIAL_CONTRACT`: Microsoft documents the key/value/type and semantics.
- `OFFICIAL_POLICY`: Microsoft documents it as policy; managed-device ownership must be detected.
- `OBSERVED_IMPLEMENTATION`: Windows currently stores a setting there, but raw Registry storage is not a stable public API.
- `TROUBLESHOOT_ONLY`: documented vendor workaround or diagnostic state, never a default optimization.
- `AUDIT_ONLY`: inventory/diagnostic target; never written by the optimizer.
- `PROHIBITED`: rejected by schema and policy.

Create a versioned, locally bundled Registry evidence catalog. Each entry must contain:

- Stable allowlist ID.
- Hive, canonical subkey, value-name rule, and Registry view.
- Exact allowed data type.
- Read/write/delete permissions.
- Support class and evidence level.
- Supported Windows/capability conditions.
- Allowed values/ranges or parser.
- Admin requirement.
- Whether the setting may be policy-managed.
- Restart/sign-out/process-restart requirement.
- Detection, preview, apply, verification, and exact rollback behavior.
- Security impact, limitations, source URL, and verification date.

The initial catalog must encode the following facts and boundaries:

| Purpose | Exact Registry target | Required behavior |
|---|---|---|
| Game Mode | `HKCU\Software\Microsoft\GameBar`, `AutoGameModeEnabled`, `REG_DWORD` | Official Windows setting; allow only `0` or `1`; current-user scope; exact snapshot |
| Game DVR policy | `HKLM\Software\Policies\Microsoft\Windows\GameDVR`, `AllowGameDVR`, `REG_DWORD` | Official policy; `0` not allowed and `1` allowed; audit by default; show policy ownership |
| Per-app GPU preference | `HKCU\Software\Microsoft\DirectX\UserGpuPreferences`, value name is a validated absolute executable path, `REG_SZ` | Observed implementation; preserve the whole prior string; support `GpuPreference=0;`, `1;`, and `2;`; prefer supported Windows UI/API when available |
| Run/RunOnce | `HKCU` and `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` or `RunOnce` | Audit only; startup order is not guaranteed; never blindly delete |
| Installed-app inventory | `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall` in relevant views | Audit only; use for BlueStacks/MSI discovery |
| App Paths | `HKLM` or `HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths` | Audit only; validate resolved executable and signature/publisher where available |
| Defender scan CPU | `HKLM\Software\Policies\Microsoft\Windows Defender\Scan`, `AvgCPULoadFactor`, `REG_DWORD` | Official policy representation; use the Defender `Set-MpPreference` provider rather than a raw write; range `0–100`, default 50, and `0` means no throttling; never disable protection or add exclusions |
| NIC advanced properties | `HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\####` | Storage is driver-specific; discover adapter/index dynamically; use `Get/Set-NetAdapterAdvancedProperty` and the driver’s valid Registry values; never hard-code `0000` |
| Pagefile | `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management`, `PagingFiles`, `REG_MULTI_SZ` | Audit only; recommend System Managed by default; do not infer a universal fixed size |
| Foreground scheduling | `HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl`, `Win32PrioritySeparation`, `REG_DWORD` | Audit only; do not ship a magic hex value; use process scheduling APIs for session-only priority |

Encode MMCSS correctly:

- Root: `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile`.
- `SystemResponsiveness` is a `REG_DWORD` percentage reserved for low-priority tasks. Values below 10 and above 100 are clamped to 20; 100 disables MMCSS. Therefore `SystemResponsiveness=0` is not a zero-percent-reserve optimization and must be prohibited.
- Under `Tasks\<task-name>`, `GPU Priority` and `SFIO Priority` are documented as unused.
- `Priority` is `1–8`; a task with `Scheduling Category=High` is treated as priority 2.
- `Clock Rate` periodic guarantees were removed starting with Windows 7.
- Do not apply MMCSS “gaming packs.” Make these values audit/evidence entries unless a future independently justified rule is added.

Implement these as conditional or troubleshooting-only, never as universal defaults:

| Feature | Registry target | Policy |
|---|---|---|
| HAGS | `HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers`, `HwSchMode`, `REG_DWORD`; observed `1` off, `2` on | Only when GPU, WDDM, driver, OS UI, and reboot support are confirmed; individual opt-in and A/B benchmark; restore absence if it was absent |
| Per-game compatibility flag | `HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`, value name is the full executable path, `REG_SZ` | `~ DISABLEDXMAXIMIZEDWINDOWEDMODE` is per-game troubleshooting; parse and preserve all unrelated tokens; never apply globally |
| MPO workaround | `HKLM\SOFTWARE\Microsoft\Windows\Dwm`, `OverlayTestMode=5`, `REG_DWORD` | Troubleshooting-only for matching display symptoms and vendor guidance; reboot; not an FPS boost |
| Transparency | `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`, `EnableTransparency`, `REG_DWORD` | User visual preference; do not claim meaningful game FPS |
| Menu delay | `HKCU\Control Panel\Desktop`, `MenuShowDelay`, `REG_SZ` | Perceived responsiveness only; validate an explicit bounded millisecond value |
| Minimize animation | `HKCU\Control Panel\Desktop\WindowMetrics`, `MinAnimate`, `REG_SZ` | User visual preference; exact snapshot and explain sign-out/Explorer restart behavior |
| Classic pointer acceleration | `HKCU\Control Panel\Mouse`, `MouseSpeed`, `MouseThreshold1`, `MouseThreshold2`, all `REG_SZ` | `0/0/0` disables classic Enhance Pointer Precision; it is not a latency reduction, and raw-input games may ignore it |

Explicitly prohibit writes or imports involving:

- Defender, Firewall, UAC, Windows Update, tamper protection, exploit protection, or automatic security exclusions.
- `SystemResponsiveness=0`, `GPU Priority=8`, `SFIO Priority=High`, and MMCSS magic packs.
- `TdrDelay`, `TdrDdiDelay`, `TdrLevel`, or other TDR testing/debug values as optimization.
- `FeatureSettingsOverride` and `FeatureSettingsOverrideMask` as performance tweaks.
- Global `TcpAckFrequency`, `TCPNoDelay`, `TcpDelAckTicks`, and `NetworkThrottlingIndex=FFFFFFFF`.
- `DisablePagingExecutive`, `LargeSystemCache`, `SystemPages`, pool-quota magic values, and pagefile disabling.
- Mass service `Start=4`, Prefetch/SysMain disable packs, raw PowerSchemes writes, persistent IFEO priority packs, aggressive `AutoEndTasks`/timeout packs, and unknown timer/IRQ/input-queue values.

BlueStacks and MSI App Player Registry rules:

- Use Uninstall/App Paths and discovered vendor keys only for read-only product/version/path discovery.
- Do not hard-code `HKLM\SOFTWARE\BlueStacks*`, MSI paths, instance names, drive letters, or schema as a cross-version contract.
- Validate the actual running render executable. BlueStacks/MSI commonly use `HD-Player.exe`, but discovery must prove it instead of assuming it.
- Apply Windows per-app GPU preference to the validated render executable, not a launcher or shortcut.
- CPU cores, RAM, renderer, resolution, DPI, and FPS are instance configuration values handled by schema-aware emulator adapters; they are not universal Windows Registry tweaks.
- A Registry key cannot guarantee Free Fire ARM32/ARM64 compatibility, FPS, sensitivity, or anti-ban behavior.

Implement a typed `RegistryProvider` with operations equivalent to:

```yaml
operation: registry_set
hive: HKCU
subkey: Software\Microsoft\GameBar
value_name: AutoGameModeEnabled
registry_view: native
value_type: REG_DWORD
data: 1
allowlist_id: windows.game_mode.current_user
support_class: OFFICIAL_CONTRACT
requires_admin: false
missing_value_policy: create_value_only
verification:
  operator: typed_equals
  expected_type: REG_DWORD
  expected_data: 1
rollback: restore_exact_snapshot
```

Schema and provider requirements:

- Hive is an enum initially limited to `HKCU` and `HKLM`.
- Store `subkey` and `value_name` separately. Canonicalize without resolving untrusted aliases or accepting wildcards.
- `registry_view` is `native`, `32`, or `64`. On Python, use `winreg.KEY_WOW64_32KEY` and `winreg.KEY_WOW64_64KEY`; never encode a view by inserting literal `WOW6432Node`.
- Support only explicit `REG_DWORD`, `REG_QWORD`, `REG_SZ`, `REG_EXPAND_SZ`, `REG_MULTI_SZ`, and `REG_BINARY`.
- Validate data losslessly by type. Do not implicitly convert strings to numbers, expand `REG_EXPAND_SZ`, flatten `REG_MULTI_SZ`, or decode arbitrary binary.
- Use the minimum Registry access mask required for each operation.
- Distinguish key missing, value missing, value present with empty data, access denied, unsupported view, and policy-managed state.
- Reject remote Registry, hive load/unload, Registry links, ACL/owner mutation, recursive key deletion, wildcard targets, embedded NUL, oversize value data, unknown type, and path outside the exact allowlist.
- The frontend must never receive a generic Registry API.
- The elevated helper must revalidate the operation, allowlist ID, type, data bounds, current state, view, nonce, and transaction identity after elevation.

Every Registry snapshot must be absence-aware and contain:

```json
{
  "hive": "HKCU",
  "subkey": "Software\\Microsoft\\GameBar",
  "value_name": "AutoGameModeEnabled",
  "registry_view": "native",
  "key_existed": true,
  "value_existed": false,
  "value_type": null,
  "raw_data": null,
  "policy_managed": false,
  "security_descriptor_hash": "read-only-diagnostic-if-available"
}
```

Rollback requirements:

- If the value was absent, delete only the value created by this transaction.
- Delete a newly created key only when the transaction created it, it remains empty, and the allowlist permits cleanup.
- Preserve `REG_EXPAND_SZ`, `REG_MULTI_SZ`, and `REG_BINARY` losslessly.
- Before rollback, compare current state to the state written by the transaction. If another actor changed it, stop and create a recovery conflict instead of overwriting.
- Do not use a `.reg` export as the only snapshot.

`.reg` files may be parsed only by an offline analyzer. The analyzer may show targets, types, decoded data, risk, support class, evidence status, conflicts, and a proposed typed operation plan. It must never call `regedit /s`, `reg import`, `reg.exe add`, PowerShell command strings, or execute the imported file. Unknown/prohibited targets remain rejected even after user confirmation.

---

## 10. Manifest-driven rule engine

Implement a versioned data-driven manifest format.

Every rule must contain:

- Stable rule ID.
- Manifest schema version.
- Rule revision.
- Indonesian title and description.
- Category.
- Risk level.
- Evidence level.
- User/admin scope.
- Persistent or session-only behavior.
- Supported capabilities.
- Documented minimum resources and requested target where relevant.
- Safe-cap resolver identifier where relevant.
- Preconditions.
- Current-state detection.
- Typed apply operations.
- Verification.
- Exact rollback behavior.
- Conflicts.
- Restart/sign-out requirement.
- Security impact.
- Official evidence URLs.
- Known limitations.
- Benchmark recommendation.
- Signature metadata.

Supported internal operation types may include:

- Strict registry read/set/delete.
- Supported Windows-setting adapters.
- Power configuration query/change/restore.
- Per-process priority changes.
- Process close requests with confirmation.
- Supported display changes.
- Safe file/config changes through schema-aware adapters.
- Emulator configuration updates.
- Safe temporary-file cleanup.
- Documented Optimize Drives invocation.
- Read-only diagnostics.

Never execute an arbitrary command supplied by a manifest.

External rule packages must be cryptographically signed.

Reject:

- Invalid signatures.
- Unsigned external packages.
- Expired packages.
- Incompatible schema versions.
- Downgrade attempts.
- Unknown operation types.
- Prohibited operations.
- Path traversal.
- Targets outside the allowlist.

Built-in manifests must remain available offline.

Generic rules must not contain a required hardware SKU list. Vendor rules may require a detected vendor, driver, API, and capability, but they must not use one CPU/GPU model as the universal default. Emulator manifests store documented minimums/requested targets; the preview engine resolves final core/RAM values from the latest `MachineCapabilityVector`.

---

## 11. Transaction and rollback engine

Implement durable states equivalent to:

- `PLANNED`
- `SNAPSHOTTED`
- `APPLYING`
- `APPLIED`
- `VERIFIED`
- `KEPT`
- `ROLLING_BACK`
- `ROLLED_BACK`
- `RECOVERY_REQUIRED`
- `FAILED_SAFE`

Before each mutation, save:

- Previous value in a lossless typed representation.
- For Registry operations: hive, subkey, value name, explicit Registry view, `key_existed`, `value_existed`, exact data type, raw data, policy-managed state, and the state the transaction intends to write.
- Previous file content or validated patch representation.
- File hash.
- Current power-plan ID.
- Rule ID and revision.
- Transaction ID.
- Timestamp.
- User and machine scope.
- Restart requirement.
- Verification instructions.

Requirements:

- Use an append-safe transaction journal.
- Rollback must be idempotent.
- Detect incomplete transactions at startup.
- Open Recovery Center before allowing new changes when recovery is pending.
- Detect state conflicts when the user or another application changed a target after apply.
- If a Registry value was absent before apply, rollback must remove the transaction-created value instead of inventing a default.
- Remove a transaction-created Registry key only if it remains empty, was created by the transaction, and its allowlist explicitly permits cleanup.
- Preserve `REG_EXPAND_SZ`, `REG_MULTI_SZ`, and `REG_BINARY` losslessly; a `.reg` export is not a sufficient transaction snapshot.
- Never use System Restore as the only rollback method.
- Offer a restore point for major grouped changes where supported.

---

## 12. Least-privilege architecture

The main application process must:

- Use an `asInvoker` application manifest.
- Run without administrator rights.
- Perform read-only scans and user-scope changes normally.

Implement a separate elevated helper:

- Launch through the standard Windows `runas` mechanism only for a confirmed privileged transaction.
- Use a one-time nonce.
- Use ACL-restricted storage or secure local IPC.
- Accept only a validated typed operation plan.
- Revalidate every operation after elevation.
- Allowlist registry hives, registry paths, file targets, and operation types.
- Open Registry keys using the minimum access mask and an explicit native/32/64-bit view.
- Reject remote Registry access, hive load/unload, Registry links, ACL/owner changes, recursive deletion, wildcards, embedded NUL, implicit type coercion, and `.reg` execution.
- Revalidate Registry allowlist ID, support class, path, view, data type, bounds, current state, transaction ID, and nonce after elevation.
- Reject arbitrary command strings.
- Reject shell metacharacters.
- Reject path traversal and reparse-point attacks.
- Never load executable code from downloaded manifests.
- Produce a validated result record.
- Exit after one transaction.

Do not install a permanent Windows service in the initial version.

Add security tests for:

- Malformed plans.
- Unsupported registry targets.
- Path traversal.
- Symlink/reparse-point attacks.
- Replay nonce.
- Operation-plan tampering.
- Arbitrary-command attempts.
- Registry-view confusion and literal `WOW6432Node` path attempts.
- Registry ACL/owner mutation, remote hive, recursive deletion, and direct `.reg` execution attempts.

---

## 13. Built-in profiles

### Safe Daily

- Startup audit.
- Background-activity recommendations.
- Balanced visual effects.
- Storage health.
- Pagefile diagnosis.
- Driver and thermal report.
- No security reduction.
- No timer, BCDEdit, TCP, or mass-service hacks.

### Gaming Balanced

- Safe Daily items relevant to gaming.
- Game Mode.
- High-performance GPU preference.
- Refresh-rate check.
- Session-only power mode.
- User-selected background-process closing.
- Automatic restoration after the game process tree exits.

### Competitive Experimental

- Gaming Balanced baseline.
- Optional HAGS.
- Windowed-game optimization.
- VSync/VRR/FPS-cap experiments.
- Optional Above Normal process priority.
- Mandatory benchmark.
- Easy rollback.
- No security-feature changes by default.

### Free Fire v7a / Nougat 32

- Detect a genuine Nougat 32-bit instance.
- Detect ARM32/armeabi-v7a context where safely available.
- Use 4 CPU cores as the documented requested target, constrained by `safe_emulator_cpu_cap`.
- Use 3072–4096 MB as the requested RAM target, constrained by `safe_emulator_ram_cap_mb`.
- Display requested, safe-cap, and final values separately.
- Use dynamic host headroom; never hard-code a 6–8 GB reserve for every machine.
- If safe values cannot meet the preferred target, reduce resolution/FPS or return degraded/unavailable; never label the fallback “optimal”.
- Start at 1280×720.
- Offer DPI 160/240 comparison.
- Start with stable 60 FPS.
- Test higher FPS only when exposed and stable.
- Compare supported renderers.
- Set the emulator render executable to the best applicable adapter. iGPU-only systems remain valid.
- Never edit Free Fire APK, client, memory, packets, data, INI, package, or anti-cheat.

### Free Fire 64 / Pie 64

- Detect a genuine Pie 64-bit or known compatible modern instance.
- Detect ARM64/arm64-v8a context where safely available.
- Use 4 CPU cores and 4096 MB RAM as requested targets, each constrained by the resource guards.
- Offer 1280×720 competitive mode.
- Offer 1920×1080 quality mode if stable.
- Provide a guided 90 FPS configuration only when supported.
- Gate 90 FPS on game/instance option, display mode, CPU/GPU headroom, temperature, and stable frame time—not on the GPU name.
- Verify GPU assignment.
- Verify monitor refresh rate.
- Compare renderers rather than assuming one is universally best.

### Free Fire MAX

- Performance requested target: 4 CPU cores and 4096 MB RAM, constrained by the safe caps.
- Guided 120 FPS mode only when supported and stable.
- Optional quality requested target: 4 CPU cores and 6144 MB RAM.
- Offer 6 GB only when host memory pressure remains safe.
- Reduce quality/FPS or mark unavailable before consuming host reserve.

### Custom Profile

- Users may compose profiles only from validated catalog rules.
- Show conflicts.
- Show persistent and temporary changes.
- Show total risk.
- Do not allow arbitrary scripts.

---

## 14. BlueStacks and MSI App Player

Treat BlueStacks and MSI App Player as related but separate products.

Implement:

- Product discovery.
- Version discovery.
- Installation-path discovery without assuming drive C.
- Instance discovery.
- Android-version discovery.
- ABI-setting discovery where safe.
- Safe config-path discovery.
- Config backup.
- Schema-aware config update.
- Atomic file writes.
- Hash verification.
- Product-specific process-tree detection.
- Version-specific feature flags.
- Unsupported-version diagnostics.
- Read-only mode when the config format is unknown.

Do not assume:

- Every version uses the same executable.
- Every version uses the same folder.
- Every version uses the same key.
- Every version supports the same renderer.
- Every version requires Hyper-V to be disabled.

Detect the installed version and current host virtualization state before recommending changes.

---

## 15. Game session controller

Implement:

1. User selects or discovers a game executable.
2. The application previews temporary changes.
3. The application creates a snapshot.
4. Session-only settings are applied.
5. The game/emulator is launched or attached.
6. The complete process tree is monitored.
7. Previous settings are restored after the process tree exits.
8. If the application crashes, recovery occurs on next startup.
9. If Windows reboots unexpectedly, Recovery Center is shown immediately.

Never inject code into a game.

Never inspect or modify game memory.

---

## 16. Benchmark engine

Create a benchmark abstraction with:

- Optional PresentMon integration.
- Safe resource-sampler fallback.
- Network diagnostics.
- Import of existing PresentMon CSV files.
- No silent third-party downloads.
- Correct third-party license handling.
- Indonesian guided benchmark wizard.

Capture where data is reliable:

- Median FPS.
- 1% low FPS.
- 0.1% low FPS.
- Median frame time.
- p95 frame time.
- p99 frame time.
- Stutter count with a documented formula.
- CPU utilization.
- CPU frequency.
- Process working set.
- System commit usage.
- GPU utilization.
- Disk active time.
- Temperature.
- Ping.
- Jitter.
- Packet loss.

Benchmark procedure:

1. Require warm-up.
2. Ask the user to use the same map, scene, route, resolution, renderer, and graphics settings.
3. Recommend 3–5 baseline runs.
4. Change one logical group of variables.
5. Recommend 3–5 comparison runs.
6. Compare medians and variance.
7. Mark invalid runs.
8. Do not declare a winner when the difference is inside noise.

Result states:

- `IMPROVED`
- `REGRESSED`
- `INCONCLUSIVE`
- `INVALID`

Account for limitations in OpenGL/Vulkan instrumentation and HAGS-related metrics. Never fabricate missing metrics.

---

## 17. Persistence

Use SQLite with migrations.

Include tables or equivalent models for:

- schema_migrations
- machines
- capability_scans
- capabilities
- games
- game_executables
- emulator_products
- emulator_instances
- profiles
- profile_rules
- tweak_rules
- transactions
- transaction_operations
- snapshots
- game_sessions
- benchmark_sessions
- benchmark_runs
- benchmark_metrics
- recommendations
- evidence_sources
- activity_events
- application_settings

Store per-user application state in an appropriate LocalAppData directory.

Use ProgramData only for installer/helper/shared files that require it, with appropriate ACLs.

Implement:

- Profile export/import.
- Diagnostic report export.
- Transaction report export.

Exported packages must never contain arbitrary executable code.

---

## 18. JavaScript-to-Python API

Create narrow typed bridge methods such as:

- `scan_system()`
- `get_scan_result(scan_id)`
- `list_recommendations(scan_id)`
- `list_profiles()`
- `preview_transaction(rule_ids, profile_id)`
- `apply_transaction(transaction_id)`
- `get_transaction_status(transaction_id)`
- `rollback_transaction(transaction_id)`
- `list_recovery_items()`
- `start_game_session(profile_id, executable_id)`
- `stop_game_session(session_id)`
- `discover_emulators()`
- `get_emulator_instances(product_id)`
- `preview_emulator_profile(instance_id, profile_id)`
- `start_benchmark(config)`
- `cancel_benchmark(benchmark_id)`
- `get_benchmark_status(benchmark_id)`
- `compare_benchmarks(ids)`
- `list_activity_events(filter)`
- `export_diagnostic_report(options)`

Long-running calls must not block the UI.

Return consistent typed objects:

- success
- data
- error code
- localized user message
- developer detail
- retryable flag
- correlation ID

Never expose to JavaScript:

- Generic filesystem access.
- Generic registry access.
- Arbitrary subprocess execution.
- Generic shell execution.
- Raw elevated-helper control.

---

## 19. UI and visual language

Create a restrained Windows desktop utility, not a landing page, sci-fi HUD, or AI-generated gaming concept. Use Fluent/Windows principles—consistency, simplicity, clarity, predictable navigation, semantic design tokens, and progressive disclosure—without importing a heavy UI framework.

### 19.1 Non-negotiable anti-AI-slop rules

Do not create:

- A giant hero, marketing slogan, or 40–72 px headings.
- Purple/blue gradients, gradient text, mass glassmorphism, or backdrop blur across the app.
- Neon glow, floating blobs/orbs, particles, cyber grids, scanlines, cursor trails, 3D objects, or animated backgrounds.
- Large rounded cards for every paragraph, cards inside cards, or 16–32 px radii.
- Generic four-column KPI cards, fake circular optimization scores, speedometers, decorative charts, or fabricated boost percentages.
- Pill buttons/tags everywhere, shadows on every surface, or gradient borders.
- Robot, chip, brain, rocket, lightning, sparkle, magic-wand, or “AI” illustrations.
- Emoji as control icons.
- Icons from mixed families or an icon beside every label.
- Staggered page entrances, bounce, parallax, infinite pulse, or decorative looping animation.
- Generic copy such as “Unleash ultimate performance”, “Your PC is flying”, “AI-powered optimization”, “zero delay”, or “BOOST NOW”.

The gaming character must come from restrained blue accents, session state, measured benchmark data, and compact technical information—not visual effects.

### 19.2 Exact design tokens

Create semantic CSS tokens and prohibit random hex values in component CSS:

    --color-bg-canvas: #0B1018;
    --color-bg-sidebar: #0F1722;
    --color-surface-1: #151E2B;
    --color-surface-2: #1B2635;
    --color-border: #2B3A4D;
    --color-text-primary: #E7EDF6;
    --color-text-secondary: #9AA9BC;
    --color-accent: #2F81F7;
    --color-accent-hover: #58A6FF;
    --color-accent-muted: #173A63;
    --color-success: #3FB950;
    --color-warning: #D29922;
    --color-danger: #F85149;

Rules:

- No gradients.
- Blue and gray/navy dominate.
- Success, warning, and danger colors communicate status only and always include text or another non-color cue.
- Meet WCAG 2.2 AA text and non-text contrast.
- Use a 2 px visible focus ring with at least 3:1 contrast against adjacent colors.
- Support `forced-colors`.
- A light theme is not required for v1; do not ship a half-finished one.

### 19.3 Typography, spacing, shape, and elevation

Use only:

    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;

Type ramp:

- Caption/metadata: 12/16 px, regular.
- Body/control: 14/20 px, regular.
- Emphasis: 14/20 px, semibold.
- Section heading: 18/24 px, semibold.
- Page title: 24/32 px, semibold.

Use sentence case and left alignment. Use system monospace only for paths, IDs, hashes, and technical logs.

Use a 4 px base grid and spacing values 8, 12, 16, 20, 24, and 32 px. Controls are 32 or 36 px high with at least a 32×32 px interaction target. Use radii of 4 px for small controls, 6 px for buttons, and 8 px for panels/dialogs. Use 1 px borders as the primary separator. Use shadows only for dialogs, menus, tooltips, and true overlays.

### 19.4 Icon and brand-asset policy

- Use only a vendored local subset of **Microsoft Fluent System Icons**, Regular style, 20/24 px, under its MIT license.
- Use SVG with `currentColor`; decorative icons use `aria-hidden="true"`.
- Icon-only controls require an `aria-label` and visible tooltip. Unfamiliar actions require text labels.
- Record the upstream URL, license, version/commit, selected files, and hashes in `ASSET_PROVENANCE.md` and preserve notices in `THIRD_PARTY_NOTICES.md`.
- Do not use Font Awesome, emoji, icon fonts, search-engine images, or a second icon family.
- **Do not generate any logo, application icon, illustration, or new UI icon with Codex, an image model, SVG generation, or procedural art.**
- Until the user supplies a human-created and approved brand asset, show the text wordmark `IPAN OPTIMIZER` and keep the default development executable icon. Document the missing final brand asset; do not invent one.

### 19.5 Desktop information architecture

Support `1024×700`, `1280×800`, and `1440×900`, plus Windows scaling 100%, 125%, 150%, and 200%.

- Title bar: 44–48 px.
- Left navigation: 224–232 px; compact 64–72 px at narrower widths.
- Content padding: 24 px, reducible to 16 px near minimum width.
- Show at most six primary destinations:
  1. Dashboard
  2. Scan & recommendations
  3. Profiles & games
  4. Emulator
  5. Benchmark
  6. Restore
- Group Startup & Background, Storage & Memory, Network, and Activity under `Tools`.
- Place Settings and About & Evidence in the navigation footer.
- Keep hierarchy at two levels. Use a breadcrumb only for deeper detail.
- Below 960 px, use compact/overlay navigation. Tables may scroll inside their own container; the entire page must not horizontally overflow.

### 19.6 Component rules

Choose components by information type:

- Recommendation: compact list row with status, title, one-line reason, risk badge, and disclosure chevron.
- Current versus proposed: two-column diff table.
- Processes, startup items, and logs: accessible data table with sorting, filtering, sticky header, and pagination or virtualization.
- Risky actions: inline warning followed by a confirmation dialog that names the exact target, persistent/session scope, restart requirement, and rollback.
- Known progress: determinate progress. Use a spinner only after one second when progress cannot be determined.
- Evidence: expandable drawer with source and verification date.

Each tweak detail must show:

- Current state and proposed state.
- Applicability status and reason.
- Safe/Conditional/Experimental.
- Expected effect without fabricated numbers.
- Known limitations, risk, and security impact.
- Evidence level, source, and verification date.
- Persistent/session-only scope and restart/sign-out requirement.
- Preview diff, Apply, Verify, and Rollback where applicable.

Use progressive disclosure. Do not turn 14 destinations or every fact into 14 large cards.

### 19.7 Dashboard and content

Never create an overall health/optimization score.

Dashboard facts:

- Snapshot/recovery status.
- CPU, RAM, and storage pressure with timestamps.
- GPU assignment and refresh-rate mismatch.
- Startup items worth reviewing.
- Emulator compatibility.
- Verified recommendations grouped by risk.
- Primary action text: `Pindai PC` or `Tinjau rekomendasi`, never `Boost`.

Missing data must render as `Memuat`, `Tidak tersedia`, `Tidak diketahui`, or `Belum diukur`, never zero.

All user-facing copy is concise Indonesian:

- `3 rekomendasi tersedia`
- `Perubahan belum diterapkan`
- `Tidak ada perubahan bermakna`
- `Pratinjau perubahan`
- `Terapkan`
- `Pulihkan`

Add a persistent, clearly visible Dry Run indicator.

### 19.8 Motion, responsiveness, and implementation

- Use 120–180 ms ease-out transitions only for hover, selection, expand/collapse, and overlays.
- Respect `prefers-reduced-motion: reduce`.
- No loop animation except a real active operation.
- Show the truthful operation sequence: snapshot → apply → verify → success or rollback.
- Use toast only for brief outcomes; actionable errors remain inline.
- Render only the active route. Lazy-load large evidence/log data.
- Use vanilla ES modules, event delegation, `DocumentFragment`, `requestAnimationFrame`, and pagination/virtualization.
- Stop or slow sampling when the window/page is hidden or minimized.
- Use small SVG/CSS/Canvas charts; do not add a chart framework.
- Keep WMI, file, benchmark, and hash work off the UI thread with cancellation.

### 19.9 Required visual QA

For every major page:

- Capture real running-app screenshots at the required viewport/scaling matrix.
- Check keyboard-only focus order and visible focus.
- Run contrast checks and test reduced motion/forced colors.
- Check overflow, truncation, table behavior, and Indonesian copy.
- Audit card count, radii, shadows, gradients, icons, motion, asset source, and performance budget.
- Compare screenshot to `DESIGN_SYSTEM.md`.
- Do not accept a generated mockup as proof; screenshots must come from the implemented application.

Use confirmation dialogs proportional to risk:

- Safe items may be grouped.
- Conditional items require a clear explanation.
- Experimental items require benchmark guidance.
- Security-related changes require individual confirmation.

### 19.10 Mandatory functional-control contract

Every visible interactive control must work. Do not create decorative buttons, placeholder actions, dead controls, `href="#"`, `javascript:` links, empty callbacks, “coming soon” controls, or buttons that only display a fake success toast.

Every button, menu item, toggle, filter, dialog action, table row action, keyboard shortcut, and clickable disclosure must have:

- A stable `control_id`.
- A specific Indonesian label or accessible name.
- A real frontend handler.
- A typed bridge method when backend work is required.
- A real backend operation or an explicitly read-only local UI operation.
- Preconditions and capability checks.
- Immediate interaction feedback within 100 ms.
- Loading, success, empty, unavailable, validation-error, backend-error, disabled, and retry behavior where applicable.
- Double-submit protection for non-idempotent operations.
- Cancellation only at a backend-defined safe boundary.
- Verification after the operation; a toast alone never proves success.
- Rollback/recovery behavior for reversible mutations.
- Keyboard activation, visible focus, and focus restoration.
- Automated test IDs and evidence in `docs/CONTROL_MATRIX.md`.

Create `docs/CONTROL_MATRIX.md` with at least these columns:

| `control_id` | Route/component | Indonesian label | User intent | Handler | Bridge method | Backend operation | Risk/permission | States | Verification | Test IDs |
|---|---|---|---|---|---|---|---|---|---|---|

The minimum functional inventory includes:

1. Every primary and secondary navigation destination.
2. Dashboard `Pindai PC` and `Tinjau rekomendasi`.
3. Recommendation search, filter, sort, expand, select, and clear-selection.
4. `Pratinjau perubahan`, `Terapkan`, `Batalkan`, and `Verifikasi`.
5. Restore item detail, `Pulihkan`, conflict review, retry, and export.
6. Add/select executable, start session, stop session, and recovery.
7. Emulator discovery, instance selection, profile preview, apply, verify, and restore.
8. Benchmark start, cancel, compare, delete local result with confirmation, and export.
9. Data-table search, filter, sort, pagination, selection, and row actions.
10. Dialog primary/secondary/close/Escape behavior.
11. Dry Run and other Settings controls.
12. Evidence links opened only after explicit user action through the allowed system-browser path.

Implementation rules:

- Prefer semantic native controls such as `<button type="button">`, `<button type="submit">` only inside a real form, `<a href="real-url">`, input, select, and details/summary where appropriate.
- Do not use clickable `<div>` or `<span>` when a native control exists.
- Disable the initiating control while the same non-idempotent request is active.
- Use an operation ID/idempotency guard so rapid double-click cannot create duplicate transactions.
- Keep UI and backend state synchronized after route changes, cancellation, errors, and recovery.
- Sanitize every string crossing the bridge and render it with safe text APIs.
- Capture and surface bridge exceptions and rejected Promises; no silent console-only failure.
- A disabled control must have an adjacent explanation; do not rely only on tooltip or color.
- Use optimistic UI only for local, reversible view state. System-state actions update the UI only after verified backend status.

Testing and release gate:

- Build a fake bridge with deterministic success, empty, unavailable, validation-error, backend-error, delayed, cancellation, and conflict responses.
- Run UI unit tests for every handler and state reducer.
- Run bridge contract tests proving argument and response schemas.
- Run E2E tests for every control in the matrix, including mouse, keyboard, rapid double-click, failure, retry, route change, and recovery.
- Run integration tests for `Pindai`, transaction preview/apply/verify/cancel/rollback, start/stop game session, emulator profile workflow, benchmark, settings persistence, and export.
- Fail CI for missing/duplicate `control_id`, missing test mapping, missing handler, missing bridge implementation, `href="#"`, inline placeholder handler, unhandled Promise rejection, console error, or false-success state.
- UI completion requires both real running-app screenshots and passing functional tests. A visual mockup cannot satisfy this requirement.

---

## 20. Security and privacy

The application must be local-first and offline-capable.

Do not send:

- Machine inventory.
- Game lists.
- Emulator data.
- Logs.
- Benchmarks.
- User identifiers.

Do not implement telemetry in the initial version.

Threat-model:

- Malicious manifest.
- Manifest downgrade.
- IPC tampering.
- Privilege escalation.
- Path traversal.
- Reparse-point/symlink attack.
- Registry path injection.
- TOCTOU between preview and apply.
- Corrupt emulator config.
- Transaction-journal corruption.
- Replay attacks.
- Log injection.
- Untrusted profile import.
- Dependency compromise.
- WebView navigation to untrusted origins.
- XSS through hardware names, paths, logs, or imported data.

Controls:

- Content Security Policy.
- HTML escaping.
- Strict input validation.
- Manifest signatures.
- Typed operation allowlist.
- ACL-restricted files.
- Atomic writes.
- Hash verification.
- One-time nonces.
- Dependency pinning.
- Code-signing support.

Prevent arbitrary external navigation in the WebView. Open only allowlisted evidence links through the default system browser after explicit user action.

---

## 21. WebView2

Use WebView2 Evergreen as the supported Windows renderer.

At startup and installation:

- Detect WebView2 Runtime.
- If missing, show a clear Indonesian diagnostic.
- The installer may offer the official Evergreen bootstrapper or offline installer.
- Require user consent.
- Verify the installer’s digital signature.
- Do not silently download or install it.
- Do not rely on legacy mshtml as the production fallback.

---

## 22. Packaging and release

Provide:

- Exact pinned dependency files.
- Reproducible PyInstaller `onedir` configuration.
- Main application manifest using `asInvoker`.
- Separate helper manifest requiring administrator privileges.
- Inno Setup installer.
- Clean uninstall behavior.
- Upgrade-safe database migrations.
- WebView2 prerequisite handling.
- Code-signing placeholders and documentation.
- SHA-256 generation for release files.
- Changelog.
- Release checklist.
- `THIRD_PARTY_NOTICES.md`.

Never embed developer credentials, API keys, signing secrets, or private paths.

---

## 23. Testing requirements

Automated tests must never mutate the real host.

Create fake backends and fixtures for:

- Windows 10 22H2.
- Windows 11 24H2.
- Windows 11 25H2.
- 2 logical cores, 4 GB RAM, HDD, integrated GPU: scan-only/degraded behavior.
- 4 cores, 8 GB RAM, integrated GPU, SATA SSD.
- 4 cores/8 threads, 8–16 GB RAM, discrete GPU.
- 6 cores/12 threads, 16 GB RAM, discrete GPU.
- 8+ cores, 32+ GB RAM, multi-GPU.
- Laptop on AC power.
- Laptop on battery with thermal/power pressure.
- HDD, SATA SSD, and NVMe variants.
- Non-admin user.
- Hyper-V enabled.
- Hyper-V disabled.
- HAGS supported.
- HAGS unsupported.
- WebView2 missing.
- WMI unavailable.
- Relevant Windows service missing.
- AMD GPU.
- NVIDIA GPU.
- Intel GPU.
- Single monitor.
- Multiple monitors.
- BlueStacks current layout.
- BlueStacks 5.21.x layout.
- Legacy BlueStacks layout.
- MSI App Player current layout.
- Legacy MSI App Player layout.
- Nougat 32 instance.
- Pie 64 instance.
- Unknown emulator config format.
- Custom Windows with removed components.
- Windows on ARM64 negative/read-only behavior until a separately tested native build exists.

Test:

- Capability detection.
- Rule applicability.
- Manifest schema.
- Manifest signature rejection.
- Manifest downgrade rejection.
- Prohibited tweak rejection.
- Snapshot/apply/verify/rollback.
- Rollback idempotency.
- Crash recovery.
- Reboot recovery journal.
- Registry type preservation.
- Registry round-trip for every supported type.
- Registry missing-key, missing-value, empty-value, access-denied, policy-managed, and unsupported-view states.
- Native/32/64-bit Registry-view isolation using `KEY_WOW64_32KEY` and `KEY_WOW64_64KEY`.
- Registry path canonicalization, allowlist, embedded-NUL, size-bound, remote-hive, recursive-delete, link, and ACL/owner-mutation rejection.
- Registry rollback when a value/key was absent before apply.
- Registry rollback conflict when another actor changes the state after apply.
- `.reg` analyzer parsing into a draft plan while direct import/execution remains impossible.
- Atomic config writes.
- Power-plan restoration.
- Game-session restoration.
- Invalid paths.
- Path traversal.
- Reparse points.
- Replay nonces.
- API validation.
- Automated inventory of every button, action link, menu item, toggle, disclosure, dialog action, keyboard action, and table row action.
- `docs/CONTROL_MATRIX.md` completeness and traceability.
- Frontend handler and state-reducer unit tests.
- JavaScript-to-Python bridge request/response contract tests for every UI-called method.
- Fake-bridge E2E tests covering success, empty, unavailable, validation error, backend error, delayed response, cancellation, conflict, retry, and route changes.
- Rapid double-click and idempotency tests for every non-idempotent action.
- Keyboard activation tests for Tab, Shift+Tab, Enter, Space, Escape, dialog focus trap, and focus return.
- Static checks rejecting `href="#"`, `javascript:`, clickable non-semantic elements without keyboard equivalence, placeholder/empty handler, duplicate `control_id`, and missing test mapping.
- Integration tests for Scan, recommendation selection, transaction preview/apply/verify/cancel/rollback, Restore, game-session start/stop, emulator-profile workflow, benchmark start/cancel/compare/export, and Settings persistence.
- Console-error, unhandled-Promise-rejection, and uncaught-bridge-exception release gates.
- Frontend state rendering.
- Keyboard navigation.
- Focus-order and focus-visible regression.
- WCAG contrast/token checks.
- Reduced-motion and forced-colors behavior.
- 1024×700, 1280×800, and 1440×900 layout snapshots at relevant DPI scaling.
- Frontend asset-size budget.
- Startup, navigation feedback, long-task, idle CPU, memory, network-request, and timer budgets.
- Asset provenance and license allowlist.
- Rejection of generated/unapproved icons, emoji controls, mixed icon families, gradients, mass glassmorphism, fake score/gauge, and decorative loops.
- UI smoke tests.
- PyInstaller smoke launch.

Create a separate manual QA matrix for testing real Windows systems, displays, games, BlueStacks, MSI App Player, and Free Fire.

---

## 24. Evidence baseline

Use official documentation as the primary source. Record each implemented tweak in `docs/EVIDENCE.md`, including:

- Source.
- Evidence level.
- What the source actually establishes.
- What it does not establish.
- Applicable systems.
- Expected effect.
- Risks.
- Security impact.
- Verification.
- Rollback.

Review at minimum:

- Microsoft Windows performance:
  https://support.microsoft.com/en-us/windows/experience/performance-optimization/tips-to-improve-pc-performance-in-windows
- Startup applications:
  https://support.microsoft.com/en-us/windows/experience/startup-boot/configure-startup-applications-in-windows
- Background applications:
  https://support.microsoft.com/en-us/windows/experience/performance-optimization/manage-background-activity-for-apps-in-windows
- Game Mode:
  https://support.xbox.com/en-US/help/games-apps/game-setup-and-play/use-game-mode-gaming-on-pc
- Windowed-game optimizations:
  https://support.microsoft.com/en-us/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11
- Refresh rate:
  https://support.microsoft.com/en-us/windows/hardware/display-graphics/change-the-refresh-rate-on-your-monitor-in-windows
- Powercfg:
  https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options
- Pagefile:
  https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/introduction-to-the-page-file
- Pagefile sizing:
  https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/how-to-determine-the-appropriate-page-file-size-for-64-bit-versions-of-windows
- MMCSS:
  https://learn.microsoft.com/en-us/windows/win32/procthread/multimedia-class-scheduler-service
- Windows settings Registry reference:
  https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-windows-11
- ApplicationManagement Policy CSP, including AllowGameDVR:
  https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-applicationmanagement
- Defender Policy CSP:
  https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-defender
- Set-MpPreference:
  https://learn.microsoft.com/en-us/powershell/module/defender/set-mppreference
- Run and RunOnce Registry keys:
  https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys
- Application Registration and App Paths:
  https://learn.microsoft.com/en-us/windows/win32/shell/app-registration
- Uninstall Registry key:
  https://learn.microsoft.com/en-us/windows/win32/msi/uninstall-registry-key
- Alternate Registry views:
  https://learn.microsoft.com/en-us/windows/win32/winprog64/accessing-an-alternate-registry-view
- Get-NetAdapterAdvancedProperty:
  https://learn.microsoft.com/en-us/powershell/module/netadapter/get-netadapteradvancedproperty
- Set-NetAdapterAdvancedProperty:
  https://learn.microsoft.com/en-us/powershell/module/netadapter/set-netadapteradvancedproperty
- TDR Registry keys for testing/debugging, not optimization:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys
- timeBeginPeriod:
  https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod
- High-resolution timestamps:
  https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps
- BCDEdit:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/bcdedit--set
- Scheduling priorities:
  https://learn.microsoft.com/en-us/windows/win32/procthread/scheduling-priorities
- TCP socket options:
  https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-tcp-socket-options
- Network adapter tuning:
  https://learn.microsoft.com/en-us/windows-server/networking/technologies/network-subsystem/net-sub-performance-tuning-nics
- Windows Device Security:
  https://support.microsoft.com/en-us/windows/security/windows-security/device-security-in-the-windows-security-app
- Least privilege:
  https://learn.microsoft.com/en-us/windows/win32/secbp/running-with-administrator-privileges
- Android ABIs:
  https://developer.android.com/ndk/guides/abis
- BlueStacks Android versions:
  https://support.bluestacks.com/hc/en-us/articles/360058931031-How-to-utilize-the-different-Android-versions-available-on-BlueStacks-5
- BlueStacks Free Fire settings:
  https://support.bluestacks.com/hc/en-us/articles/360057784811-Recommended-settings-for-Free-Fire-on-BlueStacks-5
- BlueStacks Free Fire 90 FPS:
  https://support.bluestacks.com/hc/en-us/articles/360059304111-How-to-play-Free-Fire-at-90-FPS-on-BlueStacks-5
- BlueStacks Free Fire MAX:
  https://support.bluestacks.com/hc/en-us/articles/43864024050829-Free-Fire-MAX-on-PC-with-BlueStacks-5
- BlueStacks GPU settings:
  https://support.bluestacks.com/hc/en-us/articles/360054877891-How-to-use-GPU-settings-to-increase-gaming-performance-on-BlueStacks-5
- BlueStacks renderer settings:
  https://support.bluestacks.com/hc/en-us/articles/360057389932-How-to-change-the-graphics-settings-on-BlueStacks-5
- MSI App Player:
  https://www.msi.com/Landing/appplayer
- Garena connection guidance:
  https://ffsupport.garena.com/hc/en-us/articles/4412920964762-Connection-Issues
- Garena lag troubleshooting:
  https://ffsupport.garena.com/hc/en-us/articles/4412920970394-Troubleshooting-step-Game-Lag
- Garena Abuse Policy:
  https://ffsupport.garena.com/hc/en-us/articles/4412928339866-Abuse-Policy
- PresentMon:
  https://github.com/GameTechDev/PresentMon
- pywebview architecture:
  https://pywebview.flowrl.com/guide/architecture
- pywebview bridge:
  https://pywebview.flowrl.com/guide/interdomain
- pywebview security:
  https://pywebview.flowrl.com/guide/security
- WebView2 distribution:
  https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
- Windows navigation design basics:
  https://learn.microsoft.com/en-us/windows/apps/design/basics/navigation-basics
- Typography in Windows:
  https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography
- Fluent 2 design tokens:
  https://fluent2.microsoft.design/design-tokens
- Fluent 2 layout:
  https://fluent2.microsoft.design/layout
- WCAG 2.2 Quick Reference:
  https://www.w3.org/WAI/WCAG22/quickref/
- Microsoft Fluent System Icons:
  https://github.com/microsoft/fluentui-system-icons
- Performance budgets:
  https://web.dev/articles/performance-budgets-101
- Interaction responsiveness and long-task guidance:
  https://web.dev/articles/top-cwv
- Codex best practices:
  https://learn.chatgpt.com/guides/best-practices
- Codex prompting:
  https://learn.chatgpt.com/docs/prompting
- Codex AGENTS.md repository guidance:
  https://learn.chatgpt.com/docs/agent-configuration/agents-md

If a setting lacks reliable documentation or repeatable evidence:

- Mark it unverified.
- Keep it out of default profiles.
- Do not imply that community popularity proves performance.

---

## 25. Open-source and licensing rules

You may study architecture and UX patterns from:

- Chris Titus Tech WinUtil.
- Sophia Script.
- AtlasOS.
- OptimizerNXT.
- PresentMon.

Do not blindly copy their tweaks.

Verify every project’s current license before reusing code.

Do not copy GPL code into a closed-source IPAN Optimizer product unless the project intentionally complies with the GPL obligations.

If PresentMon or another MIT component is bundled, preserve the required copyright and license notice in `THIRD_PARTY_NOTICES.md`.

If Microsoft Fluent System Icons are bundled, preserve their MIT notice, include only the selected local SVG subset, and record source version/file hashes in `ASSET_PROVENANCE.md`.

---

## 26. Implementation phases

### Phase 1 — Foundation

- Project structure.
- Root `AGENTS.md` with exact repository conventions, safety boundaries, build/test commands, UI control gate, and Definition of Done.
- Python environment and dependency locking.
- Typed contracts.
- Structured logging.
- SQLite migrations.
- Mock Windows backend.
- Base pywebview shell.
- Indonesian design system with the exact anti-AI-slop rules and semantic tokens.
- Local Fluent System Icons subset, license notice, and asset provenance.
- Performance-budget measurement harness.
- Initial `docs/CONTROL_MATRIX.md`, fake bridge, and functional UI test harness.
- Test configuration.

### Phase 2 — Read-only scan

- Capability scanner.
- `MachineCapabilityVector`.
- Resource-budget calculator with rounding/boundary tests.
- PC report.
- Compatibility status.
- Game/emulator discovery.
- Evidence display.
- Graceful handling of custom Windows.

### Phase 3 — Safety engine

- Manifest schema.
- Policy layer.
- Snapshot engine.
- Dry Run.
- Verification.
- Rollback.
- Recovery journal.
- Fake elevated helper for tests.

### Phase 4 — Safe Daily

- Startup audit.
- Background-process audit.
- Visual effects.
- Game Mode.
- Storage.
- Pagefile.
- Display.
- Power diagnostics.
- Driver/thermal report.
- Network diagnostics.

### Phase 5 — Gaming session

- Game discovery.
- GPU preference.
- Session power lifecycle.
- Background-process selection.
- Process-tree monitoring.
- Automatic restoration.
- Crash recovery.

### Phase 6 — Emulator

- BlueStacks adapter.
- MSI App Player adapter.
- Instance detection.
- ABI/version detection where safe.
- Config backup.
- Atomic config updates.
- Free Fire profiles.
- Requested-target versus safe-cap versus final-allocation UI.
- Unknown-version read-only safety.

### Phase 7 — Benchmark

- PresentMon adapter.
- Resource sampler.
- Network tests.
- Repeated-run comparison.
- Honest statistical wording.
- Benchmark history UI.

### Phase 8 — Hardening and packaging

- Real elevated helper.
- Manifest signatures.
- Threat-model tests.
- WebView2 prerequisite flow.
- PyInstaller.
- Inno Setup.
- Upgrade/uninstall tests.
- Cross-spec compatibility matrix.
- Visual/accessibility/performance-budget gates.
- Complete control inventory, bridge-contract tests, E2E tests, and zero-console-error gate.
- Release documentation.

At the end of each phase:

1. Run formatters and linters.
2. Run relevant unit/integration/security tests.
3. Fix failures.
4. Update `TASKS.md`.
5. Update documentation.
6. Record limitations honestly.

---

## 27. Definition of done

The application is complete only when:

- It launches as a non-admin user.
- It works offline after prerequisites are installed.
- Missing optional Windows components produce diagnostics instead of crashes.
- Automated tests make no real system changes.
- Every implemented tweak has detection, snapshot, apply, verification, and rollback.
- Rollback is idempotent.
- Interrupted transactions can be recovered.
- Prohibited tweaks cannot pass policy validation.
- The frontend cannot execute arbitrary system operations.
- Unknown BlueStacks/MSI versions fail safely in read-only mode.
- No default is tied to Ryzen 5 5500, RX 6600 XT, 16 GB RAM, or another named component.
- Low-resource, mainstream, high-resource, iGPU, dGPU, multi-GPU, laptop, and storage fixtures produce safe, explainable states.
- Free Fire profiles do not touch APK, memory, packets, client files, gameplay, or anti-cheat.
- Benchmark results distinguish improvement, regression, invalid tests, and inconclusive/noise.
- PyInstaller produces a working `onedir` package.
- The installer handles WebView2 safely.
- User-facing text is Indonesian.
- Every visible button, menu item, toggle, filter, disclosure, dialog action, table action, and keyboard action is listed in `docs/CONTROL_MATRIX.md`, has a real handler, and passes its mapped tests.
- No dead control, placeholder action, `href="#"`, empty callback, duplicate-submit transaction, false-success toast, uncaught bridge exception, unhandled Promise rejection, or console error remains in a primary workflow.
- Scan, transaction preview/apply/verify/cancel/rollback, Restore, game session, emulator profile, benchmark, Settings, export, and navigation workflows pass integration/E2E tests.
- The UI meets the specified asset-size, startup, interaction, idle CPU, memory, and offline-network budgets or documents a reviewed measurement-based exception.
- The required viewport/DPI, keyboard, focus, contrast, reduced-motion, and forced-colors QA passes.
- No AI-generated logo/icon/illustration, emoji control, mixed icon set, gradient, mass glassmorphism, fake score/gauge, or decorative looping motion is present.
- Every bundled visual asset has provenance and license information.
- Build, test, package, recovery, and limitation documentation is complete.

The final Codex response must provide:

- Architecture summary.
- Files created and changed.
- Commands executed.
- Test results.
- Build result.
- Installer result.
- Features completed.
- Functional-control coverage summary, including total controls, mapped tests, failures, and any intentionally disabled control with reason.
- Confirmation that primary workflows ran without console errors, unhandled Promise rejections, or uncaught bridge exceptions.
- Known limitations.
- Items not implemented and why.
- Safe next steps.

Begin now by inspecting the repository and the applicable `AGENTS.md` instructions. Create or update the specification and architecture documents, then continue into implementation after the approved plan. Do not stop at a visual prototype or a plan-only response.

# END PROMPT
