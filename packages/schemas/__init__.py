"""Shared lightweight schemas for the experimental Fooocus redesign.

These schemas must not import torch, gradio, cv2, or any model runtime code.
They are safe to use from the API, worker, tests, and future frontend tooling.
"""

from .assets import AssetReference, ImageSize
from .events import ProgressEvent
from .generation import (
    AdvancedSettings,
    ContentFilterConfig,
    ControlImageInput,
    EnhanceConfig,
    GenerationRequest,
    GenerationResult,
    ImageInputs,
    LoraConfig,
    ModelSelection,
    OutputConfig,
    OutputImage,
    SeedConfig,
    UpscaleOrVariationInput,
)

__all__ = [
    "AdvancedSettings",
    "AssetReference",
    "ContentFilterConfig",
    "ControlImageInput",
    "EnhanceConfig",
    "GenerationRequest",
    "GenerationResult",
    "ImageInputs",
    "ImageSize",
    "LoraConfig",
    "ModelSelection",
    "OutputConfig",
    "OutputImage",
    "ProgressEvent",
    "SeedConfig",
    "UpscaleOrVariationInput",
]
