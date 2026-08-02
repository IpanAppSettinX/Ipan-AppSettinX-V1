# Recovery

At startup, incomplete transactions are detected before new mutations are
allowed. Recovery displays the original state, intended state, current state,
last durable journal step, and safest available action.

Rollback is idempotent and conflict-aware. If another actor changed the target
after apply, automatic rollback stops and records a recovery conflict instead
of overwriting the new state.

Dry Run recovery uses the same state machine and journal but only changes the
shadow backend. System Restore may be offered for grouped changes where
supported, but it is never the only snapshot.

