# Static artifact and public registry research

Date: 2026-07-27

## Scope and method

The following sources were inspected without executing any untrusted binary,
batch, command, PowerShell, Registry, or configuration file:

- `D:\OPTIMIZE\Amber Oprimizer By Spokie.exe`
- `D:\OPTIMIZE\viet (1).bat`
- Public Google Drive folder ID
  `1dn5Nfk7OwLdt-qnipkDJCP5RuXKpnS3J`

The EXE was parsed as a PE file and inspected for metadata, imports, resources,
entropy, and printable embedded commands. The BAT and public Drive text corpus
were decoded, tokenized, and pattern-classified. Binary files advertised in the
Drive folder were inventoried by metadata but were not downloaded or executed.

This is a static assessment, not a malware-clean verdict. Static analysis cannot
prove that a binary is harmless, and absence of a public hash match is not
evidence of safety.

## Supplied artifact identity

| Artifact | Size | SHA-256 | Signature |
|---|---:|---|---|
| Amber Oprimizer By Spokie.exe | 72,704 bytes | `F39CE3DAA27D9E4D498FAAC6D2FD33457B82E520BD1D8455231632C91E81F18D` | Not signed |
| viet (1).bat | 159,931 bytes, 1,930 lines | `4AD6DB5DD85637CE875A7C14027E8E3BEEBEABE5FBED315040E2D492C93E05AD` | Not applicable |

### EXE observations

- PE machine: AMD64 / x64.
- Compile timestamp recorded in the PE header: 2021-01-14 13:41:54 UTC. PE
  timestamps are attacker-controlled and are not trusted authorship evidence.
- Import hash: `5f8c85c4e25cacbe99b242e6382490cb`.
- Whole-file entropy: 6.6719; `.rsrc` entropy: 7.899.
- No Authenticode signature and no overlay were present.
- Imports include `KERNEL32`, `USER32`, `ADVAPI32`, MSVC runtime libraries, and
  the C runtime `system` function.
- Printable strings contain `reg.exe` and `bcdedit.exe` commands affecting
  services, boot timer configuration, hypervisor behavior, graphics TDR, and
  security mitigations.
- Static disassembly mapped the five menu branches without starting the binary:

| Order | Embedded label | Commands reached by branch | Product decision |
|---:|---|---:|---|
| 1 | APPLY REGEDIT | 1 Registry write, 1 external URL, 1 console command | Analysis only; undocumented HKLM value blocked |
| 2 | CLEAN TEMP FILES | 1 recursive forced delete, 2 console commands | Blocked; no inventory or recoverable snapshot |
| 3 | APPLY BOOSTER | 20 BCDEdit writes, 1 console command | Blocked; boot, timer, virtualization, and mitigation risk |
| 4 | REVERT ALL CHANGES | 87 Registry writes, 18 BCD deletions, 1 console command | Replaced with snapshot/System Restore path |
| 5 | CLEAN LOG FILES (NEW!) | 2 recursive forced deletes, 1 console command | NEW marker removed; broad home-directory delete blocked |

The branch counts above exclude UI-only message boxes. They were recovered by
resolving x64 RIP-relative string references and calls to the imported C runtime
`system` function. This confirms command ownership per menu branch while keeping
the executable unopened as a process.

Decision: do not run or redistribute the EXE. Individual ideas are accepted only
after independent validation and conversion into typed, allowlisted Dry Run
rules.

### BAT observations

- 75 labels and 1,722 parsed command lines.
- 1,116 Registry command occurrences across 187 unique Registry paths and 431
  unique value names.
- Pattern matches include:

| Pattern class | Matches |
|---|---:|
| Security reduction | 54 |
| Service changes | 73 |
| Network stack | 178 |
| Scheduler / priority | 42 |
| Destructive filesystem | 23 |
| Package removal | 28 |
| Boot configuration | 15 |
| Windows Update reduction | 8 |
| Process termination | 5 |
| Hypervisor configuration | 3 |
| Remote URL references | 4 |

The menu exposes Defender off, Firewall off, Windows Update off, Hyper-V off,
debloat/removal, boot configuration, service disablement, and cache deletion.
These are not suitable as a daily universal profile.

The BAT also writes names such as `AimBot`, `AimAssist`, `AimHeadshot`,
`AutoHeadshot`, `AimLock`, and `FovAutoHeadshot`. Creating a Registry value does
not make Windows or a game consume it. No corresponding Windows contract or game
consumer was identified.

## Public Drive inventory

The public folder metadata exposed 92 folders and 496 inventory entries:

- 123 `.reg`
- 110 `.txt`
- 46 `.cfg`
- 29 `.exe`
- 19 `.bat`
- 7 `.zip`
- 5 `.cmd`
- other images, media, and configuration files

Only 303 text configuration files were downloaded: `.reg`, `.bat`, `.cmd`,
`.txt`, `.ini`, `.ps1`, and `.cfg`. Magic-byte validation rejected binary
content. The text corpus totals 4,289,523 bytes and 91,546 lines.

### Corpus measurements

| Measurement | Count |
|---|---:|
| Registry keys observed per file, summed | 675 |
| Registry value assignments | 4,609 |
| Registry commands | 2,512 |
| Mouse-behavior pattern matches | 3,235 |
| Service-change pattern matches | 461 |
| Destructive/process pattern matches | 140 |
| Security-reduction pattern matches | 90 |
| Boot/BCD pattern matches | 34 |
| Curated-candidate pattern matches | 25 |
| TDR pattern matches | 1 |

Counts are pattern matches, not unique vulnerabilities. A line can contribute to
more than one category.

### IPAN folder findings

- `Mouse Smooth Curve` sets `MouseSensitivity` to `70`, outside the documented
  Windows pointer-speed range of 1-20, and installs custom binary curves.
- `reg mouse 1` disables legacy pointer acceleration, sets sensitivity `6`, and
  installs custom curves. Only the conservative acceleration fields were
  considered; imported binary curves were rejected.
- `p.reg` uses thresholds `40` and `120`, custom binary curves, drag thresholds,
  and a short ClickLock time. It is not a safe universal profile.
- `Regedit High FPS IPAN` includes `GameDVR_Enabled=0`. This narrow capture
  control was separated from unrelated/unverified values.
- `optimizer.bat` disables services, clears caches, terminates system and user
  applications, changes boot timers, changes TDR, duplicates power plans, and
  writes multiple undocumented scheduler/filesystem/memory settings.
- `!EXM Free Tweaking Utility V9.3.cmd` contains thousands of commands spanning
  services, Game DVR, Game Mode, mouse settings, BCD, GPU, and cleanup. It is not
  imported as an executable or monolithic preset.

## Implemented decisions

| User-facing feature | Rating | Implemented behavior |
|---|---|---|
| Windows Game Mode | SAFE | Typed HKCU Dry Run rule, exact snapshot, verify, rollback |
| Aim Stabilizer | CAUTION | Honest “input pointer linear” rule: default speed and legacy acceleration off; explicitly not AI |
| Easy Drag | SAFE | Opens official Windows Mouse Settings for ClickLock; no shared binary mask overwrite |
| Boost FPS | CAUTION | Game DVR background capture off; no FPS guarantee; benchmark required |
| Aim Smooth AI | DANGEROUS / BLOCKED | Analysis-only because random curves and inert marketing values are unverified |
| Defender off | CRITICAL / BLOCKED | Visible warning; no operation or bypass |
| Firewall off | CRITICAL / BLOCKED | Visible warning; no operation |
| Windows Update off | CRITICAL / BLOCKED | Visible warning; no operation |
| BCD/timer packs | DANGEROUS / BLOCKED | Visible analysis; no operation |
| Disable TDR | CRITICAL / BLOCKED | Visible warning; no operation |
| Bulk service disable | DANGEROUS / BLOCKED | Visible analysis; no operation |
| Aggressive cleanup/process kill | DANGEROUS / BLOCKED | Visible analysis; no operation |

All Registry-capable features remain Dry Run in this development build. The
existing external release gates still require disposable-VM validation,
hardware QA, signature review, and code signing before any real provider can be
enabled.

## Primary evidence

- [Windows 11 settings Registry reference](https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-windows-11)
- [SystemParametersInfo mouse contracts](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa)
- [Microsoft mouse and ClickLock settings](https://support.microsoft.com/en-us/windows/hardware/input-devices/change-mouse-settings)
- [ApplicationManagement AllowGameDVR policy](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-applicationmanagement)
- [Defender tamper protection](https://learn.microsoft.com/en-us/defender-endpoint/manage-tamper-protection-individual-device)
- [Defender Antivirus policy](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-admx-microsoftdefenderantivirus)
- [TDR Registry keys are for driver testing/debugging](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys)
- [BCDEdit `/set` reference and warning](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/bcdedit--set)

## Reproducible local reports

Generated research artifacts are local and gitignored:

- `artifacts/artifact-analysis.json`
- `artifacts/drive-folder-metadata.json`
- `artifacts/drive-registry-crawl/crawl-report.json`
- `artifacts/drive-registry-crawl/text-download-report.json`
- `artifacts/drive-registry-analysis.json`

Scripts:

- `scripts/analyze_windows_artifacts.py`
- `scripts/parse_public_drive_metadata.py`
- `scripts/crawl_public_drive_registry.py`
- `scripts/download_public_drive_texts.py`
- `scripts/analyze_registry_corpus.py`
