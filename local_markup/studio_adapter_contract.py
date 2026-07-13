from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Protocol

from local_markup.engine_queue_contract import EngineJobKind, EngineJobRequest


class AdapterJobStatus(str, Enum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MANUAL_HANDOFF = "manual_handoff"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReferenceImage:
    name: str
    path: Optional[str] = None
    role: str = "reference"


@dataclass(frozen=True)
class ImageStudioJob:
    goal: str
    prompt: str
    negative_prompt: str
    kind: EngineJobKind
    references: List[ReferenceImage] = field(default_factory=list)
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    settings: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_engine_request(self) -> EngineJobRequest:
        metadata = dict(self.metadata)
        for key, value in self.settings.items():
            metadata[f"setting_{key}"] = str(value)
        return EngineJobRequest(
            kind=self.kind,
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            seed=self.seed,
            width=self.width,
            height=self.height,
            references=[item.path or item.name for item in self.references],
            metadata=metadata,
        )

    def normalized_payload(self) -> dict[str, object]:
        return {
            "goal": self.goal,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "workflow": self.kind.value,
            "references": [item.path or item.name for item in self.references],
            "settings": {
                "width": self.width,
                "height": self.height,
                "seed": self.seed if self.seed is not None else -1,
                **self.settings,
            },
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdapterResult:
    status: AdapterJobStatus
    message: str
    job_id: Optional[str] = None
    handoff_steps: List[str] = field(default_factory=list)
    output_paths: List[str] = field(default_factory=list)
    progress_percent: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def latest_output_path(self) -> Optional[str]:
        if not self.output_paths:
            return None
        return self.output_paths[-1]


class ProviderAdapter(Protocol):
    name: str

    def submit(self, job: ImageStudioJob) -> AdapterResult:
        ...

    def get_status(self, job_id: str) -> AdapterResult:
        ...

    def get_results(self, job_id: str) -> AdapterResult:
        ...

    def cancel(self, job_id: str) -> AdapterResult:
        ...


class ManualHandoffAdapter:
    name = "manual_handoff"

    def submit(self, job: ImageStudioJob) -> AdapterResult:
        steps = [
            "Open Fooocus in the browser.",
            f"Choose workflow: {job.kind.value}.",
            "Copy the prompt into the prompt box.",
            "Copy the negative prompt into the negative prompt box.",
            "Upload the listed reference images if any.",
            "Generate one candidate first, then review before continuing.",
        ]
        return AdapterResult(
            status=AdapterJobStatus.MANUAL_HANDOFF,
            message="Manual Fooocus handoff created. No automatic generation was started.",
            handoff_steps=steps,
        )

    def get_status(self, job_id: str) -> AdapterResult:
        return AdapterResult(status=AdapterJobStatus.MANUAL_HANDOFF, message="Manual handoff jobs do not expose live status.", job_id=job_id)

    def get_results(self, job_id: str) -> AdapterResult:
        return AdapterResult(status=AdapterJobStatus.MANUAL_HANDOFF, message="Manual handoff jobs do not expose automatic results.", job_id=job_id)

    def cancel(self, job_id: str) -> AdapterResult:
        return AdapterResult(status=AdapterJobStatus.CANCELLED, message="Manual handoff cancelled.", job_id=job_id)
