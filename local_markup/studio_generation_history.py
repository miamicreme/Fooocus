from __future__ import annotations

from hashlib import sha256
from typing import Optional

from local_markup.studio_adapter_contract import AdapterResult, ImageStudioJob
from local_markup.studio_history import StudioHistoryItem, StudioHistoryStore



def manual_history_id(job: ImageStudioJob) -> str:
    raw = "|".join([job.goal, job.prompt, job.negative_prompt, job.kind.value])
    digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"manual-{digest}"



def reference_metadata(job: ImageStudioJob) -> dict[str, str]:
    metadata: dict[str, str] = {"reference_count": str(len(job.references))}
    for index, reference in enumerate(job.references, start=1):
        prefix = f"reference_{index}"
        metadata[f"{prefix}_name"] = reference.name
        metadata[f"{prefix}_path"] = reference.path or ""
        metadata[f"{prefix}_role"] = reference.role
    return metadata



def history_item_from_adapter_result(
    job: ImageStudioJob,
    result: AdapterResult,
    image_path: Optional[str] = None,
    image_paths: Optional[list[str]] = None,
    rating: Optional[int] = None,
    notes: str = "",
) -> StudioHistoryItem:
    item_id = result.job_id or manual_history_id(job)
    output_paths = image_paths if image_paths is not None else list(result.output_paths)
    first_image = image_path or (output_paths[0] if output_paths else None)
    metadata = dict(job.metadata)
    metadata.update(reference_metadata(job))
    metadata.update(
        {
            "adapter_status": result.status.value,
            "adapter_message": result.message,
            "output_count": str(len(output_paths)),
        }
    )
    metadata.update(result.metadata)
    return StudioHistoryItem(
        item_id=item_id,
        prompt=job.prompt,
        negative_prompt=job.negative_prompt,
        workflow=job.kind.value,
        image_path=first_image,
        image_paths=output_paths,
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
    image_paths: Optional[list[str]] = None,
    rating: Optional[int] = None,
    notes: str = "",
) -> StudioHistoryStore:
    return store.add(
        history_item_from_adapter_result(
            job=job,
            result=result,
            image_path=image_path,
            image_paths=image_paths,
            rating=rating,
            notes=notes,
        )
    )
