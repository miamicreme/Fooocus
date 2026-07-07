from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StudioFeature:
    key: str
    label: str
    fooocus_area: str
    use_when: str
    avoid_when: str
    required_inputs: List[str]
    outputs: List[str]
    controls: Dict[str, str]
    risk_level: str
    guardrail_notes: str


FEATURES: Dict[str, StudioFeature] = {
    "text_to_image": StudioFeature(
        key="text_to_image",
        label="Text to Image",
        fooocus_area="Prompt only",
        use_when="The user wants a brand-new image and does not need a source image preserved.",
        avoid_when="The user wants exact edits to an uploaded image or identity preservation from a real person.",
        required_inputs=["plain prompt"],
        outputs=["primary prompt", "negative prompt", "style recommendation"],
        controls={"input_image": "off", "mask": "none", "styles": "optional"},
        risk_level="medium",
        guardrail_notes="Validate main prompt because UI-only guardrails can be bypassed.",
    ),
    "image_prompt": StudioFeature(
        key="image_prompt",
        label="Image Prompt reference",
        fooocus_area="Image Prompt",
        use_when="The uploaded image should inspire a new image, style, composition, or visual direction.",
        avoid_when="The user expects pixel-perfect edits to only one part of the source image.",
        required_inputs=["reference image", "main prompt"],
        outputs=["reference strategy", "prompt", "negative prompt"],
        controls={"input_image": "on", "control_type": "ImagePrompt", "mask": "none"},
        risk_level="medium",
        guardrail_notes="Clearly explain that this creates a new image inspired by the reference; it is not exact editing.",
    ),
    "face_reference": StudioFeature(
        key="face_reference",
        label="Face reference / identity preservation",
        fooocus_area="Image Prompt",
        use_when="The user wants the same adult person to remain recognizable across a new image or photo bundle.",
        avoid_when="The user only wants a minor local edit; use inpaint instead.",
        required_inputs=["clear face reference", "optional upper-body reference", "optional full-body/pose reference"],
        outputs=["identity prompt", "negative identity-drift prompt", "handoff recipe"],
        controls={"input_image": "on", "control_type": "FaceSwap or face reference", "mask": "none"},
        risk_level="high",
        guardrail_notes="Identity workflows should only be used with user-provided/authorized images. Warn that one headshot can drift on full-body outputs.",
    ),
    "pyracanny": StudioFeature(
        key="pyracanny",
        label="PyraCanny structure control",
        fooocus_area="Image Prompt",
        use_when="The output should follow hard edges, pose, outlines, or strong visual structure from a reference image.",
        avoid_when="The user wants loose composition only; use CPDS instead.",
        required_inputs=["structure/pose reference image", "main prompt"],
        outputs=["structure-control prompt", "weight guidance"],
        controls={"input_image": "on", "control_type": "PyraCanny", "mask": "none"},
        risk_level="medium",
        guardrail_notes="Warn that high structure weight can over-constrain the result.",
    ),
    "cpds": StudioFeature(
        key="cpds",
        label="CPDS composition control",
        fooocus_area="Image Prompt",
        use_when="The output should follow broad composition, depth, or layout without copying every edge.",
        avoid_when="The user needs exact edge/line following; use PyraCanny instead.",
        required_inputs=["composition reference image", "main prompt"],
        outputs=["composition-control prompt", "weight guidance"],
        controls={"input_image": "on", "control_type": "CPDS", "mask": "none"},
        risk_level="medium",
        guardrail_notes="Warn that composition guidance may change identity unless face reference is also used.",
    ),
    "upscale": StudioFeature(
        key="upscale",
        label="Upscale image",
        fooocus_area="Upscale or Variation",
        use_when="The image is already good and needs more size, sharpness, or polish.",
        avoid_when="The user wants a major creative change; use variation or image prompt.",
        required_inputs=["source image"],
        outputs=["upscale plan", "negative artifact prompt"],
        controls={"input_image": "on", "uov_method": "Upscale 2x", "mask": "none"},
        risk_level="low",
        guardrail_notes="Preserve composition and identity; avoid over-sharpening.",
    ),
    "variation": StudioFeature(
        key="variation",
        label="Variation",
        fooocus_area="Upscale or Variation",
        use_when="The user wants a new version inspired by the uploaded image.",
        avoid_when="The user wants exact local edits or strict identity preservation.",
        required_inputs=["source image", "variation strength"],
        outputs=["variation prompt", "drift warning"],
        controls={"input_image": "on", "uov_method": "Vary subtle or strong", "mask": "none"},
        risk_level="medium",
        guardrail_notes="Variation may drift identity, body, background, and clothing. Label it as inspired-by, not exact edit.",
    ),
    "inpaint": StudioFeature(
        key="inpaint",
        label="Inpaint / Outpaint exact edit",
        fooocus_area="Inpaint or Outpaint",
        use_when="The user wants to change one part of an uploaded image while preserving the rest.",
        avoid_when="The user wants a brand-new scene from references; use image prompt instead.",
        required_inputs=["source image", "mask", "inpaint prompt"],
        outputs=["inpaint prompt", "mask strategy", "negative prompt"],
        controls={"input_image": "on", "inpaint_mode": "Modify Content", "mask": "manual or auto"},
        risk_level="high",
        guardrail_notes="Validate main and inpaint prompt. Require mask review for face, body, clothing, and background edits.",
    ),
    "auto_mask_sam": StudioFeature(
        key="auto_mask_sam",
        label="Automatic mask with SAM / GroundingDINO",
        fooocus_area="Inpaint or Outpaint",
        use_when="The user wants text-directed automatic masking for a specific object, clothing item, person, or background.",
        avoid_when="The target is vague or the automatic mask selects too much; use manual mask or U2Net segmentation.",
        required_inputs=["source image", "detection prompt"],
        outputs=["detection prompt", "mask review checklist"],
        controls={"input_image": "on", "advanced_masking": "on", "mask_model": "sam"},
        risk_level="high",
        guardrail_notes="Always review generated mask before generation. Detection prompt should be narrow and specific.",
    ),
    "auto_mask_u2net": StudioFeature(
        key="auto_mask_u2net",
        label="Automatic mask with U2Net segmentation",
        fooocus_area="Inpaint or Outpaint",
        use_when="The user wants broad person/background/clothing segmentation rather than text-directed object detection.",
        avoid_when="The user needs a very specific object mask; use SAM/GroundingDINO instead.",
        required_inputs=["source image"],
        outputs=["segmentation strategy", "mask review checklist"],
        controls={"input_image": "on", "advanced_masking": "on", "mask_model": "u2net_human_seg or u2net_cloth_seg"},
        risk_level="medium",
        guardrail_notes="Broad masks can include too much. Review and refine before generation.",
    ),
    "enhance": StudioFeature(
        key="enhance",
        label="Enhance",
        fooocus_area="Enhance",
        use_when="The user wants to improve details, refine a winning image, or polish after generation.",
        avoid_when="The image direction is wrong; regenerate before enhancing.",
        required_inputs=["source image", "enhance goal"],
        outputs=["enhance prompt", "settings recommendation"],
        controls={"input_image": "on", "enhance": "on", "mask": "optional"},
        risk_level="medium",
        guardrail_notes="Enhance has separate prompts and masks; guardrails must apply to enhance prompts too.",
    ),
    "describe": StudioFeature(
        key="describe",
        label="Describe / image-to-prompt",
        fooocus_area="Describe",
        use_when="The user wants to understand an uploaded image or turn it into a reusable prompt.",
        avoid_when="The description should be applied without review to a sensitive/personal image.",
        required_inputs=["source image"],
        outputs=["draft prompt", "review checklist"],
        controls={"input_image": "on", "describe": "on", "apply_directly": "review first"},
        risk_level="medium",
        guardrail_notes="Review generated descriptions before applying to main prompt, especially for personal images.",
    ),
}


SCENARIO_RULES: List[tuple[str, List[str], str]] = [
    ("photo bundle", ["bundle", "set of", "all types", "photoshoot", "photo shoot", "multiple images"], "face_reference"),
    ("exact local edit", ["remove", "replace", "change only", "edit only", "inpaint", "mask"], "inpaint"),
    ("automatic object mask", ["auto mask", "detect", "scan", "select object"], "auto_mask_sam"),
    ("background/person segmentation", ["person mask", "background mask", "segment", "segmentation"], "auto_mask_u2net"),
    ("identity preservation", ["same person", "keep my face", "recognizable", "identity", "me standing", "make me"], "face_reference"),
    ("pose or edge control", ["pose", "outline", "edges", "canny", "structure"], "pyracanny"),
    ("composition control", ["composition", "depth", "layout", "cpds"], "cpds"),
    ("upscale", ["upscale", "bigger", "larger", "higher resolution"], "upscale"),
    ("variation", ["variation", "new version", "inspired by", "similar but different"], "variation"),
    ("enhance", ["enhance", "improve", "sharpen", "polish", "clean up"], "enhance"),
    ("describe", ["describe", "what is in", "turn into prompt", "analyze image"], "describe"),
]


def get_feature(key: str) -> StudioFeature:
    return FEATURES[key]


def list_features() -> List[StudioFeature]:
    return list(FEATURES.values())


def route_feature(goal: str, image_count: int, wants_identity: bool, wants_exact_edit: bool, wants_bundle: bool) -> StudioFeature:
    text = (goal or "").lower()
    if wants_bundle:
        return FEATURES["face_reference"]
    if wants_exact_edit:
        return FEATURES["inpaint"]
    for _scenario, keywords, feature_key in SCENARIO_RULES:
        if any(keyword in text for keyword in keywords):
            return FEATURES[feature_key]
    if image_count > 0 and wants_identity:
        return FEATURES["face_reference"]
    if image_count > 0:
        return FEATURES["image_prompt"]
    return FEATURES["text_to_image"]


def feature_map_markdown() -> str:
    lines = ["# AI Studio Feature Map", "", "This is the single source of truth used by the Studio Agent.", ""]
    for feature in list_features():
        lines.extend(
            [
                f"## {feature.label}",
                f"- Key: `{feature.key}`",
                f"- Fooocus area: {feature.fooocus_area}",
                f"- Use when: {feature.use_when}",
                f"- Avoid when: {feature.avoid_when}",
                f"- Required inputs: {', '.join(feature.required_inputs)}",
                f"- Outputs: {', '.join(feature.outputs)}",
                f"- Controls: {feature.controls}",
                f"- Risk: {feature.risk_level}",
                f"- Guardrails: {feature.guardrail_notes}",
                "",
            ]
        )
    return "\n".join(lines)
