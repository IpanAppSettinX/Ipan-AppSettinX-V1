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

## Structure and style

- Python source lives under `src/ipan_optimizer`; use Python 3.12 type hints.
- Frontend is packaged local HTML/CSS/vanilla ES modules with Indonesian copy.
- Use semantic controls with unique `data-control-id` values.
- Component CSS uses tokens from `tokens.css`; no gradients, webfonts, emoji
  controls, generated art, or mixed icon families.
- Keep user data out of logs; structured logs must redact paths and identifiers.

## Commands

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest
python scripts/check_control_matrix.py
python scripts/check_frontend_policy.py
python scripts/check_asset_budget.py
```

## Definition of done

A change is complete only when formatting, static checks, relevant unit,
integration, security, and UI tests pass; documentation, `TASKS.md`, and
`LAST_ACTIVITY.md` reflect the result; no test mutates the host; and every
visible control is mapped to a handler and test in `docs/CONTROL_MATRIX.md`.
