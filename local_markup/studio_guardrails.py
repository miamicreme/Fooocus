from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from local_markup.studio_knowledge import StudioFeature


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    mode: str
    feature_key: str
    risk_level: str
    warnings: List[str]
    blocked_reason: str = ""

    def as_text(self) -> str:
        status = "Allowed" if self.allowed else "Blocked"
        lines = [
            f"Status: {status}",
            f"Mode: {self.mode}",
            f"Feature: {self.feature_key}",
            f"Risk level: {self.risk_level}",
        ]
        if self.blocked_reason:
            lines.append(f"Reason: {self.blocked_reason}")
        if self.warnings:
            lines.append("Warnings:")
            lines.extend([f"- {warning}" for warning in self.warnings])
        return "\n".join(lines)


def env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def guardrail_mode() -> str:
    return os.getenv("KJB_GUARDRAILS_MODE", "balanced").strip().lower()


def validate_feature_use(feature: StudioFeature, goal: str, image_count: int, wants_identity: bool) -> GuardrailDecision:
    mode = guardrail_mode()
    warnings: List[str] = []

    if mode == "off":
        return GuardrailDecision(True, mode, feature.key, feature.risk_level, ["Guardrails are off. Use only with trusted local workflows."])

    if feature.key in {"face_reference", "image_prompt"} and wants_identity:
        warnings.append("Identity-preserving workflows should use user-provided or authorized images only.")
        if image_count == 0:
            warnings.append("No reference image detected. Identity preservation will be weak or impossible.")
        elif image_count == 1:
            warnings.append("Only one reference image detected. Full-body or bundle outputs may drift; add upper-body/full-body references when possible.")

    if feature.key == "inpaint":
        warnings.append("Exact edits require mask review before generation. Do not trust an automatic mask blindly.")

    if feature.key == "auto_mask_sam":
        warnings.append("SAM/GroundingDINO masks can select the wrong region. Review the mask before generation.")

    if feature.key == "variation":
        warnings.append("Variation creates a new version inspired by the image; it is not an exact edit and may drift identity.")

    if feature.key == "describe":
        warnings.append("Review image-to-prompt descriptions before applying them to a personal image workflow.")

    if feature.risk_level == "high" and mode == "strict":
        warnings.append("Strict mode: high-risk workflows require explicit user review of references, prompts, and masks before generation.")

    if not env_flag("KJB_ALLOW_FACE_REFERENCE", True) and feature.key == "face_reference":
        return GuardrailDecision(False, mode, feature.key, feature.risk_level, warnings, "Face reference workflows are disabled by KJB_ALLOW_FACE_REFERENCE=false.")

    if not env_flag("KJB_ALLOW_AUTO_MASK", True) and feature.key in {"auto_mask_sam", "auto_mask_u2net"}:
        return GuardrailDecision(False, mode, feature.key, feature.risk_level, warnings, "Automatic masking is disabled by KJB_ALLOW_AUTO_MASK=false.")

    return GuardrailDecision(True, mode, feature.key, feature.risk_level, warnings)
