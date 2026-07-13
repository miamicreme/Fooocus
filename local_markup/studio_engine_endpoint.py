from __future__ import annotations

import json
import random
import sys
import threading
import time
from pathlib import Path
from typing import Any

STUDIO_GENERATE_API = "studio_generate"
STUDIO_CANCEL_API = "studio_cancel"
STUDIO_HEALTH_API = "studio_health"
_ACTIVE_TASKS: dict[str, Any] = {}
_ACTIVE_TASKS_LOCK = threading.Lock()
_GENERATION_LOCK = threading.Lock()
_HOOK_INSTALLED = False


def _component_value(component: Any) -> Any:
    value = getattr(component, "value", None)
    return value() if callable(value) else value


def _load_rgb(path_value: str):
    import cv2

    path = Path(path_value)
    if not path.is_file():
        raise FileNotFoundError(f"Reference image does not exist: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Reference image could not be decoded: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _choose_uov_method(webui: Any, prefer_fast: bool = False) -> str:
    choices = list(getattr(webui.flags, "uov_list", []))
    lowered = [(choice, str(choice).casefold()) for choice in choices]
    if prefer_fast:
        for choice, text in lowered:
            if "upscale" in text and "fast" in text:
                return choice
    for choice, text in lowered:
        if "upscale" in text and "2x" in text and "fast" not in text:
            return choice
    for choice, text in lowered:
        if "upscale" in text:
            return choice
    raise RuntimeError("Fooocus does not expose an upscale method for Studio.")


def _parse_dimension(settings: dict[str, Any], name: str) -> int | None:
    value = settings.get(name)
    if value in (None, "", -1, "-1"):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _build_task(webui: Any, payload: dict[str, Any]):
    values = [_component_value(component) for component in webui.ctrls]
    overrides: dict[int, Any] = {}

    def set_value(component: Any, value: Any) -> None:
        overrides[id(component)] = value

    prompt = str(payload.get("prompt") or "").strip()
    negative_prompt = str(payload.get("negative_prompt") or "").strip()
    if not prompt and str(payload.get("workflow")) not in {"upscale", "enhance"}:
        raise ValueError("Studio generation requires a prompt.")

    settings = payload.get("settings") or {}
    if not isinstance(settings, dict):
        raise ValueError("Studio job settings must be an object.")
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    set_value(webui.prompt, prompt)
    set_value(webui.negative_prompt, negative_prompt)
    set_value(webui.image_number, max(1, int(settings.get("image_number", 1))))

    performance = settings.get("performance")
    if performance in webui.flags.Performance.values():
        set_value(webui.performance_selection, performance)

    seed = settings.get("seed", -1)
    try:
        seed = int(seed)
    except (TypeError, ValueError):
        seed = -1
    if seed < 0:
        seed = random.randint(webui.constants.MIN_SEED, webui.constants.MAX_SEED)
    set_value(webui.image_seed, seed)

    width = _parse_dimension(settings, "width")
    height = _parse_dimension(settings, "height")
    aspect_ratio = str(settings.get("aspect_ratio") or "")
    if (width is None or height is None) and "x" in aspect_ratio.lower():
        try:
            width_text, height_text = aspect_ratio.lower().split("x", 1)
            width = width or int(width_text.strip())
            height = height or int(height_text.strip())
        except ValueError:
            pass
    if width:
        set_value(webui.overwrite_width, width)
    if height:
        set_value(webui.overwrite_height, height)

    references = payload.get("references") or []
    if not isinstance(references, list):
        raise ValueError("Studio job references must be a list.")
    references = [str(item) for item in references if item]
    workflow = str(payload.get("workflow") or "text_to_image")

    if workflow == "image_prompt":
        if not references:
            raise ValueError("Image Prompt generation requires at least one reference image.")
        set_value(webui.input_image_checkbox, True)
        set_value(webui.current_tab, "ip")
        face_reference = metadata.get("reference_mode") == "face_reference"
        for index, path in enumerate(references[: len(webui.ip_images)]):
            set_value(webui.ip_images[index], _load_rgb(path))
            if face_reference and index == 0:
                set_value(webui.ip_types[index], webui.flags.cn_ip_face)
            else:
                set_value(webui.ip_types[index], webui.flags.default_ip)
            stop_at, weight = webui.flags.default_parameters[_component_value(webui.ip_types[index])]
            set_value(webui.ip_stops[index], stop_at)
            set_value(webui.ip_weights[index], weight)

    elif workflow == "inpaint":
        if len(references) < 2:
            raise ValueError("Inpaint generation requires a source image and mask image.")
        import numpy as np

        source = _load_rgb(references[0])
        mask_rgb = _load_rgb(references[1])
        mask_gray = np.mean(mask_rgb, axis=2).astype("uint8")
        mask_3 = np.repeat(mask_gray[:, :, None], 3, axis=2)
        set_value(webui.input_image_checkbox, True)
        set_value(webui.current_tab, "inpaint")
        set_value(webui.inpaint_input_image, {"image": source, "mask": mask_3})
        set_value(webui.inpaint_advanced_masking_checkbox, False)

    elif workflow == "upscale":
        if not references:
            raise ValueError("Upscale generation requires an input image.")
        set_value(webui.input_image_checkbox, True)
        set_value(webui.current_tab, "uov")
        set_value(webui.uov_input_image, _load_rgb(references[0]))
        set_value(webui.uov_method, _choose_uov_method(webui))

    elif workflow == "enhance":
        if not references:
            raise ValueError("Enhance generation requires an input image.")
        set_value(webui.input_image_checkbox, True)
        set_value(webui.current_tab, "enhance")
        set_value(webui.enhance_input_image, _load_rgb(references[0]))
        set_value(webui.enhance_checkbox, True)
        set_value(webui.enhance_uov_method, _choose_uov_method(webui))

    elif workflow != "text_to_image":
        raise ValueError(f"Unsupported Studio workflow: {workflow}")

    resolved = [overrides.get(id(component), default) for component, default in zip(webui.ctrls, values)]
    resolved.pop(0)  # currentTask state; mirrors webui.get_task().
    return webui.worker.AsyncTask(args=resolved)


def _coerce_paths(product: Any) -> list[str]:
    if product is None:
        return []
    if isinstance(product, str):
        return [product]
    if isinstance(product, (list, tuple)):
        return [str(item) for item in product if isinstance(item, (str, Path))]
    return []


def _studio_health(payload_json: str = "{}") -> dict[str, Any]:
    webui = sys.modules.get("webui")
    controls_ready = bool(webui is not None and getattr(webui, "ctrls", None))
    worker_ready = bool(webui is not None and getattr(getattr(webui, "worker", None), "async_tasks", None) is not None)
    api_ready = controls_ready and worker_ready
    return {
        "status": "ok" if api_ready else "failed",
        "message": "Studio engine endpoints are registered." if api_ready else "Fooocus web UI is not fully initialized.",
        "apis": [f"/{STUDIO_HEALTH_API}", f"/{STUDIO_GENERATE_API}", f"/{STUDIO_CANCEL_API}"],
        "controls_ready": controls_ready,
        "worker_ready": worker_ready,
        "active_job_count": len(_ACTIVE_TASKS),
    }


def _studio_generate(payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise ValueError("Studio request must be a JSON object.")
        job_id = str(payload.get("job_id") or "").strip()
        if not job_id:
            raise ValueError("Studio request is missing job_id.")
        webui = sys.modules.get("webui")
        if webui is None:
            raise RuntimeError("Fooocus web UI is not initialized.")

        with _GENERATION_LOCK:
            task = _build_task(webui, payload)
            with _ACTIVE_TASKS_LOCK:
                _ACTIVE_TASKS[job_id] = task
            webui.worker.async_tasks.append(task)
            deadline = time.monotonic() + 3600
            last_results: list[str] = []
            while time.monotonic() < deadline:
                if task.yields:
                    flag, product = task.yields.pop(0)
                    if flag in {"results", "finish"}:
                        paths = _coerce_paths(product)
                        if paths:
                            last_results = paths
                    if flag == "finish":
                        return {"status": "completed", "job_id": job_id, "output_paths": last_results}
                if task.last_stop == "stop" and not task.processing:
                    return {"status": "cancelled", "job_id": job_id, "message": "Generation cancelled from Studio.", "output_paths": last_results}
                time.sleep(0.05)
            task.last_stop = "stop"
            raise TimeoutError("Fooocus generation exceeded the one-hour Studio timeout.")
    except Exception as exc:
        return {"status": "failed", "message": f"{type(exc).__name__}: {exc}", "output_paths": []}
    finally:
        job_id = locals().get("job_id")
        if job_id:
            with _ACTIVE_TASKS_LOCK:
                _ACTIVE_TASKS.pop(job_id, None)


def _studio_cancel(payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
        job_id = str(payload.get("job_id") or "").strip()
        with _ACTIVE_TASKS_LOCK:
            task = _ACTIVE_TASKS.get(job_id)
        if task is None:
            return {"status": "not_found", "job_id": job_id, "message": "No active Studio job was found."}
        task.last_stop = "stop"
        if task.processing:
            import ldm_patched.modules.model_management as model_management

            model_management.interrupt_current_processing()
        return {"status": "cancelled", "job_id": job_id, "message": "Fooocus cancellation requested."}
    except Exception as exc:
        return {"status": "failed", "message": f"{type(exc).__name__}: {exc}"}


def _attach_endpoints(blocks: Any) -> None:
    if getattr(blocks, "_studio_engine_endpoints_attached", False):
        return
    import gradio as gr

    with blocks:
        health_input = gr.Textbox(visible=False)
        health_output = gr.JSON(visible=False)
        health_button = gr.Button(visible=False)
        health_button.click(
            _studio_health,
            inputs=health_input,
            outputs=health_output,
            api_name=STUDIO_HEALTH_API,
            queue=False,
        )

        generate_input = gr.Textbox(visible=False)
        generate_output = gr.JSON(visible=False)
        generate_button = gr.Button(visible=False)
        generate_button.click(
            _studio_generate,
            inputs=generate_input,
            outputs=generate_output,
            api_name=STUDIO_GENERATE_API,
            queue=True,
        )
        cancel_input = gr.Textbox(visible=False)
        cancel_output = gr.JSON(visible=False)
        cancel_button = gr.Button(visible=False)
        cancel_button.click(
            _studio_cancel,
            inputs=cancel_input,
            outputs=cancel_output,
            api_name=STUDIO_CANCEL_API,
            queue=False,
        )
    blocks._studio_engine_endpoints_attached = True


def install_studio_endpoint_launch_hook() -> None:
    global _HOOK_INSTALLED
    if _HOOK_INSTALLED:
        return
    import gradio as gr

    original_launch = gr.Blocks.launch

    def launch_with_studio_endpoints(self, *args, **kwargs):
        _attach_endpoints(self)
        return original_launch(self, *args, **kwargs)

    gr.Blocks.launch = launch_with_studio_endpoints
    _HOOK_INSTALLED = True
