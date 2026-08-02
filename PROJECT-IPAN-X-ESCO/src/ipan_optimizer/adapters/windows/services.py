from __future__ import annotations

import re
import sys

from ipan_optimizer.adapters.windows.common import run_fixed_command
from ipan_optimizer.domain.models import ServiceStartOperation, TypedSnapshot

_ALLOWED_SERVICES = frozenset({"SysMain", "WSearch"})
_STATE_RE = re.compile(r"STATE\s*:\s*\d+\s+([A-Z_]+)")


class ServiceReadAdapter:
    def snapshot(self, operation: ServiceStartOperation) -> TypedSnapshot:
        if operation.service_name not in _ALLOWED_SERVICES:
            raise ValueError("Service tidak berada dalam allowlist.")
        target = f"service:{operation.service_name}".casefold()
        if sys.platform != "win32":
            return TypedSnapshot(
                operation_id=operation.operation_id,
                provider="service",
                target_key=target,
                existed=False,
            )
        try:
            output = run_fixed_command(["sc.exe", "query", operation.service_name])
        except RuntimeError as exc:
            if "1060" in str(exc):
                return TypedSnapshot(
                    operation_id=operation.operation_id,
                    provider="service",
                    target_key=target,
                    existed=False,
                )
            raise
        match = _STATE_RE.search(output)
        state = match.group(1).lower() if match else "unknown"
        return TypedSnapshot(
            operation_id=operation.operation_id,
            provider="service",
            target_key=target,
            existed=True,
            value_type="service_state",
            raw_value=state,
        )
