from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from .planner import build_edit_intent


@dataclass
class MarkupUiState:
    inpaint_prompt: str
    negative_prompt: str
    mode: str
    detection_prompt: str
    summary: str
    notes: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def target_to_detection_prompt(targets: List[str]) -> str:
    cleaned = [target for target in targets if target and target != "selected area"]
    if not cleaned:
        return "selected area"
    if "people" in cleaned:
        return "person"
    return cleaned[0]


def build_markup_ui_state(user_instruction: str, image_context: Optional[str] = None) -> MarkupUiState:
    intent = build_edit_intent(user_instruction, image_context=image_context)
    target_text = ", ".join(intent.targets) if intent.targets else "selected area"
    return MarkupUiState(
        inpaint_prompt=intent.prompt,
        negative_prompt=intent.negative_prompt,
        mode=intent.mode,
        detection_prompt=target_to_detection_prompt(intent.targets),
        summary=f"Action: {intent.action} | Target: {target_text} | Suggested mode: {intent.mode}",
        notes=intent.notes,
    )


def build_markup_ui_outputs(user_instruction: str, image_context: Optional[str] = None):
    state = build_markup_ui_state(user_instruction, image_context=image_context)
    return state.inpaint_prompt, state.detection_prompt, state.summary, state.negative_prompt
