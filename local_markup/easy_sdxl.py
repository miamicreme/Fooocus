from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional

from .ui_adapter_v2 import build_markup_ui_state


WORKFLOW_COPY = {
    "Generate New Image": {
        "tab": "Prompt only",
        "prompt_prefix": "Create a high quality SDXL image of",
        "steps": "30",
        "cfg": "4",
        "denoise": "n/a",
        "help": "Use this when you want a brand-new image. No input image is required.",
    },
    "Edit This Image": {
        "tab": "Inpaint or Outpaint",
        "prompt_prefix": "Replace only the masked area with",
        "steps": "30 / 15",
        "cfg": "4",
        "denoise": "0.75 to 1.0",
        "help": "Use this when you want to change part of an uploaded image. Draw a mask over the part to change.",
    },
    "Use Image as Reference": {
        "tab": "Image Prompt",
        "prompt_prefix": "Create a new image that keeps the reference style and subject, showing",
        "steps": "30",
        "cfg": "4",
        "denoise": "n/a",
        "help": "Use this when you want a new image inspired by an uploaded reference image.",
    },
    "Improve / Enhance": {
        "tab": "Enhance",
        "prompt_prefix": "Improve quality, sharpness, lighting, and professional finish while preserving",
        "steps": "30 / 15",
        "cfg": "4",
        "denoise": "0.35 to 0.6",
        "help": "Use this when the image is basically right and you only want it cleaner or sharper.",
    },
}


AREA_HINTS = {
    "Face": "face",
    "Glasses": "glasses",
    "Hair": "hair",
    "Shirt / Clothes": "shirt, clothes",
    "Background": "background",
    "Object": "object",
    "Whole Image": "selected area",
    "I will draw the mask": "selected area",
}


@dataclass
class EasySdxlPlan:
    workflow: str
    recommended_tab: str
    positive_prompt: str
    inpaint_prompt: str
    detection_prompt: str
    negative_prompt: str
    steps: str
    cfg: str
    denoise: str
    checklist: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def build_easy_sdxl_plan(
    workflow: str,
    area: str,
    user_instruction: str,
    image_context: Optional[str] = None,
) -> EasySdxlPlan:
    workflow = workflow if workflow in WORKFLOW_COPY else "Edit This Image"
    area = area if area in AREA_HINTS else "I will draw the mask"
    instruction = (user_instruction or "").strip()
    workflow_info = WORKFLOW_COPY[workflow]

    if not instruction:
        instruction = "describe the change you want"

    state = build_markup_ui_state(instruction, image_context=image_context)
    area_hint = AREA_HINTS[area]

    if workflow == "Generate New Image":
        positive = f"{workflow_info['prompt_prefix']} {instruction}, high quality, detailed, sharp, professional"
        inpaint_prompt = ""
        detection = ""
    elif workflow == "Use Image as Reference":
        positive = f"{workflow_info['prompt_prefix']} {instruction}, high quality, detailed, sharp, professional"
        inpaint_prompt = ""
        detection = area_hint
    elif workflow == "Improve / Enhance":
        positive = f"{workflow_info['prompt_prefix']} {instruction}, natural details, clean lighting, sharp focus"
        inpaint_prompt = state.inpaint_prompt
        detection = area_hint if area != "I will draw the mask" else state.detection_prompt
    else:
        positive = state.inpaint_prompt
        inpaint_prompt = state.inpaint_prompt
        detection = area_hint if area != "I will draw the mask" else state.detection_prompt

    checklist = (
        f"Recommended workflow: {workflow}\n"
        f"Best Fooocus tab: {workflow_info['tab']}\n"
        f"What it means: {workflow_info['help']}\n\n"
        "Do this next:\n"
        f"1. Go to: {workflow_info['tab']}\n"
        f"2. Area to change/detect: {detection or area_hint}\n"
        "3. Use the generated prompt below.\n"
        "4. Keep Advanced available for CFG, steps, denoise, seed, styles, and LoRAs."
    )

    return EasySdxlPlan(
        workflow=workflow,
        recommended_tab=workflow_info["tab"],
        positive_prompt=positive,
        inpaint_prompt=inpaint_prompt,
        detection_prompt=detection,
        negative_prompt=state.negative_prompt,
        steps=workflow_info["steps"],
        cfg=workflow_info["cfg"],
        denoise=workflow_info["denoise"],
        checklist=checklist,
    )


def build_easy_sdxl_outputs(workflow: str, area: str, user_instruction: str):
    plan = build_easy_sdxl_plan(workflow, area, user_instruction)
    settings = (
        f"Steps: {plan.steps}\n"
        f"CFG: {plan.cfg}\n"
        f"Denoise: {plan.denoise}\n"
        f"Recommended tab: {plan.recommended_tab}"
    )
    return (
        plan.positive_prompt,
        plan.inpaint_prompt,
        plan.detection_prompt,
        plan.negative_prompt,
        settings,
        plan.checklist,
    )
