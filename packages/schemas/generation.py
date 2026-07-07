"""Typed generation schemas for the experimental redesign.

The goal is to replace fragile positional UI argument parsing with explicit,
serializable request objects that can be validated, stored, replayed, and shared
between API, worker, tests, and future UI code.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .assets import AssetReference, ImageSize


PerformanceMode = Literal["speed", "quality", "extreme_speed", "lightning", "custom"]
OutputFormat = Literal["png", "jpeg", "webp"]
ControlImageType = Literal["image_prompt", "face", "canny", "cpds"]
UpscaleOrVariationMode = Literal[
    "disabled",
    "upscale_fast",
    "upscale_2x",
    "upscale_subtle",
    "upscale_strong",
    "variation_subtle",
    "variation_strong",
]
InpaintMode = Literal["disabled", "inpaint", "outpaint", "detail", "modify"]
JobStatus = Literal[
    "created",
    "queued",
    "assigned",
    "loading_models",
    "preparing_inputs",
    "running",
    "postprocessing",
    "saving",
    "succeeded",
    "failed",
    "cancel_requested",
    "cancelled",
]


class SeedConfig(BaseModel):
    """Seed behavior for deterministic or random generation."""

    model_config = ConfigDict(extra="forbid")

    seed: int | None = Field(default=None, ge=0, le=2**63 - 1)
    randomize: bool = False
    increment_per_image: bool = True

    @model_validator(mode="after")
    def randomize_and_seed_should_not_conflict(self) -> "SeedConfig":
        if self.randomize and self.seed is not None:
            raise ValueError("Provide either a fixed seed or randomize=true, not both.")
        return self


class ModelSelection(BaseModel):
    """Model files selected for a generation request."""

    model_config = ConfigDict(extra="forbid")

    base: str = Field(..., min_length=1)
    refiner: str = "None"
    vae: str = "Default"
    refiner_switch: float = Field(default=0.5, ge=0.0, le=1.0)
    refiner_swap_method: Literal["joint", "separate", "vae"] = "joint"


class LoraConfig(BaseModel):
    """LoRA selection and weight."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    weight: float = Field(default=1.0, ge=-10.0, le=10.0)
    enabled: bool = True


class AdvancedSettings(BaseModel):
    """Advanced sampler/runtime settings currently spread across UI args."""

    model_config = ConfigDict(extra="forbid")

    steps: int | None = Field(default=None, ge=1, le=500)
    cfg_scale: float = Field(default=7.0, ge=0.0, le=100.0)
    sharpness: float = Field(default=2.0, ge=0.0, le=100.0)
    sampler: str | None = None
    scheduler: str | None = None
    clip_skip: int = Field(default=1, ge=1, le=12)
    adaptive_cfg: float | None = None
    adm_scaler_positive: float | None = None
    adm_scaler_negative: float | None = None
    adm_scaler_end: float | None = None
    freeu_enabled: bool = False
    freeu_b1: float | None = None
    freeu_b2: float | None = None
    freeu_s1: float | None = None
    freeu_s2: float | None = None
    disable_preview: bool = False
    disable_intermediate_results: bool = False


class ControlImageInput(BaseModel):
    """Control/image-prompt input used by image prompt, face, canny, and CPDS paths."""

    model_config = ConfigDict(extra="forbid")

    type: ControlImageType
    image: AssetReference
    stop_at: float = Field(default=0.5, ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=-10.0, le=10.0)
    skip_preprocessor: bool = False
    debug_preprocessor: bool = False


class UpscaleOrVariationInput(BaseModel):
    """Upscale or variation image input."""

    model_config = ConfigDict(extra="forbid")

    mode: UpscaleOrVariationMode = "disabled"
    image: AssetReference | None = None
    denoise_strength: float | None = Field(default=None, ge=0.0, le=1.0)
    upscale_strength: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def image_required_when_enabled(self) -> "UpscaleOrVariationInput":
        if self.mode != "disabled" and self.image is None:
            raise ValueError("Upscale/variation input image is required when mode is enabled.")
        return self


class InpaintInput(BaseModel):
    """Inpaint/outpaint request data."""

    model_config = ConfigDict(extra="forbid")

    mode: InpaintMode = "disabled"
    image: AssetReference | None = None
    mask: AssetReference | None = None
    additional_prompt: str = ""
    outpaint_selections: list[Literal["left", "right", "top", "bottom"]] = Field(default_factory=list)
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    respective_field: float = Field(default=0.618, ge=0.0, le=1.0)
    disable_initial_latent: bool = False
    invert_mask: bool = False
    erode_or_dilate: int = Field(default=0, ge=-256, le=256)

    @model_validator(mode="after")
    def image_required_when_enabled(self) -> "InpaintInput":
        if self.mode != "disabled" and self.image is None:
            raise ValueError("Inpaint/outpaint image is required when mode is enabled.")
        if self.mode in {"inpaint", "detail", "modify"} and self.mask is None:
            raise ValueError("Mask is required for inpaint/detail/modify modes.")
        return self


class EnhanceConfig(BaseModel):
    """Enhancement pass configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    input_image: AssetReference | None = None
    prompt: str = ""
    negative_prompt: str = ""
    mask_prompt: str = ""
    inpaint_strength: float = Field(default=0.5, ge=0.0, le=1.0)
    save_final_only: bool = False

    @model_validator(mode="after")
    def image_required_when_enabled(self) -> "EnhanceConfig":
        if self.enabled and self.input_image is None:
            raise ValueError("Enhance input image is required when enabled.")
        return self


class ImageInputs(BaseModel):
    """All optional image-based workflows for a generation request."""

    model_config = ConfigDict(extra="forbid")

    controls: list[ControlImageInput] = Field(default_factory=list)
    upscale_or_variation: UpscaleOrVariationInput | None = None
    inpaint: InpaintInput | None = None
    enhance: list[EnhanceConfig] = Field(default_factory=list)


class ContentFilterConfig(BaseModel):
    """Explicit image filtering policy for generated outputs."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    mode: Literal["checker", "disabled"] = "checker"
    apply_to_previews: bool = False
    apply_to_outputs: bool = True

    @model_validator(mode="after")
    def disabled_mode_should_disable_filter(self) -> "ContentFilterConfig":
        if self.mode == "disabled" and self.enabled:
            raise ValueError("Use enabled=false when mode is disabled.")
        return self


class OutputConfig(BaseModel):
    """Output format, persistence, and metadata behavior."""

    model_config = ConfigDict(extra="forbid")

    format: OutputFormat = "png"
    persist: bool = True
    save_metadata: bool = True
    metadata_scheme: str = "fooocus"
    create_grid: bool = False
    save_intermediate: bool = False


class GenerationRequest(BaseModel):
    """Complete request to generate or transform images."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=1)
    negative_prompt: str = ""
    styles: list[str] = Field(default_factory=list)
    performance: PerformanceMode = "quality"
    image_count: int = Field(default=1, ge=1, le=64)
    size: ImageSize = Field(default_factory=ImageSize)
    seed: SeedConfig = Field(default_factory=SeedConfig)
    models: ModelSelection
    loras: list[LoraConfig] = Field(default_factory=list)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)
    inputs: ImageInputs = Field(default_factory=ImageInputs)
    output: OutputConfig = Field(default_factory=OutputConfig)
    content_filter: ContentFilterConfig = Field(default_factory=ContentFilterConfig)
    user_id: str | None = None
    project_id: str | None = None
    request_metadata: dict[str, Any] = Field(default_factory=dict)


class OutputImage(BaseModel):
    """One generated output image."""

    model_config = ConfigDict(extra="forbid")

    asset: AssetReference
    seed: int | None = None
    size: ImageSize
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerationResult(BaseModel):
    """Final result for a generation job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus
    outputs: list[OutputImage] = Field(default_factory=list)
    timing_ms: dict[str, int | float] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
