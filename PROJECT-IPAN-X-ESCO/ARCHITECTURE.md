# Architecture

## Dependency direction

```text
Packaged frontend -> typed bridge -> application services
  -> pure domain/core -> provider protocols -> adapters
```

The frontend cannot import or name Windows operations. Application services
convert validated requests into use cases. Core policy validates rule,
capability, risk, and conflicts. The transaction manager is the only component
allowed to invoke a mutating provider.

## Backends

- `FakeWindowsBackend`: deterministic fixtures for tests.
- `DryRunWindowsBackend`: safe reads plus copy-on-write simulated mutations.
- Real Windows adapters: narrow read/write implementations; real write mode is
  release-gated and cannot be selected by tests.

## Transactions

State transitions are:

`PLANNED -> SNAPSHOTTED -> APPLYING -> APPLIED -> VERIFIED -> KEPT`

Failure or user restoration moves through `ROLLING_BACK -> ROLLED_BACK`.
Unsafe uncertainty becomes `RECOVERY_REQUIRED` or `FAILED_SAFE`.

Snapshots preserve absence, type, raw data, view, policy ownership, and the
state the transaction intends to write. Apply and rollback use compare-before-
write semantics.

## Long-running work

Bridge methods return quickly. Scans, benchmarks, hashing, and transactions run
in a bounded thread pool. Jobs expose progress, cancellation requests, and a
safe cancellation boundary.

## Persistence

SQLite stores application entities and migrations. An append-only JSONL
recovery journal is maintained separately with sequence and hash-chain fields
so incomplete operations remain discoverable when higher-level state is
damaged.

## Privilege

The main executable is `asInvoker`. A future one-shot elevated helper receives
only a validated typed plan and nonce, revalidates all state after elevation,
records a result, and exits. No permanent service is installed.

## Authentication

The local frontend sends credentials only through the typed `authenticate`
bridge. Python signs in directly to Firebase Authentication, hashes the
read-only Windows MachineGuid with an application scope, and writes the
account/device binding pair straight to Firestore in one atomic `commit`.
Firestore Security Rules (`firestore.rules`) cross-check the pair with
`getAfter()` so a single account maps to a single device hash and vice versa;
clients cannot update or delete bindings. No Cloud Functions or paid Firebase
plan are required.

