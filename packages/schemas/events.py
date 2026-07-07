"""Progress event schemas for API, worker, and UI communication."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .assets import AssetReference

ProgressEventType = Literal[
    "job_created",
    "job_queued",
    "worker_assigned",
    "model_loading",
    "input_preparing",
    "sampling_started",
    "preview",
    "postprocessing",
    "output_saved",
    "job_succeeded",
    "job_failed",
    "job_cancelled",
]


class ProgressEvent(BaseModel):
    """Realtime or persisted event emitted during generation."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    type: ProgressEventType
    percent: int | None = Field(default=None, ge=0, le=100)
    message: str = ""
    preview: AssetReference | None = None
    worker_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
