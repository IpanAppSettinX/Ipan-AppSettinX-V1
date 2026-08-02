from __future__ import annotations

import re
import sys

from ipan_optimizer.adapters.windows.common import run_fixed_command
from ipan_optimizer.domain.models import PowerSchemeOperation, TypedSnapshot

_GUID_RE = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


class PowerReadAdapter:
    def active_scheme(self) -> str | None:
        if sys.platform != "win32":
            return None
        output = run_fixed_command(["powercfg.exe", "/getactivescheme"])
        match = _GUID_RE.search(output)
        return match.group(1).lower() if match else None

    def list_schemes(self) -> list[dict[str, str | bool]]:
        if sys.platform != "win32":
            return []
        output = run_fixed_command(["powercfg.exe", "/list"])
        active = self.active_scheme()
        schemes: list[dict[str, str | bool]] = []
        for line in output.splitlines():
            match = _GUID_RE.search(line)
            if not match:
                continue
            guid = match.group(1).lower()
            name_match = re.search(r"\((.+?)\)", line)
            schemes.append(
                {
                    "guid": guid,
                    "name": name_match.group(1) if name_match else "Power plan",
                    "active": guid == active,
                }
            )
        return schemes

    def snapshot(self, operation: PowerSchemeOperation) -> TypedSnapshot:
        active = self.active_scheme()
        return TypedSnapshot(
            operation_id=operation.operation_id,
            provider="power",
            target_key=f"power:{operation.scheme_guid}".casefold(),
            existed=active is not None,
            value_type="power_scheme_guid",
            raw_value=active,
        )
