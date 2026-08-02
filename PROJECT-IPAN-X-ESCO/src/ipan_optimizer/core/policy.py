from __future__ import annotations

from ipan_optimizer.adapters.windows.registry import validate_registry_operation
from ipan_optimizer.domain.models import Operation, RiskLevel

_PROHIBITED_RULE_FRAGMENTS = frozenset(
    {
        "realtime",
        "disable_defender",
        "disable_firewall",
        "disable_uac",
        "disable_update",
        "disable_pagefile",
        "tcpackfrequency",
        "tcpnodelay",
        "systemresponsiveness_0",
        "gpu_priority_8",
        "bcdedit",
        "dll_injection",
        "packet_edit",
        "apk_modify",
    }
)


class PolicyViolation(ValueError):
    pass


def validate_rule_id(rule_id: str) -> None:
    normalized = rule_id.casefold()
    if any(fragment in normalized for fragment in _PROHIBITED_RULE_FRAGMENTS):
        raise PolicyViolation(f"Rule terlarang ditolak: {rule_id}")


def validate_operation(operation: Operation, *, risk: RiskLevel = RiskLevel.SAFE) -> None:
    if risk is RiskLevel.PROHIBITED:
        raise PolicyViolation("Operasi dengan risiko prohibited tidak dapat direncanakan.")
    if operation.operation == "registry_set":
        try:
            validate_registry_operation(operation)
        except ValueError as exc:
            raise PolicyViolation(str(exc)) from exc
    elif operation.operation == "service_start":
        if risk is RiskLevel.SAFE:
            raise PolicyViolation("Perubahan service tidak boleh masuk profil aman.")
    elif operation.operation == "power_set_active":
        return
    else:
        raise PolicyViolation("Tipe operasi tidak dikenal.")
