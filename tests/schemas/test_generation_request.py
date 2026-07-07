from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.schemas import AssetReference, GenerationRequest, ImageSize, ProgressEvent, SeedConfig


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "generation"


def test_basic_text_to_image_fixture_validates() -> None:
    payload = json.loads((FIXTURES / "text_to_image_basic.json").read_text(encoding="utf-8"))

    request = GenerationRequest.model_validate(payload)

    assert request.prompt
    assert request.models.base == "example-base-model.safetensors"
    assert request.size.width == 1024
    assert request.size.height == 1024
    assert request.seed.seed == 12345
    assert request.content_filter.enabled is True


def test_image_size_must_align_to_eight() -> None:
    with pytest.raises(ValidationError):
        ImageSize(width=1025, height=1024)


def test_asset_reference_requires_locator() -> None:
    with pytest.raises(ValidationError):
        AssetReference(role="input")


def test_seed_cannot_be_fixed_and_randomized() -> None:
    with pytest.raises(ValidationError):
        SeedConfig(seed=123, randomize=True)


def test_progress_event_validates_percent_bounds() -> None:
    event = ProgressEvent(job_id="job_123", type="preview", percent=50, message="Halfway")

    assert event.job_id == "job_123"
    assert event.percent == 50

    with pytest.raises(ValidationError):
        ProgressEvent(job_id="job_123", type="preview", percent=101)
