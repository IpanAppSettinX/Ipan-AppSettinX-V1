# IPAN Optimizer specification

## Product contract

IPAN Optimizer detects machine capabilities, explains bottlenecks, previews
typed changes, snapshots exact prior state, applies through narrow providers,
verifies, and rolls back on failure, regression, cancellation, crash, reboot,
or user request.

Version 1 supports Windows 10/11 x64 with WebView2 Evergreen. Windows on ARM64
is detected and reported as read-only/unsupported until a separately tested
native package exists. Custom Windows builds receive best-effort capability
detection and safe degradation.

## Invariants

- No mutation occurs without a durable transaction, snapshot, and verification.
- Dry Run is the development and first-run default.
- Automated tests cannot construct a mutating host backend.
- Missing data is never represented as zero.
- Applicability is one of `SUPPORTED`, `SUPPORTED_DEGRADED`, `UNAVAILABLE`, or
  `UNKNOWN_READ_ONLY`.
- Capability state is one of `AVAILABLE`, `UNAVAILABLE`, `UNSUPPORTED`,
  `UNKNOWN`, or `ERROR`, with reason and evidence.
- User-facing copy is clear Indonesian.
- No fake scores, gains, latency claims, or anti-ban claims.
- No security-reducing change is part of a default profile.

## V1 workflows

1. Scan and inspect capabilities.
2. Review evidence-backed recommendations.
3. Preview a transaction and exact current/proposed state.
4. Apply in Dry Run or through a confirmed typed provider.
5. Verify, keep, cancel at a safe boundary, or roll back.
6. Recover incomplete operations at startup.
7. Manage game sessions and emulator profiles.
8. Run or import repeatable benchmark sessions.
9. Export diagnostic and transaction reports without executable content.

## Member access

- Firebase Email/Password authenticates member accounts.
- Firestore Security Rules atomically bind one account to one device hash and
  one device hash to one account; local JavaScript is never authoritative.
- Raw Windows device identifiers are neither transmitted nor persisted.
- Invalid credentials, network failure, or binding conflict keeps the
  application shell locked.

## Resource guards

`host_reserve_mb = max(3072, ceil_to_512(0.30 * total_ram_mb))`

`safe_emulator_ram_cap_mb = floor_to_512(max(0, min(total_ram_mb -
host_reserve_mb, available_ram_mb - 2048)))`

Physical CPU budget uses trustworthy physical cores, otherwise
`max(1, floor(logical_processors / 2))`. Safe emulator CPU allocation is
`max(0, min(physical_budget, logical_processors - 2))`.

## Release boundary

Real Windows mutations and installer validation are release-blocked until they
pass disposable-VM tests, manual hardware QA, signing review, and the complete
control matrix. Current implementation supports fake and Dry Run execution.

