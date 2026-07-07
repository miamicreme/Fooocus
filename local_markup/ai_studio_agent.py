from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


WORKFLOW_LIBRARY: Dict[str, Dict[str, str]] = {
    "make new image": {
        "tool": "Text to Image",
        "fooocus_tab": "Prompt only",
        "why": "Best when no uploaded image needs to be preserved exactly.",
        "mask": "No mask needed.",
        "reference": "Optional style reference only.",
    },
    "edit part of image": {
        "tool": "Inpaint / Outpaint",
        "fooocus_tab": "Inpaint or Outpaint",
        "why": "Best when the user wants to change only part of an uploaded image.",
        "mask": "Use manual mask or automatic SAM/U2Net mask, then review before generation.",
        "reference": "Use the uploaded image as the source image.",
    },
    "keep identity": {
        "tool": "Image Prompt / Face Reference",
        "fooocus_tab": "Image Prompt",
        "why": "Best when the person should stay recognizable across new images.",
        "mask": "No mask unless doing exact edits.",
        "reference": "Use 2-5 clear photos: face close-up, upper body, full body if available.",
    },
    "follow pose or shape": {
        "tool": "PyraCanny / CPDS",
        "fooocus_tab": "Image Prompt",
        "why": "Best when a reference image should guide structure, pose, outline, or composition.",
        "mask": "No mask required. Use PyraCanny for edges, CPDS for composition/depth.",
        "reference": "Use a pose/structure reference image.",
    },
    "make bigger or cleaner": {
        "tool": "Upscale / Variation",
        "fooocus_tab": "Upscale or Variation",
        "why": "Best when the image is mostly right and needs more resolution or polish.",
        "mask": "No mask required.",
        "reference": "Use the image to upscale or vary.",
    },
    "photo bundle": {
        "tool": "Bundle Builder",
        "fooocus_tab": "Image Prompt",
        "why": "Best when the user wants a set of headshots, full-body portraits, lifestyle photos, or resort/fitness/business/casual variants.",
        "mask": "Use masks only for exact outfit/background edits. Use references for new bundle images.",
        "reference": "Use multiple reference photos for identity and body accuracy.",
    },
}


@dataclass
class AgentPlan:
    user_goal: str
    selected_workflow: str
    tool: str
    fooocus_tab: str
    primary_prompt: str
    negative_prompt: str
    reference_strategy: str
    mask_strategy: str
    generation_settings: str
    next_steps: str
    warnings: str

    def as_markdown(self) -> str:
        return (
            f"## Agent Plan\n\n"
            f"**Goal:** {self.user_goal}\n\n"
            f"**Selected workflow:** {self.selected_workflow}\n\n"
            f"**Tool:** {self.tool}\n\n"
            f"**Fooocus area:** {self.fooocus_tab}\n\n"
            f"### Why this workflow\n{WORKFLOW_LIBRARY[self.selected_workflow]['why']}\n\n"
            f"### Reference strategy\n{self.reference_strategy}\n\n"
            f"### Mask strategy\n{self.mask_strategy}\n\n"
            f"### Recommended settings\n{self.generation_settings}\n\n"
            f"### Next steps\n{self.next_steps}\n\n"
            f"### Warnings / guardrails\n{self.warnings}"
        )


def _clean_goal(goal: str) -> str:
    return (goal or "").strip() or "Create a high quality realistic image."


def infer_workflow(goal: str, image_count: int, wants_identity: bool, wants_exact_edit: bool, wants_bundle: bool) -> str:
    text = goal.lower()
    if wants_bundle or any(word in text for word in ["bundle", "set of", "all types", "multiple images", "photoshoot"]):
        return "photo bundle"
    if wants_exact_edit or any(word in text for word in ["remove", "replace", "change jacket", "change background", "edit only", "inpaint"]):
        return "edit part of image"
    if any(word in text for word in ["stand up", "full body", "same person", "identity", "me "]) or wants_identity:
        return "keep identity"
    if any(word in text for word in ["pose", "structure", "outline", "composition", "canny", "cpds"]):
        return "follow pose or shape"
    if any(word in text for word in ["upscale", "bigger", "enhance", "cleaner", "sharper"]):
        return "make bigger or cleaner"
    if image_count > 0:
        return "keep identity" if wants_identity else "edit part of image"
    return "make new image"


def build_prompt(goal: str, workflow: str) -> str:
    goal = _clean_goal(goal)
    base = "high quality realistic photography, natural lighting, sharp details"

    if workflow == "photo bundle":
        return (
            "same adult person from the reference photos, preserve facial identity, age, skin tone, natural expression, "
            "realistic body proportions, create a varied personal photo bundle, " + goal + ", " + base
        )
    if workflow == "keep identity":
        return (
            "same adult person from the reference photos, preserve facial identity, age, skin tone, face shape, natural expression, "
            "realistic body proportions, " + goal + ", " + base
        )
    if workflow == "edit part of image":
        return (
            "same person, preserve unchanged areas, seamless realistic edit, natural lighting, "
            "only change the requested area, " + goal
        )
    if workflow == "follow pose or shape":
        return "use the uploaded reference for pose/composition guidance, " + goal + ", " + base
    if workflow == "make bigger or cleaner":
        return "improve image quality, preserve original identity and composition, sharper details, clean finish, " + goal
    return goal + ", " + base


def build_negative_prompt(workflow: str) -> str:
    common = "low quality, blurry, distorted face, bad hands, extra limbs, warped fingers, artifacts, unrealistic anatomy"
    if workflow in {"keep identity", "photo bundle", "edit part of image"}:
        return common + ", different person, changed identity, unnatural skin, distorted eyes"
    return common


def build_next_steps(workflow: str) -> str:
    if workflow == "edit part of image":
        return (
            "1. Upload the source image.\n"
            "2. Choose the area to edit.\n"
            "3. Use automatic mask if possible, then review the mask.\n"
            "4. Generate 2-4 candidates.\n"
            "5. Pick the best one and enhance/upscale if needed."
        )
    if workflow == "keep identity":
        return (
            "1. Upload 2-5 reference photos if available.\n"
            "2. Use a clear face reference first.\n"
            "3. Add full-body reference for standing or outfit accuracy.\n"
            "4. Generate multiple candidates and keep the closest identity match."
        )
    if workflow == "follow pose or shape":
        return (
            "1. Upload the structure or pose reference.\n"
            "2. Use PyraCanny for hard edges or CPDS for softer composition.\n"
            "3. Generate candidates and adjust weight if the output follows too much or too little."
        )
    if workflow == "make bigger or cleaner":
        return "1. Upload the image.\n2. Use Upscale (2x) for quality.\n3. Use subtle variation only when you want small creative changes."
    if workflow == "photo bundle":
        return (
            "1. Upload face, upper-body, and full-body references if available.\n"
            "2. Generate one bundle category at a time.\n"
            "3. Keep the best identity match.\n"
            "4. Use upscale/enhance on winners."
        )
    return "1. Enter prompt.\n2. Pick style.\n3. Generate.\n4. Save the best result."


def build_agent_plan(
    goal: str,
    image_count: int = 0,
    wants_identity: bool = True,
    wants_exact_edit: bool = False,
    wants_bundle: bool = False,
) -> AgentPlan:
    goal = _clean_goal(goal)
    workflow = infer_workflow(goal, image_count, wants_identity, wants_exact_edit, wants_bundle)
    info = WORKFLOW_LIBRARY[workflow]
    primary_prompt = build_prompt(goal, workflow)
    negative_prompt = build_negative_prompt(workflow)
    generation_settings = (
        "Performance: Speed for drafts, Quality for final.\n"
        "Image count: 2-4 candidates.\n"
        "Styles: Fooocus Photograph + Fooocus Enhance + Fooocus Sharp for realistic personal photos.\n"
        "Seed: random for exploration, locked seed for refinement."
    )
    warnings = (
        "Reference images can drift if only one headshot is provided. Full-body goals work best with full-body references. "
        "Exact edits require a reviewed mask. For personal images, keep metadata/log privacy settings in mind."
    )
    return AgentPlan(
        user_goal=goal,
        selected_workflow=workflow,
        tool=info["tool"],
        fooocus_tab=info["fooocus_tab"],
        primary_prompt=primary_prompt,
        negative_prompt=negative_prompt,
        reference_strategy=info["reference"],
        mask_strategy=info["mask"],
        generation_settings=generation_settings,
        next_steps=build_next_steps(workflow),
        warnings=warnings,
    )


def build_agent_outputs(goal: str, image_1, image_2, image_3, wants_identity: bool, wants_exact_edit: bool, wants_bundle: bool):
    image_count = sum(x is not None for x in [image_1, image_2, image_3])
    plan = build_agent_plan(goal, image_count, wants_identity, wants_exact_edit, wants_bundle)
    return plan.as_markdown(), plan.primary_prompt, plan.negative_prompt, plan.tool, plan.fooocus_tab
