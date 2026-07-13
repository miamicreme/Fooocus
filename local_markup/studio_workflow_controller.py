from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from local_markup.ai_studio_agent_v2 import AgentPlan, build_agent_plan
from local_markup.engine_hardware_profiles import HardwareProfile, profile_summary, select_hardware_profile
from local_markup.engine_queue_contract import EngineJobKind, new_job_id
from local_markup.local_fooocus_adapter import LocalDryRunFooocusAdapter, LocalFooocusAdapter
from local_markup.studio_adapter_contract import AdapterJobStatus, AdapterResult, ImageStudioJob, ReferenceImage
from local_markup.studio_adapter_mappings import build_face_reference_job, build_image_prompt_job, build_inpaint_job
from local_markup.studio_downloads import latest_downloadable_result, write_result_manifest
from local_markup.studio_generation_history import add_adapter_result_to_history
from local_markup.studio_history import StudioHistoryStore, load_history, save_history


REFERENCE_PREFIX = "studio_reference"
_LIVE_ADAPTER = LocalFooocusAdapter()
_ACTIVE_JOB_ID = ""
_ACTIVE_JOB_LOCK = threading.Lock()


@dataclass(frozen=True)
class StudioWorkflowRun:
    plan: AgentPlan
    job: ImageStudioJob
    adapter_result: AdapterResult
    hardware_profile: HardwareProfile
    history: StudioHistoryStore
    mapping_notes: List[str]

    def adapter_markdown(self) -> str:
        reference_lines = [f"- {item.role}: `{item.path or item.name}`" for item in self.job.references]
        if not reference_lines:
            reference_lines = ["- No references needed for this first shot."]
        notes = "\n".join([f"- {note}" for note in self.mapping_notes])
        return (
            "## Studio engine job\n\n"
            f"**Workflow:** {self.plan.tool}\n\n"
            f"**Fooocus area:** {self.plan.fooocus_tab}\n\n"
            f"**Hardware recommendation:** {profile_summary(self.hardware_profile)}\n\n"
            f"### References\n{chr(10).join(reference_lines)}\n\n"
            f"### Why this setup\n{notes or '- Standard text-to-image setup.'}"
        )

    def history_markdown(self) -> str:
        return history_markdown(self.history)


@dataclass(frozen=True)
class StudioGenerationRun:
    workflow_run: StudioWorkflowRun
    result: AdapterResult
    output_paths: List[str]
    manifest_path: str

    def status_markdown(self) -> str:
        latest = self.result.latest_output_path or "No image returned yet."
        return (
            f"## Generation status: {self.result.status.value}\n\n"
            f"**Current step:** {self.result.message}\n\n"
            f"**Progress:** {self.result.progress_percent:.0f}%\n\n"
            f"**Job ID:** `{self.result.job_id or 'none'}`\n\n"
            f"**Last result:** `{latest}`"
        )


def history_markdown(store: StudioHistoryStore) -> str:
    rows = []
    for item in store.latest(limit=10):
        output_count = item.metadata.get("output_count", str(len(item.image_paths)))
        rows.append(
            f"- `{item.workflow}` job `{item.item_id}` — {output_count} output(s), "
            f"status `{item.metadata.get('adapter_status', 'unknown')}`."
        )
    return "## Local Session History\n\n" + ("\n".join(rows) if rows else "No session history yet.")


def _set_active_job(job_id: str) -> None:
    global _ACTIVE_JOB_ID
    with _ACTIVE_JOB_LOCK:
        _ACTIVE_JOB_ID = job_id


def _clear_active_job(job_id: str) -> None:
    global _ACTIVE_JOB_ID
    with _ACTIVE_JOB_LOCK:
        if _ACTIVE_JOB_ID == job_id:
            _ACTIVE_JOB_ID = ""


def current_active_job_id() -> str:
    with _ACTIVE_JOB_LOCK:
        return _ACTIVE_JOB_ID


def reference_names_from_count(image_count: int) -> List[str]:
    return [f"{REFERENCE_PREFIX}_{index + 1}" for index in range(max(0, image_count))]


def references_from_count(image_count: int, role: str = "reference") -> List[ReferenceImage]:
    return [ReferenceImage(name=name, path=name, role=role) for name in reference_names_from_count(image_count)]


def kind_for_feature(feature_key: str) -> EngineJobKind:
    if feature_key in {"inpaint", "auto_mask_sam", "auto_mask_u2net"}:
        return EngineJobKind.INPAINT
    if feature_key in {"upscale", "variation"}:
        return EngineJobKind.UPSCALE
    if feature_key == "enhance":
        return EngineJobKind.ENHANCE
    if feature_key in {"image_prompt", "face_reference", "pyracanny", "cpds", "describe"}:
        return EngineJobKind.IMAGE_PROMPT
    return EngineJobKind.TEXT_TO_IMAGE


def _default_settings() -> dict[str, str]:
    return {"performance": "Speed", "image_number": "1", "aspect_ratio": "1024x1024"}


def build_job_from_plan(plan: AgentPlan, image_count: int) -> tuple[ImageStudioJob, List[str]]:
    feature_key = plan.feature.key
    refs = reference_names_from_count(image_count)

    if feature_key == "face_reference" and refs:
        mapping = build_face_reference_job(plan.user_goal, plan.primary_prompt, plan.negative_prompt, refs[0])
        job = mapping.job
        return ImageStudioJob(
            goal=job.goal,
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            kind=job.kind,
            references=job.references,
            width=job.width,
            height=job.height,
            seed=job.seed,
            settings=_default_settings(),
            metadata=job.metadata,
        ), [note.note for note in mapping.notes]

    if feature_key in {"image_prompt", "pyracanny", "cpds", "variation", "describe"} and refs:
        mapping = build_image_prompt_job(plan.user_goal, plan.primary_prompt, plan.negative_prompt, refs)
        metadata = dict(mapping.job.metadata)
        metadata["studio_feature"] = feature_key
        job = ImageStudioJob(
            goal=mapping.job.goal,
            prompt=mapping.job.prompt,
            negative_prompt=mapping.job.negative_prompt,
            kind=mapping.job.kind,
            references=mapping.job.references,
            width=mapping.job.width,
            height=mapping.job.height,
            seed=mapping.job.seed,
            settings=_default_settings(),
            metadata=metadata,
        )
        return job, [note.note for note in mapping.notes]

    if feature_key in {"inpaint", "auto_mask_sam", "auto_mask_u2net"}:
        source = refs[0] if refs else "source_image_required"
        mask = refs[1] if len(refs) > 1 else "mask_required"
        mapping = build_inpaint_job(plan.user_goal, plan.primary_prompt, plan.negative_prompt, source, mask)
        job = mapping.job
        return ImageStudioJob(
            goal=job.goal,
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            kind=job.kind,
            references=job.references,
            width=job.width,
            height=job.height,
            seed=job.seed,
            settings=_default_settings(),
            metadata=job.metadata,
        ), [note.note for note in mapping.notes]

    job = ImageStudioJob(
        goal=plan.user_goal,
        prompt=plan.primary_prompt,
        negative_prompt=plan.negative_prompt,
        kind=kind_for_feature(feature_key),
        references=references_from_count(image_count),
        settings=_default_settings(),
        metadata={"fooocus_area": plan.fooocus_tab, "studio_feature": feature_key},
    )
    return job, [f"Use the `{feature_key}` Studio plan as a `{job.kind.value}` Fooocus job."]


def image_path_from_gradio_value(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("path", "name", "orig_name"):
            maybe_path = value.get(key)
            if isinstance(maybe_path, str):
                return maybe_path
    return None


def references_from_uploaded_images(images: list[object], job: ImageStudioJob) -> list[ReferenceImage]:
    paths = [image_path_from_gradio_value(value) for value in images]
    paths = [path for path in paths if path]
    references: list[ReferenceImage] = []
    for index, path in enumerate(paths):
        role = "reference"
        if job.kind == EngineJobKind.INPAINT:
            role = "inpaint_source" if index == 0 else "inpaint_mask"
        elif job.metadata.get("reference_mode") == "face_reference" and index == 0:
            role = "face_reference"
        elif index == 0:
            role = "primary_reference"
        references.append(ReferenceImage(name=Path(path).name, path=path, role=role))
    return references


def job_with_actual_references(job: ImageStudioJob, uploaded_images: list[object]) -> ImageStudioJob:
    references = references_from_uploaded_images(uploaded_images, job)
    if not references:
        return job
    return ImageStudioJob(
        goal=job.goal,
        prompt=job.prompt,
        negative_prompt=job.negative_prompt,
        kind=job.kind,
        references=references,
        width=job.width,
        height=job.height,
        seed=job.seed,
        settings=job.settings,
        metadata=job.metadata,
    )


def job_with_prompt_overrides(job: ImageStudioJob, prompt_override: str, negative_prompt_override: str) -> ImageStudioJob:
    return ImageStudioJob(
        goal=job.goal,
        prompt=(prompt_override or job.prompt).strip(),
        negative_prompt=(negative_prompt_override or job.negative_prompt).strip(),
        kind=job.kind,
        references=job.references,
        width=job.width,
        height=job.height,
        seed=job.seed,
        settings=job.settings,
        metadata=job.metadata,
    )


def run_studio_workflow(
    goal: str,
    image_count: int = 0,
    wants_identity: bool = True,
    wants_exact_edit: bool = False,
    wants_bundle: bool = False,
    vram_gb: int = 6,
    existing_history: Optional[StudioHistoryStore] = None,
) -> StudioWorkflowRun:
    plan = build_agent_plan(goal, image_count, wants_identity, wants_exact_edit, wants_bundle)
    job, mapping_notes = build_job_from_plan(plan, image_count)
    hardware_profile = select_hardware_profile(vram_gb)
    adapter_result = LocalDryRunFooocusAdapter().submit(job)
    return StudioWorkflowRun(
        plan=plan,
        job=job,
        adapter_result=adapter_result,
        hardware_profile=hardware_profile,
        history=existing_history or StudioHistoryStore(),
        mapping_notes=mapping_notes,
    )


def _submit_job(workflow_run: StudioWorkflowRun, job: ImageStudioJob, history: StudioHistoryStore) -> StudioGenerationRun:
    job_id = new_job_id()
    _set_active_job(job_id)
    try:
        result = _LIVE_ADAPTER.submit(job, job_id=job_id)
    finally:
        _clear_active_job(job_id)
    updated_history = add_adapter_result_to_history(history, job, result, image_paths=result.output_paths)
    save_history(updated_history)
    completed_run = StudioWorkflowRun(
        plan=workflow_run.plan,
        job=job,
        adapter_result=result,
        hardware_profile=workflow_run.hardware_profile,
        history=updated_history,
        mapping_notes=workflow_run.mapping_notes,
    )
    manifest_path = write_result_manifest(result.output_paths, result.message)
    return StudioGenerationRun(completed_run, result, list(result.output_paths), manifest_path)


def submit_generation_run(
    goal: str,
    image_1,
    image_2,
    image_3,
    wants_identity: bool,
    wants_exact_edit: bool,
    wants_bundle: bool,
    vram_gb: int = 6,
    prompt_override: str = "",
    negative_prompt_override: str = "",
) -> StudioGenerationRun:
    uploaded_images = [image_1, image_2, image_3]
    image_count = sum(image_path_from_gradio_value(item) is not None for item in uploaded_images)
    history = load_history()
    workflow_run = run_studio_workflow(
        goal, image_count, wants_identity, wants_exact_edit, wants_bundle,
        vram_gb=vram_gb, existing_history=history,
    )
    job = job_with_actual_references(workflow_run.job, uploaded_images)
    job = job_with_prompt_overrides(job, prompt_override, negative_prompt_override)
    return _submit_job(workflow_run, job, history)


def submit_enhancement_run(latest_path: str, prompt: str = "", negative_prompt: str = "", vram_gb: int = 6) -> StudioGenerationRun:
    if not latest_path or not Path(latest_path).is_file():
        raise ValueError("Generate or select an existing image before using Enhance.")
    history = load_history()
    plan = build_agent_plan(prompt or "Enhance the selected image", 1, True, False, False)
    job = ImageStudioJob(
        goal="Enhance selected Studio result",
        prompt=(prompt or "enhance detail, preserve composition and identity").strip(),
        negative_prompt=(negative_prompt or "artifacts, distortion, identity drift").strip(),
        kind=EngineJobKind.ENHANCE,
        references=[ReferenceImage(name=Path(latest_path).name, path=latest_path, role="enhance_source")],
        settings=_default_settings(),
        metadata={"fooocus_area": "Enhance", "studio_feature": "enhance"},
    )
    workflow_run = StudioWorkflowRun(
        plan=plan,
        job=job,
        adapter_result=AdapterResult(status=AdapterJobStatus.ACCEPTED, message="Enhance job prepared."),
        hardware_profile=select_hardware_profile(vram_gb),
        history=history,
        mapping_notes=["Enhance the selected image through the stable Studio engine endpoint."],
    )
    return _submit_job(workflow_run, job, history)


def build_studio_workflow_outputs(
    goal: str,
    image_1,
    image_2,
    image_3,
    wants_identity: bool,
    wants_exact_edit: bool,
    wants_bundle: bool,
    vram_gb: int = 6,
) -> tuple[str, str, str, str, str, str, str, str, str]:
    image_count = sum(item is not None for item in [image_1, image_2, image_3])
    run = run_studio_workflow(goal, image_count, wants_identity, wants_exact_edit, wants_bundle, vram_gb=vram_gb)
    shot_list = "\n\n".join([f"Shot {index + 1}: {prompt}" for index, prompt in enumerate(run.plan.shot_prompts)])
    return (
        run.plan.as_markdown(), run.plan.primary_prompt, run.plan.negative_prompt,
        run.plan.tool, run.plan.fooocus_tab, shot_list, run.plan.handoff_recipe,
        run.adapter_markdown(), run.history_markdown(),
    )


def _generation_outputs(run: StudioGenerationRun) -> tuple[str, list[str], Optional[str], str, str, str, str]:
    downloadable = latest_downloadable_result(run.output_paths) or run.manifest_path
    latest_path = run.result.latest_output_path or ""
    return (
        run.status_markdown(), run.output_paths, downloadable, latest_path,
        run.workflow_run.adapter_markdown(), run.workflow_run.history_markdown(),
        run.result.job_id or "",
    )


def submit_studio_generation(
    goal: str,
    image_1,
    image_2,
    image_3,
    wants_identity: bool,
    wants_exact_edit: bool,
    wants_bundle: bool,
    vram_gb: int,
    prompt_override: str,
    negative_prompt_override: str,
):
    return _generation_outputs(submit_generation_run(
        goal, image_1, image_2, image_3, wants_identity, wants_exact_edit,
        wants_bundle, vram_gb, prompt_override, negative_prompt_override,
    ))


def submit_studio_enhancement(latest_path: str, prompt: str, negative_prompt: str, vram_gb: int):
    try:
        return _generation_outputs(submit_enhancement_run(latest_path, prompt, negative_prompt, vram_gb))
    except Exception as exc:
        message = f"## Enhancement failed\n\n{type(exc).__name__}: {exc}"
        return message, [], None, latest_path or "", "", history_markdown(load_history()), ""


def poll_generation_status(job_id: str) -> str:
    if not job_id:
        return "## Generation status\n\nNo active job selected."
    result = _LIVE_ADAPTER.get_status(job_id)
    return f"## Generation status: {result.status.value}\n\n{result.message}"


def load_generation_results() -> tuple[list[str], Optional[str], str, str]:
    history = load_history()
    outputs: list[str] = []
    for item in history.latest(limit=20):
        outputs.extend(item.image_paths or ([item.image_path] if item.image_path else []))
    downloadable = latest_downloadable_result(outputs)
    latest_path = outputs[0] if outputs else ""
    return outputs, downloadable, latest_path, history_markdown(history)


def stop_studio_generation() -> str:
    job_id = current_active_job_id()
    if not job_id:
        return "## Stop\n\nNo Studio generation is currently active."
    result = _LIVE_ADAPTER.cancel(job_id)
    return f"## Stop: {result.status.value}\n\n{result.message}"


def use_latest_result_as_reference(latest_path: str):
    if latest_path and Path(latest_path).is_file():
        return latest_path, f"## Reference ready\n\nLoaded `{latest_path}` into Reference 1."
    return None, "## Reference unavailable\n\nGenerate or select an existing image first."


def enhance_latest_result(latest_path: str) -> str:
    if latest_path and Path(latest_path).is_file():
        return f"Ready to enhance `{latest_path}` through the stable Studio engine endpoint."
    return "Generate or select an image before using Enhance."
