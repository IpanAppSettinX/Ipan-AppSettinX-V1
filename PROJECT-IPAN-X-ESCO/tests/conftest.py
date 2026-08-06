from __future__ import annotations

from pathlib import Path

import pytest

from ipan_optimizer.adapters.fake import FakeWindowsBackend
from ipan_optimizer.app.api import ApiBridge
from ipan_optimizer.app.service import OptimizerService
from ipan_optimizer.core.journal import RecoveryJournal
from ipan_optimizer.core.transactions import TransactionManager


@pytest.fixture(autouse=True)
def _no_elevation(monkeypatch) -> None:
    """Never trigger a UAC prompt or host elevation during the test run."""
    monkeypatch.setenv("IPAN_OPTIMIZER_NO_ELEVATION", "1")


@pytest.fixture
def backend() -> FakeWindowsBackend:
    return FakeWindowsBackend()


@pytest.fixture
def service(tmp_path: Path, backend: FakeWindowsBackend) -> OptimizerService:
    manager = TransactionManager(backend, RecoveryJournal(tmp_path / "journal.jsonl"))
    return OptimizerService(backend, manager, tmp_path / "exports")


@pytest.fixture
def bridge(service: OptimizerService) -> ApiBridge:
    return ApiBridge(service)
