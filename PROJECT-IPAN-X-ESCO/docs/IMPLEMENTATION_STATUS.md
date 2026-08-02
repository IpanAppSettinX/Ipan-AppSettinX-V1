# Implementation status

## Delivered safe baseline

Phases 0-4 are implemented for the declared Dry Run boundary:

- specification, architecture, threat model, design system, compatibility, and
  recovery documentation;
- strict typed domain contracts, JSON logging, SQLite migrations, and
  fake/Dry Run backends;
- read-only Windows capability, Registry, service, and power-plan adapters;
- capability-derived recommendations and allowlisted typed operations;
- snapshot-first transactions with verification, conflict detection, rollback,
  and a hash-chained recovery journal;
- a local Indonesian pywebview UI whose canonical controls are mapped to bridge
  or local handlers, with browser and real-WebView smoke coverage.
- a curated Tweak Library that visibly distinguishes safe, caution, dangerous,
  and critical/blocked items, with explicit warning acknowledgement before a
  transaction simulation;
- static research of the supplied unsigned EXE, BAT, and 303 public Drive text
  configurations without executing or importing untrusted scripts.

Phases 5-8 provide a safe implementation baseline:

- Dry Run game-session lifecycle;
- emulator product discovery plus an allowed-root, hash-checked atomic config
  storage primitive;
- bounded PresentMon CSV import and before/after statistical comparison;
- expiring, nonce-protected elevated-plan validation and separate helper build;
- PyInstaller main/helper sources and builds, an Inno Setup installer source,
  release hashing, automated tests, and manual/release QA checklists.

## Intentional safety blocks

The current application does not execute real Registry, service, power-plan,
emulator, or process mutations. The main process is `asInvoker`; the separate
administrator helper validates plans but rejects execution. These blocks are
deliberate until mutation behavior passes disposable-VM, crash, reboot,
rollback, security, and signing review.

Defender off, Firewall off, Windows Update off, BCD/timer packs, GPU TDR
disablement, bulk service changes, and aggressive cleanup remain visible as
analysis cards so users can understand the risk. They intentionally have no
mutation operation. “Aim Smooth AI” is also analysis-only because the source
files contain unconsumed marketing value names and unvalidated binary curves,
not an AI model or documented game control.

PresentMon capture is not bundled or launched. The benchmark module imports
bounded CSV files and compares captured runs. Vendor-specific emulator schemas
are not enabled because their supported locations, version compatibility, and
restore verification still need representative installations and vendor
evidence.

## Remaining release evidence

- Compile the Inno Setup source; `ISCC.exe` was not available in this workspace.
- Run Windows 10/11 VM mutation, reboot recovery, upgrade, and uninstall cases.
- Measure cold start, CPU, memory, long tasks, and navigation latency on a named
  reference fixture.
- Test representative GPU/display, game, and emulator combinations on physical
  hardware.
- Complete license review and code-sign all distributable artifacts.

Until those gates pass, generated binaries are development artifacts, not a
production release.
