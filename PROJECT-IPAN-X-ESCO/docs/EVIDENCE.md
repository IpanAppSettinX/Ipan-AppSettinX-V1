# Evidence catalog

Every implemented rule must record source URL, verification date, evidence
level, what the source establishes, what it does not establish, applicability,
expected effect, risk, security impact, verification, and rollback.

Initial evidence sources are listed in `Riset_Tweak_Gaming_Windows_10_11.md`.
The implementation must revalidate sources before enabling a write. If a raw
Registry target lacks a stable public contract, it is treated as observed,
audit-only, or read-only even when the corresponding Windows setting is
documented.

No community popularity is sufficient evidence for a default rule.

## Implemented Dry Run rules

| Rule | Evidence | Establishes | Does not establish | Risk | Verification / rollback |
|---|---|---|---|---|---|
| `windows.game_mode` | [Xbox Game Mode](https://support.xbox.com/en-US/help/games-apps/game-setup-and-play/use-game-mode-gaming-on-pc), [Windows settings reference](https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-windows-11) | Windows exposes Game Mode and maps `AutoGameModeEnabled` to its toggle | A guaranteed FPS increase | Safe | Compare typed DWORD target; restore exact prior value/type/absence |
| `mouse.linear_pointer` | [SystemParametersInfo](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa), [mouse settings](https://support.microsoft.com/en-us/windows/hardware/input-devices/change-mouse-settings) | Pointer speed is 1-20 with default 10; Windows exposes pointer precision behavior | AI, aim assist, headshots, lower latency, or effect in raw-input games | Conditional | Compare four exact HKCU values; restore each exact snapshot |
| `gaming.background_capture_off` | [AllowGameDVR policy](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-applicationmanagement), [Windows settings reference](https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-windows-11) | Windows exposes Game DVR/capture controls | A guaranteed FPS gain or a stable effect on every Windows build | Conditional | Compare two exact HKCU DWORD targets; restore exact snapshots |

All three rules are simulation-only until the exact Registry mappings pass the
disposable Windows VM matrix. The UI describes `mouse.linear_pointer` as input
behavior, not AI, and describes background capture as a feature tradeoff, not a
performance promise.

## Rejected or analysis-only families

- Defender, Firewall, UAC, tamper protection, exploit mitigation, and Windows
  Update weakening remain prohibited.
- BCD/timer packs, TDR changes, bulk service disablement, arbitrary process
  termination, aggressive cache deletion, custom binary mouse curves, and
  fabricated Aim/Headshot Registry names are not executable rules.
- `Easy Drag` opens the official Windows Mouse Settings UI for ClickLock instead
  of overwriting `UserPreferencesMask`, which shares bits with other settings.

See `docs/ARTIFACT_SECURITY_RESEARCH.md` for hashes, corpus counts, static
methodology, and source-to-feature decisions.
