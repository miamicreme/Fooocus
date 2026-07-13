from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Callable, Iterable, List, Optional

from local_markup.engine_queue_contract import EngineJobRecord, EngineJobStatus, create_queued_record, transition_job
from local_markup.studio_adapter_contract import AdapterJobStatus, AdapterResult, ImageStudioJob


STUDIO_JOB_DIR = Path("logs") / "studio" / "jobs"
FOOOCUS_OUTPUT_DIR = Path("outputs")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class LocalFooocusSubmission:
    record: EngineJobRecord
    normalized_job_path: Path
    output_paths: List[str]
    validation_notes: List[str]


class LocalDryRunFooocusAdapter:
    name = "local_dry_run"

    def submit(self, job: ImageStudioJob) -> AdapterResult:
        submission = self.prepare_submission(job)
        return AdapterResult(
            status=AdapterJobStatus.ACCEPTED,
            message="Dry-run local Fooocus job accepted. Active generation was not started.",
            job_id=submission.record.job_id,
            handoff_steps=submission.validation_notes,
        )

    def prepare_submission(self, job: ImageStudioJob) -> LocalFooocusSubmission:
        request = job.to_engine_request()
        record = create_queued_record(request)
        notes = [
            f"Prepared job kind: {request.kind.value}",
            f"Prompt length: {len(request.prompt)}",
            f"Reference count: {len(request.references)}",
            "No active Fooocus worker call was made.",
        ]
        return LocalFooocusSubmission(record=record, normalized_job_path=Path(""), output_paths=[], validation_notes=notes)


class LocalFooocusAdapter:
    """Local Studio-to-Fooocus adapter.

    This adapter owns the top-shelf Studio contract: Studio builds one normalized
    job, confirms the local Fooocus engine is reachable, submits through an
    injectable generation callable when available, and always records the job and
    discovered output files. The callable hook keeps the contract testable while
    the live Fooocus Gradio surface remains a separate engine process.
    """

    name = "local_fooocus"

    def __init__(
        self,
        engine_host: str = "127.0.0.1",
        engine_port: int = 7865,
        output_dir: Path | str = FOOOCUS_OUTPUT_DIR,
        job_dir: Path | str = STUDIO_JOB_DIR,
        generate_callable: Optional[Callable[[dict[str, object]], Iterable[str] | str | None]] = None,
    ) -> None:
        self.engine_host = engine_host
        self.engine_port = engine_port
        self.output_dir = Path(output_dir)
        self.job_dir = Path(job_dir)
        self.generate_callable = generate_callable
        self._records: dict[str, EngineJobRecord] = {}

    @property
    def engine_url(self) -> str:
        return f"http://{self.engine_host}:{self.engine_port}"

    def is_engine_running(self, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((self.engine_host, self.engine_port), timeout=timeout):
                return True
        except OSError:
            return False

    def normalize_job(self, job: ImageStudioJob) -> dict[str, object]:
        payload = job.normalized_payload()
        payload["engine_url"] = self.engine_url
        payload["adapter"] = self.name
        return payload

    def write_normalized_job(self, job: ImageStudioJob, job_id: str) -> Path:
        self.job_dir.mkdir(parents=True, exist_ok=True)
        path = self.job_dir / f"{job_id}.json"
        payload = self.normalize_job(job)
        payload["job_id"] = job_id
        payload["created_at"] = time()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def discover_recent_outputs(self, since_timestamp: float) -> List[str]:
        if not self.output_dir.exists():
            return []
        candidates: list[Path] = []
        for path in self.output_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            try:
                if path.stat().st_mtime >= since_timestamp:
                    candidates.append(path)
            except OSError:
                continue
        return [str(path) for path in sorted(candidates, key=lambda item: item.stat().st_mtime)]

    def submit(self, job: ImageStudioJob) -> AdapterResult:
        request = job.to_engine_request()
        queued = create_queued_record(request)
        job_path = self.write_normalized_job(job, queued.job_id)
        notes = [
            f"Normalized Studio job saved: {job_path}",
            f"Engine URL checked: {self.engine_url}",
            f"Workflow: {request.kind.value}",
            f"Reference count: {len(request.references)}",
        ]

        if not self.is_engine_running():
            failed = transition_job(queued, EngineJobStatus.FAILED, error="Fooocus engine is not reachable on the local port.")
            self._records[failed.job_id] = failed
            return AdapterResult(
                status=AdapterJobStatus.FAILED,
                message="Generation failed before submission. Engine status: unavailable. Reason: connection refused on local engine. Start Fooocus engine and retry.",
                job_id=failed.job_id,
                handoff_steps=notes,
                metadata={"normalized_job_path": str(job_path), "engine_url": self.engine_url},
            )

        running = transition_job(queued, EngineJobStatus.RUNNING)
        self._records[running.job_id] = running
        started_at = time()

        try:
            output_paths = self._submit_to_engine(job, running.job_id)
            if not output_paths:
                output_paths = self.discover_recent_outputs(started_at)
            completed = transition_job(running, EngineJobStatus.SUCCEEDED, outputs=output_paths)
            self._records[completed.job_id] = completed
            if output_paths:
                return AdapterResult(
                    status=AdapterJobStatus.COMPLETED,
                    message=f"Generation completed. {len(output_paths)} output image(s) returned to Studio.",
                    job_id=completed.job_id,
                    handoff_steps=notes,
                    output_paths=output_paths,
                    progress_percent=100.0,
                    metadata={"normalized_job_path": str(job_path), "engine_url": self.engine_url},
                )
            return AdapterResult(
                status=AdapterJobStatus.FAILED,
                message="Engine was reachable, but no output image was returned or discovered. Check the Fooocus engine log.",
                job_id=completed.job_id,
                handoff_steps=notes,
                output_paths=[],
                metadata={"normalized_job_path": str(job_path), "engine_url": self.engine_url},
            )
        except Exception as exc:  # pragma: no cover - message path is tested through public result contract.
            failed = transition_job(running, EngineJobStatus.FAILED, error=str(exc))
            self._records[failed.job_id] = failed
            return AdapterResult(
                status=AdapterJobStatus.FAILED,
                message=f"Generation failed. Engine status: reachable. Reason: {type(exc).__name__}: {exc}",
                job_id=failed.job_id,
                handoff_steps=notes,
                metadata={"normalized_job_path": str(job_path), "engine_url": self.engine_url},
            )

    def _submit_to_engine(self, job: ImageStudioJob, job_id: str) -> List[str]:
        if self.generate_callable is not None:
            result = self.generate_callable(self.normalize_job(job))
            if result is None:
                return []
            if isinstance(result, str):
                return [result]
            return [str(item) for item in result]

        # The current Fooocus Gradio app is a full interactive UI, not a small
        # stable REST endpoint. Keep this method explicit so Studio fails cleanly
        # instead of pretending a browser-copy workflow is automatic.
        try:
            from gradio_client import Client  # type: ignore
        except Exception as exc:
            raise RuntimeError("gradio_client is not installed, so Studio cannot call the local engine API yet.") from exc

        client = Client(self.engine_url)
        api_info = client.view_api(return_format="dict")
        api_text = json.dumps(api_info, default=str).lower()
        if "generate" not in api_text:
            raise RuntimeError("Fooocus is running, but it does not expose a stable generate API endpoint for Studio yet.")
        raise RuntimeError("Fooocus generate endpoint was detected, but the current engine UI requires its full Gradio control payload before automatic generation can be safely enabled.")

    def get_status(self, job_id: str) -> AdapterResult:
        record = self._records.get(job_id)
        if record is None:
            return AdapterResult(status=AdapterJobStatus.FAILED, message="Unknown local Fooocus job id.", job_id=job_id)
        status_map = {
            EngineJobStatus.QUEUED: AdapterJobStatus.ACCEPTED,
            EngineJobStatus.RUNNING: AdapterJobStatus.RUNNING,
            EngineJobStatus.SUCCEEDED: AdapterJobStatus.COMPLETED,
            EngineJobStatus.FAILED: AdapterJobStatus.FAILED,
            EngineJobStatus.CANCELED: AdapterJobStatus.CANCELLED,
        }
        return AdapterResult(status=status_map[record.status], message=record.error or record.status.value, job_id=job_id, output_paths=record.outputs)

    def get_results(self, job_id: str) -> AdapterResult:
        status = self.get_status(job_id)
        if status.status == AdapterJobStatus.COMPLETED:
            return status
        return AdapterResult(status=status.status, message="No completed results are available for this job yet.", job_id=job_id, output_paths=status.output_paths)

    def cancel(self, job_id: str) -> AdapterResult:
        record = self._records.get(job_id)
        if record is not None:
            self._records[job_id] = transition_job(record, EngineJobStatus.CANCELED, error="Cancelled from Studio.")
        return AdapterResult(status=AdapterJobStatus.CANCELLED, message="Stop requested from Studio. If Fooocus is already processing, use the engine stop control for hard cancellation.", job_id=job_id)
