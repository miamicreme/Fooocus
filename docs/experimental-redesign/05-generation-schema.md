# Generation Schema Contract

Branch: `feat/generation-request-schema`

This branch introduces lightweight request/result/event schemas for the experimental redesign. The schemas are intentionally free of Torch, Gradio, OpenCV, model loading, and GPU runtime imports.

---

## Why This Exists

The existing app receives a long positional argument list from the UI and unpacks it inside the worker task object. That makes the workflow fragile because changing UI order can silently break generation behavior.

The new schema contract makes each setting explicit:

```text
GenerationRequest
  -> prompt
  -> seed
  -> model selection
  -> LoRAs
  -> advanced settings
  -> image inputs
  -> output config
  -> content filter config
```

This lets the future API, worker, UI, tests, and replay system all use the same contract.

---

## Files Added

```text
packages/__init__.py
packages/schemas/__init__.py
packages/schemas/assets.py
packages/schemas/events.py
packages/schemas/generation.py
tests/fixtures/generation/text_to_image_basic.json
tests/schemas/test_generation_request.py
```

---

## Main Schemas

| Schema | Purpose |
|---|---|
| `GenerationRequest` | Complete request to generate or transform images |
| `GenerationResult` | Final job result with outputs, timing, and error data |
| `ProgressEvent` | Realtime or persisted progress event |
| `ImageSize` | Validated width/height dimensions |
| `AssetReference` | Reference to uploaded input, preview, mask, output, or metadata asset |
| `SeedConfig` | Fixed/random/increment seed behavior |
| `ModelSelection` | Base/refiner/VAE settings |
| `LoraConfig` | LoRA name, weight, enabled state |
| `AdvancedSettings` | Sampler, scheduler, CFG, sharpness, FreeU, preview flags |
| `ImageInputs` | Control images, inpaint, upscale/variation, enhance settings |
| `OutputConfig` | Output format, persistence, metadata, grid/intermediate flags |
| `ContentFilterConfig` | Explicit image filtering behavior |

---

## Current Fixture

```text
tests/fixtures/generation/text_to_image_basic.json
```

This fixture covers the minimum parity path:

- text prompt
- negative prompt
- styles
- performance mode
- image count
- image size
- fixed seed
- base/refiner/VAE selection
- advanced sampler settings
- output metadata settings
- content filter settings

---

## Validation Tests

```text
tests/schemas/test_generation_request.py
```

Current tests validate:

- the basic fixture parses into `GenerationRequest`
- dimensions must be divisible by 8
- asset references need a locator
- seed config cannot be both fixed and randomized
- progress event percentage bounds

---

## Next Schema Work

Add fixtures for:

```text
text_to_image_lora.json
text_to_image_refiner.json
upscale_subtle.json
variation_subtle.json
image_prompt_ip.json
image_prompt_face.json
controlnet_canny.json
controlnet_cpds.json
inpaint_basic.json
outpaint_left_right.json
enhance_detail.json
metadata_png.json
```

Then build a dry-run `GenerationPlanner` that converts `GenerationRequest` into an ordered pipeline plan without requiring GPU execution.

---

## Acceptance Criteria

This branch is complete when:

1. Schemas import without model runtime dependencies.
2. The basic fixture validates.
3. Invalid dimensions fail validation.
4. Invalid asset references fail validation.
5. Invalid seed behavior fails validation.
6. Progress events validate.
7. The next adapter branch can consume `GenerationRequest`.
