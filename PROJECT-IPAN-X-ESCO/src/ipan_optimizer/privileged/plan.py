from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta

from pydantic import Field

from ipan_optimizer.core.policy import validate_operation
from ipan_optimizer.domain.models import Operation, StrictModel


class ElevatedPlan(StrictModel):
    schema_version: int = 1
    transaction_id: str
    nonce: str = Field(min_length=32, max_length=128)
    created_at: datetime
    expires_at: datetime
    plan_digest: str
    operations: list[Operation]


def _operation_digest(operations: list[Operation]) -> str:
    canonical = json.dumps(
        [operation.model_dump(mode="json") for operation in operations],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_elevated_plan(
    transaction_id: str,
    operations: list[Operation],
    *,
    lifetime_seconds: int = 120,
) -> ElevatedPlan:
    now = datetime.now(UTC)
    return ElevatedPlan(
        transaction_id=transaction_id,
        nonce=secrets.token_urlsafe(32),
        created_at=now,
        expires_at=now + timedelta(seconds=lifetime_seconds),
        plan_digest=_operation_digest(operations),
        operations=operations,
    )


def validate_elevated_plan(plan: ElevatedPlan, *, used_nonces: set[str]) -> None:
    now = datetime.now(UTC)
    if plan.nonce in used_nonces:
        raise ValueError("Nonce telah digunakan.")
    if plan.expires_at <= now or plan.created_at > now + timedelta(seconds=5):
        raise ValueError("Plan telah kedaluwarsa atau waktu tidak valid.")
    if plan.plan_digest != _operation_digest(plan.operations):
        raise ValueError("Digest operation plan tidak cocok.")
    for operation in plan.operations:
        validate_operation(operation)
