from __future__ import annotations

import pytest

from ipan_optimizer.core.rules import resolve_operations
from ipan_optimizer.privileged.plan import (
    create_elevated_plan,
    validate_elevated_plan,
)


def test_elevated_plan_validates() -> None:
    plan = create_elevated_plan("tx-1", resolve_operations(["windows.game_mode"]))
    validate_elevated_plan(plan, used_nonces=set())


def test_elevated_plan_rejects_replay() -> None:
    plan = create_elevated_plan("tx-1", resolve_operations(["windows.game_mode"]))
    with pytest.raises(ValueError, match="Nonce"):
        validate_elevated_plan(plan, used_nonces={plan.nonce})


def test_elevated_plan_rejects_digest_tampering() -> None:
    plan = create_elevated_plan("tx-1", resolve_operations(["windows.game_mode"]))
    tampered = plan.model_copy(update={"plan_digest": "0" * 64})
    with pytest.raises(ValueError, match="Digest"):
        validate_elevated_plan(tampered, used_nonces=set())
