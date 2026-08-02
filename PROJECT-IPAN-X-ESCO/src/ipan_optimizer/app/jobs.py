from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any
from uuid import uuid4

from ipan_optimizer.domain.models import JobState, JobStatus

ProgressReporter = Callable[[int, str], None]
ProgressWork = Callable[[ProgressReporter], Any]


class JobManager:
    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ipan-job",
        )
        self._jobs: dict[str, JobStatus] = {}
        self._lock = Lock()

    def submit(self, message: str, work: Callable[[], Any]) -> JobStatus:
        return self.submit_progress(message, lambda report: work())

    def submit_progress(self, message: str, work: ProgressWork) -> JobStatus:
        job_id = str(uuid4())
        status = JobStatus(
            job_id=job_id,
            state=JobState.PENDING,
            progress=0,
            message=message,
        )
        with self._lock:
            self._jobs[job_id] = status

        def report(progress: int, update_message: str) -> None:
            with self._lock:
                current = self._jobs[job_id]
                current.progress = max(current.progress, min(progress, 99))
                current.message = update_message

        def runner() -> None:
            with self._lock:
                status.state = JobState.RUNNING
                status.progress = 1
            try:
                result = work(report)
                with self._lock:
                    if status.state is JobState.CANCELLING:
                        status.state = JobState.CANCELLED
                        status.progress = 100
                        status.message = "Operasi dibatalkan pada batas aman."
                    else:
                        status.result = result
                        status.progress = 100
                        status.state = JobState.SUCCEEDED
                        status.message = "Operasi selesai dan hasil tersedia."
            except Exception as exc:
                with self._lock:
                    status.state = JobState.FAILED
                    status.progress = 100
                    status.error = str(exc)
                    status.message = "Operasi gagal dengan aman."

        self._executor.submit(runner)
        return status.model_copy(deep=True)

    def get(self, job_id: str) -> JobStatus:
        with self._lock:
            status = self._jobs.get(job_id)
            if status is None:
                raise KeyError("Job tidak ditemukan.")
            return status.model_copy(deep=True)

    def cancel(self, job_id: str) -> JobStatus:
        with self._lock:
            status = self._jobs.get(job_id)
            if status is None:
                raise KeyError("Job tidak ditemukan.")
            if status.state in {JobState.PENDING, JobState.RUNNING}:
                status.state = JobState.CANCELLING
                status.message = "Menunggu batas pembatalan yang aman."
            return status.model_copy(deep=True)
