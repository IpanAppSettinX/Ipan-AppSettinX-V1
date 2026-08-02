# IPAN Optimizer

IPAN Optimizer is a local-first Windows 10/11 desktop utility for evidence-based
diagnostics and reversible performance changes. It is not a one-click Registry
tweak pack and does not weaken Windows security.

The safe implementation baseline covers capability scanning, typed snapshots,
transaction preview/apply/verify/rollback in Dry Run, recovery journaling, the
main pywebview UI, emulator discovery primitives, benchmark CSV analysis, and
packaging sources. The Tweak Library labels each reviewed feature Safe, Caution,
Dangerous, or Critical/Blocked and does not present Registry folklore as AI.
Development mode is always Dry Run: Windows state is read when safe, while
mutations are simulated against an in-memory overlay.

Real host mutations, privileged execution, PresentMon capture, vendor-specific
emulator writes, installer compilation, code signing, and VM/hardware release
QA remain intentionally blocked. See `docs/IMPLEMENTATION_STATUS.md`.

## Development

Requires Python 3.12 x64. Create a virtual environment, install
`requirements-dev.lock`, then run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ipan_optimizer.main --dry-run
```

See `SPEC.md`, `ARCHITECTURE.md`, and `docs/RECOVERY.md` before adding an
operation. Static research of the supplied EXE, BAT, and public Drive registry
corpus is documented in `docs/ARTIFACT_SECURITY_RESEARCH.md`.
