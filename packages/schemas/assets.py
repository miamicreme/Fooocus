"""Asset and image-size schemas for generation requests and results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ImageSize(BaseModel):
    """Pixel dimensions for generated or source images."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(default=1024, ge=64, le=8192)
    height: int = Field(default=1024, ge=64, le=8192)

    @model_validator(mode="after")
    def dimensions_should_align_to_eight(self) -> "ImageSize":
        if self.width % 8 != 0 or self.height % 8 != 0:
            raise ValueError("Image dimensions must be divisible by 8 for latent-space pipelines.")
        return self


class AssetReference(BaseModel):
    """Reference to an uploaded image, mask, preview, or output asset."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str | None = Field(default=None, description="Internal asset identifier when stored by the platform.")
    path: str | None = Field(default=None, description="Local path for legacy/dev workflows.")
    url: str | None = Field(default=None, description="Remote URL for object-storage or API workflows.")
    mime_type: str | None = Field(default=None, description="Optional MIME type, such as image/png.")
    role: Literal["input", "mask", "preview", "output", "metadata"] = "input"

    @model_validator(mode="after")
    def at_least_one_locator(self) -> "AssetReference":
        if not self.asset_id and not self.path and not self.url:
            raise ValueError("AssetReference requires asset_id, path, or url.")
        return self
