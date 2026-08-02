from __future__ import annotations

import pytest

from ipan_optimizer.core.policy import PolicyViolation, validate_rule_id


@pytest.mark.parametrize(
    "rule_id",
    [
        "tweak.realtime",
        "security.disable_defender",
        "memory.disable_pagefile",
        "network.tcpnodelay",
        "game.dll_injection",
        "game.apk_modify",
    ],
)
def test_prohibited_rule_ids_are_rejected(rule_id: str) -> None:
    with pytest.raises(PolicyViolation):
        validate_rule_id(rule_id)


def test_safe_rule_id_is_allowed() -> None:
    validate_rule_id("windows.game_mode")
