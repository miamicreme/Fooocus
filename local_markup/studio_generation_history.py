from __future__ import annotations

from typing import Optional

from local_markup.studio_adapter_contract import AdapterResult, ImageStudioJob
from local_markup.studio_history import StudioHistoryItem, StudioHistoryStore


def history_item_from_adapter_result(
    job: ImageStudioJob,
    result: AdapterResult,
    image_path: Optional[str] = None,
    rating: Optional[int] = None,
    notes: str = "",
) -> StudioHistoryItem:
    item_id = result.job_id or f"manual-{abs(hash((job.goal, job.prompt, job.kind.value))) }"
    metadata = dict(job.metadata)
    metadata.update(
        {
            "adapter_status": result.status.value,
            "adapter_message": result.message,
            "reference_count": str(len(job.references)),
        }
    )
    return StudioHistoryItem(
        item_id=item_id,
        prompt=job.prompt,
        negative_prompt=job.negative_prompt,
        workflow=job.kind.value,
        image_path=image_path,
        seed=job.seed,
        rating=rating,
        notes=notes,
        metadata=metadata,
    )


def add_adapter_result_to_history(
    store: StudioHistoryStore,
    job: ImageStudioJob,
    result: AdapterResult,
    image_path: Optional[str] = None,
    rating: Optional[int] = None,
    notes: str = "",
) -> StudioHistoryStore:
    return store.add(
        history_item_from_adapter_result(
            job=job,
            result=result,
            image_path=image_path,
            rating=rating,
            notes=notes,
        )
    )
