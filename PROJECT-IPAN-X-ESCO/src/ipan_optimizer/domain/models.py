from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False, strict=True)


class CapabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class ApplicabilityState(StrEnum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_DEGRADED = "SUPPORTED_DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN_READ_ONLY = "UNKNOWN_READ_ONLY"


class RiskLevel(StrEnum):
    SAFE = "safe"
    CONDITIONAL = "conditional"
    EXPERIMENTAL = "experimental"
    PROHIBITED = "prohibited"


class EvidenceLevel(StrEnum):
    VENDOR_DOCUMENTED = "vendor_documented"
    REPEATABLE_BENCHMARK = "repeatable_benchmark"
    DIAGNOSTIC_HEURISTIC = "diagnostic_heuristic"
    COMMUNITY_HYPOTHESIS = "community_hypothesis"
    REJECTED_MYTH = "rejected_myth"


class TransactionState(StrEnum):
    PLANNED = "PLANNED"
    SNAPSHOTTED = "SNAPSHOTTED"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    VERIFIED = "VERIFIED"
    KEPT = "KEPT"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    FAILED_SAFE = "FAILED_SAFE"


class JobState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


JsonValue = Any


class EvidenceRef(StrictModel):
    source: str
    detail: str
    verified_at: datetime | None = None


class Capability(StrictModel):
    key: str
    state: CapabilityState
    value: JsonValue = None
    reason: str
    evidence: list[EvidenceRef] = Field(default_factory=list)


class MachineCapabilityVector(StrictModel):
    scan_id: str = Field(default_factory=lambda: str(uuid4()))
    captured_at: datetime = Field(default_factory=utc_now)
    machine_scope: str = "local"
    capabilities: dict[str, Capability]
    warnings: list[str] = Field(default_factory=list)


class ResourceBudget(StrictModel):
    total_ram_mb: int
    available_ram_mb: int
    host_reserve_mb: int
    safe_emulator_ram_cap_mb: int
    logical_processors: int
    physical_core_budget: int
    safe_emulator_cpu_cap: int


class RegistryView(StrEnum):
    NATIVE = "native"
    VIEW_32 = "32"
    VIEW_64 = "64"


class RegistryValueType(StrEnum):
    REG_DWORD = "REG_DWORD"
    REG_QWORD = "REG_QWORD"
    REG_SZ = "REG_SZ"
    REG_EXPAND_SZ = "REG_EXPAND_SZ"
    REG_MULTI_SZ = "REG_MULTI_SZ"
    REG_BINARY = "REG_BINARY"


class RegistrySetOperation(StrictModel):
    operation: Literal["registry_set"] = "registry_set"
    operation_id: str
    allowlist_id: str
    hive: Literal["HKCU", "HKLM"]
    subkey: str
    value_name: str
    registry_view: RegistryView = RegistryView.NATIVE
    value_type: RegistryValueType
    data: int | str | list[str] | bytes
    requires_admin: bool = False

    @field_validator("subkey", "value_name")
    @classmethod
    def reject_unsafe_registry_text(cls, value: str) -> str:
        if "\x00" in value or "*" in value or "?" in value:
            raise ValueError("Target Registry mengandung karakter yang ditolak.")
        if value.startswith("\\\\") or "wow6432node" in value.casefold():
            raise ValueError("Remote Registry dan WOW6432Node literal ditolak.")
        return value.strip("\\")


class ServiceStartOperation(StrictModel):
    operation: Literal["service_start"] = "service_start"
    operation_id: str
    service_name: str
    requires_admin: bool = True

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, value: str) -> str:
        if not value or not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Nama service tidak valid.")
        return value


class PowerSchemeOperation(StrictModel):
    operation: Literal["power_set_active"] = "power_set_active"
    operation_id: str
    scheme_guid: str
    requires_admin: bool = False

    @field_validator("scheme_guid")
    @classmethod
    def validate_guid(cls, value: str) -> str:
        import uuid

        return str(uuid.UUID(value))


Operation = Annotated[
    RegistrySetOperation | ServiceStartOperation | PowerSchemeOperation,
    Field(discriminator="operation"),
]


class TypedSnapshot(StrictModel):
    operation_id: str
    provider: str
    target_key: str
    existed: bool
    value_type: str | None = None
    raw_value: Any = None
    policy_managed: bool = False
    captured_at: datetime = Field(default_factory=utc_now)


class OperationResult(StrictModel):
    operation_id: str
    success: bool
    dry_run: bool
    message: str
    resulting_value: Any = None


class VerificationResult(StrictModel):
    operation_id: str
    verified: bool
    message: str
    current_value: Any = None


class Transaction(StrictModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_ids: list[str]
    operations: list[Operation]
    state: TransactionState = TransactionState.PLANNED
    snapshots: list[TypedSnapshot] = Field(default_factory=list)
    results: list[OperationResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    dry_run: bool = True
    error: str | None = None


class Recommendation(StrictModel):
    recommendation_id: str
    rule_id: str
    title: str
    reason: str
    risk: RiskLevel
    evidence_level: EvidenceLevel
    applicability: ApplicabilityState
    limitation: str


class ApiError(StrictModel):
    code: str
    user_message: str
    developer_detail: str = ""
    retryable: bool = False


class ApiResponse(StrictModel):
    success: bool
    data: Any = None
    error: ApiError | None = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))


class JobStatus(StrictModel):
    job_id: str
    state: JobState
    progress: int = Field(ge=0, le=100)
    message: str
    result: Any = None
    error: str | None = None
